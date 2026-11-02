"""Parser for the TI mmWave out-of-box demo output (data UART) and the radar mounting geometry.

Packet layout (TI, "Understanding the Out of Box Demo Data Output"): a header with the magic word
0x0102 0x0304 0x0506 0x0708, then ``numTLVs`` items of (type, length, payload). TLV type 1 is the
point cloud: per point float32 x, y, z [m] and doppler [m/s]. Little-endian.

Two things are **not stated in that document and must be checked on the rig** (see the logger
docs, "Radar sign check"): the radar's axes (assumed x right, y along the boresight, z up) and the
Doppler sign (assumed positive = moving away from the radar).
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

import numpy as np

MAGIC = struct.pack("<4H", 0x0102, 0x0304, 0x0506, 0x0708)
HEADER = struct.Struct("<8I")  # after the magic word: version ... subframe number
HEADER_LEN = len(MAGIC) + HEADER.size  # 40 bytes
TLV = struct.Struct("<2I")
TLV_POINTS = 1


@dataclass
class RadarFrame:
    frame_number: int
    points: np.ndarray  # (n, 4): x, y, z, doppler in the radar frame


class PacketReader:
    """Collects bytes from the data UART and returns complete frames."""

    def __init__(self, max_buffer: int = 1 << 20):
        self.buf = bytearray()
        self.max_buffer = max_buffer
        self.bad_packets = 0

    def feed(self, data: bytes) -> list[RadarFrame]:
        self.buf.extend(data)
        frames = []
        while True:
            start = self.buf.find(MAGIC)
            if start < 0:
                del self.buf[: max(0, len(self.buf) - len(MAGIC) + 1)]
                break
            if start:
                del self.buf[:start]
            if len(self.buf) < HEADER_LEN:
                break
            header = HEADER.unpack_from(self.buf, len(MAGIC))
            total_len, frame_number, num_tlvs = header[1], header[3], header[6]
            if total_len < HEADER_LEN or total_len > self.max_buffer:
                self.bad_packets += 1
                del self.buf[: len(MAGIC)]
                continue
            if len(self.buf) < total_len:
                break
            packet = bytes(self.buf[:total_len])
            del self.buf[:total_len]
            frame = _parse_packet(packet, frame_number, num_tlvs)
            if frame is None:
                self.bad_packets += 1
            else:
                frames.append(frame)
        return frames


def _parse_packet(packet: bytes, frame_number: int, num_tlvs: int) -> RadarFrame | None:
    pos = HEADER_LEN
    points = np.zeros((0, 4))
    for _ in range(num_tlvs):
        if pos + TLV.size > len(packet):
            return None
        kind, length = TLV.unpack_from(packet, pos)
        pos += TLV.size
        if pos + length > len(packet):
            return None
        if kind == TLV_POINTS and length % 16 == 0:
            points = np.frombuffer(packet, dtype="<f4", count=length // 4, offset=pos)
            points = points.reshape(-1, 4).astype(float)
        pos += length
    return RadarFrame(frame_number, points)


def build_packet(frame_number: int, points: np.ndarray) -> bytes:
    """A packet in the same format, for tests and the loopback simulator."""
    pts = np.asarray(points, dtype="<f4").reshape(-1, 4)
    payload = TLV.pack(TLV_POINTS, pts.nbytes) + pts.tobytes() if len(pts) else b""
    total = HEADER_LEN + len(payload)
    total += (-total) % 32  # TI pads packets to a multiple of 32 bytes
    header = HEADER.pack(
        0x03060000, total, 0xA6843, frame_number, 0, len(pts), int(bool(len(pts))), 0
    )
    return (MAGIC + header + payload).ljust(total, b"\0")


@dataclass
class RadarMount:
    """Where the radar points, in the body frame (x forward, y left, z up).

    yaw_deg: direction of the boresight seen from above, 0 = forward, 180 = backward.
    tilt_down_deg: how far the boresight is tilted below horizontal (45 = halfway down).
    frame_period_s: radar frame period. With it, frames are timed by frame number (no USB jitter).
    height_m: height of the radar above the ground, for the ground-point filter.
    doppler_sign: +1 if TI's doppler is positive for points moving away (assumed), else -1.
    """

    yaw_deg: float = 180.0
    tilt_down_deg: float = 45.0
    height_m: float = 0.5
    doppler_sign: float = 1.0
    min_range_m: float = 0.3
    max_range_m: float = 4.0
    ground_tolerance_m: float = 0.15
    frame_period_s: float = 0.05  # the frame period in the radar .cfg (frameCfg); 0 = unknown
    extra: dict = field(default_factory=dict)

    def rotation(self) -> np.ndarray:
        """Matrix that turns radar-frame vectors (x right, y boresight, z up) into body frame."""
        # Radar frame -> "level, pointing forward" body axes: boresight y -> body x,
        # radar x (right) -> body -y, radar z (up) -> body z.
        to_body = np.array([[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
        t = math.radians(self.tilt_down_deg)
        pitch_down = np.array(
            [[math.cos(t), 0.0, math.sin(t)], [0.0, 1.0, 0.0], [-math.sin(t), 0.0, math.cos(t)]]
        )
        y = math.radians(self.yaw_deg)
        yaw = np.array(
            [[math.cos(y), -math.sin(y), 0.0], [math.sin(y), math.cos(y), 0.0], [0, 0, 1]]
        )
        return yaw @ pitch_down @ to_body

    def ground_points(self, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Keep detections on the ground. Returns (unit vectors in body frame, radial velocity
        in the log convention: radial = -(u . v_body), positive when the ground moves away)."""
        if len(points) == 0:
            return np.zeros((0, 3)), np.zeros(0)
        p_body = points[:, :3] @ self.rotation().T
        rng = np.linalg.norm(p_body, axis=1)
        on_ground = np.abs(p_body[:, 2] + self.height_m) < self.ground_tolerance_m
        keep = on_ground & (rng >= self.min_range_m) & (rng <= self.max_range_m)
        u = p_body[keep] / rng[keep, None]
        return u, self.doppler_sign * points[keep, 3]

    def to_radar_frame(self, u_body: np.ndarray) -> np.ndarray:
        """Inverse of the rotation, for the loopback simulator."""
        return u_body @ self.rotation()

"""Turns raw sensor messages into the shared log format (``landdvl.logio``).

The input is three byte streams, each stamped with the laptop's clock when it arrived:

- **Pico** (USB serial, text lines), see ``firmware/pico_logger``:
  ``I,<t_us>,<gx>,<gy>,<gz>,<ax>,<ay>,<az>``  IMU in rad/s and m/s^2, sensor axes
  ``E,<t_us>,<ticks>``                       encoder count since start (signed)
  ``P,<t_us>``                               GNSS PPS pulse edge
  ``S,<text>``                               status text, copied to the event file
- **GNSS** (USB serial, NMEA): GGA for position and fix type, GST for accuracy.
- **Radar** (TI data UART, binary): point cloud with Doppler.

Everything is written on one clock: seconds since the first message, laptop time. The Pico's own
microsecond clock is mapped onto the laptop clock (``ClockSync``), so IMU and encoder timing is as
precise as the Pico's, without USB jitter. The same is done for the radar (frame number times the
frame period) and the GNSS (UTC time in each GGA sentence): a few milliseconds of jitter on these
timestamps measurably worsens the outage test (found with ``landdvl.rig.loopback``).

What remains is each device's **constant** delay, which this can't see. Estimate it from data
later (e.g. GNSS PPS on the Pico, or by shifting a sensor's time until the filter fits best).
"""

from __future__ import annotations

import csv
import json
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from landdvl.logio import COLUMNS
from landdvl.rig import nmea
from landdvl.rig.ti_radar import PacketReader, RadarMount


@dataclass
class RigConfig:
    metres_per_tick: float = 0.001  # from the 20 m push calibration
    wheel_sign: float = 1.0  # -1 if pushing forward counts down
    imu_axes: tuple[str, str, str] = ("x", "y", "z")  # body x, y, z as sensor axes, e.g. "-y"
    radar: RadarMount = field(default_factory=RadarMount)
    start_yaw_rad: float = 0.0  # heading of the marked start line (east = 0, north = pi/2)
    static_start_s: float = 120.0
    notes: str = ""

    @classmethod
    def from_json(cls, path: str | Path) -> RigConfig:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        radar = RadarMount(**raw.pop("radar", {}))
        if "imu_axes" in raw:
            raw["imu_axes"] = tuple(raw["imu_axes"])
        return cls(radar=radar, **raw)


def axis_matrix(axes: tuple[str, str, str]) -> np.ndarray:
    """Rows pick (and maybe negate) sensor axes to form body x, y, z."""
    m = np.zeros((3, 3))
    for row, spec in enumerate(axes):
        sign = -1.0 if spec.startswith("-") else 1.0
        m[row, "xyz".index(spec.lstrip("+-"))] = sign
    if abs(abs(np.linalg.det(m)) - 1.0) > 1e-9:
        raise ValueError(f"imu_axes {axes} must use x, y and z once each")
    return m


class ClockSync:
    """Maps a device clock to the laptop clock.

    offset = laptop time - device time. USB only ever adds delay, so the smallest offset seen
    recently is the best estimate (the message that had the least delay). A window lets the
    estimate follow slow clock drift.
    """

    def __init__(self, window_s: float = 30.0):
        self.window_s = window_s
        self.samples: deque[tuple[float, float]] = deque()  # (host time, offset)
        self.best: deque[tuple[float, float]] = deque()  # monotonic min-queue

    def update(self, host_t: float, device_t: float) -> float:
        off = host_t - device_t
        self.samples.append((host_t, off))
        while self.best and self.best[-1][1] >= off:
            self.best.pop()
        self.best.append((host_t, off))
        while self.best[0][0] < host_t - self.window_s:
            self.best.popleft()
        while self.samples[0][0] < host_t - self.window_s:
            self.samples.popleft()
        return self.best[0][1]


class LogWriter:
    """Writes the log CSVs incrementally, so a crash or a flat battery keeps the data so far."""

    EXTRA = {
        "radar": ("t", "beam", "radial_velocity", "ux", "uy", "uz"),
        "imu_raw": ("t", "gx", "gy", "gz", "ax", "ay", "az"),
        "pps": ("t",),
        "events": ("t", "source", "text"),
    }

    def __init__(self, folder: str | Path):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.files = {}
        self.writers = {}
        self.counts: dict[str, int] = {}
        for name in ("imu", "wheel", "gnss", "radar", "imu_raw", "pps", "events"):
            cols = self.EXTRA.get(name, COLUMNS.get(name))
            f = open(self.folder / f"{name}.csv", "w", newline="", encoding="utf-8")  # noqa: SIM115
            self.files[name] = f
            self.writers[name] = csv.writer(f)
            self.writers[name].writerow(cols)
            self.counts[name] = 0
        self.gnss_raw = open(self.folder / "gnss_raw.nmea", "w", encoding="utf-8")  # noqa: SIM115

    def row(self, name: str, values: tuple) -> None:
        self.writers[name].writerow([f"{v:.6f}" if isinstance(v, float) else v for v in values])
        self.counts[name] += 1

    def flush(self) -> None:
        for f in self.files.values():
            f.flush()
        self.gnss_raw.flush()

    def close(self) -> None:
        for f in self.files.values():
            f.close()
        self.gnss_raw.close()


class Rig:
    """Feed it raw messages with laptop timestamps; it writes the log."""

    def __init__(self, folder: str | Path, config: RigConfig, t0: float | None = None):
        self.cfg = config
        self.writer = LogWriter(folder)
        self.folder = Path(folder)
        self.t0 = t0
        self.pico_clock = ClockSync()
        self.radar_clock = ClockSync()
        self.gnss_clock = ClockSync()
        self.last_utc: float | None = None
        self.utc_days = 0
        self.axes = axis_matrix(config.imu_axes)
        self.last_ticks: tuple[float, int] | None = None
        self.frame: nmea.LocalFrame | None = None
        self.last_gst: nmea.GST | None = None
        self.radar_reader = PacketReader()
        self.radar_counter = 0
        self.pico_bad_lines = 0
        self.write_meta()

    # ---------------------------------------------------------------- helpers
    def _t(self, host_t: float) -> float:
        if self.t0 is None:
            self.t0 = host_t
        return host_t - self.t0

    def event(self, host_t: float, source: str, text: str) -> None:
        self.writer.row("events", (self._t(host_t), source, text))

    # ---------------------------------------------------------------- Pico
    def on_pico_line(self, host_t: float, line: str) -> None:
        parts = line.strip().split(",")
        try:
            if parts[0] == "S":
                self.event(host_t, "pico", ",".join(parts[1:]))
                return
            device_t = int(parts[1]) * 1e-6
            t = self._t(device_t + self.pico_clock.update(host_t, device_t))
            if parts[0] == "I" and len(parts) == 8:
                vals = np.array([float(p) for p in parts[2:8]])
                gyro = self.axes @ vals[:3]
                acc = self.axes @ vals[3:]
                self.writer.row("imu", (t, gyro[2], acc[0], acc[1]))
                self.writer.row("imu_raw", (t, *map(float, vals)))
            elif parts[0] == "E" and len(parts) == 3:
                ticks = int(parts[2])
                if self.last_ticks is not None and t > self.last_ticks[0]:
                    t_prev, ticks_prev = self.last_ticks
                    dist = (ticks - ticks_prev) * self.cfg.metres_per_tick * self.cfg.wheel_sign
                    self.writer.row("wheel", (t, dist / (t - t_prev)))
                self.last_ticks = (t, ticks)
            elif parts[0] == "P":
                self.writer.row("pps", (t,))
            else:
                self.pico_bad_lines += 1
        except (ValueError, IndexError):
            self.pico_bad_lines += 1

    # ---------------------------------------------------------------- GNSS
    def on_gnss_line(self, host_t: float, line: str) -> None:
        t = self._t(host_t)
        self.writer.gnss_raw.write(f"{t:.6f} {line.strip()}\n")
        msg = nmea.parse(line)
        if isinstance(msg, nmea.GST):
            self.last_gst = msg
        elif isinstance(msg, nmea.GGA):
            utc = nmea.utc_seconds(msg.utc)
            if utc is not None:
                if self.last_utc is not None and utc < self.last_utc - 43200:
                    self.utc_days += 1  # passed midnight UTC
                self.last_utc = utc
                device_t = utc + 86400 * self.utc_days
                t = self._t(device_t + self.gnss_clock.update(host_t, device_t))
            if self.frame is None:
                if msg.quality == "none":
                    return  # wait for an RTK position as the origin
                self.frame = nmea.LocalFrame(msg.lat, msg.lon)
                self.write_meta()
            east, north = self.frame.to_local(msg.lat, msg.lon)
            sigma = nmea.DEFAULT_SIGMA[msg.quality]
            if self.last_gst is not None and self.last_gst.utc == msg.utc:
                sigma = max(sigma * 0.5, self.last_gst.sigma)
            self.writer.row("gnss", (t, east, north, msg.quality, sigma))

    # ---------------------------------------------------------------- radar
    def on_radar_bytes(self, host_t: float, data: bytes) -> None:
        period = self.cfg.radar.frame_period_s
        for frame in self.radar_reader.feed(data):
            if period > 0:
                device_t = frame.frame_number * period
                t = self._t(device_t + self.radar_clock.update(host_t, device_t))
            else:
                t = self._t(host_t)
            u, radial = self.cfg.radar.ground_points(frame.points)
            for k in range(len(radial)):
                self.writer.row(
                    "radar", (t, self.radar_counter, float(radial[k]), *map(float, u[k]))
                )
                self.radar_counter += 1

    # ---------------------------------------------------------------- meta
    def write_meta(self, extra: dict | None = None) -> None:
        meta = {
            "source": "measurement rig",
            "start_pose": {"yaw": self.cfg.start_yaw_rad},
            "static_start_s": self.cfg.static_start_s,
            "radar_mount": asdict(self.cfg.radar),
            "radar_format": "point cloud: radial_velocity = -(u . v_body), u in body frame",
            "rig_config": {k: v for k, v in asdict(self.cfg).items() if k not in ("radar",)},
            "gnss_origin": None
            if self.frame is None
            else {"lat": self.frame.lat0, "lon": self.frame.lon0},
            "notes": self.cfg.notes,
        }
        if extra:
            meta.update(extra)
        with open(self.folder / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def close(self) -> dict:
        stats = {
            "rows": dict(self.writer.counts),
            "pico_bad_lines": self.pico_bad_lines,
            "radar_bad_packets": self.radar_reader.bad_packets,
        }
        self.write_meta({"stats": stats})
        self.writer.close()
        return stats

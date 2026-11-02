"""Turn a simulated log into the raw bytes the real sensors would send, and log them with ``Rig``.

This tests the whole logger without hardware: simulator -> Pico lines + NMEA + TI radar packets ->
``Rig`` -> log folder -> ``landdvl.evaluate``. The result should match the simulated log.

    python -m landdvl.rig.loopback logs/sim01 logs/sim01_loopback
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from landdvl.logio import read_log
from landdvl.rig import nmea
from landdvl.rig.core import Rig, RigConfig
from landdvl.rig.ti_radar import build_packet

ORIGIN = (55.6761, 12.5683)  # any latitude/longitude works; this one is Copenhagen
PICO_CLOCK_START = 1234.5  # s; the Pico's clock has its own zero
USB_DELAY = 0.002  # s; minimum USB delay, plus random jitter below


def streams(folder: str | Path, config: RigConfig, seed: int = 0):
    """Yield (laptop time, source, payload) sorted by laptop time."""
    log = read_log(folder)
    rng = np.random.default_rng(seed)
    events = []

    last: dict[str, float] = {}

    def host(t: float, port: str = "pico", delay: float = 0.0) -> float:
        """Arrival time on the laptop: delay plus jitter, but a port never reorders messages."""
        arrival = t + USB_DELAY + delay + rng.exponential(0.003)
        arrival = max(arrival, last.get(port, -1.0))
        last[port] = arrival
        return arrival

    inv_axes = np.linalg.inv(_axes(config))
    pico = []
    for t, gz, ax, ay in log.imu:
        gyro = inv_axes @ np.array([0.0, 0.0, gz])
        acc = inv_axes @ np.array([ax, ay, 9.81])
        vals = ",".join(f"{v:.6f}" for v in (*gyro, *acc))
        pico.append((t, f"I,{int((t + PICO_CLOCK_START) * 1e6)},{vals}"))

    dist = 0.0
    prev_t = None
    for t, speed in log.wheel:
        if prev_t is not None:
            dist += speed * (t - prev_t)
        prev_t = t
        ticks = round(dist / config.metres_per_tick * config.wheel_sign)
        pico.append((t, f"E,{int((t + PICO_CLOCK_START) * 1e6)},{ticks}"))
    pico.sort(key=lambda e: e[0])
    events += [(host(t), "pico", line) for t, line in pico]

    frame = nmea.LocalFrame(*ORIGIN)
    raw_quality = {"fix": 4, "float": 5, "none": 1}
    for (t, x, y, _), q in zip(log.gnss_xy, log.gnss_quality, strict=True):
        lat, lon = frame.to_latlon(x, y)
        secs = 36000 + t
        utc = f"{int(secs // 3600):02d}{int(secs % 3600 // 60):02d}{secs % 60:05.2f}"
        events.append(
            (host(t, "gnss", 0.03), "gnss", nmea.format_gga(utc, lat, lon, raw_quality[q]))
        )

    mount = config.radar
    beams = log.beam_vectors()
    groups: dict[float, list[tuple[int, float]]] = {}
    for t, beam, radial in log.radar[:, :3]:
        groups.setdefault(float(t), []).append((int(beam), float(radial)))
    period = 1.0 / float(log.meta.get("rates_hz", {}).get("radar", 20.0))
    config.radar.frame_period_s = period
    for t, items in sorted(groups.items()):
        n = round(t / period)  # frames without detections are not in the log, but still count
        pts = []
        for beam, radial in items:
            u = beams[beam]
            r = mount.height_m / -u[2]
            p = mount.to_radar_frame(u * r)
            pts.append((*p, radial / mount.doppler_sign))
        events.append((host(t, "radar", 0.01), "radar", build_packet(n, np.array(pts))))

    events.sort(key=lambda e: e[0])
    return events, log


def _axes(config: RigConfig) -> np.ndarray:
    from landdvl.rig.core import axis_matrix

    return axis_matrix(config.imu_axes)


def run(sim_folder: str | Path, out: str | Path, config: RigConfig | None = None) -> dict:
    config = config or RigConfig()
    events, log = streams(sim_folder, config)
    # Same start heading and static period as the simulation, as you'd note them on the rig.
    config.start_yaw_rad = float(log.meta.get("start_pose", {}).get("yaw", 0.0))
    config.static_start_s = float(log.meta.get("static_start_s", 0.0))
    rig = Rig(out, config, t0=0.0)
    for host_t, source, payload in events:
        if source == "pico":
            rig.on_pico_line(host_t, payload)
        elif source == "gnss":
            rig.on_gnss_line(host_t, payload)
        else:
            # Split packets like a UART would deliver them.
            for i in range(0, len(payload), 64):
                rig.on_radar_bytes(host_t, payload[i : i + 64])
    return rig.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Log a simulated run through the rig logger.")
    parser.add_argument("sim_log")
    parser.add_argument("out")
    args = parser.parse_args()
    stats = run(args.sim_log, args.out)
    print(stats)
    print(f"Now: python -m landdvl.evaluate {args.out}")


if __name__ == "__main__":
    main()

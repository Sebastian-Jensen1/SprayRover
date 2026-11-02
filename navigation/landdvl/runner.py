"""Replay a log through the filter, optionally with GNSS switched off in chosen time windows."""

from __future__ import annotations

import bisect
from dataclasses import dataclass, replace

import numpy as np

from landdvl.ekf import PX, PY, YAW, FilterConfig, PlanarEKF, radar_body_velocity
from landdvl.logio import Log

IMU, GNSS, WHEEL, RADAR = 0, 1, 2, 3
RADAR_SPEED_MAX_AGE = 0.25  # s; a radar speed older than this is not used for slip checks


@dataclass
class Snapshot:
    t: float
    x: np.ndarray
    P: np.ndarray


class Replay:
    def __init__(self, log: Log):
        self.log = log
        self.beams = log.beam_vectors() if "radar" in log.meta else np.zeros((0, 3))
        events: list[tuple[float, int, object]] = []
        for row in log.imu:
            events.append((row[0], IMU, (row[1], row[2], row[3])))
        for row in log.wheel:
            events.append((row[0], WHEEL, row[1]))
        for row, quality in zip(log.gnss_xy, log.gnss_quality, strict=True):
            if quality != "none":
                events.append((row[0], GNSS, (row[1], row[2], row[3])))
        # Radar rows are either fixed beams (t, beam, value) or point-cloud detections with
        # their own direction (t, beam, value, ux, uy, uz); beam is then just a counter.
        has_dirs = log.radar.shape[1] >= 6
        radar_groups: dict[float, tuple[list[np.ndarray], list[float]]] = {}
        for row in log.radar:
            dirs, vals = radar_groups.setdefault(float(row[0]), ([], []))
            dirs.append(row[3:6] if has_dirs else self.beams[int(row[1])])
            vals.append(float(row[2]))
        for t, (dirs, vals) in radar_groups.items():
            events.append((t, RADAR, (np.array(dirs), np.array(vals))))
        # IMU first at equal timestamps, so aiding corrects the newest prediction.
        events.sort(key=lambda e: (e[0], e[1]))
        self.events = events
        self.times = [e[0] for e in events]
        self.static_until = float(log.meta.get("static_start_s", 0.0))

    def initial_filter(self, config: FilterConfig) -> PlanarEKF:
        g = self.log.gnss_xy
        first = g[g[:, 0] < g[0, 0] + 1.0]
        pose = self.log.meta.get("start_pose", {})
        x0 = np.zeros(8)
        x0[PX], x0[PY] = first[:, 1].mean(), first[:, 2].mean()
        x0[YAW] = pose.get("yaw", 0.0)
        pos_sigma = max(0.05, float(first[:, 3].mean()))
        p0 = np.array([pos_sigma, pos_sigma, 0.01, 0.01, 0.1, 0.01, 0.1, 0.1]) ** 2
        return PlanarEKF(config, x0, p0)

    def run(
        self,
        ekf: PlanarEKF,
        t_start: float,
        t_end: float,
        gnss_off: tuple[float, float] | None = None,
        record_every: float = 0.1,
        snapshot_every: float | None = None,
    ) -> tuple[np.ndarray, list[Snapshot]]:
        """Process events in [t_start, t_end). Returns estimates [t, x, y, yaw] and snapshots."""
        i = bisect.bisect_left(self.times, t_start)
        last_imu_t: float | None = None
        radar_speed: tuple[float, float] | None = None  # (time, forward ground speed)
        next_record = t_start
        next_snap = t_start
        out: list[tuple[float, float, float, float]] = []
        snaps: list[Snapshot] = []
        while i < len(self.events) and self.events[i][0] < t_end:
            t, kind, data = self.events[i]
            i += 1
            if kind == IMU:
                if last_imu_t is not None:
                    ekf.predict(*data, t - last_imu_t)
                last_imu_t = t
                if t < self.static_until:
                    ekf.update_zero_velocity()
                    ekf.update_zero_rate(data[0])
            elif kind == GNSS:
                if gnss_off is None or not (gnss_off[0] <= t < gnss_off[1]):
                    ekf.update_gnss(*data)
            elif kind == WHEEL and t >= self.static_until:
                fresh = radar_speed is not None and t - radar_speed[0] <= RADAR_SPEED_MAX_AGE
                ekf.update_wheel(data, radar_speed[1] if fresh else None)
            elif kind == RADAR and t >= self.static_until:
                dirs, vals = data
                ekf.update_radar(dirs, vals)
                v_radar = radar_body_velocity(dirs, vals)
                if v_radar is not None:
                    radar_speed = (t, float(v_radar[0]))
            if t >= next_record:
                out.append((t, ekf.x[PX], ekf.x[PY], ekf.x[YAW]))
                next_record += record_every
            if snapshot_every is not None and t >= next_snap:
                snaps.append(Snapshot(t, ekf.x.copy(), ekf.P.copy()))
                next_snap += snapshot_every
        return np.array(out), snaps


def resume(snapshot: Snapshot, config: FilterConfig) -> PlanarEKF:
    ekf = PlanarEKF(config, snapshot.x, np.ones(8))
    ekf.P = snapshot.P.copy()
    return ekf


def variant(base: FilterConfig, **changes) -> FilterConfig:
    return replace(base, **changes)

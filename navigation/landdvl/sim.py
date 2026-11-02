"""Simulate the measurement rig driving through a garden and write a log.

The trolley drives lawnmower lanes across the garden, passing under trees and along the house
wall. The simulator writes exactly the files a real rig would (see ``logio``) plus ``truth.csv``,
so the fusion and evaluation code can be developed and tested before any hardware exists.

    python -m landdvl.sim --out logs/sim01 --seed 1
"""

from __future__ import annotations

import argparse
import math
from dataclasses import asdict, dataclass

import numpy as np

from landdvl.logio import write_log
from landdvl.world import Garden

TRUTH_RATE = 400.0


@dataclass(frozen=True)
class SensorModel:
    """Noise levels: typical for a cheap MEMS IMU, a pushed trolley wheel and a TI mmWave radar."""

    imu_rate: float = 200.0
    gyro_noise: float = 0.002  # rad/s, std per sample
    gyro_bias: float = 0.005  # rad/s, initial bias (std)
    gyro_bias_walk: float = 0.0002  # rad/s per sqrt(s)
    acc_noise: float = 0.05  # m/s^2, std per sample
    acc_bias: float = 0.05  # m/s^2, initial bias (std)
    acc_bias_walk: float = 0.002  # m/s^2 per sqrt(s)

    wheel_rate: float = 50.0
    wheel_noise: float = 0.01  # m/s
    wheel_scale_error: float = 0.015  # wheel circumference error (fraction)
    wheel_slip_burst: float = 0.25  # extra slip in wet/soft patches (fraction)

    gnss_rate: float = 5.0
    gnss_fix_sigma: float = 0.015  # m
    gnss_float_sigma: float = 0.30  # m
    gnss_multipath_prob: float = 0.10  # chance that a float sample has a multipath jump
    gnss_multipath_jump: float = 1.5  # m, typical jump size

    radar_rate: float = 20.0
    radar_noise: float = 0.01  # m/s floor
    radar_noise_rel: float = 0.01  # plus this fraction of the speed
    radar_dropout: float = 0.05
    radar_tilt_deg: float = 30.0  # beams tilted this far from straight down
    radar_azimuths_deg: tuple[float, ...] = (45.0, 135.0, 225.0, 315.0)

    def beam_unit_vectors(self) -> np.ndarray:
        tilt = math.radians(self.radar_tilt_deg)
        beams = []
        for az_deg in self.radar_azimuths_deg:
            az = math.radians(az_deg)
            beams.append(
                [math.sin(tilt) * math.cos(az), math.sin(tilt) * math.sin(az), -math.cos(tilt)]
            )
        return np.array(beams)


# --------------------------------------------------------------------------------------------
# Trajectory
# --------------------------------------------------------------------------------------------


def _straight_profile(length: float, v_end: float, cruise: float, accel: float) -> list[float]:
    """Speed samples for a straight that starts and ends at v_end with a trapezoid in between."""
    dt = 1.0 / TRUTH_RATE
    ramp_dist = (cruise**2 - v_end**2) / (2 * accel)
    if 2 * ramp_dist > length:
        cruise = math.sqrt(v_end**2 + accel * length)
        ramp_dist = length / 2
    speeds, v, travelled = [], v_end, 0.0
    while travelled < length:
        remaining = length - travelled
        braking = (v**2 - v_end**2) / (2 * accel)
        if remaining <= braking:
            v = max(v_end, v - accel * dt)
        elif v < cruise:
            v = min(cruise, v + accel * dt)
        speeds.append(v)
        travelled += v * dt
    return speeds


def lawnmower_commands(
    garden: Garden,
    margin: float = 3.0,
    spacing: float = 1.5,
    cruise: float = 0.5,
    turn_speed: float = 0.3,
    accel: float = 0.4,
    static_time: float = 30.0,
) -> tuple[np.ndarray, np.ndarray, tuple[float, float, float]]:
    """Speed v(t) and yaw rate w(t) at TRUTH_RATE for lanes from the top of the garden down."""
    v_list: list[float] = [0.0] * int(static_time * TRUTH_RATE)
    w_list: list[float] = [0.0] * len(v_list)

    # Gentle start from standstill to turn speed.
    ramp = int(turn_speed / accel * TRUTH_RATE)
    v_list += [turn_speed * (i + 1) / ramp for i in range(ramp)]
    w_list += [0.0] * ramp

    lane_length = garden.width - 2 * margin
    n_lanes = int((garden.height - 2 * margin) // spacing) + 1
    radius = spacing / 2
    for lane in range(n_lanes):
        speeds = _straight_profile(lane_length, turn_speed, cruise, accel)
        v_list += speeds
        w_list += [0.0] * len(speeds)
        if lane < n_lanes - 1:
            n_turn = int(math.pi * radius / turn_speed * TRUTH_RATE)
            direction = -1.0 if lane % 2 == 0 else 1.0  # right turn, then left turn, ...
            v_list += [turn_speed] * n_turn
            w_list += [direction * turn_speed / radius] * n_turn

    ramp_down = [turn_speed * (1 - (i + 1) / ramp) for i in range(ramp)]
    v_list += ramp_down + [0.0] * int(static_time * TRUTH_RATE)
    w_list += [0.0] * (len(ramp_down) + int(static_time * TRUTH_RATE))
    start = (margin, garden.height - margin, 0.0)  # top-left corner, open sky, heading east
    return np.array(v_list), np.array(w_list), start


def integrate(v: np.ndarray, w: np.ndarray, start: tuple[float, float, float]) -> np.ndarray:
    """Truth states [t, x, y, yaw, vx, vy, speed, yaw_rate, accel_forward]."""
    dt = 1.0 / TRUTH_RATE
    n = len(v)
    out = np.zeros((n, 9))
    x, y, yaw = start
    for i in range(n):
        if i > 0:
            yaw_mid = yaw + 0.5 * w[i - 1] * dt
            x += v[i - 1] * math.cos(yaw_mid) * dt
            y += v[i - 1] * math.sin(yaw_mid) * dt
            yaw += w[i - 1] * dt
        accel = (v[min(i + 1, n - 1)] - v[max(i - 1, 0)]) / (2 * dt)
        out[i] = (
            i * dt,
            x,
            y,
            yaw,
            v[i] * math.cos(yaw),
            v[i] * math.sin(yaw),
            v[i],
            w[i],
            accel,
        )
    return out


# --------------------------------------------------------------------------------------------
# Sensors
# --------------------------------------------------------------------------------------------


def _wet_patch(garden: Garden, x: float, y: float) -> bool:
    """Soft, wet ground under the trees, where wheels slip."""
    return any(math.hypot(x - t.x, y - t.y) < t.canopy_radius + 1.0 for t in garden.trees)


def simulate(garden: Garden, model: SensorModel, seed: int = 1) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    v, w, start = lawnmower_commands(garden)
    truth = integrate(v, w, start)
    n = len(truth)

    tables: dict[str, list[tuple]] = {k: [] for k in ("truth", "imu", "wheel", "gnss", "radar")}

    # Truth at 50 Hz is plenty for evaluation.
    for row in truth[:: int(TRUTH_RATE / 50)]:
        tables["truth"].append(tuple(round(float(c), 5) for c in row[:6]))

    # IMU with slowly wandering biases.
    step = int(TRUTH_RATE / model.imu_rate)
    dt_imu = 1.0 / model.imu_rate
    bg = rng.normal(0, model.gyro_bias)
    ba = rng.normal(0, model.acc_bias, 2)
    for row in truth[::step]:
        t, _, _, _, _, _, speed, yaw_rate, accel = row
        bg += rng.normal(0, model.gyro_bias_walk * math.sqrt(dt_imu))
        ba += rng.normal(0, model.acc_bias_walk * math.sqrt(dt_imu), 2)
        tables["imu"].append(
            (
                round(t, 5),
                yaw_rate + bg + rng.normal(0, model.gyro_noise),
                accel + ba[0] + rng.normal(0, model.acc_noise),
                speed * yaw_rate + ba[1] + rng.normal(0, model.acc_noise),
            )
        )

    # Wheel encoder: scale error, noise and slip bursts on wet ground.
    scale = 1.0 + model.wheel_scale_error
    for row in truth[:: int(TRUTH_RATE / model.wheel_rate)]:
        t, x, y, _, _, _, speed, _, _ = row
        slip = model.wheel_slip_burst * rng.uniform(0.3, 1.0) if _wet_patch(garden, x, y) else 0.0
        measured = speed * scale * (1.0 + slip) + rng.normal(0, model.wheel_noise)
        tables["wheel"].append((round(t, 5), measured if speed > 0 else 0.0))

    # GNSS: quality depends on where the antenna is; float has occasional multipath jumps.
    for row in truth[:: int(TRUTH_RATE / model.gnss_rate)]:
        t, x, y = row[:3]
        quality = garden.gnss_quality(x, y)
        if quality == "none":
            continue
        sigma = model.gnss_fix_sigma if quality == "fix" else model.gnss_float_sigma
        ex, ey = rng.normal(0, sigma, 2)
        if quality == "float" and rng.random() < model.gnss_multipath_prob:
            angle = rng.uniform(0, 2 * math.pi)
            jump = rng.uniform(0.5, 1.5) * model.gnss_multipath_jump
            ex += jump * math.cos(angle)
            ey += jump * math.sin(angle)
        tables["gnss"].append((round(t, 5), x + ex, y + ey, quality, sigma))

    # Radar: each beam sees the ground move past at -v (body frame) projected on the beam.
    beams = model.beam_unit_vectors()
    for row in truth[:: int(TRUTH_RATE / model.radar_rate)]:
        t, speed = row[0], row[6]
        v_body = np.array([speed, 0.0, 0.0])
        for i, u in enumerate(beams):
            if rng.random() < model.radar_dropout:
                continue
            sigma = model.radar_noise + model.radar_noise_rel * abs(speed)
            tables["radar"].append((round(t, 5), i, float(-u @ v_body + rng.normal(0, sigma))))

    meta = {
        "source": "simulator",
        "seed": seed,
        "duration_s": round(n / TRUTH_RATE, 2),
        "rates_hz": {
            "imu": model.imu_rate,
            "wheel": model.wheel_rate,
            "gnss": model.gnss_rate,
            "radar": model.radar_rate,
        },
        "radar": {
            "beam_unit_vectors": beams.round(6).tolist(),
            "convention": "radial_velocity = -(u . v_body); u points from sensor to ground",
        },
        "start_pose": {"x": start[0], "y": start[1], "yaw": start[2]},
        "static_start_s": 30.0,
        "garden": {
            "width": garden.width,
            "height": garden.height,
            "trees": [asdict(t) for t in garden.trees],
            "wall_y": 0.0,
        },
        "sensor_model": {k: v for k, v in asdict(model).items() if k != "radar_azimuths_deg"},
    }
    return tables, meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate a measurement-rig log.")
    parser.add_argument("--out", default="logs/sim01", help="output folder")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    tables, meta = simulate(Garden(), SensorModel(), seed=args.seed)
    folder = write_log(args.out, tables, meta)
    print(f"Wrote {folder} ({meta['duration_s']} s, {len(tables['gnss'])} GNSS samples)")


if __name__ == "__main__":
    main()

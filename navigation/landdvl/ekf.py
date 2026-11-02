"""Planar inertial navigation filter (extended Kalman filter, error-state style).

State (8): position x, y [m]; velocity vx, vy in the local ENU frame [m/s]; heading yaw [rad];
gyro bias [rad/s]; accelerometer bias in the body frame bx, by [m/s^2].

- **Predict** with the IMU (yaw rate + body accelerations) at the IMU rate.
- **Correct** with any of: GNSS position, wheel speed (plus "no sideways motion"), and radar
  beam velocities. Each aid can be switched off, which is how the evaluation compares
  "IMU + wheel" against "IMU + wheel + radar".

The model is 2D: it assumes level ground and ignores lever arms between sensors. That is enough
to compare aiding sources; the real rig will need tilt and lever arms added.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

PX, PY, VX, VY, YAW, BG, BAX, BAY = range(8)
N = 8
CHI2_2DOF_99 = 9.21


def _rot(yaw: float) -> np.ndarray:
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s], [s, c]])


def _wrap(angle: float) -> float:
    return (angle + math.pi) % (2 * math.pi) - math.pi


@dataclass
class FilterConfig:
    use_gnss: bool = True
    use_wheel: bool = True
    use_radar: bool = True
    gyro_noise: float = 0.002
    acc_noise: float = 0.05
    gyro_bias_walk: float = 0.0002
    acc_bias_walk: float = 0.002
    wheel_sigma: float = 0.05  # m/s; covers noise and moderate slip
    lateral_sigma: float = 0.03  # m/s; "the trolley doesn't slide sideways"
    radar_sigma: float = 0.02  # m/s per beam
    gnss_gate: bool = True  # reject GNSS samples that disagree strongly (multipath)
    gnss_max_rejects: int = 5  # after this many rejections in a row, accept again
    # Wheel-slip detection: skip a wheel update when it disagrees with the radar's own
    # ground-speed estimate by more than slip_abs + slip_rel * |radar speed|.
    slip_detection: bool = True
    slip_abs: float = 0.03  # m/s
    slip_rel: float = 0.05  # fraction of the speed; must exceed the wheel calibration error


class PlanarEKF:
    def __init__(self, config: FilterConfig, x0: np.ndarray, p0_diag: np.ndarray):
        self.cfg = config
        self.x = x0.astype(float).copy()
        self.P = np.diag(p0_diag.astype(float))
        self.last_acc_body = np.zeros(2)
        self.gnss_rejected_in_row = 0
        self.wheel_updates = 0
        self.wheel_rejected_slip = 0

    # ---------------------------------------------------------------- predict
    def predict(self, gyro_z: float, acc_x: float, acc_y: float, dt: float) -> None:
        x = self.x
        rate = gyro_z - x[BG]
        a_body = np.array([acc_x - x[BAX], acc_y - x[BAY]])
        R = _rot(x[YAW])
        a_world = R @ a_body

        x[PX] += x[VX] * dt + 0.5 * a_world[0] * dt * dt
        x[PY] += x[VY] * dt + 0.5 * a_world[1] * dt * dt
        x[VX] += a_world[0] * dt
        x[VY] += a_world[1] * dt
        x[YAW] = _wrap(x[YAW] + rate * dt)
        self.last_acc_body = a_body

        dR = np.array([[-R[1, 0], -R[0, 0]], [R[0, 0], -R[1, 0]]])  # d(R)/d(yaw)
        F = np.eye(N)
        F[PX, VX] = F[PY, VY] = dt
        F[VX : VY + 1, YAW] = dR @ a_body * dt
        F[VX : VY + 1, BAX : BAY + 1] = -R * dt
        F[YAW, BG] = -dt

        c = self.cfg
        Q = np.zeros((N, N))
        Q[VX, VX] = Q[VY, VY] = (c.acc_noise * dt) ** 2
        Q[YAW, YAW] = (c.gyro_noise * dt) ** 2
        Q[BG, BG] = c.gyro_bias_walk**2 * dt
        Q[BAX, BAX] = Q[BAY, BAY] = c.acc_bias_walk**2 * dt
        self.P = F @ self.P @ F.T + Q

    # ---------------------------------------------------------------- update helpers
    def _update(self, z: np.ndarray, h: np.ndarray, H: np.ndarray, Rm: np.ndarray, gate=None):
        y = z - h
        S = H @ self.P @ H.T + Rm
        if gate is not None and float(y @ np.linalg.solve(S, y)) > gate:
            return False
        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ y
        self.x += dx
        self.x[YAW] = _wrap(self.x[YAW])
        I_KH = np.eye(N) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ Rm @ K.T
        return True

    def _body_velocity(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """v_body = R^T v_world, plus its Jacobians w.r.t. v_world and yaw."""
        R = _rot(self.x[YAW])
        v_world = self.x[VX : VY + 1]
        Rt = R.T
        dRt = np.array([[-R[1, 0], R[0, 0]], [-R[0, 0], -R[1, 0]]])  # d(R^T)/d(yaw)
        return Rt @ v_world, Rt, dRt @ v_world

    # ---------------------------------------------------------------- aiding sources
    def update_gnss(self, x: float, y: float, sigma: float) -> bool:
        if not self.cfg.use_gnss:
            return False
        H = np.zeros((2, N))
        H[0, PX] = H[1, PY] = 1.0
        # Reject single GNSS jumps (multipath), but if several samples in a row disagree, the
        # filter itself has drifted and is too confident: accept again so it can recover.
        use_gate = self.cfg.gnss_gate and self.gnss_rejected_in_row < self.cfg.gnss_max_rejects
        gate = CHI2_2DOF_99 if use_gate else None
        accepted = self._update(
            np.array([x, y]), self.x[PX : PY + 1].copy(), H, np.eye(2) * sigma**2, gate
        )
        self.gnss_rejected_in_row = 0 if accepted else self.gnss_rejected_in_row + 1
        return accepted

    def update_wheel(self, speed: float, radar_speed: float | None = None) -> bool:
        """Wheel forward speed plus "no sideways motion". With `radar_speed` (the radar's own
        forward ground speed, measured at about the same time) slipping wheels are skipped."""
        if not self.cfg.use_wheel:
            return False
        if self.cfg.slip_detection and self.cfg.use_radar and radar_speed is not None:
            limit = self.cfg.slip_abs + self.cfg.slip_rel * abs(radar_speed)
            if abs(speed - radar_speed) > limit:
                self.wheel_rejected_slip += 1
                return False
        self.wheel_updates += 1
        v_body, dvb_dv, dvb_dyaw = self._body_velocity()
        H = np.zeros((2, N))
        H[:, VX : VY + 1] = dvb_dv
        H[:, YAW] = dvb_dyaw
        Rm = np.diag([self.cfg.wheel_sigma**2, self.cfg.lateral_sigma**2])
        return self._update(np.array([speed, 0.0]), v_body, H, Rm)

    def update_radar(self, beams: np.ndarray, radial: np.ndarray) -> bool:
        """beams: (k, 3) unit vectors in body frame; radial: (k,) measured -(u . v_body)."""
        if not self.cfg.use_radar or len(radial) == 0:
            return False
        v_body, dvb_dv, dvb_dyaw = self._body_velocity()
        U = -beams[:, :2]  # vertical velocity assumed zero on level ground
        H = np.zeros((len(radial), N))
        H[:, VX : VY + 1] = U @ dvb_dv
        H[:, YAW] = U @ dvb_dyaw
        Rm = np.eye(len(radial)) * self.cfg.radar_sigma**2
        return self._update(np.asarray(radial, dtype=float), U @ v_body, H, Rm)

    def update_zero_velocity(self) -> bool:
        """Use while standing still (e.g. the static start) to learn the IMU biases."""
        H = np.zeros((2, N))
        H[0, VX] = H[1, VY] = 1.0
        return self._update(np.zeros(2), self.x[VX : VY + 1].copy(), H, np.eye(2) * 0.005**2)

    def update_zero_rate(self, gyro_z: float) -> bool:
        """While standing still the gyro reads only its bias."""
        H = np.zeros((1, N))
        H[0, BG] = 1.0
        return self._update(
            np.array([gyro_z]), np.array([self.x[BG]]), H, np.eye(1) * self.cfg.gyro_noise**2
        )


def radar_body_velocity(beams: np.ndarray, radial: np.ndarray) -> np.ndarray | None:
    """Least-squares body velocity (forward, left) from one radar scan, without the filter.

    Each beam measures radial = -(u . v_body) with zero vertical velocity. Needs two beams with
    different horizontal directions; with a single beam, sideways motion is assumed to be zero.
    """
    if len(radial) == 0:
        return None
    U = -np.asarray(beams, dtype=float)[:, :2]
    z = np.asarray(radial, dtype=float)
    if len(z) == 1 or np.linalg.matrix_rank(U) < 2:
        ux = U[:, 0]
        if np.allclose(ux, 0):
            return None
        return np.array([float(ux @ z / (ux @ ux)), 0.0])
    v, *_ = np.linalg.lstsq(U, z, rcond=None)
    return v

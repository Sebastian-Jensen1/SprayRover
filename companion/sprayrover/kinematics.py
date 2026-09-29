"""Kinematics for the 4-wheel, independently steered rover.

Every wheel has a steering servo and a drive motor, so the rover can follow any planar body
motion (a "twist": forward speed ``vx``, sideways speed ``vy`` and yaw rate ``wz``).

- :func:`inverse_kinematics` turns a twist into a steering angle and speed for each wheel.
- :func:`forward_kinematics` estimates the twist from measured wheel angles and speeds
  (wheel odometry, later used by the ESKF).
- :func:`ackermann`, :func:`spin` and :func:`crab` build twists for the three driving modes.

Conventions (see ``CLAUDE.md``): SI units, body frame at the rover centre, x forward, y left,
z up. Steering angles are measured from the body x axis, positive counter-clockwise (to the left).

The module is pure Python on purpose, so the same code runs on the companion computer, in the
simulator and in the browser prototype (Pyodide).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

WHEEL_NAMES = ("front_left", "front_right", "rear_left", "rear_right")

# Below this wheel speed (m/s) a wheel is treated as standing still, and keeps its previous
# steering angle instead of snapping to an arbitrary direction.
STANDSTILL_SPEED = 1e-6


@dataclass(frozen=True)
class RoverGeometry:
    wheelbase: float  # front axle to rear axle
    track_width: float  # left wheel centre to right wheel centre
    wheel_radius: float
    max_steer_angle: float  # steering limit, symmetric: [-max, +max]
    max_wheel_speed: float  # ground speed limit of one wheel (m/s)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> RoverGeometry:
        """Build the geometry from the dictionary returned by ``load_rover_config()``."""
        geometry = config["geometry"]
        return cls(
            wheelbase=geometry["wheelbase"],
            track_width=geometry["track_width"],
            wheel_radius=geometry["wheel_radius"],
            max_steer_angle=geometry["max_steer_angle"],
            max_wheel_speed=config["limits"]["max_speed"],
        )

    def wheel_positions(self) -> tuple[tuple[float, float], ...]:
        """(x, y) of each wheel's steering axis in the body frame, ordered as ``WHEEL_NAMES``."""
        x = self.wheelbase / 2
        y = self.track_width / 2
        return ((x, y), (x, -y), (-x, y), (-x, -y))


@dataclass(frozen=True)
class Twist:
    """Planar body motion: vx, vy in m/s, wz in rad/s."""

    vx: float = 0.0
    vy: float = 0.0
    wz: float = 0.0


@dataclass(frozen=True)
class WheelState:
    angle: float  # steering angle (rad)
    speed: float  # signed ground speed along the wheel's rolling direction (m/s)

    def angular_velocity(self, wheel_radius: float) -> float:
        """Wheel rotation speed in rad/s, as commanded to the motor controller."""
        return self.speed / wheel_radius


@dataclass(frozen=True)
class WheelCommands:
    wheels: tuple[WheelState, ...]  # ordered as WHEEL_NAMES
    scale: float  # factor the twist was scaled by to respect max_wheel_speed (1.0 = unscaled)
    feasible: bool  # False if a steering angle had to be clamped to max_steer_angle


def _wrap_angle(angle: float) -> float:
    """Wrap an angle to [-pi, pi)."""
    return (angle + math.pi) % (2 * math.pi) - math.pi


def _choose_wheel_state(
    angle: float, speed: float, previous_angle: float, max_steer: float
) -> tuple[WheelState, bool]:
    """Pick between (angle, speed) and the equivalent (angle + pi, -speed).

    Prefers the option within the steering limit that is closest to the previous angle, so the
    servos move as little as possible and never swing a full half-turn when the rover reverses.
    """
    candidates = [
        (_wrap_angle(angle), speed),
        (_wrap_angle(angle + math.pi), -speed),
    ]
    within_limits = [c for c in candidates if abs(c[0]) <= max_steer + 1e-9]
    if within_limits:
        best = min(within_limits, key=lambda c: abs(_wrap_angle(c[0] - previous_angle)))
        return WheelState(*best), True
    # Neither option is reachable: clamp the one that needs the least steering.
    best = min(candidates, key=lambda c: abs(c[0]))
    clamped = max(-max_steer, min(max_steer, best[0]))
    return WheelState(clamped, best[1]), False


def inverse_kinematics(
    twist: Twist,
    geometry: RoverGeometry,
    previous_angles: Sequence[float] | None = None,
) -> WheelCommands:
    """Compute steering angle and speed for each wheel so the body follows ``twist``.

    The velocity of a wheel at body position (x, y) is ``(vx - wz*y, vy + wz*x)``. The wheel is
    steered along that vector and driven at its length. If any wheel would exceed
    ``max_wheel_speed``, the whole twist is scaled down so the path shape stays the same.
    """
    if previous_angles is None:
        previous_angles = (0.0,) * len(WHEEL_NAMES)

    velocities = [
        (twist.vx - twist.wz * y, twist.vy + twist.wz * x) for x, y in geometry.wheel_positions()
    ]
    fastest = max(math.hypot(vx, vy) for vx, vy in velocities)
    scale = 1.0
    if fastest > geometry.max_wheel_speed:
        scale = geometry.max_wheel_speed / fastest

    wheels = []
    feasible = True
    for (vx, vy), previous in zip(velocities, previous_angles, strict=True):
        speed = math.hypot(vx, vy) * scale
        if speed < STANDSTILL_SPEED:
            wheels.append(WheelState(previous, 0.0))
            continue
        state, ok = _choose_wheel_state(
            math.atan2(vy, vx), speed, previous, geometry.max_steer_angle
        )
        wheels.append(state)
        feasible = feasible and ok
    return WheelCommands(wheels=tuple(wheels), scale=scale, feasible=feasible)


def forward_kinematics(wheels: Sequence[WheelState], geometry: RoverGeometry) -> Twist:
    """Estimate the body twist from measured wheel angles and speeds (least squares).

    Each wheel gives two equations, ``vx - wz*y = v*cos(a)`` and ``vy + wz*x = v*sin(a)``.
    Solved relative to the centroid of the wheels, the least-squares solution has a closed form.
    """
    positions = geometry.wheel_positions()
    n = len(positions)
    cx = sum(x for x, _ in positions) / n
    cy = sum(y for _, y in positions) / n

    wheel_velocities = [(w.speed * math.cos(w.angle), w.speed * math.sin(w.angle)) for w in wheels]
    mean_vx = sum(vx for vx, _ in wheel_velocities) / n
    mean_vy = sum(vy for _, vy in wheel_velocities) / n

    numerator = 0.0
    denominator = 0.0
    for (x, y), (vx, vy) in zip(positions, wheel_velocities, strict=True):
        dx, dy = x - cx, y - cy
        numerator += dx * vy - dy * vx
        denominator += dx * dx + dy * dy
    wz = numerator / denominator

    # Velocity of the centroid, moved to the body origin.
    return Twist(vx=mean_vx + wz * cy, vy=mean_vy - wz * cx, wz=wz)


def ackermann(speed: float, curvature: float) -> Twist:
    """Drive forward (or backward) along an arc: curvature = 1/turn radius, positive = left.

    With all four wheels steerable, the turn centre lies on the body's y axis, so front and rear
    wheels steer in opposite directions and the rover turns tighter than with front steering only.
    """
    return Twist(vx=speed, vy=0.0, wz=speed * curvature)


def spin(yaw_rate: float) -> Twist:
    """Turn on the spot around the rover centre (positive = counter-clockwise)."""
    return Twist(vx=0.0, vy=0.0, wz=yaw_rate)


def crab(speed: float, heading: float) -> Twist:
    """Drive in a straight line in direction ``heading`` (rad, relative to the body x axis)
    without turning. Useful for following walls and lawn edges sideways."""
    return Twist(vx=speed * math.cos(heading), vy=speed * math.sin(heading), wz=0.0)

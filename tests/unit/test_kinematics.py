import math

import pytest
from sprayrover.config import load_rover_config
from sprayrover.kinematics import (
    RoverGeometry,
    Twist,
    WheelState,
    ackermann,
    crab,
    forward_kinematics,
    inverse_kinematics,
    spin,
)

GEOMETRY = RoverGeometry(
    wheelbase=0.6, track_width=0.5, wheel_radius=0.127, max_steer_angle=math.pi / 2,
    max_wheel_speed=2.0,
)  # fmt: skip


def approx_twist(a: Twist, b: Twist, tol: float = 1e-9) -> bool:
    return all(
        math.isclose(p, q, abs_tol=tol) for p, q in ((a.vx, b.vx), (a.vy, b.vy), (a.wz, b.wz))
    )


def test_geometry_from_shared_config():
    geometry = RoverGeometry.from_config(load_rover_config())
    assert geometry.wheelbase > 0
    assert geometry.max_wheel_speed > 0


def test_straight_ahead_all_wheels_parallel_and_equal_speed():
    result = inverse_kinematics(Twist(vx=1.0), GEOMETRY)
    assert result.feasible and result.scale == 1.0
    for wheel in result.wheels:
        assert wheel.angle == pytest.approx(0.0)
        assert wheel.speed == pytest.approx(1.0)


def test_reversing_does_not_swing_wheels_around():
    result = inverse_kinematics(Twist(vx=-1.0), GEOMETRY)
    for wheel in result.wheels:
        assert wheel.angle == pytest.approx(0.0)
        assert wheel.speed == pytest.approx(-1.0)


def test_crab_sideways_steers_all_wheels_90_degrees():
    result = inverse_kinematics(crab(0.5, math.pi / 2), GEOMETRY)
    assert result.feasible
    for wheel in result.wheels:
        assert abs(wheel.angle) == pytest.approx(math.pi / 2)
        assert abs(wheel.speed) == pytest.approx(0.5)


def test_spin_wheels_are_tangent_to_circle_around_centre():
    result = inverse_kinematics(spin(1.0), GEOMETRY)
    radius = math.hypot(GEOMETRY.wheelbase / 2, GEOMETRY.track_width / 2)
    for (x, y), wheel in zip(GEOMETRY.wheel_positions(), result.wheels, strict=True):
        # Rolling direction is perpendicular to the line from the centre to the wheel.
        assert math.cos(wheel.angle) * x + math.sin(wheel.angle) * y == pytest.approx(0.0)
        assert abs(wheel.speed) == pytest.approx(radius)


def test_ackermann_wheels_point_perpendicular_to_turn_centre():
    turn_radius = 2.0
    result = inverse_kinematics(ackermann(1.0, 1 / turn_radius), GEOMETRY)
    for (x, y), wheel in zip(GEOMETRY.wheel_positions(), result.wheels, strict=True):
        to_centre = (0.0 - x, turn_radius - y)
        rolling = (math.cos(wheel.angle), math.sin(wheel.angle))
        assert rolling[0] * to_centre[0] + rolling[1] * to_centre[1] == pytest.approx(0.0)
    # Front and rear steer in opposite directions; inner (left) wheels slower than outer.
    front_left, front_right, rear_left, rear_right = result.wheels
    assert front_left.angle > 0 > rear_left.angle
    assert front_left.speed < front_right.speed


def test_speed_is_scaled_down_but_path_shape_kept():
    twist = Twist(vx=3.0, wz=2.0)
    result = inverse_kinematics(twist, GEOMETRY)
    assert result.scale < 1.0
    assert max(abs(w.speed) for w in result.wheels) == pytest.approx(GEOMETRY.max_wheel_speed)
    estimate = forward_kinematics(result.wheels, GEOMETRY)
    assert estimate.wz / estimate.vx == pytest.approx(twist.wz / twist.vx)


def test_standstill_keeps_previous_steering_angles():
    previous = (0.1, -0.2, 0.3, -0.4)
    result = inverse_kinematics(Twist(), GEOMETRY, previous_angles=previous)
    assert [w.angle for w in result.wheels] == list(previous)
    assert all(w.speed == 0.0 for w in result.wheels)


def test_prefers_angle_closest_to_previous():
    # Sideways motion can be done at +90 deg forwards or -90 deg backwards; keep the current side.
    right = inverse_kinematics(crab(0.5, math.pi / 2), GEOMETRY, previous_angles=(-1.5,) * 4)
    assert all(w.angle == pytest.approx(-math.pi / 2) for w in right.wheels)
    assert all(w.speed == pytest.approx(-0.5) for w in right.wheels)


def test_unreachable_angle_is_clamped_and_reported():
    narrow = RoverGeometry(0.6, 0.5, 0.127, max_steer_angle=0.5, max_wheel_speed=2.0)
    result = inverse_kinematics(crab(0.5, math.pi / 2), narrow)
    assert not result.feasible
    assert all(abs(w.angle) <= 0.5 + 1e-12 for w in result.wheels)


@pytest.mark.parametrize(
    "twist",
    [Twist(1.0, 0.0, 0.0), Twist(0.3, -0.4, 0.0), Twist(0.0, 0.0, -1.2), Twist(0.5, 0.2, 0.7)],
)
def test_forward_kinematics_inverts_inverse_kinematics(twist):
    result = inverse_kinematics(twist, GEOMETRY)
    assert result.scale == 1.0
    assert approx_twist(forward_kinematics(result.wheels, GEOMETRY), twist)


def test_forward_kinematics_averages_noisy_wheels():
    wheels = [WheelState(0.0, 1.0 + d) for d in (0.01, -0.01, 0.02, -0.02)]
    estimate = forward_kinematics(wheels, GEOMETRY)
    assert estimate.vx == pytest.approx(1.0)
    assert estimate.vy == pytest.approx(0.0)


def test_wheel_angular_velocity():
    assert WheelState(0.0, 1.27).angular_velocity(0.127) == pytest.approx(10.0)

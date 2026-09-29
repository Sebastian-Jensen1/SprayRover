"""Interactive top-down view of the rover kinematics.

Drag the sliders (forward speed, sideways speed, yaw rate) and see how each wheel steers, how
fast it turns, and where the turn centre is. The simulated rover drives around and leaves a trail.

    pip install -e ".[viz]"
    python tools/kinematics_viewer.py                  # interactive window
    python tools/kinematics_viewer.py --save modes.png # static picture of the driving modes
"""

from __future__ import annotations

import argparse
import math

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Polygon, Rectangle
from matplotlib.transforms import Affine2D
from matplotlib.widgets import Button, Slider
from sprayrover.config import load_rover_config
from sprayrover.kinematics import (
    WHEEL_NAMES,
    RoverGeometry,
    Twist,
    ackermann,
    crab,
    inverse_kinematics,
    spin,
)

WHEEL_LENGTH = 0.254  # 10" wheel seen from above
WHEEL_WIDTH = 0.07
DT = 0.05


def turn_centre(twist: Twist) -> tuple[float, float] | None:
    """Instantaneous centre of rotation in the body frame, or None when driving straight."""
    if abs(twist.wz) < 1e-6:
        return None
    return (-twist.vy / twist.wz, twist.vx / twist.wz)


def draw_rover(ax, geometry: RoverGeometry, twist: Twist, pose=(0.0, 0.0, 0.0), angles=None):
    """Draw chassis, wheels, wheel-speed arrows and turn centre. Returns commands and artists."""
    x0, y0, heading = pose
    to_world = Affine2D().rotate(heading).translate(x0, y0) + ax.transData
    artists = []

    commands = inverse_kinematics(twist, geometry, previous_angles=angles)
    body = Rectangle(
        (-geometry.wheelbase / 2 - 0.08, -geometry.track_width / 2 + 0.06),
        geometry.wheelbase + 0.16,
        geometry.track_width - 0.12,
        facecolor="#d9e6d3",
        edgecolor="#3b5d33",
        transform=to_world,
    )
    artists.append(ax.add_patch(body))
    nose = Polygon([(0.34, 0.08), (0.34, -0.08), (0.44, 0.0)], color="#3b5d33", transform=to_world)
    artists.append(ax.add_patch(nose))

    for (x, y), wheel in zip(geometry.wheel_positions(), commands.wheels, strict=True):
        tyre = Rectangle(
            (-WHEEL_LENGTH / 2, -WHEEL_WIDTH / 2),
            WHEEL_LENGTH,
            WHEEL_WIDTH,
            facecolor="#222222",
            transform=Affine2D().rotate(wheel.angle).translate(x, y) + to_world,
        )
        artists.append(ax.add_patch(tyre))
        # Arrow: direction and length show the wheel's ground velocity.
        dx = wheel.speed * math.cos(wheel.angle) * 0.4
        dy = wheel.speed * math.sin(wheel.angle) * 0.4
        artists.append(
            ax.annotate(
                "",
                xy=(x + dx, y + dy),
                xytext=(x, y),
                xycoords=to_world,
                arrowprops={"arrowstyle": "->", "color": "#d1495b", "lw": 2},
            )
        )

    centre = turn_centre(Twist(twist.vx * commands.scale, twist.vy * commands.scale, twist.wz))
    if centre is not None and math.hypot(*centre) < 6:
        artists += ax.plot(*centre, "x", color="#2e86ab", ms=10, mew=2, transform=to_world)
        for x, y in geometry.wheel_positions():
            artists += ax.plot(
                [x, centre[0]], [y, centre[1]], ":", color="#2e86ab", lw=1, transform=to_world
            )
    return commands, artists


def save_modes(geometry: RoverGeometry, path: str) -> None:
    modes = [
        ("Straight ahead", Twist(vx=0.8)),
        ("Ackermann (turn radius 1.5 m)", ackermann(0.8, 1 / 1.5)),
        ("Spin on the spot", spin(1.0)),
        ("Crab 45°", crab(0.8, math.radians(45))),
    ]
    fig, axes = plt.subplots(1, len(modes), figsize=(4 * len(modes), 4.6))
    for ax, (title, twist) in zip(axes, modes, strict=True):
        commands, _ = draw_rover(ax, geometry, twist)
        ax.set_title(title)
        lines = [
            f"{label}: {math.degrees(w.angle):6.1f}°  {w.speed:5.2f} m/s"
            for label, w in zip(("FL", "FR", "RL", "RR"), commands.wheels, strict=True)
        ]
        ax.text(
            0.02, 0.02, "\n".join(lines), transform=ax.transAxes, family="monospace", fontsize=8
        )
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.0, 1.8)
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
    fig.suptitle(
        "SprayRover 4-wheel steering: wheel angles, wheel speeds (red) and turn centre (blue)"
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=120)
    print(f"Saved {path}")


def interactive(geometry: RoverGeometry) -> None:
    fig, (ax_world, ax_body) = plt.subplots(1, 2, figsize=(12, 6.5))
    fig.subplots_adjust(bottom=0.27)
    sliders = {
        "vx": Slider(fig.add_axes((0.15, 0.16, 0.7, 0.03)), "forward m/s", -1, 1, valinit=0.5),
        "vy": Slider(fig.add_axes((0.15, 0.11, 0.7, 0.03)), "sideways m/s", -1, 1, valinit=0.0),
        "wz": Slider(fig.add_axes((0.15, 0.06, 0.7, 0.03)), "yaw rate rad/s", -2, 2, valinit=0.3),
    }
    reset = Button(fig.add_axes((0.88, 0.01, 0.1, 0.04)), "Reset")

    state = {"pose": [0.0, 0.0, 0.0], "trail": [(0.0, 0.0)], "angles": (0.0,) * 4, "artists": []}

    def on_reset(_event):
        state["pose"] = [0.0, 0.0, 0.0]
        state["trail"] = [(0.0, 0.0)]

    reset.on_clicked(on_reset)
    (trail_line,) = ax_world.plot([], [], color="#6c8f5f", lw=1.5)
    for ax, title in ((ax_world, "Garden (rover drives around)"), (ax_body, "Rover close-up")):
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
        ax.set_title(title)
    ax_world.set_xlim(-5, 5)
    ax_world.set_ylim(-5, 5)
    ax_body.set_xlim(-1.5, 1.5)
    ax_body.set_ylim(-1.5, 1.5)
    info = ax_body.text(0.02, 0.02, "", transform=ax_body.transAxes, family="monospace", fontsize=9)

    def update(_frame):
        for artist in state["artists"]:
            artist.remove()
        twist = Twist(sliders["vx"].val, sliders["vy"].val, sliders["wz"].val)
        commands, artists_body = draw_rover(ax_body, geometry, twist, angles=state["angles"])
        state["angles"] = tuple(w.angle for w in commands.wheels)

        # Integrate the pose with the (possibly scaled) twist and wrap around the garden edges.
        x, y, heading = state["pose"]
        vx, vy = twist.vx * commands.scale, twist.vy * commands.scale
        heading += twist.wz * commands.scale * DT
        x += (vx * math.cos(heading) - vy * math.sin(heading)) * DT
        y += (vx * math.sin(heading) + vy * math.cos(heading)) * DT
        if abs(x) > 5 or abs(y) > 5:
            x, y = 0.0, 0.0
            state["trail"] = []
        state["pose"] = [x, y, heading]
        state["trail"] = (state["trail"] + [(x, y)])[-400:]
        trail_line.set_data(*zip(*state["trail"], strict=True))
        _, artists_world = draw_rover(ax_world, geometry, twist, pose=(x, y, heading))

        info.set_text(
            "\n".join(
                f"{name:<12}{math.degrees(w.angle):7.1f}°{w.speed:7.2f} m/s"
                for name, w in zip(WHEEL_NAMES, commands.wheels, strict=True)
            )
            + ("" if commands.feasible else "\nsteering limit reached!")
        )
        state["artists"] = artists_body + artists_world
        return []

    fig._animation = FuncAnimation(fig, update, interval=int(DT * 1000), cache_frame_data=False)
    plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--save", metavar="PNG", help="save a picture of the driving modes and exit"
    )
    args = parser.parse_args()
    geometry = RoverGeometry.from_config(load_rover_config())
    if args.save:
        save_modes(geometry, args.save)
    else:
        interactive(geometry)


if __name__ == "__main__":
    main()

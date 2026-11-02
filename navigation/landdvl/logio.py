"""Log format shared by the simulator and the real measurement rig.

A log is a folder with one CSV file per sensor and a ``meta.json`` file:

    truth.csv   t, x, y, yaw, vx, vy          (simulator only; real logs have no truth)
    imu.csv     t, gyro_z, acc_x, acc_y       body frame: x forward, y left; rad/s and m/s^2
    wheel.csv   t, speed                      forward speed from the wheel encoder, m/s
    gnss.csv    t, x, y, quality, sigma       local ENU metres; quality: fix / float / none
    radar.csv   t, beam, radial_velocity      ground speed along each beam, m/s
                (optionally + ux, uy, uz: the direction of each detection, for a point-cloud
                radar; then ``beam`` is just a counter and meta beam vectors are not needed)
    meta.json   rates, radar beam geometry, garden description, notes

Time ``t`` is seconds from the start of the log. A real rig converts GNSS latitude/longitude to
local ENU metres before writing ``gnss.csv`` (or a converter does it afterwards).
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

COLUMNS = {
    "truth": ("t", "x", "y", "yaw", "vx", "vy"),
    "imu": ("t", "gyro_z", "acc_x", "acc_y"),
    "wheel": ("t", "speed"),
    "gnss": ("t", "x", "y", "quality", "sigma"),
    "radar": ("t", "beam", "radial_velocity"),
}


@dataclass
class Log:
    imu: np.ndarray  # columns as in COLUMNS["imu"]
    wheel: np.ndarray
    gnss_xy: np.ndarray  # t, x, y, sigma
    gnss_quality: list[str]
    radar: np.ndarray  # t, beam, radial_velocity
    meta: dict
    truth: np.ndarray | None = None

    def beam_vectors(self) -> np.ndarray:
        """Unit vectors of the radar beams in the body frame, shape (n_beams, 3)."""
        return np.array(self.meta["radar"]["beam_unit_vectors"], dtype=float)


def write_log(folder: str | Path, tables: dict[str, list[tuple]], meta: dict) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        with open(folder / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS[name])
            writer.writerows(rows)
    with open(folder / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return folder


def _read_numeric(path: Path) -> np.ndarray:
    data = np.genfromtxt(path, delimiter=",", skip_header=1, dtype=float)
    return np.atleast_2d(data)


def read_log(folder: str | Path) -> Log:
    folder = Path(folder)
    with open(folder / "meta.json", encoding="utf-8") as f:
        meta = json.load(f)

    gnss_rows = []
    qualities = []
    with open(folder / "gnss.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gnss_rows.append(
                (float(row["t"]), float(row["x"]), float(row["y"]), float(row["sigma"]))
            )
            qualities.append(row["quality"])

    truth_path = folder / "truth.csv"
    return Log(
        imu=_read_numeric(folder / "imu.csv"),
        wheel=_read_numeric(folder / "wheel.csv"),
        gnss_xy=np.array(gnss_rows, dtype=float).reshape(-1, 4),
        gnss_quality=qualities,
        radar=_read_numeric(folder / "radar.csv"),
        meta=meta,
        truth=_read_numeric(truth_path) if truth_path.exists() else None,
    )

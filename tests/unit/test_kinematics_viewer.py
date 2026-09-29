import sys
from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

import matplotlib  # noqa: E402

matplotlib.use("Agg")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import kinematics_viewer  # noqa: E402
from sprayrover.config import load_rover_config  # noqa: E402
from sprayrover.kinematics import RoverGeometry  # noqa: E402


def test_save_modes_writes_png(tmp_path):
    out = tmp_path / "modes.png"
    kinematics_viewer.save_modes(RoverGeometry.from_config(load_rover_config()), str(out))
    assert out.stat().st_size > 0

import math

import numpy as np
import pytest

from landdvl.ekf import FilterConfig, PlanarEKF, radar_body_velocity
from landdvl.evaluate import artificial_outages, summary_table
from landdvl.logio import Log, read_log, write_log
from landdvl.runner import Replay
from landdvl.sim import SensorModel, simulate
from landdvl.world import Garden, Tree

SMALL = Garden(width=16.0, height=14.0, trees=(Tree(11.0, 4.0, 1.5),))


@pytest.fixture(scope="module")
def small_log(tmp_path_factory):
    tables, meta = simulate(SMALL, SensorModel(), seed=3)
    folder = write_log(tmp_path_factory.mktemp("log") / "small", tables, meta)
    return read_log(folder)


def test_gnss_quality_zones():
    assert SMALL.gnss_quality(11.0, 4.0) == "none"  # under the canopy
    assert SMALL.gnss_quality(11.0, 6.5) == "float"  # near the canopy edge
    assert SMALL.gnss_quality(2.0, 1.0) == "float"  # next to the house wall
    assert SMALL.gnss_quality(2.0, 12.0) == "fix"  # open sky


def test_radar_sees_ground_moving_backwards():
    beams = SensorModel().beam_unit_vectors()
    v_body = np.array([0.5, 0.0, 0.0])
    radial = -beams @ v_body
    assert radial[0] < 0  # forward-looking beam: ground moves towards the sensor
    assert radial[1] > 0  # backward-looking beam: ground moves away
    assert np.allclose(np.linalg.norm(beams, axis=1), 1.0)
    assert math.isclose(np.degrees(np.arccos(-beams[0, 2])), 30.0, abs_tol=1e-9)


def test_log_round_trip(small_log):
    assert small_log.truth is not None
    assert set(small_log.gnss_quality) <= {"fix", "float"}
    assert small_log.beam_vectors().shape == (4, 3)
    assert small_log.imu.shape[1] == 4


def test_filter_tracks_with_rtk(small_log):
    replay = Replay(small_log)
    ekf = replay.initial_filter(FilterConfig())
    est, _ = replay.run(ekf, 0.0, float("inf"))
    tr = small_log.truth
    tx = np.interp(est[:, 0], tr[:, 0], tr[:, 1])
    ty = np.interp(est[:, 0], tr[:, 0], tr[:, 2])
    err = np.hypot(est[:, 1] - tx, est[:, 2] - ty)
    assert np.median(err) < 0.1


def test_radar_reduces_outage_error(small_log):
    starts, results, _ = artificial_outages(small_log, duration=20.0, count=6)
    assert starts
    rows = {r["sensor_set"]: r for r in summary_table(results)}
    assert rows["IMU + radar"]["median_10s"] < rows["IMU + wheel"]["median_10s"]


def test_real_log_without_truth_uses_rtk_fix_as_reference(small_log):
    real = Log(
        imu=small_log.imu,
        wheel=small_log.wheel,
        gnss_xy=small_log.gnss_xy,
        gnss_quality=small_log.gnss_quality,
        radar=small_log.radar,
        meta={k: v for k, v in small_log.meta.items() if k not in ("garden", "source")},
        truth=None,
    )
    starts, results, _ = artificial_outages(real, duration=10.0, count=4)
    assert starts
    assert all(np.isfinite(r.errors).all() for r in results)


def test_point_cloud_radar_rows_match_beam_rows(small_log):
    beams = small_log.beam_vectors()
    dirs = beams[small_log.radar[:, 1].astype(int)]
    cloud = Log(
        imu=small_log.imu,
        wheel=small_log.wheel,
        gnss_xy=small_log.gnss_xy,
        gnss_quality=small_log.gnss_quality,
        radar=np.column_stack([small_log.radar, dirs]),
        meta={k: v for k, v in small_log.meta.items() if k != "radar"},
        truth=small_log.truth,
    )
    a = Replay(small_log)
    b = Replay(cloud)
    est_a, _ = a.run(a.initial_filter(FilterConfig()), 0.0, 80.0)
    est_b, _ = b.run(b.initial_filter(FilterConfig()), 0.0, 80.0)
    assert np.allclose(est_a, est_b)


def test_radar_body_velocity_least_squares():
    beams = SensorModel().beam_unit_vectors()
    v_true = np.array([0.4, -0.1, 0.0])
    v = radar_body_velocity(beams, -beams @ v_true)
    assert np.allclose(v, v_true[:2])
    single = radar_body_velocity(beams[:1], -beams[:1] @ np.array([0.4, 0.0, 0.0]))
    assert np.allclose(single, [0.4, 0.0])


def test_slip_detection_skips_slipping_wheel():
    ekf = PlanarEKF(FilterConfig(), np.zeros(8), np.ones(8) * 0.01)
    assert ekf.update_wheel(0.50, radar_speed=0.49)  # agrees: used
    assert not ekf.update_wheel(0.65, radar_speed=0.50)  # 30 % slip: skipped
    assert ekf.wheel_rejected_slip == 1
    off = PlanarEKF(FilterConfig(slip_detection=False), np.zeros(8), np.ones(8) * 0.01)
    assert off.update_wheel(0.65, radar_speed=0.50)


def test_sweep_cases_and_report(tmp_path):
    from landdvl import sweep

    todo = sweep.cases([1, 2], windows=5)
    n_values = sum(len(v) for v in sweep.DIMENSIONS.values())
    assert len(todo) == 2 * n_values
    cfg = sweep.filter_for(SensorModel(radar_noise=0.05))
    assert cfg.radar_sigma == pytest.approx(0.1)

    rows = []
    for dim, values in sweep.DIMENSIONS.items():
        for label, x, _ in values:
            for s, err in zip(sweep.SETS, (1.0, 0.4, 0.2), strict=True):
                rows.append(
                    dict(dimension=dim, value=label, x=x, seed=1, sensor_set=s,
                         median_10s=0.1, median_30s=err, median_60s=err, p90_30s=err)
                )  # fmt: skip
    text = sweep.write_outputs(rows, tmp_path, [1])
    assert "| 0.40 |" in text  # ratio column
    assert (tmp_path / "sweep.csv").exists()

import math

import numpy as np
import pytest

from landdvl.evaluate import full_run
from landdvl.logio import read_log, write_log
from landdvl.rig import nmea
from landdvl.rig.core import ClockSync, Rig, RigConfig, axis_matrix
from landdvl.rig.loopback import run as loopback_run
from landdvl.rig.ti_radar import PacketReader, RadarMount, build_packet
from landdvl.sim import SensorModel, simulate
from landdvl.world import Garden, Tree

SMALL = Garden(width=16.0, height=14.0, trees=(Tree(11.0, 4.0, 1.5),))


def test_nmea_gga_and_gst():
    gga = nmea.parse("$GNGGA,123519.00,5540.5660,N,01234.0980,E,4,24,0.6,30.1,M,40.0,M,1.0,0000*4E")
    assert gga is None  # wrong checksum
    good = nmea.make_sentence("GNGGA,123519.00,5540.5660,N,01234.0980,E,4,24,0.6,30.1,M,40.0,M,,")
    gga = nmea.parse(good)
    assert gga.quality == "fix"
    assert gga.lat == pytest.approx(55 + 40.566 / 60)
    assert gga.lon == pytest.approx(12 + 34.098 / 60)
    assert (
        nmea.parse(
            nmea.make_sentence("GNGGA,123520.00,5540.5660,S,01234.0980,W,5,9,1,3,M,4,M,,")
        ).quality
        == "float"
    )
    gst = nmea.parse(nmea.make_sentence("GNGST,123519.00,0.5,0.02,0.01,45.0,0.012,0.016,0.03"))
    assert gst.sigma == pytest.approx(math.sqrt((0.012**2 + 0.016**2) / 2))
    assert nmea.utc_seconds("123519.50") == pytest.approx(12 * 3600 + 35 * 60 + 19.5)


def test_local_frame_round_trip():
    frame = nmea.LocalFrame(55.6761, 12.5683)
    lat, lon = frame.to_latlon(25.0, -13.0)
    assert np.allclose(frame.to_local(lat, lon), (25.0, -13.0), atol=1e-6)
    line = nmea.format_gga("101010.00", lat, lon, 4)
    gga = nmea.parse(line)
    assert np.allclose(frame.to_local(gga.lat, gga.lon), (25.0, -13.0), atol=0.001)


def test_radar_packets_survive_splitting_and_garbage():
    pts = np.array([[0.1, 1.0, -0.5, 0.3], [-0.2, 0.8, -0.6, -0.1]])
    data = (
        b"noise" + build_packet(7, pts) + build_packet(8, np.zeros((0, 4))) + build_packet(9, pts)
    )
    reader = PacketReader()
    frames = []
    for i in range(0, len(data), 13):
        frames += reader.feed(data[i : i + 13])
    assert [f.frame_number for f in frames] == [7, 8, 9]
    assert np.allclose(frames[0].points, pts, atol=1e-6)
    assert len(frames[1].points) == 0


def test_radar_mount_geometry():
    mount = RadarMount(yaw_deg=180.0, tilt_down_deg=45.0, height_m=0.5)
    boresight = mount.rotation() @ np.array([0.0, 1.0, 0.0])
    assert np.allclose(boresight, [-math.sqrt(0.5), 0.0, -math.sqrt(0.5)])  # backwards and down
    # A ground point straight along the boresight, while the trolley moves forward at 1 m/s:
    # the ground moves away from a backward-looking radar, so TI's doppler is positive.
    u_body = boresight
    p_radar = mount.to_radar_frame(u_body * 0.5 / math.sqrt(0.5))
    doppler = -(u_body @ np.array([1.0, 0.0, 0.0]))
    u, radial = mount.ground_points(np.array([[*p_radar, doppler], [0.0, 1.0, 1.0, 0.0]]))
    assert len(radial) == 1  # the point above the ground is dropped
    assert np.allclose(u[0], u_body)
    assert radial[0] == pytest.approx(math.sqrt(0.5))


def test_clock_sync_uses_least_delayed_message():
    rng = np.random.default_rng(1)
    sync = ClockSync()
    for k in range(500):
        device = 100.0 + k * 0.005
        est = sync.update(device - 100.0 + 0.002 + rng.exponential(0.003), device)
    assert est == pytest.approx(-100.0 + 0.002, abs=1e-4)


def test_imu_axes():
    m = axis_matrix(("-y", "x", "z"))
    assert np.allclose(m @ np.array([1.0, 2.0, 3.0]), [-2.0, 1.0, 3.0])
    with pytest.raises(ValueError):
        axis_matrix(("x", "x", "z"))


def test_rig_handles_bad_input(tmp_path):
    rig = Rig(tmp_path / "log", RigConfig(), t0=0.0)
    rig.on_pico_line(0.0, "I,1000,not,a,number")
    rig.on_pico_line(0.0, "S,hello")
    rig.on_gnss_line(0.1, "$GNGGA,garbage*00")
    rig.on_radar_bytes(0.2, b"\x01\x02\x03")
    stats = rig.close()
    assert stats["pico_bad_lines"] == 1
    assert stats["rows"]["events"] == 1


def test_loopback_matches_simulation(tmp_path):
    tables, meta = simulate(SMALL, SensorModel(), seed=3)
    sim_folder = write_log(tmp_path / "sim", tables, meta)
    stats = loopback_run(sim_folder, tmp_path / "rig")
    assert stats["pico_bad_lines"] == 0 and stats["radar_bad_packets"] == 0
    sim, rig = read_log(sim_folder), read_log(tmp_path / "rig")
    assert rig.truth is None
    assert rig.imu.shape == sim.imu.shape
    assert np.abs(rig.imu[:, 1:] - sim.imu[:, 1:]).max() < 1e-5
    assert len(rig.radar) == len(sim.radar)
    assert rig.radar.shape[1] == 6
    # Same filter result on both logs, measured against the simulator's truth.
    origin = sim.gnss_xy[0, 1:3]
    for log, shift in ((sim, np.zeros(2)), (rig, origin)):
        est = full_run(log, "IMU + wheel + radar")
        tr = sim.truth
        err = np.hypot(
            est[:, 1] + shift[0] - np.interp(est[:, 0], tr[:, 0], tr[:, 1]),
            est[:, 2] + shift[1] - np.interp(est[:, 0], tr[:, 0], tr[:, 2]),
        )
        assert np.median(err) < 0.05
        assert err.max() < 0.5

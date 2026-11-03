# Land-DVL navigation experiments

Software for the navigation-module track (see [docs/business/market-navigation-module.md](../docs/business/market-navigation-module.md)).
It answers the F0 question: **does Doppler radar at least halve the position error growth when GNSS
disappears?**

It works on **simulated logs today** and on **real logs from the measurement rig** later, using the same
log format and the same code. See [docs/navigation/measurement-rig.md](../docs/navigation/measurement-rig.md)
for the rig.

## Quick start

```bash
cd navigation
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[plot,dev]"

python -m landdvl.sim --out logs/sim01 --seed 1        # 10 minutes of fake garden data (~6 s)
python -m landdvl.evaluate logs/sim01                  # outage test + report + plots (~1 min)
python -m pytest                                       # tests
```

The evaluation writes `results/sim01/report.md`, `error_growth.png` and `garden_run.png`.

## What is in here

| Module | What it does |
|---|---|
| `landdvl/world.py` | A garden with trees and a house wall. Decides GNSS quality: RTK fix in the open, float near trees and the wall, none under a canopy |
| `landdvl/sim.py` | Pushes a virtual trolley along lanes through the garden. Writes IMU (200 Hz), wheel encoder (50 Hz), GNSS (5 Hz), 4-beam radar (20 Hz) and the truth. Models IMU biases, wheel scale error and slip on wet ground under trees, GNSS multipath jumps and canopy dropouts, radar noise and dropouts |
| `landdvl/logio.py` | The log format: one CSV per sensor plus `meta.json`. **The real rig must write exactly this** |
| `landdvl/ekf.py` | Planar extended Kalman filter: IMU prediction; GNSS, wheel, radar, zero-velocity and zero-rate updates; outlier gate for multipath with recovery |
| `landdvl/runner.py` | Replays a log through the filter. Can switch GNSS off in a time window |
| `landdvl/evaluate.py` | The artificial outage test: start from a converged filter under open sky, switch GNSS off for 60 s, compare sensor sets against the truth |
| `landdvl/sweep.py` | Sensitivity analysis: varies radar noise, beam count, tilt and rate, and IMU grade, over several seeds, in parallel |
| `landdvl/rig/` | **Logger for the real measurement rig** (Pico IMU/encoder, GNSS NMEA, TI radar) and a loopback test without hardware. See [docs/navigation/rig-logger.md](../docs/navigation/rig-logger.md) |
| `firmware/pico_logger/` | Pico 2 firmware for the rig (not yet run on hardware) |

## How the test works

1. Run the filter over the whole log with everything on. Save its state every second.
2. Pick start times where the rig moves under open sky and has had RTK fix for at least 15 s.
3. From each start, rerun with GNSS switched off, once per sensor set:
   - IMU + wheel,
   - IMU + wheel + radar,
   - IMU + radar.
4. Measure the distance to the truth every second.
   - **Simulated logs:** the truth is `truth.csv`.
   - **Real logs:** the truth is the RTK fix itself, so real outage windows must be driven in the open.
     GNSS is only switched off inside the filter.

## Results (simulated, seed 1, 25 windows)

With radar-based **wheel-slip detection** (version 2: wheel and radar speeds averaged over 0.5 s, a threshold
that adapts to the measured radar noise, and a 5 s hold-off after each detected slip):

| Sensor set | median 10 s | median 30 s | median 60 s |
|---|---|---|---|
| IMU + wheel | 0.09 m | 1.36 m | 1.55 m |
| IMU + wheel + radar | 0.06 m | 0.21 m | 0.27 m |
| IMU + radar | 0.04 m | 0.20 m | 0.23 m |

The radar ratio at 30 s is **0.15** (version 1 of slip detection: 0.17; none: 0.49, `--no-slip-detection`).
Over the whole run with real GNSS, the maximum error drops from 2.31 m (IMU + wheel) to 0.29 m.

**This shows the pipeline works and that the idea is plausible under the assumed noise levels**
(`SensorModel` in `sim.py`). The real answer comes from real data.

**Which radar is good enough?** See the sensitivity analysis in
[docs/navigation/sensitivity.md](../docs/navigation/sensitivity.md) (`python -m landdvl.sweep`). In short:
- radar velocity noise ≤ 0.01–0.02 m/s per detection,
- at least 2 beam directions that differ sideways,
- tilt 30–60° from straight down,
- at least 10–20 Hz.

## Known simplifications (to fix before real data)

- **2D only:** level ground, no roll/pitch, gravity not modelled. Real IMU data needs tilt handling, or at
  least levelling at start.
- **No lever arms:** antenna, IMU, radar and wheel are assumed to be at the same point. Measure the offsets
  on the rig and add them.
- **Simple radar model:** the simulator uses 4 fixed beams. A real TI radar gives a point cloud; write each
  ground detection as a row with its direction (`ux, uy, uz` columns, already supported) and filter out
  non-ground points first.
- **Time sync:** the simulator has perfect timestamps. The rig logger puts all sensors on one clock and
  removes USB jitter, but not each device's constant delay (see the logger docs).
- **Initial heading** comes from `meta.json` (`start_pose.yaw`). On the rig, start with the trolley aligned
  to a marked line, or estimate heading from the first metres of RTK track.

## Ideas for the filter work

- Slip handling for noisy radar (> 0.02 m/s): estimate wheel slip and scale error as filter states. The
  averaged, noise-adaptive check with hold-off (version 2) is done.
- Radar outlier rejection (moving grass, puddles, the trolley's own frame in the beam).
- Error-state formulation in 3D with a proper IMU mechanisation.
- Tune `FilterConfig` noise values from static data recorded with the real sensors (Allan variance).

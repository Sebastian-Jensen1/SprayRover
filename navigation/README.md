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

## First result (simulated, seed 1, 25 windows)

| Sensor set | median 10 s | median 30 s | median 60 s |
|---|---|---|---|
| IMU + wheel | 0.08 m | 1.36 m | 1.53 m |
| IMU + wheel + radar | 0.06 m | 0.67 m | 0.71 m |
| IMU + radar | 0.04 m | 0.17 m | 0.23 m |

Radar ratio at 30 s: **0.49** (with radar / without).

**This only proves the pipeline works and that the idea is plausible under the assumed noise levels**
(`SensorModel` in `sim.py`). The real answer comes from real data.

The result also points to the first improvement. With radar on board, the wheel's slip under the trees still
pulls the estimate off, so "IMU + radar" beats "IMU + wheel + radar". **Use the radar to detect wheel slip
and down-weight or reject the wheel during slip.** This is a classic radar-vs-wheel technique and a good
first task.

## Known simplifications (to fix before real data)

- **2D only:** level ground, no roll/pitch, gravity not modelled. Real IMU data needs tilt handling, or at
  least levelling at start.
- **No lever arms:** antenna, IMU, radar and wheel are assumed to be at the same point. Measure the offsets
  on the rig and add them.
- **Simple radar model:** the simulator uses 4 fixed beams. A real TI radar gives a point cloud; write each
  ground detection as a row with its direction (`ux, uy, uz` columns, already supported) and filter out
  non-ground points first.
- **Time sync:** the simulator has perfect timestamps. The rig must timestamp all sensors on one clock.
- **Initial heading** comes from `meta.json` (`start_pose.yaw`). On the rig, start with the trolley aligned
  to a marked line, or estimate heading from the first metres of RTK track.

## Ideas for the filter work

- Slip detection: compare radar and wheel speed, inflate `wheel_sigma` or skip wheel updates during slip.
- Radar outlier rejection (moving grass, puddles, the trolley's own frame in the beam).
- Error-state formulation in 3D with a proper IMU mechanisation.
- Tune `FilterConfig` noise values from static data recorded with the real sensors (Allan variance).

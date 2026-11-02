# Which Radar Is Good Enough? (Sensitivity Analysis)

**Simulation results, not measurements.** They show which sensor properties matter and roughly how much, under
the assumptions in `navigation/landdvl/sim.py`. The real test is the
[measurement rig](measurement-rig.md).

Method:
- `python -m landdvl.sweep` changes one property at a time around the default sensors.
- It simulates the 30 × 20 m garden for 3 seeds and runs the artificial-outage test with 15 windows each.
- It reports the **median position error after 30 s without GNSS**, averaged over the seeds.
- Each filter is tuned to the sensor it gets, and wheel-slip detection is on.

![Sensitivity analysis](img/sweep.png)

## Requirements for the radar (and IMU)

Updated November 2026 with the improved slip detection (see below). Numbers are median errors after 30 s
without GNSS.

| Property | Requirement | Why |
|---|---|---|
| **Radar velocity noise per detection** | **≤ 0.01–0.02 m/s** | At 0.01 m/s, IMU + wheel + radar holds 0.18 m, against 1.29 m for IMU + wheel. At 0.02 m/s it is 0.34 m. At 0.05 m/s the combined filter loses most of the gain (1.06 m), because slipping wheels can no longer be told apart from radar noise. IMU + radar alone still holds 0.23 m there |
| **Beam directions** | **At least 2 directions that differ sideways** (e.g. front-left and front-right) | A single forward beam can't see sideways drift. IMU + radar then fails (1.65 m), and it only works together with the wheel. One wide-field TI radar that sees many ground points satisfies this |
| **Tilt from straight down** | **30–60°** | Steep beams (10°) barely see horizontal motion: 0.61 m with wheel + radar. 45° gives 0.16 m |
| **Update rate** | **≥ 10–20 Hz** | 5 Hz still helps, but less (0.23 m against 0.18 m at 20 Hz) |
| **IMU** | Default MEMS grade is fine; a better IMU helps most | A cheap IMU with 3× the noise more than doubles the error (0.42 m). A good one gives 0.12 m (0.08 m with radar alone) |

### What does a real TI radar give? (own estimate, to be measured)

TI states a **velocity resolution of 0.05 m/s** for its IWR6843 reference design
([TI, TIDUEI1C key specifications](https://ti.com/document-viewer/lit/html/TIDUEI1C/key-system-specifications-id-76d97e34-85ff-45c3-8c0e-d20c3e200186.html)).
Resolution is the step size of the Doppler measurement, not the noise. A pure rounding error with 0.05 m/s
steps has a standard deviation of 0.05 / √12 ≈ **0.014 m/s**, inside the requirement, and the radar sees many
ground points per frame. A longer chirp sequence in the radar configuration gives finer steps. **This is an
estimate.** Measure it on the rig: trolley standing still, then pushed at a known speed.

## What this means

1. **The radar idea holds up in simulation across a wide range of hardware.** Almost every configuration
   cuts the 30-second error to a fraction of IMU + wheel.
2. **Radar noise is the property that matters most.** Ask radar suppliers for velocity resolution and noise
   at walking speed (0.2–1 m/s), and measure it on the rig.
3. **Mount it at ~45°** and make sure the ground points spread left and right.
4. **With noisy radar, trust the wheel less.** In every row, IMU + radar alone is at least as good as
   IMU + wheel + radar. If the real radar is noisier than ~0.02 m/s, the next step is to estimate wheel slip
   and scale error as filter states, or to give the wheel a larger uncertainty.

## Wheel-slip detection

The filter compares the wheel speed with the radar's own ground speed (least squares from the detections in
one scan) and skips the wheel update when they disagree.

**Version 2 (November 2026):**
- **Averaging:** both speeds are averaged over the last 0.5 s. That cuts radar noise by about √10 at 20 Hz.
- **Noise-adaptive threshold:** 0.03 m/s + 5 % of the speed + 3 × the standard deviation of the averaged radar
  speed. The standard deviation is computed from the radar data itself, so it adapts to the fitted radar
  without tuning.
- **Hold-off:** after a detected slip, the wheel is also skipped for the next 5 s. Slip happens in patches
  (wet grass under the trees), and small slip of 7–10 % can't be told from noise sample by sample.

Why the hold-off matters (diagnosis at 0.02 m/s radar noise, seeds 1–2, 30 s outages): without any slip in
the simulation, IMU + wheel + radar reaches 0.21 m. With slip and version 1, 0.91 m. So almost all of the loss
came from slip getting through. Averaging alone gave little (0.91 m); a 5 s hold-off brought it to 0.31 m.

Effect across radar noise (mean over seeds 1–3, IMU + wheel + radar, median after 30 s):

| Radar noise | Version 1 | Version 2 | IMU + radar alone |
|---|---|---|---|
| 0.005 m/s | 0.14 m | 0.13 m | 0.13 m |
| 0.01 m/s | 0.22 m | 0.18 m | 0.15 m |
| 0.02 m/s | 0.72 m | 0.34 m | 0.17 m |
| 0.05 m/s | 1.19 m | 1.06 m | 0.23 m |

Settings in `FilterConfig`: `slip_window`, `slip_k`, `slip_hold` (set `slip_hold=0`, `slip_window=0` and
`slip_k=0` for the version 1 behaviour).

## Assumptions to check with real data

- Radar noise is white and Gaussian. There are no outliers from swaying grass, leaves, puddles or the
  trolley's own frame.
- Flat ground; the vertical velocity is zero.
- Perfect time sync and known beam directions.
- Wheel slip only in wet patches under the trees.

# Project Plan

How we get from the [ROSMASTER M1](platform-rosmaster-m1.md) in its box to a robot that treats weeds in a real
garden. Each phase ends with a **demo you can see** and a **measurable exit criterion**, so we know when to move
on and when to stop and rethink. Durations assume a small hobby team working evenings and weekends, so treat
them as rough estimates.

## Guiding rules

1. **The riskiest unique part first.** That is detecting and hitting weeds, not the chassis.
2. **Use what the M1 already gives us** (ROS 2, Nav2, SLAM, YOLOv11 on the Orin) before adding or writing anything.
3. **Measure, don't guess.** Survey GNSS coverage and test the M1 on grass before choosing the next hardware.
4. **Keep SprayRover code chassis-independent** (ROS 2 topics only), so it moves to the outdoor robot unchanged.
5. **Always working.** Every phase leaves something that runs.
6. **Safety from day one:** E-stop, watchdog and low speed as soon as anything moves on its own.

## Overview

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    axisFormat  %b
    section Start
    0 Get to know the M1 + garden survey :p0, 2026-11-02, 4w
    section Stage 1 (M1)
    1 Weed detection + spraying on M1    :p1, after p0, 8w
    2 Weed map + autonomous spot spray   :p2, after p1, 6w
    3 Outdoor tests: GNSS, terrace, lawn :p3, after p2, 6w
    section Stage 2 (outdoor robot)
    4 Outdoor chassis                    :p4, after p3, 10w
    5 Garden robot: shade, obstacles     :p5, after p4, 8w
    section Later
    6 Research tracks                    :p6, after p5, 12w
```

## Phase 0: Get to know the M1 and survey the garden (≈ 4 weeks)

**Goal:** the robot works with ROS 2 in our hands, and we know the garden.

| Task | Output |
|---|---|
| Work through the [first-week checklist](platform-rosmaster-m1.md#5-first-week-checklist): wheel type, kit, **SSD backup**, measurements, gamepad, ROS 2 control | Platform document completed with real values |
| Indoor demo: slam_toolbox map of a room + Nav2 drive to a goal | Toolchain proven |
| YOLOv11 segmentation demo on the Orin, frames per second noted | Detection speed known |
| **M1 outdoor test:** drive on the terrace and paved paths in dry weather. Does the lidar work in daylight? Does it drive straight? Measure top speed and how much it can carry | Decides how much of stage 1 can be tested outdoors |
| Measure the garden: lawn area, paths, beds, trees, walls, slopes. Simple map | `docs/garden-survey.md` |
| **GNSS survey:** carry an RTK receiver on a pole around the garden for 30 minutes on several days. Log RTK fix / float / none per position | A map of where RTK works. Decides D4 and D7. Needs the GNSS board, which can be reused on the robot |
| Collect 500+ lawn photos from about the height of the downward camera, in sun, shade and overcast | Start of our own dataset |
| Ask Miljøstyrelsen about automated spot application of approved ready-to-use products | Written answer in [regulations-and-safety.md](regulations-and-safety.md) |
| Repo: ROS 2 workspace for SprayRover packages, CI, issue board with phases as milestones | Clean repo skeleton |

**Exit:** M1 drives to a Nav2 goal indoors, YOLO demo runs, outdoor test filmed, GNSS map done, 500 photos.

## Phase 1: Weed detection and spraying on the M1 (≈ 8 weeks)

**Goal:** the M1 sees a weed and hits it with water, indoors and on the terrace.

| Task | Output |
|---|---|
| Mount a downward camera at the front. Calibrate camera to ground | Camera node publishing images and calibration |
| Spray module: 12 V pump, 1–2 normally-closed solenoid valves, MOSFET/relay module on a Jetson GPIO, small tank. Check the expansion board's 12 V output can supply it, otherwise use a separate fused supply | `/spray` ROS 2 service: "open valve n for t ms" |
| Simple detection first: OWL-style green detection on grey surfaces (terrace, paths, paper) | First automatic hits |
| Label 1,000+ lawn images (course 13 annotation tool or similar). Train YOLOv11 segmentation. Export for the Orin | Model with measured precision and recall (P1) |
| Treatment controller: weed position → wait until the nozzle is over it → spray. Test at low speed and with stop-and-spray | Hit rate on paper targets (P2) |
| E-stop in the battery line + watchdog node (stop without commands for 0.5 s) | P7 measured |

**Exit:** P2 met indoors with paper targets and coloured water. P1 measured on the test set (the target may be reached later).
**If not:** improve lighting (camera hood, LED ring), camera height and the dataset before going further.

## Phase 2: Weed map and autonomous spot spraying (≈ 6 weeks, mostly indoors/terrace)

**Goal:** the whole SprayRover behaviour, on the M1, on surfaces it can drive on.

| Task | Output |
|---|---|
| Weed map node: store each weed (map position, time, image crop, treatment) in a small database | F4 |
| Coverage: Nav2 + opennav_coverage drives a pattern over a marked area (e.g. 4 × 4 m on the terrace or indoors) | Autonomous coverage |
| Full run: coverage + detection + spraying + weed map. Use printed or real weed samples placed in the area | First complete SprayRover run |
| Simple web page: start/stop, status, weed map | F12 |
| Follow-up visit: drive back to stored weeds and photograph them | F5 (first version) |

**Exit:** an autonomous run over the marked area hits ≥ 80% of the placed weed samples within ±2 cm, and all
of them are in the weed map. **This is the stage 1 MVP.**

## Phase 3: Outdoor tests on the M1 (≈ 6 weeks, dry weather)

**Goal:** learn what breaks outdoors, before building the outdoor chassis.

| Task | Output |
|---|---|
| RTK GNSS on USB + robot_localization (EKF + navsat_transform) | Fused pose outdoors, P3 measured where there is fix |
| Garden map: record boundary and no-go zones. Test lidar SLAM along walls and trees (slam_toolbox / RTAB-Map) | Which localization works where in our garden |
| Detection outdoors: real lawn weeds in real light, using the dataset from phase 0 | P1 on outdoor images |
| Short autonomous runs on the terrace and paved paths, with real weeds in joints and gravel | List of what fails outdoors (sun on lidar and cameras, vibration, dust, uneven tiles) |

**Exit:** GNSS + fusion measured in the garden; a clear list of requirements for the outdoor chassis.

## Phase 4: Outdoor chassis (≈ 10 weeks)

**Goal:** the same software on a chassis that can drive on the whole lawn.

| Task | Output |
|---|---|
| Choose option A/B/C from [concept-and-architecture.md](concept-and-architecture.md#choosing-the-outdoor-chassis-stage-2-decided-in-phase-4) using the phase 3 results | Decision D8 |
| Build or convert the chassis. Weather-protected box for the Jetson. Move lidar, cameras, GNSS, spray module | Outdoor robot |
| ROS 2 driver for the new drive (`/cmd_vel` in, `/odom` out) and a new URDF. Possibly move to ROS 2 Jazzy | Same SprayRover nodes running unchanged |
| Repeat the phase 2 run on the real lawn | MVP on the lawn |

**Exit:** an autonomous run over the open lawn treats ≥ 80% of marked test weeds within ±2 cm. **This is the garden MVP.**

## Phase 5: Garden robot: shade, obstacles, follow-up (≈ 8 weeks)

| Task | Output |
|---|---|
| Shaded areas: use the phase 0 GNSS map to pick lidar/visual odometry, UWB beacons or better dead-reckoning | P4 met in the real shaded areas (F7) |
| Obstacles outdoors: lidar + depth camera in Nav2, plus a bumper. Person and animal detection with the camera | F8 |
| Follow-up visits after N days; re-treat if still alive. Then, if allowed (phase 0 answer), an approved ready-to-use product | F5, first data on how well the treatment works |
| Lawn edges and walls | F6 measured |

**Exit:** a full week of scheduled autonomous runs in the real garden, with a log of every intervention.

## Phase 6: Research tracks (later, optional)

These are the "big ideas" from the original notes. They are valuable, but kept **off the critical path**.

| Track | Idea | Start when |
|---|---|---|
| mmWave radar obstacle detection | TI IWR6843 front and rear, as in the v1 notes | After lidar + camera obstacle detection works outdoors |
| Self-contained navigation module | Cheap GNSS + IMU + Doppler radar + INS on an STM32, as in the v1 notes | When phase 5 shows where RTK + fusion is still not good enough |
| Other treatments | Hot water, mechanical tool, low-power laser in an enclosure | If chemical rules tighten, or for paths and terraces |
| Docking and charging | F10 | After phase 5 |
| Pushing tools | F11, needs the strong outdoor chassis | After phase 5 |

## Budget

| Item | Status | Estimate (DKK) |
|---|---|---|
| ROSMASTER M1 Superior kit with Jetson Orin Nano Super (list price US$1,169.90 before shipping and VAT) | **Bought** | – |
| Downward camera (USB or CSI) + mount | To buy | 300–800 |
| Spray module (pump, 1–2 valves, MOSFET/relay module, tank, nozzles, tubing) | To buy | 500–1,200 |
| E-stop, fuses, wiring | To buy | 200–500 |
| RTK GNSS board (~€223) + multiband antenna (phase 0 survey and phase 3) | To buy | 2,200–3,000 |
| Own RTK base station (optional) | Maybe | 2,200–3,000 |
| Outdoor chassis (phase 4): option A used mower + conversion, or B hoverboard base | Later | 1,500–8,000 |
| **Total for stage 1 (excluding base station)** | | **≈ 3,200–5,500** |

Only the GNSS board price was verified during research. The rest are estimates to check when ordering.

## How we work

- **GitHub milestones = phases**, issues = tasks. Each phase's exit criterion is a checklist issue.
- **Branches:** `v2` is the base branch for the new start. Feature branches come from `v2` and are merged back with a pull request.
- **Yahboom's code and documentation are not copied into our repo.** Link to
  [YahboomTechnology/ROSMASTER-M1](https://github.com/YahboomTechnology/ROSMASTER-M1) instead, and keep our own
  ROS 2 packages separate from `~/yahboomcar_ros2_ws`.
- **Every measurement goes into the repo** (`docs/results/` with date, setup and numbers), so decisions can be traced.
- **Weekly 30-minute check-in:** what was measured, what blocks, what is next.

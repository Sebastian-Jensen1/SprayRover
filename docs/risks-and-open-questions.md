# Risks and Open Questions

Ranked by how likely each risk is to stop the project, and what we do about it.
Review this list at the end of every phase in the [project plan](project-plan.md).

## Risks

| # | Risk | Likelihood | Impact | Mitigation | Phase |
|---|---|---|---|---|---|
| R1 | **Weed detection in the lawn is not good enough** (shade under trees, mixed lawn, small weeds) | High | High | Our own dataset from the real garden. Camera hood + LED lighting for even light. Segmentation model. Measure P1 before building autonomy | 0–1 |
| R2 | **Spray misses** because of timing, wind or camera calibration | Medium | High | Short camera-to-nozzle distance, low nozzle height, spray shield. Test on paper targets first | 1 |
| R3 | **RTK doesn't work in large parts of the garden** (trees, house walls) | High | Medium | Phase 0 GNSS survey before choosing a fix. Fusion with IMU and odometry. Camera-based localization or UWB in the problem areas. Slow down or stop when uncertain | 0, 3, 5 |
| R4 | **Rules prevent using a real herbicide from a robot** | Medium | High | Ask Miljøstyrelsen in phase 0. Water for all development. Swappable treatment head (hot water, mechanical) | 0 |
| R5 | **Scope creep**: building 4WS, radar and our own INS before the MVP works (the v1 problem) | High | High | Research tracks are explicitly phase 6. Each phase has an exit criterion. "Reuse first" rule | All |
| R6 | **Integration with ROS 2 takes longer than expected** for a team new to it | Medium | Medium | Start from Yahboom's working M1 ROS 2 setup and its Nav2/SLAM examples. Simulate in Gazebo before the garden. Keep our own nodes small | 2–3 |
| R7 | **Safety incident** (robot drives into a person, animal or flower bed) | Low | High | E-stop, watchdog and low speed from phase 1; geofence and bumper before driving outdoors | 1+ |
| R8 | **Weather and water damage** to the electronics | Medium | Medium | Splash-proof enclosures, cable glands, don't run in rain at first | 2+ |
| R9 | **Treatment doesn't kill perennial weeds** (e.g. dandelion grows back from its root) | Medium | Medium | Follow-up visits (F5) measure this. Repeat treatment. Mechanical tool as an alternative | 5 |
| R10 | **Licence conflict** when reusing (e.g. OpenMower documentation is non-commercial, Yahboom's code licence unclear) | Low | Medium | Check each licence before copying. Link to Yahboom's code instead of copying it. Keep our own code under a clear licence | 0 |
| R11 | **The M1 can't drive on the lawn** (28 cm long, ~8 cm mecanum wheels) | Certain | Medium | Planned for. Stage 1 develops on indoor, terrace and path surfaces. The outdoor chassis (phase 4) is needed for the lawn | 4 |
| R15 | **The M1 can't carry the spray module** (small motors, payload not published) | Medium | Medium | Measure payload in phase 0. Small tank (0.2–0.5 L). Mount the pump at the back over the axle | 0–1 |
| R12 | **M1 electronics damaged outdoors** (moisture, dust, sun heat on the Jetson) | Medium | High | Outdoor tests only in dry weather and under supervision. Cover over the electronics. SSD backup in phase 0 | 3 |
| R13 | **Lock-in to Yahboom's software image** (ROS 2 Humble, their workspace and drivers) | Medium | Medium | Back up the image. Keep SprayRover packages in their own workspace. Plan the move to ROS 2 Jazzy (Humble support ends May 2027) | 0, 4 |
| R14 | **Small battery** (12.6 V, 6000 mAh) limits test time | Medium | Low | Measure runtime in phase 0. Buy a second pack if needed | 0 |

## Open questions

| # | Question | How we answer it | Needed by |
|---|---|---|---|
| Q1 | How much of the garden has RTK fix? Where are the dead zones? | GNSS survey | End of phase 0 |
| Q2 | Is an NTRIP correction service available and affordable at the address, or do we need our own base? | Check providers; otherwise build a base | Phase 0 |
| Q3 | Which outdoor chassis: converted robot mower, hoverboard base or 4-wheel steering? | Phase 3 outdoor tests and stage 1 results | Phase 4 |
| Q4 | Which weeds matter most in the target garden? | Photo survey and labelling | Phase 1 |
| Q5 | May an approved ready-to-use product be applied by an automated spot sprayer in a private garden? | Written question to Miljøstyrelsen | Phase 0 (answer before phase 4) |
| Q6 | UM980 or ZED-F9P? | Both work over USB with the Jetson; choose on ROS 2 driver support and community | Phase 0 |
| Q7 | Is the Orin Nano Super fast enough for YOLOv11 segmentation at working speed? | Benchmark in phase 0/1 | Phase 1 |
| Q8 | Which licence for SprayRover itself (e.g. MIT for code, CERN-OHL for hardware)? | Team decision | Phase 0 |
| Q9 | ~~Mecanum or Ackermann?~~ **Answered: mecanum** (Yahboom's official parameters). Still to confirm: Superior kit (depth camera) or Standard (pan-tilt camera), which lidar | Check the robot and `~/.bashrc` | Phase 0, week 1 |
| Q10 | Can the M1's 12 V output power the pump and valve, or do we need a separate supply? | Check the expansion board rating, measure the pump's current | Phase 1 |

## What v1 taught us

- The `main` branch also has the team's note from 12 Oct 2026 about the ROSMASTER M1. It added Yahboom's
  repository as a submodule without a `.gitmodules` file, so other people can't check it out. v2 links to
  Yahboom's repository instead.
- The v1 repository is still on the `dev` and `main` branches: tidied design notes, an architecture draft,
  CI, and 4-wheel-steering kinematics with tests and a viewer. Nothing is lost.
- **Lesson 1:** v1 started with the chassis and its own Kalman filter, the parts that are least unique and
  most work. v2 starts with weeds.
- **Lesson 2:** pinning dependency versions saves time. SimpleFOC broke on a new STM32 core release in v1.
  v2 pins ROS 2, OWL and model versions too.
- **Lesson 3:** a visual prototype is useful early. v2 keeps doing quick demos: M1 indoors, then terrace, then lawn.

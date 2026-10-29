# Our Platform: Yahboom ROSMASTER M1

This is the robot the team has bought. It is the starting point for SprayRover v2. This document says exactly
what it is, what it can do out of the box, and what it can't do for our garden use case.

Sources, read October 2026:
- Yahboom's product page and its product images, including the official "Product parameters" sheet
  ([yahboom.store](https://www.yahboom.store/products/rosmaster-m1))
- Yahboom's documentation repository
  ([YahboomTechnology/ROSMASTER-M1](https://github.com/YahboomTechnology/ROSMASTER-M1), course PDFs)
- The team's note from 12 October 2026 on `main`

Values marked **(measure)** are not published by Yahboom and must be measured on the robot.

## 1. What we bought

The team note (12 Oct 2026) says:
> One Yahboom ROS2 Robot for Jetson Orin Nano 8GB Super Ros Ackerman Car,
> see https://www.yahboom.net/study/ROSMASTER-M1

The same commit added the factory system image `ROSMASTER_M1_OrinNano_20251224.img` (to `.gitignore`) and
Yahboom's M1 documentation repository as a submodule.

**Most likely kit: "Superior-with / Orin NANO SUPER-8GB", listed at US$1,169.90** (before shipping, import VAT
and duties). It is the only Jetson Orin Nano Super version of the M1 the Yahboom shop actually sells. The other
Orin variants are listed at a placeholder price of $10,000, which means they are not for sale.
The Superior kit has the depth camera instead of the pan-tilt camera.

**Wheels: mecanum, not Ackermann.** Every Yahboom source describes the M1 with four mecanum wheels: the
product title, the parameter sheet, the images and the documentation. The word "Ackerman" in the note
probably comes from a shop listing title, or from the fact that the same controller board also supports
Ackermann robots (e.g. ROSMASTER A1). A quick look at the robot confirms it: mecanum wheels have small
rollers around the rim.

## 2. Hardware (official parameters)

| Part | Value | Source |
|---|---|---|
| **Size** | **284.4 × 231.4 × 181.4 mm** (L × W × H, height including lidar). Body 124 mm wide between the wheels, 147.5 mm high without the lidar | Parameter sheet |
| Wheels | 4 × **mecanum** wheels. Diameter about 75–80 mm estimated from the drawing **(measure)** | Parameter sheet, images |
| Motors | 4 × **1:56 high-torque 520 encoder metal motor** | Parameter sheet |
| Body | Oxidised sandblasted aluminium alloy | Parameter sheet |
| Main computer | **NVIDIA Jetson Orin Nano SUPER 8 GB** with **256 GB SSD**. 4 × USB 3.0, Ethernet, 40-pin GPIO, 2 × 22-pin CSI camera connectors, CAN header, M.2 slots. Wi-Fi antennas included | Parameter sheet, kit image, course 16 |
| OS + ROS | **Ubuntu 22.04 LTS + ROS 2 Humble** | Parameter sheet |
| Controller board | Yahboom ROS robot control board (YB-ERF01 V3.0) with **STM32F103RCT6** and a **9-axis IMU (ICM20948)**. 4 motor drivers (AM2861), 12 V input with switch, 12 V and 5 V outputs, CAN, SBUS, PWM servo outputs (5/6.8 V), serial-servo port, I²C, buzzer, RGB strip. Connects to the Jetson over USB | Product images, course 23 |
| Lidar | **YDLIDAR T-mini Plus**: ToF ranging, 0.05–12 m, up to 4,000 samples/s, 60 klux anti-glare, "indoor and outdoor" according to Yahboom | Product images |
| Depth camera | **Angstrong Nuwa-HP60C**: 0.2–4 m working distance, 73.8° horizontal field of view, adjustable pitch. RGB + depth + point cloud | Product images, course 10 |
| Battery | **12.6 V, 6000 mAh** pack (3S Li-ion). DC 4.0 × 1.7 mm power socket, 12.6 V charger | Parameter sheet |
| Also in the kit | Wireless gamepad, OLED display, AI voice module with speaker (CM108B + CI1302), USB hub board, tools, cables | Kit image |
| Control options | PC (ROS 2), wireless gamepad, Yahboom map-navigation app (iOS/Android) | Parameter sheet |

**Not published, so measure on our robot:** weight, top speed, payload, ground clearance, runtime per charge,
wheelbase and track width (needed for the URDF and for odometry).

## 3. Software out of the box

| Item | Details |
|---|---|
| ROS setup | On the Orin, ROS 2 runs directly on the system (no Docker). Workspace `~/yahboomcar_ros2_ws/`. Environment: `my_robot_type: M1`, `my_lidar: tmini`, `my_camera: nuwa`, `ROS_DOMAIN_ID: 61` (set in `~/.bashrc`) |
| Factory image | `ROSMASTER_M1_OrinNano_20251224.img` (December 2025). **Keep a copy.** Course 16 explains how to back up and restore the SSD |
| Driving | ROS 2 velocity control, gamepad, keyboard, app. Linear and angular velocity calibration. URDF model (`display_M1.launch.py`). The gamepad program **starts automatically at boot** and must be turned off before development (course 01) |
| Sensors in ROS | IMU from the STM32 board, lidar scans, depth camera topics (`/ascamera_hp60c/camera_publisher/rgb0/image`, `.../depth0/points`) |
| Mapping | gmapping, Cartographer, slam_toolbox, **RTAB-Map** (camera + lidar) |
| Navigation | **Nav2** single-point and multi-point navigation with obstacle avoidance, AMCL localization on a saved map. Lidar obstacle avoidance, following and patrol |
| Vision / AI | **YOLOv11 on the Orin**: object detection, **instance segmentation**, dataset annotation, training and conversion (course 13). Mediapipe, OpenCV. Large-language-model voice and vision demos (not needed for SprayRover) |
| Firmware | Course 23 covers the STM32 board firmware (motors, IMU, servos, CAN) |

## 4. What this means for SprayRover

**The most important number is the size.** At 28 × 23 cm with wheels of about 8 cm, the M1 is a tabletop and
indoor robot. A normal lawn (grass 3–6 cm high) is as tall as half its wheels. Driving on the lawn is not
realistic, even before considering how mecanum rollers behave on grass.

| SprayRover need | Can the M1 do it? | Notes |
|---|---|---|
| ROS 2 + Nav2 (concept D1) | ✅ Yes, out of the box | Humble. Supported until May 2027, so plan a move to Jazzy |
| Weed detection (F1) | ✅ Strong | Orin Nano Super with YOLOv11 segmentation, annotation and training documented. No extra AI hardware needed |
| Camera looking down at the ground | ⚠️ Needs a mount | The depth camera points forward and can tilt. Add a small downward USB or CSI camera at the front |
| Spraying (F2) | ⚠️ Small add-on | Small 12 V pump + valve switched by a MOSFET module from a Jetson GPIO pin. Power from the board's 12 V output **(check its current rating)**. The payload is small, so use a small tank (≈ 0.2–0.5 L) **(measure what it can carry)** |
| Indoors, terrace, paved paths | ✅ Yes | Lidar SLAM + AMCL + Nav2 is made for flat, hard surfaces. This is where stage 1 happens |
| Driving on a lawn | ❌ No | Too small and too low (see above) |
| Garden positioning (F3, F7) | ⚠️ Partly testable | RTK GNSS on USB + robot_localization can be developed and tested on the terrace and paths. The real lawn test needs the outdoor chassis |
| Weather (C5) | ❌ No | Open electronics. Dry weather only, short supervised tests |
| Push tools (F11) | ❌ No | Small motors |
| Safety (C3) | ⚠️ Partly | Power switch, gamepad and "force stop" in the keyboard tool. Add an E-stop in the battery line and a watchdog in our nodes |

**Conclusion:** the M1 is an excellent **development platform for the software brain** of SprayRover:
- weed detection on the Orin,
- the spray trigger and its timing,
- the weed map, and
- ROS 2 mapping, navigation and coverage.

All of this can be built and tested indoors and on the terrace with real or printed weed samples. It is **not
the garden robot**. Once the software works, the Jetson, the sensors and the software move to an outdoor
chassis in phase 4 of the [project plan](project-plan.md). Because everything is ROS 2, only the drive driver
and the URDF model change.

## 5. First-week checklist

1. Confirm the kit: depth camera (Superior) or pan-tilt camera (Standard)? Check `~/.bashrc` for `my_lidar` and `my_camera`.
2. **Back up the factory SSD image** before changing anything (course 16, "Backup SSD system").
3. Weigh the robot. Measure wheel diameter, wheelbase, track width and ground clearance. Measure runtime on one full charge.
4. Run the gamepad demo, then turn off the auto-start gamepad program (course 01) and drive the robot from ROS 2.
5. Make a map of a room with slam_toolbox and run Nav2 to a goal (course 11). That proves the toolchain works.
6. Run the YOLOv11 segmentation demo on the Orin (course 13) and note the frames per second.
7. Measure top speed and how much weight it can carry without struggling (start with 0.5 kg).
8. Short supervised drive on the terrace or a paved path in dry weather. Check that the lidar works in daylight.

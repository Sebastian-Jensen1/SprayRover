# Our Platform: Yahboom ROSMASTER M1

This is the robot the team has bought. It is the starting point for SprayRover v2. This document says exactly
what it is, what it can do out of the box, and what it can't do for our garden use case.

Sources: Yahboom's official documentation repository
[YahboomTechnology/ROSMASTER-M1](https://github.com/YahboomTechnology/ROSMASTER-M1) (course PDFs, read
October 2026), the team's note from 12 October 2026 on `main`, and retailer listings. Values marked
**(check)** are not in Yahboom's documentation and must be confirmed on the robot itself.

## 1. What we bought

The team note (12 Oct 2026) says:
> One Yahboom ROS2 Robot for Jetson Orin Nano 8GB Super Ros Ackerman Car,
> see https://www.yahboom.net/study/ROSMASTER-M1

The same commit added the factory system image `ROSMASTER_M1_OrinNano_20251224.img` (to `.gitignore`) and
Yahboom's M1 documentation repository as a submodule. All three point to the **ROSMASTER M1 with a Jetson Orin
Nano 8GB Super**.

> ⚠️ **Check the wheels.** Yahboom's documentation describes the M1 with **mecanum wheels** (wheels with small
> angled rollers that let the robot drive sideways), not Ackermann (car-like) steering. Yahboom sells
> Ackermann robots under other names (e.g. ROSMASTER A1 PRO). The word "Ackerman" in the note probably comes
> from a shop listing title. **Look at the robot:** rollers around each wheel mean mecanum, front wheels that
> turn like a car mean Ackermann. This document assumes mecanum.

## 2. Hardware

| Part | What it is | Source |
|---|---|---|
| Main computer | **NVIDIA Jetson Orin Nano 8GB Super**, 4× USB 3.0, Ethernet, 40-pin GPIO, 2 camera connectors (22-pin CSI), CAN header, M.2 slots for SSD. Yahboom sells a "SUB" board (with power button) and the official dev kit **(check which)** | Course 16 "Jetson Orin board introduction" |
| Chassis | 4 **mecanum wheels**, 4 × **520 encoder motors** (1:56 gear ratio), anodised aluminium body | M1 README, course 23, retailer listing |
| Controller board | Yahboom **ROS expansion board V3.0** with an STM32 microcontroller. 4 motor drivers (AM2861), 12 V input with switch, 12 V and 5 V outputs, **ICM20948 9-axis IMU**, CAN, SBUS (RC receiver), PWM servo outputs (5 V or 6.8 V), serial-servo port, I²C, buzzer, RGB strip, user button. Connects to the Jetson over micro-USB | Course 23 "About expansion board V3.0" |
| Battery | **12.6 V, 6000 mAh** pack (3S Li-ion) with a 12.6 V / 2 A charger | Retailer listing |
| Lidar | 2D lidar, **YDLIDAR T-mini Plus** (default) or **Slamtec C1**. Which one is set in `~/.bashrc` (`my_lidar`) | Course 06 "ROS control", course 11 |
| Depth camera | **Angstrong "Nuwa" HP60C**: RGB image, depth image, point cloud (`ascamera` driver). Superior kit | Course 10, course 06 |
| Other camera | 2 MP USB camera on a 2-servo pan-tilt (PTZ). Standard kit | M1 README, course 01 |
| Remote control | Gamepad with USB receiver. A joystick program **starts automatically at boot** and must be turned off before development | Course 01 |
| Optional | AI voice module | M1 README |

**Measure on our robot (check):** length × width × height, weight, wheel diameter, ground clearance, top speed,
runtime per charge, which kit (Standard or Superior), which lidar and camera are mounted, payload it can carry.

## 3. Software out of the box

| Item | Details |
|---|---|
| OS + ROS | Ubuntu with **ROS 2 Humble**. On the Orin, ROS runs directly on the system (no Docker). On Raspberry Pi / Jetson Nano versions it runs in Docker |
| Workspace | `~/yahboomcar_ros2_ws/`. Robot type set with environment variable `my_robot_type: M1`, `ROS_DOMAIN_ID: 61` |
| Factory image | `ROSMASTER_M1_OrinNano_20251224.img` (December 2025). **Keep a copy.** Course 16 explains how to restore and back up the SSD |
| Driving | ROS 2 topic control (velocity, buzzer, servos), gamepad, keyboard. Linear and angular velocity calibration. URDF model (`display_M1.launch.py`) |
| Sensors in ROS | IMU and lidar data from the STM32 board, depth camera topics (`/ascamera_hp60c/camera_publisher/rgb0/image`, `.../depth0/points`) |
| Mapping | gmapping, Cartographer, slam_toolbox, **RTAB-Map** (camera + lidar) |
| Navigation | **Nav2**: single-point and multi-point navigation with obstacle avoidance, AMCL localization on a saved map. Lidar obstacle avoidance, following and patrol |
| Vision / AI | **YOLOv11 on the Orin**: object detection, **instance segmentation**, dataset annotation, model training and conversion (course 13). Mediapipe, OpenCV, colour and object tracking. Large-language-model voice and vision demos (not needed for SprayRover) |
| Firmware | Course 23 covers the STM32 board firmware (motors, IMU, servos, CAN) in detail, so we can change it if needed |

## 4. What this means for SprayRover

| SprayRover need | Can the M1 do it? | Notes |
|---|---|---|
| ROS 2 + Nav2 (concept D1) | ✅ Yes, out of the box | Humble instead of Jazzy. Humble is supported until May 2027, so plan a move to Jazzy then |
| Weed detection (F1) | ✅ Strong | The Orin Nano Super is much faster than a Raspberry Pi. YOLOv11 segmentation, training and annotation are documented. We no longer need a separate Pi + AI accelerator |
| Camera looking down at the ground | ⚠️ Needs a mount | The cameras point forward. Add a downward camera (USB or CSI) at the front, or tilt the PTZ camera down |
| Spraying (F2) | ⚠️ Needs a small add-on | 12 V pump + solenoid valve switched by a MOSFET/relay module from a Jetson GPIO pin. The 12 V output on the expansion board can power them **(check current rating)** |
| Mapping and navigation indoors, on a terrace or a path | ✅ Yes | Lidar SLAM + AMCL is made for this. Good for developing everything except lawn driving |
| Driving on a lawn | ❌ Probably poor | Mecanum rollers are made for flat, hard floors. Expect slipping, clogged rollers and bad wheel odometry on grass, and the small wheels have low ground clearance. **Test this in phase 0** |
| Garden positioning (F3, F7) | ⚠️ Add RTK GNSS later | Lidar SLAM finds walls and trees but an open lawn has few features. RTK GNSS on USB + robot_localization fits into the existing ROS 2 setup |
| Weather (C5) | ❌ No | Open electronics, indoor robot. Dry weather only, short outdoor tests under supervision |
| Push tools (F11) | ❌ No | Small 12 V motors |
| Safety (C3) | ⚠️ Partly | Has a power switch and gamepad. Add an E-stop button in the battery line and a watchdog in our nodes |

**Conclusion:** the M1 is an excellent **development platform** for the software brain of SprayRover:
- weed detection on the Orin,
- the spray trigger,
- the weed map, and
- ROS 2 navigation.

It saves months of work. It is most likely **not the final garden robot**, because of the mecanum wheels on
grass, missing weather protection and the small motors. The plan is therefore:
1. Build and prove the whole software stack on the M1 indoors, on terrace/paths and on short dry lawn.
2. Later, move the Jetson, sensors and software to an outdoor chassis. That can be a converted robot mower, a
   hoverboard base or the 4-wheel-steering design from v1.

Because everything is ROS 2, only the drive driver and the URDF model change when we switch chassis.

## 5. First-week checklist

1. Look at the wheels: mecanum or Ackermann? Write the answer in this document.
2. Note the kit (Standard/Superior), lidar model and camera model (see `~/.bashrc`).
3. **Back up the factory SSD image** before changing anything (course 16, "Backup SSD system").
4. Measure size, weight, wheel diameter, ground clearance. Measure runtime with one full charge.
5. Run the gamepad demo, then turn off the auto-start joystick program (course 01) and drive it from ROS 2.
6. Make a map of a room with slam_toolbox and run Nav2 to a goal (course 11). That proves the toolchain works.
7. Run the YOLOv11 segmentation demo on the Orin (course 13) and note the frames per second.
8. Short supervised drive on dry, short lawn: does it drive straight? Does it get stuck? Record a video.

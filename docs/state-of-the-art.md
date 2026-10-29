# State of the Art

What already exists for robots that find and treat weeds, and what SprayRover can reuse or learn from.
Researched October 2026. Vendor figures are the vendors' own claims unless noted otherwise.

## 1. Summary

- **Weed treatment that targets one plant at a time (spot spraying, lasers, mechanical tools) is commercial
  in agriculture** and has been moving into turf in 2026. It is still almost absent from private gardens.
- **The few products for home gardens are either very simple or very new.**
  - Tertill is a small solar robot that cuts small weeds in vegetable beds.
  - GreenBeam is a lawn robot that treats single weeds with light, but has no independent tests yet.
- **Navigating a garden under trees and next to walls is the problem robot-mower makers have spent the last
  five years on.** Their answer is RTK GNSS combined with something that doesn't need satellites:
  cameras (visual localization), UWB beacons, lidar, plus an IMU and wheel odometry.
- **There are strong open-source building blocks:**
  - OpenWeedLocator (weed detection + spray valves on a Raspberry Pi)
  - OpenMower (RTK robot mower on ROS)
  - Acorn (open-source farm rover with four steerable, driven wheels)
  - FarmBot (garden robot with weed detection)
  - ROS 2 Nav2 with robot_localization and Fields2Cover (navigation and coverage planning)
- **Conclusion for SprayRover:** most parts can be reused, starting with the ROSMASTER M1 the team already has. What is new and valuable is the combination:
  a low-cost, open robot that **detects weeds in a lawn or garden, treats each one, remembers where it was,
  and works under trees.**

## 2. Commercial weeding and spot-spraying systems

| Product | Segment | How it treats weeds | Navigation | Relevance for us |
|---|---|---|---|---|
| [Tertill](https://www.bobvila.com/articles/tertill-weeding-robot-review/) | Home vegetable beds (~18 m²) | Cuts small plants with a string trimmer. Anything tall enough to touch its front sensor is treated as a crop and avoided | Random driving inside a 10 cm barrier | Shows a home robot can be simple and cheap (~$250–350). Reviewers report trouble on uneven ground |
| [GreenBeam](https://www.greenbeam.us/) | Home lawns | Treats single weeds with light instead of spraying | Autonomous, all-wheel drive (vendor page) | Closest to our idea. Marketing only; no independent tests found |
| [Ecorobotix ARA](https://www.topfarmrobots.com/category/spraying) | Row crops | Camera + AI, sprays single weeds. Vendor claims up to 95% less herbicide | Tractor-mounted | Proves that spot spraying works at scale |
| [Ecorobotix ALBA](https://ecorobotix.com/en-us/blog/ecorobotix-enters-turf-care-introducing-alba-the-ai-powered-ultra-high-precision-sprayer-for-golf-course-turf-management/) (launched Jan 2026) | Golf courses, sports turf | 108 nozzles, spray spots down to ~3 × 3 cm, up to ~7 km/h ([Golfdom](https://www.golfdom.com/this-ai-spot-sprayer-can-detect-weeds-the-size-of-a-golf-ball/)) | Tractor-mounted | **Detecting weeds in turf is now commercial**, which is our exact use case at a larger scale |
| [Frost ASTRO](https://www.golfcourseindustry.com/news/frost-spray-autonomous-technology-greens/) | Golf greens | Autonomous sprayer | Autonomous (partner Mach) | Autonomy for turf is arriving |
| John Deere See & Spray | Row crops | Camera-triggered nozzles on a boom | Tractor | The industry benchmark |
| [FarmDroid FD20](https://farmdroid.com/products/farmdroid-fd20/) (Danish) | Row crops | Seeds, weeds mechanically, micro-sprays | RTK GNSS, solar powered | Danish, RTK-based, solar. Shows how simple a field robot can be when it knows exactly where it seeded |
| [Earth Rover CLAWS](https://www.agri-tech-e.co.uk/trials-show-claws-robot-can-accurately-target-weeds-with-killer-beam/) | Vegetables | Concentrated light/laser, weeds from 1 mm | RTK GNSS, AI vision | Light-based treatment without chemicals on a lightweight robot |
| [Odd.Bot Maverick](https://futurefarming.com/tech-in-focus/field-robots/odd-bot-takes-to-the-fields-with-maverick-weeding-robot) | Vegetables | Mechanical weed removal driven by AI vision | Autonomous | Mechanical treatment as an alternative to chemicals |

**Research prototype worth copying:** the University of Arkansas built a **push-cart** spot sprayer for turf.
In trials it used up to 62% less herbicide than broadcast spraying
([UADA](https://aaes.uada.edu/news/precision-turfgrass-weed-control/)).
It shows that detection and spraying can be developed and tested **without an autonomous robot**.

## 3. Robot mowers: the best reference for navigating a garden

Robot mowers solve our navigation problem in the same environment: private gardens with trees, walls and
borders. The market has moved from boundary wires to wire-free navigation.

| Approach | Example | Notes |
|---|---|---|
| RTK GNSS only | Early wire-free mowers | Works in open lawns. Under trees and near walls the signal is blocked, weakened or reflected (multipath), which gives dropouts or sudden position jumps ([Mowrator](https://mowrator.com/blogs/news/rtk-robot-mower-signal-loss-trees), [RTKdata](https://rtkdata.com/blog/wire-free-robot-mower-rtk-accuracy-guide-2026/)) |
| RTK + cameras (VSLAM) | Kress EyePilot RTKⁿ, Sunseeker | Camera recognises lawn edges, trees and walls to keep the position stable when satellite signal weakens ([Kress](https://www.kress.com/en-ie/?p=1298295), [Sunseeker](https://sunseekertech.com/us/glossary/rtk-vslam)) |
| RTK + vision + lidar | Mammotion (Tri-Fusion), MOVA | Switches sensors depending on conditions ([Mammotion](https://au.mammotion.com/blogs/news/ai-vision-vs-rtk-vs-lidar)) |
| UWB beacons | Ecovacs GOAT G1 | 2–4 beacons around a 600 m² garden, combined with GPS and inertial navigation. Vendor claims cm-level accuracy, not independently tested ([Ecovacs](https://www.ecovacs.com/global/campaign/goat-robotic-lawn-mower)) |

**Lessons:**
1. RTK alone is not enough under trees, and the industry agrees on this.
2. The proven fix is **sensor fusion**: GNSS + IMU + wheel odometry + one sensor that doesn't use satellites
   (camera or UWB).
3. Fusion quality depends on calibration and software, not just on having the sensors
   ([Sunseeker](https://sunseekertech.com/us/glossary/rtk-vslam)).

The original SprayRover idea (GNSS + IMU + ESKF + UWB) is in line with what the industry does. It is not an
unsolved research problem, but it is a lot of integration work.

## 4. Open-source projects we can build on

| Project | What it is | What we can reuse |
|---|---|---|
| [OpenWeedLocator (OWL)](https://github.com/geezacoleman/OpenWeedLocator) | Raspberry Pi + camera + relay board that switches 12 V spray valves. Published in *Scientific Reports* (2022); MIT license, Python | **The design for our spray module** (relay board + 12 V valves). Its code is Python; check that it runs on the M1's Jetson. Green-on-brown detection (plants on soil, gravel, paths) works out of the box. Green-on-green (weeds in a lawn) has been added with a Coral accelerator. Supports Pi 5 + picamera2. A unit costs about $400 ([Raspberry Pi Magazine](https://magazine.raspberrypi.com/articles/open-weed-locator)) |
| [OpenMower](https://github.com/ClemensElflein/OpenMower) | Turns a cheap robot mower (YardForce/SUMEC family) into an RTK-navigated one. Raspberry Pi + RP2040 + ArduSimple RTK. Navigation in ROS ([open_mower_ros](https://github.com/ClemensElflein/open_mower_ros)) | **A complete, working garden robot to start from:** chassis, motors, battery, RTK navigation, app. About €700 of hardware excluding the mower and base station. Documentation is CC BY-NC-SA (non-commercial); software is GPL/MIT per repository |
| [Acorn (Twisted Fields)](https://twistedfields.readthedocs.io/en/latest/overview.html) | Open-source farm rover. 4 identical corners with drive and steering motors, RTK GNSS, Python on Raspberry Pi, SimpleFOC on RP2040 motor controllers | **Reference for the 4-wheel-steering design** from v1. Shows the corner-module approach works, but also how much mechanical work it is |
| [FarmBot](https://software.farm.bot/v15/app/photos/weed-detection) | Gantry robot for raised beds. Takes photos, detects weeds by colour, marks them as "pending" on a map, removes them mechanically | **The weed-map concept:** detect, store position, treat, check again |
| [hoverboard-firmware-hack-FOC](https://gitee.com/dream_maker_w/hoverboard-firmware-hack-FOC) | Open FOC firmware for stock hoverboard mainboards (STM32F103/GD32F103). Serial control from a Raspberry Pi/Arduino | **A cheap 36 V drive.** It fixes v1's open question about a B-G431B-ESC1 controller on 36 V motors: one stock hoverboard board drives two hub motors |
| [ROS 2 Nav2](https://github.com/open-navigation) + [robot_localization](https://automaticaddison.com/?p=12035) + [opennav_coverage / Fields2Cover](https://github.com/open-navigation/opennav_coverage) | Standard open navigation stack. robot_localization fuses GNSS, IMU and odometry (EKF/UKF). opennav_coverage plans lawn coverage paths | **Navigation software we don't have to write.** Several outdoor GNSS + coverage examples exist on ROS 2 Jazzy ([arXiv 2609.01384](https://arxiv.org/pdf/2609.01384)) |

## 5. Weed detection in lawns

- Detecting weeds in turf is an active but small research area. A 2023 study trained YOLOv5–v8 on a public
  dataset of **4,203 lawn-weed images** (11,385 annotations); YOLOv8l was best, but results on new test sets
  still needed improvement ([Sportelli et al., Applied Sciences](https://mdpi.com/2076-3417/13/14/8502)).
- Segmentation (YOLOv8-seg) may handle irregular weed shapes better than bounding boxes
  ([GCM](https://gcmonline.com/research/news/advancing-ai-recognition-of-turfgrass-weeds)).
- General weed datasets such as [Weed25](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9748680/) (14,035 images)
  are farm-oriented. Small lawn datasets exist on Roboflow Universe, but are unverified.
- **Implication:** plan to **collect and label our own images from the target garden.** Lighting under trees
  and the local mix of grass and weeds matter more than the model choice.

## 6. Ways to kill a weed

| Method | Status | Notes |
|---|---|---|
| Spot spraying (herbicide) | Mature (ARA, ALBA, See & Spray, OWL) | Simplest mechanically. Limited by Danish rules for private use, see [regulations-and-safety.md](regulations-and-safety.md) |
| Spot spraying (hot water / approved low-risk products) | Possible with the same nozzle hardware | Hot water needs heating and energy; low-risk products (e.g. acetic acid or pelargonic acid based) follow the same spray path |
| Laser / concentrated light | Commercial in farming (Carbon Robotics, Earth Rover); new for homes (GreenBeam) | Research with cheap diode lasers: 47–72% of weeds removed per pass, about 8 s per weed ([Mwitta et al. 2024](https://www.frontiersin.org/articles/10.3389/fagro.2024.1388452/full)). Serious eye-safety issues |
| Mechanical (cut, pull, hoe) | Commercial (Tertill, Odd.Bot, FarmDroid, FarmBot) | No chemicals. Harder for perennial lawn weeds with deep roots (e.g. dandelion) |

## 7. Educational ROS 2 robots (our starting platform)

Yahboom's ROSMASTER series are low-cost educational ROS 2 robots with lidar, depth camera and Jetson or Raspberry Pi
computers, and with a large set of tutorials (SLAM, Nav2, YOLO). The team has bought a **ROSMASTER M1**.
It is a small indoor robot (28 × 23 × 18 cm, mecanum wheels), not a lawn robot, but it gives us a complete ROS 2 robot to develop the SprayRover software on.
See [platform-rosmaster-m1.md](platform-rosmaster-m1.md).

## 8. Where the gap is

Nobody offers an **open, low-cost robot that maps and treats single weeds in a private garden, including
under trees and along walls.**
- Farm robots are too big and expensive.
- Robot mowers navigate well but don't detect weeds.
- OWL detects and sprays but doesn't navigate.

SprayRover's value is **putting these together**, then maybe improving navigation under trees later
(the UWB / Doppler-radar / navigation-module ideas from the original notes).

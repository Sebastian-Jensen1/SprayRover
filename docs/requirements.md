# Requirements

What SprayRover must do. This builds on the original v1 notes, which are kept on the `dev` and `main` branches
under `documentation/sources/notes/`. Every requirement has an ID so the [project plan](project-plan.md) and
tests can refer to it.

Priority: **M** = must (first useful version), **S** = should, **L** = later.

Development starts on the robot the team has bought, the [Yahboom ROSMASTER M1](platform-rosmaster-m1.md).
Some requirements (lawn driving, weather) can only be met fully on the outdoor chassis planned for phase 4.

## 1. Use case

A private Danish garden: lawn, beds, gravel paths, terraces, trees and house walls. SprayRover drives around
the garden without supervision, finds weeds, treats each one, and keeps a map of where weeds were found and
treated so it can check on them later.

**First target: weeds in the lawn** (e.g. dandelion, plantain, clover), because:
- the lawn is the largest and most uniform area,
- detecting weeds in turf is proven (Ecorobotix ALBA, research datasets), and
- navigation on a lawn is what robot mowers already do.

Gravel paths and terraces come second. Detection is easier there (any green on grey), but the chemical rules are
stricter, see [regulations-and-safety.md](regulations-and-safety.md). Beds with crops come last, because
telling crop from weed in a bed is the hardest problem.

## 2. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| F1 | Detect weeds in a lawn from a downward-facing camera while driving | M |
| F2 | Treat a detected weed by spraying it, hitting within **±2 cm** of the weed centre | M |
| F3 | Drive autonomously inside a mapped garden boundary (geofence) and cover the lawn systematically | M |
| F4 | Store each detected or treated weed with position, time, image and treatment in a weed map | M |
| F5 | Re-visit stored weeds after N days to check whether they died, and treat again if needed | S |
| F6 | Follow walls and lawn edges closely: lawn edges within ±5 cm, walls within ±10 cm | S |
| F7 | Keep working under trees and next to walls, where GNSS is degraded, by using other sensors | S |
| F8 | Detect obstacles (people, animals, garden furniture, toys) and stop or drive around them | M (stop) / S (avoid) |
| F9 | Swap the treatment head between spray, hot water or a mechanical tool behind one "treat weed at (x, y)" interface | S |
| F10 | Return to a dock and charge by itself | L |
| F11 | Push or carry tools such as a grass trimmer (needs 150–200 N of pushing force, from the original notes) | L |
| F12 | Phone/web UI: start, stop, live status, weed map, logs | M (basic) / S (map) |

## 3. Performance targets (first useful version)

| ID | Target | How we measure it |
|---|---|---|
| P1 | Detection on our own test images: precision ≥ 0.85, recall ≥ 0.80 for lawn weeds ≥ 3 cm | Labelled test set taken in the target garden, never used for training |
| P2 | Spray hit rate ≥ 90% within ±2 cm, at working speed | Paper or chalk targets plus coloured water |
| P3 | Position accuracy with RTK fix in open lawn ≤ 3 cm (95%) | Compare logged positions against surveyed markers |
| P4 | Position error after 10 m without GNSS (e.g. under a tree) ≤ 20 cm | Drive a known path from open lawn into the shaded area |
| P5 | Covers a 200 m² lawn in ≤ 2 hours | Timed runs |
| P6 | Spray volume at least 80% lower than spraying the whole area | Volume used, compared with label dose × area |
| P7 | Stops within 0.3 m of an E-stop or watchdog event at working speed | Measured stop distance |

## 4. Constraints

| ID | Constraint |
|---|---|
| C1 | **Cost:** the ROSMASTER M1 is already bought. Stage 1 add-ons ≤ 5,500 DKK, the outdoor chassis ≤ 8,000 DKK, excluding tools and an optional RTK base station. Re-use off-the-shelf parts before designing PCBs |
| C2 | **Legal:** development with water only. Real use only with products approved for private use, applied according to their label |
| C3 | **Safety:** E-stop, wireless stop, watchdog, geofence, low speed, normally-closed valve (see [regulations-and-safety.md](regulations-and-safety.md)) |
| C4 | **Open source:** our own code and designs are published. Reused parts must allow this; check licences such as OpenMower's CC BY-NC-SA documentation |
| C5 | **Weather:** splash-proof electronics (IP54 as a target). Operating range 5–30 °C, dry or light drizzle |
| C6 | **Team:** a small hobby team. Prefer existing software (ROS 2, Nav2, Yahboom's M1 stack, OWL) over writing our own when the result is similar |
| C7 | **Platform:** development starts on the [Yahboom ROSMASTER M1](platform-rosmaster-m1.md) (Jetson Orin Nano Super, ROS 2 Humble). SprayRover code only uses standard ROS 2 topics and services, so it can move to an outdoor chassis later |

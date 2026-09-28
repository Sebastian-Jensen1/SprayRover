# Mechanical Design and Drivetrain

> Source: [`sources/notes/first-design.md`](../sources/notes/first-design.md) (original notes, Danish).
> Status: **concept**. Nothing has been bought or built yet.

## Chassis concept

The most common layout for rovers that drive over rough terrain is the NASA/JPL Mars rover, which is published as the
[nasa-jpl/open-source-rover](https://github.com/nasa-jpl/open-source-rover).

| Option | Pros | Cons |
|---|---|---|
| 6 wheels, each able to steer (JPL original) | Best proven design | Expensive and complex to build |
| 6 wheels, fixed ([video](https://www.youtube.com/watch?v=N7xY_O0PeXE)) | Simpler than the original | Still expensive; skid steering |
| **4 wheels, each able to steer** | Much simpler and cheaper | Less capable on very rough terrain |

**Chosen direction: 4 wheels, each with its own steering.** Inspiration:
[ITU Rover Team](https://mkn.itu.edu.tr/en/students/project-teams/itu-rover-team),
[example 1](https://www.youtube.com/watch?v=4K8A91jxjwg),
[example 2](https://www.youtube.com/watch?v=XiqmVLrzhZ0).

With four steerable wheels the rover can use Ackermann steering, turn on the spot and drive sideways ("crab").
Crab steering is useful for following walls and lawn edges precisely.

## Steering servos

- **Feetech STS3215** (the notes say "STS321", which is probably a typo, see [open questions](open-questions.md)), about €20 each.
- Serial bus servos on **RS485**. All 4 are daisy-chained back to the controller.
- Each servo reports its position, load and temperature, so the controller can check that the wheels really reached their commanded angles.

## Drive motors

- **10" hoverboard hub motors**, with the motor and position feedback (Hall sensors) built into one wheel unit. Plug-and-play and cheap to buy (Alibaba/Amazon).
- Power requirement:
  - **about 100 W per wheel** for the rover on its own.
  - **250–350 W per wheel** if it has to push a tool rover such as a grass trimmer.
- Estimated pushing force: **150–200 N** (rough estimate).
- Tyres **must be air-filled with a deep off-road tread**. Standard hoverboard tyres are solid and nearly smooth.

## Motor controllers (FOC)

- **ST [B-G431B-ESC1](https://www.st.com/en/evaluation-tools/b-g431b-esc1.html)**: a development kit that controls one motor with field-oriented control (FOC).
  It talks to the controller over UART. We can make our own cheaper PCB later.
- Firmware: **[SimpleFOC](https://www.simplefoc.com/)**, open-source closed-loop control that works out of the box on ST FOC hardware
  ([examples](https://www.simplefoc.com/example_projects), [STM32 guide](https://docs.simplefoc.com/stm32_mcu)).
- One ESC per wheel, so **4 ESCs** in total.

> ⚠️ **Check the voltage:** hoverboard hub motors normally run from a 36 V (10S) battery. The B-G431B-ESC1 is rated
> well below that. Its datasheet gives a maximum of about 25 V, but this has to be checked. See [open questions](open-questions.md).

## Reference projects

These are useful to review for ideas, including by asking an AI to compare them with our design.

| Project | Why it is interesting |
|---|---|
| [TurtleRover](https://github.com/TurtleRover) | Small, neat 4-wheel rover |
| [jakkra/Mars-Rover](https://github.com/jakkra/Mars-Rover) | Mature, advanced DIY Mars-rover build |
| [nasa-jpl/osr-rover-code](https://github.com/nasa-jpl/osr-rover-code) | Official JPL rover control code (ROS 2, heavy) |
| [Sawppy Rover](https://github.com/Roger-random/Sawppy_Rover) | Low-cost version of the JPL rover |
| [Watney](https://github.com/nikivanov/watney) | Miniature rover **with a charging solution** |
| [HyphaROS minicar](https://github.com/Hypha-ROS/hypharos_minicar) | STM32 based, includes localization maths |

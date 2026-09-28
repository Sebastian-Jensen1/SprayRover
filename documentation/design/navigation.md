# Navigation

> Source: [`sources/notes/navigation-challenge.md`](../sources/notes/navigation-challenge.md) (original notes, Danish).
> Status: **concept**. Phase 1 is the plan, the later phases are ideas.

## The problem

The rover will work in a **private garden: under trees and along house walls**. In those places GNSS signals
drop out and bounce off walls and trees before reaching the antenna (multipath). Even so, we need **position to within a few centimetres** to:

- drive precisely back and forth along walls and the edge of the lawn,
- find the same weeds again on a later run,
- repeat routes the rover has driven before.

Nobody in the DIY world has solved this cheaply. A low-cost solution would be a valuable open-source contribution,
and could also become a product.

## Phase 1: "standard solution" (GNSS + IMU + encoders + ESKF)

The plan is to start with standard parts so the rover can drive early.

**GNSS receiver: ArduSimple board in Arduino shield format.** It also fits STM32 Nucleo boards.

| Board | Module | Accuracy (from datasheets in `sources/datasheets/`) |
|---|---|---|
| [simpleRTK3B Budget](https://www.ardusimple.com/product/simplertk3b-budget/) | Unicore **UM980** | Galileo HAS: about decimetre level (HAS is still in testing). RTK: cm |
| simpleRTK2B | u-blox **ZED-F9P** | Standalone < 1.5 m; with a base station or NTRIP < 1 cm |

- **Galileo HAS** (free corrections from the Galileo satellites) gives roughly 20–40 cm, which may be enough on its own.
- **RTK base station** on the house: centimetre accuracy, but about €250 more plus cabling and a radio link.
- Both boards need a **multiband GNSS antenna**, which is sold separately.

> The original notes mix up the two boards: they say "u-blox F9P" but link the UM980-based simpleRTK3B.
> See [open questions](open-questions.md).

**Navigation MCU:** STM32H7. The notes suggest a NUCLEO-H7S3L8 with Ethernet, about $51.

```
STM32H7 (navigation MCU)
  ├── GNSS receiver       UART + PPS (timing)
  ├── IMU  ICM-42688      SPI  (TDK, preferably on a ready-made breakout board)
  ├── Wheel encoders      timer capture / motor-controller feedback
  ├── UWB modules         SPI/UART (phase 2)
  └── ESKF                prediction at IMU rate (200–400 Hz), corrected at lower rates
```

**ESKF (error-state Kalman filter):** this is the INS software. It predicts the rover's position and heading from the IMU,
then corrects the estimate with:

- GNSS position and velocity at 1–10 Hz,
- wheel odometry, plus the constraint that the wheels don't slip sideways,
- later, UWB ranges.

## Phase 2: "smart UWB solution"

The rover doesn't need to navigate *anywhere*, only inside one garden. That means we can build a **small local
Ultra-Wideband (UWB) positioning system** with a few cheap fixed anchors around the property.
Adding UWB ranges to the GNSS + IMU + ESKF system would make the position precise and robust where GNSS is weak.
Then the rover can drive quickly and confidently around the property.

## Later: self-contained navigation module (big idea)

This idea is based on the underwater navigation work done at the notes author's company. It is too big for the start.

| Part | Example / cost |
|---|---|
| 1–2 cheap GNSS receivers (no RTK), about 1 m rough position | [GY-NEO6MV2 2-pack, ~82 DKK](https://www.amazon.de/dp/B0DX1V4WS1) |
| MEMS IMU | [WT901B, ~329 DKK](https://www.amazon.de/dp/B07TD7N2DP) |
| 4-beam Doppler radar for speed over ground | TI [IWRL6844EVM](https://www.ti.com/tool/IWRL6844EVM) (dev kit > 1000 DKK). Chip [IWR6843ARQGALPR](https://www.digikey.dk/da/products/detail/texas-instruments/IWR6843ARQGALPR/15857294), about 250 DKK. The older 3-channel [IWR6843AOPEVM](https://www.digikey.dk/da/products/detail/texas-instruments/IWR6843AOPEVM/12165115) is enough to develop the concept |
| 4 × motor feedback | From the FOC controllers |
| ARM MCU running Zephyr OS | e.g. STM32 |
| INS sensor-fusion software | Not trivial; a colleague may help with the maths |

There could be money in this, but it is a hard, large project.

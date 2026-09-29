# Open Questions and Decisions

These are inconsistencies found while tidying the original notes, and decisions the system architecture still needs.
When one is decided, write the answer down here and update the related docs.

## Inconsistencies in the original notes

| # | Topic | Issue | Suggested resolution |
|---|---|---|---|
| 1 | GNSS module | The notes say "U-Blox F9P" and "ZED-F9P via UART", but link the **simpleRTK3B Budget**. Its datasheet says it uses the **Unicore UM980**, not an F9P. The F9P board is the **simpleRTK2B**. Both datasheets are in `sources/datasheets/`. | Pick one. The UM980 has triple-band + Galileo HAS; the F9P has a very large community and ArduSimple guides. |
| 2 | Navigation MCU | The notes propose the **NUCLEO-H7S3L8**, but the datasheet in the repo is for the **NUCLEO-F207ZG**. | Confirm the H7 (FPU, speed, Ethernet for the ESKF) and add its datasheet, or explain why the F207 was chosen. |
| 3 | Radar channel count | "8 virtual channels from 3 TX × 4 RX". 3 × 4 normally gives 12 virtual channels. | Check against the IWR6843LEVM user guide. |
| 4 | Servo part number | "Feetech STS321" is probably the **STS3215**. | Confirm the model and its supply voltage. |
| 5 | PCB material | "FP4" is almost certainly **FR4**. | Fixed in the tidied docs. |
| 6 | HAS accuracy | The notes say about 40 cm; the UM980 datasheet says decimetre level and warns that HAS is still in testing. | Measure it in the actual garden. |

## Technical risks to check

| # | Topic | Question |
|---|---|---|
| 7 | ESC voltage | Hoverboard hub motors are normally 36 V (10S). The **B-G431B-ESC1 is rated at about 25 V max** (check the datasheet). Run a 24 V battery at lower top speed, or choose a higher-voltage FOC controller? |
| 8 | ESC current | Is the ESC1's current rating enough for 250–350 W per wheel when pushing a trimmer? |
| 9 | ESC interface | 4 ESCs over UART needs 4 UARTs on the MCU. Would CAN be cleaner, if the ESC1 can use it? |
| 10 | Tyres | Hoverboard wheels have solid, smooth tyres. Can we get air-filled off-road tyres in 10"? |

## Architecture decisions still open

| # | Decision | Options |
|---|---|---|
| 11 | Companion computer | Raspberry Pi 5 (+ AI accelerator) vs. Jetson Orin Nano |
| 12 | Software framework | **Decided (for now):** no ROS 2 at the start; plain Python on the companion. Reconsider in phase 3 |
| 13 | Companion ↔ MCU link | Ethernet/UDP vs. UART |
| 14 | One MCU or two | One STM32H7 for navigation + vehicle control, or separate boards |
| 15 | Positioning corrections | Galileo HAS only vs. own RTK base station vs. NTRIP service |
| 16 | Spray system | Liquid, pump, number of nozzles, fixed vs. aimed nozzle |
| 17 | Power | Battery voltage/chemistry/capacity, charging/docking |
| 18 | Camera | Model, mounting position/angle, lighting (shade under trees) |

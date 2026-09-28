# Component List (candidates)

These are the parts the design documents currently point to. **Nothing has been bought yet.** Prices are the rough numbers
from the design notes. Update the status column as parts are ordered.

| Subsystem | Part | Qty | Approx. price | Interface | Status | Notes |
|---|---|---|---|---|---|---|
| Drive | 10" hoverboard hub motor (air-filled off-road tyre) | 4 | – | 3-phase + Hall | Candidate | 100 W (rover only) to 250–350 W (pushing a tool) |
| Drive | ST B-G431B-ESC1 FOC controller | 4 | – | UART | Candidate | SimpleFOC firmware. Check the voltage ([open questions](../../documentation/design/open-questions.md) #7) |
| Steering | Feetech STS3215 serial bus servo | 4 | ~€20 | RS485 | Candidate | Part number to confirm (#4) |
| Navigation | STM32 NUCLEO-H7S3L8 | 1 | ~$51 | – | Candidate | Ethernet. MCU choice to confirm (#2) |
| Navigation | ArduSimple simpleRTK3B Budget (UM980) **or** simpleRTK2B (ZED-F9P) | 1 | – | UART + PPS | Candidate | GNSS choice to confirm (#1) |
| Navigation | Multiband GNSS antenna | 1 | – | SMA | Needed | Not included with the ArduSimple boards |
| Navigation | RTK base station (optional) | 1 | ~€250 | Radio | Optional | Only if Galileo HAS is not accurate enough |
| Navigation | TDK ICM-42688 IMU breakout | 1 | – | SPI | Candidate | Prefer a ready-made breakout board |
| Navigation | UWB modules + anchors | TBD | – | SPI/UART | Phase 2 | |
| Obstacle | TI IWR6843LEVM radar | 2 | – | USB-C | Candidate | Front + rear |
| Compute | Companion computer (Raspberry Pi 5 / Jetson) | 1 | – | – | Open | See [system architecture](../../documentation/system-architecture.md) |
| Vision | Camera | 1+ | – | CSI/USB | Open | |
| Spray | Pump, solenoid valve(s), nozzle(s), tank | – | – | GPIO/MOSFET | Open | Not designed yet |
| Power | Battery, DC/DC converters, E-stop | – | – | – | Open | Depends on the motor voltage decision |

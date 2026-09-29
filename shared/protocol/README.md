# MCU ↔ companion protocol

Messages between the STM32H7 (navigation & vehicle MCU) and the Linux companion computer.

**Status: not implemented yet.** Planned design (see the
[system architecture](../../documentation/system-architecture.md), section 5):

- Message definitions live **only here**, as `.proto` files. C code (nanopb) for the MCU and Python code
  for the companion are generated from them, so the two sides cannot drift apart.
- Each frame on the wire: COBS-encoded packet containing message type, sequence number, payload and CRC.
- First messages: `MotionCommand` (companion → MCU, doubles as heartbeat), `Pose` (MCU → companion),
  `SprayCommand`, `Status`/`Fault`.

# Obstacle Avoidance

> Source: [`sources/notes/obstacle-avoidance.md`](../sources/notes/obstacle-avoidance.md) (original notes, Danish).
> Status: **concept**.

## Existing solutions

- **DIY / maker:** mostly single-channel ultrasound or single-channel radar. These only say "something is there, at
  this distance" across a very wide 80–120° cone, with no detail about where. **Not good enough for us.**
- **Commercial robot mowers without a boundary wire:** typically lidar + GNSS.
- **Better option:** **mmWave radar with a phased antenna array**, which can tell where obstacles are. This has not really reached
  the maker market yet, so building it would be a big deal.

## Phase 1: TI IWR6843 development kit

- Use the TI **[IWR6843LEVM](https://www.ti.com/tool/IWR6843LEVM)** out of the box over USB
  ([user guide](https://www.ti.com/lit/ug/swru585/swru585.pdf),
  [DigiKey](https://www.digikey.dk/da/products/detail/texas-instruments/IWR6843LEVM/18159132)).
- 60–64 GHz, **3 transmit × 4 receive** antennas, which the chip combines into a small array of virtual channels.
  The notes say 8; 3 × 4 would normally give 12. See [open questions](open-questions.md).
- Big advantage: TI's reference antenna design uses cheap standard **FR4** PCB material, so we can build our own boards later.
  Other high-end designs need special PCB materials.
- Drawback: the **vertical field of view is 80°**. Ideally it would be 15–20°, which is closer to a flat 2D scan.

## Phase 2: next-generation TI radar

- Move to TI's next generation, which is on its way: **16 virtual channels** and better resolution.
- We hope TI releases a version with a narrower vertical FOV. Otherwise we design our own PCB with a different
  antenna layout, if TI's tools let us model it.

## How it goes on the rover

- **2 radar units**, one at the **front** and one at the **rear**, in small enclosures mounted high up.
- Each unit must be calibrated to how it is mounted and to its FOV. In software, we mask out most of the 80° vertical FOV.
- Each unit is powered and sends data over **USB-C**, so the onboard computer needs 2 free USB-C ports.
- The radar data needs a capable companion computer (Raspberry Pi, Jetson Nano or similar).
  See [system architecture](../system-architecture.md).

# Rig Logger: Software for the Measurement Rig

The logger records the [measurement rig](measurement-rig.md) in the same log format as the simulator
(`navigation/landdvl/logio.py`), so `python -m landdvl.evaluate` works on real sessions without changes.

**Status (November 2026):** written and tested **without hardware**. A loopback test (below) turns
simulated data into the exact bytes the sensors send and checks that the logged result gives the same
filter result. The Pico firmware has **not been compiled or run** yet, and the radar axes and Doppler sign
must be checked on the rig.

## Parts

| File | What it does |
|---|---|
| `navigation/firmware/pico_logger/pico_logger.ino` | Pico 2 firmware: IMU over SPI at 200 Hz, wheel encoder (quadrature, 50 Hz), GNSS PPS pulse. Streams text lines over USB |
| `navigation/landdvl/rig/core.py` | Turns raw messages into the log: clock alignment, encoder ticks → speed, lat/lon → local metres, radar ground-point filter |
| `navigation/landdvl/rig/nmea.py` | GNSS: NMEA GGA (position, fix type) and GST (accuracy), checksum, local east/north frame |
| `navigation/landdvl/rig/ti_radar.py` | TI mmWave out-of-box demo packets (point cloud with Doppler) and the radar mounting geometry |
| `navigation/landdvl/rig/logger.py` | Command line program: opens the serial ports and logs until Ctrl+C |
| `navigation/landdvl/rig/loopback.py` | Simulator → raw sensor bytes → logger. Tests everything without hardware |
| `navigation/rig.example.json` | Example rig configuration (calibration values go here) |

## Running it

```bash
cd navigation
source .venv/bin/activate
pip install -e ".[rig,plot,dev]"
python -m landdvl.rig.logger --config rig.json --out logs/2026-11-15_s1 \
    --pico /dev/cu.usbmodem101 --gnss /dev/cu.usbserial-110 \
    --radar-cli /dev/cu.usbserial-0001 --radar-data /dev/cu.usbserial-0002 \
    --radar-cfg radar.cfg --notes "dry, newly mowed, 12 °C"
```

- Every port is optional, so each sensor can be tested on its own first.
- On a Mac, list the ports with `ls /dev/cu.*`. The TI board shows up as two ports: the lower number is
  usually the CLI port, the higher the data port.
- `radar.cfg` is made with TI's mmWave Demo Visualizer (or one of TI's example .cfg files). Set the frame
  period to 50 ms (20 Hz) and put the same value in `frame_period_s` in `rig.json`.
- Every few seconds the logger prints how many rows each sensor has written. If a number stops growing, that
  sensor has stopped.

Test it all without hardware:

```bash
python -m landdvl.sim --out logs/sim01
python -m landdvl.rig.loopback logs/sim01 logs/sim01_loopback
```

## What gets written

The normal log files (`imu.csv`, `wheel.csv`, `gnss.csv`, `radar.csv`, `meta.json`) plus:

| File | Contents |
|---|---|
| `radar.csv` | Point-cloud format: `t, beam, radial_velocity, ux, uy, uz`. One row per ground detection, direction in the trolley frame |
| `imu_raw.csv` | All six IMU axes, for the later 3D filter |
| `pps.csv` | Times of the GNSS PPS pulses, for checking the GNSS delay later |
| `gnss_raw.nmea` | Every GNSS sentence with its time, so positions can be reprocessed |
| `events.csv` | Status messages from the Pico |
| `meta.json` | Configuration, GNSS origin (lat/lon of the first RTK position) and row counts |

The files are written as the session goes, so a crash or a flat battery keeps the data recorded so far.

## Timestamps

All sensors end up on one clock: seconds since the first message, on the laptop's clock.

- **Pico (IMU, encoder, PPS):** the Pico stamps each sample with its own microsecond clock. The logger maps
  that clock onto the laptop clock. USB only ever adds delay, so the message with the smallest delay in the
  last 30 s gives the best mapping. This removes the USB jitter (the random variation in delivery time).
- **Radar:** same trick, using the frame number × frame period as the radar's own clock.
- **GNSS:** same trick, using the UTC time in each GGA sentence.
- **Not handled yet:** each device's **constant** delay (e.g. GNSS positions arriving ~30 ms late). It can be
  estimated later from `pps.csv` or by shifting a sensor's time until the filter fits best.

## Checks before the first session

### Radar sign check (must do)
TI's documentation gives the point format (x, y, z, Doppler) but not the axis directions or the Doppler sign.
The code assumes **x right, y along the boresight, z up** and **positive Doppler = moving away**. Check it:

1. Mount the radar as planned (backwards, ~45° down). Log 30 s with only `--radar-data`.
2. Stand still for 10 s, then push the trolley **forward** at walking speed.
3. Ground points behind a forward-moving trolley move **away** from the radar, so `radial_velocity` in
   `radar.csv` must be **positive** while pushing forward.
4. If it is negative, set `"doppler_sign": -1.0` in `rig.json`.
5. Check that `uz` is negative (points below the radar). If the axes are different, the ground filter drops
   almost all points. Then the row count for radar stays near zero.

### IMU check
- The Pico prints `WHO_AM_I=0x47` at start. Another value means a wiring or SPI problem.
- Trolley standing still and level: `az` in `imu_raw.csv` ≈ +9.8 m/s². Turning left: `gz` positive. If
  not, change `imu_axes` in `rig.json` (e.g. `["-y", "x", "z"]`).

### Encoder check
- Push forward 1 m: the speed must be positive. Otherwise set `"wheel_sign": -1.0`.
- `metres_per_tick` comes from the 20 m calibration push in the build guide.

## What the loopback test showed

The loopback turns a simulated log into Pico lines, NMEA sentences and TI radar packets, with 2 ms USB delay
plus random jitter, 30 ms GNSS delay and 10 ms radar delay. Then it logs them. Results (simulation, seed 1,
whole run with real GNSS, error against the simulator's truth):

| Log | IMU + wheel, max | IMU + wheel + radar, median | IMU + wheel + radar, max |
|---|---|---|---|
| Original simulated log | 2.31 m | 0.023 m | 0.29 m |
| Same data through the rig logger | 2.29 m | 0.020 m | 0.29 m |

So the logger keeps the information the filter needs. Two lessons along the way:

- **The outage test needs many separate windows.** On a "real" log the outage windows must start in long
  stretches of RTK fix. In the simulated garden all 15 windows started within 1 s of each other, so they were
  really one window. Small timestamp changes then moved the result from 0.16 to 0.20 m. **Drive several long
  open-sky lanes per session** (see the measurement procedure), so there are many independent windows.
- An early version of the loopback reordered messages from the same port. That broke the wheel speed. A real
  USB port keeps the order, and the logger relies on it.

## Known limits

- The firmware is untested on hardware. The ICM-42688-P register addresses and codes are from the Linux kernel
  driver ([inv_icm42600.h](https://github.com/torvalds/linux/blob/master/drivers/iio/imu/inv_icm42600/inv_icm42600.h));
  the SPI read flag (0x80) is the usual InvenSense convention and was not checked against a source.
- Radar point filter: only geometry (height, range). No SNR filter yet; TLV type 7 (SNR per point) can be
  turned on with `guiMonitor` and added later.
- GNSS accuracy: GST is used when the receiver sends it; otherwise 2 cm for fix and 30 cm for float.
- The filter is still 2D. On sloping ground the accelerometer sees part of gravity. Start on level ground.

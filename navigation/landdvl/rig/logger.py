"""Record a session on the measurement rig.

    pip install -e ".[rig]"
    python -m landdvl.rig.logger --config rig.json --out logs/2026-11-15_s1 \
        --pico /dev/ttyACM0 --gnss /dev/ttyUSB0 \
        --radar-cli /dev/ttyUSB1 --radar-data /dev/ttyUSB2 --radar-cfg radar.cfg

Stop with Ctrl+C. Every source is optional, so each sensor can be tested on its own. On a Mac the
ports are called /dev/cu.usbmodem... and /dev/cu.usbserial-...
"""

from __future__ import annotations

import argparse
import queue
import threading
import time
from pathlib import Path

from landdvl.rig.core import Rig, RigConfig


def _open(port: str, baud: int):
    import serial  # pyserial, from the "rig" extra

    return serial.Serial(port, baud, timeout=0.2)


def read_lines(port: str, baud: int, source: str, out: queue.Queue, stop: threading.Event):
    with _open(port, baud) as ser:
        while not stop.is_set():
            line = ser.readline()
            if line:
                out.put((time.monotonic(), source, line.decode("ascii", "replace")))


def read_bytes(port: str, baud: int, out: queue.Queue, stop: threading.Event):
    with _open(port, baud) as ser:
        while not stop.is_set():
            data = ser.read(4096)
            if data:
                out.put((time.monotonic(), "radar", data))


def configure_radar(port: str, cfg_file: str | Path) -> None:
    """Send TI's .cfg commands (made with TI's mmWave Demo Visualizer) to the CLI port."""
    with _open(port, 115200) as ser:
        for raw in Path(cfg_file).read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("%"):
                continue
            ser.write((line + "\n").encode("ascii"))
            reply = ser.read_until(b"mmwDemo:/>").decode("ascii", "replace")
            if "Error" in reply:
                raise RuntimeError(f"radar rejected '{line}': {reply.strip()}")


def main() -> None:
    p = argparse.ArgumentParser(description="Record a measurement-rig session.")
    p.add_argument("--out", required=True, help="new log folder")
    p.add_argument("--config", help="rig JSON config (see rig.example.json)")
    p.add_argument("--pico", help="Pico serial port")
    p.add_argument("--gnss", help="GNSS receiver serial port")
    p.add_argument("--gnss-baud", type=int, default=115200)
    p.add_argument("--radar-cli", help="TI radar CLI port (for --radar-cfg)")
    p.add_argument("--radar-data", help="TI radar data port")
    p.add_argument("--radar-cfg", help="TI .cfg file to send before logging")
    p.add_argument("--notes", default="", help="weather, ground, anything unusual")
    args = p.parse_args()

    if Path(args.out).exists():
        raise SystemExit(f"{args.out} exists already; choose a new folder")
    config = RigConfig.from_json(args.config) if args.config else RigConfig()
    if args.notes:
        config.notes = args.notes
    if args.radar_cfg:
        if not args.radar_cli:
            raise SystemExit("--radar-cfg needs --radar-cli")
        configure_radar(args.radar_cli, args.radar_cfg)

    rig = Rig(args.out, config)
    q: queue.Queue = queue.Queue()
    stop = threading.Event()
    threads = []
    if args.pico:
        threads.append(
            threading.Thread(target=read_lines, args=(args.pico, 921600, "pico", q, stop))
        )
    if args.gnss:
        threads.append(
            threading.Thread(target=read_lines, args=(args.gnss, args.gnss_baud, "gnss", q, stop))
        )
    if args.radar_data:
        threads.append(threading.Thread(target=read_bytes, args=(args.radar_data, 921600, q, stop)))
    if not threads:
        raise SystemExit("give at least one of --pico, --gnss, --radar-data")
    for t in threads:
        t.daemon = True
        t.start()

    print(
        f"Logging to {args.out}. Stand still for {config.static_start_s:.0f} s first. Ctrl+C stops."
    )
    last_status = time.monotonic()
    try:
        while True:
            try:
                host_t, source, payload = q.get(timeout=0.5)
            except queue.Empty:
                continue
            if source == "pico":
                rig.on_pico_line(host_t, payload)
            elif source == "gnss":
                rig.on_gnss_line(host_t, payload)
            else:
                rig.on_radar_bytes(host_t, payload)
            if host_t - last_status > 5.0:
                rig.writer.flush()
                c = rig.writer.counts
                print(
                    f"t={host_t - (rig.t0 or host_t):7.1f} s  imu {c['imu']}  wheel {c['wheel']}  "
                    f"gnss {c['gnss']}  radar points {c['radar']}"
                )
                last_status = host_t
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        print(rig.close())


if __name__ == "__main__":
    main()

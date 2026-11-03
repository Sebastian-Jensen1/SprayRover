"""Sensitivity analysis: which radar (and IMU) is good enough?

Changes one sensor property at a time around the default ``SensorModel``, simulates the garden
for several seeds, runs the artificial-outage test, and reports the median position error after
30 s without GNSS for each sensor set.

    python -m landdvl.sweep --out results/sweep            # full sweep, ~10 min on 4 cores
    python -m landdvl.sweep --out results/sweep --quick    # 1 seed, fewer windows, ~3 min
"""

from __future__ import annotations

import argparse
import csv
import tempfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

from landdvl.ekf import FilterConfig
from landdvl.evaluate import artificial_outages
from landdvl.logio import read_log, write_log
from landdvl.sim import SensorModel, simulate
from landdvl.world import Garden

DEFAULT = SensorModel()

# Each dimension: label -> list of (value label, numeric x for plotting, SensorModel changes)
DIMENSIONS: dict[str, list[tuple[str, float, dict]]] = {
    "Radar noise per beam (m/s)": [
        (f"{n:g}", n, dict(radar_noise=n, radar_noise_rel=n))
        for n in (0.005, 0.01, 0.02, 0.05, 0.1)
    ],
    "Number of radar beams": [
        ("1 (forward)", 1, dict(radar_azimuths_deg=(0.0,))),
        ("2 (front L/R)", 2, dict(radar_azimuths_deg=(45.0, 315.0))),
        ("3", 3, dict(radar_azimuths_deg=(0.0, 120.0, 240.0))),
        ("4 (default)", 4, dict(radar_azimuths_deg=(45.0, 135.0, 225.0, 315.0))),
        ("8", 8, dict(radar_azimuths_deg=tuple(float(a) for a in range(0, 360, 45)))),
    ],
    "Beam tilt from straight down (deg)": [
        (f"{t:g}", t, dict(radar_tilt_deg=t)) for t in (10.0, 20.0, 30.0, 45.0, 60.0)
    ],
    "Radar update rate (Hz)": [(f"{r:g}", r, dict(radar_rate=r)) for r in (5.0, 10.0, 20.0, 40.0)],
    "IMU grade": [
        (
            "cheap (3x noise)",
            0,
            dict(gyro_noise=0.006, gyro_bias_walk=0.0006, acc_noise=0.15, acc_bias_walk=0.006),
        ),
        ("default", 1, {}),
        (
            "good (1/4 noise)",
            2,
            dict(gyro_noise=0.0005, gyro_bias_walk=0.00005, acc_noise=0.0125, acc_bias_walk=0.0005),
        ),
    ],
}

SETS = ("IMU + wheel", "IMU + wheel + radar", "IMU + radar")


def filter_for(model: SensorModel) -> FilterConfig:
    """A filter tuned to the sensors it is fed, as you would tune it for real hardware."""
    return FilterConfig(
        gyro_noise=model.gyro_noise,
        acc_noise=model.acc_noise,
        gyro_bias_walk=model.gyro_bias_walk,
        acc_bias_walk=model.acc_bias_walk,
        radar_sigma=max(0.01, 2 * model.radar_noise),
    )


def run_case(case: tuple[str, str, float, dict, int, int]) -> list[dict]:
    dimension, label, x, changes, seed, windows = case
    model = replace(DEFAULT, **changes)
    tables, meta = simulate(Garden(), model, seed=seed)
    with tempfile.TemporaryDirectory() as tmp:
        log = read_log(write_log(Path(tmp) / "log", tables, meta))
    _, results, _ = artificial_outages(log, duration=60.0, count=windows, base=filter_for(model))
    rows = []
    for r in results:
        rows.append(
            {
                "dimension": dimension,
                "value": label,
                "x": x,
                "seed": seed,
                "sensor_set": r.sensor_set,
                "median_10s": float(np.median(r.errors[:, 10])),
                "median_30s": float(np.median(r.errors[:, 30])),
                "median_60s": float(np.median(r.errors[:, 60])),
                "p90_30s": float(np.percentile(r.errors[:, 30], 90)),
            }
        )
    return rows


def aggregate(rows: list[dict]) -> dict[tuple[str, str, str], dict]:
    """Mean over seeds of the median 30 s error, plus min/max over seeds."""
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for r in rows:
        groups.setdefault((r["dimension"], r["value"], r["sensor_set"]), []).append(r)
    out = {}
    for key, items in groups.items():
        e30 = np.array([i["median_30s"] for i in items])
        out[key] = {
            "x": items[0]["x"],
            "mean": float(e30.mean()),
            "min": e30.min(),
            "max": e30.max(),
        }
    return out


def write_outputs(rows: list[dict], out: Path, seeds: list[int]) -> str:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "sweep.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    agg = aggregate(rows)
    lines = [
        "# Sensitivity analysis",
        "",
        f"Median position error after **30 s without GNSS**, mean over seeds {seeds}. One property "
        "changes at a time; everything else is the default `SensorModel`. Lower is better. "
        "Ratio = (IMU + wheel + radar) / (IMU + wheel).",
        "",
    ]
    for dim, values in DIMENSIONS.items():
        lines += [
            f"## {dim}",
            "",
            "| Value | " + " | ".join(SETS) + " | Ratio |",
            "|---|---|---|---|---|",
        ]
        for label, _, _ in values:
            cells = [agg[(dim, label, s)]["mean"] for s in SETS]
            ratio = cells[1] / cells[0] if cells[0] > 0 else float("nan")
            lines.append(
                f"| {label} | " + " | ".join(f"{c:.2f} m" for c in cells) + f" | {ratio:.2f} |"
            )
        lines.append("")
    text = "\n".join(lines)
    (out / "sweep.md").write_text(text, encoding="utf-8")
    return text


def plot(rows: list[dict], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    agg = aggregate(rows)
    colors = {"IMU + wheel": "#d1495b", "IMU + wheel + radar": "#2e86ab", "IMU + radar": "#66a182"}
    dims = list(DIMENSIONS)
    fig, axes = plt.subplots(1, len(dims), figsize=(4.2 * len(dims), 4.2), sharey=True)
    for ax, dim in zip(axes, dims, strict=True):
        values = DIMENSIONS[dim]
        xs = np.arange(len(values))
        for s in SETS:
            mean = [agg[(dim, v[0], s)]["mean"] for v in values]
            lo = [agg[(dim, v[0], s)]["min"] for v in values]
            hi = [agg[(dim, v[0], s)]["max"] for v in values]
            ax.plot(xs, mean, "o-", color=colors[s], label=s)
            ax.fill_between(xs, lo, hi, color=colors[s], alpha=0.12)
        ax.set_xticks(xs)
        ax.set_xticklabels([v[0] for v in values], rotation=30, ha="right", fontsize=8)
        ax.set_title(dim, fontsize=10)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("median error after 30 s without GNSS [m]")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "sweep.png", dpi=110)
    plt.close(fig)


def cases(seeds: list[int], windows: int) -> list[tuple]:
    return [
        (dim, label, x, changes, seed, windows)
        for dim, values in DIMENSIONS.items()
        for label, x, changes in values
        for seed in seeds
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Radar/IMU sensitivity analysis.")
    parser.add_argument("--out", default="results/sweep")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--windows", type=int, default=15)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--quick", action="store_true", help="1 seed and 8 windows")
    args = parser.parse_args()
    seeds = [1] if args.quick else args.seeds
    windows = 8 if args.quick else args.windows

    todo = cases(seeds, windows)
    print(f"Running {len(todo)} simulations on {args.workers} workers ...")
    rows: list[dict] = []
    with ProcessPoolExecutor(args.workers) as pool:
        for i, result in enumerate(pool.map(run_case, todo), start=1):
            rows.extend(result)
            print(f"  {i}/{len(todo)} {todo[i - 1][0]}: {todo[i - 1][1]} (seed {todo[i - 1][4]})")
    out = Path(args.out)
    print(write_outputs(rows, out, seeds))
    plot(rows, out)
    print(f"Plot: {out / 'sweep.png'}")


if __name__ == "__main__":
    main()

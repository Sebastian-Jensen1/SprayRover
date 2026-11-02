"""Answer the F0 question: does radar at least halve the error growth when GNSS disappears?

Method ("artificial outages"):
1. Run the filter with everything on and store a snapshot of its state every second.
2. Pick many start times where the rig is moving under open sky (RTK fix), so the start is good.
3. From each start, run again with GNSS switched off for 60 s, once per sensor set.
4. Compare the estimated position with the truth every second and report median errors.

On simulated logs the truth comes from ``truth.csv``. On real logs, pick outage windows in open
areas: there the RTK fix itself is the truth (centimetre accuracy).

    python -m landdvl.evaluate logs/sim01 --out results/sim01
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from landdvl.ekf import FilterConfig
from landdvl.logio import Log, read_log
from landdvl.runner import Replay, resume, variant
from landdvl.world import Garden, Tree

SENSOR_SETS = {
    "IMU + wheel": dict(use_wheel=True, use_radar=False),
    "IMU + wheel + radar": dict(use_wheel=True, use_radar=True),
    "IMU + radar": dict(use_wheel=False, use_radar=True),
}
CHECKPOINTS = (10, 30, 60)


@dataclass
class OutageResult:
    sensor_set: str
    errors: np.ndarray  # shape (n_windows, max_duration + 1): error at each second


@dataclass
class Reference:
    """Where the rig really was. Simulated logs: truth.csv. Real logs: the RTK-fix samples."""

    t: np.ndarray
    x: np.ndarray
    y: np.ndarray
    fix: np.ndarray  # RTK fix available (open sky) at this sample
    speed: np.ndarray
    everywhere: bool  # True if the reference is valid everywhere (simulation)


def reference_track(log: Log) -> Reference:
    if log.truth is not None:
        tr = log.truth
        garden = garden_from_meta(log)
        fix = np.array([garden.gnss_quality(x, y) == "fix" for x, y in tr[:, 1:3]])
        speed = np.hypot(tr[:, 4], tr[:, 5])
        return Reference(tr[:, 0], tr[:, 1], tr[:, 2], fix, speed, everywhere=True)
    g = log.gnss_xy
    is_fix = np.array([q == "fix" for q in log.gnss_quality])
    t = g[is_fix, 0]
    speed = np.interp(t, log.wheel[:, 0], np.abs(log.wheel[:, 1]))
    return Reference(t, g[is_fix, 1], g[is_fix, 2], np.ones(len(t), bool), speed, everywhere=False)


def reference_position(ref: Reference, t: np.ndarray) -> np.ndarray:
    return np.column_stack([np.interp(t, ref.t, ref.x), np.interp(t, ref.t, ref.y)])


def pick_windows(
    log: Log, duration: float, count: int, settled_for: float = 15.0, ref: Reference | None = None
) -> list[float]:
    """Start times while moving under open sky, after at least `settled_for` seconds of RTK fix,
    so the filter has converged before GNSS is switched off. Spread over the whole log.

    On real logs the RTK fix is the only reference, so the whole window must stay in RTK fix
    (drive in the open for these runs); GNSS is only switched off inside the filter."""
    ref = ref or reference_track(log)
    start_ok = float(log.meta.get("static_start_s", 0)) + 20.0
    gap = np.diff(ref.t, prepend=ref.t[0])
    run = np.zeros(len(ref.t))  # seconds of uninterrupted fix up to each sample
    for i in range(1, len(ref.t)):
        run[i] = run[i - 1] + gap[i] if ref.fix[i] and gap[i] < 1.0 else 0.0
    end_ok = ref.t[-1] - (35 if ref.everywhere else 0)

    def covered(t0: float) -> bool:
        if ref.everywhere:
            return True
        need = t0 + np.arange(0, int(duration) + 1)
        nearest = np.abs(ref.t[np.clip(np.searchsorted(ref.t, need), 0, len(ref.t) - 1)] - need)
        return bool(np.all(nearest < 0.5))

    candidates = [
        float(t)
        for t, s, r in zip(ref.t, ref.speed, run, strict=True)
        if t > start_ok and t + duration < end_ok and s > 0.2 and r >= settled_for and covered(t)
    ]
    if not candidates:
        return []
    picks = np.linspace(0, len(candidates) - 1, min(count, len(candidates))).astype(int)
    return [candidates[i] for i in picks]


def garden_from_meta(log: Log) -> Garden:
    g = log.meta["garden"]
    return Garden(
        width=g["width"],
        height=g["height"],
        trees=tuple(Tree(t["x"], t["y"], t["canopy_radius"]) for t in g["trees"]),
    )


def artificial_outages(
    log: Log, duration: float = 60.0, count: int = 25, base: FilterConfig | None = None
) -> tuple[list[float], list[OutageResult], np.ndarray]:
    base = base or FilterConfig()
    replay = Replay(log)
    full = replay.initial_filter(base)
    estimates, snaps = replay.run(full, 0.0, float("inf"), snapshot_every=1.0)
    snap_times = np.array([s.t for s in snaps])

    ref = reference_track(log)
    starts = pick_windows(log, duration, count, ref=ref)
    results = []
    seconds = np.arange(0, int(duration) + 1)
    for name, changes in SENSOR_SETS.items():
        cfg = variant(base, **changes)
        errs = []
        for t0 in starts:
            snap = snaps[int(np.searchsorted(snap_times, t0))]
            ekf = resume(snap, cfg)
            est, _ = replay.run(
                ekf, snap.t, snap.t + duration + 0.5, gnss_off=(snap.t, snap.t + duration + 1)
            )
            t_query = snap.t + seconds
            ex = np.interp(t_query, est[:, 0], est[:, 1])
            ey = np.interp(t_query, est[:, 0], est[:, 2])
            truth = reference_position(ref, t_query)
            errs.append(np.hypot(ex - truth[:, 0], ey - truth[:, 1]))
        results.append(OutageResult(name, np.array(errs)))
    return starts, results, estimates


def full_run(log: Log, sensor_set: str, base: FilterConfig | None = None) -> np.ndarray:
    """Whole log with all real GNSS (including the bad samples under trees)."""
    base = base or FilterConfig()
    replay = Replay(log)
    ekf = replay.initial_filter(variant(base, **SENSOR_SETS[sensor_set]))
    est, _ = replay.run(ekf, 0.0, float("inf"))
    return est


def summary_table(results: list[OutageResult]) -> list[dict]:
    rows = []
    for r in results:
        row = {"sensor_set": r.sensor_set}
        for c in CHECKPOINTS:
            if c < r.errors.shape[1]:
                row[f"median_{c}s"] = float(np.median(r.errors[:, c]))
                row[f"p90_{c}s"] = float(np.percentile(r.errors[:, c], 90))
        rows.append(row)
    return rows


def verdict(rows: list[dict], at: int = 30) -> tuple[float, bool]:
    by = {r["sensor_set"]: r for r in rows}
    ratio = by["IMU + wheel + radar"][f"median_{at}s"] / by["IMU + wheel"][f"median_{at}s"]
    return ratio, ratio <= 0.5


def plot(log: Log, results: list[OutageResult], runs: dict[str, np.ndarray], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"IMU + wheel": "#d1495b", "IMU + wheel + radar": "#2e86ab", "IMU + radar": "#66a182"}

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for r in results:
        t = np.arange(r.errors.shape[1])
        med = np.median(r.errors, axis=0)
        ax.plot(t, med, color=colors[r.sensor_set], lw=2, label=r.sensor_set)
        ax.fill_between(
            t, np.percentile(r.errors, 25, axis=0), np.percentile(r.errors, 75, axis=0),
            color=colors[r.sensor_set], alpha=0.15,
        )  # fmt: skip
    ax.set_xlabel("seconds without GNSS")
    ax.set_ylabel("position error [m] (median, 25–75 %)")
    ax.set_title("Error growth during artificial GNSS outages")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "error_growth.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 6.5))
    garden = garden_from_meta(log) if "garden" in log.meta else None
    if garden is not None:
        for tree in garden.trees:
            ax.add_patch(
                plt.Circle((tree.x, tree.y), tree.canopy_radius, color="#7fb069", alpha=0.35)
            )
        ax.axhspan(-1, 0, color="#999999", alpha=0.5)
        ax.text(0.5, -0.7, "house wall", fontsize=8)
    q_colors = {"fix": "#2a9d8f", "float": "#e9c46a"}
    g = log.gnss_xy
    for q, c in q_colors.items():
        mask = np.array([qq == q for qq in log.gnss_quality])
        if mask.any():
            ax.scatter(g[mask, 1], g[mask, 2], s=3, color=c, label=f"GNSS {q}")
    if log.truth is not None:
        ax.plot(log.truth[:, 1], log.truth[:, 2], color="black", lw=1, label="truth")
    for name, est in runs.items():
        ax.plot(
            est[:, 1], est[:, 2], color=colors[name], lw=1, alpha=0.9, label=f"estimate: {name}"
        )
    ax.set_aspect("equal")
    if garden is not None:
        ax.set_xlim(-1, garden.width + 1)
        ax.set_ylim(-1, garden.height + 1)
    ax.set_title("Whole run with all GNSS samples")
    ax.legend(loc="upper left", fontsize=7, markerscale=3)
    fig.tight_layout()
    fig.savefig(out / "garden_run.png", dpi=120)
    plt.close(fig)


def write_report(rows, ratio, ok, n_windows, full_errors, out: Path) -> str:
    lines = [
        "# Artificial GNSS outage test",
        "",
        f"Windows: {n_windows} starts under open sky, GNSS switched off for up to 60 s.",
        "",
        "| Sensor set | " + " | ".join(f"median {c} s" for c in CHECKPOINTS) + " | p90 30 s |",
        "|---|" + "---|" * (len(CHECKPOINTS) + 1),
    ]
    for r in rows:
        cells = [f"{r[f'median_{c}s']:.2f} m" for c in CHECKPOINTS]
        lines.append(f"| {r['sensor_set']} | " + " | ".join(cells) + f" | {r['p90_30s']:.2f} m |")
    lines += [
        "",
        f"**Radar ratio at 30 s:** {ratio:.2f} (error with radar / without). "
        + ("**PASS:** radar at least halves the error." if ok else "**FAIL:** less than half."),
    ]
    if full_errors:
        lines += [
            "",
            "## Whole run with real GNSS (incl. multipath and canopy gaps)",
            "",
            "| Sensor set | median error | max error |",
            "|---|---|---|",
        ]
        for name, (med, mx) in full_errors.items():
            lines.append(f"| {name} | {med:.2f} m | {mx:.2f} m |")
    text = "\n".join(lines) + "\n"
    (out / "report.md").write_text(text, encoding="utf-8")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Artificial GNSS outage test on a log.")
    parser.add_argument("log", help="log folder (from the simulator or the rig)")
    parser.add_argument("--out", default=None, help="results folder (default: results/<log name>)")
    parser.add_argument("--windows", type=int, default=25)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    log = read_log(args.log)
    out = Path(args.out or Path("results") / Path(args.log).name)
    out.mkdir(parents=True, exist_ok=True)

    starts, results, _ = artificial_outages(log, count=args.windows)
    if not starts:
        raise SystemExit(
            "No suitable outage windows found. Real logs need stretches of 60+ s of driving "
            "with uninterrupted RTK fix (open sky)."
        )
    rows = summary_table(results)
    ratio, ok = verdict(rows)

    runs, full_errors = {}, {}
    ref = reference_track(log)
    for name in ("IMU + wheel", "IMU + wheel + radar"):
        est = full_run(log, name)
        runs[name] = est
        if ref.everywhere:  # only the simulator knows the truth under the trees
            truth = reference_position(ref, est[:, 0])
            err = np.hypot(est[:, 1] - truth[:, 0], est[:, 2] - truth[:, 1])
            full_errors[name] = (float(np.median(err)), float(err.max()))

    print(write_report(rows, ratio, ok, len(starts), full_errors, out))
    if not args.no_plots:
        plot(log, results, runs, out)
        print(f"Plots: {out / 'error_growth.png'}, {out / 'garden_run.png'}")


if __name__ == "__main__":
    main()

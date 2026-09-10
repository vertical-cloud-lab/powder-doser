"""Flatten the issue #116 battery runs into tidy CSVs for manuscript figures.

The raw per-run artifacts (``data/battery/<timestamp>_<powder>/run_*.json``) live
on the ``claude/issue-116-*`` branches and total ~37 MB.  This script distils
them into four small CSVs that are committed alongside the figure script, so the
candidate figures rebuild without the raw tree:

    runs.csv     one row per battery run (metadata + QC verdict)
    feed.csv     block C/D/E per-condition means (feed factor, tap quantum)
    trials.csv   every individual measured trial (block A-E)
    doses.csv    block G closed-loop dose attempts
    polls.csv    block D streaming balance polls (mass-vs-time traces)

Usage:
    python build_dataset.py /path/to/data/battery
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

# Powders whose composition matters to the alloy-discovery thrust, as opposed to
# the food-safe surrogates bought to exercise the flowability range cheaply.
RESEARCH_POWDERS = {
    "alsi10mg",
    "silicon-110-200",
    "silicon-325",
    "sodium-sulfate",
    "barium-chloride",
    "fumed-silica",
}

DISPLAY = {
    "alsi10mg": "AlSi10Mg",
    "silicon-110-200": "Si (110/200 mesh)",
    "silicon-325": "Si (-325 mesh)",
    "sodium-sulfate": "Sodium sulfate",
    "barium-chloride": "Barium chloride",
    "fumed-silica": "Fumed silica",
    "salt": "NaCl (control)",
    "calcium-lactate": "Calcium lactate",
    "sodium-alginate": "Sodium alginate",
    "xanthan-gum": "Xanthan gum",
    "carboxymethyl-cellulose": "CMC",
    "white-rice-flour": "White rice flour",
    "brown-rice-flour": "Brown rice flour",
}


def consistency_ratio(run: dict) -> float | None:
    """Block E re-feed / block C rotation, both mg/rev at tilt 45 deg.

    The two blocks measure the same quantity minutes apart.  Every
    well-behaved run in the #116 dataset lands in 0.74-1.12; a run outside
    that band measured two different things, so its block C is not a
    steady-state feed factor.  Gate reproduced from
    ``scripts/plot_powder_repeats.py`` on the run branches so the figures
    here pool exactly the runs the run log pools.
    """
    summary = run.get("host_summary") or []
    c = [r for r in summary if r["block"] == "C" and r["tilt_deg"] == 45.0]
    e = [r for r in summary
         if r["block"] == "E" and r["phase"] == "refeed" and r["tilt_deg"] == 45.0]
    if not c or not e or not c[0]["mean_g"]:
        return None
    return e[0]["mean_g"] / c[0]["mean_g"]


def poolable(run: dict) -> bool:
    """Whether this run's feed factor may join between-run statistics."""
    qc = run.get("qc") or {}
    if not qc.get("valid_for_cross_powder_comparison"):
        return False
    reason = (qc.get("reason") or "").lower()
    if "lower bound" in reason or "upper bound" in reason:
        return False
    ratio = consistency_ratio(run)
    return ratio is None or 0.74 <= ratio <= 1.12


def load_runs(root: Path) -> list[dict]:
    runs = []
    for run_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        candidates = list(run_dir.glob("run_*.json"))
        if not candidates:
            continue
        run = json.load(open(candidates[0]))
        run["_dir"] = run_dir.name
        runs.append(run)
    return runs


def write(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {path.name:<12} {len(rows):>5} rows")


def main(raw_root: Path, out_dir: Path) -> None:
    runs = load_runs(raw_root)
    print(f"loaded {len(runs)} runs from {raw_root}")
    out_dir.mkdir(parents=True, exist_ok=True)

    run_rows, feed_rows, trial_rows, dose_rows, poll_rows = [], [], [], [], []

    for run in runs:
        pid = run["powder_id"]
        run_id = run["_dir"]
        qc = run.get("qc") or {}
        params = run.get("parameters") or {}
        env = run.get("environment") or {}
        run_rows.append(
            {
                "run_id": run_id,
                "powder_id": pid,
                "display": DISPLAY.get(pid, pid),
                "powder": run.get("powder", ""),
                "batch": run.get("batch", ""),
                "track": "research" if pid in RESEARCH_POWDERS else "surrogate",
                "started_utc": run.get("started_utc", ""),
                "elapsed_s": run.get("elapsed_s", ""),
                "blocks": params.get("blocks", ""),
                "status": run.get("status", ""),
                "qc_valid": qc.get("valid_for_cross_powder_comparison", ""),
                "qc_verdict": qc.get("verdict", ""),
                "preflight_verdict": qc.get("preflight_verdict", ""),
                "median_sigma_g": env.get("median_sigma_g", ""),
                "shock_events": env.get("shock_events", ""),
                "clean_trial_fraction": env.get("clean_trial_fraction", ""),
                "ce_ratio": consistency_ratio(run) or "",
                "poolable": poolable(run),
                "n_doses": len(run.get("doses") or []),
            }
        )

        for row in run.get("host_summary") or []:
            feed_rows.append(
                {
                    "run_id": run_id,
                    "powder_id": pid,
                    "block": row["block"],
                    "phase": row["phase"],
                    "tilt_deg": row["tilt_deg"],
                    "rpm": row.get("rpm", ""),
                    "n": row["n"],
                    "mean_g": row["mean_g"],
                    "std_g": row.get("std_g", ""),
                    "sem_g": row.get("sem_g", ""),
                    "rsd_pct": row.get("rsd_pct", ""),
                }
            )

        for trial in run.get("trials") or []:
            trial_rows.append({"run_id": run_id, "powder_id": pid, **trial})

        for dose in run.get("doses") or []:
            dose_rows.append({"run_id": run_id, "powder_id": pid, **dose})

        for poll in run.get("polls") or []:
            poll_rows.append({"run_id": run_id, "powder_id": pid, **poll})

    write(out_dir / "runs.csv", list(run_rows[0]), run_rows)
    write(out_dir / "feed.csv", list(feed_rows[0]), feed_rows)
    write(
        out_dir / "trials.csv",
        ["run_id", "powder_id", "block", "tilt_deg", "phase", "trial", "action",
         "rpm", "before_g", "after_g", "delta_g", "flag", "t_ms", "sigma_g",
         "drift_g", "shock_g", "retries", "quality"],
        trial_rows,
    )
    write(
        out_dir / "doses.csv",
        ["run_id", "powder_id", "n", "target_g", "dispensed_g", "error_g",
         "status", "elapsed_s", "auger_rev", "taps", "phase_cycles", "t_ms"],
        dose_rows,
    )
    write(
        out_dir / "polls.csv",
        ["run_id", "powder_id", "block", "tilt_deg", "rpm", "t_ms", "grams", "stable"],
        poll_rows,
    )


if __name__ == "__main__":
    raw = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/battery")
    main(raw, Path(__file__).parent / "data")

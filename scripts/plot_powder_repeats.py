#!/usr/bin/env python3
"""Run-to-run reproducibility of the feed factor, for a powder measured more than once.

Why this exists
---------------
The Edison review of this dataset (``outputs/edison-battery-review/``) made
one structural criticism above all others: every powder had **one** battery
run, and the six revolutions inside a block are sequential observations of a
single fill rather than independent preparations.  Quoting a within-run RSD
as if it were the measurement's reproducibility is pseudoreplication -- it
says nothing about how much of the scatter lives *between* fills, augers,
rooms and days.

    "treat the run, not the revolution, as the experimental unit"

Salt is the first powder with enough repeats to answer that, so this script
plots the block C feed factor of every run of one powder side by side and
reports the between-run spread next to the within-run spread.  The
comparison is the point: if run-to-run RSD is no larger than the
revolution-to-revolution RSD, the six-revolution error bars are not hiding a
larger between-fill term, and the single-run numbers for the other powders
are more defensible than the review feared.  If it is much larger, they are
not, and every powder needs repeats.

Runs whose own QC flags the feed factor as unreliable are drawn but excluded
from the pooled statistics, and said so in the caption -- silently dropping
them would overstate the agreement, and silently keeping them would
manufacture disagreement.

Usage::

    python scripts/plot_powder_repeats.py salt out.png data/battery/*/run_*.json
"""

from __future__ import annotations

import json
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TILTS = (0.0, 45.0, 90.0)


def load_runs(powder_id, paths):
    """Every run of ``powder_id``, oldest first, with its block C means."""
    runs = []
    for path in paths:
        try:
            doc = json.load(open(path))
        except (OSError, ValueError):
            continue
        if doc.get("powder_id") != powder_id:
            continue
        summary = doc.get("host_summary") or []
        by_tilt = {row["tilt_deg"]: row for row in summary
                   if row["block"] == "C" and row["phase"] == "rotation"}
        if not by_tilt:
            continue
        qc = doc.get("qc") or {}
        runs.append({
            "date": (doc.get("started_utc") or "")[:10],
            "verdict": qc.get("verdict") or "",
            "valid": bool(qc.get("valid_for_cross_powder_comparison")),
            "pooled": pooled(doc, qc),
            "means": {t: by_tilt[t]["mean_g"] * 1000.0
                      for t in TILTS if t in by_tilt},
            "rsds": {t: by_tilt[t].get("rsd_pct")
                     for t in TILTS if t in by_tilt},
        })
    runs.sort(key=lambda r: r["date"])
    return runs


def pooled(doc, qc):
    """Whether this run's feed factor may join the between-run statistics.

    A run is excluded when its QC says the number is not a measurement of
    steady-state feed -- either the run is excluded outright, or its own
    notes flag the feed factor as a bound.  Salt 2026-08-06 is the case
    this exists for: blocks C and E disagreed by 2.68x on the same
    quantity, so its block C is recorded as a lower bound.
    """
    if not qc.get("valid_for_cross_powder_comparison"):
        return False
    reason = (qc.get("reason") or "").lower()
    if "lower bound" in reason or "upper bound" in reason:
        return False
    return not consistency_failed(doc)


def consistency_failed(doc, lo=0.74, hi=1.12):
    """Block C and block E measure mg/rev at tilt 45 deg minutes apart.

    Every well-behaved run in this dataset lands in 0.74-1.12.  A run
    outside it measured two different things and its block C is not a
    steady-state feed factor.
    """
    summary = doc.get("host_summary") or []
    c = [r for r in summary if r["block"] == "C" and r["tilt_deg"] == 45.0]
    e = [r for r in summary if r["block"] == "E" and r["phase"] == "refeed"
         and r["tilt_deg"] == 45.0]
    if not c or not e or not c[0]["mean_g"]:
        return False
    return not (lo <= e[0]["mean_g"] / c[0]["mean_g"] <= hi)


def between_run_stats(runs):
    """Mean, sd and RSD across runs at each tilt, over the pooled runs only."""
    out = {}
    for tilt in TILTS:
        vals = [r["means"][tilt] for r in runs
                if r["pooled"] and tilt in r["means"]]
        if len(vals) < 2:
            continue
        mean = st.mean(vals)
        sd = st.stdev(vals)
        out[tilt] = {"n": len(vals), "mean": mean, "sd": sd,
                     "rsd": 100.0 * sd / mean if mean else float("nan")}
    return out


def within_run_median_rsd(runs):
    """Median of the per-run, six-revolution RSD at each tilt."""
    out = {}
    for tilt in TILTS:
        vals = [r["rsds"][tilt] for r in runs
                if r["pooled"] and r["rsds"].get(tilt) is not None]
        if vals:
            out[tilt] = st.median(vals)
    return out


def caption(runs, between, within):
    """State what was pooled and what the comparison shows."""
    pooled_runs = [r for r in runs if r["pooled"]]
    dropped = [r for r in runs if not r["pooled"]]
    bits = ["{} of {} runs pooled".format(len(pooled_runs), len(runs))]
    if dropped:
        bits.append("excluded: " + ", ".join(
            "{} ({})".format(r["date"], r["verdict"] or "flagged")
            for r in dropped))
    verdicts = []
    for tilt in sorted(between):
        b, w = between[tilt]["rsd"], within.get(tilt)
        if w is None:
            continue
        verdicts.append("{:.0f} deg: between {:.0f} % vs within {:.0f} %"
                        .format(tilt, b, w))
    if verdicts:
        bits.append(" | ".join(verdicts))
    return "\n".join(bits)


def headline(between, within):
    """Say which term dominates, rather than asserting one does."""
    pairs = [(between[t]["rsd"], within[t])
             for t in between if within.get(t) is not None]
    if not pairs:
        return "run-to-run spread not yet estimable"
    if all(b <= w for b, w in pairs):
        return ("run-to-run spread is no larger than revolution-to-revolution "
                "spread at any tilt")
    if all(b > w for b, w in pairs):
        return ("run-to-run spread exceeds revolution-to-revolution spread at "
                "every tilt -- single-run error bars understate it")
    return "run-to-run spread exceeds the within-run spread at some tilts"


def plot(powder_id, runs, path):
    between = between_run_stats(runs)
    within = within_run_median_rsd(runs)
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    width = 0.8 / max(len(runs), 1)
    xs = range(len(TILTS))
    for i, run in enumerate(runs):
        offs = [x - 0.4 + width * (i + 0.5) for x in xs]
        vals = [run["means"].get(t, 0.0) for t in TILTS]
        label = "{}{}".format(run["date"],
                              "" if run["pooled"] else "  (not pooled)")
        ax.bar(offs, vals, width * 0.92, label=label,
               alpha=1.0 if run["pooled"] else 0.35,
               hatch=None if run["pooled"] else "//")
        for x, v in zip(offs, vals):
            ax.annotate("{:.0f}".format(v), (x, v), ha="center", va="bottom",
                        fontsize=7, rotation=90, xytext=(0, 2),
                        textcoords="offset points")
    for i, tilt in enumerate(TILTS):
        if tilt not in between:
            continue
        b = between[tilt]
        ax.errorbar([i], [b["mean"]], yerr=[b["sd"]], fmt="_", color="k",
                    capsize=8, markersize=26, elinewidth=1.6, zorder=5)
        ax.annotate("pooled {:.0f} +/- {:.0f} mg\nbetween-run RSD {:.0f} %"
                    .format(b["mean"], b["sd"], b["rsd"]),
                    (i, b["mean"] + b["sd"]), ha="center", va="bottom",
                    fontsize=8, xytext=(0, 16), textcoords="offset points")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["{:.0f} deg".format(t) for t in TILTS])
    ax.set_xlabel("tube tilt (0 deg horizontal, 90 deg vertical)")
    ax.set_ylabel("mass per 360 deg revolution (mg)")
    ax.set_title("{} -- block C feed factor across {} independent runs\n{}"
                 .format(powder_id, len(runs), headline(between, within)))
    ax.legend(fontsize=8, ncol=2)
    ax.margins(y=0.28)
    ax.grid(axis="y", alpha=0.3)
    fig.text(0.01, 0.01, caption(runs, between, within), fontsize=7.5,
             va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(path, dpi=150)
    print("wrote", path)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    powder_id, out, paths = argv[0], argv[1], argv[2:]
    runs = load_runs(powder_id, paths)
    if len(runs) < 2:
        print("need at least 2 runs of {}; found {}".format(powder_id,
                                                            len(runs)))
        return 1
    plot(powder_id, runs, out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

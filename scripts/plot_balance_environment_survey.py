#!/usr/bin/env python3
"""Figure for the bare-pan environment survey (issue #116).

Three panels, because the survey makes three separate points that a single
time series blurs together:

  A  the record itself -- quiet nearly all the time, with one shock event
     that leaves a permanent zero offset,
  B  the same data as a quiet-stretch zoom, showing the floor is at spec,
  C  worst-case environmental error against measurement duration, which is
     the panel that actually decides which blocks can run.

Usage::

    python scripts/plot_balance_environment_survey.py \\
        docs/rig-checks/data/2026-08-20_balance-bare-pan-survey-600s.csv \\
        --out docs/rig-checks/frames/2026-08-20_balance-environment-survey.png
"""

from __future__ import annotations

import argparse
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, "scripts")
from balance_environment_survey import find_steps, window_spreads  # noqa: E402

TOLERANCE_MG = 5.0
BLOCKS = [(2.5, "one 360$\\degree$ rev"), (12.0, "block D"), (180.0, "block G dose")]


def load(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    return ([float(r["t_s"]) for r in rows],
            [float(r["mg"]) for r in rows],
            [r["status"] for r in rows])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csv")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    t, mg, status = load(args.csv)
    steps = find_steps(t, mg)

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))

    # -- A: the whole record ------------------------------------------------
    ax = axes[0]
    ax.plot(t, mg, lw=0.8, color="#2f6f9f")
    for ts, dv in steps:
        ax.axvline(ts, color="#c1443c", lw=1.2, ls="--")
        ax.annotate("shock, {:+.0f} mg\nzero offset is permanent".format(dv),
                    xy=(ts, max(mg)), xytext=(6, -12),
                    textcoords="offset points", fontsize=8, color="#c1443c",
                    va="top")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("balance reading (mg)")
    ax.set_title("A  Bare pan, nothing on the balance\n"
                 "quiet floor + slow creep + one mechanical step", fontsize=10)
    ax.grid(alpha=0.25)

    # -- B: the quietest 30 s in the record, on a scale where the floor shows -
    ax = axes[1]
    best, best_pp = None, None
    j = 0
    for i in range(len(t)):
        while j < len(t) and t[j] - t[i] < 30.0:
            j += 1
        if j - i < 20 or t[j - 1] - t[i] < 24.0:
            continue
        pp = max(mg[i:j]) - min(mg[i:j])
        if best_pp is None or pp < best_pp:
            best, best_pp = (i, j), pp
    a, b = best
    base = sum(mg[a:b]) / (b - a)
    ax.plot([v - t[a] for v in t[a:b]], [v - base for v in mg[a:b]],
            lw=1.0, color="#2f6f9f")
    ax.axhspan(-0.1, 0.1, color="#8fbf6f", alpha=0.35,
               label="0.1 mg display resolution")
    ax.set_ylim(-1.2, 1.2)
    ax.set_xlabel("time within the quietest 30 s (s)")
    ax.set_ylabel("deviation from local mean (mg)")
    ax.set_title("B  The same balance between disturbances\n"
                 "{:.1f} mg peak-to-peak -- the instrument is at spec"
                 .format(best_pp), fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.25)

    # -- C: the panel that decides the workflow -----------------------------
    ax = axes[2]
    durs, meds, p90s = [], [], []
    for dur in (2, 3, 5, 8, 12, 20, 30, 45, 60, 90, 120, 180, 300):
        sp = window_spreads(t, mg, float(dur))
        if len(sp) < 5:
            continue
        sp.sort()
        durs.append(dur)
        meds.append(sp[len(sp) // 2])
        p90s.append(sp[int(0.9 * len(sp))])
    ax.plot(durs, meds, "o-", color="#2f6f9f", label="median window")
    ax.plot(durs, p90s, "s--", color="#c1443c", label="90th percentile")
    ax.axhline(TOLERANCE_MG, color="#555", lw=1.0, ls=":")
    ax.text(durs[0], TOLERANCE_MG * 1.15, "block G tolerance $\\pm$5 mg",
            fontsize=8, color="#555")
    for x, label in BLOCKS:
        ax.axvline(x, color="#999", lw=0.8, alpha=0.7)
        ax.text(x, max(p90s) * 0.85, " " + label, rotation=90, fontsize=7.5,
                color="#555", va="top")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("measurement duration (s)")
    ax.set_ylabel("environmental error, peak-to-peak (mg)")
    ax.set_title("C  Error grows with how long a measurement takes\n"
                 "short trials survive; multi-minute doses do not", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.25, which="both")

    fig.tight_layout()
    fig.savefig(args.out, dpi=140)
    print("wrote {}".format(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

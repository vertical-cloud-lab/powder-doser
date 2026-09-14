#!/usr/bin/env python3
"""Figure for the 2026-08-20 funnel-removed balance check (issue #116).

Three panels:

A  the two quiet captures taken minutes after the paper funnel came out,
   against the noisy state the same balance fell into later the same
   session -- same axes, so the degradation is visible rather than
   asserted.
B  jitter and stable-frame fraction against wall-clock time, which is
   what shows the session getting *worse* while nothing physical
   changed.
C  the hands-off recovery: seven minutes with no actuation, binned per
   minute, showing the balance walking back down.

Usage::

    python scripts/plot_balance_funnel_removed.py --out FIG.png
"""

from __future__ import annotations

import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "docs", "rig-checks", "data")

# (label, filename, lab-local clock at the start of the capture)
CAPTURES = [
    ("re-zero + 75 s", "2026-08-20_balance-funnel-removed-w1-rezero75s.csv", "09:45"),
    ("120 s", "2026-08-20_balance-funnel-removed-w2-120s.csv", "09:50"),
    ("420 s", "2026-08-20_balance-funnel-removed-w3-420s.csv", "09:52"),
    ("120 s, after actuation", "2026-08-20_balance-funnel-removed-w4-postactuation-120s.csv", "10:12"),
    ("420 s, hands off", "2026-08-20_balance-funnel-removed-w5-handsoff-420s.csv", "10:25"),
]

TOLERANCE_MG = 5.0      # block G dose tolerance


def load(name):
    path = os.path.join(DATA, name)
    with open(path) as fh:
        rows = [(float(r["t_s"]), r["status"], float(r["mg"]))
                for r in csv.DictReader(fh)]
    return rows


def jitter(values):
    if len(values) < 2:
        return 0.0
    return sum(abs(values[i + 1] - values[i])
               for i in range(len(values) - 1)) / (len(values) - 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="docs/rig-checks/frames/"
                                     "2026-08-20_balance-funnel-removed.png")
    args = ap.parse_args(argv)

    caps = [(label, load(name), clock) for label, name, clock in CAPTURES]

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))

    # -- A: quiet vs noisy, same axes ---------------------------------
    ax = axes[0]
    for label, rows, clock in caps:
        if clock not in ("09:50", "10:12"):
            continue
        t = [r[0] for r in rows]
        # Plot each capture about its own median: the question is spread,
        # not where the tare happened to land.
        mid = sorted(r[2] for r in rows)[len(rows) // 2]
        ax.plot(t, [r[2] - mid for r in rows], lw=0.9,
                label="{} ({} MDT)".format(label, clock))
    ax.axhspan(-TOLERANCE_MG, TOLERANCE_MG, color="0.85", zorder=0,
               label="block G tolerance")
    ax.set_xlabel("seconds into capture")
    ax.set_ylabel("mg from capture median")
    ax.set_title("A  same balance, 22 minutes apart\n(no physical change in between)")
    ax.legend(fontsize=8)

    # -- B: jitter / stability against wall clock ----------------------
    ax = axes[1]
    clocks = [c for _, _, c in caps]
    jit = [jitter([r[2] for r in rows]) for _, rows, _ in caps]
    stable = [100.0 * sum(1 for r in rows if r[1] == "ST") / len(rows)
              for _, rows, _ in caps]
    x = range(len(caps))
    ax.plot(x, jit, "o-", color="#b2432f", label="jitter (mg)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(clocks)
    ax.set_xlabel("lab clock (MDT)")
    ax.set_ylabel("sample-to-sample jitter, mg")
    ax.axhline(0.30, ls="--", lw=0.9, color="#b2432f",
               label="drafts above this")
    ax2 = ax.twinx()
    ax2.plot(x, stable, "s--", color="#2f6fb2", label="stable frames (%)")
    ax2.set_ylabel("stable frames, %")
    ax2.set_ylim(0, 100)
    ax.set_title("B  it got worse through the session\n(rig ruled out: see the write-up)")
    lines, labels = ax.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax.legend(lines + l2, labels + lb2, fontsize=8, loc="upper center")

    # -- C: hands-off recovery, per minute -----------------------------
    ax = axes[2]
    rows = caps[-1][1]
    bins, pps, jits = [], [], []
    for lo in range(0, 420, 60):
        window = [r for r in rows if lo <= r[0] < lo + 60]
        if not window:
            continue
        vals = [r[2] for r in window]
        bins.append(lo // 60 + 1)
        pps.append(max(vals) - min(vals))
        jits.append(jitter(vals))
    ax.bar([b - 0.18 for b in bins], pps, width=0.36, label="peak-to-peak (mg)",
           color="#7a9cc6")
    ax.bar([b + 0.18 for b in bins], [j * 10 for j in jits], width=0.36,
           label="jitter x10 (mg)", color="#b2432f")
    ax.axhline(TOLERANCE_MG, ls="--", lw=0.9, color="0.3",
               label="block G tolerance")
    ax.set_xlabel("minute of the hands-off capture")
    ax.set_ylabel("mg")
    ax.set_title("C  recovering with nothing touched\n(still not back to a runnable floor)")
    ax.legend(fontsize=8)

    fig.suptitle("A&D HR-100A after the paper funnel was removed -- 2026-08-20, "
                 "glass beaker, enclosure on, sash down", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=130)
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

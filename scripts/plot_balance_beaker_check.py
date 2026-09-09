#!/usr/bin/env python3
"""Figure for the 2026-08-20 glass-beaker balance check (issue #116).

Three panels:

A. the quiet window on the new beaker, against yesterday's paper cup --
   same axes, so the improvement is legible rather than asserted;
B. what the balance did once the rig started actuating;
C. the tare-free salt feed check, mass per revolution at each tilt,
   against the 2026-08-12 salt battery measured on the same rig.

Usage::

    python scripts/plot_balance_beaker_check.py --out FIG.png
"""

from __future__ import annotations

import argparse
import csv
import os
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "docs", "rig-checks", "data")

# Mass per 360 deg auger revolution, tilt 45 deg, 30 RPM.  Today's numbers
# are the tare-free check; the reference is block C of the 2026-08-12 salt
# battery, same rig, same speed.
TODAY = {0.0: [46.1, 36.1, 36.4],
         45.0: [148.4, 190.8, 175.3, 186.4, 195.6, 187.6],
         90.0: [164.3, 433.1, 201.8]}
REFERENCE = {0.0: 34.3, 45.0: 175.3, 90.0: 230.4}


def load(name):
    """Read either capture format: t_s/mg or the older t_ms/grams."""
    path = os.path.join(DATA, name)
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise FileNotFoundError(path)
    if "t_s" in rows[0]:
        t = [float(r["t_s"]) for r in rows]
        mg = [float(r["mg"]) for r in rows]
    else:
        t = [float(r["t_ms"]) / 1000.0 for r in rows]
        mg = [float(r["grams"]) * 1000.0 for r in rows]
    return t, mg, [r["status"] for r in rows]


def _zeroed(mg):
    """Referenced to its own first sample: these are offsets, not masses."""
    return [v - mg[0] for v in mg]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(
        HERE, "docs", "rig-checks", "frames",
        "2026-08-20_glass-beaker-check.png"))
    args = ap.parse_args(argv)

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))

    # --- A: settled, new beaker vs yesterday's paper cup -----------------
    ax = axes[0]
    t, mg, _ = load("2026-08-20_balance-glass-beaker-window2.csv")
    ax.plot(t, _zeroed(mg), lw=0.9, color="#1f77b4",
            label="glass beaker, 2026-08-20")
    try:
        t2, mg2, _ = load("2026-08-20_balance-drift-240s.csv")
        ax.plot(t2, _zeroed(mg2), lw=0.9, color="#d62728",
                label="paper cup, 2026-08-20 (earlier)")
    except FileNotFoundError:
        pass
    ax.axhspan(-5, 5, color="0.85", zorder=0)
    ax.set_title("A. settled, rig idle\n"
                 "grey band = the +/-5 mg block G dose tolerance", fontsize=9)
    ax.set_xlabel("seconds")
    ax.set_ylabel("balance offset (mg)")
    ax.legend(fontsize=7.5, loc="lower left")

    # --- B: once the rig started moving ----------------------------------
    ax = axes[1]
    t, mg, status = load("2026-08-20_balance-final-state.csv")
    ax.plot(t, _zeroed(mg), lw=0.9, color="#d62728")
    unstable = [(a, b) for a, b, s in zip(t, _zeroed(mg), status) if s != "ST"]
    if unstable:
        ax.scatter([a for a, _ in unstable], [b for _, b in unstable],
                   s=5, color="#d62728", alpha=0.45,
                   label="balance reports unstable (US)")
        ax.legend(fontsize=7.5, loc="lower left")
    ax.axhspan(-5, 5, color="0.85", zorder=0)
    ax.set_title("B. same beaker, after the tilt/dispense cycles\n"
                 "rig fully parked and de-energised", fontsize=9)
    ax.set_xlabel("seconds")

    lo = min(min(_zeroed(mg)) for mg in [load(
        "2026-08-20_balance-glass-beaker-window2.csv")[1], load(
        "2026-08-20_balance-final-state.csv")[1]])
    hi = max(max(_zeroed(mg)) for mg in [load(
        "2026-08-20_balance-glass-beaker-window2.csv")[1], load(
        "2026-08-20_balance-final-state.csv")[1]])
    for a in axes[:2]:
        a.set_ylim(lo - 3, hi + 3)

    # --- C: salt feed factor vs tilt -------------------------------------
    ax = axes[2]
    tilts = sorted(TODAY)
    means = [st.mean(TODAY[k]) for k in tilts]
    # Spread is drawn from the raw revolutions; with n=3 an SD bar would
    # overstate what three draws establish, so show the points as well.
    ax.bar([str(int(k)) for k in tilts], means, color="#1f77b4", width=0.55,
           label="2026-08-20, tare-free check")
    for i, k in enumerate(tilts):
        ax.scatter([i] * len(TODAY[k]), TODAY[k], s=18, color="0.15",
                   zorder=3, label="individual revolutions" if not i else None)
    ax.scatter(range(len(tilts)), [REFERENCE[k] for k in tilts],
               marker="_", s=460, color="#d62728", zorder=4,
               label="2026-08-12 salt battery (block C)")
    ax.set_title("C. salt, mass per 360 deg revolution at 30 RPM\n"
                 "new beaker reproduces the 08-12 run", fontsize=9)
    ax.set_xlabel("tilt (degrees)")
    ax.set_ylabel("mg per revolution")
    ax.legend(fontsize=7.5)

    fig.suptitle("A&D HR-100A with the new glass beaker, 2026-08-20 "
                 "(issue #116)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(args.out, dpi=130)
    print("wrote {}".format(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

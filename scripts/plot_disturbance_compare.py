#!/usr/bin/env python3
"""Compare two balance-disturbance battery sessions state-by-state.

Built for r2 (2026-09-15 morning, covered auger, pre drift-fix) vs r3
(same day, empty auger, post drift-fix), where the comparison itself is
the finding: the same actuation sequence that r2 resolved as ±10-60 mg
disturbance structure leaves r3's stream flat at an exact 0.0000 g with
the ST flag asserted straight through spins. Bench observation
(2026-09-16, PR #131) confirmed the r3 flatness is genuine — on the
post-fix bench actuation couples <0.1 mg into the balance; see the r3
README for the corrected interpretation.

Usage:
    python scripts/plot_disturbance_compare.py \
        <dirA> <labelA> <dirB> <labelB> <out.png>

Each dir is an analyze_balance_disturbance.py output directory
(samples.csv, blocks_summary.csv, tap_epochs.csv).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# dataviz reference palette (light mode), validated order
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
SURFACE = "#fcfcfb"
S1_BLUE = "#2a78d6"
S2_ORANGE = "#eb6834"

# actuation states shown, in battery order: (label, [source blocks])
STATES = [
    ("quiet", ["quiet_pre", "quiet_mid1", "quiet_mid2", "quiet_mid3",
               "quiet_mid4", "quiet_post"]),
    ("single taps", ["tap_single"]),
    ("3-pulse bursts", ["tap_burst"]),
    ("spin 15 rpm", ["auger15_p1", "auger15_p2"]),
    ("spin 30 rpm", ["auger30_p1", "auger30_p2"]),
    ("spin 55 rpm", ["auger55_p1", "auger55_p2"]),
    ("spin 75 rpm", ["auger75_p1", "auger75_p2"]),
    ("stepper hold", ["stepper_hold"]),
    ("45\N{DEGREE SIGN} steps", ["auger_steps"]),
    ("spin + tap", ["combined"]),
    ("servo moves", ["servo_moves"]),
]
SIGMA_FLOOR = 0.05  # mg, log-axis clip (matches analyze_* convention)


def style_ax(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, axis="y", color=MUTED, alpha=0.22, linewidth=0.6)


def state_rows(blocks):
    sig, st = [], []
    for _, srcs in STATES:
        b = blocks[blocks["block"].isin(srcs)]
        sig.append(b["sigma_detr_mg"].mean() if len(b) else np.nan)
        st.append(b["st_frac"].mean() * 100.0 if len(b) else np.nan)
    return np.array(sig), np.array(st)


def mean_tap_curve(epochs):
    bins = np.arange(-1.0, 4.5, 0.2)
    e = epochs.copy()
    e["bin"] = pd.cut(e["t_rel_s"], bins)
    mm = e.groupby("bin", observed=True).agg(
        t=("t_rel_s", "mean"), d=("dev_mg", "mean"))
    return mm["t"].values, mm["d"].values


def main():
    dir_a, lab_a, dir_b, lab_b, out = sys.argv[1:6]
    runs = []
    for d, lab, col in ((dir_a, lab_a, S1_BLUE), (dir_b, lab_b, S2_ORANGE)):
        d = Path(d)
        runs.append({
            "label": lab, "color": col,
            "blocks": pd.read_csv(d / "blocks_summary.csv"),
            "epochs": pd.read_csv(d / "tap_epochs.csv"),
        })

    fig, (axt, axs, axf) = plt.subplots(
        1, 3, figsize=(13.0, 3.9), dpi=160,
        gridspec_kw={"width_ratios": [1.05, 1.25, 1.25], "wspace": 0.42})
    fig.patch.set_facecolor(SURFACE)

    # --- panel 1: mean single-tap impulse response, overlaid ---
    for _, grp in runs[0]["epochs"].groupby("event"):
        axt.plot(grp["t_rel_s"], grp["dev_mg"], color=MUTED, lw=0.6,
                 alpha=0.30)
    for r in runs:
        t, d = mean_tap_curve(r["epochs"])
        axt.plot(t, d, color=r["color"], lw=2.0, label=r["label"])
    axt.axvline(0, color=INK2, lw=0.8, ls=":")
    axt.set_title("Single-tap impulse response\n(gray: individual "
                  + runs[0]["label"].split(":")[0] + " taps)",
                  color=INK, fontsize=10, loc="left")
    axt.set_xlabel("time since tap (s)", color=INK2, fontsize=9)
    axt.set_ylabel("mass vs pre-tap (mg)", color=INK2, fontsize=9)
    axt.legend(frameon=False, fontsize=8, labelcolor=INK2,
               loc="lower right")
    style_ax(axt)

    # --- panels 2+3: sigma and ST fraction per actuation state ---
    x = np.arange(len(STATES))
    names = [n for n, _ in STATES]
    for ax, key in ((axs, "sig"), (axf, "st")):
        for i, r in enumerate(runs):
            sig, st = state_rows(r["blocks"])
            vals = sig if key == "sig" else st
            shown = (np.clip(vals, SIGMA_FLOOR, None)
                     if key == "sig" else vals)
            ax.bar(x + (i - 0.5) * 0.38, shown, width=0.34,
                   color=r["color"], label=r["label"])
        if key == "sig":
            ax.set_yscale("log")
            ax.set_ylim(SIGMA_FLOOR * 0.8, 120.0)
            ax.set_ylabel("detrended sigma (mg, log)", color=INK2,
                          fontsize=9)
            ax.axhline(SIGMA_FLOOR, color=MUTED, lw=0.8, ls="--")
            ax.text(x[0] - 0.45, SIGMA_FLOOR * 1.1,
                    "display floor", ha="left", va="bottom",
                    fontsize=7, color=MUTED)
            ax.set_title("Balance noise per actuation state",
                         color=INK, fontsize=10, loc="left")
        else:
            ax.set_ylabel("ST-flagged frames (%)", color=INK2, fontsize=9)
            ax.set_ylim(0, 138)
            ax.set_yticks((0, 25, 50, 75, 100))
            ax.set_title("Stable flag per actuation state",
                         color=INK, fontsize=10, loc="left")
        ax.set_xticks(x, names, rotation=55, ha="right", fontsize=7.5,
                      color=INK2)
        ax.legend(frameon=False, fontsize=8, labelcolor=INK2,
                  loc="upper right")
        style_ax(ax)

    fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
    print("wrote", out)


if __name__ == "__main__":
    main()

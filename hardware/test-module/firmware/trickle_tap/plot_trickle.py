#!/usr/bin/env python3
"""Render a trickle-tap telemetry CSV into the inspection figure.

Host-side (laptop) tool, CPython + matplotlib -- NOT for the Pico.

Input: a telemetry file from a dose, obtained either by downloading
``/trickle_log_NNN.csv`` off the Pico (MicroPico file view) or by typing
``log`` at the rig REPL and pasting the output into a file (the
``--- BEGIN/END ---`` marker lines are tolerated and stripped).

Output: ``<input>.png`` (or --out) with four panels on a shared time
axis: mass with the goal/cutoff lines and stage shading, estimated rate
vs its set-point, the commanded auger rpm, and the KF prediction sigma.

Usage:  python3 plot_trickle.py trickle_log_000.csv [--out fig.png]
        python3 plot_trickle.py pasted_log.txt --goal 0.2
"""

import argparse
import csv
import io
import sys

# Categorical palette (validated, see PR #154): estimate=blue,
# target/prediction=orange, command=aqua, uncertainty=violet.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
VIOLET = "#4a3aa7"
INK = "#1a1a19"
INK2 = "#6f6e66"
GRID = "#e6e5e0"

STAGE_TINTS = {"bulk": "#f2f0ea", "trickle": "#ffffff", "tap": "#eef2f7"}


def read_rows(path):
    with open(path) as f:
        text = f.read()
    lines = [ln for ln in text.splitlines()
             if ln.strip() and not ln.startswith("---")]
    rows = list(csv.DictReader(io.StringIO("\n".join(lines))))
    if not rows or "t_s" not in rows[0]:
        sys.exit("no telemetry header found in {} -- expected the CSV "
                 "from the 'log' command or /trickle_log_NNN.csv".format(path))
    return rows


def col(rows, name, phase=None):
    t, v = [], []
    for row in rows:
        if phase is not None and row["phase"] != phase:
            continue
        s = row.get(name, "")
        if s:
            t.append(float(row["t_s"]))
            v.append(float(s))
    return t, v


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_path")
    ap.add_argument("--out", default=None)
    ap.add_argument("--goal", type=float, default=None,
                    help="goal mass (g); default = cutoff_g + margin from "
                         "the file, falling back to the last cutoff row")
    ap.add_argument("--trickle-only", action="store_true",
                    help="zoom the time axis to the PI trickle stage")
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = read_rows(args.csv_path)
    if args.trickle_only:
        keep = [float(r["t_s"]) for r in rows
                if r["phase"].startswith("trickle")]
        if keep:
            lo, hi = min(keep) - 1.0, max(keep) + 2.0
            rows = [r for r in rows if lo <= float(r["t_s"]) <= hi]
    trickle = [r for r in rows if r["phase"] == "trickle"]

    t_m, m_hat = col(rows, "m_g")
    t_z, z = col(rows, "z_g", phase="trickle")
    t_pred, pred = col(rows, "pred_g")
    t_cut, cut = col(rows, "cutoff_g")
    t_r, r_hat = col(rows, "r_gps")
    t_sp, r_sp = col(rows, "r_sp_gps")
    t_rpm, rpm = col(rows, "rpm_cmd")
    t_sig, sig = col(rows, "sigma_g")

    goal = args.goal
    if goal is None and cut:
        goal = cut[-1] + 0.035
    cutoff = cut[-1] if cut else None

    fig, axes = plt.subplots(4, 1, sharex=True, figsize=(9, 10),
                             height_ratios=[2.2, 1, 1, 1])
    fig.patch.set_facecolor("white")
    ax_m, ax_r, ax_u, ax_s = axes

    # stage shading spans (from the phase column, any row type)
    spans = []
    for row in rows:
        ph = row["phase"].replace("_end", "")
        ts = float(row["t_s"])
        if spans and spans[-1][0] == ph:
            spans[-1][2] = ts
        else:
            spans.append([ph, ts, ts])
    for ax in axes:
        for ph, a, b in spans:
            if b > a and ph in STAGE_TINTS and STAGE_TINTS[ph] != "#ffffff":
                ax.axvspan(a, b, color=STAGE_TINTS[ph], zorder=0)
    for ph, a, b in spans:
        if b > a:
            ax_m.text((a + b) / 2.0, 1.015, ph, transform=ax_m.get_xaxis_transform(),
                      ha="center", va="bottom", fontsize=9, color=INK2)

    # -- panel 1: mass ------------------------------------------------
    if t_z:
        ax_m.plot(t_z, z, ".", ms=3.5, color=INK2, alpha=0.55, zorder=2,
                  label="balance frames (raw)")
    ax_m.plot(t_m, m_hat, lw=2, color=BLUE, zorder=4, label="KF mass $\\hat{m}$")
    if t_pred:
        ax_m.plot(t_pred, pred, lw=2, color=ORANGE, zorder=3,
                  label="cutoff pred. $\\hat{m}+\\hat{r}\\tau+k\\sigma$")
    if goal is not None:
        ax_m.axhline(goal, color=INK, lw=1, ls=(0, (5, 3)), zorder=1)
        ax_m.text(0.01, goal, " goal %.4f g" % goal, va="bottom", fontsize=9,
                  color=INK, transform=ax_m.get_yaxis_transform())
    if cutoff is not None:
        ax_m.axhline(cutoff, color=ORANGE, lw=1, ls=(0, (2, 2)), zorder=1)
        ax_m.text(0.01, cutoff, " cutoff (goal $-$ margin)", va="top",
                  fontsize=9, color=ORANGE,
                  transform=ax_m.get_yaxis_transform())
    ax_m.set_ylabel("mass (g)")
    ax_m.legend(loc="lower right", frameon=False, fontsize=9)

    # -- panel 2: rate ------------------------------------------------
    ax_r.plot(t_r, [1e3 * v for v in r_hat], lw=2, color=BLUE,
              label="KF rate $\\hat{r}$")
    ax_r.plot(t_sp, [1e3 * v for v in r_sp], lw=2, ls=(0, (4, 2)),
              color=ORANGE, label="set-point $r_{sp}$")
    ax_r.set_ylabel("rate (mg/s)")
    ax_r.legend(loc="upper right", frameon=False, fontsize=9)

    # -- panel 3: command ---------------------------------------------
    ax_u.step(t_rpm, rpm, where="post", lw=2, color=AQUA)
    ax_u.set_ylabel("commanded\nauger rpm")

    # -- panel 4: uncertainty -----------------------------------------
    ax_s.plot(t_sig, [1e3 * v for v in sig], lw=2, color=VIOLET)
    ax_s.set_ylabel("prediction\n$\\sigma$ (mg)")
    ax_s.set_xlabel("time since dose start (s)")

    for ax in axes:
        ax.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(INK2)
        ax.tick_params(colors=INK2, labelcolor=INK)

    n_polls = len(trickle)
    fig.suptitle("Trickle-tap dose telemetry -- {} trickle polls".format(
        n_polls), fontsize=12, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    out = args.out or (args.csv_path.rsplit(".", 1)[0] + ".png")
    fig.savefig(out, dpi=150, facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    main()

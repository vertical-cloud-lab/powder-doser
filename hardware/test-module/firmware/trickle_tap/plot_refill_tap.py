#!/usr/bin/env python3
"""Render the tap stage of a dose: the refill-tap rule, tap by tap.

Host-side (laptop) tool, CPython + matplotlib -- NOT for the Pico.

Input: the same telemetry CSV as ``plot_trickle.py`` (``/trickle_log_
NNN.csv`` off the Pico, or the ``log`` output pasted into a file).  The
tap and refill rows carry the settled mass after every tap / refill;
from them this rebuilds what the controller decided on: each tap's
yield, the running average (restarted at every refill, as on the rig),
and the refill trigger  need / REFILL_TAPS_TO_GO.

Output: ``<input>_endgame.png`` (or --out), two panels on a shared time
axis from the first tap: distance to the goal with the tolerance band
and the refills, and per-tap yield vs the running average vs the
trigger -- a refill fires where the average drops under the trigger.
``--compare stock.csv`` overlays another dose's staircase (e.g. one run
with ``set refill_enabled 0``) for an A/B look.

The rule's knobs default to refill_params.py / trickle_params.py next to
this file; pass the values you ran with if you changed them with ``set``.

Usage:  python3 plot_refill_tap.py trickle_log_003.csv --goal 0.5
        python3 plot_refill_tap.py refill.csv --compare stock.csv
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import refill_params as rp           # noqa: E402
import trickle_params as tp          # noqa: E402
from plot_trickle import (AQUA, BLUE, GRID, INK, INK2,  # noqa: E402
                          ORANGE, read_rows)

ENDGAME = ("tap", "refill")


def endgame(rows):
    """-> (t0, [(t_s, kind, mass_g)]) for the tap stage, kind tap|refill,
    led by the last settled mass before the first tap (kind 'start')."""
    first = next((i for i, r in enumerate(rows) if r["phase"] in ENDGAME),
                 None)
    if first is None:
        sys.exit("no tap-stage rows in this telemetry (did the dose reach "
                 "the tap endgame?)")
    out = []
    for r in reversed(rows[:first]):
        if r.get("z_g"):
            out.append((float(r["t_s"]), "start", float(r["z_g"])))
            break
    for r in rows[first:]:
        if r["phase"] in ENDGAME and r.get("z_g"):
            out.append((float(r["t_s"]), r["phase"], float(r["z_g"])))
    t0 = out[0][0]
    return t0, out


def rebuild(points, goal, tol, avg_n, taps_to_go):
    """The controller's view after every tap: yield, avg, trigger."""
    taps, refills = [], []
    window = []
    prev = points[0][2]
    for t, kind, m in points[1:]:
        gain = m - prev
        prev = m
        if kind == "refill":
            refills.append((t, m, gain))
            window = []
            continue
        window.append(gain)
        window = window[-max(1, avg_n):]
        need = goal - tol - m
        taps.append((t, gain, sum(window) / len(window), need / taps_to_go,
                     need))
    return taps, refills


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--compare", default=None,
                    help="second telemetry CSV to overlay (A/B)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--goal", type=float, default=None,
                    help="goal mass (g); default GOAL_MASS_G")
    ap.add_argument("--tol", type=float, default=tp.TOLERANCE_G)
    ap.add_argument("--avg-taps", type=int, default=rp.REFILL_AVG_TAPS)
    ap.add_argument("--taps-to-go", type=float, default=rp.REFILL_TAPS_TO_GO)
    ap.add_argument("--min-to-go", type=float, default=rp.REFILL_MIN_TO_GO_G)
    ap.add_argument("--label", default="this dose")
    ap.add_argument("--compare-label", default="comparison dose")
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    goal = args.goal if args.goal is not None else tp.GOAL_MASS_G
    tol = args.tol
    t0, pts = endgame(read_rows(args.csv_path))
    taps, refills = rebuild(pts, goal, tol, args.avg_taps, args.taps_to_go)

    fig, (ax_m, ax_y) = plt.subplots(2, 1, sharex=True, figsize=(9, 7.5),
                                     height_ratios=[1.4, 1])
    fig.patch.set_facecolor("white")

    # -- panel 1: distance to the goal ----------------------------------
    ax_m.axhspan(-1000 * tol, 1000 * tol, color="#eef2f7", zorder=0)
    ax_m.axhline(0.0, color=INK, lw=1, ls=(0, (5, 3)), zorder=1)
    ax_m.text(0.995, 1000 * tol, "tolerance band  ", ha="right",
              va="bottom", fontsize=9, color=INK2,
              transform=ax_m.get_yaxis_transform())
    zone = -1000.0 * (args.min_to_go + tol)
    ax_m.axhline(zone, color=INK2, lw=1, ls=(0, (2, 2)), zorder=1)
    ax_m.text(0.005, zone, " no refills above this line", ha="left",
              va="bottom", fontsize=9, color=INK2,
              transform=ax_m.get_yaxis_transform())
    if args.compare:
        c0, cpts = endgame(read_rows(args.compare))
        ax_m.step([t - c0 for t, _, _ in cpts],
                  [1000 * (m - goal) for _, _, m in cpts], where="post",
                  lw=2, color=INK2, zorder=2, label=args.compare_label)
        t_end, _, m_end = cpts[-1]
        ax_m.annotate("{} {:.0f} s".format(args.compare_label, t_end - c0),
                      (t_end - c0, 1000 * (m_end - goal)),
                      textcoords="offset points", xytext=(-2, 10),
                      ha="right", va="bottom", fontsize=9, color=INK)
    ax_m.step([t - t0 for t, _, _ in pts],
              [1000 * (m - goal) for _, _, m in pts], where="post", lw=2,
              color=BLUE, zorder=3, label=args.label)
    t_end, _, m_end = pts[-1]
    ax_m.annotate("{} {:.0f} s".format(args.label, t_end - t0),
                  (t_end - t0, 1000 * (m_end - goal)),
                  textcoords="offset points", xytext=(6, -2), ha="left",
                  va="top", fontsize=9, color=INK)
    for i, (t, m, gain) in enumerate(refills):
        ax_m.plot([t - t0], [1000 * (m - goal)], marker="^", ms=8,
                  color=AQUA, mec="white", mew=1.5, zorder=4,
                  label="refill (auger turn)" if i == 0 else None)
        ax_m.annotate("{:+.1f}".format(1000 * gain), (t - t0,
                      1000 * (m - goal)), textcoords="offset points",
                      xytext=(0, 9), ha="center", fontsize=8, color=INK)
    ax_m.set_ylabel("mass $-$ goal (mg)")
    ax_m.legend(loc="lower right", frameon=False, fontsize=9)

    # -- panel 2: tap yield vs the rule ---------------------------------
    for t, _, _ in refills:
        for ax in (ax_m, ax_y):
            ax.axvline(t - t0, color=AQUA, lw=1, alpha=0.5, zorder=1)
    tt = [t - t0 for t, *_ in taps]
    ax_y.plot(tt, [1000 * g for _, g, _, _, _ in taps], "o", ms=4.5,
              color=INK2, alpha=0.7, zorder=2, label="tap yield")
    ax_y.plot(tt, [1000 * a for _, _, a, _, _ in taps], lw=2, color=BLUE,
              zorder=3, label="running average (last {}, restarts at a "
              "refill)".format(args.avg_taps))
    trig_t = [t - t0 for t, _, _, _, need in taps if need >= args.min_to_go]
    trig = [1000 * tr for _, _, _, tr, need in taps
            if need >= args.min_to_go]
    if trig:
        ax_y.plot(trig_t, trig, lw=2, ls=(0, (4, 2)), color=ORANGE,
                  zorder=3, label="refill below this: still needed / "
                  "{:g}".format(args.taps_to_go))
    ax_y.axhline(0.0, color=INK2, lw=0.8, zorder=1)
    ax_y.set_ylabel("yield per tap (mg)")
    ax_y.set_xlabel("time since the first tap (s)")
    ax_y.legend(loc="upper right", frameon=False, fontsize=9)

    for ax in (ax_m, ax_y):
        ax.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(INK2)
        ax.tick_params(colors=INK2, labelcolor=INK)

    title = args.title or ("Tap stage: {} taps, {} refills".format(
        len(taps), len(refills)))
    fig.suptitle(title, fontsize=12, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = args.out or (args.csv_path.rsplit(".", 1)[0] + "_endgame.png")
    fig.savefig(out, dpi=150, facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    main()

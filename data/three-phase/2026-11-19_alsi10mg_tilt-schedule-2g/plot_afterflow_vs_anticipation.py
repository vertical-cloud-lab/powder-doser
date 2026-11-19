#!/usr/bin/env python3
"""AlSi10Mg, 2 g: final error per trial, and the afterflow at each halt against the fine stage's anticipation.

Adapted from the 2026-11-19 salt run's script of the same name (only the
launch folder, the powder and the 2 g target differ).

Reads ``launch1_2243Z/trials_summary.csv`` (written by
``scripts/analyze_tilt_trials.py``) and writes ``afterflow_vs_anticipation.png``:

* Panel A: each completed trial's final error in run order, with the +/- 1 mg
  tolerance band (stalled trials are named in a note, not plotted).  Filled marks ended in the tap stage; hollow marks never reached it
  (the fine stage's afterflow carried them to or past the goal).
* Panel B: AlSi10Mg that landed after each auger halt, against the flow rate at
  the halt.  Blue: the bulk halt (80 rpm, plate at 40 deg).  Orange: the fine
  halt (25 rpm, 30 deg, both with taps).  The dashed line is the fine stage's
  20 mg anticipation; the dotted line is afterflow = 1.07 s x flow, the
  2026-08-07 stop-response fit.

usage: python plot_afterflow_vs_anticipation.py [launch dir]
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "launch1_2243Z")

BULK = "#2a78d6"     # same stage colours as scripts/analyze_tilt_trials.py
FINE = "#eb6834"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
BAND = "#ecebe7"
SURFACE = "#fcfcfb"

FINE_ANTICIPATION_MG = 20.0
FINE_EXIT_TO_GO_MG = 25.0       # t2
TAU_S = 1.07                    # 2026-08-07 stop response, afterflow / flow


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


ALL = list(csv.DictReader(open(os.path.join(LAUNCH, "trials_summary.csv"))))
# Completed doses only (ok / overshoot); stalled or failed trials are listed
# in the panel A note instead.
rows = [r for r in ALL if r["status"] in ("ok", "overshoot")
        and fnum(r["error_mg"]) is not None]
stalled = [r for r in ALL if r["status"] not in ("ok", "overshoot")]

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.9),
                               gridspec_kw={"width_ratios": [1.15, 1]})

# --- A: final error per trial ---------------------------------------------
ax1.axhspan(-1, 1, color=BAND, zorder=0)
ax1.axhline(0, color=INK2, lw=0.8, zorder=1)
for r in rows:
    n = int(r["trial"])
    e = fnum(r["error_mg"])
    tapped = (fnum(r["tap_cycles"]) or 0) > 0
    ax1.plot([n, n], [0, e], color=GRID, lw=2, zorder=2, solid_capstyle="round")
    ax1.plot(n, e, "o", ms=8, zorder=3, mec=INK, mew=1.4,
             mfc=INK if tapped else SURFACE)
ax1.set_xlabel("trial (run order)")
ax1.set_ylabel("final error (mg)")
ax1.set_xlim(0.2, max(int(r["trial"]) for r in rows) + 0.8)
ax1.set_ylim(min(-12, min(fnum(r["error_mg"]) for r in rows) - 4),
             max(fnum(r["error_mg"]) for r in rows) + 10)
ax1.grid(axis="y", color=GRID, lw=0.8)
ax1.set_axisbelow(True)
n_ok = sum(1 for r in rows if abs(fnum(r["error_mg"])) <= 1.0)
note = "grey band: the ±1 mg tolerance ({} of {} inside)".format(
    n_ok, len(rows))
if stalled:
    note += "\nnot shown: trial{} {} stalled ({})".format(
        "s" if len(stalled) > 1 else "",
        ", ".join(r["trial"] for r in stalled),
        ", ".join("{:.3f} g".format(fnum(r["final_g"])) for r in stalled
                  if fnum(r["final_g"]) is not None))
ax1.text(0.99, 0.03, note, transform=ax1.transAxes, ha="right", va="bottom",
         color=INK2, fontsize=9)
ax1.plot([], [], "o", ms=8, mec=INK, mew=1.4, mfc=INK, ls="none",
         label="reached the tap stage")
ax1.plot([], [], "o", ms=8, mec=INK, mew=1.4, mfc=SURFACE, ls="none",
         label="ended in the fine stage")
ax1.legend(loc="upper right", bbox_to_anchor=(0.82, 1.0), frameon=False,
           fontsize=9)
ax1.set_title("A  Final error of each completed 2 g AlSi10Mg trial", loc="left", fontsize=11,
              color=INK)

# --- B: afterflow vs flow at the halt -------------------------------------
xmax = 0.0
for stage, col, lab in (("bulk", BULK, "bulk halt: 80 rpm, plate 40°"),
                        ("fine", FINE, "fine halt: 25 rpm, plate 30°")):
    xs, ys = [], []
    for r in rows:
        x = fnum(r[stage + "_rate_at_halt_g_per_s"])
        y = fnum(r[stage + "_afterflow_mg"])
        if x is None or y is None:
            continue
        xs.append(x)
        ys.append(y)
    xmax = max([xmax] + xs)
    ax2.plot(xs, ys, "o", ms=8, color=col, mec=SURFACE, mew=1.5, label=lab,
             zorder=3)
xline = [0, xmax * 1.08]
ax2.plot(xline, [TAU_S * 1000 * x for x in xline], ":", color=INK2, lw=1.4,
         zorder=2, label="1.07 s × flow (2026-08-07 fit)")
ax2.axhline(FINE_ANTICIPATION_MG, color=FINE, lw=1.4, ls="--", zorder=2)
ax2.text(xline[1], FINE_ANTICIPATION_MG - 2, "fine anticipation 20 mg",
         ha="right", va="top", color=INK2, fontsize=9)
ax2.axhline(FINE_ANTICIPATION_MG + FINE_EXIT_TO_GO_MG, color=GRID, lw=1.2,
            zorder=1)
ax2.text(xline[1], FINE_ANTICIPATION_MG + FINE_EXIT_TO_GO_MG + 2,
         "fine afterflow above 45 mg overshoots", ha="right", va="bottom",
         color=INK2, fontsize=9)
ax2.set_xlim(0, xline[1])
ax2.set_ylim(bottom=0)
ax2.set_xlabel("flow rate at the halt (g/s)")
ax2.set_ylabel("AlSi10Mg landed after the halt (mg)")
ax2.grid(color=GRID, lw=0.8)
ax2.set_axisbelow(True)
ax2.legend(loc="upper left", frameon=False, fontsize=9)
ax2.set_title("B  Afterflow at each halt", loc="left", fontsize=11, color=INK)

fig.tight_layout()
out = os.path.join(HERE, "afterflow_vs_anticipation.png")
fig.savefig(out, dpi=130)
print("wrote", out)

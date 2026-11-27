#!/usr/bin/env python3
"""Calcium lactate (2 g) against AlSi10Mg (2 g) and salt (1 g) on the same stepped-tilt protocol.

All three runs used three_phase_tilt_trials.py with the same stage settings
(bulk at 80 rpm with taps, plate 60 -> 40 deg, hand-off at 0.25 g to go;
fine at 30 deg / 25 rpm with taps, 20 mg anticipation, hand-off at 25 mg to
go; stock tap stage):

* calcium lactate, 2 g, script 2026-11-20b, launch 03:05 UTC (this folder)
* AlSi10Mg, 2 g, scripts 2026-11-19e and 2026-11-20a (launches 22:43 and 02:08)
* salt, 1 g, script 2026-11-19d (launch 21:43, old tube)

Reads each launch's ``trials_summary.csv`` and per-trial CSVs (written by
``scripts/analyze_tilt_trials.py``) and writes ``three_powders.png``:

* A: final error of every completed trial, one strip per powder.  Filled
  marks reached the tap stage; hollow marks ended in the fine stage.
* B: calcium lactate's final error in run order, same marks.
* C: the cup (minus the target) from each bulk halt until the fine stage
  starts its auger, i.e. powder landing with the auger stopped.  Dotted:
  the bulk's 800 ms settle.  Dashed: the fine stage's halt threshold
  (45 mg to go) and the target.
* D: powder landed between the bulk halt and the fine stage's auger start,
  against the flow at the halt.  Dotted line: afterflow = 1.07 s x flow
  (2026-08-07 stop response).

It also prints the per-powder numbers quoted in the README.

usage: python plot_three_powders.py
"""
import csv
import glob
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TP = os.path.join(HERE, "..", "..")  # data/stepped-tilt-trials/
RUNS = [  # (key, label, target g, launch folders)
    ("salt", "salt, 1 g", 1.0,
     [os.path.join(TP, "salt", "2026-11-19_salt_tilt-schedule-old-auger-80rpm", "launch1_2143Z")]),
    ("alsi10mg", "AlSi10Mg, 2 g", 2.0,
     [os.path.join(TP, "alsi10mg", "2026-11-19_alsi10mg_tilt-schedule-2g", "launch1_2243Z"),
      os.path.join(TP, "alsi10mg", "2026-11-19_alsi10mg_tilt-schedule-2g", "launch2_0208Z")]),
    ("calcium-lactate", "calcium lactate, 2 g", 2.0,
     [os.path.join(HERE, "launch1_0305Z")]),
]
# Powder identity: categorical slots 4, 7 and 5 (validated as a set, light
# mode).  Salt and AlSi10Mg keep the colours of plot_alsi10mg_vs_salt.py;
# slots 1-3 mean bulk / fine / tap in the other figures of these READMEs.
COL = {"salt": "#eda100", "alsi10mg": "#6250d6", "calcium-lactate": "#e87ba4"}
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
BAND = "#ecebe7"
SURFACE = "#fcfcfb"
TAU_S = 1.07
BULK_SETTLE_S = 0.8
FINE_HALT_TO_GO_G = 0.045


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load(folder):
    rows = list(csv.DictReader(open(os.path.join(folder, "trials_summary.csv"))))
    for r in rows:
        r["_csv"] = os.path.join(folder, r["csv"])
    return rows


def tail(path, target):
    """Frames from the bulk halt to the fine stage's auger start."""
    rows = list(csv.DictReader(open(path)))
    t_halt = t_run = None
    for r in rows:
        ev = r["events"] or ""
        if t_halt is None and r["stage"] == "bulk" and "auger halt" in ev:
            t_halt = float(r["t_s"])
        elif (t_halt is not None and r["stage"] == "fine"
              and "auger run" in ev):
            t_run = float(r["t_s"])
            break
    if t_halt is None or t_run is None:
        return None
    pts = [(float(r["t_s"]) - t_halt, float(r["mass_g"]) - target)
           for r in rows
           if r["mass_g"] not in ("", None)
           and t_halt <= float(r["t_s"]) <= t_run]
    return pts


DATA = {}
for key, label, target, folders in RUNS:
    trials = []
    for f in folders:
        trials += load(f)
    done = [r for r in trials if r["status"] in ("ok", "overshoot")]
    for r in done:
        r["_tap"] = bool(fnum(r["tap_cycles"]))
        r["_tail"] = tail(r["_csv"], target)
    DATA[key] = (label, target, done)

# ---- printed numbers -------------------------------------------------------
for key, (label, target, done) in DATA.items():
    errs = [fnum(r["error_mg"]) for r in done]
    inside = sum(1 for e in errs if abs(e) <= 1.0)
    taps = [r for r in done if r["_tap"]]
    land = []
    for r in done:
        if r["_tail"] and fnum(r["bulk_halt_g"]) is not None:
            land.append((r["_tail"][-1][1] + target - fnum(r["bulk_halt_g"]),
                         fnum(r["bulk_rate_at_halt_g_per_s"])))
    taus = [a / q for a, q in land if q]
    print("{}: {} completed, {} within +/-1 mg, median error {:+.1f} mg "
          "(range {:+.1f} to {:+.1f}); {} reached the tap stage (median "
          "{:+.1f} mg); median dose {:.1f} s".format(
              label, len(done), inside, statistics.median(errs), min(errs),
              max(errs), len(taps),
              statistics.median([fnum(r["error_mg"]) for r in taps]) if taps else float("nan"),
              statistics.median([fnum(r["dose_s"]) for r in done])))
    if land:
        print("   landed between bulk halt and fine start: median {:.0f} mg "
              "({:.0f}-{:.0f}); flow at halt {:.3f}-{:.3f} g/s; landed/flow "
              "median {:.2f} s ({:.2f}-{:.2f})".format(
                  1000 * statistics.median(a for a, _ in land),
                  1000 * min(a for a, _ in land), 1000 * max(a for a, _ in land),
                  min(q for _, q in land), max(q for _, q in land),
                  statistics.median(taus), min(taus), max(taus)))
    revs = [fnum(r["auger_rev"]) for r in done]
    print("   auger revs per dose: median {:.1f} ({:.1f}-{:.1f}); "
          "mg per rev {:.0f}".format(statistics.median(revs), min(revs),
                                    max(revs),
                                    1000 * target / statistics.median(revs)))

# ---- figure ----------------------------------------------------------------
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2})
fig, axs = plt.subplots(2, 2, figsize=(11.5, 8.2), facecolor=SURFACE)
for ax in axs.flat:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def mark(ax, x, y, key, filled):
    ax.plot(x, y, "o", ms=7, mfc=COL[key] if filled else SURFACE,
            mec=COL[key], mew=1.6, zorder=3)


# A: final error strips
ax = axs[0, 0]
ax.axhspan(-1, 1, color=BAND, zorder=0)
for i, (key, (label, target, done)) in enumerate(DATA.items()):
    n = len(done)
    for j, r in enumerate(sorted(done, key=lambda r: fnum(r["error_mg"]))):
        dx = (j - (n - 1) / 2) / max(n, 1) * 0.5
        mark(ax, i + dx, fnum(r["error_mg"]), key, r["_tap"])
    med = statistics.median(fnum(r["error_mg"]) for r in done)
    ax.plot([i - 0.32, i + 0.32], [med, med], color=INK, lw=2, zorder=4)
ax.set_xticks(range(len(DATA)))
ax.set_xticklabels(["{}\nmedian {:+.1f} mg".format(
    v[0], statistics.median(fnum(r["error_mg"]) for r in v[2]))
    for v in DATA.values()])
ax.set_xlim(-0.6, len(DATA) - 0.1)
ax.set_ylabel("final error (mg)")
ax.set_title("A  Final error, every completed trial", loc="left",
             fontsize=10, color=INK)
ax.legend(handles=[
    Line2D([], [], ls="", marker="o", ms=7, mfc=INK2, mec=INK2,
           label="reached the tap stage"),
    Line2D([], [], ls="", marker="o", ms=7, mfc=SURFACE, mec=INK2, mew=1.6,
           label="ended in the fine stage"),
    Line2D([], [], color=INK, lw=2, label="median"),
    plt.Rectangle((0, 0), 1, 1, color=BAND, label="±1 mg tolerance")],
    loc="upper left", frameon=False, fontsize=8)

# B: calcium lactate in run order
ax = axs[0, 1]
ax.axhspan(-1, 1, color=BAND, zorder=0)
label, target, done = DATA["calcium-lactate"]
for r in done:
    mark(ax, int(r["trial"]), fnum(r["error_mg"]), "calcium-lactate", r["_tap"])
ax.set_xticks(range(1, len(done) + 1))
ax.set_xlabel("trial")
ax.set_ylabel("final error (mg)")
ax.set_title("B  Calcium lactate in run order (filled: tap stage)", loc="left",
             fontsize=10, color=INK)

# C: landing after the bulk halt
ax = axs[1, 0]
for key, (label, target, done) in DATA.items():
    for r in done:
        if r["_tail"]:
            xs, ys = zip(*r["_tail"])
            ax.plot(xs, [1000 * y for y in ys], color=COL[key], lw=1.1,
                    alpha=0.75)
ax.axvline(BULK_SETTLE_S, color=INK2, ls=":", lw=1)
ax.annotate("bulk settle (800 ms)", (BULK_SETTLE_S + 0.05, -248), fontsize=8,
            color=INK2)
for yv, txt in ((-1000 * FINE_HALT_TO_GO_G, "fine stage halts its auger above this"),
                (0.0, "target")):
    ax.axhline(yv, color=INK2, ls="--", lw=1)
    ax.annotate(txt, (0.05, yv + 4), fontsize=8, color=INK2, zorder=5,
                bbox=dict(boxstyle="square,pad=0.1", fc=SURFACE, ec="none"))
ax.set_xlabel("time since the bulk auger halt (s), until the fine stage starts its auger")
ax.set_ylabel("cup − target (mg)")
ax.set_title("C  Powder landing with the auger stopped", loc="left",
             fontsize=10, color=INK)
ax.legend(handles=[Line2D([], [], color=COL[k], lw=2, label=v[0])
                   for k, v in DATA.items()], loc="lower right",
          frameon=False, fontsize=8)

# D: landed vs flow at the bulk halt
ax = axs[1, 1]
qmax = 0.0
for key, (label, target, done) in DATA.items():
    for r in done:
        q = fnum(r["bulk_rate_at_halt_g_per_s"])
        if r["_tail"] and q and fnum(r["bulk_halt_g"]) is not None:
            landed = r["_tail"][-1][1] + target - fnum(r["bulk_halt_g"])
            ax.plot(q, 1000 * landed, "o", ms=7, mfc=COL[key], mec=SURFACE,
                    mew=1.0, zorder=3)
            qmax = max(qmax, q)
xs = [0, qmax * 1.1]
ax.plot(xs, [1000 * TAU_S * x for x in xs], color=INK2, ls=":", lw=1)
ax.set_xlim(0, xs[1])
ax.set_ylim(0, None)
ax.set_xlabel("flow at the bulk halt (g/s)")
ax.set_ylabel("landed before the fine stage started (mg)")
ax.set_title("D  Bulk afterflow against flow at the halt", loc="left",
             fontsize=10, color=INK)
ax.legend(handles=[Line2D([], [], ls="", marker="o", ms=7, mfc=COL[k],
                          mec=SURFACE, label=v[0]) for k, v in DATA.items()]
          + [Line2D([], [], color=INK2, ls=":", lw=1,
                    label="1.07 s × flow (2026-08-07 stop-response fit)")],
          loc="upper left", frameon=False, fontsize=8)

fig.suptitle("Same stepped-tilt three-phase protocol (bulk 80 rpm with taps, "
             "60 → 40°; fine 30°, 25 rpm, 20 mg anticipation; stock tap stage)",
             fontsize=10.5, color=INK, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.97))
out = os.path.join(HERE, "three_powders.png")
fig.savefig(out, dpi=140, facecolor=SURFACE)
print("wrote", out)

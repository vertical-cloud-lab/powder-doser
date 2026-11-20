#!/usr/bin/env python3
"""AlSi10Mg (2 g) against salt (1 g) on the same stepped-tilt protocol, 2026-11-19.

Both runs used three_phase_tilt_trials.py with the same stage settings (bulk at
80 rpm with taps, plate 60 -> 40 deg; fine at 30 deg / 25 rpm with taps; stock
tap stage): salt at 1 g with script 2026-11-19d (launch 21:43 UTC, old tube),
AlSi10Mg at 2 g with 2026-11-19e (launch 22:43 UTC).

Reads both launches' ``trials_summary.csv`` and per-trial CSVs (written by
``scripts/analyze_tilt_trials.py``) and writes ``alsi10mg_vs_salt.png``:

* A: final error of every completed trial (ok / overshoot), one strip per powder
* B: dose time of every completed trial
* C: bulk flow at each plate angle (median over trials, with every trial dim)
* D: powder landed after each auger halt against the flow at the halt
  (filled = bulk halt, hollow = fine halt)

It also prints the per-angle bulk table used in the README.

usage: python plot_alsi10mg_vs_salt.py [alsi launch dir] [salt launch dir]
"""
import csv
import glob
import os
import random
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
AL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "launch1_2243Z")
SALT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    HERE, "..", "2026-11-19_salt_tilt-schedule-old-auger-80rpm", "launch1_2143Z")

# Powder identity: categorical slots 4 and 7 (validated as a pair, light mode;
# slots 1-3 already mean bulk / fine / tap in the other figures of this README)
COL = {"salt": "#eda100", "alsi10mg": "#6250d6"}
NAME = {"salt": "salt, 1 g (19d)", "alsi10mg": "AlSi10Mg, 2 g (19e)"}
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
BAND = "#ecebe7"
SURFACE = "#fcfcfb"
TAU_S = 1.07            # 2026-08-07 stop-response fit, afterflow / flow
TILTS = (60.0, 55.0, 50.0, 45.0, 40.0)


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load(launch):
    rows = list(csv.DictReader(open(os.path.join(launch, "trials_summary.csv"))))
    done = [r for r in rows if r["status"] in ("ok", "overshoot")
            and fnum(r["error_mg"]) is not None]
    return rows, done


def bulk_by_angle(launch, trials):
    """Per trial and plate angle: (g/s, g per auger rev, s at the angle)."""
    out = {a: [] for a in TILTS}
    for r in trials:
        path = os.path.join(launch, r["csv"])
        # bulk frames while the auger spins (the bulk stage also holds the
        # settle after its halt, which belongs to no angle's flow)
        frames = [f for f in csv.DictReader(open(path))
                  if f["stage"] == "bulk" and f["mass_g"] not in ("", None)
                  and float(f["auger_rpm"]) > 0]
        groups = {}
        for f in frames:
            groups.setdefault(float(f["tilt_deg"]), []).append(f)
        for a, fs in groups.items():
            if a not in out or len(fs) < 3:
                continue
            t0, t1 = float(fs[0]["t_s"]), float(fs[-1]["t_s"])
            m0, m1 = float(fs[0]["mass_g"]), float(fs[-1]["mass_g"])
            span = t1 - t0
            if span <= 0.2:
                continue
            rpm = statistics.median(float(f["auger_rpm"]) for f in fs)
            revs = rpm / 60.0 * span if rpm > 0 else None
            out[a].append(((m1 - m0) / span,
                           (m1 - m0) / revs if revs else None, span))
    return out


def main():
    data = {}
    for key, launch in (("salt", SALT), ("alsi10mg", AL)):
        rows, done = load(launch)
        data[key] = {"rows": rows, "done": done,
                     "angles": bulk_by_angle(launch, done)}

    print("bulk flow by plate angle (completed trials): median (range)")
    for key in ("salt", "alsi10mg"):
        print(" ", NAME[key])
        for a in TILTS:
            v = data[key]["angles"][a]
            if not v:
                print("    {:.0f} deg: no data".format(a))
                continue
            gps = [x[0] for x in v]
            gpr = [x[1] for x in v if x[1] is not None]
            sec = [x[2] for x in v]
            print("    {:.0f} deg: {:.0f} mg/rev ({:.0f}-{:.0f}), {:.3f} g/s, "
                  "{:.1f} s at the angle, n={}".format(
                      a, 1000 * statistics.median(gpr), 1000 * min(gpr),
                      1000 * max(gpr), statistics.median(gps),
                      statistics.median(sec), len(v)))

    plt.rcParams.update({
        "font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK,
        "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
        "axes.spines.right": False, "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    })
    fig, axs = plt.subplots(2, 2, figsize=(12.5, 9.0))
    rnd = random.Random(7)
    order = ("salt", "alsi10mg")

    # --- A: final error ----------------------------------------------------
    ax = axs[0][0]
    ax.axhspan(-1, 1, color=BAND, zorder=0)
    ax.axhline(0, color=INK2, lw=0.8, zorder=1)
    for i, key in enumerate(order):
        errs = [fnum(r["error_mg"]) for r in data[key]["done"]]
        xs = [i + rnd.uniform(-0.17, 0.17) for _ in errs]
        ax.plot(xs, errs, "o", ms=8, color=COL[key], mec=SURFACE, mew=1.5,
                zorder=3)
        med = statistics.median(errs)
        ax.plot([i - 0.3, i + 0.3], [med, med], color=INK, lw=2, zorder=4)
        n_tol = sum(1 for e in errs if abs(e) <= 1.0)
        # an even count's median can fall between the 0.1 mg readings
        mtxt = ("{:+.1f}".format(med) if abs(med * 10 - round(med * 10)) < 1e-6
                else "{:+.2f}".format(med))
        ax.text(i + 0.33, med, "median {} mg\n{} of {} within ±1 mg".format(
            mtxt, n_tol, len(errs)), va="center", ha="left", fontsize=9,
            color=INK)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([NAME[k] for k in order])
    ax.set_xlim(-0.5, len(order) - 0.5 + 0.55)
    ax.set_ylabel("final error (mg)")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_title("A  Final error of each completed trial (band: ±1 mg)",
                 loc="left", fontsize=11, color=INK)

    # --- B: dose time ------------------------------------------------------
    ax = axs[0][1]
    for i, key in enumerate(order):
        ts = [fnum(r["dose_s"]) for r in data[key]["done"]]
        tap = [(fnum(r["tap_cycles"]) or 0) > 0 for r in data[key]["done"]]
        xs = [i + rnd.uniform(-0.17, 0.17) for _ in ts]
        for x, t, tp in zip(xs, ts, tap):
            ax.plot(x, t, "o", ms=8, mec=COL[key], mew=1.6,
                    mfc=COL[key] if tp else SURFACE, zorder=3)
        med = statistics.median(ts)
        ax.plot([i - 0.3, i + 0.3], [med, med], color=INK, lw=2, zorder=4)
        ax.text(i + 0.33, med, "median {:.0f} s".format(med), va="center",
                ha="left", fontsize=9, color=INK)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([NAME[k] for k in order])
    ax.set_xlim(-0.5, len(order) - 0.5 + 0.55)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("dose time, bulk start to finish (s)")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="none", ms=8, mec=INK2, mfc=INK2,
               label="reached the tap stage"),
        Line2D([], [], marker="o", ls="none", ms=8, mec=INK2, mfc=SURFACE,
               label="ended in the fine stage")],
        frameon=False, fontsize=9, loc="upper left")
    ax.set_title("B  Dose time of each completed trial", loc="left",
                 fontsize=11, color=INK)

    # --- C: bulk flow by plate angle ---------------------------------------
    ax = axs[1][0]
    for key in order:
        ang = data[key]["angles"]
        xs, meds = [], []
        for a in TILTS:
            v = [x[0] for x in ang[a]]
            if not v:
                continue
            ax.plot([a + rnd.uniform(-0.6, 0.6) for _ in v], v, "o", ms=4,
                    color=COL[key], alpha=0.35, mew=0, zorder=2)
            xs.append(a)
            meds.append(statistics.median(v))
        ax.plot(xs, meds, "-o", color=COL[key], lw=2, ms=8, mec=SURFACE,
                mew=1.5, zorder=3, label=NAME[key] + " (median)")
        if xs:
            ax.annotate(NAME[key].split(",")[0], (xs[-1], meds[-1]),
                        xytext=(8, 0), textcoords="offset points",
                        va="center", fontsize=9, color=INK)
    ax.set_xlim(63, 36)            # the bulk runs from 60 down to 40 deg
    ax.set_ylim(bottom=0)
    ax.set_xlabel("plate angle during the bulk (deg; the bulk steps 60 → 40)")
    ax.set_ylabel("bulk flow at that angle (g/s)")
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    ax.set_title("C  Bulk flow at each plate angle (80 rpm, taps on)",
                 loc="left", fontsize=11, color=INK)

    # --- D: afterflow vs flow at the halt ----------------------------------
    ax = axs[1][1]
    xmax = 0.0
    for key in order:
        for stage, filled in (("bulk", True), ("fine", False)):
            xs, ys = [], []
            for r in data[key]["done"]:
                x = fnum(r[stage + "_rate_at_halt_g_per_s"])
                y = fnum(r[stage + "_afterflow_mg"])
                if x is None or y is None:
                    continue
                xs.append(x)
                ys.append(y)
            xmax = max([xmax] + xs)
            ax.plot(xs, ys, "o", ms=8, mec=COL[key], mew=1.6,
                    mfc=COL[key] if filled else SURFACE, ls="none", zorder=3)
    xl = [0, xmax * 1.08]
    ax.plot(xl, [TAU_S * 1000 * x for x in xl], ":", color=INK2, lw=1.4,
            zorder=2)
    ax.text(xl[1], TAU_S * 1000 * xl[1], "1.07 s × flow\n(salt, 2026-08-07)",
            ha="right", va="bottom", fontsize=9, color=INK2)
    ax.set_xlim(0, xl[1])
    ax.set_ylim(bottom=0)
    ax.set_xlabel("flow rate at the halt (g/s)")
    ax.set_ylabel("powder landed after the halt (mg)")
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="none", ms=8, mec=COL["salt"],
               mfc=COL["salt"], label=NAME["salt"]),
        Line2D([], [], marker="o", ls="none", ms=8, mec=COL["alsi10mg"],
               mfc=COL["alsi10mg"], label=NAME["alsi10mg"]),
        Line2D([], [], marker="o", ls="none", ms=8, mec=INK2, mfc=INK2,
               label="bulk halt (80 rpm, 40°)"),
        Line2D([], [], marker="o", ls="none", ms=8, mec=INK2, mfc=SURFACE,
               label="fine halt (25 rpm, 30°)")],
        frameon=False, fontsize=9, loc="upper left")
    ax.set_title("D  Afterflow at each halt", loc="left", fontsize=11,
                 color=INK)

    fig.tight_layout()
    out = os.path.join(HERE, "alsi10mg_vs_salt.png")
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    main()

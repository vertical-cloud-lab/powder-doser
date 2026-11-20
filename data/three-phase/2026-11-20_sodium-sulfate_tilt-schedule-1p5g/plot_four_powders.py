#!/usr/bin/env python3
"""Sodium sulfate (1.5 g) against calcium lactate (2 g), AlSi10Mg (2 g) and salt (1 g) on the same stepped-tilt protocol.

All four runs used three_phase_tilt_trials.py with the same stage settings
(bulk at 80 rpm with taps, plate 60 -> 40 deg, hand-off at 0.25 g to go;
fine at 30 deg / 25 rpm with taps, 20 mg anticipation, hand-off at 25 mg to
go; stock tap stage):

* sodium sulfate, 1.5 g, script 2026-11-20d, launch 18:04 UTC (this folder)
* calcium lactate, 2 g, script 2026-11-20b, launch 2026-11-20 03:05 UTC
* AlSi10Mg, 2 g, scripts 2026-11-19e and 2026-11-20a (launches 22:43 and 02:08)
* salt, 1 g, script 2026-11-19d (launch 2026-11-19 21:43, old tube)

(Barium chloride, 2026-11-20c, never came out of its tube, so it has no
completed trials to plot.)

Reads each launch's ``trials_summary.csv`` and per-trial CSVs (written by
``scripts/analyze_tilt_trials.py``) and writes ``four_powders.png``:

* A: final error of every completed trial, one strip per powder.  Filled
  circles reached the tap stage, hollow circles ended in the fine stage,
  hollow squares ended in the bulk (the cup was already past the target
  when the bulk handed over).
* B: sodium sulfate's final error in run order, same marks.
* C: the cup (minus the target) from each bulk halt until the fine stage
  starts its auger -- or, in trials where no later stage turned the auger,
  until 3 s after the halt -- i.e. powder landing with the auger stopped.
  Dotted: the bulk's 800 ms settle.  Dashed: the fine stage's halt
  threshold (45 mg to go) and the target.
* D: powder landed in that window against the flow at the halt.  Dotted
  line: afterflow = 1.07 s x flow (2026-08-07 stop response).

and ``sodium_sulfate_afterflow.png``: sodium sulfate's cup for 4 s after
each bulk halt, lighter for earlier trials; and per trial, the cup at the
controller's own read (800 ms after the halt) against the final reading.

It also prints the per-powder numbers and sodium sulfate's bulk flow by
plate angle, as quoted in the README.

usage: python plot_four_powders.py
"""
import csv
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TP = os.path.join(HERE, "..")
RUNS = [  # (key, label, target g, launch folders)
    ("salt", "salt, 1 g", 1.0,
     [os.path.join(TP, "2026-11-19_salt_tilt-schedule-old-auger-80rpm", "launch1_2143Z")]),
    ("alsi10mg", "AlSi10Mg, 2 g", 2.0,
     [os.path.join(TP, "2026-11-19_alsi10mg_tilt-schedule-2g", "launch1_2243Z"),
      os.path.join(TP, "2026-11-19_alsi10mg_tilt-schedule-2g", "launch2_0208Z")]),
    ("calcium-lactate", "calcium lactate, 2 g", 2.0,
     [os.path.join(TP, "2026-11-20_calcium-lactate_tilt-schedule-2g", "launch1_0305Z")]),
    ("sodium-sulfate", "sodium sulfate, 1.5 g", 1.5,
     [os.path.join(HERE, "launch1_1804Z")]),
]
# Powder identity: categorical slots 4, 7, 5 and 6 (validated as a set, light
# mode, all pairs).  Salt, AlSi10Mg and calcium lactate keep the colours of
# plot_three_powders.py; slots 1-3 mean bulk / fine / tap in the other figures.
COL = {"salt": "#eda100", "alsi10mg": "#6250d6", "calcium-lactate": "#e87ba4",
       "sodium-sulfate": "#008300"}
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
BAND = "#ecebe7"
SURFACE = "#fcfcfb"
TAU_S = 1.07
BULK_SETTLE_S = 0.8
FINE_HALT_TO_GO_G = 0.045
NO_FINE_WINDOW_S = 3.0
TILTS = (60.0, 55.0, 50.0, 45.0, 40.0)


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
    """Frames from the bulk halt to the fine stage's auger start.

    If no later stage turned the auger (the dose ended in the bulk), the
    window is NO_FINE_WINDOW_S after the halt instead.  Returns
    (points, ended_by) with ended_by "fine" or "window".
    """
    rows = list(csv.DictReader(open(path)))
    t_halt = t_run = None
    for r in rows:
        ev = r["events"] or ""
        if t_halt is None and r["stage"] == "bulk" and "auger halt" in ev:
            t_halt = float(r["t_s"])
        elif (t_halt is not None and r["stage"] in ("fine", "tap")
              and ("auger run" in ev or "auger rotate" in ev)):
            t_run = float(r["t_s"])
            break
    if t_halt is None:
        return None, None
    ended_by = "fine"
    if t_run is None:
        t_run = t_halt + NO_FINE_WINDOW_S
        ended_by = "window"
    pts = [(float(r["t_s"]) - t_halt, float(r["mass_g"]) - target)
           for r in rows
           if r["mass_g"] not in ("", None)
           and t_halt <= float(r["t_s"]) <= t_run]
    return pts, ended_by


def ended_in(r):
    if fnum(r["tap_cycles"]):
        return "tap"
    if fnum(r["fine_s"]):
        return "fine"
    return "bulk"


def bulk_by_angle(trials):
    """Per trial and plate angle: (g/s, g per auger rev, s at the angle)."""
    out = {a: [] for a in TILTS}
    for r in trials:
        frames = [f for f in csv.DictReader(open(r["_csv"]))
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


DATA = {}
for key, label, target, folders in RUNS:
    trials = []
    for f in folders:
        trials += load(f)
    done = [r for r in trials if r["status"] in ("ok", "overshoot")]
    for r in done:
        r["_end"] = ended_in(r)
        r["_tail"], r["_tail_end"] = tail(r["_csv"], target)
    DATA[key] = (label, target, done)

# ---- printed numbers -------------------------------------------------------
for key, (label, target, done) in DATA.items():
    errs = [fnum(r["error_mg"]) for r in done]
    inside = sum(1 for e in errs if abs(e) <= 1.0)
    within5 = sum(1 for e in errs if abs(e) <= 5.0)
    by_end = {k: [r for r in done if r["_end"] == k] for k in ("bulk", "fine", "tap")}
    land = []
    for r in done:
        if r["_tail"] and fnum(r["bulk_halt_g"]) is not None:
            land.append((r["_tail"][-1][1] + target - fnum(r["bulk_halt_g"]),
                         fnum(r["bulk_rate_at_halt_g_per_s"])))
    taus = [a / q for a, q in land if q]
    print("{}: {} completed, {} within +/-1 mg, {} within +/-5 mg, median error "
          "{:+.1f} mg (range {:+.1f} to {:+.1f}); ended in bulk/fine/tap: "
          "{}/{}/{}; median dose {:.1f} s ({:.1f}-{:.1f})".format(
              label, len(done), inside, within5, statistics.median(errs),
              min(errs), max(errs), len(by_end["bulk"]), len(by_end["fine"]),
              len(by_end["tap"]),
              statistics.median([fnum(r["dose_s"]) for r in done]),
              min(fnum(r["dose_s"]) for r in done),
              max(fnum(r["dose_s"]) for r in done)))
    for k, rs in by_end.items():
        if rs:
            e = [fnum(r["error_mg"]) for r in rs]
            print("   ended in {}: {} trials, error median {:+.1f} mg "
                  "({:+.1f} to {:+.1f})".format(k, len(rs), statistics.median(e),
                                                min(e), max(e)))
    if land:
        print("   landed after the bulk halt (to the fine auger start or +{:.0f} s): "
              "median {:.0f} mg ({:.0f}-{:.0f}); flow at halt {:.3f}-{:.3f} g/s "
              "(median {:.3f}); landed/flow median {:.2f} s ({:.2f}-{:.2f})".format(
                  NO_FINE_WINDOW_S,
                  1000 * statistics.median(a for a, _ in land),
                  1000 * min(a for a, _ in land), 1000 * max(a for a, _ in land),
                  min(q for _, q in land), max(q for _, q in land),
                  statistics.median(q for _, q in land),
                  statistics.median(taus), min(taus), max(taus)))
    halts = [fnum(r["bulk_halt_g"]) for r in done if fnum(r["bulk_halt_g"]) is not None]
    if halts:
        print("   bulk halt read: median {:.4f} g ({:.4f}-{:.4f}), i.e. {:.0f}-{:.0f} mg "
              "to go".format(statistics.median(halts), min(halts), max(halts),
                             1000 * (target - max(halts)), 1000 * (target - min(halts))))
    bs = [fnum(r["bulk_s"]) for r in done if fnum(r["bulk_s"]) is not None]
    revs = [fnum(r["auger_rev"]) for r in done]
    print("   bulk {:.1f}-{:.1f} s (median {:.1f}); auger revs per dose: median "
          "{:.1f} ({:.1f}-{:.1f}); mg per rev {:.0f}".format(
              min(bs), max(bs), statistics.median(bs), statistics.median(revs),
              min(revs), max(revs), 1000 * target / statistics.median(revs)))

print("\nsodium sulfate bulk flow by plate angle (completed trials): median (range)")
ss_angles = bulk_by_angle(DATA["sodium-sulfate"][2])
for a in TILTS:
    v = ss_angles[a]
    if not v:
        print("  {:.0f} deg: no data".format(a))
        continue
    gps = [x[0] for x in v]
    gpr = [x[1] for x in v if x[1] is not None]
    sec = [x[2] for x in v]
    print("  {:.0f} deg: {:.0f} mg/rev ({:.0f}-{:.0f}), {:.3f} g/s, {:.1f} s at the "
          "angle (n={})".format(a, 1000 * statistics.median(gpr), 1000 * min(gpr),
                                1000 * max(gpr), statistics.median(gps),
                                statistics.median(sec), len(v)))

# ---- figure ----------------------------------------------------------------
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2})
fig, axs = plt.subplots(2, 2, figsize=(12.0, 8.4), facecolor=SURFACE)
for ax in axs.flat:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def mark(ax, x, y, key, end):
    if end == "tap":
        ax.plot(x, y, "o", ms=7, mfc=COL[key], mec=COL[key], mew=1.6, zorder=3)
    elif end == "fine":
        ax.plot(x, y, "o", ms=7, mfc=SURFACE, mec=COL[key], mew=1.6, zorder=3)
    else:
        ax.plot(x, y, "s", ms=6.5, mfc=SURFACE, mec=COL[key], mew=1.6, zorder=3)


# A: final error strips
ax = axs[0, 0]
ax.axhspan(-1, 1, color=BAND, zorder=0)
for i, (key, (label, target, done)) in enumerate(DATA.items()):
    n = len(done)
    for j, r in enumerate(sorted(done, key=lambda r: fnum(r["error_mg"]))):
        dx = (j - (n - 1) / 2) / max(n, 1) * 0.5
        mark(ax, i + dx, fnum(r["error_mg"]), key, r["_end"])
    med = statistics.median(fnum(r["error_mg"]) for r in done)
    ax.plot([i - 0.32, i + 0.32], [med, med], color=INK, lw=2, zorder=4)
ax.set_xticks(range(len(DATA)))
ax.set_xticklabels(["{}\nmedian {:+.1f} mg".format(
    v[0].replace(", ", "\n"), statistics.median(fnum(r["error_mg"]) for r in v[2]))
    for v in DATA.values()], fontsize=8.5)
ax.set_xlim(-0.6, len(DATA) - 0.4)
ax.set_ylabel("final error (mg)")
ax.set_title("A  Final error, every completed trial", loc="left",
             fontsize=10, color=INK)
ax.legend(handles=[
    Line2D([], [], ls="", marker="o", ms=7, mfc=INK2, mec=INK2,
           label="reached the tap stage"),
    Line2D([], [], ls="", marker="o", ms=7, mfc=SURFACE, mec=INK2, mew=1.6,
           label="ended in the fine stage"),
    Line2D([], [], ls="", marker="s", ms=6.5, mfc=SURFACE, mec=INK2, mew=1.6,
           label="ended in the bulk"),
    Line2D([], [], color=INK, lw=2, label="median"),
    plt.Rectangle((0, 0), 1, 1, color=BAND, label="±1 mg tolerance")],
    loc="upper left", frameon=False, fontsize=8)

# B: sodium sulfate in run order
ax = axs[0, 1]
ax.axhspan(-1, 1, color=BAND, zorder=0)
label, target, done = DATA["sodium-sulfate"]
for r in done:
    mark(ax, int(r["trial"]), fnum(r["error_mg"]), "sodium-sulfate", r["_end"])
ax.axhline(0, color=INK2, lw=0.8)
ax.set_xticks(range(1, int(max(int(r["trial"]) for r in done)) + 1))
ax.tick_params(axis="x", labelsize=7.5)
ax.set_xlabel("trial")
ax.set_ylabel("final error (mg)")
ax.set_title("B  Sodium sulfate in run order (squares: ended in the bulk)",
             loc="left", fontsize=10, color=INK)

# C: landing after the bulk halt
ax = axs[1, 0]
for key, (label, target, done) in DATA.items():
    for r in done:
        if r["_tail"]:
            xs, ys = zip(*r["_tail"])
            ax.plot(xs, [1000 * y for y in ys], color=COL[key], lw=1.1,
                    alpha=0.75)
ax.axvline(BULK_SETTLE_S, color=INK2, ls=":", lw=1)
ax.annotate("bulk settle (800 ms)", (BULK_SETTLE_S + 0.05, 268), fontsize=8,
            color=INK2)
for yv, txt in ((-1000 * FINE_HALT_TO_GO_G, "fine stage halts its auger above this"),
                (0.0, "target")):
    ax.axhline(yv, color=INK2, ls="--", lw=1)
    ax.annotate(txt, (0.03, yv + 4), fontsize=8, color=INK2, zorder=5,
                bbox=dict(boxstyle="square,pad=0.1", fc=SURFACE, ec="none"))
ax.set_ylim(-345, 290)
ax.set_xlabel("time since the bulk auger halt (s), until the fine stage starts "
              "its auger (or 3 s)")
ax.set_ylabel("cup − target (mg)")
ax.set_title("C  Powder landing with the auger stopped", loc="left",
             fontsize=10, color=INK)
ax.legend(handles=[Line2D([], [], color=COL[k], lw=2, label=v[0])
                   for k, v in DATA.items()], loc="lower left",
          frameon=False, fontsize=8, ncol=2)

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
ax.set_ylabel("landed after the halt, auger stopped (mg)")
ax.set_title("D  Bulk afterflow against flow at the halt", loc="left",
             fontsize=10, color=INK)
ax.legend(handles=[Line2D([], [], ls="", marker="o", ms=7, mfc=COL[k],
                          mec=SURFACE, label=v[0]) for k, v in DATA.items()]
          + [Line2D([], [], color=INK2, ls=":", lw=1,
                    label="1.07 s × flow (2026-08-07 stop-response fit)")],
          loc="upper left", frameon=False, fontsize=8)

fig.suptitle("Same stepped-tilt three-phase protocol (bulk 80 rpm with taps, "
             "60 → 40°, hand-off at 0.25 g to go; fine 30°, 25 rpm, 20 mg "
             "anticipation; stock tap stage)",
             fontsize=10.5, color=INK, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.97))
out = os.path.join(HERE, "four_powders.png")
fig.savefig(out, dpi=140, facecolor=SURFACE)
print("wrote", out)

# ---- sodium sulfate: the afterflow trial by trial ----------------------------
label, target, done = DATA["sodium-sulfate"]
print("\nsodium sulfate, per trial: landed by the controller's read (800 ms "
      "settle) and after it (final - that read)")
late = []
for r in done:
    h, s8, fin = (fnum(r["bulk_halt_g"]), fnum(r["bulk_settled_g"]),
                  fnum(r["final_g"]))
    late.append((int(r["trial"]), 1000 * (s8 - h), 1000 * (fin - s8)))
    print("  trial {:2d}: halt {:.4f} g, read {:.4f} g, final {:.4f} g: "
          "{:.0f} mg by the read, {:+.0f} mg after it".format(
              int(r["trial"]), h, s8, fin, 1000 * (s8 - h), 1000 * (fin - s8)))
for lo, hi in ((1, 9), (10, 23)):
    sel = [x for x in late if lo <= x[0] <= hi]
    errs = [fnum(r["error_mg"]) for r in done if lo <= int(r["trial"]) <= hi]
    if sel:
        print("  trials {}-{}: error median {:+.1f} mg; after the read: median "
              "{:+.0f} mg, {} of {} over +10 mg".format(
                  lo, hi, statistics.median(errs),
                  statistics.median(x[2] for x in sel),
                  sum(1 for x in sel if x[2] > 10), len(sel)))

GREENS = plt.get_cmap("Greens")
fig2, (bx, cx) = plt.subplots(1, 2, figsize=(12.0, 4.6), facecolor=SURFACE,
                              gridspec_kw={"width_ratios": [1.0, 1.15]})
for ax in (bx, cx):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
n_last = max(int(r["trial"]) for r in done)
for r in done:
    pts, _ = tail(r["_csv"], target)
    rows = list(csv.DictReader(open(r["_csv"])))
    t_halt = next(float(f["t_s"]) for f in rows
                  if f["stage"] == "bulk" and "auger halt" in (f["events"] or ""))
    pts = [(float(f["t_s"]) - t_halt, 1000 * (float(f["mass_g"]) - target))
           for f in rows if f["mass_g"] not in ("", None)
           and t_halt <= float(f["t_s"]) <= t_halt + 4.0]
    xs, ys = zip(*pts)
    k = (int(r["trial"]) - 1) / max(1, n_last - 1)
    bx.plot(xs, ys, color=GREENS(0.35 + 0.6 * k), lw=1.2)
bx.axvline(BULK_SETTLE_S, color=INK2, ls=":", lw=1)
bx.annotate("controller reads the cup\n(800 ms settle)", (BULK_SETTLE_S + 0.05, -235),
            fontsize=8, color=INK2)
bx.axhline(0, color=INK2, ls="--", lw=1)
bx.annotate("target", (3.55, 6), fontsize=8, color=INK2)
bx.set_xlim(0, 4.0)
bx.set_xlabel("time since the bulk auger halt (s)")
bx.set_ylabel("cup − target (mg)")
bx.set_title("Sodium sulfate after each bulk halt (lighter: earlier trials)",
             loc="left", fontsize=10, color=INK)
bx.legend(handles=[Line2D([], [], color=GREENS(0.35), lw=2, label="trial 1"),
                   Line2D([], [], color=GREENS(0.65), lw=2,
                          label="trial {}".format((n_last + 1) // 2)),
                   Line2D([], [], color=GREENS(0.95), lw=2,
                          label="trial {}".format(n_last))],
          loc="lower right", frameon=False, fontsize=8)
for r in done:
    t = int(r["trial"])
    s8 = 1000 * (fnum(r["bulk_settled_g"]) - target)
    fe = fnum(r["error_mg"])
    cx.plot([t, t], [s8, fe], color=INK2, lw=1.2, zorder=2)
    cx.plot(t, s8, "o", ms=7, mfc=SURFACE, mec=COL["sodium-sulfate"], mew=1.6,
            zorder=3)
    cx.plot(t, fe, "o", ms=7, mfc=COL["sodium-sulfate"], mec=SURFACE, mew=1.0,
            zorder=4)
cx.axhline(0, color=INK2, ls="--", lw=1)
cx.set_xticks(range(1, n_last + 1))
cx.tick_params(axis="x", labelsize=7.5)
cx.set_xlabel("trial")
cx.set_ylabel("cup − target (mg)")
cx.set_title("What the controller read, and where the cup ended", loc="left",
             fontsize=10, color=INK)
cx.legend(handles=[
    Line2D([], [], ls="", marker="o", ms=7, mfc=SURFACE,
           mec=COL["sodium-sulfate"], mew=1.6,
           label="controller's read, 800 ms after the halt"),
    Line2D([], [], ls="", marker="o", ms=7, mfc=COL["sodium-sulfate"],
           mec=SURFACE, label="final (8 s later, median of 8 reads)"),
    Line2D([], [], color=INK2, lw=1.2, label="landed after the read")],
    loc="upper left", frameon=False, fontsize=8)
fig2.tight_layout()
out2 = os.path.join(HERE, "sodium_sulfate_afterflow.png")
fig2.savefig(out2, dpi=140, facecolor=SURFACE)
print("wrote", out2)

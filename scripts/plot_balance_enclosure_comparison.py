"""Compare balance noise with the breeze break removed vs the enclosure closed.

Usage: python scripts/plot_balance_enclosure_comparison.py  (from the repo root)

Reads the 2026-08-19 captures under ``docs/rig-checks/data/`` -- two 75 s
windows taken with the top of the breeze break removed and the sash open,
three 75 s windows plus one 8.4 min continuous record taken with the
enclosure replaced and the sash closed -- and writes
``docs/rig-checks/frames/2026-08-19_balance-enclosure-comparison.png``.
"""

import csv
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; MUTED = "#8a8983"
BEFORE = ("#eb6834", "#b8410f")                    # shield removed
AFTER = ("#2a78d6", "#1f9d6b", "#7a4fd4")          # enclosure closed
DATA = "docs/rig-checks/data/"


def load(path):
    t, g = [], []
    with open(DATA + path) as f:
        for row in csv.DictReader(f):
            if row["status"] in ("ST", "US") and row["grams"]:
                t.append(int(row["t_ms"]) / 1000.0)
                g.append(float(row["grams"]))
    return t, g


before = [load("2026-08-19_balance-draft-noise-window%d.csv" % i)
          for i in (1, 2)]
after = [load("2026-08-19_balance-enclosed-noise-window%d.csv" % i)
         for i in (1, 2, 3)]
longrec = load("2026-08-19_balance-enclosed-drift-8min.csv")

fig, axes = plt.subplots(2, 2, figsize=(12.2, 7.6))
fig.patch.set_facecolor(SURFACE)
(ax, bx), (cx, dx) = axes

YLIM = (-22.5, 22.5)


def traces(a, runs, colours, labels, title, subtitle):
    for (t, g), colour, label in zip(runs, colours, labels):
        med = st.median(g)
        a.plot(t, [(x - med) * 1000 for x in g], color=colour, lw=1.9,
               solid_capstyle="round")
        a.annotate(label, (t[-1], (g[-1] - med) * 1000), xytext=(6, 0),
                   textcoords="offset points", va="center",
                   color=colour, fontsize=8.5)
    a.axhspan(-5, 5, color=MUTED, alpha=0.16, lw=0, zorder=0)
    a.axhline(0, color=MUTED, lw=1, zorder=1)
    a.set_xlim(0, 92)
    a.set_ylim(*YLIM)
    a.set_xlabel("time (s)", color=INK2, fontsize=9.5)
    a.set_ylabel("deviation from window median (mg)", color=INK2, fontsize=9.5)
    a.set_title(title + "\n" + subtitle, color=INK, fontsize=11,
                loc="left", pad=10)


traces(ax, before, BEFORE, ["window 1", "window 2"],
       "A  Breeze break removed, sash open",
       "the reading wanders far outside the ±5 mg dose band")
traces(bx, after, AFTER, ["window 1", "window 2", "window 3"],
       "B  Enclosure replaced, sash closed — same axes",
       "every window now fits inside the band with room to spare")
ax.annotate("shaded band = ±5 mg, the block G dose tolerance",
            (90, -20.4), color=INK2, fontsize=8.5, ha="right", va="center")

# --- Panel C: the residual, on a longer baseline ------------------------
t, g = longrec
med = st.median(g)
cx.plot([x / 60 for x in t], [(v - med) * 1000 for v in g],
        color=AFTER[0], lw=1.6, solid_capstyle="round")
cx.axhspan(-5, 5, color=MUTED, alpha=0.16, lw=0, zorder=0)
cx.axhline(0, color=MUTED, lw=1, zorder=1)
cx.set_xlim(0, 8.6)
cx.set_ylim(-9, 9)
cx.set_xlabel("time (min)", color=INK2, fontsize=9.5)
cx.set_ylabel("deviation from record median (mg)", color=INK2, fontsize=9.5)
cx.set_title("C  What is left: a slow baseline wander\n"
             "8.4 min continuous, 11.6 mg peak-to-peak end to end",
             color=INK, fontsize=11, loc="left", pad=10)
cx.annotate("≤4.2 mg inside any 60 s window,\n≤7.4 mg inside any 180 s",
            (0.25, -6.6), color=INK2, fontsize=8.5, va="center")

# --- Panel D: scatter magnitude, before vs after ------------------------
rows = [
    ("prior valid battery runs\n(block A deltas)", 0.1, MUTED),
    ("enclosed w3", 0.42, AFTER[2]),
    ("enclosed w2", 0.51, AFTER[1]),
    ("enclosed w1", 0.93, AFTER[0]),
    ("shield off w2", 5.15, BEFORE[0]),
    ("shield off w1", 8.92, BEFORE[1]),
]
ys = list(range(len(rows)))
dx.barh(ys, [r[1] for r in rows], color=[r[2] for r in rows], height=0.55,
        zorder=3)
dx.set_yticks(ys, [r[0] for r in rows], color=INK2, fontsize=8.5)
dx.set_xscale("log")
dx.set_xlim(0.05, 30)
for y, (_, v, _) in zip(ys, rows):
    dx.annotate(("≤0.1" if v == 0.1 else "%.2f" % v) + " mg", (v, y),
                xytext=(7, 0), textcoords="offset points", va="center",
                color=INK2, fontsize=9, zorder=4)
for xval, lab, style, yy, ha, off in (
        (0.1, "0.1 mg — spec repeatability", ":", 6.2, "left", 5),
        (5.0, "5 mg — dose tolerance", "--", 5.8, "right", -5)):
    dx.axvline(xval, color=MUTED, lw=1.2, ls=style, zorder=2)
    dx.annotate(lab, (xval, yy), xytext=(off, 0), textcoords="offset points",
                color=INK2, fontsize=8.5, va="center", ha=ha)
dx.set_xticks([0.1, 1, 10])
dx.xaxis.set_major_formatter(
    matplotlib.ticker.FuncFormatter(lambda v, _: "%g" % v))
dx.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
dx.set_xlabel("within-window scatter, drift removed "
              "(standard deviation, mg, log scale)", color=INK2, fontsize=9.5)
dx.set_title("D  Short-term scatter is 6–20× better\n"
             "and back within a factor of ~5 of spec",
             color=INK, fontsize=11, loc="left", pad=10)
dx.set_ylim(-0.65, 6.45)

for a in (ax, bx, cx, dx):
    a.set_facecolor(SURFACE)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        a.spines[s].set_color(MUTED)
        a.spines[s].set_linewidth(0.9)
    a.tick_params(colors=INK2, labelsize=9, length=3)
    a.grid(axis="x" if a is dx else "y", color=MUTED, alpha=0.22, lw=0.8)
    a.set_axisbelow(True)

fig.suptitle("A&D HR-100A in the fume hood — 2026-08-19, empty vessel, no "
             "actuation\nbreeze break removed / sash open (14:00 MDT)  vs  "
             "enclosure replaced / sash closed (15:46–16:17 MDT)",
             color=INK, fontsize=11.5, x=0.006, ha="left", y=0.997,
             va="top", linespacing=1.5)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig("docs/rig-checks/frames/2026-08-19_balance-enclosure-comparison.png",
            dpi=165, facecolor=SURFACE)
print("ok")

"""Render the 2026-08-19 breeze-break-removed balance noise diagnostic.

Usage: python scripts/plot_balance_draft_noise.py  (run from the repo root)
Reads the two 75 s captures under docs/rig-checks/data/ and writes
docs/rig-checks/frames/2026-08-19_balance-draft-noise.png.
"""

import csv, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; MUTED = "#8a8983"
S1 = "#2a78d6"; S2 = "#eb6834"

def load(p):
    t, g = [], []
    with open(p) as f:
        for row in csv.DictReader(f):
            if row["status"] in ("ST", "US"):
                t.append(int(row["t_ms"]) / 1000.0)
                g.append(float(row["grams"]))
    return t, g

w1 = load("docs/rig-checks/data/2026-08-19_balance-draft-noise-window1.csv")
w2 = load("docs/rig-checks/data/2026-08-19_balance-draft-noise-window2.csv")

fig, (ax, bx) = plt.subplots(
    1, 2, figsize=(11.6, 4.3), gridspec_kw={"width_ratios": [1.75, 1]})
fig.patch.set_facecolor(SURFACE)

# --- Panel A: deviation traces -------------------------------------------
for (t, g), colour, label in ((w1, S1, "window 1"), (w2, S2, "window 2")):
    med = st.median(g)
    dev = [(x - med) * 1000 for x in g]
    ax.plot(t, dev, color=colour, lw=2, solid_capstyle="round", label=label)
    ax.annotate(label, (t[-1], dev[-1]), xytext=(6, 0),
                textcoords="offset points", va="center",
                color=INK2, fontsize=9)

ax.axhspan(-5, 5, color=MUTED, alpha=0.16, lw=0, zorder=0)
ax.annotate("shaded band = ±5 mg, the block G dose tolerance", (85, -20.2),
            color=INK2, fontsize=9, ha="right", va="center")
ax.axhline(0, color=MUTED, lw=1, zorder=1)
ax.set_xlabel("time (s)", color=INK2, fontsize=9.5)
ax.set_ylabel("deviation from window median (mg)", color=INK2, fontsize=9.5)
ax.set_title("A  Empty vessel, no actuation — the reading wanders\n"
             "far outside the dose tolerance band",
             color=INK, fontsize=11, loc="left", pad=10)
ax.set_xlim(0, 86)
ax.set_ylim(-22.5, 20)

# --- Panel B: noise magnitude vs the two thresholds ----------------------
rows = [
    ("prior valid runs\n(shield on, block A)", 0.1, MUTED),
    ("window 2\n(shield off)", 5.15, S2),
    ("window 1\n(shield off)", 8.92, S1),
]
ys = range(len(rows))
bx.barh(list(ys), [r[1] for r in rows], color=[r[2] for r in rows],
        height=0.5, zorder=3)
bx.set_yticks(list(ys), [r[0] for r in rows], color=INK2, fontsize=9)
bx.set_xscale("log")
bx.set_xlim(0.05, 26)
for y, (_, v, _) in zip(ys, rows):
    txt = "≤0.1" if v == 0.1 else f"{v:.2f}"
    bx.annotate(txt + " mg", (v, y), xytext=(7, 0),
                textcoords="offset points", va="center",
                color=INK2, fontsize=9.5, zorder=4)
for xval, lab, style, yy, ha, dx in (
        (0.1, "0.1 mg — spec repeatability", ":", -0.35, "left", 5),
        (5.0, "5 mg — dose tolerance", "--", 3.3, "right", -5)):
    bx.axvline(xval, color=MUTED, lw=1.2, ls=style, zorder=2)
    bx.annotate(lab, (xval, yy), xytext=(dx, 0), textcoords="offset points",
                color=INK2, fontsize=8.5, va="center", ha=ha)
bx.set_xticks([0.1, 1, 10])
bx.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
    lambda v, _: ("%g" % v)))
bx.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
bx.set_xlabel("standard deviation of the reading (mg, log scale)",
              color=INK2, fontsize=9.5)
bx.set_title("B  50–90× worse than the balance's\nown repeatability spec",
             color=INK, fontsize=11, loc="left", pad=10)
bx.set_ylim(-0.6, 3.45)

for a in (ax, bx):
    a.set_facecolor(SURFACE)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        a.spines[s].set_color(MUTED); a.spines[s].set_linewidth(0.9)
    a.tick_params(colors=INK2, labelsize=9, length=3)
    a.grid(axis="x" if a is bx else "y", color=MUTED, alpha=0.22, lw=0.8)
    a.set_axisbelow(True)

fig.suptitle("A&D HR-100A with the breeze break removed, fume hood running "
             "— 2026-08-19, empty vessel (62.15 g), no actuation",
             color=INK, fontsize=12, x=0.007, ha="left", y=0.995)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig("docs/rig-checks/frames/2026-08-19_balance-draft-noise.png",
            dpi=170, facecolor=SURFACE)
print("ok")

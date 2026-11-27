#!/usr/bin/env python3
"""Flow probe by plate angle: the old tube (2026-11-18 06:53 UTC) vs the new
tube (2026-11-19 19:52 UTC).  Each bar is the mass gained by 2.75 auger revs
at 55 rpm (3.0 s), in the order the probe ran them.  Both probes followed a
priming spin at 0 deg.

The old-tube values are the ones in ../2026-11-18_salt_tilt-schedule/README.md
(timeline, 06:53 row); the new-tube values come from the STEP lines of
launch2_1953Z/session_launch2.log.

usage: python plot_probe_comparison.py   (run from this folder)
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LABELS = ["55°", "50°", "45°", "40°", "35°", "30°", "60°\n1st", "60°\n2nd"]
OLD_MG = [42, 26, 60, 103, 93, 90, 112, -11]
BLUE, ORANGE = "#2a78d6", "#eb6834"          # categorical slots 1, 2
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

new_mg = []
for raw in open("launch2_1953Z/session_launch2.log", encoding="utf-8"):
    if "\tSTEP," in raw:
        s = json.loads(raw.split("\tSTEP,", 1)[1])
        new_mg.append(round(1000.0 * s["gain_g"], 1))
assert len(new_mg) == len(OLD_MG), new_mg

fig, ax = plt.subplots(figsize=(9.0, 4.6), dpi=150)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
x = list(range(len(LABELS)))
w = 0.36
ax.bar([i - w / 2 - 0.01 for i in x], OLD_MG, width=w, color=BLUE,
       label="old tube, 2026-11-18 06:53 UTC")
ax.bar([i + w / 2 + 0.01 for i in x], new_mg, width=w, color=ORANGE,
       label="new tube, 2026-11-19 19:52 UTC")
for i, v in enumerate(new_mg):
    ax.text(i + w / 2 + 0.01, max(v, 0) + 2.5, "{:.0f}".format(v),
            ha="center", va="bottom", fontsize=8, color=INK2)
ax.axhline(0, color=INK2, lw=0.8)
ax.set_xticks(x)
ax.set_xticklabels(LABELS, color=INK2)
ax.set_ylabel("salt per 2.75 revs at 55 rpm (mg)", color=INK2)
ax.set_xlabel("plate angle, in the order the probe ran", color=INK2)
ax.set_title("Flow probe after a 0° priming spin: {:.0f} mg in total from the new tube, "
             "{:.0f} mg from the old one".format(sum(new_mg), sum(OLD_MG)),
             loc="left", fontsize=11, color=INK)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color("#c9c8c3")
ax.tick_params(colors=INK2)
ax.legend(frameon=False, loc="upper left", fontsize=9, labelcolor=INK2)
fig.tight_layout()
fig.savefig("probe_old_vs_new_tube.png", facecolor=SURFACE)
print("new tube mg:", new_mg)

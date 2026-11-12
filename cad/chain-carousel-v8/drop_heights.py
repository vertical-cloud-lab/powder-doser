"""Auger-to-beaker height: the lab's single doser, chain carousel v7 and v8, side views to scale (Sam, PR #185, 2026-11-12:
"Provide a comparison between the auger-to-beaker height for the current powder doser and for v7").

    python drop_heights.py   -> renders/v8/drop_heights.png, checks/drop_heights.json

v7 and v8 are their CAD's numbers (params, layout). The single doser has no CAD of its stand or balance, so its numbers are built
from: Sam's measurement on the HR-100A (pan to the underside of its draft cage: 3.125 in, issue #144), the 100 mL Griffin beaker
it doses into (50 x 70 mm, issue #144), the HR-100A's pan height (A&D's manual, 86.5 mm) and the exit's height over that beaker in
the Aug 4 photos (issue #116), scaled off the beaker's 50 mm rim: about 85 mm, +-15. PR #170's CAD gives the doser's exit 37.5
mm over its board at 30 deg of tilt (hinge 43.25 mm up, outlet 11.6 mm ahead of it), which is consistent with the board standing
just over the cage.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

HERE = Path(__file__).resolve().parent
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
SURF = "#fcfcfb"
ACC = "#2a78d6"        # exit -> rim (the headline number)
GLASS = "#cfe3f2"
PETG = "#eb6834"
GREY = "#d9d8d4"

# --- the three setups (z above the bench, mm; x along the auger, the exit at x = 0, + toward the cap) -------------------------
SINGLE = dict(name="Current single doser\n(HR-100A, issue #116 rig)", pan=86.5, pan_x=0.0, cage_under=86.5 + 79.4, cage_top=86.5 + 79.4 + 4,
              cage_x=(-80, 80), base_top=86.5 - 6, beaker=(50.0, 70.0), floor_t=2.0, riser=None, rim=86.5 + 70.0, exit=86.5 + 70.0 + 85.0,
              est=True, tilt=30.0)
V7 = dict(name="Chain carousel v7", pan=50.0, pan_x=0.0, cage_under=300.0, cage_top=311.0, cage_x=(-97.5, 89.4), base_top=40.0,
          beaker=(38.0, 49.0), floor_t=1.2, riser=0.0, rim=282.0, exit=435.65, est=False, tilt=30.0)
V8 = dict(name="Chain carousel v8", pan=50.0, pan_x=-38.0, cage_under=300.0, cage_top=311.0, cage_x=(-38 - 97.5, -38 + 89.4), base_top=40.0,
          beaker=(38.0, 49.0), floor_t=1.2, riser=38.0, rim=282.0, exit=332.0, est=False, tilt=30.0)


def numbers(s: dict) -> dict:
    floor = s["rim"] - s["beaker"][1] + s["floor_t"]
    return {"exit_mm": round(s["exit"], 1), "rim_mm": round(s["rim"], 1), "exit_to_rim": round(s["exit"] - s["rim"], 1),
            "exit_to_beaker_floor": round(s["exit"] - floor, 1), "exit_to_pan": round(s["exit"] - s["pan"], 1), "estimated": s["est"]}


def draw(ax, s: dict) -> None:
    n = numbers(s)
    bw, bh = s["beaker"]
    px = s["pan_x"]
    x0, x1 = s["cage_x"]
    ax.add_patch(Rectangle((x0 - 10, 0), x1 - x0 + 20, s["base_top"], fc=GREY, ec=MUTED, lw=0.8))           # weighing base
    ax.add_patch(Rectangle((x0, s["base_top"]), x1 - x0, s["cage_under"] - s["base_top"], fc=GLASS, ec=MUTED, lw=0.8, alpha=0.45))
    ax.add_patch(Rectangle((x0, s["cage_under"]), x1 - x0, s["cage_top"] - s["cage_under"], fc=GREY, ec=MUTED, lw=0.8))   # lid / frame
    ax.add_patch(Rectangle((-15, s["cage_under"] - 0.5), 30, s["cage_top"] - s["cage_under"] + 1, fc=SURF, ec="none"))       # the dosing hole
    ax.add_patch(Rectangle((px - 45, s["pan"] - 3), 90, 3, fc="#9b9a96", ec="none"))                                         # pan
    bx = 0.0
    if s["riser"] is not None:
        top = s["rim"] - bh + 5.0
        ax.add_patch(Rectangle((px - 22, s["pan"]), 44, top - 14 - s["pan"], fc=PETG, ec="none", alpha=0.85))
        ax.add_patch(Rectangle((min(px, 0) - 22, top - 14), abs(px) + 44, 6, fc=PETG, ec="none", alpha=0.85))
        ax.add_patch(Rectangle((-22, top - 8), 44, 8, fc=PETG, ec="none", alpha=0.85))
    base = s["rim"] - bh
    ax.add_patch(Polygon([(bx - bw / 2, s["rim"]), (bx - bw / 2, base), (bx + bw / 2, base), (bx + bw / 2, s["rim"])], closed=False, fill=False,
                         ec=INK2, lw=1.4))
    # the auger: a 25 mm tube from the exit, cap end up at the dose tilt
    t = math.radians(s["tilt"])
    L = 105.0
    ux, uz = math.cos(t), math.sin(t)
    nx, nz = -uz, ux
    r = 12.5
    pts = [(r * nx, s["exit"] + r * nz), (L * ux + r * nx, s["exit"] + L * uz + r * nz), (L * ux - r * nx, s["exit"] + L * uz - r * nz),
           (-r * nx, s["exit"] - r * nz)]
    ax.add_patch(Polygon(pts, closed=True, fc="#f4f4f2", ec=INK2, lw=1.0))
    ax.plot([0], [s["exit"]], "o", ms=5, color=INK, zorder=5)
    ax.plot([0, 0], [s["exit"], s["rim"]], ls=(0, (2, 2)), color=MUTED, lw=0.9)
    # dimensions on the right
    floor = s["rim"] - bh + s["floor_t"]
    xs = (95.0, 168.0, 252.0)
    for xd, z1, lab, col, key in ((xs[0], s["rim"], "to the rim", ACC, "exit_to_rim"), (xs[1], floor, "to the beaker's floor", INK2, "exit_to_beaker_floor"),
                                  (xs[2], s["pan"], "to the pan", MUTED, "exit_to_pan")):
        ax.annotate("", xy=(xd, z1), xytext=(xd, s["exit"]), arrowprops=dict(arrowstyle="<->", color=col, lw=1.6 if col == ACC else 1.1,
                                                                              shrinkA=0, shrinkB=0))
        ax.plot([2, xd + 4], [s["exit"], s["exit"]], color=MUTED, lw=0.5)
        ax.plot([bw / 2 + 2 if z1 != s["pan"] else 47, xd + 4], [z1, z1], color=MUTED, lw=0.5)
        v = n[key]
        txt = f"{'~' if s['est'] else ''}{v:.0f} mm\n{lab.replace(' beaker' + chr(39) + 's', '')}"
        ax.text(xd + 5, (s["exit"] + z1) / 2, txt, fontsize=8.5, color=INK if col != MUTED else INK2, va="center", ha="left",
                fontweight="bold" if col == ACC else "normal")
    ax.text(-8, s["exit"] + 4, "auger exit", fontsize=8, color=INK2, ha="right", va="bottom")
    ax.set_title(s["name"], fontsize=11, color=INK, loc="left")
    ax.axhline(0, color=INK2, lw=1.2)
    ax.set_xlim(-150, 322)
    ax.set_ylim(-10, 500)
    ax.set_aspect("equal")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.set_xticks([])
    ax.grid(axis="y", color="#ecebe8", lw=0.6)
    ax.set_axisbelow(True)


def main() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 6.8), facecolor=SURF)
    for ax, s in zip(axes, (SINGLE, V7, V8)):
        ax.set_facecolor(SURF)
        draw(ax, s)
    axes[0].set_ylabel("height above the bench, mm", color=INK2, fontsize=9)
    fig.suptitle("How far the dose falls: the auger's exit over the beaker, side views to scale", fontsize=13, color=INK, x=0.01, ha="left")
    fig.text(0.01, 0.015, "Single doser: estimated from the Aug 4 photos (issue #116), Sam's 3.125 in pan-to-cage measurement and the 100 mL Griffin "
             "beaker (issue #144); +-15 mm. v7 and v8: from their CAD (25 mL beaker on a printed riser, dosing at 30 deg; the exit is on the "
             "hinge axis, so it is the same at every tilt).", fontsize=8, color=INK2, ha="left", wrap=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    out = HERE / "renders" / "v8" / "drop_heights.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130, facecolor=SURF)
    res = {"single_doser": numbers(SINGLE), "v7": numbers(V7), "v8": numbers(V8)}
    (HERE / "checks").mkdir(exist_ok=True)
    (HERE / "checks" / "drop_heights.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

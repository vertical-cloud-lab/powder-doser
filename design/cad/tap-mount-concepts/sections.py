"""Cross-sections of the issue #203 concepts at their strike planes, looking
from the outlet towards the cap: what the tapper is made of, where the
plunger or hammer sits, and the strip the auger sweeps when it is lifted out
of its C-clips (it must stay clear of the tapper).

    python3 sections.py      # -> renders/concept_sections.png
"""
from __future__ import annotations

import math

import cadquery as cq
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

import concepts as C  # noqa: E402

PRINTED = (0.70, 0.45, 0.85)
SOL = (0.55, 0.57, 0.62)
HW = (0.45, 0.45, 0.45)


def section(wp: cq.Workplane, x: float):
    """[(outer [(z, y)], [inner ...])] of a part cut by the plane L x = x."""
    plane = cq.Face.makePlane(600, 600, basePnt=(x, 0, 0), dir=(1, 0, 0))
    cut = wp.val().intersect(plane)
    out = []
    for f in cut.Faces():
        def pts(w):
            return [(p.z, p.y) for p in (w.positionAt(t) for t in np.linspace(0, 1, 240))]
        out.append((pts(f.outerWire()), [pts(w) for w in f.innerWires()]))
    return out


def draw_part(ax, wp, x, colour, z=2, alpha=1.0):
    for outer, inners in section(wp, x):
        o = np.array(outer)
        ax.fill(-o[:, 0], o[:, 1], color=colour, alpha=alpha, zorder=z, lw=0)
        ax.plot(-o[:, 0], o[:, 1], color="k", lw=0.6, zorder=z + 0.1)
        for inn in inners:
            i = np.array(inn)
            ax.fill(-i[:, 0], i[:, 1], color="white", zorder=z + 0.05, lw=0)
            ax.plot(-i[:, 0], i[:, 1], color="k", lw=0.5, zorder=z + 0.1)


def frame(ax, title):
    # plotted as seen from the outlet: horizontal = world +X = -L z (away from the stepper to the right)
    ax.add_patch(Rectangle((-60, C.FLOOR_Y - 6), 140, 6, color=(0.80, 0.82, 0.86), zorder=1))
    ax.text(-57, C.FLOOR_Y - 4.5, "mounting plate", fontsize=7, color="0.3", zorder=1.1)
    ax.add_patch(Rectangle((-C.TUBE_R, -C.TUBE_R), 2 * C.TUBE_R, 75, facecolor=(0.93, 0.97, 1.0),
                           edgecolor=(0.4, 0.55, 0.85), ls="--", lw=0.8, zorder=0.5))
    ax.text(0, 52, "auger lifts out\nthrough here", ha="center", fontsize=7, color=(0.25, 0.4, 0.75))
    ax.add_patch(Circle((0, 0), C.TUBE_R, facecolor=(0.90, 0.76, 0.45), edgecolor="k", lw=0.8, zorder=3))
    ax.add_patch(Circle((0, 0), C.TUBE_R - 2.0, facecolor="white", edgecolor="k", lw=0.5, zorder=3.1))
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_xlim(-45, 85)
    ax.set_ylim(-37, 62)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def clip_outline(ax):
    """The front Flexible Bracket, projected (it sits 10 mm behind this plane)."""
    b = C.bracket_in_L(C.FRONT_BRACKET_X)
    for outer, _ in section(b, C.FRONT_BRACKET_X):
        o = np.array(outer)
        ax.plot(-o[:, 0], o[:, 1], color=(0.35, 0.55, 0.75), lw=0.8, ls=":", zorder=4)


def gap_note(ax, x0, x1, y, text, dy=-6):
    ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text((x0 + x1) / 2, y + dy, text, ha="center", fontsize=7)


def main():
    fig, axs = plt.subplots(1, 4, figsize=(18, 4.9))
    # 1 tower
    ax = axs[0]
    frame(ax, "1  Bolt-on tap tower (x = strike plane)")
    clip_outline(ax)
    parts = C.concept1()
    draw_part(ax, parts["Tap tower (printed)"], 0.0, PRINTED)
    draw_part(ax, parts["Solenoid"], 0.0, SOL, z=2.5)
    tip = C.TUBE_R + C.REST_GAP
    gap_note(ax, C.TUBE_R, tip, 10.0, f"{C.REST_GAP:g} mm\nat rest", dy=3)
    ax.text(30, -20, "slots: slide the solenoid\n±2 mm to set the gap", fontsize=7)
    # 2 tap bracket
    ax = axs[1]
    frame(ax, "2  Tap bracket: clip + tower in one part")
    parts = C.concept2()
    draw_part(ax, parts["Tap bracket (printed)"], C.FRONT_BRACKET_X, PRINTED, alpha=0.35)
    draw_part(ax, parts["Tap bracket (printed)"], 0.0, PRINTED)
    draw_part(ax, parts["Solenoid"], 0.0, SOL, z=2.5)
    gap_note(ax, C.TUBE_R, tip, 10.0, f"{C.REST_GAP:g} mm, set\nby one print", dy=3)
    ax.text(-43, 30, "clip (pale) is 10 mm\nbehind this plane,\non the same base", fontsize=7)
    # 3 hammer
    ax = axs[2]
    frame(ax, "3  See-saw hammer, strikes from below")
    xc = 0.5
    parts = C.concept3()
    draw_part(ax, parts["Hammer frame (printed)"], xc + 5.0, PRINTED, alpha=0.35)
    draw_part(ax, parts["Hammer arm (printed)"], xc, PRINTED, z=2.6)
    draw_part(ax, parts["Pivot (M3 screw)"], xc, HW, z=2.7)
    draw_part(ax, parts["Solenoid"], xc, SOL, z=2.5)
    hot = C.concept3(energised=True)
    draw_part(ax, hot["Hammer arm (printed)"], xc, PRINTED, z=2.4, alpha=0.3)
    gap_note(ax, 6, 6, -C.TUBE_R, "")
    ax.annotate("head swings up\n(ghost = striking)", xy=(0, -C.TUBE_R - 2), xytext=(-43, -27),
                fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.annotate("solenoid pushes\nthis end down", xy=(-C.HAMMER_ROD_Z, -19), xytext=(45, -12),
                fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.7))
    # 4 flip saddle
    ax = axs[3]
    frame(ax, "4  Flip-away saddle (old collar, hinged)")
    parts = C.concept4()
    for n, colour, z in (("Hinge post (printed)", PRINTED, 2), ("Saddle (printed)", PRINTED, 2.2),
                         ("Solenoid", SOL, 2.5), ("Hinge pin (M3 screw)", HW, 2.7)):
        draw_part(ax, parts[n], 0.0 if "post" not in n else 0.0, colour, z=z)
    opened = C.concept4(open_deg=75.0)
    for n in ("Saddle (printed)", "Solenoid"):
        draw_part(ax, opened[n], 0.0, PRINTED if "Saddle" in n else SOL, z=1.8, alpha=0.25)
    ax.annotate("flips out for a swap\n(ghost = open)", xy=(55, 20), xytext=(40, 48), fontsize=7,
                arrowprops=dict(arrowstyle="->", lw=0.7))
    fig.suptitle("Sections at the strike plane, seen from the outlet end (stepper on the left). "
                 "The auger lifts straight up out of its C-clips, so nothing may sit in the blue strip "
                 "when the tapper is at rest.", fontsize=10, x=0.01, ha="left")
    plt.tight_layout(rect=(0, 0, 1, 0.94))
    out = C.OUT / "concept_sections.png"
    plt.savefig(out, dpi=130)
    print("  ->", out.name)


if __name__ == "__main__":
    main()

"""2D dimensioned schematic of the twist-shutter cap (front + top elevations).

Mirrors the constants from cad_model.py exactly. Run:

    python sketch_2d.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Wedge

OUT = Path(__file__).parent / "renders"
OUT.mkdir(exist_ok=True)

# Mirrored from cad_model.py
AUGER_OD = 25.0
EXIT_HOLE_D = 3.0
CAP_OD = 36.0
DISC_T = 4.0
PIVOT_D = 4.0
RIM_LIP_H = 3.0
SLOT_INNER_R = 4.0
SLOT_OUTER_R = 8.0
SLOT_ANGLE = 60.0
TAB_L = 14.0
TAB_W = 6.0


def annotate(ax, x1, y1, x2, y2, label, side="bottom", off=2.0):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="<->", color="0.2", lw=0.8),
    )
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if side == "bottom":
        my -= off
    elif side == "top":
        my += off
    elif side == "right":
        mx += off
    ax.text(mx, my, label, ha="center", va="center", fontsize=8)


fig, (ax_front, ax_top) = plt.subplots(1, 2, figsize=(11, 5))

# ---- Front elevation (vertical section) ----
ax_front.set_title("Front (section) — Z up")
ax_front.set_aspect("equal")
ax_front.set_xlim(-CAP_OD / 2 - 12, CAP_OD / 2 + 18)
ax_front.set_ylim(-3, DISC_T * 2 + RIM_LIP_H + 22)

ax_front.add_patch(Rectangle((-CAP_OD / 2, 0), CAP_OD, DISC_T,
                              facecolor="#c9beed", edgecolor="0.2"))
ax_front.add_patch(Rectangle((-CAP_OD / 2, DISC_T), CAP_OD, DISC_T,
                              facecolor="#c9beed", edgecolor="0.2"))
ax_front.add_patch(Rectangle((-AUGER_OD / 2 - 1.6, 2 * DISC_T),
                              AUGER_OD + 3.2, RIM_LIP_H,
                              facecolor="#b3a7e8", edgecolor="0.2"))
ax_front.add_patch(Rectangle((-AUGER_OD / 2, 2 * DISC_T),
                              AUGER_OD, RIM_LIP_H,
                              facecolor="white", edgecolor="0.2"))
ax_front.add_patch(Rectangle((-AUGER_OD / 2, 2 * DISC_T + RIM_LIP_H),
                              2.0, 18, facecolor="0.85", edgecolor="0.5"))
ax_front.add_patch(Rectangle((AUGER_OD / 2 - 2.0, 2 * DISC_T + RIM_LIP_H),
                              2.0, 18, facecolor="0.85", edgecolor="0.5"))
ax_front.add_patch(Rectangle((CAP_OD / 2 - 1.0, DISC_T / 2 - 1.5),
                              TAB_L, 3.0,
                              facecolor="#c9beed", edgecolor="0.2"))

annotate(ax_front, -CAP_OD / 2, -1.5, CAP_OD / 2, -1.5,
         f"CAP_OD = {CAP_OD:.0f}", side="bottom", off=1.0)
annotate(ax_front, CAP_OD / 2 + 9, 0, CAP_OD / 2 + 9, DISC_T,
         f"DISC_T = {DISC_T}", side="right", off=2.5)
annotate(ax_front, CAP_OD / 2 + 9, DISC_T, CAP_OD / 2 + 9, 2 * DISC_T,
         f"DISC_T = {DISC_T}", side="right", off=2.5)
annotate(ax_front, -AUGER_OD / 2, 2 * DISC_T + RIM_LIP_H + 19,
         AUGER_OD / 2, 2 * DISC_T + RIM_LIP_H + 19,
         f"AUGER_OD = {AUGER_OD:.0f}", side="top", off=1.5)

ax_front.set_xlabel("X [mm]")
ax_front.set_ylabel("Z [mm]")
ax_front.grid(True, ls=":", lw=0.4, alpha=0.5)

# ---- Top view ----
ax_top.set_title("Top (closed: slots 180° apart)")
ax_top.set_aspect("equal")
ax_top.set_xlim(-CAP_OD / 2 - 16, CAP_OD / 2 + 6)
ax_top.set_ylim(-CAP_OD / 2 - 6, CAP_OD / 2 + 6)

ax_top.add_patch(Circle((0, 0), CAP_OD / 2,
                         facecolor="#e8e1ff", edgecolor="0.2"))
ax_top.add_patch(Circle((0, 0), AUGER_OD / 2,
                         facecolor="none", edgecolor="0.5", ls="--"))
ax_top.add_patch(Wedge((0, 0), SLOT_OUTER_R, -SLOT_ANGLE / 2, SLOT_ANGLE / 2,
                        width=SLOT_OUTER_R - SLOT_INNER_R,
                        facecolor="white", edgecolor="0.2"))
ax_top.add_patch(Wedge((0, 0), SLOT_OUTER_R,
                        180 - SLOT_ANGLE / 2, 180 + SLOT_ANGLE / 2,
                        width=SLOT_OUTER_R - SLOT_INNER_R,
                        facecolor="0.85", edgecolor="0.2", hatch="//"))
ax_top.add_patch(Circle((0, 0), PIVOT_D / 2,
                         facecolor="white", edgecolor="0.2"))
ax_top.add_patch(Rectangle((-CAP_OD / 2 - TAB_L + 1.0, -TAB_W / 2),
                            TAB_L, TAB_W,
                            facecolor="#c9beed", edgecolor="0.2"))

ax_top.text(0, SLOT_OUTER_R + 1.5, "upper slot (channel)",
            ha="center", fontsize=7)
ax_top.text(0, -SLOT_OUTER_R - 1.5, "lower slot (driver, 180° from upper)",
            ha="center", va="top", fontsize=7)
ax_top.text(-CAP_OD / 2 - TAB_L / 2, TAB_W / 2 + 1.0,
            "actuation tab\n(60° rotates open)",
            ha="center", fontsize=7)
ax_top.set_xlabel("X [mm]")
ax_top.set_ylabel("Y [mm]")
ax_top.grid(True, ls=":", lw=0.4, alpha=0.5)

fig.suptitle("Twist-shutter sealing cap — dimensioned schematic (mm)")
fig.tight_layout()
out = OUT / "sealing_cap_twist_shutter_sketch.png"
fig.savefig(out, dpi=150)
print(f"wrote {out}")

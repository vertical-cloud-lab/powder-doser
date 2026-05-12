"""
2D dimensioned schematic of the single-channel powder-doser module.

Mirrors the constants from cad_model.py so this and the CAD model never
drift; produces front-elevation + side-elevation matplotlib drawings with
dimensions called out in millimetres. Intended as the at-a-glance
"freeform sketch" complement to the parametric CadQuery model — same
role that sketch_2d.py plays for design/cad/inward-collection-cup/.

Output:
    renders/single_channel_module_sketch.png

Run:
    python sketch_2d.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ----- shared constants (see cad_model.py for the canonical copies) ------
PLATE_W = 80.0
PLATE_T = 6.0
EXIT_GAP = 8.0
EXIT_HOLE_D = 30.0

AUGER_OD = 25.0
AUGER_LEN = 250.0

NEMA11_FACE = 28.0
NEMA11_BODY_L = 45.0
NEMA11_SHAFT_L = 20.0

COUPLER_OD = 14.0
COUPLER_L = 25.0

COLLAR_OD = 40.0
COLLAR_ID = AUGER_OD + 2.0
COLLAR_H = 22.0
COLLAR_Z0 = PLATE_T + EXIT_GAP + 4.0

SOL_W = 9.6
SOL_H = 19.0
SOL_L = 22.0
SOL_WING_T = 4.0
SOL_WING_H = SOL_H + 4.0

ERM_D = 10.0
ERM_T = 2.7
ERM_PAD_T = 2.0
ERM_PAD_H = 14.0

POST_OD = 10.0
POST_INSET = 8.0

TOP_PLATE_TOP_Z = PLATE_T + EXIT_GAP + AUGER_LEN + 6.0 + COUPLER_L + 2.0
TOP_PLATE_BOT_Z = TOP_PLATE_TOP_Z - PLATE_T


def add_box(ax, x, y, w, h, *, fc, ec="black", lw=1.0, label=None, alpha=1.0):
    ax.add_patch(mpatches.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                                    linewidth=lw, alpha=alpha))
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7)


def add_circle(ax, cx, cy, r, *, fc, ec="black", lw=1.0, label=None, alpha=1.0):
    ax.add_patch(mpatches.Circle((cx, cy), r, facecolor=fc, edgecolor=ec,
                                 linewidth=lw, alpha=alpha))
    if label:
        ax.text(cx, cy, label, ha="center", va="center", fontsize=7)


def dim_v(ax, x, y0, y1, label, *, txt_x=None):
    """Vertical dimension line with arrowheads."""
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="<->", color="0.3", lw=0.7))
    tx = txt_x if txt_x is not None else x + 6
    ax.text(tx, (y0 + y1) / 2, label, fontsize=7, color="0.2", va="center")


def dim_h(ax, x0, x1, y, label, *, txt_y=None):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", color="0.3", lw=0.7))
    ty = txt_y if txt_y is not None else y + 4
    ax.text((x0 + x1) / 2, ty, label, fontsize=7, color="0.2", ha="center")


# =========================================================================
# FRONT ELEVATION — looking along -Y, +X to the right, +Z up
# =========================================================================
fig, (ax_front, ax_side) = plt.subplots(1, 2, figsize=(12, 11),
                                        gridspec_kw={"width_ratios": [1, 1]})

ax = ax_front
ax.set_aspect("equal")
ax.set_title("Front elevation (looking along −Y)\nsolenoid right, ERM coin left",
             fontsize=10)

# Base plate (outline)
add_box(ax, -PLATE_W / 2, 0, PLATE_W, PLATE_T, fc="#dcdcea", label="base plate")
# Exit clearance hole shown dashed in plate
ax.plot([-EXIT_HOLE_D / 2, EXIT_HOLE_D / 2], [PLATE_T / 2, PLATE_T / 2],
        "k--", lw=0.6)

# Posts (front face shows two posts side by side; the back two are hidden behind)
post_x = PLATE_W / 2 - POST_INSET
add_box(ax, +post_x - POST_OD / 2, PLATE_T, POST_OD, TOP_PLATE_BOT_Z - PLATE_T,
        fc="#e8e8f2", lw=0.6)
add_box(ax, -post_x - POST_OD / 2, PLATE_T, POST_OD, TOP_PLATE_BOT_Z - PLATE_T,
        fc="#e8e8f2", lw=0.6)

# Auger rotor (envelope)
auger_z0 = PLATE_T + EXIT_GAP
add_box(ax, -AUGER_OD / 2, auger_z0, AUGER_OD, AUGER_LEN, fc="#fff4cc",
        label="PR-#16\nauger\nØ25×250")

# Tap collar
add_box(ax, -COLLAR_OD / 2, COLLAR_Z0, COLLAR_OD, COLLAR_H,
        fc="#cfd8e3", alpha=0.5)
ax.text(-COLLAR_OD / 2 - 2, COLLAR_Z0 + COLLAR_H + 2, "tap collar",
        fontsize=7, ha="right")

# Solenoid on +X
sol_x = COLLAR_OD / 2 + SOL_WING_T
sol_z = COLLAR_Z0 + (COLLAR_H - SOL_H) / 2  # using SOL_H as visible height in this view
add_box(ax, sol_x, sol_z, SOL_L, SOL_H, fc="#bfa898", label="JF-0530B\nsolenoid")

# ERM coin on -X
erm_x = -(COLLAR_OD / 2 + ERM_PAD_T + ERM_T)
erm_z = COLLAR_Z0 + (COLLAR_H - ERM_PAD_H) / 2
add_box(ax, erm_x, erm_z + (ERM_PAD_H - ERM_D) / 2, ERM_T, ERM_D,
        fc="#f0c080", label="ERM\ncoin")

# Top plate
add_box(ax, -PLATE_W / 2, TOP_PLATE_BOT_Z, PLATE_W, PLATE_T, fc="#dcdcea",
        label="top plate")

# Coupler
coup_z0 = PLATE_T + EXIT_GAP + AUGER_LEN + 6.0
add_box(ax, -COUPLER_OD / 2, coup_z0, COUPLER_OD, COUPLER_L, fc="#bbbbbb",
        label="flex\ncoupler")

# Stepper on top
add_box(ax, -NEMA11_FACE / 2, TOP_PLATE_TOP_Z, NEMA11_FACE, NEMA11_BODY_L,
        fc="#3d3d44")
ax.text(0, TOP_PLATE_TOP_Z + NEMA11_BODY_L / 2, "NEMA 11\nstepper",
        ha="center", va="center", fontsize=7, color="white")

# Dimensions
dim_v(ax, -PLATE_W / 2 - 8, 0, TOP_PLATE_TOP_Z + NEMA11_BODY_L,
      f"{TOP_PLATE_TOP_Z + NEMA11_BODY_L:.0f} mm\n(envelope)",
      txt_x=-PLATE_W / 2 - 14)
dim_v(ax, PLATE_W / 2 + 8, auger_z0, auger_z0 + AUGER_LEN, f"{AUGER_LEN:.0f}",
      txt_x=PLATE_W / 2 + 14)
dim_v(ax, PLATE_W / 2 + 30, 0, PLATE_T, f"{PLATE_T:.0f}",
      txt_x=PLATE_W / 2 + 36)
dim_h(ax, -PLATE_W / 2, PLATE_W / 2, -8, f"{PLATE_W:.0f} mm")
dim_h(ax, -AUGER_OD / 2, AUGER_OD / 2, auger_z0 - 4,
      f"Ø{AUGER_OD:.0f}", txt_y=auger_z0 - 9)

ax.set_xlim(-95, 95)
ax.set_ylim(-25, TOP_PLATE_TOP_Z + NEMA11_BODY_L + 20)
ax.set_xticks([])
ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)


# =========================================================================
# SIDE ELEVATION — looking along +X, +Y to the right, +Z up.
# Shows the electronics tray + driver carriers along +Y.
# =========================================================================
ax = ax_side
ax.set_aspect("equal")
ax.set_title("Side elevation (looking along +X)\nelectronics tray on +Y face",
             fontsize=10)

# Base plate
add_box(ax, -PLATE_W / 2, 0, PLATE_W, PLATE_T, fc="#dcdcea", label="base plate")

# Posts (side view — front and back posts overlap)
add_box(ax, post_x - POST_OD / 2, PLATE_T, POST_OD, TOP_PLATE_BOT_Z - PLATE_T,
        fc="#e8e8f2", lw=0.6)
add_box(ax, -post_x - POST_OD / 2, PLATE_T, POST_OD, TOP_PLATE_BOT_Z - PLATE_T,
        fc="#e8e8f2", lw=0.6)

# Auger envelope (centred)
add_box(ax, -AUGER_OD / 2, auger_z0, AUGER_OD, AUGER_LEN, fc="#fff4cc")

# Tap collar (front profile)
add_box(ax, -COLLAR_OD / 2, COLLAR_Z0, COLLAR_OD, COLLAR_H,
        fc="#cfd8e3", alpha=0.5)
ax.text(0, COLLAR_Z0 + COLLAR_H + 2, "tap collar (Ø40 OD / Ø27 ID)",
        ha="center", fontsize=7)

# Top plate + stepper + coupler (visible from side too)
add_box(ax, -PLATE_W / 2, TOP_PLATE_BOT_Z, PLATE_W, PLATE_T, fc="#dcdcea")
add_box(ax, -COUPLER_OD / 2, coup_z0, COUPLER_OD, COUPLER_L, fc="#bbbbbb")
add_box(ax, -NEMA11_FACE / 2, TOP_PLATE_TOP_Z, NEMA11_FACE, NEMA11_BODY_L,
        fc="#3d3d44")
ax.text(0, TOP_PLATE_TOP_Z + NEMA11_BODY_L / 2, "NEMA 11\nstepper",
        ha="center", va="center", fontsize=7, color="white")

# Electronics tray on +Y (rendered as a thin vertical panel on the right of
# this side view, since +Y is "right" in this projection).
TRAY_Z0 = PLATE_T + 60.0
TRAY_H = 100.0
TRAY_T = 3.0
TRAY_W = 70.0
tray_y = PLATE_W / 2 - POST_INSET + POST_OD / 2
add_box(ax, tray_y, TRAY_Z0, TRAY_T, TRAY_H, fc="#a0a0bb",
        label="elec.\ntray")
# Driver carriers stacked on the tray
drivers = [("DRV8825", 15.5, 8), ("DRV8871", 17.0, 8), ("DRV2605L", 20.0, 8)]
z = TRAY_Z0 + 8
for name, h, t in drivers:
    add_box(ax, tray_y + TRAY_T, z, t, h, fc="#2a8a4a", label=name)
    z += h + 6

# Dimensions
dim_v(ax, -PLATE_W / 2 - 8, COLLAR_Z0, COLLAR_Z0 + COLLAR_H,
      f"collar\n{COLLAR_H:.0f}", txt_x=-PLATE_W / 2 - 32)
dim_v(ax, -PLATE_W / 2 - 8, 0, COLLAR_Z0,
      f"{COLLAR_Z0:.0f}\nfrom plate base", txt_x=-PLATE_W / 2 - 36)
dim_v(ax, PLATE_W / 2 + 36, 0, TOP_PLATE_BOT_Z,
      f"post\n{TOP_PLATE_BOT_Z - PLATE_T:.0f} mm\n(M4 bore)",
      txt_x=PLATE_W / 2 + 42)
dim_h(ax, -PLATE_W / 2, PLATE_W / 2, -8, f"{PLATE_W:.0f} mm")

ax.set_xlim(-95, 130)
ax.set_ylim(-25, TOP_PLATE_TOP_Z + NEMA11_BODY_L + 20)
ax.set_xticks([])
ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)


fig.suptitle(
    "Single-channel powder-doser module — Idea B archetype "
    "(design/brainstorming.md §2.2)\n"
    "PR-#16 auger + PR-#25 actuator stack on a single replicable frame",
    fontsize=11, y=0.995,
)
fig.tight_layout(rect=(0, 0, 1, 0.97))

OUT = Path(__file__).parent / "renders" / "single_channel_module_sketch.png"
OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT, dpi=160, bbox_inches="tight")
print(f"wrote {OUT}")

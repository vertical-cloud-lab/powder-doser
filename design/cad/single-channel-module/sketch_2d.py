"""
2D dimensioned schematic of the v2 single-channel powder-doser module
(matches cad_model.py).

Outputs:
  renders/single_channel_module_sketch.png       (3-panel: side / front / flow)
  renders/single_channel_module_powder_flow.png  (standalone larger flow view)

Run: python sketch_2d.py
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---- shared constants (must match cad_model.py) -------------------------
AUGER_OD = 25.0
AUGER_LEN = 250.0

BRG_ID, BRG_OD, BRG_T = 25.0, 37.0, 7.0

NEMA11_FACE = 28.0
NEMA11_BODY_L = 45.0

PULLEY_OD = 12.2
PULLEY_FLANGE_OD = 16.0
PULLEY_H = 16.0

SOL_W, SOL_H, SOL_L = 9.6, 19.0, 22.0
ERM_D, ERM_T = 10.0, 2.7
ERM_PAD_T = 3.0

COLLAR_OD = 50.0
COLLAR_H = 16.0
COLLAR_FLANGE_T = 6.0

SPINE_W = 90.0
SPINE_T = 8.0
SPINE_H = 360.0

CART_BASE_OD = 36.0
CART_BASE_H = 12.0
CART_HOPPER_OD = 60.0
CART_HOPPER_H = 60.0
CART_NECK_H = 6.0

CRADLE_PIVOT_Z = 200.0
CRADLE_BASE_T = 8.0
CRADLE_BASE_W = 220.0
CHEEK_W = 80.0
CHEEK_H = 220.0

ROTOR_X_OFFSET = SPINE_T / 2 + COLLAR_OD / 2 + 4.0
ROTOR_BOTTOM_Z = -30.0
AX_ROTOR = SPINE_T / 2 + COLLAR_FLANGE_T + COLLAR_OD / 2
AUGER_TOP_Z = COLLAR_H + 10 + AUGER_LEN


# ---- helpers -------------------------------------------------------------
def add_box(ax, x, y, w, h, *, fc, ec="black", lw=1.0, label=None, alpha=1.0):
    ax.add_patch(mpatches.Rectangle((x, y), w, h, facecolor=fc,
                                    edgecolor=ec, linewidth=lw, alpha=alpha))
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7)


def add_circle(ax, cx, cy, r, *, fc, ec="black", lw=1.0, label=None):
    ax.add_patch(mpatches.Circle((cx, cy), r, facecolor=fc, edgecolor=ec, linewidth=lw))
    if label:
        ax.text(cx, cy, label, ha="center", va="center", fontsize=7)


def dim_v(ax, x, y0, y1, label, *, txt_x=None):
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="<->", color="0.3", lw=0.7))
    tx = txt_x if txt_x is not None else x + 6
    ax.text(tx, (y0 + y1) / 2, label, fontsize=7, color="0.2", va="center")


def dim_h(ax, x0, x1, y, label, *, txt_y=None):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", color="0.3", lw=0.7))
    ty = txt_y if txt_y is not None else y + 4
    ax.text((x0 + x1) / 2, ty, label, fontsize=7, color="0.2", ha="center")


def label_to(ax, x_to, y_to, x_lbl, y_lbl, text):
    ax.annotate("", xy=(x_to, y_to), xytext=(x_lbl, y_lbl),
                arrowprops=dict(arrowstyle="-", color="0.4", lw=0.5))
    ax.text(x_lbl, y_lbl, text, fontsize=6.5, color="0.2",
            ha="left", va="center",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.7", lw=0.4))


# ---- panel renderers (reusable) -----------------------------------------
def draw_side_panel(ax):
    ax.set_aspect("equal")
    ax.set_title("Side elevation (looking along +Y)\n"
                 "module shown vertical (cradle locked at 0°)",
                 fontsize=10)
    add_box(ax, -90, -10, 180, CRADLE_BASE_T, fc="#bcd4bc", label="cradle_base")
    add_box(ax, -CHEEK_H / 2, CRADLE_PIVOT_Z - CHEEK_W / 2, CHEEK_H, CHEEK_W,
            fc="#dde8dd", alpha=0.5,
            label="cradle_cheek\n(arc-slot lock,\n0–75° tilt)")
    add_box(ax, -SPINE_T / 2, 0, SPINE_T, SPINE_H, fc="#dcdcea")
    ax.text(SPINE_T / 2 + 1, SPINE_H * 0.85, "spine\n(printed)",
            fontsize=7, ha="left", va="top")
    add_circle(ax, 0, CRADLE_PIVOT_Z, 2.5, fc="white", ec="black")
    ax.text(SPINE_T / 2 + 5, CRADLE_PIVOT_Z, "M5 trunnion\npivot",
            fontsize=6.5, ha="left", va="center")

    # Bearing collar
    add_box(ax, SPINE_T / 2, 0, COLLAR_FLANGE_T, COLLAR_H, fc="#dcdcea")
    ax.text(SPINE_T / 2 + COLLAR_FLANGE_T + 1, COLLAR_H + 1,
            "collar flange\n(M3 BHCS into\nspine inserts)",
            fontsize=6.5, ha="left", va="bottom")
    add_box(ax, SPINE_T / 2 + COLLAR_FLANGE_T, 0, COLLAR_OD, COLLAR_H,
            fc="#cfd8e3", alpha=0.7)
    brg_x0 = SPINE_T / 2 + COLLAR_FLANGE_T + (COLLAR_OD - BRG_OD) / 2
    add_box(ax, brg_x0, (COLLAR_H - BRG_T) / 2, BRG_OD, BRG_T,
            fc="#9aa0a6", label="6805ZZ bearing\n(Ø25 × Ø37 × 7)")
    add_box(ax, brg_x0 + (BRG_OD - BRG_ID) / 2,
            (COLLAR_H - BRG_T) / 2 - 0.2, BRG_ID, BRG_T + 0.4,
            fc="white", ec="0.6", lw=0.4)
    add_box(ax, AX_ROTOR - (ERM_D / 2 + 4), -ERM_PAD_T,
            ERM_D + 8, ERM_PAD_T, fc="#cfd8e3", alpha=0.7)
    add_box(ax, AX_ROTOR - ERM_D / 2, -ERM_PAD_T - ERM_T,
            ERM_D, ERM_T, fc="#f0c080", label="ERM coin\n(glued under collar)")

    # Rotor
    add_box(ax, AX_ROTOR - AUGER_OD / 2, ROTOR_BOTTOM_Z, AUGER_OD,
            AUGER_LEN + 6, fc="#fff4cc", alpha=0.7)
    ax.text(AX_ROTOR + AUGER_OD / 2 + 4, ROTOR_BOTTOM_Z + AUGER_LEN / 2,
            "PR-#16 v4 rotor\n(Ø25 × 250,\nrotates as one)",
            fontsize=6.5, ha="left", va="center")
    ax.annotate("", xy=(AX_ROTOR + AUGER_OD / 2 + 6, ROTOR_BOTTOM_Z),
                xytext=(AX_ROTOR + AUGER_OD / 2 + 6, 0),
                arrowprops=dict(arrowstyle="<->", color="0.3", lw=0.7))
    ax.text(AX_ROTOR + AUGER_OD / 2 + 8, ROTOR_BOTTOM_Z / 2,
            "30 mm protrusion\n(clears base at\n0–75° tilt)",
            fontsize=6.5, ha="left", va="center")

    # Cartridge
    add_box(ax, AX_ROTOR - CART_BASE_OD / 2, AUGER_TOP_Z,
            CART_BASE_OD, CART_BASE_H, fc="#f8e5b0", alpha=0.7)
    add_box(ax, AX_ROTOR - CART_HOPPER_OD / 2,
            AUGER_TOP_Z + CART_BASE_H + CART_NECK_H,
            CART_HOPPER_OD, CART_HOPPER_H, fc="#f8e5b0", alpha=0.7,
            label="cartridge\n(removable;\npowder enters here)")

    # Pulley
    pulley_z0 = ROTOR_BOTTOM_Z + AUGER_LEN + 6 + 4
    add_box(ax, AX_ROTOR - PULLEY_FLANGE_OD / 2, pulley_z0,
            PULLEY_FLANGE_OD, PULLEY_H, fc="#bbbbbb", alpha=0.7,
            label="GT2 pulley\n(16T)")
    ax.text(-90, 280,
            "NEMA 11 stepper +\nGT2 belt drive sit\non a side bracket\n"
            "(see front view ↗)",
            fontsize=7, ha="left", va="top",
            bbox=dict(boxstyle="round,pad=0.3", fc="#ffe", ec="0.5", lw=0.5))

    dim_v(ax, -65, 0, SPINE_H, f"spine {SPINE_H:.0f}", txt_x=-85)
    dim_v(ax, AX_ROTOR + AUGER_OD / 2 + 32, ROTOR_BOTTOM_Z,
          ROTOR_BOTTOM_Z + AUGER_LEN, f"rotor {AUGER_LEN:.0f}",
          txt_x=AX_ROTOR + AUGER_OD / 2 + 38)
    dim_h(ax, AX_ROTOR - AUGER_OD / 2, AX_ROTOR + AUGER_OD / 2,
          ROTOR_BOTTOM_Z - 14, f"Ø{AUGER_OD:.0f}",
          txt_y=ROTOR_BOTTOM_Z - 22)

    ax.set_xlim(-110, 130)
    ax.set_ylim(-55, 410)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def draw_front_panel(ax):
    ax.set_aspect("equal")
    ax.set_title("Front elevation (facing the spine)\n"
                 "solenoid sticks out on +Y; cradle straddles the spine",
                 fontsize=10)
    add_box(ax, -SPINE_W / 2, 0, SPINE_W, SPINE_H, fc="#dcdcea")
    ax.text(0, SPINE_H * 0.92, "spine plate\n(8 mm PETG,\n90 × 360 face)",
            ha="center", va="top", fontsize=7)

    # Insert holes
    for dy in (+30, -30):
        add_circle(ax, dy, COLLAR_H / 2 + 8, 2.25, fc="white", ec="black", lw=0.6)
    for dy in (+25, -25):
        for dz in (-10, +10):
            add_circle(ax, dy, SPINE_H - 90 + dz, 2.25,
                       fc="white", ec="black", lw=0.6)
    add_circle(ax, 0, CRADLE_PIVOT_Z, 2.7, fc="#fcfcfc", ec="black", lw=0.6)
    ax.text(SPINE_W / 2 + 4, CRADLE_PIVOT_Z, "M5 pivot",
            fontsize=6.5, va="center")
    ax.text(SPINE_W / 2 + 4, SPINE_H - 90,
            "motor bracket\n(4× M3 inserts)", fontsize=6.5, va="center")
    ax.text(SPINE_W / 2 + 4, COLLAR_H / 2 + 8,
            "collar feet\n(2× M3 inserts)", fontsize=6.5, va="center")

    # Solenoid
    sol_y = 30
    add_box(ax, sol_y, COLLAR_H / 2 - SOL_H / 2, SOL_L, SOL_H,
            fc="#bfa898", label="JF-0530B")
    ax.text(sol_y + SOL_L + 2, COLLAR_H / 2,
            "plunger taps\nrotor wall through\ncollar window",
            fontsize=6.5, va="center")

    # Cradle
    add_box(ax, -CHEEK_H / 2, CRADLE_PIVOT_Z - CHEEK_W / 2,
            CHEEK_H, CHEEK_W, fc="none", ec="#5a7a5a", lw=0.6, alpha=0.6)
    for ang in (0, 15, 30, 45, 60, 75):
        a = math.radians(ang)
        cx = 60 * math.sin(a)
        cy = CRADLE_PIVOT_Z - 60 * (1 - math.cos(a))
        add_circle(ax, cx, cy, 3.0, fc="white", ec="#5a7a5a", lw=0.6)
    ax.text(-CHEEK_H / 2 - 5, CRADLE_PIVOT_Z + 30,
            "arc-slot detents:\n0/15/30/45/60/75°",
            fontsize=6.5, ha="right", va="center")

    add_box(ax, -CRADLE_BASE_W / 2, -10, CRADLE_BASE_W, CRADLE_BASE_T,
            fc="#bcd4bc", label="cradle_base")
    dim_h(ax, -SPINE_W / 2, SPINE_W / 2, -25, f"{SPINE_W:.0f}")
    dim_v(ax, -SPINE_W / 2 - 10, 0, SPINE_H, f"{SPINE_H:.0f}",
          txt_x=-SPINE_W / 2 - 30)

    ax.set_xlim(-CRADLE_BASE_W / 2 - 25, CRADLE_BASE_W / 2 + 25)
    ax.set_ylim(-30, 410)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def draw_flow_panel(ax):
    ax.set_aspect("equal")
    ax.set_title("Powder-flow cross-section\n"
                 "hopper → top loading slots → helical channel → exit nozzle → cup",
                 fontsize=10)

    # Cartridge — sectioned
    add_box(ax, AX_ROTOR - CART_HOPPER_OD / 2,
            AUGER_TOP_Z + CART_BASE_H + CART_NECK_H,
            CART_HOPPER_OD, CART_HOPPER_H, fc="none", ec="#888", lw=0.7)
    add_box(ax, AX_ROTOR - (CART_HOPPER_OD / 2 - 2),
            AUGER_TOP_Z + CART_BASE_H + CART_NECK_H,
            CART_HOPPER_OD - 4, CART_HOPPER_H * 0.7,
            fc="#d0a060", alpha=0.5, label="powder")
    ax.plot([AX_ROTOR - CART_HOPPER_OD / 2, AX_ROTOR - CART_BASE_OD / 2],
            [AUGER_TOP_Z + CART_BASE_H + CART_NECK_H,
             AUGER_TOP_Z + CART_BASE_H], color="#888", lw=0.7)
    ax.plot([AX_ROTOR + CART_HOPPER_OD / 2, AX_ROTOR + CART_BASE_OD / 2],
            [AUGER_TOP_Z + CART_BASE_H + CART_NECK_H,
             AUGER_TOP_Z + CART_BASE_H], color="#888", lw=0.7)
    add_box(ax, AX_ROTOR - CART_BASE_OD / 2, AUGER_TOP_Z,
            CART_BASE_OD, CART_BASE_H, fc="none", ec="#888", lw=0.7)

    # Rotor outline
    add_box(ax, AX_ROTOR - AUGER_OD / 2, ROTOR_BOTTOM_Z,
            AUGER_OD, AUGER_LEN + 6, fc="none", ec="#888", lw=0.7)
    # Helix
    zs = np.linspace(ROTOR_BOTTOM_Z + 5, ROTOR_BOTTOM_Z + AUGER_LEN - 5, 200)
    xs = AX_ROTOR + (AUGER_OD / 2 - 3) * np.sin(zs * 2 * math.pi / 10)
    ax.plot(xs, zs, color="#a07040", lw=0.8, alpha=0.8)
    add_box(ax, AX_ROTOR - (AUGER_OD / 2 - 2), ROTOR_BOTTOM_Z + 5,
            AUGER_OD - 4, AUGER_LEN - 8, fc="#e8c898", alpha=0.3)

    # Top loading slots
    ax.plot([AX_ROTOR - 6.5, AX_ROTOR - 2.5],
            [AUGER_TOP_Z, AUGER_TOP_Z], color="black", lw=2.0)
    ax.plot([AX_ROTOR + 2.5, AX_ROTOR + 6.5],
            [AUGER_TOP_Z, AUGER_TOP_Z], color="black", lw=2.0)
    ax.text(AX_ROTOR + AUGER_OD / 2 + 5, AUGER_TOP_Z,
            "4× sectoral\nloading slots\n(PR-#16 v4 top cap)",
            fontsize=6.5, va="center")

    # Bearing collar profile
    add_box(ax, SPINE_T / 2, 0, COLLAR_FLANGE_T, COLLAR_H,
            fc="#dcdcea", alpha=0.5)
    add_box(ax, SPINE_T / 2 + COLLAR_FLANGE_T, 0, COLLAR_OD, COLLAR_H,
            fc="#cfd8e3", alpha=0.5)
    brg_x0 = SPINE_T / 2 + COLLAR_FLANGE_T + (COLLAR_OD - BRG_OD) / 2
    add_box(ax, brg_x0, (COLLAR_H - BRG_T) / 2, BRG_OD, BRG_T,
            fc="#9aa0a6", alpha=0.7, label="bearing")

    # Falling powder
    for k, dz in enumerate(range(-40, -100, -8)):
        ax.add_patch(mpatches.Circle((AX_ROTOR + (k % 2 - 0.5) * 1.5, dz), 0.8,
                                     fc="#d0a060", ec="#a07040", lw=0.3))
    ax.annotate("", xy=(AX_ROTOR, -110), xytext=(AX_ROTOR, ROTOR_BOTTOM_Z),
                arrowprops=dict(arrowstyle="->", color="#a07040", lw=1.4))

    # Cup
    cup_y = -135
    ax.plot([AX_ROTOR - 35, AX_ROTOR - 35, AX_ROTOR + 35, AX_ROTOR + 35],
            [cup_y + 25, cup_y, cup_y, cup_y + 25],
            color="#444", lw=1.2)
    ax.text(AX_ROTOR, cup_y + 10,
            "shared collection cup\n(load cell — v1.2)",
            fontsize=6.5, ha="center", va="center")

    # Stage callouts
    label_to(ax, AX_ROTOR,
             AUGER_TOP_Z + CART_BASE_H + CART_NECK_H + CART_HOPPER_H * 0.5,
             AX_ROTOR - 100, AUGER_TOP_Z + CART_BASE_H + 30,
             "(1) reservoir holds bulk powder")
    label_to(ax, AX_ROTOR, AUGER_TOP_Z,
             AX_ROTOR - 100, AUGER_TOP_Z - 25,
             "(2) gravity feeds through\nrotor's top loading slots")
    label_to(ax, AX_ROTOR + AUGER_OD / 2,
             ROTOR_BOTTOM_Z + AUGER_LEN / 2,
             AX_ROTOR - 100, ROTOR_BOTTOM_Z + AUGER_LEN / 2,
             "(3) helical channel meters\nby step count\n(NEMA 11 + GT2 belt)")
    label_to(ax, AX_ROTOR, -65,
             AX_ROTOR - 100, -65,
             "(4) protruding exit nozzle\ndelivers powder past\nthe frame at any tilt")

    ax.set_xlim(-110, 200)
    ax.set_ylim(-160, 410)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# ============================================================================
# Render
# ============================================================================
fig, axes = plt.subplots(1, 3, figsize=(18, 12),
                         gridspec_kw={"width_ratios": [1, 0.7, 1]})
draw_side_panel(axes[0])
draw_front_panel(axes[1])
draw_flow_panel(axes[2])
fig.suptitle(
    "Single-channel powder-doser module — v2 (review-feedback round)\n"
    "spine + bearing-coupled collar + side belt drive + cartridge + adjustable cradle",
    fontsize=11, y=0.995,
)
fig.tight_layout(rect=(0, 0, 1, 0.97))

OUT = Path(__file__).parent / "renders" / "single_channel_module_sketch.png"
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print(f"wrote {OUT}")

# Standalone larger powder-flow figure
fig2, ax2 = plt.subplots(figsize=(8, 13))
draw_flow_panel(ax2)
fig2.suptitle(
    "Powder-flow path through the v2 module (cross-section)\n"
    "address of PR review #3228854193",
    fontsize=11, y=0.995,
)
fig2.tight_layout(rect=(0, 0, 1, 0.97))
OUT2 = Path(__file__).parent / "renders" / "single_channel_module_powder_flow.png"
fig2.savefig(OUT2, dpi=150, bbox_inches="tight")
print(f"wrote {OUT2}")

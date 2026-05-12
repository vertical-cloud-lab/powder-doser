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
ERM_PAD_W = 14.0
ERM_PAD_H = 14.0

COLLAR_OD = 50.0
COLLAR_H = 16.0
COLLAR_FLANGE_T = 6.0

SPINE_W = 90.0
SPINE_T = 10.0
SPINE_H = 360.0

CART_BASE_OD = 36.0
CART_BASE_H = 12.0
CART_HOPPER_OD = 60.0
CART_HOPPER_H = 60.0
CART_NECK_H = 6.0

CRADLE_PIVOT_Z = 200.0
CRADLE_BASE_T = 8.0
CRADLE_BASE_W = 140.0
CHEEK_W = 80.0
CHEEK_H = 220.0

# v3: belt drive moved DOWN to just above the bearing collar (S2 fix).
BELT_PLANE_Z = COLLAR_H + 4.0
# v3: ERM coin moved off-axis to a side pad on the -Y face of the collar.
ERM_PAD_Y_OFFSET = -(COLLAR_OD / 2 + ERM_PAD_T / 2 - 0.4)

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
    # v3: ERM coin moved off-axis to a side pad on -Y face of the collar
    # (S2 fix: was directly under the rotor in v2). Drawn as the side pad
    # plus the coin glued to its outer face. In side-view (looking along +Y)
    # the coin appears edge-on at COLLAR mid-height, just outside the collar.
    add_box(ax, AX_ROTOR + COLLAR_OD / 2 - 0.4, COLLAR_H / 2 - ERM_PAD_W / 2,
            ERM_PAD_T, ERM_PAD_W, fc="#cfd8e3", alpha=0.7)
    add_box(ax, AX_ROTOR + COLLAR_OD / 2 - 0.4 + ERM_PAD_T,
            COLLAR_H / 2 - ERM_D / 2,
            ERM_T, ERM_D, fc="#f0c080",
            label="ERM coin\n(side pad,\noff-axis)")

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

    # v3: GT2 pulley moved to BELT_PLANE_Z (just above the bearing collar)
    # so the belt path is BELOW the cartridge, not under it (S2 fix).
    pulley_z0 = BELT_PLANE_Z
    add_box(ax, AX_ROTOR - PULLEY_FLANGE_OD / 2, pulley_z0,
            PULLEY_FLANGE_OD, PULLEY_H, fc="#bbbbbb", alpha=0.7,
            label="GT2 pulley\n(16T,\nlow position)")
    ax.text(-90, 280,
            "v3 BELT MOVED LOW:\nNEMA 11 + GT2 belt drive\n"
            "now sits in the BELT_PLANE_Z plane,\n"
            "BELOW the cartridge (S2 fix).\n"
            "Cartridge top is unobstructed\nfor refills.",
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
    # v3: motor-bracket inserts moved to LOW Z (foot of L-bracket sits at
    # Z ~ BELT_PLANE_Z - 30 ± 15) so the belt plane is below the cartridge.
    foot_centre_z = BELT_PLANE_Z + PULLEY_H + 4.0 - 30.0
    for dy in (+30, -30):
        for dz in (+15, -15):
            add_circle(ax, dy, foot_centre_z + dz, 2.25,
                       fc="white", ec="black", lw=0.6)
    add_circle(ax, 0, CRADLE_PIVOT_Z, 2.7, fc="#fcfcfc", ec="black", lw=0.6)
    ax.text(SPINE_W / 2 + 4, CRADLE_PIVOT_Z, "M5 pivot\n(+ NEMA 17 worm\ndrive on +Y side)",
            fontsize=6.5, va="center")
    ax.text(SPINE_W / 2 + 4, foot_centre_z,
            "motor bracket\n(4× M3 inserts,\nLOW Z; belt below cartridge)",
            fontsize=6.5, va="center")
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

    # ---- Continuous powder-flow path: numbered nodes + chained arrow ----
    # Addresses @swcharles' ask in PR-#35 comment 4276136447 to "include a
    # continuous arrow to show where the powder flows" with "nodes to show
    # the process". Each node is a numbered circle; a single curved-arrow
    # path links them in flow order so the eye can follow the powder's
    # journey hopper → slots → helix → nozzle → cup without rereading.
    nodes = [
        (1, AX_ROTOR,
         AUGER_TOP_Z + CART_BASE_H + CART_NECK_H + CART_HOPPER_H * 0.55,
         "reservoir\n(bulk powder)"),
        (2, AX_ROTOR, AUGER_TOP_Z + 4,
         "top loading slots\n(PR-#16 v4 cap)"),
        (3, AX_ROTOR, ROTOR_BOTTOM_Z + AUGER_LEN / 2,
         "helical channel\n(NEMA 11 + GT2 belt\nmeters by step count)"),
        (4, AX_ROTOR, ROTOR_BOTTOM_Z + 5,
         "exit nozzle\n(protrudes past frame)"),
        (5, AX_ROTOR, cup_y + 12,
         "shared collection cup\n(load cell — v1.2)"),
    ]
    for n, nx, ny, lbl in nodes:
        ax.add_patch(mpatches.Circle((nx, ny), 4.5, facecolor="#fff3c4",
                                     edgecolor="#a07040", lw=1.2, zorder=5))
        ax.text(nx, ny, str(n), ha="center", va="center",
                fontsize=8, fontweight="bold", color="#604020", zorder=6)
        ax.text(nx - 100, ny, lbl, ha="left", va="center", fontsize=6.5)
        ax.annotate("", xy=(nx - 8, ny), xytext=(nx - 60, ny),
                    arrowprops=dict(arrowstyle="-", color="0.55", lw=0.5))
    # Chained continuous arrows between consecutive nodes
    for (_, x0, y0, _l0), (_, x1, y1, _l1) in zip(nodes, nodes[1:]):
        ax.annotate("",
                    xy=(x1 + 4.5, y1 + (5 if y1 > y0 else -5)),
                    xytext=(x0 + 4.5, y0 - (5 if y1 < y0 else -5)),
                    arrowprops=dict(arrowstyle="->", color="#a07040",
                                    lw=1.6, connectionstyle="arc3,rad=0.18"),
                    zorder=4)

    # ---- Scale bar (10 mm reference) -----------------------------------
    # Addresses @swcharles' "include a generic cup and scale for context"
    # ask. Cup is already drawn above; this gives an unambiguous size key.
    sx0, sy = 60, -155
    ax.plot([sx0, sx0 + 10], [sy, sy], color="black", lw=2)
    ax.plot([sx0, sx0], [sy - 2, sy + 2], color="black", lw=2)
    ax.plot([sx0 + 10, sx0 + 10], [sy - 2, sy + 2], color="black", lw=2)
    ax.text(sx0 + 5, sy - 6, "10 mm", ha="center", va="top", fontsize=6.5)

    ax.set_xlim(-110, 200)
    ax.set_ylim(-170, 410)
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


# ----------------------------------------------------------------------------
# Tilt-sweep figure (addresses @swcharles' PR-#35 comment 4276136447 ask for
# "an image of the auger at 90, 45, and 0 degrees"). Same simplified
# side-elevation outline rendered three times, rotated about the M5 trunnion
# pivot at the cradle's detent positions. 0° = vertical, 75° = closest to
# horizontal the cradle locks at (the v2 cradle's full range is 0–75°; 90°
# is shown extrapolated for context as a dashed outline).
# ----------------------------------------------------------------------------
def _module_outline_pts():
    """Return a list of (x, z) polygon vertices tracing the module's
    side-elevation envelope: spine + collar + protruding rotor + cartridge.
    Used by the tilt-sweep figure so we can rotate one polygon per angle."""
    spine = [(-SPINE_T / 2, 0), (SPINE_T / 2, 0),
             (SPINE_T / 2, SPINE_H), (-SPINE_T / 2, SPINE_H)]
    rotor_x0 = AX_ROTOR - AUGER_OD / 2
    rotor = [(rotor_x0, ROTOR_BOTTOM_Z),
             (rotor_x0 + AUGER_OD, ROTOR_BOTTOM_Z),
             (rotor_x0 + AUGER_OD, ROTOR_BOTTOM_Z + AUGER_LEN + 6),
             (rotor_x0, ROTOR_BOTTOM_Z + AUGER_LEN + 6)]
    cart_x0 = AX_ROTOR - CART_HOPPER_OD / 2
    cart_z0 = AUGER_TOP_Z + CART_BASE_H + CART_NECK_H
    cart = [(cart_x0, cart_z0),
            (cart_x0 + CART_HOPPER_OD, cart_z0),
            (cart_x0 + CART_HOPPER_OD, cart_z0 + CART_HOPPER_H),
            (cart_x0, cart_z0 + CART_HOPPER_H)]
    return spine, rotor, cart


def _rotate(pts, deg, cx, cz):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, z in pts:
        dx, dz = x - cx, z - cz
        out.append((cx + ca * dx - sa * dz, cz + sa * dx + ca * dz))
    return out


def draw_tilt_panel(ax, angle_deg, *, dashed=False):
    ax.set_aspect("equal")
    ax.set_title(f"{angle_deg}° tilt", fontsize=10)
    spine, rotor, cart = _module_outline_pts()
    pivot = (0.0, CRADLE_PIVOT_Z)
    style = dict(fc="#dcdcea", ec="0.4", lw=1.0,
                 linestyle="--" if dashed else "-",
                 alpha=0.5 if dashed else 1.0)
    ax.add_patch(mpatches.Polygon(_rotate(spine, angle_deg, *pivot), **style))
    ax.add_patch(mpatches.Polygon(_rotate(rotor, angle_deg, *pivot),
                                  fc="#fff4cc", ec="0.4", lw=1.0,
                                  linestyle="--" if dashed else "-",
                                  alpha=0.5 if dashed else 0.8))
    ax.add_patch(mpatches.Polygon(_rotate(cart, angle_deg, *pivot),
                                  fc="#f8e5b0", ec="0.4", lw=1.0,
                                  linestyle="--" if dashed else "-",
                                  alpha=0.5 if dashed else 0.8))
    # Cradle base (always horizontal)
    ax.add_patch(mpatches.Rectangle((-CRADLE_BASE_W / 2, -10 - CRADLE_BASE_T),
                                    CRADLE_BASE_W, CRADLE_BASE_T,
                                    fc="#bcd4bc", ec="0.4", lw=1.0))
    ax.add_patch(mpatches.Circle(pivot, 3.0, fc="white", ec="black", lw=0.8))
    # Generic cup placed under the rotor exit nozzle's projected ground hit
    nozzle_world = _rotate([(AX_ROTOR, ROTOR_BOTTOM_Z)], angle_deg, *pivot)[0]
    cup_y = -10 - CRADLE_BASE_T - 30
    cup_cx = nozzle_world[0]
    ax.plot([cup_cx - 30, cup_cx - 30, cup_cx + 30, cup_cx + 30],
            [cup_y + 25, cup_y, cup_y, cup_y + 25],
            color="#444", lw=1.2)
    ax.text(cup_cx, cup_y + 10, "cup", ha="center", va="center", fontsize=7)
    # Falling-powder arrow from nozzle straight down to cup rim
    if not dashed:
        ax.annotate("", xy=(cup_cx, cup_y + 25),
                    xytext=(nozzle_world[0], nozzle_world[1]),
                    arrowprops=dict(arrowstyle="->", color="#a07040", lw=1.2))
    ax.set_xlim(-260, 260)
    ax.set_ylim(-90, 430)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


fig3, axes3 = plt.subplots(1, 4, figsize=(20, 8))
draw_tilt_panel(axes3[0], 0)
draw_tilt_panel(axes3[1], 45)
draw_tilt_panel(axes3[2], 75)
# 90° is now within the cradle's locked range — actuated by the tilt drive.
draw_tilt_panel(axes3[3], 90)
axes3[3].set_title("90° tilt (horizontal\ndispense, in v3 range 0–90°)",
                   fontsize=9)
fig3.suptitle(
    "Auger orientation through the v3 cradle's tilt range — actuated by\n"
    "NEMA 17 + worm gearbox at +Y trunnion (no human intervention needed)\n"
    "addresses PR-#35 comment 4276136447 — \"image of the auger at 90, 45, and 0 degrees\"",
    fontsize=11, y=0.99,
)
fig3.tight_layout(rect=(0, 0, 1, 0.95))
OUT3 = Path(__file__).parent / "renders" / "single_channel_module_tilt_sweep.png"
fig3.savefig(OUT3, dpi=150, bbox_inches="tight")
print(f"wrote {OUT3}")

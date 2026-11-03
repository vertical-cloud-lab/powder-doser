"""Generate a dimensioned engineering drawing of the baseplate.

Produces ``views/baseplate_dimensions.png`` — a three-view engineering
drawing (top, front, side) of the trapezoidal-tripod baseplate, with all
governing dimensions called out in the style of a typical mechanical
drawing.  All values are sourced from ``cad_model.py`` (the source of
truth), so the drawing stays in lock-step with the printed CAD.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle


# --------------------------------------------------------------------- #
# Dimensions (mirrors cad_model.py — single source of truth).           #
# --------------------------------------------------------------------- #
# Rectangular forward-only mounting tab (legs + most of the rear are
# gone per Will's comment 4721011696).
BASE_FRONT_HALF_W = 100.0           # ±100 mm at the front edge
BASE_REAR_HALF_W = 100.0            # ±100 mm at the rear edge (rectangular)
BASE_Y_FRONT = 115.0                # front edge Y (toward dispense)
BASE_Y_REAR = +55.0                 # rear  edge Y (tab shortened per review)
BASE_T = 6.0                        # tabletop thickness
BASE_REAR_CHAMFER = 25.0            # 45° chamfer on the two rear corners

# Legs removed.
BASE_LEG_W = 0.0
BASE_LEG_H = 0.0
BASE_LEG_INSET = 0.0
FRONT_LEG_X = 79.0                  # historical X used by the flange
FRONT_LEG_Y = BASE_Y_FRONT - 21.0   # legacy reference (not drawn)
REAR_LEG_X = 0.0
REAR_LEG_Y = BASE_Y_REAR + 21.0     # legacy reference (not drawn)

# Four M5 mounting holes near the four tab corners (per Will's review
# pullrequestreview-4509355231 — "match the green holes in the drawing").
BASE_MOUNT_HOLE_DIA = 5.4
BASE_MOUNT_HOLE_X = 80.0                                 # ±80 (near corners)
BASE_MOUNT_HOLE_Y_REAR = BASE_Y_REAR + 13.0             # +68 (clear of chamfer)
BASE_MOUNT_HOLE_Y_FRONT = BASE_Y_FRONT - 10.0          # +105 (front corners)

# Hinge arms (forward-and-up, one each side of the auger).
HINGE_EYE_OD = 18.0
HINGE_EYE_ID = 5.4                  # M5 clearance pin
AUGER_GAP_W = 24.0                  # mounting-plate centre slot
PLATE_X_MAX = 54.1
HINGE_LAYER_GAP = 0.4
HINGE_LOBE_W = ((PLATE_X_MAX - 0.0) - (AUGER_GAP_W / 2.0)) / 3.0      # ≈12.68
HINGE_X0 = AUGER_GAP_W / 2.0                                           # 12.00
HINGE_X1 = HINGE_X0 + HINGE_LOBE_W                                     # ≈24.68
HINGE_X2 = HINGE_X0 + 2.0 * HINGE_LOBE_W                               # ≈37.37
ARM_X_LO_POS = HINGE_X1 + HINGE_LAYER_GAP / 2.0                        # ≈24.88
ARM_X_HI_POS = HINGE_X2 - HINGE_LAYER_GAP / 2.0                        # ≈37.17
ARM_BASE_SUPPORT_LEN = 35.0       # reduced from 40 per comment 4721011696
ARM_SLOPE_RUN = 16.0
Y_DISP = 125.0                      # hinge axis Y (= dispense end)
Z_AUG = 29.25                       # hinge axis Z (absolute)
Z_BASE_TOP = -14.0                  # baseplate-body BOTTOM in absolute Z
HINGE_AXIS_Z_LOCAL = Z_AUG - Z_BASE_TOP                                # 43.25
ARM_BACK_Y = BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN                       # +80
SLOPE_TOP_Y = ARM_BACK_Y + ARM_SLOPE_RUN                               # +96

# DUAL MG996R servo mounts — +X side and mirrored -X side (per Will's
# comment 4721011696).
DRIVE_HEAD_OVERHANG = 5.0
GEAR_HINGE_TIP_D = 38.92            # 28-T m≈1.298 (was 38.17 @ 40-T m≈0.908)
GEAR_X_HI = (HINGE_X2 + HINGE_LAYER_GAP / 2.0 + PLATE_X_MAX) / 2.0 \
            + (HINGE_LOBE_W - HINGE_LAYER_GAP) / 2.0                   # ≈ 54.0
SERVO_WALL_X = GEAR_X_HI + DRIVE_HEAD_OVERHANG                         # ≈ 59.0
SERVO_WALL_T = 6.0
MG996R_BODY_L = 40.0
MG996R_BODY_H = 36.8                # along +X, from flange face
MG996R_BODY_T = 20.0                # along Z
MG996R_HOLE_DIA = 5.0
MG996R_HOLE_Y_SPREAD = 49.5
MG996R_HOLE_Z_SPREAD = 10.0
MG996R_SPLINE_Y_OFFSET = 10.1
SERVO_BODY_X_LO = SERVO_WALL_X
SERVO_BODY_X_HI = SERVO_BODY_X_LO + MG996R_BODY_H                      # ≈ 95.8
SERVO_BODY_Y_LO = Y_DISP - MG996R_SPLINE_Y_OFFSET                      # +114.9
SERVO_BODY_Y_HI = SERVO_BODY_Y_LO + MG996R_BODY_L                      # +154.9
SERVO_POST_W_Y = 14.0
SERVO_GAP_CLEAR = 0.5
NEAR_POST_Y_HI = SERVO_BODY_Y_LO - SERVO_GAP_CLEAR                     # +114.4
NEAR_POST_Y_LO = NEAR_POST_Y_HI - SERVO_POST_W_Y                       # +100.4
FAR_POST_Y_LO = SERVO_BODY_Y_HI + SERVO_GAP_CLEAR                      # +155.4
FAR_POST_Y_HI = FAR_POST_Y_LO + SERVO_POST_W_Y                         # +169.4
POST_Y_GAP = FAR_POST_Y_LO - NEAR_POST_Y_HI                            # = 41.0
PINION_Y = Y_DISP
PINION_Z_ABOVE_BASE_TOP = 10.0
PINION_Z_LOCAL = BASE_T + PINION_Z_ABOVE_BASE_TOP                      # 16.0
POST_Z_HI = PINION_Z_LOCAL + MG996R_HOLE_Z_SPREAD / 2.0 + 5.0          # 26.0

# Porch (one each side).
PORCH_X_LO = SERVO_WALL_X                                              # 59.0
PORCH_X_HI = min(SERVO_BODY_X_HI + 1.0, BASE_FRONT_HALF_W)             # 96.8
PORCH_Y_LO = BASE_Y_FRONT - 2.0                                        # 113.0
PORCH_Y_HI = FAR_POST_Y_HI + 1.0                                       # 170.4

# Underside hanging flange + supportive triangle (per review
# pullrequestreview-4509355231): the triangle sits right under the servo
# mount, the M5 hole is drilled HORIZONTALLY (along Y) through it.
FLANGE_THK = 6.0
FLANGE_DEPTH = 40.0
FLANGE_X = 79.0                     # ±79 (one flange per side, mirrored)
FLANGE_GUSSET_THK = 10.0
FLANGE_GUSSET_RUN = 20.0
FLANGE_HOLE_DIA = 5.4
FLANGE_HOLE_Z_BELOW_BASE = 15.0
FLANGE_HOLE_X_INBOARD = 7.0

# Arm-clearance slots through the mounting plate (informational — slot is
# in the plate, not the baseplate, but the slot Y bound depends on the
# baseplate's arm geometry).
ARM_SLOT_Y_BACK = ARM_BACK_Y - 2.0                                     # +78


# --------------------------------------------------------------------- #
# Drawing helpers — ANSI-style linear dimension with extension lines    #
# and arrowheads.                                                       #
# --------------------------------------------------------------------- #
LINE_COLOR = "#222222"
DIM_COLOR = "#1f6feb"
HIDDEN_COLOR = "#888888"
FILL_FACE = "#f4f4f4"


def _arrow(ax, p0, p1, color=DIM_COLOR):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle="<|-|>", mutation_scale=8,
        color=color, linewidth=0.8, shrinkA=0, shrinkB=0,
    ))


def hdim(ax, x0, x1, y, label, *, ext_from=None, ext_len=4, off=0,
         text_above=True, fontsize=8):
    """Horizontal dimension between x0 and x1 at line height y.

    ``ext_from`` is the y of the feature being dimensioned (extension
    lines run from feature → dimension line).  ``off`` slides the text
    label sideways from the midpoint.
    """
    if ext_from is None:
        ext_from = y - ext_len if y >= 0 else y + ext_len
    # Extension lines.
    ax.plot([x0, x0], [ext_from, y], color=DIM_COLOR, linewidth=0.5)
    ax.plot([x1, x1], [ext_from, y], color=DIM_COLOR, linewidth=0.5)
    # Dimension line + arrows.
    _arrow(ax, (x0, y), (x1, y))
    xm = (x0 + x1) / 2.0 + off
    va = "bottom" if text_above else "top"
    dy = 1.0 if text_above else -1.0
    ax.text(xm, y + dy, label, ha="center", va=va, fontsize=fontsize,
            color=DIM_COLOR)


def vdim(ax, y0, y1, x, label, *, ext_from=None, ext_len=4, off=0,
         text_right=True, fontsize=8):
    """Vertical dimension between y0 and y1 at line position x."""
    if ext_from is None:
        ext_from = x - ext_len if x >= 0 else x + ext_len
    ax.plot([ext_from, x], [y0, y0], color=DIM_COLOR, linewidth=0.5)
    ax.plot([ext_from, x], [y1, y1], color=DIM_COLOR, linewidth=0.5)
    _arrow(ax, (x, y0), (x, y1))
    ym = (y0 + y1) / 2.0 + off
    ha = "left" if text_right else "right"
    dx = 1.0 if text_right else -1.0
    ax.text(x + dx, ym, label, ha=ha, va="center", fontsize=fontsize,
            color=DIM_COLOR, rotation=90)


def leader(ax, p_feature, p_text, label, *, fontsize=8, ha="left"):
    """Leader line from the feature to a text callout."""
    ax.annotate(
        label, xy=p_feature, xytext=p_text, fontsize=fontsize,
        color=DIM_COLOR, ha=ha, va="center",
        arrowprops=dict(arrowstyle="->", color=DIM_COLOR, linewidth=0.6,
                        shrinkA=0, shrinkB=2),
    )


def rect(ax, x, y, w, h, *, edge=LINE_COLOR, face=FILL_FACE, lw=1.2,
         hatch=None, ls="-"):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge,
                           linewidth=lw, hatch=hatch, linestyle=ls))


def polygon(ax, pts, *, edge=LINE_COLOR, face=FILL_FACE, lw=1.2, ls="-"):
    ax.add_patch(Polygon(pts, closed=True, facecolor=face, edgecolor=edge,
                         linewidth=lw, linestyle=ls))


def circle(ax, cx, cy, r, *, edge=LINE_COLOR, face="none", lw=1.0, ls="-"):
    ax.add_patch(Circle((cx, cy), r, edgecolor=edge, facecolor=face,
                        linewidth=lw, linestyle=ls))


def centerlines(ax, cx, cy, r, *, color="#888888", lw=0.5):
    ax.plot([cx - r * 1.4, cx + r * 1.4], [cy, cy],
            color=color, linewidth=lw, linestyle=(0, (6, 2, 1, 2)))
    ax.plot([cx, cx], [cy - r * 1.4, cy + r * 1.4],
            color=color, linewidth=lw, linestyle=(0, (6, 2, 1, 2)))


# --------------------------------------------------------------------- #
# View builders.                                                        #
# --------------------------------------------------------------------- #
def draw_top_view(ax):
    """Plan view (looking down -Z): the trapezoidal tabletop, hinge arms,
    legs, porch, posts and mounting-hole pattern."""
    ax.set_title("TOP VIEW   (looking down −Z)", fontsize=10, loc="left",
                 pad=6)

    # Rectangular forward-only tabletop with chamfered REAR corners.
    c = BASE_REAR_CHAMFER
    polygon(ax, [
        (-BASE_FRONT_HALF_W, BASE_Y_FRONT),
        (+BASE_FRONT_HALF_W, BASE_Y_FRONT),
        (+BASE_FRONT_HALF_W, BASE_Y_REAR + c),
        (+BASE_REAR_HALF_W - c, BASE_Y_REAR),
        (-BASE_REAR_HALF_W + c, BASE_Y_REAR),
        (-BASE_FRONT_HALF_W, BASE_Y_REAR + c),
    ])

    # Mirrored porches (one each side, fused to the front edge under the
    # servo footprint).
    for sx in (+1, -1):
        rect(ax, sx * PORCH_X_LO if sx > 0 else -PORCH_X_HI,
             PORCH_Y_LO,
             PORCH_X_HI - PORCH_X_LO, PORCH_Y_HI - PORCH_Y_LO,
             face="#eaf2ff")

    # Four M5 rear-corner mounting holes (corners of a 60 × 60 mm square).
    for hx in (-BASE_MOUNT_HOLE_X, +BASE_MOUNT_HOLE_X):
        for hy in (BASE_MOUNT_HOLE_Y_REAR, BASE_MOUNT_HOLE_Y_FRONT):
            circle(ax, hx, hy, BASE_MOUNT_HOLE_DIA / 2.0, lw=0.8)
            centerlines(ax, hx, hy, BASE_MOUNT_HOLE_DIA, lw=0.4)

    # Two hinge arms (footprint on the tabletop).
    for sign in (-1, +1):
        x_lo = sign * (ARM_X_LO_POS if sign > 0 else ARM_X_HI_POS)
        x_hi = sign * (ARM_X_HI_POS if sign > 0 else ARM_X_LO_POS)
        if x_lo > x_hi:
            x_lo, x_hi = x_hi, x_lo
        rect(ax, x_lo, ARM_BACK_Y, x_hi - x_lo, Y_DISP - ARM_BACK_Y,
             face="#fff5e6", lw=1.0)

    # Mirrored servo posts (two per side, four total).
    for sx in (+1, -1):
        for y_lo, y_hi in [(NEAR_POST_Y_LO, NEAR_POST_Y_HI),
                           (FAR_POST_Y_LO, FAR_POST_Y_HI)]:
            post_x_lo = sx * SERVO_WALL_X if sx > 0 else -(SERVO_WALL_X + SERVO_WALL_T)
            rect(ax, post_x_lo, y_lo, SERVO_WALL_T, y_hi - y_lo,
                 face="#dbe9ff", lw=1.0)
            ym = (y_lo + y_hi) / 2.0
            cx = post_x_lo + SERVO_WALL_T / 2.0
            circle(ax, cx, ym,
                   MG996R_HOLE_DIA / 2.0, lw=0.8)

    # Pinion centreline marks (one each side).
    for sx in (+SERVO_WALL_X, -SERVO_WALL_X):
        circle(ax, sx, PINION_Y, 0.7, edge=DIM_COLOR, face=DIM_COLOR, lw=0)

    # Flange + triangle footprints (downstand, shown dashed since they
    # hang below; now positioned UNDER the servo body per the review).
    for sx in (-FLANGE_X, +FLANGE_X):
        rect(ax, sx - FLANGE_THK / 2, SERVO_BODY_Y_LO, FLANGE_THK,
             SERVO_BODY_Y_HI - SERVO_BODY_Y_LO,
             face="none", edge=HIDDEN_COLOR, lw=0.8, ls=(0, (4, 2)))
        # triangle (gusset) footprint — thickness FLANGE_GUSSET_THK in Y,
        # centred under the servo body, running inboard from the flange.
        g_yc = (SERVO_BODY_Y_LO + SERVO_BODY_Y_HI) / 2.0
        g_x_in = sx - (FLANGE_GUSSET_RUN if sx > 0 else -FLANGE_GUSSET_RUN)
        rect(ax, min(sx, g_x_in), g_yc - FLANGE_GUSSET_THK / 2,
             abs(sx - g_x_in), FLANGE_GUSSET_THK,
             face="none", edge=HIDDEN_COLOR, lw=0.8, ls=(0, (2, 2)))
        # horizontal M5 mounting hole (axis along Y) through the triangle.
        hx = sx - (FLANGE_HOLE_X_INBOARD if sx > 0 else -FLANGE_HOLE_X_INBOARD)
        circle(ax, hx, g_yc, FLANGE_HOLE_DIA / 2.0, lw=0.7,
               edge=HIDDEN_COLOR, ls=(0, (2, 2)))

    # ---------------- Overall + tabletop dimensions (LEFT/BOTTOM stack) -
    # Overall front-edge width (200) — well above the front edge.
    hdim(ax, -BASE_FRONT_HALF_W, +BASE_FRONT_HALF_W, BASE_Y_FRONT + 32,
         "200.0   (front edge, = 2 × 100)",
         ext_from=BASE_Y_FRONT + 1)
    # Rear-edge width between chamfer corners (150 = 200 − 2 × 25).
    rear_half = BASE_REAR_HALF_W - BASE_REAR_CHAMFER
    hdim(ax, -rear_half, +rear_half, BASE_Y_REAR - 18,
         f"{2 * rear_half:.0f}   (rear edge, between chamfers)",
         ext_from=BASE_Y_REAR, text_above=False)
    # Front-to-rear depth (60) — far LEFT.
    vdim(ax, BASE_Y_REAR, BASE_Y_FRONT, -BASE_FRONT_HALF_W - 28,
         f"{BASE_Y_FRONT - BASE_Y_REAR:.1f}", ext_from=-BASE_FRONT_HALF_W - 2)
    # Y-coords of front / rear edges — far LEFT, outboard of the depth dim.
    vdim(ax, 0, BASE_Y_FRONT, -BASE_FRONT_HALF_W - 55, "Y = +115",
         ext_from=-BASE_FRONT_HALF_W - 38, text_right=False)
    vdim(ax, 0, BASE_Y_REAR, -BASE_FRONT_HALF_W - 55, f"Y = +{BASE_Y_REAR:.0f}",
         ext_from=-BASE_FRONT_HALF_W - 38, text_right=False)
    # 45° chamfer on the rear corners.
    leader(ax, (BASE_REAR_HALF_W - BASE_REAR_CHAMFER / 2,
                BASE_Y_REAR + BASE_REAR_CHAMFER / 2),
           (150, -25),
           f"2 × {BASE_REAR_CHAMFER:.0f} × 45°\n  rear-corner chamfer",
           ha="left", fontsize=7)

    # ---------------- M5 corner mounting holes --------------------------
    # X-pitch between the two columns of holes.
    hdim(ax, -BASE_MOUNT_HOLE_X, +BASE_MOUNT_HOLE_X,
         BASE_MOUNT_HOLE_Y_REAR - 12,
         f"{2 * BASE_MOUNT_HOLE_X:.0f}   (M5 hole X-pitch)",
         ext_from=BASE_MOUNT_HOLE_Y_REAR - 6, text_above=False,
         fontsize=7)
    # Y-pitch between front and rear row.
    vdim(ax, BASE_MOUNT_HOLE_Y_REAR, BASE_MOUNT_HOLE_Y_FRONT,
         BASE_MOUNT_HOLE_X + 14,
         f"{BASE_MOUNT_HOLE_Y_FRONT - BASE_MOUNT_HOLE_Y_REAR:.0f}"
         "   (M5 hole Y-pitch)",
         ext_from=BASE_MOUNT_HOLE_X + 6, fontsize=7)
    # Callout for the M5 mount holes.
    leader(ax, (-BASE_MOUNT_HOLE_X, BASE_MOUNT_HOLE_Y_REAR),
           (-150, -30),
           "4 × Ø5 THRU  (M5 clearance)\n"
           "  near-corner mount holes\n"
           f"  at X = ±{BASE_MOUNT_HOLE_X:.0f},"
           f" Y = +{BASE_MOUNT_HOLE_Y_REAR:.0f} / +"
           f"{BASE_MOUNT_HOLE_Y_FRONT:.0f}\n"
           "  for bolting to a separate frame",
           ha="left", fontsize=7)

    # ---------------- Hinge arms (single leader to the LEFT) ------------
    leader(ax, (ARM_X_LO_POS, (ARM_BACK_Y + Y_DISP) / 2),
           (-140, 145),
           "Hinge arms ×2\n"
           "  X-span:  ±[24.88 → 37.17]  (width 12.28)\n"
           "  Y-span:  +80 → +125\n"
           "  (arm depth reduced from 40 → 35;\n"
           "   carries M5 hinge pin; see side/front views)",
           ha="left", fontsize=7)

    # ---------------- Servo cluster (DUAL — RIGHT-SIDE stack) -----------
    # 5 mm drive-head overhang past front edge.
    hdim(ax, BASE_FRONT_HALF_W, SERVO_WALL_X - DRIVE_HEAD_OVERHANG,
         BASE_Y_FRONT - 18,
         "5.0  (drive-head overhang)",
         ext_from=BASE_Y_FRONT - 1, text_above=False, fontsize=7)
    # Porch X extent — ABOVE the porch.
    hdim(ax, PORCH_X_LO, PORCH_X_HI, PORCH_Y_HI + 8,
         "37.8  (porch X-extent)",
         ext_from=PORCH_Y_HI + 1, fontsize=7)
    # Porch Y extent — RIGHT of the porch.
    vdim(ax, PORCH_Y_LO, PORCH_Y_HI, PORCH_X_HI + 8,
         "57.4  (porch Y-depth)", ext_from=PORCH_X_HI + 1, fontsize=7)
    # Post gap (41) — INSIDE the gap.
    hdim(ax, NEAR_POST_Y_HI, FAR_POST_Y_LO,
         SERVO_WALL_X + SERVO_WALL_T / 2.0,
         "  41.0  (post gap)",
         ext_from=SERVO_WALL_X + SERVO_WALL_T,
         text_above=False, fontsize=7, off=2)
    # Single combined leader for the servo posts (note: DUAL — mirrored).
    leader(ax, (SERVO_WALL_X + SERVO_WALL_T, NEAR_POST_Y_LO + 2),
           (170, 50),
           "Servo posts ×4  (2 per side, mirrored ±X)\n"
           "  6.0 (X) × 14.0 (Y) × 20.0 (Z high)\n"
           "  2 × Ø5 thru per post\n"
           "  on 49.5 × 10 mm pattern\n"
           "  inboard face at X = ±59.0\n"
           "  DUAL-SERVO LIFT (per comment 4721011696)",
           ha="left", fontsize=7)

    # Flange + triangle callout (downstand, hidden in plan view).
    leader(ax, (-FLANGE_X, (SERVO_BODY_Y_LO + SERVO_BODY_Y_HI) / 2),
           (-200, -60),
           "Flanges ×2  (hidden, hang below baseplate)\n"
           "  YZ-plane rib at X = ±79, thk 6\n"
           "  drops 40 below baseplate bottom\n"
           "  + XZ-plane gusset (10 thk × 20 run)\n"
           "    right under the servo mount\n"
           "  + horizontal Ø5 M5 hole (axis ‖ Y)\n"
           "    through the gusset at the 0° datum",
           ha="left", fontsize=7)

    # Origin & axes — bottom-LEFT corner.
    ax.plot([0], [0], marker="+", color=LINE_COLOR, markersize=10,
            markeredgewidth=1.0)
    ax.text(2, 2, "  X=0, Y=0  (auger axis)", fontsize=7,
            color=LINE_COLOR)
    ax.annotate("", xy=(-128, -100), xytext=(-148, -100),
                arrowprops=dict(arrowstyle="->", color="black"))
    ax.text(-126, -100, "+X", fontsize=8, va="center")
    ax.annotate("", xy=(-148, -80), xytext=(-148, -100),
                arrowprops=dict(arrowstyle="->", color="black"))
    ax.text(-148, -76, "+Y", fontsize=8, ha="center")

    ax.set_aspect("equal")
    ax.set_xlim(-220, 230)
    ax.set_ylim(-115, 195)
    ax.set_xlabel("X  (mm)")
    ax.set_ylabel("Y  (mm)")
    ax.grid(True, which="both", linewidth=0.3, alpha=0.4)


def draw_front_view(ax):
    """Front view (looking from +Y → −Y): the trapezoid is foreshortened
    to its widest cross-section, so this shows the FRONT-EDGE width,
    tabletop thickness, leg height, hinge arms (silhouette) and posts."""
    ax.set_title("FRONT VIEW   (looking from +Y, toward −Y)",
                 fontsize=10, loc="left", pad=6)

    # Tabletop edge (front face is full width 200 mm).
    rect(ax, -BASE_FRONT_HALF_W, 0, 2 * BASE_FRONT_HALF_W, BASE_T,
         face=FILL_FACE)
    # Legs removed — none drawn in this iteration.

    # Hinge arms (silhouette: arm extruded along X; in front view we see
    # its tip — disc cap of Ø HINGE_EYE_OD around the hinge axis).
    for sign in (-1, +1):
        x_lo = sign * (ARM_X_LO_POS if sign > 0 else ARM_X_HI_POS)
        x_hi = sign * (ARM_X_HI_POS if sign > 0 else ARM_X_LO_POS)
        if x_lo > x_hi:
            x_lo, x_hi = x_hi, x_lo
        # arm body silhouette (rectangular column from BASE_T to hinge axis Z)
        rect(ax, x_lo, BASE_T, x_hi - x_lo,
             HINGE_AXIS_Z_LOCAL - BASE_T, face="#fff5e6", lw=1.0)
        # disc cap at the hinge axis
        circle(ax, (x_lo + x_hi) / 2.0, HINGE_AXIS_Z_LOCAL,
               HINGE_EYE_OD / 2.0, edge=LINE_COLOR, face="#fff0d4", lw=1.0)
        circle(ax, (x_lo + x_hi) / 2.0, HINGE_AXIS_Z_LOCAL,
               HINGE_EYE_ID / 2.0, edge=LINE_COLOR, face="white", lw=0.8)

    # Servo posts (silhouette in front view: rectangles at ±SERVO_WALL_X).
    for sx in (+1, -1):
        post_x_lo = sx * SERVO_WALL_X if sx > 0 else -(SERVO_WALL_X + SERVO_WALL_T)
        rect(ax, post_x_lo, BASE_T, SERVO_WALL_T,
             POST_Z_HI - BASE_T, face="#dbe9ff", lw=1.0)
        for dz in (-MG996R_HOLE_Z_SPREAD / 2.0, +MG996R_HOLE_Z_SPREAD / 2.0):
            circle(ax, post_x_lo + SERVO_WALL_T / 2.0,
                   PINION_Z_LOCAL + dz, MG996R_HOLE_DIA / 2.0, lw=0.8)

    # Mirrored underside flanges (downstand, in front view they project
    # as rectangles below the tabletop at X = ±FLANGE_X) + the supportive
    # triangle (gusset) that runs inboard right under the servo mount.
    for sx in (-FLANGE_X, +FLANGE_X):
        rect(ax, sx - FLANGE_THK / 2, -FLANGE_DEPTH,
             FLANGE_THK, FLANGE_DEPTH, face="#efe6ff", lw=1.0)
        # gusset triangle (XZ-plane) — top edge along baseplate bottom,
        # vertical edge down the flange, hypotenuse back up to the inboard
        # run; drawn as a silhouette polygon.
        g_in = sx - (FLANGE_GUSSET_RUN if sx > 0 else -FLANGE_GUSSET_RUN)
        polygon(ax, [(sx, 0.0), (g_in, 0.0), (sx, -FLANGE_DEPTH)],
                face="#e2d4ff", lw=0.9)
        # horizontal M5 mounting hole (axis ‖ Y) through the gusset.
        hx = sx - (FLANGE_HOLE_X_INBOARD if sx > 0 else -FLANGE_HOLE_X_INBOARD)
        circle(ax, hx, -FLANGE_HOLE_Z_BELOW_BASE,
               FLANGE_HOLE_DIA / 2.0, lw=0.8)

    # ---------------- Dimensions ----------------
    # Overall width 200 — placed HIGH so it clears the hinge caps.
    hdim(ax, -BASE_FRONT_HALF_W, +BASE_FRONT_HALF_W,
         HINGE_AXIS_Z_LOCAL + 32, "200.0",
         ext_from=HINGE_AXIS_Z_LOCAL + 12)
    # Outer-arm pitch — just BELOW the overall 200 dim.
    hdim(ax, -ARM_X_HI_POS, +ARM_X_HI_POS, HINGE_AXIS_Z_LOCAL + 18,
         "74.34  (outer arm pitch)",
         ext_from=HINGE_AXIS_Z_LOCAL + HINGE_EYE_OD / 2.0 + 1,
         fontsize=7)
    # Tabletop thickness 6 — far LEFT.
    vdim(ax, 0, BASE_T, -BASE_FRONT_HALF_W - 18, "6.0",
         ext_from=-BASE_FRONT_HALF_W - 1, fontsize=7)
    # Flange X position ±79 — placed BELOW so it clears tabletop dims.
    hdim(ax, -FLANGE_X, +FLANGE_X, -FLANGE_DEPTH - 12,
         "158.0  (flange C/L pitch, X = ±79)",
         ext_from=-FLANGE_DEPTH - 2, text_above=False)

    # Hinge axis Z — far RIGHT.
    vdim(ax, 0, HINGE_AXIS_Z_LOCAL, +BASE_FRONT_HALF_W + 22,
         "43.25  (hinge axis Z)",
         ext_from=+BASE_FRONT_HALF_W + 2)
    # Hinge eye OD/ID — leader to UPPER-LEFT into free space above tabletop.
    leader(ax, (-ARM_X_HI_POS - HINGE_EYE_OD / 2.0, HINGE_AXIS_Z_LOCAL),
           (-145, HINGE_AXIS_Z_LOCAL + 20),
           "Hinge eye\n  Ø18 OD / Ø5.4 ID  (M5 pin)",
           fontsize=7, ha="left")

    # ---- Servo post block (RIGHT side) -------------
    # Pinion spline Z above tabletop top (10) — INSIDE post on the LEFT,
    # short text only.
    vdim(ax, BASE_T, PINION_Z_LOCAL, SERVO_WALL_X - 3,
         "10", ext_from=SERVO_WALL_X - 1, text_right=False, fontsize=7)
    # Hole pattern Z spread (10) — RIGHT of the post.
    vdim(ax, PINION_Z_LOCAL - MG996R_HOLE_Z_SPREAD / 2.0,
         PINION_Z_LOCAL + MG996R_HOLE_Z_SPREAD / 2.0,
         SERVO_WALL_X + SERVO_WALL_T + 8,
         "10  (hole Z-pitch)",
         ext_from=SERVO_WALL_X + SERVO_WALL_T + 1, fontsize=7)
    # Post height + position composite leader.
    leader(ax, (SERVO_WALL_X + SERVO_WALL_T, POST_Z_HI - 4),
           (SERVO_WALL_X + 70, -42),
           "Servo posts  (×4 — 2 per side, mirrored ±X)\n"
           "  6.0 thick (X)  ×  20.0 high above tabletop\n"
           "  inboard face at X = ±59.0\n"
           "  4 × Ø5 thru per side on 49.5 × 10 mm pattern",
           fontsize=7, ha="left")

    # Flange callout (leader to LEFT-DOWN into open space below tabletop).
    leader(ax, (-FLANGE_X - FLANGE_THK / 2, -FLANGE_DEPTH / 2),
           (-148, -FLANGE_DEPTH - 8),
           "Flanges  (×2, mirrored ±X)\n"
           "  6 thk × 40 deep YZ-rib\n"
           "  + 10 × 20 XZ gusset under the servo mount\n"
           "  horizontal Ø5 M5 hole (axis ‖ Y) thru gusset\n"
           f"  hole centre Z = baseplate − {FLANGE_HOLE_Z_BELOW_BASE:.0f}",
           fontsize=7, ha="left")

    ax.set_aspect("equal")
    ax.set_xlim(-165, 200)
    ax.set_ylim(-115, 95)
    ax.set_xlabel("X  (mm)")
    ax.set_ylabel("Z  (mm,  baseplate-bottom = 0)")
    ax.grid(True, which="both", linewidth=0.3, alpha=0.4)


def draw_side_view(ax):
    """Side view (looking from +X → −X): the trapezoid foreshortens to a
    rectangle along Y (front Y=+115 → rear Y=−75); shows tabletop
    thickness, leg drop, hinge arm with sloped back face, porch, posts."""
    ax.set_title("SIDE VIEW   (looking from +X, toward −X)",
                 fontsize=10, loc="left", pad=6)

    # Tabletop (projected onto YZ).
    rect(ax, BASE_Y_REAR, 0, BASE_Y_FRONT - BASE_Y_REAR,
         BASE_T, face=FILL_FACE)
    # Porch (projects past front edge — shown as a forward extension).
    rect(ax, PORCH_Y_LO, 0, PORCH_Y_HI - PORCH_Y_LO, BASE_T,
         face="#eaf2ff")
    # Legs removed.

    # Hinge arm silhouette (sloped back face).
    polygon(ax, [
        (ARM_BACK_Y, BASE_T),
        (Y_DISP, BASE_T),
        (Y_DISP, HINGE_AXIS_Z_LOCAL),
        (SLOPE_TOP_Y, HINGE_AXIS_Z_LOCAL),
    ], face="#fff5e6", lw=1.0)
    # Disc-cap eye.
    circle(ax, Y_DISP, HINGE_AXIS_Z_LOCAL, HINGE_EYE_OD / 2.0,
           edge=LINE_COLOR, face="#fff0d4", lw=1.0)
    circle(ax, Y_DISP, HINGE_AXIS_Z_LOCAL, HINGE_EYE_ID / 2.0,
           edge=LINE_COLOR, face="white", lw=0.8)

    # Two servo posts.
    for y_lo, y_hi in [(NEAR_POST_Y_LO, NEAR_POST_Y_HI),
                       (FAR_POST_Y_LO, FAR_POST_Y_HI)]:
        rect(ax, y_lo, BASE_T, y_hi - y_lo, POST_Z_HI - BASE_T,
             face="#dbe9ff", lw=1.0)
    # MG996R body silhouette in the post gap (shown dashed — it's the
    # SERVO, not the printed part; included for reference).
    rect(ax, SERVO_BODY_Y_LO, BASE_T,
         SERVO_BODY_Y_HI - SERVO_BODY_Y_LO, MG996R_BODY_T,
         face="none", edge=HIDDEN_COLOR, lw=0.8, ls=(0, (4, 2)))
    # Spline cross-mark.
    ax.plot([PINION_Y], [PINION_Z_LOCAL], marker="+", color=DIM_COLOR,
            markersize=10, markeredgewidth=1.2)

    # Underside flange (in side view: a downstand rectangle below the
    # baseplate, spanning the servo body in Y, with the gusset + horizontal
    # M5 hole at its mid-length).
    flange_y_mid = (SERVO_BODY_Y_LO + SERVO_BODY_Y_HI) / 2.0
    polygon(ax, [
        (SERVO_BODY_Y_LO, 0),
        (SERVO_BODY_Y_HI, 0),
        (SERVO_BODY_Y_HI, -FLANGE_DEPTH),
        (SERVO_BODY_Y_LO, -FLANGE_DEPTH),
    ], face="#efe6ff", lw=1.0)
    # gusset is edge-on here (XZ-plane triangle) — mark its Y location.
    ax.plot([flange_y_mid, flange_y_mid], [0, -FLANGE_DEPTH],
            color=HIDDEN_COLOR, lw=0.8, ls=(0, (3, 2)))
    # horizontal M5 mounting hole (axis ‖ Y) — appears edge-on as a short
    # bore line at the hole Z.
    ax.plot([SERVO_BODY_Y_LO, SERVO_BODY_Y_HI],
            [-FLANGE_HOLE_Z_BELOW_BASE, -FLANGE_HOLE_Z_BELOW_BASE],
            color=HIDDEN_COLOR, lw=0.8, ls=(0, (2, 2)))

    # ---------------- Dimensions ----------------
    # Overall Y depth (front to rear of mounting tab) — placed HIGH.
    hdim(ax, BASE_Y_REAR, BASE_Y_FRONT, HINGE_AXIS_Z_LOCAL + 28,
         f"{BASE_Y_FRONT - BASE_Y_REAR:.1f}   (tab Y-depth)",
         ext_from=HINGE_AXIS_Z_LOCAL + 12)
    # Tabletop thickness 6 — far LEFT.
    vdim(ax, 0, BASE_T, BASE_Y_REAR - 14, "6.0",
         ext_from=BASE_Y_REAR - 1, fontsize=7)
    # Flange depth — far LEFT below.
    vdim(ax, -FLANGE_DEPTH, 0, BASE_Y_REAR - 14, "40.0  (flange depth)",
         ext_from=BASE_Y_REAR - 1, fontsize=7, text_right=False)

    # Arm base support length (35) — placed BELOW the tabletop.
    hdim(ax, ARM_BACK_Y, Y_DISP, BASE_T - 12,
         f"{ARM_BASE_SUPPORT_LEN:.0f}  (arm base support; reduced from 40)",
         ext_from=BASE_T,
         text_above=False, fontsize=7)
    # Slope run 16 — placed ABOVE the slope-top point.
    hdim(ax, ARM_BACK_Y, SLOPE_TOP_Y, HINGE_AXIS_Z_LOCAL + 8,
         "16  (slope run, ≈58°)",
         ext_from=HINGE_AXIS_Z_LOCAL + 1, fontsize=7)
    # Hinge axis Y/Z — leader UP-LEFT.
    leader(ax, (Y_DISP, HINGE_AXIS_Z_LOCAL),
           (Y_DISP + 30, HINGE_AXIS_Z_LOCAL + 26),
           "Hinge axis\n  Y = +125,  Z = +43.25  (local)\n"
           "  10 mm forward of front edge",
           fontsize=7, ha="left")

    # Post Z height (20) — RIGHT of far post.
    vdim(ax, BASE_T, POST_Z_HI, FAR_POST_Y_HI + 8,
         "20.0  (post H)", ext_from=FAR_POST_Y_HI + 1, fontsize=7)
    # Post gap 41 — placed HIGHER.
    hdim(ax, NEAR_POST_Y_HI, FAR_POST_Y_LO,
         POST_Z_HI + 22, "41.0  (post gap)",
         ext_from=POST_Z_HI + 1, fontsize=7)
    # Pinion spline callout.
    leader(ax, (PINION_Y, PINION_Z_LOCAL),
           (PINION_Y - 55, HINGE_AXIS_Z_LOCAL - 18),
           "spline  (Z = +10)", fontsize=7, ha="right")
    # Porch fwd-of-front-edge.
    hdim(ax, BASE_Y_FRONT, PORCH_Y_HI, BASE_T - 24,
         f"{PORCH_Y_HI - BASE_Y_FRONT:.1f}  (porch fwd of front edge)",
         ext_from=BASE_T, text_above=False, fontsize=7)

    # Flange + gusset + M5 hole callout.
    leader(ax, (flange_y_mid, -FLANGE_HOLE_Z_BELOW_BASE),
           (SERVO_BODY_Y_LO - 30, -FLANGE_DEPTH - 8),
           "Underside flange  (×2, mirrored ±X — see front view)\n"
           "  YZ-plane rib: 6 thk × 40 deep, under servo body\n"
           "  + 10 × 20 XZ-plane gusset right under the mount\n"
           f"  + horizontal Ø5 M5 hole (‖ Y) at Z = "
           f"−{FLANGE_HOLE_Z_BELOW_BASE:.0f}",
           fontsize=7, ha="left")

    # Rear M5 mounting hole indicator on the tabletop (shown by Y position).
    for hy in (BASE_MOUNT_HOLE_Y_REAR, BASE_MOUNT_HOLE_Y_FRONT):
        ax.plot([hy], [BASE_T / 2], marker="o", color=DIM_COLOR,
                markersize=4, markeredgewidth=0.8, markerfacecolor="white")
    leader(ax, (BASE_MOUNT_HOLE_Y_REAR, BASE_T),
           (BASE_MOUNT_HOLE_Y_REAR - 30, BASE_T + 12),
           "4 × Ø5 M5 corner mount holes\n"
           f"  (Y = +{BASE_MOUNT_HOLE_Y_REAR:.0f} and "
           f"+{BASE_MOUNT_HOLE_Y_FRONT:.0f},  X = ±{BASE_MOUNT_HOLE_X:.0f})",
           fontsize=7, ha="right")

    ax.set_aspect("equal")
    ax.set_xlim(-130, 215)
    ax.set_ylim(-115, 95)
    ax.set_xlabel("Y  (mm)")
    ax.set_ylabel("Z  (mm,  baseplate-bottom = 0)")
    ax.grid(True, which="both", linewidth=0.3, alpha=0.4)


def draw_title_block(ax):
    """Title block + general notes (tolerances, units, datum, finish)."""
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    # Outer frame.
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor="white",
                           edgecolor=LINE_COLOR, linewidth=1.2))
    # Vertical divider — notes on the LEFT, title/meta on the RIGHT.
    ax.plot([0.62, 0.62], [0, 1], color=LINE_COLOR, linewidth=0.8)
    # Right column horizontal dividers (title / part / material / units).
    for y in (0.78, 0.58, 0.38, 0.18):
        ax.plot([0.62, 1.0], [y, y], color=LINE_COLOR, linewidth=0.6)

    # Title cell.
    ax.text(0.81, 0.90, "BASEPLATE", fontsize=15, ha="center", va="center",
            weight="bold")
    ax.text(0.81, 0.82, "Mounting-Plate Assembly  /  Powder-Doser",
            fontsize=8, ha="center", va="center", color="#444")
    # Part / material / units.
    ax.text(0.635, 0.74, "PART", fontsize=7, color="#555", ha="left")
    ax.text(0.81, 0.68, "baseplate.stl / .step", fontsize=10,
            ha="center", va="center")
    ax.text(0.635, 0.54, "MATERIAL", fontsize=7, color="#555", ha="left")
    ax.text(0.81, 0.48, "PLA / PETG  (FDM print)", fontsize=10,
            ha="center", va="center")
    ax.text(0.635, 0.34, "UNITS", fontsize=7, color="#555", ha="left")
    ax.text(0.81, 0.28, "mm  (all dims)",
            fontsize=10, ha="center", va="center")
    ax.text(0.635, 0.14, "REVISION", fontsize=7, color="#555", ha="left")
    ax.text(0.81, 0.08, "PR #66 — issue #63", fontsize=9,
            ha="center", va="center")

    # Notes column.
    ax.text(0.02, 0.95, "GENERAL NOTES", fontsize=10, weight="bold",
            ha="left", va="top")
    notes = (
        "1.  All dimensions in millimetres.  Angles in degrees.\n"
        "\n"
        "2.  Tolerances (FDM, unless otherwise noted):\n"
        "        Linear dims:     ±0.30 mm   (≤ 50 mm)\n"
        "                                  ±0.50 mm   (> 50 mm)\n"
        "        Hole / bore Ø:   +0.20 / −0.10 mm\n"
        "        Angular:           ±1°\n"
        "\n"
        "3.  Datum:  auger axis (X = 0, Y = 0) at the hinge axis.\n"
        "        Hinge axis Z (absolute) = +29.25.\n"
        "        Baseplate-LOCAL Z origin = baseplate BOTTOM face;\n"
        "        baseplate TOP face = Z = +6.\n"
        "\n"
        "4.  Tabletop is a small forward-only RECTANGULAR mounting tab\n"
        "        with chamfered rear corners:\n"
        "        ±100 wide × Y ∈ [+55, +115] (60 mm Y-depth),\n"
        "        2 × 25 × 45° chamfer on the two rear corners.\n"
        "        Legs + most of the rear are GONE; the part bolts to\n"
        "        a separate frame via the corner M5 holes.\n"
        "\n"
        "5.  4 × Ø5 M5 mounting holes near the four tab corners\n"
        "        (X = ±80, Y = +68 and +105).\n"
        "\n"
        "6.  Hinge arms (×2) carry the shared M5 hinge pin.\n"
        "        Arm back face is sloped 16 mm run, ≈58° from horiz.\n"
        "        Arm base support shortened 40 → 35 (clears front bkt).\n"
        "        Validated 0.00 mm³ at 0° / 45° / 90°.\n"
        "\n"
        "7.  Servo posts (×2 per side, mirrored ±X — DUAL servo lift).\n"
        "        Holes are Ø5 thru on a 49.5 × 10 mm pattern\n"
        "        per side (clearance for M3 flange screws).\n"
        "        Driving-head tip hangs 5.0 mm past the front edge.\n"
        "        Pinion / hinge-gear mesh:  2 : 1, m ≈ 0.908,\n"
        "        C = 27.25 mm — gears NOT on this part (see assembly).\n"
        "\n"
        "8.  Underside flange (×2, mirrored ±X) at X = ±79, under the\n"
        "        servo mount:\n"
        "        YZ rib 6 thk × 40 deep (spans the servo body),\n"
        "        + XZ gusset 10 thk × 20 run right under the mount,\n"
        "        + horizontal Ø5 M5 hole (axis ‖ Y, 0° datum)\n"
        "        through the gusset at Z = −15.\n"
        "\n"
        "9.  All printed values traceable to cad_model.py."
    )
    ax.text(0.02, 0.91, notes, fontsize=7.0, ha="left", va="top",
            family="monospace", linespacing=1.30)


# --------------------------------------------------------------------- #
# Layout                                                                #
# --------------------------------------------------------------------- #
def main(out_path: str = "views/baseplate_dimensions.png") -> None:
    fig = plt.figure(figsize=(17, 22))
    gs = fig.add_gridspec(
        nrows=3, ncols=2,
        height_ratios=[1.55, 1.05, 1.10],
        width_ratios=[1.0, 1.0],
        hspace=0.22, wspace=0.18,
        left=0.05, right=0.97, top=0.97, bottom=0.04,
    )
    ax_top = fig.add_subplot(gs[0, :])
    ax_front = fig.add_subplot(gs[1, 0])
    ax_side = fig.add_subplot(gs[1, 1])
    ax_title = fig.add_subplot(gs[2, :])

    draw_top_view(ax_top)
    draw_front_view(ax_front)
    draw_side_view(ax_side)
    draw_title_block(ax_title)

    fig.suptitle(
        "BASEPLATE — DIMENSIONED DRAWING   "
        "(top / front / side views, all dims in mm)",
        fontsize=12, weight="bold", y=0.992,
    )
    fig.savefig(out_path, dpi=180, facecolor="white",
                bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    import os, sys
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    out = sys.argv[1] if len(sys.argv) > 1 else "views/baseplate_dimensions.png"
    main(out)

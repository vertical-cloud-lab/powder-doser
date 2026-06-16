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
# Tabletop trapezoid.
BASE_FRONT_HALF_W = 100.0           # ±100 mm at the front edge
BASE_REAR_HALF_W = 32.0             # ±32 mm at the rear edge
BASE_Y_FRONT = 115.0                # front edge Y (toward dispense)
BASE_Y_REAR = -75.0                 # rear  edge Y
BASE_T = 6.0                        # tabletop thickness

# Tripod legs.
BASE_LEG_W = 18.0                   # leg cross-section (square)
BASE_LEG_H = 95.0                   # leg height below the tabletop
BASE_LEG_INSET = 12.0               # inset from the local edge to leg face
FRONT_LEG_X = BASE_FRONT_HALF_W - BASE_LEG_INSET - BASE_LEG_W / 2.0   # ±79
FRONT_LEG_Y = BASE_Y_FRONT - BASE_LEG_INSET - BASE_LEG_W / 2.0        # +94
REAR_LEG_X = 0.0
REAR_LEG_Y = BASE_Y_REAR + BASE_LEG_INSET + BASE_LEG_W / 2.0          # -54

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
ARM_BASE_SUPPORT_LEN = 40.0
ARM_SLOPE_RUN = 16.0
Y_DISP = 125.0                      # hinge axis Y (= dispense end)
Z_AUG = 29.25                       # hinge axis Z (absolute)
Z_BASE_TOP = -14.0                  # baseplate-body BOTTOM in absolute Z
HINGE_AXIS_Z_LOCAL = Z_AUG - Z_BASE_TOP                                # 43.25
ARM_BACK_Y = BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN                       # +75
SLOPE_TOP_Y = ARM_BACK_Y + ARM_SLOPE_RUN                               # +91

# MG996R servo mount (two square posts + cantilevered porch).
DRIVE_HEAD_OVERHANG = 5.0
GEAR_HINGE_TIP_D = 38.17            # ≈ 38.2 mm
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

# Porch.
PORCH_X_LO = SERVO_WALL_X                                              # 59.0
PORCH_X_HI = min(SERVO_BODY_X_HI + 1.0, BASE_FRONT_HALF_W)             # 96.8
PORCH_Y_LO = BASE_Y_FRONT - 2.0                                        # 113.0
PORCH_Y_HI = FAR_POST_Y_HI + 1.0                                       # 170.4

# Underside triangular flange.
FLANGE_THK = 6.0
FLANGE_DEPTH = 30.0

# Arm-clearance slots through the mounting plate (informational — slot is
# in the plate, not the baseplate, but the slot Y bound depends on the
# baseplate's arm geometry).
ARM_SLOT_Y_BACK = ARM_BACK_Y - 2.0                                     # +73


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

    # Tabletop trapezoid.
    polygon(ax, [
        (-BASE_FRONT_HALF_W, BASE_Y_FRONT),
        (+BASE_FRONT_HALF_W, BASE_Y_FRONT),
        (+BASE_REAR_HALF_W,  BASE_Y_REAR),
        (-BASE_REAR_HALF_W,  BASE_Y_REAR),
    ])

    # Porch (fused to the front edge, projecting +X past the front leg).
    rect(ax, PORCH_X_LO, PORCH_Y_LO,
         PORCH_X_HI - PORCH_X_LO, PORCH_Y_HI - PORCH_Y_LO,
         face="#eaf2ff")

    # Two front-corner legs (footprint shown dashed since they're below).
    for sx in (-FRONT_LEG_X, +FRONT_LEG_X):
        rect(ax, sx - BASE_LEG_W / 2, FRONT_LEG_Y - BASE_LEG_W / 2,
             BASE_LEG_W, BASE_LEG_W,
             face="none", edge=HIDDEN_COLOR, lw=0.8, ls=(0, (4, 2)))
    rect(ax, REAR_LEG_X - BASE_LEG_W / 2, REAR_LEG_Y - BASE_LEG_W / 2,
         BASE_LEG_W, BASE_LEG_W,
         face="none", edge=HIDDEN_COLOR, lw=0.8, ls=(0, (4, 2)))

    # Two hinge arms (footprint on the tabletop).
    for sign in (-1, +1):
        x_lo = sign * (ARM_X_LO_POS if sign > 0 else ARM_X_HI_POS)
        x_hi = sign * (ARM_X_HI_POS if sign > 0 else ARM_X_LO_POS)
        if x_lo > x_hi:
            x_lo, x_hi = x_hi, x_lo
        rect(ax, x_lo, ARM_BACK_Y, x_hi - x_lo, Y_DISP - ARM_BACK_Y,
             face="#fff5e6", lw=1.0)

    # Two square servo posts.
    for y_lo, y_hi in [(NEAR_POST_Y_LO, NEAR_POST_Y_HI),
                       (FAR_POST_Y_LO, FAR_POST_Y_HI)]:
        rect(ax, SERVO_WALL_X, y_lo, SERVO_WALL_T, y_hi - y_lo,
             face="#dbe9ff", lw=1.0)
        # Two Ø5 ear holes per post (centred on the post midline along Y).
        ym = (y_lo + y_hi) / 2.0
        circle(ax, SERVO_WALL_X + SERVO_WALL_T / 2.0, ym,
               MG996R_HOLE_DIA / 2.0, lw=0.8)

    # Pinion centreline mark.
    circle(ax, SERVO_WALL_X, PINION_Y, 0.7, edge=DIM_COLOR, face=DIM_COLOR,
           lw=0)

    # ---------------- Overall + tabletop dimensions (LEFT/BOTTOM stack) -
    # Overall front-edge width (200) — well above the front edge.
    hdim(ax, -BASE_FRONT_HALF_W, +BASE_FRONT_HALF_W, BASE_Y_FRONT + 32,
         "200.0   (front edge, = 2 × 100)",
         ext_from=BASE_Y_FRONT + 1)
    # Rear-edge width (64).
    hdim(ax, -BASE_REAR_HALF_W, +BASE_REAR_HALF_W, BASE_Y_REAR - 18,
         "64.0   (rear edge, = 2 × 32)",
         ext_from=BASE_Y_REAR, text_above=False)
    # Front-to-rear depth (190) — far LEFT.
    vdim(ax, BASE_Y_REAR, BASE_Y_FRONT, -BASE_FRONT_HALF_W - 28,
         "190.0", ext_from=-BASE_FRONT_HALF_W - 2)
    # Y-coords of front / rear edges — far LEFT, outboard of the 190 dim.
    vdim(ax, 0, BASE_Y_FRONT, -BASE_FRONT_HALF_W - 55, "Y = +115",
         ext_from=-BASE_FRONT_HALF_W - 38, text_right=False)
    vdim(ax, BASE_Y_REAR, 0, -BASE_FRONT_HALF_W - 55, "Y = −75",
         ext_from=-BASE_FRONT_HALF_W - 38, text_right=False)

    # ---------------- Legs (BELOW, inside trapezoid) --------------------
    # Front-leg pitch 158 — placed just BELOW the leg footprints.
    hdim(ax, -FRONT_LEG_X, +FRONT_LEG_X, FRONT_LEG_Y - 26,
         "158.0   (front-leg C/L pitch)",
         ext_from=FRONT_LEG_Y - BASE_LEG_W / 2, text_above=False,
         fontsize=7)
    # Front-leg Y inset (21 from front edge to leg C/L) — to the LEFT
    # between the −X leg and the trapezoid edge.
    vdim(ax, FRONT_LEG_Y, BASE_Y_FRONT, -FRONT_LEG_X - 18,
         "21.0", ext_from=-FRONT_LEG_X - BASE_LEG_W / 2 - 1,
         text_right=False, fontsize=7)
    # Rear-leg Y inset.
    vdim(ax, BASE_Y_REAR, REAR_LEG_Y, -28,
         "21.0", ext_from=-BASE_LEG_W / 2 - 1, text_right=False,
         fontsize=7)
    # Leg footprint callout — single short leader, well away from text.
    leader(ax, (-FRONT_LEG_X + BASE_LEG_W / 2,
                FRONT_LEG_Y + BASE_LEG_W / 2),
           (-145, 70),
           "Legs ×3  (square)\n"
           "  18 × 18 footprint\n"
           "  centred at\n"
           "  (±79, +94)\n"
           "  (0, −54)\n"
           "  hang 95 below\n"
           "  (Z-shown dashed)",
           ha="left", fontsize=7)

    # ---------------- Hinge arms (single leader to the LEFT) ------------
    leader(ax, (ARM_X_LO_POS, (ARM_BACK_Y + Y_DISP) / 2),
           (-140, 145),
           "Hinge arms ×2\n"
           "  X-span:  ±[24.88 → 37.17]  (width 12.28)\n"
           "  Y-span:  +75 → +125\n"
           "  (carries M5 hinge pin; see side/front views)",
           ha="left", fontsize=7)

    # ---------------- Servo cluster (RIGHT-SIDE stack) ------------------
    # 5 mm drive-head overhang past front edge — INSIDE the trapezoid
    # gap between front edge and the post (along Y between front leg and
    # near post, where there is empty space).
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
    # Single combined leader for the servo posts — placed FAR RIGHT.
    leader(ax, (SERVO_WALL_X + SERVO_WALL_T, NEAR_POST_Y_LO + 2),
           (170, 50),
           "Servo posts ×2\n"
           "  6.0 (X) × 14.0 (Y) × 20.0 (Z high)\n"
           "  2 × Ø5 thru per post\n"
           "  on 49.5 × 10 mm pattern\n"
           "  (see front view for hole Z)\n"
           "  inboard face at X = 59.0",
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
    # Two front-corner legs.
    for sx in (-FRONT_LEG_X, +FRONT_LEG_X):
        rect(ax, sx - BASE_LEG_W / 2, -BASE_LEG_H,
             BASE_LEG_W, BASE_LEG_H, face="#efefef")
    # Rear leg (hidden behind tabletop in front view — show dashed).
    rect(ax, REAR_LEG_X - BASE_LEG_W / 2, -BASE_LEG_H,
         BASE_LEG_W, BASE_LEG_H,
         face="none", edge=HIDDEN_COLOR, lw=0.8, ls=(0, (4, 2)))

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

    # Two servo posts (silhouette in front view: rectangles at SERVO_WALL_X).
    # In a strict orthographic projection both posts project to the same
    # silhouette — draw the one at +X, since the gear/posts only exist on
    # the +X side.
    rect(ax, SERVO_WALL_X, BASE_T, SERVO_WALL_T,
         POST_Z_HI - BASE_T, face="#dbe9ff", lw=1.0)
    # Ø5 hole pattern on the post (4 holes, but front view shows only 2
    # along Z since the other two are behind in Y).
    for dz in (-MG996R_HOLE_Z_SPREAD / 2.0, +MG996R_HOLE_Z_SPREAD / 2.0):
        circle(ax, SERVO_WALL_X + SERVO_WALL_T / 2.0,
               PINION_Z_LOCAL + dz, MG996R_HOLE_DIA / 2.0, lw=0.8)

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
    # Leg height 95 — far LEFT, outboard of the 6 dim.
    vdim(ax, -BASE_LEG_H, 0, -BASE_FRONT_HALF_W - 38, "95.0",
         ext_from=-BASE_FRONT_HALF_W - 22)
    # Leg width 18.
    hdim(ax, -FRONT_LEG_X - BASE_LEG_W / 2, -FRONT_LEG_X + BASE_LEG_W / 2,
         -BASE_LEG_H - 6, "18.0",
         ext_from=-BASE_LEG_H, text_above=False, fontsize=7)
    # Front-leg pitch 158 — placed BELOW so it clears the rear-leg footprint.
    hdim(ax, -FRONT_LEG_X, +FRONT_LEG_X, -BASE_LEG_H - 18,
         "158.0  (front-leg pitch)",
         ext_from=-BASE_LEG_H - 8, text_above=False)

    # Hinge axis Z — far RIGHT.
    vdim(ax, 0, HINGE_AXIS_Z_LOCAL, +BASE_FRONT_HALF_W + 22,
         "43.25  (hinge axis Z)",
         ext_from=+BASE_FRONT_HALF_W + 2)
    # Hinge eye OD/ID — leader to UPPER-LEFT into free space above tabletop.
    leader(ax, (-ARM_X_HI_POS - HINGE_EYE_OD / 2.0, HINGE_AXIS_Z_LOCAL),
           (-145, HINGE_AXIS_Z_LOCAL + 20),
           "Hinge eye\n  Ø18 OD / Ø5.4 ID  (M5 pin)",
           fontsize=7, ha="left")

    # ---- Servo post block (RIGHT side, well clear of legs) -------------
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
    # Post height + position composite leader — placed in the empty
    # space ABOVE the rightmost area, not overlapping legs.
    leader(ax, (SERVO_WALL_X + SERVO_WALL_T, POST_Z_HI - 4),
           (SERVO_WALL_X + 70, -42),
           "Servo post  (×2)\n"
           "  6.0 thick (X)  ×  20.0 high above tabletop\n"
           "  inboard face at X = +59.0\n"
           "  4 × Ø5 thru on 49.5 × 10 mm pattern",
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

    # Legs (front + rear). In side view both front legs overlap.
    rect(ax, FRONT_LEG_Y - BASE_LEG_W / 2, -BASE_LEG_H,
         BASE_LEG_W, BASE_LEG_H, face="#efefef")
    rect(ax, REAR_LEG_Y - BASE_LEG_W / 2, -BASE_LEG_H,
         BASE_LEG_W, BASE_LEG_H, face="#efefef")

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

    # Underside triangular flange (hidden behind front leg in this view —
    # show as outline only).
    polygon(ax, [
        (FRONT_LEG_Y, BASE_T),
        (PORCH_Y_HI, BASE_T),
        (FRONT_LEG_Y, BASE_T - FLANGE_DEPTH),
    ], face="none", edge=HIDDEN_COLOR, lw=0.8, ls=(0, (3, 2)))

    # ---------------- Dimensions ----------------
    # Overall Y depth 190 — placed HIGH, well above the hinge cap.
    hdim(ax, BASE_Y_REAR, BASE_Y_FRONT, HINGE_AXIS_Z_LOCAL + 28,
         "190.0   (tabletop Y-depth)",
         ext_from=HINGE_AXIS_Z_LOCAL + 12)
    # Tabletop thickness 6 — far LEFT.
    vdim(ax, 0, BASE_T, BASE_Y_REAR - 14, "6.0",
         ext_from=BASE_Y_REAR - 1, fontsize=7)
    # Leg height 95.
    vdim(ax, -BASE_LEG_H, 0, BASE_Y_REAR - 30, "95.0",
         ext_from=BASE_Y_REAR - 16)
    # Front-leg Y position (21 from front edge).
    hdim(ax, FRONT_LEG_Y, BASE_Y_FRONT, -BASE_LEG_H - 10, "21.0",
         ext_from=-BASE_LEG_H, text_above=False, fontsize=7)
    # Rear-leg Y position (21 from rear edge).
    hdim(ax, BASE_Y_REAR, REAR_LEG_Y, -BASE_LEG_H - 10, "21.0",
         ext_from=-BASE_LEG_H, text_above=False, fontsize=7)

    # Arm base support length 40 — placed BELOW the tabletop, far enough
    # to clear the porch dim.
    hdim(ax, ARM_BACK_Y, Y_DISP, BASE_T - 12,
         "40.0  (arm base support)", ext_from=BASE_T,
         text_above=False, fontsize=7)
    # Slope run 16 — placed ABOVE the slope-top point, well clear of the eye.
    hdim(ax, ARM_BACK_Y, SLOPE_TOP_Y, HINGE_AXIS_Z_LOCAL + 8,
         "16  (slope run, ≈58°)",
         ext_from=HINGE_AXIS_Z_LOCAL + 1, fontsize=7)
    # Hinge axis Y/Z — leader UP-LEFT, well clear of slope dim.
    leader(ax, (Y_DISP, HINGE_AXIS_Z_LOCAL),
           (Y_DISP + 30, HINGE_AXIS_Z_LOCAL + 26),
           "Hinge axis\n  Y = +125,  Z = +43.25  (local)\n"
           "  10 mm forward of front edge",
           fontsize=7, ha="left")

    # Post Z height (20) — RIGHT of far post.
    vdim(ax, BASE_T, POST_Z_HI, FAR_POST_Y_HI + 8,
         "20.0  (post H)", ext_from=FAR_POST_Y_HI + 1, fontsize=7)
    # Post gap 41 — placed HIGHER, well above post tops.
    hdim(ax, NEAR_POST_Y_HI, FAR_POST_Y_LO,
         POST_Z_HI + 22, "41.0  (post gap)",
         ext_from=POST_Z_HI + 1, fontsize=7)
    # Pinion / spline cross-mark callout — leader UP-LEFT into open space
    # above the arm silhouette.
    leader(ax, (PINION_Y, PINION_Z_LOCAL),
           (PINION_Y - 55, HINGE_AXIS_Z_LOCAL - 18),
           "spline  (Z = +10)", fontsize=7, ha="right")
    # Porch fwd-of-front-edge — well BELOW tabletop, clear of arm support dim.
    hdim(ax, BASE_Y_FRONT, PORCH_Y_HI, BASE_T - 24,
         f"{PORCH_Y_HI - BASE_Y_FRONT:.1f}  (porch fwd of front edge)",
         ext_from=BASE_T, text_above=False, fontsize=7)

    # Flange depth — leader to LEFT-BELOW.
    leader(ax, (FRONT_LEG_Y + 4, BASE_T - FLANGE_DEPTH / 2.0),
           (FRONT_LEG_Y - 40, BASE_T - FLANGE_DEPTH - 4),
           "Underside flange (hidden)\n"
           "  6 thk × 30 deep × ~21 long",
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
        "4.  Tabletop is a TRAPEZOID:\n"
        "        ±100 at Y = +115 (front)   →   ±32 at Y = −75 (rear).\n"
        "\n"
        "5.  TRIPOD legs (all 18 × 18 × 95 mm):\n"
        "        (+79, +94),  (−79, +94),  (0, −54).\n"
        "\n"
        "6.  Hinge arms (×2) carry the shared M5 hinge pin.\n"
        "        Arm back face is sloped 16 mm run, ≈58° from horiz.,\n"
        "        so the plate sweeps 0°–90° without collision\n"
        "        (validated: 0.00 mm³ at 0° / 45° / 90°).\n"
        "\n"
        "7.  Servo posts (×2) seat the MG996R flange ears.\n"
        "        Holes are Ø5 thru on a 49.5 × 10 mm pattern\n"
        "        (clearance for M3 flange screws).\n"
        "        Driving-head tip hangs 5.0 mm past the front edge.\n"
        "        Pinion / hinge-gear mesh:  2 : 1, m ≈ 0.908,\n"
        "        C = 27.25 mm — gears NOT on this part (see assembly).\n"
        "\n"
        "8.  Underside triangular flange (6 × 30 × ~21 mm) ties the\n"
        "        cantilevered porch to the +X front leg.\n"
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

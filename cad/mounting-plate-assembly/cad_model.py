"""Mounting plate + hinged baseplate + hinge pins for the powder-doser.

Re-design per the fifth review on the issue #62 thread:

  * **Lifted brackets from PR #47** — the 14 mm-thick flange raises
    the auger bore to Z = 29.25 mm, giving the PR #49 Ø50 gear band
    4.25 mm of radial clearance over a flat plate.  There is now
    **no plinth under the brackets** and **no through-plate slot**
    under the gear band.
  * **Updated tap-collar mount plate from PR #51** (60 × 18 × 14 mm,
    bore at the same Z = 29.25 mm as the bracket).
  * **Auger gear, tap collar and front bracket are packed flush** —
    only 1 mm of air clearance between the gear-band face, the tap
    collar and the front bracket so gravity holds them against each
    other.
  * **Pinion centred on the gear band in Y** — the motor face is set
    so the pinion centre lands exactly on the gear-band centre,
    transferring full torque across the gear face.
  * **3-layer sandwich hinges** — each side of the auger gap carries
    {inner mounting-plate lobe, middle baseplate arm, outer
    mounting-plate lobe} sharing a single M5 pin per side.  The
    layers each occupy one third of their ramp half-span, so the
    hinge spans the full front of the plate.

Only the **new** parts are generated here (mounting_plate, baseplate,
hinge_pins).  The auger, brackets, tap-collar and motor STLs are
imported verbatim from the upstream PRs in ``imported-parts/``:

  - PR #49 v3 — ``cad/auger-geared/archimedes-auger-geared.stl``,
                ``cad/auger-geared/stepper-pinion.stl``
  - PR #51    — ``design/cad/tap-collar/stl/tap_collar.stl`` +
                ``mount_plate.stl``
  - PR #47    — ``design/cad/auger-bracket/stl/auger_bracket.stl``
                (the *lifted* 14 mm-flange variant)

Coordinate frame
================
  +X to the right (looking at the front of the machine from the
                    dispense end)
  +Y forward       (= the direction the auger discharges powder when
                    tilted; the dispense end of the auger is at +Y_DISP)
  +Z up

  Mounting plate top face is at z = 0, bottom at z = -PLATE_T.
  Auger centreline is at z = Z_AUG = 29.25 mm (= bracket native bore
  height, set by the lifted PR #47 flange).

Run from the package directory to (re)generate all three STEPs + STLs::

    cd cad/mounting-plate-assembly
    python3 cad_model.py
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

# --------------------------------------------------------------------- #
# Imported-part dimensions — kept in lock-step with the source PRs.
# Any change here MUST be matched against the upstream cad_model.py.
# --------------------------------------------------------------------- #

# PR #49 v3 — geared auger + pinion + NEMA 11 dummy.
AUGER_OD = 25.0
AUGER_LEN = 250.0
GEAR_BAND_AXIAL_FROM_DISP = AUGER_LEN / 3.0   # 83.33 mm from dispense end
GEAR_BAND_FACE_W = 10.0
GEAR_BAND_TIP_DIA = 50.0
PINION_TIP_DIA = 18.0
GEAR_CENTRE_DISTANCE = 32.0
PINION_LEN = 16.0
NEMA11_BODY_W = 28.2
NEMA11_BODY_L = 32.0
NEMA11_FACE_HOLE_PITCH = 23.0
NEMA11_PILOT_DIA = 22.0
NEMA11_SHAFT_DIA = 5.0
NEMA11_SHAFT_LEN = 18.0

# PR #47 — auger bracket (CadQuery; bore Ø25.5, plate 60 × 12 × 14).
# The PR #47 bracket is the **lifted** variant whose 14 mm-thick flange
# raises the bore axis to 29.25 mm above the flange-bottom, giving the
# Ø50 PR #49 gear band 4.25 mm of radial clearance over a flat plate.
# This is what eliminates both the under-bracket plinths and the
# through-plate gear-band slot from the previous pass (per @swcharles'
# fifth review on the issue #62 thread).
BRK_FLANGE_W = 60.0
BRK_FLANGE_D = 12.0
BRK_FLANGE_T = 14.0
BRK_MOUNT_HOLE_INSET_X = 6.0
BRK_MOUNT_HOLE_D = 3.4
BRK_COLLAR_OD = 33.5
BRK_COLLAR_OR = BRK_COLLAR_OD / 2
BRK_COLLAR_PLATE_OVERLAP = 1.5
BRK_RING_CENTRE_LOCAL_Z = (
    BRK_FLANGE_T + BRK_COLLAR_OR - BRK_COLLAR_PLATE_OVERLAP
)                                                    # 29.25 mm

# PR #51 — tap-collar mount plate (60 × 18 × 14, 2 × M3 at X = ±24).
# The latest #51 head bumps PLATE_DEPTH from 12 → 18 mm to match the
# lengthened TC collar so the M2 solenoid holes sit fully over solid
# collar material.  The mount-plate is dimensionally locked to the
# PR #47 bracket so the same M3 corner pattern works for both, and the
# collar bore sits at exactly the same Z = 29.25 mm above the plate
# bottom as the bracket bore — so bracket and tap-collar bolt flat to
# the same plate top with no Z shim and the auger threads through both
# at the same Z.
TAP_PLATE_W = 60.0
TAP_PLATE_D = 18.0
TAP_PLATE_T = 14.0
TAP_MOUNT_HOLE_INSET_X = 6.0
TAP_MOUNT_HOLE_D = 3.4
TAP_COLLAR_BORE_LOCAL_Z = 29.25

# --------------------------------------------------------------------- #
# Mounting-plate parameters
# --------------------------------------------------------------------- #
PLATE_T = 6.0

# Brackets bolt directly to the plate top (no plinths per the third
# review).  Auger axis sits at the bracket's native bore-centre height.
Z_AUG = BRK_RING_CENTRE_LOCAL_Z                              # +19.74

# Auger spans Y = [Y_REAR, Y_DISP].  Dispense end at +Y.
Y_DISP = +AUGER_LEN / 2.0                                    # +125
Y_REAR = -AUGER_LEN / 2.0                                    # -125
Y_GEAR_BAND = Y_DISP - GEAR_BAND_AXIAL_FROM_DISP             # +41.67

# Component Y positions along the auger (hinge end → motor end).
# Component ORDER matches the drawing.  Per the fifth review, front
# bracket / tap-collar / gear band are packed flush along Y with only
# a 1 mm air-clearance gap between adjacent ring faces so gravity holds
# them together against the brackets.
#   gear band       : Y_GEAR_BAND ± GEAR_BAND_FACE_W/2 = +41.67 ± 5
#   tap collar      : Y_TAP       ± TAP_PLATE_D/2     = +56.67 ± 9
#   front bracket   : Y_BRK_FRONT ± BRK_FLANGE_D/2    = +72.67 ± 6
PACK_GAP = 1.0
Y_TAP       = (Y_GEAR_BAND + GEAR_BAND_FACE_W / 2.0
               + PACK_GAP + TAP_PLATE_D / 2.0)                # +56.67
Y_BRK_FRONT = (Y_TAP + TAP_PLATE_D / 2.0
               + PACK_GAP + BRK_FLANGE_D / 2.0)               # +72.67
Y_BRK_REAR  = -95.0

# --- Plate X envelope (SYMMETRIC about X=0 — auger in the middle) ------
PLATE_X_HALF = GEAR_CENTRE_DISTANCE + NEMA11_BODY_W / 2.0 + 8.0  # 54.1
PLATE_X_MIN = -PLATE_X_HALF
PLATE_X_MAX = +PLATE_X_HALF
PLATE_W = PLATE_X_MAX - PLATE_X_MIN
PLATE_X_CENTRE = 0.0

# --- Plate Y envelope --------------------------------------------------
# Plate front edge sits 10 mm short of the hinge axis (the hinge axis
# is overhung forward by the eye + ramp top).
PLATE_Y_FRONT = Y_DISP - 10.0                                # +115
PLATE_Y_BACK  = Y_BRK_REAR - BRK_FLANGE_D / 2.0 - 7.0        # -114.5
PLATE_L = PLATE_Y_FRONT - PLATE_Y_BACK
PLATE_Y_CENTRE = (PLATE_Y_FRONT + PLATE_Y_BACK) / 2.0

# --- Auger gap (open U-notch in the +Y plate edge) ---------------------
AUGER_GAP_W = 32.0                          # X width of the notch
AUGER_GAP_Y_BACK = PLATE_Y_FRONT - 35.0     # how far back the notch goes

# --- Hinge sandwich (3 layers per side: plate / base / plate) ---------
# Per the fifth review, each side of the auger gap carries a 3-layer
# sandwich joint instead of a single-pin contact.  The +X half-ramp
# (from the auger-gap edge at X = +AUGER_GAP_W/2 out to PLATE_X_MAX)
# is divided equally into thirds along X:
#
#   inner third  : mounting-plate hinge lobe (inboard)
#   middle third : baseplate arm eye         (sandwiched)
#   outer third  : mounting-plate hinge lobe (outboard)
#
# A single M5 pin per side runs through all three lobes, making a much
# stiffer pivot.  The mirror layout applies on the -X side.
HINGE_EYE_OD = 18.0                       # thicker than the v4 (Ø14) pass
HINGE_EYE_ID = 5.4
# Each ramp half-span runs from the auger-gap edge to the plate X edge.
RAMP_HALF_SPAN = (PLATE_X_MAX - PLATE_X_CENTRE) - (AUGER_GAP_W / 2.0)  # 38.05
HINGE_LOBE_W = RAMP_HALF_SPAN / 3.0       # ≈ 12.68 mm — each of 3 layers
# A tiny shim of clearance between layers so the pin spins freely.
HINGE_LAYER_GAP = 0.4

# Convenience: X-coordinates of the layer boundaries on the +X side.
#   x0 = +AUGER_GAP_W/2                 (inner edge of the inner lobe)
#   x1 = x0 + HINGE_LOBE_W              (mounting/baseplate boundary)
#   x2 = x0 + 2 * HINGE_LOBE_W          (baseplate/mounting boundary)
#   x3 = PLATE_X_MAX                    (outer edge of the outer lobe)
HINGE_X0 = +AUGER_GAP_W / 2.0
HINGE_X1 = HINGE_X0 + HINGE_LOBE_W
HINGE_X2 = HINGE_X0 + 2.0 * HINGE_LOBE_W
HINGE_X3 = PLATE_X_MAX

# --- Front ramps (one each side of the auger gap) ----------------------
# Each ramp is a right-triangle prism in the YZ plane, extruded along X
# from the auger-gap edge out to the plate X edge for its side.
RAMP_Y_BACK = PLATE_Y_FRONT - 25.0                         # +90
RAMP_TOP_Z = Z_AUG + HINGE_EYE_OD / 2.0                    # +36.25

# --- NEMA-11 motor mount block (on TOP of plate) ----------------------
BOSS_W = NEMA11_BODY_W + 8.0                               # 36.2
BOSS_H = NEMA11_BODY_W + 8.0
BOSS_T = 6.0
MOTOR_FACE_Y = Y_GEAR_BAND - PINION_LEN / 2.0 - 2.0        # +31.67
X_MOTOR = +GEAR_CENTRE_DISTANCE                            # +32
Z_MOTOR = Z_AUG

# --- Linear-actuator rod-end pivot lug — REMOVED (no underside features).

# --- Baseplate (trapezoidal tripod) -----------------------------------
# Per Will's PR #66 review (comment 4615931709) the baseplate is
# trimmed from a 200 × 250 mm rectangle on four corner legs to a
# trapezoidal tabletop on a TRIPOD: the two rear corner legs are
# replaced by a single rear-centre leg and the tabletop tapers from
# the full-width front edge back to a narrow rear edge over that leg.
#
# Rear-leg placement.  @swcharles' note: the rear leg need not reach the
# auger's rear end (Y = -125); it only has to sit a small distance
# behind the worst-case (fully-loaded) centre of mass.  The dominant
# masses are the auger (Y ∈ [-125, +125], loaded COM ≈ 0) and the
# front-mounted stepper + gear/tap/bracket cluster (Y ≈ +30…+70), which
# bias the assembly COM FORWARD to roughly Y ≈ +15.  A rear foot at
# Y ≈ -54 therefore sits ~70 mm behind the COM — a generous stability
# margin — while removing ~60 mm of unused rear baseplate.
BASE_T = 6.0
BASE_LEG_H = 95.0
BASE_LEG_W = 18.0
BASE_LEG_INSET = 12.0

# Tabletop trapezoid — full width at the front edge (near the hinge),
# tapering to a narrow rear edge centred over the single rear leg.
BASE_FRONT_HALF_W = 100.0                                  # ±100 at front
BASE_REAR_HALF_W = 32.0                                    # ±32 at rear

# Baseplate position — front edge 10 mm BEHIND the hinge axis
# (= the hinge axis is 10 mm forward of the baseplate's front edge,
# per the issue #62 follow-up drawing).
BASE_Y_FRONT = Y_DISP - 10.0                               # +115
BASE_Y_REAR  = -75.0                                       # was -135 (rect)
# Back-compat aliases used by the side-view render diagrams.
BASE_Y_BACK  = BASE_Y_REAR
BASE_Y_CENTRE = (BASE_Y_FRONT + BASE_Y_REAR) / 2.0
BASE_W = 2.0 * BASE_FRONT_HALF_W                           # front-edge width
BASE_L = BASE_Y_FRONT - BASE_Y_REAR

# Z_BASE_TOP is the BOTTOM of the baseplate body in absolute frame.
# Baseplate top face is at z = Z_BASE_TOP + BASE_T.  Choose so there's
# an 8 mm air gap below the mounting plate bottom (z=-PLATE_T).
Z_BASE_TOP = -PLATE_T - 8.0                                # -14

# --- Baseplate hinge arms (forward-and-up, one each side) -------------
# Each arm now occupies the MIDDLE third of its ramp half-span so it is
# sandwiched between the mounting plate's inner and outer hinge lobes
# (per the fifth review).  The arm rises from the base top to the
# hinge axis level and shares the same M5 pin.
ARM_THK = HINGE_LOBE_W - HINGE_LAYER_GAP                   # ≈ 12.28 mm
# Hinge axis in baseplate's local frame (before final translate).
HINGE_AXIS_Z_LOCAL = Z_AUG - Z_BASE_TOP                    # +43.25

# How far back of the baseplate's front edge the hinge-arm bottom sits
# on the baseplate top.  Per Will's review the arm bottom face must be
# in COMPLETE contact with the baseplate — so extend the arm back into
# the baseplate area for solid support (no cantilever).
ARM_BASE_SUPPORT_LEN = 40.0

# (Linear-actuator base clevis removed — the linear actuator is no
# longer part of the design.)

# --- Hinge gear band + servo pinion (issue #63) ----------------------
# A spur gear is added to the +X OUTER mounting-plate hinge lobe so a
# servo on the baseplate can drive the tilt of the mounting plate.
# A 2:1 reduction between hinge gear and pinion keeps the torque load
# on the MG996R within its 9.4 kgf·cm rating.
GEAR_PA_DEG = 20.0                        # pressure angle (standard 20°)
GEAR_HINGE_TEETH = 40                     # 2 : 1 reduction with the 20-T pinion
GEAR_PINION_TEETH = 20
GEAR_FACE_W = HINGE_LOBE_W - HINGE_LAYER_GAP  # match the outer lobe thickness
# Pinion centreline placement is dictated by the MG996R geometry:
# the spline sits on the midline of the 20 mm-thick body, so seating
# the body flat on a wall that rises from the baseplate top puts the
# spline axis exactly 10 mm above the baseplate top (Will's
# annotation on PR #66 image attachment to comment 4500836183).
# We therefore drive the pinion Z from that spec and back-solve the
# gear module so the 40-T hinge gear at Z = Z_AUG still meshes with
# the 20-T pinion at the required Z, preserving the 2 : 1 ratio.
PINION_Z_ABOVE_BASE_TOP = 10.0
GEAR_CENTRE_C = (Z_AUG - (Z_BASE_TOP + BASE_T + PINION_Z_ABOVE_BASE_TOP))  # 27.25
GEAR_MODULE = (2.0 * GEAR_CENTRE_C
               / (GEAR_HINGE_TEETH + GEAR_PINION_TEETH))                   # ≈ 0.9083
GEAR_HINGE_PCD = GEAR_HINGE_TEETH * GEAR_MODULE
GEAR_PINION_PCD = GEAR_PINION_TEETH * GEAR_MODULE
GEAR_HINGE_TIP_D = GEAR_HINGE_PCD + 2 * GEAR_MODULE
GEAR_HINGE_ROOT_D = GEAR_HINGE_PCD - 2.5 * GEAR_MODULE
GEAR_PINION_TIP_D = GEAR_PINION_PCD + 2 * GEAR_MODULE
GEAR_PINION_ROOT_D = GEAR_PINION_PCD - 2.5 * GEAR_MODULE
# The hinge gear band sits just outboard of the existing +X outer hinge
# lobe (replacing the cylindrical 18 mm-OD eye on that side with a
# Ø42 gear).  X centre: midpoint of the +X outer-lobe span.
GEAR_X_CENTRE = (HINGE_X2 + HINGE_LAYER_GAP / 2 + HINGE_X3) / 2.0
GEAR_X_LO = GEAR_X_CENTRE - GEAR_FACE_W / 2.0
GEAR_X_HI = GEAR_X_CENTRE + GEAR_FACE_W / 2.0

# --- MG996R servo + mount (per Will's annotated datasheet, PR #66) ----
# Dimensions sourced from the dimensioned drawing posted by @williamulbz
# on PR #66 (image attachment to comment 4500498763).  Key callouts:
#   * body 40 × 20 × 36.8 mm
#   * flange ears tip-to-tip 54.5 mm (each ear 7.25 mm wide)
#   * 4 × Ø5 mounting holes on a 49.5 (Y) × 10 (Z) rectangular pattern
#   * spline axis sits 10.1 mm from the near body end → hole offsets
#     from the spline axis are −14.85 mm (near pair) and +34.65 mm
#     (far pair), both annotated directly on the drawing
#   * flange thickness 2 mm; total height 44.8 mm (28.7 below flange
#     to body bottom + 14.1 above flange to body top + 2 mm flange)
# The spline axis is parallel to the hinge axis (along X) so the pinion
# meshes with the hinge gear face.  Pinion sits OUTBOARD of the
# mounting plate (X > PLATE_X_MAX) with the servo body even further
# outboard; the spline points -X (toward the gear) and the body
# extends +X away from the mounting plate so there is no body
# interference at any tilt angle.
MG996R_BODY_L = 40.0     # along spline-perpendicular long axis (Y)
MG996R_BODY_T = 20.0     # body thickness (Z)
MG996R_BODY_H = 36.8     # body height (X — inward from flange face)
MG996R_FLANGE_L = 54.5                   # flange total length along Y
MG996R_FLANGE_T = 2.0                    # flange ear thickness along X
MG996R_HOLE_DIA = 5.0                    # Ø5 mounting holes (n5 callout)
MG996R_HOLE_Y_SPREAD = 49.5              # hole pair spread along body length (Y)
MG996R_HOLE_Z_SPREAD = 10.0              # hole pair spread along body thickness (Z)
MG996R_SPLINE_Y_OFFSET = 10.1            # spline offset from near body-end along Y
MG996R_SPLINE_LEN = 4.0                  # spline protrusion past flange face
# Spline output collar Ø (the raised boss the pinion-hub sits over).
# The MG996R has a ~Ø14 mm collar around the 25-T spline; we bore the
# wall to Ø10 so the printed pinion hub + set-screw clamp passes
# through and the collar tucks into a shallow counter-bore.
MG996R_SPLINE_COLLAR_DIA = 14.0
MG996R_SPLINE_CLEAR_DIA = 10.0
# Pinion lies at the same X centre as the gear, offset in -Z by the
# centre distance C so the spline sits just above the baseplate top.
PINION_X_CENTRE = GEAR_X_CENTRE
PINION_X_LO = GEAR_X_LO
PINION_X_HI = GEAR_X_HI
PINION_Y = Y_DISP                       # parallel to hinge axis
PINION_Z = Z_AUG - GEAR_CENTRE_C        # = +2.0 mm — 10 mm above baseplate top
# Servo mount — TWO separate SQUARE posts (per Will's PR #66 reviews,
# comments 4615931709 + 4624739034) rather than a full-face wall.  Each
# post is a clean rectangular pillar (no back brace / wedge) that
# carries one MG996R flange ear (its two Ø5 holes); the servo body +
# output boss protrude past the posts in the open gap between them for
# proper alignment.  The posts' inboard (-X) face is the flange seating
# plane.
SERVO_WALL_T = 6.0                      # post thickness along X (flange seat → +X)
# Post inboard (-X) face position.  Per Will's review (comment
# 4624739034, "blue line") the distance from the post face to the FAR
# (low-X) edge of the hinge gear band must be 14.1 mm — the MG996R
# flange-to-output reach read from the dimensioned drawing.  This pulls
# the posts OUTBOARD of the pinion so the servo spline carries the
# pinion exactly onto the hinge-gear face (centre distance and the 2:1
# ratio are unchanged — the gears themselves are untouched).
SERVO_FACE_TO_GEAR_FAR = 14.1
SERVO_WALL_X = GEAR_X_LO + SERVO_FACE_TO_GEAR_FAR       # ≈ 55.8
SERVO_BODY_X_LO = SERVO_WALL_X + SERVO_WALL_T
SERVO_BODY_X_HI = SERVO_BODY_X_LO + MG996R_BODY_H
# Posts run from the porch/baseplate top up to a little above the upper
# flange hole so the ear is fully backed by post material.
SERVO_WALL_Z_LO = BASE_T                # baseplate top in baseplate-local frame
# Hole-centre Y offsets from the spline axis — annotated directly on
# the dimensioned drawing as −14.85 mm and +34.65 mm (= 49.5 mm hole
# spacing, with holes seated 2.5 mm in from each ear tip).
MG996R_HOLE_Y_OFFSETS = (
    -(MG996R_SPLINE_Y_OFFSET + 7.25 - 2.5),               # = -14.85
    +(MG996R_BODY_L - MG996R_SPLINE_Y_OFFSET + 7.25 - 2.5),  # = +34.65
)
# The MG996R body (40 mm long in Y) must protrude PAST the two posts
# through the open gap between them (per Will's review, comment
# 4624739034 — "green dimension").  So the posts sit just OUTBOARD of
# each body end with a small clearance: the gap between the posts' inner
# faces equals the 40 mm body length + 2·SERVO_GAP_CLEAR.  Each post
# extends further OUTBOARD (away from the gap) to fully back its ear's
# two Ø5 holes.
SERVO_BODY_Y_LO = PINION_Y - MG996R_SPLINE_Y_OFFSET       # near body end (Y)
SERVO_BODY_Y_HI = SERVO_BODY_Y_LO + MG996R_BODY_L         # far  body end (Y)
SERVO_GAP_CLEAR = 0.5                    # per-side body clearance into the gap
SERVO_POST_W_Y = 14.0                    # post width along Y (outboard of the body)
SERVO_POST_Y_SPANS = (
    (SERVO_BODY_Y_LO - SERVO_GAP_CLEAR - SERVO_POST_W_Y,
     SERVO_BODY_Y_LO - SERVO_GAP_CLEAR),                  # near post
    (SERVO_BODY_Y_HI + SERVO_GAP_CLEAR,
     SERVO_BODY_Y_HI + SERVO_GAP_CLEAR + SERVO_POST_W_Y),  # far  post
)
SERVO_POST_HOLE_Z = (-MG996R_HOLE_Z_SPREAD / 2.0,         # 2 holes / post (Z ±5)
                     +MG996R_HOLE_Z_SPREAD / 2.0)

# Hardware
M3_CLEAR = 3.4
M5_CLEAR = 5.4

# --- Arm-clearance slots in the mounting plate (interference fix) ----
# The baseplate's two forward-and-up hinge arms occupy the MIDDLE third
# of each ramp half-span and extend back from the hinge axis to
# ``arm_back_y = BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN`` along the
# baseplate top.  When the mounting plate folds flush to 0° the
# baseplate arms would pierce the solid mounting-plate body wherever
# their Y/X envelopes overlap (Y∈[75, 115], X∈[±28.7, ±41.4] — total
# interference volume ≈ 5900 mm³).  Cut a clearance slot through the
# mounting plate at each arm's middle-third X band, from the front
# (+Y) edge back to just behind the arm's back face, so the arm passes
# cleanly through the plate when folded.
ARM_SLOT_Y_BACK = (BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN) - 2.0   # +73 (2 mm clear)
ARM_SLOT_CLEARANCE = 0.5                # per side along X


# --------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------- #
def _gear_polygon(num_teeth: int, module: float,
                  pa_deg: float = 20.0) -> list[tuple[float, float]]:
    """Return a closed 2D polygon (list of (x, y) points) describing a
    true-involute spur gear — matches the geometry used by the
    ``spur_gear_2d`` module in PR #49 (cad/auger-geared/gear-teeth.scad).

    Geometry:
        * pitch radius     Rp = N · m / 2
        * base radius      Rb = Rp · cos(α)            (involute starts here)
        * addendum         a  = m         → tip radius  Ra = Rp + m
        * dedendum         d  = 1.25 · m  → root radius Rd = Rp − 1.25 m
        * tooth thickness at pitch circle = π · m / 2
        * each flank is the true involute of the base circle,
          sampled at ``FLANK_STEPS`` points between base and tip

    Returns one closed CCW polygon walking root → −θ-flank (base→tip)
    → tip arc → +θ-flank (tip→base) → root arc to next tooth.  Suitable
    for ``cq.Workplane.polyline(...).close().extrude(...)``.
    """
    pa = math.radians(pa_deg)
    rp = num_teeth * module / 2.0
    rb = rp * math.cos(pa)
    ra = rp + module
    # If undercut would put the root inside the base circle, just clip
    # the involute at the base circle (the visible root then sits at rb).
    rd_target = rp - 1.25 * module
    rd = max(rd_target, rb)

    inv_pa = math.tan(pa) - pa                       # involute(α)
    half_tooth = math.pi / (2.0 * num_teeth)         # angular ½-thickness at pitch
    # Angular position (relative to tooth centre) of the involute
    # at the base circle, chosen so the involute passes through the
    # pitch circle at ±half_tooth (i.e. correct pitch-line thickness).
    flank_base_theta = half_tooth + inv_pa

    # Sample involute from base/root → tip in parameter t,
    # where r = rb·√(1+t²) and the involute angle = t − atan(t).
    t_start = math.sqrt(max((rd / rb) ** 2 - 1.0, 0.0))
    t_end = math.sqrt((ra / rb) ** 2 - 1.0)
    FLANK_STEPS = 12

    # +θ-side flank samples (root → tip), as (r, θ_rel_to_tooth_centre).
    # On the +θ flank, θ_rel = +flank_base_theta − (t − atan(t)).
    plus_flank: list[tuple[float, float]] = []
    for k in range(FLANK_STEPS + 1):
        t = t_start + (t_end - t_start) * k / FLANK_STEPS
        r = rb * math.sqrt(1.0 + t * t)
        theta_rel = flank_base_theta - (t - math.atan(t))
        plus_flank.append((r, theta_rel))

    # Mirror to get the −θ-side flank (same r, opposite θ).
    minus_flank = [(r, -th) for (r, th) in plus_flank]

    # Tip arc — a few extra samples between the two flank tips so
    # the tooth crown is a true arc and not a chord.
    TIP_ARC_STEPS = 3
    tip_theta_plus = plus_flank[-1][1]               # > 0
    tip_theta_minus = minus_flank[-1][1]             # < 0
    tip_arc: list[tuple[float, float]] = []
    for k in range(1, TIP_ARC_STEPS):
        frac = k / TIP_ARC_STEPS
        # interpolate from -tip_theta → +tip_theta
        th = tip_theta_minus + (tip_theta_plus - tip_theta_minus) * frac
        tip_arc.append((ra, th))

    pts: list[tuple[float, float]] = []
    angular_pitch = 2.0 * math.pi / num_teeth
    for i in range(num_teeth):
        c = i * angular_pitch
        # CCW around tooth boundary:
        #   1. −θ flank, base → tip (θ_rel increases from −flank_base_theta toward 0)
        for r, th in minus_flank:
            ang = c + th
            pts.append((r * math.cos(ang), r * math.sin(ang)))
        #   2. tip arc, −θ side → +θ side
        for r, th in tip_arc:
            ang = c + th
            pts.append((r * math.cos(ang), r * math.sin(ang)))
        #   3. +θ flank, tip → base (θ_rel increases from small + toward +flank_base_theta)
        for r, th in reversed(plus_flank):
            ang = c + th
            pts.append((r * math.cos(ang), r * math.sin(ang)))
        # Root arc to next tooth is implicit (next iteration's first
        # point is on the root circle at the next −θ-flank base).
    return pts


def _build_spur_gear(num_teeth: int, module: float, face_w: float,
                     bore_dia: float, flat: bool = False,
                     pa_deg: float = 20.0) -> cq.Workplane:
    """Build a spur gear extruded along +Z, centred on the origin.

    ``flat=True`` adds a 0.5 mm chordal flat to the bore — useful for
    set-screw bores (e.g. the MG996R 25-T spline workaround).
    """
    pts = _gear_polygon(num_teeth, module, pa_deg)
    gear = (
        cq.Workplane("XY")
        .polyline(pts).close()
        .extrude(face_w)
    )
    if bore_dia > 0:
        bore = (
            cq.Workplane("XY")
            .circle(bore_dia / 2.0)
            .extrude(face_w + 2.0)
            .translate((0, 0, -1.0))
        )
        gear = gear.cut(bore)
        if flat:
            flat_depth = 0.5
            flat = (
                cq.Workplane("XY")
                .box(bore_dia + 2.0, flat_depth,
                     face_w + 2.0, centered=(True, False, True))
                .translate((0, bore_dia / 2.0 - flat_depth / 2.0, face_w / 2.0))
            )
            gear = gear.cut(flat)
    return gear


def _through_plate_hole(x: float, y: float, dia: float,
                        plinth_h: float = 0.0) -> cq.Workplane:
    """Through-hole from plinth-top down to plate-bottom + slop."""
    z_top = plinth_h + 1.0
    z_bot = -(PLATE_T + 1.0)
    return (
        cq.Workplane("XY")
        .workplane(offset=z_top)
        .center(x, y)
        .circle(dia / 2.0)
        .extrude(z_bot - z_top)
    )


def build_mounting_plate() -> cq.Workplane:
    """Top plate: brackets-on-plinths + tap-collar + NEMA11 + front
    ramps + hinge eyes ALL on top, with a single open U-notch in the
    +Y edge for the auger."""
    # Plate body — asymmetric, centred on (PLATE_X_CENTRE, PLATE_Y_CENTRE).
    plate = (
        cq.Workplane("XY")
        .box(PLATE_W, PLATE_L, PLATE_T, centered=(True, True, False))
        .translate((PLATE_X_CENTRE, PLATE_Y_CENTRE, -PLATE_T))
    )

    # ---- Open U-notch in the +Y plate edge (auger gap) ------------------
    # Cut from y = AUGER_GAP_Y_BACK forward, slightly past the front edge.
    notch_l = PLATE_Y_FRONT - AUGER_GAP_Y_BACK + 4.0
    notch_y_centre = AUGER_GAP_Y_BACK + notch_l / 2.0 - 2.0
    notch = (
        cq.Workplane("XY")
        .workplane(offset=1.0)
        .center(0, notch_y_centre)
        .rect(AUGER_GAP_W, notch_l)
        .extrude(-(PLATE_T + 2.0))
    )
    plate = plate.cut(notch)

    # ---- Bracket mounting holes (M3 clearance through plate) ----------
    # Brackets bolt directly to the plate top (no plinths).
    brk_hole_x = BRK_FLANGE_W / 2.0 - BRK_MOUNT_HOLE_INSET_X         # ±24
    for cy in (Y_BRK_FRONT, Y_BRK_REAR):
        for sx in (+brk_hole_x, -brk_hole_x):
            plate = plate.cut(_through_plate_hole(sx, cy, M3_CLEAR))

    # ---- Tap-collar mount holes (mount sits flush, no plinth) ---------
    tap_hole_x = TAP_PLATE_W / 2.0 - TAP_MOUNT_HOLE_INSET_X          # ±24
    for sx in (+tap_hole_x, -tap_hole_x):
        plate = plate.cut(_through_plate_hole(sx, Y_TAP, M3_CLEAR))

    # ---- NEMA-11 motor mount block (on plate TOP) ----------------------
    # Vertical wall whose +Y face carries the NEMA-11 face holes;
    # motor body extends in -Y from that face.
    boss_top_z = Z_MOTOR + BOSS_H / 2.0
    boss_centre_z = boss_top_z / 2.0
    boss = (
        cq.Workplane("XY")
        .box(BOSS_W, BOSS_T, boss_top_z, centered=(True, True, True))
        .translate((X_MOTOR, MOTOR_FACE_Y - BOSS_T / 2.0, boss_centre_z))
    )
    plate = plate.union(boss)
    # 4 × M3 face holes (pattern is NEMA 11 standard 23 mm).
    for sx in (+NEMA11_FACE_HOLE_PITCH / 2, -NEMA11_FACE_HOLE_PITCH / 2):
        for sz in (+NEMA11_FACE_HOLE_PITCH / 2, -NEMA11_FACE_HOLE_PITCH / 2):
            hole = (
                cq.Workplane("XZ")
                .workplane(offset=-(MOTOR_FACE_Y + 1))
                .center(X_MOTOR + sx, Z_MOTOR + sz)
                .circle(M3_CLEAR / 2.0)
                .extrude(BOSS_T + 2.0)
            )
            plate = plate.cut(hole)
    # Central Ø22 pilot for shaft + pinion clearance.
    pilot = (
        cq.Workplane("XZ")
        .workplane(offset=-(MOTOR_FACE_Y + 1))
        .center(X_MOTOR, Z_MOTOR)
        .circle(NEMA11_PILOT_DIA / 2.0)
        .extrude(BOSS_T + 2.0)
    )
    plate = plate.cut(pilot)

    # ---- Front ramps + sandwich hinge lobes ----------------------------
    # Per the fifth review each side of the auger gap is a continuous
    # ramp from the plate top up to the hinge axis, with the +X and -X
    # halves each split along X into thirds:
    #
    #     inner third  : mounting-plate hinge lobe   (this part)
    #     middle third : baseplate arm eye           (baseplate part)
    #     outer third  : mounting-plate hinge lobe   (this part)
    #
    # The outermost surface of every lobe is the ramp face, so the ramp
    # geometry naturally inherits the lobe boundaries.  All three lobes
    # share one M5 pin per side that runs along X through the eye bore.
    HINGE_R = HINGE_EYE_OD / 2.0
    for side in (+1, -1):
        # X coordinates of the lobe boundaries on this side.
        if side > 0:
            x0, x1, x2, x3 = HINGE_X0, HINGE_X1, HINGE_X2, HINGE_X3
            mp_layers = ((x0, x1 - HINGE_LAYER_GAP / 2),
                         (x2 + HINGE_LAYER_GAP / 2, x3))
        else:
            x0, x1, x2, x3 = -HINGE_X0, -HINGE_X1, -HINGE_X2, -HINGE_X3
            mp_layers = ((x1 + HINGE_LAYER_GAP / 2, x0),
                         (x3, x2 - HINGE_LAYER_GAP / 2))

        for x_inner, x_outer in mp_layers:
            x_lo, x_hi = sorted((x_inner, x_outer))
            # Ramp wedge for this lobe — triangular YZ prism that fills
            # from the back of the ramp footprint forward to the plate
            # front edge, rising from z=0 up to the hinge axis.
            ramp = (
                cq.Workplane("YZ")
                .workplane(offset=x_lo)
                .moveTo(RAMP_Y_BACK, 0)
                .lineTo(PLATE_Y_FRONT, 0)
                .lineTo(PLATE_Y_FRONT, RAMP_TOP_Z)
                .close()
                .extrude(x_hi - x_lo)
            )
            plate = plate.union(ramp)
            # Eye lobe — disc-cap that overhangs the plate front edge so
            # the bore axis lands at the dispense point (Y_DISP).  Built
            # as a rectangle + half-cylinder cap so it fairs smoothly
            # into the ramp top face.
            tab_y_back = PLATE_Y_FRONT - 1.0  # 1 mm overlap for robust union
            tab = (
                cq.Workplane("YZ")
                .workplane(offset=x_lo)
                .moveTo(tab_y_back, Z_AUG - HINGE_R)
                .lineTo(Y_DISP, Z_AUG - HINGE_R)
                .lineTo(Y_DISP, Z_AUG + HINGE_R)
                .lineTo(tab_y_back, Z_AUG + HINGE_R)
                .close()
                .extrude(x_hi - x_lo)
            )
            cap = (
                cq.Workplane("YZ")
                .workplane(offset=x_lo)
                .center(Y_DISP, Z_AUG)
                .circle(HINGE_R)
                .extrude(x_hi - x_lo)
            )
            plate = plate.union(tab).union(cap)
            # Through-bore (M5 clearance) along X through this lobe.
            bore = (
                cq.Workplane("YZ")
                .workplane(offset=x_lo - 1.0)
                .center(Y_DISP, Z_AUG)
                .circle(HINGE_EYE_ID / 2.0)
                .extrude((x_hi - x_lo) + 2.0)
            )
            plate = plate.cut(bore)

    # ---- Hinge gear band on the +X OUTER lobe (issue #63) --------------
    # The outermost +X mounting-plate hinge lobe carries a 40-tooth
    # spur gear band that meshes with the servo pinion at C = 30 mm,
    # 2:1 reduction.  The gear band is integrated into the mounting
    # plate as a single solid (not a separate STL part) per the issue.
    # The gear is built in the XY plane (axis along Z), then rotated to
    # align its axis with the X-axis at (Y_DISP, Z_AUG).
    gear = _build_spur_gear(GEAR_HINGE_TEETH, GEAR_MODULE,
                            GEAR_FACE_W, HINGE_EYE_ID)
    # Rotate so the gear axis (was +Z) becomes +X (extrusion goes from
    # X=0 to X=+face_w in the rotated frame), then translate to the
    # hinge axis at the +X outer-lobe X centre.
    gear = (
        gear.rotate((0, 0, 0), (0, 1, 0), 90)
            .translate((GEAR_X_LO, Y_DISP, Z_AUG))
    )
    plate = plate.union(gear)

    # ---- Arm-clearance slots through the plate body (interference fix) --
    # The two baseplate hinge arms (one each side of the auger gap)
    # pass through the plate body when folded flush to the baseplate.
    # Cut a vertical clearance slot through the plate at each arm's X
    # band, from the +Y edge back to just behind the arm's back face.
    # Without this, the arms pierce the plate by ~5900 mm³ at 0° tilt.
    slot_y_back = ARM_SLOT_Y_BACK
    slot_y_front = PLATE_Y_FRONT + 2.0
    slot_l = slot_y_front - slot_y_back
    slot_y_centre = (slot_y_front + slot_y_back) / 2.0
    for sign in (+1, -1):
        slot_x_lo = sign * HINGE_X1 if sign > 0 else -HINGE_X2
        slot_x_hi = sign * HINGE_X2 if sign > 0 else -HINGE_X1
        # Pad both X edges with ARM_SLOT_CLEARANCE so the arm slides
        # freely through the slot.
        slot_x_lo -= ARM_SLOT_CLEARANCE
        slot_x_hi += ARM_SLOT_CLEARANCE
        slot = (
            cq.Workplane("XY")
            .workplane(offset=1.0)
            .center((slot_x_lo + slot_x_hi) / 2.0, slot_y_centre)
            .rect(slot_x_hi - slot_x_lo, slot_l)
            .extrude(-(PLATE_T + 2.0))
        )
        plate = plate.cut(slot)

    return plate


def build_baseplate() -> cq.Workplane:
    """Bench-side plate with two forward-and-up hinge arms (one each
    side of the auger).  No powder window — powder falls in front of
    the baseplate (the dispense point sits 10 mm forward of the base
    front edge).

    The tabletop is a TRAPEZOID — full width at the front edge (near the
    hinge), tapering back to a narrow rear edge — standing on a TRIPOD:
    two front-corner legs plus a single rear-centre leg (per Will's
    PR #66 review)."""
    base = (
        cq.Workplane("XY")
        .polyline([
            (-BASE_FRONT_HALF_W, BASE_Y_FRONT),
            (+BASE_FRONT_HALF_W, BASE_Y_FRONT),
            (+BASE_REAR_HALF_W,  BASE_Y_REAR),
            (-BASE_REAR_HALF_W,  BASE_Y_REAR),
        ]).close()
        .extrude(BASE_T)
    )

    # Tripod legs.  Two at the front corners (just inboard of the wide
    # front edge) and ONE at the rear centre (replacing the old pair of
    # rear-corner legs).  Each leg drops the tabletop to give cup +
    # scale clearance in front of the baseplate.
    front_leg_x = BASE_FRONT_HALF_W - BASE_LEG_INSET - BASE_LEG_W / 2
    front_leg_y = BASE_Y_FRONT - BASE_LEG_INSET - BASE_LEG_W / 2
    rear_leg_y  = BASE_Y_REAR  + BASE_LEG_INSET + BASE_LEG_W / 2
    leg_positions = [
        (+front_leg_x, front_leg_y),
        (-front_leg_x, front_leg_y),
        (0.0,          rear_leg_y),
    ]
    for sx, sy in leg_positions:
        leg = (
            cq.Workplane("XY")
            .box(BASE_LEG_W, BASE_LEG_W, BASE_LEG_H,
                 centered=(True, True, False))
            .translate((sx, sy, -BASE_LEG_H))
        )
        base = base.union(leg)

    # Forward-and-up hinge arms — middle layer of the 3-layer sandwich.
    # Each arm occupies the centre third of its ramp half-span so it
    # slips between the mounting plate's inner and outer hinge lobes.
    # The arm rises from the base top to the hinge axis level and ends
    # in a disc-cap eye that shares the M5 pin with the plate lobes.
    # The arm bottom face extends BACK onto the baseplate top so it is
    # in full contact with the baseplate (per Will's review).
    #
    # The BACK (toward −Y, motor) edge is sloped from arm_back_y at the
    # baseplate top down to a point near the hinge axis, so the mounting
    # plate's underside has clearance to sweep through 45° and beyond
    # without colliding with the arm (also per Will's review).
    HINGE_R = HINGE_EYE_OD / 2.0
    arm_top_local = HINGE_AXIS_Z_LOCAL + HINGE_R
    arm_back_y = BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN
    # The sloped back face runs from (arm_back_y, BASE_T) up to
    # (slope_top_y, arm_top_local); ARM_SLOPE_RUN = 16 mm gives ~58°
    # from horizontal (steeper than 45° so the arm clears the plate
    # underside throughout the 0-90° tilt range).
    ARM_SLOPE_RUN = 16.0
    slope_top_y = arm_back_y + ARM_SLOPE_RUN
    arm_spans = (
        (HINGE_X1 + HINGE_LAYER_GAP / 2,  HINGE_X2 - HINGE_LAYER_GAP / 2),
        (-HINGE_X2 + HINGE_LAYER_GAP / 2, -HINGE_X1 - HINGE_LAYER_GAP / 2),
    )
    for x_lo, x_hi in arm_spans:
        arm = (
            cq.Workplane("YZ")
            .workplane(offset=x_lo)
            .moveTo(arm_back_y, BASE_T)
            .lineTo(Y_DISP, BASE_T)
            .lineTo(Y_DISP, arm_top_local)
            .lineTo(slope_top_y, arm_top_local)
            .close()
            .extrude(x_hi - x_lo)
        )
        base = base.union(arm)
        cap = (
            cq.Workplane("YZ")
            .workplane(offset=x_lo)
            .center(Y_DISP, HINGE_AXIS_Z_LOCAL)
            .circle(HINGE_R)
            .extrude(x_hi - x_lo)
        )
        base = base.union(cap)
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=x_lo - 1.0)
            .center(Y_DISP, HINGE_AXIS_Z_LOCAL)
            .circle(HINGE_EYE_ID / 2.0)
            .extrude((x_hi - x_lo) + 2.0)
        )
        base = base.cut(bore)

    # (Linear-actuator base clevis removed — no longer using a linear
    # actuator.)

    # ---- MG996R servo mount — TWO SQUARE posts (issue #63, PR #66) ------
    # Per Will's reviews (comments 4615931709 + 4624739034) the full-face
    # mounting wall is replaced by TWO separate square posts, one under
    # each MG996R flange ear, so the servo body + output boss protrude
    # PAST the posts through the open gap between them.  Each post is a
    # clean rectangular pillar (no back brace / wedge — the brace was the
    # "red" shape Will flagged as blocking proper seating of the servo's
    # mounting holes).  The gap between the posts' inner faces equals the
    # 40 mm body length (+ clearance) so the body fits between them; the
    # posts' inboard (-X) face is the flange seating plane at
    # X = SERVO_WALL_X, pulled outboard so the post-face-to-far-gear-edge
    # distance is 14.1 mm (gears untouched → centre distance and the 2:1
    # ratio are preserved).
    #
    # The far post sits well forward of the baseplate front edge, so we
    # (a) extend the baseplate top forward as a "porch" under the servo
    # footprint, and (b) tie the cantilevered porch down to the adjacent
    # front leg with a triangular flange under the tabletop (Will's
    # earlier 2nd bullet — kept).
    pinion_z_local = PINION_Z - Z_BASE_TOP
    post_z_lo = SERVO_WALL_Z_LO
    post_z_hi = pinion_z_local + MG996R_HOLE_Z_SPREAD / 2.0 + 5.0

    # (a) baseplate porch — a slab of baseplate-thickness material under
    # the servo footprint, fused to the baseplate front edge.
    PORCH_X_LO = SERVO_WALL_X             # flush with the posts' inboard face
    PORCH_X_HI = min(SERVO_BODY_X_HI + 1.0, BASE_FRONT_HALF_W)
    PORCH_Y_LO = BASE_Y_FRONT - 2.0       # 2 mm overlap into baseplate
    PORCH_Y_HI = SERVO_POST_Y_SPANS[1][1] + 1.0   # just past the far post
    porch = (
        cq.Workplane("XY")
        .box(PORCH_X_HI - PORCH_X_LO,
             PORCH_Y_HI - PORCH_Y_LO,
             BASE_T,
             centered=(False, False, False))
        .translate((PORCH_X_LO, PORCH_Y_LO, 0))
    )
    base = base.union(porch)

    # (b) the two square posts, each carrying its ear's two Ø5 holes.
    for (y_lo, y_hi), hole_y in zip(SERVO_POST_Y_SPANS, MG996R_HOLE_Y_OFFSETS):
        post = (
            cq.Workplane("XY")
            .box(SERVO_WALL_T, y_hi - y_lo, post_z_hi - post_z_lo,
                 centered=(False, False, False))
            .translate((SERVO_WALL_X, y_lo, post_z_lo))
        )
        base = base.union(post)
        # this ear's two Ø5 mounting holes through the post (along X).
        for dz in SERVO_POST_HOLE_Z:
            hole = (
                cq.Workplane("YZ")
                .workplane(offset=SERVO_WALL_X - 1.0)
                .center(PINION_Y + hole_y, pinion_z_local + dz)
                .circle(MG996R_HOLE_DIA / 2.0)
                .extrude(SERVO_WALL_T + 2.0)
            )
            base = base.cut(hole)

    # (c) underside triangular flange — stiffens the cantilevered porch
    # against the servo's weight + lifting reaction torque by tying it
    # down to the adjacent (+X) front leg.  A downstand rib hanging
    # below the tabletop in the Y-Z plane at the leg's X, deepest over
    # the leg and tapering to nothing at the porch front edge.
    FLANGE_THK = 6.0                      # rib thickness along X
    FLANGE_DEPTH = 30.0                   # how far it hangs below the tabletop
    flange_x = front_leg_x                # align with the +X front leg
    flange = (
        cq.Workplane("YZ")
        .workplane(offset=flange_x - FLANGE_THK / 2.0)
        .moveTo(front_leg_y, BASE_T)                 # over the leg, at tabletop
        .lineTo(PORCH_Y_HI, BASE_T)                  # forward to porch front
        .lineTo(front_leg_y, BASE_T - FLANGE_DEPTH)  # down into the leg
        .close()
        .extrude(FLANGE_THK)
    )
    base = base.union(flange)

    # Translate the whole baseplate so its bottom face sits at Z_BASE_TOP.
    return base.translate((0, 0, Z_BASE_TOP))


def build_servo_pinion() -> cq.Workplane:
    """20-tooth m=1.0 spur pinion for the MG996R (PCD 20, tip Ø22).

    Bore is Ø6 with a 0.5 mm chordal flat — the simplest printable
    interface to the MG996R's 25-T spline (set-screw retention).
    The pinion is built in its own frame (axis along X, centred on
    origin in YZ) ready for translation to (PINION_X_LO, PINION_Y,
    PINION_Z) at assembly time.
    """
    pinion = _build_spur_gear(GEAR_PINION_TEETH, GEAR_MODULE,
                              GEAR_FACE_W, 6.0, flat=True)
    # Phase the pinion by half a tooth pitch about its own axis so its
    # teeth align with the hinge gear's gaps at the mesh point (avoids
    # static tooth-on-tooth interpenetration in CAD; in practice the
    # servo will rotate to the correct phase on power-up anyway).
    half_pitch = 360.0 / GEAR_PINION_TEETH / 2.0
    pinion = pinion.rotate((0, 0, 0), (0, 0, 1), half_pitch)
    # Rotate so the axis (was +Z) becomes +X (extrusion goes from X=0
    # to X=+face_w in the rotated frame); translate at assembly time.
    pinion = pinion.rotate((0, 0, 0), (0, 1, 0), 90)
    return pinion


def build_hinge_pin() -> cq.Workplane:
    """A pair of long M5 pins (one per side), each running through the
    full 3-layer sandwich on its side:

        inner mounting-plate lobe + middle baseplate arm eye +
        outer mounting-plate lobe.

    Pin length spans HINGE_X0 → HINGE_X3 (= one ramp half-span) plus
    2 mm of slop at each end so the head can grip outside the outer
    lobe and the tail clears the inner lobe when withdrawn."""
    pin_len = (HINGE_X3 - HINGE_X0) + 4.0
    pin_centre_plus = (HINGE_X0 + HINGE_X3) / 2.0
    pin_plus = (
        cq.Workplane("YZ")
        .circle(5.0 / 2.0)
        .extrude(pin_len)
        .translate((pin_centre_plus - pin_len / 2.0, 0, 0))
    )
    pin_minus = pin_plus.mirror("YZ")
    return pin_plus.union(pin_minus)


def _tilt_mounting_plate(plate: cq.Workplane, tilt_deg: float) -> cq.Workplane:
    """Rotate the mounting plate about the hinge axis (global X through
    (Y_DISP, Z_AUG)) by ``tilt_deg`` (positive = lifts the rear up)."""
    if abs(tilt_deg) < 1e-9:
        return plate
    return (
        plate.translate((0, -Y_DISP, -Z_AUG))
             .rotate((0, 0, 0), (1, 0, 0), -tilt_deg)
             .translate((0, Y_DISP, Z_AUG))
    )


def validate_no_interference(verbose: bool = True) -> dict[str, float]:
    """Compute interference volumes between key moving + static parts:

      * mounting_plate ∩ baseplate at 0° (folded flush)
      * mounting_plate ∩ baseplate at 90° (vertical)
      * pinion ∩ baseplate (mounted servo position — should be 0)

    A non-zero interference volume means the parts physically overlap
    and the CAD is wrong.  Returns a dict of {check_name: volume_mm3}.
    """
    results: dict[str, float] = {}
    mp = build_mounting_plate()
    bp = build_baseplate()

    for tilt in (0.0, 45.0, 90.0):
        mp_t = _tilt_mounting_plate(mp, tilt)
        inter = mp_t.val().intersect(bp.val())
        vol = inter.Volume() if inter is not None else 0.0
        results[f"plate∩base @ {tilt:.0f}°"] = vol

    # Pinion sits on the baseplate; should not interfere with the base.
    pinion = build_servo_pinion().translate((PINION_X_LO, PINION_Y, PINION_Z))
    inter = pinion.val().intersect(bp.val())
    vol = inter.Volume() if inter is not None else 0.0
    results["pinion∩base (servo install)"] = vol

    if verbose:
        print()
        print("Interference checks (volume in mm³; should be ~0):")
        for name, v in results.items():
            tag = "OK   " if v < 1.0 else "FAIL "
            print(f"  [{tag}] {name:36s}  {v:10.2f} mm³")
    return results


# --------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------- #
def main() -> None:
    here = Path(__file__).resolve().parent
    step_dir = here / "step"
    stl_dir = here / "stl"
    step_dir.mkdir(exist_ok=True)
    stl_dir.mkdir(exist_ok=True)

    parts = {
        "mounting_plate": build_mounting_plate(),
        "baseplate": build_baseplate(),
        "hinge_pin": build_hinge_pin(),
        "servo_pinion": build_servo_pinion(),
    }
    for name, part in parts.items():
        step_path = step_dir / f"{name}.step"
        stl_path = stl_dir / f"{name}.stl"
        cq.exporters.export(part, str(step_path))
        cq.exporters.export(part, str(stl_path))
        bb = part.val().BoundingBox()
        print(f"  {name:16s}  X[{bb.xmin:7.2f},{bb.xmax:7.2f}]  "
              f"Y[{bb.ymin:7.2f},{bb.ymax:7.2f}]  "
              f"Z[{bb.zmin:7.2f},{bb.zmax:7.2f}]")
        print(f"    → {step_path.relative_to(here)}, {stl_path.relative_to(here)}")

    print()
    print(f"Plate X envelope             : [{PLATE_X_MIN:+.2f}, {PLATE_X_MAX:+.2f}] mm  "
          f"(symmetric about X=0)")
    print(f"Plate Y envelope             : [{PLATE_Y_BACK:+.2f}, {PLATE_Y_FRONT:+.2f}] mm")
    print(f"Auger axis Z (Z_AUG)         : {Z_AUG:+.2f} mm  "
          f"(bracket native — no plinths)")
    print(f"Gear-band-tip clearance over : {Z_AUG - GEAR_BAND_TIP_DIA/2:+.2f} mm "
          f"(negative = below plate top — overhangs through the open notch)")
    print(f"Auger gap (notch) X-width    : {AUGER_GAP_W:.1f} mm")
    print(f"Hinge eye OD                 : {HINGE_EYE_OD:.1f} mm  "
          f"(3-layer sandwich, each lobe ≈ {HINGE_LOBE_W:.2f} mm thick along X)")
    print(f"Ramp top Z                   : {RAMP_TOP_Z:+.2f} mm")
    print(f"Hinge axis                   : X-axis through (Y={Y_DISP:+.2f}, Z={Z_AUG:+.2f})")
    print(f"Baseplate front edge Y       : {BASE_Y_FRONT:+.2f} (hinge axis "
          f"= front edge + {Y_DISP - BASE_Y_FRONT:.0f} mm)")
    print(f"Component order (Y, hinge→far): brkF={Y_BRK_FRONT:+.0f}  "
          f"tap={Y_TAP:+.0f}  motor={Y_GEAR_BAND:+.2f}  brkR={Y_BRK_REAR:+.0f}")
    print(f"Hinge gear (mounting plate)  : Z={GEAR_HINGE_TEETH}T m={GEAR_MODULE}  "
          f"PCD={GEAR_HINGE_PCD:.1f}  tipØ={GEAR_HINGE_TIP_D:.1f}  "
          f"face={GEAR_FACE_W:.2f} mm @ X={GEAR_X_CENTRE:.2f}")
    print(f"Servo pinion                 : Z={GEAR_PINION_TEETH}T m={GEAR_MODULE}  "
          f"PCD={GEAR_PINION_PCD:.1f}  tipØ={GEAR_PINION_TIP_D:.1f}  "
          f"→ 2:1 reduction, C={GEAR_CENTRE_C:.1f} mm")
    print(f"MG996R spline axis           : (X={PINION_X_CENTRE:.2f}, "
          f"Y={PINION_Y:.2f}, Z={PINION_Z:+.2f})  "
          f"servo wall at X={SERVO_WALL_X:.2f}")

    validate_no_interference()


if __name__ == "__main__":
    main()

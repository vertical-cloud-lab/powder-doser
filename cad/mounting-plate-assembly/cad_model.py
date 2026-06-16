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
# Rear auger bracket — moved forward to just BEHIND the front drive
# cluster (motor/gears/servo mount) so the mounting plate can be cut
# down to a little more than half its former length (per Will's review
# pullrequestreview-4509355231: "move the back bracket up until it's
# just behind the servo mount and cut off the excess behind it").  Was
# -95 (plate ≈ 223 mm long); now -2 (plate ≈ 130 mm — ~58 %).
Y_BRK_REAR  = -2.0

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
PLATE_Y_BACK  = Y_BRK_REAR - BRK_FLANGE_D / 2.0 - 7.0        # -15 (was -114.5)
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

# --- Baseplate (forward-only mounting tab — legs/back removed) --------
# Per Will's review (comment 4721011696) the baseplate is trimmed down
# to "basically only the small section in front that interfaces with
# anything": the hinge arms, the (mirrored) servo porches, and a small
# strip of rear material carrying four M5 mounting holes used to bolt
# this part onto a separate leg/frame assembly.  ALL legs are removed
# (was a tripod) and the trapezoidal taper is gone (now rectangular).
BASE_T = 6.0
# Legs removed entirely; kept as zeros so back-compat constants exist
# for any importer that still references them (render_assembly.py etc).
BASE_LEG_H = 0.0
BASE_LEG_W = 0.0
BASE_LEG_INSET = 0.0

# Rectangular tabletop — full width at both edges (was trapezoidal).
BASE_FRONT_HALF_W = 100.0                                  # ±100 at front
BASE_REAR_HALF_W = 100.0                                   # ±100 at rear (rectangular)

# Baseplate position — front edge 10 mm BEHIND the hinge axis
# (= the hinge axis is 10 mm forward of the baseplate's front edge,
# per the issue #62 follow-up drawing).  Per Will's review
# (pullrequestreview-4509355231: "shorten the length even more") the
# rear edge is pulled further forward — the tab is now only ~60 mm deep
# (was 85), just enough to carry the hinge-arm bases, the servo porches
# and the four corner mounting holes.
BASE_Y_FRONT = Y_DISP - 10.0                               # +115
BASE_Y_REAR  = +55.0                                       # was +30; tab shortened
# Back-compat aliases used by the side-view render diagrams.
BASE_Y_BACK  = BASE_Y_REAR
BASE_Y_CENTRE = (BASE_Y_FRONT + BASE_Y_REAR) / 2.0
BASE_W = 2.0 * BASE_FRONT_HALF_W                           # front-edge width
BASE_L = BASE_Y_FRONT - BASE_Y_REAR

# Chamfered rear corners — per Will's review (pullrequestreview-4509355231:
# "chamfer the back corners (like in the drawing)").  A 45° chamfer cuts
# CHAMFER mm off each rear corner (the two corners on the −Y / rear edge,
# away from the servo mounts).
BASE_REAR_CHAMFER = 25.0

# --- M5 mounting holes (bolt baseplate to separate leg/frame assembly) ----
# Per Will's reviews (comment 4721011696 + pullrequestreview-4509355231:
# "move the mounting holes to match the placements of the green holes in
# the drawing").  Four Ø5.4 (M5 clearance) through-holes near the four
# corners of the tab — two near the chamfered rear corners and two near
# the front corners — clear of the hinge arms, servo posts and porches.
BASE_MOUNT_HOLE_DIA = 5.4                  # M5 clearance
BASE_MOUNT_HOLE_X = 80.0                    # ±80 from centreline (near corners)
BASE_MOUNT_HOLE_Y_REAR = BASE_Y_REAR + 13.0                 # +68 (clear of the chamfer)
BASE_MOUNT_HOLE_Y_FRONT = BASE_Y_FRONT - 10.0              # +105 (front corners)

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
ARM_BASE_SUPPORT_LEN = 35.0    # was 40 — reduced slightly so the arm depth
                               # no longer encroaches on the front bracket
                               # (Will's review comment 4721011696)

# (Linear-actuator base clevis removed — the linear actuator is no
# longer part of the design.)

# --- Hinge gear band + servo pinion (issue #63) ----------------------
# A spur gear is added to BOTH outer mounting-plate hinge lobes (+X and
# -X) so TWO servos on the baseplate can drive the tilt of the mounting
# plate together — per Will's review (comment 4721011696) the plate is
# now supported by two servos / gears instead of one.  Each servo / gear
# pair is identical (same module, same 2 : 1 reduction, same MG996R
# mount); the -X side is a pure mirror of the +X side across X = 0.
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
# The hinge gear band sits just outboard of the existing outer hinge
# lobes (replacing the cylindrical 18 mm-OD eye on those sides with a
# Ø38 gear).  +X side: X centre at the midpoint of the +X outer-lobe span.
# -X side is the pure mirror.
GEAR_X_CENTRE = (HINGE_X2 + HINGE_LAYER_GAP / 2 + HINGE_X3) / 2.0
GEAR_X_LO = GEAR_X_CENTRE - GEAR_FACE_W / 2.0
GEAR_X_HI = GEAR_X_CENTRE + GEAR_FACE_W / 2.0
# Mirrored gear band on the -X outer lobe.
GEAR_X_CENTRE_NEG = -GEAR_X_CENTRE
GEAR_X_LO_NEG = -GEAR_X_HI                 # near face (toward origin) on -X side
GEAR_X_HI_NEG = -GEAR_X_LO                 # far  face (away from origin) on -X side

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
# +X pinion lies at the same X centre as the +X gear, offset in -Z by
# the centre distance C so the spline sits just above the baseplate top.
PINION_X_CENTRE = GEAR_X_CENTRE
PINION_X_LO = GEAR_X_LO
PINION_X_HI = GEAR_X_HI
# Mirrored -X pinion — same Z, same Y, mirrored X.
PINION_X_CENTRE_NEG = GEAR_X_CENTRE_NEG
PINION_X_LO_NEG = GEAR_X_LO_NEG
PINION_X_HI_NEG = GEAR_X_HI_NEG
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
# 4625212895) the posts sit BEHIND the MG996R mounting holes and the
# servo is placed so the very TIP of its driving head hangs 5 mm past
# the baseplate front edge (per Will's follow-up comment 4633722007 —
# revised down from the earlier 8 mm).  On the dimensioned drawing the
# driving head (output boss + horn) physically protrudes 8 mm = 6 mm +
# 2 mm above the servo body top, and the mounting flange (the two ears)
# sits at that same body top; sliding the servo 3 mm inboard along +X
# now leaves only the outermost 5 mm of the driving head overhanging
# the baseplate front edge.  The printed pinion is pressed onto the
# servo spline and meshes across the hinge-gear face (X = GEAR_X_LO..
# GEAR_X_HI); centre distance and the 2:1 ratio live in Z and are
# unchanged — only the X placement of the posts/servo moves, so the
# gears are untouched.
DRIVE_HEAD_OVERHANG = 5.0               # tip-of-driving-head past baseplate front edge
SERVO_WALL_X = GEAR_X_HI + DRIVE_HEAD_OVERHANG          # = 59.0 (flange/edge plane)
# The mounting flange is AT the servo body top, so the body top plane
# coincides with the flange seating plane (the posts back the ears at
# the body's -X end, flanking it in ±Y).
SERVO_BODY_X_LO = SERVO_WALL_X
SERVO_BODY_X_HI = SERVO_BODY_X_LO + MG996R_BODY_H
# Mirrored servo on the -X side (per Will's comment 4721011696 — second
# servo to support the mounting plate from the opposite side).  Posts
# inboard (+X) face at X = -SERVO_WALL_X; body extends further -X.
SERVO_WALL_X_NEG = -SERVO_WALL_X                         # = -59.0
SERVO_BODY_X_LO_NEG = -SERVO_BODY_X_HI                   # ≈ -95.8 (far end of -X body)
SERVO_BODY_X_HI_NEG = -SERVO_BODY_X_LO                   # = -59.0 (flange face, inboard)
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
# their Y/X envelopes overlap (Y∈[80, 115], X∈[±28.7, ±41.4] — total
# interference volume ≈ 5000 mm³).  Cut a clearance slot through the
# mounting plate at each arm's middle-third X band, from the front
# (+Y) edge back to just behind the arm's back face, so the arm passes
# cleanly through the plate when folded.
ARM_SLOT_Y_BACK = (BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN) - 2.0   # +78 (2 mm clear)
ARM_SLOT_CLEARANCE = 0.5                # per side along X

# --- Underside hanging flange + supportive triangle (×2, one per side) ---
# Per Will's reviews (comment 4721011696 + pullrequestreview-4509355231)
# each servo mount has an underside hanging FLANGE braced by a
# supportive TRIANGLE.  The latest review corrects two things:
#   * The triangle previously floated far BEHIND the part (an XZ-plane
#     workplane-offset sign bug placed it at Y ≈ −118).  It must sit
#     RIGHT UNDER the servo mount, INTERSECTING both the flange and the
#     baseplate (porch).
#   * The M5 mounting hole moves OFF the flange and ONTO the triangle,
#     drilled HORIZONTALLY — parallel to the auger (along Y) at the 0°
#     position — so the tab can be bolted to a frame wall that faces
#     fore/aft.
# Geometry (per side, mirrored across X = 0):
#   * Flange — a vertical YZ-plane plate (thickness FLANGE_THK along X)
#     at X = ±FLANGE_X, hanging FLANGE_DEPTH below the porch underside,
#     spanning the servo body in Y.
#   * Triangle (gusset) — an XZ-plane rib of thickness FLANGE_GUSSET_THK
#     along Y, centred under the servo body, sharing the flange's outer
#     vertical edge (X = ±FLANGE_X) and its top edge with the porch
#     bottom (Z = 0), bracing inboard over FLANGE_GUSSET_RUN.
#   * Mounting hole — Ø5.4 (M5) drilled along Y through the triangle.
FLANGE_THK = 6.0                          # flange plate thickness along X
FLANGE_DEPTH = 40.0                       # how far the flange drops below the baseplate
FLANGE_X = 79.0                           # ±79 in X — under the servo body
FLANGE_GUSSET_THK = 10.0                  # triangle thickness along Y (room for the Y-hole)
FLANGE_GUSSET_RUN = 20.0                  # triangle X-run inboard from the flange (stays on the porch)
FLANGE_HOLE_DIA = 5.4                     # M5 clearance, drilled through the triangle along Y
FLANGE_HOLE_Z_BELOW_BASE = 15.0           # hole centre Z below the baseplate bottom
FLANGE_HOLE_X_INBOARD = 7.0               # hole centre X inboard of the flange face


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

    # ---- Hinge gear bands on BOTH outer lobes (issue #63) --------------
    # Both the +X and -X outermost mounting-plate hinge lobes carry a
    # 40-tooth spur gear band that meshes with its servo pinion at
    # C = 27.25 mm, 2:1 reduction.  The gear bands are integrated into
    # the mounting plate as a single solid (not separate STL parts).
    # The gear is built in the XY plane (axis along Z), then rotated to
    # align its axis with the X-axis at (Y_DISP, Z_AUG).  Per Will's
    # review (comment 4721011696) the plate is now supported by TWO
    # servos / gears instead of one — the -X side is a pure mirror of
    # the +X side across X = 0.
    gear = _build_spur_gear(GEAR_HINGE_TEETH, GEAR_MODULE,
                            GEAR_FACE_W, HINGE_EYE_ID)
    # Rotate so the gear axis (was +Z) becomes +X (extrusion goes from
    # X=0 to X=+face_w in the rotated frame), then translate to the
    # hinge axis at each outer-lobe X centre.
    gear_pos = (
        gear.rotate((0, 0, 0), (0, 1, 0), 90)
            .translate((GEAR_X_LO, Y_DISP, Z_AUG))
    )
    plate = plate.union(gear_pos)
    # Mirrored -X gear band — built the same way and placed at the -X
    # outer lobe (near face of the band sits at GEAR_X_LO_NEG = -GEAR_X_HI).
    gear_neg = (
        gear.rotate((0, 0, 0), (0, 1, 0), 90)
            .translate((GEAR_X_LO_NEG, Y_DISP, Z_AUG))
    )
    plate = plate.union(gear_neg)

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
    side of the auger), TWO mirrored MG996R servo mounts (one each
    side), and four M5 mounting holes at the rear for bolting to a
    separate leg/frame assembly.

    Per Will's review (comment 4721011696) this part is now just the
    "small section in front that interfaces with anything": the hinge
    arms, the two servo porches with their square posts, the underside
    hanging flanges with supportive gussets + M5 mounting holes, and a
    short stub of rear material carrying the four M5 mounting holes
    (arranged at the corners of a 60 × 60 square).  All four tripod
    legs and the trapezoidal taper are removed; the part bolts onto a
    separate leg assembly via the rear M5 holes.
    """
    # Rectangular tabletop (front-edge to rear-edge, full width).
    base = (
        cq.Workplane("XY")
        .box(BASE_W, BASE_L, BASE_T, centered=(False, False, False))
        .translate((-BASE_FRONT_HALF_W, BASE_Y_REAR, 0))
    )

    # Chamfer the two REAR corners (−Y edge, away from the servos) at 45°
    # — per Will's review (pullrequestreview-4509355231 "chamfer the back
    # corners").  Cut a triangular prism from each rear corner.
    c = BASE_REAR_CHAMFER
    for sx in (+1, -1):
        x_corner = sx * BASE_FRONT_HALF_W
        x_inner = sx * (BASE_FRONT_HALF_W - c)
        wedge = (
            cq.Workplane("XY")
            .workplane(offset=-1.0)
            .polyline([
                (x_corner, BASE_Y_REAR - 1.0),
                (x_corner + sx * 1.0, BASE_Y_REAR + c),
                (x_inner, BASE_Y_REAR - 1.0),
            ])
            .close()
            .extrude(BASE_T + 2.0)
        )
        base = base.cut(wedge)

    # Forward-and-up hinge arms — middle layer of the 3-layer sandwich.
    # Each arm occupies the centre third of its ramp half-span so it
    # slips between the mounting plate's inner and outer hinge lobes.
    # The arm rises from the base top to the hinge axis level and ends
    # in a disc-cap eye that shares the M5 pin with the plate lobes.
    # The BACK (toward −Y, motor) edge is sloped from arm_back_y at the
    # baseplate top down to a point near the hinge axis, so the mounting
    # plate's underside has clearance to sweep through 45° and beyond
    # without colliding with the arm.
    HINGE_R = HINGE_EYE_OD / 2.0
    arm_top_local = HINGE_AXIS_Z_LOCAL + HINGE_R
    arm_back_y = BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN
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

    # ---- MG996R servo mounts — TWO mirrored (±X) per Will's review -----
    # (comment 4721011696 — second servo + gear, mirrored from the +X
    # side).  Each side is identical: a baseplate-thickness PORCH under
    # the servo footprint extending forward past the baseplate front
    # edge, TWO SQUARE POSTS flanking each MG996R body (one under each
    # flange ear, carrying that ear's two Ø5 holes), and one underside
    # hanging FLANGE with a supportive triangular gusset and an M5
    # mounting hole through the flange face.  The gap between each
    # pair of posts equals the 40 mm body length (+ clearance) so the
    # body + output boss protrude through the open gap.
    pinion_z_local = PINION_Z - Z_BASE_TOP
    post_z_lo = SERVO_WALL_Z_LO
    post_z_hi = pinion_z_local + MG996R_HOLE_Z_SPREAD / 2.0 + 5.0

    for side in (+1, -1):
        wall_x = +SERVO_WALL_X if side > 0 else SERVO_WALL_X_NEG
        body_x_hi = (SERVO_BODY_X_HI if side > 0
                     else SERVO_BODY_X_LO_NEG)
        # post inboard face (toward auger) = wall_x; post body extends
        # OUTBOARD (away from auger) by SERVO_WALL_T.
        post_x_lo = min(wall_x, wall_x + side * SERVO_WALL_T)
        post_x_hi = max(wall_x, wall_x + side * SERVO_WALL_T)
        # porch X span — from the post inboard face out to the body far end.
        porch_x_lo = min(wall_x, body_x_hi)
        porch_x_hi = max(wall_x, body_x_hi)
        # clamp to baseplate envelope
        porch_x_lo = max(porch_x_lo, -BASE_FRONT_HALF_W)
        porch_x_hi = min(porch_x_hi, +BASE_FRONT_HALF_W)
        porch_y_lo = BASE_Y_FRONT - 2.0
        porch_y_hi = SERVO_POST_Y_SPANS[1][1] + 1.0
        porch = (
            cq.Workplane("XY")
            .box(porch_x_hi - porch_x_lo,
                 porch_y_hi - porch_y_lo,
                 BASE_T,
                 centered=(False, False, False))
            .translate((porch_x_lo, porch_y_lo, 0))
        )
        base = base.union(porch)

        # The two square posts, each carrying its ear's two Ø5 holes.
        for (y_lo, y_hi), hole_y in zip(SERVO_POST_Y_SPANS,
                                        MG996R_HOLE_Y_OFFSETS):
            post = (
                cq.Workplane("XY")
                .box(post_x_hi - post_x_lo,
                     y_hi - y_lo,
                     post_z_hi - post_z_lo,
                     centered=(False, False, False))
                .translate((post_x_lo, y_lo, post_z_lo))
            )
            base = base.union(post)
            # ear's two Ø5 mounting holes through the post (along X).
            for dz in SERVO_POST_HOLE_Z:
                hole = (
                    cq.Workplane("YZ")
                    .workplane(offset=post_x_lo - 1.0)
                    .center(PINION_Y + hole_y, pinion_z_local + dz)
                    .circle(MG996R_HOLE_DIA / 2.0)
                    .extrude((post_x_hi - post_x_lo) + 2.0)
                )
                base = base.cut(hole)

        # ---- Underside hanging flange + supportive triangle + M5 hole ---
        # Per Will's review (pullrequestreview-4509355231): the triangle
        # must sit RIGHT UNDER the servo mount, INTERSECTING the flange
        # and the baseplate (porch) — previously it floated far behind
        # the part.  The M5 mounting hole is now drilled HORIZONTALLY
        # (along Y, parallel to the auger at 0°) through the TRIANGLE,
        # not the flange.  Mirrored onto both sides (one per servo).
        flange_x = side * FLANGE_X                  # ±79 — under the servo body
        flange_y_lo = SERVO_BODY_Y_LO               # span the servo body in Y
        flange_y_hi = SERVO_BODY_Y_HI
        # Flange — vertical YZ-plane plate (thickness FLANGE_THK along X),
        # hanging FLANGE_DEPTH below the porch underside (Z = 0 local).
        flange = (
            cq.Workplane("YZ")
            .workplane(offset=flange_x - FLANGE_THK / 2.0)
            .moveTo(flange_y_lo, 0)
            .lineTo(flange_y_hi, 0)
            .lineTo(flange_y_hi, -FLANGE_DEPTH)
            .lineTo(flange_y_lo, -FLANGE_DEPTH)
            .close()
            .extrude(FLANGE_THK)
        )
        base = base.union(flange)
        # Supportive triangle — XZ-plane rib of thickness FLANGE_GUSSET_THK
        # along Y, centred under the servo body.  Its top edge (Z = 0)
        # sits against the porch bottom and its outer vertical edge
        # (X = ±FLANGE_X) coincides with the flange, so it intersects
        # BOTH; it braces inboard over FLANGE_GUSSET_RUN.
        gusset_y_centre = (flange_y_lo + flange_y_hi) / 2.0
        g_x_out = flange_x
        g_x_in = flange_x - side * FLANGE_GUSSET_RUN
        gusset = (
            cq.Workplane("XZ")
            .polyline([(g_x_out, 0), (g_x_in, 0), (g_x_out, -FLANGE_DEPTH)])
            .close()
            .extrude(FLANGE_GUSSET_THK)
            .translate((0, gusset_y_centre + FLANGE_GUSSET_THK / 2.0, 0))
        )
        base = base.union(gusset)
        # M5 mounting hole — drilled along Y through the triangle.
        hole_x = flange_x - side * FLANGE_HOLE_X_INBOARD
        hole_z = -FLANGE_HOLE_Z_BELOW_BASE
        hole = (
            cq.Workplane("XZ")
            .center(hole_x, hole_z)
            .circle(FLANGE_HOLE_DIA / 2.0)
            .extrude(FLANGE_GUSSET_THK + 2.0)
            .translate((0, gusset_y_centre + (FLANGE_GUSSET_THK + 2.0) / 2.0, 0))
        )
        base = base.cut(hole)

    # ---- M5 mounting holes (4 holes near the four tab corners) --------
    # Per Will's reviews (comment 4721011696 + pullrequestreview-4509355231:
    # "move the mounting holes to match the placements of the green holes
    # in the drawing") — used to bolt this part onto a separate leg/frame
    # assembly.  Two near the chamfered rear corners, two near the front.
    for sx in (-BASE_MOUNT_HOLE_X, +BASE_MOUNT_HOLE_X):
        for sy in (BASE_MOUNT_HOLE_Y_REAR, BASE_MOUNT_HOLE_Y_FRONT):
            hole = (
                cq.Workplane("XY")
                .workplane(offset=BASE_T + 1.0)
                .center(sx, sy)
                .circle(BASE_MOUNT_HOLE_DIA / 2.0)
                .extrude(-(BASE_T + 2.0))
            )
            base = base.cut(hole)

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

    # Pinions (both sides) sit on the baseplate; neither should interfere.
    for tag, x_lo in (("pinion+X∩base (servo install)", PINION_X_LO),
                      ("pinion-X∩base (servo install)", PINION_X_LO_NEG)):
        pinion = build_servo_pinion().translate((x_lo, PINION_Y, PINION_Z))
        inter = pinion.val().intersect(bp.val())
        vol = inter.Volume() if inter is not None else 0.0
        results[tag] = vol

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

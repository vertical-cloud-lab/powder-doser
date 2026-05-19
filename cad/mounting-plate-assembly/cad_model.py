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

# --- Baseplate --------------------------------------------------------
BASE_W = 200.0
BASE_L = 250.0
BASE_T = 6.0
BASE_LEG_H = 95.0
BASE_LEG_W = 18.0
BASE_LEG_INSET = 12.0

# Baseplate position — front edge 10 mm BEHIND the hinge axis
# (= the hinge axis is 10 mm forward of the baseplate's front edge,
# per the issue #62 follow-up drawing).
BASE_Y_FRONT = Y_DISP - 10.0                               # +115
BASE_Y_BACK  = BASE_Y_FRONT - BASE_L                       # -135
BASE_Y_CENTRE = (BASE_Y_FRONT + BASE_Y_BACK) / 2.0

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

# --- Linear-actuator base clevis on baseplate top ---------------------
ACT_BASE_Y = -110.0
ACT_BASE_W = 16.0
ACT_BASE_T = 10.0
ACT_BASE_H = 30.0
ACT_BASE_BORE_D = 5.4

# Hardware
M3_CLEAR = 3.4
M5_CLEAR = 5.4


# --------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------- #
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

    return plate


def build_baseplate() -> cq.Workplane:
    """Bench-side plate with two forward-and-up hinge arms (one each
    side of the auger).  No powder window — powder falls in front of
    the baseplate (the dispense point sits 10 mm forward of the base
    front edge)."""
    base = (
        cq.Workplane("XY")
        .box(BASE_W, BASE_L, BASE_T, centered=(True, True, False))
        .translate((0, BASE_Y_CENTRE, 0))
    )

    # Corner legs (drop the bench-side plate to give cup + scale
    # clearance in front of the baseplate).
    leg_x = BASE_W / 2 - BASE_LEG_INSET - BASE_LEG_W / 2
    leg_y_front = BASE_Y_FRONT - BASE_LEG_INSET - BASE_LEG_W / 2
    leg_y_back  = BASE_Y_BACK  + BASE_LEG_INSET + BASE_LEG_W / 2
    for sx in (+leg_x, -leg_x):
        for sy in (leg_y_front, leg_y_back):
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
    HINGE_R = HINGE_EYE_OD / 2.0
    arm_top_local = HINGE_AXIS_Z_LOCAL + HINGE_R
    arm_spans = (
        (HINGE_X1 + HINGE_LAYER_GAP / 2,  HINGE_X2 - HINGE_LAYER_GAP / 2),
        (-HINGE_X2 + HINGE_LAYER_GAP / 2, -HINGE_X1 - HINGE_LAYER_GAP / 2),
    )
    for x_lo, x_hi in arm_spans:
        arm = (
            cq.Workplane("YZ")
            .workplane(offset=x_lo)
            .moveTo(BASE_Y_FRONT, BASE_T)
            .lineTo(Y_DISP, BASE_T)
            .lineTo(Y_DISP, arm_top_local)
            .lineTo(BASE_Y_FRONT, arm_top_local)
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

    # Linear-actuator base clevis on baseplate TOP (z = BASE_T+).
    clevis = (
        cq.Workplane("XY")
        .box(ACT_BASE_W, ACT_BASE_T, ACT_BASE_H, centered=(True, True, False))
        .translate((0, ACT_BASE_Y, BASE_T))
    )
    base = base.union(clevis)
    clevis_bore = (
        cq.Workplane("YZ")
        .workplane(offset=-(ACT_BASE_W / 2.0 + 1.0))
        .center(ACT_BASE_Y, BASE_T + ACT_BASE_H - 6.0)
        .circle(ACT_BASE_BORE_D / 2.0)
        .extrude(ACT_BASE_W + 2.0)
    )
    base = base.cut(clevis_bore)

    # Translate the whole baseplate so its bottom face sits at Z_BASE_TOP.
    return base.translate((0, 0, Z_BASE_TOP))


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


if __name__ == "__main__":
    main()

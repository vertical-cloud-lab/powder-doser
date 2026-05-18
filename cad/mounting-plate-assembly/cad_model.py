"""Mounting plate + hinged baseplate + hinge pins for the powder-doser.

Re-design per the second review on the issue #62 thread (#56 follow-up):

  * All components (brackets, tap-collar mount, NEMA-11 mount block,
    front ramps, hinge eyes) sit on the **TOP** of the mounting plate.
  * The plate has **NO holes other than mounting holes** and **NO gaps**
    other than a single open U-notch in the +Y edge.  The auger
    overhangs through that notch in mid-air; the gear band & pinion
    have *air-clearance* above the plate top.
  * The auger sits **centred on the plate in X** (auger axis at X=0;
    plate is symmetric about X=0 so the central auger gap is in the
    middle of the +Y edge).
  * The brackets bolt **directly to the plate top** with no plinths
    (per the third review).  The auger centreline therefore sits at
    the bracket's native bore height above the plate top.
  * The hinge is **split into two separate hinges** — one on each
    side of the auger, **equal in size and symmetric about X=0**.
    Each side: one mounting-plate eye + one baseplate-arm eye butted
    axially on a short M5 pin.  Hinge eye thickness has been bumped
    to make the hinges noticeably beefier.
  * Each hinge eye is fed by a **full-width front ramp** rising from
    the plate top to the hinge axis.  Together the two ramps cover the
    entire +Y face of the plate except for the central auger-gap.
  * **No features hang from the plate underside** — the linear-actuator
    rod-end lug from earlier revisions has been removed.
  * The **hinge axis is 10 mm in front of the baseplate's front edge**
    (i.e., the dispense point is held 10 mm clear of the baseplate),
    so the auger dispenses into a cup placed in front of the baseplate.
  * The baseplate carries **two complementary forward-and-up arms**,
    one on each side of the auger, each ending in an eye at the
    hinge axis with a corresponding gap between them.
  * Component order along the auger from the hinge end toward the
    motor end matches the drawing exactly:
        hinge → front bracket → tap collar mount → motor (over the
        gear band) → rear bracket.

Only the **new** parts are generated here (mounting_plate, baseplate,
hinge_pins).  The auger, brackets, tap-collar and motor STLs are
imported verbatim from the upstream PRs in ``imported-parts/``:

  - PR #49 v3 — ``cad/auger-geared/archimedes-auger-geared.stl``,
                ``cad/auger-geared/stepper-pinion.stl``
  - PR #51    — ``design/cad/tap-collar/stl/tap_collar.stl`` +
                ``mount_plate.stl``
  - PR #55    — ``cad/auger-bracket/auger-bracket.stl``

Coordinate frame
================
  +X to the right (looking at the front of the machine from the
                    dispense end)
  +Y forward       (= the direction the auger discharges powder when
                    tilted; the dispense end of the auger is at +Y_DISP)
  +Z up

  Mounting plate top face is at z = 0, bottom at z = -PLATE_T.
  The auger is held above the plate top on integrated **plinths** under
  each bracket footprint (so the gear band tip clears the plate top
  with no through-plate slot).  Auger centreline is at z = Z_AUG.

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

# PR #55 — auger bracket (CadQuery; bore Ø25.4, plate 60 × 25 × 10).
BRK_FLANGE_W = 60.0
BRK_FLANGE_D = 25.0
BRK_FLANGE_T = 10.0
BRK_MOUNT_HOLE_INSET_X = 6.0
BRK_MOUNT_HOLE_D = 3.4
BRK_RING_OD = 35.4
BRK_RING_OR = BRK_RING_OD / 2
BRK_RING_CENTRE_LOCAL_Z = BRK_FLANGE_T + BRK_RING_OR * 0.55  # 19.74 mm

# PR #51 — tap-collar mount plate (60 × 12 × 14, 2 × M3 at X = ±24).
TAP_PLATE_W = 60.0
TAP_PLATE_D = 12.0
TAP_PLATE_T = 14.0
TAP_MOUNT_HOLE_INSET_X = 6.0
TAP_MOUNT_HOLE_D = 3.4
# In the upstream tap-collar STL, the collar bore sits 30.25 mm above
# the bottom of the mount plate (i.e., above the mating face that bolts
# to OUR mounting plate top).  Choosing Z_AUG = this value means the
# tap-collar bolts flat to the plate top with no plinth, while keeping
# the auger axis aligned with the collar bore.
TAP_COLLAR_BORE_LOCAL_Z = 30.25

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
# Component ORDER matches the drawing.
Y_BRK_FRONT = +85.0
Y_TAP       = +60.0
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

# --- Hinge eyes (one each side of the auger gap) -----------------------
# Equal-sized, symmetric about X=0; thicker than the previous pass per
# the third review.
HINGE_EYE_OD = 14.0
HINGE_EYE_ID = 5.4
HINGE_EYE_THK = 10.0
# Inboard X of each mounting-plate eye = outer edge of the auger gap.
HINGE_MP_X_INNER = AUGER_GAP_W / 2.0
# Centreline of each mounting-plate eye in X.
HINGE_MP_X = HINGE_MP_X_INNER + HINGE_EYE_THK / 2.0

# --- Front ramps (one each side of the auger gap) ----------------------
# Each ramp is a right-triangle prism in the YZ plane, extruded along X
# from the auger-gap edge out to the plate X edge for its side.
RAMP_Y_BACK = PLATE_Y_FRONT - 25.0                         # +90
RAMP_TOP_Z = Z_AUG + HINGE_EYE_OD / 2.0                    # +36.25

# --- NEMA-11 motor mount block (on TOP of plate) ----------------------
BOSS_W = NEMA11_BODY_W + 8.0                               # 36.2
BOSS_H = NEMA11_BODY_W + 8.0
BOSS_T = 6.0
MOTOR_FACE_Y = Y_GEAR_BAND - GEAR_BAND_FACE_W / 2.0 - 2.0  # +34.67
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
# Each arm extends forward from the base front edge (Y=BASE_Y_FRONT) to
# the hinge axis (Y=Y_DISP), rising vertically from base top to the
# hinge axis level.  Its eye sits OUTBOARD of the mounting-plate eye on
# the same side (axially butted, sharing one M5 pin per side).
ARM_THK = 8.0
# Inboard X of each baseplate arm = outboard X of the mounting-plate eye.
ARM_X_INNER = HINGE_MP_X_INNER + HINGE_EYE_THK             # 22
ARM_X = ARM_X_INNER + ARM_THK / 2.0                        # 26
# Hinge axis in baseplate's local frame (before final translate).
HINGE_AXIS_Z_LOCAL = Z_AUG - Z_BASE_TOP                    # +44.25

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

    # ---- Gear-band + pinion clearance cutout --------------------------
    # With brackets bolted flat (no plinths), the Ø50 gear band centred
    # at (X=0, Y=Y_GEAR_BAND) and its mating Ø18 pinion at X=+32 dip
    # below the plate top.  A minimum-area through-cutout under just
    # the band+pinion footprint keeps the rest of the plate solid.
    GEAR_SLOT_Y_HALF = (GEAR_BAND_FACE_W + PINION_LEN) / 2.0 + 3.0
    gear_slot = (
        cq.Workplane("XY")
        .workplane(offset=1.0)
        .moveTo(-GEAR_BAND_TIP_DIA / 2 - 3.0, Y_GEAR_BAND)
        .rect(GEAR_BAND_TIP_DIA + 6.0 + GEAR_CENTRE_DISTANCE,
              GEAR_SLOT_Y_HALF * 2.0,
              centered=(False, True))
        .extrude(-(PLATE_T + 2.0))
    )
    plate = plate.cut(gear_slot)

    # ---- Tap-collar mount holes (no plinth — mount sits flush) ---------
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

    # ---- Front ramps (full-width, one each side of the auger gap) ------
    # Each ramp is a right-triangle prism extruded along X.  The
    # triangle (in YZ) is: A=(RAMP_Y_BACK,0), B=(PLATE_Y_FRONT,0),
    # C=(PLATE_Y_FRONT, RAMP_TOP_Z).
    ramp_spans = (
        (+AUGER_GAP_W / 2.0, PLATE_X_MAX),     # +X side
        (PLATE_X_MIN, -AUGER_GAP_W / 2.0),     # -X side
    )
    for x_inner, x_outer in ramp_spans:
        ramp = (
            cq.Workplane("YZ")
            .workplane(offset=x_inner)
            .moveTo(RAMP_Y_BACK, 0)
            .lineTo(PLATE_Y_FRONT, 0)
            .lineTo(PLATE_Y_FRONT, RAMP_TOP_Z)
            .close()
            .extrude(x_outer - x_inner)
        )
        plate = plate.union(ramp)

    # ---- Hinge eyes (one each side of the auger gap) -------------------
    # Each eye is a thin disk extruded outboard from the auger-gap
    # edge, joined to the ramp front face by a small horizontal tab so
    # the bore sits 10 mm forward of the plate edge (= at Y=Y_DISP).
    for side in (+1, -1):
        x_inner = side * (AUGER_GAP_W / 2.0)          # inboard X
        # Horizontal tab from ramp front face out to the eye centre.
        tab_y_back = PLATE_Y_FRONT - 1.0  # 1 mm overlap so union is robust
        tab = (
            cq.Workplane("YZ")
            .workplane(offset=x_inner if side > 0 else x_inner - HINGE_EYE_THK)
            .moveTo(tab_y_back, Z_AUG - HINGE_EYE_OD / 2.0)
            .lineTo(Y_DISP + HINGE_EYE_OD / 2.0, Z_AUG - HINGE_EYE_OD / 2.0)
            .lineTo(Y_DISP + HINGE_EYE_OD / 2.0, Z_AUG + HINGE_EYE_OD / 2.0)
            .lineTo(tab_y_back, Z_AUG + HINGE_EYE_OD / 2.0)
            .close()
            .extrude(HINGE_EYE_THK)
        )
        plate = plate.union(tab)
        # Through-hole along X (M5 clearance).
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=x_inner - 1 if side > 0 else x_inner - HINGE_EYE_THK - 1)
            .center(Y_DISP, Z_AUG)
            .circle(HINGE_EYE_ID / 2.0)
            .extrude(HINGE_EYE_THK + 2)
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

    # Forward-and-up hinge arms.  Each arm is a YZ rectangle from
    # (BASE_Y_FRONT, BASE_T) to (Y_DISP, HINGE_AXIS_Z_LOCAL + HINGE_EYE_OD/2)
    # extruded ARM_THK along X.  The arm carries the M5 bore at
    # (Y_DISP, HINGE_AXIS_Z_LOCAL).  Each side gets its own arm so the
    # auger has a central gap between them, mirroring the mounting plate.
    arm_top_local = HINGE_AXIS_Z_LOCAL + HINGE_EYE_OD / 2.0
    for side in (+1, -1):
        x_inner = side * ARM_X_INNER                        # ±22
        x_outer = side * (ARM_X_INNER + ARM_THK)            # ±30
        # 4-point arm profile (rectangle in YZ).
        arm = (
            cq.Workplane("YZ")
            .workplane(offset=x_inner if side > 0 else x_outer)
            .moveTo(BASE_Y_FRONT, BASE_T)
            .lineTo(Y_DISP + HINGE_EYE_OD / 2.0, BASE_T)
            .lineTo(Y_DISP + HINGE_EYE_OD / 2.0, arm_top_local)
            .lineTo(BASE_Y_FRONT, arm_top_local)
            .close()
            .extrude(ARM_THK)
        )
        base = base.union(arm)
        # M5 bore along X through the arm at the hinge axis.
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=(x_inner if side > 0 else x_outer) - 1)
            .center(Y_DISP, HINGE_AXIS_Z_LOCAL)
            .circle(HINGE_EYE_ID / 2.0)
            .extrude(ARM_THK + 2)
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
    """A pair of short M5 pins (one per side), separated by the auger
    gap.  Each pin spans the mounting-plate eye + baseplate arm eye on
    its side, with 2 mm of slop at each end."""
    pin_len = HINGE_EYE_THK + ARM_THK + 4.0
    # Pin centre X (on +X side): centred over its (eye + arm) pair.
    x_centre_plus = AUGER_GAP_W / 2.0 + (HINGE_EYE_THK + ARM_THK) / 2.0
    pin_plus = (
        cq.Workplane("YZ")
        .circle(5.0 / 2.0)
        .extrude(pin_len)
        .translate((x_centre_plus - pin_len / 2.0, 0, 0))
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
    print(f"Hinge eye OD × thickness     : {HINGE_EYE_OD:.1f} × {HINGE_EYE_THK:.1f} mm "
          f"(equal-sized, mirror-symmetric about X=0)")
    print(f"Ramp top Z                   : {RAMP_TOP_Z:+.2f} mm")
    print(f"Hinge axis                   : X-axis through (Y={Y_DISP:+.2f}, Z={Z_AUG:+.2f})")
    print(f"Baseplate front edge Y       : {BASE_Y_FRONT:+.2f} (hinge axis "
          f"= front edge + {Y_DISP - BASE_Y_FRONT:.0f} mm)")
    print(f"Component order (Y, hinge→far): brkF={Y_BRK_FRONT:+.0f}  "
          f"tap={Y_TAP:+.0f}  motor={Y_GEAR_BAND:+.2f}  brkR={Y_BRK_REAR:+.0f}")


if __name__ == "__main__":
    main()

"""Mounting plate + baseplate + hinge pin for the powder-doser.

Only the **new** parts in this package are generated here: the mounting
plate (top half of the rotating sub-assembly, carries two PR#55 brackets,
one PR#51 tap-collar mount and one NEMA 11 motor that drives the PR#49
geared auger), the baseplate (sits on the bench, has a central hinge
tang and a powder-fall window) and the M5 hinge pin that joins them.

Every other part used in the assembly renderer is **imported** from its
own upstream PR — see ``imported-parts/``:

  - PR #49 v3 — ``cad/auger-geared/archimedes-auger-geared.stl``,
                ``cad/auger-geared/stepper-pinion.stl``
  - PR #51    — ``design/cad/tap-collar/stl/tap_collar.stl`` (the
                rotating split-collar; the mount-plate it bolts to is
                ``design/cad/tap-collar/stl/mount_plate.stl``)
  - PR #55    — ``cad/auger-bracket/auger-bracket.stl``

Coordinate frame
================

  +X to the right (looking at the front of the machine)
  +Y forward (= the direction the auger discharges powder when tilted)
  +Z up

The mounting plate's top face is at z = 0, bottom at z = -PLATE_T.
The auger lies horizontal along +Y; its centreline at
(x = 0, z = Z_AUG = -PLATE_T - (BRK_RING_CENTRE_LOCAL_Z - BRK_FLANGE_T))
because the two PR#55 brackets are bolted FLANGE-UP to the plate
underside, so the bracket's bore ends up below the plate.

The hinge axis is the global x-axis at (y = Y_DISP, z = Z_AUG); a single
M5 pin passes through the mounting plate's left yoke eye, through the
baseplate's central tang, and out the mounting plate's right yoke eye.
Rotation about this axis tilts the auger from horizontal (0°) to
straight-down (90°) about its own dispense point — no hinge hardware
ever crosses the powder path.

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
AUGER_OD = 25.0                       # tube outside diameter
AUGER_LEN = 250.0                     # full-length variant
GEAR_BAND_AXIAL_FROM_DISP = AUGER_LEN / 3.0   # 83.33 mm from dispensing end
GEAR_BAND_FACE_W = 10.0               # axial width of gear band
GEAR_BAND_TIP_DIA = 50.0              # tip diameter of the 48-tooth band
PINION_TIP_DIA = 18.0                 # 16-tooth pinion
GEAR_CENTRE_DISTANCE = 32.0           # parallel-axis spacing pinion <-> auger
PINION_LEN = 16.0
NEMA11_BODY_W = 28.2                  # square cross-section
NEMA11_BODY_L = 32.0                  # along motor axis
NEMA11_FACE_HOLE_PITCH = 23.0         # M2.5 corner-hole pitch on motor face
NEMA11_PILOT_DIA = 22.0               # central pilot Ø
NEMA11_SCREW_CLEAR = 3.0              # M2.5 clearance (use M3 hardware in plate)
NEMA11_SHAFT_DIA = 5.0
NEMA11_SHAFT_LEN = 18.0               # shaft length out the front face

# PR #55 — auger bracket (CadQuery; bore Ø25.4, plate 60 × 25 × 10).
BRK_FLANGE_W = 60.0                   # along X
BRK_FLANGE_D = 25.0                   # along Y (auger axis)
BRK_FLANGE_T = 10.0                   # Z
BRK_MOUNT_HOLE_INSET_X = 6.0          # from each X end → hole centre at ±24
BRK_MOUNT_HOLE_D = 3.4                # M3 clearance through plate
BRK_RING_OD = 35.4
BRK_RING_OR = BRK_RING_OD / 2
# In the bracket's native frame the flange bottom is at z=0 and the ring
# centre is at z = FLANGE_T + RING_OR * 0.55 (see PR #55 source).
BRK_RING_CENTRE_LOCAL_Z = BRK_FLANGE_T + BRK_RING_OR * 0.55  # 19.74 mm

# PR #51 — tap-collar mount plate (60 × 12 × 14, 2 × M3 at X = ±24).
TAP_PLATE_W = 60.0                    # X
TAP_PLATE_D = 12.0                    # Y
TAP_PLATE_T = 14.0                    # Z
TAP_MOUNT_HOLE_INSET_X = 6.0
TAP_MOUNT_HOLE_D = 3.4

# --------------------------------------------------------------------- #
# Mounting plate parameters (the ONLY parts we generate here).
# --------------------------------------------------------------------- #
PLATE_W = 120.0       # X — wide enough for the NEMA 11 boss at X=+32
PLATE_L = 220.0       # Y — covers the bracket span (Y=±95) with margin;
                      # yoke arms extend forward past the +Y edge to the
                      # dispense point at Y = +125.
PLATE_T = 6.0         # Z — thickness

# Auger centred along the plate's Y axis. Dispense end at +Y.
Y_DISP = AUGER_LEN / 2                 # +125 mm — front edge of auger
Y_REAR = -AUGER_LEN / 2                # -125 mm — motor end of auger
Y_GEAR_BAND = Y_DISP - GEAR_BAND_AXIAL_FROM_DISP   # +41.67 mm

# Auger centreline Z, set by the bracket geometry: brackets bolt FLANGE-UP
# to the plate underside (flange-bottom mating face mates against plate
# underside at z = -PLATE_T), and the bracket's bore centre is at
# BRK_RING_CENTRE_LOCAL_Z above its native flange-bottom — so the bore
# ends up that far BELOW the plate underside after the flip-and-mate.
Z_AUG = -(PLATE_T + BRK_RING_CENTRE_LOCAL_Z)   # -25.74 mm

# Baseplate sits BELOW the mounting plate, on the bench. Its top surface
# is set well below the auger so the assembly can tilt 0..90° about the
# hinge axis (at Y_DISP, Z_AUG) without the tilting auger crashing into
# the baseplate. The hinge tang rises from the baseplate top up to the
# auger centreline (Z_AUG) where the hinge pin passes through.
Z_BASE_TOP = -55.0                              # 39.3 mm below the auger
                                                 # = AUGER_OD/2 + 26.8 mm gap

# Bracket Y positions: near the auger ends, well clear of the gear band
# (Y = +41.67 ± 5) and the tap-collar (Y = -40).
Y_BRK_FRONT = +95.0
Y_BRK_REAR  = -95.0

# Tap-collar mount Y — between gear band and rear bracket, leaving
# clearance on both sides.
Y_TAP = -40.0

# NEMA 11 mount: motor axis parallel to auger, pinion shaft pointing in
# +Y so the pinion sits over the gear band at Y = Y_GEAR_BAND.
# Motor body centre Y = Y_GEAR_BAND - PINION_LEN - NEMA11_BODY_L/2 + face_overshoot.
# We mount the motor face flush against an integrated boss on the plate
# underside; the boss face is at Y = MOTOR_FACE_Y, motor extends in -Y.
MOTOR_FACE_Y = Y_GEAR_BAND - GEAR_BAND_FACE_W / 2.0 - 2.0   # 2 mm air gap
# Pinion centred axially on the gear band → pinion length straddles the
# band evenly: pinion centre Y = Y_GEAR_BAND, pinion z aligned to Z_AUG.
# Motor centre X offset by the gear-mesh centre distance.
X_MOTOR = +GEAR_CENTRE_DISTANCE              # +32 mm
Z_MOTOR = Z_AUG                              # parallel-axis with auger

# Motor mount boss (drops from plate underside to hold the motor face in
# the right XYZ). The boss face is a vertical wall at Y = MOTOR_FACE_Y
# facing +Y; bolts pass THROUGH the boss into the motor's M2.5 face holes.
BOSS_W = NEMA11_BODY_W + 2 * 4.0             # 28.2 + 8 = 36.2 mm
BOSS_H = NEMA11_BODY_W + 2 * 4.0             # square block in (X,Z)
BOSS_T = 4.0                                 # wall thickness along Y
# Boss centred on (X_MOTOR, Z_MOTOR), spanning Y = [MOTOR_FACE_Y, MOTOR_FACE_Y + BOSS_T]

# Hinge yoke (forward of the plate's +Y edge, eyes coaxial with the
# auger's dispense point).
YOKE_ARM_LEN = Y_DISP - PLATE_L / 2 + 25.0   # arm reaches from the plate
                                              # +Y edge to past the auger tip
YOKE_EYE_OD = 14.0
YOKE_EYE_ID = 5.4                            # M5 hinge pin clearance
YOKE_EYE_GAP = 26.0                          # central powder slot
YOKE_DROP_W = YOKE_EYE_OD                    # drop-leg cross-section

# Linear-actuator rod-end pivot lug on plate underside.
ACT_LUG_Y = -60.0
ACT_LUG_T = 8.0                              # along Y
ACT_LUG_W = 12.0                             # along X
ACT_LUG_H = 24.0                             # how far it drops below plate
ACT_LUG_BORE_D = 5.4                         # M5 clearance

# Baseplate dimensions (sits on the bench, has central tang + powder
# window + linear-actuator clevis + four corner legs).
BASE_W = 200.0
BASE_L = 320.0
BASE_T = 6.0
BASE_LEG_H = 95.0                            # clears 50 mm cup + 30 mm scale
BASE_LEG_W = 18.0                            # square leg cross-section
BASE_LEG_INSET = 12.0                        # legs inset from each corner

WINDOW_W = 60.0                              # powder-fall hole
WINDOW_L = 60.0
WINDOW_Y = Y_DISP                            # directly below the dispense point

# Central tang on baseplate top — fits in the yoke gap, bored for the
# hinge pin along X.
TANG_W = YOKE_EYE_GAP - 0.4                  # 0.2 mm clearance per side
TANG_T = YOKE_EYE_OD + 6.0                   # in Y
# Tang rises from baseplate TOP up to past the auger centreline by 8 mm.
TANG_H = (Z_AUG + 8.0) - Z_BASE_TOP          # ≈ 47.3 mm
TANG_Y = WINDOW_Y                            # tang centred on dispense
TANG_HINGE_Z = Z_AUG                         # hinge bore at auger centreline

# Linear-actuator base clevis on baseplate.
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
def _hole_along_z(x: float, y: float, dia: float, depth: float = PLATE_T + 2.0,
                  z_top: float = 1.0) -> cq.Workplane:
    """Through-hole along -Z, centred at (x, y, z_top)."""
    return (
        cq.Workplane("XY")
        .workplane(offset=z_top)
        .center(x, y)
        .circle(dia / 2)
        .extrude(-depth)
    )


def build_mounting_plate() -> cq.Workplane:
    """Top plate: carries 2 brackets + tap-collar + NEMA 11 + yoke + lug."""
    plate = (
        cq.Workplane("XY")
        .box(PLATE_W, PLATE_L, PLATE_T, centered=(True, True, False))
        .translate((0, 0, -PLATE_T))
    )

    # ------ Bracket mount holes (PR #55: 2 × M3 at X = ±24, on plate Y) ----
    brk_x = BRK_FLANGE_W / 2 - BRK_MOUNT_HOLE_INSET_X       # 24
    for cy in (Y_BRK_FRONT, Y_BRK_REAR):
        for sx in (+brk_x, -brk_x):
            plate = plate.cut(_hole_along_z(sx, cy, M3_CLEAR))

    # ------ Tap-collar mount holes (PR #51: 2 × M3 at X = ±24, Y = Y_TAP) --
    tap_x = TAP_PLATE_W / 2 - TAP_MOUNT_HOLE_INSET_X        # 24
    for sx in (+tap_x, -tap_x):
        plate = plate.cut(_hole_along_z(sx, Y_TAP, M3_CLEAR))

    # ------ NEMA 11 mount boss on plate underside -------------------------
    # The boss is a small block whose +Y face mates with the motor face.
    # Its bottom Z encloses the motor body; its top Z bites a couple of mm
    # into the plate underside so the union with the plate is solid.
    boss_top_z = -PLATE_T + 1.0
    boss_bot_z = Z_MOTOR - NEMA11_BODY_W / 2 - 4.0
    boss_h = boss_top_z - boss_bot_z
    boss_centre_z = (boss_top_z + boss_bot_z) / 2
    boss = (
        cq.Workplane("XY")
        .box(BOSS_W, BOSS_T, boss_h, centered=(True, True, True))
        .translate((X_MOTOR, MOTOR_FACE_Y + BOSS_T / 2, boss_centre_z))
    )
    plate = plate.union(boss)
    # M3 mount holes through the boss into the motor face (4 corners +
    # central pilot for the shaft + pinion).
    for sx in (+NEMA11_FACE_HOLE_PITCH / 2, -NEMA11_FACE_HOLE_PITCH / 2):
        for sz in (+NEMA11_FACE_HOLE_PITCH / 2, -NEMA11_FACE_HOLE_PITCH / 2):
            hole = (
                cq.Workplane("XZ")
                .workplane(offset=-(MOTOR_FACE_Y + BOSS_T + 1))  # XZ-plane is at Y=0
                .center(X_MOTOR + sx, Z_MOTOR + sz)
                .circle(M3_CLEAR / 2)
                .extrude(BOSS_T + 2)
            )
            plate = plate.cut(hole)
    pilot = (
        cq.Workplane("XZ")
        .workplane(offset=-(MOTOR_FACE_Y + BOSS_T + 1))
        .center(X_MOTOR, Z_MOTOR)
        .circle(NEMA11_PILOT_DIA / 2)
        .extrude(BOSS_T + 2)
    )
    plate = plate.cut(pilot)

    # ------ Forward yoke: two arms + drop legs + eyes ---------------------
    arm_offset_x = YOKE_EYE_GAP / 2 + YOKE_EYE_OD / 2
    arm_w = YOKE_EYE_OD
    arm_y0 = PLATE_L / 2
    arm_y1 = Y_DISP                              # eye at the dispense point
    arm_len = arm_y1 - arm_y0
    for side in (+1, -1):
        cx = side * arm_offset_x
        # Horizontal arm (continues the plate forward at plate level)
        arm = (
            cq.Workplane("XY")
            .box(arm_w, arm_len + 2, PLATE_T, centered=(True, True, False))
            .translate((cx, (arm_y0 + arm_y1) / 2, -PLATE_T))
        )
        plate = plate.union(arm)
        # Vertical drop leg from plate bottom down to the eye centreline.
        drop_h = abs(Z_AUG - (-PLATE_T)) + YOKE_EYE_OD / 2
        drop = (
            cq.Workplane("XY")
            .box(arm_w, arm_w, drop_h, centered=(True, True, False))
            .translate((cx, arm_y1, -PLATE_T - drop_h))
        )
        plate = plate.union(drop)
        # Eye disc — bore axis along X (perpendicular to auger Y), centred
        # on the auger centreline Z = Z_AUG.
        eye = (
            cq.Workplane("YZ")
            .workplane(offset=cx - YOKE_EYE_OD / 2)
            .center(arm_y1, Z_AUG)
            .circle(YOKE_EYE_OD / 2)
            .extrude(YOKE_EYE_OD)
        )
        plate = plate.union(eye)
        # Hinge pin bore
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=cx - YOKE_EYE_OD)
            .center(arm_y1, Z_AUG)
            .circle(YOKE_EYE_ID / 2)
            .extrude(YOKE_EYE_OD * 2 + 1)
        )
        plate = plate.cut(bore)

    # ------ Powder-fall slot through the plate (front section) ------------
    slot_w = YOKE_EYE_GAP
    slot_l = 50.0
    slot_y_centre = PLATE_L / 2 - slot_l / 2 + 2
    slot = (
        cq.Workplane("XY")
        .workplane(offset=1)
        .center(0, slot_y_centre)
        .rect(slot_w, slot_l)
        .extrude(-(PLATE_T + 2))
    )
    plate = plate.cut(slot)

    # ------ Gear-band / pinion clearance slot -----------------------------
    # The PR#49 auger gear band (Ø50 tip) and the pinion (Ø18 at X=+32) both
    # extend above the plate bottom by a few mm at Y = Y_GEAR_BAND, so cut a
    # rectangular clearance slot through the plate covering both.
    gb_clearance_w = (X_MOTOR + PINION_TIP_DIA / 2 + 2.0) - (-(GEAR_BAND_TIP_DIA / 2) - 2.0)
    gb_clearance_x_centre = (X_MOTOR + PINION_TIP_DIA / 2 + 2.0 + -(GEAR_BAND_TIP_DIA / 2) - 2.0) / 2
    gb_clearance_l = GEAR_BAND_FACE_W + 6.0
    gb_slot = (
        cq.Workplane("XY")
        .workplane(offset=1)
        .center(gb_clearance_x_centre, Y_GEAR_BAND)
        .rect(gb_clearance_w, gb_clearance_l)
        .extrude(-(PLATE_T + 2))
    )
    plate = plate.cut(gb_slot)

    # ------ Linear-actuator rod-end pivot lug on underside ----------------
    lug = (
        cq.Workplane("XY")
        .box(ACT_LUG_W, ACT_LUG_T, ACT_LUG_H, centered=(True, True, False))
        .translate((0, ACT_LUG_Y, -PLATE_T - ACT_LUG_H))
    )
    plate = plate.union(lug)
    lug_bore = (
        cq.Workplane("YZ")
        .workplane(offset=-(ACT_LUG_W / 2 + 1))
        .center(ACT_LUG_Y, -PLATE_T - ACT_LUG_H + 6)
        .circle(ACT_LUG_BORE_D / 2)
        .extrude(ACT_LUG_W + 2)
    )
    plate = plate.cut(lug_bore)

    return plate


def build_baseplate() -> cq.Workplane:
    """Bench-side plate: legs, central hinge tang, powder window, actuator clevis."""
    base = (
        cq.Workplane("XY")
        .box(BASE_W, BASE_L, BASE_T, centered=(True, True, False))
    )

    # Corner legs
    for sx in (+(BASE_W / 2 - BASE_LEG_INSET - BASE_LEG_W / 2),
               -(BASE_W / 2 - BASE_LEG_INSET - BASE_LEG_W / 2)):
        for sy in (+(BASE_L / 2 - BASE_LEG_INSET - BASE_LEG_W / 2),
                   -(BASE_L / 2 - BASE_LEG_INSET - BASE_LEG_W / 2)):
            leg = (
                cq.Workplane("XY")
                .box(BASE_LEG_W, BASE_LEG_W, BASE_LEG_H, centered=(True, True, False))
                .translate((sx, sy, -BASE_LEG_H))
            )
            base = base.union(leg)

    # Powder window directly under the dispense point
    win = (
        cq.Workplane("XY")
        .workplane(offset=-1)
        .center(0, WINDOW_Y)
        .rect(WINDOW_W, WINDOW_L)
        .extrude(BASE_T + 2)
    )
    base = base.cut(win)

    # Central hinge tang — solid block on top, bored for the hinge pin
    # Tang bore centred at TANG_HINGE_Z (= Z_AUG). In this builder we work
    # in a local frame where the baseplate top is at z=BASE_T (untranslated);
    # the final translate to Z_BASE_TOP at the end of the function shifts
    # everything down so the tang bore lands on Z_AUG exactly.
    tang = (
        cq.Workplane("XY")
        .box(TANG_W, TANG_T, TANG_H, centered=(True, True, False))
        .translate((0, TANG_Y, BASE_T))
    )
    base = base.union(tang)
    # Bore at z = (TANG_HINGE_Z - Z_BASE_TOP) above the baseplate bottom
    # (= local z origin), which after translation lands on Z_AUG.
    tang_bore_local_z = TANG_HINGE_Z - Z_BASE_TOP
    tang_bore = (
        cq.Workplane("YZ")
        .workplane(offset=-(TANG_W / 2 + 1))
        .center(TANG_Y, tang_bore_local_z)
        .circle(YOKE_EYE_ID / 2)
        .extrude(TANG_W + 2)
    )
    base = base.cut(tang_bore)

    # Linear-actuator base clevis (single tab with X-bore). Pivot z chosen
    # so the actuator line stays clear of the hinge tang.
    clevis = (
        cq.Workplane("XY")
        .box(ACT_BASE_W, ACT_BASE_T, ACT_BASE_H, centered=(True, True, False))
        .translate((0, ACT_BASE_Y, BASE_T))
    )
    base = base.union(clevis)
    clevis_bore = (
        cq.Workplane("YZ")
        .workplane(offset=-(ACT_BASE_W / 2 + 1))
        .center(ACT_BASE_Y, BASE_T + ACT_BASE_H - 6)
        .circle(ACT_BASE_BORE_D / 2)
        .extrude(ACT_BASE_W + 2)
    )
    base = base.cut(clevis_bore)

    # Translate the whole baseplate so its top face sits at Z_BASE_TOP.
    return base.translate((0, 0, Z_BASE_TOP))


def build_hinge_pin() -> cq.Workplane:
    """M5-pattern hinge pin: long enough to span both yoke eyes + tang."""
    length = YOKE_EYE_GAP + 2 * YOKE_EYE_OD + 4
    return (
        cq.Workplane("YZ")
        .circle(5.0 / 2)
        .extrude(length)
        .translate((-length / 2, 0, 0))
    )


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
    print(f"Auger centreline Z (Z_AUG)   : {Z_AUG:.2f} mm")
    print(f"Gear band Y (Y_GEAR_BAND)    : {Y_GEAR_BAND:.2f} mm")
    print(f"Motor centre (X,Y,Z)         : ({X_MOTOR}, {MOTOR_FACE_Y - NEMA11_BODY_L/2:.2f}, {Z_MOTOR:.2f}) mm")
    print(f"Hinge axis Y (Y_DISP)        : {Y_DISP:.2f} mm  (auger dispense point)")


if __name__ == "__main__":
    main()

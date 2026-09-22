"""Parametric mounting plate + baseplate + hinge pin for the powder-doser.

Issue: vertical-cloud-lab/powder-doser#62 ("Mounting Plate Design").

This package generates three new, 3D-print-ready parts:

  * ``mounting_plate``  — the rotating board that carries the auger
    sub-assembly (2 × auger bracket, 1 × tap-collar mount plate, 1 × NEMA-11
    motor on a motor-mounting block).
  * ``baseplate``       — the bench-side board with hinge posts that the
    mounting plate pins onto.
  * ``hinge_pin``       — the M5 pin that joins one mounting-plate knuckle
    to one baseplate post (×2 pins total in the assembly).

Hinge layout (matches the user's "Hinge Design (offset)" sketch)
================================================================

The mounting plate carries two **triangular hinge knuckles** along its
rear edge (low-Y edge in our frame).  Each knuckle is a right-triangle
gusset that drops past the bottom of the plate and ends in a circular eye
whose axis runs along +X (parallel to the rear edge).  The baseplate has
two matching **upright posts**, also tipped with an eye on the same axis;
each post slots into the gap beside its mating knuckle and a single M5 pin
joins the pair.  The eyes are offset BELOW the plane of the mounting plate
so that when the plate is rotated 90° upward it stands vertically beside
the hinge posts without the plate underside colliding with them.

The auger is laid lengthwise along +Y on the mounting plate; the
dispense end of the auger overhangs the FRONT (+Y) edge of the plate so
that at 90° tilt the auger points straight DOWN past the baseplate and
delivers powder to a cup placed below.

Coordinate frame
----------------

  +X to the right (looking at the front of the machine)
  +Y forward (auger discharge direction)
  +Z up

The mounting plate's top face is at z = 0, bottom at z = -PLATE_T.
The auger centreline at (x = 0, z = Z_AUG) — see Z_AUG derivation below.
The hinge axis lies along +X at (y = HINGE_Y, z = HINGE_Z).

Run from the package directory to (re)generate STEPs + STLs::

    cd cad/mounting-plate
    python3 cad_model.py
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq

# --------------------------------------------------------------------- #
# Imported-part dimensions — kept in lock-step with the source PRs.
# Any change here MUST be matched against the upstream cad_model.py
# in each referenced PR.  We do NOT consume the upstream STEP/STL here;
# instead we replicate just the dimensions we need to size the plate's
# hole pattern and motor-mount boss correctly.
# --------------------------------------------------------------------- #

# PR #49 v3 — Ø25 × 250 mm geared Archimedes auger + NEMA 11 + pinion.
AUGER_OD: float = 25.0
AUGER_LEN: float = 250.0
GEAR_BAND_AXIAL_FROM_DISP: float = AUGER_LEN / 3.0     # 83.33 mm from dispense end
GEAR_BAND_FACE_W: float = 10.0                          # axial width of gear band
GEAR_BAND_TIP_DIA: float = 50.0                         # 48-tooth band tip Ø
PINION_TIP_DIA: float = 18.0                            # 16-tooth pinion tip Ø
GEAR_CENTRE_DISTANCE: float = 32.0                      # parallel-axis spacing
NEMA11_BODY_W: float = 28.2                             # square body, side length
NEMA11_BODY_L: float = 32.0                             # along motor axis
NEMA11_FACE_HOLE_PITCH: float = 23.0                    # M2.5 face-hole pitch
NEMA11_PILOT_DIA: float = 22.0                          # central pilot Ø

# PR #55 — auger bracket (split shaft-collar with flat flange).
BRK_FLANGE_W: float = 60.0                              # along X
BRK_FLANGE_D: float = 25.0                              # along Y
BRK_FLANGE_T: float = 10.0                              # Z
BRK_MOUNT_HOLE_INSET_X: float = 6.0                     # → hole at X = ±24
BRK_RING_OD: float = 35.4
# In the bracket's native frame the flange bottom is at z=0 and the bore
# centre is at z = FLANGE_T + RING_OR * 0.55 (see PR #55 source).
BRK_RING_CENTRE_LOCAL_Z: float = BRK_FLANGE_T + (BRK_RING_OD / 2) * 0.55

# PR #51 — tap-collar mount plate.
TAP_PLATE_W: float = 60.0                               # X
TAP_PLATE_D: float = 12.0                               # Y
TAP_PLATE_T: float = 14.0                               # Z
TAP_MOUNT_HOLE_INSET_X: float = 6.0                     # → hole at X = ±24

# Hardware clearances.
M3_CLEAR: float = 3.4
M5_CLEAR: float = 5.4
M5_PIN_DIA: float = 5.0

# --------------------------------------------------------------------- #
# Mounting plate parameters (the ONLY parts we generate here).
# --------------------------------------------------------------------- #
# Plate footprint is sized to enclose:
#   * 2 brackets at Y = ±95 (flange 60 × 25)         → needs Y span ≥ 220
#   * the tap-collar mount at Y = -40 (60 × 12)      → already inside
#   * the motor boss at (X = +32, Y = motor_face)    → needs X span ≥ ~90
# We trim the "unnecessary space" the user called out by making the plate
# rectangular and tight to the parts rather than including a wide
# right-hand panel.
PLATE_W: float = 110.0       # X — fits motor boss at X=+32 (half-width 18.1)
PLATE_L: float = 220.0       # Y — fits brackets at Y=±95 (flange ±12.5)
PLATE_T: float = 6.0         # Z — thickness (rigid in PLA at 100% infill)

# Auger lies along Y, centred on the plate's Y axis.  The hinge sits at
# the +Y edge of the plate so that at 90° tilt the dispense end ends up
# DOWNWARD past the hinge (powder falls naturally) and the closed
# motor end ends up UP (no powder spill at the rear).
Y_DISP: float = AUGER_LEN / 2                      # +125 mm (dispense end)
Y_REAR: float = -AUGER_LEN / 2                     # -125 mm (closed/motor end)
Y_GEAR_BAND: float = Y_DISP - GEAR_BAND_AXIAL_FROM_DISP  # +41.67 mm

# Auger centreline Z is set by the bracket geometry: brackets bolt
# FLANGE-DOWN to the plate's TOP face (flange mating surface against the
# plate at z=0, bracket extends upward).  The bracket's bore centre is at
# BRK_RING_CENTRE_LOCAL_Z above its flange-bottom — so the auger ends up
# that far ABOVE the plate top.
Z_AUG: float = BRK_RING_CENTRE_LOCAL_Z             # +19.74 mm above plate top

# Bracket Y positions — near the auger ends, well clear of the gear band
# (Y = +41.67 ± 5) and the tap-collar.  Per the user's sketch, the
# tap-collar and front bracket sit on the HINGE/dispense side (near +Y).
Y_BRK_FRONT: float = +95.0     # near dispense + hinge
Y_BRK_REAR: float = -95.0      # near closed/motor end

# Tap-collar mount Y — between the front bracket and the dispense end,
# per the user's drawing ("Tap Collar" sits just above the lowest
# bracket, which is the hinge side).
Y_TAP: float = +75.0

# NEMA 11 motor parallel to auger, pinion shaft in +Y direction so the
# pinion sits over the gear band at Y = Y_GEAR_BAND.  The motor body is
# carried by an integrated boss rising from the plate top face; the
# boss's +Y face mates against the motor face.
MOTOR_FACE_Y: float = Y_GEAR_BAND - GEAR_BAND_FACE_W / 2.0 - 2.0   # 2 mm air gap
X_MOTOR: float = +GEAR_CENTRE_DISTANCE              # +32 mm
Z_MOTOR: float = Z_AUG                              # parallel-axis with auger

# Motor-mount boss (rectangular block on the plate top face).
BOSS_W: float = NEMA11_BODY_W + 2 * 4.0             # 36.2 mm — X span
BOSS_T: float = 6.0                                 # Y wall thickness
BOSS_H: float = Z_MOTOR + NEMA11_BODY_W / 2 + 4.0   # rises to enclose motor
                                                     # bottom (boss base on
                                                     # plate top at z=0)

# Hinge: two knuckles on the FRONT (+Y) edge of the plate, axis along +X.
# The "offset" in the user's sketch refers to the eye being DROPPED below
# the plate plane so that the rotation axis lies underneath the plate;
# at 90° tilt the plate then stands vertically (auger pointing DOWN past
# the hinge edge) without colliding with the baseplate hinge posts.
HINGE_Y: float = +PLATE_L / 2                       # front (+Y) edge of plate
HINGE_EYE_OD: float = 12.0
HINGE_EYE_ID: float = M5_CLEAR                      # M5 pin
HINGE_EYE_WIDTH: float = 8.0                        # along X (eye thickness)
HINGE_DROP: float = 18.0                            # eye centre BELOW plate
HINGE_Z: float = -PLATE_T - HINGE_DROP              # eye centre Z

# Two hinge knuckles, symmetric about X=0.
HINGE_X_OFFSET: float = 30.0                        # distance from X=0 of each
HINGE_KNUCKLE_GUSSET_THK: float = 6.0               # gusset wall thickness (Y)

# Baseplate footprint and hinge posts.  Baseplate sits BELOW the hinge
# axis so its posts rise up to meet the mounting-plate knuckles.  It
# extends in +Y past the hinge to cover the place where the auger's
# dispense end lands at 90° tilt — see ``DISPENSE_Y_AT_90`` below.
BASE_T: float = 6.0
POST_H: float = 28.0                                # post height (rises from
                                                     # baseplate top to eye)
# Baseplate top face Z — eye centre sits POST_H above baseplate top.
Z_BASE_TOP: float = HINGE_Z - POST_H                # baseplate top face Z

# Where the auger's dispense tip lands when the plate is rotated -90°
# about the hinge axis (X-axis at (HINGE_Y, HINGE_Z)).  A point at
# (Y, Z) rotated by -90° about (HINGE_Y, HINGE_Z) maps to
# (HINGE_Y + (Z - HINGE_Z), HINGE_Z - (Y - HINGE_Y)).
DISPENSE_Y_AT_90: float = HINGE_Y + (Z_AUG - HINGE_Z)
DISPENSE_Z_AT_90: float = HINGE_Z - (Y_DISP - HINGE_Y)

# Powder-fall window directly under the 90° dispense landing point.
WINDOW_W: float = 50.0
WINDOW_L: float = 50.0
WINDOW_Y: float = DISPENSE_Y_AT_90

# Baseplate footprint: must enclose the plate's hinge edge (Y = HINGE_Y),
# the hinge posts (slightly behind the plate edge in +Y), AND the
# powder window in front of the hinge in +Y.  Y span: from a margin
# behind the closed motor end of the auger up to a margin past the
# powder window.
BASE_Y_MIN: float = -PLATE_L / 2 - 20.0             # behind closed end
BASE_Y_MAX: float = WINDOW_Y + WINDOW_L / 2 + 20.0  # past window
BASE_L: float = BASE_Y_MAX - BASE_Y_MIN
BASE_Y_CENTRE: float = (BASE_Y_MIN + BASE_Y_MAX) / 2
BASE_W: float = PLATE_W + 40.0                      # wider than plate

# Hinge POST positions on the baseplate — placed just OUTSIDE the plate
# edge in +Y so the posts don't crash into the plate at 0° tilt.  Each
# post mates with its matching knuckle on the mounting plate via a
# single M5 pin running along +X.
POST_Y: float = HINGE_Y + HINGE_EYE_OD              # 12 mm in front of plate edge
POST_W: float = HINGE_EYE_OD                        # square cross-section

# Corner mounting tabs for bolting the baseplate to a bench / breadboard.
BASE_BOLT_INSET: float = 8.0
BASE_BOLT_DIA: float = 5.4                          # M5 clearance


# --------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------- #
def _z_through_hole(plate: cq.Workplane, x: float, y: float, dia: float,
                    *, z_top: float = 1.0, depth: float = PLATE_T + 2.0) -> cq.Workplane:
    """Cut a through-hole in ``plate`` along -Z at (x, y), starting above z_top."""
    hole = (
        cq.Workplane("XY")
        .workplane(offset=z_top)
        .center(x, y)
        .circle(dia / 2)
        .extrude(-depth)
    )
    return plate.cut(hole)


# --------------------------------------------------------------------- #
# Mounting plate
# --------------------------------------------------------------------- #
def build_mounting_plate() -> cq.Workplane:
    """The rotating top board: bracket / tap-collar / motor mounts + hinges."""
    plate = (
        cq.Workplane("XY")
        .box(PLATE_W, PLATE_L, PLATE_T, centered=(True, True, False))
        .translate((0, 0, -PLATE_T))
    )

    # --- Bracket mount holes (PR #55: 2 × M3 at X = ±24, Y = ±95) -------
    brk_hole_x = BRK_FLANGE_W / 2 - BRK_MOUNT_HOLE_INSET_X      # 24 mm
    for cy in (Y_BRK_FRONT, Y_BRK_REAR):
        for sx in (+brk_hole_x, -brk_hole_x):
            plate = _z_through_hole(plate, sx, cy, M3_CLEAR)

    # --- Tap-collar mount holes (PR #51: 2 × M3 at X = ±24, Y = -40) ----
    tap_hole_x = TAP_PLATE_W / 2 - TAP_MOUNT_HOLE_INSET_X       # 24 mm
    for sx in (+tap_hole_x, -tap_hole_x):
        plate = _z_through_hole(plate, sx, Y_TAP, M3_CLEAR)

    # --- Gear-band clearance window through the plate -------------------
    # The auger gear band (Ø50) and the pinion (Ø18 at X=+32) hang BELOW
    # the bracket bores; at the plate's TOP face those tip circles dip
    # below the bracket flange so the plate underneath them needs a
    # clearance slot.
    gb_x_min = -(GEAR_BAND_TIP_DIA / 2) - 2.0
    gb_x_max = (X_MOTOR + PINION_TIP_DIA / 2) + 2.0
    gb_slot_w = gb_x_max - gb_x_min
    gb_slot_x = (gb_x_min + gb_x_max) / 2
    gb_slot_l = GEAR_BAND_FACE_W + 8.0
    gb_slot = (
        cq.Workplane("XY")
        .workplane(offset=1)
        .center(gb_slot_x, Y_GEAR_BAND)
        .rect(gb_slot_w, gb_slot_l)
        .extrude(-(PLATE_T + 2))
    )
    plate = plate.cut(gb_slot)

    # --- Motor-mount boss on plate TOP face -----------------------------
    # Block centred on (X_MOTOR, MOTOR_FACE_Y + BOSS_T/2), rising from
    # plate top (z = 0) up to enclose the motor body's lower edge.
    boss = (
        cq.Workplane("XY")
        .box(BOSS_W, BOSS_T, BOSS_H, centered=(True, True, False))
        .translate((X_MOTOR, MOTOR_FACE_Y + BOSS_T / 2, 0))
    )
    plate = plate.union(boss)

    # Motor face holes — 4 × M3 at 23 mm corner pitch + Ø22 pilot, drilled
    # along +Y through the boss into the motor face.
    for sx in (+NEMA11_FACE_HOLE_PITCH / 2, -NEMA11_FACE_HOLE_PITCH / 2):
        for sz in (+NEMA11_FACE_HOLE_PITCH / 2, -NEMA11_FACE_HOLE_PITCH / 2):
            hole = (
                cq.Workplane("XZ")
                .workplane(offset=-(MOTOR_FACE_Y - 1))      # start +Y of boss
                .center(X_MOTOR + sx, Z_MOTOR + sz)
                .circle(M3_CLEAR / 2)
                .extrude(-(BOSS_T + 2))
            )
            plate = plate.cut(hole)
    pilot = (
        cq.Workplane("XZ")
        .workplane(offset=-(MOTOR_FACE_Y - 1))
        .center(X_MOTOR, Z_MOTOR)
        .circle(NEMA11_PILOT_DIA / 2)
        .extrude(-(BOSS_T + 2))
    )
    plate = plate.cut(pilot)

    # --- Rear-edge hinge knuckles (×2) ----------------------------------
    # Each knuckle is a right-triangle gusset that drops from the plate
    # underside down to the hinge axis, with a circular eye on the far
    # end.  The gusset's flat face is in the YZ plane.
    for side in (+1, -1):
        cx = side * HINGE_X_OFFSET
        # Triangular gusset: vertices in (Y, Z) at:
        #   A = (HINGE_Y,                 -PLATE_T)       — top-rear corner
        #   B = (HINGE_Y + HINGE_DROP,    -PLATE_T)       — top-forward corner
        #   C = (HINGE_Y,                 HINGE_Z)        — bottom-rear corner
        # plus the eye at (HINGE_Y, HINGE_Z) extending forward into the
        # gusset volume.
        gusset = (
            cq.Workplane("YZ")
            .workplane(offset=cx - HINGE_KNUCKLE_GUSSET_THK / 2)
            .moveTo(HINGE_Y, -PLATE_T)
            .lineTo(HINGE_Y + HINGE_DROP, -PLATE_T)
            .lineTo(HINGE_Y, HINGE_Z)
            .close()
            .extrude(HINGE_KNUCKLE_GUSSET_THK)
        )
        plate = plate.union(gusset)
        # Circular eye boss around the hinge axis.
        eye = (
            cq.Workplane("YZ")
            .workplane(offset=cx - HINGE_EYE_WIDTH / 2)
            .center(HINGE_Y, HINGE_Z)
            .circle(HINGE_EYE_OD / 2)
            .extrude(HINGE_EYE_WIDTH)
        )
        plate = plate.union(eye)
        # Hinge pin bore through the eye.
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=cx - HINGE_EYE_WIDTH)
            .center(HINGE_Y, HINGE_Z)
            .circle(HINGE_EYE_ID / 2)
            .extrude(HINGE_EYE_WIDTH * 2 + 2)
        )
        plate = plate.cut(bore)

    return plate


# --------------------------------------------------------------------- #
# Baseplate
# --------------------------------------------------------------------- #
def build_baseplate() -> cq.Workplane:
    """Bench-side board: hinge posts + powder window + corner bolt tabs."""
    # Build in a local frame centred on (0, BASE_Y_CENTRE) with bottom at
    # z=0, then translate so the top face lands at Z_BASE_TOP.  All
    # Y-coordinates passed into builders below are in WORLD coords, so
    # we offset by -BASE_Y_CENTRE before placing local features.
    base = (
        cq.Workplane("XY")
        .box(BASE_W, BASE_L, BASE_T, centered=(True, True, False))
        .translate((0, BASE_Y_CENTRE, 0))
    )

    # Corner M5 bolt holes for fastening to a bench / breadboard.
    bx = BASE_W / 2 - BASE_BOLT_INSET
    for sx in (+bx, -bx):
        for sy in (BASE_Y_CENTRE + (BASE_L / 2 - BASE_BOLT_INSET),
                   BASE_Y_CENTRE - (BASE_L / 2 - BASE_BOLT_INSET)):
            base = _z_through_hole(base, sx, sy, BASE_BOLT_DIA,
                                   z_top=BASE_T + 1, depth=BASE_T + 2)

    # Powder-fall window directly under the dispense landing at 90° tilt.
    win = (
        cq.Workplane("XY")
        .workplane(offset=-1)
        .center(0, WINDOW_Y)
        .rect(WINDOW_W, WINDOW_L)
        .extrude(BASE_T + 2)
    )
    base = base.cut(win)

    # Hinge posts (×2): vertical square columns rising from the baseplate
    # top, tipped with a circular eye that mates with the mounting-plate
    # knuckle.  Local frame: baseplate top is at z = BASE_T.
    eye_centre_local_z = BASE_T + POST_H
    for side in (+1, -1):
        cx = side * HINGE_X_OFFSET
        # The post sits BESIDE its mating knuckle with a small clearance
        # gap so the two hinge halves interlock without rubbing.  Knuckle
        # eye occupies X = [cx - 4, cx + 4] (8 mm wide); post is 12 mm
        # wide, placed with 1 mm clearance on the outer side of cx.
        post_x_offset = side * (HINGE_EYE_WIDTH / 2 + 1.0 + POST_W / 2)
        post_cx = cx + post_x_offset
        post = (
            cq.Workplane("XY")
            .box(POST_W, POST_W, POST_H, centered=(True, True, False))
            .translate((post_cx, POST_Y, BASE_T))
        )
        base = base.union(post)
        # Eye at top of post.
        eye = (
            cq.Workplane("YZ")
            .workplane(offset=post_cx - HINGE_EYE_WIDTH / 2)
            .center(POST_Y, eye_centre_local_z)
            .circle(HINGE_EYE_OD / 2)
            .extrude(HINGE_EYE_WIDTH)
        )
        base = base.union(eye)
        # Hinge pin bore through the post eye.
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=post_cx - HINGE_EYE_WIDTH)
            .center(POST_Y, eye_centre_local_z)
            .circle(HINGE_EYE_ID / 2)
            .extrude(HINGE_EYE_WIDTH * 2 + 2)
        )
        base = base.cut(bore)

    # Translate so the baseplate's TOP face sits at Z_BASE_TOP.
    return base.translate((0, 0, Z_BASE_TOP - BASE_T))


# --------------------------------------------------------------------- #
# Hinge pin
# --------------------------------------------------------------------- #
def build_hinge_pin() -> cq.Workplane:
    """One M5 hinge pin; spans (knuckle eye) + (post eye)."""
    length = HINGE_EYE_WIDTH * 2 + 4.0
    return (
        cq.Workplane("YZ")
        .circle(M5_PIN_DIA / 2)
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
    print(f"{'part':16s}  {'X range':>22s}  {'Y range':>22s}  {'Z range':>22s}")
    for name, part in parts.items():
        step_path = step_dir / f"{name}.step"
        stl_path = stl_dir / f"{name}.stl"
        cq.exporters.export(part, str(step_path))
        cq.exporters.export(part, str(stl_path), tolerance=0.05, angularTolerance=0.2)
        bb = part.val().BoundingBox()
        print(f"  {name:14s}  "
              f"[{bb.xmin:7.2f},{bb.xmax:7.2f}]  "
              f"[{bb.ymin:7.2f},{bb.ymax:7.2f}]  "
              f"[{bb.zmin:7.2f},{bb.zmax:7.2f}]")

    print()
    print("Key reference dimensions")
    print("------------------------")
    print(f"  Plate footprint (X × Y × Z)   : {PLATE_W} × {PLATE_L} × {PLATE_T} mm")
    print(f"  Baseplate footprint           : {BASE_W} × {BASE_L} × {BASE_T} mm")
    print(f"  Auger centreline Z (Z_AUG)    : {Z_AUG:+.2f} mm  (above plate top)")
    print(f"  Hinge axis (Y, Z)             : ({HINGE_Y:+.1f}, {HINGE_Z:+.2f}) mm")
    print(f"  Hinge knuckles X (±)          : ±{HINGE_X_OFFSET:.1f} mm")
    print(f"  Bracket Y                      : ±{Y_BRK_FRONT:.1f} mm")
    print(f"  Tap-collar Y                   : {Y_TAP:+.1f} mm")
    print(f"  Motor centre (X, Y, Z)         : "
          f"({X_MOTOR:+.1f}, {MOTOR_FACE_Y - NEMA11_BODY_L / 2:+.2f}, {Z_MOTOR:+.2f}) mm")
    print(f"  Dispense @ 0°  (Y, Z)          : ({Y_DISP:+.1f}, {Z_AUG:+.2f}) mm")
    print(f"  Dispense @ 90° (Y, Z)          : ({DISPENSE_Y_AT_90:+.2f}, "
          f"{DISPENSE_Z_AT_90:+.2f}) mm  (powder window centred here)")


if __name__ == "__main__":
    main()

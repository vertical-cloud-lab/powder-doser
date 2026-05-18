"""Mounting plate + baseplate + hinge pin for the powder-doser.

Layout is built directly from the hand-drawn spec attached to issue
`#62 Mounting Plate Design` (the parent issue #56 references it through
the #46 part-by-part design tree).  In particular:

  * Every component (brackets, tap-collar mount, motor mount block, NEMA
    motor body and pinion, hinge brackets) lives on the **TOP** surface
    of the plate.  Nothing hangs below.
  * The plate is **asymmetric in X**: the auger runs along one edge,
    the motor extends out to the opposite long edge, and the side
    opposite the motor is intentionally trimmed close to the auger so
    there is no "unnecessary space".
  * Order along the auger from the hinge end (+Y) going away towards the
    motor end (-Y) is exactly: **front bracket → tap-collar mount →
    motor (= over the gear band at Y_GEAR_BAND) → rear bracket**.
  * The hinge axis is the global X axis through the auger's dispensing
    point (Y_DISP, Z_AUG) so the dispensing point literally does not
    move when the plate tilts 0..90°.
  * The two yoke brackets that carry the hinge pin are right-triangular
    wedges sitting on the plate **top** at the +Y edge, with bore axis
    along X.  The baseplate carries a matching central tang that rises
    UP from its top surface to interleave between the two yoke
    brackets, with the bore on the same X-axis.

Only the **new** parts are generated here (mounting_plate, baseplate,
hinge_pin).  The auger, brackets, tap-collar and motor STLs are imported
verbatim from the upstream PRs in ``imported-parts/``:

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
  Auger centreline at (x = 0, z = Z_AUG = +BRK_RING_CENTRE_LOCAL_Z),
  i.e. one bracket "ring-centre-over-flange-bottom" height above the
  plate top, since both brackets bolt **flange-DOWN** onto the plate
  top surface.

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
# Bracket's native frame: flange bottom on z=0, ring centre at z = ~19.74.
BRK_RING_CENTRE_LOCAL_Z = BRK_FLANGE_T + BRK_RING_OR * 0.55  # 19.74 mm

# PR #51 — tap-collar mount plate (60 × 12 × 14, 2 × M3 at X = ±24).
TAP_PLATE_W = 60.0                    # X
TAP_PLATE_D = 12.0                    # Y
TAP_PLATE_T = 14.0                    # Z
TAP_MOUNT_HOLE_INSET_X = 6.0
TAP_MOUNT_HOLE_D = 3.4

# --------------------------------------------------------------------- #
# Mounting-plate parameters
# --------------------------------------------------------------------- #
PLATE_T = 6.0                         # Z thickness

# Auger centreline = ring centre of brackets bolted flange-DOWN on top.
Z_AUG = +BRK_RING_CENTRE_LOCAL_Z      # +19.74 mm above plate top

# Auger spans Y = [Y_REAR, Y_DISP].  Dispense end at +Y.
Y_DISP = +AUGER_LEN / 2.0             # +125 mm — front edge of auger (= hinge)
Y_REAR = -AUGER_LEN / 2.0             # -125 mm — motor end of auger
Y_GEAR_BAND = Y_DISP - GEAR_BAND_AXIAL_FROM_DISP   # +41.67 mm

# --- Component Y positions (hinge end → away) -------------------------
# Order per the issue #62 drawing:
#   hinge axis @ Y_DISP=+125
#   front bracket
#   tap-collar mount
#   motor (constrained by gear-band Y)
#   rear bracket
Y_BRK_FRONT = +95.0                   # just behind dispense, ≥7 mm clear
                                      # of yoke wedge base (Y=+88)
Y_TAP       = +70.0                   # between front bracket and gear band
Y_BRK_REAR  = -95.0                   # near auger's motor end
# Y of the NEMA pinion shaft is locked by the gear mesh at Y_GEAR_BAND.

# --- Plate X envelope (asymmetric: clear side -X, component side +X) --
# Auger at X=0; bracket flange extends ±30 (60 mm wide); motor body
# centreline at X=+GEAR_CENTRE_DISTANCE=+32 with body ±NEMA11_BODY_W/2.
# Trim the -X side to just past the bracket flange edge; extend +X to
# enclose the motor body + a margin so a future motor cowling can bolt
# down without overhanging.
PLATE_X_MIN = -(BRK_FLANGE_W / 2.0) - 4.0          # -34 mm
PLATE_X_MAX = +GEAR_CENTRE_DISTANCE + NEMA11_BODY_W / 2.0 + 8.0  # +54.1 mm
PLATE_W = PLATE_X_MAX - PLATE_X_MIN                 # ~88 mm
PLATE_X_CENTRE = (PLATE_X_MIN + PLATE_X_MAX) / 2.0  # ~+10 mm

# --- Plate Y envelope --------------------------------------------------
# Encloses rear bracket (-95) and stops just past the front bracket
# (+95+12.5 = +107).  Yoke wedges extend forward on top of the plate to
# Y_DISP=+125 where the hinge eyes sit.
PLATE_Y_FRONT = +110.0
PLATE_Y_BACK  = Y_BRK_REAR - BRK_FLANGE_D / 2.0 - 7.0   # -114.5 mm
PLATE_L = PLATE_Y_FRONT - PLATE_Y_BACK                  # ~224.5 mm
PLATE_Y_CENTRE = (PLATE_Y_FRONT + PLATE_Y_BACK) / 2.0   # ~-2.25 mm

# --- Hinge yoke wedges (on TOP of plate, +Y edge) ---------------------
# Right-triangular wedges in the Y-Z plane: vertical face at the +Y plate
# edge, horizontal face on the plate top, hypotenuse rising from
# Y=YOKE_WEDGE_Y_BACK at z=0 to Y=PLATE_Y_FRONT at z=YOKE_WEDGE_TOP_Z.
# The hinge bore is at (Y_DISP, Z_AUG) so it overhangs the plate edge by
# (Y_DISP - PLATE_Y_FRONT) = 15 mm — supported by a short cylindrical
# eye that extends forward of the wedge.
YOKE_WEDGE_THK     = 8.0              # wedge thickness in X (each)
YOKE_WEDGE_GAP     = 26.0             # central X clearance between wedges
YOKE_WEDGE_TOP_Z   = Z_AUG + 8.0      # wedge rises a bit above auger axis
YOKE_WEDGE_Y_BACK  = PLATE_Y_FRONT - 22.0   # wedge base extends 22 mm back
YOKE_EYE_OD        = 14.0
YOKE_EYE_ID        = 5.4              # M5 hinge-pin clearance
YOKE_EYE_AXIAL_LEN = YOKE_WEDGE_THK   # eye is just an extension of the wedge

# Each yoke wedge centred in X at:
YOKE_X_INNER = YOKE_WEDGE_GAP / 2 + YOKE_WEDGE_THK / 2   # ±17

# --- NEMA-11 motor mount block (on TOP of plate) ----------------------
# Per the drawing, the motor sits on top of the plate with its axis
# parallel to the plate (= parallel to the auger).  Pinion sticks out
# the front face of the motor in the +Y direction so it meshes with the
# auger's gear band at Y = Y_GEAR_BAND.
# The integrated "Motor Mounting Block" is a vertical wall on the plate
# top.  Its +Y face carries the NEMA 11 face holes; the motor body
# extends in -Y away from that face.
BOSS_W   = NEMA11_BODY_W + 8.0        # X width of boss (36.2 mm)
BOSS_H   = NEMA11_BODY_W + 8.0        # Z height of boss (36.2 mm)
BOSS_T   = 6.0                        # Y wall thickness
# +Y face of the boss = motor-face plane (2 mm air gap to gear band).
MOTOR_FACE_Y = Y_GEAR_BAND - GEAR_BAND_FACE_W / 2.0 - 2.0   # +34.67 mm
X_MOTOR  = +GEAR_CENTRE_DISTANCE      # +32 mm — pinion meshes auger
Z_MOTOR  = Z_AUG                      # parallel-axis with auger

# --- Linear-actuator rod-end pivot lug (on plate UNDERSIDE) -----------
# The actuator pulls down on the rear of the plate from below.  Lug
# hangs from the underside of the plate at the rear.
ACT_LUG_Y = -60.0
ACT_LUG_T = 8.0                       # along Y
ACT_LUG_W = 12.0                      # along X
ACT_LUG_H = 24.0                      # how far it drops below the plate
ACT_LUG_BORE_D = 5.4

# --- Baseplate --------------------------------------------------------
BASE_W = 200.0
BASE_L = 320.0
BASE_T = 6.0
BASE_LEG_H = 95.0                     # clears 50 mm cup + 30 mm scale
BASE_LEG_W = 18.0
BASE_LEG_INSET = 12.0

# Baseplate top just below mounting-plate bottom with a small clearance.
# With everything ABOVE the mounting plate, tilting forward 0..90° lifts
# the plate's rear corner UP, not down — so no deep gap is required.
Z_BASE_TOP = -PLATE_T - 6.0            # -12 mm  (6 mm air gap)

# Powder window directly under the dispense point.
WINDOW_W = 60.0
WINDOW_L = 60.0
WINDOW_Y = Y_DISP

# Central hinge tang on baseplate top.  Single tab sitting between the
# two mounting-plate yoke wedges, bored for the hinge pin.
TANG_W = YOKE_WEDGE_GAP - 0.4         # 0.2 mm clearance per side
TANG_T = YOKE_EYE_OD + 6.0            # Y depth
TANG_Y = Y_DISP
TANG_BORE_Z_ABS = Z_AUG               # bore on the auger centreline
TANG_TOP_Z_ABS = Z_AUG + 8.0          # rises to match yoke top

# Linear-actuator base clevis on baseplate top.
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
def _through_hole(x: float, y: float, dia: float) -> cq.Workplane:
    """A through-hole boolean tool spanning z=[-PLATE_T-1, +1]."""
    return (
        cq.Workplane("XY")
        .workplane(offset=1.0)
        .center(x, y)
        .circle(dia / 2.0)
        .extrude(-(PLATE_T + 2.0))
    )


def build_mounting_plate() -> cq.Workplane:
    """Top plate: brackets + tap-collar + NEMA 11 + yoke ALL on top."""
    # Asymmetric plate centred on (PLATE_X_CENTRE, PLATE_Y_CENTRE).
    plate = (
        cq.Workplane("XY")
        .box(PLATE_W, PLATE_L, PLATE_T, centered=(True, True, False))
        .translate((PLATE_X_CENTRE, PLATE_Y_CENTRE, -PLATE_T))
    )

    # ------ Bracket mount holes (2 × M3 at X = ±24) ----------------------
    brk_x = BRK_FLANGE_W / 2.0 - BRK_MOUNT_HOLE_INSET_X            # 24
    for cy in (Y_BRK_FRONT, Y_BRK_REAR):
        for sx in (+brk_x, -brk_x):
            plate = plate.cut(_through_hole(sx, cy, M3_CLEAR))

    # ------ Tap-collar mount holes (2 × M3 at X = ±24, Y = Y_TAP) --------
    tap_x = TAP_PLATE_W / 2.0 - TAP_MOUNT_HOLE_INSET_X             # 24
    for sx in (+tap_x, -tap_x):
        plate = plate.cut(_through_hole(sx, Y_TAP, M3_CLEAR))

    # ------ NEMA 11 motor mount block (sits ON TOP of plate) -------------
    # Block bottom mates with plate top (z=0); block extends up to
    # boss_top_z; +Y face is at MOTOR_FACE_Y and carries 4 × M3 +
    # central Ø22 pilot for the NEMA 11.
    boss_bot_z = 0.0
    boss_top_z = Z_MOTOR + BOSS_H / 2.0
    boss_h = boss_top_z - boss_bot_z
    boss_centre_z = (boss_top_z + boss_bot_z) / 2.0
    boss = (
        cq.Workplane("XY")
        .box(BOSS_W, BOSS_T, boss_h, centered=(True, True, True))
        .translate((X_MOTOR, MOTOR_FACE_Y - BOSS_T / 2.0, boss_centre_z))
    )
    plate = plate.union(boss)
    # M3 holes through the boss for the NEMA 11 face screws.
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
    # Central Ø22 pilot for the shaft + pinion.
    pilot = (
        cq.Workplane("XZ")
        .workplane(offset=-(MOTOR_FACE_Y + 1))
        .center(X_MOTOR, Z_MOTOR)
        .circle(NEMA11_PILOT_DIA / 2.0)
        .extrude(BOSS_T + 2.0)
    )
    plate = plate.cut(pilot)

    # ------ Hinge yoke wedges (two triangular wedges on plate TOP) -------
    for side in (+1, -1):
        cx = side * YOKE_X_INNER
        # Triangular wedge in the Y-Z plane: vertices
        #   A = (YOKE_WEDGE_Y_BACK, 0)            # back-bottom
        #   B = (PLATE_Y_FRONT,     0)            # front-bottom (plate edge)
        #   C = (PLATE_Y_FRONT,     YOKE_WEDGE_TOP_Z)   # front-top
        wedge = (
            cq.Workplane("YZ")
            .workplane(offset=cx - YOKE_WEDGE_THK / 2.0)
            .moveTo(YOKE_WEDGE_Y_BACK, 0)
            .lineTo(PLATE_Y_FRONT, 0)
            .lineTo(PLATE_Y_FRONT, YOKE_WEDGE_TOP_Z)
            .close()
            .extrude(YOKE_WEDGE_THK)
        )
        plate = plate.union(wedge)
        # Eye extension: a thick disc sticking forward of the wedge,
        # centred on (Y_DISP, Z_AUG), so the bore overhangs the plate edge
        # by exactly (Y_DISP - PLATE_Y_FRONT) = 15 mm.
        eye = (
            cq.Workplane("YZ")
            .workplane(offset=cx - YOKE_WEDGE_THK / 2.0)
            .center(Y_DISP, Z_AUG)
            .circle(YOKE_EYE_OD / 2.0)
            .extrude(YOKE_EYE_AXIAL_LEN)
        )
        plate = plate.union(eye)
        # Hinge pin bore through the eye + wedge along X.
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=cx - YOKE_WEDGE_THK)
            .center(Y_DISP, Z_AUG)
            .circle(YOKE_EYE_ID / 2.0)
            .extrude(YOKE_WEDGE_THK * 2 + 2)
        )
        plate = plate.cut(bore)

    # ------ Gear-band / pinion clearance pocket on plate TOP -------------
    # Component side: cut a shallow pocket on the plate top so the gear
    # band (Ø50 tip, dips to z=Z_AUG-25=−5.3 → below the plate top by
    # 5.3 mm) and the pinion (Ø18 tip, at X=+32) have free clearance
    # against the plate top.  Pocket spans through-plate so chips also
    # fall away.
    gb_x_min = -(GEAR_BAND_TIP_DIA / 2.0) - 2.0      # -27
    gb_x_max = +X_MOTOR + PINION_TIP_DIA / 2.0 + 2.0  # +43
    gb_w = gb_x_max - gb_x_min
    gb_cx = (gb_x_min + gb_x_max) / 2.0
    gb_l = GEAR_BAND_FACE_W + 8.0
    gb_slot = (
        cq.Workplane("XY")
        .workplane(offset=1.0)
        .center(gb_cx, Y_GEAR_BAND)
        .rect(gb_w, gb_l)
        .extrude(-(PLATE_T + 2.0))
    )
    plate = plate.cut(gb_slot)

    # ------ Powder-fall slot through plate at the dispense end -----------
    # The auger's dispense hole sits just behind the hinge axis (Y just
    # short of +125).  A slot through the plate lets powder fall when
    # the assembly is tilted vertical.
    slot_w = YOKE_WEDGE_GAP                          # 26
    slot_l = 30.0
    slot_y_centre = PLATE_Y_FRONT - slot_l / 2.0 + 2.0
    slot = (
        cq.Workplane("XY")
        .workplane(offset=1.0)
        .center(0, slot_y_centre)
        .rect(slot_w, slot_l)
        .extrude(-(PLATE_T + 2.0))
    )
    plate = plate.cut(slot)

    # ------ Linear-actuator rod-end pivot lug on plate UNDERSIDE ---------
    lug = (
        cq.Workplane("XY")
        .box(ACT_LUG_W, ACT_LUG_T, ACT_LUG_H, centered=(True, True, False))
        .translate((0, ACT_LUG_Y, -PLATE_T - ACT_LUG_H))
    )
    plate = plate.union(lug)
    lug_bore = (
        cq.Workplane("YZ")
        .workplane(offset=-(ACT_LUG_W / 2.0 + 1.0))
        .center(ACT_LUG_Y, -PLATE_T - ACT_LUG_H + 6.0)
        .circle(ACT_LUG_BORE_D / 2.0)
        .extrude(ACT_LUG_W + 2.0)
    )
    plate = plate.cut(lug_bore)

    return plate


def build_baseplate() -> cq.Workplane:
    """Bench-side plate: legs, central hinge tang on TOP, powder window."""
    base = (
        cq.Workplane("XY")
        .box(BASE_W, BASE_L, BASE_T, centered=(True, True, False))
    )

    # Corner legs (drop below to give cup + scale clearance).
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

    # Powder window directly under the dispense point.
    win = (
        cq.Workplane("XY")
        .workplane(offset=-1.0)
        .center(0, WINDOW_Y)
        .rect(WINDOW_W, WINDOW_L)
        .extrude(BASE_T + 2.0)
    )
    base = base.cut(win)

    # Central hinge tang on baseplate top.  Local frame: baseplate
    # bottom on z=0, top on z=BASE_T.  We want, AFTER the final
    # translate (0, 0, Z_BASE_TOP), the tang's bore to land on
    # z=TANG_BORE_Z_ABS=Z_AUG=+19.74 and the tang's top on
    # z=TANG_TOP_Z_ABS=Z_AUG+8.  In local frame this is:
    #   tang_top_local = TANG_TOP_Z_ABS - Z_BASE_TOP
    #   tang_bore_local = TANG_BORE_Z_ABS - Z_BASE_TOP
    tang_top_local = TANG_TOP_Z_ABS - Z_BASE_TOP
    tang_bore_local = TANG_BORE_Z_ABS - Z_BASE_TOP
    tang_h = tang_top_local - BASE_T
    tang = (
        cq.Workplane("XY")
        .box(TANG_W, TANG_T, tang_h, centered=(True, True, False))
        .translate((0, TANG_Y, BASE_T))
    )
    base = base.union(tang)
    tang_bore = (
        cq.Workplane("YZ")
        .workplane(offset=-(TANG_W / 2 + 1.0))
        .center(TANG_Y, tang_bore_local)
        .circle(YOKE_EYE_ID / 2.0)
        .extrude(TANG_W + 2.0)
    )
    base = base.cut(tang_bore)

    # Linear-actuator base clevis on baseplate top.
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

    # Translate the whole baseplate so its top face sits at Z_BASE_TOP.
    return base.translate((0, 0, Z_BASE_TOP))


def build_hinge_pin() -> cq.Workplane:
    """M5-pattern hinge pin: spans both yoke eyes + central tang + slop."""
    length = TANG_W + 2 * YOKE_WEDGE_THK + 2 * YOKE_EYE_AXIAL_LEN + 4
    return (
        cq.Workplane("YZ")
        .circle(5.0 / 2.0)
        .extrude(length)
        .translate((-length / 2.0, 0, 0))
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
    print(f"Plate X envelope             : [{PLATE_X_MIN:+.2f}, {PLATE_X_MAX:+.2f}] mm  "
          f"(asymmetric; clear side -X, motor side +X)")
    print(f"Plate Y envelope             : [{PLATE_Y_BACK:+.2f}, {PLATE_Y_FRONT:+.2f}] mm")
    print(f"Auger centreline Z (Z_AUG)   : {Z_AUG:+.2f} mm  (above plate top)")
    print(f"Gear band Y (Y_GEAR_BAND)    : {Y_GEAR_BAND:+.2f} mm")
    print(f"Motor centre (X,Y,Z)         : ({X_MOTOR:+.2f}, "
          f"{MOTOR_FACE_Y - NEMA11_BODY_L / 2:+.2f}, {Z_MOTOR:+.2f}) mm")
    print(f"Hinge axis                   : X-axis through (Y={Y_DISP:+.2f}, Z={Z_AUG:+.2f})")
    print(f"Component order (Y, hinge→far): brkF={Y_BRK_FRONT:+.0f}  "
          f"tap={Y_TAP:+.0f}  motor={Y_GEAR_BAND:+.2f}  brkR={Y_BRK_REAR:+.0f}")


if __name__ == "__main__":
    main()

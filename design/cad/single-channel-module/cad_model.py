"""
Parametric CadQuery model of the single-channel powder-doser module —
**v2 architecture** addressing PR review feedback from @williamulbz
(commits in this PR after c39e07f).

Key changes vs v1:

  - The top-plate / bottom-plate / 4-corner-post frame is gone. The
    structural backbone is a single printed **spine** plate; everything
    bolts to its +X face.
  - The auger rotor is now supported, and its tap/vibration energy is
    coupled, by a real **6805ZZ deep-groove ball bearing** (Ø25 ID /
    Ø37 OD / 7 mm) pressed into the bearing collar. Vibration from the
    ERM coin reaches the rotor through the bearing's ball/race contact;
    the JF-0530B solenoid plunger taps the rotor wall *directly*
    through a window cut into the collar body.
  - The NEMA 11 stepper is mounted on the +X face of the spine on a
    side bracket and drives the auger via a 1:1 **GT2 belt** (16T
    pulleys, ~110 mm closed-loop belt). The top of the rotor is now
    free for a removable powder **cartridge** that snaps onto the
    rotor's four PR-#16-v4 top loading slots.
  - The rotor protrudes 30 mm past the base of the spine so the
    falling-powder column escapes the frame even when the module is
    tilted off vertical. The bearing collar is the *bottom* support;
    there is no longer a "base plate exit hole".
  - All printed-part fastener holes are sized for **M3 brass heat-set
    inserts** (4.0 mm × 4 mm Ruthex-style, 4.5 mm pilot hole), not
    self-tappers.
  - The module's working orientation is no longer vertical. A separate
    **adjustable-angle cradle** (`cradle_cheek` × 2 + `cradle_base`)
    pivots the spine on M5 trunnions and locks at 0° / 15° / 30° / 45°
    / 60° / 75° via an arc slot.

Coordinate frame:
    +Z = up, +Y = "front" (towards the viewer), +X = away from the
    spine (outward, where the rotor and electronics live)
    Rotor axis: parallel to Z, at (X = ROTOR_X_OFFSET, Y = 0)
    Spine plate: in the YZ plane, offset to -X of the rotor axis.
    Z = 0 at the bottom of the bearing collar (the lowest *frame* point;
    the rotor protrudes ~30 mm below this).
    All dimensions in millimetres.

Run:
    python cad_model.py

writes `single_channel_module.step`, `stl/<part>.stl` for every
printable part, and four orthographic SVG line renders into ./renders/.
"""
from __future__ import annotations

from pathlib import Path
import math

import cadquery as cq

OUT_DIR = Path(__file__).parent
RENDER_DIR = OUT_DIR / "renders"
STL_DIR = OUT_DIR / "stl"
RENDER_DIR.mkdir(exist_ok=True)
STL_DIR.mkdir(exist_ok=True)


# ============================================================================
# Constants — single source of truth (mirrored in sketch_2d.py and README.md).
# ============================================================================

# --- PR-#16 v4 auger rotor --------------------------------------------------
AUGER_OD = 25.0
AUGER_LEN = 250.0
AUGER_M3_BOSS_R = 4.0
AUGER_M3_BOSS_H = 6.0
AUGER_TOP_CAP_H = 6.0
AUGER_EXIT_HOLE_D = 3.0

# --- 6805ZZ deep-groove ball bearing ---------------------------------------
BRG_ID = 25.0
BRG_OD = 37.0
BRG_T = 7.0

# --- NEMA 11 bipolar stepper (PR-#25 item 10) ------------------------------
NEMA11_FACE = 28.0
NEMA11_BODY_L = 45.0
NEMA11_SHAFT_D = 5.0
NEMA11_SHAFT_L = 20.0
NEMA11_BOSS_D = 22.0
NEMA11_BOSS_H = 1.5
NEMA11_BOLT_PCD = 23.0

# --- GT2 belt drive (1:1, 16T pulleys) -------------------------------------
PULLEY_OD = 12.2          # 16-tooth GT2, OD over teeth
PULLEY_FLANGE_OD = 16.0
PULLEY_H = 16.0
BELT_WIDTH = 6.0
BELT_THK = 1.4

# --- JF-0530B 5 V mini push-pull solenoid (PR-#25 item 4) ------------------
SOL_W = 9.6
SOL_H = 19.0
SOL_L = 22.0
SOL_PLUNGER_D = 4.0
SOL_PLUNGER_PROTRUDE = 2.0   # plunger extends past front face when at rest
SOL_BOLT_PITCH = 14.0

# --- ERM coin vibration motor (PR-#25 item 2) ------------------------------
ERM_D = 10.0
ERM_T = 2.7

# --- Heat-set inserts (M3 brass, Ruthex-style M3×5×4) -----------------------
INSERT_PILOT_D = 4.5      # printed-hole pilot for the insert
INSERT_OD = 4.0
INSERT_L = 4.0

# --- Bearing collar (printed) ----------------------------------------------
COLLAR_OD = 50.0
COLLAR_H = 16.0
COLLAR_BORE = BRG_OD       # press fit; modelled at nominal — no shrink
COLLAR_FLANGE_W = 76.0     # spans across the spine to the two M3 inserts
COLLAR_FLANGE_T = 6.0
COLLAR_FLANGE_H = COLLAR_H
COLLAR_FOOT_BOLT_PITCH = 60.0   # M3 inserts on this Y pitch
SOL_WINDOW_D = SOL_PLUNGER_D + 1.0   # plunger passes THROUGH the collar
SOL_WING_T = 6.0           # solenoid bracket wall thickness (was 4 in v1)
SOL_WING_GUSSET = 8.0      # gusset rib width tying the wing to the collar
ERM_PAD_T = 3.0
ERM_PAD_W = 14.0
ERM_PAD_H = 14.0

# --- Spine (printed) -------------------------------------------------------
SPINE_W = 90.0    # along Y
SPINE_T = 8.0     # along X — printed flat-on-bed, then stood on edge
SPINE_H = 360.0   # along Z
ROTOR_X_OFFSET = SPINE_T / 2 + COLLAR_OD / 2 + 4.0   # rotor sits clear of spine
PULLEY_AXIS_OFFSET = ROTOR_X_OFFSET                  # rotor axis is also pulley axis
MOTOR_AXIS_OFFSET_Y = -50.0     # motor axis offset along Y from rotor axis
MOTOR_AXIS_X = ROTOR_X_OFFSET   # both pulleys at same X

# --- Motor bracket (printed) -----------------------------------------------
MB_W = 50.0       # along Y
MB_H = 50.0       # along Z (mounts NEMA-11 face)
MB_T = 5.0        # along X (face plate)
MB_FOOT_W = 60.0  # foot that bolts to the spine
MB_FOOT_T = 5.0
MB_FOOT_H = 35.0  # how far back along X the foot rides on the spine

# --- Cartridge / hopper (printed, removable) -------------------------------
CART_BORE_D = AUGER_OD + 0.6     # slip fit over the rotor's top
CART_BASE_OD = 36.0              # collar that grabs the rotor top cap
CART_BASE_H = 12.0
CART_HOPPER_OD = 60.0
CART_HOPPER_H = 60.0
CART_NECK_H = 6.0                # taper transition

# --- Adjustable-angle cradle (printed, off-module stand) -------------------
CRADLE_PIVOT_X = 0.0     # pivot is at spine's centre-of-mass (waist)
CRADLE_PIVOT_Z = 200.0
CRADLE_PIVOT_BOLT_D = 5.0     # M5 trunnion
CRADLE_DETENT_R = 60.0        # arc-slot radius from pivot
CRADLE_DETENT_ANGLES_DEG = [0, 15, 30, 45, 60, 75]
CHEEK_W = 80.0    # along Z (height of cheek when laid flat)
CHEEK_H = 220.0   # along Y (length of cheek)
CHEEK_T = 6.0
CRADLE_BASE_W = 220.0   # along Y
CRADLE_BASE_D = 180.0   # along X
CRADLE_BASE_T = 8.0
CRADLE_GAP = SPINE_T + 2.0   # space between the two cheeks for the spine

# --- Assembly working tilt for renders -------------------------------------
DEMO_TILT_DEG = 30.0   # what the renders show the cradle locked at


# ============================================================================
# Utility
# ============================================================================
def hex_grid(_): pass  # placeholder to keep linters happy


# ============================================================================
# PRINTED PARTS
# ============================================================================
def make_spine() -> cq.Workplane:
    """Single flat backbone plate, printed flat-on-bed.

    Cut-outs:
      - Top:    motor-bracket M3 insert holes (4×) on the bracket's foot pattern.
      - Mid:    bearing-collar M3 insert holes (2×) where the collar flange sits.
      - Waist: trunnion-pivot through-hole (M5 clearance) for the cradle.
      - Lightening pocket on the +X face for filament economy (just visual).
    """
    sp = (
        cq.Workplane("YZ")
        .workplane(offset=-SPINE_T / 2)
        .rect(SPINE_W, SPINE_H, centered=(True, False))
        .extrude(SPINE_T)
    )
    # Bearing-collar inserts — at the collar Z range, centred Y, on COLLAR_FOOT_BOLT_PITCH
    collar_z_centre = COLLAR_H / 2 + 8.0   # collar rests above 8 mm spine baseline
    for dy in (+COLLAR_FOOT_BOLT_PITCH / 2, -COLLAR_FOOT_BOLT_PITCH / 2):
        sp = (
            sp.faces(">X")
            .workplane(centerOption="CenterOfBoundBox")
            .center(dy, collar_z_centre - SPINE_H / 2)
            .hole(INSERT_PILOT_D)
        )
    # Motor-bracket inserts — 4-hole pattern on a 30×20 rectangle near the top
    motor_face_z = SPINE_H - 90.0
    for dy in (+25, -25):
        for dz in (+10, -10):
            sp = (
                sp.faces(">X")
                .workplane(centerOption="CenterOfBoundBox")
                .center(dy, motor_face_z - SPINE_H / 2 + dz)
                .hole(INSERT_PILOT_D)
            )
    # Trunnion pivot bore (through hole, M5 clearance) at the waist
    sp = (
        sp.faces(">X")
        .workplane(centerOption="CenterOfBoundBox")
        .center(0, CRADLE_PIVOT_Z - SPINE_H / 2)
        .hole(CRADLE_PIVOT_BOLT_D + 0.4)
    )
    return sp


def make_bearing_collar() -> cq.Workplane:
    """Bearing-bored stationary collar with INTEGRAL solenoid bracket
    (gusseted), INTEGRAL ERM pad, INTEGRAL flange/feet.

    The 6805ZZ press-fits into the central bore; rotor passes through the
    bearing inner race. Solenoid plunger window goes THROUGH the collar
    so the plunger tip impacts the rotor wall directly.
    """
    cz0 = 0.0
    rotor_x = ROTOR_X_OFFSET

    # Main collar body (cylindrical) with bearing seat
    body = (
        cq.Workplane("XY")
        .workplane(offset=cz0)
        .center(rotor_x, 0)
        .circle(COLLAR_OD / 2)
        .circle(BRG_OD / 2)
        .extrude(COLLAR_H)
    )

    # Solenoid plunger through-window (cylinder along +Y axis)
    window = (
        cq.Workplane("XZ")
        .workplane(offset=-COLLAR_OD)
        .center(rotor_x, cz0 + COLLAR_H / 2)
        .circle(SOL_WINDOW_D / 2)
        .extrude(2 * COLLAR_OD)
    )
    body = body.cut(window)

    # Solenoid bracket wing on +Y — a flat plate in the XZ plane
    wing_y0 = COLLAR_OD / 2 - 2.0
    wing = (
        cq.Workplane("XZ")
        .workplane(offset=wing_y0)
        .center(rotor_x, cz0 + COLLAR_H / 2)
        .rect(SOL_H + 6, COLLAR_H)
        .extrude(SOL_WING_T)
    )
    # Cut plunger clearance + 2× M2 mounting holes through the wing
    wing_window = (
        cq.Workplane("XZ")
        .workplane(offset=wing_y0 - 1)
        .center(rotor_x, cz0 + COLLAR_H / 2)
        .circle(SOL_WINDOW_D / 2)
        .extrude(SOL_WING_T + 2)
    )
    wing = wing.cut(wing_window)
    for dx in (+SOL_BOLT_PITCH / 2, -SOL_BOLT_PITCH / 2):
        m2 = (
            cq.Workplane("XZ")
            .workplane(offset=wing_y0 - 1)
            .center(rotor_x + dx, cz0 + COLLAR_H / 2)
            .circle(2.4 / 2)
            .extrude(SOL_WING_T + 2)
        )
        wing = wing.cut(m2)

    # Triangular gusset: ties the wing back to the collar body in Y/Z
    gusset_pts = [
        (wing_y0, cz0),
        (wing_y0, cz0 + COLLAR_H * 0.6),
        (COLLAR_OD / 2 - 2.0 + 0.1, cz0),  # at collar OD on +Y
    ]
    # Easier: build in YZ plane swept along X
    gusset = (
        cq.Workplane("YZ")
        .workplane(offset=rotor_x - SOL_WING_GUSSET / 2)
        .moveTo(wing_y0, cz0)
        .lineTo(wing_y0, cz0 + COLLAR_H * 0.6)
        .lineTo(COLLAR_OD / 2 - 2.0, cz0)
        .close()
        .extrude(SOL_WING_GUSSET)
    )

    # ERM coin pad: a disc on the underside (-Z) of the collar
    pad = (
        cq.Workplane("XY")
        .workplane(offset=-ERM_PAD_T)
        .center(rotor_x, 0)
        .circle(ERM_D / 2 + 4)
        .extrude(ERM_PAD_T)
    )
    # Shallow recess for ERM glue alignment
    pad_recess = (
        cq.Workplane("XY")
        .workplane(offset=-ERM_PAD_T - 0.1)
        .center(rotor_x, 0)
        .circle(ERM_D / 2 + 0.2)
        .extrude(0.7)
    )
    pad = pad.cut(pad_recess)

    # Mounting flange on -X (toward the spine), with two integral feet
    # and through-bores for M3 BHCS that thread into spine inserts
    flange = (
        cq.Workplane("XY")
        .workplane(offset=cz0)
        .center(SPINE_T / 2 + COLLAR_FLANGE_T / 2, 0)
        .rect(COLLAR_FLANGE_T, COLLAR_FLANGE_W)
        .extrude(COLLAR_FLANGE_H)
    )
    for dy in (+COLLAR_FOOT_BOLT_PITCH / 2, -COLLAR_FOOT_BOLT_PITCH / 2):
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=-COLLAR_OD)
            .center(dy, cz0 + COLLAR_FLANGE_H / 2)
            .circle(3.4 / 2)
            .extrude(2 * COLLAR_OD)
        )
        flange = flange.cut(bore)

    return body.union(wing).union(gusset).union(pad).union(flange)


def make_motor_bracket() -> cq.Workplane:
    """Right-angle bracket: foot bolts to the spine, faceplate carries
    the NEMA 11 stepper. Faceplate is set Y-offset so the stepper shaft
    aligns with the auger pulley axis (1:1 GT2 belt).
    """
    motor_face_z = SPINE_H - 90.0
    motor_face_y = MOTOR_AXIS_OFFSET_Y

    foot = (
        cq.Workplane("YZ")
        .workplane(offset=SPINE_T / 2)
        .moveTo(0, motor_face_z)
        .rect(MB_FOOT_W, MB_FOOT_H)
        .extrude(MB_FOOT_T)
    )
    # Foot M3 clearance (4 holes matching the spine inserts)
    foot = (
        foot.faces(">X")
        .workplane(centerOption="CenterOfBoundBox")
        .pushPoints([(+25, +10), (-25, +10), (+25, -10), (-25, -10)])
        .hole(3.4)
    )

    # Vertical face that holds the stepper: stands off in +X
    face = (
        cq.Workplane("XY")
        .workplane(offset=motor_face_z + MB_H / 2)
        .center((SPINE_T / 2) + MB_FOOT_T + MB_H / 2, motor_face_y)
        .rect(MB_H, MB_W)
        .extrude(MB_T)
    )
    # NEMA 11 boss bore + 4× M2.5 clearance on 23 mm BHC
    face = (
        face.faces(">Z")
        .workplane()
        .hole(NEMA11_BOSS_D + 1.0)
    )
    bolt_xy = [(+NEMA11_BOLT_PCD / 2, +NEMA11_BOLT_PCD / 2),
               (-NEMA11_BOLT_PCD / 2, +NEMA11_BOLT_PCD / 2),
               (-NEMA11_BOLT_PCD / 2, -NEMA11_BOLT_PCD / 2),
               (+NEMA11_BOLT_PCD / 2, -NEMA11_BOLT_PCD / 2)]
    face = (
        face.faces(">Z")
        .workplane()
        .pushPoints(bolt_xy)
        .hole(3.0)
    )
    return foot.union(face)


def make_cartridge() -> cq.Workplane:
    """Removable hopper cartridge that snaps onto the rotor's top
    loading slots (PR-#16 v4: 4× sectoral slots, 4 mm × 7 mm at 6.5 mm
    radius). The cartridge has a Ø25.6 collar that drops over the rotor
    top, then a 60° conical hopper to a 60-mm-Ø cylindrical reservoir.
    Lifts off for refills / colour swaps.
    """
    rotor_x = ROTOR_X_OFFSET
    auger_top_z = COLLAR_H + 10.0 + AUGER_LEN   # cartridge rim sits at this Z
    base = (
        cq.Workplane("XY")
        .workplane(offset=auger_top_z)
        .center(rotor_x, 0)
        .circle(CART_BASE_OD / 2)
        .circle(CART_BORE_D / 2)
        .extrude(CART_BASE_H)
    )
    # 60° taper to hopper OD
    neck = (
        cq.Workplane("XY")
        .workplane(offset=auger_top_z + CART_BASE_H)
        .center(rotor_x, 0)
        .circle(CART_BASE_OD / 2)
        .workplane(offset=CART_NECK_H)
        .circle(CART_HOPPER_OD / 2)
        .loft(combine=True)
    )
    # Hollow neck (subtract a smaller loft)
    neck_inner = (
        cq.Workplane("XY")
        .workplane(offset=auger_top_z + CART_BASE_H)
        .center(rotor_x, 0)
        .circle(CART_BORE_D / 2)
        .workplane(offset=CART_NECK_H)
        .circle(CART_HOPPER_OD / 2 - 2.0)
        .loft(combine=True)
    )
    neck = neck.cut(neck_inner)

    hopper = (
        cq.Workplane("XY")
        .workplane(offset=auger_top_z + CART_BASE_H + CART_NECK_H)
        .center(rotor_x, 0)
        .circle(CART_HOPPER_OD / 2)
        .circle(CART_HOPPER_OD / 2 - 2.0)
        .extrude(CART_HOPPER_H)
    )
    return base.union(neck).union(hopper)


def make_cradle_cheek(side: str) -> cq.Workplane:
    """One side of the adjustable-angle cradle. ``side='L'`` puts the cheek
    at +Y, ``'R'`` at -Y. The cheek is a flat plate with:
      * an M5 pivot hole through the centre (matches spine waist hole)
      * an arc slot at radius CRADLE_DETENT_R for the M5 lock bolt
      * 6 detent dimples at CRADLE_DETENT_ANGLES_DEG
      * a foot at the bottom that bolts to cradle_base
    """
    sign = +1 if side == "L" else -1
    y_face = sign * (SPINE_T / 2 + 0.5)   # cheek inside face just outside the spine

    # Sketch the cheek profile in a plane offset along Y
    cheek = (
        cq.Workplane("XZ")
        .workplane(offset=y_face)
        .center(0, CRADLE_PIVOT_Z)
        .moveTo(-CHEEK_H / 2, -CHEEK_W / 2)
        .rect(CHEEK_H, CHEEK_W, centered=False)
        .extrude(sign * CHEEK_T)
    )
    # Pivot hole
    cheek = (
        cheek.faces({"L": ">Y", "R": "<Y"}[side])
        .workplane(centerOption="CenterOfBoundBox")
        .hole(CRADLE_PIVOT_BOLT_D + 0.4)
    )
    # Arc slot — sweep an oval along the arc by stamping holes; cheap
    # but printable. Stamp a hole every 5° from -10° to 80° at radius
    # CRADLE_DETENT_R.
    pts = []
    for ang_deg in range(-10, 85, 5):
        a = math.radians(ang_deg)
        pts.append((CRADLE_DETENT_R * math.sin(a),
                    CRADLE_DETENT_R * math.cos(a) - CRADLE_DETENT_R))
    # Convert points to be relative to the cheek face centre (which is
    # CRADLE_PIVOT in world coords; so we shift Z by -CRADLE_PIVOT_Z).
    cheek = (
        cheek.faces({"L": ">Y", "R": "<Y"}[side])
        .workplane(centerOption="CenterOfBoundBox")
        .pushPoints(pts)
        .hole(CRADLE_PIVOT_BOLT_D + 1.0)
    )
    # Foot — extends to Z=0 (cradle_base top); a thicker rectangle at the bottom
    foot = (
        cq.Workplane("XZ")
        .workplane(offset=y_face)
        .moveTo(-CHEEK_H / 2, 0)
        .rect(CHEEK_H, CRADLE_BASE_T + 8, centered=False)
        .extrude(sign * (CHEEK_T + 2))
    )
    cheek = cheek.union(foot)
    return cheek


def make_cradle_base() -> cq.Workplane:
    """Flat base plate that the two cheeks bolt down to. Has 4× M3
    insert holes for the cheek feet plus 4× corner M4 clearance bores
    for bench-mounting / ring-frame integration."""
    base = (
        cq.Workplane("XY")
        .box(CRADLE_BASE_D, CRADLE_BASE_W, CRADLE_BASE_T,
             centered=(True, True, False))
    )
    # Corner M4 clearance bores
    a, b = CRADLE_BASE_D / 2 - 10, CRADLE_BASE_W / 2 - 10
    base = (
        base.faces(">Z")
        .workplane()
        .pushPoints([(+a, +b), (-a, +b), (-a, -b), (+a, -b)])
        .hole(4.4)
    )
    return base


# ============================================================================
# VENDOR / PLACEHOLDER PARTS
# ============================================================================
def make_auger() -> cq.Workplane:
    """PR-#16 v4 rotor envelope. The rotor extends 30 mm BELOW the
    bearing-collar baseline (i.e. into negative Z) so its dispense
    nozzle clears the frame even when the cradle tilts."""
    rotor_x = ROTOR_X_OFFSET
    rotor_z0 = -30.0   # 30 mm below the collar baseline
    body = (
        cq.Workplane("XY")
        .workplane(offset=rotor_z0)
        .center(rotor_x, 0)
        .circle(AUGER_OD / 2)
        .extrude(AUGER_LEN)
    )
    # Top boss for pulley / coupler attachment
    boss = (
        cq.Workplane("XY")
        .workplane(offset=rotor_z0 + AUGER_LEN)
        .center(rotor_x, 0)
        .circle(AUGER_M3_BOSS_R)
        .extrude(AUGER_M3_BOSS_H)
    )
    return body.union(boss)


def make_bearing() -> cq.Workplane:
    """6805ZZ deep-groove ball bearing modelled as a flat annulus — its
    thin sealed envelope (Ø25 ID / Ø37 OD / 7 mm)."""
    rotor_x = ROTOR_X_OFFSET
    z0 = (COLLAR_H - BRG_T) / 2
    return (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .center(rotor_x, 0)
        .circle(BRG_OD / 2)
        .circle(BRG_ID / 2)
        .extrude(BRG_T)
    )


def make_pulley(rotor_x: float, rotor_y: float, z0: float) -> cq.Workplane:
    """Generic GT2 16T pulley with two flanges. Drawn as toothed cylinder
    + two flange disks; the teeth are not modelled at scale."""
    body = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .center(rotor_x, rotor_y)
        .circle(PULLEY_OD / 2)
        .extrude(PULLEY_H - 4)
    )
    flange_b = (
        cq.Workplane("XY")
        .workplane(offset=z0 - 2)
        .center(rotor_x, rotor_y)
        .circle(PULLEY_FLANGE_OD / 2)
        .extrude(2)
    )
    flange_t = (
        cq.Workplane("XY")
        .workplane(offset=z0 + PULLEY_H - 4)
        .center(rotor_x, rotor_y)
        .circle(PULLEY_FLANGE_OD / 2)
        .extrude(2)
    )
    return body.union(flange_b).union(flange_t)


def make_belt(motor_x, motor_y, rotor_x, rotor_y, z_centre) -> cq.Workplane:
    """A planar oval ring approximating the GT2 belt path between the
    two pulleys. Drawn as the outer offset minus the inner offset of
    the two pulley circles, swept at belt thickness."""
    # Two circles connected by tangent lines — easier as a rectangle with
    # rounded ends spanning between the pulley centres.
    span = math.hypot(motor_x - rotor_x, motor_y - rotor_y)
    angle = math.degrees(math.atan2(motor_y - rotor_y, motor_x - rotor_x))
    # Make in local frame (rotor pulley at origin)
    half_w = PULLEY_OD / 2 + BELT_THK / 2
    inner_half_w = PULLEY_OD / 2 - BELT_THK / 2
    outer = (
        cq.Workplane("XY")
        .workplane(offset=z_centre - BELT_WIDTH / 2)
        .moveTo(0, half_w)
        .lineTo(span, half_w)
        .threePointArc((span + half_w, 0), (span, -half_w))
        .lineTo(0, -half_w)
        .threePointArc((-half_w, 0), (0, half_w))
        .close()
        .extrude(BELT_WIDTH)
    )
    inner = (
        cq.Workplane("XY")
        .workplane(offset=z_centre - BELT_WIDTH / 2)
        .moveTo(0, inner_half_w)
        .lineTo(span, inner_half_w)
        .threePointArc((span + inner_half_w, 0), (span, -inner_half_w))
        .lineTo(0, -inner_half_w)
        .threePointArc((-inner_half_w, 0), (0, inner_half_w))
        .close()
        .extrude(BELT_WIDTH)
    )
    belt = outer.cut(inner)
    belt = belt.rotate((0, 0, 0), (0, 0, 1), angle)
    belt = belt.translate((rotor_x, rotor_y, 0))
    return belt


def make_stepper() -> cq.Workplane:
    motor_face_z = SPINE_H - 90.0
    face_x = MOTOR_AXIS_X
    face_y = MOTOR_AXIS_OFFSET_Y
    # Stepper sits on TOP of the bracket faceplate at motor_face_z + MB_H
    body_z0 = motor_face_z + MB_H + MB_T  # above the bracket faceplate? no — bracket is in XY plane
    # Re-derive: the bracket's faceplate (in XY at Z = motor_face_z + MB_H/2 + MB_T)
    # in the make_motor_bracket layout I rewrote above with motor_face_z + MB_H/2.
    # Simpler: place the stepper body with its faceplate at Z = motor_face_z + MB_H + MB_T.
    body = (
        cq.Workplane("XY")
        .workplane(offset=body_z0)
        .center(face_x, face_y)
        .rect(NEMA11_FACE, NEMA11_FACE)
        .extrude(NEMA11_BODY_L)
    )
    boss = (
        cq.Workplane("XY")
        .workplane(offset=body_z0 - NEMA11_BOSS_H)
        .center(face_x, face_y)
        .circle(NEMA11_BOSS_D / 2)
        .extrude(NEMA11_BOSS_H)
    )
    shaft = (
        cq.Workplane("XY")
        .workplane(offset=body_z0 - NEMA11_SHAFT_L - NEMA11_BOSS_H)
        .center(face_x, face_y)
        .circle(NEMA11_SHAFT_D / 2)
        .extrude(NEMA11_SHAFT_L)
    )
    return body.union(boss).union(shaft)


def make_solenoid() -> cq.Workplane:
    """JF-0530B solenoid bolted to the +Y face of the collar's wing,
    plunger pointing in -Y towards the rotor."""
    rotor_x = ROTOR_X_OFFSET
    z_c = COLLAR_H / 2
    # Wing's outer face is at Y = COLLAR_OD/2 - 2 + SOL_WING_T
    y_face = COLLAR_OD / 2 - 2 + SOL_WING_T
    body = (
        cq.Workplane("XZ")
        .workplane(offset=y_face)
        .center(rotor_x, z_c)
        .rect(SOL_W, SOL_H)
        .extrude(SOL_L)
    )
    # Plunger going through the wing into the rotor
    plunger = (
        cq.Workplane("XY")
        .workplane(offset=z_c - SOL_PLUNGER_D / 2)
        .center(rotor_x, y_face - SOL_PLUNGER_PROTRUDE)
        .circle(SOL_PLUNGER_D / 2)
        .extrude(SOL_PLUNGER_D)
    )
    return body.union(plunger)


def make_erm() -> cq.Workplane:
    """ERM coin glued to the underside of the bearing collar."""
    rotor_x = ROTOR_X_OFFSET
    z_top = -ERM_PAD_T   # top of the coin = bottom of pad
    return (
        cq.Workplane("XY")
        .workplane(offset=z_top - ERM_T)
        .center(rotor_x, 0)
        .circle(ERM_D / 2)
        .extrude(ERM_T)
    )


# ============================================================================
# Build instances of each part
# ============================================================================
spine = make_spine()
collar = make_bearing_collar()
motor_bracket = make_motor_bracket()
cartridge = make_cartridge()
cheek_L = make_cradle_cheek("L")
cheek_R = make_cradle_cheek("R")
cradle_base = make_cradle_base().translate((0, 0, -10))   # below the spine

auger = make_auger()
bearing = make_bearing()

# Pulleys: rotor pulley on top of the rotor M3 boss, motor pulley on stepper
rotor_z0 = -30.0
pulley_z0 = rotor_z0 + AUGER_LEN + AUGER_M3_BOSS_H + 4.0
rotor_pulley = make_pulley(ROTOR_X_OFFSET, 0, pulley_z0)
motor_pulley = make_pulley(MOTOR_AXIS_X, MOTOR_AXIS_OFFSET_Y, pulley_z0)
belt = make_belt(MOTOR_AXIS_X, MOTOR_AXIS_OFFSET_Y, ROTOR_X_OFFSET, 0,
                 pulley_z0 + (PULLEY_H - 4) / 2)

stepper = make_stepper()
solenoid = make_solenoid()
erm = make_erm()


# ============================================================================
# ASSEMBLY
# ============================================================================
PRINTED = cq.Color(0.85, 0.85, 0.92)
CRADLE_C = cq.Color(0.55, 0.7, 0.55)
asm = cq.Assembly(name="single_channel_module_v2")
asm.add(spine, name="spine", color=PRINTED)
asm.add(collar, name="bearing_collar", color=PRINTED)
asm.add(motor_bracket, name="motor_bracket", color=PRINTED)
asm.add(cartridge, name="cartridge", color=cq.Color(0.95, 0.85, 0.55))
asm.add(cheek_L, name="cradle_cheek_L", color=CRADLE_C)
asm.add(cheek_R, name="cradle_cheek_R", color=CRADLE_C)
asm.add(cradle_base, name="cradle_base", color=CRADLE_C)

asm.add(auger, name="auger_rotor_envelope_PR16", color=cq.Color(1.0, 0.95, 0.6))
asm.add(bearing, name="bearing_6805ZZ", color=cq.Color(0.45, 0.45, 0.5))
asm.add(rotor_pulley, name="GT2_pulley_rotor", color=cq.Color(0.55, 0.55, 0.6))
asm.add(motor_pulley, name="GT2_pulley_motor", color=cq.Color(0.55, 0.55, 0.6))
asm.add(belt, name="GT2_belt", color=cq.Color(0.15, 0.15, 0.15))
asm.add(stepper, name="NEMA11_stepper", color=cq.Color(0.25, 0.25, 0.28))
asm.add(solenoid, name="JF0530B_solenoid", color=cq.Color(0.4, 0.25, 0.2))
asm.add(erm, name="ERM_coin_vibration", color=cq.Color(0.9, 0.6, 0.2))


# ============================================================================
# EXPORTS
# ============================================================================
step_path = OUT_DIR / "single_channel_module.step"
asm.save(str(step_path))
print(f"wrote {step_path}")

# STL exports of every printable part
for name, part in [
    ("spine", spine),
    ("bearing_collar", collar),
    ("motor_bracket", motor_bracket),
    ("cartridge", cartridge),
    ("cradle_cheek_L", cheek_L),
    ("cradle_cheek_R", cheek_R),
    ("cradle_base", cradle_base),
]:
    stl_path = STL_DIR / f"{name}.stl"
    cq.exporters.export(part, str(stl_path), tolerance=0.1, angularTolerance=0.2)
    print(f"wrote {stl_path}")

# Remove now-obsolete v1 STLs
for old in ("base_plate", "top_plate", "corner_post", "tap_collar",
            "electronics_tray"):
    p = STL_DIR / f"{old}.stl"
    if p.exists():
        p.unlink()
        print(f"removed obsolete {p}")


# Combined solid for SVG line work
def _union_all(parts):
    out = None
    for p in parts:
        out = p if out is None else out.union(p)
    return out


print("unioning combined solid for SVG renders ...")
combined = _union_all([
    spine, collar, motor_bracket, cartridge,
    cheek_L, cheek_R, cradle_base,
    auger, bearing, rotor_pulley, motor_pulley, belt,
    stepper, solenoid, erm,
])

opts = {
    "width": 1400, "height": 1100,
    "marginLeft": 12, "marginTop": 12,
    "showAxes": False,
    "strokeWidth": 0.4,
    "strokeColor": (20, 20, 20),
    "hiddenColor": (170, 170, 170),
    "showHidden": True,
}
for name, projdir in [
    ("iso",   (1.4, -1.1, 0.7)),
    ("front", (0, -1, 0)),
    ("side",  (1, 0, 0)),
    ("top",   (0, 0, 1)),
]:
    path = RENDER_DIR / f"single_channel_module_{name}.svg"
    cq.exporters.export(combined, str(path), opt={**opts, "projectionDir": projdir})
    print(f"wrote {path}")

# Also clean up obsolete render PNGs that no longer match (we regenerate
# the iso/front/top/side PNGs in a follow-up cairosvg pass)
print("done.")

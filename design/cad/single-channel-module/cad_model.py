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

import math
from pathlib import Path

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

# --- GT2 belt drive ---------------------------------------------------------
# v4: rotor pulley sized UP from 16T (Ø12.2) to 36T (Ø~26.5) per @swcharles's
# belt-clipping note: a 16T GT2 pulley (Ø12.2) is SMALLER than the rotor
# body (Ø25), so the belt could not physically wrap a 16T pulley clamped to
# the rotor without intersecting the rotor wall. A 36T (Ø26.5) rotor pulley
# clears the rotor by ~0.75 mm and gives a 36:16 ≈ 2.25× reduction (a feature,
# not a bug — slows the auger rotation, raising metering precision).
MOTOR_PULLEY_OD = 12.2     # 16T GT2 motor pulley (small, on NEMA 11 shaft)
ROTOR_PULLEY_OD = 26.5     # 36T GT2 rotor pulley (large, clamps onto rotor)
PULLEY_FLANGE_DELTA = 4.0  # flange OD = pulley OD + this
PULLEY_H = 16.0
BELT_WIDTH = 9.0           # v4: 6 -> 9 mm wide (S-belt section was marginal at this size)
BELT_THK = 1.4
# Backwards-compat alias for sketch_2d.py
PULLEY_OD = MOTOR_PULLEY_OD
PULLEY_FLANGE_OD = MOTOR_PULLEY_OD + PULLEY_FLANGE_DELTA

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
# v3: ERM is OFF-AXIS (S2). It glues to a flat pad on the -Y outside of the
# collar wall instead of being directly under the rotor (the v2 placement
# blocks the dispense column AND adds inertia at the rotor centreline).
ERM_PAD_Y_OFFSET = -(COLLAR_OD / 2 + ERM_PAD_T / 2 - 0.4)

# --- Spine (printed) -------------------------------------------------------
# v3: 8 -> 10 mm thickness for stiffness (was wear-prone per @swcharles S7).
SPINE_W = 90.0    # along Y
SPINE_T = 10.0    # along X — printed flat-on-bed, then stood on edge
SPINE_H = 360.0   # along Z
ROTOR_X_OFFSET = SPINE_T / 2 + COLLAR_OD / 2 + 4.0   # rotor sits clear of spine
PULLEY_AXIS_OFFSET = ROTOR_X_OFFSET                  # rotor axis is also pulley axis
# v3: motor moved to a vertical Y-stack so the foot and face actually touch
# (S1/S4) and the belt path is BELOW the cartridge (S2). The motor pulley
# sits just above the bearing collar, the rotor pulley likewise — the cartridge
# above is unobstructed.
MOTOR_AXIS_OFFSET_Y = -45.0     # motor axis offset along Y from rotor axis
MOTOR_AXIS_X = ROTOR_X_OFFSET   # both pulleys at same X
# v3 round-2 fix (Edison r2 #3): belt plane raised to clear the bearing collar
# flange (Z=0..16) AND keep the bracket foot above the spine bottom. The
# motor bracket foot extends DOWN from MOTOR_FACE_TOP_Z to COLLAR_H+4, which
# requires MOTOR_FACE_TOP_Z to be high enough that the foot fits.
BELT_PLANE_Z = COLLAR_H + 34.0   # = 50 mm; clears flange + leaves foot room
MOTOR_FACE_TOP_Z = BELT_PLANE_Z + PULLEY_H + 4.0   # underside of bracket faceplate

# --- Motor bracket (printed) -----------------------------------------------
# v3: rebuilt as a true L: foot lies flat on the spine +X face (extruded
# +X by MB_FOOT_T), face stands UP from the foot's far edge (extruded +Z by MB_H).
# The foot Y-extent reaches MOTOR_AXIS_OFFSET_Y so the face is mechanically
# joined to the foot — no Y-gap as in v2 (S1/S4).
MB_FACE_W = 42.0      # along Y (face plate width — must enclose NEMA-11 28mm face + bolts)
MB_FACE_H = 36.0      # along Z (face plate height — must enclose NEMA-11 face + bolts)
MB_FACE_T = 5.0       # along X (faceplate thickness)
MB_FOOT_T = 5.0       # foot thickness in Z (lays flat against spine +X face)
MB_FOOT_X = 45.0      # how far foot extends in +X from spine face — Edison r2 #2: was 32, too small for NEMA-11 23 mm BHC at MOTOR_AXIS_X=29
MB_FOOT_Y_LO = MOTOR_AXIS_OFFSET_Y - MB_FACE_W / 2 - 4.0
# Edison r2 #2: faceplate must NOT cross the rotor (rotor occupies Y=±12.5).
# Truncate the foot's Y_HI to leave 1 mm clearance from the rotor wall.
MB_FOOT_Y_HI = -(AUGER_OD / 2 + 1.0)   # ≈ -13.5
MB_FOOT_W = MB_FOOT_Y_HI - MB_FOOT_Y_LO   # ≈ 53 mm — Y-span of the foot

# --- Cartridge / hopper (printed, removable) -------------------------------
CART_BORE_D = AUGER_OD + 0.6     # slip fit over the rotor's top
CART_BASE_OD = 36.0              # collar that grabs the rotor top cap
CART_BASE_H = 12.0
CART_HOPPER_OD = 60.0
CART_HOPPER_H = 60.0
CART_NECK_H = 6.0                # taper transition

# --- Adjustable-angle cradle (printed, off-module stand) -------------------
# v3: tilt is now actuated by a NEMA 17 stepper at the +Y trunnion through a
# 30:1 worm gearbox (ungeared NEMA-17 holding torque is enough for the
# ~0.6 N·m static moment of the loaded module about the pivot at any tilt
# in 0–90°). The -Y trunnion is still a passive M5 bolt.
CRADLE_PIVOT_X = 0.0     # pivot is at spine's centre-of-mass (waist)
# v4 (@swcharles): pivot moved DOWN from 220 → 70 so the rotor exit nozzle
# (at z=-30) sits only ~100 mm below the pivot instead of 250 mm. This cuts
# the dispense-nozzle swing arc by 60% across the 0–90° tilt range, so the
# cup below it doesn't have to be re-positioned every time the angle changes
# AND the powder drop height stays small/consistent.
CRADLE_PIVOT_Z = 70.0    # was 220 — pivot near auger mouth, not near top of frame
CRADLE_PIVOT_BOLT_D = 5.0     # M5 trunnion (passive side)
CRADLE_DETENT_R = 60.0        # arc-slot radius from pivot
CRADLE_DETENT_ANGLES_DEG = [0, 15, 30, 45, 60, 75, 90]
CHEEK_W = 100.0   # along Z (height of cheek body proper, around the pivot)
CHEEK_H = 130.0   # along X (length of cheek; was 220 — Edison r1 #5)
CHEEK_T = 8.0     # v3: 6 -> 8 mm (S7 stiffness)
# v3: trim the cradle base from 220x180 to 140x110 (S3 outboard plates).
CRADLE_BASE_W = 140.0   # along Y
CRADLE_BASE_D = 110.0   # along X
CRADLE_BASE_T = 8.0
CRADLE_GAP = SPINE_T + 2.0   # space between the two cheeks for the spine

# --- Tilt-drive NEMA 17 + worm gearbox (vendor envelopes) ------------------
NEMA17_FACE = 42.3
NEMA17_BODY_L = 40.0
NEMA17_SHAFT_D = 5.0
NEMA17_SHAFT_L = 24.0
NEMA17_BOSS_D = 22.0
NEMA17_BOSS_H = 2.0
NEMA17_BOLT_PCD = 31.0
WORM_GEARBOX_W = 56.0       # 30:1 NEMA-17 worm gearbox envelope (Y span)
WORM_GEARBOX_H = 60.0       # along Z
WORM_GEARBOX_X = 40.0       # how far it sticks out in X from the cheek face

# --- Assembly working tilt for renders -------------------------------------
DEMO_TILT_DEG = 30.0   # what the renders show the cradle locked at

# --- A&D scale envelope (context body, not printed) ------------------------
# v4 (@swcharles): module must rest on a real surface with the cup
# directly under the dispense nozzle. A&D EJ-303B-class footprint.
SCALE_BASE_D = 213.0
SCALE_BASE_W = 213.0
SCALE_BASE_H = 80.0
SCALE_PAN_OD = 130.0
SCALE_PAN_T = 4.0
SCALE_PAN_PILLAR_H = 12.0

# --- Generic collection cup (context body, not printed) --------------------
CUP_OD = 60.0
CUP_H = 100.0
CUP_WALL = 1.5


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
    # Motor-bracket inserts — v3 r2: 4-hole pattern on the foot of the L
    # bracket. Foot must clear the bearing collar flange (Z=0..16) AND not
    # dangle below the spine bottom; positions are kept in sync with
    # `make_motor_bracket()` via a shared computation.
    foot_centre_y = (MB_FOOT_Y_LO + MB_FOOT_Y_HI) / 2
    foot_bottom_z = COLLAR_H + 4.0
    foot_top_z = MOTOR_FACE_TOP_Z
    foot_h = foot_top_z - foot_bottom_z
    foot_centre_z = (foot_bottom_z + foot_top_z) / 2
    insert_dz = max(8.0, foot_h / 2 - 6.0)
    insert_dy_step = max(12.0, MB_FOOT_W / 2 - 8.0)
    for dy_sign in (-1, +1):
        for dz_sign in (-1, +1):
            sp = (
                sp.faces(">X")
                .workplane(centerOption="CenterOfBoundBox")
                .center(foot_centre_y + dy_sign * insert_dy_step,
                        foot_centre_z + dz_sign * insert_dz - SPINE_H / 2)
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

    # v3: ERM coin pad is OFF-AXIS — a flat pad on the -Y outside of the
    # collar wall (was on-axis under the rotor in v2; @swcharles S2 flagged
    # the on-axis placement as a flow-path obstruction). The pad sits at
    # collar mid-height so its vibrations couple into the bearing inner
    # race through the collar wall in shear.
    pad = (
        cq.Workplane("XY")
        .workplane(offset=cz0 + COLLAR_H / 2 - ERM_PAD_W / 2)
        .center(rotor_x, ERM_PAD_Y_OFFSET)
        .rect(ERM_PAD_H, ERM_PAD_T)
        .extrude(ERM_PAD_W)
    )

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
    """v3 right-angle (L) bracket. The foot is a vertical plate pressed
    against the spine's +X face; the faceplate is a horizontal plate
    cantilevered from the TOP edge of the foot. Both share the foot's
    Y range so they actually meet along an edge (S1, S4 fix).

    The faceplate is at low Z — just above the bearing collar — so the
    GT2 belt runs in the BELT_PLANE_Z plane, BELOW the cartridge
    (S2 fix).

    The NEMA 11 stepper bolts on TOP of the faceplate, shaft pointing
    DOWN through a clearance hole, pulley sitting in the belt plane.
    """
    # 1) Vertical foot — a thin slab pressed against the spine. v3 r2 fix
    # (Edison #3): foot bottom must NOT clash with the bearing collar
    # flange (Z=0..16) and must NOT dangle below the spine bottom (Z=0).
    foot_centre_y = (MB_FOOT_Y_LO + MB_FOOT_Y_HI) / 2
    foot_bottom_z = COLLAR_H + 4.0          # 4 mm above collar flange top
    foot_top_z = MOTOR_FACE_TOP_Z           # meets the cantilever face
    foot_h = foot_top_z - foot_bottom_z
    foot_centre_z = (foot_bottom_z + foot_top_z) / 2
    foot = (
        cq.Workplane("YZ")
        .workplane(offset=SPINE_T / 2)
        .moveTo(foot_centre_y, foot_centre_z)
        .rect(MB_FOOT_W, foot_h)
        .extrude(MB_FOOT_T)
    )
    # Foot M3 clearance — 4 holes matching the spine's inserts.
    insert_dz = max(8.0, foot_h / 2 - 6.0)
    insert_dy_step = max(12.0, MB_FOOT_W / 2 - 8.0)
    foot = (
        foot.faces(">X")
        .workplane(centerOption="CenterOfBoundBox")
        .pushPoints([(-insert_dy_step, +insert_dz),
                     (-insert_dy_step, -insert_dz),
                     (+insert_dy_step, +insert_dz),
                     (+insert_dy_step, -insert_dz)])
        .hole(3.4)
    )

    # 2) Horizontal faceplate — cantilevered out in +X from the TOP edge
    # of the foot. They share Z=MOTOR_FACE_TOP_Z and the same Y range,
    # giving a continuous L (no Y/Z gap as in v2).
    face = (
        cq.Workplane("XY")
        .workplane(offset=MOTOR_FACE_TOP_Z)
        .moveTo(SPINE_T / 2 + MB_FOOT_X / 2, foot_centre_y)
        .rect(MB_FOOT_X, MB_FOOT_W)
        .extrude(MB_FACE_T)
    )

    # 3) Continuous gusset web — v4 fix per @swcharles. The previous v3
    # bracket had TWO separate triangular gussets (gy = ±25 from foot
    # centre, each 5 mm thick along Y). They unioned correctly to the
    # face/foot, but visually read as 3 disconnected bodies in renders
    # because the Y span between them (≈ 45 mm) is empty. We now build
    # a SINGLE solid gusset whose Y span equals the bracket's Y span
    # (MB_FOOT_W) — guaranteed one-body, with a thinner top web and
    # ribbed underside for filament economy.
    gusset_y_span = MB_FOOT_W - 4.0   # 2 mm setback each side
    gusset_x_max = 24.0               # how far it cantilevers in +X
    gusset_z_drop = 24.0              # how far it descends in -Z
    gusset = (
        cq.Workplane("XZ")
        .workplane(offset=foot_centre_y - gusset_y_span / 2)
        .moveTo(SPINE_T / 2, MOTOR_FACE_TOP_Z)
        .lineTo(SPINE_T / 2 + gusset_x_max, MOTOR_FACE_TOP_Z)
        .lineTo(SPINE_T / 2, MOTOR_FACE_TOP_Z - gusset_z_drop)
        .close()
        .extrude(gusset_y_span)
    )
    face = face.union(gusset)

    # 4) NEMA 11 shaft clearance + 4× M2.5 mount holes through the faceplate
    # at MOTOR_AXIS_OFFSET_Y.
    face = (
        face.faces(">Z")
        .workplane()
        .center(MOTOR_AXIS_X - (SPINE_T / 2 + MB_FOOT_X / 2), MOTOR_AXIS_OFFSET_Y - foot_centre_y)
        .hole(NEMA11_BOSS_D + 1.0)
    )
    bolt_xy = [
        (+NEMA11_BOLT_PCD / 2, +NEMA11_BOLT_PCD / 2),
        (-NEMA11_BOLT_PCD / 2, +NEMA11_BOLT_PCD / 2),
        (-NEMA11_BOLT_PCD / 2, -NEMA11_BOLT_PCD / 2),
        (+NEMA11_BOLT_PCD / 2, -NEMA11_BOLT_PCD / 2),
    ]
    face = (
        face.faces(">Z")
        .workplane()
        .center(MOTOR_AXIS_X - (SPINE_T / 2 + MB_FOOT_X / 2), MOTOR_AXIS_OFFSET_Y - foot_centre_y)
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
    # v3 fix (Edison round-1 item 1): the rotor's top face is at
    # rotor_z0 + AUGER_LEN; the v2 expression `COLLAR_H + 10 + AUGER_LEN`
    # left a ~56 mm air gap above the rotor (rotor top = -30+250 = 220,
    # cartridge rim was at 16+10+250 = 276). The cartridge collar must
    # SLIP-FIT over the rotor top cap — its bottom rim sits 4 mm BELOW the
    # rotor top so the collar fully engages the cap.
    rotor_top_z = -30.0 + AUGER_LEN              # = 220 mm
    auger_top_z = rotor_top_z - 4.0              # cartridge rim 4 mm below rotor top
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
    """One side of the adjustable-angle cradle. The two cheeks STRADDLE the
    spine in the X direction (spine has X-thickness `SPINE_T`, so each
    cheek bolts to one of the spine's flat ±X faces). ``side='L'`` puts
    the cheek at -X, ``'R'`` at +X. The cheek is a flat plate parallel to
    the YZ plane with:
      * an M5 pivot hole through the centre (matches spine waist hole)
      * an arc slot at radius CRADLE_DETENT_R for the M5 lock bolt
      * detent positions at CRADLE_DETENT_ANGLES_DEG
      * a foot at the bottom that bolts to cradle_base

    v3 round-2 fix (Edison r2 #1): the v2/v3-r1 cheek used `Workplane("XZ")`
    offset along Y, which embedded the cheek INSIDE the spine's Y range.
    Cheeks now use `Workplane("YZ")` offset along ±X, so they actually
    straddle the spine across its 10 mm X thickness.
    """
    sign = -1 if side == "L" else +1
    x_face = sign * (SPINE_T / 2 + 0.5)   # cheek inside face just outside the spine

    # Sketch the cheek profile in a YZ plane offset along X. On a YZ
    # workplane, U=Y and V=Z, so rect(CHEEK_H, CHEEK_W) gives CHEEK_H
    # along Y and CHEEK_W along Z. CHEEK_H=130 covers the arc-slot Y-range;
    # CHEEK_W=100 covers the pivot ± half-arc in Z.
    cheek = (
        cq.Workplane("YZ")
        .workplane(offset=x_face)
        .center(0, CRADLE_PIVOT_Z)
        .rect(CHEEK_H, CHEEK_W)
        .extrude(sign * CHEEK_T)
    )
    # Pivot hole — drilled along ±X through the cheek face.
    cheek = (
        cheek.faces({"L": "<X", "R": ">X"}[side])
        .workplane(centerOption="CenterOfBoundBox")
        .hole(CRADLE_PIVOT_BOLT_D + 0.4)
    )
    # Arc-slot detent holes — pts are (Y, Z) relative to the face centre,
    # which after rect-centred is at world (0, CRADLE_PIVOT_Z).
    pts = []
    for ang_deg in range(-10, 95, 5):
        a = math.radians(ang_deg)
        pts.append((CRADLE_DETENT_R * math.sin(a),
                    CRADLE_DETENT_R * math.cos(a) - CRADLE_DETENT_R))
    cheek = (
        cheek.faces({"L": "<X", "R": ">X"}[side])
        .workplane(centerOption="CenterOfBoundBox")
        .pushPoints(pts)
        .hole(CRADLE_PIVOT_BOLT_D + 1.0)
    )
    # Continuous spar from the cheek body DOWN to the foot, so the
    # printed cheek is one connected solid (no air gap between pivot
    # region and the foot at the cradle base).
    spar_z_top = CRADLE_PIVOT_Z - CHEEK_W / 2
    spar_z_bot = 0.0
    spar_h = spar_z_top - spar_z_bot
    if spar_h > 0:
        spar = (
            cq.Workplane("YZ")
            .workplane(offset=x_face)
            .moveTo(-30, spar_z_bot)
            .rect(60, spar_h, centered=False)
            .extrude(sign * CHEEK_T)
        )
        cheek = cheek.union(spar)
    # Foot — sits flat on the cradle base (top at Z=0).
    foot = (
        cq.Workplane("YZ")
        .workplane(offset=x_face)
        .moveTo(-CHEEK_H / 2, 0)
        .rect(CHEEK_H, 10.0, centered=False)
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


def make_pulley(rotor_x: float, rotor_y: float, z0: float,
                pulley_od: float = MOTOR_PULLEY_OD) -> cq.Workplane:
    """Generic GT2 pulley with two flanges. Drawn as toothed cylinder
    + two flange disks; the teeth are not modelled at scale.

    v4: ``pulley_od`` parameterised so the rotor pulley (36T, Ø26.5)
    can be larger than the motor pulley (16T, Ø12.2). A 16T rotor
    pulley would be SMALLER than the rotor body (Ø25), and its belt
    wrap would intersect the rotor wall (@swcharles's belt-clipping
    note); a 36T rotor pulley clears the rotor with ~0.75 mm margin.
    """
    flange_od = pulley_od + PULLEY_FLANGE_DELTA
    body = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .center(rotor_x, rotor_y)
        .circle(pulley_od / 2)
        .extrude(PULLEY_H - 4)
    )
    flange_b = (
        cq.Workplane("XY")
        .workplane(offset=z0 - 2)
        .center(rotor_x, rotor_y)
        .circle(flange_od / 2)
        .extrude(2)
    )
    flange_t = (
        cq.Workplane("XY")
        .workplane(offset=z0 + PULLEY_H - 4)
        .center(rotor_x, rotor_y)
        .circle(flange_od / 2)
        .extrude(2)
    )
    return body.union(flange_b).union(flange_t)


def make_belt(motor_x, motor_y, rotor_x, rotor_y, z_centre,
              motor_pulley_od: float = MOTOR_PULLEY_OD,
              rotor_pulley_od: float = ROTOR_PULLEY_OD) -> cq.Workplane:
    """Planar oval ring approximating the GT2 belt path between the
    two pulleys. Uses outer-tangent envelopes around two CIRCLES of
    DIFFERENT radius (v4): the motor pulley is small, the rotor
    pulley is large, so the belt envelope is a stadium with an
    asymmetric tangent quadrilateral, not a uniform oval.
    """
    # Vector from rotor (large) to motor (small)
    span = math.hypot(motor_x - rotor_x, motor_y - rotor_y)
    angle = math.degrees(math.atan2(motor_y - rotor_y, motor_x - rotor_x))
    r_big = rotor_pulley_od / 2
    r_sml = motor_pulley_od / 2
    # Build belt in local frame: rotor pulley centre at origin (0,0),
    # motor pulley centre at (span, 0). Wrap each pulley with a half-
    # disk; tangent lines link them on each side.
    outer_big = r_big + BELT_THK / 2
    inner_big = r_big - BELT_THK / 2
    outer_sml = r_sml + BELT_THK / 2
    inner_sml = r_sml - BELT_THK / 2
    outer = (
        cq.Workplane("XY")
        .workplane(offset=z_centre - BELT_WIDTH / 2)
        .moveTo(0, outer_big)
        .lineTo(span, outer_sml)
        .threePointArc((span + outer_sml, 0), (span, -outer_sml))
        .lineTo(0, -outer_big)
        .threePointArc((-outer_big, 0), (0, outer_big))
        .close()
        .extrude(BELT_WIDTH)
    )
    inner = (
        cq.Workplane("XY")
        .workplane(offset=z_centre - BELT_WIDTH / 2)
        .moveTo(0, inner_big)
        .lineTo(span, inner_sml)
        .threePointArc((span + inner_sml, 0), (span, -inner_sml))
        .lineTo(0, -inner_big)
        .threePointArc((-inner_big, 0), (0, inner_big))
        .close()
        .extrude(BELT_WIDTH)
    )
    belt = outer.cut(inner)
    belt = belt.rotate((0, 0, 0), (0, 0, 1), angle)
    belt = belt.translate((rotor_x, rotor_y, 0))
    return belt


def make_stepper() -> cq.Workplane:
    """v3: NEMA 11 sits on top of the LOW bracket faceplate, shaft pointing
    DOWN through the faceplate to the pulley in the belt plane.
    """
    face_x = MOTOR_AXIS_X
    face_y = MOTOR_AXIS_OFFSET_Y
    # Stepper body bottom is at the top of the faceplate.
    body_z0 = MOTOR_FACE_TOP_Z + MB_FACE_T
    body = (
        cq.Workplane("XY")
        .workplane(offset=body_z0)
        .center(face_x, face_y)
        .rect(NEMA11_FACE, NEMA11_FACE)
        .extrude(NEMA11_BODY_L)
    )
    # Pilot boss extends DOWN into the faceplate counter-bore.
    boss = (
        cq.Workplane("XY")
        .workplane(offset=body_z0 - NEMA11_BOSS_H)
        .center(face_x, face_y)
        .circle(NEMA11_BOSS_D / 2)
        .extrude(NEMA11_BOSS_H)
    )
    # Shaft extends DOWN through the faceplate to the belt plane (pulley).
    shaft = (
        cq.Workplane("XY")
        .workplane(offset=body_z0 - NEMA11_BOSS_H - NEMA11_SHAFT_L)
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
    # v3 fix (Edison round-1 item 4): plunger is a ROD along -Y from the
    # solenoid front face into the rotor wall, NOT a Z-extruded coin as
    # in v2. Sketched in the XZ plane, extruded along -Y from the wing's
    # outer face into the collar bore.
    plunger_len = (y_face - SOL_PLUNGER_PROTRUDE) - 0   # plunger reaches rotor centreline
    plunger = (
        cq.Workplane("XZ")
        .workplane(offset=y_face - SOL_PLUNGER_PROTRUDE)
        .center(rotor_x, z_c)
        .circle(SOL_PLUNGER_D / 2)
        .extrude(-plunger_len)
    )
    return body.union(plunger)


def make_erm() -> cq.Workplane:
    """v3: ERM coin glued to the side pad on -Y face of the bearing collar
    (off-axis, S2). The coin's flat face mates with the pad's outer face."""
    rotor_x = ROTOR_X_OFFSET
    z_centre = COLLAR_H / 2
    # Pad outer face is at Y = ERM_PAD_Y_OFFSET - ERM_PAD_T/2; coin sits
    # against that face on the -Y side.
    y_outer = ERM_PAD_Y_OFFSET - ERM_PAD_T / 2
    return (
        cq.Workplane("XZ")
        .workplane(offset=y_outer - ERM_T)
        .center(rotor_x, z_centre)
        .circle(ERM_D / 2)
        .extrude(ERM_T)
    )


def make_tilt_drive() -> cq.Workplane:
    """v3 NEW: NEMA 17 + worm-gearbox envelope at the +X trunnion of the
    cradle (v3 r2 fix: cheeks now straddle the spine in X, so the
    tilt-drive sits adjacent to the +X cheek's outer face). Output shaft
    of the gearbox couples directly to the spine's M5 trunnion bore so
    the cradle tilt can be commanded by software. The -X trunnion remains
    a passive M5 pivot bolt.
    """
    pivot_z = CRADLE_PIVOT_Z
    # Cheek outer face on +X side (after v3 r2 axis fix)
    cheek_outer_x = +(SPINE_T / 2 + 0.5 + CHEEK_T)
    box_x0 = cheek_outer_x + 4.0   # 4 mm air gap between cheek face and box
    # Gearbox housing — sketched in YZ workplane normal to X
    box = (
        cq.Workplane("YZ")
        .workplane(offset=box_x0)
        .center(0, pivot_z)
        .rect(WORM_GEARBOX_W, WORM_GEARBOX_H)
        .extrude(WORM_GEARBOX_X)
    )
    # NEMA 17 stepper bolted to the back (+X) face of the gearbox.
    stepper_x0 = box_x0 + WORM_GEARBOX_X
    stepper = (
        cq.Workplane("YZ")
        .workplane(offset=stepper_x0)
        .center(0, pivot_z)
        .rect(NEMA17_FACE, NEMA17_FACE)
        .extrude(NEMA17_BODY_L)
    )
    # Output shaft stub — engages cheek + spine trunnion bore in X axis.
    out_shaft = (
        cq.Workplane("YZ")
        .workplane(offset=cheek_outer_x - SPINE_T - CHEEK_T)
        .center(0, pivot_z)
        .circle(CRADLE_PIVOT_BOLT_D / 2 + 0.2)
        .extrude(box_x0 - (cheek_outer_x - SPINE_T - CHEEK_T))
    )
    return box.union(stepper).union(out_shaft)


def make_scale() -> cq.Workplane:
    """A&D EJ-303B-class lab scale envelope (context body, NOT printed).

    Per @swcharles's v4 ask: every render needs a scale + cup so the
    module isn't shown 'floating in midair'. Approximated as a flat
    weighing pan platform on a stepped base. ~213×213×80 mm body
    matches A&D's EJ-303B / FX-i series footprint cited in PR #31.

    Origin: pan top is at Z=Z_SCALE_TOP (positioned in main below).
    """
    base = (
        cq.Workplane("XY")
        .box(SCALE_BASE_D, SCALE_BASE_W, SCALE_BASE_H,
             centered=(True, True, False))
    )
    # Stepped weighing pan rest
    pan_pillar = (
        cq.Workplane("XY")
        .workplane(offset=SCALE_BASE_H)
        .box(SCALE_PAN_OD * 0.4, SCALE_PAN_OD * 0.4, SCALE_PAN_PILLAR_H,
             centered=(True, True, False))
    )
    # Round weighing pan
    pan = (
        cq.Workplane("XY")
        .workplane(offset=SCALE_BASE_H + SCALE_PAN_PILLAR_H)
        .circle(SCALE_PAN_OD / 2)
        .extrude(SCALE_PAN_T)
    )
    return base.union(pan_pillar).union(pan)


def make_cup() -> cq.Workplane:
    """Generic Ø60×100 mm collection cup — context body, NOT printed.
    Sits on the scale pan, directly under the rotor exit nozzle."""
    wall = (
        cq.Workplane("XY")
        .circle(CUP_OD / 2)
        .circle(CUP_OD / 2 - CUP_WALL)
        .extrude(CUP_H)
    )
    floor = (
        cq.Workplane("XY")
        .circle(CUP_OD / 2)
        .extrude(CUP_WALL)
    )
    return wall.union(floor)


# ============================================================================
# Build instances of each part
# ============================================================================
spine = make_spine()
collar = make_bearing_collar()
motor_bracket = make_motor_bracket()
cartridge = make_cartridge()
cheek_L = make_cradle_cheek("L")
cheek_R = make_cradle_cheek("R")
cradle_base = make_cradle_base().translate((0, 0, -CRADLE_BASE_T))   # base top at Z=0 (no gap to cheek foot)

auger = make_auger()
bearing = make_bearing()

# Pulleys: v3 — belt plane is BELOW the cartridge, just above the bearing
# collar (S2). Both pulleys ride at BELT_PLANE_Z. The rotor pulley clamps
# onto the rotor shaft at this height (PR-#16 v4 rotor shaft is solid here).
rotor_z0 = -30.0
pulley_z0 = BELT_PLANE_Z
rotor_pulley = make_pulley(ROTOR_X_OFFSET, 0, pulley_z0, pulley_od=ROTOR_PULLEY_OD)
motor_pulley = make_pulley(MOTOR_AXIS_X, MOTOR_AXIS_OFFSET_Y, pulley_z0, pulley_od=MOTOR_PULLEY_OD)
belt = make_belt(MOTOR_AXIS_X, MOTOR_AXIS_OFFSET_Y, ROTOR_X_OFFSET, 0,
                 pulley_z0 + (PULLEY_H - 4) / 2)

stepper = make_stepper()
solenoid = make_solenoid()
erm = make_erm()
tilt_drive = make_tilt_drive()

# Context bodies (NOT printed): a real lab scale + collection cup so the
# module isn't shown 'floating in midair' (@swcharles v4).
# Place the scale BELOW the rotor exit nozzle (z=-30) so the cup actually
# sits beneath the dispense column. Cradle base hangs above the scale via
# the cradle cheeks (which would in real life clamp to a side stand or
# equipment-rack mount; for visualisation we just drop the scale).
SCALE_PAN_TOP_Z = -150.0   # 120 mm below the rotor exit nozzle
Z_SCALE_BASE_BOTTOM = SCALE_PAN_TOP_Z - SCALE_PAN_T - SCALE_PAN_PILLAR_H - SCALE_BASE_H
scale = make_scale().translate((0, 0, Z_SCALE_BASE_BOTTOM))
# Cup sits ON the scale pan, directly under the rotor exit nozzle.
cup = make_cup().translate((ROTOR_X_OFFSET, 0, SCALE_PAN_TOP_Z))


# ============================================================================
# ASSEMBLY
# ============================================================================
PRINTED = cq.Color(0.85, 0.85, 0.92)
CRADLE_C = cq.Color(0.55, 0.7, 0.55)
asm = cq.Assembly(name="single_channel_module_v3")
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
asm.add(tilt_drive, name="NEMA17_tilt_worm_gearbox", color=cq.Color(0.25, 0.25, 0.28))

# Context bodies — flagged in their names so anyone parsing the STEP
# knows these are not part of the printed module.
asm.add(scale, name="CONTEXT_AnD_lab_scale", color=cq.Color(0.7, 0.7, 0.75))
asm.add(cup, name="CONTEXT_collection_cup", color=cq.Color(0.85, 0.92, 1.0))


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
    stepper, solenoid, erm, tilt_drive,
])

# v4 (@swcharles): export a single STL of the WHOLE assembly so reviewers
# can load one file and see how every piece fits together. Also export
# a "with-context" STL that includes the scale + cup envelopes.
print("writing full-assembly STL ...")
cq.exporters.export(combined, str(STL_DIR / "ASSEMBLY_full_module.stl"),
                    tolerance=0.15, angularTolerance=0.3)
print(f"wrote {STL_DIR / 'ASSEMBLY_full_module.stl'}")

combined_with_context = _union_all([combined, scale, cup])
cq.exporters.export(combined_with_context,
                    str(STL_DIR / "ASSEMBLY_full_module_with_scale_and_cup.stl"),
                    tolerance=0.2, angularTolerance=0.4)
print(f"wrote {STL_DIR / 'ASSEMBLY_full_module_with_scale_and_cup.stl'}")

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
    cq.exporters.export(combined_with_context, str(path),
                        opt={**opts, "projectionDir": projdir})
    print(f"wrote {path}")

# Also clean up obsolete render PNGs that no longer match (we regenerate
# the iso/front/top/side PNGs in a follow-up cairosvg pass)
print("done.")

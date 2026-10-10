"""World frame and part placements for the doser assemblies.

Ported from PR #170's ``cad/full-assembly/onshape/layout.py`` (numbers read
off the lab's Fusion 360 STEP files there), so the text-to-cad assemblies
put every part exactly where PR #170's does.  Each recreated part is
modelled in the frame its Fusion STEP was exported in, so the same 4 x 4
transforms place both.

World frame = the baseplate's frame: Z up, plate underside on z = 0, hinge
axis along X through (y, z) = (HINGE_Y, HINGE_Z), outlet end of the auger
towards -Y, stepper on the -X side, mm.

Two layouts:

* ``"below"`` - the current design: each MG996R sits on two posts on the
  baseplate's front arms, its 14T pinion meshing the mounting plate's 28T
  gear from below the hinge (spline 27.26 mm under it).
* ``"above"`` - the servos-above variant (issue #172): both servos and
  their pinions turned 180 deg about the hinge axis, so the pinions mesh
  the 28T gears from above, and the baseplate's front arms, legs and posts
  go.  Nothing hangs below or in front of the nozzle any more.  The whole
  doser also sits ``DROP["above"]`` = 5 mm lower on its baseplate: the
  towers and cradles are that much shorter, and the plate is relieved
  under the mounting plate's floor (see baseplate.py).  Every placement
  except the baseplate's is the PR #170 one moved down by ``lower(variant)``.
"""
from __future__ import annotations

import math

import numpy as np

# --------------------------------------------------------------------------- #
# 4 x 4 helpers
# --------------------------------------------------------------------------- #
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
NX, NY, NZ = (-1, 0, 0), (0, -1, 0), (0, 0, -1)


def T(R=None, t=(0.0, 0.0, 0.0)) -> np.ndarray:
    """4x4 from a rotation given as columns (images of local X, Y, Z)."""
    M = np.eye(4)
    if R is not None:
        M[:3, :3] = np.array(R, dtype=float).T
    M[:3, 3] = t
    return M


def rot_about(axis, deg: float, point=(0.0, 0.0, 0.0)) -> np.ndarray:
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(4)
    R[:3, :3] = np.eye(3) + s * K + (1 - c) * K @ K
    p = np.asarray(point, float)
    return T(None, p) @ R @ T(None, -p)


# --------------------------------------------------------------------------- #
# features of the parts (PR #170 layout.py)
# --------------------------------------------------------------------------- #
HINGE_Y, HINGE_Z = 45.4, 43.25
HINGE = (0.0, HINGE_Y, HINGE_Z)
SERVO_SPLINE_Z = 16.0                       # below the hinge by 27.26 mm
SERVO_CENTRE_DIST = HINGE_Z - SERVO_SPLINE_Z
SERVO_POST_INNER_X = 67.1
SERVO_FLANGE_UNDERSIDE_BELOW_TOP = 37.0 - 26.5
GEAR_PLANE_X = (41.8, 54.1)                 # 28T gears, |x|

MP_MID_Z = -41.8
MP_FLOOR_Y = -29.25
MP_STEPPER_FACE_BACK_X = -89.33
MP_STEPPER_FACE_FRONT_X = -83.33
MP_STEPPER_Z = -9.8
# the floor's three M3 rows (mounting_plate.FLOOR_HOLE_XS), front to back:
# the front bracket at -42.33, the tap-collar base at -58.33, the rear
# bracket at -124.  The collar rides loose on the tube, so it has to sit
# between the front bracket and the auger's 44T gear, which keep it on its
# base when the doser tilts (PR #170 had the front bracket and the base the
# other way round, with nothing in front of the collar).
MP_ROWS_BRACKET = (-124.0, -42.33)
MP_ROW_TAP_BASE = -58.33
TAP_BASE_DEPTH = 18.0

# The 20T pinion and the auger's 44T gear (centred on the pinion's teeth)
# stand GEAR_TAP_BASE_GAP behind the tap-collar base: the base's hard-stop
# tower is inside the pinion's tip circle, and the gear's inside the base's
# block.  That is 1.6 mm further back than PR #170, which put the pinion's
# hub 0.5 mm off the stepper plate; the Ø9 hub now reaches 1.1 mm into the
# plate's Ø22 pilot hole (the motor's pilot fills only the back 2 mm of it).
GEAR_TAP_BASE_GAP = 1.0
PINION_TEETH_W, PINION_LEN = 10.0, 16.1
AUGER_GEAR_FROM_OUTLET = 83.33
AUGER_LEN = 250.0
# the cap screwed home: its thread groove meets the auger's 3.5 mm-pitch
# thread half a turn round from the model's frame (checks/cap_thread.py: the
# overlap is 546 mm^3 at 0 deg and zero from 150 to 210 deg)
CAP_TURN_DEG = 180.0

MP = T([NY, Z, NX], (MP_MID_Z, HINGE_Y, HINGE_Z))

PINION_FRONT_X = MP_ROW_TAP_BASE - TAP_BASE_DEPTH / 2 - GEAR_TAP_BASE_GAP   # -68.33
_pinion_teeth_mid_x = PINION_FRONT_X - PINION_TEETH_W / 2
OUTLET_MP_X = _pinion_teeth_mid_x + AUGER_GEAR_FROM_OUTLET     # 10.0 mm
AUGER_IN_MP = T([Z, Y, NX], (OUTLET_MP_X, 0.0, MP_MID_Z))


def bracket_in_mp(row_x: float) -> np.ndarray:
    return T([Z, X, Y], (row_x - 6.0, MP_FLOOR_Y, MP_MID_Z))


COLLAR_IN_MP = T([NZ, NX, Y], (MP_ROW_TAP_BASE + 8.5, 0.0, MP_MID_Z))
TAP_BASE_IN_MP = T([Z, X, Y], (MP_ROW_TAP_BASE, MP_FLOOR_Y, MP_MID_Z))
SOLENOID_IN_COLLAR = T(None, (0.0, 15.8, 41.0))
COLLAR_ROLL_DEG = -30.0

NEMA_IN_MP = T([NZ, Y, X], (MP_STEPPER_FACE_BACK_X, 0.0, MP_STEPPER_Z))
PINION_PHASE_DEG = 9.0
PINION_IN_MP = T([Z, Y, NX], (PINION_FRONT_X, 0.0, MP_STEPPER_Z)) @ rot_about(Z, PINION_PHASE_DEG)

_servo_top_x = SERVO_POST_INNER_X - SERVO_FLANGE_UNDERSIDE_BELOW_TOP
SERVO_POS = T([NY, Z, NX], (_servo_top_x, HINGE_Y, SERVO_SPLINE_Z))
SERVO_NEG = T([NY, NZ, X], (-_servo_top_x, HINGE_Y, SERVO_SPLINE_Z))
SPINION_POS = T([Y, Z, X], (GEAR_PLANE_X[0], HINGE_Y, SERVO_SPLINE_Z))
SPINION_NEG = T([Y, NZ, NX], (-GEAR_PLANE_X[0], HINGE_Y, SERVO_SPLINE_Z))

SERVO_RATIO = 28 / 14
STEPPER_RATIO = 44 / 20

# mounting board: top on z = 0.  Its front edge is where the legs' back
# faces are (current design), or 52.6 mm further back for the servos-above
# plate, which overhangs the board.  There the tap-collar base's M3 x 30
# flat head ends flush with the plate's underside (y = 101-107 at rest),
# so the board's edge has to stay behind it.
BOARD_T = 38.1
BOARD_FRONT_Y = {"below": 55.4, "above": 108.0}

# the servos-above variant: the servo side of the drive turned 180 deg
# about the hinge axis
FLIP = rot_about(X, 180.0, HINGE)

# How far each layout's doser sits below PR #170's.  At rest the mounting
# plate's floor is 2.0 mm above the baseplate and the M3 button heads under
# it 0.35 mm, so lowering it means relieving the plate under the floor
# (baseplate.py).  5 mm leaves those heads 1.35 mm above the board top.
DROP = {"below": 0.0, "above": 5.0}


def lower(variant: str = "below") -> np.ndarray:
    """Moves PR #170's placements down to this layout's height."""
    return T(None, (0.0, 0.0, -DROP[variant]))


def hinge(variant: str = "below") -> tuple[float, float, float]:
    return (0.0, HINGE_Y, HINGE_Z - DROP[variant])


def outlet_point(tilt_deg: float = 0.0, variant: str = "below") -> np.ndarray:
    """World position of the outlet hole (centre of the auger's end face)."""
    M = lower(variant) @ tilt_matrix(tilt_deg) @ MP @ AUGER_IN_MP
    return (M @ np.array([0.0, 0.0, 0.0, 1.0]))[:3]


def tilt_matrix(tilt_deg: float) -> np.ndarray:
    """The mounting plate's motion: outlet down for positive tilt (about
    PR #170's hinge; ``lower(variant)`` goes on the left)."""
    return rot_about(X, tilt_deg, HINGE)


def placements(tilt_deg: float = 0.0, variant: str = "below",
               roll_deg: float = COLLAR_ROLL_DEG, auger_deg: float = 0.0) -> dict:
    """name -> (part key, world 4x4).  Part keys name the recreated models
    (src/parts, src/purchased); ``variant`` is "below" or "above"."""
    if variant not in ("below", "above"):
        raise ValueError(variant)
    low = lower(variant)
    mp = low @ tilt_matrix(tilt_deg) @ MP
    roll = rot_about(X, roll_deg, (0.0, 0.0, MP_MID_Z))
    collar = mp @ roll @ COLLAR_IN_MP
    auger = mp @ AUGER_IN_MP @ rot_about(Z, auger_deg)
    pinion = mp @ PINION_IN_MP @ rot_about(Z, -STEPPER_RATIO * auger_deg)
    sp = SERVO_RATIO * tilt_deg
    side = low @ (FLIP if variant == "above" else np.eye(4))
    above = variant == "above"
    return {
        "Baseplate": ("baseplate_servos_above" if above else "baseplate", np.eye(4)),
        "Mounting plate": ("mounting_plate_servos_above" if above else "mounting_plate", mp),
        "Auger": ("auger", auger),
        "Auger cap": ("auger_cap", auger @ T(None, (0, 0, AUGER_LEN)) @ rot_about(Z, CAP_TURN_DEG)),
        "Bracket (rear)": ("bracket", mp @ bracket_in_mp(MP_ROWS_BRACKET[0])),
        "Bracket (front)": ("bracket", mp @ bracket_in_mp(MP_ROWS_BRACKET[1])),
        "Tap collar base": ("tap_collar_base", mp @ TAP_BASE_IN_MP),
        "Tap collar": ("tap_collar", collar),
        "Solenoid (Adafruit 412)": ("solenoid_412", collar @ SOLENOID_IN_COLLAR),
        "Stepper pinion": ("stepper_pinion", pinion),
        "Stepper (NEMA 11)": ("nema11", mp @ NEMA_IN_MP),
        "Servo pinion (+X)": ("servo_pinion", side @ SPINION_POS @ rot_about(Z, -sp)),
        "Servo pinion (-X)": ("servo_pinion", side @ SPINION_NEG @ rot_about(Z, sp)),
        "Servo MG996R (+X)": ("mg996r", side @ SERVO_POS),
        "Servo MG996R (-X)": ("mg996r", side @ SERVO_NEG),
    }


def board_placement(variant: str = "below", front_y: float | None = None) -> np.ndarray:
    y = BOARD_FRONT_Y[variant] if front_y is None else front_y
    return T(None, (0.0, y, 0.0))


def to_location(M: np.ndarray):
    """4x4 -> build123d Location."""
    from build123d import Location
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
    return Location(tr)

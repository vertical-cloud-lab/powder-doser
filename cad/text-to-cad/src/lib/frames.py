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
  go.  Nothing hangs below or in front of the nozzle any more.
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
MP_ROWS_BRACKET = (-124.0, -58.33)
MP_ROW_TAP_BASE = -42.33

PINION_HUB_GAP = 0.5
PINION_TEETH_W, PINION_LEN = 10.0, 16.1
AUGER_GEAR_FROM_OUTLET = 83.33
AUGER_LEN = 250.0

MP = T([NY, Z, NX], (MP_MID_Z, HINGE_Y, HINGE_Z))

_pinion_teeth_mid_x = (MP_STEPPER_FACE_FRONT_X + PINION_HUB_GAP
                       + (PINION_LEN - PINION_TEETH_W) + PINION_TEETH_W / 2)
OUTLET_MP_X = _pinion_teeth_mid_x + AUGER_GEAR_FROM_OUTLET     # 11.6 mm
AUGER_IN_MP = T([Z, Y, NX], (OUTLET_MP_X, 0.0, MP_MID_Z))


def bracket_in_mp(row_x: float) -> np.ndarray:
    return T([Z, X, Y], (row_x - 6.0, MP_FLOOR_Y, MP_MID_Z))


COLLAR_IN_MP = T([NZ, NX, Y], (MP_ROW_TAP_BASE + 8.5, 0.0, MP_MID_Z))
TAP_BASE_IN_MP = T([Z, X, Y], (MP_ROW_TAP_BASE, MP_FLOOR_Y, MP_MID_Z))
SOLENOID_IN_COLLAR = T(None, (0.0, 15.8, 41.0))
COLLAR_ROLL_DEG = -30.0

NEMA_IN_MP = T([NZ, Y, X], (MP_STEPPER_FACE_BACK_X, 0.0, MP_STEPPER_Z))
PINION_PHASE_DEG = 9.0
PINION_IN_MP = (T([Z, Y, NX], (MP_STEPPER_FACE_FRONT_X + PINION_HUB_GAP + PINION_LEN,
                               0.0, MP_STEPPER_Z))
                @ rot_about(Z, PINION_PHASE_DEG))

_servo_top_x = SERVO_POST_INNER_X - SERVO_FLANGE_UNDERSIDE_BELOW_TOP
SERVO_POS = T([NY, Z, NX], (_servo_top_x, HINGE_Y, SERVO_SPLINE_Z))
SERVO_NEG = T([NY, NZ, X], (-_servo_top_x, HINGE_Y, SERVO_SPLINE_Z))
SPINION_POS = T([Y, Z, X], (GEAR_PLANE_X[0], HINGE_Y, SERVO_SPLINE_Z))
SPINION_NEG = T([Y, NZ, NX], (-GEAR_PLANE_X[0], HINGE_Y, SERVO_SPLINE_Z))

SERVO_RATIO = 28 / 14
STEPPER_RATIO = 44 / 20

# mounting board: top on z = 0, front edge where the legs' back faces are
BOARD_T = 38.1
BOARD_FRONT_Y = 55.4

# the servos-above variant: the servo side of the drive turned 180 deg
# about the hinge axis
FLIP = rot_about(X, 180.0, HINGE)


def outlet_point(tilt_deg: float = 0.0) -> np.ndarray:
    """World position of the outlet hole (centre of the auger's end face)."""
    M = tilt_matrix(tilt_deg) @ MP @ AUGER_IN_MP
    return (M @ np.array([0.0, 0.0, 0.0, 1.0]))[:3]


def tilt_matrix(tilt_deg: float) -> np.ndarray:
    """The mounting plate's motion: outlet down for positive tilt."""
    return rot_about(X, tilt_deg, HINGE)


def placements(tilt_deg: float = 0.0, variant: str = "below",
               roll_deg: float = COLLAR_ROLL_DEG, auger_deg: float = 0.0) -> dict:
    """name -> (part key, world 4x4).  Part keys name the recreated models
    (src/parts, src/purchased); ``variant`` is "below" or "above"."""
    if variant not in ("below", "above"):
        raise ValueError(variant)
    mp = tilt_matrix(tilt_deg) @ MP
    roll = rot_about(X, roll_deg, (0.0, 0.0, MP_MID_Z))
    collar = mp @ roll @ COLLAR_IN_MP
    auger = mp @ AUGER_IN_MP @ rot_about(Z, auger_deg)
    pinion = mp @ PINION_IN_MP @ rot_about(Z, -STEPPER_RATIO * auger_deg)
    sp = SERVO_RATIO * tilt_deg
    side = FLIP if variant == "above" else np.eye(4)
    above = variant == "above"
    return {
        "Baseplate": ("baseplate_servos_above" if above else "baseplate", np.eye(4)),
        "Mounting plate": ("mounting_plate_servos_above" if above else "mounting_plate", mp),
        "Auger": ("auger", auger),
        "Auger cap": ("auger_cap", auger @ T(None, (0, 0, AUGER_LEN))),
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


def board_placement() -> np.ndarray:
    return T(None, (0.0, BOARD_FRONT_Y, 0.0))


def to_location(M: np.ndarray):
    """4x4 -> build123d Location."""
    from build123d import Location
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
    return Location(tr)

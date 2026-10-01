"""Where every part goes in the current-design assembly (tilt 0).

World frame = the Fusion baseplate's own frame: Z up, plate underside on
z = 0, hinge axis along X through (y, z) = (45.4, 43.25), outlet end of
the auger towards -Y (over the U-cutout), stepper on the -X side.  All
lengths in mm.  Each part keeps the frame its STEP file was exported in;
``PLACEMENTS`` maps it into the world with a 4 x 4 transform.

How the frames were tied together (numbers read off the STEP files):

* Mounting plate (MP) frame: hinge axis = MP Z through the origin, floor
  top at MP y = -29.25, auger axis along MP X at (y, z) = (0, -41.8),
  stepper plate faces at x = -89.33 / -83.33 with the NEMA 11 pilot at
  (y, z) = (0, -9.8), i.e. 32 mm from the auger = (20 + 44) / 2 at module 1.
  Its knuckles sit 0.3 mm inside the baseplate towers and its 28 T gears
  0.6 mm outside them when the MP's mid-plane (MP z = -41.8) is world x = 0.
* Brackets and the tap-collar base stand on the MP floor rows at
  MP x = -124 and -58.33 (brackets) and -42.33 (tap-collar base); their
  bores are 29.25 mm above their bases, which puts the auger on MP y = 0.
* Auger: the 20 T pinion's hub sits 0.5 mm off the stepper plate, and the
  auger's 44 T gear (83.33 mm from the outlet) is centred on the pinion
  teeth, so the outlet ends up 11.6 mm in front of the hinge axis.
* Servos: posts' holes at y = 11.5 / 59.54, z = 11.48 / 20.52 (48.04 x
  9.04 mm); spline straight under the hinge at (y, z) = (45.4, 16), which
  is 27.26 mm = 1.298 x (28 + 14) / 2 from it; flange on the posts' inner
  faces (|x| = 67.1).  Servo pinions coplanar with the 28 T gears.
* Tap collar: Fusion collar on the auger above the AI base, solenoid
  plate towards the cap so the solenoid hangs over the collar's Ø6.9
  plunger hole (as on the 11 Sep rig photo, where the solenoid is in
  front of its plate).  Clamp ears over the base's hard-stop bump.
  Roll about the auger is 0 here (plunger vertical); on the rig the
  collar has turned roughly 40° towards +X.

    python3 layout.py              # interference check + preview PNG + GLB
"""
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COMP = HERE.parent / "components"

# --------------------------------------------------------------------------- #
# frame bookkeeping
# --------------------------------------------------------------------------- #
def T(R=None, t=(0.0, 0.0, 0.0)) -> np.ndarray:
    """4x4 from a rotation (columns = images of the local X, Y, Z axes)."""
    M = np.eye(4)
    if R is not None:
        M[:3, :3] = np.array(R, dtype=float).T   # given as columns
    M[:3, 3] = t
    return M


def rot_about(axis, deg) -> np.ndarray:
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    M = np.eye(4)
    M[:3, :3] = np.eye(3) + s * K + (1 - c) * K @ K
    return M


X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
NX, NY, NZ = (-1, 0, 0), (0, -1, 0), (0, 0, -1)

# baseplate (world) features
HINGE_Y, HINGE_Z = 45.4, 43.25
SERVO_SPLINE_Z = 16.0
SERVO_POST_INNER_X = 67.1
SERVO_FLANGE_UNDERSIDE_BELOW_TOP = 37.0 - 26.5     # purchased_parts.py
GEAR_PLANE_X = (41.8, 54.1)                         # 28 T gears, |x|

# mounting-plate features (MP frame)
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

# MP frame -> world
MP = T([NY, Z, NX], (MP_MID_Z, HINGE_Y, HINGE_Z))   # MP (0, 0, -41.8) -> world x = 0

# auger frame: axis +Z from the outlet; into the MP: +Z -> MP -X
pinion_teeth_mid_x = (MP_STEPPER_FACE_FRONT_X + PINION_HUB_GAP
                      + (PINION_LEN - PINION_TEETH_W) + PINION_TEETH_W / 2)
OUTLET_MP_X = pinion_teeth_mid_x + AUGER_GEAR_FROM_OUTLET
AUGER_IN_MP = T([Z, Y, NX], (OUTLET_MP_X, 0.0, MP_MID_Z))


def bracket_in_mp(row_x: float) -> np.ndarray:
    # bracket: base z = 0, bore along +Y (0..12), holes at y = 6
    return T([Z, X, Y], (row_x - 6.0, MP_FLOOR_Y, MP_MID_Z))


# tap-collar base (AI, single hole row at y = 0, bump at +x) and the Fusion
# collar (bore along +Y 0..17, solenoid plate at y = 15.8..17, ears at -x).
COLLAR_IN_MP = T([NZ, NX, Y],
                 (MP_ROW_TAP_BASE + 8.5, 0.0, MP_MID_Z))
TAP_BASE_IN_MP = T([Z, X, Y],
                   (MP_ROW_TAP_BASE, MP_FLOOR_Y, MP_MID_Z))
SOLENOID_IN_COLLAR = T(None, (0.0, 15.8, 41.0))
COLLAR_ROLL_DEG = 0.0

# stepper + pinion
NEMA_IN_MP = T([NZ, Y, X],
               (MP_STEPPER_FACE_BACK_X, 0.0, MP_STEPPER_Z))
PINION_IN_MP = T([Z, Y, NX],
                 (MP_STEPPER_FACE_FRONT_X + PINION_HUB_GAP + PINION_LEN, 0.0, MP_STEPPER_Z))

# servos (world): spline +Z native, case towards native +X
_servo_top_x = SERVO_POST_INNER_X - SERVO_FLANGE_UNDERSIDE_BELOW_TOP
SERVO_POS = T([NY, Z, NX], (_servo_top_x, HINGE_Y, SERVO_SPLINE_Z))
SERVO_NEG = T([NY, NZ, X], (-_servo_top_x, HINGE_Y, SERVO_SPLINE_Z))
SPINION_POS = T([Y, Z, X], (GEAR_PLANE_X[0], HINGE_Y, SERVO_SPLINE_Z))
SPINION_NEG = T([Y, NZ, NX], (-GEAR_PLANE_X[0], HINGE_Y, SERVO_SPLINE_Z))


def placements(tilt_deg: float = 0.0, roll_deg: float = COLLAR_ROLL_DEG) -> dict:
    """name -> (STEP path relative to components/, world transform)."""
    tilt = (T(None, (0, HINGE_Y, HINGE_Z)) @ rot_about(X, tilt_deg)
            @ T(None, (0, -HINGE_Y, -HINGE_Z)))
    mp = tilt @ MP
    roll = (T(None, (0, 0, MP_MID_Z)) @ rot_about(X, roll_deg)
            @ T(None, (0, 0, -MP_MID_Z)))           # about the auger axis (MP X)
    collar = mp @ roll @ COLLAR_IN_MP
    return {
        "Baseplate": ("fusion-step/baseplate.step", np.eye(4)),
        "Mounting plate": ("fusion-step/mounting-plate.step", mp),
        "Auger": ("fusion-step/auger.step", mp @ AUGER_IN_MP),
        "Auger cap": ("fusion-step/auger-cap.step",
                      mp @ AUGER_IN_MP @ T(None, (0, 0, AUGER_LEN))),
        "Bracket (rear)": ("fusion-step/brackets.step", mp @ bracket_in_mp(MP_ROWS_BRACKET[0])),
        "Bracket (front)": ("fusion-step/brackets.step", mp @ bracket_in_mp(MP_ROWS_BRACKET[1])),
        "Tap collar base (AI)": ("ai-step/tap-collar-base.step", mp @ TAP_BASE_IN_MP),
        "Tap collar": ("fusion-step/tap-collar.step", collar),
        "Solenoid (Adafruit 412)": ("purchased/adafruit-412-solenoid.step",
                                    collar @ SOLENOID_IN_COLLAR),
        "Stepper pinion": ("fusion-step/stepper-pinion.step", mp @ PINION_IN_MP),
        "Stepper (NEMA 11)": ("purchased/nema11-11hs18-0674s.step", mp @ NEMA_IN_MP),
        "Servo pinion (+X)": ("fusion-step/servo-pinion.step", SPINION_POS),
        "Servo pinion (-X)": ("fusion-step/servo-pinion.step", SPINION_NEG),
        "Servo MG996R (+X)": ("purchased/mg996r-servo.step", SERVO_POS),
        "Servo MG996R (-X)": ("purchased/mg996r-servo.step", SERVO_NEG),
    }


def _shape(path: Path):
    import cadquery as cq
    shp = cq.importers.importStep(str(path))
    return cq.Compound.makeCompound(shp.vals())


def _moved(shape, M):
    import cadquery as cq
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
    return cq.Shape.cast(shape.moved(cq.Location(tr)).wrapped)


def interference(places: dict, min_vol: float = 1.0) -> list[tuple[str, str, float]]:
    shapes = {n: _moved(_shape(COMP / p), M) for n, (p, M) in places.items()}
    hits = []
    for a, b in itertools.combinations(shapes, 2):
        ba, bb = shapes[a].BoundingBox(), shapes[b].BoundingBox()
        if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin
                or bb.ymax < ba.ymin or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
            continue
        v = shapes[a].intersect(shapes[b]).Volume()
        if v > min_vol:
            hits.append((a, b, round(v, 1)))
    return hits


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-check", action="store_true")
    a = ap.parse_args()
    places = placements()
    out = {n: {"step": p, "transform_mm": np.round(M, 6).tolist()} for n, (p, M) in places.items()}
    (HERE / "placements.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"outlet {OUTLET_MP_X:.2f} mm in front of the hinge (MP x); "
          f"world outlet y = {HINGE_Y - OUTLET_MP_X:.2f}")
    if not a.no_check:
        for h in interference(places):
            print("overlap", h)


if __name__ == "__main__":
    main()

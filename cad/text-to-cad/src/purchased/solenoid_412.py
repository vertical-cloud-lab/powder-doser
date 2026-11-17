"""Adafruit 412 push-pull solenoid (JF-0530B / TAU0730TM), simplified.

step.parts has no Adafruit 412 / JF-0530B (searched JF-0530B, 0530B, JF0530,
JF-0530, TAU0730TM, solenoid, push pull, Adafruit 412, the adafruit family,
the plunger tag, ...; its only solenoid is the Adafruit 413 *large* solenoid,
29 x 24 x 69.7 mm), so this is PR #170's simplified model
(cad/full-assembly/onshape/purchased_parts.py, ``adafruit412_pieces()``)
rebuilt parametrically; see checks/results/purchased_step_parts.json.

Frame (as PR #170): mounting face on the plane y = 0 with the body in -y;
plunger axis along +z (spring end up) at x = 0, y = -7; body centred on
z = 0.  Datasheet numbers as recorded in PR #51/#170: 29.7 mm body, 14 x 17 mm
open frame, Ø6.9 bushing, 51.9 mm long with the plunger, two M3 ears
diagonally opposite (18.2 mm across, 16.0 mm along).

Children, named as PR #170's pieces so the tapping animation can move them:

* ``frame``   -- ``yoke`` (open frame with the two ears and the bushing) and
  ``coil``; fixed.
* ``plunger`` -- plunger rod with its end cap; slides along z.
* ``spring``  -- six turns between the frame top and the cap; squashes.

PR #170's pieces overlap (the plunger runs through a solid coil and end
plates, and the spring turns bite 0.1 mm into it, so the union is one solid).
Here the frame has a Ø5.0 bore for the plunger and the spring's bore equals
the plunger diameter, so the pieces only touch and the plunger can move
without passing through anything; their union is unchanged.
"""
from __future__ import annotations

from cadgen import build123d as bd
from cadgen import srgb, step

BODY_L = 29.7                  # frame length along the plunger axis (z)
FRAME_W, FRAME_D = 17.0, 14.0  # across the mounting face (x), away from it (y)
FRAME_WALL = 1.2               # open frame plates
LEN_TOTAL = 51.9               # plunger push end to cap top
BOTTOM_STICKOUT = 6.0          # plunger below the body (push end)
PLUNGER_D = 5.0
BUSHING_D, BUSHING_T = 6.9, 0.5
COIL_D = FRAME_D - 2.8         # 11.2
COIL_L = BODY_L - 3.0          # 26.7
EAR_SIZE, EAR_T = 6.0, 1.0     # square ears on the mounting face
EAR_HOLE_D = 3.1               # M3 clearance
HOLE_ACROSS, HOLE_ALONG = 18.2, 16.0   # ear holes: spacing in x, in z
CAP_D, CAP_T = 9.0, 1.0
SPRING_OD, SPRING_ID = 8.0, PLUNGER_D
SPRING_TURNS, SPRING_WIRE = 6, 0.8     # rings standing in for the coils
SPRING_START = 1.0             # first turn above the frame top

AXIS_Y = -FRAME_D / 2          # plunger axis: x = 0, y = -7
TOP_LEN = LEN_TOTAL - BODY_L - BOTTOM_STICKOUT   # plunger above the frame: 16.2
SPRING_PITCH = (TOP_LEN - 3.0) / SPRING_TURNS    # 2.2

YOKE_COLOR = "#9A9EA8"         # zinc-plated steel
COIL_COLOR = "#B87333"         # copper winding
PLUNGER_COLOR = "#C8CCD2"
SPRING_COLOR = "#7D838C"


def _base() -> tuple:
    """Centred in x and y, based on z = 0."""
    return (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)


def _on_axis(z0: float, d: float, length: float) -> bd.Solid:
    """Cylinder of diameter d on the plunger axis from z0 up by length."""
    return bd.Pos(0, AXIS_Y, z0) * bd.Cylinder(d / 2, length, align=_base())


def _bore() -> bd.Solid:
    """The plunger's bore through the frame (line-to-line with the plunger)."""
    return _on_axis(-BODY_L / 2 - BUSHING_T - 1.0, PLUNGER_D, BODY_L + BUSHING_T + 2.0)


def _yoke() -> bd.Part:
    outer = bd.Pos(0, AXIS_Y, 0) * bd.Box(FRAME_W, FRAME_D, BODY_L)
    # through-cut along x leaves the two side plates and the two end plates
    window = bd.Pos(0, AXIS_Y, 0) * bd.Box(FRAME_W + 2.0, FRAME_D - 2 * FRAME_WALL,
                                           BODY_L - 2 * FRAME_WALL)
    yoke = outer - window
    # two ears on the mounting face, diagonally opposite; each ear is drilled
    # on its own, so the frame plate refills the inboard part of the hole
    for sx, sz in ((-1, -1), (1, 1)):
        at = bd.Pos(sx * HOLE_ACROSS / 2, -EAR_T / 2, sz * HOLE_ALONG / 2)
        ear = at * bd.Box(EAR_SIZE, EAR_T, EAR_SIZE)
        ear = ear - at * bd.Rot(90, 0, 0) * bd.Cylinder(EAR_HOLE_D / 2, EAR_T + 2.0)
        yoke = yoke + ear
    bushing = _on_axis(-BODY_L / 2 - BUSHING_T, BUSHING_D, BUSHING_T)
    return (yoke + bushing - _bore()).clean()


def _coil() -> bd.Part:
    return _on_axis(-COIL_L / 2, COIL_D, COIL_L) - _bore()


def _plunger() -> bd.Part:
    rod = _on_axis(-BODY_L / 2 - BOTTOM_STICKOUT, PLUNGER_D, LEN_TOTAL)
    cap = _on_axis(BODY_L / 2 + TOP_LEN - CAP_T, CAP_D, CAP_T)
    return (rod + cap).clean()


def _spring() -> bd.Compound:
    turns = []
    for k in range(SPRING_TURNS):
        z0 = BODY_L / 2 + SPRING_START + k * SPRING_PITCH
        ring = _on_axis(z0, SPRING_OD, SPRING_WIRE) - _on_axis(z0 - 1.0, SPRING_ID, SPRING_WIRE + 2.0)
        turns.extend(ring.solids())
    return bd.Compound(turns)


@step(out="../../STEP/purchased/solenoid_412.step")
def solenoid_412():
    yoke = _yoke()
    yoke.label = "yoke"
    yoke.color = srgb(YOKE_COLOR)
    coil = _coil()
    coil.label = "coil"
    coil.color = srgb(COIL_COLOR)
    frame = bd.Compound(children=[yoke, coil], label="frame")
    plunger = _plunger()
    plunger.label = "plunger"
    plunger.color = srgb(PLUNGER_COLOR)
    spring = _spring()
    spring.label = "spring"
    spring.color = srgb(SPRING_COLOR)
    return bd.Compound(children=[frame, plunger, spring], label="solenoid_412")


if __name__ == "__main__":
    solenoid_412()

"""Stepper pinion: 20T module-1 spur pinion on the NEMA 11 stepper shaft.

Recreates components/fusion-step/stepper-pinion.step (Fusion 360 SpurGear
add-in: module 1.0, 20 teeth, 20 deg, zero backlash) in its own frame: axis
+Z, gear face z = 0 .. GEAR_WIDTH, hub on top to z = LENGTH, tooth 0 on +X.
It meshes the auger tube's 44T gear at 32 mm centres.
"""
from __future__ import annotations

from cadgen import build123d as bd
from cadgen import step, stl

from lib.gears import spur_gear

GEAR_MODULE = 1.0
GEAR_TEETH = 20
GEAR_WIDTH = 10.0
LENGTH = 16.1                   # gear + hub
HUB_D = 9.0
BORE_D = 5.2                    # NEMA 11 shaft (5 mm) + clearance
FLAT_OFFSET = 2.1               # D-flat distance from the axis, on +Y


def _d_bore(length: float) -> bd.Solid:
    """D-shaped through-bore, run 1 mm past both faces."""
    bore = bd.Pos(0, 0, -1) * bd.Cylinder(BORE_D / 2, length + 2,
                                          align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    flat = bd.Pos(0, FLAT_OFFSET, -1) * bd.Box(BORE_D * 2, BORE_D, length + 2,
                                               align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.MIN))
    return (bore - flat).solids()[0]


@step(out="../../STEP/parts/stepper_pinion.step")
@stl(out="../../STL/parts/stepper_pinion.stl")
def stepper_pinion():
    gear = spur_gear(GEAR_MODULE, GEAR_TEETH, GEAR_WIDTH)
    hub_start = GEAR_WIDTH / 2                      # sunk into the gear: no coplanar faces
    hub = bd.Pos(0, 0, hub_start) * bd.Cylinder(HUB_D / 2, LENGTH - hub_start,
                                                align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    part = (gear + hub - _d_bore(LENGTH)).solids()[0]
    part.label = "stepper_pinion"
    return part


if __name__ == "__main__":
    stepper_pinion()

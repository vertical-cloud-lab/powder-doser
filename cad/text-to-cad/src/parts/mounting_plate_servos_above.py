"""Mounting plate for the servos-above variant (issue #172).

Identical to mounting_plate.py except that the toothed sector of both 28T
gears is turned 180 deg about the hinge.  The lab's plate has teeth only
from about 251 deg through 0 deg to 97 deg (MP x-y plane, from MP +x),
which covers a pinion below the hinge (270 deg) over the 0-45 deg tilt
range (270-315 deg).  A pinion above the hinge works over 90-135 deg, so
the sector has to move with it.
"""
from __future__ import annotations

from cadgen import step, stl

from mounting_plate import make_mounting_plate

SECTOR_TURN_DEG = 180.0


@step(out="../../STEP/parts/mounting_plate_servos_above.step")
@stl(out="../../STL/parts/mounting_plate_servos_above.stl")
def mounting_plate_servos_above():
    return make_mounting_plate(tooth_sector_rotation_deg=SECTOR_TURN_DEG)


if __name__ == "__main__":
    mounting_plate_servos_above()

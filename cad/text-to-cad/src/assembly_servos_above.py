"""The doser with its servos above the hinge (issue #172), fully assembled.

Every recreated printed part, the purchased parts, every screw and nut
(step.parts geometry, PR #170's joints), the POWDER_DOSER_V2 electronics on
their holder, and the 38.1 mm board.  The sidecar declares the mates: the
0-45 deg hinge geared to both servo pinions, the auger geared to the
stepper pinion, and the solenoid plunger (see lib/doser.py).

    PYTHONPATH=src:src/parts:src/purchased:src/electronics python3 src/assembly_servos_above.py
"""
from __future__ import annotations

from cadgen import glb, step

from lib import doser
from lib.electronics_place import electronics

VARIANT = "above"
KINEMATICS = doser.kinematics(VARIANT)


@step(out="../STEP/assembly_servos_above.step", kinematics=KINEMATICS)
@glb(out="../GLB/assembly_servos_above.glb")
def assembly_servos_above():
    return doser.build_doser(VARIANT, electronics=electronics(VARIANT))


if __name__ == "__main__":
    assembly_servos_above()

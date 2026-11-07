"""The current doser (servos below the hinge), recreated with text-to-cad.

Same parts as PR #170's full assembly, placed by the same transforms, but
every printed part is a build123d model here (scored against the Fusion
files in checks/results/fidelity/), the fasteners are step.parts models,
and the POWDER_DOSER_V2 electronics are included.

    PYTHONPATH=src:src/parts:src/purchased:src/electronics python3 src/assembly_current.py
"""
from __future__ import annotations

from cadgen import glb, step

from lib import doser
from lib.electronics_place import electronics

VARIANT = "below"
KINEMATICS = doser.kinematics(VARIANT)


@step(out="../STEP/assembly_current.step", kinematics=KINEMATICS)
@glb(out="../GLB/assembly_current.glb")
def assembly_current():
    return doser.build_doser(VARIANT, electronics=electronics(VARIANT))


if __name__ == "__main__":
    assembly_current()

"""Baseplate for the servos-above variant (issue #172); see baseplate.py."""
from __future__ import annotations

from cadgen import step, stl

from baseplate import make_baseplate


@step(out="../../STEP/parts/baseplate_servos_above.step")
@stl(out="../../STL/parts/baseplate_servos_above.stl")
def baseplate_servos_above():
    return make_baseplate("above")


if __name__ == "__main__":
    baseplate_servos_above()

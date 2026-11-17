"""Servo pinion: 14T spur pinion on an MG996R servo output.

Recreates components/fusion-step/servo-pinion.step (Fusion 360 SpurGear
add-in: module 1.298, 14 teeth, 20 deg, zero backlash) in its own frame: axis
+Z, faces at z = 0 and z = GEAR_WIDTH, tooth 0 on +X. Outside diameter
(14 + 2) x 1.298 = 20.768 mm; it meshes the mounting plate's 28T gears
(same module) at (14 + 28) x 1.298 / 2 = 27.258 mm centres.

Servo interface: the reference models no spline teeth. The MG996R's 25T
output spline (about 5.9 mm) goes into a plain 6.0 mm socket, 3.5 mm deep in
the z = GEAR_WIDTH face. The M3 horn screw passes through a 3.4 mm hole from
the z = 0 face, with its head in a 60 deg countersink.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step, stl

from lib.gears import spur_gear

GEAR_MODULE = 1.298
GEAR_TEETH = 14
GEAR_WIDTH = 12.3
SPLINE_SOCKET_D = 6.0            # MG996R output spline, plain bore
SPLINE_SOCKET_DEPTH = 3.5        # from the z = GEAR_WIDTH face
SCREW_HOLE_D = 3.4               # M3 horn screw clearance
HEAD_RECESS_D = 6.94             # countersink diameter at the z = 0 face
HEAD_RECESS_ANGLE = 60.0         # included
HEAD_RECESS_DEPTH = 1.77


def _bore() -> bd.Solid:
    """Revolved cutter for the socket, screw hole and countersink (runs 1 mm
    past both faces)."""
    t = math.tan(math.radians(HEAD_RECESS_ANGLE / 2))
    r_cs = HEAD_RECESS_D / 2
    z_sock = GEAR_WIDTH - SPLINE_SOCKET_DEPTH
    pts = [(0.0, -1.0), (r_cs + t, -1.0), (r_cs - HEAD_RECESS_DEPTH * t, HEAD_RECESS_DEPTH),
           (SCREW_HOLE_D / 2, HEAD_RECESS_DEPTH), (SCREW_HOLE_D / 2, z_sock),
           (SPLINE_SOCKET_D / 2, z_sock), (SPLINE_SOCKET_D / 2, GEAR_WIDTH + 1.0),
           (0.0, GEAR_WIDTH + 1.0)]
    face = bd.Face(bd.Wire.make_polygon([(r, 0.0, z) for r, z in pts], close=True))
    return bd.revolve(face, bd.Axis.Z).solids()[0]


@step(out="../../STEP/parts/servo_pinion.step")
@stl(out="../../STL/parts/servo_pinion.stl")
def servo_pinion():
    part = (spur_gear(GEAR_MODULE, GEAR_TEETH, GEAR_WIDTH) - _bore()).solids()[0]
    part.label = "servo_pinion"
    return part


if __name__ == "__main__":
    servo_pinion()

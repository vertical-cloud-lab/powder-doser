"""Printed holder that stands the POWDER_DOSER_V2 PCB upright on the 38.1 mm
wooden mounting board, components facing the doser (-Y).

Frame (shared with pcb_holder_assembly.py): z = 0 is the wooden board's top
surface (the holder's underside), x = 0 the holder's centre line, y = 0 the
holder's front face; the whole holder lies in y = 0..HOLDER_D.

Shape: a 5 mm base plate (front toe with a weight-saving window, rear deck
with three countersunk #10 wood-screw holes), a 4 mm upright that carries the
PCB on three M3 x 10 mm F-F hex standoffs (M3 x 8 button-head screws from
behind), and two 4 mm gussets behind the upright.

Printing: base down on the bed, no supports.  Upright and gussets are
vertical walls; the gusset hypotenuses face up (about 58 deg); the three
horizontal M3 holes are teardrops (45 deg roof); countersinks open upward.
All walls >= 4 mm.  PLA/PETG, 3 perimeters, 30 % infill.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import srgb, step, stl

from pcb_layout import BOARD_H, BOARD_W, MOUNT_HOLES, STANDOFF_L


HOLDER_W = 120.0          # base width (x = -60..60)
HOLDER_D = 70.0           # base depth (y = 0..70)
BASE_T = 5.0
UPRIGHT_Y = 36.0          # upright front face (standoff seat)
UPRIGHT_T = 4.0
UPRIGHT_W = 110.0
UPRIGHT_H = 84.0
PCB_Z0 = 12.0             # PCB lower edge above the wood
PCB_X0 = -BOARD_W / 2     # PCB left edge (board x = 0) in the holder frame
GUSSET_X = (-22.0, 22.0)
GUSSET_T = 4.0
GUSSET_TOP = 50.0
GUSSET_BACK = 68.0
WOOD_SCREWS = ((-45.0, 56.0), (0.0, 56.0), (45.0, 56.0))
M3_CLEAR = 3.4
NO10_CLEAR = 5.2
NO10_HEAD = 9.9           # 82 deg flat head
TOE_WINDOW = (-48.0, 6.0, 48.0, 30.0)   # x0, y0, x1, y1


def standoff_points() -> dict[str, tuple[float, float]]:
    """(x, z) of the three PCB mounting holes on the upright face."""
    return {k: (PCB_X0 + x, PCB_Z0 + y) for k, (x, y) in MOUNT_HOLES.items()}


def _teardrop_y(x: float, z: float, d: float, y0: float, y1: float) -> bd.Shape:
    """Horizontal hole along Y with a 45 deg roof (point towards +Z)."""
    r = d / 2
    length = y1 - y0
    circle = bd.Cylinder(r, length, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    roof = bd.Box(r, r, length, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).rotate(bd.Axis.Z, 45)
    roof = roof.moved(bd.Location((0, r / math.sqrt(2), 0)))   # apex at r*sqrt(2)
    tool = circle.fuse(roof).rotate(bd.Axis.X, 90)   # local +Z -> -Y, local +Y -> +Z
    return tool.moved(bd.Location((x, y1, z)))


def build_holder() -> bd.Shape:
    base = bd.Box(HOLDER_W, HOLDER_D, BASE_T, align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.MIN))
    x0, y0, x1, y1 = TOE_WINDOW
    window = bd.Box(x1 - x0, y1 - y0, BASE_T + 2, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN)).moved(
        bd.Location((x0, y0, -1)))
    window = bd.fillet(window.edges().filter_by(bd.Axis.Z), 4.0)
    base = base.cut(window)

    upright = bd.Box(UPRIGHT_W, UPRIGHT_T, UPRIGHT_H, align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.MIN)).moved(
        bd.Location((0, UPRIGHT_Y, 0)))
    gussets = []
    for gx in GUSSET_X:
        tri = bd.Polyline((UPRIGHT_Y + UPRIGHT_T - 0.5, BASE_T - 0.5),
                          (UPRIGHT_Y + UPRIGHT_T - 0.5, GUSSET_TOP),
                          (GUSSET_BACK, BASE_T - 0.5), close=True)
        face = bd.make_face(bd.Plane.YZ * tri)
        g = bd.extrude(face, amount=GUSSET_T / 2, both=True).moved(bd.Location((gx, 0, 0)))
        gussets.append(g)
    body = base.fuse(upright, *gussets).clean()

    tools = []
    for x, z in standoff_points().values():
        tools.append(_teardrop_y(x, z, M3_CLEAR, UPRIGHT_Y - 1, UPRIGHT_Y + UPRIGHT_T + 1))
    sink_depth = (NO10_HEAD - NO10_CLEAR) / 2 / math.tan(math.radians(41))
    for x, y in WOOD_SCREWS:
        tools.append(bd.Cylinder(NO10_CLEAR / 2, BASE_T + 2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).moved(
            bd.Location((x, y, -1))))
        cone = bd.Cone(NO10_CLEAR / 2, NO10_HEAD / 2 + 0.2, sink_depth + 0.2,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        tools.append(cone.moved(bd.Location((x, y, BASE_T - sink_depth))))
    body = body.cut(bd.Compound(tools))
    body.label = "pcb_holder"
    body.color = srgb("#E0A030")
    return body


@stl(out="../../STL/electronics/pcb_mount.stl")
@step(out="../../STEP/electronics/pcb_mount.step")
def pcb_mount():
    return build_holder()


if __name__ == "__main__":
    pcb_mount()

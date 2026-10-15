"""How close a dispense cup can come to the nozzle.

A cup of radius r, centred under the outlet hole, is raised from far below
until its rim touches something.  The rim can rise to the lowest point of
any solid inside the vertical cylinder of radius r through the outlet, so

    gap(r) = z_outlet - min over solids of  min z(solid & cylinder)

and the solid that sets it is the "limiting" part.  The mounting board
counts like any other solid, so a cup wider than the overhang in front of
the board's edge ends up below the board.

``clearance(parts, outlet, radii)`` takes ``{name: build123d Shape}``
already placed in the world frame (Z up) and returns, for every radius,
the gap and the limiting part.  The assemblies' own scripts call it for
each tilt; see checks/README.md.
"""
from __future__ import annotations

import math


def _cylinder(x: float, y: float, r: float, z0: float = -400.0, h: float = 800.0):
    from build123d import Cylinder, Location
    return Cylinder(r, h).moved(Location((x, y, z0 + h / 2)))


def _common_zmin(a, b) -> float | None:
    """Lowest z of a & b (OCC boolean + optimal bounding box), None if empty."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer

    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    if not op.IsDone():
        raise RuntimeError("boolean failed")
    res = op.Shape()
    if not TopExp_Explorer(res, TopAbs_SOLID).More():
        return None
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(res, box, False, False)
    return None if box.IsVoid() else box.CornerMin().Z()


def clearance(parts: dict, outlet: tuple[float, float, float],
              radii=(10.0, 15.0, 20.0, 25.0, 30.0, 40.0)) -> list[dict]:
    """parts: name -> placed Shape (world frame).  outlet: (x, y, z)."""
    ox, oy, oz = outlet
    rows = []
    for r in radii:
        cyl = _cylinder(ox, oy, r)
        cb = cyl.bounding_box()
        best = (math.inf, None)
        for name, shp in parts.items():
            bb = shp.bounding_box()
            if (bb.max.X < cb.min.X or bb.min.X > cb.max.X
                    or bb.max.Y < cb.min.Y or bb.min.Y > cb.max.Y):
                continue
            try:
                z = _common_zmin(shp, cyl)
            except RuntimeError:       # a failed boolean is reported, not skipped
                z = bb.min.Z
                name = name + " (bbox fallback)"
            if z is not None and z < best[0]:
                best = (z, name)
        rim, who = best
        rows.append({"cup_radius_mm": r,
                     "rim_max_z_mm": None if math.isinf(rim) else round(rim, 2),
                     "gap_mm": None if math.isinf(rim) else round(oz - rim, 2),
                     "limited_by": who})
    return rows

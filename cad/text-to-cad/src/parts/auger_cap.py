"""Auger cap: the screw-on cap closing the reservoir end of the auger tube.

Recreates components/fusion-step/auger-cap.step (Fusion 360 body "Cap") in
the frame it was exported in: axis +Z, inner face of the end wall at z = 0,
open rim at z = -CAP_DEPTH, top outside at z = +END_WALL.

The internal thread is the auger's external thread tooth (see auger.py) offset
outwards by THREAD_CLEARANCE normal to its flanks and swept as a groove into a
plain CAP_MINOR_D bore; it runs out through the rim and the inner end face.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step, stl

from auger import (THREAD_CREST_ROUND, THREAD_FLANK_SLOPE, THREAD_MAJOR_D,
                   THREAD_MINOR_D, THREAD_PITCH, THREAD_ROOT_WIDTH)

CAP_OD = 29.0
CAP_DEPTH = 25.0                 # inner end face to rim (= auger thread length)
END_WALL = 2.0                   # end wall thickness, z = 0 .. END_WALL
TOP_CHAMFER = 2.0                # 45 deg, the full end-wall height
CAP_MINOR_D = 23.5               # internal-thread crest (plain bore)
THREAD_CLEARANCE = 0.5           # groove = auger tooth offset by this, normal to the flanks
THREAD_PHASE_Z = -0.4            # groove centre on +X (mod pitch); right-handed


def _xz(points: list[tuple[float, float]]) -> bd.Face:
    return bd.Face(bd.Wire.make_polygon([(r, 0.0, z) for r, z in points], close=True))


def _groove_profile(z: float) -> bd.Face:
    """Auger tooth section grown by THREAD_CLEARANCE, centred at height z on +X."""
    r_root, c = THREAD_MINOR_D / 2, THREAD_CLEARANCE
    r_bottom = THREAD_MAJOR_D / 2 + c
    # half-width of the grown flank line at radius r
    grow = c * math.hypot(1.0, THREAD_FLANK_SLOPE)

    def half(r: float) -> float:
        return THREAD_ROOT_WIDTH / 2 - (r - r_root) * THREAD_FLANK_SLOPE + grow

    r_in = CAP_MINOR_D / 2 - 0.5                  # inside the bore: cuts through it
    prof = _xz([(r_in, z - half(r_in)), (r_bottom, z - half(r_bottom)),
                (r_bottom, z + half(r_bottom)), (r_in, z + half(r_in))])
    bottom = [v for v in prof.vertices() if abs(v.X - r_bottom) < 1e-9]
    return prof.fillet_2d(THREAD_CREST_ROUND + c, bottom)


def _cavity() -> bd.Solid:
    below = 1.0                                   # run the cut out through the rim
    bore = bd.Cylinder(CAP_MINOR_D / 2, CAP_DEPTH + below,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX))
    reach = THREAD_ROOT_WIDTH                     # > half the groove width
    k0 = math.floor((-CAP_DEPTH - below - reach - THREAD_PHASE_Z) / THREAD_PITCH)
    k1 = math.ceil((reach - THREAD_PHASE_Z) / THREAD_PITCH)
    z0 = THREAD_PHASE_Z + k0 * THREAD_PITCH
    turns = k1 - k0
    path = bd.Edge.make_helix(THREAD_PITCH, THREAD_PITCH * turns, 5.0, center=(0, 0, z0))
    coil = bd.sweep(_groove_profile(z0), path, is_frenet=True).solids()[0]
    groove = coil.intersect(bd.Cylinder(CAP_OD / 2, CAP_DEPTH + below,
                                        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX)))
    return bore.fuse(*groove.solids()).solids()[0]


def _shell() -> bd.Solid:
    r, t = CAP_OD / 2, TOP_CHAMFER
    return bd.revolve(_xz([(0.0, -CAP_DEPTH), (r, -CAP_DEPTH), (r, END_WALL - t),
                           (r - t, END_WALL), (0.0, END_WALL)]), bd.Axis.Z).solids()[0]


@step(out="../../STEP/parts/auger_cap.step")
@stl(out="../../STL/parts/auger_cap.stl")
def auger_cap():
    cap = _shell().cut(_cavity()).clean().solids()[0]
    cap.label = "auger_cap"
    return cap


if __name__ == "__main__":
    auger_cap()

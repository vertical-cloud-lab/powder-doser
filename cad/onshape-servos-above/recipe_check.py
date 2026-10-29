"""Check the by-hand recipe for the auger cap (README, "Building the cap's tree by hand") against fsgen's build.

    fsgen studio build parts/auger_cap.fs        # writes out/auger_cap/auger_cap.step (0 calls)
    python recipe_check.py                        # 0 calls

The recipe draws the thread groove the way a person would in Onshape: a trapezoid with numbered corners and two
1 mm sketch fillets, instead of the script's computed tangent points and arc midpoints. This builds the recipe
with build123d (same OpenCascade kernel as fsgen's local build) in the script's order and compares volume and
IoU with fsgen's build of parts/auger_cap.fs. Writes results/local/auger_cap_recipe.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import (Axis, Face, Helix, Plane, Polyline, Pos, Solid, Wire, fillet, import_step, make_face,
                       revolve, sweep)

HERE = Path(__file__).resolve().parent

# the script's variables (parts/auger_cap.fs)
CAP_D, CAP_DEPTH, END_WALL, CAP_MINOR_D = 29.0, 25.0, 2.0, 23.5
PITCH, MAJOR_D, MINOR_D, CLEARANCE, PHASE = 3.5, 26.0, 23.0, 0.5, -0.4
SINK = 0.5

# recipe numbers, as a person would enter them
Z_PLANE = PHASE - 8 * PITCH                        # thread plane and groove centre: -28.4 mm
R_IN = CAP_MINOR_D / 2 - SINK                      # inner side of the groove: 11.25 mm
R_OUT = MAJOR_D / 2 + CLEARANCE                    # groove bottom: 13.5 mm
H_IN = 1 + (MINOR_D / 2 - R_IN) / 6 + CLEARANCE * math.sqrt(1 + 1 / 36)   # half-width at R_IN: 1.548564 mm
H_OUT = H_IN - (R_OUT - R_IN) / 6                 # flanks rise 1 in 6: half-width at R_OUT before filleting
FILLET = 0.5 + CLEARANCE                          # 1 mm
CORNERS = {"A": (R_IN, Z_PLANE - H_IN), "B": (R_OUT, Z_PLANE - H_OUT),
           "C": (R_OUT, Z_PLANE + H_OUT), "D": (R_IN, Z_PLANE + H_IN)}


def front(points):
    """A closed outline on the Front plane: sketch (x, y) -> world (X, Z)."""
    return make_face(Polyline(*[(x, 0, z) for x, z in points], close=True))


def build() -> Solid:
    r = CAP_D / 2
    cap = revolve(front([(0, -CAP_DEPTH), (r, -CAP_DEPTH), (r, 0), (r - END_WALL, END_WALL), (0, END_WALL)]),
                  Axis.Z, 360)
    helix = Helix(pitch=PITCH, height=10 * PITCH, radius=CAP_MINOR_D / 2, center=(0, 0, Z_PLANE))
    trapezoid = front([CORNERS[k] for k in "ABCD"])
    outer = [v for v in trapezoid.vertices() if abs(v.X - R_OUT) < 1e-6]
    profile = fillet(outer, radius=FILLET)
    groove = sweep(profile, path=Wire([helix]), is_frenet=True)
    cap = cap - groove
    cap = cap + revolve(front([(0, 0), (r, 0), (r - END_WALL, END_WALL), (0, END_WALL)]), Axis.Z, 360)
    bore = Pos(0, 0, -CAP_DEPTH - 5) * Solid.make_cylinder(CAP_MINOR_D / 2, CAP_DEPTH + 5)
    return cap - bore


def main() -> None:
    rec = build()
    ref = import_step(HERE / "out" / "auger_cap" / "auger_cap.step")
    inter = (rec & ref).volume
    union = rec.volume + ref.volume - inter
    res = {"recipe_corners_mm": {k: [round(v, 4) for v in p] for k, p in CORNERS.items()},
           "fillet_mm": FILLET, "thread_plane_offset_below_top_mm": round(-Z_PLANE, 4),
           "recipe_volume_mm3": round(rec.volume, 2), "script_volume_mm3": round(ref.volume, 2),
           "iou": round(inter / union, 6), "solids": len(rec.solids())}
    out = HERE / "results" / "local" / "auger_cap_recipe.json"
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

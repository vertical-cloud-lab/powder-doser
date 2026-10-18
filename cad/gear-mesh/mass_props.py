"""Mass properties of the doser module (Sam's Oct 13 mounting plate + lab auger + cap)
about the hinge, from the CAD, for the mesh-preload analysis. Writes out/mass_props.json.

Frame: Sam's studio frame. Hinge axis = y through the origin, auger along +x from the
outlet (x = 0.4), plate underside at z = -18. Printed parts are PETG (1.27 g/cm^3);
the solid fraction is the share of the CAD volume that prints solid (0.2 mm layers,
3 perimeters, 40 % gyroid infill, as in cad/auger/slices/README.md): the auger's walls
and flights are all perimeter, the 5 mm plate is not.

    python mass_props.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "paternoster"))
from step_io import read_step_parts  # noqa: E402

REF = HERE.parent / "paternoster" / "reference"
RHO_PETG = 1.27e-3          # g/mm^3
SOLID = {"plate": 0.80, "auger": 1.00, "cap": 0.90, "carriage": 0.75}


def props(shape, M=None):
    """(volume mm^3, centroid, inertia tensor about the centroid per unit density) of a shape, optionally moved by 4x4 M."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from OCP.gp import gp_Trsf
    from OCP.TopLoc import TopLoc_Location
    w = shape.wrapped
    if M is not None:
        t = gp_Trsf()
        t.SetValues(*[float(M[i, j]) for i in range(3) for j in range(4)])
        w = w.Moved(TopLoc_Location(t))
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(w, g)
    c = g.CentreOfMass()
    I = g.MatrixOfInertia()
    J = np.array([[I.Value(i, j) for j in (1, 2, 3)] for i in (1, 2, 3)])
    return g.Mass(), np.array([c.X(), c.Y(), c.Z()]), J


def main() -> dict:
    sam = read_step_parts(REF / "sam-oct13-mounting-plate-and-carriage.step")
    aug = next(iter(read_step_parts(REF / "auger-threaded-storage.step").values()))
    cap = next(iter(read_step_parts(REF / "auger-cap-threaded.step").values()))
    A = np.array([[0, 0, 1, 0.4], [0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1.0]])     # auger STEP z -> Sam's +x
    C = A.copy()
    C[0, 3] += 250.0
    parts = {"plate": (sam["Mounting Plate"], None), "auger": (aug, A), "cap": (cap, C), "carriage": (sam["Carriage"], None)}
    out = {}
    for k, (s, M) in parts.items():
        v, c, J = props(s, M)
        rho = RHO_PETG * SOLID[k]
        m = v * rho                                     # g
        Jc = J * rho                                    # g mm^2 about the centroid (OCC returns it about the centroid per unit density)
        # about the hinge axis (y through the origin): parallel axis
        Iy_hinge = Jc[1, 1] + m * (c[0] ** 2 + c[2] ** 2)
        Ix_axis = Jc[0, 0] + m * (c[1] ** 2 + c[2] ** 2)  # about the auger axis (x through y = z = 0)
        out[k] = dict(volume_cm3=round(v / 1000, 3), solid_fraction=SOLID[k], mass_g=round(m, 2),
                      com_mm=[round(x, 2) for x in c], Iy_hinge_gmm2=round(Iy_hinge, 0), Ix_axis_gmm2=round(Ix_axis, 0))
    mod = ["plate", "auger", "cap"]
    m = sum(out[k]["mass_g"] for k in mod)
    com = sum(np.array(out[k]["com_mm"]) * out[k]["mass_g"] for k in mod) / m
    out["module_empty"] = dict(mass_g=round(m, 2), com_mm=[round(x, 2) for x in com],
                               Iy_hinge_gmm2=round(sum(out[k]["Iy_hinge_gmm2"] for k in mod), 0),
                               note="plate + auger + cap, no powder; the auger tube rotates in the plate's clamp rings")
    out["auger_rotating"] = dict(mass_g=round(out["auger"]["mass_g"] + out["cap"]["mass_g"], 2),
                                 Ix_axis_gmm2=round(out["auger"]["Ix_axis_gmm2"] + out["cap"]["Ix_axis_gmm2"], 0),
                                 note="auger + cap about the auger axis (the cap screws onto the tube and turns with it)")
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "mass_props.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main()

"""How closely a text-to-cad recreation matches the part it duplicates.

Both STEP files must be in the same frame (each recreated part is modelled in
the frame its Fusion 360 STEP was exported in), so no registration is done:
the numbers are the plain overlay.

    python3 checks/fidelity.py NEW.step REF.step [--name NAME]

Prints and saves (checks/results/fidelity/<name>.json):
  * volumes, intersection volume and IoU = V(new & ref) / V(new | ref)
  * bounding-box min/max deltas
  * surface deviation: points sampled on one surface, distance to the
    closest point of the other's tessellation (mean, 95th percentile, max;
    both ways; tessellation tolerance 0.02 mm)
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "fidelity"


def load(path: str):
    from build123d import Compound, import_step

    shape = import_step(path)
    solids = shape.solids()
    if not solids:
        raise SystemExit(f"{path}: no solids")
    if len(solids) == 1:
        return solids[0]
    # several bodies (the mounting plate's gears overlap its knuckles):
    # fuse them, so no volume is counted twice
    fused = solids[0].fuse(*solids[1:]).clean()
    return Compound(fused.solids())


NUDGE = (1.3e-3, 0.7e-3, 0.9e-3)   # mm; see common_volume


def common_volume(a, b, fuzzy: float = 0.0) -> float:
    """Volume of a & b.  A recreation shares many faces with its reference,
    and OCC's boolean returns nothing for exactly coincident faces, so ``a``
    is nudged by NUDGE (about 1.8 um) first.  That costs at most
    area x 1.8 um, under 0.1 % of the volume for these parts."""
    from build123d import Location
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from OCP.TopTools import TopTools_ListOfShape

    op = BRepAlgoAPI_Common()
    args, tools = TopTools_ListOfShape(), TopTools_ListOfShape()
    args.Append(a.moved(Location(NUDGE)).wrapped)
    tools.Append(b.wrapped)
    op.SetArguments(args)
    op.SetTools(tools)
    if fuzzy:
        op.SetFuzzyValue(fuzzy)
    op.SetRunParallel(True)
    op.Build()
    if not op.IsDone():
        return float("nan")
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(op.Shape(), props)
    return props.Mass()


def mesh_of(shape, tol: float = 0.02):
    import trimesh

    verts, tris = shape.tessellate(tol, 0.1)
    v = np.array([(p.X, p.Y, p.Z) for p in verts], float)
    return trimesh.Trimesh(v, np.array(tris, int), process=False)


def surface_distance(src, dst, n: int, seed: int = 0) -> np.ndarray:
    """Distances from n points sampled on src's surface to dst's surface
    (closest point on dst's triangles, not on its samples)."""
    import trimesh

    pts, _ = trimesh.sample.sample_surface(src, n, seed=seed)
    _, dist, _ = trimesh.proximity.closest_point(dst, pts)
    return np.asarray(dist)


def compare(new_path: str, ref_path: str, n: int = 20000) -> dict:
    t0 = time.time()
    new, ref = load(new_path), load(ref_path)
    v_new = sum(s.volume for s in new.solids())
    v_ref = sum(s.volume for s in ref.solids())
    v_int = 0.0   # solid by solid: OCC's boolean on two compounds drops solids
    for sa in new.solids():
        ba = sa.bounding_box()
        for sb in ref.solids():
            bb = sb.bounding_box()
            if all(lo1 <= hi2 and lo2 <= hi1 for lo1, hi1, lo2, hi2
                   in zip(ba.min, ba.max, bb.min, bb.max)):
                v_int += common_volume(sa, sb)
    iou = v_int / (v_new + v_ref - v_int)
    bn, br = new.bounding_box(), ref.bounding_box()
    mn, mr = mesh_of(new), mesh_of(ref)
    d_nr = surface_distance(mn, mr, n)           # new surface -> ref surface
    d_rn = surface_distance(mr, mn, n, seed=1)   # ref surface -> new surface
    stat = lambda d: {"mean": float(d.mean()), "p95": float(np.percentile(d, 95)),
                      "max": float(d.max())}
    return {
        "new": str(new_path), "ref": str(ref_path),
        "volume_new_mm3": round(v_new, 1), "volume_ref_mm3": round(v_ref, 1),
        "volume_intersection_mm3": round(v_int, 1),
        "volume_error_pct": round(100 * (v_new - v_ref) / v_ref, 2),
        "iou": round(iou, 4),
        "bbox_min_delta_mm": [round(a - b, 3) for a, b in zip(bn.min, br.min)],
        "bbox_max_delta_mm": [round(a - b, 3) for a, b in zip(bn.max, br.max)],
        "surface_dev_new_to_ref_mm": stat(d_nr),
        "surface_dev_ref_to_new_mm": stat(d_rn),
        "faces_new": len(new.faces()), "faces_ref": len(ref.faces()),
        "seconds": round(time.time() - t0, 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("new")
    ap.add_argument("ref")
    ap.add_argument("--name", default=None)
    ap.add_argument("-n", type=int, default=20000, help="surface samples per part")
    a = ap.parse_args()
    res = compare(a.new, a.ref, a.n)
    name = a.name or Path(a.new).stem
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

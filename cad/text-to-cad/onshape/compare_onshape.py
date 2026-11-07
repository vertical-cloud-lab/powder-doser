"""Check the Onshape edit against the geometry it should give (issue #172).

Reads the STEP that went to Onshape (doser_step.py) and the edited Part
Studio exported back (lower_table.py verify), explodes both into solids and
checks that

* the board did not move,
* every other solid moved by exactly (0, 0, -trim): matched by volume and
  centroid, compared by centroid and bounding box,
* the baseplate equals the original with its bottom ``trim`` mm cut off and
  moved down by ``trim`` (IoU from OCC booleans), i.e. the table is thinner
  and everything on it is lower.

Optionally (``--t2c``) also compares the Onshape baseplate with a
baseplate STEP from the text-to-cad edit.  Writes results/compare.json and
a section through the +X hinge tower (renders/onshape/section_x35.png).

    python3 onshape/compare_onshape.py --trim 3 [--t2c STEP/parts/baseplate_servos_above.step]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from OCP.Bnd import Bnd_Box
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Section
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepGProp import BRepGProp
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir, gp_Trsf, gp_Vec
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_EDGE, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_UniformDeflection
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopLoc import TopLoc_Location

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BEFORE = Path("/tmp/os/doser_servos_above.step")


def read(path: Path):
    r = STEPControl_Reader()
    if r.ReadFile(str(path)) != IFSelect_RetDone:
        raise RuntimeError(path)
    r.TransferRoots()
    return r.OneShape()


def solids(shape) -> list:
    out, ex = [], TopExp_Explorer(shape, TopAbs_SOLID)
    while ex.More():
        out.append(TopoDS.Solid_s(ex.Current()))
        ex.Next()
    return out


def props(s) -> dict:
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(s, g)
    c = g.CentreOfMass()
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(s, b, False, False)
    lo, hi = b.CornerMin(), b.CornerMax()
    return {"volume": g.Mass(), "centroid": np.array([c.X(), c.Y(), c.Z()]),
            "lo": np.array([lo.X(), lo.Y(), lo.Z()]), "hi": np.array([hi.X(), hi.Y(), hi.Z()])}


def moved(s, dz: float):
    t = gp_Trsf()
    t.SetTranslation(gp_Vec(0, 0, dz))
    return BRepBuilderAPI_Transform(s, t, True).Shape()


def volume(s) -> float:
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(s, g)
    return g.Mass()


def mesh_volume(s, tol: float = 0.01) -> float:
    """Volume of a fine triangulation.  OCC's surface integration is off by
    up to 8 % on the B-spline thread faces Onshape writes back (auger cap),
    while the meshes of the two agree to 0.06 %."""
    BRepMesh_IncrementalMesh(s, tol, False, 0.1, True)
    v, ex = 0.0, TopExp_Explorer(s, TopAbs_FACE)
    while ex.More():
        f, loc = TopoDS.Face_s(ex.Current()), TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f, loc)
        if tri is not None:
            T = loc.Transformation()
            P = np.array([[q.X(), q.Y(), q.Z()] for q in
                          (tri.Node(i).Transformed(T) for i in range(1, tri.NbNodes() + 1))])
            rev = f.Orientation() == TopAbs_REVERSED
            for k in range(1, tri.NbTriangles() + 1):
                i0, i1, i2 = tri.Triangle(k).Get()
                if rev:
                    i1, i2 = i2, i1
                v += np.dot(P[i0 - 1], np.cross(P[i1 - 1], P[i2 - 1])) / 6.0
        ex.Next()
    return v


def iou(a, b) -> float:
    inter = volume(BRepAlgoAPI_Common(a, b).Shape())
    union = volume(BRepAlgoAPI_Fuse(a, b).Shape())
    return inter / union if union > 0 else float("nan")


def expected_baseplate(base, trim: float):
    """The original baseplate with its bottom `trim` mm cut off, moved down by `trim`."""
    slab = BRepPrimAPI_MakeBox(gp_Pnt(-500, -500, -100), gp_Pnt(500, 500, trim)).Shape()
    return moved(BRepAlgoAPI_Cut(base, slab).Shape(), -trim)


def is_board(p) -> bool:
    return p["volume"] > 1.5e6                          # 250 x 220 x 38.1 mm


def is_baseplate(p) -> bool:
    return abs(p["lo"][0] + 95) < 0.01 and abs(p["hi"][0] - 95) < 0.01 and abs(p["hi"][1] - 170) < 0.01


def section_xy(shape, x: float) -> list[np.ndarray]:
    """Polylines (y, z) of the section of `shape` by the plane at this x."""
    sec = BRepAlgoAPI_Section(shape, gp_Pln(gp_Pnt(x, 0, 0), gp_Dir(1, 0, 0)))
    sec.Build()
    out, ex = [], TopExp_Explorer(sec.Shape(), TopAbs_EDGE)
    while ex.More():
        cu = BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current()))
        d = GCPnts_UniformDeflection(cu, 0.02)
        if d.IsDone() and d.NbPoints() > 1:
            pts = [d.Value(i) for i in range(1, d.NbPoints() + 1)]
            out.append(np.array([[p.Y(), p.Z()] for p in pts]))
        ex.Next()
    return out


def plot_section(before, after, trim: float, x: float, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
    for lines, kw in ((section_xy(before, x), dict(color="#9a9a9a", lw=0.9, ls="--")),
                      (section_xy(after, x), dict(color="#1f5fbf", lw=1.1))):
        for i, pl in enumerate(lines):
            ax.plot(pl[:, 0], pl[:, 1], **kw)
    ax.plot([], [], color="#9a9a9a", ls="--", label="as imported (table 6 mm)")
    ax.plot([], [], color="#1f5fbf", label=f"Onshape, #table_trim = {trim:g} mm (table {6 - trim:g} mm)")
    ax.set_xlim(15, 185)
    ax.set_ylim(-12, 92)
    ax.set_aspect("equal")
    ax.set_xlabel("y (mm, outlet end on the left)")
    ax.set_ylabel("z (mm, board top = 0)")
    ax.set_title(f"Section at x = {x:g} mm (+X hinge tower), exported back from Onshape")
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    ax.grid(alpha=0.25, lw=0.5)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    print("->", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trim", type=float, default=3.0)
    ap.add_argument("--after", type=Path, default=None)
    ap.add_argument("--t2c", type=Path, default=None, help="text-to-cad baseplate STEP to compare with")
    a = ap.parse_args()
    after_path = a.after or Path(f"/tmp/os/onshape_after_trim{a.trim:g}.step")
    before, after = read(BEFORE), read(after_path)
    sb, sa = solids(before), solids(after)
    pb, pa = [props(s) for s in sb], [props(s) for s in sa]
    res = {"trim_mm": a.trim, "solids_before": len(sb), "solids_after": len(sa)}

    # pair each original solid with the exported one it should have become
    used, worst_c, worst_box, worst_v, pairs = set(), 0.0, 0.0, 0.0, 0
    base_after = None
    for i, p in enumerate(pb):
        dz = 0.0 if is_board(p) else -a.trim
        if is_baseplate(p):
            j = next(j for j, q in enumerate(pa) if is_baseplate(q))
            base_after, base_before = sa[j], sb[i]
            used.add(j)
            continue
        want = p["centroid"] + [0, 0, dz]
        j = min((j for j in range(len(pa)) if j not in used),
                key=lambda j: np.linalg.norm(pa[j]["centroid"] - want)
                + abs(pa[j]["volume"] - p["volume"]) / max(p["volume"], 1e-9))
        used.add(j)
        q = pa[j]
        worst_c = max(worst_c, float(np.linalg.norm(q["centroid"] - want)))
        worst_box = max(worst_box, float(np.abs(q["lo"] - p["lo"] - [0, 0, dz]).max()),
                        float(np.abs(q["hi"] - p["hi"] - [0, 0, dz]).max()))
        dv = abs(q["volume"] - p["volume"]) / p["volume"]
        if dv > 1e-3:                       # integration error on B-splines? check on meshes
            dv = abs(mesh_volume(sa[j]) - mesh_volume(sb[i])) / p["volume"]
        worst_v = max(worst_v, dv)
        pairs += 1
    res["other_solids"] = {"pairs": pairs, "max_centroid_error_mm": worst_c,
                           "max_bbox_error_mm": worst_box, "max_volume_error_rel": worst_v,
                           "note": "volumes from OCC integration, or from fine meshes where those differ by > 0.1 %"}

    exp = expected_baseplate(base_before, a.trim)
    pe, po = props(exp), props(base_after)
    res["baseplate"] = {
        "volume_before_mm3": volume(base_before), "volume_expected_mm3": pe["volume"],
        "volume_onshape_mm3": po["volume"],
        "bbox_onshape_mm": [po["lo"].round(4).tolist(), po["hi"].round(4).tolist()],
        "bbox_expected_mm": [pe["lo"].round(4).tolist(), pe["hi"].round(4).tolist()],
        "iou_vs_expected": iou(base_after, exp)}
    if a.t2c:
        t = solids(read(a.t2c))[0]
        pt = props(t)
        res["baseplate"]["text_to_cad"] = {
            "file": str(a.t2c), "volume_mm3": pt["volume"],
            "bbox_mm": [pt["lo"].round(4).tolist(), pt["hi"].round(4).tolist()],
            "iou_vs_onshape": iou(base_after, t)}
    print(json.dumps(res, indent=1))
    (HERE / "results" / f"compare_trim{a.trim:g}.json").write_text(json.dumps(res, indent=1) + "\n")
    plot_section(before, after, a.trim, 35.0, ROOT / "renders" / "onshape" / f"section_x35_trim{a.trim:g}.png")


if __name__ == "__main__":
    main()

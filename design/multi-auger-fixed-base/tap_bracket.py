"""Import #203's tap collar bracket from Onshape into the unit frame (issue #204).

    ONSHAPE_ACCESS_KEY=... ONSHAPE_SECRET_KEY=... python tap_bracket.py

Ethan's Onshape document "Doser with new solenoid setup" (#203) holds the
bracket (part studio "Solenoid bracket") and a full doser assembly with it in
place of the front Flexible Bracket ("Assembly new solenoid setup").  This
script exports that assembly as STEP, fits Ethan's mounting plate onto PR
#170's (ICP on surface samples), checks the fit on the parts both
assemblies share (auger, rear bracket, cap, stepper), and writes the bracket
and its solenoid (Adafruit 412 yoke, coil and plunger) in PR #170's world
frame at tilt 0 to ``tap-bracket/tap-bracket-pr170.step``.  doserlib reads
that file, so the concepts don't need the Onshape keys.

``tap-bracket/solenoid-bracket-onshape.step`` is the bracket on its own, as
Onshape exports it (its part studio's frame).
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUTDIR = HERE / "tap-bracket"
API = "https://cad.onshape.com/api/v6"
DID, WID = "3db901b123bbee05f5c196f3", "71800ea0548acad53e21d816"     # "Doser with new solenoid setup"
EL_ASSEMBLY = "75a706585a5f944cebeab4c6"                               # "Assembly new solenoid setup"
EL_BRACKET = "68af1a083e7d90e44c40f87c"                                # "Solenoid bracket"
CACHE = Path(os.environ.get("ONSHAPE_CACHE", Path.home() / ".cache" / "powder-doser-onshape"))

# Ethan's assembly names every Onshape part "Part 1", so its parts are told
# apart by volume (mm^3, rounded), checked against the instance list.
BY_VOLUME = {91686: "mounting plate", 27432: "tap bracket", 10766: "Flexible Bracket (rear)",
             53761: "auger", 150817: "baseplate"}
SOLENOID = ("solenoid_coil", "solenoid_yoke", "solenoid_plunger")


# --------------------------------------------------------------------------- #
# Onshape export
# --------------------------------------------------------------------------- #
def _export(kind: str, eid: str, dst: Path) -> dict:
    import requests
    auth = (os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
    js = {"Accept": "application/json"}
    r = requests.post(f"{API}/{kind}/d/{DID}/w/{WID}/e/{eid}/translations", auth=auth, headers=js,
                      json={"formatName": "STEP", "storeInDocument": False, "flattenAssemblies": False,
                            "yAxisIsUp": False}, timeout=120)
    r.raise_for_status()
    tid = r.json()["id"]
    for _ in range(100):
        t = requests.get(f"{API}/translations/{tid}", auth=auth, headers=js, timeout=60).json()
        if t["requestState"] != "ACTIVE":
            break
        time.sleep(3)
    if t["requestState"] != "DONE":
        raise RuntimeError(f"Onshape translation {t['requestState']}: {t.get('failureReason')}")
    d = requests.get(f"{API}/documents/d/{DID}/externaldata/{t['resultExternalDataIds'][0]}", auth=auth, timeout=300)
    d.raise_for_status()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(d.content)
    mv = requests.get(f"{API}/documents/d/{DID}/w/{WID}/currentmicroversion", auth=auth, headers=js, timeout=60).json()
    return {"element": eid, "microversion": mv.get("microversion"), "bytes": len(d.content)}


# --------------------------------------------------------------------------- #
# STEP reading with names and placements
# --------------------------------------------------------------------------- #
def read_named_solids(path: Path) -> list[tuple[str, object]]:
    """(leaf name, cq.Shape in the file's root frame) for every leaf of a STEP assembly."""
    import cadquery as cq
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDF import TDF_Label, TDF_LabelSequence
    from OCP.TDocStd import TDocStd_Document
    from OCP.TopLoc import TopLoc_Location
    from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool

    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    rd = STEPCAFControl_Reader()
    rd.SetNameMode(True)
    if rd.ReadFile(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"can't read {path}")
    rd.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def name(lab):
        n = TDataStd_Name()
        return n.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), n) else "?"

    out = []

    def walk(lab, loc):
        if XCAFDoc_ShapeTool.IsReference_s(lab):
            ref = TDF_Label()
            XCAFDoc_ShapeTool.GetReferredShape_s(lab, ref)
            walk(ref, loc.Multiplied(XCAFDoc_ShapeTool.GetLocation_s(lab)))
        elif XCAFDoc_ShapeTool.IsAssembly_s(lab):
            comps = TDF_LabelSequence()
            XCAFDoc_ShapeTool.GetComponents_s(lab, comps)
            for i in range(1, comps.Length() + 1):
                walk(comps.Value(i), loc)
        else:
            out.append((name(lab), cq.Shape.cast(XCAFDoc_ShapeTool.GetShape_s(lab).Moved(loc))))

    roots = TDF_LabelSequence()
    st.GetFreeShapes(roots)
    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i), TopLoc_Location())
    return out


# --------------------------------------------------------------------------- #
# registration onto PR #170
# --------------------------------------------------------------------------- #
def _mesh(shape, tol=0.2):
    import trimesh
    v, f = shape.tessellate(tol, 0.3)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=False)


def fit(src_pts: np.ndarray, dst_pts: np.ndarray, iters=40):
    """Rigid fit of src onto dst: ICP from every PCA-axis start, best median kept."""
    import trimesh
    from scipy.spatial import cKDTree
    tree = cKDTree(dst_pts)

    def pca(x):
        c = x.mean(0)
        return c, np.linalg.svd(x - c, full_matrices=False)[2]

    ca, va = pca(src_pts)
    cb, vb = pca(dst_pts)
    best = None
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            R = vb.T @ np.array([signs[i] * va[perm[i]] for i in range(3)])
            if np.linalg.det(R) < 0:
                continue
            T = np.eye(4)
            T[:3, :3], T[:3, 3] = R, cb - R @ ca
            for _ in range(iters):
                d, j = tree.query(src_pts @ T[:3, :3].T + T[:3, 3])
                keep = d < max(np.percentile(d, 90), 0.5)
                T = trimesh.registration.procrustes(src_pts[keep], dst_pts[j[keep]], reflection=False, scale=False,
                                                    return_cost=False)
            d, _ = tree.query(src_pts @ T[:3, :3].T + T[:3, 3])
            if best is None or np.median(d) < best[0]:
                best = (float(np.median(d)), float(np.percentile(d, 95)), T)
    return best


def surface_gap(a_mesh, b_mesh, n=20000):
    from scipy.spatial import cKDTree
    d, _ = cKDTree(b_mesh.sample(3 * n)).query(a_mesh.sample(n))
    return round(float(np.median(d)), 2), round(float(np.percentile(d, 95)), 2)


def main():
    import cadquery as cq
    sys.path.insert(0, str(HERE))
    import doserlib as D

    info = {"document": f"https://cad.onshape.com/documents/{DID}/w/{WID}", "exports": {}}
    asm = CACHE / "assembly_new_solenoid_setup.step"
    info["exports"]["assembly"] = _export("assemblies", EL_ASSEMBLY, asm)
    OUTDIR.mkdir(exist_ok=True)
    info["exports"]["bracket"] = _export("partstudios", EL_BRACKET, OUTDIR / "solenoid-bracket-onshape.step")
    print("exported", json.dumps(info["exports"]))

    parts = {}
    for n, s in read_named_solids(asm):
        key = BY_VOLUME.get(round(s.Volume()), n if n in SOLENOID + ("auger_cap", "stepper_motor") else None)
        if key:
            parts[key] = s
    missing = set(BY_VOLUME.values()) - set(parts) | set(SOLENOID) - set(parts)
    if missing:
        raise RuntimeError(f"not found in the assembly: {sorted(missing)}")

    pl = D.L.placements(0.0, roll_deg=D.L.COLLAR_ROLL_DEG)

    def pr170(name):
        rel, M = pl[name]
        sh = (cq.importers.importStep(str(D.L.COMP / rel)).vals()[0] if name == "Mounting plate"
              else D.step_shape(rel))
        m = _mesh(sh)
        m.apply_transform(M)
        return m

    mp_e, mp_p = _mesh(parts["mounting plate"]), pr170("Mounting plate")
    med, p95, T = fit(mp_e.sample(20000), mp_p.sample(60000))
    info["ethan_to_pr170_world"] = np.round(T, 6).tolist()
    info["fit_mounting_plate_mm"] = {"median": round(med, 2), "p95": round(p95, 2)}
    checks = {}
    for ek, pn in [("auger", "Auger"), ("Flexible Bracket (rear)", "Bracket (rear)"), ("auger_cap", "Auger cap"),
                   ("stepper_motor", "Stepper (NEMA 11)"), ("tap bracket", "Bracket (front)")]:
        m = _mesh(parts[ek])
        m.apply_transform(T)
        checks[f"{ek} -> PR170 {pn}"] = dict(zip(("median", "p95"), surface_gap(m, pr170(pn))))
    info["fit_checks_mm"] = checks
    print(json.dumps(info, indent=1))

    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*T[0, :4], *T[1, :4], *T[2, :4])
    loc = cq.Location(tr)
    assy = cq.Assembly(name="tap_bracket_pr170_world_tilt0")
    out = {}
    for key in ("tap bracket",) + SOLENOID:
        s = parts[key].moved(loc)
        out[key] = s
        bb = s.BoundingBox()
        info.setdefault("pr170_world_bounds", {})[key] = [round(v, 1) for v in
                                                         (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)]
        assy.add(s, name=key.replace(" ", "_"))
    assy.save(str(OUTDIR / "tap-bracket-pr170.step"))
    (OUTDIR / "registration.json").write_text(json.dumps(info, indent=1) + "\n")
    print("wrote", OUTDIR / "tap-bracket-pr170.step")


if __name__ == "__main__":
    main()

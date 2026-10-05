"""The text-to-cad session's version of the lowering, made in Onshape (issue #172).

That session lowers the hinge instead of thinning the table: the towers and
the servo cradles get shorter by ``drop``, the tilting system and the servos
sit ``drop`` lower, and the table is pocketed under the mounting plate,
whose floor is only 2.0 mm above it at rest (the bracket screw heads are
0.35 mm above it).  Tilting only raises those parts, so the rest pose sets
the limit.

This runs in a branch of the same Onshape document, started from the
"text-to-cad import" version, so the two edits sit side by side:

1. ``hinge_drop``                Variable, 5 mm
2. ``Lower the tilting system``  Transform (0, 0, -#hinge_drop) of everything
                                 but the board, the baseplate and the four
                                 #10 screws that hold the baseplate down
3. ``Lower hinge, relieve table`` the custom feature in
                                 ``featurescript/lower_hinge.fs``: splits the
                                 baseplate at z = 20 mm, moves everything above
                                 down by #hinge_drop and merges it back
                                 (shorter towers and cradles), then pockets
                                 the table under the mounting plate (its
                                 outline at the table + 1 mm, down to 0.5 mm
                                 under the lowered floor) and opens Ø7 holes
                                 under the four bracket screw heads

    python3 onshape/lower_hinge.py fs         # write featurescript/lower_hinge.fs
    python3 onshape/lower_hinge.py branch     # branch + Feature Studio + features
    python3 onshape/lower_hinge.py verify     # views, boxes, STEP back, version
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

import numpy as np

import lower_table as lt
from onshape_client import HERE, Onshape

FS_FILE = HERE / "featurescript" / "lower_hinge.fs"
BRANCH = "hinge 5 mm lower (text-to-cad approach)"
FS_VERSION = 3083                  # the std library version the Part Studio reported
SPLIT_Z = 20.0
BOARD_SCREWS = {"board_screw_neg_y155", "board_screw_neg_y155_1", "board_screw_neg_y155_2",
                "board_screw_neg_y155_3"}


def footprint() -> np.ndarray:
    """The mounting plate's outline where it would sink into the table
    (sections at z = 8.2, 9.8 and 11.4 mm at rest, unioned), + 1 mm."""
    import sys
    sys.path.insert(0, str(HERE))
    from compare_onshape import BEFORE, props, read, solids
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from OCP.GCPnts import GCPnts_UniformDeflection
    from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
    from shapely.geometry import LineString, Polygon
    from shapely.ops import polygonize, unary_union

    sb = solids(read(BEFORE))
    mp = next(s for s in sb if abs(props(s)["lo"][2] - 8.0) < 0.01 and props(s)["hi"][0] > 54)

    def section(z):
        s = BRepAlgoAPI_Section(mp, gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1)))
        s.Build()
        out, ex = [], TopExp_Explorer(s.Shape(), TopAbs_EDGE)
        while ex.More():
            d = GCPnts_UniformDeflection(BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())), 0.05)
            out.append(LineString([(round(d.Value(i).X(), 4), round(d.Value(i).Y(), 4))
                                   for i in range(1, d.NbPoints() + 1)]))
            ex.Next()
        return Polygon(max(polygonize(unary_union(out)), key=lambda p: p.area).exterior)

    fp = unary_union([section(z) for z in (8.2, 9.8, 11.4)])
    fp = fp.buffer(1.0, join_style=2, mitre_limit=2.0)
    # keep the table under the tower feet (x 28.9-41.2, y 55.4-81.77): the
    # plate's notches clear the towers by only 0.3 mm, so +1 mm would undercut them
    from shapely.geometry import box
    for x0, x1 in ((28.9, 41.2), (-41.2, -28.9)):
        fp = fp.difference(box(x0, 55.4, x1, 81.77))
    fp = fp.simplify(0.05)
    assert fp.geom_type == "Polygon" and fp.is_valid, fp.geom_type
    return np.array(fp.exterior.coords)


def write_fs() -> None:
    pts = footprint()
    pts_fs = ",\n    ".join(f"vector({x:.3f}, {y:.3f}) * millimeter" for x, y in pts)
    FS_FILE.parent.mkdir(exist_ok=True)
    FS_FILE.write_text(f"""FeatureScript {FS_VERSION};
import(path : "onshape/std/geometry.fs", version : "{FS_VERSION}.0");

// Powder doser, servos above (vertical-cloud-lab/powder-doser #172).
// Lowers the baseplate's hinge towers and servo cradles by `drop` (every
// piece above `splitHeight` moves down and is merged back), then pockets the
// table under the mounting plate so its floor clears the table by
// `clearance` once the tilting system is `drop` lower, and opens holes under
// the four bracket screw heads.  Written by cad/text-to-cad/onshape/lower_hinge.py.

// the mounting plate's outline where it would sink into the table, + 1 mm
const MP_OUTLINE = [
    {pts_fs}
];
const SCREW_HEADS_MM = [[24.0, 103.73], [-24.0, 103.73], [24.0, 169.4], [-24.0, 169.4]];
const SCREW_HEAD_HOLE_R = 3.5 * millimeter;     // heads are 5.7 mm across
const TABLE_TOP = 6 * millimeter;
const MP_BOTTOM_AT_REST = 8 * millimeter;
const SCREW_HEADS_AT_REST = 6.35 * millimeter;

function sketchPlaneOnTable() returns Plane
{{
    return plane(vector(0, 0, 1) * TABLE_TOP, vector(0, 0, 1), vector(1, 0, 0));
}}

annotation {{ "Feature Type Name" : "Lower hinge, relieve table" }}
export const lowerHinge = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {{
        annotation {{ "Name" : "Baseplate", "Filter" : EntityType.BODY && BodyType.SOLID, "MaxNumberOfPicks" : 1 }}
        definition.baseplate is Query;

        annotation {{ "Name" : "Drop" }}
        isLength(definition.drop, {{ (millimeter) : [0, 5, 6.3] }} as LengthBoundSpec);

        annotation {{ "Name" : "Split height" }}
        isLength(definition.splitHeight, {{ (millimeter) : [12.5, 20, 30] }} as LengthBoundSpec);

        annotation {{ "Name" : "Clearance" }}
        isLength(definition.clearance, {{ (millimeter) : [0, 0.5, 2] }} as LengthBoundSpec);
    }}
    {{
        const drop = definition.drop;
        if (drop < 1e-6 * millimeter)
            return;

        // 1. shorter towers and cradles: split, move the tops down, merge
        opPlane(context, id + "splitPlane", {{ "plane" : plane(vector(0, 0, 1) * definition.splitHeight, vector(0, 0, 1), vector(1, 0, 0)) }});
        opSplitPart(context, id + "split", {{ "targets" : definition.baseplate,
                    "tool" : qCreatedBy(id + "splitPlane", EntityType.FACE), "keepTools" : false }});
        const pieces = qUnion([definition.baseplate, qCreatedBy(id + "split", EntityType.BODY)]);
        var tops = [];
        for (var body in evaluateQuery(context, pieces))
        {{
            if (evBox3d(context, {{ "topology" : body, "tight" : true }}).minCorner[2] > definition.splitHeight - 1e-4 * millimeter)
                tops = append(tops, body);
        }}
        opTransform(context, id + "down", {{ "bodies" : qUnion(tops), "transform" : transform(vector(0, 0, -1) * drop) }});
        opBoolean(context, id + "merge", {{ "tools" : pieces, "operationType" : BooleanOperationType.UNION }});
        if (size(evaluateQuery(context, qCreatedBy(id + "splitPlane"))) > 0)
            opDeleteBodies(context, id + "deletePlane", {{ "entities" : qCreatedBy(id + "splitPlane") }});
        const base = qUnion([definition.baseplate, qCreatedBy(id + "merge", EntityType.BODY)]);

        // 2. pocket under the mounting plate
        const floorZ = MP_BOTTOM_AT_REST - drop - definition.clearance;
        if (floorZ < TABLE_TOP)
        {{
            const sk = newSketchOnPlane(context, id + "pocketSketch", {{ "sketchPlane" : sketchPlaneOnTable() }});
            skPolyline(sk, "outline", {{ "points" : MP_OUTLINE }});
            skSolve(sk);
            opExtrude(context, id + "pocketTool", {{ "entities" : qSketchRegion(id + "pocketSketch"),
                      "direction" : vector(0, 0, -1), "endBound" : BoundingType.BLIND, "endDepth" : TABLE_TOP - floorZ }});
            opBoolean(context, id + "pocket", {{ "tools" : qCreatedBy(id + "pocketTool", EntityType.BODY),
                      "targets" : base, "operationType" : BooleanOperationType.SUBTRACTION }});
            opDeleteBodies(context, id + "deletePocketSketch", {{ "entities" : qCreatedBy(id + "pocketSketch") }});
        }}

        // 3. holes under the bracket screw heads, through the table
        if (SCREW_HEADS_AT_REST - drop - definition.clearance < max(floorZ, 0 * millimeter))
        {{
            const sk = newSketchOnPlane(context, id + "headSketch", {{ "sketchPlane" : sketchPlaneOnTable() }});
            for (var i = 0; i < size(SCREW_HEADS_MM); i += 1)
                skCircle(sk, "head" ~ i, {{ "center" : vector(SCREW_HEADS_MM[i][0], SCREW_HEADS_MM[i][1]) * millimeter,
                         "radius" : SCREW_HEAD_HOLE_R }});
            skSolve(sk);
            opExtrude(context, id + "headTool", {{ "entities" : qSketchRegion(id + "headSketch"),
                      "direction" : vector(0, 0, -1), "endBound" : BoundingType.BLIND, "endDepth" : TABLE_TOP + 1 * millimeter }});
            opBoolean(context, id + "heads", {{ "tools" : qCreatedBy(id + "headTool", EntityType.BODY),
                      "targets" : base, "operationType" : BooleanOperationType.SUBTRACTION }});
            opDeleteBodies(context, id + "deleteHeadSketch", {{ "entities" : qCreatedBy(id + "headSketch") }});
        }}
    }});
""")
    print("->", FS_FILE, len(pts), "outline points")


def ps_ws(rec: dict, wid: str) -> str:
    return f"/partstudios/d/{rec['documentId']}/w/{wid}/e/{rec['partStudio']['elementId']}"


def cmd_branch(c: Onshape, rec: dict, drop: float) -> None:
    br = rec.setdefault("branches", {}).setdefault(BRANCH, {})
    did = rec["documentId"]
    if "workspaceId" not in br:
        v0 = rec["versions"][0]
        ws = c.post(f"/documents/d/{did}/workspaces", json={
            "name": BRANCH, "versionId": v0["id"], "documentId": did,
            "description": f"The text-to-cad session's lowering (towers and cradles {drop:g} mm shorter, "
                           "table pocketed under the mounting plate), from the 'text-to-cad import' version"})
        br.update(workspaceId=ws["id"], fromVersion=v0["name"])
        lt.save(rec)
        print("branch workspace:", ws["id"])
    wid = br["workspaceId"]
    if "featureStudio" not in br:
        fs = c.post(f"/featurestudios/d/{did}/w/{wid}", json={"name": "Doser edits (#172)"})
        br["featureStudio"] = {"elementId": fs["id"]}
        lt.save(rec)
    fsid = br["featureStudio"]["elementId"]
    sha = hashlib.sha256(FS_FILE.read_bytes()).hexdigest()
    if br["featureStudio"].get("sha256") != sha:
        out = c.post(f"/featurestudios/d/{did}/w/{wid}/e/{fsid}",
                     json={"btType": "BTFeatureStudioContents-2239", "contents": FS_FILE.read_text(),
                           "serializationVersion": "1.2.21", "rejectMicroversionSkew": False})
        notices = [n for n in out.get("notices", []) if n.get("level") in ("ERROR", "WARNING")]
        (HERE / "results" / "featurestudio_notices.json").write_text(json.dumps(out.get("notices", []), indent=1) + "\n")
        if any(n.get("level") == "ERROR" for n in notices):
            raise RuntimeError(json.dumps(notices, indent=1)[:3000])
        br["featureStudio"]["sha256"] = sha
        br["featureStudio"].pop("microversion", None)       # read it from the elements list
        lt.save(rec)
    feats = br.setdefault("features", {})
    path = ps_ws(rec, wid)

    def add(feature):
        res = c.post(f"{path}/features", json={"feature": feature})
        st = res.get("featureState", {}).get("featureStatus")
        feats[feature["name"]] = {"featureId": res["feature"]["featureId"], "status": st}
        lt.save(rec)
        print(feature["name"], st)
        if st not in ("OK", "INFO"):
            raise RuntimeError(f"{feature['name']}: {res.get('featureState')}")

    if "hinge_drop" not in feats:
        f = lt.variable_feature(drop)
        f["name"] = "hinge_drop"
        f["parameters"][2] = lt.p_str("name", "hinge_drop")
        f["parameters"][3] = lt.p_qty("lengthValue", f"{drop:g} mm")
        f["parameters"][4] = lt.p_str("description", "how much lower the hinge, the tilting system and the servos sit")
        add(f)
    if "Lower the tilting system" not in feats:
        movers = [b["id"] for b in rec["bodies"]
                  if b["name"] not in {"board", "baseplate"} | BOARD_SCREWS]
        assert len(movers) == len(rec["bodies"]) - 6, len(movers)
        add({"btType": "BTMFeature-134", "featureType": "transform", "name": "Lower the tilting system",
             "parameters": [lt.q_ids("entities", movers),
                            lt.p_enum("transformType", "TransformType", "TRANSLATION_3D"),
                            lt.p_qty("dx", "0 mm"), lt.p_qty("dy", "0 mm"), lt.p_qty("dz", "-#hinge_drop"),
                            lt.p_bool("makeCopy", False)]})
    if "Lower hinge, relieve table" not in feats:
        mv = br["featureStudio"].get("microversion")
        if not mv:
            mv = next(e["microversionId"] for e in c.get(f"/documents/d/{did}/w/{wid}/elements")
                      if e["id"] == fsid)
            br["featureStudio"]["microversion"] = mv
        add({"btType": "BTMFeature-134", "featureType": "lowerHinge", "name": "Lower hinge, relieve table",
             "namespace": f"e{fsid}::m{mv}",
             "parameters": [lt.q_ids("baseplate", [rec["baseplate"]["partId"]]),
                            lt.p_qty("drop", "#hinge_drop"), lt.p_qty("splitHeight", f"{SPLIT_Z:g} mm"),
                            lt.p_qty("clearance", "0.5 mm")]})
    br["hinge_drop_mm"] = drop
    lt.save(rec)


def cmd_verify(c: Onshape, rec: dict) -> None:
    br = rec["branches"][BRANCH]
    wid, did = br["workspaceId"], rec["documentId"]
    path, drop = ps_ws(rec, wid), br["hinge_drop_mm"]
    # the split and merge give the baseplate a new part id: look it up by name
    parts = c.get(f"/parts/d/{did}/w/{wid}/e/{rec['partStudio']['elementId']}")
    br["baseplate"] = [{"partId": p["partId"], "name": p["name"]} for p in parts if "baseplate" in p["name"]]
    box = c.get(f"{path}/boundingboxes")
    (lt.RESULTS / "hinge_bbox_after.json").write_text(json.dumps(box, indent=1) + "\n")
    for view, tag in (("isometric", "iso"), ("right", "right")):
        r = c.get(f"{path}/shadedviews", params={"viewMatrix": view, "outputHeight": 900, "outputWidth": 1400,
                                                  "pixelSize": 0, "edges": "show", "useAntiAliasing": "true"})
        out = lt.RENDERS / f"onshape_hinge_{tag}.png"
        out.write_bytes(base64.b64decode(r["images"][0]))
        print("->", out)
    tr = c.post(f"{path}/translations", json={"formatName": "STEP", "storeInDocument": False,
                                              "stepVersionString": "AP242", "flattenAssemblies": True})
    st = lt.wait_translation(c, tr["id"], first=20, every=15, polls=10)
    r = c.get(f"/documents/d/{did}/externaldata/{st['resultExternalDataIds'][0]}", raw=True,
              headers={"Accept": "application/octet-stream"})
    out = Path(f"/tmp/os/onshape_hinge_drop{drop:g}.step")
    out.write_bytes(r.content)
    v = c.post(f"/documents/d/{did}/versions", json={
        "documentId": did, "workspaceId": wid, "name": f"hinge {drop:g} mm lower",
        "description": f"#hinge_drop = {drop:g} mm: towers and cradles shorter, tilting system and servos "
                       f"lower, table pocketed under the mounting plate"})
    br.setdefault("versions", []).append({"id": v["id"], "name": f"hinge {drop:g} mm lower"})
    br["export"] = str(out)
    lt.save(rec)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["fs", "branch", "verify"])
    ap.add_argument("--drop", type=float, default=5.0)
    ap.add_argument("--budget", type=int, default=12)
    a = ap.parse_args()
    if a.step == "fs":
        write_fs()
        return
    c, rec = Onshape(budget=a.budget, run=f"hinge-{a.step}"), lt.load()
    try:
        {"branch": lambda: cmd_branch(c, rec, a.drop), "verify": lambda: cmd_verify(c, rec)}[a.step]()
    finally:
        rec.setdefault("api_calls", {})
        key = f"hinge-{a.step}"
        rec["api_calls"][key] = rec["api_calls"].get(key, 0) + c.calls
        lt.save(rec)
        print(f"{key}: {c.calls} API calls")


if __name__ == "__main__":
    main()

"""Build one tri-star leg unit (leg_unit.py) as a native Onshape Part Studio through the REST API (issue #204, 24 Nov).

Ethan asked for one of the telescoping tripod leg units, with the actuator mount for the lever + lean layout
(L4), in Onshape.  This script makes a new document in the account the API key belongs to and builds the
three made parts of one leg from sketches, planes and extrudes, so every size can be edited afterwards:

  * Leg head (printed): arm, window, base screw holes and nut traps, sleeve and its bore, the M5 height-pin
    hole, the tab with the U-bracket's pocket, its M3 hole and nut trap;
  * Leg tube (20 x 20 x 1.5 mm aluminium): its bore and the ten height-pin holes, set at the 340 mm height;
  * Leg foot (printed): pad and socket, with the cross hole it shares with the tube.

It then reads the parts back (volumes, bounding box, an STL export) and checks them against leg_unit.py's,
and saves two shaded views.  It writes leg-unit/onshape.json and leg-unit/leg_unit_onshape.stl.

    pip install requests cadquery trimesh manifold3d numpy
    ONSHAPE_ACCESS_KEY=... ONSHAPE_SECRET_KEY=... python onshape_leg.py     # new document (about 55 API calls)
    python onshape_leg.py --did D --wid W --eid E                            # resume into an existing Part Studio
    python onshape_leg.py --check-only --did D --wid W --eid E               # re-run the checks (about 8 calls)
    python onshape_leg.py --dry-run                                          # write the feature JSON only, no calls

Frame: leg_unit.py's leg frame.  Origin on the beaker axis at the shelf's underside (the arm's top face is
the Top plane), x across the module, y outward along its centre line, z up.  For the back module this is
base/base.step's frame, so the leg drops onto a base drawn that way without moving it.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import onshape_clevis as OC                     # noqa: E402  (REST helpers and the Sketch class)

CAD = HERE / "leg-unit"
J = json.loads((HERE / "leg_unit.json").read_text())
H, TB, FT = J["head"], J["tube"], J["foot"]
S_MODEL = 340.0                                 # the tube and foot are drawn at this height (shelf underside to bench)
PC = H["sleeve"]["bore_centre"]                 # 301.8: tube centre, from the beaker axis
PIN_Y = H["tab"]["pocket_centre"][1]            # 258.5: the P16's rear pin
CALLS = OC.CALLS


def scoped(feat, fid_body):
    """Limit an extrude's boolean to the body made by feature ``fid_body``."""
    p = [q for q in feat["parameters"] if q.get("parameterId") != "defaultScope"]
    p.append(OC.boolean(False, "defaultScope"))
    p.append({"btType": "BTMParameterQueryList-148", "parameterId": "booleanScope",
              "queries": [{"btType": "BTMIndividualQuery-138",
                           "queryString": f'query=qCreatedBy(makeId("{fid_body}"), EntityType.BODY);'}]})
    feat["parameters"] = p
    return feat


def rect(s, cx, cy, w, h, dims=True):
    ids = s.polygon([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)])
    if dims:
        s.length(ids[0], w)
        s.length(ids[1], h)
    return ids


# --------------------------------------------------------------------------- #
# sketches
# --------------------------------------------------------------------------- #
def sk_profile():
    """Right plane: u = y (out from the beaker axis), v = z."""
    s = OC.Sketch()
    pts = [tuple(p) for p in H["profile"]]
    ids = s.polygon(pts)
    s.length(ids[0], pts[1][0] - pts[0][0])         # arm top, 92 -> 318.1
    s.length(ids[1], -pts[2][1])                    # sleeve outer face, 281.75
    s.length(ids[2], pts[2][0] - pts[3][0])         # sleeve bottom, 32.6
    s.length(ids[7], pts[8][0] - pts[7][0])         # tab top, 35
    s.length(ids[6], pts[7][1] - pts[6][1])         # tab end, 8
    s.length(ids[11], pts[0][1] - pts[11][1])       # arm end, 15
    return s


def sk_window_holes():
    s = OC.Sketch()
    s.polygon([tuple(p) for p in H["window"]])
    for x, y in H["holes"]:
        s.circle((x, y), H["hole_d"])
    return s


def sk_nut_traps():
    s = OC.Sketch()
    for x, y in H["holes"]:
        s.polygon(OC.hexagon(x, y, H["nut_trap_af"]))
    return s


def sk_square(cx, cy, w):
    s = OC.Sketch()
    rect(s, cx, cy, w, w)
    return s


def sk_pin_hole():
    s = OC.Sketch()                                  # Front plane: u = x, v = z
    s.circle((0.0, H["m5_pin"]["z"]), H["m5_pin"]["d"])
    return s


def sk_pocket():
    s = OC.Sketch()
    px, py, _ = H["tab"]["pocket"]
    rect(s, 0.0, PIN_Y, px, py)
    return s


def sk_m3_hole():
    s = OC.Sketch()
    s.circle((0.0, PIN_Y), 3.4)
    return s


def sk_m3_nut():
    s = OC.Sketch()
    s.polygon(OC.hexagon(0.0, PIN_Y, 5.7))
    return s


def sk_tube_holes():
    s = OC.Sketch()                                  # Front plane: u = x, v = z
    z0 = -S_MODEL + FT["pad_t"]
    for h in TB["holes_from_lower_end"]:
        s.circle((0.0, z0 + h), TB["hole_d"])
    return s


def sk_foot_hole():
    s = OC.Sketch()                                  # Right plane: u = y, v = z
    s.circle((PC, -S_MODEL + FT["pad_t"] + TB["foot_hole_h"]), FT["hole_d"])
    return s


def plan():
    """(label, builder); builders get the feature ids made so far, by label."""
    tt, tthk = H["tab"]["top"], H["tab"]["thickness"]
    zsb = H["sleeve"]["bottom"]
    ztb = -S_MODEL + FT["pad_t"]                     # tube bottom = top of the foot's pad
    b = H["sleeve"]["bore"]
    return [
        ("Head profile", lambda i: sk_profile().feature("Head profile", OC.plane_query("Right"))),
        ("Leg head", lambda i: OC.extrude("Leg head", i["Head profile"], "NEW", 2 * H["width_x"] / 2, symmetric=True)),
        ("Arm window and screw holes", lambda i: sk_window_holes().feature("Arm window and screw holes", OC.plane_query("Top"))),
        ("Arm cut", lambda i: OC.extrude("Arm cut", i["Arm window and screw holes"], "REMOVE", H["arm_depth"] + 5.0, opposite=True)),
        ("Arm underside", lambda i: OC.offset_plane("Arm underside", "Top", H["arm_depth"], True)),
        ("Nut traps sketch", lambda i: sk_nut_traps().feature("Nut traps sketch", OC.plane_query(i["Arm underside"]))),
        ("Nut traps", lambda i: OC.extrude("Nut traps", i["Nut traps sketch"], "REMOVE", H["nut_trap_depth"])),
        ("Sleeve bottom", lambda i: OC.offset_plane("Sleeve bottom", "Top", -zsb, True)),
        ("Bore sketch", lambda i: sk_square(0.0, PC, b).feature("Bore sketch", OC.plane_query(i["Sleeve bottom"]))),
        ("Bore", lambda i: OC.extrude("Bore", i["Bore sketch"], "REMOVE", H["sleeve"]["bore_top"] - zsb)),
        ("Height pin hole sketch", lambda i: sk_pin_hole().feature("Height pin hole sketch", OC.plane_query("Front"))),
        ("Height pin hole", lambda i: OC.extrude("Height pin hole", i["Height pin hole sketch"], "REMOVE", 700.0, symmetric=True)),
        ("Tab top", lambda i: OC.offset_plane("Tab top", "Top", -tt, True)),
        ("Bracket pocket sketch", lambda i: sk_pocket().feature("Bracket pocket sketch", OC.plane_query(i["Tab top"]))),
        ("Bracket pocket", lambda i: OC.extrude("Bracket pocket", i["Bracket pocket sketch"], "REMOVE", H["tab"]["pocket"][2], opposite=True)),
        ("Bracket screw hole sketch", lambda i: sk_m3_hole().feature("Bracket screw hole sketch", OC.plane_query(i["Tab top"]))),
        ("Bracket screw hole", lambda i: OC.extrude("Bracket screw hole", i["Bracket screw hole sketch"], "REMOVE", tthk + 1.0, opposite=True)),
        ("Tab underside", lambda i: OC.offset_plane("Tab underside", "Top", -(tt - tthk), True)),
        ("Bracket nut trap sketch", lambda i: sk_m3_nut().feature("Bracket nut trap sketch", OC.plane_query(i["Tab underside"]))),
        ("Bracket nut trap", lambda i: OC.extrude("Bracket nut trap", i["Bracket nut trap sketch"], "REMOVE", 2.6)),
        # the tube, at 340 mm
        ("Tube bottom", lambda i: OC.offset_plane("Tube bottom", "Top", -ztb, True)),
        ("Tube outline", lambda i: sk_square(0.0, PC, TB["size"]).feature("Tube outline", OC.plane_query(i["Tube bottom"]))),
        ("Leg tube", lambda i: OC.extrude("Leg tube", i["Tube outline"], "NEW", TB["length"])),
        ("Tube bore sketch", lambda i: sk_square(0.0, PC, TB["size"] - 2 * TB["wall"]).feature("Tube bore sketch", OC.plane_query(i["Tube bottom"]))),
        ("Tube bore", lambda i: scoped(OC.extrude("Tube bore", i["Tube bore sketch"], "REMOVE", TB["length"]), i["Leg tube"])),
        ("Tube pin holes sketch", lambda i: sk_tube_holes().feature("Tube pin holes sketch", OC.plane_query("Front"))),
        ("Tube pin holes", lambda i: scoped(OC.extrude("Tube pin holes", i["Tube pin holes sketch"], "REMOVE", 700.0, symmetric=True), i["Leg tube"])),
        # the foot
        ("Bench", lambda i: OC.offset_plane("Bench", "Top", S_MODEL, True)),
        ("Foot pad sketch", lambda i: sk_square(0.0, PC, FT["pad"]).feature("Foot pad sketch", OC.plane_query(i["Bench"]))),
        ("Leg foot", lambda i: OC.extrude("Leg foot", i["Foot pad sketch"], "NEW", FT["pad_t"])),
        ("Foot socket sketch", lambda i: sk_square(0.0, PC, FT["socket"]).feature("Foot socket sketch", OC.plane_query(i["Tube bottom"]))),
        ("Foot socket", lambda i: scoped(OC.extrude("Foot socket", i["Foot socket sketch"], "ADD", FT["socket_h"]), i["Leg foot"])),
        ("Foot socket bore sketch", lambda i: sk_square(0.0, PC, FT["bore"]).feature("Foot socket bore sketch", OC.plane_query(i["Tube bottom"]))),
        ("Foot socket bore", lambda i: scoped(OC.extrude("Foot socket bore", i["Foot socket bore sketch"], "REMOVE", FT["socket_h"] + 1.0), i["Leg foot"])),
        ("Foot screw hole sketch", lambda i: sk_foot_hole().feature("Foot screw hole sketch", OC.plane_query("Right"))),
        ("Foot screw hole", lambda i: OC.extrude("Foot screw hole", i["Foot screw hole sketch"], "REMOVE", 100.0, symmetric=True)),
    ]


# --------------------------------------------------------------------------- #
# REST
# --------------------------------------------------------------------------- #
def build(did=None, wid=None, eid=None):
    call = OC.call
    if did is None:
        doc = call("POST", "/documents", {
            "name": "Leg unit - tri-star L4 telescoping stand (powder-doser #204)",
            "description": "One of the three telescoping leg units for the three-auger tri-star (powder-doser issue #204): "
                           "printed head (arm, sleeve, tab for the Actuonix P16-200's U-bracket), 20 x 20 x 1.5 aluminium "
                           "tube and printed foot, for the lever + lean actuator layout (L4). Built through the REST API by "
                           "design/multi-auger-fixed-base/onshape_leg.py from leg_unit.json.",
            "isPublic": False})
        did, wid = doc["id"], doc["defaultWorkspace"]["id"]
        print("document", did, flush=True)
    if eid is None:
        els = call("GET", f"/documents/d/{did}/w/{wid}/elements")
        eid = next(e["id"] for e in els if e.get("elementType") == "PARTSTUDIO")
    ids, tree = {}, []
    have = call("GET", f"/partstudios/d/{did}/w/{wid}/e/{eid}/features").get("features", [])
    for k, (label, fn) in enumerate(plan()):
        feat = fn(ids)
        if k < len(have) and have[k]["featureType"] == feat["featureType"] and have[k].get("name") == feat["name"]:
            fid, status = have[k]["featureId"], "OK (kept)"
        else:
            res = call("POST", f"/partstudios/d/{did}/w/{wid}/e/{eid}/features", {"feature": feat})
            fid = res["feature"]["featureId"]
            status = res.get("featureState", {}).get("featureStatus", "?")
        ids[label] = fid
        tree.append(dict(name=feat["name"], type=feat["featureType"], featureId=fid, status=status.split()[0]))
        print(f"  {feat['name']:<28} {feat['featureType']:<9} {fid}  {status}", flush=True)
        if status.split()[0] != "OK":
            raise RuntimeError(f"feature {feat['name']} came back {status}; stopping (document {did}, element {eid})")
    return did, wid, eid, tree


def name_things(did, wid, eid):
    """Name the three parts (in the order they were made) and the Part Studio tab."""
    call = OC.call
    parts = call("GET", f"/parts/d/{did}/w/{wid}/e/{eid}")

    def order(p):                                   # new parts are "Part 1", "Part 2", ... in the order they were made
        try:
            return int(str(p.get("name", "")).split()[-1])
        except ValueError:
            return 99
    parts = sorted(parts, key=order)
    names = ["Leg head", "Leg tube", "Leg foot"]
    out = []
    for p, nm in zip(parts, names):
        call("POST", f"/metadata/d/{did}/w/{wid}/e/{eid}/p/{p['partId']}",
             {"properties": [{"propertyId": OC.NAME_PROP, "value": nm}]})
        out.append(dict(partId=p["partId"], name=nm))
    try:
        call("POST", f"/metadata/d/{did}/w/{wid}/e/{eid}", {"properties": [{"propertyId": OC.NAME_PROP, "value": "Leg unit"}]})
        tab = "Leg unit"
    except RuntimeError as e:                       # keep going: the tab keeps its default name
        tab = f"Part Studio 1 (rename failed: {str(e)[:120]})"
    return out, len(parts), tab


def read_back(did, wid, eid):
    call = OC.call
    mp = call("GET", f"/partstudios/d/{did}/w/{wid}/e/{eid}/massproperties", params={"massAsGroup": "false"})
    vols = {k: round(v.get("volume", [0])[0] * 1e6, 3) for k, v in mp.get("bodies", {}).items()}
    bb = call("GET", f"/partstudios/d/{did}/w/{wid}/e/{eid}/boundingboxes", params={"includeHidden": "false"})
    box = {k: round(bb[k] * 1000.0, 3) for k in ("lowX", "lowY", "lowZ", "highX", "highY", "highZ")}
    stl = call("GET", f"/partstudios/d/{did}/w/{wid}/e/{eid}/stl", raw=True,
               params={"mode": "binary", "units": "millimeter", "grouping": "true",
                       "chordTolerance": "0.02", "angleTolerance": "0.08"})
    mv = call("GET", f"/documents/d/{did}/w/{wid}/currentmicroversion")
    return dict(volume_cm3_by_part_id=vols, bounding_box_mm=box, microversion=mv.get("microversion")), stl


def shaded_views(did, wid, eid):
    """Two views rendered by Onshape itself: isometric, and a side view (looking along -x)."""
    out = []
    views = [("iso", ["isometric", "0.707,0.707,0,0,-0.409,0.409,0.816,0,0.577,-0.577,0.577,0"]),
             ("side", ["right", "0,1,0,0,0,0,1,0,1,0,0,0"])]
    for tag, vms in views:
        for vm in vms:
            try:
                r = OC.call("GET", f"/partstudios/d/{did}/w/{wid}/e/{eid}/shadedviews",
                            params={"viewMatrix": vm, "outputHeight": 900, "outputWidth": 900, "pixelSize": 0, "edges": "show"})
            except RuntimeError as e:
                print("  shaded view", tag, vm, "failed:", str(e)[:160], flush=True)
                continue
            img = base64.b64decode(r["images"][0])
            fn = CAD / f"onshape_{tag}.png"
            fn.write_bytes(img)
            out.append(fn)
            break
    return out


def compare(stl_bytes):
    """The Onshape parts against leg_unit.py's head, tube and foot at 340 mm, all in the leg frame."""
    import io
    import numpy as np
    import trimesh
    import manifold3d as mf
    import cadquery as cq
    import leg_unit as LU

    ons = trimesh.load(io.BytesIO(stl_bytes), file_type="stl")
    loc = LU.head().fuse(LU.tube(S_MODEL)).fuse(LU.foot(S_MODEL))
    tmp = CAD / "_local.stl"
    cq.exporters.export(cq.Workplane().add(loc), str(tmp), tolerance=0.02, angularTolerance=0.08)
    lm = trimesh.load(str(tmp))
    tmp.unlink()

    def man(t):
        return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))

    a, b = man(ons), man(lm)
    return dict(onshape_volume_cm3=round(ons.volume / 1000.0, 3), leg_unit_py_volume_cm3=round(loc.Volume() / 1000.0, 3),
                leg_unit_py_by_part_cm3=dict(head=round(LU.head().Volume() / 1000, 3), tube=round(LU.tube(S_MODEL).Volume() / 1000, 3),
                                             foot=round(LU.foot(S_MODEL).Volume() / 1000, 3)),
                onshape_bounds_mm=np.round(ons.bounds, 2).tolist(), leg_unit_py_bounds_mm=np.round(lm.bounds, 2).tolist(),
                symmetric_difference_mm3=round(float((a - b).volume() + (b - a).volume()), 2), watertight=bool(ons.is_watertight))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--did"), ap.add_argument("--wid"), ap.add_argument("--eid")
    a = ap.parse_args()
    CAD.mkdir(exist_ok=True)
    if a.dry_run:
        ids = {k: f"<{k}>" for k, _ in plan()}
        (CAD / "onshape_features.json").write_text(json.dumps([fn(ids) for _, fn in plan()], indent=1) + "\n")
        print("wrote leg-unit/onshape_features.json:", len(plan()), "features")
        return
    out_p = CAD / "onshape.json"
    old = json.loads(out_p.read_text()) if out_p.exists() else {}
    if a.check_only:
        d = old.get("document", {})
        did, wid, eid, tree = a.did or d["did"], a.wid or d["wid"], a.eid or d["eid"], old.get("features")
        parts, tab = old.get("parts"), old.get("tab")
    else:
        did, wid, eid, tree = build(a.did, a.wid, a.eid)
        parts, n, tab = name_things(did, wid, eid)
        print("parts", n, parts, "tab", tab, flush=True)
    rb, stl = read_back(did, wid, eid)
    (CAD / "leg_unit_onshape.stl").write_bytes(stl)
    cmp_ = compare(stl)
    print("read back:", rb, flush=True)
    print("compare:", cmp_, flush=True)
    views = shaded_views(did, wid, eid)
    res = dict(
        what="One tri-star leg unit (leg_unit.json) as a native Onshape Part Studio, built through the REST API",
        document=dict(did=did, wid=wid, eid=eid, url=f"https://cad.onshape.com/documents/{did}/w/{wid}/e/{eid}",
                      owner="the account the API key belongs to (Ethan's); private until shared"),
        tab=tab, parts=parts, features=tree, read_back=rb, compare_with_leg_unit_py=cmp_,
        shaded_views=[str(v.relative_to(HERE)) for v in views], tube_and_foot_drawn_at=S_MODEL,
        frame="leg frame: origin on the beaker axis at the shelf's underside, x across, y out along the module's centre line, z up",
        api_calls_this_run=CALLS["n"], when_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    if a.check_only and old:
        for k in ("api_calls_build",):
            if k in old:
                res[k] = old[k]
    else:
        res["api_calls_build"] = CALLS["n"]
    out_p.write_text(json.dumps(res, indent=1) + "\n")
    print("API calls this run:", CALLS["n"])


if __name__ == "__main__":
    main()

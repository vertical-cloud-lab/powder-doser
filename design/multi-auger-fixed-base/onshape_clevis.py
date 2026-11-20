"""Build the clevis block as a native Onshape Part Studio through the REST API (issue #204, 20 Nov).

Ethan asked for the rod-end clevis block (clevis.py, 17 Nov) in Onshape.  This script makes
a new document in the account the API key belongs to and builds the block from sketches
and extrudes, so every size can be edited in Onshape afterwards.  It then reads the part
back (mass properties, bounding box, an STL export) and checks it against clevis.py's
block.  It writes clevis/onshape.json (the document, the feature list, the checks and the
number of API calls) and clevis/clevis_block_onshape.stl (the part as Onshape exports it).

    pip install requests cadquery trimesh manifold3d numpy
    ONSHAPE_ACCESS_KEY=... ONSHAPE_SECRET_KEY=... python onshape_clevis.py            # new document (about 25 API calls)
    python onshape_clevis.py --did D --wid W                                            # build into an existing document
    python onshape_clevis.py --check-only --did D --wid W --eid E                       # re-run the checks only (about 6 calls)
    python onshape_clevis.py --dry-run                                                  # write the feature JSON, no API calls

Frame (the same as clevis.json and clevis/clevis_block.step): origin at the centre of the
pad's top face, the face that sits against the floor's underside; x along the pin, y along
the plate (+y toward the rear), z up.  The block hangs below the Top plane.

Feature tree:
    1  Sketch "Pad sketch" (Top): 30 x 24 rectangle
    2  Extrude "Pad": 4 mm down, new part
    3  Sketch "Lug profile" (Right): 14 wide, from the pad's underside to the pin axis, R7 round it
    4  Extrude "Lugs": that profile, symmetric 14.5 (both lugs and the gap), add
    5  Extrude "Lug gap": the same profile, symmetric 6.5, remove
    6  Sketch "Pin hole sketch" (Right): dia 4.25 on the pin axis, 9.75 below the top face
    7  Extrude "Pin hole": symmetric 40, remove
    8  Sketch "Screw holes sketch" (Top): 2 x dia 3.4, 22 apart
    9  Extrude "Screw holes": 10 mm down, remove
   10  Plane "Pad underside": Top, offset 4 mm down
   11  Sketch "Nut pockets sketch" (Pad underside): 2 hexagons, 5.8 across flats, flats facing the pad's ends
   12  Extrude "Nut pockets": 2.6 mm up into the pad, remove
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAD = HERE / "clevis"
API = "https://cad.onshape.com/api/v6"
NAME_PROP = "57f3fb8efa3416c06701d60d"          # Onshape's standard "Name" property

J = json.loads((HERE / "clevis.json").read_text())
PX, PY, PT = J["pad"]["x"], J["pad"]["y"], J["pad"]["thickness"]          # 30, 24, 4
LUG_T, LUG_W, LUG_R, GAP = J["lugs"]["thickness"], J["lugs"]["width"], J["lugs"]["end_radius"], J["lugs"]["gap_between"]
PIN_Z, PIN_D = -J["pin_hole"]["axis_below_top_face"], J["pin_hole"]["dia"]  # -9.75, 4.25
SX, SCREW_D = J["screw_holes"]["x"][1], J["screw_holes"]["dia"]            # 11, 3.4
NUT_AF, NUT_H = J["nut_pockets"]["across_flats"], J["nut_pockets"]["depth"]  # 5.8, 2.6
OVER = 2 * LUG_T + GAP                                                      # 14.5 over both lugs

CALLS = {"n": 0}


# --------------------------------------------------------------------------- #
# feature JSON (sketch geometry is in metres)
# --------------------------------------------------------------------------- #
def m(v):
    return v / 1000.0


def sv(v, pid):
    return {"btType": "BTMParameterString-149", "value": v, "parameterId": pid}


def qty(expr, pid):
    return {"btType": "BTMParameterQuantity-147", "expression": expr, "parameterId": pid}


def enum(name, v, pid):
    return {"btType": "BTMParameterEnum-145", "enumName": name, "value": v, "parameterId": pid}


def boolean(v, pid):
    return {"btType": "BTMParameterBoolean-144", "value": v, "parameterId": pid}


def qlist(pid, query_string):
    return {"btType": "BTMParameterQueryList-148", "parameterId": pid,
            "queries": [{"btType": "BTMIndividualQuery-138", "queryString": query_string}]}


def plane_query(feature_or_plane):
    return f'query=qCreatedBy(makeId("{feature_or_plane}"), EntityType.FACE);'


class Sketch:
    """Lines, arcs and circles with their constraints, in the sketch's own (u, v) in mm."""

    def __init__(self):
        self.entities, self.constraints, self._n = [], [], 0

    def _id(self, p):
        self._n += 1
        return f"{p}{self._n}"

    def con(self, kind, *params):
        self.constraints.append({"btType": "BTMSketchConstraint-2", "constraintType": kind,
                                 "entityId": self._id("c"), "parameters": list(params)})

    def line(self, a, b):
        eid = self._id("l")
        du, dv = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(du, dv)
        self.entities.append({"btType": "BTMSketchCurveSegment-155", "entityId": eid,
                              "startPointId": f"{eid}.start", "endPointId": f"{eid}.end",
                              "startParam": 0.0, "endParam": m(ln), "isConstruction": False,
                              "geometry": {"btType": "BTCurveGeometryLine-117", "pntX": m(a[0]), "pntY": m(a[1]),
                                           "dirX": du / ln, "dirY": dv / ln}})
        if abs(dv) < 1e-9:
            self.con("HORIZONTAL", sv(eid, "localFirst"))
        elif abs(du) < 1e-9:
            self.con("VERTICAL", sv(eid, "localFirst"))
        return eid

    def arc(self, c, r, start_dir, sweep):
        """Counter-clockwise arc about c, starting in direction start_dir (unit, (u, v)), sweeping `sweep` rad."""
        eid = self._id("a")
        self.entities.append({"btType": "BTMSketchCurveSegment-155", "entityId": eid,
                              "startPointId": f"{eid}.start", "endPointId": f"{eid}.end", "centerId": f"{eid}.center",
                              "startParam": 0.0, "endParam": sweep, "isConstruction": False,
                              "geometry": {"btType": "BTCurveGeometryCircle-115", "radius": m(r),
                                           "xCenter": m(c[0]), "yCenter": m(c[1]),
                                           "xDir": start_dir[0], "yDir": start_dir[1], "clockwise": False}})
        return eid

    def circle(self, c, d):
        eid = self._id("o")
        self.entities.append({"btType": "BTMSketchCurve-4", "entityId": eid, "centerId": f"{eid}.center",
                              "isConstruction": False,
                              "geometry": {"btType": "BTCurveGeometryCircle-115", "radius": m(d / 2),
                                           "xCenter": m(c[0]), "yCenter": m(c[1]), "xDir": 1.0, "yDir": 0.0,
                                           "clockwise": False}})
        self.con("DIAMETER", sv(eid, "localFirst"), qty(f"{d:g} mm", "length"))
        return eid

    def coincident(self, p, q):
        self.con("COINCIDENT", sv(p, "localFirst"), sv(q, "localSecond"))

    def polygon(self, pts):
        ids = [self.line(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
        for i in range(len(ids)):
            self.coincident(f"{ids[i]}.end", f"{ids[(i + 1) % len(ids)]}.start")
        return ids

    def length(self, eid, mm):
        self.con("LENGTH", sv(eid, "localFirst"), qty(f"{mm:g} mm", "length"))

    def feature(self, name, plane_qs):
        return {"btType": "BTMSketch-151", "featureType": "newSketch", "name": name,
                "parameters": [qlist("sketchPlane", plane_qs)],
                "entities": self.entities, "constraints": self.constraints}


def extrude(name, sketch_id, op, depth_mm, symmetric=False, opposite=False):
    p = [enum("ExtendedToolBodyType", "SOLID", "bodyType"),
         enum("NewBodyOperationType", op, "operationType"),
         {"btType": "BTMParameterQueryList-148", "parameterId": "entities",
          "queries": [{"btType": "BTMIndividualSketchRegionQuery-140", "featureId": sketch_id}]},
         enum("BoundingType", "BLIND", "endBound"),
         qty(f"{depth_mm:g} mm", "depth")]
    if symmetric:                                  # Onshape: total depth, half each side of the sketch plane
        p.append(boolean(True, "symmetric"))
    if opposite:
        p.append(boolean(True, "oppositeDirection"))
    if op != "NEW":
        p.append(boolean(True, "defaultScope"))
    return {"btType": "BTMFeature-134", "featureType": "extrude", "name": name, "parameters": p}


def offset_plane(name, ref_plane, offset_mm, opposite):
    return {"btType": "BTMFeature-134", "featureType": "cPlane", "name": name,
            "parameters": [enum("CPlaneType", "OFFSET", "cplaneType"),
                           qlist("entities", plane_query(ref_plane)),
                           qty(f"{offset_mm:g} mm", "offset"),
                           boolean(opposite, "oppositeDirection")]}


def hexagon(cx, cy, af):
    r = af / math.sqrt(3.0)
    return [(cx + r * math.cos(math.radians(30 + 60 * i)), cy + r * math.sin(math.radians(30 + 60 * i))) for i in range(6)]


def sketch_pad():
    s = Sketch()
    ids = s.polygon([(-PX / 2, -PY / 2), (PX / 2, -PY / 2), (PX / 2, PY / 2), (-PX / 2, PY / 2)])
    s.length(ids[0], PX)
    s.length(ids[1], PY)
    return s


def sketch_lug():
    """On the Right plane: u = +y (along the plate), v = +z."""
    s = Sketch()
    a, b, c, d = (LUG_R, -PT), (-LUG_R, -PT), (-LUG_R, PIN_Z), (LUG_R, PIN_Z)
    top = s.line(a, b)
    left = s.line(b, c)
    arc = s.arc((0.0, PIN_Z), LUG_R, (-1.0, 0.0), math.pi)       # from (-R, pin) round the bottom to (+R, pin)
    right = s.line(d, a)
    s.coincident(f"{top}.end", f"{left}.start")
    s.coincident(f"{left}.end", f"{arc}.start")
    s.coincident(f"{arc}.end", f"{right}.start")
    s.coincident(f"{right}.end", f"{top}.start")
    s.con("TANGENT", sv(left, "localFirst"), sv(arc, "localSecond"))
    s.con("TANGENT", sv(right, "localFirst"), sv(arc, "localSecond"))
    s.con("RADIUS", sv(arc, "localFirst"), qty(f"{LUG_R:g} mm", "length"))     # sets the width too (2 x R7 = 14)
    s.length(left, -PIN_Z - PT)
    return s


def sketch_pin():
    s = Sketch()
    s.circle((0.0, PIN_Z), PIN_D)
    return s


def sketch_screws():
    s = Sketch()
    s.circle((-SX, 0.0), SCREW_D)
    s.circle((SX, 0.0), SCREW_D)
    return s


def sketch_nuts():
    s = Sketch()
    for sx in (-1, 1):
        s.polygon(hexagon(sx * SX, 0.0, NUT_AF))
    return s


def plan():
    """(label, builder) in order; builders take the feature ids of the earlier features by label."""
    return [
        ("Pad sketch", lambda ids: sketch_pad().feature("Pad sketch", plane_query("Top"))),
        ("Pad", lambda ids: extrude("Pad", ids["Pad sketch"], "NEW", PT, opposite=True)),
        ("Lug profile", lambda ids: sketch_lug().feature("Lug profile", plane_query("Right"))),
        ("Lugs", lambda ids: extrude("Lugs", ids["Lug profile"], "ADD", OVER, symmetric=True)),
        ("Lug gap", lambda ids: extrude("Lug gap", ids["Lug profile"], "REMOVE", GAP, symmetric=True)),
        ("Pin hole sketch", lambda ids: sketch_pin().feature("Pin hole sketch", plane_query("Right"))),
        ("Pin hole", lambda ids: extrude("Pin hole", ids["Pin hole sketch"], "REMOVE", 40.0, symmetric=True)),
        ("Screw holes sketch", lambda ids: sketch_screws().feature("Screw holes sketch", plane_query("Top"))),
        ("Screw holes", lambda ids: extrude("Screw holes", ids["Screw holes sketch"], "REMOVE", 10.0, opposite=True)),
        ("Pad underside", lambda ids: offset_plane("Pad underside", "Top", PT, True)),
        ("Nut pockets sketch", lambda ids: sketch_nuts().feature("Nut pockets sketch", plane_query(ids["Pad underside"]))),
        ("Nut pockets", lambda ids: extrude("Nut pockets", ids["Nut pockets sketch"], "REMOVE", NUT_H)),
    ]


# --------------------------------------------------------------------------- #
# REST
# --------------------------------------------------------------------------- #
def _auth():
    return (os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])


def call(method, path, body=None, params=None, raw=False, timeout=120):
    import requests
    CALLS["n"] += 1
    hdr = {"Accept": "application/octet-stream" if raw else "application/json"}
    r = requests.request(method, f"{API}{path}", auth=_auth(), params=params, json=body, timeout=timeout,
                         headers=hdr, allow_redirects=False)
    if r.status_code in (302, 303, 307) and "Location" in r.headers:   # exports redirect; keep the key on the hop
        CALLS["n"] += 1
        r = requests.get(r.headers["Location"], auth=_auth(), headers=hdr, timeout=timeout)
    if not r.ok:
        raise RuntimeError(f"{method} {path} -> HTTP {r.status_code}: {r.text[:600]}")
    return r.content if raw else (r.json() if r.content else {})


def build(name, description, did=None, wid=None, eid=None):
    """New document with a "Clevis block" Part Studio (or that tab in an existing document), then the features.
    The key can't delete elements (HTTP 403), so the new document keeps its empty "Part Studio 1"."""
    if did is None:
        doc = call("POST", "/documents", {"name": name, "description": description, "isPublic": False})
        did, wid = doc["id"], doc["defaultWorkspace"]["id"]
        print("document", did, flush=True)
    if eid is None:
        els = call("GET", f"/documents/d/{did}/w/{wid}/elements")
        eid = next((e["id"] for e in els if e.get("name") == "Clevis block" and e.get("elementType") == "PARTSTUDIO"), None)
        if eid is None:
            eid = call("POST", f"/partstudios/d/{did}/w/{wid}", {"name": "Clevis block"})["id"]
    ids, tree = {}, []
    have = call("GET", f"/partstudios/d/{did}/w/{wid}/e/{eid}/features").get("features", [])   # resume after a failure
    for i, (label, fn) in enumerate(plan()):
        feat = fn(ids)
        if i < len(have) and have[i]["featureType"] == feat["featureType"]:
            fid = have[i]["featureId"]
            if have[i].get("name") != feat["name"]:                         # same feature, renamed since
                call("POST", f"/partstudios/d/{did}/w/{wid}/e/{eid}/features/featureid/{fid}",
                     {"feature": dict(feat, featureId=fid)})
            status = "OK (kept)"
        else:
            res = call("POST", f"/partstudios/d/{did}/w/{wid}/e/{eid}/features", {"feature": feat})
            fid = res["feature"]["featureId"]
            status = res.get("featureState", {}).get("featureStatus")
        ids[label] = fid
        tree.append(dict(name=feat["name"], type=feat["featureType"], featureId=fid, status=status.split()[0]))
        print(f"  {feat['name']:<19} {feat['featureType']:<9} {fid}  {status}", flush=True)
        if status.split()[0] != "OK":
            raise RuntimeError(f"feature {feat['name']} came back {status}; stopping (document {did})")
    return did, wid, eid, tree


def name_part(did, wid, eid):
    parts = call("GET", f"/parts/d/{did}/w/{wid}/e/{eid}")
    pid = parts[0]["partId"]
    meta = call("GET", f"/metadata/d/{did}/w/{wid}/e/{eid}/p/{pid}")
    prop = next((p["propertyId"] for p in meta.get("properties", []) if p.get("name") == "Name"), NAME_PROP)
    call("POST", f"/metadata/d/{did}/w/{wid}/e/{eid}/p/{pid}",
         {"properties": [{"propertyId": prop, "value": "Clevis block"}]})
    return pid, len(parts)


def read_back(did, wid, eid):
    mp = call("GET", f"/partstudios/d/{did}/w/{wid}/e/{eid}/massproperties", params={"massAsGroup": "false"})
    bodies = mp.get("bodies", {})
    vol = [b.get("volume", [None])[0] for b in bodies.values()]
    bb = call("GET", f"/partstudios/d/{did}/w/{wid}/e/{eid}/boundingboxes", params={"includeHidden": "false"})
    box = {k: round(bb[k] * 1000.0, 3) for k in ("lowX", "lowY", "lowZ", "highX", "highY", "highZ")}
    stl = call("GET", f"/partstudios/d/{did}/w/{wid}/e/{eid}/stl", raw=True,
               params={"mode": "binary", "units": "millimeter", "grouping": "true",
                       "chordTolerance": "0.01", "angleTolerance": "0.05"})
    mv = call("GET", f"/documents/d/{did}/w/{wid}/currentmicroversion")
    return dict(volume_cm3=[round(v * 1e6, 4) for v in vol if v is not None], bounding_box_mm=box,
                microversion=mv.get("microversion")), stl


def compare(stl_bytes):
    """The Onshape part against clevis.py's block, both in the block frame."""
    import io
    import numpy as np
    import trimesh
    import manifold3d as mf
    sys.path.insert(0, str(HERE))
    import clevis as CL
    import cadquery as cq

    ons = trimesh.load(io.BytesIO(stl_bytes), file_type="stl")
    blk = CL.block()
    tmp = CAD / "_local.stl"
    cq.exporters.export(cq.Workplane().add(blk), str(tmp), tolerance=0.01, angularTolerance=0.05)
    loc = trimesh.load(str(tmp))
    tmp.unlink()

    def man(t):
        return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))

    a, b = man(ons), man(loc)
    diff = (a - b).volume() + (b - a).volume()
    return dict(onshape_volume_cm3=round(ons.volume / 1000.0, 4), clevis_py_volume_cm3=round(blk.Volume() / 1000.0, 4),
                onshape_bounds_mm=np.round(ons.bounds, 3).tolist(), clevis_py_bounds_mm=np.round(loc.bounds, 3).tolist(),
                symmetric_difference_mm3=round(float(diff), 3), watertight=bool(ons.is_watertight))


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
        print("wrote clevis/onshape_features.json")
        return
    out_p = CAD / "onshape.json"
    old = json.loads(out_p.read_text()) if out_p.exists() else {}
    if a.check_only:
        did, wid, eid, tree = a.did or old["document"]["did"], a.wid or old["document"]["wid"], a.eid or old["document"]["eid"], old.get("features")
        pid = old.get("part_id")
    else:
        did, wid, eid, tree = build("Clevis block - tri-star actuator mount (powder-doser #204)",
                                    "Rod-end clevis block for the Actuonix P16 under the gearless mounting plate "
                                    "(tri-star B2, powder-doser issue #204). Built through the REST API by "
                                    "design/multi-auger-fixed-base/onshape_clevis.py from clevis.json.",
                                    a.did, a.wid, a.eid)
        pid, _ = name_part(did, wid, eid)
    rb, stl = read_back(did, wid, eid)
    (CAD / "clevis_block_onshape.stl").write_bytes(stl)
    cmp_ = compare(stl)
    print("read back:", rb, flush=True)
    print("compare:", cmp_, flush=True)
    res = dict(
        what="The clevis block (clevis.json) as a native Onshape Part Studio, built through the REST API",
        document=dict(did=did, wid=wid, eid=eid, url=f"https://cad.onshape.com/documents/{did}/w/{wid}/e/{eid}",
                      owner="the account the API key belongs to (Ethan's); private until shared"),
        part_id=pid, features=tree, read_back=rb, compare_with_clevis_py=cmp_,
        api_calls_this_run=CALLS["n"], when_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        frame=J["frame"])
    if a.check_only and old:
        res["api_calls_build"] = old.get("api_calls_build", old.get("api_calls_this_run"))
    else:
        res["api_calls_build"] = CALLS["n"]
    out_p.write_text(json.dumps(res, indent=1) + "\n")
    print("API calls this run:", CALLS["n"])


if __name__ == "__main__":
    main()

"""Put the stepper holes of Ethan's Onshape mounting plate on the NEMA-11's 23 mm square.

Ethan's native plate (document "Mounting plate", 16 Oct 2026) is one solid: the plate,
both 28T tilt gears and both links, as they should print. Its "Stepper mount holes
sketch" places the NEMA-11 holes 24.4 x 23.0 mm apart: the left hole line sits 6 mm from
the block's left edge, while the top line sits 6.6 mm from its top edge, and the bore's
vertical centreline sits 18 mm from the right edge of a 36.2 mm block, so the bore is
0.1 mm off centre and the holes are mirrored about that line. PR #170's Fusion plate and
the 11HS18-0674S datasheet have the holes on a 23 mm square around a centred bore.

This changes the two dimensions, 6 -> 6.6 mm and 18 -> 18.1 mm, and nothing else:
holes at 23.0 x 23.0 mm, bore centred on the block. It saves a version before and after.

    python fix_motor_holes.py            # 4 calls: feature list, version, feature update, version

Run from this folder with ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY set.
"""
from __future__ import annotations

import copy
import json

from client import HERE, Onshape

DID = "53e9cce7f09a50f89c120028"   # Mounting plate (Ethan Webster, 16 Oct 2026)
WID = "d45f5e9d7335aff0b1f1e88d"   # its main workspace
EID = "224d71f16476d8c27dc6e3e0"   # Part Studio 1
FID = "F22XafiYiWk3fn8_1"          # Stepper mount holes sketch
# dimension (by the sketch line it places) -> (old, new)
DIMS = {"02YQINjMSnN1.0": ("6 mm", "6.6 mm"),      # left hole line, from the block's left edge
        "7zV6QhdAn8Xq.0": ("18 mm", "18.1 mm")}    # bore centreline, from the block's right edge
# matching start positions for the solver, in metres (sketch x)
MOVE_X = {-0.0441: -0.0435, -0.0197: -0.0205, -0.0319: -0.0320}
REC = HERE / "mounting_plate_onshape.json"


def patched(feature: dict) -> dict:
    ft = copy.deepcopy(feature)
    done = set()
    for c in ft["constraints"]:
        if c["constraintType"] != "DISTANCE":
            continue
        ps = {p["parameterId"]: p for p in c["parameters"]}
        line = ps.get("localSecond", {}).get("value")
        if line in DIMS:
            old, new = DIMS[line]
            assert ps["length"]["expression"] == old, (line, ps["length"]["expression"])
            ps["length"]["expression"] = new
            done.add(line)
    assert done == set(DIMS), done
    for e in ft["entities"]:
        g = e["geometry"]
        for key in ("xCenter", "pntX"):
            if key in g:
                for old, new in MOVE_X.items():
                    if abs(g[key] - old) < 1e-6:
                        g[key] = new
    return ft


def main() -> None:
    o = Onshape(budget=4, run="pr181-fix-motor-holes")
    feats = o.get(f"partstudios/d/{DID}/w/{WID}/e/{EID}/features")
    feature = next(f for f in feats["features"] if f["featureId"] == FID)
    new = patched(feature)
    (HERE / "results").mkdir(exist_ok=True)
    for tag, ft in (("before", feature), ("after", new)):
        (HERE / "results" / f"stepper_holes_sketch_{tag}.json").write_text(json.dumps(ft, indent=1) + "\n")
    rec = json.loads(REC.read_text()) if REC.exists() else {}
    v0 = o.post(f"documents/d/{DID}/versions", {
        "documentId": DID, "workspaceId": WID, "name": "Ethan 16 Oct (before motor-hole fix)",
        "description": "Ethan Webster's plate as of 16 Oct 2026, saved before PR #181 moved the "
                       "stepper holes onto the NEMA-11's 23 mm square."})
    r = o.post(f"partstudios/d/{DID}/w/{WID}/e/{EID}/features/featureid/{FID}", {
        "btType": "BTFeatureDefinitionCall-1406", "feature": new,
        "sourceMicroversion": feats["sourceMicroversion"],
        "serializationVersion": feats["serializationVersion"], "rejectMicroversionSkew": False})
    state = r.get("featureState", {}).get("featureStatus")
    print("feature status:", state)
    if state != "OK":
        raise SystemExit(json.dumps(r.get("featureState"), indent=1))
    v1 = o.post(f"documents/d/{DID}/versions", {
        "documentId": DID, "workspaceId": WID, "name": "Motor holes on 23 mm square (PR #181)",
        "description": "Stepper mount holes sketch: left hole line 6 -> 6.6 mm and bore centreline "
                       "18 -> 18.1 mm, so the NEMA-11 holes sit on a 23.0 x 23.0 mm square around a "
                       "centred bore, as in PR #170's Fusion plate. Nothing else changed. "
                       "https://github.com/vertical-cloud-lab/powder-doser/pull/181"})
    rec.update({"documentId": DID, "workspaceId": WID, "elementId": EID,
                "url": f"https://cad.onshape.com/documents/{DID}",
                "versions": [{"id": v["id"], "name": v["name"], "createdAt": v.get("createdAt")} for v in (v0, v1)]})
    REC.write_text(json.dumps(rec, indent=1) + "\n")
    print("versions:", [(v["name"], v["id"]) for v in (v0, v1)], "calls", o.calls)


if __name__ == "__main__":
    main()

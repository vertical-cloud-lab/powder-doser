"""The servos-above doser with a thinner table, edited in Onshape through the
REST API (issue #172; the Onshape side of the text-to-cad edit).

The edit: the baseplate's table (the 6 mm slab the hinge towers and servo
cradles stand on) gets thinner by ``table_trim``, so the towers, the tilting
system, the servos and their screws all sit ``table_trim`` lower; the board
stays where it is.  In Onshape that is three native features after the
import, all driven by one variable:

1. ``#table_trim``         Variable (length)
2. ``Thin the table``      Move face, OFFSET: the baseplate's underside moves
                           up by #table_trim (the slab gets thinner)
3. ``Lower the doser``     Transform, translate (0, 0, -#table_trim): every
                           body but the board, baseplate included, so the
                           underside is back on the board and everything
                           above the table is #table_trim lower

Steps (each records what it made in onshape_document.json; re-running a
step reuses what is recorded):

    python3 onshape/doser_step.py /tmp/os/doser_servos_above.step
    python3 onshape/lower_table.py import       # doc + flattened import
    python3 onshape/lower_table.py inspect      # bodies, faces, feature specs
    python3 onshape/lower_table.py edit --trim 3
    python3 onshape/lower_table.py set --trim 2.5   # change the variable later
    python3 onshape/lower_table.py verify       # boxes, volume, views, STEP back

The import is flattened (every body of the assembly in place in one Part
Studio), so a single variable moves everything; an Onshape assembly from
the same STEP would need the lowering applied to its instances separately.
Every call is counted and logged (onshape_client.py) because the company's
plan (EDU Educator) has 2,500 API calls a year.
"""
from __future__ import annotations

import argparse
import base64
import json
import time
from pathlib import Path

from onshape_client import HERE, Onshape

REC = HERE / "onshape_document.json"
RESULTS = HERE / "results"
RENDERS = HERE.parent / "renders" / "onshape"
COMPANY = "Vertical Cloud Lab"
DOC_NAME = "Powder doser - servos above, thinner table (text-to-cad, #172)"
STEP = Path("/tmp/os/doser_servos_above.step")
STEP_NAME = "Powder doser servos above (text-to-cad).step"
TABLE_T = 6.0                     # mm, baseplate.PLATE_T


def load() -> dict:
    return json.loads(REC.read_text()) if REC.exists() else {}


def save(rec: dict) -> None:
    REC.write_text(json.dumps(rec, indent=1) + "\n")


def ps(rec: dict) -> str:
    return f"/partstudios/d/{rec['documentId']}/w/{rec['workspaceId']}/e/{rec['partStudio']['elementId']}"


def wait_translation(c: Onshape, tid: str, first: float = 40, every: float = 25, polls: int = 14) -> dict:
    """Every poll is a metered call: wait before the first one, then poll slowly."""
    time.sleep(first)
    for _ in range(polls):
        st = c.get(f"/translations/{tid}")
        if st["requestState"] == "DONE":
            return st
        if st["requestState"] == "FAILED":
            raise RuntimeError(f"translation {tid} failed: {st.get('failureReason')}")
        time.sleep(every)
    raise RuntimeError(f"translation {tid} still running after {polls} polls")


def version(c: Onshape, rec: dict, name: str, description: str) -> None:
    v = c.post(f"/documents/d/{rec['documentId']}/versions",
               json={"documentId": rec["documentId"], "workspaceId": rec["workspaceId"],
                     "name": name, "description": description})
    rec.setdefault("versions", []).append({"id": v["id"], "name": name})
    save(rec)


def shaded(c: Onshape, rec: dict, out: Path, view: str, w: int = 1400, h: int = 900) -> None:
    r = c.get(f"{ps(rec)}/shadedviews",
              params={"viewMatrix": view, "outputHeight": h, "outputWidth": w,
                      "pixelSize": 0, "edges": "show", "useAntiAliasing": "true"})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(r["images"][0]))
    print("->", out)


# --------------------------------------------------------------------------- #
def cmd_import(c: Onshape, rec: dict, commit: str) -> None:
    if "documentId" not in rec:
        cid = next(it["id"] for it in c.get("/companies")["items"] if it["name"] == COMPANY)
        doc = c.post("/documents", json={
            "name": DOC_NAME, "ownerId": cid, "ownerType": 1, "isPublic": False,
            "description": "Servos-above powder doser from vertical-cloud-lab/powder-doser "
                           f"cad/text-to-cad (PR #176, {commit}), flattened into one Part Studio; "
                           "the table is thinned by native features driven by #table_trim "
                           "(cad/text-to-cad/onshape/lower_table.py)."})
        rec.update(documentId=doc["id"], workspaceId=doc["defaultWorkspace"]["id"], owner=COMPANY,
                   url=f"https://cad.onshape.com/documents/{doc['id']}/w/{doc['defaultWorkspace']['id']}")
        save(rec)
        print("document:", rec["url"])
    if "partStudio" not in rec:
        data = STEP.read_bytes()
        res = c.post(f"/blobelements/d/{rec['documentId']}/w/{rec['workspaceId']}",
                     files={"file": (STEP_NAME, data, "application/step")},
                     data={"encodedFilename": STEP_NAME, "fileContentLength": str(len(data)),
                           "translate": "true", "flattenAssemblies": "true", "yAxisIsUp": "false",
                           "storeInDocument": "false"})
        tid = res.get("translationId") or res["id"]
        st = wait_translation(c, tid)
        rec["partStudio"] = {"elementId": st["resultElementIds"][0], "source": f"text-to-cad {commit}"}
        save(rec)
        print("part studio:", rec["partStudio"]["elementId"])
    if not rec.get("versions"):
        version(c, rec, "text-to-cad import", f"assembly_servos_above.step at {commit}, "
                "electronics left out, before any edit")
    shaded(c, rec, RENDERS / "onshape_before_right.png", "right")
    box = c.get(f"{ps(rec)}/boundingboxes")
    (RESULTS / "bbox_before.json").write_text(json.dumps(box, indent=1) + "\n")


def cmd_inspect(c: Onshape, rec: dict) -> None:
    """Body ids and names, the baseplate's underside, and the specs of the
    three features (parameter ids are taken from these, not guessed)."""
    raw = Path("/tmp/os/bodydetails_raw.json")       # 12 MB, not committed
    det = json.loads(raw.read_text()) if raw.exists() else c.get(f"{ps(rec)}/bodydetails")
    raw.write_text(json.dumps(det) + "\n")
    rec["bodies"] = [{"id": b["id"], "name": (b.get("properties") or {}).get("name", "")}
                     for b in det["bodies"]]
    base = [b for b in det["bodies"] if (b.get("properties") or {}).get("name") == "baseplate"]
    assert len(base) == 1, "expected one body named 'baseplate'"
    # the underside: the plane face whose box is flat at z = 0 (the API reports
    # the plane's normal as +Z here, so go by the box, not the normal)
    under = [f["id"] for f in base[0]["faces"] if f["surface"]["type"] == "PLANE"
             and abs(f["box"]["minCorner"]["z"]) < 1e-7 and abs(f["box"]["maxCorner"]["z"]) < 1e-7]
    assert len(under) == 1, under
    rec["baseplate"] = {"partId": base[0]["id"], "underside": under}
    save(rec)
    specs_path = Path("/tmp/os/featurespecs_full.json")
    specs = (json.loads(specs_path.read_text()) if specs_path.exists()
             else c.get(f"{ps(rec)}/featurespecs"))
    specs_path.write_text(json.dumps(specs) + "\n")
    keep = {}
    for s in specs.get("featureSpecs", []):
        if s.get("featureType") in ("moveFace", "transform", "assignVariable"):
            keep[s["featureType"]] = {"name": s.get("featureTypeName"), "parameters": [
                {"id": q["parameterId"], "type": q["btType"].split("-")[0].replace("BTParameterSpec", ""),
                 "name": q.get("parameterName"),
                 **({"enum": q.get("enumName"), "options": q.get("options")} if "Enum" in q["btType"] else {}),
                 **({"quantity": q.get("quantityType")} if "Quantity" in q["btType"] else {})}
                for q in s.get("parameters", [])]}
    (RESULTS / "featurespecs.json").write_text(json.dumps(keep, indent=1) + "\n")
    print(json.dumps(rec["baseplate"]), len(rec["bodies"]), "bodies,", len(keep), "feature specs kept")


# feature JSON ---------------------------------------------------------------
def q_ids(pid: str, ids: list[str]) -> dict:
    return {"btType": "BTMParameterQueryList-148", "parameterId": pid,
            "queries": [{"btType": "BTMIndividualQuery-138", "deterministicIds": ids}]}


def p_enum(pid: str, enum: str, v: str) -> dict:
    return {"btType": "BTMParameterEnum-145", "parameterId": pid, "enumName": enum, "value": v}


def p_qty(pid: str, e: str) -> dict:
    return {"btType": "BTMParameterQuantity-147", "parameterId": pid, "expression": e}


def p_bool(pid: str, v: bool) -> dict:
    return {"btType": "BTMParameterBoolean-144", "parameterId": pid, "value": v}


def p_str(pid: str, v: str) -> dict:
    return {"btType": "BTMParameterString-149", "parameterId": pid, "value": v}


def variable_feature(trim: float) -> dict:
    return {"btType": "BTMFeature-134", "featureType": "assignVariable", "name": "table_trim",
            "parameters": [p_enum("mode", "VariableMode", "ASSIGNED"),
                           p_enum("variableType", "VariableType", "LENGTH"), p_str("name", "table_trim"),
                           p_qty("lengthValue", f"{trim:g} mm"),
                           p_str("description", f"how much thinner the {TABLE_T:g} mm table gets; "
                                                "the doser sits this much lower")]}


def add_feature(c: Onshape, rec: dict, feature: dict) -> str:
    out = c.post(f"{ps(rec)}/features", json={"feature": feature})
    status = out.get("featureState", {}).get("featureStatus")
    fid = out["feature"]["featureId"]
    rec.setdefault("features", {})[feature["name"]] = {"featureId": fid, "status": status}
    save(rec)
    print(f"{feature['name']}: {fid} {status}")
    if status not in ("OK", "INFO"):
        raise RuntimeError(f"{feature['name']}: {out.get('featureState')}")
    return fid


def cmd_edit(c: Onshape, rec: dict, trim: float) -> None:
    feats = rec.get("features", {})
    if "table_trim" not in feats:
        add_feature(c, rec, variable_feature(trim))
    if "Thin the table" not in feats:
        add_feature(c, rec, {
            "btType": "BTMFeature-134", "featureType": "moveFace", "name": "Thin the table",
            "parameters": [p_enum("outputType", "MoveFaceOutputType", "MOVE"),
                           q_ids("moveFaces", rec["baseplate"]["underside"]),
                           p_enum("moveFaceType", "MoveFaceType", "OFFSET"),
                           p_qty("offsetDistance", "#table_trim"),
                           p_bool("oppositeDirection", True)]})
    if "Lower the doser" not in feats:
        movers = [b["id"] for b in rec["bodies"] if b["name"] != "board"]
        assert len(movers) == len(rec["bodies"]) - 1, "expected exactly one body named 'board'"
        add_feature(c, rec, {
            "btType": "BTMFeature-134", "featureType": "transform", "name": "Lower the doser",
            "parameters": [q_ids("entities", movers),
                           p_enum("transformType", "TransformType", "TRANSLATION_3D"),
                           p_qty("dx", "0 mm"), p_qty("dy", "0 mm"), p_qty("dz", "-#table_trim"),
                           p_bool("makeCopy", False)]})
    rec["table_trim_mm"] = trim
    save(rec)


def cmd_set(c: Onshape, rec: dict, trim: float) -> None:
    """Change #table_trim: one feature update, everything regenerates."""
    fid = rec["features"]["table_trim"]["featureId"]
    feat = variable_feature(trim)
    feat["featureId"] = fid
    out = c.post(f"{ps(rec)}/features/featureid/{fid}", json={"feature": feat})
    rec["table_trim_mm"] = trim
    rec["features"]["table_trim"]["status"] = out.get("featureState", {}).get("featureStatus")
    save(rec)
    print("table_trim ->", trim, rec["features"]["table_trim"]["status"])


def cmd_verify(c: Onshape, rec: dict, commit: str) -> None:
    trim = rec["table_trim_mm"]
    box = c.get(f"{ps(rec)}/boundingboxes")
    (RESULTS / "bbox_after.json").write_text(json.dumps(box, indent=1) + "\n")
    mp = c.get(f"{ps(rec)}/massproperties", params={"partId": rec["baseplate"]["partId"]})
    (RESULTS / "baseplate_massproperties_after.json").write_text(json.dumps(mp, indent=1) + "\n")
    shaded(c, rec, RENDERS / "onshape_after_right.png", "right")
    shaded(c, rec, RENDERS / "onshape_after_iso.png", "isometric")
    # the edited Part Studio back as STEP, for the local checks (compare_onshape.py)
    tr = c.post(f"{ps(rec)}/translations", json={
        "formatName": "STEP", "storeInDocument": False, "stepVersionString": "AP242",
        "flattenAssemblies": True, "includeExportIds": False})
    st = wait_translation(c, tr["id"], first=20, every=15, polls=10)
    r = c.get(f"/documents/d/{rec['documentId']}/externaldata/{st['resultExternalDataIds'][0]}",
              raw=True, headers={"Accept": "application/octet-stream"})
    out = Path(f"/tmp/os/onshape_after_trim{trim:g}.step")
    out.write_bytes(r.content)
    rec["export"] = {"file": str(out), "bytes": len(r.content), "table_trim_mm": trim}
    save(rec)
    version(c, rec, f"table {TABLE_T:g} -> {TABLE_T - trim:g} mm",
            f"#table_trim = {trim:g} mm: the baseplate's table is {TABLE_T - trim:g} mm thick and "
            f"everything on it sits {trim:g} mm lower (text-to-cad {commit})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["import", "inspect", "edit", "set", "verify"])
    ap.add_argument("--trim", type=float, default=3.0)
    ap.add_argument("--budget", type=int, default=30)
    ap.add_argument("--commit", default="8aae55e")
    a = ap.parse_args()
    RESULTS.mkdir(exist_ok=True)
    c, rec = Onshape(budget=a.budget, run=a.step), load()
    try:
        {"import": lambda: cmd_import(c, rec, a.commit), "inspect": lambda: cmd_inspect(c, rec),
         "edit": lambda: cmd_edit(c, rec, a.trim), "set": lambda: cmd_set(c, rec, a.trim),
         "verify": lambda: cmd_verify(c, rec, a.commit)}[a.step]()
    finally:
        rec.setdefault("api_calls", {})
        rec["api_calls"][a.step] = rec["api_calls"].get(a.step, 0) + c.calls
        save(rec)
        print(f"{a.step}: {c.calls} API calls")


if __name__ == "__main__":
    main()

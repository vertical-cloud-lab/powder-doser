"""Upload the current-design parts to Onshape and build the assembly.

1. creates a document owned by the "Vertical Cloud Lab" Onshape company
   (or reuses the one recorded in onshape_document.json),
2. imports every STEP in ``layout.placements()`` once (one Part Studio per
   file, parts renamed after the hardware),
3. creates an Assembly, inserts one instance per placement and sets its
   absolute transform from ``layout.py`` (tilt 0, the rig's home pose),
4. saves a shaded isometric view rendered by Onshape.

Needs ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY (an API key pair of an
account in the company).

    python3 onshape_build.py          # import what's missing + a new Assembly tab
                                      # in the document in onshape_document.json
    python3 onshape_build.py --new    # start a new document
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
from requests.auth import HTTPBasicAuth

import layout

HERE = Path(__file__).resolve().parent
API = "https://cad.onshape.com/api/v10"
COMPANY_NAME = "Vertical Cloud Lab"
DOC_NAME = "Powder doser - full assembly (current design)"
DOC_JSON = HERE / "onshape_document.json"
ASM_NAME = "Powder doser assembly"

# STEP file -> (Part Studio name, {solid name in the STEP: part name})
STEP_NAMES = {
    "fusion-step/baseplate.step": ("Baseplate", {"Body1": "Baseplate"}),
    "fusion-step/mounting-plate.step": ("Mounting plate", {
        "Spur Gear (28 teeth)": "Tilt gear 28T (stepper side)",
        "Spur Gear (28 teeth) (1)": "Tilt gear 28T (solenoid side)",
        "Body2": "Tilt gear arm (stepper side)",
        "Body3": "Mounting plate",
        "Body5": "Tilt gear arm (solenoid side)"}),
    "fusion-step/auger.step": ("Auger (threaded storage)", {"Shaft": "Auger"}),
    "fusion-step/auger-cap.step": ("Auger cap", {"Cap": "Auger cap"}),
    "fusion-step/brackets.step": ("Auger bracket", {"Body1": "Auger bracket"}),
    "fusion-step/tap-collar.step": ("Tap collar", {"Body1": "Tap collar"}),
    "fusion-step/stepper-pinion.step": ("Stepper pinion 20T", {"Spur Gear (20 teeth)": "Stepper pinion 20T"}),
    "fusion-step/servo-pinion.step": ("Servo pinion 14T", {"Spur Gear (14 teeth)": "Servo pinion 14T"}),
    "ai-step/tap-collar-base.step": ("Tap collar base (AI, PR 51)", {}),
    "purchased/nema11-11hs18-0674s.step": ("NEMA 11 stepper 11HS18-0674S", {}),
    "purchased/mg996r-servo.step": ("MG996R servo", {}),
    "purchased/adafruit-412-solenoid.step": ("Adafruit 412 solenoid", {}),
}
NAME_PROP = "57f3fb8efa3416c06701d60d"   # Onshape "Name" metadata property


class Onshape:
    def __init__(self):
        self.auth = HTTPBasicAuth(os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
        self.s = requests.Session()

    def req(self, method, path, **kw):
        kw.setdefault("timeout", 120)
        headers = kw.pop("headers", {})
        headers.setdefault("Accept", "application/json;charset=UTF-8; qs=0.09")
        for attempt in range(4):
            r = self.s.request(method, API + path, auth=self.auth, headers=headers, **kw)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(5 * (attempt + 1))
                continue
            break
        if not r.ok:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:500]}")
        return r.json() if r.content and "json" in r.headers.get("Content-Type", "") else r

    get = lambda self, p, **kw: self.req("GET", p, **kw)
    post = lambda self, p, **kw: self.req("POST", p, **kw)


def company_id(c: Onshape) -> str:
    for it in c.get("/companies")["items"]:
        if it["name"] == COMPANY_NAME:
            return it["id"]
    raise RuntimeError(f"not a member of {COMPANY_NAME}")


def renamed_step(src: Path, part_names: dict, product: str) -> bytes:
    """STEP text with the solid and product names replaced, so the imported
    parts come in with readable names."""
    txt = src.read_text(errors="replace")
    for old, new in part_names.items():
        txt = txt.replace(f"MANIFOLD_SOLID_BREP('{old}'", f"MANIFOLD_SOLID_BREP('{new}'")
    txt = re.sub(r"PRODUCT\('[^']*','[^']*'", f"PRODUCT('{product}','{product}'", txt)
    return txt.encode()


def import_step(c: Onshape, did: str, wid: str, rel: str) -> str:
    studio, names = STEP_NAMES[rel]
    data = renamed_step(layout.COMP / rel, names, studio)
    fname = f"{studio}.step"
    files = {"file": (fname, data, "application/step")}
    form = {"encodedFilename": fname, "fileContentLength": str(len(data)),
            "translate": "true", "flattenAssemblies": "false", "yAxisIsUp": "false",
            "storeInDocument": "false"}
    res = c.post(f"/blobelements/d/{did}/w/{wid}", files=files, data=form)
    tr = {"id": res.get("translationId") or res["id"]}
    for _ in range(120):
        st = c.get(f"/translations/{tr['id']}")
        if st["requestState"] == "DONE":
            return st["resultElementIds"][0]
        if st["requestState"] == "FAILED":
            raise RuntimeError(f"translation of {rel} failed: {st.get('failureReason')}")
        time.sleep(3)
    raise RuntimeError(f"translation of {rel} timed out")


def name_parts(c: Onshape, did: str, wid: str, eid: str, rel: str) -> list[dict]:
    parts = c.get(f"/parts/d/{did}/w/{wid}/e/{eid}")
    studio, names = STEP_NAMES[rel]
    if not names and len(parts) == 1 and parts[0]["name"] != studio:
        c.post(f"/metadata/d/{did}/w/{wid}/e/{eid}/p/{parts[0]['partId']}",
               json={"properties": [{"propertyId": NAME_PROP, "value": studio}]})
        parts[0]["name"] = studio
    return parts


def rename_element(c: Onshape, did: str, wid: str, eid: str, name: str) -> None:
    try:
        c.post(f"/metadata/d/{did}/w/{wid}/e/{eid}",
               json={"properties": [{"propertyId": NAME_PROP, "value": name}]})
    except RuntimeError as e:
        print("could not rename tab:", str(e)[:120])   # cosmetic only


def build(new_doc: bool) -> dict:
    c = Onshape()
    places = layout.placements()
    if not new_doc and DOC_JSON.exists():
        rec = json.loads(DOC_JSON.read_text())
        did, wid = rec["documentId"], rec["workspaceId"]
    else:
        cid = company_id(c)
        doc = c.post("/documents", json={
            "name": DOC_NAME, "ownerId": cid, "ownerType": 1, "isPublic": False,
            "description": "Fusion 360 parts (lab account) + AI tap-collar base + simplified "
                           "NEMA 11 / MG996R / Adafruit 412, placed by "
                           "vertical-cloud-lab/powder-doser cad/full-assembly/onshape (PR #170)."})
        did, wid = doc["id"], doc["defaultWorkspace"]["id"]
        rec = {"documentId": did, "workspaceId": wid, "owner": COMPANY_NAME}
    rec["url"] = f"https://cad.onshape.com/documents/{did}/w/{wid}"
    studios = rec.setdefault("partStudios", {})
    for rel in dict.fromkeys(p for p, _ in places.values()):
        if rel in studios:
            continue
        eid = import_step(c, did, wid, rel)
        parts = name_parts(c, did, wid, eid, rel)
        studios[rel] = {"elementId": eid, "parts": [
            {"partId": p["partId"], "name": p["name"]} for p in parts]}
        DOC_JSON.write_text(json.dumps(rec, indent=1) + "\n")
        print(f"imported {rel} -> {eid} ({len(parts)} part(s))", flush=True)

    aid = None
    for e in c.get(f"/documents/d/{did}/w/{wid}/elements"):
        if e["elementType"] == "ASSEMBLY" and e["name"] in ("Assembly 1", ASM_NAME):
            if not c.get(f"/assemblies/d/{did}/w/{wid}/e/{e['id']}")["rootAssembly"]["instances"]:
                aid = e["id"]           # reuse the empty default tab
                break
    if aid is None:
        aid = c.post(f"/assemblies/d/{did}/w/{wid}", json={"name": ASM_NAME})["id"]
    rename_element(c, did, wid, aid, ASM_NAME)
    order = []
    for name, (rel, M) in places.items():
        st = studios[rel]
        for p in st["parts"]:
            c.post(f"/assemblies/d/{did}/w/{wid}/e/{aid}/instances", json={
                "documentId": did, "elementId": st["elementId"], "partId": p["partId"],
                "isAssembly": False, "isWholePartStudio": False})
            order.append((name, st["elementId"], p["partId"], M))
    defn = c.get(f"/assemblies/d/{did}/w/{wid}/e/{aid}")
    insts = defn["rootAssembly"]["instances"]
    pool = {}
    for inst in insts:
        pool.setdefault((inst["elementId"], inst["partId"]), []).append(inst["id"])
    placed = []
    for name, eid, pid, M in order:
        iid = pool[(eid, pid)].pop(0)
        Mm = np.array(M, float).copy()
        Mm[:3, 3] /= 1000.0                         # mm -> m
        c.post(f"/assemblies/d/{did}/w/{wid}/e/{aid}/occurrencetransforms", json={
            "occurrences": [{"path": [iid]}], "transform": Mm.flatten().tolist(),
            "isRelative": False})
        placed.append({"placement": name, "instanceId": iid, "partId": pid})
    rec["assembly"] = {"elementId": aid, "instances": placed,
                       "url": f"https://cad.onshape.com/documents/{did}/w/{wid}/e/{aid}"}
    DOC_JSON.write_text(json.dumps(rec, indent=1) + "\n")
    print("assembly", rec["assembly"]["url"])
    return rec


def shaded_view(rec: dict, out: Path, view="isometric", w=1400, h=1000) -> None:
    c = Onshape()
    did, wid, aid = rec["documentId"], rec["workspaceId"], rec["assembly"]["elementId"]
    r = c.get(f"/assemblies/d/{did}/w/{wid}/e/{aid}/shadedviews",
              params={"viewMatrix": view, "outputHeight": h, "outputWidth": w,
                      "pixelSize": 0, "edges": "show", "useAntiAliasing": "true"})
    out.write_bytes(base64.b64decode(r["images"][0]))
    print("->", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", action="store_true", help="new document even if onshape_document.json exists")
    ap.add_argument("--view-only", action="store_true")
    a = ap.parse_args()
    rec = json.loads(DOC_JSON.read_text()) if a.view_only else build(a.new)
    shaded_view(rec, HERE.parent / "renders" / "onshape_assembly_iso.png")


if __name__ == "__main__":
    main()

"""Upload the current-design parts to Onshape and build the assembly.

1. creates a document owned by the "Vertical Cloud Lab" Onshape company
   (or reuses the one recorded in onshape_document.json),
2. imports every STEP in ``layout.placements()`` that is new (one Part
   Studio per file); a changed STEP replaces the geometry of its Part
   Studio in place (the blob its Import feature reads), so part ids, tabs
   and assembly instances stay; part names are kept in step with STEP_NAMES,
3. inserts one instance per placement in the assembly tab and sets its
   absolute transform from ``layout.py`` (tilt 0, the rig's home pose),
4. saves shaded views rendered by Onshape (renders/onshape_assembly_*.png).

Needs ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY (an API key pair of an
account in the company).

    python3 onshape_build.py          # sync the document in onshape_document.json
    python3 onshape_build.py --new    # start a new document
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import time
from pathlib import Path

import numpy as np
import requests
from requests.auth import HTTPBasicAuth

import sys

import layout

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import hardware  # noqa: E402
API = "https://cad.onshape.com/api/v10"
COMPANY_NAME = "Vertical Cloud Lab"
DOC_NAME = "Powder doser - full assembly (current design)"
DOC_JSON = HERE / "onshape_document.json"
ASM_NAME = "Powder doser assembly"

# STEP file -> (Part Studio name, {solid name in the STEP: part name}).
# Left/right as seen from the outlet end (stepper on the left).
STEP_NAMES = {
    "fusion-step/baseplate.step": ("Baseplate", {"Body1": "Baseplate"}),
    "fusion-step/mounting-plate.step": ("Mounting plate", {
        "Spur Gear (28 teeth)": "Tilt gear 28T (left)",
        "Spur Gear (28 teeth) (1)": "Tilt gear 28T (right)",
        "Body2": "Tilt gear arm (left)",
        "Body3": "Mounting plate",
        "Body5": "Tilt gear arm (right)"}),
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
    "mount/mounting-board.step": ("Mounting board (any flat board, 1.5 in thick)", {}),
}
for _k in hardware.HARDWARE:   # fasteners, in their seat frames (hardware.py)
    _pn = hardware.MCMASTER.get(_k, "")
    STEP_NAMES[f"hardware/{_k}.step"] = (
        f"{hardware.SHORT[_k]}" + (f" (McMaster {_pn})" if _pn else ""), {})
NAME_PROP = "57f3fb8efa3416c06701d60d"   # Onshape "Name" metadata property


def all_placements() -> dict:
    """layout.py's parts and mounting board, plus every fastener from
    hardware.py (with the board's wood screws)."""
    places = {**layout.placements(), **layout.mount_placements()}
    for name, key, _, M in hardware.fastener_placements(with_board=True):
        places[name] = (f"hardware/{key}.step", M)
    return places


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


def _import_feature(c: Onshape, did: str, wid: str, eid: str):
    """(features response, the importForeign feature, its blob element id)."""
    fs = c.get(f"/partstudios/d/{did}/w/{wid}/e/{eid}/features")
    for ft in fs["features"]:
        if ft["featureType"] == "importForeign":
            for prm in ft["parameters"]:
                if prm["parameterId"] == "blobData":
                    return fs, ft, prm["namespace"].split("::")[0][1:]
    return fs, None, None


def update_in_place(c: Onshape, did: str, wid: str, eid: str, rel: str) -> bool:
    """Replace the geometry of an imported Part Studio without a new tab:
    upload the new STEP over the blob its Import feature reads, then point
    the feature at the blob's new microversion.  Part ids (and so the
    assembly's instances) are kept.  False if the studio isn't a plain
    single-import one."""
    fs, ft, blob = _import_feature(c, did, wid, eid)
    if ft is None:
        return False
    studio, names = STEP_NAMES[rel]
    data = renamed_step(layout.COMP / rel, names, studio)
    fname = f"{studio}.step"
    c.post(f"/blobelements/d/{did}/w/{wid}/e/{blob}",
           files={"file": (fname, data, "application/step")},
           data={"encodedFilename": fname, "fileContentLength": str(len(data))})
    mv = next(e["microversionId"] for e in c.get(f"/documents/d/{did}/w/{wid}/elements")
              if e["id"] == blob)
    for prm in ft["parameters"]:
        if prm["parameterId"] == "blobData":
            prm["namespace"] = f"e{blob}::m{mv}"
    fs = c.get(f"/partstudios/d/{did}/w/{wid}/e/{eid}/features")
    c.post(f"/partstudios/d/{did}/w/{wid}/e/{eid}/features/featureid/{ft['featureId']}",
           json={"feature": ft, "serializationVersion": fs["serializationVersion"],
                 "sourceMicroversion": fs["sourceMicroversion"]})
    return True


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


def _sha(rel: str) -> str:
    """Hash of the STEP file minus its FILE_NAME header (export time stamp),
    so regenerating an unchanged part doesn't trigger a re-import."""
    txt = (layout.COMP / rel).read_text(errors="replace")
    return hashlib.sha256(re.sub(r"FILE_NAME\(.*?\);", "", txt, count=1, flags=re.S).encode()).hexdigest()


def desired_name(rel: str, solid: str | None) -> str:
    studio, names = STEP_NAMES[rel]
    return names.get(solid, studio) if solid else studio


def sync_part_names(c: Onshape, rec: dict) -> None:
    """Rename parts (metadata only, geometry untouched) to STEP_NAMES."""
    did, wid = rec["documentId"], rec["workspaceId"]
    for rel, st in rec["partStudios"].items():
        if rel not in STEP_NAMES:      # a file no longer in the assembly
            continue
        for p in st["parts"]:
            want = desired_name(rel, p.get("solid"))
            if p["name"] != want:
                c.post(f"/metadata/d/{did}/w/{wid}/e/{st['elementId']}/p/{p['partId']}",
                       json={"properties": [{"propertyId": NAME_PROP, "value": want}]})
                print(f"renamed {p['name']!r} -> {want!r}")
                p["name"] = want


def sync_studios(c: Onshape, rec: dict, places: dict) -> None:
    """Import every STEP that is new since the recorded upload, and update
    changed ones in place.  If that fails, a changed file gets a fresh Part
    Studio and the old tab is renamed "(superseded)", because the API key
    has no delete scope."""
    did, wid = rec["documentId"], rec["workspaceId"]
    studios = rec.setdefault("partStudios", {})
    for rel in dict.fromkeys(p for p, _ in places.values()):
        sha = _sha(rel)
        old = studios.get(rel)
        if old and old.get("sha256", sha) == sha:
            old["sha256"] = sha
            continue
        if old and not old.get("superseded"):
            try:
                if update_in_place(c, did, wid, old["elementId"], rel):
                    ids = {p["partId"] for p in c.get(f"/parts/d/{did}/w/{wid}/e/{old['elementId']}")}
                    if ids == {p["partId"] for p in old["parts"]}:
                        old["sha256"] = sha
                        DOC_JSON.write_text(json.dumps(rec, indent=1) + "\n")
                        print(f"updated {rel} in place", flush=True)
                        continue
                    print(f"{rel}: part ids changed in place; re-importing")
            except RuntimeError as e:
                print(f"{rel}: in-place update failed ({str(e)[:160]}); re-importing")
        eid = import_step(c, did, wid, rel)
        parts = name_parts(c, did, wid, eid, rel)
        if old:
            rename_element(c, did, wid, old["elementId"],
                           f"{STEP_NAMES[rel][0]} (superseded, safe to delete)")
            rename_element(c, did, wid, eid, STEP_NAMES[rel][0])
        inv = {v: k for k, v in STEP_NAMES[rel][1].items()}
        studios[rel] = {"elementId": eid, "sha256": sha, "parts": [
            {"partId": p["partId"], "name": p["name"], "solid": inv.get(p["name"])} for p in parts]}
        DOC_JSON.write_text(json.dumps(rec, indent=1) + "\n")
        print(f"imported {rel} -> {eid} ({len(parts)} part(s))", flush=True)
    # files that left the assembly (e.g. a fastener size that changed)
    wanted = {p for p, _ in places.values()}
    for rel, st in studios.items():
        if rel not in wanted and not st.get("superseded"):
            rename_element(c, did, wid, st["elementId"],
                           f"{Path(rel).stem} (superseded, safe to delete)")
            st["superseded"] = True
            print(f"superseded {rel}")
    DOC_JSON.write_text(json.dumps(rec, indent=1) + "\n")


def sync_assembly(c: Onshape, rec: dict, places: dict) -> None:
    """One instance per (placement, part), each at its layout.py transform.
    Instances this script recorded for the same placement and part are
    reused (their transforms are reset to layout.py); ones it recorded that
    are no longer wanted are deleted.  Instances added by hand are left alone."""
    did, wid = rec["documentId"], rec["workspaceId"]
    studios = rec["partStudios"]
    aid = rec.get("assembly", {}).get("elementId")
    if aid is None:
        for e in c.get(f"/documents/d/{did}/w/{wid}/elements", params={"elementType": "ASSEMBLY"}):
            if e["name"] in ("Assembly 1", ASM_NAME) and not c.get(
                    f"/assemblies/d/{did}/w/{wid}/e/{e['id']}")["rootAssembly"]["instances"]:
                aid = e["id"]           # reuse the empty default tab
                break
        if aid is None:
            aid = c.post(f"/assemblies/d/{did}/w/{wid}", json={"name": ASM_NAME})["id"]
        rename_element(c, did, wid, aid, ASM_NAME)
    base = f"/assemblies/d/{did}/w/{wid}/e/{aid}"
    live = {i["id"]: i for i in c.get(base)["rootAssembly"]["instances"]}
    ours = [r["instanceId"] for r in rec.get("assembly", {}).get("instances", [])]
    recorded = {(r["placement"], r["partId"], r.get("elementId", live.get(r["instanceId"], {}).get("elementId"))): r["instanceId"]
                for r in rec.get("assembly", {}).get("instances", []) if r["instanceId"] in live}
    placed, keep = [], set()
    for name, (rel, M) in places.items():
        st = studios[rel]
        for p in st["parts"]:
            key = (name, p["partId"], st["elementId"])
            iid = recorded.get(key)
            if iid is None:
                before = set(live)
                c.post(f"{base}/instances", json={
                    "documentId": did, "elementId": st["elementId"], "partId": p["partId"],
                    "isAssembly": False, "isWholePartStudio": False})
                live = {i["id"]: i for i in c.get(base)["rootAssembly"]["instances"]}
                (iid,) = set(live) - before
            keep.add(iid)
            Mm = np.array(M, float).copy()
            Mm[:3, 3] /= 1000.0                     # mm -> m
            c.post(f"{base}/occurrencetransforms", json={
                "occurrences": [{"path": [iid]}], "transform": Mm.flatten().tolist(),
                "isRelative": False})
            placed.append({"placement": name, "instanceId": iid, "elementId": st["elementId"],
                           "partId": p["partId"], "part": p["name"]})
    stale = [i for i in ours if i in live and i not in keep]   # never touches hand-added parts
    if stale:
        c.post(f"{base}/modify", json={"deleteInstances": stale, "editDescription": "remove stale parts"})
        print(f"deleted {len(stale)} stale instance(s)")
    rec["assembly"] = {"elementId": aid, "instances": placed,
                       "url": f"https://cad.onshape.com/documents/{did}/w/{wid}/e/{aid}"}
    DOC_JSON.write_text(json.dumps(rec, indent=1) + "\n")
    print("assembly", rec["assembly"]["url"])


def build(new_doc: bool) -> dict:
    c = Onshape()
    hardware.export_steps()
    places = all_placements()
    if not new_doc and DOC_JSON.exists():
        rec = json.loads(DOC_JSON.read_text())
    else:
        doc = c.post("/documents", json={
            "name": DOC_NAME, "ownerId": company_id(c), "ownerType": 1, "isPublic": False,
            "description": "Fusion 360 parts (lab account) + AI tap-collar base + simplified "
                           "NEMA 11 / MG996R / Adafruit 412, placed by "
                           "vertical-cloud-lab/powder-doser cad/full-assembly/onshape (PR #170)."})
        rec = {"documentId": doc["id"], "workspaceId": doc["defaultWorkspace"]["id"],
               "owner": COMPANY_NAME}
    rec["url"] = f"https://cad.onshape.com/documents/{rec['documentId']}/w/{rec['workspaceId']}"
    sync_studios(c, rec, places)
    sync_part_names(c, rec)
    sync_assembly(c, rec, places)
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
    for view in ("isometric", "front", "top", "right"):
        tag = "iso" if view == "isometric" else view
        shaded_view(rec, HERE.parent / "renders" / f"onshape_assembly_{tag}.png", view=view)


if __name__ == "__main__":
    main()

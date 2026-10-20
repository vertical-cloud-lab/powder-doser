"""The Onshape side that fsgen doesn't do itself, for the native auger (issue #172).

Adapted from cad/fsgen/v0.2.0/onshape_doc.py (issue #171). Every request goes through fsgen's own
client, so it lands in the same call ledger (``.fsgen_api_ledger.jsonl``) as fsgen's pushes.

    python onshape_doc.py create              # 2 calls: company id, new company-owned document; fsgen will
                                              #   build in its default "Part Studio 1" (no extra tab)
    fsgen studio push auger.fs --name "Auger" --document <URL> --metrics --budget 30
    python onshape_doc.py rename              # 1 call: tab "Part Studio 1" -> "Auger"
    python onshape_doc.py mass                # 1 call: parts, volume, centroid, area
    python onshape_doc.py views [tag]         # 1 call per view
    python onshape_doc.py tree                # 1 call: the feature tree as Onshape stores it
    python onshape_doc.py export [stem]       # STEP export (translation, polls, download)
    python onshape_doc.py version "name" "description"   # 1 call

Run from this folder with ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY set.
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from fsgen.native import build as nb
from fsgen.onshape import Onshape

HERE = Path(__file__).resolve().parent
REC = HERE / "onshape_document.json"
COMPANY = "Vertical Cloud Lab"
DOC_NAME = "Powder doser auger - native feature tree (#172)"
STUDIO = "Auger"
RENDERS = HERE / "renders" / "onshape"
# Onshape view matrices (row-major 3x4): isometric, and a view from the front (-Y) side
VIEWS = {"iso": "isometric",
         "front": "1,0,0,0,0,0,1,0,0,-1,0,0"}


def load() -> dict:
    return json.loads(REC.read_text()) if REC.exists() else {}


def save(rec: dict) -> None:
    REC.write_text(json.dumps(rec, indent=1) + "\n")


def studio(rec: dict) -> nb.StudioState:
    st = nb.find_state(STUDIO, rec["documentId"], rec["workspaceId"])
    if st is None:
        raise SystemExit(f"no fsgen state for {STUDIO!r}: run create first")
    return st


def cmd_create(o: Onshape, rec: dict) -> None:
    if "documentId" in rec:
        print("already created:", rec["url"])
        return
    cid = next(it["id"] for it in o.get("companies")["items"] if it["name"] == COMPANY)
    doc = o.post("documents", {
        "name": DOC_NAME, "ownerId": cid, "ownerType": 1, "isPublic": False,
        "description": "The powder doser's auger tube as a native, variable-driven feature tree, pushed with "
                       "fsgen 0.2.0 (github.com/Lucasfrit/onshape-fsgen) from vertical-cloud-lab/powder-doser "
                       "cad/onshape-auger/auger.fs (issue #172). Same part as cad/text-to-cad/src/parts/auger.py "
                       "(PR #176), which matches the lab's Fusion 360 auger. Edit the variables in the "
                       "'Auger variables' tab."})
    did, wid = doc["id"], doc["defaultWorkspace"]["id"]
    eid = doc.get("defaultElementId")
    rec.update(documentId=did, workspaceId=wid, owner=COMPANY, public=doc.get("public"),
               url=f"https://cad.onshape.com/documents/{did}/w/{wid}", defaultElementId=eid)
    save(rec)
    if eid:
        # let fsgen build in the default "Part Studio 1" instead of adding a second tab
        nb.save_state(nb.StudioState(did, wid, eid, STUDIO, key=f"{STUDIO}@{wid}"))
    print("document:", rec["url"], "public:", rec["public"], "default element:", eid)
    print("push with: --document", rec["url"])


def cmd_rename(o: Onshape, rec: dict) -> None:
    st = studio(rec)
    o.post(f"metadata/d/{st.did}/w/{st.wid}/e/{st.eid}",
           {"properties": [{"propertyId": "57f3fb8efa3416c06701d60d", "value": STUDIO}]})
    print("tab renamed:", STUDIO)


def cmd_version(o: Onshape, rec: dict, name: str, description: str) -> None:
    v = o.post(f"documents/d/{rec['documentId']}/versions",
               {"documentId": rec["documentId"], "workspaceId": rec["workspaceId"],
                "name": name, "description": description})
    rec.setdefault("versions", []).append({"id": v["id"], "name": name, "description": description,
                                           "url": f"https://cad.onshape.com/documents/{rec['documentId']}/v/{v['id']}"})
    save(rec)
    print("version:", name, v["id"])


def cmd_views(o: Onshape, rec: dict, tag: str, only: str | None) -> None:
    st = studio(rec)
    for view, matrix in VIEWS.items():
        if only and view != only:
            continue
        r = o.get(f"partstudios/d/{st.did}/w/{st.wid}/e/{st.eid}/shadedviews",
                  params={"viewMatrix": matrix, "outputHeight": 900, "outputWidth": 1400, "pixelSize": 0,
                          "edges": "show", "useAntiAliasing": "true"})
        out = RENDERS / f"{tag}_{view}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(r["images"][0]))
        print("->", out.relative_to(HERE))


def cmd_tree(o: Onshape, rec: dict) -> None:
    st = studio(rec)
    feats = o.get(f"partstudios/d/{st.did}/w/{st.wid}/e/{st.eid}/features")
    out = HERE / "results" / "onshape_features.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(feats, indent=1) + "\n")
    for f in feats["features"]:
        print(f"  {f['featureType']:16s} {f['name']}")
    print("->", out.relative_to(HERE))


def cmd_mass(o: Onshape, rec: dict, tag: str) -> None:
    """Volume, centroid and area per part in one call (the centroid shows the flight's handedness)."""
    st = studio(rec)
    mp = o.get(f"partstudios/d/{st.did}/w/{st.wid}/e/{st.eid}/massproperties", params={"massAsGroup": "false"})
    out = HERE / "results" / f"onshape_massproperties_{tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(mp, indent=1) + "\n")
    for k, v in (mp.get("bodies") or {}).items():
        if k == "-all-":
            continue
        print(k, "volume mm3", round(v["volume"][0] * 1e9, 3), "area mm2", round(v["periphery"][0] * 1e6, 3),
              "centroid mm", [round(c * 1e3, 4) for c in v["centroid"][:3]])
    print("->", out.relative_to(HERE))


def cmd_export(o: Onshape, rec: dict, stem: str) -> None:
    st = studio(rec)
    files = nb.export_studio(o, st, HERE / "results" / "onshape_export", stem, ("step",))
    print("exported:", [str(f.relative_to(HERE)) for f in files])


def cmd_status(o: Onshape, rec: dict) -> None:
    st = studio(rec)
    s = nb.check_statuses(o, st, [f["fid"] for f in st.features])
    for f in st.features:
        print(f"  {s.get(f['fid'], '?'):8s} {f['name']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["create", "rename", "version", "views", "tree", "export", "mass", "status"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--only", choices=list(VIEWS), help="views: just this one")
    ap.add_argument("--budget", type=int, default=10)
    a = ap.parse_args()
    o = Onshape(budget=a.budget, purpose=f"onshape_doc {a.cmd}")
    rec = load()
    if a.cmd == "create":
        cmd_create(o, rec)
    elif a.cmd == "rename":
        cmd_rename(o, rec)
    elif a.cmd == "version":
        cmd_version(o, rec, a.args[0], a.args[1] if len(a.args) > 1 else "")
    elif a.cmd == "tree":
        cmd_tree(o, rec)
    elif a.cmd == "views":
        cmd_views(o, rec, a.args[0] if a.args else "final", a.only)
    elif a.cmd == "export":
        cmd_export(o, rec, a.args[0] if a.args else "auger_onshape")
    elif a.cmd == "mass":
        cmd_mass(o, rec, a.args[0] if a.args else "final")
    else:
        cmd_status(o, rec)
    print(o.summary())

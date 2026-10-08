"""The Onshape side that fsgen doesn't do itself (issue #171).

fsgen pushes Part Studios into a document it creates as private ("fsgen-workspace"). This
script makes the document public and owned by the Vertical Cloud Lab company instead, points
fsgen at it, and adds versions, Onshape renders and the STEP export used for the checks.
Every request goes through fsgen's own client, so it lands in the same call ledger
(``.fsgen_api_ledger.jsonl``) as fsgen's pushes.

    python onshape_doc.py create                # 2 calls: company id, new public document
    fsgen studio push parts/baseplate_servos_above.fs --name "Baseplate (servos above)" --metrics
    python onshape_doc.py version "name" "description"     # 1 call
    python onshape_doc.py views                 # 1 call per view
    python onshape_doc.py export                # STEP export (translation, polls, download)

Run from this folder with ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY set.
"""
from __future__ import annotations

import argparse
import base64
import json
import time
from pathlib import Path

from fsgen.native import build as nb
from fsgen.onshape import Onshape

HERE = Path(__file__).resolve().parent
REC = HERE / "onshape_document.json"
COMPANY = "Vertical Cloud Lab"
DOC_NAME = "Powder doser baseplate, servos above - fsgen native tree (#171)"
STUDIO = "Baseplate (servos above)"
RENDERS = HERE / "renders" / "onshape"
# Onshape view matrices (row-major 3x4): isometric and a view from the right (+X) side
VIEWS = {"iso": "isometric",
         "right": "0,1,0,0,0,0,1,0,1,0,0,0"}


def load() -> dict:
    return json.loads(REC.read_text()) if REC.exists() else {}


def save(rec: dict) -> None:
    REC.write_text(json.dumps(rec, indent=1) + "\n")


def studio(rec: dict) -> nb.StudioState:
    return nb.StudioState(**nb.load_states()[STUDIO])


def cmd_create(o: Onshape, rec: dict) -> None:
    if "documentId" in rec:
        print("already created:", rec["url"])
        return
    cid = next(it["id"] for it in o.get("companies")["items"] if it["name"] == COMPANY)
    doc = o.post("documents", {
        "name": DOC_NAME, "ownerId": cid, "ownerType": 1, "isPublic": True,
        "description": "Generated with fsgen (github.com/Lucasfrit/onshape-fsgen) from "
                       "vertical-cloud-lab/powder-doser cad/fsgen/parts/baseplate_servos_above.fs; same spec "
                       "as cad/text-to-cad/src/parts/baseplate.py (PR #176). The tower and cradle sketches "
                       "are re-sent by fsgen when #plateThickness or #hingeDrop change: edit the .fs and "
                       "push again rather than changing those two variables here."})
    did, wid = doc["id"], doc["defaultWorkspace"]["id"]
    rec.update(documentId=did, workspaceId=wid, owner=COMPANY, public=doc.get("public"),
               url=f"https://cad.onshape.com/documents/{did}/w/{wid}",
               defaultElementId=doc.get("defaultElementId"))
    save(rec)
    # fsgen reads the document from this file instead of creating its private "fsgen-workspace"
    Path(".fsgen_workspace.json").write_text(json.dumps(
        {"did": did, "wid": wid, "fs": "", "part": "", "eval": ""}, indent=2))
    print("document:", rec["url"], "public:", rec["public"])


def cmd_version(o: Onshape, rec: dict, name: str, description: str) -> None:
    v = o.post(f"documents/d/{rec['documentId']}/versions",
               {"documentId": rec["documentId"], "workspaceId": rec["workspaceId"],
                "name": name, "description": description})
    rec.setdefault("versions", []).append({"id": v["id"], "name": name, "description": description,
                                           "url": f"https://cad.onshape.com/documents/{rec['documentId']}/v/{v['id']}"})
    save(rec)
    print("version:", name, v["id"])


def cmd_views(o: Onshape, rec: dict, tag: str) -> None:
    st = studio(rec)
    for view, matrix in VIEWS.items():
        r = o.get(f"partstudios/d/{st.did}/w/{st.wid}/e/{st.eid}/shadedviews",
                  params={"viewMatrix": matrix, "outputHeight": 900, "outputWidth": 1400, "pixelSize": 0,
                          "edges": "show", "useAntiAliasing": "true"})
        out = RENDERS / f"{tag}_{view}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(r["images"][0]))
        print("->", out.relative_to(HERE))


def cmd_export(o: Onshape, rec: dict, tag: str) -> None:
    st = studio(rec)
    files = nb.export_studio(o, st, HERE / "results" / "onshape_export", tag, ("step",))
    print("exported:", [str(f.relative_to(HERE)) for f in files])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["create", "version", "views", "export"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--budget", type=int, default=10)
    a = ap.parse_args()
    o = Onshape(budget=a.budget, purpose=f"onshape_doc {a.cmd}")
    rec = load()
    t0 = time.time()
    if a.cmd == "create":
        cmd_create(o, rec)
    elif a.cmd == "version":
        cmd_version(o, rec, a.args[0], a.args[1] if len(a.args) > 1 else "")
    elif a.cmd == "views":
        cmd_views(o, rec, a.args[0] if a.args else "final")
    else:
        cmd_export(o, rec, a.args[0] if a.args else "baseplate_servos_above_onshape")
    print(o.summary())

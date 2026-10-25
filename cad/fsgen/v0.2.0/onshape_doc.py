"""The Onshape side that fsgen doesn't do itself, for the fsgen 0.2.0 repeat (issue #171).

Same job as ``../onshape_doc.py`` (fsgen 0.1), adapted to 0.2.0: fsgen now pushes into an existing
document with ``--document <URL>``, so ``create`` no longer writes ``.fsgen_workspace.json``, and
fsgen's saved state is keyed ``"<Part Studio name>@<workspace id>"``, so a branch gets its own
entry in the same ``.fsgen_native.json``. Every request goes through fsgen's own client, so it
lands in the same call ledger (``.fsgen_api_ledger.jsonl``) as fsgen's pushes.

    python onshape_doc.py create                       # 2 calls: company id, new public document
    fsgen studio push baseplate_servos_above.fs --name "Baseplate (servos above)" --document <URL> --metrics
    python onshape_doc.py version "name" "description" # 1 call
    python onshape_doc.py branch "name"                # 1 call: branch from the last version
    python onshape_doc.py views [tag] [--ws W] [--only iso]   # 1 call per view
    python onshape_doc.py tree                         # 1 call: the feature tree as Onshape stores it
    python onshape_doc.py export [stem]                # STEP export (translation, polls, download)
    python onshape_doc.py setvars NAME=MM ... --ws W   # 1 call: change variables in Onshape's Variable
                                                       #   Studio only, like an edit in the Onshape UI
    python onshape_doc.py mass --ws W                  # 1 call: parts, volume, area
    python onshape_doc.py status --ws W                # 1 call: every feature's status

``--ws`` is "main" (default) or a branch name from ``onshape_document.json``. Run from this folder
with ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY set.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import time
from pathlib import Path

from fsgen.native import build as nb
from fsgen.native.script import trace
from fsgen.onshape import Onshape

HERE = Path(__file__).resolve().parent
REC = HERE / "onshape_document.json"
COMPANY = "Vertical Cloud Lab"
DOC_NAME = "Powder doser baseplate, servos above - fsgen 0.2.0 native tree (#171)"
STUDIO = "Baseplate (servos above)"
SCRIPT = HERE / "baseplate_servos_above.fs"
RENDERS = HERE / "renders" / "onshape"
# Onshape view matrices (row-major 3x4): isometric and a view from the right (+X) side
VIEWS = {"iso": "isometric",
         "right": "0,1,0,0,0,0,1,0,1,0,0,0"}


def load() -> dict:
    return json.loads(REC.read_text()) if REC.exists() else {}


def save(rec: dict) -> None:
    REC.write_text(json.dumps(rec, indent=1) + "\n")


def workspace(rec: dict, ws: str) -> str:
    if ws == "main":
        return rec["workspaceId"]
    return next(b["workspaceId"] for b in rec.get("branches", []) if b["name"] == ws)


def studio(rec: dict, ws: str = "main") -> nb.StudioState:
    st = nb.find_state(STUDIO, rec["documentId"], workspace(rec, ws))
    if st is None:
        raise SystemExit(f"no fsgen state for {STUDIO!r} in workspace {ws!r}: push or branch first")
    return st


def cmd_create(o: Onshape, rec: dict) -> None:
    if "documentId" in rec:
        print("already created:", rec["url"])
        return
    cid = next(it["id"] for it in o.get("companies")["items"] if it["name"] == COMPANY)
    doc = o.post("documents", {
        "name": DOC_NAME, "ownerId": cid, "ownerType": 1, "isPublic": True,
        "description": "Generated with fsgen 0.2.0 (github.com/Lucasfrit/onshape-fsgen) from "
                       "vertical-cloud-lab/powder-doser cad/fsgen/v0.2.0/baseplate_servos_above.fs; same spec "
                       "as cad/text-to-cad/src/parts/baseplate.py (PR #176). A repeat of the fsgen 0.1 study "
                       "in cad/fsgen. See cad/fsgen/v0.2.0/README.md for which variables follow an edit "
                       "made here in the Variable Studio."})
    did, wid = doc["id"], doc["defaultWorkspace"]["id"]
    rec.update(documentId=did, workspaceId=wid, owner=COMPANY, public=doc.get("public"),
               url=f"https://cad.onshape.com/documents/{did}/w/{wid}",
               defaultElementId=doc.get("defaultElementId"))
    save(rec)
    print("document:", rec["url"], "public:", rec["public"])
    print("push with: --document", rec["url"])


def cmd_version(o: Onshape, rec: dict, name: str, description: str) -> None:
    v = o.post(f"documents/d/{rec['documentId']}/versions",
               {"documentId": rec["documentId"], "workspaceId": rec["workspaceId"],
                "name": name, "description": description})
    rec.setdefault("versions", []).append({"id": v["id"], "name": name, "description": description,
                                           "url": f"https://cad.onshape.com/documents/{rec['documentId']}/v/{v['id']}"})
    save(rec)
    print("version:", name, v["id"])


def cmd_branch(o: Onshape, rec: dict, name: str) -> None:
    """Branch from the last version and give fsgen a state entry for the branch.

    Element and feature ids are kept in a branch, but fsgen 0.2.0 looks its state up by
    "<name>@<workspace id>", so without this entry ``--document <branch URL>`` would make a second
    Part Studio in the branch instead of updating the branched one."""
    v = rec["versions"][-1]
    ws = o.post(f"documents/d/{rec['documentId']}/workspaces",
                {"name": name, "versionId": v["id"], "description": f"branched from version {v['name']}"})
    url = f"https://cad.onshape.com/documents/{rec['documentId']}/w/{ws['id']}"
    rec.setdefault("branches", []).append({"name": name, "workspaceId": ws["id"], "fromVersion": v["id"], "url": url})
    save(rec)
    st = studio(rec)
    st.wid, st.key = ws["id"], f"{STUDIO}@{ws['id']}"
    nb.save_state(st)
    print("branch:", name, url)


def cmd_views(o: Onshape, rec: dict, tag: str, ws: str, only: str | None) -> None:
    st = studio(rec, ws)
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
        print(f"  {f['featureType']:12s} {f['name']}")
    print("->", out.relative_to(HERE))


def cmd_export(o: Onshape, rec: dict, stem: str) -> None:
    st = studio(rec)
    files = nb.export_studio(o, st, HERE / "results" / "onshape_export", stem, ("step",))
    print("exported:", [str(f.relative_to(HERE)) for f in files])


def variables_with(values: dict[str, float]) -> list[dict]:
    """The script's Variable Studio contents with some values (mm) changed, as fsgen would send them."""
    src = SCRIPT.read_text()
    for name, mm in values.items():
        src, n = re.subn(rf'variable\(context, "{name}", [^)]*\)', f'variable(context, "{name}", {mm:g} * millimeter)', src)
        if n != 1:
            raise SystemExit(f"variable {name!r} not found in {SCRIPT.name}")
    return trace(src).variable_list


def cmd_setvars(o: Onshape, rec: dict, ws: str, assignments: list[str]) -> None:
    """Change variables in the Variable Studio only (no feature is re-sent, fsgen's state is left alone):
    what an edit in Onshape's UI does, to see whether the tree follows the variables by itself."""
    if ws == "main":
        raise SystemExit("setvars: use a branch, main keeps the design")
    st = studio(rec, ws)
    values = {a.split("=")[0]: float(a.split("=")[1]) for a in assignments}
    o.post(f"variables/d/{st.did}/w/{st.wid}/e/{st.vs_eid}/variables", variables_with(values))
    b = next(b for b in rec["branches"] if b["name"] == ws)
    b.setdefault("variableStudioEdits", []).append({"values_mm": values, "t": time.strftime("%Y-%m-%dT%H:%M:%S")})
    save(rec)
    print("Variable Studio set:", values)


def cmd_mass(o: Onshape, rec: dict, ws: str) -> None:
    m = nb.studio_metrics(o, studio(rec, ws))
    print(json.dumps(m))


def cmd_status(o: Onshape, rec: dict, ws: str) -> None:
    st = studio(rec, ws)
    s = nb.check_statuses(o, st, [f["fid"] for f in st.features])
    for f in st.features:
        print(f"  {s.get(f['fid'], '?'):6s} {f['name']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["create", "version", "branch", "views", "tree", "export", "setvars", "mass",
                                    "status"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--ws", default="main", help='"main" or a branch name')
    ap.add_argument("--only", choices=list(VIEWS), help="views: just this one")
    ap.add_argument("--budget", type=int, default=10)
    a = ap.parse_args()
    o = Onshape(budget=a.budget, purpose=f"onshape_doc {a.cmd}" + (f" ({a.ws})" if a.ws != "main" else ""))
    rec = load()
    if a.cmd == "create":
        cmd_create(o, rec)
    elif a.cmd == "version":
        cmd_version(o, rec, a.args[0], a.args[1] if len(a.args) > 1 else "")
    elif a.cmd == "branch":
        cmd_branch(o, rec, a.args[0])
    elif a.cmd == "tree":
        cmd_tree(o, rec)
    elif a.cmd == "views":
        cmd_views(o, rec, a.args[0] if a.args else "final", a.ws, a.only)
    elif a.cmd == "export":
        cmd_export(o, rec, a.args[0] if a.args else "baseplate_servos_above_onshape")
    elif a.cmd == "setvars":
        cmd_setvars(o, rec, a.ws, a.args)
    elif a.cmd == "mass":
        cmd_mass(o, rec, a.ws)
    else:
        cmd_status(o, rec, a.ws)
    print(o.summary())

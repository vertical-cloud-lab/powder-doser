"""The Onshape side that fsgen doesn't do itself, for the servos-above doser's native parts (issue #172).

Adapted from cad/fsgen/v0.2.0/onshape_doc.py (issue #171). Every request goes through fsgen's own
client, so it lands in the same call ledger (``.fsgen_api_ledger.jsonl``) as fsgen's pushes. One document
holds one Part Studio per printed part (``--studio``, the name the part was pushed under) and the assembly.

    python onshape_doc.py create              # 2 calls: company id, new company-owned document
    fsgen studio push parts/auger.fs --name "Auger" --document <URL> --metrics --budget 30
    python onshape_doc.py adopt --studio S    # 2 calls: rebuild fsgen's state for a studio pushed earlier
                                              #   (elements + feature tree), so the next push updates in place
    python onshape_doc.py rename --studio S   # 1 call: tab "Part Studio 1" -> S
    python onshape_doc.py rename-doc          # 1 call: document name and description
    python onshape_doc.py share               # 1 call: share with the Vertical Cloud Lab company
    python onshape_doc.py mass --studio S     # 1 call: parts, volume, centroid, area
    python onshape_doc.py views --studio S [tag]   # 1 call per view
    python onshape_doc.py tree --studio S     # 1 call: the feature tree as Onshape stores it
    python onshape_doc.py export --studio S [stem] # STEP export (translation, polls, download)
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
DOC_NAME = "Powder doser, servos above - native feature trees (#172)"
DOC_DESCRIPTION = (
    "The servos-above powder doser's printed parts as native, variable-driven feature trees (one Part Studio "
    "each, variables in each part's Variable Studio), pushed with fsgen 0.2.0 (github.com/Lucasfrit/onshape-fsgen) "
    "from vertical-cloud-lab/powder-doser cad/onshape-servos-above/parts/*.fs (issue #172). Same parts as "
    "text-to-cad's cad/text-to-cad/src/parts (PR #176), which match the lab's Fusion 360 parts. Change a part in "
    "its .fs script and push again (some sketch dimensions are not driven by the Variable Studio).")
STUDIO = "Auger"
RENDERS = HERE / "renders" / "onshape"
# Onshape view matrices (row-major 3x4): isometric, and a view from the front (-Y) side
VIEWS = {"iso": "isometric",
         "front": "1,0,0,0,0,0,1,0,0,-1,0,0"}


def load() -> dict:
    return json.loads(REC.read_text()) if REC.exists() else {}


def save(rec: dict) -> None:
    REC.write_text(json.dumps(rec, indent=1) + "\n")


def studio(rec: dict, name: str = STUDIO) -> nb.StudioState:
    st = nb.find_state(name, rec["documentId"], rec["workspaceId"])
    if st is None:
        raise SystemExit(f"no fsgen state for {name!r}: push it (or adopt it) first")
    return st


def company_id(o: Onshape, rec: dict) -> str:
    if "companyId" not in rec:
        rec["companyId"] = next(it["id"] for it in o.get("companies")["items"] if it["name"] == COMPANY)
        save(rec)
    return rec["companyId"]


def cmd_create(o: Onshape, rec: dict) -> None:
    if "documentId" in rec:
        print("already created:", rec["url"])
        return
    cid = company_id(o, rec)
    doc = o.post("documents", {
        "name": DOC_NAME, "ownerId": cid, "ownerType": 1, "isPublic": False,
        "description": DOC_DESCRIPTION})
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


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_").replace("__", "_")


def cmd_rename(o: Onshape, rec: dict, name: str) -> None:
    st = studio(rec, name)
    o.post(f"metadata/d/{st.did}/w/{st.wid}/e/{st.eid}",
           {"properties": [{"propertyId": "57f3fb8efa3416c06701d60d", "value": name}]})
    print("tab renamed:", name)


def cmd_rename_doc(o: Onshape, rec: dict) -> None:
    o.post(f"documents/{rec['documentId']}", {"name": DOC_NAME, "description": DOC_DESCRIPTION})
    rec["name"] = DOC_NAME
    save(rec)
    print("document renamed:", DOC_NAME)


def cmd_share(o: Onshape, rec: dict) -> None:
    """Share with the lab's company. The 2026-10-20 attempt got 400: it left out entryType, which defaults to
    0 (user); the spec lists 0 user, 1 company, 2 team, 3 document, 4 application, 5 connection_user."""
    cid = company_id(o, rec)
    perms = ["READ", "WRITE", "COPY", "EXPORT", "COMMENT", "LINK"]
    body = {"documentId": rec["documentId"], "entries": [{"entryType": 1, "companyId": cid}],
            "permissionSet": perms}
    o.post(f"documents/{rec['documentId']}/share", body)
    rec["sharedWith"] = {"company": COMPANY, "permissions": perms}
    save(rec)
    print("shared with", COMPANY, perms)


def cmd_adopt(o: Onshape, rec: dict, name: str, script: str) -> None:
    """Rebuild fsgen's state for a Part Studio that was pushed before but whose .fsgen_native.json was lost
    (2 calls). Features are matched to the script's trace by name and hashed from the script, so the next
    push re-sends nothing that Onshape already has."""
    from fsgen.native.script import trace
    tr = trace(Path(script).read_text())
    els = o.get(f"documents/d/{rec['documentId']}/w/{rec['workspaceId']}/elements")
    by_name = {e["name"]: e for e in els}
    ps = by_name.get(name) or (by_name.get("Part Studio 1") if name == STUDIO else None)
    if ps is None or ps.get("elementType") != "PARTSTUDIO":
        raise SystemExit(f"no Part Studio named {name!r}: {[e['name'] for e in els]}")
    vs = by_name.get(f"{name} variables")
    feats = o.get(f"partstudios/d/{rec['documentId']}/w/{rec['workspaceId']}/e/{ps['id']}/features")
    states = feats.get("featureStates", {})
    onshape = [(f["name"], f["featureId"], f["featureType"]) for f in feats["features"]]
    entries = []
    for rec_f, (oname, fid, ftype) in zip(tr.features, onshape):
        if rec_f.name != oname:
            raise SystemExit(f"tree differs at {rec_f.name!r} (Onshape: {oname!r}); not adopting")
        entries.append({"name": rec_f.name, "type": rec_f.feature_type, "hash": nb.feature_hash(rec_f),
                        "fid": fid, "status": states.get(fid, {}).get("featureStatus", "OK")})
    if len(onshape) != len(tr.features):
        raise SystemExit(f"Onshape has {len(onshape)} features, the script {len(tr.features)}; not adopting")
    import hashlib
    vh = hashlib.sha1(json.dumps(tr.variable_list, sort_keys=True).encode()).hexdigest()[:16] if vs else None
    st = nb.StudioState(rec["documentId"], rec["workspaceId"], ps["id"], name, features=entries,
                        vs_eid=vs["id"] if vs else None, vs_hash=vh, vs_referenced=bool(vs),
                        key=f"{name}@{rec['workspaceId']}")
    nb.save_state(st)
    out = HERE / "results" / f"onshape_features_{slug(name)}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(feats, indent=1) + "\n")
    print(f"adopted {name!r}: {len(entries)} features,",
          {k: sum(e['status'] == k for e in entries) for k in {e['status'] for e in entries}},
          "variable studio:", vs["name"] if vs else None)
    print("elements:", [(e["name"], e["elementType"]) for e in els])


def cmd_version(o: Onshape, rec: dict, name: str, description: str) -> None:
    v = o.post(f"documents/d/{rec['documentId']}/versions",
               {"documentId": rec["documentId"], "workspaceId": rec["workspaceId"],
                "name": name, "description": description})
    rec.setdefault("versions", []).append({"id": v["id"], "name": name, "description": description,
                                           "url": f"https://cad.onshape.com/documents/{rec['documentId']}/v/{v['id']}"})
    save(rec)
    print("version:", name, v["id"])


def cmd_views(o: Onshape, rec: dict, name: str, tag: str, only: str | None) -> None:
    st = studio(rec, name)
    for view, matrix in VIEWS.items():
        if only and view != only:
            continue
        r = o.get(f"partstudios/d/{st.did}/w/{st.wid}/e/{st.eid}/shadedviews",
                  params={"viewMatrix": matrix, "outputHeight": 900, "outputWidth": 1400, "pixelSize": 0,
                          "edges": "show", "useAntiAliasing": "true"})
        out = RENDERS / f"{slug(name)}_{tag}_{view}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(r["images"][0]))
        print("->", out.relative_to(HERE))


def cmd_tree(o: Onshape, rec: dict, name: str) -> None:
    st = studio(rec, name)
    feats = o.get(f"partstudios/d/{st.did}/w/{st.wid}/e/{st.eid}/features")
    out = HERE / "results" / f"onshape_features_{slug(name)}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(feats, indent=1) + "\n")
    for f in feats["features"]:
        print(f"  {f['featureType']:16s} {f['name']}")
    print("->", out.relative_to(HERE))


def cmd_mass(o: Onshape, rec: dict, name: str, tag: str) -> None:
    """Volume, centroid and area per part in one call (the centroid shows a flight's handedness)."""
    st = studio(rec, name)
    mp = o.get(f"partstudios/d/{st.did}/w/{st.wid}/e/{st.eid}/massproperties", params={"massAsGroup": "false"})
    out = HERE / "results" / f"onshape_massproperties_{slug(name)}_{tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(mp, indent=1) + "\n")
    for k, v in (mp.get("bodies") or {}).items():
        if k == "-all-" or "volume" not in v:          # wire and sketch bodies carry no volume
            continue
        print(k, "volume mm3", round(v["volume"][0] * 1e9, 3), "area mm2", round(v["periphery"][0] * 1e6, 3),
              "centroid mm", [round(c * 1e3, 4) for c in v["centroid"][:3]])
    print("->", out.relative_to(HERE))


def cmd_export(o: Onshape, rec: dict, name: str, stem: str) -> None:
    st = studio(rec, name)
    files = nb.export_studio(o, st, HERE / "results" / "onshape_export", stem, ("step",))
    print("exported:", [str(f.relative_to(HERE)) for f in files])


def cmd_status(o: Onshape, rec: dict, name: str) -> None:
    st = studio(rec, name)
    s = nb.check_statuses(o, st, [f["fid"] for f in st.features])
    for f in st.features:
        print(f"  {s.get(f['fid'], '?'):8s} {f['name']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["create", "adopt", "rename", "rename-doc", "share", "version", "views",
                                    "tree", "export", "mass", "status"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--studio", default=STUDIO, help="Part Studio (tab) name the part was pushed under")
    ap.add_argument("--script", help="adopt: the part's .fs script")
    ap.add_argument("--only", choices=list(VIEWS), help="views: just this one")
    ap.add_argument("--budget", type=int, default=10)
    a = ap.parse_args()
    o = Onshape(budget=a.budget, purpose=f"onshape_doc {a.cmd}")
    rec = load()
    if a.cmd == "create":
        cmd_create(o, rec)
    elif a.cmd == "adopt":
        cmd_adopt(o, rec, a.studio, a.script or str(HERE / "parts" / "auger.fs"))
    elif a.cmd == "rename":
        cmd_rename(o, rec, a.studio)
    elif a.cmd == "rename-doc":
        cmd_rename_doc(o, rec)
    elif a.cmd == "share":
        cmd_share(o, rec)
    elif a.cmd == "version":
        cmd_version(o, rec, a.args[0], a.args[1] if len(a.args) > 1 else "")
    elif a.cmd == "tree":
        cmd_tree(o, rec, a.studio)
    elif a.cmd == "views":
        cmd_views(o, rec, a.studio, a.args[0] if a.args else "final", a.only)
    elif a.cmd == "export":
        cmd_export(o, rec, a.studio, a.args[0] if a.args else f"{slug(a.studio)}_onshape")
    elif a.cmd == "mass":
        cmd_mass(o, rec, a.studio, a.args[0] if a.args else "final")
    else:
        cmd_status(o, rec, a.studio)
    print(o.summary())

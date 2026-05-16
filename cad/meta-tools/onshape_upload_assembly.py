"""Onshape REST: upload the five Phase-2 (fallback Phase-1) per-part STEPs
plus the Phase-3 composite assembly STEP, and emit clickable Onshape URLs
for each newly created Part Studio so a reviewer can open them directly
in the Onshape UI.

Reads ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY from env. The URLs printed
to stdout contain real document/workspace/element IDs (so the user can
click them); none of those IDs are persisted into the repo by this
script — only the ``logs/onshape-upload-assembly.summary.txt`` file is
written and it deliberately redacts ids before committing.

Run with::

    python cad/meta-tools/onshape_upload_assembly.py
"""
from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import os
import pathlib
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com")
REPO = pathlib.Path(__file__).resolve().parent.parent.parent
LOG_PATH = REPO / "logs" / "onshape-upload-assembly.summary.txt"

# Prefer Phase-2 iterated outputs; fall back to Phase-1 if missing.
PARTS = [
    ("auger_solid",
     "cad/meta-tools/zoo-output/multi-part-iter/auger_solid/auger_solid.step",
     "cad/meta-tools/zoo-output/multi-part/auger_solid/auger_solid.step"),
    ("stepper_mount_collar",
     "cad/meta-tools/zoo-output/multi-part-iter/stepper_mount_collar/stepper_mount_collar.step",
     "cad/meta-tools/zoo-output/multi-part/stepper_mount_collar/stepper_mount_collar.step"),
    ("embed_pocket_sleeve",
     "cad/meta-tools/zoo-output/multi-part-iter/embed_pocket_sleeve/embed_pocket_sleeve.step",
     "cad/meta-tools/zoo-output/multi-part/embed_pocket_sleeve/embed_pocket_sleeve.step"),
    ("servo_yoke",
     "cad/meta-tools/zoo-output/multi-part/servo_yoke/servo_yoke.step",
     None),
    ("pi_mount_bracket",
     "cad/meta-tools/zoo-output/multi-part/pi_mount_bracket/pi_mount_bracket.step",
     None),
]

ASSEMBLY = ("full_system_assembly",
            "design/cad/full-system-modular/full_system_assembly.step")


def _sign(method: str, secret_key: bytes, access_key: str, path: str,
          query: str, ctype: str) -> dict:
    nonce = secrets.token_hex(13)[:25]
    date = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    sig_str = "\n".join([method, nonce, date, ctype, path, query, ""]).lower()
    sig = base64.b64encode(
        hmac.new(secret_key, sig_str.encode("utf-8"), hashlib.sha256).digest()
    ).decode()
    return {
        "Date": date,
        "On-Nonce": nonce,
        "Authorization": f"On {access_key}:HmacSHA256:{sig}",
        "Content-Type": ctype,
        "Accept": "application/json",
    }


def signed(method: str, access: str, secret: bytes, path: str,
           query: str = "", body: bytes | None = None,
           ctype: str = "application/json"):
    headers = _sign(method, secret, access, path, query, ctype)
    url = BASE + path + (("?" + query) if query else "")
    req = urllib.request.Request(url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def multipart_signed(access: str, secret: bytes, path: str, fields: dict,
                     file_name: str, file_bytes: bytes,
                     file_field: str = "file"):
    boundary = "----onshape" + uuid.uuid4().hex
    ctype = f"multipart/form-data; boundary={boundary}"
    parts = []
    for k, v in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        )
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; "
        f"filename=\"{file_name}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode()
    )
    body = b"".join(parts)
    headers = _sign("POST", secret, access, path, "", ctype)
    headers["Accept"] = "application/json;charset=UTF-8;qs=0.09"
    url = BASE + path
    req = urllib.request.Request(url, method="POST", data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _resolve_doc(access: str, sk: bytes) -> tuple[str, str, str]:
    """Return (did, wid, doc_name) for the first non-empty workspace."""
    code, body = signed("GET", access, sk, "/api/v6/documents",
                        "filter=0&limit=10&sortColumn=modifiedAt&sortOrder=desc")
    if code != 200:
        raise SystemExit(f"GET /documents HTTP {code}: {body[:200]!r}")
    docs = json.loads(body).get("items", [])
    if not docs:
        raise SystemExit("no documents on this Onshape account.")
    doc = docs[0]
    did = doc["id"]
    code, body = signed("GET", access, sk, f"/api/v6/documents/{did}")
    if code != 200:
        raise SystemExit(f"GET /documents/{{did}} HTTP {code}: {body[:200]!r}")
    wid = json.loads(body)["defaultWorkspace"]["id"]
    return did, wid, doc.get("name", "?")


def _upload_step(access: str, sk: bytes, did: str, wid: str,
                 name: str, step_path: pathlib.Path) -> list[str]:
    """Upload one STEP with translate=true; return new element ids."""
    fields = {
        "encodedFilename": step_path.name,
        "fileName": step_path.name,
        "translate": "true",
        "storeInDocument": "true",
        "createComposite": "false",
        "splitAssembliesIntoMultipleDocuments": "false",
        "flattenAssemblies": "false",
        "yAxisIsUp": "false",
        "allowFaultyParts": "true",
    }
    code, body = multipart_signed(
        access, sk, f"/api/v6/blobelements/d/{did}/w/{wid}",
        fields, step_path.name, step_path.read_bytes(),
    )
    if code not in (200, 201):
        print(f"  [{name}] upload HTTP {code}: {body[:300].decode(errors='replace')}")
        return []
    j = json.loads(body)
    tid = j.get("translationId") or j.get("id")
    if not tid:
        print(f"  [{name}] no translationId in response")
        return []
    # Poll translation up to 5 minutes.
    deadline = time.time() + 300
    while time.time() < deadline:
        time.sleep(4)
        code, body = signed("GET", access, sk, f"/api/v6/translations/{tid}")
        if code != 200:
            continue
        t = json.loads(body)
        state = t.get("requestState")
        if state == "DONE":
            return t.get("resultElementIds") or []
        if state == "FAILED":
            print(f"  [{name}] translation FAILED: {t.get('failureReason')}")
            return []
    print(f"  [{name}] translation poll timed out")
    return []


def _element_url(did: str, wid: str, eid: str) -> str:
    return f"{BASE}/documents/{did}/w/{wid}/e/{eid}"


def main() -> int:
    access = os.environ.get("ONSHAPE_ACCESS_KEY")
    secret = os.environ.get("ONSHAPE_SECRET_KEY")
    if not access or not secret:
        print("ONSHAPE_ACCESS_KEY/SECRET_KEY not set; aborting.")
        return 1
    sk = secret.encode("utf-8")
    print(f"BASE = {BASE}")

    did, wid, doc_name = _resolve_doc(access, sk)
    print(f"target document: {doc_name!r}")
    doc_url = f"{BASE}/documents/{did}/w/{wid}"
    print(f"document URL: {doc_url}")

    results: list[tuple[str, pathlib.Path, list[str]]] = []

    # Resolve part sources.
    to_upload: list[tuple[str, pathlib.Path]] = []
    for name, primary, fallback in PARTS:
        chosen = None
        for rel in (primary, fallback):
            if rel and (REPO / rel).exists():
                chosen = REPO / rel
                break
        if chosen is None:
            print(f"  [{name}] no STEP found, skipping")
            continue
        to_upload.append((name, chosen))

    asm_path = REPO / ASSEMBLY[1]
    if asm_path.exists():
        to_upload.append((ASSEMBLY[0], asm_path))
    else:
        print(f"  [{ASSEMBLY[0]}] assembly STEP missing at {asm_path}, skipping")

    print(f"\nWill upload {len(to_upload)} STEPs:")
    for name, p in to_upload:
        print(f"  - {name:24s}  {p.relative_to(REPO)}  ({p.stat().st_size} bytes)")

    print("\n== uploads ==")
    for name, step_path in to_upload:
        print(f"\n[{name}] uploading {step_path.name} ...")
        eids = _upload_step(access, sk, did, wid, name, step_path)
        results.append((name, step_path, eids))
        for eid in eids:
            print(f"  -> {_element_url(did, wid, eid)}")

    # Summary.
    print("\n== Clickable Onshape URLs ==")
    print(f"Document: {doc_url}")
    for name, step_path, eids in results:
        if not eids:
            print(f"  {name}: (upload failed or no element id)")
        else:
            for eid in eids:
                print(f"  {name}: {_element_url(did, wid, eid)}")

    # Redacted summary file (safe to commit).
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        f.write(f"# onshape upload-assembly summary  {ts}\n")
        f.write(f"BASE = {BASE}\n")
        f.write("document URL (redacted): "
                f"{BASE}/documents/<did>/w/<wid>\n")
        f.write("\n## uploaded elements\n")
        for name, step_path, eids in results:
            status = f"{len(eids)} element(s)" if eids else "FAILED"
            f.write(f"- {name}: {status}  (source: {step_path.relative_to(REPO)})\n")
        f.write("\n(real did/wid/eid printed to stdout only; not committed)\n")
    print(f"\nredacted summary -> {LOG_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

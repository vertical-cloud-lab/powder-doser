"""Onshape REST: upload the five Phase-2 (fallback Phase-1) per-part STEPs
plus the Phase-3 composite assembly STEP, and emit clickable Onshape URLs
for each newly created Part Studio so a reviewer can open them directly
in the Onshape UI.

Reads ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY from env. The URLs printed
to stdout contain real document/workspace/element IDs (so the user can
click them); none of those IDs are persisted into the repo by this
script — only the ``logs/onshape-upload-assembly.summary.txt`` file is
written and it deliberately redacts ids before committing.

To avoid confusing provenance (these parts were authored via Zoo's
ML-ephant ``/ai/text-to-cad`` + ``/ml/text-to-cad/iteration`` endpoints,
not CADSmith), this script targets a dedicated Onshape document named
``Powder Doser v2 (Zoo ML-ephant)`` by default and creates it on first
run if it doesn't yet exist. Override with the ``ONSHAPE_TARGET_DOC_NAME``
env var. Uploaded blobs/Part Studios are also prefixed with ``zoo__`` so
the provenance is clear even from element names inside the document.

By default the document is owned by the ``Vertical Cloud Lab`` Onshape
classroom (BTOwnerType=COMPANY) and is **public**, so URLs the script
prints are openable without sign-in. Override with::

    ONSHAPE_OWNER_NAME=<classroom or company name>   # default: Vertical Cloud Lab
    ONSHAPE_OWNER_ID=<companyId>                     # takes precedence over name
    ONSHAPE_OWNER_TYPE=<0=user|1=company|2=team>     # default: 1
    ONSHAPE_PUBLIC=0                                 # opt out of public

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

# Target a dedicated, clearly-named document so the provenance is obvious in
# the Onshape UI. Override via env if the user prefers a different name.
TARGET_DOC_NAME = os.environ.get(
    "ONSHAPE_TARGET_DOC_NAME", "Powder Doser v2 (Zoo ML-ephant)"
)
# Element-name prefix to make per-Part-Studio provenance obvious even inside
# the document (e.g. ``zoo__auger_solid``). Honours the doc name override.
NAME_PREFIX = os.environ.get("ONSHAPE_NAME_PREFIX", "zoo__")

# Classroom / company ownership. When set, newly-created documents are owned
# by the named Onshape company/classroom (rather than by the calling user)
# and shared with everyone enrolled. ``ONSHAPE_OWNER_NAME`` is resolved to
# an id by name-matching against ``GET /api/v6/companies`` on first run;
# alternately set ``ONSHAPE_OWNER_ID`` directly. ``ONSHAPE_OWNER_TYPE``
# follows Onshape's ``BTOwnerType``: 0=user, 1=company (the EDU classroom
# case), 2=team. Default is the "Vertical Cloud Lab" classroom so that the
# uploaded geometry inherits classroom membership for collaborators.
OWNER_NAME = os.environ.get("ONSHAPE_OWNER_NAME", "Vertical Cloud Lab")
OWNER_ID = os.environ.get("ONSHAPE_OWNER_ID")  # if set, takes precedence
OWNER_TYPE = int(os.environ.get("ONSHAPE_OWNER_TYPE", "1"))  # 1 = COMPANY

# Public-by-default: matches the user's manual setting on prior documents in
# this PR. Set ``ONSHAPE_PUBLIC=0`` (or ``false``/``no``) to opt out and
# create a private document instead.
def _truthy(val: str) -> bool:
    return val.strip().lower() not in ("", "0", "false", "no", "off")
IS_PUBLIC = _truthy(os.environ.get("ONSHAPE_PUBLIC", "1"))

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


def _resolve_owner(access: str, sk: bytes) -> tuple[str | None, int]:
    """Return (owner_id, owner_type) for the classroom/company to own newly
    created documents. Resolves ``ONSHAPE_OWNER_NAME`` against the user's
    company list when ``ONSHAPE_OWNER_ID`` is not provided. Returns
    ``(None, 0)`` (i.e. owned by the calling user) if no match is found,
    so the script degrades gracefully on accounts without a classroom.
    """
    if OWNER_ID:
        return OWNER_ID, OWNER_TYPE
    if not OWNER_NAME:
        return None, 0
    # Company / classroom lookup (BTOwnerType.COMPANY = 1).
    code, body = signed("GET", access, sk, "/api/v6/companies")
    if code != 200:
        print(f"  [owner] GET /companies HTTP {code} -> falling back to user-owned")
        return None, 0
    for c in json.loads(body).get("items", []):
        if c.get("name") == OWNER_NAME:
            return c["id"], 1
    # Try teams as a secondary lookup (BTOwnerType.TEAM = 2).
    code, body = signed("GET", access, sk, "/api/v6/teams")
    if code == 200:
        for t in json.loads(body).get("items", []):
            if t.get("name") == OWNER_NAME:
                return t["id"], 2
    print(f"  [owner] no company/team named {OWNER_NAME!r}; "
          "falling back to user-owned")
    return None, 0


def _resolve_doc(access: str, sk: bytes,
                 target_name: str = TARGET_DOC_NAME) -> tuple[str, str, str, bool, str]:
    """Return (did, wid, doc_name, created, owner_label) for the document
    named ``target_name``. Creates it on first run if not already present,
    owned by the configured classroom/company (so members can see it) and
    public by default (so the per-element URLs the script prints are
    openable without sign-in).
    """
    owner_id, owner_type = _resolve_owner(access, sk)
    owner_label = (f"{OWNER_NAME} (companyId={owner_id}, type={owner_type})"
                   if owner_id else "calling user")

    # Search by name first across both user-visible and (when configured)
    # classroom-owned documents.
    def _scan(filter_id: int, extra: str = "") -> str | None:
        offset = 0
        while True:
            q = (f"filter={filter_id}&limit=20&offset={offset}"
                 f"&sortColumn=modifiedAt&sortOrder=desc{extra}")
            code, body = signed("GET", access, sk, "/api/v6/documents", q)
            if code != 200:
                return None
            page = json.loads(body)
            for doc in page.get("items", []):
                if doc.get("name") == target_name:
                    return doc["id"]
            if not page.get("next") and len(page.get("items", [])) < 20:
                return None
            offset += 20

    did = None
    # filter=0: My Onshape (covers user-owned + shared with user, incl.
    # documents within the user's classrooms).
    did = _scan(0)
    if did is None and owner_id:
        # filter=7: documents owned by a specific company/team.
        did = _scan(7, f"&owner={owner_id}&ownerType={owner_type}")

    if did is not None:
        code, body = signed("GET", access, sk, f"/api/v6/documents/{did}")
        if code != 200:
            raise SystemExit(
                f"GET /documents/{{did}} HTTP {code}: {body[:200]!r}"
            )
        j = json.loads(body)
        wid = j["defaultWorkspace"]["id"]
        return did, wid, j.get("name", target_name), False, owner_label

    # Not found -> create a fresh document with the desired ownership /
    # visibility.
    doc_payload: dict = {
        "name": target_name,
        "description": ("Zoo ML-ephant (KittyCAD /ai/text-to-cad + "
                        "/ml/text-to-cad/iteration) outputs for the "
                        "powder-doser full-system design. Auto-created by "
                        "cad/meta-tools/onshape_upload_assembly.py."),
        "isPublic": IS_PUBLIC,
    }
    if owner_id:
        doc_payload["ownerId"] = owner_id
        doc_payload["ownerType"] = owner_type
    payload = json.dumps(doc_payload).encode("utf-8")
    code, body = signed("POST", access, sk, "/api/v6/documents", "",
                        body=payload)
    if code not in (200, 201):
        raise SystemExit(
            f"POST /documents HTTP {code}: {body[:300]!r}"
        )
    j = json.loads(body)
    did = j["id"]
    wid = j["defaultWorkspace"]["id"]
    return did, wid, j.get("name", target_name), True, owner_label


def _upload_step(access: str, sk: bytes, did: str, wid: str,
                 name: str, step_path: pathlib.Path) -> list[str]:
    """Upload one STEP with translate=true; return new element ids.

    The uploaded element is named ``{NAME_PREFIX}{name}.step`` so that the
    Zoo provenance is visible from the Onshape document tree even without
    opening the per-element URLs.
    """
    display_name = f"{NAME_PREFIX}{name}.step"
    fields = {
        "encodedFilename": display_name,
        "fileName": display_name,
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
        fields, display_name, step_path.read_bytes(),
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

    did, wid, doc_name, created, owner_label = _resolve_doc(access, sk)
    verb = "created" if created else "found"
    print(f"target document ({verb}): {doc_name!r}")
    print(f"  owner: {owner_label}")
    print(f"  public: {IS_PUBLIC}  (override via ONSHAPE_PUBLIC=0)")
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
        f.write(f"target document name: {doc_name!r}  ({verb})\n")
        f.write(f"owner               : {OWNER_NAME!r} "
                f"(type={OWNER_TYPE if OWNER_ID else (1 if OWNER_NAME else 0)}, "
                "companyId redacted)\n")
        f.write(f"public              : {IS_PUBLIC}\n")
        f.write(f"element name prefix : {NAME_PREFIX!r}  "
                "(makes Zoo ML-ephant provenance obvious in Onshape UI)\n")
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

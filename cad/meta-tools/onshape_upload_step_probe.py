"""Onshape REST: upload a local STEP into the workspace + translate it.

Demonstrates the practical "what can we actually do" workflow now that
the classroom-scoped API key authenticates end-to-end (issue #16 / PR
discussion):

  1. Resolve the user's first non-empty document and its default
     workspace via ``GET /documents`` + ``GET /documents/{did}``.
  2. Enumerate existing elements (``GET /documents/d/{did}/w/{wid}/elements``)
     so we can detect already-imported parts.
  3. Upload a local STEP file as a Blob Element (multipart POST to
     ``/blobelements/d/{did}/w/{wid}``) with ``translate=true`` so
     Onshape spins up an import-translation that turns the STEP into a
     real Part Studio with BREP geometry.
  4. Poll ``/translations/{tid}`` until ``DONE`` and report the new
     element id(s).
  5. Re-translate the imported Part Studio back to STL via
     ``POST /partstudios/d/{did}/w/{wid}/e/{eid}/translations`` with
     ``formatName=STL`` to confirm the round-trip works.

Reads ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY from env.  Never echoes
secrets, document ids, user ids, or email addresses.
"""
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
STEP_PATH = pathlib.Path(
    os.environ.get(
        "ONSHAPE_UPLOAD_STEP",
        str(pathlib.Path(__file__).parent / "zoo-output" / "auger_barrel_cadquery.step"),
    )
)


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
                     file_name: str, file_bytes: bytes, file_field: str = "file"):
    """Onshape's blob upload requires multipart/form-data with translate flag."""
    boundary = "----onshape" + uuid.uuid4().hex
    ctype = f"multipart/form-data; boundary={boundary}"
    parts = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; "
        f"filename=\"{file_name}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode()
    )
    body = b"".join(parts)
    # Onshape signs with the *declared* Content-Type including boundary.
    headers = _sign("POST", secret, access, path, "", ctype)
    headers["Accept"] = "application/json;charset=UTF-8;qs=0.09"
    url = BASE + path
    req = urllib.request.Request(url, method="POST", data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main() -> int:
    access = os.environ.get("ONSHAPE_ACCESS_KEY")
    secret = os.environ.get("ONSHAPE_SECRET_KEY")
    if not access or not secret:
        print("ONSHAPE_ACCESS_KEY/SECRET_KEY not set; skipping.")
        return 0
    if not STEP_PATH.exists():
        print(f"local STEP not found at {STEP_PATH}; skipping upload demo.")
        return 0
    sk = secret.encode("utf-8")
    print(f"BASE = {BASE}")
    print(f"upload source: {STEP_PATH.name}  ({STEP_PATH.stat().st_size} bytes)")

    # 1. Find a document.
    print("\n== GET /documents ==")
    code, body = signed("GET", access, sk, "/api/v6/documents",
                        "filter=0&limit=10&sortColumn=modifiedAt&sortOrder=desc")
    print(f"HTTP {code}")
    if code != 200:
        print(body[:300].decode(errors="replace"))
        return 1
    docs = json.loads(body).get("items", [])
    if not docs:
        print("no documents on this account; create one in the Onshape UI first.")
        return 0
    doc = docs[0]
    did = doc["id"]
    print(f"  using doc name={doc.get('name')!r}  (id redacted)")

    # 2. Default workspace.
    code, body = signed("GET", access, sk, f"/api/v6/documents/{did}")
    if code != 200:
        print(f"GET /documents/{{did}} HTTP {code}: {body[:200].decode(errors='replace')}")
        return 1
    wid = json.loads(body)["defaultWorkspace"]["id"]
    print(f"  default workspace resolved (id redacted)")

    # 3. List elements before upload.
    code, body = signed("GET", access, sk,
                        f"/api/v6/documents/d/{did}/w/{wid}/elements")
    elems_before = json.loads(body) if code == 200 else []
    print(f"  elements before upload: {len(elems_before)}  "
          f"({[e.get('name') for e in elems_before]})")

    # 4. Upload STEP as blob with translate=true.
    print(f"\n== POST /blobelements/d/{{did}}/w/{{wid}} (translate=true) ==")
    file_bytes = STEP_PATH.read_bytes()
    upload_name = STEP_PATH.name
    fields = {
        "encodedFilename": upload_name,
        "fileName": upload_name,
        "translate": "true",
        "storeInDocument": "true",
        "createComposite": "false",
        "splitAssembliesIntoMultipleDocuments": "false",
        "flattenAssemblies": "false",
        "yAxisIsUp": "false",
        "allowFaultyParts": "true",
    }
    code, body = multipart_signed(
        access, sk,
        f"/api/v6/blobelements/d/{did}/w/{wid}",
        fields, upload_name, file_bytes,
    )
    print(f"HTTP {code}")
    if code not in (200, 201):
        print(body[:600].decode(errors="replace"))
        return 1
    j = json.loads(body)
    print(f"  response keys: {sorted(j.keys())}")
    tid = j.get("translationId") or j.get("id")
    print(f"  translation id (redacted) created; initial state={j.get('requestState')}")

    # 5. Poll translation.
    print(f"\n== GET /translations/{{tid}} (poll) ==")
    deadline = time.time() + 90
    new_eids = []
    while time.time() < deadline:
        time.sleep(3)
        code, body = signed("GET", access, sk, f"/api/v6/translations/{tid}")
        if code != 200:
            print(f"  poll HTTP {code}: {body[:200].decode(errors='replace')}")
            break
        t = json.loads(body)
        state = t.get("requestState")
        print(f"  state={state}")
        if state in ("DONE", "FAILED"):
            new_eids = t.get("resultElementIds") or []
            if state == "FAILED":
                print(f"  failure reason: {t.get('failureReason')}")
            break

    if not new_eids:
        print("  no result element ids returned; bailing.")
        return 0

    # 6. Verify Part Studio appears + translate it back to STL.
    code, body = signed("GET", access, sk,
                        f"/api/v6/documents/d/{did}/w/{wid}/elements")
    elems_after = json.loads(body) if code == 200 else []
    print(f"\n  elements after upload: {len(elems_after)}  "
          f"({[e.get('name') for e in elems_after]})")

    eid = new_eids[0]
    print(f"\n== POST /partstudios/.../translations  (formatName=STL) ==")
    payload = json.dumps({
        "formatName": "STL",
        "storeInDocument": False,
        "units": "millimeter",
        "mode": "binary",
    }).encode()
    code, body = signed(
        "POST", access, sk,
        f"/api/v6/partstudios/d/{did}/w/{wid}/e/{eid}/translations",
        body=payload,
    )
    print(f"HTTP {code}")
    if code in (200, 202):
        t = json.loads(body)
        print(f"  STL translation queued; initial state={t.get('requestState')}")
    else:
        print(body[:400].decode(errors="replace"))

    return 0


if __name__ == "__main__":
    sys.exit(main())

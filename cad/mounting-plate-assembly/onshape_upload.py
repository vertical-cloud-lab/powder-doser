#!/usr/bin/env python3
"""Upload the powder-doser mounting-plate full assembly STEP to Onshape.

Creates a public Onshape document, imports the combined STEP via the
blob-element translation API, waits for the translation to finish, and
prints the shareable document link.
"""
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE = "https://cad.onshape.com"
AK = os.environ.get("ONSHAPE_ACCESS_KEY", "").strip()
SK = os.environ.get("ONSHAPE_SECRET_KEY", "").strip()
if not AK or not SK:
    sys.exit("ONSHAPE_ACCESS_KEY and ONSHAPE_SECRET_KEY must both be set.")
AUTH = "Basic " + base64.b64encode(f"{AK}:{SK}".encode()).decode()

STEP = sys.argv[1] if len(sys.argv) > 1 else (
    "cad/mounting-plate-assembly/assembly/full_assembly.step")
DOC_NAME = sys.argv[2] if len(sys.argv) > 2 else (
    "powder-doser — mounting-plate dual-servo full assembly")


def req(method, path, headers=None, data=None, raw=False):
    url = BASE + path
    h = {"Authorization": AUTH, "Accept": "application/json"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=120)
        body = resp.read()
        return resp.status, (body if raw else json.loads(body or b"{}"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def main():
    if not os.path.isfile(STEP):
        sys.exit(f"STEP file not found: {STEP}")
    # 1. Create a public document.
    status, doc = req(
        "POST", "/api/v6/documents",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"name": DOC_NAME, "isPublic": True}).encode())
    if status >= 300:
        print("create doc failed:", status, doc)
        sys.exit(1)
    did = doc["id"]
    wid = doc["defaultWorkspace"]["id"]
    print("document:", did, "workspace:", wid)

    # 2. Upload the STEP as a blob element with translate=true.
    with open(STEP, "rb") as f:
        file_bytes = f.read()
    fname = os.path.basename(STEP)

    boundary = "----onshapeBoundary7f3a9c"
    parts = []

    def field(name, value):
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())

    field("encodedFilename", fname)
    field("fileContentLength", str(len(file_bytes)))
    field("translate", "true")
    field("flattenAssemblies", "false")
    field("yAxisIsUp", "false")
    field("storeInDocument", "false")
    # file part
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        (f'Content-Disposition: form-data; name="file"; '
         f'filename="{fname}"\r\n').encode())
    parts.append(b"Content-Type: application/step\r\n\r\n")
    parts.append(file_bytes)
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    status, res = req(
        "POST", f"/api/v6/blobelements/d/{did}/w/{wid}",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        data=body)
    if status >= 300:
        print("blob upload failed:", status, res)
        sys.exit(1)
    tid = res.get("translationId") or res.get("id")
    print("translation:", tid)

    # 3. Poll translation.
    for _ in range(120):
        time.sleep(5)
        st, tr = req("GET", f"/api/v6/translations/{tid}")
        if st >= 300:
            print("poll failed:", st, tr)
            break
        state = tr.get("requestState")
        print("  state:", state)
        if state == "DONE":
            print("result elements:", tr.get("resultElementIds"))
            break
        if state == "FAILED":
            print("translation FAILED:", tr.get("failureReason"))
            break

    link = f"{BASE}/documents/{did}/w/{wid}"
    print("LINK:", link)
    return link


if __name__ == "__main__":
    main()

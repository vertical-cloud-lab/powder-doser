"""End-to-end test of the classroom+public upload defaults added in commit
7a72dad to ``onshape_upload_assembly.py``.

Uploads a single tiny test STEP (``cad/meta-tools/zoo-output/classroom-upload-test/test_part.step``,
a 20x10x5 mm plate with a 4x M1 hole pattern, ~34 KB) into a fresh
``Powder Doser — classroom upload test`` Onshape document, owned by the
``Vertical Cloud Lab`` classroom and public-by-default. Then re-fetches
the document via ``GET /api/v6/documents/{did}`` and prints the resolved
ownership + ``public`` flag so the behaviour can be verified without
opening the Onshape UI.

This exists purely as a probe / acceptance test for the classroom-ownership
patch — it is independent of the powder-doser assembly upload itself
and intentionally targets a different (test-only) document name so no
existing geometry is touched.

Run::

    ONSHAPE_ACCESS_KEY=... ONSHAPE_SECRET_KEY=... \\
        python cad/meta-tools/onshape_classroom_upload_test_probe.py
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import sys

# Re-use the helpers and constants from onshape_upload_assembly so the
# probe exercises the exact code-path used for the real upload.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import onshape_upload_assembly as oua  # noqa: E402

TARGET_DOC_NAME = os.environ.get(
    "ONSHAPE_TEST_DOC_NAME", "Powder Doser — classroom upload test"
)
TEST_STEP = pathlib.Path(__file__).resolve().parent / (
    "zoo-output/classroom-upload-test/test_part.step"
)
LOG_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / (
    "logs/onshape-classroom-upload-test.summary.txt"
)


def main() -> int:
    access = os.environ.get("ONSHAPE_ACCESS_KEY")
    secret = os.environ.get("ONSHAPE_SECRET_KEY")
    if not access or not secret:
        print("ONSHAPE_ACCESS_KEY/SECRET_KEY not set; aborting.")
        return 1
    sk = secret.encode("utf-8")
    print(f"BASE = {oua.BASE}")
    print(f"target document  : {TARGET_DOC_NAME!r}")
    print(f"target owner name: {oua.OWNER_NAME!r} (type={oua.OWNER_TYPE})")
    print(f"public default   : {oua.IS_PUBLIC}")
    print(f"test STEP        : {TEST_STEP} "
          f"({TEST_STEP.stat().st_size} bytes)")

    did, wid, doc_name, created, owner_label = oua._resolve_doc(
        access, sk, target_name=TARGET_DOC_NAME
    )
    verb = "created" if created else "found"
    print(f"\ndocument ({verb}): {doc_name!r}")
    print(f"  owner: {owner_label}")
    doc_url = f"{oua.BASE}/documents/{did}/w/{wid}"
    print(f"  url  : {doc_url}")

    # Re-fetch document metadata to verify the public flag / ownership the
    # classroom defaults actually produced (rather than what we asked for).
    code, body = oua.signed("GET", access, sk, f"/api/v6/documents/{did}")
    if code == 200:
        j = json.loads(body)
        owner = j.get("owner") or {}
        print("\n== verified document metadata ==")
        print(f"  public      : {j.get('public')}")
        print(f"  permission  : {j.get('permission')}")
        print(f"  owner.type  : {owner.get('type')}  "
              "(0=user, 1=company, 2=team)")
        print(f"  owner.name  : {owner.get('name')!r}")
    else:
        print(f"  [warn] GET /documents/{{did}} HTTP {code}")
        j = {}

    print("\n== upload ==")
    eids = oua._upload_step(access, sk, did, wid, "test_part", TEST_STEP)
    for eid in eids:
        print(f"  -> {oua._element_url(did, wid, eid)}")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%MZ"
        )
        f.write(f"# onshape classroom-upload-test summary  {ts}\n")
        f.write(f"BASE                 = {oua.BASE}\n")
        f.write(f"target document name : {doc_name!r}  ({verb})\n")
        f.write(f"owner config         : name={oua.OWNER_NAME!r} "
                f"type={oua.OWNER_TYPE}\n")
        f.write(f"public config        : {oua.IS_PUBLIC}\n")
        owner = (j.get("owner") or {}) if j else {}
        f.write(f"verified public      : {j.get('public')!r}\n")
        f.write(f"verified owner.type  : {owner.get('type')!r}\n")
        f.write(f"verified owner.name  : {owner.get('name')!r}\n")
        f.write(f"verified permission  : {j.get('permission')!r}\n")
        f.write(f"test STEP            : "
                f"cad/meta-tools/zoo-output/classroom-upload-test/test_part.step "
                f"({TEST_STEP.stat().st_size} bytes)\n")
        f.write(f"uploaded element(s)  : {len(eids)}\n")
        f.write("document URL (redacted): "
                f"{oua.BASE}/documents/<did>/w/<wid>\n")
    print(f"\nwrote {LOG_PATH.relative_to(pathlib.Path.cwd())}")
    return 0 if eids else 2


if __name__ == "__main__":
    raise SystemExit(main())

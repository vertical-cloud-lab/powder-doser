"""Probe Zoo (zoo.dev) ML-ephant text-to-CAD + KittyCAD APIs.

Reads ZOO_API_TOKEN from the env (never echoed). Demonstrates two paths
that are directly relevant to the powder-doser Archimedes auger
(issue #16):

  1. KittyCAD design API  — GET /user (auth ping) and
     GET /file/conversions (lists prior file-format conversions; the
     paid endpoint we care about is POST /file/conversion/{src}/{dst}
     for STEP <-> STL <-> OBJ <-> GLTF round-trips).

  2. ML-ephant text-to-CAD — POST /ai/text-to-cad/{output_format}
     submits an async ML job that turns a natural-language prompt into
     real CAD geometry; we poll GET /user/text-to-cad/{id} until
     completion and write the returned file(s) to ``zoo-output/``.

Spec: https://zoo.dev/docs/api  (KittyCAD + ML-ephant share api.zoo.dev)

The Cloudflare edge in front of api.zoo.dev rejects requests with the
default ``Python-urllib/3.x`` UA (``error code: 1010``), so we set an
explicit project UA on every request.
"""
import base64
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("ZOO_BASE_URL", "https://api.zoo.dev")
UA = "powder-doser-meta-tools/1.0 (+https://github.com/vertical-cloud-lab/powder-doser)"
OUT_DIR = pathlib.Path(__file__).parent / "zoo-output"

# Auger spec lifted verbatim from issue #16.
PROMPT = (
    "An Archimedes auger / helical screw dispenser, 20 mm outside diameter, "
    "100 mm tall, with an M3 threaded mounting hole on the top spindle and "
    "a 2.5 mm exit hole at the bottom. Single-start helix, ~10 mm pitch, "
    "central shaft ~6 mm diameter."
)


def _request(method: str, path: str, token: str, body: bytes | None = None,
             extra_headers: dict | None = None):
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": UA,
        "Accept": "application/json",
    }
    if body is not None:
        headers.setdefault("Content-Type", "application/json")
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(BASE + path, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


def kittycad_user_ping(token: str) -> None:
    print("\n== KittyCAD: GET /user (auth ping) ==")
    code, body, _ = _request("GET", "/user", token)
    print(f"HTTP {code}")
    if code == 200:
        j = json.loads(body)
        safe = {k: j.get(k) for k in ("name", "company", "first_name", "last_name") if k in j}
        # email/id intentionally suppressed in the audit log.
        print(json.dumps(safe, indent=2, default=str))
    else:
        print(body[:400].decode(errors="replace"))


def kittycad_list_conversions(token: str) -> None:
    print("\n== KittyCAD: GET /user/file/conversions (history) ==")
    code, body, _ = _request("GET", "/user/file/conversions?limit=5", token)
    print(f"HTTP {code}")
    try:
        j = json.loads(body)
        items = j.get("items", []) if isinstance(j, dict) else []
        print(f"items returned: {len(items)}")
        for it in items[:5]:
            print(
                f"  - id={it.get('id')}  status={it.get('status')}  "
                f"{it.get('src_format')}->{it.get('output_format')}  "
                f"created={it.get('created_at')}"
            )
    except Exception:
        print(body[:400].decode(errors="replace"))


def text_to_cad(token: str, fmt: str = "step") -> dict | None:
    """Submit + poll a text-to-CAD job; returns the final job dict or None."""
    print(f"\n== ML-ephant: POST /ai/text-to-cad/{fmt} (async submit) ==")
    qs = urllib.parse.urlencode({"prompt": PROMPT})
    payload = json.dumps({"prompt": PROMPT}).encode("utf-8")
    code, body, _ = _request("POST", f"/ai/text-to-cad/{fmt}?{qs}", token, body=payload)
    print(f"HTTP {code}")
    if code not in (200, 201, 202):
        print(body[:600].decode(errors="replace"))
        return None
    job = json.loads(body)
    job_id = job.get("id")
    print(f"submitted id={job_id} status={job.get('status')}")

    print(f"\n== ML-ephant: GET /user/text-to-cad/{{id}} (poll) ==")
    deadline = time.time() + 240  # 4-minute cap
    poll_every = 5
    while time.time() < deadline:
        time.sleep(poll_every)
        code, body, _ = _request("GET", f"/user/text-to-cad/{job_id}", token)
        if code != 200:
            print(f"poll HTTP {code} {body[:200].decode(errors='replace')}")
            return None
        job = json.loads(body)
        status = job.get("status")
        print(f"  status={status}")
        if status in ("completed", "failed"):
            return job
    print("  poll deadline reached; giving up.")
    return job


def save_outputs(job: dict, fmt: str) -> None:
    if not job:
        return
    outputs = job.get("outputs") or {}
    if not outputs:
        print("(no outputs returned)")
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, b64 in outputs.items():
        try:
            # Zoo's API omits base64 padding; restore it before decoding.
            data = base64.b64decode(b64 + "=" * (-len(b64) % 4))
        except Exception as e:
            print(f"  - {name}: not base64 ({e})")
            continue
        # Sanitize filename: keep only basename, force the requested ext.
        safe = pathlib.Path(name).name or f"auger.{fmt}"
        dst = OUT_DIR / safe
        dst.write_bytes(data)
        print(f"  - wrote {dst.relative_to(OUT_DIR.parent)}  ({len(data)} bytes)")
    # KCL "code" field is the parametric source; archive it too.
    kcl = job.get("code")
    if kcl:
        (OUT_DIR / "auger_mlephant.kcl").write_text(kcl)
        print(f"  - wrote zoo-output/auger_mlephant.kcl  ({len(kcl)} chars)")
    meta = {k: v for k, v in job.items() if k not in ("outputs", "code")}
    (OUT_DIR / "auger_mlephant.job.json").write_text(
        json.dumps(meta, indent=2, default=str)
    )


def main() -> int:
    token = os.environ.get("ZOO_API_TOKEN")
    if not token:
        print("ZOO_API_TOKEN not set in env; skipping Zoo probe.")
        return 0
    print(f"BASE = {BASE}")
    print(f"token: len={len(token)}")
    print(f"prompt: {PROMPT!r}")

    kittycad_user_ping(token)
    kittycad_list_conversions(token)

    fmt = os.environ.get("ZOO_TEXT_TO_CAD_FORMAT", "step")
    job = text_to_cad(token, fmt=fmt)
    if job:
        print(f"\nfinal status: {job.get('status')}  prompt-id: {job.get('id')}")
        if job.get("status") == "failed":
            print(f"error: {job.get('error') or job.get('feedback')}")
        save_outputs(job, fmt)
    return 0


if __name__ == "__main__":
    sys.exit(main())

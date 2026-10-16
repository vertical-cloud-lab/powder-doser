"""Iterate on an existing Zoo / ML-ephant text-to-CAD result via
``POST /ml/text-to-cad/iteration`` (PR #5 review comment 4464171767).

The iteration endpoint takes the previous KCL source as
``original_source_code`` and a list of ``source_ranges`` (each with a
prompt + line/column range). Returning a whole-file edit is the simplest
form: one source range that covers the whole file plus a delta prompt.

Usage::

    python zoo_iteration_probe.py                # submit iteration on auger_mlephant.kcl
    python zoo_iteration_probe.py poll <id>      # poll a running iteration

Outputs land under ``cad/meta-tools/zoo-output/iteration/``.
"""
from __future__ import annotations

import base64
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

BASE = "https://api.zoo.dev"
UA = "powder-doser-meta-tools/1.0 (+https://github.com/vertical-cloud-lab/powder-doser)"
HERE = pathlib.Path(__file__).resolve().parent
SRC_KCL = HERE / "zoo-output" / "auger_mlephant.kcl"
OUT_DIR = HERE / "zoo-output" / "iteration"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Targeted delta on top of the original auger: add a side hopper inlet
# (the spec-side TODO noted in the previous Judge-style review — bring
# the auger + tube closer to a single-part design from issue #16) plus
# the small wire-exit notch needed for embedded ERM/solenoid wiring.
ITERATION_PROMPT = (
    "Wrap the existing auger in a coaxial hollow tube of 24 mm outer "
    "diameter (2 mm wall) running the full part height, so the auger "
    "and tube are a single printable assembly. Add a side hopper inlet "
    "as a 12 mm diameter hole through the tube wall, axis perpendicular "
    "to the auger, centered 20 mm below the top spindle. Add a 4 mm "
    "diameter wire-exit notch through the tube wall at the dispense end, "
    "180 degrees opposite the hopper. Keep all existing parameters and "
    "the Archimedes flight unchanged."
)


def _request(method: str, path: str, token: str, body: bytes | None = None,
             content_type: str = "application/json"):
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": UA,
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(BASE + path, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _whole_file_range(src: str) -> dict:
    """Build a SourceRangePrompt that covers the whole file.

    KCL ``SourcePosition`` uses 1-based ``line`` and ``column`` indices,
    matching the editor's gutter numbering (line 0 / column 0 returns
    ``Source range out of bounds`` from the iteration server).
    """
    lines = src.splitlines() or [""]
    return {
        "prompt": ITERATION_PROMPT,
        "range": {
            "start": {"line": 1, "column": 1},
            "end": {"line": len(lines), "column": len(lines[-1]) + 1},
        },
    }


def submit(token: str) -> int:
    src = SRC_KCL.read_text()
    payload = {
        "original_source_code": src,
        "source_ranges": [_whole_file_range(src)],
        "prompt": ITERATION_PROMPT,
        "project_name": "powder-doser-auger-iteration",
    }
    code, body = _request(
        "POST", "/ml/text-to-cad/iteration", token,
        body=json.dumps(payload).encode("utf-8"),
    )
    print(f"submit HTTP {code}")
    if code not in (200, 201, 202):
        print(body[:1000].decode(errors="replace"))
        (OUT_DIR / "submit-error.txt").write_bytes(body)
        return 2
    job = json.loads(body)
    job_id = job.get("id")
    (OUT_DIR / "job-id.txt").write_text(str(job_id))
    (OUT_DIR / "submit-response.json").write_text(
        json.dumps(job, indent=2, default=str))
    print(f"submitted id={job_id} status={job.get('status')}")
    print(f"prompt length: {len(ITERATION_PROMPT)} chars, "
          f"original source: {len(src)} chars")
    return 0


def save_outputs(job: dict) -> None:
    outputs = job.get("outputs") or {}
    for name, b64 in outputs.items():
        try:
            data = base64.b64decode(b64 + "=" * (-len(b64) % 4))
        except Exception as e:
            print(f"  - {name}: not base64 ({e})")
            continue
        safe = pathlib.Path(name).name or "out.bin"
        dst = OUT_DIR / f"iter_{safe}"
        dst.write_bytes(data)
        print(f"  - wrote {dst.relative_to(HERE.parent.parent)}  ({len(data)} bytes)")
    if job.get("code"):
        (OUT_DIR / "iter_auger.kcl").write_text(job["code"])
        print(f"  - wrote iter_auger.kcl  ({len(job['code'])} chars)")
    meta = {k: v for k, v in job.items() if k not in ("outputs", "code")}
    (OUT_DIR / "iter.job.json").write_text(
        json.dumps(meta, indent=2, default=str))


def poll(token: str, job_id: str, deadline_minutes: int = 30) -> int:
    print(f"polling {job_id}")
    deadline = time.time() + deadline_minutes * 60
    job: dict = {}
    while time.time() < deadline:
        code, body = _request("GET", f"/user/text-to-cad/{job_id}", token)
        if code != 200:
            print(f"poll HTTP {code} {body[:200].decode(errors='replace')}")
            return 1
        job = json.loads(body)
        status = job.get("status")
        print(f"  status={status}")
        if status in ("completed", "failed"):
            break
        time.sleep(30)
    if not job:
        print("poll deadline reached, no job state")
        return 1
    print(f"final status: {job.get('status')}")
    if job.get("status") == "failed":
        print(f"error: {job.get('error') or job.get('feedback')}")
    save_outputs(job)
    return 0 if job.get("status") == "completed" else 1


def main(argv: list[str]) -> int:
    token = os.environ.get("ZOO_API_TOKEN")
    if not token:
        print("ZOO_API_TOKEN not set", file=sys.stderr)
        return 1
    if len(argv) >= 2 and argv[1] == "poll":
        jid = argv[2] if len(argv) > 2 else (OUT_DIR / "job-id.txt").read_text().strip()
        return poll(token, jid)
    return submit(token)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

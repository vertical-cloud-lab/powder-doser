"""Submit + poll a Zoo ML-ephant text-to-CAD job for the full powder-doser
system (issue #16, PR #5 review comment 4463659493).

Two modes:

  python zoo_full_system_probe.py            # submit a new job (spends credits)
  python zoo_full_system_probe.py poll <id>  # poll an existing job, save outputs

On a successful poll the STEP / KCL / job metadata are written under
``cad/meta-tools/zoo-output/full-system/`` next to the submit-time job id.
"""
from __future__ import annotations

import base64
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.zoo.dev"
UA = "powder-doser-meta-tools/1.0 (+https://github.com/vertical-cloud-lab/powder-doser)"
OUT_DIR = pathlib.Path(__file__).resolve().parent / "zoo-output" / "full-system"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Verbatim from comment 4463659493 (slightly compressed to fit the
# ML-ephant prompt budget — longer prompts return HTTP 500).
PROMPT = (
    "A 3D-printable powder dispenser housing in mm. "
    "Vertical hollow tube, 24 outside diameter, 20 inside bore, 110 long. "
    "Top: 50x50x6 square flange with four M3 holes on a 42 mm square pattern, "
    "for mounting a NEMA 17 stepper (42x42 footprint). The auger spindle (5 mm) "
    "couples directly to the stepper shaft via a 5x5 set-screw coupling. "
    "Side inlet hopper neck, 12 mm diameter, just below the flange. "
    "Near the bottom (within 25 mm of dispense exit): a 12x4 deep circular pocket "
    "on +X for a 10 mm ERM vibration disc, and a 16x16x12 deep rectangular pocket "
    "on -X for a small solenoid. Each pocket has a 4 mm wire-exit channel. "
    "Dispense exit: chamfered 4 mm hole at the bottom. "
    "Below the exit, a yoke that holds an SG90 servo (23x12x27) so the servo pivots "
    "a 20x12x1.2 deflector blade about the dispense axis. "
    "Back face: a 60x30 mounting boss for a Raspberry Pi Zero 2 W with four M2.5 "
    "holes on a 58x23 grid."
)


def _request(method: str, path: str, token: str, body: bytes | None = None):
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": UA,
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def submit(token: str) -> int:
    fmt = "step"
    payload = json.dumps({"prompt": PROMPT}).encode("utf-8")
    qs = urllib.parse.urlencode({"prompt": PROMPT})
    code, body = _request("POST", f"/ai/text-to-cad/{fmt}?{qs}", token, body=payload)
    print(f"submit HTTP {code}")
    if code not in (200, 201, 202):
        print(body[:1000].decode(errors="replace"))
        (OUT_DIR / "submit-error.txt").write_bytes(body)
        return 2
    job = json.loads(body)
    job_id = job.get("id")
    (OUT_DIR / "job-id.txt").write_text(str(job_id))
    (OUT_DIR / "submit-response.json").write_text(json.dumps(job, indent=2, default=str))
    print(f"submitted id={job_id} status={job.get('status')}")
    print(f"prompt length: {len(PROMPT)} chars")
    return 0


def save_outputs(job: dict) -> None:
    outputs = job.get("outputs") or {}
    for name, b64 in outputs.items():
        try:
            data = base64.b64decode(b64 + "=" * (-len(b64) % 4))
        except Exception as e:
            print(f"  - {name}: not base64 ({e})")
            continue
        safe = pathlib.Path(name).name or "auger.step"
        # Prefix the saved filename so it's distinguishable from the
        # earlier single-part `auger_mlephant.step` artefact.
        dst = OUT_DIR / f"full_system_{safe}"
        dst.write_bytes(data)
        print(f"  - wrote {dst.relative_to(OUT_DIR.parent.parent)}  ({len(data)} bytes)")
    if job.get("code"):
        (OUT_DIR / "full_system.kcl").write_text(job["code"])
        print(f"  - wrote full_system.kcl  ({len(job['code'])} chars)")
    meta = {k: v for k, v in job.items() if k not in ("outputs", "code")}
    (OUT_DIR / "full_system.job.json").write_text(
        json.dumps(meta, indent=2, default=str)
    )


def poll(token: str, job_id: str, deadline_minutes: int = 30) -> int:
    print(f"polling {job_id}")
    deadline = time.time() + deadline_minutes * 60
    poll_every = 30
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
        time.sleep(poll_every)
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
        return poll(token, argv[2] if len(argv) > 2 else
                    (OUT_DIR / "job-id.txt").read_text().strip())
    return submit(token)


if __name__ == "__main__":
    sys.exit(main(sys.argv))


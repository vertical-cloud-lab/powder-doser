"""Phase-1 multi-part text-to-CAD probe (PR #5 review comment 4464317865).

Per the plan posted in this PR thread, the previous one-shot full-system
prompt produced two systematic failures: (a) the auger had an axial slab
removed, and (b) ML-ephant injected a hopper that violated the spec
("internal volume of the auger itself is sufficient"). The fix is to
issue *narrow*, *single-part* prompts in a small parallel batch and
graft the returned solids together later (CadQuery assembly), instead
of asking ML-ephant to solve the assembly all at once.

This script submits five independent ``POST /ai/text-to-cad/{format}``
jobs (one per part listed below), saves the returned ``id`` for every
job to ``zoo-output/multi-part/<part>/job-id.txt`` *before any polling*
so a cold-start resume can fetch results without re-spending evaluate
minutes, then polls them concurrently and writes STEP/KCL/job-meta to
the same per-part directory.

Parts (≤6 sentence prompts, explicit *negative* constraints to defeat
the failure modes seen in 8e90d7e / c48a9d0):

  1. ``auger_solid``         — single-body auger-in-tube, no hopper, no slab.
  2. ``stepper_mount_collar`` — NEMA 11 (28×28×45) flange + ST-FC01 stub.
  3. ``embed_pocket_sleeve`` — slip-on sleeve with ERM + solenoid pockets.
  4. ``servo_yoke``          — HD-1810MG yoke under the dispense exit.
  5. ``pi_mount_bracket``    — Pi Zero 2 W back-plate, 58×23 mm M2.5 grid.

Usage::

    python zoo_multi_part_probe.py submit          # batch-submit all 5
    python zoo_multi_part_probe.py submit auger_solid  # one part only
    python zoo_multi_part_probe.py poll            # poll all stored ids
    python zoo_multi_part_probe.py status          # quick id+status table
"""
from __future__ import annotations

import base64
import concurrent.futures
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
HERE = pathlib.Path(__file__).resolve().parent
OUT_ROOT = HERE / "zoo-output" / "multi-part"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

# Tight per-part prompts. Each one spells out the geometric envelope,
# dimensions, mounting features, and explicit "do NOT" exclusions, so
# ML-ephant cannot drift into an assembly-level interpretation. Numbers
# follow the BoM on the copilot/identify-vibration-motor-solenoid-parts
# branch (Adafruit #1201 ERM, JF-0530B solenoid, HD-1810MG servo, Pi
# Zero 2 W official 58×23 mm grid, NEMA 11 11HS18-0674S stepper).
PARTS: dict[str, str] = {
    "auger_solid": (
        "An Archimedes auger inside a coaxial outer tube, fused as one "
        "single closed solid body. Outer tube diameter 24 mm, wall 2 mm, "
        "total height 100 mm. Internal helical flight: outer radius 9.7 mm, "
        "central shaft diameter 6 mm, single-start helix, 10 mm pitch, "
        "flight thickness 1.6 mm. M3 threaded mounting hole through the "
        "top spindle face on the central axis, and a 2.5 mm diameter "
        "exit hole through the bottom face on the central axis. The "
        "auger and tube must be one watertight body. Do NOT add a side "
        "hopper. Do NOT cut an axial slab or window in the tube wall. "
        "Do NOT model a separate inner channel; the auger flight occupies "
        "the bore directly."
    ),
    "stepper_mount_collar": (
        "A square mounting collar for a NEMA 11 stepper motor. Top face "
        "is a 28 mm × 28 mm square plate, 4 mm thick, with a 22 mm pilot "
        "hole on center and four M2.5 clearance holes on a 23 mm square "
        "bolt circle. Below the plate, a coaxial cylindrical sleeve of "
        "16 mm outer diameter, 5.5 mm bore, 18 mm long, that envelopes a "
        "5 mm × 5 mm jaw coupler (ST-FC01). The bottom of the sleeve has "
        "a 24 mm circular flange 3 mm thick that mates against the top "
        "of a 24 mm OD tube. Do NOT model the stepper motor itself. Do "
        "NOT add wires or screws."
    ),
    "embed_pocket_sleeve": (
        "A thin-walled cylindrical sleeve that slips over a 24 mm OD "
        "tube near its dispense end. Sleeve inner diameter 24.2 mm, "
        "outer diameter 30 mm, height 24 mm. On one side cut a circular "
        "blind pocket 11 mm diameter and 3.6 mm deep for an ERM disc "
        "vibration motor. On the diametrically opposite side cut a "
        "rectangular blind pocket 12 mm × 9 mm × 19 mm deep for a "
        "tubular push-pull solenoid. Both pockets must connect to the "
        "outside of the sleeve via a Ø4 mm wire-exit channel angled "
        "downward 30°. Do NOT cut through to the bore. Do NOT add a "
        "hopper or any other opening."
    ),
    "servo_yoke": (
        "A U-shaped yoke that pivots a 24 mm OD tube about a horizontal "
        "axis below its dispense exit. The yoke is two parallel arms, "
        "each 30 mm × 22 mm × 4 mm, joined by a 30 mm × 24 mm × 4 mm "
        "base plate. The arms are spaced 26 mm apart inside-to-inside. "
        "Each arm has a coaxial Ø6 mm pivot hole 18 mm above the base. "
        "On one arm, add an external boss with the 21-tooth servo spline "
        "footprint of an HD-1810MG metal-gear servo (Ø5.8 mm bore, M3 "
        "horn screw on axis). The base plate has four M3 clearance holes "
        "in a 22 mm × 18 mm rectangular pattern for chassis mounting. Do "
        "NOT model the servo body or the auger tube."
    ),
    "pi_mount_bracket": (
        "A flat back-plate bracket for a Raspberry Pi Zero 2 W. Plate "
        "outline 70 mm × 32 mm × 3 mm. Four M2.5 stand-off bosses 4 mm "
        "tall and 5 mm diameter, located on the official Pi Zero 2 W "
        "58 mm × 23 mm rectangular hole pattern, centered on the plate. "
        "Two slot mounting holes (4 mm wide, 12 mm long) at each short "
        "end of the plate, on the long-axis centerline, for chassis "
        "attachment. Add a 16 mm × 8 mm rectangular cable cut-out "
        "centered on one long edge for the GPIO ribbon. Do NOT model "
        "the Raspberry Pi itself. Do NOT add a lid or cover."
    ),
}


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


def _part_dir(name: str) -> pathlib.Path:
    d = OUT_ROOT / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def submit_one(token: str, name: str, prompt: str, fmt: str = "step") -> str | None:
    d = _part_dir(name)
    qs = urllib.parse.urlencode({"prompt": prompt})
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    code, body = _request("POST", f"/ai/text-to-cad/{fmt}?{qs}", token, body=payload)
    print(f"[{name}] submit HTTP {code}")
    if code not in (200, 201, 202):
        (d / "submit-error.txt").write_bytes(body)
        print(f"[{name}] submit failed: {body[:300].decode(errors='replace')}")
        return None
    job = json.loads(body)
    jid = job.get("id")
    # Persist the id BEFORE doing anything else so cold-start resume works.
    (d / "job-id.txt").write_text(str(jid))
    (d / "submit-response.json").write_text(json.dumps(job, indent=2, default=str))
    (d / "prompt.txt").write_text(prompt)
    print(f"[{name}] id={jid} status={job.get('status')}")
    return jid


def save_job(name: str, job: dict) -> None:
    d = _part_dir(name)
    outputs = job.get("outputs") or {}
    for fname, b64 in outputs.items():
        try:
            data = base64.b64decode(b64 + "=" * (-len(b64) % 4))
        except Exception as e:
            print(f"[{name}]   - {fname}: not base64 ({e})")
            continue
        safe = pathlib.Path(fname).name or f"{name}.bin"
        dst = d / safe
        dst.write_bytes(data)
        print(f"[{name}]   - wrote {dst.name} ({len(data)} bytes)")
    if job.get("code"):
        (d / f"{name}.kcl").write_text(job["code"])
        print(f"[{name}]   - wrote {name}.kcl ({len(job['code'])} chars)")
    meta = {k: v for k, v in job.items() if k not in ("outputs", "code")}
    (d / "job.json").write_text(json.dumps(meta, indent=2, default=str))


def poll_one(token: str, name: str, job_id: str,
             deadline_minutes: int = 30, every_s: int = 20) -> str:
    d = _part_dir(name)
    deadline = time.time() + deadline_minutes * 60
    last = "unknown"
    while time.time() < deadline:
        code, body = _request("GET", f"/user/text-to-cad/{job_id}", token)
        if code != 200:
            print(f"[{name}] poll HTTP {code}: {body[:200].decode(errors='replace')}")
            return "http_error"
        job = json.loads(body)
        last = job.get("status") or "unknown"
        print(f"[{name}] status={last}")
        if last in ("completed", "failed"):
            save_job(name, job)
            if last == "failed":
                err = job.get("error") or job.get("feedback")
                (d / "error.txt").write_text(str(err))
            return last
        time.sleep(every_s)
    return f"timeout({last})"


def submit_batch(token: str, names: list[str]) -> dict[str, str]:
    """Submit jobs sequentially (cheap), but kick off all 5 fast and persist
    the ids to disk before any polling so a session restart can resume."""
    ids: dict[str, str] = {}
    for n in names:
        jid = submit_one(token, n, PARTS[n])
        if jid:
            ids[n] = jid
    (OUT_ROOT / "job-ids.json").write_text(json.dumps(ids, indent=2))
    print(f"\nsubmitted {len(ids)}/{len(names)}; ids in {OUT_ROOT/'job-ids.json'}")
    return ids


def poll_batch(token: str, ids: dict[str, str]) -> dict[str, str]:
    """Poll all jobs concurrently with a thread pool."""
    results: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(ids) or 1) as ex:
        futs = {ex.submit(poll_one, token, n, jid): n for n, jid in ids.items()}
        for fut in concurrent.futures.as_completed(futs):
            n = futs[fut]
            try:
                results[n] = fut.result()
            except Exception as e:
                results[n] = f"exception:{e!s}"
    (OUT_ROOT / "results.json").write_text(json.dumps(results, indent=2))
    print("\n== Poll summary ==")
    for n, s in results.items():
        print(f"  {n:24s} {s}")
    return results


def load_ids() -> dict[str, str]:
    f = OUT_ROOT / "job-ids.json"
    if f.exists():
        return json.loads(f.read_text())
    # Fall back to per-part job-id.txt files (e.g. partial submit).
    ids = {}
    for n in PARTS:
        jf = OUT_ROOT / n / "job-id.txt"
        if jf.exists():
            ids[n] = jf.read_text().strip()
    return ids


def cmd_status(token: str) -> int:
    ids = load_ids()
    if not ids:
        print("no stored job ids; run `submit` first")
        return 1
    print(f"{'part':<24s} {'id':<40s} status")
    for n, jid in ids.items():
        code, body = _request("GET", f"/user/text-to-cad/{jid}", token)
        if code != 200:
            print(f"{n:<24s} {jid:<40s} HTTP {code}")
            continue
        job = json.loads(body)
        print(f"{n:<24s} {jid:<40s} {job.get('status')}")
    return 0


def main(argv: list[str]) -> int:
    token = os.environ.get("ZOO_API_TOKEN")
    if not token:
        print("ZOO_API_TOKEN not set", file=sys.stderr)
        return 1
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "submit":
        names = argv[2:] if len(argv) > 2 else list(PARTS)
        unknown = [n for n in names if n not in PARTS]
        if unknown:
            print(f"unknown parts: {unknown}; choose from {list(PARTS)}")
            return 1
        ids = submit_batch(token, names)
        return 0 if ids else 2
    if cmd == "poll":
        ids = load_ids()
        if not ids:
            print("no stored ids; nothing to poll")
            return 1
        results = poll_batch(token, ids)
        return 0 if all(v == "completed" for v in results.values()) else 1
    if cmd == "status":
        return cmd_status(token)
    print(f"unknown command: {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

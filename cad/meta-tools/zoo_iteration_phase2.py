"""Phase 2 iteration probes for the multi-part workflow.

For the parts that came back from Phase 1 with observable defects, send
a tightly-scoped delta prompt via ``POST /ml/text-to-cad/iteration`` to
the *original part's* KCL source. The iteration endpoint takes
``original_source_code`` + ``source_ranges`` (1-based line/column —
line 0 returns 400, see the ``zoo iteration api`` repo memo) and
returns patched KCL only (no STEP blob — convert via ``kcl_to_step.py``
as for Phase 1).

Defects observed in Phase 1 (rendered PNGs under
``zoo-output/multi-part/renders/``):

* ``auger_solid`` — 4 disjoint solids in the returned STEP instead of a
  single fused body. Iteration: ``union`` everything into one solid.
* ``stepper_mount_collar`` — 2 solids (plate + sleeve not fused).
  Iteration: ``union`` plate + sleeve + flange.
* ``embed_pocket_sleeve`` — 3 solids and 54 mm X-extent (vs the
  prompted 30 mm OD), so the wire-exit channels became separate
  protruding tubes. Iteration: cut the channels into the existing
  sleeve body instead of adding tubes.

``servo_yoke`` and ``pi_mount_bracket`` came back with 1 solid each and
sensible bboxes — no Phase 2 iteration needed.

Usage::

    python zoo_iteration_phase2.py submit       # submit all 3
    python zoo_iteration_phase2.py submit auger_solid
    python zoo_iteration_phase2.py poll         # poll all submitted
    python zoo_iteration_phase2.py status
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
import urllib.request

BASE = os.environ.get("ZOO_BASE_URL", "https://api.zoo.dev")
UA = "powder-doser-meta-tools/1.0 (+https://github.com/vertical-cloud-lab/powder-doser)"
HERE = pathlib.Path(__file__).resolve().parent
PHASE1_ROOT = HERE / "zoo-output" / "multi-part"
OUT_ROOT = HERE / "zoo-output" / "multi-part-iter"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

ITERATIONS: dict[str, str] = {
    "auger_solid": (
        "The current model returns 4 disjoint solids. Combine the outer "
        "tube, the central shaft, and the helical flight into a single "
        "fused watertight body using a union/boolean-add operation. The "
        "resulting STEP must contain exactly one solid. Keep all "
        "geometry and parameters unchanged; only change the boolean "
        "structure so the parts merge."
    ),
    "stepper_mount_collar": (
        "Fuse the top mounting plate, the cylindrical sleeve below it, "
        "and the bottom 24 mm flange into a single solid via union. "
        "Verify the four M2.5 bolt holes pass cleanly through the plate "
        "and that the 22 mm pilot hole is concentric with the 5.5 mm "
        "coupler bore. The resulting STEP must contain exactly one "
        "solid. Do not change any dimensions."
    ),
    "embed_pocket_sleeve": (
        "The wire-exit channels are currently modelled as solid "
        "protruding tubes outside the sleeve, making the part 54 mm "
        "wide instead of the intended 30 mm OD. Replace each external "
        "tube with a Ø4 mm cylindrical hole CUT into the existing "
        "sleeve wall, angled 30 degrees downward, connecting the "
        "respective embed pocket to the outer cylindrical surface of "
        "the sleeve. The final outer envelope must be a 30 mm OD "
        "cylinder of height 24 mm — no protrusions. Keep the ERM and "
        "solenoid pockets as before."
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


def _whole_file_range(src: str, prompt: str) -> dict:
    """1-based line/column range covering the whole file (line 0 → 400)."""
    lines = src.splitlines() or [""]
    return {
        "prompt": prompt,
        "range": {
            "start": {"line": 1, "column": 1},
            "end": {"line": len(lines), "column": len(lines[-1]) + 1},
        },
    }


def _part_dir(name: str) -> pathlib.Path:
    d = OUT_ROOT / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def submit_one(token: str, name: str, prompt: str) -> str | None:
    src_kcl = PHASE1_ROOT / name / f"{name}.kcl"
    if not src_kcl.exists():
        print(f"[{name}] missing Phase-1 KCL at {src_kcl}")
        return None
    src = src_kcl.read_text()
    payload = {
        "original_source_code": src,
        "source_ranges": [_whole_file_range(src, prompt)],
        "prompt": prompt,
        "project_name": f"powder-doser-{name}-iter",
    }
    code, body = _request(
        "POST", "/ml/text-to-cad/iteration", token,
        body=json.dumps(payload).encode("utf-8"),
    )
    print(f"[{name}] submit HTTP {code}")
    d = _part_dir(name)
    if code not in (200, 201, 202):
        (d / "submit-error.txt").write_bytes(body)
        print(f"[{name}] {body[:300].decode(errors='replace')}")
        return None
    job = json.loads(body)
    jid = job.get("id")
    (d / "job-id.txt").write_text(str(jid))
    (d / "submit-response.json").write_text(json.dumps(job, indent=2, default=str))
    (d / "delta-prompt.txt").write_text(prompt)
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
        (d / safe).write_bytes(data)
        print(f"[{name}]   - wrote {safe} ({len(data)} bytes)")
    if job.get("code"):
        (d / f"{name}.kcl").write_text(job["code"])
        print(f"[{name}]   - wrote {name}.kcl ({len(job['code'])} chars)")
    meta = {k: v for k, v in job.items() if k not in ("outputs", "code")}
    (d / "job.json").write_text(json.dumps(meta, indent=2, default=str))


def poll_one(token: str, name: str, job_id: str,
             deadline_minutes: int = 30, every_s: int = 20) -> str:
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
                (_part_dir(name) / "error.txt").write_text(str(err))
            return last
        time.sleep(every_s)
    return f"timeout({last})"


def submit_batch(token: str, names: list[str]) -> dict[str, str]:
    ids: dict[str, str] = {}
    for n in names:
        jid = submit_one(token, n, ITERATIONS[n])
        if jid:
            ids[n] = jid
    (OUT_ROOT / "job-ids.json").write_text(json.dumps(ids, indent=2))
    print(f"\nsubmitted {len(ids)}/{len(names)}; ids in {OUT_ROOT/'job-ids.json'}")
    return ids


def poll_batch(token: str, ids: dict[str, str]) -> dict[str, str]:
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
    print("\n== Phase-2 poll summary ==")
    for n, s in results.items():
        print(f"  {n:24s} {s}")
    return results


def load_ids() -> dict[str, str]:
    f = OUT_ROOT / "job-ids.json"
    if f.exists():
        return json.loads(f.read_text())
    return {n: (OUT_ROOT / n / "job-id.txt").read_text().strip()
            for n in ITERATIONS if (OUT_ROOT / n / "job-id.txt").exists()}


def cmd_status(token: str) -> int:
    ids = load_ids()
    if not ids:
        print("no stored ids; run `submit` first")
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
        names = argv[2:] if len(argv) > 2 else list(ITERATIONS)
        unknown = [n for n in names if n not in ITERATIONS]
        if unknown:
            print(f"unknown parts: {unknown}; choose from {list(ITERATIONS)}")
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

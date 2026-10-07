#!/usr/bin/env python3
"""Fetch the Whitehead / single-run calibration Edison result (PR #124).

Usage: fetch_whitehead_da_result.py [wait [max_minutes]]

Reads the trajectory id recorded by run_whitehead_da_query.py in
query_out/whitehead_da.task.json and writes, next to it:
  whitehead_da.answer.md       the formatted answer
  whitehead_da.result.json     the full verbose trajectory dump
  whitehead_da.<field>.json    bibliography/reference fields, when present
Safe to re-run; without "wait" it exits if the task is not terminal yet.  With
"wait" it polls every 2 min, giving up after max_minutes (default 45)."""
import json
import os
import sys
import time
from pathlib import Path

from edison_client import EdisonClient
from edison_client.models.rest import ExecutionStatus

HERE = Path(__file__).parent
OUT = HERE / "query_out"
NAME = "whitehead_da"


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


def _terminal(status) -> bool:
    try:
        return ExecutionStatus(status).is_terminal_state()
    except Exception:
        return str(status) in {"success", "fail", "failed", "cancelled", "error", "truncated"}


def _dump(obj) -> dict:
    return obj.model_dump(mode="json") if hasattr(obj, "model_dump") else dict(obj)


def main() -> None:
    wait = len(sys.argv) > 1 and sys.argv[1] == "wait"
    max_min = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
    client = EdisonClient(api_key=_api_key())
    tid = json.loads((OUT / f"{NAME}.task.json").read_text())["trajectory_id"]
    t0 = time.monotonic()
    while True:
        r = client.get_task(tid)
        status = getattr(r, "status", None)
        print(f"{NAME}: status {status} ({(time.monotonic() - t0) / 60:.1f} min)", flush=True)
        if _terminal(status):
            break
        if not wait or time.monotonic() - t0 > max_min * 60:
            return
        time.sleep(120)
    dump = _dump(r)
    answer = (
        getattr(r, "formatted_answer", None)
        or getattr(r, "answer", None)
        or dump.get("formatted_answer")
        or dump.get("answer")
        or ""
    )
    (OUT / f"{NAME}.answer.md").write_text(answer or "(no answer field)")
    print(f"{NAME}: wrote answer ({len(answer or '')} chars)", flush=True)
    for key in ("bibliography", "references", "context", "used_references"):
        val = dump.get(key)
        if val:
            (OUT / f"{NAME}.{key}.json").write_text(json.dumps(val, indent=2, default=str))
            print(f"{NAME}: wrote {key}", flush=True)
    full = _dump(client.get_task(tid, verbose=True))
    (OUT / f"{NAME}.result.json").write_text(json.dumps(full, indent=2, default=str))
    print(f"{NAME}: wrote full trajectory ({len(json.dumps(full, default=str))} chars)", flush=True)


if __name__ == "__main__":
    main()

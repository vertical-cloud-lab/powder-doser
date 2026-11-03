#!/usr/bin/env python3
"""Fetch an Edison analysis result by name (issue #123 / PR #124).

Usage: fetch_analysis_result.py <name> [wait]

Reads query_out/<name>.task.json (written by the corresponding run_* script) and
writes <name>.answer.md plus any bibliography artifacts next to it. Safe to
re-run; without "wait" it exits if the task is not terminal yet."""
import json
import os
import sys
import time
from pathlib import Path

from edison_client import EdisonClient
from edison_client.models.rest import ExecutionStatus

HERE = Path(__file__).parent
OUT = HERE / "query_out"


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


def main() -> None:
    name = sys.argv[1]
    wait = len(sys.argv) > 2 and sys.argv[2] == "wait"
    client = EdisonClient(api_key=_api_key())
    tid = json.loads((OUT / f"{name}.task.json").read_text())["trajectory_id"]
    while True:
        r = client.get_task(tid)
        status = getattr(r, "status", None)
        try:
            terminal = ExecutionStatus(status).is_terminal_state()
        except Exception:
            terminal = str(status) in {"success", "fail", "cancelled", "truncated"}
        print(f"{name}: status {status}", flush=True)
        if terminal:
            break
        if not wait:
            return
        time.sleep(240)
    dump = r.model_dump(mode="json")
    answer = (
        getattr(r, "formatted_answer", None)
        or getattr(r, "answer", None)
        or dump.get("formatted_answer")
        or dump.get("answer")
        or ""
    )
    (OUT / f"{name}.answer.md").write_text(answer or "(no answer field)")
    print(f"{name}: wrote answer ({len(answer or '')} chars)", flush=True)
    for key in ("bibliography", "references", "context", "used_references"):
        val = dump.get(key)
        if val:
            (OUT / f"{name}.{key}.json").write_text(json.dumps(val, indent=2, default=str))
            print(f"{name}: wrote {key}", flush=True)


if __name__ == "__main__":
    main()

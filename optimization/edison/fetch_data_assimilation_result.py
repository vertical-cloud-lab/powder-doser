#!/usr/bin/env python3
"""Fetch the data-assimilation Edison result for issue #123 / PR #124.

Reads the trajectory id recorded by run_data_assimilation_query.py in
query_out/data_assimilation.task.json and writes data_assimilation.answer.md
(plus bibliography files when present) next to it. Safe to re-run; skips the
task if it is not terminal yet. Pass "wait" to poll until terminal."""
import json
import os
import sys
import time
from pathlib import Path

from edison_client import EdisonClient
from edison_client.models.rest import ExecutionStatus

HERE = Path(__file__).parent
OUT = HERE / "query_out"
NAME = "data_assimilation"


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


def main() -> None:
    wait = len(sys.argv) > 1 and sys.argv[1] == "wait"
    client = EdisonClient(api_key=_api_key())
    tid = json.loads((OUT / f"{NAME}.task.json").read_text())["trajectory_id"]
    while True:
        r = client.get_task(tid)
        status = getattr(r, "status", None)
        try:
            terminal = ExecutionStatus(status).is_terminal_state()
        except Exception:
            terminal = str(status) in {"success", "fail", "cancelled", "truncated"}
        print(f"{NAME}: status {status}", flush=True)
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
    (OUT / f"{NAME}.answer.md").write_text(answer or "(no answer field)")
    print(f"{NAME}: wrote answer ({len(answer or '')} chars)", flush=True)
    for key in ("bibliography", "references", "context", "used_references"):
        val = dump.get(key)
        if val:
            (OUT / f"{NAME}.{key}.json").write_text(json.dumps(val, indent=2, default=str))
            print(f"{NAME}: wrote {key}", flush=True)


if __name__ == "__main__":
    main()

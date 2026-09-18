#!/usr/bin/env python3
"""Fetch the three follow-up Edison results for issue #123 / PR #124.

Reads the trajectory ids recorded by run_followup_queries.py in
query_out/<name>.task.json and writes <name>.answer.md (plus bibliography
files when present) next to them. Safe to re-run; skips tasks that are not
terminal yet."""
import json
import os
from pathlib import Path

from edison_client import EdisonClient
from edison_client.models.rest import ExecutionStatus

HERE = Path(__file__).parent
OUT = HERE / "query_out"

NAMES = ("mpc_followup", "physics_engines", "particle_methods")


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


def main() -> None:
    client = EdisonClient(api_key=_api_key())
    for name in NAMES:
        task_file = OUT / f"{name}.task.json"
        if not task_file.exists():
            print(f"{name}: no task file, skipping", flush=True)
            continue
        tid = json.loads(task_file.read_text())["trajectory_id"]
        r = client.get_task(tid)
        status = getattr(r, "status", None)
        try:
            terminal = ExecutionStatus(status).is_terminal_state()
        except Exception:
            terminal = status in {"success", "fail", "cancelled", "truncated"}
        print(f"{name}: status {status}", flush=True)
        if not terminal:
            continue
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
                (OUT / f"{name}.{key}.json").write_text(
                    json.dumps(val, indent=2, default=str)
                )


if __name__ == "__main__":
    main()

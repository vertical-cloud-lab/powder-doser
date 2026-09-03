#!/usr/bin/env python3
"""Fetch the completed Edison LITERATURE_HIGH result for issue #123.

Reads the trajectory id recorded in query_out/query.task.json and writes the
answer + bibliography next to it. See run_control_theory_query.py for the
script that created the task."""
import json
import os
from pathlib import Path

from edison_client import EdisonClient

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
    tid = json.loads((OUT / "query.task.json").read_text())["trajectory_id"]
    client = EdisonClient(api_key=_api_key())
    r = client.get_task(tid)
    status = getattr(r, "status", None)
    print("status:", status, flush=True)
    dump = r.model_dump(mode="json")
    answer = (
        getattr(r, "formatted_answer", None)
        or getattr(r, "answer", None)
        or dump.get("formatted_answer")
        or dump.get("answer")
        or ""
    )
    (OUT / "query.answer.md").write_text(answer or "(no answer field)")
    print("answer chars:", len(answer or ""), flush=True)
    for key in ("bibliography", "references", "context", "used_references"):
        val = dump.get(key)
        if val:
            (OUT / f"query.{key}.json").write_text(json.dumps(val, indent=2, default=str))
            print("wrote", key, flush=True)


if __name__ == "__main__":
    main()

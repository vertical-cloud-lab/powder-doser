"""Fetch the Edison Scientific result for the alternative-powder-dosing
feedback query (issue #12) and persist it to ``edison_result.md`` and
``edison_result.json`` next to this script.

Reads the API key from the ``EDISON_API_KEY`` environment variable and
the task id from ``edison_query.json``. Idempotent — safe to re-run.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

from edison_client import EdisonClient

HERE = pathlib.Path(__file__).resolve().parent


def main() -> int:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        sys.stderr.write(
            "EDISON_API_KEY not set in the environment; cannot fetch.\n"
        )
        return 1

    query_meta = json.loads((HERE / "edison_query.json").read_text())
    task_id = query_meta.get("task_id")
    if not task_id:
        sys.stderr.write("No task_id recorded in edison_query.json.\n")
        return 1

    client = EdisonClient(api_key=api_key)
    task = client.get_task(task_id)
    payload = task.model_dump() if hasattr(task, "model_dump") else dict(task)

    (HERE / "edison_result.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )

    formatted = payload.get("formatted_answer") or payload.get("answer") or ""
    (HERE / "edison_result.md").write_text(formatted, encoding="utf-8")

    print(
        f"Fetched task {task_id}; status={payload.get('status')}; "
        f"wrote edison_result.{{json,md}} ({len(formatted)} chars)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Fetch the Edison Scientific **analysis** result for the per-concept
alternative-dosing review. Reads task id from ``edison_analysis_query.json``
and persists the answer next to it as ``edison_analysis_result.{md,json}``.

Idempotent — safe to re-run.
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

    query_meta_path = HERE / "edison_analysis_query.json"
    query_meta = json.loads(query_meta_path.read_text())
    task_id = query_meta.get("task_id")
    if not task_id:
        sys.stderr.write("No task_id recorded in edison_analysis_query.json.\n")
        return 1

    client = EdisonClient(api_key=api_key)
    task = client.get_task(task_id)
    payload = task.model_dump() if hasattr(task, "model_dump") else dict(task)

    (HERE / "edison_analysis_result.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )

    formatted = payload.get("formatted_answer") or payload.get("answer") or ""
    (HERE / "edison_analysis_result.md").write_text(
        formatted or f"# Edison analysis task `{task_id}`\n\n"
        f"status: `{payload.get('status')}`\n\n"
        "No formatted answer was returned.\n",
        encoding="utf-8",
    )

    print(
        f"Fetched analysis task {task_id}; status={payload.get('status')}; "
        f"wrote edison_analysis_result.{{json,md}} ({len(formatted)} chars)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

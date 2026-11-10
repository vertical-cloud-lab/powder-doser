#!/usr/bin/env python3
"""Wait for and archive the composition-error Edison LITERATURE task.

Reads the task id from edison_task.json (written by dispatch_lit_query.py),
polls every 90 s until the task is terminal or ``--max-minutes`` (default 35)
have passed since dispatch, then writes next to this script:

  composition_error_lit.task.json        full task payload (secrets removed)
  composition_error_lit.answer.md        formatted answer
  composition_error_lit.references.md    numbered reference list
  fetch_status.json                      final status and timestamps

Run as one blocking call (the wait is inside Python, not the shell):
  python paper/composition_error/fetch_results.py
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from edison_client import EdisonClient

HERE = Path(__file__).resolve().parent
NAME = "composition_error_lit"
TERMINAL = {"success", "fail", "failed", "cancelled", "error"}
SECRET_KEYS = {
    "api_key", "apikey", "access_token", "refresh_token", "id_token",
    "authorization", "password", "secret", "email", "user_email",
}


def scrub(obj):
    """Drop keys that could hold credentials; keep everything else."""
    if isinstance(obj, dict):
        return {k: ("[removed]" if str(k).lower() in SECRET_KEYS else scrub(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [scrub(v) for v in obj]
    return obj


def dump(task) -> dict:
    if hasattr(task, "model_dump"):
        return task.model_dump(mode="json")
    return json.loads(json.dumps(dict(task), default=str))


def archive(client: EdisonClient, task_id: str, api_key: str) -> str:
    task = client.get_task(task_id=task_id, verbose=True)
    status = str(task.status)
    data = scrub(dump(task))
    text = json.dumps(data, indent=2, default=str)
    if api_key and api_key in text:  # never write the key, whatever field it hides in
        text = text.replace(api_key, "[removed]")
    (HERE / f"{NAME}.task.json").write_text(text + "\n")
    answer, refs = "", ""
    try:
        pqa = data["environment_frame"]["state"]["state"]["response"]["answer"]
        answer = pqa.get("formatted_answer") or pqa.get("answer") or ""
        refs = pqa.get("references") or ""
    except (KeyError, TypeError, AttributeError):
        answer = data.get("formatted_answer") or data.get("answer") or ""
    if answer:
        (HERE / f"{NAME}.answer.md").write_text(str(answer).rstrip() + "\n")
    if refs:
        (HERE / f"{NAME}.references.md").write_text(str(refs).rstrip() + "\n")
    print(f"archived: status={status} answer_chars={len(str(answer))} "
          f"refs_chars={len(str(refs))}", flush=True)
    return status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-minutes", type=float, default=35.0,
                    help="stop waiting this long after dispatch")
    ap.add_argument("--interval", type=float, default=90.0)
    args = ap.parse_args()

    api_key = os.environ["EDISON_PLATFORM_API_KEY"]
    client = EdisonClient(api_key=api_key)
    rec = json.loads((HERE / "edison_task.json").read_text())
    task_id = rec["task_id"]
    dispatched = datetime.fromisoformat(rec["dispatched_utc"])
    deadline = dispatched.timestamp() + 60 * args.max_minutes

    status = "unknown"
    while True:
        task = client.get_task(task_id=task_id, verbose=True)
        status = str(task.status)
        now = datetime.now(timezone.utc)
        print(f"{now:%H:%M:%S}Z status: {status}", flush=True)
        if status in TERMINAL or time.time() >= deadline:
            break
        time.sleep(args.interval)

    if status in TERMINAL:
        status = archive(client, task_id, api_key)
    (HERE / "fetch_status.json").write_text(json.dumps({
        "task_id": task_id,
        "status": status,
        "checked_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dispatched_utc": rec["dispatched_utc"],
        "archived": status in TERMINAL,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()

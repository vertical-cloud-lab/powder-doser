#!/usr/bin/env python3
"""Dispatch (without waiting) the round-2 Edison ANALYSIS mock review of the
revised base powder-doser manuscript.

The revised draft addresses the human PR #97 review feedback (HR-100A balance,
no hopper, AI-vs-human signposting, Zoo Design Studio / Zookeeper coverage,
corrected tap-collar narrative).  Inputs are uploaded as a single zipped
collection (same convention as run_mock_review.py); the task id is written to
mock_review_r2_task_ids.json so a later session can fetch the result with
``client.get_task(task_id, verbose=True)``.

Usage:
  export EDISON_API_KEY=...
  python dispatch_mock_review_r2.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

from run_mock_review import QUERY

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"

TAG = "powder-doser-mock-review-r2"


def main() -> None:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        raise SystemExit("EDISON_API_KEY is not set.")

    client = EdisonClient(api_key=api_key)

    print(f"Uploading {INPUTS} as a zipped collection...", flush=True)
    stored = client.store_file_content(
        name="powder_doser_mock_review_r2_inputs",
        file_path=str(INPUTS),
        as_collection=True,
    )
    file_uri = f"data_entry:{stored.data_storage.id}"
    print(f"  uploaded -> {file_uri}", flush=True)

    task = {"name": JobNames.ANALYSIS, "query": QUERY, "tags": [TAG]}
    print("Dispatching ANALYSIS task (no wait)...", flush=True)
    task_id = str(client.create_task(task, files=[file_uri]))
    (HERE / "mock_review_r2_task_ids.json").write_text(
        json.dumps({"mock_review_r2": task_id, "inputs": file_uri}, indent=2)
    )
    print(f"dispatched task id={task_id}", flush=True)


if __name__ == "__main__":
    main()

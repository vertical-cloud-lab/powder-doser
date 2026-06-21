#!/usr/bin/env python3
"""Dispatch an Edison Scientific ANALYSIS task that reviews the revised
base powder-doser manuscript after the PR #97 author-feedback revision
(BYU/Acceleration-Consortium affiliations, corrected authorship, removed
advisory-board/NASA claims, added AI-usage metrics, figure-overlap fixes).

Inputs (uploaded as a single zipped collection, per the ANALYSIS convention):
  inputs/main.pdf   -- the revised manuscript draft
  inputs/si.pdf     -- the supplementary information

Outputs are written next to this script as
revision_review.{task.json,answer.md,notebook.ipynb} and the task id is
recorded in revision_review_task_ids.json.

Usage:
  export EDISON_API_KEY=...
  python dispatch_revision_review.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"

QUERY = (
    "The attached collection contains the revised manuscript (main.pdf) and "
    "its supplementary information (si.pdf) for an open-source, 3D-printed "
    "auger powder doser designed with generative AI, prepared as a "
    "hardware-focused Full Paper for Digital Discovery (RSC). This draft was "
    "revised per author feedback: it reports only completed work with no "
    "synthetic or placeholder dispensing data, frames dispensing-accuracy "
    "numbers as design targets, and emphasises the generative-AI CAD case "
    "study. Provide a thorough analytical review: "
    "(1) Assess scope fit and significance for Digital Discovery's hardware "
    "Full Paper track. "
    "(2) Identify the strongest and weakest aspects of the manuscript as "
    "written, citing specific sections, figures, and tables. "
    "(3) Check internal consistency of the claims (cost, components, "
    "closed-loop control, AI-vs-human signposting, tool comparison) against "
    "the figures and SI. "
    "(4) Flag any remaining placeholder-like or unsupported statements. "
    "(5) Comment on figure clarity and whether any panel text appears "
    "crowded or mislabelled. "
    "(6) Finish with a concise, priority-ranked list of the most important "
    "concrete revisions the authors should make before submission. "
    "Assess the manuscript exactly as written; do not invent results."
)

TAG = "powder-doser-revision-review"


def _extract_answer(data: dict) -> str:
    try:
        return data["environment_frame"]["state"]["state"]["answer"] or ""
    except (KeyError, TypeError):
        pass
    return data.get("answer") or data.get("formatted_answer") or ""


def _extract_notebook(data: dict):
    try:
        nb = data["environment_frame"]["state"]["state"]["nb_state"]
        if nb:
            return nb
    except (KeyError, TypeError):
        pass
    return data.get("notebook")


def main() -> None:
    api_key = (
        os.environ.get("EDISON_API_KEY")
        or os.environ.get("EDISON_PLATFORM_API_KEY")
    )
    if not api_key:
        raise SystemExit("EDISON_API_KEY is not set.")
    api_key = api_key.strip()

    client = EdisonClient(api_key=api_key)

    print(f"Uploading {INPUTS} as a zipped collection...", flush=True)
    stored = client.store_file_content(
        name="powder_doser_revision_review_inputs",
        file_path=str(INPUTS),
        as_collection=True,
    )
    entry_id = stored.data_storage.id
    file_uri = f"data_entry:{entry_id}"
    print(f"  uploaded -> {file_uri}", flush=True)

    task = {"name": JobNames.ANALYSIS, "query": QUERY, "tags": [TAG]}
    print("Dispatching ANALYSIS task...", flush=True)
    results = client.run_tasks_until_done(
        [task], verbose=True, progress_bar=False, timeout=5400, files=[file_uri]
    )
    result = results[0]
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)

    (HERE / "revision_review.task.json").write_text(
        json.dumps(data, default=str, indent=2)
    )
    answer = _extract_answer(data)
    (HERE / "revision_review.answer.md").write_text(answer)
    nb = _extract_notebook(data)
    if nb is not None:
        (HERE / "revision_review.notebook.ipynb").write_text(
            json.dumps(nb, default=str, indent=2)
        )
    task_id = str(data.get("task_id") or data.get("id") or "")
    (HERE / "revision_review_task_ids.json").write_text(
        json.dumps({"revision_review": task_id}, indent=2)
    )
    print(
        f"status={data.get('status')} id={task_id} answer_chars={len(answer)}",
        flush=True,
    )


if __name__ == "__main__":
    main()

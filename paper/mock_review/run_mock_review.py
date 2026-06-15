#!/usr/bin/env python3
"""Run an Edison Scientific ANALYSIS task that produces mock editor and
reviewer feedback for the base powder-doser manuscript.

Inputs (uploaded as a single zipped collection, per the ANALYSIS convention):
  inputs/main.pdf                 -- the manuscript draft
  inputs/si.pdf                   -- the supplementary information
  inputs/16-journal-editors.md    -- Digital Discovery editor scouting (PR #91)
  inputs/17-suggested-reviewers.md-- candidate reviewer personas (PR #91)

Outputs are written next to this script as
mock_review.{task.json,answer.md,notebook.ipynb}.

Usage:
  export EDISON_API_KEY=...
  python run_mock_review.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"

QUERY = (
    "The attached collection contains a manuscript draft (main.pdf) and its "
    "supplementary information (si.pdf) prepared for submission to Digital "
    "Discovery (RSC) as a hardware-focused Full Paper, plus two scouting notes "
    "(16-journal-editors.md, 17-suggested-reviewers.md) listing the journal's "
    "editors and a pool of plausible reviewers with their research foci. "
    "Act as a full mock peer-review panel for this manuscript. Specifically: "
    "(1) As the handling editor (persona: Alan Aspuru-Guzik, Editor-in-Chief, "
    "AI-for-chemistry/self-driving-labs), write a short editor's assessment: "
    "scope fit for Digital Discovery's hardware Full Paper track, overall "
    "novelty/significance, and an initial decision recommendation. "
    "(2) Write three detailed, independent reviewer reports, each in the "
    "persona of a DIFFERENT reviewer drawn from 17-suggested-reviewers.md, "
    "choosing personas that span (a) self-driving labs / lab automation (e.g. "
    "Milad Abolhasani or Keith Brown), (b) powder dosing / feeder metrology "
    "(e.g. Johannes Khinast or Fernando Muzzio), and (c) LLM/generative CAD "
    "(e.g. Wojciech Matusik or Adriana Schulz). Each report should reflect "
    "that persona's expertise and priorities, and should contain: a summary "
    "of the contribution as they would see it; major comments (numbered, "
    "specific, actionable, citing section/figure numbers from the PDF); minor "
    "comments (numbered); and a recommendation (accept / minor revision / "
    "major revision / reject). Do not exclude any persona for conflicts -- "
    "this is a mock exercise. "
    "(3) Finish with a consolidated, de-duplicated, priority-ranked action "
    "list for the authors: the 10-15 most important concrete revisions across "
    "all reports, each tagged with which reviewer(s) raised it. "
    "Assess the manuscript exactly as written; quote or reference specific "
    "passages, figures, and tables where possible."
)

TAG = "powder-doser-mock-review"


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
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        raise SystemExit("EDISON_API_KEY is not set.")

    client = EdisonClient(api_key=api_key)

    print(f"Uploading {INPUTS} as a zipped collection...", flush=True)
    stored = client.store_file_content(
        name="powder_doser_mock_review_inputs",
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

    (HERE / "mock_review.task.json").write_text(
        json.dumps(data, default=str, indent=2)
    )
    answer = _extract_answer(data)
    (HERE / "mock_review.answer.md").write_text(answer)
    nb = _extract_notebook(data)
    if nb is not None:
        (HERE / "mock_review.notebook.ipynb").write_text(
            json.dumps(nb, default=str, indent=2)
        )
    task_id = str(data.get("task_id") or data.get("id") or "")
    (HERE / "mock_review_task_ids.json").write_text(
        json.dumps({"mock_review": task_id}, indent=2)
    )
    print(
        f"status={data.get('status')} id={task_id} answer_chars={len(answer)}",
        flush=True,
    )


if __name__ == "__main__":
    main()

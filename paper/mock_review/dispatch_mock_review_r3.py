#!/usr/bin/env python3
"""Round-3 Edison ANALYSIS mock review of the base powder-doser manuscript.

This round reviews the draft after Sam Charles's part-1 video review and the
1 Oct 2026 Sam/Sterling meeting: real data from both test rounds, tilt
limited to 0-45 degrees, the tested Fusion 360 auger in Fig. 1, and the
plain-language pass.  The round-2 review (written against an earlier draft
with synthetic data) is included so the panel can say which of its concerns
are now resolved.

Inputs are uploaded as one zipped collection (inputs_r3/):
  main.pdf, si.pdf                       -- the current draft and SI
  16-journal-editors.md                  -- editor scouting (PR #91)
  17-suggested-reviewers.md              -- reviewer personas (PR #91)
  previous_review_round2.md              -- the round-2 mock review

Usage:
  python dispatch_mock_review_r3.py            # upload + dispatch, record task id
  python dispatch_mock_review_r3.py --wait     # then poll and archive the result

The task id goes to mock_review_r3_task_ids.json; results are written as
mock_review_r3.{answer.md,notebook.ipynb,task.json}.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames

from run_mock_review import _extract_answer, _extract_notebook

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs_r3"
IDS = HERE / "mock_review_r3_task_ids.json"
TAG = "powder-doser-mock-review-r3"

QUERY = (
    "The attached collection contains a manuscript draft (main.pdf) and its "
    "supplementary information (si.pdf) prepared for submission to Digital "
    "Discovery (RSC) as a hardware-focused Full Paper, two scouting notes "
    "(16-journal-editors.md, 17-suggested-reviewers.md) listing the journal's "
    "editors and a pool of plausible reviewers, and previous_review_round2.md, "
    "a mock review of an EARLIER draft that still used synthetic placeholder "
    "data. The current draft reports real measurements from two test rounds "
    "on 13 powders (open-loop test protocols and closed-loop doses at 50 mg, "
    "200 mg and 1 g), and it is a case study of designing laboratory hardware "
    "with generative-AI CAD tools under human direction. "
    "Act as a full mock peer-review panel for the CURRENT draft. "
    "(1) As the handling editor (persona: Alan Aspuru-Guzik, Editor-in-Chief, "
    "AI-for-chemistry/self-driving-labs), write a short editor's assessment: "
    "scope fit for the hardware Full Paper track, novelty and significance, "
    "and an initial decision recommendation. "
    "(2) Write three detailed, independent reviewer reports in the personas of "
    "three DIFFERENT reviewers from 17-suggested-reviewers.md spanning (a) "
    "self-driving labs / lab automation (e.g. Milad Abolhasani), (b) powder "
    "dosing / feeder metrology (e.g. Johannes Khinast), and (c) LLM / "
    "generative CAD (e.g. Adriana Schulz). Each report needs: a summary of "
    "the contribution; numbered major comments and numbered minor comments "
    "that are specific and actionable and cite section, figure and table "
    "numbers or quote passages from the PDF; and a recommendation (accept / "
    "minor revision / major revision / reject). Do not exclude any persona "
    "for conflicts; this is a mock exercise. "
    "(3) Using previous_review_round2.md, list which of the round-2 action "
    "items are now resolved, partly resolved, or still open in the current "
    "draft, with one line of evidence each. "
    "(4) Check internal consistency and readability: numbers that disagree "
    "between the abstract, text, tables, figures, captions and SI; claims "
    "about which parts were designed by AI versus by people that are unclear "
    "or contradictory; the tilt range (the paper states 0-45 degrees as the "
    "maximum); and sentences that are hard to follow for a non-specialist "
    "reader (quote them and suggest a plainer version). "
    "(5) Finish with a consolidated, de-duplicated, priority-ranked action "
    "list for the authors: the 10-15 most important concrete revisions, each "
    "tagged with which reviewer(s) raised it and whether it needs new "
    "experiments, new analysis of existing data, or only writing changes. "
    "Assess the manuscript exactly as written."
)


def _client() -> EdisonClient:
    key = os.environ.get("EDISON_PLATFORM_API_KEY") or os.environ.get("EDISON_API_KEY")
    if not key:
        raise SystemExit("EDISON_PLATFORM_API_KEY is not set.")
    return EdisonClient(api_key=key)


def dispatch(client: EdisonClient) -> str:
    print(f"Uploading {INPUTS.name}/ as a zipped collection...", flush=True)
    stored = client.store_file_content(
        name="powder_doser_mock_review_r3_inputs",
        file_path=str(INPUTS),
        as_collection=True,
    )
    file_uri = f"data_entry:{stored.data_storage.id}"
    print(f"  uploaded -> {file_uri}", flush=True)
    task = {"name": JobNames.ANALYSIS, "query": QUERY, "tags": [TAG]}
    task_id = str(client.create_task(task, files=[file_uri]))
    IDS.write_text(json.dumps({"mock_review_r3": task_id, "inputs": file_uri}, indent=2))
    print(f"dispatched task id={task_id}", flush=True)
    return task_id


def wait_and_fetch(client: EdisonClient, task_id: str, poll_s: int = 120,
                   max_s: int = 3300) -> str:
    start = time.time()
    while True:
        task = client.get_task(task_id=task_id, verbose=True)
        status = str(getattr(task, "status", ""))
        print(f"[{int(time.time() - start)}s] status: {status}", flush=True)
        if status in {"success", "fail", "failed", "cancelled", "error"}:
            break
        if time.time() - start > max_s:
            print("timed out waiting; fetch later with --wait", flush=True)
            return status
        time.sleep(poll_s)
    data = task.model_dump() if hasattr(task, "model_dump") else dict(task)
    (HERE / "mock_review_r3.task.json").write_text(json.dumps(data, default=str, indent=2))
    answer = _extract_answer(data)
    (HERE / "mock_review_r3.answer.md").write_text(answer)
    nb = _extract_notebook(data)
    if nb is not None:
        (HERE / "mock_review_r3.notebook.ipynb").write_text(json.dumps(nb, default=str, indent=2))
    print(f"status={status} answer_chars={len(answer)}", flush=True)
    return status


def main() -> None:
    client = _client()
    if IDS.exists():
        task_id = json.loads(IDS.read_text())["mock_review_r3"]
        print(f"using recorded task id={task_id}", flush=True)
    else:
        task_id = dispatch(client)
    if "--wait" in sys.argv:
        wait_and_fetch(client, task_id)


if __name__ == "__main__":
    main()

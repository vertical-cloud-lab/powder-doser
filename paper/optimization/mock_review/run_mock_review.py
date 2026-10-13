#!/usr/bin/env python3
"""Edison ANALYSIS mock review of the optimization manuscript (issue #179).

Follows the pattern of the base manuscript's mock reviews (issue #96,
copilot/draft-base-manuscript:paper/mock_review/): the inputs are uploaded as
one zipped collection and a single ANALYSIS task plays the handling editor and
four reviewers drawn from the repository's scouting notes.

Inputs (inputs/, rebuilt by `prepare`):
  main.pdf                          -- the draft
  OUTLINE.md                        -- the authors' list of remaining work
  16-journal-editors.md             -- editor scouting        (PR #91)
  17-suggested-reviewers.md         -- reviewer personas      (PR #91)
  08-powder-properties-experts.md   -- powder-flow experts    (PR #41 branch)

Usage (from paper/optimization/):
  python mock_review/run_mock_review.py prepare    # copy inputs
  python mock_review/run_mock_review.py dispatch   # upload + create task, record id
  python mock_review/run_mock_review.py wait       # poll in the foreground, archive result

The task id is recorded in mock_review_task_ids.json; results are written as
mock_review.{task.json,answer.md,notebook.ipynb}.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
INPUTS = HERE / "inputs"
IDS = HERE / "mock_review_task_ids.json"
TAG = "powder-doser-optimization-mock-review"

GIT_SOURCES = {
    "16-journal-editors.md": "origin/copilot/determine-journals-editors-reviewers:paper/background/16-journal-editors.md",
    "17-suggested-reviewers.md": "origin/copilot/determine-journals-editors-reviewers:paper/background/17-suggested-reviewers.md",
    "08-powder-properties-experts.md": "origin/copilot/determine-helpful-individuals-organizations:paper/background/08-powder-properties-experts.md",
}

QUERY = (
    "The attached collection contains a manuscript draft (main.pdf) intended for Additive Manufacturing "
    "(Elsevier) as a full-length research article, the authors' list of remaining work (OUTLINE.md), and three "
    "scouting notes from the authors' repository (16-journal-editors.md, 17-suggested-reviewers.md, "
    "08-powder-properties-experts.md) that describe editors and potential reviewers. The paper treats the "
    "calibration of an open-source, 3D-printed auger powder doser as multi-objective Bayesian optimization "
    "(demonstrated on sodium chloride with validation repeats), reports the doser's response to 13 powders, "
    "proposes multi-task Bayesian optimization across powders, and builds a discrete element model of the "
    "auger to infer effective cohesion and friction from dosing data, to be compared with shear-cell, Hall-flow "
    "and spreadability measurements. The draft is a work in progress: text in orange square brackets and figure "
    "panels marked SYNTHETIC DATA are deliberate placeholders for results not yet collected. Do not spend "
    "comments on the mere presence of placeholders; instead judge whether the PLANNED experiments and analyses "
    "behind them (Methods 2.5-2.8 and OUTLINE.md) would be sufficient and convincing, and what is missing. "
    "Act as a full mock peer-review panel. "
    "(1) As the handling editor (persona: the Additive Manufacturing editor named in 16-journal-editors.md, or "
    "Adam Clare if none fits), write a short assessment: scope fit for Additive Manufacturing (which requires "
    "substantial advancement of additive manufacturing research and applies Elsevier's machine-learning "
    "requirements for statistical models), novelty, significance, and the initial decision you would make if the "
    "placeholders were filled with the planned results. "
    "(2) Write four independent reviewer reports in the personas of four DIFFERENT people from the scouting notes, "
    "covering (a) AM powder feedstock, flowability and spreadability (e.g. Laura Cordova or Zackary Snow), "
    "(b) DEM calibration and Bayesian inverse inference of contact parameters (e.g. Hongyang Cheng, Carl Wassgren "
    "or Bilal El Kassem), (c) Bayesian optimization and autonomous experimentation for AM (e.g. Benji Maruyama "
    "or Keith A. Brown), and (d) powder feeding and dosing metrology (e.g. Johannes Khinast or Fernando Muzzio). "
    "Ground each persona in that person's published work. Each report needs a summary of the contribution; "
    "numbered major and minor comments that are specific and actionable and cite section, figure and table "
    "numbers or quote the PDF; and a recommendation. Do not exclude any persona for conflicts; this is a mock "
    "exercise. "
    "(3) Check internal consistency of the real results: numbers that disagree between abstract, text, tables, "
    "figures and captions; claims that go beyond the data shown; statistics that need intervals or tests. "
    "(4) Finish with a consolidated, de-duplicated, priority-ranked action list of the 12-20 most important "
    "revisions, each tagged with the reviewer(s) who raised it and whether it needs new experiments, new "
    "analysis of existing data, or writing changes only. Assess the manuscript exactly as written."
)


def _client():
    from edison_client import EdisonClient

    key = os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit("EDISON_PLATFORM_API_KEY is not set.")
    return EdisonClient(api_key=key)


def prepare() -> None:
    if INPUTS.exists():
        shutil.rmtree(INPUTS)
    INPUTS.mkdir(parents=True)
    shutil.copy(PAPER / "main.pdf", INPUTS / "main.pdf")
    shutil.copy(PAPER / "OUTLINE.md", INPUTS / "OUTLINE.md")
    for name, ref in GIT_SOURCES.items():
        out = subprocess.run(["git", "show", ref], capture_output=True, check=True, cwd=PAPER).stdout
        (INPUTS / name).write_bytes(out)
    print("inputs:", sorted(p.name for p in INPUTS.iterdir()))


def dispatch() -> str:
    from edison_client import JobNames

    client = _client()
    stored = client.store_file_content(name="powder_doser_optimization_mock_review_inputs",
                                       file_path=str(INPUTS), as_collection=True)
    file_uri = f"data_entry:{stored.data_storage.id}"
    task = {"name": JobNames.ANALYSIS, "query": QUERY, "tags": [TAG]}
    task_id = str(client.create_task(task, files=[file_uri]))
    IDS.write_text(json.dumps({"mock_review": task_id, "inputs": file_uri,
                               "dispatched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=2))
    print("dispatched task id:", task_id)
    return task_id


def _answer(data: dict) -> str:
    try:
        return data["environment_frame"]["state"]["state"]["answer"] or ""
    except (KeyError, TypeError):
        return data.get("answer") or data.get("formatted_answer") or ""


def _notebook(data: dict):
    try:
        nb = data["environment_frame"]["state"]["state"]["nb_state"]
        if nb:
            return nb
    except (KeyError, TypeError):
        pass
    return data.get("notebook")


def wait(poll_s: int = 180, max_s: int = 3000) -> str:
    client = _client()
    task_id = json.loads(IDS.read_text())["mock_review"]
    start = time.time()
    while True:
        task = client.get_task(task_id=task_id, verbose=True)
        status = str(task.status)
        print(f"[{int(time.time() - start)} s] status: {status}", flush=True)
        if status in {"success", "fail", "failed", "cancelled", "error"}:
            break
        if time.time() - start > max_s:
            print("still running; re-run `wait` later to fetch", flush=True)
            return status
        time.sleep(poll_s)
    data = task.model_dump() if hasattr(task, "model_dump") else dict(task)
    (HERE / "mock_review.task.json").write_text(json.dumps(data, default=str, indent=2))
    ans = _answer(data)
    (HERE / "mock_review.answer.md").write_text(ans)
    nb = _notebook(data)
    if nb is not None:
        (HERE / "mock_review.notebook.ipynb").write_text(json.dumps(nb, default=str, indent=2))
    print(f"status={status} answer_chars={len(ans)}", flush=True)
    return status


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    {"prepare": prepare, "dispatch": dispatch, "wait": wait}[cmd]()

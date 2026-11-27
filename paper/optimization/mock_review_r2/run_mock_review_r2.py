#!/usr/bin/env python3
"""Second Edison mock review of the optimization manuscript (issue #179), on the 27 Nov 2026 rewrite.

Round 1 (mock_review/, task 2a2e76ab, 13 Oct) reviewed the first draft. This round reviews the rewrite
built on the 125 dose records, and adds two checks the first round could not make: a duplication check
against the companion hardware paper (its LaTeX source, PR #97) and a check of the statistics against the
per-dose SI tables.

Inputs (inputs/, rebuilt by `prepare`):
  main.pdf, si.pdf                  -- the draft and its SI
  OUTLINE.md, SUBMISSION.md         -- remaining work (with run counts) and the journal checklist
  hardware_paper_main.tex           -- the companion hardware paper as of the review (PR #97 branch)
  16-journal-editors.md, 17-suggested-reviewers.md, 08-powder-properties-experts.md -- persona notes

Usage (from paper/optimization/), with the Edison client in a Python 3.12 environment:
  python mock_review_r2/run_mock_review_r2.py prepare
  python mock_review_r2/run_mock_review_r2.py dispatch
  python mock_review_r2/run_mock_review_r2.py wait        # blocking foreground loop
  python mock_review_r2/run_mock_review_r2.py artifacts
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
TAG = "powder-doser-optimization-mock-review-r2"
GIT_SOURCES = {
    "16-journal-editors.md": "origin/copilot/determine-journals-editors-reviewers:paper/background/16-journal-editors.md",
    "17-suggested-reviewers.md": "origin/copilot/determine-journals-editors-reviewers:paper/background/17-suggested-reviewers.md",
    "08-powder-properties-experts.md": "origin/copilot/determine-helpful-individuals-organizations:paper/background/08-powder-properties-experts.md",
    "hardware_paper_main.tex": "origin/copilot/draft-base-manuscript:paper/main.tex",
}
QUERY = (
    "The attached collection contains a manuscript draft (main.pdf) and its supplementary information (si.pdf) "
    "intended for Additive Manufacturing (Elsevier) as a full-length research article; the authors' plan of "
    "remaining work with run counts (OUTLINE.md); their checklist against the journal's guide for authors "
    "(SUBMISSION.md); the LaTeX source of a COMPANION hardware paper by the same group (hardware_paper_main.tex), "
    "which reports the doser's construction and its fixed-setting response to 13 powders; and three scouting "
    "notes on editors and reviewers (16-journal-editors.md, 17-suggested-reviewers.md, "
    "08-powder-properties-experts.md). The manuscript treats per-powder calibration of an open-source auger "
    "powder doser as multi-objective Bayesian optimization: two campaigns on sodium chloride, validation blocks, "
    "transfer of the settings to AlSi10Mg and to a laboratory-atomized Al 4047, and rank correlations of dosing "
    "response with literature powder properties. Text in orange square brackets and figure panels marked "
    "SYNTHETIC DATA are deliberate placeholders for planned results (multi-task calibration, DEM inference, "
    "measured properties); do not comment on their mere presence, but judge whether the planned work in "
    "OUTLINE.md section 4 (experiments E0-E9, analyses, schedule) would make the paper acceptable, and what the "
    "smallest sufficient set of experiments is. "
    "Act as a mock peer-review panel and an auditor. "
    "(1) Handling editor (persona: the Additive Manufacturing editor in 16-journal-editors.md, or A. T. Clare): "
    "scope fit, novelty, significance; whether the paper as it stands is better suited to the journal's new "
    "Methods-paper type or to another journal; the decision you would make now and after the planned work. "
    "(2) Three independent reviewer reports in the personas of three DIFFERENT people from the scouting notes: "
    "(a) AM powder feedstock and flowability, (b) Bayesian optimization and autonomous experimentation, "
    "(c) powder feeding and dosing metrology. Numbered major and minor comments citing section, figure and table "
    "numbers, and a recommendation. "
    "(3) Statistics audit: recompute what you can from the per-dose SI tables (e.g. medians, ranges, the "
    "Mann-Whitney comparisons of time between the hand-tuned doses, the bo-005 validation block and the corner-09 "
    "block, the paired comparison of the 16 corners between campaigns) and report any number in the main text "
    "that disagrees with the SI tables, any test that is inappropriate, and any claim that goes beyond the data. "
    "(4) Duplication audit: list every figure, table, number or claim in main.pdf that repeats a figure, table, "
    "number or claim of hardware_paper_main.tex, say whether it is cited as such, and whether Elsevier's "
    "duplicate-publication policy would object; also list anything the two papers state differently about the "
    "same data. "
    "(5) Finish with a consolidated, priority-ranked action list of the 10-20 most important revisions, each "
    "tagged as new experiments, new analysis of existing data, or writing only. Assess the manuscript exactly as "
    "written."
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
    for name in ("main.pdf", "si.pdf", "OUTLINE.md", "SUBMISSION.md"):
        shutil.copy(PAPER / name, INPUTS / name)
    for name, ref in GIT_SOURCES.items():
        out = subprocess.run(["git", "show", ref], capture_output=True, check=True, cwd=PAPER).stdout
        (INPUTS / name).write_bytes(out)
    print("inputs:", sorted(p.name for p in INPUTS.iterdir()))


def dispatch() -> str:
    from edison_client import JobNames

    client = _client()
    stored = client.store_file_content(name="powder_doser_optimization_mock_review_r2_inputs",
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


def artifacts() -> None:
    """Download every output file of the trajectory into outputs/ (data only; nothing is executed)."""
    client = _client()
    data = json.loads((HERE / "mock_review.task.json").read_text())
    out_dir = HERE / "outputs"
    out_dir.mkdir(exist_ok=True)
    for item in data["environment_frame"]["state"]["info"]["output_data"]:
        name = Path(item["filename"]).name
        got = client.fetch_data_from_storage(item["entry_id"])
        if isinstance(got, list):
            got = got[0] if got else None
        if isinstance(got, Path) and got.is_dir():
            shutil.copytree(got, out_dir / name, dirs_exist_ok=True)
        elif isinstance(got, Path):
            shutil.copy(got, out_dir / name)
        elif got is not None and hasattr(got, "content"):
            content = got.content
            (out_dir / name).write_bytes(content if isinstance(content, bytes) else str(content).encode())
        else:
            print("could not fetch", name)
            continue
        dest = out_dir / name
        size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file()) if dest.is_dir() else dest.stat().st_size
        print("fetched", name, size)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    {"prepare": prepare, "dispatch": dispatch, "wait": wait, "artifacts": artifacts}[cmd]()

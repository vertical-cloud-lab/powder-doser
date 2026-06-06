#!/usr/bin/env python3
"""Batch 3 of the publication-venue scouting for the powder-doser project
(issue: "Determine potential journals, editors, reviewers, and conferences").

This is the *consolidated final recommendation* step. Unlike Batches 1-2, which
dispatch ``LITERATURE_HIGH`` (PaperQA) queries, this batch runs a single Edison
Scientific ``ANALYSIS`` (data-analysis "crow") task that ingests the committed
artifacts from the prior two batches and synthesizes one actionable submission
plan: primary journal + companions, the handling editor(s) to request, a
non-conflicted suggested-reviewer slate, and the conference roadmap.

Per the ANALYSIS convention, the whole ``edison_artifacts/`` directory is
uploaded as a single zipped collection via
``client.store_file_content(file_path=DIR, as_collection=True)`` (uploading the
files individually makes the crow fail silently). The resulting answer, notebook,
and any written output files are saved alongside the other artifacts.

Outputs go to ``paper/background/edison_artifacts/`` as
``consolidated_recommendation.{task.json,answer.md,notebook.ipynb}`` plus any
files the crow writes, and the job UUID is recorded in
``consolidated_recommendation_task_ids.json`` for continuation. Run with::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_consolidated_recommendation.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

ARTIFACTS_DIRNAME = "edison_artifacts"

QUERY = (
    "You are given the raw outputs of a multi-batch literature-scouting effort "
    "for a specific paper. The paper describes a low-cost, open-source, "
    "self-driving-laboratory (SDL) multi-powder doser for autonomous additive-"
    "manufacturing (AM) alloy discovery, with a closed-loop gravimetric "
    "calibration algorithm and extensive calibration data, an auger auto-change "
    "mechanism, dispensing of up to 50 unique powders, and a CAD design produced "
    "via an LLM/code-based generative-CAD pipeline. The attached files are the "
    "committed artifacts: venue shortlists (venues_sdl_hardware.*, "
    "venues_generative_cad.*), journal editors (journal_editors.*), suggested "
    "reviewers (likely_reviewers.*), and target conferences "
    "(target_conferences.*); each <key>.answer.md is the prose answer, "
    "<key>.references.md the bibliography, and <key>.artifact-00.md a structured "
    "table. Synthesize ONE consolidated, actionable submission plan that "
    "reconciles all batches. Specifically produce: (1) a single recommended "
    "primary journal with a one-paragraph justification and the named handling "
    "editor(s) to request, plus the companion venues (reproducibility hardware "
    "paper and software DOI) and the higher-impact alternative framing; (2) a "
    "ranked, de-duplicated suggested-reviewer slate of ~8-12 names drawn from "
    "the reviewer pool, balanced across the sub-topics (SDL/automation, open "
    "hardware, powder dosing/metrology, AM alloy discovery, generative CAD), "
    "explicitly flagging any author-overlap conflicts of interest (e.g. Digital "
    "Discovery advisory-board members who also appear as candidate reviewers) so "
    "they are NOT suggested as reviewers; (3) a conference roadmap grouped into "
    "best-fit / strong / stretch with the single best near-term venue called "
    "out; and (4) a short submission-sequence recommendation (what to submit "
    "where, and in what order). Where the inputs mark a person or fact as "
    "'unverified' or 'verify at journal page', preserve that caveat. Do not "
    "fabricate any email address or contact detail not present in the inputs. "
    "Cite the specific input file(s) backing each recommendation."
)

TAG = "powder-doser-venues"


def _extract_answer(data: dict) -> str:
    """ANALYSIS answer lives at environment_frame.state.state.answer (a str)."""
    try:
        return data["environment_frame"]["state"]["state"]["answer"] or ""
    except (KeyError, TypeError):
        pass
    return data.get("answer") or data.get("formatted_answer") or ""


def _extract_notebook(data: dict) -> dict | None:
    """ANALYSIS notebook (ipynb JSON) lives at environment_frame...nb_state."""
    try:
        nb = data["environment_frame"]["state"]["state"]["nb_state"]
        if nb:
            return nb
    except (KeyError, TypeError):
        pass
    return data.get("notebook")


def _extract_output_data(data: dict) -> list:
    """Files written by the crow are listed at environment_frame.state.info."""
    try:
        out = data["environment_frame"]["state"]["info"]["output_data"]
        if out:
            return out
    except (KeyError, TypeError):
        pass
    return []


def main() -> None:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        raise SystemExit(
            "EDISON_API_KEY is not set. Export it before running this script."
        )

    out_dir = Path(__file__).parent / ARTIFACTS_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)

    client = EdisonClient(api_key=api_key)

    # ANALYSIS crow needs the directory as a single zipped collection; uploading
    # files individually makes the task fail silently.
    print(f"Uploading {out_dir} as a zipped collection...", flush=True)
    stored = client.store_file_content(
        name="powder_doser_venue_artifacts",
        file_path=str(out_dir),
        as_collection=True,
    )
    entry_id = stored.data_storage.id
    file_uri = f"data_entry:{entry_id}"
    print(f"  uploaded -> {file_uri}", flush=True)

    task = {
        "name": JobNames.ANALYSIS,
        "query": QUERY,
        "tags": [TAG, "consolidated_recommendation"],
    }
    print("Dispatching ANALYSIS task...", flush=True)
    # ANALYSIS (data-analysis crow) runs are notably slower than the
    # LITERATURE_HIGH batches because the crow executes a notebook over the
    # uploaded collection; allow up to 90 min before giving up.
    results = client.run_tasks_until_done(
        [task], verbose=True, progress_bar=False, timeout=5400, files=[file_uri]
    )
    result = results[0]
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)

    key = "consolidated_recommendation"
    (out_dir / f"{key}.task.json").write_text(
        json.dumps(data, default=str, indent=2)
    )
    answer = _extract_answer(data)
    (out_dir / f"{key}.answer.md").write_text(answer)
    notebook = _extract_notebook(data)
    if notebook is not None:
        (out_dir / f"{key}.notebook.ipynb").write_text(
            json.dumps(notebook, default=str, indent=2)
        )
    output_data = _extract_output_data(data)

    task_id = str(data.get("task_id") or data.get("id") or "")
    (out_dir / f"{key}_task_ids.json").write_text(
        json.dumps({key: task_id}, indent=2)
    )
    print(
        f"  {key}: status={data.get('status')} id={task_id} "
        f"answer_chars={len(answer)} notebook={'yes' if notebook else 'no'} "
        f"output_files={[d.get('filename') if isinstance(d, dict) else d for d in output_data]}",
        flush=True,
    )
    print(f"Wrote artifacts to {out_dir}", flush=True)


if __name__ == "__main__":
    main()

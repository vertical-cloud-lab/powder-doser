#!/usr/bin/env python3
"""Submit DESIGN-LOG.md to Edison Scientific (ANALYSIS / crow) for feedback.

Asks Edison's data-analysis crow to review the chronological Record of Designs
(DESIGN-LOG.md) and report how to make the resource more valuable. The submitted
answer is written to edison_artifacts/design-log-analysis.answer.md and the task
metadata to edison_artifacts/design-log-analysis.task.json.

Requires EDISON_API_KEY in the environment and `pip install edison-client`.
ANALYSIS (crow) needs a *zipped collection* upload (store_file_content with
as_collection=True); uploading a bare single file makes the task fail silently.
"""
import json
import os
import pathlib
import shutil
import tempfile

from edison_client import EdisonClient, JobNames, TaskRequest

REPO = pathlib.Path(__file__).resolve().parents[2]
LOG = REPO / "DESIGN-LOG.md"
ARTIFACTS = pathlib.Path(__file__).resolve().parent / "edison_artifacts"
KEY = "design-log-analysis"

QUERY = (
    "The attached DESIGN-LOG.md is a single, chronological 'Record of Designs' for an "
    "open-hardware automated powder-dosing instrument (the powder-doser repository). It "
    "documents every design and every iteration of every design in commit-date order, each "
    "entry carrying a Trigger (the issue/PR/review that prompted it), a 1-2 sentence Design "
    "note on what changed and why, and embedded visual artifacts (CAD render PNGs/SVGs, "
    "animated GIFs, printed-part photos, and bench-test video links).\n\n"
    "Please act as an expert reviewer of engineering design documentation and knowledge "
    "management. Analyze the document and report back:\n"
    "1. Structural and content analysis: quantify the log (entries, iteration chains, "
    "artifact types, coverage gaps, date span, balance across subsystems).\n"
    "2. Strengths: what makes this a good design record.\n"
    "3. Weaknesses and risks: e.g. link rot from commit-pinned raw URLs, missing rationale/"
    "decision context, lack of cross-references, no searchable metadata, no failure capture.\n"
    "4. Concrete, prioritized recommendations for how to make this resource MORE VALUABLE "
    "to (a) new contributors onboarding, (b) researchers citing the work, and (c) future "
    "maintainers. Consider: decision/rationale capture (ADR-style), traceability to "
    "requirements, machine-readable front-matter, a summary/index table, tagging by "
    "subsystem, capturing dead-ends/failures, dimensions/specs per iteration, and archival "
    "of artifacts to avoid link rot.\n"
    "Be specific and actionable; cite concrete observations from the document."
)


def _extract_answer(dump: dict):
    try:
        return dump["environment_frame"]["state"]["state"]["answer"]
    except Exception:
        return dump.get("answer")


def main():
    client = EdisonClient(api_key=os.environ["EDISON_API_KEY"])
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        bundle = pathlib.Path(td) / "design_log_bundle"
        bundle.mkdir()
        shutil.copy(LOG, bundle / "DESIGN-LOG.md")
        resp = client.store_file_content(
            name="powder-doser-design-log",
            file_path=str(bundle),
            as_collection=True,
        )
    uri = f"data_entry:{resp.data_storage.id}"
    print("Uploaded:", uri)

    task = TaskRequest(name=JobNames.ANALYSIS, query=QUERY)
    results = client.run_tasks_until_done(task, files=[uri], verbose=True, timeout=2400)
    dump = results[0].model_dump()

    task_id = dump.get("task_id") or dump.get("id")
    answer = _extract_answer(dump) or "(no answer extracted)"

    (ARTIFACTS / f"{KEY}.answer.md").write_text(answer)
    (ARTIFACTS / f"{KEY}.task.json").write_text(
        json.dumps(
            {
                "job_name": JobNames.ANALYSIS.value,
                "job_type": "ANALYSIS",
                "task_id": str(task_id),
                "data_entry_uri": uri,
                "input_file": "DESIGN-LOG.md",
                "status": dump.get("status"),
                "query": QUERY,
            },
            indent=2,
        )
    )
    print(f"task_id={task_id} status={dump.get('status')}")
    print(answer)


if __name__ == "__main__":
    main()

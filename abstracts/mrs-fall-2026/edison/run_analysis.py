#!/usr/bin/env python3
"""Edison ANALYSIS: identify the MRS Fall 2026 symposia best aligned with the
powder-doser project, using the official call-for-abstracts PDF + a repo context
bundle (issues/PRs). Uploads the bundle as a single collection per the Edison
file-management docs, then polls to completion and writes the answer."""
import json
import os
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest
from edison_client.models.rest import ExecutionStatus

HERE = Path(__file__).parent
BUNDLE = HERE / "analysis_bundle"
OUT = HERE / "analysis_out"
OUT.mkdir(exist_ok=True)

QUERY = (
    "You are helping select where to submit a conference abstract to the 2026 MRS "
    "Fall Meeting (Boston). Two files are attached: (1) the official MRS Fall 2026 "
    "Call for Abstracts PDF, which contains ~68 symposia (each with a code like "
    "MT01, scope description, topics, and organizer names); and (2) repo_context.md, "
    "a dump of the GitHub issues and pull requests for our project (the main branch "
    "is sparse; most work lives in issues/PR branches).\n\n"
    "Our project: an open-source, low-cost powder doser (dispenser) for precise "
    "metering of dry metal/feedstock powders, developed as part of a self-driving / "
    "Bayesian-optimization materials-discovery workflow at the BYU Vertical Cloud Lab. "
    "A central theme is using agentic AI and generative CAD/text-to-CAD tools "
    "(GitHub Copilot agents, zoo.dev, CADSmith, etc.) for mechanical and "
    "electromechanical design, with engineers designing parts and AI modeling them. "
    "Downstream the dosed powders feed ultrasonic atomization and laser powder bed "
    "fusion (L-PBF) of additively manufactured aerospace structural alloys.\n\n"
    "TASK: Parse the call for abstracts and identify, by code and full title, the "
    "symposia whose scope best matches our work. Rank the TOP 5 most-aligned symposia "
    "and, for each, give: (a) the code and full title, (b) a 2-4 sentence justification "
    "grounded in both the symposium scope text and specific evidence from our "
    "repo_context.md, (c) the listed symposium organizers (names + affiliations), and "
    "(d) which angle of our project to emphasize if we submit there. Then give a short "
    "list of 3-5 secondary/honorable-mention symposia. Be concrete and cite symposium "
    "codes exactly as they appear in the PDF. Focus on what we have actually done "
    "according to the repo, not aspirational ideas."
)


def main() -> None:
    client = EdisonClient(api_key=os.environ["EDISON_API_KEY"])

    print("Uploading bundle as collection ...", flush=True)
    resp = client.store_file_content(
        name="powder-doser MRS f26 symposium-selection bundle",
        file_path=str(BUNDLE),
        description=(
            "MRS Fall 2026 call for abstracts PDF + powder-doser repo issues/PRs "
            "context, for symposium alignment analysis."
        ),
        as_collection=True,
    )
    entry_id = resp.data_storage.id
    uri = f"data_entry:{entry_id}"
    print("uploaded entry:", uri, flush=True)

    task = TaskRequest(name=JobNames.ANALYSIS, query=QUERY)
    tid = client.create_task(task, files=[uri])
    print("trajectory_id:", tid, flush=True)
    (OUT / "analysis.task.json").write_text(
        json.dumps({"trajectory_id": str(tid), "data_entry": uri, "query": QUERY}, indent=2)
    )

    deadline = time.time() + 2200
    while time.time() < deadline:
        time.sleep(30)
        r = client.get_task(tid)
        status = getattr(r, "status", None)
        print("status:", status, flush=True)
        try:
            terminal = ExecutionStatus(status).is_terminal_state()
        except Exception:
            terminal = status in {"success", "fail", "cancelled", "truncated"}
        if terminal:
            dump = r.model_dump(mode="json")
            (OUT / "analysis.full.json").write_text(json.dumps(dump, indent=2, default=str))
            answer = (
                getattr(r, "formatted_answer", None)
                or getattr(r, "answer", None)
                or dump.get("formatted_answer")
                or dump.get("answer")
                or ""
            )
            (OUT / "analysis.answer.md").write_text(answer or "(no answer field)")
            print("=== TERMINAL:", status, "===", flush=True)
            print(answer[:6000] if answer else "(no answer)", flush=True)
            return
    print("TIMEOUT waiting for analysis task", flush=True)


if __name__ == "__main__":
    main()

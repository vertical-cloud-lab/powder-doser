#!/usr/bin/env python3
"""Edison Scientific ``ANALYSIS`` task that reviews the three shortened
generative-CAD outreach email drafts in
``outreach/generative-cad-email-drafts.md`` (PR #43).

The drafts are embedded verbatim in the prompt (no file upload needed).
Artifacts land in ``outreach/edison_artifacts/`` using the same
``<key>.task.json`` / ``<key>.answer.md`` / ``<key>.references.md`` layout as
``paper/background/edison_run_outreach_contacts.py``. The task id is written
to ``<key>._task_id.json`` immediately after dispatch so a follow-up session
can fetch results if this one times out. Re-run with::

    pip install edison_client
    export EDISON_PLATFORM_API_KEY=...
    python outreach/edison_run_draft_review.py

Usage: ``python edison_run_draft_review.py`` dispatches and waits;
``python edison_run_draft_review.py fetch`` only fetches an already-dispatched
task using the saved task id.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames

KEY = "gencad_outreach_draft_review"
HERE = Path(__file__).parent
OUT_DIR = HERE / "edison_artifacts"
DRAFTS = HERE / "generative-cad-email-drafts.md"

PROMPT_HEADER = """\
Review the three short cold-outreach emails below, drafted by a small
university research lab (BYU Vertical Cloud Lab, ~3 people) that builds an
open-source auger-fed powder doser for metal additive manufacturing and
generates most of its CAD with LLM/agentic pipelines. The sender is Luke
Winters, a researcher in the lab; the PI (Dr. Sterling Baird) is cc'd.

Recipients:
1. Jesse Barkley — CMU PhD student, first author of the CADSmith agentic
   CAD-generation paper (cc: his advisor Prof. Amir Barati Farimani).
2. Adam Urbanczyk — lead maintainer of the open-source CadQuery code-CAD
   library (message will be sent via Discord DM or GitHub Discussion).
3. Jessie Frazelle — co-founder/CEO of Zoo (zoo.dev, Text-to-CAD API and
   Zoo Design Studio); the lab is a paying customer, and the PI already sent
   a short LinkedIn note in May proposing a chat.

The lab's explicit style goals, in priority order: (a) BRIEF — these were cut
down from much longer drafts and must stay short; (b) acknowledge the
recipient's work and its relevance; (c) just enough concrete detail about the
lab's own generative-CAD usage to be credible and give the recipient
something to go on; (d) one clear ask per email.

For EACH email give:
- Verdict: send as-is / minor edits / needs rework.
- What works (1-2 bullets).
- Specific problems, if any (wording, tone, credibility, unclear ask,
  anything that reads as filler), each with a concrete replacement wording.
- Any sentence that should be CUT outright to make it shorter without losing
  the acknowledgement or the credibility signal.
Also flag anything that could come across as presumptuous, transactional, or
spam-like to a cold recipient, and check the subject lines. Do NOT pad the
emails back out with more detail; shorter is preferred. Keep your review
concise and actionable.

=== DRAFTS UNDER REVIEW ===

"""


def extract_drafts() -> str:
    text = DRAFTS.read_text()
    # Drop the routing-notes preamble; the drafts start at the first "## 1."
    match = re.search(r"^## 1\..*", text, flags=re.MULTILINE | re.DOTALL)
    return match.group(0) if match else text


def write_artifacts(client: EdisonClient, task_id: str) -> None:
    task = client.get_task(task_id=task_id, verbose=True)
    data = task.model_dump() if hasattr(task, "model_dump") else dict(task)
    (OUT_DIR / f"{KEY}.task.json").write_text(
        json.dumps(data, default=str, indent=2)
    )
    try:
        answer = data["environment_frame"]["state"]["state"]["response"]["answer"]
        formatted = answer.get("formatted_answer") or answer.get("answer") or ""
        references = answer.get("references") or ""
    except (KeyError, TypeError):
        formatted, references = "", ""
    (OUT_DIR / f"{KEY}.answer.md").write_text(formatted)
    (OUT_DIR / f"{KEY}.references.md").write_text(references)
    print(
        f"{KEY}: status={data.get('status')} "
        f"answer_chars={len(formatted)} refs_chars={len(references)}",
        flush=True,
    )


def wait(client: EdisonClient, task_id: str) -> None:
    while True:
        status = str(client.get_task(task_id=task_id, lite=True).status)
        print("status:", status, flush=True)
        if status in {"success", "fail", "failed", "cancelled", "error"}:
            return
        time.sleep(120)


def main() -> None:
    api_key = os.environ.get("EDISON_PLATFORM_API_KEY")
    if not api_key:
        raise SystemExit("EDISON_PLATFORM_API_KEY is not set.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = EdisonClient(api_key=api_key)

    task_id_file = OUT_DIR / f"{KEY}._task_id.json"
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        task_id = json.load(task_id_file.open())["task_id"]
    else:
        task_id = client.create_task(
            {
                "name": JobNames.ANALYSIS,
                "query": PROMPT_HEADER + extract_drafts(),
                "tags": ["powder-doser-grant", KEY, "outreach-contacts"],
            }
        )
        task_id_file.write_text(json.dumps({"task_id": str(task_id)}, indent=2))
        print("task_id:", task_id, flush=True)
    wait(client, str(task_id))
    write_artifacts(client, str(task_id))


if __name__ == "__main__":
    main()

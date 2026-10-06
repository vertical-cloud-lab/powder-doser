#!/usr/bin/env python3
"""Edison LITERATURE (low effort): three SEPARATE mock-review queries, one per
TMS 2027 abstract, each using the assigned symposium's organizing committee as
mock-reviewer personas (per PR #78 request).

Abstract -> assigned symposium (flyer id in tms2027_symposia.yaml):
- powder-dosing (Sam, oral)        -> 021 AI-Enabled Materials Processing
- calibration-optimization (Will)  -> 075 Powder Materials Processing and
                                       Fundamental Understanding
- generative-ai-cad (Luke)         -> 105 Accelerating Innovation in Materials
                                       and Manufacturing

Symposium titles, scopes, and organizer names/affiliations/backgrounds are read
from ../tms2027_symposia.yaml so the personas stay in sync with the catalog.
Submits all three tasks up front, then polls to completion and writes
persona_reviews_out/<key>.answer.md (+ .task.json with the full query).
"""
import json
import os
import time
from pathlib import Path

import yaml
from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest
from edison_client.models.rest import ExecutionStatus

HERE = Path(__file__).parent
TMS = HERE.parent
OUT = HERE / "persona_reviews_out"
OUT.mkdir(exist_ok=True)

INITIAL_WAIT_SECONDS = 600  # per repo CLAUDE.md: wait ~10 min before polling
POLL_SECONDS = 60
TASK_TIMEOUT_SECONDS = 2400

ABSTRACTS = [
    {
        "key": "powder-dosing",
        "presenter": "Sam (oral presentation)",
        "symposium_id": "021",
    },
    {
        "key": "calibration-optimization",
        "presenter": "Will",
        "symposium_id": "075",
    },
    {
        "key": "generative-ai-cad",
        "presenter": "Luke",
        "symposium_id": "105",
    },
]


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


def _load_symposia() -> dict:
    data = yaml.safe_load((TMS / "tms2027_symposia.yaml").read_text())
    syms = data["symposia"] if isinstance(data, dict) and "symposia" in data else data
    return {str(s.get("id")): s for s in syms}


def _abstract_text(key: str) -> str:
    text = (TMS / key / "abstract.md").read_text()
    # Strip the local metadata header; reviewers only need title + body.
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


def _build_query(entry: dict, sym: dict) -> str:
    organizers = "\n".join(
        f"- {o.get('name')} ({o.get('affiliation')}) - {o.get('background') or 'background not on file'}"
        for o in sym.get("organizers", [])
    )
    return f"""We are preparing an abstract for the 2027 TMS Annual Meeting & \
Exhibition (Orlando, FL; March 14-18, 2027; body limited to 150 words, submitted \
via ProgramMaster). This abstract is assigned to the symposium \
"{sym.get('title')}" ({sym.get('track')} track). Presenter: {entry['presenter']}.

Please act as a panel of MOCK PEER REVIEWERS drawn from that symposium's actual \
ORGANIZING COMMITTEE, listed below. Adopt each person's persona, grounded in their \
research areas (and, where you can quickly find it, their recent literature):
{organizers}

Review the abstract through each organizer's lens: does it fit the symposium scope \
(below), what would that reviewer want to see, and where does the abstract over- or \
under-reach for this audience? Then provide SPECIFIC, ACTIONABLE TEXTUAL \
SUGGESTIONS: concrete ADDITIONS (sentences or phrases to insert, and where), \
REMOVALS (text to cut and why), and MODIFICATIONS (rewordings). The body is limited \
to 150 words, so any proposed addition must say what to cut to stay within the \
limit. Finish with a short prioritized punch-list and note any claims needing \
stronger evidence. Keep feedback faithful to what the abstract actually claims; do \
not invent results.

=== SYMPOSIUM SCOPE (from the TMS 2027 call-for-abstracts flyer) ===
{sym.get('scope')}

=== ABSTRACT UNDER REVIEW (150-word body) ===
{_abstract_text(entry['key'])}
"""


def main() -> None:
    client = EdisonClient(api_key=_api_key())
    symposia = _load_symposia()

    pending: dict[str, str] = {}
    for entry in ABSTRACTS:
        sym = symposia[entry["symposium_id"]]
        query = _build_query(entry, sym)
        task = TaskRequest(name=JobNames.LITERATURE, query=query)
        tid = str(client.create_task(task))
        pending[entry["key"]] = tid
        print(f"submitted {entry['key']}: trajectory_id={tid}", flush=True)
        (OUT / f"{entry['key']}.task.json").write_text(
            json.dumps(
                {
                    "trajectory_id": tid,
                    "job": str(JobNames.LITERATURE),
                    "symposium_id": entry["symposium_id"],
                    "symposium": sym.get("title"),
                    "query": query,
                },
                indent=2,
            )
        )

    print(f"waiting {INITIAL_WAIT_SECONDS}s before first poll", flush=True)
    time.sleep(INITIAL_WAIT_SECONDS)

    deadline = time.time() + TASK_TIMEOUT_SECONDS
    while pending and time.time() < deadline:
        for key, tid in list(pending.items()):
            r = client.get_task(tid)
            status = getattr(r, "status", None)
            print(f"{key}: {status}", flush=True)
            try:
                terminal = ExecutionStatus(status).is_terminal_state()
            except Exception:
                terminal = status in {"success", "fail", "cancelled", "truncated"}
            if terminal:
                dump = r.model_dump(mode="json")
                answer = (
                    getattr(r, "formatted_answer", None)
                    or getattr(r, "answer", None)
                    or dump.get("formatted_answer")
                    or dump.get("answer")
                    or ""
                )
                (OUT / f"{key}.answer.md").write_text(answer or "(no answer field)")
                print(f"=== {key} TERMINAL: {status} ===", flush=True)
                del pending[key]
        if pending:
            time.sleep(POLL_SECONDS)
    if pending:
        print(f"TIMEOUT waiting for: {sorted(pending)}", flush=True)


if __name__ == "__main__":
    main()

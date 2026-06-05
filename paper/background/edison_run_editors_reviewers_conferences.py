#!/usr/bin/env python3
"""Batch 2 of the publication-venue scouting for the powder-doser project
(issue: "Determine potential journals, editors, reviewers, and conferences").

Three SEPARATE Edison Scientific ``LITERATURE_HIGH`` queries are dispatched in
parallel, as the issue requests ("use separate edison queries for journal
editors, potential or likely journal reviewers, and target conferences"). All
three are grounded in the target-venue shortlist that Batch 1
(``edison_run_venues.py``) produced — primarily Digital Discovery (RSC),
HardwareX, Additive Manufacturing, The International Journal of Advanced
Manufacturing Technology, ASME Journal of Mechanical Design / JCISE, Cell
Reports Physical Science, and npj Computational Materials.

* ``journal_editors`` — named editors / editorial-board members at the target
  journals who handle SDL / open-hardware / AM / generative-design submissions.
* ``likely_reviewers`` — researchers whose published work overlaps the paper
  (multi-powder dosing, SDLs, open hardware, AM alloy discovery, LLM/code-based
  generative CAD) and who would be credible suggested reviewers.
* ``target_conferences`` — conferences / workshops where this work fits (SDL /
  acceleration, materials & AM, design-automation, generative-CAD/ML).

Following the #43 outreach-contacts convention, each prompt forbids fabricating
e-mail addresses and requires a public, verifiable source URL for every named
person (editorial-board page, faculty page, ORCID, conference committee page).

Outputs go to ``paper/background/edison_artifacts/`` as
``<key>.{task.json,answer.md,references.md}``. Run with::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_editors_reviewers_conferences.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

# Target-venue shortlist carried over from Batch 1 (edison_run_venues.py).
VENUE_CONTEXT = (
    "The target-journal shortlist established by the prior literature batch for "
    "this project is, in priority order: Digital Discovery (RSC) [primary], "
    "HardwareX (Elsevier), Review of Scientific Instruments (AIP), Additive "
    "Manufacturing (Elsevier), Additive Manufacturing Letters, The "
    "International Journal of Advanced Manufacturing Technology (Springer), "
    "ASME Journal of Mechanical Design, ASME Journal of Computing and "
    "Information Science in Engineering (JCISE), Computer-Aided Design "
    "(Elsevier), Advanced Engineering Informatics, Cell Reports Physical "
    "Science, npj Computational Materials, Materials & Design, and "
    "IEEE/ASME Transactions on Mechatronics. The paper is an open-hardware, "
    "self-driving-laboratory (SDL) multi-powder doser for autonomous additive-"
    "manufacturing alloy discovery, with a closed-loop gravimetric calibration "
    "algorithm and extensive calibration data, an auger auto-change mechanism, "
    "dispensing of up to 50 unique powders, and a CAD design produced via an "
    "LLM/code-based generative-CAD pipeline."
)

NO_FABRICATION = (
    "Do NOT fabricate or guess e-mail addresses or any contact detail. For every "
    "named person, provide a publicly verifiable source URL (journal editorial-"
    "board page, university faculty page, ORCID, Google Scholar, or conference "
    "committee page) where their role/affiliation can be confirmed, and only "
    "list a contact channel (institutional email, lab page, ORCID, professional "
    "social handle) if it is publicly published on such a page. If no public "
    "personal email exists, say so and give the lab/group/editorial page "
    "instead. Mark anything uncertain as 'unverified'."
)

QUERIES: dict[str, str] = {
    "journal_editors": (
        "Identify the current editors and relevant editorial-board members of "
        "the journals most likely to handle a submission of the project "
        "described below, so the authors know who would steer the paper and who "
        "to suggest as a handling editor. " + VENUE_CONTEXT + " For each of the "
        "top venues — especially Digital Discovery (RSC), HardwareX (Elsevier), "
        "Additive Manufacturing (Elsevier), The International Journal of "
        "Advanced Manufacturing Technology, ASME Journal of Mechanical Design, "
        "ASME JCISE, Cell Reports Physical Science, and npj Computational "
        "Materials — list: the Editor(s)-in-Chief, and the specific associate / "
        "topic / handling editors whose remit covers self-driving labs, "
        "laboratory automation, open hardware, additive manufacturing, "
        "design automation, or AI/ML-for-design. For each named editor give: "
        "full name, exact editorial role, home institution, research focus, and "
        "why their remit matches this paper. " + NO_FABRICATION + " Cite the "
        "journal editorial-board pages directly."
    ),
    "likely_reviewers": (
        "Identify ~15-25 named researchers who would be credible, appropriate "
        "peer reviewers (suggested reviewers) for the project described below, "
        "spanning its sub-topics. " + VENUE_CONTEXT + " Organize the suggested "
        "reviewers into categories: (a) self-driving laboratories / autonomous "
        "experimentation / lab automation; (b) open-source scientific hardware "
        "and low-cost instrumentation; (c) powder dosing / dispensing / powder "
        "flowability and metrology; (d) additive manufacturing of alloys, "
        "high-throughput / combinatorial alloy discovery; (e) LLM / AI / "
        "code-based generative CAD and design automation. For each researcher "
        "give: full name, current affiliation, the specific overlapping "
        "expertise and 1-3 representative papers (with DOIs) that make them a "
        "good reviewer, and which sub-topic they cover. Prefer active "
        "mid-career-to-senior researchers and avoid obvious conflicts of "
        "interest where identifiable. " + NO_FABRICATION + " Cite each "
        "researcher's representative publications and faculty/ORCID page."
    ),
    "target_conferences": (
        "Identify and rank the best conferences, workshops, and symposia at "
        "which to present the project described below, covering both the "
        "self-driving-lab / materials angle and the generative-CAD angle. "
        + VENUE_CONTEXT + " Assess specifically: the Acceleration Consortium / "
        "self-driving-lab meetings and AI-for-materials acceleration workshops; "
        "MRS (Materials Research Society) Spring and Fall Meetings and relevant "
        "symposia; TMS Annual Meeting; the AIChE Annual Meeting; Faraday "
        "Discussions and RSC automation/AI meetings; Gordon Research "
        "Conferences relevant to autonomous experimentation or AM; additive-"
        "manufacturing conferences (RAPID + TCT, ASTM ICAM, Solid Freeform "
        "Fabrication Symposium); design-automation venues (ASME IDETC/CIE — "
        "Design Automation Conference and CIE); open-hardware venues (GOSH — "
        "Gathering for Open Science Hardware); and ML/vision/graphics venues "
        "and their workshops relevant to generative CAD (NeurIPS, ICML, ICLR "
        "AI4Science / AI4Mat / ML4Materials workshops, CVPR, SIGGRAPH). For "
        "each venue give: full name, organizer, scope, typical timing/location, "
        "submission format (abstract vs. full paper, archival vs. "
        "non-archival), approximate selectivity/prestige, and a 1-3 sentence "
        "justification of fit, grouped into best-fit, strong, and stretch "
        "tiers. Emphasize venues genuinely amenable to a hardware-focused, "
        "self-driving-lab contribution. " + NO_FABRICATION + " Cite official "
        "conference pages and representative recent editions."
    ),
}

TAG = "powder-doser-venues"


def extract_answer(data: dict) -> tuple[str, str]:
    """Pull the formatted answer + references out of a task model_dump()."""
    try:
        answer = data["environment_frame"]["state"]["state"]["response"]["answer"]
        formatted = answer.get("formatted_answer") or answer.get("answer") or ""
        references = answer.get("references") or ""
        return formatted, references
    except (KeyError, TypeError):
        pass
    formatted = data.get("formatted_answer") or data.get("answer") or ""
    references = data.get("references") or ""
    return formatted, references


def main() -> None:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        raise SystemExit(
            "EDISON_API_KEY is not set. Export it before running this script."
        )

    out_dir = Path(__file__).parent / "edison_artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = EdisonClient(api_key=api_key)
    tasks = [
        {
            "name": JobNames.LITERATURE_HIGH,
            "query": q,
            "tags": [TAG, key],
        }
        for key, q in QUERIES.items()
    ]
    print(f"Dispatching {len(tasks)} LITERATURE_HIGH tasks...", flush=True)
    results = client.run_tasks_until_done(
        tasks, verbose=True, progress_bar=False, timeout=3600
    )

    task_ids: dict[str, str] = {}
    for key, result in zip(QUERIES.keys(), results):
        data = (
            result.model_dump() if hasattr(result, "model_dump") else dict(result)
        )
        (out_dir / f"{key}.task.json").write_text(
            json.dumps(data, default=str, indent=2)
        )
        formatted, references = extract_answer(data)
        (out_dir / f"{key}.answer.md").write_text(formatted)
        (out_dir / f"{key}.references.md").write_text(references)
        task_ids[key] = str(data.get("task_id") or data.get("id") or "")
        print(
            f"  {key}: status={data.get('status')} id={task_ids[key]} "
            f"answer_chars={len(formatted)} refs_chars={len(references)}",
            flush=True,
        )

    (out_dir / "editors_reviewers_conferences_task_ids.json").write_text(
        json.dumps(task_ids, indent=2)
    )
    print(f"Wrote artifacts to {out_dir}", flush=True)


if __name__ == "__main__":
    main()

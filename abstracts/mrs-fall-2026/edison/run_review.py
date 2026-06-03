#!/usr/bin/env python3
"""Edison LITERATURE_HIGH: mock peer review of the MRS Fall 2026 abstract using
the personas of the organizers of the top-ranked symposia (MT03, MT01, MT04),
grounded in those organizers' recent literature. Asks for specific textual
additions, removals, and modifications. Polls to completion and writes the
answer + references."""
import json
import os
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest
from edison_client.models.rest import ExecutionStatus

HERE = Path(__file__).parent
OUT = HERE / "review_out"
OUT.mkdir(exist_ok=True)

ABSTRACT_TITLE = (
    "An Open-Source, Low-Cost Powder Doser Built with Agentic AI and Generative "
    "CAD for Autonomous Alloy Discovery"
)
ABSTRACT_BODY = (HERE.parent / "abstract.md").read_text()

QUERY = f"""We are preparing a single-symposium abstract for the 2026 MRS Fall Meeting \
(Boston). An Edison ANALYSIS of the official Call for Abstracts ranked the most \
aligned symposia as: MT03 (AI-Driven Workflows and Autonomous Platforms for \
Functional Material Design and Catalysis), MT01 (Leveraging Advances in AI for \
Materials Design and Autonomous Materials Science), and MT04 (Technologies for \
Informed and Accelerated Synthesis of Inorganic Materials), with materials-application \
alternates SF03 (Intermetallics) and SF01 (High-Entropy Materials).

Please act as a panel of MOCK PEER REVIEWERS for these symposia. Where possible, \
adopt the personas of the actual symposium organizers and ground your critique in \
their recent (last ~5 years) published literature, which you should search for and \
cite. The organizers are:
- MT03: Don Futaba (AIST, Japan), Rui Goncalves (Nanyang Technological University), \
Placidus Amama (Kansas State University), Karolina Laszczyk (Wroclaw University of \
Science and Technology).
- MT01: Guoxiang (Emma) Hu (Georgia Tech), Mahshid Ahmadi (University of Tennessee, \
Knoxville), Bin Ouyang (Florida State University), Dong-Hwa Seo (KAIST).
- MT04: Yong-Jie Hu (Drexel), Yan Zeng (Florida State University), Yuta Saito \
(Tohoku University), Richard Otis (Proteus Space / formerly NASA JPL).

For each persona/reviewer, look up representative recent work (autonomous \
experimentation, self-driving labs, Bayesian optimization, generative/agentic CAD, \
high-throughput inorganic synthesis, additive manufacturing of alloys, etc.) and \
review our abstract THROUGH THAT LENS, noting what such a reviewer would want to see.

Provide SPECIFIC, ACTIONABLE TEXTUAL SUGGESTIONS: concrete ADDITIONS (sentences or \
phrases to insert, and where), REMOVALS (text to cut and why), and MODIFICATIONS \
(rewordings), so we can edit the abstract directly. Then give an overall \
prioritized punch-list and note any claims that need stronger evidence or citation. \
Honor the MRS constraints: abstract body must stay <= 4000 characters including \
spaces, with no figures. Keep feedback faithful to what the abstract actually claims.

=== ABSTRACT UNDER REVIEW ===
Title: {ABSTRACT_TITLE}

{ABSTRACT_BODY}
"""


def main() -> None:
    client = EdisonClient(api_key=os.environ["EDISON_API_KEY"])
    task = TaskRequest(name=JobNames.LITERATURE_HIGH, query=QUERY)
    tid = client.create_task(task)
    print("trajectory_id:", tid, flush=True)
    (OUT / "review.task.json").write_text(
        json.dumps({"trajectory_id": str(tid), "query": QUERY}, indent=2)
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
            answer = (
                getattr(r, "formatted_answer", None)
                or getattr(r, "answer", None)
                or dump.get("formatted_answer")
                or dump.get("answer")
                or ""
            )
            (OUT / "review.answer.md").write_text(answer or "(no answer field)")
            refs = dump.get("formatted_answer") or ""
            # Persist any bibliography/context fields when present.
            for key in ("bibliography", "references", "context", "used_references"):
                val = dump.get(key)
                if val:
                    (OUT / f"review.{key}.json").write_text(
                        json.dumps(val, indent=2, default=str)
                    )
            print("=== TERMINAL:", status, "===", flush=True)
            print((answer or "(no answer)")[:6000], flush=True)
            return
    print("TIMEOUT waiting for review task", flush=True)


if __name__ == "__main__":
    main()

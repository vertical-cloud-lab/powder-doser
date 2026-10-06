#!/usr/bin/env python3
"""Edison LITERATURE_HIGH: mock peer review of the TMS 2027 abstract for the
symposium "Additive Manufacturing and Innovative Feedstock Processing for
Multifunctional Materials" (TMS 2027 Annual Meeting & Exhibition, Orlando).

Uses the personas of the symposium's four organizing-committee members as mock
reviewers, grounded in their recent literature, and asks for specific textual
additions, removals, and modifications plus a prioritized punch-list. The TMS
Call-for-Abstracts flyer text is embedded so the critique is anchored to the
symposium scope and key dates. Polls to completion and writes the answer."""
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

TASK_TIMEOUT_SECONDS = 2200


def _api_key() -> str:
    # copilot-instructions name EDISON_API_KEY; the CI environment provides it
    # as EDISON_PLATFORM_API_KEY. Accept either.
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


ABSTRACT_TITLE = (
    "An Open-Source, Low-Cost Powder Doser for Autonomous Metal-Alloy Discovery"
)
ABSTRACT_BODY = (HERE.parent / "abstract.md").read_text()
CFA_FLYER = (HERE / "cfa_flyer_text.md").read_text()

QUERY = f"""We are preparing a single abstract for the 2027 TMS Annual Meeting & \
Exhibition (Orlando, FL; March 14-18, 2027; abstract deadline July 1, 2026; body \
limited to 150 words, submitted via ProgramMaster). We intend to submit to the \
symposium "Additive Manufacturing and Innovative Feedstock Processing for \
Multifunctional Materials" (TMS Functional Materials Division; Additive Manufacturing \
and Magnetic Materials Committees).

Please act as a panel of MOCK PEER REVIEWERS drawn from that symposium's actual \
ORGANIZING COMMITTEE. Adopt each person's persona and ground your critique in their \
recent (last ~5-7 years) published literature, which you should search for and cite:
- Daniel Salazar (BCMaterials, Spain) - hard/soft magnets, permanent-magnet and \
magnetocaloric powders, additive manufacturing of magnetic materials.
- Markus Chmielus (University of Pittsburgh) - binder-jet and powder-bed additive \
manufacturing, magnetic shape-memory and functional alloys, powder characterization.
- Henry Colorado (Universidad de Antioquia, Colombia) - advanced/functional materials \
processing, composites, sustainable and additive manufacturing.
- Riccardo Casati (Politecnico di Milano, Italy) - laser powder bed fusion of \
aluminum and other structural alloys, feedstock powder and process-property relationships.

For each reviewer, look up representative recent work and review our abstract THROUGH \
THAT LENS, noting what such a reviewer would want to see, whether the work fits this \
symposium's scope (powder/wire synthesis and feedstock processing, atomization incl. \
ultrasonic, L-PBF and other AM routes, magnetic/functional/lightweight-structural \
materials), and where the abstract over- or under-reaches for this audience.

Provide SPECIFIC, ACTIONABLE TEXTUAL SUGGESTIONS: concrete ADDITIONS (sentences or \
phrases to insert, and where), REMOVALS (text to cut and why), and MODIFICATIONS \
(rewordings) so we can edit the abstract directly. Because this is a 150-word abstract, \
every suggestion must respect that hard limit - if you propose an addition, say what to \
cut to stay <= 150 words. Then give an overall prioritized punch-list and a table of any \
claims that need stronger evidence or citation. Keep feedback faithful to what the \
abstract actually claims; do not invent results. Also assess whether this symposium or \
one of the AI/ML/autonomous-workflow symposia would be the stronger home for this work.

=== TMS 2027 CALL-FOR-ABSTRACTS FLYER (symposium scope + key dates) ===
{CFA_FLYER}

=== ABSTRACT UNDER REVIEW (150-word body) ===
Title: {ABSTRACT_TITLE}

{ABSTRACT_BODY}
"""


def main() -> None:
    client = EdisonClient(api_key=_api_key())
    task = TaskRequest(name=JobNames.LITERATURE_HIGH, query=QUERY)
    tid = client.create_task(task)
    print("trajectory_id:", tid, flush=True)
    (OUT / "review.task.json").write_text(
        json.dumps({"trajectory_id": str(tid), "query": QUERY}, indent=2)
    )

    deadline = time.time() + TASK_TIMEOUT_SECONDS
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

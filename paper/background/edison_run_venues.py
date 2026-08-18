#!/usr/bin/env python3
"""Batch 1 of the publication-venue scouting for the powder-doser project
(issue: "Determine potential journals, editors, reviewers, and conferences").

Two Edison Scientific ``LITERATURE_HIGH`` (paperqa-class) queries are dispatched
in parallel:

* ``venues_sdl_hardware`` — candidate journals/venues for the powder-doser as a
  self-driving-lab (SDL) / open-hardware paper, assuming the closed-loop
  calibration algorithm, auger auto-change, and 50-unique-powder dispensing are
  all in place, and that extensive calibration data is reported.
* ``venues_generative_cad`` — higher-impact journals that fit the
  generative-CAD framing of the same project. The prompt is grounded with the
  generative-CAD venues that actually surfaced in the repo's prior Edison notes
  (PRs #29 and #43: ACM Transactions on Graphics / SIGGRAPH, CVPR / IEEE-CVF,
  NeurIPS, Computer-Aided Design, The International Journal of Advanced
  Manufacturing Technology, Journal of Mechanical Design, Additive
  Manufacturing, Proceedings of the Design Society).

Outputs are written to ``paper/background/edison_artifacts/`` with the same
layout as the existing runners (``<key>.task.json`` / ``.answer.md`` /
``.references.md``), plus any agent-generated structured tables as
``<key>.<artifact>.md`` (e.g. ``<key>.artifact-00.md``). Run with::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_venues.py

Each high-effort literature query takes roughly 20-30 minutes; both are
dispatched in parallel via ``run_tasks_until_done``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

QUERIES: dict[str, str] = {
    "venues_sdl_hardware": (
        "Identify and rank the best peer-reviewed journals to publish an "
        "open-hardware, self-driving-laboratory (SDL) instrument paper, and "
        "explain the fit of each. The instrument is a low-cost, open-source "
        "multi-powder doser for autonomous additive-manufacturing (AM) alloy "
        "and materials discovery. Assume the following capabilities are already "
        "in place: a closed-loop gravimetric calibration algorithm with "
        "extensive reported calibration data across many powders; an automatic "
        "auger / screw auto-change mechanism; and the ability to dispense up to "
        "50 unique powders in one run. The paper will combine mechanical "
        "(CAD/3D-printed hardware), electronics/firmware, control software, and "
        "a substantial materials-science calibration dataset. For each candidate "
        "venue give: full journal name, publisher, scope, approximate impact "
        "factor / CiteScore, whether it accepts hardware/methods/dataset papers, "
        "open-access options and typical APC, typical time-to-decision, and a "
        "1-3 sentence justification of fit. Explicitly assess Digital Discovery "
        "(RSC), HardwareX (Elsevier), Journal of Open Hardware, the Journal of "
        "Open Source Hardware/Software, Review of Scientific Instruments (AIP), "
        "HardwareX-style instrument venues, Cell Reports Physical Science, "
        "Matter, Nature Communications, npj Computational Materials, ACS Central "
        "Science, Lab on a Chip, IEEE/ASME Transactions on Mechatronics, "
        "Additive Manufacturing, Additive Manufacturing Letters, Materials & "
        "Design, Science Advances, PLOS ONE, SoftwareX, and any others you "
        "consider strong. Group them into tiers (best-fit/primary, strong "
        "secondary, stretch/high-impact, and fallback). Emphasize venues that "
        "are genuinely amenable to a hardware-focused, self-driving-lab "
        "contribution with calibration data. Cite journal scope pages and "
        "representative recent (2020-2025) SDL / open-hardware / automated "
        "materials papers published in each."
    ),
    "venues_generative_cad": (
        "Identify and rank the highest-impact peer-reviewed venues (journals "
        "and archival conference proceedings) to publish work that leans into "
        "the GENERATIVE-CAD aspect of an open-hardware self-driving-laboratory "
        "project, in which the mechanical hardware (a multi-powder doser for "
        "autonomous AM alloy discovery) is designed via an LLM/AI-driven, "
        "code-based generative-CAD pipeline (e.g., CadQuery / build123d / "
        "OpenSCAD text-to-CAD, agentic design loops, geometry-kernel verifiers, "
        "design-for-additive-manufacturing). Prior literature reviews for this "
        "project (the project's own generative-CAD background notes) found that "
        "generative-CAD work is published across: ACM Transactions on Graphics "
        "(SIGGRAPH / SIGGRAPH Asia), CVPR / ICCV / ECCV and other IEEE/CVF "
        "venues, NeurIPS / ICML / ICLR, Computer-Aided Design (Elsevier), "
        "Computer-Aided Design and Applications, The International Journal of "
        "Advanced Manufacturing Technology, ASME Journal of Mechanical Design, "
        "Journal of Computing and Information Science in Engineering (JCISE), "
        "Additive Manufacturing, Applied Sciences, Computers in Industry, "
        "Advanced Engineering Informatics, and Proceedings of the Design "
        "Society. For each candidate venue give: full name, publisher, scope, "
        "approximate impact factor / CiteScore / h5-index (for conferences), "
        "whether it accepts an applied systems/hardware contribution that uses "
        "(rather than purely advances) generative-CAD methods, typical "
        "acceptance bar, and a 1-3 sentence justification of fit. Specifically "
        "weigh the trade-off that this is an APPLIED hardware/SDL contribution "
        "using generative CAD as a design methodology, not a pure ML/graphics "
        "methods paper, and flag which high-impact venues would or would not "
        "accept it on that basis. Recommend the best high-impact venue(s) that "
        "remain reasonably amenable to a hardware-focused, self-driving-lab "
        "contribution. Cite venue scope pages and representative recent "
        "(2022-2025) generative-CAD papers in each."
    ),
}

TAG = "powder-doser-venues"


def extract_answer(data: dict) -> tuple[str, str, dict]:
    """Pull the formatted answer, references, and agent-generated artifacts.

    PaperQA emits structured tables under ``answer.artifacts`` (e.g.
    ``artifact-00``); these are distinct from the prose answer and references and
    must be persisted alongside them so no associated artifact is dropped.
    """
    try:
        answer = data["environment_frame"]["state"]["state"]["response"]["answer"]
        formatted = answer.get("formatted_answer") or answer.get("answer") or ""
        references = answer.get("references") or ""
        artifacts = answer.get("artifacts") or {}
        return formatted, references, artifacts
    except (KeyError, TypeError):
        pass
    # PQATaskResponse fallback (top-level formatted_answer / answer).
    formatted = data.get("formatted_answer") or data.get("answer") or ""
    references = data.get("references") or ""
    artifacts = data.get("artifacts") or {}
    return formatted, references, artifacts


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
        formatted, references, artifacts = extract_answer(data)
        (out_dir / f"{key}.answer.md").write_text(formatted)
        (out_dir / f"{key}.references.md").write_text(references)
        for akey, content in sorted((artifacts or {}).items()):
            text = content or ""
            if not text.endswith("\n"):
                text += "\n"
            (out_dir / f"{key}.{akey}.md").write_text(text)
        task_ids[key] = str(data.get("task_id") or data.get("id") or "")
        print(
            f"  {key}: status={data.get('status')} id={task_ids[key]} "
            f"answer_chars={len(formatted)} refs_chars={len(references)} "
            f"artifacts={len(artifacts or {})}",
            flush=True,
        )

    (out_dir / "venues_task_ids.json").write_text(json.dumps(task_ids, indent=2))
    print(f"Wrote artifacts to {out_dir}", flush=True)


if __name__ == "__main__":
    main()

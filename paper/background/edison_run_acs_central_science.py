#!/usr/bin/env python3
"""Follow-up venue evaluation: ACS Central Science (PR #91 discussion).

Phillip Lampkin (U. Utah) suggested ACS Central Science as a fit for the
powder-doser paper, with the framing "generative AI got us ~80% of the way to
a useful, affordable device that solves a longstanding solids-dosing problem
in chemistry", modeled after the MacMillan-group integrated photoreactor paper
(Le et al., ACS Cent. Sci. 2017, 3, 647-653, DOI 10.1021/acscentsci.7b00159).

This runner dispatches a single Edison ``LITERATURE_HIGH`` query that
evaluates ACS Central Science against the shortlist already established in
``15-target-journals-and-venues.md`` / ``19-consolidated-recommendation.md``
(Digital Discovery primary; HardwareX + JOSS/SoftwareX companions; Additive
Manufacturing / AM Letters / Advanced Engineering Informatics / IJAMT as the
AM-leaning alternatives), using the photoreactor paper as the key precedent.

Outputs follow the existing layout in ``paper/background/edison_artifacts/``:
``acs_central_science.{task.json,answer.md,references.md}`` plus any
agent-generated tables as ``acs_central_science.<artifact>.md``. Run with::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_acs_central_science.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

QUERIES: dict[str, str] = {
    "acs_central_science": (
        "Evaluate ACS Central Science as a publication venue for an "
        "open-hardware, AI-designed laboratory instrument paper, and compare "
        "it against a shortlist of alternatives. The instrument is a low-cost, "
        "open-source multi-powder doser for autonomous additive-manufacturing "
        "(AM) alloy and materials discovery in self-driving labs (SDLs): "
        "closed-loop gravimetric calibration with extensive calibration data "
        "across many AM-relevant powders, automatic auger auto-change, and "
        "dispensing of up to 50 unique powders per run. Critically, the "
        "mechanical design was produced largely (~80%) via an LLM-driven, "
        "code-based generative-CAD pipeline, so one candidate framing is: "
        "'generative AI can quickly get you most of the way to a useful, "
        "affordable device that solves a longstanding problem in solids "
        "dosing/powder dispensing for chemistry and materials labs'. "
        "Address the following, citing verifiable sources: "
        "(1) ACS Central Science scope, article types, selectivity/acceptance "
        "bar, open-access model and any APC (it is reportedly fully open "
        "access with no author charges - verify), impact factor/CiteScore, "
        "and typical time-to-decision. "
        "(2) The precedent of Le, Wismer, ..., MacMillan, 'A General "
        "Small-Scale Reactor To Enable Standardization and Acceleration of "
        "Photocatalytic Reactions', ACS Cent. Sci. 2017, 3, 647-653 (DOI "
        "10.1021/acscentsci.7b00159): what made that device paper acceptable "
        "there (standardization, reproducibility, broad utility to the "
        "chemistry community, commercialization as the integrated "
        "photoreactor), and how closely the powder-doser story could map onto "
        "it. Identify OTHER ACS Central Science papers (2017-2025) reporting "
        "devices, instruments, lab automation, self-driving labs, or "
        "AI-assisted design, to gauge how regularly such work appears there. "
        "(3) The main risks: the doser targets AM alloy/materials workflows "
        "more than mainstream chemistry; ACS Central Science expects broad "
        "significance to the chemical sciences; assess whether a solids-dosing "
        "/ powder-handling pain point (e.g., automated dispensing of solid "
        "reagents and catalysts in high-throughput and self-driving chemistry "
        "labs) is a recognized longstanding problem in the chemistry "
        "literature that this device credibly addresses. "
        "(4) Compare ACS Central Science head-to-head with the existing "
        "shortlist for this paper: Digital Discovery (RSC, current primary), "
        "Additive Manufacturing (Elsevier), Additive Manufacturing Letters, "
        "Advanced Engineering Informatics, International Journal of Advanced "
        "Manufacturing Technology, and HardwareX (+ JOSS/SoftwareX as "
        "companions). For each: audience reached (chemistry vs AM/alloy vs "
        "SDL/automation), prestige, OA cost, and whether the AI-designed- "
        "device framing or the AM-alloy-calibration framing plays better. "
        "(5) Give a bottom-line recommendation: under what conditions ACS "
        "Central Science should displace Digital Discovery or Additive "
        "Manufacturing as the primary target, what the manuscript would need "
        "to emphasize (e.g., chemistry-lab solid dosing use cases, benchmark "
        "generality, the MacMillan-style standardization story), and how a "
        "companion HardwareX/JOSS strategy would interact with an ACS Central "
        "Science submission. Do not fabricate editor names or contact "
        "details; include a public source URL for any named person."
    ),
}

TAG = "powder-doser-acs-central-science"


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
    print(f"Dispatching {len(tasks)} LITERATURE_HIGH task(s)...", flush=True)
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

    (out_dir / "acs_central_science_task_ids.json").write_text(
        json.dumps(task_ids, indent=2)
    )
    print(f"Wrote artifacts to {out_dir}", flush=True)


if __name__ == "__main__":
    main()

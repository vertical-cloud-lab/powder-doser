#!/usr/bin/env python3
"""Reproducibility runner for the four Edison Scientific LITERATURE_HIGH queries
that produced the markdown notes in ``paper/background/``.

The exact prompts are duplicated here verbatim from the ``Question:`` line at
the top of each ``0*-*.md`` file so this script is a self-contained record of
what was sent to Edison. Outputs are written to
``paper/background/edison_artifacts/``:

* ``<key>.task.json``  — full ``TaskResponse.model_dump()`` from Edison
  (status, agent state, environment frame, response, references, contexts,
  cost, token counts, ...).
* ``<key>.answer.md``  — the rendered ``formatted_answer`` (or ``answer``)
  string, identical to what was committed as ``0*-*.md`` minus our local
  formatting.
* ``<key>.references.md`` — the standalone numbered references list.

Run with ``EDISON_API_KEY`` set in the environment::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run.py

A high-effort literature query takes roughly 20-30 minutes per task; all four
are dispatched in parallel via ``run_tasks_until_done``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

QUERIES: dict[str, str] = {
    "powder_commercial": (
        "Provide a comprehensive landscape review of commercial powder dispensing "
        "and dosing solutions used in laboratories, pharmaceutical manufacturing, "
        "and metal additive manufacturing (AM). Include specific company and product "
        "names (e.g., Mettler Toledo Quantos, Chemspeed, Freeman Technology FT4, "
        "Schenck Process, Coperion K-Tron, Gericke, ATS Scientific, Sartorius, "
        "Brabender, Movacolor, Schenck AccuRate, MTS, etc.), quoted accuracy/precision "
        "specifications (mg or % deviation), throughput, supported powder types, and "
        "approximate price ranges. Highlight the gap between high-end (>$50k) "
        "automated dosers and the lack of accessible solutions for research labs "
        "performing high-throughput multi-material AM alloy discovery. Cite all "
        "claims and include vendor URLs and recent (2018-2025) trade or peer-reviewed "
        "sources."
    ),
    "powder_academic": (
        "Find recent (2018-2025) peer-reviewed academic publications on automated "
        "powder dispensing, dosing, and feeding for: (a) multi-material and "
        "high-throughput metal additive manufacturing of aerospace alloys (Ni, Ti, "
        "high-entropy alloys, refractory alloys), (b) compositionally graded alloy "
        "discovery and combinatorial materials science, (c) self-driving labs / "
        "autonomous experimentation that handle solid powders, and (d) characterization "
        "of powder flowability and dosing accuracy (cohesive, fine, irregular powders). "
        "For each paper give: full citation (authors, year, journal, volume, pages, "
        "DOI), a 3-5 sentence summary, and why it is relevant to the design of a "
        "low-cost open-hardware multi-powder doser for autonomous AM alloy discovery. "
        "Aim for ~10-15 strong references."
    ),
    "gencad_landscape": (
        "Provide a state-of-the-art landscape of generative CAD and generative design "
        "tools and research as of 2025. Cover: (a) commercial topology-optimization / "
        "generative-design products (Autodesk Fusion Generative Design, nTopology / "
        "nTop, Siemens NX Topology Optimizer, PTC Creo Generative Design, ANSYS "
        "Discovery, Altair Inspire, Rhino + Grasshopper); (b) parametric / "
        "code-based CAD frameworks (CadQuery, OpenSCAD, build123d, Onshape "
        "FeatureScript, JSCAD); (c) AI/LLM-driven CAD generation research "
        "(Text2CAD, CAD-LLM, DeepCAD, SkexGen, Point2CAD, sketch-to-3D, multimodal "
        "diffusion-based CAD, agentic CAD pipelines); and (d) constraints/limitations "
        "of each (manufacturability, editability, parametric controllability, "
        "scriptability for CI/CD). Quote benchmark results where available. Cite "
        "vendor pages and ~5 recent (2022-2025) peer-reviewed or arXiv papers."
    ),
    "gencad_academic": (
        "Find recent (2021-2025) peer-reviewed and arXiv academic publications on "
        "generative CAD, AI-assisted CAD, LLM-based CAD code generation, "
        "parametric/programmatic CAD, and learning-based shape generation for "
        "engineering design. Cover capabilities (text-to-CAD, sketch-to-CAD, "
        "constraint-aware generation, design-for-AM, B-rep generation, CSG / "
        "feature-tree generation, agentic design loops) and limitations "
        "(manufacturability, parametric editability, accuracy, evaluation benchmarks, "
        "hallucination of features, lack of standard datasets). For each paper give: "
        "full citation, 3-5 sentence summary, and relevance to building a Python/"
        "code-based generative CAD pipeline for an open-source powder-dosing device. "
        "Include landmark datasets/benchmarks (DeepCAD, Fusion 360 Gallery, ABC "
        "dataset, SketchGraphs, Text2CAD). Aim for ~10-15 references."
    ),
}

TAG = "powder-doser-grant"


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
        tasks, verbose=True, progress_bar=False, timeout=3000
    )

    for key, result in zip(QUERIES.keys(), results):
        data = (
            result.model_dump() if hasattr(result, "model_dump") else dict(result)
        )
        (out_dir / f"{key}.task.json").write_text(
            json.dumps(data, default=str, indent=2)
        )
        try:
            answer = data["environment_frame"]["state"]["state"]["response"]["answer"]
            formatted = answer.get("formatted_answer") or answer.get("answer") or ""
            references = answer.get("references") or ""
        except (KeyError, TypeError):
            formatted, references = "", ""
        (out_dir / f"{key}.answer.md").write_text(formatted)
        (out_dir / f"{key}.references.md").write_text(references)
        print(
            f"  {key}: status={data.get('status')} "
            f"answer_chars={len(formatted)} refs_chars={len(references)}",
            flush=True,
        )

    print(f"Wrote artifacts to {out_dir}", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Follow-up Edison Scientific LITERATURE_HIGH query, dispatched in response to
@sgbaird-alt's question on PR #34 about mitigating LLM spatial-reasoning /
assembly failures observed in PR #35 (Claude Opus 4.7-generated CadQuery model).

The full context for the question is the review at
https://github.com/vertical-cloud-lab/powder-doser/pull/35#pullrequestreview-4274628757
and the inline review comments on
``design/cad/single-channel-module/cad_model.py`` and its ``README.md``.

Output goes to ``paper/background/edison_artifacts/`` with the same layout as
the original four queries (``<key>.task.json`` / ``.answer.md`` /
``.references.md``). Run with::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_followup_spatial.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

QUERIES: dict[str, str] = {
    "llm_cad_spatial_mitigation": (
        "Find recent (2023-2026) peer-reviewed and arXiv academic publications, "
        "engineering reports, and developer write-ups on the spatial reasoning, "
        "assembly, and geometric-correctness limitations of large language models "
        "(LLMs) and agentic systems when generating mechanical CAD — specifically "
        "code-based CAD (CadQuery, OpenSCAD, build123d, FreeCAD Python API), "
        "B-rep / feature-tree generation, and LLM-driven parametric assembly. "
        "Cover the following failure modes that have been empirically observed in "
        "Claude Opus 4.7 / GPT-class models generating CadQuery code: (i) parts "
        "modelled in isolation but never Boolean-unioned with the host body "
        "(e.g., mounting bosses floating off a ring, brackets not attached); "
        "(ii) wrong-direction Boolean cuts and extrudes (e.g., CadQuery "
        "`workplane(invert=True)`, `extrude(both=True)` doubling thickness, "
        "`cut`/`hole` going the wrong way); (iii) clearance / fit / tolerance "
        "values that are arithmetically inconsistent (e.g., N modules on a pitch "
        "circle that geometrically overlap, made-up clearances that don't match "
        "operating envelope); (iv) missing functional paths (e.g., no inlet for "
        "powder/fluid, motor blocks the part it drives, no fastener access); "
        "(v) vendor-part envelopes ignored or misremembered; (vi) fastener "
        "strategy underspecified (self-tap into FDM print vs. heat-set inserts "
        "vs. through-bolts). For each source give: full citation (authors, year, "
        "venue, DOI/arXiv ID), 3-5 sentence summary, and the concrete mitigation "
        "strategy it proposes or evaluates. Specifically catalogue mitigations "
        "across these axes: (A) tool-side guardrails — schema-constrained "
        "decoding, deterministic geometry-kernel verifiers (OCCT/CadQuery topology "
        "checks, watertight/manifold checks, interference / clash detection, "
        "DRC-style design rule checks for AM, FEA-in-the-loop, slicer-side "
        "printability checks); (B) prompting / agent strategies — "
        "self-consistency, self-repair / critic-revisor loops, ReAct-style "
        "tool-use with a CAD kernel, multi-view rendering fed back into the "
        "model (visual chain-of-thought / image-augmented critique), test-driven "
        "CAD (write assertions on volume, mass, bounding box, hole counts, "
        "interference-free assemblies); (C) representation choices — sketch + "
        "constraint-based vs. CSG vs. mesh, decomposition into sub-assemblies, "
        "explicit interface contracts between parts, parametric skeletons / "
        "datums, vendor-component libraries with verified envelopes (KiCad-style "
        "footprint libs but for mechanical); (D) human-in-the-loop and "
        "manual-intervention patterns — where to insert a human reviewer, what "
        "review artifacts (multi-view renders, dimensioned 2D sketches, "
        "exploded views, animated assembly), how to make manual edits feed back "
        "into the parametric source, and the cost/benefit of fully autonomous "
        "vs. supervised generation for hardware that will be 3D printed and "
        "assembled. Include landmark / canonical references (CAD-LLM, Text2CAD, "
        "DeepCAD, SkexGen, Fusion 360 Gallery, ABC dataset, SketchGraphs, "
        "CADCrafter, BlenderBench, related agentic-design benchmarks like "
        "BlocksWorld / spatial-reasoning evals) and quote any reported quantitative "
        "results (pass rate, watertightness rate, manufacturability rate, human "
        "edit distance). Aim for ~12-18 references."
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
            "tags": [TAG, key, "followup-spatial"],
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

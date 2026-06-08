#!/usr/bin/env python3
"""Edison Scientific ``LITERATURE_HIGH`` runner for the *intermediate step* in the
generative-PCB pipeline: tools that take a high-level **topology / block diagram +
component list + requirements** and produce a **basic "starter" board design**
(a schematic with assigned footprints and a preliminary board outline / floorplan)
in KiCad (or similar) that can then be handed to an autonomous **placement/routing**
engine such as Quilter or DeepPCB.

This answers @lbwinters' observation on PR #76
(https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4653987091)
that neither Quilter nor DeepPCB can start from a bare topology — both need a
fully-defined starter board — so a *bridge* tool is required between a topology
generator (e.g. LaMAGIC) and the layout engines, and @sgbaird's follow-up request
to "query Edison Scientific to research any similar tools (using generative AI to
move from a basic topology and list of components and requirements to a basic
board design in KiCad or similar)".

Like the other ``LITERATURE_HIGH`` runners in this folder
(``edison_run.py``, ``edison_run_electrical_pcb.py``) this is the open-literature
``paperqa`` pipeline (not the file-analysis "crow"); the companion
``edison_run_topology_to_board_analysis.py`` runs the ``ANALYSIS`` job over this
repo's actual KiCad schematic. The exact prompt is embedded verbatim below so the
script is a self-contained record of what was sent to Edison. Outputs land in
``paper/background/edison_artifacts/``:

* ``<key>.task.json``  -- full ``TaskResponse.model_dump()`` from Edison.
* ``<key>.answer.md``  -- the rendered ``formatted_answer`` (or ``answer``).
* ``<key>.references.md`` -- the standalone numbered references list.

Run with ``EDISON_API_KEY`` (or ``EDISON_PLATFORM_API_KEY``) set::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_topology_to_board.py

A high-effort literature query takes roughly 20-40 minutes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

KEY = "topology_to_starter_board_tools"
TAG = "powder-doser-grant"
PILLAR_TAG = "electrical-pcb"

QUERY = (
    "Survey, as of 2025, the tools, services, and research methods that use "
    "generative AI / automation to perform the INTERMEDIATE step of the PCB design "
    "pipeline: taking a high-level circuit TOPOLOGY or block diagram, a list of "
    "COMPONENTS (or functional requirements/specifications), and producing a basic "
    "'starter' board design that a downstream autonomous placement/routing engine "
    "(such as Quilter or DeepPCB / InstaDeep) can ingest. Concretely, the target "
    "output of this intermediate step is a captured SCHEMATIC with a complete "
    "netlist, real manufacturer parts with assigned physical FOOTPRINTS, a Bill of "
    "Materials, and ideally a preliminary board OUTLINE and component FLOORPLAN, "
    "exported as native KiCad (or Altium/EAGLE) files. Because autonomous routers "
    "explicitly cannot start from a bare topology (they require footprints, a board "
    "outline, and design rules), this 'topology+BOM -> starter board' gap is the "
    "focus.\n\n"
    "Cover specifically:\n"
    "(a) commercial / AI-native platforms that claim to bridge concept or block "
    "diagram to schematic + floorplan, e.g. CELUS (CELUS Design Platform, CUBOs, "
    "Design Assistant), Flux.ai (AI schematic copilot), JITX (programmatic "
    "design / algorithmic floorplanning), Circuit Mind, Cofactr/Diadem, "
    "Quilter and DeepPCB's own input requirements and any pre-layout helpers; for "
    "each: what input it accepts (topology/block diagram vs. full schematic), what "
    "it outputs (schematic, netlist, footprints, BOM, board outline, floorplan), "
    "which ECAD formats it exports (KiCad?), whether it has a public API / CLI / "
    "scriptable interface vs. GUI/login-only, pricing/free-tier, and maturity.\n"
    "(b) design-as-code / programmatic frameworks that can generate a footprinted, "
    "netlisted KiCad project from a higher-level description (atopile, tscircuit, "
    "SKiDL, Horizon EDA, KiCad's Python / IPC API + kicad-cli, PCBmodE), and how "
    "much of board-outline/floorplan generation they automate vs. leave manual.\n"
    "(c) recent (2020-2025) peer-reviewed / arXiv research on automatically going "
    "from netlist or topology to an initial PLACEMENT / FLOORPLAN / board outline "
    "(analog/PCB placement, constructive floorplanning, ML/RL placement, "
    "LLM-driven schematic-to-layout, force-directed or partitioning-based initial "
    "placement), including benchmarks and reported success rates.\n"
    "(d) honest assessment of the gap: for a low-cost, open-hardware, "
    "mixed-signal motor + sensor control board (microcontroller driving stepper "
    "drivers, solenoids, servos, vibration motors, and an HX711/load-cell front "
    "end), how automatable is this intermediate step today, what still requires a "
    "human, and which tools are realistically usable from a headless, "
    "version-controlled, CI / coding-agent workflow (no interactive GUI).\n\n"
    "For each tool/method give: what it is, the concrete input->output, ECAD/KiCad "
    "interoperability, scriptability/API availability, licensing/cost, maturity, "
    "and cited evidence (vendor documentation and ~8-15 recent peer-reviewed or "
    "arXiv papers). Conclude with which tools most credibly fill the "
    "topology+BOM -> KiCad-starter-board gap and feed cleanly into Quilter/DeepPCB."
)


def _api_key() -> str:
    for name in ("EDISON_API_KEY", "EDISON_PLATFORM_API_KEY"):
        val = os.environ.get(name)
        if val:
            return val
    raise SystemExit(
        "Set EDISON_API_KEY (or EDISON_PLATFORM_API_KEY) before running this script."
    )


def main() -> None:
    api_key = _api_key()
    out_dir = Path(__file__).parent / "edison_artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = EdisonClient(api_key=api_key)
    task = {
        "name": JobNames.LITERATURE_HIGH,
        "query": QUERY,
        "tags": [TAG, PILLAR_TAG, KEY],
    }
    print("Dispatching LITERATURE_HIGH task (this can take 20-40 min)...", flush=True)
    results = client.run_tasks_until_done(
        [task], verbose=True, progress_bar=False, timeout=5400
    )

    result = results[0]
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    (out_dir / f"{KEY}.task.json").write_text(json.dumps(data, default=str, indent=2))

    formatted, references = _extract(data)
    (out_dir / f"{KEY}.answer.md").write_text(formatted)
    (out_dir / f"{KEY}.references.md").write_text(references)
    print(
        f"  {KEY}: status={data.get('status')} "
        f"answer_chars={len(formatted)} refs_chars={len(references)}",
        flush=True,
    )
    print(f"Wrote artifacts to {out_dir}", flush=True)


def _extract(data: dict) -> tuple[str, str]:
    for key in ("formatted_answer", "answer"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val, data.get("references") or ""
    try:
        answer = data["environment_frame"]["state"]["state"]["response"]["answer"]
    except (KeyError, TypeError):
        return "", ""
    if isinstance(answer, dict):
        formatted = answer.get("formatted_answer") or answer.get("answer") or ""
        return formatted, answer.get("references") or ""
    if isinstance(answer, str):
        return answer, ""
    return "", ""


if __name__ == "__main__":
    main()

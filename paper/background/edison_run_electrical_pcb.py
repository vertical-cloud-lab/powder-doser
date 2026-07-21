#!/usr/bin/env python3
"""Reproducibility runner for the Edison Scientific LITERATURE_HIGH queries that
expand the ``paper/background/`` literature review from generative *CAD* (issue
#28 / PR #29) to generative *electrical and PCB design* (issue #75).

Background context for the queries comes from this repo's electrical-system work:
the powder-doser is a low-cost, open-hardware, modular multi-powder dosing device
whose test/bench electronics are authored as KiCad projects driven by a
microcontroller (Raspberry Pi Pico W / RP2040) controlling stepper drivers,
vibration motors, solenoids, servos, and load-cell feedback, with an emphasis on
easy I/O expansion to many modules (see issues #25, #44, #60 and PRs #45, #61).

The exact prompts are embedded verbatim below so this script is a self-contained
record of what was sent to Edison. Outputs are written to
``paper/background/edison_artifacts/``:

* ``<key>.task.json``  — full ``TaskResponse.model_dump()`` from Edison
  (status, agent state, environment frame, response, references, contexts,
  cost, token counts, ...).
* ``<key>.answer.md``  — the rendered ``formatted_answer`` (or ``answer``)
  string.
* ``<key>.references.md`` — the standalone numbered references list.

Run with ``EDISON_API_KEY`` set in the environment::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_electrical_pcb.py

A high-effort literature query takes roughly 20-30 minutes per task; all of them
are dispatched in parallel via ``run_tasks_until_done``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

QUERIES: dict[str, str] = {
    "gen_eda_landscape": (
        "Provide a state-of-the-art landscape of generative, AI-assisted, and "
        "automated tools for electronic design automation (EDA), schematic capture, "
        "and printed circuit board (PCB) design as of 2025. Cover: (a) mainstream "
        "schematic/PCB design suites and their automation/AI features (KiCad and its "
        "scripting/IPC API, Altium Designer and Altium 365 / Co-Designer AI, Cadence "
        "Allegro/OrCAD X and the Allegro AI/Optimality engines, Siemens Xpedition / "
        "PADS, Zuken CR-8000, Autodesk Fusion Electronics / EAGLE, DipTrace, "
        "EasyEDA); (b) AI-native and generative EDA startups and products (Flux.ai, "
        "JITX, Quilter, DeepPCB / InstaDeep, Celus, CELUS Design Platform, Diadem, "
        "Cofactr, Allspice, Snapmagic/SnapEDA, Spectra/Untether, Microsoft/Google "
        "ML-placement efforts); (c) cloud/CI-friendly and code-based hardware "
        "description ecosystems (atopile, tscircuit, SKiDL, PCBmodE, gEDA, Edea, "
        "Horizon EDA); and (d) for each, the concrete generative/automation "
        "capability offered (component selection, schematic generation, auto "
        "placement, autorouting, DFM/DRC, BOM and supply-chain optimization) and its "
        "limitations (manufacturability, editability, controllability, scriptability "
        "for version control / CI). Quote benchmark or case-study results where "
        "available. Emphasize which tools are open-source or scriptable and therefore "
        "suitable for an open-hardware, CI-driven workflow. Cite vendor pages and "
        "~5-8 recent (2021-2025) peer-reviewed or arXiv papers."
    ),
    "eda_schematic_synthesis_academic": (
        "Find recent (2019-2025) peer-reviewed and arXiv academic publications on "
        "automated and generative schematic / circuit-topology synthesis and netlist "
        "generation for electronic design. Cover: (a) machine-learning and generative "
        "models for analog and mixed-signal circuit topology generation, (b) "
        "LLM-based and agentic generation of schematics, netlists, and circuit "
        "descriptions (e.g., LaMAGIC, AnalogCoder, Atelier/Artisan-style analog "
        "agents, schematic-from-spec systems), (c) graph-neural-network and "
        "reinforcement-learning approaches to circuit synthesis and device sizing, and "
        "(d) constraint-/specification-driven topology selection. For each paper give: "
        "full citation (authors, year, venue, volume, pages, DOI/arXiv id), a 3-5 "
        "sentence summary, and why it is relevant to building a code-based generative "
        "pipeline for the control/driver electronics of an open-source modular "
        "multi-powder dosing device (microcontroller, stepper drivers, motor drivers, "
        "load-cell front-end). Note capabilities and limitations (validity of "
        "generated circuits, manufacturability, hallucination, evaluation). Aim for "
        "~10-15 strong references."
    ),
    "pcb_placement_routing_ml": (
        "Find recent (2018-2025) peer-reviewed and arXiv academic publications on "
        "machine-learning, reinforcement-learning, and optimization-based methods for "
        "PCB and chip physical design — specifically component placement and routing. "
        "Cover: (a) deep-RL and learning-based macro/component placement (e.g., Google "
        "Nature 2021 chip placement and its critiques/reproductions such as Cheng et "
        "al. 'The False Dawn' and Stronger Baselines), (b) analog and PCB placement "
        "automation, (c) learning-based and classical autorouting / detailed routing "
        "for PCBs (DeepPCB and related), (d) DRC-aware and manufacturability-aware "
        "placement/routing, and (e) benchmarks and metrics used to evaluate them. For "
        "each paper give: full citation, 3-5 sentence summary, and relevance to "
        "automatically generating manufacturable PCBs for low-cost open-hardware motor "
        "/ sensor control boards. Highlight reported quantitative results "
        "(wirelength, congestion, DRC violations, runtime) and known limitations. Aim "
        "for ~10-15 references."
    ),
    "llm_hardware_hdl_codegen": (
        "Find recent (2022-2025) peer-reviewed and arXiv academic publications on "
        "large-language-model and code-generation approaches to hardware design: "
        "LLM-based generation of HDL (Verilog/VHDL/Chisel), netlists, analog circuit "
        "code, and structured hardware description, plus agentic / multi-step "
        "design loops and self-repair. Cover landmark and representative systems "
        "(e.g., ChipGPT, ChipNeMo, VerilogEval, RTLLM, AutoChip, AnalogCoder, "
        "LaMAGIC, MAGE/agentic-EDA, GPT4AIGChip, self-debugging / self-verification "
        "loops) and the benchmarks used to evaluate them (functional correctness, "
        "synthesizability, pass@k). For each give: full citation, 3-5 sentence "
        "summary, and relevance to LLM-driven generation of microcontroller-centric "
        "control electronics and firmware for an open-hardware lab-automation device. "
        "Discuss capabilities and limitations (correctness, hallucination of parts or "
        "pins, verification, dataset scarcity). Aim for ~10-15 references."
    ),
    "code_based_eda_frameworks": (
        "Provide an in-depth review of code-based, programmatic, and "
        "'design-as-code' approaches to electronics and PCB design that can be "
        "version-controlled and driven from a CI pipeline (analogous to code-CAD such "
        "as CadQuery/OpenSCAD for mechanical design). Cover tools and frameworks "
        "including atopile (the .ato language), tscircuit (React-for-PCB), SKiDL, "
        "PCBmodE, gEDA/gaf, Horizon EDA, Edea, KiCad's Python / IPC scripting and "
        "kicad-cli, JITX (Stanza-based programmatic PCB), and any LLM/text-to-PCB or "
        "text-to-schematic research prototypes. For each, describe the programming "
        "model, what is generated automatically vs. specified by the designer, "
        "support for parametrization and reuse, manufacturability/DRC integration, "
        "rendering/export (Gerber, BOM, netlist), maturity, and licensing. Discuss the "
        "trade-offs versus GUI-based EDA and versus AI/generative EDA, and which "
        "approaches best fit an open-hardware, reproducible, CI-rendered workflow for "
        "a modular multi-powder dosing device. Cite project pages/repos and ~5-8 "
        "recent (2020-2025) papers or technical sources."
    ),
    "eda_datasets_benchmarks": (
        "Survey the datasets, benchmarks, and evaluation methodologies used in "
        "machine-learning and generative electronic design automation (EDA) as of "
        "2025, spanning both PCB-level and chip-level design. Cover: (a) circuit / "
        "netlist / schematic datasets and benchmark suites (e.g., VerilogEval, RTLLM, "
        "MCNC/ISPD/ICCAD placement and routing benchmarks, CircuitNet, the Open "
        "Circuit Benchmark / analog topology datasets, any open KiCad/PCB corpora), "
        "(b) metrics for placement, routing, schematic generation, and HDL generation "
        "(wirelength, congestion, DRC violations, functional pass rate, "
        "synthesizability), and (c) the gaps and challenges in evaluating generative "
        "circuit/PCB design (lack of standardized, manufacturable, open PCB datasets; "
        "reproducibility concerns). For each dataset/benchmark give a full citation, a "
        "3-5 sentence description, license/availability, and its relevance to "
        "evaluating a generative pipeline for open-hardware control PCBs. Aim for "
        "~10-15 references."
    ),
    "open_hardware_eda_for_labs": (
        "Find recent (2018-2025) peer-reviewed and arXiv publications, plus notable "
        "open-source projects, on the design and automated/generative design of "
        "electronics for open-source scientific hardware and laboratory automation — "
        "the application context for a low-cost, modular, microcontroller-driven "
        "multi-powder dosing device. Cover: (a) open-hardware electronics design "
        "practice and reproducibility for scientific instruments (e.g., OpenFlexure, "
        "Jubilee, Opentrons, Poseidon/pumps, GOSH community, Journal of Open Hardware "
        "/ HardwareX norms), (b) modular and expandable motor/sensor control "
        "electronics (stepper and DC-motor driver boards, multiplexed I/O, load-cell "
        "/ HX711 front-ends, CAN/I2C/SPI expansion) and design-for-manufacture for "
        "low-cost assembly, and (c) any application of generative or automated EDA to "
        "such instruments. For each source give: full citation, 3-5 sentence summary, "
        "and explicit relevance to designing manufacturable, easily-replicated control "
        "PCBs for a multi-channel powder doser. Identify the gap: how mature is "
        "generative/automated electrical design for open scientific hardware, and what "
        "remains manual? Aim for ~10-15 references."
    ),
}

TAG = "powder-doser-grant"
PILLAR_TAG = "electrical-pcb"


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
            "tags": [TAG, PILLAR_TAG, key],
        }
        for key, q in QUERIES.items()
    ]
    print(f"Dispatching {len(tasks)} LITERATURE_HIGH tasks...", flush=True)
    results = client.run_tasks_until_done(
        tasks, verbose=True, progress_bar=False, timeout=3600
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

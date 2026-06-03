#!/usr/bin/env python3
"""Edison Scientific ANALYSIS runner that turns the generative electrical/PCB
literature pillar (notes ``07``-``13`` / ``edison_artifacts/*.answer.md``) into
concrete, powder-doser-specific implementation recommendations.

This answers the review request from @lbwinters on PR #76
(https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4615501821):

    "From your research, it seems there are several different approaches, based on
    differing systems, and requiring different amounts of initial training and
    data. For our work with the powder doser, which approaches do you find most
    feasible for use? Additionally, analyze whether these approaches can be
    created inside of our GitHub environment. Based on your logic, suggest several
    different recommendations of implementations that Copilot could best use to
    draft the PCB design for the powder doser. For each of these recommendations
    include the pros and cons of the approach, potential limitations, and
    necessary next steps to create the workflow."

Unlike the ``LITERATURE_HIGH`` runners in this folder (``edison_run.py``,
``edison_run_electrical_pcb.py``), this uses ``JobNames.ANALYSIS`` (the
data-analysis "crow"), which reasons over *uploaded files* rather than searching
the open literature. Per the official Edison docs on file management
(https://docs.edisonscientific.com/edison-client/file-management), a *directory*
of inputs must be uploaded as a single zipped **collection** via
``store_file_content(..., as_collection=True)``; uploading the files
individually causes the analysis task to fail silently. The returned
``data_entry:<uuid>`` URI is then passed to ``create_task``/
``run_tasks_until_done`` via the ``files=`` argument.

The "prior artifacts" uploaded here are the seven rendered literature reviews
plus their standalone reference lists -- i.e. every ``*.answer.md`` and
``*.references.md`` under ``edison_artifacts/`` (the verbatim notes ``07``-``13``
are byte-identical copies of the ``*.answer.md`` files). The multi-megabyte
``*.task.json`` raw agent-state dumps are intentionally excluded: they duplicate
the answer/reference text and would only add parsing noise for the analysis
agent.

Outputs are written next to the literature artifacts in ``edison_artifacts/``:

* ``<key>.task.json``  -- full ``TaskResponse.model_dump()`` from Edison.
* ``<key>.answer.md``  -- the rendered analysis answer (``formatted_answer`` /
  ``answer``).
* ``<key>.notebook.ipynb`` -- the analysis notebook, when Edison returns one.

Run with ``EDISON_API_KEY`` set in the environment::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_pcb_recommendation_analysis.py
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

KEY = "pcb_recommendations_for_powder_doser"
TAG = "powder-doser-grant"
PILLAR_TAG = "electrical-pcb"

# Repository context handed to the analysis agent so its recommendations are
# grounded in how this project actually builds and renders hardware.
CONTEXT = (
    "Context about the target project (the 'powder doser'). It is a low-cost, "
    "open-hardware, modular, multi-powder dosing device for autonomous discovery "
    "of additively-manufactured aerospace alloys. Its control electronics are "
    "authored as KiCad 7 projects driven by a Raspberry Pi Pico W / RP2040 "
    "microcontroller running CircuitPython, controlling stepper drivers, "
    "vibration motors, solenoids, servos, and HX711 load-cell feedback, with an "
    "emphasis on easily expandable I/O to many modules. The whole project is "
    "developed on GitHub and is built/rendered headlessly in CI and in the "
    "GitHub Copilot coding-agent sandbox (Ubuntu): existing workflows already run "
    "headless KiCad 7 (apt kicad/kicad-symbols/kicad-footprints, kicad-cli sch/"
    "pcb export svg/pdf, rsvg-convert) and headless code-CAD (CadQuery/OpenSCAD "
    "under xvfb). Mechanical parts are already authored 'as code' (parametric "
    "CadQuery/OpenSCAD committed to git and rendered in CI). The electrical work "
    "should follow the same reproducible, version-controlled, CI-rendered, "
    "Copilot-drivable philosophy. Sandbox constraints: no interactive GUI, only "
    "command-line/Python tooling, network access to package registries, and an "
    "LLM coding agent (Copilot) that edits text files and runs shell commands."
)

QUERY = (
    "You are given, as uploaded files, a set of literature/landscape reviews on "
    "generative, AI-assisted, and code-based electronic design automation (EDA) "
    "and PCB design (files named *.answer.md with companion *.references.md). "
    "Read them as your evidence base and synthesize an actionable engineering "
    "recommendation; cite the uploaded reviews (and the specific tools/papers "
    "they reference) where relevant.\n\n"
    + CONTEXT
    + "\n\nDeliver the following:\n"
    "1. A concise comparison of the distinct approaches surfaced in the reviews "
    "(e.g., GUI suites with AI features; AI-native/generative EDA SaaS such as "
    "Flux.ai, JITX, Quilter, DeepPCB, Celus; design-as-code frameworks such as "
    "atopile, tscircuit, SKiDL, Horizon EDA, KiCad Python/IPC + kicad-cli; and "
    "research-grade LLM/ML schematic-synthesis and placement/routing methods), "
    "organized by how much up-front training data or model training each "
    "requires, and by how scriptable/version-controllable it is.\n"
    "2. For our work with the powder doser specifically, which approaches you "
    "find MOST FEASIBLE to use, and why.\n"
    "3. An explicit analysis of whether each feasible approach can be created and "
    "run INSIDE our GitHub environment (headless CI / Copilot coding-agent "
    "sandbox, no GUI, version-controlled text files, no large in-house model "
    "training), calling out which are blocked by closed-source SaaS, GUI-only "
    "workflows, login/credentials, or compute/training requirements.\n"
    "4. Several concrete, ranked RECOMMENDATIONS of implementations that the "
    "GitHub Copilot coding agent could best use to draft the PCB design for the "
    "powder doser. For EACH recommendation give: (a) what it is and the concrete "
    "workflow, (b) pros, (c) cons, (d) potential limitations, and (e) the "
    "necessary next steps to stand up the workflow in this repository (tools to "
    "install, files/CI to add, and how renders/DRC/Gerbers/BOM would be produced "
    "and committed). Prefer open-source, scriptable, CI-friendly options that fit "
    "the existing headless-KiCad + design-as-code conventions, and be honest "
    "about where a human-in-the-loop or a GUI step is still required."
)


def main() -> None:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        raise SystemExit(
            "EDISON_API_KEY is not set. Export it before running this script."
        )

    art_dir = Path(__file__).parent / "edison_artifacts"
    if not art_dir.is_dir():
        raise SystemExit(f"Artifacts directory not found: {art_dir}")

    inputs = sorted(art_dir.glob("*.answer.md")) + sorted(
        art_dir.glob("*.references.md")
    )
    if not inputs:
        raise SystemExit(f"No *.answer.md / *.references.md inputs found in {art_dir}")

    client = EdisonClient(api_key=api_key)

    # Stage the prior artifacts into a clean directory and upload the whole thing
    # as a single zipped collection (required for Edison Analysis directory
    # inputs -- uploading files individually fails silently).
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "powder_doser_eda_literature"
        stage.mkdir()
        for src in inputs:
            shutil.copy2(src, stage / src.name)
        print(f"Staged {len(inputs)} prior artifacts into {stage}", flush=True)

        upload = client.store_file_content(
            name="powder-doser generative EDA/PCB literature reviews (07-13)",
            file_path=stage,
            description=(
                "Rendered Edison LITERATURE_HIGH answers and reference lists for "
                "the generative electrical/PCB-design pillar of the powder-doser "
                "grant background (PR #76). Evidence base for a powder-doser PCB "
                "implementation recommendation."
            ),
            as_collection=True,
            tags=[TAG, PILLAR_TAG, "analysis-input"],
        )
        file_uri = f"data_entry:{upload.data_storage.id}"
        print(f"Uploaded collection -> {file_uri}", flush=True)

        task = TaskRequest(
            name=JobNames.ANALYSIS,
            query=QUERY,
            tags=[TAG, PILLAR_TAG, KEY],
        )
        print("Dispatching ANALYSIS task (this can take a while)...", flush=True)
        results = client.run_tasks_until_done(
            task, verbose=True, progress_bar=False, timeout=5400, files=[file_uri]
        )

    result = results[0]
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)

    out_dir = art_dir
    (out_dir / f"{KEY}.task.json").write_text(json.dumps(data, default=str, indent=2))

    formatted = _extract_answer(data)
    (out_dir / f"{KEY}.answer.md").write_text(formatted)

    notebook = _extract_notebook(data)
    if notebook:
        (out_dir / f"{KEY}.notebook.ipynb").write_text(notebook)

    print(
        f"  {KEY}: status={data.get('status')} answer_chars={len(formatted)} "
        f"notebook={'yes' if notebook else 'no'}",
        flush=True,
    )
    print(f"Wrote artifacts to {out_dir}", flush=True)


def _extract_answer(data: dict) -> str:
    """Pull the rendered answer text out of a TaskResponse dump.

    Handles the top-level ``formatted_answer``/``answer`` fields as well as the
    nested ``environment_frame`` locations used by the analysis ("Finch") and
    literature job types.
    """
    for key in ("formatted_answer", "answer"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val
    try:
        state = data["environment_frame"]["state"]["state"]
    except (KeyError, TypeError):
        return ""
    # Analysis jobs expose the submitted answer directly as a string.
    direct = state.get("answer")
    if isinstance(direct, str) and direct.strip():
        return direct
    # Literature jobs nest it under response.answer.
    answer = state.get("response", {}).get("answer", {})
    if isinstance(answer, dict):
        return answer.get("formatted_answer") or answer.get("answer") or ""
    if isinstance(answer, str):
        return answer
    return ""


def _extract_notebook(data: dict) -> str:
    """Return the analysis notebook as a JSON string if Edison produced one."""
    nb = data.get("notebook")
    if nb is None:
        try:
            state = data["environment_frame"]["state"]["state"]
            nb = state.get("nb_state")
        except (KeyError, TypeError, AttributeError):
            nb = None
    if nb is None:
        try:
            nb = data["environment_frame"]["state"]["info"].get("notebook")
        except (KeyError, TypeError, AttributeError):
            nb = None
    if nb is None:
        return ""
    if isinstance(nb, str):
        return nb
    return json.dumps(nb, default=str, indent=2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Edison Scientific ANALYSIS runner that addresses @lbwinters' Quilter.ai
review of the generated starter-board upload trio (PR #76 comment 4723827215).

After uploading the generated KiCad files to Quilter.ai, @lbwinters reported
four issues / requests, transcribed *verbatim* below in ``LUKE_INSTRUCTIONS``:

  1. a "pin count mismatch detected" parsing warning between the schematic and
     the board (examine the files + Quilter docs and fix it),
  2. the uploaded board is the same size as the (schematic-derived) placed
     board, wasting space -- analyse the *best board size* for Quilter to
     auto-place these components onto,
  3. a stackup recommendation (they have been using JLCPCB 2-layer 6mil/6mil),
     plus a "no ground layer is defined" warning to address, and
  4. (prepare for, no action yet) verifying the per-stackup datasheet values.

This uploads the generated upload trio (placed + unplaced ``.kicad_pcb`` /
``.kicad_sch`` / ``.kicad_pro``), the headless generator, the machine-readable
summary, the board previews, and the Quilter capability note as a single zipped
**collection** (``store_file_content(..., as_collection=True)``, per the
official Edison file-management docs
https://docs.edisonscientific.com/edison-client/file-management) and asks the
data-analysis agent to work through all four points with concrete, headlessly
implementable fixes for ``build_starter_board.py``.

Run with ``EDISON_API_KEY`` set in the environment::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_quilter_review_analysis.py
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

KEY = "quilter_review_for_powder_doser"
TAG = "powder-doser-grant"
PILLAR_TAG = "electrical-pcb"

# Files uploaded for review. Both upload trios (placed + unplaced), the headless
# generator, its machine-readable summary, the board previews, and the Quilter
# capability note. The schematic-render SVGs are large; the board SVGs are the
# ones that show the placement under review.
STARTER = Path(__file__).parent / "starter_board"
BACKGROUND = Path(__file__).parent
UPLOADS = [
    STARTER / "build_starter_board.py",
    STARTER / "starter_board_summary.json",
    STARTER / "test_module_starter.kicad_pcb",
    STARTER / "test_module_starter.kicad_sch",
    STARTER / "test_module_starter.kicad_pro",
    STARTER / "test_module_starter.svg",
    STARTER / "test_module_unplaced.kicad_pcb",
    STARTER / "test_module_unplaced.kicad_sch",
    STARTER / "test_module_unplaced.kicad_pro",
    STARTER / "test_module_unplaced.svg",
    BACKGROUND / "16-quilter-ai-pcb-layout.md",
    BACKGROUND / "21-starter-board-for-quilter-deeppcb.md",
]

# @lbwinters' review, transcribed verbatim from PR #76 comment 4723827215.
LUKE_INSTRUCTIONS = (
    "1) After uploading each of the previous kicad files into Quilter.ai, I've "
    "gotten a parsing warning \"There are component mismatches between "
    "schematics and board: Pin count mismatch detected. Quilter will continue, "
    "but placement quality may be affected. Examine our files and any "
    "corresponding quilter documentation that would have resulted in this "
    "error. If changes must be made, do it, retest until it's perfect, and then "
    "report back.\n\n"
    "2) Quilter places the components onto whatever size board is uploaded. In "
    "the unplaced files, the board is the same size as the board you've created "
    "by basically copying and pasting the schematic layout onto the board. This "
    "means that there is still a lot of wasted space. Can you run an analysis on "
    "the best board size for quilter to place these components onto? We want to "
    "maximize space while preserving the necessary area for the components as "
    "well as spacing between components and tracings.\n\n"
    "3) Quilter requests the type of stackup we would like to use. Up until now, "
    "I have been using the JLCPCB 2 Layer 6mil/6mil. Based on our requests and "
    "components is this the optimal stickup of layers and spacing? Do some "
    "research and make a recommendation. Additionally, after choosing the "
    "previously mentioned stickup, I get a warning message: \"No ground layer "
    "is defined in this stickup. Signal integrity may be reduced without a "
    "dedicated ground plane\"\n\n"
    "4) After choosing the stickup, quilter presents a data sheet of values that "
    "should be verified as correct before moving on. I am not uploading that "
    "right now, but be prepared after giving us the optimal stickup, for me to "
    "give you that datasheet and ask for it to be verified before we begin the "
    "run."
)

CONTEXT = (
    "Context about the target project (the 'powder doser'). It is a low-cost, "
    "open-hardware, modular, multi-powder dosing device for autonomous discovery "
    "of additively-manufactured aerospace alloys. Its control electronics are a "
    "KiCad 7 project driven by a Raspberry Pi Pico W / RP2040 running "
    "MicroPython, controlling a Pololu Tic T500 stepper, a DRV8871 solenoid "
    "driver, a DRV2605L + ERM vibration motor, a servo, a Pololu shunt "
    "regulator, a Pololu D24V22F5 5 V buck regulator off a 12 V barrel jack, and "
    "a Waveshare Pico-2CH-RS232 module (SP3232EEN) for an A&D HR-100A balance "
    "(gravimetric feedback). The board is generated entirely by the uploaded "
    "headless Python script build_starter_board.py (pure-Python kiutils, no "
    "KiCad install required) and is meant as the router-ready input for "
    "autonomous PCB placement/routing tools (Quilter, DeepPCB). The generator "
    "emits two upload trios: test_module_starter (a pre-placed compact board) "
    "and test_module_unplaced (the same parts staged outside an identical empty "
    "board outline so Quilter/DeepPCB can be tested on auto-placement). Both "
    "carry the full 24-net ratsnest unrouted. The current board outline is "
    "~140.6 x 82.0 mm with 15 footprints / 137 pads. The schematic symbol pin "
    "count equals the board footprint pad count for every reference designator, "
    "and kicad-cli's netlist exporter reports zero unconnected pins; despite "
    "this Quilter still reports a 'Pin count mismatch'. The whole project is "
    "developed on GitHub and built/rendered headlessly in CI and the GitHub "
    "Copilot coding-agent sandbox (Ubuntu): no interactive GUI, only "
    "command-line/Python tooling, and the fix must be implementable in the "
    "uploaded build_starter_board.py and committed to git."
)

QUERY = (
    "You are given, as uploaded files, a headless KiCad-7 starter board for the "
    "powder doser: the generator (build_starter_board.py), both upload trios "
    "(test_module_starter[.kicad_pcb/.kicad_sch/.kicad_pro] = pre-placed, and "
    "test_module_unplaced[...] = parts staged outside an empty board outline), a "
    "JSON summary (starter_board_summary.json with per-part body sizes, pad/pin "
    "counts and the board outline), SVG previews of both boards, and two "
    "background notes on Quilter.ai's capabilities (16, 21).\n\n"
    + CONTEXT
    + "\n\nA collaborator uploaded these exact files to Quilter.ai and reported "
    "the following (verbatim):\n\n"
    + LUKE_INSTRUCTIONS
    + "\n\nWork through each numbered point and deliver:\n"
    "1. PIN COUNT MISMATCH. Diagnose the most likely cause of Quilter's "
    "'component mismatches between schematics and board: Pin count mismatch "
    "detected' given that our own checks show schematic pin count == board pad "
    "count for every reference and kicad-cli reports zero unconnected pins. "
    "Consider how Quilter associates a schematic symbol with a board footprint "
    "(reference vs shared path/tstamp UUID), whether it re-resolves footprints "
    "from its own KiCad libraries (so our real library ids like "
    "Connector_BarrelJack:BarrelJack_Horizontal or "
    "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm may resolve to a different pad "
    "count/numbering than our embedded copy), the parts with many no-connect "
    "pads (the 40-pin Pi Pico W and the 40-pin RS-232 receptacle wired on only "
    "15 / 6 pins), the missing schematic<->board linkage (the board footprints "
    "carry no (path ...) back to the schematic symbol UUIDs and no (attr ...)), "
    "and pad-number ordering. Give the single most probable root cause plus a "
    "ranked list of the others, and for each a concrete, headlessly "
    "implementable change to build_starter_board.py to eliminate it. State how "
    "to verify the fix without the Quilter GUI.\n"
    "2. BEST BOARD SIZE. Recommend the board outline size (and aspect ratio) we "
    "should hand Quilter for auto-placement of this exact part set (15 "
    "footprints, the sizes are in the summary). Quilter places onto whatever "
    "outline is uploaded, so the unplaced board should be sized to give it room "
    "to place + route without wasting copper. Give a target area and "
    "width x height (mm), the reasoning (sum of component areas, a placement "
    "utilisation factor, room for 2-layer routing and the EDGE_MARGIN), how it "
    "compares to the current ~140.6 x 82.0 mm, and exactly how to compute the "
    "outline in build_board()/_pack_positions for the unplaced variant.\n"
    "3. STACKUP. Evaluate JLCPCB 2-layer 6mil/6mil for this board (mixed-signal: "
    "+12 V switching motor/solenoid power, 3V3/5V logic, I2C, two UARTs, RS-232) "
    "and either endorse it or recommend a better option (e.g. 4-layer with a "
    "dedicated ground plane). Address Quilter's warning 'No ground layer is "
    "defined in this stickup. Signal integrity may be reduced without a "
    "dedicated ground plane': explain the signal-integrity trade-off for THIS "
    "board, when 2-layer-with-ground-pour is acceptable vs when a 4-layer "
    "Sig/GND/PWR/Sig stackup is worth it, and give a concrete recommendation "
    "with the trace-width / clearance / copper-weight implications and how a "
    "ground plane / pour would be expressed for Quilter and in our net classes.\n"
    "4. DATASHEET VERIFICATION (prep only). Briefly outline what per-stackup "
    "values Quilter will present after the stackup is chosen (layer thicknesses, "
    "copper weights, dielectric constant/Dk, prepreg/core, min track/space, "
    "impedance targets) and what we should check each against, so we are ready "
    "to verify that datasheet in a follow-up.\n\n"
    "Throughout, prefer advice that can be implemented headlessly in the Python "
    "generator and committed to git; be explicit about anything that still needs "
    "a human-in-the-loop step."
)


def main() -> None:
    api_key = os.environ.get("EDISON_API_KEY") or os.environ.get(
        "EDISON_PLATFORM_API_KEY"
    )
    if not api_key:
        raise SystemExit(
            "EDISON_API_KEY is not set. Export it before running this script."
        )

    missing = [p.name for p in UPLOADS if not p.is_file()]
    if missing:
        raise SystemExit(
            f"Missing inputs {missing}; run build_starter_board.py first."
        )

    client = EdisonClient(api_key=api_key)

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "powder_doser_quilter_review"
        stage.mkdir()
        for src in UPLOADS:
            shutil.copy2(src, stage / src.name)
        print(f"Staged {len(UPLOADS)} files into {stage}", flush=True)

        upload = client.store_file_content(
            name="powder-doser starter board + Quilter review inputs",
            file_path=stage,
            description=(
                "Headless KiCad-7 starter board upload trios (placed + unplaced) "
                "plus generator, summary, previews and Quilter notes, for a "
                "review of @lbwinters' Quilter.ai findings (PR #76 comment "
                "4723827215): pin-count mismatch, best board size, and stackup."
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

    out_dir = Path(__file__).parent / "edison_artifacts"
    out_dir.mkdir(exist_ok=True)
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
    """Pull the rendered answer text out of a TaskResponse dump."""
    for key in ("formatted_answer", "answer"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val
    try:
        state = data["environment_frame"]["state"]["state"]
    except (KeyError, TypeError):
        return ""
    direct = state.get("answer")
    if isinstance(direct, str) and direct.strip():
        return direct
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

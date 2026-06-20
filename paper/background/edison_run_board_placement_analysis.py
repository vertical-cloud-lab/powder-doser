#!/usr/bin/env python3
"""Edison Scientific ANALYSIS runner that reviews the generated starter-board
*placement* and asks for concrete ways to make it more compact / manufacturable.

This answers the review request from @sgbaird on PR #76
(https://github.com/vertical-cloud-lab/powder-doser/pull/76) and the DeepPCB
trial feedback from @lbwinters on issue #94
(https://github.com/vertical-cloud-lab/powder-doser/issues/94#issuecomment-4665660451):
the first board uploaded to DeepPCB came out *"still very spaced out"* because
the earlier ``build_starter_board.py`` reused the schematic-sheet anchor
coordinates as the board floorplan (a ~279x199 mm board for 14 small breakouts).
``build_starter_board.py`` now compact-packs the real component bodies into a
near-square grid (``_pack_positions``), shrinking the outline to ~82x113 mm; this
runner uploads the regenerated board files and asks the analysis agent to sanity
check the placement and suggest further improvements.

Like ``edison_run_pcb_recommendation_analysis.py`` this uses
``JobNames.ANALYSIS`` (the data-analysis "crow"), which reasons over *uploaded
files*. Per the official Edison file-management docs
(https://docs.edisonscientific.com/edison-client/file-management), a *directory*
of inputs must be uploaded as a single zipped **collection** via
``store_file_content(..., as_collection=True)`` -- uploading the files
individually fails silently. The returned ``data_entry:<uuid>`` URI is passed to
``run_tasks_until_done`` via ``files=``.

Run with ``EDISON_API_KEY`` set in the environment::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_board_placement_analysis.py
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

KEY = "board_placement_review_for_powder_doser"
TAG = "powder-doser-grant"
PILLAR_TAG = "electrical-pcb"

# Files uploaded for review: the generated Quilter/DeepPCB upload trio plus the
# headless generator and its machine-readable summary. The large preview PNGs
# are skipped (they add upload weight without adding analyzable text/geometry).
UPLOAD_NAMES = [
    "build_starter_board.py",
    "test_module_starter.kicad_pcb",
    "test_module_starter.kicad_sch",
    "test_module_starter.kicad_pro",
    "starter_board_summary.json",
    "test_module_starter.svg",
]

CONTEXT = (
    "Context about the target project (the 'powder doser'). It is a low-cost, "
    "open-hardware, modular, multi-powder dosing device for autonomous discovery "
    "of additively-manufactured aerospace alloys. Its control electronics are a "
    "KiCad 7 project driven by a Raspberry Pi Pico W / RP2040 running "
    "MicroPython, controlling a Pololu Tic T500 stepper, a DRV8871 solenoid "
    "driver, a DRV2605L + ERM vibration motor, a servo, a shunt regulator, and a "
    "D24V22F5 buck regulator, with an HX711-style load cell elsewhere in the "
    "system. The whole project is developed on GitHub and built/rendered "
    "headlessly in CI and in the GitHub Copilot coding-agent sandbox (Ubuntu): "
    "no interactive GUI, only command-line/Python tooling. The starter board is "
    "generated entirely by the uploaded headless Python script "
    "build_starter_board.py (pure-Python kiutils, no KiCad install required) and "
    "is meant as the router-ready input for autonomous PCB placement/routing "
    "tools (DeepPCB, Quilter). Each part's real body outline, courtyard, and 3-D "
    "model come from committed vendor design files; pads are still a simplified "
    "0.1-inch header inside each real body (a known proxy caveat). Connectivity "
    "is expressed with global net labels in the schematic; the board carries the "
    "full 20-net ratsnest unrouted (the routers do placement + routing)."
)

QUERY = (
    "You are given, as uploaded files, a headless KiCad-7 starter board for the "
    "powder doser: the generator script (build_starter_board.py), the generated "
    "board (.kicad_pcb), schematic (.kicad_sch), project (.kicad_pro), a JSON "
    "summary (starter_board_summary.json with the per-part body sizes and the "
    "board outline), and an SVG preview of the board.\n\n"
    + CONTEXT
    + "\n\nBackground on the change being reviewed: an earlier version reused the "
    "schematic-sheet anchor coordinates as the board floorplan, which left the 14 "
    "small breakouts ridiculously spaced out (~279x199 mm). The generator now "
    "compact-packs the real component courtyards into a near-square grid via a "
    "shelf-packing function (_pack_positions: left-to-right rows wrapping at a "
    "width derived from sqrt(total courtyard area), with a fixed 1.5 mm gap "
    "between courtyards), shrinking the board to ~82x113 mm while a pairwise "
    "_assert_no_overlap guard keeps it DRC-clean.\n\n"
    "Deliver the following:\n"
    "1. A sanity check of the new compact placement: is ~82x113 mm reasonable for "
    "this part set, are there obvious wasted-area or routability problems with a "
    "pure area-based shelf pack, and is the per-courtyard 1.5 mm gap sensible for "
    "a hand-routable / auto-routable 2-layer board with these connectors?\n"
    "2. Concrete, ranked suggestions to improve the *initial* placement quality "
    "for an autonomous router (DeepPCB/Quilter), e.g. grouping by power domain "
    "(+12V/+5V/+3V3/GND), keeping decoupling caps next to their regulators/loads, "
    "edge-placing connectors/off-board actuator headers, separating the "
    "motor/solenoid power section from the logic/I2C section, and choosing board "
    "aspect ratio. For each suggestion give the rationale and roughly how to "
    "implement it in the existing _pack_positions / NETLIST data structures.\n"
    "3. Any correctness or manufacturability red flags you can see from the "
    "uploaded geometry (pad/courtyard sizing, the proxy 0.1-inch header pads, the "
    "board outline margin, net-class/track-width choices), and the minimal next "
    "steps to make this board a credible autonomous-routing input. Prefer "
    "advice that can be implemented headlessly in the Python generator and "
    "committed to git; be honest about where a human-in-the-loop step remains."
)


def main() -> None:
    api_key = os.environ.get("EDISON_API_KEY") or os.environ.get(
        "EDISON_PLATFORM_API_KEY"
    )
    if not api_key:
        raise SystemExit(
            "EDISON_API_KEY is not set. Export it before running this script."
        )

    board_dir = Path(__file__).parent / "starter_board"
    if not board_dir.is_dir():
        raise SystemExit(f"starter_board directory not found: {board_dir}")

    inputs = [board_dir / name for name in UPLOAD_NAMES]
    missing = [p.name for p in inputs if not p.is_file()]
    if missing:
        raise SystemExit(
            f"Missing starter-board inputs {missing}; run build_starter_board.py first."
        )

    client = EdisonClient(api_key=api_key)

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "powder_doser_starter_board"
        stage.mkdir()
        for src in inputs:
            shutil.copy2(src, stage / src.name)
        print(f"Staged {len(inputs)} starter-board files into {stage}", flush=True)

        upload = client.store_file_content(
            name="powder-doser generated starter board (compact placement)",
            file_path=stage,
            description=(
                "Headless KiCad-7 starter board for the powder doser (generator + "
                "board/schematic/project + summary + preview) for an autonomous "
                "placement/routing review (PR #76, issue #94)."
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

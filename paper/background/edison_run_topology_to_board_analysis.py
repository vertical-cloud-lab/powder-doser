#!/usr/bin/env python3
"""Edison Scientific ``ANALYSIS`` runner that asks the same "intermediate step"
question as ``edison_run_topology_to_board.py`` but grounded in THIS repository's
actual control-electronics schematic: it uploads the powder-doser test-module
**KiCad** project (schematic + symbols + project + the build script + module
README) and asks which generative-AI tools/workflow can take a topology + a
component list + requirements and produce a basic *starter board* (footprints +
preliminary outline/floorplan) in KiCad ready to feed into Quilter / DeepPCB --
and whether any of that can run headlessly inside the GitHub / Copilot CI sandbox.

This answers @sgbaird's request on PR #76
(https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654166992):
"Also send an edison analysis query with KiCad files from this repository
uploaded, asking something similar."

Per the official Edison file-management docs
(https://docs.edisonscientific.com/edison-client/file-management) a *directory*
of inputs must be uploaded as a single zipped **collection** via
``store_file_content(..., as_collection=True)``; uploading the files individually
causes the analysis task to fail silently. The returned ``data_entry:<uuid>`` URI
is passed to ``run_tasks_until_done`` via the ``files=`` argument.

The KiCad inputs live on the test-module electronics branch (PR #61), not on this
literature branch, so for a self-contained, reproducible run this script will use
a local ``hardware/test-module/kicad`` directory if present, and otherwise
download the files from their pinned commit on GitHub. Outputs land in
``paper/background/edison_artifacts/``:

* ``<key>.task.json``  -- full ``TaskResponse.model_dump()`` from Edison.
* ``<key>.answer.md``  -- the rendered analysis answer.
* ``<key>.notebook.ipynb`` -- the analysis notebook, when Edison returns one.

Run with ``EDISON_API_KEY`` (or ``EDISON_PLATFORM_API_KEY``) set::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_topology_to_board_analysis.py
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

KEY = "topology_to_board_for_powder_doser"
TAG = "powder-doser-grant"
PILLAR_TAG = "electrical-pcb"

# Pinned commit of PR #61 (copilot/set-up-test-module-electronics) so the upload
# is reproducible even though the KiCad project is not on this branch.
KICAD_PIN = "147e5055fb6ec935af164a88e447ed1748f370df"
KICAD_FILES = [
    "hardware/test-module/kicad/test_module.kicad_sch",
    "hardware/test-module/kicad/test_module.kicad_pro",
    "hardware/test-module/kicad/test_module.kicad_sym",
    "hardware/test-module/kicad/sym-lib-table",
    "hardware/test-module/kicad/generate.py",
    "hardware/test-module/README.md",
]
RAW_BASE = "https://raw.githubusercontent.com/vertical-cloud-lab/powder-doser"

CONTEXT = (
    "The uploaded files are the real KiCad 7 control-electronics project for the "
    "'powder doser' -- a low-cost, open-hardware, modular multi-powder dosing "
    "device for autonomous discovery of additively-manufactured aerospace alloys. "
    "This single-channel bench/test module is driven by a Raspberry Pi Pico W "
    "(RP2040) and is a mixed-signal motor + sensor board: a 12 V->5 V buck "
    "regulator (Pololu D24V22F5), a Pololu Tic T500 stepper controller driving a "
    "NEMA-11 auger stepper (with a shunt regulator to clamp back-EMF), a DRV8871 "
    "driving a tap solenoid, a DRV2605L haptic driver + ERM vibration motor, a "
    "hobby servo for the dispensing-angle axis, an HX711/load-cell front end in "
    "the broader design, and bulk decoupling. The schematic (test_module.kicad_sch "
    "+ test_module.kicad_sym + test_module.kicad_pro) is authored 'as code' by "
    "generate.py and rendered headlessly in CI (apt kicad + kicad-cli export). The "
    "whole project is developed on GitHub and must be buildable/renderable in a "
    "headless Ubuntu CI / GitHub Copilot coding-agent sandbox: no interactive GUI, "
    "only command-line/Python tooling, package-registry network access, and an LLM "
    "coding agent that edits text files and runs shell commands. There is as yet "
    "NO PCB layout (.kicad_pcb) -- only the schematic/netlist exists."
)

QUERY = (
    "You are given this project's actual KiCad schematic project as uploaded "
    "files (test_module.kicad_sch is the schematic/netlist; test_module.kicad_sym "
    "the custom symbols; generate.py the script that emits the schematic; "
    "README.md the bill of materials and wiring rationale). Read them to ground "
    "your answer in the real circuit.\n\n"
    + CONTEXT
    + "\n\nThe project's autonomous-PCB plan is: generate a circuit TOPOLOGY with "
    "an LLM/topology tool (e.g. LaMAGIC), then route the board with an autonomous "
    "placement/routing engine (Quilter or DeepPCB). The problem: those routers "
    "cannot start from a bare topology -- they need a complete starter board "
    "(schematic with footprints, a board outline, and design rules). Deliver:\n"
    "1. Given THIS schematic/netlist, characterize what is already present "
    "(components, nets, mixed-signal power/ground concerns) and exactly what is "
    "still missing to reach a router-ready 'starter board' (footprints, board "
    "outline, placement/floorplan, design rules, mounting/connector constraints).\n"
    "2. Which generative-AI / automated tools can perform this INTERMEDIATE step "
    "of turning a topology + component list + requirements into a footprinted, "
    "netlisted KiCad starter board with a preliminary outline/floorplan that "
    "Quilter or DeepPCB can ingest? Evaluate CELUS specifically (can it ingest a "
    "block diagram/topology and export native KiCad with footprints + floorplan?), "
    "plus Flux.ai, JITX, and design-as-code options (atopile, tscircuit, SKiDL, "
    "KiCad Python/IPC + kicad-cli).\n"
    "3. For EACH viable option, state explicitly whether it can run INSIDE our "
    "headless GitHub CI / Copilot coding-agent sandbox (no GUI, version-controlled "
    "text files, scriptable/API access) or whether it is blocked by GUI-only / "
    "login / closed-SaaS / training requirements.\n"
    "4. Several concrete, RANKED recommendations for how the Copilot coding agent "
    "could best produce a starter board for THIS device that then feeds Quilter or "
    "DeepPCB. For each: (a) the concrete workflow and tools, (b) pros, (c) cons, "
    "(d) limitations, and (e) the necessary next steps to stand it up in this "
    "repository (what to install, files/CI to add, how the footprints/outline/"
    "floorplan/netlist would be produced and committed). Be honest about where a "
    "human-in-the-loop or GUI step is still required, especially for the "
    "mixed-signal motor + load-cell power/ground partitioning."
)


def _api_key() -> str:
    for name in ("EDISON_API_KEY", "EDISON_PLATFORM_API_KEY"):
        val = os.environ.get(name)
        if val:
            return val
    raise SystemExit(
        "Set EDISON_API_KEY (or EDISON_PLATFORM_API_KEY) before running this script."
    )


def _stage_kicad(stage: Path) -> int:
    """Copy the test-module KiCad inputs into ``stage``.

    Prefer a local checkout (``<repo>/hardware/test-module/...``); fall back to
    downloading each file from its pinned commit on GitHub raw.
    """
    repo_root = Path(__file__).resolve().parents[2]
    staged = 0
    for rel in KICAD_FILES:
        dest = stage / Path(rel).name
        local = repo_root / rel
        if local.is_file():
            shutil.copy2(local, dest)
            staged += 1
            continue
        url = f"{RAW_BASE}/{KICAD_PIN}/{rel}"
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310
                dest.write_bytes(resp.read())
            staged += 1
        except OSError as exc:  # network/host failure
            print(f"  WARNING: could not fetch {rel}: {exc}", flush=True)
    return staged


def main() -> None:
    api_key = _api_key()
    out_dir = Path(__file__).parent / "edison_artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = EdisonClient(api_key=api_key)

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "powder_doser_kicad_test_module"
        stage.mkdir()
        n = _stage_kicad(stage)
        if n == 0:
            raise SystemExit("No KiCad inputs could be staged (local or remote).")
        print(f"Staged {n} KiCad input files into {stage}", flush=True)

        upload = client.store_file_content(
            name="powder-doser test-module KiCad project (schematic/netlist)",
            file_path=stage,
            description=(
                "Real KiCad 7 schematic project for the powder-doser single-channel "
                "test module (RP2040 Pico W + Tic T500 stepper + DRV8871 solenoid + "
                "DRV2605L/ERM + servo + buck/shunt regulators). Evidence base for an "
                "analysis of the topology->starter-board intermediate step (PR #76)."
            ),
            as_collection=True,
            tags=[TAG, PILLAR_TAG, "analysis-input", "kicad"],
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
    nb = data.get("notebook")
    if nb is None:
        try:
            nb = data["environment_frame"]["state"]["state"].get("nb_state")
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

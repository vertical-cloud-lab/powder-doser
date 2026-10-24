#!/usr/bin/env python3
"""Dispatch (without waiting) an Edison ANALYSIS task reviewing the newly
added ten-powder validation plan and three-phase dosing protocol in the base
manuscript (PR #97), benchmarked against the Digital Discovery digital-pipette
papers whose ISO 8655-6 gravimetric evaluation the plan is modelled on.

Inputs (zipped collection from ./inputs): main.pdf, si.pdf, both digital
pipette PDFs, and powder_plan_context.md. The task id is written to
analysis_task_ids.json for a later fetch.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
TAG = "powder-doser-powder-plan-analysis"

QUERY = """\
You are given the current draft of an open-hardware Digital Discovery
manuscript (main.pdf, with SI si.pdf) describing a low-cost 3D-printed
single-channel powder doser, plus the two published Digital Discovery
"digital pipette" papers (v1, 2023, DOI 10.1039/d3dd00115f; v2 Commit, 2026,
DOI 10.1039/d5dd00336a) and a context note (powder_plan_context.md).

The manuscript has just been revised to add: (1) a planned ten-powder
validation set (Table 1: NaCl, calcium lactate, sodium alginate, xanthan gum,
white and brown rice flour, AlSi10Mg, fine ~45 um and coarse 100-200 mesh
silicon, fumed-silica glidant); (2) a three-phase closed-loop dosing
procedure (bulk -> fine -> tap-to-target) in the Experimental section; and
(3) an ISO 8655-inspired gravimetric validation protocol (n>=10 replicates at
5 g / 500 mg / 50 mg / 20 mg targets; systematic error, CV, overshoot rate,
dose time; pre-registered acceptance limits) explicitly modelled on the
digital-pipette papers' evaluation.

Please analyze:
1. Internal consistency. Do the new Table 1, the Dispensing performance text,
   the Experimental protocol, the abstract, Fig. 3 and its caption, the
   Conclusions/future-work section, and the SI all tell one coherent story
   (ten powders, three phases, fixed hand-chosen parameters, optimization
   deferred)? List any contradictions, dangling references to the older
   "coarse-then-trickle" two-phase description, or figure/text mismatches.
2. Benchmarking against the digital-pipette precedent. Compare our planned
   validation protocol point-by-point with what the v1 paper (ISO 8655-6:
   test-volume ladder at 100/50/10% of nominal, n=10, systematic + random
   error vs ISO 8655-2 limits, calibration curve, viscosity sweep, human
   comparison) and the v2 Commit paper actually reported. What elements of
   their evaluation are we missing that a Digital Discovery reviewer who knows
   those papers would expect (e.g., a calibration/resolution curve analogue,
   a manual hand-weighing comparison arm, environmental controls), and what
   powder-specific elements do we add that they lacked?
3. Adequacy and defensibility of the planned metrics and ladder. Are four
   target masses x ten powders x n>=10 defensible for a hardware Full Paper?
   Is anything statistically weak (e.g., CV at 20 mg near balance noise,
   absence of an uncertainty budget), over-promised, or under-specified
   (missing environmental/humidity reporting, no stated powder
   characterization methods for PSD/density/flowability)?
4. Actionable edits. Give a ranked list of concrete, text-level fixes to the
   manuscript (section + what to change) that can be made now, before bench
   data exist. Do NOT flag the synthetic watermarked data in Fig. 3 as a
   defect; it is a deliberate placeholder pending the bench campaign.
"""


def main() -> None:
    api_key = os.environ.get("EDISON_PLATFORM_API_KEY") or os.environ.get(
        "EDISON_API_KEY"
    )
    if not api_key:
        raise SystemExit("EDISON_PLATFORM_API_KEY is not set.")

    client = EdisonClient(api_key=api_key)

    print(f"Uploading {INPUTS} as a zipped collection...", flush=True)
    stored = client.store_file_content(
        name="powder_doser_powder_plan_inputs",
        file_path=str(INPUTS),
        as_collection=True,
    )
    file_uri = f"data_entry:{stored.data_storage.id}"
    print(f"  uploaded -> {file_uri}", flush=True)

    task = {"name": JobNames.ANALYSIS, "query": QUERY, "tags": [TAG]}
    print("Dispatching ANALYSIS task (no wait)...", flush=True)
    task_id = str(client.create_task(task, files=[file_uri]))
    (HERE / "analysis_task_ids.json").write_text(
        json.dumps({"powder_plan_analysis": task_id, "inputs": file_uri}, indent=2)
    )
    print(f"dispatched task id={task_id}", flush=True)


if __name__ == "__main__":
    main()

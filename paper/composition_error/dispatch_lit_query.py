#!/usr/bin/env python3
"""Dispatch (without waiting) one standard Edison LITERATURE query on the
composition tolerances that matter when blending elemental or pre-alloyed
powders for alloy development and additive manufacturing.

Context: the base manuscript (PR #97) states that the per-dose acceptance
limits (+/-10 % of the requested mass below 100 mg, +/-5 % at or above it)
keep dosing error below one atomic percent of composition error for a typical
five-component blend. A mock reviewer asked for this to be derived or
softened. The derivation lives in paper/figures/data/composition_error.py;
this query collects literature values to put the result in context.

The task id is written to edison_task.json immediately after dispatch so the
result can be fetched later with fetch_results.py.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from edison_client import EdisonClient, JobNames

HERE = Path(__file__).resolve().parent
TAG = "powder-doser-composition-error"

QUERY = """\
We built an open-source, 3D-printed auger powder doser with closed-loop
gravimetric feedback from a 0.1 mg readability analytical balance. It doses
50 mg to 1 g (and larger) portions of elemental or pre-alloyed metal powders
(for example gas-atomized AlSi10Mg, crystalline silicon, and Al 4047 / Al-12Si)
to blend alloy feedstocks for an ultrasonic atomizer and for additive
manufacturing in an alloy-discovery workflow. Total blend batch sizes will
typically be 10 to 500 g. Our per-dose acceptance limits are +/-10 % of the
requested mass below 100 mg and +/-5 % at or above 100 mg. We want to state
how much composition error (atomic % or weight %) these limits allow and
whether that is acceptable for alloy development.

Question: What composition tolerances (in at% or wt%) are used or required
when blending elemental or pre-alloyed powders for alloy development and
additive manufacturing, and how accurately must the powders be weighed for
gram-to-hundreds-of-gram batches?

Please give quantitative values with citations (DOIs where possible) for:
1. In-situ alloying in additive manufacturing (laser powder bed fusion,
   directed energy deposition) from blended elemental or pre-alloyed powders
   (e.g. Al-Si, AlSi10Mg + Si, Al-Cu, Ti-6Al-4V, Ti-Nb, NiTi, CoCrFeMnNi,
   AlCoCrFeNi high-entropy alloys): the reported deviation between nominal
   blend composition and measured as-built composition, and how weighing
   error compares with other error sources (evaporation of Al, Mg, Mn,
   segregation, incomplete mixing or melting).
2. Combinatorial or high-throughput alloy discovery with powders (e.g.
   Moorehead et al. 2020 high-throughput synthesis of Mo-Nb-Ta-W by in-situ
   alloying in directed energy deposition; Vecchio et al. 2021 high-throughput
   rapid experimental alloy development, HT-READ; powder-blend or
   arc-melted libraries): the composition step size used (e.g. 1, 2, or
   5 at%) and the composition accuracy reported or considered acceptable.
3. Registered composition limits for AlSi10Mg and Al-Si alloys: EN AC-43000
   (EN 1706), ISO 3522, ASTM F3318 for AlSi10Mg powder bed fusion, Aluminum
   Association registrations such as A360 and 4047 (Al-12Si), and
   hypereutectic Al-Si (A390, Al-20Si, Al-50Si controlled-expansion alloys).
   What are the widths of the Si and Mg ranges in wt%, and what weighing
   accuracy does that imply when blending these alloys from powders?
4. Weighing practice for alloy batches of 1 to 500 g (arc melting,
   mechanical alloying, AM feedstock blending): typical balance readability
   and weighing tolerances reported (e.g. +/-0.1 mg, +/-1 mg, 0.01 wt%), and
   guidance from standards (e.g. USP <41> minimum weight, ISO/ASTM 52907
   feedstock specification).
5. The typical uncertainty of composition measurement by ICP-OES, XRF, and
   EDS (e.g. EDS about +/-0.5 to 1 at%), since that sets a floor on how
   precisely an as-made composition can be verified, and any published
   treatment of propagating component mass errors into at% or wt% errors.
"""


def main() -> None:
    api_key = os.environ.get("EDISON_PLATFORM_API_KEY")
    if not api_key:
        raise SystemExit("EDISON_PLATFORM_API_KEY is not set.")

    client = EdisonClient(api_key=api_key)
    task = {"name": JobNames.LITERATURE, "query": QUERY, "tags": [TAG]}
    print("Dispatching LITERATURE task (no wait)...", flush=True)
    task_id = str(client.create_task(task))
    record = {
        "composition_error_lit": task_id,
        "task_id": task_id,
        "job_name": str(JobNames.LITERATURE.value),
        "tag": TAG,
        "dispatched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "query": QUERY,
    }
    (HERE / "edison_task.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"dispatched task id={task_id}", flush=True)


if __name__ == "__main__":
    main()

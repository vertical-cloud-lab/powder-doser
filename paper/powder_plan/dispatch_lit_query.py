#!/usr/bin/env python3
"""Dispatch (without waiting) a high-effort Edison LITERATURE query on
calibration/validation methodology for low-cost gravimetric powder
micro-dosing, complementing the earlier control-theory query (issue #123)
and the mock-review ANALYSIS rounds.

Context: the base manuscript (PR #97) will report a ten-powder validation
campaign (NaCl, white/brown rice flour, xanthan gum, sodium alginate,
calcium lactate, AlSi10Mg, fine ~45 um and coarse 100-200 mesh silicon,
fumed-silica glidant) using a three-phase (bulk -> fine -> tap/settle)
gravimetric dosing procedure, with calibration reporting modelled on the
ISO 8655-6 gravimetric protocol used by the Digital Discovery digital
pipette papers (10.1039/d3dd00115f, 10.1039/d5dd00336a).

The task id is written to lit_query_task_ids.json so the result can be
fetched with ``client.get_task(task_id, verbose=True)``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

HERE = Path(__file__).resolve().parent
TAG = "powder-doser-calibration-lit"

QUERY = """\
We are building a low-cost, open-source, 3D-printed single-channel powder doser
(Archimedes auger, 25 mm OD, with solenoid tap and ERM-vibration de-bridging
assistance, servo-controlled tilt angle, and closed-loop gravimetric feedback
from a 0.1 mg analytical balance) for self-driving laboratories, targeting
20 mg - 5 g doses. Dosing uses a three-phase procedure: (1) bulk feed by
continuous auger rotation at a steep tilt angle, (2) fine feed by small
incremental rotations with stabilized mass readings, and (3) terminal
tap-and-settle cycles to reach the target mass without overshoot. We will
validate on ten chemically and rheologically diverse powders: sodium chloride
(free-flowing baseline), white rice flour and brown rice flour (highly
cohesive), xanthan gum (cohesive, bridging), sodium alginate, calcium lactate
(very fast-flowing), gas-atomized AlSi10Mg alloy powder (spherical, dense),
crystalline silicon powder in two size grades (fine ~45 um, which jams augers
and flows poorly, and coarser 100-200 mesh), and fumed-silica glidant (also
used at ~0.5-1 wt% as a flow aid for the fine silicon).

Question: What calibration and performance-validation data, statistical
metrics, and experimental protocols does the literature support for
characterizing a gravimetric powder micro-dosing device of this kind, and how
should a per-powder calibration be structured and reported?

Please cover, with quantitative detail where the literature provides it:
1. Standards-based gravimetric test design. ISO 8655-6 (piston-operated
   volumetric apparatus) prescribes n=10 replicate deliveries at 100%, 50%,
   and 10% of nominal volume, reporting systematic error (mean deviation from
   target) and random error (standard deviation / CV) against ISO 8655-2
   maximum permissible errors; the Digital Discovery "digital pipette" papers
   applied exactly this to open hardware. What is the closest analogous
   standard or accepted practice for powder dosing (e.g. USP <41>/<1251>
   balance qualification, OIML R76, ISO 5725 accuracy/precision framework,
   FDA/ICH or pharmacopoeial content-uniformity testing, loss-in-weight feeder
   qualification practice), and what target-mass ladder, replicate count, and
   acceptance limits would a reviewer expect for 20 mg - 5 g powder doses?
2. Per-powder calibration curves. Evidence and best practice for feed-factor
   calibration (mass per auger revolution) as a function of auger speed, tilt
   angle, and fill level; linearity, hysteresis, and drift with powder
   depletion and densification; how loss-in-weight feeder studies calibrate
   and re-calibrate feed factors, and recommended refresh intervals.
3. Statistical metrics and reporting. Systematic vs random error separation,
   CV vs absolute SD at small doses, overshoot rate as an asymmetric error
   metric (powder cannot be removed once dispensed), dose-time reporting,
   minimum weighable quantity given balance repeatability (USP minimum-weight
   concept), and uncertainty budgets combining balance noise, evaporation/
   moisture uptake, static, and vibration-coupled noise.
4. Powder characterization needed alongside dosing data so results transfer:
   particle size distribution, bulk/tapped density, Hausner ratio / Carr
   index, angle of repose, FT4/shear-cell flow function, moisture content;
   which of these best predict auger micro-dosing performance per published
   correlations.
5. Environmental and material covariates: humidity/hygroscopicity effects
   (NaCl deliquescence, rice-flour and xanthan moisture uptake), electrostatic
   charging of fine silicon and polymers, glidant (fumed silica) dose-response
   on cohesive-powder flow, and metal-powder (AlSi10Mg) handling
   considerations relevant to reporting.
6. Precedents for validation of open-source or low-cost dosing/dispensing
   hardware (liquid or solid) in SDL contexts, and what level of validation
   reviewers of Digital Discovery-class journals have accepted.

Where possible, recommend a concrete, defensible validation protocol table
(conditions x replicates x metrics) for our ten-powder campaign, and flag any
published datasets we could compare against. Note: closed-loop optimization
(Bayesian or otherwise) of dosing parameters is explicitly out of scope for
this first paper (future work); the focus is calibration and validation of the
fixed three-phase procedure.
"""


def main() -> None:
    api_key = os.environ.get("EDISON_PLATFORM_API_KEY") or os.environ.get(
        "EDISON_API_KEY"
    )
    if not api_key:
        raise SystemExit("EDISON_PLATFORM_API_KEY is not set.")

    client = EdisonClient(api_key=api_key)
    task = {"name": JobNames.LITERATURE_HIGH, "query": QUERY, "tags": [TAG]}
    print("Dispatching LITERATURE_HIGH task (no wait)...", flush=True)
    task_id = str(client.create_task(task))
    (HERE / "lit_query_task_ids.json").write_text(
        json.dumps({"calibration_lit": task_id}, indent=2)
    )
    print(f"dispatched task id={task_id}", flush=True)


if __name__ == "__main__":
    main()

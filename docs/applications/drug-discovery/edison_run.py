#!/usr/bin/env python3
"""Edison Scientific literature queries for the drug-discovery application
space (issue #159).

Requested in
https://github.com/vertical-cloud-lab/powder-doser/issues/159 by @lbwinters:
find articles on current automated drug-discovery setups, focusing on the
need to dose powder at the milligram-to-gram scale into a liquid *before*
the drug is dispensed in much smaller (nL-pL) amounts, e.g. onto a
lab-on-a-chip. Three ``LITERATURE_HIGH`` queries cover the three requested
deliverables (key articles / current technology / applications) and one
``PRECEDENT`` query checks whether anyone has already done this with a
low-cost doser.

Outputs are written to ``edison_artifacts/`` next to this script, with the
same layout as ``paper/background/edison_artifacts/``:

* ``_task_ids.json``       -- task id + job name for every submitted query.
* ``<key>.task.json``      -- full verbose ``TaskResponse.model_dump()``.
* ``<key>.answer.md``      -- the rendered ``formatted_answer`` (or ``answer``).
* ``<key>.references.md``  -- the standalone numbered references list.

Usage (from the repo root)::

    pip install edison-client
    export EDISON_PLATFORM_API_KEY=...
    python docs/applications/drug-discovery/edison_run.py submit
    python docs/applications/drug-discovery/edison_run.py wait   # blocks
    python docs/applications/drug-discovery/edison_run.py fetch  # no wait

``wait`` polls in a foreground ``time.sleep`` loop (see CLAUDE.md for why it
must not be backgrounded on a CI runner) and writes each task's artifacts as
soon as it reaches a terminal state.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from edison_client import EdisonClient, JobNames

OUT_DIR = Path(__file__).resolve().parent / "edison_artifacts"
TASK_IDS = OUT_DIR / "_task_ids.json"
TAG = "powder-doser-issue-159"
TERMINAL = {"success", "fail", "failed", "cancelled", "error"}

DEVICE_CONTEXT = (
    "Context: we are developing an inexpensive, open-source, gravimetric "
    "powder doser (auger / vibratory feed with a load-cell balance in the "
    "loop) for self-driving laboratories. It was designed for multi-powder "
    "dosing of metal powders for additive-manufacturing alloy discovery and "
    "targets the milligram-to-gram range; it is not intended for "
    "sub-milligram dosing. We want to know where it could be useful in drug "
    "discovery, in particular as the upstream 'weigh solid into a vial, then "
    "dissolve' step that precedes far smaller (nanoliter-to-picoliter) "
    "liquid dispensing onto microplates or lab-on-a-chip / organ-on-chip "
    "devices. "
)

QUERIES: dict[str, tuple[JobNames, str]] = {
    "drugdisc_solid_to_solution": (
        JobNames.LITERATURE_HIGH,
        DEVICE_CONTEXT
        + "In current automated drug discovery workflows (compound management, "
        "high-throughput screening, cell-based and phenotypic assays, and "
        "microfluidic / lab-on-a-chip / organ-on-chip / tumor-on-chip drug "
        "screening), how are solid compounds converted into the liquid stocks "
        "that downstream nanoliter/picoliter dispensers consume (acoustic "
        "droplet ejection such as the Labcyte/Beckman Echo, pin tools, "
        "piezoelectric or inkjet dispensers such as the Tecan D300e, and "
        "on-chip dilution / concentration-gradient generators)? Describe the "
        "'solid-to-solution' step in detail: typical weighed masses (sub-mg, "
        "1-5 mg, 10-100 mg, gram scale), vessels (vials, 2D-barcoded tubes, "
        "plates), solvents (DMSO, water, buffer), target concentrations (e.g. "
        "10 mM DMSO master stocks), whether solvent is added volumetrically "
        "or gravimetrically to hit a target concentration from the recorded "
        "mass, and the accuracy/precision actually required. Identify the "
        "published automation solutions and their bottlenecks (manual "
        "weighing labor, electrostatic / cohesive / hygroscopic / sticky "
        "APIs, cross-contamination, incomplete dissolution and solubility "
        "failures, DMSO water uptake and freeze-thaw degradation that force "
        "re-solubilization from solid), and quantify throughput "
        "(weighings/day), labor and cost where reported. For each key source "
        "give a full citation (authors, year, journal, DOI) and a 2-4 sentence "
        "summary. Aim for 12-20 references, emphasizing 2010-2026 "
        "peer-reviewed work (e.g. SLAS Discovery, SLAS Technology / JALA, "
        "Drug Discovery Today, Lab on a Chip, Organic Process Research & "
        "Development).",
    ),
    "drugdisc_solid_dispensing_tech": (
        JobNames.LITERATURE_HIGH,
        DEVICE_CONTEXT
        + "Review the current technology for automated milligram- and "
        "gram-scale solid/powder dispensing used in pharmaceutical research "
        "and drug discovery: gravimetric dosing heads and platforms (Mettler "
        "Toledo Quantos and CHRONECT XPR, Chemspeed GDU-S SWILE / GDU-Pfd / "
        "FLEX / SWING / Crystal Powderdose, Unchained Labs (Freeslate) Junior "
        "and Big Kahuna, Zinsser Analytic, Labman, Symyx Powdernium, "
        "Sartorius, Hamilton, Brooks/Titian, Tecan), positive-displacement "
        "solid dispensers (e.g. SWILE), capsule micro-dosers for "
        "API-in-capsule (Capsugel Xcelodose, 3P Innovation Fill2Weigh), and "
        "alternative strategies (ChemBeads / coated-bead solid dispensing, "
        "dissolve-and-dispense stock-solution workarounds, vibratory / "
        "tapping / sieving micro-feeders, electrostatic or acoustic powder "
        "dosing). For each, report dose range, accuracy and %RSD (especially "
        "at 0.1-1 mg, 1-5 mg, 5-50 mg and gram targets), dispense time, "
        "dependence on powder properties (cohesive, electrostatic, "
        "hygroscopic, needle-shaped APIs; Hausner ratio, flow function), "
        "containment of potent compounds (OEB / OEL), cross-contamination and "
        "cleaning, and approximate cost. Include the multi-company "
        "benchmarking studies of automated powder dispensing in pharma "
        "high-throughput experimentation (e.g. Bahr et al. 2018 and 2020) and "
        "any newer 2021-2026 evaluations, plus open-source or low-cost "
        "academic powder dispensers built for self-driving labs. Provide a "
        "comparison table and full citations with DOIs.",
    ),
    "drugdisc_applications": (
        JobNames.LITERATURE_HIGH,
        DEVICE_CONTEXT
        + "Identify and prioritize application opportunities in drug "
        "discovery, preclinical development and pharmaceutical R&D where such "
        "a doser, dispensing about 1 mg to several grams of solid into vials "
        "followed by automated solvent addition and mixing / dissolution, "
        "would add value, particularly as the upstream 'solid-to-stock-"
        "solution' step that feeds much smaller-scale downstream liquid "
        "dosing. Evaluate, citing literature: (1) stock preparation for "
        "cell-based, microfluidic and organ-/tumor-on-chip drug sensitivity "
        "assays, including patient-derived samples and personalized oncology "
        "drug panels; (2) solid-form and pre-formulation screening (salt, "
        "polymorph, co-crystal, solubility, dissolution, excipient "
        "compatibility, amorphous solid dispersions); (3) high-throughput "
        "experimentation for medicinal and process chemistry where solid "
        "catalysts, ligands, bases and reagents are dosed at 1-50 mg; (4) "
        "formulation and drug-product prototyping (API-in-capsule, "
        "3D-printed tablets, inhalation powder blends, pediatric / "
        "personalized pharmacy compounding); (5) self-driving / autonomous "
        "chemistry labs that currently avoid powders by working from "
        "pre-made stock solutions; (6) academic core facilities and "
        "low-resource labs that cannot afford commercial dosing systems "
        "costing more than about $50k. For each opportunity state the "
        "required dose range, accuracy / %RSD, throughput, and regulatory "
        "(GMP) or containment constraints, and whether milligram-to-gram "
        "resolution is sufficient or sub-milligram capability is needed. "
        "Also address what accuracy is actually required when the exact "
        "dispensed mass is recorded and the solvent volume is then adjusted "
        "to reach the target concentration, or when stock concentration is "
        "verified afterwards (qNMR, CLND, LC-UV/MS). Conclude with a ranked "
        "list of the most promising niches and suggested key performance "
        "specifications, with full citations and DOIs.",
    ),
    "drugdisc_precedent": (
        JobNames.PRECEDENT,
        "Has anyone built or used a low-cost or open-source automated powder "
        "dispenser (gravimetric, auger, vibratory or tapping) to prepare drug "
        "or compound stock solutions, i.e. dispensing roughly 1-5 mg of solid "
        "into a vial followed by automated solvent addition and mixing, that "
        "then feed a downstream nanoliter/picoliter liquid dispenser or a "
        "microfluidic / lab-on-a-chip / organ-on-chip drug screening device?",
    ),
}


def make_client() -> EdisonClient:
    api_key = os.environ.get("EDISON_PLATFORM_API_KEY") or os.environ.get(
        "EDISON_API_KEY"
    )
    if not api_key:
        raise SystemExit("Set EDISON_PLATFORM_API_KEY (or EDISON_API_KEY).")
    return EdisonClient(api_key=api_key)


def submit(force: bool = False) -> None:
    if TASK_IDS.exists() and not force:
        raise SystemExit(f"{TASK_IDS} exists; pass --force to resubmit.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = make_client()
    record: dict[str, dict[str, str]] = {}
    for key, (job, query) in QUERIES.items():
        task_id = client.create_task(
            {"name": job, "query": query, "tags": [TAG, key]}
        )
        record[key] = {
            "task_id": str(task_id),
            "job_name": job.value,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"submitted {key}: {task_id} ({job.value})", flush=True)
        TASK_IDS.write_text(json.dumps(record, indent=2) + "\n")


def _extract_answer(data: dict) -> tuple[str, str]:
    try:
        answer = data["environment_frame"]["state"]["state"]["response"]["answer"]
    except (KeyError, TypeError):
        return "", ""
    if isinstance(answer, str):
        return answer, ""
    formatted = answer.get("formatted_answer") or answer.get("answer") or ""
    return formatted, answer.get("references") or ""


def write_artifacts(client: EdisonClient, key: str, task_id: str) -> str:
    result = client.get_task(task_id, verbose=True)
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    (OUT_DIR / f"{key}.task.json").write_text(
        json.dumps(data, default=str, indent=2)
    )
    formatted, references = _extract_answer(data)
    (OUT_DIR / f"{key}.answer.md").write_text(formatted)
    (OUT_DIR / f"{key}.references.md").write_text(references)
    status = str(data.get("status"))
    print(
        f"  wrote {key}: status={status} answer_chars={len(formatted)} "
        f"refs_chars={len(references)}",
        flush=True,
    )
    return status


def wait(max_minutes: float, interval: float) -> None:
    record = json.loads(TASK_IDS.read_text())
    client = make_client()
    pending = dict(record)
    deadline = time.monotonic() + 60 * max_minutes
    while pending:
        for key, meta in list(pending.items()):
            status = str(client.get_task(meta["task_id"], lite=True).status)
            print(f"{datetime.now(timezone.utc):%H:%M:%S} {key}: {status}", flush=True)
            if status in TERMINAL:
                write_artifacts(client, key, meta["task_id"])
                pending.pop(key)
        if not pending:
            break
        if time.monotonic() > deadline:
            print(f"deadline reached; still pending: {sorted(pending)}", flush=True)
            break
        time.sleep(interval)


def fetch() -> None:
    record = json.loads(TASK_IDS.read_text())
    client = make_client()
    for key, meta in record.items():
        status = str(client.get_task(meta["task_id"], lite=True).status)
        if status in TERMINAL:
            write_artifacts(client, key, meta["task_id"])
        else:
            print(f"{key}: {status} (not fetched)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_submit = sub.add_parser("submit")
    p_submit.add_argument("--force", action="store_true")
    p_wait = sub.add_parser("wait")
    p_wait.add_argument("--max-minutes", type=float, default=45)
    p_wait.add_argument("--interval", type=float, default=240)
    sub.add_parser("fetch")
    args = parser.parse_args()
    if args.cmd == "submit":
        submit(force=args.force)
    elif args.cmd == "wait":
        wait(args.max_minutes, args.interval)
    else:
        fetch()


if __name__ == "__main__":
    main()

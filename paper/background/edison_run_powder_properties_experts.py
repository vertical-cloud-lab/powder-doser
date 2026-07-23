#!/usr/bin/env python3
"""Edison Scientific ``LITERATURE_HIGH`` follow-up queries that identify named
individuals and organizations who could weigh in on **powder properties**
specifically — flowability, cohesion/friction measurement, DEM modeling and
calibration, and AM powder spreadability/packing — as requested in PR #41
(sgbaird: "run a set of follow-up Edison queries ... based on the TMS
abstract by Will ... people who could weigh in on powder properties
specifically").

The queries are anchored to Will's TMS 2027 abstract (PR #78,
``abstracts/tms-2027/calibration-optimization/abstract.md``): "Auger-Based
Powder Dosing as a Mechanistic Probe of Powder Flow Behavior: Multi-Task
Bayesian Calibration and Physics-Based Property Inference". The abstract text
is embedded verbatim below so each query is self-contained and reproducible.

This is the powder-properties counterpart to
``edison_run_powder_dispensing_outreach_contacts.py`` (this PR) and
``edison_run_outreach_contacts.py`` (PR #43); the per-contact H3 layout,
``(source: <URL>)`` tag, and "do not invent emails" guardrail are mirrored so
all the synthesized outreach notes are directly comparable.

Output is written to ``paper/background/edison_artifacts/`` with the same
``<key>.task.json`` / ``<key>.answer.md`` / ``<key>.references.md`` layout.
The script is split into dispatch / wait / fetch phases so the task IDs
(``powder_properties_experts._task_ids.json``) can be committed immediately
after dispatch and results fetched later if needed. Re-run with::

    pip install edison_client
    export EDISON_API_KEY=...   # never commit this value
    python paper/background/edison_run_powder_properties_experts.py dispatch
    python paper/background/edison_run_powder_properties_experts.py wait
    python paper/background/edison_run_powder_properties_experts.py fetch

(or ``all`` to run the three phases back-to-back).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames

TMS_ABSTRACT = (
    "Title: Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow "
    "Behavior: Multi-Task Bayesian Calibration and Physics-Based Property "
    "Inference\n\n"
    "Dispensed mass from an auger-based powder doser depends on actuator "
    "settings and powder properties, so every calibration curve doubles as a "
    "compact probe of cohesion, friction, and packing behavior. We frame "
    "calibration of an open-source doser as AI-driven, multi-objective, "
    "multi-task Bayesian optimization, with objectives of dose accuracy, "
    "repeatability, dispensing time, and accessible dose range. Each powder "
    "is a related task—primarily alloy precursors, in elemental or "
    "master-alloy form depending on handling constraints and hazards, dosed "
    "under inert atmosphere, alongside feedstocks such as AlSi10Mg and "
    "stainless steel—and multi-task models share information across "
    "powders to cut per-powder calibration effort. Alongside gravimetric "
    "parameter sweeps, we are exploring discrete element modeling with "
    "cohesive-frictional contact laws and measured particle-size "
    "distributions, enabling inference of effective cohesion and friction "
    "from dosing data, to be checked against shear-cell and Hall-flow "
    "measurements. Linking dosing response to these properties may "
    "anticipate downstream behavior such as spreadability and packing "
    "uniformity."
)

PREAMBLE = (
    "A small university research lab (BYU Vertical Cloud Lab, ~3 people, "
    "NASA Space Grant scale, building an open-source auger-based powder "
    "doser for self-driving-lab metal-alloy discovery) is preparing the "
    "following TMS 2027 abstract and wants to identify named people and "
    "organizations who could weigh in on the POWDER PROPERTIES side of the "
    "work — not powder dispensing hardware in general (that outreach list "
    "already exists), but flow behavior, property measurement, and "
    "simulation.\n\n--- TMS 2027 abstract (verbatim) ---\n"
    + TMS_ABSTRACT
    + "\n--- end abstract ---\n\n"
    "For EACH named contact give: full name, current affiliation / role, "
    "the specific reason they are relevant to THIS abstract (1-3 sentences "
    "with concrete evidence — paper, instrument, code, standard, talk), AT "
    "LEAST ONE direct, *publicly listed* contact channel (institutional or "
    "company email, lab website contact page, GitHub handle, LinkedIn, "
    "company support address), and the FULL public URL where that contact "
    "info is listed so the claim can be verified. If only a lab/org-level "
    "channel is public, say so explicitly. Do NOT invent emails — if you "
    "cannot find a public address, say 'no public direct email found; "
    "reachable via <URL>'. Format the answer as Markdown with one H2 per "
    "category and one H3 subsection per named contact (each contact gets "
    "its own anchor), and end every subsection with a parenthetical "
    "'(source: <full URL>)'. Prioritize direct individual channels over "
    "generic info@ inboxes.\n\n"
)

QUERIES: dict[str, str] = {
    "powder_properties_rheology_experts": (
        PREAMBLE
        + "Focus of THIS query: experts in **powder rheology, flowability, "
        "and cohesion/friction measurement** who could advise on the "
        "shear-cell and Hall-flow validation path in the abstract and on "
        "characterizing cohesive, static-prone metal and alloy-precursor "
        "powders. Cover (aim ~4-6 named contacts per category, ~15-20 "
        "total):\n"
        "  1. **Academic powder-mechanics / particle-technology PIs** "
        "(e.g., Mojtaba Ghadiri and Ali Hassanpour at Leeds, Colin Hare, "
        "Mike Bradley at the Wolfson Centre for Bulk Solids Handling "
        "Technology, Fernando Muzzio and Benjamin Glasser at Rutgers "
        "C-SOPS, Jennifer Sinclair Curtis, Christine Hrenya at CU Boulder, "
        "and comparable groups working on cohesion/friction of fine "
        "powders).\n"
        "  2. **Powder-characterization instrument makers with named "
        "application scientists** (Freeman Technology / Micromeritics FT4 "
        "— Tim Freeman; Granutools — Geoffroy Lumay, Filip Francqui; "
        "Anton Paar powder cell; Mercury Scientific Revolution; Brookfield "
        "PFT; ring shear testers — Dietmar Schulze).\n"
        "  3. **Standards and test-method communities** for powder flow "
        "(ASTM B09 on metal powders, ASTM D18/D6773 Schulze shear test, "
        "ISO 4490 Hall flowmeter, MPIF standards staff, USP <1174>).\n"
        "  4. **People who have specifically published on flow properties "
        "of metal-AM feedstocks** (Hall/Carney flow vs rheometer studies, "
        "AlSi10Mg / stainless / Ti-6Al-4V powder characterization)."
    ),
    "powder_properties_dem_calibration": (
        PREAMBLE
        + "Focus of THIS query: experts in **discrete element modeling "
        "(DEM) with cohesive-frictional contact laws, DEM parameter "
        "calibration, and inverse inference of powder properties from "
        "process data** — the people who could weigh in on the abstract's "
        "plan to infer effective cohesion and friction from auger dosing "
        "curves. Cover (aim ~4-6 named contacts per category, ~15-20 "
        "total):\n"
        "  1. **Academic DEM / granular-mechanics PIs** (e.g., Carl "
        "Wassgren at Purdue, Jin Ooi and Kevin Hanley at Edinburgh, Stefan "
        "Luding at Twente, Thorsten Pöschel at FAU Erlangen, Christine "
        "Hrenya, Paul Cleary at CSIRO — including anyone who has published "
        "DEM of screw/auger feeders or conveyors specifically).\n"
        "  2. **DEM calibration methodology authors** — papers on "
        "calibrating DEM contact parameters against shear-cell / angle-of-"
        "repose / drum tests, Bayesian or surrogate-based DEM calibration "
        "(e.g., GrainLearning — Vanessa Magnanimo / Hongyang Cheng), and "
        "virtual calibration workflows.\n"
        "  3. **Open-source and commercial DEM software teams with public "
        "dev contacts** (LIGGGHTS / Aspherix — DCS Computing, Christoph "
        "Kloss; Yade; MercuryDPM — Anthony Thornton / Thomas Weinhart; "
        "MFiX-DEM at NETL; Lethe CFD-DEM — Bruno Blais at Polytechnique "
        "Montréal; Altair EDEM application engineers; Rocky DEM).\n"
        "  4. **Groups coupling DEM to machine learning / Bayesian "
        "optimization for granular processes** relevant to the multi-task "
        "calibration framing."
    ),
    "powder_properties_am_spreadability": (
        PREAMBLE
        + "Focus of THIS query: experts in **metal-AM powder spreadability, "
        "packing, and powder-bed quality metrology** who could weigh in on "
        "the abstract's closing claim that dosing-derived properties may "
        "anticipate spreadability and packing uniformity. Cover (aim ~4-6 "
        "named contacts per category, ~15-20 total):\n"
        "  1. **Researchers who built spreadability / recoating test rigs "
        "or metrics for L-PBF powders** (e.g., work by Zackary Snow and "
        "Edward Reutzel at Penn State, Christopher Roberts / Sheffield, "
        "Inspire AG (Adriaan Spierings), and other published spreading-rig "
        "or spreadability-index authors 2018-2026).\n"
        "  2. **National-lab and metrology-institute powder programs** "
        "(NIST AM Bench and NIST powder-characterization staff such as "
        "Justin Whiting and Alkan Donmez; NRC Canada; BAM Berlin — powder "
        "spreading of AM feedstocks; Ames National Laboratory atomization "
        "— Iver Anderson / Emma White).\n"
        "  3. **AM powder producers and services with named technical "
        "staff** (Carpenter Additive / LPW, AP&C (GE Additive), Equispheres, "
        "6K Additive, Kymera, Praxair/Linde — powder quality and reuse "
        "studies with public application-engineering contacts).\n"
        "  4. **Standards efforts on AM powder spreadability and packing** "
        "(ASTM F42 powder subcommittees, ASTM AM CoE powder spreadability "
        "round robins, ISO/ASTM 52907) with named committee contacts where "
        "public."
    ),
}

TAG = "powder-doser-grant"
KEY_PREFIX = "powder_properties_experts"
TERMINAL = {"success", "fail", "failed", "cancelled", "error"}

OUT_DIR = Path(__file__).parent / "edison_artifacts"
IDS_PATH = OUT_DIR / f"{KEY_PREFIX}._task_ids.json"


def _client() -> EdisonClient:
    api_key = os.environ.get("EDISON_API_KEY") or os.environ.get(
        "EDISON_PLATFORM_API_KEY"
    )
    if not api_key:
        raise SystemExit(
            "EDISON_API_KEY (or EDISON_PLATFORM_API_KEY) is not set. "
            "Export it before running this script."
        )
    return EdisonClient(api_key=api_key)


def dispatch() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = _client()
    ids: dict[str, str] = {}
    for key, query in QUERIES.items():
        task_id = client.create_task(
            {
                "name": JobNames.LITERATURE_HIGH,
                "query": query,
                "tags": [TAG, key, "outreach-contacts", "powder-properties"],
            }
        )
        ids[key] = str(task_id)
        print(f"dispatched {key}: {task_id}", flush=True)
    IDS_PATH.write_text(json.dumps(ids, indent=2))
    print(f"Wrote task ids to {IDS_PATH}", flush=True)


def wait(poll_seconds: int = 240) -> None:
    client = _client()
    ids = json.loads(IDS_PATH.read_text())
    pending = dict(ids)
    while pending:
        done = []
        for key, task_id in pending.items():
            task = client.get_task(task_id=task_id)
            status = str(getattr(task, "status", "?")).lower()
            print(f"status {key}: {status}", flush=True)
            if status in TERMINAL:
                done.append(key)
        for key in done:
            pending.pop(key)
        if pending:
            time.sleep(poll_seconds)
    print("All tasks terminal.", flush=True)


def fetch() -> None:
    client = _client()
    ids = json.loads(IDS_PATH.read_text())
    for key, task_id in ids.items():
        result = client.get_task(task_id=task_id, verbose=True)
        data = (
            result.model_dump() if hasattr(result, "model_dump") else dict(result)
        )
        (OUT_DIR / f"{key}.task.json").write_text(
            json.dumps(data, default=str, indent=2)
        )
        try:
            answer = data["environment_frame"]["state"]["state"]["response"]["answer"]
            formatted = answer.get("formatted_answer") or answer.get("answer") or ""
            references = answer.get("references") or ""
        except (KeyError, TypeError):
            formatted, references = "", ""
        (OUT_DIR / f"{key}.answer.md").write_text(formatted)
        (OUT_DIR / f"{key}.references.md").write_text(references)
        print(
            f"  {key}: status={data.get('status')} "
            f"answer_chars={len(formatted)} refs_chars={len(references)}",
            flush=True,
        )
    print(f"Wrote artifacts to {OUT_DIR}", flush=True)


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    if phase in ("dispatch", "all"):
        dispatch()
    if phase in ("wait", "all"):
        wait()
    if phase in ("fetch", "all"):
        fetch()


if __name__ == "__main__":
    main()

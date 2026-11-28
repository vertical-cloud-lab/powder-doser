#!/usr/bin/env python3
"""Edison literature queries that corroborate the ten in-house test apparatuses (PR #205).

Five high-effort literature queries, one per pair of tests, ask what the published record says about
each in-house design choice: base and drum sizes, lateral vs drop tapping, tilting-plate wall friction
at low stress, image-based PSD, small orifices, salt-solution humidity chambers, uniaxial strength at
low stress, lab spreading rigs and Faraday cups. A sixth query (q6) is sent after the simulations, with
their numbers, to check them against the literature.

Usage (from design/in-house-tests/):
  python edison/run_queries.py dispatch [key ...]   # create tasks, record ids in edison/_task_ids.json
  python edison/run_queries.py status               # one line per task
  python edison/run_queries.py wait [max_s] [key ...]   # poll in the foreground, then fetch
  python edison/run_queries.py fetch [key ...]      # write edison/<key>.{task.json,answer.md}

The API key is read from EDISON_PLATFORM_API_KEY and never printed. Pattern from #196
(docs/physics-simulations/edison/run_queries.py at e8811bd).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
IDS = HERE / "_task_ids.json"
TAG = "powder-doser-in-house-tests"
DONE = {"success", "fail", "failed", "cancelled", "error"}

CONTEXT = (
    "Context: we run an open-source, 3D-printed (PLA) auger powder doser for self-driving labs in alloy "
    "discovery for additive manufacturing. A 25 mm OD tube with a 21 mm bore and a helical flight ends in a "
    "3 mm outlet; a NEMA 11 stepper turns it at 1-109 rpm, servos tilt it 0-90 degrees, a solenoid taps it, "
    "and doses fall onto a 0.1 mg analytical balance. We record a dosing fingerprint (mass per revolution vs "
    "tilt and speed, mass per tap, afterflow, no-flow fraction) on 13 powders (NaCl, gas-atomized AlSi10Mg, "
    "silicon, rice flours, xanthan gum, carboxymethyl cellulose, BaCl2 dihydrate, fumed silica and others) and "
    "calibrate a LIGGGHTS DEM twin. Property labels from handbooks limit our models (angle-of-repose ranges "
    "6-16 degrees wide), so we are designing ten small in-house tests built around the doser, each using a few "
    "grams and run on the same jar and day as the fingerprint: (1) heap angle of repose on a 20 mm fixed "
    "pedestal on the balance, photographed in silhouette; (2) bulk and tapped density in a 10 mL Class A "
    "cylinder filled by the auger and tapped by a cam drop of 3 mm at 250 taps/min, column height read by "
    "camera; (3) a servo tilting plate with an IMU: wall friction of a 25 mm powder-filled ring at 70-450 Pa "
    "on PLA, stainless steel and glass, and the start angle of 1-5 mm powder layers; (4) particle size and "
    "shape from backlit images with a Raspberry Pi HQ camera and a 0.12-1.8x zoom lens; (5) a 25 mm cup with "
    "1-6 mm orifice discs and a servo gate emptying onto the balance (Beverloo fit, smallest orifice that "
    "flows, with and without taps); (6) humidity chambers held by saturated salt solutions (MgCl2, Mg(NO3)2, "
    "NaCl, KCl, silica gel) with SHT45 sensors, weighing uptake and dosing before and after; (7) a 40 mm by "
    "15 mm rotating drum driven by the doser's stepper, 1-20 rpm; (8) unconfined yield strength of a 20 mm by "
    "40 mm column from a split mould after 0.2-2 kPa consolidation, crushed by a lead-screw platen on a 100 g "
    "load cell; (9) a blade spreading a 0.1-0.2 mm layer over a 100 x 30 mm coupon at 10-100 mm/s; (10) a "
    "Faraday cup (aluminium cup in a grounded can) with a femtoamp op-amp charge amplifier under the doser "
    "outlet. "
)

QUERIES = {
    "q1_heap_and_drum": ("LITERATURE_HIGH", (
        "For tests (1) and (7): what does the literature report on (a) fixed-base (pedestal) angle-of-repose "
        "tests compared with ISO 4324 funnel pouring, the lifting cylinder and the tilting box: the effect of "
        "base diameter relative to particle size (how many particle diameters before the angle stops "
        "depending on base size), pour height and rate, feeding from a screw instead of a funnel, image "
        "analysis of heap profiles versus the apex formula, repeatability (standard deviation over repeat "
        "pours) and inter-method differences; (b) small rotating drums (GranuDrum 84 mm, Revolution Powder "
        "Analyzer, and drums under 50 mm): the effect of drum diameter, depth and end-wall friction on the "
        "dynamic angle and avalanche statistics, the Froude-number regimes, the cohesive index definitions, "
        "and how many particle diameters a drum must span; (c) DEM studies that simulated these exact tests "
        "for calibration and how well the calibrated parameters transferred to other flows. Give numbers for "
        "table salt, gas-atomized metal AM powders (AlSi10Mg, 316L, Ti-6Al-4V) and fine cohesive powders.")),
    "q2_density_and_orifice": ("LITERATURE_HIGH", (
        "For tests (2) and (5): what does the literature report on (a) tapped density in small (10-25 mL) "
        "cylinders versus the 100-250 mL of USP <616> and ASTM B527: wall effects versus cylinder diameter to "
        "particle size, fill method (funnel, sieve, auger), drop height (3 mm vs 14 mm) and tap rate, lateral "
        "versus vertical tapping, how many taps to plateau, the repeatability of the Hausner ratio, and "
        "Kawakita or other compaction-curve fits; (b) flow through small orifices: the Beverloo constants C and "
        "k for fine and cohesive powders, the Flodex minimum orifice diameter test (USP <1174>) and how the "
        "minimum orifice relates to unconfined yield strength by Jenike's arching criterion, the effect of "
        "vibration or tapping on the critical orifice, air counter-flow effects for particles below about 100 "
        "micrometres, and the comparison of these small-orifice tests with Hall and Carney funnels (ASTM B213, "
        "B964). Include numbers for metal AM powders, salts and pharmaceutical powders.")),
    "q3_wall_friction_and_ucs": ("LITERATURE_HIGH", (
        "For tests (3) and (8): what does the literature report on (a) inclined-plane or tilting-plate "
        "measurements of powder wall friction (a powder-filled ring or sled on a tilting wall coupon) compared "
        "with Jenike (ASTM D6128) and Schulze ring-shear (D6773) wall-friction tests, especially at low normal "
        "stress (50-500 Pa) where shear cells struggle, the stress dependence of the wall friction angle, "
        "wall adhesion, and typical wall friction angles of powders on polymers (PLA, PETG, ABS, nylon), "
        "stainless steel and glass; (b) the start angle of thin powder layers on inclined rough planes versus "
        "layer thickness (Pouliquen h_stop/h_start curves) for cohesive powders; (c) uniaxial or unconfined "
        "compression tests of powder columns at low consolidation stress (0.2-5 kPa): published apparatus "
        "(Williams and Birks, Parrella, Freeman, the Brookfield PFT, the Ezi-Tester, Johanson Indicizer), the "
        "height-to-diameter ratio, mould wall friction during consolidation, how uniaxial strength compares "
        "with shear-cell unconfined yield strength and flow function ffc, and the smallest consolidation "
        "stresses at which strength has been measured reliably.")),
    "q4_psd_images_and_spreading": ("LITERATURE_HIGH", (
        "For tests (4) and (9): what does the literature report on (a) particle size and shape from 2D "
        "backlit images (static image analysis, ISO 13322-1) compared with laser diffraction (ISO 13320, ASTM "
        "B822) and sieving (ASTM B214): systematic differences in d10, d50 and d90, number-to-volume "
        "conversion, the number of particles needed for a given precision of d50 and d90, dispersion of "
        "cohesive fine powders on slides (dry and wet), resolution limits (pixels per particle), and low-cost "
        "camera or smartphone microscopes validated against commercial instruments; (b) laboratory powder "
        "spreading rigs for powder-bed additive manufacturing (blade or roller over a coupon, single layers): "
        "the metrics used (coverage, packing fraction, areal mass, surface roughness, streaks), the effect of "
        "gap (1-5 particle diameters) and speed (10-100 mm/s), repeatability, and how well angle of repose, "
        "Hausner ratio, drum avalanche angle and shear-cell ffc predict spreadability. Include DEM validation "
        "of such rigs and numbers for AlSi10Mg, 316L and Ti-6Al-4V.")),
    "q5_humidity_and_charge": ("LITERATURE_HIGH", (
        "For tests (6) and (10): what does the literature report on (a) saturated-salt humidity chambers "
        "(Greenspan 1977; ISO 12571; OIML): accuracy, temperature sensitivity, equilibration time after "
        "opening, the effect of a mixing fan, sample size and layer thickness for gravimetric sorption, "
        "agreement with dynamic vapour sorption, and humidity effects on the flow of NaCl (deliquescence near "
        "75 % RH), metal AM powders (AlSi10Mg, Ti-6Al-4V) and pharmaceutical powders, including caking; (b) "
        "Faraday-cup measurement of the charge-to-mass ratio of powders after feeding, conveying or sieving: "
        "cup and shield design, electrometers versus home-built charge amplifiers (op-amp choice, feedback "
        "capacitor, leakage, guarding), collection efficiency for fines, typical charge-to-mass ratios for "
        "salts, metal powders and organic powders after contact with polymers (PLA, PTFE, PETG, nylon) and "
        "steel, and their humidity dependence.")),
}

# Sent after the DEM/FEA/CFD/theory work, with its numbers pasted in (see dispatch_results()).
RESULTS_QUERY_KEY = "q6_corroborate_simulations"


def _client():
    from edison_client import EdisonClient

    key = os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit("EDISON_PLATFORM_API_KEY is not set.")
    return EdisonClient(api_key=key)


def _client_retry(tries: int = 6):
    for attempt in range(tries):
        try:
            return _client()
        except Exception as exc:  # noqa: BLE001
            print(f"login attempt {attempt + 1} failed ({type(exc).__name__}); retrying", flush=True)
            time.sleep(15 * (attempt + 1))
    raise SystemExit("could not log in to Edison")


def _load_ids() -> dict:
    return json.loads(IDS.read_text()) if IDS.exists() else {}


def _create(client, job: str, query: str):
    from edison_client import JobNames

    for attempt in range(6):
        try:
            return str(client.create_task({"name": getattr(JobNames, job), "query": query, "tags": [TAG]}))
        except Exception as exc:  # noqa: BLE001 - the login endpoint intermittently returns 403
            print(f"create attempt {attempt + 1} failed ({type(exc).__name__}); retrying", flush=True)
            time.sleep(15 * (attempt + 1))
            client = _client_retry()
    return None


def _record(key: str, job: str, query: str, task_id: str) -> None:
    from edison_client import JobNames

    ids = _load_ids()
    ids[key] = {"task_id": task_id, "job": job, "job_name": getattr(JobNames, job).value,
                "dispatched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "query": query}
    IDS.write_text(json.dumps(ids, indent=2) + "\n")


def dispatch(keys: list[str] | None = None) -> None:
    client = _client_retry()
    ids = _load_ids()
    for key, (job, text) in QUERIES.items():
        if keys and key not in keys:
            continue
        if key in ids:
            print(f"{key}: already dispatched ({ids[key]['task_id']})")
            continue
        query = CONTEXT + text
        task_id = _create(client, job, query)
        if task_id is None:
            print(f"{key}: NOT dispatched", flush=True)
            continue
        _record(key, job, query, task_id)
        print(f"{key}: {job} -> {task_id}", flush=True)


def dispatch_results(summary_file: str) -> None:
    """q6: paste the simulation summary and ask Edison to check it against published values."""
    ids = _load_ids()
    if RESULTS_QUERY_KEY in ids:
        print(f"{RESULTS_QUERY_KEY}: already dispatched ({ids[RESULTS_QUERY_KEY]['task_id']})")
        return
    summary = Path(summary_file).read_text()
    query = CONTEXT + (
        "We simulated these ten tests as designed (LIGGGHTS DEM with real-size salt-like spheres 0.36-0.49 mm, "
        "Hertz-Mindlin, Young's modulus reduced to 2e5 Pa, sliding friction 0.5, wall friction 0.4, EPSD2 rolling "
        "friction 0.3, and a cohesive variant with SJKR cohesion energy density 6 kJ/m3, granular Bond number "
        "about 5; plus FEA, CFD and textbook models). Our predicted readings are below. For each number, say "
        "whether it is consistent with published measurements or simulations of the same test on comparable "
        "powders (table salt, sand or glass beads of similar size, and cohesive powders), cite the closest "
        "published values, and flag any prediction that looks implausible and why:\n\n" + summary)
    client = _client_retry()
    task_id = _create(client, "LITERATURE_HIGH", query)
    if task_id is None:
        raise SystemExit(f"{RESULTS_QUERY_KEY}: NOT dispatched")
    _record(RESULTS_QUERY_KEY, "LITERATURE_HIGH", query, task_id)
    print(f"{RESULTS_QUERY_KEY}: LITERATURE_HIGH -> {task_id}", flush=True)


def _status(client, task_id: str) -> str:
    return str(client.get_task(task_id=task_id).status)


def status() -> dict[str, str]:
    client = _client_retry()
    out = {}
    for key, rec in _load_ids().items():
        try:
            out[key] = _status(client, rec["task_id"])
        except Exception as exc:  # noqa: BLE001
            out[key] = f"error ({type(exc).__name__})"
        print(f"{key}: {out[key]}", flush=True)
    return out


def _answer_text(task) -> str:
    for attr in ("formatted_answer", "answer"):
        val = getattr(task, attr, None)
        if val:
            return str(val)
    env = getattr(task, "environment_frame", None) or {}
    try:
        return str(env["state"]["state"]["response"]["answer"]["formatted_answer"])
    except Exception:  # noqa: BLE001
        return ""


def fetch(keys: list[str] | None = None) -> None:
    client = _client_retry()
    for key, rec in _load_ids().items():
        if keys and key not in keys:
            continue
        task = client.get_task(task_id=rec["task_id"], verbose=True)
        st = str(task.status)
        data = task.model_dump(mode="json") if hasattr(task, "model_dump") else json.loads(task.json())
        (HERE / f"{key}.task.json").write_text(json.dumps(data, indent=2, default=str) + "\n")
        ans = _answer_text(task)
        if st == "success" and ans:
            (HERE / f"{key}.answer.md").write_text(
                f"# {key}\n\nEdison `{rec['job_name']}`, task `{rec['task_id']}`, dispatched "
                f"{rec['dispatched_utc']}.\n\n## Query\n\n{rec['query']}\n\n## Answer\n\n{ans}\n")
        print(f"{key}: {st}, answer {len(ans)} chars", flush=True)


def wait(max_s: float = 3000, keys: list[str] | None = None) -> None:
    t0 = time.time()
    client = _client_retry()
    while True:
        pending = []
        for key, rec in _load_ids().items():
            if keys and key not in keys:
                continue
            try:
                st = _status(client, rec["task_id"])
            except Exception as exc:  # noqa: BLE001
                st = f"error ({type(exc).__name__})"
                client = _client_retry()
            if st not in DONE:
                pending.append(key)
        print(time.strftime("%H:%M:%S"), "pending:", pending, flush=True)
        if not pending or time.time() - t0 > max_s:
            break
        time.sleep(120)
    fetch(keys)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "dispatch":
        dispatch(sys.argv[2:] or None)
    elif cmd == "dispatch-results":
        dispatch_results(sys.argv[2])
    elif cmd == "status":
        status()
    elif cmd == "fetch":
        fetch(sys.argv[2:] or None)
    elif cmd == "wait":
        max_s = float(sys.argv[2]) if len(sys.argv) > 2 else 3000
        wait(max_s, sys.argv[3:] or None)
    else:
        raise SystemExit(__doc__)

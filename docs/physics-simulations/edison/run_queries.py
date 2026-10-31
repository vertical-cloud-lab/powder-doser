#!/usr/bin/env python3
"""Edison literature queries: which physics-based simulations fit the powder doser work (PR #184, #179).

A series of Edison Scientific tasks (paperqa3 literature, high-effort literature and precedent search)
asks what physics-based simulations could be run on the doser and on the standard powder tests discussed in
PR #184 (DEM inference of cohesion and friction, shear cell, Hall/Carney, angle of repose, densities,
moisture, static, spreadability).

Usage (from docs/physics-simulations/):
  python edison/run_queries.py dispatch        # create every task, record ids in edison/_task_ids.json
  python edison/run_queries.py status          # one status line per task (no waiting)
  python edison/run_queries.py wait            # poll in the foreground until all finish, then fetch
  python edison/run_queries.py fetch           # write edison/<key>.{task.json,answer.md}

The API key is read from EDISON_PLATFORM_API_KEY and is never printed.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
IDS = HERE / "_task_ids.json"
TAG = "powder-doser-physics-simulations"
DONE = {"success", "fail", "failed", "cancelled", "error"}

CONTEXT = (
    "Context: we run an open-source, 3D-printed (PLA/PETG) auger powder doser for self-driving labs in alloy "
    "discovery for additive manufacturing. A small helical auger (1 mL and 10 mL reservoirs, about 3 mm outlet) "
    "is turned by a stepper motor at 1-30 rpm, the doser can be tilted 0-30 degrees from horizontal, and a "
    "solenoid taps the housing; doses of 0.05-8 g fall onto an analytical balance under closed-loop control. "
    "We have dosed 13 powders (NaCl table salt, gas-atomized AlSi10Mg and Al 4047, two silicon grades, rice "
    "flour, xanthan gum, carboxymethyl cellulose, BaCl2 and others) and record a 'dosing fingerprint': mass per "
    "auger revolution versus tilt and speed, the mass freed by one tap, the afterflow time constant after the "
    "auger stops, and the fraction of increments with no flow. A LIGGGHTS DEM model of the auger outlet "
    "(Hertz-Mindlin, SJKR cohesion, constant-directional-torque rolling friction) reproduces the measured "
    "105 mg/rev for salt with no fitted parameters but costs 26-30 CPU-minutes per simulated revolution. We "
    "want to (i) infer powder properties (cohesion, friction, moisture sensitivity, packing) from dosing data "
    "by simulation-based Bayesian calibration, (ii) check the inferred values against standard tests (ASTM "
    "D7891 FT4 shear cell, D6773 Schulze ring shear, B213 Hall and B964 Carney flow, B212/B527 apparent and "
    "tap density, angle of repose, B214 sieving, B822 laser diffraction, loss on drying), and (iii) anticipate "
    "spreadability in powder-bed additive manufacturing. "
)

QUERIES = {
    "q1_feeder_simulation_methods": ("LITERATURE_HIGH", (
        "Which physics-based simulation methods have been used to model screw or auger feeders and the "
        "micro-dosing of powders: DEM with any contact model, coupled CFD-DEM, continuum approaches (material "
        "point method, SPH, FEM with Drucker-Prager or mu(I) rheology), cellular automata, and analytical or "
        "reduced-order feed-factor models? For each method give the codes used (open-source such as LIGGGHTS, "
        "LAMMPS granular, MercuryDPM, Yade, Project Chrono, MFiX, Blaze-DEM, or commercial such as EDEM, Rocky, "
        "PFC), the contact and cohesion models, speed-ups (coarse-graining, reduced Young's modulus, GPU), "
        "typical computational cost, what was validated against experiments (mass flow rate, feed factor, "
        "fluctuations, refill), and which studies used the simulation to infer powder properties from feeder "
        "data. Rank the methods by suitability for a millimetre-scale auger dosing cohesive fine powders "
        "(10-100 micrometres) and salts, and list concrete published input parameters we could reuse.")),
    "q2_dem_calibration_standard_tests": ("LITERATURE_HIGH", (
        "How are DEM contact parameters (sliding friction, rolling friction, JKR or SJKR surface energy, "
        "restitution, Young's modulus) calibrated for cohesive powders by simulating standard characterization "
        "tests: shear cells (Jenike, Schulze ring shear, FT4 rotational shear), FT4 dynamic flow (basic "
        "flowability energy), angle of repose (fixed funnel, rotating drum, lifting cylinder), Hall and Carney "
        "funnel discharge, bulk and tapped density, and uniaxial compression? Which tests are sensitive to which "
        "parameters, which parameter combinations are not identifiable from one test, and which combinations of "
        "tests break the degeneracy? Which surrogate and Bayesian methods are used (GrainLearning sequential "
        "Monte Carlo, Gaussian-process emulators, Kriging, polynomial chaos, neural-network surrogates, MCMC, "
        "approximate Bayesian computation, design of experiments), with how many simulations? Give quantitative "
        "examples for metal additive-manufacturing powders, salts and pharmaceutical powders.")),
    "q3_spreadability_simulation": ("LITERATURE", (
        "What physics-based simulations are used to predict powder spreadability and packing in powder-bed "
        "additive manufacturing (laser powder bed fusion, binder jetting, electron beam melting): DEM of blade "
        "and roller recoating with cohesive contact models, coarse-grained DEM, coupled DEM-CFD, and continuum "
        "models? Which spreadability metrics (packing fraction, surface roughness, coverage, mass per area, void "
        "fraction, segregation) are computed, how are they validated against spreading experiments, and how "
        "well do standard flowability tests (Hall flow, angle of repose, Hausner ratio, shear-cell ffc, FT4 "
        "energy, avalanche angle in a rotating drum) predict spreadability? Which open-source codes and "
        "published input decks exist?")),
    "q4_moisture_capillary": ("LITERATURE", (
        "How do physics-based simulations represent humidity and moisture effects on fine-powder flow: liquid "
        "(capillary) bridge force models in DEM (Willett, Rabinovich, Lian, pendular regime), "
        "relative-humidity-dependent cohesion, hygroscopic salts such as NaCl and BaCl2 with deliquescence and "
        "caking by solid bridges, and moisture sorption kinetics? Which open-source DEM codes implement "
        "capillary forces (LIGGGHTS, LAMMPS, Yade, MercuryDPM)? How have these models been validated against "
        "shear-cell, angle-of-repose or flow-rate measurements at controlled humidity, and could they model an "
        "experiment in which a powder is dosed before and after exposure to humid air?")),
    "q5_electrostatics": ("LITERATURE", (
        "What physics-based models and simulations describe triboelectric charging of powders during feeding, "
        "conveying and dosing (condenser model, work-function or surface-state models, DEM with charge transfer "
        "plus Coulomb and image forces, CFD-DEM with electrostatics), particularly contacts between metal or "
        "salt particles and polymer walls (PLA, PETG, nylon); the effect of humidity and of inert gases "
        "(argon, nitrogen) on charge relaxation and gas breakdown; and adhesion of charged fine particles to "
        "walls? Which open-source codes implement this, which parameters are needed, and how were the "
        "simulations validated (Faraday-cup charge-to-mass ratio)?")),
    "q6_precedent_feeder_as_instrument": ("PRECEDENT", (
        "Has anyone used the dosing or discharge response of a small screw or auger feeder or powder doser "
        "(mass per revolution as a function of tilt angle and screw speed, flow intermittency, afterflow) "
        "together with discrete element simulations to inversely infer powder properties such as cohesion or "
        "interparticle friction, that is, used the feeder itself as a powder characterization instrument, and "
        "validated the inferred values against shear-cell or other standard flowability measurements?")),
    "q7_continuum_reduced_order": ("LITERATURE", (
        "Which continuum and reduced-order physics models predict granular discharge through small orifices "
        "and screw conveyors for cohesive powders: Beverloo and modified Beverloo laws with cohesion, "
        "Jenike-Johanson arching and hopper design from shear-cell flow functions, Janssen stress saturation, "
        "mu(I) and non-local rheologies, Drucker-Prager or Mohr-Coulomb plasticity in FEM, the material point "
        "method, smoothed-particle hydrodynamics, cellular automata and avalanche models, and screw-conveyor "
        "volumetric-efficiency models (for example Roberts; Owen and Cleary)? Which have open-source "
        "implementations (for example Taichi MPM, PySPH, Uintah, Basilisk, OpenFOAM granular solvers), what "
        "inputs do they need, and how accurately do they predict mass flow rate compared with DEM and "
        "experiment?")),
    "q8_tapping_packing_shape": ("LITERATURE", (
        "How are tapping, vibration and compaction of fine powders simulated: DEM of tapped density and "
        "Hausner ratio, vibration-assisted dosing from vibrated capillaries and funnels, Monte Carlo and "
        "random-packing algorithms (Lubachevsky-Stillinger, Jodrey-Tory, random sequential addition) for "
        "packing density from a particle-size distribution, and image-based workflows that turn SEM or "
        "micro-CT particle images into DEM particles? How well do these reproduce measured bulk and tapped "
        "density and the mass released by a single tap? How are irregular particle shapes (salt crystals, "
        "water-atomized or milled powders) represented (multi-sphere, superquadric, polyhedral DEM), and how "
        "much does shape matter compared with cohesion?")),
    "q9_ml_surrogate_simulators": ("LITERATURE", (
        "What machine-learned surrogate simulators exist for granular flow (graph-network simulators such as "
        "GNS and 'learning to simulate', neural operators, Gaussian-process or neural-network emulators of DEM "
        "outputs), how are they trained from DEM data, how well do they generalize to new geometries and contact "
        "parameters, and have they been used for inverse problems such as estimating friction or cohesion from "
        "observed flow? Which open-source implementations and pretrained models exist?")),
}


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


def dispatch(keys: list[str] | None = None) -> None:
    from edison_client import JobNames

    client = _client_retry()
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    for key, (job, text) in QUERIES.items():
        if keys and key not in keys:
            continue
        if key in ids:
            print(f"{key}: already dispatched ({ids[key]['task_id']})")
            continue
        query = CONTEXT + text
        task_id = None
        for attempt in range(6):
            try:
                task_id = str(client.create_task({"name": getattr(JobNames, job), "query": query, "tags": [TAG]}))
                break
            except Exception as exc:  # noqa: BLE001 - the login endpoint intermittently returns 403
                print(f"{key}: attempt {attempt + 1} failed ({type(exc).__name__}); retrying", flush=True)
                time.sleep(15 * (attempt + 1))
                client = _client_retry()
        if task_id is None:
            print(f"{key}: NOT dispatched", flush=True)
            continue
        ids[key] = {"task_id": task_id, "job": job, "job_name": getattr(JobNames, job).value,
                    "dispatched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "query": query}
        IDS.write_text(json.dumps(ids, indent=2) + "\n")
        print(f"{key}: {job} -> {task_id}", flush=True)


def _status(client, task_id: str) -> str:
    return str(client.get_task(task_id=task_id).status)


def status() -> dict[str, str]:
    client = _client_retry()
    ids = json.loads(IDS.read_text())
    out = {}
    for key, ent in ids.items():
        try:
            out[key] = _status(client, ent["task_id"])
        except Exception as exc:  # noqa: BLE001 - report and continue
            out[key] = f"error: {type(exc).__name__}"
        print(f"{key}: {out[key]}", flush=True)
    return out


def _dump(task) -> dict:
    if hasattr(task, "model_dump"):
        return task.model_dump(mode="json")
    return json.loads(json.dumps(task, default=str))


def fetch() -> None:
    client = _client_retry()
    ids = json.loads(IDS.read_text())
    for key, ent in ids.items():
        task = client.get_task(task_id=ent["task_id"], verbose=True)
        data = _dump(task)
        st = str(task.status)
        (HERE / f"{key}.task.json").write_text(json.dumps(data, indent=2, default=str) + "\n")
        answer = ""
        for path in (("environment_frame", "state", "state", "response", "answer", "formatted_answer"),
                     ("environment_frame", "state", "state", "response", "answer", "answer"),):
            cur = data
            try:
                for p in path:
                    cur = cur[p]
                if isinstance(cur, str) and cur.strip():
                    answer = cur
                    break
            except (KeyError, TypeError):
                continue
        if not answer:
            for k in ("formatted_answer", "answer"):
                v = getattr(task, k, None) or data.get(k)
                if isinstance(v, str) and v.strip():
                    answer = v
                    break
        header = (f"# Edison {ent['job']} task `{ent['task_id']}` ({key})\n\n"
                  f"Status: {st}. Dispatched {ent['dispatched_utc']}.\n\n## Query\n\n{ent['query']}\n\n## Answer\n\n")
        (HERE / f"{key}.answer.md").write_text(header + (answer or "_(no answer text in the task record)_") + "\n")
        ent["status"] = st
        ent["fetched_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        print(f"{key}: {st}, answer {len(answer)} chars", flush=True)
    IDS.write_text(json.dumps(ids, indent=2) + "\n")


def wait(poll_s: int = 120, max_s: int = 3300) -> None:
    client = _client_retry()
    ids = json.loads(IDS.read_text())
    start = time.time()
    while True:
        states = {}
        for key, ent in ids.items():
            try:
                states[key] = _status(client, ent["task_id"])
            except Exception as exc:  # noqa: BLE001
                states[key] = f"error: {type(exc).__name__}"
        print(f"[{int(time.time() - start)} s] " + ", ".join(f"{k.split('_')[0]}={v}" for k, v in states.items()),
              flush=True)
        if all(v in DONE for v in states.values()):
            break
        if time.time() - start > max_s:
            print("not all finished; fetching what is there", flush=True)
            break
        time.sleep(poll_s)
    fetch()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "dispatch":
        dispatch(sys.argv[2:] or None)
    elif cmd == "status":
        status()
    elif cmd == "wait":
        wait(max_s=int(sys.argv[2]) if len(sys.argv) > 2 else 3300)
    elif cmd == "fetch":
        fetch()
    else:
        raise SystemExit(__doc__)

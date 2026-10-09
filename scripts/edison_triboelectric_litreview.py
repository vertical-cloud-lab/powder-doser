"""Submit / wait on the issue-158 triboelectric-charging literature review at Edison.

Follow-up to the issue-158 digital-twin review (task ``674609d3-…``), which
flagged triboelectric charging as unmodelled in every mainstream granular /
robotics engine. This single high-effort literature task
(``job-futurehouse-paperqa3-high``) asks which published charge-transfer
models exist, which have already been implemented in DEM / CFD-DEM codes, and
what it would take to import one into a digital-twin engine for the doser
(issue #158, comment by @lbwinters).

Uses the ``edison-client`` SDK, whose PROD stage already points at the
Edison Scientific platform endpoint (``https://api.platform.edisonscientific.com``).
Authentication is via the ``EDISON_PLATFORM_API_KEY`` environment variable
(``EDISON_API_KEY`` accepted as a fallback for parity with the older
``scripts/edison_submit.py``); the key is never printed.

Artifacts land in ``docs/edison/triboelectric_artifacts/`` following the same
per-key triplet convention as ``hardware/edison_artifacts/``:

* ``triboelectric_litreview._task_id.json`` — task id, written at submit time
  so an interrupted session can be resumed by a follow-up run.
* ``triboelectric_litreview.task.json`` — full task object from the API.
* ``triboelectric_litreview.task.verbose.json`` — verbose trajectory payload.
* ``triboelectric_litreview.answer.md`` — the assistant's answer in markdown.
* ``triboelectric_litreview.references.md`` — formatted answer + references.

plus the human-readable verbatim doc
``docs/edison/literature-high-triboelectric-charging-models.md`` (same
``Question:`` + answer layout as the other files in ``docs/edison/``).

Usage (from the repo root)::

    python scripts/edison_triboelectric_litreview.py submit
    python scripts/edison_triboelectric_litreview.py wait   # poll loop + fetch
    python scripts/edison_triboelectric_litreview.py fetch  # fetch once, no wait
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames, TaskRequest

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = REPO_ROOT / "docs" / "edison" / "triboelectric_artifacts"
KEY = "triboelectric_litreview"
TASK_ID_FILE = ARTIFACT_DIR / f"{KEY}._task_id.json"
VERBATIM_DOC = (
    REPO_ROOT / "docs" / "edison" / "literature-high-triboelectric-charging-models.md"
)

TERMINAL_STATUSES = {"success", "fail", "failed", "cancelled", "error"}
POLL_SECONDS = 240

QUERY = """\
We are building an open-hardware powder-dosing platform for a self-driving
"digital alloy" laboratory and want to add **triboelectric (contact)
charging** to a physics-based digital twin that we use to iterate hardware
designs in silico (geometry and motion candidates ranked by a Bayesian
optimiser before anything is 3D-printed). A prior literature review we
commissioned concluded that none of the mainstream granular / robotics
simulation engines (LIGGGHTS, MercuryDPM, Yade, Project Chrono, Altair EDEM,
Ansys Rocky, NVIDIA Isaac Sim/Lab PhysX position-based-dynamics particles as
used by MATTERIX, GranularGym, MPM / differentiable solvers) ships a
calibrated tribocharging capability, so simulated design rankings may be
wrong whenever charging matters. Please verify or correct that claim. Our
core question: **can published charge models developed by others be
imported into such an engine, and what would that take?**

**System context.**
- Devices: (1) an auger doser — an FDM-printed Archimedes screw in a printed
  hopper (PLA / PETG / nylon, possibly carbon-loaded ESD-safe filament),
  NEMA-11 stepper, ERM vibration motor and solenoid tapper as flow aids,
  dispensing into a vial or crucible on an analytical / precision balance in
  a closed gravimetric loop (targets roughly 10 mg to 10 g); (2) a
  gantry-mounted passive "powder excavator": a printed half-cylinder trough
  that scoops from a powder bed and pours by cam-driven tilt; a grounded
  copper-tape lining has been proposed as a charging mitigation.
- Powders: gas-atomised metal powders for additive manufacturing, anchored
  by AlSi10Mg (D50 about 35 um, native Al2O3 skin) and high-purity Si
  (native SiO2), later a broader palette (Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn,
  Zr, Nb, Mo, W or Ta); also cohesive inorganic powders (catalysts,
  ceramics, salts) and occasionally organics / polymers.
- Environment: ambient lab air now (variable relative humidity), later a dry
  argon glovebox (ppm-level H2O), which changes both charge dissipation and
  the gas-discharge limit on particle and wall charge.

Please perform a high-effort literature search and synthesis covering:

1. **Catalogue of particle-scale charge-transfer models usable in
   simulation.** For each family — condenser / capacitor models based on
   contact potential (work-function) difference and contact area (e.g.
   Matsusaka, Masuda, Matsuyama, Ghadiri), charge-relaxation /
   gas-discharge-limited models (Matsuyama and Yamamoto; Paschen-limited),
   surface-state and effective-work-function models for insulators (Lowell
   and Rose-Innes; Castle and Schein), trapped-electron / high-energy-electron
   models for same-material and size-dependent bipolar charging (Lacks and
   co-workers), ion- and water-mediated transfer and humidity models
   (McCarty and Whitesides), material-transfer, mosaic / patch and stochastic
   models (Baytekin and Grzybowski; Haeberle et al.; Waitukaitis and
   co-workers; Apodaca), and flexoelectric models (Mizzi and Marks) — give
   the governing equation(s), the per-contact inputs a DEM code would need
   to supply (normal / tangential overlap, contact area and its time
   history, impact velocity, contact duration, sliding or rolling distance,
   initial charges, local electric field), the material parameters and how
   they are measured, the regimes where the model has been validated against
   experiment (single-impact rigs, Faraday-cup charge-to-mass, acoustic
   levitation), and its known failure modes. Distinguish metal-metal,
   metal-insulator (metal powder against printed polymer walls) and
   insulator-insulator contacts, and say what is known specifically for
   oxide-skinned metal powders (Al alloys, Si, Ti) and for FDM polymers
   (PLA, PETG, nylon, ABS, conductive / ESD filaments).

2. **Existing simulation implementations: what can actually be imported.**
   Survey DEM and CFD-DEM studies that implemented tribocharging together
   with electrostatic forces, e.g. vibratory feeders (Laurentie et al.),
   rotating drums and blenders (Pei, Wu and Adams; Naik, Chaudhuri et al.,
   including multiscale DFT + DEM), pneumatic conveying (Korevaar et al.;
   Grosshans and Papalexandris), vibrated and fluidised beds (Kolehmainen,
   Ozel, Sundaresan et al., including humidity effects), polyethylene
   reactors (Konopka and Kosek), particle-surface sliding / rolling charging
   (Ireland), granular-gas and same-material charging (Duff and Lacks; Kok
   and Lacks), powder spreading in metal additive manufacturing, and capsule
   / dosator filling or other pharmaceutical powder handling. For each give:
   the host code (EDEM API, LIGGGHTS / CFDEM, LAMMPS, MFiX-DEM, MercuryDPM,
   Yade, Rocky, in-house), whether source code, user-defined functions or
   plugins are publicly available, how electrostatic forces were computed
   (direct pairwise sum with cut-off, Ewald / PPPM, P3M or hybrid near/far
   field schemes such as Kolehmainen et al. 2016, fast multipole,
   particle-in-cell Poisson solve), how walls were treated (grounded
   conductors via image charges vs. charge-accumulating insulating walls,
   wall-charge saturation and leakage), and the quantitative agreement with
   experiment (charge-to-mass ratio, charge distribution, bipolar charging,
   wall sheeting / adhered mass).

3. **Engine extensibility for hosting an imported charge model.** For each
   candidate host — open-source DEM (LIGGGHTS-PUBLIC fixes, contact-model
   templates and per-atom properties; the LAMMPS GRANULAR package combined
   with charge-carrying atom styles and Coulomb / kspace solvers; MercuryDPM
   species and interaction classes, including any existing charged species;
   Yade Law2 functors; Project Chrono DEM-Engine (DEME) JIT-compiled custom
   force models with per-particle / per-contact "wildcard" state; MFiX-DEM),
   commercial DEM (Altair EDEM C++ API custom contact models, particle body
   forces and custom properties; Ansys Rocky API / modules) and GPU robotics
   or differentiable simulators (NVIDIA Isaac Sim/Lab PhysX particle systems
   as used by MATTERIX, NVIDIA Warp / Newton, Genesis, Taichi / MPM) —
   assess (a) support for a per-particle charge state that persists and
   updates at every contact, (b) per-contact history for contact-area or
   contact-time integrals, (c) long-range or field-based force evaluation and
   its cost at 1e5 to 1e7 particles, (d) GPU support, (e) charge state on
   moving STL wall meshes, and (f) published precedent for electrostatics in
   that engine. Where particle-level physics is impractical (position-based
   robotics engines), discuss reduced-order alternatives, e.g. a
   MATTERIX-style "semantics" layer that tracks lumped charge on containers
   and surfaces with an ODE and applies effective adhesion, retained-mass or
   force terms.

4. **Numerical and scaling issues.** Time-step constraints; cut-off errors
   for Coulomb and polarisation / dielectrophoretic forces; induced (image)
   charge and polarisation of conducting metal particles and charge sharing
   between conducting particles in contact; dielectric walls; how charge
   should be scaled under coarse-graining (preserving charge-to-mass ratio
   vs. Coulomb-to-gravity or Coulomb-to-van-der-Waals force ratios) and any
   published coarse-graining rules for charged DEM; stochastic charge
   variance; and whether any differentiable implementations exist.

5. **Effects most relevant to gravimetric dosing.** Evidence on how charging
   changes dose accuracy and precision: electrostatic adhesion and wall
   build-up (retained mass in hoppers, screws, scoops, vials),
   arching / agglomeration, flow-rate drift over repeated doses as polymer
   walls accumulate charge, particle scattering at the outlet, and
   **electrostatic weighing errors** on analytical and micro balances caused
   by charged powder or containers (image forces to the pan or draft shield,
   ionizer mitigation). Has anyone modelled or simulated the balance-reading
   error caused by charge, and how large is it at milligram-to-gram scale?

6. **Calibration and validation protocols.** Low-cost and standard
   measurements to parameterise and validate an imported charge model:
   Faraday-cup charge-to-mass of dispensed doses, electrometers /
   nanocoulomb meters, electrostatic field meters on hoppers, Kelvin-probe
   work-function measurements of powders and printed polymers, surface
   resistivity of printed parts, single-particle impact or sliding rigs,
   shaker or drum tribochargers, humidity and atmosphere control; inverse
   calibration of charging parameters with Bayesian optimisation or
   ACCES-style CMA-ES; parameter identifiability and transferability
   between geometries.

7. **Mitigation levers that a twin could evaluate.** Conductive / ESD
   filaments or coatings, grounded metal liners (e.g. copper tape), surface
   texture, material choices that minimise contact-potential difference,
   ionizers, humidity control, vibration / tapping schedules — and whether
   simulations have successfully ranked such levers against experiment.

8. **Recommendation.** Given the devices and powders above, recommend the
   most credible path to adding charging to our twin: which charge model(s)
   to import, into which engine, how to compute the fields, what to
   calibrate first, the expected implementation effort and run-time cost per
   design evaluation on a single modern GPU, the expected fidelity, and the
   top risks where simulation would still misrank designs.

Provide comparative tables (models x inputs / parameters / validation;
engines x extensibility / per-particle state / electrostatics / GPU /
licence / precedent). Ground every claim in cited references; prefer
peer-reviewed sources, but include preprints, theses and credible software
documentation where peer-reviewed work is sparse, and explicitly flag where
the literature is silent.
"""


def make_client() -> EdisonClient:
    """Build an EdisonClient authenticated from the environment."""
    api_key = os.environ.get("EDISON_PLATFORM_API_KEY") or os.environ.get(
        "EDISON_API_KEY"
    )
    if not api_key:
        sys.exit("EDISON_PLATFORM_API_KEY env var is not set")
    return EdisonClient(api_key=api_key)


def submit() -> None:
    """Submit the literature task and persist its task id."""
    client = make_client()
    task_id = client.create_task(
        TaskRequest(name=JobNames.LITERATURE_HIGH, query=QUERY)
    )
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    TASK_ID_FILE.write_text(
        json.dumps(
            {"task_id": str(task_id), "job_name": JobNames.LITERATURE_HIGH.value},
            indent=2,
        )
        + "\n"
    )
    print(f"submitted triboelectric lit review: task_id={task_id}")
    print(f"task id written to {TASK_ID_FILE.relative_to(REPO_ROOT)}")


def _load_task_id() -> str:
    if not TASK_ID_FILE.exists():
        sys.exit(f"{TASK_ID_FILE} not found -- run the submit subcommand first")
    return json.loads(TASK_ID_FILE.read_text())["task_id"]


def fetch() -> str:
    """Fetch the task once and write the artifact files. Returns status.

    The answer lives on the *non-verbose* ``PQATaskResponse`` (``answer`` /
    ``formatted_answer``); the verbose variant returns the raw environment
    frame without those convenience fields, so both are fetched and saved.
    """
    client = make_client()
    task_id = _load_task_id()
    task = client.get_task(task_id=task_id)
    status = str(getattr(task, "status", "?"))
    print(f"status: {status}", flush=True)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    dump = task.model_dump(mode="json", exclude_none=True)
    (ARTIFACT_DIR / f"{KEY}.task.json").write_text(
        json.dumps(dump, indent=2, default=str) + "\n"
    )
    verbose = client.get_task(task_id=task_id, verbose=True)
    (ARTIFACT_DIR / f"{KEY}.task.verbose.json").write_text(
        json.dumps(verbose.model_dump(mode="json", exclude_none=True), indent=2,
                   default=str)
        + "\n"
    )

    answer = getattr(task, "answer", None)
    formatted = getattr(task, "formatted_answer", None)
    if answer:
        (ARTIFACT_DIR / f"{KEY}.answer.md").write_text(str(answer).rstrip() + "\n")
    if formatted:
        (ARTIFACT_DIR / f"{KEY}.references.md").write_text(
            str(formatted).rstrip() + "\n"
        )
    if formatted or answer:
        # ``formatted_answer`` already opens with "Question: <query>", the
        # same layout as the other verbatim docs in docs/edison/.
        VERBATIM_DOC.write_text(str(formatted or answer).rstrip() + "\n")
        print(f"artifacts written under {ARTIFACT_DIR.relative_to(REPO_ROOT)}")
    else:
        print("(no answer body yet)")
    return status


def wait() -> None:
    """Block until the task reaches a terminal status, then fetch artifacts.

    The poll loop lives *inside* this single Python process (per CLAUDE.md:
    background polling dies with the runner, and the harness blocks the
    shell ``sleep`` builtin — Python-side ``time.sleep`` is fine).
    """
    client = make_client()
    task_id = _load_task_id()
    while True:
        task = client.get_task(task_id=task_id)
        status = str(getattr(task, "status", "?"))
        print(f"{time.strftime('%H:%M:%S')} status: {status}", flush=True)
        if status in TERMINAL_STATUSES:
            break
        time.sleep(POLL_SECONDS)
    fetch()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("submit")
    sub.add_parser("wait")
    sub.add_parser("fetch")
    args = parser.parse_args()
    if args.cmd == "submit":
        submit()
    elif args.cmd == "wait":
        wait()
    elif args.cmd == "fetch":
        fetch()


if __name__ == "__main__":
    main()

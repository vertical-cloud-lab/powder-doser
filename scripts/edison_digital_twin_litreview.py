"""Submit / wait on the issue-158 digital-twin literature review at Edison.

One high-effort literature task (``job-futurehouse-paperqa3-high``) asking for
the state of the art in digital-twin / physics-simulation environments for
iterating powder-dosing hardware designs in silico (issue #158, prompted by
MATTERIX, Darvish et al., *Nature Computational Science* 2025).

Uses the ``edison-client`` SDK, whose PROD stage already points at the
Edison Scientific platform endpoint (``https://api.platform.edisonscientific.com``).
Authentication is via the ``EDISON_PLATFORM_API_KEY`` environment variable
(``EDISON_API_KEY`` accepted as a fallback for parity with the older
``scripts/edison_submit.py``); the key is never printed.

Artifacts land in ``docs/edison/digital_twin_artifacts/`` following the same
per-key triplet convention as ``hardware/edison_artifacts/``:

* ``digital_twin_litreview._task_id.json`` — task id, written at submit time
  so an interrupted session can be resumed by a follow-up run.
* ``digital_twin_litreview.task.json`` — full task object from the API.
* ``digital_twin_litreview.answer.md`` — the assistant's answer in markdown.
* ``digital_twin_litreview.references.md`` — formatted answer + references.

plus the human-readable verbatim doc
``docs/edison/literature-high-digital-twin-simulation.md`` (same
``Question:`` + answer layout as the other files in ``docs/edison/``).

Usage (from the repo root)::

    python scripts/edison_digital_twin_litreview.py submit
    python scripts/edison_digital_twin_litreview.py wait   # poll loop + fetch
    python scripts/edison_digital_twin_litreview.py fetch  # fetch once, no wait
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
ARTIFACT_DIR = REPO_ROOT / "docs" / "edison" / "digital_twin_artifacts"
KEY = "digital_twin_litreview"
TASK_ID_FILE = ARTIFACT_DIR / f"{KEY}._task_id.json"
VERBATIM_DOC = REPO_ROOT / "docs" / "edison" / "literature-high-digital-twin-simulation.md"

TERMINAL_STATUSES = {"success", "fail", "failed", "cancelled", "error"}
POLL_SECONDS = 240

QUERY = """\
We are building an open-hardware powder-dosing platform for self-driving
laboratories (a digital-alloy lab dosing metal powders such as high-purity Si
and AlSi10Mg into crucibles). Two devices are in play:

1. An **auger doser**: an FDM-printed Archimedes screw inside a printed
   hopper, driven by a NEMA-11 stepper, with an ERM vibration motor and a
   solenoid tapper as flow aids, controlled by a Raspberry Pi in a
   closed-loop **gravimetric** cycle — dispense, read a laboratory balance,
   trickle to a target mass (targets roughly 10 mg to 10 g).
2. A **"powder excavator"**: a gantry-mounted, actuator-free half-cylinder
   trough on a longitudinal pivot pin that scoops from a bulk powder bed;
   its tilt schedule is programmed purely passively (a fixed cam ramp or a
   peg-in-routed-slot board engaged by gantry motion), with a fixed
   strike-off bar defining the fill volume.

Target powders are dozens of microns in diameter and often cohesive,
hygroscopic, and/or triboelectrically charging. All geometry is authored as
parametric code (CadQuery / OpenSCAD) and exported to STEP/STL for FDM
printing, so candidate designs are cheap to generate but slow to test
physically.

We want to stand up a **digital-twin environment for generative design**: a
physics simulation of the actual dosing task — source powder, the moving
printed parts, and the balance reading (dispensed mass vs. time) — faithful
enough that geometry and motion-schedule candidates can be ranked in silico
(e.g. by a Bayesian optimiser) before anything is printed. The inspiration
is MATTERIX (Darvish et al., *Nature Computational Science* 2025;
arXiv:2601.13232), a GPU-accelerated Isaac-Sim-based digital twin of a
robotic chemistry lab that includes powder and liquid simulation, workflow
semantics, and sim-to-real transfer.

Please perform a high-effort literature search and synthesis covering:

1. **Simulation methods and engines for device-scale granular flow.**
   Discrete element method (DEM) codes (LIGGGHTS, Yade, MercuryDPM,
   MFiX-DEM, Project Chrono, Altair EDEM, Rocky DEM, Ansys), GPU-resident
   DEM, material point method (MPM), SPH, continuum mu(I)-rheology solvers,
   position-based dynamics, and the granular capabilities of robotics
   simulators (NVIDIA Isaac Sim/Lab + PhysX particles, Genesis, AGX
   Dynamics, MuJoCo, Taichi-based solvers). Compare fidelity, speed,
   licensing, and suitability for cohesive fine powders.

2. **Quantitative fidelity for dosing-like tasks.** DEM studies of screw /
   auger feeders, vibratory channel dosing, hopper discharge, tapping /
   knocking de-bridging, and scoop/bucket digging of cohesive powder. What
   agreement with experiment is actually reported (mass-flow-rate error,
   dose CV, spread mass fraction), and under what calibration effort?

3. **Cohesion modelling and particle-count tractability.** JKR / simplified
   JKR, Edinburgh Elasto-Plastic Adhesion (EEPA), liquid-bridge models;
   coarse-graining / scaled-particle approaches and their validity limits
   when real particles are tens of microns (real particle counts are
   astronomically large); van der Waals, moisture, and electrostatic
   contributions for metal powders specifically (Si, Al alloys, with oxide
   layers).

4. **DEM parameter calibration workflows.** Angle-of-repose, shear-cell /
   FT4 rheometer, tapped-density tests; inverse calibration via Bayesian
   optimisation, surrogate models, or ML; transferability of calibrated
   parameter sets across process geometries; virtual calibration and the
   risk of non-unique parameter sets.

5. **Simulation-in-the-loop design optimisation.** Published examples of
   optimising equipment geometry with granular simulation in the loop
   (hopper / chute / screw / mixer blade / bucket shape optimisation via
   DEM + Bayesian or evolutionary optimisers, surrogate-assisted DEM
   design); differentiable granular simulators (DiffTaichi, NVIDIA Warp,
   gradSim) used for design or control gradients; reported wall-clock cost
   per design evaluation.

6. **Digital twins and sim-to-real for laboratory automation.** Where does
   MATTERIX sit relative to other lab digital twins; robot-learning results
   with granular media (scooping, pouring, trickling policies trained in
   simulation and transferred to hardware); domain randomisation over
   granular parameters; and any work that models the *measurement* side —
   a balance in the loop (settling time, vibration noise, drift) — for
   closed-loop gravimetric dosing.

7. **Recommended stack and gaps.** Given the two devices above, recommend a
   concrete open-source simulation stack (engine + cohesive contact model +
   calibration protocol + optimiser + CAD hand-off via STL/STEP), the
   expected wall-clock per candidate evaluation on a single modern GPU, and
   the top gaps/risks where simulation is unlikely to rank designs
   correctly (e.g. triboelectrics, humidity, FDM surface roughness).

Ground every claim in cited references; prefer peer-reviewed sources, but
include preprints and credible vendor/tool documentation where peer-reviewed
work is sparse. Comparative tables are welcome where tools occupy the same
niche.
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
        json.dumps({"task_id": str(task_id), "job_name": JobNames.LITERATURE_HIGH.value},
                   indent=2)
        + "\n"
    )
    print(f"submitted digital-twin lit review: task_id={task_id}")
    print(f"task id written to {TASK_ID_FILE.relative_to(REPO_ROOT)}")


def _load_task_id() -> str:
    if not TASK_ID_FILE.exists():
        sys.exit(f"{TASK_ID_FILE} not found -- run the submit subcommand first")
    return json.loads(TASK_ID_FILE.read_text())["task_id"]


def fetch() -> str:
    """Fetch the task once and write the artifact triplet. Returns status.

    The answer lives on the *non-verbose* ``PQATaskResponse`` (``answer`` /
    ``formatted_answer``); the verbose variant returns a
    ``TaskResponseVerbose`` whose payload is the raw environment frame
    without those convenience fields, so we deliberately fetch non-verbose.
    """
    client = make_client()
    task_id = _load_task_id()
    task = client.get_task(task_id=task_id)
    status = str(getattr(task, "status", "?"))
    print(f"status: {status}", flush=True)

    dump = task.model_dump(mode="json", exclude_none=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / f"{KEY}.task.json").write_text(
        json.dumps(dump, indent=2, default=str) + "\n"
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
        print(f"status: {status}", flush=True)
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

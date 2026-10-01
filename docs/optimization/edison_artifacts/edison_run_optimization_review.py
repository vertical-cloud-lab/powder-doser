"""Submit the issue-161 controller-optimization question set to Edison
Scientific as a high-effort literature query (LITERATURE_HIGH), then poll
and persist the artifacts.

Follows the repo convention (see ``paper/background/edison_run.py`` and
``hardware/edison_artifacts/edison_run_hardware_review.py``): artifacts are
committed alongside this script as ``<key>.task.json``, ``<key>.answer.md``
and ``<key>.references.md``, plus ``<key>._task_id.json`` written at submit
time so a later session can resume fetching.

Requires the ``EDISON_PLATFORM_API_KEY`` environment variable. Usage::

    python docs/optimization/edison_artifacts/edison_run_optimization_review.py submit
    python docs/optimization/edison_artifacts/edison_run_optimization_review.py wait
    python docs/optimization/edison_artifacts/edison_run_optimization_review.py fetch

``submit`` creates the task and writes ``<key>._task_id.json`` immediately.
``wait`` blocks in-process (``time.sleep`` loop) until the task reaches a
terminal state, then writes all artifacts — run it as a single foreground
call with a long timeout, never in the background.  ``fetch`` writes
artifacts from the task's current state without waiting.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames

OUT_DIR = Path(__file__).resolve().parent
KEY = "optimization_review"

# The verbatim brainstorm from issue #161 that this query is grounded in.
ISSUE_BRAINSTORM = """\
In creating the bang-bang controller followed by a trim method, we have
multiple parameters that are user-defined. Some of these parameters change
with the optimal control algorithm, while some don't. We have some parameters
that are influenced by collected test data and some that are just used because
they seem to make sense. This issue is to explore what can be optimized and
what are our objectives?

Possible optimization objectives:
Bang-bang
- fastest dispensing orientation
- minimize error
PI trim control
- minimize error
Tap trim control
- minimize error

Parameters:
Bang-bang (for speed)
- tilt
- auger rpms
- tap frequency
Bang-bang (for accuracy)
- Q (process noise covariance matrix)
- R (measurement noise matrix)
PI trim control
- KP
- KI

There are many other parameters we could potentially try to optimize, but this
is what I was thinking about for now. I was also thinking of making the
bang-bang a two-step optimization. We could first optimize the control
parameters (tilt, rpm, tapping) for the fastest possible dispensing and then
optimize to minimize the error of this already established configuration. We
have to be wary of including certain parameters in an optimization. For
example, including tilt and RPM's in the optimization to minimize error of the
bang-bang solution would most likely make the system way too slow.
"""

PROMPT = f"""\
We are building an open-source benchtop powder doser for self-driving
laboratories (target application: high-throughput metal-AM alloy discovery,
but validated first on surrogate powders such as xanthan gum). The dispensing
head is an auger/screw conveyor driven by a NEMA-11 stepper (continuously
variable RPM), mounted on a servo that sets the dispensing tilt angle, with a
solenoid tapper (variable tap frequency) and an ERM vibration motor to combat
bridging/ratholing. Mass feedback comes from a laboratory balance under the
receiving vessel; the noisy balance signal is filtered with a Kalman filter
whose process-noise covariance Q and measurement-noise covariance R are
currently hand-set.

The controller is a two-phase gravimetric strategy, analogous to coarse/fine
or bulk/trickle dosing: (1) a "bang-bang" bulk phase runs the auger at a fixed
speed/tilt/tap setting until the filtered mass estimate crosses a cutoff near
the setpoint, then shuts off; (2) a "trim" phase closes the remaining error
either with a PI controller (gains KP, KI) modulating the auger, or with
discrete solenoid taps ("tap trim") that each shake loose a small increment of
powder. Note dispensing is irreversible: overshoot cannot be removed, only a
failed dose discarded.

A team member has brainstormed which user-defined parameters should be tuned
by an optimization campaign and what the objectives should be. Their verbatim
notes:

---
{ISSUE_BRAINSTORM}
---

Please write a literature-grounded review that answers, with citations to
peer-reviewed work (and authoritative vendor/application literature where
peer-reviewed sources are thin):

1. **Objectives.** In published work on gravimetric powder dosing —
   loss-in-weight feeding, pharmaceutical micro-dosing (e.g. Mettler-Toledo
   Quantos, Capsugel Xcelodose, tapping/vibratory capillary dosers), catch
   weighers, and self-driving-lab solid dispensers — what objective functions
   are used to characterize and optimize performance? Cover dosing time /
   throughput, mean absolute or relative error, repeatability (CV/RSD),
   overshoot rate, and minimum dispensable increment. How do published
   systems combine speed and accuracy: weighted scalarization, epsilon-
   constraint ("as fast as possible subject to error < tolerance"), or true
   multi-objective Pareto fronts? Given that overshoot is irreversible in
   powder dispensing, is an asymmetric penalty (penalizing overshoot more
   than undershoot, or deliberately undershooting the bulk phase and trimming
   up) the established practice?

2. **Two-stage vs. joint optimization.** Critique the proposed two-step
   scheme (first optimize tilt / auger RPM / tap frequency for fastest
   dispensing, then freeze those and optimize the accuracy-oriented
   parameters). When does sequential/greedy optimization of coupled
   controller parameters fail? In coarse-to-fine dosing specifically, the
   bulk-phase flow rate at cutoff determines the in-flight mass and
   spillover, so speed parameters directly bound achievable accuracy — how
   does the literature handle this coupling (e.g. optimizing the switchover
   threshold jointly with feed rate, flow-rate-dependent cutoff prediction,
   feedforward of estimated in-flight mass)? Is a constrained formulation
   ("minimize dose time s.t. |error| ≤ tol with x% confidence") preferable
   to two sequential single-objective problems?

3. **Which parameters belong in a black-box optimization at all?** For each
   parameter class, what does the literature recommend:
   (a) Kalman filter Q and R — should these be tuned by black-box
   optimization against dosing error, or identified from data (innovation-
   based/adaptive filtering, autocovariance least squares, offline noise
   characterization of the balance)? What is standard for mass-flow
   estimation in loss-in-weight feeders, where filter lag vs. noise directly
   trades off cutoff timing?
   (b) PI trim gains KP, KI — classical tuning (relay autotuning, IMC,
   Ziegler-Nichols variants) vs. data-driven/Bayesian tuning; what's known
   about controller tuning when the plant is an integrating, stochastic,
   quantized process (powder arrives in discrete avalanches)?
   (c) Mechanical/recipe parameters (tilt, auger RPM, tap frequency) — these
   shape the flow-rate regime; evidence on how auger speed, inclination
   angle, and vibration/tapping parameters affect mean flow rate AND
   flow-rate variability (pulsation, avalanching) for cohesive vs.
   free-flowing powders.
   (d) Structural parameters often forgotten: bulk→trim switchover
   threshold, trim tolerance band, balance settling wait — are these more
   impactful than the listed ones?

4. **Optimization algorithms for hardware-in-the-loop tuning.** Survey
   Bayesian optimization of controller parameters on physical systems where
   each evaluation is an expensive, stochastic real experiment: multi-
   objective BO (e.g. qNEHVI/EHVI) for speed-accuracy trade-offs, constrained
   and safe BO (e.g. SafeOpt) to avoid spills/jams, handling heteroscedastic
   noise and replication, typical evaluation budgets, and contextual /
   transfer approaches so a campaign tuned on one powder transfers to another
   (powder properties as context variables). Include examples from
   self-driving labs tuning their own hardware.

5. **Powder-physics limits.** What does the literature say about the floor
   on achievable dosing error — minimum stable increment from tapping or
   slow auger rotation (avalanche size statistics), balance noise and
   settling, electrostatics/cohesion effects — and how the optimal
   parameters shift with powder flowability (Hausner ratio, FFC)? This
   bounds what any optimizer can deliver and informs tolerance selection.

6. **Recommended protocol.** Synthesize into a concrete recommendation for
   this system: which parameters to optimize with which objective(s), which
   to identify/tune by other means, which to fix; whether to run screening
   (DOE/sensitivity analysis) before BO; how many replicates per condition
   given stochastic powder flow; and what to log so later campaigns can
   reuse the data. State the single most defensible formulation of the
   optimization problem for this doser.

Structure the answer with the section numbering above.
"""


def make_client() -> EdisonClient:
    api_key = os.environ.get("EDISON_PLATFORM_API_KEY") or os.environ.get(
        "EDISON_API_KEY"
    )
    if not api_key:
        sys.exit("EDISON_PLATFORM_API_KEY env var is not set")
    return EdisonClient(api_key=api_key)


def submit() -> None:
    client = make_client()
    task_data = {
        "name": JobNames.LITERATURE_HIGH,
        "query": PROMPT,
        "tags": ["powder-doser", "issue-161", KEY],
    }
    trajectory_id = client.create_task(task_data)
    print(f"submitted LITERATURE_HIGH: task_id={trajectory_id}", flush=True)
    (OUT_DIR / f"{KEY}._task_id.json").write_text(
        json.dumps({"task_id": str(trajectory_id)}, indent=2) + "\n"
    )


def _load_task_id() -> str:
    return json.loads((OUT_DIR / f"{KEY}._task_id.json").read_text())["task_id"]


def _get_task(client: EdisonClient, task_id: str):
    try:
        return client.get_task(task_id, verbose=True)
    except TypeError:
        return client.get_task(task_id)


def _write_artifacts(task) -> None:
    task_json = task.model_dump(mode="json") if hasattr(task, "model_dump") else task
    (OUT_DIR / f"{KEY}.task.json").write_text(
        json.dumps(task_json, indent=2, default=str) + "\n"
    )
    answer = (
        getattr(task, "formatted_answer", None)
        or getattr(task, "answer", None)
        or ""
    )
    (OUT_DIR / f"{KEY}.answer.md").write_text(str(answer) + ("\n" if answer else ""))
    refs = ""
    env_frame = getattr(task, "environment_frame", None) or {}
    if isinstance(env_frame, dict):
        refs = (
            env_frame.get("state", {})
            .get("state", {})
            .get("response", {})
            .get("answer", {})
            .get("references", "")
            or ""
        )
    if not refs:
        for attr in ("references", "citations"):
            v = getattr(task, attr, None)
            if v:
                refs = str(v)
                break
    (OUT_DIR / f"{KEY}.references.md").write_text(refs + ("\n" if refs else ""))
    print(f"wrote artifacts to {OUT_DIR}", flush=True)


def wait() -> None:
    client = make_client()
    task_id = _load_task_id()
    while True:
        task = _get_task(client, task_id)
        status = str(getattr(task, "status", "?"))
        print(f"status: {status}", flush=True)
        if status in {"success", "fail", "failed", "cancelled", "error"}:
            _write_artifacts(task)
            return
        time.sleep(240)


def fetch() -> None:
    client = make_client()
    task = _get_task(client, _load_task_id())
    print(f"status: {getattr(task, 'status', '?')}", flush=True)
    _write_artifacts(task)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "submit"
    if cmd == "submit":
        submit()
    elif cmd == "wait":
        wait()
    elif cmd == "fetch":
        fetch()
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()

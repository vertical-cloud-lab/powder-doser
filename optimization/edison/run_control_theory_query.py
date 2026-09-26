#!/usr/bin/env python3
"""Edison LITERATURE_HIGH: multi-parameter, multi-objective control theory for
the powder doser optimization problem (issue #123).

Asks for the control-theory landscape that generalizes single-loop PID to
multiple simultaneous, independently-actuated, time-varying parameters and
multiple competing objectives, and how that landscape connects to Bayesian
optimization (controller/policy tuning, contextual BO, safe BO), with
grounding in powder feeding / loss-in-weight feeder literature. Polls to
completion and writes the answer + bibliography to query_out/."""
import json
import os
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest
from edison_client.models.rest import ExecutionStatus

HERE = Path(__file__).parent
OUT = HERE / "query_out"
OUT.mkdir(exist_ok=True)

# High-effort literature query: wait 15 min before first poll, then every 5 min.
INITIAL_WAIT_SECONDS = 900
POLL_INTERVAL_SECONDS = 300
TASK_TIMEOUT_SECONDS = 3300


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


QUERY = """We are formulating an optimization/control problem for an open-source, \
low-cost powder doser used for gravimetric metering of dry powders (ultimately metal \
additive-manufacturing feedstocks such as AlSi10Mg, silicon, and stainless steel) in \
an autonomous, self-driving-lab alloy-discovery loop. The rig is an Archimedean auger \
driven by a stepper motor, with a solenoid tapper, a vibration motor for agitation, \
and a servo-controlled tilt, dispensing onto an analytical balance (the balance \
itself has controllable settings, e.g., filtering/integration time). Crucially, the \
actuators are NOT restricted to a single fixed set of parameters per dispense: each \
actuator can be commanded independently and simultaneously AS A FUNCTION OF TIME \
during a dose (e.g., auger speed ramps down as the target mass is approached, \
tapping/vibration duty cycles change between bulk-feed and trickle-feed phases). \
There is also a contextual/exogenous component: hopper/auger fill level, the powder's \
cumulative exposure history to air and humidity, and ambient temperature all shift \
the process dynamics but are observed rather than controlled. Objectives compete: \
dosing accuracy (target +/- 1 mg, stretch +/- 0.1 mg), dispense time / throughput, \
repeatability/precision across doses, and avoidance of overshoot (powder cannot be \
removed once dispensed, so overshoot is asymmetric and effectively a constraint), \
plus secondary concerns like cross-contamination and actuator wear.

Please provide a HIGH-EFFORT literature review of multi-parameter, multi-objective \
control theory as it applies to this setting - i.e., the principled extrapolation of \
single-loop PID control to MULTIPLE simultaneous manipulated variables and MULTIPLE \
competing objectives. Specifically cover, with citations:

1. MIMO / multivariable control foundations: how classical PID generalizes to \
multi-input systems (decentralized/multi-loop PID, relative gain array and loop \
pairing, decoupling, LQR/LQG, H-infinity, and especially model predictive control \
(MPC) as the standard way to handle multiple inputs, multiple objectives, and hard \
constraints simultaneously). When is MPC overkill vs. appropriate for a slow, \
low-dimensional mechatronic dosing rig?

2. Multi-objective control: how competing objectives are actually handled in control \
practice - weighted-sum / scalarized cost functions, lexicographic and prioritized \
objectives, constraint reformulation (treat overshoot as a hard constraint rather \
than an objective), Pareto-front approaches in controller tuning, and multi-objective \
MPC. Include guidance on MINIMIZING the number of objectives (when should an \
objective be demoted to a constraint or folded into a scalarization?).

3. Time-varying / phased control policies: gain scheduling, phase-switched control \
(bulk feed -> trickle feed, as in weighing/filling machines), trajectory \
parameterization of control inputs (piecewise-constant or spline-parameterized input \
profiles), iterative learning control (ILC) and run-to-run / batch-to-batch control \
for repetitive dosing tasks, and event-triggered switching near the setpoint.

4. The bridge to Bayesian optimization: BO for controller/policy tuning (tuning PID \
gains, MPC weights, or parameterized dose profiles from closed-loop performance \
data), multi-objective BO (qNEHVI, ParEGO, etc.) for Pareto exploration of \
accuracy-vs-time tradeoffs, CONTEXTUAL BO (contextual Gaussian processes) for \
conditioning on observed-but-uncontrolled variables (fill level, humidity exposure \
history, temperature), safe BO (e.g., SafeOpt) to respect the no-overshoot \
constraint during learning, time-varying BO for drifting processes, and \
transfer/multi-task BO across powders. Contrast policy-parameter BO ("learn the \
knobs of a feedback law") vs. direct open-loop profile optimization, and discuss \
sample efficiency for hardware experiments where each dose costs real time and \
material.

5. Domain-specific literature: control of loss-in-weight (LIW) feeders and screw/auger \
powder feeders in pharmaceutical continuous manufacturing (refill disturbances, feed \
factor estimation and its dependence on fill level, hopper level as a scheduling \
variable), gravimetric filling/check-weighing machines with coarse/fine feed phases, \
powder flowability effects (humidity, caking, cohesion) on feeder control, and any \
work on ML/BO-driven auto-tuning of powder feeders or self-driving-lab dosing \
(e.g., solid-dispensing in autonomous chemistry platforms).

6. A synthesis/recommendation section: for a low-cost rig with noisy mass feedback \
(balance settling time!), slow sampling, per-experiment cost of minutes, and many \
powders each needing its own configuration - what layered architecture does the \
literature support? E.g., inner loop = simple phase-switched feed profile with \
gravimetric feedback; outer loop = contextual multi-objective BO over the profile's \
parameters per powder; run-to-run/ILC corrections between doses. State which \
objectives the literature suggests keeping (we want as FEW objectives as possible), \
which to convert to constraints, and what the parameter vector for the outer BO loop \
typically looks like in analogous systems. Please include a table mapping our rig's \
knobs/contexts/objectives onto the standard control-theoretic and BO vocabulary.
"""


def main() -> None:
    client = EdisonClient(api_key=_api_key())
    task = TaskRequest(name=JobNames.LITERATURE_HIGH, query=QUERY)
    tid = client.create_task(task)
    print("trajectory_id:", tid, flush=True)
    (OUT / "query.task.json").write_text(
        json.dumps({"trajectory_id": str(tid), "query": QUERY}, indent=2)
    )

    print(f"initial wait {INITIAL_WAIT_SECONDS}s (high-effort literature query)", flush=True)
    time.sleep(INITIAL_WAIT_SECONDS)
    deadline = time.time() + TASK_TIMEOUT_SECONDS
    while time.time() < deadline:
        r = client.get_task(tid)
        status = getattr(r, "status", None)
        print("status:", status, flush=True)
        try:
            terminal = ExecutionStatus(status).is_terminal_state()
        except Exception:
            terminal = status in {"success", "fail", "cancelled", "truncated"}
        if terminal:
            dump = r.model_dump(mode="json")
            answer = (
                getattr(r, "formatted_answer", None)
                or getattr(r, "answer", None)
                or dump.get("formatted_answer")
                or dump.get("answer")
                or ""
            )
            (OUT / "query.answer.md").write_text(answer or "(no answer field)")
            for key in ("bibliography", "references", "context", "used_references"):
                val = dump.get(key)
                if val:
                    (OUT / f"query.{key}.json").write_text(
                        json.dumps(val, indent=2, default=str)
                    )
            print("=== TERMINAL:", status, "===", flush=True)
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    print("TIMEOUT waiting for Edison task", flush=True)


if __name__ == "__main__":
    main()

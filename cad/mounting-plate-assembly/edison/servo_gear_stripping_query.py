"""Dispatch / fetch an Edison Scientific literature query about the
servo-pinion gear stripping seen on the powder-doser mounting-plate tilt
mechanism (issue #65, comment 4802963723).

The mounting plate is tilted by two MG996R hobby servos.  Each servo
drives a 20-tooth 3D-printed pinion that meshes with a 40-tooth gear band
integrated into the mounting-plate hinge lobe (2:1 reduction, module
~0.91 mm, 20 deg pressure angle).  During the Utah AI Convergence '26
poster session the mechanism worked, but after repeated use the teeth on
the servo pinion began to strip.  This script asks Edison how best to
address that failure (metal vs printed gears, module/face-width changes,
mount rigidity / anti-backlash bracket, material choice, etc.).

Usage:
    python3 servo_gear_stripping_query.py dispatch   # create the task, record id
    python3 servo_gear_stripping_query.py fetch       # poll + write the answer

The Edison API key is read from EDISON_API_KEY (falling back to
EDISON_PLATFORM_API_KEY); it is .strip()-ed because the injected secret
can carry a trailing newline that otherwise yields a 403 on /auth/login.
The key is never printed.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_ID_FILE = HERE / "task_id.txt"
ANSWER_MD = HERE / "servo_gear_stripping_answer.md"
RAW_JSON = HERE / "servo_gear_stripping_raw.json"

QUERY = """\
I am designing the tilt mechanism for a benchtop automated powder-dosing \
instrument. A flat "mounting plate" carrying a powder auger is tilted up \
and down about a hinge by TWO hobby servos (TowerPro MG996R, ~10 kg-cm \
stall torque, plastic-gear standard version). Each servo drives a \
20-tooth pinion that meshes with a 40-tooth gear band integrated directly \
into the mounting-plate hinge lobe, giving a 2:1 reduction. The gears are \
spur gears, 20 degree pressure angle, module ~0.91 mm (fine), tip diameter \
~20 mm on the pinion and ~38 mm on the hinge gear, face width ~12 mm. Both \
the pinion and the hinge gear are 3D printed (FDM). The pinion is clamped \
to the MG996R 25-tooth output spline. The mechanism lifts a meaningful \
load: the mounting plate plus a powder auger that becomes significantly \
heavier when fully loaded, so the gears carry a substantial holding and \
lifting torque.

Observed failure: the mechanism worked fine during a one-day demo, but the \
NEXT day, after repeated actuation cycles, the TEETH ON THE SERVO PINION \
began to STRIP. It seems to be a wear/fatigue failure that develops with \
repeated use rather than a single overload event. Separately, the servo \
was only temporarily held in place (taped, not screwed) during testing, \
and when the operator pressed the motor down by hand the gears appeared to \
SKIP less - suggesting the printed motor mount may not be rigid enough, \
letting the pinion and gear separate radially under load so the teeth ride \
up and skip ("tooth jumping"/insufficient mesh).

Please give concrete, prioritized engineering recommendations on how to \
best eliminate this gear stripping. Specifically address:

1. Are METAL gears (e.g., a metal pinion, or upgrading to a metal-gear \
servo such as the MG996R metal-geartrain version, or a machined/POM gear) \
REQUIRED here, or can a well-designed 3D-printed gear survive this duty? \
Quantify roughly: for a printed spur gear at module ~0.9 mm, 20 mm pitch \
diameter, ~12 mm face width in PLA vs PETG vs nylon, what tooth-root \
bending stress / allowable torque can be expected, and how does that \
compare to the MG996R stall torque amplified through the spline?

2. Material: the printed parts are currently FDM. Compare PLA vs PETG vs \
PA (nylon) vs POM for small spur-gear teeth under repeated cyclic loading - \
which best resists tooth stripping / wear, and is switching from PLA to \
PETG (or nylon) likely sufficient, or is metal unavoidable?

3. Mount rigidity: would adding a BRACKET / second bearing support to the \
servo-mount so the motor cannot deflect (maintaining true center distance \
and full tooth engagement) meaningfully reduce skipping/stripping? How \
important is constraining center distance and preventing radial separation \
versus the absolute tooth strength? Best practices for rigidly mounting a \
hobby servo driving a load-bearing gear (screw-down vs tape, outboard \
bearing on the gear shaft, anti-backlash).

4. Geometry: would a coarser module (fewer, larger teeth), wider face \
width, larger pinion (more teeth, avoiding undercut on the 20T pinion), \
or a different reduction help the printed teeth survive? Any quick design \
changes with high payoff.

5. Any alternative to spur-gear drive for a low-speed, high-torque, \
intermittent tilt actuator at this scale that would be more robust \
(e.g., worm drive / self-locking, lever arm + linear actuator, larger \
servo, geared stepper) - briefly.

Prioritize the cheapest / fastest fixes first (material swap, mount \
bracket, geometry tweak) and clearly state when metal becomes necessary.
"""


def _client():
    from edison_client import EdisonClient

    key = (os.environ.get("EDISON_API_KEY")
           or os.environ.get("EDISON_PLATFORM_API_KEY"))
    if not key:
        sys.exit("No EDISON_API_KEY / EDISON_PLATFORM_API_KEY in environment.")
    return EdisonClient(api_key=key.strip())


def dispatch() -> str:
    from edison_client import JobNames, TaskRequest

    client = _client()
    task = TaskRequest(name=JobNames.LITERATURE_HIGH, query=QUERY)
    task_id = client.create_task(task)
    task_id = str(task_id)
    TASK_ID_FILE.write_text(task_id + "\n")
    print(f"Dispatched LITERATURE_HIGH task: {task_id}")
    return task_id


def fetch(timeout_s: int = 1800, poll_s: int = 60) -> None:
    from edison_client.models.rest import ExecutionStatus

    if not TASK_ID_FILE.exists():
        sys.exit("No task_id.txt - run `dispatch` first.")
    task_id = TASK_ID_FILE.read_text().strip()
    client = _client()

    deadline = time.time() + timeout_s
    resp = None
    while True:
        resp = client.get_task(task_id)
        status = getattr(resp, "status", None)
        try:
            terminal = ExecutionStatus(status).is_terminal_state()
        except Exception:
            terminal = str(status) in {"success", "fail", "cancelled", "truncated"}
        print(f"task {task_id} status={status}")
        if terminal or time.time() > deadline:
            break
        time.sleep(poll_s)

    dump = resp.model_dump()
    RAW_JSON.write_text(json.dumps(dump, indent=2, default=str))

    answer = (dump.get("formatted_answer")
              or dump.get("answer")
              or "")
    if not answer:
        env = dump.get("environment_frame") or {}
        try:
            answer = env["state"]["state"]["answer"]
        except Exception:
            answer = ""

    header = (
        "# Edison feedback: servo-pinion gear stripping (issue #65)\n\n"
        f"- Job type: LITERATURE_HIGH\n- Task id: `{task_id}`\n"
        f"- Status: {getattr(resp, 'status', 'unknown')}\n\n"
        "Query asked how best to stop the 3D-printed servo-pinion teeth from "
        "stripping on the MG996R-driven mounting-plate tilt gears "
        "(metal vs printed gears, PLA/PETG/nylon, mount-bracket rigidity, "
        "gear geometry). Full query text in "
        "`servo_gear_stripping_query.py`.\n\n---\n\n"
    )
    ANSWER_MD.write_text(header + (answer or "_(no answer text returned)_\n"))
    print(f"Wrote {ANSWER_MD} ({len(answer)} chars of answer).")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dispatch"
    if cmd == "dispatch":
        dispatch()
    elif cmd == "fetch":
        fetch()
    else:
        sys.exit(f"unknown command {cmd!r} (use dispatch|fetch)")

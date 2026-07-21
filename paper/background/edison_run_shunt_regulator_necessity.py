#!/usr/bin/env python3
"""Edison Scientific ``LITERATURE_HIGH`` runner: is the shunt regulator (SR1)
necessary on the powder-doser control board?

Dispatched for @sgbaird's PR #76 request
(https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-5005495385)
to back the engineering assessment of whether the Pololu #3776 shunt regulator
across the +12 V rail is required, with evidence on stepper-motor regenerative
overvoltage, solenoid flyback recirculation, hobby-servo back-driving, and
wall-adapter (non-sinking) supplies. The exact prompt is embedded verbatim so
the script is a self-contained record of what was sent. Outputs land in
``paper/background/edison_artifacts/``:

* ``<key>.task.json``  -- full ``TaskResponse.model_dump()`` from Edison.
* ``<key>.answer.md``  -- the rendered ``formatted_answer`` (or ``answer``).
* ``<key>.references.md`` -- the standalone numbered references list.

Run with ``EDISON_API_KEY`` (or ``EDISON_PLATFORM_API_KEY``) set::

    pip install edison_client
    python paper/background/edison_run_shunt_regulator_necessity.py            # block until done
    python paper/background/edison_run_shunt_regulator_necessity.py --dispatch # create task, save id
    python paper/background/edison_run_shunt_regulator_necessity.py --fetch-once  # poll saved id once

The split dispatch/fetch modes exist so a CI session can dispatch early, keep
working, and poll in the foreground (never in the background — the runner dies
with the job). A high-effort literature query takes roughly 20-40 minutes.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from edison_client import EdisonClient, JobNames

KEY = "shunt_regulator_necessity"
TAG = "powder-doser-grant"
PILLAR_TAG = "electrical-pcb"

QUERY = (
    "Assess, with quantitative evidence from vendor application notes and "
    "peer-reviewed / arXiv literature, whether a SHUNT REGULATOR (overvoltage "
    "clamp) is necessary on the 12 V supply rail of the following small "
    "lab-automation motor-control board, or whether bulk capacitance alone (or a "
    "TVS diode) suffices.\n\n"
    "SYSTEM: A 12 V wall adapter feeds a 2.1 mm barrel jack (an AC-DC adapter "
    "CANNOT SINK current). On the +12 V rail sit: (1) a Pololu Tic T500 stepper "
    "controller (MP6500 driver, 4.5-35 V absolute max) driving a small NEMA-11 "
    "bipolar stepper (~1 A/phase current limit) that turns a low-inertia powder "
    "auger at modest speeds; (2) a TI DRV8871 H-bridge (45 V abs max, internal "
    "current regulation, synchronous recirculation) driving a 12 V frame solenoid "
    "(~18 ohm, ~0.65 A) used as a vibratory/knock actuator; (3) a Pololu D24V22F5 "
    "5 V buck regulator input (36 V max); (4) a single ~100 uF electrolytic bulk "
    "capacitor; and (5) the part in question, a Pololu #3776 shunt regulator "
    "board (TL431-based comparator switching a power resistor across the rail to "
    "clamp overvoltage, ~9 W dissipation class) wired across +12 V / GND. The 5 V "
    "buck output powers two MG996R-class hobby servos that raise/lower a tilting "
    "mounting plate through a hinge (the servos can be mechanically back-driven, "
    "e.g. if the tilt platform is slammed down deliberately to shock powder "
    "loose), plus a Raspberry Pi Pico W. A DRV2605L haptic driver + ERM vibration "
    "motor run from 3.3 V. Future duty cycle: stepper + solenoid + both tilt "
    "servos + haptic motor may all run SIMULTANEOUSLY, with abrupt stops.\n\n"
    "Address specifically:\n"
    "(a) Physics and magnitude of stepper-motor regenerative overvoltage into a "
    "supply that cannot sink current: under what speed/inertia/deceleration "
    "conditions does a bipolar stepper driven by a chopper driver (mixed decay, "
    "e.g. MP6500/DRV8825 class) pump enough energy back to raise the rail "
    "dangerously? Quantified spike measurements or worked energy calculations "
    "from app notes (Pololu's 'understanding destructive LC voltage spikes' and "
    "shunt-regulator documentation, TI, Trinamic/ADI, Allegro, ROHM app notes on "
    "regeneration, load dump, and supply pumping) and papers. How does a "
    "low-inertia direct-driven auger at low RPM compare with the worst cases?\n"
    "(b) Solenoid / inductive-load turn-off: with an H-bridge like the DRV8871 "
    "recirculating flyback energy into the supply rail, how much does a ~0.5 mJ - "
    "few-mJ solenoid dump raise a 12 V rail buffered by ~100 uF, and when is "
    "extra clamping needed? Include worked C*V^2 / L*I^2 energy-balance math.\n"
    "(c) Hobby-servo back-driving and abrupt mechanical shock loads: can "
    "back-driven RC servos (MG996R class) on a buck converter OUTPUT (which "
    "cannot sink) push the 5 V rail up, and what protections are typical? Note "
    "that a shunt regulator on the 12 V INPUT rail does not protect the 5 V "
    "output rail.\n"
    "(d) Simultaneous-operation worst case: does running stepper + solenoid + "
    "servos + ERM at once increase overvoltage risk (e.g. synchronized abrupt "
    "stop / load dump), or mainly droop/brownout risk?\n"
    "(e) Alternatives and their trade-offs: bigger low-ESR bulk electrolytic "
    "(e.g. 470-1000 uF), unidirectional TVS diode sized between 13.5 V standoff "
    "and 35 V clamp, zener + resistor, active clamp/brake circuits, ideal-diode "
    "load-dump protection - versus the TL431-style switched-resistor shunt "
    "regulator. Which are appropriate at this power level and why?\n"
    "(f) Verdict for THIS board: given the Tic T500's 35 V max, the DRV8871's "
    "45 V max, the buck's 36 V max, a 13.2 V-class shunt clamp, one 100 uF cap, "
    "a low-inertia NEMA-11 auger, and a wall adapter that cannot sink - is the "
    "shunt regulator necessary, cheap insurance worth keeping, or removable? "
    "State the failure scenarios it does and does not protect against, and any "
    "conditions (higher supply voltage, larger motor, added flywheel/inertia, "
    "battery vs adapter) that would change the answer. Cite vendor documentation "
    "plus ~8-15 recent peer-reviewed or arXiv sources where available."
)


def _api_key() -> str:
    for name in ("EDISON_API_KEY", "EDISON_PLATFORM_API_KEY"):
        val = os.environ.get(name)
        if val:
            return val
    raise SystemExit(
        "Set EDISON_API_KEY (or EDISON_PLATFORM_API_KEY) before running this script."
    )


OUT_DIR = Path(__file__).parent / "edison_artifacts"
TASK_ID_FILE = OUT_DIR / f"{KEY}.task_id"


def _extract(data: dict) -> tuple[str, str]:
    for key in ("formatted_answer", "answer"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val, data.get("references") or ""
    try:
        answer = data["environment_frame"]["state"]["state"]["response"]["answer"]
    except (KeyError, TypeError):
        return "", ""
    if isinstance(answer, dict):
        formatted = answer.get("formatted_answer") or answer.get("answer") or ""
        return formatted, answer.get("references") or ""
    if isinstance(answer, str):
        return answer, ""
    return "", ""


def _write_artifacts(data: dict) -> None:
    (OUT_DIR / f"{KEY}.task.json").write_text(json.dumps(data, default=str, indent=2))
    formatted, references = _extract(data)
    (OUT_DIR / f"{KEY}.answer.md").write_text(formatted)
    (OUT_DIR / f"{KEY}.references.md").write_text(references)
    print(
        f"  {KEY}: status={data.get('status')} "
        f"answer_chars={len(formatted)} refs_chars={len(references)}",
        flush=True,
    )
    print(f"Wrote artifacts to {OUT_DIR}", flush=True)


def dispatch() -> None:
    client = EdisonClient(api_key=_api_key())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    task = {
        "name": JobNames.LITERATURE_HIGH,
        "query": QUERY,
        "tags": [TAG, PILLAR_TAG, KEY],
    }
    task_id = client.create_task(task)
    TASK_ID_FILE.write_text(str(task_id) + "\n")
    print(f"Dispatched LITERATURE_HIGH task {task_id} (saved to {TASK_ID_FILE})",
          flush=True)


def fetch_once() -> int:
    """Poll the saved task once. Exit 0 when terminal (artifacts written),
    3 while still running, 2 on missing id."""
    if not TASK_ID_FILE.exists():
        print(f"No task id at {TASK_ID_FILE}; run --dispatch first.", flush=True)
        return 2
    task_id = TASK_ID_FILE.read_text().strip()
    client = EdisonClient(api_key=_api_key())
    result = client.get_task(task_id, verbose=True)
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    status = str(data.get("status", "")).lower()
    print(f"task {task_id}: status={status}", flush=True)
    if status in ("success", "failure", "failed", "cancelled", "error"):
        _write_artifacts(data)
        return 0
    return 3


def main() -> None:
    if "--dispatch" in sys.argv:
        dispatch()
        return
    if "--fetch-once" in sys.argv:
        raise SystemExit(fetch_once())
    # Default: blocking one-shot reproduction path (matches sibling runners).
    client = EdisonClient(api_key=_api_key())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    task = {
        "name": JobNames.LITERATURE_HIGH,
        "query": QUERY,
        "tags": [TAG, PILLAR_TAG, KEY],
    }
    print("Dispatching LITERATURE_HIGH task (this can take 20-40 min)...", flush=True)
    results = client.run_tasks_until_done(
        [task], verbose=True, progress_bar=False, timeout=5400
    )
    result = results[0]
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    _write_artifacts(data)


if __name__ == "__main__":
    main()

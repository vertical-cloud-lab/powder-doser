"""Submit the hardware identification + KiCad schematic package to Edison
Scientific (ANALYSIS query) for an independent review.

This runner follows the convention used elsewhere in the repo: upload the
relevant files first (returns ``data_entry:{uuid}`` URIs), then create an
ANALYSIS task and persist the resulting ``.task.json``, ``.answer.md`` and
``.references.md`` alongside this script under
``hardware/edison_artifacts/``.

Requires the ``EDISON_API_KEY`` environment variable. Usage::

    EDISON_API_KEY=... python hardware/edison_artifacts/edison_run_hardware_review.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from edison_client import EdisonClient, JobNames

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
KEY = "hardware_review"

# Files to upload for review.
ATTACHMENTS = [
    ROOT / "hardware" / "vibration-motor-and-solenoid.md",
    ROOT / "hardware" / "kicad" / "README.md",
    ROOT / "hardware" / "kicad" / "powder_doser_actuators.kicad_sch",
    ROOT / "hardware" / "kicad" / "powder_doser_actuators.pdf",
    ROOT / "hardware" / "kicad" / "powder_doser_actuators.png",
    ROOT / "hardware" / "kicad" / "powder_doser.kicad_sym",
]

PROMPT = """\
Please review the attached hardware design package for an open-source
powder-doser instrument controlled by a Raspberry Pi Zero 2 W. The package
contains:

* ``hardware/vibration-motor-and-solenoid.md`` — narrative parts/wiring guide
  identifying a NEMA 11 stepper (auger drive) + Pololu DRV8825 carrier, an
  Adafruit DRV2605L + ERM disc (vibration), an external solenoid + Adafruit
  DRV8871 (tapping), plus a recommended single-supply variant
  (12 V wall-wart + Pololu D24V22F5 buck) and a per-vendor purchasing guide.
* ``hardware/kicad/`` — a KiCad 7 schematic of the actuator stack
  (``.kicad_sch`` + PDF + PNG render + custom symbol library).

Please give concrete, actionable feedback on:

1. Electrical correctness — power rail sizing (12 V/3 A wall-wart, D24V22F5
   2.5 A buck, shared 5 V rail for Pi + solenoid), the DRV8871 single-direction
   PWM mode (``IN2`` tied to GND, PWM on ``IN1``), the DRV8825 enable/sleep
   wiring, flyback/decoupling, common-GND tie, and any obvious foot-guns.
2. Mechanical / system integration — direct-coupled stepper vs. belt drive,
   the "no slip ring needed" rotating-vs-stationary partitioning, and the
   vibration-motor mounting on the stationary housing wall.
3. Parts selection — whether the chosen Adafruit/Pololu breakouts and the
   NEMA 11 stepper are reasonable for a benchtop powder-metering channel,
   any preferable substitutes (e.g. Tic-500 / plug-and-play steppers), and
   whether the per-channel BOM is sensible for the multi-channel ring frame
   referenced in PR #35.
4. Anything in the KiCad schematic that is unclear, incorrect, or worth
   re-organising for readability.

Be specific and cite the exact files / sections where applicable.
"""


def main() -> int:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        print("ERROR: EDISON_API_KEY not set", file=sys.stderr)
        return 2

    missing = [str(p) for p in ATTACHMENTS if not p.is_file()]
    if missing:
        print("ERROR: missing attachments:\n  " + "\n  ".join(missing), file=sys.stderr)
        return 2

    client = EdisonClient(api_key=api_key)

    print("Uploading attachments…", flush=True)
    uris: list[str] = []
    for p in ATTACHMENTS:
        uri = client.upload_file(str(p))
        print(f"  {p.relative_to(ROOT)} -> {uri}", flush=True)
        uris.append(uri)

    task_data = {"name": JobNames.ANALYSIS, "query": PROMPT}
    print("Submitting ANALYSIS task…", flush=True)
    trajectory_id = client.create_task(task_data, files=uris)
    print(f"  trajectory_id = {trajectory_id}", flush=True)

    # Poll. Per repo custom instructions: wait 10 minutes initially, then 5.
    # Cap total wait to ~60 minutes for a sandboxed runner.
    deadline = time.time() + 60 * 60
    first = True
    task = None
    while time.time() < deadline:
        wait_s = 600 if first else 300
        first = False
        print(f"  sleeping {wait_s}s before polling…", flush=True)
        time.sleep(wait_s)
        task = client.get_task(trajectory_id)
        status = getattr(task, "status", None)
        print(f"  status: {status}", flush=True)
        if status in {"success", "fail", "failed", "cancelled"}:
            break

    if task is None:
        print("ERROR: no task object returned", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    task_json = task.model_dump(mode="json") if hasattr(task, "model_dump") else task
    (OUT_DIR / f"{KEY}.task.json").write_text(
        json.dumps(task_json, indent=2, default=str) + "\n"
    )
    answer = getattr(task, "answer", None) or ""
    (OUT_DIR / f"{KEY}.answer.md").write_text(str(answer) + ("\n" if answer else ""))
    refs = ""
    for attr in ("formatted_answer", "references", "citations"):
        v = getattr(task, attr, None)
        if v:
            refs = str(v)
            break
    (OUT_DIR / f"{KEY}.references.md").write_text(refs + ("\n" if refs else ""))
    print(f"Wrote artifacts to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

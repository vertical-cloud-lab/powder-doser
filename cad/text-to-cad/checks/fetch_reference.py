"""Fetch the parts the recreation is scored against into STEP/reference/.

They are PR #170's STEP files (the lab's Fusion 360 exports, the AI
tap-collar base and PR #170's purchased-part and fastener stand-ins), read
straight out of git so nothing is duplicated in this branch.  STEP/reference/
is git-ignored.

    python3 checks/fetch_reference.py [--ref origin/claude/issue-165-20261001-1931]
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "STEP" / "reference"
PREFIX = "cad/full-assembly/components/"
DEFAULT_REF = "origin/claude/issue-165-20261001-1931"   # PR #170

FILES = {
    "auger": "fusion-step/auger.step",
    "auger_cap": "fusion-step/auger-cap.step",
    "baseplate": "fusion-step/baseplate.step",
    "bracket": "fusion-step/brackets.step",
    "mounting_plate": "fusion-step/mounting-plate.step",
    "servo_pinion": "fusion-step/servo-pinion.step",
    "stepper_pinion": "fusion-step/stepper-pinion.step",
    "tap_collar": "fusion-step/tap-collar.step",
    "tap_collar_base": "ai-step/tap-collar-base.step",
    "mg996r": "purchased/mg996r-servo.step",
    "nema11": "purchased/nema11-11hs18-0674s.step",
    "solenoid_412": "purchased/adafruit-412-solenoid.step",
    "mounting_board": "mount/mounting-board.step",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=DEFAULT_REF)
    a = ap.parse_args()
    branch = a.ref.split("/", 1)[1] if a.ref.startswith("origin/") else None
    if branch:
        subprocess.run(["git", "fetch", "-q", "origin", branch], check=True, cwd=ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    for key, rel in FILES.items():
        data = subprocess.run(["git", "show", f"{a.ref}:{PREFIX}{rel}"], check=True,
                              capture_output=True, cwd=ROOT).stdout
        (OUT / f"{key}.step").write_bytes(data)
        print(f"{key:16s} <- {rel} ({len(data) / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()

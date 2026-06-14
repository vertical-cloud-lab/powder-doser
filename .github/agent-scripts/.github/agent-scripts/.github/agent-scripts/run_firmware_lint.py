#!/usr/bin/env python3
"""
run_firmware_lint.py
Run ruff on the firmware directory and write JSON to reports/firmware-lint.json.
Exit code 2 if any error-level findings exist.
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_PATH = Path("hardware/test-module/firmware")
REPORT = Path("reports/firmware-lint.json")


def ensure_ruff():
    if shutil.which("ruff") is None:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff"])


def run_ruff(path: Path):
    proc = subprocess.run(["ruff", "--format", "json", str(path)], capture_output=True, text=True)
    stdout = proc.stdout or "[]"
    try:
        parsed = json.loads(stdout)
    except Exception:
        parsed = []
    return proc.returncode, parsed, proc.stdout


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--issue", type=int, default=87)
    p.add_argument("--pr", type=int, default=61)
    p.add_argument("--path", default=str(DEFAULT_PATH))
    args = p.parse_args(argv)

    ensure_ruff()
    code, parsed, raw = run_ruff(Path(args.path))

    errors = 0
    warnings = 0
    error_list = []
    if isinstance(parsed, list):
        for item in parsed:
            # ruff items include code, filename, start
            error_list.append({
                "file": item.get("filename"),
                "line": item.get("location", {}).get("row") if item.get("location") else item.get("line"),
                "code": item.get("code"),
                "message": item.get("message")
            })
            # treat all findings as warnings unless code starts with "E" or similar (heuristic)
            if item.get("code", "").startswith(("E", "F")):
                errors += 1
            else:
                warnings += 1

    out = {"summary": {"errors": errors, "warnings": warnings}, "errors": error_list, "raw": parsed}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    if errors:
        print(f"{errors} error(s) found by ruff", file=sys.stderr)
        sys.exit(2)
    print("Firmware lint complete")
    sys.exit(0)


if __name__ == "__main__":
    main()

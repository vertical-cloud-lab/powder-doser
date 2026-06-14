#!/usr/bin/env python3
"""
run_bom_checks.py
Simple heuristics: compare README BOM lines (if any) to schematic symbol tokens.
Writes JSON to reports/bom-report.json
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_README = Path("hardware/test-module/README.md")
DEFAULT_SCH = Path("hardware/test-module/kicad/test_module.kicad_sch")
REPORT = Path("reports/bom-report.json")

PART_TOKENS = [
    "DRV8825", "DRV2605", "DRV8871", "Pololu", "ERM", "JF-0530B", "NEMA", "HD-1810MG",
    "DRV8825", "DRV2605L", "DRV2605L"
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def parse_readme_bom(txt: str) -> set:
    # simple heuristic: find a markdown table and the "Part" or "Description" column tokens
    parts = set()
    for line in txt.splitlines():
        for token in PART_TOKENS:
            if token.lower() in line.lower():
                parts.add(token)
    return parts


def parse_schematic_tokens(txt: str) -> set:
    parts = set()
    for token in PART_TOKENS:
        if token in txt:
            parts.add(token)
    return parts


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--issue", type=int, default=87)
    p.add_argument("--pr", type=int, default=61)
    p.add_argument("--readme-path", default=str(DEFAULT_README))
    p.add_argument("--sch-path", default=str(DEFAULT_SCH))
    args = p.parse_args(argv)

    readme_txt = read_text(Path(args.readme_path))
    sch_txt = read_text(Path(args.sch_path))

    readme_parts = parse_readme_bom(readme_txt)
    sch_parts = parse_schematic_tokens(sch_txt)

    issues = []
    errors = 0
    warnings = 0

    for p in sorted(sch_parts - readme_parts):
        issues.append({"severity": "warning", "message": f"schematic uses {p} but BOM README missing entry", "suggestion": "Add to README BOM table"})
        warnings += 1

    for p in sorted(readme_parts - sch_parts):
        issues.append({"severity": "warning", "message": f"BOM lists {p} but schematic has no reference", "suggestion": "Verify README or schematic"})
        warnings += 1

    # trivial incompatible example (not exhaustive)
    if "DRV8825" in sch_parts and "DRV2605" in readme_parts and "DRV2605" not in sch_parts:
        issues.append({"severity": "error", "message": "README lists DRV2605 but schematic uses DRV8825", "suggestion": "Fix README or schematic"})
        errors += 1

    out = {"summary": {"errors": errors, "warnings": warnings}, "issues": issues}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    if errors:
        print(f"{errors} error(s) found", file=sys.stderr)
        sys.exit(2)
    print("BOM check complete")
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
run_pinmap_check.py
Compare KiCad global_label names to firmware PIN_ constants.
Writes JSON to reports/pinmap-report.json
Exit code 2 if any PIN_* missing from schematic.
"""
from __future__ import annotations
import argparse
import ast
import json
import re
import sys
from pathlib import Path

DEFAULT_SCH = Path("hardware/test-module/kicad/test_module.kicad_sch")
DEFAULT_CFG = Path("hardware/test-module/firmware/config.py")
REPORT = Path("reports/pinmap-report.json")


def extract_labels_from_sch(path: Path) -> set:
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return set()
    labels = set(re.findall(r'\(global_label\s+"?([^\s")]+)', txt))
    return labels


def extract_pin_constants_from_config(path: Path) -> dict:
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    tree = ast.parse(src)
    pins = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("PIN_"):
                    name = target.id
                    try:
                        val = ast.literal_eval(node.value)
                    except Exception:
                        val = None
                    pins[name] = val
    return pins


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--issue", type=int, default=87)
    p.add_argument("--pr", type=int, default=61)
    p.add_argument("--sch-path", default=str(DEFAULT_SCH))
    p.add_argument("--config-path", default=str(DEFAULT_CFG))
    args = p.parse_args(argv)

    labels = extract_labels_from_sch(Path(args.sch_path))
    pins = extract_pin_constants_from_config(Path(args.config_path))

    expected_map = {p: p[len("PIN_"):] for p in pins.keys()}

    missing = []
    for pname, net in expected_map.items():
        if net not in labels:
            missing.append({"pin_const": pname, "expected_net": net})

    extra_labels = sorted(list(labels - set(expected_map.values())))

    out = {
        "pin_constants": sorted(list(pins.keys())),
        "labels_in_schematic": sorted(list(labels)),
        "missing_in_schematic": missing,
        "extra_labels_in_schematic": extra_labels,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    if missing:
        print(f"{len(missing)} missing pin mappings found", file=sys.stderr)
        sys.exit(2)
    print("Pinmap check OK")
    sys.exit(0)


if __name__ == "__main__":
    main()

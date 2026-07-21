"""Export every part and the full assembly to STEP and STL.

Run from the repo root::

    python -m cad.build

Outputs land under ``cad/build/`` (gitignored). Each part is exported
twice -- once as STEP (parametric, lossless, CAD-tool-friendly) and once as
STL (mesh, slicer-friendly).

A small JSON manifest lists every exported file plus the parameter values
used; the next step in the feedback loop (``cad/dfm.py``) reads it back to
report what was built.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import cadquery as cq

from .excavator import (
    ExcavatorParams,
    build_arm,
    build_assembly,
    build_cam_ramp,
    build_pin,
    build_slot_board,
    build_strike_off_bar,
    build_trough,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = REPO_ROOT / "cad" / "build"


def _export(part: cq.Workplane, stem: str) -> list[Path]:
    """Export a single part as STEP and STL, return both paths."""
    step_path = BUILD_DIR / f"{stem}.step"
    stl_path = BUILD_DIR / f"{stem}.stl"
    cq.exporters.export(part, str(step_path), exportType="STEP")
    cq.exporters.export(part, str(stl_path), exportType="STL")
    return [step_path, stl_path]


def main() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    p = ExcavatorParams()

    parts = {
        "trough":         build_trough(p),
        "arm":            build_arm(p),
        "pin":            build_pin(p),
        "strike_off_bar": build_strike_off_bar(p),
        "cam_ramp":       build_cam_ramp(p),
        "slot_board":     build_slot_board(p),
    }

    written: list[str] = []
    for name, part in parts.items():
        for path in _export(part, name):
            written.append(str(path.relative_to(REPO_ROOT)))
            print(f"wrote {path.relative_to(REPO_ROOT)}")

    # Full assembly: STEP only (STL of an Assembly needs flattening that
    # CadQuery's STL exporter doesn't natively support).
    asm = build_assembly(p)
    asm_path = BUILD_DIR / "assembly.step"
    asm.save(str(asm_path), "STEP")
    written.append(str(asm_path.relative_to(REPO_ROOT)))
    print(f"wrote {asm_path.relative_to(REPO_ROOT)}")

    # Manifest: parameter snapshot + list of files that were written.
    # ``slot_path`` is a tuple-of-tuples; jsonify it to nested lists.
    params_dict = asdict(p)
    params_dict["slot_path"] = [list(pt) for pt in p.slot_path]
    manifest = {
        "params": params_dict,
        "files":  written,
    }
    manifest_path = BUILD_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"wrote {manifest_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

"""Phase 3 assembly merge for the multi-part Zoo workflow.

Loads all five Zoo-returned per-part STEP files (or the hand-authored
ground-truth substitute when the corresponding ML-ephant output is
missing/failed) and lays them out into a CadQuery ``Assembly`` with
explicit transforms so the parts are co-located in the design space:

* ``auger_solid``         — origin, axis = +Z, dispense end at z=0
* ``stepper_mount_collar`` — translated above the auger top, axis = +Z
* ``embed_pocket_sleeve`` — slipped over the auger near the dispense end
* ``servo_yoke``          — under the dispense exit, axis horizontal
* ``pi_mount_bracket``    — back face of the housing, +X normal

The assembly exports as one composite STEP plus a colour-coded GLTF (so
each part remains a separately-coloured solid in the Judge render). Use
the existing ``cad/meta-tools/render_step.py`` to render the composite.

No Zoo calls; pure local CadQuery merge.
"""
from __future__ import annotations

import pathlib

import cadquery as cq

HERE = pathlib.Path(__file__).resolve().parent
ZOO_OUT = HERE.parent.parent.parent / "cad" / "meta-tools" / "zoo-output" / "multi-part"

# (part_name, fallback STEP relative to HERE, transform location)
# Transform = (x, y, z, rx, ry, rz) with angles in degrees.
PART_LAYOUT = [
    # canonical auger sits at origin, dispense exit at z=0, top at z=100.
    ("auger_solid",          "ground_truth_auger.step", (0,    0,    0,    0,   0,   0)),
    # stepper collar sits on top of the auger (z=100), axis +Z.
    ("stepper_mount_collar", None,                       (0,    0,  100,    0,   0,   0)),
    # embed sleeve slips over the auger near dispense end (z=10..34).
    ("embed_pocket_sleeve",  None,                       (0,    0,   10,    0,   0,   0)),
    # servo yoke sits under dispense, base at z=-4, opening upward.
    ("servo_yoke",           None,                       (0,    0,   -4,    0,   0,   0)),
    # pi bracket on the back face (+X), centered axially.
    ("pi_mount_bracket",     None,                       (16,   0,   50,    0,  90,   0)),
]

PART_COLORS = {
    "auger_solid":          (0.78, 0.74, 0.58, 1.0),  # tan
    "stepper_mount_collar": (0.55, 0.65, 0.85, 1.0),  # blue
    "embed_pocket_sleeve":  (0.85, 0.55, 0.55, 1.0),  # red
    "servo_yoke":           (0.60, 0.85, 0.60, 1.0),  # green
    "pi_mount_bracket":     (0.85, 0.80, 0.45, 1.0),  # gold
}


def _load_step(name: str, fallback: str | None) -> cq.Workplane | None:
    """Prefer Phase-2 iterated STEP, then Phase-1 STEP, then ground truth."""
    candidates = []
    iter_dir = ZOO_OUT.parent / "multi-part-iter" / name
    p1_dir = ZOO_OUT / name
    for d in (iter_dir, p1_dir):
        if d.exists():
            candidates += sorted(d.glob("*.step"))
    if fallback:
        candidates += [HERE / fallback]
    for c in candidates:
        if c.exists() and c.stat().st_size > 0:
            try:
                shape = cq.importers.importStep(str(c))
                solids = shape.solids().vals()
                if not solids:
                    continue
                print(f"  [{name}] loaded {c.relative_to(HERE.parent.parent.parent)} "
                      f"({len(solids)} solid(s))")
                return shape
            except Exception as e:
                print(f"  [{name}] failed to load {c.name}: {e}")
                continue
    print(f"  [{name}] no STEP available — skipping in assembly")
    return None


def build_assembly() -> cq.Assembly:
    asm = cq.Assembly(name="powder-doser-full-system-modular")
    for name, fallback, (x, y, z, rx, ry, rz) in PART_LAYOUT:
        shape = _load_step(name, fallback)
        if shape is None:
            continue
        loc = cq.Location(cq.Vector(x, y, z), cq.Vector(0, 0, 1), 0)
        if (rx, ry, rz) != (0, 0, 0):
            loc = (
                cq.Location(cq.Vector(x, y, z))
                * cq.Location(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), rx)
                * cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), ry)
                * cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), rz)
            )
        asm.add(shape, name=name, loc=loc, color=cq.Color(*PART_COLORS[name]))
    return asm


def main() -> int:
    print("== Phase 3 assembly merge ==")
    asm = build_assembly()
    out_step = HERE / "full_system_assembly.step"
    out_gltf = HERE / "full_system_assembly.gltf"
    asm.save(str(out_step), exportType="STEP")
    try:
        asm.save(str(out_gltf), exportType="GLTF")
    except Exception as e:
        print(f"  (GLTF export skipped: {e})")
    print(f"\nwrote {out_step.name}  ({out_step.stat().st_size} bytes)")
    if out_gltf.exists():
        print(f"wrote {out_gltf.name}  ({out_gltf.stat().st_size} bytes)")
    # Component summary
    children = list(asm.children) if hasattr(asm, "children") else []
    print(f"\ncomponents in assembly: {len(children)}")
    for c in children:
        print(f"  - {c.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# CAD-grounded A–H dispensing scenes

This directory contains **physical CAD geometry** for the eight powder-dosing alternatives (A–H), grounding the previously hand-tuned 2-D dispensing animations in a real, shared world frame in millimetres.

Per [@sgbaird-yolo's comment on PR #13](https://github.com/vertical-cloud-lab/powder-doser/pull/13#issuecomment-4427631537): *"you still didn't address the spatial inconsistencies. I suggest you use something more physical (e.g., CAD software of some kind)"*.

## What's here

| File | What |
|---|---|
| `A_scene.step` … `H_scene.step` | One STEP-203 CAD scene per concept (CadQuery `Assembly.save`). Each scene includes the **shared** machine context — the 3018-Pro V2 bed slab, the gantry top rail, and a 15 mm OD vial on the bed — **plus** that concept's primary mechanism body in its LOAD-phase pose, all positioned in one millimetre-unit world frame. Re-openable in FreeCAD, Fusion 360, SolidWorks, OnShape, etc. |
| `manifest.json` | Per-concept world-frame AABBs for every part drawn in the animation. Same units as the STEP files; matches the AABB used by the animator one-for-one. |
| `<X>_animation.gif` | Per-concept side-view animation (480 × 360 px, 12 fps, 5 s, looping). Every frame is built from CAD-derived part rectangles projected through the same `SideProjector`. |
| `<X>_frame_<phase>.png` | One still per concept per phase: `LOAD`, `APPROACH`, `DISPENSE`, `SETTLE`. Useful for static review without playing the GIF. |
| `composite_animation.gif` | 4 × 2 composite of all eight per-concept GIFs, built frame-by-frame from the same render functions so tiles never desync. Tile order: A B C D / E F G H. |

## How spatial alignment is guaranteed

1. [`scripts/scene_world_frame.py`](../../scripts/scene_world_frame.py) defines a single `WorldFrame` (all dimensions in mm) — the bed plane Z, the gantry rail Z, the mechanism rest column X, the vial position and the vial height. Every concept consumes these constants; no concept invents its own bed line or vial.
2. The same file defines a single `SideProjector` that maps any world `(x_mm, z_mm)` to pixel coordinates. The same instance (`PROJ`) is used by every renderer for every frame.
3. [`scripts/scene_cad.py`](../../scripts/scene_cad.py) constructs each concept's mechanism as a real CadQuery solid located at `mech_home_x` (LOAD) → `vial_x` (DISPENSE/SETTLE) using a shared `gantry_x(t)` trajectory and a shared phase clock. Every part the animator draws is sourced from a CadQuery AABB — not a hand-typed pixel pair.
4. [`scripts/animate_dispensing_cad.py`](../../scripts/animate_dispensing_cad.py) renders each frame by iterating over those parts and calling `PROJ.project_box` for each. The composite is built frame-by-frame from the same render functions, so the bed-line, vial mouths, gantry rail, and mechanism home column land on identical pixel rows/columns across all eight tiles.
5. Each frame includes a `10 mm` scale bar derived from `PROJ.mm_per_px()`, proving the transform is metric.

## How to regenerate

```bash
# 1. Build CadQuery scenes + STEP exports + manifest.json
python scripts/scene_cad.py

# 2. Render per-concept animations + phase stills + composite
python scripts/animate_dispensing_cad.py
```

Total runtime ≈ 1 minute on a vanilla GitHub Actions runner. Requires `cadquery` and `Pillow` from `cadquery-ocp` (Open CASCADE). No OpenSCAD or browser is needed.

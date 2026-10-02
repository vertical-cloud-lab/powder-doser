# Powder Doser — full parametric assembly (issue #106)

A parametric [CadQuery](https://cadquery.readthedocs.io/) (Python) model of the
auger-fed **Powder Doser**, generated entirely from the standalone engineering
prompt in [`SPEC.md`](SPEC.md). It produces a manifold solid + STEP for every
3D-printed part listed in SPEC §2, plus a single tilt-0° **assembly**, and runs
the SPEC §6 interaction-rule checks (clearances + the one intended
interference) as boolean-overlap volumes.

## Quick start

```bash
pip install cadquery trimesh matplotlib vtk
xvfb-run -a python3 build.py
```

This regenerates everything into `exports/`:

| folder         | contents                                              |
| -------------- | ----------------------------------------------------- |
| `exports/step` | one `.step` per part + `00_assembly.step` (committed) |
| `exports/stl`  | matching `.stl` meshes (git-ignored — regenerable)    |
| `exports/img`  | shaded isometric `.png` per part + assembly           |

`exports/img/00_assembly_iso_az090_hires.png` is a 5600 × 4000 px,
per-part-coloured VTK render of the full assembly at the iso `az=90°`
viewpoint, sharing the colour scheme of
`cad/mounting-plate-assembly/render_assembly.py` (`vtk` + `xvfb-run`
required for that view).

Every solid is validated with OpenCascade's `BRepCheck_Analyzer` and reported
with its volume; the §6 report prints `PASS`/`FAIL` per rule.

## Source layout

| file          | role                                                              |
| ------------- | ----------------------------------------------------------------- |
| `params.py`   | every dimension transcribed from `SPEC.md` (no CAD imports)       |
| `helpers.py`  | involute `gear_solid` + helical `screw_solid` generators          |
| `build.py`    | all part builders, `build_assembly()`, `interference_report()`    |
| `SPEC.md`     | the authoritative standalone prompt (issue #106)                  |

## Parts (SPEC §2)

| # | part | builder | notes |
| - | ---- | ------- | ----- |
| 1  | Archimedes auger — storage, v4 nozzle (full + short) | `build_auger(..., storage=True)` | Ø25 tube, Ø21 bore stays open, internal helix in bottom ⅓, external 48T drive band |
| 2  | Threaded sealable auger + screw-on cap | `build_auger(..., threaded=True)`, `build_cap` | **external** thread crest flush with OD; cap thread **internal**; 0.35 mm hand fit |
| 3  | Stepper pinion (16T) | `build_stepper_pinion` | Ø5 + 0.2 slip bore, M3 setscrew, meshes the band at C=32 (3:1) |
| 4  | Mounting plate ("the table") | `build_mounting_plate` | tilts; dual 40T hinge gears + arm-clearance slots |
| 5  | Baseplate | `build_baseplate` | fixed tab; hinge arms + dual servo porches/flanges |
| 6  | M5 hinge pin | `build_hinge_pin` | |
| 7  | Servo pinion (20T) | `build_servo_pinion` | MG996R 25T spline bore; 2:1 to the hinge gear (C=27.25) |
| 8  | Auger bracket (split clamp) | `build_bracket` | Ø25.5 running-fit bore |
| 9  | Tap collar (coin motor + solenoid + hardstop) | `build_tap_collar` | free-spin Ø25.5 bore; solenoid boss on +X; coin pad on −X; ear on +Y |
| 10 | Tap-collar mount plate | `build_tap_mount` | rotation hardstop for the collar ear |

## SPEC §6 interaction-rule report

`python3 build.py` (or `build.interference_report()`) confirms, as solid-overlap
volumes:

- auger bore stays open through the 48T band (0 mm³ obstruction);
- pinion ↔ band external mesh at C = 32 (light tooth contact only) and the
  NEMA 11 body clears the auger OD by ~5.5 mm;
- the auger thread is external / the cap thread internal (0.35 mm hand fit);
- the tap collar free-spins on the auger (0 mm³ bore overlap);
- the solenoid plunger tip is the **only** deliberate interference, reaching
  3.0 mm into the auger OD along X;
- the mounting plate sweeps 0° / 45° / 90° with **0 mm³** collision against the
  baseplate hinge arms.

## Conventions / gotchas

- **World frame:** mounting-plate top at Z=0; auger axis along **+Y** at
  Z=+29.25; dispense tip toward +Y; tilt axis along X at (y=125, z=29.25).
  Tube-shaped parts are authored axis-up (+Z) and rotated +90° about X for the
  assembly.
- **Gears** are built as a root disc fused with one extruded tooth-face prism
  per tooth — a single closed involute polyline self-intersects at its seam and
  yields invalid/non-watertight solids.
- **Threads:** the external auger thread is a helical V-**groove cut** into the
  tube (crests stay flush with the OD); the internal cap thread is a swept
  ridge whose crest overlaps 0.3 mm into the bore wall so the boolean union
  stays manifold.

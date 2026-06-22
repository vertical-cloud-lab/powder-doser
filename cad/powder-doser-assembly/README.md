# Powder Doser — zoo.dev-driven CAD generation

This directory designs the complete **Powder Doser** assembly (a vertically
orientable, auger-fed dry-powder dispenser) part-by-part using the
[zoo.dev](https://zoo.dev) **ML-ephant Text-to-CAD** API, exactly as requested
in the project issue. Every part is generated from a self-contained
engineering prompt, compiled to STEP, and bounding-box-checked against the
specification.

## Pipeline

`generate.py` drives the whole flow against the Zoo API (token in
`ZOO_API_TOKEN`):

1. **Text-to-CAD** — POST the prompt to `https://api.zoo.dev/ai/text-to-cad/step?kcl=true`
   (the `kcl` model), poll `GET /user/text-to-cad/{id}` until complete, and
   save the generated **KCL** native source to `exports/<part>/source.kcl`.
2. **Export** — compile the KCL to `output.step`, `output.glb` and
   `output.obj` with the [`zoo` CLI](https://github.com/KittyCAD/cli)
   (`zoo kcl export --output-format=step …`).
3. **Verify** — parse the OBJ vertices into a bounding box recorded in
   `exports/<part>/manifest.json` for comparison against the spec.

The script is resumable (parts already exporting are skipped unless `--force`)
and supports `--only <name>` and `--no-export`.

```sh
export ZOO_API_TOKEN=...                      # your zoo.dev API token
# zoo CLI on PATH (https://github.com/KittyCAD/cli/releases)
python3 generate.py                           # generate all missing parts
python3 generate.py --only stepper-pinion     # regenerate one part
```

## Parts (`prompts/`)

Each prompt is derived from the engineering specification (auger PR #49,
mounting-plate PR #66, tap-collar PR #51, nozzle issue #48) and includes a
"why it matters" note so the generator reasons about *function*, not just
numbers. The 10 printed parts plus variants:

| # | Prompt | Part |
|---|--------|------|
| 01 | `01-storage-auger-full.md` | Storage auger, full 250 mm, v4 nozzle + 48T gear band |
| 02 | `02-storage-auger-bench.md` | Storage auger, 90 mm bench-test |
| 03 | `03-threaded-auger.md` | Threaded sealable auger (external thread) |
| 04 | `04-threaded-cap.md` | Screw-on sealing cap (internal thread) |
| 05 | `05-stepper-pinion.md` | 16T NEMA 11 stepper pinion |
| 06 | `06-mounting-plate.md` | Tilting mounting plate ("the table") |
| 07 | `07-baseplate.md` | Fixed baseplate + hinge arms + servo posts |
| 08 | `08-servo-pinion.md` | 20T MG996R servo pinion |
| 09 | `09-auger-bracket.md` | Split shaft-collar auger bracket |
| 10 | `10-tap-collar.md` | Tap collar (vibration motor + solenoid) |
| 11 | `11-tap-collar-mount.md` | Tap-collar mount plate with hardstop |

## Generated so far (`exports/`)

| Part | STEP | Bbox (mm) | Spec check |
|------|------|-----------|------------|
| `stepper-pinion` | ✅ | 17.95 × 17.95 × 16.0 | tip Ø18 ✓, height = 10 face + 6 hub = 16 ✓ |
| `auger-bracket` | ✅ | 60.0 × 12.0 × 45.97 | flange 60×12 ✓, collar top ≈ 29.25 + 16.75 = 46 ✓ |

The remaining parts are reproduced by re-running `generate.py`. **Note on
generator limits:** Text-to-CAD reliably one-shots prismatic and spur-gear
geometry (pinions, brackets, plates) but currently times out on
helical-thread and splined features (the threaded cap, the threaded auger's
external thread, and the servo-pinion spline flat). For those, simplify the
prompt to the printable envelope and add the thread/flat as a follow-up
modeling step, or iterate the prompt (the zoo.dev conversation API supports
refining a previous design).

## Coordinate system & assembly

Per the spec: the auger long axis is **+Y**, dispense tip at **+Y**, **+Z is
up**; the auger bore centreline sits **Z = +29.25 mm above the mounting-plate
top**. The intended assembly order along the auger axis from the hinge (+Y)
toward the motor (−Y) is: hinge → front bracket → tap collar → auger gear band
(stepper meshing beside it) → rear bracket. Key §6 interaction rules to honour
when assembling: the auger bore stays open through the annular 48T band; the
pinion↔auger mesh is 3:1 at centre distance 32; the auger thread is external
and the cap thread internal (0.35 mm hand fit); the tap collar spins freely on
the tube (running fit, never a clamp) but is arrested by its hardstop ear; and
the solenoid plunger tip is the one deliberate interference (3.0 mm into the
auger OD).

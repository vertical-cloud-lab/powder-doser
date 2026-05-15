# Mounting plate + baseplate assembly

Closes [#58](https://github.com/vertical-cloud-lab/powder-doser/issues/58).
Pulls upstream part dimensions from
[#46](https://github.com/vertical-cloud-lab/powder-doser/issues/46) (auger
bracket), [#48](https://github.com/vertical-cloud-lab/powder-doser/issues/48)
(geared auger / NEMA-17 drive), and
[#50](https://github.com/vertical-cloud-lab/powder-doser/issues/50)
(tap collar with hardstop).

The package designs:

- **`mounting_plate`** — the upper plate that carries every moving piece
  (two auger brackets, the tap-collar mounting flange with hardstop,
  the NEMA-17 stepper). The plate hinges about an axis that intersects
  the auger's vertical discharge bore, so the whole top assembly tilts
  0°→90° **without cutting through the auger** and **without blocking
  the powder path**.

- **`baseplate`** — the lower plate that carries the mating hinge
  pillars, the lower (pivot) clevis of the linear actuator, four
  150 mm legs, and a rectangular cut-out beneath the discharge bore so
  powder falls through onto the cup on the scale below.

- **Companion placeholders** for the auger, brackets, tap-collar
  mount, NEMA-17 motor body, linear actuator (body + rod + clevises),
  cup, and scale. These are stand-ins so the assembly STEP renders in
  context — the printable parts are only `mounting_plate.{step,stl}`
  and `baseplate.{step,stl}`.

## Assembly views

| 0° (horizontal)            | 45°                          | 90° (vertical)              |
|----------------------------|------------------------------|-----------------------------|
| ![0 iso](renders/assembly_0deg_iso.png)   | ![45 iso](renders/assembly_45deg_iso.png) | ![90 iso](renders/assembly_90deg_iso.png) |
| ![0 front](renders/assembly_0deg_front.png) | ![45 front](renders/assembly_45deg_front.png) | ![90 front](renders/assembly_90deg_front.png) |

> The linear-actuator placeholder in each STEP is rendered at its 0°
> length only (it does not auto-extend with `tilt_deg`); the actual
> per-tilt actuator length is shown in the matplotlib rotation diagram
> below, which uses the geometry of the pinned tab and base clevis.

### Rotation about the hinge

![Rotation 0 / 45 / 90 deg](diagrams/rotation_0_45_90.png)

Hinge axis is parallel to **+Y**, intersecting the auger's discharge
bore at world `(X, Z) = (HINGE_X, pin_world_z) = (18, 202)` mm. Tilt is
applied about the **−Y** axis using the right-hand rule, so the +X end
(motor) swings **up** as the tilt increases (this avoids a collision
between the NEMA-17 body and the baseplate at 90°).

The linear actuator (M5 pin, lower clevis on the baseplate at
`X = HINGE_X + 130 mm`, upper tab on the mounting-plate underside at
`X = HINGE_X + 55 mm`) needs the following lengths:

| tilt | LA length |
|------|-----------|
| 0°   | ~77 mm    |
| 45°  | ~100 mm   |
| 90°  | ~144 mm   |

Required stroke ≈ **67 mm**, which sits comfortably inside the 100 mm
stroke of the placeholder actuator (`LA_BODY_LEN = 150 mm`,
`LA_STROKE = 100 mm`). Re-derive these numbers automatically by
running `diagrams.py` after editing constants in `cad_model.py`.

### Powder flow

![Powder flow](diagrams/powder_flow.png)

The discharge bore is a Ø10 mm vertical hole through the auger barrel
**on the hinge axis**. Because the bore axis coincides with the hinge
axis, the powder always exits at the same world `(X, Y)` regardless of
tilt — it falls through the mounting-plate's discharge notch, through
the baseplate cut-out, and into the cup on the scale.

## Install diagrams

### Mounting plate (top view, plate flange-down)

![Install mounting plate](diagrams/install_mounting_plate.png)

| group | hardware | quantity | hole pattern (mm) |
|-------|----------|----------|--------------------|
| BRK-D (bracket #1, discharge end) | M3 × 12 SHCS + M3 nut | 4 | 38 × 18 |
| TAP   (tap-collar mount)          | M3 × 12 SHCS + M3 nut | 4 | 38 × 18 |
| BRK-M (bracket #2, motor end)     | M3 × 12 SHCS + M3 nut | 4 | 38 × 18 |
| NEMA-17                            | M3 × 8 SHCS           | 4 | 31 × 31 + Ø22 pilot |
| Hinge pin                          | M5 × 60 + M5 lock-nut | 1 (shared with baseplate) | — |
| LA tab (underside)                 | M5 × 25 clevis pin    | 1 (shared with baseplate) | — |

Hole references are labelled `D1..D4`, `T1..T4`, `M1..M4`,
`NEMA-1..NEMA-4` on the diagram.

### Baseplate (top view, plate flange-up)

![Install baseplate](diagrams/install_baseplate.png)

The baseplate sits on four 150 mm legs (`LEG-1..LEG-4`); a typical
130 × 110 × 28 mm bench scale plus a Ø60 × 70 mm cup sits underneath
with ~50 mm of clearance, with the cup centred on the discharge
cut-out.

## Print orientation

| part            | orientation | notes |
|-----------------|-------------|-------|
| `mounting_plate.stl` | flange-up (top surface on the build plate) | hinge pillars and LA tab print as overhangs; turn on tree supports under those features only. Plate body needs no supports. |
| `baseplate.stl`      | plate-up (legs hanging down) | flip in the slicer so legs are vertical and unsupported; alternatively print legs separately and bolt them on through the M4 cross-brace holes. |

Both parts are designed for FDM in PETG or PLA at 0.2 mm layer height,
30 % infill, 4 perimeters. The `cup` and `scale` STLs are placeholders
only (do not print).

## Reproducing the files

```bash
pip install cadquery
cd design/cad/mounting-plate-assembly
python cad_model.py            # writes step/ + stl/
xvfb-run -a python render_views.py   # writes renders/
python diagrams.py             # writes diagrams/
```

`xvfb-run` is required for `render_views.py` because VTK needs a DISPLAY
even when rendering off-screen.

## CADsmith — pros and cons (informed by this attempt)

The issue asked us to author this part through
[CADsmith](https://github.com/vertical-cloud-lab/CADSmith), the
multi-agent CadQuery pipeline (Planner → Coder → Executor → Validator
→ Refiner). **We could not actually run CADsmith in this sandbox**:
its `Setup` section requires `ANTHROPIC_API_KEY` (Claude Sonnet for
the code-generation agents and Claude Opus for the vision Judge), and
that secret is not provisioned for this Copilot Coding Agent
environment (only `ZOO_API_TOKEN` and `EDISON_API_KEY` are). The same
blocker stopped PR #55 (the simple-part exercise from #54). The
geometry above is therefore hand-authored as a parametric CadQuery
script in the same shape CADsmith would emit, so the part can be
re-validated through the CADsmith loop on a machine that does have the
key, without having to restructure anything.

With that caveat, here is what the exercise revealed about CADsmith's
strengths and weaknesses for a complex multi-part task like this one:

### Pros

- **Closed-loop dimensional accuracy.** CADsmith's published numbers
  (38× lower mean Chamfer Distance vs. zero-shot, 100 % execution
  rate on its 100-prompt benchmark) come from feeding the OCCT
  bounding-box / volume / face-count metrics back into the Refiner.
  For a part like this mounting plate — where the M3 clearance hole
  is 3.4 mm and the bolt circle is 31 mm — sub-millimetre dimensional
  errors matter, and a closed loop is exactly the right primitive.

- **Vision Judge catches "looks-wrong" failures kernel metrics miss.**
  The three-view render + Claude Opus Judge is well suited to this
  assembly's failure modes (e.g. "the hinge pillars don't actually
  straddle the auger", "the discharge notch doesn't reach the bore"),
  which are obvious visually but invisible to a bounding-box check.
  We hit a few of these in this PR (motor swinging down through the
  baseplate at 90°, LA tab on the wrong end of the plate forcing a
  ~250 mm stroke); a Judge would have flagged each on the first
  iteration instead of in a hand review.

- **Parametric CadQuery is the right output format.** The CadQuery
  script CADsmith emits is the same artifact that survives this PR
  (`cad_model.py`), so a future re-run that re-derives the geometry
  through the multi-agent loop gives us a regenerable, diff-able
  source of truth — not an opaque mesh.

- **RAG over CadQuery API + error patterns** removes the worst
  failure mode of zero-shot LLM CAD ("invented method names that
  don't exist"). Even hand-authoring this script we hit two of those
  (`toVtkPolyData` import path moved between cq versions; `centerOption`
  edge cases on multi-face selections); the error refiner would have
  caught both.

### Cons

- **The hard secrets dependency is the real blocker.** CADsmith
  *requires* `ANTHROPIC_API_KEY`. In this sandbox that means the
  CADsmith path is not just slow or expensive — it is *unrunnable*.
  Until either CADsmith adds support for a model that's reachable
  from the agent (e.g. via `GITHUB_TOKEN`-mediated Copilot models, or
  a self-hosted endpoint), every "use CADsmith" issue will fall back
  to hand-authored CadQuery, exactly like this PR and #55. This is
  the single biggest practical issue with adopting it for our
  workflow.

- **Conda-only setup.** The README pins
  `conda install -c cadquery -c conda-forge cadquery=master`. We
  installed `cadquery==2.7.0` from PyPI here in seconds and it worked
  fine for everything we needed, but the official path requires a
  conda environment, which complicates CI and Copilot Coding Agent
  setup steps (`copilot-setup-steps.yml` would need a miniconda
  install rather than a `pip install`).

- **Single-part orientation.** CADsmith's benchmark and pipeline are
  oriented around producing **one** part from one prompt. A complex
  multi-part task like this one (mounting plate + baseplate + several
  cooperating placeholders + an assembly + 0/45/90 rotation diagrams
  + a powder-flow diagram) doesn't decompose cleanly into a single
  prompt; we would have to drive CADsmith N times with hand-written
  context glue between calls. The "agentic" part of CADsmith stops
  at one part — assembly-level validation (do the bracket holes line
  up with the plate holes? does the LA stroke fit the rotation
  envelope?) is **not** in the loop and would still need the hand
  scripting we're doing in `cad_model.build_assembly()`.

- **Iteration cost on T3-class parts.** The benchmark notes that
  removing vision raises T3 mean Chamfer Distance from 1.42 to 49.68
  — i.e. the vision Judge is doing a lot of the work on complex
  parts. Each outer-loop iteration is one Opus call + one Sonnet
  refinement call + a re-render and a re-execute. For a part of this
  complexity (≈ 400 lines of CadQuery, 16 distinct hole groups,
  hinge constraint, discharge-notch constraint, leg constraint), the
  outer loop will plausibly need 3–5 iterations, and each iteration
  costs a non-trivial number of Opus tokens. A hand author closing
  the same loop with eyeballs is faster and cheaper for this size of
  part — *until* CADsmith can be wired to a model that's already
  paid for.

- **Vision still misses "near-miss" assembly errors.** The README's
  own failure example (the quadcopter T3_019 — F1 = 0.963, IoU =
  0.985, but small gaps between arms and hub that the three fixed
  views couldn't see) is exactly the failure mode we're most worried
  about here: e.g. a 0.3 mm interference between the auger OD and
  the bracket bore, or a hinge pin hole misaligned by 1 mm between
  the upper and lower pillars. Three fixed views can miss those, and
  the Judge will pass the part anyway. Adaptive view selection or
  high-resolution crops, both called out as future work in the
  CADsmith README, would close that gap.

**Bottom line:** CADsmith is a credible solution for "give me a
single, dimensionally-correct printable part" once the API-key
constraint is solved. For an assembly task like this one, it would
need an outer "assembly" agent layered on top before it could replace
the hand-written `build_assembly()` you see in `cad_model.py`.

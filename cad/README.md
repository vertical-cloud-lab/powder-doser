# Parametric CAD pipeline

This directory holds the **scripted, open-source parametric CAD model** for
the powder-excavator design discussed in `docs/manuscript/main.tex` and
`README.md`. It is the start of a feedback-loop-friendly hardware design
pipeline:

```
ExcavatorParams (single source of truth, mm)
        │
        ├──► excavator.py  ──► CadQuery solids (trough, arms, pin, …)
        │                          │
        │                          ├──► build.py  ──► STEP + STL + manifest.json
        │                          │
        │                          └──► (open in CQ-editor / FreeCAD / KiCAD-AS-PCB / …)
        │
        └──► dfm.py  ──► automated checks
                            • FDM printability (min wall, overhang)
                            • gantry-only kinematics (no second axis on the bucket)
                            • cam-ramp and pin-slot reachability
```

## Why CadQuery (instead of Rhino/Grasshopper, Fusion, nTop, …)?

Per PR #2 the user asked for **something open that you can install and run**.
[CadQuery](https://github.com/CadQuery/cadquery) is a pip-installable, pure-
Python parametric kernel built on top of OCCT (the same kernel FreeCAD uses).
That makes it a natural fit for this repo:

* `pip install cadquery` is the only setup step.
* The model is plain Python source code, so a "design iteration" is a
  `git diff` plus a `python -m cad.build` re-run.
* Outputs are STEP and STL — every open-source slicer (PrusaSlicer,
  OrcaSlicer, Cura) and every CAD viewer (FreeCAD, OCC's CAD Assistant,
  KiCAD's 3D viewer) can read them.

[`build123d`](https://github.com/gumyr/build123d) is the natural **sibling
pick** on the same OCCT/OCP kernel — also Apache-2.0, also pip-installable,
also pure-Python — and is worth treating as a co-equal alternative rather
than a follow-on. [OpenSCAD](https://openscad.org/) is the cleanest
**non-Python second source** (CSG DSL, `apt install openscad`, headless
STL out of the box) and is useful as a sanity check that geometry behaves
the same in two kernels.

### Where the *commercial* CAD tools actually land

The original PR-#2 phrasing dismissed Rhino/Grasshopper, Fusion 360 (with
Generative Design), nTop, and Onshape FeatureScript with a single line —
*"none of the others survive the fresh CI runner test."* The follow-on
meta-tool evaluation (PR #7, `cad/meta-tools/`) attempted each one inside
an Ubuntu sandbox and produced a more accurate picture; the primary
recommendations from that evaluation are folded in here:

| Tool | Authoring on Linux | Headless eval on Linux | What it actually takes |
|------|--------------------|------------------------|------------------------|
| **CadQuery** / **build123d** (current pick + sibling) | ✅ pip | ✅ pure-Python OCCT | nothing |
| **OpenSCAD** (second source) | ✅ apt | ✅ `openscad -o out.stl in.scad` | nothing |
| **rhino3dm** (NURBS IO only) | ✅ pip | ✅ pure-Python | nothing — but no Grasshopper layer |
| **Rhino Compute** front-end | ✅ `dotnet build` | ✅ runs on Linux | needs to be paired with a worker |
| **Rhino Compute** worker (`compute.geometry`) | ✅ builds | ❌ needs `libRhinoLibrary.so` | Windows host **or** Wine + Rhino-Win + licence; **or** a paid hosted Compute |
| **Grasshopper** (`.gh`) | ⚠️ Windows authoring only | ⚠️ via Compute worker | same as Compute worker |
| **Onshape FeatureScript** | ✅ author `.fs` as text | ⚠️ exec is server-side REST | `ONSHAPE_ACCESS_KEY` + `ONSHAPE_SECRET_KEY` secrets + an Onshape account (Public free tier or free Education plan) |
| **nTop Automate (Linux)** | ⚠️ tarball login-walled | ⚠️ paid licence file | vendor-issued tarball + licence as encrypted GitHub secrets; commercial subscription |
| **Fusion 360 / Generative Design** | ❌ Win-only PE32 GUI installer | ❌ paid cloud, no public REST | effectively impossible to bolt onto this CI |

So the corrected reading is: CadQuery/build123d are still the right
primary pick, OpenSCAD is a free second source, **Onshape and nTop are
viable in CI but require vendor accounts/secrets**, and Fusion GD really
doesn't fit. See [`cad/meta-tools/README.md`](meta-tools/README.md) (when
PR #7 lands) for the install/build/runtime logs behind each row.

### Cost / Linux-headless reality for the paid rows

| Tool | List price (USD) | Academic option | Linux-headless reality |
|------|------------------|------------------|-------------------------|
| **Rhino 8** (perpetual, single-user) | ~$995 commercial | **~$195** academic perpetual, full-featured | **No native Linux build, no supported headless mode** (Win/macOS only). `rhino3dm` and the `rhino.compute` proxy run on Linux, but the geometry kernel needs Rhino-for-Windows behind it. |
| **Onshape** | Free **Public** ($0, world-visible, non-commercial); Standard ~$1.5k/u/yr; Pro ~$2.5k/u/yr | **Education plan is free** for verified individuals (full features, non-commercial) | Browser + cloud REST — Linux-native by construction. `pip install onshape-client` and post to `cad.onshape.com`. |
| **nTop / nTop Automate** | **Quote-only — no public list price** (comparable enterprise CAD ~$2.4k–$8k/u/yr; nTop generally at or above that band) | Quote-only via `academic@ntop.com` | Real Linux-headless tarball intended for HPC/CI batch use, but download dashboard is login-walled and the runtime needs a paid licence file. |

Practical read: **Onshape (free Education plan)** is the only one of the
three that's actually free, Linux-native, and ready to wire into CI today.
**Rhino academic** is cheap-ish but fundamentally Windows/macOS. **nTop**
is the most powerful for generative/lattice work but the price is opaque
and almost certainly not justified at the v1 trough-design scale; revisit
only if/when geometry pushes past CadQuery's BREP kernel.

## Target hardware and matched toolchain

The literature-canonical SDL rig (per the Edison `paperqa3-high` synthesis,
task `c0f412d3-d85d-466a-abd1-db6614a2db70`, archived in PR #7 as
`cad/meta-tools/edison-c0f412d3-literature-synthesis.md`) is **Jubilee +
balance + OpenCV + Ax/BoTorch** — that is the right *aspirational* target
but **not** the rig we are actually building. The planned hardware for
powder-excavator is hobby-grade and manual-load:

* **Genmitsu 3018-Pro V2** — desktop GRBL CNC (~300 × 180 × 45 mm work
  envelope, ~10 k RPM 775 spindle, ER11 collet, Woodpecker-style
  controller speaking GRBL G-code over USB). Manual workholding, no
  auto-tool-change.
* **Prusa i3 / MK3** (or **Creality Ender-3**) — manual-load FDM printer,
  no sample changer, no instrumented bed.

The v1 meta-tool stack that matches that hardware is:

| Stage | Tool | Why it fits |
|-------|------|-------------|
| Parametric CAD | **CadQuery** (or **build123d**) | Pip-installable, headless, real STEP/STL out, runs in CI. |
| Second-source / sanity check | **OpenSCAD** | `apt install openscad`, already builds an STL on a stock runner. |
| FDM slicing (MK3 / Ender) | **PrusaSlicer CLI** | Headless, ships profiles for both MK3S and Ender-3 in-box, exports G-code plus per-print metrics (time, filament, support volume) usable as DFM signals. |
| CNC CAM for the 3018 | **FreeCAD Path workbench** (headless via `freecadcmd`) or **Kiri:Moto** (STL-in / GRBL-out, no scripting) | Both emit GRBL-flavored G-code suitable for the 3018's Woodpecker controller. FreeCAD Path is the CI-friendly option; Kiri:Moto is the low-friction option. |
| G-code simulation | **Camotics** (apt) or **NC Viewer** (web) | Visualise the toolpath before crashing a 3.175 mm endmill into the bed. |
| Sender to the 3018 | **UGS** (Universal Gcode Sender) or **bCNC** | Standard GRBL senders. Operator side, not CI. |
| DFM | Will-It-Print-style checks (overhang / small feature / warping / toppling / Ra) for FDM; geometric guards (min endmill diameter, max depth-of-cut per pass, no internal sharp corners smaller than tool radius, no features taller than ~40 mm Z) for CNC | Planned: split `cad/dfm.py` into FDM checks and CNC checks. |
| Glue | Python + Jupyter | Unchanged. |

Net stack for v1: CadQuery (+ OpenSCAD second source) → PrusaSlicer CLI for
the MK3/Ender parts, FreeCAD Path → GRBL for the 3018 parts → Camotics
preview → manual build/measure → pandas scorecard in Jupyter.

### Design-space exploration

Default is **manual parameter sweeps + a small pandas/Jupyter scorecard** —
every trial currently requires a human to print/mill/measure, so a Latin-
hypercube of 6–9 designs evaluated in a notebook beats any framework.
Reach for **Optuna** (`n_trials ≈ 10–20`) only past ~5 parameters and
~15+ physical builds, when the manual scorecard stops scaling.
**Ax/BoTorch** and **Science-Jubilee**-style closed-loop SDL stay on the
*future* SDL wishlist for if/when a load cell, scale, or webcam ever gets
bolted onto the bench — the current hobby-grade hardware doesn't expose
the closed-loop instrumented-feedback hook those frameworks assume.

### Edison generative-CAD literature task

The Edison Scientific generative-CAD literature task (initial submission
`task_id` `524e7e92-a326-440a-b6fd-f6eb220d9019` was sent to the wrong
endpoint and cancelled; resubmitted as
`f5a27ed3-8530-4102-9e31-5af9bbe9b0e0` against the correct
`api.platform.edisonscientific.com` endpoint, see
[`docs/edison/README.md`](../docs/edison/README.md)) returned the
synthesis archived in PR #7 as
`cad/meta-tools/edison-c0f412d3-literature-synthesis.md`. The
key follow-ups from that synthesis — `build123d` as a sibling to CadQuery,
*Will It Print* (Budinoff 2021) as a more credible AM-DFM source than the
current `cad/dfm.py`, and the Jubilee/Ax-vs-our-actual-hardware caveat —
are reflected in the tables above.

## Files

| File | What it is |
|---|---|
| [`excavator.py`](excavator.py) | Parametric model. `ExcavatorParams` dataclass + `build_*` functions for the trough, arms, pivot pin, strike-off bar, smooth cam ramp, and the pin-slot board (Panel E variant). |
| [`build.py`](build.py) | Exporter — writes STEP + STL for every part and a STEP for the assembly into `cad/build/`, plus a `manifest.json` with the parameter snapshot. |
| [`render.py`](render.py) | **Visualisation.** Renders every part and the full assembly to vector SVGs under [`docs/figures/cad/`](../docs/figures/cad/) using CadQuery's built-in hidden-line SVG exporter — no rasterizer or X server required. Useful for "what does the print actually look like?" without having to load STEP/STL into a viewer. |
| [`dfm.py`](dfm.py) | **Feedback mechanism.** Runs FDM-printability and gantry-only kinematics checks against the current parameter set; non-zero exit code on failure (CI-friendly). |
| [`tests/test_excavator.py`](tests/test_excavator.py) | Unit tests: parts build at default parameters, DFM passes at defaults, deliberate regressions (sub-min-wall trough, off-board slot path) are caught. |

## Usage

From the repo root:

```bash
# install (one-time)
pip install cadquery

# generate STEP/STL for every part + assembly + the manifest
python -m cad.build

# render every part + full assembly to docs/figures/cad/*.svg
python -m cad.render

# run the design-for-manufacturing + gantry-kinematics feedback
python -m cad.dfm

# run the unit tests
python -m unittest discover cad/tests -v
```

The default parameter set in `ExcavatorParams` matches the dimensions called
out in `docs/manuscript/main.tex` (trough length L = 80 mm, L ≈ 3 D, etc.).
Iterate by editing `excavator.py` (or constructing a modified
`ExcavatorParams` with `dataclasses.replace(...)` from a notebook) and
re-running `python -m cad.dfm` — that is the feedback loop.

## What `dfm.py` actually checks

Categories of checks (each prints `[OK]` / `[WARN]` / `[FAIL]`):

* **`sanity.*`** — every dimension must be positive.
* **`fdm.*`** — printability for FDM (min wall thickness ≥ `min_wall`,
  cam-ramp underside overhang ≤ `max_overhang_deg`, rim-lip chamfer present,
  pin clearance positive).
* **`kinematics.cam.*`** — rim lip engages the smooth cam ramp; ramp fits
  inside the gantry's X travel; ramp angle is in the 15–45° band.
* **`kinematics.slot.*`** — the **gantry-only constraint** from PR comment
  4166621470 ("we have a gantry system and would like to avoid installing
  a second axis"): every slot waypoint lies inside the board, the slot's X
  span fits inside `gantry_x_travel`, and the slot's Z span fits inside
  `gantry_z_travel`. Reversals in the slot's X direction are flagged as
  warnings (legal — the gantry just reverses — but worth surfacing).

The exit code is `0` if every error-severity check passes (warnings do not
fail the run), so `python -m cad.dfm` is suitable to drop into CI as a
guardrail for future parameter changes.

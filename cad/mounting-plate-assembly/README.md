# Mounting-plate + baseplate assembly

> Issue: [vertical-cloud-lab/powder-doser#56](https://github.com/vertical-cloud-lab/powder-doser/issues/56)
> Upstream parts (consumed as STL/STEP from `imported-parts/`):
> [#49 geared auger + pinion + NEMA 11](https://github.com/vertical-cloud-lab/powder-doser/pull/49),
> [#51 split tap-collar + mount plate](https://github.com/vertical-cloud-lab/powder-doser/pull/51),
> [#55 split shaft-collar auger bracket](https://github.com/vertical-cloud-lab/powder-doser/pull/55)

This package designs the **foundation** of the powder-doser machine: a
mounting plate that carries the auger brackets (PR #55 ×2), the tap-collar
mount (PR #51) and the NEMA 11 stepper (PR #49), and a baseplate that
holds the other half of the hinge plus a linear-actuator base clevis. The
mounting plate **rotates about the auger's own dispense axis** so that no
part of the hinge ever crosses the powder path, and the baseplate's legs
raise everything above the bench so a cup sits on a scale directly under
the dispense point.

**This PR was rewritten** after review feedback that the first cut used
hand-modelled placeholders for the auger / bracket / tap-collar / motor.
The current version imports the actual most-recent STL/STEP from PRs #49,
#51 and #55 into `imported-parts/`, and the mounting plate's hole pattern
and motor mount are derived from those files' real dimensions (e.g. PR #55
brackets really have only **2 × M3 corner holes at X = ±24**, not the 4
holes I assumed; PR #49's motor is a **NEMA 11 driving a parallel-axis
pinion at C = 32 mm**, not a NEMA 17 sitting square to the plate).

The package was also requested as an **exploration of zoo.dev** for
parametric CAD; see [§ zoo.dev experience](#zoodev-experience-pros--cons)
below.

## Files

```
cad/mounting-plate-assembly/
├── imported-parts/                   ← real geometry from upstream PRs
│   ├── auger-geared/                  – PR #49: auger + pinion + preview
│   ├── auger-bracket/                 – PR #55: bracket
│   └── tap-collar/                    – PR #51: collar + mount plate
├── kcl/                              ← primary zoo.dev sources (KCL)
│   ├── params.kcl                    – shared parameter sheet
│   ├── mounting_plate.kcl
│   ├── baseplate.kcl
│   └── hinge_pin.kcl
├── cad_model.py                      ← CadQuery mirror (parametric)
├── render_views.py                   ← VTK iso/front/top/side PNG per part
├── render_assembly.py                ← full-assembly + diagrams (matplotlib)
├── step/                             ← per-part .step (printer-ready)
├── stl/                              ← per-part .stl   (printer-ready)
├── views/                            ← per-part PNG renders (4 views each)
└── assembly/
    ├── assembly_iso.png  / _front / _top / _side  ← 3-D renders
    ├── assembly_45deg_iso.png / assembly_90deg_iso.png
    ├── full_assembly.step
    ├── installation_diagram.png      ← top view, every mounting hole labelled
    ├── rotation_0_45_90.png          ← tilt sequence driven by actuator
    └── powder_flow.png               ← auger → dispense → cup
```

## Design summary

The auger (PR #49, Ø25 × 250 mm with a Ø50 spur gear band at `total_h/3`
from the dispensing end) lies along **+Y**, dispense end at Y = +125 and
motor end at Y = −125. Two PR #55 brackets bolt FLANGE-UP to the mounting
plate's underside at `Y = ±95` and grip the auger 9.74 mm below the plate
underside; the resulting **auger centreline is at `Z = Z_AUG = −25.74 mm`**.
The PR #51 tap-collar wraps the auger at `Y = -40` between the two
brackets, bolted to the plate via its own mount-plate at `Y = -40` (`2 × M3
at X = ±24`).

**Parallel-axis stepper drive.** PR #49 mates the auger gear band (Ø50
tip, 48T module-1) with a Ø18 pinion (16T module-1) on a NEMA 11 shaft, at
the standard `C = (Z₁ + Z₂)·m / 2 = 32 mm` centre distance. The mounting
plate has an **integrated motor-mount boss on its underside** at
`(X_MOTOR = +32, Y = motorFaceY, Z = Z_AUG)`, with the four standard
NEMA 11 `23 mm`-pitch face holes (M3 in our boss; the motor itself takes
M2.5 — use the standard short M2.5 screws or step-tap to M3) and a Ø22
pilot for the pinion / shaft. A small clearance slot is cut through the
plate over the gear band so the Ø50 band tip is not constrained at the
plate underside.

**Hinge axis = dispense-point axis.** The mounting plate has two yoke arms
extending in +Y past the front edge; each arm drops down to an **eye whose
bore axis is along X** and whose centre line is at the auger centreline
(`Z = Z_AUG = -25.74 mm`). The two eyes are separated by `yokeEyeGap =
26 mm` so the powder slot stays open. The baseplate has a **single
central tang** that fits in that gap; one M5 hinge pin passes through eye
→ tang → eye on the dispense axis. Because the rotation axis IS the
dispense axis, neither hinge hardware nor any structural member ever
crosses the powder path at any tilt.

The baseplate has a `60 × 60 mm` powder window centred under the dispense
point, four `95 mm` corner legs that clear a 50 mm cup on a 30 mm scale,
and a rear clevis for the linear-actuator base. A short lug hangs from
the mounting plate underside at `actLugY = −60 mm` to receive the
actuator's rod-end clevis pin. Both pivots use the same M5 pin.

### Mounting-hole map (top view)

`installation_diagram.png` shows every hole on the mounting plate labelled
by the part it mates with. All hole-spacings match the upstream parts'
own bolt patterns:

| Part                  | Source PR | Pattern                                 | Hole size  | Centre Y (mm) |
| --------------------- | --------- | --------------------------------------- | ---------- | ------------- |
| Bracket FRONT         | #55       | 2 × M3 at X = ±24                       | Ø3.4 (M3)  | +95           |
| Bracket REAR          | #55       | 2 × M3 at X = ±24                       | Ø3.4 (M3)  | −95           |
| Tap-collar mount      | #51       | 2 × M3 at X = ±24                       | Ø3.4 (M3)  | −40           |
| NEMA 11 motor mount   | #49       | 4 × M3 at 23 mm pitch + Ø22 pilot       | Ø3.4 (M3)  | ≈+19 (motor face) |
| Yoke eyes (hinge)     | this PR   | 2 eyes along X, gap 26 mm               | Ø5.4 (M5)  | +125          |
| Actuator rod-end lug  | this PR   | cross-bore on a 24 mm-tall lug          | Ø5.4 (M5)  | −60           |

### Rotation kinematics

`rotation_0_45_90.png` walks the assembly through 0°, 45° and 90° tilt
about the hinge axis. At 0° the auger is horizontal; at 90° it points
straight down through the baseplate's powder window. The diagram annotates
the corresponding linear-actuator length (computed live from the current
pivot placement):

| Tilt | Actuator length |
| ---- | --------------- |
| 0°   | ≈ 74 mm         |
| 45°  | ≈ 130 mm        |
| 90°  | ≈ 270 mm        |

The current pivot placement gives a large length swing (≈ 196 mm) for a
0–90° sweep, which is more than a typical Actuonix L12 (50 mm stroke) can
deliver. Two easy fixes — both for follow-up:
* Move `actLugY` further from the hinge to shorten the required stroke
  (longer lever arm = smaller dL / dθ near 0°).
* Use a longer-stroke actuator class (e.g. L16-100) or stack two L12s.

### Powder-flow

`powder_flow.png` traces powder from the auger (rotation moves it in
−Y → +Y), out the auger's dispense end at the auger tip, straight down
through the gap between the yoke eyes, then through the baseplate's powder
window, and into the cup on the scale. The path is gravity-only,
completely unobstructed at any tilt between 0° and 90°.

## Reproducing the renders

This package ships **two equivalent build paths**. In the Copilot
sandbox we used the CadQuery path because the zoo.dev account ran out of
included quota (see below) — both paths consume the same parameter sheet
(`kcl/params.kcl` for KCL, the duplicated constants at the top of
`cad_model.py` for CadQuery).

### A. CadQuery (worked here)

```sh
pip install cadquery matplotlib numpy vtk
sudo apt install xvfb

cd cad/mounting-plate-assembly
python3 cad_model.py                    # → step/*.step, stl/*.stl
xvfb-run -a python3 render_views.py     # → views/<part>_(iso|front|top|side).png
xvfb-run -a python3 render_assembly.py  # → assembly/*.png + full_assembly.step
```

### B. zoo.dev (requires a funded account)

```sh
# Install the zoo CLI:
curl -fsSL https://github.com/KittyCAD/cli/releases/download/v0.2.171/zoo-x86_64-unknown-linux-musl \
  -o /usr/local/bin/zoo && chmod +x /usr/local/bin/zoo
export ZOO_API_TOKEN=…

cd cad/mounting-plate-assembly/kcl
for part in mounting_plate baseplate hinge_pin ; do
  zoo kcl export --output-format step ${part}.kcl ../step/${part}.step
  zoo kcl export --output-format stl  ${part}.kcl ../stl/${part}.stl
  zoo kcl snapshot ${part}.kcl ../views/${part}_iso.png
done
```

## zoo.dev experience: pros & cons

Authoring this package against zoo.dev exposed both real strengths and
real friction.  Honest report:

### Pros

* **KCL is concise and readable.**  Pipe-chained `startSketchOn(...) |>
  startProfile(...) |> line(...) |> close() |> extrude(length = ...)`
  reads almost like a CAD recipe and is easy to diff in code review.
  Modules import each other (`import "params.kcl" as p`) which makes a
  shared parameter sheet trivial.
* **One toolchain for everything.**  The `zoo` CLI gives `kcl export`
  (STEP / STL / glTF / etc.), `kcl snapshot` (PNG), `kcl format`, and
  `ml text-to-cad` from the same binary; no separate STL exporter, viewer,
  or screenshot tool is needed.  In CadQuery you assemble those yourself
  (cq.exporters, VTK + xvfb, matplotlib).
* **Text-to-CAD is a real prototyping accelerator** for simple parametric
  primitives — the cup placeholder here is exactly the kind of thing that
  is faster to *describe* than to model.
* **Hosted geometry kernel.**  No local OpenCascade or VTK install needed
  on a CI runner; the CLI shells out to api.zoo.dev.

### Cons (encountered first-hand)

* **Quota is real, low, and silently breaks renders mid-task.**  Halfway
  through this package the account hit `HTTP 402 missing_payment_method`:
  the websocket-based `kcl export` started rejecting every request with
  the misleading error `engine: Please send { headers: { Authorization:
  "Bearer <token>" } } over this websocket.` even though `zoo auth status`
  reported a valid logged-in session.  The real diagnosis only appeared
  when calling the REST API directly (`POST /ai/text-to-cad/step` →
  `402: missing_payment_method`).  **This is the single biggest issue:**
  a cloud-only workflow with an opaque quota is fragile compared to a
  local kernel.  I had to fall back to CadQuery to finish the package.
* **No local kernel.**  Without quota the CLI is unable to compute *any*
  geometry — even just exporting a 5-line sketch.  CadQuery on the same
  machine produced all ten parts in under 10 s with no network.
* **Iteration API is finicky.**  The `/ml/text-to-cad/iteration` endpoint
  is 1-indexed (line 0 / column 0 returns `Source range out of bounds`,
  even though that's the convention used by every diff tool) and only
  returns patched source, not a new STEP blob.
* **KCL gotchas worth knowing:**
  * `circle(center = [...], radius = …)` is *positional-with-keyword*; the
    similar-looking `arc()` and `line()` use different keyword names.
  * `fn(@x, y)` uses `@` to mark the first positional arg — easy to miss.
  * Booleans are implicit: extruded sketches subtract from solids they
    intersect inside the same chain, but **not** across solids assigned to
    different variables — you have to be explicit with the order.
  * Translating an existing solid in place is awkward; you generally
    rebuild the geometry centred on the target instead, which makes
    multi-part assemblies harder than in CadQuery's `.translate()` /
    `Assembly` API.
* **Text-to-CAD is fragile** for anything more complex than a primitive.
  Returns only STEP (no parametric source), so subsequent edits require
  the iteration API and a heuristic source-range guess.

### Verdict

Use zoo.dev when you want a hosted, "describe-then-render" pipeline for
simple parts and don't mind a quota dependency — it's genuinely faster
than wiring up VTK + xvfb yourself.  Don't put it on the critical path of
a long-running CI job or an offline lab workflow; a local kernel
(CadQuery, OpenSCAD, build123d) is more reliable for those use cases.
This package *commits both paths* so neither failure mode blocks the
other.

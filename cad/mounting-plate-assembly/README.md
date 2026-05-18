# Mounting-plate + baseplate assembly

> Issue: [vertical-cloud-lab/powder-doser#56](https://github.com/vertical-cloud-lab/powder-doser/issues/56)
> Related parts: bracket [#46](https://github.com/vertical-cloud-lab/powder-doser/issues/46), gear-band auger [#48](https://github.com/vertical-cloud-lab/powder-doser/issues/48), tap-collar [#50](https://github.com/vertical-cloud-lab/powder-doser/issues/50)

This package designs the **foundation** of the powder-doser machine: a
mounting plate that carries the auger brackets, tap-collar mount and NEMA
17 stepper, and a baseplate that holds the other half of the hinge plus a
linear-actuator placeholder.  The mounting plate **rotates about the auger's
own dispense axis** so that no part of the hinge ever crosses the powder
path, and the baseplate's legs raise everything above the bench so a cup
sits on a scale directly under the dispense point.

The package was also requested as an **exploration of zoo.dev** for
parametric CAD; see [§ zoo.dev experience](#zoodev-experience-pros--cons)
below.

## Files

```
cad/mounting-plate-assembly/
├── kcl/                              ← primary zoo.dev sources (KCL)
│   ├── params.kcl                    – shared parameter sheet
│   ├── mounting_plate.kcl
│   ├── baseplate.kcl
│   ├── hinge_pin.kcl
│   ├── linear_actuator_placeholder.kcl
│   ├── cup_placeholder.kcl
│   ├── scale_placeholder.kcl
│   ├── auger_placeholder.kcl
│   ├── bracket_placeholder.kcl
│   ├── tap_collar_mount_placeholder.kcl
│   └── nema17_placeholder.kcl
├── cad_model.py                      ← CadQuery mirror (parametric)
├── render_views.py                   ← VTK iso/front/top/side PNG per part
├── render_assembly.py                ← full-assembly + diagrams (matplotlib)
├── render_with_zoo.sh                ← rerun every part through `zoo kcl …`
├── submit_text_to_cad.py             ← cup via zoo.dev Text-to-CAD
├── step/                             ← per-part .step (printer-ready)
├── stl/                              ← per-part .stl   (printer-ready)
├── views/                            ← per-part PNG renders (4 views each)
└── assembly/
    ├── assembly_iso.png  / _front / _top / _side  ← 3-D renders
    ├── full_assembly.step
    ├── installation_diagram.png      ← top view, every mounting hole labelled
    ├── rotation_0_45_90.png          ← tilt sequence driven by actuator
    └── powder_flow.png               ← auger → dispense → cup
```

## Design summary

The auger lies along **+Y**, motor at −Y end, dispense hole on the −Z side
of the tube near the +Y tip.  Two brackets (the shaft-collar style from
#46) hang from the mounting plate's underside and grip the auger; one
tap-collar mount-plate (#50) sits between them; one NEMA 17 stepper hangs
from the rear of the plate driving the auger's spur band (#48).

**Hinge axis = dispense-point axis.**  The mounting plate has two yoke arms
extending in +Y past the front edge; each arm drops down to an **eye whose
bore axis is along X** and whose centre line is at the auger centreline
(`Z = HINGE_Z = −16 mm`).  The two eyes are separated by a `yokeEyeGap = 24
mm` powder slot.  The baseplate has a **single central tang** that fits in
that gap; one M5 hinge pin passes through eye→tang→eye on the dispense
axis.  Because the rotation axis IS the dispense axis, neither hinge
hardware nor any structural member ever crosses the powder path at any
tilt.

The baseplate has a `60 × 60 mm` powder window centred under the dispense
point, four `95 mm` corner legs that clear a 50 mm cup on a 30 mm scale,
and a rear clevis for the linear-actuator base.  A short lug hangs from
the mounting plate underside at `actRodPlateY = −40 mm` to receive the
actuator's rod-end clevis pin.  Both pivots use the same M5 pin.

### Mounting-hole map (top view)

`installation_diagram.png` shows every hole on the mounting plate labelled
by the part it mates with:

| Part                  | Pattern (X span × Y span, mm) | Hole size  | Centre Y (mm) |
| --------------------- | ----------------------------- | ---------- | ------------- |
| Bracket REAR (#46)    | 16 × 22, 4 holes              | Ø3.4 (M3)  | −55           |
| Bracket FRONT (#46)   | 16 × 22, 4 holes              | Ø3.4 (M3)  | +25           |
| Tap-collar mount (#50)| 16 × 22, 4 holes              | Ø3.4 (M3)  | +5            |
| NEMA 17               | 31 × 31, 4 corner + Ø22.5 pilot | Ø3.4 (M3) | −75           |
| Yoke eyes             | 2 eyes along X                | Ø5.4 (M5)  | +112          |
| Actuator rod-end lug  | cross-bore on a 16 mm-tall lug | Ø5.4 (M5) | −40           |

### Rotation kinematics

`rotation_0_45_90.png` walks the assembly through 0°, 45° and 90° tilt
about the hinge axis.  At 0° the auger is horizontal; at 90° it points
straight down.  The diagram annotates the corresponding linear-actuator
length:

| Tilt | Actuator length |
| ---- | --------------- |
| 0°   | ≈ 43 mm         |
| 45°  | ≈ 139 mm        |
| 90°  | ≈ 248 mm        |

The current pivot placement gives a large length swing (≈ 205 mm) for a
0–90° sweep, which is more than a typical Actuonix L12 (50 mm stroke) can
deliver.  Two easy fixes — both for follow-up:
* Move `actRodPlateY` further from the hinge to shorten the required
  stroke (longer lever arm = smaller dL / dθ near 0°).
* Use an L16-100 or larger actuator class.

### Powder-flow

`powder_flow.png` traces powder from the auger (rotation moves it in +Y),
out the dispense hole at the auger tip, straight down through the gap
between the yoke eyes, then through the baseplate's powder window, and
into the cup on the scale.  The path is gravity-only, completely
unobstructed at any tilt between 0° and 90°.

## Reproducing the renders

This package ships **two equivalent build paths**.  In the Copilot
sandbox we used the CadQuery path because the zoo.dev account ran out of
included quota (see below) — but both produce identical geometry from the
same parameter sheet.

### A. CadQuery (worked here)

```sh
pip install cadquery matplotlib numpy vtk
sudo apt install xvfb

cd cad/mounting-plate-assembly
xvfb-run -a python3 cad_model.py        # → step/*.step, stl/*.stl
xvfb-run -a python3 render_views.py     # → views/<part>_(iso|front|top|side).png
xvfb-run -a python3 render_assembly.py  # → assembly/*.png + full_assembly.step
```

### B. zoo.dev (requires a funded account)

```sh
# Install the zoo CLI:
curl -fsSL https://github.com/KittyCAD/cli/releases/download/v0.2.171/zoo-x86_64-unknown-linux-musl \
  -o /usr/local/bin/zoo && chmod +x /usr/local/bin/zoo

export ZOO_API_TOKEN=…
./render_with_zoo.sh                    # → step/*, stl/*, views/*
python3 submit_text_to_cad.py           # → step/cup_text_to_cad.{step,json}
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

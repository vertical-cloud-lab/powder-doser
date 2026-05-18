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

**This PR was rewritten twice** in response to review feedback:
1. The first cut used hand-modelled placeholders for the auger / bracket
   / tap-collar / motor.  The next iteration imported the actual
   most-recent STL/STEP from PRs #49, #51 and #55 into
   `imported-parts/`, and the mounting plate's hole pattern and motor
   mount are derived from those files' real dimensions (e.g. PR #55
   brackets really have only **2 × M3 corner holes at X = ±24**, not the
   4 holes I assumed; PR #49's motor is a **NEMA 11 driving a
   parallel-axis pinion at C = 32 mm**, not a NEMA 17 sitting square to
   the plate).
2. The **previous** revision aligned the layout with the original
   hand-drawn spec attached to
   [#62 Mounting Plate Design](https://github.com/vertical-cloud-lab/powder-doser/issues/62)
   — every component on the **TOP** of the plate, hinge through the
   auger's dispense point, plate asymmetric in X, component order
   along the auger matching the drawing.
3. The **previous** revision implemented the issue #62 *follow-up*
   review (comment 4314329233): face-mounted NEMA-11, auger raised on
   bracket plinths so the gear band tip cleared the plate top, single
   U-notch for the auger overhang, two SEPARATE side hinges fed by
   full-width front ramps, hinge axis 10 mm forward of the baseplate.
4. The **current** revision implements the issue #62 *third* review
   (comment 4314491753):
   * **Auger now sits in the middle** of the plate (X=0).  The plate
     is **symmetric about X=0** (`X ∈ [−54.1, +54.1]`); the central
     auger gap in the +Y edge is therefore in the middle.
   * **Equal-sized, thicker hinges** (Ø14 × 10 mm-thick eyes,
     mirror-symmetric about X=0; previously Ø12 × 6 mm).
   * **Bracket plinths removed** — brackets bolt directly to the plate
     top.  The auger axis is now at the bracket's native bore height
     (Z_AUG ≈ 19.74 mm above plate top, down from 30.25 mm).  A
     minimum gear-band+pinion clearance cutout is reintroduced under
     the band only, so the rest of the plate stays solid.
   * **Plate underside is now feature-free** — the linear-actuator
     rod-end lug that used to hang below the plate has been removed.

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

The layout follows the issue
[#62 Mounting Plate Design](https://github.com/vertical-cloud-lab/powder-doser/issues/62)
drawing and its **follow-up review** (comment 4314329233):

* **Components on TOP of the plate.**  Front bracket, tap-collar mount,
  NEMA-11 motor mount block, front ramps and hinge eye-tabs all sit on
  the plate top.  Nothing hangs below except the linear-actuator
  rod-end pivot lug.
* **No holes or gaps in the plate other than mounting holes** and a
  single open **U-notch in the +Y plate edge** that lets the auger
  overhang in mid-air at the dispense end.
* **Auger raised on integrated plinths.**  The brackets bolt
  flange-down onto `~10.5 mm`-tall integrated plinths at `Y = ±` their
  respective Ys, raising the auger axis to `Z_AUG = +30.25 mm`.  At
  that height the Ø50 gear-band tip clears the plate top by 5 mm — no
  through-plate clearance slot needed.  The tap-collar mount bolts
  **flush** on the plate top (no plinth) because the upstream
  tap-collar's native bore is at exactly `+30.25 mm` above its
  mating face.
* **Motor face-mounted** on a vertical wall on the plate top: the
  NEMA-11 bolts through the wall's **+Y face** (i.e. its **front** face,
  permitted by the follow-up review).  The motor body extends in **−Y**
  away from that face; its shaft + 16T pinion pokes back through the
  wall's Ø22 pilot and meshes with the auger's Ø50 gear band at the
  standard `C = 32 mm` centre distance.
* **Asymmetric in X.**  Plate `X ∈ [−34, +54]` — clear side at −X, the
  motor block extends out the +X side.
* **Component order along the auger (hinge end → motor end):**
  `hinge axis @ Y=+125` → `front bracket @ Y=+85` → `tap-collar mount
  @ Y=+60` → `NEMA-11 over the gear band @ Y=+41.67` → `rear bracket
  @ Y=−95`.  Front bracket + tap-collar Ys shifted back ~10 mm vs. the
  prior revision to make room for the new front ramps.
* **Two SEPARATE side hinges** (one each side of the auger gap).  A
  single central hinge would foul the auger; instead each side carries
  one mounting-plate eye + one baseplate arm eye, butted axially on
  one short M5 pin.  The mounting plate's two eye-tabs and the two
  full-width **front ramps** together cover the entire +Y face of the
  plate except for the auger gap.
* **Hinge axis is 10 mm in front of the baseplate's front edge.**
  Baseplate `Y ∈ [−135, +115]`, hinge axis at `Y = +125`.  The
  baseplate has two **forward-and-up hinge arms** (one each side of
  the auger) that reach from `Y = +115` forward to `Y = +125`, rising
  from the baseplate top up to the hinge axis.
* **No powder window** in the baseplate — the dispense point sits
  10 mm forward of the baseplate's front edge, so powder falls in
  front of the baseplate directly into the cup on the scale.

**Geometry.**  The auger (PR #49, Ø25 × 250 mm with a Ø50 spur-gear
band centred at `total_h/3` from the dispense end) lies along **+Y**,
dispense end at `Y = +125`.  Two PR #55 brackets bolt flange-down onto
~10.5 mm plinths at `Y = +85` / `Y = −95`, gripping the auger 19.74 mm
above the plinth top → auger axis at `Z = +30.25 mm`.  The PR #51
tap-collar wraps the auger at `Y = +60`, bolted flush to the plate top.

**Hinge axis = dispense-point axis.**  Two side eye-tabs on the plate
top (at `X = ±19`) carry the bore at `(Y = +125, Z = +30.25)` — the
auger's dispense point.  Two matching baseplate arms carry the
matching eye on the same axis, offset outboard at `X = ±26`.  Two
short M5 pins (one per side) tie the two halves together.  Because
the rotation axis IS the dispense axis, the dispense point literally
**does not move** while the plate tilts 0–90° (see
`rotation_0_45_90.png` — red dot is fixed across all three tilts).

### Mounting-hole map (top view)

`installation_diagram.png` shows every hole on the mounting plate
labelled by the part it mates with.  All hole spacings match the
upstream parts' own bolt patterns:

| Part                  | Source PR | Pattern                                              | Hole size  | Centre Y (mm) |
| --------------------- | --------- | ---------------------------------------------------- | ---------- | ------------- |
| Front bracket         | #55       | 2 × M3 at X = ±24 (on a ~10.5 mm plinth)             | Ø3.4 (M3)  | +85           |
| Tap-collar mount      | #51       | 2 × M3 at X = ±24 (flush — no plinth)                | Ø3.4 (M3)  | +60           |
| NEMA 11 motor mount   | #49       | 4 × M3 at 23 mm pitch + Ø22 pilot **on the vertical front face of the wall** | Ø3.4 (M3) | motor face at +34.67 |
| Rear bracket          | #55       | 2 × M3 at X = ±24 (on a ~10.5 mm plinth)             | Ø3.4 (M3)  | −95           |
| Side hinge eyes (×2)  | this PR   | 2 separate eye-tabs at X = ±19, one each side of the auger gap | Ø5.4 (M5)  | +125         |
| Actuator rod-end lug  | this PR   | cross-bore on a 24 mm-tall lug (UNDERSIDE)           | Ø5.4 (M5)  | −60           |

### Rotation kinematics

`rotation_0_45_90.png` walks the assembly through 0°, 45° and 90° tilt
about the hinge axis.  At 0° the auger is horizontal; at 90° it points
straight down past the front of the baseplate into the cup.  The
diagram annotates the corresponding linear-actuator length (computed
live from the current pivot placement).

The current pivot placement gives a large length swing (≈ 200 mm) for
a 0–90° sweep, which is more than a typical Actuonix L12 (50 mm
stroke) can deliver.  Noted as a follow-up for the BOM stage — easy
fixes are:
* Move `ACT_LUG_Y` further from the hinge to shorten the required stroke.
* Use a longer-stroke actuator class (e.g. L16-100) or stack two L12s.

### Powder-flow

`powder_flow.png` traces powder from the auger (rotation moves it
−Y → +Y), out the auger's dispense end at the auger tip, then
**straight down in front of the baseplate** (the baseplate's front
edge sits 10 mm behind the dispense point) into the cup on the scale.
The path is gravity-only, completely unobstructed at any tilt between
0° and 90°.

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

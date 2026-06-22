# Mounting-plate + baseplate assembly

> Issue: [vertical-cloud-lab/powder-doser#56](https://github.com/vertical-cloud-lab/powder-doser/issues/56)
> Upstream parts (consumed as STL/STEP from `imported-parts/`):
> [#49 geared auger + pinion + NEMA 11](https://github.com/vertical-cloud-lab/powder-doser/pull/49),
> [#51 split tap-collar + mount plate](https://github.com/vertical-cloud-lab/powder-doser/pull/51),
> [#47 lifted split shaft-collar auger bracket](https://github.com/vertical-cloud-lab/powder-doser/pull/47)

> **View in Onshape (interactive, public — ALL parts):**
> <https://cad.onshape.com/documents/1ef016b2b8f24272a968265d/w/0085fb652e7ecf313b560ada>
> — the **complete** assembly (`full_assembly.step`: mounting plate,
> baseplate, both hinge pins, both servo pinions, **plus** the imported
> auger, both auger brackets, the tap-collar + mount plate, the stepper
> pinion, and simplified NEMA-11 / MG996R bodies) imported as a public
> Onshape document so you can orbit/zoom to any angle instead of the fixed
> PNG perspectives. Several pre-rendered iso angles also live in
> `assembly/assembly_iso_az###.png` (orbited every 45° about the vertical
> axis) plus `assembly_iso_high.png` / `assembly_iso_low.png`.

This package designs the **foundation** of the powder-doser machine: a
mounting plate that carries the auger brackets (PR #47 ×2), the tap-collar
mount (PR #51) and the NEMA 11 stepper (PR #49), and a baseplate that
holds the other half of the hinge. The
mounting plate **rotates about the auger's own dispense axis** so that no
part of the hinge ever crosses the powder path, and the baseplate's legs
raise everything above the bench so a cup sits on a scale directly under
the dispense point.

**This PR has been iterated several times** in response to review feedback.
The **current** revision implements the issue #62 *fifth* review
(comment 4320428756):

* **Lifted PR #47 brackets** replace the earlier PR #55 ones.  The
  14 mm-thick flange raises the auger axis to `Z_AUG = +29.25 mm`,
  giving the Ø50 gear band 4.25 mm of radial clearance over a flat
  plate.  The gear-band clearance slot in the plate is gone.
* **Updated PR #51 tap-collar mount plate** (60 × 18 × 14, bore at the
  same Z = 29.25 mm as the bracket) — bracket and tap-collar bolt flat
  to the same plate top with no shim and the auger threads through
  both at the same Z.
* **Gear band, tap collar and front bracket are packed flush** with
  only 1 mm of air clearance between adjacent ring faces, so gravity
  pushes them against the front bracket.
  (`Y_GEAR_BAND = +41.67`, `Y_TAP = +56.67`, `Y_BRK_FRONT = +72.67`.)
* **Pinion centred on the gear band in Y** — the motor face is set so
  the pinion centre lands exactly on the gear band centre (previously
  it was offset by 8 mm).
* **3-layer sandwich hinges.**  Each side of the auger gap carries
  `{inner mounting-plate lobe, middle baseplate arm, outer
  mounting-plate lobe}` sharing one long M5 pin per side.  Each
  layer takes one third of its ramp half-span (`≈ 12.7 mm`), so the
  hinges span the entire front of the plate.

### Servo-driven hinge (issue #63)

The mounting-plate tilt is now driven by an **MG996R servo** through
a **2:1 spur-gear reduction**:

* **Hinge gear** — the outermost +X mounting-plate hinge lobe carries
  an integrated **40-tooth, m ≈ 0.908** spur-gear band (PCD 36.3,
  tip Ø 38.2,
  face width = lobe thickness ≈ 12.30 mm).  The gear is part of the
  mounting plate's single solid — not a separate STL.
* **Servo pinion** (new part `servo_pinion.{step,stl}`) — **20 teeth,
  m ≈ 0.908** (PCD 18.2, tip Ø 20.2), giving a **2:1 reduction** at
  `C = 27.25 mm` — the module is back-solved so that the 40-T hinge
  gear at the auger axis still meshes with the 20-T pinion whose
  spline axis sits exactly 10 mm above the baseplate top (= the
  centreline of the MG996R's 20 mm-thick body, per the dimensioned
  drawing).  Bore is Ø 6 with a 0.5 mm chordal flat for set-screw
  retention on the MG996R 25-T spline (the simplest printable
  interface — for production swap to a true 25-T spline socket).
* **Gear tooth profile** — both the hinge gear band and the servo
  pinion use **true involute** tooth flanks (base-circle involute
  sampled at 12 points per flank + a 3-point tip arc), matching the
  involute teeth produced by PR #49's `spur_gear_2d` (`cad/auger-geared/gear-teeth.scad`).  No more straight-flank
  trapezoidal teeth.
* **Servo mount — two square posts** (per Will's PR #66 reviews).
  Instead of a full-face wall, the MG996R bolts to **two separate
  square posts** (clean rectangular pillars — no back brace/wedge), one
  under each flange ear.  Each post carries that ear's **two Ø 5 mm
  holes** on the MG996R 49.5 × 10 mm flange pattern (hole-centre Y
  offsets from the spline axis −14.85 mm and +34.65 mm, read directly
  from the dimensioned drawing).  Key fixes from Will's
  comment 4624739034:
    * **The body protrudes between the posts.**  The gap between the
      posts' inner faces is the **40 mm body length** (+1 mm clearance),
      so the MG996R body + output boss pass cleanly through the open gap
      between them — the posts sit just *outboard* of each body end.
    * **Posts placed behind the holes; driving head overhangs 5 mm.**
      Per Will's comments 4625212895 / 4633722007 the posts sit *behind*
      the servo's mounting holes and the servo is positioned so the very
      **tip of its driving head hangs 5 mm past the baseplate front
      edge** (revised down from 8 mm).  The driving head (output boss +
      horn) physically protrudes `6 mm + 2 mm = 8 mm` above the body
      top per the dimensioned drawing; with the flange seated 3 mm
      inboard of the body top plane only the outermost 5 mm of the
      driving head now overhangs.  The MG996R mounting flange (the two
      ears) is at the body top, so the flange seating plane = the
      baseplate (porch) front edge.  The posts' inboard (−X) face is
      therefore set at `X = +59.0 mm` (= the gear's near face at
      `+54.0 mm` plus the 5 mm overhang).  The pinion on the servo
      spline still lands exactly on the hinge-gear face, so the centre
      distance — and the 2:1 ratio — are unchanged (the gears themselves
      are untouched, as the placement only moves in X).
  The **servo body** sits at `X ∈ [+59.0, +95.8] mm` and rests on a
  forward **porch** of baseplate-thickness material under the servo
  footprint.  The cantilevered porch is **structurally tied** to the
  baseplate by a **triangular flange under the tabletop** that ties it
  down to the adjacent (+X) front leg, resisting the bending the servo's
  weight + lifting reaction torque would otherwise put into the
  cantilever.
* **DUAL servo lift + stripped-down baseplate** (per Will's comment
  4721011696).  The single +X servo mount is now **mirrored onto the
  −X side** so the mounting plate is driven by **two servos +
  two hinge-gear bands** working together — a second 40-tooth gear
  band is added to the −X outer mounting-plate hinge lobe (mirror of
  the +X gear band), and the porch + two square posts + underside
  flange are duplicated on the −X side with identical geometry.  At
  the same time the **legs and most of the rear of the baseplate are
  gone** — the part is now a small forward-only **rectangular
  mounting tab** (200 mm wide × 60 mm deep, `Y ∈ [+55, +115]`) with
  the two **rear corners chamfered 25 × 45°**, that bolts onto a
  separate frame via **four Ø5 M5 mounting holes** near the four tab
  corners (X = ±80, Y = +68 and +105).  The underside flange is **kept
  and enhanced**: it's a 40 mm-deep rectangular rib under the servo
  body with a **supportive triangular gusset** (XZ-plane rib,
  10 × 20 mm) sitting **right under the servo mount** so it intersects
  both the flange and the baseplate, and a **horizontal M5 mounting
  hole** (axis parallel to the auger / Y, at the 0° datum) drilled
  **through the gusset** (Z = baseplate bottom − 15 mm), so each
  flange also acts as a side-bolting feature.  The hinge-arm depth is
  also reduced slightly (40 → 35 mm) to clear the front bracket.
* **Trapezoidal tabletop on a tripod** *(superseded — see "DUAL servo
  lift" above; the trapezoidal tripod has been replaced with a
  rectangular forward-only mounting tab)*.  The previous baseplate
  was a trapezoidal tabletop standing on a tripod (two front-corner
  legs + one rear-centre leg).
* **Gear tooth profile** — both the hinge gear band and the servo
  pinion use **true involute** tooth flanks (base-circle involute
  sampled at 12 points per flank + a 3-point tip arc), matching the
  involute teeth produced by PR #49's `spur_gear_2d` (`cad/auger-geared/gear-teeth.scad`).  No more straight-flank
  trapezoidal teeth.
* **Hinge-arm back face is sloped**, not vertical — the back-top corner
  of each baseplate hinge arm is replaced with a ~58°-from-horizontal
  slope (the back edge runs from `Y = +75` at the baseplate top up to
  `Y = +91` at the hinge-axis level).  This gives the mounting plate's
  underside clearance to sweep through 45° and beyond without colliding
  with the arm.
* **Interference fix** — the baseplate's middle-third hinge arms used
  to pierce the mounting-plate body at 0° fold-down (5904 mm³ of
  overlap).  The fix cuts two vertical clearance slots through the
  plate (one per arm) at `Y ∈ [+73, +117]`, X-bands matching the arm
  spans with ±0.5 mm clearance, so the arms pass cleanly through the
  plate when folded.
* **Validation** — `cad_model.py` now defines
  `validate_no_interference()` which is called from `main()` and
  reports the intersection volume of:
    * `mounting_plate ∩ baseplate` at 0° (folded flush) — **0.00 mm³**
    * `mounting_plate ∩ baseplate` at 45°                 — **0.00 mm³**
    * `mounting_plate ∩ baseplate` at 90° (vertical)      — **0.00 mm³**
    * `pinion ∩ baseplate` (installed servo)              — **0.00 mm³**

The package was also requested as an **exploration of zoo.dev** for
parametric CAD; see [§ zoo.dev experience](#zoodev-experience-pros--cons)
below.

## Files

```
cad/mounting-plate-assembly/
├── imported-parts/                   ← real geometry from upstream PRs
│   ├── auger-geared/                  – PR #49: auger + pinion + preview
│   ├── auger-bracket/                 – PR #47: lifted bracket
│   └── tap-collar/                    – PR #51: collar + mount plate
├── kcl/                              ← primary zoo.dev sources (KCL)
│   ├── params.kcl                    – shared parameter sheet
│   ├── mounting_plate.kcl
│   ├── baseplate.kcl
│   └── hinge_pin.kcl
├── cad_model.py                      ← CadQuery mirror (parametric)
├── render_views.py                   ← VTK iso/front/top/side PNG per part
├── render_assembly.py                ← full-assembly + diagrams (matplotlib)
├── onshape_upload.py                 ← push full_assembly.step to a public Onshape doc
├── step/                             ← per-part .step (printer-ready)
├── stl/                              ← per-part .stl   (printer-ready)
├── views/                            ← per-part PNG renders (4 views each)
└── assembly/
    ├── assembly_iso.png  / _front / _top / _side  ← 3-D renders
    ├── assembly_45deg_iso.png / assembly_90deg_iso.png
    ├── assembly_iso_az000..315.png   ← iso orbited every 45° (pick best angle)
    ├── assembly_iso_high.png / assembly_iso_low.png  ← higher/lower iso elevation
    ├── full_assembly.step             ← ALL parts (new + imported), Onshape-ready
    ├── installation_diagram.png      ← top view, every mounting hole labelled
    ├── rotation_0_45_90.png          ← tilt sequence about the auger dispense point
    └── powder_flow.png               ← auger → dispense → cup
```

## Design summary

The layout follows the issue
[#62 Mounting Plate Design](https://github.com/vertical-cloud-lab/powder-doser/issues/62)
drawing and its five rounds of review:

* **Components on TOP of the plate.**  Front bracket, tap-collar mount,
  NEMA-11 motor mount block, front ramps and hinge lobes all sit on
  the plate top.  Nothing hangs below — the plate underside is
  completely feature-free.
* **No holes or gaps in the plate other than mounting holes** and a
  single open **U-notch in the +Y plate edge** that lets the auger
  overhang in mid-air at the dispense end.
* **Lifted brackets (PR #47) — no plinths, no slot.**  The 14 mm-thick
  bracket flange raises the auger axis to `Z_AUG = +29.25 mm`.  At
  that height the Ø50 gear-band tip clears the plate top by 4.25 mm,
  so the gear-band clearance slot in the plate is gone.  The PR #51
  tap-collar bolts **flush** on the plate top because its native bore
  is at the same `Z = +29.25 mm` as the bracket bore.
* **Front bracket / tap collar / gear band are packed flush** with
  only 1 mm of air clearance between adjacent ring faces, so gravity
  holds them against the front bracket.
* **Pinion centred on the gear band in Y** — the motor face is set
  so the pinion centre lands exactly on the gear band centre,
  transferring full torque across the gear face.
* **Motor face-mounted** on a vertical wall on the plate top: the
  NEMA-11 bolts through the wall's **+Y face**, its body extends in
  **−Y** away from that face, and its shaft + 16T pinion pokes back
  through the wall's Ø22 pilot to mesh with the auger's Ø50 gear band
  at the standard `C = 32 mm` centre distance.
* **Symmetric in X.**  Plate `X ∈ [−54.1, +54.1]` — auger centred at
  `X = 0`; the central auger gap in the +Y edge sits in the middle.
* **Component order along the auger (hinge end → motor end):**
  `hinge axis @ Y=+125` → `front bracket @ Y=+72.67` → `tap-collar
  mount @ Y=+56.67` → `NEMA-11 over the gear band @ Y=+41.67` →
  `rear bracket @ Y=−95`.
* **3-layer sandwich hinges.**  Each side of the auger gap carries
  `{inner mounting-plate lobe, middle baseplate arm, outer
  mounting-plate lobe}` sharing one long M5 pin per side.  Each
  layer takes one third of its ramp half-span (`≈ 12.7 mm` thick
  along X), so the hinges span the entire front of the plate.  The
  mounting plate's four eye lobes and the two **full-width front
  ramps** together cover the entire +Y face of the plate except for
  the central auger gap.
* **Hinge axis is 10 mm in front of the baseplate's front edge.**
  Baseplate front edge at `Y = +115`, rear edge at `Y = −75`
  (trapezoidal tabletop), hinge axis at `Y = +125`.  The
  baseplate has two **forward-and-up hinge arms** (one each side of
  the auger) that reach from `Y = +115` forward to `Y = +125`, each
  arm slotting into the centre third of its ramp half-span.
* **No powder window** in the baseplate — the dispense point sits
  10 mm forward of the baseplate's front edge, so powder falls in
  front of the baseplate directly into the cup on the scale.

**Geometry.**  The auger (PR #49, Ø25 × 250 mm with a Ø50 spur-gear
band centred at `total_h/3` from the dispense end) lies along **+Y**,
dispense end at `Y = +125`.  Two PR #47 lifted brackets bolt flange-down
flush onto the plate top at `Y = +72.67` / `Y = −95`, gripping the
auger 29.25 mm above the plate top → auger axis at `Z = +29.25 mm`.
The PR #51 tap-collar wraps the auger at `Y = +56.67`, bolted flush to
the plate top right next to the front bracket with 1 mm of air gap.

**Hinge axis = dispense-point axis.**  Four eye lobes on the plate top
(two each side, sandwich-style at one-third spacings of each ramp
half-span) and two baseplate arms (one each side, occupying the middle
third) all carry the bore at `(Y = +125, Z = +29.25)` — the auger's
dispense point.  Two long M5 pins (one per side, each running through
all three layers of its sandwich) tie the two halves together.
Because the rotation axis IS the dispense axis, the dispense point
literally **does not move** while the plate tilts 0–90° (see
`rotation_0_45_90.png` — red dot is fixed across all three tilts).

### Mounting-hole map (top view)

`installation_diagram.png` shows every hole on the mounting plate
labelled by the part it mates with.  All hole spacings match the
upstream parts' own bolt patterns:

| Part                  | Source PR | Pattern                                              | Hole size  | Centre Y (mm) |
| --------------------- | --------- | ---------------------------------------------------- | ---------- | ------------- |
| Front bracket         | #47       | 2 × M3 at X = ±24 (flush — lifted flange)            | Ø3.4 (M3)  | +72.67        |
| Tap-collar mount      | #51       | 2 × M3 at X = ±24 (flush)                            | Ø3.4 (M3)  | +56.67        |
| NEMA 11 motor mount   | #49       | 4 × M3 at 23 mm pitch + Ø22 pilot **on the vertical front face of the wall** | Ø3.4 (M3) | motor face at +31.67 |
| Rear bracket          | #47       | 2 × M3 at X = ±24 (flush — lifted flange)            | Ø3.4 (M3)  | −2            |
| Side hinge sandwich   | this PR   | 4 plate eye-lobes (Ø18 × ≈12.7 mm) at X = inner+outer thirds of each ramp half-span | Ø5.4 (M5)  | +125         |

### Rotation kinematics

`rotation_0_45_90.png` walks the assembly through 0°, 45° and 90° tilt
about the hinge axis.  At 0° the auger is horizontal; at 90° it points
straight down past the front of the baseplate into the cup.  The
hinge axis is fixed at the auger's dispense point so that point does
not move as the assembly tilts (red dot in the diagram).

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

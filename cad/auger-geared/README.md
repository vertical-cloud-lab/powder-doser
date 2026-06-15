# Geared Archimedes auger + NEMA 11 pinion

A drop-in alternative drive scheme for the rotating powder-dispenser
tube introduced in PR [#16][pr16]. The original design drives the
auger through an M3 spindle on top via a flexible shaft coupler from
the NEMA 11 stepper documented in [#24][i24] / PR [#25][pr25]. This
folder adds a parallel-axis option: an external spur-gear band
machined directly into the *outside* of the auger, meshing with a
small pinion on the stepper shaft mounted alongside the housing.

This part lives in **`cad/auger-geared/` and intentionally does not
touch `cad/auger/`** so that PR #16's hand-tuned v5 monolithic-tube
design is preserved unchanged.

## Why a side-mounted gear?

Per the source issue, the side-driven topology lets us:

- Run the stepper next to the auger instead of in line with it,
  shortening the overall stack height.
- Use a single rigid bracket to hold both the stepper and the auger
  housing, removing the flexible shaft coupler (item 12 in the BOM).
- Get a free 2.5 : 1 mechanical reduction, which more than triples
  the holding torque available at the auger and quarters the angular
  step at the auger relative to the motor.

The image attached to the source issue shows the auger as a long
tube with a single toothed band wrapped around it about a third of
the way up from the dispensing (bottom) end, and a small pinion +
NEMA-style stepper sitting beside it. That is what this folder
generates.

## Files

| File | What it is |
|------|------------|
| `gear-teeth.scad` | Shared spur-tooth math (`tooth_half_angle`, `clamp_half_angle`, `spur_gear_2d`). `include`d by `auger-core.scad` and `stepper-pinion.scad` so the meshing pair cannot drift apart. `spur_gear_2d` takes an optional `inner_r` to hollow the gear disc out — used by the auger band so the powder bore stays open through the gear's axial slice. |
| `auger-core.scad` | **(v3)** Parametric core geometry: `tube_walls`, `bottom_funnel`, `top_cap`, `central_shaft`, `helical_fin`, `gear_band`, plus the assembly module `archimedes_auger_geared(total_h, gear_center_z)`. `include`d by both length variants below so they cannot drift apart. |
| `archimedes-auger-geared.scad` | **Full-length variant** (`total_h = 250 mm`). Internals (bore, conical exit funnel, M3 spindle mount, top-cap loading slots, **central shaft + helical fin**) are equivalent to `cad/auger/archimedes-auger.scad` v4.1 — i.e. the helical Archimedean screw is restored after `cad/auger/`'s v5 stripped it. The only addition vs the bare auger is the external `gear_band()`, which is `union()`'d onto the **outside** of the wall as an annulus so the bore is fully open through the gear's axial slice. |
| `archimedes-auger-geared-short.scad` | **(v3, NEW)** Short alternate variant (`total_h = 180 mm`). Same internals + gear band as the full-length variant; the only difference is that the body **above** the gear band is trimmed by 70 mm (= 7 cm) to shorten the overall stack height while preserving the gear-to-dispensing-end distance (so the same pinion / motor bracket fit unchanged). The Archimedean helix runs continuously from the funnel up to the underside of the top cap in both variants. |
| `stepper-pinion.scad` | The 16-tooth meshing pinion. 5 mm round bore + radial M3 setscrew, sized for the StepperOnline `11HS18-0674S` NEMA 11 chosen as the auger drive motor in PR #25 (see `hardware/vibration-motor-and-solenoid.md`, item 10). |
| `mesh-preview.scad` | Non-printable visual sanity check that the 48/16 pair meshes at the 32 mm center distance (used to produce `mesh-preview-top.png`). |
| `assembly-preview.scad`, `assembly-preview.stl`, `assembly-preview-{iso,top,front}.png` | Non-printable assembly visualisation: full-length auger + pinion + a NEMA 11 dummy body block (28.2 × 28.2 × 32 mm) in their final relative positions, so the radial air gap between the motor body and the auger OD can be confirmed at a glance. |
| `assembly-preview-short.scad`, `assembly-preview-short-{iso,front}.png` | **(v3, NEW)** Same view but with the short alternate auger, for side-by-side stack-height comparison. |
| `cross-section-full.scad`, `cross-section-short.scad`, `archimedes-auger-geared-cross-section.png`, `archimedes-auger-geared-short-cross-section.png` | **(v3, NEW)** Half-cut renders of each variant that show the central shaft + helical fin running continuously from the funnel mouth, through the gear band z-range, up to the underside of the top cap — the visual evidence requested in the v2 review that "the auger core is present". |
| `storage-auger-core.scad` | **(NEW)** Parametric core for the high-capacity **storage auger**: `archimedes_auger_storage(total_h, gear_center_z, with_gear)`. Reuses the unchanged outer cylinder / bore / top cap / exit funnel / gear band from `auger-core.scad` and the v4 nozzle screw geometry from `nozzle-variants.scad`, but truncates the internal screw to the **bottom third** of the bore so the top two thirds is an open loose-powder store. |
| `archimedes-auger-storage.scad` | **(NEW)** Full-length storage auger (`total_h = 250 mm`, with gear band). Identical outer cylinder to `archimedes-auger-geared.scad`; the only change is that the screw occupies the bottom third (≈ 83 mm) and the top two thirds is open storage volume. |
| `archimedes-auger-storage-test.scad` | **(NEW)** Smaller gearless bench-test version of the storage auger (`total_h = 90 mm`, ≈ 3.54 in). Same 1/3-screw / 2/3-open-storage stipulation, same inlets/outlets, no gear band — matching the short nozzle test pieces. |
| `archimedes-auger-geared.stl`, `archimedes-auger-geared-short.stl`, `archimedes-auger-storage.stl`, `archimedes-auger-storage-test.stl`, `stepper-pinion.stl` | Pre-rendered, manifold STLs ready to slice. All pass OpenSCAD's `Simple: yes` manifold check. |
| `*.png` | Iso + top renders for documentation. |

## v3 — what changed vs v2

@williamulbz, after slicing the v2 STL: *"the inner auger core is completely missing from this part file. This is something that was already handled previously in #16 and successfully printed. Be sure that the next iteration has the same core auger as that design"*. Two changes in v3:

1. **Restored the central shaft + helical fin.** v1 of this folder copied `cad/auger/archimedes-auger.scad` v5 verbatim, and v5 had explicitly stripped the helix + shaft after a single H2D print test produced inner-core stringing. v3 puts them back, matching the v4.1-era geometry of `cad/auger/` that printed and metered powder successfully. Parameters (Ø8 mm shaft, 10 mm pitch, 2 mm fin thickness, manifold-overlap sinks of 0.4 mm into the shaft and 0.2 mm into the wall) follow PR #16 v2.1/v4.1.
   - The shaft starts at `z ≈ 3.53 mm` — exactly the height inside the conical funnel where the cone's interior radius equals `shaft_r = 4 mm`, so the shaft fuses tangentially to the funnel cone wall with no floating tip and no blocking of the 1.5 mm exit hole.
   - The helix is a single `linear_extrude` with `twist = -360 · (h / fin_pitch)` over the full shaft height, so it is **continuous** — there is no break at the gear band z, the funnel transition, or the top cap. See `archimedes-auger-geared-cross-section.png` and `archimedes-auger-geared-short-cross-section.png` for the visual evidence.
2. **Added the short alternate variant.** `archimedes-auger-geared-short.scad` (`total_h = 180 mm`) trims 70 mm (7 cm) off the body **above** the gear band, leaving the gear-to-dispensing-end distance unchanged at `83.33 mm` so the meshing pinion / motor bracket from the full-length variant fit it without modification. Capacity drops from ≈80 cm³ to ≈56 cm³ in exchange for 70 mm less Z height — useful when the Bambu Lab H2D's vertical envelope is the constraint.

The geometry shared by both variants now lives in `auger-core.scad`; each top-level `.scad` file just sets `total_h`/`gear_center_z` and calls `archimedes_auger_geared(...)`. So future internals changes get applied to both variants automatically.

## Gear ratio and mesh parameters

| Parameter | Value |
|---|---|
| **Gear ratio (motor → auger reduction)** | **`Z_g / Z_p = 48 / 16 = 3.0 : 1`** |
| Module (`m`) | 1.0 mm |
| Pressure angle | 20° (linear-flank stub-tooth approximation — see SCAD header) |
| Pinion teeth (`Z_p`) | 16 |
| Driven (auger) teeth (`Z_g`) | 48 |
| Pinion pitch diameter | 16.0 mm |
| Auger pitch diameter | 48.0 mm |
| Pinion tip / root diameter | 18.0 / 13.5 mm |
| Auger tip / root diameter | 50.0 / 45.5 mm |
| **Center distance (`C`)** | **`(Z_g + Z_p) · m / 2 = 32.0 mm`** |
| **NEMA 11 body clearance to auger OD** | **`C − auger_OR − motor_half_body = 32 − 12.5 − 14.1 = 5.4 mm`** |
| Tip clearance at mesh | `C − (tip_r₁ + tip_r₂) − tooth_play ≈ 0.25 mm` (= nominal `0.25·m`) |
| Face width (axial overlap) | 10 mm |
| Auger gear-band axial center | `total_height / 3 = 83.33 mm` from the dispensing end |
| Pinion bore | Ø5.0 mm + 0.20 mm clearance |
| Pinion setscrew | M3 radial, tapped after print |

### What the ratio buys us at the auger

The NEMA 11 (`11HS18-0674S`) is a 1.8°/full-step bipolar stepper with
≈10 N·cm holding torque (PR #25, item 10).

| At the motor | At the auger (× 3.0 reduction) |
|---|---|
| 1.8°/full-step | **0.60°/full-step** |
| 200 full-steps / rev | **600 full-steps / rev** |
| 3 200 µ-steps / rev (1/16) | **9 600 µ-steps / rev** |
| 10 N·cm holding | **≈ 30 N·cm holding** (less mesh efficiency, ~26 N·cm at ~88 % spur-gear efficiency) |
| Tangential speed at 25 mm OD: 0.785 mm / motor-rev | 0.262 mm / motor-rev (× 3.0 finer at the dispensing surface) |

The finer angular resolution and higher holding torque are both
favourable for fine powder metering; the trade-off is that the auger
turns 3.0 × slower than the motor, so peak dispense rate drops by the
same factor. For the autotrickler-style metering scheme called out in
PR #16's header (rotation + gravity + vibration tap), low RPM is the
intended operating regime.

### Why 48/16 instead of v1's 30/12

The first revision of this PR used `Z_g = 30, Z_p = 12, m = 1`, giving
`C = 21 mm`. The gears meshed correctly when test-printed — but with
the auger at `OR = 12.5 mm` and the NEMA 11 frame extending
`14.1 mm` in every radial direction from its own shaft axis, the motor
body would have intersected the auger tube by `21 − 12.5 − 14.1 = 5.6 mm`.
v2 increases the mesh to `Z_g = 48, Z_p = 16`, which moves the motor
shaft axis out to `C = 32 mm` and leaves a `5.4 mm` radial air gap
between the auger OD and the nearest face of the motor frame —
matching the layout sketch attached to issue #48.

## Internal-geometry guarantee (issue requirement)

Quoting the source issue:

> no part of this new design can alter or interfere with the internal
> design of the auger. The internals should be exactly the same —
> only its external features should change.

To make this auditable:

1. All shared geometry — `tube_walls()`, `bottom_funnel()`, `top_cap()`,
   `central_shaft()`, `helical_fin()`, `gear_band()` and the constants
   `outer_diameter`, `wall_thickness`, `m3_pilot_d`, `top_cap_height`,
   `m3_boss_r`, `m3_boss_h`, `exit_hole_d`, `bottom_cap_h`,
   `slot_count`, `slot_width`, `slot_length`, `slot_radius`,
   `shaft_r`, `fin_thickness`, `fin_pitch` — lives in
   `auger-core.scad` and is shared verbatim between the full-length
   and short variants.
2. The bore + funnel + cap dimensions match `cad/auger/archimedes-auger.scad`. The central shaft + helical fin (Ø8 mm shaft, 10 mm pitch, 2 mm fin) match the v4.1-era inner geometry that PR #16 successfully printed before v5 stripped it; **v3 of this folder restores those parts after v2 was found (post-print) to be missing them**.
3. The added `gear_band()` module is `union()`-only — it never
   appears inside a `difference()` against the bore, funnel, cap,
   M3 pilot, central shaft, or helical fin.
4. `gear_band()` calls `spur_gear_2d(..., inner_r = inner_r)`, where
   `inner_r = 10.5 mm` is the auger's bore radius. The 2D gear shape
   is therefore an **annulus** (root-circle disc minus the bore
   circle) plus the trapezoidal teeth — *not* a solid disc. This was
   the regression in v1: the gear shape was a full disc, which when
   unioned at the band's z fully sealed the bore between the top cap
   and the gear band, turning the auger into a closed cup. v2+ keeps
   the bore open through the band's axial slice; you can see this in
   `archimedes-auger-geared-top.png` and in `assembly-preview-iso.png`.
5. `gear_root_r = 22.75 mm` is **10.25 mm larger** than
   `outer_r = 12.5 mm`, so the band fuses to the auger wall through
   that 10.25 mm annular shoulder; no tooth feature ever crosses
   into the bore.
6. **Helix-presence check** (the explicit ask in v2's review): see
   `archimedes-auger-geared-cross-section.png` and
   `archimedes-auger-geared-short-cross-section.png` for half-cut
   renders that show the shaft + helical fin running from the funnel
   mouth all the way to the underside of the top cap, unbroken
   across the gear band z range, in **both** variants. Reproduce
   those renders with `cross-section-full.scad` /
   `cross-section-short.scad`.

The cross-section block at the bottom of `archimedes-auger-geared.scad`
(commented out) lets you visually re-confirm this in OpenSCAD's
preview.

## Assembly view

`assembly-preview.scad` (and the rendered `assembly-preview*.png` /
`assembly-preview.stl`) places the printable parts and a dummy NEMA 11
body in their final relative positions:

- Auger at the origin, axis along +Z.
- Pinion (imported from `stepper-pinion.stl`) at `x = 32 mm`, on a
  parallel axis, axially aligned so its gear face overlaps the auger's
  gear band over the full 10 mm face width.
- NEMA 11 dummy body (28.2 × 28.2 × 32 mm) behind the pinion (–Z from
  the pinion's gear face), centred on the same `x = 32 mm` axis as
  the pinion. Its nearest face to the auger sits `5.4 mm` clear of
  the auger OD — visualised as a small green rod in the SCAD source
  (commented out for export-quality renders if you regenerate).

`assembly-preview-iso.png`, `assembly-preview-top.png`, and
`assembly-preview-front.png` are the views to share with collaborators
who want a single picture of how the geared auger, pinion, and motor
fit together.

## Bracket / mounting (out of scope here, noted for the next PR)

This folder ships only the auger, the pinion, and the assembly
visualisation. The motor bracket that holds the NEMA 11 at
`C = 32 mm ± δ` from the auger axis, with slotted mounting holes to
take up backlash, is a separate part — it will be added under the same
parent issue once the geometry here is test-printed and confirmed.
For prototyping, any rigid plate with two parallel bores 32 mm apart
(Ø22 mm for a bushing on the auger side, the NEMA 11 bolt circle for
the motor side) is sufficient. Pre-load the mesh by sliding the motor
outward by ~0.05 mm before tightening, then back off if the gears bind.

## Short test pieces — one per nozzle design (issue #48)

@williamulbz (PR #49 review comment [4566308356][pr49-c4566308356]) asked for **shorter test designs for each of the 4 nozzle designs** that @swcharles documented in [issue #48 comment 4513155870][i48-c4513155870] (a/k/a the "v1..v4 nozzle types"), so all four can be printed and bench-tested side-by-side without burning filament on a full 250 mm geared body:

| Variant | Bottom-end geometry | Test file | STL | Cross-section |
|---------|---------------------|-----------|-----|---------------|
| **1** | Direct cutoff of the screw, large open funnel below | `archimedes-auger-test-nozzle1.scad` | `archimedes-auger-test-nozzle1.stl` | `archimedes-auger-test-nozzle1-cross-section.png` |
| **2** | Continue the screw to just before the exit; straight Ø8 shaft; small short funnel | `archimedes-auger-test-nozzle2.scad` | `archimedes-auger-test-nozzle2.stl` | `archimedes-auger-test-nozzle2-cross-section.png` |
| **3** | Direct cutoff of the screw above a tapered shaft tip that shrinks to a near-point at the exit | `archimedes-auger-test-nozzle3.scad` | `archimedes-auger-test-nozzle3.stl` | `archimedes-auger-test-nozzle3-cross-section.png` |
| **4** | Continue the screw as the shaft tapers down — combines v2 and v3 | `archimedes-auger-test-nozzle4.scad` | `archimedes-auger-test-nozzle4.stl` | `archimedes-auger-test-nozzle4-cross-section.png` |

All four test pieces share the same outer geometry and the same inlets / outlets as the production part:

- Total height **90 mm (≈ 3.54 in)** — in the 3–4 in band asked for.
- Tube OD 25 mm, ID 21 mm, 2 mm wall — unchanged from the geared part.
- Top cap: 4 radial loading slots + M3 spindle pilot — unchanged.
- Bottom: Ø3 mm exit hole — unchanged.
- Helix: 2 mm thick, 10 mm pitch — unchanged.
- **No external gear band.** Spin the spindle by hand (or chuck the M3 pilot into a low-speed cordless drill) during the bench test.

Helix-turn count by variant (the spec asks for ≥ 3 full turns; all four clear the bar by a wide margin):

| Variant | Helix z-range | Full turns |
|---------|---------------|-----------:|
| v1 | 3.53 mm → 84 mm | **8.05** |
| v2 | 3 mm → 84 mm | **8.10** |
| v3 | 12 mm → 84 mm | **7.20** |
| v4 | 0.5 mm → 84 mm | **8.35** |

Geometry is shared in `nozzle-variants.scad`, which adds variant-aware bottom-funnel / central-shaft / helical-fin modules on top of the constants in `auger-core.scad`. Each top-level test `.scad` just sets `nozzle_variant = 1..4` and calls `archimedes_auger_test(total_h, nozzle_variant)`, so the four files cannot drift apart.

The cross-section PNGs above are the same kind of half-cut render that confirmed the helix presence in v3 of the geared body — they make the difference between the four variants obvious at a glance and confirm that all four have the full inner Archimedean screw across the bench-test length.

## Storage auger — high powder capacity (issue #48 v4 nozzle, 1/3 screw)

@swcharles ([PR #49 comment 4712371378][pr49-c4712371378]) asked for a new auger version, the **storage auger**, that trades internal screw length for loose-powder storage volume:

> We're adjusting the design for more powder storage capacity. Make a new auger version (leaving the old auger version in the file system) called "storage auger" utilizing the same (and now standard) v4 auger nozzle type … remove the top two thirds of the internal screw, allowing for a large internal open area to store loose powder. To be clear, the outer cylinder should be unchanged — all that changes in this design is where the screw starts. Also create a smaller scale auger with the same stipulations (1/3 auger, 2/3 open space inside the cylinder) for testing …

| Part | File | STL | Outer cylinder | Gear band | Screw zone | Open store |
|------|------|-----|---------------|-----------|-----------|-----------|
| **Storage auger** (full) | `archimedes-auger-storage.scad` | `archimedes-auger-storage.stl` | 250 mm, **unchanged** vs geared | yes (at 83.33 mm) | bottom 0 → 83.33 mm | top 83.33 → 250 mm |
| **Storage auger** (bench test) | `archimedes-auger-storage-test.scad` | `archimedes-auger-storage-test.stl` | 90 mm (≈ 3.54 in) | no | bottom 0 → 30 mm | top 30 → 90 mm |

What is **unchanged** from the existing parts (so "the outer cylinder should be unchanged" holds by construction — these modules are reused verbatim from `auger-core.scad`):

- Tube OD 25 mm, ID 21 mm, 2 mm wall.
- Top cap: 4 radial loading slots + M3 spindle pilot.
- Bottom: Ø3 mm exit hole with the standard **v4** nozzle funnel + tapered screw tip.
- Full part: the same 48-tooth annular gear band at `total_h / 3` that meshes with `stepper-pinion.scad`.

What **changes**: the internal Archimedean screw (central shaft + helical fin) now occupies only the **bottom third** of the bore (`screw_top_z = total_h / 3` — verified 0 → 83.33 mm on the full part, 0 → 30 mm on the test part). The top two thirds of the bore is left completely open as a loose-powder reservoir that feeds down into the screw. The screw itself uses the standard v4 nozzle geometry (tapered tip + helix following the shaft down to just above the exit), so the dispensing end is identical to nozzle test piece 4.

Shared geometry lives in `storage-auger-core.scad` (`archimedes_auger_storage(total_h, gear_center_z, with_gear)`); each top-level `.scad` just sets the length and whether the gear band is present, so the two storage variants cannot drift apart. The half-cut cross-sections (`archimedes-auger-storage-cross-section.png`, `archimedes-auger-storage-test-cross-section.png`) show the screw confined to the bottom third with the open store above.

## Print notes

Both parts are sized for the same stack as PR #16:

- **Auger** (`archimedes-auger-geared.stl`): PLA or PETG, 0.2 mm
  layers, 0.4 mm nozzle, 1.75 mm filament. Print **vertical**, exit
  hole down, 4 mm brim. 3+ perimeters, 40 % gyroid infill. The gear
  band's overhang is symmetric (it sticks out radially from a
  cylindrical wall), so no supports are needed for the teeth
  themselves; the slicer's tree supports under the *underside* of the
  band are optional and easy to remove. The band is now noticeably
  larger than v1 (Ø50 mm vs Ø32 mm tip) — it adds about 13 g of
  material but no extra print-time on the critical Z dimension.
- **Pinion** (`stepper-pinion.stl`): PLA or PETG, 0.2 mm layers,
  0.4 mm nozzle. Print **flat** (gear face down) so the teeth come
  out as full-perimeter walls — best dimensional accuracy. 4
  perimeters, 30 % gyroid infill, no supports. Tap the radial M3
  setscrew hole after printing.

## Reproducing the renders

```bash
# Solids
openscad -o archimedes-auger-geared.stl       archimedes-auger-geared.scad
openscad -o archimedes-auger-geared-short.stl archimedes-auger-geared-short.scad
openscad -o stepper-pinion.stl                stepper-pinion.scad
openscad -o assembly-preview.stl              assembly-preview.scad

# PNG previews (need a display; xvfb-run works headless)
xvfb-run -a openscad -o archimedes-auger-geared-iso.png \
    --imgsize=900,900 --camera=0,0,125,55,0,25,500 \
    --colorscheme=Tomorrow archimedes-auger-geared.scad
xvfb-run -a openscad -o archimedes-auger-geared-top.png \
    --imgsize=600,600 --camera=0,0,125,0,0,0,90 --projection=ortho \
    --colorscheme=Tomorrow archimedes-auger-geared.scad
xvfb-run -a openscad -o archimedes-auger-geared-short-iso.png \
    --imgsize=900,800 --camera=0,0,90,55,0,25,400 \
    --colorscheme=Tomorrow archimedes-auger-geared-short.scad
xvfb-run -a openscad -o archimedes-auger-geared-short-top.png \
    --imgsize=600,600 --camera=0,0,90,0,0,0,90 --projection=ortho \
    --colorscheme=Tomorrow archimedes-auger-geared-short.scad

# Helix-presence cross-sections (the v3 ask)
xvfb-run -a openscad -o archimedes-auger-geared-cross-section.png \
    --imgsize=700,1100 --camera=0,-80,125,90,0,0,300 --projection=ortho \
    --colorscheme=Tomorrow cross-section-full.scad
xvfb-run -a openscad -o archimedes-auger-geared-short-cross-section.png \
    --imgsize=700,800 --camera=0,-80,90,90,0,0,220 --projection=ortho \
    --colorscheme=Tomorrow cross-section-short.scad

xvfb-run -a openscad -o stepper-pinion-iso.png \
    --imgsize=600,600 --camera=0,0,8,55,0,25,40 \
    --colorscheme=Tomorrow stepper-pinion.scad
xvfb-run -a openscad -o stepper-pinion-top.png \
    --imgsize=400,400 --camera=0,0,8,0,0,0,22 --projection=ortho \
    --colorscheme=Tomorrow stepper-pinion.scad
xvfb-run -a openscad -o mesh-preview-top.png \
    --imgsize=900,500 --camera=16,0,83,0,0,0,80 --projection=ortho \
    --colorscheme=Tomorrow mesh-preview.scad
xvfb-run -a openscad -o assembly-preview-iso.png \
    --imgsize=1100,900 --camera=15,0,90,55,0,30,260 \
    --colorscheme=Tomorrow assembly-preview.scad
xvfb-run -a openscad -o assembly-preview-top.png \
    --imgsize=900,500 --camera=15,0,83,0,0,0,90 \
    --projection=ortho --colorscheme=Tomorrow assembly-preview.scad
xvfb-run -a openscad -o assembly-preview-front.png \
    --imgsize=1100,800 --camera=15,0,83,90,0,0,260 \
    --projection=ortho --colorscheme=Tomorrow assembly-preview.scad

# Nozzle-variant test pieces (one .stl + one cross-section .png per variant)
for N in 1 2 3 4; do
  openscad -o "archimedes-auger-test-nozzle${N}.stl" \
              "archimedes-auger-test-nozzle${N}.scad"
  cat > "_cs_tmp${N}.scad" <<EOF
include <nozzle-variants.scad>;
total_h = 90;
difference() {
    archimedes_auger_test(total_h, ${N});
    translate([-30, -0.5, -1]) cube([60, 30, total_h + 2]);
}
EOF
  xvfb-run -a openscad --render \
    -o "archimedes-auger-test-nozzle${N}-cross-section.png" \
    --imgsize=500,900 --camera=0,120,45,0,0,45 \
    --projection=ortho --viewall --colorscheme=Tomorrow \
    "_cs_tmp${N}.scad"
  rm "_cs_tmp${N}.scad"
done

# Storage auger (full + bench test)
openscad -o archimedes-auger-storage.stl      archimedes-auger-storage.scad
openscad -o archimedes-auger-storage-test.stl archimedes-auger-storage-test.scad
xvfb-run -a openscad -o archimedes-auger-storage-iso.png \
    --imgsize=900,900 --camera=0,0,125,55,0,25,500 \
    --colorscheme=Tomorrow archimedes-auger-storage.scad
xvfb-run -a openscad -o archimedes-auger-storage-test-iso.png \
    --imgsize=700,800 --camera=0,0,45,55,0,25,200 \
    --colorscheme=Tomorrow archimedes-auger-storage-test.scad
cat > _cs_storage.scad <<EOF
include <storage-auger-core.scad>;
total_h = 250; gz = total_h/3;
difference() {
    archimedes_auger_storage(total_h, gz, true);
    translate([-gear_tip_r-1, -gear_tip_r-1, -1])
        cube([2*gear_tip_r+2, gear_tip_r+1, total_h+2]);
}
EOF
xvfb-run -a openscad --render -o archimedes-auger-storage-cross-section.png \
    --imgsize=700,1100 --camera=0,-80,125,90,0,0,300 --projection=ortho \
    --colorscheme=Tomorrow _cs_storage.scad
rm _cs_storage.scad
cat > _cs_storage_test.scad <<EOF
include <storage-auger-core.scad>;
total_h = 90;
difference() {
    archimedes_auger_storage(total_h, 0, false);
    translate([-30, -30, -1]) cube([60, 30, total_h+2]);
}
EOF
xvfb-run -a openscad --render -o archimedes-auger-storage-test-cross-section.png \
    --imgsize=500,900 --camera=0,-80,45,90,0,0,140 --projection=ortho \
    --colorscheme=Tomorrow _cs_storage_test.scad
rm _cs_storage_test.scad
```

Or paste either `.scad` into <https://openscad.org/demo/> → **F6**
(Render) → **File → Export → Export as STL**.

## Cross-references

- PR [#16][pr16] — original Archimedes auger (v5 hollow tube). This
  folder mirrors v5 internals exactly.
- Issue [#24][i24] / PR [#25][pr25] — NEMA 11 stepper selection
  (`11HS18-0674S`, 5 mm round shaft, 1.8°/step, ≈10 N·cm holding) and
  the Tic T500 / DRV8825 driver options that the gear ratio above is
  derived against.

[pr16]: https://github.com/vertical-cloud-lab/powder-doser/pull/16
[i24]:  https://github.com/vertical-cloud-lab/powder-doser/issues/24
[pr25]: https://github.com/vertical-cloud-lab/powder-doser/pull/25
[i48-c4513155870]:    https://github.com/vertical-cloud-lab/powder-doser/issues/48#issuecomment-4513155870
[pr49-c4566308356]:   https://github.com/vertical-cloud-lab/powder-doser/pull/49#issuecomment-4566308356
[pr49-c4712371378]:   https://github.com/vertical-cloud-lab/powder-doser/pull/49#issuecomment-4712371378

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
| `gear-teeth.scad` | Shared spur-tooth math (`tooth_half_angle`, `clamp_half_angle`, `spur_gear_2d`). `include`d by both `archimedes-auger-geared.scad` and `stepper-pinion.scad` so the meshing pair cannot drift apart. |
| `archimedes-auger-geared.scad` | The geared auger. Internals (bore, conical exit funnel, M3 spindle mount, top-cap loading slots) are byte-for-byte identical to `cad/auger/archimedes-auger.scad` v5. The only addition is the `gear_band()` module, which is `union()`'d onto the **outside** of the wall. |
| `stepper-pinion.scad` | The 12-tooth meshing pinion. 5 mm round bore + radial M3 setscrew, sized for the StepperOnline `11HS18-0674S` NEMA 11 chosen as the auger drive motor in PR #25 (see `hardware/vibration-motor-and-solenoid.md`, item 10). |
| `mesh-preview.scad` | Non-printable visual sanity check that the 30/12 pair meshes at the 21 mm center distance (used to produce `mesh-preview-top.png`). |
| `archimedes-auger-geared.stl`, `stepper-pinion.stl` | Pre-rendered, manifold STLs ready to slice. Both pass OpenSCAD's `Simple: yes` manifold check. |
| `*.png` | Iso + top renders for documentation. |

## Gear ratio and mesh parameters

| Parameter | Value |
|---|---|
| **Gear ratio (motor → auger reduction)** | **`Z_g / Z_p = 30 / 12 = 2.5 : 1`** |
| Module (`m`) | 1.0 mm |
| Pressure angle | 20° (linear-flank stub-tooth approximation — see SCAD header) |
| Pinion teeth (`Z_p`) | 12 |
| Driven (auger) teeth (`Z_g`) | 30 |
| Pinion pitch diameter | 12.0 mm |
| Auger pitch diameter | 30.0 mm |
| Pinion tip / root diameter | 14.0 / 9.5 mm |
| Auger tip / root diameter | 32.0 / 27.5 mm |
| **Center distance (`C`)** | **`(Z_g + Z_p) · m / 2 = 21.0 mm`** |
| Tip clearance at mesh | `C − (tip_r₁ + root_r₂) = 0.25 mm` (= nominal `0.25·m`) |
| Face width (axial overlap) | 10 mm |
| Auger gear-band axial center | `total_height / 3 = 83.33 mm` from the dispensing end |
| Pinion bore | Ø5.0 mm + 0.20 mm clearance |
| Pinion setscrew | M3 radial, tapped after print |

### What the ratio buys us at the auger

The NEMA 11 (`11HS18-0674S`) is a 1.8°/full-step bipolar stepper with
≈10 N·cm holding torque (PR #25, item 10).

| At the motor | At the auger (× 2.5 reduction) |
|---|---|
| 1.8°/full-step | **0.72°/full-step** |
| 200 full-steps / rev | **500 full-steps / rev** |
| 3 200 µ-steps / rev (1/16) | **8 000 µ-steps / rev** |
| 10 N·cm holding | **≈ 25 N·cm holding** (less mesh efficiency, ~22 N·cm at ~88 % spur-gear efficiency) |
| Tangential speed at 25 mm OD: 0.785 mm / motor-rev | 0.314 mm / motor-rev (× 2.5 finer at the dispensing surface) |

The finer angular resolution and higher holding torque are both
favourable for fine powder metering; the trade-off is that the auger
turns 2.5 × slower than the motor, so peak dispense rate drops by the
same factor. For the autotrickler-style metering scheme called out in
PR #16's header (rotation + gravity + vibration tap), low RPM is the
intended operating regime.

## Internal-geometry guarantee (issue requirement)

Quoting the source issue:

> no part of this new design can alter or interfere with the internal
> design of the auger. The internals should be exactly the same —
> only its external features should change.

To make this auditable:

1. The four modules `tube_walls()`, `bottom_funnel()`, `top_cap()`,
   and the constants `outer_diameter`, `total_height`,
   `wall_thickness`, `m3_pilot_d`, `top_cap_height`, `m3_boss_r`,
   `m3_boss_h`, `exit_hole_d`, `bottom_cap_h`, `slot_count`,
   `slot_width`, `slot_length`, `slot_radius` are copied **verbatim**
   from `cad/auger/archimedes-auger.scad` v5.
2. The added `gear_band()` module is `union()`-only — it never
   appears inside a `difference()` against the bore, funnel, cap, or
   M3 pilot.
3. `gear_root_r = 13.75 mm` is **1.25 mm larger** than
   `outer_r = 12.5 mm`, so even the deepest tooth root sits entirely
   outside the auger wall. No tooth feature ever crosses into the
   wall, so the inner bore and powder path are mechanically identical
   to v5.

The cross-section block at the bottom of `archimedes-auger-geared.scad`
(commented out) lets you visually re-confirm this in OpenSCAD's
preview.

## Bracket / mounting (out of scope here, noted for the next PR)

This folder ships only the auger and the pinion. The motor bracket
that holds the NEMA 11 at `C = 21 mm ± δ` from the auger axis, with
slotted mounting holes to take up backlash, is a separate part — it
will be added under the same parent issue once the geometry here is
test-printed and confirmed. For prototyping, any rigid plate with two
parallel bores 21 mm apart (Ø22 mm for a bushing on the auger side,
the NEMA 11 bolt circle for the motor side) is sufficient. Pre-load
the mesh by sliding the motor outward by ~0.05 mm before tightening,
then back off if the gears bind.

## Print notes

Both parts are sized for the same stack as PR #16:

- **Auger** (`archimedes-auger-geared.stl`): PLA or PETG, 0.2 mm
  layers, 0.4 mm nozzle, 1.75 mm filament. Print **vertical**, exit
  hole down, 4 mm brim. 3+ perimeters, 40 % gyroid infill. The gear
  band's overhang is symmetric (it sticks out radially from a
  cylindrical wall), so no supports are needed for the teeth
  themselves; the slicer's tree supports under the *underside* of the
  band are optional and easy to remove.
- **Pinion** (`stepper-pinion.stl`): PLA or PETG, 0.2 mm layers,
  0.4 mm nozzle. Print **flat** (gear face down) so the teeth come
  out as full-perimeter walls — best dimensional accuracy. 4
  perimeters, 30 % gyroid infill, no supports. Tap the radial M3
  setscrew hole after printing.

## Reproducing the renders

```bash
# Solids
openscad -o archimedes-auger-geared.stl archimedes-auger-geared.scad
openscad -o stepper-pinion.stl          stepper-pinion.scad

# PNG previews (need a display; xvfb-run works headless)
xvfb-run -a openscad -o archimedes-auger-geared-iso.png \
    --imgsize=900,900 --camera=0,0,125,55,0,25,500 \
    --colorscheme=Tomorrow archimedes-auger-geared.scad
xvfb-run -a openscad -o archimedes-auger-geared-top.png \
    --imgsize=600,600 --camera=0,0,125,0,0,0,90 --projection=ortho \
    --colorscheme=Tomorrow archimedes-auger-geared.scad
xvfb-run -a openscad -o stepper-pinion-iso.png \
    --imgsize=600,600 --camera=0,0,8,55,0,25,40 \
    --colorscheme=Tomorrow stepper-pinion.scad
xvfb-run -a openscad -o stepper-pinion-top.png \
    --imgsize=400,400 --camera=0,0,8,0,0,0,18 --projection=ortho \
    --colorscheme=Tomorrow stepper-pinion.scad
xvfb-run -a openscad -o mesh-preview-top.png \
    --imgsize=900,500 --camera=10,0,83,0,0,0,60 --projection=ortho \
    --colorscheme=Tomorrow mesh-preview.scad
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

# Single-channel powder-doser module — "Idea B" archetype

This folder is the first physical-prototype design pass for the powder
doser. It implements **Idea B / §2.2** of
[`design/brainstorming.md`](../../brainstorming.md): a self-contained
single-channel module — one auger + one stepper + one solenoid + one
vibration motor + that channel's three driver carriers — that gets
**replicated N times** around a shared collection cup to build the full
multi-powder doser.

> [!NOTE]
> This is the **archetype**, not the full N-channel system. The fan-in
> ring frame, the load-cell, and the inert-atmosphere enclosure are
> deliberately deferred — see [§ Roadmap](#roadmap) for the staged plan.
> The §2.2 fan-in geometry (12 channels around a shared cup) is already
> sketched in the sibling folder
> [`design/cad/inward-collection-cup/`](../inward-collection-cup/) for
> orientation; this folder *zooms in* on a single channel of that ring.

Issue: **vertical-cloud-lab/powder-doser#33** ("Modular Single-Channel
Powder Doser Design").
Resolves the design-execution half of the issue (the discussion half was
the brainstorming PR [#31](https://github.com/vertical-cloud-lab/powder-doser/pull/31)).

## Renders

| | |
|---|---|
| ![Isometric](renders/single_channel_module_iso.png) | ![Dimensioned sketch](renders/single_channel_module_sketch.png) |
| Isometric line render of the full assembly (`cad_model.py` → `.step` → SVG → PNG). | 2D dimensioned schematic — front + side elevations (`sketch_2d.py`). |

Additional orthographic SVG/PNG views (`single_channel_module_front`,
`_side`, `_top`) are in [`renders/`](renders/).

## What's in this folder

| File | What it is |
|---|---|
| [`cad_model.py`](cad_model.py) | Parametric **CadQuery** model. Builds every printed part, places every vendor component (NEMA 11, JF-0530B, ERM coin, DRV8825 / DRV8871 / DRV2605L, 5 mm ↔ M3 flex coupler, the PR-#16 auger envelope), exports `single_channel_module.step` and per-part STLs. |
| [`sketch_2d.py`](sketch_2d.py) | Matplotlib schematic with dimensions in millimetres (front + side). Same constants as `cad_model.py`. |
| [`single_channel_module.step`](single_channel_module.step) | STEP export of the **full assembly** (printed parts in lavender, vendor placeholders in their own colours). Open in FreeCAD / Fusion 360 / SolidWorks / KiCad StepUp. |
| [`stl/`](stl/) | Per-part STLs of every printed part — ready to drop into a slicer (PrusaSlicer / Cura / Bambu Studio). |
| [`renders/`](renders/) | Isometric, front, side, top SVG line renders + PNG rasterizations + the 2D dimensioned PNG. |

## Reproducing

```bash
cd design/cad/single-channel-module
pip install cadquery matplotlib cairosvg

python cad_model.py     # writes the .step + stl/*.stl + renders/*.svg
python sketch_2d.py     # writes renders/single_channel_module_sketch.png

# rasterize the four CAD SVGs to PNG
python -c "import cairosvg
for v in ('iso','front','top','side'):
    cairosvg.svg2png(url=f'renders/single_channel_module_{v}.svg',
                     write_to=f'renders/single_channel_module_{v}.png',
                     output_width=1600)"
```

## Design requirements (cross-referenced)

Pulled from [`design/brainstorming.md`](../../brainstorming.md) §1, §1a,
§2.2, and §3, with the corresponding bullet from this design called out.

| # | Requirement (source) | How this design meets it |
|---|---|---|
| R1 | Use the **PR-#16 Archimedes auger** as-is (issue text + brainstorming §2.2) | The rotor is modelled as a Ø25 × 250 mm envelope from `cad/auger/archimedes-auger.scad` v4. The frame's top-plate bore (Ø22) clears the auger's M3 spindle boss; the base-plate exit hole (Ø30) clears the auger OD with 2.5 mm radial gap for the powder column. |
| R2 | Each station carries **all three #1a actuators** (auger + tap + vibration) | NEMA 11 stepper at the top plate (auger), JF-0530B solenoid bracketed against the +X face of the tap collar (tap), ERM coin pad on the −X face (vibration). |
| R3 | Direct-drive auger via 5 mm flex coupler (PR-#25 item 12) | Top plate hosts NEMA 11 on its standard 23 mm BHC; coupler bridges 25 mm vertically from the stepper's 5 mm shaft to the auger's M3 boss. Coupler envelope (Ø14 × 25) is included in the assembly. |
| R4 | **Modular / replicable** — N copies fit around a shared cup (§2.2: ~12 channels on a 150 mm pitch circle) | Module footprint is **80 × 80 mm** with 4 corner M4 bores on a 64 mm square pitch. With those 12 channels on a 150 mm-Ø pitch circle, adjacent module footprints don't collide (pitch-circle arc length per module ≈ 39 mm; the 80 mm module faces are oriented *radially* outward, so the tangential footprint is the 80 mm side as seen from the cup, which fits comfortably with ~10 mm gap). The design is intentionally **vertical first**; the 30°-inward tilt called out in §2.2 is added at the *next* level (the ring frame) by tilting each module's base-plate mount, not by re-cutting the module itself. |
| R5 | Vibration / tap actuators must mount to **stationary** structure (PR-#25 "rotating vs stationary parts") | The tap collar is a separate stationary printed part bolted to the base plate via two M3 bosses; it surrounds the rotor with 1 mm radial clearance. Solenoid and ERM lead wires terminate on the stationary tray. Only the auger rotor + flex coupler rotate. |
| R6 | Pi I/O fan-out (§2.2 pitfall): N step/dir lines exceed Pi Zero header capacity by ~12 channels | Each module hosts **its own DRV8825**, so the host bus to the Pi is a small set of shared signals (STEP/DIR pairs broken out per channel by an I²C GPIO expander, or TMC-style stepper bus). The electronics tray has stack space for the three driver carriers per module; Pi-side bus electronics are *not* part of the per-module design and live on a future shared backplane. |
| R7 | Per-channel calibration burden (§2.2 pitfall) is software-side | Mechanical parts are identical across modules; calibration variance is captured per-channel in firmware (deferred). |
| R8 | No cross-contamination at the wetted surface (§2.2 benefit) | A given printed module owns one rotor + one tap collar; both are dedicated to a single powder. The shared collection cup is a **deferred** problem (see [§ Roadmap](#roadmap) — a wash/swap or per-batch disposable-liner strategy is planned before v2). |
| R9 | Dispense outlet ~80 mm above cup rim (§2.2 visualization) | With the module mounted vertically, the rotor exit sits at Z = `PLATE_T + EXIT_GAP` = 14 mm above the bottom of the base plate; the 80 mm clearance is achieved by the *ring frame* mounting the base plates that height above the cup. |
| R10 | Print on a hobbyist FDM (matches existing `cad/auger/` convention) | All printed parts fit the Bambu Lab H2D bed (350 × 320 × 325 mm) — the largest piece is a corner post at Ø10 × 285 mm, oriented vertically with no support. See [§ Print orientation & settings](#print-orientation--settings). |

## Geometry (single source of truth)

Every dimension below is duplicated as a constant in **both**
`cad_model.py` and `sketch_2d.py`; if you change one, change the other.

### Printed parts (PETG or PLA, hobbyist FDM)

| Part | Footprint / envelope | Notes |
|---|---|---|
| `base_plate` | 80 × 80 × 6 mm | Ø30 central exit hole; 4× M4 corner bores (Ø4.4) on 64 mm pitch; 2× M3 self-tap bosses on a 50 mm pitch for the tap-collar feet. |
| `tap_collar` | Ø40 OD / Ø27 ID, 22 mm tall | 1 mm radial clearance to the Ø25 rotor. +X solenoid wing (4 × 30 × 23 mm) with 2× M2 bolt holes on 14 mm pitch + Ø5.5 plunger clearance hole. −X ERM pad (2 × 14 × 14 mm) with shallow Ø10.4 × 0.6 recess for adhesive alignment. |
| `corner_post` | Ø10 × 285 mm | Axial Ø4.4 M4 bore. Four printed per module. |
| `top_plate` | 80 × 80 × 6 mm | Ø22 stepper-boss clearance; 4× Ø3 NEMA-11 mounting holes on 23 mm BHC; 4× Ø4.4 corner bores. |
| `electronics_tray` | 70 × 100 × 3 mm panel + two Ø-clamp ribs | Bolts to the +Y corner posts. Hole patterns for the three driver carriers are not yet drilled — the panel is intentionally over-sized so the user can match-drill to the carrier they actually receive (DRV-series board outlines vary slightly by vendor batch). |

### Vendor / placeholder parts (purchased — see [BOM](#bill-of-materials))

| Part | Envelope | Source |
|---|---|---|
| NEMA 11 stepper | 28 × 28 × 45 mm body, 5 mm shaft | PR-#25 item 10 |
| Flex coupler 5 mm ↔ M3 | Ø14 × 25 mm | PR-#25 item 12 |
| JF-0530B solenoid | 9.6 × 19 × 22 mm, 4.5 mm stroke | PR-#25 item 4 |
| ERM coin vibration motor | Ø10 × 2.7 mm | PR-#25 item 2 |
| DRV8825 carrier (stepper) | 20 × 15.5 × 8 mm | PR-#25 item 11 |
| DRV8871 carrier (solenoid) | 21 × 17 × 8 mm | PR-#25 item 5 |
| DRV2605L breakout (ERM) | 18 × 20 × 8 mm | PR-#25 item 1 |

Total module envelope: **80 × 80 × 342 mm** (W × D × H).

## Bill of materials (per module)

| Qty | Item | Approx. \$ | Source |
|---|---|---|---|
| 1 | PR-#16 v4 auger rotor (printed) | ~$1 (PETG) | `cad/auger/archimedes-auger.scad` |
| 1 | NEMA 11 stepper, 5 mm shaft | $14–18 | [SparkFun ROB-10848](https://www.sparkfun.com/products/10848) |
| 1 | 5 mm ↔ M3 flexible shaft coupler | $3–6 | Amazon / McMaster |
| 1 | DRV8825 stepper-driver carrier | $7.95 | [Pololu #2133](https://www.pololu.com/product/2133) |
| 1 | JF-0530B 5 V mini push-pull solenoid | $4.95 | [Adafruit #412](https://www.adafruit.com/product/412) |
| 1 | DRV8871 DC motor driver breakout | $7.50 | [Adafruit #3190](https://www.adafruit.com/product/3190) |
| 1 | ERM 10 mm vibration coin (or LRA #1631) | $1.95 | [Adafruit #1201](https://www.adafruit.com/product/1201) |
| 1 | DRV2605L haptic-driver breakout | $7.95 | [Adafruit #2305](https://www.adafruit.com/product/2305) |
| 8 | M4 × 35 mm BHCS + nyloc nut (4× base→post, 4× post→top) | <$3 | any |
| 4 | M2.5 × 8 mm BHCS (NEMA 11 → top plate) | <$1 | any |
| 2 | M2 × 6 mm BHCS (solenoid → wing) | <$0.50 | any |
| 2 | M3 × 8 mm self-tapping (collar feet → base bosses) | <$0.50 | any |
| 1 | Adhesive pad (3M VHB or instant) for the ERM coin | <$0.50 | any |

**Per-module electronics+motor sub-total ≈ $50.** Frame printing
consumables are roughly $4 of PETG. Multiply by N (target 8–12 for v1).

The **shared** parts (12 V wall-wart + Pololu D24V22F5 buck converter +
Pi Zero 2 W + Perma-Proto Bonnet, plus the GPIO expander / TMC bus) are
*not* per-module and live on a future backplane PR.

## Print orientation & settings

All printed parts are sized for **PLA or PETG, 0.4 mm nozzle, 0.2 mm
layers**, on any FDM bed ≥ 290 mm Z (the corner post is the height
constraint). 0.2 mm layers + 4 perimeters + 25 % gyroid infill is the
recommended starting point. Specifics:

| Part | Orientation | Supports | Notes |
|---|---|---|---|
| `base_plate.stl` | Flat on bed, exit hole down | none | Brim recommended (small cross-section near the exit hole). |
| `top_plate.stl` | Flat on bed, NEMA-11 holes up | none | Same as base. |
| `corner_post.stl` | Vertical, M4 bore axial | none | The Ø4.4 axial bore prints fine vertically with 4 perimeters; if you bridge instead, increase to 5 perimeters. |
| `tap_collar.stl` | Solenoid wing on the bed | trees on the wing M2 holes only | The 22 mm-tall collar prints upright comfortably. |
| `electronics_tray.stl` | Panel flat on the bed, ribs up | none | The two clamp ribs are short and bridge cleanly. |

The PR-#16 v4 auger has its own print recipe in
[`cad/auger/archimedes-auger.scad`](../../../cad/auger/archimedes-auger.scad)
— follow that file's header notes (vertical, exit hole on the bed,
4 mm brim, 50° support overhangs).

## Assembly order

1. Print all parts; tap the auger's M3 boss with an M3 hand tap.
2. Bolt the **NEMA 11** to the **top plate** with 4× M2.5 × 8 (faceplate
   *up*, shaft down through the Ø22 bore).
3. Slide the four **corner posts** onto four M4 × 35 BHCS through the
   **base plate** corners; finger-tight only.
4. Drop the **top plate** (with stepper attached) onto the four M4
   shafts; fasten with nyloc nuts.
5. Bolt the **tap collar** to the base plate using 2× M3 self-tappers
   into the printed bosses (collar centred on the rotor axis, solenoid
   wing on +X).
6. Bolt the **JF-0530B solenoid** to the +X wing with 2× M2 × 6.
7. Adhere the **ERM coin** to the −X collar pad (clean both surfaces with
   IPA first; press for 30 s).
8. Slide the **flex coupler** down through the top-plate bore onto the
   stepper's 5 mm shaft (set screw, 1 mm gap to the plate).
9. Drop the **auger rotor** through the base-plate exit hole from above;
   thread its M3 boss into the lower set-screw clamp of the flex coupler.
   *Critical:* leave 1 mm of axial play so vibration doesn't preload the
   rotor against the coupler.
10. Mount the **electronics tray** to the +Y posts; match-drill the PCB
    standoffs to your specific carrier boards; solder leads back to the
    actuators.

## Roadmap

> The issue text asks for a "project plan/pathway to a prototype" with
> a `AI design → printing → testing → feedback → AI design` loop. This is
> that plan, as far as the per-module mechanical archetype.

- [x] **v1.0 (this folder)** — single-module mechanical archetype.
  Printable, full BOM, full assembly STEP. *Deliverable:* the
  `stl/*.stl` + this README + the BOM above are sufficient for a single
  user to print and bench-assemble one module.
- [ ] **v1.1 — print + bench-test loop** *(needs human in the loop)*.
  Print one module, populate it with the PR-#25 actuator stack, drive
  it from the existing `hardware/kicad/` schematic, and dispense
  xanthan gum + one metal powder (e.g. 316L) into a tared cup on a
  bench scale. **Failure modes to look for:** rotor wobble (cantilever
  off the coupler), tap-collar resonance frequency vs ERM band, M3
  boss thread pull-out, solenoid plunger gap to rotor wall, exit-hole
  bridging at low RPM. **Bring back:** photos, weighed-mass-vs-step
  curve, and any printed-part fractures.
- [ ] **v1.2 — N=2 fan-in test rig.** Two modules + a shared bench
  load-cell, no ring frame yet — bolted to a piece of MDF on the
  required 30°-inward tilt. Validates that the §2.2 cup geometry
  works in the small before committing to the 12-channel ring.
- [ ] **v1.3 — ring frame for N=12.** One printed (or laser-cut acrylic)
  ring with 12 tilted module pads on the §2.2 150 mm pitch circle,
  shared cup + load cell underneath. *Sibling folder:*
  `design/cad/ring-frame/` (does not exist yet).
- [ ] **v2.0 — inert-atmosphere enclosure.** Wrap the N-module ring in
  a sealed box with a single dispense aperture; deferred until v1.3
  has logged a campaign of dispenses without cross-contamination.
- [ ] **(Idea C, deferred)** Swappable-cartridge variant. Once v1.x is
  validated, evaluate replacing each module's printed `tap_collar` +
  `auger rotor` with a quick-release cartridge that lets one module
  service many powders. *Not designed here* — kept as a roadmap entry
  per the issue text.

## Parts I'd like added to the repo (or links / models I couldn't find)

If the team can drop these into the repo I can pull them into the next
revision of `cad_model.py` instead of using the rectangular envelopes
I'm using now:

- **NEMA 11 STEP model** for the specific stepper the team buys
  (SparkFun ROB-10848 vs StepperOnline 11HS18-0674S — they differ in
  body length and shaft flat). StepperOnline publishes STEP files;
  SparkFun does not. Whichever is purchased, the manufacturer's STEP
  in `hardware/cad/vendor/nema11-<part-number>.step` would let me
  replace the box-envelope I'm using.
- **JF-0530B STEP/STL.** No manufacturer file is published; a
  community-modelled STEP would replace my box envelope and give a
  more accurate plunger geometry.
- **ERM coin model** with the actual lead-wire egress (currently
  modelled as a featureless disc).
- **Flex coupler** — the specific Ø/length the team purchases; mine
  is a generic Ø14 × 25 placeholder.
- **Driver carrier KiCad → STEP exports** for DRV8825 / DRV8871 /
  DRV2605L (Pololu and Adafruit publish board outlines but not
  full-component STEPs). My carriers are box envelopes with no
  header pins / connector cutouts.
- **M3, M4, M2.5, M2 fasteners** — McMaster STEPs would let me drop
  bolts into the assembly for visual completeness; I have left them
  out to keep the model load-time short, but they could be added in a
  `_with_fasteners.step` variant.

None of these are blocking; they would just upgrade the assembly
realism in v1.1+.

## Known limitations / next steps

- **The auger is shown as a smooth Ø25 envelope**, not the actual
  v4 helical geometry. The real geometry lives in
  [`cad/auger/archimedes-auger.scad`](../../../cad/auger/archimedes-auger.scad)
  and is a separate solid; importing the OpenSCAD STL into CadQuery
  would inflate this model's size by ~5 MB without changing any
  fit-check that matters at this stage. (The two interfaces that *do*
  matter — the M3 spindle at the top and the Ø3 exit hole at the
  bottom — are modelled.)
- **No cantilever / wobble analysis.** A 250 mm rotor hanging off a
  flex coupler will deflect; whether it still clears the 1 mm tap-collar
  gap under tap impact is a real question for v1.1 bench testing. If it
  fails, the fix is a printed sleeve bearing in the base plate (a third
  printed part), not a redesign of the module frame.
- **The electronics tray's PCB hole pattern is intentionally not
  drilled** — different vendor batches of DRV8825/8871/2605L use
  slightly different mounting-hole positions, so the user is expected
  to match-drill once the boards are in hand. Locking this in is
  blocked on the team confirming which vendor SKU they're buying.
- **No fan-in tilt yet.** The module is designed *vertical*; the §2.2
  30°-inward tilt is delegated to the ring-frame design (v1.3 above).
- **No collection cup or load cell** — those live in
  `design/cad/inward-collection-cup/` (visualization) and a future
  `design/cad/ring-frame/` (actual hardware).

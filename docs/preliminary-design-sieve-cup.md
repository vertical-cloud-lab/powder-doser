# Preliminary design — top-ranked alternative-dosing system

> Tracks issue [#12]; complements the cam-ramp scoop in
> [#2] and the bimodal compliant trough in [#5]. Implements the
> headline recommendation from
> [`docs/alternative-dosing/brainstorm.md`](alternative-dosing/brainstorm.md)
> after the Edison-revised ranking, and follows the same procedure used
> in #2 and #5 (parametric OpenSCAD source → headless STL/PNG/spin GIF
> renders → printable-today design doc), per the toolchain agreed in
> [#7] (PrusaSlicer CLI, manual sweeps + pandas, no Optuna /
> Ax-BoTorch yet, FreeCAD Path / Kiri:Moto for any CNC step).

## What this preliminary design covers

The brainstorm + Edison literature critique converged on two top-ranked
systems for the one-day workshop build:

| Rank | Concept | Active components | Realistic min. dose (cohesive < 100 µm) | Closest published analogue |
| --- | --- | --- | --- | --- |
| 1 | **G — ERM-augmented sieve cup** | 1 (10 mm coin ERM + CR2032 + SPST switch) | ~0.5–2 mg open-loop; ~0.2–1 mg with weigh-and-stop | Vibratory sieve–chute microdoser, Besenhard 2015 [1] |
| 2 | **A — Tap-driven sieve cup** | 0 | ~1–5 mg open-loop; ~0.5–2 mg with iterative gravimetric | Same vibratory-sieve family [1], with quantized impulse |

Both share the **same printed cup body** — concept G is concept A plus
a side pocket for the ERM motor and a holder pocket for a CR2032 coin
cell. We exploit that by rendering both from a single parametric
OpenSCAD file ([`cad/sieve_cup.scad`](../cad/sieve_cup.scad)) with one
boolean parameter (`erm_motor_pocket`), so a future redesign of either
concept is a one-flag flip rather than a fork.

Concept A additionally needs a **bed-mounted anvil** that the gantry
pecks the cup against; that's a second tiny printed part
([`cad/tap_anvil.scad`](../cad/tap_anvil.scad)).

## Why these two concepts (one-paragraph recap)

The Edison literature critique
([`docs/alternative-dosing/edison_result.md`](alternative-dosing/edison_result.md),
task `c0c87f11-…`) noted that *continuous* bounded vibration matches
the published vibratory-sieve-chute regime — Besenhard 2015 [1]
demonstrates mg-scale capsule fills with a quantitatively-defined
no-flow threshold at low excitation amplitude and spillage at high
amplitude — far better than a *quantized* single-tap impulse. Hence
G (ERM motor on a coin cell) is the headline build, with A (passive,
gantry-as-actuator) as the parallel-track fallback that runs on the
*same printed cup* if the ERM hardware is unavailable. This pair
attacks the sub-10 mg cohesive-powder gap surfaced in PR #11 §5.

## Mechanical concept

```
                                      ↑ gantry Z+
   ┌─────────────────┐
   │   spindle boss  │  ← Ø 43 mm, two wrench-flats for 3018-Pro V2
   │  (clamp grip)   │    spindle clamp set-screws; vent at top
   ├─────────────────┤
   │   powder cup    │
   │   reservoir     │  ← Ø 24 mm × 22 mm = ~10 mL working volume
   │   (~5 mL fill)  │
   │ ╲ funnel cone ╱ │  ← anti-bridging cone biases powder centrally
   │  ╲___________╱  │
   ├──┬───────────┬──┤
   │  │ ░░ mesh ░░│  │  ← swappable polyester/SS mesh disc (PA66 25–80 µm
   │  └───────────┘  │    typical), clamped by a screw-on retainer ring
   └─────[ pad ]─────┘  ← annular strike pad, takes the impact
                ↓ powder
        ╔═══════════╗
        ║ tap_anvil ║  ← bolts to the 3018 bed on a 30×30 mm M3 pattern;
        ║   ↓ vial  ║    central bore aligns with cup mesh, drops powder
        ╚═══════════╝    straight into a 15 mm OD vial held in the collar
```

### Concept A — passive, gantry-as-actuator

1. The gantry rapids the loaded cup over the anvil.
2. A short G-code "peck" cycle (e.g. `G1 Z-2 F600` then `G1 Z+2 F1500`,
   repeated `N` times) drives the cup down so the cup's annular strike
   pad strikes the anvil's strike pad. Each impact is one tap.
3. Each tap dislodges a small mass of powder through the mesh; that
   mass falls through the anvil's central bore into the vial in the
   collar below.
4. Total dose = `N × per-tap mass`, calibrated against an external
   0.1 mg balance.

### Concept G — same cup + one ERM motor

1. The gantry positions the cup over the vial (no anvil needed for the
   open-loop variant; an anvil is still useful as a bump-stop).
2. A SPST switch on the side wires a CR2032 coin cell to a 10 mm coin
   ERM glued into the side pocket. The motor runs at its native
   amplitude/frequency (~12 000 rpm at 3 V → ~200 Hz vibration) for a
   timed interval `T`.
3. Total dose ≈ continuous mass-flow-rate × `T`, in the
   "well-defined operating window" of the vibratory-sieve regime
   (Besenhard 2015 [1]: an amplitude *threshold* below which there's
   no flow, and a spillage threshold above which the sieve dumps).
4. For sub-mg targeting, replace the dumb SPST switch with a relay
   driven from an external 0.1 mg balance — the closed-loop
   "weigh-and-stop" recipe used in [1] to prevent overshoot.

## Parameter table

The single SCAD source exposes every dimension that matters for either
concept as a top-of-file variable. The defaults below are the
preliminary-design starting point; adjust and re-render to retune.

| Variable | Default | Sets |
| --- | --- | --- |
| `cup_id` | 24.0 mm | Powder reservoir inside diameter |
| `cup_wall` | 2.0 mm | Cup side-wall thickness |
| `cup_height` | 22.0 mm | Powder column height (~10 mL working volume) |
| `cup_floor_thick` | 2.0 mm | Floor thickness around the mesh window |
| `mesh_window_d` | 18.0 mm | Open dia. through which the mesh dispenses |
| `mesh_relief_h` | 1.0 mm | Recess depth that captures the mesh disc |
| `inner_cone_h` | 3.0 mm | Anti-bridging funnel inside the cup |
| `boss_d` | 43.0 mm | Boss OD (matches 3018 spindle clamp) |
| `boss_h` | 18.0 mm | Boss length the clamp grips |
| `boss_flat_w` | 6.0 mm | Wrench-flat width on the boss |
| `retainer_pocket_d` | 32.0 mm | Mesh-retainer ring pocket OD |
| `strike_pad_d` | 14.0 mm | Inner reference dia. for the strike-pad annulus; the cup's strike-pad OD is `strike_pad_d + 6 mm` = **20 mm** to match the anvil strike face |
| `erm_motor_pocket` | `false` | **Concept selector** — `true` for G, `false` for A |
| `erm_pocket_d` | 10.4 mm | Coin-ERM pocket dia. (with print clearance) |
| `cell_pocket_d` | 5.5 mm | CR2032-holder pocket depth into wall |

For the anvil ([`cad/tap_anvil.scad`](../cad/tap_anvil.scad)): the
strike-face geometry (`strike_face_od = 20 mm`, `strike_face_id =
12 mm`) is matched to the cup's strike-pad outer diameter
(`strike_pad_d + 6 mm` = **20 mm**) and to a standard 15 mm OD vial
collar (`vial_collar_d = 16.5 mm`). The base plate is 60 × 50 × 5 mm
with four counterbored M3 holes on a 30 × 30 mm pattern, fitting the
standard 3018-Pro V2 T-slot bed.

## Recommended print settings

Same procedure as the bimodal-trough design doc in PR #5: PETG, layer
lines along the load, no support material, brim if necessary. The cup
is *monolithic* — no fasteners, no separate flexure-prestress step.

| Setting | Value | Why |
| --- | --- | --- |
| Material | **PETG** | Tough enough for repeated taps without crazing; resistant to PLA's brittle failure at the 100 + tap fatigue regime; friendly to most lab solvents (water, ethanol, IPA) for cleaning between runs. |
| Print orientation | **base flat on bed** (default STL orientation) | Layer lines run perpendicular to the impact axis, so each tap is a *compressive* hit on the strike pad rather than a peeling load on a layer line. |
| Layer height | **0.20 mm** | Cup wall is 2.0 mm = 10 layers — robust. The mesh-window step features are coarse so finer layers are not needed. |
| Wall count | **3 perimeters** (0.4 mm nozzle) | Gives a fully-solid 1.2 mm contour shell on the cup wall; combined with infill the wall is effectively solid. |
| Top/bottom layers | **5** | Keeps the floor + boss top stiff. |
| Infill | **40 % gyroid** | The boss takes lateral set-screw clamping — gyroid resists deformation and gives the spindle clamp something to grip. |
| Nozzle | **0.4 mm** | Standard. The thinnest features (boss vent Ø 3 mm, ERM pocket Ø 10.4 mm) are well above any tip-precision threshold. |
| Print speed | ≤ 60 mm/s | Standard PETG. The ERM pocket walls are short and benefit from slightly slower outer-wall speed (~30 mm/s). |
| Brim | **5 mm** | Footprint is small (Ø 32 mm); a brim resists tipping during the boss print. |
| Bed temp | 75–80 °C (PETG) | Standard. |
| Nozzle temp | 235–245 °C (PETG) | Standard. |
| Cooling | **30 % fan** (PETG) | Standard. |
| Estimated print time | **~75 min** (cup) + ~25 min (anvil) | Tested in PrusaSlicer with the above settings. |
| Estimated material   | **~14 g PETG** total | < $0.50 per copy — print 3-4 cup variants at different `mesh_window_d` for parameter sweep. |

For the anvil: same PETG/0.20 mm/3-perimeter recipe; print **bolt face
down** (default STL orientation) so the strike face is the topmost
layer (a single, clean surface — no layer-line texture on the impact
zone).

For the **mesh disc itself**: not 3D-printed. Cut a Ø 30 mm disc from
food-grade polyester sieve cloth (PA-66, 25 µm / 38 µm / 53 µm / 80 µm
apertures, available from McMaster, Saatifil, or any lab-supply
catalogue) or from stainless 304 mesh (50 / 100 / 200 mesh = 297 / 149
/ 74 µm apertures). The matched-to-powder mesh is the **single most
important calibration knob** — Besenhard 2015 §3 reports a hard no-flow
threshold below a powder-specific amplitude, and the mesh aperture
times the cohesive aggregate size sets that threshold. **Print 4 cups
at a time** so the same powder can be tried against four meshes
without re-clamping.

## Mounting & test procedure

1. **Clamp the cup** in the 3018-Pro V2 spindle clamp by gripping the
   boss between the two opposed wrench-flats. Snug the set-screws; do
   *not* over-torque (PETG creeps).
2. **(Concept A only)** Bolt the anvil to the bed plate with four
   M3 × 8 mm cap screws on the 30 × 30 mm hole pattern. Drop a 15 mm
   vial into the collar.
3. **Insert the mesh** into the cup base recess; clamp it with the
   printed retainer ring (or, for the simplest possible build, a dab
   of cyanoacrylate around the mesh perimeter — single-use cup).
4. **(Concept G only)** Glue the ERM into the side pocket with a dab
   of cyanoacrylate, with the lead wires routed up the wall slot.
   Solder the wires to a CR2032 holder (Keystone 1066 or equivalent)
   slipped into the back-side pocket, with a SPST slide switch glued
   to a free flat. Test the motor briefly with the cup empty — it
   should buzz audibly.
5. **Load powder** through the boss vent (or by removing the cup from
   the clamp, filling, and re-clamping) to ~50 % of the reservoir
   height — over-filling causes powder to compact under the funnel
   cone and silence the dispenser.
6. **Calibrate per powder** against an external 0.1 mg balance (the
   "iterative gravimetric" recipe in the brainstorm):
   - For concept A: vary `N` (tap count) in {1, 5, 10, 25, 50}, record
     mass for each, fit a line to (`N`, `mass`).
   - For concept G: vary `T` (vibration time) in {0.2, 0.5, 1.0, 2.0,
     5.0 s}, record mass, fit a line. **Verify the operating window** —
     the linear region should sit between a no-flow regime at very
     short `T` (excitation × fill-condition combination below
     threshold) and a spillage regime at long `T`. The Besenhard 2015
     [1] finding is that this window is real and definable for any
     given mesh + powder + amplitude combination.
7. **Bed-condition mitigation** (Besenhard 2015 [1] §3 explicitly
   calls this out as a control variable): re-level the powder bed
   between runs by giving the cup three light side-taps with a
   fingernail before each dispense cycle.
8. **Cycle test:** 200 dispenses on a single fill, expecting ≤ 15 %
   RSD open-loop on G (per Besenhard 2015 [1] for the closest
   peer-reviewed analogue) and ≤ 30 % RSD on A.

## Build-day timeline (one workshop day)

Mirrors the half-day breakdown in PR #5 / PR #2:

| Hour | Activity |
| --- | --- |
| 0:00 – 0:30 | Print 4 × cup (G variant) + 1 × anvil + 1 × spare cup (A variant) overnight (or in parallel on two printers; ~2 h total for one Prusa MK3). |
| 0:30 – 1:00 | Cut four mesh discs (e.g. 25 / 38 / 53 / 80 µm polyester) using a sharp Ø 30 mm steel punch. |
| 1:00 – 2:00 | Glue ERM + CR2032 holder + SPST switch into one G cup; solder; bench-test the buzz. |
| 2:00 – 4:00 | Mount cup in 3018 clamp; bolt anvil to bed; write a simple G-code peck cycle inline (rapid above the anvil, feed down to strike, retract, dwell, repeat); homing + dry-run on empty cup. |
| 4:00 – 6:00 | Loaded characterisation against external 0.1 mg balance: vary `T` (G) or `N` (A), build (`time → mass`) calibration. |
| 6:00 – 8:00 | Cycle test (200 dispenses); record RSD; identify the no-flow / spillage thresholds for the as-built unit; pick the operating point for actual use. |

The split is generous; if any single step blows past its window the
parallel-track fallback (run concept A on the same printed cup with no
electronics) is always available.

## Validation against the published analogues

| Predicted behaviour | Source | How we'd notice if the design departs from it |
| --- | --- | --- |
| Hard no-flow threshold below a critical excitation amplitude | Besenhard 2015 [1] §3 | At very short `T` (G) or single tap (A), `mass = 0` regardless of mesh / fill. Below the threshold, no calibration line. |
| Spillage at excitation amplitudes much above the operating window | Besenhard 2015 [1] §3 | At long `T` (G) or excessive peck velocity (A), dispensed mass becomes super-linear in time, RSD blows up, vial overflows. Operating window is the *linear* middle. |
| Low-mg targets achievable (≈ 2.5 mg in [1]) with 5–15 % RSD open-loop | Besenhard 2015 [1] §2 | If RSD on the G calibration cycle is much worse than 15 %, suspect ERM mounting (loose vibration coupling) or mesh blinding. |
| Cohesive sub-100 µm powders systematically underperform freer-flowing ones | Besenhard 2015 [1] §4; Hou 2024 [4] | Freer-flowing reference powders (glass beads, sugar) should hit single-digit RSD; switching to the cohesive target powder will move the operating window left and increase RSD. |
| Closed-loop weigh-and-stop yields ~3–10 % RSD on G | Besenhard 2015 [1] §2; brainstorm + Edison ranking row 1 | If the closed-loop variant doesn't beat the open-loop variant by ≥ 2× in RSD, the balance latency / control loop is the bottleneck — go to a faster balance. |

## Files in this preliminary design

| Path | Role |
| --- | --- |
| [`cad/sieve_cup.scad`](../cad/sieve_cup.scad) | Single parametric source for both concept-A and concept-G cups (toggled by `erm_motor_pocket`). |
| [`cad/tap_anvil.scad`](../cad/tap_anvil.scad) | Bed-mounted anvil for concept A. |
| [`cad/sieve-cup.stl`](../cad/sieve-cup.stl) | Concept-A printable mesh. |
| [`cad/sieve-cup-erm.stl`](../cad/sieve-cup-erm.stl) | Concept-G printable mesh. |
| [`cad/tap-anvil.stl`](../cad/tap-anvil.stl) | Anvil printable mesh. |
| [`cad/sieve-cup{,-erm}-iso.png`](../cad/), [`cad/tap-anvil-iso.png`](../cad/tap-anvil-iso.png) | Static iso renders. |
| [`cad/sieve-cup{,-erm}-spin.gif`](../cad/), [`cad/tap-anvil-spin.gif`](../cad/tap-anvil-spin.gif) | 360° turntable spins (re-run via `python -m scripts.render_sieve_cup --variant {passive,erm,anvil}`). |
| [`scripts/render_sieve_cup.py`](../scripts/render_sieve_cup.py) | Companion render script (mirrors `scripts/render_trough_spin.py` from PR #5). |
| [`cad/README.md`](../cad/README.md) | Per-folder quickstart + render commands. |

## What is *not* yet here

Per PR #7's "manual sweeps + pandas/Jupyter scorecard by default;
Optuna only past ~5 parameters and ~15+ physical builds" — none of the
following is in this preliminary design, by intent:

- **No FEA / physics analyser.** The sieve cup has no stiffness-driven
  bistability question (unlike PR #5's bimodal trough), so a PRBM /
  CalculiX cross-check would not buy us anything; the relevant physics
  is the powder-flow-through-mesh relationship, which is empirical and
  per-powder. A future iteration could add a `scripts/sieve_dose_model.py`
  Beverloo-style flow-rate estimator if a second build round needs it.
- **No Optuna sweep.** The four parameters that matter
  (`mesh_window_d`, mesh aperture, fill height, ERM voltage / `N` taps)
  are well within the manual-sweep regime. A pandas notebook capturing
  the (`time` → `mass`) calibration curves per (cup, powder, mesh) cell
  is the right next artefact, but it needs physical data we don't yet
  have.
- **No CNC toolpath.** Both parts are FDM-only. If a future revision
  needs a precision-machined strike face (e.g. for hardness on the
  anvil), the FreeCAD Path / Kiri:Moto → GRBL path agreed in PR #7 is
  the route — but the preliminary design ships printable as-is.

## References

1. Besenhard, M.O. *et al.* "Accuracy of micro powder dosing via a
   vibratory sieve-chute system." *Eur. J. Pharm. Biopharm.* 94,
   264–272 (2015). DOI: [10.1016/j.ejpb.2015.04.037](https://doi.org/10.1016/j.ejpb.2015.04.037).
2. Alsenz, J. "PowderPicking: an inexpensive, manual, medium-throughput
   method for powder dispensing." *Powder Technology* 209, 152–157
   (2011). DOI: [10.1016/j.powtec.2011.02.014](https://doi.org/10.1016/j.powtec.2011.02.014).
3. Besenhard, M.O. *et al.* "Micro-feeding and dosing of powders via a
   small-scale powder pump." *Int. J. Pharm.* 519, 314–322 (2017).
   DOI: [10.1016/j.ijpharm.2016.12.029](https://doi.org/10.1016/j.ijpharm.2016.12.029).
4. Hou, P. C-H. "Development of a micro-feeder for cohesive
   pharmaceutical powders." Dissertation (2024).
   DOI: [10.48730/4gp7-jb67](https://doi.org/10.48730/4gp7-jb67).

Full Edison-fetched literature critique (with five additional
citations including Faulhammer 2014 dosator and Jiang 2023
dual-arm-robot evidence) is at
[`alternative-dosing/edison_result.md`](alternative-dosing/edison_result.md).

[#2]: https://github.com/vertical-cloud-lab/powder-excavator/pull/2
[#5]: https://github.com/vertical-cloud-lab/powder-excavator/pull/5
[#7]: https://github.com/vertical-cloud-lab/powder-excavator/pull/7
[#11]: https://github.com/vertical-cloud-lab/powder-excavator/pull/11
[#12]: https://github.com/vertical-cloud-lab/powder-excavator/issues/12

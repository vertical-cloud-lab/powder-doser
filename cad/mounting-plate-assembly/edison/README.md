# Edison Scientific feedback — servo-pinion gear stripping

Context: issue #65, comment
[4802963723](https://github.com/vertical-cloud-lab/powder-doser/issues/65#issuecomment-4802963723).
The MG996R-driven mounting-plate tilt gears worked during the Utah AI
Convergence '26 poster session but began **stripping the 3D-printed servo
pinion teeth** after a day of repeated use, with skipping reduced when the
(taped, not screwed) motor was pressed down by hand.

## Files

- `servo_gear_stripping_query.py` — reproducible Edison `LITERATURE_HIGH`
  dispatcher/fetcher (`python3 servo_gear_stripping_query.py dispatch|fetch`).
  Reads `EDISON_API_KEY` (or `EDISON_PLATFORM_API_KEY`), `.strip()`-ed.
- `servo_gear_stripping_answer.md` — the formatted Edison answer (task
  `765aef1c-eae6-4ced-86e3-eac48ebb8a13`), with citations.
- `servo_gear_stripping_raw.json` — raw task response for reproducibility.
- `task_id.txt` — the Edison task id.

## Key takeaways (cheapest → most definitive)

1. **Rigid screw-down servo mount (highest payoff, ~free).** The failure is
   primarily *insufficient mesh engagement* from a compliant mount letting
   the center distance grow and teeth ride up / skip. At module ≈ 0.91 mm
   the working depth is only ≈ 0.91 mm, so a 0.2–0.3 mm center-distance
   growth nearly disengages the mesh. Bolt the servo through all four ears
   with M3 screws, capture it in a tight pocket, add gussets / a metal
   angle, and ideally an outboard bearing on the hinge-gear shaft. **Yes —
   a stiffening bracket on the motor mount should help materially.**
2. **Coarsen the module 0.91 → ~1.5 mm** (keep 20T/40T). Lewis root stress
   scales ≈ 1/module, dropping ~31 MPa → ~11 MPa and printing far cleaner.
3. **Switch the printed pinion PLA/PETG → PA12 nylon (or PA-CF).** PETG is
   *weaker* than PLA and would make it worse; PA12 is the best printed
   choice (tougher, ~4× the fatigue life of PA6). Print hot/dry, ~100%
   infill, teeth oriented so layers stack across the face width.
4. **Widen the face 12 → 15–18 mm** if packaging allows (~⅓ stress drop).
5. **Metal/POM pinion** = definitive fix; **required** at the current fine
   module + torque unless the module is coarsened. A metal-gear MG996R only
   helps the *internal* servo train, not the external printed pinion.
6. Architecture alternatives for production reliability: worm drive
   (self-locking), micro linear actuator + lever, or a geared stepper.

**Material note:** the repo does **not** currently specify PLA vs PETG for
the printed parts (no filament/material callout in `cad/` or
`BILL-OF-MATERIALS.md`). Per Edison, neither brittle PLA nor weaker PETG is
ideal here — PA12 nylon is the recommended printed material, and the pinion
should ideally be POM/metal at the present geometry.

## Picking from the Bambu Lab "strength & stiffness" collection

Follow-up question (PR comment): which of the
[Bambu Lab strength/stiffness filaments](https://bambulab.com/en-us/filament/collections/exceptional-in-strength-stiffness)
suits the printed gears? That collection is the fibre-reinforced engineering
grades — the relevant ones are:

| Filament | Matrix | Flex. strength (XY) | Stiffness | HDT | Fit for the gears |
|---|---|---|---|---|---|
| **PA6-CF** | nylon 6 + carbon | ~151 MPa | high (~4 GPa+) | 186 °C | **Best all-round pick** — nylon's toughness/fatigue + wear resistance with CF stiffness to hold tooth form |
| **PAHT-CF** | high-temp nylon + carbon | high | high | high | Equivalent to PA6-CF, lower moisture pickup; good alternative |
| **PA6-GF** | nylon 6 + glass | (see TDS) | highest rigidity | high | Stiff & strong, less abrasive than CF on the nozzle; viable |
| PPA-CF | PPA + carbon | ~208 MPa | optimal (~8 GPa+) | 227 °C | "Near-metal" but overkill, pricey, demanding to print |
| PET-CF | PET + carbon | ~131 MPa | high (~4 GPa+) | 205 °C | Strong + moisture-tolerant, but PET matrix wears worse than nylon for gear teeth |

**Recommendation:** print the pinion (and the mating hinge-gear band) in
**PA6-CF** — it is the closest match to Edison's PA12/PA-CF guidance: a tough,
fatigue- and wear-resistant nylon matrix (ideal for gear teeth under repeated
cyclic load) stiffened with carbon fibre so the teeth hold their profile and
resist the bending that was stripping the PLA pinion. **PAHT-CF** is an equally
good substitute (and picks up less moisture); **PA6-GF** is the next choice if
you want to avoid the more abrasive CF grades. Skip PET-CF for the teeth (PET
matrix is less wear-/fatigue-friendly than nylon) and PPA-CF is more than this
duty needs.

Practical notes for any of these fibre-reinforced grades:
- **Hardened steel nozzle required** (CF/GF are abrasive) and an enclosure /
  high-temp hotend (Bambu X1C-class).
- **Dry the filament** before printing — nylons are hygroscopic and wet prints
  lose strength and dimensional accuracy (which directly hurts gear mesh).
- ~100 % infill, and orient the gear so layers stack **across the face width**
  (tooth-root continuity in the loaded direction).

Caveat: a filament upgrade was only #3 on Edison's priority list. The biggest
wins remain the **rigid screw-down servo mount / stiffening bracket** (so the
mesh can't separate) and a **coarser module**; PA6-CF pairs best with those
rather than replacing them.

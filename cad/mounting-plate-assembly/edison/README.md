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

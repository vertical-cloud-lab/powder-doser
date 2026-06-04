# Measuring the maximum powder volume of the auger

This folder answers
[*"Measuring Auger Volume"*](https://github.com/vertical-cloud-lab/powder-doser/issues/48):

> suggest methods for measuring the maximum possible volume of each auger,
> focusing on Auger Type 4 … select the best method and calculate powder
> capacity for Auger 4 … avoid CAD software if possible … ideally a function
> of length, i.e. a 5 in auger has *x* powder capacity.

"Auger Type 4" is the dispensing-nozzle variant defined in
[issue #48 comment 4513155870](https://github.com/vertical-cloud-lab/powder-doser/issues/48#issuecomment-4513155870):
**"continuing the screw as the middle shaft shrinks as well"** (it combines
variants 2 and 3). All four variants share the same tube, top cap and Ø3 mm
exit; they differ only in the bottom-funnel / shaft-tip / helix geometry near
the exit (see [`../nozzle-variants.scad`](../nozzle-variants.scad)).

The deliverable is [`auger_capacity.py`](auger_capacity.py): a parametric
model that computes the **maximum powder void volume** (the empty space inside
the barrel that powder can fill) for any variant and any barrel length, with
**no CAD software in the loop**, and a generated table
[`auger_capacity_table.csv`](auger_capacity_table.csv).

## What "maximum possible volume" means here

The maximum powder a fully-loaded auger can hold is the **void volume** inside
the barrel: the housing's open interior (tube bore + funnel cone, up to the
underside of the top cap) **minus** the solid screw (central shaft + helical
fin). It is the theoretical ceiling — every void packed solid with powder.
(The *operationally* useful number, the dose moved per screw turn, falls out of
the same model and is reported below.)

## Methods considered

| # | Method | Avoids CAD? | Gives V(length)? | Notes |
|---|--------|:----------:|:----------------:|-------|
| 1 | **CAD "measure volume"** — load the part in OpenSCAD/Fusion/FreeCAD, subtract screw from a barrel solid, read the volume. | ✗ | ✗ (re-measure per length) | What the issue explicitly asks to avoid. Accurate but manual, not a formula. |
| 2 | **Physical displacement** — fill a printed auger with water/glass beads and weigh, or Archimedes-displace the screw. | ✓ | ✗ | Needs a print per length; bead packing ≠ geometric void; messy, slow. |
| 3 | **STL mesh integration** — take the committed `*.stl`, compute its solid volume (divergence theorem), subtract from a bore cylinder. | ✓ | ✗ (one mesh = one length) | Good cross-check, but each length needs its own exported mesh — not a formula, and still rides on a meshing step. |
| 4 | **Analytic geometric integration** — every piece (tube wall, funnel cone, shaft, helical fin) has a closed-form cross-section at height *z*, so integrate the void area `A(z)` along the barrel. | ✓ | ✓ (closed form) | Pure geometry + arithmetic; yields an exact `V(L)` and runs in milliseconds. |

## Selected method: analytic geometric integration (method 4)

It is the only candidate that satisfies **both** constraints in the issue — no
CAD software **and** a capacity-as-a-function-of-length result — and it is the
cheapest and most reproducible.

The auger is a solid of revolution (tube wall, bottom funnel cone, Ø8 mm
central shaft, top cap) plus **one** helical fin, which is a flat radial blade
swept up the shaft. At any height *z* the void cross-section is

```
A_void(z) = π·r_bore(z)²  −  π·r_shaft(z)²  −  A_fin_in_bore(z)
```

where `r_bore(z)` is the housing's open interior radius (the funnel cone in the
bottom 12 mm, then the Ø21 mm bore), `r_shaft(z)` is the central shaft (a cone
in the tapered tip of v3/v4, then Ø8 mm), and `A_fin_in_bore(z)` is the
2 mm-thick fin blade restricted to the open annulus (its inner/outer "sink"
overlaps into the shaft and wall are not double-counted). The capacity is the
integral of `A_void(z)` from the exit up to the underside of the top cap,
evaluated by thin z-slices.

Because the bore, shaft and fin cross-sections are all **constant** along the
straight barrel, the integral is **exactly linear in length** above the fixed
end features:

```
V(L) = 283.095 · L  −  3929      [mm³,  L in mm]   (Auger 4)
```

The slope is the per-millimetre void of the straight barrel,
`π·(10.5² − 4²) − 2·(10.5 − 4) = 283.095 mm³/mm`; the constant folds in the
funnel/tapered-tip and top-cap end effects. Every variant shares the same slope
(same tube and screw) and differs only in the constant.

### Validation against the printed mesh (method 3 as a check)

`python3 auger_capacity.py --validate` re-derives each **solid** test piece
from the identical slice model and compares it with the signed volume of the
committed STL meshes (`../archimedes-auger-test-nozzle*.stl`, L = 90 mm):

| variant | slice model (mm³) | STL mesh (mm³) | error |
|:-------:|------------------:|---------------:|------:|
| 1 | 22068.1 | 22189.6 | −0.55 % |
| 2 | 20148.7 | 20278.2 | −0.64 % |
| 3 | 21814.7 | 21931.5 | −0.53 % |
| 4 | 21898.7 | 22083.6 | −0.84 % |

All four agree to better than 1 %, confirming the geometry model (the small
residual is the flat-blade-per-slice approximation of the slightly slanted
helix). Since the void figure comes from the same parameters, it inherits that
accuracy.

## Result — Auger 4 powder capacity

Run `python3 auger_capacity.py` (defaults to variant 4 at L = 127 mm = 5 in):

- **Per length:** `V(L) = 283.095·L − 3929 mm³` (L in mm) =
  **7.19 mL of void per inch** of barrel above the fixed ends.
- **A 5 in (127 mm) Auger 4 holds ≈ 32.0 mL** (32 024 mm³) of powder at full
  pack — about **38 g** of fine NaCl at a 1.2 g/mL bulk density.
- The printed **90 mm (3.54 in) test piece** holds **≈ 21.5 mL** (21 549 mm³).
- **Dose per screw revolution** (10 mm pitch): `283.095 × 10 ≈ 2.83 mL/rev`
  (2831 mm³) of channel volume — the natural metering unit for dosing control.

Capacity vs barrel length for Auger 4 (full table for all four variants in
[`auger_capacity_table.csv`](auger_capacity_table.csv)):

| length (mm) | length (in) | V (mm³) | V (mL) |
|------------:|------------:|--------:|-------:|
|  60 | 2.36 | 13 056 | 13.06 |
|  90 | 3.54 | 21 549 | 21.55 |
| 100 | 3.94 | 24 380 | 24.38 |
| 127 | 5.00 | 32 024 | 32.02 |
| 150 | 5.91 | 38 535 | 38.53 |
| 180 | 7.09 | 47 028 | 47.03 |
| 200 | 7.87 | 52 690 | 52.69 |
| 250 | 9.84 | 66 844 | 66.84 |

The four variants are within ~1.5 mL of each other at any given length (they
share the entire barrel and differ only in the small funnel/tip region):
Auger 2 is the largest (≈ 33.8 mL at 5 in, its short funnel leaves the most
open bore) and Auger 1 the smallest (≈ 31.9 mL).

### Caveat — geometric maximum vs. usable dose

`V(L)` is the **geometric** maximum (every void packed solid). It is already
the right answer to "maximum possible volume," but two operational factors make
the powder actually *delivered* smaller:

- **Fill fraction** — a gravity- or auger-fed barrel rarely packs 100 %; the
  helical channel typically runs partially full.
- **Bulk vs. true density** — using a measured *bulk* (tapped) density already
  folds inter-particle porosity into the mass estimate.

For dosing control the **per-revolution** figure (≈ 2.83 mL/rev) multiplied by a
calibrated volumetric-efficiency factor is the number to use; the bench tests in
issue #48 are the right way to fit that factor per powder.

## Reaching a larger target volume (e.g. 250 mL, no hopper)

`V(L)` makes the design trade-off explicit. Length alone cannot get far: at the
current Ø25 mm barrel the void is only `283 mm³/mm`, so 250 mL would need
`250 000 / 283 ≈ 884 mm ≈ 35 in` of barrel — not buildable as one screw. Capacity
instead scales with the bore **area**, i.e. roughly the **square of the
diameter**, so the practical lever is diameter, not length.

`python3 auger_capacity.py --target-ml 250` inverts the model to size the bore
needed at each length (holding the Ø8 mm shaft, 2 mm fin, 2 mm wall and 10 mm
pitch fixed):

| length (mm) | length (in) | bore Ø (mm) | outer Ø (mm) | mL/rev | vs Ø25 now |
|------------:|------------:|------------:|-------------:|-------:|-----------:|
| 150 | 5.91 | 47.6 | 51.6 | 16.9 | 2.07× |
| 200 | 7.87 | 41.5 | 45.5 | 12.7 | 1.82× |
| 250 | 9.84 | 37.3 | 41.3 | 10.2 | 1.65× |
| 300 | 11.81 | 34.3 | 38.3 |  8.5 | 1.53× |
| 350 | 13.78 | 31.9 | 35.9 |  7.3 | 1.44× |

So a 250 mL screw is a roughly **1.5–1.8× wider barrel** (outer Ø ≈ 38–46 mm) at
a 250–300 mm length — a modest diameter bump, not a 35 in tube. Two design
consequences cross-reference against the current geared auger
([PR #49](https://github.com/vertical-cloud-lab/powder-doser/pull/49)):

- **Drive torque & gear band.** A wider tube needs a larger gear band (the
  Ø48 mm/48-tooth band roots on the bore) and lifts more powder per turn, so the
  NEMA 11 likely needs more reduction or a NEMA 14/17.
- **Metering resolution.** The per-revolution dose grows with the bore too
  (≈ 8–17 mL/rev above), which is coarse for fine dosing; dropping the 10 mm
  pitch claws resolution back without losing volume.

The bracket/clamp ([PRs #47](https://github.com/vertical-cloud-lab/powder-doser/pull/47),
[#53](https://github.com/vertical-cloud-lab/powder-doser/pull/53)) bore would
also follow the wider tube. The intercept-based sizing is accurate to a few
percent; confirm a final pick by re-running the slice model on the resized
geometry.

## Reproducing

```sh
python3 auger_capacity.py                  # Auger 4 summary + length table
python3 auger_capacity.py --all            # all four variants at 5 in
python3 auger_capacity.py --variant 4 --length 127
python3 auger_capacity.py --validate       # check vs committed STL meshes
python3 auger_capacity.py --target-ml 250  # size bore/length to reach 250 mL
python3 auger_capacity.py --csv auger_capacity_table.csv
```

Pure Python standard library — no NumPy, no OpenSCAD, no CAD kernel. The
geometry constants are copied verbatim (with citations) from
[`../auger-core.scad`](../auger-core.scad) and
[`../nozzle-variants.scad`](../nozzle-variants.scad), so the script never has to
call OpenSCAD; if those sources change, update the constants at the top of
`auger_capacity.py` to match.

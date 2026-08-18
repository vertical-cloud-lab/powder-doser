# Powder-doser mounting plate + baseplate

> Resolves issue [vertical-cloud-lab/powder-doser#62](https://github.com/vertical-cloud-lab/powder-doser/issues/62).

This package provides the **foundation** of the powder-doser machine: the
rectangular **mounting plate** that carries all the auger sub-assembly
parts (auger brackets, tap-collar mount, NEMA-11 motor + motor-mount
boss), the rectangular **baseplate** that sits on the bench and holds the
hinge posts + powder-fall window, and the **M5 hinge pin** that joins
each mounting-plate knuckle to its matching baseplate post.

The mounting plate **rotates from horizontal (0°) to vertical (90°)**
about a hinge axis that sits along one edge of the plate (the +Y edge in
our frame).  At 0° the auger is horizontal — the rest pose for loading
powder.  At 90° the plate is vertical and the auger points straight
DOWN past the hinge, dispensing powder through the baseplate's powder
window directly into a cup placed below.

The design follows the user's "Hinge Design (Offset)" sketch in the
issue: the mounting plate has two **triangular hinge knuckles** that
drop below the plate plane to a pair of eyes; the baseplate has two
**upright posts** with matching eyes that interleave beside the
knuckles, and a single M5 pin per pair forms the pivot.

Each upstream part's bolt pattern is replicated on the plate at the
correct location, so the brackets / tap-collar / motor from the in-flight
upstream PRs drop straight in without modification:

| Part                 | Source PR | Hole pattern on the plate            | Plate Y (mm) |
| -------------------- | --------- | ------------------------------------ | ------------ |
| Front auger bracket  | [#55](https://github.com/vertical-cloud-lab/powder-doser/pull/55) | 2 × M3 (Ø3.4) at X = ±24 | **+95** |
| Rear auger bracket   | [#55](https://github.com/vertical-cloud-lab/powder-doser/pull/55) | 2 × M3 (Ø3.4) at X = ±24 | **−95** |
| Tap-collar mount     | [#51](https://github.com/vertical-cloud-lab/powder-doser/pull/51) | 2 × M3 (Ø3.4) at X = ±24 | **+75** |
| NEMA-11 motor boss   | [#49](https://github.com/vertical-cloud-lab/powder-doser/pull/49) | 4 × M3 at 23 mm pitch + Ø22 pilot, integrated boss | motor face at Y ≈ **+27** |
| Hinge knuckles (×2)  | this PR   | Ø5.4 (M5) bore, eyes on X-axis        | edge at Y = **+110** |
| Hinge posts (×2)     | this PR   | Ø5.4 (M5) bore on baseplate           | Y = **+122** |

The gear-mesh centre distance comes from PR #49 (`C = (Z1 + Z2)·m / 2 =
32 mm` for the 48-tooth / 16-tooth module-1 pair), so the motor sits at
**X = +32 mm**, parallel to the auger and just behind the gear band at
Y ≈ +41.67 mm.  A rectangular clearance window through the plate keeps
the Ø50 gear band tip and the Ø18 pinion tip from rubbing on the plate.

## Geometry at a glance

| Dimension                                      | Value     |
| ---------------------------------------------- | --------- |
| Mounting plate footprint (X × Y × Z)           | 110 × 220 × 6 mm |
| Baseplate footprint (X × Y × Z)                | 150 × 328.7 × 6 mm |
| Plate thickness (Z)                            | 6 mm |
| Baseplate thickness (Z)                        | 6 mm |
| Auger centreline above plate top (Z\_AUG)      | +19.73 mm |
| Hinge axis (Y, Z)                              | (+110.0, −24.0) mm |
| Hinge drop (knuckle eye below plate underside) | 18 mm |
| Hinge post height (above baseplate top)        | 28 mm |
| Knuckle / post X pitch                         | ±30 mm (60 mm pitch) |
| Knuckle / post eye OD × bore                   | Ø12 × Ø5.4 (M5) |
| Dispense @ 0° tilt (Y, Z)                      | (+125.0, +19.73) mm |
| Dispense @ 90° tilt (Y, Z)                     | (+153.7, −39.0) mm |
| Powder window (X × Y)                          | 50 × 50 mm centred at Y = +153.7 |
| Bracket Y spacing                              | 190 mm centre-to-centre |
| Baseplate corner bolt holes                    | 4 × Ø5.4 (M5), 8 mm from each corner |

See `drawing/engineering_drawing.{png,pdf,svg}` for the full dimensioned
2-view engineering drawing (mounting plate top + side, baseplate top,
and a hinge-detail blow-up).

## Files

```
cad/mounting-plate/
├── cad_model.py              ← parametric CadQuery model (the source of truth)
├── render_views.py           ← VTK iso / front / top / side PNG per part
├── render_assembly.py        ← assembly renders at 0°, 45°, 90° tilt
├── engineering_drawing.py    ← matplotlib dimensioned drawing
├── step/                     ← printer-ready STEP per part
├── stl/                      ← printer-ready STL per part
├── views/                    ← four-view PNGs per part
├── assembly/                 ← 0° / 45° / 90° iso + front/side/top PNGs
└── drawing/engineering_drawing.{png,pdf,svg}
```

## Reproducing everything

```sh
pip install cadquery matplotlib numpy vtk
sudo apt install xvfb

cd cad/mounting-plate
python3 cad_model.py                    # → step/*.step, stl/*.stl
xvfb-run -a python3 render_views.py     # → views/<part>_(iso|front|top|side).png
xvfb-run -a python3 render_assembly.py  # → assembly/*.png
python3 engineering_drawing.py          # → drawing/engineering_drawing.{png,pdf,svg}
```

All three scripts read parameters from the constants at the top of
`cad_model.py` — change a value there and everything downstream
(dimensions on the drawing included) updates consistently.

## Design notes

* **The "unnecessary space" the user called out has been removed.**
  The plate is a tight rectangle (110 × 220 mm) sized to the parts it
  carries; no large unused panel on the +X side.
* **Hinge axis offset BELOW the plate plane.**  At 90° this lets the
  plate swing up cleanly past the baseplate without the plate underside
  colliding with the hinge posts.  The knuckle eyes drop 18 mm below
  the plate underside and the posts rise 28 mm above the baseplate top,
  so at 0° there's a 28 − 18 = 10 mm working gap between the
  plate-underside and the baseplate-top.
* **At 0° the plate is cantilevered** — supported only at the hinge edge.
  The auger and motor weights are small (< 1 kg total) and the
  cantilever length is short, so 6 mm PLA at 100 % infill is more than
  rigid enough.  If extra stiffness is wanted later, add a folding rest
  leg under the motor end.
* **Powder window position is set by the 90° dispense landing**
  (Y = +153.7 mm in our frame), not the 0° dispense position.  The
  90° pose is the operating pose — the 0° pose is a loading / cleaning
  rest position with no powder flowing.
* **Drive train.**  Parallel-axis gearmesh with the PR #49 auger gear
  band: a NEMA-11 stepper (the 28 × 28 × 32 mm body) sits on an
  integrated boss on the plate top, with its shaft and pinion entering
  a Ø22 pilot through the boss to mesh with the auger gear band
  underneath.  The Ø50 band tip and Ø18 pinion tip both extend below
  the plate top — the rectangular clearance window in the plate
  accommodates both.
* **All hole sizes are clearance holes** — Ø3.4 for M3 fasteners,
  Ø5.4 for M5 fasteners — assuming a printed thread is not used.
  Add heat-set inserts or back the holes with M3/M5 nuts as needed.

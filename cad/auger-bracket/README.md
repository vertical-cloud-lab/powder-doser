# Auger Clamp Bracket

Split shaft-collar with mounting plate, sized to clamp the v5
Archimedes auger from `cad/auger/` (OD = 25 mm). Two of these
bolt to a flat chassis rail to support the auger.

The whole part is **one piece**, generated as a single 2D profile
(ring + ears + plate + tangent flank transitions, all in the XZ
plane) extruded uniformly along the auger axis (Y, 10 mm).

## Files

| File | Purpose |
|------|---------|
| `auger-bracket.scad` | Parametric OpenSCAD source; all dimensions named at the top. |
| `auger-bracket.stl`  | Binary STL, ready to slice. |
| `views/*.png`        | iso / front / top / side renders. |

## Geometry (per the sketch)

| Feature | Value |
|---|---|
| Auger OD | 25.0 mm |
| Diametral bore clearance | 0.8 mm (bore Ø 25.8 mm) |
| Ring wall | 4.0 mm |
| Ring width (along auger axis) | 10.0 mm |
| Clamp slit width | 2.0 mm |
| Pinch-bolt hole | M3 clearance Ø 3.4 mm |
| Plate length × thickness | 50 × 4 mm |
| Mount holes | 2 × M3 clearance, 38 mm apart |
| Print-on face | Flat bottom of the plate (no supports) |

## Reproducing the renders

```bash
cd cad/auger-bracket
xvfb-run -a openscad -o auger-bracket.stl --export-format=binstl auger-bracket.scad
xvfb-run -a openscad -o views/iso.png   --imgsize=600,600 --autocenter --viewall --colorscheme=Tomorrow auger-bracket.scad
xvfb-run -a openscad -o views/front.png --imgsize=600,600 --autocenter --viewall --colorscheme=Tomorrow --camera=0,0,0,90,0,0,140 auger-bracket.scad
xvfb-run -a openscad -o views/top.png   --imgsize=600,600 --autocenter --viewall --colorscheme=Tomorrow --camera=0,0,0,0,0,0,140  auger-bracket.scad
xvfb-run -a openscad -o views/side.png  --imgsize=600,600 --autocenter --viewall --colorscheme=Tomorrow --camera=0,0,0,90,0,90,140 auger-bracket.scad
```

OpenSCAD reports `Simple: yes` / `Volumes: 2` (the part + its bore
cavity), and `trimesh` confirms `is_watertight: True`.

## Print

- 0.2 mm layers, 0.4 mm nozzle, 3 perimeters, 25 % gyroid infill.
- PLA or PETG.
- Print bottom-face-down — no supports.
- M3 socket-head + nut on the pinch bolt; M3 × 12 cap screws into
  the rail through the two plate holes.

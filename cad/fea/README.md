# CalculiX FEA of the carousel parts

FEA of the chain carousels v3 and v4 and of the paternoster, as they stand on #185 at
[`45e9740`](https://github.com/vertical-cloud-lab/powder-doser/tree/45e9740), for deflection, stress, safety factor and
natural frequency. Every model is meshed with gmsh (second-order tetrahedra, C3D10) from the designs' own CadQuery
parts and solved with CalculiX 2.21 (`ccx`). v3 and v4 are still changing on #185 and their builds aren't committed,
so `export_design.py` builds their parts and placements from source first.

v3 keeps v2's frame, motor mount, shafts and carriage plate, and adds Sam's 2026-10-29 features plus a 4.0 kg acrylic
enclosure. v4 moves the augers outside the loop. Its frame is wider (posts at y ±180 instead of ±112) and taller (top
rails at z 755 instead of 721), and its loop and motor sit 40 mm higher. What each result means for the design is in
**[RESULTS.md](RESULTS.md)**. Every case's numbers are in [out/SUMMARY.md](out/SUMMARY.md) (generated) and
`out/<module>/<case>.json`, with a picture next to each.

## Pipeline

| file | what it does |
|---|---|
| `fem.py` | gmsh mesh of a list of parts. Parts that touch are fused, so a bolted joint is bonded. Writes the CalculiX deck (fixes, forces, pressures, cosine bearing loads, rigid patches for bolts, pins and hubs, gravity, springs; static, frequency or buckling step), runs `ccx`, reads `.frd`/`.dat`, renders |
| `materials.py` | materials and the allowable each is checked against. Printed PETG: the across-layer strength, 23 MPa. Sustained loads: a 1000 h creep modulus (1000 MPa) and an 8 MPa allowable |
| `loads.py` | every load in one table, with its source (the designs' simulations, datasheets, the STEP volumes) |
| `verify.py` | checks against hand solutions, below |
| `export_design.py` | builds a design's parts and placements from its source into `$FEA_WORK/designs/<design>/` |
| `cases/frame.py` | whole frames with the NEMA 34 on its wall, the motor close-ups, mass and centre of mass for tipping, and the v4 fix (variants `motorpost` and `motorpost2`: one or two 2020 posts screwed to the back plate beside the motor) |
| `cases/shafts.py` | corner shafts, the paternoster's idler stub axles, the printed tensioner block |
| `cases/carriage.py` | carriages (v3 inside the loop, v4 outside) at each orientation, hinge lugs and pins, plate latches, side tabs |
| `cases/station.py` | the station: kinematic dock (Hertz), electronics carriage seat and arms, guide cradle, clevis and P16 bracket, latch rail, rests, hold-downs (`station_geo_dump.py` dumps the station's frames and pins first) |
| `cases/gondola.py` | the paternoster's printed gondola (hanging, creep, a P16 stall through its hinge) and its shoulder-screw pivots |
| `report.py` | collects every case into `out/SUMMARY.md`, plus the tipping check, the motor screws' slip check, and the modes against the stepper's step rates |

### Checks against hand solutions (`verify.py`, rerun on this runner)

| check | CalculiX | hand | difference |
|---|---|---|---|
| cantilever, 20 mm steel bar, 100 N: tip deflection | 0.09765 mm | 0.09832 mm (Timoshenko) | -0.7 % |
| same bar: bending stress at mid-span | 7.47 MPa | 7.50 MPa | -0.4 % |
| same bar: first bending mode | 411.0 Hz | 412.2 Hz | -0.3 % |
| 1/4 in 6061 strip: 1 vs 3 elements through it | 0.7027 mm | 0.7063 mm | -0.5 % (so one element through the side plates is enough) |
| Euler buckling of a 6 mm rod | 805.1 N | 804.5 N | +0.1 % |
| 2020 extrusion (webbed section): second moment | 7486 mm^4 | 7200 mm^4 (catalogue) | +4 % |

This CalculiX 2.21 build returns wrong buckling factors on 4 OpenMP threads (0.98 N for the 805 N column), so every run
is single-threaded and cases run as separate processes. The CAD's 2020 profile has no webs, so its core and corners are
five separate bars that bend 3.4x too much. The frame models use an equivalent 20 x 20 bar with the webbed section's
bending stiffness, torsional stiffness and mass per length.

## Modelling choices that matter

- **Joints.** Bolted joints are bonded. A side plate joins its post only at its M5 screws: a 14 mm pad bridges a 0.3 mm
  gap, so the plate can lift off between screws ("pads"). The fully glued overlap ("bonded") is run as a stiff bound.
- **Motor.** The NEMA 34 is modelled as its envelope: 86 mm flange, 150 + 19 mm body, 14 mm shaft, 5.6 kg, bonded on
  its flange face. The vendor STEP is 200k nodes of detail that carries no load.
- **Enclosure.** The panels' mass (v3 4.0 kg, v4 5.1 kg) is smeared along the 2020 members. Their stiffness is left out,
  so the frames' sway modes come out a little low.
- **Loop.** Each 32T sprocket carries an eighth of the loop's mass, and the chain's tension pulls it into the loop. In
  the drive cases, the stator's torque reaction goes into the back plate, the drive chain pulls the two 15T sprockets
  together, and the bottom runs' tight side pulls B+ and B- together (a jam at B-).
- **Shafts.** The insert bearings are self-aligning, so the shafts are pin-supported. The keyway is not meshed; it enters
  the fatigue check through Peterson's factors. A shaft that turns under a fixed load sees fully reversed bending.
- **Peaks.** Each case's peak stress leaves out nodes within a few mm of point-like supports and load patches, where
  the stress is singular. The raw peak is in the JSON too.
- **Memory.** At most 3 `ccx` jobs run at once, each capped at 4.5 GB of address space (`CCX_SLOTS`, `CCX_MEM_GB`), so a
  model that is too big fails on its own. Frames are 174k-223k nodes and take 2.2 GB and 35 s per static solve.

## Running it

```bash
pip install cadquery gmsh pyvista scipy numpy imageio
sudo apt-get install calculix-ccx libegl1 libosmesa6 libgl1-mesa-dri   # ccx 2.21; EGL/OSMesa for off-screen renders
cd cad/fea
python verify.py
python export_design.py chain-carousel-v3 && python export_design.py chain-carousel-v4
python cases/frame.py            # or name cases: python cases/frame.py chain-carousel-v3_pads_jam
python cases/shafts.py
python cases/carriage.py
python cases/station.py
python cases/gondola.py
python report.py                 # out/SUMMARY.md
```

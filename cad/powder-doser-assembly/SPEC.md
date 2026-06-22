# Powder Doser — engineering specification (as implemented)

This document captures the engineering specification that drives the
parametric CAD package in this directory.  It is a condensed, build-oriented
restatement of the text-only "full assembly prompt" attached to
[issue #111](https://github.com/vertical-cloud-lab/powder-doser/issues/111),
organised the same way (§0–§9) so the code, the parameters in
[`params.py`](params.py), and this spec stay in lock-step.

Every dimension below is millimetres unless noted.  Where this package makes a
modelling choice that goes beyond a literal number in the prompt (for example
the exact three-layer hinge stack-up that makes the tilt sweep collision-free),
that choice is called out as **[impl]**.

## 0. What it is

A vertically-orientable, auger-fed powder dispenser that meters small,
repeatable doses of dry powder (salt, xanthan gum, …) out of a single nozzle.
An Archimedes screw inside a tube conveys powder along its helix so that
**dose ∝ revolutions** (meterable, and it keeps metering at any tilt). Every
3D-printed part is a separate, manifold, FDM-printable solid; an assembly shows
how the printed parts fit together with the off-the-shelf hardware.

Subsystems:

| Subsystem | Function |
|-----------|----------|
| Auger + nozzle | the metering element (pitch + v4 tip + 1/3-screw / 2/3-reservoir split) |
| Stepper + 16T pinion → 48T auger band (3:1) | the actuator (countable rotation, torque to convey packed powder) |
| Tap collar (coin ERM + solenoid) | anti-bridging — buzz + periodic hammer-tap, spin-floats but is rotationally arrested |
| Tilting plate + dual MG996R servos → 40T hinge gears | aiming — tilts horizontal→vertical-down, two servos share the load |
| NEMA 11 motor block | drives the stepper pinion |
| Split auger brackets | running-fit shaft supports along the tube |

## 1. Global datums

* `+Y` = auger long axis; dispense tip at `+Y`, motor end at `−Y`.
* `+Z` = up; mounting-plate top surface is the `Z = 0` datum.
* Auger bore centreline at `X = 0`, `Z = +29.25` (`AUGER_AXIS_Z`).

## 3. Auger (shared tube + internal screw)

* Tube OD 25.0, wall 2.0 → bore Ø21.0.  Lengths: 250 (full), 180, 90 (bench
  test, no gear band).
* Top loading cap 6.0 tall with four Ø? loading slots on a 6.5 bolt-circle and
  a central M3 self-tap pilot (Ø2.7).
* Bottom **v4 nozzle**: tapered tip, single axial exit hole Ø3.0, screw stops
  ~0.5 above the exit plane so it never extrudes through the hole.
* Internal Archimedes screw: shaft Ø8, single-start pitch 10.0, fin thickness
  2.0; fin inner edge overlaps the shaft 0.4, outer edge overlaps the bore wall
  0.2 (so there is no powder-bypass gap).
* **Storage variant:** screw occupies only the bottom 1/3 of the length; the
  top 2/3 is a smooth reservoir.
* **Threaded sealable variant + cap:** top 25.4 (1") of the tube carries a
  coarse printable thread (pitch 4.0, crest flush with the tube OD); the cap is
  the same thread grown by a 0.35 hand-fit clearance, with a 3.0 wall/top and a
  1.5 top chamfer. **[impl]** thread + cap are modelled the same way as
  `cad/auger-geared/` (linear-extruded tooth + radially-grown mating cap), so
  the fit is phase-independent.

## 4. Printed parts

### 4.1 Gears (20° pressure angle, 0.15 backlash)

| Gear | Teeth | Module | Pitch Ø | Tip Ø | Notes |
|------|------:|-------:|--------:|------:|-------|
| Auger drive band | 48 | 1.0 | 48.0 | 50.0 | annular — bore stays Ø21 open through the band |
| Stepper pinion | 16 | 1.0 | 16.0 | 18.0 | 3:1 onto the band, C = 32; Ø5 bore + hub + M3 setscrew |
| Servo pinion | 20 | 0.9083 | 18.2 | 20.2 | 2:1 onto the hinge gear, C = 27.25; MG996R 25T spline bore |
| Hinge gear | 40 | 0.9083 | 36.33 | 38.15 | one per side, on the outer mounting-plate hinge lobe |

The 48T band sits with its centre 1/3 of the length back from the dispense
end (83.33 from the `+Y` tip).

### 4.2 Mounting plate ("the table")

6.0-thick plate, ±54.1 wide, Y from −15 to 115, with an open U-notch
(32 wide, starting 35 back from the front edge) for the dispense tip. Carries
the two hinge lobes (see §4.4) and clearance slots **[impl]** so the table
never fouls the fixed baseplate hinge arm through the tilt sweep.

### 4.3 Baseplate (fixed forward tab)

6.0-thick, ±100 wide, Y 55–115, bottom at Z = −14, rear corners chamfered
25×45°. Four M5 clearance holes at X = ±80, Y = 68/105. Carries the middle
hinge arm and the servo posts/flanges.

### 4.4 Hinge

Axis at Z = 29.25, 10 forward of the baseplate front edge (Y = 125). Ø18 eyes,
M5 pin (Ø5.0 nominal, Ø5.4 clearance bores). **[impl]** Each side is a
three-layer sandwich centred at X = ±48: *inner plate lobe | (0.4) | middle
baseplate arm | (0.4) | outer plate lobe*; the outer lobe carries the 40T hinge
gear, the middle baseplate arm has a sloped front so the table clears it.

### 4.5 Servos (dual MG996R)

Body 40×20×36.8, 25T spline. Posts rise from the baseplate; an underside flange
rib (X = ±79) drops 40 below the baseplate with an M5 side-bolt 15 below.
**[impl]** post/flange X kept outboard of the table swept envelope so nothing
collides during tilt.

### 4.6 NEMA 11 motor block

Body 28×28, length 32, Ø5 shaft, Ø22 pilot. Mounted so the 16T pinion meshes
with the band at C = 32 and the motor body clears the auger OD (~5.4 gap).

### 4.7 Auger brackets + tap collar

* Split shaft-collar brackets: Ø(OD+0.5) running-fit bore, 2.0 saw slot, M3
  clamp holes at X = ±12.
* Tap collar: OD 33.5, depth 17, Ø25.5 running-fit bore, 2.0 clamp slot, a Ø10
  coin-ERM recess, a solenoid bushing boss (Ø6.9 / plunger bore Ø7.5) on its
  M3 pattern (18.2 × 16.0), and a hard-stop ear that keys into the mount so the
  collar spin-floats but is rotationally arrested.

## 5. Off-the-shelf envelopes (assembly only)

NEMA 11 stepper, two MG996R servos, coin ERM, and the tap solenoid
(Adafruit 412 / TAU0730TM, body 30×15.5×16, Ø6.9 bushing, Ø7.5 plunger).

## 6. Part-to-part interaction rules (verified by `interference_report()`)

1. Auger bore stays fully open (Ø21) through the gear band — **0 mm³**.
2. Pinion/band mesh with backlash only (no jam).
3. NEMA 11 body clears the auger OD (~5.4 radial gap).
4. Tap collar is a **running fit** on the tube (small radial clearance, no
   solid overlap).
5. Solenoid plunger is a **deliberate interference** — its tip reaches 3.0
   inside the auger OD so it actually taps the wall (overlap **> 0**).
6. Auger brackets are a running fit (no solid overlap).
7. Tilt clearance: the table never intersects the baseplate at 0°, 45°, or 90°.

`python3 build.py` prints all nine checks; the build only "passes" when every
one is satisfied.

## 7. Tolerances / fastener pilots

M3 clearance 3.4, M3 self-tap pilot 2.7, M3 setscrew pilot 2.5, M5 clearance
5.4, printed-thread hand fit 0.35, ~0.15 gear backlash, ~0.2 slip-fit on press
bores.

## 9. Outputs

Per part: STEP + STL + a rendered PNG preview. Plus a tilt-0 STEP/STL/PNG of
the full assembly and the §6 interference report. STL meshes and PNG previews
are committed; the large per-part STEP solids are reproducible with
`python3 build.py` (see [`.gitignore`](.gitignore)).

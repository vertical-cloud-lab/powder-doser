# Powder doser in text-to-cad (issue #172)

The lab's current powder doser (PR #170's full assembly, from the Fusion 360
files in #115/#97), rebuilt as code with
[text-to-cad](https://github.com/earthtojake/text-to-cad): every printed part
is a build123d model, the purchased parts are vendor or parametric models,
every screw and nut is a step.parts model, and the POWDER_DOSER_V2 PCB is
built from its Gerbers. The assemblies carry kinematics (tilt geared to both
servo pinions, auger geared to the stepper, solenoid plunger) and animation
clips. A second layout puts the **servos above the hinge**, so nothing hangs
below or in front of the nozzle. Both layouts are checked for interference,
nozzle-to-cup clearance and printability, and a DEM model simulates the
powder (tilt, rotation, tapping).

Toolchain: `cadgen[snapshot]==0.7.10` (text-to-cad's runtime) and
build123d 0.11.1 on Python 3.12, with the text-to-cad `cad`, `step-parts` and
`dfam-check` skills.

| Servos above (new) | Current (servos below) |
|---|---|
| ![servos above](renders/assembly/assembly_servos_above_iso.png) | ![current](renders/assembly/assembly_current_iso.png) |

| Assembly, step by step (servos above) | Tilt, turn, tap |
|---|---|
| ![assembly](renders/assembly/assembly_servos_above_assembly.gif) | ![motion](renders/assembly/assembly_servos_above_motion.gif) |

## Layout

| Path | What |
|---|---|
| `src/parts/` | Printed parts: baseplate (+ servos-above variant), mounting plate (+ variant), auger, auger cap, bracket, tap collar, tap-collar base, servo and stepper pinions |
| `src/purchased/` | MG996R servo, NEMA 11 (vendor STEP 11HS18-0674S), Adafruit 412 solenoid |
| `src/electronics/` | POWDER_DOSER_V2 PCB from the Gerbers, its modules, and the printed holder ([README](src/electronics/README.md)) |
| `src/lib/` | `frames.py` (world frame and every placement, ported from PR #170), `hardware_placements.py` + `fasteners.py` (step.parts screws and nuts in PR #170's seat frames), `doser.py` (the assembly tree, kinematics and animation clips), `assembly_steps.py` (build order and captions), `electronics_place.py` |
| `src/assembly_current.py`, `src/assembly_servos_above.py` | The two full assemblies → `STEP/`, `GLB/` |
| `scripts/render_clips.py` | Renders the clips with text-to-cad's own `cadgen step snapshot --animation … --video` and captions the assembly GIF |
| `checks/` | Fidelity, interference, electronics clearance, cap thread, nozzle-to-cup clearance, printability, PCB checks; results in `checks/results/` |
| `sim/` | DEM powder model of the auger ([README](sim/README.md)); figures in `renders/sim/` |
| `docs/onshape.md` | How this could work with Onshape and its REST API |

## Build

```bash
pip install "cadgen[snapshot]==0.7.10" rtree networkx lxml
python3 -m playwright install --with-deps chromium      # snapshots
sudo apt-get install -y ffmpeg                           # GIF/MP4 clips
cd cad/text-to-cad
export PYTHONPATH=src:src/parts:src/purchased:src/electronics
python3 src/assembly_servos_above.py                     # about 7 min on a 4-core runner
python3 src/assembly_current.py
python3 scripts/render_clips.py --variant above --clips motion assembly --fps 6
python3 checks/fetch_reference.py                        # PR #170's files, for the checks
(cd checks && PYTHONPATH=../src:. python3 interference.py --fasteners)
```

On a GitHub-hosted runner, keep an eye on memory. Each cadgen daemon worker
holds 0.5–2 GB, and fine STL exports of the helical auger spike well above
that. Two earlier CI sessions on this issue lost their runner ("The runner
has received a shutdown signal") while running jobs like these. Install
`earlyoom`, which kills the offending Python process instead of the runner,
and set `CADGEN_JOBS=2` to cap the daemon's parallelism.

## Fidelity of the recreation

`checks/fidelity.py` scores each recreated part against the file it
duplicates, in the same frame with no registration
(`checks/results/fidelity/`):

| Part | IoU | Volume error | Max surface deviation |
|---|---|---|---|
| Baseplate | 0.9996 | 0.00 % | 0.005 mm |
| Mounting plate | 0.9997 | 0.01 % | 0.012 mm |
| Bracket | 0.9996 | 0.00 % | 0.001 mm |
| Tap collar | 0.9995 | 0.00 % | 0.002 mm |
| Tap-collar base | 0.9997 | 0.00 % | < 0.001 mm |
| Servo pinion (14T) | 0.9996 | 0.05 % | 0.010 mm |
| Stepper pinion (20T) | 0.9996 | 0.04 % | 0.016 mm |
| Auger cap | (boolean failed on the threads) | 0.19 % | 0.011 mm |
| Auger | (not run: too heavy for the runner) | 0.013 %, identical bounding box | – |
| MG996R / Adafruit 412 | 0.9998 / 0.9991 | 0.00 % | – |
| NEMA 11 | 0.955 against PR #170's stand-in | 0.34 % | the recreation uses the real vendor STEP (28.2 mm square, rounded corners) |

Fasteners: 13 step.parts models against PR #170's stand-ins. Twelve score
IoU 0.83–0.999; the M5 × 45 hinge screw's boolean returned 0 (its volume is
14 % under: it is step.parts' M5 × 50 cut to 45). The step.parts `_simple`
screws draw the thread at the minor diameter, which accounts for most of the
difference.

## Servos above: what changes and what it buys

* **Baseplate** (`baseplate_servos_above.py`): the front arms, legs and
  servo posts go. The servos sit in open-top cradles on the hinge towers, and
  a slot between the towers clears the tap-collar hardware. The plate
  overhangs the board's front edge by 44.6 mm, and it prints flat with
  0.6 % of its surface needing support (the current baseplate needs 6.9 %).
* **Mounting plate** (`mounting_plate_servos_above.py`): the two 28T gears
  are turned 180° about the hinge, so the 14T pinions mesh them from above.
* **Build order** (`src/lib/assembly_steps.py`, the GIF above): the plate goes
  onto the towers first, then the servos drop in from above (their splines
  pass 8 mm over the gear tips), and then the pinions slide on from inside.

How close a cup can come to the outlet. A cup of diameter D, centred under
the outlet, is raised until its rim touches something
(`checks/nozzle_clearance.py`, gap in mm, limiting part in brackets):

| Layout, tilt | Ø20 | Ø40 | Ø58 | Ø85 | Ø120 |
|---|---|---|---|---|---|
| Current, 0° | 12.5 (auger) | 12.5 (auger) | 81.3 (board) | 81.3 (board) | 81.3 (board) |
| Current, 45° | 8.8 (auger) | 73.2 (board) | 73.2 (board) | 73.2 (board) | 73.2 (baseplate) |
| Current, board moved back, 45° | 8.8 (auger) | 35.0 (baseplate) | 35.0 (baseplate) | 35.0 (baseplate) | 73.2 (baseplate) |
| Servos above, 0° | 12.5 (auger) | 12.5 (auger) | 22.3 (mounting plate) | 43.2 (baseplate) | 43.2 (baseplate) |
| Servos above, 22.5° | 11.6 (auger) | 11.6 (auger) | 11.6 (auger) | 38.8 (baseplate) | 38.8 (baseplate) |
| **Servos above, 45°** | **8.8 (auger)** | **8.8 (auger)** | **8.8 (auger)** | 35.0 (baseplate) | 35.0 (baseplate) |

8.8 mm is the floor here: it is the auger tube's own end face
(12.5 mm × cos 45°). At 45° with the servos above, cups up to 58 mm across
reach it. With the current layout, any cup 40 mm or wider stops 73 mm below
the outlet, because the board and the baseplate's front arms are in the
way.

![nozzle clearance](renders/checks/nozzle_clearance_reference.png)

## Interference

Full write-up: [`checks/results/interference.md`](checks/results/interference.md).
In short:

* **Fixed:** the auger cap's thread was half a turn out of phase with the
  auger's as placed (546 mm³). `CAP_TURN_DEG = 180` seats it
  ([`checks/cap_thread.py`](checks/cap_thread.py)).
* **Fixed:** the first electronics pose put the PCB holder on the auger's
  centre line behind the doser, where the tube and the mounting plate cut
  through it. The holder now stands beside the doser on the +X side, turned
  90° with its components facing the doser
  ([`checks/electronics_clearance.py`](checks/electronics_clearance.py)).
* **Inherited from the lab's files (current layout only):** the
  baseplate's servo posts overlap each MG996R by 69 mm³, and at rest the
  M3 screw and nut under the tap-collar base hit the baseplate (4.7 and
  7.3 mm³). The servos-above baseplate has neither.
* **Vendor-model artefacts:** the NEMA 11 STEP's rigid lead stubs pierce the
  mounting plate and rear bracket. The real leads leave towards the plate, so
  route them away from it.
* Nothing else collides at 0, 15, 30 or 45° in either layout.

## Printability

`checks/printability.py` (text-to-cad's `dfam-check` approach: wall
thickness, overhang/support area, best orientation) on the STLs:
[`checks/results/printability.md`](checks/results/printability.md).
The baseplates, bracket, tap-collar base and PCB holder are clean watertight
single bodies with minimum walls of 1.7–4 mm. The tap collar's thinnest wall
is 0.74 mm. The auger's helical flight is 0.5 mm thick by design, which is
about one extrusion line on a 0.4 mm nozzle. The auger, auger cap and both
mounting plates export non-watertight or multi-body STLs (the helical sweeps,
and the gears as separate bodies), so their mesh wall minimums (0.002–0.14 mm)
are artefacts. A slicer repairs these meshes, but they should be unioned or
exported finer before anyone relies on their numbers.

## Powder simulation (DEM)

[`sim/`](sim/README.md) is a soft-sphere DEM of the auger's outlet section,
written for this issue in numba. The rotating tube, helical flight, core and
funnel are analytic signed-distance fields. Contacts are linear
spring–dashpot with Coulomb friction (μ = 0.6 particle–particle, 0.35
particle–PLA) and elastic–plastic rolling resistance (μ_r = 0.8). Those
values were calibrated so that a lifted-cylinder heap stands at **32.6°**
(the first, constant-torque rolling model only reached 20.6°). Tilt enters
as the gravity direction, rotation through the moving walls, and a solenoid
tap as a 4 ms, about 38 g acceleration pulse of the tube.

| Non-cohesive: tilt 35° → 1 rev → 4 taps → back | Cohesive (Bo = 3), same sequence |
|---|---|
| ![DEM](renders/sim/dem_sequence.gif) | ![DEM cohesive](renders/sim/dem_sequence_cohesive.gif) |

* **Dose per revolution:** 1st rev 98 / 238 / 279 mg at 0 / 22.5 / 45°,
  about 285 mg once running at 22.5–45°. That is about 320 mm³ of bulk
  powder per turn; multiply by your powder's bulk density. The dose arrives
  as one pulse per revolution. A horizontal auger delivers about 35 % less.
* **Leakage:** none. With the tube stopped at 45°, the flight pockets hold
  the powder, and taps alone release nothing.
* **Taps:** with free-flowing powder they only clean out the funnel (11, 5,
  1, 0 mg). With cohesive powder, one revolution released just 45 mg
  because powder bridged in the funnel, and then **the first tap released
  67 mg**, more than the whole revolution. So in this model, tapping is what
  makes a cohesive powder dispense.
* **Caveats:** coarse-grained 0.8–1.0 mm spheres (2067 of them), soft
  contacts, and an assumed 41 % flight fill. Powder counts as dispensed at a
  capture plane where the gap is still about 4 diameters, because the real
  1.1 mm outlet annulus would jam spheres this size. Cohesion is an assumed
  Bond number, not a measured one, and each case was run once. Compare the
  trends and the bulk volume per revolution, not absolute milligrams.

## Onshape

[`docs/onshape.md`](docs/onshape.md) covers the options. The most valuable
next step is pushing this project's kinematics sidecar into the existing
Onshape assembly as real mates and gear relations (the live document has
none). The return path, Onshape version → STEP → these checks in CI, comes
second.

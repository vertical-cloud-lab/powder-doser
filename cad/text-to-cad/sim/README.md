# DEM powder-flow simulation of the auger outlet (issue #172)

A small soft-sphere discrete element model (DEM) of powder in the outlet end of the
rotating auger tube. It simulates the three actuators of the doser: **tilt** (servos,
0 to 45 deg outlet-down), **rotation** (stepper, 20T:44T onto the tube) and **tapping**
(Adafruit 412 solenoid on the tap collar).

![sequence](../renders/sim/dem_sequence.gif)

## Files

| File | What it is |
|---|---|
| `dem.py` | numba DEM engine: contact laws, cell list, analytic auger walls, integrator |
| `scenarios.py` | parameters + the scenarios below (one per process) |
| `render.py` | GIF + PNG figures from the results |
| `results/*.json` | per-scenario numbers, parameters and time logs (cup mass, tilt, tube angle, overlap, KE) |
| `../renders/sim/dem_sequence.gif` | tilt, then 1 rev, then 4 taps, then tilt back (side section, lab frame) |
| `../renders/sim/dem_sequence_still.png` | one frame of the GIF (mid-rotation) |
| `../renders/sim/dem_sequence_mass.png` | sequence: dispensed mass, tilt and tube revolutions vs time |
| `../renders/sim/dem_dose_vs_tilt.png` | cumulative dose vs revolutions and dose per rev at 0 / 22.5 / 45 deg |
| `../renders/sim/dem_tap_response.png` | 45 deg hold + 4 taps without rotation: bed kinetic energy (sampled every 5 ms, so the spike heights are only indicative) and mass per tap, compared with the taps after 1 rev in the sequence |
| `../renders/sim/dem_repose.png` | heap profile of the angle-of-repose check |

## How to run

```bash
python3 -m venv /tmp/simenv && /tmp/simenv/bin/pip install -q numba numpy scipy matplotlib pillow
export NUMBA_NUM_THREADS=3
cd cad/text-to-cad/sim
/tmp/simenv/bin/python scenarios.py repose      # angle-of-repose check          (<1 min)
/tmp/simenv/bin/python scenarios.py settle      # seed + settle the bed (first!)  (<1 min)
/tmp/simenv/bin/python scenarios.py dose 0      # also 22.5 and 45                (2 min each)
/tmp/simenv/bin/python scenarios.py leaktap     # 45 deg, no rotation, 4 taps     (1.5 min)
/tmp/simenv/bin/python scenarios.py sequence 35 # GIF run                         (2.5 min)
/tmp/simenv/bin/python render.py                # GIF + PNGs -> ../renders/sim/
```

Wall-clock times are for 3 numba threads on a shared 4-core GitHub runner. Peak memory
is a few hundred MB. Frame dumps and the settled bed go to `/tmp/simframes` (not committed).

## Model

**Contacts** (each pair i-j, normal n from j to i, overlap delta):

* normal: `F_n = max(0, k_n*delta - g_n*v_n)`, `g_n = 2*zeta*sqrt(m_eff*k_n)`, with zeta
  set from the restitution e (`zeta = -ln e / sqrt(pi^2 + ln^2 e)`);
* tangential (Cundall-Strack): spring `xi` accumulated from the tangential slip
  velocity and rotated into the current tangent plane, `F_t = -k_t*xi - g_t*v_t`, capped
  at `mu*F_n` (the spring is reset to the Coulomb limit when sliding);
* rolling resistance (constant-torque "type A"): `M_r = -mu_r*R_eff*F_n*w_rel/|w_rel|`,
  stands in for particle shape and weak cohesion. The torque is capped (cap shared over
  the particle's contacts) so it can stop but never reverse a relative spin in one step.
* walls use the same laws with `m_eff = m`, `R_eff = r` and the wall velocity
  `v_w = Omega z x r` of the rotating tube.

Semi-implicit Euler integration, counting-sort cell list (cell = largest diameter),
every particle sums all of its own contacts (parallel loop, per-particle contact
history in ping-pong buffers).

**Auger geometry** (from `src/parts/auger.py`), as analytic signed distances in the
non-rotating tube frame (z = tube axis, outlet face z = 0, y = up when horizontal):
bore r = 10.5 mm; outlet funnel cone from r = 10.5 at z = 12 to r = 1.5 at z = 0 (with the
bore it forms the exact concave corner); core r = 4 mm with its conical tip (r = 0.4 at
z = 0); right-handed helicoid flight, 0.5 mm thick, pitch 10.416 mm, starting on +X at
z = 0. Distance to the flight: `(|dz_wrapped| - t/2) * 2*pi*r / sqrt((2*pi*r)^2 + p^2)`
with `dz = z - t/2 - p*(phi - theta)/2pi`, where theta is the tube angle. Each wall
primitive is its own contact, so particles in the flight/bore corner touch both.
Turning the tube anticlockwise seen from the cap (Omega > 0 about +z) carries the
powder to the outlet, which the runs confirm.

**Actuators** (all in the tube frame):

* tilt beta: gravity `g = -9.81*(0, cos beta, sin beta)` m/s^2; cosine ramps of 0.25 to
  0.35 s. The hinge's centripetal/Euler terms (tilt rates below 2.5 rad/s) are neglected.
  The GIF rotates the tube about the outlet only for display.
* rotation: tube angle theta(t) with 0.05 s speed ramps.
* tap: the solenoid strikes the top of the tube through the vertical hole in the tap
  collar. Assumed tube motion: an out-and-back bump `u = -A sin^2(pi t/T) y`,
  A = 0.3 mm, T = 4 ms (peak acceleration 37.7 g, peak tube speed 0.24 m/s, ends at
  rest). Particles feel the pseudo-acceleration `-u''(t)`. These values are an
  assumption; they have not been measured.

## Parameters

| Quantity | Value | Why |
|---|---|---|
| sphere diameter | 0.8 to 1.0 mm uniform (mean 0.9) | coarse-grained; ±11 % polydispersity stops crystallisation |
| solid density | 1500 kg/m^3 | organic/salt-like lab powder; bulk density about 900 kg/m^3 at 0.6 packing |
| k_n / k_t | 25 / 7.14 N/m (k_t = 2/7 k_n) | softened. Overlap 0.5 % d at rest, 2.5 to 4.5 % d while rotating, up to 7.5 % d at the tap peak |
| restitution e | 0.3 (zeta = 0.358) | dissipative powder impacts |
| mu particle-particle | 0.5 | typical for dry powders |
| mu particle-wall (PLA) | 0.35 | smoother printed wall |
| mu_r (pp and pw) | 0.25 | raised from 0.1 after the repose check; still gives only 21 deg |
| time step | 1.5e-5 s | contact time of the lightest pair 3.0e-4 s, so t_c/20 |
| tube speed | 60 rpm (stepper 132 rpm) | sped up to save compute; Froude w^2 R/g = 0.042, so still quasi-static |
| simulated section | z = 6 to 38.0 mm (funnel + 2.5 flight turns) | frictionless lid at the top; no feed from the reservoir |
| initial fill | all free space below y = -2 mm at 0 deg (41 % of the annulus), z >= 12.5 mm | partly full flights; settled 0.3 s under gravity |
| particle count | 2067 (1188 mg) | |
| capture plane | z = 6 mm, annular gap 3.8 mm (4.2 mean diameters) | see the caveats |

## Results

| Scenario | Result |
|---|---|
| angle of repose (fixed-base heap, 694 spheres on a rough 8 mm-radius disc, lifted cylinder) | **20.6 deg** (18.2 deg with mu_r = 0.1) |
| dose, 0 deg tilt, 1.5 rev | 1st rev **134 mg**, rev 0.5 to 1.5 **280 mg**, 333 mg in total |
| dose, 22.5 deg | 1st rev **237 mg**, rev 0.5 to 1.5 **321 mg**, 497 mg in total |
| dose, 45 deg | 1st rev **281 mg**, rev 0.5 to 1.5 **315 mg**, 610 mg in total |
| leakage: 45 deg, no rotation, 0.4 s hold | **0 mg** (no particle crossed the capture plane) |
| taps at 45 deg, no rotation (4 taps) | **0, 0, 0, 0 mg** |
| sequence: 0 to 35 deg, 1 rev, 4 taps, back to 0 deg | tilt 0 mg; 1 rev **272 mg**; taps **8.3, 3.4, 0, 0 mg**; tilt back 0 mg; total 283 mg |

"Total" includes a short avalanche that continues after the tube stops (the vertical
steps at the end of the curves in `dem_dose_vs_tilt.png`). Dose arrives in **one pulse
per revolution**: the single-start flight pushes the outlet-side pocket into the funnel
once per turn. The quarter-turn values are in the JSON files.

Observations:

* More tilt means a larger and earlier first-revolution dose, because powder is already
  sitting against the outlet-side flight. In the window from rev 0.5 to 1.5 the tilt
  effect is much smaller (280 to 321 mg), i.e. once running the auger behaves like a
  positive-displacement conveyor and tilt mainly sets how much the flights hold.
* With the tube stopped, the flights hold the powder even at 45 deg. Each flight turn is a
  closed helical pocket whose lowest point is at the bottom of the tube, and the funnel
  floor is inclined only 8 deg at 45 deg tilt, less than the wall friction angle (19 deg).
  Taps without rotation shift the bed but release nothing.
* Taps right after a rotation knock loose the residue left in the funnel (8 mg, then
  3 mg, then nothing). Tapping is a clean-up step, not a metering step, in this model.
* Bulk volume per revolution (rev 0.5 to 1.5) is 310 to 360 mm^3 at 0.6 packing.

## Caveats: what the numbers mean and what they don't

* **Coarse graining.** Spheres of 0.9 mm stand in for 10 to 100 µm powder with no
  cohesion, van der Waals or humidity. Compare doses as **bulk volume per revolution**
  (multiply by your powder's bulk density), not as particle counts or absolute mg. The
  repose angle of 21 deg is lower than for most lab powders (30 to 45 deg), so this model
  powder is more free-flowing than most real ones. The 0 mg leakage is conservative,
  since a more cohesive powder leaks even less. Arch-breaking by taps, which matters for
  cohesive powders, is not represented.
* **Outlet.** The real 1.1 mm-wide outlet annulus would jam 0.9 mm spheres, which is
  unphysical. "Dispensed" therefore means "crossed z = 6 mm in the funnel", where the
  gap is still 4.2 diameters. Arching or rat-holing at the true outlet cannot be
  predicted here.
* **Finite section.** The section has a lid at z = 38 mm and no reservoir feed, so the
  doses hold for the assumed 41 % fill and the first 1.5 revolutions. Dose per rev
  scales with how full the flights are, which in practice depends on the reservoir and
  on tilt history.
* **Soft contacts.** k_n is about 1000 times softer than real particles. Quasi-static
  flow is unaffected, but stress waves from a tap travel slowly, so a tap acts like a
  body-force jolt on the whole bed. The tap amplitude and duration are assumed.
* **Statistics.** One initial packing and one run per case, so there are no error bars.
  The one-pulse-per-rev discharge makes partial-revolution numbers depend on phase.
* The tube is driven at 60 rpm (Fr = 0.04) rather than the real stepper speed. At this
  Froude number, flow per revolution should not depend on speed.

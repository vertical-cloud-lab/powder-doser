# DEM powder-flow simulation of the auger outlet (issue #172)

A small soft-sphere discrete element model (DEM) of powder in the outlet end of the
rotating auger tube. It simulates the three actuators of the doser: **tilt** (servos,
0 to 45 deg outlet-down), **rotation** (stepper, 20T:44T onto the tube) and **tapping**
(Adafruit 412 solenoid on the tap collar).

![sequence](../renders/sim/dem_sequence.gif)

Cohesive variant (Bo = 3): `../renders/sim/dem_sequence_cohesive.gif`.

## Files

| File | What it is |
|---|---|
| `dem.py` | numba DEM engine: contact laws, cell list, analytic auger walls, integrator |
| `scenarios.py` | parameters + the scenarios below (one per process) |
| `render.py` | GIF + PNG figures from the results |
| `results/*.json` | v2 (calibrated) per-scenario numbers, parameters and time logs (cup mass, tilt, tube angle, overlap, KE); `*_bo3` = cohesive; `repose_mur*_mu*.json` = calibration points |
| `results/v1/` | the first, uncalibrated run (type-A rolling, mu_r = 0.25, mu = 0.5) for comparison |
| `../renders/sim/dem_sequence_cohesive.gif` | same sequence with cohesion, Bo = 3 |
| `../renders/sim/dem_sequence.gif` | tilt, then 1 rev, then 4 taps, then tilt back (side section, lab frame) |
| `../renders/sim/dem_sequence_still.png` | one frame of the GIF (mid-rotation) |
| `../renders/sim/dem_sequence_mass.png` | sequence: dispensed mass, tilt and tube revolutions vs time |
| `../renders/sim/dem_dose_vs_tilt.png` | cumulative dose vs revolutions and dose per rev at 0 / 22.5 / 45 deg |
| `../renders/sim/dem_tap_response.png` | 45 deg hold + 4 taps without rotation: bed kinetic energy (sampled every 5 ms, so the spike heights are only indicative) and mass per tap, compared with the taps after 1 rev in the sequence |
| `../renders/sim/dem_repose.png` | heap profile of the calibrated angle-of-repose test |

## How to run

```bash
python3 -m venv /tmp/simenv && /tmp/simenv/bin/pip install -q numba numpy scipy matplotlib pillow
export NUMBA_NUM_THREADS=3
cd cad/text-to-cad/sim
export SIM_MUPP=0.6 SIM_MUR=0.8                       # calibrated values (also the defaults below)
/tmp/simenv/bin/python scenarios.py repose            # angle-of-repose test        (1.5 min)
/tmp/simenv/bin/python scenarios.py settle            # seed + settle the bed first (0.5 min)
/tmp/simenv/bin/python scenarios.py dose 45 1.25      # also 0 and 22.5             (2 min each)
/tmp/simenv/bin/python scenarios.py leaktap           # 45 deg, no rotation, 4 taps (1.5 min)
/tmp/simenv/bin/python scenarios.py sequence 35       # GIF run                     (3 min)
SIM_BOND=3 /tmp/simenv/bin/python scenarios.py settle        # cohesive bed
SIM_BOND=3 /tmp/simenv/bin/python scenarios.py sequence 35   # cohesive GIF run
/tmp/simenv/bin/python render.py                      # GIFs + PNGs -> ../renders/sim/
```

Wall-clock times are for 2 to 3 numba threads on a shared 4-core GitHub runner. Peak memory
is a few hundred MB. Frame dumps and the settled bed go to `/tmp/simframes` (not committed).

## Model

**Contacts** (each pair i-j, normal n from j to i, overlap delta):

* normal: `F_n = max(0, k_n*delta - g_n*v_n)`, `g_n = 2*zeta*sqrt(m_eff*k_n)`, with zeta
  set from the restitution e (`zeta = -ln e / sqrt(pi^2 + ln^2 e)`);
* tangential (Cundall-Strack): spring `xi` accumulated from the tangential slip
  velocity and rotated into the current tangent plane, `F_t = -k_t*xi - g_t*v_t`, capped
  at `mu*F_n` (the spring is reset to the Coulomb limit when sliding);
* rolling resistance, EPSD (Ai et al. 2011 "type C"): a rolling spring
  `M_k += -k_r * w_rel,t * dt` with `k_r = 2.25*k_n*mu_r^2*R*^2`, capped at `mu_r*R*·F_n`,
  plus viscous damping `-C_r*w_rel,t` with `C_r = 2*eta_r*sqrt(I_r*k_r)` (eta_r = 0.3) while
  below the cap. It stands in for particle shape. v1 used a constant-torque "type A"
  model, which holds a static heap poorly (see the calibration table).
* optional cohesion (`SIM_BOND`): a constant pull-off force `F_coh = Bo*m_mean*g` while in
  contact or within a gap of 0.05 d, to particles and to the tube walls (not the
  artificial lid). The friction and rolling limits use `F_rep + F_coh`. This is a
  **coarse-grained cohesion assumption**: Bo = 3 for 0.9 mm spheres stands in for the
  much larger Bond numbers of real fine powders. It is not a calibrated van der Waals or
  liquid-bridge model.
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
| k_n / k_t | 25 / 7.14 N/m (k_t = 2/7 k_n) | softened. Overlap 0.5 % d at rest, 1.4 to 5 % d while rotating, up to 7 % d at the tap peak |
| restitution e | 0.3 (zeta = 0.358) | dissipative powder impacts |
| mu particle-particle | 0.6 | calibrated (with mu_r) to a 32.6 deg repose angle |
| mu particle-wall (PLA) | 0.35 | smoother printed wall |
| mu_r (pp and pw), EPSD | 0.8, damping ratio eta_r = 0.3 | calibrated, see below; large because spheres stand in for angular grains |
| cohesion (variant only) | Bo = 3 (F_coh = 1.7e-5 N), range 0.05 d | coarse-grained assumption, see Model |
| time step | 1.5e-5 s | contact time of the lightest pair 3.0e-4 s, so t_c/20 |
| tube speed | 60 rpm (stepper 132 rpm) | sped up to save compute; Froude w^2 R/g = 0.042, so still quasi-static |
| simulated section | z = 6 to 38.0 mm (funnel + 2.5 flight turns) | frictionless lid at the top; no feed from the reservoir |
| initial fill | all free space below y = -2 mm at 0 deg (41 % of the annulus), z >= 12.5 mm | partly full flights; settled 0.3 s under gravity |
| particle count | 2067 (1188 mg) | |
| capture plane | z = 6 mm, annular gap 3.8 mm (4.2 mean diameters) | see the caveats |

## Angle-of-repose calibration

Lifted-cylinder test: a column of 3035 spheres (radius 7 mm, 27 mm high) in a frictionless
cylinder lifted at 50 mm/s, on a 17 mm-radius base of 1113 glued (fixed) spheres. The
flank slope is fitted to the 90th-percentile surface height in 1 mm radial bins between
25 % and 75 % of the heap height.

| mu (pp) | mu_r (EPSD) | angle | heap height |
|---|---|---|---|
| 0.5 | 0.3 | 27.7 deg | 7.0 d (smaller 20 mm column) |
| 0.5 | 0.5 | 28.1 deg | 8.3 d |
| 0.5 | 0.8 | 31.2 deg | 8.7 d |
| **0.6** | **0.8** | **32.6 deg** (used) | 8.8 d |
| v1: 0.5 | 0.25 type A, small heap on 8 mm disc | 20.6 deg | 4.6 d |

With mu = 0.5 the angle saturates near 31 deg because sliding then limits the flank, so
mu was raised to 0.6. The heaps reached 8.8 d, just short of the 10 d target. A larger
heap did not fit the time budget.

## Results (v2, calibrated: mu = 0.6, mu_r = 0.8 EPSD)

| Scenario | v2 calibrated | v1 uncalibrated |
|---|---|---|
| dose, 0 deg: 1st rev / one rev in steady running | **98 / 184 mg** | 134 / 280 mg |
| dose, 22.5 deg | **238 / 283 mg** | 237 / 321 mg |
| dose, 45 deg | **279 / 287 mg** | 281 / 315 mg |
| leakage, 45 deg, no rotation, 0.4 s | **0 mg** | 0 mg |
| 4 taps, 45 deg, no rotation | **0, 0, 0, 0 mg** | 0, 0, 0, 0 mg |
| sequence 35 deg: 1 rev | **266 mg** | 272 mg |
| sequence 35 deg: taps 1 to 4 | **11.1, 5.3, 0.6, 0 mg** | 8.3, 3.4, 0, 0 mg |
| sequence, cohesive Bo = 3: 1 rev | **45 mg** | n/a |
| sequence, cohesive Bo = 3: taps 1 to 4 | **66.7, 7.4, 6.7, 0.5 mg** | n/a |
| tilt back (both) | 0 mg | 0 mg |

The steady-running window is rev 0.25 to 1.25 in v2 (1.25 rev runs) and rev 0.5 to 1.5
in v1 (1.5 rev runs).

Observations:

* Dose arrives in **one pulse per revolution**: the single-start flight pushes the
  outlet-side pocket into the funnel once per turn.
* Tilt mainly matters for the first revolution and at 0 deg. With the calibrated, less
  mobile powder, the horizontal auger delivers about 35 % less per revolution than at
  22.5 or 45 deg, where steady running gives about 285 mg per rev. That is 320 mm^3 of
  bulk powder at 0.6 packing; scale by your powder's bulk density.
* With the tube stopped, the flights hold the powder even at 45 deg. Each flight turn is a
  closed helical pocket whose lowest point is at the bottom of the tube, and the funnel
  floor slopes only 8 deg at 45 deg tilt. Taps shake the bed but release nothing.
* Non-cohesive powder: taps after a rotation knock loose 11 mg, then 5 mg, then
  nothing. They clean out the funnel; they don't meter.
* **Cohesive powder (Bo = 3): taps matter.** One revolution released only 45 mg (versus
  266 mg non-cohesive), because powder bridged and stayed held up in the funnel and on
  the flight. The **first tap dislodged 67 mg**, more than the whole revolution, and
  taps 2 to 4 gave 7, 7 and 0.5 mg. 126 mg in total versus 283 mg non-cohesive; the rest
  stays stuck in the funnel and flights. In this model, tapping is what makes a cohesive
  powder dispense after a rotation.

## Caveats: what the numbers mean and what they don't

* **Coarse graining.** Spheres of 0.9 mm stand in for 10 to 100 µm powder with no
  cohesion, van der Waals or humidity. Compare doses as **bulk volume per revolution**
  (multiply by your powder's bulk density), not as particle counts or absolute mg. The
  repose angle was calibrated to 32.6 deg, but a sphere model matched on one bulk test
  does not reproduce every flow regime. The cohesive variant (Bo = 3) is one illustrative
  setting, not calibrated to a powder.
* **Outlet.** The real 1.1 mm-wide outlet annulus would jam 0.9 mm spheres, which is
  unphysical. "Dispensed" therefore means "crossed z = 6 mm in the funnel", where the
  gap is still 4.2 diameters. Arching or rat-holing at the true outlet cannot be
  predicted here.
* **Finite section.** The section has a lid at z = 38 mm and no reservoir feed, so the
  doses hold for the assumed 41 % fill and the first 1.25 to 1.5 revolutions. Dose per rev
  scales with how full the flights are, which in practice depends on the reservoir and
  on tilt history.
* **Soft contacts.** k_n is about 1000 times softer than real particles. Quasi-static
  flow is unaffected, but stress waves from a tap travel slowly, so a tap acts like a
  body-force jolt on the whole bed. The tap amplitude and duration are assumed.
* **Statistics.** One initial packing and one run per case, so there are no error bars.
  The one-pulse-per-rev discharge makes partial-revolution numbers depend on phase.
* The tube is driven at 60 rpm (Fr = 0.04) rather than the real stepper speed. At this
  Froude number, flow per revolution should not depend on speed.

# Paternoster carousel: MuJoCo dynamics simulation

A physics model of the paternoster multi-doser carousel (`../params.py`, `../kinematics.py`):
12 gondolas hang from SA-1 pivots on two #35 chains, swing freely under gravity, and bump into
each other or the shafts if they swing too far. The model checks the motion profiles, the
corners, the speed limit, and the station (dock, tilt to 90 deg, solenoid taps, auger turning).
It also proposes and tests fixes.

The model files in this folder are `model.py`, `carousel_sim.py`, `plots.py` and `render.py`. Everything else here (`AUGER-SIM.md`, `corotation.py`, `out/auger/`) belongs to a separate auger study.

## How to rerun

```bash
cd cad/paternoster/sim
python carousel_sim.py                    # every run below, plots + out/results.json (1-2 min)
MUJOCO_GL=glfw xvfb-run -a -s "-screen 0 1920x1080x24" python render.py lap station   # videos (a few min)
MUJOCO_GL=glfw xvfb-run -a -s "-screen 0 1920x1080x24" python render.py fastlap       # optional 10 s lap video
```

Needs mujoco 3.16, numpy, scipy, matplotlib, imageio(+ffmpeg) and Pillow. Rendering only works
headless through `glfw` under `xvfb-run` (EGL and OSMesa are not available on the runner).
The first run builds `out/pivot_table.npz` from `kinematics.pivots` (about 3 s).

## Model

| item | value / treatment |
|---|---|
| chain | Two chains, driven kinematically from `kinematics.pivots(shift)`, used directly. The pivot table is built for shift in [0, 10) links at 0.002-link steps (3 s; cached in `out/pivot_table.npz`, rebuilt automatically whenever `kinematics.py` or `params.py` changes). Module k at shift s sits where module 0 sits at s + 10k. |
| pivot drive | Each gondola has a slide-y, a slide-z and a hinge-x joint at the pivot axis. A stiff servo drives each slide (2e5 N/m, 550 N*s/m, with velocity and gravity feed-forward), which acts as a rigid, tensioned chain. The servo forces are the chain-to-gondola forces. The front and back pivots share (y, z), so one hinge on the common x axis models both. |
| swing | Free hinge about x through the pivot: gravity, inertia, contacts, joint damping c, and Coulomb friction (`frictionloss` = mu * m * g * r, r = 2 mm) |
| gondola (PETG) | Two end plates of 0.035 kg each (62 x 57 mm, x 5.9-11.9 and mirrored) and a 5 mm floor/rails at 0.05 kg: 0.12 kg in total |
| module | Mounting plate 0.07 kg, brackets 0.03 kg, and auger + powder 0.16 kg (0.12-0.20 kg tested). Module COM is at HINGE_X + 89.7 mm, 5 mm below the hinge axis. |
| loaded gondola | 0.38 kg. COM is 24.0 mm below the pivot and 143.5 mm from the front chain, so the front chain carries 56 %. I about the pivot axis = 351 kg*mm^2 (computed by MuJoCo from the geoms). |
| collisions | End plates and floors (boxes) collide with each other and with the bottom through-shafts (dia 15.875 at y = +-95.25, z = 420). The top stubs and sprockets do not reach the gondola's x range [5.9, 319.1], so they are visual only. |
| clearance metric | Exact signed distance (SAT plus vertex-edge) between the swung 62 x 57 mm envelopes of every neighbour pair, logged every 5 ms. Gondola-to-shaft clearance is measured the same way. |
| drive torque | tau = sum_k F_k . dP_k/ds / (2 pi/32) + J_drive * alpha (virtual work of the pivot forces). J_drive = 5.2e-3 kg*m^2: two chains (0.75 kg) at R, eight 32T sprockets, and the NEMA 34 rotor. Chain and bearing friction are not included. The rigid chain turns every chordal kink into a short force spike, so the peak is reported raw and as a 25 ms moving average (closer to what a real, slightly elastic chain passes to the motor). |
| chain tension | Tension step across the drive sprocket per chain = tau / (2R). The rise along a strand is the sum of the tangential pivot forces (front-chain share). |
| integrator | MuJoCo 3.16, `implicitfast`, dt = 0.5 ms, elliptic cones |
| station rig | Current CAD: carriage stub pins at Sam's (32, -33.1) mm from the hinge (docked); base clevis at hinge + (32, -310.5) mm. Actuonix P16-150-22-12-P + 60 mm U-yoke: 257.4 mm retracted, 150 mm stroke, 50 N limit, run at 40 mm/s (46 mm/s no-load); DOCK_EXT = 20 mm. Modelled as clevis (hinge y, plus a 150 N*m/rad roll spring for clevis play/compliance) -> slide (position servo 3e4 N/m) -> stub-pin axis (hinge y) -> carriage 0.285 kg (with the dock magnet). The carriage docks to the mounting plate with a weld (soft for 0.25 s while the cones seat, then rigid). The module hinges on the gondola about y at (HINGE_X, HINGE_Z) and rests on a stop at 0 deg. The auger turns on its own joint: velocity servo, 0.18 N*m limit (NEMA 11 x 44/20), 0.03 N*m powder drag. Taps are 3 N for 10 ms at the collar (20 mm from the outlet): four sideways (y), then four normal to the plate. |
| chain at the station | Either rigid (the reference), or compliant: each pivot hangs from a tab spring (2 N/mm as specified, 50 N/mm as a stiffer check) in series with its chain's bottom-run span (4T/L = 840 N/m per chain at an assumed 40 N tension, massless). The UHMW-PE hold-down strip is a rigid one-sided stop on the chain, 0.5 mm above the link plates' top edge. The station gondola gets an extra pitch joint so that its front and back pivots rise separately. |

### `kinematics.py`: the bug and the fix

The first run of this study found that `pin_positions()` jumped by up to 0.9 mm whenever frac(shift)
passed 0, and `pivots()` by up to 1.0 mm. The station pivot jumped 0.47 mm between shift 9.0 and
9.0000001. The cause: a free span's end pin switched at the seat angle, but the pin that had just left
was not on the new chord. That run worked around the jumps by smoothing the pivot table over one link.

`kinematics.py` now uses the tooth phase g in [-1/2, 1/2): a span's end pins sit at the departure and
arrival angles + g*DELTA, and the end pin changes over at g = +1/2, where nothing jumps. The model now
calls `kinematics.pivots()` directly with no smoothing. The largest pivot move per 0.002-link table step
is 0.023 mm. The path still has small kinks (true chordal action), which the rigid-chain servo turns
into short force spikes; that is why the drive torque below is given both raw and 25 ms averaged.

All numbers below use the fixed kinematics. "Old" values are from the first run with the smoothed table.

## Results

### Pendulum (one loaded gondola)

| module | mass (kg) | COM below pivot (mm) | I_pivot (kg*mm^2) | f (Hz) | period (s) |
|---|---|---|---|---|---|
| light (auger 0.12 kg) | 0.34 | 24.96 | 337 | 2.50 | 0.400 |
| **nominal (0.16 kg)** | **0.38** | **24.01** | **351** | **2.54** | **0.393** |
| heavy (0.20 kg) | 0.42 | 23.25 | 365 | 2.58 | 0.388 |

A free-decay run gives a period of 0.3937 s, which matches.

### Pivot damping: release from 5 deg with the chain stopped (`free_decay.png`)

| viscous c (N*m*s/rad) | pivot friction mu (r = 2 mm) | time to stay < 0.5 deg (s) |
|---|---|---|
| 0 | 0 | > 8 (undamped) |
| 1e-4 | 0 | > 8 (zeta = 0.009) |
| 1e-3 | 0 | 1.60 (zeta = 0.09) |
| 0 | 0.1 | 0.90 |
| 1e-4 | 0.1 | 0.90 |
| 1e-3 | 0.1 | 0.51 |

The oil film in a 4 mm bronze sleeve gives c of about 2*pi*mu_oil*r^3*L/h, roughly 3e-6 N*m*s/rad for
both pivots: negligible. I use c = 1e-4 as the nominal value; runs marked "mu 0.1" add the bronze
sleeve's Coulomb friction.

**Coulomb friction is not negligible.** With mu = 0.1 at r = 2 mm the friction torque is 0.75 mN*m,
against a restoring stiffness m*g*d = 0.0895 N*m/rad. That gives a dead band of +-0.48 deg, and the
amplitude falls by about 1.9 deg every cycle. Pivot friction is the main damping in this machine. It
is helpful, but it also means a gondola can come to rest up to about 0.5 deg off vertical, which is
0.3 mm at the mounting plate and well inside the cones' capture range.

### Single indexes (3 indexes from home, 2 s dwell; the station gondola is the one at u = 10)

<!-- T:index -->
| run | profile | move (s) | pivot friction | peak chain speed (mm/s) | max swing anywhere (deg) | station residual (deg) | residual 0.5 s after stop (deg) | settle to < 0.5 deg (s) | min neighbour gap (mm) | min shaft gap (mm) | drive torque peak raw / 25 ms avg (N*m) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `index_trap_1.0s` | trapezoid, t_acc = T/3 | 1.0 | none | 143 | 7.03 | 3.47 | 3.22 | > dwell | 9.8 | 17.7 | 0.41 / 0.26 |
| `index_scurve_1.0s` | S-curve | 1.0 | none | 143 | 11.75 | 9.65 | 8.89 | > dwell | 9.7 | 16.1 | 1.47 / 0.45 |
| `index_zv_1.0s` | S-curve + ZV | 1.0 | none | 178 | 10.91 | 2.31 | 2.13 | > dwell | 9.6 | 17.5 | 0.55 / 0.32 |
| `index_trap_1.5s` | trapezoid, t_acc = T/3 | 1.5 | none | 95 | 5.93 | 3.54 | 3.26 | > dwell | 10.5 | 17.4 | 0.22 / 0.14 |
| `index_scurve_1.5s` | S-curve | 1.5 | none | 95 | 4.80 | 3.03 | 2.79 | > dwell | 10.5 | 17.7 | 0.85 / 0.22 |
| `index_zv_1.5s` | S-curve + ZV | 1.5 | none | 110 | 3.97 | 0.97 | 0.90 | > dwell | 10.6 | 17.7 | 0.26 / 0.18 |
| `index_trap_1.0s_mu0.1` | trapezoid, t_acc = T/3 | 1.0 | mu 0.1 | 143 | 5.16 | 2.24 | 0.45 | 0.47 | 10.3 | 17.7 | 0.41 / 0.26 |
| `index_scurve_1.0s_mu0.1` | S-curve | 1.0 | mu 0.1 | 143 | 9.03 | 6.57 | 4.37 | 1.21 | 9.8 | 17.7 | 1.47 / 0.44 |
| `index_zv_1.0s_mu0.1` | S-curve + ZV | 1.0 | mu 0.1 | 178 | 9.66 | 1.15 | 0.32 | 0.06 | 10.1 | 17.7 | 0.55 / 0.33 |
| `index_trapTn_1.0s_mu0.1` | trapezoid, t_acc = 0.393 s | 1.0 | mu 0.1 | 157 | 6.28 | 1.30 | 0.33 | 0.07 | 10.4 | 17.7 | 0.75 / 0.31 |
| `index_trap_1.5s_mu0.1` | trapezoid, t_acc = T/3 | 1.5 | mu 0.1 | 95 | 1.77 | 0.35 | 0.25 | 0.00 | 11.1 | 17.7 | 0.19 / 0.11 |
| `index_scurve_1.5s_mu0.1` | S-curve | 1.5 | mu 0.1 | 95 | 2.87 | 0.57 | 0.26 | 0.01 | 10.8 | 17.7 | 0.84 / 0.21 |
| `index_zv_1.5s_mu0.1` | S-curve + ZV | 1.5 | mu 0.1 | 110 | 2.63 | 0.68 | 0.11 | 0.04 | 10.8 | 17.7 | 0.25 / 0.18 |
| **`index_trapTn_1.5s_mu0.1`** | trapezoid, t_acc = 0.393 s | 1.5 | mu 0.1 | 86 | 2.10 | **0.62** | 0.11 | **0.03** | 11.1 | 17.7 | 0.21 / 0.13 |
| `index_trap_1.0s_c1e-3` | trapezoid, t_acc = T/3 | 1.0 | none, c = 1e-3 | 143 | 5.31 | 2.05 | 1.17 | 1.13 | 10.2 | 17.7 | 0.41 / 0.26 |
| `index_trap_1.0s_c0` | trapezoid, t_acc = T/3 | 1.0 | none, c = 0 | 143 | 8.05 | 3.77 | 3.77 | > dwell | 9.7 | 17.3 | 0.41 / 0.26 |
| `index_zv_1.0s_aug0.12` | S-curve + ZV | 1.0 | none | 178 | 11.01 | 2.70 | 2.54 | > dwell | 9.5 | 17.5 | 0.49 / 0.30 |
| `index_zv_1.0s_aug0.20` | S-curve + ZV | 1.0 | none | 178 | 10.82 | 2.04 | 1.88 | > dwell | 9.5 | 17.5 | 0.60 / 0.35 |
| `index_zv_0.8s` | S-curve + ZV | 0.8 | none | 237 | 17.53 | 6.31 | 5.80 | > dwell | 8.9 | 13.5 | 0.66 / 0.52 |
| `index_trap_1.0s_channel` | trapezoid, t_acc = T/3 | 1.0 | none | 143 | 7.03 | 3.48 | 3.23 | > dwell | 10.1 | 17.7 | 0.41 / 0.26 |
| `index_trapTn_1.0s` | trapezoid, t_acc = 0.393 s | 1.0 | none | 157 | 7.45 | 1.49 | 1.37 | > dwell | 9.8 | 17.7 | 0.75 / 0.32 |
| `index_trapTn_1.2s` | trapezoid, t_acc = 0.393 s | 1.2 | none | 118 | 4.34 | 1.14 | 1.06 | 1.93 | 10.6 | 17.7 | 0.32 / 0.18 |
| **`index_trapTn_1.5s`** | trapezoid, t_acc = 0.393 s | 1.5 | none | 86 | 4.01 | **0.52** | 0.49 | **0.38** | 11.0 | 17.7 | 0.22 / 0.14 |
| `index_trapTn_1.2s_mu0.1` | trapezoid, t_acc = 0.393 s | 1.2 | mu 0.1 | 118 | 3.21 | 0.94 | 0.09 | 0.06 | 10.8 | 17.7 | 0.33 / 0.19 |
| `index_zv_trapbase_1.5s` | trapezoid + ZV | 1.5 | none | 110 | 3.75 | 1.08 | 1.00 | > dwell | 10.7 | 17.7 | 1.06 / 0.27 |
| `index_trapTn_1.5s_aug0.12` | trapezoid, t_acc = 0.393 s | 1.5 | none | 86 | 3.82 | 0.52 | 0.47 | 0.28 | 11.0 | 17.7 | 0.21 / 0.13 |
| `index_trapTn_1.5s_aug0.20` | trapezoid, t_acc = 0.393 s | 1.5 | none | 86 | 3.84 | 0.83 | 0.77 | > dwell | 11.1 | 17.7 | 0.22 / 0.14 |
<!-- /T -->

`index_trap_1.0s_channel` is a single index with the earlier guide-channel pins and rails fitted (no
effect on swing). `aug0.12` / `aug0.20` change the auger + powder mass while keeping the profile tuned
to the nominal module.

"Settle" is the last time after a stop at which |swing| > 0.5 deg. "> dwell" means the gondola was
still swinging above 0.5 deg at the end of the 2 s dwell. No run produced a contact.

### Full laps (`swing_lap12.png`, `swing_by_region_fastlaps.png`, `clearance_fastlaps.png`, `motor_torque.png`)

`lap12_*` runs are 12 indexes with a 0.5 s dwell. `fastlap_*` runs are one continuous lap with an
S-curve speed profile.

<!-- T:laps -->
| run | peak chain speed (mm/s) | max swing (deg) | worst region | min neighbour gap (mm) | min shaft gap (mm) | contact samples | drive torque peak raw / 25 ms avg (N*m) | rms (N*m) | drive tension step per chain (N) |
|---|---|---|---|---|---|---|---|---|---|
| `lap12_trap_1.0s` | 143 | 7.3 | top run | 10.1 | 17.7 | 0 | 0.41 / 0.26 | 0.15 | 4.2 |
| `lap12_trapTn_1.5s` | 86 | 4.4 | top run | 11.0 | 17.7 | 0 | 0.22 / 0.14 | 0.07 | 2.2 |
| `fastlap_10s` | 127 | 9.9 | TR corner | 10.5 | 14.0 | 0 | 1.56 / 0.31 | 0.14 | 16.0 |
| `fastlap_6s` | 224 | 36.2 | TR corner | 7.2 | 4.4 | 0 | 2.71 / 0.53 | 0.29 | 27.9 |
| `fastlap_4s` | 357 | 165.1 | bottom run | -0.6 | -3.0 | 504 | 6.04 / 3.17 | 0.46 | 62.1 |

Max swing by region (deg):

| region | lap12_trap_1.0s | lap12_trapTn_1.5s | fastlap_10s | fastlap_6s | fastlap_4s |
|---|---|---|---|---|---|
| bottom run | 7.3 | 4.4 | 8.1 | 30.5 | 165.1 |
| BR corner | 6.2 | 3.4 | 8.5 | 26.9 | 45.4 |
| right side | 2.6 | 2.0 | 8.7 | 29.5 | 56.2 |
| TR corner | 6.1 | 4.0 | 9.9 | 36.2 | 67.6 |
| top run | 7.3 | 4.4 | 8.4 | 33.8 | 68.0 |
| TL corner | 6.9 | 3.5 | 9.2 | 26.4 | 67.9 |
| left side | 3.3 | 1.9 | 8.3 | 25.7 | 72.8 |
| BL corner | 6.1 | 3.9 | 9.2 | 30.3 | 165.1 |
<!-- /T -->

With every gondola upright, the smallest gap between neighbours is 11.4 mm (old: 11.1 mm). It occurs
where one gondola is about 1.2 links before a corner and its neighbour is about 0.8 links past it. The
corners pump the swing. Each corner turns the pivot path by 90 deg over 8 links (about 90 mm of pivot
travel), and the excitation grows quickly once that traverse time approaches the 0.39 s pendulum
period. At 224 mm/s it does, and the swing reaches 36 deg. At 357 mm/s a gondola goes over the top and
hits its neighbour and a shaft.

### Station: dock, tilt to 90 deg, taps and auger, with the CAD rig (`station.png`, `station.mp4`)

Since the gear-mesh study (`../../gear-mesh/README.md`) the carriage pivots on stub pins at its
centre-of-mass height, Sam's (32, -33.1) docked, carried by a U-yoke rigid on the P16's rod. The P16 + yoke is
one two-force link, 257.4 mm retracted (197.4 + 60), with its base clevis 277.4 mm under the docked pins. Docking
uses 20 mm of stroke; 90 deg needs 85 of 150 mm. The shorter lever about the hinge (32 mm at 0 deg, against
40 mm before) raises the actuator force at low tilt, and with it the pull on the station gondola's front pivot.
The dock is welded here, as before. `cad/gear-mesh/mesh_mujoco.py` models the dock itself: tooth contact, the
magnet, the locating pins.

<!-- T:station -->
| station run | chain model | static pivot Fz front / back (N) | min pivot Fz front / back (N) | pivot rise max front / back (mm) | chain rise max front / back (mm) | strip force max front / back (N) | swing docked (deg) | actuator peak while tilting (N) | tilt reached (deg) |
|---|---|---|---|---|---|---|---|---|---|
| `station_cad_rigidchain` | rigid chain (reference) | 2.09 / 1.64 | -9.57 / -1.03 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.012 | 19.3 | 90.5 |
| `station_cad_chain_nostrip` | 40 N chain span + 2 N/mm tab, no strip | 2.08 / 1.65 | -5.52 / -0.39 | 12.75 / 3.42 | 8.98 / 2.41 | 0.00 / 0.00 | 0.012 | 12.8 | 92.6 |
| `station_cad_strip` | hold-down strip, gap 0.5 mm, tab 2 N/mm | 2.08 / 1.65 | -6.71 / -0.58 | 4.88 / 1.61 | 0.50 / 0.50 | 8.34 / 1.80 | 0.012 | 14.5 | 92.7 |
| `station_cad_strip_tab50` | hold-down strip, gap 0.5 mm, tab 50 N/mm | 2.08 / 1.65 | -9.16 / -1.09 | 0.73 / 0.56 | 0.50 / 0.50 | 10.85 / 2.72 | 0.012 | 18.6 | 91.0 |

Pivot loads during the tilt, `station_cad_rigidchain` (median over +-2.5 deg; N, mm):

| tilt (deg) | 0 | 15 | 30 | 45 | 60 | 75 | 90 |
|---|---|---|---|---|---|---|---|
| front pivot Fz (N) | -7.45 | -2.84 | -1.83 | -1.07 | -0.34 | 0.47 | 1.38 |
| back pivot Fz (N) | -0.70 | 0.02 | 0.18 | 0.30 | 0.42 | 0.55 | 0.70 |

Pivot loads during the tilt, `station_cad_strip` (median over +-2.5 deg; N, mm):

| tilt (deg) | 0 | 15 | 30 | 45 | 60 | 75 | 90 |
|---|---|---|---|---|---|---|---|
| front pivot Fz (N) | -3.67 | -3.16 | -1.78 | -1.07 | -0.36 | 0.44 | 1.25 |
| back pivot Fz (N) | -0.03 | -0.03 | 0.18 | 0.30 | 0.42 | 0.55 | 0.68 |
| front pivot rise (mm) | 3.12 | 3.09 | 2.44 | 2.09 | 1.73 | 1.33 | 0.93 |
| front strip force (N) | 4.83 | 4.75 | 3.47 | 2.75 | 2.03 | 1.25 | 0.44 |

Pivot loads during the tilt, `station_cad_strip_tab50` (median over +-2.5 deg; N, mm):

| tilt (deg) | 0 | 15 | 30 | 45 | 60 | 75 | 90 |
|---|---|---|---|---|---|---|---|
| front pivot Fz (N) | -6.61 | -2.83 | -1.83 | -1.06 | -0.34 | 0.46 | 1.34 |
| back pivot Fz (N) | -0.56 | 0.02 | 0.18 | 0.30 | 0.42 | 0.55 | 0.70 |
| front pivot rise (mm) | 0.67 | 0.60 | 0.58 | 0.56 | 0.55 | 0.53 | 0.52 |
| front strip force (N) | 8.13 | 4.50 | 3.50 | 2.73 | 2.01 | 1.21 | 0.33 |

Actuator force against tilt (CAD rig, rigid chain):

| tilt (deg) | 0 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 |
|---|---|---|---|---|---|---|---|---|---|---|
| stroke used (mm) | 20 | 26 | 33 | 41 | 49 | 57 | 64 | 72 | 79 | 85 |
| lever arm about hinge (mm) | 32 | 38 | 42 | 45 | 46 | 46 | 44 | 42 | 38 | 33 |
| force, static estimate (N) | 10.45 | 9.24 | 8.39 | 7.73 | 7.15 | 6.58 | 5.98 | 5.30 | 4.48 | 3.40 |
| force, simulation (N) | 16.03 | 9.97 | 9.10 | 8.37 | 7.77 | 7.20 | 6.63 | 6.02 | 5.32 | 4.60 |
<!-- /T -->

The peaks (the minimum pivot Fz, the largest strip force, the largest rise) happen in the first 0.2 s
of the tilt. In the model the rod starts at full speed (40 mm/s) with no ramp. The quasi-static uplift
at 0 deg is about 2.7 N at the front pivot (static estimate: the hinge load swings from 2.55 N down to
3.0 N up). A P16-P start ramp, or starting the tilt at reduced speed, would cut the peaks toward that
value.

Fz is the vertical force from the chain (through the tab) on the gondola, so a value below 0 means the
gondola is pulling the chain up. With the strip the chain itself cannot rise more than 0.5 mm, and the
strip takes the rest of the uplift. "Pivot rise" adds the tab's own stretch.

The static estimate is 8.0 N at 0 deg because the 40 mm lever is short and module + carriage weigh 5.0
N. The rest, about 3 N, is pushed up through the hinge into the gondola. The 11.3 N simulated at 0 deg
includes the start-of-tilt transient (the rod accelerating to 40 mm/s); the peak is 14.8 N, about 30 %
of the P16-P's 50 N.

While docked, four sideways taps and four normal taps (3 N, 10 ms each) plus the auger turning at 54
rpm against 0.03 N*m of drag move the gondola by at most **0.012 deg**, well under the 0.2 deg
limit. This assumes the actuator's clevis roll stiffness is 150 N*m/rad. At 90 deg the module's weight
acts through the hinge, so the pivots are loaded downward again: 3.4 N front and 1.0 N back.

## Fixed kinematics: new vs old numbers

| quantity | old (smoothed table) | new (fixed kinematics) |
|---|---|---|
| min neighbour gap, all upright (mm) | 11.1 | 11.4 |
| trapezoid 1.0 s: max swing / station residual (deg) | 7.02 / 3.48 | 7.03 / 3.47 |
| S-curve 1.0 s: max swing / residual (deg) | 11.73 / 9.70 | 11.75 / 9.65 |
| S-curve + ZV 1.0 s: max swing / residual (deg) | 10.98 / 2.17 | 10.91 / 2.31 |
| S-curve + ZV 1.5 s: max swing / residual (deg) | 4.00 / 1.15 | 3.97 / 0.97 |
| trapezoid t_acc = T_n, 1.5 s, no friction: max swing / residual (deg) / settle (s) | 3.19 / 0.07 / 0.00 | 4.01 / 0.52 / 0.38 |
| trapezoid t_acc = T_n, 1.5 s, mu 0.1: residual 0.5 s after stop (deg) / settle (s) | 0.09 / 0.03 | 0.11 / 0.03 |
| trapezoid 1.0 s, mu 0.1: settle (s) | 0.47 | 0.47 |
| 12-index lap, recommended profile: max swing (deg) / min gap (mm) | 3.2 / 10.9 | 4.4 / 11.0 |
| 10 s lap: max swing (deg) / min gap / shaft gap (mm) | 10.2 / 10.2 / 13.7 | 9.9 / 10.5 / 14.0 |
| 6 s lap: max swing (deg) / min gap / shaft gap (mm) | 36.9 / 6.7 / 4.1 | 36.2 / 7.2 / 4.4 |
| drive torque peak, trapezoid 1.0 s / 10 s lap (N*m) | 0.31 / 0.65 | raw 0.41 / 1.56; 25 ms avg 0.26 / 0.31 |

The fix changes little except the recommended profile's residual: 0.07 deg became 0.52 deg without
pivot friction. The true chordal action keeps feeding the pendulum during each start and stop. The
tooth-passing frequency sweeps through 2.54 Hz at about 24 mm/s, and no time-based profile cancels
that. With the bronze pivot friction the residual is gone within 0.03 s.

## Iterations (before -> after)

1. **Index profile.** The baseline is a trapezoid with t_acc = T/3 and T = 1.0 s. It leaves 3.5 deg of
   swing at the station, which does not decay without pivot friction.
   - The jerk-limited S-curve made this **worse**: 9.6 deg. The residual depends on how much
     acceleration content sits at f_n (2.54 Hz), not on jerk.
   - The ZV shaper helps, giving 2.3 deg at 1.0 s and 0.97 deg at 1.5 s. It cannot cancel the
     kick a gondola gets when its SA-1 link leaves the bottom-left sprocket: at every stop one link
     straddles that tangent point, and that kick depends on position, not time.
   - **A trapezoid with t_acc equal to the pendulum period (0.393 s)** puts a spectral zero exactly at
     f_n. At 1.5 s per index: 0.52 deg residual, settled in 0.38 s without friction, 4.0 deg
     largest swing anywhere, 11.0 mm smallest gap.
2. **Pivot damping.** With the bronze sleeve's Coulomb friction (mu = 0.1) every profile at 1.5 s
   settles in 0.04 s or less. The tuned trapezoid settles in 0.03 s and the plain trapezoid in 0.00 s.
   At 1.0 s the plain trapezoid needs 0.47 s and the S-curve 1.21 s. Viscous damping of 1e-3 does
   less (1.13 s).
3. **Corners and speed limit.** A continuous 10 s lap (127 mm/s) swings 10 deg and keeps
   10.5 mm between neighbours. A 6 s lap (224 mm/s) swings 36 deg and leaves 7.2 mm, with 4.4 mm to a
   shaft. A 4 s lap flips a gondola. **Limit the chain to about 130 mm/s.**
4. **Chain lift at the station.**
   - The first rig (rod pin 50 mm from the hinge) lifted the front chain with 1.9 N. Moving the pin to
     68 mm fixed it, at the cost of 148 of 150 mm of stroke.
   - A guide channel inside the gondola also held the chain down, but it had no effect on swing, and
     the coordinator noted it has no support path that misses the moving gondolas. It has been
     dropped.
   - The CAD rig (YOKE_X = 40) lifts harder. On a rigid chain the front pivot pulls up with
     4.0 N at the start of the tilt (6.2 N peak). With a 40 N chain and the soft tab, and no
     strip, the front pivot rises **9.1 mm**, of which the chain rises 6.4 mm.
   - **With the hold-down strips, the chain stops at 0.5 mm.** The strip takes up to
     5.9 N (front) and 1.4 N (back) with the 2 N/mm tab, and 7.8 / 1.6 N with a 50 N/mm tab.
     The pivot itself still rises 3.7 mm with a 2 N/mm tab, but only 0.66 mm with a 50 N/mm tab.
     The strip unloads past about 40 deg of tilt.

## Recommended design changes

1. **Motion:** use a trapezoid whose acceleration and deceleration each last one pendulum period
   (0.39 s; measure it on the real gondola with a phone video), with about 1.5 s per index (peak 86
   mm/s). With bronze pivot friction it settles in 0.03 s; with none, it still leaves only about
   0.5 deg and settles in 0.4 s. It is the most robust of the profiles tested. Do not use a plain
   S-curve.
2. **Speed limit:** keep continuous moves at or below about 130 mm/s chain speed (a lap of at least
   10 s). Near 220 mm/s the corner traverse matches the pendulum period.
3. **Pivots:** keep the oil-impregnated bronze sleeves (mu of about 0.1). Their friction is the
   machine's main swing damper.
4. **Station:** keep the UHMW-PE chain hold-down strips. They cap the chain's rise at the 0.5 mm gap
   and carry at most about 8 N per strip. What is left is the gondola's own compliance between the
   chain and the plate, which sets how far the docked plate rises (0.7 mm at 50 N/mm, 3.7 mm at 2
   N/mm). Make the SA-1 tab, shoulder screw and end plate stack stiff (tens of N/mm). Moving the rod
   pin further from the hinge would also reduce the uplift itself: about 3 N at YOKE_X = 40 vs
   none at 65 mm or more, as in the earlier rig study.
5. **Drive:** the torque at the shaft stays below about 0.5 N*m (25 ms average) for any sensible
   profile, against 12 N*m available. Friction, not inertia, will set the real requirement.

## Outputs (`out/`)

<!-- T:outputs -->
| file | size | content |
|---|---|---|
| `results.json` | 85 kB | every number above (model, free decays, all runs, station timelines); `null` means not settled within the dwell |
| `swing_index_profiles.png` | 246 kB | station-gondola swing for the four index profiles at 1.0 and 1.5 s (no pivot friction) |
| `swing_lap12.png` | 535 kB | all 12 gondolas through a full lap of indexing, baseline and recommended profile |
| `swing_by_region_fastlaps.png` | 51 kB | max swing per straight or corner for the continuous laps |
| `clearance_fastlaps.png` | 219 kB | smallest neighbour gap over time for the continuous laps |
| `motor_torque.png` | 100 kB | drive-shaft torque (raw rigid-chain value) for indexing and laps |
| `free_decay.png` | 204 kB | pivot damping and friction sensitivity |
| `station.png` | 321 kB | station with the CAD rig: tilt/stroke, actuator force vs tilt, pivot rise, pivot forces, strip force, docked swing |
| `lap_index.mp4` | 8.0 MB | 12 indexes with the recommended profile (trapezoid, accel = one pendulum period, 1.5 s per index), labelled. Side view along x (left), 3/4 view (right). 1280x720 H.264 30 fps, 24.3 s, rendered at 15 fps without shadows |
| `lap_index.gif` | 9.8 MB | the same, 720 px wide, 10 fps |
| `station.mp4` | 677 kB | station sequence with the CAD rig as ported on 2026-10-18 (stub pins at the carriage's COM height, U-yoke) and the hold-down strips: dock, tilt to 90 deg, auger + taps, tilt back, undock. Side view along y and 3/4 view; other gondolas see-through. 1280x720 H.264 30 fps, 8.9 s |
| `station.gif` | 0.83 MB | the same, 720 px wide, 10 fps |
<!-- /T -->

`out/pivot_table.npz` is a cache, rebuilt in about 3 s; it does not need committing. `out/auger/` belongs to the separate auger study.

## Limitations

- In the carousel runs the chain is rigid and the pivots follow `kinematics.pivots()` exactly; chordal
  kinks become short force spikes, which is why torque is also given as a 25 ms average. Only the
  station runs model the chain's compliance: a massless span spring per chain, a tab spring per pivot,
  and the strip as a rigid stop. Chain stretch, the sag of a lightly tensioned span, and tooth impacts
  are not modelled.
- Masses and inertia come from primitive shapes, not STL meshes (none were in `stl/` when this ran).
  The swing frequency depends on the COM drop, which is well bounded (23-25 mm), so this should not
  change the conclusions.
- The 40 N chain tension, the 2 N/mm and 50 N/mm tab stiffnesses, and the 150 N*m/rad clevis roll
  stiffness are assumptions. The strip results scale with them as the tables show.
- The tap is a force pulse on the module, and the auger load is a constant 0.03 N*m drag. Gear mesh
  and solenoid recoil are not modelled.

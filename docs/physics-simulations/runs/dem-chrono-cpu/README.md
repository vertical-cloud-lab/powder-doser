# dem-chrono-cpu: silo discharge through a square orifice (Project Chrono, core ChSystemSMC on CPU)

## What it models and why it matters here
Flow through an orifice under gravity is the simplest discharge benchmark. It is the physics behind the Hall/Carney
funnel tests and the powder's free fall from the doser's exit. Beverloo's law, W = C rho_b sqrt(g) (D - k d)^2.5,
gives the mass flow rate W from the bulk density rho_b, the orifice size D and the grain size d. The run checks that a
CPU-only Chrono build reproduces that scaling with the paper's salt parameters. It also tests whether Chrono, PR
#180's recommended GPU engine family, is usable on this runner without a GPU.

## Code and version
* PyChrono **10.0.0, conda-forge build `py312h3a49c4c_0`**, Python 3.12, in its own env:
  `conda create -p /tmp/sims-scratch/dem-chrono-cpu/env -c conda-forge --override-channels python=3.12 pychrono=10.0.0 numpy`.
  The install took about 1 min.
* Solver: core `ChSystemSMC` with Hertz contact, `MultiStep` tangential history and material-based coefficients, on 1
  thread.
* Collision: Bullet (`ChCollisionSystem.Type_BULLET`). This conda-forge build has no multicore collision (no Thrust),
  and Chrono::GPU/DEM is CUDA-only (see PR #180).

## Setup
* **Grains.** N = 1500 spheres. Diameters are 4 x (0.361 / 0.425 / 0.489) mm = 1.444 / 1.700 / 1.956 mm (coarse-grained
  4x; mean d = 1.70 mm), number fractions 0.3 / 0.4 / 0.3.
* **Material.** Density 2165 kg/m3, E = 2e5 Pa, Poisson 0.3, restitution 0.5. Sliding friction 0.5 between particles
  and 0.4 against the walls. Rolling friction 0.3 is set but has no effect (see below).
* **Silo.** Flat-bottomed, 16 mm x 16 mm inside (fixed boxes). A square orifice of side L sits in the floor, closed by
  a plug.
* **Fill.** Grains start on a lattice, settle for 0.2 s against the plug (fill height 24 mm), then the plug is moved
  away.
* **Counting.** Grains whose centres fall 4 mm below the floor are counted and parked (fixed, collision off).
* **Orifice sizes.** L = 5.5, 7, 8.5 and 10 mm (L/d = 3.2-5.9). Each runs 0.6 s after opening.
* **Time step.** dt = 5e-5 s, about 0.12 of the Rayleigh time of the smallest grain.
* **Flow rate.** W is the slope of discharged mass against time, from 0.1 s after opening until 60 % of the inventory
  has left (or the run ends).
* **Bulk density.** rho_b = total mass / (box area x settled fill height).
* **Beverloo fit.** A square orifice has area (L - k d)^2 and hydraulic diameter (L - k d), so
  W = C_sq rho_b sqrt(g) (L - k d)^2.5. C_sq x pi/4 is the coefficient comparable to the circular-orifice C, which is
  usually 0.55-0.65. Fitting W^0.4 against L gives C and k.

## How to rerun
```
bash run.sh [scratch_dir]   # rolling-friction check, four orifice sizes, then analyze.py (PNG + GIF/MP4 of L = 8.5 mm)
```

## Runtime
RESULTS_RUNTIME

## Result
RESULTS_TABLE

## Status
RESULTS_STATUS

## Limitations
* **Domain size.** The silo is small: the box is only 1.6-2.9 orifice widths across and the fill only 24 mm deep.
  Wall effects and a falling fill height bias W. The flow is not a converged Beverloo measurement.
* **Coarse-grained spheres** (4x salt size) with a reduced E = 2e5 Pa. The real salt (d = 0.43 mm) would need about
  60x more grains for the same silo.
* **No rolling resistance.** Core `ChSystemSMC` ignores `SetRollingFriction`: a sphere rolling at 0.1 m/s keeps
  exactly the same speed with mu_roll = 0 and 0.3 (`rolling_check.json`). Cubic salt grains resist rolling more than
  these spheres do.
* **Square orifice, not circular.** The circular-equivalent C uses the area ratio pi/4. Many Beverloo fits use
  circular orifices.
* **Bullet in SI units blew up.** With mm-size bodies in metres, Bullet threw grains out at about 700 m/s within
  0.02 s. PR #180 saw the same: Bullet "blows up while settling against the plug". The fix was to run Chrono
  internally in millimetres (`--lu 1000`: lengths x1000, E/1000, g x1000; all outputs converted back to SI). Lowering
  Bullet's contact-breaking threshold to 1e-5 m did not help.

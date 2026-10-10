# DEM digital twin of the auger powder doser (issue #158)

Particle-level (discrete element method, DEM) simulations of the rig's
rotating-tube auger, using real-size salt grains, gravity and contact
mechanics. No coarse-graining is used. They were run to answer three
questions from #158:

1. **How closely can a twin represent the rig?** Compare against the
   measured salt yields from PRs #131 and #166 and the battery runs.
2. **How many particles can we simulate?** Is a whole auger (hundreds of
   thousands, or millions, of grains) feasible?
3. **Which internal auger dimensions matter for very small doses?** This
   covers the 0.1–10 mg doses in #117 and expensive powders such as Sc.

RESULTS_PLACEHOLDER

## How many particles can we simulate?

`benchmark.py` packs the **entire** 250 mm auger bore (23 flight turns plus the funnel, of the parametric
Auger4 geometry) with real-size grains in a dense FCC packing, so every grain starts with 12 contacts (a
pessimistic case). It then times LIGGGHTS on one core of this runner (AMD EPYC 7763, 2 physical cores /
4 vCPUs, 15 GB RAM, no GPU):

| grain d (mm) | grains in the auger | M particle-steps/s (1 core) | s per step | peak RAM (GB) | kB per grain |
|---|---|---|---|---|---|
| 0.90 | 106,788 | 0.67 | 0.16 | 0.25 | 2.5 |
| 0.60 | 381,487 | 0.74 | 0.52 | 0.63 | 1.8 |
| 0.45 | 942,885 | 0.66 | 1.42 | 1.42 | 1.6 |
| 0.35 | 2,045,660 | 0.88 | 2.32 | 2.95 | 1.5 |

![scaling](results/scaling.png)

Real counts for the rig auger (79 mL; 1.39 mL of free funnel volume around the core tip):

| powder | one grain | 1 mg dose | 10 mg dose | funnel full | whole auger full |
|---|---|---|---|---|---|
| salt, d50 0.425 mm | 87 µg | 11 grains | 115 | 19 k | **1.1 M** (94 g) |
| AlSi10Mg, d50 42 µm | 0.10 µg | 9.7 k | 97 k | 18 M | **1.0 billion** (107 g) |
| Sc, d50 40 µm (assumed) | 0.10 µg | 10 k | 100 k | 21 M | **1.2 billion** |

What that means:

* **Memory is not the limit for salt.** A completely full rig auger of real-size salt (about 1.1 M grains)
  needs about 1.7 GB. This runner could hold about 8–9 M grains.
* **Time is the limit.** At about 0.75 M particle-steps/s per core and Δt about 21 µs, one auger
  revolution at 60 rpm is about 49 k steps.
  * The whole salt-filled auger therefore costs about **19 h per revolution on one core**, or about 5 h
    with ideal 4-core MPI. The Debian LIGGGHTS MPI build crashes on STL meshes, so that is a projection.
  * The dosing-relevant section (funnel plus 1.5–2 flights, 29 k grains) costs **about 30 min per
    revolution**, which is what the twin below uses.
  * A GPU engine (Chrono::GPU / DEM-Engine, as recommended in the earlier review) is the route to the
    whole auger.
* **Fine metal powders (AlSi10Mg, Si, Sc) are out of reach at real size.**
  * A whole auger holds about 10⁹ particles.
  * The Δt also shrinks about 10× with the grain size, so even the funnel alone (about 2 × 10⁷
    particles) is beyond any single machine.
  * Two options remain: simulate *just the dose* (a 1–10 mg dose is only 10⁴–10⁵ particles, which is
    tractable), or coarse-grain with cohesion rescaled to keep the Bond number.
  * Cohesion, not grain count, is the physics that matters there: Si −325 mesh (d50 about 25 µm) gave
    **0 mg/rev** on the rig, while −110/+200 mesh gave 302 mg/rev at 45°.



## What is simulated

| Item | Value | Source |
|---|---|---|
| Engine | LIGGGHTS-PUBLIC 3.8 (Debian `liggghts`), serial; one case per core | the MPI build segfaults reading STL meshes on this runner |
| Contact law | Hertz–Mindlin with tangential history, EPSD2 rolling friction, no cohesion | standard for free-flowing salt; rolling friction stands in for the cubic grain shape |
| Salt grains | d50 0.425 mm, three sizes ±15 %, ρ 2165 kg/m³ | literature class values in `data/powder-properties/literature_powder_properties.csv` (branch `claude/issue-163-…`); no PSD has been measured |
| Friction | μ particle–particle 0.5, particle–PLA 0.4, rolling 0.3 (0.7 / 0.6 / 0.5 in the high-friction case) | uncalibrated, typical values for salt |
| Stiffness | E = 0.2 MPa, ν 0.3, e 0.5, Δt = 0.2 × Rayleigh time | softened, as is standard practice for DEM flows. Checked on a dump: mean overlap 0.35 % of d, 99 % of contacts below 1.2 % |
| Rig auger | measured by slicing `threaded-auger-final.stl` (branch `claude/issue-165-…`):<br>• 20.9 mm bore<br>• solid 7.96 mm core whose conical tip ends inside the exit (annular exit, r 0.43–1.5 mm, 7 mm²)<br>• 0.5 mm single-start right-handed flight at 10.4 mm pitch, continuing down the 37° half-angle, 12 mm funnel | `geometry.py` (parametric; the same generator builds every variant) |
| Simulated section | funnel plus the lowest 1.5 flight turns (2 for the micro-augers); a feed zone above is kept topped up by insertion | the rig's 83 mm flighted section plus 166 mm reservoir is too long to simulate whole at real grain size (see the scaling section) |
| Tilt and rpm | gravity is tilted (tilt = plate angle = physical tube angle, outlet down); the mesh spins at auger rpm | firmware on the PR #166 branch: `PLATE_GEAR_RATIO`, `AUGER_GEAR_RATIO` |
| Protocol | settle with the exit plugged → unplug and spin for 1.5 rev → stop for 0.5–0.6 s (afterflow) | outflow is counted (and grains deleted) at a disk 1.5 mm below the exit |

## Files

| File | Purpose |
|---|---|
| [`geometry.py`](geometry.py) | parametric auger surface mesh: bore, flight(s), solid or open core, conical core tip, funnel, exit |
| [`run_case.py`](run_case.py) | builds one case (mesh, initial packing that avoids the flight, LIGGGHTS input), runs it, logs the outflow |
| [`benchmark.py`](benchmark.py) | packs the entire 250 mm auger with 0.1–2 M grains and times LIGGGHTS (throughput and memory) |
| [`analyze.py`](analyze.py) | dosing metrics: mg/rev, mass per 5/15/45/90° nudge (mean, sd, CV), afterflow, funnel hold-up |
| [`figures.py`](figures.py) | comparison, scaling and sweep plots |
| [`render.py`](render.py) | OVITO (Tachyon) cut-away movie: the near half of the rotating auger is clipped away (wall grey-blue, flight blue, solid core amber); grains are coloured by speed; a live dispensed-mass panel sits alongside |
| [`results/`](results/) | case configs, outflow time series, metrics, benchmark data, figures, movies |

Reproduce one case (about 10 min for a micro-auger, about 1–1.5 h for the rig section on one core):

```bash
sudo apt-get install -y liggghts ffmpeg mesa-vulkan-drivers
pip install numpy scipy matplotlib trimesh shapely ovito pillow
cd sim/dem
python run_case.py results/cases/rig_t27p5_r60/config.json --workdir /tmp/dem/rig_t27p5_r60
python analyze.py /tmp/dem/rig_t27p5_r60
python render.py --case /tmp/dem/rig_t27p5_r60 --out rig.mp4 --gif rig.gif
```

## Limitations

* **Uncalibrated contact parameters.** Friction, rolling friction and restitution are textbook values for salt, not
  fitted to this powder lot. No particle-size distribution has been measured for any powder on the rig, so the 0.425 mm
  class value is an assumption, and grain size relative to the exit gap matters a lot (below).
* **Spheres, not cubes.** EPSD2 rolling friction mimics the rotational resistance of cubic salt grains, but not their
  interlocking. Arching at narrow exits is probably *under*-estimated.
* **Short runs.** 1.25–1.5 revolutions per case (one core, about 30 min per revolution for the rig section).
  Per-revolution means carry a standard error of a few to about 10 %.
  * The windowed nudge statistics come from continuous rotation, not start/stop nudges.
  * Start/stop behaviour is only probed through the afterflow window.
* **Section, not whole tube.** Only the funnel and the lowest 1.5–2 flights are simulated.
  * Insertion keeps a feed zone topped up, which stands in for a well-filled reservoir.
  * The rig's strong dependence on fill level (143 → 40 mg/s as a 55° tube emptied) is therefore not modelled.
  * Some feed-zone grains spill out of the open top of the meshed section. They never reach the outlet and are hidden in the movies.
* **No cohesion for salt, no humidity, no tribocharging, no tapper.** The micro "cohesive" case uses SJKR with an
  illustrative cohesion energy density only. Electrostatics would need DEM-Engine or LAMMPS (see the triboelectric review on this issue).
* **Softened stiffness** (E = 0.2 MPa) is standard for dense granular flow and the overlaps were checked. Impact-dominated
  details (bouncing in the free fall below the exit) are not resolved.
* **The CAD core tip** (Ø0.86 mm at the exit plane) cannot be printed as drawn with a 0.4 mm nozzle. The "as-printed"
  variant cuts it 2 mm short as a guess; measuring the printed exit would settle this.

## Next steps

1. **Measure the as-printed exit** (photograph or calliper the core tip and annulus) and the salt PSD (sieve or image).
   These are the two inputs the twin is most sensitive to.
2. **Calibrate** μ, μ_r and the fill level against the battery C angle sweep (36 / 161 / 248 mg/rev at 0 / 22.5 / 45°)
   with a small Bayesian-optimisation loop. Each evaluation is one micro-scale or 30 min rig-scale run. Then validate
   against the PR #166 rpm law (flow ∝ rpm^0.65) without refitting.
3. **Get a GPU** for whole-auger runs: DEM-Engine (Chrono) or Chrono::GPU from the earlier review. Then the 1.1 M-grain full
   tube (and fill-level effects) become an overnight job, not a week.
4. **For fine metal powders and Sc**, simulate only the dose region at real size (10⁴–10⁵ particles per mg-scale dose),
   or coarse-grain with Bond-number-preserving cohesion. Calibrate against AlSi10Mg (339±15 mg/rev at 45°, CV 4.5 %)
   and the Si −325 no-flow result.

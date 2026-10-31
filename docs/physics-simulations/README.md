# Physics-based simulations for the doser and the powder tests

Requested on PR #184 ([comment](https://github.com/vertical-cloud-lab/powder-doser/pull/184#issuecomment-6537306678)):
find which physics-based simulations could be run for what the optimization paper (#179, PR #184) and the
28 Oct meeting discuss, using a series of Edison queries and full texts read through the doser Pi, then
attempt to run **all** of the methods found.

| Folder / file | What |
|---|---|
| [`LITERATURE.md`](LITERATURE.md) | The 21 method families found, where each is used, which doser question it could answer, and the open-source codes |
| [`edison/`](edison/) | The nine Edison queries ([`run_queries.py`](edison/run_queries.py)). The key was refused with 403 in the session that wrote them ([`STATUS.md`](edison/STATUS.md)); after the key was rotated they were sent at 03:00 UTC from a session on #196, and their answers land here |
| [`fulltext/`](fulltext/) | Headed-Chrome reader that opens open-access papers through the Pi with pointer moves and clicks ([`fetch_fulltexts.py`](fulltext/fetch_fulltexts.py)); [`manifest.json`](fulltext/manifest.json) pins what was read (texts not committed) |
| [`runs/<id>/`](runs/) | One folder per simulation attempt: inputs and scripts to rerun, `README.md`, `result.json`, figure, and an animation where the run evolves in time |
| [`results.md`](results.md), [`results.json`](results.json) | All runs in one table, built by [`collect_results.py`](collect_results.py) |

## Results

31 runs, 24 ran and 7 partly (reduced scale or one part failing). Animations and figures are in each folder; the PR description (#196) shows them all.

| # | Family ([catalog](LITERATURE.md)) | Run | Code | Status | Headline |
|---|---|---|---|---|---|
| 1 | DEM: auger twin | [`dem-liggghts-auger-short`](runs/dem-liggghts-auger-short) | LIGGGHTS 3.8 | ran | #180 rig case reruns here. A quarter turn delivers 16.7 mg dry (#180: 12 mg) and 0.13 mg (one grain) cohesive |
| 2 | DEM on a standard test | [`dem-liggghts-aor`](runs/dem-liggghts-aor) | LIGGGHTS 3.8 | ran | Angle of repose 21.9° ± 1.4° dry, 39.3° ± 3.6° cohesive |
| 3 | DEM on a standard test | [`dem-liggghts-drum`](runs/dem-liggghts-drum) | LIGGGHTS 3.8 | ran | Dynamic angle 39.2° ± 4.4° dry; cohesive slab avalanches from 62° to 25° (± 12.4°) |
| 4 | DEM on a standard test | [`dem-liggghts-hall`](runs/dem-liggghts-hall) | LIGGGHTS 3.8 | ran | Hall 138 s/50 g (Beverloo: 0.358 g/s, DEM 0.363), Carney 17.4 s/50 g; cohesive Hall jams after 56 grains |
| 5 | DEM on a standard test | [`dem-liggghts-tap`](runs/dem-liggghts-tap) | LIGGGHTS 3.8 | ran | Hausner ratio 1.07 dry, 1.16 cohesive (30 taps; cohesive still compacting) |
| 6 | DEM on a standard test | [`dem-liggghts-shear`](runs/dem-liggghts-shear) | LIGGGHTS 3.8 | ran | At 50–200 Pa: dry c = 6.6 Pa, φ = 24.8°, *ff*<sub>c</sub> 20.8; cohesive c = 11.9 Pa, φ = 32.3°, *ff*<sub>c</sub> 13.8 |
| 7 | DEM: spreading | [`dem-liggghts-spread`](runs/dem-liggghts-spread) | LIGGGHTS 3.8 | ran | Dry layer φ 0.34, 90 % coverage. Cohesive: no layer on a smooth plate; φ 0.26, 72 % coverage on a cohesive one |
| 8 | DEM: liquid bridges | [`dem-liggghts-capillary`](runs/dem-liggghts-capillary) | LIGGGHTS 3.8 | ran | `easo/capillary/viscous` works; wet heaps (Bo of order 100) build columns and clumps, not cones |
| 9 | DEM → μ(I) | [`dem-lammps-shear-mui`](runs/dem-lammps-shear-mui) | LAMMPS 2024 | ran | μ(I) from 0.493 to 0.568, μ<sub>s</sub> 0.488; JKR (Bo ≈ 10) lifts μ by about 0.1 and gives c ≈ 8.4 Pa |
| 10 | DEM: charging | [`dem-lammps-charge`](runs/dem-lammps-charge) | LAMMPS 2024 | ran | 1×10⁻⁵ C/kg barely changes the bed; 1×10⁻⁴ C/kg stops a dense bed forming (partly a cutoff artefact) |
| 11 | DEM: liquid bridges | [`dem-yade-capillary`](runs/dem-yade-capillary) | Yade (daily) | partial | Collapsed height H/H₀ 0.07 dry, 0.25 at 0.1 % water, 0.33 at 1 %. The dry baseline lacks rolling resistance (broken in this contact law) |
| 12 | DEM on a standard test | [`dem-yade-directshear`](runs/dem-yade-directshear) | Yade (daily) | ran | Periodic triaxial at 50–400 Pa: peak 47°, residual 44°; no cohesion above ± 20 Pa noise at Bo 5 or 50 |
| 13 | DEM: orifice | [`dem-mercurydpm`](runs/dem-mercurydpm) | MercuryDPM (source) | partial | 5.9 d orifice clogs after 112 grains; 8.2 d flows at 0.84 × Beverloo |
| 14 | DEM: orifice | [`dem-chrono-cpu`](runs/dem-chrono-cpu) | PyChrono 10 (SMC) | ran | 1.9–15 g/s through 5.5–10 mm; Beverloo fit C 0.61, k 1.18 |
| 15 | DEM: grain shape | [`dem-nonspherical`](runs/dem-nonspherical) | Yade (daily) | partial | Heap angle 28.5° spheres, 37.7° spheres + rolling resistance, 40.3° cube clumps; LIGGGHTS superquadrics not runnable in the Debian build |
| 16 | Contact dynamics | [`contact-dynamics`](runs/contact-dynamics) | LMGC90 (source) | partial | 2D silo: 4 d jams, 5–10 d flow; 2D Beverloo C = 0.87, k = 1.23 |
| 17 | CFD–DEM | [`cfd-dem`](runs/cfd-dem) | OpenFOAM v1912 DPMFoam | partial | MFiX not installable. A 100 µm AlSi10Mg plug falls 28 mm in 80 ms with air (76 ms vacuum, 93 ms for one isolated grain) |
| 18 | DEM–FEM | [`dem-fem-coupling`](runs/dem-fem-coupling) | 4C (Docker) | partial | An 11 mg dose hitting a compliant pan: 0.38 mm sag at 28 ms, then rebound above flat. Stopped at 48 of 70 ms |
| 19 | DEM: tribocharging | [`dem-tribocharge-numba`](runs/dem-tribocharge-numba) | own numba DEM | ran | Charge saturates in 0.75 rev: 27.5 µC/kg in dry air, 14.2 in argon; 5.2 % vs 4.0 % of grains held on the wall |
| 20 | MPM | [`mpm-taichi`](runs/mpm-taichi) | Taichi 1.7.4 | ran | Column runout 3.06 (c = 0) vs 1.11 (c = 100 Pa). The silo did **not** follow the 3/2 law at this resolution (a finer grid more than doubled the flow) |
| 21 | SPH | [`sph-granular`](runs/sph-granular) | own numba WCSPH | ran | Runout 4.23 vs 1.35; agrees with MPM. PySPH 1.0b2 built but has no granular scheme |
| 22 | FEM plasticity | [`fem-druckerprager`](runs/fem-druckerprager) | own Q8 FEM | ran | An arch over a 3 mm slot holds above c ≈ 13.5 Pa (φ 34°), i.e. *ff*<sub>c</sub> below about 7.9 at 400 Pa |
| 23 | μ(I) and non-local | [`mui-rheology`](runs/mui-rheology) | own numpy | ran | Bagnold profiles to 10⁻⁵. Non-local model: a 2.5 d layer of salt-like powder stops at 37.4°, a 15 d layer at 34.1° |
| 24 | Closed form | [`analytic-orifice-screw`](runs/analytic-orifice-screw) | own numpy | ran | Annulus-limited Beverloo, no fit: 0 / 136 / 149 / 185 mg/rev against measured 28 / 108 / 105 / 195 |
| 25 | Cellular automata | [`ca-avalanche`](runs/ca-avalanche) | own numba | ran | Oslo model verified (τ 1.550); feeder CA: cohesion makes bursts 2.7× larger |
| 26 | Monte Carlo packing | [`mc-packing`](runs/mc-packing) | own numba | ran | Salt PSD: poured 1262 kg/m³, dense 1370 kg/m³, Hausner analog 1.085 |
| 27 | Moisture | [`moisture-sorption`](runs/moisture-sorption) | own scipy | ran | Pure NaCl: no change in flow below about 73.5 % RH; bridges and Bo ≈ 40–130 from 75 % RH |
| 28 | Bayesian SMC | [`bayes-grainlearning`](runs/bayes-grainlearning) | GrainLearning 2.0.5 | ran | 240 evaluations of a stand-in model: μ<sub>s</sub> 0.62 ± 0.02, Bo 0.017 ± 0.013 |
| 29 | Emulator + MCMC | [`bayes-gp-emulator-mcmc`](runs/bayes-gp-emulator-mcmc) | scikit-learn + emcee | ran | The tilt sweep alone leaves rolling friction unidentified; a wall-friction test fixes μ<sub>s</sub> to ± 0.05 |
| 30 | Learned simulator | [`gns-gnn-simulator`](runs/gns-gnn-simulator) | GNS (PyTorch) | partial | Trained 13 min on 45 DEM runs: runout −6 % / +20 % in range; blew up out of range |
| 31 | PINN (extra) | [`surrogate-pinn`](runs/surrogate-pinn) | PyTorch | ran | Janssen stress: forward error ≤ 3.3 %; inverse K·μ<sub>w</sub> 0.199 ± 0.004 (truth 0.2) |

One family has no run of its own: **coarse-grained DEM** (family 5). It is used inside runs 11, 13, 14 and 17, where grains were scaled up 2.9–4×.

## What this suggests for the paper (PR #184)

These are smoke tests and small studies, not calibrated predictions. Still, several points bear directly on the plan in `OUTLINE.md` §4A and §2.6 of the draft.

1. **One DEM parameter set can be checked against every cheap test the lab plans to run.**
   - **Cost.** With the #180 twin's salt parameters, the angle of repose, rotating drum, Hall/Carney, tapping, shear cell and blade spreading each took 1–10 CPU-minutes on one core (runs 2–7).
   - **Effect of cohesion.** Switching on SJKR cohesion at Bo ≈ 5 moved every test in the expected direction:

     | Test | Dry | Cohesive |
     |---|---|---|
     | Angle of repose | 22° | 39° |
     | Drum avalanche scatter | ± 4° | ± 12° |
     | Hausner ratio | 1.07 | 1.16 |
     | *ff*<sub>c</sub> | 21 | 14 |
     | Hall funnel | flows | jams |
     | Auger | flows | stops |

   - **So** the inferred cohesion and friction can be tested against the in-house measurements from the 28 Oct meeting (angle of repose, bulk and tapped density, Hall/Carney) inside the same model, not only against an outsourced *ff*<sub>c</sub>.
2. **The tilt sweep alone will not pin down every contact parameter.**
   - **Our run.** In the emulator study (29), mg/rev vs tilt left rolling friction unidentified. A second observable that constrains wall friction broke the degeneracy.
   - **The full texts agree.** Karkala et al. needed a shear cell *and* dynamic yield strength. Lupo et al. could not match angle of repose and unconfined yield strength with one JKR parameter set.
   - **Suggestion.** Infer from the tilt sweep plus at least one of: wall friction, mass per tap, or the angle of repose or tapped density measured on the same jar.
3. **The doser works at tens to hundreds of Pa; shear cells test at kPa.**
   - **Reservoir.** The stress saturates at 320–534 Pa beyond a few cm of fill (24).
   - **Exit.** Only about 14 Pa is available to break an arch over the exit (24). The FEM run puts the arching threshold at c ≈ 13.5 Pa, i.e. *ff*<sub>c</sub> below about 7.9 at 400 Pa consolidation (22). The DEM shear cell ran at 50–200 Pa (6).
   - **For Fig. 6c.** Comparing inferred cohesion with a kPa-level *ff*<sub>c</sub> needs the flow function extrapolated to low stress.
   - **For the paper's claim.** This is also an argument for it: the doser responds in a stress range standard testers don't reach.
4. **Cheap physics follows the tilt trend and could serve as a prior.**
   - **Exit annulus.** Beverloo through the core-tip annulus with g·sin(tilt), with no fitted parameter, gets 45° within 5 % and the shape from 22.5° to 45° (24).
   - **Other orifices.** The DEM Hall and Carney runs land within 1–4 % of Beverloo (4); MercuryDPM gives 0.84× (13); Chrono and LMGC90 return Beverloo constants (14, 16).
   - **Suggestion.** A Beverloo-annulus mean function could seed the BO and the inference. The 0° point (screw-driven, 28 mg/rev) still needs the DEM.
5. **Moisture and static need measurements before more simulation.**
   - **Moisture.** Pure NaCl should dose the same until about 73.5 % RH, with bridges forming at 73.5–75.2 % (27). So the "before and after humid air" test should straddle 75 % RH and log RH. Once bridges form, DEM heaps change completely (8, 11).
   - **Static.** In LAMMPS, 1×10⁻⁵ C/kg barely changes a bed while 1×10⁻⁴ C/kg dominates it (10). The condenser model puts salt on PLA at 1.4–2.8×10⁻⁵ C/kg (19), near the low end, but its inputs are assumed. A Faraday-cup charge-to-mass measurement on the auger output (#84, #117) decides which regime the doser is in.
6. **Spreading tests need a specified substrate.** Dry salt spreads (φ 0.34). A cohesive powder slid off a smooth plate as one block but spread on a cohesive one (7). The CubXL or wiper protocol should fix the plate material and finish.
7. **Fine metal powders need more than this runner.**
   - **Air.** Air drag matters for 35 µm grains: an isolated grain takes 307 ms to fall 28 mm, against 76 ms in vacuum (17).
   - **Grain count.** Fine-powder DEM needs coarse-graining or a GPU (#180).
   - **Inference cost.** The 48-point emulator design costs about 96 CPU-hours in LIGGGHTS (29).
   - **Learned simulators.** They train in minutes but fail outside their training range (30).

## Caveats

- **Scale and settings.** Every run is reduced in size and time:
  - single-threaded, one seed per case;
  - Young's modulus softened by about 10⁵ in the DEM runs;
  - grains scaled 2.5–4× in several engines;
  - 2D in the contact-dynamics, MPM, SPH, FEM, charging and GNS runs.

  Each `README.md` lists its own limitations.
- **Inputs are not same-lot measurements.** Salt parameters are the #180 twin's, the "cohesive" powder is a chosen Bond number, and the charging and moisture constants are literature or assumed values. None of these is a measurement on the doser's jars.
- **Stand-in model.** The Bayesian runs (28, 29) calibrate a stand-in model, not the DEM, and two of its constants were tuned toward the DEM's nominal parameters.
- **Literature status.** Rows marked *abs.* in `LITERATURE.md` rest on abstracts or search snippets; **FT** rows were checked against the full text.
- **Runner housekeeping.** The 4C Docker image (9.7 GB unpacked) and about 2 GB of scratch outputs stayed on the runner and were not committed. A NumPy in `~/.local` shadows the system one, so Yade needs `PYTHONNOUSERSITE=1`.


## Rerunning

Each `runs/<id>/README.md` has its own commands. The codes come from:

- Debian packages: `liggghts` (LIGGGHTS-PUBLIC 3.8), `lammps`, `yade`, `openmpi-bin`;
- pip: `taichi`, `pysph`, `grainlearning`, `scikit-learn`, `emcee`, `torch` (CPU), `numba`, `imageio-ffmpeg`;
- conda: `pychrono`, `mfix` where a run used them;
- source: MercuryDPM.

Every run was sized for a shared 4-core GitHub runner with no GPU, single-threaded, mostly under 10 minutes. They
are smoke tests and small studies, not calibrated predictions. The numbers that matter for the paper still need
same-lot measurements (PR #184, OUTLINE §4A).

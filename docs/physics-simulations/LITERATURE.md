# Which physics-based simulations fit the doser work: what the literature shows

This is the survey behind [`README.md`](README.md). It asks which simulation methods could be run for the topics
of PR #184 and the 28 Oct meeting: inferring cohesion and friction from dosing data, the standard flow tests
(shear cell, Hall/Carney, angle of repose, bulk and tapped density), moisture, static, and spreadability.

**How it was gathered.** The nine Edison queries in [`edison/run_queries.py`](edison/run_queries.py) could not be
sent: every login returned 403 ([`edison/STATUS.md`](edison/STATUS.md)). In their place:

- web searches on each query's topic, and
- **15 open-access full texts read (16 attempted) in a headed Chrome whose traffic left through the doser Pi**, with real pointer
  moves and clicks ([`fulltext/fetch_fulltexts.py`](fulltext/fetch_fulltexts.py)). The texts are not committed
  (public repo); [`fulltext/manifest.json`](fulltext/manifest.json) records each URL, size, sha256 and date.

Rows marked **FT** were checked against the full text; rows marked *abs.* rest on the abstract or a search
snippet only.

## Method families and where they are used

| # | Method family | What it resolves | Used in the literature for (source) | Doser question it could answer | Open-source codes |
|---|---|---|---|---|---|
| 1 | **Soft-sphere DEM** with Hertz–Mindlin contact, rolling resistance and a cohesion law (SJKR, JKR, EEPA, van der Waals) | Every grain and contact | Screw dosing of cohesive cocoa powder, calibrated on friction and cohesion; upscaled particles; reproduces small doses, over-predicts arching at larger ones: Imole et al. 2016, MercuryDPM (**FT**). Feeder with agitator, EDEM, HM+JKR, coarse-graining cited: *Sci. Rep.* 2024 (**FT**). Inclined screw conveyors at 30° and 60°, throughput within 16 % and 24 % of experiment: Owen & Cleary (*abs.*) | The auger twin itself (#180); mg/rev vs tilt; afterflow; the core-tip annulus | LIGGGHTS, LAMMPS, MercuryDPM, Yade, Chrono |
| 2 | **DEM calibrated on standard tests** | Contact parameters from bulk tests | Surface energy of 34 µm Ti-6Al-4V (γ ≈ 0.1 mJ/m²) from funnel angle of repose; AoR more sensitive to γ than to stiffness, friction or restitution: Meier et al. 2019, in-house BACI (**FT**). Surface energy plus sliding and rolling friction from dynamic yield strength and a 20,000-particle shear cell, EDEM HM+JKR; the shear cell alone could not fix the friction pair: Karkala et al. 2019 (**FT**). Angle of repose and uniaxial compression gave different rolling-friction values (≈5×10⁻⁵ vs 0.33) for the same powder, so one JKR parameter set could not match both: Lupo et al. 2021 (**FT**). Tapped density by repeated 3 mm drops every 0.24 s with EEPA cohesion: EDEM Powders Starter Pack (*abs.*) | Which tests to measure so the inference is identifiable | same as 1 |
| 3 | **DEM with liquid bridges** (Willett, Rabinovich, Weigert, Bagheri) | Capillary force vs gap and liquid volume | Four bridge models compared in Yade in a split-bottom shear cell: Gladkyy & Schwarze 2014 (**FT**). Classical Willett and the Bagheri approximation added to MercuryDPM (LiquidBridgeWillet, LiquidBridgeClassicalWillet, LiquidBridgeBagheri): Bagheri, Roy & Pöschel 2024 (**FT**). Wet polypropylene powders calibrated on the dynamic angle of repose in a rotating drum, with particle scaling l = 3 and 5 and the maximum bridge volume as the fitted knob: Pourandi et al. 2025, MercuryDPM (**FT**). Caking under humidity cycles by capillary condensation: *EPJ Web Conf.* 2017 (*abs.*; its PDF could not be captured through the Pi). Humidity entered as a granular Bond number for lactose and Avicel at 20–60 % RH in hoppers: Chaudhuri group, AIChE 2016–17 (*abs.*) | Sterling's "dose before and after humid air" test; hygroscopic salts (BaCl₂ caking in #116) | Yade, MercuryDPM, LIGGGHTS (`cohesion easo/capillary/viscous`) |
| 4 | **DEM with tribocharging** (condenser model, Coulomb and image forces) | Charge per contact, long-range forces | CFD–DEM with the condenser model in pneumatic conveying; charge drives rings, clusters and plugs: Huang et al. 2023 (*abs.*). Charge-transfer limit and efficiency measured for DEM models; 2D fails for multi-contact systems: Rasera et al. 2022–23 (*abs.*). Work-function condenser model validated on pharmaceutical powders: Chaudhuri, AIChE 2018 (*abs.*). Tribocharging, dielectrophoresis and van der Waals forces added to EDEM for lunar regolith handling: Hogue, Calle, Weitzman & Curry, NASA KSC with DEM Solutions (**FT**) | Salt sticking to the auger in the glove box (#117); grounding (#84); argon vs air | LAMMPS (`granular` + `coul/*`), self-written |
| 5 | **Coarse-grained / scaled DEM** | Parcels standing for many grains | Particle scaling in screw dosing: Imole et al. 2016 (**FT**). Scaling factors 3 and 5 with liquid bridges, agglomeration amplified at high liquid content: Pourandi et al. 2025 (**FT**). Multi-level coarse-graining of hopper-screw feeders cited by *Sci. Rep.* 2024 (**FT**) | Fine metal powders (AlSi10Mg, 35 µm): about 10⁹ grains per auger (#180) | all DEM codes |
| 6 | **Non-spherical DEM** (multi-sphere clumps, superquadrics) | Grain shape | Cubes, cuboids and cylinders as superquadrics and multi-spheres; rolling friction can stand in for shape, at about half the estimated value: Soltanbeigi et al. 2021 and a companion paper (*abs.*). Superquadrics in LIGGGHTS verified on AoR and hopper discharge: Podlozhnyuk et al. 2017 (*abs.*). Multi-sphere 70 µm AM particles in a powder bed: Haeri et al. 2018 (**FT**, extended abstract) | Cubic salt crystals vs spherical atomized metal | Yade (clumps), LIGGGHTS (superquadric builds), LAMMPS (rigid bodies) |
| 7 | **DEM–FEM coupling** | Grains plus a deforming tool | Roller spreading of 0–20 µm Ti-6Al-4V with counter-rotation and oscillation, packing 50–60 % in one layer: Weissbach et al. 2023, BACI (now 4C) (**FT**) | Spreadability tests with a wiper (meeting point 6) | 4C, Chrono (FEA + SMC) |
| 8 | **CFD–DEM** | Gas–particle drag | Condenser-model charging in pneumatic conveying: Huang et al. 2023 (*abs.*) | Fine powder falling from the exit; dust; spreading of < 20 µm powders | MFiX, CFDEMcoupling |
| 9 | **Non-smooth contact dynamics** | Rigid grains, exact Coulomb friction | Reference discrete solution for 2D silo discharge (W = 90d and 180d) against the μ(I) continuum: Staron, Lagrée & Popinet 2014 (**FT**) | Orifice discharge benchmark | LMGC90, Siconos |
| 10 | **μ(I) visco-plastic continuum** (Navier–Stokes with a granular viscosity) | Flow field without grains | 2D silo discharge in the Gerris VOF solver recovers Beverloo scaling; slow creep zones are not captured: Staron, Lagrée & Popinet 2014 (**FT**). Abaqus FEM with the non-local model: Henann & Kamrin 2013, cited by Dunatunga & Kamrin (**FT**) | Fast forward model of exit flow vs tilt | Basilisk/Gerris, OpenFOAM |
| 11 | **Material point method** (elasto-viscoplastic, Drucker–Prager or μ(I)) | Large-deformation continuum | μ(I) elasto-viscoplastic MPM with a yield criterion and separation into a disconnected phase; validated on the static repose angle of collapsing heaps, Beverloo scaling in plane-strain silos (Q = Cρ√g (D − kd)^3/2) and steady chute-flow profiles: Dunatunga & Kamrin 2015 (**FT**). Semi-implicit MPM with exact Drucker–Prager: Daviet & Bertails-Descoubes 2016 (*abs.*) | Column collapse ≈ angle of repose; hopper discharge | Taichi, Uintah, CB-Geo MPM |
| 12 | **SPH for granular flow** | Mesh-free continuum | Drucker–Prager / Mohr–Coulomb SPH column collapses (cited by the MPM papers, *abs.*) | Same as 11 | PySPH, DualSPHysics |
| 13 | **FEM with Mohr–Coulomb / Drucker–Prager plasticity** | Stress field, failure | Hopper and silo stress design; Jenike-type arching (textbook) | Does an arch hold over the 3 mm exit? | FEniCSx, scikit-fem |
| 14 | **Non-local granular fluidity** | Size effects in thin layers | Kamrin & Koval 2012; Henann & Kamrin 2013 (textbook) | Thickness-dependent stopping angle (h_stop) in a 1–2 mm annulus | self-written |
| 15 | **Reduced-order and closed-form models** | Bulk balances | Beverloo/Hagen orifice discharge; Jenike critical outlet from the flow function; Janssen; screw volumetric efficiency (Roberts; Owen & Cleary) | Baseline and prior for the BO and the inference | self-written |
| 16 | **Cellular automata / sandpile** | Avalanches, intermittency | BTW/Oslo sandpiles (textbook) | Interruption fraction I_stop | self-written |
| 17 | **Monte Carlo / geometric packing** | Packing fraction from a PSD | Random sequential addition, drop-and-roll, Lubachevsky–Stillinger (textbook) | Bulk vs tapped density, Hausner ratio from a measured PSD | self-written |
| 18 | **Moisture sorption + capillary cohesion** | Water uptake vs time and RH | GAB/BET isotherms, Kelvin condensation (EPJ 2017, *abs.*) | Humid-air exposure test; RH logging | self-written |
| 19 | **Bayesian calibration with sequential Monte Carlo** | Posterior over contact parameters | GrainLearning: iterative Bayesian filtering, RNN surrogates; used against angle of repose, shear cell and sintering in particle technology: Cheng et al. 2024 (**FT**) and 2019 (*abs.*) | The inference step itself (§2.6 of the draft) | GrainLearning |
| 20 | **Surrogate (emulator) + MCMC or Bayesian optimization** | Cheap stand-in for DEM | Surface energy and rolling resistance by Bayesian optimization against void ratio (Katagiri et al., *abs.*); surrogate optimization on ring shear and consolidation (Mohajeri et al. 2021, *abs.*); regression surrogates over ≥ 10 parameters (Forgber, Khinast & Fink, *abs.*) | Same, with fewer 30-min DEM runs | scikit-learn, GPyTorch, BoTorch, emcee |
| 21 | **Learned graph-network simulators** | Particle trajectories from data | Differentiable GNS (reverse-mode autodiff through the learned simulator) inverts material properties and boundary conditions from a target runout, with orders of magnitude faster convergence than finite-difference gradients: Choi & Kumar 2024 (**FT**); multi-layer slopes, up to 145× faster than MPM: Choi, Macedo & Liu 2025 (*abs.*) | Fast, differentiable doser surrogate (future) | GNS (PyTorch) |

## What the full texts add for this project

- **Screw dosing of cohesive powder has been simulated, but not inverted.** Imole et al. calibrated friction and
  cohesion by hand on other tests, then predicted the dosing. None of the papers found uses a feeder's own output to
  infer powder properties, which is the paper's claim. The closest is drum-based calibration (Pourandi et al.) and
  funnel/AoR-based calibration (Meier et al.).
- **One test is not enough.** Karkala et al. needed the shear cell *and* dynamic yield strength to pin down
  sliding and rolling friction; Lupo et al. could not match angle of repose and unconfined yield strength with one
  JKR parameter set. For the doser this argues for inferring from the tilt sweep **plus** at least one more
  observable (mass per tap, afterflow, or a measured AoR or tapped density).
- **Surface energy dominates fine metal powders.** Meier et al. found AoR far more sensitive to surface energy than
  to stiffness, friction or restitution for 34 µm Ti-6Al-4V, and give γ ≈ 0.1 mJ/m² as typical.
- **Moisture is a calibrated liquid-bridge volume, not a first-principles input.** Pourandi et al. fit the maximum
  bridge volume to drum data and found particle scaling amplifies agglomeration at high liquid content.
- **Codes.** MercuryDPM (Imole, Pourandi, Bagheri) and Yade (Gladkyy) are the open-source DEM codes with the most
  complete wet-contact models; EDEM dominates the shear-cell and feeder papers; spreading papers use in-house
  DEM–FEM (BACI/4C).

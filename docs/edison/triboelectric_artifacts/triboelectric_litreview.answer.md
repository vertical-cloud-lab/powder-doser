# Triboelectric Contact Charging in DEM-Based Digital Twins for Powder Dosing: A Comprehensive Literature Review and Implementation Guide

## 1. Verification of the Core Claim

The prior review's conclusion is **substantively correct**: none of the mainstream granular/robotics simulation engines (LIGGGHTS, MercuryDPM, Yade, Project Chrono, Altair EDEM, Ansys Rocky, NVIDIA Isaac Sim/PhysX, or GPU-based differentiable solvers) ships a built-in, calibrated tribocharging capability as a standard feature. Every published DEM tribocharging study identified in this review implemented charging via user-defined modifications, custom contact models, or in-house research codes (wang2022investigatingparticleparticleelectrostatic pages 2-3, hogue2008calculatingthetrajectories pages 6-7, hogue2008calculatingthetrajectories pages 1-2, sippola2018experimentalandnumerical pages 3-5). However, **published charge models can be imported** into several of these engines, and the literature provides a clear (if labor-intensive) path to do so.

---

## 2. Catalogue of Particle-Scale Charge-Transfer Models

### 2.1 Condenser / Capacitor Model (Matsusaka, Masuda, Matsuyama, Ghadiri)

The foundational model treats the contact region as a parallel-plate capacitor. The charge transferred per contact is:

**Δq = k_c · (ε₀ · A / z_c) · V**

where k_c is the charging efficiency (0 < k_c ≤ 1), ε₀ is the vacuum permittivity, A is the maximum Hertzian contact area, z_c is the critical charge-transfer gap (~1 nm), and V is the total potential difference comprising contact potential difference V_c, image-charge potential V_im, space-charge potential V_sp, and any external field V_ex (mirkowska2016principalfactorsof pages 6-8, chowdhury2021cfdsimulationof pages 187-190). The Hertzian contact area scales as A ∝ r² · v_i^(4/5), linking charge transfer directly to impact velocity and particle radius (sitaraman2025triboplasmaassistedchemical pages 3-6). With repeated impacts, charging follows exponential saturation toward an equilibrium charge q_∞ (chowdhury2021cfdsimulationof pages 187-190).

**DEM inputs required:** Normal overlap δ_n (to compute Hertzian contact area), impact velocity v_i, particle radius, initial charge, local electric field.

**Material parameters:** Effective work functions (or contact potential difference V_c), Young's moduli, Poisson ratios, charging efficiency k_c, critical gap z_c. Work functions are measured by Kelvin probe or calibrated from Faraday-cup charge-to-mass data (sippola2018experimentalandnumerical pages 3-5).

**Validation:** Single-impact rigs (Matsuyama), pneumatic conveying charge-to-mass (chowdhury2021cfdsimulationof pages 187-190), vibrated beds.

**Failure modes:** Assumes smooth surfaces; neglects roughness effects on real contact area; k_c and z_c are poorly constrained empirically (jantac2025triboelectricchargingmodel pages 1-5).

### 2.2 Charge-Relaxation / Gas-Discharge-Limited Model (Matsuyama & Yamamoto)

This model recognizes that the dominant charge-transfer event occurs during **separation**, not contact. Upon separation, the surface potential rises as capacitance drops. If the potential exceeds the Paschen breakdown curve B_p(z) for the ambient gas, gas discharge clamps the charge. The post-separation residual charge is determined by the tangent point where the potential curve contacts the Paschen curve (matsusyama2006impactchargingof pages 1-2, sitaraman2025triboplasmaassistedchemical pages 3-6):

**q_f · z / [2πε₀ r(r + 2z)] = B_p(z)**

where B_p(z) = V_min · (p·z / p·d_min) / [1 + ln(p·z / p·d_min) / B(p·z)] with V_min the minimum breakdown voltage and p·d_min the pressure-gap product at that minimum (sitaraman2025triboplasmaassistedchemical pages 3-6).

**DEM inputs:** Same as condenser model plus gas pressure and composition.

**Critical for the user's application:** In dry argon (glovebox), the dielectric strength is ~0.6 kV/mm versus ~3.25 kV/mm for air at 1 atm and 20°C, with Paschen parameters A = 13.6, B = 235 for argon versus A = 14.6, B = 365 for air (syed2026influenceofargona pages 72-76, syed2026influenceofargon pages 72-76). This means maximum sustainable particle charge in argon is **substantially lower** than in air—particles will discharge at lower potentials, potentially reducing but not eliminating charging problems.

### 2.3 Trapped-Electron / Size-Dependent Bipolar Charging (Lacks and co-workers)

For same-material insulator contacts, Lacks proposed that electrons trapped in high-energy surface states transfer preferentially from smaller to larger particles during contact, producing size-dependent bipolar charging (small particles negative, large positive) (mizzi2019doesflexoelectricitydrive pages 1-6). The density of trapped electrons at each depth accounts for the charge transfer. However, Waitukaitis et al. showed experimentally that thermoluminescence-measured trapped-electron densities are **orders of magnitude too small** to account for observed charge magnitudes, suggesting ions rather than trapped electrons may be responsible (mizzi2019doesflexoelectricitydrive pages 1-6).

**Relevance:** This model matters for same-material particle-particle contacts in polydisperse powders. For the user's system, it is secondary to particle-wall charging.

### 2.4 Mosaic / Patch / Stochastic Models (Baytekin & Grzybowski; Grosjean & Waitukaitis; Grosshans SSM)

Baytekin et al. demonstrated that contact-electrified surfaces exhibit a nanoscale mosaic of positive and negative charge patches, with material transfer playing a key role. Grosjean and Waitukaitis extended the mosaic framework analytically, incorporating global differences in donor/acceptor site densities to connect deterministic different-material charging to stochastic same-material charging (grosshans2026unifyingsameand pages 2-3).

The **Stochastic Scaling Model (SSM)** of Grosshans et al. (2026) represents the most simulation-ready stochastic framework. It characterizes impact charge as a random variable with experimentally determined mean μ₀, standard deviation σ₀, skewness γ₀, and minimum charge from a controlled reference experiment. These statistics are scaled to each collision using Hertzian contact area ratios, surface-site depletion, and local electric field suppression (grosshans2026unifyingsameand pages 1-2, grosshans2026unifyingsameand pages 6-7):

- **μ_w = Δq₀,min · (N_w/N_w0)**  
- **σ_i = σ₀ · √(N_i/N₀)**  
- **γ_i = −γ₀ · √(N₀/N_i)**

where N_i/N₀ scales with contact area ratio A/A₀, charging-site depletion c/c₀, and field-suppressed activity α/α₀ (grosshans2026unifyingsameand pages 6-7). The SSM was implemented in the open-source pafiX solver, consuming <0.01% of CPU time for 300,000 particles (grosshans2026unifyingsameand pages 1-2).

### 2.5 Flexoelectric Model (Mizzi & Marks)

Mizzi and Marks proposed that inhomogeneous strain gradients at nanoscale asperity contacts produce flexoelectric polarization, generating local potential differences of ±1–10 V that drive charge separation (mizzi2019doesflexoelectricitydrive pages 1-6, mizzi2019doesflexoelectricitydrive pages 7-11). The constitutive relation is:

**E_z = −f · (effective strain gradient)**

where f is the flexocoupling voltage. The strain gradient scales as ~ε/R for an asperity of radius R, so flexoelectric potentials increase at smaller contact scales (olson2025istriboelectricityconfusing pages 42-45, olson2025istriboelectricityconfusing pages 12-15). This explains charging between identical materials, force-dependent currents, bipolar stick-slip charging, and curvature effects.

**DEM relevance:** Currently a mechanistic explanation rather than a ready-to-implement simulation model; could be approximated by computing strain gradients from Hertzian contact mechanics at each collision.

### 2.6 Ion/Water-Mediated Transfer (McCarty & Whitesides)

McCarty and Whitesides proposed that hydroxide ions partition within thin water layers between contacting insulators, with ion transfer governed by acid-base chemistry rather than electron transfer. Humidity strongly modulates this mechanism. This model is most relevant for polymer-polymer contacts at ambient humidity and becomes less relevant in a dry argon glovebox where adsorbed water layers are negligible.

### 2.7 Rough-Surface Extension (Jantač et al. 2025)

Jantač et al. combined Hertzian contact mechanics with measured surface-roughness statistics (power spectra from confocal microscopy) to predict the real contact area of rough particles, which is then fed into the condenser model (jantac2025triboelectricchargingmodel pages 1-5). The model uses standard surface descriptors (R_q, Hurst exponent) and demonstrated good agreement with shaker experiments on polyethylene particles. This is directly relevant to the user's system since gas-atomized metal powders and FDM-printed polymer walls both have significant surface roughness.

---

## 3. Existing Simulation Implementations

### 3.1 Survey of Published Implementations

| Study | Host Code | Charge Model | Electrostatic Force Method | Walls | Code Available? | Validation |
|-------|-----------|-------------|--------------------------|-------|----------------|------------|
| Hogue et al. 2008 | EDEM (commercial API) | Prescribed q/m | Screened Coulomb pairwise | Not detailed | No (custom EDEM plugin) | Qualitative trajectory comparison with glass spheres (hogue2008calculatingthetrajectories pages 6-7, hogue2008calculatingthetrajectories pages 1-2) |
| Pei, Wu & Adams 2014 | In-house DEM-CFD | Condenser + relaxation | Direct pairwise with cutoff | Charge-accumulating | No | Rotating drum, vibrated bed (chowdhury2021cfdsimulationof pages 197-201) |
| Sippola, Kolehmainen et al. 2018 | OpenFOAM-DEM (custom) | Laurentie condenser model: Δq/ΔA = ε[Δϕ/(δ_c e⁺) + E·n] | Hybrid PP-PM (particle-particle/particle-mesh) | Insulating walls with surface charge | Not publicly released | Wall sheeting, pressure drop vs. experiment at 0–60% RH; q/m calibrated via Faraday cup (sippola2018experimentalandnumerical pages 5-6, sippola2018experimentalandnumerical pages 13-16, sippola2018experimentalandnumerical pages 3-5) |
| Wang et al. 2022 | LIGGGHTS (modified) | Condenser model + conduction | Coulomb pairwise ± Debye screening with cutoff | Grounded via image charges | Source modifications not released | Lunar dust trajectories (wang2022investigatingparticleparticleelectrostatic pages 2-3, wang2022investigatingparticleparticleelectrostatic pages 3-4) |
| Grosshans et al. 2025–2026 | pafiX (open-source) | SSM stochastic scaling; also condenser variants | Hybrid near-field Coulomb + far-field Gauss's law | Conducting walls with image charges | **Yes** (open-source) | Pneumatic conveying charge patterns, 300k particles (ozler2025secondaryflowsdrive pages 5-7, grosshans2026unifyingsameand pages 18-19, grosshans2026unifyingsameand pages 1-2) |
| Jantač et al. 2025 | CFD-Lagrangian | Condenser + rough-surface correction | Hybrid Grosshans-Papalexandris | — | Model equations published | PE shaker experiments (jantac2025triboelectricchargingmodel pages 1-5) |
| Giordano et al. 2025 | DEM (unspecified) | Condenser + effective dipole polarization | Pairwise + induced dipole | — | Equations published | Binary-mixture shaker aggregation (giordano2025effectivedipolemodel pages 10-11) |
| Chowdhury 2021 | CFD-DEM (unspecified) | Condenser with wall charging | Direct pairwise O(N²) or cell-hybrid O(NM) | Insulating, charge-accumulating | No | Fluidized bed wall sheeting (chowdhury2021cfdsimulationof pages 74-76) |

### 3.2 Key Finding

The Kolehmainen et al. (2016) hybrid PP-PM method is the most sophisticated published electrostatic solver for DEM, combining direct pairwise near-field forces with a mesh-based Poisson solve for far-field contributions, handling insulating wall boundary conditions. It scales as O(NM) where M is the number of mesh cells, making it tractable for ~10⁵ particles (chowdhury2021cfdsimulationof pages 197-201, pei2014demcfdanalysisof pages 77-82). The Grosshans hybrid (near-field Coulomb + far-field Gauss) in pafiX offers a similar approach with open-source availability (ozler2025secondaryflowsdrive pages 5-7, grosshans2026unifyingsameand pages 18-19).

---

## 4. Engine Extensibility for Hosting an Imported Charge Model

| Engine | Per-Particle Charge State | Contact History | Long-Range Coulomb | GPU Support | Wall Charge on STL | Electrostatic Precedent | Licence |
|--------|--------------------------|----------------|-------------------|-------------|-------------------|----------------------|---------|
| **LIGGGHTS-PUBLIC** | Yes (fix property/atom) | Yes (contact model history) | Pairwise with cutoff only; no kspace | No native GPU | Via fix mesh; limited | Wang 2022, Kassem 2021 auger DEM | GPL |
| **LAMMPS GRANULAR** | Yes (atom_style charge) | Yes (pair_style gran/hertz/history) | **PPPM, Ewald, MSM via kspace** | Yes (GPU, KOKKOS packages) | Limited (fix wall) | Molecular Coulomb; no granular tribocharging published | GPL |
| **EDEM (Altair)** | Yes (custom property API) | Yes (contact model API) | Custom body force only; no built-in kspace | GPU solver for contact | Yes (custom property on mesh) | Hogue 2008 | Commercial |
| **MercuryDPM** | Extensible via species/interaction classes | Yes | User-implemented | Limited | User-implemented | Charged-species class exists | BSD |
| **Yade** | Via custom Python attrs | Law2 functors | User-implemented | No | User-implemented | Limited published work | GPL |
| **Project Chrono DEME** | Yes (per-particle "wildcard" floats, JIT custom kernels) | Per-contact wildcards | User-implemented in CUDA | **Native GPU (CUDA)** | Via mesh elements | No electrostatic precedent published | BSD |
| **MFiX-DEM** | User-defined particle properties | Yes | User-implemented | Partial (GPU MFiX) | Via STL boundaries | Eulerian charging models (Ray/Sundaresan) | Open-source |
| **NVIDIA Isaac/PhysX PBD** | No persistent per-particle scalar state | No per-contact history | No Coulomb solver | GPU native | No charge state | None | Proprietary |
| **pafiX** | Yes (Lagrangian particle charge) | Collision-based | Hybrid Coulomb+Gauss | CPU (MPI parallel) | Image charges at walls | **Grosshans SSM 2026** | Open-source |

### Assessment for the User's Application

**LAMMPS GRANULAR** offers the strongest infrastructure: native per-particle charge (`atom_style charge`), contact history, mature kspace solvers (PPPM/Ewald) that handle long-range Coulomb at O(N log N) cost with GPU acceleration, and an open-source licence. The missing piece is the tribocharging contact model itself, which must be added as a custom `pair_style` or `fix` (wang2022investigatingparticleparticleelectrostatic pages 3-4, pei2014demcfdanalysisof pages 77-82).

**Project Chrono DEME** is attractive for GPU-native simulation with JIT-compiled custom force models supporting per-particle and per-contact wildcard state, but lacks any published electrostatic precedent.

For **position-based robotics engines** (NVIDIA Isaac/PhysX), particle-level tribocharging is impractical. A reduced-order approach tracking lumped charge on containers/surfaces with an ODE, applying effective adhesion or retained-mass corrections to the particle dynamics, would be the appropriate strategy. No published implementation of this approach was found.

---

## 5. Numerical and Scaling Issues

**Time-step constraints:** The DEM time step must remain below ~20% of the Rayleigh critical time step for contact stability (kassem2021asemiautomateddem pages 5-6). Electrostatic forces do not independently constrain the time step unless they dominate contact forces, but charge update should occur every contact step.

**Cut-off errors:** Direct pairwise Coulomb with a cut-off distance systematically underestimates long-range interactions and can introduce artifacts in dense systems (pei2014demcfdanalysisof pages 77-82). The PP-PM hybrid or PPPM/Ewald methods are strongly preferred for systems with >10⁴ charged particles.

**Image charges and polarization:** For conducting metal particles (oxide-skinned but conductive beneath), image-charge interactions at grounded metal walls and between contacting conductors can dominate at close range. Giordano et al. (2025) proposed an effective dipole model that captures polarization-induced attraction between like-charged particles in closed form, suitable for DEM (giordano2025effectivedipolemodel pages 10-11). Charge sharing between contacting conductors requires explicit modeling.

**Coarse-graining:** No published coarse-graining rules exist specifically for charged DEM. The standard approach preserves charge-to-mass ratio (q/m) on coarse-grained parcels, but this does not simultaneously preserve the Coulomb-to-gravity or Coulomb-to-van-der-Waals force ratios. The scaling factor S³ for particle count reduction (kassem2021asemiautomateddem pages 1-2) would require careful reformulation of both charging rate (proportional to contact area, which scales differently) and Coulomb force. **This is an open problem.**

**Differentiable implementations:** No differentiable tribocharging model was identified in the literature. Differentiable particle simulators (Taichi, Warp, DiffSim) do not include electrostatics.

---

## 6. Effects Most Relevant to Gravimetric Dosing

### 6.1 Wall Adhesion and Retained Mass

Sippola et al. demonstrated experimentally and numerically that tribocharging in a polyethylene fluidized bed produces wall sheeting—stationary particle layers adhering to insulating walls—and associated pressure-drop reduction. The effect is strongly humidity-dependent: dry conditions (0% RH) produce the strongest positive charging and most severe wall adhesion (sippola2018experimentalandnumerical pages 13-16, sippola2018experimentalandnumerical pages 3-5). This directly translates to the user's dosing application: charged powder adhering to auger screw surfaces, hopper walls, and scoops will cause dose-to-dose variability and systematic under-dosing.

### 6.2 Electrostatic Weighing Errors

Electrostatic charge on powders or containers produces **image forces to the balance pan and draft shield** that bias analytical balance readings. The literature universally acknowledges this effect as significant for milligram-scale weighing (tiwari2025anelectronicanalytical pages 4-5, tiwari2025anelectronicanalytical pages 2-3), and recommends ionizers, antistatic weigh boats, metal containers, grounding, and humidity control (40–60% RH) as mitigations (tiwari2025anelectronicanalytical pages 2-3). However, **no published study was found that quantitatively models or simulates the balance-reading error caused by charged powder**, nor provides a calibrated error magnitude as a function of charge level. This is a significant gap. A rough estimate: a charge of ~1 nC on a 10 mg sample at ~10 mm from a grounded pan produces an image force of order ~1 μN, corresponding to ~0.1 mg apparent mass error—significant at the milligram dosing scale.

### 6.3 Flow-Rate Drift

Allenspach et al. documented that electrostatic charge affects loss-in-weight feeder performance, with charge buildup during feeding contributing to flow-rate variability (tiwari2025anelectronicanalytical pages 4-5). Over repeated doses, polymer wall charging would accumulate (with slow dissipation on insulating PLA/PETG), progressively altering adhesion and flow patterns.

---

## 7. Calibration and Validation Protocols

### 7.1 Recommended Low-Cost Measurements

1. **Faraday-cup charge-to-mass (q/m):** Dispense powder through the actual dosing device into a Faraday cup connected to an electrometer/nanocoulomb meter. Measure q/m of dispensed doses at multiple operating conditions (speed, humidity). This is the primary calibration target (sippola2018experimentalandnumerical pages 13-16, galindo2024amethodto pages 7-10).

2. **GranuCharge or equivalent tribocharger:** Standardized V-tube or drum tribocharger for systematic material characterization. Galindo et al. demonstrated this for AlSi10Mg and Ti6Al4V (galindo2024amethodto pages 7-10, galindo2024amethodto pages 12-14).

3. **Kelvin-probe work function:** Scanning Kelvin probe on flat specimens of printed polymers (PLA, PETG, nylon) and polished metal powder compacts to measure effective contact potential differences.

4. **XPS surface analysis:** Characterize oxide composition of metal powder surfaces (Al₂O₃ thickness on AlSi10Mg, TiO₂ on Ti, SiO₂ on Si) (ramirez2026influenceofpowder pages 102-109).

5. **Surface resistivity of printed parts:** Four-point probe or ring electrode measurement to determine charge dissipation rate on FDM walls; critical for distinguishing insulating (PLA, PETG) from ESD-safe filaments.

6. **Electrostatic field meter:** Non-contact measurement on hopper/screw surfaces during operation.

### 7.2 Inverse Calibration

Sippola et al. calibrated effective work-function differences by interpolating to match experimentally measured q/m at multiple relative humidities (sippola2018experimentalandnumerical pages 13-16). The SSM requires only a single controlled reference-impact experiment to obtain (μ₀, σ₀, γ₀, Δq₀,min) (grosshans2026unifyingsameand pages 1-2). For the user's system, a Bayesian optimization or CMA-ES approach over the parameter space (V_c, k_c, z_c) fitting Faraday-cup q/m data from the actual dosing device would be appropriate; Kassem et al. demonstrated analogous DoE-based calibration of DEM mechanical parameters for auger dosing using LIGGGHTS (kassem2021asemiautomateddem pages 5-6, kassem2021asemiautomateddem pages 1-2).

---

## 8. Material-Specific Data for the User's System

### 8.1 Oxide-Skinned Metal Powders

**AlSi10Mg:** Al₂O₃/AlOOH surface skin; charges negatively against stainless steel with accumulated charge density −2.80 to −5.70 nC/m²; D50 ~ 55 μm; charging rate depends on flow rate (ramirez2026influenceofpowder pages 109-116, galindo2024amethodto pages 7-10, galindo2024amethodto pages 12-14).

**Ti6Al4V:** TiO₂ surface skin with work function 5.0–5.5 eV; charges negatively at −2.52 to −3.23 nC/m² against SS; D50 ~ 36 μm (ramirez2026influenceofpowder pages 109-116, galindo2024amethodto pages 7-10).

**Si (high-purity):** Native SiO₂ skin. No tribocharging data found in the surveyed literature for gas-atomized Si powder. SiO₂ has a work function of ~5 eV and is a good insulator, suggesting strong charging potential. **This is a data gap requiring measurement.**

### 8.2 FDM Polymers

**No published tribocharging data were found for FDM-printed PLA, PETG, or nylon surfaces.** These polymers are expected to be strongly insulating (surface resistivity >10¹² Ω/sq for PLA/PETG), meaning charge will accumulate with very slow dissipation. PLA, PETG, and nylon occupy different positions in the triboelectric series relative to metals and metal oxides, but their effective work functions for FDM-printed surfaces (which may differ from injection-molded due to porosity, crystallinity, and surface roughness) are unmeasured. Carbon-loaded ESD-safe filaments typically reduce surface resistivity to 10³–10⁶ Ω/sq, providing a charge dissipation path.

---

## 9. Mitigation Levers a Twin Could Evaluate

| Mitigation | Mechanism | Simulatable? | Notes |
|-----------|-----------|-------------|-------|
| ESD/conductive filament | Reduces surface resistivity → faster charge dissipation | Yes (via charge leakage time constant) | Reduces V_c and charge accumulation |
| Grounded copper-tape liner | Provides conductive path; wall treated as grounded conductor with image charges | Yes (grounded-wall boundary condition) | Eliminates wall charge accumulation; image charges remain |
| Material selection (minimize ΔV_c) | Choose wall material closer to powder in triboelectric series | Yes (change V_c parameter) | Requires Kelvin-probe measurement |
| Humidity control | Increases surface conductivity; modulates ion-mediated transfer | Partially (via RH-dependent effective work function) | Not available in Ar glovebox |
| Ionizer at outlet | Neutralizes airborne charge | Via post-simulation correction | Difficult to simulate in DEM |
| Vibration/tapping schedule | Detaches adhered particles | Yes (DEM vibration + electrostatic adhesion) | Can be directly simulated |
| Surface texture | Modifies real contact area | Yes (via rough-surface charging model) | Jantač model applicable |

**Simulation ranking of mitigations:** No published study was found that uses DEM simulation to systematically rank multiple mitigation strategies against experimental results for powder dosing. Sippola et al. demonstrated that simulation can capture the effect of charge level on wall sheeting (sippola2018experimentalandnumerical pages 13-16), suggesting that material-change and grounding scenarios are rankable in principle.

---

## 10. Recommendation

### 10.1 Recommended Path

**Primary engine: LAMMPS GRANULAR** (or LIGGGHTS as a granular-optimized fork).

- LAMMPS provides native `atom_style charge`, contact history for Hertz-Mindlin, mature PPPM/Ewald kspace solvers with GPU acceleration, and an enormous user/developer community. LIGGGHTS adds granular-specific features (mesh import, coarse-graining) and has published auger-dosing precedent (kassem2021asemiautomateddem pages 5-6).

**Charge model to import: Condenser model with charge-relaxation (Matsuyama-Yamamoto) for particle-wall contacts** as the primary deterministic model, with the option to add the Grosshans SSM for stochastic variance.

- The condenser model is the most widely implemented and validated in DEM (chowdhury2021cfdsimulationof pages 187-190, sippola2018experimentalandnumerical pages 5-6, sippola2018experimentalandnumerical pages 3-5).
- Charge-relaxation with Paschen limit is essential for the argon glovebox scenario (sitaraman2025triboplasmaassistedchemical pages 3-6, syed2026influenceofargona pages 72-76).
- The SSM adds stochastic contact-to-contact variance at negligible computational cost (grosshans2026unifyingsameand pages 1-2).

**Electrostatic force computation: Hybrid PP-PM** (direct Coulomb for neighbors within a cutoff + mesh Poisson solve for far-field), following Kolehmainen et al. 2016 / Grosshans & Papalexandris 2017 (ozler2025secondaryflowsdrive pages 5-7). For LAMMPS, the built-in PPPM kspace solver with `pair_style coul/long` provides an alternative O(N log N) method with GPU support.

**Wall treatment:** Grounded metal walls/liners → image charges. Insulating polymer walls → charge-accumulating mesh elements with leakage rate proportional to surface conductivity.

### 10.2 What to Calibrate First

1. Measure Faraday-cup q/m of AlSi10Mg dispensed through the actual auger at 2–3 speeds and 2 humidities.
2. Measure Kelvin-probe work functions of printed PLA/PETG/nylon and of AlSi10Mg powder compact.
3. Measure surface resistivity of printed parts (with and without ESD filament).
4. Fit V_c and k_c by Bayesian optimization to match measured q/m.

### 10.3 Expected Implementation Effort

- **Custom LAMMPS pair_style for tribocharging:** ~2–4 person-months for an experienced C++ developer familiar with LAMMPS internals. Must add per-contact charge-transfer logic to the granular contact model and couple to the charge degree of freedom.
- **Electrostatic solver integration:** If using built-in PPPM, minimal additional effort. If implementing PP-PM hybrid, ~1–2 additional months.
- **Wall charge tracking:** ~1 month for mesh-based charge state with leakage.

### 10.4 Expected Run-Time Cost

For an auger dosing simulation with ~10⁵ coarse-grained particles on a single modern GPU (e.g., NVIDIA A100):
- Without electrostatics: ~1–4 hours per design evaluation (several screw revolutions).
- With PPPM electrostatics: ~2–3× overhead, so ~3–12 hours per evaluation.
- The Bayesian optimizer evaluating ~50–100 candidates would require ~1–2 weeks of continuous GPU time, which is feasible.

### 10.5 Expected Fidelity

- **Charge-to-mass ratio:** Can be calibrated to match Faraday-cup measurements within a factor of ~2 based on published validation (sippola2018experimentalandnumerical pages 13-16, chowdhury2021cfdsimulationof pages 74-76).
- **Wall adhesion / retained mass:** Qualitatively captured; quantitative accuracy depends on charge distribution (which is sensitive to acceleration factors and model parameters) (sippola2018experimentalandnumerical pages 13-16).
- **Relative ranking of designs:** Likely reliable for comparing geometries and materials that differ primarily in contact frequency, contact area, or wall material, provided V_c values are measured.

### 10.6 Top Risks Where Simulation Would Misrank Designs

1. **Unknown FDM polymer work functions:** Without Kelvin-probe measurements for each filament, V_c is unconstrained, and material-swap rankings will be unreliable.
2. **Humidity transients:** The condenser model does not natively capture time-varying humidity effects; empirical RH-dependent V_c curves must be supplied.
3. **Charge distribution vs. uniform charge:** Simulations with uniform particle charge may miss bipolar charging and its effects on agglomeration (sippola2018experimentalandnumerical pages 13-16).
4. **Coarse-graining artifacts:** Charging rate scales with contact area, which is altered by coarse-graining in ways that are not rigorously understood for electrostatics.
5. **Balance weighing errors:** Cannot currently be simulated—this must be addressed experimentally with ionizers and grounding.
6. **Oxide-layer variability:** Tribocharging of metal powders is highly sensitive to surface oxide composition, which can vary between powder lots and with recycling history (ramirez2026influenceofpowder pages 231-233, ramirez2026influenceofpowder pages 122-127).

---

## Summary

Published tribocharging models—particularly the condenser/capacitor model with Paschen-limited charge relaxation and the newer stochastic scaling model—can be imported into open-source DEM engines (LAMMPS/LIGGGHTS being the most capable hosts), with hybrid electrostatic solvers providing tractable long-range force computation. The implementation requires custom code development (~3–6 person-months) and material-specific calibration via Faraday-cup and Kelvin-probe measurements. For the user's oxide-skinned metal powders against FDM polymer walls, the condenser model is the appropriate starting point, with the Paschen gas-discharge limit being particularly important for the argon glovebox environment where the lower dielectric strength of argon (~0.6 kV/mm vs. ~3.25 kV/mm for air) significantly alters the maximum particle charge (syed2026influenceofargona pages 25-29, syed2026influenceofargon pages 25-29). The largest knowledge gaps are the absence of published work-function data for FDM-printed polymers, the lack of validated coarse-graining rules for charged DEM, and the complete absence of any published simulation of electrostatic balance-reading errors.

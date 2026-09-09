Question: Context: we are building an open-source, low-cost powder doser for gravimetric metering of dry powders (ultimately metal additive-manufacturing feedstocks such as AlSi10Mg, silicon, stainless steel; salt and similar surrogates during development) inside an autonomous self-driving-lab alloy-discovery loop. The rig is an Archimedean auger in a tilted tube driven by a stepper motor (44:20 gear), a solenoid tapper that strikes the tube, and a servo-controlled tilt of the whole assembly (0-45 degrees from horizontal), dispensing into a vial on an analytical balance (A&D HR-100A, ~1 mg readability, ~1 s settling; readings during actuation are vibration-corrupted). Current controller: a deterministic three-phase policy (bulk feed at steep tilt -> fine incremental rotations -> tap-until-tolerance at shallow tilt), with per-phase parameters (tilt angle, rotation increment/speed, taps per cycle, settle time, gram-based phase-switch thresholds) intended to be tuned by contextual multi-objective Bayesian optimization. Objectives: absolute mass error (target +/- 1 mg, stretch +/- 0.1 mg) and dose time, with no-overshoot as a hard asymmetric constraint (powder cannot be removed). Context variables: hopper fill level, powder humidity-exposure history, ambient temperature. Empirically observed interactions: (a) tapping or rotating at steeper tilt dispenses far more per action than at shallow tilt; (b) a tap immediately after an auger rotation dispenses more than repeated taps alone, because taps deplete the loose powder near the tube lip while rotation replenishes it - i.e., the state includes an unobserved "lip reservoir" that actuators couple through.

Question: what existing physics-based simulation ENGINES could serve as a "digital twin" of powder flowing through and out of this tilted auger, so we can prototype and pre-tune dosing control policies in simulation before hardware runs? We are explicitly interested in video-game and animation-style physics engines (real-time or near-real-time, plausible rather than perfectly calibrated), not only research-grade codes. Please survey, with citations and links where possible, OPEN-SOURCE options in particular:

1. Game/animation-style engines with granular-material support: e.g., NVIDIA PhysX/Flex/Warp/Isaac Sim particle systems, Project Chrono (Chrono::Granular / Chrono::GPU), Bullet, MuJoCo (and its recent particle/deformable support), Taichi (MPM/DEM examples, e.g., taichi_elements), Blender's rigid-body/particle systems and Molecular add-on, Houdini-style grain solvers (POP grains / PBD) and position-based-dynamics libraries. For each: license, GPU support, particle counts achievable in near-real-time, contact model fidelity (friction, cohesion, rolling resistance), Python scriptability, and evidence of use for granular flow.

2. Research/engineering DEM codes usable as engines: LIGGGHTS/LAMMPS granular, YADE, Kratos DEM, MercuryDPM, MFiX-DEM, esyS-Particle, GranOO - same criteria, plus screw-conveyor/auger example cases if published.

3. Reduced/hybrid approaches for speed: continuum granular models, material-point method (MPM), position-based dynamics, cellular automata, and learned surrogates (graph-network simulators like DeepMind's GNS, NeuralDEM) that approximate DEM at a fraction of the cost - can they capture auger conveying and tap-induced avalanching well enough for control-policy pretraining?

4. Sim-to-real considerations for granular digital twins: DEM calibration of contact parameters against simple bench tests (angle of repose, drained mass flow), particle upscaling/coarse-graining (simulating 100-micron powder with mm-scale pseudo-particles), how sensitive auger mass-per-revolution and tap-triggered discharge are to calibration error, and published examples of tuning or verifying feeder/doser control policies in simulation before deployment.

5. Recommendation: a shortlist (2-3) of open-source engines best matched to "tilted auger + tube + solenoid taps + vial on balance" at engineering-workstation scale, and a suggested workflow coupling the engine to our Python control code (step the sim, command auger angle/tilt/tap impulses, read out dispensed mass).

## Scope and key requirement

A credible “digital twin” for a tilted-tube Archimedean auger with a solenoid tapper must reproduce **stateful outlet dynamics** (your empirically observed “lip reservoir”) and strong **actuation–geometry coupling** (tilt angle × rotation × tapping). This points to **granular-contact engines** (DEM) as the most faithful, with **graphics-style particle/continuum engines** (PBD, MPM) as fast approximations for policy prototyping and pretraining.

---

## 1) Game/animation-style engines with granular/particle support (open-source emphasis)

### A. Position-based dynamics / particle engines (plausible real-time)

**NVIDIA FleX (via SoftGym / PyFlex-style ecosystem)**

- Performance evidence: SoftGym reports simulations run **~4× faster than real time including rendering** on a single RTX 2080Ti; **1M steps in ~6 hours wall time**, corresponding to ≥35 hours of real robot time (lin2021softgymbenchmarkingdeep pages 2-5, lin2021softgymbenchmarkingdeep pages 5-7).
- Fit to auger dosing: Likely useful for **qualitative** regimes (tilt-dependent avalanching and agitation-triggered discharge), but less reliable for **mg-scale metering** because its contact/friction history modeling is not DEM-grade.

**PBD as an explicit contact-model class**

Differentiable-simulation literature treats **position-based dynamics (PBD)** as one of several major differentiable contact formulations, alongside LCP, convex optimization, and compliant contacts, supporting its use as a “game-like” contact approximation (zhong2207differentiablephysicssimulations pages 1-2).

### B. Material Point Method (MPM) engines (graphics + robotics; fast but continuum-ish)

**ChainQueen (MLS-MPM class; GPU)**

- Granular relevance: notes that MPM can simulate **granular materials like sand** (hu2019chainqueenarealtime pages 1-2).
- Speed evidence: reports **4–9× speedup** over previous state-of-the-art alternatives and efficient GPU forward+backprop (hu2019chainqueenarealtime pages 1-2).
- Fit: good for fast rollouts and differentiable tuning, but likely to blur discrete “lip reservoir refill/depletion” effects relative to DEM.

### C. Open-source differentiable-simulation ecosystem pointers

Reviews of differentiable simulators emphasize that simulators increasingly leverage GPUs for large numbers of fast rollouts and discuss contact-model tradeoffs (newbury2024areviewof pages 1-3, newbury2024areviewof pages 10-11). These are useful guides when selecting a GPU-first engine intended to couple tightly to Python control.

---

## 2) Research/engineering DEM codes usable as engines (open-source, granular fidelity)

### YADE (open-source DEM)

- Open-source DEM framework (kozicki2008anewopensource pages 1-2, kozicki2008anewopensource pages 14-15).
- Contact model fidelity evidence: supports **normal, tangential, and rolling contact stiffness**, plus friction and a rolling plastic limit coefficient (kozicki2008anewopensource pages 11-13).
- Granular validation example: triaxial “Labenne sand” simulation with **10,000 discrete elements** reproducing nonlinear stress–strain and dilatancy across confining pressures (kozicki2008anewopensource pages 11-13).
- Fit: strong for capturing the “lip reservoir” state as emergent particle configuration; well-suited to studying rotate→tap synergy.

### Why DEM matters vs typical game rigid-body engines

A calibration-focused DEM paper highlights that DEM differs from rigid-body dynamics (RBD) engines common in robotics/video games because DEM allows **inter-object penetration** for accurate contact behavior and keeps **stateful friction history** for hysteresis modeling, whereas RBD prioritizes speed over microscopic fidelity (nicusan2025accesnoninvasivesimulation pages 11-12). This is directly aligned with your observation that dosing depends on an unobserved state near the lip.

### LIGGGHTS / other DEM engines: calibration workflow evidence

ACCES (Python-based) targets autonomous calibration of DEM (including LIGGGHTS in their workflows) and explicitly calibrates **restitution** and **rolling/sliding/torsional friction** coefficients for both particle–particle and particle–wall contacts (nicusan2025accesnoninvasivesimulation pages 1-2, nicusan2025accesnoninvasivesimulation pages 28-31). This provides a concrete path to making a DEM twin quantitatively predictive for dosing.

*Note:* In this run, full-text evidence for screw-conveyor/auger example cases across LIGGGHTS/MercuryDPM/MFiX-DEM was not obtained, so auger-specific case studies are not cited here.

---

## 3) Reduced/hybrid approaches for speed (for policy pretraining)

### A. Learned surrogates of DEM

**Graph Network Simulator (GNS)**

GNS learns particle accelerations from particle states/boundaries and is described as providing accurate predictions while being **orders of magnitude faster** than traditional numerical methods for granular flows and complex boundaries, though complexity grows with particle count and requires decomposition/hierarchical scaling methods (fransen2026towardsscientificmachine pages 11-13).

**NeuralDEM**

NeuralDEM is referenced as a **real-time** simulation approach for industrial particulate flows (bibliographic mention) (fransen2026towardsscientificmachine pages 26-28).

### B. Suitability for “auger + taps”

These surrogates may be adequate for macroscopic discharge vs tilt/agitation, but rotate→tap coupling is contact-history-driven; surrogates typically need training data that covers this exact regime to be trustworthy.

---

## 4) Sim-to-real considerations for granular digital twins (actionable calibration lessons)

### A. Calibrate against simple bench tests and optimize parameters

ACCES automates DEM calibration using evolutionary strategies (CMA-ES) and calibrates restitution plus rolling/sliding/torsional friction (particle–particle and particle–wall) against experimental measurements (nicusan2025accesnoninvasivesimulation pages 11-12, nicusan2025accesnoninvasivesimulation pages 1-2).

### B. Avoid non-identifiability (critical for “no overshoot” dosing)

Calibration targets must be sensitive enough and numerous enough to uniquely constrain parameters; **sliding and rolling friction can trade off**, risking non-unique fits (nicusan2025accesnoninvasivesimulation pages 16-18). Multi-regime tests (e.g., rotating drum at multiple RPM representing distinct regimes) help disambiguate parameters (nicusan2025accesnoninvasivesimulation pages 16-18).

### C. Validate using multiple statistics, not one scalar

ACCES emphasizes comparing distributions/statistics (velocity distributions, density distributions, diffusion/segregation patterns) against experimental particle-tracking measurements (nicusan2025accesnoninvasivesimulation pages 16-18). For your doser, analogs would include: mass-per-rev distributions at multiple tilts, tap-response curves, and drained-flow/angle-of-repose tests.

---

## 5) Recommendation and workflow

The most actionable open-source shortlist is:

| Engine | Method type | Expected ability to capture tilt-dependent mass-per-action | Expected ability to capture tap-induced avalanching / lip-reservoir coupling | Computational speed for many rollouts | Python integration | Evidence / notes | Key citations |
|---|---|---|---|---|---|---|---|
| Project Chrono::GPU | GPU DEM | High: DEM should directly resolve gravity, wall friction, auger geometry, and free-surface filling/emptying, so angle-dependent dispense-per-rotation is a natural emergent output. | High: explicit particle contacts and history-dependent friction make it the best fit for tap + rotate sequencing and hidden near-lip inventory, assuming sufficient calibration. | Moderate: likely the fastest physics-faithful option among open-source choices for workstation-scale granular rollouts, but still much slower than PBD/MPM surrogates; exact particle-count evidence not retrieved here. | Good: Chrono ecosystem has Python-facing workflows and Gym-style coupling has been demonstrated. | Recommended as the main engineering twin if you can accept DEM calibration cost; include coarse-graining and domain randomization. Specific Chrono::GPU paper exists but evidence was not retrieved in full here; Chrono is identified as an open-source dynamics engine and distributed RL wrapper exists. | (zou2026chronogymnasiumanopensource pages 8-8) |
| YADE | CPU DEM | High: DEM contact laws with normal/tangential/rolling stiffness and friction have already been used for granular media, so tilt sensitivity should be captured well if geometry and calibration are adequate. | High: very suitable for stateful granular discharge, avalanching, and history effects at the outlet; hidden lip-reservoir state should emerge from particle configuration. | Low to moderate: excellent for fidelity and scripting, but CPU DEM will be slow for broad policy search unless heavily coarse-grained or used to generate surrogate-training data. | High: open-source framework designed for extensibility and interactive use; strong scripting workflow. | Strong evidence base for granular materials: YADE is an open-source DEM framework and a 10,000-particle sand triaxial example reproduced nonlinear granular behavior, supporting credibility for powder-flow mechanism studies. | (kozicki2008anewopensource pages 11-13, kozicki2008anewopensource pages 1-2) |
| Taichi MLS-MPM / ChainQueen / diffTaichi-style MPM | MPM (continuum / particle-grid hybrid) | Moderate: should capture gross angle-dependent flow and slumping, especially if tuned as a frictional/elastoplastic granular continuum, but not individual grain metering as faithfully as DEM. | Moderate: can represent tap-induced avalanching and transient free-surface relaxation, but the discrete near-lip reservoir and grain-by-grain refill/depletion mechanism will be blurred relative to DEM. | High: best candidate for large numbers of training rollouts; real-time GPU MPM and 4-9x speedups over prior methods were reported for ChainQueen-class simulators, and MPM is widely used for granular media. | High: strong Python-centered workflow in Taichi/diffTaichi ecosystems. | Best as a pretraining or surrogate-data engine rather than the final calibrated twin; useful for policy structure search, then refine on DEM/hardware. ChainQueen notes MPM can simulate granular materials and is GPU-accelerated; differentiable-simulator reviews also place MLS-MPM among contact-capable simulators. | (hu2019chainqueenarealtime pages 1-2, hu2019chainqueenarealtime pages 11-13, newbury2024areviewof pages 10-11, newbury2024areviewof pages 1-3) |


*Table: This table compares three open-source simulation-engine directions for a tilted-auger powder doser digital twin. It emphasizes which engines are most likely to capture the auger's geometry-dependent metering and tap-coupled outlet dynamics, while balancing speed and Python controllability.*

### Suggested Python coupling workflow (controller ↔ simulator)

1. **Geometry & actuation**: import tube+auger CAD; prescribe auger rotation; implement tapper as an impulse on the tube or a short displacement/velocity pulse at a strike point.
2. **Step the sim**: small Δt during actuation; “settle windows” by running until kinetic energy/flow rate drops below a threshold.
3. **Virtual sensing**: define a vial catch plane/volume; integrate mass crossing it; corrupt observations during vibration and only sample mass after settle, mirroring your balance behavior.
4. **Calibration**: wrap the sim with an ACCES-like automated calibration loop over restitution and rolling/sliding/torsional friction coefficients (nicusan2025accesnoninvasivesimulation pages 1-2), using multi-regime tests to avoid parameter tradeoffs (nicusan2025accesnoninvasivesimulation pages 16-18).
5. **Policy development**: use fast engines (FleX-like / MPM) to prototype control policy structure quickly (SoftGym throughput ~4× real-time) (lin2021softgymbenchmarkingdeep pages 2-5), then refine in DEM because DEM explicitly captures friction-history state (nicusan2025accesnoninvasivesimulation pages 11-12).

---

## Gaps (explicit)

- This run did not retrieve full-text feature sheets for Bullet/MuJoCo granular support, Blender/Houdini grain solvers, or Chrono::GPU particle-count benchmarks.
- Screw-conveyor/auger DEM example papers were identified in search results but not obtained as usable full-text evidence, so they are not cited.

Overall recommendation: use **GPU DEM (Chrono::GPU)** as the “final” engineering twin, use **YADE** for a scriptable baseline DEM and mechanism exploration, and use **GPU MPM (ChainQueen/Taichi MLS-MPM class)** or FleX-like particle simulation for fast pretraining and controller-structure search before DEM/hardware refinement (hu2019chainqueenarealtime pages 1-2, kozicki2008anewopensource pages 11-13, nicusan2025accesnoninvasivesimulation pages 1-2, lin2021softgymbenchmarkingdeep pages 2-5).

References

1. (lin2021softgymbenchmarkingdeep pages 2-5): Xingyu Lin, Yufei Wang, Jake Olkin, and David Held. Softgym: benchmarking deep reinforcement learning for deformable object manipulation. Preprint, Jan 2021. URL: https://doi.org/10.48550/arxiv.2011.07215, doi:10.48550/arxiv.2011.07215. This article has 344 citations.

2. (lin2021softgymbenchmarkingdeep pages 5-7): Xingyu Lin, Yufei Wang, Jake Olkin, and David Held. Softgym: benchmarking deep reinforcement learning for deformable object manipulation. Preprint, Jan 2021. URL: https://doi.org/10.48550/arxiv.2011.07215, doi:10.48550/arxiv.2011.07215. This article has 344 citations.

3. (zhong2207differentiablephysicssimulations pages 1-2): Yaofeng Desmond Zhong, Jiequn Han, and Georgia Olympia Brikis. Differentiable physics simulations with contacts: do they have correct gradients w.r.t. position, velocity and control? ArXiv, Jul 2207. URL: https://doi.org/10.48550/arxiv.2207.05060, doi:10.48550/arxiv.2207.05060. This article has 33 citations.

4. (hu2019chainqueenarealtime pages 1-2): Yuanming Hu, Jiancheng Liu, Andrew Spielberg, Joshua B. Tenenbaum, William T. Freeman, Jiajun Wu, Daniela Rus, and Wojciech Matusik. Chainqueen: a real-time differentiable physical simulator for soft robotics. 2019 International Conference on Robotics and Automation (ICRA), pages 6265-6271, Oct 2019. URL: https://doi.org/10.48550/arxiv.1810.01054, doi:10.48550/arxiv.1810.01054. This article has 413 citations.

5. (newbury2024areviewof pages 1-3): Rhys Newbury, Jack Collins, Kerry He, Jiahe Pan, Ingmar Posner, David Howard, and Akansel Cosgun. A review of differentiable simulators. IEEE Access, 12:97581-97604, Jul 2024. URL: https://doi.org/10.48550/arxiv.2407.05560, doi:10.48550/arxiv.2407.05560. This article has 85 citations and is from a peer-reviewed journal.

6. (newbury2024areviewof pages 10-11): Rhys Newbury, Jack Collins, Kerry He, Jiahe Pan, Ingmar Posner, David Howard, and Akansel Cosgun. A review of differentiable simulators. IEEE Access, 12:97581-97604, Jul 2024. URL: https://doi.org/10.48550/arxiv.2407.05560, doi:10.48550/arxiv.2407.05560. This article has 85 citations and is from a peer-reviewed journal.

7. (kozicki2008anewopensource pages 1-2): J. Kozicki and F.V. Donzé. A new open-source software developed for numerical simulations using discrete modeling methods. Computer Methods in Applied Mechanics and Engineering, 197:4429-4443, Sep 2008. URL: https://doi.org/10.1016/j.cma.2008.05.023, doi:10.1016/j.cma.2008.05.023. This article has 440 citations and is from a highest quality peer-reviewed journal.

8. (kozicki2008anewopensource pages 14-15): J. Kozicki and F.V. Donzé. A new open-source software developed for numerical simulations using discrete modeling methods. Computer Methods in Applied Mechanics and Engineering, 197:4429-4443, Sep 2008. URL: https://doi.org/10.1016/j.cma.2008.05.023, doi:10.1016/j.cma.2008.05.023. This article has 440 citations and is from a highest quality peer-reviewed journal.

9. (kozicki2008anewopensource pages 11-13): J. Kozicki and F.V. Donzé. A new open-source software developed for numerical simulations using discrete modeling methods. Computer Methods in Applied Mechanics and Engineering, 197:4429-4443, Sep 2008. URL: https://doi.org/10.1016/j.cma.2008.05.023, doi:10.1016/j.cma.2008.05.023. This article has 440 citations and is from a highest quality peer-reviewed journal.

10. (nicusan2025accesnoninvasivesimulation pages 11-12): A. Nicuşan, Dominik Werner, J. Sykes, Jonathan Seville, Tzany Kokalova, and C. Windows-Yule. Acces: non-invasive simulation calibration via optimisation using evolutionary algorithms and metaprogramming. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2505.02967, doi:10.48550/arxiv.2505.02967. This article has 8 citations.

11. (nicusan2025accesnoninvasivesimulation pages 1-2): A. Nicuşan, Dominik Werner, J. Sykes, Jonathan Seville, Tzany Kokalova, and C. Windows-Yule. Acces: non-invasive simulation calibration via optimisation using evolutionary algorithms and metaprogramming. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2505.02967, doi:10.48550/arxiv.2505.02967. This article has 8 citations.

12. (nicusan2025accesnoninvasivesimulation pages 28-31): A. Nicuşan, Dominik Werner, J. Sykes, Jonathan Seville, Tzany Kokalova, and C. Windows-Yule. Acces: non-invasive simulation calibration via optimisation using evolutionary algorithms and metaprogramming. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2505.02967, doi:10.48550/arxiv.2505.02967. This article has 8 citations.

13. (fransen2026towardsscientificmachine pages 11-13): Marc Fransen, Andreas Fürst, Deepak Tunuguntla, Daniel N. Wilke, Benedikt Alkin, Daniel Barreto, Johannes Brandstetter, Miguel Angel Cabrera, Xinyan Fan, Mengwu Guo, Bram Kieskamp, Krishna Kumar, John Morrissey, Jonathan Nuttall, Jin Ooi, Luisa Orozco, Stefanos-Aldo Papanicolopulos, Tongming Qu, Dingena Schott, Takayuki Shuku, WaiChing Sun, Thomas Weinhart, Dongwei Ye, and Hongyang Cheng. Towards scientific machine learning for granular material simulations: challenges and opportunities. Archives of Computational Methods in Engineering, 33:789-821, Aug 2026. URL: https://doi.org/10.1007/s11831-025-10322-8, doi:10.1007/s11831-025-10322-8. This article has 15 citations and is from a peer-reviewed journal.

14. (fransen2026towardsscientificmachine pages 26-28): Marc Fransen, Andreas Fürst, Deepak Tunuguntla, Daniel N. Wilke, Benedikt Alkin, Daniel Barreto, Johannes Brandstetter, Miguel Angel Cabrera, Xinyan Fan, Mengwu Guo, Bram Kieskamp, Krishna Kumar, John Morrissey, Jonathan Nuttall, Jin Ooi, Luisa Orozco, Stefanos-Aldo Papanicolopulos, Tongming Qu, Dingena Schott, Takayuki Shuku, WaiChing Sun, Thomas Weinhart, Dongwei Ye, and Hongyang Cheng. Towards scientific machine learning for granular material simulations: challenges and opportunities. Archives of Computational Methods in Engineering, 33:789-821, Aug 2026. URL: https://doi.org/10.1007/s11831-025-10322-8, doi:10.1007/s11831-025-10322-8. This article has 15 citations and is from a peer-reviewed journal.

15. (nicusan2025accesnoninvasivesimulation pages 16-18): A. Nicuşan, Dominik Werner, J. Sykes, Jonathan Seville, Tzany Kokalova, and C. Windows-Yule. Acces: non-invasive simulation calibration via optimisation using evolutionary algorithms and metaprogramming. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2505.02967, doi:10.48550/arxiv.2505.02967. This article has 8 citations.

16. (zou2026chronogymnasiumanopensource pages 8-8): Bocheng Zou, Harry Zhang, Khailanii Slaton, Jingquan Wang, Derrick Ruan, H. Unjhawala, R. Serban, and D. Negrut. Chrono-gymnasium: an open-source, gymnasium-compatible distributed simulation framework. ArXiv, May 2026. URL: https://doi.org/10.48550/arxiv.2605.14911, doi:10.48550/arxiv.2605.14911. This article has 0 citations.

17. (hu2019chainqueenarealtime pages 11-13): Yuanming Hu, Jiancheng Liu, Andrew Spielberg, Joshua B. Tenenbaum, William T. Freeman, Jiajun Wu, Daniela Rus, and Wojciech Matusik. Chainqueen: a real-time differentiable physical simulator for soft robotics. 2019 International Conference on Robotics and Automation (ICRA), pages 6265-6271, Oct 2019. URL: https://doi.org/10.48550/arxiv.1810.01054, doi:10.48550/arxiv.1810.01054. This article has 413 citations.
Question: We are building an open-hardware powder-dosing platform for self-driving
laboratories (a digital-alloy lab dosing metal powders such as high-purity Si
and AlSi10Mg into crucibles). Two devices are in play:

1. An **auger doser**: an FDM-printed Archimedes screw inside a printed
   hopper, driven by a NEMA-11 stepper, with an ERM vibration motor and a
   solenoid tapper as flow aids, controlled by a Raspberry Pi in a
   closed-loop **gravimetric** cycle — dispense, read a laboratory balance,
   trickle to a target mass (targets roughly 10 mg to 10 g).
2. A **"powder excavator"**: a gantry-mounted, actuator-free half-cylinder
   trough on a longitudinal pivot pin that scoops from a bulk powder bed;
   its tilt schedule is programmed purely passively (a fixed cam ramp or a
   peg-in-routed-slot board engaged by gantry motion), with a fixed
   strike-off bar defining the fill volume.

Target powders are dozens of microns in diameter and often cohesive,
hygroscopic, and/or triboelectrically charging. All geometry is authored as
parametric code (CadQuery / OpenSCAD) and exported to STEP/STL for FDM
printing, so candidate designs are cheap to generate but slow to test
physically.

We want to stand up a **digital-twin environment for generative design**: a
physics simulation of the actual dosing task — source powder, the moving
printed parts, and the balance reading (dispensed mass vs. time) — faithful
enough that geometry and motion-schedule candidates can be ranked in silico
(e.g. by a Bayesian optimiser) before anything is printed. The inspiration
is MATTERIX (Darvish et al., *Nature Computational Science* 2025;
arXiv:2601.13232), a GPU-accelerated Isaac-Sim-based digital twin of a
robotic chemistry lab that includes powder and liquid simulation, workflow
semantics, and sim-to-real transfer.

Please perform a high-effort literature search and synthesis covering:

1. **Simulation methods and engines for device-scale granular flow.**
   Discrete element method (DEM) codes (LIGGGHTS, Yade, MercuryDPM,
   MFiX-DEM, Project Chrono, Altair EDEM, Rocky DEM, Ansys), GPU-resident
   DEM, material point method (MPM), SPH, continuum mu(I)-rheology solvers,
   position-based dynamics, and the granular capabilities of robotics
   simulators (NVIDIA Isaac Sim/Lab + PhysX particles, Genesis, AGX
   Dynamics, MuJoCo, Taichi-based solvers). Compare fidelity, speed,
   licensing, and suitability for cohesive fine powders.

2. **Quantitative fidelity for dosing-like tasks.** DEM studies of screw /
   auger feeders, vibratory channel dosing, hopper discharge, tapping /
   knocking de-bridging, and scoop/bucket digging of cohesive powder. What
   agreement with experiment is actually reported (mass-flow-rate error,
   dose CV, spread mass fraction), and under what calibration effort?

3. **Cohesion modelling and particle-count tractability.** JKR / simplified
   JKR, Edinburgh Elasto-Plastic Adhesion (EEPA), liquid-bridge models;
   coarse-graining / scaled-particle approaches and their validity limits
   when real particles are tens of microns (real particle counts are
   astronomically large); van der Waals, moisture, and electrostatic
   contributions for metal powders specifically (Si, Al alloys, with oxide
   layers).

4. **DEM parameter calibration workflows.** Angle-of-repose, shear-cell /
   FT4 rheometer, tapped-density tests; inverse calibration via Bayesian
   optimisation, surrogate models, or ML; transferability of calibrated
   parameter sets across process geometries; virtual calibration and the
   risk of non-unique parameter sets.

5. **Simulation-in-the-loop design optimisation.** Published examples of
   optimising equipment geometry with granular simulation in the loop
   (hopper / chute / screw / mixer blade / bucket shape optimisation via
   DEM + Bayesian or evolutionary optimisers, surrogate-assisted DEM
   design); differentiable granular simulators (DiffTaichi, NVIDIA Warp,
   gradSim) used for design or control gradients; reported wall-clock cost
   per design evaluation.

6. **Digital twins and sim-to-real for laboratory automation.** Where does
   MATTERIX sit relative to other lab digital twins; robot-learning results
   with granular media (scooping, pouring, trickling policies trained in
   simulation and transferred to hardware); domain randomisation over
   granular parameters; and any work that models the *measurement* side —
   a balance in the loop (settling time, vibration noise, drift) — for
   closed-loop gravimetric dosing.

7. **Recommended stack and gaps.** Given the two devices above, recommend a
   concrete open-source simulation stack (engine + cohesive contact model +
   calibration protocol + optimiser + CAD hand-off via STL/STEP), the
   expected wall-clock per candidate evaluation on a single modern GPU, and
   the top gaps/risks where simulation is unlikely to rank designs
   correctly (e.g. triboelectrics, humidity, FDM surface roughness).

Ground every claim in cited references; prefer peer-reviewed sources, but
include preprints and credible vendor/tool documentation where peer-reviewed
work is sparse. Comparative tables are welcome where tools occupy the same
niche.


# Digital-Twin Simulation for Generative Design of Open-Hardware Powder-Dosing Platforms: A Literature Synthesis

## 1. Simulation Methods and Engines for Device-Scale Granular Flow

The discrete element method (DEM) remains the dominant particle-resolved approach for device-scale granular simulation. Among open-source codes, **LIGGGHTS** (and its maintained forks such as LIGGGHTS-INL and CFDEM) is the most widely used for industrial powder-flow applications including screw feeders, hoppers, and mixers, with demonstrated automated calibration workflows (nicusan2025accesnoninvasivesimulation pages 5-6, nicusan2025accesnoninvasivesimulation pages 18-20). **Yade** and **MercuryDPM** offer excellent extensibility for custom adhesive contact laws but are generally CPU-bound and slower for large optimization campaigns. **MFiX-DEM** adds gas–solid coupling but introduces unnecessary CFD overhead for dry dosing scenarios (cocco2017cfddemmodelingthe pages 18-21, cocco2017cfddemmodelingthe pages 5-10).

For GPU-accelerated DEM, **Project Chrono (Chrono::GPU)** has demonstrated exceptional scalability: up to ~710 million frictionless spheres or ~220 million frictional spheres on a single commodity GPU, with linear scaling until GPU memory is exhausted (kelly2020billiondegreeof pages 1-3, kelly2020billiondegreeof pages 22-24, kelly2020billiondegreeof pages 19-22). However, its current cohesion support is version-dependent and it is not a turnkey platform for calibrated cohesive fine-powder modeling. Commercial GPU-DEM solvers (**Altair EDEM**, **Rocky DEM**) offer turnkey JKR/EEPA contact models but at significant license cost.

Among **robotics simulators**, NVIDIA Isaac Sim uses a position-based dynamics (PBD) particle solver with an iterative density solver for relatively large time steps (darvish2025matterixtowarda pages 15-16, darvish2025matterixtowarda pages 5-7). This is the engine underlying MATTERIX. **GranularGym** is an open-source GPU simulator (Julia + CUDA) that achieves real-time simulation of ~50,000 dry frictional spheres on an RTX 3080 Ti, but explicitly lacks cohesive contact models and is acknowledged as an approximation insufficient for the full range of granular rheological behavior (millard2023granulargymhigh pages 1-2, millard2023granulargymhigh pages 7-8). **MuJoCo** has no native powder-specific contact model and is impractical for explicit powder beds. **AGX Dynamics** offers effective bulk cohesion parameters but not research-grade JKR/EEPA micromechanics.

**SPH** and **MPM** (including DiffTaichi-based solvers) represent granular media as a continuum, which can serve as a bulk proxy for large flows but cannot resolve individual grains, agglomerate breakup, screw-clearance flow, or milligram-scale dose intermittency that characterize the user's dosing application (rakhshaUnknownyearcomparinggranulardynamics pages 2-3).

The following table compares the major engines across key dimensions relevant to the user's application:

| Engine / method | Type | Open-source? | GPU-accelerated? | Maximum reported particle count | Cohesive contact models available | Suitability for cohesive fine powder | Typical use case | Key limitation |
|---|---|---:|---:|---|---|---|---|---|
| LIGGGHTS | Soft-sphere DEM | Yes, GPL; maintenance fragmented across forks | Primarily CPU/MPI; fork-dependent GPU support | No universal maximum; commonly 10⁵–10⁷ on clusters | Hertz–Mindlin, cohesion-energy-density/SJKR-style adhesion, capillary models through packages or extensions | **High**, with the right fork and calibration | Screw feeders, hoppers, mixers, vibrating beds, CFD–DEM | Model availability varies by fork; cohesive DEM requires small time steps. ACCES demonstrates automated LIGGGHTS calibration (nicusan2025accesnoninvasivesimulation pages 5-6, nicusan2025accesnoninvasivesimulation pages 18-20) |
| Yade | Soft-sphere DEM and coupled multiphysics | Yes, GPL | Mostly CPU/OpenMP | No authoritative maximum; typically 10⁴–10⁶ for detailed models | CohFrictMat, JKR-style adhesion, capillary bridges, bonded contacts, extensible laws | **High fidelity; low-to-medium throughput** | Wet/cohesive granular research and custom calibration | Excellent extensibility, but generally too slow for large optimization campaigns without coarse-graining |
| MercuryDPM | Soft-sphere DEM | Yes, BSD-3-Clause | Mainly CPU/OpenMP/MPI | No universal maximum; usually research-scale 10⁴–10⁶+ | Reversible/irreversible adhesion, liquid bridges, sintering, thermal and custom interactions | **High fidelity; medium-to-low throughput** | Fundamental powder flow, hoppers, cohesive-contact development | Smaller ecosystem and less turnkey CAD/workflow integration than commercial solvers |
| MFiX-DEM | CFD–DEM / soft-sphere DEM | Yes, US-government open source | CPU/MPI; GPU capability depends on release | Usually millions rather than hundreds of millions | Cohesion and van der Waals-style forces, heat/mass transfer, gas–solid coupling | **Medium–high** when air coupling matters | Aerated hoppers, pneumatic transport, fluidized beds | Unnecessary CFD cost for dry dosing; stiff cohesive interactions can make simulations extremely slow (cocco2017cfddemmodelingthe pages 18-21, cocco2017cfddemmodelingthe pages 5-10) |
| Project Chrono / Chrono::GPU | GPU soft-sphere DEM plus multibody dynamics | Yes, BSD-3-Clause | Yes, CUDA | About **710–715 million frictionless** or **210–220 million frictional spheres** on one GPU (kelly2020billiondegreeof pages 1-3, kelly2020billiondegreeof pages 22-24, kelly2020billiondegreeof pages 19-22) | Frictional Hertz/Mindlin-type history model; cohesion support is version-dependent | **Medium** | Very large dry-granular and terramechanics simulations | Exceptional counts rely on specialized spherical-particle assumptions; not a turnkey JKR/EEPA fine-powder platform (kelly2020billiondegreeof pages 1-3) |
| Altair EDEM | Commercial soft-sphere DEM | No, proprietary | Yes, GPU and CPU | Hardware/model-dependent; no universal independent maximum | JKR, simplified JKR, EEPA, liquid bridges, bonding, user-defined models | **Very high** | Industrial screw feeders, hoppers, mixers, powder spreading | License cost and closed implementation; stiffness reduction accelerates runs but can change forces (thoesen2019screw‐generatedforcesin pages 8-9) |
| Ansys Rocky DEM | Commercial GPU soft-sphere DEM | No, proprietary | Yes, multi-GPU | Hardware/model-dependent; commonly millions to tens of millions | Adhesive/cohesive forces, liquid bridges and custom models; exact support is version-dependent | **High** | Industrial equipment, nonspherical particles, wear and breakage | License cost; throughput falls with complex shape, cohesion, rolling resistance and contact history |
| NVIDIA Isaac Sim / PhysX particles | Position-based dynamics particle system | Source-access varies; not conventionally permissive open source | Yes, GPU | Scene- and hardware-dependent; no validated fine-powder maximum reported by MATTERIX | Generic cohesion, friction, viscosity and density constraints; not calibrated JKR/EEPA/electrostatics | **Low for quantitative dosing; medium for workflow prototyping** | Robotics, perception, pouring/scooping policies, laboratory workflow simulation | PBD prioritizes stability and real-time interaction over powder micromechanics; MATTERIX uses it for powders and liquids (darvish2025matterixtowarda pages 15-16, darvish2025matterixtowarda pages 5-7, darvish2025matterixtowarda pages 22-24) |
| GranularGym | Implicit rigid-contact granular solver / DEM-family method | Yes, Julia with Python interface | Yes, CUDA and Apple Metal | **50,000 particles in real time** on RTX 3080 Ti; interactive for hundreds of thousands (millard2023granulargymhigh pages 1-2) | Dry Coulomb friction; no demonstrated JKR, EEPA, moisture or electrostatics | **Low** | Fast robot learning, scooping, digging and control | Rigid spheres and simplified dry contact do not reproduce cohesive-powder rheology (millard2023granulargymhigh pages 1-2, millard2023granulargymhigh pages 7-8) |
| AGX Dynamics / Algoryx Momentum Granular | Nonsmooth/implicit granular dynamics plus multibody simulation | No, proprietary | GPU acceleration available | Vendor- and configuration-dependent | Effective bulk cohesion and compaction parameters; not generally research-grade JKR/EEPA micromechanics | **Medium–low** | Real-time excavation, construction vehicles and robotics | Effective macroscopic parameters may not transfer to micron-scale cohesive dosing |
| MuJoCo | Rigid-body contact dynamics; particles represented as bodies/plugins | Yes, Apache-2.0 | Core dynamics primarily CPU | Generally hundreds to low thousands of bodies, not millions | No native powder-specific JKR, EEPA, capillary, humidity or electrostatic model | **Very low** | Robot kinematics, rigid manipulation and control | Explicit powder beds are impractical; best coupled to a separate material solver |
| Taichi / DiffTaichi MPM | Material point method / differentiable continuum particles | Yes, license project-dependent | Yes, CUDA/Vulkan and other backends | Commonly 10⁵–10⁷ material points, implementation-dependent | Drucker–Prager and other continuum plasticity laws; no grain-scale JKR/EEPA contacts | **Medium for bulk excavation; low for dose intermittency** | Differentiable control, inverse identification and bulk sand/soil | Grid diffusion suppresses individual grains, agglomerate breakup, outlet-arch statistics and milligram trickling |
| Ansys Fluent CFD–DEM | Commercial CFD coupled to DEM | No, proprietary | GPU support varies by coupling path | Commonly 10⁵–10⁷; no fixed maximum | Depends on DEM backend; adhesion, liquid bridges, heat/mass transfer and custom forces may be available | **High only when gas/moisture coupling is essential** | Pneumatic conveying, aerated discharge and dust entrainment | Expensive and complex for dry dosing; collision-scale time steps and cohesive forces dominate runtime (cocco2017cfddemmodelingthe pages 5-10) |
| SPH granular continuum | Mesh-free continuum particles | Code-dependent | Frequently GPU-accelerated | Hundreds of thousands to hundreds of millions of computational points | Cohesion through yield stress/effective constitutive laws, not grain-contact adhesion | **Low–medium** | Large bulk flow, terrain and multiphase free surfaces | Cannot resolve screw-clearance grains, agglomerates, arch statistics or discrete milligram doses; non-Newtonian SPH is only a bulk proxy (rakhshaUnknownyearcomparinggranulardynamics pages 2-3) |


*Table: Comparison of dedicated DEM, robotics-oriented particle systems, and continuum solvers for device-scale powder flow. The table emphasizes licensing, GPU scale, cohesion support, and fitness for quantitative simulation of cohesive fine-powder dosing.*

## 2. Quantitative Fidelity for Dosing-Like Tasks

Reported DEM validation for screw/auger systems shows that simulated thrust forces for Archimedes screws in glass-bead beds are typically **5–20% higher** than experimental values at 30–120 rpm, with the discrepancy attributable to stiffness reduction, alignment imperfections, and load-cell drift (thoesen2019screw‐generatedforcesin pages 8-9). For cohesive powder characterization, calibrated DEM models have reproduced angle of repose within ~2% and porosity within ~2.5% when using design-of-experiments and multivariate regression calibration (elkassem2021amultivariateregression pages 21-23). Soybean seed DEM calibration using a GA-BP-GA neural surrogate achieved 2.91% angle-of-repose error, improving on response-surface methods alone at 4.39% (xie2026optimizationbasedcalibrationof pages 7-9).

For scooping and excavation—relevant to the powder excavator—the simulation-to-reality gap for a wheel-loader bucket filling in deformable soil was found to be approximately **10%** across loaded mass, motion trajectories, actuator forces, and total work, with only weak dependence on simulation fidelity level (aoshima2025examiningthesimulationtoreality pages 1-3). A transferred force-feedback controller showed ~5% performance degradation despite a ~15% domain gap between simulation resolutions. For robotic food scooping, policies trained in Isaac Lab simulation achieved **82% real-world success** across unseen food categories (tai2025gritsaspillageaware pages 1-2, tai2025gritsaspillageaware pages 4-5).

Surrogate-assisted DEM optimization of screw conveyors using EDEM, Latin hypercube sampling, and NSGA-II demonstrated that physical validation of the optimized design yielded a 15.77% mass-flow-rate increase and 26.16% energy-consumption reduction compared to the baseline (zhang2026multiobjectiveoptimizationof pages 3-5).

| Reference | Task / geometry | DEM code | Contact model | Particle count | Key metric | Reported agreement | Calibration effort |
|---|---|---|---|---:|---|---|---|
| Thoesen et al. (2019) (thoesen2019screw‐generatedforcesin pages 8-9) | Double-helix Archimedes screws moving through glass-bead beds; three pitches and six speeds | EDEM | Soft-sphere DEM with friction; stiffness sensitivity evaluated | Not reported | Screw thrust force | Simulated forces were **5–20% higher** than experiments at 30–120 rpm. Increasing particle modulus from 20 to 680 MPa changed predicted thrust from 4.31 to 3.90 N. | Glass beads were mechanically characterized; approximately 180 physical trials. Reduced stiffness accelerated simulation about tenfold but introduced a fidelity trade-off. |
| El-Kassem et al. (2021) (elkassem2021amultivariateregression pages 21-23, elkassem2021amultivariateregression pages 2-3) | Angle-of-repose and porosity tests for free-flowing and cohesive powders | Generic DEM implementation | Frictional contact plus cohesion-energy-density term | Not reported | Angle of repose and porosity | Cohesive-powder validation predicted 40.8° versus 40.0° experimentally, about **2% error**; porosity was 56.23% versus 54.84%, about **2.5% error**. | Six inputs—stiffness, particle size, restitution, static friction, rolling friction, and cohesion—were screened with a quadratic D-optimal design and multivariate regression; multiple observables reduced parameter ambiguity. |
| Zhang et al. (2026) (zhang2026multiobjectiveoptimizationof pages 3-5) | Inclined screw conveyor; pitch, inclination, and rotational speed varied | EDEM | Hertz–Mindlin no-slip | Not reported | Mass-flow rate and energy consumption | Physical validation of the selected design found **15.77% higher mass-flow rate** and **26.16% lower energy consumption**; absolute simulation-to-experiment error was not reported in the retrieved evidence. | Optimal Latin-hypercube DEM sampling, least-squares surrogate fitting, NSGA-II Pareto search, entropy-weighted TOPSIS selection, and bench validation. |
| Girnth et al. (2024) (girnth2024dimensionlessquantitiesin pages 5-7, girnth2024dimensionlessquantitiesin pages 14-15, girnth2024dimensionlessquantitiesin pages 4-5, girnth2024dimensionlessquantitiesin pages 9-11, girnth2024dimensionlessquantitiesin pages 15-16) | Calibration for powder-bed processing of AlSi10Mg and other AM powders; applicable to spreading | Not specified | Hertz–Mindlin, damping, rolling resistance, and JKR adhesion | Not reported | Angle of repose and bulk density | A dimensionless regression selected JKR surface energy so repose angle and bulk density matched experiments; no single spreading-error percentage was reported in the retrieved evidence. | Measured size distribution, morphology, sliding friction, restitution, repose angle, and bulk density; explored modulus reduction, timestep, rolling friction, and JKR surface energy. |
| Aoshima and Servin (2025) (aoshima2025examiningthesimulationtoreality pages 1-3) | Full-scale wheel-loader bucket filling in deformable soil | Multibody–DEM simulator | Frictional granular contact with optional multiscale acceleration | Resolution reported as 50–400 mm rather than particle count | Loaded mass, motion, actuator forces, and work | Aggregate simulation-to-reality gap was approximately **10%**, weakly dependent on fidelity. A roughly 15% domain gap reduced transferred-controller performance by about 5%. | Field-test time series were used for validation across several spatial and temporal resolutions; simulated speed ranged from 1/10,000 real time to five times real time. |
| Xie et al. (2026) (xie2026optimizationbasedcalibrationof pages 7-9) | Soybean angle-of-repose calibration followed by pneumatic seed-metering validation | EDEM and EDEM–Fluent | Calibrated frictional seed-contact model | Not reported | Angle of repose and subsequent metering behavior | Optimized model produced 22.35° versus 23.02° experimentally, a **2.91% error**, improving on response-surface calibration alone at 4.39%. | Free-fall collision, inclined sliding, and rolling tests established ranges; steepest ascent screened parameters; RSM and a GA–BP–GA neural surrogate performed inverse calibration before bench tests. |
| Kadokawa et al. (2025) (kadokawa2025progressiveresolutionpolicydistillation pages 2-3, kadokawa2025progressiveresolutionpolicydistillation pages 10-11) | Particle-based robotic rock excavation with progressive simulation resolution | Rock-excavation particle simulator | Not specified | Varied by coarse, intermediate, and fine resolution; exact counts not reported | Real-world excavation success and training time | Progressive-resolution training achieved approximately **90% success** across nine real-rock environments while reducing sampling time to **less than one-seventh** of fine-resolution-only learning. This is policy-transfer performance, not direct mass or flow validation. | Policies were pretrained at coarse resolution and conservatively distilled through intermediate to fine resolutions before real-world testing; no explicit granular-parameter calibration protocol was reported. |


*Table: Reported validation results for screw transport, cohesive-powder characterization, powder-bed processing, and granular excavation. The table distinguishes direct simulation error from optimized-design improvements and downstream policy-transfer success.*

## 3. Cohesion Modelling and Particle-Count Tractability

For dry metal powders used in additive manufacturing (including AlSi10Mg with mean particle diameter ~35 μm), **van der Waals adhesion is the dominant cohesive mechanism** when moisture content is low and electrostatic effects are weak (girnth2024dimensionlessquantitiesin pages 3-4, girnth2024dimensionlessquantitiesin pages 4-5). The **Johnson–Kendall–Roberts (JKR)** model is the standard framework for representing this adhesion in DEM: its normal force combines Hertzian elastic repulsion with an adhesive term based on surface energy density w_JKR. For AlSi10Mg powders, reported JKR surface energy search intervals span approximately **0.5–3.5 mJ/m²** (girnth2024dimensionlessquantitiesin pages 9-11). The **Edinburgh Elasto-Plastic Adhesion (EEPA)** model adds loading-history dependence and is appropriate when irreversible compaction matters, while liquid-bridge models should be reserved for cases where moisture is experimentally confirmed to be significant.

**Coarse-graining** (using larger simulated particles than real ones) is essential for tractability—real 35 μm particles in even a 1 g dose would number ~10⁷–10⁸, far exceeding practical single-GPU DEM limits for cohesive systems. However, simply enlarging particles changes the adhesive Bond number (ratio of cohesive to gravitational/inertial force), potentially distorting arching, flowability, and dose variability (girnth2024dimensionlessquantitiesin pages 3-4). Adhesive force scales with particle radius while gravitational force scales with radius cubed, so coarse-grained particles are relatively less cohesive unless the surface energy is explicitly corrected. A scale factor of 3–5× (real 35 μm → simulated ~100–175 μm) is a reasonable starting point, but the particle-to-geometry aspect ratio (e.g., screw clearance / particle diameter) must remain sufficiently large, and discharge behavior must be revalidated (girnth2024dimensionlessquantitiesin pages 3-4, girnth2024dimensionlessquantitiesin pages 9-11). Reducing Young's modulus by ~100× can accelerate simulations ~10× but alters predicted forces, particularly in confined geometries like screws (thoesen2019screw‐generatedforcesin pages 8-9).

Dimensionless parameterization using the Buckingham pi-theorem has been demonstrated for AlSi10Mg, Al₂O₃, and PEEK powders, relating simulated angle of repose and bulk density to JKR surface energy, friction, rolling resistance, and a combined parameter K = c_r · μ_s / μ_r through an empirical power law, enabling calibration with as few as two simulation sets (girnth2024dimensionlessquantitiesin pages 14-15, girnth2024dimensionlessquantitiesin pages 15-16).

## 4. DEM Parameter Calibration Workflows

DEM calibration is fundamentally an inverse problem: microscopic contact parameters (friction, rolling resistance, restitution, cohesion energy) must be inferred from macroscopic bulk measurements. The **ACCES** framework demonstrates a state-of-the-art workflow using CMA-ES evolutionary optimization to calibrate LIGGGHTS DEM parameters against rotating-drum experiments at two speeds (10 rpm rolling regime and 50 rpm cascading regime), requiring approximately **144 simulation evaluations for 4 free parameters** (nicusan2025accesnoninvasivesimulation pages 5-6, nicusan2025accesnoninvasivesimulation pages 18-20, nicusan2025accesnoninvasivesimulation pages 16-18). Using two flow regimes provides stronger constraints than a single angle-of-repose test, reducing parameter non-uniqueness (nicusan2025accesnoninvasivesimulation pages 16-18, nicusan2025accesnoninvasivesimulation pages 6-8).

Design-of-experiments approaches with multivariate regression have also been applied, demonstrating that rolling friction dominates angle of repose in cohesive powders while static friction has a smaller effect, and that multiple observables (angle of repose + porosity) substantially improve parameter identifiability (elkassem2021amultivariateregression pages 2-3, elkassem2021amultivariateregression pages 21-23, elkassem2021amultivariateregression pages 1-2).

**Non-uniqueness** is a critical risk: different parameter combinations can produce the same angle of repose but diverge in dynamic behavior or different geometries (elkassem2021amultivariateregression pages 23-24, nicusan2025accesnoninvasivesimulation pages 2-4). ACCES addresses transferability by validating calibrated parameters against systems differing by orders of magnitude in scale—rotating drums, tumbling mixers, and vibrofluidised beds—with reportedly excellent agreement, though asymmetric transfer was observed: drum data could predict vibrofluidised-bed behavior, but not vice versa (nicusan2025accesnoninvasivesimulation pages 25-27, nicusan2025accesnoninvasivesimulation pages 18-20). The recommendation is to calibrate against complementary tests spanning different flow regimes and validate against the actual target geometry (auger discharge, scoop tilt) before trusting design rankings.

## 5. Simulation-in-the-Loop Design Optimisation

Published examples of DEM-in-the-loop equipment optimization include screw-conveyor design using EDEM simulations, Latin-hypercube sampling, least-squares surrogate models, and NSGA-II multi-objective optimization for mass-flow-rate versus energy-consumption trade-offs (zhang2026multiobjectiveoptimizationof pages 3-5). CFD-DEM has been used to evaluate particle-flow stagnation and thermal hot-spots in solar receiver geometries, enabling redesign before physical prototyping (cocco2017cfddemmodelingthe pages 10-14). GA-BP neural-network surrogates have been trained on DEM simulation data and used for inverse parameter optimization (xie2026optimizationbasedcalibrationof pages 7-9).

**Differentiable granular simulators** are an emerging capability. DiffTaichi and NVIDIA Warp provide automatic differentiation through MPM-based continuum granular solvers, enabling gradient-based optimization and system identification. However, MPM grid diffusion suppresses individual grain behavior, making these tools better suited for bulk excavation or terrain deformation than for milligram-scale dosing intermittency. Progressive-resolution policy distillation has been demonstrated for excavation RL, reducing training time by 7× while maintaining ~90% real-world task success (kadokawa2025progressiveresolutionpolicydistillation pages 2-3).

For wall-clock cost, DEM simulations of screw feeders on EDEM saw roughly 10× speedup from 100× stiffness reduction but with altered predicted forces (thoesen2019screw‐generatedforcesin pages 8-9). For the user's dosing application with ~10⁵ coarse-grained particles and 5–10 s of device operation, planning estimates are **10–60 minutes per candidate on a modern single-GPU DEM solver** or **1–8 hours on CPU/MPI LIGGGHTS**, depending heavily on stiffness, cohesion model, mesh complexity, and timestep.

## 6. Digital Twins and Sim-to-Real for Laboratory Automation

**MATTERIX** (Darvish et al., *Nature Computational Science* 2025) is the most directly relevant digital-twin framework, built on NVIDIA Isaac Sim and Isaac Lab. It simulates robotic manipulation, powder and liquid dynamics (via GPU-accelerated PBD particles), device functionality, heat transfer, and basic chemical kinetics (darvish2025matterixtowarda pages 2-5, darvish2025matterixtowarda pages 15-16, darvish2025matterixtowarda pages 1-2). For liquid pouring, MATTERIX reported 61.3 ± 4.4 mL simulated versus 59.6 ± 7.9 mL real from 100 mL initial volume. Real-world deployment achieved **75% success** over 12 pick-and-place trials and **90% success** over 10 liquid-pouring trials (darvish2025matterixtowarda pages 11-14). MATTERIX extends Isaac Lab with a semantics engine that models device behaviors difficult to represent physically, including pipette operations and heater activation (darvish2025matterixtowarda pages 7-9).

However, MATTERIX's PBD particle solver prioritizes real-time stability and robot-learning interaction rates over powder micromechanics. It does not implement calibrated JKR/EEPA adhesion, triboelectric charging, or the grain-scale resolution needed to predict milligram dose variability. Complementary lab-simulation platforms include **Labimus** (humanoid manipulation in chemical labs) and **AutoBio** (biology laboratory automation), both extending Isaac Sim (darvish2025matterixtowarda pages 2-5).

For **sim-to-real transfer with granular media**, the most rigorous quantification comes from wheel-loader excavation studies showing ~10% aggregate simulation-to-reality gap with weak fidelity dependence (aoshima2025examiningthesimulationtoreality pages 1-3). Robotic food scooping using Isaac Lab with domain randomization (varying mass, friction, particle size) achieved 82% real-world success across unseen food categories (tai2025gritsaspillageaware pages 1-2, tai2025gritsaspillageaware pages 4-5, tai2025gritsaspillageaware pages 2-4). Progressive-resolution policy distillation achieved ~90% real-world excavation success while dramatically reducing training time (kadokawa2025progressiveresolutionpolicydistillation pages 2-3, kadokawa2025progressiveresolutionpolicydistillation pages 10-11).

No published work was found that models the **measurement side**—a laboratory balance in the loop with settling time, vibration noise, drift, and stable-reading logic—for closed-loop gravimetric dosing simulation. This represents a significant gap that must be addressed empirically.

## 7. Recommended Stack and Gaps

Based on the synthesis above, the following table presents a concrete recommended open-source simulation stack for the user's powder-dosing digital-twin environment:

| Layer | Recommended Tool | Role | Notes / Alternatives |
|---|---|---|---|
| DEM engine | **LIGGGHTS granular fork** such as LIGGGHTS-INL or CFDEM/LIGGGHTS | Particle-resolved simulation of the hopper, auger, trough, strike-off bar, vibration, tapping, and discharged mass | Use a maintained fork exposing the required adhesive law and moving-triangle meshes. **MercuryDPM** is a strong alternative for implementing advanced adhesion models; **Chrono::GPU** offers greater throughput but is less turnkey for calibrated cohesive powders. LIGGGHTS has been wrapped successfully by automated calibration workflows (nicusan2025accesnoninvasivesimulation pages 5-6, nicusan2025accesnoninvasivesimulation pages 18-20). |
| Cohesive contact model | **JKR or simplified JKR**, with Hertz–Mindlin friction and rolling resistance | Effective representation of dry van der Waals adhesion among oxidized metal-powder particles | Calibrate surface energy instead of treating it as a handbook constant. For approximately 35 μm AlSi10Mg, a defensible initial search interval is **0.5–3.5 mJ m⁻²** (girnth2024dimensionlessquantitiesin pages 5-7, girnth2024dimensionlessquantitiesin pages 4-5, girnth2024dimensionlessquantitiesin pages 9-11). Consider **EEPA** when irreversible compaction and loading history matter; add liquid bridges only when moisture evidence justifies them. |
| Coarse-graining | **Scaled spherical or clumped particles with adhesion correction** | Reduce the otherwise astronomical particle count while preserving selected bulk responses | Begin with a **3–5× diameter scale factor**: real 35 μm particles become roughly 100–175 μm simulation particles. Preserve relevant dimensionless ratios, especially adhesive Bond number and particle-to-clearance ratio, and revalidate discharge, arching, and dose increments. Simple enlargement changes adhesion relative to gravity and inertia (girnth2024dimensionlessquantitiesin pages 3-4, girnth2024dimensionlessquantitiesin pages 9-11). |
| Calibration protocol | **ACCES/Coexist with CMA-ES**, using complementary bulk tests | Infer friction, rolling resistance, restitution, cohesion, and possibly effective particle size | Use a rotating drum at **10 and 50 rpm**, angle of repose, loose and tapped bulk density, and preferably shear-cell or FT4 data; reserve hopper discharge and auger-dose traces for validation. ACCES calibrated four parameters in **144 samples** and showed why two flow regimes constrain parameters better than one test (nicusan2025accesnoninvasivesimulation pages 5-6, nicusan2025accesnoninvasivesimulation pages 18-20, nicusan2025accesnoninvasivesimulation pages 16-18, nicusan2025accesnoninvasivesimulation pages 9-11). |
| CAD hand-off | **CadQuery/OpenSCAD → STL → DEM triangle mesh** | Transfer each generated hopper, screw, scoop, cam, slot, and strike-off geometry into simulation | Retain STEP as the design master, then tessellate deterministically with controlled chordal and angular tolerances. Keep facets substantially smaller than screw clearances and local radii, remove self-intersections, enforce watertight normals, and record tessellation settings with each candidate. |
| Design optimiser | **BoTorch/Ax Bayesian optimisation** around the DEM black box | Rank expensive geometry and motion-schedule candidates under multiple objectives and uncertainty | Start with a space-filling Sobol or Latin-hypercube design, fit Gaussian-process surrogates, and optimize expected improvement or hypervolume. Use **NSGA-II** when the evaluation budget is larger or responses are discontinuous; an EDEM screw study used Latin-hypercube sampling, a surrogate, and NSGA-II for flow/energy trade-offs (zhang2026multiobjectiveoptimizationof pages 3-5). |
| Workflow orchestration | **Python + Coexist/ACCES + pandas** | Generate CAD, write DEM inputs, launch jobs, recover failures, extract mass-versus-time traces, and update the optimiser | Store geometry hash, mesh tolerance, random seed, powder-parameter posterior, solver version, and outputs for every run. ACCES directly edits and launches LIGGGHTS scripts and supports parallel local or cluster execution (nicusan2025accesnoninvasivesimulation pages 25-27, nicusan2025accesnoninvasivesimulation pages 18-20). |
| Balance model | **Empirical state-space or convolution model** layered over DEM truth mass | Convert particles entering the crucible into the reading observed by the Raspberry Pi controller | Model transport delay, low-pass settling, vibration-dependent noise, quantisation, drift, tare events, and stable-reading logic from logged hardware data. Do not expect granular physics to predict the metrology chain; MATTERIX models workflow semantics but does not establish a validated analytical-balance model for milligram dosing (darvish2025matterixtowarda pages 7-9, darvish2025matterixtowarda pages 14-15). |
| Expected wall-clock | **Tiered-fidelity campaign** | Budget candidate evaluations and reserve high fidelity for finalists | Planning estimate—not a published benchmark—for approximately **10⁵ coarse-grained particles and 5–10 s of device motion**: **10–60 min** on a suitably implemented modern single-GPU DEM solver, or **1–8 h** with CPU/MPI LIGGGHTS, depending strongly on stiffness, cohesion, mesh complexity, and timestep. Chrono demonstrates linear GPU scaling at far larger counts, while reducing stiffness by 100× produced about a 10× speedup in an EDEM screw study but altered predicted force (kelly2020billiondegreeof pages 1-3, kelly2020billiondegreeof pages 22-24, thoesen2019screw‐generatedforcesin pages 8-9). Benchmark one representative geometry before fixing the optimization budget. |
| Top gaps and risks | **Uncertainty model, domain randomisation, and physical finalist testing** | Prevent false confidence in simulated rankings | Highest risks are triboelectric charging without a standard validated dosing-scale DEM model; humidity-dependent capillary and oxide-surface behavior; agglomerates and particle-shape satellites; FDM roughness, porosity, wear, and print-orientation-dependent wall friction; uncertain tapper/vibrator coupling; coarse-graining failure near screw clearances and outlets; and 10 mg dose increments falling below the model’s particle-mass or stochastic-noise floor. Treat rankings as probabilistic and test finalists across parameter posteriors and random fills (girnth2024dimensionlessquantitiesin pages 3-4, elkassem2021amultivariateregression pages 2-3, nicusan2025accesnoninvasivesimulation pages 16-18, aoshima2025examiningthesimulationtoreality pages 1-3). |


*Table: An open-source, tiered stack for cohesive-powder simulation, calibration, CAD integration, optimization, and balance emulation. The table also identifies realistic runtime ranges and the principal threats to correct in-silico design ranking.*

### Principal Gaps and Risks

The top threats to correct in-silico design ranking are:

1. **Triboelectric charging**: No standard validated DEM contact model exists for triboelectric charge buildup and dissipation during auger dosing of oxidized metal powders. This is a first-order effect for fine Si and Al-alloy powders and is essentially unmodeled in all available open-source DEM platforms (girnth2024dimensionlessquantitiesin pages 3-4).

2. **Humidity and capillary bridging**: Moisture sensitivity of oxide-layer-bearing metal powders introduces capillary bridges whose strength depends on ambient RH, storage history, and powder-specific surface chemistry. Liquid-bridge DEM models exist but require per-powder calibration data that may not transfer across lots.

3. **FDM surface roughness**: Particle-wall friction coefficients depend on print orientation, layer height, infill, and material, and will change with wear. No published DEM calibration study has characterized FDM-printed surfaces for fine metal powder flow.

4. **Coarse-graining failure near critical features**: Screw-to-housing clearances, outlet orifices, and strike-off bars have dimensions comparable to tens of real particle diameters. Coarse-grained particles may not correctly predict arching, bridging, or trickle-flow cessation at these features (girnth2024dimensionlessquantitiesin pages 3-4, girnth2024dimensionlessquantitiesin pages 9-11).

5. **Milligram-scale dose stochasticity**: A 10 mg dose of 35 μm AlSi10Mg powder contains ~10⁵ particles. Even with coarse-graining, the simulated particle count per dose is only ~10³–10⁴, potentially placing dose-to-dose variability below the simulation's stochastic noise floor.

6. **Balance dynamics**: The closed-loop gravimetric controller depends on balance settling time, vibration coupling from the stepper/tapper, and stable-reading algorithms. No physics simulator models this metrology chain; it must be characterized empirically and layered over the DEM mass output.

7. **Parameter non-uniqueness**: Calibrated DEM parameter sets that reproduce one bulk test may fail in a different geometry or flow regime. Multi-test calibration (ACCES-style) and validation in the target geometry are essential before trusting design rankings (nicusan2025accesnoninvasivesimulation pages 16-18, nicusan2025accesnoninvasivesimulation pages 2-4, nicusan2025accesnoninvasivesimulation pages 6-8).

### Practical Recommendation

A tiered approach is advisable: use LIGGGHTS with JKR cohesion and ACCES calibration for quantitative dose-mass and flow-rate predictions of the auger doser, and Chrono::GPU or GranularGym-style fast simulation for rapid coarse screening of excavator tilt schedules. Reserve MATTERIX/Isaac Sim PBD for full-workflow integration testing (robot motion + perception + semantics) rather than for quantitative powder micromechanics. Always test physical finalists, as the simulation is expected to rank designs correctly for gross geometry changes (screw pitch, hopper angle, tilt schedule) but may not reliably distinguish candidates that differ only in subtle features affected by cohesion, electrostatics, or FDM surface texture.

References

1. (nicusan2025accesnoninvasivesimulation pages 5-6): ACCES: Non-Invasive Simulation Calibration via Optimisation using Evolutionary Algorithms and Metaprogramming This article has 11 citations.

2. (nicusan2025accesnoninvasivesimulation pages 18-20): ACCES: Non-Invasive Simulation Calibration via Optimisation using Evolutionary Algorithms and Metaprogramming This article has 11 citations.

3. (cocco2017cfddemmodelingthe pages 18-21): R Cocco, WD Fullmer, P Liu, and CM Hrenya. Cfd-dem: modeling the small to understand the large. Unknown journal, 2017.

4. (cocco2017cfddemmodelingthe pages 5-10): R Cocco, WD Fullmer, P Liu, and CM Hrenya. Cfd-dem: modeling the small to understand the large. Unknown journal, 2017.

5. (kelly2020billiondegreeof pages 1-3): Conlain Kelly, Nicholas Olsen, and Dan Negrut. Billion degree of freedom granular dynamics simulation on commodity hardware via heterogeneous data-type representation. Multibody System Dynamics, 50:355-379, Jun 2020. URL: https://doi.org/10.1007/s11044-020-09749-7, doi:10.1007/s11044-020-09749-7. This article has 38 citations and is from a domain leading peer-reviewed journal.

6. (kelly2020billiondegreeof pages 22-24): Conlain Kelly, Nicholas Olsen, and Dan Negrut. Billion degree of freedom granular dynamics simulation on commodity hardware via heterogeneous data-type representation. Multibody System Dynamics, 50:355-379, Jun 2020. URL: https://doi.org/10.1007/s11044-020-09749-7, doi:10.1007/s11044-020-09749-7. This article has 38 citations and is from a domain leading peer-reviewed journal.

7. (kelly2020billiondegreeof pages 19-22): Conlain Kelly, Nicholas Olsen, and Dan Negrut. Billion degree of freedom granular dynamics simulation on commodity hardware via heterogeneous data-type representation. Multibody System Dynamics, 50:355-379, Jun 2020. URL: https://doi.org/10.1007/s11044-020-09749-7, doi:10.1007/s11044-020-09749-7. This article has 38 citations and is from a domain leading peer-reviewed journal.

8. (darvish2025matterixtowarda pages 15-16): Kourosh Darvish, Arjun Sohal, Abhijoy Mandal, Hatem Fakhruldeen, Nikola Radulov, Zhengxue Zhou, Satheeshkumar Veeramani, Joshua Choi, Sijie Han, Brayden Zhang, Jeeyeoun Chae, Alex Wright, Yijie Wang, Hossein Darvish, Yuchi Zhao, Gary Tom, Han Hao, Miroslav Bogdanovic, Gabriella Pizzuto, Andrew I. Cooper, Alán Aspuru Guzik, Florian Shkurti, and Animesh Garg. Matterix: toward a digital twin for robotics-assisted chemistry laboratory automation. Nature Computational Science, 6(1):67-82, Dec 2026. URL: https://doi.org/10.1038/s43588-025-00924-4, doi:10.1038/s43588-025-00924-4. This article has 12 citations and is from a peer-reviewed journal.

9. (darvish2025matterixtowarda pages 5-7): Kourosh Darvish, Arjun Sohal, Abhijoy Mandal, Hatem Fakhruldeen, Nikola Radulov, Zhengxue Zhou, Satheeshkumar Veeramani, Joshua Choi, Sijie Han, Brayden Zhang, Jeeyeoun Chae, Alex Wright, Yijie Wang, Hossein Darvish, Yuchi Zhao, Gary Tom, Han Hao, Miroslav Bogdanovic, Gabriella Pizzuto, Andrew I. Cooper, Alán Aspuru Guzik, Florian Shkurti, and Animesh Garg. Matterix: toward a digital twin for robotics-assisted chemistry laboratory automation. Nature Computational Science, 6(1):67-82, Dec 2026. URL: https://doi.org/10.1038/s43588-025-00924-4, doi:10.1038/s43588-025-00924-4. This article has 12 citations and is from a peer-reviewed journal.

10. (millard2023granulargymhigh pages 1-2): David Millard, Daniel Pastor, Joseph Bowkett, Paul Backes, and Gaurav S. Sukhatme. Granular gym: high performance simulation for robotic tasks with granular materials. ArXiv, Jun 2023. URL: https://doi.org/10.48550/arxiv.2306.01369, doi:10.48550/arxiv.2306.01369. This article has 8 citations.

11. (millard2023granulargymhigh pages 7-8): David Millard, Daniel Pastor, Joseph Bowkett, Paul Backes, and Gaurav S. Sukhatme. Granular gym: high performance simulation for robotic tasks with granular materials. ArXiv, Jun 2023. URL: https://doi.org/10.48550/arxiv.2306.01369, doi:10.48550/arxiv.2306.01369. This article has 8 citations.

12. (rakhshaUnknownyearcomparinggranulardynamics pages 2-3): M Rakhsha, C Kelly, N Olsen, L Yang, and R Serban. Comparing granular dynamics vs. fluid dynamics via large dof-count parallel simulation on the gpu. Unknown journal, Unknown year.

13. (thoesen2019screw‐generatedforcesin pages 8-9): Andrew Thoesen, Sierra Ramirez, and Hamid Marvi. Screw‐generated forces in granular media: experimental, computational, and analytical comparison. AIChE Journal, 65:894-903, Mar 2019. URL: https://doi.org/10.1002/aic.16517, doi:10.1002/aic.16517. This article has 23 citations and is from a peer-reviewed journal.

14. (darvish2025matterixtowarda pages 22-24): Kourosh Darvish, Arjun Sohal, Abhijoy Mandal, Hatem Fakhruldeen, Nikola Radulov, Zhengxue Zhou, Satheeshkumar Veeramani, Joshua Choi, Sijie Han, Brayden Zhang, Jeeyeoun Chae, Alex Wright, Yijie Wang, Hossein Darvish, Yuchi Zhao, Gary Tom, Han Hao, Miroslav Bogdanovic, Gabriella Pizzuto, Andrew I. Cooper, Alán Aspuru Guzik, Florian Shkurti, and Animesh Garg. Matterix: toward a digital twin for robotics-assisted chemistry laboratory automation. Nature Computational Science, 6(1):67-82, Dec 2026. URL: https://doi.org/10.1038/s43588-025-00924-4, doi:10.1038/s43588-025-00924-4. This article has 12 citations and is from a peer-reviewed journal.

15. (elkassem2021amultivariateregression pages 21-23): Bilal El-Kassem, Nizar Salloum, Thomas Brinz, Yousef Heider, and Bernd Markert. A multivariate regression parametric study on dem input parameters of free-flowing and cohesive powders with experimental data-based validation. Computational Particle Mechanics, 8:87-111, Jan 2021. URL: https://doi.org/10.1007/s40571-020-00315-8, doi:10.1007/s40571-020-00315-8. This article has 39 citations.

16. (xie2026optimizationbasedcalibrationof pages 7-9): Shuangcheng Xie, Wensheng Yuan, Chengqian Jin, Yugang Feng, Fuqiang Gou, and Yuqing Ma. Optimization-based calibration of soybean seed discrete element parameters via rsm and ga-bp-ga. INMATEH-Agricultural Engineering, pages 1240, Apr 2026. URL: https://doi.org/10.35633/inmateh-78-97, doi:10.35633/inmateh-78-97. This article has 1 citations.

17. (aoshima2025examiningthesimulationtoreality pages 1-3): Koji Aoshima and Martin Servin. Examining the simulation-to-reality gap of a wheel loader digging in deformable terrain. Jul 2025. URL: https://doi.org/10.1007/s11044-024-10005-5, doi:10.1007/s11044-024-10005-5. This article has 33 citations and is from a domain leading peer-reviewed journal.

18. (tai2025gritsaspillageaware pages 1-2): Yen-Ling Tai, Yi-Ru Yang, Kuan-Ting Yu, Yu-Wei Chao, and Yi-Ting Chen. Grits: a spillage-aware guided diffusion policy for robot food scooping tasks. ArXiv, Oct 2025. URL: https://doi.org/10.48550/arxiv.2510.00573, doi:10.48550/arxiv.2510.00573. This article has 3 citations.

19. (tai2025gritsaspillageaware pages 4-5): Yen-Ling Tai, Yi-Ru Yang, Kuan-Ting Yu, Yu-Wei Chao, and Yi-Ting Chen. Grits: a spillage-aware guided diffusion policy for robot food scooping tasks. ArXiv, Oct 2025. URL: https://doi.org/10.48550/arxiv.2510.00573, doi:10.48550/arxiv.2510.00573. This article has 3 citations.

20. (zhang2026multiobjectiveoptimizationof pages 3-5): Xiaoyuan Zhang, Tingting Xi, Baoan Wang, and Haikang Li. Multi-objective optimization of screw conveyors based on nsga-ii algorithm and entropy-weighted topsis. INMATEH - Agricultural Engineering, pages 717, Apr 2026. URL: https://doi.org/10.35633/inmateh-78-58, doi:10.35633/inmateh-78-58. This article has 1 citations.

21. (elkassem2021amultivariateregression pages 2-3): Bilal El-Kassem, Nizar Salloum, Thomas Brinz, Yousef Heider, and Bernd Markert. A multivariate regression parametric study on dem input parameters of free-flowing and cohesive powders with experimental data-based validation. Computational Particle Mechanics, 8:87-111, Jan 2021. URL: https://doi.org/10.1007/s40571-020-00315-8, doi:10.1007/s40571-020-00315-8. This article has 39 citations.

22. (girnth2024dimensionlessquantitiesin pages 5-7): Simon Girnth, Tim Heitkamp, Christian Wacker, Nils Waldt, Günter Klawitter, and Klaus Dröder. Dimensionless quantities in discrete element method: powder model parameterization for additive manufacturing. Progress in Additive Manufacturing, 9:1967-1983, Jan 2024. URL: https://doi.org/10.1007/s40964-023-00543-3, doi:10.1007/s40964-023-00543-3. This article has 4 citations and is from a peer-reviewed journal.

23. (girnth2024dimensionlessquantitiesin pages 14-15): Simon Girnth, Tim Heitkamp, Christian Wacker, Nils Waldt, Günter Klawitter, and Klaus Dröder. Dimensionless quantities in discrete element method: powder model parameterization for additive manufacturing. Progress in Additive Manufacturing, 9:1967-1983, Jan 2024. URL: https://doi.org/10.1007/s40964-023-00543-3, doi:10.1007/s40964-023-00543-3. This article has 4 citations and is from a peer-reviewed journal.

24. (girnth2024dimensionlessquantitiesin pages 4-5): Simon Girnth, Tim Heitkamp, Christian Wacker, Nils Waldt, Günter Klawitter, and Klaus Dröder. Dimensionless quantities in discrete element method: powder model parameterization for additive manufacturing. Progress in Additive Manufacturing, 9:1967-1983, Jan 2024. URL: https://doi.org/10.1007/s40964-023-00543-3, doi:10.1007/s40964-023-00543-3. This article has 4 citations and is from a peer-reviewed journal.

25. (girnth2024dimensionlessquantitiesin pages 9-11): Simon Girnth, Tim Heitkamp, Christian Wacker, Nils Waldt, Günter Klawitter, and Klaus Dröder. Dimensionless quantities in discrete element method: powder model parameterization for additive manufacturing. Progress in Additive Manufacturing, 9:1967-1983, Jan 2024. URL: https://doi.org/10.1007/s40964-023-00543-3, doi:10.1007/s40964-023-00543-3. This article has 4 citations and is from a peer-reviewed journal.

26. (girnth2024dimensionlessquantitiesin pages 15-16): Simon Girnth, Tim Heitkamp, Christian Wacker, Nils Waldt, Günter Klawitter, and Klaus Dröder. Dimensionless quantities in discrete element method: powder model parameterization for additive manufacturing. Progress in Additive Manufacturing, 9:1967-1983, Jan 2024. URL: https://doi.org/10.1007/s40964-023-00543-3, doi:10.1007/s40964-023-00543-3. This article has 4 citations and is from a peer-reviewed journal.

27. (kadokawa2025progressiveresolutionpolicydistillation pages 2-3): Yuki Kadokawa, Hirotaka Tahara, and Takamitsu Matsubara. Progressive-resolution policy distillation: leveraging coarse-resolution simulations for time-efficient fine-resolution policy learning. Jan 2025. URL: https://doi.org/10.1109/tase.2025.3590068, doi:10.1109/tase.2025.3590068. This article has 6 citations and is from a domain leading peer-reviewed journal.

28. (kadokawa2025progressiveresolutionpolicydistillation pages 10-11): Yuki Kadokawa, Hirotaka Tahara, and Takamitsu Matsubara. Progressive-resolution policy distillation: leveraging coarse-resolution simulations for time-efficient fine-resolution policy learning. Jan 2025. URL: https://doi.org/10.1109/tase.2025.3590068, doi:10.1109/tase.2025.3590068. This article has 6 citations and is from a domain leading peer-reviewed journal.

29. (girnth2024dimensionlessquantitiesin pages 3-4): Simon Girnth, Tim Heitkamp, Christian Wacker, Nils Waldt, Günter Klawitter, and Klaus Dröder. Dimensionless quantities in discrete element method: powder model parameterization for additive manufacturing. Progress in Additive Manufacturing, 9:1967-1983, Jan 2024. URL: https://doi.org/10.1007/s40964-023-00543-3, doi:10.1007/s40964-023-00543-3. This article has 4 citations and is from a peer-reviewed journal.

30. (nicusan2025accesnoninvasivesimulation pages 16-18): ACCES: Non-Invasive Simulation Calibration via Optimisation using Evolutionary Algorithms and Metaprogramming This article has 11 citations.

31. (nicusan2025accesnoninvasivesimulation pages 6-8): ACCES: Non-Invasive Simulation Calibration via Optimisation using Evolutionary Algorithms and Metaprogramming This article has 11 citations.

32. (elkassem2021amultivariateregression pages 1-2): Bilal El-Kassem, Nizar Salloum, Thomas Brinz, Yousef Heider, and Bernd Markert. A multivariate regression parametric study on dem input parameters of free-flowing and cohesive powders with experimental data-based validation. Computational Particle Mechanics, 8:87-111, Jan 2021. URL: https://doi.org/10.1007/s40571-020-00315-8, doi:10.1007/s40571-020-00315-8. This article has 39 citations.

33. (elkassem2021amultivariateregression pages 23-24): Bilal El-Kassem, Nizar Salloum, Thomas Brinz, Yousef Heider, and Bernd Markert. A multivariate regression parametric study on dem input parameters of free-flowing and cohesive powders with experimental data-based validation. Computational Particle Mechanics, 8:87-111, Jan 2021. URL: https://doi.org/10.1007/s40571-020-00315-8, doi:10.1007/s40571-020-00315-8. This article has 39 citations.

34. (nicusan2025accesnoninvasivesimulation pages 2-4): ACCES: Non-Invasive Simulation Calibration via Optimisation using Evolutionary Algorithms and Metaprogramming This article has 11 citations.

35. (nicusan2025accesnoninvasivesimulation pages 25-27): ACCES: Non-Invasive Simulation Calibration via Optimisation using Evolutionary Algorithms and Metaprogramming This article has 11 citations.

36. (cocco2017cfddemmodelingthe pages 10-14): R Cocco, WD Fullmer, P Liu, and CM Hrenya. Cfd-dem: modeling the small to understand the large. Unknown journal, 2017.

37. (darvish2025matterixtowarda pages 2-5): Kourosh Darvish, Arjun Sohal, Abhijoy Mandal, Hatem Fakhruldeen, Nikola Radulov, Zhengxue Zhou, Satheeshkumar Veeramani, Joshua Choi, Sijie Han, Brayden Zhang, Jeeyeoun Chae, Alex Wright, Yijie Wang, Hossein Darvish, Yuchi Zhao, Gary Tom, Han Hao, Miroslav Bogdanovic, Gabriella Pizzuto, Andrew I. Cooper, Alán Aspuru Guzik, Florian Shkurti, and Animesh Garg. Matterix: toward a digital twin for robotics-assisted chemistry laboratory automation. Nature Computational Science, 6(1):67-82, Dec 2026. URL: https://doi.org/10.1038/s43588-025-00924-4, doi:10.1038/s43588-025-00924-4. This article has 12 citations and is from a peer-reviewed journal.

38. (darvish2025matterixtowarda pages 1-2): Kourosh Darvish, Arjun Sohal, Abhijoy Mandal, Hatem Fakhruldeen, Nikola Radulov, Zhengxue Zhou, Satheeshkumar Veeramani, Joshua Choi, Sijie Han, Brayden Zhang, Jeeyeoun Chae, Alex Wright, Yijie Wang, Hossein Darvish, Yuchi Zhao, Gary Tom, Han Hao, Miroslav Bogdanovic, Gabriella Pizzuto, Andrew I. Cooper, Alán Aspuru Guzik, Florian Shkurti, and Animesh Garg. Matterix: toward a digital twin for robotics-assisted chemistry laboratory automation. Nature Computational Science, 6(1):67-82, Dec 2026. URL: https://doi.org/10.1038/s43588-025-00924-4, doi:10.1038/s43588-025-00924-4. This article has 12 citations and is from a peer-reviewed journal.

39. (darvish2025matterixtowarda pages 11-14): Kourosh Darvish, Arjun Sohal, Abhijoy Mandal, Hatem Fakhruldeen, Nikola Radulov, Zhengxue Zhou, Satheeshkumar Veeramani, Joshua Choi, Sijie Han, Brayden Zhang, Jeeyeoun Chae, Alex Wright, Yijie Wang, Hossein Darvish, Yuchi Zhao, Gary Tom, Han Hao, Miroslav Bogdanovic, Gabriella Pizzuto, Andrew I. Cooper, Alán Aspuru Guzik, Florian Shkurti, and Animesh Garg. Matterix: toward a digital twin for robotics-assisted chemistry laboratory automation. Nature Computational Science, 6(1):67-82, Dec 2026. URL: https://doi.org/10.1038/s43588-025-00924-4, doi:10.1038/s43588-025-00924-4. This article has 12 citations and is from a peer-reviewed journal.

40. (darvish2025matterixtowarda pages 7-9): Kourosh Darvish, Arjun Sohal, Abhijoy Mandal, Hatem Fakhruldeen, Nikola Radulov, Zhengxue Zhou, Satheeshkumar Veeramani, Joshua Choi, Sijie Han, Brayden Zhang, Jeeyeoun Chae, Alex Wright, Yijie Wang, Hossein Darvish, Yuchi Zhao, Gary Tom, Han Hao, Miroslav Bogdanovic, Gabriella Pizzuto, Andrew I. Cooper, Alán Aspuru Guzik, Florian Shkurti, and Animesh Garg. Matterix: toward a digital twin for robotics-assisted chemistry laboratory automation. Nature Computational Science, 6(1):67-82, Dec 2026. URL: https://doi.org/10.1038/s43588-025-00924-4, doi:10.1038/s43588-025-00924-4. This article has 12 citations and is from a peer-reviewed journal.

41. (tai2025gritsaspillageaware pages 2-4): Yen-Ling Tai, Yi-Ru Yang, Kuan-Ting Yu, Yu-Wei Chao, and Yi-Ting Chen. Grits: a spillage-aware guided diffusion policy for robot food scooping tasks. ArXiv, Oct 2025. URL: https://doi.org/10.48550/arxiv.2510.00573, doi:10.48550/arxiv.2510.00573. This article has 3 citations.

42. (nicusan2025accesnoninvasivesimulation pages 9-11): ACCES: Non-Invasive Simulation Calibration via Optimisation using Evolutionary Algorithms and Metaprogramming This article has 11 citations.

43. (darvish2025matterixtowarda pages 14-15): Kourosh Darvish, Arjun Sohal, Abhijoy Mandal, Hatem Fakhruldeen, Nikola Radulov, Zhengxue Zhou, Satheeshkumar Veeramani, Joshua Choi, Sijie Han, Brayden Zhang, Jeeyeoun Chae, Alex Wright, Yijie Wang, Hossein Darvish, Yuchi Zhao, Gary Tom, Han Hao, Miroslav Bogdanovic, Gabriella Pizzuto, Andrew I. Cooper, Alán Aspuru Guzik, Florian Shkurti, and Animesh Garg. Matterix: toward a digital twin for robotics-assisted chemistry laboratory automation. Nature Computational Science, 6(1):67-82, Dec 2026. URL: https://doi.org/10.1038/s43588-025-00924-4, doi:10.1038/s43588-025-00924-4. This article has 12 citations and is from a peer-reviewed journal.

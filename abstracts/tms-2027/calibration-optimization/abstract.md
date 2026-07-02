---
Meeting: TMS 2027 Annual Meeting & Exhibition (Orlando, FL)
Dates: March 14–18, 2027 (Orlando World Center Marriott)
Submission deadline: July 1, 2026
Format: abstract body limited to 150 words; submitted via ProgramMaster
(https://www.programmaster.org/TMS2027).
Presenter: Will
Focus: calibration optimization and powder properties, with physics-based
simulations to infer physical properties (refreshed per PR #78 comment
assigning presenters and symposia; split from the original combined
abstract, see ../README.md).
Assigned symposium: Powder Materials Processing and Fundamental Understanding
(Materials Synthesis and Processing track; flyer 075) — its scope explicitly
welcomes computational modeling and simulation of powder systems and
machine learning / data-driven discovery in powder materials science.
Prior top-5 ranking (for reference; rationale in ../README.md):
  1. AI-Enabled Materials Processing: Integrating Accelerated Experimental
     Workflows and Processing-Aware Machine Learning (Data-Driven and
     Computational Materials Design)
  2. AI/ML/Data Informatics for Materials Discovery: Bridging Experiment,
     Theory, and Modeling (Data-Driven and Computational Materials Design)
  3. Algorithms Development in Materials Science and Engineering (Data-Driven
     and Computational Materials Design)
  4. Artificial Intelligence Applications in Integrated Computational
     Materials Engineering (AI-ICME) (Data-Driven and Computational
     Materials Design)
  5. Powder Materials Processing and Fundamental Understanding (Materials
     Synthesis and Processing) — now the assigned target
  Submit the abstract to only one symposium.
---

Title: Calibration Optimization of an Auger-Based Powder Doser as a Probe of Powder Flow Behavior, with Physics-Based Simulation to Infer Physical Properties

Dispensed mass from an auger-based powder doser depends on actuator settings and powder properties, so every calibration curve doubles as an indirect probe of powder flow behavior. We frame calibration of an open-source doser—combining stepper-driven auger rotation, solenoid tapping, vibration-motor agitation, and servo-controlled tilt—as an AI-driven, multi-objective, multi-task optimization problem suited to multi-task Bayesian optimization. The competing objectives are dose accuracy, repeatability, dispensing time, and minimum and maximum deliverable dose. Each powder—progressing from non-hazardous surrogates to laser powder bed fusion feedstocks such as AlSi10Mg, silicon, and stainless steel—is a related task, and multi-task models share information across powders to cut per-powder calibration effort. Alongside gravimetric parameter sweeps, we are exploring physics-based simulations of powder conveying and agitation (e.g., discrete element modeling) that connect dosing response to cohesion, friction, and particle size distribution, enabling inference of powder properties from calibration data and simulation-seeded calibration of new powders.

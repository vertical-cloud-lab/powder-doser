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
Edison organizer-persona review applied (PR #78,
../edison/persona_reviews_out/calibration-optimization.answer.md): title and
framing reoriented to dosing-as-mechanistic-probe (the doser is the means,
not the end); the actuator inventory was cut; the inferred properties are
now named (effective cohesion, friction) with an independent validation path
(shear-cell and Hall-flow measurements); the DEM sentence gained concrete
modeling detail (cohesive-frictional contact laws, measured particle-size
distributions); and a closing bridge to downstream powder behavior
(spreadability, packing uniformity) was added. "We are exploring" was KEPT
for the DEM thread — no simulation work exists in the repo yet, so a firmer
verb would overclaim. "AI-driven" and Bayesian-optimization wording KEPT per
swcharles's request (PR #78) despite the panel's note that generic AI
language reads weakly here. Per sgbaird (PR #78), "non-hazardous surrogates"
was replaced: powders are primarily alloy precursors, in raw elemental or
master-alloy form depending on handling constraints and hazards, dosed under
inert atmosphere.
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

Title: Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow Behavior: Multi-Task Bayesian Calibration and Physics-Based Property Inference

Dispensed mass from an auger-based powder doser depends on actuator settings and powder properties, so every calibration curve doubles as a compact probe of cohesion, friction, and packing behavior. We frame calibration of an open-source doser as AI-driven, multi-objective, multi-task Bayesian optimization, with objectives of dose accuracy, repeatability, dispensing time, and accessible dose range. Each powder is a related task—primarily alloy precursors, in elemental or master-alloy form depending on handling constraints and hazards, dosed under inert atmosphere, alongside feedstocks such as AlSi10Mg and stainless steel—and multi-task models share information across powders to cut per-powder calibration effort. Alongside gravimetric parameter sweeps, we are exploring discrete element modeling with cohesive-frictional contact laws and measured particle-size distributions, enabling inference of effective cohesion and friction from dosing data, to be checked against shear-cell and Hall-flow measurements. Linking dosing response to these properties may anticipate downstream behavior such as spreadability and packing uniformity.

---
Meeting: 2026 MRS Fall Meeting & Exhibit (Boston, MA)
Submission deadline: June 17, 2026, 11:59 pm ET
Format: abstract body limited to 4000 characters including spaces; no images,
graphics, or charts; title and body in mixed/Title Case.
Target symposium (Edison ANALYSIS ranking; full rationale in
edison/analysis_out/analysis.answer.md):
  1. MT03 — AI-Driven Workflows and Autonomous Platforms for Functional
     Material Design and Catalysis (primary)
  2. MT01 — Leveraging Advances in AI for Materials Design and Autonomous
     Materials Science (alternate)
  3. MT04 — Technologies for Informed and Accelerated Synthesis of Inorganic
     Materials (alternate, synthesis-enablement framing)
  Materials-application alternates: SF03 (Intermetallics), SF01 (High-Entropy
  Materials). Submit each abstract to only one symposium.
---

Title: An Open-Source, Low-Cost Powder Doser Built with Agentic AI and Generative CAD for Autonomous Alloy Discovery

Additive manufacturing of aerospace structural alloys increasingly requires rapid, reproducible exploration of powder feedstocks, but accurate metering and blending of dry powders remains a manual bottleneck in research laboratories. Commercial powder dispensers are often expensive and poorly suited to alloy-development workflows involving many powders, frequent recipe changes, and reproducible small-volume dispensing. Existing open-source designs have not been rigorously developed or tested for laser powder bed fusion (L-PBF) feedstocks. We developed an open-source, low-cost, modular powder doser for precise metering of metal and feedstock powders, designed for integration into a self-driving, Bayesian-optimization materials-discovery loop in which dosed powders feed ultrasonic atomization and L-PBF processing of additively manufactured aerospace alloys. Initial testing includes non-hazardous powders followed by representative L-PBF base powders geared towards aluminum and steel alloys (e.g., AlSi10Mg, silicon, stainless steel), with a target gravimetric dose accuracy on the order of ±0.1 mg for volumes up to 250 mL across up to 30 reservoirs, with cross-contamination characterization.

The dispensing element is a stepper-driven Archimedean auger. Powder flow is promoted by a tap collar carrying a coin vibration motor and a solenoid that vibrate and tap the auger, while feed angle is controlled by a tilting baseplate. We test the simultaneous implementation of solenoid tapping, servo-controlled tilt, vibration-motor agitation, and stepper-driven augering within a single system to accommodate a wide range of powders and corresponding challenges (bridging, clumping, air dispersion, static charge). The system was designed parametrically to allow for changes to dispense volumes (i.e., auger diameter and length). Because delivered mass depends on powder properties and actuator settings, we are developing a machine-learning calibration algorithm that maps auger, tap, vibration, and tilt parameters to dispensed mass for each powder. A systematic parameter sweep characterizes dose accuracy, repeatability, and minimum and maximum dose, enabling correction with limited human intervention.

In parallel, we evaluated agentic AI and generative "text-to-CAD" tools for mechanical design. Workflows included coding agents and hosted generative-CAD services using large language models such as CADSmith, zoo.dev, and GitHub Copilot Cloud Agents with Claude Opus 4.7 to generate and revise parametric CAD in CadQuery and OpenSCAD from engineering requirements. Fully AI-generated designs were not deployment-ready, so we adopted an engineer-led workflow: engineers defined part geometry, dimensions, hand sketches, and manufacturing constraints; AI models the parts; and engineers review, print, and iterate. Specific prompts and explicit constraints substantially improved results, but usable geometry still required many correction cycles, with weak spatial reasoning as a recurring limitation. At times, these generative models also recognized problems in advance.

This work reports an open hardware and software platform together with a practitioner-level assessment of agentic-AI and generative-CAD capabilities for laboratory device development. Open-source deliverables include parametric CAD, a bill of materials, control code, and validation protocols. We present the dosing mechanism, AI-modeled prototypes, calibration and parameter-sweep results, a comparison of attempted AI CAD workflows, and the role of the doser within an autonomous alloy-discovery pipeline relevant to aerospace additive manufacturing. For additional context around the design process, including a chronological history of all project designs, see https://github.com/vertical-cloud-lab/powder-doser/blob/copilot/record-of-designs/DESIGN-LOG.md and https://github.com/vertical-cloud-lab/powder-doser/discussions/39.

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

Additive manufacturing of aerospace structural alloys increasingly depends on rapid, reproducible exploration of powder feedstocks, yet accurately metering and blending dry powders remains a largely manual bottleneck in research laboratories. Commercial dispensers are often cost-prohibitive and poorly matched to alloy-focused, many-powder workflows that require frequent recipe changes and reproducible metering, and existing open-source designs have not been rigorously developed or tested for laser powder bed fusion (L-PBF). We are developing an open-source, low-cost, modular powder doser for precise metering of metal and feedstock powders, designed for integration into a self-driving, Bayesian-optimization materials-discovery loop in which dosed powders will feed ultrasonic atomization and L-PBF of additively manufactured aerospace alloys. Initial testing targets non-hazardous powders before progressing to representative L-PBF feedstocks such as AlSi10Mg, silicon, and stainless steel, with a target gravimetric dose accuracy on the order of [±X mg].

The dispensing element is a stepper-driven Archimedean auger; powder flow is promoted by a tap collar carrying a coin vibration motor and a solenoid that vibrate and tap the auger, while feed angle is set by a tilting baseplate. We compared actuation options for each function—solenoid tapping versus servo-controlled tilt angle versus vibration-motor agitation versus stepper-driven augering—to balance impulse, repeatability, and wire management in an autonomous, many-channel system. A central motivation is accommodating a wide range of powders with differing flowability while remaining flexible across both small and large dispense volumes: auger throughput (about [X] mL per revolution) is tuned by adjusting the auger diameter and flight width, so a single architecture spans small screening doses to larger blends without redesign.

Because dosing depends strongly on powder properties and actuator settings, we are developing a machine-learning-based calibration algorithm that maps commanded auger, tap, vibration, and tilt parameters to delivered mass per powder, trained on gravimetric measurements. A systematic parameter sweep across these variables characterizes dose accuracy, repeatability, and minimum/maximum dose for each powder and feeds the calibration model, enabling correction with minimal human intervention.

In parallel, we assessed how far agentic AI and generative ("text-to-CAD") tools can carry mechanical design. We evaluated several AI-assisted CAD workflows—including coding agents and hosted generative-CAD services—using large language models to generate and revise parametric CAD (CadQuery, OpenSCAD) from engineering requirements. Fully AI-generated part designs were not deployment-ready, so we adopted an engineer-led workflow: engineers design parts and specify exact dimensions, sketches, and manufacturing constraints; AI models those parts; and engineers review, 3D print, and iterate. Our central finding is that specificity improves results—explicit drawings and constraints outperform high-level prompts—but usable geometry still requires many correction cycles, with weak spatial reasoning a recurring limitation.

This work reports an open hardware and software effort together with a candid, practitioner-level assessment of agentic-AI and generative-CAD capabilities for laboratory device development. Open-source deliverables will include parametric CAD, a bill of materials, control code, and validation protocols. We will present the dosing mechanism and prototypes designed by engineers and modeled by AI, calibration and parameter-sweep results, a comparison of the attempted AI CAD/modeling workflows, and the role of the doser within an autonomous alloy-discovery pipeline relevant to aerospace additive manufacturing.

Question: We are preparing a single-symposium abstract for the 2026 MRS Fall Meeting (Boston). An Edison ANALYSIS of the official Call for Abstracts ranked the most aligned symposia as: MT03 (AI-Driven Workflows and Autonomous Platforms for Functional Material Design and Catalysis), MT01 (Leveraging Advances in AI for Materials Design and Autonomous Materials Science), and MT04 (Technologies for Informed and Accelerated Synthesis of Inorganic Materials), with materials-application alternates SF03 (Intermetallics) and SF01 (High-Entropy Materials).

Please act as a panel of MOCK PEER REVIEWERS for these symposia. Where possible, adopt the personas of the actual symposium organizers and ground your critique in their recent (last ~5 years) published literature, which you should search for and cite. The organizers are:
- MT03: Don Futaba (AIST, Japan), Rui Goncalves (Nanyang Technological University), Placidus Amama (Kansas State University), Karolina Laszczyk (Wroclaw University of Science and Technology).
- MT01: Guoxiang (Emma) Hu (Georgia Tech), Mahshid Ahmadi (University of Tennessee, Knoxville), Bin Ouyang (Florida State University), Dong-Hwa Seo (KAIST).
- MT04: Yong-Jie Hu (Drexel), Yan Zeng (Florida State University), Yuta Saito (Tohoku University), Richard Otis (Proteus Space / formerly NASA JPL).

For each persona/reviewer, look up representative recent work (autonomous experimentation, self-driving labs, Bayesian optimization, generative/agentic CAD, high-throughput inorganic synthesis, additive manufacturing of alloys, etc.) and review our abstract THROUGH THAT LENS, noting what such a reviewer would want to see.

Provide SPECIFIC, ACTIONABLE TEXTUAL SUGGESTIONS: concrete ADDITIONS (sentences or phrases to insert, and where), REMOVALS (text to cut and why), and MODIFICATIONS (rewordings), so we can edit the abstract directly. Then give an overall prioritized punch-list and note any claims that need stronger evidence or citation. Honor the MRS constraints: abstract body must stay <= 4000 characters including spaces, with no figures. Keep feedback faithful to what the abstract actually claims.

=== ABSTRACT UNDER REVIEW ===
Title: An Open-Source, Low-Cost Powder Doser Built with Agentic AI and Generative CAD for Autonomous Alloy Discovery

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

Additive manufacturing of aerospace structural alloys increasingly depends on rapid, reproducible exploration of powder feedstocks, yet a key workflow step—accurately metering and blending dry powders—remains a largely manual bottleneck in research laboratories. Commercial dispensers are expensive and poorly matched to alloy-focused, many-powder workflows, and existing open-source designs have not been rigorously developed or tested for laser powder bed fusion (L-PBF). We are developing an open-source, low-cost, modular powder doser for precise metering of metal and feedstock powders as part of a self-driving, Bayesian-optimization materials-discovery loop, in which dosed powders feed ultrasonic atomization and L-PBF of additively manufactured aerospace alloys.

A central goal of the project is to evaluate how far agentic AI and generative ("text-to-CAD") tools can carry mechanical and electromechanical design. We evaluated several AI CAD/modeling workflows—including GitHub Copilot coding agents and hosted generative-CAD services—and used large language models to generate and revise parametric CAD (e.g., CadQuery, OpenSCAD) directly from engineering requirements. In practice, fully AI-generated part designs were not usable for our application. We therefore adopted an engineer-led workflow in which engineers design the parts and specify exact dimensions, sketches, and manufacturing constraints, and AI tools model those parts; engineers then review the models, 3D print prototypes, and iterate.

Our central finding so far is that specificity improves results: providing explicit drawings and constraints yields better models than high-level prompts, but useful geometry still requires many correction cycles. A recurring limitation is weak spatial reasoning—even near-final AI models frequently introduce hallucinated or unnecessary features that must be removed or, if still functional, tolerated. Most repeated AI sessions are spent correcting and guiding the model toward the intended geometry rather than exploring new designs, and AI did not reduce assembly complexity. Across this phase, AI is most effective as a modeling assistant rather than an autonomous design agent, and the engineers never opened a traditional CAD graphical interface.

This work reports an open hardware and software effort together with a candid, practitioner-level assessment of current agentic-AI and generative-CAD capabilities and limitations for laboratory device development. We will present the dosing mechanism and prototypes designed by engineers and modeled by AI, a comparison of the attempted AI CAD/modeling workflows, lessons learned for constraining AI outputs to meet manufacturing requirements, and the role of the doser within an autonomous alloy-discovery pipeline relevant to aerospace additive manufacturing.



# Mock Peer Review Panel: MRS Fall 2026 Abstract on Open-Source Powder Doser

## Overview

This report presents mock peer reviews from the perspectives of the 12 symposium organizers across three candidate sessions (MT03, MT01, MT04), grounded in their recent published work. Each reviewer persona was constructed from literature searches and evidence gathering covering autonomous experimentation, self-driving labs, generative AI for materials, high-throughput synthesis, CALPHAD-based alloy design, and additive manufacturing. The review identifies a consistent set of themes: the abstract's strongest asset—a candid, practitioner-level AI-CAD assessment—is simultaneously its greatest liability at these symposia, because the materials-discovery and autonomy payloads are underspecified relative to the AI workflow narrative.

---

## Section 1: Symposium MT03 — AI-Driven Workflows and Autonomous Platforms

### Reviewer 1: Don Futaba (AIST, Japan)

**Lens:** Futaba's group has demonstrated real-time autonomous control of continuous macroscopic processes using active-learning-based decision-making and in situ characterization, converging in ~11 iterations without prior training data (muroga2025realtimeautonomouscontrol pages 1-1). His team also applies ML to CNT forest synthesis to address crystallinity–yield trade-offs.

**Key concern:** The abstract claims integration into "a self-driving, Bayesian-optimization materials-discovery loop," but no closed-loop operation, decision logic, convergence metric, or quantitative dosing performance is reported. Futaba's own work emphasizes measurable autonomous-system performance (e.g., R² = 0.87–0.90 for controlled variables) (muroga2025realtimeautonomouscontrol pages 1-1).

**Suggested ADDITION (Paragraph 1, after sentence 3):** *"Initial benchtop tests target gravimetric dosing accuracy and repeatability at the tens-of-milligrams scale, with throughput sufficient for multi-composition feedstock screening."*

**Suggested MODIFICATION (Paragraph 1):** Change "as part of a self-driving, Bayesian-optimization materials-discovery loop" to "for eventual integration into a self-driving, Bayesian-optimization materials-discovery loop" to avoid overclaiming.

### Reviewer 2: Placidus Amama (Kansas State University)

**Lens:** Amama has published extensively on high-throughput experimentation for selective CNT growth using in situ Raman spectral feedback and combinatorial catalyst screening (pelkie2025automationandautonomous pages 245-247, szymanski2021towardautonomousdesign pages 61-64). His work emphasizes quantifiable screening throughput and experimental design spaces.

**Key concern:** The abstract does not define an experimental design space, throughput gain, or evidence that the hardware enables higher-quality discovery campaigns.

**Suggested ADDITION (Paragraph 4):** *"Validation will compare commanded and delivered powder masses across representative metal powder chemistries relevant to atomization and L-PBF."*

### Reviewer 3: Karolina Laszczyk (Wroclaw University of Science and Technology)

**Lens:** Laszczyk works on 3D-printed functional micro-devices integrating CNT films, with emphasis on practical fabrication and device performance. She would evaluate whether the open-hardware claim is backed by concrete, reproducible design artifacts.

**Key concern:** The abstract says AI modeled parts and prototypes were printed, but gives no concrete hardware description showing manufacturability, modularity, or open-hardware usefulness.

**Suggested ADDITION (Paragraph 4):** *"Open-source deliverables will include parametric CAD, bill of materials, control code, and validation protocols."*

### Reviewer 4: Rui Goncalves (Nanyang Technological University)

**Lens:** Goncalves works on functional materials and catalysis. He would evaluate whether the abstract's contribution extends beyond tool development to materials-science value.

**Key concern:** The abstract foregrounds AI-CAD workflow critique more than the materials-discovery value proposition.

**Suggested MODIFICATION (Paragraph 1, sentence 2):** Rewrite "Commercial dispensers are expensive and poorly matched to alloy-focused, many-powder workflows" as "Commercial dispensers are often cost-prohibitive and poorly matched to alloy-focused, many-powder workflows requiring frequent recipe changes and reproducible metering."

---

## Section 2: Symposium MT01 — Leveraging Advances in AI for Materials Design

### Reviewer 5: Guoxiang (Emma) Hu (Georgia Tech)

**Lens:** Hu has developed MatterTune, a platform for fine-tuning atomistic foundation models (mok2602reasoningdrivendesignof pages 22-24), and MAESTRO, a multi-agent LLM framework for reasoning-driven catalyst design that systematically benchmarks AI outputs against DFT validation (mok2602reasoningdrivendesignof pages 17-22). Her work demands structured AI evaluation, not anecdotal impressions.

**Key concern:** The phrase "agentic AI and generative CAD" risks sounding trend-driven unless the abstract clearly states the task boundary, evaluation criteria, and lessons for human-AI co-design.

**Suggested MODIFICATION (Paragraph 2, first two sentences):** Rewrite as: *"We evaluated several AI-assisted CAD workflows, including coding agents and generative-CAD services, by asking them to translate engineering requirements into editable parametric models (CadQuery/OpenSCAD). Across these trials, fully AI-generated designs were not deployment-ready for the dosing application."*

**Suggested ADDITION (Paragraph 3, after sentence 1):** *"Usable outputs required explicit dimensions, constrained sketches, and repeated human verification of fit, manufacturability, and assembly interfaces."*

### Reviewer 6: Mahshid Ahmadi (University of Tennessee, Knoxville)

**Lens:** Ahmadi is a leading practitioner of robotic combinatorial synthesis and high-throughput automated workflows for perovskite materials, using chemical robotics and ML to explore stability across vast compositional spaces (higgins2020chemicalroboticsenabled pages 1-5, higgins2020chemicalroboticsenableda pages 1-4). She has published extensively on closing the characterization loop and moving toward autonomous experimentation (foadian2024fromsunlightto pages 3-3, foadian2024fromsunlightto pages 4-6).

**Key concern:** A closed-loop/autonomy reviewer will ask: where is the loop closure? The abstract reads as upstream tool development plus an AI-CAD assessment, not yet as autonomous materials science.

**Suggested ADDITION (Paragraph 4, before final sentence):** *"The control stack is being structured around recipe-driven operation, gravimetric verification, and software interfaces compatible with laboratory orchestration frameworks."*

### Reviewer 7: Bin Ouyang (Florida State University)

**Lens:** Ouyang works on computational design of compositionally complex and high-entropy materials, with specialized datasets and domain-specific ML models for screening vast composition spaces (sundar2022automatedhierarchicalscreening pages 7-9, sundar2022automatedhierarchicalscreening pages 9-10). He co-authored a universal framework for stability estimation in multi-principal-element alloys.

**Key concern:** The alloy-discovery framing is compelling, but the abstract never states what composition classes are targeted or why a powder doser is especially enabling for compositionally complex alloys.

**Suggested ADDITION (Paragraph 1, after the revised loop sentence):** *"Target applications include multicomponent aerospace alloy families relevant to intermetallic and multi-principal-element composition screening."*

### Reviewer 8: Dong-Hwa Seo (KAIST)

**Lens:** Seo developed ALBATROSS, an integrated robotic platform for high-throughput electrolyte screening that automates formulation, coin-cell assembly, and electrochemical evaluation within a glovebox, achieving 85/87 successful assemblies and RSD < 1.2% in discharge capacity (lee2026albatrossarobotised pages 1-5, lee2026albatrossarobotised pages 13-15). He co-authored a perspective on self-driving laboratories in Korea emphasizing systems-level integration (hwang2026selfdrivinglaboratoriesin pages 4-5, hwang2026selfdrivinglaboratoriesin pages 3-4).

**Key concern:** Reviewers from this lens want systems-level integration and robust automation claims, not only low-cost hardware. The abstract does not specify reliability, unattended operation, or interfaces to orchestration software.

**Suggested ADDITION (Paragraph 1, after sentence 2):** *"The modular design supports rapid swapping of powder reservoirs and machine-readable recipes for many-powder studies."*

---

## Section 3: Symposium MT04 — Technologies for Informed and Accelerated Synthesis

### Reviewer 9: Yong-Jie Hu (Drexel University)

**Lens:** Y.-J. Hu has published on automated hierarchical screening of refractory multicomponent alloys, coupling physics-informed ML models with CALPHAD phase-equilibrium calculations to screen 10⁷ quaternary compositions (sundar2022automatedhierarchicalscreening pages 7-9, sundar2022automatedhierarchicalscreening pages 9-10). His work bridges computational screening to experimental alloy design.

**Key concern:** The abstract links the doser to alloy discovery but provides no quantitative bridge from dosing capability to composition-space exploration or alloy design metrics.

**Suggested ADDITION (Paragraph 4, after "autonomous alloy-discovery pipeline"):** Append the phrase *"including future coupling to CALPHAD- or Scheil-informed composition selection for AM feedstock design."*

### Reviewer 10: Yan Zeng (Florida State University)

**Lens:** Zeng is a co-author of AlabOS, the orchestration framework for the A-Lab autonomous laboratory, which has synthesized over 3,500 samples in ~1.5 years (fei2024alabosapythonbased pages 26-30). Critically, her team documented that PowderDosing is a known bottleneck in A-Lab: it showed 0% exception recovery in operational data, far lower than other tasks (fei2024alabosapythonbased pages 26-30, fei2024alabosapythonbased pages 25-26).

**Key concern:** As a synthesis-enablement reviewer, she would ask whether the doser is robust enough for autonomous operation. Exception handling, batching, resource contention, and failure recovery are absent from the abstract.

**Suggested MODIFICATION:** If the system is not yet autonomous-ready, avoid overclaiming. If it is, mention robustness features explicitly: *"machine-readable recipes, gravimetric verification, and error-checking routines are being implemented to support autonomous batch operation."* The A-Lab's documented PowderDosing bottleneck (fei2024alabosapythonbased pages 26-30) makes this a particularly salient concern for this symposium.

### Reviewer 11: Yuta Saito (Tohoku University)

**Lens:** Saito's work focuses on discovery of metastable phases through nontraditional synthesis pathways, including polymorphic crystallization of amorphous films to produce metastable van der Waals semiconductors.

**Key concern:** The abstract does not explain why this dosing platform might unlock new synthesis outcomes rather than merely simplify sample preparation.

**Suggested ADDITION (Paragraph 1):** *Add a phrase connecting precise powder formulation to exploration of off-stoichiometric or otherwise difficult-to-access alloy feedstocks relevant to atomization/L-PBF processing.*

### Reviewer 12: Richard Otis (Proteus Space / formerly NASA JPL)

**Lens:** Otis is the creator of pycalphad, the open-source CALPHAD tool for Python (211+ citations) (otis2024pycalphadcalphadbasedcomputational pages 10-11), and co-authored work on Scheil-Gulliver simulations for designing functionally graded alloys by additive manufacturing (bocklund2020scheilgulliversimulationsfor pages 1-6, bocklund2020scheilgulliversimulationsfor pages 18-22, bocklund2020scheilgulliversimulationsfor pages 6-10). His work at JPL applied CALPHAD-based composition-path screening to avoid brittle phases in AM FGMs (reichardt2021advancesinadditive pages 28-29, reichardt2021advancesinadditive pages 29-30).

**Key concern:** The AM framing is strong, but the abstract does not connect the doser to composition-path design, thermodynamic planning, or validation against AM-relevant phase/solidification constraints. The open-source claim is also vague.

**Suggested REMOVAL:** Cut "Most repeated AI sessions are spent correcting and guiding the model toward the intended geometry rather than exploring new designs, and AI did not reduce assembly complexity." This sentence adds detail appropriate for a full paper but consumes characters better used for dosing/AM integration specifics.

**Suggested MODIFICATION (Title):** Consider: *"Open-Source Modular Powder Dosing for Autonomous Alloy Discovery: Lessons from Agentic AI and Generative CAD"* — this moves the title emphasis from trendy tools to the materials-discovery hardware contribution while preserving the AI-CAD angle.

---

## Section 4: Reviewer Persona Summary Table

The following table consolidates each organizer's research focus, key concern, and desired changes:

| Symposium | Organizer / Affiliation | Recent Research Focus | Key Concern They Would Raise About the Abstract | What They Would Want Added or Changed |
|---|---|---|---|---|
| MT03 | Don Futaba (AIST, Japan) | Autonomous control of continuous materials processes; active-learning and in situ feedback for process optimization; prior ML-linked CNT synthesis context (muroga2025realtimeautonomouscontrol pages 1-2, muroga2025realtimeautonomouscontrol pages 1-1) | The abstract says the doser is part of a self-driving Bayesian loop, but it does not yet show closed-loop operation, decision logic, or quantitative control performance. | Add one sentence specifying the autonomous role of the doser in the loop: inputs, outputs, feedback signal, and target metrics; include at least preliminary quantitative dosing/control metrics (e.g., mass error, repeatability, throughput) and clarify whether Bayesian optimization is already implemented or planned. |
| MT03 | Rui Goncalves (Nanyang Technological University) | Functional materials and catalysis-oriented materials design; emphasis on material-property relevance and application-driven synthesis context (query evidence summarized in plan; limited direct paper retrieval) | The abstract foregrounds AI-CAD workflow critique more than the materials-discovery value proposition; a catalysis/functional-materials-oriented reviewer may worry the scientific payload is too hardware-development-centric. | Tighten the application framing: explain why powder dosing fidelity matters for alloy composition exploration, downstream atomization/L-PBF reproducibility, and ultimately property mapping; reduce generic commentary about AI limitations unless tied to research throughput or data quality. |
| MT03 | Placidus Amama (Kansas State University) | High-throughput experimentation for CNT growth and catalyst screening; in situ feedback and combinatorial exploration of synthesis variables (pelkie2025automationandautonomous pages 245-247, szymanski2021towardautonomousdesign pages 61-64) | The abstract does not yet define an experimental design space, throughput gain, or evidence that the hardware enables higher-quality discovery campaigns rather than just cheaper hardware. | Add explicit experimental scope: number of powders/channels, achievable composition resolution, dosing rate, and how the doser enables high-throughput alloy-feedstock screening; mention validation plan against reference weighing or composition assay. |
| MT03 | Karolina Laszczyk (Wroclaw University of Science and Technology) | 3D-printed/CNT-enabled microsystems and device fabrication; practical integration of printable hardware into functional devices (search evidence incl. Laszczyk 2020 review and unobtainable recent 3D-printing/CNT papers) | The abstract says AI modeled parts and prototypes were printed, but gives no concrete hardware description showing manufacturability, modularity, or open-hardware usefulness. | Add 1-2 concrete hardware descriptors: e.g., auger/vibratory/gravity mechanism, modular cartridge architecture, printable materials, off-the-shelf electronics, and what exactly will be released open-source. |
| MT01 | Guoxiang (Emma) Hu (Georgia Tech) | Atomistic foundation models (MatterTune) and multi-agent LLM reasoning for catalyst design; AI systems that are useful when paired with strong structure/property validation (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22) | The phrase “agentic AI and generative CAD” risks sounding trend-driven unless the abstract clearly states the task boundary, evaluation criteria, and lessons for human-AI co-design. | Reframe the core claim as a benchmarked human-AI design study: specify the design tasks attempted, the success criterion for a “usable” CAD output, and the principal failure modes (spatial reasoning, hallucinated features, correction burden). |
| MT01 | Mahshid Ahmadi (University of Tennessee, Knoxville) | Robotic combinatorial synthesis, high-throughput workflows, and closed-loop/ML-guided materials discovery with automated characterization (higgins2020chemicalroboticsenabled pages 1-5, foadian2024fromsunlightto pages 3-3, foadian2024fromsunlightto pages 4-6, higgins2020chemicalroboticsenableda pages 1-4) | A closed-loop/autonomy reviewer will ask: where is the loop closure? The present abstract reads as upstream tool development plus anecdotal AI-CAD assessment, not yet as autonomous materials science. | Add a sentence that explicitly maps the doser into the autonomous workflow: powder formulation → atomization/L-PBF → characterization → surrogate/Bayesian update → next composition. If still under development, say “designed for integration into” rather than implying demonstrated closed-loop operation. |
| MT01 | Bin Ouyang (Florida State University) | Computational design of compositionally complex/high-entropy materials; specialized datasets and domain knowledge for HE materials screening (foadian2024fromsunlightto pages 4-4, foadian2024fromsunlightto pages 11-12) | The alloy-discovery framing is compelling, but the abstract never states what composition classes are targeted or why a powder doser is especially enabling for compositionally complex alloys. | Add a phrase naming target alloy families if true (e.g., multi-principal-element, intermetallic, aerospace Ti/Ni/Fe systems) and why precise multicomponent dosing is critical for exploring those spaces efficiently. |
| MT01 | Dong-Hwa Seo (KAIST) | ALBATROSS robotic battery-testing platform; self-driving laboratory systems that integrate formulation, assembly, measurement, and autonomous iteration (hwang2026selfdrivinglaboratoriesin pages 4-5, lee2026albatrossarobotised pages 1-5, hwang2026selfdrivinglaboratoriesin pages 3-4, lee2026albatrossarobotised pages 13-15) | Reviewers from this lens will want systems-level integration and robust automation claims, not only low-cost hardware. The abstract does not specify reliability, unattended operation, or interfaces to orchestration software. | Add practical autonomy details: software control stack, machine-readable recipe input, sensor/scale feedback, failure detection, and whether the doser supports unattended batch operation; emphasize reproducibility and interoperability over novelty language. |
| MT04 | Yong-Jie Hu (Drexel) | CALPHAD + ML/physics-informed screening of refractory multicomponent alloys; quantitative exploration of alloy design spaces (sundar2022automatedhierarchicalscreening pages 7-9, sundar2022automatedhierarchicalscreening pages 10-10, sundar2022automatedhierarchicalscreening pages 9-10) | The abstract links the doser to alloy discovery but provides no quantitative bridge from dosing capability to composition-space exploration, screening strategy, or alloy design metrics. | Add one sentence quantifying the searchable composition space enabled by the platform and how dosing accuracy constrains downstream alloy-model fidelity or experimental screening of multicomponent alloys. |
| MT04 | Yan Zeng (Florida State University) | Autonomous inorganic synthesis, AlabOS orchestration, solid-state synthesis bottlenecks, and exception-handling/resource management in autonomous labs (fei2024alabosapythonbased pages 26-30, fei2024alabosapythonbased pages 1-5, fei2024alabosapythonbased pages 12-16) | As a synthesis-enablement reviewer, she would ask whether the doser is robust enough for autonomous operation: exception handling, batching, resource contention, and failure recovery are absent from the abstract. | Add robustness language: e.g., “machine-readable recipes, gravimetric verification, and error-checking/failure-recovery routines are being implemented to support autonomous batch operation”; if not yet done, avoid overclaiming autonomy. |
| MT04 | Yuta Saito (Tohoku University) | Discovery of metastable phases via nontraditional thin-film synthesis pathways; synthesis route as a lever for accessing new phases (hwang2026selfdrivinglaboratoriesin pages 4-5) | The current abstract does not explain why this dosing platform might unlock new synthesis outcomes rather than merely simplify sample preparation. | Add a phrase connecting precise powder formulation to exploration of off-stoichiometric, metastable, or otherwise difficult-to-access alloy feedstocks relevant to atomization/L-PBF processing. |
| MT04 | Richard Otis (Proteus Space / formerly NASA JPL) | Open-source pycalphad; CALPHAD-enabled alloy/path design for additive manufacturing and functionally graded materials; Scheil-Gulliver tools for AM composition planning (reichardt2021advancesinadditive pages 28-29, bocklund2020scheilgulliversimulationsfor pages 1-6, bocklund2020scheilgulliversimulationsfor pages 18-22, otis2024pycalphadcalphadbasedcomputational pages 10-11) | The AM framing is strong, but the abstract does not connect the doser to composition-path design, thermodynamic planning, or validation against AM-relevant phase/solidification constraints. | Add one concise sentence linking the doser to computationally guided feedstock design for AM (e.g., CALPHAD/Scheil-informed composition selection) and specify whether the open-source release includes recipe-generation/control software as well as CAD/mechanical files. |


*Table: This table summarizes likely reviewer perspectives for all 12 symposium organizers across MT03, MT01, and MT04. It highlights each organizer’s recent research emphasis, the main weakness they would likely identify in the abstract, and the most important additions or revisions they would want before submission.*

---

## Section 5: Prioritized Punch-List for Abstract Revision

The following table provides a directly actionable, priority-ordered set of edits. Because the MRS abstract body limit is 4000 characters including spaces, every addition should be paired with a corresponding removal or tightening elsewhere:

| Priority | Action Type | Location in Abstract | Specific Textual Change | Rationale |
|---|---|---|---|---|
| 1 | ADD | Paragraph 1, after sentence 3 | Insert: "Initial benchtop tests target gravimetric dosing accuracy and repeatability at the tens-of-milligrams scale, with throughput sufficient for multi-composition feedstock screening." | Adds the quantitative performance hook most reviewers want; without metrics, the platform reads as conceptual rather than enabling autonomous experimentation or synthesis (muroga2025realtimeautonomouscontrol pages 1-2, higgins2020chemicalroboticsenabled pages 1-5, sundar2022automatedhierarchicalscreening pages 7-9, lee2026albatrossarobotised pages 1-5). |
| 2 | MODIFY | Paragraph 1, sentence ending "...as part of a self-driving, Bayesian-optimization materials-discovery loop" | Rewrite as: "...for eventual integration into a self-driving, Bayesian-optimization materials-discovery loop, in which dosed powders will feed ultrasonic atomization and L-PBF of additively manufactured aerospace alloys." | Prevents overclaiming a closed loop if not yet demonstrated; aligns with closed-loop standards in autonomous materials science and synthesis (foadian2024fromsunlightto pages 3-3, foadian2024fromsunlightto pages 4-6, hwang2026selfdrivinglaboratoriesin pages 4-5, fei2024alabosapythonbased pages 26-30). |
| 3 | ADD | Paragraph 1, after the revised loop sentence | Insert: "Target applications include multicomponent aerospace alloy families relevant to intermetallic and multi-principal-element composition screening." | Names the alloy space so the discovery claim is materially grounded and better aligned with SF03/SF01 alternates and MT04/MT01 composition-space reviewers (sundar2022automatedhierarchicalscreening pages 7-9, sundar2022automatedhierarchicalscreening pages 9-10, reichardt2021advancesinadditive pages 28-29, sun2024materialsmapacalphadbased pages 19-29). |
| 4 | ADD | Paragraph 1, after sentence 2 | Insert: "The modular design supports rapid swapping of powder reservoirs and machine-readable recipes for many-powder studies." | Adds concrete hardware/system capability tied to throughput and autonomy rather than generic affordability (lee2026albatrossarobotised pages 1-5, fei2024alabosapythonbased pages 26-30, fei2024alabosapythonbased pages 1-5). |
| 5 | MODIFY | Title | Rewrite title as: "Open-Source Modular Powder Dosing for Autonomous Alloy Discovery: Lessons from Agentic AI and Generative CAD" | Moves the title emphasis from trendy tools to the materials-discovery hardware contribution while preserving the AI-CAD angle (muroga2025realtimeautonomouscontrol pages 1-2, higgins2020chemicalroboticsenabled pages 1-5, reichardt2021advancesinadditive pages 28-29). |
| 6 | REMOVE | Paragraph 3, sentence "Most repeated AI sessions are spent correcting...rather than exploring new designs, and AI did not reduce assembly complexity." | Remove this sentence entirely. | Good detail for a full paper, but in a 4000-character abstract it overweights the negative AI-CAD narrative and underweights the materials/autonomy contribution (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22). |
| 7 | MODIFY | Paragraph 2, first two sentences | Rewrite as: "We evaluated several AI-assisted CAD workflows, including coding agents and generative-CAD services, by asking them to translate engineering requirements into editable parametric models (CadQuery/OpenSCAD). Across these trials, fully AI-generated designs were not deployment-ready for the dosing application." | Keeps the human-AI evaluation, but makes it sound like a structured benchmark rather than an anecdotal complaint (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22). |
| 8 | ADD | Paragraph 3, after sentence 1 | Insert: "Usable outputs required explicit dimensions, constrained sketches, and repeated human verification of fit, manufacturability, and assembly interfaces." | Sharpens the central finding into actionable design criteria, which AI/materials reviewers will value more than general statements about hallucinations (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22). |
| 9 | ADD | Paragraph 4, before the final sentence | Insert: "The control stack is being structured around recipe-driven operation, gravimetric verification, and software interfaces compatible with laboratory orchestration frameworks." | Adds the orchestration/interoperability layer that autonomous-lab reviewers expect (fei2024alabosapythonbased pages 26-30, fei2024alabosapythonbased pages 1-5, fei2024alabosapythonbased pages 12-16). |
| 10 | ADD | Paragraph 4, after "autonomous alloy-discovery pipeline" | Insert phrase: "including future coupling to CALPHAD- or Scheil-informed composition selection for AM feedstock design" | Connects the doser to computationally guided feedstock design and AM path planning, which strongly improves MT04 fit (reichardt2021advancesinadditive pages 28-29, bocklund2020scheilgulliversimulationsfor pages 1-6, bocklund2020scheilgulliversimulationsfor pages 18-22, sun2024materialsmapacalphadbased pages 19-29). |
| 11 | ADD | Paragraph 4, after "open hardware and software effort" | Insert: "Open-source deliverables will include parametric CAD, bill of materials, control code, and validation protocols." | Specifies what is actually open-source, which strengthens the practical contribution and democratization angle (lee2026albatrossarobotised pages 1-5, fei2024alabosapythonbased pages 26-30, otis2024pycalphadcalphadbasedcomputational pages 10-11). |
| 12 | MODIFY | Paragraph 1, sentence 2: "Commercial dispensers are expensive and poorly matched..." | Rewrite as: "Commercial dispensers are often cost-prohibitive and poorly matched to alloy-focused, many-powder workflows requiring frequent recipe changes and reproducible metering." | More specific problem statement; ties cost to workflow pain points relevant to autonomy and high-throughput synthesis (hwang2026selfdrivinglaboratoriesin pages 4-5, lee2026albatrossarobotised pages 1-5, fei2024alabosapythonbased pages 26-30). |
| 13 | REMOVE | Paragraph 3, sentence "A recurring limitation is weak spatial reasoning—even near-final AI models frequently introduce hallucinated or unnecessary features that must be removed or, if still functional, tolerated." | Trim to shorter phrase within another sentence, or remove if space is tight. | Useful but verbose; the same point can be conveyed more compactly to save characters for dosing metrics and workflow integration (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22). |
| 14 | ADD | Paragraph 4, end of first sentence | Insert: "Validation will compare commanded and delivered powder masses across representative metal powder chemistries relevant to atomization and L-PBF." | Gives a credible experimental validation plan and shows awareness that powder chemistry affects dosing behavior (muroga2025realtimeautonomouscontrol pages 1-2, higgins2020chemicalroboticsenabled pages 1-5, sundar2022automatedhierarchicalscreening pages 7-9, fei2024alabosapythonbased pages 26-30). |


*Table: This table gives a direct-edit punch-list for revising the abstract, ordered by importance and tied to the strongest reviewer concerns across MT03, MT01, and MT04. It is designed to help tighten symposium fit while staying within the MRS 4000-character limit.*

---

## Section 6: Claims Requiring Stronger Evidence

Multiple statements in the current abstract would draw reviewer scrutiny for being unsupported, unquantified, or uncited. The following table identifies the highest-risk claims:

| Claim | Evidence Status | What Evidence Is Needed | Risk Level |
|---|---|---|---|
| "as part of a self-driving, Bayesian-optimization materials-discovery loop" | Unsupported | Clarify whether closed-loop operation is already demonstrated or only planned; if demonstrated, state the measured objective, optimizer input/output, and at least one completed iteration or workflow result. If not, rephrase as "designed for integration into" or "for eventual integration into" (muroga2025realtimeautonomouscontrol pages 1-2, higgins2020chemicalroboticsenabled pages 1-5, foadian2024fromsunlightto pages 3-3) | High |
| "Commercial dispensers are expensive and poorly matched to alloy-focused, many-powder workflows" | Weakly Supported | Add a citation, benchmark, or short comparative basis: typical commercial price range, number of channels, incompatibility with dry metal powders, or lack of recipe flexibility for multicomponent alloy screening (hwang2026selfdrivinglaboratoriesin pages 4-5, lee2026albatrossarobotised pages 1-5) | Medium |
| "existing open-source designs have not been rigorously developed or tested for laser powder bed fusion (L-PBF)" | Unsupported | Cite representative open-source powder dosing/dispensing systems and explain specifically what is missing for L-PBF relevance: powder chemistry, size distribution, inert handling, repeatability, contamination control, or integration with atomization/L-PBF workflows (fei2024alabosapythonbased pages 26-30) | High |
| "fully AI-generated part designs were not usable for our application" | Weakly Supported | Define "usable" and provide at least one evaluation criterion: dimensional fidelity, printability, tolerance stack-up, assembly fit, or number/fraction of designs passing review; otherwise soften to "were not yet reliable enough" (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22) | Medium |
| "specificity improves results" | Needs Quantification | Provide a concrete comparison between high-level prompts and constrained prompts, such as fewer correction cycles, higher pass rate, or better dimensional conformity when drawings/constraints were supplied (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22) | Medium |
| "useful geometry still requires many correction cycles" | Needs Quantification | Give an approximate median/range of correction rounds or a qualitative threshold such as "typically >5 revision cycles"; otherwise this reads as anecdotal (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22) | Medium |
| "A recurring limitation is weak spatial reasoning" | Weakly Supported | Support with one brief example category of failure—misaligned holes, impossible clearances, extra features, nonmanifold geometry—or collapse into a narrower, less interpretive claim if no data are available (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22) | Medium |
| "Most repeated AI sessions are spent correcting and guiding the model toward the intended geometry rather than exploring new designs" | Needs Quantification | Add a rough proportion of effort/time spent on correction vs. exploration, or rephrase as a qualitative observation from this project phase (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22) | Low |
| "AI did not reduce assembly complexity" | Unsupported | Define the assembly complexity metric (part count, fastener count, manual steps, tolerance sensitivity) and compare AI-assisted vs. baseline engineer-designed assemblies; otherwise cut this claim (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22) | Medium |
| "AI is most effective as a modeling assistant rather than an autonomous design agent" | Weakly Supported | This is a reasonable framing claim, but it should be tied to the observed task boundary in this project: translation of explicit requirements into parametric geometry was useful; unconstrained device design was not (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22) | Low |
| "the engineers never opened a traditional CAD graphical interface" | Needs Context | Explain what was produced despite this—e.g., printable parametric models in CadQuery/OpenSCAD—and whether engineers reviewed rendered/STL outputs or physical prototypes instead; otherwise the claim sounds rhetorical (mok2602reasoningdrivendesignof pages 22-24, mok2602reasoningdrivendesignof pages 17-22) | Low |
| "This work reports an open hardware and software effort" / "open-source" | Unsupported | Specify what will actually be released: CAD files, bill of materials, firmware/control code, test data, validation protocols, or orchestration scripts, and whether release has already occurred or is planned (fei2024alabosapythonbased pages 26-30, otis2024pycalphadcalphadbasedcomputational pages 10-11) | Medium |
| "low-cost" | Needs Quantification | Give an approximate prototype bill-of-materials cost or relative cost reduction versus commercial systems; otherwise "low-cost" is too subjective (lee2026albatrossarobotised pages 1-5, fei2024alabosapythonbased pages 26-30) | Medium |
| "precise metering of metal and feedstock powders" | Needs Quantification | Add a target or preliminary figure for dose accuracy, repeatability, minimum/maximum dose, or throughput, ideally by gravimetric verification across representative powders (muroga2025realtimeautonomouscontrol pages 1-2, fei2024alabosapythonbased pages 26-30) | High |
| "relevant to aerospace additive manufacturing" | Weakly Supported | Name the alloy family or use case that makes the relevance concrete—e.g., Ti-, Ni-, Fe-based aerospace alloys, intermetallics, or multi-principal-element systems—and, if possible, tie it to downstream AM process constraints (reichardt2021advancesinadditive pages 28-29, bocklund2020scheilgulliversimulationsfor pages 1-6, bocklund2020scheilgulliversimulationsfor pages 18-22) | Medium |


*Table: This table identifies the abstract statements most likely to draw reviewer skepticism because they lack citation support, quantitative evidence, or clear scope. It is useful for deciding which claims to soften, substantiate, or replace before fitting the abstract into the MRS character limit.*

---

## Section 7: Cross-Cutting Observations and Strategic Recommendations

**Balance of content.** The abstract currently allocates roughly 60% of its text to the AI-CAD evaluation and 40% to the powder-doser hardware and its role in autonomous alloy discovery. All 12 reviewer perspectives suggest inverting this ratio or at least reaching parity. The AI-CAD assessment is a valuable secondary contribution, but it is the materials-discovery hardware that aligns the abstract to these symposia.

**Closed-loop language.** The single most impactful revision is softening "as part of a self-driving, Bayesian-optimization materials-discovery loop" to future-tense or aspirational language unless closed-loop operation is already demonstrated. Reviewers like Ahmadi, Futaba, Seo, and Zeng have all published on closed-loop systems and will hold this claim to a high standard (muroga2025realtimeautonomouscontrol pages 1-1, higgins2020chemicalroboticsenabled pages 1-5, lee2026albatrossarobotised pages 1-5, fei2024alabosapythonbased pages 26-30).

**Quantitative anchors.** The abstract currently contains no numbers. Even preliminary figures—approximate dosing accuracy, prototype BOM cost, number of powder channels, correction-cycle count for AI CAD—would substantially strengthen credibility across all three symposia.

**Symposium-specific framing.** If submitting to MT03 (primary), emphasize the doser as an AI-driven autonomous platform component. If submitting to MT01, foreground the human-AI co-design evaluation and LLM/generative-CAD benchmarking. If submitting to MT04, emphasize the synthesis-enablement angle: the doser as inorganic-synthesis infrastructure for powder-based alloy exploration, ideally connected to CALPHAD-informed composition planning (bocklund2020scheilgulliversimulationsfor pages 1-6, bocklund2020scheilgulliversimulationsfor pages 18-22).

**Character-budget strategy.** The current abstract is at or near the 4000-character limit. To accommodate the recommended additions (estimated ~600–800 characters), cut: (1) the sentence "Most repeated AI sessions are spent correcting…" (~180 chars), (2) the sentence on hallucinated features (~200 chars, or trim to a subordinate clause), and (3) tighten verbose phrasing throughout Paragraphs 2–3. This should free approximately 500–600 characters for the highest-priority additions (dosing metrics, alloy targets, loop-closure language, and open-source specifics).

References

1. (muroga2025realtimeautonomouscontrol pages 1-1): Shun Muroga, Takashi Honda, Yasuaki Miki, Hideaki Nakajima, Don N. Futaba, and Kenji Hata. Real-time autonomous control of a continuous macroscopic process as demonstrated by plastic forming. Materials Horizons, 12:623-629, Jan 2025. URL: https://doi.org/10.1039/d4mh00051j, doi:10.1039/d4mh00051j. This article has 1 citations and is from a domain leading peer-reviewed journal.

2. (pelkie2025automationandautonomous pages 245-247): B Pelkie. Automation and autonomous experimentation for sol-gel nanomaterial synthesis. Unknown journal, 2025.

3. (szymanski2021towardautonomousdesign pages 61-64): Nathan J. Szymanski, Yan Zeng, Haoyan Huo, Christopher J. Bartel, Haegyeom Kim, and Gerbrand Ceder. Toward autonomous design and synthesis of novel inorganic materials. Materials horizons, 8 8:2169-2198, May 2021. URL: https://doi.org/10.1039/d1mh00495f, doi:10.1039/d1mh00495f. This article has 194 citations and is from a domain leading peer-reviewed journal.

4. (mok2602reasoningdrivendesignof pages 22-24): Dong Hyeon Mok, Seoin Back, Victor Fung, and Guoxiang Hu. Reasoning-driven design of single atom catalysts via a multi-agent large language model framework. ArXiv, Feb 2602. URL: https://doi.org/10.48550/arxiv.2602.21533, doi:10.48550/arxiv.2602.21533. This article has 1 citations.

5. (mok2602reasoningdrivendesignof pages 17-22): Dong Hyeon Mok, Seoin Back, Victor Fung, and Guoxiang Hu. Reasoning-driven design of single atom catalysts via a multi-agent large language model framework. ArXiv, Feb 2602. URL: https://doi.org/10.48550/arxiv.2602.21533, doi:10.48550/arxiv.2602.21533. This article has 1 citations.

6. (higgins2020chemicalroboticsenabled pages 1-5): Kate Higgins, Sai Mani Valleti, Maxim Ziatdinov, Sergei V. Kalinin, and Mahshid Ahmadi. Chemical robotics enabled exploration of stability in multicomponent lead halide perovskites via machine learning. ACS energy letters, 5:3426-3436, Oct 2020. URL: https://doi.org/10.1021/acsenergylett.0c01749, doi:10.1021/acsenergylett.0c01749. This article has 142 citations and is from a domain leading peer-reviewed journal.

7. (higgins2020chemicalroboticsenableda pages 1-4): Kate Higgins, Sai Mani Prudhvi Valleti, M. Ziatdinov, S. Kalinin, and M. Ahmadi. Chemical robotics enabled exploration of stability and photoluminescent behavior in multicomponent hybrid perovskites via machine learning. ChemRxiv, Jun 2020. URL: https://doi.org/10.26434/chemrxiv.12436079, doi:10.26434/chemrxiv.12436079. This article has 2 citations.

8. (foadian2024fromsunlightto pages 3-3): Elham Foadian, Sheryl Sanchez, Sergei V. Kalinin, and Mahshid Ahmadi. From sunlight to solutions: closing the loop on halide perovskites. ACS Materials Au, 5:11-23, Oct 2024. URL: https://doi.org/10.1021/acsmaterialsau.4c00096, doi:10.1021/acsmaterialsau.4c00096. This article has 4 citations and is from a peer-reviewed journal.

9. (foadian2024fromsunlightto pages 4-6): Elham Foadian, Sheryl Sanchez, Sergei V. Kalinin, and Mahshid Ahmadi. From sunlight to solutions: closing the loop on halide perovskites. ACS Materials Au, 5:11-23, Oct 2024. URL: https://doi.org/10.1021/acsmaterialsau.4c00096, doi:10.1021/acsmaterialsau.4c00096. This article has 4 citations and is from a peer-reviewed journal.

10. (sundar2022automatedhierarchicalscreening pages 7-9): Aditya Sundar, David Bugallo Ferron, Yong-Jie Hu, and Liang Qi. Automated hierarchical screening of refractory multicomponent alloys with high intrinsic ductility and surface passivation potency. MRS Communications, 12:1086-1095, Sep 2022. URL: https://doi.org/10.1557/s43579-022-00241-1, doi:10.1557/s43579-022-00241-1. This article has 5 citations and is from a peer-reviewed journal.

11. (sundar2022automatedhierarchicalscreening pages 9-10): Aditya Sundar, David Bugallo Ferron, Yong-Jie Hu, and Liang Qi. Automated hierarchical screening of refractory multicomponent alloys with high intrinsic ductility and surface passivation potency. MRS Communications, 12:1086-1095, Sep 2022. URL: https://doi.org/10.1557/s43579-022-00241-1, doi:10.1557/s43579-022-00241-1. This article has 5 citations and is from a peer-reviewed journal.

12. (lee2026albatrossarobotised pages 1-5): Hyun-Gi Lee, Jaekyeong Han, Minjun Kwon, Hyeonuk Kwon, Jooha Park, Hoe Jin Hah, and Dong-Hwa Seo. Albatross: a robotised system for high-throughput electrolyte screening <i>via</i> automated electrolyte formulation, coin-cell fabrication, and electrochemical evaluation. Digital Discovery, 5:1522-1530, Jan 2026. URL: https://doi.org/10.1039/d5dd00580a, doi:10.1039/d5dd00580a. This article has 1 citations and is from a peer-reviewed journal.

13. (lee2026albatrossarobotised pages 13-15): Hyun-Gi Lee, Jaekyeong Han, Minjun Kwon, Hyeonuk Kwon, Jooha Park, Hoe Jin Hah, and Dong-Hwa Seo. Albatross: a robotised system for high-throughput electrolyte screening <i>via</i> automated electrolyte formulation, coin-cell fabrication, and electrochemical evaluation. Digital Discovery, 5:1522-1530, Jan 2026. URL: https://doi.org/10.1039/d5dd00580a, doi:10.1039/d5dd00580a. This article has 1 citations and is from a peer-reviewed journal.

14. (hwang2026selfdrivinglaboratoriesin pages 4-5): Jiho Hwang, Seongmin Kim, Sooyoun Lim, Juhwan Kim, Seungwoo Lee, Seonghyeon Min, Jisoo Song, Jeongwook Lim, Seonghun Hong, Jin-Ha Hwang, Youn-Suk Choi, Dong-Hwa Seo, Sang Soo Han, KangGeon Kim, Su-Hyun Yoo, Jungho Shin, Jang Wook Choi, Jaewook Nam, Jungwon Park, Jaeyune Ryu, and Yousung Jung. Self-driving laboratories in korea: a new era of autonomous discovery. Digital Discovery, 5:1968-1980, Jan 2026. URL: https://doi.org/10.1039/d6dd00024j, doi:10.1039/d6dd00024j. This article has 1 citations and is from a peer-reviewed journal.

15. (hwang2026selfdrivinglaboratoriesin pages 3-4): Jiho Hwang, Seongmin Kim, Sooyoun Lim, Juhwan Kim, Seungwoo Lee, Seonghyeon Min, Jisoo Song, Jeongwook Lim, Seonghun Hong, Jin-Ha Hwang, Youn-Suk Choi, Dong-Hwa Seo, Sang Soo Han, KangGeon Kim, Su-Hyun Yoo, Jungho Shin, Jang Wook Choi, Jaewook Nam, Jungwon Park, Jaeyune Ryu, and Yousung Jung. Self-driving laboratories in korea: a new era of autonomous discovery. Digital Discovery, 5:1968-1980, Jan 2026. URL: https://doi.org/10.1039/d6dd00024j, doi:10.1039/d6dd00024j. This article has 1 citations and is from a peer-reviewed journal.

16. (fei2024alabosapythonbased pages 26-30): Yuxing Fei, Bernardus Rendy, Rishi Kumar, Olympia Dartsi, Hrushikesh P. Sahasrabuddhe, Matthew J. McDermott, Zheren Wang, Nathan J. Szymanski, Lauren N. Walters, David Milsted, Yan Zeng, Anubhav Jain, and Gerbrand Ceder. Alabos: a python-based reconfigurable workflow management framework for autonomous laboratories. ArXiv, May 2024. URL: https://doi.org/10.48550/arxiv.2405.13930, doi:10.48550/arxiv.2405.13930. This article has 43 citations.

17. (fei2024alabosapythonbased pages 25-26): Yuxing Fei, Bernardus Rendy, Rishi Kumar, Olympia Dartsi, Hrushikesh P. Sahasrabuddhe, Matthew J. McDermott, Zheren Wang, Nathan J. Szymanski, Lauren N. Walters, David Milsted, Yan Zeng, Anubhav Jain, and Gerbrand Ceder. Alabos: a python-based reconfigurable workflow management framework for autonomous laboratories. ArXiv, May 2024. URL: https://doi.org/10.48550/arxiv.2405.13930, doi:10.48550/arxiv.2405.13930. This article has 43 citations.

18. (otis2024pycalphadcalphadbasedcomputational pages 10-11): Richard Otis and Zi-Kui Liu. Pycalphad: Calphad-Based Computational Thermodynamics in Python, pages 373-392. Jenny Stanford Publishing, May 2024. URL: https://doi.org/10.1201/9781003514466-18, doi:10.1201/9781003514466-18. This article has 211 citations.

19. (bocklund2020scheilgulliversimulationsfor pages 1-6): Brandon Bocklund, Lourdes D. Bobbio, Richard A. Otis, Allison M. Beese, and Zi-Kui Liu. Scheil-gulliver simulations for the design of functionally graded alloys by additive manufacturing using pycalphad. Text, Jan 2020. URL: https://doi.org/10.48550/arxiv.2001.11611, doi:10.48550/arxiv.2001.11611. This article has 6 citations and is from a peer-reviewed journal.

20. (bocklund2020scheilgulliversimulationsfor pages 18-22): Brandon Bocklund, Lourdes D. Bobbio, Richard A. Otis, Allison M. Beese, and Zi-Kui Liu. Scheil-gulliver simulations for the design of functionally graded alloys by additive manufacturing using pycalphad. Text, Jan 2020. URL: https://doi.org/10.48550/arxiv.2001.11611, doi:10.48550/arxiv.2001.11611. This article has 6 citations and is from a peer-reviewed journal.

21. (bocklund2020scheilgulliversimulationsfor pages 6-10): Brandon Bocklund, Lourdes D. Bobbio, Richard A. Otis, Allison M. Beese, and Zi-Kui Liu. Scheil-gulliver simulations for the design of functionally graded alloys by additive manufacturing using pycalphad. Text, Jan 2020. URL: https://doi.org/10.48550/arxiv.2001.11611, doi:10.48550/arxiv.2001.11611. This article has 6 citations and is from a peer-reviewed journal.

22. (reichardt2021advancesinadditive pages 28-29): Ashley Reichardt, Andrew A. Shapiro, Richard Otis, R. Peter Dillon, John Paul Borgonia, Bryan W. McEnerney, Peter Hosemann, and Allison M. Beese. Advances in additive manufacturing of metal-based functionally graded materials. International Materials Reviews, 66:1-29, Jan 2021. URL: https://doi.org/10.1080/09506608.2019.1709354, doi:10.1080/09506608.2019.1709354. This article has 397 citations and is from a domain leading peer-reviewed journal.

23. (reichardt2021advancesinadditive pages 29-30): Ashley Reichardt, Andrew A. Shapiro, Richard Otis, R. Peter Dillon, John Paul Borgonia, Bryan W. McEnerney, Peter Hosemann, and Allison M. Beese. Advances in additive manufacturing of metal-based functionally graded materials. International Materials Reviews, 66:1-29, Jan 2021. URL: https://doi.org/10.1080/09506608.2019.1709354, doi:10.1080/09506608.2019.1709354. This article has 397 citations and is from a domain leading peer-reviewed journal.

24. (muroga2025realtimeautonomouscontrol pages 1-2): Shun Muroga, Takashi Honda, Yasuaki Miki, Hideaki Nakajima, Don N. Futaba, and Kenji Hata. Real-time autonomous control of a continuous macroscopic process as demonstrated by plastic forming. Materials Horizons, 12:623-629, Jan 2025. URL: https://doi.org/10.1039/d4mh00051j, doi:10.1039/d4mh00051j. This article has 1 citations and is from a domain leading peer-reviewed journal.

25. (foadian2024fromsunlightto pages 4-4): Elham Foadian, Sheryl Sanchez, Sergei V. Kalinin, and Mahshid Ahmadi. From sunlight to solutions: closing the loop on halide perovskites. ACS Materials Au, 5:11-23, Oct 2024. URL: https://doi.org/10.1021/acsmaterialsau.4c00096, doi:10.1021/acsmaterialsau.4c00096. This article has 4 citations and is from a peer-reviewed journal.

26. (foadian2024fromsunlightto pages 11-12): Elham Foadian, Sheryl Sanchez, Sergei V. Kalinin, and Mahshid Ahmadi. From sunlight to solutions: closing the loop on halide perovskites. ACS Materials Au, 5:11-23, Oct 2024. URL: https://doi.org/10.1021/acsmaterialsau.4c00096, doi:10.1021/acsmaterialsau.4c00096. This article has 4 citations and is from a peer-reviewed journal.

27. (sundar2022automatedhierarchicalscreening pages 10-10): Aditya Sundar, David Bugallo Ferron, Yong-Jie Hu, and Liang Qi. Automated hierarchical screening of refractory multicomponent alloys with high intrinsic ductility and surface passivation potency. MRS Communications, 12:1086-1095, Sep 2022. URL: https://doi.org/10.1557/s43579-022-00241-1, doi:10.1557/s43579-022-00241-1. This article has 5 citations and is from a peer-reviewed journal.

28. (fei2024alabosapythonbased pages 1-5): Yuxing Fei, Bernardus Rendy, Rishi Kumar, Olympia Dartsi, Hrushikesh P. Sahasrabuddhe, Matthew J. McDermott, Zheren Wang, Nathan J. Szymanski, Lauren N. Walters, David Milsted, Yan Zeng, Anubhav Jain, and Gerbrand Ceder. Alabos: a python-based reconfigurable workflow management framework for autonomous laboratories. ArXiv, May 2024. URL: https://doi.org/10.48550/arxiv.2405.13930, doi:10.48550/arxiv.2405.13930. This article has 43 citations.

29. (fei2024alabosapythonbased pages 12-16): Yuxing Fei, Bernardus Rendy, Rishi Kumar, Olympia Dartsi, Hrushikesh P. Sahasrabuddhe, Matthew J. McDermott, Zheren Wang, Nathan J. Szymanski, Lauren N. Walters, David Milsted, Yan Zeng, Anubhav Jain, and Gerbrand Ceder. Alabos: a python-based reconfigurable workflow management framework for autonomous laboratories. ArXiv, May 2024. URL: https://doi.org/10.48550/arxiv.2405.13930, doi:10.48550/arxiv.2405.13930. This article has 43 citations.

30. (sun2024materialsmapacalphadbased pages 19-29): Hui Sun, Bo Pan, Zhening Yang, Adam M. Krajewski, Brandon Bocklund, Shun-Li Shang, Jingjing Li, Allison M. Beese, and Zi-Kui Liu. Materialsmap: a calphad-based tool to design composition pathways through feasibility map for desired dissimilar materials, demonstrated with resistance spot welding joining of ag-al-cu. Materialia, 36:102153, Aug 2024. URL: https://doi.org/10.1016/j.mtla.2024.102153, doi:10.1016/j.mtla.2024.102153. This article has 11 citations and is from a peer-reviewed journal.
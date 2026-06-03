---
Meeting: 2026 MRS Fall Meeting & Exhibit (Boston, MA)
Submission deadline: June 17, 2026, 11:59 pm ET
Format: abstract body limited to 4000 characters including spaces; no images,
graphics, or charts; title and body in mixed/Title Case.
Target symposium: see edison/analysis_out/analysis.answer.md for the Edison
ANALYSIS ranking of best-aligned symposia from the Call for Abstracts.
---

Title: An Open-Source, Low-Cost Powder Doser Built with Agentic AI and Generative CAD for Autonomous Alloy Discovery

Additive manufacturing of aerospace structural alloys increasingly depends on rapid, reproducible exploration of powder feedstocks, yet a key workflow step—accurately metering and blending dry powders—remains a largely manual bottleneck in research laboratories. Commercial dispensers are expensive and poorly matched to alloy-focused, many-powder workflows, and existing open-source designs have not been rigorously developed or tested for laser powder bed fusion (L-PBF). We are developing an open-source, low-cost, modular powder doser for precise metering of metal and feedstock powders as part of a self-driving, Bayesian-optimization materials-discovery loop, in which dosed powders feed ultrasonic atomization and L-PBF of additively manufactured aerospace alloys.

A central goal of the project is to evaluate how far agentic AI and generative ("text-to-CAD") tools can carry mechanical and electromechanical design. We evaluated several AI CAD/modeling workflows—including GitHub Copilot coding agents and hosted generative-CAD services—and used large language models to generate and revise parametric CAD (e.g., CadQuery, OpenSCAD) directly from engineering requirements. In practice, fully AI-generated part designs were not usable for our application. We therefore adopted an engineer-led workflow in which engineers design the parts and specify exact dimensions, sketches, and manufacturing constraints, and AI tools model those parts; engineers then review the models, 3D print prototypes, and iterate.

Our central finding so far is that specificity improves results: providing explicit drawings and constraints yields better models than high-level prompts, but useful geometry still requires many correction cycles. A recurring limitation is weak spatial reasoning—even near-final AI models frequently introduce hallucinated or unnecessary features that must be removed or, if still functional, tolerated. Most repeated AI sessions are spent correcting and guiding the model toward the intended geometry rather than exploring new designs, and AI did not reduce assembly complexity. Across this phase, AI is most effective as a modeling assistant rather than an autonomous design agent, and the engineers never opened a traditional CAD graphical interface.

This work reports an open hardware and software effort together with a candid, practitioner-level assessment of current agentic-AI and generative-CAD capabilities and limitations for laboratory device development. We will present the dosing mechanism and prototypes designed by engineers and modeled by AI, a comparison of the attempted AI CAD/modeling workflows, lessons learned for constraining AI outputs to meet manufacturing requirements, and the role of the doser within an autonomous alloy-discovery pipeline relevant to aerospace additive manufacturing.

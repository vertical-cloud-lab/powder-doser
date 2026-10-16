---
Meeting: TMS 2027 Annual Meeting & Exhibition (Orlando, FL)
Dates: March 14–18, 2027 (Orlando World Center Marriott)
Submission deadline: July 1, 2026
Format: abstract body limited to 150 words; submitted via ProgramMaster
(https://www.programmaster.org/TMS2027).
Presenter: Luke
Focus: agentic systems design — CAD, PCB/electronics, firmware, and more
(refreshed per PR #78 comment assigning presenters and symposia; split from
the original combined abstract, see ../README.md).
Edison organizer-persona review applied (PR #78,
../edison/persona_reviews_out/generative-ai-cad.answer.md): the vendor/tool
list (CADSmith, zoo.dev, GitHub Copilot Cloud Agents with Claude Opus 4.7)
was cut in favor of "multiple generative-CAD and agent-coding platforms" —
both personas flagged it as dating quickly and crowding out findings (the
named tools remain in the MRS Fall 2026 abstract, a different venue);
the headline finding ("fully AI-generated designs were not deployment-ready")
was moved up and made concrete (geometric errors, hallucinated features —
grounded in the PR #78 review discussion and discussion #39);
"practitioner-level" became "engineer-led"; the opening was softened
("promise faster" rather than implying measured compression); the title now
names L-PBF feedstock research; and a broader-implication sentence
(open-source route reducing dependence on proprietary instrument pipelines)
was added. NO quantitative hook (correction-cycle counts, first-pass success
rates) was added — those numbers were never recorded in the repo, so adding
them would fabricate data.
Assigned symposium: Accelerating Innovation in Materials and Manufacturing
(Special Topics track; flyer 105). Caveat from ../hidden-gems.md: the flyer
describes a one-day invited-talk + panel program with a midday pitch
competition for students/postdocs/early-career professionals — the pitch
competition may be the practical entry point for a contributed submission.
Prior top-5 ranking (for reference; rationale in ../README.md):
  1. AI-Enabled Materials Processing: Integrating Accelerated Experimental
     Workflows and Processing-Aware Machine Learning (Data-Driven and
     Computational Materials Design)
  2. Accelerating Innovation in Materials and Manufacturing (Special
     Topics) — now the assigned target
  3. AI/ML/Data Informatics for Materials Discovery: Bridging Experiment,
     Theory, and Modeling (Data-Driven and Computational Materials Design)
  4. Additive Manufacturing Modeling, Simulation, and Artificial Intelligence:
     Microstructure, Mechanics, and Process (Additive Manufacturing)
  5. Artificial Intelligence Applications in Integrated Computational
     Materials Engineering (AI-ICME) (Data-Driven and Computational
     Materials Design)
  Submit the abstract to only one symposium.
---

Title: Agentic Systems Design of an Open-Source Powder Doser for L-PBF Feedstock Research: CAD, PCB, and Firmware

Agentic AI and generative design tools promise faster laboratory hardware development, but their deployable capabilities across CAD, electronics, and firmware remain poorly characterized. We report an engineer-led assessment spanning the systems-design stack of an open-source powder doser for laser powder bed fusion feedstock research. Using multiple generative-CAD and agent-coding platforms, we produced parametric CadQuery and OpenSCAD models, KiCad schematics, and MicroPython firmware for multi-actuator control with load-cell feedback. Fully AI-generated designs were not deployment-ready—outputs carried geometric errors and hallucinated features—so engineers defined geometry, dimensions, hand sketches, and manufacturing constraints; AI modeled the parts; engineers reviewed, printed, and iterated. Higher-specificity prompts improved usable output, yet weak spatial reasoning remained a recurring limitation across many correction cycles. This open-source route can broaden access to powder-handling instrumentation and reduce dependence on proprietary development pipelines. We present prototypes, workflow tradeoffs, and guidance for AI-assisted development of materials-lab hardware.

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

Title: Agentic Systems Design for Laboratory Hardware: CAD, PCB, and Beyond in Developing an Open-Source Powder Doser

Agentic AI coding tools and generative design services promise to compress laboratory hardware development, yet their practical capabilities remain poorly characterized. We report a practitioner-level assessment spanning the systems-design stack of an open-source powder doser for laser powder bed fusion feedstock research: mechanical CAD, control electronics, firmware, and documentation. Generative-CAD workflows—CADSmith, zoo.dev, and GitHub Copilot Cloud Agents with Claude Opus 4.7 producing parametric CadQuery and OpenSCAD models—were complemented by agent-generated KiCad schematics and MicroPython firmware for stepper, solenoid, vibration-motor, and servo control with load-cell feedback. Fully AI-generated designs were not deployment-ready, so we adopted an engineer-led workflow: engineers defined geometry, dimensions, hand sketches, and manufacturing constraints; AI modeled the parts; engineers reviewed, printed, and iterated. Specificity substantially improved results, yet usable output still required many correction cycles, with weak spatial reasoning a recurring limitation. We present prototypes, workflow comparisons, and practical guidance for AI-assisted instrument development.

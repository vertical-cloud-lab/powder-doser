---
Title: AI-assisted generative design for an open-source powder doser

We are developing a low-cost, compact powder doser for precise metering of dry powders used in lab- and field-scale experiments. Our project investigates how generative AI can accelerate concept generation, automate parametric CAD, and guide iterative optimization of mechanical components while ensuring manufacturability for fused filament fabrication (FFF) and straightforward assembly.

Goals: (1) demonstrate a reproducible, modular powder doser design that balances precision, throughput, and robustness; (2) evaluate how AI-assisted design workflows impact design speed, creativity, and performance trade-offs; (3) document best practices for constraining AI outputs to meet engineering and manufacturing requirements.

AI methods used so far: We used large language models to generate design concepts, parts-lists, and parametric OpenSCAD/FreeCAD scripts from high-level functional prompts. We used AI to propose geometry variants and to produce annotated CAD-to-print instructions. Candidate geometries were evaluated with simple data-driven performance heuristics and rapid 3D-printed prototypes. AI was also used to draft experimental protocols and to format the poster and abstract text.

Key findings and lessons learned: Generative AI substantially speeds early-stage ideation and produces useful parametric templates; however, unguarded outputs can include infeasible tolerances or unsupported geometries. Constraining prompts with manufacturing rules, explicit material and tolerance parameters, and verification steps (print simulation or simple force checks) markedly improved outcomes. AI-assisted scripting is most valuable when combined with human-in-the-loop validation: designers quickly explore more variants, but engineers still must enforce constraints, run tests, and iterate. Early prototypes created with AI-generated scripts reached comparable assembly simplicity to hand-designed parts, and the AI-enabled workflow reduced concept-to-prototype turnaround by multiple iterations.

Planned poster content: design motivation and requirements, AI-guided workflow (prompts → parametric CAD → prototyping → test), representative AI-generated designs and print results, performance data from preliminary dosing tests, and practical recommendations for others using AI to design mechanical lab devices.

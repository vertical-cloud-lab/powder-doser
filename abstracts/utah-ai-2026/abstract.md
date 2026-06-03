---
Title: AI-assisted generative design for an open-source powder doser

We are developing a low-cost, compact powder doser for precise metering of dry powders used in lab- and field-scale experiments. Our project investigates how generative AI can support engineering work for mechanical components while maintaining manufacturability for fused filament fabrication (FFF) and straightforward assembly.

Goals: (1) demonstrate a reproducible, modular, low-cost powder doser design that balances precision, throughput, and robustness; (2) evaluate how AI-assisted design workflows impact engineering effort and model quality; (3) document best practices for constraining AI outputs to meet engineering and manufacturing requirements.

AI methods used so far: We evaluated multiple AI CAD/modeling workflows and used large language models to generate and revise parametric CAD from engineering requirements. In practice, fully AI-generated part designs were not usable for this project, so we shifted to an engineer-led workflow: engineers designed the parts, then AI tools modeled those parts from specific sketches, dimensions, and constraints. Candidate geometries were evaluated through repeated review cycles and rapid 3D-printed prototypes.

Key findings and lessons learned: Specificity improved results. Providing explicit dimensions, drawings, and manufacturing constraints produced better models than high-level prompts, but useful outputs still required many correction cycles. A recurring limitation was weak spatial reasoning: even near-final AI models often included hallucinated or unnecessary geometric details that had to be fixed or accepted if they were still functional. Across this phase, AI was most effective as a modeling assistant rather than a design agent; prototypes were designed by engineers and modeled by AI, then reviewed and iterated by engineers.

Planned poster content: design motivation and requirements, comparison of attempted AI CAD/modeling workflows, the engineer-led/AI-modeled iteration loop (requirements and drawings → CAD model generation → prototype review), representative modeled parts and print results, and practical recommendations for using AI in mechanical lab-device development.

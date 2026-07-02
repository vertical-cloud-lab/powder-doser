---
Meeting: TMS 2027 Annual Meeting & Exhibition (Orlando, FL)
Dates: March 14–18, 2027 (Orlando World Center Marriott)
Submission deadline: July 1, 2026
Format: abstract body limited to 150 words; submitted via ProgramMaster
(https://www.programmaster.org/TMS2027).
Presenter: Sam
Presentation type: oral presentation
Focus: the multi-reservoir (15+) programmable doser, framed as enabling
instrumentation for AI-enabled, closed-loop processing workflows (refreshed
per PR #78 comment assigning presenters and symposia; split from the original
combined abstract, see ../README.md). Title says "15+" rather than "30+" so
it stays consistent with the proposal-anchored "up to 30 reservoirs" design
target in the body. Per PR #78 feedback (sgbaird), "cross-contamination
characterization" was removed: contamination is prevented by design via
dedicated per-powder augers and an automated auger-swap system, not
characterized.
Assigned symposium: AI-Enabled Materials Processing: Integrating Accelerated
Experimental Workflows and Processing-Aware Machine Learning (Data-Driven and
Computational Materials Design track; flyer 021)
Prior top-5 ranking (for reference; rationale in ../README.md):
  1. Atomization & Powder Metallurgy for Advanced Applications: An MPMD
     Symposium Honoring Iver Anderson (Materials Synthesis and Processing)
  2. Powder Materials Processing and Fundamental Understanding (Materials
     Synthesis and Processing)
  3. AI-Enabled Materials Processing (Data-Driven and Computational Materials
     Design) — now the assigned target
  4. Accelerating Innovation in Materials and Manufacturing (Special Topics)
  5. Additive Manufacturing and Innovative Feedstock Processing for
     Multifunctional Materials (Additive Manufacturing) — see Edison review
     caveats (magnetics-oriented audience)
  Submit the abstract to only one symposium.
---

Title: A Programmable Powder Doser with 15+ Reservoirs and Automated Auger Swapping for AI-Enabled Alloy-Development Workflows

AI-enabled processing workflows are only as fast as their slowest manual step—for alloy development, often feedstock metering and blending. We present an open-source programmable powder doser with a sub-$1,000 bill-of-materials target, far below commercial dispensers, designed as enabling instrumentation for closed-loop, Bayesian-optimization alloy-development campaigns whose dosed powders will feed ultrasonic atomization and laser powder bed fusion (L-PBF). A stepper-driven Archimedean auger with solenoid tapping, vibration-motor agitation, and servo-controlled tilt accommodates powders prone to bridging, clumping, air dispersion, and static charging. Design targets include up to 30 independently addressable reservoirs, 250 mL blends, and ±1 mg per-powder accuracy (±0.1 mg stretch). Cross-contamination between recipes is prevented by design: dedicated per-powder augers exchanged by an automated auger-swap system. A machine-learning calibration layer maps actuator parameters to dispensed mass per powder. We present the dosing mechanism, auger-swap system, calibration approach, and open-source deliverables: parametric CAD, bill of materials, control code, validation protocols.

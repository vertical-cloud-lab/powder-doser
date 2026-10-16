---
Meeting: TMS 2027 Annual Meeting & Exhibition (Orlando, FL)
Dates: March 14–18, 2027 (Orlando World Center Marriott)
Submission deadline: July 1, 2026
Format: abstract body limited to 150 words; submitted via ProgramMaster
(https://www.programmaster.org/TMS2027).
Presenter: Sam
Presentation type: oral presentation
Focus: the multi-reservoir (15+) programmable doser, framed as the
feedstock-preparation node of a closed-loop, AI-enabled processing workflow
(refreshed per PR #78 comment assigning presenters and symposia; split from
the original combined abstract, see ../README.md). Per PR #78 feedback
(sgbaird), "cross-contamination characterization" was removed: contamination
is prevented by design via dedicated per-powder augers and an automated
auger-swap system, not characterized.
Edison organizer-persona review applied (PR #78,
../edison/persona_reviews_out/powder-dosing.answer.md): reframed
workflow-first (feedstock-preparation node of a closed-loop BO pipeline);
reservoir count unified to "15+" in both title and body (resolves the
15+/up-to-30 inconsistency; the proposal's "up to 30" remains the reference
design ceiling); dropped the unsupported ±0.1 mg stretch goal; ML calibration
sentence now states the gravimetric load-cell training signal; actuator and
powder-challenge lists compressed; itemized deliverables collapsed to "full
open-source hardware and software package". The sub-$1,000 BOM target was
KEPT despite the Voisin persona's suggestion to cut it — Sam explicitly
requested the price point (PR #78 comment). No demonstrated metrics were
added: the repo has no measured dosing data yet, so all numbers remain
labeled design targets. Per sgbaird (PR #78), target feedstocks are alloy
precursors (elemental or master-alloy form) dosed under inert atmosphere.
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

AI-enabled processing workflows are only as fast as their slowest manual step—for alloy development, often feedstock metering and blending. We present an open-source programmable powder doser—the feedstock-preparation node of a closed-loop, Bayesian-optimization alloy-development pipeline—with a sub-$1,000 bill-of-materials target, far below commercial dispensers. Optimization-selected recipes are executed automatically, and dosed powders will feed ultrasonic atomization and laser powder bed fusion (L-PBF). A stepper-driven Archimedean auger with multi-mode agitation and tilt control accommodates cohesive, static-prone alloy-precursor powders—elemental or master-alloy form—dosed under inert atmosphere. Design targets include 15+ independently addressable reservoirs, 250 mL blends, and ±1 mg per-powder accuracy. Cross-contamination between recipes is prevented by design: dedicated per-powder augers exchanged by an automated auger-swap system. A machine-learning calibration layer, trained on gravimetric load-cell feedback, maps actuator parameters to dispensed mass per powder. We present the dosing mechanism, auger-swap system, calibration approach, and full open-source hardware and software package.

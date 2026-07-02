# TMS 2027 — abstracts

Submissions to the **TMS 2027 Annual Meeting & Exhibition** (The Minerals,
Metals & Materials Society), March 14–18, 2027, Orlando World Center Marriott,
Orlando, FL. Abstracts are submitted through ProgramMaster
(<https://www.programmaster.org/TMS2027>) with a **150-word** body limit; the
call-for-abstracts deadline is **July 1, 2026**.

## Structure: one combined abstract split into three

The original combined abstract ([`abstract.md`](abstract.md), kept for
reference — it is what the Edison mock review in
[`edison/review_out/review.answer.md`](edison/review_out/review.answer.md)
evaluated) has been split into three targeted abstracts, each ≤150 words and
each anchored to the proposal (PR #27) and to work recorded in this
repository's issues, PRs, and discussions:

1. [`generative-ai-cad/abstract.md`](generative-ai-cad/abstract.md) — agentic
   systems design across the stack: CAD, PCB/electronics, firmware, and the
   engineer-led AI-modeled workflow assessment (146 words; presenter: Luke).
2. [`powder-dosing/abstract.md`](powder-dosing/abstract.md) — the
   multi-reservoir (15+) programmable doser with automated auger swapping
   (dedicated per-powder augers preventing cross-contamination by design):
   auger + tap collar + vibration + tilt, proposal targets
   (up to 30 reservoirs, 250 mL, ±1 mg / ±0.1 mg stretch, sub-$1,000
   bill-of-materials target), powder progression (150 words; presenter: Sam,
   oral).
3. [`calibration-optimization/abstract.md`](calibration-optimization/abstract.md)
   — doser calibration framed as AI-driven, multi-objective, multi-task
   (Bayesian) optimization over the dosing parameters across many powder
   types, with physics-based simulation to infer powder physical properties
   (150 words; presenter: Will).

Symposium rankings below are drawn from the full TMS 2027 symposium list in
[`tms2027_symposium_organizers.csv`](tms2027_symposium_organizers.csv)
(106 symposia with organizers and CFA flyer links, provided in PR #78).

## Full machine-readable symposium catalog

All 106 official CFA flyer PDFs have been downloaded, text-extracted, and
parsed into [`tms2027_symposia.yaml`](tms2027_symposia.yaml): per symposium —
title, track, flyer URL, division/committee sponsors, full scope text, and the
organizing committee with a brief researched background line per organizer.
A scan of every scope for unexpected fits for this project is in
[`hidden-gems.md`](hidden-gems.md) (pitch competition in the Accelerating
Innovation symposium, the MMC symposium as a powder-blending audience, an
organizer bridging the AI-ICME and Powder Materials Processing symposia, and
more).

## Top-5 symposia per abstract

### 1. Generative AI / generative CAD / agentic workflow

| # | Symposium | Track |
|---|-----------|-------|
| 1 | AI-Enabled Materials Processing: Integrating Accelerated Experimental Workflows and Processing-Aware Machine Learning | Data-Driven and Computational Materials Design |
| 2 | Accelerating Innovation in Materials and Manufacturing | Special Topics |
| 3 | AI/ML/Data Informatics for Materials Discovery: Bridging Experiment, Theory, and Modeling | Data-Driven and Computational Materials Design |
| 4 | Additive Manufacturing Modeling, Simulation, and Artificial Intelligence: Microstructure, Mechanics, and Process | Additive Manufacturing |
| 5 | Artificial Intelligence Applications in Integrated Computational Materials Engineering (AI-ICME) | Data-Driven and Computational Materials Design |

Rationale: this abstract is a workflow/AI-tooling contribution. #1 explicitly
welcomes AI-enabled experimental workflows and the instrumentation that
supports them; #2 is the broadest home for "how we build lab capability
faster"; #3–#5 host AI-in-materials audiences but lean toward
discovery/modeling rather than hardware design, so they are alternates.

### 2. L-PBF-oriented powder dosing (hardware)

| # | Symposium | Track |
|---|-----------|-------|
| 1 | Atomization & Powder Metallurgy for Advanced Applications: An MPMD Symposium Honoring Iver Anderson | Materials Synthesis and Processing |
| 2 | Powder Materials Processing and Fundamental Understanding | Materials Synthesis and Processing |
| 3 | AI-Enabled Materials Processing: Integrating Accelerated Experimental Workflows and Processing-Aware Machine Learning | Data-Driven and Computational Materials Design |
| 4 | Accelerating Innovation in Materials and Manufacturing | Special Topics |
| 5 | Additive Manufacturing and Innovative Feedstock Processing for Multifunctional Materials | Additive Manufacturing |

Rationale: #1 is the natural powder-metallurgy/feedstock audience — the doser
literally meters powder toward ultrasonic atomization and L-PBF — and #2 is the
core powder-handling venue. #3 fits the autonomous-workflow-instrument angle.
#5 is kept for completeness but was flagged by the Edison organizer-persona
review as magnetics-oriented (Magnetic Materials Committee); it would require
substantial reframing (see
[`edison/review_out/review.answer.md`](edison/review_out/review.answer.md)).

### 3. Calibration as multi-objective, multi-task optimization

| # | Symposium | Track |
|---|-----------|-------|
| 1 | AI-Enabled Materials Processing: Integrating Accelerated Experimental Workflows and Processing-Aware Machine Learning | Data-Driven and Computational Materials Design |
| 2 | AI/ML/Data Informatics for Materials Discovery: Bridging Experiment, Theory, and Modeling | Data-Driven and Computational Materials Design |
| 3 | Algorithms Development in Materials Science and Engineering | Data-Driven and Computational Materials Design |
| 4 | Artificial Intelligence Applications in Integrated Computational Materials Engineering (AI-ICME) | Data-Driven and Computational Materials Design |
| 5 | Powder Materials Processing and Fundamental Understanding | Materials Synthesis and Processing |

Rationale: this is a processing-aware ML/optimization story — #1 is nearly a
perfect scope match ("processing-aware machine learning"), #2–#4 host the
optimization/informatics methods audience, and #5 would value the powder
flow-behavior insight the calibration data provides.

## Assigned symposia and presenters (current)

Per the PR #78 comment assigning presenters, the three abstracts were
refreshed and assigned as follows (each abstract goes to exactly one
symposium; the assignment is non-overlapping):

| Abstract | Presenter | Symposium | Angle |
|---|---|---|---|
| [`powder-dosing`](powder-dosing/abstract.md) | Sam (oral) | AI-Enabled Materials Processing: Integrating Accelerated Experimental Workflows and Processing-Aware ML (flyer 021) | 30-reservoir programmable doser with automated per-powder auger swapping (cross-contamination prevented by design), as enabling instrumentation for closed-loop workflows |
| [`calibration-optimization`](calibration-optimization/abstract.md) | Will | Powder Materials Processing and Fundamental Understanding (flyer 075) | Calibration optimization and powder properties, plus physics-based simulation (e.g., DEM) to infer physical properties from dosing response |
| [`generative-ai-cad`](generative-ai-cad/abstract.md) | Luke | Accelerating Innovation in Materials and Manufacturing (flyer 105) | Agentic systems design: CAD, PCB/electronics (KiCad, firmware — PRs #25/#45/#61, issue #75/PR #76), and more |

Caveat for the Luke/105 assignment: per [`hidden-gems.md`](hidden-gems.md),
that symposium's technical sessions appear to be invited-talk + panel format
with a midday pitch competition, which may be the practical entry point for a
contributed submission.

The earlier suggested assignment (kept for history): generative-ai-cad →
Accelerating Innovation; powder-dosing → Atomization & Powder Metallurgy;
calibration-optimization → AI-Enabled Materials Processing.

No content was added that is not already grounded in this repository's issues,
PRs, discussions, or proposal (PR #27). The calibration/optimization abstract
uses the same in-development framing ("we are developing…") as the reviewed
MRS abstract's ML-calibration paragraph reinstated by @sgbaird.

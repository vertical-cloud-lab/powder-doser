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

1. [`generative-ai-cad/abstract.md`](generative-ai-cad/abstract.md) — the
   agentic-AI / generative-CAD / engineer-led AI-modeled workflow assessment
   (144 words).
2. [`powder-dosing/abstract.md`](powder-dosing/abstract.md) — the L-PBF-oriented
   powder-dosing hardware: auger + tap collar + vibration + tilt, proposal
   targets (30 reservoirs, 250 mL, ±1 mg / ±0.1 mg stretch,
   cross-contamination characterization), powder progression (140 words).
3. [`calibration-optimization/abstract.md`](calibration-optimization/abstract.md)
   — doser calibration framed as multi-objective, multi-task optimization over
   the dosing parameters across many powder types (148 words).

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

## Suggested assignment (avoiding overlap)

Each abstract goes to exactly one symposium. Since "AI-Enabled Materials
Processing" tops two lists, a non-overlapping assignment that spreads the work
across audiences:

- **generative-ai-cad** → Accelerating Innovation in Materials and
  Manufacturing (or AI-Enabled Materials Processing if preferred)
- **powder-dosing** → Atomization & Powder Metallurgy (Iver Anderson honorary)
- **calibration-optimization** → AI-Enabled Materials Processing

No content was added that is not already grounded in this repository's issues,
PRs, discussions, or proposal (PR #27). The calibration/optimization abstract
uses the same in-development framing ("we are developing…") as the reviewed
MRS abstract's ML-calibration paragraph reinstated by @sgbaird.

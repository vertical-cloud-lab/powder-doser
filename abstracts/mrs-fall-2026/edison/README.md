# Edison Scientific artifacts — MRS Fall 2026 abstract

This folder documents two Edison Scientific runs used to target and pressure-test
the [`../abstract.md`](../abstract.md) submission for the 2026 MRS Fall Meeting.

## 1. Symposium selection (`run_analysis.py` → `analysis_out/`)

An Edison **ANALYSIS** job that uploads (as a single collection, per the Edison
file-management docs):

- the official MRS Fall 2026 *Call for Abstracts* PDF, and
- [`repo_context.md`](repo_context.md) — a dump of this repository's issues and
  pull requests (the `main` branch is sparse; most work lives in issues/PR
  branches),

and asks Edison to rank the symposia whose scope best matches the project.

**Result** (`analysis_out/analysis.answer.md`): top-ranked targets are
**MT03** (primary), **MT01**, and **MT04**, with materials-application
alternates **SF03** (Intermetallics) and **SF01** (High-Entropy Materials).

## 2. Mock peer review (`run_review.py` → `review_out/`)

An Edison **LITERATURE_HIGH** job that reviews the (already MRS-retargeted)
abstract through the personas of the organizers of MT03/MT01/MT04, grounded in
those organizers' recent literature, and returns specific textual additions,
removals, and modifications plus a prioritized punch-list and a "claims needing
evidence" table.

**Result:** `review_out/review.answer.md`.

### Edits applied from the review

The reviewer punch-list (Sections 5–7) was used as input, then narrowed per
PR feedback from @williamulbz to only claims that are grounded in this
repository (notably proposal PR #27):

- Softened the closed-loop claim and sharpened the commercial-dispenser problem
  statement.
- Replaced the abstract's dosing-metric placeholders with the proposal-defined
  hardware targets from #27: up to 30 reservoirs, blends up to ≤250 mL,
  per-powder gravimetric accuracy of ±1 mg with a ±0.1 mg stretch goal,
  cross-contamination tests on five to seven representative L-PBF feedstock
  powders, and an inert-atmosphere enclosure deferred to a later version.
- Named representative L-PBF feedstocks (AlSi10Mg, silicon, stainless steel)
  and the non-hazardous-first test plan.
- Added a hardware-specifics paragraph grounded in repository discussions:
  stepper-driven Archimedean auger (cad/auger, cad/auger-geared), tap collar
  with coin vibration motor and solenoid (PR #51, issue #24), and tilting
  baseplate driven by a hobby servo (issue #65). The actuator trade-study is
  described in terms of options the project has actually considered
  (solenoid vs. vibration motor for flow promotion; servo vs. linear actuator
  for tilt).
- Added the explicit open-source deliverables list (parametric CAD, BOM,
  control code, validation protocols).

Reviewer suggestions **not** applied (and why):

- Machine-learning-based calibration algorithm and a systematic parameter
  sweep: removed per @williamulbz — these have been discussed but not yet
  worked on in this repository, so they should not appear in the abstract.
- Tuning auger throughput by adjusting auger diameter and flight width:
  removed per @williamulbz — this has not been a discussed design path.
- BOM cost, correction-cycle counts, and CALPHAD/Scheil coupling: still
  unsupported by repository evidence; left out.

## Reproducing

```sh
pip install edison-client pdfplumber
export EDISON_API_KEY=...    # provided in the agent sandbox
python run_analysis.py       # writes analysis_out/
python run_review.py         # writes review_out/
```

`*.log` and the large `*.full.json` task dumps are git-ignored.

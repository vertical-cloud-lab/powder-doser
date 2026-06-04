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

Most of the reviewer punch-list (Sections 5–7) has now been applied, using
bracketed placeholders where real numbers/decisions are still pending from the
engineers (so nothing is fabricated):

- Softened the closed-loop claim and sharpened the commercial-dispenser problem
  statement (as before).
- Added a quantitative dosing hook and powder-target sentence with a
  `[±X mg]` placeholder, naming representative L-PBF feedstocks (AlSi10Mg,
  silicon, stainless steel) and the non-hazardous-first test plan.
- Added a hardware-specifics paragraph: stepper-driven Archimedean auger, tap
  collar (coin vibration motor + solenoid), tilting baseplate, the actuator
  trade-study (solenoid vs. servo tilt vs. vibration motor vs. stepper), and the
  motivation to span small/large dispense volumes by adjusting auger diameter
  and flight width (`[X]` mL/revolution placeholder).
- Added a calibration paragraph describing the machine-learning-based
  calibration algorithm and the parameter sweep over auger/tap/vibration/tilt
  settings.
- Trimmed the AI-CAD discussion (per punch-list items 6/13) to rebalance toward
  the materials/hardware contribution, and added the explicit open-source
  deliverables list (parametric CAD, BOM, control code, validation protocols).

Remaining `[…]` placeholders (dose accuracy, mL/revolution) should be replaced
with measured/target values by the engineers before submission. See
`review_out/review.answer.md` Sections 5–7 for the full punch-list.

## Reproducing

```sh
pip install edison-client pdfplumber
export EDISON_API_KEY=...    # provided in the agent sandbox
python run_analysis.py       # writes analysis_out/
python run_review.py         # writes review_out/
```

`*.log` and the large `*.full.json` task dumps are git-ignored.

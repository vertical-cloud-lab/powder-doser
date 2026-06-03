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

Conservative, accuracy-only edits were applied to the abstract:

- Softened the closed-loop claim ("as part of … loop" → "designed for
  integration into … loop"; "feed" → "will feed") to avoid overclaiming a
  demonstrated self-driving loop.
- Sharpened the commercial-dispenser problem statement (cost-prohibitive;
  frequent recipe changes; reproducible metering).

The remaining reviewer suggestions (adding quantitative dosing metrics, BOM
cost, correction-cycle counts, explicit open-source deliverable lists, and the
optional title rewrite) were intentionally **not** auto-applied: they require
real numbers/decisions from the engineers and should not be fabricated. See
`review_out/review.answer.md` Sections 5–7 for the full punch-list.

## Reproducing

```sh
pip install edison-client pdfplumber
export EDISON_API_KEY=...    # provided in the agent sandbox
python run_analysis.py       # writes analysis_out/
python run_review.py         # writes review_out/
```

`*.log` and the large `*.full.json` task dumps are git-ignored.

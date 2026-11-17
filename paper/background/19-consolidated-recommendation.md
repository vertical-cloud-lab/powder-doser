# 19 — Consolidated recommendation: where to submit the powder-doser paper

*Batch 3 — Edison `ANALYSIS` (data-analysis "crow") synthesis. Unlike Batches
1–2 (`LITERATURE_HIGH`/PaperQA), this batch ingested the committed artifacts of
both prior batches as a single zipped collection and produced one reconciled
submission plan. Raw artifacts:
`edison_artifacts/consolidated_recommendation.{answer.md,notebook.ipynb,task.json}`;
runner: `edison_run_consolidated_recommendation.py` (task
`12944119-d7ea-4fed-b111-d6c51b5e7a23`, `status=success`). This note is the
human-readable summary; the crow's full answer and per-claim source citations
are in `consolidated_recommendation.answer.md`.*

This is the **single actionable plan** that reconciles notes **15** (venues),
**16** (editors), **17** (reviewers), and **18** (conferences).

## TL;DR

- **Primary journal → Digital Discovery (RSC).** It ranked #1 under *both* the
  SDL-hardware framing and the generative-CAD framing — the only shortlisted
  venue credible for self-driving labs, open hardware, low-cost automation,
  materials discovery, *and* a code/AI-enabled design story.
- **Request Alán Aspuru-Guzik** (EiC) as handling editor — the only
  firmly *confirmed* role. Mention other Digital Discovery board names only if
  the system asks, each flagged *verify at journal page*.
- **Companions:** **HardwareX** (reproducible build) + **JOSS / SoftwareX**
  (software DOI).
- **Higher-impact alternatives:** **Additive Manufacturing** (if rewritten
  around autonomous AM alloy discovery) or **IJAMT** (if the LLM/code-CAD
  workflow becomes a major contribution).
- **Best near-term conference:** the **Accelerate Conference**.

## Submission sequence

1. **Flagship → Digital Discovery.** Write it as the integrated open-hardware
   SDL paper (low-cost multi-powder doser, closed-loop gravimetric calibration,
   auger auto-change, 50-powder operation, autonomous AM-alloy-discovery use
   case), with the LLM/code-based generative-CAD pipeline as *enabling
   methodology*, not the sole claim. Request **Aspuru-Guzik** as handling editor.
2. **Companion → HardwareX** for exhaustive reproducibility (build files, BOM,
   assembly, validation, calibration protocol, maintenance) — no APC.
3. **Software object → JOSS or SoftwareX** for the control/calibration package
   DOI, if it is reusable beyond this instrument.
4. **Present early at the Accelerate Conference** for the best near-term SDL
   feedback; then **MRS Fall** (materials visibility) and **SFF Symposium**
   (AM-engineering depth). Use **ASME IDETC/CIE** only for a spun-out
   generative-CAD/design-automation manuscript.
5. **Escalation paths:** a stronger AM-discovery result → *Additive
   Manufacturing*; a matured design-method contribution → *IJAMT*, then possibly
   *ASME JMD/JCISE* for a CAD-method spinout.

## Handling editor to request (primary journal)

- **Alán Aspuru-Guzik** — Editor-in-Chief, Digital Discovery, U. Toronto
  *(confirmed)* — best topical match for the AI/materials/SDL framing.
- Mention only if prompted, each *verify at journal page*: Keith A. Brown (BU),
  Sterling G. Baird (AC/UBC), Jason Hein (UBC), Connor W. Coley (MIT).

## Suggested reviewer slate (10, de-duplicated, conflict-screened)

Balanced across all five sub-topics; conflicts with the **Digital Discovery**
editorial/advisory board are **excluded** (see note **17**).

| # | Reviewer | Affiliation | Sub-topic |
|---:|---|---|---|
| 1 | **Milad Abolhasani** | NC State | SDL / automation |
| 2 | **Benji Maruyama** | AFRL | SDL/automation + AM |
| 3 | **Johannes G. Khinast** | TU Graz | powder dosing / metrology |
| 4 | **Wen Chen** | USC (prev. UMass) | AM alloy discovery |
| 5 | **Dan J. Thoma** | UW–Madison | AM alloy discovery (multi-powder DED) |
| 6 | **Wojciech Matusik** | MIT CSAIL | generative CAD |
| 7 | **Richard W. Bowman** | U. Bath | open hardware |
| 8 | **Tobias Wenzel** | U. Bath / EMBL *(affil. unverified)* | open hardware |
| 9 | **Thomas De Beer** | Ghent U. | powder metrology / process analytics |
| 10 | **Adriana Schulz** | U. Washington | generative CAD |

**Alternates (if more names are requested):** Fernando J. Muzzio (Rutgers,
powder flow), Kenneth S. Vecchio (UCSD, high-throughput alloys), Faez Ahmed
(MIT, text-to-CAD), Raymundo Arroyave (Texas A&M, computational alloy/process).

### Conflicts — do **not** suggest as reviewers for a Digital Discovery submission
- **Keith A. Brown** and **Sterling G. Baird** — both in the reviewer pool *and*
  on the Digital Discovery advisory board (Baird is also author-side).
- **Alán Aspuru-Guzik** — requested as editor, not a reviewer.
- **Connor W. Coley** and **Jason Hein** — on the Digital Discovery
  editorial/advisory list; not reviewer suggestions for the primary journal.
- **Joshua M. Pearce** — reserved as the HardwareX editor for the companion
  paper rather than a reviewer here.

## Conference roadmap (condensed; full detail in note 18)

- **Best-fit:** Accelerate Conference *(best near-term)*, MRS Fall, SFF
  Symposium, Faraday Discussions, ORNL SDL workshop *(recurrence unverified)*.
- **Strong:** TMS, ASME IDETC/CIE *(best archival gen-CAD venue)*, AIChE, MRS
  Spring, ASTM ICAM, GOSH, AI4Mat @ NeurIPS/ICLR.
- **Stretch (ML/graphics, methods only):** CVPR workshops, SIGGRAPH/TOG, NeurIPS
  /ICLR main, ICML workshops, GRC Combinatorial & High-Throughput Materials.

## Caveats preserved from the inputs

- Only **Aspuru-Guzik**'s editorial role is *confirmed*; all other board roles
  are *verify at journal page* and rosters rotate.
- Reviewer affiliations/DOIs flagged *unverified* in note **17** (Wenzel,
  Saggiomo affiliations; Ahmed's GenCAD DOI) remain unverified.
- No personal email addresses were fabricated; route editor/reviewer suggestions
  through the journal submission system.

---

*Method note: the Batch-3 crow was instructed to reconcile the batches, produce a
de-duplicated ~8–12-name reviewer slate, flag editorial-board/reviewer conflicts,
preserve `unverified`/`verify at journal page` caveats, and cite the backing
input file(s) per claim — see `consolidated_recommendation.answer.md` for the
per-claim citations and the crow's own decision log.*

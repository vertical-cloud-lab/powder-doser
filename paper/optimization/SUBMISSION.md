# Submission checklist: *Additive Manufacturing*, full-length article

Requirements are from the journal's live guide for authors, read on 2026-11-27 through the lab Pi
(ScienceDirect blocks datacenter IPs), and from Elsevier's machine-learning requirements (2022 PDF linked
from the guide). The guide is paraphrased here, not copied; check it again on the day of submission.
Status: **done** = in the draft now; **open** = someone has to act (owner in brackets).

## Format and limits

| Requirement | Status |
|---|---|
| 5,000–13,000 words for the whole manuscript, including references and figure captions | **done for now**: about 8,500 words of text and captions plus 2,700 in the 80 references, 11,200 in all (counted from the LaTeX source; a `pdftotext` count of the PDF is higher because it also picks up the text inside the vector figures). The planned multi-task, DEM and property results would add 1,500–2,500 words, so moving the DEM model details and the fixed-setting descriptors to the SI is the first cut if needed. Recount in Word or iThenticate before submitting |
| Abstract of at most 250 words, no references, stands alone | **done**: 249 words; one orange placeholder sentence still to replace |
| 1–7 keywords | **done**: 7 |
| 3–5 highlights of at most 85 characters each, as a separate file named with "highlights" | text **done** (5, longest 84 characters); separate file **open** (export at submission) |
| Graphical abstract (encouraged), separate file, TIFF/EPS/PDF | **open**: `figures/graphical_abstract.pdf` exists but still shows the old DEM-centred story; redraw once the scope is fixed |
| ISO/ASTM 52900 terminology in the title and abstract; no unspecific "additive manufacturing" in the title | **done**: "feedstock", "powder bed fusion", "directed energy deposition"; the title does not use "additive manufacturing" |
| Third person preferred | **done** in this pass (the earlier draft used "we") |
| Figures in-line with the text for review | **done** (the `elsarticle` preprint option floats them; check placement in the final build) |
| Figures also as separate files, 300 dpi minimum for halftones (1063 px single column, 2244 px full page) | **done** for PNG at 300 dpi; vector PDFs also in `figures/` |
| Sections numbered 1, 1.1, ...; cross-references by number | **done** |
| Stand-alone paper; no part papers | **done**: the hardware is described in full in Section 2.1, and the boundary with the companion paper is stated |
| Reproducibility: equipment models, software and firmware versions, process parameters, feedstock | mostly **done**; **open**: tube ID and as-printed exit geometry (Will), auger capacity (58 or 70 mL; Will), salt and AlSi10Mg supplier and lot (Will), solenoid supply voltage (Will) |
| No preprint before submission ("strongly discouraged") | nothing posted; keep it that way |
| Clean submission, no reviewer-response highlighting | **done** once the orange placeholders and the convention comments at the top of `main.tex` are removed |

## Declarations and statements

| Requirement | Status |
|---|---|
| Corresponding author with institutional e-mail and full postal address | **open** (Sterling): confirm the address and the e-mail on the title page |
| Author list, order, affiliations | **open** (Sterling and all authors): not agreed; the draft copies the hardware paper's six authors with W. Mulberry first |
| CRediT statement | **open** (all authors) |
| Declaration of competing interests (Elsevier's declaration tool, uploaded as .docx) | text **done**; the .docx is **open** (corresponding author) |
| Funding statement (or the journal's "no specific grant" sentence) | **open** (Sterling) |
| Declaration of generative AI use, Elsevier wording, before the references | **done**; AI used in the research itself is described in Section 2.4 |
| Research data (Option C): deposit in a repository, cite and link it in the article | **open** (Sterling): Zenodo release of `paper/optimization/` and the firmware; the DOI goes into the data availability statement. Do not publish until approved |
| Machine-learning requirements (Elsevier, 9 items) | **done** for the existing models: SI Table S8 maps every item; cross-validation in SI Table S6 and Fig. S1. **open**: the multi-task benchmark (item 9 baselines) |
| Cover letter | draft in [`cover_letter.md`](cover_letter.md); **open**: final claims, reviewer slate checked for conflicts by each author |
| Editor conflict | Associate Editor N. B. Crane is at BYU (same department); the cover letter asks that he not handle the paper |

## Content still owed (see OUTLINE.md, Section 4)

Orange placeholders in `main.tex`: 26 (multi-task results, DEM inference, measured properties, data DOI,
CRediT, funding, hardware facts). Synthetic panels: Fig. 5 (both panels), Fig. 6b–c, Fig. 7c.

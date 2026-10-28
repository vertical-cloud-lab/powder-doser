# ESI (Supplementary Information) checklist (10 Oct 2026)

Checks `paper/si.tex` / [`si.pdf`](../si.pdf) (21 pages) against what *Digital Discovery*
(DD) and the RSC ask of supplementary information for a hardware Full paper. Sources: the DD
author guidelines (saved in `paper/guidelines/`, unchanged on 10 Oct), RSC "Preparing
Supplementary Information", RSC "Data sharing", and the DD hardware editorial (Hein and
Schrier, *Digital Discovery*, 2024, **3**, 447-448). Owners and dates refer to
[`HUMAN-TODOS.md`](HUMAN-TODOS.md) and [`SUBMISSION-PLAN.md`](SUBMISSION-PLAN.md).

✅ met · 🟡 partly met · ❌ not met · ➖ not applicable

## 1. Format and upload

| | Requirement | Source | Status | Action, owner |
|---|---|---|---|---|
| 1.1 | Upload the SI with the original submission; it is peer reviewed | RSC SI | ✅ | Upload `si.pdf` with the manuscript (C7) |
| 1.2 | One document, with S-numbered sections, tables and figures | RSC SI | ✅ | S1-S11, Tables S1-S12, Figs. S1-S8 |
| 1.3 | Title page with the article title and every author | RSC SI | ✅ | Must match `main.tex` if the author list changes (G2) |
| 1.4 | The main text says what the SI contains (the † note) | DD template | ✅ | Updated today to list the new test-protocol section |
| 1.5 | References cited in the SI listed in the main reference list, and the Data availability statement says so | DD guidelines | ✅ | `main.tex` Data availability, last sentence |
| 1.6 | Main text cites SI items by number without hard-coding | house rule (`xr`) | ✅ | `\siref{}` throughout; build `si.tex` before `main.tex` |
| 1.7 | Common, machine-readable formats for data | RSC SI | ✅ | CSVs in the repository, cited from the SI captions |
| 1.8 | Videos, if uploaded as ESI: under 4 min, MP4, 720p or better, 25-30 fps, with a transcript | RSC SI | ➖ | Recordings are linked from YouTube. Optional: upload the #170 assembly animation as a short ESI movie |
| 1.9 | Upload limit: up to 20 files in one ZIP, or 5 at a time | DD guidelines | 🟡 | Main text needs about 17 files plus `si.aux`; build the ZIP and strip `TODO` comments (C7) |

## 2. Hardware-paper content (DD guidelines and the hardware editorial)

| | Requirement | Where | Status | Action, owner |
|---|---|---|---|---|
| 2.1 | Comprehensive bill of materials | S1, Table S1 | 🟡 | Add part numbers, the M2.5/M3/M5 fasteners, cables, the PCB or its breadboard alternative (C2) |
| 2.2 | Construction guide a graduate student can follow | S2, Table S2, Figs. S1-S2 | 🟡 | Add a wiring diagram or pin table (L1), MicroPython flashing steps and per-part print settings (C2) |
| 2.3 | Design files in editable formats, in a public, persistent repository | Data availability; Table S2 | 🟡 | Merge #74 and #170 (G7), make the Onshape document public (G8), PCB board files on `main` (L1) |
| 2.4 | A clear licence, preferably an open-hardware one such as CERN-OHL | repository | ❌ | Choose and add licence files (G4) |
| 2.5 | Minimal "hello world" first experiment | S2 | ❌ | Decide (G15); if yes, Sam runs it (S9) and Claude writes it up (C5) |
| 2.6 | Comparison with existing alternatives: capabilities, cost, adaptability, build time | main text, cost paragraph | 🟡 | Decide (G15); if yes, an SI table with sourced prices (C5) |
| 2.7 | Operating and safety instructions | main text, Safety | 🟡 | Hazards are stated; add the precautions used (S5) |
| 2.8 | Accuracy of the primary measurement | main text, Experimental | 🟡 | Balance repeatability, linearity and calibration (S6) |
| 2.9 | Sources of materials where they matter | Table 1 | 🟡 | Supplier, grade and particle size for each powder (S7) |
| 2.10 | Test protocols, in enough detail to repeat | main Table 3; **S9, Table S10** | ✅ | Folded in from PR #150 today: raw settings and run and record counts for protocols A-H in both rounds, generated from the committed CSVs. Close #150 (G20) |
| 2.11 | Every measurement traceable to its run | S7, S10, Tables S7, S8, S11 | ✅ | None |
| 2.12 | Application to accelerated discovery shown | main text, Conclusions | 🟡 | Numbers for the atomizer charges (W1) |

## 3. AI and LLM use

| | Requirement | Where | Status | Action, owner |
|---|---|---|---|---|
| 3.1 | Log files of LLM inputs and outputs, with model names and dates | S11, Table S12, Fig. S8; draft release | 🟡 | April to early-July Actions logs expired; later logs are in the draft release. Decide when to publish it (item 9) |
| 3.2 | AI-modelled geometry labelled as such | Figs. 2, S3; Table S3 | ✅ | None |
| 3.3 | AI tools used for figures: licensed training data, commercial reuse allowed | cover letter | ❌ | Confirm or state not applicable (G18) |
| 3.4 | No AI-edited photographs | Figs. 1b, 6a | 🟡 | Confirm (G18); if the Fig. 1b logo is blurred, use a plain blur (G14) |

## 4. For the data reviewer

DD sends code and data to a separate data reviewer who checks that they run and reproduce the
results.

| | Requirement | Status | Action, owner |
|---|---|---|---|
| 4.1 | One command per artefact rebuilds it | ✅ | `make_data_figures.py`, and one generator per SI table in `paper/figures/data/` |
| 4.2 | Pinned environment | ❌ | `requirements.txt` with versions (C4) |
| 4.3 | Column descriptions for the CSVs | ❌ | Data dictionary (C4) |
| 4.4 | How to cite the code and data | ❌ | `CITATION.cff`, `.zenodo.json`, README section (C4); Zenodo DOI (G13) |
| 4.5 | STL files free of mesh errors | 🟡 | Check the released STLs once #170 is merged (C4) |

## 5. What the SI contains now

| Section | Content | Tables and figures |
|---|---|---|
| S1 Bill of materials | Purchased parts and prices | Table S1 |
| S2 Construction guide | Printed parts with Fusion 360 links; 19 assembly steps | Table S2; Figs. S1, S2 |
| S3 Auger and outlet geometry | Outlet variants; tested vs AI-modelled auger | Fig. S3; Table S3 |
| S4 AI-assisted CAD workflow | Workflow page; design-log summary | Fig. S4; Table S4 |
| S5 Bench noise | Noise at rest and after actuation | Figs. S5, S6; Table S5 |
| S6 Human tasks | Every task a person did in the campaign | Table S6 |
| S7 Closed-loop dose record | Every dose attempt; example traces | Tables S7, S8; Fig. S7 |
| S8 Composition error | Dosing error to composition error | Table S9 |
| **S9 Test protocols as recorded** | **New today, from PR #150** | **Table S10** |
| S10 Run inventory | Every run in both rounds | Table S11 |
| S11 AI usage log | Tools, models and dates; requests per week | Table S12; Fig. S8 |

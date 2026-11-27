# Which paper to write: three routes (for Sterling's scope decision)

The first blocker is a decision, not an experiment. Both mock reviews (13 Oct and 27 Nov) said the present
data do not yet make an *Additive Manufacturing* full-length research article. The 27 Nov review added that
the journal's new **Methods paper** type fits the present calibration-and-drift story better. This note sets
the three routes side by side. The experiment codes (E0–E9) are those of [`OUTLINE.md`](OUTLINE.md) §4A.

| | A. Focused research article (recommended) | B. Methods paper | C. Full scope (TMS abstract) |
|---|---|---|---|
| Claim | Per-powder BO calibration works on AM feedstock and the dose records tell feedstock batches apart | A transferable, uncertainty-aware procedure for calibrating a powder doser, with its pitfalls (drift, empty tube, best-dose-by-chance) | A plus multi-task calibration across powders and DEM inference of cohesion and friction |
| Journal type | Full-length research article (5,000–13,000 words) | Methods paper: tutorial style, judged on clarity, rigour, reproducibility and breadth of use to AM | Full-length research article |
| New experiments | E0–E3, E5–E6; sieved and unsieved Al 4047 paired and replicated; one repeat-fill or repeat-day anchor; one AM-facing outcome (small E9, or charge composition accuracy) | E0–E2 at least: the AM powder is needed for "breadth of use to AM". The salt session and the AlSi10Mg session, each with a matched baseline and validation | A plus E4 (prospective multi-task), E7 (shear cell) and E8 (DEM design, emulator, inference) |
| Rig time | about 220 doses, 3 rig days | about 160 doses, 2 rig days | about 260 doses, 4 rig days, plus compute |
| Outside dependencies | funnel set, T/RH sensor, calibration weight, SEM time | sensor and weight | as A, plus a shear-cell lab |
| What changes in the draft | Title and abstract drop "multi-task" and DEM inference (kept as outlook); Figs. 5 and 6b–c leave the main text | Restructure as a tutorial: workflow figure, decision points, failure handling, a worked example per powder; Fig. 7 and the DEM move to the SI or out | Fill the placeholders |
| Realistic submission | about 26 Feb 2027 | about 12 Feb 2027 | about 16 Apr 2027 |
| Main risk | The doser may not separate the two Al 4047 batches beyond its own scatter. If so, report it and fall back to B | Editors may see salt plus one alloy as too narrow for AM; the companion paper's overlap must stay small | Timeline and identifiability of DEM inference on fine metal powders; the shear-cell turnaround |

Notes:

- The TMS 2027 talk (14–18 Mar) can show more than any of these papers claims. The talk does not
  constrain the paper's scope.
- Either A or B can be submitted before TMS. C cannot.
- In every route, the cover letter must disclose the companion hardware paper. The hardware paper plans to
  submit on 18 Dec 2026, and its §2.7 reports the same atomizer charges. The letter should also list the
  shared records (SI Table S10).

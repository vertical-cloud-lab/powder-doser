The figure/caption do **not yet make the HUMAN vs AI split unambiguous**.

What is already clear:
- The figure itself is clearly marked as non-experimental: `fig3_dispense.pdf` carries a visible diagonal **“SYNTHETIC DATA”** watermark on all three panels, and `make_figures.py` hard-codes this via `synthetic_watermark(ax, text: str = "SYNTHETIC DATA")` and generates panel values from `np.linspace`, `np.logspace`, and `RNG.normal(...)` inside `def fig3()` rather than reading a data file. That is direct evidence that the plotted data are placeholders, not measurements (`make_figures.py`, `def fig3()`, `def synthetic_watermark()`).
- The current caption also says this explicitly: `caption_fig3_dispense.md` opens with **“Dispensing characterization (SYNTHETIC placeholder data, to be replaced by bench measurements; watermarks will be removed when real data are substituted)”**.
- The manuscript does contain the needed division-of-labour language, but it lives elsewhere, not in this caption. In `main.pdf` page 2: **“the human team made the design decisions, supplied specifications and drawings, reviewed every output, and printed and tested the parts, while the AI tools did the modelling”**. On page 4: **“the human team provided annotated engineering drawings, several of them fully dimensioned with geometric relations… [and] the AI's role had narrowed to modelling the parts”**. On page 8: **“GitHub Copilot coding agent (Claude-family models) generated CAD code, firmware, and figure scripts under human review”**.

Why this figure/caption is still weak on signposting:
- The current caption says nothing about **who** did what. It identifies the data as synthetic, but a reader would not learn that the **design decisions, annotated/dimensioned drawings, review, printing, and testing were HUMAN**, while **parametric CAD modelling was AI-assisted**.
- That omission conflicts with the review instruction in `pr97_comments.md`: **“Throughout this section, clarify where ai was used. We should be signposting the design contributions of ai versus engineers throughout the manuscript--it should always be clear who did what.”**
- Another PR comment sharpens the required wording: **“some of them had dimensions and relations… eventually, ai was only being used to model the parts, not to make design decisions beyond calculating relevant dimensions and tolerancing”** (`pr97_comments.md`).
- For this specific figure, there is another subtle risk: because it is a performance/characterization figure rather than a CAD-render figure, readers may wrongly infer that AI helped generate or interpret the *experimental* results. The supplied files do **not** support that claim. What they support is narrower: the plotted placeholder data and figure script were AI-generated under human review (`main.pdf`, p. 8), while real bench measurements are still pending (`caption_fig3_dispense.md`; `make_figures.py` header; `main.pdf`, p. 6).

A file-grounded reading of the figure:
- `fig3_dispense.pdf`, panel (a): cumulative dispensed mass vs time for four powders.
- `fig3_dispense.pdf`, panel (b): requested vs measured mass with a ±10% shaded band.
- `fig3_dispense.pdf`, panel (c): dose CV vs auger speed.
- `make_figures.py` confirms these are synthetic placeholders:
  - panel (a) uses synthetic rates from `POWDERS = [("Glass beads...", ..., 1.6), ...]` and noisy time traces;
  - panel (b) uses `req = np.logspace(...)` and simulated `meas = req * (1 + RNG.normal(...)) + RNG.normal(...)`;
  - panel (c) uses simulated `cv = 0.6 + 0.035 * rpm + RNG.normal(...)`.
- No bench dataset is bundled here. The branch tree points to relevant likely code for future real measurements under `origin/copilot/integrate-scale-feedback-loop`, especially:
  - `hardware/test-module/firmware/dosing.py`
  - `hardware/test-module/firmware/scale.py`
  - `hardware/test-module/firmware/sim/sim_rig.py`
  - `hardware/test-module/analysis/rs232_analysis.py`
  But the tree search found **no** accompanying measurement files such as CSV/Parquet/NPZ for dispensing characterization.

One important bundle inconsistency to flag:
- The bundle README says this is **“Figure 3 (dispensing characterization, SYNTHETIC)”** and the file is named `fig3_dispense.pdf`, but `main.pdf` identifies the dispensing characterization figure as **Fig. 4**, while **Fig. 3** in the manuscript is the AI-CAD outcomes figure. I can still judge the supplied figure/caption, but this numbering mismatch should be cleaned up before revision.

## Recommended caption rewrite

**Dispensing characterization using synthetic placeholder data only; no experimental measurements are shown.** The plotted values in all panels are simulated placeholders generated for figure layout and analysis planning and are watermarked **SYNTHETIC DATA**; they will be replaced with bench measurements in revision. The underlying doser hardware, test plan, acceptance criteria, and all design decisions were set by the **human team**, which also supplied the design specifications/drawings, reviewed outputs, and is responsible for fabrication and bench testing. The doser geometry itself was produced by **AI-assisted parametric CAD modelling under human review**; AI did not determine the final engineering design. (a) Cumulative dispensed mass versus time for four representative powders at fixed auger speed. (b) Requested versus measured dose for planned closed-loop gravimetric control; shaded band indicates ±10%. (c) Planned dose repeatability summary, reported as coefficient of variation versus auger speed, motivating a coarse-then-trickle dosing strategy.

Why this rewrite is safer:
- It makes the **HUMAN** role explicit: design decisions, specs/drawings, review, fabrication, testing.
- It makes the **AI** role explicit but narrow: parametric CAD modelling under human review.
- It does **not** overclaim that AI produced the real characterization data, because no such data exist in the bundle.
- It stays consistent with `pr97_comments.md` and with the explicit labour split in `main.pdf`.

## Prioritized action list for this figure
- **1. Add explicit HUMAN vs AI language to the caption**, using wording close to the rewrite above.
- **2. Fix the figure-number mismatch** between the bundle naming (`fig3_dispense`) and the manuscript text (`Fig. 4` in `main.pdf`).
- **3. Keep the synthetic disclaimer prominent** in both caption and graphic until real measurements replace the placeholder traces.
- **4. Avoid implying AI generated or interpreted experimental results** unless a later revision can support that with actual files and text.
- **5. When real data arrive, source them from the test-module workflow** suggested by the branch tree (`hardware/test-module/...`) and replace the synthetic curves entirely.

- Used the supplied bundle files as the sole evidence base: `caption_fig3_dispense.md`, `fig3_dispense.pdf`, `make_figures.py`, `pr97_comments.md`, `main.pdf`, and `all_branches_file_tree.txt`.
- Treated the manuscript PDF as authoritative for quoted wording and figure numbering, while still analyzing the user-supplied figure file under review despite the numbering mismatch.
- Used branch-tree paths only to identify likely relevant repository files; did not infer contents for files not included in the bundle.
- Limited attribution to HUMAN vs AI, per instructions, and avoided naming individuals.
- Did not claim the existence of real dispensing measurements because no measurement dataset was present in the supplied files.
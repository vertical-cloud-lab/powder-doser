The revised `fig3_dispense` fixes some context around the synthetic status, but several round-1 consistency problems remain. Below I separate resolved vs unresolved items, then list remaining concrete fixes that do not require new bench data.

1) Previously flagged issues that are now resolved

- The figure is now explicitly marked as synthetic in both the graphic and caption.
  - In `fig3_dispense.pdf`, all three panels carry the diagonal watermark `SYNTHETIC DATA` and the extracted PDF text shows it in panels `(a)`, `(b)`, and `(c)`.
  - `caption_fig3_dispense.md` opens with: `Dispensing characterization (SYNTHETIC placeholder data, to be replaced by bench measurements; watermarks will be removed when real data are substituted).`
  - `make_figures.py` enforces this consistently by calling `synthetic_watermark(ax)` in each panel of `fig3()` at lines 358, 376, and 388, with the helper defined at lines 66–81.
- The manuscript body now states more clearly that the plotted data are placeholders illustrating the intended analysis rather than real performance claims.
  - `main.pdf`, §2.4: `The data shown are synthetic placeholders (watermarked in the figure) illustrating the analysis and presentation that the bench campaign now under way will populate...`
  - That is better aligned with the caption than an unqualified performance-style description.
- The manuscript body now includes the planned replicate count and operating context, even though the figure/caption still do not.
  - `main.pdf`, §3.4: `Doses are dispensed onto a tared collection cup on the analytical balance (A&D HR-100A, 0.1 mg readability), with n ≥10 replicates per condition.`
  - Also in §3.4: `closed-loop accuracy is evaluated across 20 mg–5 g requested masses with coarse-then-trickle control.`
  - This resolves part of the earlier concern at the manuscript level, though not yet at the figure-caption level.
- The requested-mass sample points in panel (b) now match the manuscript’s stated 20 mg–5 g campaign range.
  - `make_figures.py` line 362 defines `req = np.logspace(np.log10(0.02), np.log10(5), 14)`, i.e. 0.02 g to 5 g.
  - `main.pdf`, §2.4 and §3.4 both state `20 mg–5 g`.

2) Previously flagged issues that are not yet resolved

- Figure numbering is still inconsistent across the bundle vs the compiled manuscript.
  - `caption_fig3_dispense.md` header says `Figure 3`.
  - `README.md` says `Location in manuscript: main.tex, Figure 3 (dispensing characterization, SYNTHETIC)`.
  - `make_figures.py` labels this block `# Figure 3 — dispensing characterization (synthetic placeholder data)` at lines 331–332.
  - But `main.pdf` clearly renders this as `Fig. 4 Dispensing characterization ...`.
  - So the round-1 numbering mismatch is not fixed.
- Panel (b) still does not match the manuscript’s actual acceptance-target logic.
  - `caption_fig3_dispense.md` says: `shaded band is ±10%.`
  - `make_figures.py` implements exactly one constant ±10% band via `ax.fill_between(lims, [l * 0.9 for l in lims], [l * 1.1 for l in lims], ...)` at lines 370–372.
  - But `main.pdf`, §2.4 states: `Acceptance targets ... are ±5% accuracy above 100 mg and ±10% at 20 mg`.
  - So the figure still shows a single ±10% envelope where the manuscript text describes a two-regime target.
- Panel (a) caption still does not say that the panel is intended as a mass-flow calibration view.
  - `caption_fig3_dispense.md`: `Cumulative dispensed mass versus time per powder at fixed auger speed.`
  - `main.pdf`, §2.4 is more specific: panel `(a)` is `establishing per-powder mass-flow calibrations`.
  - The earlier suggestion to add explicit calibration language to the figure caption has not been implemented.
- The figure/caption still do not say that final experimental panels will summarize replicate measurements with uncertainty.
  - `main.pdf`, §3.4 supplies `n ≥10 replicates per condition`, but `caption_fig3_dispense.md` says nothing about replicates or uncertainty.
  - Panel `(b)` in `fig3_dispense.pdf` shows parity points without error bars or replicate aggregation language.
- The optional axis-tightening issue in panel (b) is still present.
  - Data points are generated from 0.02–5 g (`make_figures.py`, line 362), but the parity-line/band limits are `lims = [0.01, 8]` (line 368), so the drawn axes and shaded region extend beyond the stated campaign range.
  - This is not a fatal error, but the round-1 suggestion to tighten to the actual range was not adopted.

3) Remaining concrete inconsistencies or unsupported claims fixable without new bench measurements

- Caption/body mismatch on accuracy targets in panel (b).
  - This is the clearest remaining concrete inconsistency.
  - Evidence:
    - `caption_fig3_dispense.md`: `shaded band is ±10%.`
    - `make_figures.py` lines 370–372: only ±10% is drawn.
    - `main.pdf`, §2.4: `±5% accuracy above 100 mg and ±10% at 20 mg`.
  - Fix without new data: redraw the acceptance overlay to match the manuscript’s two-threshold rule, or explicitly relabel the band as a placeholder tolerance envelope rather than the true acceptance criterion.
- Bundle metadata/source comments still identify this as Figure 3 while the manuscript shows Figure 4.
  - Evidence:
    - `README.md`, `caption_fig3_dispense.md`, and `make_figures.py` all still call it Figure 3.
    - `main.pdf` shows `Fig. 4`.
  - Fix without new data: update bundle metadata and source comments to match the compiled manuscript, or renumber the manuscript consistently.
- Caption is still a little too empirical for a placeholder figure because it does not explicitly say the panels illustrate the planned analysis/protocol.
  - `main.pdf`, §2.4 already has the safer wording: `illustrating the analysis and presentation that the bench campaign ... will populate`.
  - `caption_fig3_dispense.md` still reads like a straight results caption after the parenthetical disclaimer.
  - Fix without new data: rewrite the panel descriptions to say `illustrative placeholder traces/points for the planned analysis` or similar.
- Panel (a) caption under-describes the panel’s intended function relative to the manuscript body.
  - Evidence:
    - Caption: only `Cumulative dispensed mass versus time per powder at fixed auger speed.`
    - Body: `establishing per-powder mass-flow calibrations` (`main.pdf`, §2.4).
  - Fix without new data: add `illustrating per-powder mass-flow calibration` to panel (a) wording.
- Figure/caption still omit replicate/uncertainty signposting even though the manuscript protocol already specifies it.
  - Evidence:
    - `main.pdf`, §3.4: `n ≥10 replicates per condition`.
    - `caption_fig3_dispense.md`: no replicate or uncertainty wording.
  - Fix without new data: add one sentence to the caption such as `Final experimental versions will report replicate measurements (n ≥ 10 per condition) with uncertainty.`
- Panel (b) plot limits extend beyond the stated operating range.
  - Evidence:
    - Requested masses are 0.02–5 g in `make_figures.py` line 362.
    - Shaded band/identity line use `lims = [0.01, 8]` at line 368.
  - Fix without new data: set the displayed limits to the actual placeholder campaign range.
- AI-vs-human signposting is still absent for this figure package.
  - This is weaker than the panel-(b) acceptance mismatch, but still implementable and supported by the supplied review record.
  - Evidence:
    - `pr97_comments.md`, thread at `paper/main.tex line 189`: `Throughout this section, clarify where ai was used. We should be signposting the design contributions of ai versus engineers throughout the manuscript--it should always be clear who did what.`
    - `caption_fig3_dispense.md` contains no HUMAN/AI attribution.
  - For this specific figure, the safest supported wording is limited: the placeholder plot is script-generated from `make_figures.py`; it is not bench data. Avoid implying AI generated or analyzed experiments. If you add attribution, keep it to something like: placeholder visualization generated from code; real measurements will be HUMAN-conducted bench data. Do not overstate beyond the supplied files.

What does not appear to be a remaining issue for this figure

- Hopper / load-cell / sensor wording is not a current inconsistency in this figure.
  - `pr97_comments.md` and the resource notes correct the platform wording globally: `A&D HR-100A analytical balance ... NOT an HX711 load cell` and `No hopper in the end design; the auger tube itself is the reservoir, loaded via slots.`
  - But `fig3_dispense.pdf`, `caption_fig3_dispense.md`, and `make_figures.py::fig3()` do not depict or mention a hopper, HX711, or load cell at all.
  - `main.pdf`, §3.4 already says `analytical balance (A&D HR-100A, 0.1 mg readability)`.
  - So I do not see a remaining fig3-specific hopper/load-cell wording mismatch.
- CAD-render/provenance issues are not central here because `README.md` explicitly says this figure consumes `CAD-render assets consumed: (none; synthetic plot)`.
  - If future data/protocol provenance is needed, likely relevant branch-tree paths are under `origin/copilot/integrate-scale-feedback-loop`, especially `hardware/test-module/firmware/dosing.py`, `hardware/test-module/firmware/scale.py`, `hardware/test-module/firmware/sim/sim_rig.py`, and `hardware/test-module/analysis/rs232_analysis.py`, all named in `all_branches_file_tree.txt`.

Prioritized action list: only implementable non-bench-data fixes

1. Fix the numbering mismatch everywhere in the bundle: `caption_fig3_dispense.md`, `README.md`, and the `# Figure 3` comment block in `make_figures.py` should match `main.pdf`’s `Fig. 4`.
2. Redraw panel (b)’s acceptance overlay to match the manuscript’s stated targets (`±10%` at 20 mg, `±5%` above 100 mg), or explicitly label the current ±10% band as a placeholder-only envelope.
3. Rewrite the caption so it says the panels illustrate the planned analysis/protocol rather than measured performance.
4. Add panel-(a) wording tying the cumulative-mass traces to `per-powder mass-flow calibration`, matching `main.pdf` §2.4.
5. Add one caption sentence stating that final experimental panels will report replicate measurements (`n ≥ 10` per condition) with uncertainty.
6. Tighten panel (b) display limits to the actual placeholder range used in code (`20 mg–5 g`).
7. Optionally add a brief HUMAN-vs-AI/provenance note for this placeholder figure, but keep it minimal and fully supported by the supplied files.

- Discretionary analytical decisions made during the analysis
- Treated the compiled `main.pdf` as the authoritative source for current manuscript figure numbering and figure/body wording when it conflicted with bundle-local metadata.
- Counted an issue as unresolved when the contradiction remained anywhere across `fig3_dispense.pdf`, `caption_fig3_dispense.md`, `make_figures.py`, and `main.pdf`, even if part of the manuscript had been improved elsewhere.
- Treated panel-(b)’s constant ±10% band as a concrete inconsistency, not just a stylistic issue, because `main.pdf` specifies a different two-threshold acceptance rule.
- Did not re-litigate the known fact that the dispensing plots are synthetic placeholders, per the user’s instruction.
- Named branch-tree files only as potentially relevant provenance or future data-source paths when those files were listed in `all_branches_file_tree.txt`; I did not infer their contents beyond the file names.
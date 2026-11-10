Resolved from round 1

- The manuscript now clearly flags the figure as placeholder-only rather than measured performance evidence. In `main.pdf`, §2.4 says: “The data shown are synthetic placeholders (watermarked in the figure) illustrating the analysis and presentation that the bench campaign now under way will populate…”. That fixes the earlier problem that the text/caption read too empirically for synthetic data. The figure itself still shows a diagonal `SYNTHETIC DATA` watermark in all three panels of `fig3_dispense.pdf`, and `make_figures.py` applies that watermark to each axis via `synthetic_watermark(ax)` inside `fig3()`.

- The body text now adds the missing purpose statement for panel (a). In `main.pdf` §2.4, panel (a) is described as “cumulative dispensed mass versus time at fixed auger speed, establishing per-powder mass-flow calibrations”. That resolves the round-1 request to connect panel (a) to calibration purpose. The caption file `caption_fig3_dispense.md` still omits the calibration phrase, but the manuscript body now has it.

- The manuscript now states replicate counts and controller logic in the protocol section. In `main.pdf` §3.4: “Doses are dispensed … with n ≥10 replicates per condition.” The same section also specifies the intended control logic: “coarse mode … until 90% of the target mass is reached, then switches to trickle mode … tap/vibration bursts … quiet windows ≥0.5 s…”. This resolves the earlier complaint that those conditions were undocumented, at least in the manuscript text.

- The manuscript now states the intended acceptance targets explicitly. In `main.pdf` §2.4: “Acceptance targets … are ±5% accuracy above 100 mg and ±10% at 20 mg, with per-dose times under 30 s.” That is an improvement over the earlier underspecified target language.

- The earlier hopper / load-cell confusion is gone from the manuscript text. `pr97_comments.md` records the correction: “No hopper in the end design; the auger tube itself is the reservoir, loaded via slots” and “A&D HR-100A analytical balance … NOT an HX711 load cell.” In the revised `main.pdf`, I find no `load cell` / `load-cell` wording, and §3.2/§3.4 consistently say `A&D HR-100A` analytical balance over `RS-232`. That issue was raised in round 1 for the paper more broadly and is now resolved for the manuscript text surrounding this figure.

Not yet resolved from round 1

- The figure-number mismatch is still not fully cleaned up across the bundle. The supplied caption file begins `# Caption for fig3_dispense (main.tex, Figure 3...)`, but the compiled manuscript labels this figure `Fig. 4`. In `main.pdf`, §2.4 opens with “Fig. 4 summarizes…” and the caption under the rendered figure begins `Fig. 4 Dispensing characterization...`. So the manuscript is internally consistent, but the review bundle metadata/caption-header remains stale.

- Panel (b) still does not match the manuscript’s stated acceptance logic. `make_figures.py` draws a single constant ±10% envelope across the full range:
  - requests: `req = np.logspace(np.log10(0.02), np.log10(5), 14)`
  - band: `ax.fill_between(lims, [l * 0.9 for l in lims], [l * 1.1 for l in lims], ...)`
  The caption in both `caption_fig3_dispense.md` and `main.pdf` still says “shaded band is ±10%.” That conflicts with the revised body text in `main.pdf` §2.4, which says the actual target is `±5% above 100 mg and ±10% at 20 mg`. This was a concrete round-1 issue and it remains open.

- The figure/caption still do not carry replicate counts or uncertainty. Round 1 asked not to show parity points without uncertainty. In the revised figure, panel (b) remains plain colored points with no error bars; panels (a) and (c) are bare lines. `caption_fig3_dispense.md` contains no `n`, no uncertainty description, and `make_figures.py` adds no uncertainty encoding. The only place `n ≥10 replicates per condition` now appears is `main.pdf` §3.4.

- Missing operating conditions in the figure remain missing. Round 1 asked for fixed rpm in panel (a), fixed requested dose in panel (c), and tested setpoints in panel (b). The revised `fig3_dispense.pdf` axes still show only:
  - (a) `Time (s)` vs `Dispensed mass (g)`
  - (b) `Requested mass (g)` vs `Measured mass (g)`
  - (c) `Auger speed (rpm)` vs `Dose CV (%)`
  Neither `caption_fig3_dispense.md` nor `make_figures.py` states the fixed rpm for (a), the fixed dose for (c), or the discrete tested targets for (b).

- Panel (c) was not revised to a more controller-relevant metric. It is still “Dose repeatability (coefficient of variation) versus auger speed” in `caption_fig3_dispense.md` and in `make_figures.py`. The round-1 request to use something like time-to-target, overshoot, or coarse-only vs coarse-then-trickle performance remains unmet.

- The suggested file-level provenance additions for future real data are still absent. The branch tree names plausible source locations such as `hardware/test-module/firmware/dosing.py`, `hardware/test-module/firmware/scale.py`, `hardware/test-module/analysis/rs232_analysis.py`, `docs/candidate-powders.md`, and `docs/candidate-powders-shopping-list.md` in `all_branches_file_tree.txt`, but the revised caption and manuscript text do not cite any of these files for this figure.

- HUMAN vs AI signposting was not added for this figure. `caption_fig3_dispense.md` is purely descriptive and does not clarify that this panel set is synthetic plotting authored from code rather than AI-generated experimental evidence. Given `pr97_comments.md` line ~189 (“clarify where ai was used … it should always be clear who did what”), that figure-specific signposting issue remains open.

Remaining concrete inconsistencies or unsupported claims fixable without new bench data

- Caption/body mismatch on acceptance criteria. This is the cleanest remaining inconsistency. `caption_fig3_dispense.md` and the compiled `Fig. 4` caption both say “shaded band is ±10%”, while the body text in `main.pdf` §2.4 says the target is `±5% above 100 mg and ±10% at 20 mg`. One of those must change. Since `make_figures.py` currently plots a uniform ±10% band, the easiest non-bench fix is either:
  - redraw panel (b) with the stepped/segmented acceptance envelope that matches the body text, or
  - explicitly label the ±10% band as a temporary placeholder envelope in both the panel and caption.

- Caption still reads more like a results caption than a protocol caption. The body has already shifted to “illustrating the analysis and presentation that the bench campaign … will populate,” but `caption_fig3_dispense.md` still uses bare result-style descriptions. A no-data fix is to change each clause to “illustrative placeholder for…” or “intended analysis: …”. Right now the body and caption are not at the same level of caution.

- Panel (c) caption logic overstates what the panel shows. The caption says panel (c) is “motivating coarse-then-trickle dosing.” But the plotted quantity is only CV vs rpm. That supports a generic speed/precision tradeoff; it does not by itself show the benefit of switching from coarse to trickle. Without new data, this can be fixed by softening the wording to something like “illustrating the speed/precision trade-off relevant to coarse-then-trickle control.”

- The figure still lacks the protocol metadata the body now has. `main.pdf` §3.4 already gives reusable text: `n ≥10`, `20 mg–5 g`, `90%` switch point, `RS-232`, `median-of-5`, `quiet windows ≥0.5 s`, and `A&D HR-100A`. None of that requires new measurements. At minimum, the caption could add the intended tested range and the planned replication level. Candidate real workflow files named in `all_branches_file_tree.txt` that this wording could point to are `hardware/test-module/firmware/dosing.py`, `hardware/test-module/firmware/scale.py`, `hardware/test-module/firmware/sim/sim_rig.py`, and `hardware/test-module/analysis/rs232_analysis.py`.

- The fixed-condition wording remains underdocumented. Panel (a) says “fixed auger speed” but not which speed; panel (c) shows CV vs rpm but not at which requested dose. Even for synthetic placeholders, the caption can state that the exact values are placeholders or intended operating conditions. No new data are required to add those labels.

- The synthetic watermark is still very dominant. In `make_figures.py`, `synthetic_watermark()` places a centered diagonal `SYNTHETIC DATA` label at `fontsize=11`, `alpha=0.38` on every panel. Round 1 suggested moving synthetic status to a smaller corner label. Since the synthetic status is already explicit in the caption and body, this is an implementable presentation fix with no bench work.

- The figure bundle still has stale naming that can confuse review. The local files are `fig3_dispense.pdf` and `caption_fig3_dispense.md`, but the manuscript compiles this content as `Fig. 4`. That discrepancy is visible in the supplied files themselves and should be normalized in the caption header / README / review notes.

- The figure still has no AI/HUMAN provenance cue. Per the project-wide rule in `pr97_comments.md`, the figure should not leave ambiguity about authorship. For this figure, the safe statement is that the plotted placeholder data are synthetic code-generated placeholders curated by humans for manuscript layout, and are not experimental outputs from either humans or AI. That distinction matters because the paper’s real AI claims are about programmatic CAD generation, not about generating experimental results.

Prioritized non-bench fixes remaining

1. Fix panel (b) and its caption so the acceptance envelope matches `main.pdf` §2.4 (`±5% above 100 mg`, `±10% at 20 mg`), or explicitly mark the current ±10% band as placeholder-only.
2. Update the caption to match the body’s protocol-safe wording: say the panels illustrate the intended analysis/presentation, not measured performance.
3. Add missing figure-level metadata already present in `main.pdf` §3.4: `n ≥10`, `20 mg–5 g`, `A&D HR-100A`, and key controller details as concise caption text or panel annotations.
4. Fix the stale bundle numbering (`caption_fig3_dispense.md` says Figure 3; compiled manuscript is Fig. 4).
5. Soften panel (c) wording from “motivating coarse-then-trickle dosing” to a claim the plotted CV-vs-rpm panel actually supports.
6. Reduce the diagonal watermark to a less intrusive corner or panel tag.
7. Add one short HUMAN-vs-AI provenance note for this figure, making clear that these are synthetic placeholders generated in code for layout/protocol illustration, not AI-generated experimental findings.

- Discretionary analytical decisions made during the analysis
- Treated `main.pdf` as the authoritative source for compiled figure numbering and current manuscript wording, while still checking `caption_fig3_dispense.md` for stale bundle metadata.
- Counted an issue as resolved when the revised manuscript body fixed it, even if the standalone caption file or panel artwork had not yet caught up.
- Excluded “replace synthetic data with bench data” from the action list because the user explicitly said not to re-litigate the known placeholder status.
- Used branch-tree paths from `all_branches_file_tree.txt` only as named candidate provenance files, without claiming their contents beyond what the filenames support.
- Kept attribution strictly at HUMAN vs AI, per instructions, and avoided naming individuals even when `pr97_comments.md` did.
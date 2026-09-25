Resolved items from round 1

- Synthetic status is now explicit in both the figure and caption.
  - The caption now opens: “Dispensing characterization (SYNTHETIC placeholder data, to be replaced by bench measurements; watermarks will be removed when real data are substituted).” (`caption_fig3_dispense.md:3`)
  - The code applies a watermark to all three panels via `synthetic_watermark(ax)` in panels (a)–(c). (`make_figures.py:358, 376, 388`)
  - The compiled manuscript carries the same warning in the figure caption and in §2.4: “The data shown are synthetic placeholders…” (`main.pdf`, p. 6 §2.4; p. 7 Fig. 4 caption)

- The figure is now aligned with the manuscript’s four-powder story.
  - `make_figures.py` defines four powders: glass beads, alumina, 316L steel powder, and xanthan gum. (`make_figures.py:334-339`)
  - Section 2.4 names the same set: “free-flowing glass beads, alumina, 316L steel powder, and cohesive xanthan gum.” (`main.pdf`, p. 6 §2.4)
  - Panel (a) legend in the revised figure shows those four powders, and panels (b)–(c) reuse the same color mapping. (`fig3_dispense.pdf`; `make_figures.py:350-356, 363-367, 381-384`)

- The caption now matches the current three-panel layout and panel meanings.
  - Panel (a): “Cumulative dispensed mass versus time…” (`caption_fig3_dispense.md:3`)
  - Panel (b): “Requested versus measured dose…” (`caption_fig3_dispense.md:3`)
  - Panel (c): “Dose repeatability (coefficient of variation) versus auger speed…” (`caption_fig3_dispense.md:3`)
  - These match the plotting code in `fig3()` and the rendered PDF. (`make_figures.py:347-388`; `fig3_dispense.pdf`)

- The manuscript body now explains what each panel is meant to represent, instead of leaving the synthetic figure underspecified.
  - §2.4 states that panel (a) is for “mass-flow calibrations,” panel (b) is the “primary accuracy metric,” and panel (c) motivates coarse-then-trickle dosing. (`main.pdf`, p. 6 §2.4)

Previously flagged issues not yet resolved

- The figure-number mismatch is still not resolved across the bundle.
  - The bundle metadata and caption header still call this “Figure 3”: `caption_fig3_dispense.md:1` says “# Caption for fig3_dispense (main.tex, Figure 3 …)”.
  - The compiled manuscript labels the same graphic “Fig. 4”. (`main.pdf`, p. 7, Fig. 4 caption)
  - The source filename is still `fig3_dispense.pdf`, and `make_figures.py` still saves it under that name. (`make_figures.py:390`)

- Panel (b) still does not match the manuscript’s stated acceptance criteria.
  - The manuscript text says: “Acceptance targets … are ±5% accuracy above 100 mg and ±10% at 20 mg…” (`main.pdf`, p. 6 §2.4)
  - The rendered caption still says: “shaded band is ±10%.” (`caption_fig3_dispense.md:3`; `main.pdf`, p. 7 Fig. 4 caption)
  - The code draws a uniform multiplicative ±10% band across the whole range using `0.9x` to `1.1x`. (`make_figures.py:368-372`)
  - So the earlier inconsistency remains: the plotted criterion is flatter and looser than the manuscript criterion.

- The requested-mass axis in panel (b) still extends beyond the stated test range.
  - The synthetic setpoints are generated from 0.02 g to 5 g. (`make_figures.py:362`)
  - But the axis/identity-line limits are set to `[0.01, 8]`. (`make_figures.py:368`)
  - §2.4 and §3.4 both describe evaluation across 20 mg–5 g. (`main.pdf`, p. 6 §2.4; p. 7 §3.4)

- The caption is better, but it is still not fully placeholder-safe at the panel-description level.
  - The lead sentence clearly says placeholder/synthetic. Good.
  - But the panel text still reads like measured results rather than planned analyses: “Requested versus measured dose with closed-loop gravimetric control,” “Dose repeatability… versus auger speed…” (`caption_fig3_dispense.md:3`)
  - §2.4 is more careful: it says the figure is “illustrating the analysis and presentation that the bench campaign now under way will populate.” (`main.pdf`, p. 6 §2.4)
  - That more cautious framing has not been carried into the caption itself.

- The caption still does not carry the protocol details that round 1 said were missing.
  - No replicate count appears in the caption, though §3.4 says “n ≥ 10 replicates per condition.” (`main.pdf`, p. 7 §3.4)
  - No operating condition is given for panel (a), despite “fixed auger speed” being claimed in the caption. (`caption_fig3_dispense.md:3`)
  - No fixed requested dose is given for panel (c), even though §3.4 says calibration sweeps are done “at fixed dose.” (`main.pdf`, p. 7 §3.4)
  - No tested setpoints are named in panel (b), beyond what can be inferred from the code. (`make_figures.py:362`)

- Round-1 signposting on HUMAN vs AI is still absent for this figure.
  - PR review explicitly asked to “clarify where ai was used” and to keep “always … clear who did what.” (`pr97_comments.md:22-36`)
  - The current Figure 4 caption has no HUMAN/AI attribution line. (`caption_fig3_dispense.md`)
  - For this specific figure, that omission is easy to fix because the bundle itself says it consumes no CAD assets: “CAD-render assets consumed: (none; synthetic plot).” (`README.md:7-9`)

Remaining concrete inconsistencies or unsupported claims fixable without new bench data

- Caption/body mismatch on panel (a) purpose.
  - The body says panel (a) establishes “per-powder mass-flow calibrations.” (`main.pdf`, p. 6 §2.4)
  - The caption only says “Cumulative dispensed mass versus time per powder at fixed auger speed.” (`caption_fig3_dispense.md:3`)
  - Fix: add “illustrative mass-flow calibration curves” or equivalent to panel (a)’s caption text.

- Caption/body mismatch on panel (b) acceptance logic.
  - Body: ±10% at 20 mg, ±5% above 100 mg. (`main.pdf`, p. 6 §2.4)
  - Figure/caption/code: one uniform ±10% band. (`caption_fig3_dispense.md:3`; `make_figures.py:368-372`)
  - Fix: either redraw the shaded band as a piecewise acceptance envelope or explicitly label the current band as an illustrative placeholder that does not yet encode the final acceptance rule.

- Caption/body mismatch on panel (c) experimental framing.
  - Caption says “Dose repeatability … versus auger speed.” (`caption_fig3_dispense.md:3`)
  - §3.4 says calibration sweeps are “auger speed at fixed dose.” (`main.pdf`, p. 7 §3.4)
  - The figure itself does not indicate the fixed dose.
  - Fix: add the fixed-dose condition to the caption or panel annotation.

- Unsupported “fixed auger speed” wording in panel (a) without an actual speed value.
  - Caption claims fixed speed. (`caption_fig3_dispense.md:3`)
  - No rpm is shown in the panel or caption. (`fig3_dispense.pdf`)
  - Fix: add the rpm value, or soften to “illustrative cumulative dispensing traces.”

- Unsupported “closed-loop gravimetric control” wording in panel (b) without any controller signpost.
  - The wording is true at manuscript level: the balance is HR-100A over RS-232 and the control protocol is described in §3.4. (`main.pdf`, p. 2 §2.1; p. 7 §3.4; `pr97_comments.md:125-127`)
  - But panel (b) itself does not distinguish coarse-only vs coarse-then-trickle, quiet windows, or the 90% switch discussed in §3.4.
  - Fix: add a short caption phrase like “illustrative planned parity analysis for the coarse-then-trickle controller” or annotate the figure/SI, without claiming measured controller performance.

- Missing HUMAN vs AI attribution for a figure that is plainly code-generated rather than CAD-rendered.
  - `README.md` says this figure uses no CAD assets. (`README.md:7-9`)
  - `make_figures.py` generates the panels directly in matplotlib. (`make_figures.py:342-390`)
  - PR guidance says attribution should distinguish only HUMAN vs AI, and note that no GUI CAD package was used. (`pr97_comments.md:22-36, 128-130`)
  - Fix: add one caption sentence along the lines of: “This placeholder plotting figure was authored in code; it is not a CAD render. The underlying protocol and acceptance criteria were set by HUMAN researchers; no GUI CAD package was used in this project, and this figure consumes no CAD assets.” If you want to avoid overclaiming AI involvement here, keep it neutral and just state that it is a synthetic coded placeholder.

- Bundle-level provenance mismatch remains confusing.
  - The compiled order is Fig. 1 overview, Fig. 2 design specifics, Fig. 3 generative-AI CAD outcomes, Fig. 4 dispensing characterization, Fig. 5 future work. (`main.pdf`, pp. 3-7)
  - The local bundle calls this `fig3_dispense`, while `all_branches_file_tree.txt` also includes `paper/figures/fig3_dispense.pdf` as a repository path. (`all_branches_file_tree.txt`, line containing `paper/figures/fig3_dispense.pdf`)
  - Fix: either keep the repository-local filename but stop calling it “Figure 3” in the caption header, or rename the figure asset and manuscript references consistently.

- Minor cross-panel signposting gap.
  - Panel (a) contains the only powder legend; panels (b) and (c) reuse the same colors without saying so in the caption. (`fig3_dispense.pdf`; `make_figures.py:350-356, 363-367, 381-384`)
  - Fix: add “colors follow panel (a)” to the caption.

Prioritized action list

1. Fix panel (b) so the shaded acceptance band matches the manuscript’s stated ±10% at 20 mg / ±5% above 100 mg logic, or label the current ±10% band as placeholder-only.
2. Fix the numbering mismatch: stop calling this “Figure 3” in `caption_fig3_dispense.md` when the compiled manuscript labels it Fig. 4; reconcile filename/header/manuscript wording.
3. Make the caption fully placeholder-safe by changing panel descriptions from result-like wording to “illustrative/planned analysis” wording.
4. Add the missing protocol specifics already stated elsewhere in the manuscript: `n ≥ 10`, panel (a) speed condition, panel (c) fixed-dose condition, and the 20 mg–5 g range for panel (b).
5. Tighten panel (b) x-axis limits from `[0.01, 8]` to the actual 0.02–5 g range used in `make_figures.py`.
6. Add one short caption note on provenance/signposting: this is a synthetic code-generated placeholder figure with no CAD-render assets consumed; keep attribution at HUMAN vs AI only if you choose to mention it.
7. Add a small caption note that panels (b) and (c) use the same powder color coding as panel (a).

- Discretionary analytical decisions made during the analysis
- Treated the compiled `main.pdf` as the authority for manuscript figure numbering and in-text claims, while still checking the bundle-local names (`fig3_dispense`, `caption_fig3_dispense.md`) as part of the inconsistency audit.
- Counted an item as resolved only when the revised PDF/caption/code all agreed, not when the issue was fixed in the manuscript body alone.
- Did not re-argue the known problem that the plotted data are synthetic placeholders, per the user’s instruction; I limited unresolved items to metadata, wording, logic, and plotting choices that can be fixed without new measurements.
- Used `all_branches_file_tree.txt` only to name relevant repository paths, especially `paper/figures/fig3_dispense.pdf` and likely future control/protocol sources under `hardware/test-module/...`; I did not infer the contents of branch-tree-only files beyond what their names support.
- Treated HUMAN-vs-AI attribution as a signposting requirement rather than inventing specific authorship for this figure, because the supplied files do not explicitly document which agent, if any, drafted `make_figures.py`.
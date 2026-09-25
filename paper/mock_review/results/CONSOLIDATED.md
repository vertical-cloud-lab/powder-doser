# Per-figure Edison ANALYSIS review — consolidated digest

36 ANALYSIS tasks = 6 analytical lenses x 6 figures. Each task received the manuscript, the single figure, its caption, the figure source (`make_figures.py` + CAD-render assets), the static PR-comment snapshot, and the full cross-branch file tree. Full per-task answers are in `results/<lens>__<figure>.answer.md`; task ids in `figure_review_task_ids.json`. Notebooks are git-ignored (large embedded data) but reproducible via `fetch_figure_reviews.py`.


## fig1_overview


### consistency

Prioritized action list for Figure 1
- Replace panel (b) first. It is the main source of contradiction: it still shows a hopper/reservoir and a load cell. Candidate branch-tree assets to inspect next: `paper/figures/assets/auger_geared_cross_section.png` and `cad/auger-geared/archimedes-auger-geared-cross-section.png`.
- Remove `GT2` from panel (a) annotations in `make_figures.py` unless you can document an actual belt stage elsewhere in the manuscript.
- Rewrite panel (a) caption so it does not claim the render visibly shows the solenoid and vibration motor if those parts remain indistinct.
- Downgrade `sealed park` in panel (c) to `horizontal park` or equivalent manuscript-supported wording.
- If panel (b) cannot be replaced immediately, explicitly mark it as a historical v2 concept render with obsolete hopper/load-cell features so the figure stops contradicting itself.

- Discretionary analytical decisions made during the analysis
  - Treated visible text embedded in the supplied raster assets (`assets/*.png`) as primary evidence alongside the caption and extracted PDF text.
  - Used the branch-tree file list to name candidate replacement assets, but did not assume their contents beyond what their filenames support.
  - Counted a statement as inconsistent when the figure panel itself contradicted the caption/body, even if the caption attempted to verbally correct an older render.
  - Classified `sealed park` as an overstatement rather than a hard contradiction because the body supports `no gravity feed, clean shutoff` but not a literal seal.


### reviewer

Prioritized action list for Figure 1
- 1. Replace panel (b) with a final-design cross-section, or remove it from the main figure.
- 2. Replace panel (a) with an as-built photograph, or show render + photo side-by-side.
- 3. Add physical scale/dimensions to the overview: at least auger OD (25 mm) and overall footprint or a scale bar.
- 4. Redraw panel (d) so the target mass enters the controller, not the actuator.
- 5. Enlarge or simplify panel (c); explicitly mark hinge axis and fixed dispense point.
- 6. Either move panel (e) to SI or annotate it by generation (Gen 1–4).
- 7. Increase all panel text/callout sizes and re-tune leader lines after final export.

- Discretionary analytical decisions made during the analysis
- Treated `fig1_overview.pdf` plus `caption_fig1_overview.md`, `make_figures.py`, and `main.pdf` as the primary evidence, using `pr97_comments.md` and `all_branches_file_tree.txt` only for corroboration and candidate-file identification.
- Evaluated legibility from the exported PDF at final rendered size rather than from source-code nominal font sizes alone, because `bbox_inches="tight"` changed the effective printed scale.
- Focused the critique on figure necessity, legibility, and sufficiency for peer review, not on broader manuscript claims except where they directly affected figure consistency.
- Treated the Digital Discovery hardware editorial (DOI `10.1039/D4DD90009J`) as contextual journal-standard guidance for hardware-paper expectations, while avoiding unsupported claims about figure-specific RSC rules that were not directly retrieved verbatim.
- Fl


### provenance

Prioritized action list for Figure 1
- Highest priority: archive and cite the exact generator for panel (a), not just `assembly_iso_final.png`. If it came from `cad/mounting-plate-assembly/render_assembly.py` plus imported STLs, say so explicitly and archive the exact commit/branch inputs.
- Fix panel (a) caption/callouts to match what the repository and render actually support. Remove or qualify “NEMA-11,” “GT2,” and any mention of visible solenoid/vibration motor unless those files and rendered parts are archived.
- In panel (b), keep the “early v2-module render” qualifier and make the non-final hopper explicit in the panel text or caption, since HUMAN review says the final design has no separate hopper.
- In panel (c), cite one canonical source path for `rotation_0_45_90` and archive the SVG if that is the publication master.
- In panel (e), cite `DESIGN-LOG.md` directly in the caption or SI so the “97-entry design log” claim is auditably tied to a repository file.

- Discretionary analytical decisions made during the analysis
- Treated visual identity between the supplied and regenerated PDFs as sufficient evidence of figure reproducibility, since bytewise PDF equality is not expected across save operations.
- Used the cross-branch filename tree as the authoritative source for repository provenance, because the task required grounding claims in supplied files and naming files from that tree.
- Mapped panel (a) to the closest integrating CAD branch (`origin/copilot/add-servo-angle-control`) even though the exact upstream render script for `assembly_iso_final.png` was abs


### improvement

st final render from the branch tree and say plainly that it is a CAD render.

- **Discretionary analytical decisions made during the analysis**
- Prioritized internal consistency over visual novelty, because the supplied review comments identify factual mismatch as the main risk.
- Treated `assets/single_channel_module_powder_flow.png` as unsuitable for a main-text overview panel because its labels and geometry conflict with the final design described in `caption_fig1_overview.md`, `pr97_comments.md`, and `main.pdf`.
- Recommended keeping a five-panel structure only conditionally; otherwise suggested moving the timeline to SI as a valid alternative use of space.
- Interpreted the manuscript body’s description of a “printed spur pair, 2.25:1” as the authoritative drive description when resolving the figure’s “GT2/gear drive” inconsistency.
- Limited provenance language to HUMAN vs AI contributions, per the supplied instructions and review comments, and avoided naming individuals.
- Treated branch-tree file paths as candidate assets only when they were explicitly present in `all_branches_file_tree.txt`, and marked uninspected files as candidates rather than asserting their contents.


### signposting

prioritized action list for Figure 1

1. **Revise the caption first** to state the HUMAN/AI split explicitly, using wording close to the rewrite above.
2. **Add a brief in-figure signpost**, ideally in panel (e) or as a small global note: “Humans chose the design and reviewed/tested parts; AI generated parametric CAD models.”
3. **Avoid implying AI made architecture decisions** in panels (a)-(c); keep wording on AI to “modelled/rendered” rather than “designed”.
4. **Keep the no-hopper correction** exactly as now in panel (b), because `pr97_comments.md` explicitly flags this.
5. **If space allows, anchor the timeline to provenance artifacts** by citing the human sketch (`powder-excavator-sketch.jpg`) and the repository design log (`DESIGN-LOG.md` / issue `#73`, PR `#74`) in the main text or SI, not necessarily in the caption.

- Discretionary analytical decisions made during the analysis
- Used the manuscript body in `main.pdf` as the controlling statement of intended authorship when judging caption adequacy, because it contains the clearest explicit HUMAN/AI division.
- Treated branch-tree file paths as provenance evidence for likely relevant artifacts when the files themselves were not included in the bundle.
- Did not attribute any panel to Zoo Design Studio specifically, because the supplied figure bundle and branch-tree paths did not tie Figure 1 assets unambiguously to a Zoo-derived render.
- Focused the rewrite on authorship clarity rather than stylistic shortening, because the user’s stated priority was AI-vs-human signposting.


### narrative

Prioritized action list

1. **Fix the contradiction in (b).** Either redraw the cross-section to match the final no-hopper design (auger tube = reservoir, loaded through top-cap slots) or drop the panel. The current caption disclaimer is not a fix; it admits the asset is wrong (`pr97_comments.md` line 178; `main.pdf` Sec. 2.1 p. 2).
2. **Move (e) timeline out of Fig. 1.** Either to SI, to an inline Sec. 2.2 element, or replaced by the deferred design-log analysis (acceptance rate by workflow, defect taxonomy from `DESIGN-LOG.md` and `design-log-analysis.answer.md`). It duplicates the four-generation prose, introduces dates the text never uses, and dilutes a hardware-overview figure with a methodology narrative.
3. **Decide on (d).** Recommend cut. If retained, move next to Sec. 3.4 / Fig. 4(b), where the loop is actually specified and measured. The current placement makes Fig. 1 a mini-abstract-figure rather than a hardware overview.
4. **Replace the (a) CAD render with a photograph of the printed platform** as the caption already promises. Use `presentation/assets/final-print-on-ultimaker.jpg` or `docs/assets/printed/auger-issue16-print-nacl.jpg` from the branch tree. While doing this, verify the callouts (the (a) panel asset is ~89% transparent, so labels currently float over empty space).
5. **Tighten callout text in (a)** to match the manuscript's "no hopper" language so panels (a) and (b)/Sec. 2.1 are mutually consistent.

### Discretionary decisions

- Treated Fig. 1(c) as the strongest panel because the fixed-dispense-point geometry is the only Fig. 1 claim the prose


## fig2_genai


### consistency

prioritized action list for this figure
1. Replace panel (d) with an actual whole-assembly/single-prompt failure render, or rewrite panel (d) to match the current `single_channel_module_iso.png` asset.
2. Replace panel (f) with the correct mounting-plate iteration render in the same framing as (e), (g), and (h).
3. Resolve panel (b) ambiguity: decide whether it shows the final Zoo-derived tap collar or the last pre-Zoo programmatic iteration, then rewrite title + caption accordingly.
4. Update the caption header / bundle metadata so this figure is called Figure 3 in the manuscript context.
5. Add callouts/crops to panels (e–h), especially the hole, raised-platform region, and gap.
6. Soften or source the stale-input root-cause statement for (e–h) if the exact provenance files are not being cited.

- Discretionary analytical decisions made during the analysis
- Treated the compiled manuscript (`main.pdf`) as the authoritative source for final figure numbering, over developer-facing filenames/comments in `caption_fig2_genai.md` and `make_figures.py`.
- Used `all_branches_file_tree.txt` to infer asset provenance when the underlying branch files themselves were not directly included in the bundle.
- Flagged claims as unsupported when they were not traceable from the supplied files, even if they were plausible from context.
- Did not treat readability problems alone as contradictions, but reported them when caption claims depended on details that are barely visible in the rendered figure.
- Kept attribution strictly at HUMAN vs AI, per instructions, and did not name individuals 


### reviewer

prioritized action list

1. Redo panel (d) so the claimed interferences/floating parts are actually visible, ideally with arrows/callouts.
2. Re-render panels (e–h) from one fixed viewpoint and add defect annotations or zoomed insets.
3. Add the actual Zoo-derived production tap collar, or rewrite panel (b)/caption so the shown object is not mistaken for the final production part.
4. Add scale context: scale bars, key dimensions, or labeled clearances for panels where geometry is the claim.
5. Resolve provenance gaps for the figure assets and fix the figure-numbering mismatch between `caption_fig2_genai.md` and `main.pdf`.
6. If space allows, replace one weak qualitative panel with one compact quantitative summary from the logged iteration history.

- Discretionary analytical decisions made during the analysis:
- Treated the compiled `main.pdf` as the authoritative source for figure numbering when it conflicted with `caption_fig2_genai.md` and `README.md`.
- Evaluated legibility primarily at the scale of the supplied rendered figure, because that approximates reviewer experience better than inspecting raw asset files alone.
- Used `all_branches_file_tree.txt` to assess likely provenance paths for panel assets, but did not claim absence of source files beyond what was findable in that supplied tree.
- Interpreted this as a figure-specific peer-review task, so I focused on evidentiary sufficiency, attribution clarity, and hardware-figure conventions rather than rewriting manuscript prose more broadly.
- Flagged the absence of quantitative subpanels as a weakness because the b


### provenance

Prioritized action list for this figure:
- **1. Highest priority:** archive or cite the exact upstream source files for panels (e)–(h). Right now the four mounting-plate iteration panels are manuscript-only PNGs with no traceable per-panel CAD/code in the branch tree.
- **2. Archive the exact tap-collar provenance chain for (a) and (b):** the specific `v1` snapshot for panel (a), the reviewed programmatic snapshot for panel (b), and, separately, the actual Zoo Design Studio production tap-collar files or transcript-backed exports if panel (b) is meant to reference them.
- **3. In the caption or SI, distinguish clearly that panel (b) shows the programmatic reviewed collar, while the production collar was later redesigned in Zoo Design Studio and is not necessarily the image shown.**
- **4. Cite concrete source paths for the well-supported panels in the SI or repository release:** the auger branch files for (c) and the single-channel-module files for (d).
- **5. Fix numbering drift:** reconcile the bundle metadata calling this Figure 2 with the supplied compiled `main.pdf`, where this caption appears as Figure 3.

- Used the supplied `make_figures.py` and bundled assets as the sole basis for reproducibility verification; did not infer missing data beyond the branch tree and comment snapshot.
- Treated near-identical regenerated PDF output as reproducible despite byte-level differences, because rasterized comparison showed only minimal rendering/metadata variation.
- Mapped manuscript assets to upstream CAD/code by exact filename when possible; otherwise used closest branch-tr


### improvement

prioritized action list for this figure
- Rebuild Figure 2 around failure row vs recovery row; do not keep the current mixed “bad/good/good/bad” top row.
- Remove `plate_iter2_platforms_iso.png` from the main figure unless you can re-render the whole plate sequence from one viewpoint.
- Add visible callouts on defect regions; don’t rely on the caption alone.
- Replace one plate iteration slot with a compact workflow-summary panel.
- Rewrite the caption to make HUMAN vs AI roles explicit and to state that no GUI CAD package was used; mention late Zoo Design Studio / Zookeeper use and the three-iteration tap-collar recovery.

- Discretionary analytical decisions made during the analysis:
  - Prioritized narrative clarity over preserving all eight current renders at equal status, and recommended replacing one render with a text summary panel.
  - Recommended dropping `plate_iter2_platforms_iso.png` from the main-text figure because its unmatched isometric viewpoint weakens the iteration story more than the extra intermediate state helps.
  - Treated the figure as a qualitative workflow/provenance figure, so I did not recommend adding quantitative bench data.
  - Used the manuscript’s compiled Figure 3 / section 2.3 narrative in `main.pdf` and review comments in `pr97_comments.md` as the governing interpretation when resolving how the figure should communicate the workflow.
  - Produced a concrete mockup using only supplied assets to test whether the proposed panel reordering is implementable without new data.
  - Limited claims about iteration counts to those explicitly presen


### signposting

Prioritized action list
- **1. Replace the caption lead sentence** with an explicit HUMAN/AI division-of-labour sentence, using the manuscript wording as the source of truth.
- **2. Revise panels (b), (c), and (e–h)** so they explicitly say humans supplied specifications/drawings or corrected inputs, while AI generated the CAD geometry.
- **3. Add one clause stating that no conventional GUI CAD was used**, to stay consistent with `pr97_comments.md` and the manuscript.
- **4. Check the figure numbering mismatch** between `README.md`/`caption_fig2_genai.md` and the compiled `main.pdf` before editing `main.tex`.

- Used the manuscript text in `main.pdf` as the primary source of truth for the HUMAN/AI division of labour because it is more explicit than the current caption.
- Treated `pr97_comments.md` as the controlling constraint for interpretation where it corrected or sharpened figure wording, especially for panel (a) and AI-vs-human signposting.
- Used `all_branches_file_tree.txt` only to name likely relevant provenance files and branch-tree paths, without claiming contents that were not present in the supplied bundle.
- Did not infer any individual-specific attribution; all attribution was collapsed to HUMAN vs AI as instructed.
- Flagged the apparent figure-number mismatch because `README.md` says Figure 2 while `main.pdf` displays the reviewed panel set as Fig. 3.


### narrative

Prioritized action list (this figure)

1. KEEP in the main text; do not move to SI or merge with Fig. 1.
2. Resolve the (e–h) framing conflict between body text ("agent proposed the raised-bracket solution") and caption ("agent silently designed around stale inputs"). Pick one story and align.
3. Fix panel (d) title from "v1 module" to "v2 module" to match Section 2.2 and the asset branch (`modular-single-channel-powder-doser-design`).
4. Reconcile the figure number across `fig2_genai.pdf` / `caption_fig2_genai.md` / `README.md` / main.tex callouts so file name, callouts, and compiled label agree.
5. In panel (b)'s caption add "via the Zookeeper agent" to make the only Zoo Design Studio main-text figure-callout name the agent (responding to @swcharles, PR #97 line 245).
6. Optional: add a brief subtitle annotation to (a) vs (b) explicitly tagging the workflow used for each ("whole-assembly programmatic CAD" vs "Zoo Design Studio / Zookeeper"), so a reader who skims only the figure can recover the central claim of Section 2.3.

### Discretionary decisions

- Used "Figure 3" when describing the figure's location in the compiled PDF and "fig2_genai" / "Figure 2" when referring to the bundle's naming; this avoids ambiguity but the manuscript itself must pick one.
- Treated reuse of `auger_assembly_iso.png` and `single_channel_module_iso.png` across figures as asset-level reuse rather than redundancy, because the framings and accompanying captions assign each instance a distinct narrative job. A stricter reviewer could call this duplication; I judged it acceptable.
- Recommended


## fig3_dispense


### consistency

Prioritized action list for this figure
- Fix the numbering mismatch first: update the bundle metadata/caption header from “Figure 3” to “Figure 4” to match `main.pdf`.
- Fix panel (b) next: either redraw the acceptance envelope to match the manuscript’s ±5% / ±10% target logic, or explicitly label the ±10% band as a placeholder only.
- Tighten the caption so every claim is placeholder-safe: say that panels illustrate the intended analysis, not measured performance.
- Add one sentence that final experimental panels will summarize replicate measurements (n≥10 per condition) with uncertainty.
- Optionally tighten panel (b) axis limits to the actual 20 mg–5 g range used in `make_figures.py`.
- Add “mass-flow calibration” language to panel (a) so the caption matches the manuscript body’s stated purpose.

- Discretionary analytical decisions made during the analysis:
  - Treated the compiled `main.pdf` as the authoritative source for the manuscript’s current figure numbering, because the task asked for consistency against “the manuscript body.”
  - Flagged some items as “unsupported/overstated” rather than “contradictory” when the figure was explicitly synthetic but the caption still read too empirically.
  - Did not infer hidden repository content beyond naming branch-tree paths; only used supplied files for substantive claims, per the task instruction.
  - Focused on figure/caption/body/reviewer consistency and did not expand into broader manuscript issues not tied to this figure.


### reviewer

Prioritized action list

1. Highest priority: replace the synthetic data with real dispensing measurements or remove the figure from the main text.
2. Redraw panel (b) using the manuscript’s actual acceptance criteria: ±10% at 20 mg and ±5% above 100 mg.
3. Add replicate counts and uncertainty for all panels; do not show parity points without uncertainty.
4. Add missing operating conditions: fixed rpm in panel (a), fixed requested dose in panel (c), and tested setpoints in panel (b).
5. Replace or augment panel (c) with a controller-relevant metric such as time-to-target, overshoot, or coarse-only vs coarse-then-trickle performance.
6. Add actuation-ablation and powder-descriptor context, either in the figure or companion SI.
7. Improve legibility with larger text and non-color encodings.

- Discretionary analytical decisions made during the analysis
- Treated the figure source file `fig3_dispense.pdf` as the target even though it is numbered as Figure 4 in the compiled `main.pdf`.
- Used the supplied caption file, figure-generation script, PR comment snapshot, and manuscript text as the admissible evidence base; did not infer missing experimental results.
- Quantified issues in the synthetic code output (e.g., implied flow rates, acceptance-band mismatch, curve redundancy) because these are directly derivable from `make_figures.py` and the supplied figure.
- Considered scale bars not applicable for this data figure, and instead focused on missing operating-condition metadata, units, uncertainty, and controller context.
- Named potentially relevant branch-tree files only as


### provenance

Prioritized action list for Figure 3:
- Replace the synthetic panels with real dispensing data before submission, or move the figure out of Results if bench data are not ready.
- Merge or archive the `origin/copilot/integrate-scale-feedback-loop/hardware/test-module/...` files alongside the manuscript, because they are the main real sources substantiating “closed-loop gravimetric control.”
- Archive and cite the powder-selection files `docs/candidate-powders.md` and `docs/candidate-powders-shopping-list.md` to justify the powder set used in the caption and code.
- Add explicit file-level citations in the caption or SI for the future real panel data sources, not just the plotting script.
- If Figure 3 remains synthetic in review drafts, label it in the manuscript text as a workflow/protocol figure rather than performance evidence.

- Used the supplied `all_branches_file_tree.txt` as the authoritative source for cross-branch file existence, because the task required naming files from the branch tree.
- Treated `make_figures.py` plus the bundled README/caption as the primary provenance evidence for whether Figure 3 consumes CAD assets or measured data.
- Distinguished between reproducibility of the figure artifact (plot can be regenerated from code) and reproducibility of the scientific claim (no measured dataset located).
- Used the manuscript PDF text as supporting evidence for claims about synthetic placeholder status and closed-loop dosing context, because `main.tex` was not separately supplied in the bundle.
- Flagged files on `origin/copilot/integrate-scale-feedback-loop


### improvement

prioritized action list

- **1. Replace current panel (c)** with a time-to-target panel or a controller-trace panel. Current CV-vs-rpm is the least defensible panel.
- **2. Replace parity panel (b)** with error-vs-requested-mass and draw the manuscript’s actual acceptance limits (`±10%`, `±5%`).
- **3. Convert panel (a)** from raw cumulative mass traces to calibration curves used by the controller.
- **4. Add direct controller annotations**: `90%` switch, trickle phase, tap/vibration events, quiet windows.
- **5. Move synthetic status to a small corner label** and stop using the dominant diagonal watermark.
- **6. Revise the caption** to name the powders, the A&D `HR-100A` analytical balance, `n ≥ 10`, and the explicit throughput/accuracy targets.

- Used the compiled `main.pdf` as the authority for what claims the figure must support, even though the source file is named `fig3_dispense.pdf` and renders as Fig. 4 in the PDF.
- Prioritized a `2 × 2` redesign over a `2 × 3` redesign to keep the figure implementable in a double-column RSC layout.
- Recommended replacing the parity plot with an error-vs-target plot because the manuscript’s acceptance criteria are threshold-based (`±5%`, `±10%`) rather than identity-line-based.
- Recommended dropping the synthetic CV-vs-rpm panel because the source code shows it is powder-independent apart from color and therefore not informative.
- Treated branch-tree paths such as `hardware/test-module/firmware/dosing.py`, `scale.py`, `sim/sim_rig.py`, and `rs232_analysis.py` as plausible implementation/data sources only because they appear in


### signposting

Prioritized action list for this figure
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


### narrative

Prioritized action list
- Replace `fig3_dispense.pdf` with real bench measurements or remove the figure from the main paper.
- If real data are not ready, delete the synthetic panels rather than moving them to SI unchanged; keep only a brief protocol description in text.
- When real data are ready, keep panel (b) as the core main-text result; demote or simplify panels (a) and possibly (c) if space is tight.
- Fix the figure-numbering mismatch between bundle metadata (`fig3_dispense`) and the compiled manuscript (dispensing appears as Fig. 4).
- If a non-results visual is still needed before data exist, build a protocol/control schematic from existing code paths named in `origin/copilot/integrate-scale-feedback-loop` instead of showing synthetic numeric outcomes.

- Set the decision threshold as: keep only with real data; otherwise cut rather than move to SI.
- Treated the compiled manuscript (`main.pdf`) as authoritative for narrative role, while using `make_figures.py`, the caption file, PR comments, and branch-tree paths to verify provenance and intent.
- Used branch-tree evidence to assess whether undisclosed real characterization datasets likely exist; because no such data files appear in `all_branches_file_tree.txt`, I did not infer any measured results beyond what the manuscript states.


## fig4_design


### consistency

prioritized action list for this figure:
1. **Fix panel (b) caption first.** Replace "carrying the solenoid striker and ERM vibration motor" with wording that says the printed geometry is **designed to mount** them, unless you replace the asset with a render that actually shows the actuators.
2. **Standardize bearing/drive wording.** Use **"without loading the auger bearing"** in both the body text and the caption.
3. **Tighten panel (a) caption.** Remove "flight clearances" unless you annotate the clearance explicitly in the graphic.
4. **Name the visible sub-assembly honestly.** If keeping the current panel (b) asset, mention the **mount plate** or call it a **tap-collar sub-assembly**.
5. **Optionally add provenance at first mention.** Since the final collar shown here came from a Zoo redesign, add one short AI-vs-human provenance note in the body text or caption.

- Treated `caption_fig4_design.md`, `make_figures.py`, `assets/tap_collar_final_iso.png`, `assets/auger_geared_cross_section.png`, `main.pdf`, `pr97_comments.md`, and `all_branches_file_tree.txt` as the only admissible evidence sources.
- Used the compiled PDF numbering (`main.pdf` Fig. 2) while also noting the repo-local name (`fig4_design`) because they differ.
- Counted as inconsistencies only cases where the figure/caption/body text overclaimed, disagreed, or omitted a visible subpart in a way likely to mislead a reader; I did not count every absent feature as an inconsistency unless the text implied it was shown.
- Treated the AI-attribution issue for panel (b) as a lower-priority consistency/signposting 


### reviewer

Prioritized action list for this figure**
1. Fix the figure-numbering/file-label inconsistency between `fig4_design.pdf` / `caption_fig4_design.md` / `make_figures.py` and the compiled `main.pdf`.
2. Add quantitative annotations to panel (a): at least auger OD, key internal diameter(s), pitch/lead, and the claimed flight clearance, all in mm.
3. Revise panel (b) so the solenoid striker, ERM motor location, auger tube, and load path are actually shown or explicitly marked as omitted.
4. Add callouts/arrows for all captioned features in both panels.
5. Consider a transverse inset or third panel to show radial clearance unambiguously.
6. Rework layout/size so panel (a) is readable at journal scale.
7. Tighten the caption so it matches only what is visible, and add a brief HUMAN vs AI provenance note if journal style permits.

- Assessed the design-specifics figure as the rendered asset `fig4_design.pdf`, while also noting that in the compiled manuscript this content is Fig. 2, not Fig. 4, because the supplied files are internally inconsistent.
- Used the compiled `main.pdf` as the primary source of manuscript-grounded claims, and used `make_figures.py`, `caption_fig4_design.md`, `pr97_comments.md`, and `all_branches_file_tree.txt` as supporting provenance/context files.
- Treated missing dimensions/scale bars/callouts as a sufficiency problem rather than inferring values from unavailable CAD source, because the actual source files with parameters are named in the branch tree but not present locally.
- Did not claim synthetic data in this figure, because only the dispensing-cha


### provenance

Prioritized action list

1. Add explicit provenance for panel (a): cite the exact auger branch and archive `cross-section-full.scad`, `archimedes-auger-geared.scad`, `auger-core.scad`, `gear-teeth.scad`, and the matching cross-section PNG.
2. Resolve panel (b) provenance: identify the exact source file that produced `paper/figures/assets/tap_collar_final_iso.png`. If it was a Zoo Design Studio result, archive the corresponding Zoo prompt/output files by name.
3. If no such final source can be located, rename/revert panel (b) to the traceable `design/cad/tap-collar` artifact and cite `cad_model.py`, `render_views.py`, `tap_collar.step`, and the matching render.
4. Rewrite the panel (b) caption to match what the render actually shows unless you can archive files for the solenoid striker, ERM motor, and true split-clamp geometry.
5. In the manuscript or SI, add a short provenance note for Fig. 4 stating that the figure is assembled from repository renders generated from programmatic CAD; no GUI CAD package was used, with late exploratory Zoo Design Studio use only where explicitly archived.

- Re-ran `fig4()` from `make_figures.py` in a writable sandbox to verify figure-level reproducibility from the supplied `assets/` bundle.
- Treated `paper/figures/assets/auger_geared_cross_section.png` as deriving from the full-length auger render and prioritized `cross-section-full.scad` over `cross-section-short.scad` because the bundled panel is a tall full-length cross-section.
- Used the branch tree as the authoritative source for file existence and flagged only files named there.
- T


### improvement

Prioritized action list for this figure
- 1) Replace panel (b) with a render that actually shows the solenoid/ERM arrangement, preferably from `design/cad/tap-collar/renders/assembly_side.png` or `assembly_iso.png`; otherwise generate one new render from `design/cad/tap-collar/cad_model.py` and `render_views.py`.
- 2) Widen panel (a) and switch to a short or cropped cross-section, ideally `cad/auger-geared/archimedes-auger-geared-short-cross-section.png` if available from the listed branch.
- 3) Add direct callouts on panel (a): helical flight, powder channel, wall, clearance, and transport direction.
- 4) Add direct callouts on panel (b): split clamp, strike path, ERM location, and avoided load path to the drive side.
- 5) Delete the verbose panel titles and replace them with compact labels plus a tighter caption.
- 6) Optionally add a small auger isometric inset from `cad/auger-geared/archimedes-auger-geared-short-iso.png` or `...-iso.png` to orient the section cut.

- Used the supplied `main.pdf` extracted text as the manuscript ground truth for how the figure is described, because `main.tex` itself was not included in the bundle.
- Treated the float-number mismatch as a LaTeX ordering issue: the bundle says “main.tex, Figure 4,” while the compiled `main.pdf` shows this content as Fig. 2.
- Limited all recommendations to existing supplied assets or branch-tree paths when possible, rather than proposing new scientific content.
- Did not assign dimensions or identify ambiguous geometry features beyond what can be supported by the visible render and caption text.
- Distingu


### signposting

Prioritized action list
- **1. Rewrite the caption** to state the HUMAN/AI split explicitly, using one of the versions above.
- **2. Fix panel (b) wording** from “carrying” to “used to mount” or add the actual solenoid/ERM to the render.
- **3. Add a visual provenance cue in-panel** if possible, e.g. a small subtitle: “Human-specified, AI-modelled”.
- **4. Cross-check numbering** so internal review notes do not confuse bundle name `fig4_design` with rendered manuscript Fig. 2.
- **5. If space allows, cite the workflow more concretely in nearby text** by pointing readers from this figure to the generative-AI evolution figure and the manuscript statement that humans supplied annotated/dimensioned drawings while AI handled parametric modelling.

- Used the rendered manuscript PDF, figure-generation script, static PR comment snapshot, and branch-tree file as the only evidence sources.
- Treated `fig4_design` as the bundle/file under review but noted that it renders as Fig. 2 in `main.pdf` because the manuscript includes figures out of filename order.
- Named branch-tree paths as relevant candidate provenance files when exact one-to-one asset derivation was not explicitly documented in the supplied files.
- Chose not to claim exact authorship for `tap_collar_final_iso.png` beyond what the manuscript and code explicitly support: a late-stage Zoo redesign for the production tap collar.
- Recommended caption wording that says “used to mount” rather than “carrying” because the rendered panel does not visibly include the solenoid or ERM motor.


### narrative

Prioritized action list for this figure
- **1. Remove the duplicated tap-collar panel or replace it with a genuinely new view.** `tap_collar_final_iso.png` is already reused in paper Fig. 3b via `make_figures.py`.
- **2. Decide whether the auger cross-section alone is enough for a main-text detail figure.** If yes, keep only that panel in main.
- **3. If keeping a two-panel main-text figure, swap in richer assets from the branch tree** such as tap-collar render sets under `origin/copilot/design-tap-collar` or clearer auger cross-sections under `origin/copilot/add-new-auger-design`.
- **4. Add callouts in `make_figures.py`** so “design specifics” are actually visible as specifics, not just unlabeled CAD renders.
- **5. If no stronger replacement is ready, move the current `fig4_design.pdf` to SI** and let paper Fig. 1 and Fig. 3 carry the main narrative.

- Treated the reviewed file `fig4_design.pdf` as paper-numbered Fig. 2 after verifying figure include order from `make_figures.py` and `main.pdf`.
- Evaluated narrative role primarily from explicit in-text callouts in `main.pdf`, weighting repeated callouts more heavily than caption intent.
- Judged redundancy at the asset level by tracing image reuse in `make_figures.py`, which showed `tap_collar_final_iso.png` is used in both the design-specifics and AI-outcomes figures.
- Considered branch-tree-only assets as possible alternatives, but did not assume their quality or exact appearance beyond what the file tree names support.
- Recommended “move to SI” as the fallback for the current figure because the manuscript remains c


## fig5_future


### consistency

Prioritized action list for Figure 5
- **1. Fix the strongest unsupported claim first:** change “working CAD in the repository” and “cartridge-sealing concepts” to wording that matches the actual repository tree.
- **2. Decide whether panel (a) is 8-channel or generic N-channel:** either relabel it as eight-channel or redraw it to look generic.
- **3. Clarify panel (b):** state that it is a preliminary positional/layout CAD study, not a full multi-module assembly and not a balance-integrated render.
- **4. Soften Section 4 future-work certainty:** align with the HUMAN reviewer comment that this area has changed and is not fully reported on GitHub yet.
- **5. If desired, add one sentence of provenance:** e.g. that the concept CAD is programmatic/AI-authored under HUMAN review, consistent with the manuscript’s broader attribution policy.

- Used only the supplied bundle (`main.pdf`, `caption_fig5_future.md`, `make_figures.py`, `assets/inward_collection_cup_iso.png`, `pr97_comments.md`, `all_branches_file_tree.txt`) and did not infer missing repository contents beyond the branch-tree paths.
- Treated `make_figures.py` as the authoritative source for what Figure 5 actually draws, including the hard-coded `n = 8` in panel (a).
- Distinguished between what is directly shown in the figure asset versus what is claimed in manuscript prose; flagged only cases where the prose exceeded the visible/rendered support or the repository tree support.
- Interpreted `origin/copilot/design-channel-sealing-cap` as evidence for channel/outlet sealing concepts, not cartridge-sealing concepts, bec


### reviewer

Prioritized action list for Figure 5

1. Decide whether to cut Figure 5 entirely or upgrade it substantially; do not keep it in its current placeholder state.
2. If retained, replace panel (b) with a clearer annotated render and/or top+section views, ideally using assets implied by `design/cad/inward-collection-cup/inward_collection_cup_top.png` and `sketch_top_side.png` from `origin/copilot/brainstorming-design-possibilities`.
3. Add explicit dimensions in mm: cup diameter, tilt angle, channel spacing, and nozzle-to-cup geometry.
4. Make panel (a) and panel (b) describe the same channel count and architecture.
5. Revise the caption to mark the figure as conceptual/exploratory future work, not validated hardware.
6. Add labels or a small extra panel addressing the critical SDL/metrology risks: spillover, cross-contamination, and single-balance interference.

- Discretionary analytical decisions made during the analysis
- Treated this as a qualitative figure-review task rather than a statistical analysis task because the supplied figure contains no quantitative dataset or testable measurements.
- Used `main.pdf`, `caption_fig5_future.md`, `make_figures.py`, `pr97_comments.md`, and `all_branches_file_tree.txt` as the primary evidence sources, and did not infer unsupported technical details from absent CAD source contents.
- Interpreted panel-legibility partly from the compiled `fig5_future.pdf` and the supplied render asset `assets/inward_collection_cup_iso.png`, because the figure-generation code shows that the asset is used directly.
- Flagged the panel-count/geometry misma


### provenance

Prioritized action list for this figure

1. **(must) Provide a source for panel (a).** Either: (i) add a `design/cad/multi-channel-radial/` directory (analogous to `inward-collection-cup/`) with a `cad_model.py` and a real render, then point `make_figures.py` at it; or (ii) rewrite the caption + body text to call panel (a) a *schematic concept drawn for the manuscript*, not a CAD study.
2. **(must) Tone down the body claim on main.pdf p. 7** ("the multi-doser geometry … already have working CAD in the repository"). The repository contains a single inward-tilting cup study and a sealing-cap branch — *not* a complete multi-doser geometry.
3. **(must) Drop "on a single balance" from caption (a)** or render a balance into the schematic — currently the asset doesn't include one.
4. **(should) Archive the panel (b) source bundle** with the manuscript: `design/cad/inward-collection-cup/{README.md, cad_model.py, inward_collection_cup.step, *_iso.{png,svg}, *_top.{png,svg}, sketch_2d.py, sketch_top_side.png}` from `origin/copilot/brainstorming-design-possibilities`, plus `paper/figures/make_figures.py` from `origin/copilot/draft-base-manuscript`. Cite them in the caption or SI.
5. **(should) Add an AI-vs-HUMAN attribution line to the caption** (per `@swcharles`'s PR-thread comment at `paper/main.tex` ~line 189): panel (a) matplotlib schematic and panel (b) `cad_model.py` are AI-authored; human contributions for this figure appear limited to review/curation.
6. **(nice) Merge the two source branches onto `main`** (or onto a tagged release used for archival/Zenodo DOI) so the figure's


### improvement

Prioritized action list

- P1: Replace current panel (a) with an annotated top-view geometry schematic showing dispense convergence, pitch radius, and 360°/N.
- P1: Keep `assets/inward_collection_cup_iso.png` as panel (b), but crop tighter and add direct callouts for inward tilt, common dispense region, and shared cup.
- P1: Expand the caption so it distinguishes CAD-backed content from architecture schematics and explicitly ties the figure to the manuscript’s 8–12-channel claim.
- P2: Add a small shared-balance arbitration panel explaining how one cup and one balance service multiple channels.
- P3: Add a scaling-roadmap panel only if you keep the “50-powder pool via swappable sealed cartridges” sentence in the manuscript.
- P3: If possible, pull `design/cad/inward-collection-cup/inward_collection_cup_top.png` or `sketch_top_side.png` from `origin/copilot/brainstorming-design-possibilities` to strengthen the CAD-backed part of the figure.

- Used the supplied branch tree to identify likely supporting assets on other branches, but did not assume their contents beyond the file names because those files were not present in the local bundle.
- Treated panel (b) as CAD-backed and proposed new panels (a), (c), and (d) as explicitly schematic to avoid overstating evidence.
- Recommended converting the figure from single-column to double-column because the current size in `make_figures.py` is too small for a legible architecture figure.
- Did not recommend any performance plots or powder-flow simulations because the bundle contains no multi-channel bench data, and the figure-gener


### signposting

Prioritized action list for Fig. 5

1. **Replace the caption** with one of the versions above so AI-vs-human authorship of each panel is explicit and the panels are flagged as unbuilt/untested (addresses PR97 threads at lines 189 and 258 simultaneously).
2. **Add a panel-level signpost on the figure itself.** Either tag (a) with a small "concept schematic" annotation and (b) with "AI-generated CAD render", or mirror the `synthetic_watermark` pattern from `make_figures.py` (lines 66–82) with a "CONCEPT — NOT BUILT" diagonal watermark on both panels. This matches the manuscript's existing convention for non-validated content (cf. Fig. 4 SYNTHETIC DATA watermarks).
3. **In `make_figures.py::fig5`, record the asset provenance in a comment** above line 398 pointing to `design/cad/inward-collection-cup/cad_model.py` on `origin/copilot/brainstorming-design-possibilities`, so the human-vs-AI claim in the caption is traceable from the figure source. (Optional but recommended given the reviewer's repeated insistence that AI claims be verifiable from GitHub.)
4. **Either generate a human-dimensioned engineering drawing** for the inward-collection-cup (the same way `cad/mounting-plate/drawing/engineering_drawing.{pdf,png,svg}` exists for the single-channel module on `origin/copilot/design-mounting-plate`) and add it as panel (c), **or** explicitly state in the caption that no such drawing exists yet. Without one of these, the figure cannot honestly show the "human reviewed, dimensioned" half of the workflow that §2.3 advertises.
5. **Cross-check Section 4 prose against the figure.** Th


### narrative

Prioritized action list

1. **Move Fig. 5 to the SI** (rename `figS2_future_multi_doser`), and replace the in-text Fig. 5 citation in §4 with a sentence pointer ("see SI Fig. S2"). Rationale: PR thread on line 258 says the future-work section and its figures will change; the figure is not anchored in Results; repo CAD does not yet support the N-channel claim.
2. **Fix the panel (b) caption/label mismatch.** The asset shows the cup, not "inward-tilting channels over [the] cup". Either re-render with a representative channel tilted over the cup (the inward-cup `cad_model.py` on `origin/copilot/brainstorming-design-possibilities` plus the single-channel module on `origin/copilot/draft-base-manuscript` can be composed), or relabel the panel honestly as "shared collection cup (CAD study)".
3. **Soften the §4 claim** "the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository." The branch tree only supports a cartridge STL under `design/cad/single-channel-module/stl/cartridge.stl` and the standalone `design/cad/inward-collection-cup/`. There is no N-channel array CAD on any of the 45 branches. Rewrite as "early CAD studies of the shared cup and a sealed cartridge exist in the repository (`design/cad/inward-collection-cup/`, `design/cad/single-channel-module/stl/cartridge.stl`)".
4. **If keeping (a) anywhere**, make it information-bearing: annotate the cartridge-swap concept, label the balance under the cup, and align N with the 8–12 number used in §4 — or drop the cartoon and replace with a small top-view CAD render generated from the s


## figS1_nozzles


### consistency

Prioritized action list for Fig. S1
- **1. Fix the caption first.** Replace “differing in exit constriction and chamfer geometry” with wording the reader can verify from the rendered panels.  
- **2. Verify Type 1–4 labels against final CAD source.** Use the branch-tree source candidates `origin/copilot/add-new-auger-design → cad/auger-geared/nozzle-variants.scad` and `archimedes-auger-test-nozzle1–4.scad`, because the manuscript itself reports a prior nozzle-label swap.  
- **3. Either crop tighter or rename the figure.** If the panels remain full lower-auger cross-sections, call them “auger lower-end / nozzle-tip variants,” not just “exit-nozzle variants.”  
- **4. If geometry-specific claims matter, annotate the panels.** Add dimensions or parameter callouts for the actual controlled differences.  
- **5. Keep the legend narrow unless verified.** Do not add hopper, sensor, or tool-attribution detail unless it is directly checked against the relevant source files and reviewer corrections.

- Used the supplied manuscript PDF, SI PDF, caption file, figure-generation script, rendered assets, PR comment snapshot, and branch-tree listing as the only evidence base.
- Treated visual inspection of the supplied cross-section assets as evidence for what the figure does and does not actually show.
- Did not infer exact geometric dimensions or parameter values from the images alone, because those values are not present in the supplied bundle.
- Flagged the nozzle-label swap as a provenance risk rather than a proven current error, because the supplied files document the prior swap but


### reviewer

prioritized action list for Figure S1
1. Add quantitative geometry labels for each variant: exit diameter, minimum constriction diameter, chamfer angle, and key axial lengths, all in mm/deg.
2. Add a zoomed inset of the exit region for each type, or a second row showing only the terminal tip at larger scale.
3. Revise the caption to say what varies, what stays fixed, and whether the panels are CAD cross-sections of an integrated auger-nozzle body.
4. Add provenance mapping from Type 1–4 to the underlying CAD variants in `cad/auger-geared/` so the labels are auditable, especially given the documented nozzle-swap incident.
5. If real nozzle-performance data exist, add a small companion panel or table with n, units, and error bars; if not, keep the claim purely geometric and remove any implication that Fig. S1 itself compares performance.
6. If space allows, pair the CAD renders with one printed photo or microscope image from the printed set to show fabrication fidelity.

- Discretionary analytical decisions made during the analysis
- Treated the task as a figure-specific peer review, not a full manuscript review, because the user explicitly narrowed scope to `figS1_nozzles`.
- Prioritized primary evidence from `si.pdf`, `main.pdf`, `caption_figS1_nozzles.md`, `make_figures.py`, `pr97_comments.md`, and `all_branches_file_tree.txt` over inference from file names alone.
- Used the branch tree to name potentially relevant source files without claiming their contents when those files were not present in the local bundle.
- Evaluated “necessity, legibility, and sufficiency” against


### provenance

Prioritized action list for figS1_nozzles
1. **Cite the four SCAD sources directly in the SI Fig. S1 caption or in §S3** as the authoritative geometry, e.g. "Geometries defined by `cad/auger-geared/archimedes-auger-test-nozzle{1..4}.scad` on branch `copilot/add-new-auger-design`."
2. **Archive a deterministic build recipe**: commit the OpenSCAD render command (or expose it in `edison_run_nozzles.py`'s docstring) that maps each `.scad` → `…-cross-section.png`, and add a copy/rename step to `make_figures.py` (or a `Makefile`) so the path from `.scad` → `figS1_nozzles.pdf` is fully scripted.
3. **Add a Zenodo/figshare archive entry** (or git tag) pinning the four `.scad` + `.stl` + cross-section PNGs at the manuscript revision; reference its DOI in the SI.
4. **Either reword the caption** ("Cross-sections of CAD designs for the four exit-nozzle variants…") or **inset a photograph** from `docs/assets/printed/nozzle-augers-issue48-printed-set.jpg` (`origin/copilot/record-of-designs`) so the word "printed" is substantiated by the figure itself.
5. **Solicit review of S1 specifically** — PR97 reviewers (human + bot) did not comment on it; given the SI claims the four geometries drive a forthcoming dispense campaign, the variant rationale in `cad/auger-geared/edison_artifacts/nozzle-selection.answer.md` should be sanity-checked.

### Discretionary decisions
- Used PyMuPDF (`pymupdf`) at 200 dpi for the supplied-vs-regenerated PDF raster diff. A different dpi or renderer (Cairo/Poppler) would give numerically different but qualitatively equivalent diff statistics.
- Treated "frac di


### improvement

Prioritized action list for Figure S1

1. Rebuild Figure S1 as overview row + enlarged outlet-detail row using the existing four PNG assets.
2. Add arrowed annotations for “exit constriction” and “chamfer” in the detail panels.
3. State explicitly in the caption that all panels are at the same scale.
4. If available from `nozzle-variants.scad` and the four nozzle `.scad` files, add outlet dimensions/chamfer annotations.
5. Optionally add a small printed-part photo inset from `docs/assets/printed/nozzle-augers-issue48-printed-set.jpg` if it cleanly maps to the four types.
6. Do not add performance claims unless you have real bench data; if such data now exist, a tiny outcomes panel would be the highest-value scientific addition.

- Used the supplied PNG cross-sections as the primary visual evidence for what differentiates the four variants, because the branch tree showed likely CAD sources but not their contents in this bundle.
- Prioritized a crop-and-annotate redesign over requesting new renders, because the existing assets appear sufficient for a substantially better comparison figure.
- Recommended qualitative geometry descriptors unless exact dimensions can be recovered from the `.scad` files, to avoid inventing numeric parameters.
- Treated performance-data additions as optional and contingent on real bench data, because `si.pdf` states those results are planned rather than reported.
- Suggested a printed-part photo inset only as an option, since the branch tree confirms the file exists but its content/quality was not directly inspected here.


### signposting

Prioritized action list for figS1_nozzles

1. **Replace the caption** with the version above so HUMAN-decided / AI-modelled / HUMAN-reviewed-printed-tested is explicit, per @swcharles `main.tex:189` and @sgbaird `main.tex:189`. *(highest priority — directly addresses the open PR comment.)*
2. **Add panel letters (a)–(d)** to the four renders in `make_figures.py:figs1()` using the existing `panel_label()` helper (already used in `fig1`/`fig2`); the caption above already refers to them.
3. **Add dimensioned annotations** to at least the exit-orifice diameter and chamfer angle for each variant — these are the parameters the caption claims distinguish the four, and @swcharles `main.tex:193` explicitly calls for dimensioned drawings as part of the AI-vs-human story. Source the numbers from `archimedes-auger-test-nozzle{1..4}.scad` and `nozzle-variants.scad` rather than re-deriving.
4. **Add a scale bar** (millimetres). The figure currently gives a reader no way to judge size; the auger tube OD is stated as 25 mm in main.pdf §3.1, so a 5 mm bar is appropriate.
5. **Cross-link to the "silently swapped" anecdote.** The caption above does this in prose; alternatively, add a one-line footnote on the figure: *"Variant labelling verified against SCAD source after a documented swap error; see §2.3."* This is the single most concrete human-review datum tied to this exact figure.
6. **Cite the branch/file provenance in the caption** (as above) so a reader can audit who-did-what without hunting through the design log — this matches the SI §S4 promise that *"all AI interactions are preserve


### narrative

Prioritised action list

1. **Rewrite caption** to specify what varies between Types 1–4 with values from the SCAD sources (`cad/auger-geared/archimedes-auger-test-nozzle*.scad`). Highest impact, lowest cost.
2. **Crop panels to the tip region** and add geometric annotations; keep one small full-auger inset for orientation. Removes the Fig. 2a redundancy.
3. **Connect to §2.3.0.2 silent-swap anecdote** by naming the swapped pair in the SI text and/or panel labels.
4. **Add forward-pointer sentence in SI §S3** stating that the comparative dispensing data are deferred to the multi-doser follow-up, mirroring the deferral language already used for the design-log analysis.
5. **Leave figure in SI.** Do not merge, move to main, or cut.

### Discretionary decisions

- Treated Fig. S1's primary role as "document variants for future campaign" based on the SI §S3 future-tense wording; an equally defensible reading is "support the §2.3 sentence on exit-nozzle effects," and the recommendation would be similar under either reading.
- Judged the four panels as substantially redundant with Fig. 2a based on visual inspection of the supplied PNGs (≈75–80 % of pixel area is non-differentiating flighting). A reviewer with a stricter redundancy bar might recommend merging S1 into a single multi-tip composite panel; a more lenient bar might leave it alone.
- Assumed the §2.3.0.2 "four miniature test nozzles" anecdote refers to the same four variants based on file-naming (`archimedes-auger-test-nozzle{1..4}`) and the `edison_run_nozzles.py` script on the branch; this is not stated explicitly in 

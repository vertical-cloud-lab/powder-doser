Figure 5 does not yet earn its place in a Digital Discovery Full Paper in its current form. It is understandable as a brief future-work placeholder, but it is not yet necessary, legible, or sufficient as a figure-level piece of evidence.

Why I say that, grounded in the supplied files:

- The manuscript makes only one substantive Figure 5 claim in the main text: “Ongoing work extends the platform to (1) a multi-powder doser arraying N printed channels around a shared collection cup (Fig. 5)…” and says this future work “will be reported separately” (`main.pdf`, p. 7). That means the figure is not supporting current experimental results; it is supporting a roadmap claim.
- The caption is minimal: “Future work: multi-powder doser. (a) N-channel radial array concept around a shared collection cup on a single balance. (b) CAD study of inward-tilting channels over the shared cup.” (`caption_fig5_future.md`; same text in `main.pdf`, p. 7).
- The source confirms panel (a) is a schematic and panel (b) is just a rendered CAD asset, not a tested device or measured result (`make_figures.py`, lines 364–403). No synthetic data are shown here, so there is no synthetic-data overclaim in the narrow sense. But the figure can still overstate maturity if readers infer build status or feasibility beyond what is shown.
- PR review already flags that “The future work has changed a bit… This section and its figures will be changed as updated information is uploaded.” (`pr97_comments.md`, lines 73–76). So even internal review treats this figure as provisional.
- The branch tree shows the likely source branch for panel (b) is `origin/copilot/brainstorming-design-possibilities`, with files under `design/cad/inward-collection-cup/`, including `README.md`, `cad_model.py`, `inward_collection_cup.step`, `inward_collection_cup_iso.png`, `inward_collection_cup_top.png`, and `sketch_2d.py` (`all_branches_file_tree.txt`). That is useful provenance, but it also reinforces that this is design exploration, not demonstrated hardware.

Numbered major comments

1. The figure is not yet strong enough to justify a full manuscript figure unless the paper truly needs a future-work visual.
- The main text gives Figure 5 only one short forward-looking sentence (`main.pdf`, p. 7). That is weak figure-to-text integration.
- Because the paper is about a single-channel printed auger doser, Figure 5 currently reads as a speculative appendix-like teaser rather than a core figure.
- Action: either remove Figure 5 from the main paper and keep the future-work statement in text, or upgrade Figure 5 into a genuinely informative design figure with dimensions, architecture labels, and explicit constraints.

2. Panel (a) is too abstract to carry technical meaning.
- In `make_figures.py`, panel (a) is generated as eight identical unlabeled rectangles around a circle labeled “shared cup” (lines 368–395). There are no arrows, no dispense directions, no actuators, no balance, no cartridge/seal elements, and no indication of what “N-channel” means mechanically.
- The caption adds “on a single balance,” but the balance is not shown in the panel or labeled in the figure (`caption_fig5_future.md`).
- Action: redraw panel (a) as a real system architecture schematic. At minimum label one channel module, the shared collection cup, the balance pan, dispense axes, inward tilt angle, and whether the channels are fixed or move during operation.

3. Panel (b) is not legible enough for publication as evidence.
- The asset used is `assets/inward_collection_cup_iso.png`, imported directly by `show(ax, "inward_collection_cup_iso.png")` in `make_figures.py` line 398.
- Visually, panel (b) is a thin wireframe with hidden/internal geometry visible, minimal contrast, and no callouts. The central cup and the individual channels are difficult to parse at journal-column scale.
- The CAD panel looks exploratory, not presentation-grade. It does not show the key design point clearly: why inward tilt solves collection into one cup.
- Action: replace the wireframe with a shaded render or an annotated orthographic/top view plus one perspective inset. Suppress hidden lines unless they are essential.

4. There is an apparent geometry mismatch between panels (a) and (b).
- Panel (a) explicitly depicts an 8-channel radial ring (`make_figures.py`, line 373 sets `n = 8`).
- Panel (b) does not read as the same architecture. It appears to show a multi-rank inward fan rather than a simple planar 8-position ring. At figure scale, the visible channel count is not obvious, and it does not visually map onto panel (a).
- Action: make the channel count consistent across panels, or explicitly state that panel (b) is a partial CAD study rather than the exact realization of panel (a). If panel (b) is a 5-, 8-, 10-, or N-channel variant, say so in the caption.

5. The caption overclaims conceptual completeness relative to what the panels show.
- “N-channel radial array concept around a shared collection cup on a single balance” implies a system-level architecture, but panel (a) does not show the balance and panel (b) does not show gravimetric integration.
- “CAD study of inward-tilting channels over the shared cup” is fairer, but still incomplete because the image does not indicate dimensions, tilt angle, nozzle spacing, vertical clearance, cup diameter, or whether collision/interference has been checked.
- Action: tighten the caption to make the status explicit. For example: “Conceptual schematic” and “exploratory CAD render” would be more honest than language implying a settled design.

6. Key feasibility information is missing.
For a Digital Discovery audience spanning self-driving labs and powder metrology, the missing information is not cosmetic. It is what makes the design credible.
Missing from the figure/caption:
- channel count used in the CAD study
- cup diameter
- nozzle-to-cup radial offset
- tilt angle(s)
- height from nozzle exit to collection plane
- center-to-center spacing between channels
- footprint on the balance pan
- whether one active channel can dose while adjacent channels remain loaded without spill/cross-contamination
- whether the shared-balance concept tolerates vibration/actuation from neighboring channels
- Action: add at least a dimensioned top view or side section with units in mm.

7. The figure omits the exact risks readers will care about most.
- The manuscript text does not discuss crosstalk, contamination, or gravimetric interference for the shared-cup architecture; I found no explicit discussion of these in `main.pdf`. The only contamination-related wording in the manuscript is elsewhere, about “cross-contamination-free disposable wetted parts” (`main.pdf`, p. 6), not about Figure 5’s shared-cup geometry.
- For this figure, those are the critical design questions. Without at least a schematic treatment, the concept remains under-argued.
- Action: add a panel or annotations showing the intended mitigation of cross-talk/spillage. Even one annotated top view with powder trajectories or keep-out zones would help.

8. The figure does not distinguish demonstrated hardware from future concept strongly enough.
- The manuscript needs careful HUMAN vs AI attribution and careful status marking (`pr97_comments.md`, lines 22–36, 67–71). Figure 5 itself does not say whether either panel comes from human-defined architecture, AI-authored CAD code, Zoo Design Studio exploration, or mixed workflow.
- Since this paper is partly about generative CAD, that provenance matters.
- Action: in the caption, state that this is future-work concept CAD produced by programmatic CAD workflows, and if relevant note whether late exploratory Zoo Design Studio work informed it. Do not imply a GUI CAD workflow; the project notes explicitly say none was used (`pr97_comments.md`, lines 128–130).

Numbered minor comments

1. Add a scale bar or, better, explicit dimensions in mm.
- Scale bars are less ideal for CAD than direct dimensions. For this figure, dimensions are better.

2. Add units everywhere dimensions are introduced.
- The current figure has none.

3. Label the balance explicitly if the caption claims “on a single balance.”
- Right now the balance is absent from the visual logic of panel (a).

4. Add arrows indicating powder flow direction.
- Especially in panel (b), the inward-tilt idea is not self-evident at first glance.

5. Use consistent terminology across caption and manuscript.
- The text says “shared collection cup” (`main.pdf`, p. 7), while the graphic says “shared cup.” Use one phrase consistently.

6. Increase line weight and contrast in panel (b).
- At reduced size, the wireframe becomes faint and ambiguous.

7. Consider replacing panel (b) with a top view plus one sectional side view.
- The branch tree suggests relevant companion assets may exist or be derivable from `design/cad/inward-collection-cup/inward_collection_cup_top.png` and `design/cad/inward-collection-cup/sketch_top_side.png` in `origin/copilot/brainstorming-design-possibilities` (`all_branches_file_tree.txt`). Those would likely explain the geometry better than the current perspective wireframe.

8. State design status in the caption.
- For example: “exploratory CAD study; not yet experimentally validated.”
- That would align with the manuscript’s own wording that future work “will be reported separately” (`main.pdf`, p. 7).

9. If retained, connect Figure 5 more explicitly to the modular single-channel design.
- The Introduction says each channel is an independent printable unit that will later be arrayed around a shared collection cup (`main.pdf`, p. 2). The figure should visually show that continuity, perhaps by rendering one recognizable single-channel module and then the array.

10. Clarify whether cartridges/seals are part of this concept figure.
- The conclusion mentions “swappable sealed cartridges” (`main.pdf`, p. 7). Nothing in Figure 5 indicates that.
- If that claim remains in the text, either show it here or avoid implying Figure 5 covers it.

On overclaiming and synthetic data

- I see no synthetic data in Figure 5. The synthetic-data watermark logic in `make_figures.py` is used for Figure 3 only, not Figure 5 (compare lines 304, 322, 334 versus the Figure 5 code at lines 364–403).
- So I would not criticize Figure 5 for synthetic data.
- I would criticize it for maturity signaling: it can be read as more developed than the evidence shown. The safe wording is that it is a concept plus exploratory CAD study, not a validated multi-powder platform.

Necessity, legibility, sufficiency

- Necessary? Not yet. The paper can stand without it because the future-work claim is brief and non-essential.
- Legible? Marginal. Panel (a) is readable but too generic; panel (b) is hard to interpret at publication size.
- Sufficient? No. It lacks dimensions, labels, design constraints, and any evidence that the proposed architecture addresses spillage, collision, or measurement interference.

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
- Flagged the panel-count/geometry mismatch conservatively as an “apparent” inconsistency rather than asserting an exact channel count for panel (b), since only the rendered image and not the underlying CAD model source were available in the bundle.
- Evaluated “necessity” against the manuscript’s level of Figure 5 integration in the text, especially the single substantive reference on page 7 and the statement that future work will be reported separately.
- Treated branch-tree paths such as `design/cad/inward-collection-cup/inward_collection_cup_top.png` and `sketch_top_side.png` as likely relevant candidate files, naming them explicitly but not claiming their contents beyond what filenames support.
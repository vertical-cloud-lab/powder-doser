Figure 2 is trying to do the right job, but right now it asks the reader to decode two different stories at once: (i) why whole-assembly / under-specified AI CAD failed, and (ii) how part-by-part / corrected-input workflows recovered. The current 2×4 grid in `make_figures.py` (`fig2()`, lines 233–274) gives each panel equal weight, but the visual hierarchy does not match the manuscript’s claim in `main.pdf` Fig. 3 and the caption in `caption_fig2_genai.md`. The result is that the key takeaways are there, but they’re buried.

The strongest redesign is to make the figure read as a comparison of failure modes versus recovery, not as eight equally important thumbnails.

Priority 1: Reorder the panels into a narrative layout
- The current order in `make_figures.py` is `(a,b,c,d)` = tap collar v1, tap collar final, auger assembly, whole-assembly attempt; `(e–h)` = mounting-plate iterations. That interleaves “bad”, “good”, “good”, “bad” across the top row, then a separate iteration sequence below. It forces the reader to keep switching mental frames.
- I’d redesign it as two rows with explicit logic:
  - Top row: failure cases
    - (a) `assets/tap_collar_v1_iso.png`
    - (b) `assets/single_channel_module_iso.png`
    - (c) `assets/plate_iter1_hole_top.png`
    - (d) `assets/plate_iter3_gap_top.png`
  - Bottom row: recovered / workable outcomes
    - (e) `assets/tap_collar_final_iso.png`
    - (f) `assets/auger_assembly_iso.png`
    - (g) `assets/plate_iter4_final_top.png`
    - (h) compact summary panel, not another render
- Why this works: it matches the manuscript text in `main.pdf` p. 5, Fig. 3 caption and p. 4–6 section 2.3: whole-assembly fails; part-by-part with explicit interfaces succeeds; stale upstream files caused one of the mounting-plate detours; Zoo rescued the tap collar late.
- I made a concrete mockup of this layout here: `data_entry:fig2-proposed-redesign-pdf-rrzh`

Priority 2: Replace the current panel (h) with a summary panel
- Right now the bottom row uses four mounting-plate renders `(e–h)`. That is too much repetition for a main-text figure.
- The weakest use of space is showing all four plate iterations at equal size. The figure only needs enough of that sequence to prove the failure mode and the recovery.
- Keep three plate states, not four:
  - unexplained hole: `assets/plate_iter1_hole_top.png`
  - stale-input failure state with floating plate: `assets/plate_iter3_gap_top.png`
  - corrected-input clean state: `assets/plate_iter4_final_top.png`
- Drop `assets/plate_iter2_platforms_iso.png` from the main figure unless you can re-render the full series at the same viewpoint. In the current figure, panel (f) is an isometric view while (e), (g), and (h) are orthographic views. That breaks visual comparability. I verified this from the supplied assets and from `make_figures.py` lines 257–267, where iter2 is literally `plate_iter2_platforms_iso.png` while the others are `*_top.png`.
- Use the freed slot for a compact text/table panel summarizing the workflow claim already made in `main.pdf` pp. 5–6:
  - whole-assembly prompt → visually plausible, mechanically incoherent
  - part-by-part + explicit interfaces → converged
  - stale upstream files supplied by HUMAN → agent designed around them silently
  - final tap collar → AI modelling in Zoo Design Studio, three chat-driven iterations with Zookeeper
- This summary panel would do more work for a Digital Discovery reader than a fourth near-duplicate plate view.

Priority 3: Add minimal annotations directly on the renders
The current figure depends almost entirely on panel titles and caption. That’s risky because the defects are not all obvious at journal size.

Add 1–3 callouts per panel:
- `tap_collar_v1_iso.png`:
  - arrow to solenoid collision/interference region
  - arrow to missing clearance for mounted components
  - arrow to impossible stack-up / clamp geometry
- `tap_collar_final_iso.png`:
  - arrow to split-clamp ring
  - arrow to the two mounting pads carrying auxiliary actuators
  - label “usable geometry, later productionized in Zoo”
- `single_channel_module_iso.png`:
  - arrow to floating component
  - arrow to suspected interference / unsupported assembly relation
- `plate_iter1_hole_top.png`:
  - circle the unexplained hole under the gear region
- `plate_iter3_gap_top.png`:
  - bracket or shaded band showing the gap that leaves the plate floating
- `plate_iter4_final_top.png`:
  - small “clean interface after fresh upstream files” note at the corrected mating region
- `auger_assembly_iso.png`:
  - one arrow to the large auger gear
  - one arrow to the stepper pinion
  - optional label “successful part-by-part outcome”

These annotations are implementable in `paper/figures/make_figures.py` by adding `ax.annotate(...)` calls, the same way Figure 1 is annotated (`make_figures.py`, lines 133–149). No new data are required.

Priority 4: Fix the viewpoint inconsistency in the plate-iteration story
- The current plate sequence mixes views:
  - `plate_iter1_hole_top.png`
  - `plate_iter2_platforms_iso.png`
  - `plate_iter3_gap_top.png`
  - `plate_iter4_final_top.png`
- Despite the filenames, the “top” images read more like front/planar assembly views, while iter2 is a true isometric perspective. In the compiled figure this makes the sequence look like unrelated images instead of one evolution path.
- Best fix with existing assets: remove iter2 from the main figure.
- Better fix if branch assets can be re-rendered: regenerate all four plate panels from one camera angle using the CAD source from:
  - `origin/copilot/design-mounting-plate/cad/mounting-plate/render_views.py`
  - `origin/copilot/design-mounting-plate-for-powder-doser/cad/mounting-plate-assembly/render_views.py`
  - `origin/copilot/design-mounting-plate-cadsmith/design/cad/mounting-plate-assembly/render_views.py`
- If you want to preserve the full iteration sequence, move it to the SI as a 1×4 strip with matched views.

Priority 5: Make HUMAN vs AI attribution explicit in the caption, not implied
This is required by the review comments in `pr97_comments.md`:
- lines 23–25: “clarify where ai was used”
- lines 27–36 and 128–130: distinguish HUMAN vs AI only, and note no GUI CAD package was used; only programmatic CAD and later Zoo Design Studio / Zookeeper
- lines 38–45: panel (a) needed correction in how the failure was described
- lines 119–121: tap collar redesigned in Zoo Design Studio in three iterations

The caption should therefore say plainly:
- HUMAN supplied specifications, reviewed outputs, and in the plate case accidentally supplied stale upstream files
- AI generated the CAD geometry
- No Fusion 360 / SolidWorks / other GUI CAD workflow was used
- Zoo Design Studio was used late and exploratorily; tap collar reached a usable design there in three iterations

Priority 6: Tighten panel titles; let the caption carry the nuance
The current titles in `make_figures.py` are accurate but too long for the panel size, especially:
- “Tap collar, first AI proposal: interferences, bad tolerancing, no component clearance”
- “Tap collar after review iterations (final part redesigned in Zoo)”
- “Whole-assembly attempt (single prompt, v1 module)”
- “Iter. 3: gap appears; motor plate floats”

Shorter titles would improve legibility:
- (a) `Tap collar v1: unusable`
- (b) `Whole assembly: plausible, but incoherent`
- (c) `Plate iter 1: unexplained hole`
- (d) `Plate iter 3: floating plate`
- (e) `Tap collar: usable after Zoo`
- (f) `Geared auger: part-by-part success`
- (g) `Plate iter 4: clean after fresh inputs`
- (h) `Workflow summary`

Then put the specifics in the caption.

Priority 7: Consider one small connector graphic between “bad” and “good” pairs
This is optional, but if space allows:
- add a thin arrow from (a) to (e): “iterative review → Zoo redesign”
- add a thin arrow from (c)/(d) to (g): “fresh upstream files”
This would make the figure scan faster.

What can be done now with existing assets
Implementable immediately from the supplied bundle:
- Reorder panels in `make_figures.py`
- Remove `plate_iter2_platforms_iso.png` from the main-text figure
- Add direct annotations and colored FAIL/OK badges
- Replace one plate panel with a compact text summary panel
- Tighten panel titles
- Rewrite caption for explicit HUMAN vs AI attribution

What would require new renders or new source retrieval
- A consistent four-panel plate-iteration sequence from the same camera angle would require new renders from branch CAD sources, most likely from:
  - `origin/copilot/design-mounting-plate/cad/mounting-plate/...`
  - `origin/copilot/design-mounting-plate-for-powder-doser/cad/mounting-plate-assembly/...`
  - `origin/copilot/design-mounting-plate-cadsmith/design/cad/mounting-plate-assembly/...`
- A stronger tap-collar before/after comparison would benefit from matched orientation renders from `origin/copilot/design-tap-collar/design/cad/tap-collar/render_views.py`
- A true quantitative mini-summary panel would require extracting iteration counts / acceptance outcomes from the 97-entry design log referenced in `main.pdf` and `pr97_comments.md` (issue #73 / PR #74); that log is not included in this bundle, so I cannot derive numbers here without fabricating them.
- Bench data are not needed for this figure. This is a workflow/provenance figure, not a performance figure.

Suggested tightened caption draft
Figure 2. Generative-AI CAD outcomes: recurrent failure modes and the workflow that recovered workable parts. HUMAN researchers defined the architecture, supplied interface specifications and drawings, reviewed every output, and in the mounting-plate case accidentally supplied stale upstream part files; AI tools generated the CAD geometry. No conventional GUI CAD package was used at any stage; parts were modelled through programmatic CAD, with Zoo Design Studio used late and exploratorily through chat with its Zookeeper agent. (a) First AI-generated tap collar, mechanically unusable: features interfere, tolerances are incorrect, and the geometry provides no clearance for the solenoid and ERM vibration motor the part must carry. (b) Whole-assembly generation from a single prompt produced a visually plausible module but hidden interferences and unsupported component relationships. (c,d) Two mounting-plate failure states during iterative AI modelling: an unexplained hole beneath the gear region (c), and a later geometry gap that left the mating plate effectively floating (d). The latter arose because HUMAN reviewers had supplied stale upstream part files, which the agent silently designed around. (e) Usable tap-collar geometry obtained later in Zoo Design Studio; the tap collar reached a usable design in three Zoo iterations. (f) Geared auger and stepper pinion generated successfully in the part-by-part workflow. (g) Clean mounting-plate geometry after the correct upstream files were supplied. Together, these cases show that single-shot assembly generation was unreliable, whereas part-by-part generation against explicit interfaces was workable under disciplined HUMAN review.

Short prioritized action list for this figure
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
  - Limited claims about iteration counts to those explicitly present in the supplied files, especially the “three iterations” statement for the tap collar in `caption_fig2_genai.md`, `main.pdf`, and `pr97_comments.md`.
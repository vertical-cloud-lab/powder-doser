Figure 5 is too slight for the claim it is carrying. In the manuscript, this figure supports the sentence: “Ongoing work extends the platform to (1) a multi-powder doser arraying N printed channels around a shared collection cup (Fig. 5), with a loaded subset of 8–12 powders and a path to a 50-powder pool via swappable sealed cartridges …” (main.pdf, p. 7). But the current figure shows only a generic 8-block cartoon in panel (a) and a lightly rendered CAD view in panel (b), while the current caption is only two short sentences (caption_fig5_future.md). That mismatch makes the figure read as underdeveloped relative to the manuscript’s specific future-work claims.

A concrete redesign should do two things:
1. make the geometry legible enough for a hardware audience
2. separate what already exists as CAD from what is still only a system concept

I’d redesign Figure 5 as a 3-panel figure at minimum, and 4 panels if you want it to carry the full paragraph in Conclusions.

Highest-priority redesign

1. Replace the current panel (a) with an engineering-style top view, not a generic icon ring.

Current problem:
- In make_figures.py, fig5() panel (a) is just eight identical rotated rectangles around a circle labeled “shared cup” (`make_figures.py`, lines 368–395).
- The title says “N-channel radial array (concept)”, but the panel does not show the two things a reader needs: where material exits, and what geometric variable is being proposed.

Specific change:
- Keep the top-view concept, but redraw it as a top-view geometry panel with:
  - central shared cup
  - circular pitch radius for channel placement
  - channel centerlines pointing toward the cup
  - one wedge annotation labeled `360°/N`
  - one radius annotation labeled `R_pitch`
  - one note that “shown: N = 8; manuscript text proposes 8–12 loaded channels”
- Use circles or tube-end footprints rather than rectangles if possible. The present rectangles imply arbitrary blocks, not dosing channels.
- Add a dashed envelope circle to indicate overall footprint.

Why this matters:
- The manuscript states the single-channel module “will later be arrayed around a shared collection cup” (main.pdf, p. 2). The current panel does not really show an arrayable hardware geometry; it shows a symbolic arrangement.
- A top-tier hardware paper needs one panel that reads as a design drawing, even if still conceptual.

Implementability:
- Can be done now in matplotlib only, by editing the existing fig5() code in `make_figures.py`.
- No new CAD render required.

2. Keep the current CAD render as a separate panel, but annotate it aggressively.

Current problem:
- Panel (b) is the strongest existing asset: `assets/inward_collection_cup_iso.png`.
- But in the compiled figure it is pale, unlabeled, and visually ambiguous. Without annotation, a reader has to infer what is being shown.
- The title “Inward-tilting channels over shared cup (CAD)” is accurate but too generic.

Specific change:
- Keep `assets/inward_collection_cup_iso.png` as the core image.
- Add 3–5 callouts directly on the render:
  - “inward-tilting channel” or “auger tube axis”
  - “common dispense region” or “shared dispense point”
  - “shared collection cup”
  - “balance pan / cup fixture plane” if that base square is intended as the weighing interface
  - optionally “independent printable unit replicated around cup”
- Add one explicit overlay for tilt geometry, e.g. a small arc or angle annotation labeled `α`.
- Increase line/label contrast. Right now the render is too washed out for reduction.
- Crop tighter. The current render spends a lot of area on empty baseplate and whitespace.

Grounding:
- The asset exists locally as `assets/inward_collection_cup_iso.png` and in the branch tree as `design/cad/inward-collection-cup/inward_collection_cup_iso.png` on `origin/copilot/brainstorming-design-possibilities`.
- The branch tree also names likely better supporting views that are not in this bundle but should be considered if you reopen that branch:
  - `design/cad/inward-collection-cup/inward_collection_cup_top.png`
  - `design/cad/inward-collection-cup/inward_collection_cup_top.svg`
  - `design/cad/inward-collection-cup/sketch_top_side.png`
  - `design/cad/inward-collection-cup/README.md`
  - `design/cad/inward-collection-cup/cad_model.py`

Implementability:
- Annotation and crop can be done now with the existing asset.
- A top-view CAD companion would require pulling `inward_collection_cup_top.png` or regenerating a render from `cad_model.py` on that branch.

3. Add a panel that explains the weighing logic of a shared cup.

Current problem:
- The phrase “shared collection cup on a single balance” appears both in the manuscript and the caption (main.pdf, p. 7; caption_fig5_future.md), but the figure never explains the control consequence of that choice.
- For a hardware reader, the central system question is not just geometry; it is how one balance services N channels.

Specific change:
- Add a small schematic panel showing sequential dosing onto one cup:
  - channel 1 doses to setpoint
  - balance reads cumulative mass
  - tare or accounting step
  - channel 2 doses
  - repeat
- A simple staircase or state-diagram panel is enough.
- Label it clearly as “control concept” or “schematic, not bench data.”

Why this matters:
- It turns the figure from “here is a shape” into “here is the proposed instrument architecture.”
- That is a much better fit for a hardware Full Paper.

Implementability:
- Can be done now as vector artwork in matplotlib.
- No new render or data required.

4. Only add a cartridge-scaling panel if you want Figure 5 to support the full future-work paragraph.

Current problem:
- The manuscript text claims “a loaded subset of 8–12 powders and a path to a 50-powder pool via swappable sealed cartridges” (main.pdf, p. 7), but Figure 5 currently shows nothing about cartridges.
- That makes the paragraph overpromise relative to the figure.

Specific change:
- If you keep this claim in the text, add a small roadmap/system panel: 
  - Stage 1: N = 1 single-channel module
  - Stage 2: N = 8–12 loaded channels around shared cup
  - Stage 3: 50-powder pool via swappable sealed cartridges
- This should be a roadmap or architecture box, not fake CAD.
- Do not imply a finalized cartridge mechanism unless you have an actual design artifact.

Grounding:
- The branch tree points to one related artifact: `design/cad/single-channel-module/stl/cartridge.stl` on `origin/copilot/modular-single-channel-powder-doser-design`.
- It also points to `paper/background/15-zoo-design-studio-multi-doser.md` on `origin/copilot/zoo-design-studio-multi-doser`.
- I do not have those files in this bundle, so I cannot verify whether they contain cartridge geometry suitable for a figure.

Implementability:
- A roadmap box can be done now.
- Any actual cartridge render would require pulling files from those branches or making new CAD.

What to remove or de-emphasize

- Remove the current generic rectangle-ring aesthetic in panel (a). It looks like a placeholder, not a figure for a final paper.
- De-emphasize the words “concept” and “CAD” in titles. Use those terms once in the caption instead. Panel titles should tell the reader what they are learning.
- Remove redundant empty whitespace around panel (b).
- Do not add simulated powder trajectories or fake performance overlays. There are no supporting data in this bundle, and the manuscript’s figure-generation script explicitly warns against synthetic data elsewhere (`make_figures.py`, lines 4–8, 66–81).

Recommended final layout

Best option: 4 panels across two conceptual levels
- (a) Top-view array geometry
- (b) Annotated CAD render of inward-tilting channels over shared cup
- (c) Shared-balance arbitration / dosing sequence schematic
- (d) Scaling roadmap from 8–12 loaded channels to cartridge-based larger pool

If space is tight, use a 3-panel version
- Left: (a) top-view geometry
- Middle: (b) annotated CAD render
- Right: (c) shared-balance arbitration

I would not keep this as the current single-column 2-panel figure unless you are forced by layout. In `make_figures.py`, Fig. 5 is currently built at `figsize=(SINGLE_COL_IN, 2.2)` (`make_figures.py`, line 365), which is only about 8.3 cm × 5.6 cm. That is too cramped for a future-architecture figure with real explanatory value. This should become a double-column figure if the journal layout allows it.

Specific caption rewrite

Current caption:
- “Future work: multi-powder doser. (a) $N$-channel radial array concept around a shared collection cup on a single balance. (b) CAD study of inward-tilting channels over the shared cup.” (`caption_fig5_future.md`)

Problems with current caption:
- too short
- does not distinguish existing CAD from architecture-level concept
- does not connect to the manuscript’s specific claims about 8–12 loaded channels and a 50-powder path
- does not explain why inward tilt matters

Proposed tightened caption draft

Figure 5. Proposed architecture for a future multi-powder doser built by replicating the single-channel module around one gravimetric collection point. (a) Top-view layout of an N-channel radial array centered on a shared collection cup; the key geometric variables are the channel pitch radius and angular spacing (360°/N). The configuration shown is illustrative (N = 8), consistent with the manuscript’s planned 8–12 loaded channels. (b) Programmatic-CAD study of inward-tilting channels converging on a common dispense region above the shared cup, which would sit on a single analytical balance. (c) Schematic of the proposed shared-balance dosing logic, in which channels are actuated sequentially against one gravimetric readout. (d) Scaling concept from a loaded 8–12-channel array to a larger powder pool via swappable sealed cartridges. Panels (a), (c), and (d) are architecture schematics; panel (b) is based on existing CAD assets in the repository.

If you stay with only two panels, then use this shorter caption:

Figure 5. Proposed multi-powder doser architecture. (a) Top-view schematic of an N-channel radial array centered on a shared collection cup on a single analytical balance; the geometry shown is illustrative (N = 8) and represents the planned 8–12 loaded-channel format described in the text. (b) Programmatic-CAD study of inward-tilting channels converging on a common dispense region above the shared cup. Panel (a) is a system-level concept; panel (b) is derived from existing repository CAD.

Attribution and provenance language

Given the review comments, the figure or caption should be explicit about provenance where relevant. The PR snapshot says the manuscript should “always be clear who did what” and should distinguish HUMAN vs AI contributions, while also emphasizing that “No GUI CAD (Fusion 360 / SolidWorks) was used at any point; only programmatic CAD (LLM coding agents authoring parametric CAD code) and, late and exploratorily, Zoo Design Studio (chat-driven, with its Zookeeper agent)” (`pr97_comments.md`, lines 22–36 and 128–130).

For this figure, the safest wording is:
- panel (b) is based on existing programmatic CAD assets in the repository
- panels (a), (c), and optionally (d) are manuscript schematics synthesizing the proposed architecture

I would not put a HUMAN/AI attribution directly in the caption unless the journal style tolerates it, but the caption should avoid implying a conventional GUI-CAD workflow.

What requires new renders or new data

Can be done now with existing assets
- redraw panel (a) as a better top-view schematic
- annotate and crop panel (b)
- add a shared-balance logic schematic panel
- add a scaling-roadmap panel
- expand the caption to distinguish CAD-backed vs conceptual panels

Would require pulling additional existing branch artifacts
- a cleaner top-view CAD companion from `design/cad/inward-collection-cup/inward_collection_cup_top.png` or `.svg`
- a top+side explanatory view from `design/cad/inward-collection-cup/sketch_top_side.png`
- any documentation in `design/cad/inward-collection-cup/README.md` or `cad_model.py`
- any multi-doser narrative from `paper/background/15-zoo-design-studio-multi-doser.md`

Would require genuinely new work
- any panel showing real cartridge hardware for the “50-powder pool” claim, unless suitable branch assets exist and are verified
- any bench data on dosing throughput, cross-contamination, or timing for the shared-cup architecture
- any claim about actual multi-channel performance

One concrete mockup

I prepared a quick mockup showing that a 4-panel redesign is implementable with the current bundle plus matplotlib schematics:
`data_entry:fig5-future-proposed-mockup-png-htes`

Treat that as a layout sketch, not a finished figure.

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
- Did not recommend any performance plots or powder-flow simulations because the bundle contains no multi-channel bench data, and the figure-generation script explicitly distinguishes placeholder synthetic content elsewhere.
The current Figure 1 is trying to do three jobs at once: hero image, mechanism explanation, and project meta-story. Right now it underserves all three. The biggest problem is not style, it is internal inconsistency across panels and caption.

1. **What needs fixing first**

- **Panel (b) should not stay as-is.** The supplied asset `assets/single_channel_module_powder_flow.png` is explicitly an early v2 cross-section with a separate top reservoir/hopper, and even the current caption admits that “in the final design the auger tube itself is the powder reservoir, with no separate hopper” (`caption_fig1_overview.md`, lines 3–3). That mismatch is also flagged in the review snapshot: “We haven't talked about or implemented a removeable hopper. We won't have one on the end design, just the full auger” (`pr97_comments.md`, lines 16–20). The figure currently asks the reader to look at a final-looking platform in (a) and then understand flow through an obsolete geometry in (b). Bad trade.
- **Panel (a) overclaims what is visible.** The caption says panel (a) shows “tap collar with solenoid and vibration motor, and servo-tilted hinged mounting plate” (`caption_fig1_overview.md`, line 3), but in `assets/assembly_iso_final.png` the visible, clearly identifiable parts are the auger tube, bracket/collar region, gear pair/stepper region, mounting plate, and baseplate. The solenoid, vibration motor, and servo are not clearly shown. So either the render must change or the caption/callouts must stop claiming they are visible.
- **The drive description is inconsistent.** The panel (a) callout in `make_figures.py` is `"NEMA-11 stepper\n+ GT2/gear drive"` (lines 136 and 145–149), while the manuscript body describes a “gear train (printed spur pair, 2.25:1)” in the full-system description (main PDF text extracted from `main.pdf`, p5). Panel (b) also contains internal text referring to “NEMA 11 + GT2 belt.” Pick one. Based on the manuscript, it should be **spur gear drive**, not GT2/belt.
- **Panel (b) leaks dev-only text into the paper.** The asset contains “address of PR review #3228854193” and labels like “PR-#16 v4 cap” in the image itself (`assets/single_channel_module_powder_flow.png`). Those are repository breadcrumbs, not publication annotations.
- **Panel (b) also mislabels sensing and system staging.** It refers to a “shared collection cup (load cell — v1.2),” but the review record says the final sensing is “A&D HR-100A analytical balance (0.1 mg) over RS-232 via MAX3232 — NOT an HX711 load cell” (`pr97_comments.md`, lines 124–127). “Shared collection cup” also belongs to the future multi-channel concept, not the single-channel Figure 1; the manuscript uses the shared-cup idea for later arraying and Figure 5, not the current single-channel platform (`main.pdf`, p1 and p6 text).
- **The figure is too short for five panels.** `make_figures.py` sets `figsize=(DOUBLE_COL_IN, 4.6)` for Figure 1 (line 123). With the present 2×3 grid (line 124), panels (c)–(e) end up tiny, especially after journal scaling.

2. **Recommended redesign: a specific panel layout**

I’d keep this as a 5-panel figure only if you tighten the story and make one panel much smaller. The best implementable redesign with current assets is:

### Recommended layout
**Top row:**
- **(a) Hero system view, large, left ~2/3 width**
- **(b) Fixed-dispense-point tilt geometry, right ~1/3 width**

**Bottom row:**
- **(c) Powder-flow path / component-path schematic, left ~1/3 width**
- **(d) Closed-loop gravimetric control concept, middle ~1/3 width**
- **(e) Design timeline, right ~1/3 width, compressed or moved to SI if space is tight**

Why this order? Because the body text actually cites 1c, 1d, and 1e, not 1a or 1b. The tilt geometry and control logic are the distinctive system-level ideas. They deserve more prominence than the obsolete cross-section.

3. **Panel-by-panel redesign**

### (a) Replace current annotated hero shot with a cleaner final-system panel
**Keep:** a large CAD render if no assembled bench photo exists.

**Use existing assets if possible:**
- Current file: `assets/assembly_iso_final.png`
- Candidate branch-tree alternatives worth checking:
  - `design/cad/single-channel-module/renders/single_channel_module_labeled.png` on `origin/copilot/modular-single-channel-powder-doser-design`
  - `design/cad/single-channel-module/renders/single_channel_module_iso.png` on the same branch
  - `design/cad/full-system-direct-drive/renders/full_system_iso.png` on `origin/copilot/explore-meta-tools-for-cad`
  - `cad/meta-tools/zoo-output/renders/full_system_zoo.png` on `origin/copilot/explore-meta-tools-for-cad`

**Redesign details:**
- Strip the current long diagonal callouts down to **4 numbered callouts max**:
  1. auger tube / reservoir
  2. printed spur gear pair + NEMA-11 stepper
  3. tap collar / agitation region
  4. tilting mounting plate about fixed nozzle tip
- Put labels outside the object boundary in one consistent column or as numbered dots with a legend beneath. The present callouts in `make_figures.py` (lines 133–149) sprawl into whitespace and feel provisional.
- Remove the visible placeholder note “CAD render; photograph of the printed platform to be added” (`make_figures.py`, line 150) from the figure itself. Keep that honesty, if needed, in the caption, not as grey italic text embedded in the art.
- Add **one scale bar** or one dimension anchor if available from CAD. No new bench data needed; this can come from the model.

**If a new render is allowed:**
- Generate a slightly higher-angle iso that clearly exposes the agitation/collar region and hinge geometry.
- If possible, render the actual final configuration with visible servo/solenoid/motor; otherwise stop naming those parts as visible.

**What this requires:**
- **Existing assets only:** possible, but caption must be corrected to match what is visible.
- **New render needed:** if you want the figure to actually show solenoid, vibration motor, and servo explicitly.

### (b) Promote the tilt-sweep panel and simplify it
Current asset: `assets/rotation_0_45_90.png`

This is one of the strongest panels conceptually, but its embedded title is doing too much. The source in `make_figures.py` trims only the top 10% (lines 163–168), leaving a busy scientific-notation title block in the original asset.

**Redesign details:**
- Keep the three-angle progression: 0°, 45°, 90°.
- Crop harder and remove the in-image prose about “hinge axis is X through (Y=125, Z=29.2)” and “axis sits 10 mm forward of baseplate front edge.” Move those facts into the caption.
- Add one compact annotation directly in-panel: **red dot = fixed dispense point**.
- If possible from the existing asset, faintly connect the three red dots with a vertical guide or overlay a statement “dispense point unchanged.”
- Retain axes only if they remain legible at print size. If not, remove ticks and keep just the geometry plus one concise annotation.

**What this requires:**
- **Existing asset likely sufficient** with better cropping and annotation.
- **New render not required** unless the original plot cannot be cleaned without regenerating it.

### (c) Replace the current obsolete cross-section with either a corrected final cross-section or a simplified flow-path schematic
Current asset: `assets/single_channel_module_powder_flow.png`

I would not keep the current version in a main-text figure. It is too obviously a repository-internal work product.

**Best option:** replace with a **new final-design cross-section** showing:
- powder loaded through slots in the auger tube wall
- auger tube acting as reservoir
- helical channel conveying powder
- exit nozzle above collection cup on the balance

This would align with the current caption text and reviewer correction (`caption_fig1_overview.md`; `pr97_comments.md`, lines 16–20, 124–127).

**If you must stay with existing assets:**
- Use the current image only after heavy editing:
  - remove all internal titles
  - remove PR numbers and “v4 cap” language
  - relabel “reservoir” so it does **not** imply a separate hopper in the final design
  - relabel sensing as **analytical balance** rather than load cell
  - relabel the cup as **collection cup**, not shared collection cup
- But honestly, this still leaves you with an obsolete geometry in a flagship overview figure.

**Branch-tree file to inspect for a better base:**
- `design/cad/full-system-direct-drive/renders/full_system_cross_section.png` on `origin/copilot/explore-meta-tools-for-cad`
- Also `design/cad/single-channel-module/renders/single_channel_module_powder_flow.png` and `single_channel_module_labeled.png` on `origin/copilot/modular-single-channel-powder-doser-design`

**What this requires:**
- **Prefer new render.** This is the one panel I’d spend effort regenerating.

### (d) Keep the closed-loop control panel, but make it more specific
Current panel is drawn directly in `make_figures.py`, lines 170–200.

It’s clear enough, but generic.

**Redesign details:**
- Replace “Dose request (target mass)” with **Target mass**
- Replace “Auger + tap + vibration actuation” with **Actuate auger / tap / vibration**
- Replace “Controller (coarse → trickle)” with **Controller: coarse feed → trickle → stop**
- Replace “Balance reading (A&D HR-100A, RS-232)” with **Balance mass reading (HR-100A, RS-232)**
- Add a final arrow from controller back to actuation labeled **update motor/tap command**
- Optionally label the measurement arrow **mass error = target − measured**

This panel should visually echo the hardware in (a), not feel like a generic control textbook box chart.

**What this requires:**
- **Existing code only.** No new data or renders needed.

### (e) Either compress the timeline hard or move it to SI
Current timeline in `make_figures.py`, lines 202–224, is informative for the AI-method story, but it is the weakest use of main-figure real estate.

**If kept in main text:**
- Reduce to **4 milestones max** tied to visible design transitions:
  - Apr 23: human sketch / scoop concept
  - Apr 24: auger selected
  - May 12–15: single-channel module and part-by-part redesign
  - May 19: fixed-dispense-point tilting platform
- Drop “Jun 1 — 97-entry design log.” That is a repository/documentation fact, not a platform design milestone.
- Add small HUMAN / AI tags if the journal will tolerate it, because the review explicitly asks the manuscript to signpost AI versus human contributions (`pr97_comments.md`, lines 22–36). Example: “human sketch”, “AI CAD iteration under human review”, “late exploratory Zoo/Zookeeper use”.

**Better option:**
- Move the timeline to SI and use the freed panel for a **real hardware photo** once available.

**What this requires:**
- **Existing code only** for compression.
- **No bench data needed.**

4. **What to add and what to remove**

### Add
- One explicit notation somewhere in the figure or caption that the system was designed with **programmatic CAD generated by AI coding agents under human review**, not GUI CAD. This is required by the review record (`pr97_comments.md`, lines 27–36 and 128–130).
- One concise annotation in panel (b) or caption that the **dispense point remains fixed during tilt**.
- One accurate sensing label: **A&D HR-100A analytical balance, RS-232**.
- If possible, a small inset or numbered cue indicating the **powder loading slots** in the final geometry.

### Remove
- All PR-number references and branch-internal terms from panel (b): “address of PR review #3228854193”, “PR-#16 v4 cap”.
- “GT2” unless the hardware actually uses a belt drive. The manuscript says spur gear pair.
- “shared collection cup” from Figure 1.
- The visible placeholder note about swapping in a photo later.
- Any claim in panel (a) or caption that parts are visible when they are not.

5. **Caption rewrite: tighter and aligned to the supplied files**

Here is a caption draft that stays inside what the supplied files support and avoids overclaiming visible components:

**Draft caption**

**Fig. 1 Platform overview.** (a) CAD overview of the single-channel powder-doser platform, showing the printed auger tube, printed spur-gear drive coupled to a NEMA-11 stepper, tap-collar region, and servo-tilting mounting plate on the baseplate. The mechanical parts were produced through a programmatic CAD workflow in which AI coding agents generated parametric CAD code and the human team supplied requirements, reviewed outputs, and selected designs; no conventional GUI CAD package was used. (b) Tilt sweep from 0°, 45°, and 90° showing fixed-dispense-point kinematics: the hinge axis passes through the nozzle tip, so the dispense point remains stationary as the module rotates from parked to vertical dispensing. (c) Powder-flow concept for the final single-channel design: powder is loaded through slots into the auger tube, conveyed through the helical channel, and discharged through the exit nozzle into a collection cup on an A&D HR-100A analytical balance. (d) Closed-loop gravimetric dosing concept, in which balance readings are used to transition from coarse feed to trickle feed and stop at the target mass. (e) Compressed design timeline from initial human concept sketch to the final tilting auger platform; the complete 97-entry design log is archived in the repository.

Notes on this draft:
- It removes the unsupported claim that solenoid and vibration motor are visible in panel (a).
- It folds in the required HUMAN vs AI provenance using only the distinctions allowed by the instructions and review comments.
- It removes the obsolete hopper language.
- It uses **analytical balance**, not load cell.

If you regenerate panel (a) to clearly show the solenoid and vibration motor, you can add them back.

6. **What can be implemented now vs what needs new material**

### Implementable now with existing assets/code
- Reorder panel prominence so tilt geometry is more prominent than the obsolete cross-section.
- Clean panel (a) callouts in `make_figures.py` (lines 133–149).
- Remove placeholder note from panel (a) (`make_figures.py`, line 150).
- Tighten panel (d) labels (`make_figures.py`, lines 177–200).
- Compress or remove panel (e) (`make_figures.py`, lines 206–224).
- Rewrite caption for accuracy.
- Change all drive-language to **printed spur gear pair**.

### Requires a new render
- A correct final-design powder-path cross-section for panel (c)/(b replacement).
- A new final-system render if you want visibly identifiable solenoid, vibration motor, and servo in the hero panel.

### Requires new bench imagery or bench data
- Replacing panel (a) with an assembled hardware photograph.
- Any claim about demonstrated operation beyond the conceptual loop already shown in panel (d).

7. **Priority order I’d use**

1. **Replace or regenerate panel (b)** so it matches the final no-hopper design and correct balance terminology.
2. **Fix panel (a) labels/caption** to stop claiming invisible components and to replace “GT2/gear drive” with accurate spur-gear language.
3. **Promote the tilt-sweep panel** and simplify its annotation; this is one of the figure’s strongest ideas.
4. **Compress or move the timeline** to SI unless the editorial angle strongly depends on design-process chronology.
5. **If available, replace the hero render with a real assembled-platform photo**; if not, use the cleanest final render from the branch tree and say plainly that it is a CAD render.

- **Discretionary analytical decisions made during the analysis**
- Prioritized internal consistency over visual novelty, because the supplied review comments identify factual mismatch as the main risk.
- Treated `assets/single_channel_module_powder_flow.png` as unsuitable for a main-text overview panel because its labels and geometry conflict with the final design described in `caption_fig1_overview.md`, `pr97_comments.md`, and `main.pdf`.
- Recommended keeping a five-panel structure only conditionally; otherwise suggested moving the timeline to SI as a valid alternative use of space.
- Interpreted the manuscript body’s description of a “printed spur pair, 2.25:1” as the authoritative drive description when resolving the figure’s “GT2/gear drive” inconsistency.
- Limited provenance language to HUMAN vs AI contributions, per the supplied instructions and review comments, and avoided naming individuals.
- Treated branch-tree file paths as candidate assets only when they were explicitly present in `all_branches_file_tree.txt`, and marked uninspected files as candidates rather than asserting their contents.
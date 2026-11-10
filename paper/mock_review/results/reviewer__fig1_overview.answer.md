Figure 1 is probably necessary, but not in its current form. It does useful work as the manuscript’s first orienting figure because the main text leans on it for the core claims about the platform overview, fixed dispense point, closed-loop dosing, and rapid design evolution (`main.pdf`, p. 2: “parts cost under $200 (Fig. 1)”, “(Fig. 1c)”, “(Fig. 1d)”, “(compressed in Fig. 1e)”). But as drawn, it is not yet sufficient for peer review in Digital Discovery: it mixes final and superseded designs, several panels are too small to read at journal scale, and key hardware details named in the text/caption are absent or ambiguously labeled. The main problem is not raster resolution; it is figure logic, consistency, and legibility.

1. Major comments

1. Replace or clearly quarantine panel (b), because it currently shows a superseded architecture and an inconsistent sensor.
   - The caption explicitly says panel (b) is an “early v2-module render” and that “in the final design the auger tube itself is the powder reservoir, with no separate hopper” (`caption_fig1_overview.md`; same in `main.pdf`, Fig. 1 caption, p. 3).
   - Yet panel (b) visibly labels a separate `reservoir (bulk powder)` feeding `top loading slots`, which contradicts the body text: “There is no separate hopper: powder is loaded directly into the printed Archimedes auger (25 mm OD) through loading slots in the auger tube” (`main.pdf`, p. 2), and again “no separate hopper” (`main.pdf`, p. 6).
   - Worse, panel (b) labels the collection device as `shared collection cup (load cell — v1.2)`, while the manuscript repeatedly states the actual instrument is an `A&D HR-100A analytical balance` read over `RS-232` (`main.pdf`, pp. 2, 6, 7). That is a concrete internal inconsistency, not just stale art.
   - Action: either redraw panel (b) for the final architecture, or mark it much more aggressively as historical/superseded and remove the load-cell wording. In its present state, this panel overclaims fidelity to the current platform.

2. Panel (a) needs an as-built photograph or a side-by-side render/photo panel before publication.
   - The caption states: “CAD render; photograph of the printed platform will replace this render” (`caption_fig1_overview.md`). The panel itself repeats this as a note rendered into the figure (`make_figures.py`, line 150).
   - The body says the parts were in fact printed and tested: “the human team made the design decisions, supplied specifications and drawings, reviewed every output, and printed and tested the parts” (`main.pdf`, p. 2), and later “All printed parts were produced in PLA on a Bambu Lab H2D” (`main.pdf`, p. 6).
   - For a hardware paper in Digital Discovery, a CAD-only hero panel is weak when the manuscript claims a physically built platform. The journal’s hardware editorial stresses replicability and modification, and requires documentation enabling construction by a typical researcher (Soldatov et al., “Guidelines for hardware-focused articles,” Digital Discovery 2024, DOI `10.1039/D4DD90009J`: “comprehensive bill of materials and construction guide” and public design files/code).
   - The branch tree suggests candidate photographs exist and should be checked, especially `origin/copilot/initial-prototyping-mini-excavator/PXL_20260423_231729467.jpg` and the printed-part images in `origin/copilot/record-of-designs/docs/assets/printed/`. If no good full assembly photo exists yet, say so and do not imply otherwise.

3. Add physical scale information to panel (a) and/or panel (b); the figure lacks enough dimensional grounding for a hardware overview.
   - The body gives at least one nominal dimension: the auger is `25 mm OD` (`main.pdf`, pp. 2, 6). Panel (b) includes a `10 mm` scale bar, but panel (a), the main overview render, has no scale cue at all.
   - The manuscript nowhere gives the overall footprint, channel length, auger pitch, nozzle inner diameter, or tilt-stage envelope in this figure, and these are exactly the sorts of quantities a hardware reviewer will look for.
   - Action: minimally add one of the following to panel (a): overall footprint dimensions, auger OD label, or a scale bar. Better: include a compact dimension inset or an orthographic silhouette with L × W × H and nozzle-tip position.

4. Panel (c) supports an important claim but is too compressed to carry it convincingly.
   - The manuscript uses Fig. 1c to support a central geometric claim: “the hinge geometry keeps the exit-nozzle dispense point stationary during tilt (Fig. 1c)” (`main.pdf`, p. 2), and the caption says “the hinge axis passes through the exit-nozzle tip” (`caption_fig1_overview.md`).
   - In the current assembled figure, panel (c) is only about one-third of the bottom row width. It contains three subplots, axes, ticks, units, and a red dispense-point marker, all at very small final size. The source asset is `assets/rotation_0_45_90.png`, inserted into a single 1-column cell (`make_figures.py`, lines 162–168).
   - Action: enlarge panel (c), or strip it down. The reader needs to see the hinge axis, nozzle tip, and the invariance of dispense-point position unambiguously. A cleaner schematic with overlaid trajectories and one explicit statement like “nozzle-tip translation = 0 mm by construction” would do more than three tiny CAD screenshots.
   - If you keep axes, keep the units. If you drop axes, explicitly mark the fixed point and hinge axis.

5. Panel (d) has a control-logic diagram error/ambiguity and should be redrawn.
   - The code draws `Dose request (target mass)` feeding directly into `Auger + tap + vibration actuation`, while the `Controller (coarse → trickle)` sits in a feedback loop from `Balance reading` back to the actuator (`make_figures.py`, lines 177–200).
   - That is not a standard closed-loop control depiction. The target mass should enter the controller or a comparator, not the plant/actuator directly.
   - Since the main text uses panel (d) to support “closed-loop gravimetric dosing” (`main.pdf`, p. 2), the logic should be exact, not approximate.
   - Action: redraw panel (d) as setpoint → controller → actuator/plant → measured mass → feedback, with the A&D HR-100A balance as the sensor. If you want to keep it simple, label the plant as “powder module” and the controller as “coarse/trickle logic using balance feedback.”

6. The figure is overcrowded for its narrative job; panel prioritization should change.
   - Quantitatively, panel (b), the stale v2 cross-section, gets more area than panel (d), even though panel (d) supports an active system-level claim and panel (b) is not even the final design (`make_figures.py`, gridspec lines 123–125, 152–160, 170–201).
   - Panel (e) compresses eight milestones into a narrow column and does not label the four generations that the text says are central: “four distinct generations in six weeks” (`main.pdf`, p. 2).
   - Action: either split this into two figures, or simplify Figure 1 to three panels: (a) as-built/photo+render overview, (b) final powder path cross-section, (c) fixed dispense point or control loop. The timeline can move to SI or to a generative-CAD workflow figure.

2. Minor comments

1. Legibility is below journal-ready standard in multiple panels.
   - `make_figures.py` uses panel-specific font sizes of 5.0, 5.2, 5.5, and 6.0 pt in Figure 1 (`make_figures.py`, fig1 code). After `bbox_inches="tight"`, the actual PDF width is about 390 pt = 5.42 in, smaller than the nominal double-column width encoded in the script. This shrinks a 5.5 pt callout to roughly 4.4 pt at print size, and the 4.5 pt placeholder note to about 3.6 pt.
   - Even without invoking a hard rule, those are not comfortably readable in a two-column chemistry journal.
   - Action: raise all in-panel text to a true final-size minimum, and avoid tight-cropping that rescales the whole composite down.

2. Panel (a) callouts miss important components named in the caption and text.
   - Labeled in panel (a): `Archimedes auger`, `Auger bracket + tap collar`, `NEMA-11 stepper + GT2/gear drive`, `Hinged mounting plate`, `Baseplate` (`make_figures.py`, lines 133–149).
   - Named in the caption/body but not labeled in panel (a): solenoid, ERM vibration motor, exit nozzle, hinge axis, balance/collection cup, and the servo itself as a distinct component (`caption_fig1_overview.md`; `main.pdf`, p. 2).
   - Action: add callouts for at least the solenoid, vibration motor, exit nozzle, and servo, or revise the caption so it does not promise more than the panel shows.

3. Two callouts in panel (a) appear misleading.
   - The `Baseplate` leader line appears to land on a support leg/upright rather than the top plate. The `Hinged mounting plate` callout also points ambiguously into the lower structural region rather than clearly to the tilting plate.
   - This impression is consistent with the hard-coded callout targets in `make_figures.py` (`Baseplate` target `(0.46, 0.72)`; `Hinged mounting plate` target `(0.62, 0.62)`).
   - Action: re-place leader endpoints manually after viewing the final exported PDF, not just the notebook preview.

4. Panel (b) title/caption should explicitly say “historical concept, not final geometry” if retained.
   - Right now the caption says “early v2-module render,” but a fast reader can still take it as the actual powder path of the current device.
   - Action: prepend “Superseded” or “early design only” in the panel title itself, not just the caption.

5. Panel (c) needs a legend or more explicit visual encoding.
   - The red dot appears to mark the dispense point, but that is not stated on-panel.
   - Action: add a legend note like “red dot = fixed nozzle-tip dispense point” and mark the hinge axis.

6. Panel (d) should use consistent terminology with the manuscript.
   - The figure box says `Balance reading (A&D HR-100A, RS-232)`, which is good, but panel (b) says `load cell — v1.2`, which is not good. Terminology should be harmonized across all panels.

7. Panel (e) is informative but under-explained.
   - The text says the project passed through “four distinct generations in six weeks” (`main.pdf`, p. 2), but panel (e) just lists dates and milestones. It does not map these to Gen 1–4.
   - Action: if panel (e) stays in the main figure, visually group milestones by generation or label them. Otherwise it reads like project-management metadata rather than scientific evidence.

8. The year label “Design timeline (2026)” is internally consistent but can distract.
   - The manuscript is clearly a 2026 draft (`main.pdf` cites “Claude-family models, 2026 sessions”; placeholder journal header still shows unfilled Received/Accepted fields). The year label is not wrong, but it adds clutter without helping interpretation.
   - Action: consider dropping “(2026)” unless the chronology itself is under discussion.

9. The caption should distinguish final-state hardware from historical design evidence more sharply.
   - Right now panels (a), (c), and (d) read like final-platform evidence; panel (b) is historical; panel (e) is process history. That is a lot of ontologies for one figure.
   - Action: revise the caption to say which panels depict the final implemented architecture and which are historical/process panels.

10. Be careful not to over-claim data-like content where none exists.
   - Figure 1 itself does not use synthetic measurement data, unlike `make_figures.py` Figure 3, which is explicitly watermarked `SYNTHETIC DATA` (lines 278–336). That is good.
   - But panel (d) can be read as implying a demonstrated closed-loop controller, and panel (a) as implying a finalized as-built system image. Since panel (a) is still a render and panel (d) is a concept diagram, the caption should avoid implying fully validated integrated operation unless shown elsewhere with real data.

Is the figure necessary, legible, and sufficient?
- Necessary: probably yes. The manuscript needs an overview figure because the text repeatedly anchors core claims to Fig. 1 (`main.pdf`, p. 2).
- Legible: not yet. Panels (c)–(e) and several callouts/titles are too small at final size.
- Sufficient: no. It lacks a faithful final powder-path panel, an as-built visual, dimensional grounding, and a logically clean closed-loop diagram.

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
- Flagged panel (d) as a control-diagram logic issue based on standard closed-loop block-diagram interpretation of the rendered arrows and the source code in `make_figures.py`.
- Considered branch-tree files as leads only; I named candidate photo/CAD/data files from `all_branches_file_tree.txt` without claiming their contents beyond what filenames and branch paths support.
Resolved in the revised Fig. 1

1. The old hopper/load-cell contradiction in panel (b) is resolved.
- Round-1 problem: `round1_CONSOLIDATED.md` said panel (b) "still shows a hopper/reservoir and a load cell" and called it the main contradiction for Fig. 1.
- Current evidence in `make_figures.py:152-207`: panel (b) is no longer an imported obsolete render. It is redrawn as a schematic with a rectangular auger tube, loading slots, an exit nozzle, falling powder, a cup, and a balance base. The key callout is explicit: `"auger tube = reservoir\n(loaded through slots,\nno separate hopper)"` (`make_figures.py:193-196`).
- The revised caption matches this exactly: `caption_fig1_overview.md:3` says panel (b) shows powder loaded through slots into the auger tube, "which is itself the reservoir (no separate hopper)," then to the exit nozzle and collection cup on the analytical balance.
- The exported figure text in `fig1_overview.pdf` matches: panel (b) reads `auger tube = reservoir (loaded through slots, no separate hopper)` and `cup on balance (A&D HR-100A)`.
- This also aligns with the PR snapshot: `pr97_comments.md:16-21` and `:124-127` say there is no end-design hopper and the sensing hardware is an A&D HR-100A analytical balance, not a load cell.

2. The drive wording has been corrected from the old GT2-style inconsistency to a spur-gear description.
- Round-1 digest: `round1_CONSOLIDATED.md:13-14` said to remove `GT2` from panel (a) unless a belt stage could be documented.
- Current panel (a) callout in `make_figures.py:136` is `"NEMA-11 stepper +\nprinted spur-gear drive"`.
- The caption now says `printed spur-gear drive from a NEMA-11 stepper` (`caption_fig1_overview.md:3`).
- The manuscript body supports this wording: `main.pdf` extracted text on p. 5 says `gear train (printed spur pair, 2.25:1)` and p. 2 says the auger is driven by a NEMA-11 stepper. No `GT2` wording remains in the revised figure materials.

3. The panel (a) caption no longer falsely implies the render visibly resolves the tap solenoid and ERM motor.
- Round-1 digest: `round1_CONSOLIDATED.md:14-15` asked for a rewrite so the caption would not claim those parts are visibly shown if they remain indistinct.
- Revised caption: `caption_fig1_overview.md:3` now says the `tap collar` mounts `the tap solenoid and ERM vibration motor, not individually resolved at this scale`.
- That qualifier also appears in the compiled caption text extracted from `main.pdf` p. 3.
- This is a real fix: the supplied render asset `assets/assembly_iso_final.png` does not clearly resolve those small actuator details.

4. The “sealed park” overstatement in panel (c) has been fixed to “horizontal park.”
- Round-1 digest: `round1_CONSOLIDATED.md:15` said to downgrade `sealed park` to `horizontal park` or equivalent.
- Revised caption: `caption_fig1_overview.md:3` now says the channel tilts from `0° (horizontal park)` to `90° (vertical dispense)`.
- The same wording appears in the extracted caption from `main.pdf` p. 3.

5. The panel (d) control-logic direction has been corrected so the target mass enters the controller, not the actuator.
- Round-1 reviewer digest: `round1_CONSOLIDATED.md:31-32` asked to redraw panel (d) so the target mass enters the controller.
- Current code in `make_figures.py:227-254` defines four boxes: `Dose request (target mass)`, `Controller (coarse → trickle)`, `Auger + tap + vibration actuation`, and `Balance reading (A&D HR-100A, RS-232)`.
- Arrows now run as follows:
  - dose request down into controller (`make_figures.py:247-248`)
  - controller to actuation (`:249-250`)
  - actuation to balance (`:251-252`)
  - balance back to controller (`:253-254`)
- The revised caption matches: `caption_fig1_overview.md:3` says `the target mass enters the controller, which drives the actuation while the balance feeds the measured mass back.`
- The exported PDF text shows the same structure.

6. Human-vs-AI signposting for this figure has been added and is now consistent with the manuscript-wide constraint.
- Round-1 signposting digest: `round1_CONSOLIDATED.md:76-80` asked for explicit HUMAN/AI division of labour and to avoid implying AI chose the architecture.
- Revised caption end: `caption_fig1_overview.md:3` says `humans selected the architecture and reviewed, printed, and tested every part, while AI coding agents generated the parametric CAD models and renders` and adds `no GUI CAD package ... was used.`
- This matches the PR guidance in `pr97_comments.md:22-36` and `:128-130`: distinguish HUMAN vs AI only; no Fusion 360/SolidWorks were used; late exploratory Zoo Design Studio use existed elsewhere in the project.
- The caption correctly keeps the claim at the level of programmatic CAD and renders, without naming individuals.

7. The timeline panel now explicitly anchors the 97-entry claim to `DESIGN-LOG.md`.
- Round-1 provenance digest: `round1_CONSOLIDATED.md:51` asked to cite `DESIGN-LOG.md` directly.
- Revised caption: `caption_fig1_overview.md:3` says `the complete 97-entry design log (DESIGN-LOG.md) is available in the repository.`
- The branch tree confirms that file exists: `all_branches_file_tree.txt` includes `DESIGN-LOG.md`.

Previously flagged issues not yet resolved

1. Panel (a) is still a CAD render, not an as-built photograph.
- Round-1 reviewer digest: `round1_CONSOLIDATED.md:29-30` recommended replacing panel (a) with a photograph or showing render + photo side-by-side.
- Current status: unresolved.
- Evidence: the caption still says `CAD render; photograph of the printed platform will replace this render` (`caption_fig1_overview.md:3`), and `make_figures.py:150` adds the same note directly onto the panel.
- Relevant branch-tree candidates named previously in the digest remain plausible: `presentation/assets/final-print-on-ultimaker.jpg` and `docs/assets/printed/auger-issue16-print-nacl.jpg` are named in `round1_CONSOLIDATED.md:96`; if those are intended, they should be checked against `all_branches_file_tree.txt` before substitution.

2. Panel (c) is still cramped, and the hinge axis is not explicitly marked in the exported figure.
- Round-1 reviewer digest: `round1_CONSOLIDATED.md:32-33` asked to enlarge/simplify panel (c) and explicitly mark the hinge axis and fixed dispense point.
- Current status: only partly resolved.
- Evidence for what is fixed: the underlying asset `assets/rotation_0_45_90.png` clearly contains the red dispense-point marker and a detailed internal suptitle explaining the hinge-axis geometry.
- Evidence for what remains unresolved: `make_figures.py:211-216` trims off the top 10% of that asset specifically to remove the internal suptitle, leaving only the three small subplots under the generic title `Tilt sweep about fixed dispense point`. In the final `fig1_overview.pdf`, the red dot remains, but the hinge axis is not explicitly labeled in-panel.
- Branch-tree provenance for the asset is available: `cad/mounting-plate-assembly/assembly/rotation_0_45_90.png`, `design/cad/mounting-plate-assembly/diagrams/rotation_0_45_90.png`, and `design/cad/mounting-plate-assembly/diagrams/rotation_0_45_90.svg` are all named in `all_branches_file_tree.txt`.

3. The figure still lacks an in-figure physical scale or footprint annotation.
- Round-1 reviewer digest: `round1_CONSOLIDATED.md:30-31` asked for at least the auger OD and an overall footprint or scale bar.
- Current status: only partly addressed.
- Evidence: the caption gives `25 mm OD` (`caption_fig1_overview.md:3`), but no scale bar or overall footprint appears in `fig1_overview.pdf`, and `make_figures.py` adds no dimensional annotation in any panel.

4. Panel (e) remains in the main figure and is still not annotated by generation.
- Round-1 reviewer and narrative digests: `round1_CONSOLIDATED.md:33`, `:94-95` recommended moving the timeline to SI or at least marking it by generation.
- Current status: unresolved.
- Evidence: `make_figures.py:256-279` still builds panel (e) as `Design timeline (2026)` with eight milestone rows, and there are no `Gen 1–4` labels.

Remaining concrete inconsistencies or unsupported claims fixable without new bench data

1. Panel (a) callout layout is still broken in the exported figure.
- Evidence from the revised `fig1_overview.pdf` and the callout positions in `make_figures.py:133-149`:
  - `Auger bracket + tap collar` and `NEMA-11 stepper + printed spur-gear drive` overlap at the top of panel (a), making both labels partly illegible.
  - The italic note `CAD render; photograph of the printed platform to be added` (`make_figures.py:150`) is drawn through the support structure in the rendered panel, so the note itself is hard to read.
- This is a presentation inconsistency between intended annotation and final export. It is fixable just by moving `xytext` coordinates and the placeholder note.

2. The `Hinged plate (servo tilt)` callout in panel (a) does not clearly point to the hinged plate.
- Evidence: in `make_figures.py:137`, the callout anchor is `(0.62, 0.62)` on the cropped image. In the exported panel, that leader lands near the right-hand support area / white-space edge rather than unambiguously on the upper tilting plate that carries the auger.
- The caption claims panel (a) shows a `servo-tilted hinged mounting plate on the baseplate` (`caption_fig1_overview.md:3`). The part exists conceptually, but the callout is not landing cleanly on the feature it names.
- This is a low-cost fix: move the callout target and text so it lands on the actual upper plate.

3. The `Baseplate` callout in panel (a) is weakly supported by the render as currently framed.
- Evidence: in `make_figures.py:138`, `Baseplate` is called out with anchor `(0.46, 0.72)`. In the exported figure, the leader runs toward the lower support region, but the label sits in empty space and the render does not cleanly separate a distinct baseplate from the support legs/substructure.
- This does not make the caption false, but it does make the callout ambiguous. Either reframe the render so the baseplate is visible, or retarget/reword the label to what is visibly identifiable.

4. The caption disclaims that the solenoid and ERM are not individually resolved, but it does not make the same visibility caveat for the servo.
- Evidence:
  - Caption wording: `tap collar (which mounts the tap solenoid and ERM vibration motor, not individually resolved at this scale), and servo-tilted hinged mounting plate...` (`caption_fig1_overview.md:3`).
  - In `assets/assembly_iso_final.png`, the servo itself is not clearly identifiable either.
- This is not a hard contradiction, but it is asymmetrical wording. If the point is feature honesty, the same “not individually resolved at this scale” logic should either cover all small actuators or the panel should avoid implying they are visually discernible.

5. Panel (c) currently suppresses a useful explanatory label that already exists in the source asset.
- Evidence: the source asset `assets/rotation_0_45_90.png` contains the explanatory suptitle `hinge axis is X through ... dispense point literally does not move (red dot)`; then `make_figures.py:212` trims the top 10% away.
- Result: the caption carries the logic, but the figure itself loses the in-panel explanation that would make panel (c) self-contained.
- This is fixable without new data: either keep a compressed version of that source title, or add one short overlay label identifying hinge axis and fixed dispense point.

6. Panel (e) is internally consistent, but still weakly connected to the “four generations” story because the panel itself does not label generations.
- Evidence:
  - The body text says the project passed through `four distinct generations in six weeks` (`main.pdf` p. 2 extracted text).
  - Panel (e) in `make_figures.py:260-268` lists dated milestones only.
- Since the round-1 narrative review specifically flagged this, the current timeline still underserves the manuscript logic even though it is not factually wrong.
- Fixable without new data: add `Gen 1` through `Gen 4` brackets or color bands, or move the timeline to SI.

Prioritized non-bench-data fixes still remaining

1. Fix panel (a) annotation layout first: separate the overlapping top labels, move the hinged-plate leader onto the actual tilting plate, and reposition the `CAD render` note so it is readable.
2. Decide whether panel (e) stays in Fig. 1. If yes, annotate it by generation; if not, move it to SI.
3. Improve panel (c) self-explanation by restoring or replacing the trimmed hinge-axis/fixed-dispense annotation.
4. Add one in-figure scale cue, at minimum the auger `25 mm OD` or a small scale bar / footprint note.
5. Tighten panel (a) visibility wording so small actuators are treated consistently; if the servo is not visually resolved, qualify that just as you already did for the solenoid and ERM.
6. Replace panel (a) with an as-built photo when ready, using a branch-tree candidate only after checking the actual file content.

- Discretionary analytical decisions made during the analysis
- Treated `fig1_overview.pdf`, `caption_fig1_overview.md`, `make_figures.py`, `main.pdf`, `pr97_comments.md`, and `round1_CONSOLIDATED.md` as the primary evidence base, using `all_branches_file_tree.txt` only to name candidate paths and provenance files.
- Counted a round-1 issue as resolved when the revised figure/caption/code no longer contained the contradiction, even if a reviewer’s preferred replacement strategy was not followed exactly.
- Treated layout/legibility problems in the exported PDF as real figure issues when the code-level intent was undermined by overlapping labels or poorly landed leaders.
- Did not treat the continued use of a CAD render in panel (a) as a contradiction, because the caption openly discloses that it is still a render and says a photograph will replace it.
- Did not re-open the known synthetic-data issue from other figures, per instruction.
- Limited attribution to HUMAN vs AI and preserved the project constraint that no GUI CAD package was used; mentioned Zoo Design Studio / Zookeeper only where the supplied files made that broader workflow relevant.
Resolved from round 1

1. Panel (b) hopper/load-cell contradiction is resolved.
- Round-1 problem: `round1_CONSOLIDATED.md` said panel (b) "still shows a hopper/reservoir and a load cell" and should be replaced.
- Revised evidence in `make_figures.py:152-207`: panel (b) is no longer an imported render; it is redrawn as a schematic whose code explicitly states it is "drawn to match the final no-hopper design" and that "the auger tube itself is the reservoir, loaded through slots; dispensed mass lands in a cup on the analytical balance." The callouts are explicit:
  - `make_figures.py:193`: `auger tube = reservoir (loaded through slots, no separate hopper)`
  - `make_figures.py:196`: `cup on balance (A&D HR-100A)`
- The revised caption matches that redraw: `caption_fig1_overview.md:3` says panel (b) shows powder loaded "through slots into the auger tube, which is itself the reservoir (no separate hopper)" and discharged to a "collection cup on the analytical balance."
- The manuscript body now matches too: `main.pdf` states, "There is no separate hopper: powder is loaded directly into the printed Archimedes auger ... through loading slots in the auger tube, so the auger itself is the powder reservoir" and mass is measured by "an analytical balance (A&D HR-100A ... ) ... over RS-232."
- This also fixes the HUMAN review correction in `pr97_comments.md:17-20, 125-126`, which said there is no removable hopper in the end design and that sensing is by an A&D HR-100A analytical balance, not an HX711 load cell.

2. The earlier `GT2` drive wording is resolved.
- Round-1 problem: `round1_CONSOLIDATED.md` said to remove `GT2` from panel (a) annotations unless a belt stage existed.
- Revised evidence: panel (a) now labels the drive `NEMA-11 stepper + printed spur-gear drive` in `make_figures.py:136`.
- This now matches the manuscript, which describes a printed spur-gear drive and later a "printed spur pair, 2.25:1" in `main.pdf`; no GT2 belt is mentioned in the manuscript.

3. The `sealed park` overstatement is resolved.
- Round-1 problem: `round1_CONSOLIDATED.md` said to downgrade `sealed park` to manuscript-supported wording.
- Revised evidence: `caption_fig1_overview.md:3` now says panel (c) tilts from `0° (horizontal park)` to `90° (vertical dispense)`.
- `main.pdf` uses the same wording: the auger can be "parked horizontally" and Fig. 1c says `0° (horizontal park) to 90° (vertical dispense)`.
- `sealed park` is absent from the revised caption and manuscript text.

4. Panel (d) control-logic direction is resolved.
- Round-1 problem: `round1_CONSOLIDATED.md` reviewer lens said panel (d) should be redrawn so target mass enters the controller, not the actuator.
- Revised evidence in `make_figures.py:218-254`:
  - top box: `Dose request (target mass)` (`make_figures.py:228`)
  - controller box: `Controller (coarse → trickle)` (`make_figures.py:229`)
  - actuation box: `Auger + tap + vibration actuation` (`make_figures.py:230`)
  - balance box: `Balance reading (A&D HR-100A, RS-232)` (`make_figures.py:231`)
  - arrows implement target mass -> controller (`make_figures.py:247-248`), controller -> actuation (`249-250`), actuation -> balance (`251-252`), balance -> controller feedback (`253-254`).
- The rendered revised figure matches that logic.
- The caption also now states: `the target mass enters the controller, which drives the actuation while the balance feeds the measured mass back` (`caption_fig1_overview.md:3`).

5. The timeline / 97-entry log linkage is now internally consistent.
- Panel (e) says `Design timeline (2026)` in the figure and ends with `Jun 10 97-entry design log`.
- Caption support: `caption_fig1_overview.md:3` says `(e) Compressed design timeline; the complete 97-entry design log is available in the repository.`
- Manuscript support: `main.pdf` says, "The mechanical design passed through four distinct generations in six weeks, all documented chronologically in a 97-entry design log in the repository (compressed in Fig. 1e)."

Previously flagged issues not yet resolved

1. Panel (a) still overclaims what the CAD render visibly shows.
- Round-1 problem: `round1_CONSOLIDATED.md` said to rewrite panel (a) caption so it does not claim the render visibly shows the solenoid and vibration motor if those parts remain indistinct.
- Current caption still says panel (a) includes a `tap collar carrying the solenoid striker and ERM vibration motor` (`caption_fig1_overview.md:3`).
- But panel (a) callouts in `make_figures.py:133-139` do not label either the solenoid or the ERM. The visible callouts are only:
  - `Archimedes auger (printed, geared)`
  - `Auger bracket + tap collar`
  - `NEMA-11 stepper + printed spur-gear drive`
  - `Hinged mounting plate (servo tilt)`
  - `Baseplate`
- In the supplied rendered panel, the solenoid and ERM are not clearly identifiable as such. So this round-1 issue remains unresolved.

2. The promised photograph has still not replaced the CAD render in panel (a).
- The caption says panel (a) is a `CAD render; photograph of the printed platform will replace this render` (`caption_fig1_overview.md:3`), and `make_figures.py:150` repeats `CAD render; photograph of the printed platform to be added`.
- So the figure still knowingly contains a placeholder visual for panel (a).
- Relevant branch-tree candidates exist and should be named rather than inferred: `presentation/assets/final-print-on-ultimaker.jpg` on branch `origin/copilot/use-marp-create-project-wrapup-presentation`, and `docs/assets/printed/auger-issue16-print-nacl.jpg` on branch `origin/copilot/record-of-designs` (`all_branches_file_tree.txt`).

3. The figure still lacks the scale/dimension context requested in round 1.
- `round1_CONSOLIDATED.md` reviewer lens asked for at least auger OD (25 mm) and overall footprint or a scale bar.
- No panel in revised `fig1_overview.pdf`, `caption_fig1_overview.md`, or `make_figures.py` adds those dimensions.
- That omission is concrete because `main.pdf` explicitly gives `25 mm OD` for the auger, so one implementable fix is available without new bench work.

Remaining concrete inconsistencies / unsupported claims that can still be fixed without bench data

1. Caption-panel mismatch in panel (a): solenoid/ERM claim unsupported by what is shown.
- Caption claims visible hardware detail not actually legible in the render: `tap collar carrying the solenoid striker and ERM vibration motor` (`caption_fig1_overview.md:3`).
- The render/callouts do not document those two parts.
- Fix: either relabel caption to visible geometry only, or swap in a render/photo where those components are actually shown and labeled.

2. Panel (a) conflates two parts in one callout.
- `make_figures.py:135` labels one region `Auger bracket + tap collar`.
- Elsewhere the manuscript treats the tap collar as a distinct split-clamp mounted on the auger tube, carrying the solenoid/ERM (`main.pdf`; also compare the separate tap-collar treatment in the design-specific figure discussion in `round1_CONSOLIDATED.md`).
- This is not a quoted reviewer flag, but it is a real signposting problem. Fix: split into separate callouts or simplify to only the visibly defensible part.

3. Panel (a) has a layout collision.
- In the rendered PDF, the `Hinged mounting plate (servo tilt)` label overruns into the neighboring column, visually colliding with panel (b).
- Source is `make_figures.py:137` plus its placement at `(0.93, 0.42)` on a crowded panel.
- Fix: move the label, shorten it, or reposition panel (a)/(b) spacing.

4. Panel (d) has a second layout collision.
- In the rendered PDF, the `(d)` panel letter overlaps the `Dose request (target mass)` box.
- Source: panel label is placed at top-left by `panel_label()` and the first box is placed at `(0.7, 7.7)` in `make_figures.py:228`.
- The logic is fixed, but the layout is still sloppy. Easy fix.

5. Panel (c) no longer carries the explanatory source text that identifies the red dot / hinge logic.
- The underlying asset `rotation_0_45_90.png` contains a title: `Rotation about the auger dispensing point ... dispense point literally does not move (red dot); axis sits 10 mm forward ...` as visible in the supplied asset.
- But `make_figures.py:212` crops away the top 10% of that asset: `img = img[int(img.shape[0] * 0.10):, :]  # trim internal suptitle`.
- The revised figure therefore keeps the red dot but removes the in-panel explanation of what it is, while the remaining panel is very small.
- Fix: add a small callout for `fixed dispense point` and/or `hinge axis`, or regenerate the panel without depending on cropped embedded text.

6. Panel (c) still does not explicitly mark the hinge axis or fixed dispense point at journal scale.
- Round-1 reviewer lens asked to `explicitly mark hinge axis and fixed dispense point` and to enlarge/simplify panel (c).
- The current tiny three-view panel makes the red dot barely interpretable, and there is no explicit added label in `make_figures.py`.
- Because the underlying asset already supports the claim, this is a presentation fix, not a data gap.

7. Panel (e) dates are only in the graphic, not in body prose.
- The figure panel lists dated milestones (`Apr 23`, `Apr 24`, `May 8`, `May 12`, `May 14`, `May 15`, `May 19`, `Jun 10`), but the manuscript body does not give those dates in prose; it only says the design evolved over `six weeks` and references the `97-entry design log` in `Fig. 1e`.
- That is not a hard contradiction, but it makes panel (e) less auditably grounded than it could be.
- Fix: cite `DESIGN-LOG.md` directly in the caption or SI. The branch tree names it explicitly as `DESIGN-LOG.md` on branch `origin/copilot/record-of-designs`.

8. AI-vs-HUMAN attribution is still absent from the figure caption.
- `round1_CONSOLIDATED.md` signposting lens asked to make the HUMAN/AI split explicit and avoid implying AI made architecture decisions.
- Current caption is silent on provenance (`caption_fig1_overview.md`).
- This matters especially here because the bundle instructions require attribution only at HUMAN vs AI level and specify that no GUI CAD package was used; only programmatic CAD, with late exploratory Zoo Design Studio use elsewhere.
- Fix: add a brief provenance sentence in the caption or SI, e.g. that humans selected the architecture and reviewed/tested parts, while AI coding agents generated parametric CAD/renders; no GUI CAD package was used.

9. The 97-entry log claim is supported, but not directly cited to the repository file in the figure materials.
- The caption says the complete log is available in the repository, but does not name the file.
- `all_branches_file_tree.txt` names `DESIGN-LOG.md` on branch `origin/copilot/record-of-designs`.
- Fix: cite that file directly in caption or SI so the claim is auditable from the figure package.

10. The photograph replacement is already available in the branch tree but not yet used.
- This is not a contradiction by itself, but it is an implementable gap explicitly acknowledged by the current figure.
- Candidate files from the branch tree:
  - `presentation/assets/final-print-on-ultimaker.jpg` on `origin/copilot/use-marp-create-project-wrapup-presentation`
  - `docs/assets/printed/auger-issue16-print-nacl.jpg` on `origin/copilot/record-of-designs`
- Swapping one of these into panel (a), or showing render + photo side by side, would directly resolve the placeholder note without new experiments.

Prioritized action list for remaining non-bench-data fixes

1. Rewrite panel (a) caption so it only claims what the render visibly supports; remove or qualify the solenoid/ERM wording unless those parts are actually shown and labeled.
2. Replace panel (a) with an as-built photograph, or render+photo pair, using a branch-tree asset such as `presentation/assets/final-print-on-ultimaker.jpg` or `docs/assets/printed/auger-issue16-print-nacl.jpg`.
3. Fix panel (c) signposting: explicitly label the red dot as the fixed dispense point and mark the hinge axis; enlarge or simplify the panel if needed.
4. Add at least one physical dimension or scale cue, preferably the manuscript-supported auger OD of 25 mm.
5. Clean the layout collisions: move the panel (a) `Hinged mounting plate` callout and separate the panel (d) letter from the `Dose request` box.
6. Add a short provenance note for HUMAN vs AI contributions and state that no GUI CAD package was used; if keeping the design-log claim in panel (e), cite `DESIGN-LOG.md` explicitly.

- Discretionary analytical decisions made during the analysis
- Treated `main.pdf`, `fig1_overview.pdf`, `caption_fig1_overview.md`, and `make_figures.py` as the primary evidence base, using `round1_CONSOLIDATED.md`, `pr97_comments.md`, and `all_branches_file_tree.txt` for issue tracking and provenance support.
- Counted an issue as resolved only when the revised PDF and the figure source both reflected the fix, not when the caption alone tried to paper over an old asset.
- Treated panel-layout collisions and missing callout labels as concrete figure problems because they affect what a reviewer can actually recover from the exported PDF.
- Used branch-tree paths only as named candidate files and did not assume the contents of unbundled files beyond what their filenames and paths support.
- Kept attribution at HUMAN vs AI only, per the task instructions, and did not assign any figure work to named individuals.
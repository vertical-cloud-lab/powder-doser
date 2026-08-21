## Fig. 1 (`fig1_overview`) — narrative role review

### The job this figure is asked to do

Fig. 1 is loaded with five jobs at once. From the caption (`caption_fig1_overview.md`) and the body references (`main.pdf`, Sec. 2.1–2.2):

- (a) Identify the single-channel module and name its main parts (CAD render with five callouts).
- (b) Show the powder-flow path through the module (annotated cross-section).
- (c) Show the fixed-dispense-point tilt geometry (0°/45°/90° kinematic sweep).
- (d) Define the closed-loop coarse-then-trickle dosing concept (4-box block diagram).
- (e) Compress the 97-entry design log into an 8-milestone timeline (Apr 23 – Jun 1).

Body cites are: "Fig. 1" (whole, p. 2), "Fig. 1c" (p. 2 and again p. 4), "Fig. 1d" (p. 2), "Fig. 1e" (p. 3). Panels (a) and (b) are never cited individually in the running text.

### Is the role coherent and non-redundant?

Partly. The figure tries to be both a "what the thing is" diagram and a "how the project unfolded" infographic, and the second purpose doesn't belong here.

**What works (keep):**
- **(c) Tilt sweep.** Genuinely non-trivial geometry that the prose summarises in one sentence ("the hinge axis passes through the exit-nozzle tip … the dispense point does not translate", p. 2). The three views with the stationary red dot at (Y=125, Z=29.2) make the claim instantly checkable, and the text cites it twice. This is the panel doing the most work per unit space.
- **(a) Module overview.** It is the introductory hardware diagram and the only labeled view of the assembly anywhere in the paper. Fig. 2 only shows close-ups (auger cross-section, split-clamp tap collar), and Fig. 3(d) is a different, *failed* v1 assembly used as a negative example. So (a) is not duplicated. Caveat: the panel is mostly empty space — non-transparent pixels cover only ~11% of the asset — and the caption already admits "photograph of the printed platform will replace this render." It's holding a slot, not delivering a final figure.

**What doesn't (problems):**
- **(b) Powder-flow cross-section directly contradicts the manuscript's own design claim.** The asset (`assets/single_channel_module_powder_flow.png`) is titled "Powder-flow path through the **v2 module** (cross-section) / address of PR review #3228854193", and its sub-title reads "**hopper** → top loading slots → helical channel → exit nozzle → cup." Label ① in the figure is literally a separate hopper box labeled "reservoir (bulk powder)" sitting on top of the auger tube. The manuscript Sec. 2.1 says the opposite: *"There is no separate hopper: powder is loaded directly into the printed Archimedes auger (25 mm OD) through loading slots in the auger tube, so the auger itself is the powder reservoir"* (p. 2). The caption tries to paper over this with "(early v2-module render) … in the final design the auger tube itself is the powder reservoir, with no separate hopper," but that is an apology for showing a superseded design as the platform's flow diagram, and exactly the issue @swcharles flagged on PR #97 line 178: *"We haven't talked about or implemented a removeable hopper. We won't have one on the end design, just the full auger."* The panel is also ~94% whitespace.
- **(d) Closed-loop block diagram is purely a visual restatement of two sentences.** Sec. 2.1 already says "closing the loop for coarse-then-trickle gravimetric dosing" and Sec. 3.4 gives the actual algorithm (90% switch, median-of-5 filter, ≥0.5 s quiet windows, terminate on target or overshoot/timeout). Fig. 4(b) is the *results* figure for the same loop. Fig. 1(d) is a 4-box/4-arrow diagram with no information not already in prose. In a hardware Full Paper aimed at SDL builders, a block diagram of this kind is standard; in an 8-page manuscript already overstuffed, it's a luxury.
- **(e) Design timeline is misplaced.** All 8 milestones map one-to-one onto the four "generations" already enumerated in Sec. 2.2 ("scoop", "auger", "single-channel module", "part-by-part / servo-tilt"). The only thing the timeline panel adds is calendar dates, which appear nowhere else in the manuscript text — Sec. 2.2 only says "six weeks." More importantly, the panel's narrative role is to argue for the methodological contribution (97 logged iterations as a dataset), which is the job of Sec. 2.3 and Fig. 3, not the platform-overview figure. The branch tree shows the underlying material lives elsewhere — `DESIGN-LOG.md` (`origin/copilot/record-of-designs`) and `paper/background/edison_artifacts/design-log-analysis.answer.md` — and the paper itself defers a structured analysis to the follow-up ("a structured quantitative analysis of this log … is reported in the repository and will accompany the multi-doser follow-up"). So Fig. 1(e) is both redundant with the prose and a placeholder for a deferred analysis.

### Verdict

**Keep Fig. 1 as a platform-overview figure, but cut it down to (a) + (c)** — the two panels that actually carry information not available in the prose or other figures.

- Drop (b) outright in its current form. It depicts a superseded v2 design (separate hopper labeled ①) that the manuscript explicitly disclaims, contradicting Sec. 2.1 and PR review #178. If a cross-section is wanted in Fig. 1, redraw it for the final design (auger tube as reservoir, top-cap loading slots only — `paper/figures/assets/auger_geared_cross_section.png` on `origin/copilot/draft-base-manuscript` is closer to the right artefact, and Fig. 2(a) already covers the auger cross-section role for design specifics).
- Move (d) to Sec. 3.4 if retained at all; it pairs naturally with the coarse-then-trickle algorithm description and Fig. 4(b) parity plot, not with the hardware overview. Or cut it — the prose is sufficient.
- Move (e) to SI, or fold it into Sec. 2.2 as a small inline timeline, or replace it entirely with the deferred design-log analysis (acceptance rates by workflow, defect taxonomy) the paper itself promises. A timeline of dates the paper never mentions in text doesn't earn a quarter of a Fig. 1.
- Replace the (a) render with the printed-platform photograph the caption promises before submission (`presentation/assets/final-print-on-ultimaker.jpg` on `origin/copilot/use-marp-create-project-wrapup-presentation`, or `docs/assets/printed/auger-issue16-print-nacl.jpg` on `origin/copilot/record-of-designs`); the current asset is ~89% transparent and reads as a placeholder.

A trimmed Fig. 1 with two panels — labeled final-design overview and the fixed-dispense-point tilt sweep — does the introductory job the paper needs and stops competing with Figs. 2, 3, and 4 for the same narrative real estate.

### Prioritized action list

1. **Fix the contradiction in (b).** Either redraw the cross-section to match the final no-hopper design (auger tube = reservoir, loaded through top-cap slots) or drop the panel. The current caption disclaimer is not a fix; it admits the asset is wrong (`pr97_comments.md` line 178; `main.pdf` Sec. 2.1 p. 2).
2. **Move (e) timeline out of Fig. 1.** Either to SI, to an inline Sec. 2.2 element, or replaced by the deferred design-log analysis (acceptance rate by workflow, defect taxonomy from `DESIGN-LOG.md` and `design-log-analysis.answer.md`). It duplicates the four-generation prose, introduces dates the text never uses, and dilutes a hardware-overview figure with a methodology narrative.
3. **Decide on (d).** Recommend cut. If retained, move next to Sec. 3.4 / Fig. 4(b), where the loop is actually specified and measured. The current placement makes Fig. 1 a mini-abstract-figure rather than a hardware overview.
4. **Replace the (a) CAD render with a photograph of the printed platform** as the caption already promises. Use `presentation/assets/final-print-on-ultimaker.jpg` or `docs/assets/printed/auger-issue16-print-nacl.jpg` from the branch tree. While doing this, verify the callouts (the (a) panel asset is ~89% transparent, so labels currently float over empty space).
5. **Tighten callout text in (a)** to match the manuscript's "no hopper" language so panels (a) and (b)/Sec. 2.1 are mutually consistent.

### Discretionary decisions

- Treated Fig. 1(c) as the strongest panel because the fixed-dispense-point geometry is the only Fig. 1 claim the prose cannot make in a sentence; a reasonable alternative is to call (a) the strongest panel as the entry-point hardware identifier.
- Recommended cutting rather than reworking Fig. 1(d); a defensible alternative is to keep it but move it to Sec. 3.4 next to the coarse-then-trickle algorithm and Fig. 4(b) parity plot.
- Recommended SI / inline placement for Fig. 1(e); an alternative is to retain it as the seed for the deferred design-log analysis the manuscript already promises for the multi-doser follow-up paper.
- Used PR #97 review threads as authoritative on intended final design (no hopper, HR-100A balance, Zoo Design Studio adopted late), in line with @sgbaird's instruction in `pr97_comments.md` to ground attribution and design state in the PR comments.
- Treated "non-white / non-transparent pixel fraction" of the assets (a: ~11%, b: ~6%, c: ~8%) as a proxy for whether a panel reads as a finished figure or a placeholder; this is an informal visual-density heuristic, not a publication-quality criterion.
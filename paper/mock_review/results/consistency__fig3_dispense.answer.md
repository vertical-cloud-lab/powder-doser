Findings first: the biggest internal-consistency problem is that this bundle calls the dispensing-characterization figure “Figure 3,” but in the supplied manuscript it is clearly Figure 4. After that, the main figure/text mismatch is the acceptance-band logic in panel (b): the manuscript body states a two-tier target (±5% above 100 mg, ±10% at 20 mg), while the figure and caption show only a single ±10% band. A smaller but still real issue is that the manuscript describes a replicate-based characterization protocol (n ≥ 10 per condition), but this synthetic placeholder figure presents single traces / point clouds with no replicate structure or uncertainty display.

Analysis plan executed:
1. Cross-checked the supplied figure PDF (`fig3_dispense.pdf`), caption (`caption_fig3_dispense.md`), and source (`make_figures.py`).
2. Cross-checked those against the manuscript body in `main.pdf`.
3. Cross-checked against reviewer comments in `pr97_comments.md`.
4. Used `all_branches_file_tree.txt` only to name potentially relevant repository files/paths where applicable.

What is consistent
- The caption explicitly says this is synthetic placeholder data to be replaced later: `caption_fig3_dispense.md`, line 3. The rendered figure is watermarked “SYNTHETIC DATA” in all panels. That matches.
- Panel meanings match source code:
  - (a) cumulative mass vs time: `make_figures.py`, `def fig3()`, first panel.
  - (b) requested vs measured mass with a shaded ±10% band: `make_figures.py`, `ax.fill_between(... 0.9 ... 1.1 ...)`.
  - (c) dose CV vs auger speed: `make_figures.py`, third panel.
- The four powders named in panel (a) match the manuscript’s text description of the characterization set:
  - Source labels in `make_figures.py`: “Glass beads (70–110 µm)”, “Al₂O₃ (50 µm)”, “316L steel (15–45 µm)”, “Xanthan gum”.
  - Manuscript body, `main.pdf` p. 6: “free-flowing glass beads, alumina, 316L steel powder, and cohesive xanthan gum.”
- No hopper/balance contradiction appears in this specific figure or caption. The PR correction says “No hopper in the end design; the auger tube itself is the reservoir” and “A&D HR-100A analytical balance ... NOT an HX711 load cell” (`pr97_comments.md`, lines 125–127). This dispensing figure does not contradict that.

Inconsistencies, contradictions, or unsupported claims

1. Figure number mismatch across the bundle vs manuscript
- Bundle README: `README.md`
  - “Location in manuscript: main.tex, Figure 3 (dispensing characterization, SYNTHETIC)”
- Caption file: `caption_fig3_dispense.md`, line 1
  - “# Caption for fig3_dispense (main.tex, Figure 3 (dispensing characterization, SYNTHETIC))”
- Manuscript body: `main.pdf`, p. 6–7
  - “Fig. 4 summarizes the dispensing characterization protocol...”
  - Compiled caption on p. 7 starts “Fig. 4 Dispensing characterization...”
- Why this is a problem
  - The supplied bundle labels this as Figure 3, but the manuscript itself labels it Figure 4. That is a direct internal inconsistency.
- Proposed correction
  - In `README.md` and `caption_fig3_dispense.md`, change “Figure 3” to “Figure 4.”
  - Suggested wording: “Location in manuscript: main.tex, Figure 4 (dispensing characterization, SYNTHETIC).”
- Relevant branch-tree path
  - `paper/figures/fig3_dispense.pdf` in `all_branches_file_tree.txt`. The filename can stay `fig3_dispense.pdf` if desired, but then the caption metadata should not call it Figure 3.

2. Panel (b) acceptance band does not match the manuscript’s stated acceptance criteria
- Figure caption: `caption_fig3_dispense.md`, line 3
  - “(b) Requested versus measured dose with closed-loop gravimetric control; shaded band is ±10%.”
- Figure source: `make_figures.py`
  - `ax.fill_between(lims, [l * 0.9 ...], [l * 1.1 ...], ...)`
- Manuscript body: `main.pdf`, p. 6
  - “Acceptance targets ... are ±5% accuracy above 100 mg and ±10% at 20 mg...”
- Why this is a problem
  - The figure presents one uniform ±10% band, but the manuscript text states a stricter two-tier criterion. As drawn, panel (b) visually encodes a different performance criterion from the one stated in the body.
- Proposed correction options
  - Best fix to caption/body alignment: revise the caption so it does not imply the ±10% band is the manuscript’s acceptance criterion.
  - Suggested corrected caption wording:
    - “(b) Requested versus measured dose with closed-loop gravimetric control; the shaded band marks ±10% as a placeholder visualization for the synthetic dataset. Final experimental data will be plotted against the manuscript’s acceptance targets (±5% above 100 mg; ±10% at 20 mg).”
  - Alternative figure fix: redraw panel (b) with a piecewise acceptance envelope matching the text.

3. The body describes a replicate-based protocol, but the figure presentation does not show replicates or uncertainty
- Manuscript protocol: `main.pdf`, p. 7, Section 3.4
  - “Doses are dispensed ... with n≥10 replicates per condition.”
- Figure caption: `caption_fig3_dispense.md`, line 3
  - No mention of replicates, error bars, ribbons, or summary statistics.
- Figure source: `make_figures.py`
  - (a) one smooth trace per powder
  - (b) one point cloud per powder
  - (c) one smoothed line per powder
- Why this is a problem
  - It is not a contradiction, because the figure is labeled synthetic. But it is an unsupported presentation relative to the stated protocol: the reader cannot tell how replicate variability will be represented in the final figure.
- Proposed correction
  - Tighten the caption so the placeholder status covers the missing replicate structure.
  - Suggested wording:
    - “(a)–(c) Placeholder visualizations only; final experimental panels will summarize replicate measurements (n≥10 per condition) with appropriate uncertainty displays.”
  - Or, if you want to keep the current visual layout, add “schematic” language:
    - “... illustrating intended analysis structure rather than final statistical presentation.”

4. “Closed-loop gravimetric control” in panel (b) is only asserted, not demonstrated, in the synthetic source
- Caption: `caption_fig3_dispense.md`, line 3
  - “Requested versus measured dose with closed-loop gravimetric control...”
- Source: `make_figures.py`
  - `meas = req * (1 + RNG.normal(0, 0.035, req.size)) + RNG.normal(0, 0.004, req.size)`
- Manuscript body: `main.pdf`, p. 6–7
  - Describes a specific coarse-then-trickle feedback protocol using the A&D HR-100A over RS-232.
- Why this is a problem
  - The synthetic source generates noisy parity data, but nothing in the figure itself demonstrates that the values arose from a closed-loop controller rather than generic simulated measurement noise. Since the caption already admits the data are synthetic, this is not scientific misconduct, but the claim is stronger than the support actually shown in the placeholder figure.
- Proposed correction
  - Tone down the caption until real data are substituted.
  - Suggested wording:
    - “(b) Placeholder requested-versus-measured dose parity plot representing the intended closed-loop gravimetric-control analysis.”

5. The manuscript body frames panel (b) as the “primary accuracy metric” across 20 mg–5 g, but the axis limits visually extend beyond that range
- Manuscript body: `main.pdf`, p. 6
  - “requested-versus-measured dose parity across 20 mg–5 g...”
- Source: `make_figures.py`
  - requested masses are indeed generated from 0.02 to 5 g.
- Rendered figure: `fig3_dispense.pdf`
  - Log axes display ticks from `10^-2` to `10^1` g, i.e. 10 mg to 10 g.
- Why this is a problem
  - Minor, but the displayed axis range is wider than the text-defined experimental range. A reader could infer doses outside the stated range.
- Proposed correction
  - Set panel (b) axis limits to the actual synthetic range if you want tight internal consistency.
  - Suggested source change in `make_figures.py`: replace `lims = [0.01, 8]` with limits that bracket 0.02–5 g more tightly, e.g. `lims = [0.02, 5]` or slightly padded values.
  - Suggested caption wording if you keep the wide axes:
    - “Data points span 20 mg–5 g; axis limits are padded for readability.”

6. The body says panel (a) establishes “mass-flow calibrations,” but the placeholder presentation omits any explicit calibration framing
- Manuscript body: `main.pdf`, p. 6
  - “(a) cumulative dispensed mass versus time at fixed auger speed, establishing per-powder mass-flow calibrations”
- Caption: `caption_fig3_dispense.md`, line 3
  - “(a) Cumulative dispensed mass versus time per powder at fixed auger speed.”
- Why this is a problem
  - Not a contradiction, but the caption drops the calibration purpose that the body emphasizes.
- Proposed correction
  - Add that purpose to the caption.
  - Suggested wording:
    - “(a) Cumulative dispensed mass versus time per powder at fixed auger speed, illustrating the intended per-powder mass-flow calibration.”

7. The body says panel (c) motivates coarse-then-trickle dosing, but the caption does not say the shown trend is a placeholder trend assumption
- Caption: `caption_fig3_dispense.md`, line 3
  - “(c) Dose repeatability (coefficient of variation) versus auger speed, motivating coarse-then-trickle dosing.”
- Source: `make_figures.py`
  - CV is explicitly simulated to rise with rpm: `cv = 0.6 + 0.035 * rpm + ...`
- Why this is a problem
  - Again, not a contradiction, but the caption reads like an empirical conclusion even though the figure is synthetic. In the placeholder state, that motivation is assumed by the synthetic design, not shown by experiment.
- Proposed correction
  - Suggested wording:
    - “(c) Placeholder trend of dose repeatability (coefficient of variation) versus auger speed, illustrating the rationale for coarse-then-trickle dosing to be tested experimentally.”

8. Reviewer-comment alignment: no direct contradiction here, but this figure should avoid over-claiming because PR comments push for strict grounding and role clarity
- PR comments: `pr97_comments.md`
  - lines 23–25: “clarify where ai was used... it should always be clear who did what.”
  - lines 125–130: hardware facts fixed to “A&D HR-100A analytical balance ... No hopper ... No GUI CAD...”
- Why this matters for this figure
  - This specific figure is synthetic and data-only, so it should stay factual and restrained. It should not imply real measured performance before the bench campaign exists.
- Proposed correction
  - Add one sentence to the caption making the status explicit:
    - “This figure is a synthetic layout placeholder and should not be read as reporting measured dispensing performance.”

Things I checked but did not find inconsistent
- No contradiction with the HR-100A correction in `pr97_comments.md` lines 125–127. This figure does not misidentify the sensing hardware.
- No contradiction with the “no hopper” correction. This figure is not a hardware schematic and does not depict a hopper.
- No AI-vs-human attribution conflict in this figure/caption specifically. The attribution disputes in `pr97_comments.md` concern the CAD-design narrative around Fig. 3 in the manuscript, not this dispensing-characterization figure.

Potentially relevant files named from the branch tree
- `paper/figures/fig3_dispense.pdf`
- `design/cad/mounting-plate-assembly/diagrams/powder_flow.png`
- `design/cad/mounting-plate-assembly/diagrams/powder_flow.svg`
- `cad/mounting-plate-assembly/assembly/powder_flow.png`
- `docs/candidate-powders.md`
- `docs/candidate-powders-shopping-list.md`
These may matter later if you want to align powder selection language or cross-reference the broader characterization plan, but they were not needed to establish the inconsistencies above.

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
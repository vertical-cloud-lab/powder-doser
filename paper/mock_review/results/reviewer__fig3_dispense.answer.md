This figure does not yet earn its place in a Digital Discovery Full Paper in its current form. It is clearly marked as synthetic, which is honest, but that also means it cannot support any performance claim. As a reviewer, I would treat it as a placeholder for a future manuscript state, not as publishable evidence. The panels are mostly legible, but they are not yet sufficient, and several numerical and interpretive mismatches need fixing before this figure can carry the dispensing-characterization burden the manuscript assigns to it.

1. Major comments

1. Replace the synthetic figure with real bench data before submission; otherwise the figure should be removed.
- The caption explicitly says this is “SYNTHETIC placeholder data, to be replaced by bench measurements” (`caption_fig3_dispense.md`, line 3), and the figure-generation script says synthetic panels “will be replaced with real bench data before submission” (`make_figures.py`, lines 4–8, 278–337).
- The manuscript also states: “The data shown are synthetic placeholders (watermarked in the figure)” and that the “bench campaign [is] now under way” (quoted from `main.pdf`, §2.4 as extracted from the PDF).
- That is transparent, but for peer review it leaves the figure without evidentiary value. In a Digital Discovery hardware paper, a dispensing-characterization figure is not decorative. It is core validation. If the data are not ready, I would rather see the figure removed and the section reframed as a protocol/future-work section than a synthetic performance figure presented as a main-text result.

2. The figure currently over-promises by functioning like a results figure while containing no results.
- Section 2.4 in `main.pdf` says Fig. 4/`fig3_dispense.pdf` “summarizes the dispensing characterization protocol” but then immediately interprets it as if it establishes calibrations, parity, and a speed-accuracy trade-off.
- The problem is not only that the data are synthetic; it is that the figure visually reads like completed performance validation. For example, panel (b) shows a tidy requested-versus-measured parity cloud with a shaded ±10% band, and panel (c) shows smooth CV trends that imply a settled operating principle.
- For a reviewer, that is too close to an over-claim even with the watermark. I would require either: (i) replacement with real data, or (ii) redesign as an explicit workflow schematic/protocol figure rather than a pseudo-results figure.

3. Panel (b) is not aligned with the manuscript’s stated acceptance criteria.
- The text in `main.pdf` §2.4 states the acceptance targets are “±5% accuracy above 100 mg and ±10% at 20 mg, with per-dose times under 30 s.”
- But the panel (b) caption says only: “shaded band is ±10%” (`caption_fig3_dispense.md`, line 3), and `make_figures.py` implements a constant ±10% band across the full mass range (lines 316–318).
- That is a substantive mismatch. If the true criterion is piecewise, the figure should show the actual acceptance envelope, not a uniform ±10% band. At minimum, the band should tighten above 100 mg, or separate acceptance lines should be drawn and labeled.

4. Panel (b) needs replicate structure and uncertainty, not just one marker cloud.
- Section 3.4 of `main.pdf` says “n≥10 replicates per condition.” But panel (b) does not show replicate aggregation, uncertainty bars, or sample size.
- For a gravimetric dosing paper, a parity plot without error bars is thin. I would want either mean ± SD/95% CI at each requested mass for each powder, or a distribution-based display (box/violin/raincloud) at key dose setpoints.
- If the goal is to demonstrate controller accuracy across 20 mg–5 g, then the reader needs to see how error scales with dose and powder, not just that points cluster near parity.

5. Panel (a) is missing the critical operating condition: the fixed auger speed.
- The caption says “Cumulative dispensed mass versus time per powder at fixed auger speed” (`caption_fig3_dispense.md`, line 3), but it never states what that speed is.
- The source code generates panel (a) with powder-specific linear mass-flow rates but no annotated rpm (`make_figures.py`, lines 293–305).
- Since panel (c) is explicitly about auger speed, omitting the speed in panel (a) makes the calibration uninterpretable. State the rpm in the panel, caption, or legend. If different powders used different fixed speeds, that must be shown directly.

6. Panel (c) is currently weak evidence because the four powder traces are almost indistinguishable.
- In `make_figures.py`, all four curves in panel (c) are generated from the same underlying formula, `0.6 + 0.035 * rpm + noise`, with no powder-specific mean behavior (lines 324–334).
- Quantitatively, the four displayed curves are essentially redundant: the mean cross-powder spread is about 0.04 %CV across a total plotted range of about 1–5 %CV, so powder identity contributes almost nothing visible.
- That defeats the stated purpose of comparing powders “spanning the flowability range of interest” (`main.pdf`, §2.4). If powder identity matters, show powder-specific differences. If it does not, collapse the panel to one representative trend plus uncertainty, and move powder-to-powder comparison to another metric.

7. The figure is insufficiently connected to the controller details claimed in the text.
- Section 3.4 in `main.pdf` gives real methodological specifics: coarse mode to 90% of target, then trickle mode; RS-232 balance reads; median-of-5 filter; quiet windows ≥0.5 s after actuation.
- None of that is visible in the figure. Yet panel (c) is said to motivate “coarse-then-trickle dosing,” and panel (b) is said to reflect “closed-loop gravimetric control.”
- To earn its place, at least one panel should directly show controller-relevant behavior: overshoot distribution, settling time, coarse-to-trickle transition, time-to-target versus requested mass, or accuracy with and without tap/vibration.
- As written, the figure promises a control characterization but mainly shows generic trend sketches.

8. The manuscript says the campaign will report key powder and actuation descriptors, but the figure omits them.
- `main.pdf` §2.4 says the campaign will report “size distribution, bulk/tapped density, flowability class,” plus “actuation ablations (auger only, +tap, +vibration), balance noise under idle and actuated conditions, and wear/fouling observations.”
- None of these appear in the figure.
- That makes the figure insufficient as the main dispensing characterization figure. At least one of the following is needed in this figure or companion SI: powder-property table, actuation-ablation panel, balance-noise panel, and/or time-to-dose panel.

9. The synthetic flow rates in panel (a) risk creating unrealistic expectations.
- The code assigns nominal rates of 1.6, 1.1, 2.3, and 0.45 g s^-1 for the four powders (`make_figures.py`, lines 280–285, 295–299). That yields about 48.0 g, 33.0 g, 68.9 g, and 13.5 g in 30 s, respectively.
- Those values are not themselves impossible, but they are high enough that a reviewer will ask whether they are consistent with auger geometry, reservoir filling, and fine-dose control at the low end.
- The branch tree suggests a potentially relevant file exists on `origin/copilot/measuring-auger-volume`: `cad/auger-geared/capacity/auger_capacity_table.csv`, along with `cad/auger-geared/capacity/auger_capacity.py` and `README.md`. If real data are not yet available, a geometry-based throughput bound from those files could at least constrain plausible rates.
- Until then, the synthetic rates are just invented slopes. They should not be interpreted.

10. Accessibility and legibility need work.
- Panel (a) relies on color alone to distinguish powders. There are no distinct markers or line styles.
- The legend is very small. In the script it is set to `fontsize=4.2` (`make_figures.py`, line 302), which is marginal for a journal figure after print reduction.
- Panel (b) uses the same colors for all powders but no legend within the panel, so the reader must borrow the mapping from panel (a).
- Panel (c) is especially hard to parse because all four lines nearly overlap.
- For a journal spanning automation and materials, assume many readers will inspect this as a reduced-width PDF figure. Increase font sizes, use marker/line-style redundancy, and simplify the encoding.

2. Minor comments

1. Clarify the figure numbering mismatch.
- The file under review is `fig3_dispense.pdf`, but in the compiled `main.pdf` it appears as Figure 4. That is not scientifically important, but it is easy to trip over during revision and response-to-review.

2. State sample size in the caption.
- Since `main.pdf` §3.4 says “n≥10 replicates per condition,” that should appear in the caption for the real figure.

3. State the dose setpoints used in panel (b).
- The code uses 14 requested masses from 0.02 to 5 g (`make_figures.py`, line 308). The real figure should state the actual setpoints or show them clearly in SI.

4. Add units and resolution context for the balance-limited regime.
- The manuscript specifies an A&D HR-100A with 0.1 mg readability (`pr97_comments.md`, lines 125–126; `main.pdf`, §§2.1, 3.4). At 20 mg, that is 0.5% of the target mass. Showing this measurement floor, or at least mentioning it in the caption/SI, would help readers judge whether low-dose error is controller-limited or balance-limited.

5. Consider adding a residuals panel for panel (b).
- Requested-versus-measured parity plots compress error structure. A companion plot of percent error or absolute error versus requested mass would make the low-dose regime much easier to assess.

6. Define CV operationally in the caption or SI.
- Panel (c) says “Dose CV (%)”. State whether this is the coefficient of variation of dispensed mass across replicates at fixed requested mass and speed, and specify the requested mass used for the sweep.

7. Panel (c) should indicate the tested dose during the rpm sweep.
- A CV-versus-rpm curve is uninterpretable unless the requested dose is fixed and reported.

8. Consider showing time-to-target, not only mass-flow and CV.
- The text makes a time claim: “per-dose times under 30 s” (`main.pdf`, §2.4). No panel currently shows dose time directly. A time-to-target panel would test that claim much better than cumulative mass versus time.

9. The caption should distinguish what comes from HUMAN work versus AI-generated placeholders only if relevant to provenance.
- Here the core issue is less authorship than evidentiary status. Still, the surrounding project record is clear that no GUI CAD package was used, only programmatic CAD and later exploratory Zoo Design Studio use (`pr97_comments.md`, lines 128–130). That is background provenance, not figure-specific evidence, so avoid cluttering this caption with it unless the figure itself is reframed around workflow.

10. If the figure remains synthetic during internal drafting, label each panel itself as schematic or mock data.
- The diagonal watermark helps, but in panel (b) especially the figure still looks close to a normal results plot. A subtitle such as “mock analysis layout” would reduce the chance of misreading in slides, reviews, or branch snapshots.

3. Missing items I would expect before this figure is publishable

- Real bench data replacing all synthetic traces and points.
- Stated n for every panel.
- Error bars or distributions for repeat measurements.
- Actual acceptance envelope in panel (b), including ±5% above 100 mg and ±10% at 20 mg.
- The fixed auger speed for panel (a).
- The fixed requested dose for panel (c).
- A direct timing metric, ideally time-to-target versus dose and powder.
- An actuation-ablation comparison: auger only, +tap, +vibration, as promised in `main.pdf` §2.4.
- At least one panel or SI table linking performance to powder descriptors: particle size, bulk/tapped density, and flowability class.
- A residual/error representation for low-dose performance.

4. What I would do with this figure specifically

1. If real data exist, rebuild the figure around three stronger panels:
   - (a) mass-flow calibration with mean ± SD across replicates at stated rpm(s);
   - (b) percent error versus requested mass with the true acceptance envelope;
   - (c) time-to-target and/or overshoot rate for coarse-only versus coarse-then-trickle, optionally split by actuation mode.

2. If real data do not yet exist, remove this figure from the main text.
- Replace it with a protocol/controller schematic, and move the promised characterization to future work.

3. Use the branch tree to pull in any supporting non-synthetic constraints.
- Likely relevant paths include `origin/copilot/measuring-auger-volume: cad/auger-geared/capacity/auger_capacity_table.csv` for volumetric capacity bounds, and `origin/copilot/integrate-scale-feedback-loop: hardware/test-module/firmware/dosing.py`, `scale.py`, `sim/sim_rig.py`, `sim/test_dosing_sim.py`, and `analysis/rs232_analysis_results.md` for controller and balance-integration details.
- Those files may help turn this into a real methods-backed figure rather than a placeholder sketch.

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
- Named potentially relevant branch-tree files only as possible supporting resources, without claiming their contents beyond what the branch tree and retrieved summaries support.
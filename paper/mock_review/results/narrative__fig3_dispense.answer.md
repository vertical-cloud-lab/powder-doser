Keep the figure only if it is replaced with real bench data before submission; otherwise cut it from the main paper. In the current bundle, `fig3_dispense.pdf` is explicitly synthetic, and the manuscript already says so twice: the caption says “SYNTHETIC placeholder data, to be replaced by bench measurements” (`caption_fig3_dispense.md`), and Section 2.4 states that “The data shown are synthetic placeholders ... illustrating the analysis and presentation that the bench campaign now under way will populate” (`main.pdf`, Section 2.4, page 6; compiled as Fig. 4 in the PDF). A placeholder results figure cannot carry the empirical burden this part of the paper needs.

What job this figure is trying to do
- Its intended argumentative job is clear from Section 2.4: it is supposed to be the paper’s evidence figure for performance. The text says it summarizes the “dispensing characterization protocol” across four powders and defines the three main claims the eventual data should support: per-powder mass-flow calibration (panel a), closed-loop dosing accuracy (panel b), and the speed–accuracy trade-off motivating coarse-then-trickle control (panel c) (`main.pdf`, page 6; `caption_fig3_dispense.md`).
- In the paper’s logic, this is the bridge from “we built a low-cost auger doser” (Sections 2.1–2.2; Fig. 1) and “we learned how AI-assisted CAD did and didn’t work” (Section 2.3; compiled Fig. 3) to “the device actually doses powder usefully.” Without that bridge, the manuscript is mostly a design/methodology paper plus future intent.

Why the current figure is not coherent in that role
- The figure is synthetic by construction, not merely unlabeled or preliminary. `make_figures.py` generates all three panels from `numpy` random draws using a fixed RNG seed (`RNG = np.random.default_rng(42)`), and the code comments label it “dispensing characterization (synthetic placeholder data)” (`make_figures.py`, lines 278–337). Panel (a) uses invented linear rates plus sinusoidal/noise terms; panel (b) uses simulated log-space parity points with random error; panel (c) uses simulated CV-vs-rpm curves. None of it is derived from measurements.
- Because the values are synthetic, the figure cannot support the surrounding quantitative language in Section 2.4: “Acceptance targets,” “under way,” “will also report powder-property descriptors,” “actuation ablations,” “balance noise,” and “wear/fouling observations” (`main.pdf`, page 6). The prose is honest that these are forthcoming, but that honesty also undercuts the need for a full main-text results figure now.
- The synthetic watermark is visible in all three panels of `fig3_dispense.pdf`, which helps prevent misreading but also tells the reader that the paper’s central performance figure is not evidence yet.

Coherence with surrounding figures
- Relative to Fig. 1, the role is coherent in concept. Fig. 1 establishes the hardware, powder path, tilt geometry, closed-loop concept, and timeline (`main.pdf`, page 3). Panel 1d already introduces closed-loop gravimetric dosing conceptually. The dispense figure is where that concept should be tested quantitatively.
- Relative to compiled Fig. 3 (the AI-CAD outcomes figure), the role is also coherent in concept. Fig. 3 argues that part-by-part AI-assisted programmatic CAD under HUMAN review worked better than whole-assembly generation, with Zoo Design Studio/Zookeeper adopted late for some parts (`main.pdf`, pages 4–5; `pr97_comments.md`, lines 38–76, 117–130). The dispensing figure is then supposed to show that the resulting hardware performs.
- Relative to compiled Fig. 2 (design specifics: auger cross-section and tap collar), there is little redundancy. Fig. 2 is structural/mechanical; the dispense figure is functional/performance.

Where it becomes redundant or awkward
- Panel (c) partly duplicates the claim already made in prose and concept diagrams: coarse-then-trickle dosing is introduced in Fig. 1d and described in Section 3.4 (`main.pdf`, pages 3 and 7). With real data, panel (c) would justify that strategy empirically. With synthetic data, it only restates the intended control logic.
- Panel (a) is weak even as a placeholder because the manuscript already says the auger tube is the reservoir, powders differ in flowability, and calibration sweeps will be done (`main.pdf`, pages 2, 6, 7). Without measured rates or uncertainty, it adds little beyond “different powders behave differently,” which the text already implies.
- The whole figure also competes with the paper’s other real contribution: the AI-assisted hardware-design case study. Right now, the manuscript’s strongest documented evidence is about workflow and provenance, not dosing performance. A synthetic performance figure shifts attention to the paper’s least-supported claim.

Keep / merge / move / cut recommendation
1. Best option: keep in main text only after replacement with real data.
   - This is the right narrative slot for a real characterization figure. If bench data arrive, the figure should stay in the main paper because it carries the main empirical proof that the open-hardware doser works, not just that it was designed.
   - When real data are substituted, panel (b) is the indispensable panel. It directly tests the main application claim: requested vs measured dose under closed-loop gravimetric control. That is the clearest “does it work?” result.
   - Panels (a) and (c) are useful but secondary. They support calibration and controller rationale.

2. If real data do not arrive for this submission: cut from the main paper, do not move to SI unchanged.
   - Moving a synthetic results figure to SI does not solve the problem. It still advertises unmeasured performance, just in a less visible place.
   - The main text can still discuss the planned characterization protocol briefly, but it should not display fabricated placeholder curves as if they were an interim figure.
   - If the authors want to preserve the protocol visually, a schematic workflow figure would be safer than synthetic result panels. That schematic does not exist in the supplied bundle, but a likely place to build from is `hardware/test-module/firmware/dosing.py` or `hardware/test-module/firmware/scale.py` from branch `origin/copilot/integrate-scale-feedback-loop`, both named in `all_branches_file_tree.txt`. Those files suggest a real control workflow exists in code even if bench data are not yet in the repository.

3. Do not merge it with another current figure in its present form.
   - Merging into Fig. 1 would worsen overload: Fig. 1 already contains assembly overview, cross-section, tilt sweep, control concept, and timeline.
   - Merging into the AI-CAD figure would confuse two separate claims: design workflow quality versus dispensing performance.
   - If real data exist later, a slimmed main-text figure with only the most decision-relevant panel(s), especially parity/accuracy, could be justified.

Specific file-grounded issues to note
- File-numbering mismatch: the bundle README and caption call this `fig3_dispense` and “Figure 3,” but in the compiled `main.pdf` the dispensing characterization appears as Fig. 4, while compiled Fig. 3 is the generative-AI CAD outcomes figure. That should be reconciled before further review (`README.md`; `main.pdf`, pages 5–7).
- There is no evidence in the supplied repository tree of actual dispensing datasets yet. Across all 45 branches, the only CSV named in `all_branches_file_tree.txt` is `cad/auger-geared/capacity/auger_capacity_table.csv`; no bench characterization CSV/JSON/parquet files are listed. That supports the manuscript’s statement that the bench campaign is still forthcoming.
- The figure-generation source itself states the policy clearly: “Panels that contain synthetic (placeholder) data are watermarked ... they will be replaced with real bench data before submission” (`make_figures.py`, lines 4–8). On the supplied evidence, that replacement has not happened yet.

HUMAN vs AI contribution framing for this figure
- HUMAN contribution: defining the characterization story the paper wants to tell, choosing the powders/metrics/ranges described in Section 2.4 and the caption, and deciding how performance should connect to the hardware narrative.
- AI contribution: authoring the figure-generation code that renders synthetic placeholder plots (`make_figures.py`) and, more broadly, contributing to surrounding CAD/programmatic workflows described in the manuscript.
- Important constraint from the record: no GUI CAD package such as Fusion 360 or SolidWorks was used; mechanical design was done through programmatic CAD written by LLM coding agents under HUMAN review, with Zoo Design Studio used late and exploratorily through chat with its Zookeeper agent (`pr97_comments.md`, lines 27–36 and 125–130; `main.pdf`, pages 1–2, 4–6).

Prioritized action list
- Replace `fig3_dispense.pdf` with real bench measurements or remove the figure from the main paper.
- If real data are not ready, delete the synthetic panels rather than moving them to SI unchanged; keep only a brief protocol description in text.
- When real data are ready, keep panel (b) as the core main-text result; demote or simplify panels (a) and possibly (c) if space is tight.
- Fix the figure-numbering mismatch between bundle metadata (`fig3_dispense`) and the compiled manuscript (dispensing appears as Fig. 4).
- If a non-results visual is still needed before data exist, build a protocol/control schematic from existing code paths named in `origin/copilot/integrate-scale-feedback-loop` instead of showing synthetic numeric outcomes.

- Set the decision threshold as: keep only with real data; otherwise cut rather than move to SI.
- Treated the compiled manuscript (`main.pdf`) as authoritative for narrative role, while using `make_figures.py`, the caption file, PR comments, and branch-tree paths to verify provenance and intent.
- Used branch-tree evidence to assess whether undisclosed real characterization datasets likely exist; because no such data files appear in `all_branches_file_tree.txt`, I did not infer any measured results beyond what the manuscript states.
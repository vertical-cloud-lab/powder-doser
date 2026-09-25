Handling Editor Assessment (persona: Alán Aspuru-Guzik, Digital Discovery Editor-in-Chief)

This manuscript is in scope for Digital Discovery’s hardware-focused Full Paper track. The combination of a low-cost powder-dosing module for self-driving laboratories, explicit open-hardware release, and a critical account of AI-mediated CAD design is well aligned with the journal’s interest in digital discovery infrastructure, autonomy, and reproducibility. The strongest aspects are the practical hardware target, the unusually complete provenance trail for the AI-assisted design workflow, and the potential relevance to autonomous materials workflows where solids handling remains a real bottleneck.

That said, the paper in its current form is not yet ready for acceptance as a full research article because the central performance claim is not supported by real dispensing data. Section 2.4 and Fig. 4 are explicitly described as “synthetic placeholders,” and the manuscript therefore does not yet demonstrate the claimed dosing accuracy, repeatability, or operating envelope. As written, the work is best understood as a promising hardware-and-methods platform paper with incomplete validation. My recommendation is major revision. A revised version with real benchmarking data, clearer separation between demonstrated results and forward-looking claims, and tighter positioning of the AI-CAD contribution could become a strong fit for the journal.

Reviewer 1 Report (persona: Milad Abolhasani; self-driving labs / autonomous experimentation)

Summary of the contribution

This paper addresses a real SDL bottleneck: reliable, low-cost powder dispensing. The authors present a single-channel auger-based module with tilt, tap, vibration, and gravimetric feedback, targeted at later expansion into a multi-powder system for alloy discovery. From an SDL perspective, the manuscript’s main contribution is not just the hardware bill of materials and architecture, but the attempt to make powder dosing modular, open, and digitally reproducible. I also see value in the full logging of the AI-assisted mechanical design process. If validated properly, this could be useful to many labs that can automate liquids but still handle solids manually.

Major comments

1. The main experimental claim is not yet experimentally supported.
   - Section 2.4 states that “The data shown are synthetic placeholders” and Fig. 4 is watermarked “SYNTHETIC DATA.” For a Full Paper, this is the core problem. The manuscript claims an “accurate” doser in the title, abstract, and conclusions, but no real dose-accuracy, repeatability, throughput, or failure-rate data are shown.
   - Action: replace Fig. 4 with measured results and add a complete validation section: requested vs measured mass, replicate counts, absolute and relative error, CV, overshoot rate, time-to-dose, and failed-dose frequency across the stated powder set.

2. The closed-loop control strategy is described, but not characterized as a control system.
   - Section 3.4 describes switching from coarse mode to trickle mode at 90% target mass, with median-of-5 balance filtering and quiet windows of >=0.5 s. That is useful, but SDL users need to know how robust this is to balance lag, actuator-induced vibration, powder dribble after auger stop, and different flow regimes.
   - Action: quantify controller behavior. Show transient examples of mass vs time near cutoff, overshoot distributions, settling time, and whether the 90% switch threshold is fixed or powder-specific. A short ablation on cutoff threshold and quiet-window duration would help.

3. The paper needs a clearer system-level SDL integration story.
   - The introduction positions this as enabling autonomous additive-manufacturing alloy discovery, but the demonstrated system is a single channel over a balance. Fig. 5 is future work. As written, there is a gap between the use-case framing and the demonstrated capability.
   - Action: either narrow the claims to a validated single-channel module for SDL integration, or provide a concrete integration demonstration. Even a simple scripted autonomous run sequence with target list execution, logging, and recovery behavior would strengthen the SDL framing.

4. Benchmarking against manual weighing or existing low-cost workflows is missing.
   - Cost is discussed in Section 2.5, but a user deciding whether to adopt this system will want practical throughput and operator-burden comparisons.
   - Action: include a benchmark against manual analytical-balance dosing by a trained human, or against a simple open-loop auger-only baseline. Compare dose time, error, intervention rate, and reproducibility.

5. The manuscript should define the operational envelope and failure modes more explicitly.
   - You mention four powders: glass beads, alumina, 316L steel, and xanthan gum. That spans flowability qualitatively, but the reader needs to know where the method breaks.
   - Action: report powder descriptors and failure cases systematically: particle size range, bulk and tapped density, angle of repose or other flow proxy if available, bridging tendency, residual holdup, nozzle clogging, cleaning burden, and cross-run carryover.

6. The open-source value proposition is strong, but reproducibility requires a more concrete replication package.
   - Section 3.2 points to firmware and schematics in the repository; good. For SDL adoption, the important issue is whether an external lab can reproduce the instrument without reverse engineering the paper.
   - Action: add a concise table in the paper or SI summarizing repository contents, versioned release/commit, calibration scripts, communication protocols, and minimum build skills.

Minor comments

1. Fig. 1 caption says “photograph of the printed platform will replace this render.” That must be updated before submission.
2. The corresponding author email is still “TODO-corresponding-email” on page 1.
3. The manuscript should report balance sampling rate or effective acquisition cadence over RS-232.
4. Clarify whether the under-$200 estimate in Section 2.5 includes fasteners, wiring, printed mass, and failed-print overhead.
5. In Section 4, “can be built for under $200” reads stronger than the evidence currently supports; this should be softened until real data are included.
6. Consider adding a simple state diagram for the dosing routine.

Recommendation

Major revision.

Reviewer 2 Report (persona: Johannes G. Khinast; powder dosing / feeder metrology)

Summary of the contribution

I read this manuscript primarily as a feeder and micro-dosing paper. The authors propose a low-cost single-channel gravimetric auger feeder with auxiliary tapping, vibration, and tilt control. The low-cost, open-hardware aspect is interesting. The metrology framing is also potentially useful because the literature on precise low-dose powder feeding remains dominated by proprietary or domain-specific systems. However, as a dosing paper, the manuscript is currently incomplete because the actual performance data are absent and the feeder geometry and test protocol are not yet described at the level needed for technical assessment.

Major comments

1. The paper lacks real feeder-performance data.
   - This is the main issue. Section 2.4 explicitly states that Fig. 4 contains synthetic placeholders. Without measured feeder curves, dose distributions, and powder-dependent behavior, it is not possible to assess whether the instrument performs meaningfully as a micro-dosing platform.
   - Action: provide real data for each powder and, ideally, each nozzle variant in SI Fig. S1. At minimum report mean error, standard deviation, CV, overshoot frequency, minimum reliably dosed mass, maximum practical mass-flow rate, and drift over repeated doses.

2. Critical feeder geometry is under-specified for a dosing paper.
   - The auger OD is given as 25 mm in Section 2.1 and Section 3.1, and Fig. 2a shows the cross-section, but important geometric parameters are missing from the main text: helix pitch, flight thickness, radial clearance, trough/tube geometry, nozzle dimensions, loading-slot dimensions, and tolerance strategy for printed parts.
   - Action: add a table of the governing dimensions and tolerances, including which are fixed and which are parametric. These parameters strongly influence refill, compaction, leakage, and discharge behavior.

3. The role of tilt, tapping, and vibration needs proper ablation.
   - Section 2.1 presents all three auxiliary mechanisms as part of the system, and Section 2.4 says actuation ablations “will” be reported. They should be reported here, not deferred.
   - Action: quantify auger-only vs auger+tap vs auger+vibration vs full system. This is necessary to determine which mechanism is actually responsible for stable feeding, especially for cohesive powders.

4. The powder characterization is too thin for interpreting dosing results.
   - Naming four powders is not enough. Flow behavior depends on PSD, shape, density, cohesion, moisture sensitivity, and electrostatics. In feeder studies, interpretation without such descriptors is weak.
   - Action: provide a powder table with at least particle size distribution, density measures, and a flowability metric. If some measurements are unavailable, state that clearly and justify the chosen proxies.

5. The gravimetric methodology needs more detail and noise analysis.
   - Section 3.4 states use of an A&D HR-100A with 0.1 mg readability, median-of-5 filtering, and quiet windows >=0.5 s after actuation. Readability is not the same as dynamic uncertainty during vibration and mechanical motion.
   - Action: report baseline balance noise, noise during idle with the mechanism mounted, and noise following actuation events. Show how long the signal takes to stabilize and justify the 0.5 s waiting criterion from data.

6. There is no discussion of refill behavior and hold-up in the auger-reservoir design.
   - Section 2.1 says there is “no separate hopper” and the auger itself is the powder reservoir, loaded through slots. That is mechanically simple, but it raises questions about refill uniformity along the screw, segregation, limited capacity, and dependence on initial filling state.
   - Action: quantify fill volume, mass capacity, effect of initial fill fraction on dose accuracy, and residual mass at the end of a run.

7. The acceptance criteria appear application-driven but not yet justified by data.
   - Section 2.4 gives targets of ±5% above 100 mg and ±10% at 20 mg so dose error contributes less than one atomic percent in a five-component blend. That is reasonable as a use-case target, but the manuscript does not yet show the derivation clearly or demonstrate that those thresholds are met.
   - Action: show the calculation connecting dose error to composition error for the intended alloy-discovery use case and then present measured attainment rates against those targets.

8. Durability, wear, and powder compatibility of PLA are not addressed sufficiently.
   - Section 2.1 and 3.1 specify PLA printed parts. That is attractive for cost, but abrasive powders such as alumina and metallic powders such as 316L can alter surfaces, clearances, and electrostatic behavior.
   - Action: include short-term wear observations after repeated dosing, any measurable change in performance over time, and whether alternative materials should be preferred for some powder classes.

Minor comments

1. SI Table S1 excludes printed parts and the analytical balance; the main text should consistently state this every time the cost claim appears.
2. Fig. S1 nozzle variants are shown, but the manuscript does not state which nozzle was used in the main module shown in Fig. 1.
3. In Section 2.1, “dosing resolution is set by step-counted auger rotation” is incomplete; practical resolution also depends on powder behavior and post-stop discharge.
4. Report whether the stepper was microstepped and at what setting.
5. Clarify whether the gear ratio 2.25:1 in Section 3.1 is reduction from motor to auger and how backlash affected dosing.
6. The paper would benefit from a schematic nomenclature panel for all key mechanical elements.

Recommendation

Major revision.

Reviewer 3 Report (persona: Adriana Schulz; LLM / generative CAD / parametric design)

Summary of the contribution

This manuscript is unusual and interesting because it treats AI-generated CAD not as a benchmark exercise on synthetic geometry tasks, but as part of a full hardware design campaign. The strongest contribution, from my perspective, is the documented workflow: part-by-part programmatic CAD, explicit interface specifications, CI-based checks, human visual review, and public preservation of failures. That is valuable because most published generative CAD work does not show how these tools behave under real engineering constraints. I also appreciate the authors’ negative results, especially the statement in Section 2.3.0.1 that whole-assembly generation failed while interface-first decomposition worked.

My concern is that the AI-CAD claims are currently more anecdotal than analytical. The manuscript contains many strong qualitative conclusions about the tools, but only limited structured evidence in the paper itself. I am supportive of the paper’s direction, but the methodology section needs tightening and the claims need to be bounded more carefully.

Major comments

1. The AI-CAD contribution needs clearer separation between demonstrated evidence and team impression.
   - Section 2.3.0.3 says Zoo Design Studio “was judged by the design team to be the best of the tools tried,” and later notes that “the rankings are qualitative impressions from a single design campaign, not measurements.” I appreciate the honesty, but as written the section still reads like a comparative evaluation.
   - Action: either (a) reframe this strictly as a case study with anecdotal observations, or (b) add structured comparative data in the manuscript: identical tasks, prompts, success criteria, iteration counts, defect counts, and time-to-usable-part for each tool.

2. The paper should formalize the interface-first workflow more precisely.
   - The key methodological claim is that part-by-part generation against explicit interface specifications succeeded where whole-assembly generation failed. This is potentially the most transferable contribution.
   - Action: add a compact workflow diagram or pseudo-protocol showing inputs, constraints, automated checks, review loop, and stopping criteria. I want a reader to be able to reproduce the method, not just the hardware.

3. Quantitative analysis of the 97-entry design log should be moved from “reported in the repository” into the paper.
   - Section 2.3.0.1 says a structured quantitative analysis of the design log “is reported in the repository and will accompany the multi-doser follow-up.” This is exactly the sort of evidence needed now.
   - Action: bring a subset into the paper or SI: number of parts attempted, number accepted, average iterations per accepted part, defect taxonomy, proportion of defects caught by CI versus human review, and fraction of whole-assembly attempts that failed.

4. Provenance categories need sharper definitions.
   - Section 2.2 and Section 2.3 refer to parts as AI-generated, AI-revised, or human-corrected. These categories are useful, but I do not know their exact operational meaning.
   - Action: define provenance labels formally and add a table listing final production parts with their provenance category, tool used, and number of iterations.

5. “No conventional interactive CAD package was used” is an interesting boundary condition, but the manuscript should clarify the extent of human geometric intervention.
   - Section 2.3 says the only graphical CAD environment opened was Zoo Design Studio, used in limited exploratory capacity. Fine. But the manuscript also says the human team provided annotated drawings, some fully dimensioned. At that stage, much of the design intent may already be solved by the humans.
   - Action: be more explicit about what remained a nontrivial CAD task for the AI versus what was already fully specified by the humans. Otherwise some readers will over-interpret the degree of autonomous design.

6. The figures should better support the AI-method claims.
   - Fig. 3 is helpful, especially panels (e-h) showing how stale upstream files caused nonsensical evolution. But the figure currently mixes several narratives: failed assembly generation, iterative recovery, and human-side file-management error.
   - Action: revise Fig. 3 or split it so each panel sequence supports one claim cleanly. A table paired with the figure could map failure modes to detection method and consequence.

7. The manuscript should discuss generalizability limits.
   - The conclusions in Section 4 imply a transferable methodology for AI-designed instruments. That may be true, but this paper studies one device family, one team, and a narrow set of CAD kernels/tools.
   - Action: explicitly discuss threats to validity: single-project bias, changing model versions, team learning effects, prompt-engineering dependence, and how much the success depends on simple part topology and human willingness to review every iteration.

Minor comments

1. In the abstract, the phrase “designed without conventional CAD software” is striking but may distract from the more precise claim: designed through agent-mediated programmatic CAD under human review.
2. The manuscript should define “automated self-checks” more concretely at first mention; “single-body assertions, watertightness, interface-dimension probes run in CI” appears later but could be surfaced earlier.
3. Section 2.3.0.2 has one of the most important observations in the paper, namely silent regressions. Consider emphasizing this earlier, possibly in the abstract or introduction.
4. If prompt/response logs are central to reproducibility, cite a stable repository release or archival snapshot, not only the GitHub URL.
5. The note on “2026 sessions” in Section 3.3 is not sufficient for reproducibility; model identifiers and dates should be tabulated in SI.
6. Some claims could be tightened stylistically. For example, “good enough” is intuitive, but a more technical phrase such as “premature convergence to minimally acceptable geometry under high verification cost” would read more precisely.

Recommendation

Major revision.

Consolidated priority-ranked action list for the authors

1. Replace all synthetic dispensing results with real bench data, especially Fig. 4 and the claims in Section 2.4. Report requested vs measured dose, replicate counts, error, CV, overshoot, throughput, and failure rate across powders. [R1, R2]
2. Recast title/abstract/conclusions so they match what is actually demonstrated. Until real validation is included, avoid presenting the doser as already proven “accurate.” [R1, R2]
3. Add a full metrology section for the gravimetric loop: balance noise, stabilization time after actuation, justification of the 0.5 s quiet window, and transient mass-vs-time traces near cutoff. [R1, R2]
4. Quantify the control strategy, including coarse-to-trickle switching behavior, overshoot distributions, and sensitivity to controller parameters such as the 90% switch threshold and filtering choices. [R1]
5. Add actuation ablations: auger only, auger+tap, auger+vibration, and full system, ideally across more than one powder class. [R2]
6. Provide a proper powder-property table and operating-envelope discussion: PSD, bulk/tapped density, flowability proxy, cohesion/bridging behavior, residual holdup, and failure modes. [R1, R2]
7. Add a geometry-and-tolerances table for the feeder: pitch, flight thickness, clearances, nozzle dimensions, loading-slot dimensions, gear ratio details, and print/material choices. [R2]
8. Bring quantitative evidence from the 97-entry AI design log into the paper or SI: part counts, acceptance rates, iteration counts, defect taxonomy, and what CI caught versus human review. [R3]
9. Formalize the AI-CAD workflow as a reproducible method with a diagram or pseudo-protocol: interface specification, prompt structure, generated artifacts, automated checks, human review, and stopping criteria. [R3]
10. Sharpen the AI-method claims by distinguishing case-study observations from comparative evaluation. If keeping tool-comparison language, add structured cross-tool metrics; otherwise frame those judgments explicitly as qualitative impressions from one campaign. [R3]
11. Define part provenance categories clearly and tabulate final parts with provenance, tool used, and iteration count. [R3]
12. Clarify the SDL integration story. Either narrow the claim to a validated single-channel module or add a concrete autonomous-run demonstration showing how the instrument would slot into an SDL workflow. [R1]
13. Add practical benchmarking against at least one baseline, such as manual analytical-balance dosing or open-loop auger dosing, with comparison of accuracy, time, and intervention burden. [R1]
14. Address durability and materials compatibility, especially wear or fouling of PLA with abrasive or metallic powders and the effect on performance over repeated runs. [R2]
15. Fix production-readiness issues in the manuscript package: replace placeholder figure language, remove “TODO-corresponding-email,” archive the repository at a stable release/DOI, and ensure SI/model metadata are complete. [R1, R3]

Discretionary analytical decisions made during the analysis

- Chose reviewer personas Milad Abolhasani, Johannes Khinast, and Adriana Schulz from the provided reviewer pool to span the three expertise axes requested by the user.
- Treated the manuscript as a Digital Discovery hardware Full Paper and therefore evaluated the absence of real validation data as a major barrier to acceptance rather than as a minor presentation issue.
- Weighted the manuscript’s hardware validation gap more heavily than its open-hardware novelty because the paper explicitly presents itself as an experimentally grounded research article.
- Interpreted the AI-CAD contribution primarily as a case-study/methodology contribution, not a formal benchmark study, because the manuscript itself states that cross-tool rankings are qualitative impressions from a single campaign.
- Used “major revision” rather than “reject” across all reports because the manuscript appears potentially publishable if the missing real data and methodological clarifications are added, and because much of the open-hardware and provenance infrastructure already exists.
- Consolidated duplicate concerns across reviewers into a single ranked revision list, prioritizing issues that affect evidentiary sufficiency before issues of framing, reproducibility packaging, or prose.
# Optimization manuscript: outline and what still needs to be prepared

Draft: [`main.tex`](main.tex) → [`main.pdf`](main.pdf) (issue #179). Working title, from the TMS 2027
abstract: *Auger-based powder dosing as a probe of powder flow: multi-objective, multi-task Bayesian
calibration and physics-based property inference.*

In the PDF, orange bracketed sans-serif text marks a value or claim that waits on data, and every figure
panel built from invented numbers carries a diagonal "SYNTHETIC DATA" mark and a caption that starts with
"[Placeholder: synthetic data.]". Everything else reports work that exists in the repository.

## 1. Target and constraints

- **Journal:** *Additive Manufacturing* (Elsevier), full-length article, @sgbaird's stated preference
  (#179). Fallbacks discussed in the repo: *Additive Manufacturing Letters* (≤5,000 words, faster) if the
  DEM inference is not mature; *Powder Technology* or *KONA* if the DEM inference becomes the main claim;
  a controls venue (e.g. IEEE/ASME *Transactions on Mechatronics*, IEEE *T-ASE*) only if the controller
  and multi-task BO are the contribution (#91 scouting notes, `15-target-journals-and-venues.md`).
- **Guide-for-authors items that shape the draft** (archived 2024 guide plus current Elsevier policy pages;
  re-check the live guide before submission):
  - 5,000–13,000 words *including* references and figure captions.
  - Abstract ≤250 words, no references; ≤6 keywords; 3–5 highlights of ≤85 characters (separate file);
    graphical abstract ≥531 × 1328 px.
  - Numbered references (`elsarticle-num`), figures in-line, third person preferred (the draft uses
    "we", matching the companion paper; decide).
  - "Two-part papers are not allowed": the paper must stand on its own, so it repeats enough of the
    hardware description (Section 2.1) rather than deferring to the companion paper.
  - Posting a preprint before submission is discouraged.
  - **Machine-learning rubric** (Elsevier ML requirements, linked from the guide): papers that skip it are
    returned as premature. It asks for each model's formulation, the dataset, why ML is needed over a
    simpler model, training/testing protocol and hyperparameters, residual and edge-case analysis, and
    comparison against random guessing or the prior state of the art. The multi-task and inference
    results need baselines and held-out tests for this reason (Section 4.B).
  - Generative-AI declaration with Elsevier's wording, immediately before the references; AI used in the
    research itself (the agent that operated the campaigns, wrote firmware and analysis code) goes in
    Methods. Both are in the draft.

## 2. Status of each claim in the TMS abstract

Builds on the status table in `docs/optimization/tms-2027/README.md` on the #166 branch, updated with
the DEM results in PR #180 and the flowability work on the #163 branches.

| Claim | Status | Evidence in the draft | Still needed |
|---|---|---|---|
| Calibration as AI-driven multi-objective BO | **Done, one powder** | Salt: 42-dose SOBOL→SAASBO/qNEHVI campaign (Ax 0.4.3); `bo-005` validated 8/8, median 78 s, 1.8 mg vs 245 s hand-tuned (Fig. 3) | Same campaign on more powders |
| Objectives: accuracy, repeatability, time, accessible dose range | **Two of four** | Time and \|error\| optimized; repeatability only measured after the fact (validation blocks); every dose targeted 0.5 g | Repeatability and dose-range objectives in the campaign code; replicate design; dose-range blocks |
| Every calibration curve is a probe of cohesion, friction, packing | **Early evidence** | 24-fold delivery range, no-flow powders, Si size pair (Fig. 2); delivery ranks like literature angle of repose, ρ = −0.84 (Fig. 6a); per-powder τ_afterflow, tap quantum, speed exponent | Measured properties of the same lots; batch-to-batch resolution |
| Each powder is a related task; multi-task models cut calibration effort | **Not started** | Salt settings carried over to AlSi10Mg (7.993 g of 8 g); Fig. 4 is synthetic | Multi-task GP in `opt_campaign.py`; ≥4 single-task campaigns; benchmark |
| Alloy precursors, elemental or master alloy, under inert atmosphere; AlSi10Mg and stainless steel | **Not started** | One AlSi10Mg and one Al 4047 production dose in air; one qualitative glove-box trial (salt, norbornene, AIBN; Jul 2026) | Glove-box integration; precursor list and hazard review; 316L powder |
| DEM with cohesive-frictional contacts and measured PSDs | **Forward model done** | LIGGGHTS twin, no fitted parameters: 105 vs 105 ± 11 mg/rev at the centre point; tilt trend; exit-gap and grain-size sensitivity (Fig. 5a) | Friction sweep and cohesion curve in the rig geometry; measured PSD and exit geometry; emulator; inference (Fig. 5b, c synthetic) |
| Checked against shear-cell and Hall-flow measurements | **Not started** | Fig. 6c synthetic | Hall/Carney, shear cell (outsourced), PSD, densities on the same lots |
| May anticipate spreadability and packing uniformity | **Proposed only** | Doser flowability proxies V_g and I_stop proposed on the #163 branch | Blade-spread single layers on 3–4 deliberately varied batches |

## 3. Manuscript outline and figure plan

| Section | State in the draft |
|---|---|
| Abstract, highlights, keywords | Written; one placeholder sentence for the multi-task and inference results |
| 1 Introduction | Written (AM alloy discovery → flow characterization limits → feeder behaviour depends on flow properties → BO / multi-task BO → DEM calibration → contributions) |
| 2.1 Doser and dose procedure | Written from the #97/#166 hardware facts; confirm the solenoid model and supply voltage of the tested tap collar |
| 2.2 Powders (Table 1) | Written; needs supplier/lot and measured PSD for every powder |
| 2.3 Gravimetric response at fixed settings | Written (protocols C, D, E, G; dosing fingerprint; V_g, I_stop) |
| 2.4 Calibration as multi-objective BO (Table 2) | Written; describes the salt campaign as run |
| 2.5 Multi-task calibration | Written as a plan; formulation thresholds are placeholders |
| 2.6 DEM | Written for the forward model; inference design is a placeholder |
| 2.7 Independent characterization | Written as a plan |
| 2.8 Statistics | Written; ML-rubric items flagged |
| 3.1 Dosing response separates powders (Fig. 2) | **Real data** (#97/#173, #116 battery) |
| 3.2 Bayesian calibration on salt (Fig. 3) | **Real data** (#166 campaign + 2026-10-06 validation) |
| 3.3 Multi-task calibration (Fig. 4) | **Placeholder** text and synthetic figure |
| 3.4 DEM twin (Fig. 5) | (a) **real** (#180); (b, c) synthetic; inference text placeholder |
| 3.5 Dosing response and properties (Fig. 6) | (a, b) **real** (#163 correlation study); (c) synthetic; comparison text placeholder |
| 4 Discussion | Written; multi-task paragraph has a placeholder |
| 5 Conclusions | Written; one placeholder sentence |
| Declarations | GenAI and competing-interest statements written; CRediT, funding, acknowledgements open |

Figures (all built by `figures/make_figures.py` from `data/`):

| Fig. | Panels | Real now | Synthetic now → replaced by |
|---|---|---|---|
| 1 Overview | (a) one `bo-005` dose trace with stages; (b) data-flow schematic | (a) | — (schematic; update boxes as work completes). Consider adding a photo of the rig and the procedure still from #175 |
| Overview, relations (new; placement open) | cheap doser measurements (feed factor, "ghost dose" tapped density, angle of repose) linked to standard tests (Hall/Carney, PSD, shear cell, tapped density, moisture) through physics-based ML, with the powder's state and history as inputs; from the 28 Oct whiteboard sketch (`meetings/2026-10-28-whiteboard.jpg`) | schematic with a 3D still on every card (`figures/stills/`: the standard tests from the PR #190 animations, the doser measurements as new scenes around the PR #170 doser CAD) | — (`figures/make_overview_relations.py`; `--board` draws only the links on the sketch, `--flat` the earlier flat icons; stills from `figures/render3d/render_stills.py`) |
| 2 Thirteen powders | (a) mg/rev at fixed settings; (b) 1 g closed-loop outcomes | all | — |
| 3 Salt campaign | (a) objective space incl. validation blocks; (b) repeatability; (c) traces; (d) settings changed | all | — (the hypervolume trace was dropped: the observed hypervolume barely moved after screening because two lucky single doses dominate it; move it to the SI with that explanation if wanted) |
| 4 Multi-task | (a) hypervolume vs doses on a held-out powder; (b) learned task correlations | none | leave-one-powder-out replays + one prospective campaign |
| 5 DEM | (a) sim vs measured mg/rev vs tilt; (b) response surface; (c) posterior | (a) | emulator and posterior from the cohesion/friction design |
| 6 Properties | (a) delivery vs literature angle of repose; (b) tilt response per powder; (c) inferred cohesion vs shear-cell ffc | (a, b) | measured ffc, Hall flow on the same lots; swap literature AoR for measured |
| SI (to make) | test-protocol table; screening main effects; per-dose campaign table; τ_afterflow fit; DEM inputs and sensitivity; property table with sources | — | — |

## 4. Still to prepare

### A. Experiments (in dependency order)

1. **Record and fix the hardware state.** Which auger and exit produced each dataset (unresolved in
   #180); measure the as-printed exit hole and core-tip gap, since the DEM shows delivery doubling when the
   tip moves 1 mm. Confirm the tap solenoid and its voltage.
2. **Characterize the lots** (same jars that are dosed): PSD by sieving (sieves on order,
   byu-vcl#262) or laser diffraction; bulk and tapped density / Hausner ratio; angle of repose; moisture
   (loss on drying) with RH logged; Hall flow, or Carney for powders that do not pass; shear-cell ffc
   (FT4 or ring shear, likely outsourced). The #163 discussion judged the full suite for every powder
   unreasonable, so prioritize the powders used in the campaigns and the inference.
3. **Single-task campaigns** with the salt protocol (≈42 doses + 8-dose validation each): AlSi10Mg, 316L
   stainless steel, sieved Al 4047, and at least one elemental alloy precursor. These are the tasks for the
   multi-task model; plan powder quantities (a battery uses 4–10 g; a campaign moves ≈20 g into the cup).
4. **Repeatability and dose range.** Add a dose-range block at each validated point (e.g. 0.05, 0.5 and
   5 g) and decide the replicate count per evaluation for the repeatability objective.
5. **Dosing fingerprints** for every lot (battery A–H or the 15-min proxy protocol proposed on #163),
   with a same-day reference powder: salt's feed factor drifted ≈10 % between days.
6. **Inert atmosphere.** Glove-box dosing of reactive elemental precursors; decide elemental vs master
   alloy per element from handling constraints and hazards (the TMS abstract's framing); static and
   loosening fasteners were problems in the July glove-box trial.
7. **Prospective multi-task test** on a freshly atomized batch.
8. **Spreadability and batch-to-batch resolution.** Blade-spread single 50–100 µm layers of 3–4
   deliberately varied batches of one alloy (sieved vs unsieved, dried vs humid, reused vs virgin, plus
   commercial AlSi10Mg); fingerprint the same batches on the same day. Specify blade gap and speed,
   substrate, spread length, RH, replicate layers and image metrics (areal mass, coverage, uniformity,
   streak/void area), and validate coarse-grained DEM against one fine-powder experiment.

9. **Controller housekeeping that affects comparisons across powders** (from the #154/#166/#131
   records): identify the balance lag τ_bal in the HR-100A's configured response mode (drop tests give
   0.16 s; the firmware assumes the datasheet's 0.7 s, worth 12 mg at trickle and 50–85 mg at bulk rates)
   and its data rate (5.1 vs 10.5 Hz seen); run the built-but-unrun margin and bulk→tap campaigns; A/B the
   refill-tap endgame (taps take a median 76 % of dose time).
10. **Owed bench items:** dried BaCl₂ closed-loop re-run (caked after humidity cycling); block F
   (vibration) never ran; CMC 200 mg re-run; T/RH logging; a drawdown test separating fill level from
   packing (feed factor moved 1.5–1.8× between sessions, #140); wall hold-up of the auger; a calibration
   weight and the granite-slab comparison for the balance (#147).
11. **Glove-box and low-inventory requirements** raised by users: 0.1–10 mg at ±0.1 mg for synthetic
   chemistry (#117), static in argon, and a micro-auger for expensive elements such as Sc (#158; the
   current auger needs 30–40 g to prime, a 10 mm micro-auger 1–2 g). Hazard review for combustible and
   pyrophoric fines (Al, Mg, Ti, Zr; #141).

### B. Analyses and code

1. **Formulation.** Move from \|error\| to a one-sided error with a P(overshoot) constraint, plus
   repeatability P(\|e\| ≤ tol) and accessible dose range, reconciling with the formulation already in
   `docs/optimization/README.md` (#162: minimize time s.t. P(\|error\| ≤ tol) ≥ 0.95 and P(overshoot) ≤ 0.01).
2. **Multi-task model** in `scripts/opt_campaign.py`: task parameter (multi-task GP, index kernel) and a
   descriptor kernel from the dosing fingerprint; warm start from existing doses (the mechanism already
   used to attach screening doses).
3. **Benchmark** (needed for the ML rubric): leave-one-powder-out replays on surrogates fitted to each
   campaign; baselines Sobol, single-task SAASBO, carry-over of the most similar powder's settings, a pooled
   GP without task correlations, a descriptor-only model and a rule-based warm start; same initial designs
   for every method, paired seeds, and no held-out data in the "best known hypervolume";
   metric = doses to 90 % of best known hypervolume; ≥10 replays with seeds; report hyperparameters.
4. **DEM.** Friction sweep and a cohesion curve in the rig geometry (only one cohesion point, in the
   micro-auger, exists); separate particle–wall adhesion from particle–particle cohesion; tie the inferred
   cohesion to the softened stiffness; fix the inconsistencies listed in the #180 review (counting-disk
   position in the README, exit area 7 vs 6.5 mm², whole-run vs steady-state mg/rev, 30→60 rpm scaling of
   the 0° and 45° references, missing `micro_hifric` / `micro_tilt0` data); longer runs and several seeds;
   coarse-graining for fine metal powders; add taps.
5. **Inference.** Emulator design (number of runs, ranges), Bayesian calibration with a discrepancy term,
   identifiability check on synthetic data, virtual shear test vs measured shear cell.
6. **Property links.** Redo Fig. 6 with measured properties; add V_g and I_stop once their repeatability
   is measured; correct for multiple comparisons or pre-register the few tests that matter.
7. **Statistics for Fig. 3.** Bootstrap intervals on the validation-block medians; report the model's
   prediction intervals at `bo-005` before and after dosing.

12. **Reconcile units in older records.** Battery records (#116) store tilt as a servo setting (0/45/90 =
   0/22.5/45° of auger tilt); early #131 scripts reported per *motor* revolution (×2.2 for the auger). The
   draft uses auger tilt and auger revolutions throughout; check every number copied from older docs.
13. **The trim study's "±5 mg is out of reach of any control law" (#154, simulation)** is contradicted by
   later bench data (16/16 validation doses inside a 3 mg band; AlSi10Mg 1 g doses −2.7, +9.4, −1.1 mg)
   because taps on a depleted lip free 0.4–3.6 mg rather than the assumed 6.5 mg. Do not cite the claim.
14. **Optional idea (@sgbaird, #124):** estimate in-flight mass and feed factor from a single run by data
   assimilation (JAX), which would turn every dose, not just calibration batteries, into a measurement.

15. **Salt campaign caveats to address or state** (from the #166 records): the BO phase was stopped by a
   CI deadline after 14 of the 30–40 planned doses and the observed hypervolume did not grow during it;
   the four hand-tuned doses ran at two different τ_afterflow values (two at 0.30 s, two at 0.834 s), so
   run a matched 8-dose hand-tuned block at the fitted τ; spills were never observed in unattended runs,
   so "validated" means no jam or overshoot only; time noise is heavy-tailed (centre point 24–391 s),
   which argues for a robust or heteroscedastic noise model; the screening boxes were never range-found.
16. **Expected reviewer question:** why multi-objective BO rather than single-objective constrained BO
   (an Edison methods check on #124 recommended the latter at about 24 trials)? Answer with the
   Pareto/repeatability argument, or add a single-objective baseline. Novelty support: the 07-07 Edison
   query on #124 found no published multi-objective or contextual BO of powder-dosing parameters in an
   SDL setting.

### C. Writing and submission

- Author list, order and corresponding author (the draft copies the companion paper's six authors with
  W. Mulberry first, since he leads #179 and presents at TMS; nothing is decided). CRediT roles.
- Funding and acknowledgements.
- Decide "we" vs third person.
- Replace every orange placeholder and synthetic panel; remove the placeholder conventions from `main.tex`.
- Supplementary information (list in Section 3).
- Archive data and code with a DOI (e.g. Zenodo release) and update the data-availability statement.
- **Overlap with the companion paper.** The 13-powder data in Fig. 2 and Table 1 are already reported in
  the *Digital Discovery* draft (#97). Either cite them as published there and keep them short (or move
  them to the SI), or agree which paper reports them first; Elsevier screens for duplicate publication.
- Relationship to the companion hardware paper (*Digital Discovery*, due 13 Nov): cite it as a preprint
  or published paper; keep enough hardware detail here to stand alone.
- Suggested reviewers and cover letter from the #91 notes (`17-suggested-reviewers.md`), conflict-screened.
- Check the 12 entries flagged in [`references_validation.md`](references_validation.md) (six ASTM
  standards without DOIs, the software/repository/companion-paper entries, two DataCite DOIs that resolve
  but are not in Crossref, one subtitle mismatch).
- Word count against the 5,000–13,000 limit once results are in.

### D. Suggested order of work (relative to TMS, 14–18 Mar 2027)

1. Now–Nov: hardware state (A1), lot characterization started (A2), formulation and multi-task code
   (B1–B2), DEM sweeps (B4).
2. Nov–Jan: single-task campaigns (A3–A5), benchmark (B3), emulator and inference on salt (B5).
3. Jan–Feb: glove-box precursor campaign (A6), prospective test (A7), property links (B6).
4. Mar: TMS talk with real Figs. 3–6; spreadability (A8) and submission after.

## 4b. Edison mock review (2026-10-13) and what was done with it

Task `2a2e76ab-6ce4-489d-b248-dd7dab7026b5` (ANALYSIS), run on the draft at `7842545`; answer, task
JSON, notebook and all 33 trajectory files are in [`mock_review/`](mock_review/). Panel: handling
editor (Ryan R. Wicker persona; the live board lists **A. T. Clare as Editor-in-Chief**, Wicker as
emeritus, so address the cover letter to Clare), Laura Cordova (AM feedstock / spreadability), Hongyang
Cheng (DEM inference), Keith A. Brown (BO / autonomous experimentation), Johannes Khinast (feeder
metrology). All four: **major revision**; editor: send for review only if the AM-facing validation
(same-lot properties, spreadability, multi-powder campaigns) is completed, otherwise consider *Powder
Technology*, *Digital Discovery* or *HardwareX*. Placeholder-data comments: none were raised (the prompt
asked the panel to judge the planned work instead), so nothing was skipped on that basis (#96 rule).

| # | Action (reviewer) | Type | Done in this draft |
|---|---|---|---|
| 1 | Same-lot characterization of the dosed lots (Co, Ch, Kh) | experiments | Planned (§4.A2) |
| 2 | Batch-to-batch / treatment study within one alloy, e.g. AlSi10Mg dried vs humid, sieved vs unsieved (Co, editor) | experiments | **Added to plan** (§4.A8 extended); not run |
| 3 | Blade-spread validation with a fully specified protocol: blade gap and speed, substrate, length, RH, replicate layers, image metrics (Co, Ch) | experiments | Planned; protocol details still to write |
| 4 | Real multi-task campaigns on several metal / precursor powders (Br, editor, Kh) | experiments | Planned (§4.A3) |
| 5 | Multi-task benchmark with paired replay seeds, same initial designs, no leakage of held-out data into "best known hypervolume", plus pooled-GP, descriptor-only and rule-based baselines (Br) | analysis | Planned (§4.B3); baseline list to extend |
| 6 | One-sided error, P(overshoot) constraint, time conditional on success (Br, Kh) | analysis | Planned (§4.B1); discussed in text |
| 7 | Intervals for validation results (Br, Kh) | analysis | **Done**: bootstrap CIs of medians, Clopper–Pearson bounds, n = 59 needed for P ≥ 0.95 |
| 8 | Measurement-system analysis of the fingerprint: repeatability across fills, days, operators; standardized powder state (Kh) | experiments | Limitation now stated in Discussion; experiments planned (§4.A5) |
| 9 | Unified failure taxonomy (Kh, Br) | writing | **Done** in §2.4; per-dose table still for the SI |
| 10 | Measured as-built exit geometry with uncertainty propagated (Ch, Kh) | experiments | Planned (§4.A1) |
| 11 | Synthetic-recovery identifiability study before real inference; separate particle–wall adhesion (Ch) | simulation | Planned (§4.B4–B5); wall-adhesion caveat added to §2.6 |
| 12 | Full emulator / likelihood / discrepancy specification, posterior predictive checks (Ch, Br) | analysis | Planned (§4.B5) |
| 13 | Validate coarse-graining in the narrow outlet (Ch, Co) | simulation | **Added to plan**; not done |
| 14 | Temper AM claims ("no extra cost", "does not fail on cohesive powders", single AlSi10Mg dose) (editor, Co) | writing | **Done** throughout |
| 15 | Fix Fig. 6a fine-Si caption, screening overshoot counts, Fig. 5a speed labels, quantitative DEM residuals (all) | writing | **Done** |
| 16 | SI tables: per-dose campaign table, feed-factor curves, property table, DEM inputs and runs (all) | writing | Still to make (§3, SI row) |
| 17 | Table mapping every statistical model to the Elsevier ML rubric (editor, Br, Ch) | writing | Still to make |
| 18 | Separate the AI agent's role from the optimizer's (Br, editor) | writing | **Done** in §2.4 |

Also done from the minor comments: El Kassem et al. (KONA 2021, DEM calibration from auger-dosing
experiments) cited as the closest precedent in the Introduction; "no fitted parameters" rephrased as "no
parameters fitted to dosing data"; the stopping band is described as symmetric (±δ); the abstract states
that 14 of the 42 doses were chosen by the optimizer; a table of fingerprint descriptors (units,
replicates, status) added; Spearman ρ now reported with a bootstrap interval and a Bonferroni-adjusted p.
Still open from the minor comments: supplier/lot/storage history in Table 1; label stage-transition masses
in Fig. 1a; an image or sieve result for the clogged Al 4047; CPU model for the DEM timings; outlet mesh
resolution and leak checks; units and uncertainty for tap quantum and τ_af in a table.

## 5. Sources mined for this draft

| Topic | Where |
|---|---|
| TMS abstract and persona review | `abstracts/utah-ai-2026`: `abstracts/tms-2027/calibration-optimization/` (#78) |
| Venues, editors, reviewers, AM abstract | `copilot/determine-journals-editors-reviewers`: `paper/background/15–19-*.md` (#91) |
| Base manuscript, bench data, protocols, 13 powders | `copilot/draft-base-manuscript` (#97), `claude/versatility-figure-gif` (#173), `claude/issue-116-*` battery branches |
| Optimization formulation and literature | `claude/issue-161-20260909-2256`: `docs/optimization/` (#162) |
| Salt campaign, validation, production doses, TMS status table | `claude/issue-164-20260922-1928` (#166), `claude/opt-results-slides-20261005` (#175) |
| Trim study, closed loop | `claude/issue-153-20260903-2040` (#154), `copilot/integrate-scale-feedback-loop` (#100) |
| DEM twin | `claude/issue-158-20261010-0534` (#180), `claude/issue-172-20261003-2216` (#176) |
| Literature properties, correlations, flowability proxies | `claude/issue-163-20260918-2102`, `claude/issue-163-20261007-0613` (#163) |

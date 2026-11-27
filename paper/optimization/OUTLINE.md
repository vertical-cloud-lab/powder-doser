# Optimization manuscript: outline and what still needs to be prepared

Draft: [`main.tex`](main.tex) → [`main.pdf`](main.pdf), SI [`si.tex`](si.tex) → [`si.pdf`](si.pdf)
(issue #179). Working title: *Per-powder Bayesian calibration of an auger doser for alloy feedstock
preparation, and dosing records as a probe of powder flow*. The TMS 2027 talk title is broader
("...multi-task Bayesian calibration and physics-based property inference"); widen the paper's title when
those results exist.

In the PDF, orange bracketed sans-serif text marks a value or claim that waits on data or a decision, and
every figure panel built from invented numbers carries a diagonal "SYNTHETIC DATA" mark and a caption that
starts with "[Placeholder: synthetic data.]". Everything else reports work that exists in the repository.
Every number in the text comes from [`analysis/results/stats.json`](analysis/results/stats.json) and
[`gp_cv.json`](analysis/results/gp_cv.json), written by `analysis/opt_stats.py` and
`analysis/gp_diagnostics.py` from the dose records in `data/`.

## 0. Where it stands (27 Nov 2026)

- **Data.** All 125 records of MongoDB `opt_trials` (29 Sep to 20 Oct 2026) are in
  `data/opt_trials/`. There are no newer calibration or production records. The 133 stepped-tilt trials
  of 18–24 Nov (#131) are Xavier's data-assimilation work (#210), and Sterling assigned them to the
  hardware paper on 27 Nov, so they are not used here.
- **Real results in the draft:**
  - campaign 1 and its validation, with exact tests against the hand-tuned baseline and the best observed dose;
  - leave-one-out checks of the GP model against simpler models;
  - campaign 2 (the hand-over margin) and the powder drift that stopped it;
  - six salt doses from 5 mg to 10 g at the recommended settings;
  - the AlSi10Mg transfer dose and the Al 4047 feed signal;
  - property rank correlations with literature values;
  - the DEM forward model.
- **Placeholders:** multi-task results (Fig. 5, synthetic), DEM inference (Fig. 6b–c), measured
  properties (Fig. 7c), hardware facts (tube ID, exit geometry, capacity), supplier and lot, CRediT,
  funding, the data DOI. There are 24 orange markers in all.
- **Journal requirements:** checked against the live guide in [`SUBMISSION.md`](SUBMISSION.md). The
  cover letter draft is [`cover_letter.md`](cover_letter.md).

### Boundary with the hardware paper (#97)

Both requests of 27 Nov name the Al 4047 atomizer doses. The hardware run, working in parallel on #97,
added "the 10 executor trials and the three charges they filled" to its branch (`4012927`), and later the
charge accuracies (`4b6cd5b`). The two papers are kept apart as follows:

| Data | Hardware paper (#97) | This paper |
|---|---|---|
| 13-powder fixed-setting battery and its 50 mg / 200 mg / 1 g closed-loop doses | owns the figures, table and claims (10–231 mg/rev, 24 of 39 doses within 5%, ...) | cites them; uses the records only for the new property correlations (Fig. 7). The old Fig. 2 and Table 1 are removed |
| Speed exponent from protocol D | "an indication only" (firmware timing error) | no longer used as a result |
| Al 4047 atomizer charges (30 Sep, 19–20 Oct) | owns the charges: how they were dosed, the bulk-only mode, "each container within 2.5 mg" (`4b6cd5b`), and "can be blocked by coarse agglomerates" as a design limit | uses only the bulk feed rate at fixed settings and its decay, as a feedstock-flow signal (Fig. 4a–b), and cites #97 for the charges |
| AlSi10Mg 8 g charge (29 Sep) | shows the request and reply (v2 Fig. 4a) and, since `4b6cd5b` (27 Nov), states "7.993 g for 8 g" in its results and conclusions | cites #97 for the accuracy ("within 0.1%") and uses only the bulk feed rate (144 mg/s) as the transfer result. The abstract and conclusions no longer state the charge accuracy |
| Salt BO campaigns, validation, dose range, GP checks | mentions controller work as future work only | owns them |
| Stepped-tilt trials (#131) | owns them | not used |

**Check both drafts against each other before either is submitted** (Sam and Will).

## 1. Target and constraints

- **Journal:** *Additive Manufacturing* (Elsevier), full-length article, Sterling's stated preference
  (#179, 10 Oct). The live guide (27 Nov) adds a **Methods paper** type: tutorial-style papers on
  "calibration, and validation procedures" and "best practices for uncertainty quantification,
  repeatability, and reproducibility". The present data fit that type better than a full-length research
  article. Other fallbacks discussed in the repo: *Additive Manufacturing Letters* (≤5,000 words), *Powder
  Technology* or *KONA* if the DEM inference becomes the main claim, and a controls venue.
- **Limits and rules:** see [`SUBMISSION.md`](SUBMISSION.md). In short: 5,000–13,000 words including
  references and captions; abstract ≤250 words; 1–7 keywords; 3–5 highlights ≤85 characters; ISO/ASTM
  52900 terms in the title and abstract; third person preferred; full reproducibility details; data
  deposited and cited (Option C); Elsevier's ML requirements; no preprint before submission; no part papers.
- **Editor conflict:** Associate Editor Nathan B. Crane is at BYU (Mechanical Engineering). Ask in the
  cover letter that he not handle the paper. Editor-in-Chief: A. T. Clare (board read 27 Nov).

## 2. Status of each claim in the TMS abstract

| Claim | Status | Evidence in the draft | Still needed |
|---|---|---|---|
| Calibration as AI-driven multi-objective BO | **Done, one powder** | Campaign 1: 42 doses (16 corners, 4 centre, 4 hand-tuned, 4 re-centre, 2 Sobol, 12 SAASBO/qLogNEHVI; Ax 0.4.3). `bo-005` validated 8/8, median 78 s (CI 69–110 s), 1.8 mg; vs 4 hand-tuned doses p = 0.004, 3.1× (2.7× at matched τ). `corner-09` (best single dose) repeated at a median 202 s. LOO checks: the GP's uncertainty is calibrated, but it does not out-predict a linear model | Same session design on more powders; a matched 8-dose hand-tuned block |
| Objectives: accuracy, repeatability, time, accessible dose range | **Two optimized; range seen once** | Time and \|error\| optimized. Repeatability reported from validation blocks, which matches the 28 Oct decision to report it rather than optimize it. Six single doses from 5 mg to 10 g at `bo-005` all ended 0.3–2.7 mg under target, so ±5% is met only above about 60 mg | Dose-range blocks (8 doses each at 0.05 and 5 g) per validated setting; one-sided error and P(overshoot) constraint in the code |
| Every calibration curve is a probe of cohesion, friction, packing | **Early evidence** | Delivery ranks like literature AoR (ρ = −0.84, n = 12); moisture tracks 1 g dose error (ρ = +0.87, n = 9). The Al 4047 bulk feed is 13× below AlSi10Mg at the same settings and recovered after oversized particles were removed | Measured properties of the same lots; within-alloy batch comparison (sieved vs unsieved Al 4047) |
| Each powder is a related task; multi-task models cut calibration effort | **Not started** | Salt settings carried over to AlSi10Mg (one dose, −0.09%) but not to unsieved Al 4047. Fig. 5 is synthetic | ≥2 more single-task sessions, a retrospective benchmark, one prospective session |
| Alloy precursors under inert atmosphere | **Dropped for now** (28 Oct meeting) | — | In air, in a dehumidified enclosure; maybe some tests in the Utah glove box |
| DEM with cohesive-frictional contacts and measured PSDs | **Forward model done** | No fitted parameters: 105 vs 105 ± 11 mg/rev at the centre point; tilt trend; exit-gap and grain-size sensitivity (Fig. 6a) | Friction × cohesion design, emulator, inference on salt with a measured PSD and exit geometry |
| Checked against shear-cell and Hall-flow measurements | **Not started** | Fig. 7c synthetic | Funnel set (buy); shear cell (outside lab) on the campaign lots |
| May anticipate spreadability and packing | **Proposed only** | — | Blade-spread layers with the CubXL or a printer with a wiper (28 Oct) |

## 3. Manuscript outline and figure plan

| Section | State |
|---|---|
| Abstract (246 words), highlights (5), keywords (7) | Written from real data; one placeholder sentence for multi-task and DEM inference |
| 1 Introduction | Written; four questions, each tied to its evidence |
| 2.1–2.3 Doser, powders, dose records | Written; tube ID, exit geometry, capacity, supplier and lot are placeholders |
| 2.4 Campaign 1 | Written, with the corrections of 27 Nov (the cup was never emptied; 2 Sobol + 12 model doses; baseline at two τ values) |
| 2.5 Campaign 2 | Written |
| 2.6 Metal feedstock doses | Written (feed rate only; charges cited to #97) |
| 2.7 Fixed-setting records | Written (protocols C and G of the companion study) |
| 2.8 Multi-task (planned) | Written as a plan, with state covariates and the 28 Oct objectives |
| 2.9 DEM, 2.10 characterization (planned), 2.11 statistics | Written |
| 3.1 Calibration on salt (Fig. 2) | **Real data**, with exact tests and LOO model checks |
| 3.2 Campaign 2 and drift (Fig. 3) | **Real data** |
| 3.3 Metal feedstock (Fig. 4) | **Real data** |
| 3.4 Multi-task (Fig. 5) | **Placeholder** |
| 3.5 DEM (Fig. 6) | (a) **real**; (b, c) synthetic |
| 3.6 Properties (Fig. 7) | (a, b) **real** (literature properties); (c) synthetic |
| 4 Discussion, 5 Conclusions | Written; placeholders where results are missing |
| SI | Per-dose tables for every campaign and the metal doses; screening main effects; LOO model checks and setting relevance; ML-requirements table; property table with provenance |

| Fig. | Panels | Real now | Synthetic now → replaced by |
|---|---|---|---|
| 1 Overview (#195) | cheap doser measurements ↔ standard tests (relational matrix) | schematic (no data) | — |
| 2 Campaign 1 | objective space; repeat blocks; traces; settings changed | all | — |
| 3 Campaign 2 | paired corners at 35 vs 0 mg; bulk feed by session; every dose in order | all | — |
| 4 Metal feedstock | bulk feed at fixed settings (salt, AlSi10Mg, Al 4047); delivery rate within doses; dose range at `bo-005` | all | — |
| 5 Multi-task | hypervolume vs doses; task correlations | none | leave-one-out replays + one prospective session |
| 6 DEM | sim vs measured; response surface; posterior | (a) | emulator and posterior |
| 7 Properties | delivery vs AoR; 1 g dose error vs moisture; inferred cohesion vs ffc | (a, b) | measured ffc and Hall flow on the same lots |
| S1 | LOO predictions of three models | all | — |
| Graphical abstract | — | old DEM-centred sketch | redraw once the scope is fixed |

## 4. What is missing for a complete paper

### A. Experiments, with run counts

Sizes follow the one-session-per-jar design in
[`campaign-as-data/PLAN.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/claude/physics-sims-20261031/docs/physics-simulations/runs/campaign-as-data/PLAN.md)
(#196 branch): about 5–6 h per session, half of it unattended. One session runs an opening fingerprint
(protocols C, D and E), a fixed 22-dose screen, 14–20 BO doses, an 8-dose validation block, a dose-range
block, a closing fingerprint and a salt reference. To that design this plan adds an **8-dose hand-tuned
(or carried-over) block interleaved with the validation block**, the comparison campaign 1 lacks. Block
sizes: with the dose-time scatter of campaign 1 (log-SD 0.26), 8 vs 8 doses detect a 2-fold difference in
time with power ≈1.0 and a 1.5-fold one with power 0.78 (exact Mann–Whitney, α = 0.05; 4 vs 8, as now,
gives 0.72 for a 2-fold difference). Showing P(inside band) ≥ 0.8 with no failures takes 14 doses, ≥ 0.9
takes 29 and ≥ 0.95 takes 59, so the paper should report Clopper–Pearson bounds, not claim 0.95.

| # | What | Doses | Rig time | Powder | Who | Why it is needed |
|---|---|---|---|---|---|---|
| E0 | Bench reset and hardware state: record the tube ID; measure the exit bore and core-tip gap; drawdown test for the working fill; calibration weight; T/RH sensor | — | ½ day | salt | **Will** (bench), **Sterling** (buy the sensor and weight) | Reproducibility (journal rule); the DEM shows a 1 mm tip shift doubles delivery; campaign 2 failed on an emptying tube |
| E1 | **Salt session** with the fixed code (C1–C9): screen 22, BO 20, validation 8 + hand-tuned 8 + 8 at the screen-plus-linear-model pick (the `bo-005` corner with a 30° trickle tilt; `analysis/linear_screen_baseline.py`), dose range 8 × 0.05 g + 8 × 5 g | ≈82 | 1 day | ≈75 g handled | **Will + Claude** | Matched baseline (removes the τ confound); re-validates `bo-005` on a fresh fill after its 13 Oct failure; tests whether BO beat the simpler screen-plus-linear-model strategy (ML checklist item 5); dose range; drift check |
| E2 | **AlSi10Mg session**, same design; the 8-dose baseline is the salt `bo-005` settings (transfer) | ≈74 | 1 day | ≈70 g | **Will + Claude** | Second powder; the AM feedstock; tests transfer properly (now one dose) |
| E3 | **Sieved Al 4047 session**, same design, plus the opening fingerprint on the unsieved batch | ≈74 + 20 min | 1 day | ≈70 g sieved | **Will** (sieving), **Claude** | Third powder; the lab's own feedstock; within-alloy batch comparison (editor and reviewers asked for it) |
| E4 | **Prospective multi-task session** on a fourth feedstock (630 bronze, Al 6063 or a custom alloy; 28 Oct list): 12 multi-task BO doses, validation 8, baseline 8, opening fingerprint | ≈30 | ½ day | ≈40 g | **Sterling** (choose and obtain the powder), **Will + Claude** | The multi-task claim; without it, drop "multi-task" from the scope |
| E5 | **Same-lot characterization** of the 4 campaign lots (+ salt): bulk and tapped density, angle of repose (Will's stand), loss on drying with T/RH, PSD by SEM image analysis or sieving | — | 1–2 days bench + SEM time | few g each | **Will** (in-house), **Sterling** (SEM access) | Measured properties instead of literature values (all four mock reviewers) |
| E6 | Hall/Carney flow on the metal lots | — | 1 h | 50 g each, reusable | **Sterling** (buy a funnel set), **Will** | Standard AM flow test; cohesive powders recorded as no-flow |
| E7 | Shear cell ($ff_c$) on 3–4 lots, outside lab | — | 2–4 weeks turnaround | 10–85 mL each | **Sterling** (contract lab or collaborator) | The check on inferred cohesion |
| E8 | DEM friction × cohesion design for salt (≈30 parameter sets × 3 tilts), emulator, Bayesian calibration | — | ≈45–90 CPU-h + 2–3 days of code | — | **Claude** (needs E0 geometry and the salt PSD from E5) | Inference on one powder (proof of concept) |
| E9 | Blade-spread single layers of 3–4 Al 4047 batches (sieved, unsieved, dried, humid) | — | 1–2 days | 5–10 g per layer | **Will** (CubXL or printer with a wiper) | Only if the spreadability sentence stays; otherwise cut it from the abstract and discussion |

**Total new rig work for the full scope: about 260 doses in 4 rig days (E1–E4), ½ day of bench reset, and
1–2 days of characterization.** Before E1 the code changes C1–C9 and decisions D1–D7 in
[`READINESS.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/claude/physics-sims-20261031/docs/physics-simulations/runs/campaign-as-data/READINESS.md)
have to be done. They take about 2–3 days of agent work plus Will's review; Will settled four of the
decisions on 17 Nov. Close the paused campaign 2 and void its starved doses (D6).

**Minimum version** (drops multi-task and DEM inference from the claims and keeps them as outlook):
E0–E3, E5 and E6, as the round-2 mock review also concluded (§4c). The review adds three things:
- make E3 a **paired, replicated sieved/unsieved Al 4047 comparison**, with the removed or retained
  fraction measured;
- repeat one anchor setting on a **second fill or a second day** (8 doses), so that setting effects can be
  separated from the powder's state;
- add **one quantitative AM-facing outcome**, either a small E9 (blade-spread layers of the two Al 4047
  states) or the composition accuracy of atomizer charges against a tolerance.

That is about 220 doses in 3 rig days, or about 175 if the two dose-range blocks per session are dropped
along with the dose-range claim. It is an *Additive Manufacturing* full-length article only if the sieved
and unsieved Al 4047 are told apart beyond the measurement scatter. Otherwise submit it as an AM **Methods
paper** (the review's preferred route for the present data) or to *Powder Technology*.

### B. Analyses and code

1. **Code before E1:** C1–C9 of `READINESS.md`. These cover the bulk-spin timing, protocol D timing, a
   session runner, logging of `session_id`, `jar_id`, `auger_id`, fill, T/RH and τ_bal, a hopper limit,
   telemetry retry, a box widened to 45°, and τ_bal = 0.16 s.
2. **Model changes from this draft's checks:** model log(time) (LOO ρ 0.44 vs 0.24); a one-sided error
   with a P(overshoot) constraint; the state covariates as context inputs.
3. **Multi-task model and benchmark:** index and descriptor kernels; leave-one-powder-out replays with
   paired seeds and the same initial designs, with no held-out data in "best known". Baselines: Sobol,
   single-task SAASBO, a pooled GP, a descriptor-only model, carry-over of the most similar powder's settings
   and a linear model, at least 10 replays. Item 9 of the ML requirements needs this.
4. **DEM:** see E8, plus the #180 review fixes listed in the 13 Oct outline (counting-disk position, exit
   area, whole-run vs steady-state mg/rev, the 30 → 60 rpm scaling).
5. **Property links:** redo Fig. 7 with measured properties; pre-register the few physically motivated
   tests (cohesion ↔ delivery and interruption fraction; moisture ↔ dose error in hygroscopic powders;
   size ↔ flow within one material) and treat the rest as leads.

### C. Writing and submission (who)

| Item | Who |
|---|---|
| Scope decision: full (multi-task + DEM inference) or minimum; title follows | **Sterling** |
| Author list, order, corresponding author; CRediT | **Sterling** and every author |
| Funding statement and acknowledgements | **Sterling** |
| Hardware facts in §2.1: tube ID, capacity (58 or 70 mL), exit geometry, solenoid voltage; salt and AlSi10Mg supplier and lot | **Will** |
| Boundary with #97: confirm the split above and read both drafts against each other | **Sam** and **Will** |
| Zenodo release of `paper/optimization/` + firmware with a DOI (Option C); not published until approved | **Sterling** approves; Claude prepares |
| Redraw the graphical abstract; remove placeholder conventions; final word count in Word or iThenticate | Claude, after the scope decision |
| Reviewer slate and editor conflict (cover letter) | **Sterling**, each author checks conflicts |
| Edison mock review of the next full draft | Claude, when E1–E3 are in |

### D. Realistic schedule

The hardware paper (#97) plans to submit on 18 Dec 2026 (its status note of 27 Nov), and Will has tasks
there too. This schedule therefore keeps December for decisions, code and the bench reset, and puts the
rig sessions in January.

| Window | Work |
|---|---|
| 30 Nov – 18 Dec | Scope, article type and authors (Sterling). Code C1–C9 and decisions D1–D7 (Claude; Will reviews). E0 bench reset. Buy the T/RH sensor, calibration weight and funnel set. Sieve Al 4047. Ask a contract lab or collaborator for shear-cell quotes |
| 5–29 Jan | E1 salt, E2 AlSi10Mg and E3 sieved/unsieved Al 4047 sessions (3 rig days); E5–E6 in-house characterization; ship E7 samples. For the full scope, also E4 |
| 1–19 Feb | Analysis and figures; the AM-facing outcome (small E9 or charge composition accuracy); for the full scope, the multi-task benchmark and E8 |
| 22 Feb – 5 Mar | Write-up, Edison mock review round 3, author review |
| 14–18 Mar | TMS 2027 talk |
| **Submit** | **Minimum version: about 26 February 2027.** **Full scope: about 16 April 2027**, after TMS, if the shear-cell results are back by mid-March. |

The dates assume the single working doser is free for 3–4 rig days in January. Will (or another person)
must be at the rig for each session: one person, a cup return every 10 doses. The BYU winter break (about
18 Dec – 5 Jan) is left free.

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

## 4c. Edison mock review, round 2 (2026-11-27) and what was done with it

Task `1fea381a-1bc8-4018-a5e3-4613e9acd287` on the rewrite (`2cdf739`). Its files are in
[`mock_review_r2/`](mock_review_r2/), and the full report is
`mock_review_r2/outputs/mock_peer_review_and_audit.md`.

- **Verdict:** reject as a full research article now; the editor would send it out after E0–E3 and E5–E6.
  The present data fit the journal's Methods-paper type better.
- **Numbers reproduced:** the salt medians, the exact p = 0.004, the Hodges–Lehmann and bootstrap
  intervals, Table S1, the outcome counts and the binomial bounds.
- **Duplication:** no copied figure or table was found. The shared events (the AlSi10Mg charge, the Al 4047
  obstruction and clearing) were flagged as the main risk.

| # | Finding | Done in this draft |
|---|---|---|
| 1 | Fig. 7b showed ρ = 0.35, n = 12; the text said ρ = 0.87, n = 9 | **Fixed**: the figure now uses the #163 rule (completed 1 g doses only, n = 9) and shows ρ = 0.87 |
| 2 | "No effect" of the margin is a failure to detect, confounded with drift | **Fixed** in the abstract and §3.2 |
| 3 | Two "ok" doses settle outside their band; ok ≠ inside the failure limits | **Explained** in §2.3 and the SI captions (scored 2 s after the controller's call) |
| 4 | "±5% above about 55 mg" is extrapolated | **Reworded**: the 50 mg dose missed by 5.1%; dose-range blocks are needed |
| 5 | 10 g dose with the firmware fault counted among "all six" | **Stated** in §3.1 |
| 6 | The 7%, ρ = 0.90 and feed numbers not auditable from the SI | **Fixed**: SI Tables S2 and S4 now list each dose's bulk feed |
| 7 | Cleared Al 4047 dose: 31 mg/s here vs about 25 mg/s in #97 | **Fixed**: two estimators reported (mean over the bulk stage, slope over its middle), 18–31 mg/s, and 23 mg/s over the whole dose; the bulk-only mode's taper and boost make the settings nominal |
| 8 | Same events told in both papers (AlSi10Mg 7.993 g; obstruction, reverse turns, clearing) | **Fixed here**: §3.3 cites #97 for the event and the charges and keeps only the feed analysis. **Open**: agree with #97 which paper tells the obstruction story (Sam, Will) |
| 9 | GP coverage ≠ calibrated, useful uncertainty | **Reworded** (40/42 and 39/42 coverage; wide intervals) |
| 10 | Comparisons don't show BO beats simpler strategies | **Stated** in the Discussion; a retrospective screen-plus-linear-model baseline is an open analysis |
| 11 | Fig. 1 marks the humid-air feed factor as measured | **Fixed**: "humid-air test proposed" |
| 12 | Flight length 84 vs 83 mm; companion title; "every prompt" scope; glove-box observation not attributed; Fig. 6a provenance | **Fixed** |
| 13 | Table 1 inventory misses the 2 pre-restart doses | **Fixed** |
| 14 | Freeze the scope and article type | **Open** (Sterling) |
| 15 | Paired, replicated sieved/unsieved experiment; repeat-fill/day anchor; one AM-facing outcome | **Added** to the minimum version (§4A) |
| 16 | Tie-aware permutation tests, success-conditioned time, grouped uncertainty across sessions | **Open** analysis, once E1–E3 give independent sessions |

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

# Hypothetical results figures for the TMS 2027 abstract

Requested in [PR #166](https://github.com/vertical-cloud-lab/powder-doser/pull/166) for the
abstract tracked in [#179](https://github.com/vertical-cloud-lab/powder-doser/issues/179):
*"Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow Behavior: Multi-Task
Bayesian Calibration and Physics-Based Property Inference"* (written in
[PR #78](https://github.com/vertical-cloud-lab/powder-doser/pull/78),
`abstracts/tms-2027/calibration-optimization/abstract.md` on branch `abstracts/utah-ai-2026`).

Each figure is a 16:9 slide (1920 x 1080), in the style of the
[PR #175](https://github.com/vertical-cloud-lab/powder-doser/pull/175) slides: the message
at the top left, no text under 24 pt, and no legends. **Everything watermarked "DUMMY DATA"
is invented to show the shape of the result. It is not a prediction.** Regenerate with
`python docs/optimization/tms-2027/make_hypothetical_figures.py` (needs matplotlib and
scipy).

| Figure | Abstract claim | Measured | Dummy |
|---|---|---|---|
| [`fig1_multitask_calibration.png`](fig1_multitask_calibration.png) | Multi-task models share information across powders and cut per-powder calibration effort | Black marks: salt, hand-tuned (4 doses, median 245 s), and the recommended point `bo-005` after 42 campaign doses, validated with 8 doses (median 78 s) | The single-task and multi-task learning curves and their bands |
| [`fig2_property_inference.png`](fig2_property_inference.png) | Dosing data, read through DEM, give effective cohesion and friction, checked against shear cell | Left panel: feed per auger turn at 90° tilt for 12 powders (#116 battery) against literature angle of repose (tabulated in #163, branch `claude/issue-163-20260918-2102` at `e7b7964`); Spearman ρ = −0.84 | Right panel: every ellipse and cross |

## How this PR lines up with the abstract

| Abstract claim | Status after PR #166 |
|---|---|
| Calibration as AI-driven multi-objective BO | **Done on one powder.** Salt: 42-dose SOBOL→SAASBO campaign (Ax 0.4.3), validated: `bo-005` doses 0.5 g in a median 78 s at 0.8–2.6 mg error, against a 245 s median for the hand-tuned settings. |
| Objectives: accuracy, repeatability, time, accessible dose range | **Two of four.** Time and \|error\| are optimized. Repeatability is measured after the fact (8-dose validation blocks), not optimized. Every campaign dose targeted 0.5 g, so dose range is untested. |
| Calibration curve as a probe of cohesion, friction, packing | **Early evidence.** τ_afterflow is fitted per powder from dosing data (salt: 0.834 s from 26 auger stops, stored in `powder_models`). Across 12 powders, the #116 feed per turn tracks literature angle of repose (#163). No measured flow property of our own lots exists yet. |
| Each powder a related task; multi-task models | **Not started.** Only salt has a campaign. Every record is keyed by `powder_id`, and the margin campaign's warm start (attach existing doses to Ax) is the mechanism a multi-task model needs. The salt optimum carried over unchanged to AlSi10Mg (7.993 g of 8 g in 315 s); Al 4047 clogged on unsieved chunks. |
| Alloy precursors under inert atmosphere, AlSi10Mg, stainless steel | **Not started.** One AlSi10Mg and one Al 4047 production dose, in air. No stainless steel, no elemental precursor, no glovebox dosing. |
| DEM with cohesive-frictional contacts and measured PSD | **Starting.** #158 has a DEM engine review (LIGGGHTS + JKR with ACCES calibration was the suggested route) and a digital-twin run started on 2026-10-10. No calibrated DEM results yet. |
| Checked against shear cell and Hall flow | **Not started.** No shear-cell, Hall-flow or PSD measurements in the repo. |
| Link to spreadability and packing uniformity | **Proposed only.** #163 proposed two doser flowability proxies for LPBF spreading (branch `claude/issue-163-20261007-0613`); none has been run. |

## Experiments still needed

1. **More single-task campaigns, same box and target:** AlSi10Mg, 316L, sieved Al 4047 and one
   elemental precursor, each about 42 doses plus an 8-dose validation block. These are the
   tasks for the multi-task model. Add a dose-range block at each validated point (for example
   0.05, 0.5 and 5 g) to cover the accessible-dose-range objective.
2. **Multi-task benchmark (Figure 1):** leave-one-powder-out replays against surrogates fitted to
   those campaigns, then one prospective multi-task campaign on a held-out powder (a new
   atomized batch). Count the doses until the recommended settings are within 10 % of the best.
   This needs a task parameter (multi-task GP) in `opt_campaign.py`.
3. **Independent flow measurements on the same lots:** PSD (sieves are on order,
   vertical-cloud-lab/byu-vcl#262), bulk and tapped density, Hall flow (Carney funnel for
   powders that won't pass the Hall funnel), angle of repose, and a shear cell (FT4 or ring
   shear tester, likely at an outside lab).
4. **A dosing fingerprint per powder:** feed per turn against tilt and rpm (the #116 battery),
   τ_afterflow (the PR #166 fit) and mg per tap at two or three tilts. These are what the DEM
   model has to reproduce.
5. **DEM inversion (Figure 2):** auger and tube geometry from the CAD, cohesive-frictional
   contacts and the measured PSD. Calibrate surface energy and friction per powder to the
   fingerprint, then run a virtual shear test and compare it with the measured one.
6. **Inert atmosphere and downstream:** glovebox dosing for the reactive elemental precursors,
   and a spreadability test (doctor blade) on atomized batches to support the spreadability
   claim.

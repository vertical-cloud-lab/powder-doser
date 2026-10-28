# Abstract rework from the Utah AI Convergence abstract (27–28 Oct 2026)

Sterling asked to restart the Digital Discovery (DD) abstract from the Utah AI
Convergence 2026 poster abstract, rather than from the current abstract in
[`../main.tex`](../main.tex). The abstract in `main.tex` has **not** been
changed; the candidates below are for review. The full session, including
every prompt and tool call, is in [`transcript.md`](transcript.md).

## Versions

| File | Words | Status |
|---|---|---|
| [`0_utah_original.md`](0_utah_original.md) | 434 | Source: Utah AI Convergence 2026 poster abstract (`abstracts/utah-ai-convergence-2026/abstract.md` on branch `abstracts/utah-ai-2026`, PR #78) |
| [`1_utah_past_tense.md`](1_utah_past_tense.md) | 497 | Past tense, same four paragraphs, facts updated to the manuscript. Fits the Utah 500-word limit, not DD |
| [`2_dd_condensed_rejected.md`](2_dd_condensed_rejected.md) | 248 | **Rejected**: lost the Utah abstract's voice and read too much like the `main.tex` abstract |
| [`3_dd_utah_voice.md`](3_dd_utah_voice.md) | 249 | Utah sentences kept near-verbatim, cut by whole sentences; no doser results |
| [`4_dd_doser_focus.md`](4_dd_doser_focus.md) | 239 | **Current candidate.** First half as in 3; second half rewritten to show what the doser achieved |

Word counts exclude the title. DD asks for a single-paragraph abstract of
"around 50 to 250 words" and sets no character limit
([`../guidelines/`](../guidelines/), also
[`../submission/GUIDELINES-AUDIT.md`](../submission/GUIDELINES-AUDIT.md)).

## Current candidate (4)

> Additive manufacturing of aerospace structural alloys depends on rapid, reproducible exploration of powder feedstocks, yet accurately metering and blending dry metal powders remains a largely manual bottleneck in research laboratories. Commercial dispensers are often cost-prohibitive and poorly matched to alloy-focused, many-powder workflows, and existing open-source designs have not been rigorously developed or tested for laser powder bed fusion (L-PBF). We developed an open-source, low-cost, modular powder doser for precise metering of metal and feedstock powders, intended for integration into a self-driving, Bayesian-optimization materials-discovery loop in which dosed powders feed ultrasonic atomization and L-PBF of aerospace alloys. The first module, a single channel built from 3D-printed parts and off-the-shelf electronics, cost under $200 plus an analytical balance, roughly two orders of magnitude below commercial dosing heads. In closed loop, every 1 g dose on seven of 13 tested powders landed within ±5% of the target, and all nine 1 g doses on the three alloy-relevant powders landed within 1%. The doser also ran inside an inert-atmosphere glove box under the control of an AI agent, and weighed AlSi10Mg into a charge that our ultrasonic atomizer turned into new powder. Its parts were first designed by engineers and modeled by agentic AI: engineers supplied exact dimensions, sketches, and manufacturing constraints; AI modeled the parts as editable parametric scripts; and engineers reviewed, printed, and iterated. In our experience, AI was most effective as a modeling assistant rather than an autonomous design agent.

Where each new claim comes from in `main.tex`:

| Claim | Source |
|---|---|
| Under $200 plus a balance; about two orders of magnitude below a commercial dosing head | Results, "The dosing module" |
| Every 1 g dose on seven powders within ±5%; all nine 1 g doses on the three research-relevant powders within 10 mg (1%) | Results, closed-loop dosing (24 of 39 valid 1 g doses passed overall) |
| Glove-box run controlled by an AI agent over the network | "A first trial in a glove box" (24 July 2026, qualitative) |
| About 8 g of AlSi10Mg weighed into a charge for the ultrasonic atomizer | Outlook (late September 2026) |
| Parts later recreated in Fusion 360 (covered only by "first" in the abstract) | "How the parts were designed" |

## Decisions and feedback so far

- **Starting point:** the Utah abstract, in past tense, keeping its structure
  and flow, without adding unnecessary details.
- **Removed as no longer accurate:** "up to 30 reservoirs" and the ±0.1 mg
  stretch goal (proposal targets); "cross-contamination characterization"
  (now prevented by design, per PR #78); "the engineers have not opened a
  traditional CAD graphical interface" (parts were later redrawn in
  Fusion 360, and the tested auger is a recreation); the vibration motor (its
  driver never worked).
- **Version 2 rejected** because it paraphrased too much and converged on the
  `main.tex` abstract. Later versions keep Utah sentences wherever possible.
- **Version 4** responds to "last half, put more focus on how great the powder
  doser is".

## Open questions for review

1. Version 4 cites only the best 1 g results. The overall 24 of 39 at 1 g, and
   the weaker 50 and 200 mg results (14 and 18 of 30), are omitted; the
   `main.tex` abstract states both. About 11 words of room remain for a
   clause such as "smaller doses were less reliable".
2. The glove-box trial was qualitative (its first salt dose ended 4.4 mg
   short). Is "ran inside an inert-atmosphere glove box under the control of
   an AI agent" the right weight for it?
3. Version 4 drops most of the AI lessons (specificity, spatial reasoning,
   time spent on corrections). Bring one back at the cost of a doser
   sentence?
4. Once a version is chosen, it replaces the abstract in `main.tex`
   (and `../submission/GUIDELINES-AUDIT.md` / `SUBMISSION-PLAN.md` word counts
   need updating).

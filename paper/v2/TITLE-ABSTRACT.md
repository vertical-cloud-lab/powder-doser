# Title and abstract (v2)

Step one of the restart agreed on 27 Oct: title, abstract, then the figures and
tables, before the full manuscript is rebuilt around them
([transcript](../meeting_2026-10-27/TRANSCRIPT-corrected.md), 33:18–34:12).
`main.tex` is unchanged.

## Title

Pick one (or edit). The current title is listed first for reference.

- [ ] **Current:** An open-source, 3D-printed auger powder doser designed with generative artificial intelligence
- [ ] **Utah AI Convergence poster:** An Open-Source, Low-Cost Powder Doser Designed with Agentic AI and Generative CAD for Autonomous Alloy Discovery
- [x] **Proposed:** An open-source powder doser for autonomous alloy discovery, designed by engineers and modelled by AI agents
- [ ] **Shorter:** Engineers design, AI agents model: an open-source powder doser for alloy discovery

Why the proposed one: it names what the paper delivers (the doser, for alloy discovery)
and the division of labour the paper argues for (engineers design, AI models), which is
also the abstract's last two sentences. Sam asked not to "dumb it down" (00:40); the
current title reads as a general-audience title and hides the alloy-discovery purpose.

## Abstract

**Version 5 (249 words): version 4 plus the two changes asked for at the meeting.**
Version 4 is the candidate from the 28 Oct session
([`../abstract_2026-10-28/`](../abstract_2026-10-28/README.md)).

> Additive manufacturing of aerospace structural alloys depends on rapid, reproducible exploration of powder feedstocks, yet accurately metering and blending dry metal powders remains a largely manual bottleneck in research laboratories. Commercial dispensers are often cost-prohibitive and poorly matched to alloy-focused, many-powder workflows, and existing open-source designs have not been rigorously developed or tested for laser powder bed fusion (L-PBF). We developed an open-source, low-cost, modular powder doser for metal and feedstock powders, intended for a self-driving materials-discovery loop in which dosed powders feed ultrasonic atomization and L-PBF of aerospace alloys. The first module, a single channel built from 3D-printed parts and off-the-shelf electronics, cost under $200 plus an analytical balance, roughly two orders of magnitude below commercial dosing heads. In closed loop, every 1 g dose on seven of 13 tested powders landed within ±5% of the target, and the nine on AlSi10Mg, coarse silicon, and sodium sulfate landed within 1%; smaller doses were less reliable. The doser also ran inside an inert-atmosphere glove box under the control of an AI agent, and weighed AlSi10Mg into a charge that our ultrasonic atomizer turned into new powder. Its parts were designed by engineers and, from April to July 2026, modeled by AI agents (GitHub Copilot with Claude Opus 4.7–4.8; Zoo Design Studio's Zookeeper): engineers supplied dimensions, sketches, and manufacturing constraints; AI modeled the parts as editable parametric scripts; and engineers reviewed, printed, and iterated. AI was most effective as a modeling assistant rather than an autonomous design agent.

What changed from version 4, and why:

| Change | Reason |
|---|---|
| Dates and models of the AI modelling: "from April to July 2026 … GitHub Copilot with Claude Opus 4.7–4.8; Zoo Design Studio's Zookeeper" | Sterling, 03:40: say between which dates and with which models, which also shows how fast the project moved. Dates: first Copilot CAD session 23 Apr, last 30 Jun; Zoo subscription cancelled by 17 Jul ([`../figures/data/ai_tools_timeline.csv`](../figures/data/ai_tools_timeline.csv)) |
| "the nine on AlSi10Mg, coarse silicon, and sodium sulfate" replaces "all nine 1 g doses on the three alloy-relevant powders" | Version 4's wording was wrong: fine silicon (−325 mesh) is also alloy-relevant and none of its six 1 g doses passed, and sodium sulfate is not an alloy powder |
| "smaller doses were less reliable" | Open question 1 of the 28 Oct README; 14 of 30 at 50 mg and 18 of 30 at 200 mg (Table 3 below) |
| Cut "precise metering of", "Bayesian-optimization", "exact", "In our experience" | Room for the above within DD's 250 words |
| Cross-contamination stays out | Sterling, 02:49: the design prevents it, so the paper points to the multi-doser instead |

Still open from the 28 Oct README: whether the glove-box sentence carries the right weight
(question 2), and whether one AI lesson should come back (question 3). Also: Claude Code
(Opus 5.5) assembled the design in Onshape in October; the abstract leaves that out
because it is not part of how the tested parts were modelled.

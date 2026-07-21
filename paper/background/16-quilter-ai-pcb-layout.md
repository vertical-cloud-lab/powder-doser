_Hands-on landscape note on **Quilter.ai** (commercial autonomous PCB-layout
SaaS), written in response to @sgbaird's request on PR
[#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4635695822)
("have a look at quilter.ai, look at reddit, too") and @lbwinters' pointer to its
free tier
([comment](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4635685642)).
Sources are vendor pages, third-party reviews, and community/benchmark posts,
cited inline by URL; the "no public API" claim is verified empirically by
[`quilter_probe.py`](quilter_probe.py) (read-only). Captured 2026-06._

# Quilter.ai for the powder-doser control PCB

## TL;DR

Quilter.ai is a **physics-driven AI for PCB _layout_ (placement + routing) only**
— not schematics, not simulation. It ingests a *complete* schematic + board file
(outline, footprints, netlist) and returns placed-and-routed candidates in your
**native ECAD format, including KiCad**, with no proprietary lock-in
(<https://docs.quilter.ai/get-started/quickstart>;
<https://www.quilter.ai/pricing>). It is the natural *downstream* complement to
note [`14`](14-pcb-design-recommendations-for-powder-doser.md)'s recommendation
(SKiDL/atopile/KiCad for schematic-as-code) — it targets exactly the "full-board
placement/routing still wants a human pass" gap that note `14` flagged.

**The catch for us:** Quilter is **web-UI-only** (`app.quilter.ai`). There is **no
public API / CLI / SDK**, so it **cannot be driven from our headless GitHub /
Copilot CI** — it is a manual, human-in-the-loop tool, not a Copilot-automatable
one. The free tier is genuinely free for academic/personal use (no flux.ai-style
download paywall), but the free tier **trains Quilter's engine on your board
metadata/files**, which is acceptable for open hardware but worth a conscious
choice.

## What it is (and is not)

- **Layout automation, not schematic generation.** Quilter's own docs explicitly
  say "We cannot generate a schematic for you" and point users to Flux.ai / CELUS
  / Circuit Mind for that step (<https://docs.quilter.ai/get-started/quickstart>).
  It also does not do circuit simulation or analysis
  (<https://www.quilter.ai/free-ai-pcb-design>).
- **Inputs:** a complete schematic in **Altium, KiCad, Cadence Allegro, or
  Siemens Xpedition**, plus a linked board file with a valid outline, footprints,
  and a netlist. Pre-placed components and pre-routed copper are treated as
  "locked," so you can hand-route RF/HV/critical nets and let Quilter do the rest
  (<https://docs.quilter.ai/get-started/quickstart>; <https://www.quilter.ai/pricing>).
- **Outputs:** multiple placed/routed candidates exported back to the original
  tool's native format — KiCad is first-class — with "no proprietary format and
  no lock-in" (<https://www.quilter.ai/pricing>).

## Can it run inside our GitHub/Copilot environment?

**No — UI only, verified.** `quilter_probe.py` (read-only, stdlib) shows:

- `api.quilter.ai` and `api.app.quilter.ai` **do not resolve** (DNS failure).
- Every probed REST-style path (`app.quilter.ai/api/`, `.../api/v1/jobs`,
  `www.quilter.ai/api/`, `docs.quilter.ai/api-reference`) returns the **SPA HTML
  shell or 404**, never JSON.

So the only interaction model is "log into `app.quilter.ai`, upload files in the
browser, download candidates." That is the same class of blocker as **Flux.ai**
(probed separately for this PR): not scriptable, not headless, not version-
controllable as part of CI. (Independent reviews reach the same conclusion: no
documented public API/CLI; enterprise/private-beta API access is "contact sales,"
e.g. <https://aichief.com/ai-development-tools/quilter/>.) Notably, the
competing **DeepPCB** *does* expose an API and integrates into existing EDA flows
(<https://deeppcb.ai/deeppcb-vs-quilter-open-source-routing-compared-2026/>),
which matters more than raw quality if CI automation is the goal.

## Free tier & pricing (relevant to an academic open-hardware project)

- **Free tier:** unlimited iterations and "all Quilter product features" for
  **academic, personal, and eligible pre-revenue professional use** (eligibility:
  < 10 employees and < \$50K/yr revenue) — the powder-doser project qualifies
  (<https://www.quilter.ai/free-ai-pcb-design>).
- **Data/privacy caveat (free tier):** Quilter "uses your board's metadata
  (outline, component footprints, constraints) and/or input files to generate
  training puzzles that improve our design engine"; only Enterprise designs are
  "never used for … training" (<https://www.quilter.ai/free-ai-pcb-design>). For
  an open-hardware project whose boards are public anyway this is low-risk, but it
  should be a deliberate choice.
- **Paid model:** pay **per project by unrouted pin count** (pre-routed pins are
  free), unlimited iterations per project, parallel jobs, cloud or self-hosted on
  AWS (<https://www.quilter.ai/pricing>). This is a different shape from the
  flux.ai billing complaints @sgbaird flagged
  ([reddit warning](https://www.reddit.com/r/PCB/comments/1t476x4/warning_fluxai_billing_traps_and_deceptive/)):
  the free tier does not gate downloads behind per-credit charges.

## Community / Reddit sentiment — and what to trust

Sentiment is **cautiously positive but skeptical**, and the signal is muddied by
two things worth calling out:

- **Name collision:** TrustPilot/“www.quilter.com” reviews are a **UK financial-
  services firm**, *not* Quilter.ai — ignore those. (The Edison literature notes
  `07`/`14` also conflate the commercial product with an academic RL placement
  baseline called "quilter"; the company-vs-baseline distinction matters.)
- **Vendor benchmarks cut both ways:** Quilter's own "months → minutes" numbers
  are unverifiable internal benchmarks, and the most-cited head-to-head
  (<https://deeppcb.ai/deeppcb-vs-quilter-open-source-routing-compared-2026/>) is
  published by **competitor DeepPCB**, so treat it as directional, not neutral.

That benchmark (three public open-source **KiCad** boards, upload-and-route, no
manual tuning) reported DeepPCB ahead of Quilter on every board:

| Board (airwires) | Metric | DeepPCB | Quilter |
| --- | --- | --- | --- |
| STRF (98) | completion / vias | 99% / 29 | 94% / 58 |
| PocketBeagle (290) | completion / vias | 96% / 135 | 82% / 163 |
| BeagleConnect Freedom (414) | completion / vias | 97% / 191 | 87% / 235 |
| **Average** | completion | **97.3%** | **87.7%** |
| | time to first result | 1–2 min | 15–20 min |

Recurring community themes (r/PCB, EEVblog-style critique, review aggregators):
strong **time savings** and DRC-clean, physics-aware output on **moderate-
complexity** boards; but **excess vias**, **sub-100% completion** on dense/high-
speed boards (so manual cleanup remains), and slower first results. Consensus
"you still need an engineer for the final ~10% on hard boards"
(<https://www.futurepedia.io/tool/quilter>; <https://declom.com/quilter/>).
Best-fit envelope quoted across reviews: **< ~1000 pins / < ~100 components** —
which comfortably covers the powder-doser RP2040 + stepper/solenoid/servo +
HX711 control board.

## Bottom line for the powder doser

- **Good fit on capability:** native KiCad in/out, aimed squarely at moderate-
  complexity motor/sensor control boards, free for our academic use, and it
  attacks the exact placement/routing step note `14` said still needs a human.
- **Bad fit on automation:** **no API → not CI/Copilot-drivable.** It would be a
  **manual, browser-based, human-in-the-loop** step, not part of the repo's
  reproducible headless pipeline.
- **Suggested role:** keep the **schematic-as-code** source of truth in
  SKiDL/atopile/KiCad (note `14`), export the KiCad board, then optionally use
  Quilter's **free tier** as an *assistive, manual layout pass* on candidate
  boards — comparing its output against KiCad's own router and, if CI-scriptable
  routing is wanted, against **DeepPCB's API**. Accept the free-tier
  train-on-your-data terms knowingly (fine for public hardware).

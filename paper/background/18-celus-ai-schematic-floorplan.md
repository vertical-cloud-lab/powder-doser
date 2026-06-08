_Hands-on landscape note on **CELUS** (the CELUS Design Platform), written in
response to @lbwinters' and @sgbaird's requests on PR
[#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654166992)
to research CELUS as the **intermediate step** between an LLM topology tool (e.g.
LaMAGIC) and an autonomous router (Quilter / DeepPCB), and to collect reviews.
It is the counterpart to notes [`16`](16-quilter-ai-pcb-layout.md) (Quilter) and
[`17`](17-deeppcb-ai-pcb-routing.md) (DeepPCB). Sources are vendor pages,
third-party reviews, and community posts, cited inline by URL; the "no public
API" finding is verified empirically by [`celus_probe.py`](celus_probe.py)
(read-only). Captured 2026-06._

# CELUS for the powder-doser control PCB (the topology → starter-board bridge)

## Why this note exists

@lbwinters' key observation on PR #76
([comment](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4653987091)):
neither **Quilter** nor **DeepPCB** can go from a *topology schematic + component
list* to a finished board — **both require a fully-defined starter board** (a
captured schematic with footprints, a board outline, and design rules) before
they can place/route. (The deeppcb.yaml the team provided confirms this: a job
needs a board file with footprints + netlist; routing only starts from that.) So
a workflow of **LaMAGIC (topology) → Quilter/DeepPCB (layout)** has a missing
middle: something that turns the topology + parts into a **router-ready KiCad
starter board**. CELUS is the tool @lbwinters found that claims to fill exactly
that gap — this note evaluates it for our headless, CI-driven project.

## TL;DR

CELUS is an **AI front-end-of-design platform**: you give it high-level
requirements or a **functional block diagram** (or use its natural-language
Design Assistant), and its engine assembles a **complete, connected schematic +
BOM** from modular pre-verified blocks called **CUBOs**, then exports a
**complete KiCad project package — schematic, symbols, and footprints —** ready
to "update the PCB, create the ratsnest, begin placement and routing"
(<https://www.celus.io/news/pcb-layout-all-in-one-solution-with-celus-kicad>;
<https://www.celus.io/news/define-design-develop>). On **capability** this is the
best match in this survey for the topology→starter-board bridge: its output is
precisely the footprinted, netlisted KiCad starter board that Quilter/DeepPCB
need as input.

**The catch for us is the same one that sinks Quilter/Flux.ai: it is a
login-gated web app with no public API.** `celus_probe.py` confirms there is no
documented developer/REST surface, so CELUS **cannot be driven from our headless
GitHub / Copilot CI** — it is a manual, browser-based, human-in-the-loop step.

## What it is (and is not)

- **A "systems-level architecture compiler," not a router.** You input function,
  not individual passives: draw blocks (e.g. "motor driver" → "MCU" → "sensor")
  or describe the system to the Design Assistant; clicking **Resolve** has the AI
  search its component + CUBO database for real manufacturer parts that satisfy
  the block requirements and auto-wires the underlying schematic
  (<https://www.celus.io/news/define-design-develop>;
  <https://grokipedia.com/page/CELUS_Design_Platform>).
- **CUBOs = validated, reusable circuit blocks** ("schematic Lego") that bundle
  the main component **and** its required support circuitry (passives,
  connectors), with electrical constraints and footprints already attached — so
  you don't hand-build symbols/footprints
  (<https://innoelectro.com/en/lectures/from-rough-idea-to-connected-schematic-in-minutes-supercharging-hardware-design-with-celus>).
- **Output = a complete KiCad (or Altium / PADS / Cadence) project package.**
  The KiCad export "won't need additional libraries or footprints… included in
  the project package, allowing you to update the PCB, create the ratsnest, begin
  placement and routing"
  (<https://www.celus.io/news/pcb-layout-all-in-one-solution-with-celus-kicad>,
  Jul 2024). That is exactly the **starter board** the routers require.
- **It is not** an autonomous placement/router or a simulator — it stops at
  schematic + BOM + (preliminary) floorplan and hands off to your ECAD/router
  (so it sits *upstream* of Quilter/DeepPCB, not in competition with them).

## Can it run inside our GitHub/Copilot environment?

**No — web-UI / login-only, verified.** `celus_probe.py` (read-only, stdlib)
shows:

- `www.celus.io`, `app.celus.io`, `api.celus.io`, `developer.celus.io`,
  `docs.celus.io` all **resolve** (one CloudFront fleet), but
- `api.celus.io` (and `/v1/`) returns a **bare framework `404 page not found`**
  (no public API root/version), `app.celus.io` is a **login-gated Next.js SPA**,
  and there is **no working `developer.`/`docs.` portal** and no
  `www.celus.io/developers` page — i.e. **no documented public API / CLI / SDK**.

Independent reviews reach the same conclusion: CELUS "does not prominently
advertise a public API… most automation is via the web interface, not a
developer-facing REST or scripting API," and EDA hand-off is **via file export,
not a programmable API**
(<https://morepcb.com/open-source-ai-pcb-design-tools-2026-kicad-flux-celus/>).
So using CELUS means: log into `app.celus.io`, build the design in the browser,
download the KiCad package by hand. That is the **same blocker class as Quilter
and Flux.ai** (notes `16`/`15`) — not headless, not scriptable, not
version-controllable as a CI step. (Contrast **DeepPCB**, note `17`, which *does*
have a real public API — but DeepPCB only routes, it does not bridge topology to a
starter board.)

## Free tier, reviews, and reputation

- **Free tier:** CELUS offers free sign-up and immediate designing; the entry
  tier is reported sufficient for hobby / small / proof-of-concept projects, with
  paid plans (pricing on request) for advanced/collaboration features
  (<https://www.celus.io/solutions/engineers>;
  <https://morepcb.com/open-source-ai-pcb-design-tools-2026-kicad-flux-celus/>).
  An academic open-hardware board like ours fits the free-tier envelope.
- **Sentiment (engineering forums / reviews):** generally **positive on
  time-savings** for the front end — strong at turning natural-language
  requirements or block diagrams into a working schematic + supply-chain-aware
  BOM, and viewed as **more mature at schematic automation** than Flux.ai/JITX —
  but with the consistent caveat that it **does not replace expert-driven layout,
  final DRC, and review**, especially on non-trivial boards
  (<https://www.quilter.ai/blog/a-2026-ranking-of-ai-first-pcb-design-platforms-quilter-vs-jitx-vs-celus>;
  <https://www.powerelectronicsnews.com/celus-design-platform-revolutionizes-electronics-design-with-ai/>).
  Reported scale ~23k engineers / ~30k projects
  (<https://www.celus.io/solutions/engineers>). **Trust caveat:** the most
  detailed CELUS-vs-rivals ranking is published by **competitor Quilter**, so
  treat its relative ordering as directional, not neutral (the same caution
  flagged for the DeepPCB-vs-Quilter benchmarks in notes `16`/`17`).
- **Mixed-signal caveat for *our* board:** CELUS assembles function from CUBOs
  and supply-chain-optimizes parts, but the motor + load-cell power/ground
  partitioning (keeping DRV8871/Tic stepper noise off the HX711 front end) is the
  kind of "electrical intent" these tools don't fully own — expect to review the
  generated schematic, not trust it blind.

## Where CELUS fits the powder-doser pipeline

The pipeline @lbwinters sketched, with the gap filled:

```
topology / requirements
   │  (LaMAGIC or an LLM: circuit topology)
   ▼
CELUS  ─ block diagram / NL → connected schematic + BOM + footprints
   │     → native KiCad project package      ◀── the missing "starter board"
   ▼
KiCad  ─ verify board outline, lock connectors/mounting holes, set DRC/stackup
   │
   ▼
Quilter (manual, unmetered)  ── or ──  DeepPCB (scriptable API, metered)
   │     autonomous placement + routing
   ▼
human review of dense / mixed-signal nets → manufacture
```

- **Good fit on capability:** CELUS is the cleanest answer to "topology + parts →
  router-ready KiCad starter board," and its native-KiCad output drops straight
  into the note-`14` KiCad-centric plan and then into Quilter/DeepPCB.
- **Bad fit on automation:** **login/web-UI only → not CI/Copilot-drivable.** It
  is a manual step, like Quilter and Flux.ai.
- **Honest alternative for the bridge that *is* automatable:** the
  **design-as-code** path (atopile / tscircuit / SKiDL / KiCad Python + IPC +
  `kicad-cli`) can also emit a footprinted, netlisted KiCad project from a
  higher-level text description and **does** run headlessly in CI — at the cost of
  writing the description by hand (which the Copilot agent itself can do as a
  baseline, as @sgbaird noted). The Edison literature and analysis runs added for
  this PR (`edison_run_topology_to_board*.py`, notes `19`/`20`) weigh CELUS
  against those code-first options for this specific board.

## Bottom line

CELUS is the **most capable** topology→starter-board bridge surfaced so far and
exports exactly the **native KiCad** package Quilter/DeepPCB need, with a free
tier we qualify for — but it is **web-UI / login-only with no public API**
(verified), so it is a **manual, human-in-the-loop** step, not a headless CI one.
Recommended role: use CELUS (free tier) as an assistive, browser-based way to go
from a block diagram to a KiCad starter board, then route with **Quilter**
(manual) or **DeepPCB** (scriptable, metered — and its API is confirmed reachable
from our sandbox, see note `17`). For the part of the bridge we actually want to
*automate* in CI, prefer the design-as-code route from note `14`.

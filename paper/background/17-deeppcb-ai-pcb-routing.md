_Hands-on landscape note on **DeepPCB** (InstaDeep's commercial autonomous
PCB-routing SaaS), written in response to @sgbaird's request on PR
[#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4635908170)
("check on DeepPCB similar to what you did for quilter.ai, e.g., reddit threads")
and @lbwinters' note that DeepPCB's free tier is limited to one board / 30 min of
runtime
([comment](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4635875109)).
It is the direct counterpart to note [`16`](16-quilter-ai-pcb-layout.md)
(Quilter.ai). Sources are vendor pages, third-party reviews, and
community/benchmark posts, cited inline by URL; the central "DeepPCB **does** have
a real public API" claim is verified empirically by
[`deeppcb_probe.py`](deeppcb_probe.py) (read-only). Captured 2026-06._

# DeepPCB for the powder-doser control PCB

## TL;DR

DeepPCB is a **reinforcement-learning, cloud-native AI for PCB _placement +
routing_ only** — not schematics, not simulation — built by **InstaDeep** (now
BioNTech) and run on Google Cloud
(<https://deeppcb.ai/>;
<https://instadeep.com/2024/09/instadeep-introduces-deeppcb-pro-an-ai-powered-pcb-design-tool/>).
Like Quilter (note [`16`](16-quilter-ai-pcb-layout.md)) it ingests an *unrouted*
board (outline, footprints, netlist) from a standard EDA tool — **KiCad**, Altium,
Eagle, EasyEDA — and streams back placed-and-routed candidates you download in
your native format. So it, too, is a *downstream* complement to note
[`14`](14-pcb-design-recommendations-for-powder-doser.md)'s schematic-as-code plan,
hitting the same "placement/routing still wants a human pass" gap.

**The decisive difference from Quilter for us:** DeepPCB exposes a **real public
HTTP API** (`api.deeppcb.ai`, documented Swagger spec, account/API-key gated), so
unlike Quilter/Flux.ai it **can in principle be driven from our headless GitHub /
Copilot CI**. The catch is economic, not technical: the free tier is **one board
and ~30 minutes of routing time**, and beyond that it is **pay-per-minute**
(0.5 AI credit ≈ \$0.50/min), so an iterate-in-CI loop gets expensive fast — the
exact concern @lbwinters raised.

## What it is (and is not)

- **Routing/placement automation, not schematic generation.** DeepPCB takes a
  *complete* board with footprints and a netlist and does placement + geometric
  routing; you still need a separate EDA tool (KiCad in our case) for schematic
  capture (<https://deeppcb.ai/>;
  <https://deeppcb.ai/help/>). Same division of labour as Quilter.
- **RL-based, cloud-only.** It runs entirely on InstaDeep's cloud (Google Cloud),
  using reinforcement learning to generate a *stream* of diverse candidate
  layouts with per-candidate metrics, rather than one fixed result
  (<https://deeppcb.ai/deeppcb-api-your-pcb-design-ai-agent/>). There is no local
  install and no offline mode.
- **Inputs/outputs:** upload an unrouted board from KiCad/Altium/Eagle/EasyEDA,
  download placed-and-routed solutions back in major formats — no proprietary
  lock-in claimed (<https://deeppcb.ai/>; <https://deeppcb.ai/help/>).
- **Board envelope (free tier):** up to **4 layers, ~150 airwires, ~100
  components, ~2200 pins** — comfortably covering the powder-doser RP2040 +
  stepper/solenoid/servo + HX711 control board
  (<https://deeppcb.ai/pricing/>; <https://deeppcb.ai/help/>).

## Can it run inside our GitHub/Copilot environment?

**Technically yes — there is a real API — but the free tier makes CI iteration
impractical.** `deeppcb_probe.py` (read-only, stdlib) shows, in direct contrast to
the Quilter probe:

- `api.deeppcb.ai` **resolves** to a real backend host (distinct from the static
  marketing site) and answers as an **ASP.NET `Kestrel` API server**, returning a
  plain-text `200 Healthy` at `/health` and bare `404`s (no body) on unknown
  routes — i.e. a genuine control plane, **not** an SPA HTML shell.
- DeepPCB documents the integration explicitly: sign up, request an API key, and
  use the Swagger spec under `api.deeppcb.ai` to call placement/routing from your
  own tooling (<https://deeppcb.ai/deeppcb-api-your-pcb-design-ai-agent/>).

Compare Quilter, where `api.quilter.ai` does **not** resolve and every path is the
SPA shell (note [`16`](16-quilter-ai-pcb-layout.md)): DeepPCB is the one
autonomous-layout vendor in this survey that is actually **scriptable/headless**.
So a CI step like "export unrouted KiCad board → POST to DeepPCB → poll → download
routed board" is buildable. **But two real blockers remain:**

1. **API key requires a manual account/credit setup** (no anonymous/programmatic
   signup), and the key/credits would have to be provisioned as a CI secret — a
   human, paid prerequisite, not a self-contained headless step.
2. **Cost model punishes iteration.** Free = 1 board + ~30 min; after that it is
   **pay-as-you-go per minute** (<https://deeppcb.ai/pricing/>). A Copilot loop
   that re-routes on every commit would burn credits quickly, exactly as
   @lbwinters flagged. Quilter's free tier (unlimited iterations, pay-per-pin
   only when paid) is friendlier for repeated runs, but is *not* automatable;
   DeepPCB is automatable but *metered by time*.

## Update — authenticated API ping confirms it (key now provisioned)

@sgbaird provisioned a real `DEEPPCB_API_KEY` as a repo secret and asked
([comment](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654166992))
whether the API can actually be reached from the sandbox. It can.
[`deeppcb_api_ping.py`](deeppcb_api_ping.py) (read-only, **consumes no credits**)
authenticates with the key over **HTTPS** (`https://api.deeppcb.ai`; the public
OpenAPI doc lists `http://`, but TLS works and is used) via the
`x-deeppcb-api-key` header and successfully calls the three free/read-only
endpoints:

- `GET /api/v1/apiuser/credit-flow` → `200`, account summary (this trial key:
  **0.0 credits, 0 boards created** — so no routing/placement can be run until
  credits are added);
- `GET /api/v1/boards/board-schema` → `200`, the ~42 KB "DeepPCB File Format"
  JSON Schema;
- `GET /api/v1/boards/constraints-schema` → `200`, the board-constraints schema.

The ping deliberately **does not** touch the credit-consuming endpoints
(`POST /boards`, `PATCH /boards/{id}/confirm` with `jobType` Routing/Placement),
so it is safe to re-run in CI as a connectivity/auth check. This upgrades the
earlier unauthenticated `deeppcb_probe.py` finding from "a real API appears to
exist" to "the API **authenticates and answers from our environment**" — DeepPCB
is genuinely wirable into the headless pipeline. The only remaining gate is
economic: the provisioned account has **0 credits**, so an actual route still
needs the free trial (1 board / ~30 min) or paid credits, consistent with the
cost caveat below.

## Free tier & pricing (relevant to an academic open-hardware project)

- **Free trial:** **30 minutes of AI routing time, one board**, within the
  4-layer / ~150-airwire / ~100-component / ~2200-pin envelope; **no stop/resume**
  on the free tier (<https://deeppcb.ai/pricing/>; <https://deeppcb.ai/help/>).
- **Paid (pay-as-you-go):** **0.5 AI credit ≈ \$0.50 per minute** (30 credits/hr).
  Bundles quoted around **\$30 / 1 hr, \$280 / 10 hr (~\$28/hr), \$800 / 30 hr
  (~\$27/hr)**; paid plans raise the layer/airwire/component ceilings and add
  stop/resume (<https://deeppcb.ai/pricing/>;
  <https://deeppcb.ai/deeppcb-api-your-pcb-design-ai-agent/>). The **API is the
  same price as the web app** — no surcharge for automation, but no free
  automation headroom either.
- **Net for us:** good enough to *trial* on our one control board for free; not a
  basis for an unattended, iterate-every-commit CI router without a budget.

## Community / Reddit sentiment — and what to trust

Sentiment is **mixed and more skeptical than Quilter's**, weighted toward expert
critique of output quality:

- **r/PrintedCircuitBoard / EEVblog:** the most-cited grassroots feedback is
  critical — engineers calling early demo/board results "horribly routed" on even
  *simple* boards, and EEVblog's hands-on test flagging aesthetic/DRC concerns and
  questioning manufacturable quality vs. a human router
  (<https://www.reddit.com/r/PrintedCircuitBoard/comments/16clihg/deeppcb_pure_aipowered_cloudnative_printed/>;
  <https://www.eevblog.com/forum/blog/eevblog-1535-deeppcb-ai-autorouting-tested!/>).
- **Enterprise/marketing:** InstaDeep's own customer stories report large
  time savings (prototype-ready layouts in hours), but these are vendor sources,
  not neutral reviews
  (<https://instadeep.com/2024/09/instadeep-introduces-deeppcb-pro-an-ai-powered-pcb-design-tool/>).
- **DeepPCB-vs-Quilter benchmarks cut both ways — mind who publishes them.** The
  benchmark that favors DeepPCB (97.3% vs 87.7% avg completion, fewer vias, faster
  first result) is published by **DeepPCB itself**
  (<https://deeppcb.ai/deeppcb-vs-quilter-open-source-routing-compared-2026/>);
  Quilter's own 2026 guide instead casts DeepPCB as the more *complexity-limited*
  of the two
  (<https://www.quilter.ai/blog/the-2026-guide-to-autonomous-pcb-design-quilter-vs-deeppcb-vs-flux-ai>).
  Both are vendor self-assessments — treat each as directional, not neutral. (As
  with Quilter, beware the Edison notes `07`/`14` conflating these commercial
  products with academic RL routing baselines.)

Consensus best-fit envelope across reviews: **small-to-moderate boards** with a
human cleanup pass on the densest nets — which covers our control board, but with
the caveat that the "last ~10%" likely still needs manual touch-up.

## Bottom line for the powder doser

- **Capability fit:** native KiCad in/out, RL placement+routing aimed at exactly
  our moderate-complexity motor/sensor board; **free for one trial board**.
- **Automation fit (the differentiator):** **DeepPCB is the only autonomous-layout
  vendor here with a real, documented public API** (verified: `api.deeppcb.ai`
  Kestrel backend + `/health` + Swagger), so it *is* CI/Copilot-scriptable —
  unlike Quilter/Flux.ai. **But** it needs a manually provisioned, paid API
  key, and its **per-minute metering** makes an iterate-on-every-commit loop
  costly; the free tier is a single 30-minute board.
- **Suggested role:** keep the **schematic-as-code** source of truth in
  SKiDL/atopile/KiCad (note [`14`](14-pcb-design-recommendations-for-powder-doser.md)),
  then evaluate DeepPCB as the **scriptable routing back end** for a *deliberate,
  budgeted* CI pass (its API is the one that fits the repo's headless pipeline),
  while using **Quilter's free tier** for unmetered manual iteration. Net: pairs
  naturally with @lbwinters' topology→layout idea — LaMAGIC/SKiDL for the
  schematic, then DeepPCB (automatable, metered) or Quilter (manual, unmetered)
  for placement/routing — with a human review of the final dense nets either way.

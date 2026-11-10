# CADScribe (cadscribelabs.com) — evaluation, July 2026

Researched 2026-07-26 in response to
[PR #7 comment](https://github.com/vertical-cloud-lab/powder-doser/pull/7)
(sgbaird: "not sure we've tried AdamCAD or CADScribe"). Two parallel
web-research passes — product/company/API and sentiment/independent
evaluations — same archival convention as `leo-ai-evaluation.md` and
`adamcad-evaluation.md`. Vendor claims flagged as such; every bullet
carries its source URL.

## Disambiguation first (three "CADScribe"s exist)

- **cadscribelabs.com** — the text-to-CAD chatbot tested by Xometry Pro.
  **This is the one evaluated here.**
- **cadscribe.com** — an unrelated German CAD-services/training firm in
  Munich (verified by direct fetch). Not this.
- **aitools.inc/tools/cadscribe** — an "Unverified" directory listing
  describing a CAD-documentation tool that matches neither site;
  auto-generated noise. (There's also an unrelated Indian AutoCAD-tutorial
  YouTube channel named "@Cadscribe".)

## TL;DR verdict

CADscribe is a tiny (3 co-founders, no known funding), bootstrapped,
student-founded (HEC Paris, ~April 2024) browser chatbot for text-to-CAD.
Unlike AdamCAD it **does emit STEP** (BREP-backed, per the CEO: prompts are
"translated into a query language used to actually create the STEP file"),
and in Xometry's 7-tool test it actually scored **3/5 accuracy vs Zoo's
2/5** on their simple/medium prompts. But it is **not usable in this repo's
headless CI lanes today**:

1. **No API — and it's been "roadmap" for over two years.** Fabbaloo noted
   "API" as an in-development homepage feature in April 2024; in the Feb
   2026 Xometry interview the CEO still lists the API as a one-year-vision
   item. No docs site, no OpenAPI, no PyPI/npm packages, no GitHub org, no
   MCP server. The private backend (`/init_chat`, `/get?msg=...`,
   `/download_stl/{id}/{format}`) requires Clerk browser-session tokens —
   scripting it would mean scraping session auth, fragile and unauthorized.
2. **Quality ceiling below our needs.** Every independent test agrees:
   good for simple single parts (plates with holes, cylinders, basic
   gears), unreliable-to-failing beyond that — Xometry's manifold-block
   prompt "could not generate a model" (input-length cutoff, no useful
   error); TexoCAD found the same prompt gives three different models
   across runs; the CEO himself: "the quality of output is still not
   great… This applies to all text-to-CAD models right now."
3. **No parametric continuity.** No exposed code/history representation
   (unlike Zoo's KCL or CADAM's OpenSCAD); each chat refinement is
   effectively a fresh generation; Xometry's table lists Editing Support:
   None. That kills the iteration workflow we exercise on Zoo
   (`/ml/text-to-cad/iteration` keeping named parameters stable).
4. **Tiny operation.** ~1,000 monthly signups (vendor), "very few" paying
   customers, €4.99/mo premium, free tier capped at 10 messages, growth
   purely organic. Candid CEO, but no funding, no case studies, and near
   zero community footprint.

**Recommendation for this repo:** not adoptable — no API, no headless path,
quality below Zoo for our multi-feature parts despite the simple-part edge
in Xometry's scoring. Cheapest experiment if ever curious: the free
10-message tier in a browser. Revisit only if the long-promised API
actually ships.

---

## 1. Product & company

- Browser-based chat text-to-CAD: type a part description, get a model in
  ~5–15 s, iterate conversationally. **Exports: STEP and STL only** (the
  format dropdown in the production JS bundle contains exactly `step` and
  `stl`). React SPA, Clerk auth, Stripe billing; no desktop app, no CLI.
  https://cadscribelabs.com/ ;
  https://xometry.pro/en/articles/cadscribe-ai-interview/
- Pipeline (vendor-described): prompt → LLM → "a query language used to
  actually create the STEP file". The CEO declined to say whether the
  query language is proprietary or existing (he name-checks build123d as a
  peer approach); the geometry kernel and LLMs are undisclosed. Free tier
  runs "a less capable LLM since it costs pennies"; premium a "much
  bigger" model + optional thinking models.
- On failure the app returns a literal "fail" 3D model (the bundle ships
  `static/stl/fail.stl`) — noted with amusement by Fabbaloo.
  https://www.fabbaloo.com/news/introducing-cadscribe-a-text-to-3d-tool-for-quick-3d-parts-modeling
- Company: founded ~April 2024 by three data-science students at HEC Paris
  (originally a 3D-printing-marketplace idea, pivoted). CEO Dikens Celaj;
  the other two co-founders' names could not be verified. No
  Crunchbase/funding records — almost certainly bootstrapped. Vendor
  metrics: ~1,000 monthly signups, mostly students; paying customers
  "very few". https://xometry.pro/en/articles/cadscribe-ai-interview/
- Long-term strategy (CEO): either an "AI-first CAD editor" (Cursor
  analogy) or integrations with AutoCAD/Dassault/Onshape; near-term
  roadmap: API, dimension sliders, better UI.

## 2. Pricing

- No public pricing page (login-gated SPA; no `/pricing` route in the
  bundle). **Free: 10 prompts/messages** (Xometry, confirmed by a
  `free_messages` counter + hard upgrade gate in the bundle). **Premium:
  €4.99/month** (CEO, Feb 2026 interview) — bigger model, thinking-model
  toggle, "pretty much unlimited messages". Xometry's table lists
  $4.99/mo.

## 3. User sentiment

- **Essentially no community footprint**: 0 Hacker News stories/comments
  (all Algolia hits are false positives), no G2/Capterra listing,
  Trustpilot page 404s, never launched on Product Hunt.
- **Reddit launch was founder-seeded**: a late-March/April 2024 burst
  across r/3Dprinting, r/CNC, r/blender etc. from three team-linked
  accounts (one handle, betapekens, is embedded in the site's own JS
  bundle), nearly all posts score 1 / 0 comments. One thread earned a
  "reddit gave CADscribe the hug of death" comment; the single later
  organic mention (June 2024): "Last time I tried it it didn't work great
  though."
- **One genuine independent YouTube review** (3D Luke, Apr 2024, ~7.5k
  views, explicitly unsponsored): "I see the potential, but functionality
  is limited." https://www.youtube.com/watch?v=QD5RkOFKnxg

## 4. Independent evaluations & benchmarks

- **Xometry Pro "We Tested 7 Text-to-CAD Tools" (Aug 2025)** — the
  clearest independent signal, and the source of the mention that
  triggered this evaluation:
  - Simple prompt (20 mm cylinder): "performed well… producing usable CAD
    files." Medium (24-tooth gear, full specs): "geometry did not match
    the request." Complex (manifold block): "could not generate a model" —
    prompt-length cutoff, no useful error feedback. Creative prompts:
    "limited and schematic."
  - Verdict table: **Accuracy ★★★☆☆** (vs Zoo ★★☆☆☆, AdamCAD ★★★★☆),
    Creative ★☆☆☆☆, Exports STEP/STL, **Editing Support: None**, best use
    "Quick single-part generation for simple parts."
  - Note for our records: in Xometry's specific prompt set CADScribe
    out-scored Zoo on accuracy — worth remembering as a caveat on "Zoo is
    better", though Zoo's API, KCL parametric source, and iteration
    endpoints (which Xometry didn't test) are what actually matter for
    this repo. https://xometry.pro/en/articles/text-to-cad-tools-test/
- **All3DP ran a dedicated CADscribe test** (July 2025, "Does Text-to-CAD
  Model Generation Really Work?") — existence confirmed but the body is
  JS-loaded and unreadable from this runner, so its verdict is unknown.
  https://all3dp.com/2/ai-cad-model-generator-cadscribe/
- **TexoCAD review (Jan 2026)**: simple parts within ~5% dimensional
  tolerance; gears/sheet-metal unreliable; same prompt → three different
  models across runs; no parametric continuity between iterations;
  verdict "behind Zoo.dev in output quality."
  https://blog.texocad.ai/posts/cadscribe-review
- **Fabbaloo (Apr 2024)**: "10cm plate with central 4cm hole" worked
  first try; sphere-with-flat-top failed (returned the "fail" model);
  praised 10–15 s speed.
- **Academic benchmarks: zero appearances** — arXiv full-text search 0
  results; not in MUSE (2605.28579), Text2CAD-Bench (2605.18430), or
  CADBench (2605.10873). No Develop3D/Cadalyst/Hackaday/engineering.com
  coverage. No case studies, vendor or independent.

## 5. Programmatic access (the decisive part for this repo)

- **No API, SDK, docs, or keys.** `docs.`/`api.`/`app.cadscribelabs.com`
  don't resolve (DNS-checked); `/openapi.json` returns the SPA shell;
  PyPI `cadscribe` 404; npm 0 results; GitHub search 0 repos; no
  `cadscribe`/`cadscribelabs` org.
- What exists is a **private, undocumented REST backend** (Envoy-fronted):
  `/init_chat`, `/get?msg=...` (generation), `/get_free_messages`,
  `/reload_chat/{id}`, `/download_stl/{objectId}/{format}`, plus
  Clerk/Stripe routes — all requiring a Clerk browser-session bearer
  token (verified: unauthenticated calls return 401). No key issuance, no
  programmatic-use terms. Driving it from CI would mean scraping session
  tokens — fragile and unauthorized, same conclusion as Leo AI's private
  backend.
- API has been promised since launch: listed as in-development on the
  April 2024 homepage (Fabbaloo), still a roadmap item in the Feb 2026
  interview ("We're already talking to people who want to use this tool
  programmatically"). Nothing has shipped.

## 6. Fit against this repo's existing lanes

| Lane | What it gives us | CADscribe equivalent? |
|------|------------------|------------------------|
| CadQuery / build123d | Headless parametric BREP + STEP/STL/3MF in CI | ❌ browser-only chatbot; kernel undisclosed |
| Zoo ML-ephant (`/ai/text-to-cad`, iteration endpoints) | REST text-to-CAD returning KCL + STEP, parameter-stable iteration | ❌ no API (2+ years of roadmap); no code representation; no iteration continuity |
| Onshape REST | Headless upload/translate/export | ❌ nothing comparable; Onshape integration is a "long-term maybe" (CEO) |
| Interactive design assistance | Zoo Design Studio / Onshape UI | ⚠️ marginal: fine for a quick free-tier "pen holder"-class part; below our multi-feature envelope parts |

Net: CADscribe is the smallest and least CI-relevant of the tools
evaluated in this PR — an honest student project whose own CEO says the
output quality "is still not great". Its one notable datapoint is beating
Zoo on Xometry's simple-part accuracy scoring, which is a caveat worth
keeping, not a reason to switch. Revisit only if the API ships.

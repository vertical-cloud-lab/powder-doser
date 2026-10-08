# AdamCAD / Adam (adam.new) — evaluation, July 2026

Researched 2026-07-26 in response to
[PR #7 comment](https://github.com/vertical-cloud-lab/powder-doser/pull/7)
(sgbaird: "not sure we've tried AdamCAD or CADScribe"). Two parallel
web-research passes — product/company/API and sentiment/independent
evaluations — same archival convention as `leo-ai-evaluation.md`. Vendor
claims are flagged as such; every bullet carries its source URL.

## TL;DR verdict

Adam (YC W25, formerly "AdamCAD", now at **adam.new**) is a real, fast-moving,
open-source-adjacent text-to-CAD startup — the most organically discussed of
the tools we've evaluated (five substantive Hacker News threads, 100–215
points each). But like Leo AI it is **not usable in this repo's headless CI
lanes today**:

1. **No public API.** No `/api` or `/docs` page in the sitemap, `api.adam.new`
   404s, `docs.adam.new` has an expired cert, zero npm/PyPI packages, no MCP
   server, no CLI. Adam is an API *consumer* (it drives Onshape's REST API and
   FeatureScript under the hood), not a provider.
2. **Mesh-out, not BREP-out, on the standalone path.** The open-source CADAM
   app has the LLM write **OpenSCAD** compiled in-browser via WASM — exports
   are **STL/SCAD/DXF only, no STEP** (OpenSCAD has no BREP). BREP output
   exists only inside the Onshape/Fusion copilot, i.e. through a human-driven
   host-CAD session.
3. **Interactive-only delivery.** Browser web app + Onshape App Store /
   Fusion / Blender / SketchUp extensions. No desktop app, no headless mode,
   no Linux story anywhere in the docs or changelog.
4. **The one genuinely interesting artifact for us is CADAM itself** — GPL-3.0
   open source (~4.9k GitHub stars): LLM → OpenSCAD → WASM preview → parameter
   sliders. But self-hosting it headless would mean re-plumbing a browser app,
   at which point you'd just use OpenSCAD + an LLM directly — which our
   CadQuery/OpenSCAD lanes already cover with a real BREP kernel.

**Recommendation for this repo:** not adoptable for the CadQuery → STEP/STL
→ slicer CI pipeline (no API, no STEP, no headless). Its copilot pivot is
worth *watching* because it manipulates Onshape feature trees via the same
Onshape API we already drive — if they ever expose that agent as an API, it
would slot into our Onshape lane. The cheap experiment, if curious: the free
CADAM web app, or the Onshape copilot extension in the classroom account
(interactive only).

---

## 1. Product & company

Adam has pivoted twice; there are now three distinct product surfaces:

- **CADAM** (original viral text-to-CAD web app, open-sourced Sept 2025,
  GPL-3.0, ~4.9k stars): LLM writes OpenSCAD (BOSL/BOSL2/MCAD libs),
  compiled in-browser by OpenSCAD WebAssembly, Three.js preview,
  auto-generated parameter sliders. Exports **STL, SCAD, DXF** per the repo
  README — CSG/mesh pipeline, **no STEP**.
  https://adam.new/cadam/ ; https://github.com/Adam-CAD/CADAM
- **Adam Copilot** (Product Hunt launch July 1 2026, #5 of the day): AI
  assistant *inside* Onshape and Autodesk Fusion via native extensions —
  prompt-driven part edits, feature-tree cleanup, parametrization of dumb
  models. Geometry is computed by the host kernel (Onshape/Parasolid,
  Fusion); the agent "calls tools through the Onshape API and writes
  FeatureScript". https://adam.new/copilot ;
  https://www.producthunt.com/products/adam-cad-copilot
- **Current positioning (July 2026)**: "AI CAD Copilot for Hardware Teams" —
  CAD edits plus BOM management, RFQs, ECO packets, with
  Onshape/Fusion/SolidWorks, Arena, Slack, McMaster-Carr, Jira integrations.
  https://adam.new/
- Architecture philosophy (their blog "The Bitter Lesson of AI CAD"): they
  deleted a custom DSL in favour of LLMs writing CAD-as-code + screenshot
  based visual self-correction; BREP context serialized as explicit JSON;
  post-training small models on real CAD sessions.
  https://adam.new/blog/bitter-lesson-ai-cad ; https://adam.new/blog/research
- Disclosed LLMs: user-selectable frontier models — changelog lists Claude
  Sonnet 5 + GPT-5.5 (July 1 2026), GPT-5.6 (July 9), Grok 4.5 (July 13);
  the founder says Claude (Fable 5) is the default for agentic CAD tasks.
  Earlier HN threads: Gemini 2.5 → 3.1 Pro won their internal spatial
  reasoning evals. https://adam.new/changelog
- Company: Y Combinator W25, San Francisco, founded 2025 out of Zach Dive's
  UC Berkeley Master of Design thesis. Founders Zach Dive (CEO) and Aaron
  (Heteng) Li (CPO); a third co-founder ("Avi", CTO) appears only in
  aggregator sources. Team of ~4 per YC. **$4.1M seed** (Oct 31 2025, led by
  TQ Ventures; 468 Capital, Pioneer, Script Capital, Transpose; angels incl.
  Trevor Blackwell and Theo Browne).
  https://www.ycombinator.com/companies/adam ;
  https://techcrunch.com/2025/10/31/yc-alum-adam-raises-4-1m-to-turn-viral-text-to-3d-tool-into-ai-copilot/
- Vendor traction claims: 1M+ models generated, "tens of thousands" of users
  (relayed by TechCrunch, not audited).

## 2. Pricing

- The official https://adam.new/pricing page is JS-rendered and — notably —
  currently contains a live dev artifact: "Pricing and limits should be
  treated as product copy until finalized by the team."
- Search-indexed copy of that page (July 2026): **Pro $40/month, 10,000
  tokens/month** shared across CADAM + Onshape + Fusion copilots; Enterprise
  custom/usage-based. Unverified from a direct fetch.
- Older figures (TechCrunch Oct 2025 + third-party review July 2026):
  free tier with limited prompts, Standard $5.99/mo, Pro $17.99/mo.
  Pricing is clearly in flux mid-pivot.
- HN commenters on the May 2026 "AI CAD Harness" thread specifically
  criticized token-pricing opacity.

## 3. User sentiment

- **Hacker News is the primary organic source** — unusual among the tools
  we've evaluated (Leo AI had zero HN stories):
  - "Show HN: GPT image editing, but for 3D models" (Jun 2025, 188 pts):
    praise for quick print-usable generations; criticism of spatial
    reasoning failures (gridfinity, wall mounts) and topology cleanup.
    https://news.ycombinator.com/item?id=44182206
  - "Show HN: Open-sourcing our text-to-CAD app" (Sep 2025, 179 pts).
    https://news.ycombinator.com/item?id=45140921
  - "Show HN: AI CAD Harness" (May 2026, 101 pts): founder admission that
    "serious mechanical engineers don't want a black box that spits out an
    STL"; ME pushback ("text-to-CAD is… not helpful"), fear of hallucinated
    dimensions reaching the real world.
    https://news.ycombinator.com/item?id=47977694
  - "Launch HN: Adam (YC W25) – Open-Source AI CAD" (Jun 2026, 215 pts):
    real wins ("four custom bumpers printing") alongside hard failures (a
    connector generated from a datasheet had wrong pitch, wrong pin
    positions, missing pins).
    https://news.ycombinator.com/item?id=48572553
- **Formal review platforms: near zero.** No G2 review page, 0 Capterra, 0
  Trustpilot; Product Hunt launch got 273 upvotes but 0 written reviews;
  AlternativeTo has 1 review. No organic Reddit threads found; no
  independent in-depth YouTube reviews; no Develop3D/Cadalyst/All3DP/
  Hackaday coverage.
- Net pattern: genuine maker/hobbyist traction and unusually candid founder
  engagement, consistent professional-engineer skepticism on precision
  parts.

## 4. Independent evaluations & benchmarks

- **Xometry Pro "We Tested 7 Text-to-CAD Tools" (Aug 2025)** — the same
  test that panned Leo AI — was *favourable* on AdamCAD: 20 mm cylinder and
  24-tooth gear "generated accurately, with listed editable parameters";
  the high-complexity manifold came out simplified but with fillets and
  customizable channels; creative-mode outputs "not always ready for 3D
  printing". **Formats delivered: STL and SCAD** (consistent with the
  no-STEP finding). Positioned as the only tool bridging technical and
  creative workflows, with **Zoo better for geometric precision**.
  https://xometry.pro/en/articles/text-to-cad-tools-test/
- **Academic benchmarks: zero appearances.** Not in Text2CAD-Bench (arXiv
  2605.18430), MUSE (2605.28579), CADBench (2605.10873) — same pattern as
  Leo: published benchmarks test raw LLMs/research models, not commercial
  tools.
- Listicle coverage (RapidDirect "Best 8 AI CAD Tools", TheCADHub) is
  undisclosed-methodology content, one written by a competitor.
- No vendor case studies exist either — the homepage has no customer logos
  or testimonials; the closest thing to evidence is the HN anecdotes.

## 5. Programmatic access (the decisive part for this repo)

- **Sitemap has no /api, /docs, or /developers page**; `api.adam.new` →
  404; `docs.adam.new` → expired certificate; changelog contains no API,
  MCP, SDK, or CLI entries. https://adam.new/sitemap.xml
- **Zero packages**: npm search "adamcad" → 0 results; PyPI `adamcad` →
  404. No Adam MCP server in any MCP registry. GitHub org has exactly one
  public repo (CADAM).
- One aggregator claims "programmatic access via developer endpoints" —
  unsupported anywhere official; treat as hallucinated SEO copy.
- CADAM self-hosting is possible (GPL-3.0) but it's a browser app whose
  geometry engine is OpenSCAD-WASM running client-side, backed by
  TanStack/Supabase auth — no CLI, no headless mode. Re-plumbing it for CI
  ≈ "OpenSCAD + an LLM", which we already have better versions of.
- The copilot's programmatic substance is that *it* drives the **Onshape
  REST API + FeatureScript** — the same API this repo already calls
  directly with the classroom key.

## 6. Fit against this repo's existing lanes

| Lane | What it gives us | Adam equivalent? |
|------|------------------|------------------|
| CadQuery / build123d | Headless parametric BREP + STEP/STL/3MF in CI | ❌ CADAM is OpenSCAD-WASM in a browser: mesh-only, no headless |
| Zoo ML-ephant (`/ai/text-to-cad`, iteration endpoints) | REST text-to-CAD returning KCL + STEP, scriptable Judge loop | ❌ no API at all; Xometry rated Zoo better for geometric precision anyway |
| Onshape REST | Headless upload/translate/export, classroom docs | ⚠️ Adam's copilot *consumes* this same API interactively; nothing callable by us |
| Interactive design assistance | Zoo Design Studio / Onshape UI | ✅ plausible niche: Onshape copilot extension in the classroom account (human-driven) |

Net: Adam is the most credible *interactive* AI-CAD product we've looked at
(real open source, real organic users, honest founders), but it publishes
nothing a Linux CI runner can call. Revisit if (a) they expose the copilot
agent as an API, or (b) CADAM grows a server-side/CLI evaluation path.

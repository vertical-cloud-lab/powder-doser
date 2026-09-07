# Leo AI (getleo.ai) — evaluation, July 2026

Researched 2026-07-21 in response to
[PR #7 comment](https://github.com/vertical-cloud-lab/powder-doser/pull/7#issuecomment-4995563901)
(sgbaird, via the "shigley LLM" → Maor Farid LinkedIn-post trail). Four
parallel web-research passes: product/company, user sentiment, formal
evaluations/case studies, and programmatic-API access. Same archival
convention as `edison-c0f412d3-literature-synthesis.md`. Vendor claims are
flagged as such throughout; every bullet carries its source URL.

## TL;DR verdict

Leo AI is a credible, well-funded **interactive engineering-knowledge
copilot** (Q&A grounded in handbooks like Shigley's, calculations with
citations, PDM-aware part search, SolidWorks add-in) — but it is **not
usable in this repo's headless CI lanes today**:

1. **No self-serve API.** `getleo.ai/api` is a request-access form ("business
   users only", reviewed case-by-case). No docs site, no SDK, no OpenAPI
   spec, no MCP server, no PyPI/npm packages. The ToS explicitly prohibits
   automated access outside granted API access.
2. **Windows/interactive delivery.** Web app + Windows `Leo.exe` desktop app
   + Windows-only CAD add-ins (SolidWorks, Creo, Fusion, Inventor) that talk
   to the desktop app over localhost. Nothing runs headless, nothing runs on
   a Linux runner.
3. **Zero independent evaluation.** No peer-reviewed paper, arXiv preprint,
   or benchmark (Text2CAD-Bench, CADBench, MUSE, BenchCAD, CADSmith) includes
   Leo. The flagship "96% accuracy vs GPT's 46%" claim is vendor-internal
   with no published methodology. The single independent hands-on test found
   (Xometry Pro, "We Tested 7 Text-to-CAD Tools") reported Leo produced
   **2D rendered images, not engineering-ready CAD files**, while Zoo,
   AdamCAD, and CADScribe delivered usable STL/STEP.
4. **The $99/month figure is unconfirmed.** getleo.ai has no public pricing
   page (both `/pricing` and `/plans` 404). Third-party listings (GetApp,
   Capterra) show a **$15/user/month Pro** tier plus quote-based
   Business/Enterprise tiers. A different, unrelated "Leo AI" (video
   marketing SaaS) has $29/$129/$249 tiers — a likely source of pricing
   confusion, as is Dassault's own unrelated SOLIDWORKS companion also
   named "LEO".

**Recommendation for this repo:** not adoptable for the CadQuery → STEP/STL
→ slicer CI pipeline (no API, no Linux, no headless). Its actual strength —
cited engineering Q&A and PDM part search — overlaps the *human* side of the
workflow, not the generative-geometry side where Zoo/ML-ephant sits. If the
interactive copilot itself is interesting, the cheap experiment is the
$15/mo Pro tier + free trial in the web app, plus submitting the
`getleo.ai/api` access form to ask about API terms. Don't budget $99/mo on
the LinkedIn trail alone.

---

## 1. Product & company

- Positioning: "mechanical engineering copilot" built on a patented "Large
  Mechanical Model" (LMM) trained on native CAD geometry + "1M+ vetted
  engineering sources" (vendor claims). Features: engineering Q&A grounded
  in PLM data + handbooks; calculations with formula citation; part search
  over PLM + 120M vendor parts (TraceParts partnership, Sept 2025); assembly
  building; concept-image generation; 2D→3D mesh conversion.
  https://www.getleo.ai/ ; https://www.getleo.ai/tutorials-tips ;
  https://www.engineering.com/leo-ai-teams-up-with-traceparts-for-ai-part-search/
- Text-to-CAD assemblies (since ~May 2026): full part/feature tree,
  "compatible with SolidWorks, Onshape, CATIA, Inventor"; CEO admits mates
  are still closed manually. Independent trade-press coverage of a vendor
  demo. https://www.engineering.com/leo-ai-can-now-generate-full-cad-assemblies/
- Notable messaging contradiction: an earlier getleo.ai blog post positioned
  Leo as "search over generation" ("does not generate new CAD geometry from
  text") while 2026 marketing touts full assembly generation.
  https://www.getleo.ai/blog/text-to-cad-api-integration-solidworks
- Shigley grounding: the retrieval corpus is claimed to include *Shigley's
  Mechanical Engineering Design* and *Machinery's Handbook* with
  exact-page citation. **No published validation of this grounding exists**
  (no retrieval-accuracy study, no Shigley problem-set eval, no licensing
  discussion). https://www.getleo.ai/blog/ai-for-mechanical-engineers-why-lmms-like-leo-are-the-future
- Company: founded May 2023, Boston (50 Milk St). Founders Dr. Maor Farid
  (CEO — Technion PhD, MIT postdoc) and Moti Moravia (CTO). ~12 people per
  the About page. $9.7M total seed announced Sept 2025, led by Flint
  Capital; angels include Bertrand Sicot (ex-SolidWorks CEO) and Google VP
  Yossi Matias. https://www.getleo.ai/about ;
  https://www.getleo.ai/blog/leo-ai-raises-9-7m-to-build-the-world-s-first-ai-for-mechanical-engineering ;
  https://www.finsmes.com/2025/09/leo-ai-raises-9-7m-in-seed-funding.html
- Vendor metrics are internally inconsistent across their own pages: user
  counts 20k → 50k → 60k; hours-saved 5, 5–7, 8.3, 12 hrs/week; parts count
  112M vs 120M; accuracy 95% vs 96%. Machine Design (the most substantive
  press profile, Nov 2025) is interview-only — it repeats these figures
  without verification.
  https://www.machinedesign.com/automation-iiot/article/55330891/leo-ai-leo-ai-how-cad-aware-ai-is-changing-mechanical-design-and-engineering-workflows

## 2. Pricing

- **No first-party pricing page**: `getleo.ai/pricing` and `/plans` both
  404; the getting-started flow just says "purchase the subscription that
  best suits your needs." https://www.getleo.ai/getting-started
- Third-party listings (vendor-sourced): **Pro $15/user/month** (unlimited
  Q&A, calculations, standard parts finder, 3D concept generation);
  Business/Enterprise quote-based (CAD-tool integration, PDM/directory
  connections, org-specific data). Free trial available; "free version"
  reported inconsistently (GetApp yes, Capterra no).
  https://www.getapp.com/emerging-technology-software/a/leo-ai/ ;
  https://www.capterra.com/p/10032244/Leo-AI/
- **$99/month: not confirmed anywhere for getleo.ai.** The unrelated
  video-marketing "Leo AI" ($29/$129/$249) and Dassault's SOLIDWORKS "LEO"
  companion are common conflation sources.
  https://coldiq.com/tools/leo-ai ;
  https://www.solidworks.com/product/solidworks-design/ai-companions

## 3. User sentiment

- **G2: ~4.9 stars, 46 reviews** — the only platform with meaningful volume.
  Praise: real geometry-aware part search, source citations, visible Python
  calc logic, PDM connection. Only concrete negative: response speed.
  Caveat: early-stage B2B G2 reviews are often vendor-solicited.
  https://www.g2.com/products/leo-ai-leo/reviews
- Everywhere else, genuine end-user voice is **near zero**: 1 Trustpilot
  review, 0 Capterra/Software Advice/Slashdot reviews, no Product Hunt
  launch, no Develop3D/Cadalyst coverage, 0 Hacker News stories.
- Reddit: no organic practitioner discussion found. The three comments that
  mention getleo.ai (2024, r/MechanicalEngineering) follow a
  seeding/astroturf pattern (promotional sign-offs, single-purpose
  accounts). One neutral organic mention in r/3Dmodeling (Jan 2025).
- LinkedIn discourse is founder-generated (Maor Farid's posts, incl. the
  "AI is making mechanical engineers slower" post that led here — 138
  reactions; comment pushback centers on verification behavior, not the
  product).
  https://www.linkedin.com/posts/maorfaridphd_ai-is-making-mechanical-engineers-slower-activity-7445527049257152513-QpIK
- Search results for "Leo AI review" are dominated by getleo.ai's own SEO
  listicles ranking themselves #1 — independent evaluation is largely
  crowded out.

## 4. Formal evaluations & case studies

- **Academic/independent benchmarks: none include Leo.** Verified against
  Text2CAD-Bench (arXiv 2605.18430), MUSE (2605.28579), CADBench
  (2605.10873), BenchCAD (2605.10865), PR-CAD (2604.19773), and CADSmith
  (2603.26512) — all evaluate LLMs/research models, never commercial
  copilots, so absence is typical, but it means zero academic signal on Leo
  either way.
- **The one independent hands-on test is unfavorable on generation**:
  Xometry Pro tested 7 text-to-CAD tools; Leo produced "coherent and
  visually representative" 2D images that were "not engineering-ready,"
  while Zoo, AdamCAD, and CADScribe produced usable STL/STEP. (Tests Leo's
  generation feature, not its knowledge-QA core.)
  https://xometry.pro/en/articles/text-to-cad-tools-test/
- Case studies (all vendor-published, none audited): HP (decision in 2 min
  vs hours), V12 (part search 3–5 hrs → minutes), Toothsure (5 days → 1
  day), Oberman (30–40% design-time cut), anonymous DoD unit (hydraulic
  analysis 3 days → <1 hr). Named users in press: Scania, Siemens, NVIDIA,
  Intel, Mobileye. https://www.getleo.ai/customers ;
  https://www.getleo.ai/case-study-dod
- Interesting adjacent datapoint: a Nature Scientific Reports study (Mar
  2025) measured ChatGPT at 46.6% on 800 ME-education questions — matching
  the "GPT's 46%" figure Leo markets against, though Leo never cites it.
  https://www.nature.com/articles/s41598-025-93871-z

## 5. Programmatic access (the decisive part for this repo)

- **API**: `https://www.getleo.ai/api` = request-access form only
  ("business users only", case-by-case review). `docs.getleo.ai`,
  `developer(s).getleo.ai` don't resolve. `api.getleo.ai` exists (their
  private app backend, Descope auth) but exposes no public docs
  (`/openapi.json`, `/docs` etc. all 404).
- The web-app bundle reveals internal endpoints incl.
  `POST api/v1/session/{id}/cad_generation/export` with formats
  `step/stp/stl/obj/glb/iges/x_t/sldprt/sldasm`, plus `api/v1/onshape/*`
  OAuth sync routes and TraceParts CAD generation — i.e. **STEP export and
  an Onshape integration exist server-side**, but only session-authed and
  undocumented. Driving them would breach the ToS, which prohibits
  "any automated system … to access the Site" and reverse engineering.
  https://www.getleo.ai/terms-of-service
- Delivery: React web app (`app.getleo.ai`), Windows `Leo.exe`, Windows MSI
  add-ins for SolidWorks/PDM, Creo, Fusion, Inventor. Add-ins talk to the
  desktop app on `localhost:4000`; desktop relays to `api.getleo.ai`.
  Requires an interactive CAD session. The SolidWorks add-in source is,
  oddly, hosted in a personal GitHub repo.
  https://github.com/kimdavis1/leo-ai-sw-addins
- Developer ecosystem: no GitHub org, no PyPI/npm packages, no MCP server,
  no Discord/Slack; Discourse forum link in the footer didn't resolve from
  this runner. Enterprise deployment claims (on-prem, ITAR) appear only in
  sales blogs; the official Trust Center confirms SOC 2 Type II + GDPR on
  GCP. https://www.getleo.ai/security

## 6. Fit against this repo's existing lanes

| Lane | What it gives us | Leo AI equivalent? |
|------|------------------|--------------------|
| CadQuery / build123d | Headless parametric BREP + STEP/STL/3MF in CI | ❌ nothing headless; no Linux |
| Zoo ML-ephant (`/ai/text-to-cad`, `/ml/text-to-cad/iteration`) | REST text-to-CAD returning KCL + STEP, scriptable Judge loop | ❌ no self-serve API; the only independent generation test yielded images, not CAD |
| Onshape REST | Headless upload/translate/export, classroom-owned docs | ⚠️ Leo has an Onshape OAuth integration in its web app (human-facing), not an API we can call |
| Interactive design assistance (human in the loop) | — (currently Zoo Design Studio / Onshape UI) | ✅ this is Leo's real niche: cited Q&A (Shigley et al.), calcs, part search inside SolidWorks/web |

Net: Leo AI competes with the *engineer's browser tab*, not with this PR's
CI pipeline. Revisit only if (a) their API program grants meaningful access
after the `getleo.ai/api` form, or (b) an independent benchmark of the
knowledge-QA claims appears.

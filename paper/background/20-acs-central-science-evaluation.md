# 20 — ACS Central Science evaluation (follow-up to notes 15/19)

*Follow-up batch — single Edison `LITERATURE_HIGH` query prompted by Phillip
Lampkin's suggestion (PR #91 discussion) that ACS Central Science could fit the
"generative AI got us ~80% of the way to a useful, affordable device" story,
modeled on the MacMillan-group photoreactor paper. Raw artifacts:
`edison_artifacts/acs_central_science.{answer.md,references.md,artifact-00.md,artifact-01.md,task.json}`;
runner: `edison_run_acs_central_science.py` (task
`520122e9-b35d-4977-844b-b549fff8de0e`, `status=success`). Note **15** scored
ACS Central Science Tier-3 *without* the photoreactor precedent; this note
re-evaluates it with that precedent in hand.*

## TL;DR

- **ACS Central Science is a credible stretch target, not a default primary.**
  Diamond OA (**no APC**), IF ~12.7, but ~8–10% acceptance and an explicit
  "broad significance to the chemical sciences" bar. Edison estimates ~50%
  desk-rejection risk for this paper as currently framed (AM-alloy-first).
- **The device-paper precedent is real and recurring** (~1–2 instrument papers
  per year), anchored by the Le/Wismer/MacMillan photoreactor
  (10.1021/acscentsci.7b00159) and continued by the HTe-Chem standardized
  electrochemical reactor (Rein et al. 2021, 10.1021/acscentsci.1c00328), the
  Wi-eChem low-cost 3D-printed wireless reactor (Chen & Mo 2023,
  10.1021/acscentsci.3c00856), and — closest to our story — **ERCAD**, a
  parametric 3D-printed reactor *design tool* (Heard, Deeks & Lennox 2024,
  10.1021/acscentsci.4c00988).
- **The solids-dosing pain point is well documented in the chemistry
  literature** (Seifrid 2022 *Acc. Chem. Res.*; Tom et al. 2024 *Chem. Rev.*;
  Christensen 2021 *Chem. Sci.*; Jiang 2023 *Digital Discovery* on commercial
  dispenser limits), so the "longstanding problem" claim survives scrutiny.
- **Go/no-go condition:** submit to ACS Central Science *only if* the
  manuscript is rewritten chemistry-first — general-purpose solid dispensing
  for any lab (catalysts, reagents, pharma intermediates), with AM alloy
  discovery as one demonstration and the AI-design pipeline as the hook, not
  the headline. Otherwise Digital Discovery (audience) or Additive
  Manufacturing (AM-alloy prestige) remain the better primaries per note 19.

## The MacMillan photoreactor precedent — what transferred and what doesn't

Le, Wismer, …, Davies, MacMillan, *ACS Cent. Sci.* 2017, 3(6), 647–653
(~246 citations; Princeton + Merck; commercialized as the Penn PhD Photoreactor
M2). Edison's read on why it was accepted: (i) a broadly recognized
reproducibility pain point (no standardized photoreactor), (ii) demonstrated
utility across diverse reaction classes, (iii) a democratization/
standardization narrative, and (iv) a path to community adoption/
commercialization. The powder doser maps well onto (i) and (iii) — solids
dosing is a documented SDL bottleneck and the doser is open-source and
low-cost — but (ii) requires reframing the AM-powder calibration dataset as a
*generality benchmark across particle sizes, morphologies, densities, and flow
regimes*, and demonstrating (or at least arguing) chemistry-lab use cases
beyond AM alloys.

## Device/instrument precedent papers at ACS Central Science (2017–2026)

Full table in `acs_central_science.artifact-01.md`. Highlights: MacMillan
photoreactor (2017), HTe-Chem (2021), Wi-eChem (2023), ERCAD parametric
reactor-design tool (2024), ECCR+SID mass-spec instrumentation (2024), an SDL
perspective and a robo-fluidic photochemistry toolbox *(both 2026-dated —
verify DOIs at journal page)*. **ERCAD is the closest analogue**: open,
3D-printable hardware plus a computational design methodology — a direct
precedent for the generative-CAD framing.

## Head-to-head vs. the existing shortlist

Full table in `acs_central_science.artifact-00.md`. Condensed:

| Venue | IF | OA cost | Acceptance likelihood | Best framing |
|---|---:|---|---|---|
| **ACS Central Science** | ~12.7 | **no APC** | **Low** (~8–10% bar) | chemistry-lab solid dosing first; AI-design as hook |
| Digital Discovery (RSC) | ~6.2 | ~£2–2.5k APC | High | AI-design + SDL hardware |
| Additive Manufacturing | ~11 | hybrid (~$3–3.5k if OA) | Medium–High | AM powder calibration + alloy discovery |
| AM Letters | ~4.2 | ~$1.5–1.7k APC | High | short AM-calibration communication |
| Adv. Eng. Informatics | ~8 | hybrid | Medium | LLM/gen-CAD pipeline as the contribution |
| IJAMT | ~3.5 | hybrid | High | practical instrument/process engineering |
| HardwareX | ~2.3 | **no APC** | Very High | companion: full build + validation |
| JOSS / SoftwareX | — / ~2.4 | no APC / APC | High / Medium–High | companion: software DOI |

Key trade-off vs. Digital Discovery: ~2× the impact factor, a far broader
chemistry readership, and zero APC — at roughly 10× the rejection risk, and
with the AM-alloy audience (sgbaird's stated preference, PR #91) reached only
indirectly.

## Recommended strategy (Edison's bottom line)

1. **Tier 1 attempt:** ACS Central Science with the chemistry-general
   solid-dosing framing (standardization narrative + powder-generality
   benchmark + AI-design hook). Accept the ~50% desk-rejection risk; a desk
   reject is fast (typical first decision 4–6 weeks) and costs little.
2. **Tier 1 fallback:** on rejection, redirect unchanged-in-substance to
   **Digital Discovery**, or pivot to **Additive Manufacturing** if the
   AM-calibration framing leads (Adam Clare outreach already in motion —
   `abstracts/additive-manufacturing/abstract.md`).
3. **Tier 2 companions (either way):** **HardwareX** build paper + **JOSS**
   software DOI — no APC, and they carry the reproducibility payload a
   high-bar flagship paper cannot. An ACS Central Science submission does not
   conflict with these companions any more than a Digital Discovery one does.

This slots into note **19**'s sequence as an optional step 0 ahead of the
Digital Discovery flagship submission; the rest of the plan (reviewer slate,
conferences, escalation paths) is unchanged.

## Caveats preserved from the inputs

- Venue metrics (IF, CiteScore, acceptance rate, time-to-decision, APCs) are
  Edison estimates — *verify at journal pages* before relying on them.
- The 2026-dated ACS Central Science entries (Brown & Berlinguette perspective;
  Arshad et al. "Roblonski") are flagged *verify DOI*; the 2017–2024 precedent
  papers carry resolvable DOIs.
- No editor names or contact details were fabricated; Carolyn Bertozzi is
  cited only as founding EiC (public record). Route any editor requests
  through the ACS submission system.
- The "~80% AI-designed" figure is our own project claim, passed to Edison as
  context — it must be substantiated in the manuscript itself.

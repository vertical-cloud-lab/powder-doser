# Testing flux.ai for PCB generation — findings and recommendations

Resolves the issue *"Test out flux.ai for PCB generation"* (agent instruction:
*"Attempt remote usage with a dummy API key, if possible. Provide
recommendations"*). This note records what was actually tried, what was
observed, and what we recommend for the powder-doser control electronics. It
complements the EDA-automation survey in `14-recommendations-electrical.md`.

## What flux.ai is

[Flux](https://www.flux.ai) is a browser-based, collaborative PCB EDA tool. Its
**Copilot** feature is an AI "circuit co-designer": you describe a board in
natural language and it suggests parts, drafts schematic blocks, wires them,
keeps a live BOM, and assists with layout/routing and DFM checks. It is a strong
fit for rapid prototyping of "standard" boards (MCU + sensors + drivers), which
is exactly the shape of our dosing controller (MCU + stepper driver + HX711
load-cell front end).

Copilot is metered in **ACU credits** (AI Compute Units): as of June 2026,
roughly 10 ACU/month on Starter and ~100 ACU/editor/month on Pro/Teams, with
overage billed per ACU. Larger/more complex generations consume more credits.

## Remote-usage attempt with a dummy API key

The issue asked to attempt remote usage with a dummy API key. A read-only,
stdlib-only probe was written and run: `paper/background/flux_probe.py`. It
sends a fake bearer token / `X-Api-Key` to the documented host plus the paths a
programmatic Copilot or project API would most plausibly use, and classifies
each response. Reproduce with:

```bash
python3 paper/background/flux_probe.py
```

Observed result (2026-06):

```
 STATUS  KIND                    URL
    200  html-spa-shell          https://docs.flux.ai/
    200  html-spa-shell          https://www.flux.ai/api
    200  html-spa-shell          https://www.flux.ai/api/v1
    200  html-spa-shell          https://www.flux.ai/api/copilot
    200  html-spa-shell          https://www.flux.ai/api/graphql
    ERR  connection-error        https://api.flux.ai/
    ERR  connection-error        https://api.flux.ai/v1
```

Interpretation:

- There is **no `api.flux.ai` host** (DNS/connection failure), and no
  documented developer/API/SDK/token page anywhere in the docs sitemap
  (`https://docs.flux.ai/sitemap.xml` lists only Introduction / reference /
  tutorial pages, including Copilot usage docs — but nothing about an API key).
- Every `www.flux.ai/api*` path returns the **single-page-app HTML shell** with
  `200`, i.e. the front-end router's catch-all `index.html`. The dummy key is
  silently **ignored, not rejected** — there is no key-authenticated REST/GraphQL
  surface to reject it. (A real key-gated API would return `401/403` JSON.)

**Conclusion:** flux.ai currently exposes **no public REST API and no
API-key-based remote interface** for programmatic PCB generation. Copilot is
only reachable interactively through the authenticated web UI (session-based,
ACU-metered). So "remote usage with a dummy API key" is **not possible** today,
and cannot be automated headlessly in CI the way our existing
ZOO/Edison runners are.

## Recommendations

1. **Do not block our toolchain on a flux.ai API — there isn't one.** It cannot
   be scripted from this repo / GitHub Actions the way `kicad-cli`, SKiDL, or
   the ZOO/Edison runners can. Treat Flux as an *interactive design aid*, not an
   automatable pipeline stage.

2. **Keep the code-first, CI-friendly stack from note 14 as the source of
   truth** (KiCad + SKiDL/atopile, ERC/DRC, BOM/gerber export in CI). Those
   produce text artifacts we can version, diff, and gate on PRs — Flux cannot.

3. **Use Flux Copilot opportunistically for drafting**, not as the system of
   record:
   - Good for: quickly sketching a single dosing channel (MCU + stepper driver +
     HX711) and exploring part choices via natural-language prompts.
   - Then **export to KiCad** (Flux documents a Flux↔KiCad path) and commit the
     KiCad/SKiDL output so the design re-enters our reviewable, CI-checked flow.
   - Record the Copilot prompt + model context in the PR for provenance, exactly
     as recommended for any LLM-assisted schematic in note 14.

4. **Mind the limits before relying on it:** Copilot is weakest on novel /
   high-speed / RF / regulated designs, the part library is shallower than
   dedicated suites, ACU credits are consumed quickly when iterating, and it is
   cloud/browser-only (no offline/air-gapped use). Human review of any generated
   schematic remains non-negotiable.

5. **Revisit if Flux ships a public API.** If/when a documented API key + REST
   endpoint appears, `flux_probe.py` will start returning a `json-like` /
   `401`-style response instead of the HTML shell — that is the signal to
   prototype a `flux_run.py` runner alongside the existing ZOO/Edison ones. Until
   then, prefer the open, automatable tools.

## Files

- `paper/background/flux_probe.py` — reproducible, read-only remote probe used
  for the dummy-key attempt above.
- `paper/background/15-flux-ai-pcb-generation.md` — this note.

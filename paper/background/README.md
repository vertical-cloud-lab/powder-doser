# Background research for the BYU NASA Space Grant proposal

This folder collects literature and landscape reviews to inform the
**background section** of the grant proposal scaffolded under
[`paper/main.tex`](../main.tex) (see issue
[#26](https://github.com/vertical-cloud-lab/powder-doser/issues/26)).

The proposal is framed around generative CAD applied to this repository
(`powder-doser`), tied to a larger vision of autonomous discovery of
additively manufactured (AM) aerospace alloys, where accurate multi-powder
dosing is a critical unmet need. Two background pillars therefore need to be
covered, each addressed by both a *landscape* review (commercial / tool-level
state of the art) and a *literature* review (recent peer-reviewed work):

| File | Pillar | Scope |
| --- | --- | --- |
| [`01-powder-dispensing-commercial-landscape.md`](01-powder-dispensing-commercial-landscape.md) | Powder dispensing | Commercial systems (Mettler Toledo Quantos/CHRONECT, Chemspeed SWING/FLEX, Unchained Labs, Coperion K-Tron, Schenck, Gericke, Brabender, Movacolor, Freeman FT4, Sartorius), accuracy/throughput/price, gap analysis for sub-$10k AM-capable multi-powder dosing. References issue [#10](https://github.com/vertical-cloud-lab/powder-doser/issues/10). |
| [`02-powder-dispensing-academic-literature.md`](02-powder-dispensing-academic-literature.md) | Powder dispensing | Recent (2018–2025) peer-reviewed papers on automated dosing, multi-material/HT metal AM (Ni, Ti, HEAs, refractory alloys), compositionally graded alloy discovery, self-driving labs handling solids, and powder-flowability characterization. |
| [`03-generative-cad-landscape.md`](03-generative-cad-landscape.md) | Generative CAD | Commercial (Fusion Generative Design, nTop, Siemens NX, PTC Creo, ANSYS Discovery, Altair Inspire, Rhino + Grasshopper) and code-based / parametric (CadQuery, OpenSCAD, build123d, Onshape FeatureScript, JSCAD) tools, plus AI/LLM-driven CAD research, with capability and limitation comparisons. References issue [#6](https://github.com/vertical-cloud-lab/powder-doser/issues/6). |
| [`04-generative-cad-academic-literature.md`](04-generative-cad-academic-literature.md) | Generative CAD | Recent (2021–2025) peer-reviewed and arXiv work on generative CAD, AI-assisted CAD, LLM-based CAD code generation, programmatic CAD, and learning-based shape generation, plus landmark datasets (DeepCAD, Fusion 360 Gallery, ABC, SketchGraphs, Text2CAD). |
| [`05-llm-cad-spatial-reasoning-mitigation.md`](05-llm-cad-spatial-reasoning-mitigation.md) | Generative CAD | Synthesis (triggered by [PR #34 comment 4433787200](https://github.com/vertical-cloud-lab/powder-doser/pull/34#issuecomment-4433787200)) on LLM/agent spatial-reasoning + assembly failures observed in [PR #35](https://github.com/vertical-cloud-lab/powder-doser/pull/35) (Claude Opus 4.7 CadQuery), with concrete tool-side / prompting / representation / human-in-the-loop mitigations. Backed by a follow-up Edison `LITERATURE_HIGH` query (see below). |
| [`06-tools-and-repositories-to-try.md`](06-tools-and-repositories-to-try.md) | Both | Synthesis (triggered by [PR #29 comment 4434939162](https://github.com/vertical-cloud-lab/powder-doser/pull/29#issuecomment-4434939162)) re-organising the tools cited across `01`–`05` around what can actually be cloned, installed, or subscribed to today: code-CAD foundations (CadQuery, build123d, OCP, FreeCAD, slicers), 2024–2026 LLM-CAD research repos (CADSmith, CAD-Coder, CAD-Recode, Text-to-CadQuery, CAD-MLLM, CADCrafter, …), datasets, commercial subscriptions worth trialling (Onshape, Zoo.dev) vs. ones to skip on the proposal budget (nTop, Creo, NX), and a 6-step recommended trial set. Connects to [PR #7](https://github.com/vertical-cloud-lab/powder-doser/pull/7)'s open-source CAD tooling work. |

## Provenance

These notes were produced by four parallel
[Edison Scientific](https://edisonscientific.gitbook.io/edison-cookbook)
`LITERATURE_HIGH` queries (the `paperqa`-class deep literature pipeline). Each
claim in the notes is followed by a citation key of the form
`(authorYYYYshortid pages X-Y)`; the corresponding numbered references — with
authors, journal, DOI, and citation count — are listed at the bottom of each
file.

The notes are intentionally kept verbatim (lightly formatted markdown) rather
than paraphrased, so that citation provenance to the underlying sources is
preserved when individual passages are pulled into the LaTeX manuscript.

## How to use these notes when drafting the proposal

1. Skim each file's table of contents (`##` section headings) and the
   *Conclusions / Key takeaways* sections at the end.
2. Pull specific claims into the proposal's Background and Motivation
   sections, replacing the inline `(authorYYYY... pages ...)` Edison citation
   keys with `\cite{...}` calls into [`paper/rsc.bib`](../rsc.bib).
3. For any reference cited in the proposal, copy the corresponding entry from
   the file's *References* section into `paper/rsc.bib` as a proper BibTeX
   entry (the DOI is provided in every Edison reference). Only references
   that are actually cited in the manuscript should end up in `rsc.bib` —
   leave the broader bibliography here in the notes for traceability.
4. The *Technology Gap Analysis* table in
   `01-powder-dispensing-commercial-landscape.md` and the
   *Capabilities vs. Limitations* discussion in
   `03-generative-cad-landscape.md` and
   `04-generative-cad-academic-literature.md` are particularly relevant
   for motivating the proposal's research questions.

## Raw query artifacts (provenance)

The full raw outputs from Edison — including the underlying contexts,
references, agent state, cost, and token counts — are committed under
[`edison_artifacts/`](edison_artifacts/) for reproducibility. Each query has
three files (`<key>.task.json`, `<key>.answer.md`, `<key>.references.md`); see
[`edison_artifacts/README.md`](edison_artifacts/README.md) for layout.

## Reproducing or refreshing the notes

The four original queries can be re-run end-to-end with
[`edison_run.py`](edison_run.py); the follow-up spatial-reasoning query that
backs `05-llm-cad-spatial-reasoning-mitigation.md` lives in
[`edison_run_followup_spatial.py`](edison_run_followup_spatial.py). Both
embed their prompts verbatim and write the artifacts described above:

Both runners read the API key from the `EDISON_API_KEY` environment variable
via `os.environ["EDISON_API_KEY"]` (never hard-coded or logged):

```sh
pip install edison_client
export EDISON_API_KEY=...   # never commit this value
python paper/background/edison_run.py
python paper/background/edison_run_followup_spatial.py
```

A high-effort literature query takes roughly 20–30 minutes per task; all four
are dispatched in parallel via `EdisonClient.run_tasks_until_done`.

The prompts are also quoted verbatim at the top of each `0*-*.md` file (the
`Question:` line), so they can be edited and re-run independently.

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

## Reproducing or refreshing the notes

The four queries can be re-run with the Edison Python client. With
`edison_client` installed (`pip install edison_client`) and an
`EDISON_API_KEY` exported to the environment:

```python
from edison_client import EdisonClient, JobNames

client = EdisonClient(api_key=...)  # do not log/echo the key
queries = [
    ("powder_commercial", "Provide a comprehensive landscape review of commercial powder dispensing ..."),
    ("powder_academic",   "Find recent (2018-2025) peer-reviewed academic publications on automated powder dispensing ..."),
    ("gencad_landscape",  "Provide a state-of-the-art landscape of generative CAD and generative design ..."),
    ("gencad_academic",   "Find recent (2021-2025) peer-reviewed and arXiv academic publications on generative CAD ..."),
]
results = client.run_tasks_until_done(
    [{"name": JobNames.LITERATURE_HIGH, "query": q, "tags": ["powder-doser-grant", k]} for k, q in queries],
    timeout=3000,
)
```

The full prompts used to produce these notes are quoted at the top of each
markdown file (the `Question:` line), so they can be edited and re-run
verbatim.

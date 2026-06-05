# Background research for the BYU NASA Space Grant proposal

This folder collects literature and landscape reviews to inform the
**background section** of the grant proposal scaffolded under
[`paper/main.tex`](../main.tex) (see issue
[#26](https://github.com/vertical-cloud-lab/powder-doser/issues/26)).

The proposal is framed around **generative design applied to this repository**
(`powder-doser`), tied to a larger vision of autonomous discovery of additively
manufactured (AM) aerospace alloys, where accurate multi-powder dosing is a
critical unmet need. Each pillar is covered by both a *landscape* review
(commercial / tool-level state of the art) and a *literature* review (recent
peer-reviewed work).

## Pillars

### Powder dispensing & generative CAD (issue [#28](https://github.com/vertical-cloud-lab/powder-doser/issues/28), PR [#29](https://github.com/vertical-cloud-lab/powder-doser/pull/29))

Files `01`–`06` cover powder dispensing (commercial landscape + academic
literature) and generative **CAD** (landscape, academic literature, LLM-CAD
spatial-reasoning mitigations, and a tools-to-try synthesis). See PR
[#29](https://github.com/vertical-cloud-lab/powder-doser/pull/29) for the
provenance and headline findings of that pillar.

### Generative electrical & PCB design (issue [#75](https://github.com/vertical-cloud-lab/powder-doser/issues/75))

Files `07`–`13` extend the generative-design background from CAD to **electrical
and printed-circuit-board (PCB) design** — the natural complement now that this
repo's hardware includes microcontroller-driven control electronics authored as
KiCad projects (steppers, vibration motors, solenoids, servos, load-cell
feedback, expandable I/O; see issues
[#25](https://github.com/vertical-cloud-lab/powder-doser/issues/25),
[#44](https://github.com/vertical-cloud-lab/powder-doser/issues/44),
[#60](https://github.com/vertical-cloud-lab/powder-doser/issues/60) and PRs
[#45](https://github.com/vertical-cloud-lab/powder-doser/pull/45),
[#61](https://github.com/vertical-cloud-lab/powder-doser/pull/61)).

| File | Pillar | Scope |
| --- | --- | --- |
| [`07-generative-eda-pcb-landscape.md`](07-generative-eda-pcb-landscape.md) | Generative EDA/PCB | State-of-the-art **tools** for generative / AI-assisted / automated EDA, schematic capture, and PCB design: mainstream suites (KiCad, Altium, Cadence Allegro/OrCAD X, Siemens Xpedition/PADS, Zuken, Fusion Electronics/EAGLE, DipTrace, EasyEDA), AI-native startups (Flux.ai, JITX, Quilter, DeepPCB, Celus, Cofactr, Allspice, SnapEDA), and code-based ecosystems (atopile, tscircuit, SKiDL, gEDA, Edea, Horizon EDA), with capability vs. limitation comparisons. The dedicated "what tools are available" query. |
| [`08-schematic-circuit-synthesis-academic.md`](08-schematic-circuit-synthesis-academic.md) | Generative EDA/PCB | Recent (2019–2025) academic work on automated/generative **schematic & circuit-topology synthesis** and netlist generation: ML/generative analog topology generation, LLM/agentic schematic-from-spec systems, GNN/RL circuit synthesis and device sizing. |
| [`09-pcb-placement-routing-ml.md`](09-pcb-placement-routing-ml.md) | Generative EDA/PCB | Recent (2018–2025) ML/RL/optimization methods for **placement and routing** (incl. the Google Nature 2021 chip-placement work and its critiques, analog/PCB placement, learning-based autorouting, DRC-aware methods, benchmarks). |
| [`10-llm-hardware-hdl-codegen.md`](10-llm-hardware-hdl-codegen.md) | Generative EDA/PCB | Recent (2022–2025) **LLM / code-generation** approaches to hardware design: HDL (Verilog/VHDL/Chisel) and netlist generation, agentic design loops, self-repair, and their correctness/synthesizability benchmarks (VerilogEval, RTLLM, ChipGPT, ChipNeMo, AnalogCoder, LaMAGIC, …). |
| [`11-code-based-eda-frameworks.md`](11-code-based-eda-frameworks.md) | Generative EDA/PCB | **Design-as-code** / programmatic EDA that is version-controllable and CI-friendly (the electrical analogue of code-CAD): atopile, tscircuit, SKiDL, PCBmodE, gEDA, Horizon EDA, Edea, KiCad Python/IPC + `kicad-cli`, JITX; programming models, manufacturability/DRC, export, maturity, licensing. |
| [`12-eda-datasets-benchmarks.md`](12-eda-datasets-benchmarks.md) | Generative EDA/PCB | **Datasets & benchmarks** for ML/generative EDA across PCB- and chip-level design (VerilogEval, RTLLM, ISPD/ICCAD placement & routing benchmarks, CircuitNet, Open Circuit Benchmark, open KiCad/PCB corpora), the metrics used, and the gaps in evaluating manufacturable generative PCB design. |
| [`13-open-hardware-eda-for-labs.md`](13-open-hardware-eda-for-labs.md) | Generative EDA/PCB | Generative/automated electrical design in the **open-hardware lab-automation** context (OpenFlexure, Jubilee, Opentrons, HardwareX norms; modular motor/sensor control boards, multiplexed I/O, load-cell front-ends, DfM for low-cost assembly) and how mature generative EDA is for such instruments — the gap this project's control electronics sit in. |
| [`14-pcb-design-recommendations-for-powder-doser.md`](14-pcb-design-recommendations-for-powder-doser.md) | Generative EDA/PCB | **Synthesis / recommendation** pass: an Edison `ANALYSIS` task that reads notes `07`–`13` back in and turns them into ranked, powder-doser-specific recommendations for how the GitHub Copilot coding agent could draft the control PCB (most-feasible approaches, whether each can run inside the headless GitHub/Copilot environment, and per-option pros/cons, limitations, and next steps). Answers @lbwinters' review request on PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4615501821). |
| [`16-quilter-ai-pcb-layout.md`](16-quilter-ai-pcb-layout.md) | Generative EDA/PCB | **Tool deep-dive:** hands-on landscape note on **Quilter.ai** (commercial autonomous PCB-*layout* SaaS) — what it does (KiCad-native placement/routing, not schematics), free-tier eligibility and the train-on-your-data caveat, community/Reddit sentiment and the DeepPCB benchmark (with the company-vs-academic-baseline name collision called out), and the key finding that it is **web-UI-only (no public API)** so it cannot be driven from the headless GitHub/Copilot CI. "No API" is verified by [`quilter_probe.py`](quilter_probe.py). Answers @sgbaird's request on PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4635695822). |
| [`17-deeppcb-ai-pcb-routing.md`](17-deeppcb-ai-pcb-routing.md) | Generative EDA/PCB | **Tool deep-dive:** hands-on landscape note on **DeepPCB** (InstaDeep's commercial autonomous PCB-*routing* SaaS) — the direct counterpart to note `16`. Covers what it does (RL placement/routing, KiCad-native I/O, not schematics), its one-board / 30-minute free trial and per-minute pricing, and mixed/skeptical Reddit + EEVblog sentiment with the vendor-published DeepPCB-vs-Quilter benchmarks called out as non-neutral. Key finding: unlike Quilter/Flux.ai, DeepPCB **does expose a real public API** (`api.deeppcb.ai`, Swagger-documented), so it *is* headless/CI-scriptable — but needs a manually provisioned, paid, per-minute-metered API key. "Has a real API" is verified empirically by [`deeppcb_probe.py`](deeppcb_probe.py). Answers @sgbaird's request on PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4635908170). |

(Note `15` is reserved for the parallel **Flux.ai** tool deep-dive investigated
separately for this PR; this branch jumps `14` → `16` to avoid renumbering.)

## Provenance

These notes were produced by parallel
[Edison Scientific](https://edisonscientific.gitbook.io/edison-cookbook)
`LITERATURE_HIGH` queries (the `paperqa`-class deep literature pipeline). The
generative-EDA/PCB pillar (`07`–`13`) was dispatched by
[`edison_run_electrical_pcb.py`](edison_run_electrical_pcb.py); the prior
powder/CAD pillar by `edison_run.py` / `edison_run_followup_spatial.py` (PR
[#29](https://github.com/vertical-cloud-lab/powder-doser/pull/29)). The
recommendation note (`14`) is produced by a follow-on Edison `ANALYSIS` run,
[`edison_run_pcb_recommendation_analysis.py`](edison_run_pcb_recommendation_analysis.py),
which uploads the seven rendered reviews as a single zipped *collection* (per the
[Edison file-management docs](https://docs.edisonscientific.com/edison-client/file-management))
and analyzes them rather than searching new literature. Each claim in the
literature notes is followed by a citation key of the form `(authorYYYYshortid
pages X-Y)`; the corresponding numbered references — with authors, journal, DOI,
and citation count — are listed at the bottom of each file. Raw artifacts (full
`TaskResponse` JSON, rendered answer, standalone references list) live under
[`edison_artifacts/`](edison_artifacts/).

Note `16` (Quilter.ai) and note `17` (DeepPCB) are **not** Edison outputs: they
are hand-authored tool deep-dives from vendor pages, third-party reviews, and
community/benchmark posts (cited inline by URL), with their central API claims
verified empirically by the read-only probes
[`quilter_probe.py`](quilter_probe.py) ("no public API") and
[`deeppcb_probe.py`](deeppcb_probe.py) ("has a real public API").

The notes are intentionally kept verbatim (lightly formatted markdown) rather
than paraphrased, so that citation provenance to the underlying sources is
preserved when individual passages are pulled into the LaTeX manuscript.

## How to use these notes when drafting the proposal

1. Skim each file's table of contents (`##` section headings) and the
   *Conclusions / Key takeaways* sections at the end.
2. Pull specific claims into the proposal's Background and Motivation sections,
   replacing the inline `(authorYYYY... pages ...)` Edison citation keys with
   `\cite{...}` calls into [`paper/rsc.bib`](../rsc.bib).
3. For any reference cited in the proposal, copy the corresponding entry from
   the file's *References* section into `paper/rsc.bib`.

## Reproducing the queries

```bash
pip install edison_client
export EDISON_API_KEY=...
python paper/background/edison_run_electrical_pcb.py
```

A high-effort `LITERATURE_HIGH` query takes ~20–30 min; all seven are dispatched
in parallel via `EdisonClient.run_tasks_until_done`. The exact prompts are
embedded verbatim in the runner.

To regenerate the recommendation note (`14`) — an Edison `ANALYSIS` run over the
seven rendered reviews:

```bash
pip install edison_client
export EDISON_API_KEY=...
python paper/background/edison_run_pcb_recommendation_analysis.py
```

The analysis runner uploads every `edison_artifacts/*.answer.md` and
`*.references.md` as a single zipped collection
(`store_file_content(..., as_collection=True)`) and asks the data-analysis agent
to synthesize powder-doser-specific PCB recommendations; the embedded prompt is
verbatim in the runner.

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

## Provenance

These notes were produced by parallel
[Edison Scientific](https://edisonscientific.gitbook.io/edison-cookbook)
`LITERATURE_HIGH` queries (the `paperqa`-class deep literature pipeline). The
generative-EDA/PCB pillar (`07`–`13`) was dispatched by
[`edison_run_electrical_pcb.py`](edison_run_electrical_pcb.py); the prior
powder/CAD pillar by `edison_run.py` / `edison_run_followup_spatial.py` (PR
[#29](https://github.com/vertical-cloud-lab/powder-doser/pull/29)). Each claim in
the notes is followed by a citation key of the form `(authorYYYYshortid pages
X-Y)`; the corresponding numbered references — with authors, journal, DOI, and
citation count — are listed at the bottom of each file. Raw artifacts (full
`TaskResponse` JSON, rendered answer, standalone references list) live under
[`edison_artifacts/`](edison_artifacts/).

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

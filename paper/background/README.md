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
| [`17-deeppcb-ai-pcb-routing.md`](17-deeppcb-ai-pcb-routing.md) | Generative EDA/PCB | **Tool deep-dive:** hands-on landscape note on **DeepPCB** (InstaDeep's commercial autonomous PCB-*routing* SaaS) — the direct counterpart to note `16`. Covers what it does (RL placement/routing, KiCad-native I/O, not schematics), its one-board / 30-minute free trial and per-minute pricing, and mixed/skeptical Reddit + EEVblog sentiment with the vendor-published DeepPCB-vs-Quilter benchmarks called out as non-neutral. Key finding: unlike Quilter/Flux.ai, DeepPCB **does expose a real public API** (`api.deeppcb.ai`, Swagger-documented), so it *is* headless/CI-scriptable — but needs a manually provisioned, paid, per-minute-metered API key. "Has a real API" is verified empirically by [`deeppcb_probe.py`](deeppcb_probe.py); the API is further confirmed to **authenticate and answer from this sandbox** with the provisioned `DEEPPCB_API_KEY` by the read-only [`deeppcb_api_ping.py`](deeppcb_api_ping.py). Answers @sgbaird's requests on PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4635908170). |
| [`18-celus-ai-schematic-floorplan.md`](18-celus-ai-schematic-floorplan.md) | Generative EDA/PCB | **Tool deep-dive:** hands-on landscape note on **CELUS** (the CELUS Design Platform) — the **intermediate "topology → router-ready starter board" bridge** @lbwinters identified between an LLM topology tool (LaMAGIC) and an autonomous router (Quilter/DeepPCB, which both require a fully-footprinted KiCad starter board). Covers what it does (block-diagram / natural-language → connected schematic + BOM + floorplan via pre-verified **CUBO** blocks, with native **KiCad** project export including symbols + footprints), free sign-up tier, and review/forum sentiment (with the competitor-published Quilter-vs-CELUS ranking flagged as non-neutral). Key finding: CELUS is the best *capability* match for the bridge but is **web-UI / login-only with no public API**, so — like Quilter/Flux.ai — it is a manual, human-in-the-loop step, not a headless CI one. "No public API" is verified by [`celus_probe.py`](celus_probe.py). Answers @sgbaird's request on PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654166992). |
| [`19-topology-to-starter-board-tools.md`](19-topology-to-starter-board-tools.md) | Generative EDA/PCB | **Edison `LITERATURE_HIGH` survey** of the *intermediate* "topology + BOM → router-ready KiCad starter board" step that Quilter/DeepPCB cannot do themselves: commercial/AI-native bridges (CELUS, Flux.ai, JITX, Circuit Mind, Cofactr), design-as-code frameworks (atopile, tscircuit, SKiDL, Horizon EDA, KiCad-CLI + Python, PCBmodE), and 2020–2025 research on netlist/topology → placement/floorplan (incl. recent NL→KiCad systems pcbGPT, PCBSchemaGen, SchGen, and the HWE-Bench 8.15% end-to-end warning), each scored on input→output, KiCad interoperability, scriptability/API, licensing, and maturity. Kept verbatim. Produced by [`edison_run_topology_to_board.py`](edison_run_topology_to_board.py). Answers @sgbaird's request on PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654166992). |
| [`20-topology-to-starter-board-for-powder-doser.md`](20-topology-to-starter-board-for-powder-doser.md) | Generative EDA/PCB | **Synthesis / recommendation** pass: an Edison `ANALYSIS` task that audits **this repo's actual KiCad control-board schematic** (`hardware/test-module/kicad/` from PR [#61](https://github.com/vertical-cloud-lab/powder-doser/pull/61)) and turns it into concrete, ranked steps for the Copilot agent to produce the footprinted, outlined `.kicad_pcb` starter board Quilter/DeepPCB need. Finds the schematic complete (14 parts / 20 nets) but missing footprints, board file, outline, and placement; ranks **(1)** extending the existing `generate.py` + `kiutils` to emit an unplaced outlined board headlessly, **(2)** migrating to atopile/tscircuit, **(3)** a human-in-the-loop GUI init for the mixed-signal partitioning — flagging CELUS/Flux.ai as login-only and JITX as paywalled for CI. Kept verbatim. Produced by [`edison_run_topology_to_board_analysis.py`](edison_run_topology_to_board_analysis.py). Answers @sgbaird's request on PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654166992). |
| [`21-starter-board-for-quilter-deeppcb.md`](21-starter-board-for-quilter-deeppcb.md) | Generative EDA/PCB | **Build note (not Edison):** the concrete implementation of note `20`'s Rank-1 plan — a headless, self-contained [`starter_board/build_starter_board.py`](starter_board/build_starter_board.py) (pure-Python `kiutils`, no KiCad/GUI/network) that turns the PR [#61](https://github.com/vertical-cloud-lab/powder-doser/pull/61) schematic's 14-part / 20-net topology into an actual **router-ready starter board** — [`test_module_starter.kicad_pcb`](starter_board/test_module_starter.kicad_pcb) (14 footprints, 66 pads / 59 net-assigned, compact ~82 × 113 mm Edge.Cuts outline) plus a [`.kicad_pro`](starter_board/test_module_starter.kicad_pro) with `Default`/`Power` net classes — that uploads directly to Quilter or DeepPCB. A matching [`.kicad_sch`](starter_board/test_module_starter.kicad_sch) schematic (14 symbols, 20 nets, global-label connectivity verified pin-by-pin with `kicad-cli`) is emitted from the same netlist so the full **board + schematic + project trio** can be uploaded together (answering @lbwinters' [request](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4663888863)). The generator also emits a second **`test_module_unplaced`** trio — same netlist/parts but staged **outside** an identical empty outline — so DeepPCB/Quilter can be tested on **auto-placement** (not just routing) and compared against the generator's compact placement (issue [#94](https://github.com/vertical-cloud-lab/powder-doser/issues/94)). Each component's **real body outline, courtyard, and 3-D model** come from the vendor design files committed under `hardware/vendor-files/` (PR [#25](https://github.com/vertical-cloud-lab/powder-doser/pull/25)) — Adafruit Eagle `.brd` outlines + Pololu/StepperOnline STEP envelopes — instead of generic header proxies; the 20-net ratsnest is preserved exactly. Honest caveats: pad geometry is still a simplified 0.1″ header inside each real body (swap for full KiCad footprints before fab), and mixed-signal partitioning still wants a human pass. Answers @sgbaird's requests on PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654482011) and the [real-parts follow-up](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654591085). |

(Note `15` is reserved for the parallel **Flux.ai** tool deep-dive investigated
separately for this PR; this branch jumps `14` → `16` to avoid renumbering.
Notes `19` and `20` cover the two Edison runs added for the
topology→starter-board question — a `LITERATURE_HIGH` survey of
topology/concept→KiCad-board tools and an `ANALYSIS` over this repo's actual
KiCad test-module schematic.)

## Provenance

These notes were produced by parallel
[Edison Scientific](https://edisonscientific.gitbook.io/edison-cookbook)
`LITERATURE_HIGH` queries (the `paperqa`-class deep literature pipeline). The
generative-EDA/PCB pillar (`07`–`13`) was dispatched by
[`edison_run_electrical_pcb.py`](edison_run_electrical_pcb.py); the
topology→starter-board survey (`19`) by
[`edison_run_topology_to_board.py`](edison_run_topology_to_board.py); the prior
powder/CAD pillar by `edison_run.py` / `edison_run_followup_spatial.py` (PR
[#29](https://github.com/vertical-cloud-lab/powder-doser/pull/29)). The
recommendation notes (`14`, `20`) are produced by follow-on Edison `ANALYSIS`
runs ([`edison_run_pcb_recommendation_analysis.py`](edison_run_pcb_recommendation_analysis.py)
uploads the seven rendered reviews; [`edison_run_topology_to_board_analysis.py`](edison_run_topology_to_board_analysis.py)
uploads this repo's actual KiCad test-module project) as a single zipped
*collection* (per the
[Edison file-management docs](https://docs.edisonscientific.com/edison-client/file-management))
and analyzes them rather than searching new literature. Each claim in the
literature notes is followed by a citation key of the form `(authorYYYYshortid
pages X-Y)`; the corresponding numbered references — with authors, journal, DOI,
and citation count — are listed at the bottom of each file. Raw artifacts (full
`TaskResponse` JSON, rendered answer, standalone references list) live under
[`edison_artifacts/`](edison_artifacts/).

Note `16` (Quilter.ai), note `17` (DeepPCB), and note `18` (CELUS) are **not**
Edison outputs: they are hand-authored tool deep-dives from vendor pages,
third-party reviews, and community/benchmark posts (cited inline by URL), with
their central API claims verified empirically by the read-only probes
[`quilter_probe.py`](quilter_probe.py) ("no public API"),
[`deeppcb_probe.py`](deeppcb_probe.py) ("has a real public API"), and
[`celus_probe.py`](celus_probe.py) ("resolves but no documented public API →
web-UI/login-only"). For DeepPCB, [`deeppcb_api_ping.py`](deeppcb_api_ping.py)
additionally performs an **authenticated, read-only** check against the live API
using the repo's provisioned `DEEPPCB_API_KEY` secret (credit-flow + the
board/constraints schemas) — it never prints the key and **consumes no credits**
(it deliberately avoids the credit-charging `POST /boards` /
`PATCH /boards/{id}/confirm` routing endpoints).

The notes are intentionally kept verbatim (lightly formatted markdown) rather
than paraphrased, so that citation provenance to the underlying sources is
preserved when individual passages are pulled into the LaTeX manuscript.

Note `21` (starter board) is likewise **not** an Edison output: it is a
hand-built artifact. [`starter_board/build_starter_board.py`](starter_board/build_starter_board.py)
generates the uploadable `test_module_starter.kicad_pcb` (and a matching
`test_module_starter.kicad_sch` schematic) headlessly from a
netlist transcribed verbatim from PR
[#61](https://github.com/vertical-cloud-lab/powder-doser/pull/61)'s
`generate.py`, with each component's real body outline, courtyard, and 3-D
model taken from the vendor design files committed under
`hardware/vendor-files/` (PR
[#25](https://github.com/vertical-cloud-lab/powder-doser/pull/25)); it depends
only on pure-Python `kiutils` (no KiCad install required to build the board or
schematic). When `kicad-cli` is available it additionally verifies the
schematic netlist and renders previews, but both steps are skipped gracefully
without it.

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

To regenerate the two topology→starter-board Edison runs added for this PR — a
`LITERATURE_HIGH` survey of topology/concept→KiCad-board tools (note `19`) and an
`ANALYSIS` over this repo's actual KiCad test-module schematic (note `20`):

```bash
pip install edison_client
export EDISON_API_KEY=...
python paper/background/edison_run_topology_to_board.py
python paper/background/edison_run_topology_to_board_analysis.py
```

The analysis runner stages the KiCad sources from `hardware/test-module/kicad/`
(falling back to downloading them from the pinned PR
[#61](https://github.com/vertical-cloud-lab/powder-doser/pull/61) commit when
that hardware is not on the current branch) and uploads them as a single zipped
collection before asking which tools could turn a topology + parts list into
that board.

The DeepPCB API can be smoke-tested (authenticated, read-only, no credits spent)
once a key is provisioned as the `DEEPPCB_API_KEY` secret:

```bash
export DEEPPCB_API_KEY=...
python paper/background/deeppcb_api_ping.py
```

The Quilter and CELUS probes need no key or network credentials:

```bash
python paper/background/quilter_probe.py
python paper/background/deeppcb_probe.py
python paper/background/celus_probe.py
```

To regenerate the **starter board** (note `21`) — the actual router-ready
`.kicad_pcb` that uploads to Quilter/DeepPCB:

```bash
pip install kiutils            # pure-Python; cairosvg optional for the PNG
python paper/background/starter_board/build_starter_board.py
```

`kicad-cli` (KiCad ≥ 7) is optional; without it the script uses a built-in
dependency-free SVG fallback (and `cairosvg`, if present, for the PNG). The
board, project, and summary are produced regardless.

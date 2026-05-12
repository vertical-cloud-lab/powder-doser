# 06 — Tools, GitHub repositories, and commercial subscriptions to try

**Status:** Synthesis triggered by [PR #29 review comment 4434939162](https://github.com/vertical-cloud-lab/powder-doser/pull/29#issuecomment-4434939162) (@sgbaird) — "you've now looked at a lot of different references, especially very recent articles (2026). What tools are people using? Are there github repositories or similar that can be tried out? […] Are there commercial subscriptions that would be worth trying out?"

The five preceding background notes (`01`–`05`) cite ≈100 distinct sources but mostly catalogue *methods, benchmarks, and findings* rather than the runnable code that backs them. This note re-organises the same evidence base around **what you can actually clone, install, or subscribe to today**, with the proposal-relevant dose of "is it worth the trial".

It is scoped to the two pillars of the proposal (#26): (a) accurate multi-powder dosing for AM alloy discovery (#10) and (b) generative / agentic / code-based CAD for engineering hardware (#6, picked up from [PR #7](https://github.com/vertical-cloud-lab/powder-doser/pull/7)'s open-source CAD tooling work). For a full description of each underlying method, see the cross-referenced sections in `03`–`05`; for raw provenance, see [`edison_artifacts/`](edison_artifacts/).

URLs were verified at the time this note was written; if a link 404s, the canonical record is the DOI in the relevant `0X-*.references.md` file.

---

## 1. Code-based CAD foundations (already production-ready)

These are the substrate that almost every recent LLM-CAD paper builds on. They are also the substrate this repo already uses (`design/cad/<module>/cad_model.py`). All free, all OSS, all installable today.

| Tool | Repo | License | Why it matters here | Notes for this repo |
|---|---|---|---|---|
| **CadQuery 2** | [CadQuery/cadquery](https://github.com/CadQuery/cadquery) | Apache-2.0 | Python-first, OpenCascade-backed B-rep CAD. Cited as "best trade-off between usability and flexibility" in `xie2505texttocadqueryanew pages 12-15`. Already the primary representation in `design/cad/single-channel-module/cad_model.py`. | In active use. Pin a known-good version in the repo's environment to dodge the OCP numerical-robustness issues called out in `03-…landscape.md §3`. |
| **build123d** | [gumyr/build123d](https://github.com/gumyr/build123d) | Apache-2.0 | Newer Python-first CAD framework, also OpenCascade-backed, with a more modern API and `BuildPart`/`BuildSketch` context-manager syntax. Worth piloting on a *new* module to compare ergonomics vs CadQuery. | Trial candidate. If a future module is greenfield, write it in build123d and benchmark LLM-generation success vs CadQuery on the same prompt. |
| **OCP** (OpenCascade Python bindings) | [CadQuery/OCP](https://github.com/CadQuery/OCP) | LGPL-2.1 | The shared OCCT binding under both CadQuery and build123d. Direct OCP calls (`IsValid()`, `BRepCheck_Analyzer`, connected-components) are how you implement the §A guardrails in `05-…mitigation.md`. | Use directly inside `tests/test_cad_model.py` for the verifier set. |
| **ocp-vscode** + **cq-editor** | [bernhard-42/vscode-ocp-cad-viewer](https://github.com/bernhard-42/vscode-ocp-cad-viewer), [CadQuery/CQ-editor](https://github.com/CadQuery/CQ-editor) | Apache-2.0 | Live preview / hot-reload viewers that work with both CadQuery and build123d. Closes the human review loop for the §2.D ("code-level human edits") workflow Sadik & Bujny 2025 quantitatively endorse. | Recommend for any human reviewer touching `cad_model.py`. |
| **OpenSCAD** | [openscad/openscad](https://github.com/openscad/openscad) | GPL-2.0 | Declarative CSG DSL. Limited for engineering work but the *target language* of the **CADReview** benchmark (`chen2025cadreviewautomaticallyreviewing pages 8-9`), so you'd use it if you want to reproduce that 41.5% GPT-4o error-detection ceiling locally. | Reference only; do not standardise on it. |
| **FreeCAD** | [FreeCAD/FreeCAD](https://github.com/FreeCAD/FreeCAD) | LGPL-2.0 | The Python-scriptable open-source MCAD that **CAD-Assistant** (`mallis2025cadassistanttoolaugmentedvllms pages 5-6`) uses as its tool back-end. Useful as a parametric viewer for STEPs that this repo's CadQuery code exports, and as the integration target if you want to reproduce CAD-Assistant locally. | Optional viewer; see also FreeCAD-MCP below. |
| **Autodesk PrusaSlicer** / **OrcaSlicer** | [prusa3d/PrusaSlicer](https://github.com/prusa3d/PrusaSlicer), [SoftFever/OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) | AGPL-3.0 | Headless CLI mode (`prusa-slicer --export-gcode --slice`) is the cheapest "manufacturability" gate you can put in CI — overhang angle, support volume, layer count. Catches PR #35 failure classes F8/F9 from `05-…mitigation.md` automatically. | High recommend for `tests/test_printability.py`. |

---

## 2. LLM-CAD research repos worth cloning (2024–2026)

All published with code; all directly relevant to "agentic, code-based, manufacturability-aware CAD" (#6). Listed roughly in the order I'd actually try them on this repo's modules.

### 2.1 First-tier (clone now, run on a `single-channel-module`-class prompt)

1. **CADSmith** — [jabarkle/CADSmith](https://github.com/jabarkle/CADSmith) (Barkley et al., 2026; `barkley2603cadsmithmultiagentcad`)
   - Multi-agent loop: Planner → Coder (CadQuery) → Executor (OpenCascade) → Validator → independent VLM **Judge** → Refiner.
   - Reports **100 % execution success, median IoU 0.9629, mean Chamfer Distance 28.37 → 0.74 (≈38×)**. The ablation removing the rendered three-view image inflates Tier-3 mean CD from 1.42 → 49.68 — empirical evidence for the §2.B.1 claim in `05-…mitigation.md` that visual feedback is necessary, not optional.
   - **Why try it here:** it is the closest published prior art to the architecture `05-…mitigation.md` recommends for this repo. Running it on the auger-cradle prompt that produced PR #35 would be the cleanest A/B test we can do without writing new code.

2. **CAD-Coder** — [anniedoris/CAD-Coder](https://github.com/anniedoris/CAD-Coder) + [anniedoris/GenCAD-Code](https://github.com/anniedoris/GenCAD-Code) (Doris et al., 2025/2026; `guan2025cadcodertexttocadgeneration`)
   - **Open-source VLM** fine-tuned to emit CadQuery code from a CAD image. GenCAD-Code dataset is 163 k image–code pairs and is also released. Reports 100 % syntax validity on the benchmark and beats GPT-4.5 / Qwen2.5-VL-72B on geometric metrics.
   - **Why try it here:** the only fully open-weight VLM in this space that already speaks CadQuery — i.e., the only one we can self-host without a frontier-API budget. Runs the §2.B.1 critic loop locally.

3. **CAD-Recode** — [filaPro/cad-recode](https://github.com/filaPro/cad-recode) (Rukhovich et al., ICCV 2025; `rukhovich2025cadrecodereverseengineering`)
   - Reverse-engineers CadQuery code from a 3D point cloud. Built on Qwen2-1.5B; trained on 1 M procedurally generated CAD programs.
   - **Why try it here:** if you have a STEP/STL of a vendor part (e.g. NEMA-17 stepper), this gets you a *parametric* CadQuery model of it — the bootstrap path to the `design/cad/_vendor_envelopes/` library that `05-…mitigation.md §2.C.4` recommends.

4. **Text-to-CadQuery** — [Text-to-CadQuery/Text-to-CadQuery](https://github.com/Text-to-CadQuery/Text-to-CadQuery) (Xie & Ju, 2025; `xie2505texttocadqueryanew`)
   - End-to-end pipeline: data annotation (Gemini 2.0 Flash) → fine-tuning (six open LMs from CodeGPT to Qwen2.5-7B) → inference → STL render → Gemini eval → metrics. Best fine-tune (Qwen2.5-3B) hits top-1 = 69.3 %, median CD = 0.191.
   - **Why try it here:** the cleanest "fine-tune your own small LM on a CadQuery corpus" reference implementation we have — useful if a domain-specific model trained on `design/cad/**/cad_model.py` ends up making sense.

### 2.2 Second-tier (read first; clone if first-tier doesn't fit)

| Tool | Repo / project page | What it adds |
|---|---|---|
| **DeepCAD** | [ChrisWu1997/DeepCAD](https://github.com/ChrisWu1997/DeepCAD) | The 2021 baseline that almost every newer paper benchmarks against; the `DeepCAD` dataset (~170 k models with construction sequences) is the de facto pre-training corpus for everything in §2.1 above. |
| **Text2CAD** | [SadilKhan/Text2CAD](https://github.com/SadilKhan/Text2CAD) (NeurIPS 2024; `khan2024text2cadgeneratingsequential`) | Same dataset/pipeline lineage; emits CAD construction sequences rather than CadQuery code. |
| **GenCAD** | [ferdous-alam/GenCAD](https://github.com/ferdous-alam/GenCAD) (Alam et al., 2024; `alam2024gencadimagegeneratedcad`) | Image-conditional; transformer + diffusion. Pre-cursor to CAD-Coder. |
| **CAD-MLLM / Omni-CAD** | [CAD-MLLM project page](https://cad-mllm.github.io/) (`xu2024cadmllmunifyingmultimodalityconditioned`) | First multimodal (text + image + point-cloud) CAD generator; introduced topology-quality metrics (Segment Error, Dangling-Edge Length, Self-Intersection Ratio) that are useful as additional CI gates regardless of which model you use. |
| **CAD-Assistant** | [datasetninja/CAD-Assistant](https://github.com/datasetninja/CAD-Assistant) (`mallis2025cadassistanttoolaugmentedvllms`) | Tool-augmented VLLM agent; back-end is FreeCAD's Python API. Reference implementation for the "Judge agent + tool calls" pattern in `05-…mitigation.md`. |
| **CADCrafter** | [chen-yuxuan/CADCrafter](https://github.com/chen-yuxuan/CADCrafter) (Chen et al., 2025; `chen2025cadcraftergeneratingcomputeraided`) | DPO fine-tuning with code-checker feedback as the preference signal. Reaches 3.6 % Invalid Rate on DeepCAD multi-view. Useful template for *training-time* incorporation of the §2.A deterministic verifiers. |
| **GenCAD-Self-Repairing** | code release per `tsuji2025gencadselfrepairingfeasibilityenhancement` | 65.84 % repair rate of previously infeasible B-reps via latent-space diffusion guidance. |
| **CADReview** | code release per `chen2025cadreviewautomaticallyreviewing` | The benchmark showing GPT-4o detects only 41.5 % of human-made OpenSCAD errors. Run this *before* you decide to trust any single-model self-correction loop. |
| **ArtiCAD** | code release per `shui2026articadarticulatedcad` | Connector-first articulated-CAD generation. The architectural validation for the `make_skeleton()` + interface-contract recommendation in `05-…mitigation.md §2.C.1–.2`. |
| **cadrille** | [cadrille project](https://github.com/datasetninja/cadrille) (Mallis et al., 2025) | RL-finetuned multimodal CAD reconstruction. Newer than CAD-Assistant from the same group. |
| **DeepSCAD / SkexGen / HNC-CAD / BrepGen** | Various | Foundational sketch-and-extrude / B-rep generative models. Read for representation choices, clone only if you need the specific dataset format. |

### 2.3 LLM-tooling integrations worth a pilot

- **FreeCAD-MCP** — [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) — MCP server that lets Claude/GPT drive FreeCAD via the same protocol the GitHub MCP server in this repo already uses. The most direct way to give Claude Opus 4.7 *iterative* control over the kernel rather than one-shot code emission, which is the failure mode `05-…mitigation.md §1` documented.
- **OnPy** — [kyle-tennison/onpy](https://github.com/kyle-tennison/onpy) — Python-FeatureScript wrapper for Onshape. Useful if you want LLM output to land in Onshape (cloud, versioned, browsable) rather than a local STEP.
- **CadQuery MCP** servers — several community implementations (search GitHub for `cadquery mcp`); none yet canonical, but worth tracking if FreeCAD-MCP's mapping of CadQuery primitives ends up awkward.

---

## 3. Datasets you might actually use

| Dataset | Source | Size | Why you'd download it |
|---|---|---|---|
| **DeepCAD** | [ChrisWu1997/DeepCAD](https://github.com/ChrisWu1997/DeepCAD) | ~170 k construction sequences | The pre-training corpus for every model in §2.1. |
| **Fusion 360 Gallery Reconstruction Dataset** | [AutodeskAILab/Fusion360GalleryDataset](https://github.com/AutodeskAILab/Fusion360GalleryDataset) | ~8 k sequences | Higher-quality, designer-authored sequences; the standard generalisation test set. |
| **ABC** | [https://archive.nyu.edu/handle/2451/61215](https://archive.nyu.edu/handle/2451/61215) | 1 M+ B-rep CAD models | Raw STEP/OBJ at scale; backbone of CAD-Recode's procedural training set. |
| **SketchGraphs** | [PrincetonLIPS/SketchGraphs](https://github.com/PrincetonLIPS/SketchGraphs) | 15 M sketches | Sketch-level training, used by CAD-LLM. |
| **Text2CAD** dataset | bundled with the model repo | ~170 k text–CAD pairs | Text-conditioning ground truth. |
| **GenCAD-Code** | [anniedoris/GenCAD-Code](https://github.com/anniedoris/GenCAD-Code) | 163 k image–CadQuery pairs | The CAD-Coder training set; closest to "CAD images → code" we have. |
| **Omni-CAD** | per `xu2024cadmllmunifyingmultimodalityconditioned` | ~450 k multimodal | Text + image + point-cloud annotations. |

None of these have powder-dispenser-relevant geometry; their value is *training/evaluation*, not as a starting CAD library.

---

## 4. Commercial CAD subscriptions worth a trial

Cost-tiered. The proposal context (#26, BYU NASA Space Grant, sub-\$10 k hardware target) frames "worth trying" as: low monthly cost, headless or scriptable, exports clean STEP, and either has a generous free tier or per-seat pricing that survives a graduate-student budget.

| Product | Pricing (May 2026) | Trial verdict | Source for claims |
|---|---|---|---|
| **Onshape Education / Free** | Free for public/education; \$1,500+/yr commercial | **Try.** Browser-based, full Parasolid kernel, **REST API + FeatureScript** for full automation, and PR #7 already validated end-to-end auth (HTTP 200 on Part Studio + Assembly + BOM endpoints). Best vendor-platform candidate for an "LLM emits FeatureScript / OnPy → Onshape regenerates → REST API exports STEP" loop. | PR #7, `03-…landscape.md §3` (FeatureScript row). |
| **Zoo.dev (Text-to-CAD)** | Free 20–40 min/mo; pay-as-you-go \$0.0083/s ≈ \$0.50/min; Plus \$20/mo (400 min); Pro \$99/mo (unlimited); Team \$399/mo/user | **Try.** The only commercial Text-to-CAD with a public **API** that emits **B-rep STEP** rather than mesh. The free tier is enough for ~10–20 doser-module-sized prompts/mo. Worth a baseline comparison vs the §2.1 OSS pipeline. | [zoo.dev/zoo-pricing](https://zoo.dev/zoo-pricing); confirmed via web search at the time of writing. |
| **Autodesk Fusion 360** | Free for personal use / education / startups; \$680/yr commercial; Generative Design extension extra | **Already in scope.** Fusion's *Generative Design* extension is the canonical commercial topology-optimization tool (`03-…landscape.md §2`); useful for *organic-form* concepts but produces the hard-to-edit mesh outputs the proposal explicitly contrasts itself against. Use only as a baseline. | `03-…landscape.md §2`, vendor pricing page. |
| **nTop (formerly nTopology)** | Subscription; per-seat (≈ \$10 k+/yr historically; education tier exists) | **Skip** unless someone gives us a seat. Field-driven implicit modelling is best-in-class for AM-oriented lattices, but the cost and the Linux-headless story (PR #7 \"Cost / Linux-headless reality check\") put it outside the proposal's own framing. | `03-…landscape.md §2`, PR #7. |
| **Autodesk Forma / Spacemaker** | Subscription | Skip — building/architecture, not engineering hardware. | n/a |
| **PTC Creo Generative / Siemens NX TO / ANSYS Discovery / Altair Inspire** | Enterprise quote | Skip; same TO/GD class as Fusion but costlier and less scriptable. | `03-…landscape.md §2`. |
| **Spline AI / Meshy / Tripo / Luma** | \$10–\$30/mo each | Skip for engineering work — they emit textured meshes for media / games, not editable parametric CAD. | n/a; consensus across `03`/`04`. |
| **Anthropic Claude (Pro / Team / API)** | \$20/mo Pro; API metered | **Already in use** as the underlying model for this repo's coding-agent workflow. The PR #35 review is the canonical evidence base for what it gets wrong on spatial reasoning; `05-…mitigation.md` is the canonical mitigation list. The bet of this repo is on the *workflow* around the model, not on swapping the model. | n/a |
| **OpenAI / Gemini API** | Metered | Worth keeping budget for the *VLM Judge* role (CADSmith pattern); GPT-4o or Gemini 2.0 Flash as a *second* opinion on rendered three-view images is the highest-leverage single mitigation in §3 of `05-…mitigation.md`. | `05-…mitigation.md §5`. |

---

## 5. Powder-dispensing side: very little open source

The asymmetry in this list reflects the asymmetry in the field. Every commercial powder-dispenser cited in `01-…commercial-landscape.md` is closed (Mettler-Toledo Quantos, Chemspeed SWING/FLEX, Unchained Labs, Coperion K-Tron, Schenck, Gericke, Brabender, Movacolor, Freeman FT4, Sartorius), and HT-READ (Vecchio/UCSD; `02-…academic-literature.md`) — the only published automated multi-powder + metal-AM platform — does not release CAD or firmware.

What does exist:

| Resource | Where | Why it's relevant |
|---|---|---|
| **OpenFlexure** | [openflexure.org](https://openflexure.org/), [openflexure/openflexure-microscope](https://gitlab.com/openflexure) | Closest precedent for *open-hardware lab automation in the < \$1 k stack* — printable mechanics, parametric OpenSCAD, peer-reviewed. Architectural reference for documentation/release practices. |
| **Jubilee** | [machineagency/jubilee](https://github.com/machineagency/jubilee) (UW Machine Agency) | Open-hardware multi-tool platform (E3D tool-changer + BedSlinger). Several published powder-handling tool heads in the lab-automation literature use it as a substrate. The most aligned chassis to mimic. |
| **Opentrons OT-2 / Flex** | [Opentrons/opentrons](https://github.com/Opentrons/opentrons) | Liquid-handling, not powder, but the Python protocol API is the de facto reference for "what an open SDL hardware API looks like". |
| **Bahr 2018 collaborative-evaluation dataset** | per `bahr2018collaborativeevaluationof` | Inter-platform Quantos evaluation data; useful as a *target benchmark* for any new doser's accuracy/RSD numbers. |
| **Aerosint (Coperion)** powder-deposition data | per `neirinck2021powderdepositionsystems` | No code release, but the only published quantitative comparison of selective-deposition mechanisms for multi-metal PBF. |

The gap identified in `01-…commercial-landscape.md §6` ("no sub-\$10 k automated multi-powder doser validated for metal AM feedstocks") is reflected in the GitHub ecosystem: there is **no equivalent of OpenFlexure for multi-powder dosing**. That, again, is the gap the proposal is positioned to fill.

---

## 6. Recommended trial set for this repo (concrete next steps)

If we had to spend one PR-worth of effort, in priority order, on tools from this list:

1. **Add `tests/test_cad_model.py` to `design/cad/single-channel-module/`** using direct OCP calls (watertightness, connected components, vendor-envelope match, derived clearances). No new dependency beyond what CadQuery already pulls in. This is the §A guardrail set from `05-…mitigation.md` and closes ~half of the PR #35 defect classes with no model change at all.
2. **Pilot CAD-Coder on the `single-channel-module` prompt** ([anniedoris/CAD-Coder](https://github.com/anniedoris/CAD-Coder)). Self-hostable, open weights, already speaks CadQuery — gets us a baseline number for "what does an OSS VLM produce for this prompt" without spending API budget.
3. **Pilot CADSmith** ([jabarkle/CADSmith](https://github.com/jabarkle/CADSmith)) on the same prompt as the architectural reference for the multi-agent + Judge pattern. Compare its output to the PR #35 artefact directly.
4. **Bootstrap `design/cad/_vendor_envelopes/` with CAD-Recode** ([filaPro/cad-recode](https://github.com/filaPro/cad-recode)) on the COTS-part STEP files referenced in #25 (NEMA-17, GT2 pulley, 6805ZZ bearing, 5 mm solenoid). Replaces hand-authored envelope models with a parametric CadQuery model per part.
5. **One \$20/mo Zoo.dev Plus seat** ([zoo.dev/zoo-pricing](https://zoo.dev/zoo-pricing)) for a one-month commercial-Text-to-CAD baseline. Compare directly with the §2.1 OSS pipeline output for the same prompt.
6. **Wire OrcaSlicer CLI into CI** as the cheapest manufacturability gate; catches `05-…mitigation.md §A.6`.

Items 1, 2, 4, 6 are free in money and runtime. Items 3 and 5 cost a GPU-day and \$20 respectively.

What we should *not* do: subscribe to nTop, Creo, NX, Discovery, or Inspire on the proposal budget. Their outputs do not survive the editability/scriptability filter the proposal is built around (see `03-…landscape.md §2` and PR #7's reality-check sub-table).

---

## Appendix — provenance and update process

Same as the rest of `paper/background/`: claims here are anchored to the citation keys defined in the per-file References sections of `01`–`05` and to the raw Edison artifacts under [`edison_artifacts/`](edison_artifacts/). New material in this note that does not appear in `01`–`05` (Zoo.dev pricing, the GitHub URLs themselves, OnPy, FreeCAD-MCP, OpenFlexure, Jubilee, Opentrons) was verified by direct vendor / repository lookup at write time and should be re-verified before being copied into `paper/main.tex` / `paper/rsc.bib`.

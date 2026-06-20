For the powder doser, I recommend a **code-first, KiCad-backed workflow**, with **SKiDL + headless KiCad as the primary path**, **atopile as the runner-up**, and **tscircuit only as an experimental third option**.

## What matters most
The project constraints are brutal in a useful way: no GUI, no large in-house model training, everything in Git, everything runnable in CI, and an LLM coding agent that edits text and runs commands. That rules out a lot of shiny things.

The best fit is the stack that is:
- plain-text and reviewable in Git
- runnable headlessly in Ubuntu CI
- compatible with existing KiCad 7 rendering/export workflows
- usable by Copilot as a text/code authoring tool
- not dependent on closed SaaS, logins, or proprietary runtimes

## 1. Concise comparison of the main approaches

### A. GUI EDA suites with AI features
Examples: **KiCad**, **Altium 365**, **Cadence Allegro/OrCAD X**, **Siemens Xpedition/PADS**, **Zuken CR-8000**, **Fusion Electronics/EAGLE**, **EasyEDA**.

- **Up-front training/model requirements:** Usually none for the user, but AI features rely on vendor-owned models and data.
- **Scriptable/version-controllable:** 
  - **KiCad:** good. Text-based files, Python automation, `kicad-cli`, CI-friendly [gen_eda_landscape.answer.md; code_based_eda_frameworks.answer.md].
  - Most commercial suites: weak to moderate for Git/CI because of closed ecosystems and less transparent file formats [gen_eda_landscape.answer.md].
- **Bottom line:** KiCad is the only one here that cleanly fits your repo/CI philosophy.

### B. AI-native / generative EDA SaaS
Examples: **Flux.ai**, **JITX**, **Quilter**, **CELUS**, **SnapMagic/SnapEDA**, **Diadem**, **Cofactr**, **Allspice**.

- **Up-front training/model requirements:** No local training, but they depend on vendor-hosted models or proprietary engines.
- **Scriptable/version-controllable:** 
  - **JITX:** high scriptability, but proprietary language/runtime [code_based_eda_frameworks.answer.md; gen_eda_landscape.answer.md].
  - **Flux.ai / CELUS / SnapMagic:** more cloud workflow than repo-native workflow [gen_eda_landscape.answer.md].
  - **Quilter:** research/open baseline, but not a practical production path here; HiePlace beat it by **76.7%–91.3% cost reduction** with huge runtime cuts in academic comparisons [gen_eda_landscape.answer.md].
- **Bottom line:** interesting, but mostly blocked by SaaS dependence, credentials, closed tooling, or poor fit to headless GitHub automation.

### C. Design-as-code frameworks
Examples: **SKiDL**, **atopile**, **tscircuit**, **Edea**, **KiCad Python/IPC + `kicad-cli`**, **Horizon EDA**, **PCBmodE**, **gEDA**.

- **Up-front training/model requirements:** none.
- **Scriptable/version-controllable:** best in class.
- **Strongest options:**
  - **SKiDL:** Python EDSL, mature, text-first, reusable generators, built-in ERC, easy CI [code_based_eda_frameworks.answer.md].
  - **atopile:** `.ato` HDL compiled into KiCad artifacts; very Git/CI friendly [code_based_eda_frameworks.answer.md].
  - **KiCad Python + `kicad-cli`:** strongest downstream artifact/export/DRC path and already aligned with your current CI [code_based_eda_frameworks.answer.md; open_hardware_eda_for_labs.answer.md].
  - **Edea:** useful as glue around KiCad artifacts in CI [code_based_eda_frameworks.answer.md].
- **Bottom line:** this is the right family for the powder doser.

### D. Research-grade LLM/ML generation for schematics, placement, routing
Examples: **PCBSchemaGen**, **HWE-Bench**, **PCEval**, **FanoutNet**, **HiePlace**, **AnalogCoder**, **MenTeR**, **AnalogSAGE**.

- **Up-front training/model requirements:** ranges from training-free prompting to major dataset/training requirements.
- **Scriptable/version-controllable:** usually yes as research code, but not mature as engineering workflow.
- **Reality check:**
  - **PCBSchemaGen** is promising: **93.3% success on easy tasks**, **78.1% on hard tasks**, using SKiDL plus constraint checks and knowledge-graph validation [code_based_eda_frameworks.answer.md; eda_datasets_benchmarks.answer.md].
  - **HWE-Bench** is the cold shower: best full-design pass rate only **8.15%** [code_based_eda_frameworks.answer.md].
  - **FanoutNet** reported **100% routability** on its fanout benchmarks and **6.8% wirelength improvement**, but that is fanout, not full board routing [pcb_placement_routing_ml.answer.md].
- **Bottom line:** good for ideas and future augmentation, not for primary production workflow.

## 2. Most feasible approaches for the powder doser

### Most feasible: **SKiDL + KiCad + `kicad-cli`**
Why:
- Your agent is already operating in a text-only sandbox. SKiDL is Python. Copilot likes Python.
- The doser has repeated modules: stepper channel, vibration/solenoid/servo outputs, HX711 inputs, expansion connectors. SKiDL generator functions and loops are a natural fit.
- Existing CI already exports KiCad SVG/PDF headlessly. This is the downstream half of the workflow already done.
- HardOps-style hardware CI is directly aligned with this approach [open_hardware_eda_for_labs.answer.md; code_based_eda_frameworks.answer.md].

### Second most feasible: **atopile + KiCad**
Why:
- Very strong design-as-code story.
- Native focus on reusable modules and package-style dependency management.
- Compiles toward KiCad artifacts, so it fits your current rendering/export backbone.
- Slightly riskier than SKiDL because the ecosystem is younger and Copilot has seen much more Python than `.ato`.

### Feasible but lower priority: **KiCad text artifacts + Python/Edea automation only**
Why:
- Even without a full code-first HDL, you can automate a lot around KiCad: project templating, variant generation, BOM normalization, DRC, Gerbers, previews.
- This is the lowest-risk extension of what you already do.
- But it gives you less elegant modular circuit generation than SKiDL/atopile.

### Experimental only: **tscircuit**
Why:
- Strong CI and text story.
- Copilot is good at TypeScript/React.
- But it is less mature and less aligned with your existing KiCad-centric toolchain.

## 3. Can each feasible approach run inside your GitHub/Copilot environment?

### SKiDL + KiCad
**Yes.**
- **Runs headlessly:** yes.
- **Needs GUI:** no.
- **Needs login/credentials:** no.
- **Needs large model training:** no.
- **Fit with repo:** excellent.
- **Caveat:** SKiDL mainly covers schematic/netlist generation. Final board placement/routing still needs either scripted placement plus limited autorouting or a later human KiCad layout pass.

### atopile + KiCad
**Yes, likely.**
- **Runs headlessly:** yes.
- **Needs GUI:** no.
- **Needs login/credentials:** no.
- **Needs large model training:** no.
- **Fit with repo:** very good.
- **Caveat:** younger ecosystem; expect more setup friction and more compiler/library edge cases than with Python.

### KiCad + Python/Edea automation
**Yes.**
- **Runs headlessly:** yes.
- **Needs GUI:** no for exports/checks/transforms; maybe yes later for nuanced placement/routing.
- **Needs login/credentials:** no.
- **Needs large model training:** no.
- **Fit with repo:** excellent.

### tscircuit
**Probably yes, but not my first choice.**
- **Runs headlessly:** yes.
- **Needs GUI:** no.
- **Needs login/credentials:** no.
- **Needs large model training:** no.
- **Fit with repo:** moderate.
- **Caveat:** weaker fit with your existing KiCad 7 artifact pipeline and less mature manufacturing-validation path.

### What is blocked
- **Flux.ai / CELUS / SnapMagic / similar SaaS:** blocked by cloud/login/proprietary workflow.
- **JITX:** blocked in practice by proprietary runtime and licensing, even though it is code-based.
- **Closed enterprise suites:** blocked by GUI/licensing/workstation assumptions.
- **Research ML routing/placement stacks:** blocked in practice by maturity, integration burden, and in some cases training/compute assumptions.

## 4. Ranked implementation recommendations

### Recommendation 1: **SKiDL for schematic generation, KiCad for board/layout/artifacts**
**What it is and workflow**
1. Write the doser electronics as Python modules in `hardware/electronics/skidl/`.
2. Define reusable generators: RP2040 core, power input/protection, HX711 channel, stepper-driver channel, solenoid/servo output block, expansion bus connector block.
3. Generate netlist and, where possible, bridge into KiCad project artifacts.
4. Maintain a KiCad project as the physical/layout target.
5. Run CI to export SVG/PDF renders, DRC/ERC reports, Gerbers, drill, pick-and-place, and BOM via `kicad-cli`.

**Pros**
- Best fit for Copilot.
- Best fit for repeated modular channels.
- Pure text, easy diff/review.
- Leverages your existing KiCad 7 CI immediately.
- Supported by the strongest practical evidence base for code-first open hardware workflows [code_based_eda_frameworks.answer.md; open_hardware_eda_for_labs.answer.md].

**Cons**
- Schematic capture is code-first, but physical board design is still downstream.
- Symbol/footprint mapping can be fiddly.

**Potential limitations**
- I cannot claim fully automated, production-grade placement/routing from the evidence. The reviews consistently show that this remains unreliable. HWE-Bench's **8.15%** full-design pass rate is the warning label here [code_based_eda_frameworks.answer.md].
- Mixed-signal layout around noisy motors and sensitive load-cell inputs still wants human judgment.

**Necessary next steps in the repo**
- Install: `pip install skidl`
- Add files:
  - `hardware/electronics/skidl/parts.py`
  - `hardware/electronics/skidl/blocks.py`
  - `hardware/electronics/skidl/powder_doser.py`
  - `hardware/electronics/kicad/powder_doser/` as the physical KiCad project
- Add CI jobs:
  - run SKiDL generation
  - run KiCad ERC/DRC
  - export schematic PDF/SVG and PCB SVG/PDF
  - export Gerbers/drill/position/BOM
- Commit generated artifacts either on release tags or to a dedicated artifacts branch; do not churn the main branch on every commit unless you want noisy diffs.

### Recommendation 2: **atopile as the primary source, KiCad as downstream physical tool**
**What it is and workflow**
1. Author module definitions in `.ato`.
2. Model repeated powder-dosing channels as parameterized reusable blocks.
3. Compile to KiCad artifacts.
4. Reuse the existing KiCad headless export pipeline.

**Pros**
- Very clean hardware-as-code story.
- Strong modularity and reuse.
- Good philosophical match to your CadQuery/OpenSCAD workflow.

**Cons**
- Younger ecosystem.
- Higher chance of agent friction than Python.

**Potential limitations**
- Less battle-tested than SKiDL for this exact GitHub-agent workflow.
- Still does not remove the layout problem.

**Necessary next steps in the repo**
- Install atopile and pin version in CI.
- Add:
  - `hardware/electronics/atopile/ato.yaml`
  - `hardware/electronics/atopile/src/*.ato`
- CI:
  - compile atopile project
  - run KiCad headless exports on generated output
  - publish BOM/Gerbers/renders exactly as you do now

### Recommendation 3: **Keep KiCad as source of truth, add Python/Edea automation around it**
**What it is and workflow**
1. Continue authoring the actual KiCad project.
2. Use Python/Edea scripts for repetitive edits, variant generation, connector/bus replication, BOM normalization, and CI checks.
3. Use Copilot mainly as a KiCad-file and script author, not as a schematic generator.

**Pros**
- Lowest risk.
- Minimal change to current repo and workflows.
- Makes immediate use of existing headless KiCad setup.

**Cons**
- Less elegant than full design-as-code.
- Reuse and parametric generation are weaker.

**Potential limitations**
- Still partially GUI-shaped if you want high-quality layout.

**Necessary next steps in the repo**
- Install Edea if needed.
- Add Python tooling under `hardware/electronics/tools/`.
- Add CI steps for deterministic lint/export/report generation.
- Use a stable project template for each board variant/module.

### Recommendation 4: **Experimental tscircuit pilot for one small daughterboard only**
**What it is and workflow**
Use tscircuit to prototype a simple board, such as an HX711 load-cell daughterboard or a modular I/O expander, not the full controller.

**Pros**
- Very agent-friendly for TS/JS-heavy developers.
- Excellent text-first CI ergonomics.

**Cons**
- Lower confidence for a production mixed-signal controller board.
- Less aligned with your existing KiCad artifact stack.

**Potential limitations**
- Maturity and library coverage.

**Necessary next steps in the repo**
- Add a Node toolchain and a separate `hardware/electronics/tscircuit/` package.
- Limit scope to a contained board.
- Evaluate output quality before expanding.

## The recommendation, plain version
If you want the best odds of success without pretending the field is more mature than it is:

1. **Adopt SKiDL + KiCad + `kicad-cli` now.**
2. **Prototype atopile in parallel on one sub-board or reusable module library.**
3. **Use KiCad for final physical board realization and CI artifact generation.**
4. **Do not bet the project on autonomous LLM schematic synthesis or ML placement/routing.** Use those only as assistants, not as the source of truth.

That gives you a workflow that is open, scriptable, reproducible, Git-native, and realistic about where the human still has to touch the board. Sad for the robot. Good for the doser.

- **Discretionary analytical decisions made during the analysis**
- Prioritized feasibility inside a headless GitHub/Copilot/KiCad environment over theoretical automation performance reported in academic benchmarks.
- Ranked SKiDL above atopile because the target environment centers on Copilot text editing and Python is more mature and better supported than `.ato` for agent-authored code.
- Treated KiCad as the mandatory downstream physical-design/export layer for all practical recommendations because the repository already has working KiCad 7 headless CI.
- Excluded closed SaaS tools from recommended primary workflows even when they offered stronger automation, because the user explicitly required local, version-controlled, headless operation without login-bound dependencies.
- Treated research ML/LLM schematic/placement/routing systems as assistive or experimental rather than production recommendations because benchmark evidence showed major reliability gaps at end-to-end board design scale.
- Recommended human-in-the-loop final placement/routing for mixed-signal motor-control/load-cell boards rather than claiming full autonomy, based on the review evidence that schematic/topology success does not imply manufacturable board success.
- Suggested artifact generation on release tags or a dedicated artifacts branch as a repo hygiene choice, since either commit strategy is scientifically valid and affects workflow noise rather than correctness.
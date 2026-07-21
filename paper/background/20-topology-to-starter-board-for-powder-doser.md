_Edison Scientific `ANALYSIS` pass over **this repository's actual KiCad control-board schematic** (the `hardware/test-module/kicad/` project from PR [#61](https://github.com/vertical-cloud-lab/powder-doser/pull/61) — `test_module.kicad_sch`, `.kicad_sym`, `generate.py`, etc. — uploaded as a single zipped collection), answering @lbwinters'/@sgbaird's question on PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654166992) about the **topology → router-ready starter-board gap**: what would it take to turn the existing schematic into the footprinted, outlined `.kicad_pcb` that Quilter/DeepPCB (notes [`16`](16-quilter-ai-pcb-layout.md)/[`17`](17-deeppcb-ai-pcb-routing.md)) require as input, and which intermediate tools (CELUS, note [`18`](18-celus-ai-schematic-floorplan.md); Flux.ai; JITX; atopile; tscircuit; SKiDL; KiCad-CLI + Python) can do that headlessly in CI. Produced by [`edison_run_topology_to_board_analysis.py`](edison_run_topology_to_board_analysis.py); raw artifacts under [`edison_artifacts/topology_to_board_for_powder_doser.*`](edison_artifacts/). Kept verbatim._

Here is the analysis of the project's state, an evaluation of intermediate automated tools, their headless CI suitability, and concrete recommendations for how the Copilot coding agent should proceed to produce a starter board for Quilter or DeepPCB.

### 1. Characterization of the Current Schematic
Based on a direct audit of `test_module.kicad_sch` and `generate.py`:
- **Present:** A complete topology with 14 unique components (U1-U5, M1-M3, C1-C3, J1, SR1, SOL1) and 20 distinct nets (including mixed-signal power constraints like the isolated `+12V` rail with C3 and SR1 for back-EMF clamping). The project uses a project-local symbol library (`test_module.kicad_sym`). 
- **Missing for a router-ready board:** 
  1. **Footprints:** All 26 `Footprint` properties in the schematic are completely empty strings. The footprints do not currently exist in the project (no `.kicad_mod` files or `fp-lib-table`).
  2. **`.kicad_pcb` File:** There is no board file.
  3. **Board Outline (Edge.Cuts):** Because there is no `.kicad_pcb`, there is no defined board area.
  4. **Component Placement/Floorplan:** No components have (x,y) coordinates on a board layout. Quilter/DeepPCB need the components *imported* into a board file before they can route them.

### 2 & 3. Evaluation of Generative AI / Automated EDA Tools & Headless Suitability
Quilter and DeepPCB both require an initial board state to start (Quilter strictly requires a `.kicad_pcb` with footprints assigned and a board outline; DeepPCB requires a netlist, footprints, and an outline). Here is how intermediate tools stack up for generating that initial state:

* **CELUS:** Evaluates requirements and block diagrams to select components and emit a footprinted schematic/netlist. 
  * **Headless in CI:** **No.** It is a login-walled, proprietary SaaS web application. It cannot be scripted via GitHub Actions/Copilot.
* **Flux.ai:** AI-assisted web-based schematic/PCB editor. Can export to KiCad.
  * **Headless in CI:** **No.** Proprietary, GUI-first web SaaS.
* **JITX:** Domain-specific language (Stanza) that compiles code to a complete `.kicad_pcb` with footprints, outline, and an auto-placed floorplan. Best-in-class output for your specific requirements.
  * **Headless in CI:** **Yes, but paywalled.** Has a CLI compiler (`jitx`) that runs on Linux, but requires a registered account and license to run. Free tier exists for evaluation, but the compiler isn't open source.
* **atopile:** Open-source Python-like DSL (`.ato`) that compiles to KiCad. Allows embedding footprint strings in code and exports a `.kicad_pcb` natively.
  * **Headless in CI:** **Yes, fully.** `pip install atopile`, then `ato build`. Open source (Apache 2.0). However, it does not do board outlines or placement out of the box—you get a pile of footprints at (0,0) unless explicitly coded.
* **tscircuit:** TypeScript/React-based design-as-code tool. Can export `.kicad_pcb` including a specified Edge.Cuts board outline.
  * **Headless in CI:** **Yes, fully.** `npx @tscircuit/cli export`. Open source (MIT).
* **SKiDL:** Pure Python netlist generation.
  * **Headless in CI:** **Yes.** `pip install skidl`. But it only generates the `.net` file, not the `.kicad_pcb`.
* **KiCad-CLI + Python (`pcbnew` or `kiutils`):** Standard KiCad tools. `kicad-cli sch export netlist` runs headlessly. There is **no** `kicad-cli pcb create` from schematic, but Python libraries can script it. 
  * **Headless in CI:** **Yes, fully.** A pure Python pip package like `kiutils` or KiCad's bundled `pcbnew` module can load a netlist, fetch footprints, draw an Edge.Cuts rectangle, and save a `.kicad_pcb` entirely headless. 

### 4. Ranked Recommendations for the Copilot Coding Agent

#### Rank 1: The "Design-as-Code to KiCad API" Hybrid (Native `generate.py` Extension + `kiutils`)
Instead of adopting a whole new DSL (atopile/tscircuit), leverage the fact that you already generate your schematic via `generate.py`. Have the coding agent extend the Python pipeline.

* **Workflow:**
  1. Have the Copilot agent modify `generate.py` to populate the `Footprint` properties with valid KiCad library strings. 
     * *Pico W:* Use standard `Module:RPi_Pico_SMD_TH`.
     * *Adafruit breakouts (#2305, #3190):* Import the open-source `Adafruit_KiCad_Library`.
     * *Pololu / external:* Use standard 0.1" header proxies (`Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical` for the buck, etc.) or write quick custom `.kicad_mod` arrays using Python.
  2. Use `kicad-cli sch export netlist` in CI to generate the `.net` file.
  3. The agent writes a new script `build_board.py` using the `kiutils` pip package. The script parses the netlist, instantiates footprints, arranges them in a rough grid, draws a 100x80mm Edge.Cuts rectangle, and saves `test_module.kicad_pcb`.
  4. The generated `.kicad_pcb` is submitted to Quilter.
* **Pros:** 100% free, 100% headless, zero GUI interaction, leverages existing Python generation script. 
* **Cons/Limitations:** Proxied pin headers don't have the exact physical silk-screen outlines of the real Pololu/Adafruit boards. The initial layout grid is arbitrary and relies entirely on Quilter to untangle it. 
* **Next Steps for Repository:**
  1. Add `kiutils` to CI dependencies. 
  2. Map footprints in `PLACEMENTS` in `generate.py`. 
  3. Implement `build_board.py` logic.

#### Rank 2: Migration to `tscircuit` or `atopile`
If you want the intermediate board completely defined in code rather than scripting raw KiCad files, have the agent rewrite the schematic logic into one of the open-source EDA DSLs.

* **Workflow:** The agent translates `generate.py` into a single `test_module.tsx` (tscircuit) or `test_module.ato` (atopile), specifying footprints and board boundaries in code. CI runs `npx @tscircuit/cli` or `ato build` to emit the `.kicad_pcb`.
* **Pros:** Built explicitly for CI workflows. Clear syntax for defining board outlines.
* **Cons/Limitations:** Requires rewriting `generate.py` in a new language. You still face the footprint availability problem for custom modules.
* **Next Steps for Repository:** Install node/tscircuit in CI, prompt the agent to translate the 20 nets and 14 components into code, write custom component definitions for the Pololu modules.

#### Rank 3: Human-in-the-Loop GUI Initialization (Pragmatic approach)
If exact physical outlines and thermal constraints for the DRV8871/shunt regulator matter immediately, automation will fall short without a library.

* **Workflow:** 
  1. The agent extends `generate.py` to map footprints as in Rank 1. 
  2. A human opens the KiCad GUI once, imports the netlist to PCBnew, downloads the complex Tic T500 (dual-row + screw terminal) footprint from SnapEDA, places the shunt regulator (SR1) physically close to C3 and U5 for optimal back-EMF clamping (a mixed-signal routing constraint that AI placers struggle to prioritize without explicit grouping rules), defines the Edge.Cuts, and commits the "Starter Board" `.kicad_pcb`.
  3. Quilter is triggered manually or via API (if available on enterprise tier) to finish the routing.
* **Pros:** Ensures critical mixed-signal partitioning (ground planes and back-EMF paths) are respected, which Quilter might otherwise route inefficiently. Accurate physical footprints.
* **Cons/Limitations:** Breaks the "100% headless CI" goal. 

**Summary Recommendation:** Proceed with **Rank 1**. Instruct the Copilot agent to `pip install kiutils`, modify `generate.py` to assign standard KiCad 0.1" header proxies to the breakout boards, export the netlist headlessly, and generate an unplaced, outlined `.kicad_pcb` via a new Python build script. This achieves your CI goals immediately and provides the exact file Quilter requires.

***

### Discretionary Analytical Decisions:
- Selected `kiutils` over KiCad's bundled `pcbnew` Python module for the primary programmatic board generation script, as it is a pure-Python parser that can be trivially pip-installed in CI without invoking KiCad's C++ bindings or virtual framebuffers. 
- Mapped external breakout boards (Pololu/Adafruit) to standard KiCad 0.1" header footprints (`Connector_PinHeader_2.54mm`) as functional CI proxies, rather than attempting to script the generation of complex custom geometries natively without visual verification.
- Recommended a 100x80mm arbitrary Edge.Cuts boundary for the starter board; this is a discretionary default that Quilter can work within until mechanical constraints dictate otherwise.
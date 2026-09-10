The current Figure 1 caption does **not** make the HUMAN/AI division of labour unambiguous enough for PR97.

What the files show

- The current caption in `caption_fig1_overview.md` only describes device features and the timeline. It never says who did what.
- The compiled caption in `main.pdf` is the same: “Fig. 1 Platform overview. (a) Single-channel powder-doser module ... (e) Compressed design timeline...” with no HUMAN/AI attribution.
- PR97 explicitly asks for signposting throughout this section: `pr97_comments.md`, thread on `paper/main.tex line 189`: “clarify where ai was used. We should be signposting the design contributions of ai versus engineers throughout the manuscript--it should always be clear who did what.”
- PR97 also narrows the intended split: `pr97_comments.md`, thread on `paper/main.tex line 193`: the manuscript should mention “specific drawings given, including that some of them had dimensions and relations ... eventually, ai was only being used to model the parts, not to make design decisions beyond calculating relevant dimensions and tolerancing”.
- The manuscript body already states the intended division clearly. In `main.pdf`, Results/Discussion page 2 says: “the human team made the design decisions, supplied specifications and drawings, reviewed every output, and printed and tested the parts, while the AI tools did the modelling”. Figure 1’s caption does not carry that clarity into the figure itself.
- `pr97_comments.md` resource notes add two constraints the figure/caption must stay consistent with: (i) “No GUI CAD (Fusion 360 / SolidWorks) was used at any point”; (ii) later exploratory use of Zoo Design Studio with its Zookeeper agent should be distinguished from the main programmatic-CAD workflow.

Panel-specific assessment

- **Panel (a)** is explicitly a CAD render, not a photograph. `make_figures.py` labels it “annotated final single-channel assembly render” and overlays the note “CAD render; photograph of the printed platform to be added”. That helps with render-vs-photo status, but not with HUMAN-vs-AI authorship. Since the render comes from programmatic CAD assets (`paper/figures/assets/assembly_iso_final.png`; related assembly files named in the branch tree include `cad/mounting-plate-assembly/cad_model.py`, `cad/mounting-plate-assembly/render_assembly.py`, `design/cad/mounting-plate-assembly/cad_model.py`), readers can easily infer that the whole design was “AI-designed” unless the caption says otherwise.
- **Panel (b)** shows the powder-flow cross-section from `paper/figures/assets/single_channel_module_powder_flow.png`. Related branch-tree files include `design/cad/single-channel-module/cad_model.py` and `design/cad/single-channel-module/sketch_2d.py`. The caption correctly fixes the hopper point: “the auger tube itself is the powder reservoir, with no separate hopper,” matching the PR97 correction. But again it does not say that the flow-path concept and final architecture were human decisions, while the depicted geometry was AI-modelled.
- **Panel (c)** shows the tilt sweep from `paper/figures/assets/rotation_0_45_90.png`; related branch-tree source files include `design/cad/mounting-plate-assembly/diagrams/rotation_0_45_90.svg` and `design/cad/mounting-plate-assembly/diagrams.py`. The caption explains the fixed dispense point well. Still missing: the hinge/nozzle constraint reads like a CAD-derived insight unless the caption says it was a human-specified design requirement represented through AI-generated parametric CAD.
- **Panel (d)** is a schematic drawn in `make_figures.py`, not a CAD render. It describes operation, not authorship.
- **Panel (e)** is where signposting could have been easiest, but the current timeline labels only milestones (“Scoop/excavator sketch”, “Part-by-part redesign”, “97-entry design log”). It does not tell the reader that the sketching, architecture choices, review, printing, and testing were HUMAN, while the part models were generated through AI-assisted parametric CAD. The branch tree points to relevant files that support this distinction, including the human-side sketch `powder-excavator-sketch.jpg`, the engineering drawing path `cad/mounting-plate/drawing/engineering_drawing.pdf`, and the design-log paths named in PR97 (`DESIGN-LOG.md`, also noted as living in issue `#73` / PR `#74`).

Bottom line judgment

- **Not yet unambiguous.** The current figure/caption makes the platform understandable, but it does **not** satisfy the PR97 request that “it should always be clear who did what.”
- The main ambiguity is that panels (a)-(c) are all CAD-derived visuals, so without explicit wording, a reader could wrongly attribute the underlying design decisions to AI rather than to humans.
- The caption also misses a chance to state the important negative fact from PR97: **no conventional GUI CAD package was used**.

Rewritten caption

**Figure 1. Platform overview and division of labour.** **Human contributions:** the device concept, architecture, operating requirements, interface constraints, annotated or dimensioned reference drawings, review of each iteration, and the physical printing and testing workflow. **AI contributions:** generation of the parametric CAD models used to produce the rendered geometries in panels (a-c), primarily through programmatic CAD code; no conventional GUI CAD package (e.g. Fusion 360 or SolidWorks) was used. (a) Single-channel powder-doser module shown as a CAD render of the final architecture; a photograph of the printed platform will replace this render. The human team specified the module layout and component roles; AI tools produced the corresponding parametric model of the printed Archimedes auger, gear drive from a NEMA-11 stepper, tap-collar assembly, and servo-tilted hinged mounting plate on the baseplate. (b) Powder-flow path through the module cross-section, shown from an early rendered model: loading slots → helical channel → exit nozzle → collection cup on the balance. In the final design, the auger tube itself serves as the powder reservoir, with no separate hopper. (c) Tilt sweep about the fixed dispense point: the human-specified hinge geometry places the axis through the exit-nozzle tip so the dispense point does not translate as the channel tilts from 0° (sealed park) to 90° (vertical dispense); the illustrated geometry is AI-modelled. (d) Closed-loop gravimetric dosing concept. (e) Compressed design timeline from initial human sketching and architecture selection through AI-assisted part modelling, human review, and repository logging; the complete 97-entry design log is available in the repository.

Why this rewrite is more accurate

- It mirrors the explicit division already stated in the manuscript body in `main.pdf`.
- It does **not** overclaim AI decision-making. That matters because PR97 says AI was eventually “only being used to model the parts, not to make design decisions beyond calculating relevant dimensions and tolerancing”.
- It stays consistent with the available provenance paths in `all_branches_file_tree.txt`:
  - human sketch artifact: `powder-excavator-sketch.jpg`
  - human-facing engineering drawing artifact: `cad/mounting-plate/drawing/engineering_drawing.pdf` (also `.png`, `.svg`; generated via `cad/mounting-plate/engineering_drawing.py`)
  - AI/programmatic CAD sources for Figure 1-related visuals: `design/cad/single-channel-module/cad_model.py`, `design/cad/single-channel-module/sketch_2d.py`, `cad/mounting-plate-assembly/cad_model.py`, `design/cad/mounting-plate-assembly/diagrams.py`, and the figure assets under `paper/figures/assets/`
  - late exploratory Zoo-related files exist in the tree, e.g. `cad/meta-tools/logs/zoo-text-to-cad.log` and `paper/background/23-zds-transcript-editing-session.md`, so Zoo can be discussed in the manuscript, but Figure 1 does not need to name it unless this panel specifically depends on a Zoo-derived part.

Short prioritized action list for Figure 1

1. **Revise the caption first** to state the HUMAN/AI split explicitly, using wording close to the rewrite above.
2. **Add a brief in-figure signpost**, ideally in panel (e) or as a small global note: “Humans chose the design and reviewed/tested parts; AI generated parametric CAD models.”
3. **Avoid implying AI made architecture decisions** in panels (a)-(c); keep wording on AI to “modelled/rendered” rather than “designed”.
4. **Keep the no-hopper correction** exactly as now in panel (b), because `pr97_comments.md` explicitly flags this.
5. **If space allows, anchor the timeline to provenance artifacts** by citing the human sketch (`powder-excavator-sketch.jpg`) and the repository design log (`DESIGN-LOG.md` / issue `#73`, PR `#74`) in the main text or SI, not necessarily in the caption.

- Discretionary analytical decisions made during the analysis
- Used the manuscript body in `main.pdf` as the controlling statement of intended authorship when judging caption adequacy, because it contains the clearest explicit HUMAN/AI division.
- Treated branch-tree file paths as provenance evidence for likely relevant artifacts when the files themselves were not included in the bundle.
- Did not attribute any panel to Zoo Design Studio specifically, because the supplied figure bundle and branch-tree paths did not tie Figure 1 assets unambiguously to a Zoo-derived render.
- Focused the rewrite on authorship clarity rather than stylistic shortening, because the user’s stated priority was AI-vs-human signposting.
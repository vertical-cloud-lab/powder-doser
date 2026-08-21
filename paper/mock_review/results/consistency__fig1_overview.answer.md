Internal-consistency review for Figure 1 (`fig1_overview`) based only on the supplied bundle.

Figure 1 has four substantive consistency problems, three of them serious. The biggest issue is panel (b): the caption and manuscript text try to describe the final no-hopper, HR-100A-based design, but the embedded asset is visibly an earlier v2 concept that still shows a separate hopper/reservoir and a load-cell cup. There is also a drive-train mismatch in panel (a): the figure text says `GT2/gear drive`, while the manuscript body describes a printed gear train / spur pair and never a GT2 belt. Panel (a) also overclaims what is visible: the caption says the render shows the tap collar with solenoid and vibration motor, but those parts are not actually visible in the render. A smaller wording issue is panel (c) calling 0° a `sealed park`, which is stronger than what the manuscript body supports.

Detailed inconsistencies

1. Panel (b) still depicts a separate hopper/reservoir, contradicting the manuscript’s no-hopper claim.
- Figure caption (`caption_fig1_overview.md`, panel b):
  - `... loading slots → helical channel → exit nozzle → collection cup on the balance; in the final design the auger tube itself is the powder reservoir, with no separate hopper.`
- Manuscript body (`main.pdf`, §2.1 Platform overview):
  - `There is no separate hopper: powder is loaded directly into the printed Archimedes auger (25 mm OD) through loading slots in the auger tube, so the auger itself is the powder reservoir.`
- Reviewer correction (`pr97_comments.md`, lines 16–21 and 125–127):
  - `We haven't talked about or implemented a removeable hopper. We won't have one on the end design, just the full auger.`
  - `No hopper in the end design; the auger tube itself is the reservoir, loaded via slots.`
- But the actual panel-b source asset (`assets/single_channel_module_powder_flow.png`; branch-tree path also present as `design/cad/single-channel-module/renders/single_channel_module_powder_flow.png`) visibly says:
  - title text: `hopper → top loading slots → helical channel → exit nozzle → cup`
  - left annotation: `reservoir (bulk powder)`
  - and it shows a separate top box above the tube.
- Why this matters:
  - The caption tries to “correct” the early render in prose, but the image itself still tells the reader the opposite story.
- Proposed correction:
  - Best fix: replace panel (b) with a hopperless cross-section from a final-design asset. The branch tree suggests likely relevant files such as `paper/figures/assets/auger_geared_cross_section.png` and the source branch path `cad/auger-geared/archimedes-auger-geared-cross-section.png`.
  - If you keep the current v2 render, revise the caption to admit the mismatch explicitly:
    - `(b) Early v2 cross-section shown for flow-path intuition only. This historical render still includes a separate reservoir/hopper; in the final design, powder is loaded through slots in the auger tube, which itself serves as the reservoir.`

2. Panel (b) labels the sensing element as a load cell, contradicting the HR-100A analytical balance used in the manuscript and reviewer comments.
- Figure caption (`caption_fig1_overview.md`, panel b):
  - `... collection cup on the balance ...`
- Manuscript body (`main.pdf`, §2.1 Platform overview):
  - `Dispensed mass is measured by an analytical balance (A&D HR-100A, 0.1 mg readability) beneath the collection cup...`
- Manuscript body (`main.pdf`, §3.1 Fabrication / nearby methods text):
  - `Gravimetric feedback uses an A&D HR-100A analytical balance (0.1 mg readability) under the collection cup.`
- Reviewer correction (`pr97_comments.md`, lines 20 and 125–126):
  - `Also, it's an HR-100A load cell`
  - resource note clarifies the intended correction more precisely: `Sensing: A&D HR-100A analytical balance (0.1 mg) over RS-232 via MAX3232 — NOT an HX711 load cell.`
- But the panel-b asset (`assets/single_channel_module_powder_flow.png`; source path `design/cad/single-channel-module/renders/single_channel_module_powder_flow.png`) visibly labels the cup as:
  - `shared collection cup (load cell — v1.2)`
- Why this matters:
  - The panel mixes an obsolete sensing concept into the platform overview, while panel (d) and the text correctly describe the HR-100A balance.
- Proposed correction:
  - Best fix: replace the asset.
  - If retained temporarily, revise the caption to say exactly what the reader is seeing:
    - `The historical v2 render shown here still labels the cup as a load-cell concept; the final platform instead uses an A&D HR-100A analytical balance beneath the collection cup.`

3. Panel (a) figure text introduces a `GT2` drive that the manuscript does not support.
- In the figure-generation code (`make_figures.py`, lines 133–139), panel (a) callout text is:
  - `NEMA-11 stepper\n+ GT2/gear drive`
- Manuscript body (`main.pdf`, §2.1 Platform overview):
  - `The auger is driven through a printed gear train by a NEMA-11 stepper motor.`
- Manuscript body (`main.pdf`, fabrication text):
  - `gear train (printed spur pair, 2.25:1)`
- Reviewer snapshot contains no support for a GT2 belt in Figure 1; the resource notes instead emphasize the HR-100A and no-hopper corrections.
- The branch tree does show gear-related assets such as `paper/figures/assets/auger_assembly_iso.png` and `cad/auger-geared/stepper-pinion-iso.png`, but nothing in the supplied manuscript text supports a GT2 belt for this panel overview.
- Why this matters:
  - This is an unsupported mechanical claim introduced by the figure annotation itself.
- Proposed correction:
  - Change the callout in `make_figures.py` from:
    - `NEMA-11 stepper + GT2/gear drive`
  - to:
    - `NEMA-11 stepper + printed gear train`
  - or, if you want the ratio consistent with the body:
    - `NEMA-11 stepper + printed spur pair (2.25:1)`

4. Panel (a) caption claims visible solenoid and vibration-motor hardware that the render does not show.
- Figure caption (`caption_fig1_overview.md`, panel a):
  - `... printed Archimedes auger, gear drive from a NEMA-11 stepper, tap collar with solenoid and vibration motor, and servo-tilted hinged mounting plate on the baseplate.`
- Manuscript body (`main.pdf`, §2.1 Platform overview) does state those are real parts of the system:
  - `... a 12 V push–pull solenoid striking a printed tap collar ... and an eccentric-rotating-mass (ERM) vibration motor mounted on the same collar.`
- But the actual render asset (`assets/assembly_iso_final.png`; branch-tree path `paper/figures/assets/assembly_iso_final.png`) does not clearly show a solenoid or an ERM vibration motor. The panel-a callouts added in `make_figures.py` also do not identify either part separately; they only label `Auger bracket + tap collar`.
- Why this matters:
  - The caption says panel (a) shows hardware that the reader cannot verify in the render.
- Proposed correction:
  - Safer caption wording:
    - `Platform overview. (a) Single-channel powder-doser module CAD render showing the printed auger, auger bracket/tap-collar region, NEMA-11-driven gear train, and hinged mounting plate on the baseplate; the solenoid and vibration motor are part of the final system but are not clearly visible in this render.`
  - Or replace panel (a) with a render/photo where those components are actually visible. The branch tree suggests potentially relevant files outside the current bundle, for example `design/cad/tap-collar/renders/assembly_iso.png` and `paper/figures/assets/auger_assembly_iso.png`.

5. Panel (a) visually under-supports `servo-tilted hinged mounting plate`.
- Figure caption (`caption_fig1_overview.md`, panel a):
  - `... servo-tilted hinged mounting plate ...`
- Manuscript body (`main.pdf`, §2.1 Platform overview):
  - `The auger assembly rides on a hinged mounting plate whose tilt is set by a servo-driven gear sector...`
- The render asset (`assets/assembly_iso_final.png`) does show a sloped plate structure, but the servo and hinge mechanism are not obvious, and no callout names the servo or gear sector directly.
- Why this matters:
  - This is not as bad as the hopper/load-cell problems, but the caption promises a clearer visual identification than the panel provides.
- Proposed correction:
  - Tighten wording to what is plainly visible:
    - `... hinged mounting plate on the baseplate ...`
  - If you want to preserve the actuation detail, move it to the body or add a clearer inset/callout.

6. Panel (c) uses `sealed park`, which overstates what the body text supports.
- Figure caption (`caption_fig1_overview.md`, panel c):
  - `... tilts from 0° (sealed park) to 90° (vertical dispense).`
- Manuscript body (`main.pdf`, §2.1 Platform overview):
  - `... the auger can be parked horizontally (no gravity feed, clean shutoff) and tilted toward vertical for dispensing...`
- Asset (`assets/rotation_0_45_90.png`; branch-tree path `design/cad/mounting-plate-assembly/diagrams/rotation_0_45_90.png`) supports fixed dispense-point geometry, but it does not establish a literal seal.
- Why this matters:
  - `sealed` implies a stronger physical claim than `no gravity feed, clean shutoff`.
- Proposed correction:
  - Replace `sealed park` with manuscript-consistent wording:
    - `0° (horizontal park)`
  - or:
    - `0° (horizontal, no-gravity-feed park)`

7. Panel (b) and panel (d) tell two different sensing stories inside the same figure.
- Panel (b) asset: `shared collection cup (load cell — v1.2)` in `assets/single_channel_module_powder_flow.png`.
- Panel (d) code/text (`make_figures.py`, line 180):
  - `Balance reading (A&D HR-100A, RS-232)`
- Manuscript body: HR-100A analytical balance over RS-232.
- Why this matters:
  - Even if the caption tries to patch panel (b), the figure as a whole is internally split between an obsolete load-cell concept and the final HR-100A design.
- Proposed correction:
  - Use a panel-(b) asset consistent with panel (d), or explicitly mark panel (b) as a historical concept render:
    - `Early v2 concept render; cup/load-cell labeling shown here is obsolete and was superseded by the HR-100A balance configuration in the final platform.`

What is consistent
- Panel (d) is consistent with the manuscript and reviewer notes on sensing:
  - `Balance reading (A&D HR-100A, RS-232)` in `make_figures.py` matches the body text and `pr97_comments.md` resource note.
- Panel (c) is broadly consistent on the fixed dispense point:
  - caption, body text, and `assets/rotation_0_45_90.png` all support the claim that the dispense point does not translate during tilt.
- The manuscript’s AI-vs-human and no-GUI-CAD framing is not contradicted by this figure.
  - `pr97_comments.md` requires only HUMAN vs AI attribution and says no Fusion 360/SolidWorks were ever used; the manuscript body already states that. Figure 1 itself does not make a conflicting attribution claim.

Concrete corrected wording
- Panel (a) caption, minimal-change version:
  - `Platform overview. (a) Single-channel powder-doser module (CAD render; photograph of the printed platform will replace this render): printed Archimedes auger, NEMA-11-driven printed gear train, auger bracket/tap-collar region, and hinged mounting plate on the baseplate.`
- Panel (b) caption, honest-if-keeping-current-asset version:
  - `(b) Early v2 cross-section retained to illustrate the flow path. This historical render still shows a separate reservoir/hopper and a load-cell cup; in the final design, powder is loaded through slots in the auger tube, which itself serves as the reservoir, and the collection cup sits on an A&D HR-100A analytical balance.`
- Panel (c) caption wording:
  - `(c) Tilt sweep about the fixed dispense point: the hinge axis passes through the exit-nozzle tip so the dispense point does not translate as the channel tilts from 0° (horizontal park) to 90° (vertical dispense).`
- `make_figures.py` panel-(a) callout replacement:
  - replace `NEMA-11 stepper\n+ GT2/gear drive`
  - with `NEMA-11 stepper\n+ printed gear train`

Prioritized action list for Figure 1
- Replace panel (b) first. It is the main source of contradiction: it still shows a hopper/reservoir and a load cell. Candidate branch-tree assets to inspect next: `paper/figures/assets/auger_geared_cross_section.png` and `cad/auger-geared/archimedes-auger-geared-cross-section.png`.
- Remove `GT2` from panel (a) annotations in `make_figures.py` unless you can document an actual belt stage elsewhere in the manuscript.
- Rewrite panel (a) caption so it does not claim the render visibly shows the solenoid and vibration motor if those parts remain indistinct.
- Downgrade `sealed park` in panel (c) to `horizontal park` or equivalent manuscript-supported wording.
- If panel (b) cannot be replaced immediately, explicitly mark it as a historical v2 concept render with obsolete hopper/load-cell features so the figure stops contradicting itself.

- Discretionary analytical decisions made during the analysis
  - Treated visible text embedded in the supplied raster assets (`assets/*.png`) as primary evidence alongside the caption and extracted PDF text.
  - Used the branch-tree file list to name candidate replacement assets, but did not assume their contents beyond what their filenames support.
  - Counted a statement as inconsistent when the figure panel itself contradicted the caption/body, even if the caption attempted to verbally correct an older render.
  - Classified `sealed park` as an overstatement rather than a hard contradiction because the body supports `no gravity feed, clean shutoff` but not a literal seal.
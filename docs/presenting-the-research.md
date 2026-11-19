# Presenting the powder-doser research: goals, hypotheses, methods, results and figures

A snapshot as of **19 Nov 2026**, written for [issue #160](https://github.com/vertical-cloud-lab/powder-doser/issues/160)
in answer to: *"Provide a summary of the overall current goals for the powder doser in the context of presenting the
research. What are the hypothesis, methods and results? What figures do we have that can support this in a
presentation?"*

Most of the work this page points to sits on open pull requests, not on `main`. Every figure and file link is
therefore pinned to a commit, so it keeps working when those branches move. The numbers come from the drafts'
own text and tables, cited next to each one. Where a draft says a result is still missing, this page says so too.

## The research in one paragraph

Alloy discovery in this lab runs as a closed loop. An optimizer picks a composition, powders are weighed into a
cup, the ultrasonic atomizer turns the charge into new powder, and laser powder bed fusion (L-PBF) prints it.
Weighing and blending the powders by hand is the slowest step. The powder doser automates it with an open-source,
3D-printed auger: one printed tube is both the powder's reservoir and its dosing screw, and the doser turns, tilts
and taps that tube over a cup on an analytical balance until the balance reads the target. One channel costs
under $200 plus the balance. On 13 powders it delivered 10 to 231 mg per auger revolution, and in closed loop
every 1 g dose of 7 of the 13 powders landed within ±5%. Bayesian
optimization then tuned the controller unattended on salt and made 0.5 g doses three times faster than hand
tuning. The open questions are how to scale to 15+ powders with automated auger swapping, whether calibrating
each powder can double as a measurement of how it flows, and what AI agents were and weren't good at in
designing the doser.

## Three threads: three talks, two papers

| Thread | TMS 2027 talk (14–18 Mar 2027, Orlando) | Paper | Where it stands |
|---|---|---|---|
| **1. The doser and the multi-doser** | *A Programmable Powder Doser with 15+ Reservoirs and Automated Auger Swapping for AI-Enabled Alloy-Development Workflows*. Sam, oral. This is the abstract in issue #160 | Hardware paper for *Digital Discovery*. The v2 figures, tables, title and abstract are in [PR #209](https://github.com/vertical-cloud-lab/powder-doser/pull/209); the earlier full draft is [PR #97](https://github.com/vertical-cloud-lab/powder-doser/pull/97) | One channel built and tested on 13 powders. The multi-doser exists in CAD only |
| **2. Calibration, and dosing as a probe of powder flow** | *Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow Behavior: Multi-Task Bayesian Calibration and Physics-Based Property Inference*. Will | *Additive Manufacturing* draft, [PR #184](https://github.com/vertical-cloud-lab/powder-doser/pull/184) (37 pp.; some panels still synthetic) | BO done on one powder (salt). DEM forward model done. Multi-task BO and measured powder properties not started |
| **3. AI agents in the design loop** | *Agentic Systems Design of an Open-Source Powder Doser for L-PBF Feedstock Research: CAD, PCB, and Firmware*. Luke | Folded into the hardware paper: Figs. 2, 3 and S1 and Table 4 of [PR #209](https://github.com/vertical-cloud-lab/powder-doser/pull/209) | Done; the lessons are written up |

The three TMS abstracts, with their target symposia and mock reviews, are in
[`abstracts/tms-2027/`](https://github.com/vertical-cloud-lab/powder-doser/tree/b905a3b/abstracts/tms-2027)
([PR #78](https://github.com/vertical-cloud-lab/powder-doser/pull/78)). The project's three original objectives (an open-source multi-powder doser; a generative-CAD-first design process; a study of
where agentic AI succeeded and failed) are in the BYU NASA Space Grant proposal,
[`proposals/byu-nasa-space-grant-2026/`](https://github.com/vertical-cloud-lab/powder-doser/tree/12666ed/proposals/byu-nasa-space-grant-2026).

## Goals

### The long-term goal

Make the doser the feedstock-preparation node of the lab's closed-loop alloy-development pipeline: the optimizer
picks a recipe, the doser weighs each powder straight into the cup the atomizer uses next (so the powder is never
transferred), and the atomized powder goes on to L-PBF.

![The closed-loop alloy-discovery workflow from the NASA Space Grant proposal](https://github.com/vertical-cloud-lab/powder-doser/blob/12666ed/nasa-space-grant-am-alloy-workflow.png?raw=true)

### Design targets, and where each one stands

| Design target (TMS abstract; NASA proposal) | Where it stands, Nov 2026 |
|---|---|
| **15+ independently addressable reservoirs** (the proposal says up to 30) | One powder per doser. Each powder has its own capped auger, swapped by hand (Fig. 5 of PR #209). 25 repeat single dosers are being printed and assembled ([#181](https://github.com/vertical-cloud-lab/powder-doser/pull/181), [#191](https://github.com/vertical-cloud-lab/powder-doser/issues/191), [#193](https://github.com/vertical-cloud-lab/powder-doser/issues/193), [#197](https://github.com/vertical-cloud-lab/powder-doser/issues/197)). A 13-module chain carousel ([PR #185](https://github.com/vertical-cloud-lab/powder-doser/pull/185); v7 is the main version) and a fixed-base 2–3 auger "tri-star" ([#204](https://github.com/vertical-cloud-lab/powder-doser/issues/204)) exist in CAD only |
| **Automated auger swap**, so recipes can't cross-contaminate | Designed, not built: the carousel's docking station (#185), and Ethan's solenoid bracket, which lets an auger come out without removing the tapper ([#203](https://github.com/vertical-cloud-lab/powder-doser/issues/203)). Cross-contamination is prevented by design and is not being measured |
| **±1 mg per powder** | Best so far: a median error of 1.8 mg (0.8–2.6 mg) on 0.5 g of salt with optimized settings ([#166](https://github.com/vertical-cloud-lab/powder-doser/pull/166)). The 13-powder campaign used ±5% as its acceptance limit (±10% below 100 mg) |
| **250 mL blends** | One auger holds 58 mL. The largest doses so far are 8 g atomizer charges (AlSi10Mg on 29 Sep, Al 4047 on 30 Sep) |
| **Sub-$1,000 bill of materials** | One channel: under $200 plus an analytical balance. The carousel test rig: $1,035 for v2, $2,406 for v9 ([PR #185](https://github.com/vertical-cloud-lab/powder-doser/pull/185)) |
| **Alloy precursors, elemental or master alloy, under inert atmosphere** | Dosed in air so far: AlSi10Mg, two Si grades and Al 4047. One qualitative glove-box trial at the University of Utah in July (salt, norbornene, AIBN; [#117](https://github.com/vertical-cloud-lab/powder-doser/issues/117)); static and loosening fasteners were the problems |
| **ML calibration layer trained on balance feedback** | Multi-objective Bayesian optimization tuned 8 controller settings on salt. Validated settings are stored per powder and reused for production doses (`scripts/dose.py`, [#166](https://github.com/vertical-cloud-lab/powder-doser/pull/166)) |

### What people are working on now

- **Hardware paper:** the figures and tables were drafted first, as agreed at the 27 Oct meeting; Sam's 17 Nov
  review notes have been addressed ([PR #209](https://github.com/vertical-cloud-lab/powder-doser/pull/209)). The
  manuscript gets rebuilt around them next.
- **Optimization paper:** more single-powder campaigns (AlSi10Mg, 316L, sieved Al 4047 and one elemental
  precursor), measured properties of the same powder lots (Hall/Carney flow, tapped density, particle size,
  shear cell), then the multi-task benchmark and the DEM inference
  ([`OUTLINE.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/OUTLINE.md) §4).
- **Repeat dosers:** 25 units; the first full unit is being assembled and reviewed
  ([#191](https://github.com/vertical-cloud-lab/powder-doser/issues/191)). The open question is whether they are
  standalone dosers or carousel modules ([#181](https://github.com/vertical-cloud-lab/powder-doser/pull/181)).
- **Multi-doser:** the carousel ([PR #185](https://github.com/vertical-cloud-lab/powder-doser/pull/185), with FEA
  in [PR #188](https://github.com/vertical-cloud-lab/powder-doser/pull/188)), the fixed-base tri-star
  ([#204](https://github.com/vertical-cloud-lab/powder-doser/issues/204)), the new tap bracket
  ([#203](https://github.com/vertical-cloud-lab/powder-doser/issues/203)) and the linear actuator both need
  ([#202](https://github.com/vertical-cloud-lab/powder-doser/issues/202)).
- **Downstream use:** atomizer charges for a composition spread
  ([#186](https://github.com/vertical-cloud-lab/powder-doser/issues/186); the 22.5 wt% point needs thin-walled
  crucibles), and chemistry users: polymerization in beakers and flasks (#204) and milligram synthetic chemistry
  in a glove box ([#117](https://github.com/vertical-cloud-lab/powder-doser/issues/117)).
- **Powder tests on the doser itself:** concept designs for ten in-house tests
  ([PR #205](https://github.com/vertical-cloud-lab/powder-doser/pull/205)), and a data-assimilation project on
  the logged dose traces ([#210](https://github.com/vertical-cloud-lab/powder-doser/issues/210)).

## Hypotheses

None of the drafts states a formal hypothesis. These are the claims the abstracts and drafts set out to test,
written as hypotheses, with the evidence so far.

| # | Hypothesis | How it is tested | Evidence so far |
|---|---|---|---|
| **H1** Hardware | A 3D-printed auger that is both reservoir and screw, turned, tilted and tapped under closed-loop balance feedback, can dose powders with very different flow (gas-atomized metal to cohesive food powders) to within a few percent at gram scale, at a small fraction of the cost of a commercial dosing head | Test protocols A–H on 13 powders, in two rounds (4 Aug–15 Sep 2026) | **Supported at 1 g** for 7 of 13 powders: every dose within ±5%, and the nine on AlSi10Mg, coarse Si and sodium sulfate within 1%. **Not yet at 50–200 mg** (14 of 30 and 18 of 30 within the limit). 3 powders didn't flow at all |
| **H2** Scaling | Giving each powder its own auger, and swapping augers by machine, scales the doser to 15+ powders with no cross-contamination by design | The carousel test rig (#185) or the fixed-base tri-star (#204) | **Not tested.** CAD, interference checks and FEA predictions only |
| **H3** Calibration | Multi-objective Bayesian optimization finds controller settings that are both faster and more accurate than hand tuning, in a few dozen unattended doses | 42-dose SOBOL → SAASBO/qNEHVI campaign on salt, then an 8-dose validation block | **Supported on one powder:** median 78 s and 1.8 mg error, against 245 s and 4.6 mg for hand-tuned settings |
| **H4** Transfer | Treating each powder as a related task of one multi-task model cuts the doses needed to calibrate a new powder | Leave-one-powder-out replays, then one prospective campaign (planned) | **Not started.** One anecdote: salt's settings dosed 8 g of AlSi10Mg to 7.993 g unchanged. Fig. 4 of the draft is synthetic |
| **H5** Dosing as a probe | A powder's dosing response (mass per revolution against tilt and speed, afterflow, mass per tap) measures how it flows: a DEM twin can turn it into an effective cohesion and friction that agree with shear-cell and Hall-flow tests | DEM (LIGGGHTS) twin of the auger, plus standard tests on the same lots | **Early evidence.** Delivery ranks like the literature angle of repose (Spearman ρ = −0.84, 12 powders). The DEM twin, with no parameter fitted to dosing data, gives 105 mg/rev against a measured 105 ± 11 at the campaign's centre point. None of our own lots has been measured yet |
| **H6** AI in design | AI agents are most useful as modelling assistants (engineers design, AI models, engineers review), not as autonomous designers | The same prompt given to Copilot, CADSmith and Zoo; part-by-part modelling with review, April–July 2026 | **Supported, qualitatively.** No tool produced a working assembly from one whole-doser prompt. The tested doser runs on parts the engineers redrew in Fusion 360 |

## Methods

**The doser (one channel).** From the optimization draft's §2.1
([`main.tex`](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/main.tex)) and
Fig. 1 of [PR #209](https://github.com/vertical-cloud-lab/powder-doser/pull/209):
- A one-piece PLA auger printed on the Bambu H2D: a 21 mm bore, 250 mm tube holding up to 58 mL, with a single
  flight (10.4 mm pitch) over the last 84 mm and a 3 mm exit hole. A screw-on cap closes the fill end, so a
  filled auger can be stored loaded.
- A NEMA-11 stepper turns the auger through a 20:44 gear pair, at up to about 109 rpm.
- Two servos tilt the auger about a hinge near the outlet through 2:1 gears.
- A 12 V push-pull solenoid taps the tube with 60 ms pulses.
- An A&D HR-100A analytical balance (0.1 mg readability, 102 g capacity) reads the cup over RS-232.
- A Raspberry Pi Pico W runs the dosing firmware (MicroPython). A Raspberry Pi Zero 2 W next to the rig runs each
  dose and uploads its record to MongoDB.

**The dose controller (three stages).**
1. *Bulk:* tilted, fast rotation, optionally with taps at 2 Hz.
2. *Trickle:* slow rotation under a PI controller on the flow rate, which a Kalman filter estimates from the
   balance. It stops when the predicted final mass, including the powder still falling, comes within a margin
   of the target.
3. *Tap:* the auger stops and single taps free a few milligrams at a time until the reading is within the
   stopping band.

A dose more than 100 mg over the target is aborted. Every dose writes one machine-readable record: the settings
as executed, the time in each stage, every stop event and the balance trace.

**Powders.** 13 in all. Seven food-safe surrogates: NaCl, xanthan gum, white and brown rice flour, calcium
lactate, CMC and sodium alginate. Six research powders: gas-atomized AlSi10Mg, two silicon grades (−110/+200 and
−325 mesh), sodium sulfate, barium chloride and fumed silica. Later production doses used Al 4047.

**Test protocols A–H** (Table 2 of [PR #209](https://github.com/vertical-cloud-lab/powder-doser/pull/209)):
balance baseline; static hold; mass per revolution at 0, 22.5 and 45° tilt; speed sweep with the balance
streamed; single taps; vibration (no data: driver fault); closed loop at 1 g; closed loop at 50 and 200 mg.

**Calibration by Bayesian optimization**
([PR #166](https://github.com/vertical-cloud-lab/powder-doser/pull/166)):
- Ax 0.4.3, starting with a 2^(8−4) fractional-factorial screen (16 corners and 4 centre points).
- Then a SAASBO Gaussian process, which assumes only a few settings matter, with the qNEHVI acquisition function.
- Two objectives for a 0.5 g dose: time and |error|, with limits of 180 s and 20 mg.
- Eight settings, among them the bulk tilt and speed, when to switch to the trickle, the trickle and tap tilts,
  and the stopping band.
- Recommended settings get an 8-dose validation block. The afterflow time constant τ is fitted per powder.

**Simulation.** A LIGGGHTS DEM twin of the printed auger
([PR #180](https://github.com/vertical-cloud-lab/powder-doser/pull/180)), and a survey with small runs of every
other physics-based method found ([PR #196](https://github.com/vertical-cloud-lab/powder-doser/pull/196)).

**Remote, agent-run operation.** The rig is on the lab's tailnet, the bench is on a YouTube livestream, and Claude
(in GitHub Actions) runs doses and campaigns in response to issue comments. Fig. 4a of PR #209 shows a person
asking for 8 g of AlSi10Mg and the agent dosing it.

**AI-assisted CAD** (Table 4 of [PR #209](https://github.com/vertical-cloud-lab/powder-doser/pull/209)):
- The GitHub Copilot coding agent (CadQuery and OpenSCAD), CADSmith, the Zoo Text-to-CAD API and Zoo Design
  Studio, April–July 2026.
- The engineers then redrew the tested parts in Fusion 360, and since October in Onshape.

## Results

**Open loop: one doser, 13 powders, one fixed set of settings** (Fig. 6 and Tables 1 and S1 of PR #209):
- 10 powders moved, from 10 mg (sodium alginate) to 231 mg (AlSi10Mg) per auger revolution at 22.5° tilt: a
  24-fold range.
- Fumed silica, −325 mesh silicon and brown rice flour moved nothing measurable.
- Tilt matters a lot. AlSi10Mg delivered 49, 231 and 339 mg per revolution at 0, 22.5 and 45°.
- Under continuous rotation the powder arrives in surges, one per revolution.
- One tap releases up to 20 mg. Revolution-to-revolution variation is 2–18% for most powders, and 37% for white
  rice flour.

**Closed loop** (Fig. 7, Table 3):

| Target | Within the limit | Median time of those doses | Misses that were overshoots |
|---|---|---|---|
| 50 mg (±10%) | 14 of 30 | 52 s | 10 of 16 |
| 200 mg (±5%) | 18 of 30 | 152 s | 3 of 12 |
| 1 g (±5%) | 24 of 39 | 185 s | 0 of 15 |

Fast powders overshoot small targets and slow ones fall short. The draft attributes the misses mainly to the
controller rather than the hardware.

**Bayesian calibration on salt**
([PR #166](https://github.com/vertical-cloud-lab/powder-doser/pull/166),
[slides in PR #175](https://github.com/vertical-cloud-lab/powder-doser/pull/175)):
- 42 doses, unattended. After the hand-tuned doses, the optimizer tried 31 other settings in under 2½ hours.
- The recommended settings, `bo-005`, were validated 8 of 8, with a median of 78 s and a median error of 1.8 mg.
  Hand-tuned settings took a median of 245 s with a 4.6 mg error, so the optimized dose is three times faster.
- Most of the gain is in the endgame: each tap moved twice as much powder, so the tap stage took a third of the
  time.
- Every setting it changed ended at the edge of its range, so the next search should widen the ranges.
- A follow-on campaign with a ninth setting (the trickle's stopping margin) ran on 13 and 15 Oct. The rig's state
  confounds its comparison with September, and it was paused when the salt feed collapsed.

**Production doses for the atomizer.**
- Salt's settings, unchanged, dosed 8 g of AlSi10Mg to 7.993 g.
- Al 4047 charges for byu-vcl's composition spread
  ([#186](https://github.com/vertical-cloud-lab/powder-doser/issues/186)) finished at 3.0432 g against a
  3.0407 g target (7.5 wt%) and at 6.5676 g against 6.5674 g (15 wt%).
- Unsieved Al 4047 clogged the outlet more than once, and people had to step in. That is the
  human-in-the-loop story of the 30 Sep video ([PR #174](https://github.com/vertical-cloud-lab/powder-doser/pull/174)).

**Dosing as a probe of powder flow** ([PR #184](https://github.com/vertical-cloud-lab/powder-doser/pull/184),
[PR #180](https://github.com/vertical-cloud-lab/powder-doser/pull/180)):
- Across 12 powders, delivery ranks like the *literature* angle of repose (Spearman ρ = −0.84).
- The DEM twin, with no parameter fitted, matches salt at the campaign's centre point: 105 mg/rev against
  105 ± 11 measured.
- It follows the tilt trend but under-predicts at 22.5° (71 against about 108) and at 45° (153 against about 195).
- In the DEM, moving the core tip 1 mm back from the exit doubles the delivery. Small print differences
  therefore matter.

**AI in the design loop** (Figs. 2, 3 and S1, and the failure-mode table in
[PR #209](https://github.com/vertical-cloud-lab/powder-doser/pull/209)):
- Asked for the whole doser at once, every tool returned parts that did not form a working assembly. One part at
  a time, with interfaces listed and engineers reviewing every render, worked better.
- The recurring failures were parts that didn't fit, unrequested changes, swapped variants, sub-millimetre
  errors, designing around out-of-date inputs, no sense of "finished", and wrong orientations.
- Since July the agents have mostly run the tests, written firmware and analysis, and assembled the team's CAD
  through the Onshape API.

**Multi-doser** (designs only; every number is a CAD or FEA prediction):
- **Chain carousel**, v1 to v9 ([PR #185](https://github.com/vertical-cloud-lab/powder-doser/pull/185)): 13
  modules on twin vertical #35 chains. A docking station with a single Actuonix P16 lifts and tilts the module
  at the station. v7 is the main version; v9 brings the outlet to 32 mm above the beaker.
- **FEA** of every carousel part ([PR #188](https://github.com/vertical-cloud-lab/powder-doser/pull/188)):
  keep the NEMA 34's holding current low inside an enclosure, keep microstepping, and wait 3–7 s after a stop
  before reading the balance.
- **Fixed-base tri-star** ([#204](https://github.com/vertical-cloud-lab/powder-doser/issues/204)): three gearless
  modules at 120° over one beaker, each tilted by a P16 linear actuator, with Ethan's tap bracket. The one-piece
  base is 320.5 × 280.2 mm, which fits one H2D nozzle's build area.

### What not to claim yet

- ±1 mg accuracy, 15+ reservoirs, automated auger swapping, or 250 mL blends. These are design targets.
- Dosing under inert atmosphere, beyond one qualitative glove-box trial.
- Measured cross-contamination. The claim is "prevented by design".
- Multi-task calibration, or inferred cohesion and friction that agree with shear-cell or Hall-flow
  measurements. The figures for these are synthetic.
- That the doser "predicts spreadability". That link is proposed only.

## Figures for a talk

### A suggested 15-minute talk

| # | Slide message | Figure |
|---|---|---|
| 1 | Weighing powders is the slowest manual step in AI-driven alloy development | NASA workflow figure; optimization graphical abstract |
| 2 | Commercial dispensers are costly and poorly matched to many-powder alloy work; ours is open-source and costs under $200 a channel | Fig. 1 (the doser) |
| 3 | One printed tube is both the powder's reservoir and its dosing screw | Fig. 1c section; Fig. 5 (filling and swapping augers) |
| 4 | A dose runs in three stages: bulk, trickle, tap | Fig. 4, or the procedure animation (PR #175, slide 1) |
| 5 | One doser, 13 powders: a 24-fold range of flow, and 3 that didn't flow | Versatility GIF (PR #173) or Fig. 6 |
| 6 | In closed loop, 1 g doses land within ±5%; small doses are the open problem | Fig. 7 or Table 3 |
| 7 | Bayesian optimization made doses three times faster than hand tuning, unattended | PR #175 slides 2–6, or Fig. 3 of the optimization draft |
| 8 | An AI agent ran it from a GitHub comment, live on the livestream | Al 4047 slide video (PR #174); Fig. 4a |
| 9 | Every calibration is also a measurement of the powder | Overview figure (PR #195); DEM against measurement (PR #180) |
| 10 | Scaling up: one auger per powder, swapped by machine | Carousel v7/v9 (PR #185); tri-star (#204) |
| 11 | Engineers design, AI models: what the agents did and didn't do well | Fig. 2 (timeline), Fig. S1 (CAD comparison) |
| 12 | Next steps | The status table in [`OUTLINE.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/OUTLINE.md) §2 |

The slides in PR #175 are built to a specific style: a one-sentence message at the top left, nothing under 24 pt,
no legends, and builds that add one thing per step. Each step is also saved as a separate 1920 × 1080 PNG for
click-to-advance slides.

### The key figures

| | |
|---|---|
| **Fig. 1 The doser** (PR #209) ![Fig. 1](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig1_doser.png?raw=true) | **Fig. 4 How a dose runs** (PR #209) ![Fig. 4](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig4_dosing.png?raw=true) |
| **Fig. 5 One auger per powder** (PR #209) ![Fig. 5](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig5_use.png?raw=true) | **Versatility: one doser, 13 powders** (PR #173) ![Versatility build](https://github.com/vertical-cloud-lab/powder-doser/blob/d75b7b7/paper/figures/versatility/versatility_build.gif?raw=true) |
| **Fig. 6 Open-loop delivery** (PR #209) ![Fig. 6](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig6_open_loop.png?raw=true) | **Fig. 7 Closed-loop doses** (PR #209) ![Fig. 7](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig7_closed_loop.png?raw=true) |
| **Salt campaign: Pareto front** (PR #175, `model` version) ![Pareto](https://github.com/vertical-cloud-lab/powder-doser/blob/ff074df/docs/optimization/slides/pareto/model/build.gif?raw=true) | **Salt campaign: optimized vs hand-tuned dose** (PR #175) ![Traces](https://github.com/vertical-cloud-lab/powder-doser/blob/ff074df/docs/optimization/slides/traces/pair/build.gif?raw=true) |
| **Optimization draft Fig. 3: the salt campaign** (PR #184) ![Opt Fig. 3](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/figures/fig3_salt_campaign.png?raw=true) | **The dose procedure, animated** (PR #175) ![Procedure](https://github.com/vertical-cloud-lab/powder-doser/blob/ff074df/docs/optimization/slides/procedure/procedure_annotated.gif?raw=true) |
| **Every calibration is a measurement of the powder** (PR #184 graphical abstract) ![Graphical abstract](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/figures/graphical_abstract.png?raw=true) | **Cheap doser measurements linked to standard powder tests** (PR #195) ![Overview relations](https://github.com/vertical-cloud-lab/powder-doser/blob/c975ff0/paper/optimization/figures/fig_overview_relations.png?raw=true) |
| **DEM twin against measurement** (PR #180) ![DEM vs measured](https://github.com/vertical-cloud-lab/powder-doser/blob/f84aa9e/sim/dem/results/rig_vs_measured.png?raw=true) | **Al 4047 loaded, then dosed by Claude from a comment** (PR #174, storyboard of the 47 s video) ![Storyboard](https://github.com/vertical-cloud-lab/powder-doser/blob/ed26df4/docs/videos/2026-09-30-al4047-claude-dose/storyboard.jpg?raw=true) |
| **Fig. 2 AI agents and engineers, Apr–Nov 2026** (PR #209) ![Fig. 2](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig2_timeline.png?raw=true) | **Fig. S1 Generative-CAD comparison** (PR #209) ![Fig. S1](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/figS1_cad_comparison.png?raw=true) |
| **Multi-doser carousel v7, the main version** (PR #185) ![Carousel v7](https://github.com/vertical-cloud-lab/powder-doser/blob/5e1a775/cad/chain-carousel-v7/renders/v7/overview_v7.gif?raw=true) | **Fixed-base tri-star with the new tap bracket** (#204) ![Tri-star](https://github.com/vertical-cloud-lab/powder-doser/blob/4d2177e/design/multi-auger-fixed-base/renders/b2_tap_bracket.png?raw=true) |

### Everything else

| Figure | What it shows | Status |
|---|---|---|
| [Fig. 3 The original AI parts and what replaced them](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig3_redesign.png) | Tap collar, auger and bracket: AI versions against the team's | Real |
| [Fig. 6B](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig6B_open_loop_banded.png), [7B](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig7B_closed_loop_mg.png), [7C](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/fig7C_closed_loop_mg_overlay.png) | Alternative versions: banded rows; dose error in mg | Real; which version to use is still open |
| [Fig. S2](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/figS2_rev_variation.png), [S3](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/figS3_dose_time.png), [S4](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/preview/figS4_assembly_exploded.png) | Revolution-to-revolution variation; time per dose; every part with the BoM | Real |
| All captions and tables of the hardware paper | [`FIGURES-AND-TABLES.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/FIGURES-AND-TABLES.md), [`CAPTIONS.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/CAPTIONS.md), [`TITLE-ABSTRACT.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/660bc15/paper/v2/TITLE-ABSTRACT.md) | Under review |
| [Optimization Fig. 1](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/figures/fig1_overview.png), [Fig. 2](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/figures/fig2_powders.png) | One `bo-005` dose trace with its stages, and a data-flow schematic; the 13 powders | Real |
| [Optimization Fig. 4](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/figures/fig4_multitask_placeholder.png), [Fig. 5](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/figures/fig5_dem.png), [Fig. 6](https://github.com/vertical-cloud-lab/powder-doser/blob/ec30713/paper/optimization/figures/fig6_properties.png) | Multi-task results; DEM; dosing against properties | **Partly synthetic:** Fig. 4 entirely, Fig. 5b–c and Fig. 6c are marked "SYNTHETIC DATA" |
| [TMS 2027 "hypothetical results" slides](https://github.com/vertical-cloud-lab/powder-doser/tree/d14a50d/docs/optimization/tms-2027) | The shape of the multi-task and property-inference results | **Dummy data**, watermarked. Shows the plan, not a result |
| [Salt-campaign slides: math explainers, knobs](https://github.com/vertical-cloud-lab/powder-doser/tree/ff074df/docs/optimization/slides) | Pareto front and hypervolume; the GP model and next dose; what the optimizer changed | The math slides use made-up numbers and say so; the rest are real |
| [Versatility figure, static, with step PNGs](https://github.com/vertical-cloud-lab/powder-doser/tree/d75b7b7/paper/figures/versatility) | Same as the GIF, for click-to-advance slides | Real |
| [Current-design CAD renders](https://github.com/vertical-cloud-lab/powder-doser/tree/7f5b3b7/cad/full-assembly/renders) | The full assembly, annotated, at three tilts, and exploded with the BoM ([PR #170](https://github.com/vertical-cloud-lab/powder-doser/pull/170)) | Real CAD |
| [Rig photo, 11 Sep 2026](https://github.com/vertical-cloud-lab/powder-doser/blob/7f5b3b7/cad/full-assembly/reference/rig-2026-09-11-front.jpg) | The doser as tested | Photo |
| [Carousel v9](https://github.com/vertical-cloud-lab/powder-doser/blob/5e1a775/cad/chain-carousel-v9/renders/v9/overview_v9.gif), [v2](https://github.com/vertical-cloud-lab/powder-doser/blob/5e1a775/cad/chain-carousel-v2/renders/chain_carousel_v2.gif) and the [public Onshape documents](https://github.com/vertical-cloud-lab/powder-doser/blob/5e1a775/cad/chain-carousel-v7/README.md) | The variations and the first vertical version | CAD only |
| [Carousel FEA](https://github.com/vertical-cloud-lab/powder-doser/blob/575df1d/cad/fea/RESULTS.md) | Deflection, stress, vibration and heat of every carousel part (PR #188) | Predictions |
| [Tri-star renders](https://github.com/vertical-cloud-lab/powder-doser/tree/4d2177e/design/multi-auger-fixed-base/renders) | Concepts A1/A2/B1/B2, parts reused, new and removed, clearance, base drawing, clevis block (#204) | CAD only |
| [DEM clips and sweeps](https://github.com/vertical-cloud-lab/powder-doser/tree/f84aa9e/sim/dem/results) | Cut-away GIFs of the auger, exit-gap sensitivity, micro-auger sweep (PR #180) | Simulation |
| [Powder-test animations](https://github.com/vertical-cloud-lab/powder-doser/tree/1e0d6f8/docs/powder-tests/animations) | Hall/Carney flow, densities, angle of repose, sieving, laser diffraction, loss on drying, FT4 and ring shear, with costs (PR #190) | Schematic; the numbers on screen are illustrative |
| [In-house test concepts](https://github.com/vertical-cloud-lab/powder-doser/blob/626da9b/design/in-house-tests/concepts.png) | Ten powder tests built on the doser (PR #205) | Concepts |
| [Physics-simulation survey](https://github.com/vertical-cloud-lab/powder-doser/tree/c93c3e0/docs/physics-simulations) | Small runs of every method found (PR #196) | Simulation |
| [POSE 2026 rotating-tube proof of concept](https://github.com/vertical-cloud-lab/powder-doser/blob/12666ed/POSE_tube_xanthan_gum.png) | The first tube, printed in about 24 hours (May 2026) | History |

### Videos

- [Al 4047 loaded, then dosed by Claude from a GitHub comment with the livestream](https://github.com/vertical-cloud-lab/powder-doser/blob/ed26df4/docs/videos/2026-09-30-al4047-claude-dose/al4047_claude_dose_slide.mp4)
  (47 s, 16:9, made for a full-screen slide; [PR #174](https://github.com/vertical-cloud-lab/powder-doser/pull/174))
- [The dose procedure, animated on the CAD with the real balance trace](https://github.com/vertical-cloud-lab/powder-doser/blob/ff074df/docs/optimization/slides/procedure/procedure_annotated.mp4)
  (21 s; [PR #175](https://github.com/vertical-cloud-lab/powder-doser/pull/175))
- [A remote closed-loop salt dose, live](https://www.youtube.com/live/XJ5TRApc6pI?t=12835)
  ([#145](https://github.com/vertical-cloud-lab/powder-doser/issues/145))
- Multi-doser: [prototype pitch (14 min)](https://www.youtube.com/watch?v=IkjBxqa06u0),
  [how the carriage pieces fit together](https://youtu.be/BSgpeKZgoXU),
  [the 3D-printed prototype](https://www.youtube.com/watch?v=liB6YNSN8-Q)
- [Manual calibration playlist](https://www.youtube.com/playlist?list=PLZTWCFxzhTQv42fTuW2Tjs9o1KuWA_b-I)
  (tilt, rotate and tap tests per powder, Jul–Aug 2026)
- [Sam's Zoo Design Studio session](https://www.youtube.com/watch?v=6YsOMIsOfkY) (AI CAD in practice)
- The bench livestream channel: [byu-vcl-hardware-streams](https://youtube.com/@byu-vcl-hardware-streams)
- [POSE 2026 slides](https://docs.google.com/presentation/d/1SZyMInTeK6V5QMu_9ptvdzXFou06gq9Mr7xBxdh9StA/edit?usp=sharing)

### Before you use a figure

- **Synthetic and dummy panels** are marked as such on the image. Keep them out of a results slide, or label them
  as the plan.
- **Open choices:** Fig. 6 or 6B, and Fig. 7, 7B or 7C, are still open. Brand names (the balance) are legible in
  Figs. 1a and 5c, and whether to crop them is undecided
  ([open questions in PR #209](https://github.com/vertical-cloud-lab/powder-doser/pull/209)).
- **Fig. 4's tube positions are CAD renders.** Real footage of the three stages exists only on the 4 Sep
  livestream.
- **None of these branches is merged.** If a figure changes, take the newer commit from its PR rather than this
  page.

## Who leads what

| Area | People |
|---|---|
| Direction, agents and lab infrastructure | Sterling (sgbaird) |
| Mechanical design, multi-doser, hardware paper | Sam (swcharles) |
| Firmware, optimization, optimization paper | Will (williamulbz) |
| PCB, generative-design talk | Luke (lbwinters) |
| Current Onshape CAD, tap bracket, tri-star | Ethan (ethanw-24) |
| Prints and assembly of the repeat dosers | Brandon (brandonmunk), lshuldberg |

For the project's full history, and who did what since April, see the orientation document in
[PR #198](https://github.com/vertical-cloud-lab/powder-doser/pull/198).

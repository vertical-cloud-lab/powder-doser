# Alternative powder-dosing styles for the Genmitsu 3018-Pro V2

Issue [#12](https://github.com/vertical-cloud-lab/powder-excavator/issues/12)
asks us to think beyond the two designs already on the table — the
pivoting scoop / ladle in PR
[#2](https://github.com/vertical-cloud-lab/powder-excavator/pull/2) and the
bimodal compliant trough in PR
[#5](https://github.com/vertical-cloud-lab/powder-excavator/pull/5) — and
to propose alternative dosing styles that:

- bolt onto the **Genmitsu 3018-Pro V2** spindle/gantry mount,
- are realistically buildable in **one workshop day** (3D printing fine,
  electronics/motors are allowed but each added active component is a
  schedule risk),
- and address the gaps surfaced by the commercial-landscape sweep in
  PR [#11](https://github.com/vertical-cloud-lab/powder-excavator/pull/11)
  — chiefly the **sub-10 mg cohesive-powder dispensing gap**, the absence
  of an *open* powder head, and the dominance of gravimetric Quantos /
  positive-displacement SWILE as the only well-evidenced sub-mg paths.

The approach we take throughout: **let the gantry itself be the actuator**
wherever possible (the 3018 already has fast, repeatable XYZ motion under
GRBL control, so any dosing primitive that can be triggered by a
contact / press / tap / scrape against a fixed feature on the bed is
essentially "free" from a build-risk perspective).

## Design constraints recap

| Constraint | Source | Implication for alternatives |
| --- | --- | --- |
| Must mount on Genmitsu 3018-Pro V2 spindle clamp | issue #12 | Tool envelope ≤ ~Ø45 mm clamp, ≤ ~3 kg, ≤ ~300 × 180 × 45 mm work area |
| One workshop day left | issue #12 | Prefer purely-mechanical or single-discrete-component electronic designs |
| 3D printing OK; electronics/motors OK but risky | issue #12 | Rank passive > single-component-active > full electromechanical |
| Sub-10 mg, cohesive powder is unsolved at the open-source level | PR #11 §5 / §6 | Aim for designs that *attack* this regime, not that copy the > 50 mg gravimetric heads |
| Gravity / hopper feeds clog on cohesive powders | PR #11 §1, §4 | Prefer designs where powder is **mechanically liberated each cycle** (tap, scrape, displace) rather than relying on gravity flow |
| Avoid duplicating the scoop (#2) and bistable trough (#5) | issue #12 | Concepts below explicitly do not pivot a bucket and do not rely on a snap-through flexure |

## Candidate alternatives

The list below is ordered by **risk-adjusted feasibility for a one-day
build**: passive / fully gantry-driven first, then designs that need a
single small active component, then ones that meaningfully add
electromechanical complexity.

### A. Tap-driven sieve cup (passive, gantry-as-actuator) ⭐

A printed cup (~10–20 mL) with a calibrated **mesh** or laser-precise
slot pattern in its base is mounted to the spindle clamp. The cup is
pre-loaded with powder. Cohesive powders **do not flow through the mesh
under gravity**, but each tap shakes some loose. The 3018 dispenses by
descending until the cup strikes a fixed printed anvil on the bed at a
controlled feedrate; one G-code "peck" = one tap = a near-constant micro-
dose. Total dose is metered by **tap count** (open-loop) or by an
external balance underneath (closed-loop), as recommended in
[issue #3](https://github.com/vertical-cloud-lab/powder-excavator/issues/3).

- *Mechanism in the PR #11 taxonomy*: vibratory / sieve micro-feeder,
  but **driven by gantry-impulse instead of a piezo or ERM motor** —
  removes the only active component a SWILE-class sieve dispenser would
  normally need.
- *Why it's interesting*: directly attacks the cohesive-powder regime
  (taps overcome surface forces; gravity alone cannot), keeps the
  electronics count at zero, and the only printed parts are a
  bottom-mesh cup and an anvil.
- *Risks*: tap-energy repeatability depends on Z-axis acceleration
  consistency; mesh size has to be matched to particle size (one printed
  cup per powder); needs an external balance for sub-mg accuracy.
- *Build day*: print cup + anvil (~3 h), hand-cut steel mesh insert
  (~30 min), G-code peck routine (~1 h), characterise on a 0.1 mg balance
  (~3 h).

### B. Pez-style positive-displacement chamber strip ⭐

A printed cartridge holds a row of small (e.g. 5–50 µL) **fixed-volume
chambers** in series. Each chamber is pre-loaded once, off-line, by
slot-filling and striking off the top with a flat blade (so each chamber
holds a metrologically-flat constant volume — the "loss-on-strike" idea
already used by powder-fill machines at industrial scale). To dose, the
gantry advances the cartridge one chamber-pitch using a fixed pawl on
the bed (rack-and-ratchet), bringing the next loaded chamber over the
target. A spring-loaded ejector or a fixed pin pushes the chamber's
contents downward into the vial.

- *Mechanism in the PR #11 taxonomy*: positive-displacement / volumetric
  micro-dispenser, conceptually closest to **Chemspeed SWILE** — the
  best-evidenced sub-mg head in the literature — but built from PLA and
  TPU rather than glass capillaries and pneumatics.
- *Why it's interesting*: per-dispense mass is set by chamber geometry
  (printable to ~0.05 mm with FDM, finer with resin), so once the
  packing density of a powder is calibrated, mass is repeatable without
  any feedback. Cross-contamination is bounded (each chamber is
  used once and discarded with the strip).
- *Risks*: cohesive powders may bridge over chamber openings during
  fill; open-strike accuracy is fundamentally limited by powder
  packing variance (PR #11 §4 cites < 1 % under "ideal conditions",
  much worse for cohesive solids); strip needs to be re-loaded between
  runs.
- *Build day*: design + print strip + cartridge holder + ratchet pawl
  (~4 h), print fill jig + striker bar (~1 h), characterise (~3 h).

### C. Capillary dip + fixed wiper (a printable mini-SWILE) ⭐

A short, fine-bore printed (or commercial PEEK / PTFE) **straw** is held
by the spindle clamp. The gantry dips it into a powder reservoir; the
straw fills by a combination of jamming and capillary forces. The gantry
then traverses to the dispense site and drives the straw past a fixed
**wiper / scraper** on the bed (a printed knife-edge), shearing off the
powder column into the receiving vial.

- *Mechanism in the PR #11 taxonomy*: directly the **Chemspeed SWILE**
  principle — piston-and-glass-capillary positive displacement, the
  only sub-mg head that has been benchmarked from 0.1 mg upward in
  the published evidence (PR #11 §1, §2). Replicating it in
  printable / off-the-shelf parts is exactly the "open SWILE
  alternative" gap called out in PR #11 §5.
- *Why it's interesting*: smallest doses of any concept here; entirely
  passive on the dispense side (the wiper is bolted to the bed, the
  straw is bolted to the spindle, the gantry does the rest).
- *Risks*: "fill" repeatability of an unmodulated dip is the SWILE's
  Achilles heel even in the commercial product; very fine bores will
  clog with cohesive powders; printed bores may not be smooth enough
  without a PTFE-spray finish.
- *Build day*: print straw holder + wiper + reservoir (~2 h), source
  straws / PEEK tubing from the makerspace (~1 h), characterise
  (~4 h).

### D. Brush / swab pickup + comb knock-off

A natural-bristle brush or static-dissipative microfibre swab is
clamped to the spindle. The gantry dips the brush into a powder dish;
particles adhere to the bristles by van der Waals + electrostatic
attraction (the same surface forces that make cohesive powders hard to
dose by gravity become the *mechanism* here). The gantry transports the
loaded brush to the dispense site and drags it across a fixed printed
**comb** that mechanically knocks particles off into the target vial.

- *Mechanism in the PR #11 taxonomy*: not directly represented in the
  commercial landscape — closest analogue is the dual-arm spatula
  dispenser of Jiang et al. 2023 (PR #11 §6), but at a much smaller
  pickup mass.
- *Why it's interesting*: turns the cohesive-powder failure mode into
  the design principle; absolutely minimal hardware; very small mean
  doses (likely sub-mg).
- *Risks*: highly powder-dependent; mass per stroke probably has high
  RSD; needs external balance / weighing for any usable accuracy.
- *Build day*: print brush holder + comb + reservoir (~2 h),
  characterise (~4 h).

### E. Salt-shaker oscillation dispenser

A printed cup with a calibrated bottom slot/mesh is moved by the gantry
in a fast sinusoidal X-Y "shake" pattern over the target. Total dose is
proportional to (shake amplitude × frequency × duration). No tap
required — the side-to-side acceleration substitutes for the vertical
tap of concept A.

- *Mechanism*: gantry-driven analogue of a vibratory sieve feeder (PR
  #11 §4 cites commercial equivalents from 0.36 to 1440 g/h).
- *Why it's interesting*: smooth, continuous control of dose by time
  rather than discrete taps; no impacts on the gantry frame.
- *Risks*: GRBL feedrate / acceleration limits cap how "vibratory" the
  motion really is — the 3018 is not a piezo. Minimum stable dose may
  be tens of mg.
- *Build day*: print cup (~1 h), tune G-code shake pattern (~3 h),
  characterise (~3 h).

### F. Passive auger via rack-and-pinion against a fixed pin

A short Archimedes screw inside a printed tube is geared (printed
rack + pinion or one-way clutch) to a small linear stage on the
spindle. As the gantry pushes the stage past a fixed pin on the bed, the
pinion ratchets the screw forward by a fixed angle, positively
displacing one auger-thread of powder out of the tube tip into the
target vial.

- *Mechanism in the PR #11 taxonomy*: volumetric screw / auger feeder,
  the dominant industrial principle (Coperion K-Tron, Acrison, Schenck;
  PR #11 §3) — but here all rotation comes from gantry push, no motor.
- *Why it's interesting*: continuous and repeatable in principle; gives
  per-stroke dose set by pitch × thread cross-section.
- *Risks*: small printed augers are leaky / fragile; tolerances on
  printed gear teeth are marginal at this size; cohesive powders pack
  against the auger root; build complexity is the highest of the
  passive options.
- *Build day*: high — design and print auger + clutch + stage (~6 h),
  iterate, characterise. Risk of not finishing in one day.

### G. Add a single ERM coin motor to concept A

Identical to concept A (tap-driven sieve cup) but augmented with a
~$2 ERM "phone haptic" coin motor glued to the side of the cup, run
from a 3 V coin cell via a SPST switch (no microcontroller). The motor
provides higher-frequency vibration than the gantry tap can supply,
extending the lower bound of dose-rate and improving repeatability.

- *Why it's interesting*: best-evidence, lowest-risk way of attacking
  the cohesive-powder regime if a single active component is acceptable
  (matches the strategy already proposed in
  [issue #3 Challenge 2](https://github.com/vertical-cloud-lab/powder-excavator/issues/3#issue-anti-adhesion)).
- *Risks*: introduces one battery / motor / switch — the smallest
  possible deviation from "fully passive". Vibration amplitude is
  fixed; closed-loop control requires either a relay or an MCU.

### H. Solenoid-tapped sieve (closed-loop tap)

Concept A but with a 5 V push-pull solenoid replacing the gantry tap,
fired by a microcontroller against an external balance reading. This is
the most accurate path here but also the most "electronics-heavy", and
duplicates much of what a Quantos already does — likely not worth the
build-day risk on day-of-workshop.

## Ranking summary (revised after Edison feedback)

The ranking below has been updated to reflect the Edison literature
critique (full text in [`edison_result.md`](./edison_result.md), task id
`c0c87f11-6e21-41a7-85dd-6ca3429e3fe3`). Edison's main correction was to
**promote concept G above concept A**: continuous ERM vibration matches
the published vibratory-sieve-chute regime (Besenhard et al. 2015 [1],
mg-scale capsule fills, with a measurable no-flow threshold at low
excitation and spillage at high excitation) much more closely than a
discrete gantry tap, whose **energy is quantized** and depends on
machine compliance. Dose-floor and RSD columns are now anchored to the
closest peer-reviewed analogues rather than to gut estimate.

| Rank | Concept | Active comps. | Realistic min. dose (cohesive < 100 µm) | Expected RSD | Closest published analogue |
| --- | --- | --- | --- | --- | --- |
| 1 | **G. ERM-augmented sieve** | 1 (coin motor + cell) | ~0.5–2 mg open-loop; ~0.2–1 mg with weigh-and-stop | ~5–15% open-loop; ~3–10% closed-loop | Vibratory sieve–chute microdoser, Besenhard 2015 [1] |
| 2 | **A. Tap-driven sieve cup** | 0 | ~1–5 mg open-loop; ~0.5–2 mg with iterative gravimetric | ~10–30% open-loop; ~5–15% closed-loop | Same vibratory-sieve family [1] but with quantized impulse |
| 3 | **B. Pez-style chamber strip** | 0 | ~1–10 mg per cavity | ~10–25% on cohesive fines | Low-dose dosator capsule fill, Faulhammer 2014 [2,3] |
| 4 | **C. Capillary dip + wiper** | 0 | ~0.5–5 mg; possibly 0.1–1 mg with iteration | ~8–20% (worse on cohesive) | Manual PowderPicking, Alsenz 2011 [4] — 0.6–25 mg, ~6 % CV |
| 5 | E. Salt-shaker oscillation | 0 | ~1–10 mg | ~15–40% open-loop | Same vibratory sieve family but less controlled [1] |
| 6 | F. Passive auger | 0 | ~2–20 mg per stroke | ~10–30% (bridging dominates) | Cohesive-powder feeder failure modes, Hou 2024 [5], Besenhard 2017 [6] |
| 7 | D. Brush pickup + comb | 0 | ~0.1–2 mg "transferred" | ~20–100 % | No clear peer-reviewed analogue retrieved |
| 8 | **H. Solenoid + balance** | 2+ (solenoid, MCU) | ~0.1–1 mg | ~1–5 % once tuned | Closed-loop vibratory sieve [1]; intent matches Quantos workflow |

**Recommended for the one-day build (revised):** lead with concept **G**
(tap-driven sieve cup + a single ~$2 ERM coin motor on a coin cell), and
keep concept **A** as the parallel-track fully-passive backup so that if
the ERM hardware is unavailable or fails, the same printed cup runs
unchanged off gantry-tap impulses. Concept **B** (Pez chamber strip)
remains a useful third track because it can be characterised on a
benchtop balance even when the 3018 isn't free. Edison's evidence does
**not** support our earlier instinct that A alone was the strongest
candidate — going from a single tap to continuous-but-bounded vibration
is what gives access to the documented sub-mg vibratory-sieve operating
window.

> **Preliminary design** for both A and G (single parametric SCAD
> source, printable today, with a bed-mounted anvil for A) is at
> [`../preliminary-design-sieve-cup.md`](../preliminary-design-sieve-cup.md);
> printable parts live in [`../../cad/`](../../cad/).

## Build mitigations carried over from the Edison citations

These come directly from the failure modes the cited papers attribute to
each archetype, so the one-day prototypes should bake them in from the
start:

- **A / E / G / H (sieve / shaker family).** Design the printed cup so
  the **excitation amplitude is adjustable** — Besenhard et al. show a
  hard no-flow threshold at low amplitude and spillage at high
  amplitude [1], so an adjustable mount (e.g. set-screw preload on the
  ERM, swappable anvil heights for A) is more important than nominal
  amplitude. Make the bottom mesh **swappable per powder**, and add a
  way to **re-level the powder bed** between runs — bed condition
  mattered even in lab vibratory-sieve-chute systems [1].
- **C (capillary + wiper).** Copy the three explicit mitigations that
  let manual PowderPicking reach ~6 % CV [4]: (i) tap / compact the
  source bed before each pick, (ii) take **multiple** insertions
  ("picking") per dispense rather than relying on a single fill, (iii)
  include an explicit external-tip wipe step *before* the shear-off
  wipe over the target.
- **B / F (cavity strip and passive auger).** Assume cohesive sub-100-µm
  powders will become **non-volumetric** — Faulhammer's "Group II"
  regime [2,3] — and will form plugs / arches at small geometries.
  Either restrict use of these concepts to better-flowing powders, or
  add a compaction / vibratory-conditioning step to the fill process.

## Additional alternatives surfaced by the Edison critique

Edison flagged six further micro-dose primitives we hadn't enumerated
that meet the same gantry / one-day / 3D-print-friendly constraints.
They are listed here for completeness; none are prioritised for this
workshop because each adds either non-trivial electronics or non-
trivial EHS handling, but they are worth tracking for follow-on work.

- **I. Electrostatic pickup / release wand.** A high-voltage,
  low-current electrode behind a dielectric tip charges to attract
  powder and discharges (or reverses) to release. Can plausibly reach
  the µg–sub-mg regime by making cohesive adhesion *controllable*
  rather than a nuisance. Cost: HV electronics, contamination, humidity
  sensitivity.
- **J. Tribo-electric "spray" / puff deposition.** Tribo-charge in a
  small channel and release a charged plume onto a grounded target.
  Microgram-scale possible; cost is airborne-dust / EHS handling.
- **K. Carrier-particle assisted magnetic dispensing.** Blend the
  cohesive powder with a known mass fraction of ferromagnetic carrier
  beads, then magnetically pick a controlled count of beads (each
  carrying a known small powder fraction). Converts a cohesive-powder
  problem into a coarse-particle problem; cost: changes the formulation
  and adds a segregation risk.
- **L. Gas-pulse micro-hopper.** A small chamber with an orifice and a
  squeeze-bulb / solenoid valve fires a calibrated pressure pulse to
  break arches and eject a small quantity. Can be made *passive* if the
  gantry compresses the bulb against a fixed feature.
- **M. Vacuum pick-and-place "suction dosator".** Pull a small powder
  plug into a tip with vacuum from a cheap diaphragm pump; mechanically
  eject at the target. Closer to true dosator physics than concept C.
- **N. Adhesive PDMS / tape stamp.** Pick a thin powder layer onto a
  controlled-area sticky pad; release by contact transfer. Very fast
  prototyping; poor quantitative repeatability and contamination risk.
- **O. Meltable-binder micro-pelletization.** Briefly contact powder
  with a tiny molten-wax droplet (or heated tip) so a reproducible
  pellet adheres; deposit pellet at the target. Turns the cohesive
  powder into a handled solid; cost: chemistry compatibility and
  heating hardware.

## Where this leaves the sub-10 mg cohesive-powder gap

Mapping back to the gap statement in PR #11 §5:

- **Most plausible one-day gap-closers:** **G** and **H**, because the
  vibratory-sieve operating window has been quantitatively characterised
  in the low-mg regime with a definable amplitude window and a
  closed-loop overshoot-prevention strategy [1]. **G** is the
  one-day-friendly path; **H** is the accuracy-maximising but
  electronics-heavy path.
- **Partial gap-closers:** **A** and **C**, especially when paired with
  iterative gravimetric ("dose, weigh, top-up") control. A leverages the
  same vibratory physics with cruder excitation [1]; C inherits the
  0.6 mg manual lower bound demonstrated by PowderPicking [4].
- **Unlikely to close the gap on their own:** **B**, **D**, **E**, **F**
  on cohesive sub-100-µm powders without added vibratory conditioning,
  compaction control, anti-static, or closed-loop weighing.

## Edison feedback query

A single Edison **literature** query was submitted (don't-wait policy,
per the issue) and has been fetched. Artefacts:

- [`edison_query.json`](./edison_query.json) — submitted task id
  `c0c87f11-6e21-41a7-85dd-6ca3429e3fe3`, prompt, and submission
  timestamp.
- [`edison_result.md`](./edison_result.md) — full formatted answer with
  inline citations.
- [`edison_result.json`](./edison_result.json) — raw API response.
- [`fetch_edison_result.py`](./fetch_edison_result.py) — re-fetch script
  used to produce the two files above.

## References (from the Edison answer)

1. Besenhard, M.O. *et al.* "Accuracy of micro powder dosing via a
   vibratory sieve-chute system." *Eur. J. Pharm. Biopharm.* 94,
   264–272 (2015). DOI: [10.1016/j.ejpb.2015.04.037](https://doi.org/10.1016/j.ejpb.2015.04.037).
2. Faulhammer, E. *et al.* "Low-dose capsule filling of inhalation
   products: critical material attributes and process parameters."
   *Int. J. Pharm.* 473, 617–626 (2014). DOI: [10.1016/j.ijpharm.2014.07.050](https://doi.org/10.1016/j.ijpharm.2014.07.050).
3. Faulhammer, E. *et al.* "Effect of process parameters and powder
   properties on low-dose dosator capsule filling."
4. Alsenz, J. "PowderPicking: an inexpensive, manual, medium-throughput
   method for powder dispensing." *Powder Technology* 209, 152–157
   (2011). DOI: [10.1016/j.powtec.2011.02.014](https://doi.org/10.1016/j.powtec.2011.02.014).
5. Hou, P. C-H. "Development of a micro-feeder for cohesive
   pharmaceutical powders." Dissertation (2024). DOI: [10.48730/4gp7-jb67](https://doi.org/10.48730/4gp7-jb67).
6. Besenhard, M.O. *et al.* "Micro-feeding and dosing of powders via a
   small-scale powder pump." *Int. J. Pharm.* 519, 314–322 (2017).
   DOI: [10.1016/j.ijpharm.2016.12.029](https://doi.org/10.1016/j.ijpharm.2016.12.029).
7. Jiang, Y. *et al.* "Autonomous biomimetic solid dispensing using a
   dual-arm robotic manipulator." *Digital Discovery* 2, 1733–1744
   (2023). DOI: [10.1039/d3dd00075c](https://doi.org/10.1039/d3dd00075c).

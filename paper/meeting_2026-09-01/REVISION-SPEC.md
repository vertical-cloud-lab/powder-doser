# Revision spec — powder-doser manuscript (PR #97)

**Status: draft for human review. Nothing here has been implemented.**

This is the merge Sterling described at `01:27:41`: the meeting transcript, Sam's
written notes, the open PR threads (#97, #149, #150), the round-2 Edison mock
review and the round-1 dataset, combined into one ordered work-list. Review it,
edit it, and then it gets executed.

Evidence for every item is in **[MEETING-FEEDBACK.md](MEETING-FEEDBACK.md)**;
`F##` tags below point into it. `S##` tags are this spec's own item numbers — use
them to accept, reject or amend individual items.

**How to review this:** the fastest useful pass is (1) read §0 and decide the six
questions in §9, (2) skim the figure table in §2 and say which of the eight
figures you want, (3) mark anything in §3–§6 you disagree with. Everything else
follows from those.

---

## 0. The one thing that blocks everything else

### S01 — ⚠️ Resolve the gear ratio before regenerating any figure
`F106` · **Blocker** · Owner: Sam + Claude

Three sources disagree about the stepper-to-auger reduction:

| Source | Says | |
|---|---|---|
| `cad/auger-geared/stepper-pinion.scad` | `Z_g / Z_p = 48 / 16 = 3.0 : 1` | authoritative |
| `paper/main.tex` §Mechanical design | `2.25:1` | **wrong** |
| `hardware/.../firmware/main.py` | no gear term at all → effectively `1:1` | **wrong** |

The firmware computes `steps_per_rev = STEPPER_FULL_STEPS_REV * STEPPER_MICROSTEPS`,
so a commanded "revolution" is one **stepper** revolution — one third of an auger
revolution. This matches Sam's account exactly: *"When I commanded three
revolutions, that was one revolution."*

**Everything downstream is affected:**

- Every `mg per revolution` value in A2, F1, D1, R2, R3, R4, R6, R8 is per
  *stepper* revolution. Per auger revolution they are **3× larger**.
- Protocol C's "6 revolutions per tilt" were **2 auger revolutions**.
- Protocol D's "3 revolutions" were 3.44 / 4.63 *stepper* revolutions (S02) —
  about **1.15 / 1.54 auger revolutions**.
- **The one-slug-per-revolution result (`F91`) may be misattributed.** The
  autocorrelation peak is 3.94 s against a 4.00 s *commanded* revolution at 15 rpm.
  If the auger actually turns at 5 rpm, one slug per *auger* revolution would be
  12 s. So either the discharge is quantised per *stepper* turn — which needs a
  mechanical explanation, since the flights turn once per auger revolution — or
  the period attribution is wrong. This is currently one of the headline
  mechanistic results and it must be re-derived before publication.

**Acceptance:** a single documented ratio constant, applied once in the analysis
pipeline; `main.tex` corrected to 3.0:1; the firmware either applies the ratio or
its output is explicitly labelled "stepper revolutions"; every regenerated figure
states which revolution it means in the axis label; and the slug-period question
answered one way or the other.

### S02 — Fix the block-D over-rotation on the Pico
`F103` · **Blocker for the speed sweep** · Owner: Sam

The speed loop advances its own clock by the nominal 250 ms poll period while each
iteration actually waits 287 ms (early) or 386 ms (after 2026-08-20) for a balance
read, with the auger in velocity mode throughout. Fix by measuring elapsed time or
using a positioned move. Sterling began drafting an issue for this during the
meeting (`01:12`).

**Acceptance:** commanded revolutions equal delivered revolutions to within one
slug on the 15 rpm traces, verified on a fresh run.

### S03 — Balance auto-off
`F74` · Owner: Sam

The A&D HR-100A was found off mid-campaign with no explanation. Determine whether
it has an auto-off, disable it or add a keep-alive, and mark gaps in the streamed
record explicitly so a dropout cannot be mistaken for a flat reading.

---

## 1. Standing rules for every figure

These apply to all figures below and to the pipeline in general. They came up
repeatedly rather than once.

| | Rule | From |
|---|---|---|
| **S04** | No explanatory text baked into the figure image. Everything explanatory goes in the LaTeX caption. | `F17` |
| **S05** | Powders that conveyed nothing are **not plotted at a numeric position** — no arrows, no bounds, no markers. They appear as struck-through row labels in a "did not convey" band, explained in the caption. | `F11`, `F16`, `F33` |
| **S06** | Derived ratios inherit censoring. A "2× gravity assist" computed from two noise-floor readings must not appear as a number. | `F79` |
| **S07** | No jitter when n = 3. Replicates align on the category position. | `F30` |
| **S08** | Keep the surrogate (food-safe) vs research-relevant colour split everywhere it applies. | `F15` |
| **S09** | Every cross-powder caption states that fill level was uncontrolled, that particle size/shape were not measured, and where the raw data lives. | `F18`, `F19` |
| **S10** | No undefined acronyms on axes. `RSD` is spelled out or replaced; `feed factor` is defined at first use; `block C` never appears in a reader-facing label. | `F10`, `F23` |
| **S11** | Note log scale explicitly wherever relative and absolute effects diverge. | `F82` |
| **S12** | Powder type is not a major axis unless the panel is specifically about between-powder comparison. Encode powder by symbol/colour instead. | `F02`, `F99` |

---

## 2. The figure set

Sam asked for a definite list rather than a menu (`F126`: *"we want these eight
figures — look at the data and give me these eight figures"*). This is that list:
**seven main figures and two main tables**, plus SI.

### Main text

| # | Figure | Content | Source | Status |
|---|---|---|---|---|
| **S13** | Fig. 1 | Platform overview | existing `fgr:overview` | **Edit:** delete panel (e) timeline (`F03`); add coordinate frame to panel (c) (`F05`); replace the CAD render in (a) with the bench photograph when available |
| **S14** | Fig. 2 | Design specifics | existing `fgr:design` | **Decide:** keep 2(a) cross-section; 2(b) tap collar either gets a stated purpose, moves into Fig. 3, or is cut (`F06`, §9 Q2) |
| **S15** | Fig. 3 | Generative-AI CAD outcomes | existing `fgr:genai` | **Keep as is.** Explicitly endorsed (`00:05:35`) |
| **S16** | Fig. 4 | **Dispensing performance** (new, 3 panels) | round-1 data | **Replaces the synthetic figure entirely** (`F07`) |
| **S17** | Fig. 5 | **Actuation knobs, isolated** (new, 2–3 panels) | round-1 data | New (`F61`) |
| **S18** | Fig. 6 | **Operating map** | candidate F1, relabelled | New to the paper (`F23`) |
| **S19** | Fig. 7 | Future work / multi-doser | existing `fgr:future` | **Edit:** refresh once the revised plan lands |
| **S20** | Table 1 | The powders **as run** (13) | round-1 inventory | **Rewrite** from plan to record (`F08`) |
| **S21** | Table 2 | **Test protocols A–I** | PR #150 Table S2 | **Move from SI to main text** (`F60`); extend with H and I |

### S16 — Fig. 4 "Dispensing performance", in detail

The three panels answer Sterling's three reader questions (`F44`): *can you dose
it, how fast, can you be accurate?*

- **(a) Can you dose it — and how much per turn.** Feed factor for all 13 powders
  on a log axis, surrogate vs research-relevant by colour, the three
  non-conveying powders as struck-through labels in a "did not convey" band.
  Source: candidate A2, **rescaled per S01**. Axis label in plain language, and
  it must say *auger* revolution.
- **(b) What the flow actually looks like.** Mass-vs-time staircase traces for a
  representative subset. Source: candidate C2, unchanged in concept — this is the
  panel both authors liked without reservation (`F46`).
- **(c) Can you be accurate, and what does it cost.** **Dose error vs time to
  dose**, one marker per dose, powder by symbol + colour, termination state
  encoded, protocol G only. This is the specific new figure Sterling asked for
  (`F58`) and it also appears in Sam's written notes. Axis renamed to remove the
  "time to terminate" ambiguity (`F36`).

> **Coverage warning.** Panel (c) is currently built from the *worse* half of the
> powder set: protocol G is missing for AlSi10Mg, barium chloride, fumed silica,
> Si (110/200), sodium sulfate and NaCl — five of the six best conveyors plus the
> control. **S30 (re-run protocol G) is what makes this panel publishable.**

### S17 — Fig. 5 "Actuation knobs, isolated", in detail

- **(a) Tilt.** Mass per auger revolution vs tilt (0/45/90°), framed as *how much
  of the delivery is gravity rather than the auger* (`F77`). Keep the Si (−325)
  result — nothing at 0° and 45°, something at 90° (`F80`).
- **(b) Speed.** Rate vs auger speed with the fill-limited / mobilisation-limited
  split (`F86`). **Gated on S02 and S31** — n = 1 per speed, no taring between
  speeds, and a fixed 15→45→90 order that perfectly confounds speed with sequence
  position. Do not publish until re-run.
- **(c) Tap.** Mass per solenoid tap vs feed factor, showing that powders with
  near-identical feed factors have ~10× different tap quanta (`F67`, `F68`).

> **No vibration arm exists.** Protocol F has produced zero records in 11 attempts
> (`F55`). Either fix the DRV2605L before round 2 and add a panel (d), or say
> plainly in the text that vibration assistance was fitted but not characterised
> — see §9 Q3.

### S18 — Fig. 6 "Operating map"

Candidate F1, kept for its argument (a two-number fingerprint places a new powder
into *readily doseable* / *slow, fine-only* / *not doseable*) but relabelled
throughout per S10. Both axes come from ~2 minutes of bench time, which is the
selling point.

**Honesty constraint:** there is no independent characterisation of these powders
(no PSD, no bulk density, no shear cell), so this is a clustering rather than a
validated diagnostic, and the caption must say so. See S39.

### Supplementary

| # | Item | From |
|---|---|---|
| **S22** | Fig. S1 nozzle variants — keep | existing |
| **S23** | Fig. S2 **generative-AI usage per unit time** (replaces the deleted Fig. 1e timeline) | `F04` |
| **S24** | Fig. S3 **SEM / powder characterisation** | `F39` |
| **S25** | Fig. S4 **bench environment**: noise floor by date and location (lab / fume hood / enclosure) | `F118` |
| **S26** | Table S1 BOM — keep | existing |
| **S27** | Table S3 **run inventory**: date, powder, location, protocols completed, QC verdict | `F09`, `F119` |
| **S28** | **Data dictionary** defining every recorded column and the word "trial" | `F52`, `F57` |

---

## 3. Bench work (round 2)

Sam committed to running these on the Thursday after the meeting (`F124`).

### S29 — Protocols H and I: closed-loop mass ladder at 50 / 200 / 1000 mg
`F111`–`F114` · **Highest value** · Owner: Sam

Supersedes the earlier 5 g / 500 mg / 50 mg / 20 mg plan. 5 g dropped (refill
burden; limited stock of Si 110/200). 20 mg dropped (below the post-fume-hood-move
noise floor). The 50 mg point is deliberately near the noise floor — report the
per-run floor alongside it rather than presenting it as clean.

### S30 — Re-run protocol G for the six missing powders
`F72` · **Highest value** · Owner: Sam

AlSi10Mg, barium chloride, fumed silica, Si (110/200), sodium sulfate, NaCl.
Sterling: *"filling in these would be the completeness step for the manuscript."*
Without this, Fig. 4(c) characterises only the powders that dose badly.

### S31 — Re-run the speed sweep properly
`F83`, `F110` · Owner: Sam

Tare between speeds, randomise speed order, and only after S02 is fixed. Consider
polling faster (or running the sweep at low rpm only) so the within-revolution
structure is not aliased above 15 rpm.

### S32 — Weigh the loaded auger before and after every run
`F20` · Owner: Sam · Cheap and permanent

Gives fill level, total conveyed mass, and a check on collected-vs-conveyed mass —
which is currently an unquantified under-collection sitting beneath every feed
factor.

### S33 — Record bench location per run
`F118`, `F119` · Owner: Sam / reconstructable for round 1

Lab / fume hood / fume hood + enclosure. For round 1 this is recoverable from
Sam's rule (food-safe in the lab, non-food-safe in the fume hood) and the live
streams. **State that location is confounded with powder class** — every
research-relevant powder was measured in the noisier environment.

### S34 — *(optional)* Bulk and tapped density on ~10 mL of each powder
Not raised in the meeting; carried over from the earlier analysis. One hour, no
capital cost, and it is what would turn Fig. 6 from a clustering into a calibrated
map. Flagged for a decision rather than assumed — see §9 Q5.

---

## 4. Main-text changes

| # | Change | From |
|---|---|---|
| **S35** | Apply the PR #149 jargon audit. Priority order: abstract, Conclusions' 117-word sentence, the four words that mean something else to a DD reader (*ablations*, *silent regressions*, *interferences*, *primitives*), the eight unexpanded acronyms, and the seven different names for "no ordinary CAD program was used". | `F01` |
| **S36** | Rewrite §Dispensing performance from future tense to past tense with real results. | `F07` |
| **S37** | Add the stall mechanism: the three-phase controller is monotonic (bulk → fine → tap) with **no return to an earlier phase**, so once the flight nearest the exit empties, tapping alone cannot refill it. CMC spent 148 taps and never reached target. Name phase re-entry as future work. | `F42`, `F43` |
| **S38** | Frame the three non-conveying powders as an **auger-geometry limitation of this design** (wider cavity / larger pitch / taller flight would move the boundary), not as properties of those powders. Distinguish two failure modes: cohesion-vs-driving-force (Si −325) and aeration (fumed silica). | `F66`, `F21` |
| **S39** | Add the mechanistic paragraph on why the extremes behave as they do: gas-atomised AlSi10Mg is spherical and narrowly distributed *because LPBF requires it*; milled Si (−325) is angular and fine. | `F21`, `F22` |
| **S40** | Promote "nothing flows on its own" from assertion to measurement. Protocol B measures the clean-shutoff claim the manuscript currently asserts. | `F100` |
| **S41** | Add the operating-envelope statement and the U of U gap: 0.1–10 mg is **not** currently achievable; extending to it needs per-powder calibration, vibration isolation, and revised auger dimensions. Cite issue #117. | `F115`, `F117` |
| **S42** | Future work: the dosing battery as a cheap powder-characterisation instrument (speed sweep distinguishes cohesive from non-cohesive). Present as a hypothesis with a named validation experiment, **not** as a demonstrated capability. | `F88`, `F89` |
| **S43** | Future work: pause-mid-revolution experiment and transparent (resin-printed) augers. | `F102` |
| **S44** | Limitations: the reset problem — dose outcome depends on where in the helix powder happens to sit at the start; there is no defined reset; and in real dosing you would never reset anyway. | `F95` |
| **S45** | Correct the gear ratio in §Mechanical design from 2.25:1 to 3.0:1. | `S01` |
| **S46** | Cut crest factor entirely. | `F96` |
| **S47** | Reconcile the two acceptance bands. The paper declares ±5 % at ≥100 mg while the firmware chases ±5 mg — a band 10× tighter at a 1 g target. That difference is what turns four passing powders into "stalled". Also revisit the "per-dose times under 30 s" claim: doses that reached ±5 mg took 113–265 s. | carried over; sharpened by `F41` |

---

## 5. Style rules for AI-drafted text

### S48 — Drop the rhetorical register
`F65` · Standing

State limitations plainly. *"Only one measurement was taken at each speed, so a
coefficient of variation cannot be computed"* rather than *"No, you cannot compute
the CV from n = 1."* The statistics were right; the register was not. This applies
to analysis comments as well as manuscript prose.

---

## 6. Repository and process

| # | Item | From |
|---|---|---|
| **S49** | Rename "block" → "test protocol" in all prose and tables. The `block` field name stays in the firmware and the archived CSV schema — that is a wire format, and renaming it would break every committed dataset. | `F26`, PR #150 |
| **S50** | Define "trial" in the protocol table and the data dictionary. For protocol C, 18 = 6 revolutions × 3 tilts, so the revolution is the trial. Resolve protocol B's three-trial structure by reading `powder_battery.py`, not from memory. | `F50`, `F52` |
| **S51** | Record what each protocol is *for* in the collection script itself, so the "what did we even collect?" problem does not recur. | `F09` |

---

## 7. Explicitly out of scope for this manuscript

- Multi-doser weighing station (`F120`) — record in the multi-doser thread.
- Bayesian / algorithmic dose optimisation — remains Will's thread and future work.
- The 0.1–10 mg regime (`F115`) — stated as a gap, not attempted.

---

## 8. Sequencing

```
S01 gear ratio ──┬──> rescale dataset ──> regenerate S16(a), S17, S18
S02 block-D fix ─┘                    │
                                      │
S30 re-run protocol G ────────────────┴──> S16(c) becomes publishable
S29 protocols H and I ────────────────────> parity/ladder result for the preprint
S31 speed re-run ─────────────────────────> S17(b) becomes publishable

S35 jargon pass (PR #149) ── independent, can start now
S21 move protocol table to main ── independent, can start now
S13/S14/S15 figure edits ── independent, can start now
                                      │
                                      └──> Overleaf ──> preprint ──> submit
```

Target: revisions back by **November** (`F123`). Preprint before or alongside
submission, with the H/I ladder included because it pre-empts the most obvious
reviewer question (`F125`).

---

## 9. Questions that need a human decision

These are the points where the meeting did not settle on an answer, or where the
material conflicts. The spec cannot be executed cleanly without them.

**Q1 — Is the eight-figure set above the right set?**
Seven main figures + two main tables. Say which to cut, merge or add. (`F126`)

**Q2 — What happens to Fig. 2(b), the tap collar?**
Sterling could not tell whether it was a design panel or a generative-AI panel.
Options: give it a purpose in the caption, move it into Fig. 3, or cut it. (`F06`)

**Q3 — Vibration: fix it, or drop the claim?**
Protocol F has never produced a record. Either repair the DRV2605L before round 2
and add an ablation arm, or remove "vibration assistance" from the abstract and
platform overview. Right now the paper advertises a capability that has never been
measured. (`F55`)

**Q4 — "Digital Discovery's parameters, etc.?"**
This is in Sam's notes but was never discussed aloud. Read as *do we meet the
journal's requirements for a hardware Full Paper?* — if so, a compliance checklist
against `paper/guidelines/` is straightforward. Confirm the intent. (`§O`)

**Q5 — "More about what we learned about AI's limitations?"**
Also notes-only. The generative-AI half is the thinner of the paper's two
contributions, and the round-2 Edison reviewer (Schulz) asked for the same
expansion — quantitative log analysis, a defect taxonomy, a formalised workflow
diagram. But expanding it cuts against the push to shorten and simplify. Which
way? (`§O`)

**Q6 — Do the S34 bulk/tapped density measurements happen?**
One hour of work. It is what would let Fig. 6 claim to be a calibrated map rather
than a clustering, and it lets two published relationships be tested directly. Not
raised in the meeting, so it is not assumed.

---

## 10. What is *not* in this spec, and why

- **Nothing has been implemented.** Per `F127`, the agreed sequence is merge →
  review → run. This is the merge.
- **The PR #149 jargon fixes are not restated here.** They are already written up
  line-by-line in `paper/readability/JARGON-AUDIT.md`; duplicating them would
  create two sources of truth.
- **Deferred Edison review items are not re-litigated.** Where the meeting and the
  Edison reviewers ask for the same thing (real data, characterisation table,
  actuation ablation), the meeting's wording is used, since it comes with the
  authors' own priorities attached.
- **The bench photograph for Fig. 1(a)** and the corresponding-author email remain
  human TODOs already flagged in `main.tex`.

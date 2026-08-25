# Dose-rate EDA — issue #116 round-1 battery, blocks A–F

Exploratory analysis of everything the round-1 campaign measured about **dose
rate**: what the auger delivers, and how that changes with powder, tilt, speed
and actuation mode. Block G (the three-phase closed-loop controller) is
deliberately out of scope here — it is a *controller* result, and the candidate
figures for it live in [`../candidates/`](../candidates).

```bash
python eda_dose_rate.py          # -> out/*.png and out/rate_summary.csv
```

Inputs are the committed tidy CSVs in [`../candidates/data/`](../candidates/data),
distilled by `../candidates/build_dataset.py` from the per-run artifacts on the
`claude/issue-116-*` branches. `out/rate_summary.csv` is the one-row-per-powder
table of every derived quantity discussed below.

## What was collected

Twenty battery runs between 2026-08-04 and 2026-08-21, 13 distinct powders,
14 QC-valid for cross-powder comparison. The battery is one *frozen* sequence
run identically for every powder — the firmware docstring is explicit that this
"is deliberately not an optimization workflow".

| Block | What it varies | Measurement | Trials/run |
|---|---|---|---|
| A `baseline` | nothing | 8 no-actuation deltas at tilt 45° | 8 |
| B `hold` | tilt (0/45/90°) | mass change over a 15 s static hold, no actuator | 3 |
| C `rotation` | tilt (0/45/90°) at 30 RPM | 6 × single 360° revolutions, stable read after each | 18 |
| D `speed` | auger RPM (15/45/90) at tilt 45° | 3 rev continuous + streamed balance polls | 3 (+48/16/8 polls) |
| E `tap` | tilt (0/45°) | 8 × (measured 360° re-feed + one solenoid tap) | 32 |
| F `vib` | tilt (0/45°) | same with the ERM motor | **0 — never ran** |
| G `dose` | — | 3 closed-loop 1 g doses (out of scope here) | 0–3 |

Block F never produced a single trial in any run: the DRV2605L haptic driver
reports EIO, and 11 of the 19 runs requested block F and got a META skip row.
**The vibration actuator is uncharacterised across the whole campaign.** The
manuscript's Experimental section is already correct about this ("the ERM
vibration motor is available as an additional agitation primitive but is not
used in the baseline procedure"), but the abstract and platform overview still
advertise "tapping and vibration assistance", and the planned actuation ablation
(auger only / +tap / +vibration) currently has no vibration arm to report.

## The eight panels

| # | Figure | Question |
|---|---|---|
| R1 | `R1_coverage.png` | What did the campaign actually measure, per powder? |
| R2 | `R2_rate_ladder.png` | What is the dose rate at one reference condition? |
| R3 | `R3_tilt.png` | What does tilt buy, and how much of the flow is gravity? |
| R4 | `R4_speed.png` | What does auger speed buy? |
| R5 | `R5_instantaneous.png` | What does the flow look like *in time*? |
| R6 | `R6_knobs.png` | What is each control knob worth, per event? |
| R7 | `R7_normalisation.png` | A defect in block D's per-revolution normalisation |
| R8 | `R8_variance.png` | Which parameter actually explains the rate? |

## Findings

**1. Rate spans three decades under one frozen parameter set.** At the
reference condition (30 RPM, tilt 45°) the module delivers 115 mg/s for
AlSi10Mg and ≤0.12 mg/s for fumed silica. Three powders (brown rice flour,
Si −325 mesh, fumed silica) are *censored*, not small — they never cleared the
balance floor, and are drawn as upper bounds throughout.

**2. Tilt is the strongest knob the firmware owns.** Median gravity assist
(mg/rev at 90° ÷ mg/rev at 0°) is **6.9×**, range 2.2–14.5×. It is also the
*only* knob that turns a non-doseable powder into a doseable one: Si −325 mesh
conveys literally nothing at 0° and 45° and 1.2 mg/rev at 90°.

**3. Speed is sub-linear, and that splits the powders into two regimes.**
Fitting rate ∝ RPM^α gives a median **α = 0.78** — six times the speed buys
about **4.1×** the rate, not 6×. Equivalently, mass per revolution *falls* with
speed (median exponent −0.34): the flights fill by time, not by turn. Three
powders invert this (white rice flour α = 1.36, CMC 1.13, sodium alginate 1.08):
they are cohesive, and the faster rotation mobilises them rather than starving
them. The split is **fill-limited vs mobilisation-limited**, and it predicts
opposite tuning advice for the two groups.

*Depletion control:* within a block-C tilt (six consecutive revolutions at fixed
conditions) mass declines by a median **1.0 % per revolution**, so the ~9
revolutions of a block-D sweep can account for at most ~9 % of the observed
15→90 RPM decline of 30–50 %. The speed effect is real, though speed and
sequence position are perfectly confounded by the fixed 15→45→90 order.

**4. The discharge is quantised at one slug per revolution.** Autocorrelating
the semi-instantaneous rate from the 15 RPM poll traces gives a median peak at
**3.94 s** against a revolution period of 4.00 s, over 10 powders. The crest
factor (95th-percentile instantaneous rate ÷ mean) is **2.8 at 15 RPM**,
falling to 2.3 and 1.9 at 45 and 90 RPM — but the balance polls only every
0.29–0.39 s, so a 0.67 s revolution at 90 RPM is sampled below Nyquist and
those two numbers are aliased floors, not measurements.

**5. Nothing flows on its own.** Across every powder and every tilt, a 15 s
static hold with no actuation produced no mass change that clears its own run's
noise floor — with one marginal exception (Si 110/200 mesh, 46 mg at 90° against
a 29 mg floor). The two largest apparent hold signals (sodium sulfate 120 mg,
NaCl 42 mg) both occur at tilt **0°**, where gravity discharge is impossible,
so they are bench drift. This is direct evidence for the "clean shutoff"
design claim, and it should be reported rather than assumed.

**6. The tap is a fine increment, where it is resolvable at all.** Where a tap
clears the run's noise floor it delivers 1–12 % of a revolution (calcium lactate
20.4 mg/tap = 12 % of a rev; xanthan gum 13.6 mg = 10 %). On the post-fume-hood
runs the per-tap signal is below the bench noise, so block E is under-powered
for exactly the research-relevant powders.

**7. Block D's per-revolution normalisation is wrong in the recorded data.**
The firmware's speed loop advances its own clock by the *nominal* poll period
(`waited_ms += speed_poll_ms`) but each iteration also waits for a balance read,
and the auger is in velocity mode for the whole loop. The commanded three
revolutions were therefore **3.44** on runs up to 2026-08-12 and **4.63** from
2026-08-20 on. Total mass and mg/s over the reconstructed window are unaffected;
mg/rev is inflated by 15–54 %. Correcting it moves the block-C-vs-block-D ratio
from 1.22× to **0.84×**, against 0.92× predicted independently by the fitted
speed exponent — two independent measurements that only agree after the fix.
**This is a firmware bug worth fixing before round 2** (measure the elapsed time
rather than counting nominal poll periods, or drive a positioned move).

**8. Powder identity dominates.** A nested decomposition of
log₁₀(mass per revolution) over all resolvable block-C revolutions gives
**70 % powder identity, 20 % tilt, 4 % powder × tilt, 6 % revolution-to-revolution
residual**. Median revolution-to-revolution RSD at the reference condition is
**13.5 %**.

## Caveats carried into every panel

- Feed factor is **collected** mass under this collection geometry, not conveyed
  mass; under-collection is powder-dependent (raised in #116 on 2026-08-21).
- The bench moved into a fume hood on 2026-08-20. Runs after that date have a
  no-actuation baseline of 3–29 mg (`noise_floor_mg` in `rate_summary.csv`)
  against 0.0 mg before, so milligram-scale blocks (B, E) are only resolvable on
  the earlier, quieter runs. Blocks C and D are unaffected — their signals are
  10–300 mg.
- The 2026-08-06 NaCl run is a documented outlier (its block C and block E
  disagree by 2.68× on the same quantity) and is not the representative NaCl run.
- The 2026-08-11 AlSi10Mg run had dead tilt servos (plate stuck at 0°).
- Block E on fumed silica carries a documented solenoid-impulse artifact and is
  never read as a tap quantum.
- No powder in the campaign has independent characterisation — no PSD, no bulk
  or tapped density, no shear cell. Every statement above is instrument-referred.

## What round 2 should change

1. **Fix the block-D duration** (finding 7) so mg/rev is trustworthy without
   post-hoc reconstruction.
2. **Randomise the speed order and tare between speeds**, to break the
   speed/sequence confound.
3. **Get block F running** — the vibration actuator is claimed in the manuscript
   and measured nowhere.
4. **Poll faster during block D**, or run the speed sweep at low RPM only, so
   the crest factor is not aliased above 15 RPM.
5. **Bulk and tapped density on ~10 mL of each powder** — an hour with a
   graduated cylinder converts every panel here from a clustering into a
   calibrated map, and lets Li's conditioned-bulk-density ↔ feed-factor relation
   be tested directly.

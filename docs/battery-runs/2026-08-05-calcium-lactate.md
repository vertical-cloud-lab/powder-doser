# Battery run — calcium lactate, 2026-08-05

Fourth valid-feed run of the uniform powder test battery (issue #116), and the
fast end of the dataset: **232 mg per auger revolution at tilt 90°**, 6× white
rice flour and ~1000× brown rice flour under identical conditions. It is also
the first powder for which the frozen salt-tuned three-phase controller gets
within 3 % of a 1 g target, and the first for which phase 3 (tapping) runs at
all.

| | |
|---|---|
| Run directory | [`data/battery/20260805T200002Z_calcium-lactate/`](../../data/battery/20260805T200002Z_calcium-lactate) |
| MongoDB | `powder_doser.battery_runs`, `_id` `6a739ace81270b29eb5b8915` |
| Powder | calcium lactate (food-safe batch, `batch: food-safe-2026-08`) |
| Loaded by | @swcharles (tape removed, confirmed at the bench) |
| Blocks run | A, B, C, D, E, G (F skipped — vibration motor not attached) |
| Wall clock | 20:00:02 → 20:19:24 UTC (**19 min 22 s**) |
| **QC verdict** | **`ok` — valid for cross-powder comparison** |

## Timing

| Block | Starts (UTC) | Duration |
|---|---|---|
| A baseline | 20:00:04 | 22 s |
| B hold | 20:00:26 | 1 min 01 s |
| C rotation | 20:01:28 | 2 min 13 s |
| D speed | 20:03:41 | 36 s |
| E tap | 20:04:17 | 2 min 43 s |
| F vib | — | skipped |
| G dose | 20:07:00 | 12 min 24 s (265 / 263 / 215 s per dose) |

Half the usual block G, because each dose reaches its stall detector in ~4 min
instead of grinding through a 200-cycle fine-phase budget for ~14 min.

## Pre-flight feed check

Tare, tilt 90°, five 360° revolutions at 30 RPM, then 10 taps:

| | value |
|---|---|
| 5 auger revolutions | 1.2245 g |
| per revolution | 244.2 / 241.4 / 246.9 / 245.1 / 246.9 mg |
| 10 taps | 34.7 mg |
| Verdict | `feed confirmed` |

Note there is **no charging transient** — revolution 1 already delivers the
steady-state mass. White rice flour needed two revolutions to charge the
delivery section (1.7 → 23.3 → 70.2 mg). A free-flowing powder refills the
flights faster than the auger empties them, so the transient disappears.

## Results

### Block A — baseline

8 no-actuation reads, all deltas exactly 0.0000 g. Noise floor is below the
balance's 0.1 mg display resolution, so every number below clears it by at
least an order of magnitude.

### Block B — static hold

15 s at 0°, 45° and 90° with no actuation: **0.0000 g at every tilt.** Despite
being the fastest-conveying powder here, calcium lactate does not avalanche
through a stationary auger even fully vertical. Flow is auger-gated, not
gravity-gated — which is what makes the auger a meter rather than a valve.

### Block C — feed factor vs tilt (6 × 360° at 30 RPM each)

| tilt | mg / revolution | RSD |
|---|---|---|
| 0° | 47.3 | 23 % |
| 45° | 198.3 | **2.2 %** |
| 90° | 232.2 | **2.9 %** |

Two things stand out.

**The spread is the tightest in the dataset by a factor of four.** 2.2 % RSD at
tilt 45°, against 8 % for sodium alginate (the previous best) and 37 % for white
rice flour. Six consecutive revolutions at 45° landed within 11 mg of each
other on a 198 mg mean.

**Repeatability improves as flow increases**, which inverts the trend seen in
white rice flour, where RSD *grew* with the mean (22 → 37 → 45 % across the
three tilts). There is no universal accuracy-vs-throughput tradeoff; there is
one for cohesive powders. Calcium lactate is both the fastest and the most
repeatable powder measured.

The 23 % RSD at tilt 0° is a charging artefact, not scatter: revolution 1
delivered 25.9 mg and revolutions 2–6 delivered 45.0–54.4 mg. Excluding the
first revolution, the horizontal RSD drops to 7 %.

Like sodium alginate, the feed factor **saturates above 45°** (198 → 232 mg/rev,
+17 %), where white rice flour nearly triples over the same span.

### Block D — speed (3 continuous revolutions at tilt 45°)

| auger RPM | mg / 3 rev | mg / revolution |
|---|---|---|
| 15 | 571.3 | **190.4** |
| 45 | 450.5 | **150.2** |
| 90 | 385.6 | **128.5** |

**Mass per revolution falls 33 % as speed rises 6×** — the opposite of every
other powder measured:

| Powder | mg/rev, 15 → 90 RPM | change |
|---|---|---|
| White rice flour | 19.1 → 37.0 | **+94 %** |
| Sodium alginate | 11.1 → 13.0 | +17 % |
| **Calcium lactate** | **190.4 → 128.5** | **−33 %** |

Three distinct regimes, and a clean physical reading of each. A cohesive powder
is *filling-limited by cohesion*: faster rotation fluidises it, the flights pack
more fully, and mass per revolution rises. A free-flowing powder is
*filling-limited by time*: the flights fill under gravity at a finite rate, so
spinning faster gives each flight less time to fill and mass per revolution
falls. Sodium alginate sits between the two and meters almost purely
geometrically.

The practical consequence for control is the useful part. For calcium lactate,
RPM is **not** a clean throughput knob — raising it 6× raises the delivery rate
only ~4× — but low RPM buys *more* mass per revolution, so the highest-precision
operating point and the highest-yield-per-turn operating point coincide at slow
speed. For white rice flour they are opposed.

### Block E — tapping (8 trials each, with a measured 360° re-feed per trial)

| tilt | 360° re-feed rotation | single tap |
|---|---|---|
| 0° | 42.33 mg | 2.31 mg (RSD 14 %) |
| 45° | 165.50 mg | **20.36 mg** (RSD 14 %) |

**This is the first powder in which the solenoid tap does measurable work.**
20.36 mg per tap at tilt 45°, roughly 100× the 0.11 mg (white rice flour) and
0.24 mg (sodium alginate) measured on the same hardware, and with a *tighter*
relative spread (14 % vs >180 %) — the eight individual taps ran 14.9–22.9 mg.

That reframes the "tapping is a dud" conclusion from the three previous runs.
The solenoid was never the problem in isolation: a single 60 ms pulse against
the mount transfers the same energy every time, and whether that dislodges
anything depends on the powder holding at the lip. For cohesive powders it
cannot break internal friction; for a free-flowing powder it shakes loose a
genuine, repeatable quantum. **Tap efficacy is a powder property, not just a
hardware property** — and it is strongly tilt-dependent (9× from 0° to 45°).

### Block G — 3 × 1.000 g closed-loop doses, frozen salt-tuned controller

| dose | delivered | error | status | time | cycles | taps |
|---|---|---|---|---|---|---|
| 1 | 0.9846 g | **−15.4 mg** | `stalled` | 265 s | bulk 13, fine 16, tap 83 | 166 |
| 2 | 0.9654 g | **−34.6 mg** | `stalled` | 263 s | bulk 15, fine 16, tap 82 | 164 |
| 3 | 0.9705 g | **−29.5 mg** | `stalled` | 215 s | bulk 15, fine 16, tap 57 | 114 |

Mean error **−26.5 mg**, roughly **5× better than white rice flour** (−138 mg)
and **11× better than sodium alginate** (−292 mg) under the identical frozen
controller. Still outside the ±5 mg tolerance, so all three are recorded as
failures — but they fail by a different mechanism, and the mechanism is the
interesting part.

The previous three powders exited `cycle-budget`: the bulk phase halted at its
salt-tuned 0.12 g anticipation with far too much left to go, and the fine phase
could not close the gap within 200 cycles. Calcium lactate does not have that
problem — bulk and fine together get to within ~30 mg in about 30 cycles. What
stops it is **phase 3**:

1. Phase 2 *fine* moves 45° increments, which at ~200 mg/rev is **~25 mg per
   increment**. The fine→tap handover fires at 0.050 g to go, so a single
   increment can carry the dose from "above the handover" to ~20–35 mg short —
   overshooting the handover *downward* in one step.
2. Phase 3 *tap* then has to close 20–35 mg by tapping alone at tilt 0°, where
   block E measures 2.3 mg/tap **with a freshly re-fed lip**. During a dose the
   auger has already stopped, so the lip runs dry and the observed rate collapses
   to ~0.1–0.2 mg per cycle.
3. Phase 3's only recovery is a 5° nudge, capped at 10. All three doses spent
   the full nudge budget and then tripped the no-flow stall detector.

So the error is not random: it is approximately one fine increment minus the
tolerance band, and it reproduces to ±10 mg across three doses.

### Controller implications (for #123/#130)

Recorded here rather than acted on, since block G's parameters are frozen by
design:

1. **Scale the fine increment to the measured feed factor.** A fixed 45°
   increment is ~1 mg for brown rice flour and ~25 mg for calcium lactate. To
   land inside ±5 mg the increment should be chosen so one step is smaller than
   the tolerance — here roughly 45° × (5/25) ≈ 9°.
2. **Let phase 3 re-feed properly, or hand back to phase 2.** Tapping against a
   dry lip is near-useless even for a powder with a healthy 20 mg/tap quantum.
   The nudge exists for this, but 10 × 5° = 50° of rotation is less than one
   fine increment.
3. **Tap at 45°, not 0°.** Block E measures 9× more mass per tap at 45° than at
   0° for this powder. Phase 3's choice of tilt 0° is salt-derived.
4. **`stalled` and `cycle-budget` are different failures** and should be
   reported separately: one means the powder stopped moving, the other means the
   controller ran out of patience.

## Cross-powder position

| Powder | mg/rev @ 90° | RSD @ 45° | mg/tap @ 45° | mean dose error |
|---|---|---|---|---|
| **Calcium lactate** | **232.2** | **2.2 %** | **20.36** | **−26.5 mg** |
| White rice flour | 37.2 | 37 % | 0.11 | −138 mg |
| Sodium alginate | 10.9 | 8 % | 0.24 | −292 mg |
| Brown rice flour (auger #2) | ≤ 0.3 | — | 0.16 | −999 mg (stalled) |

The dataset now spans **three orders of magnitude in feed factor** on identical
hardware and identical parameters, which is the span the manuscript (PR #97)
needs to argue that a single frozen parameter set cannot serve all powders.

Calcium lactate corroborates @carl-robison's manual characterisation — *"the
upper boundary for flow velocity, behaving almost like a liquid"* — and refines
it: it is fast, but it is also the *most controllable* powder in the set, not
the least. His observation that "applying mechanical tapping provides virtually
no noticeable increase in dispensing speed" is consistent with block E in
relative terms (a tap is 12 % of a revolution's mass) while the absolute tap
quantum is the largest measured.

## Figures

- [`calcium-lactate_results.png`](../../data/battery/20260805T200002Z_calcium-lactate/calcium-lactate_results.png)
  — four-panel per-powder figure
- [`battery_compare_all.png`](../../data/battery/battery_compare_all.png) —
  cross-powder feed factor (log) and dose outcome

## Notes

- Block F (vibration) skipped: the DRV2605L is still absent/unpowered, and the
  motor is not attached. Needs back-filling for every powder once fixed.
- The rig parked at tilt 0° on completion (`META,park_tilt_deg,0.0` immediately
  before `RUN,END,ok` in the raw serial log).
- `plot_battery_results.py` panel titles are now derived from the data rather
  than hard-coded; the previous fixed titles ("tapping contributes almost
  nothing", "doses run out of fine-phase budget") were both false for this run.

# Xanthan gum — uniform powder battery, 2026-08-06

Sixth valid-feed run of the issue #116 battery. Frozen parameters, no
per-powder tuning (see [the protocol](../powder-battery-protocol.md)).

| | UTC | MDT (lab) |
|---|---|---|
| Pre-flight | 14:01:51 → 14:02:37 | 08:01:51 → 08:02:37 |
| Battery started | 2026-08-06T14:02:54Z | 08:02:54 |
| Battery ended | 2026-08-06T14:19:06Z | 08:19:06 |
| Elapsed | 0:16:12 | |

Run directory: `data/battery/20260806T140254Z_xanthan-gum/`.
MongoDB `powder_doser.battery_runs` `_id` `6a7497dc1144cfd7ea7c11e8`,
`batch: food-safe-2026-08`, `qc.verdict = ok`,
`valid_for_cross_powder_comparison = true`.

Per-block: A 22 s · B 1 m 01 s · C 2 m 13 s · D 33 s · E 2 m 32 s ·
F skipped (motor not attached) · G 9 m 28 s.

## Pre-flight

Tare, tilt 90°, five 360° revolutions at 30 RPM, then 10 taps:

| revolution | delivered (mg) |
|---|---|
| 1 | 125.2 |
| 2 | 152.2 |
| 3 | 160.3 |
| 4 | 266.5 |
| 5 | 149.7 |

**170.8 mg/rev, `feed confirmed`** on the first check — no escalation
needed, and no charging transient worth speaking of (revolution 1 is
already within ~25 % of steady state). 10 taps added 92.2 mg, which was
the first sign that the solenoid would do real work on this powder.

## Results

### Block A — baseline

Eight no-actuation reads, all exactly 0.0000 g. Noise floor below the
balance's 0.1 mg display resolution.

### Block B — static hold

No spontaneous discharge at 0°, 45° or 90° over 15 s. Sixth powder in a
row: nothing in this set avalanches through a stationary auger, even
fully vertical. Flow is auger-gated, not gravity-gated.

### Block C — feed factor vs tilt (6 × 360° at 30 RPM each)

| tilt | mg / revolution | RSD |
|---|---|---|
| 0° | 23.7 | 20.6 % |
| 45° | 161.2 | 12.1 % |
| 90° | **186.8** | **4.0 %** |

Monotonic in tilt, saturating above 45° (+16 % from 45° to 90°), and
**4.0 % RSD at 90° is the second-tightest spread in the dataset**, behind
only calcium lactate's 2.2 %.

Revolution by revolution (`xanthan-gum_sequence.png`), all three tilts
classify as **steady** — the first run in the set where none of the three
is charging, decaying or intermittent:

| tilt | revolutions 1–6 (mg) |
|---|---|
| 0° | 15.3, 20.3, 27.6, 26.0, 26.9, 26.2 |
| 45° | 199.5, 151.5, 163.0, 151.1, 148.0, 154.0 |
| 90° | 200.7, 180.6, 184.7, 183.5, 182.2, 188.9 |

The one mild transient is at 0°, where the first two revolutions run
below the last four — the horizontal column taking a turn or two to
settle into the flights.

### Block D — speed (3 continuous revolutions, tilt 45°)

| auger RPM | mg / 3 rev | mg / revolution |
|---|---|---|
| 15 | 700.0 | **233.3** |
| 45 | 374.0 | 124.7 |
| 90 | 317.6 | **105.9** |

**Mass per revolution falls 55 % across a 6× speed change** — the
strongest negative speed dependence measured so far, steeper than calcium
lactate's −33 %. Block C's 161 mg/rev at 30 RPM sits between the 15 and
45 RPM points, so the trend is consistent across two blocks measured
minutes apart.

This is the free-flowing/filling-limited-by-time regime taken to its
extreme: flights fill under gravity at a finite rate, so a faster screw
gives each flight less time to fill. Practical consequence — 6× the RPM
buys only ~2.7× the throughput, and the highest mass per turn coincides
with the slowest rotation.

### Block E — tapping (8 trials per tilt, each with a measured 360° re-feed)

| tilt | 360° re-feed rotation | single tap |
|---|---|---|
| 0° | 19.98 mg (RSD 4.6 %) | 0.15 mg (RSD 205 %) |
| 45° | 136.35 mg (RSD 4.8 %) | **13.61 mg (RSD 25 %)** |

**Second powder where the solenoid moves real mass** (calcium lactate was
the first, at 20.36 mg/tap). Individual taps at 45° ran 9.0–17.8 mg.
The tilt dependence is ~90×, even steeper than calcium lactate's 9×:
tapping at 0° is indistinguishable from zero, tapping at 45° is a usable
fine-actuator quantum.

Across the six powders, tap efficacy tracks feed factor rather than
tracking anything about the solenoid — the two powders with the highest
mg/rev are the two where tapping works:

| Powder | mg/rev @ 45° | mg/tap @ 45° |
|---|---|---|
| Calcium lactate | 198.3 | 20.36 |
| **Xanthan gum** | **161.2** | **13.61** |
| Carboxymethyl cellulose | 26.3 | 0.15 |
| White rice flour | 12.8 | 0.11 |
| Sodium alginate | 9.6 | 0.24 |
| Brown rice flour | 0.25 | 0.16 |

A tap dislodges whatever is sitting loose at the delivery lip; how much
that is scales with how much the auger has just conveyed there. Above
~100 mg/rev the tap is a real actuator, below ~30 mg/rev it is noise.

### Block F — vibration

Skipped; the DRV2605L motor is not attached. Sixth valid run missing
block F. Still needs back-filling.

### Block G — 3 × 1.000 g closed-loop doses (frozen salt-tuned controller)

| dose | delivered | error | status | time | cycles | taps |
|---|---|---|---|---|---|---|
| 1 | 0.9564 g | −43.6 mg | `stalled` | 174 s | bulk 16, fine 16, tap 38 | 76 |
| 2 | 0.9699 g | −30.1 mg | `stalled` | 199 s | bulk 18, fine 18, tap 45 | 90 |
| 3 | 0.9750 g | −25.0 mg | `stalled` | 193 s | bulk 18, fine 18, tap 43 | 86 |

Mean error **−32.9 mg**, second best of the six powders behind calcium
lactate (−26.5 mg). Errors improve monotonically across the three doses,
as they did for carboxymethyl cellulose.

The failure mode is the calcium lactate one, not the white-rice-flour
one. Bulk and fine both converge quickly — 16–18 cycles each, against
200 for the powders that exhaust the fine budget — and all three doses
reach **phase 3**, then die there:

1. A 45° fine increment moves ~20 mg at this feed factor, so the fine
   phase steps past the 50 mg-to-go handover in two or three moves and
   hands roughly 25–45 mg to phase 3.
2. Phase 3 taps at **tilt 0°**, where block E measures 0.15 mg/tap — a
   ~90× penalty against the same tap at 45°. 76–90 taps therefore
   recover ~10 mg, not the required 25–45 mg.
3. The 5° re-feed nudges (max 10) run out and the no-flow stall detector
   trips.

So the residual is essentially the handover threshold minus what phase 3
can claw back at the wrong tilt.

## Where this leaves the controller work (#123/#130)

Xanthan gum sharpens two implications already raised by calcium lactate
and carboxymethyl cellulose, and adds one:

1. **Phase 3 should not tap at 0°.** Third powder in a row where the
   dose reaches phase 3 and stalls there, and the second where the same
   tap at 45° would have moved 90× more mass. This is now the dominant
   failure mode for well-conveying powders.
2. **The fine increment must scale with the measured feed factor.** 45°
   at 161 mg/rev is a ~20 mg step against a ±5 mg tolerance, so the fine
   phase cannot land inside the band regardless of budget. Roughly 11°
   would be the equivalent step here.
3. **The bulk anticipation should be measured, not frozen.** Bulk
   converged in 16–18 cycles here where sodium alginate needed 103–114,
   because the salt-tuned 0.12 g anticipation happens to suit a fast
   powder. Nothing about that is a property of the controller.

## On the manual observations

@carl-robison's hand test described xanthan gum as flowing best at a
steady 45°, with *"a purely vertical orientation resulting in an initial
large burst followed by an immediate clog"*, and flat orientation giving
*"decent volumetric control"*, with *"active mechanical tapping essential
to keep the gum moving."*

The tapping half is confirmed and quantified: 13.61 mg/tap at 45° is the
second-largest tap quantum in the set, and the only other powder with a
usable one is calcium lactate.

The tilt half is not. On the rig, **90° is both the fastest and by far
the most repeatable setting** (186.8 mg/rev at 4.0 % RSD), steady across
all six revolutions with no burst-then-clog signature anywhere in the
trace, and 0° is the *worst* of the three at 23.7 mg/rev and 21 % RSD.

Both observations are probably right about different machines. A hand
test measures gravity-driven flowability: a vertical column of a cohesive
gum arches, and nothing in the operator's hands breaks that arch except
shaking. The rig's auger rotates continuously through the intake, so it
mechanically breaks arches as they form — which is exactly the case where
a powder's gravity flowability stops predicting its conveyed flow rate.

That is worth stating in the manuscript (#97) as the reason powered
conveying is characterised separately from flowability: for xanthan gum
the hand test and the auger disagree about the *best* operating tilt, not
just about the magnitude. Note that carboxymethyl cellulose disagreed in
the opposite direction on the same axis — manually preferring vertical,
measuring 2.8× worse at vertical than at 45° — so the disagreement is not
a consistent offset that could be corrected for.

## Cross-powder position

| Powder | mg/rev @ 45° | mg/rev @ 90° | best RSD | mg/tap @ 45° | mean dose error |
|---|---|---|---|---|---|
| Calcium lactate | 198.3 | 232.2 | 2.2 % | 20.36 | −26.5 mg |
| **Xanthan gum** | **161.2** | **186.8** | **4.0 %** | **13.61** | **−32.9 mg** |
| White rice flour | 12.8 | 37.2 | 22 % | 0.11 | −138 mg |
| Carboxymethyl cellulose | 26.3 | 9.3 | 9.1 % | 0.15 | −43.2 mg |
| Sodium alginate | 9.6 | 10.9 | 8 % | 0.24 | −292 mg |
| Brown rice flour (auger #2) | 0.25 | 0.20 | — | 0.16 | stalled |

Xanthan gum is the second-fastest and second-most-repeatable powder, and
second best under the frozen controller — a clean second data point for
the "well-conveying powders fail in phase 3" cluster that previously
rested on calcium lactate alone.

## Consumption

Roughly 6 g. Block C alone is 18 revolutions at up to 187 mg, and the
three doses are ~2.9 g. Fast powders cost about 2× the original 4 g
estimate.

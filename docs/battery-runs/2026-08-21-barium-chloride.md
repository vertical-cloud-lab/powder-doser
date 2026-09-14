# Barium chloride — uniform powder battery, 2026-08-21

| | |
|---|---|
| Run id | `20260821T170712Z_barium-chloride` |
| Started | 2026-08-21 17:07:12 UTC / 11:07:12 MDT |
| Ended | 2026-08-21 17:20:21 UTC / 11:20:21 MDT |
| Elapsed | 0:13:09 |
| Blocks | A, B, C, D, E (F skipped — DRV2605L not on the I²C bus; G not requested) |
| Batch | `inorganic-2026-08` |
| Operator | swc (loaded the auger, removed the delivery-end tape) |
| Mongo `_id` | `6a888958f7f79cac25b6cff6` |
| QC | `valid_for_cross_powder_comparison = true`, `verdict = ok` |
| Measured mass | 5.62 g over 64 trials |

Per block: A 49 s · B 1 m 41 s · C 4 m 02 s · D 1 m 01 s · E 5 m 31 s.

## The measurement environment was the best of the whole dataset

This is the first run since the move into the fume hood whose noise
floor matches the pre-move runs, and by some margin the quietest
measurement conditions any powder has been measured in.

| | pre-run survey | during the run |
|---|---|---|
| sample-to-sample jitter | **0.005 mg** | — |
| stable frames | **837 / 837 (100 %)** | — |
| mechanical steps > 10 mg in 240 s | **0** | — |
| drift over the longest quiet stretch | +0.8 mg/min | — |
| environmental error over 180 s | **2.5 mg** (inside the ±5 mg dose band) | — |
| block A no-actuation deltas | — | **8 × exactly 0.0000 g** |
| max per-trial σ, all 64 trials | — | **0.2 mg** |
| shock events / retries / disturbed trials | — | **0 / 0 / 0** |

For comparison the AlSi10Mg pre-run survey four hours earlier read
1.50 mg jitter with 4 % of frames stable — a factor of ~300 in jitter.
Nothing about the rig changed in between; see
`docs/rig-checks/2026-08-21-bench-activity-and-quiet-bench.md`.

Two consequences worth stating, because they are the first time either
has been true since the move:

* **Block B independently establishes the no-avalanche result.** All
  three 15 s holds read *exactly* 0.0000 g against a 0.0 mg baseline
  floor, rather than sitting inside a ±20–90 mg block A spread. Eleven
  powders now, and none discharges through a stationary auger even
  fully vertical: flow is auger-gated, not gravity-gated.
* **Block G is unblocked by the environment.** The 180 s row of the
  survey is 2.5 mg against a ±5 mg tolerance. It was 18.3 mg before the
  sodium sulfate run and 33.3 mg on 2026-08-20. Block G was not run here
  (this battery was requested as the standard `ABCDE`), but for the
  first time the gate would have passed.

## Results

### Block C — feed factor vs tilt

| tilt | mean mg/rev | RSD | revolutions 1–6 (mg) | sequence |
|---|---|---|---|---|
| 0° | 23.3 | 47 % | 9.9, 9.8, 23.8, 30.1, 32.9, 33.2 | **charging** |
| 45° | 184.7 | 17 % | 143.1, 157.3, 184.2, 214.6, 183.7, 225.3 | **charging** |
| 90° | 200.4 | 38 % | 319.0, 275.1, 160.7, 163.1, 137.5, 146.9 | **decaying** |

None of these three is six draws from one distribution, so the means
are not feed factors. Block C runs 0° → 45° → 90° in fixed order and
the column state changes underneath it: the pre-flight ramp
(0.7, 49.8, 117.8, 59.1, 36.0 mg) shows the delivery section was still
filling when block C started, and by 90° the first revolution discharges
what accumulated (319 mg) before settling to ~140–165 mg/rev.

**Block E is the better estimate at 0° and 45°.** Its re-feed rotations
are the same action — one 360° revolution at 30 RPM at the same tilt —
measured 5–10 minutes later with the column at steady state:

| tilt | block E re-feed | RSD | block C mean | E / C |
|---|---|---|---|---|
| 0° | **37.4 mg/rev** | 6.2 % | 23.3 | 1.61 |
| 45° | **190.8 mg/rev** | 6.1 % | 184.7 | **1.03** |

1.03 at 45° is the tightest block C / block E agreement in the dataset
(the band across all runs is 0.74–1.12; the 2026-08-06 salt run failed
this check at 2.68 and was recorded as a lower bound). The 1.61 at 0°
is the charging transient, not disagreement — drop block C's first two
revolutions at 0° and the mean rises from 23.3 to 30.0.

So the steady-state numbers for the cross-powder table are **37.4 mg/rev
at 0°** and **190.8 mg/rev at 45°**, with **90° reported as a decaying
sequence rather than a mean**.

### Block D — per-speed split unusable for this powder

| auger RPM | delta | mg/rev |
|---|---|---|
| 15 | 783.0 mg | **261.0** |
| 45 | 135.3 mg | 45.1 |
| 90 | 408.5 mg | 136.2 |

Non-monotonic, and 45.1 mg/rev is a quarter of what the same tilt
delivers in blocks C and E minutes either side, so this is not a speed
law and should not be quoted as one.

The poll trace says the screw was turning and nothing was coming out.
Block D polls the balance continuously, and at 45 RPM the delivered mass
climbs to ~120 mg in the first 1.5 s and then sits flat for the rest of
the 4 s burst — revolutions 2 and 3 delivered essentially nothing. The
15 RPM trial immediately before it had just drawn 783 mg in 12 s, the
largest single draw anywhere in this run.

Two candidate mechanisms, and this run cannot separate them:

* **depletion and recharge.** The 15 RPM trial emptied the charged
  delivery section faster than the column refilled it, so the 45 RPM
  trial ran on a depleted outlet and the 90 RPM trial ran after it had
  partly recovered (408.5 mg). Block C at 90° decaying 319 → 147 mg/rev
  is the same story earlier in the run.
* **trial-boundary leakage.** Block D is tared once at the start and not
  between speeds, so mass still in flight when a trial's bracket closes
  is collected by the next one. That is safe while a trial's mass lands
  inside its own settle window and stops being safe when three
  revolutions take 4 s or 2 s.

Either way the split is unusable here. The 15 RPM point (261.0 mg/rev),
which starts from the tare and runs long enough to settle, is the one
usable value. Every earlier fast powder produced a monotonic block D, so
this is a marginal case rather than a broken block — but it is worth
re-taring between speeds, or randomising the speed order, before block D
is trusted on a powder that conveys ~200 mg/rev.

### Block E — the tap quantum, resolved

| tilt | 360° re-feed | single tap | tap RSD | individual taps (mg) |
|---|---|---|---|---|
| 0° | 37.4 mg | **0.06 mg** | — | +0.2, 0.0, −0.1, −0.1, +0.2, +0.1, +0.1, +0.1 |
| 45° | 190.8 mg | **2.13 mg** | 49 % | +2.0, +2.5, +1.9, +1.5, +1.9, +1.5, +4.5, +1.2 |

This is the first resolved tap quantum in four runs. All eight taps at
45° are positive with a minimum of 1.2 mg, against a block A floor of
exactly 0.0 mg — so 2.13 mg (median 1.9) is a measurement, not a
coin-flip. At 0° the eight taps span two display counts either side of
zero, which is a genuine upper bound of **< 0.2 mg/tap**, not "not
resolved". Tilt dependence is ~35×, between calcium lactate's 9× and
xanthan gum's 90×.

## The "tap efficacy tracks feed factor" pattern is refuted

Three runs (calcium lactate, xanthan gum, then a string of unresolved
ones) had suggested that a tap only does useful work above roughly
100 mg/rev, and that its quantum scales with the feed factor. Barium
chloride is the controlled test, because its feed factor lands almost
exactly on calcium lactate's:

| powder | mg/rev @ 45° | mg/tap @ 45° | ratio |
|---|---|---|---|
| calcium lactate | 198.3 | **20.36** | 10.3 % |
| **barium chloride** | **190.8** | **2.13** | **1.1 %** |
| xanthan gum | 161.2 | 13.61 | 8.4 % |
| salt (08-12) | 175.3 | 0.91 | 0.5 % |

**At matched feed factor the tap quantum differs by 10×.** Feed factor
is therefore not what sets tap efficacy, and the ~100 mg/rev threshold
proposed on 2026-08-06 should be dropped. It also removes the
environmental excuse: the three unresolved runs were unresolved because
the bench was noisy, but this one was measured at a 0.0 mg floor and the
answer is simply that the tap is small for this powder.

What the four high-feed powders do split on is composition — the two
organics (calcium lactate, xanthan gum) tap at 8–10 % of a revolution
and the two inorganic salts (barium chloride, NaCl) at 0.5–1 %. With
n = 4 that is a hypothesis to test, not a finding; the obvious next test
is sodium sulfate's and silicon's tap quanta, both of which were
measured on a noisy bench and are now cheap to re-measure (block E alone
is ~5 minutes) on a quiet one.

## Blocks A and B

* **A** — 8 no-actuation reads, every one exactly 0.0000 g.
* **B** — 15 s static holds at 0°, 45°, 90°: exactly 0.0000 g at all three.

## What this cost

5.62 g of barium chloride over 64 trials, with **zero retries** — so
none of it went into discarded measurements. The AlSi10Mg run four hours
earlier spent 6.45 g (43 % of the powder it drew) re-measuring trials
the room had disturbed. A quiet bench is a material saving on a fast
powder, not only a data-quality one.

## Safety note

Barium chloride is the first acutely toxic powder in this series
(soluble barium salt; toxic by ingestion and inhalation), as distinct
from the food-safe set and from the metal powders whose hazard is dust
and combustibility. The beaker contents and any spill are toxic waste:
collect rather than brush out, damp-wipe the plate and enclosure rather
than dry-sweeping, and dispose through the hazardous stream in a sealed
vessel.

## Standing items

* **Block F (vibration) is missing from every run** — the DRV2605L is
  absent from the I²C bus, so it is not wired in rather than failing.
* **Block G** is no longer blocked by the environment (see above) but
  has not been run since the move.
* A **100 g class E2/F1 weight** is still not at the rig, so the
  HR-100A has not been calibrated since the move into the fume hood.

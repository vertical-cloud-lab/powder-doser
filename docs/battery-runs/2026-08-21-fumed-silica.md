# Fumed silica — 2026-08-21 (issue #116)

**Run**: `data/battery/20260821T182705Z_fumed-silica/` ·
`powder_doser.battery_runs` `_id 6a889c1c24b506a3f973c0f7` ·
batch `inorganic-2026-08` · blocks A–E (F skipped, G not requested).

**18:27:05 → 18:42:35 UTC (12:27:05 → 12:42:35 MDT), 15 min 29 s,
`RUN,END,ok`**, tilt parked at 0°.

**QC: excluded from cross-powder comparison**,
`qc.verdict = no-conveyance-outlet-unverified`. Two independent reasons,
both recorded as a dated amendment on the run document:

1. the delivery end could not be visually confirmed — the improvised
   draft cage installed before this run blocks the bench camera, so a
   genuinely non-conveying powder and a taped/capped outlet are
   indistinguishable here;
2. the block E tilt 0° tap quantum is an instrumentation artifact (below).

## Headline

**Conveyance is at or below 0.25 mg per 360° revolution** — at or below
brown rice flour, the previous floor of the dataset, and roughly
**1400× below AlSi10Mg** measured on the same rig three hours earlier.

That number comes from a purpose-built long-integration test, not from
block C, because block C cannot resolve it (see below).

## Why the standard checks could not answer this

Both gates fired and neither was informative:

| check | result |
|---|---|
| `battery_preflight`, 5 rev @ tilt 90° | `empty-or-blocked`, **−9.2 mg/rev** (negative) |
| `battery_feed_diagnostic`, 45 rev + 60 taps | `mechanical-no-feed`; rotation −66.7 mg, taps +39.9 mg |

Both modules threshold a *few tens of revolutions* against a balance
whose unbracketed noise floor in this room is ±35 mg. That is fine for
every powder measured so far, whose feed factors run 10–340 mg/rev. It
is useless here, and the arithmetic says so in advance:

- salt delivers ~230 mg/rev at tilt 90° at a bulk density of ~1.2 g/cm³,
  so this auger moves roughly **0.19 cm³ per revolution**;
- fumed silica's bulk density is **~0.03–0.06 g/cm³**;
- so a fumed-silica feed that filled the flights *as well as salt does*
  would be **≈7 mg/rev**, and realistically — this being the most
  cohesive powder in the set — **1–3 mg/rev**.

A healthy column and a blocked one therefore produce the same reading
over 45 revolutions. **`mechanical-no-feed` is not a verdict about this
powder**; it is the module reporting that the question was out of range.

## The long-integration test

Beat the noise floor with revolutions instead of precision. All at tilt
90°, 90 RPM, via `battery_feed_diagnostic` with its stage constants
raised:

| stage | revolutions | delta | mg/rev |
|---|---|---|---|
| long | 150 | −29.9 mg | −0.199 |
| fast | 150 | +38.8 mg | +0.259 |
| 30 taps | — | −8.4 mg | — |
| post-agitation | 50 | −8.3 mg | −0.166 |
| **total** | **350** | **+0.6 mg** | **+0.0017** |

The three rotation stages scatter about zero with inconsistent sign, so
the mean is not a small feed rate — it is zero to within ±0.25 mg/rev.
At 2 mg/rev, 350 revolutions would have delivered 700 mg and been
unmissable.

Agitation does not unlock it either: 30 taps followed by 50 more
revolutions conveyed nothing, so this is not arching that collapses under
vibration.

## Block C could not resolve it

| tilt | mg/rev | sd | **SEM** | revolutions (mg) |
|---|---|---|---|---|
| 0° | 2.52 | 14.07 | **5.74** | −7.0, 28.3, 0.3, −12.6, 3.4, 2.7 |
| 45° | 2.72 | 14.25 | **5.82** | 10.9, 16.1, −15.5, 18.6, −7.2, −6.6 |
| 90° | 5.57 | 9.96 | **4.07** | 13.5, 17.2, −5.1, −5.8, 11.9, 1.7 |

Every mean is inside one standard error of zero, and each tilt contains
negative revolutions. Block A — eight trials with **no actuation at all**
— scattered −6.1 to +4.4 mg (sd 3.86, 10.5 mg peak-to-peak). Six
revolutions cannot see a sub-mg signal through that; 350 can.

Block B holds read +7.9 / −19.1 / +1.5 mg at 0 / 45 / 90°: inside the
block A spread, signs physically inconsistent (horizontal is the least
favourable orientation and read positive). Consistent with the eleven
previous powders — nothing in this dataset avalanches through a
stationary auger — but this run does not independently establish it.

Block D read −21.1 / −6.7 / +26.3 mg over 3 revolutions at 15 / 45 /
90 RPM. Not a speed dependence; noise.

## The block E tilt 0° tap is the solenoid, not powder

| tilt | 360° re-feed | single tap | tap sd | trials flagged `shock` |
|---|---|---|---|---|
| 0° | **−8.86 mg** | **+32.18 mg** | 6.22 | **8 / 8** |
| 45° | +12.7 mg | +1.9 mg | 2.2 | 0 / 8 |

All eight taps at 0° landed between +21.6 and +42.0 mg, each needing two
retries, each flagged `shock`, each carrying a −18 to −40 mg shock
correction that a comparable positive residue survived.

It cannot be powder:

1. **A tap cannot deliver more than rotation brings to the lip.** The
   re-feed rotation in the same trials, at the same tilt, was *negative*.
2. **The tilt dependence runs backwards.** Every powder with a real tap
   quantum is far more responsive at 45° than at 0° (calcium lactate
   2.3 → 20.4 mg, xanthan gum 0.15 → 13.6 mg). Here 0° is 17× *larger*
   than 45°, and only 0° trips the shock detector.
3. **It is new.** Same rig, same solenoid, block E tilt 0° tap mean:

   | run | 0° tap mean | sd | shock flags |
   |---|---|---|---|
   | silicon -325, 2026-08-21 16:18 | −0.04 mg | 0.18 | 0 |
   | barium chloride, 2026-08-21 17:07 | +0.06 mg | 0.12 | 0 |
   | **fumed silica, 2026-08-21 18:27** | **+32.18 mg** | 6.22 | **8** |

   A 500× jump inside 70 minutes, on a bench that measured 0.005 mg
   jitter for the barium chloride run. The draft cage was installed in
   exactly that window.

Read as the tap solenoid's mechanical impulse coupling into the load
cell through a path that did not exist this morning. At tilt 0° the
mounting plate is flat against the deck — the stiffest coupling
geometry — which is why 45° is unaffected. **This is only visible
because the powder signal is zero**; on a powder delivering 200 mg/rev
it would have been a 15 % error nobody would have caught.

Worth a bench check: does the cage rest on, or touch, the balance, the
breeze break or the doser platform?

## Environment

Pre-run survey (240 s, read-only,
[CSV](../rig-checks/data/2026-08-21_fumed-silica-preroll-survey-240s.csv)):
jitter **0.281 mg**, 43 % of frames stable, drift −1.9 mg/min,
**0 mechanical step events > 10 mg**. The survey's own verdict was
"even short trials are being disturbed", but with zero shocks and low
creep the disturbance is *continuous*, which is the kind bracket
averaging removes — the same call made for the silicon and AlSi10Mg runs.

An hour earlier, before the cage went on, the barium chloride survey read
**0.005 mg jitter with 100 % of frames stable**. So the bench is ~50×
noisier than it was pre-cage. Confounded by the operator having just been
at the bench, but it belongs next to the tap finding above rather than
being quietly averaged away.

During the run: median per-trial σ **4.1 mg**, 9 shock events, 16 retries
(all of them block E tilt 0° taps), 24 / 64 clean trials.

## Balance

The balance was sitting at **−4.2 g**, a stale mid-run tare from the
barium chloride run whose beaker has since been emptied. `scripts/balance_zero.py`
reported sending A&D `Z` and then warned about the very offset it had
failed to clear: `Z` is the RE-ZERO key and is **range-limited** to a few
percent of capacity, and this unit has `erCd = 0` so a refusal is silent.
The script now detects the refusal and falls back to `T` (tare, full
range). Harmless for the data — every battery measurement is a difference
between two bracket fits, so a stale zero cancels exactly — but it was
misreporting what it had done.

`META,tare,skipped-unstable` / `refused` appears throughout this run's log
for the same reason; that is the intended best-effort behaviour.

## What would settle it

One bench check, ~2 minutes:

1. **Look at the delivery end.** If it is open, this run's ≤0.25 mg/rev
   is a real, publishable measurement — the powder this geometry cannot
   convey — and it can be promoted to
   `valid_for_cross_powder_comparison = true`, exactly as brown rice
   flour auger #2 was on 2026-08-05.
2. **Check what the draft cage touches.** Nothing rigid may bridge the
   fixed frame to the balance or its enclosure.
3. Restoring a camera sightline (a clear window on the camera side of
   the box, or moving the camera inside the sash) removes the need to ask
   at all — it is the check that resolved the taped CMC outlet, the caught
   tap collar and the stuck servo plate.

Either answer is publishable. Fumed silica is a *useful* extreme: at
~0.04 g/cm³ and maximal cohesion it is the physical floor of what a
screw feeder of this geometry can meter, and the dataset would then span
**AlSi10Mg 338.9 mg/rev → fumed silica ≤0.25 mg/rev**, more than three
orders of magnitude on one auger with one frozen parameter set.

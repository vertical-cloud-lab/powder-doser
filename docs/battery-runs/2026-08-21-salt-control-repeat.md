# Salt — 2026-08-21, control repeat (issue #116)

**Run**: `data/battery/20260821T192031Z_salt/` ·
`powder_doser.battery_runs` `_id 6a88a992a74cd6a9af55a28d` ·
batch `food-safe-2026-08` · blocks A–E (F skipped, G not requested).

**19:20:31 → 19:35:03 UTC (13:20:31 → 13:35:03 MDT), 14 min 32 s,
`RUN,END,ok`**, tilt parked at 0°.

**QC: valid for cross-powder comparison**, `qc.verdict = ok`, with two
caveats recorded on the run document rather than folded into the means
(tap quantum not resolved; block B does not independently establish the
absence of gravity discharge).

Per block: A 45 s · B 1 m 29 s · C 4 m 00 s · D 56 s · E 7 m 16 s.
About **6.3 g** of salt through the auger.

## Why this run

Two jobs, neither of them "another salt repeat":

1. **Re-establish the control on a quiet bench.** The three salt runs
   before this one were each compromised in a different way — 2026-08-06
   by an under-filled auger (blocks C and E disagreed 2.68×, so its block
   C is recorded as a lower bound), 2026-08-20 by a room throwing a shock
   every ~40 s (`environment-stress-test`, truncated). Only 2026-08-12 was
   clean, and it predates the move into the fume hood.
2. **Restore the visual outlet check.** The fumed-silica run 53 minutes
   earlier was excluded as `no-conveyance-outlet-unverified` because the
   improvised draft cage blocked the bench camera, making a genuinely
   non-conveying powder indistinguishable from a taped outlet.

## Pre-run state

| check | result |
|---|---|
| Pico firmware | all five battery modules byte-identical to the repo |
| balance | re-zeroed remotely from a stale −4.35 g reference |
| jitter | **0.066–0.117 mg** — at the balance's 0.1 mg display resolution |
| stable frames | 57–77 % |
| mechanical shocks in 240 s | **0** |
| baseline creep | **−14.2 mg/min** |
| survey verdict | short-trial blocks A–F safe to run |
| bench camera | delivery end plainly open — no tape, no cap |
| pre-flight | **`feed confirmed`, 242.2 mg/rev** |

The camera view is clear again, so the check that could not be made for
fumed silica is available once more. Note what that does and does not
establish: each powder has its **own auger**, and the tape or cap lives on
the auger, so salt conveying does not retroactively clear the fumed-silica
auger. What it establishes is that the *check* works again, and that the
fixed part of the delivery path — outlet position, beaker, geometry — is
sound.

Pre-flight revolutions: **296.2, 223.0, 232.0, 236.2, 223.7 mg**, then 10
taps → 77.9 mg. **No charging transient**: revolution 1 is already at
steady state. Worth contrasting with silicon (3 revolutions in the noise,
then charge) and CMC (~30 revolutions) — the pre-flight average is a
go/no-go on the delivery path, not a feed factor, and how badly it
understates depends on how fast the column charges rather than on
cohesion.

## Block C — feed factor vs tilt

Six 360° revolutions at 30 RPM per tilt.

| tilt | mg / revolution | RSD | median trial σ | revolutions 1–6 (mg) |
|---|---|---|---|---|
| 0° | 38.0 | 27.3 % | 1.5 mg | 22.6, 38.0, 45.0, 41.7, 29.7, 51.0 |
| 45° | 146.5 | 18.3 % | 8.0 mg | 136.0, 167.3, 158.5, 138.6, 176.3, 102.2 |
| 90° | 265.2 | 12.4 % | 7.5 mg | 279.6, 227.3, 273.0, 287.0, 221.9, 302.2 |

Monotonic in tilt, **+81 % from 45° to 90°** — this run does *not*
saturate above 45°, where 2026-08-12 gained +31 % and 2026-08-20 +34 %
over the same span. With n=3 comparable runs that is inside the
between-run spread rather than a new finding; see below.

Internal consistency: block E's re-feed rotations at tilt 45°, measured
about five minutes later at the same RPM, give **155.4 mg/rev**, so
E/C = **1.06** — inside the 0.74–1.12 band every well-behaved run in the
dataset sits in, and a long way from 2026-08-06's 2.68.

## Block D — speed

Three continuous revolutions at tilt 45°.

| auger RPM | mg / 3 rev | mg / revolution |
|---|---|---|
| 15 | 740.1 | **246.7** |
| 45 | 656.0 | 218.7 |
| 90 | 492.8 | **164.3** |

**−33 % across a 6× speed change** — filling-limited by time, the same
family as calcium lactate (−33 %), sodium sulfate (−48 %), AlSi10Mg
(−49 %) and xanthan gum (−55 %), and reproducing 2026-08-12's −47 % in
sign and rough magnitude.

The 15 RPM trace is again the cleanest pulsation record available:
discrete slugs, one per revolution, with flat plateaus between them.

One consistent offset worth stating rather than smoothing: block D at
45 RPM (218.7 mg/rev) sits **above** block C at 30 RPM (146.5 mg/rev) at
the same tilt, so the two blocks do not lie on one curve. The same gap
appears in the 2026-08-12 run (block D 45 RPM 192 vs block C 175). Block C
steps 360° at a time from rest while block D rotates continuously, so the
stepped protocol appears to cost mass per revolution. Testing that needs a
continuous-vs-stepped comparison at matched RPM, which the battery does not
currently run.

## Block E — the tap quantum is not resolved, and the figure title was wrong

| tilt | 360° re-feed | single tap | individual taps (mg) |
|---|---|---|---|
| 0° | 40.3 mg | **+8.97 mg** (RSD 125 %) | +8.9, +7.1, +2.2, +2.3, +2.2, +27.2, −3.2, +25.1 |
| 45° | 155.4 mg (RSD 15 %) | **−4.10 mg** (RSD 261 %) | +8.1, −1.7, −19.3, +3.1, −15.9, −14.3, +3.6, +3.6 |

The +8.97 mg at tilt 0° clears both of the resolution tests the figure
titles have used since 2026-08-20: it is above block A's 2.88 mg standard
deviation and above twice its own 3.96 mg standard error. It is still not
a tap quantum, for a reason neither test could see:

**the tap goes negative exactly where conveyance is strongest.** The
re-feed rotation nearly quadruples from 0° to 45° (40.3 → 155.4 mg) while
the tap mean falls from +9.0 to −4.1 mg. A tap can only dislodge what
rotation has already carried to the delivery lip, and gravity assists both,
so in every run where a quantum did resolve it was *largest* at the
best-fed tilt — calcium lactate 2.3 → 20.4 mg/tap, xanthan gum
0.2 → 13.6 mg/tap. An inversion is not a powder property.

`tap_headline` in `scripts/plot_battery_results.py` took `max()` over
tilts, so it reported "tapping moves up to 9 mg per tap". It now evaluates
the claim **at the tilt whose re-feed rotation is largest**: if the tap
does nothing measurable there, a bigger number at a worse-fed tilt is the
room. Swept over all 19 committed runs, no earlier title changes.

The pre-flight's 10 taps at tilt 90° delivered **77.9 mg (7.8 mg/tap)**
after five revolutions had heavily charged the lip. That is a single
aggregate rather than eight bracketed trials and is not comparable to the
block E protocol, but it is the only positive, coherent tap number this run
produced, and it suggests the block E result is about lip charge rather
than about salt.

Salt's resolved tap quantum therefore remains **0.91 mg/tap at 45°**, from
2026-08-12.

## Blocks A and B

**A** — eight no-actuation reads: −1.7, +6.8, +2.3, −2.6, +0.7, +2.8,
+1.1, +1.1 mg. Spread **9.4 mg**, sd **2.88 mg**. That is the tightest
no-actuation baseline since the move into the fume hood (AlSi10Mg 88 mg,
sodium sulfate 22.7 mg, silicon 20.2 mg) though still well above the
0.0000 g every pre-move run returned.

**B** — 15 s static holds: +41.9 mg at 0°, −13.4 mg at 45°, +3.3 mg at
90°. The 0° reading carries a per-trial **σ of 39.7 mg** and a −41.7 mg
drift correction, and the 45° trial is flagged `shock`. All three are
consistent with no discharge — and the signs are physically inconsistent
with a real one, since horizontal is the least favourable orientation and
read most positive — but this run does not independently establish it.
A hold is the one measurement the actuator gate cannot help, because there
is no action to bracket against.

## Environment

| | this run | AlSi10Mg (4 h) | silicon (1 d) | sodium sulfate (1 d) |
|---|---|---|---|---|
| median per-trial σ | **2.8 mg** | 10.4 mg | 7.9 mg | 5.9 mg |
| clean trials | **29 / 64** | 1 / 64 | 5 / 64 | 12 / 64 |
| shock events (device) | 13 | 15 | 9 | 9 |
| re-measured trials | **10** | 38 | 12 | 3 |
| drift removed | 672 mg | — | 688 mg | — |

Best per-trial uncertainty since the move. Against a 146–265 mg/rev
signal, 2.8 mg is **1–2 %**.

The shocks cluster in block E (all 10 retries are block E trials, from
`t=513 s` onward) rather than in the first minutes, which is the opposite
of the sodium-sulfate and silicon runs, where the bench was still settling
after loading. Here the bench was quiet at the start and something
disturbed it later.

## Run-to-run reproducibility — what this run is actually for

Salt is now the first powder with enough repeats to answer the Edison
review's central structural criticism: *"treat the run, not the revolution,
as the experimental unit."* Six revolutions inside one block are sequential
observations of one fill; quoting their RSD as the measurement's
reproducibility says nothing about the spread between fills, augers, rooms
and days.

`scripts/plot_powder_repeats.py` (new) plots every run of one powder side
by side and reports the between-run spread next to the within-run spread,
pooling only runs whose own QC does not flag the feed factor as a bound.

Pooling the two runs that qualify (2026-08-12 and this one; 2026-08-06 is
recorded as a lower bound, 2026-08-20 is the environment stress test):

| tilt | pooled mean | between-run RSD (n=2) | median within-run RSD |
|---|---|---|---|
| 0° | 36 mg/rev | 7 % | 18 % |
| 45° | 161 mg/rev | 13 % | 12 % |
| 90° | 248 mg/rev | 10 % | 9 % |

As a sensitivity check, adding the 2026-08-20 stress-test run — whose
block C is a real measurement even though the run is excluded — gives n=3
and between-run RSD of 20.6 % (0°), 9.3 % (45°), 12.2 % (90°).

**Between-run scatter is comparable to within-run scatter, not larger.**
Two runs is a weak variance estimate and the claim should not be pushed
further than that, but it is the first evidence that the six-revolution
error bars in this dataset are not concealing a much larger between-fill
term. That materially strengthens the single-run numbers for the other
powders — it does not replace repeating them.

## Standing items

- **Block G was not run.** The pre-run survey put the 180 s environmental
  error at 42.5 mg against a ±5 mg dose band. A closed-loop dose has no
  do-nothing interval to bracket against, so this is the one thing the
  artifact-rejection pipeline cannot fix. It needs the balance isolated.
- **Block F (vibration) is missing from every run** — the DRV2605L is not
  on the I²C bus at all.
- The HR-100A still has not been calibrated since the move; that needs a
  100 g class E2/F1 external weight, which is not at the rig.

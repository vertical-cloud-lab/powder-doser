# 2026-08-20 — new glass beaker, salt feed check, and two tooling fixes

Requested on [issue #116](https://github.com/vertical-cloud-lab/powder-doser/issues/116):
check balance stability with the replacement glass beaker, then run a short
salt test. Read-only balance work first, then actuation.

All times UTC; the lab is MDT (UTC−6).

## Summary

| Question | Answer |
|---|---|
| Does the new beaker fit and leave capacity? | **Yes** — 47.33 g gross on a 102.0084 g balance, ~55 g headroom |
| Is it more stable than the paper cup? | **Yes** — worst wander in any 60 s fell 15.2 mg → 5.9 mg |
| Does the rig convey salt? | **Yes** — 39.5 / 187.1 / 266 mg per revolution at tilt 0 / 45 / 90°, reproducing the 2026-08-12 salt battery |
| Did the standard battery run? | **No** — the pre-flight aborts `scale-unreadable`; the balance will not hold stability long enough for `read_stable()` |

## The beaker

Gross load 47.33 g. The A&D HR-100A's capacity is 102.0084 g, so ~55 g of
headroom — ample for the ~7 g a fast powder's battery consumes. It clears
the breeze break, so the shield is closed and the sash is down, unlike the
2026-08-19 configuration that had the shield top removed.

Three read-only captures, `Q` (immediate datum) at ~3.5 Hz, plus a 300 s
continuous record.

| | paper cup (2026-08-19/20) | **glass beaker, settled** |
|---|---|---|
| sample-to-sample jitter | 0.066 mg | **0.111 mg** |
| worst peak-to-peak in any 60 s | 15.2 mg | **5.9 mg** |
| over the whole window | 19.8 mg / 240 s | **6.3 mg / 150 s** |
| last 60 s | — | **sd 0.93 mg, 4.3 mg p-p** |
| reported stable (`ST`) | — | 65 % |
| samples >5 mg from the median | — | **0 %** |

The first capture after placing the beaker was much worse (sd 4.67 mg,
15.0 mg p-p, slope +11.6 mg/min) and the 300 s record showed isolated
excursions — 29.8 mg peak-to-peak inside a single 10 s window — decaying
over about four minutes. That is a settling transient, not the beaker's
steady state; the numbers above are from the second capture.

**Verdict: the beaker is an improvement and is the right vessel.** It is
still ~5× the HR-100A's 0.1 mg published repeatability, and short of the
`0.0000 g` block A deltas every valid battery run was collected at, but the
slow walk that made the paper cup unusable is largely gone.

## The rig conveys salt correctly

The stock pre-flight aborts (below), so feed was measured a different way:
no tare at all, just a stable reading before and after each revolution, and
subtract. The balance reads reliably when nothing has just moved, so this
works where the tare-based path does not.

Tilt 45°, 30 RPM, six 360° revolutions — 148.4, 190.8, 175.3, 186.4, 195.6,
187.6 mg. The first is the delivery section charging; the remaining five
average **187.1 mg/rev, RSD 3.6 %**.

| tilt | 2026-08-20, mg/rev | 2026-08-12 salt battery, block C |
|---|---|---|
| 0° | 39.5 (n=3) | 34.3 |
| 45° | 187.1 (n=5, excl. charging rev) | 175.3 |
| 90° | 266 (n=3, 164/433/202) | 230.4 |

Every tilt agrees with the 2026-08-12 salt battery to within ~15 %, on a
different vessel eight days later. Tilt is working (monotonic in tilt),
the stepper is turning the auger, and the balance is measuring. The 433 mg
outlier at 90° follows a 63 mg spontaneous discharge during the tilt move
itself — slumping at vertical, not a measurement problem.

## Why the standard battery still cannot run

`battery_preflight.run()` returns `scale-unreadable` in ~22 s, before it
turns the auger. Instrumenting its prologue step by step:

```
A pre-move read : ScaleReading(US, 0.0225, 'g')
B post-move read: ScaleReading(US, 0.0182, 'g')
C post-setspeed : ScaleReading(US, 0.0247, 'g')
D post-tare 0   : None
```

The balance is `US` (unstable) *before* the plate moves. `_read_grams()`
rejects anything that is not `stable`, so the block aborts.

This is intermittent, and the intermittency is the finding: the balance was
65 % stable at 14:35, every read stable through the 15:05–15:15 salt check,
and 0–35 % stable at 15:21 with the rig fully parked, servo PWM released,
stepper disabled and solenoid off. Ruled out along the way:

- **Not the servo holding torque** — releasing both servo PWM channels
  (`duty_u16(0)`) left jitter at 0.552 mg, unchanged.
- **Not tilt alone** — 0° is as affected as 90° during a bad stretch, and
  90° reads fine during a good one.
- **Not the tare** (see below) — reads are already `US` before any tare.
- **Not a latched instrument error** — the bench camera shows a normal
  weight in grams, no `Error 1` and no overload `E` glyph.

What changed alongside the beaker is a **rolled paper cone** now sitting in
the beaker mouth, its wide lip reaching up to the underside of the rig deck
([frame](frames/2026-08-20_tilt90-glass-beaker.png)). A large light paper
sail on the pan, possibly touching the fixed deck, fits the signature: quiet
for minutes, then unable to settle, with the rig itself proven innocent.
It is also the cheapest thing to test — remove or shorten the cone so
nothing on the pan can touch anything off it, and repeat the 75 s capture.

Bench activity in the room is the other candidate and cannot be excluded
remotely.

## Fixed: `scale.zero()` sent the wrong A&D command

Independent of the above, and a real bug. `scale.zero()` sent A&D **`Z`**
(re-zero). `Z` only moves the zero point within a limited range around the
calibrated zero. Measured on a balance reading `ST 2.1054 g` three times
running, with 2.0964 g in the beaker:

```
-- scale.zero() : sends Z then waits 500 ms --
  + 9379 ms  None
  +18751 ms  None
  +24839 ms  ScaleReading(ST, 2.108, 'g')     <- unchanged: the zero never took
```

Roughly 19 s of unreadable balance, and the value does not move. With
`erCd = 0` on this balance nothing is reported back, so it fails silently.
**`T`** (tare) has full range and works on the same load:

```
-- sending T (tare, full range) --
  +  322 ms ScaleReading(ST, 0.0002, 'g')
PT after: b'PT,+002.0925  g'
```

`zero()` now sends `T`, and its post-command settle went from 500 ms (no
margin — a working re-zero takes ~1.6 s) to 1500 ms.

`scale.py` had only ever existed on the Pico, so this change would have left
no trace in the repo. It is now tracked at
`hardware/test-module/firmware/scale.py`: committed verbatim as found first,
then patched, so the change reads as a diff. The as-found file is also on
the Pi at `~/scale.py.bak-20260820`.

**This was not what blocked the pre-flight** — the balance is already `US`
before the tare — so fixing it did not unblock the run. It is worth having
anyway: every block of the battery starts with a tare, and once more than a
couple of grams collect in the vessel, `Z` would have started costing 19 s
and a silently-skipped zero per block.

## Fixed: `scripts/bench_frame.py`

Two one-line faults, both diagnosed on 2026-08-19 but unfixable that session
because the file existed only on unmerged branches:

1. **Redirects.** Live manifest and segment URLs answer 302; `curl -sS`
   silently wrote a 0-byte file, which surfaced as "empty segment" and read
   as "wrong itag". Now `curl -sSL`.
2. **itags.** The script pinned one format. Which ladder a broadcast
   advertises depends on the client yt-dlp reaches: the Pi's copy has no JS
   runtime, falls back to the android-vr player API and sees the classic
   **91–95**, while other extraction paths return **229–232/269**. The
   2026-08-19 note recording "the current set is 229–232" was only half the
   story. It now tries `95, 232, 94, 231, 93, 230, 229, 269` in order and,
   on exhausting them, reports every itag it tried instead of failing opaquely.

Verified end to end against the live broadcast: three frames pulled this
session. Covered by `scripts/tests/test_bench_frame.py` (20 checks).

## Bench actions

1. **Deal with the paper cone.** Nothing resting on the pan may touch
   anything fixed. Either remove it, or shorten it so its lip is well clear
   of the rig deck. Then re-run the 75 s capture — it is free, and it is
   what decides whether the next battery is worth collecting.
2. **Run `CAL`** if convenient. The balance has not been calibrated since
   the move into the hood, and the manual asks for a calibration with the
   large breeze break installed after relocation.
3. Do not tare by hand — `python scripts/balance_zero.py`.

## Acceptance criterion before the next battery

From the 2026-08-19 write-up, unchanged: detrended scatter ≤0.5 mg **and**
≤2 mg of wander over 3 minutes, with the balance reporting `ST` on the large
majority of samples. Today's settled window met the wander half (4.3 mg p-p
over 60 s) but not with the reliability `read_stable()` needs.

## Rig state

Parked and safe: tilt 0°, servo PWM released, stepper stopped and disabled,
solenoid off. No tmux session or capture process. ~2.1 g of salt was
dispensed into the beaker during the feed check and is still there. No
`battery_runs` document was created — the dataset stands at **11 runs,
8 valid**.

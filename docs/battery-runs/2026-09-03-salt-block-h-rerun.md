# Block H re-run — salt, 2026-09-03 (second attempt)

Run directory: `data/battery/20260903T170437Z_salt/`
MongoDB: `powder_doser.battery_runs`, `_id 6a99adb7c2bb4690f93ed6d4`
`qc.verdict = doser-scale-unreadable`, `valid_for_cross_powder_comparison = false`

Requested by @swcharles on the hypothesis that the morning attempt
(`docs/battery-runs/2026-09-03-salt-block-h-first-run.md`) failed because a
student repeatedly used the fume hood's compressed air, which is mounted above
the powder doser. **No code changed between the two attempts**: the three-phase
doser still reads the balance through `Scale.read_stable()`.

| | MDT | UTC |
|---|---|---|
| Balance check | 10:56 | 16:56 |
| Environment survey (240 s) | 11:00 → 11:04 | 17:00 → 17:04 |
| Pre-flight | 11:04 | 17:04 |
| **Block H started** | **11:04:37** | 17:04:37 |
| **Block H ended** | **11:05:55** | 17:05:55 |
| **Elapsed** | **0:01:17** | |

## Outcome

Worse than the morning attempt. **Six of six doses failed, and the auger never
turned on any of them** (`0.00 auger rev, 0 taps` on every row).

| # | target | delivered | error | status | elapsed |
|---|---|---|---|---|---|
| 0 | 50 mg | 0.0 mg | −50.0 mg | `scale-error` | 13.0 s |
| 1 | 50 mg | 0.0 mg | −50.0 mg | `scale-error` | 12.0 s |
| 2 | 50 mg | 0.0 mg | −50.0 mg | `scale-error` | 13.0 s |
| 3 | 200 mg | 0.0 mg | −200.0 mg | `scale-error` | 12.0 s |
| 4 | 200 mg | 0.0 mg | −200.0 mg | `scale-error` | 13.0 s |
| 5 | 200 mg | 1541.0 mg | +1341.0 mg | `overshoot` | 10.0 s |

Dose 5 is the refused-tare failure documented on 2026-08-20 and again in the
morning run: the tare was silently refused while the balance was unstable, the
doser then read the **1.541 g of salt the pre-flight had just delivered**, and
`−1.3410 g to go` skipped all three phases at once. It is not an overshoot in
any physical sense — no powder was dispensed by the dose.

The morning attempt at least got one controller cycle out of dose 2. This one
got none. **No number in this run is a measurement of salt's dose accuracy.**

## The mechanism was fine; the read path was not

The pre-flight run 90 seconds before Block H returned **`feed confirmed`, 5
revolutions → 1.4088 g = 281.8 mg/rev** at tilt 90°, per-revolution
173 / 280 / 272 / 325 / 360 mg. That is salt's normal feed factor for this rig
(230–265 mg/rev on 08-12 and 08-21) and it is *measured through the same
balance*, because `battery_preflight` uses the 2026-08-20 `balance_filter` path:
bracketed instantaneous (`Q`) frames, drift fitted and extrapolated, shocks
subtracted, best-effort tare.

So on this bench, at this moment, the balance could support a bracketed
measurement to better than 10 % on a 280 mg quantity, and could not support a
single `ST` frame for the doser. That is the 2026-09-03 morning conclusion
reproduced exactly, and it is a property of the two read paths, not of the room.

## Does the compressed air explain it? Not on this evidence

The hypothesis predicts a *transient* disturbance: blasts while the student is
present, recovery once they stop. What the balance actually did:

| when (MDT) | jitter | stable frames | shocks |
|---|---|---|---|
| 10:19 at rest, before any actuation | 0.013 mg | 154/157 (98 %) | — |
| 10:21–10:25 survey | 0.011 mg | 816/837 (97 %) | 0 |
| *(morning pre-flight, feed diagnostic, Block H)* | | | |
| 10:39 | 1.804 mg | 2/105 (2 %) | — |
| 10:42 | 2.882 mg | 0/210 (0 %) | — |
| 10:56 | 1.994 mg | 2/157 (1 %) | — |
| 11:00–11:04 survey | 2.109 mg | 37/837 (4 %) | 8 in 240 s |
| *(this run)* | | | |
| 11:09–11:12 (servo A/B/A windows) | 0.72–0.81 mg | 12–17 % | — |
| 11:12 → 11:23, eleven 30 s polls | 0.66 → 4.64 mg | 3–17 % | — |

Three things argue against the compressed air being the whole story:

1. **It has not recovered in an hour.** Compressed air is a burst; the balance
   settles from a burst in seconds to a minute or two. It has now been outside
   its morning condition continuously from 10:39 to at least 11:23.
2. **Nobody is at the hood.** Bench-camera frames at 11:01 and 11:25 show the
   rig unattended, the beaker centred and clear of the breeze break, the tube
   parked flat and the balance in normal weighing mode (no error glyph).
3. **It is not monotonically improving.** It fell to 0.66 mg by 11:13 and then
   climbed back to 4.64 mg by 11:22, with four 30 s polls in between returning
   *no frames at all*. That is a bench that keeps being disturbed, not one
   recovering from a finite number of blasts.

What the compressed air *can* explain is why the morning's 10:19–10:25 window
was the quietest of the whole campaign and the 11:00 window had 8 shock events:
the room is genuinely variable. It does not explain a floor that is 60× the
morning's floor an hour later.

**The sharper framing:** the balance is in a state where blocks A–E would still
produce usable data — the pre-flight proves that — and blocks G/H cannot run at
all. The binding constraint is the doser's dependence on `ST`, and the room
decides only *how often* that dependence bites.

## The servo hold hypothesis is ruled out

The timing (pristine before the first actuation of the day, degraded ever
after) suggested the tilt servos might be holding position and coupling
vibration into the deck. They are not: reading the PWM slices after the run
returned **duty 0 on both channels** — the battery's teardown leaves the servo
de-energised — and three 30 s balance windows taken with the PWM explicitly
released, restored and released again were statistically identical
(jitter 0.761 / 0.724 / 0.811 mg, stable 17 / 12 / 16 %). Raw data:
`docs/rig-checks/data/2026-09-03_balance-servo-pwm-ab.csv`.

This reproduces the 2026-08-20 A/B/A result on a different day and with the
repaired servos.

## What to do next

1. **Give the three-phase doser the `balance_filter` read path.** This is the
   morning run's recommendation #1 and this run is the second consecutive
   demonstration that nothing else unblocks Block G or Block H. It is a
   measurement-robustness change, not a control change — no phase, angle, RPM,
   tap count or threshold moves — but it must be recorded as a method change,
   because all eleven existing Block G runs were collected through
   `read_stable()`.
2. **Move to the quieter fume hood** (@swcharles reports one is being
   arranged), and put the balance on granite + a compliant pad. Isolation is
   what makes a multi-minute closed-loop dose honest; it is not what makes the
   doser able to read.
3. **Empty the beaker between runs, and specifically after the pre-flight.**
   The pre-flight deliberately dispenses ~1.4 g to confirm feed, and that mass
   is what turns a refused tare into a 1.5 g "overshoot" instead of a 0 mg one.
   Worth doing automatically: prompt for it, or subtract the pre-flight mass.
4. **Do not quote a 50 mg accuracy number from either attempt.** The one
   controller cycle that ran this morning overshot a 50 mg target by 7.5 mg on a
   single 45° fine increment, so even with the read path fixed the fine
   increment has to scale with the measured feed factor before 50 mg is
   reachable.

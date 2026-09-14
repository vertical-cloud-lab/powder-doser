# Salt — uniform powder battery, 2026-08-12 (repeat / servo-fix confirmation)

The salt repeat requested on 2026-08-06 and deferred, finally run after
the tilt servo was repaired. It has two jobs: (1) confirm the servo fix
so the metal powders can be re-run with a working tilt axis, and (2)
settle the intra-run **drift** the first salt run
([notes](2026-08-06-salt.md)) flagged, which made that run's block C
feed factor a lower bound.

Both are resolved. **The plate tilts, and there is no drift this time.**
All three closed-loop doses converged inside ±5 mg (mean error −4.1 mg),
so salt remains the control the dataset is measured against — now with a
clean, internally consistent feed-factor curve.

| | UTC | MDT (lab) |
|---|---|---|
| Servo camera check | — | 15:44:09 (horizontal) → 15:47:19 (vertical) |
| Pre-flight | 21:50 → 21:51 | 15:50 → 15:51 |
| Battery started | 2026-08-12T21:51:54Z | 15:51:54 |
| Battery ended | 2026-08-12T22:07:07Z | 16:07:07 |
| Elapsed | 0:15:13 | |

Run directory: `data/battery/20260812T215154Z_salt/`.
MongoDB `powder_doser.battery_runs` `_id` `6a7cee8ef04570b8af97ee27`,
`batch: food-safe-2026-08`, `qc.verdict = ok`,
`qc.valid_for_cross_powder_comparison = true`,
`qc.preflight_verdict = feed confirmed`.

Per-block: A 22 s · B 1 m 01 s · C 2 m 11 s · D 33 s · E 2 m 36 s ·
F skipped (motor not attached) · G 8 m 25 s.

Operator: swcharles reported the servo repaired and loaded salt; the run
itself was remote and unattended.

## The servo fix was verified before the run, not just assumed

The 2026-08-11 AlSi10Mg run was silently wasted because the plate stayed
at 0° for the whole battery and there is no plate encoder to catch it
([amendment](2026-08-11-alsi10mg.md)). So this run did **not** trust the
"fixed" report:

- **On camera** (fume-hood stream `k9gPANBiMjU`): the plate was commanded
  from horizontal to vertical and physically moved — tube horizontal at
  15:44:09 MDT, vertical at 15:47:19 after `Servo.move_to(plate 45°)`.
- **In the run data**: block C feed factor climbs monotonically with
  tilt (below), the exact signature that was *absent* from AlSi10Mg
  (three near-equal values). A stuck plate cannot produce a tilt curve.

Lesson folded into the protocol doc: after any servo/tilt maintenance,
confirm the plate physically moves (camera, or block C shape) before
trusting a run — the firmware confirms the servo *signal*, never the
plate.

## Pre-flight

Tare, tilt 90°, five 360° revolutions at 30 RPM, then 10 taps:

| revolution | delivered (mg) |
|---|---|
| 1 | 233.9 |
| 2 | 238.1 |
| 3 | 253.0 |
| 4 | 242.6 |
| 5 | 246.8 |

**242.9 mg/rev, feed confirmed** — steady from the first revolution, no
charging transient. This is ~18× the first salt run's pre-flight
(13.1 mg/rev), because this auger was freshly and fully loaded. The whole
run sits an order of magnitude higher in feed factor than 2026-08-06 for
the same reason.

## Block C — feed factor rises with tilt (n = 6 each, 30 RPM)

| tilt | mg / revolution | RSD |
|---|---|---|
| 0° | 34.3 | 8.6 % |
| 45° | 175.3 | 6.0 % |
| 90° | 230.4 | 6.0 % |

Monotonic and saturating above 45° (+31 % from 45° to 90°), all tilts
`steady` revolution by revolution, single-digit RSD at 45°/90°. This is
the same shape as the first salt run (5.6 / 17.1 / 24.9 mg/rev) scaled up
~10× by the fuller auger — the *curve* is reproducible, the *magnitude*
tracks fill.

## Drift check — the first salt run's anomaly does not reproduce

Blocks C and E independently measure mg per 360° revolution at the same
tilt, ~5 minutes apart. On 2026-08-06 salt was the one powder whose E/C
ratio was anomalous (2.68 at 45°, climbing *up* through the run), which
is why that run's block C was recorded as a lower bound.

| | block C 45° | block E 45° re-feed | E / C |
|---|---|---|---|
| salt 2026-08-06 | 17.10 | 45.79 | **2.68** (anomalous) |
| **salt 2026-08-12** | **175.3** | **162.3** | **0.93** (normal) |

0.93 is squarely in the 0.74–1.12 band the other six powders sit in — a
slight downward drift as the column depletes, exactly what the fixed
block order predicts. So the upward drift in the first run was a one-off
(most likely early-run charging of a less-full auger), **not** a standing
property of salt. This run's block C feed factor is therefore a real
measurement, not a lower bound, and the block D speed slope below is
interpretable where the first run's was not.

## Block D — mass per revolution falls with speed (tilt 45°)

3 continuous revolutions at each speed:

| auger RPM | mg / 3 rev | mg / revolution |
|---|---|---|
| 15 | 708.4 | 236.1 |
| 45 | 574.9 | 191.6 |
| 90 | 378.4 | 126.1 |

**−47 % across a 6× speed change** — a clean, monotonic negative slope,
which the first salt run could not show because of its drift. Salt in a
full auger behaves like the other free-flowing powders (calcium lactate
−33 %, xanthan gum −55 %): filling-limited by time, so a faster screw
gives each flight less time to fill. The 15 RPM trace is the clearest
pulsation record in the panel — discrete ~40 mg slugs, one per
revolution, with flat plateaus between.

## Block E — tapping contributes almost nothing

| tilt | 360° re-feed | single tap |
|---|---|---|
| 0° | 36.99 mg | 0.04 mg (RSD 138 %) |
| 45° | 162.26 mg | 0.91 mg (RSD 19 %) |

The tap quantum is 0.91 mg at 45° — small, but note the 19 % RSD: unlike
the low-feed flours/alginate (>180 % RSD, indistinguishable from zero),
salt's tap is *reliable*, just small. That reliability, not magnitude, is
what lets phase 3 close a dose (below). Smaller than the first salt run's
3.05 mg/tap, consistent with a fuller column packing the lip more firmly.

## Block G — all three doses converge (frozen salt-tuned controller)

| dose | delivered | error | status | time | cycles | taps |
|---|---|---|---|---|---|---|
| 1 | 0.9956 g | −4.4 mg | `ok` | 169 s | bulk 11, fine 14, tap 35 | 70 |
| 2 | 0.9968 g | −3.2 mg | `ok` | 132 s | bulk 12, fine 14, tap 21 | 42 |
| 3 | 0.9953 g | −4.7 mg | `ok` | 203 s | bulk 12, fine 11, tap 61 | 122 |

**Mean error −4.1 mg; three of three `ok`.** Cleaner than 2026-08-06,
which landed 2× `ok` + 1× `overshoot` (mean +0.2 mg) and showed the same
monotone drift toward overshoot that this run does not. Every phase does
its job: bulk converges in 11–12 cycles, fine in 11–14, and phase 3 taps
the last ~30–50 mg home rather than stalling or overshooting. The tight
−3.2 to −4.7 mg spread with no drift is the strongest control result in
the dataset.

Reading this against the frozen-controller argument: with a well-charged
auger and no drift, the salt-tuned parameters hit ±5 mg on salt every
time — so the −27 to −292 mg errors on the other powders are a
transferability problem (calibration tuned on salt does not carry), not a
hardware limit. That is the manuscript's point, now on a repeat.

## Other blocks

- **A baseline** — 8 no-actuation reads, all exactly 0.0000 g.
- **B hold** — no spontaneous discharge at 0°, 45° or 90°. Salt does not
  avalanche through a stationary auger even fully vertical; flow is
  auger-gated, not gravity-gated.
- **F vib** — skipped, DRV2605L not attached. Still missing from every
  run; needs one back-fill pass once the motor is on.

## Bottom line

Servo fix confirmed (camera + block C). Drift resolved (E/C = 0.93). Salt
remains the control and now has a clean feed-factor curve and a
three-of-three converging dose set. The metal powders can be re-run with
a working tilt axis — starting with the AlSi10Mg re-run the amendment
already flagged.

# Block H, first hardware run — salt, 2026-09-03

Run directory: `data/battery/20260903T163527Z_salt/`
MongoDB: `powder_doser.battery_runs`, `_id 6a99a3cb42801c63fd831214`
`qc.verdict = doser-scale-unreadable`, `valid_for_cross_powder_comparison = false`

| | MDT | UTC |
|---|---|---|
| Balance check | 10:19 | 16:19 |
| Environment survey (240 s) | 10:21 → 10:25 | 16:21 → 16:25 |
| Pre-flight | 10:26 | 16:26 |
| Escalated feed diagnostic | 10:30 → 10:34 | 16:30 → 16:34 |
| **Block H started** | **10:35:27** | 16:35:27 |
| **Block H ended** | **10:37:55** | 16:37:55 |
| **Elapsed** | **0:02:28** | |

Blocks A–G were not requested; salt is already characterised by the 2026-08-06,
08-12 and 08-21 runs. This run exists to exercise Block H on hardware for the
first time.

## Outcome in one line

The Block H *code* works end to end. The Block H *doses* do not, because the
three-phase doser cannot read the balance while the rig is actuating.

## What worked

`RUN,END,ok`. Every piece of the 2026-09-03 Block H implementation behaved as
designed:

- both targets ran, in order, three repeats each;
- `META,dose_h.thresholds.0.0500 -> 0.0500;0.0250;0.0050` and
  `META,dose_h.thresholds.0.2000 -> 0.2000;0.0500;0.0050`, i.e. the
  `t1 = min(t1, target)` and `t2 = min(t2, target/2)` rules fired exactly as
  specified, with the tolerance held at ±5 mg;
- the bulk phase correctly skipped itself on every dose
  (`phase 1/3 'bulk' skipped (0.2000 g to go is already <= 0.2000 g threshold)`),
  which is the whole point of scaling `t1` — a bulk phase carrying ~0.12 g in
  flight must never open for a 50 or 200 mg dose;
- every `DOSE` row carries the trailing `H` block letter (`battery_version` 3);
- `dose_summary_by_target` split the results per target rather than averaging a
  50 mg dose against a 200 mg one.

## What failed

| # | target | delivered | error | status | cycles | taps |
|---|---|---|---|---|---|---|
| 0 | 50 mg | 0.0 mg | −50.0 mg | `scale-error` | — | 0 |
| 1 | 50 mg | 7539.3 mg | +7489.3 mg | `overshoot` | bulk 0, fine 0, tap 0 | 0 |
| 2 | 50 mg | **57.5 mg** | **+7.5 mg** | `overshoot` | bulk 0, fine 1, tap 0 | 0 |
| 3 | 200 mg | 168.1 mg | −31.9 mg | `scale-error` | bulk 0, fine 4, tap 5 | 12 |
| 4 | 200 mg | −0.1 mg | −200.1 mg | `scale-error` | bulk 0, fine 1 | 0 |
| 5 | 200 mg | 6.1 mg | −193.9 mg | `scale-error` | bulk 0, fine 1 | 0 |

Four of six exited `scale-error`. **Neither of the two that reached a terminal
control state is a measurement of salt's dose accuracy**, so no accuracy number
from this run should be quoted.

### Root cause: the doser requires `ST`; the balance does not offer it

The A&D HR-100A was in the **best condition of the whole campaign at rest** —
the 240 s pre-run survey returned 0.011 mg sample-to-sample jitter, 816/837
frames stable (97 %), zero shock events, +0.0 mg/min drift, and an
environmental error over 180 s of **0.8 mg** against the ±5 mg dose band. That
is the first time since the fume-hood move that the Block G/H environmental gate
has passed.

It collapsed the moment the rig actuated, and did not recover:

| when | jitter | stable frames |
|---|---|---|
| 10:19, at rest, before any actuation | 0.013 mg | 154/157 (98 %) |
| 10:21–10:25 survey, at rest | 0.011 mg | 816/837 (97 %) |
| 10:39, right after the run | 1.804 mg | 2/105 (2 %) |
| 10:42, eight minutes after the run | 2.882 mg | **0/210 (0 %)** |

`Scale.read_stable()` waits for the balance to assert `ST` and returns `None`
otherwise; the doser turns that `None` into `scale-error` and abandons the dose.
With 0–2 % of frames stable, that is a coin flip per read.

**Dose 1 is the same fault one step earlier.** The doser tared, the balance
silently refused the tare while unstable, and the doser then read the 7.5393 g
of salt already sitting in the beaker from the feed diagnostic. Against a 50 mg
target that is an instant overshoot — recorded as `bulk:0;fine:0;tap:0`, i.e.
the auger never turned. This is precisely the refused-tare behaviour documented
on 2026-08-20 (`docs/rig-checks/2026-08-20-balance-error-1-remote-rezero.md`).

### Why blocks A–E do not have this problem

The 2026-08-20 work replaced the battery's stable-frame dependence with
`balance_filter`: bracketed *instantaneous* (`Q`) frames either side of an
actuator-gated window, drift fitted and extrapolated, shocks subtracted, and a
best-effort tare, on the reasoning that every battery measurement is a
*difference* between two bracket fits so a stale zero cancels exactly. That work
was applied to `powder_battery.py` and `battery_preflight.py`. **It was never
extended to the three-phase doser**, which Blocks G and H both call. Blocks A–E
have been running fine on this bench for two weeks; Blocks G and H inherited the
old read path.

This reframes the standing "Block G is blocked on the granite" note. Isolation
is still wanted, but it is not the only blocker and today it was not the binding
one: the room was quiet enough to dose in, and the doser still could not read.

### The one real control observation

Dose 2 is the only dose whose controller ran to completion:

    fine cycle 1 -> 57.5 mg delivered, target 50 mg, overshoot +7.5 mg

**A single 45° fine increment overshot the entire 50 mg target.** The Block H
design comment predicted this ("one 45° fine increment is ~20 mg on a fast
powder — 40 % of a 50 mg dose") and set `t2 = target/2` so the tap phase would
take the last half. It is worse than predicted: salt was conveying at
**182–235 mg/rev** in the feed diagnostic minutes earlier, so a 45° increment is
~28 mg of commanded travel and delivered 57.5 mg once in-flight mass landed —
i.e. **larger than the target, never mind the ±5 mg tolerance**.

So even with the read path fixed, a 50 mg dose is not reachable by the frozen
Block G parameter set on a powder this fast. The fine increment has to scale
with the measured feed factor. This is the same conclusion the calcium lactate
run reached at 1.000 g, arriving here much more sharply because the target is
20× smaller.

The 200 mg target is the one worth defending: dose 3 reached 168.1 mg through 4
fine and 5 tap cycles before the read failed, which is the controller behaving
sensibly.

## Pre-flight: `suspect-no-feed`, escalated, feed confirmed

The standard 5-revolution pre-flight returned **−20.1 mg net**
(−58, +42, −15, +12, −0.2 mg per revolution) → `suspect-no-feed`. Per protocol
that is never grounds to stop, so it escalated to `battery_feed_diagnostic`:

| test | delivered | per revolution |
|---|---|---|
| 10 rev @ 60 RPM | 1.8181 g | 181.8 mg |
| 3 × 20 taps | 0.279 / 0.243 / 0.275 g | ~13.4 mg/tap |
| 3 × 5 rev @ 30 RPM | 1.1254 / 1.1172 / 1.1725 g | 225 / 223 / 235 mg |

182–235 mg/rev is salt's normal feed factor at tilt 90° (230–265 mg/rev on
08-12 and 08-21), so the delivery path was clear. The auger had been idle since
2026-09-01, so the delivery section was empty and the pre-flight revolutions
charged it; the swing in those five readings is the post-tilt settling
transient, not conveyance.

Worth noting for the protocol: this is the fourth time the 5-revolution
pre-flight has under-reported a freshly-idle column (CMC 73×, silicon 4.5×,
AlSi10Mg, and now salt reading *negative*). The per-revolution list, not the
average, is the thing to read.

## Recommended next steps

1. **Give the three-phase doser the `balance_filter` read path** — bracketed
   instantaneous frames and a best-effort tare, exactly as `powder_battery.py`
   got on 2026-08-20. This is a measurement-robustness change, not a control
   change: no phase, angle, RPM, tap count or threshold moves. It should be
   made deliberately, because all 11 existing Block G runs were collected
   through `read_stable()`, so the change needs to be recorded as a method
   change in the run documents.
2. **Re-run Block H on salt** afterwards, before spending it on other powders.
3. **Scale the fine increment with the measured feed factor** before quoting any
   50 mg accuracy number. At 225 mg/rev a 45° step cannot resolve 50 mg ±5 mg.
   Consider dropping the 50 mg target for fast powders, or making the increment
   `target/N` rather than a fixed angle.
4. **Empty the beaker between runs.** 7.5 g of diagnostic salt sitting in it is
   what turned a refused tare into a 7.5 g "overshoot" instead of a 0 mg one.
5. The **balance degradation is unresolved** — it got worse over the eight
   minutes after the run rather than settling, which is not the decaying
   actuation transient seen on 2026-08-20. The bench camera shows no mechanical
   bridge between vessel and frame, so this needs a look at the bench.

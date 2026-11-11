# Blocked-auger balance-disturbance battery, run 1 — 2026-09-15 (halted by mass guard)

Requested on PR #131: with a **mechanically blocked auger** installed (so no
powder can dispense), characterize what taps and auger revolutions look like
on the balance — pure measurement disturbance, separating actuator vibration
from the fume-hood environment (issue #157), per the #162 Edison review's
data gaps (R under motor/tapper disturbance, settling under disturbance).

**What actually happened: the "blocked" auger dispenses.** Quiet windows sat
at drift level, but every actuation block deposited real, persistent mass.
The battery's 5 g cup guard halted the session at t = 444 s, mid-way through
the 55 rpm block (about 40 % through the planned sequence). Independent
settled weigh after halt: **5.1661 g absolute** in the cup (session start:
−0.022 g).

## Evidence that it is powder, not vibration bias

- Levels **persist after actuation stops** (quiet_mid2 sits flat at the
  post-burst level, +0.2 mg/min) — a vibration-biased reading would relax.
- Post-spin windows show classic **afterflow tails** (+75 and +84 mg landing
  over ~4 s after the 15/30 rpm blocks ended).
- Per-tap epochs are step functions (balance τ ≈ 0.16 s smear), not
  transients that return to baseline.

## Deposition per actuation (tilt 0° throughout)

| actuator | deposition | note |
|---|---|---|
| single tap (60 ms) | **20.1 mg/tap** (n=20) | first taps ~40–120 mg, decaying to ~5–10 mg (lip depletion) |
| 3-pulse burst | 15.1 mg/burst (n=8) | after the lip was already drawn down |
| auger 15 rpm | **277 mg/rev** | 15 s continuous, 3.75 rev |
| auger 30 rpm | 226 mg/rev | 15 s, 7.5 rev |
| auger 55 rpm | 173 mg/rev | 8.9 s until guard halt |

For scale: salt at 0° tilt gave 24–61 mg/rev and 0.03–0.34 mg/tap
(2026-07-31); *nothing* previously measured on this rig approaches
277 mg/rev at 0°. The exit-funnel region below any plug holds ≲2 g, and
5.2 g landed with per-rev yield still high at halt — so the main powder
column is feeding the screw. **The block is not blocking** (failed / fell
out / wrong auger installed). A per-rev yield that *falls* with rpm
(277→226→173) is consistent with a gravity-choked path being agitated.

## Salvage: fume-hood quiet floor (#157, #162 "R from stationary readings")

Detrended sigma over datum-changed frames, per quiet window:

| window | sigma (mg) | slope (mg/min) | ST-flag fraction |
|---|---|---|---|
| quiet_pre (120 s) | 1.18 | +1.3 | 0.79 |
| quiet_mid1 (30 s) | 0.33 | +5.7¹ | 0.85 |
| quiet_mid2 (30 s) | 0.73 | +0.2 | 0.85 |

¹ 30 s right after the tap block — includes fresh-deposit settling, not pure
drift.

Compared with pre-hood anchors: 08-14 bench quiet frame noise 0.13–0.42 mg;
08-07 static floor 0.59 mg/60 s with −1.5 mg/min drift. Today's floor is
**~2–4× noisier, with multi-mg wander on 20–40 s timescales and drift of
flipped sign**, and the balance flags itself unstable 15–21 % of the time
even with nothing running — consistent with fume-hood airflow as a dominant
low-frequency disturbance. Raw stream ran at ~10.4 Hz effective datum rate
(balance `Spd` likely at 10/s).

Also observed: the tap impulse itself kicks the reading **negative by
~10–20 mg for ~0.3–0.5 s** before the landed mass registers (visible in the
epoch overlay) — a genuine mechanical disturbance signature, though here it
is superposed with real deposition.

## State / next steps

- **Cup holds ~5.17 g of un-ledgered powder** (identity of the loaded
  material unconfirmed) — empty before the next run.
- Rig left safe: guard halted all actuation; stepper de-energized; Pico
  soft-reset to resident firmware; port released.
- The full battery
  ([`balance_disturbance.py`](../../../hardware/test-module/firmware/balance_disturbance.py))
  is committed and ready to re-run as-is once the block is physically
  verified (it self-checks: if the first blocks deposit nothing, the rest of
  the ~16 min sequence completes and delivers the full disturbance map).

## Files

- `balance_disturbance_r1.log` — raw telemetry (4,518 frames, ST/US flags,
  rpm/tap/servo state per frame; M/E/P/D rows)
- `samples.csv`, `blocks_summary.csv`, `tap_epochs.csv`, `summary.json` —
  parsed outputs of `scripts/analyze_balance_disturbance.py`
- `blocked_auger_overview.png` — full-session evidence figure
- `quietfloor_and_leak.png` — quiet floor, per-tap steps, leak rates

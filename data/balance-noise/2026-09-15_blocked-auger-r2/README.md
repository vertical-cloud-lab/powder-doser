# Blocked-auger balance-disturbance battery, run 2 — 2026-09-15 (complete)

Re-run of the r1 battery after the auger exit was physically covered
(PR #131 request). Same script
([`balance_disturbance.py`](../../../hardware/test-module/firmware/balance_disturbance.py)),
same protocol, unchanged parameters; full ~16 min sequence completed with
no mass-guard trip.

**The cover holds.** Net mass change over the whole session: **−0.4 mg**.
Apparent deposition per actuation is zero at the noise level (single tap
−0.4 mg/tap, bursts −0.4 mg/burst, auger −1.3 to −3.6 mg/rev — small
*negative* deltas, i.e. vibration re-seating, not powder). A pre-battery
leak probe (3 rev @ 30 rpm → −21 mg, vs r1's +226 mg/rev) agreed. So
unlike r1, every deviation in this log is **measurement disturbance, not
mass** — exactly the dataset the #162 gaps asked for.

## Disturbance map (what each actuator does to the reading)

Detrended sigma over datum-changed frames; bias = block-end minus
block-start level. Mean quiet floor this session: **1.4 mg** (see below).

| state | sigma (mg) | ST-flag % | bias while active | recovery |
|---|---|---|---|---|
| quiet windows (6) | 0.30–4.50 | 28–90 % | — | — |
| single taps (20) | 10.7 | 26 % | −8.3 mg kick at +0.89 s/tap | back to ≈0 by ~2 s (mean) |
| 3-pulse bursts (8) | 9.2 | 36 % | same shape | same |
| auger continuous 15–75 rpm | 3.9–7.8 | **0–8 %** | **−6 to −31 mg depressed** | +0.3 to +51 mg after halt |
| stepper hold (energized, v=0) | 2.5 | 40 % | ≈0 | — |
| discrete 45° increments (10) | **13.3** | 48 % | ±30–60 mg excursions | relaxes over ~1 min |
| combined 55 rpm + 1 tap/s | 4.5 | 5 % | as auger | +40 mg after halt |
| servo tilt moves (0↔25↔60°) | 8.8 | 59 % | p2p 57 mg kicks | returns to baseline |

Key numbers for the #162 gaps:

- **R (stationary)**: 0.30–4.50 mg 1σ per window, *time-varying* — the
  six quiet windows differ by 15× within one 16-min session.
- **R (under actuation)**: taps ~9–11 mg, continuous auger ~4–8 mg,
  discrete increments ~13 mg, hold ~2.5 mg, servo ~9 mg — all with
  ground-truth mass ≈ constant.
- **Settling after auger halt**: first ST-flagged frame arrives
  **1.4–2.2 s** after the spin stops, at every rpm (`first_stable_s` in
  `blocks_summary.csv`); the *level* keeps recovering for longer.
- **ST/US behaviour**: the stable flag is useless during a spin (0–8 %
  ST) and only ~26–36 % during tap trains; it returns within ~2 s of
  actuation stopping.

## The controller-relevant discovery: spins bias the reading LOW

While the auger turns, the balance reads **5–30 mg below** the true
(constant) mass, and the deficit relaxes back over seconds after the
halt (post-block recoveries +8…+51 mg, largest after 75 rpm). Two
consequences:

1. A mass-threshold stop evaluated on readings taken *while spinning*
   fires **late** by that bias — it adds to real afterflow.
2. Part of what past sessions logged as post-halt "afterflow" (e.g. r1's
   +75/+84 mg tails; the 08-07 stop-response tails) is this recovery,
   not powder landing. r2 bounds the vibration component at roughly
   +10–50 mg depending on rpm; the powder component is the remainder.

Taps excite a **slow ±20–30 mg oscillation** (tens of seconds) on top of
the fume-hood wander: the mean single-tap response returns to ≈0, but an
*individual* reading 3–4.5 s after a tap has sd ≈ 18 mg (range ±30 mg).
Single-reading tap-yield estimates in the hood need averaging or a
longer settle than the pre-hood data needed.

## Fume-hood floor (issue #157): elevated, and intermittent

Quiet-window sigma: 4.50 (pre), 1.39, 0.90, 0.30, 0.39, 1.09 (post) mg;
drift −0.7 to +19 mg/min, sign-flipping; quiet p2p up to 19 mg / 120 s.
Best windows match the pre-hood bench floor (08-14: 0.13–0.42 mg; 08-07:
0.59 mg), worst are >10× it — the hood contribution comes in episodes
rather than as a constant. The user-suspected "most noise is the fume
hood" is therefore half-right: the hood sets a wandering, episodic floor
(dominates *quiet* variance), but actuation adds separable structure
3–10× above it plus the deterministic bias/kick signatures above, which
persist even in the quietest windows.

## State / provenance

- Cup was emptied before this run (pan absolute ~0.46 g vs 5.17 g at r1
  halt); salt ledger unaffected (nothing dispensed).
- Rig left safe: battery's finally-block halted actuators; Pico
  soft-reset to resident firmware (`[rig] ready` confirmed); port
  released. Known `DRV2605L (EIO)` boot warning unchanged.
- Launched detached on the Pi:
  `mpremote connect /dev/ttyACM0 run /tmp/balance_disturbance.py
  > /tmp/balance_disturbance_r2.log`; log fetched back over Tailscale
  SSH.

## Files

- `balance_disturbance_r2.log` — raw telemetry (9,451 D-frames at
  ~10.4 Hz datum rate, ST/US flags, rpm/tap/servo state; M/E/P rows)
- `samples.csv`, `blocks_summary.csv`, `tap_epochs.csv`, `summary.json`
  — parsed outputs of `scripts/analyze_balance_disturbance.py` (now also
  emits `first_stable_s` per block and handles the clean outcome)
- `blocked_auger_overview.png` — full-session trace + actuation timeline
- `quietfloor_and_leak.png` — quiet floor, mean tap impulse response,
  apparent deposition (≈0)
- `disturbance_map.png` — sigma + ST-fraction per actuation state

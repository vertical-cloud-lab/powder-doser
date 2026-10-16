# Rate-PI trickle-tap trim test — carboxymethyl cellulose, 2026-09-08

First hardware run of a **PI dose controller** on this rig (PR #131). Every
earlier real dose came from the fixed-increment three-phase firmware; this is
the `trickle_tap` controller from the PR #124 twin
(`optimization/benchmarks/bangbang.py` @ `dc99459`) ported to run on the Pico,
requested on PR #131 to measure how well **PI trim control** reaches a goal
mass. PI version only (no bang-bang bulk stages) — every trial starts from rest
at the trim tilt, the "small target → straight to the trickle" branch.

## What ran

`hardware/test-module/firmware/pi_trickle_trim.py` on the Pico via
`mpremote run` (RAM only). Controller = seeded rate-PI trickle (`rpm =
clip(kp·err + ki·∫, 0, 45)`, kp 250 / ki 120) + 3-state KF (mass, rate, balance
lag; τ_bal = 0.16 s measured) + predictive cutoff `m̂ + r̂τ + kσ ≥ target −
margin` + single-tap finish with 5° nudges when the lip runs dry — **PI law,
gains, margins, cutoff and `tap_finish` copied verbatim** from `bangbang.py`.

Trim settings per the request: trickle tilt **20°** (a low/trim angle), tap
finish 0°, ±5 mg tolerance. A feed probe at session start found 20° does not
convey CMC (−7 mg/rev = noise), so it auto-bumped the trickle tilt to **25°**
(12 mg/rev) — logged in the run document.

6 interleaved trials, targets {200, 100, 400, 200, 100, 200} mg, ~32 min,
0.19 g CMC dispensed total.

## Result — the PI trim does not reach target on CMC

| target | n | final error (raw) | final error (drift-corr.) | verdict |
|---|---|---|---|---|
| 100 mg | 2 | −87.4, −94.4 mg | −79.8, −84.5 mg | tap_stalled |
| 200 mg | 3 | −173.7, −170.4, −157.0 mg | −165.4, −162.1, −146.8 mg | tap_stalled |
| 400 mg | 1 | −367.7 mg | −359.3 mg | tap_stalled |

All six **undershoot massively** (mean −175 mg raw, −166 mg drift-corrected);
**0/6 within ±5 mg, 0/6 over target.** The undershoot scales with target
because the trickle delivers ~nothing and the tap+nudge endgame contributes a
roughly fixed ~13–43 mg regardless of target.

Two failure modes, both visible in the telemetry:

1. **The rate-PI trickle cannot sustain flow on CMC.** It either stall-bails
   (8 s no gain, m̂ ≈ 0) or fires a *premature* predictive cutoff on KF-predicted
   committed mass (r̂τ + kσ) that never physically arrives. The KF believes flow
   is happening (r̂ spikes to 50–110 mg/s chasing the setpoint) while the balance
   barely moves — CMC arches / won't trickle-convey at the low rates the trim PI
   commands.
2. **Taps deliver ~0 on CMC** (consistent with the 08-05 battery: tap yield
   0.01–0.15 mg). Every trial exhausted all 120 tap cycles without reaching
   tolerance; the only powder the endgame delivered came from the ≤6 auger
   *nudges*.

This is a cross-powder transfer failure: a controller tuned on free-flowing
salt does not transfer to cohesive CMC, on both actuators.

## Files

- `pi_trim_cmc_0908.log` — raw M/E/B/D/P/C/H/T telemetry (3313 lines, incl.
  every raw balance frame with stable/unstable flag)
- `trials_carboxymethyl-cellulose.csv` — one row per trial: errors (raw +
  drift-corrected), trickle landing, KF halt decomposition, tap/nudge counts
- `tapcycles_carboxymethyl-cellulose.csv` — per-tap-cycle mass deltas
- `drift_carboxymethyl-cellulose.csv` — quiet-window drift fits
- `run_carboxymethyl-cellulose.json` — full run document (also in MongoDB
  `powder_doser.dose_runs`, `doc_type: pi_trickle_trim`) with video reference (#148)
- `pi_trim_dashboard.png`, `pi_trim_scorecard.png` — figures
  (`scripts/analyze_pi_trim.py`)

## Drift note (fume hood, #116/#157)

No hardware tare (the A&D refuses `Z` under load); every trial works in
differences from its own settled baseline. Steady thermal drift was
**−1.66 mg/min** (clean end-of-session survey); the 15 s pre-trial windows read
steeper (−13 to −31 mg/min) but those are post-dose settling transients, not
drift, and are not used for correction. Drift correction shifts each error by
only +8 to +10 mg — it does not change any conclusion.

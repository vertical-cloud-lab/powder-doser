# Data bundle: auger powder doser as a flowability screen (vertical-cloud-lab/powder-doser)

## The instrument
Open-hardware auger doser. A tube with a helical auger (stepper, 5-100 rpm) is fed from a small hopper. A servo
tilts the tube: tilt 0 deg = horizontal, 90 deg = vertical (outlet down, gravity assisting). A solenoid taps the
tube. An analytical balance (0.1 mg readability) under the outlet is polled at roughly 2.5-4 Hz. The lab bench is
noisy (block A baseline std is often 10-30 mg; see docs/powder-battery-protocol.md, "environment survey").

## Files
- `docs/powder-battery-protocol.md`: the uniform 12-powder test battery (blocks A-H). A = balance baseline,
  B = 15 s static hold at tilt 0/45/90 (spontaneous discharge), C = 6 single 360 deg revolutions at 30 rpm at each
  tilt 0/45/90 with a stable read after each (per-revolution mass = feed factor), D = 3 continuous revolutions at
  15/45/90 rpm at tilt 45 with streamed polls, E = single taps at tilt 0/45 each preceded by a measured re-feed
  revolution, G/H = closed-loop doses.
- `docs/battery-runs/run-log.csv`: one row per run with `qc_valid`, `qc_verdict`, feed factors and the data dir.
  Use only `qc_valid == True` runs for A-E statistics unless a note says otherwise. `RUN-LOG.md` is the narrative.
- `data/battery/<UTC>_<powder>/`: per run. `trials_*.csv` (one row per measured action: block, tilt_deg, phase,
  trial, rpm, before_g, after_g, delta_g, sigma_g, drift_g, shock_g, retries, quality), `summary_*.csv`
  (block-level mean/std/RSD), `polls_*.csv` (streamed polls: block, tilt_deg, rpm, t_ms, grams, stable; block D
  and dose phases), `doses_*.csv`, `run_*.json`, `timeline_*.csv`, `retries_*.csv`.
  Salt (the control) has three valid A-E runs on different days (2026-08-12, 2026-08-20, 2026-08-21): use them
  for day-to-day repeatability. Fumed silica (2026-08-21) is an extreme-cohesion anchor.
- `data/powder-properties/`: `battery_responses.csv` (curated per-powder responses) and
  `literature_powder_properties.csv` (+ `_long.csv` with sources): literature bulk/tapped density, Hausner ratio,
  d50, angle of repose (AoR), true density, moisture. `docs/powder-property-correlations.md` is the prior analysis
  (literature AoR vs log feed factor at 90 deg: Spearman rho -0.84, n = 12). Literature values are class-typical,
  not lot measurements; several HR and AoR values are estimates (flagged in the long CSV).
- `data/opt/production-alsi10mg/`: one 8 g dose of commercial gas-atomized AlSi10Mg (an LPBF-grade powder) at
  bulk tilt 40 deg, 100 rpm, 2 Hz cadence taps. `zero/trial_*.json` has `telemetry` (`header` + `rows`, about 4 Hz)
  and `stop_events`. README: steady 0.25 g/s after a 13 s priming delay.
- `data/opt/production-al4047-9fxeqt/`: three doses of freshly gas-atomized, UNSIEVED in-house Al 4047 (Al-12Si)
  at the SAME bulk settings. Oversize chunks lodged in the tube. Bulk flow decayed from about 0.17 g/s to
  0.011-0.017 g/s; the 10 deg trickle stalled; taps at 15 deg added about 0.06 mg/tap. README has the details.
- `data/opt/salt-20260929T014732Z/`: a 40-dose Bayesian-optimization campaign on salt that varied bulk tilt
  (15-40 deg), bulk rpm (20-100), taps etc. `campaign_records.jsonl` + `zero/trial_*.json` (telemetry) give bulk
  flow rate vs tilt x rpm for one powder, useful for within-powder repeatability and the flow-rate surface.

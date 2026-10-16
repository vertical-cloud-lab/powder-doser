# Phase-resolved afterflow characterization — salt — 2026-08-13

Firmware: `hardware/test-module/firmware/afterflow_phase.py` (run on the Pico
via `mpremote run`, RAM only). Analysis: `scripts/analyze_afterflow_phase.py`.

Auger↔stepper gearing is **44:20 = 2.2** (folded into
`main_three_phase.Stepper.steps_per_rev = 200×8×2.2 = 3520 microsteps per
AUGER revolution`). Auger phase is tracked exactly from the commanded
microstep shadow: `phase_deg = (_position mod 3520)/3520 × 360`.

## Tests
- **Test A — slug periodicity.** 45° auger increments across 4 revolutions ×
  2 scans (position mode, exact angle), mass weighed at each increment.
- **Test B — afterflow vs halt phase.** Cruise 4 revolutions at 90 auger RPM,
  decelerate to a hard stop at a commanded auger phase φ∈{0…315°}, de-energise,
  weigh the settling tail. afterflow = settled − m_halt. 8 phases × (55°:3,
  70°:2 reps), interleaved. Auger-only (no taps).

## Files
- `afterflow_phase_salt.log` — raw CSV telemetry (M/E/D/P/A/B lines)
- `afterflow_phase_A.csv`, `afterflow_phase_B.csv` — parsed per-trial tables
- `afterflow_phase_slug.png` — Test A (yield vs phase; cumulative vs angle)
- `afterflow_phase_halt.png` — Test B (raw + detrended afterflow vs phase; drift)

## Measurement note
No hardware tare: the A&D `Z` (re-zero) command silently halts the balance's
`Q`-poll replies when the pan is loaded (the cup can't be emptied remotely
mid-session). Masses are tracked ABSOLUTE and all yields/afterflows are
differences, so the standing offset cancels. The auger is de-energised before
every weigh so the Tic driver can't inject noise into the scale UART.

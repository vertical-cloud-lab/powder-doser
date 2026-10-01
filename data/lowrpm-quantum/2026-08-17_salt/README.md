# Low-rpm stop battery + quantum vs tilt at trim speed — salt — 2026-08-17

The two measurements requested in [PR #124](https://github.com/vertical-cloud-lab/powder-doser/pull/124#issuecomment-5273170433)
before the trim stage can be designed.

Firmware: `hardware/test-module/firmware/lowrpm_quantum.py` (run on the Pico via
`mpremote run`, RAM only). Analysis: `scripts/analyze_lowrpm_quantum.py`.

## Tests

- **Test D — low-rpm stop battery** (20 trials). 5 / 10 / 15 / 25 auger rpm ×
  5 reps at 55° tilt, auger-only. Each trial cruises **3 auger revolutions**,
  decelerates to the **same commanded auger phase (0°)** in position mode,
  de-energises, and weighs the settling tail. afterflow = settled − m_halt;
  flow-at-halt is fitted offline from the streamed cruise samples.
- **Test Q — quantum vs tilt at trim speed** (108 increments). 20° auger
  increments at 10 rpm, weighed **at rest** (stepper de-energised + 400 ms
  quiet), at 15 / 35 / 55° tilt × 2 scans of exactly one revolution each.
- **Test D2 — bonus tilt arm** (8 trials). The same stop battery at 25° tilt,
  2 reps, to test whether AF0 scales with tilt / lip charge.

## How "matched fill" was achieved without weighing the tube

The loaded tube (tube + salt) exceeds the balance's 102 g range, so weighing the
fill between blocks is not possible remotely. Three substitutes were used, and
for the specific confound at issue they are stronger than a between-block
weighing:

1. **Equal mass per trial by construction** — every stop trial cruises the same
   3 revolutions, so each rpm level consumes the same mass per trial.
2. **Rotated + alternately reversed rpm order within each rep block**
   (`build_plan_D`), so each rpm level sees the same mean position in the
   drawdown sequence. This is exactly what the C7 sweep lacked.
3. **Matched-revolution flow check** — 1 revolution at a fixed reference
   (55°, 30 rpm), weighed at rest, before every block, as a per-block
   fill/stationarity index (`flow_checks.csv`).

## Files

- `lowrpm_quantum_salt.log` — raw CSV telemetry (M/E/D/P/F/S/Q lines)
- `stop_trials.csv` — 28 stop trials (Test D + D2) with fitted flow-at-halt
- `quantum.csv` — 108 increments (Test Q), one row per increment
- `flow_checks.csv` — 7 matched-revolution fill indices
- `summary.md` — all fits, tables, and the measurement diagnostics
- `lowrpm_afterflow.png` — Test D/D2
- `quantum_vs_tilt.png` — Test Q

## Measurement caveats that matter for reading this data

- **No hardware tare.** The A&D `Z` command silently stops answering `Q` polls
  while the pan is loaded, so masses are tracked ABSOLUTE from one baseline and
  every yield/afterflow is a difference (the standing offset cancels).
- **The balance is quiet; the weighing *timing* is not.** Consecutive at-rest
  weighs with no powder moved between them agree to **±0.18 mg sd**, and the
  static noise stream is 0.39 mg sd. But Test Q's per-increment yields have a
  lag-1 autocorrelation of **−0.5** and their summed sd does **not** grow as
  √k — the signature of reading noise entering a differenced quantity, not of
  real per-increment scatter. The 400 ms quiet + first-stable-frame weigh is
  too fast after an auger move: it contributes ≈ 21 mg of per-reading noise,
  which swamps the ≈ 6 mg quantum. **Test Q's mean gain is sound; its scatter
  is not measured.** A re-run needs a multi-second settle per increment.
  (The 2026-08-13 Test A data shows the same signature, lag-1 acf −0.41.)
- **The session was not stationary**: the first flow check delivered ~0 g/rev
  (priming) and later checks ranged 0.033–0.105 g/rev. The rpm comparison is
  protected by the blocked design; absolute feed factors are not.

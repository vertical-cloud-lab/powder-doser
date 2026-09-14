# Battery coverage figure

`out/battery_coverage.png` — the full-campaign powders × blocks coverage matrix
(issue #116): what data exists for every powder and every battery block,
aggregated over QC-valid runs from both rounds — round 1 characterization
(2026-08-04 → 2026-08-21, blocks A–E, some with G) and round 2 closed-loop
dosing (2026-09-01 → 2026-09-10, blocks G at 1 g and H at 50/200 mg).
Companion to the round-1 EDA's `R1_coverage.png` (PR #97), which showed one
representative run per powder; this one shows the campaign totals.

- `build_coverage.py` — renders the figure from the committed snapshot;
  `--refresh` first rebuilds the snapshot from MongoDB
  `powder_doser.battery_runs` (connection string in the `MONGODB_URI`
  environment variable, never committed).
- `data/battery_runs_index.csv` — one row per uploaded run document (35 after
  deduplicating one double upload of the 2026-09-03T17:04 salt run): per-block
  trial counts, dose counts by target, QC validity/verdict, grams dispensed.

Cells hold data only from QC-valid runs; hatched † cells mark data that exists
only in excluded runs (fumed silica A–E, barium chloride G+H), and —‡ marks
deliberate close-outs (Si 110/200 G+H gate stand-down, dosing descope of the
two non-dispensing powders). Block F (vibration) never produced a trial —
the DRV2605L haptic driver was dead all campaign and vibration assistance is
excluded from the manuscript's baseline procedure.

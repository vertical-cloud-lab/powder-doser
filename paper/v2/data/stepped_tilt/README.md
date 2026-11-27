# Stepped-tilt trials (18–20 Nov 2026), for the paper

The 30-trial dosing runs @XZaitzeff asked for on
[PR #131](https://github.com/vertical-cloud-lab/powder-doser/pull/131), copied here so that the
manuscript figure and table build from this branch alone.

- **Source:** branch `claude/issue-130-20260721-1807` at commit `401815e` (24 Nov 2026),
  `data/stepped-tilt-trials/`. That folder's
  [README](https://github.com/vertical-cloud-lab/powder-doser/blob/401815e/data/stepped-tilt-trials/README.md)
  describes every run, the per-trial balance CSVs (about 9–10 frames per second), the bench-camera
  frames and the MongoDB documents (`powder_doser.dose_runs`, `doc_type: "three_phase_tilt_trial"`).
- **`raw/`:** the 16 `trials_summary.csv` files (one per launch), byte-identical to the source.
  File names are `<powder>__<run folder>__<launch folder>__trials_summary.csv`.
- **`trials.csv`:** one row per trial, all 133. `protocol` is `final` for the 116 trials on the
  settings that were then frozen (script versions 19d, 19e and 20a–20e) and `development` for the
  17 earlier salt trials (18a–19c), in which the settings were still being changed. Columns beyond
  the source: `error_pct`, `end_stage` (the stage a completed dose ended in), `dose_completed`
  (status `ok` or `overshoot`), `within_1mg`, `within_5pct` (the paper's ±5% acceptance limit) and
  the plot coordinates (`plot_x_symlog` = sign(e)·log10(1 + |e| / mg)).
- **`summary.csv`:** one row per powder, final settings only (the repeatability table of the manuscript).
- **`plot_doses.csv`:** the 103 completed doses, with marker classes, read by `../../steppedtilt.tex`.

Rebuild everything, including `../../figures/steppedtilt.pdf`, with `./build.sh` (gawk and
pdflatex; MiKTeX installs pgfplots on first use). `./build.sh --fetch` first refreshes `raw/` from
the source branch.

## The protocol (final settings)

One three-phase dose per trial, 30 trials per run, unattended:

- **Bulk:** auger at 80 rpm with one 60 ms solenoid tap every 300 ms. The plate starts at 60° and
  steps down 55 → 50 → 45 → 40° in five equal mass bands as the cup fills (or after 3 s without
  flow at an angle), until 0.25 g remains.
- **Fine:** plate at 30°, auger turning steadily at 25 rpm with the same taps, stopped 20 mg before
  the hand-over at 25 mg to go.
- **Tap:** the controller's stock tap stage at 0°: one tap plus a 15° auger turn per cycle, a 1.5 s
  settle, a 5° nudge after three dry cycles, done within ±1 mg.

Targets were 1 g (NaCl), 1.5 g (sodium sulfate, barium chloride) and 2 g (AlSi10Mg, calcium lactate,
xanthan gum). A run stopped itself after two failed trials in a row, at the beaker's mass cap, or
when the balance reported an overload.

## Results on the final settings

| Powder | Target | Trials | Doses | Within ±1 mg | Within ±5% | Median error | Mean ± SD | Median time |
|---|---|---|---|---|---|---|---|---|
| AlSi10Mg | 2 g | 26 | 20 | 11 | 20 | +0.7 mg | +7.6 ± 13.6 mg | 47 s |
| Sodium sulfate | 1.5 g | 23 | 23 | 1 | 12 | +65.5 mg | +90.4 ± 74.2 mg | 12 s |
| Calcium lactate | 2 g | 18 | 18 | 1 | 14 | +46.5 mg | +48.3 ± 43.1 mg | 24 s |
| Barium chloride | 1.5 g | 4 | 0 | – | – | – | – | – |
| Xanthan gum | 2 g | 18 | 18 | 3 | 18 | +5.0 mg | +17.4 ± 23.5 mg | 62 s |
| NaCl | 1 g | 27 | 24 | 3 | 23 | +7.3 mg | +15.6 ± 17.4 mg | 27 s |
| **All** | | **116** | **103** | **19** | **87** | | | |

The six AlSi10Mg trials that did not complete were one priming trial at the start of each launch
(the powder had not yet reached the outlet), three at the end of launch 1 when the tube ran dry,
and one ended by a balance overload. NaCl's three were the tube running dry at the end of the run.
Barium chloride gave nothing in about 113 auger revolutions; it had caked in its tube.

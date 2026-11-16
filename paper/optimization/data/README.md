# Data behind the optimization manuscript

Copies of the files the figures read, so that `figures/make_figures.py` runs on
this branch alone. Each file is byte-identical to its source; nothing was edited.
When a source branch is merged, these copies can be replaced by paths into the
merged tree.

| Path here | Source branch @ commit : path | PR / issue | What it is |
|---|---|---|---|
| `salt-20260929T014732Z/campaign.json` | `claude/issue-164-20260922-1928` @ `930618b` : `data/opt/salt-20260929T014732Z/campaign.json` | #166 / #164 | Campaign configuration: search space, objectives and thresholds, frozen controller parameters, hand-tuned baseline |
| `salt-20260929T014732Z/campaign_records.jsonl` | same branch : `.../campaign_records.jsonl` | #166 | One record per dose (60): 42 campaign doses + 18 validation doses; settings, status, time, error, stop events |
| `salt-20260929T014732Z/zero/trial_<uuid>.json` | same branch : `.../zero/trial_<uuid>.json` | #166 | Full trial documents with 4 Hz balance telemetry (used for Fig. 1a and 3c) |
| `salt-20260929T014732Z/pareto.json`, `ax_snapshot.json`, `report.md` | same branch | #166 | Observed and model Pareto sets, Ax experiment snapshot (model predictions), campaign report |
| `salt-20260929T014732Z/validation_20261006.md` | same branch | #166 | 8-dose validation blocks of `bo-005` and `corner-09` (doses 42 and 43 ran before a restart and count in no block) |
| `production-alsi10mg/README.md` | same branch : `data/opt/production-alsi10mg/README.md` | #166 | 8 g AlSi10Mg dose with the salt settings (7.9928 g, 314.5 s) |
| `powders/versatility_data.csv` | `claude/versatility-figure-gif` @ `d75b7b7` : `paper/figures/versatility/versatility_data.csv` | #173 | Per-powder mg/rev (protocol C, 22.5 deg, 30 rpm) and 1 g closed-loop outcomes, 13 powders |
| `powders/battery_responses.csv` | `claude/issue-163-20260918-2102` @ `e7b7964` : `data/powder-properties/battery_responses.csv` | #163 | Curated #116 battery responses for 12 powders. **Column names use servo-horn degrees:** `ff0/ff45/ff90` are 0, 22.5 and 45 deg of auger tilt (2:1 gear) |
| `powders/literature_powder_properties.csv` | same branch : `data/powder-properties/literature_powder_properties.csv` | #163 | Literature/supplier property values for the material class (not measured on our lots); sources in `literature_powder_properties_long.csv` on that branch |
| `powders/correlation_table.md` | same branch : `data/powder-properties/correlation_table.md` | #163 | Spearman correlations, 42 predictor-response pairs, uncorrected |

The DEM numbers in Fig. 5a are typed into `figures/make_figures.py` from
`sim/dem/README.md` and `sim/dem/figures.py` (`RIG_DATA`) on
`claude/issue-158-20261010-0534` (PR #180); the per-case outflow files there
(`sim/dem/results/cases/*/outflow.txt`, `results/metrics.jsonl`) should replace
the typed values once that PR is merged.

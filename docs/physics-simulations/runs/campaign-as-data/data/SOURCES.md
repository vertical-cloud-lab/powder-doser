# Where these inputs come from

Byte-identical copies, so `extract.py` runs from this checkout alone.

| File | Source branch @ commit : path | What it is |
|---|---|---|
| `salt_trials/trial_*.json` (60) | `claude/issue-179-20261015-2206` @ `ec30713` : `paper/optimization/data/salt-20260929T014732Z/zero/` | The salt campaign's spooled trial documents (#166), one per dose, written by the Pi Zero executor (`opt_dose_capture.py`): settings, outcomes, stop events, covariates and balance telemetry |
| `salt_trials.sha256` | made here | sha256 of each trial file |

Also read, from elsewhere in this survey:
* `../ml-property-dose/data/salt_campaign_records.jsonl`: the campaign's per-dose records, for each dose's label
  and mode (the trial documents carry only the uuid).
* `../heldout-powders/data/rate_summary.csv` and `battery_responses.csv`: Sam's salt fingerprint (#116) and #163's
  pooled values.

Tilts in the trial documents are mounting-plate degrees (the 2:1 servo gear is folded in by the firmware), the same
physical angle as the 0 / 22.5 / 45° of `rate_summary.csv`.

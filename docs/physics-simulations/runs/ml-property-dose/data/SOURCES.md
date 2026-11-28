# Where these input tables come from

Byte-identical copies, so `ml_property_dose.py` and `consistency.py` run from this checkout alone.

| File | Source branch @ commit : path | sha256 | What it is |
|---|---|---|---|
| `trials.csv` | `copilot/draft-base-manuscript` @ `963fdba` : `paper/figures/candidates/data/trials.csv` | `6f7887bd…b71774` | Sam's #116 battery, one row per trial (block A noise, B hold, C single revolutions at three tilts, D speeds, E taps) for all 19 runs |
| `runs.csv` | same : `paper/figures/candidates/data/runs.csv` | `58dc1493…e06311` | One row per run: powder, QC verdict, whether it can be pooled |
| `salt_campaign_records.jsonl` | `claude/issue-179-20261015-2206` @ `ec30713` : `paper/optimization/data/salt-20260929T014732Z/campaign_records.jsonl` | `2eea189b…2e0d8d` | The 60 doses of the salt BO campaign (#166): settings, outcome, time, error, taps and stop events. Used only by `consistency.py` |

`trials.csv` is used only for the replicate noise of the fingerprint (the six protocol C revolutions at 45°).
The per-powder summary, the #163 handbook properties and their ranges are read from
[`../heldout-powders/data/`](../../heldout-powders/data/SOURCES.md), and the DEM-chain predictions from
[`../heldout-powders/predictions.json`](../../heldout-powders/predictions.json).

Tilt values in `trials.csv` are servo settings (0, 45, 90), which are physical tube angles of 0, 22.5 and 45° (2:1 gear).

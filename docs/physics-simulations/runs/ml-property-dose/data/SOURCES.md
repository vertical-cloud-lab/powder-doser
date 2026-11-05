# Where these input tables come from

Byte-identical copies, so `ml_property_dose.py` runs from this checkout alone.

| File | Source branch @ commit : path | sha256 | What it is |
|---|---|---|---|
| `trials.csv` | `copilot/draft-base-manuscript` @ `963fdba` : `paper/figures/candidates/data/trials.csv` | `6f7887bd…b71774` | Sam's #116 battery, one row per trial (block A noise, B hold, C single revolutions at three tilts, D speeds, E taps) for all 19 runs |
| `runs.csv` | same : `paper/figures/candidates/data/runs.csv` | `58dc1493…e06311` | One row per run: powder, QC verdict, whether it can be pooled |

`trials.csv` is used only for the replicate noise of the fingerprint (the six protocol C revolutions at 45°).
The per-powder summary, the #163 handbook properties and their ranges are read from
[`../heldout-powders/data/`](../../heldout-powders/data/SOURCES.md), and the DEM-chain predictions from
[`../heldout-powders/predictions.json`](../../heldout-powders/predictions.json).

Tilt values in `trials.csv` are servo settings (0, 45, 90), which are physical tube angles of 0, 22.5 and 45° (2:1 gear).

# Where these input tables come from

Byte-identical copies, so `predict.py` runs from this folder alone.

| File | Source branch @ commit : path | What it is |
|---|---|---|
| `rate_summary.csv` | `copilot/draft-base-manuscript` @ `963fdba` : `paper/figures/rate_eda/out/rate_summary.csv` | Sam's paper (#116 battery, round 1): one row per powder (13). mg/rev at 0, 22.5 and 45° tube tilt from protocol C (30 rpm, 6 single revolutions per tilt), speed exponent from protocol D, tap quantum, 15 s static hold |
| `dose_summary_by_powder_target.csv` | same : `paper/figures/data/dose_summary_by_powder_target.csv` | Closed-loop doses (blocks G and H) per powder and target: errors, pass rates, times |
| `literature_powder_properties.csv` | `claude/issue-163-20260918-2102` @ `e7b7964` : `data/powder-properties/literature_powder_properties.csv` | #163: literature or supplier values for each material class (not measured on the lab's lots). 12 powders; fumed silica has none |
| `literature_powder_properties_long.csv` | same : `data/powder-properties/literature_powder_properties_long.csv` | The same values with ranges, how specific each source is, and URLs |
| `battery_responses.csv` | same : `data/powder-properties/battery_responses.csv` | #163's curated responses (salt pooled over two runs); kept for comparison, not used by `predict.py` |

Tilt columns in `rate_summary.csv` are physical tube angles (0, 22.5, 45°). In `battery_responses.csv`,
`ff0/ff45/ff90` are the servo settings for the same three angles (2:1 tilt gear).

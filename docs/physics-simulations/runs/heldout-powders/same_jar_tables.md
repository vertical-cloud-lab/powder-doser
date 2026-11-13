### Predictions for each jar, written before the jars are measured

Line: AoR = 45.15 − 4.30 × log<sub>10</sub>(mg/rev at 45°), fitted on the 12 handbook values (in-sample RMSE 3.07°, leave-one-out 3.53°). DEM: the path position that reproduces the jar's mg/rev at 45° and 22.5° (density-corrected), its DEM repose angle plus the mean offset +8.36°. Both are on the handbook scale; a different AoR method on the jars shifts every value by about the same amount.

| jar | handbook AoR (range) | mg/rev at 45°, Aug | side of the step | AoR, line | AoR, DEM path |
|---|---|---|---|---|---|
| AlSi10Mg | 30° (25–39) | 339 | below | 34.3° | 31.2° |
| Si 75–150 µm | 36° (32–42) | 302 | below | 34.5° | 29.9° |
| salt | 32° (30–38) | 265 | below | 34.7° | 36.2° |
| Na₂SO₄ | 32° (30–36) | 244 | below | 34.9° | 37.5° |
| Ca lactate | 40° (32–48) | 232 | below | 35.0° | 23.8° |
| BaCl₂ | 34° (28–40) | 200 | below | 35.3° | 39.0° |
| xanthan | 35° (28–42) | 187 | below | 35.4° | 28.0° |
| white rice flour | 45° (38.1–52.8) | 37.1 | above | 38.4° | 43.1° |
| alginate | 42° (34–50) | 10.9 | above | 40.7° | 44.5° |
| CMC | 41° (38–50) | 9.35 | above | 41.0° | 43.5° |
| Si <44 µm | 43° (38–50) | 1.2 | above | 44.8° | 49.1° |
| brown rice flour | 47° (40–55) | 0.2 | above | 48.2° | 51.4° |
| fumed silica | – | 5.57 (under the 6.1 mg noise floor) | above | ≥ 41.8° | – |

**Criteria**

* **C1** One AoR threshold separates the jars that convey at 45° (≥ 50 mg/rev: AlSi10Mg, Si 75–150 µm, salt, Na₂SO₄, Ca lactate, BaCl₂, xanthan) from the rest, fumed silica included (13 of 13).
* **C2** The Spearman ρ between the jars' measured AoR and log10 mg/rev at 45° (the 12 jars with August data above the floor) is at least as strong as with the handbook values: ρ ≤ −0.84.
* **C3** The line AoR = 45.15 − 4.30 log10(mg/rev at 45°), fitted on the handbook values, predicts the jars' measured AoR with RMSE below 3.5° once one common offset (the difference between methods) is removed; refitted leave-one-jar-out on the measured values, also below 3.5°.
* **C4** Among the 7 jars that convey, the measured AoR rises with the DEM path's value (Spearman ρ ≥ +0.71, one-sided p < 0.05 for 7 jars). The DEM reads their spread in solid volume per revolution as a spread in friction; the line reads it as noise (it puts all 7 at 34–35.5°).

### Handbook spread

Published AoR ranges are 6–16° wide (median 13°). Read as the uncertainty in each jar's AoR, that is 3.21–3.71° RMS (range = ±2 SD, or uniform). 8 of 12 ranges straddle the 40.5° step. Of the handbook AoR's variance across the 12 powders (31.7 deg²), 32–43 % would be that spread (reliability 0.57–0.68). Correcting the linear AoR trend for that spread (errors in variables) leaves a residual share of the scatter of -0.19 to 0.00, i.e. nothing: the spread alone can account for all of it. (n = 12, and the trend is closer to a step than a line, so read this as "the handbook data cannot rule out a near-perfect relation", not as proof of one.)

### Solid volume per revolution, the 7 powders that convey (45°, 30 rpm)

| powder | mg/rev | ÷ particle density (mm³ solid) | ÷ handbook bulk density (mm³ bulk) | handbook d50 (µm) | grains across the 1.07 mm annulus (coarse–best–fine) |
|---|---|---|---|---|---|
| BaCl₂ | 200 | 65 | 154 | 300 | 1.8–3.6–10.7 |
| Na₂SO₄ | 244 | 91 | 174 | 135 | 4.3–7.9–14.3 |
| salt | 265 | 122 | 223 | 425 | 2.1–2.5–3.6 |
| xanthan | 187 | 123 | 301 | 90 | 7.1–11.9–17.8 |
| AlSi10Mg | 339 | 127 | 251 | 42 | 22.3–25.5–26.8 |
| Si 75–150 µm | 302 | 130 | 242 | 106 | 7.1–10.1–14.3 |
| Ca lactate | 232 | 156 | 581 | 220 | 3.6–4.9–7.1 |

CV 25 % by particle density, 52 % by handbook bulk density. Within 6 % of the median (122.9 mm³): salt, xanthan, AlSi10Mg, Si 75–150 µm. The twin without cohesion: 135.4 mm³ at 0.425 mm and 250.8 mm³ at 0.35 mm (1.853×); a Beverloo slot through those two points (k = 1.869) gives 923.3 mm³ at 42 µm.

### A powder that has never been dosed

`python same_jar.py new <AoR> <particle density>`, models fitted on all 12. Example, AoR 32.0°, 2.7 g/cm³ (mg/rev):

```
{
 "45": {
  "line_mg_rev": 397.4,
  "monotone_mg_rev": 243.5,
  "dem_chain_mg_rev": 374.4,
  "dem_offset_deg": 6.25,
  "if_it_conveys_solid_volume_rule_mg_rev": 332.0
 },
 "22p5": {
  "line_mg_rev": 309.4,
  "monotone_mg_rev": 209.9,
  "dem_chain_mg_rev": 183.8,
  "dem_offset_deg": 6.75
 }
}
```


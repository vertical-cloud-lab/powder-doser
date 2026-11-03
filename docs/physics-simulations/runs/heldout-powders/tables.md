### Leave-one-powder-out scores (12 powders)

RMSE and median error are in log<sub>10</sub>(mg/rev) and as a factor; ρ is the Spearman rank correlation of the held-out predictions with the measurements; the last column counts powders put on the right side of 50 mg/rev at 45° (7 convey, 5 do not).

| model | 45°: RMSE | median error | ρ | flow class | 22.5°: RMSE | median error | ρ | flow class |
|---|---|---|---|---|---|---|---|---|
| training mean (no information) | 1.12 | 6.3× | -1.00 | 2/12 | 1.23 | 7.4× | -1.00 | 4/12 |
| log mg/rev linear in literature AoR (2 fitted) | 0.74 | 2.5× | +0.81 | 11/12 | 0.84 | 3.2× | +0.73 | 11/12 |
| … plus log particle density (3 fitted) | 0.73 | 3.7× | +0.82 | 10/12 | 0.85 | 6.4× | +0.73 | 9/12 |
| monotone (isotonic) fit on AoR | 0.82 | 1.4× | +0.78 | 11/12 | 0.88 | 1.6× | +0.70 | 11/12 |
| linear in log Bond number from d50 (2 fitted) | 1.07 | 4.5× | +0.13 | 7/12 | 1.21 | 4.2× | -0.04 | 7/12 |
| Beverloo through the core-tip annulus, no fit | 1.56 | 4.5× | +0.33 | 7/12 | 1.65 | 4.3× | +0.43 | 7/12 |
| Beverloo, fitted log offset (1 fitted) | 1.13 | 5.1× | +0.03 | 6/12 | 1.25 | 5.6× | +0.03 | 5/12 |
| **DEM chain, no fitted parameter** | 1.23 | 5.5× | +0.84 | 9/12 | 1.53 | 6.0× | +0.63 | 9/12 |
| DEM chain, no fit, bulk-density scaling | 1.35 | 8.6× | +0.86 | 9/12 | 1.55 | 8.3× | +0.75 | 8/12 |
| **DEM chain, fitted AoR offset (1 fitted)** | 0.71 | 1.9× | +0.80 | 11/12 | 0.95 | 1.4× | +0.79 | 11/12 |
| DEM chain, fitted offset and log scale (2 fitted) | 0.72 | 1.8× | +0.76 | 11/12 | 1.02 | 3.4× | +0.60 | 11/12 |

Fitted AoR offset Δ across the 12 folds: median 6.25° (range 4.5–7°) at 45°, median 6.75° (range 5.25–8°) at 22.5°.

Paired comparison of per-powder absolute errors (Wilcoxon signed-rank, 12 powders):

| tilt | comparison | powders where the first is better / worse | median difference (log<sub>10</sub>) | p |
|---|---|---|---|---|
| 45° | dem_shift vs aor_ols | 7 / 5 | -0.08 | 0.79 |
| 45° | dem_shift vs aor_iso | 5 / 7 | +0.03 | 0.68 |
| 45° | dem0 vs aor_ols | 3 / 9 | +0.50 | 0.08 |
| 22.5° | dem_shift vs aor_ols | 9 / 3 | -0.27 | 0.11 |
| 22.5° | dem_shift vs aor_iso | 6 / 6 | -0.00 | 0.97 |
| 22.5° | dem0 vs aor_ols | 5 / 7 | +0.56 | 0.20 |

Literature AoR redrawn uniformly within each published range (200 draws), LOPO repeated:

| tilt | model | median RMSE | 10–90 % | median flow class | DEM chain better in |
|---|---|---|---|---|---|
| 45° | aor_ols | 0.87 | 0.66–1.05 | 10/12 |  |
| 45° | dem_shift | 0.92 | 0.57–1.23 | 10/12 | 42 % of draws |
| 22.5° | aor_ols | 1.00 | 0.79–1.15 | 10/12 |  |
| 22.5° | dem_shift | 1.18 | 0.73–1.57 | 10/12 | 26 % of draws |

### Per powder at 45° (mg/rev; held-out predictions)

| powder | literature AoR (range) | measured | DEM chain, no fit | DEM chain, fitted offset | AoR regression | DEM no-fit over the AoR range |
|---|---|---|---|---|---|---|
| AlSi10Mg | 30° | 339 | 200 | 391 | 1.14e+03 | 4.25–378 |
| Si (110/200 mesh) | 36° | 302 | 23 | 185 | 82.6 | 0.57–110 |
| NaCl (control) | 32° | 265 | 102 | 300 | 437 | 7.11–162 |
| Sodium sulfate | 32° | 244 | 126 | 369 | 446 | 26.2–200 |
| Calcium lactate | 40° | 232 | 1.17 | 30.2 | 17.2 | 0.1–70.5 |
| Barium chloride | 34° | 200 | 68.9 | 390 | 191 | 2.43–368 |
| Xanthan gum | 35° | 187 | 23.2 | 152 | 129 | 0.37–181 |
| White rice flour | 45° | 37.1 | 0.103 | 0.847 | 1.86 | 0.1–4.51 |
| Sodium alginate | 42° | 10.9 | 0.4 | 20.8 | 10.6 | 0.1–36.7 |
| CMC | 41° | 9.35 | 0.697 | 29.4 | 16.2 | 0.1–5.26 |
| Si (-325 mesh) | 43° | 1.2 | 0.321 | 23 | 10.3 | 0.11–7.66 |
| Brown rice flour | 47° | 0.2 | 0.1 | 0.982 | 4.63 | 0.1–1.14 |

### Inverse: each held-out powder's literature AoR from its measured mg/rev

| model | RMSE (deg) | MAE (deg) | ρ |
|---|---|---|---|
| training mean | 5.9 | 5.4 | +nan |
| linear in log mg/rev at 45° | 3.5 | 2.9 | +0.70 |
| DEM path, both tilts, mean offset | 7.0 | 5.7 | +0.64 |
| DEM path, no offset | 10.5 | 8.4 | +0.64 |

### Few-shot: 45° from the same powder's measured 22.5° value

| model | RMSE | median error | ρ |
|---|---|---|---|
| training powders' median 45/22.5 ratio | 0.36 | 1.24× | +0.90 |
| DEM path (22.5° → position → 45°) | 0.48 | 1.57× | +0.93 |

### Speed: effective exponent a (mg/s ∝ rpm<sup>a</sup>) at 22.5°

| | 30 rpm (mg/rev) | 90 rpm (mg/rev) | a |
|---|---|---|---|
| DEM P1 | 138.4 | 114.2 | 0.82 |
| DEM k750 | 132.1 | 47.1 | 0.06 |
| measured, the 7 powders that convey (protocol D, 15–90 rpm) | | | 0.65 (range 0.53–0.80) |
| measured, the 4 poor powders with an exponent | | | 1.11 (range 0.85–1.36) |


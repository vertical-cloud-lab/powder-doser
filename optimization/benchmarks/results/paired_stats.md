# Paired analysis (seed-cluster bootstrap)

12 design cells x 30 seed clusters; 4000 bootstrap resamples of whole seed clusters (all cells and methods for a sampled seed move together). Estimand: equal-weight mean over cells of the per-cell mean paired difference. A CI excluding 0 indicates a difference robust to seed-level noise; with 30 clusters these intervals are still coarse.

### Failure modes (rates over all doses per method)

| method | timeout % | stalled % | error % | overshoot_abort % |
|---|---|---|---|---|
| three_phase | 100 | 0 | 0 | 0 |
| three_phase_vel | 100 | 0 | 0 | 0 |
| rate_pi_kf | 52 | 0 | 0 | 0 |
| dual_ukf | 18 | 0 | 0 | 0 |
| mpc | 61 | 0 | 0 | 0 |
| bangbang_ff | 0 | 0 | 0 | 0 |
| bangbang_safe | 0 | 0 | 0 | 0 |
| bangbang_trim | 0 | 0 | 0 | 10 |

### three_phase_vel − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -1.70 **\*** | [-2.20, -1.15] |  |
| time (s, cens. 300) | -0.03 | [-0.08, +0.00] |  |
| taps | +14.15 **\*** | [+12.93, +15.41] |  |
| within ±5 mg | +0.00 | [+0.00, +0.01] | 1 / 0 |
| overshoot (strict) | +0.00 | [+0.00, +0.00] | 0 / 0 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +0.00 |
| AlSi10Mg | nominal | 2.0 | -3.23 |
| AlSi10Mg | stressed | 0.3 | +0.00 |
| AlSi10Mg | stressed | 2.0 | -2.97 |
| lactose | nominal | 0.3 | +0.00 |
| lactose | nominal | 2.0 | -4.50 |
| lactose | stressed | 0.3 | +0.00 |
| lactose | stressed | 2.0 | -3.01 |
| salt | nominal | 0.3 | +0.00 |
| salt | nominal | 2.0 | -3.55 |
| salt | stressed | 0.3 | +0.00 |
| salt | stressed | 2.0 | -3.15 |

</details>

### rate_pi_kf − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +19.24 **\*** | [+16.20, +22.10] |  |
| time (s, cens. 300) | -61.75 **\*** | [-67.73, -55.81] |  |
| taps | +19.41 **\*** | [+15.72, +23.11] |  |
| within ±5 mg | +0.26 **\*** | [+0.19, +0.33] | 94 / 0 |
| overshoot (strict) | +0.02 **\*** | [+0.01, +0.04] | 8 / 0 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -21.60 |
| AlSi10Mg | nominal | 2.0 | +132.34 |
| AlSi10Mg | stressed | 0.3 | -24.89 |
| AlSi10Mg | stressed | 2.0 | +129.37 |
| lactose | nominal | 0.3 | -16.73 |
| lactose | nominal | 2.0 | +4.41 |
| lactose | stressed | 0.3 | -25.27 |
| lactose | stressed | 2.0 | +57.08 |
| salt | nominal | 0.3 | -18.76 |
| salt | nominal | 2.0 | +3.40 |
| salt | stressed | 0.3 | -20.34 |
| salt | stressed | 2.0 | +31.94 |

</details>

### dual_ukf − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -24.20 **\*** | [-24.85, -23.53] |  |
| time (s, cens. 300) | -77.78 **\*** | [-85.91, -69.19] |  |
| taps | -25.40 **\*** | [-29.09, -21.77] |  |
| within ±5 mg | +0.43 **\*** | [+0.30, +0.56] | 154 / 0 |
| overshoot (strict) | +0.01 **\*** | [+0.00, +0.03] | 5 / 0 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -22.10 |
| AlSi10Mg | nominal | 2.0 | -28.44 |
| AlSi10Mg | stressed | 0.3 | -25.98 |
| AlSi10Mg | stressed | 2.0 | -33.84 |
| lactose | nominal | 0.3 | -16.50 |
| lactose | nominal | 2.0 | -22.02 |
| lactose | stressed | 0.3 | -24.36 |
| lactose | stressed | 2.0 | -32.56 |
| salt | nominal | 0.3 | -17.36 |
| salt | nominal | 2.0 | -20.94 |
| salt | stressed | 0.3 | -18.99 |
| salt | stressed | 2.0 | -27.32 |

</details>

### mpc − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -19.83 **\*** | [-20.79, -18.89] |  |
| time (s, cens. 300) | -30.52 **\*** | [-35.60, -25.48] |  |
| taps | +17.49 **\*** | [+13.58, +21.39] |  |
| within ±5 mg | +0.22 **\*** | [+0.14, +0.30] | 78 / 0 |
| overshoot (strict) | +0.01 | [+0.00, +0.02] | 3 / 0 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -19.14 |
| AlSi10Mg | nominal | 2.0 | -21.94 |
| AlSi10Mg | stressed | 0.3 | -20.29 |
| AlSi10Mg | stressed | 2.0 | -24.75 |
| lactose | nominal | 0.3 | -16.53 |
| lactose | nominal | 2.0 | -20.57 |
| lactose | stressed | 0.3 | -23.24 |
| lactose | stressed | 2.0 | -26.21 |
| salt | nominal | 0.3 | -15.19 |
| salt | nominal | 2.0 | -17.60 |
| salt | stressed | 0.3 | -14.95 |
| salt | stressed | 2.0 | -17.55 |

</details>

### bangbang_ff − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +493.38 **\*** | [+485.86, +501.23] |  |
| time (s, cens. 300) | -295.60 **\*** | [-295.61, -295.58] |  |
| taps | -97.19 **\*** | [-98.72, -95.62] |  |
| within ±5 mg | -0.00 | [-0.01, +0.00] | 0 / 1 |
| overshoot (strict) | +0.00 | [+0.00, +0.00] | 0 / 0 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +131.25 |
| AlSi10Mg | nominal | 2.0 | +992.23 |
| AlSi10Mg | stressed | 0.3 | +134.32 |
| AlSi10Mg | stressed | 2.0 | +1150.12 |
| lactose | nominal | 0.3 | +64.57 |
| lactose | nominal | 2.0 | +671.30 |
| lactose | stressed | 0.3 | +73.76 |
| lactose | stressed | 2.0 | +1070.09 |
| salt | nominal | 0.3 | +60.40 |
| salt | nominal | 2.0 | +639.60 |
| salt | stressed | 0.3 | +67.13 |
| salt | stressed | 2.0 | +865.81 |

</details>

### bangbang_safe − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +571.53 **\*** | [+565.10, +578.16] |  |
| time (s, cens. 300) | -295.82 **\*** | [-295.84, -295.81] |  |
| taps | -97.19 **\*** | [-98.75, -95.62] |  |
| within ±5 mg | -0.00 | [-0.01, +0.00] | 0 / 1 |
| overshoot (strict) | +0.00 | [+0.00, +0.00] | 0 / 0 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +251.45 |
| AlSi10Mg | nominal | 2.0 | +999.06 |
| AlSi10Mg | stressed | 0.3 | +247.11 |
| AlSi10Mg | stressed | 2.0 | +1153.14 |
| lactose | nominal | 0.3 | +239.07 |
| lactose | nominal | 2.0 | +677.85 |
| lactose | stressed | 0.3 | +232.24 |
| lactose | stressed | 2.0 | +1072.58 |
| salt | nominal | 0.3 | +236.57 |
| salt | nominal | 2.0 | +645.11 |
| salt | stressed | 0.3 | +234.79 |
| salt | stressed | 2.0 | +869.43 |

</details>

### bangbang_trim − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -24.10 **\*** | [-25.00, -23.16] |  |
| time (s, cens. 300) | -216.60 **\*** | [-223.77, -208.85] |  |
| taps | -79.54 **\*** | [-82.05, -77.07] |  |
| within ±5 mg | +0.55 **\*** | [+0.46, +0.63] | 199 / 1 |
| overshoot (strict) | +0.22 **\*** | [+0.15, +0.29] | 78 / 0 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -20.35 |
| AlSi10Mg | nominal | 2.0 | -26.61 |
| AlSi10Mg | stressed | 0.3 | -26.01 |
| AlSi10Mg | stressed | 2.0 | -33.87 |
| lactose | nominal | 0.3 | -11.96 |
| lactose | nominal | 2.0 | -22.83 |
| lactose | stressed | 0.3 | -24.97 |
| lactose | stressed | 2.0 | -33.01 |
| salt | nominal | 0.3 | -16.97 |
| salt | nominal | 2.0 | -22.45 |
| salt | stressed | 0.3 | -20.71 |
| salt | stressed | 2.0 | -29.46 |

</details>

### rate_pi_kf − dual_ukf

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +43.45 **\*** | [+40.34, +46.52] |  |
| time (s, cens. 300) | +16.03 **\*** | [+8.26, +23.03] |  |
| taps | +44.81 **\*** | [+41.30, +48.41] |  |
| within ±5 mg | -0.17 **\*** | [-0.25, -0.08] | 32 / 92 |
| overshoot (strict) | +0.01 | [-0.01, +0.03] | 7 / 4 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +0.49 |
| AlSi10Mg | nominal | 2.0 | +160.78 |
| AlSi10Mg | stressed | 0.3 | +1.09 |
| AlSi10Mg | stressed | 2.0 | +163.22 |
| lactose | nominal | 0.3 | -0.23 |
| lactose | nominal | 2.0 | +26.42 |
| lactose | stressed | 0.3 | -0.91 |
| lactose | stressed | 2.0 | +89.64 |
| salt | nominal | 0.3 | -1.39 |
| salt | nominal | 2.0 | +24.34 |
| salt | stressed | 0.3 | -1.35 |
| salt | stressed | 2.0 | +59.25 |

</details>

### rate_pi_kf − mpc

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +39.08 **\*** | [+35.94, +42.24] |  |
| time (s, cens. 300) | -31.23 **\*** | [-37.43, -25.22] |  |
| taps | +1.92 | [-2.23, +6.12] |  |
| within ±5 mg | +0.04 | [-0.00, +0.09] | 51 / 35 |
| overshoot (strict) | +0.01 | [-0.00, +0.03] | 8 / 3 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -2.46 |
| AlSi10Mg | nominal | 2.0 | +154.28 |
| AlSi10Mg | stressed | 0.3 | -4.60 |
| AlSi10Mg | stressed | 2.0 | +154.12 |
| lactose | nominal | 0.3 | -0.20 |
| lactose | nominal | 2.0 | +24.98 |
| lactose | stressed | 0.3 | -2.03 |
| lactose | stressed | 2.0 | +83.30 |
| salt | nominal | 0.3 | -3.57 |
| salt | nominal | 2.0 | +21.00 |
| salt | stressed | 0.3 | -5.39 |
| salt | stressed | 2.0 | +49.48 |

</details>

### dual_ukf − mpc

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -4.37 **\*** | [-5.01, -3.71] |  |
| time (s, cens. 300) | -47.26 **\*** | [-53.90, -40.99] |  |
| taps | -42.89 **\*** | [-46.11, -39.68] |  |
| within ±5 mg | +0.21 **\*** | [+0.14, +0.28] | 86 / 10 |
| overshoot (strict) | +0.01 | [+0.00, +0.01] | 4 / 2 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -2.95 |
| AlSi10Mg | nominal | 2.0 | -6.50 |
| AlSi10Mg | stressed | 0.3 | -5.69 |
| AlSi10Mg | stressed | 2.0 | -9.09 |
| lactose | nominal | 0.3 | +0.03 |
| lactose | nominal | 2.0 | -1.44 |
| lactose | stressed | 0.3 | -1.12 |
| lactose | stressed | 2.0 | -6.35 |
| salt | nominal | 0.3 | -2.17 |
| salt | nominal | 2.0 | -3.34 |
| salt | stressed | 0.3 | -4.04 |
| salt | stressed | 2.0 | -9.77 |

</details>

### bangbang_trim − dual_ukf

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +0.10 | [-0.63, +0.96] |  |
| time (s, cens. 300) | -138.82 **\*** | [-147.67, -130.25] |  |
| taps | -54.14 **\*** | [-57.56, -50.84] |  |
| within ±5 mg | +0.12 **\*** | [+0.03, +0.21] | 93 / 49 |
| overshoot (strict) | +0.20 **\*** | [+0.15, +0.27] | 73 / 0 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +1.75 |
| AlSi10Mg | nominal | 2.0 | +1.84 |
| AlSi10Mg | stressed | 0.3 | -0.03 |
| AlSi10Mg | stressed | 2.0 | -0.03 |
| lactose | nominal | 0.3 | +4.55 |
| lactose | nominal | 2.0 | -0.82 |
| lactose | stressed | 0.3 | -0.62 |
| lactose | stressed | 2.0 | -0.45 |
| salt | nominal | 0.3 | +0.39 |
| salt | nominal | 2.0 | -1.51 |
| salt | stressed | 0.3 | -1.72 |
| salt | stressed | 2.0 | -2.14 |

</details>

### bangbang_trim − rate_pi_kf

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -43.34 **\*** | [-46.46, -40.21] |  |
| time (s, cens. 300) | -154.85 **\*** | [-163.81, -146.50] |  |
| taps | -98.95 **\*** | [-103.13, -94.92] |  |
| within ±5 mg | +0.29 **\*** | [+0.23, +0.35] | 136 / 32 |
| overshoot (strict) | +0.19 **\*** | [+0.14, +0.26] | 75 / 5 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +1.25 |
| AlSi10Mg | nominal | 2.0 | -158.95 |
| AlSi10Mg | stressed | 0.3 | -1.12 |
| AlSi10Mg | stressed | 2.0 | -163.24 |
| lactose | nominal | 0.3 | +4.78 |
| lactose | nominal | 2.0 | -27.24 |
| lactose | stressed | 0.3 | +0.30 |
| lactose | stressed | 2.0 | -90.09 |
| salt | nominal | 0.3 | +1.78 |
| salt | nominal | 2.0 | -25.84 |
| salt | stressed | 0.3 | -0.37 |
| salt | stressed | 2.0 | -61.39 |

</details>

\* = 95% cluster-bootstrap CI excludes zero.

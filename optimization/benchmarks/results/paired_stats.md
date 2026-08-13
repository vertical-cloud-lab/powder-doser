# Paired analysis (seed-cluster bootstrap)

12 design cells x 30 seed clusters; 4000 bootstrap resamples of whole seed clusters (all cells and methods for a sampled seed move together). Estimand: equal-weight mean over cells of the per-cell mean paired difference. A CI excluding 0 indicates a difference robust to seed-level noise; with 30 clusters these intervals are still coarse.

### Failure modes (rates over all doses per method)

| method | timeout % | stalled % | error % | overshoot_abort % |
|---|---|---|---|---|
| three_phase | 58 | 0 | 0 | 1 |
| three_phase_vel | 53 | 0 | 0 | 2 |
| rate_pi_kf | 11 | 0 | 0 | 1 |
| dual_ukf | 8 | 0 | 0 | 1 |
| mpc | 25 | 0 | 0 | 1 |
| bo_three_phase | 33 | 0 | 0 | 3 |
| bangbang_ff | 0 | 0 | 0 | 0 |
| bangbang_safe | 0 | 0 | 0 | 0 |
| bangbang_trim | 13 | 0 | 0 | 33 |

### three_phase_vel − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -11.95 **\*** | [-20.15, -5.11] |  |
| time (s, cens. 300) | -10.98 **\*** | [-15.96, -6.09] |  |
| taps | +3.58 **\*** | [+0.67, +6.52] |  |
| within ±5 mg | +0.04 **\*** | [+0.01, +0.07] | 26 / 12 |
| overshoot (strict) | +0.02 | [-0.01, +0.04] | 10 / 4 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +0.00 |
| AlSi10Mg | nominal | 2.0 | +2.60 |
| AlSi10Mg | stressed | 0.3 | +0.00 |
| AlSi10Mg | stressed | 2.0 | -1.36 |
| lactose | nominal | 0.3 | +0.00 |
| lactose | nominal | 2.0 | +1.65 |
| lactose | stressed | 0.3 | +0.00 |
| lactose | stressed | 2.0 | -140.05 |
| salt | nominal | 0.3 | +0.00 |
| salt | nominal | 2.0 | -1.73 |
| salt | stressed | 0.3 | +0.00 |
| salt | stressed | 2.0 | -4.56 |

</details>

### rate_pi_kf − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -22.35 **\*** | [-32.06, -14.27] |  |
| time (s, cens. 300) | -99.46 **\*** | [-109.34, -88.66] |  |
| taps | -19.06 **\*** | [-24.43, -13.41] |  |
| within ±5 mg | +0.24 **\*** | [+0.16, +0.32] | 111 / 24 |
| overshoot (strict) | +0.06 **\*** | [+0.02, +0.12] | 32 / 9 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -4.25 |
| AlSi10Mg | nominal | 2.0 | -4.58 |
| AlSi10Mg | stressed | 0.3 | -2.21 |
| AlSi10Mg | stressed | 2.0 | -6.83 |
| lactose | nominal | 0.3 | -1.62 |
| lactose | nominal | 2.0 | -6.17 |
| lactose | stressed | 0.3 | -8.07 |
| lactose | stressed | 2.0 | -195.77 |
| salt | nominal | 0.3 | -3.67 |
| salt | nominal | 2.0 | -5.26 |
| salt | stressed | 0.3 | -7.52 |
| salt | stressed | 2.0 | -22.22 |

</details>

### dual_ukf − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -24.10 **\*** | [-33.02, -16.70] |  |
| time (s, cens. 300) | -78.84 **\*** | [-88.73, -68.23] |  |
| taps | -19.24 **\*** | [-25.41, -12.92] |  |
| within ±5 mg | +0.30 **\*** | [+0.22, +0.38] | 128 / 21 |
| overshoot (strict) | +0.04 **\*** | [+0.01, +0.08] | 24 / 8 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -2.70 |
| AlSi10Mg | nominal | 2.0 | -4.21 |
| AlSi10Mg | stressed | 0.3 | -1.00 |
| AlSi10Mg | stressed | 2.0 | -6.09 |
| lactose | nominal | 0.3 | -1.63 |
| lactose | nominal | 2.0 | -6.50 |
| lactose | stressed | 0.3 | -10.73 |
| lactose | stressed | 2.0 | -231.29 |
| salt | nominal | 0.3 | +2.78 |
| salt | nominal | 2.0 | -4.72 |
| salt | stressed | 0.3 | -1.42 |
| salt | stressed | 2.0 | -21.72 |

</details>

### mpc − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -24.87 **\*** | [-34.66, -17.34] |  |
| time (s, cens. 300) | -34.61 **\*** | [-43.72, -25.04] |  |
| taps | +14.72 **\*** | [+9.17, +20.64] |  |
| within ±5 mg | +0.20 **\*** | [+0.13, +0.26] | 94 / 23 |
| overshoot (strict) | +0.02 | [-0.01, +0.05] | 18 / 11 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -4.43 |
| AlSi10Mg | nominal | 2.0 | -2.03 |
| AlSi10Mg | stressed | 0.3 | -2.10 |
| AlSi10Mg | stressed | 2.0 | +0.27 |
| lactose | nominal | 0.3 | -1.18 |
| lactose | nominal | 2.0 | -14.34 |
| lactose | stressed | 0.3 | -9.26 |
| lactose | stressed | 2.0 | -230.98 |
| salt | nominal | 0.3 | -3.66 |
| salt | nominal | 2.0 | -4.85 |
| salt | stressed | 0.3 | -7.31 |
| salt | stressed | 2.0 | -18.51 |

</details>

### bo_three_phase − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | -1.62 | [-13.10, +9.49] |  |
| time (s, cens. 300) | -36.79 **\*** | [-44.61, -28.45] |  |
| taps | -21.00 **\*** | [-25.83, -15.71] |  |
| within ±5 mg | +0.14 **\*** | [+0.08, +0.19] | 77 / 27 |
| overshoot (strict) | +0.04 **\*** | [+0.01, +0.07] | 23 / 8 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -3.51 |
| AlSi10Mg | nominal | 2.0 | -1.87 |
| AlSi10Mg | stressed | 0.3 | -0.49 |
| AlSi10Mg | stressed | 2.0 | -3.22 |
| lactose | nominal | 0.3 | -1.43 |
| lactose | nominal | 2.0 | +10.77 |
| lactose | stressed | 0.3 | -7.71 |
| lactose | stressed | 2.0 | +8.49 |
| salt | nominal | 0.3 | -2.08 |
| salt | nominal | 2.0 | -2.94 |
| salt | stressed | 0.3 | -4.68 |
| salt | stressed | 2.0 | -10.76 |

</details>

### bangbang_ff − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +262.25 **\*** | [+253.62, +270.61] |  |
| time (s, cens. 300) | -257.87 **\*** | [-265.64, -249.49] |  |
| taps | -77.90 **\*** | [-82.35, -73.27] |  |
| within ±5 mg | -0.20 **\*** | [-0.27, -0.13] | 6 / 78 |
| overshoot (strict) | +0.28 **\*** | [+0.24, +0.32] | 111 / 9 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +145.28 |
| AlSi10Mg | nominal | 2.0 | +79.00 |
| AlSi10Mg | stressed | 0.3 | +133.70 |
| AlSi10Mg | stressed | 2.0 | +168.90 |
| lactose | nominal | 0.3 | +77.55 |
| lactose | nominal | 2.0 | +640.46 |
| lactose | stressed | 0.3 | +90.39 |
| lactose | stressed | 2.0 | +872.83 |
| salt | nominal | 0.3 | +20.85 |
| salt | nominal | 2.0 | +321.41 |
| salt | stressed | 0.3 | +17.95 |
| salt | stressed | 2.0 | +578.69 |

</details>

### bangbang_safe − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +338.71 **\*** | [+329.25, +348.07] |  |
| time (s, cens. 300) | -258.07 **\*** | [-265.52, -249.60] |  |
| taps | -77.90 **\*** | [-82.30, -73.43] |  |
| within ±5 mg | -0.21 **\*** | [-0.29, -0.14] | 3 / 80 |
| overshoot (strict) | +0.03 **\*** | [+0.01, +0.06] | 23 / 11 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +192.28 |
| AlSi10Mg | nominal | 2.0 | +65.56 |
| AlSi10Mg | stressed | 0.3 | +194.53 |
| AlSi10Mg | stressed | 2.0 | +173.66 |
| lactose | nominal | 0.3 | +279.05 |
| lactose | nominal | 2.0 | +644.52 |
| lactose | stressed | 0.3 | +271.03 |
| lactose | stressed | 2.0 | +875.95 |
| salt | nominal | 0.3 | +229.73 |
| salt | nominal | 2.0 | +331.44 |
| salt | stressed | 0.3 | +226.63 |
| salt | stressed | 2.0 | +580.20 |

</details>

### bangbang_trim − three_phase

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +27.11 **\*** | [+9.66, +44.87] |  |
| time (s, cens. 300) | -176.41 **\*** | [-188.45, -164.33] |  |
| taps | -56.84 **\*** | [-62.16, -51.48] |  |
| within ±5 mg | +0.16 **\*** | [+0.07, +0.23] | 106 / 50 |
| overshoot (strict) | +0.41 **\*** | [+0.36, +0.46] | 154 / 5 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +16.59 |
| AlSi10Mg | nominal | 2.0 | +26.49 |
| AlSi10Mg | stressed | 0.3 | +13.58 |
| AlSi10Mg | stressed | 2.0 | +68.18 |
| lactose | nominal | 0.3 | +6.49 |
| lactose | nominal | 2.0 | +44.20 |
| lactose | stressed | 0.3 | -8.72 |
| lactose | stressed | 2.0 | +189.49 |
| salt | nominal | 0.3 | +3.32 |
| salt | nominal | 2.0 | -5.03 |
| salt | stressed | 0.3 | -6.62 |
| salt | stressed | 2.0 | -22.60 |

</details>

### rate_pi_kf − dual_ukf

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +1.75 | [-1.07, +4.36] |  |
| time (s, cens. 300) | -20.61 **\*** | [-30.10, -11.76] |  |
| taps | +0.18 | [-5.93, +5.46] |  |
| within ±5 mg | -0.06 | [-0.11, +0.00] | 46 / 66 |
| overshoot (strict) | +0.02 | [-0.01, +0.05] | 27 / 20 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | -1.55 |
| AlSi10Mg | nominal | 2.0 | -0.38 |
| AlSi10Mg | stressed | 0.3 | -1.21 |
| AlSi10Mg | stressed | 2.0 | -0.75 |
| lactose | nominal | 0.3 | +0.01 |
| lactose | nominal | 2.0 | +0.33 |
| lactose | stressed | 0.3 | +2.66 |
| lactose | stressed | 2.0 | +35.52 |
| salt | nominal | 0.3 | -6.45 |
| salt | nominal | 2.0 | -0.53 |
| salt | stressed | 0.3 | -6.10 |
| salt | stressed | 2.0 | -0.50 |

</details>

### rate_pi_kf − mpc

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +2.52 **\*** | [+1.27, +4.25] |  |
| time (s, cens. 300) | -64.85 **\*** | [-70.23, -59.31] |  |
| taps | -33.78 **\*** | [-37.23, -30.08] |  |
| within ±5 mg | +0.04 | [-0.01, +0.11] | 59 / 43 |
| overshoot (strict) | +0.04 **\*** | [+0.01, +0.08] | 30 / 14 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +0.19 |
| AlSi10Mg | nominal | 2.0 | -2.55 |
| AlSi10Mg | stressed | 0.3 | -0.11 |
| AlSi10Mg | stressed | 2.0 | -7.11 |
| lactose | nominal | 0.3 | -0.44 |
| lactose | nominal | 2.0 | +8.18 |
| lactose | stressed | 0.3 | +1.20 |
| lactose | stressed | 2.0 | +35.21 |
| salt | nominal | 0.3 | -0.01 |
| salt | nominal | 2.0 | -0.41 |
| salt | stressed | 0.3 | -0.21 |
| salt | stressed | 2.0 | -3.71 |

</details>

### dual_ukf − mpc

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +0.77 | [-1.09, +3.08] |  |
| time (s, cens. 300) | -44.23 **\*** | [-50.49, -38.13] |  |
| taps | -33.96 **\*** | [-37.93, -29.73] |  |
| within ±5 mg | +0.10 **\*** | [+0.04, +0.15] | 67 / 31 |
| overshoot (strict) | +0.03 | [-0.00, +0.05] | 22 / 13 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +1.73 |
| AlSi10Mg | nominal | 2.0 | -2.17 |
| AlSi10Mg | stressed | 0.3 | +1.11 |
| AlSi10Mg | stressed | 2.0 | -6.36 |
| lactose | nominal | 0.3 | -0.45 |
| lactose | nominal | 2.0 | +7.85 |
| lactose | stressed | 0.3 | -1.46 |
| lactose | stressed | 2.0 | -0.31 |
| salt | nominal | 0.3 | +6.45 |
| salt | nominal | 2.0 | +0.13 |
| salt | stressed | 0.3 | +5.89 |
| salt | stressed | 2.0 | -3.20 |

</details>

### bangbang_trim − dual_ukf

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +51.22 **\*** | [+34.30, +69.52] |  |
| time (s, cens. 300) | -97.56 **\*** | [-106.29, -89.73] |  |
| taps | -37.60 **\*** | [-42.04, -33.30] |  |
| within ±5 mg | -0.14 **\*** | [-0.25, -0.03] | 61 / 112 |
| overshoot (strict) | +0.37 **\*** | [+0.32, +0.41] | 148 / 15 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +19.29 |
| AlSi10Mg | nominal | 2.0 | +30.69 |
| AlSi10Mg | stressed | 0.3 | +14.58 |
| AlSi10Mg | stressed | 2.0 | +74.27 |
| lactose | nominal | 0.3 | +8.12 |
| lactose | nominal | 2.0 | +50.70 |
| lactose | stressed | 0.3 | +2.01 |
| lactose | stressed | 2.0 | +420.78 |
| salt | nominal | 0.3 | +0.54 |
| salt | nominal | 2.0 | -0.31 |
| salt | stressed | 0.3 | -5.20 |
| salt | stressed | 2.0 | -0.88 |

</details>

### bangbang_trim − rate_pi_kf

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +49.46 **\*** | [+32.08, +68.28] |  |
| time (s, cens. 300) | -76.95 **\*** | [-86.10, -68.15] |  |
| taps | -37.78 **\*** | [-42.37, -33.48] |  |
| within ±5 mg | -0.09 | [-0.18, +0.01] | 65 / 96 |
| overshoot (strict) | +0.35 **\*** | [+0.30, +0.39] | 137 / 11 |

<details><summary>per-cell mean Δ|error| (mg)</summary>

| powder | context | target g | Δ|e| mg |
|---|---|---|---|
| AlSi10Mg | nominal | 0.3 | +20.83 |
| AlSi10Mg | nominal | 2.0 | +31.07 |
| AlSi10Mg | stressed | 0.3 | +15.79 |
| AlSi10Mg | stressed | 2.0 | +75.02 |
| lactose | nominal | 0.3 | +8.11 |
| lactose | nominal | 2.0 | +50.37 |
| lactose | stressed | 0.3 | -0.65 |
| lactose | stressed | 2.0 | +385.26 |
| salt | nominal | 0.3 | +6.99 |
| salt | nominal | 2.0 | +0.23 |
| salt | stressed | 0.3 | +0.90 |
| salt | stressed | 2.0 | -0.38 |

</details>

\* = 95% cluster-bootstrap CI excludes zero.

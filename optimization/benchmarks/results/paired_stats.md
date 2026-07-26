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

### rate_pi_kf − dual_ukf

| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |
|---|---|---|---|
| |error| (mg) | +1.75 | [-1.07, +4.31] |  |
| time (s, cens. 300) | -20.61 **\*** | [-29.89, -11.75] |  |
| taps | +0.18 | [-5.63, +5.57] |  |
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
| |error| (mg) | +2.52 **\*** | [+1.25, +4.21] |  |
| time (s, cens. 300) | -64.85 **\*** | [-70.51, -59.34] |  |
| taps | -33.78 **\*** | [-37.19, -30.17] |  |
| within ±5 mg | +0.04 | [-0.01, +0.10] | 59 / 43 |
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
| |error| (mg) | +0.77 | [-1.12, +3.00] |  |
| time (s, cens. 300) | -44.23 **\*** | [-50.34, -38.34] |  |
| taps | -33.96 **\*** | [-37.88, -29.93] |  |
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

\* = 95% cluster-bootstrap CI excludes zero.

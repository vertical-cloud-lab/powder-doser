# Benchmark summary

3240 doses. Grid: powders ['AlSi10Mg', 'lactose', 'salt'], contexts ['nominal', 'stressed'], targets [0.3, 2.0] g, 30 seeds/cell. Tolerance ±5 mg; overshoot = true mass > target (strict). All numbers are true post-settle vial mass; controllers saw only the simulated balance.

**Descriptive only** (methods-check review): pooled medians mix powders/contexts/targets and include timeout-censored 300 s doses, so they must not be used to rank methods - see `paired_stats.md` for cell-level paired differences with seed-cluster bootstrap CIs. `time_s` ends at controller declaration and excludes the 1 s scoring settle; `not-ok` counts controller status (timeout/stall/error/overshoot-abort), which is distinct from being outside tolerance. p95 is the 0.95 order statistic of the pooled sample.

### Pooled

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| all | three_phase | 360 | 29.84 | 41.5 | 0 | 0 | 302 | 111 | 360 |
| all | three_phase_vel | 360 | 28.58 | 39.2 | 1 | 0 | 302 | 122 | 359 |
| all | rate_pi_kf | 360 | 9.01 | 176.5 | 26 | 2 | 300 | 136 | 188 |
| all | dual_ukf | 360 | 5.48 | 9.5 | 43 | 1 | 228 | 72 | 63 |
| all | mpc | 360 | 8.35 | 21.1 | 22 | 1 | 300 | 118 | 218 |
| all | bangbang_naive | 360 | 283.05 | 466.3 | 0 | 100 | 6 | 0 | 0 |
| all | bangbang_ff | 360 | 390.62 | 1182.7 | 0 | 0 | 4 | 0 | 0 |
| all | bangbang_safe | 360 | 437.06 | 1186.9 | 0 | 0 | 4 | 0 | 0 |
| all | bangbang_trim | 360 | 4.71 | 14.7 | 55 | 22 | 68 | 11 | 36 |

### By powder

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| AlSi10Mg | three_phase | 120 | 32.48 | 44.7 | 0 | 0 | 301 | 96 | 120 |
| AlSi10Mg | three_phase_vel | 120 | 31.29 | 39.4 | 0 | 0 | 302 | 113 | 120 |
| AlSi10Mg | rate_pi_kf | 120 | 63.28 | 194.2 | 18 | 1 | 301 | 160 | 76 |
| AlSi10Mg | dual_ukf | 120 | 5.32 | 9.0 | 42 | 1 | 222 | 74 | 9 |
| AlSi10Mg | mpc | 120 | 10.40 | 22.4 | 19 | 0 | 301 | 137 | 88 |
| AlSi10Mg | bangbang_naive | 120 | 239.37 | 292.8 | 0 | 100 | 8 | 0 | 0 |
| AlSi10Mg | bangbang_ff | 120 | 585.30 | 1215.3 | 0 | 0 | 4 | 0 | 0 |
| AlSi10Mg | bangbang_safe | 120 | 631.74 | 1215.3 | 0 | 0 | 4 | 0 | 0 |
| AlSi10Mg | bangbang_trim | 120 | 5.10 | 21.9 | 48 | 19 | 82 | 15 | 13 |
| lactose | three_phase | 120 | 29.27 | 42.4 | 1 | 0 | 301 | 111 | 120 |
| lactose | three_phase_vel | 120 | 28.64 | 40.6 | 2 | 0 | 302 | 126 | 119 |
| lactose | rate_pi_kf | 120 | 7.33 | 120.8 | 30 | 3 | 210 | 86 | 57 |
| lactose | dual_ukf | 120 | 5.46 | 9.4 | 47 | 2 | 219 | 65 | 22 |
| lactose | mpc | 120 | 6.85 | 18.3 | 32 | 2 | 242 | 98 | 45 |
| lactose | bangbang_naive | 120 | 306.73 | 475.5 | 0 | 100 | 6 | 0 | 0 |
| lactose | bangbang_ff | 120 | 392.08 | 1142.7 | 0 | 0 | 4 | 0 | 0 |
| lactose | bangbang_safe | 120 | 451.63 | 1142.7 | 0 | 0 | 4 | 0 | 0 |
| lactose | bangbang_trim | 120 | 4.64 | 20.0 | 58 | 30 | 51 | 7 | 18 |
| salt | three_phase | 120 | 26.64 | 37.5 | 0 | 0 | 302 | 112 | 120 |
| salt | three_phase_vel | 120 | 25.03 | 35.6 | 0 | 0 | 302 | 124 | 120 |
| salt | rate_pi_kf | 120 | 7.48 | 89.5 | 32 | 2 | 245 | 85 | 55 |
| salt | dual_ukf | 120 | 5.77 | 10.0 | 40 | 1 | 249 | 76 | 32 |
| salt | mpc | 120 | 9.84 | 21.1 | 14 | 1 | 301 | 118 | 85 |
| salt | bangbang_naive | 120 | 351.17 | 483.7 | 0 | 100 | 6 | 0 | 0 |
| salt | bangbang_ff | 120 | 367.06 | 927.1 | 0 | 0 | 4 | 0 | 0 |
| salt | bangbang_safe | 120 | 430.16 | 932.0 | 0 | 0 | 4 | 0 | 0 |
| salt | bangbang_trim | 120 | 4.46 | 9.2 | 59 | 16 | 78 | 16 | 5 |

### By context

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| nominal | three_phase | 180 | 26.33 | 36.6 | 1 | 0 | 302 | 111 | 180 |
| nominal | three_phase_vel | 180 | 25.27 | 34.8 | 1 | 0 | 302 | 124 | 179 |
| nominal | rate_pi_kf | 180 | 7.48 | 172.9 | 28 | 2 | 289 | 122 | 86 |
| nominal | dual_ukf | 180 | 5.13 | 9.1 | 48 | 3 | 216 | 69 | 17 |
| nominal | mpc | 180 | 6.84 | 17.0 | 31 | 1 | 285 | 108 | 76 |
| nominal | bangbang_naive | 180 | 382.67 | 485.6 | 0 | 100 | 6 | 0 | 0 |
| nominal | bangbang_ff | 180 | 385.29 | 1044.1 | 0 | 0 | 4 | 0 | 0 |
| nominal | bangbang_safe | 180 | 437.04 | 1046.6 | 0 | 0 | 4 | 0 | 0 |
| nominal | bangbang_trim | 180 | 4.41 | 21.3 | 55 | 30 | 44 | 6 | 27 |
| stressed | three_phase | 180 | 33.21 | 44.7 | 0 | 0 | 302 | 102 | 180 |
| stressed | three_phase_vel | 180 | 31.96 | 40.9 | 0 | 0 | 302 | 114 | 180 |
| stressed | rate_pi_kf | 180 | 14.15 | 178.9 | 25 | 2 | 300 | 152 | 102 |
| stressed | dual_ukf | 180 | 5.78 | 9.6 | 38 | 0 | 248 | 80 | 46 |
| stressed | mpc | 180 | 11.25 | 21.9 | 13 | 1 | 301 | 126 | 142 |
| stressed | bangbang_naive | 180 | 229.77 | 333.5 | 0 | 100 | 7 | 0 | 0 |
| stressed | bangbang_ff | 180 | 512.42 | 1205.6 | 0 | 0 | 4 | 0 | 0 |
| stressed | bangbang_safe | 180 | 558.87 | 1206.7 | 0 | 0 | 4 | 0 | 0 |
| stressed | bangbang_trim | 180 | 4.80 | 9.0 | 56 | 13 | 90 | 20 | 9 |

### By target (g)

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| 0.3 | three_phase | 180 | 26.24 | 35.3 | 1 | 0 | 302 | 132 | 180 |
| 0.3 | three_phase_vel | 180 | 26.24 | 35.3 | 1 | 0 | 302 | 132 | 180 |
| 0.3 | rate_pi_kf | 180 | 4.68 | 9.5 | 52 | 4 | 161 | 60 | 16 |
| 0.3 | dual_ukf | 180 | 5.47 | 8.9 | 45 | 1 | 193 | 65 | 19 |
| 0.3 | mpc | 180 | 7.10 | 17.6 | 27 | 1 | 290 | 114 | 81 |
| 0.3 | bangbang_naive | 180 | 287.66 | 408.4 | 0 | 100 | 4 | 0 | 0 |
| 0.3 | bangbang_ff | 180 | 107.39 | 176.7 | 0 | 0 | 3 | 0 | 0 |
| 0.3 | bangbang_safe | 180 | 266.45 | 283.3 | 0 | 0 | 2 | 0 | 0 |
| 0.3 | bangbang_trim | 180 | 4.81 | 18.7 | 53 | 23 | 66 | 15 | 21 |
| 2.0 | three_phase | 180 | 33.94 | 45.5 | 0 | 0 | 302 | 64 | 180 |
| 2.0 | three_phase_vel | 180 | 30.88 | 40.6 | 1 | 0 | 302 | 92 | 179 |
| 2.0 | rate_pi_kf | 180 | 82.42 | 184.5 | 1 | 0 | 302 | 168 | 172 |
| 2.0 | dual_ukf | 180 | 5.49 | 10.7 | 41 | 2 | 254 | 79 | 44 |
| 2.0 | mpc | 180 | 11.16 | 21.9 | 17 | 1 | 301 | 120 | 137 |
| 2.0 | bangbang_naive | 180 | 280.71 | 485.6 | 0 | 100 | 11 | 0 | 0 |
| 2.0 | bangbang_ff | 180 | 979.69 | 1205.6 | 0 | 0 | 6 | 0 | 0 |
| 2.0 | bangbang_safe | 180 | 979.69 | 1206.7 | 0 | 0 | 6 | 0 | 0 |
| 2.0 | bangbang_trim | 180 | 4.57 | 10.6 | 57 | 20 | 72 | 10 | 15 |

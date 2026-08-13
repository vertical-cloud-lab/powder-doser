# Benchmark summary

3600 doses. Grid: powders ['AlSi10Mg', 'lactose', 'salt'], contexts ['nominal', 'stressed'], targets [0.3, 2.0] g, 30 seeds/cell. Tolerance ±5 mg; overshoot = true mass > target (strict). All numbers are true post-settle vial mass; controllers saw only the simulated balance.

**Descriptive only** (methods-check review): pooled medians mix powders/contexts/targets and include timeout-censored 300 s doses, so they must not be used to rank methods - see `paired_stats.md` for cell-level paired differences with seed-cluster bootstrap CIs. `time_s` ends at controller declaration and excludes the 1 s scoring settle; `not-ok` counts controller status (timeout/stall/error/overshoot-abort), which is distinct from being outside tolerance. p95 is the 0.95 order statistic of the pooled sample.

### Pooled

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| all | three_phase | 360 | 8.79 | 133.7 | 22 | 4 | 300 | 88 | 214 |
| all | three_phase_vel | 360 | 7.69 | 42.2 | 26 | 5 | 300 | 90 | 199 |
| all | rate_pi_kf | 360 | 5.24 | 38.7 | 46 | 10 | 149 | 43 | 42 |
| all | dual_ukf | 360 | 4.83 | 9.8 | 52 | 8 | 184 | 55 | 32 |
| all | mpc | 360 | 5.59 | 14.5 | 42 | 6 | 236 | 91 | 93 |
| all | bo_three_phase | 360 | 6.14 | 56.4 | 36 | 8 | 249 | 54 | 129 |
| all | bangbang_naive | 360 | 500.33 | 1013.1 | 0 | 100 | 5 | 0 | 0 |
| all | bangbang_ff | 360 | 139.22 | 1082.4 | 2 | 32 | 4 | 0 | 0 |
| all | bangbang_safe | 360 | 256.18 | 1089.2 | 1 | 7 | 3 | 0 | 0 |
| all | bangbang_trim | 360 | 6.65 | 224.0 | 38 | 45 | 36 | 2 | 164 |

### By powder

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| AlSi10Mg | three_phase | 120 | 7.17 | 22.7 | 25 | 3 | 274 | 90 | 55 |
| AlSi10Mg | three_phase_vel | 120 | 6.35 | 24.1 | 31 | 9 | 246 | 88 | 51 |
| AlSi10Mg | rate_pi_kf | 120 | 5.20 | 8.6 | 47 | 3 | 147 | 42 | 0 |
| AlSi10Mg | dual_ukf | 120 | 5.19 | 9.5 | 48 | 3 | 221 | 78 | 14 |
| AlSi10Mg | mpc | 120 | 5.96 | 18.8 | 34 | 3 | 253 | 111 | 39 |
| AlSi10Mg | bo_three_phase | 120 | 6.00 | 17.4 | 34 | 3 | 269 | 80 | 40 |
| AlSi10Mg | bangbang_naive | 120 | 748.54 | 1091.0 | 0 | 100 | 4 | 0 | 0 |
| AlSi10Mg | bangbang_ff | 120 | 136.09 | 255.9 | 2 | 71 | 4 | 0 | 0 |
| AlSi10Mg | bangbang_safe | 120 | 185.69 | 230.6 | 2 | 21 | 3 | 0 | 0 |
| AlSi10Mg | bangbang_trim | 120 | 21.99 | 217.5 | 15 | 64 | 12 | 0 | 91 |
| lactose | three_phase | 120 | 7.44 | 346.9 | 27 | 8 | 300 | 59 | 74 |
| lactose | three_phase_vel | 120 | 7.42 | 264.5 | 28 | 7 | 300 | 59 | 71 |
| lactose | rate_pi_kf | 120 | 6.13 | 70.8 | 36 | 16 | 231 | 104 | 41 |
| lactose | dual_ukf | 120 | 4.14 | 10.8 | 61 | 18 | 169 | 48 | 10 |
| lactose | mpc | 120 | 5.38 | 13.9 | 45 | 10 | 234 | 92 | 32 |
| lactose | bo_three_phase | 120 | 5.20 | 629.5 | 48 | 18 | 192 | 21 | 38 |
| lactose | bangbang_naive | 120 | 264.42 | 493.9 | 0 | 100 | 6 | 0 | 0 |
| lactose | bangbang_ff | 120 | 359.86 | 1173.2 | 0 | 0 | 4 | 0 | 0 |
| lactose | bangbang_safe | 120 | 431.68 | 1173.2 | 0 | 0 | 4 | 0 | 0 |
| lactose | bangbang_trim | 120 | 5.48 | 1087.8 | 46 | 33 | 82 | 17 | 50 |
| salt | three_phase | 120 | 11.72 | 34.0 | 15 | 0 | 301 | 100 | 85 |
| salt | three_phase_vel | 120 | 10.68 | 27.7 | 20 | 0 | 301 | 114 | 77 |
| salt | rate_pi_kf | 120 | 4.61 | 7.9 | 57 | 11 | 109 | 32 | 1 |
| salt | dual_ukf | 120 | 5.06 | 9.3 | 48 | 2 | 170 | 48 | 8 |
| salt | mpc | 120 | 5.26 | 12.6 | 47 | 3 | 227 | 82 | 22 |
| salt | bo_three_phase | 120 | 6.91 | 23.0 | 26 | 2 | 261 | 68 | 51 |
| salt | bangbang_naive | 120 | 489.59 | 678.0 | 0 | 100 | 5 | 0 | 0 |
| salt | bangbang_ff | 120 | 156.46 | 644.6 | 5 | 25 | 4 | 0 | 0 |
| salt | bangbang_safe | 120 | 255.13 | 644.6 | 0 | 0 | 4 | 0 | 0 |
| salt | bangbang_trim | 120 | 4.80 | 21.9 | 52 | 38 | 32 | 2 | 23 |

### By context

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| nominal | three_phase | 180 | 6.35 | 28.5 | 29 | 4 | 284 | 78 | 78 |
| nominal | three_phase_vel | 180 | 5.89 | 26.3 | 36 | 7 | 261 | 82 | 66 |
| nominal | rate_pi_kf | 180 | 4.82 | 8.6 | 52 | 11 | 131 | 38 | 6 |
| nominal | dual_ukf | 180 | 4.72 | 9.4 | 54 | 7 | 170 | 56 | 12 |
| nominal | mpc | 180 | 5.04 | 11.2 | 50 | 6 | 227 | 88 | 32 |
| nominal | bo_three_phase | 180 | 5.26 | 13.6 | 46 | 10 | 204 | 44 | 36 |
| nominal | bangbang_naive | 180 | 590.95 | 1071.7 | 0 | 100 | 5 | 0 | 0 |
| nominal | bangbang_ff | 180 | 123.74 | 673.3 | 3 | 40 | 4 | 0 | 0 |
| nominal | bangbang_safe | 180 | 251.87 | 679.2 | 2 | 14 | 3 | 0 | 0 |
| nominal | bangbang_trim | 180 | 8.11 | 66.6 | 34 | 53 | 26 | 0 | 93 |
| stressed | three_phase | 180 | 14.59 | 291.7 | 15 | 3 | 301 | 92 | 136 |
| stressed | three_phase_vel | 180 | 14.30 | 57.3 | 17 | 3 | 301 | 98 | 133 |
| stressed | rate_pi_kf | 180 | 5.43 | 52.8 | 41 | 9 | 159 | 48 | 36 |
| stressed | dual_ukf | 180 | 4.95 | 10.8 | 50 | 9 | 193 | 55 | 20 |
| stressed | mpc | 180 | 6.09 | 16.4 | 34 | 5 | 264 | 98 | 61 |
| stressed | bo_three_phase | 180 | 7.54 | 450.0 | 26 | 6 | 300 | 62 | 93 |
| stressed | bangbang_naive | 180 | 438.31 | 764.8 | 0 | 100 | 5 | 0 | 0 |
| stressed | bangbang_ff | 180 | 163.84 | 1136.5 | 2 | 24 | 4 | 0 | 0 |
| stressed | bangbang_safe | 180 | 275.45 | 1152.1 | 0 | 0 | 3 | 0 | 0 |
| stressed | bangbang_trim | 180 | 6.19 | 1015.2 | 42 | 37 | 57 | 8 | 71 |

### By target (g)

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| 0.3 | three_phase | 180 | 6.49 | 21.8 | 30 | 4 | 287 | 90 | 86 |
| 0.3 | three_phase_vel | 180 | 6.49 | 21.8 | 30 | 4 | 287 | 90 | 86 |
| 0.3 | rate_pi_kf | 180 | 5.00 | 8.7 | 50 | 11 | 114 | 33 | 8 |
| 0.3 | dual_ukf | 180 | 4.46 | 10.1 | 58 | 7 | 131 | 40 | 10 |
| 0.3 | mpc | 180 | 4.94 | 9.0 | 51 | 7 | 182 | 73 | 14 |
| 0.3 | bo_three_phase | 180 | 5.44 | 14.8 | 43 | 8 | 200 | 46 | 40 |
| 0.3 | bangbang_naive | 180 | 472.01 | 796.7 | 0 | 100 | 4 | 0 | 0 |
| 0.3 | bangbang_ff | 180 | 84.41 | 232.6 | 3 | 50 | 3 | 0 | 0 |
| 0.3 | bangbang_safe | 180 | 236.34 | 294.7 | 0 | 0 | 2 | 0 | 0 |
| 0.3 | bangbang_trim | 180 | 8.78 | 39.6 | 33 | 64 | 13 | 0 | 97 |
| 2.0 | three_phase | 180 | 11.96 | 291.7 | 14 | 3 | 301 | 82 | 128 |
| 2.0 | three_phase_vel | 180 | 11.26 | 202.4 | 22 | 6 | 300 | 90 | 113 |
| 2.0 | rate_pi_kf | 180 | 5.51 | 56.4 | 43 | 9 | 178 | 52 | 34 |
| 2.0 | dual_ukf | 180 | 5.21 | 9.5 | 46 | 9 | 229 | 67 | 22 |
| 2.0 | mpc | 180 | 6.42 | 17.0 | 33 | 4 | 286 | 108 | 79 |
| 2.0 | bo_three_phase | 180 | 7.70 | 452.5 | 29 | 7 | 296 | 60 | 89 |
| 2.0 | bangbang_naive | 180 | 546.67 | 1071.7 | 0 | 100 | 7 | 0 | 0 |
| 2.0 | bangbang_ff | 180 | 478.66 | 1136.5 | 1 | 14 | 5 | 0 | 0 |
| 2.0 | bangbang_safe | 180 | 503.22 | 1152.1 | 2 | 14 | 5 | 0 | 0 |
| 2.0 | bangbang_trim | 180 | 6.08 | 1015.2 | 43 | 26 | 82 | 16 | 67 |

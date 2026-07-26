# Benchmark summary

720 doses. Grid: powders ['AlSi10Mg', 'lactose', 'salt'], contexts ['nominal', 'stressed'], targets [0.3, 2.0] g, 10 seeds/cell. Tolerance ±5 mg; overshoot = true mass > target (strict). All numbers are true post-settle vial mass; controllers saw only the simulated balance.

### Pooled

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| all | three_phase | 120 | 8.44 | 119.1 | 27 | 2 | 300 | 76 | 70 |
| all | three_phase_vel | 120 | 8.14 | 41.7 | 28 | 2 | 300 | 94 | 66 |
| all | rate_pi_kf | 120 | 4.62 | 48.5 | 58 | 2 | 147 | 45 | 16 |
| all | dual_ukf | 120 | 4.72 | 8.4 | 57 | 5 | 170 | 52 | 10 |
| all | mpc | 120 | 4.81 | 17.4 | 52 | 8 | 228 | 92 | 32 |
| all | bo_three_phase | 120 | 25.60 | 115.8 | 18 | 2 | 301 | 93 | 89 |

### By powder

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| AlSi10Mg | three_phase | 40 | 7.10 | 25.2 | 25 | 2 | 286 | 80 | 21 |
| AlSi10Mg | three_phase_vel | 40 | 7.38 | 25.2 | 25 | 2 | 300 | 124 | 21 |
| AlSi10Mg | rate_pi_kf | 40 | 4.76 | 7.7 | 60 | 0 | 140 | 38 | 0 |
| AlSi10Mg | dual_ukf | 40 | 4.99 | 8.4 | 50 | 0 | 186 | 60 | 4 |
| AlSi10Mg | mpc | 40 | 5.98 | 17.4 | 32 | 0 | 274 | 112 | 15 |
| AlSi10Mg | bo_three_phase | 40 | 26.99 | 133.4 | 22 | 2 | 301 | 276 | 28 |
| lactose | three_phase | 40 | 5.42 | 184.4 | 45 | 5 | 268 | 42 | 16 |
| lactose | three_phase_vel | 40 | 5.33 | 246.7 | 45 | 5 | 259 | 57 | 15 |
| lactose | rate_pi_kf | 40 | 5.56 | 77.5 | 42 | 5 | 207 | 90 | 15 |
| lactose | dual_ukf | 40 | 4.61 | 18.2 | 58 | 12 | 155 | 41 | 5 |
| lactose | mpc | 40 | 3.90 | 53.1 | 70 | 22 | 200 | 72 | 8 |
| lactose | bo_three_phase | 40 | 45.85 | 186.2 | 8 | 0 | 301 | 76 | 36 |
| salt | three_phase | 40 | 16.01 | 33.1 | 10 | 0 | 301 | 104 | 33 |
| salt | three_phase_vel | 40 | 12.38 | 32.0 | 15 | 0 | 301 | 118 | 30 |
| salt | rate_pi_kf | 40 | 4.00 | 9.0 | 72 | 0 | 124 | 39 | 1 |
| salt | dual_ukf | 40 | 4.56 | 7.2 | 62 | 2 | 142 | 44 | 1 |
| salt | mpc | 40 | 4.74 | 14.0 | 52 | 2 | 221 | 84 | 9 |
| salt | bo_three_phase | 40 | 12.69 | 37.5 | 22 | 2 | 300 | 192 | 25 |

### By context

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| nominal | three_phase | 60 | 5.89 | 25.7 | 35 | 3 | 270 | 72 | 26 |
| nominal | three_phase_vel | 60 | 5.81 | 22.9 | 38 | 3 | 255 | 84 | 23 |
| nominal | rate_pi_kf | 60 | 4.16 | 9.0 | 67 | 2 | 135 | 40 | 3 |
| nominal | dual_ukf | 60 | 4.89 | 8.4 | 52 | 3 | 147 | 48 | 4 |
| nominal | mpc | 60 | 4.61 | 9.7 | 60 | 7 | 217 | 89 | 10 |
| nominal | bo_three_phase | 60 | 19.77 | 101.6 | 20 | 3 | 301 | 92 | 40 |
| stressed | three_phase | 60 | 12.92 | 145.0 | 18 | 2 | 301 | 86 | 44 |
| stressed | three_phase_vel | 60 | 14.64 | 119.8 | 18 | 2 | 301 | 99 | 43 |
| stressed | rate_pi_kf | 60 | 5.06 | 57.0 | 50 | 2 | 167 | 56 | 13 |
| stressed | dual_ukf | 60 | 4.47 | 10.2 | 62 | 7 | 178 | 54 | 6 |
| stressed | mpc | 60 | 5.43 | 27.2 | 43 | 10 | 254 | 98 | 22 |
| stressed | bo_three_phase | 60 | 31.44 | 140.9 | 15 | 0 | 301 | 135 | 49 |

### By target (g)

| group | method | n | med \|e\| mg | p95 \|e\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |
|---|---|---|---|---|---|---|---|---|---|
| 0.3 | three_phase | 60 | 6.59 | 27.2 | 33 | 3 | 300 | 96 | 30 |
| 0.3 | three_phase_vel | 60 | 6.59 | 27.2 | 33 | 3 | 300 | 96 | 30 |
| 0.3 | rate_pi_kf | 60 | 4.00 | 8.1 | 67 | 2 | 110 | 33 | 2 |
| 0.3 | dual_ukf | 60 | 4.40 | 13.0 | 68 | 7 | 116 | 39 | 3 |
| 0.3 | mpc | 60 | 4.48 | 8.2 | 65 | 7 | 191 | 80 | 4 |
| 0.3 | bo_three_phase | 60 | 15.57 | 67.6 | 27 | 2 | 301 | 92 | 39 |
| 2.0 | three_phase | 60 | 13.58 | 145.0 | 20 | 2 | 300 | 66 | 40 |
| 2.0 | three_phase_vel | 60 | 8.50 | 119.8 | 23 | 2 | 301 | 94 | 36 |
| 2.0 | rate_pi_kf | 60 | 5.05 | 73.7 | 50 | 2 | 171 | 52 | 14 |
| 2.0 | dual_ukf | 60 | 5.09 | 7.3 | 45 | 3 | 214 | 68 | 7 |
| 2.0 | mpc | 60 | 5.69 | 24.8 | 38 | 10 | 281 | 104 | 28 |
| 2.0 | bo_three_phase | 60 | 37.29 | 140.9 | 8 | 2 | 301 | 146 | 50 |

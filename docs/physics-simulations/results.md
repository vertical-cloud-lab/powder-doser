| Run | Code | Status | Wall time | Key results |
|---|---|---|---|---|
| `dem-liggghts-aor` | — | — | no result.json | — |
| `dem-liggghts-tap` | — | — | no result.json | — |
| `dem-liggghts-shear` | — | — | no result.json | — |
| `dem-liggghts-spread` | — | — | no result.json | — |
| `dem-lammps-shear-mui` | — | — | no result.json | — |
| `dem-lammps-charge` | — | — | no result.json | — |
| `dem-yade-capillary` | — | — | no result.json | — |
| `dem-yade-directshear` | — | — | no result.json | — |
| `dem-mercurydpm` | — | — | no result.json | — |
| `dem-chrono-cpu` | — | — | no result.json | — |
| `dem-tribocharge-numba` | — | — | no result.json | — |
| [`mui-rheology`](runs/mui-rheology/) | self-written Python (numpy, scipy.linalg.solve_banded, numba) numpy 2.5.4 | **ran** | 1.7 min | local_muI: {22deg: {u_surface_numerical_sqrt_gd: 1.15, u_surface_bagnold_sqrt_gd: 1.15, u_surface_numerical_m_per_s: 0.0804, rms_error_rel_to_surface_velocity: 1e-05}, 24deg: {u_surface_numerical_sqrt_gd: 3.94, u_surface |
| [`analytic-orifice-screw`](runs/analytic-orifice-screw/) | custom Python (numpy/scipy/matplotlib) python 3.12.3, numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2 | **ran** | 5 s | assumptions: {rho_b_salt: 1.25e+03, d50_salt_mm: 0.425, C: 0.58, k: 1.5}; beverloo_table: [{orifice: salt, exit 3.00 mm (no core tip), W_g_s: 0.616, W_g_s_k1p6: 0.589, W_g_s_k1p4: 0.644}, {orifice: salt, core-tip annulus |
| `ca-avalanche` | — | — | no result.json | — |
| `mc-packing` | — | — | no result.json | — |
| [`moisture-sorption`](runs/moisture-sorption/) | custom Python (numpy/scipy solve_ivp BDF/matplotlib) python 3.12.3, numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2 | **ran** | 7 s | inputs: {NaCl: {rho_p: 2.16e+03, d: 0.000425, rho_b: 1.25e+03, DRH: 0.753}, BaCl2.2H2O: {rho_p: 3.1e+03, d: 0.000425, rho_b: 1.79e+03, DRH: 0.9}}; D_vapour_air_m2_s: 2.55e-05; c_sat_kg_m3: 0.023 |
| [`bayes-grainlearning`](runs/bayes-grainlearning/) | GrainLearning (pip grainlearning) 2.0.5 | **ran** | 1 s | iterations_run: 6; samples_per_iteration: 40; model_evaluations: 240 |
| [`bayes-gp-emulator-mcmc`](runs/bayes-gp-emulator-mcmc/) | scikit-learn GaussianProcessRegressor + emcee + scipy.stats.qmc.Sobol scikit-learn 1.9.1, emcee 3.1.6 | **ran** | 3.0 min | design_points: 48; prior_box: {mu_s: [0.1, 1], mu_r: [0.02, 0.6], Bo: [0, 1.5]}; emulator_validation_400_heldout: [{output: mg@0, rmse: 2.12, r2: 0.979, kernel: 1.92**2 * Matern(length_scale=[0.25, 4.72, 1.51], nu=2.5) + |
| `gns-gnn-simulator` | — | — | no result.json | — |
| `cfd-dem` | — | — | no result.json | — |
| `contact-dynamics` | — | — | no result.json | — |
| `dem-fem-coupling` | — | — | no result.json | — |
| `dem-nonspherical` | — | — | no result.json | — |

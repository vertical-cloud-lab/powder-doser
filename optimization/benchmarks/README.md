# Controller benchmark suite (issue #123 / PR #124)

Simulation study comparing the candidate dosing control methods proposed in
PR #124 and the Edison reviews, against the digital twin
(`../simulation/powder_sim.py`, v2 — revised per the Edison benchmark critique
in `../edison/query_out/sim_critique.answer.md`).

**Interpretation caveat (from the critique):** the twin's coefficients are
provisional until the bench calibration experiments are run, so results here
are a *simulation sensitivity study* — evidence about controller structure and
failure modes, not proof that one controller is superior on hardware.

## Layout

| File | Purpose |
|---|---|
| `rig.py` | Fair sensor/actuator surface: controllers see only the simulated 10 Hz balance stream and their own commanded state — never lip/screw/true mass. Ground truth is read only for scoring, after the dose ends. |
| `controllers.py` | The five method families: `three_phase` (firmware baseline), `three_phase_vel` (velocity bulk), `rate_pi_kf` (rate-PI + switching-R Kalman filter, filterpy), `dual_ukf` (joint state+feed-factor UKF, filterpy), `mpc` (short-horizon constrained MPC, cvxpy/OSQP). All share the tap-until-tolerance endgame. |
| `bo_tuning.py` | Ax/BoTorch tuning of 9 three-phase policy parameters per powder (scalarized cost, asymmetric overshoot penalty, firmware defaults as safe seed). Writes `results/bo_params.json`. |
| `benchmark.py` | Grid runner: methods × powders × contexts × targets × seeds → `results/results.jsonl`. |
| `summary_md.py` | Markdown tables → `results/summary.md`. |
| `plots.py` | Figures → `results/fig_*.png`. |

## Reproduce

```bash
pip install numpy scipy filterpy cvxpy ax-platform matplotlib
python bo_tuning.py                    # ~15 min: per-powder BO campaigns
python benchmark.py                    # full grid (adds bo_three_phase)
python summary_md.py && python plots.py
```

Objectives/constraints scored per dose: |mass error| after full settle
(tolerance ±5 mg), dose time, tap count (wear), strict overshoot
(true mass > target — the asymmetric hard constraint), and failure status
(stall / timeout / overshoot-abort).

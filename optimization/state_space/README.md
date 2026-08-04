# State-space model of the powder doser

Executable form of [`docs/state-space-model.md`](../../docs/state-space-model.md)
— read that first; it explains every state, input and parameter and shows the
salt data each one was identified from.

| file | what it does |
|---|---|
| [`state_space.py`](state_space.py) | the model: 14 continuous states + discrete flow mode, `f/tap/step/measure`, `linearize`, `discretize`, `observability_report`, and a 4-state reduced LTI for LQG/MPC. Run it directly for a demo. |
| [`fit_salt_parameters.py`](fit_salt_parameters.py) | identifies every parameter from the PR #131 salt datasets → [`salt_params.json`](salt_params.json) + [`figures/`](figures) |
| [`validate.py`](validate.py) | replays the recorded PID doses through the model → [`validation.json`](validation.json) + `figures/fig3-…` |
| [`tests/`](tests) | 15 behaviour tests (`python -m unittest discover optimization/state_space/tests`) |

```bash
# the raw data lives on the #131 branch until it merges
git worktree add /tmp/pr131 origin/claude/issue-130-20260721-1807

python optimization/state_space/fit_salt_parameters.py --data-root /tmp/pr131/data
python optimization/state_space/validate.py            --data-root /tmp/pr131/data
python optimization/state_space/state_space.py
python -m unittest discover optimization/state_space/tests
```

`salt_params.json` and the figures are committed, so the model is usable without
re-running the identification. Requires `numpy`, `scipy`, `matplotlib`.

**The parameters are salt-only.** Treat `salt_params.json` as one entry in a
per-powder library; the identification pipeline is the reusable part.

# Edison status

All nine queries in [`run_queries.py`](run_queries.py) were sent on 31 Oct 2026 at 03:01 UTC after the
`EDISON_PLATFORM_API_KEY` was rotated, and all nine finished with `success` within 34 minutes. Task ids, job names
and the full query text are in [`_task_ids.json`](_task_ids.json).

| Query | Job | Task | Status | Files |
|---|---|---|---|---|
| `q1_feeder_simulation_methods` | LITERATURE_HIGH | `896156d6` | success | [answer](q1_feeder_simulation_methods.answer.md), [record](q1_feeder_simulation_methods.task.json) |
| `q2_dem_calibration_standard_tests` | LITERATURE_HIGH | `1676409e` | success | [answer](q2_dem_calibration_standard_tests.answer.md), [record](q2_dem_calibration_standard_tests.task.json) |
| `q3_spreadability_simulation` | LITERATURE | `a6bcdec7` | success | [answer](q3_spreadability_simulation.answer.md), [record](q3_spreadability_simulation.task.json) |
| `q4_moisture_capillary` | LITERATURE | `a6982778` | success | [answer](q4_moisture_capillary.answer.md), [record](q4_moisture_capillary.task.json) |
| `q5_electrostatics` | LITERATURE | `68790371` | success | [answer](q5_electrostatics.answer.md), [record](q5_electrostatics.task.json) |
| `q6_precedent_feeder_as_instrument` | PRECEDENT | `920cf7f0` | success | [answer](q6_precedent_feeder_as_instrument.answer.md), [record](q6_precedent_feeder_as_instrument.task.json) |
| `q7_continuum_reduced_order` | LITERATURE | `556fb258` | success | [answer](q7_continuum_reduced_order.answer.md), [record](q7_continuum_reduced_order.task.json) |
| `q8_tapping_packing_shape` | LITERATURE | `5ba96ea1` | success | [answer](q8_tapping_packing_shape.answer.md), [record](q8_tapping_packing_shape.task.json) |
| `q9_ml_surrogate_simulators` | LITERATURE | `45fcea4f` | success | [answer](q9_ml_surrogate_simulators.answer.md), [record](q9_ml_surrogate_simulators.task.json) |
| `q10_simulator_workflow_feasibility` | LITERATURE_HIGH | `ef1201e2` | success | [answer](q10_simulator_workflow_feasibility.answer.md), [record](q10_simulator_workflow_feasibility.task.json) |
| `q11_ml_property_dose_models` | LITERATURE_HIGH | `57e91c6d` | success | [answer](q11_ml_property_dose_models.answer.md), [record](q11_ml_property_dose_models.task.json) |

`<key>.answer.md` holds the formatted answer with its reference list; `<key>.task.json` is the full verbose task
record (trajectory and evidence) as returned by `get_task(verbose=True)`.

q11 was added on 5 Nov 2026 after another question on PR #196: how to train machine-learning models that predict powder properties from dosing behaviour and, given the properties, the dosing outcome (run 33, [`../runs/ml-property-dose/`](../runs/ml-property-dose/)). It was sent at 21:56 UTC and finished with `success` by 22:19 UTC.

q10 was added on 3 Nov 2026 after a question on PR #196: how the simulator would infer a new powder's
properties and speed up its calibration, and how to test whether that is feasible within the project. It was sent at
19:46 UTC and finished with `success` at 20:13 UTC.

## Earlier failure (before the key rotation)

Between 01:47 and 02:14 UTC the same day, every login to `/auth/login` returned HTTP 403 `{"detail":"Forbidden"}`,
from the runner and through the doser Pi alike, so the key itself was being refused. For that reason the
literature step first used web search plus open-access full texts read through the Pi ([`../fulltext/`](../fulltext/)).

## Re-running

```bash
cd docs/physics-simulations
python edison/run_queries.py dispatch    # skips keys already in _task_ids.json
python edison/run_queries.py wait        # one foreground call; polls every 2 min, then fetches
python edison/run_queries.py wait 3300 q11_ml_property_dose_models   # only the named query
```

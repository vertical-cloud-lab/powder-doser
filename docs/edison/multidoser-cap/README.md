# Edison Scientific — rotation-agnostic front cap for the multi-doser carousel

Artifacts for the two Edison queries submitted from
[`scripts/edison_rotation_agnostic_cap.py`](../../../scripts/edison_rotation_agnostic_cap.py)
in response to the multi-doser design discussion in
[issue #128](https://github.com/vertical-cloud-lab/powder-doser/issues/128).

The design question: modules hang on a roller-chain carousel at an arbitrary
clock angle about their own long axis, so any front cap over the dispensing
outlet must either be insensitive to that angle or the docking motion must
index the module to a known angle. A spring-loaded ratcheting iris was the
starting proposal.

| Task | Job | Task ID | Artifacts |
|---|---|---|---|
| `precedent` | `job-futurehouse-paperqa3-precedent` | `f0314fd1-e7d0-437a-8fe2-c71837ba9bbf` | [`precedent.answer.md`](precedent.answer.md), [`precedent.references.md`](precedent.references.md), [`precedent.artifact-00.md`](precedent.artifact-00.md), [`precedent.task.json`](precedent.task.json) |
| `literature` | `job-futurehouse-paperqa3-high` | `ebdaf3e2-6d8a-44b2-9e4d-cab547fb75f5` | [`literature.answer.md`](literature.answer.md), [`literature.references.md`](literature.references.md), [`literature.artifact-00.md`](literature.artifact-00.md), [`literature.artifact-01.md`](literature.artifact-01.md), [`literature.task.json`](literature.task.json) |

Verbatim prompts are in [`_prompts.md`](_prompts.md); task IDs in
[`_task_ids.json`](_task_ids.json).

## Headline result

Both tasks independently converge on the same recommendation: **solve the
orientation problem at the dock, not inside the cap.** An asymmetric helical
lead-in on the station converts the robot's axial insertion into rotation that
drives the module to a single unique clock angle; once indexed, a simple rigid
spring-closed shutter/cap with one O-ring land does the sealing. The iris —
ratcheted or not — ranks last on powder-service grounds (blade-lap leakage
paths, powder ingress into pivots, printed-polymer wear debris, and no real
moisture/oxygen barrier).

Reproduce or extend with:

```bash
python scripts/edison_rotation_agnostic_cap.py submit
python scripts/edison_rotation_agnostic_cap.py wait
```

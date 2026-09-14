# Rig state

Operator-reported bench state that is not derivable from the run data — the
run documents record what happened *during* runs; this file records what is
true *between* them. Update whenever the loaded powder changes.

## Currently loaded powder

| As of (UTC) | Powder | Notes | Source |
|---|---|---|---|
| 2026-09-14 18:12 | **silicon −110/+200 mesh** | Loaded for the owed blocks G+H, **delivery-end tape removed** (operator-stated). Gate held 12:22–13:58 MDT without passing (second stand-down, [notes](2026-09-14-silicon-110-200-gh-standdown2.md)); beaker emptied/cleaned mid-hold by the operator; Pi dropped off the tailnet 14:00 MDT so the fresh-load pre-flight is still owed. Column charge state unverified. | [@swcharles, issue #116](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-5668524313) |
| 2026-09-11 14:15 | salt (NaCl, control) | Loaded after the campaign's last completed test (Si −325 mesh G+H, 2026-09-10). No run requested — recorded on operator instruction only; the rig was not touched. Delivery-end tape state not stated. | [@swcharles, issue #116](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-5635766543) |

Earlier loads are traceable through the run log (`RUN-LOG.md` on the campaign
branches) and the issue #116 / PR #131 threads.

# Rig state

Operator-reported bench state that is not derivable from the run data — the
run documents record what happened *during* runs; this file records what is
true *between* them. Update whenever the loaded powder changes.

## Currently loaded powder

| As of (UTC) | Powder | Notes | Source |
|---|---|---|---|
| 2026-09-11 14:15 | **salt** (NaCl, control) | Loaded after the campaign's last completed test (Si −325 mesh G+H, 2026-09-10). No run requested — recorded on operator instruction only; the rig was not touched. Delivery-end tape state not stated. | [@swcharles, issue #116](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-5635766543) |

Earlier loads are traceable through the run log (`RUN-LOG.md` on the campaign
branches) and the issue #116 / PR #131 threads.

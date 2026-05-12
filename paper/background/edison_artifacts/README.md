# Edison query artifacts

This directory holds the **raw provenance artifacts** for the four
`LITERATURE_HIGH` queries that produced the markdown notes in
[`paper/background/`](../). Files are written by
[`paper/background/edison_run.py`](../edison_run.py).

For each query key (`powder_commercial`, `powder_academic`,
`gencad_landscape`, `gencad_academic`):

| File | Content |
| --- | --- |
| `<key>.task.json` | Full Edison `TaskResponse.model_dump()` — status, agent state, environment frame, response object, references, contexts, cost, token counts, tool history, etc. (multi-MB JSON.) |
| `<key>.answer.md` | The rendered `formatted_answer` (or `answer`) string. This is the same body that was extracted into `../0*-*.md`. |
| `<key>.references.md` | The standalone numbered references list (with DOIs and citation counts) extracted from the answer object. |

These artifacts are committed for reproducibility and traceability of every
claim in the background notes — see issue
[#10](https://github.com/vertical-cloud-lab/powder-doser/issues/10) and
[#26](https://github.com/vertical-cloud-lab/powder-doser/issues/26).

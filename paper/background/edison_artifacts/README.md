# Edison query artifacts

This directory holds the **raw provenance artifacts** for the Edison Scientific
`LITERATURE_HIGH` queries that produced the markdown notes in
[`paper/background/`](../).

The generative-electrical/PCB-design notes (`07`–`13`) are written by
[`paper/background/edison_run_electrical_pcb.py`](../edison_run_electrical_pcb.py)
(issue [#75](https://github.com/vertical-cloud-lab/powder-doser/issues/75)); the
prior powder-dispensing / generative-CAD notes (`01`–`06`) by `edison_run.py`
and `edison_run_followup_spatial.py` (PR
[#29](https://github.com/vertical-cloud-lab/powder-doser/pull/29)).

For each generative-EDA/PCB query key (`gen_eda_landscape`,
`eda_schematic_synthesis_academic`, `pcb_placement_routing_ml`,
`llm_hardware_hdl_codegen`, `code_based_eda_frameworks`,
`eda_datasets_benchmarks`, `open_hardware_eda_for_labs`):

| File | Content |
| --- | --- |
| `<key>.task.json` | Full Edison `TaskResponse.model_dump()` — status, agent state, environment frame, response object, references, contexts, cost, token counts, tool history, etc. (multi-MB JSON.) |
| `<key>.answer.md` | The rendered `formatted_answer` (or `answer`) string. This is the same body that was extracted into `../0*-*.md` / `../1*-*.md`. |
| `<key>.references.md` | The standalone numbered references list (with DOIs and citation counts) extracted from the answer object. |

All seven generative-EDA/PCB runs returned `status=success`.

These artifacts are committed for reproducibility and traceability of every
claim in the background notes — see issues
[#26](https://github.com/vertical-cloud-lab/powder-doser/issues/26) and
[#75](https://github.com/vertical-cloud-lab/powder-doser/issues/75).

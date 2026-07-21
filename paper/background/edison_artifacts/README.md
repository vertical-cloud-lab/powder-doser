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

## Analysis pass (`pcb_recommendations_for_powder_doser`)

In addition to the `LITERATURE_HIGH` runs above, an Edison **`ANALYSIS`** task
([`../edison_run_pcb_recommendation_analysis.py`](../edison_run_pcb_recommendation_analysis.py))
reads the seven rendered reviews back in — uploaded as a single zipped
*collection* via `store_file_content(..., as_collection=True)`, per the
[Edison file-management docs](https://docs.edisonscientific.com/edison-client/file-management) —
and synthesizes them into concrete, powder-doser-specific PCB-implementation
recommendations (answering @lbwinters' review request on PR
[#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4615501821)).
Its rendered output is the note
[`../14-pcb-design-recommendations-for-powder-doser.md`](../14-pcb-design-recommendations-for-powder-doser.md).

| File | Content |
| --- | --- |
| `pcb_recommendations_for_powder_doser.task.json` | Full Edison `TaskResponse.model_dump()` for the analysis task. |
| `pcb_recommendations_for_powder_doser.answer.md` | The rendered analysis answer (same body as `../14-*.md`). |
| `pcb_recommendations_for_powder_doser.notebook.ipynb` | The analysis notebook Edison generated, when present. |

## Topology → starter-board runs (`topology_to_starter_board_tools`, `topology_to_board_for_powder_doser`)

Two further Edison runs were added for the **topology → router-ready starter
board** question on PR
[#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654166992)
(the gap that Quilter/DeepPCB cannot bridge themselves):

- `topology_to_starter_board_tools` — a `LITERATURE_HIGH` survey
  ([`../edison_run_topology_to_board.py`](../edison_run_topology_to_board.py)) of
  tools/research that turn a topology + BOM into a footprinted, netlisted KiCad
  starter board (CELUS, Flux.ai, JITX, atopile/tscircuit/SKiDL, KiCad-CLI +
  Python, and recent NL→KiCad research systems). Rendered output:
  [`../19-topology-to-starter-board-tools.md`](../19-topology-to-starter-board-tools.md).
  Files: `<key>.{task.json,answer.md,references.md}`.
- `topology_to_board_for_powder_doser` — an `ANALYSIS` run
  ([`../edison_run_topology_to_board_analysis.py`](../edison_run_topology_to_board_analysis.py))
  that uploads **this repo's actual KiCad test-module project**
  (`hardware/test-module/kicad/` from PR
  [#61](https://github.com/vertical-cloud-lab/powder-doser/pull/61)) as a single
  zipped *collection* and recommends, per the audited schematic, how the Copilot
  agent should produce the starter board. Rendered output:
  [`../20-topology-to-starter-board-for-powder-doser.md`](../20-topology-to-starter-board-for-powder-doser.md).
  Files: `<key>.{task.json,answer.md,notebook.ipynb}`.

Both runs returned `status=success`.

## Shunt-regulator necessity run (`shunt_regulator_necessity`)

A `LITERATURE_HIGH` run
([`../edison_run_shunt_regulator_necessity.py`](../edison_run_shunt_regulator_necessity.py))
asking whether the Pololu #3776 shunt regulator (SR1) on the +12 V rail is
necessary, given the board's stepper/solenoid/servo transient sources and a
non-sinking wall adapter (PR
[#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-5005495385)).
Dispatched with `--dispatch` (task id kept in `<key>.task_id`) and fetched in a
follow-up session with `--fetch-once`. Files:
`<key>.{task.json,answer.md,references.md}`; returned `status=success`.

These artifacts are committed for reproducibility and traceability of every
claim in the background notes — see issues
[#26](https://github.com/vertical-cloud-lab/powder-doser/issues/26) and
[#75](https://github.com/vertical-cloud-lab/powder-doser/issues/75).

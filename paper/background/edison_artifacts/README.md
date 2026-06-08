# Edison Scientific artifacts

Query artifacts from Edison Scientific runs against this repository's design assets.
Each run is stored as `<key>.task.json` (job metadata + verbatim prompt) plus the
submitted answer as `<key>.answer.md`.

| Key | Job type | Input | Runner |
| --- | --- | --- | --- |
| `design-log-analysis` | ANALYSIS (crow) | `DESIGN-LOG.md` | [`../edison_run_design_log_analysis.py`](../edison_run_design_log_analysis.py) |

Runners require `EDISON_API_KEY` and `pip install edison-client`. ANALYSIS jobs
upload their input as a zipped collection (`store_file_content(..., as_collection=True)`).

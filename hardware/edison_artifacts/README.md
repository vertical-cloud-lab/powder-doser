# Edison Scientific artifacts (hardware review)

This directory holds the artifacts returned by an Edison Scientific
ANALYSIS run against the hardware identification + KiCad schematic package
in this PR. The runner is `edison_run_hardware_review.py`, which uploads
the relevant files (`hardware/vibration-motor-and-solenoid.md`, the KiCad
schematic + render + custom symbol library, and the KiCad README) and then
submits an `ANALYSIS` task with the prompt embedded verbatim in the script.

Outputs follow the same per-key triplet convention as
`paper/background/edison_artifacts/`:

* `<key>.task.json` — full task object returned by the Edison API.
* `<key>.answer.md` — the assistant's answer in markdown.
* `<key>.references.md` — formatted answer / references / citations if the
  API populated any.

Re-running the runner requires `EDISON_API_KEY` to be set in the
environment.

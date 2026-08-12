# Test payloads

## `cube_h2d.gcode.3mf`

The 20 mm calibration cube referenced throughout
[`docs/h2d-programmatic-access.md`](../docs/h2d-programmatic-access.md)
(Step 3 dry run and the empirical CLI walkthrough). Sliced **for the
Bambu Lab H2D only** — do not send it to the A1 mini (wrong-printer
files are triage item #1 in the A1-mini doc).

Provenance (regenerated 2026-08-12 in CI, PR #23):

- BambuStudio CLI v02.06.00.51 AppImage, headless (`xvfb-run`), on
  Ubuntu 24.04.
- Profiles: `Bambu Lab H2D 0.4 nozzle` / `0.20mm Standard @BBL H2D` /
  `Bambu PLA Basic @BBL H2D` ×2 (one per tool), flattened with
  [`scripts/flatten_bambu_profiles.py`](../scripts/flatten_bambu_profiles.py)
  **including the template G-code sidecars** (fix of 2026-08-12).
- Command: the doc's verified recipe — `--orient 1 --arrange 1
  --filament-map-mode "Manual" --filament-map "1,2" --slice 1`.
- The process profile had `curr_bed_type = "Textured PEI Plate"`
  injected before slicing, so the job commands a 55 °C first-layer bed
  instead of the CLI's Cool Plate 35 °C default (the setting behind the
  first Thumbelina "ghost print").
- Why the regeneration: the 2026-07-29 file was flattened *without* the
  template sidecars, so its start G-code was the generic
  `fdm_machine_common` fallback — no `M620`/`T<n>` material-load, which
  ghost-prints (bed heats, motions run, nothing extrudes; the failure
  Thumbelina hit on 2026-08-12 on the A1-mini side). This file carries
  the real H2D start sequence (`M620 S0A … T0` load, purge, wipe).

Header facts (from `Metadata/plate_1.gcode` inside the archive):
`printer_model = Bambu Lab H2D`, `filament_map = 1,2` /
`filament_map_mode = Manual` (IDEX), bed `M190 S55`,
~14 min estimated, 3.66 g PLA.

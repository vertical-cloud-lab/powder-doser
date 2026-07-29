# Test payloads

## `cube_h2d.gcode.3mf`

The 20 mm calibration cube referenced throughout
[`docs/h2d-programmatic-access.md`](../docs/h2d-programmatic-access.md)
(Step 3 dry run and the empirical CLI walkthrough). Sliced **for the
Bambu Lab H2D only** — do not send it to the A1 mini (wrong-printer
files are triage item #1 in the A1-mini doc).

Provenance (regenerated 2026-07-29 in CI, PR #23):

- BambuStudio CLI v02.06.00.51 AppImage, headless (`xvfb-run`), on
  Ubuntu 24.04.
- Profiles: `Bambu Lab H2D 0.4 nozzle` / `0.20mm Standard @BBL H2D` /
  `Bambu PLA Basic @BBL H2D` ×2 (one per tool), flattened with
  [`scripts/flatten_bambu_profiles.py`](../scripts/flatten_bambu_profiles.py).
- Command: the doc's verified recipe — `--orient 1 --arrange 1
  --filament-map-mode "Manual" --filament-map "1,2" --slice 1`.
- One improvement over the original May 2026 run: the process profile
  had `curr_bed_type = "Textured PEI Plate"` injected before slicing,
  so the job commands a 55 °C first-layer bed instead of the CLI's
  Cool Plate 35 °C default (the setting behind the Thumbelina
  "ghost print").

Header facts (from `Metadata/plate_1.gcode` inside the archive):
`printer_model = Bambu Lab H2D`, `filament_map = 1,2` /
`filament_map_mode = Manual` (IDEX), bed `M190 S55`, nozzle
205–220 °C, ~9 min estimated, 3.72 g PLA.

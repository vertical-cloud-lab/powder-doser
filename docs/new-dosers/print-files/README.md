# Sliced A1 mini files for doser #1

Ready-to-print `.gcode.3mf` files for the A1 mini ("Thumbelina"), made from
the PR #170 STEP export
[`mounting-plate.step`](https://github.com/vertical-cloud-lab/powder-doser/blob/ce256c3/cad/full-assembly/components/fusion-step/mounting-plate.step).
That STEP holds 5 bodies (the plate, both 28T tilt gears, 2 links). They were
split apart and each one laid on its largest flat face. The gears end up with
their axis vertical.

| File | Contents | PLA | Time |
|---|---|---:|---:|
| [`doser1_mounting_plate.gcode.3mf`](doser1_mounting_plate.gcode.3mf) | Mounting plate, with tree supports | 46.8 g | 1 h 38 min |
| [`doser1_tilt_gears_links.gcode.3mf`](doser1_tilt_gears_links.gcode.3mf) | Both 28T tilt gears and both links, no supports | 19.2 g | 50 min |

Together that's 66 g, against 70 g on Sam's slicer sheet.

![Mounting plate toolpaths](doser1_mounting_plate_preview.png)

**Settings.** BambuStudio 02.06.00.51 CLI with the stock `Bambu Lab A1 mini
0.4 nozzle`, `0.20mm Standard @BBL A1M` and `Bambu PLA Basic @BBL A1M`
profiles, flattened with `flatten_bambu_profiles.py` (branch
`copilot/programmatic-access-bambu-h2d`). Changes from stock: textured PEI
plate (65 °C bed), 3 walls, 25 % infill. The mounting plate also uses
`tree(auto)` supports on the build plate only. Its two hinge knuckles start in
mid-air 27.9 mm up, and without supports the slicer warns about floating
regions. The supports are the orange trees in the preview. Printing the
gears and links on the same plate needs supports off, so they're in a
separate file.

**Starting a print.** In Bambu Studio, open the file, *Slice plate*, then
*Print plate*, pick Thumbelina, and map the filament to an AMS lite slot.
Studio slices the file again rather than sending the committed G-code, so
first check that the process preset shows as modified
(`* 0.20mm Standard @BBL A1M`) with the settings above (see
[below](#opening-the-files-in-studios-gui-22-oct-2026)). The mounting plate
is also on Thumbelina's storage as `doser1_mounting_plate.gcode.3mf`, so it
can be started from the touchscreen's file list, which runs the committed
G-code.

**Why an agent can't start it on its own (15 Oct 2026).** Thumbelina is on
firmware 01.08.00.00, which has Bambu's printer-control authorization. Over
LAN from the tailnet Pi, status reads, the camera, FTPS upload and the
chamber-light command all work. `print.project_file` comes back with
`err_code 84033543`, the unsigned-command rejection. A Bambu Cloud login
doesn't help, because starting a print from non-Bambu software is restricted
in cloud mode too. Two ways to unblock it: turn on **Developer Mode** on the
printer (Settings, LAN Only Mode / Developer Mode), or start jobs from Bambu
Studio, Handy or Bambu Connect.

## Opening the files in Studio's GUI (22 Oct 2026)

Bambu Studio 02.08.02.61 opens these files as projects and slices them
again. As first committed (`8254040`), they lost their changed settings
there. The GUI loaded the stock `0.20mm Standard @BBL A1M` with no
*modified* mark, so the plate had 2 walls, 15 % infill and no supports. Its
slice came to 36.1 g and 1 h 18 min, with a floating-regions warning for the
hinge knuckles. byu-vcl found the same cause
([runbook](https://github.com/vertical-cloud-lab/byu-vcl/blob/591fd92/bambu/studio/README.md#the-gui-resets-a-cli-projects-changed-settings)).
The flattened presets keep the stock preset's name, and
`different_settings_to_system` in `Metadata/project_settings.config` was
empty, so the GUI takes the stock preset of that name.

Both files now list their changes there, in the form Studio itself writes
when it saves a project:
- the plate: `enable_support;sparse_infill_density;support_on_build_plate_only;wall_loops`;
- the gears and links: `sparse_infill_density;wall_loops`.

Nothing else in the files changed, and the plate G-code is byte-identical.
With the patch, the GUI keeps the settings and its slices match the
committed ones:
- the plate: 46.78 g and 267 layers, against 46.77 g and 267;
- the gears and links: 19.20 g, against 19.20 g.

Studio estimates the plate at 1 h 36 min instead of 1 h 38 min because it
uses Bambu's stock acceleration limits, which byu-vcl also saw. The unpatched
file still opened as stock in the same session, so the patch is what keeps
the settings.

## Sending from an agent (22 Oct 2026)

An approved `@claude-print` run can send these. In a test run on PR #181,
Studio logged in on the runner with the password and an authenticator code
from `bambu-totp`, and no e-mailed code was needed. Both printers were on the
account, and Thumbelina was already selected. *Print plate* opened *Send
print job* with these defaults:
- "Thumbelina, the A1 Mini" and the PEI plate;
- PLA mapped to slot A3;
- timelapse off;
- bed levelling and flow calibration on.

The test closed the dialog without sending
([thread](https://github.com/vertical-cloud-lab/powder-doser/pull/181#issuecomment-6352282576)).

![Send print job, closed without sending](studio_send_dialog_2026-10-22.png)

That screenshot is the unpatched file's slice, so it shows 36.12 g. Two notes
for the real send:
- The runner's default Azure apt mirror stalled for 25 min. Pointing
  `/etc/apt/apt-mirrors.txt` at `mirrors.edge.kernel.org` got Studio's
  packages in 4 s.
- The job name defaults to `doser1_mounting_plate.gcode`. It has no spaces,
  so it doesn't need renaming.

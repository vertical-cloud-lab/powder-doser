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

**Starting a print.** Open the file in Bambu Studio, then choose *Print
plate*, pick Thumbelina, and map the filament to an AMS lite slot. The
mounting plate file is also already on Thumbelina's storage as
`doser1_mounting_plate.gcode.3mf`, so it can be started from the
touchscreen's file list.

**Why an agent can't start it on its own (15 Oct 2026).** Thumbelina is on
firmware 01.08.00.00, which has Bambu's printer-control authorization. Over
LAN from the tailnet Pi, status reads, the camera, FTPS upload and the
chamber-light command all work. `print.project_file` comes back with
`err_code 84033543`, the unsigned-command rejection. A Bambu Cloud login
doesn't help, because starting a print from non-Bambu software is restricted
in cloud mode too. Two ways to unblock it: turn on **Developer Mode** on the
printer (Settings, LAN Only Mode / Developer Mode), or start jobs from Bambu
Studio, Handy or Bambu Connect.

#!/usr/bin/env bash
# Regenerate every FC-1 output from fc1.kicad_sch / fc1.kicad_pcb (KiCad 9.0, kicad-cli).
set -euo pipefail
cd "$(dirname "$0")"
kicad-cli sch erc --format report --output erc.rpt fc1.kicad_sch
kicad-cli pcb drc --schematic-parity --format report --output drc.rpt fc1.kicad_pcb
# schematic
kicad-cli sch export pdf --output fc1-schematic.pdf fc1.kicad_sch
tmp=$(mktemp -d); kicad-cli sch export svg --output "$tmp" fc1.kicad_sch; mv "$tmp"/fc1.svg fc1-schematic.svg; rmdir "$tmp"
# fabrication: Gerbers (Protel names, no X2, mask subtracted from silk) + Excellon drill + maps
rm -rf gerbers && mkdir -p gerbers
kicad-cli pcb export gerbers --output gerbers/ --no-x2 --no-netlist --subtract-soldermask \
  --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" fc1.kicad_pcb
kicad-cli pcb export drill --output gerbers/ --format excellon --drill-origin absolute --excellon-units mm \
  --excellon-zeros-format decimal --excellon-oval-format alternate --excellon-separate-th \
  --generate-map --map-format gerberx2 fc1.kicad_pcb
rm -f fc1-gerbers.zip; (cd gerbers && zip -q -X ../fc1-gerbers.zip ./*)
# pick-and-place (origin = board lower-left corner, y up), all parts except DNP
kicad-cli pcb export pos --output fc1-pos.csv --format csv --units mm --side both --use-drill-file-origin --exclude-dnp fc1.kicad_pcb
# renders: KiCad's 3D models are not installed on the runner; the 12 models this board uses were fetched from
# https://gitlab.com/kicad/libraries/kicad-packages3D (tag 9.0.8) into $KICAD9_3DMODEL_DIR (see README).
# The BNC (no model in the library) and the Coto relay (project footprint) render as bare pads.
export KICAD9_3DMODEL_DIR="${KICAD9_3DMODEL_DIR:-/tmp/fc1-3d}"
xvfb-run -a kicad-cli pcb render --side top --width 2000 --height 1600 --quality high --background opaque --output fc1-top.png fc1.kicad_pcb
xvfb-run -a kicad-cli pcb render --side bottom --width 2000 --height 1600 --quality high --background opaque --output fc1-bottom.png fc1.kicad_pcb
xvfb-run -a kicad-cli pcb render --side top --rotate "-40,0,30" --perspective --zoom 0.85 --width 2000 --height 1600 --quality high --background opaque --output fc1-iso.png fc1.kicad_pcb
echo done

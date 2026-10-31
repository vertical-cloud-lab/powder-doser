#!/bin/bash
# Short smoke-test rerun of the PR #180 rig auger case rig_t27p5_r60 (27.5 deg tilt, 60 rpm),
# 0.12 s settle with the exit plugged + 0.25 revolution, dry and with SJKR cohesion (6 kJ/m3).
# geometry.py and run_case.py are copied unchanged from branch claude/issue-158-20261010-0534 (sim/dem/).
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
SCRATCH=${SCRATCH:-/tmp/sims-scratch/dem-liggghts-auger-short}
mkdir -p "$SCRATCH"
export OMP_NUM_THREADS=1
for c in auger_short_dry auger_short_coh; do
  python "$HERE/run_case.py" "$HERE/$c.json" --workdir "$SCRATCH/$c"
done
python "$HERE/figures.py"

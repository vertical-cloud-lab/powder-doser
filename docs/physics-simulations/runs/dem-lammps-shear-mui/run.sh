#!/bin/bash
# Rerun both cases (single core each; 9 and 6 min on the shared 4-core runner).
# Output (log, stress time series, dumps) goes to $OUT (default /tmp/sims-scratch/dem-lammps-shear-mui).
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-/tmp/sims-scratch/dem-lammps-shear-mui}
mkdir -p "$OUT"
export OMP_NUM_THREADS=1
cd "$OUT"
# non-cohesive Hertz-Mindlin
lmp -in "$HERE/in.shear" -var gamma 0.0    -var tag noncoh -var nsc 1.0 -var out "$OUT" -log "$OUT/log.noncoh" -screen none
# JKR cohesion, gamma = 8.5e-3 J/m^2 (granular Bond number ~10 for the 0.425 mm grain)
# (reduced stage list to keep the run under 8 min on the shared runner)
lmp -in "$HERE/in.shear" -var gamma 8.5e-3 -var tag jkr    -var nsc 1.0 -var out "$OUT" -log "$OUT/log.jkr"    -screen none \
    -var rlist 2.5 25.0 150.0 2.5 2.5 -var plist 100.0 100.0 100.0 200.0 25.0 -var slist 2.0 2.0 4.0 1.0 1.0
python3 "$HERE/analyze.py" "$OUT" "$HERE"

#!/bin/bash
# Rerun all five cases (single core each; 26-68 s each on the shared runner), then the analysis.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-/tmp/sims-scratch/dem-lammps-charge}
mkdir -p "$OUT"; cd "$OUT"
export OMP_NUM_THREADS=1
run(){ lmp -in "$HERE/in.charge" -var qm $2 -var sigw $3 -var tag $1 -var out "$OUT" -log "$OUT/log.$1" -screen none ${4:+-var nrun $4}; }
run A 0.0   0.0
run B -1e-5 1e-5
run C -1e-4 1e-5
run D -1e-4 0.0
run Clong -1e-4 1e-5 60000
python3 "$HERE/analyze.py" "$OUT" "$HERE"

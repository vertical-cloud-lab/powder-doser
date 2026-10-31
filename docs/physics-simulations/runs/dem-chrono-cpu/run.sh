#!/bin/bash
# PyChrono 10.0.0 (conda-forge) core ChSystemSMC on CPU, Bullet collision, 1 thread.
# Env used: conda create -p /tmp/sims-scratch/dem-chrono-cpu/env -c conda-forge --override-channels python=3.12 pychrono=10.0.0 numpy
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-/tmp/sims-scratch/dem-chrono-cpu/env/bin/python}
OUT=${1:-/tmp/sims-scratch/dem-chrono-cpu}
mkdir -p "$OUT"
export OMP_NUM_THREADS=1
$PY "$HERE/silo_discharge.py" --rolling-check --out "$OUT"
for L in 5.5 7 8.5; do
  $PY "$HERE/silo_discharge.py" --L $L --n 900 --box 14 --t-settle 0.2 --t-flow 0.5 --out "$OUT" > "$OUT/L$L.log" 2>&1
done
/tmp/venv-dem2/bin/python "$HERE/analyze.py" "$OUT" "$HERE" L08.5

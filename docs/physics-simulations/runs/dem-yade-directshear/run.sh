#!/bin/bash
# Yade daily (upstream .deb for Ubuntu noble from http://www.yade-dem.org/packages/), single thread.
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-/tmp/sims-scratch/dem-yade-directshear}
mkdir -p "$OUT"
for s3 in 50 150 400; do
  OMP_NUM_THREADS=1 yadedaily -j1 -n -x "$HERE/peri_triax.py" $s3 "$OUT" 600 > "$OUT/s3_$s3.log" 2>&1
done
/tmp/venv-dem2/bin/python "$HERE/analyze.py" "$OUT" "$HERE"

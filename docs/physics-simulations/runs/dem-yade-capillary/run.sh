#!/bin/bash
# Runs the three column-collapse cases one after another (single thread each), then the analysis.
# Yade: upstream daily .deb for Ubuntu noble from http://www.yade-dem.org/packages/ (binary: yadedaily)
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-/tmp/sims-scratch/dem-yade-capillary}
mkdir -p "$OUT"
for c in "wet1 0.01" "wet01 0.001" "dry 0"; do
  set -- $c
  OMP_NUM_THREADS=1 yadedaily -j1 -n -x "$HERE/column_collapse.py" "$1" "$2" "$OUT" > "$OUT/$1.log" 2>&1
done
/tmp/venv-dem2/bin/python "$HERE/analyze.py" "$OUT" "$HERE"

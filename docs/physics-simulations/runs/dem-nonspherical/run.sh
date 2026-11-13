#!/bin/bash
# Yade (yadedaily 20261024 from the Yade PPA/Debian packages; `yade` also works) lifted-cylinder heaps.
# Main set: seed 1 -> out3, replicate: seed 2 -> out4 (N = 361 per heap, one process at a time).
HERE=$(cd "$(dirname "$0")" && pwd)
B=${SCRATCH:-/tmp/sims-scratch/dem-nonspherical}
export OMP_NUM_THREADS=1 PYTHONNOUSERSITE=1   # PYTHONNOUSERSITE: avoid a user-site NumPy 2.x shadowing the system one
for s in 1 2; do
  S=$B/out$((s + 2)); mkdir -p "$S"
  for c in cube8 sphere sphere_rr; do
    CASE=$c NPART=361 HCLOUD_FAC=2.0 SEED=$s OUT="$S" yadedaily -n -x "$HERE/heap_yade.py" > "$S/log_$c.txt" 2>&1
  done
done
python3 -m venv /tmp/venv-cfd && /tmp/venv-cfd/bin/pip install -q numpy matplotlib imageio imageio-ffmpeg
/tmp/venv-cfd/bin/python "$HERE/post_yade.py" "$B/out3,$B/out4" "$HERE"

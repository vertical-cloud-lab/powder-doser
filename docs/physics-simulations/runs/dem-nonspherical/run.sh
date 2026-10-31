#!/bin/bash
# Yade (yadedaily 20261024 from the Yade PPA/Debian packages; `yade` also works) lifted-cylinder heaps.
HERE=$(cd "$(dirname "$0")" && pwd)
S=${SCRATCH:-/tmp/sims-scratch/dem-nonspherical}/out3
mkdir -p "$S"
export OMP_NUM_THREADS=1 PYTHONNOUSERSITE=1   # PYTHONNOUSERSITE: avoid a user-site NumPy 2.x shadowing the system one
for c in cube8 sphere sphere_rr; do
  CASE=$c NPART=361 HCLOUD_FAC=2.0 OUT="$S" yadedaily -n -x "$HERE/heap_yade.py" > "$S/log_$c.txt" 2>&1
done
python3 -m venv /tmp/venv-cfd && /tmp/venv-cfd/bin/pip install -q numpy matplotlib imageio imageio-ffmpeg
/tmp/venv-cfd/bin/python "$HERE/post_yade.py" "$S" "$HERE"

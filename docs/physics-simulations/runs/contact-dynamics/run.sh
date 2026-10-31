#!/bin/bash
# LMGC90 user version 2025 (pyproject 2025.rc3), built from source (no pip/conda package exists).
HERE=$(cd "$(dirname "$0")" && pwd)
S=${SCRATCH:-/tmp/sims-scratch/contact-dynamics}
mkdir -p "$S/src" "$S/build"
sudo apt-get install -y --no-install-recommends gfortran swig liblapack-dev libblas-dev python3-dev cmake
curl -L -o "$S/src/lmgc90_user_2025.zip" "https://seafile.lmgc.univ-montp2.fr/f/a2cd2470d4694a469485/?dl=1"
(cd "$S/src" && unzip -q -o lmgc90_user_2025.zip)
python3 -m venv "$S/venv" && "$S/venv/bin/pip" install -q numpy scipy matplotlib imageio imageio-ffmpeg
cd "$S/build" && PYTHONNOUSERSITE=1 cmake "$S/src/lmgc90_user_2025" -DPython_EXECUTABLE="$S/venv/bin/python" \
   -DLMGC90_WITH_HDF5=OFF -DLMGC90_SPARSE_LIBRARY=none -DLMGC90_MATLIB_VERSION=none \
   -DLMGC90_ENABLE_TESTING=OFF -DLMGC90_ENABLE_DOC=OFF -DCMAKE_BUILD_TYPE=Release && make -j1 && make install
export OMP_NUM_THREADS=1 PYTHONNOUSERSITE=1
for w in 6 4 8 10 7 5; do
  snap=0; [ "$w" = "6" ] && snap=100
  "$S/venv/bin/python" "$HERE/silo_lmgc90.py" $w "$S/W$w" 6000 $snap > "$S/log_W$w.txt" 2>&1
done
"$S/venv/bin/python" "$HERE/post_lmgc90.py" "$S" "$HERE"

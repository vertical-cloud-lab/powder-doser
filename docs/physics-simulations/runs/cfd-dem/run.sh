#!/bin/bash
# CFD-DEM with OpenFOAM v1912 DPMFoam (Ubuntu 24.04 package).  One core per run, run sequentially.
#   sudo apt-get install -y --no-install-recommends openfoam openfoam-examples
HERE=$(cd "$(dirname "$0")" && pwd)
S=${SCRATCH:-/tmp/sims-scratch/cfd-dem}
source /usr/share/openfoam/etc/bashrc 2>/dev/null
for m in twoway oneway vacuum; do
  python3 "$HERE/make_case.py" $m "$S/case_$m"
  (cd "$S/case_$m" && blockMesh > log.blockMesh 2>&1 && OMP_NUM_THREADS=1 DPMFoam > log.DPMFoam 2>&1)
done
# post-processing (numpy, matplotlib, imageio, imageio-ffmpeg)
python3 -m venv /tmp/venv-cfd && /tmp/venv-cfd/bin/pip install -q numpy matplotlib imageio imageio-ffmpeg
/tmp/venv-cfd/bin/python "$HERE/post_cfd.py" "$S" "$HERE"

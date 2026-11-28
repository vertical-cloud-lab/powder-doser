#!/bin/sh
# Rerun every CFD study in this folder, in the order used for the results (one process at a time).
# Run inside the repository (orifice_air.py and stream_impact.py read #196's CSV with git show).
set -e
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY="nice -n 10 python"
$PY validate_cavity.py 32 64 128          # lid-driven cavity vs Ghia et al. 1982
$PY validate_diffusion.py                 # slab diffusion vs the Fourier series
$PY validate_pipe.py                      # axisymmetric pipe flow vs Hagen-Poiseuille
$PY humidity_3d.py 5 abc                  # test 6, still air, 5 mm cells
$PY humidity_3d.py 2.5 abc                # 2.5 mm cells (case b about 10 min, case c needs CG: about 1 GB with LU)
$PY humidity_fan2d.py flow below 3e-4     # fan under the shelf
$PY humidity_fan2d.py flow above 3e-4     # fan over the dish
$PY humidity_fan2d.py vapour below_nu3e-04 above_nu3e-04
$PY stream_impact.py                      # falling stream: speeds, entrained air
for c in fine1 salt1 fine01 fine1_tall; do
  $PY faraday_flow.py flow $c 0.75        # test 10 cup flow, 0.75 mm cells
  $PY faraday_flow.py track $c            # grain tracking
done
$PY faraday_flow.py flow fine1 0.5        # grid check
$PY faraday_flow.py track fine1 0.5
$PY orifice_air.py                        # test 5
$PY figures.py
$PY summary.py

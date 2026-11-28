#!/bin/sh
# Fifth queue: cup flows on grids that put the stream edge (r = 1.5 mm) on a cell face:
# 0.75 mm for all cases, 0.5 mm for the grid check of fine1; then grain tracking.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY="nice -n 10 /tmp/venv/bin/python"
$PY faraday_flow.py flow fine1 0.75 > log_ff_fine1.txt 2>&1
$PY faraday_flow.py track fine1 > log_ft_fine1.txt 2>&1
$PY faraday_flow.py flow salt1 0.75 > log_ff_salt1.txt 2>&1
$PY faraday_flow.py track salt1 > log_ft_salt1.txt 2>&1
$PY faraday_flow.py flow fine01 0.75 > log_ff_fine01.txt 2>&1
$PY faraday_flow.py track fine01 > log_ft_fine01.txt 2>&1
$PY faraday_flow.py flow fine1 0.5 > log_ff_fine1_h05.txt 2>&1
$PY faraday_flow.py track fine1 0.5 > log_ft_fine1_h05.txt 2>&1
echo done > queue5_done.txt

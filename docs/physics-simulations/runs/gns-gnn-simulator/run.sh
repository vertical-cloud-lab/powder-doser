#!/usr/bin/env bash
# Rerun the GNS experiment end to end (single thread). Bulky outputs go to $SCR.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SCR=${SCR:-/tmp/sims-scratch/gns-gnn-simulator}
PY=${PY:-/tmp/venv-bayes/bin/python}
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$SCR"
# environment (once):
#   python3 -m venv /tmp/venv-bayes
#   /tmp/venv-bayes/bin/pip install numpy scipy matplotlib numba imageio imageio-ffmpeg absl-py dm-tree
#   /tmp/venv-bayes/bin/pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
#   /tmp/venv-bayes/bin/pip install torch_scatter torch_cluster -f https://data.pyg.org/whl/torch-2.5.0+cpu.html
#   /tmp/venv-bayes/bin/pip install torch_geometric==2.6.1   # 2.7+ wants pyg-lib>=0.6 for radius_graph
[ -d "$SCR/gns" ] || git clone --depth 1 https://github.com/geoelements/gns.git "$SCR/gns"
COMMIT=$(git -C "$SCR/gns" rev-parse --short HEAD)
$PY "$HERE/dem_collapse.py" "$SCR/data" 40 2 3 11                         # ~70 s
$PY "$HERE/train_gns.py" "$SCR/gns" "$SCR/data" "$SCR/out" "$HERE" 780    # 13 min training + rollouts
$PY "$HERE/plot_gns.py" "$SCR/out" "$HERE" "$SCR/data"                   # PNG, GIF, MP4
$PY "$HERE/make_result.py" "$SCR/out" "$SCR/data" "$HERE" "$COMMIT"      # result.json

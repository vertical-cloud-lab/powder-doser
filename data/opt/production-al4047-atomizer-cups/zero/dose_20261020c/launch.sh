#!/bin/bash
# launch.sh <tag> <uuid> <target_g> <timeout_s>: start one dose detached on the Zero
set -e
D=/tmp/claude186c/dose; cd ~/powder-doser
OUT=data/opt/production-al4047-atomizer-cups/run_$1_${2:0:8}.out
setsid nohup ~/powder-doser-venv/bin/python scripts/opt_dose_capture.py \
  --powder-id al4047 --target-g "$3" --campaign-id production-al4047-atomizer-cups \
  --trial "$2" --mode production --operator claude-for-williamulbz --timeout-s "$4" \
  --params "$(cat $D/params_$1.json)" --frozen "$(cat $D/frozen_$1.json)" \
  --covariates "$(cat $D/cov_$1.json)" > "$OUT" 2>&1 < /dev/null &
echo "launched pid $! -> $OUT"

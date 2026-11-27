#!/bin/bash
# 2026-11-24b: top-up of the 3 g CMC dose at 60 deg with taps (PR #131)
cd /tmp/cmc3g
L=/tmp/cmc3g/run_cmc3g_topup.log
M=~/powder-doser-venv/bin/mpremote
P=~/powder-doser-venv/bin/python
echo "LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/cmc3g/fixed_tilt_dose_topup.py 2>&1 | $P -u /tmp/cmc3g/stamp.py $L
echo "MPREMOTE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L

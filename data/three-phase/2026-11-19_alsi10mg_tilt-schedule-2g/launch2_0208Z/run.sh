#!/bin/bash
# 2026-11-20a: trials 21-30 of the 30 x 2 g AlSi10Mg run (salt protocol of 2026-11-19d) after the refill (PR #131)
cd /tmp/tilt30al2
L=/tmp/tilt30al2/run_launch2.log
M=~/powder-doser-venv/bin/mpremote
P=~/powder-doser-venv/bin/python
echo "LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30al2/three_phase_tilt_trials.py 2>&1 | $P -u /tmp/tilt30al2/stamp.py $L
echo "MPREMOTE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L

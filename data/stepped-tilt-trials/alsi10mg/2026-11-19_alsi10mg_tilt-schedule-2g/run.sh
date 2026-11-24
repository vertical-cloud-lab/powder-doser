#!/bin/bash
# 2026-11-19e: 30 x 2 g AlSi10Mg, the salt protocol of 2026-11-19d (bulk 80 rpm with taps, stepped 60->40 deg) (PR #131)
cd /tmp/tilt30al
L=/tmp/tilt30al/run_launch1.log
M=~/powder-doser-venv/bin/mpremote
P=~/powder-doser-venv/bin/python
echo "LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30al/three_phase_tilt_trials.py 2>&1 | $P -u /tmp/tilt30al/stamp.py $L
echo "MPREMOTE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L

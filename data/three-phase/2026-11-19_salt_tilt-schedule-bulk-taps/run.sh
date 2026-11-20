#!/bin/bash
# 2026-11-19b: 30 x 1 g salt, stepped bulk tilt 60->40 deg WITH bulk taps (PR #131)
cd /tmp/tilt30f
L=/tmp/tilt30f/run_launch1.log
M=~/powder-doser-venv/bin/mpremote
P=~/powder-doser-venv/bin/python
echo "LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30f/three_phase_tilt_trials.py 2>&1 | $P -u /tmp/tilt30f/stamp.py $L
echo "MPREMOTE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L

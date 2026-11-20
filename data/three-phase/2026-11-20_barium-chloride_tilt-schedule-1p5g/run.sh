#!/bin/bash
# 2026-11-20c: 30 x 1.5 g barium chloride, the protocol of 2026-11-20b (bulk 80 rpm with taps, stepped 60->40 deg) (PR #131)
cd /tmp/tilt30ba
L=/tmp/tilt30ba/run_launch1.log
M=~/powder-doser-venv/bin/mpremote
P=~/powder-doser-venv/bin/python
echo "LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30ba/three_phase_tilt_trials.py 2>&1 | $P -u /tmp/tilt30ba/stamp.py $L
echo "MPREMOTE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L

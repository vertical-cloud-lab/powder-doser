#!/bin/bash
cd /tmp/tilt30e
L=/tmp/tilt30e/run_launch1.log
echo "LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 ~/powder-doser-venv/bin/mpremote connect /dev/ttyACM0 run /tmp/tilt30e/three_phase_tilt_trials.py 2>&1 | ~/powder-doser-venv/bin/python -u /tmp/tilt30e/stamp.py $L
echo "MPREMOTE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L

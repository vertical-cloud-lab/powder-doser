#!/bin/bash
# 2026-11-20c launch 2, the 11-18/11-19 recovery sequence after a launch that stalled on a fresh tube:
# priming spin (0 deg, 55 rpm, 40 s), per-angle flow probe, then the identical 2026-11-20c trial script (PR #131)
cd /tmp/tilt30ba
L=/tmp/tilt30ba/run_launch2.log
M=~/powder-doser-venv/bin/mpremote
P=~/powder-doser-venv/bin/python
echo "PRIME_LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30ba/prime_spin.py 2>&1 | $P -u /tmp/tilt30ba/stamp.py $L
echo "PRIME_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L
echo "PROBE_LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30ba/angle_probe.py 2>&1 | $P -u /tmp/tilt30ba/stamp.py $L
echo "PROBE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L
echo "LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30ba/three_phase_tilt_trials.py 2>&1 | $P -u /tmp/tilt30ba/stamp.py $L
echo "MPREMOTE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L

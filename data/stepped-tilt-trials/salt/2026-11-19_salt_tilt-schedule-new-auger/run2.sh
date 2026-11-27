#!/bin/bash
# Same sequence as the first attempt (2026-11-18 morning): priming spin (0 deg, 55 rpm, 40 s),
# per-angle flow probe, then the identical 2026-11-19a trial script.
cd /tmp/tilt30e
L=/tmp/tilt30e/run_launch2.log
M=~/powder-doser-venv/bin/mpremote
P=~/powder-doser-venv/bin/python
echo "PRIME_LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30e/prime_spin.py 2>&1 | $P -u /tmp/tilt30e/stamp.py $L
echo "PRIME_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L
echo "PROBE_LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30e/angle_probe.py 2>&1 | $P -u /tmp/tilt30e/stamp.py $L
echo "PROBE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L
echo "LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 $M connect /dev/ttyACM0 run /tmp/tilt30e/three_phase_tilt_trials.py 2>&1 | $P -u /tmp/tilt30e/stamp.py $L
echo "MPREMOTE_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L

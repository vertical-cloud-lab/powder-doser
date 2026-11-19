#!/bin/bash
cd /tmp/tilt30f
L=/tmp/tilt30f/run_primecheck.log
echo "PRIMECHECK_LAUNCH_UTC $(date -u +%FT%T.%3NZ)" >> $L
PYTHONUNBUFFERED=1 ~/powder-doser-venv/bin/mpremote connect /dev/ttyACM0 run /tmp/tilt30f/prime_check_taps.py 2>&1 | ~/powder-doser-venv/bin/python -u /tmp/tilt30f/stamp.py $L
echo "PRIMECHECK_EXIT ${PIPESTATUS[0]} $(date -u +%FT%T.%3NZ)" >> $L

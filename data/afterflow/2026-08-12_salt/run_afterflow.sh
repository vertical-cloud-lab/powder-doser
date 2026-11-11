#!/bin/bash
cd /tmp
~/powder-doser-venv/bin/mpremote connect /dev/ttyACM0 run /tmp/afterflow_battery.py
echo "MPREMOTE_EXIT=$?"

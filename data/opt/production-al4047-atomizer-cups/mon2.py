#!/usr/bin/env python3
"""Issue #186 helper (runs on the Zero): follow one dose's raw serial log
until the executor's summary line lands or MAX_S passes.

    mon2.py TAG UUID MAX_S
"""
import os
import sys
import time

tag, uuid, max_s = sys.argv[1], sys.argv[2], float(sys.argv[3])
spool = os.path.expanduser(
    "~/powder-doser/data/opt/production-al4047-atomizer-cups")
log = os.path.join(spool, "serial_{}.log".format(uuid))
out = os.path.join(spool, "run_{}_{}.out".format(tag, uuid[:8]))
keys = ("poll ", "===", "RESULT", "stall", "timeout", "guard", "no flow",
        "halt", "settled", "error", "Error")
t0, last = time.time(), None
while time.time() - t0 < max_s:
    try:
        with open(log, errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        lines = []
    prog = [l for l in lines if any(k in l for k in keys)]
    if prog and prog[-1] != last:
        print(time.strftime("%H:%M:%S", time.gmtime()), prog[-1][:200],
              flush=True)
        last = prog[-1]
    if os.path.exists(out):
        with open(out, errors="replace") as f:
            text = f.read()
        if '"trial_uuid"' in text:
            print("--- executor finished ---", flush=True)
            print(text[-2500:], flush=True)
            break
    time.sleep(10)
else:
    print("--- monitor stopped after {:.0f} s ---".format(max_s), flush=True)

# Read-only: stream the balance for 45 s with the rig idle (PR #131, 2026-11-24 CMC dose)
import time
import main_three_phase as m3
sc = m3.Scale()
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 45000:
    r = sc.read()
    if r is not None:
        print("R,{},{},{}".format(time.ticks_diff(time.ticks_ms(), t0), r.status, r.grams))
    time.sleep_ms(400)

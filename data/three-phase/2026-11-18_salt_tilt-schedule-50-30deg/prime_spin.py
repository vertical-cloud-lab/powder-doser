"""Priming spin before relaunching the 30-trial run (PR #131, version 2026-11-18c).

Same as the 06:48 UTC priming this morning: plate at 0 deg, auger at
55 rpm for 40 s, then 6 s of settling.  The balance is logged throughout
(~10 Hz) so the priming flow is on record.  Runs from Pico RAM via
``mpremote run``; nothing is written to the Pico filesystem.

    P,<t_ms>,<stat>,<grams>,<tilt>,<rpm>,<poll_ms>      one balance frame
    PRIME,<json>                                         summary
"""
import json
import time

import main_three_phase as m3

SPIN_RPM = 55.0
SPIN_S = 40.0
SETTLE_S = 6.0
TILT = 0.0

T0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), T0)


def frame(scale, tilt, rpm):
    t_a = time.ticks_ms()
    r = scale.read()
    stat, g = "NA", ""
    if r is not None:
        stat = r.status
        if r.grams is not None:
            g = "{:.4f}".format(r.grams)
    print("P,{},{},{},{:.1f},{:.1f},{}".format(
        t_ms(), stat, g, tilt, rpm, time.ticks_diff(time.ticks_ms(), t_a)))
    if r is None or r.grams is None or r.overload:
        return None
    return r.grams


def stream(scale, seconds, tilt, rpm, stepper=None):
    vals = []
    end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        if stepper is not None:
            stepper.keep_alive()
        g = frame(scale, tilt, rpm)
        if g is not None:
            vals.append(g)
        time.sleep_ms(5)
    return vals


def median(v):
    if not v:
        return None
    v = sorted(v)
    return v[len(v) // 2]


tap = m3.Tap()
servo = m3.Servo()
stepper = m3.Stepper()
scale = m3.Scale()
servo.move_to(TILT)
pre = stream(scale, 2.0, TILT, 0.0)
m0 = median(pre[-8:])
print("PRIME_SPIN_START,{}".format(t_ms()))
try:
    stepper.run_at_rpm(SPIN_RPM)
    stream(scale, SPIN_S, TILT, SPIN_RPM, stepper)
finally:
    stepper.stop()
    print("PRIME_SPIN_STOP,{}".format(t_ms()))
post = stream(scale, SETTLE_S, TILT, 0.0)
m1 = median(post[-8:])
print("PRIME," + json.dumps({
    "tilt_deg": TILT, "rpm": SPIN_RPM, "spin_s": SPIN_S,
    "revs": SPIN_RPM / 60.0 * SPIN_S,
    "m0_abs_g": m0, "m1_abs_g": m1,
    "gain_g": None if (m0 is None or m1 is None) else round(m1 - m0, 4)}))

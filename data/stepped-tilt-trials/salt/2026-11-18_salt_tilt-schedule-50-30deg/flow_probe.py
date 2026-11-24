"""One flow probe after two stalled launches (PR #131, version 2026-11-18c).

5 single taps at 0 deg (stock 60 ms pulse, 1.5 s apart), then 2.75 auger
revolutions at 55 rpm with the plate at 30 deg (this morning's probe: 90 mg
there), then back to 0 deg.  Balance logged throughout (~10 Hz).  Runs from
Pico RAM via ``mpremote run``; nothing is written to the Pico.

    P,<t_ms>,<stat>,<grams>,<tilt>,<rpm>,<poll_ms>,<step>   one balance frame
    PROBE,<json>                                            per-step summary
"""
import json
import time

import main_three_phase as m3

T0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), T0)


class S:
    tilt = 0.0
    rpm = 0.0
    step = "pre"


def frame(scale):
    t_a = time.ticks_ms()
    r = scale.read()
    stat, g = "NA", ""
    if r is not None:
        stat = r.status
        if r.grams is not None:
            g = "{:.4f}".format(r.grams)
    print("P,{},{},{},{:.1f},{:.1f},{},{}".format(
        t_ms(), stat, g, S.tilt, S.rpm,
        time.ticks_diff(time.ticks_ms(), t_a), S.step))
    if r is None or r.grams is None or r.overload:
        return None
    return r.grams


def stream(scale, seconds, stepper=None):
    vals = []
    end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        if stepper is not None:
            stepper.keep_alive()
        g = frame(scale)
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
out = {}
try:
    servo.move_to(0.0)
    S.tilt = 0.0
    m0 = median(stream(scale, 2.0)[-8:])
    S.step = "taps0"
    for i in range(5):
        tap.tap(1, 60, 0)
        print("E,{},tap {}".format(t_ms(), i + 1))
        stream(scale, 1.5)
    m1 = median(stream(scale, 2.0)[-8:])
    out["taps_0deg_g"] = None if None in (m0, m1) else round(m1 - m0, 4)
    S.step = "tilt30"
    servo.move_to(30.0)
    S.tilt = 30.0
    m2 = median(stream(scale, 1.5)[-8:])
    S.step = "spin30"
    stepper.run_at_rpm(55.0)
    S.rpm = 55.0
    stream(scale, 3.0, stepper)        # 2.75 rev at 55 rpm
    stepper.stop()
    S.rpm = 0.0
    S.step = "settle30"
    m3_ = median(stream(scale, 3.0)[-8:])
    out["spin_30deg_2.75rev_g"] = None if None in (m2, m3_) else round(m3_ - m2, 4)
finally:
    try:
        stepper.stop()
    except Exception:
        pass
    S.step = "home"
    servo.move_to(0.0)
    S.tilt = 0.0
    stream(scale, 1.0)
    print("PROBE," + json.dumps(out))

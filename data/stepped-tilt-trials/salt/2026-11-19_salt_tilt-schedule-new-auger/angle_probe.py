"""Per-angle flow probe on the new auger (PR #131, 2026-11-19, version 2026-11-19a).

Repeats the 2026-11-18 06:53 UTC probe from the first attempt: 2.75 auger
revolutions at 55 rpm with the plate at 55, 50, 45, 40, 35 and 30 deg, then
60 deg twice, then back to 0 deg.  Each step: move the plate, log 1.5 s,
spin 3.0 s, log 3.0 s of settling.  Balance logged throughout (~10 Hz).
Runs from Pico RAM via ``mpremote run``; nothing is written to the Pico.

    P,<t_ms>,<stat>,<grams>,<tilt>,<rpm>,<poll_ms>,<step>   one balance frame
    E,<t_ms>,<event>
    PROBE,<json>                                            summary
"""
import json
import time

import main_three_phase as m3

ANGLES = (55.0, 50.0, 45.0, 40.0, 35.0, 30.0, 60.0, 60.0)
RPM = 55.0
SPIN_S = 3.0          # 2.75 rev at 55 rpm
PRE_S = 1.5
SETTLE_S = 3.0

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
    if r.grams > 95.0:
        raise RuntimeError("display over 95 g")
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
steps = []
try:
    servo.move_to(0.0)
    S.tilt = 0.0
    stream(scale, 1.5)
    for k, a in enumerate(ANGLES):
        S.step = "tilt{:.0f}_{}".format(a, k + 1)
        servo.move_to(a)
        S.tilt = a
        print("E,{},servo at {:.1f} deg".format(t_ms(), a))
        m_a = median(stream(scale, PRE_S)[-6:])
        S.step = "spin{:.0f}_{}".format(a, k + 1)
        stepper.run_at_rpm(RPM)
        S.rpm = RPM
        print("E,{},auger run {:.1f} rpm".format(t_ms(), RPM))
        stream(scale, SPIN_S, stepper)
        stepper.stop()
        S.rpm = 0.0
        print("E,{},auger halt".format(t_ms()))
        S.step = "settle{:.0f}_{}".format(a, k + 1)
        m_b = median(stream(scale, SETTLE_S)[-6:])
        g = None if None in (m_a, m_b) else round(m_b - m_a, 4)
        steps.append({"k": k + 1, "tilt_deg": a, "revs": RPM / 60.0 * SPIN_S,
                      "m_before_abs_g": m_a, "m_after_abs_g": m_b, "gain_g": g})
        print("STEP," + json.dumps(steps[-1]))
finally:
    try:
        stepper.stop()
    except Exception:
        pass
    S.step = "home"
    S.rpm = 0.0
    servo.move_to(0.0)
    S.tilt = 0.0
    stream(scale, 1.5)
    print("PROBE," + json.dumps({"steps": steps}))

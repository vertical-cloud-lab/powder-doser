"""Tapped priming spin + tap on/off check (PR #131, 2026-11-19c, new auger tube).

Run between launches after launch 2 stopped on its safety rule: does salt
still reach the outlet, and do the taps still change the flow?

1. plate 0 deg, auger 55 rpm WITH taps (one 60 ms pulse per 300 ms), 30 s
2. plate 45 deg, auger 55 rpm: 10 s auger only, 10 s with taps, 10 s auger only
Each spin is followed by 4 s of settling; every balance frame is logged.
Keeps only the last 8 readings in memory (the 11-19 prime_spin.py ran out
of memory keeping all of them).  Runs from Pico RAM via ``mpremote run``.

    P,<t_ms>,<stat>,<grams>,<tilt>,<rpm>,<taps>,<step>,<poll_ms>   one frame
    E,<t_ms>,<event>
    STEP,<json>                                    one per spin
    PRIMECHECK,<json>                              summary
"""
import json
import time

import main_three_phase as m3

RPM = 55.0
TAP_ON_MS = 60
TAP_PERIOD_MS = 300
STEPS = (                     # name, plate deg, spin s, taps
    ("prime0_taps", 0.0, 30.0, True),
    ("a45_auger", 45.0, 10.0, False),
    ("b45_taps", 45.0, 10.0, True),
    ("c45_auger", 45.0, 10.0, False),
)
SETTLE_S = 4.0
MOVE_LOG_S = 1.5

T0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), T0)


class S:
    tilt = 0.0
    rpm = 0.0
    taps = 0
    step = "pre"


def frame(scale):
    t_a = time.ticks_ms()
    r = scale.read()
    stat, g = "NA", ""
    if r is not None:
        stat = r.status
        if r.grams is not None:
            g = "{:.4f}".format(r.grams)
    print("P,{},{},{},{:.1f},{:.1f},{},{},{}".format(
        t_ms(), stat, g, S.tilt, S.rpm, S.taps, S.step,
        time.ticks_diff(time.ticks_ms(), t_a)))
    if r is None or r.grams is None or r.overload:
        return None
    return r.grams


def run_for(scale, seconds, stepper=None, tap=None):
    last = []
    end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
    next_tap = time.ticks_ms()
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        if stepper is not None:
            stepper.keep_alive()
        if tap is not None and time.ticks_diff(time.ticks_ms(), next_tap) >= 0:
            tap.tap(1, TAP_ON_MS, 0)
            S.taps += 1
            next_tap = time.ticks_add(next_tap, TAP_PERIOD_MS)
            if time.ticks_diff(time.ticks_ms(), next_tap) > 0:
                next_tap = time.ticks_add(time.ticks_ms(), TAP_PERIOD_MS)
        g = frame(scale)
        if g is not None:
            last.append(g)
            if len(last) > 8:
                last.pop(0)
        time.sleep_ms(5)
    return last


def med(v):
    if not v:
        return None
    v = sorted(v)
    return v[len(v) // 2]


tap = m3.Tap()
servo = m3.Servo()
stepper = m3.Stepper()
scale = m3.Scale()
results = []
try:
    servo.move_to(0.0)
    S.tilt = servo.angle
    m_prev = med(run_for(scale, 2.0))
    for name, tilt, secs, taps in STEPS:
        if abs(servo.angle - tilt) > 0.05:
            print("E,{},servo {:.1f} -> {:.1f} deg".format(t_ms(), servo.angle, tilt))
            servo.move_to(tilt)
            S.tilt = servo.angle
            S.step = name + "_move"
            m_prev = med(run_for(scale, MOVE_LOG_S))
        S.step = name
        taps0 = S.taps
        print("E,{},step {} start ({:.1f} deg, {} rpm, taps {})".format(
            t_ms(), name, tilt, RPM, "on" if taps else "off"))
        stepper.run_at_rpm(RPM)
        S.rpm = RPM
        try:
            run_for(scale, secs, stepper, tap if taps else None)
        finally:
            stepper.stop()
            S.rpm = 0.0
            print("E,{},step {} auger halt".format(t_ms(), name))
        S.step = name + "_settle"
        m1 = med(run_for(scale, SETTLE_S))
        rec = {"step": name, "tilt_deg": tilt, "spin_s": secs,
               "revs": round(RPM / 60.0 * secs, 2), "taps": S.taps - taps0,
               "m0_abs_g": m_prev, "m1_abs_g": m1,
               "gain_mg": (None if (m_prev is None or m1 is None)
                           else round(1000.0 * (m1 - m_prev), 1))}
        print("STEP," + json.dumps(rec))
        results.append(rec)
        m_prev = m1
finally:
    for f in (stepper.stop, lambda: stepper.enable(False), tap._off,
              lambda: servo.move_to(0.0)):
        try:
            f()
        except Exception:
            pass
    print("PRIMECHECK," + json.dumps(results))

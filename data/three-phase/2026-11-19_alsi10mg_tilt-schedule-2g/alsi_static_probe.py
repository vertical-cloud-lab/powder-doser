# Static-tilt pour probe before the AlSi10Mg trials (PR #131, 2026-11-19e).
# Runs on the Pico via `mpremote run` (RAM only).  The auger never turns and
# the tapper never fires: the plate goes 0 -> 30 -> 40 -> 50 -> 60 -> 0 deg,
# holding each angle HOLD_S while every balance frame is printed.  It checks
# that this powder does not pour out of a still tube at the bulk angles (the
# salt didn't up to 72 deg on 2026-07-31).  Any rise of more than
# POUR_ABORT_G over the start returns the plate to 0 deg at once.
import time
import main_three_phase as m3

HOLD_S = 4.0
ANGLES = (30.0, 40.0, 50.0, 60.0)
POUR_ABORT_G = 0.5

servo = m3.Servo()
scale = m3.Scale()
T0 = time.ticks_ms()
S = {"m0": None, "abort": None}


def t():
    return time.ticks_diff(time.ticks_ms(), T0)


def hold(seconds, tag):
    end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
    vals = []
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        r = scale.read()
        if r is None or r.grams is None:
            print("P,{},{},{:.1f},NA,".format(t(), tag, servo.angle))
        else:
            print("P,{},{},{:.1f},{},{:.4f}".format(t(), tag, servo.angle,
                                                    r.status, r.grams))
            vals.append(r.grams)
            if (S["m0"] is not None and
                    r.grams - S["m0"] > POUR_ABORT_G):
                S["abort"] = "{:.4f} g over the start at {:.1f} deg".format(
                    r.grams - S["m0"], servo.angle)
                return vals
        time.sleep_ms(80)
    return vals


def med(v):
    if not v:
        return None
    v = sorted(v)
    return v[len(v) // 2]


try:
    print("PROBE_START,{}".format(t()))
    servo.move_to(0.0)
    v = hold(3.0, "start")
    S["m0"] = med(v[-8:])
    print("M0,{}".format(S["m0"]))
    for a in ANGLES:
        print("E,{},servo -> {:.1f}".format(t(), a))
        servo.move_to(a)
        v = hold(HOLD_S, "hold{:.0f}".format(a))
        print("ANGLE,{:.1f},{}".format(a, med(v[-6:])))
        if S["abort"]:
            break
finally:
    servo.move_to(0.0)
    v = hold(3.0, "end")
    print("END,{},{}".format(med(v[-8:]), S["abort"]))

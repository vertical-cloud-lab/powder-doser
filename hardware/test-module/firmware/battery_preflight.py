"""Pre-flight feed check for the uniform powder battery (issue #116).

The battery takes ~45 minutes.  A capped outlet, an auger that is not
seated in the drive coupler, or an empty delivery section all produce
the same flat-zero data that a genuinely cohesive powder does -- and
that ambiguity is exactly what invalidated the first brown-rice-flour
run (2026-08-04).  This module answers one question in ~1 minute,
*before* the battery starts:

    does turning the auger convey powder at all?

Sequence (tilt 90 deg = fully vertical, the most favourable geometry):

1. tare
2. ``revs`` x 360 deg auger rotations at 30 RPM, stable reading after each
3. ``taps`` solenoid taps, stable reading after

Interpretation:

- rotation moves tens of mg per revolution  -> feed confirmed, run the battery
- rotation ~0 but taps move mass            -> **no-feed**: powder past the
  blockage shakes loose, nothing is conveyed.  Check the cap / coupler /
  delivery flights before spending 45 minutes.
- rotation ~0 *and* taps ~0                 -> empty or fully blocked.

Emits machine-readable lines on stdout so a host can parse them::

    PRE,rev,<i>,<before_g>,<after_g>,<delta_g>
    PRE,tap,<n>,<before_g>,<after_g>,<delta_g>
    PRE,END,<verdict>,<rotation_delta_g>,<taps_delta_g>

Run on the Pico::

    import battery_preflight; battery_preflight.run()
"""

import time

try:
    _sleep_ms = time.sleep_ms                 # MicroPython
except AttributeError:                        # CPython (sim/tests)
    def _sleep_ms(ms):
        time.sleep(ms / 1000.0)

PLATE_PER_TILT = 0.5      # mounting-plate degrees per user-facing tilt degree

TILT_DEG = 90.0           # fully vertical: most favourable for feeding
REVS = 5                  # 360 deg auger rotations
RPM = 30.0
TAPS = 10
TAP_ON_MS = 60
TAP_OFF_MS = 150
SETTLE_MS = 2000
TILT_SETTLE_MS = 2000
STABLE_TIMEOUT_MS = 10000

# A revolution that conveys at least this much is unambiguous feed.
FEED_OK_G = 0.005         # 5 mg/rev summed over REVS -> 25 mg


def _read_grams(scale, timeout_ms=STABLE_TIMEOUT_MS):
    reading = scale.read_stable(timeout_ms=timeout_ms)
    if (reading is None or not reading.stable or reading.overload or
            reading.grams is None):
        return None
    unit = getattr(reading, "unit", "g")
    if unit and unit != "g":
        print("[preflight] scale reports {!r}, not grams".format(unit))
        return None
    return reading.grams


def check(stepper, tap, servo, scale, revs=REVS, rpm=RPM, taps=TAPS,
          tilt_deg=TILT_DEG, settle_ms=SETTLE_MS, log=print, sleep_ms=None):
    """Run the feed check with already-constructed drivers.

    Returns a dict with per-revolution deltas, the tap delta and a
    verdict string (``feed confirmed`` / ``suspect-no-feed`` /
    ``empty-or-blocked`` / ``scale-unreadable``).
    """
    sleep_ms = sleep_ms or _sleep_ms
    servo.move_to(tilt_deg * PLATE_PER_TILT)
    sleep_ms(TILT_SETTLE_MS)
    stepper.set_speed(rpm)
    scale.zero()
    sleep_ms(settle_ms)

    rev_deltas = []
    before = _read_grams(scale)
    if before is None:
        log("[preflight] scale unreadable")
        print("PRE,END,scale-unreadable,0,0")
        return {"tilt_deg": tilt_deg, "rev_deltas": [], "rotation_delta_g": 0.0,
                "taps_delta_g": 0.0, "verdict": "scale-unreadable"}

    for i in range(revs):
        stepper.rotate_degrees(360.0)
        sleep_ms(settle_ms)
        after = _read_grams(scale)
        if after is None:
            log("[preflight] scale unreadable at revolution {}".format(i))
            break
        delta = after - before
        rev_deltas.append(delta)
        print("PRE,rev,{},{:.4f},{:.4f},{:.4f}".format(i, before, after, delta))
        before = after

    rotation_total = sum(rev_deltas)

    tap_before = before
    tap.tap(taps, TAP_ON_MS, TAP_OFF_MS)
    sleep_ms(settle_ms)
    tap_after = _read_grams(scale)
    taps_delta = 0.0 if tap_after is None else tap_after - tap_before
    print("PRE,tap,{},{:.4f},{:.4f},{:.4f}".format(
        taps, tap_before, 0.0 if tap_after is None else tap_after, taps_delta))

    if rotation_total >= FEED_OK_G:
        verdict = "feed confirmed"
    elif taps_delta >= FEED_OK_G:
        verdict = "suspect-no-feed"
    else:
        verdict = "empty-or-blocked"

    print("PRE,END,{},{:.4f},{:.4f}".format(
        verdict, rotation_total, taps_delta))
    log("[preflight] {} rev -> {:.4f} g ({:.2f} mg/rev), {} taps -> "
        "{:.4f} g :: {}".format(
            len(rev_deltas), rotation_total,
            1000.0 * rotation_total / len(rev_deltas) if rev_deltas else 0.0,
            taps, taps_delta, verdict))
    return {
        "tilt_deg": tilt_deg,
        "rpm": rpm,
        "rev_deltas": rev_deltas,
        "rotation_rev_total": len(rev_deltas),
        "rotation_delta_g": rotation_total,
        "taps_total": taps,
        "taps_delta_g": taps_delta,
        "verdict": verdict,
    }


def run(**overrides):
    """Bring up the drivers and run the feed check (Pico entry point)."""
    import config                                        # noqa: F401
    import main_three_phase as m3p

    stepper = m3p.Stepper()
    tap = m3p.Tap()
    servo = m3p.Servo()
    scale = m3p.Scale()
    try:
        return check(stepper, tap, servo, scale, **overrides)
    finally:
        for teardown in (stepper.stop, lambda: stepper.enable(False),
                         tap._off, lambda: servo.move_to(0.0)):
            try:
                teardown()
            except Exception:
                pass

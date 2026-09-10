"""Escalating feed diagnostic: cohesion/arching vs mechanical no-feed.

``battery_preflight`` answers "does the auger convey?".  When the answer
is no, this module answers the follow-up: *why* not.  The two causes look
identical on the balance for a single short rotation, but they separate
under escalation:

============================  ==========================================
Observation                   Interpretation
============================  ==========================================
long rotation conveys         cohesive but workable -- slow feed
rotation dead, taps alive,    **arching / ratholing**: agitation collapses
then rotation conveys         the arch and the screw picks up again
rotation dead before *and*    **mechanical no-feed**: capped outlet, auger
after agitation, taps alive   not seated in the coupler, or an empty
                              delivery section.  Nothing is conveyed;
                              taps only shake loose what is already past
                              the obstruction.
everything dead               empty column or a full blockage
============================  ==========================================

The stepper's own commanded-vs-actual position is logged at every stage,
so a driver-side stall is ruled out separately from the powder.  Note
this confirms the *motor* turned, never that the *tube* turned with it.

Stages (all at tilt 90 deg, the most favourable geometry):

1. ``long``    -- 10 continuous revolutions at 60 RPM
2. ``fast``    -- 10 continuous revolutions at 90 RPM (fluidisation attempt)
3. ``agitate`` -- 3 x (20 taps, then 5 x 360 deg at 30 RPM), each measured
                  separately so post-agitation rotation is isolated

Emits::

    DIAG,<stage>,<label>,<before_g>,<after_g>,<delta_g>,<steps_commanded>,<steps_actual>
    DIAG,END,<verdict>,<rotation_g>,<taps_g>,<post_agitation_rotation_g>

Run on the Pico::

    import battery_feed_diagnostic as d; d.run()
"""

import time

try:
    _sleep_ms = time.sleep_ms                 # MicroPython
except AttributeError:                        # CPython (sim/tests)
    def _sleep_ms(ms):
        time.sleep(ms / 1000.0)

PLATE_PER_TILT = 0.5

TILT_DEG = 90.0
LONG_REVS = 10
LONG_RPM = 60.0
FAST_REVS = 10
FAST_RPM = 90.0
AGITATE_ROUNDS = 3
AGITATE_TAPS = 20
AGITATE_REVS = 5
AGITATE_RPM = 30.0
TAP_ON_MS = 60
TAP_OFF_MS = 150
SETTLE_MS = 2500
TILT_SETTLE_MS = 2000
STABLE_TIMEOUT_MS = 10000

# Above this a stage is "conveying" rather than balance noise.
MOVED_G = 0.005


def _read_grams(scale, timeout_ms=STABLE_TIMEOUT_MS):
    reading = scale.read_stable(timeout_ms=timeout_ms)
    if (reading is None or not reading.stable or reading.overload or
            reading.grams is None):
        return None
    return reading.grams


def _position(stepper):
    """Stepper's own position counter, or ``None`` if unavailable."""
    try:
        return stepper.tic.current_position()
    except Exception:
        return None


def diagnose(stepper, tap, servo, scale, tilt_deg=TILT_DEG,
             settle_ms=SETTLE_MS, log=print, sleep_ms=None):
    """Run the escalation with already-constructed drivers."""
    sleep_ms = sleep_ms or _sleep_ms
    servo.move_to(tilt_deg * PLATE_PER_TILT)
    sleep_ms(TILT_SETTLE_MS)
    scale.zero()
    sleep_ms(settle_ms)

    stages = []

    def measure(stage, label, action, expected_deg=0.0):
        before = _read_grams(scale)
        pos0 = _position(stepper)
        action()
        sleep_ms(settle_ms)
        after = _read_grams(scale)
        pos1 = _position(stepper)
        if before is None or after is None:
            log("[diag] scale unreadable during {}/{}".format(stage, label))
            return None
        delta = after - before
        moved = None if (pos0 is None or pos1 is None) else abs(pos1 - pos0)
        print("DIAG,{},{},{:.4f},{:.4f},{:.4f},{},{}".format(
            stage, label, before, after, delta,
            "" if expected_deg is None else expected_deg,
            "" if moved is None else moved))
        row = {"stage": stage, "label": label, "before_g": before,
               "after_g": after, "delta_g": delta, "steps_moved": moved,
               "expected_deg": expected_deg}
        stages.append(row)
        return row

    def spin(revs, rpm):
        def _do():
            stepper.set_speed(rpm)
            stepper.run_at_rpm(rpm)
            spin_ms = revs / rpm * 60.0 * 1000
            waited = 0
            while waited < spin_ms:
                # max(1, ...) so a sub-millisecond remainder cannot make
                # the step zero and spin this loop forever.
                step = min(200, max(1, int(spin_ms - waited)))
                sleep_ms(step)
                waited += step
                try:
                    stepper.keep_alive()
                except Exception:
                    pass
            stepper.stop()
        return _do

    long_row = measure("long", "{}rev@{}rpm".format(LONG_REVS, int(LONG_RPM)),
                       spin(LONG_REVS, LONG_RPM), LONG_REVS * 360.0)
    fast_row = measure("fast", "{}rev@{}rpm".format(FAST_REVS, int(FAST_RPM)),
                       spin(FAST_REVS, FAST_RPM), FAST_REVS * 360.0)

    taps_g = 0.0
    post_agitation_g = 0.0
    for round_i in range(AGITATE_ROUNDS):
        tap_row = measure(
            "agitate", "taps{}x{}".format(round_i, AGITATE_TAPS),
            lambda: tap.tap(AGITATE_TAPS, TAP_ON_MS, TAP_OFF_MS), 0.0)
        if tap_row:
            taps_g += tap_row["delta_g"]

        def rotate():
            stepper.set_speed(AGITATE_RPM)
            for _ in range(AGITATE_REVS):
                stepper.rotate_degrees(360.0)

        rot_row = measure("agitate", "rot{}x{}rev".format(round_i, AGITATE_REVS),
                          rotate, AGITATE_REVS * 360.0)
        if rot_row:
            post_agitation_g += rot_row["delta_g"]

    rotation_g = ((long_row["delta_g"] if long_row else 0.0) +
                  (fast_row["delta_g"] if fast_row else 0.0))

    if rotation_g >= MOVED_G:
        verdict = "conveying-slowly"
    elif post_agitation_g >= MOVED_G:
        verdict = "arching-responds-to-agitation"
    elif taps_g >= MOVED_G:
        verdict = "mechanical-no-feed"
    elif taps_g > 0:
        verdict = "mechanical-no-feed-marginal"
    else:
        verdict = "empty-or-fully-blocked"

    print("DIAG,END,{},{:.4f},{:.4f},{:.4f}".format(
        verdict, rotation_g, taps_g, post_agitation_g))
    log("[diag] rotation {:.4f} g, taps {:.4f} g, post-agitation rotation "
        "{:.4f} g :: {}".format(rotation_g, taps_g, post_agitation_g, verdict))
    return {
        "tilt_deg": tilt_deg,
        "stages": stages,
        "rotation_g": rotation_g,
        "taps_g": taps_g,
        "post_agitation_rotation_g": post_agitation_g,
        "rotation_revs": LONG_REVS + FAST_REVS,
        "taps_total": AGITATE_ROUNDS * AGITATE_TAPS,
        "post_agitation_revs": AGITATE_ROUNDS * AGITATE_REVS,
        "verdict": verdict,
    }


def run(**overrides):
    """Bring up the drivers and run the diagnostic (Pico entry point)."""
    import config                                        # noqa: F401
    import main_three_phase as m3p

    stepper = m3p.Stepper()
    tap = m3p.Tap()
    servo = m3p.Servo()
    scale = m3p.Scale()
    try:
        return diagnose(stepper, tap, servo, scale, **overrides)
    finally:
        for teardown in (stepper.stop, lambda: stepper.enable(False),
                         tap._off, lambda: servo.move_to(0.0)):
            try:
                teardown()
            except Exception:
                pass

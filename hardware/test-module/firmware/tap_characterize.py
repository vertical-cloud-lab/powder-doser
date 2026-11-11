"""Single-tap yield / lip-depletion characterization (PR #131 request).

Runs ON the Pico via ``mpremote run`` (RAM only -- nothing is written to
the Pico's filesystem).  Re-uses main_three_phase's hardware driver
classes (Stepper / Servo / Tap / Scale) but implements no dose logic.

Purpose
-------
Test the tap model hypothesised in the Edison MPC review
(``optimization/edison/mpc-data-collection/query.answer.md``):

    "Define a lip inventory state x_lip that taps drain and auger
     rotations refill.  Each tap removes dm_tap = g_tap(tilt, x_lip)
     from the lip, where g_tap decreases as x_lip depletes."

i.e. successive taps *without* re-feed should show diminishing returns,
and the yield of the first tap should depend on tilt.

Sequence (one "trial" = one (angle, replicate) pair)
---------------------------------------------------
1. move the plate to the trial tilt angle, settle
2. baseline stable weigh
3. PRIME: rotate the auger PRIME_DEG at PRIME_RPM -- this is what
   re-fills the lip, and is also the per-trial reset between replicates
4. settle, stable weigh (prime yield = auger delivery at this tilt)
5. CONTROL: N_CTRL wait-and-weigh intervals with NO tap -- measures
   spontaneous creep/drift at this tilt so tap yields are not confounded
   by powder that would have fallen anyway
6. TAPS: N_TAPS x (exactly ONE solenoid pulse, then raw-stream the
   landing tail, then a stable weigh).  Deliberately single taps, not
   bursts, so per-tap marginal yield is directly observable.
7. POST: N_POST no-tap intervals to confirm the tail has died

Replicate order alternates ascending/descending through the angle list
so slow drift (hopper drawdown, temperature) does not alias onto tilt.

Telemetry (CSV over USB stdout)
-------------------------------
    M,<key>,<value>                                     metadata
    P,<t_ms>,<trial>,<angle>,<rep>,<idx>,<kind>,<mass>  settled point
    D,<t_ms>,<trial>,<idx>,<kind>,<mass>,<S|U>          raw poll sample
    E,<t_ms>,<text>                                     event
``kind`` is one of: base, prime, ctrl, tap, post.
"""

import time
import main_three_phase as m3

POWDER_ID = "salt"
# True mounting-plate degrees.  The servo's mechanical ceiling is 90 plate
# deg (config.SERVO_MAX_ANGLE_DEG 180 / PLATE_GEAR_RATIO 2).  Steep tilts
# were cleared by a no-actuator safety probe on 2026-07-31: holding the
# plate at 25..72 deg produced 0.0 mg of spontaneous flow, so the tube
# does not free-pour and the auger/tap remain the only mass sources.
ANGLES = (0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0)
REPS = 3
PRIME_DEG = 360.0                  # one auger revolution re-feeds the lip
PRIME_RPM = 30.0
N_CTRL = 3                         # no-tap control intervals before taps
N_TAPS = 10                        # SINGLE taps, one at a time
N_POST = 2                         # no-tap intervals after the taps
TAP_ON_MS = 60                     # config.TAP_ON_MS -- one pulse only
TAIL_MS = 1000                     # raw-stream window after each tap
TAIL_DT_MS = 60
SETTLE_MS = 400                    # extra quiet before asking for stable
PRIME_SETTLE_MS = 3000             # in-flight powder after a rotation
STABLE_TIMEOUT_MS = 6000
MAX_CUP_G = 25.0                   # abort if the collection cup fills up
                                   # (single tare, so settled mass is the
                                   # session-cumulative delivered mass)

_t0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _t0)


def ev(msg):
    print("E,{},{}".format(t_ms(), msg))


def meta(k, v):
    print("M,{},{}".format(k, v))


class Rig:
    def __init__(self):
        self.scale = m3.Scale()
        self.stepper = m3.Stepper()
        self.servo = m3.Servo()
        self.tap = m3.Tap()
        self.trial = 0
        self.angle = 0.0
        self.rep = 0

    # -- measurement ---------------------------------------------------
    def stream(self, ms, idx, kind):
        """Raw Q-poll stream (keeps unstable frames) for ``ms``."""
        end = time.ticks_add(time.ticks_ms(), int(ms))
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            r = self.scale.read()
            if r is None or r.grams is None:
                print("D,{},{},{},{},nan,X".format(
                    t_ms(), self.trial, idx, kind))
            else:
                print("D,{},{},{},{},{:.4f},{}".format(
                    t_ms(), self.trial, idx, kind, r.grams,
                    "S" if r.stable else "U"))
            time.sleep_ms(TAIL_DT_MS)

    def settled(self, idx, kind):
        """Wait for a stable frame and log it as a settled point."""
        time.sleep_ms(SETTLE_MS)
        r = self.scale.read_stable(timeout_ms=STABLE_TIMEOUT_MS)
        if r is None or r.grams is None:
            ev("no stable frame for {} idx={}".format(kind, idx))
            r = self.scale.read()
        g = None if (r is None or r.grams is None) else r.grams
        print("P,{},{},{:.1f},{},{},{},{}".format(
            t_ms(), self.trial, self.angle, self.rep, idx, kind,
            "nan" if g is None else "{:.4f}".format(g)))
        return g

    # -- actuation -----------------------------------------------------
    def prime(self):
        """One auger rotation: the lip-inventory reset / re-feed."""
        self.stepper.set_speed(PRIME_RPM)
        self.stepper.enable(True)
        ev("prime rotate {:.0f} deg @ {:.0f} rpm".format(
            PRIME_DEG, PRIME_RPM))
        self.stepper.rotate_degrees(PRIME_DEG)
        self.stepper.stop()

    def single_tap(self):
        """Exactly one solenoid pulse -- no bursts."""
        self.tap.tap(1, on_ms=TAP_ON_MS, off_ms=0)

    # -- one trial -----------------------------------------------------
    def trial_run(self, angle, rep):
        self.trial += 1
        self.angle = angle
        self.rep = rep
        ev("=== trial {} : angle {:.1f} plate deg, rep {} ===".format(
            self.trial, angle, rep))
        self.servo.move_to(angle)
        time.sleep_ms(1200)

        base = self.settled(0, "base")
        if base is not None and base > MAX_CUP_G:
            ev("cup at {:.2f} g > {:.1f} g limit -- stopping".format(
                base, MAX_CUP_G))
            raise KeyboardInterrupt
        self.prime()
        self.stream(PRIME_SETTLE_MS, 0, "prime")
        self.settled(0, "prime")

        for i in range(1, N_CTRL + 1):
            self.stream(TAIL_MS, i, "ctrl")
            self.settled(i, "ctrl")

        for i in range(1, N_TAPS + 1):
            ev("tap {} (single pulse, {} ms)".format(i, TAP_ON_MS))
            self.single_tap()
            self.stream(TAIL_MS, i, "tap")
            self.settled(i, "tap")

        for i in range(1, N_POST + 1):
            self.stream(TAIL_MS, i, "post")
            self.settled(i, "post")


def main():
    meta("experiment", "tap-characterization")
    meta("powder_id", POWDER_ID)
    meta("angles_plate_deg", "|".join("{:.1f}".format(a) for a in ANGLES))
    meta("reps", REPS)
    meta("prime_deg", PRIME_DEG)
    meta("prime_rpm", PRIME_RPM)
    meta("n_ctrl", N_CTRL)
    meta("n_taps", N_TAPS)
    meta("n_post", N_POST)
    meta("tap_count_per_event", 1)
    meta("tap_on_ms", TAP_ON_MS)
    meta("tap_pwm_duty", m3.config.TAP_PWM_DUTY)
    meta("tail_ms", TAIL_MS)

    rig = Rig()
    try:
        rig.servo.move_to(0.0)
        ev("zeroing scale (single tare for the whole session)")
        rig.scale.zero()
        rig.scale.read_stable(timeout_ms=8000)
        for rep in range(1, REPS + 1):
            order = ANGLES if rep % 2 else tuple(reversed(ANGLES))
            for angle in order:
                rig.trial_run(angle, rep)
        ev("all trials complete")
    except KeyboardInterrupt:
        ev("KeyboardInterrupt -- stopping")
    finally:
        try:
            rig.stepper.tic.set_target_velocity(0)
            rig.stepper.stop()
        except Exception:
            pass
        try:
            rig.tap._off()
        except Exception:
            pass
        try:
            rig.servo._write_angle(0.0)
        except Exception:
            pass
    print("SUMMARY,trials={},taps_per_trial={}".format(rig.trial, N_TAPS))


main()

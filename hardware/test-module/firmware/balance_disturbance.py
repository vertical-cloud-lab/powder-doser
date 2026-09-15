"""Blocked-auger balance-disturbance characterization (PR #131, issue #157).

Runs ON the Pico via ``mpremote run`` (RAM only).  Re-uses
``main_three_phase``'s hardware driver classes; no dose-controller logic.

Question under test (PR #131 request, 2026-09-15)
--------------------------------------------------
A mechanically BLOCKED auger is installed, so no powder can dispense.
Every deviation the balance reports while actuators run is therefore
measurement disturbance (vibration coupling + fume-hood environment),
not mass.  This isolates the #162 Edison-review gaps:

  * R (measurement noise) from stationary readings AND under motor /
    tapper / servo disturbances, per actuation state;
  * post-disturbance settling behaviour (how long until the stream is
    back at the quiet floor -- the "balance settling wait");
  * ST/US stable-flag behaviour per actuation state (for adaptive
    stability detection);
  * the fume-hood quiet floor + drift itself (issue #157), bracketed by
    two long quiet windows.

Design notes
------------
* NO ``zero()`` anywhere: the A&D refuses Z under load (2026-09-08
  session) and drift analysis wants an unbroken absolute series.  All
  analysis is differences.
* Quiet windows interleave every actuation block so the fume-hood
  contribution can be subtracted from the actuation windows.
* Auger RPM ladder is run twice, second pass in reverse order, so any
  slow environmental trend cannot alias onto RPM.
* A mass guard halts everything if |m - m0| > GUARD_G (the auger is
  supposed to be blocked; if the block leaks, stop and say so).

Telemetry (CSV over USB stdout)
-------------------------------
    M,<key>,<value>                                metadata
    E,<t_ms>,<text>                                event / block marker
    D,<t_ms>,<block>,<mass|nan>,<S|U|X>,<rpm>,<taps>,<servo>   raw poll
    P,<t_ms>,<kind>,<mass|nan>                     settled point
    SESSION_END                                    sentinel (last line)
"""

import time
import main_three_phase as m3

# Mechanical configuration the battery is running against, stamped into the
# telemetry metadata.  r1/r2 (2026-09-15) ran "blocked-auger" (nominally
# blocked, then exit-covered); r3 runs "empty-auger" -- a clean auger with no
# powder anywhere, after the balance drift fix.  Edit per run.
CONFIG_LABEL = "empty-auger"

POLL_MS = 60                # same cadence the dose controllers use
QUIET_LONG_S = 120.0
QUIET_MID_S = 30.0
N_TAP_SINGLE = 20
TAP_WINDOW_S = 6.0          # 1 s pre-quiet, tap, ~5 s tail
N_TAP_BURST = 8
BURST_WINDOW_S = 8.0
TAP_ON_MS = 60              # resident-firmware tap config
TAP_OFF_MS = 150
RPM_LADDER = (15.0, 30.0, 55.0, 75.0)
SPIN_S = 15.0
POST_SPIN_S = 15.0
HOLD_S = 20.0               # stepper energized, velocity 0
N_ROT = 10                  # discrete fine-phase increments
ROT_DEG = 45.0
ROT_RPM = 30.0
ROT_GAP_S = 4.0
COMBINED_S = 20.0           # 55 rpm + 1 tap/s (rapid-dispense pattern)
COMBINED_RPM = 55.0
COMBINED_TAP_EVERY_S = 1.0
POST_COMBINED_S = 20.0
SERVO_TARGETS = (25.0, 60.0)
SERVO_DWELL_S = 6.0
GUARD_G = 5.0               # blocked auger: nothing should land

_t0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _t0)


def ev(msg):
    print("E,{},{}".format(t_ms(), msg))


def meta(k, v):
    print("M,{},{}".format(k, v))


class Guard(Exception):
    pass


class Rig:
    def __init__(self):
        self.scale = m3.Scale()
        self.stepper = m3.Stepper()
        self.servo = m3.Servo()
        self.tap = m3.Tap()
        self.taps = 0
        self.rpm = 0.0
        self.servo_deg = 0.0
        self.m0 = None
        self._sign = 1 if m3.config.STEPPER_DIRECTION >= 0 else -1

    def vel_for(self, rpm):
        return self._sign * max(
            1, int(rpm / 60.0 * self.stepper.steps_per_rev * 10000))

    def auger_run(self, rpm):
        self.stepper.set_speed(rpm)
        self.stepper.enable(True)
        self.stepper.tic.set_target_velocity(self.vel_for(rpm))
        self.rpm = rpm

    def auger_halt(self, deenergize=True):
        self.stepper.tic.set_target_velocity(0)
        if deenergize:
            self.stepper.stop()
        self.rpm = 0.0

    def halt_all(self):
        try:
            self.auger_halt()
        except Exception:
            pass
        try:
            self.tap._off()
        except Exception:
            pass

    def sample(self, block):
        r = self.scale.read()
        ts = t_ms()
        if r is None or r.grams is None:
            print("D,{},{},nan,X,{:.0f},{},{:.1f}".format(
                ts, block, self.rpm, self.taps, self.servo_deg))
            return None
        print("D,{},{},{:.4f},{},{:.0f},{},{:.1f}".format(
            ts, block, r.grams, "S" if r.stable else "U",
            self.rpm, self.taps, self.servo_deg))
        if self.m0 is not None and abs(r.grams - self.m0) > GUARD_G:
            ev("MASS_GUARD |m-m0|>{} g -- blocked auger leaking? HALT".format(
                GUARD_G))
            raise Guard()
        return r.grams

    def stream(self, seconds, block, spin_keepalive=False):
        end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            self.sample(block)
            if spin_keepalive:
                self.stepper.keep_alive()
            time.sleep_ms(POLL_MS)

    def settled(self, kind, timeout_ms=8000):
        r = self.scale.read_stable(timeout_ms=timeout_ms)
        if r is None or r.grams is None:
            ev("no stable frame for {}".format(kind))
            r = self.scale.read()
        g = None if (r is None or r.grams is None) else r.grams
        print("P,{},{},{}".format(
            t_ms(), kind, "nan" if g is None else "{:.4f}".format(g)))
        return g

    def block(self, name):
        ev("BLOCK_START,{}".format(name))

    def block_end(self, name):
        ev("BLOCK_END,{}".format(name))


def main():
    meta("experiment", CONFIG_LABEL + "-balance-disturbance")
    meta("powder_id", "none-" + CONFIG_LABEL)
    meta("poll_ms", POLL_MS)
    meta("rpm_ladder", "|".join("{:.0f}".format(r) for r in RPM_LADDER))
    meta("spin_s", SPIN_S)
    meta("n_tap_single", N_TAP_SINGLE)
    meta("n_tap_burst", N_TAP_BURST)
    meta("tap_on_off_ms", "{}|{}".format(TAP_ON_MS, TAP_OFF_MS))
    meta("n_rot", N_ROT)
    meta("rot_deg_rpm", "{:.0f}|{:.0f}".format(ROT_DEG, ROT_RPM))
    meta("combined_s_rpm", "{:.0f}|{:.0f}".format(COMBINED_S, COMBINED_RPM))
    meta("servo_targets", "|".join(
        "{:.0f}".format(a) for a in SERVO_TARGETS))
    meta("guard_g", GUARD_G)
    meta("note", "no zero(): A&D refuses Z under load; absolute series")

    rig = Rig()
    try:
        # reference points -- absolute pan mass, never tared
        for _ in range(3):
            rig.settled("ref_start")
            time.sleep_ms(400)
        r = rig.scale.read()
        rig.m0 = None if (r is None or r.grams is None) else r.grams
        meta("m0_abs_g", "nan" if rig.m0 is None else
             "{:.4f}".format(rig.m0))

        # 1 -- long quiet floor (fume hood + drift anchor)
        rig.block("quiet_pre")
        rig.stream(QUIET_LONG_S, "quiet_pre")
        rig.block_end("quiet_pre")

        # 2 -- single taps, one per window
        rig.block("tap_single")
        for i in range(N_TAP_SINGLE):
            rig.stream(1.0, "tap_single")
            ev("TAP,{}".format(i + 1))
            rig.tap.tap(1, on_ms=TAP_ON_MS, off_ms=0)
            rig.taps += 1
            rig.stream(TAP_WINDOW_S - 1.0, "tap_single")
        rig.block_end("tap_single")

        rig.block("quiet_mid1")
        rig.stream(QUIET_MID_S, "quiet_mid1")
        rig.block_end("quiet_mid1")

        # 3 -- standard 3-pulse bursts (the resident `t` pattern)
        rig.block("tap_burst")
        for i in range(N_TAP_BURST):
            rig.stream(1.0, "tap_burst")
            ev("BURST,{}".format(i + 1))
            rig.tap.tap(3, on_ms=TAP_ON_MS, off_ms=TAP_OFF_MS)
            rig.taps += 3
            rig.stream(BURST_WINDOW_S - 1.0, "tap_burst")
        rig.block_end("tap_burst")

        rig.block("quiet_mid2")
        rig.stream(QUIET_MID_S, "quiet_mid2")
        rig.block_end("quiet_mid2")

        # 4 -- continuous auger RPM ladder, two passes, reversed second
        for p, ladder in ((1, RPM_LADDER), (2, tuple(reversed(RPM_LADDER)))):
            for rpm in ladder:
                name = "auger{:.0f}_p{}".format(rpm, p)
                rig.block(name)
                rig.auger_run(rpm)
                rig.stream(SPIN_S, name, spin_keepalive=True)
                rig.auger_halt()
                rig.block_end(name)
                post = "post_" + name
                rig.block(post)
                rig.stream(POST_SPIN_S, post)
                rig.block_end(post)

        rig.block("quiet_mid3")
        rig.stream(QUIET_MID_S, "quiet_mid3")
        rig.block_end("quiet_mid3")

        # 5 -- stepper energized but not moving (between-increment state)
        rig.block("stepper_hold")
        rig.stepper.set_speed(RPM_LADDER[0])
        rig.stepper.enable(True)
        rig.stepper.tic.set_target_velocity(0)
        rig.stream(HOLD_S, "stepper_hold", spin_keepalive=True)
        rig.auger_halt()
        rig.block_end("stepper_hold")

        # 6 -- discrete fine-phase increments (blocking rotate)
        rig.block("auger_steps")
        rig.stepper.set_speed(ROT_RPM)
        for i in range(N_ROT):
            rig.stream(ROT_GAP_S / 2.0, "auger_steps")
            ev("ROT_START,{}".format(i + 1))
            rig.rpm = ROT_RPM
            rig.stepper.rotate_degrees(ROT_DEG)
            rig.rpm = 0.0
            ev("ROT_END,{}".format(i + 1))
            rig.stream(ROT_GAP_S / 2.0, "auger_steps")
        rig.stepper.stop()
        rig.block_end("auger_steps")

        rig.block("quiet_mid4")
        rig.stream(QUIET_MID_S, "quiet_mid4")
        rig.block_end("quiet_mid4")

        # 7 -- rapid-dispense pattern: spin + tap-while-rotating
        rig.block("combined")
        rig.auger_run(COMBINED_RPM)
        end = time.ticks_add(time.ticks_ms(), int(COMBINED_S * 1000))
        next_tap = time.ticks_add(
            time.ticks_ms(), int(COMBINED_TAP_EVERY_S * 1000))
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            rig.sample("combined")
            rig.stepper.keep_alive()
            if time.ticks_diff(time.ticks_ms(), next_tap) >= 0:
                rig.tap.tap(1, on_ms=TAP_ON_MS, off_ms=0)
                rig.taps += 1
                next_tap = time.ticks_add(
                    next_tap, int(COMBINED_TAP_EVERY_S * 1000))
            time.sleep_ms(POLL_MS)
        rig.auger_halt()
        rig.block_end("combined")
        rig.block("post_combined")
        rig.stream(POST_COMBINED_S, "post_combined")
        rig.block_end("post_combined")

        # 8 -- servo tilt moves (empty pan disturbance only)
        rig.block("servo_moves")
        for tgt in SERVO_TARGETS:
            ev("SERVO_MOVE,0->{:.0f}".format(tgt))
            rig.servo.move_to(tgt)
            rig.servo_deg = tgt
            rig.stream(SERVO_DWELL_S, "servo_moves")
            ev("SERVO_MOVE,{:.0f}->0".format(tgt))
            rig.servo.move_to(0.0)
            rig.servo_deg = 0.0
            rig.stream(SERVO_DWELL_S, "servo_moves")
        rig.block_end("servo_moves")

        # 9 -- long quiet close (drift anchor #2)
        rig.block("quiet_post")
        rig.stream(QUIET_LONG_S, "quiet_post")
        rig.block_end("quiet_post")

        for _ in range(3):
            rig.settled("ref_end")
            time.sleep_ms(400)
        ev("battery complete")
    except Guard:
        ev("stopped by mass guard")
    except KeyboardInterrupt:
        ev("KeyboardInterrupt -- stopping")
    finally:
        rig.halt_all()
        try:
            rig.servo._write_angle(0.0)
        except Exception:
            pass
    print("SUMMARY,taps_total={}".format(rig.taps))
    print("SESSION_END")


main()

"""Rapid-dispense stop-response characterization (PR #131 request).

Runs ON the Pico via ``mpremote run`` (RAM only -- nothing is written to
the Pico's filesystem).  Re-uses main_three_phase's hardware driver
classes (Stepper velocity mode / Servo plate degrees / Tap / Scale); no
dose-controller logic.

Question under test
-------------------
How well can the rig dose at a *rapid* pace -- high tilt, fast auger
RPM, tapping while rotating -- if all actuation halts the instant the
scale FIRST reads the goal mass?  The quantities of interest are:

  * the mass reading at the halt trigger (first sample >= 0.5 g),
  * the settled mass after everything stops (in-flight / afterflow
    overshoot = settled - trigger),
  * scale noise during dispensing vs. static (one-time baseline).

Sequence
--------
0. NOISE BASELINE (once): tare at 0 deg tilt, then a 60 s raw Q-poll
   stream with nothing actuating (keeps unstable frames), then five
   stable reads.  This is the static noise floor every later number is
   compared against.
1. Per trial (angle, rep):
   a. plate to the trial tilt, settle; absolute (pre-tare) stable weigh
      for cup accounting; tare; 2 s pre-roll stream.
   b. RAPID DISPENSE: auger continuous at FAST_RPM, one solenoid pulse
      every TAP_EVERY-th poll loop (tapping while rotating).  Poll the
      scale as fast as it answers; the FIRST reading (stable or not)
      >= TRIGGER_G halts ALL actuation immediately (velocity -> 0, tap
      off).  Latency between the trigger sample and the stop commands
      is a few ms (same loop iteration).
   c. SETTLE: 15 s raw stream at the trial tilt (nothing moving), then
      a stable weigh, then 5 s more and a confirmation stable weigh.
2. Replicate order alternates through the angle list so hopper drawdown
   does not alias onto tilt.

Telemetry (CSV over USB stdout)
-------------------------------
    M,<key>,<value>                                      metadata
    E,<t_ms>,<text>                                      event
    D,<t_ms>,<trial>,<phase>,<mass>,<S|U|X>,<rpm>,<taps> raw poll sample
    P,<t_ms>,<trial>,<angle>,<rep>,<kind>,<mass>         settled point
    R,<trial>,<angle>,<rep>,<m_trig>,<t_disp_s>,<m_settled>,\
      <m_settled2>,<taps>,<verdict>                      per-trial summary
``phase``: noise, preroll, dispense, settle.  ``kind``: pretare, tare0,
settled, settled2.
"""

import time
import main_three_phase as m3

POWDER_ID = "salt"
# Plate degrees.  Steep tilts cleared by the 2026-07-31 no-actuator
# safety probe (0.0 mg spontaneous flow while parked at 25..72 deg).
ANGLES = (25.0, 40.0, 50.0, 60.0, 70.0)
REPS = 2
TRIGGER_G = 0.500                  # halt on the first reading >= this
FAST_RPM = 55.0                    # proven bulk speed (07-28..07-30)
TAP_EVERY = 3                      # one tap pulse every N poll loops
TAP_ON_MS = 60
NOISE_S = 60.0                     # one-time static baseline
PREROLL_S = 2.0
SETTLE_STREAM_S = 15.0
CONFIRM_WAIT_S = 5.0
DOSE_TIMEOUT_S = 90.0              # per-trial hard stop
NOFLOW_ABORT_S = 25.0              # nothing landing while spinning
MAX_CUP_G = 40.0                   # abort if absolute cup mass exceeds

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
        self.taps = 0
        self.rpm = 0.0
        sign = 1 if m3.config.STEPPER_DIRECTION >= 0 else -1
        self._vel = sign * max(
            1, int(FAST_RPM / 60.0 * self.stepper.steps_per_rev * 10000))

    # -- actuation -----------------------------------------------------
    def auger_run(self):
        self.stepper.tic.set_target_velocity(self._vel)
        self.rpm = FAST_RPM

    def halt_all(self):
        """Stop EVERYTHING, as fast as the drivers allow."""
        self.stepper.tic.set_target_velocity(0)
        self.tap._off()
        self.rpm = 0.0

    # -- measurement ---------------------------------------------------
    def sample(self, phase):
        r = self.scale.read()
        ts = t_ms()
        if r is None or r.grams is None:
            print("D,{},{},{},nan,X,{:.0f},{}".format(
                ts, self.trial, phase, self.rpm, self.taps))
            return None, False
        print("D,{},{},{},{:.4f},{},{:.0f},{}".format(
            ts, self.trial, phase, r.grams, "S" if r.stable else "U",
            self.rpm, self.taps))
        return r.grams, r.stable

    def stream(self, seconds, phase, dt_ms=60):
        end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            self.sample(phase)
            time.sleep_ms(dt_ms)

    def settled(self, kind, timeout_ms=8000):
        r = self.scale.read_stable(timeout_ms=timeout_ms)
        if r is None or r.grams is None:
            ev("no stable frame for {}".format(kind))
            r = self.scale.read()
        g = None if (r is None or r.grams is None) else r.grams
        print("P,{},{},{:.1f},{},{},{}".format(
            t_ms(), self.trial, self.angle, self.rep, kind,
            "nan" if g is None else "{:.4f}".format(g)))
        return g

    # -- one trial -----------------------------------------------------
    def trial_run(self, angle, rep):
        self.trial += 1
        self.angle = angle
        self.rep = rep
        ev("=== trial {} : angle {:.1f} plate deg, rep {} ===".format(
            self.trial, angle, rep))
        self.servo.move_to(angle)
        time.sleep_ms(1200)

        pre = self.settled("pretare")
        if pre is not None and pre > MAX_CUP_G:
            ev("cup at {:.2f} g > {:.1f} g limit -- stopping".format(
                pre, MAX_CUP_G))
            raise KeyboardInterrupt
        self.scale.zero()
        self.settled("tare0")
        self.stream(PREROLL_S, "preroll")

        # ---- rapid dispense ----
        taps_start = self.taps
        self.stepper.set_speed(FAST_RPM)
        self.stepper.enable(True)
        self.auger_run()
        t_start = time.ticks_ms()
        ev("dispense start: {:.0f} rpm, tap every {} polls".format(
            FAST_RPM, TAP_EVERY))
        m_trig = None
        verdict = "timeout"
        loop_i = 0
        last_gain_m = 0.0
        last_gain_t = t_start
        while True:
            el = time.ticks_diff(time.ticks_ms(), t_start) / 1000.0
            if el > DOSE_TIMEOUT_S:
                ev("dispense timeout at {:.0f} s".format(el))
                break
            m, _ = self.sample("dispense")
            self.stepper.keep_alive()
            if m is not None and m >= TRIGGER_G:
                self.halt_all()          # same loop iteration as trigger
                m_trig = m
                verdict = "ok"
                ev("TRIGGER {:.4f} g at t={:.2f} s -- ALL STOP".format(
                    m, el))
                break
            if m is not None:
                if m - last_gain_m > 0.0005:
                    last_gain_m = m
                    last_gain_t = time.ticks_ms()
                elif time.ticks_diff(
                        time.ticks_ms(), last_gain_t) / 1000.0 \
                        > NOFLOW_ABORT_S:
                    ev("no flow for {:.0f} s -- abort trial".format(
                        NOFLOW_ABORT_S))
                    verdict = "stalled"
                    break
            loop_i += 1
            if loop_i % TAP_EVERY == 0:
                self.tap.tap(1, on_ms=TAP_ON_MS, off_ms=0)
                self.taps += 1
        self.halt_all()
        self.stepper.stop()
        t_disp = time.ticks_diff(time.ticks_ms(), t_start) / 1000.0

        # ---- settle at the trial tilt (nothing moving) ----
        self.stream(SETTLE_STREAM_S, "settle")
        m_set = self.settled("settled")
        self.stream(CONFIRM_WAIT_S, "settle")
        m_set2 = self.settled("settled2")

        print("R,{},{:.1f},{},{},{:.2f},{},{},{},{}".format(
            self.trial, angle, rep,
            "nan" if m_trig is None else "{:.4f}".format(m_trig),
            t_disp,
            "nan" if m_set is None else "{:.4f}".format(m_set),
            "nan" if m_set2 is None else "{:.4f}".format(m_set2),
            self.taps - taps_start, verdict))


def main():
    meta("experiment", "rapid-dispense-stop-response")
    meta("powder_id", POWDER_ID)
    meta("trigger_g", TRIGGER_G)
    meta("fast_rpm", FAST_RPM)
    meta("tap_every_polls", TAP_EVERY)
    meta("tap_on_ms", TAP_ON_MS)
    meta("angles_plate_deg", "|".join("{:.1f}".format(a) for a in ANGLES))
    meta("reps", REPS)
    meta("noise_baseline_s", NOISE_S)
    meta("settle_stream_s", SETTLE_STREAM_S)

    rig = Rig()
    try:
        # ---- one-time static noise baseline ----
        rig.servo.move_to(0.0)
        time.sleep_ms(1200)
        ev("noise baseline: tare, then {:.0f} s static raw stream".format(
            NOISE_S))
        rig.settled("pretare")
        rig.scale.zero()
        rig.settled("tare0")
        rig.stream(NOISE_S, "noise")
        for _ in range(5):
            rig.settled("settled")
            time.sleep_ms(400)
        ev("noise baseline done")

        for rep in range(1, REPS + 1):
            order = ANGLES if rep % 2 else tuple(reversed(ANGLES))
            for angle in order:
                rig.trial_run(angle, rep)
        ev("all trials complete")
    except KeyboardInterrupt:
        ev("KeyboardInterrupt -- stopping")
    finally:
        try:
            rig.halt_all()
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
    print("SUMMARY,trials={},taps_total={}".format(rig.trial, rig.taps))


main()

"""Afterflow characterization battery -- PR #131 request (tests C6-C8 + B4).

Runs ON the Pico via ``mpremote run`` (RAM only -- nothing is written to
the Pico's filesystem).  Re-uses ``main_three_phase``'s hardware driver
classes (Stepper velocity mode / Servo plate degrees / Tap / Scale); no
dose-controller logic.  Extends ``stop_response.py`` (2026-08-07).

Goal
----
Quantify **afterflow**: the powder that lands *after* all actuation is
halted the instant the scale first reads a target mass.  The 08-07 pilot
found afterflow ~= flow-at-halt x tau, tau ~= 1.07 s, with n=2/angle and
a fixed 0.5 g trigger.  This battery upgrades the protocol per the
Edison critique and the PR #124 outline:

  C6  Randomized-order factorial stop-response: tilt {40,55,70} x halt
      mass {0.30,0.60,(1.00)} g, >=4 reps, tap-while-rotating.  Tests
      whether tau depends on tilt and on halt mass (trajectory point).
  C7  Afterflow linearity vs auger speed: fixed 55 deg, halt 0.5 g,
      auger-only, rpm {15,30,55,75}.  Tests afterflow = flow x tau
      (linear through zero) vs afterflow = a + flow x tau.
  C8  Actuator decomposition at 55 deg / 0.5 g: auger-only vs
      tap-while-rotating (isolates the tap contribution to afterflow),
      plus a tap-only static-bed probe (prime the lip, stop the auger,
      fire single taps -- bounds tap-alone yield & afterflow).
  B4  Max-rate feed map (only if budget remains): continuous, no stop,
      6 s at tilt {40,55,70}, rpm 55 -> flow(tilt) from the slope.

SAFETY -- 50 g cup cap (operator away, smaller cup)
--------------------------------------------------
A software running sum of dispensed mass is kept across the whole
session (``self.cum``).  Enforced two ways, on the Pico, in the loop:
  * before every trial, if ``cum + expected_trial > CAP_G`` the battery
    stops gracefully;
  * mid-dispense, if ``cum + this_trial_mass >= HARD_G`` every actuator
    halts immediately and the trial aborts.
Plus the per-trial no-flow and timeout watchdogs from stop_response, so
a disconnected scale can never cause a runaway.  CAP_G/HARD_G are set
well under 50 g so the physical cup can never overflow.

Telemetry (CSV over USB stdout)
-------------------------------
    M,<key>,<value>
    E,<t_ms>,<text>
    D,<t_ms>,<trial>,<phase>,<mass>,<S|U|X>,<rpm>,<taps>
    P,<t_ms>,<trial>,<tilt>,<rep>,<kind>,<mass>
    R,<trial>,<test>,<tilt>,<rep>,<rpm>,<halt_g>,<mode>,<m_trig>,
      <t_disp_s>,<m_settled>,<m_settled2>,<dispensed>,<cum>,<taps>,<verdict>
``phase``: noise, preroll, dispense, settle, prime, taptail.
``mode``: rot, auger, cont, taponly.
"""

import time
import main_three_phase as m3

POWDER_ID = "salt"

# ---- safety budget (grams dispensed into the cup this session) ----
CAP_G = 46.0        # stop the battery before starting a trial past this
HARD_G = 48.0       # emergency halt mid-dispense if reached (< 50 g cup)

# ---- timing ----
NOISE_S = 20.0
PREROLL_S = 1.5
SETTLE_STREAM_S = 8.0
CONFIRM_WAIT_S = 3.0
DOSE_TIMEOUT_S = 90.0
NOFLOW_ABORT_S = 12.0
POLL_MS = 60

# ---- dispense ----
FAST_RPM = 55.0
TAP_EVERY = 3          # tap-while-rotating: one pulse every N poll loops
TAP_ON_MS = 60
CONT_S = 6.0           # B4 continuous run duration
PRIME_REVS = 3.0       # C8 tap-only: revolutions to prime the lip
TAPONLY_N = 15         # C8 tap-only: single taps after priming

_t0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _t0)


def ev(msg):
    print("E,{},{}".format(t_ms(), msg))


def meta(k, v):
    print("M,{},{}".format(k, v))


def _vel_for(stepper, rpm):
    sign = 1 if m3.config.STEPPER_DIRECTION >= 0 else -1
    return sign * max(1, int(rpm / 60.0 * stepper.steps_per_rev * 10000))


class Rig:
    def __init__(self):
        self.scale = m3.Scale()
        self.stepper = m3.Stepper()
        self.servo = m3.Servo()
        self.tap = m3.Tap()
        self.trial = 0
        self.tilt = 0.0
        self.rep = 0
        self.taps = 0
        self.rpm = 0.0
        self.cum = 0.0        # running sum of dispensed mass (g)
        self.stopped = False  # set when the cap forces an early stop

    # -- actuation -----------------------------------------------------
    def auger_run(self, rpm):
        self.stepper.set_speed(rpm)
        self.stepper.enable(True)
        self.stepper.tic.set_target_velocity(_vel_for(self.stepper, rpm))
        self.rpm = rpm

    def halt_all(self):
        try:
            self.stepper.tic.set_target_velocity(0)
        except Exception:
            pass
        try:
            self.tap._off()
        except Exception:
            pass
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

    def stream(self, seconds, phase, dt_ms=POLL_MS):
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
            t_ms(), self.trial, self.tilt, self.rep, kind,
            "nan" if g is None else "{:.4f}".format(g)))
        return g

    # -- one stop-response / continuous trial --------------------------
    def trial_run(self, test, tilt, rep, rpm, halt_g, mode):
        # budget gate before starting
        expect = (CONT_S * 0.20) if mode == "cont" else (halt_g + 0.30)
        if self.cum + expect > CAP_G:
            ev("BUDGET: cum {:.2f} g + expected {:.2f} g > cap {:.1f} g "
               "-- stopping battery".format(self.cum, expect, CAP_G))
            self.stopped = True
            return

        self.trial += 1
        self.tilt = tilt
        self.rep = rep
        ev("=== trial {} : {} tilt {:.1f} rep {} rpm {:.0f} halt {:.2f} "
           "mode {} (cum {:.2f} g) ===".format(
               self.trial, test, tilt, rep, rpm, halt_g, mode, self.cum))
        self.servo.move_to(tilt)
        time.sleep_ms(1200)

        self.scale.zero()
        self.settled("tare0")
        self.stream(PREROLL_S, "preroll")

        if mode == "taponly":
            self._taponly(test, tilt, rep, rpm, halt_g)
            return

        taps_start = self.taps
        t_start = time.ticks_ms()
        self.auger_run(rpm)
        ev("dispense start: mode {} rpm {:.0f}".format(mode, rpm))
        m_trig = None
        verdict = "timeout"
        loop_i = 0
        last_gain_m = 0.0
        last_gain_t = t_start
        abort = False
        while True:
            el = time.ticks_diff(time.ticks_ms(), t_start) / 1000.0
            m, _ = self.sample("dispense")
            self.stepper.keep_alive()

            # emergency cup-cap guard (m ~= this-trial mass after tare)
            if m is not None and self.cum + m >= HARD_G:
                self.halt_all()
                ev("HARD CAP: cum {:.2f} + trial {:.2f} >= {:.1f} g -- "
                   "EMERGENCY HALT".format(self.cum, m, HARD_G))
                m_trig = m
                verdict = "capstop"
                abort = True
                break

            if mode == "cont":
                if el > CONT_S:
                    self.halt_all()
                    m_trig = m
                    verdict = "cont_done"
                    ev("continuous {:.1f} s done".format(el))
                    break
            else:
                if m is not None and m >= halt_g:
                    self.halt_all()          # same loop iteration
                    m_trig = m
                    verdict = "ok"
                    ev("TRIGGER {:.4f} g at t={:.2f} s -- ALL STOP".format(
                        m, el))
                    break

            if el > DOSE_TIMEOUT_S:
                self.halt_all()
                ev("dispense timeout at {:.0f} s".format(el))
                verdict = "timeout"
                break

            if m is not None:
                if m - last_gain_m > 0.0005:
                    last_gain_m = m
                    last_gain_t = time.ticks_ms()
                elif time.ticks_diff(time.ticks_ms(),
                                     last_gain_t) / 1000.0 > NOFLOW_ABORT_S:
                    self.halt_all()
                    ev("no flow for {:.0f} s -- abort".format(NOFLOW_ABORT_S))
                    verdict = "stalled"
                    break

            loop_i += 1
            if mode == "rot" and loop_i % TAP_EVERY == 0:
                self.tap.tap(1, on_ms=TAP_ON_MS, off_ms=0)
                self.taps += 1

        self.halt_all()
        try:
            self.stepper.stop()
        except Exception:
            pass
        t_disp = time.ticks_diff(time.ticks_ms(), t_start) / 1000.0

        self.stream(SETTLE_STREAM_S, "settle")
        m_set = self.settled("settled")
        self.stream(CONFIRM_WAIT_S, "settle")
        m_set2 = self.settled("settled2")

        disp = 0.0 if m_set is None else max(0.0, m_set)
        self.cum += disp
        print("R,{},{},{:.1f},{},{:.0f},{:.2f},{},{},{:.2f},{},{},"
              "{:.4f},{:.4f},{},{}".format(
                  self.trial, test, tilt, rep, rpm, halt_g, mode,
                  "nan" if m_trig is None else "{:.4f}".format(m_trig),
                  t_disp,
                  "nan" if m_set is None else "{:.4f}".format(m_set),
                  "nan" if m_set2 is None else "{:.4f}".format(m_set2),
                  disp, self.cum, self.taps - taps_start, verdict))
        if abort:
            self.stopped = True

    # -- C8 tap-only static-bed probe ----------------------------------
    def _taponly(self, test, tilt, rep, rpm, halt_g):
        taps_start = self.taps
        # prime the lip: run the auger a fixed number of revolutions
        prime_s = PRIME_REVS / (30.0 / 60.0)   # revs at 30 rpm
        t_start = time.ticks_ms()
        self.auger_run(30.0)
        ev("prime: {:.1f} rev @ 30 rpm".format(PRIME_REVS))
        while time.ticks_diff(time.ticks_ms(), t_start) / 1000.0 < prime_s:
            m, _ = self.sample("prime")
            self.stepper.keep_alive()
            if m is not None and self.cum + m >= HARD_G:
                self.halt_all()
                ev("HARD CAP during prime -- halt")
                self.stopped = True
                break
        self.halt_all()
        try:
            self.stepper.stop()
        except Exception:
            pass
        self.stream(2.0, "settle")
        m_primed = self.settled("primed")

        # single taps, one at a time, auger static
        for i in range(TAPONLY_N):
            self.tap.tap(1, on_ms=TAP_ON_MS, off_ms=0)
            self.taps += 1
            self.stream(1.0, "taptail")
            self.settled("tap{}".format(i + 1))
        m_set = self.settled("settled")
        self.stream(CONFIRM_WAIT_S, "settle")
        m_set2 = self.settled("settled2")

        disp = 0.0 if m_set is None else max(0.0, m_set)
        self.cum += disp
        t_disp = time.ticks_diff(time.ticks_ms(), t_start) / 1000.0
        print("R,{},{},{:.1f},{},{:.0f},{:.2f},taponly,{},{:.2f},{},{},"
              "{:.4f},{:.4f},{},taponly".format(
                  self.trial, test, tilt, rep, 30.0, halt_g,
                  "nan" if m_primed is None else "{:.4f}".format(m_primed),
                  t_disp,
                  "nan" if m_set is None else "{:.4f}".format(m_set),
                  "nan" if m_set2 is None else "{:.4f}".format(m_set2),
                  disp, self.cum, self.taps - taps_start))


def build_plan():
    """Deterministic, order-interleaved trial plan (test,tilt,rep,rpm,
    halt_g,mode).  Tilt/mass order alternates per rep so hopper drawdown
    does not alias onto a factor (true-RNG is avoided for reproducibility
    and MicroPython portability)."""
    plan = []

    # ---- C6: factorial stop-response, tap-while-rotating ----
    tilts = [40.0, 55.0, 70.0]
    masses = [0.30, 0.60]
    for rep in range(1, 5):                      # 4 reps
        torder = tilts if rep % 2 else list(reversed(tilts))
        for ti, tilt in enumerate(torder):
            morder = masses if (rep + ti) % 2 else list(reversed(masses))
            for hm in morder:
                plan.append(("C6", tilt, rep, FAST_RPM, hm, "rot"))
    for tilt in tilts:                           # halt-mass dependence
        plan.append(("C6", tilt, 5, FAST_RPM, 1.00, "rot"))

    # ---- C7: afterflow vs auger speed, fixed 55 deg, auger-only ----
    rpms = [15.0, 30.0, 55.0, 75.0]
    for rep in range(1, 4):                      # 3 reps
        rorder = rpms if rep % 2 else list(reversed(rpms))
        for rpm in rorder:
            plan.append(("C7", 55.0, rep, rpm, 0.50, "auger"))

    # ---- C8: actuator decomposition, fixed 55 deg / 0.5 g ----
    for rep in range(1, 5):                      # 4 reps each mode
        order = ["auger", "rot"] if rep % 2 else ["rot", "auger"]
        for mode in order:
            plan.append(("C8", 55.0, rep, FAST_RPM, 0.50, mode))
    for rep in range(1, 3):                       # 2 tap-only probes
        plan.append(("C8", 55.0, rep, 30.0, 0.0, "taponly"))

    # ---- B4: max-rate feed map (budget permitting) ----
    for rep in range(1, 3):                      # 2 reps
        torder = tilts if rep % 2 else list(reversed(tilts))
        for tilt in torder:
            plan.append(("B4", tilt, rep, FAST_RPM, 0.0, "cont"))

    return plan


def main():
    meta("experiment", "afterflow-battery-C6-C8-B4")
    meta("powder_id", POWDER_ID)
    meta("cap_g", CAP_G)
    meta("hard_g", HARD_G)
    meta("fast_rpm", FAST_RPM)
    meta("tap_every_polls", TAP_EVERY)
    meta("tap_on_ms", TAP_ON_MS)
    meta("cont_s", CONT_S)
    meta("prime_revs", PRIME_REVS)
    meta("taponly_n", TAPONLY_N)
    meta("settle_stream_s", SETTLE_STREAM_S)
    meta("auger_tare_g", 56.716)
    meta("total_loaded_g", 127.98)

    rig = Rig()
    plan = build_plan()
    meta("planned_trials", len(plan))
    try:
        # one-time static noise baseline
        rig.servo.move_to(0.0)
        time.sleep_ms(1200)
        ev("noise baseline: tare, {:.0f} s static raw stream".format(NOISE_S))
        rig.scale.zero()
        rig.settled("tare0")
        rig.stream(NOISE_S, "noise")
        for _ in range(5):
            rig.settled("settled")
            time.sleep_ms(300)
        ev("noise baseline done")

        for (test, tilt, rep, rpm, halt_g, mode) in plan:
            rig.trial_run(test, tilt, rep, rpm, halt_g, mode)
            if rig.stopped:
                ev("battery stopped early (budget/cap)")
                break
        ev("battery complete")
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
    print("SUMMARY,trials={},taps_total={},cum_g={:.3f}".format(
        rig.trial, rig.taps, rig.cum))


main()

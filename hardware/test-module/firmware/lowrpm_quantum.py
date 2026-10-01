"""Low-RPM stop battery + quantum-vs-tilt at trim speed -- PR #131 (2026-08-17).

Runs ON the Pico via ``mpremote run`` (RAM only -- nothing is written to
the Pico filesystem).  Re-uses ``main_three_phase``'s hardware driver
classes (Stepper / Servo / Scale); no dose-controller logic.

Why this exists
---------------
Follow-up to the PR #124 low-RPM analysis, which asked for exactly two
measurements before the trim stage can be designed:

  D  "Low-RPM stop battery at matched fill -- 5 / 10 / 15 / 25 rpm, >=5
     reps, fill weighed between blocks.  Tests whether AF0 really is flat
     below 15 rpm (the current intercept is extrapolated from a 15-75 rpm
     fit, and the C7 reps are order-confounded with drawdown).  If AF0
     turns out to scale with tilt/lip charge rather than being a
     constant, stage 2's safety margin gets much smaller."

  Q  "Quantum vs tilt at trim speed -- 20 deg increments weighed at rest,
     at 3 tilts.  Gives mg/deg and its scatter at the trim operating
     point, which is what sizes the increments.  This is Test A repeated
     where trim actually lives."

Design decisions that matter for interpreting the data
------------------------------------------------------
* MATCHED FILL.  The loaded tube (tube + salt) exceeds the balance's
  102 g range, so "weigh the fill between blocks" is not possible
  remotely.  Two substitutes are used instead, and they are stronger
  than a between-block weighing for the specific confound at issue:
    1. Every stop trial cruises the SAME number of auger revolutions
       (CRUISE_REVS), so every rpm level consumes the same mass per
       trial -- the drawdown per level is identical by construction.
    2. rpm order is rotated + alternately reversed within each rep block
       (``build_plan_D``), so each rpm level sees the same mean position
       in the drawdown sequence.  This is precisely what the C7 sweep
       lacked (its reps were order-confounded).
    3. A matched-revolution FLOW CHECK (1 rev at a fixed reference
       tilt/rpm, weighed at rest) is run before every block, giving a
       per-block fill/stationarity index; blocks can be detrended or
       rejected against it after the fact.

* PHASE-LOCKED HALT.  Every stop trial decelerates to the SAME commanded
  auger phase (HALT_PHASE_DEG), using position mode, so the 08-13 finding
  that the halt phase may matter cannot alias onto rpm.  The 44:20
  motor->auger reduction is folded into ``Stepper.steps_per_rev`` = 3520
  microsteps per AUGER revolution, so phase is exact to <0.11 deg.

* AUGER-ONLY.  No taps anywhere in this battery (matches C7, and taps are
  a separate actuator with their own lip-charge state).

* NO HARDWARE TARE.  The A&D ``Z`` command silently stops answering ``Q``
  polls while the pan is loaded and the cup cannot be emptied remotely, so
  masses are tracked ABSOLUTE from a single baseline and every yield /
  afterflow is a DIFFERENCE (the standing offset cancels).  Absolute mass
  is also the cup-capacity guard.

* WEIGHED AT REST.  The stepper is de-energised and given QUIET_MS of
  silence before every weigh, so the Tic driver cannot inject noise into
  the scale UART.  De-energising does not disturb the shadow ``_position``,
  so the session-wide phase reference survives.

Tests
-----
  D  Low-rpm stop battery.  For each rep block: flow check, then one stop
     trial per rpm in {5,10,15,25} -- cruise CRUISE_REVS revolutions at
     that rpm, decelerate to the fixed halt phase, de-energise, and weigh
     the settling tail.  afterflow = settled - m_halt; flow-at-halt is
     fitted offline from the streamed cruise samples.  TILT_D deg.

  Q  Quantum vs tilt at trim speed.  At each tilt in TILTS_Q, advance the
     auger in INCR_DEG steps for exactly one revolution per scan, weighing
     (at rest, stepper de-energised) after every increment.  Tilt order is
     reversed on the second scan so drawdown does not alias onto tilt.

  D2 Bonus tilt arm (runs last, only if budget allows).  The same stop
     battery at TILT_D2, 2 reps -- tests whether AF0 scales with tilt /
     lip charge rather than being a constant.  Placed last so truncation
     cannot harm the two requested tests; its internal rpm comparison is
     self-contained and unaffected by the drawdown that precedes it.

Telemetry (CSV over USB stdout)
-------------------------------
    M,<key>,<value>
    E,<t_ms>,<text>
    D,<t_ms>,<trial>,<phase>,<mass>,<S|U|X>,<rpm>,<auger_rev>,<phase_deg>
    P,<t_ms>,<trial>,<kind>,<mass>,<stab>,<auger_rev>,<phase_deg>
    F,<block>,<label>,<tilt>,<rpm>,<revs>,<m_before>,<m_after>,<yield>
    S,<trial>,<test>,<block>,<tilt>,<rep>,<rpm>,<cruise_revs>,<phase_cmd>,
      <auger_rev_total>,<m_base>,<m_halt>,<t_move_s>,<m_settled>,
      <afterflow>,<dispensed>,<abs_mass>,<verdict>
    Q,<trial>,<scan>,<incr>,<tilt>,<rpm>,<incr_deg>,<cum_deg>,<phase_deg>,
      <auger_rev>,<m_before>,<m_after>,<yield>,<stab>
``D.phase``: noise, preroll, move, settle, scanmove, flowmove.
"""

import time
import main_three_phase as m3

POWDER_ID = "salt"

# ---- safety budget (absolute cup mass, g -- cup empty at session start) ----
CAP_G = 32.0        # refuse to start a new trial above this
HARD_G = 38.0       # emergency mid-move halt

# ---- timing ----
NOISE_S = 15.0
PREROLL_S = 1.0
SETTLE_STREAM_S = 8.0     # streamed settling tail after a stop
SETTLED_MAX_S = 4.0       # robust settled() poll budget
QUIET_MS = 400            # silence after de-energising, before weighing
POLL_MS = 120             # ~8 Hz, matched to the balance datum rate

# ---- Test D: low-rpm stop battery ----
TILT_D = 55.0
RPMS_D = [5.0, 10.0, 15.0, 25.0]
REPS_D = 5
CRUISE_REVS = 3           # identical mass per trial at every rpm
HALT_PHASE_DEG = 0.0      # phase-locked halt

# ---- Test Q: quantum vs tilt at trim speed ----
RPM_Q = 10.0              # trim speed
INCR_DEG = 20.0
TILTS_Q = [15.0, 35.0, 55.0]
N_SCANS_Q = 2             # 18 increments = exactly 1 auger rev per scan

# ---- flow check (matched-revolution fill/stationarity index) ----
FLOW_TILT = 55.0
FLOW_RPM = 30.0
FLOW_REVS = 1

# ---- Test D2: bonus tilt arm (runs last) ----
TILT_D2 = 25.0
REPS_D2 = 2

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
        self.spr = int(round(self.stepper.steps_per_rev))   # 3520
        self.trial = 0
        self.rpm = 0.0
        self.absmass = 0.0
        self.aborted = False
        self.noflow = 0

    # -- phase helpers -------------------------------------------------
    def auger_rev(self):
        return self.stepper._position / self.spr

    def phase_deg(self):
        return (self.stepper._position % self.spr) / self.spr * 360.0

    def _delta_to_phase(self, revs, phase_deg):
        cur = self.stepper._position % self.spr
        want = int(round(phase_deg / 360.0 * self.spr)) % self.spr
        extra = (want - cur) % self.spr
        return revs * self.spr + extra

    # -- measurement ---------------------------------------------------
    def sample(self, phase):
        r = self.scale.read()
        ts = t_ms()
        arev = self.auger_rev()
        aph = self.phase_deg()
        if r is None or r.grams is None:
            print("D,{},{},{},nan,X,{:.0f},{:.4f},{:.2f}".format(
                ts, self.trial, phase, self.rpm, arev, aph))
            return None
        print("D,{},{},{},{:.4f},{},{:.0f},{:.4f},{:.2f}".format(
            ts, self.trial, phase, r.grams, "S" if r.stable else "U",
            self.rpm, arev, aph))
        return r.grams

    def stream(self, seconds, phase):
        end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
        last = None
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            m = self.sample(phase)
            if m is not None:
                last = m
                self.absmass = m
            time.sleep_ms(POLL_MS)
        return last

    def settled(self, kind, max_s=SETTLED_MAX_S):
        """Poll read() up to max_s; return (grams, stable).  Returns a stable
        ST datum if one arrives, else the last valid (unstable) datum."""
        end = time.ticks_add(time.ticks_ms(), int(max_s * 1000))
        last = None
        laststab = False
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            r = self.scale.read()
            if r is not None and r.grams is not None:
                last = r.grams
                laststab = r.stable
                if r.stable:
                    break
            time.sleep_ms(80)
        if last is not None:
            self.absmass = last
        print("P,{},{},{},{},{},{:.4f},{:.2f}".format(
            t_ms(), self.trial, kind,
            "nan" if last is None else "{:.4f}".format(last),
            "S" if laststab else "U", self.auger_rev(), self.phase_deg()))
        return last, laststab

    def rest_weigh(self, kind):
        """De-energise, wait out the driver noise, then weigh at rest."""
        self.stepper.enable(False)
        self.rpm = 0.0
        time.sleep_ms(QUIET_MS)
        return self.settled(kind)

    # -- position-mode move, streaming the balance throughout ----------
    def move_usteps(self, delta_u, rpm, phase_label):
        self.stepper.set_speed(rpm)
        if not self.stepper._enabled:
            self.stepper.enable(True)
        self.rpm = rpm
        self.stepper._position += delta_u
        self.stepper.tic.set_target_position(self.stepper._position)

        a = m3.config.STEPPER_ACCEL_REV_PER_S2 * self.spr
        vmax = abs(rpm) / 60.0 * self.spr
        dd = abs(delta_u)
        if a <= 0 or vmax <= 0:
            t_move = 0.5
        else:
            d_acc = vmax * vmax / (2.0 * a)
            if 2.0 * d_acc <= dd:
                t_move = 2.0 * (vmax / a) + (dd - 2.0 * d_acc) / vmax
            else:
                t_move = 2.0 * (dd / a) ** 0.5
        t_move += 0.35        # landing margin: the Tic must reach target

        t_start = time.ticks_ms()
        m_last = None
        while time.ticks_diff(time.ticks_ms(), t_start) / 1000.0 < t_move:
            m = self.sample(phase_label)
            if m is not None:
                m_last = m
                self.absmass = m
                if m >= HARD_G:
                    self.stepper.enable(False)
                    ev("HARD CAP mid-move: abs {:.2f} >= {:.1f}".format(
                        m, HARD_G))
                    self.aborted = True
                    break
            self.stepper.keep_alive()
            time.sleep_ms(POLL_MS)
        self.rpm = 0.0
        return m_last, t_move

    # -- matched-revolution flow check (fill / stationarity index) -----
    def flow_check(self, block, label):
        self.trial += 1
        ev("--- flow check {} (block {}): {:.0f} rev @ {:.0f} rpm, tilt "
           "{:.0f} ---".format(label, block, FLOW_REVS, FLOW_RPM, FLOW_TILT))
        self.servo.move_to(FLOW_TILT)
        time.sleep_ms(900)
        m0, _ = self.rest_weigh("flow_before")
        if m0 is None:
            m0 = self.absmass
        self.move_usteps(FLOW_REVS * self.spr, FLOW_RPM, "flowmove")
        m1, _ = self.rest_weigh("flow_after")
        if m1 is None:
            m1 = self.absmass
        yld = m1 - m0
        print("F,{},{},{:.0f},{:.0f},{},{:.4f},{:.4f},{:.4f}".format(
            block, label, FLOW_TILT, FLOW_RPM, FLOW_REVS, m0, m1, yld))
        if yld < 0.005:
            self.noflow += 1
            ev("flow check LOW: {:.4f} g/rev (consecutive low = {})".format(
                yld, self.noflow))
            if self.noflow >= 2:
                ev("ABORT: two consecutive low flow checks -- hopper empty "
                   "or bridged")
                self.aborted = True
        else:
            self.noflow = 0
        return yld

    # -- Test D / D2: low-rpm stop trial -------------------------------
    def stop_trial(self, test, block, tilt, rep, rpm):
        if self.absmass > CAP_G:
            ev("BUDGET: abs {:.2f} > cap {:.1f} -- stop".format(
                self.absmass, CAP_G))
            self.aborted = True
            return
        self.trial += 1
        ev("=== {} trial {} : tilt {:.0f} rep {} rpm {:.0f} cruise {} rev "
           "-> halt phase {:.0f} (abs {:.2f}) ===".format(
               test, self.trial, tilt, rep, rpm, CRUISE_REVS,
               HALT_PHASE_DEG, self.absmass))
        self.servo.move_to(tilt)
        time.sleep_ms(900)
        m_base, _ = self.rest_weigh("base")
        if m_base is None:
            m_base = self.absmass
        self.stream(PREROLL_S, "preroll")

        delta_u = self._delta_to_phase(CRUISE_REVS, HALT_PHASE_DEG)
        m_halt, t_move = self.move_usteps(delta_u, rpm, "move")
        self.stepper.enable(False)      # de-energise: quiet + hold phase
        if m_halt is None:
            m_halt = self.absmass
        self.stream(SETTLE_STREAM_S, "settle")
        m_set, _ = self.settled("settled")
        if m_set is None:
            m_set = self.absmass

        after = m_set - m_halt
        disp = m_set - m_base
        verdict = "capstop" if self.aborted else "ok"
        print("S,{},{},{},{:.0f},{},{:.0f},{},{:.1f},{:.4f},{:.4f},{:.4f},"
              "{:.2f},{:.4f},{:.4f},{:.4f},{:.4f},{}".format(
                  self.trial, test, block, tilt, rep, rpm, CRUISE_REVS,
                  HALT_PHASE_DEG, self.auger_rev(), m_base, m_halt, t_move,
                  m_set, after, disp, self.absmass, verdict))

    # -- Test Q: quantum vs tilt at trim speed -------------------------
    def quantum_scan(self, scan, tilt, n_incr):
        self.trial += 1
        ev("=== Q scan {} trial {} : tilt {:.0f} rpm {:.0f} incr {:.0f} deg "
           "x {} (abs {:.2f}) ===".format(
               scan, self.trial, tilt, RPM_Q, INCR_DEG, n_incr, self.absmass))
        self.servo.move_to(tilt)
        time.sleep_ms(900)
        m_prev, _ = self.rest_weigh("q0")
        if m_prev is None:
            m_prev = self.absmass
        incr_u = int(round(INCR_DEG / 360.0 * self.spr))
        for i in range(n_incr):
            self.move_usteps(incr_u, RPM_Q, "scanmove")
            m_now, stab = self.rest_weigh("q{}".format(i + 1))
            if m_now is None:
                m_now = m_prev
                stab = False
            print("Q,{},{},{},{:.0f},{:.0f},{:.0f},{:.1f},{:.2f},{:.4f},"
                  "{:.4f},{:.4f},{:.4f},{}".format(
                      self.trial, scan, i + 1, tilt, RPM_Q, INCR_DEG,
                      (i + 1) * INCR_DEG, self.phase_deg(), self.auger_rev(),
                      m_prev, m_now, m_now - m_prev, "S" if stab else "U"))
            m_prev = m_now
            if self.absmass >= CAP_G:
                ev("CAP during quantum scan: abs {:.2f} g".format(
                    self.absmass))
                self.aborted = True
                break


def build_plan_D(rpms, reps):
    """Rotate + alternately reverse the rpm order within each rep block, so
    every rpm level sees the same mean position in the drawdown sequence."""
    plan = []
    n = len(rpms)
    for rep in range(1, reps + 1):
        k = (rep - 1) % n
        order = rpms[k:] + rpms[:k]
        if rep % 2 == 0:
            order = list(reversed(order))
        for rpm in order:
            plan.append((rep, rpm))
    return plan


def build_plan_Q():
    """Tilt order reversed on the second scan so drawdown does not alias
    onto tilt."""
    plan = []
    for scan in range(1, N_SCANS_Q + 1):
        order = list(TILTS_Q) if scan % 2 == 1 else list(reversed(TILTS_Q))
        for tilt in order:
            plan.append((scan, tilt))
    return plan


def main():
    meta("experiment", "lowrpm-stop-battery-D-and-quantum-vs-tilt-Q")
    meta("powder_id", POWDER_ID)
    meta("gear_ratio_stepper_per_auger", "44/20=2.2")
    meta("steps_per_auger_rev", 3520)
    meta("full_steps_rev", m3.config.STEPPER_FULL_STEPS_REV)
    meta("microsteps", m3.config.STEPPER_MICROSTEPS)
    meta("stepper_direction", m3.config.STEPPER_DIRECTION)
    meta("accel_rev_per_s2", m3.config.STEPPER_ACCEL_REV_PER_S2)
    meta("cap_g", CAP_G)
    meta("hard_g", HARD_G)
    meta("tare_mode", "no-hardware-tare-absolute-differences")
    meta("auger_tare_g", 56.716)
    meta("tilt_D", TILT_D)
    meta("rpms_D", "|".join("{:.0f}".format(r) for r in RPMS_D))
    meta("reps_D", REPS_D)
    meta("cruise_revs_D", CRUISE_REVS)
    meta("halt_phase_deg", HALT_PHASE_DEG)
    meta("rpm_Q", RPM_Q)
    meta("incr_deg_Q", INCR_DEG)
    meta("tilts_Q", "|".join("{:.0f}".format(t) for t in TILTS_Q))
    meta("n_scans_Q", N_SCANS_Q)
    meta("flow_check", "{:.0f}rev@{:.0f}rpm@{:.0f}deg".format(
        FLOW_REVS, FLOW_RPM, FLOW_TILT))
    meta("tilt_D2", TILT_D2)
    meta("reps_D2", REPS_D2)

    rig = Rig()
    plan_d = build_plan_D(RPMS_D, REPS_D)
    plan_q = build_plan_Q()
    plan_d2 = build_plan_D(RPMS_D, REPS_D2)
    meta("planned_D_trials", len(plan_d))
    meta("planned_Q_scans", len(plan_q))
    meta("planned_D2_trials", len(plan_d2))

    n_incr_q = int(round(360.0 / INCR_DEG))
    meta("incr_per_scan_Q", n_incr_q)

    try:
        rig.servo.move_to(0.0)
        time.sleep_ms(1000)
        ev("baseline (no tare) + {:.0f} s static noise stream".format(NOISE_S))
        rig.settled("baseline0", max_s=4.0)
        rig.stream(NOISE_S, "noise")
        rig.settled("noise_end", max_s=4.0)
        ev("noise baseline done")

        # ---- Test D: low-rpm stop battery, blocked by rep ----
        last_rep = None
        for (rep, rpm) in plan_d:
            if rig.aborted:
                break
            if rep != last_rep:
                rig.flow_check(rep, "D_pre")
                last_rep = rep
                if rig.aborted:
                    break
            rig.stop_trial("D", rep, TILT_D, rep, rpm)
        if not rig.aborted:
            rig.flow_check(REPS_D + 1, "D_post")
        ev("Test D done (abs {:.2f} g)".format(rig.absmass))

        # ---- Test Q: quantum vs tilt at trim speed ----
        if not rig.aborted:
            for (scan, tilt) in plan_q:
                rig.quantum_scan(scan, tilt, n_incr_q)
                if rig.aborted:
                    break
            ev("Test Q done (abs {:.2f} g)".format(rig.absmass))

        # ---- Test D2: bonus tilt arm ----
        if not rig.aborted:
            rig.flow_check(90, "D2_pre")
            last_rep = None
            for (rep, rpm) in plan_d2:
                if rig.aborted:
                    break
                rig.stop_trial("D2", rep, TILT_D2, rep, rpm)
            ev("Test D2 done (abs {:.2f} g)".format(rig.absmass))

        ev("battery complete")
    except KeyboardInterrupt:
        ev("KeyboardInterrupt -- stopping")
    finally:
        try:
            rig.stepper.tic.set_target_velocity(0)
        except Exception:
            pass
        try:
            rig.stepper.stop()
        except Exception:
            pass
        try:
            rig.servo.move_to(0.0)
        except Exception:
            pass
    print("SUMMARY,trials={},abs_g={:.3f}".format(rig.trial, rig.absmass))


main()

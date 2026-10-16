"""Rate-PI trickle-tap trim test -- PR #131 request (2026-09-08).

Runs ON the Pico via ``mpremote run`` (RAM only -- nothing is written to
the Pico filesystem).  Re-uses ``main_three_phase``'s hardware driver
classes (Stepper / Servo / Tap / Scale); no dose-controller logic from
there.

What this is
------------
The FIRST hardware run of a PI dose controller on this rig (the trim
bench plan on the #154 branch, ``docs/trim-bench-plan.md`` section B1 --
every earlier real dose came from the fixed-increment three-phase
scheme).  The controller is a line-for-line port of ``trickle_tap`` from
``optimization/benchmarks/bangbang.py`` @ dc99459 on the PR #124 branch:

    seeded rate-PI trickle          rpm = clip(kp*err + ki*int, 0, 45)
                                    err = r_sp - r_hat
                                    r_sp = clip((remaining - margin)
                                                / (2*tau), 0.003, 0.05)
    + adaptive margin               margin = 0.035 + 0.06*max(0, ff-0.30)
    + online feed factor            ff <- 0.9*ff + 0.1*(dispensed/revs)
    + predictive cutoff             m_hat + r_hat*tau + k*sigma
                                        >= target - margin
    + stall bail (8 s no gain)      -> fall through to the tap finish
    + tap finish                    single taps, settle, stable read;
                                    5 deg nudges when the lip runs dry
                                    (``controllers.tap_finish`` defaults,
                                    taps_per_cycle=1, tol +/-5 mg)

Only the PI version is exercised (no bang-bang bulk stages): every trial
starts from rest at the trim tilt, exactly the "small target goes
straight to the trickle" branch of ``BangBangTrim``.

Estimator: the same 3-state KF3 (true mass, rate, balance reading) this
branch already validated on hardware in ``kf_bangbang.py``, with the
MEASURED instrument constants rather than the twin's assumptions:
tau_bal = 0.16 s (2026-08-14 drop tests), R = 0.4/2.0 mg quiet/actuating,
Q_ACC_SD = 0.25 (calibrated by replaying the 2026-08-12 afterflow
battery).  The PI law, gains, margins and cutoff are untouched.

Trim settings, per the PR #131 request: trickle tilt 20 deg (the
function's own default -- vs 45-55 deg bulk), tap finish at 0 deg.
Powder: carboxymethyl cellulose (loaded 2026-09-08, issue #116; battery
data says 2.6 mg/rev @ 0 deg, 26 mg/rev @ 45 deg, taps ~0.01-0.15 mg --
cohesive, so the feed probe below bumps the tilt in 5 deg steps up to
30 deg if 20 deg turns out not to convey at all, and logs what it did).

Fume-hood drift (issues #116 / #157): the new hood drifts a smooth
-4.5..+2.6 mg/min.  No hardware tare is attempted (the A&D silently
refuses ``Z`` under load); every trial works in differences from its own
settled baseline, and a quiet drift window is logged before each trial
(plus a 90 s survey at session start / 60 s at end) so the analysis can
report raw AND drift-corrected errors.

Instrumentation, per bench-plan B1: every control cycle logs the KF
internals (m_hat, r_hat, b_hat, sigma) and the PI terms (r_sp, integ,
ff, margin, commanded rpm); the halt line decomposes the cutoff budget
into its m_hat / r_hat*tau / k*sigma / margin parts.

Telemetry (CSV over USB stdout)
-------------------------------
    M,<key>,<value>
    E,<t_ms>,<text>
    D,<t_ms>,<trial>,<phase>,<mass>,<S|U|X>,<fresh>,<rpm>,<m_hat>,
      <r_hat>,<b_hat>,<sigma>,<pred>,<r_sp>,<integ>,<ff>,<margin>
    P,<t_ms>,<trial>,<kind>,<mass>,<S|U>
    C,<t_ms>,<trial>,<cycle>,<taps>,<nudges>,<m_before>,<m_after>
    H,<t_ms>,<trial>,<m_hat>,<r_tau>,<k_sigma>,<margin>,<target>,<why>
    T,<trial>,<target_g>,<tilt>,<tap_tilt>,<rep>,<m_base>,<t_trickle_s>,
      <revs>,<ff_end>,<m_posttrickle>,<taps>,<nudges>,<tap_cycles>,
      <t_total_s>,<m_settled>,<m_settled2>,<dispensed_g>,<error_mg>,
      <trickle_short_mg>,<verdict>
"""

import math
import time

try:
    import main_three_phase as m3
except ImportError:      # off-device import (analysis pulls constants)
    m3 = None

POWDER_ID = "carboxymethyl-cellulose"

# ---- trickle_tap parameters (bangbang.py @ dc99459, verbatim) -------
DT_S = 0.2             # control period
TRICKLE_TILT = 20.0    # plate deg (trim setting; may be bumped by probe)
TAU_S = 0.30           # afterflow lookahead in the cutoff
CUTOFF_MARGIN_G = 0.035
MAX_RATE = 0.05        # r_sp ceiling (g/s)
R_SP_FLOOR = 0.003     # r_sp floor (g/s)
KP = 250.0
KI = 120.0
INTEG_CLIP = 0.5
RPM_MAX = 45.0
FF_PRIOR = 0.35        # g/rev prior (the function's own default)
TAP_TILT = 0.0
STALL_BAIL_S = 8.0
K_SIGMA = 1.0

# ---- tap_finish parameters (controllers.py defaults, verbatim) ------
TOL_G = 0.005
TAPS_PER_CYCLE = 1     # trickle_tap passes 1 (single taps: charged lip)
TAP_SETTLE_S = 1.2
MAX_TAP_CYCLES = 120
NUDGE_DEG = 5.0
NUDGE_RPM = 10.0
MAX_NUDGES = 20

# ---- estimator constants (hardware-measured, kf_bangbang.py) --------
TAU_BAL_S = 0.16       # instrument lag, 2026-08-14 drop tests
RATE_TAU_S = 0.5
Q_ACC_SD = 0.25        # replay-calibrated on the 08-12 afterflow data
R_SD_QUIET = 0.0004
R_SD_ACTUATE = 0.0020
STALE_MS = 260

# ---- session / battery ----------------------------------------------
POLL_MS = 95
SURVEY_S = 90.0        # session-start quiet survey (drift + jitter)
SURVEY_END_S = 60.0
DRIFT_WIN_S = 15.0     # per-trial quiet window before the baseline
PREROLL_S = 1.5        # KF lock-in on the baseline before actuating
SETTLE_STREAM_S = 4.0
CONFIRM_WAIT_S = 3.0
TRIAL_TIMEOUT_S = 420.0
WALL_BUDGET_S = 2100.0     # stop starting new trials past this point
PROBE_REVS = 3.0
PROBE_RPM = 30.0
PROBE_MIN_G_PER_REV = 0.0015
TILT_BUMP_MAX = 30.0   # never raise the trim tilt past this

# (target_g, rep) -- interleaved so drift / lip history cannot alias
# onto target size.
TRIALS = (
    (0.20, 1),
    (0.10, 1),
    (0.40, 1),
    (0.20, 2),
    (0.10, 2),
    (0.20, 3),
)

# ---- safety budget --------------------------------------------------
BUDGET_G = 8.0         # max total dispensed this session (small cup!)
CAP_HEADROOM_G = 20.0
BAL_MAX_G = 95.0

_t0 = time.ticks_ms() if m3 is not None else 0


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _t0)


def ev(msg):
    print("E,{},{}".format(t_ms(), msg))


def meta(k, v):
    print("M,{},{}".format(k, v))


def clip(x, lo, hi):
    return lo if x < lo else (hi if x > hi else x)


# ---------------------------------------------------------------------
# 3-state Kalman filter -- identical to kf_bangbang.py's KF3.
# ---------------------------------------------------------------------

class KF3:
    """x = [m, r, b]; balance observes b = first-order lag of m."""

    def __init__(self, tau_bal=TAU_BAL_S, ff=FF_PRIOR):
        self.tau_bal = tau_bal
        self.ff = ff
        self.reset()

    def reset(self, m0=0.0):
        self.x = [m0, 0.0, m0]
        self.P = [[1e-6, 0.0, 0.0],
                  [0.0, 2.5e-3, 0.0],
                  [0.0, 0.0, 1e-6]]

    def predict(self, dt, u_rev_s):
        a = dt / RATE_TAU_S
        if a > 1.0:
            a = 1.0
        beta = 1.0 - math.exp(-dt / self.tau_bal)
        m, r, b = self.x
        self.x = [m + r * dt,
                  (1.0 - a) * r + a * self.ff * u_rev_s,
                  beta * m + (1.0 - beta) * b]
        F = ((1.0, dt, 0.0),
             (0.0, 1.0 - a, 0.0),
             (beta, 0.0, 1.0 - beta))
        P = self.P
        FP = [[sum(F[i][k] * P[k][j] for k in range(3)) for j in range(3)]
              for i in range(3)]
        NP = [[sum(FP[i][k] * F[j][k] for k in range(3)) for j in range(3)]
              for i in range(3)]
        va = Q_ACC_SD * Q_ACC_SD
        NP[0][0] += va * dt ** 4 / 4.0
        NP[0][1] += va * dt ** 3 / 2.0
        NP[1][0] += va * dt ** 3 / 2.0
        NP[1][1] += va * dt * dt
        NP[2][2] += 1e-10
        self.P = NP

    def update(self, z, noisy):
        sd = R_SD_ACTUATE if noisy else R_SD_QUIET
        P = self.P
        S = P[2][2] + sd * sd
        K = [P[0][2] / S, P[1][2] / S, P[2][2] / S]
        y = z - self.x[2]
        for i in range(3):
            self.x[i] += K[i] * y
        row = (P[2][0], P[2][1], P[2][2])
        for i in range(3):
            for j in range(3):
                P[i][j] -= K[i] * row[j]
        for i in range(3):
            for j in range(i + 1, 3):
                s = 0.5 * (P[i][j] + P[j][i])
                P[i][j] = s
                P[j][i] = s
        if self.x[1] < 0.0:
            self.x[1] = 0.0

    def pred_sigma(self, tau):
        P = self.P
        v = P[0][0] + tau * tau * P[1][1] + 2.0 * tau * P[0][1]
        return math.sqrt(v) if v > 0.0 else 0.0


# ---------------------------------------------------------------------

class Rig:
    def __init__(self):
        self.scale = m3.Scale()
        self.stepper = m3.Stepper()
        self.servo = m3.Servo()
        self.tapper = m3.Tap()
        self.spr = int(round(self.stepper.steps_per_rev))
        self.trial = 0
        self.rpm = 0.0
        self.absmass = 0.0
        self.dispensed = 0.0
        self.abs0 = None
        self.aborted = False

    # -- actuation -----------------------------------------------------
    def set_rpm(self, rpm):
        sign = 1 if m3.config.STEPPER_DIRECTION >= 0 else -1
        if rpm <= 0.0:
            if self.stepper._enabled:
                self.stepper.tic.set_target_velocity(0)
            self.rpm = 0.0
            return
        self.stepper.set_speed(rpm)
        if not self.stepper._enabled:
            self.stepper.enable(True)
        vel = sign * max(1, int(rpm / 60.0 * self.spr * 10000))
        self.stepper.tic.set_target_velocity(vel)
        self.rpm = rpm

    def deenergize(self):
        try:
            self.stepper.tic.set_target_velocity(0)
        except Exception:
            pass
        try:
            self.stepper.enable(False)
        except Exception:
            pass
        self.rpm = 0.0

    def rotate_deg(self, deg, rpm):
        """Blocking incremental rotation (tap-finish nudge)."""
        self.stepper.set_speed(rpm)
        self.stepper.rotate_degrees(deg)
        self.deenergize()

    def tap(self, n):
        self.tapper.tap(n)

    # -- measurement ---------------------------------------------------
    def raw(self):
        r = self.scale.read()
        if r is None or r.grams is None:
            return None, False
        self.absmass = r.grams
        return r.grams, r.stable

    def sample(self, phase):
        z, stab = self.raw()
        print("D,{},{},{},{},{},0,{:.1f},,,,,,,,,".format(
            t_ms(), self.trial, phase,
            "nan" if z is None else "{:.4f}".format(z),
            "X" if z is None else ("S" if stab else "U"), self.rpm))
        return z

    def stream(self, seconds, phase):
        end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
        last = None
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            m = self.sample(phase)
            if m is not None:
                last = m
            time.sleep_ms(POLL_MS)
        return last

    def settled(self, kind, timeout_ms=8000):
        """Stable read; falls back to a 5-fresh-frame median bracket
        (the A&D withholds ST while disturbed -- the #116 read-path
        lesson)."""
        r = self.scale.read_stable(timeout_ms=timeout_ms)
        stab = True
        g = None if (r is None or r.grams is None) else r.grams
        if g is None:
            stab = False
            vals, prev = [], None
            t_end = time.ticks_add(time.ticks_ms(), 4000)
            while len(vals) < 5 and \
                    time.ticks_diff(t_end, time.ticks_ms()) > 0:
                z, _ = self.raw()
                if z is not None and z != prev:
                    vals.append(z)
                    prev = z
                time.sleep_ms(POLL_MS)
            if vals:
                vals.sort()
                g = vals[len(vals) // 2]
        if g is not None:
            self.absmass = g
        print("P,{},{},{},{},{}".format(
            t_ms(), self.trial, kind,
            "nan" if g is None else "{:.4f}".format(g),
            "S" if stab else "U"))
        return g

    # -- the ported controller -----------------------------------------
    def trickle_tap(self, target_g, m_base, t_trial0):
        """bangbang.trickle_tap, differences from m_base, sim waits
        replaced by measured-dt KF prediction.  Returns (verdict,
        t_trickle_s, revs, ff, taps, nudges, cycles, m_posttrickle)."""
        kf = KF3()
        kf.reset(0.0)                       # seeded at the settled base
        self.servo.move_to(TRICKLE_TILT)
        time.sleep_ms(800)

        # pre-roll: quiet frames so the filter locks the baseline
        t_prev = time.ticks_ms()
        z_prev = None
        t_upd = time.ticks_ms()
        end = time.ticks_add(time.ticks_ms(), int(PREROLL_S * 1000))
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            now = time.ticks_ms()
            dt = time.ticks_diff(now, t_prev) / 1000.0
            t_prev = now
            if dt <= 0.0:
                dt = POLL_MS / 1000.0
            kf.ff = FF_PRIOR
            kf.predict(dt, 0.0)
            z, stab = self.raw()
            fresh = 0
            if z is not None:
                fresh = 1 if (z != z_prev or time.ticks_diff(
                    now, t_upd) > STALE_MS) else 0
                if fresh:
                    kf.update(z - m_base, False)
                    t_upd = now
                z_prev = z
            self._log_pi(now, "preroll", z, stab, fresh, kf,
                         0.0, 0.0, FF_PRIOR, CUTOFF_MARGIN_G)
            time.sleep_ms(POLL_MS)

        # ---- the rate-PI trickle loop (verbatim port) ----
        integ, rpm, ff, revs = 0.0, 0.0, FF_PRIOR, 0.0
        last_m, last_gain_t = 0.0, time.ticks_ms()
        t_start = time.ticks_ms()
        verdict = "cutoff"
        # ~150 ms sleep + one balance Q-poll lands near the 0.2 s the
        # sim's rig.wait(dt) provides; the measured dt feeds the KF.
        loop_ms = 150
        while True:
            el = time.ticks_diff(time.ticks_ms(), t_trial0) / 1000.0
            if el > TRIAL_TIMEOUT_S:
                self.set_rpm(0.0)
                verdict = "timeout"
                break
            time.sleep_ms(loop_ms)
            now = time.ticks_ms()
            dt = time.ticks_diff(now, t_prev) / 1000.0
            t_prev = now
            if dt <= 0.0:
                dt = DT_S
            revs += (rpm / 60.0) * dt
            kf.ff = ff
            kf.predict(dt, rpm / 60.0)
            z, stab = self.raw()
            fresh = 0
            if z is not None:
                fresh = 1 if (z != z_prev or time.ticks_diff(
                    now, t_upd) > STALE_MS) else 0
                if fresh:
                    kf.update(z - m_base, self.rpm > 0.0)
                    t_upd = now
                z_prev = z
            m, r = kf.x[0], kf.x[1]
            if revs > 0.3 and m > 1e-3:
                ff = 0.9 * ff + 0.1 * (m / revs)
            margin = CUTOFF_MARGIN_G + 0.06 * max(0.0, ff - 0.30)
            sigma = kf.pred_sigma(TAU_S)
            remaining = target_g - m
            r_sp = clip((remaining - margin) / (2.0 * TAU_S),
                        R_SP_FLOOR, MAX_RATE)
            self._log_pi(now, "trickle", z, stab, fresh, kf,
                         r_sp, integ, ff, margin)
            if m + r * TAU_S + K_SIGMA * sigma >= target_g - margin:
                self.set_rpm(0.0)
                print("H,{},{},{:.4f},{:.4f},{:.4f},{:.4f},{:.4f},cutoff"
                      .format(t_ms(), self.trial, m, r * TAU_S,
                              K_SIGMA * sigma, margin, target_g))
                break
            if m - last_m > 2e-3:
                last_m, last_gain_t = m, now
            elif time.ticks_diff(now, last_gain_t) / 1000.0 \
                    > STALL_BAIL_S:
                self.set_rpm(0.0)
                print("H,{},{},{:.4f},{:.4f},{:.4f},{:.4f},{:.4f},stall"
                      .format(t_ms(), self.trial, m, r * TAU_S,
                              K_SIGMA * sigma, margin, target_g))
                verdict = "stall_bail"
                break
            err = r_sp - r
            integ = clip(integ + err * dt, -INTEG_CLIP, INTEG_CLIP)
            rpm = clip(KP * err + KI * integ, 0.0, RPM_MAX)
            self.set_rpm(rpm)
            self.stepper.keep_alive()
            if z is not None and z > BAL_MAX_G:
                ev("HARD CAP mid-trickle: {:.2f} g".format(z))
                self.set_rpm(0.0)
                self.aborted = True
                verdict = "capped"
                break
        t_trickle = time.ticks_diff(time.ticks_ms(), t_start) / 1000.0
        self.deenergize()
        time.sleep_ms(1200)                  # rig.wait(1.2) before taps

        if verdict in ("timeout", "capped"):
            # the sim returns without the tap finish on these paths
            m_post = self.settled("posttrickle")
            if m_post is None:
                m_post = self.absmass
            return (verdict, t_trickle, revs, ff, 0, 0, 0, m_post)

        # ---- tap finish (controllers.tap_finish, taps_per_cycle=1) ----
        self.servo.move_to(TAP_TILT)
        time.sleep_ms(800)
        prev = self.settled("posttrickle")
        if prev is None:
            prev = self.absmass
        m_post = prev
        taps = nudges = cycles = stall = 0
        tap_verdict = "tap_stalled"
        for _ in range(MAX_TAP_CYCLES):
            remaining = target_g - (prev - m_base)
            if remaining <= TOL_G:
                tap_verdict = ("ok" if remaining >= -TOL_G
                               else "overshoot_abort")
                break
            el = time.ticks_diff(time.ticks_ms(), t_trial0) / 1000.0
            if el > TRIAL_TIMEOUT_S:
                tap_verdict = "timeout"
                break
            cycles += 1
            n = TAPS_PER_CYCLE if remaining > 0.02 else 1
            m_before = prev
            self.tap(n)
            taps += n
            time.sleep_ms(int(TAP_SETTLE_S * 1000))
            grams = self.settled("tapread")
            if grams is None:
                grams = self.absmass
            print("C,{},{},{},{},{},{:.4f},{:.4f}".format(
                t_ms(), self.trial, cycles, taps, nudges,
                m_before, grams))
            if grams - prev < 2e-4:
                stall += 1
                if stall >= 3:
                    if nudges >= MAX_NUDGES:
                        tap_verdict = "tap_stalled"
                        prev = grams
                        break
                    self.rotate_deg(NUDGE_DEG, NUDGE_RPM)
                    time.sleep_ms(int(TAP_SETTLE_S * 1000))
                    nudges += 1
                    stall = 0
            else:
                stall = 0
            prev = grams
        final_verdict = tap_verdict if verdict in ("cutoff", "stall_bail") \
            else verdict
        return (final_verdict, t_trickle, revs, ff, taps, nudges, cycles,
                m_post)

    def _log_pi(self, ts, phase, z, stab, fresh, kf, r_sp, integ, ff,
                margin):
        print("D,{},{},{},{},{},{},{:.1f},{:.4f},{:.4f},{:.4f},{:.5f},"
              "{:.4f},{:.4f},{:.3f},{:.4f},{:.4f}".format(
                  time.ticks_diff(ts, _t0), self.trial, phase,
                  "nan" if z is None else "{:.4f}".format(z),
                  "X" if z is None else ("S" if stab else "U"),
                  fresh, self.rpm, kf.x[0], kf.x[1], kf.x[2],
                  kf.pred_sigma(TAU_S),
                  kf.x[0] + kf.x[1] * TAU_S,
                  r_sp, integ, ff, margin))

    # -- one full trial ------------------------------------------------
    def trial_run(self, target_g, rep):
        self.trial += 1
        ev("=== trial {} : target {:.3f} g, trickle tilt {:.0f}, tap "
           "tilt {:.0f}, rep {} (dispensed {:.3f} g) ===".format(
               self.trial, target_g, TRICKLE_TILT, TAP_TILT, rep,
               self.dispensed))

        # quiet drift window (stepper de-energised, servo parked)
        self.deenergize()
        self.stream(DRIFT_WIN_S, "drift")

        m_base = self.settled("base")
        if m_base is None:
            m_base = self.absmass
        if self.abs0 is None:
            self.abs0 = m_base
        if m_base > BAL_MAX_G or m_base - self.abs0 > CAP_HEADROOM_G:
            ev("CAP: absolute cup {:.2f} g -- stopping battery".format(
                m_base))
            self.aborted = True
            return

        t_trial0 = time.ticks_ms()
        (verdict, t_trickle, revs, ff, taps, nudges, cycles,
         m_post) = self.trickle_tap(target_g, m_base, t_trial0)

        self.deenergize()
        self.stream(SETTLE_STREAM_S, "settle")
        m_set = self.settled("settled")
        self.stream(CONFIRM_WAIT_S, "settle")
        m_set2 = self.settled("settled2")
        if m_set is None:
            m_set = self.absmass
        if m_set2 is None:
            m_set2 = m_set

        t_total = time.ticks_diff(time.ticks_ms(), t_trial0) / 1000.0
        disp = m_set2 - m_base
        self.dispensed += max(0.0, disp)
        err_mg = (disp - target_g) * 1000.0
        short_mg = ((m_post - m_base) - target_g) * 1000.0
        print("T,{},{:.3f},{:.0f},{:.0f},{},{:.4f},{:.1f},{:.2f},"
              "{:.4f},{:.4f},{},{},{},{:.1f},{:.4f},{:.4f},{:.4f},"
              "{:+.1f},{:+.1f},{}".format(
                  self.trial, target_g, TRICKLE_TILT, TAP_TILT, rep,
                  m_base, t_trickle, revs, ff, m_post, taps, nudges,
                  cycles, t_total, m_set, m_set2, disp, err_mg,
                  short_mg, verdict))
        ev("trial {} {}: dispensed {:.4f} g, error {:+.1f} mg "
           "(trickle landed {:+.1f} mg), {} taps, {} nudges, "
           "{:.1f} s".format(self.trial, verdict, disp, err_mg,
                             short_mg, taps, nudges, t_total))
        if self.dispensed > BUDGET_G:
            ev("BUDGET: {:.2f} g dispensed >= {:.1f} g -- stopping"
               .format(self.dispensed, BUDGET_G))
            self.aborted = True


def feed_probe(rig):
    """Confirm the trim tilt conveys CMC at all; bump 20->25->30 deg if
    it does not (cohesive powders arch -- battery Block C saw 46-157 %
    RSD off the 45 deg sweet spot).  Also charges the lip so trial 1
    matches the mid-dose context trickle_tap is written for."""
    global TRICKLE_TILT
    while True:
        ev("feed probe: {} rev at {:.0f} rpm, tilt {:.0f}".format(
            PROBE_REVS, PROBE_RPM, TRICKLE_TILT))
        rig.servo.move_to(TRICKLE_TILT)
        time.sleep_ms(1000)
        m0 = rig.settled("probe_base")
        rig.stepper.set_speed(PROBE_RPM)
        rig.stepper.rotate_degrees(PROBE_REVS * 360.0)
        rig.deenergize()
        rig.stream(3.0, "settle")
        m1 = rig.settled("probe_end")
        if m0 is None or m1 is None:
            ev("probe read failed -- aborting")
            rig.aborted = True
            return
        rig.dispensed += max(0.0, m1 - m0)
        per_rev = (m1 - m0) / PROBE_REVS
        ev("probe yield {:.4f} g over {} rev -> {:.4f} g/rev".format(
            m1 - m0, PROBE_REVS, per_rev))
        print("B,{},{:.0f},{:.4f},{:.4f}".format(
            t_ms(), TRICKLE_TILT, m1 - m0, per_rev))
        if per_rev >= PROBE_MIN_G_PER_REV:
            meta("trickle_tilt_final", TRICKLE_TILT)
            return
        if TRICKLE_TILT >= TILT_BUMP_MAX:
            ev("no conveyance up to {:.0f} deg -- battery aborted, "
               "bench attention needed".format(TILT_BUMP_MAX))
            rig.aborted = True
            return
        TRICKLE_TILT += 5.0
        ev("no conveyance -- bumping trim tilt to {:.0f} deg".format(
            TRICKLE_TILT))


def main():
    meta("experiment", "pi-trickle-tap-trim")
    meta("powder_id", POWDER_ID)
    meta("algorithm", "trickle_tap @ bangbang.py dc99459 (PR #124)")
    meta("kp", KP)
    meta("ki", KI)
    meta("dt_s", DT_S)
    meta("tau_s", TAU_S)
    meta("cutoff_margin_g", CUTOFF_MARGIN_G)
    meta("max_rate", MAX_RATE)
    meta("r_sp_floor", R_SP_FLOOR)
    meta("rpm_max", RPM_MAX)
    meta("ff_prior", FF_PRIOR)
    meta("k_sigma", K_SIGMA)
    meta("stall_bail_s", STALL_BAIL_S)
    meta("trickle_tilt_deg", TRICKLE_TILT)
    meta("tap_tilt_deg", TAP_TILT)
    meta("tol_g", TOL_G)
    meta("taps_per_cycle", TAPS_PER_CYCLE)
    meta("tap_settle_s", TAP_SETTLE_S)
    meta("max_tap_cycles", MAX_TAP_CYCLES)
    meta("nudge_deg", NUDGE_DEG)
    meta("max_nudges", MAX_NUDGES)
    meta("tau_bal_s", TAU_BAL_S)
    meta("rate_tau_s", RATE_TAU_S)
    meta("q_acc_sd", Q_ACC_SD)
    meta("r_sd_quiet", R_SD_QUIET)
    meta("r_sd_actuate", R_SD_ACTUATE)
    meta("trial_timeout_s", TRIAL_TIMEOUT_S)
    meta("budget_g", BUDGET_G)
    meta("trials", "|".join("{:.2f}:{}".format(*t) for t in TRIALS))

    rig = Rig()
    try:
        rig.servo.move_to(0.0)
        time.sleep_ms(1200)
        ev("session survey {:.0f} s (quiet, no tare -- absolute)".format(
            SURVEY_S))
        rig.settled("pre")
        rig.stream(SURVEY_S, "survey")
        rig.settled("survey_end")

        feed_probe(rig)

        t_batt = time.ticks_ms()
        for (target_g, rep) in TRIALS:
            if rig.aborted:
                break
            el = time.ticks_diff(time.ticks_ms(), t_batt) / 1000.0
            if el > WALL_BUDGET_S:
                ev("wall budget {:.0f} s reached -- stopping cleanly "
                   "with {} trials done".format(WALL_BUDGET_S,
                                               rig.trial))
                break
            rig.trial_run(target_g, rep)

        n_trials = rig.trial
        ev("end survey {:.0f} s".format(SURVEY_END_S))
        rig.trial = 0
        rig.stream(SURVEY_END_S, "endsurvey")
        rig.settled("end")
        ev("battery complete: {} trials, {:.3f} g dispensed".format(
            n_trials, rig.dispensed))
    except KeyboardInterrupt:
        ev("KeyboardInterrupt -- stopping")
    finally:
        try:
            rig.deenergize()
        except Exception:
            pass
        try:
            rig.servo._write_angle(0.0)
        except Exception:
            pass
    print("SUMMARY,dispensed={:.3f}".format(rig.dispensed))
    print("RUN,END,ok")


if m3 is not None:       # on the Pico: run.  Off-device: import-only.
    main()

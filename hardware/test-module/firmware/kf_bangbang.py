"""Kalman-filter bang-bang dosing test -- PR #131 request (2026-08-17).

Runs ON the Pico via ``mpremote run`` (RAM only -- nothing is written to
the Pico filesystem).  Re-uses ``main_three_phase``'s hardware driver
classes (Stepper / Servo / Scale); no dose-controller logic from there.

What this is
------------
The first HARDWARE test of the estimator prototyped in simulation on the
PR #124 branch (``optimization/benchmarks/bangbang.py``): the 3-state
``MassRateLagKF`` (true mass, flow rate, balance reading) driving a
"bang-bang" stop rule -- spin the auger at one constant rate and hard-stop
the instant the predicted SETTLED cup mass reaches the target.

The KF is re-implemented here in dependency-free MicroPython (no numpy /
filterpy on the Pico): 3x3 predict + scalar measurement update, ~50 flops
per frame, comfortably real time at the balance's ~5 Hz datum rate.

State / model
-------------
    x = [m, r, b]
      m  true cup mass (g, relative to the trial baseline)
      r  flow rate (g/s)
      b  what the BALANCE will report -- a first-order lag of m

    m' = m + r dt
    r' = (1-a) r + a * ff * u        a = dt / RATE_TAU_S, u = commanded rev/s
    b' = beta m + (1-beta) b         beta = 1 - exp(-dt / TAU_BAL_S)
    z  = b + noise                   the balance measures b, NOT m

``TAU_BAL_S`` is an INSTRUMENT constant, measured on this balance by the
2026-08-14 known-mass drop tests: **tau_bal = 0.16 s** (pooled first-order
fit over 28 clean steps, mass- and height-independent; see
``data/balance-step/2026-08-14/``).  The twin had assumed 0.7 s.

Stop rules (one per variant, all on the same hardware pass)
----------------------------------------------------------
  naive   halt when the RAW reading crosses target      (control)
  kflag   halt when the KF's lag-free mass m_hat >= target
            -- isolates what removing the 0.16 s instrument lag buys
  kf      halt when m_hat + r_hat * TAU_AFTER_S >= target
            -- BangBangFF: adds the physical afterflow lookahead
  kfsafe  halt when m_hat + r_hat * TAU_AFTER_S + K_SIGMA * sigma_pred
            >= target   -- BangBangSafe: undershoot-biased by the KF's own
            covariance, since powder cannot be removed

``TAU_AFTER_S`` covers only the PHYSICAL afterflow (lip drain + free
fall), because the KF has already removed the instrument lag.  It (and
Q_ACC_SD) were calibrated OFFLINE before this run by replaying this exact
filter over the 39 recorded dispense-and-settle trials of the 2026-08-12
afterflow battery and scoring the predictor against each trial's settled
mass (``scripts/analyze_kf_bangbang.py --replay``):

    auger-only (C7, n=12), tau_bal = 0.16 s
        tau_after = 0.25 s -> predictor error   +4 +/- 17 mg
        raw balance reading at halt             -27 +/- .. mg (late)
    with the twin's assumed tau_bal = 0.70 s   +37..+52 mg  (biased)

so the 0.16 s measured lag is worth ~40 mg of bias on its own.  This
battery is auger-only (no taps): the tap-while-rotating trials (C6) need
a larger lookahead, ~0.45 s.

Measurement / balance quirks (learned the hard way, 2026-08-13)
---------------------------------------------------------------
* No per-trial hardware tare: the A&D `Z` is silently rejected / stops
  answering `Q` while the pan is loaded and settling.  Every trial takes a
  settled BASELINE and works in differences, so a standing cup offset
  cancels.
* The balance updates its datum at only ~5 Hz while we poll at ~10 Hz, so
  the same value comes back twice.  A repeated value is NOT independent
  information: the KF measurement update only fires on a FRESH frame
  (value changed, or >= STALE_MS since the last update); otherwise the
  frame is predict-only.  ``fresh`` is logged per sample.
* The stepper is de-energised before every settle/weigh so the Tic driver
  cannot inject noise into the scale UART.

Telemetry (CSV over USB stdout)
-------------------------------
    M,<key>,<value>
    E,<t_ms>,<text>
    D,<t_ms>,<trial>,<phase>,<mass>,<S|U|X>,<fresh>,<rpm>,<m_hat>,<r_hat>,
      <b_hat>,<sigma>,<pred>
    P,<t_ms>,<trial>,<kind>,<mass>,<S|U>
    T,<trial>,<variant>,<target_g>,<tilt>,<rpm>,<rep>,<m_base>,<m_halt_raw>,
      <m_hat_halt>,<r_hat_halt>,<sigma_halt>,<pred_halt>,<t_disp_s>,
      <m_settled>,<m_settled2>,<dispensed_g>,<error_mg>,<afterflow_mg>,
      <verdict>
"""

import math
import time

try:
    import main_three_phase as m3
except ImportError:      # off-device: the analysis script imports KF3 alone
    m3 = None

POWDER_ID = "salt"

# ---- estimator constants -------------------------------------------
TAU_BAL_S = 0.16       # MEASURED instrument lag (2026-08-14 drop tests)
TAU_AFTER_S = 0.25     # physical afterflow lookahead (lip + in-flight)
RATE_TAU_S = 0.5       # how fast the rate state relaxes to ff * u
FF_PRIOR = 0.10        # g per auger rev prior (depleted tube, ~0.04 g/s
                       # at 55 rpm in the 2026-08-12 B4 block); the
                       # measurement update corrects it within ~1 s
Q_ACC_SD = 0.25        # process noise: rate random-walk accel (g/s^2)
R_SD_QUIET = 0.0004    # balance noise, static (0.13-0.42 mg measured)
R_SD_ACTUATE = 0.0020  # balance noise while the auger spins
K_SIGMA = 2.0          # kfsafe undershoot bias, in predictor sigmas
STALE_MS = 260         # a repeated value older than this is used anyway

# ---- rig / battery --------------------------------------------------
TILT = 55.0            # plate deg -- good flow, well characterised
RPM = 55.0             # the "bang" rate
RPM_FAST = 90.0        # second rate, to show the rate/target interaction
POLL_MS = 95           # ~10.5 Hz, ~2x the balance datum rate
PREROLL_S = 1.5
SETTLE_STREAM_S = 6.0
CONFIRM_WAIT_S = 3.0
NOISE_S = 20.0
DOSE_TIMEOUT_S = 150.0
NOFLOW_ABORT_S = 25.0

# ---- safety budget --------------------------------------------------
BUDGET_G = 15.0        # max total dispensed per pass
CAP_HEADROOM_G = 18.0  # abort if absolute cup mass climbs this far
BAL_MAX_G = 95.0       # keep the pan under the balance's 102 g range

# (variant, target_g, rpm, rep) -- interleaved so hopper drawdown cannot
# alias onto either variant or target.  PASS 1 sweeps the four targets and
# all four stop rules; PASS 2 (run straight after, same salt, same cup)
# adds replicates and probes the small-target floor where the afterflow
# itself is comparable to the dose.
TRIALS_PASS1 = (
    ("kf",     0.20, RPM,      1),
    ("naive",  0.50, RPM,      1),
    ("kf",     0.50, RPM,      1),
    ("kfsafe", 0.50, RPM,      1),
    ("kflag",  0.50, RPM,      1),
    ("kf",     1.00, RPM,      1),
    ("naive",  1.00, RPM,      1),
    ("kfsafe", 1.00, RPM,      1),
    ("kf",     2.00, RPM,      1),
    ("kf",     2.00, RPM,      2),
    ("kf",     1.00, RPM_FAST, 1),
    ("kf",     1.00, RPM,      2),
    ("kf",     0.50, RPM,      2),
    ("kf",     0.20, RPM,      2),
)

TRIALS_PASS2 = (
    ("kf",     0.10, RPM,      1),
    ("kf",     0.50, RPM,      3),
    ("kflag",  1.00, RPM,      1),
    ("kf",     1.00, RPM,      3),
    ("naive",  0.50, RPM,      2),
    ("kfsafe", 0.50, RPM,      2),
    ("kf",     2.00, RPM,      3),
    ("kf",     0.20, RPM,      3),
    ("kf",     0.10, RPM,      2),
    ("kf",     1.00, RPM_FAST, 2),
)

PASS = 2
TRIALS = TRIALS_PASS1 if PASS == 1 else TRIALS_PASS2

_t0 = time.ticks_ms() if m3 is not None else 0


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _t0)


def ev(msg):
    print("E,{},{}".format(t_ms(), msg))


def meta(k, v):
    print("M,{},{}".format(k, v))


# ---------------------------------------------------------------------
# 3-state Kalman filter, dependency-free (lists of floats).
# ---------------------------------------------------------------------

class KF3:
    """x = [m, r, b]; balance observes b = first-order lag of m."""

    def __init__(self, tau_bal=TAU_BAL_S, ff=FF_PRIOR):
        self.tau_bal = tau_bal
        self.ff = ff
        self.reset()

    def reset(self, m0=0.0):
        self.x = [m0, 0.0, m0]
        # mass/reading known well at the (settled) baseline, rate unknown
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
        # P = F P F^T + Q   (3x3, written out -- no numpy on the Pico)
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
        # keep it symmetric + the rate physical (powder never leaves)
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
        self.spr = int(round(self.stepper.steps_per_rev))
        self.trial = 0
        self.rpm = 0.0
        self.absmass = 0.0
        self.dispensed = 0.0
        self.abs0 = None
        self.aborted = False
        self.kf = KF3()
        self.m_base = 0.0
        self.pred = 0.0

    # -- actuation -----------------------------------------------------
    def auger_run(self, rpm):
        sign = 1 if m3.config.STEPPER_DIRECTION >= 0 else -1
        self.stepper.set_speed(rpm)
        if not self.stepper._enabled:
            self.stepper.enable(True)
        vel = sign * max(1, int(rpm / 60.0 * self.spr * 10000))
        self.stepper.tic.set_target_velocity(vel)
        self.rpm = rpm

    def halt(self):
        """Abrupt stop -- no decel ramp, the fastest the Tic allows."""
        self.stepper.tic.halt_and_set_position(0)
        self.stepper._position = 0
        self.rpm = 0.0

    def deenergize(self):
        try:
            self.stepper.enable(False)
        except Exception:
            pass

    # -- measurement ---------------------------------------------------
    def sample(self, phase, kf=None):
        r = self.scale.read()
        ts = t_ms()
        if r is None or r.grams is None:
            print("D,{},{},{},nan,X,0,{:.0f},,,,,".format(
                ts, self.trial, phase, self.rpm))
            return None, False
        self.absmass = r.grams
        if kf is None:
            print("D,{},{},{},{:.4f},{},0,{:.0f},,,,,".format(
                ts, self.trial, phase, r.grams,
                "S" if r.stable else "U", self.rpm))
        return r.grams, r.stable

    def stream(self, seconds, phase):
        end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
        last = None
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            m, _ = self.sample(phase)
            if m is not None:
                last = m
            time.sleep_ms(POLL_MS)
        return last

    def settled(self, kind, timeout_ms=8000):
        r = self.scale.read_stable(timeout_ms=timeout_ms)
        stab = True
        if r is None or r.grams is None:
            stab = False
            r = self.scale.read()
        g = None if (r is None or r.grams is None) else r.grams
        if g is not None:
            self.absmass = g
        print("P,{},{},{},{},{}".format(
            t_ms(), self.trial, kind,
            "nan" if g is None else "{:.4f}".format(g),
            "S" if stab else "U"))
        return g

    # -- one bang-bang trial -------------------------------------------
    def trial_run(self, variant, target_g, rpm, rep):
        self.trial += 1
        ev("=== trial {} : {} target {:.3f} g, tilt {:.0f}, {:.0f} rpm, "
           "rep {} (dispensed {:.2f} g) ===".format(
               self.trial, variant, target_g, TILT, rpm, rep,
               self.dispensed))
        self.servo.move_to(TILT)
        time.sleep_ms(1200)

        m_base = self.settled("base")
        if m_base is None:
            m_base = self.absmass
        self.m_base = m_base
        if self.abs0 is None:
            self.abs0 = m_base
        if m_base > BAL_MAX_G or m_base - self.abs0 > CAP_HEADROOM_G:
            ev("CAP: absolute cup {:.2f} g -- stopping battery".format(
                m_base))
            self.aborted = True
            return

        kf = self.kf
        kf.reset(0.0)
        self.pred = 0.0

        # pre-roll: quiet frames so the filter locks onto the baseline
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
            kf.predict(dt, 0.0)
            z, stab = self.sample("preroll", kf=kf)
            fresh = 0
            if z is not None:
                fresh = 1 if (z != z_prev or time.ticks_diff(
                    now, t_upd) > STALE_MS) else 0
                if fresh:
                    kf.update(z - m_base, False)
                    t_upd = now
                z_prev = z
            self._log_kf(now, "preroll", z, stab, fresh)
            time.sleep_ms(POLL_MS)

        # ---- the bang: constant max rate until the stop rule fires ----
        u_rev_s = rpm / 60.0
        self.auger_run(rpm)
        t_start = time.ticks_ms()
        t_prev = t_start
        verdict = "timeout"
        m_halt = None
        mhat_halt = rhat_halt = sig_halt = pred_halt = 0.0
        last_gain_m, last_gain_t = 0.0, t_start
        while True:
            now = time.ticks_ms()
            el = time.ticks_diff(now, t_start) / 1000.0
            if el > DOSE_TIMEOUT_S:
                ev("timeout at {:.1f} s".format(el))
                break
            dt = time.ticks_diff(now, t_prev) / 1000.0
            t_prev = now
            if dt <= 0.0:
                dt = POLL_MS / 1000.0
            kf.predict(dt, u_rev_s)
            z, stab = self.sample("dispense", kf=kf)
            fresh = 0
            if z is not None:
                fresh = 1 if (z != z_prev or time.ticks_diff(
                    now, t_upd) > STALE_MS) else 0
                if fresh:
                    kf.update(z - m_base, True)
                    t_upd = now
                z_prev = z
            mhat, rhat = kf.x[0], kf.x[1]
            sig = kf.pred_sigma(TAU_AFTER_S)
            if variant == "naive":
                pred = (z - m_base) if z is not None else 0.0
            elif variant == "kflag":
                pred = mhat
            elif variant == "kfsafe":
                pred = mhat + rhat * TAU_AFTER_S + K_SIGMA * sig
            else:                                     # "kf"
                pred = mhat + rhat * TAU_AFTER_S
            self.pred = pred
            self._log_kf(now, "dispense", z, stab, fresh)
            if pred >= target_g:
                self.halt()                            # same iteration
                m_halt = z
                mhat_halt, rhat_halt = mhat, rhat
                sig_halt, pred_halt = sig, pred
                verdict = "ok"
                ev("STOP {} at t={:.2f} s: raw {} pred {:.4f} "
                   "m_hat {:.4f} r_hat {:.4f} sigma {:.4f}".format(
                       variant, el,
                       "nan" if z is None else "{:.4f}".format(z - m_base),
                       pred, mhat, rhat, sig))
                break
            self.stepper.keep_alive()
            if z is not None:
                if (z - m_base) - last_gain_m > 0.0008:
                    last_gain_m = z - m_base
                    last_gain_t = now
                elif time.ticks_diff(now, last_gain_t) / 1000.0 \
                        > NOFLOW_ABORT_S:
                    ev("no flow for {:.0f} s -- abort trial".format(
                        NOFLOW_ABORT_S))
                    verdict = "stalled"
                    break
            if z is not None and z > BAL_MAX_G:
                ev("HARD CAP mid-dispense: {:.2f} g".format(z))
                verdict = "capped"
                self.aborted = True
                break
            time.sleep_ms(POLL_MS)
        self.halt()
        self.deenergize()
        t_disp = time.ticks_diff(time.ticks_ms(), t_start) / 1000.0
        if m_halt is None:
            m_halt = self.absmass
            mhat_halt, rhat_halt = kf.x[0], kf.x[1]
            sig_halt = kf.pred_sigma(TAU_AFTER_S)
            pred_halt = self.pred

        # ---- settle (nothing moving) ----
        self.stream(SETTLE_STREAM_S, "settle")
        m_set = self.settled("settled")
        self.stream(CONFIRM_WAIT_S, "settle")
        m_set2 = self.settled("settled2")
        if m_set is None:
            m_set = self.absmass
        if m_set2 is None:
            m_set2 = m_set

        disp = m_set2 - m_base
        self.dispensed += max(0.0, disp)
        err_mg = (disp - target_g) * 1000.0
        after_mg = (m_set2 - m_halt) * 1000.0
        print("T,{},{},{:.3f},{:.0f},{:.0f},{},{:.4f},{:.4f},{:.4f},"
              "{:.4f},{:.5f},{:.4f},{:.2f},{:.4f},{:.4f},{:.4f},{:.1f},"
              "{:.1f},{}".format(
                  self.trial, variant, target_g, TILT, rpm, rep,
                  m_base, m_halt, mhat_halt, rhat_halt, sig_halt,
                  pred_halt, t_disp, m_set, m_set2, disp, err_mg,
                  after_mg, verdict))
        ev("trial {} {}: dispensed {:.4f} g, error {:+.1f} mg, "
           "afterflow {:+.1f} mg, {:.1f} s".format(
               self.trial, variant, disp, err_mg, after_mg, t_disp))
        if self.dispensed > BUDGET_G:
            ev("BUDGET: {:.2f} g dispensed >= {:.1f} g -- stopping".format(
                self.dispensed, BUDGET_G))
            self.aborted = True

    def _log_kf(self, ts_ms, phase, z, stab, fresh):
        kf = self.kf
        print("D,{},{},{},{},{},{},{:.0f},{:.4f},{:.4f},{:.4f},"
              "{:.5f},{:.4f}".format(
                  time.ticks_diff(ts_ms, _t0), self.trial, phase,
                  "nan" if z is None else "{:.4f}".format(z),
                  "X" if z is None else ("S" if stab else "U"),
                  fresh, self.rpm, kf.x[0], kf.x[1], kf.x[2],
                  kf.pred_sigma(TAU_AFTER_S), self.pred))


def main():
    meta("experiment", "kf-bangbang-stop-accuracy")
    meta("powder_id", POWDER_ID)
    meta("tau_bal_s", TAU_BAL_S)
    meta("tau_after_s", TAU_AFTER_S)
    meta("rate_tau_s", RATE_TAU_S)
    meta("ff_prior_g_per_rev", FF_PRIOR)
    meta("q_acc_sd", Q_ACC_SD)
    meta("r_sd_quiet", R_SD_QUIET)
    meta("r_sd_actuate", R_SD_ACTUATE)
    meta("k_sigma", K_SIGMA)
    meta("tilt_plate_deg", TILT)
    meta("rpm", RPM)
    meta("rpm_fast", RPM_FAST)
    meta("poll_ms", POLL_MS)
    meta("budget_g", BUDGET_G)
    meta("pass", PASS)
    meta("trials", "|".join("{}:{:.2f}:{:.0f}:{}".format(*t)
                            for t in TRIALS))

    rig = Rig()
    try:
        rig.servo.move_to(0.0)
        time.sleep_ms(1200)
        ev("static noise baseline {:.0f} s (no tare -- absolute)".format(
            NOISE_S))
        rig.settled("pre")
        rig.stream(NOISE_S, "noise")
        rig.settled("noise_end")

        # priming pass: fills the auger lip so trial 1 is not a cold start
        ev("prime: 3 auger rev at {:.0f} rpm, tilt {:.0f}".format(
            RPM, TILT))
        rig.servo.move_to(TILT)
        time.sleep_ms(1000)
        m0 = rig.settled("prime_base")
        rig.stepper.set_speed(RPM)
        rig.stepper.rotate_degrees(3 * 360.0)
        rig.deenergize()
        rig.stream(4.0, "settle")
        m1 = rig.settled("prime_end")
        if m0 is not None and m1 is not None:
            rig.dispensed += max(0.0, m1 - m0)
            ev("prime yield {:.4f} g over 3 rev -> {:.4f} g/rev".format(
                m1 - m0, (m1 - m0) / 3.0))

        for (variant, target_g, rpm, rep) in TRIALS:
            if rig.aborted:
                break
            rig.trial_run(variant, target_g, rpm, rep)
        ev("battery complete: {} trials, {:.3f} g dispensed".format(
            rig.trial, rig.dispensed))
    except KeyboardInterrupt:
        ev("KeyboardInterrupt -- stopping")
    finally:
        try:
            rig.halt()
            rig.deenergize()
        except Exception:
            pass
        try:
            rig.servo._write_angle(0.0)
        except Exception:
            pass
    print("SUMMARY,trials={},dispensed={:.3f}".format(
        rig.trial, rig.dispensed))


if m3 is not None:       # on the Pico: run.  Off-device: import-only.
    main()

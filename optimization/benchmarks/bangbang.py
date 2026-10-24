"""Bang-bang dosing controllers (PR #124, the 2026-08-12 direction).

The team converged on a "bang-bang" idea (williamulbz, PR #124 2026-08-12):
dispense at the maximum feasible rate and hard-stop the instant the *predicted
settled cup mass* reaches target.  On the twin, max-rate dispensing commits a
large hidden inventory (screw hold-up + lip + in-flight + balance lag) -- a
naive stop-at-crossing overshoots by hundreds of mg -- so the whole problem is
the cup-mass predictor, exactly as the 08-12 write-up laid out.

This module prototypes that predictor and the controllers around it, developed
in iterations (kept as separate classes so the benchmark can score them side by
side and show the progression):

* BangBangNaive     - iter 1: max rate, stop when the raw balance crosses
                      target.  Reproduces the afterflow problem; a control.
* BangBangFF        - iter 2: max rate, stop on the KF committed-mass predictor
                      m_hat + r_hat * tau >= target.  tau is a fixed bench-style
                      prior (NOT the plant-coupled committed_lookahead_s(tilt),
                      which the methods-check flagged as grey-box leakage), so
                      this is a fair, hardware-realizable stop rule.
* BangBangSafe      - iter 3: adds an uncertainty margin k * sigma_pred from the
                      KF covariance so the hard stop lands on the undershoot
                      side of target (powder can't be removed -- asymmetric).
* BangBangTrim      - iter 4: bang-bang bulk to a safe undershoot, then hand the
                      last few mg to the shared tap/nudge trim endgame.  The
                      realistic winner: bang-bang speed with tolerance-grade
                      accuracy and no overshoot, and it also recovers when a
                      cohesive powder blocks (the trim endgame nudges).

The predictor is the 2-state (mass, rate) switching-covariance Kalman filter
from controllers.MassRateKF (the estimator the Edison MPC follow-up and the
data-assimilation critique both recommend), fed the commanded rev/s so it does
not lag the spin-up ramp.
"""
from __future__ import annotations

import math

import numpy as np

from rig import Rig
from controllers import tap_finish, TOL_G

# Balance filter time constant (seconds).  An INSTRUMENT property (the A&D's
# internal integration), measured once with the step-response test A1 from the
# 2026-08-12 plan -- not a powder/plant coefficient -- so modelling it carries
# no grey-box leakage.  The twin uses balance_integration_s = 0.7.
BAL_TAU_S = 0.7


class MassRateLagKF:
    """3-state (true mass, rate, balance reading) Kalman filter.

    Extends the 2-state MassRateKF by modelling the balance's first-order
    integration lag explicitly:  the pan reading b tracks true mass m through
    b' = (m - b)/tau_bal, and the balance MEASURES b, not m.  The controller
    then predicts against the lag-free true mass m, so the committed-mass
    lookahead only has to cover the physical afterflow (~0.3 s), not the 0.7 s
    instrument lag the 2-state filter had to absorb into a fudged tau.  This is
    the "3-state KF modelling balance lag" the benchmark README deferred."""

    RATE_TAU_S = 0.5

    def __init__(self, dt: float, bal_tau_s: float = BAL_TAU_S):
        from filterpy.kalman import KalmanFilter
        from filterpy.common import Q_discrete_white_noise
        self.kf = KalmanFilter(dim_x=3, dim_z=1)
        self.kf.x = np.zeros((3, 1))
        self.a = min(1.0, dt / self.RATE_TAU_S)
        self.beta = 1.0 - math.exp(-dt / max(1e-3, bal_tau_s))
        # x = [m, r, b];  m += r dt ;  r relaxes to ff*u ;  b tracks m
        self.kf.F = np.array([[1.0, dt, 0.0],
                              [0.0, 1.0 - self.a, 0.0],
                              [self.beta, 0.0, 1.0 - self.beta]])
        self.kf.H = np.array([[0.0, 0.0, 1.0]])       # balance observes b
        self.kf.P = np.diag([0.05, 0.05, 0.05])
        q2 = Q_discrete_white_noise(dim=2, dt=dt, var=2e-4)
        self.kf.Q = np.array([[q2[0, 0], q2[0, 1], 0.0],
                              [q2[1, 0], q2[1, 1], 0.0],
                              [0.0, 0.0, 1e-8]])
        self.dt = dt

    def seed(self, mass: float) -> None:
        self.kf.x[0, 0] = mass
        self.kf.x[2, 0] = mass

    def update(self, z: float, noisy: bool, u_rev_s: float = None,
               ff: float = None, fresh: bool = True) -> tuple[float, float]:
        from controllers import NOISY_SD, QUIET_SD
        self.kf.R = np.array([[(NOISY_SD if noisy else QUIET_SD) ** 2]])
        if u_rev_s is None:
            self.kf.F[1, 1] = 1.0
            self.kf.predict()
        else:
            self.kf.F[1, 1] = 1.0 - self.a
            B = np.array([[0.0], [self.a * (ff or 0.3)], [0.0]])
            self.kf.predict(u=np.array([[u_rev_s]]), B=B)
        if fresh:
            self.kf.update(np.array([[z]]))
        self.kf.x[1, 0] = max(0.0, self.kf.x[1, 0])
        return float(self.kf.x[0, 0]), float(self.kf.x[1, 0])

    def pred_sigma(self, tau_s: float) -> float:
        """Std-dev of the committed-mass prediction m + r*tau."""
        P = self.kf.P
        var = P[0, 0] + tau_s ** 2 * P[1, 1] + 2 * tau_s * P[0, 1]
        return float(np.sqrt(max(var, 0.0)))

# Physical afterflow time constant (seconds) for the stop predictor,
# pred = m_true_hat + r_hat * tau.  With the 3-state KF removing the balance
# lag, this only has to cover the actual afterflow (lip drain + free fall):
# the twin characterisation put tau_eff ~ 0.25-0.4 s at working flow rates.
# It is a fixed scalar the bang-bang controller calibrates from a few
# dispense-and-settle runs (the PR #131 stop-response test), NOT the
# plant-coupled committed_lookahead_s(tilt) the methods-check flagged.
TAU_PRIOR_S = 0.30
# max feed factor prior (g/rev) for the KF input model; only sets the spin-up
# transient, the measurement update corrects it within a few frames.
FF_PRIOR = 0.5


class BangBangNaive:
    """Iter 1 (control): full rate, stop when the raw balance crosses target."""

    name = "bangbang_naive"

    def __init__(self, dt=0.1, tilt=45.0):
        self.dt, self.tilt = dt, tilt

    def run(self, rig: Rig, target_g: float) -> str:
        rig.set_tilt(self.tilt)
        rig.wait(0.8)
        rig.set_rpm(Rig_MAX_RPM)
        while True:
            rig.wait(self.dt)
            z, _ = rig.read()
            if z >= target_g:
                break
            if rig.timed_out():
                rig.set_rpm(0.0)
                return "timeout"
        rig.set_rpm(0.0)
        rig.wait(1.5)
        return "ok"


class BangBangFF:
    """Iter 2: max rate, stop on the KF committed-mass predictor.

    Halt when  m_hat + r_hat * tau >= target.  No uncertainty margin yet, so it
    straddles target; shows the predictor cancels most of the afterflow."""

    name = "bangbang_ff"

    def __init__(self, dt=0.1, tilt=45.0, tau_s=TAU_PRIOR_S, ff_prior=FF_PRIOR):
        self.dt, self.tilt, self.tau_s, self.ff_prior = dt, tilt, tau_s, ff_prior

    def _stage(self, rig: Rig, target_g: float, rpm: float, tau_s: float,
               k_sigma: float, stop_g: float, kf: MassRateLagKF | None = None,
               tilt: float | None = None,
               stall_bail_s: float = 0.0) -> tuple[str, MassRateLagKF]:
        """One constant-rate ("bang") stage: spin at rpm until the KF
        committed-mass predictor  m_hat + r_hat*tau (+ k_sigma*sigma)  reaches
        stop_g, then halt.  The KF is threaded across stages so the estimate
        (and covariance) carries over.  stall_bail_s > 0 bails out of a stalled
        stage (no fresh mass for that long) so a blocked cohesive powder falls
        through to the tap/nudge endgame instead of spinning forever."""
        if kf is None:
            kf = MassRateLagKF(self.dt)
        if tilt is None:
            tilt = self.tilt
        rig.set_tilt(tilt)
        rig.wait(0.8)
        rig.set_rpm(rpm)
        last_tick, last_m, last_gain_t = -1, None, rig.t
        while True:
            if rig.timed_out():
                rig.set_rpm(0.0)
                return "timeout", kf
            rig.wait(self.dt)
            z, _, tick = rig.read_frame()
            m, r = kf.update(z, rig.actuating(), u_rev_s=rpm / 60.0,
                             ff=self.ff_prior, fresh=tick != last_tick)
            last_tick = tick
            sigma = kf.pred_sigma(tau_s)
            if m + r * tau_s + k_sigma * sigma >= stop_g:
                break
            if stall_bail_s > 0.0:
                if last_m is None or m - last_m > 2e-3:
                    last_m, last_gain_t = m, rig.t
                elif rig.t - last_gain_t > stall_bail_s:
                    rig.set_rpm(0.0)
                    return "stalled", kf
        rig.set_rpm(0.0)
        return "ok", kf

    def run(self, rig: Rig, target_g: float) -> str:
        st, _ = self._stage(rig, target_g, Rig_MAX_RPM, self.tau_s,
                            k_sigma=0.0, stop_g=target_g)
        if st != "ok":
            return st
        rig.wait(1.5)
        return "ok"


class BangBangSafe(BangBangFF):
    """Iter 3: bias the hard stop to the undershoot side by k * sigma_pred."""

    name = "bangbang_safe"

    def __init__(self, k_sigma=2.0, guard_g=0.0, **kw):
        super().__init__(**kw)
        self.k_sigma, self.guard_g = k_sigma, guard_g

    def run(self, rig: Rig, target_g: float) -> str:
        st, _ = self._stage(rig, target_g, Rig_MAX_RPM, self.tau_s,
                            k_sigma=self.k_sigma, stop_g=target_g - self.guard_g)
        if st == "timeout":
            return st
        rig.wait(1.5)
        return "ok"


def trickle_tap(rig: Rig, target_g: float, dt=0.2, tilt=20.0, tau_s=0.30,
                cutoff_margin_g=0.035, max_rate=0.05, kp=250.0, ki=120.0,
                ff_prior=0.35, tap_tilt=0.0, stall_bail_s=8.0,
                k_sigma=1.0) -> str:
    """Seeded rate-PI trickle + predictive cutoff + tap endgame.

    Same decelerating trickle the rate_pi_kf controller lands with, but the KF
    is seeded from the current settled reading so it starts mid-dose (the
    bang-bang bulk has already delivered most of the mass).  The rate set-point
    tapers to zero as the committed-mass prediction approaches target, so the
    hand-off to the tap finish lands within a tap or two -- much softer and more
    powder-robust than a constant slow stage.  Bails to the tap/nudge finish if
    a cohesive powder stalls (no fresh mass for stall_bail_s)."""
    m0 = rig.stable_read()
    kf = MassRateLagKF(dt)
    kf.seed(m0)                              # seed mass + balance state
    rig.set_tilt(tilt)
    rig.wait(0.8)
    integ, rpm, ff, revs = 0.0, 0.0, ff_prior, 0.0
    last_tick, last_m, last_gain_t = -1, m0, rig.t
    while True:
        if rig.timed_out():
            rig.set_rpm(0.0)
            return "timeout"
        rig.wait(dt)
        revs += (rpm / 60.0) * dt
        z, _, tick = rig.read_frame()
        m, r = kf.update(z, rig.actuating(), u_rev_s=rpm / 60.0, ff=ff,
                         fresh=tick != last_tick)
        last_tick = tick
        if revs > 0.3 and m - m0 > 1e-3:
            ff = 0.9 * ff + 0.1 * ((m - m0) / revs)
        # margin adapts to the identified feed factor: a fast powder (high ff)
        # carries more in-flight mass past the cutoff, so stop it earlier.  This
        # keeps the trickle landing SHORT across powders without a per-powder
        # constant; the tap finish closes the rest.
        margin = cutoff_margin_g + 0.06 * max(0.0, ff - 0.30)
        # cutoff biased to the undershoot side by k_sigma * sigma so the tap
        # finish always has a little to add rather than the trickle overshooting
        if m + r * tau_s + k_sigma * kf.pred_sigma(tau_s) >= target_g - margin:
            break
        if m - last_m > 2e-3:
            last_m, last_gain_t = m, rig.t
        elif rig.t - last_gain_t > stall_bail_s:
            break                            # stalled -> let the tap finish try
        remaining = target_g - m
        r_sp = float(np.clip((remaining - margin) / (2.0 * tau_s),
                             0.003, max_rate))
        err = r_sp - r
        integ = float(np.clip(integ + err * dt, -0.5, 0.5))
        # rpm ceiling keeps a fast powder from dumping a slug before the rate
        # estimate catches up (the ramp is where small targets overshoot)
        rpm = float(np.clip(kp * err + ki * integ, 0.0, 45.0))
        rig.set_rpm(rpm)
    rig.set_rpm(0.0)
    rig.wait(1.2)
    # single tap per cycle for the finish: arriving fast leaves a charged lip,
    # so a 2-tap burst can dump a slug past target (overshoot is the hard,
    # asymmetric constraint here -- powder can't be removed).
    return tap_finish(rig, target_g, tap_tilt_deg=tap_tilt, taps_per_cycle=1)


class BangBangTrim(BangBangFF):
    """Iter 4: bang-bang bulk to a safe undershoot, then trim to tolerance.

    Halts the max-rate phase a safe guard below target (with a k*sigma cushion
    from the predictor covariance) so the committed inventory lands short, then
    an incremental fine phase + tap/nudge endgame finishes the last few mg with
    no overshoot.  This is the realistic bang-bang controller: full-speed bulk
    with tolerance-grade accuracy.  Pure bang-bang alone cannot hit +/-5 mg on
    this twin (irreducible ~+/-150 mg spread from rate-estimate noise * tau plus
    slug quantization), so the trim is not optional -- it is where bang-bang
    stops and the proven coarse/fine endgame takes over."""

    name = "bangbang_trim"

    def __init__(self, guard_g=0.30, fast_tau_s=0.10, trickle_tilt=20.0,
                 trim_tilt=0.0, **kw):
        super().__init__(**kw)
        self.guard_g, self.fast_tau_s = guard_g, fast_tau_s
        self.trickle_tilt, self.trim_tilt = trickle_tilt, trim_tilt

    def run(self, rig: Rig, target_g: float) -> str:
        # stage 1 -- fast bang: full rate, halt when the lag-corrected mass
        # reaches target - guard.  The stop is on MEASURED mass (short tau, no
        # sigma bias), so the guard alone -- sized above the worst-case afterflow
        # -- absorbs the committed inventory regardless of powder/flow.  Using
        # r*tau here over-predicts the afterflow at very high flow (the afterflow
        # saturates at the lip+in-flight inventory, it does not keep flowing at
        # r), which made a fast powder stop hundreds of mg short; the precise
        # r*tau predictor is reserved for the low-rate trickle where it is
        # accurate.  Skipped for small targets, which go straight to the trickle.
        if target_g > self.guard_g + 0.10:
            st, _ = self._stage(rig, target_g, Rig_MAX_RPM, self.fast_tau_s,
                                k_sigma=0.0, stop_g=target_g - self.guard_g)
            if st == "timeout":
                return st
            rig.wait(1.0)
        # stage 2+3 -- seeded rate-PI trickle to a soft cutoff, then tap finish
        return trickle_tap(rig, target_g, tilt=self.trickle_tilt,
                           tap_tilt=self.trim_tilt)


# resolved at import: the firmware/twin auger clamp, so "bang" = true max rate
from rig import PowderDoserSim as _Sim  # noqa: E402
Rig_MAX_RPM = _Sim.MAX_AUGER_RPM


BANGBANG_CONTROLLERS = {
    "bangbang_naive": BangBangNaive,
    "bangbang_ff": BangBangFF,
    "bangbang_safe": BangBangSafe,
    "bangbang_trim": BangBangTrim,
}

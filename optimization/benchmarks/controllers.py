"""Candidate dosing controllers benchmarked against the digital twin.

All controllers implement  run(rig, target_g) -> str status  and interact only
through the Rig sensor/actuator surface (noisy balance + own commanded state).

Methods (see PR #124 discussion and the Edison reviews):

* ThreePhase          - firmware baseline: bulk increments / fine increments /
                        tap-until-tolerance (main_three_phase.py defaults).
* ThreePhaseVelocity  - same, but continuous-rotation bulk with anticipation_g
                        (firmware's optional velocity mode).
* RatePIKF            - continuous bulk + rate-PI trickle with predictive
                        cutoff, driven by a 2-state (mass, rate) Kalman filter
                        with regime-switching measurement noise (filterpy).
                        The architecture the Edison MPC follow-up recommended.
* DualUKF             - same skeleton, but an unscented KF additionally
                        estimates the feed factor (g/rev) online as a
                        random-walk parameter (joint state-parameter
                        estimation per the data-assimilation review) and uses
                        it for feedforward speed selection.
* MPCController       - short-horizon constrained linear MPC (cvxpy/OSQP) on
                        the grey-box mass/rate model with a hard m <= target
                        margin constraint, feed factor from an EWMA estimator.

Open-source packages: filterpy (Kalman/UKF), cvxpy+OSQP (MPC QP). BO tuning of
ThreePhase parameters lives in bo_tuning.py (Ax/BoTorch).
"""
from __future__ import annotations

import math

import numpy as np

from rig import Rig

QUIET_SD = 5e-4        # assumed balance noise sd when quiet (g)
NOISY_SD = 8e-3        # assumed sd while actuating (g)
TOL_G = 0.005          # +/- tolerance for "done" (firmware PHASE3_TOLERANCE_G)
LOOKAHEAD_S = 1.2      # balance lag + free fall (excludes lip holdup)


def committed_lookahead_s(tilt_deg: float) -> float:
    """Grey-box latency estimate: powder committed but not yet weighed is
    roughly rate * (lip time-constant + fall + balance lag). The lip drains at
    ~1.2*steepness^2*(1-0.6*coh) per second (calibratable on the bench); we
    assume moderate cohesion since the controller cannot observe it."""
    s = math.sin(math.radians(tilt_deg)) / math.sin(math.radians(45.0))
    drain = max(0.08, 1.2 * s * s * 0.85)
    return min(8.0, 1.0 / drain) + 0.85


# --------------------------------------------------------------------------
# Shared endgame: tap-until-tolerance (all methods finish the last mg here)
# --------------------------------------------------------------------------

def tap_finish(rig: Rig, target_g: float, tol_g: float = TOL_G,
               tap_tilt_deg: float = 0.0, taps_per_cycle: int = 2,
               settle_s: float = 1.2, max_cycles: int = 120,
               nudge_deg: float = 5.0, max_nudges: int = 20) -> str:
    """Firmware phase-3 logic: tap bursts, settle, stable measure; nudge the
    auger a few degrees when the lip runs empty."""
    rig.set_rpm(0.0)
    rig.set_tilt(tap_tilt_deg)
    rig.wait(0.8)
    stall, nudges = 0, 0
    prev = rig.stable_read()
    for _ in range(max_cycles):
        remaining = target_g - prev
        if remaining <= tol_g:
            return "ok" if remaining >= -tol_g else "overshoot_abort"
        if rig.timed_out():
            return "timeout"
        n = taps_per_cycle if remaining > 0.02 else 1
        rig.tap(n)
        rig.wait(settle_s)
        grams = rig.stable_read()
        if grams - prev < 2e-4:
            stall += 1
            if stall >= 3:
                if nudges >= max_nudges:
                    return "stalled"
                rig.rotate_deg(nudge_deg, 10.0)
                rig.wait(settle_s)
                nudges += 1
                stall = 0
        else:
            stall = 0
        prev = grams
    return "stalled"


# --------------------------------------------------------------------------
# 1-2: firmware three-phase baseline (incremental and velocity-bulk variants)
# --------------------------------------------------------------------------

class ThreePhase:
    """Deterministic three-phase policy, defaults from main_three_phase.py.
    Parameters are exposed so BO (bo_tuning.py) can tune the same controller."""

    name = "three_phase"

    def __init__(self, t1_g=0.5, t2_g=0.05, bulk_tilt=45.0, bulk_rot_deg=360.0,
                 bulk_rpm=55.0, bulk_settle_s=0.8, fine_tilt=22.5,
                 fine_rot_deg=30.0, fine_rpm=30.0, fine_settle_s=1.5,
                 tap_tilt=0.0, taps_per_cycle=2, tap_settle_s=1.2,
                 velocity_bulk=False, anticipation_g=0.10, poll_s=0.25):
        self.p = dict(t1_g=t1_g, t2_g=t2_g, bulk_tilt=bulk_tilt,
                      bulk_rot_deg=bulk_rot_deg, bulk_rpm=bulk_rpm,
                      bulk_settle_s=bulk_settle_s, fine_tilt=fine_tilt,
                      fine_rot_deg=fine_rot_deg, fine_rpm=fine_rpm,
                      fine_settle_s=fine_settle_s, tap_tilt=tap_tilt,
                      taps_per_cycle=int(round(taps_per_cycle)),
                      tap_settle_s=tap_settle_s, velocity_bulk=velocity_bulk,
                      anticipation_g=anticipation_g, poll_s=poll_s)

    def run(self, rig: Rig, target_g: float) -> str:
        p = self.p
        # --- phase 1: bulk ---
        if target_g > p["t1_g"]:
            rig.set_tilt(p["bulk_tilt"])
            rig.wait(0.8)
            if p["velocity_bulk"]:
                rig.set_rpm(p["bulk_rpm"])
                halt_at = p["t1_g"] + p["anticipation_g"]
                while True:
                    rig.wait(p["poll_s"])
                    grams, _ = rig.read()
                    if target_g - grams <= halt_at or rig.timed_out():
                        break
                rig.set_rpm(0.0)
                rig.wait(p["bulk_settle_s"])
            else:
                stall, prev = 0, rig.stable_read()
                while target_g - prev > p["t1_g"]:
                    if rig.timed_out():
                        return "timeout"
                    rig.rotate_deg(p["bulk_rot_deg"], p["bulk_rpm"])
                    rig.wait(p["bulk_settle_s"])
                    grams = rig.stable_read()
                    stall = stall + 1 if grams - prev < 2e-4 else 0
                    if stall >= 5:
                        return "stalled"
                    prev = grams
        # --- phase 2: fine increments ---
        rig.set_rpm(0.0)
        rig.set_tilt(p["fine_tilt"])
        rig.wait(0.8)
        stall, prev = 0, rig.stable_read()
        while target_g - prev > p["t2_g"]:
            if rig.timed_out():
                return "timeout"
            rig.rotate_deg(p["fine_rot_deg"], p["fine_rpm"])
            rig.wait(p["fine_settle_s"])
            grams = rig.stable_read()
            stall = stall + 1 if grams - prev < 2e-4 else 0
            if stall >= 8:
                break  # let the tap phase try to finish
            prev = grams
        # --- phase 3: taps ---
        return tap_finish(rig, target_g, tap_tilt_deg=p["tap_tilt"],
                          taps_per_cycle=p["taps_per_cycle"],
                          settle_s=p["tap_settle_s"])


class ThreePhaseVelocity(ThreePhase):
    name = "three_phase_vel"

    def __init__(self, **kw):
        kw.setdefault("velocity_bulk", True)
        super().__init__(**kw)


# --------------------------------------------------------------------------
# Switching-covariance Kalman filter on the balance signal (filterpy)
# --------------------------------------------------------------------------

class MassRateKF:
    """2-state (mass, rate) KF with regime-switching R - the estimator the
    Edison MPC follow-up and data-assimilation critique both recommend."""

    RATE_TAU_S = 0.5  # assumed first-order lag rate <- ff * commanded rev/s

    def __init__(self, dt: float):
        from filterpy.kalman import KalmanFilter
        from filterpy.common import Q_discrete_white_noise
        self.kf = KalmanFilter(dim_x=2, dim_z=1)
        self.kf.x = np.zeros((2, 1))
        self.a = min(1.0, dt / self.RATE_TAU_S)
        self.kf.F = np.array([[1.0, dt], [0.0, 1.0 - self.a]])
        self.kf.H = np.array([[1.0, 0.0]])
        self.kf.P *= 0.05
        self.kf.Q = Q_discrete_white_noise(dim=2, dt=dt, var=2e-4)
        self.dt = dt

    def update(self, z: float, noisy: bool, u_rev_s: float = None,
               ff: float = None, fresh: bool = True) -> tuple[float, float]:
        """u_rev_s + ff: optional control-input model so the estimate does not
        lag a commanded ramp (input-blind KF is badly biased during spin-up).
        fresh=False (a held balance sample) runs predict only: repeating the
        measurement update on a held frame would treat one observation as
        independent replicated evidence (methods-check A)."""
        self.kf.R = np.array([[(NOISY_SD if noisy else QUIET_SD) ** 2]])
        if u_rev_s is None:
            self.kf.F[1, 1] = 1.0   # input-blind: constant-rate model
            self.kf.predict()
        else:
            self.kf.F[1, 1] = 1.0 - self.a
            self.kf.predict(u=np.array([[u_rev_s]]),
                            B=np.array([[0.0], [self.a * (ff or 0.3)]]))
        if fresh:
            self.kf.update(np.array([[z]]))
        # powder only accumulates; clamp a negative rate estimate
        self.kf.x[1, 0] = max(0.0, self.kf.x[1, 0])
        return float(self.kf.x[0, 0]), float(self.kf.x[1, 0])


class RatePIKF:
    """Continuous bulk + rate-PI trickle with predictive cutoff on KF state."""

    name = "rate_pi_kf"

    def __init__(self, dt=0.2, bulk_rate=0.12, bulk_tilt=40.0, trickle_tilt=20.0,
                 trickle_tau_s=5.0, cutoff_margin_g=0.018, kp=250.0, ki=120.0,
                 handoff_g=0.02):
        self.dt, self.bulk_rate = dt, bulk_rate
        self.bulk_tilt, self.trickle_tilt = bulk_tilt, trickle_tilt
        self.trickle_tau_s, self.cutoff_margin_g = trickle_tau_s, cutoff_margin_g
        self.kp, self.ki, self.handoff_g = kp, ki, handoff_g

    def run(self, rig: Rig, target_g: float) -> str:
        kf = MassRateKF(self.dt)
        tilt = self.bulk_tilt if target_g > 0.5 else self.trickle_tilt
        rig.set_tilt(tilt)
        rig.wait(0.8)
        integ, rpm, ff, revs = 0.0, 0.0, 0.35, 0.0
        last_tick = -1
        L_tr = committed_lookahead_s(self.trickle_tilt)
        while True:
            if rig.timed_out():
                rig.set_rpm(0.0)
                return "timeout"
            rig.wait(self.dt)
            revs += (rpm / 60.0) * self.dt
            z, _, tick = rig.read_frame()
            m, r = kf.update(z, rig.actuating(), u_rev_s=rpm / 60.0, ff=ff,
                             fresh=tick != last_tick)
            last_tick = tick
            if revs > 0.3 and m > 1e-3:
                ff = 0.9 * ff + 0.1 * (m / revs)
            remaining = target_g - m
            # taper against the *trickle* lookahead so the rate is already low
            # before the shallow-tilt regime slows the lip drain
            r_sp = float(np.clip((remaining - self.cutoff_margin_g) / (2.0 * L_tr),
                                 0.003, self.bulk_rate))
            if remaining < 0.5 and tilt != self.trickle_tilt:
                tilt = self.trickle_tilt
                rig.set_tilt(tilt)
            # predictive cutoff on committed mass (lip + in-flight + lag)
            if m + r * committed_lookahead_s(tilt) >= target_g - self.cutoff_margin_g:
                break
            err = r_sp - r
            integ = float(np.clip(integ + err * self.dt, -0.5, 0.5))
            rpm = float(np.clip(self.kp * err + self.ki * integ, 0.0, 100.0))
            rig.set_rpm(rpm)
            rpm = rpm  # commanded value used for next KF predict
        rig.set_rpm(0.0)
        rig.wait(1.5)
        return tap_finish(rig, target_g)


# --------------------------------------------------------------------------
# Dual UKF# --------------------------------------------------------------------------
# Dual UKF: joint state + feed-factor estimation (filterpy UKF)
# --------------------------------------------------------------------------

class DualUKF:
    """UKF over [mass, rate, feed_factor]; commanded rev/s enters the process
    model, so the feed factor is identified online and used as feedforward."""

    name = "dual_ukf"

    def __init__(self, dt=0.2, bulk_rate=0.12, bulk_tilt=40.0, trickle_tilt=20.0,
                 trickle_tau_s=5.0, cutoff_margin_g=0.018, ff_prior=0.30):
        self.dt, self.bulk_rate = dt, bulk_rate
        self.bulk_tilt, self.trickle_tilt = bulk_tilt, trickle_tilt
        self.trickle_tau_s, self.cutoff_margin_g = trickle_tau_s, cutoff_margin_g
        self.ff_prior = ff_prior

    def run(self, rig: Rig, target_g: float) -> str:
        from filterpy.kalman import MerweScaledSigmaPoints, UnscentedKalmanFilter
        dt = self.dt
        self._u = 0.0  # commanded rev/s, read by fx

        def fx(x, dt_):
            m, r, ff = x
            r_cmd = max(0.0, ff) * self._u
            r_next = r + min(1.0, dt_ / 0.5) * (r_cmd - r)
            return np.array([m + r * dt_, max(0.0, r_next), max(0.01, ff)])

        def hx(x):
            return x[:1]

        pts = MerweScaledSigmaPoints(3, alpha=0.3, beta=2.0, kappa=0.0)
        ukf = UnscentedKalmanFilter(dim_x=3, dim_z=1, dt=dt, fx=fx, hx=hx,
                                    points=pts)
        ukf.x = np.array([0.0, 0.0, self.ff_prior])
        ukf.P = np.diag([1e-4, 1e-4, 0.04])
        ukf.Q = np.diag([1e-8, 4e-5, 4e-5 * dt])

        tilt = self.bulk_tilt if target_g > 0.5 else self.trickle_tilt
        rig.set_tilt(tilt)
        rig.wait(0.8)
        L_tr = committed_lookahead_s(self.trickle_tilt)
        last_tick = -1
        while True:
            if rig.timed_out():
                rig.set_rpm(0.0)
                return "timeout"
            rig.wait(dt)
            z, _, tick = rig.read_frame()
            ukf.R = np.array([[(NOISY_SD if rig.actuating() else QUIET_SD) ** 2]])
            ukf.predict()
            if tick != last_tick:   # held frame -> no measurement update
                ukf.update(np.array([z]))
            last_tick = tick
            m, r, ff = ukf.x
            ff = float(np.clip(ff, 0.10, 1.5))
            ukf.x[2] = ff
            remaining = target_g - m
            r_sp = float(np.clip((remaining - self.cutoff_margin_g) / (2.0 * L_tr),
                                 0.003, self.bulk_rate))
            if remaining < 0.5 and tilt != self.trickle_tilt:
                tilt = self.trickle_tilt
                rig.set_tilt(tilt)
            if m + r * committed_lookahead_s(tilt) >= target_g - self.cutoff_margin_g:
                break
            # feedforward from the identified feed factor (+ small P correction)
            u = r_sp / ff + 0.5 * (r_sp - r) / ff
            u_max = (60.0 if remaining > 0.1 else 25.0) / 60.0
            self._u = float(np.clip(u, 0.0, u_max))
            rig.set_rpm(self._u * 60.0)
        rig.set_rpm(0.0)
        self._u = 0.0
        rig.wait(1.0)
        return tap_finish(rig, target_g)


# --------------------------------------------------------------------------
# Short-horizon constrained MPC (cvxpy / OSQP)
# --------------------------------------------------------------------------

class MPCController:
    """Linear MPC on the grey-box model  m+ = m + r*dt ;  r+ = r + a(ff*u - r)
    with the committed-mass CUTOFF HEURISTIC  m_k + L*r_k <= target - margin
    at every predicted step. Per the methods-check review this is not a hard
    no-overshoot guarantee (hidden screw/lip inventory is unmodelled), so it
    is a soft constraint with an exact L1 slack penalty - a hard version goes
    infeasible whenever the estimate already violates the bound, which made
    solver failures indistinguishable from deliberate zero commands.  Slack
    activations and failed solves are counted (slack_uses / bad_solves).
    Feed factor via EWMA; state from the switching-R KF."""

    name = "mpc"

    def __init__(self, dt=0.25, horizon=16, margin_g=0.022, ff_prior=0.45,
                 bulk_tilt=40.0, trickle_tilt=20.0, w_track=1.0, w_u=2e-4,
                 w_du=0.05, du_max=0.15, handoff_g=0.02):
        import cvxpy as cp
        self.dt, self.N, self.margin_g = dt, horizon, margin_g
        self.ff_prior, self.handoff_g = ff_prior, handoff_g
        self.bulk_tilt, self.trickle_tilt = bulk_tilt, trickle_tilt
        a = min(1.0, dt / 0.5)
        u = cp.Variable(self.N, nonneg=True)
        m = cp.Variable(self.N + 1)
        r = cp.Variable(self.N + 1)
        self._m0 = cp.Parameter()
        self._r0 = cp.Parameter()
        self._ff = cp.Parameter(nonneg=True)
        self._tgt = cp.Parameter()
        self._budget = cp.Parameter()   # grams of conveyable input left
        self._uprev = cp.Parameter()
        self._L = cp.Parameter(nonneg=True)   # committed-mass lookahead (s)
        self._rcap = cp.Parameter()   # bulk-rate cap: bounds lip holdup bias
        cons = [m[0] == self._m0, r[0] == self._r0, u <= 60.0 / 60.0,
                cp.abs(u[0] - self._uprev) <= du_max, r[1:] <= self._rcap]
        for k in range(self.N):
            cons += [m[k + 1] == m[k] + r[k] * dt,
                     r[k + 1] == r[k] + a * (self._ff * u[k] - r[k])]
            if k:
                cons += [cp.abs(u[k] - u[k - 1]) <= du_max]
        # committed-mass cutoff heuristic, SOFT with an exact/L1 slack penalty
        # (actuator + slew bounds stay hard); plus a volumetric future-input
        # budget: what the screw may convey at an upper-bound feed factor
        # cannot exceed the estimated remaining mass (guards blind feeding
        # while the balance signal stalls, e.g. arching)
        slack = cp.Variable(self.N + 1, nonneg=True)
        cons += [m + cp.multiply(self._L, r) <= self._tgt + slack]
        self._ffhi = cp.Parameter(nonneg=True)
        cons += [self._ffhi * dt * cp.cumsum(u) <= self._budget]
        cost = (w_track * cp.sum_squares(self._tgt - m[1:])
                + w_u * cp.sum_squares(u)
                + w_du * cp.sum_squares(cp.diff(u))
                + 1e3 * cp.sum(slack))          # exact penalty weight
        self._prob = cp.Problem(cp.Minimize(cost), cons)
        self._uvar = u
        self._slack = slack
        self.slack_uses = 0     # solves where the soft constraint was active
        self.bad_solves = 0     # solver exceptions / no solution returned

    def run(self, rig: Rig, target_g: float) -> str:
        kf = MassRateKF(self.dt)
        ff, ff_n = self.ff_prior, 1.0
        rig.set_tilt(self.bulk_tilt if target_g > 0.5 else self.trickle_tilt)
        rig.wait(0.8)
        u_cmd, revs, last_tick = 0.0, 0.0, -1
        tilt = self.bulk_tilt if target_g > 0.5 else self.trickle_tilt
        while True:
            if rig.timed_out():
                rig.set_rpm(0.0)
                return "timeout"
            rig.wait(self.dt)
            revs += u_cmd * self.dt
            z, _, tick = rig.read_frame()
            m, r = kf.update(z, rig.actuating(), u_rev_s=u_cmd, ff=ff,
                             fresh=tick != last_tick)
            last_tick = tick
            L = committed_lookahead_s(tilt)
            if revs > 0.4 and m > 0.03:              # EWMA feed-factor update,
                corr = min(r * L, 0.6 * m)           # committed-mass correction,
                ff_obs = (m + corr) / revs           # bounded so an early rate
                w = min(0.10, 1.0 / (ff_n + 1.0))    # spike cannot blow it up
                ff = max((1.0 - w) * ff + w * ff_obs, 0.5 * ff)
                ff_n += 1.0
            remaining = target_g - m
            if (m + r * L >= target_g - self.margin_g - self.handoff_g
                    and r < 0.005 and u_cmd < 1e-3):
                break
            if remaining < 0.5:
                tilt = self.trickle_tilt
                rig.set_tilt(tilt)
            self._m0.value, self._r0.value = m, r
            self._ff.value = max(0.02, ff)
            self._tgt.value = target_g - self.margin_g
            # future-input budget: what the screw may still convey (at an
            # upper-bound ff) is capped by the estimated remaining mass; the
            # prior stops binding once the online estimate has converged
            ff_hi = 1.3 * ff if ff_n >= 8 else max(1.3 * ff, self.ff_prior)
            self._ffhi.value = ff_hi
            corr = min(r * L, 0.6 * max(m, 1e-6))
            self._budget.value = max(0.0, (target_g - self.margin_g) - m - corr)
            self._uprev.value = u_cmd
            self._L.value = L
            self._rcap.value = max(0.12, 0.6 * r)
            try:
                self._prob.solve(solver="OSQP", warm_start=True)
                if self._uvar.value is None:
                    raise RuntimeError(self._prob.status)
                u_cmd = float(max(0.0, self._uvar.value[0]))
                if self._slack.value is not None and \
                        float(np.max(self._slack.value)) > 1e-6:
                    self.slack_uses += 1
            except Exception:
                self.bad_solves += 1
                u_cmd = 0.0                           # fail safe: stop feeding
            rig.set_rpm(u_cmd * 60.0)
        rig.set_rpm(0.0)
        rig.wait(1.0)
        return tap_finish(rig, target_g)


ALL_CONTROLLERS = {
    "three_phase": ThreePhase,
    "three_phase_vel": ThreePhaseVelocity,
    "rate_pi_kf": RatePIKF,
    "dual_ukf": DualUKF,
    "mpc": MPCController,
}

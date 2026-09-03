"""Estimators shared by the trim methods (issue #153).

Two things live here:

``MassRateLagKF``
    The 3-state ``[mass, rate, balance]`` Kalman filter that PR #124's
    ``bangbang.py`` uses, reimplemented in plain numpy so this study does not
    depend on ``filterpy``.  It is the *rate-based* worldview: estimate a
    continuous flow and predict forward with ``m + r * tau``.

``YieldModel``
    The *increment-based* worldview.  It never estimates a rate.  It identifies
    the settled mass delivered per commanded auger revolution and the dispersion
    of that delivery, then answers the only question the trim endgame actually
    needs: *what is the largest command whose upper mass quantile still fits the
    remaining one-sided budget?*

The split is deliberate.  The 2026-08-22 Edison spot-check made the point that
near target the delivery is a marked point process, so a rate is a poor summary
of it; but it also made the point that afterflow, free fall, screw discharge and
estimator error "need not be separately identifiable for a robust cutoff
predictor" -- calibrate the *total post-command settled mass* and take its upper
conditional quantile.  ``YieldModel`` is that recommendation implemented.
"""
from __future__ import annotations

import math

import numpy as np

from trim_sim import NOISY_SD_G, QUIET_SD_G

__all__ = ["MassRateLagKF", "YieldModel", "TapYieldModel",
           "compound_poisson_exceedance", "lognormal_exceedance"]


# ---------------------------------------------------------------------------
# Rate-based estimator (the PI/PID worldview)
# ---------------------------------------------------------------------------

class MassRateLagKF:
    """3-state KF over ``x = [m, r, b]`` observing only the balance ``b``.

    ``m`` is true cup mass, ``r`` its rate, ``b`` the lagged pan reading with
    ``b' = (m - b) / tau_bal``.  Because the balance is the only measurement,
    the filter's ``m`` is a *model-based estimate of current mass* -- it is only
    lag-free to the extent ``tau_bal`` is right, which is exactly the
    sensitivity the study sweeps.
    """

    RATE_TAU_S = 0.5     # how fast the delivery rate relaxes toward ff * u

    def __init__(self, dt: float, tau_bal_s: float = 0.7):
        self.dt = dt
        self.a = min(1.0, dt / self.RATE_TAU_S)
        self.beta = 1.0 - math.exp(-dt / max(1e-3, tau_bal_s))
        self.F = np.array([[1.0, dt, 0.0],
                           [0.0, 1.0 - self.a, 0.0],
                           [self.beta, 0.0, 1.0 - self.beta]])
        self.H = np.array([[0.0, 0.0, 1.0]])
        self.x = np.zeros((3, 1))
        self.P = np.diag([0.05, 0.05, 0.05])
        # Piecewise-white-noise Q on (m, r); the balance state is nearly
        # deterministic given m.
        var = 2e-4
        self.Q = np.array([[0.25 * dt ** 4 * var, 0.5 * dt ** 3 * var, 0.0],
                           [0.5 * dt ** 3 * var, dt ** 2 * var, 0.0],
                           [0.0, 0.0, 1e-8]])
        self.clamp_hits = 0      # how often the r >= 0 projection fired

    def seed(self, mass_g: float) -> None:
        self.x[0, 0] = mass_g
        self.x[2, 0] = mass_g

    def update(self, z: float, noisy: bool, u_rev_s: float | None = None,
               ff: float = 0.3, fresh: bool = True) -> tuple[float, float]:
        if u_rev_s is None:
            self.F[1, 1] = 1.0
            self.x = self.F @ self.x
        else:
            self.F[1, 1] = 1.0 - self.a
            B = np.array([[0.0], [self.a * ff], [0.0]])
            self.x = self.F @ self.x + B * u_rev_s
        self.P = self.F @ self.P @ self.F.T + self.Q

        if fresh:
            R = np.array([[(NOISY_SD_G if noisy else QUIET_SD_G) ** 2]])
            S = self.H @ self.P @ self.H.T + R
            K = self.P @ self.H.T @ np.linalg.inv(S)
            y = np.array([[z]]) - self.H @ self.x
            self.x = self.x + K @ y
            self.P = (np.eye(3) - K @ self.H) @ self.P

        # Non-negativity projection on the rate.  NOTE: this leaves the
        # mean/covariance pair inconsistent -- P is not corrected -- so
        # pred_sigma() is miscalibrated whenever the clamp is active.  The
        # Edison spot-check flagged exactly this; we keep the behaviour (it is
        # what the deployed controller does) but count it so the study can
        # report how often the sigma-based margin is unreliable.
        if self.x[1, 0] < 0.0:
            self.x[1, 0] = 0.0
            self.clamp_hits += 1
        return float(self.x[0, 0]), float(self.x[1, 0])

    def pred_sigma(self, tau_s: float) -> float:
        """sd of the committed-mass prediction ``m + r * tau``."""
        var = (self.P[0, 0] + tau_s ** 2 * self.P[1, 1]
               + 2 * tau_s * self.P[0, 1])
        return float(math.sqrt(max(var, 0.0)))


# ---------------------------------------------------------------------------
# Increment-based estimator (the chance-constrained worldview)
# ---------------------------------------------------------------------------

def _gammq(a: float, x: float) -> float:
    """Regularized upper incomplete gamma Q(a, x) = 1 - P(a, x).

    Series expansion below the crossover, continued fraction above (the
    standard Numerical Recipes split).  Written out rather than pulled from
    scipy so this study depends only on numpy.
    """
    if x < 0.0 or a <= 0.0:
        raise ValueError("gammq domain")
    if x == 0.0:
        return 1.0
    gln = math.lgamma(a)
    if x < a + 1.0:                       # series for P(a, x)
        ap, total, delta = a, 1.0 / a, 1.0 / a
        for _ in range(500):
            ap += 1.0
            delta *= x / ap
            total += delta
            if abs(delta) < abs(total) * 1e-12:
                break
        return 1.0 - total * math.exp(-x + a * math.log(x) - gln)
    # continued fraction for Q(a, x) (modified Lentz)
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    return h * math.exp(-x + a * math.log(x) - gln)


def compound_poisson_exceedance(lam: float, mu_s: float, cv_s: float,
                                threshold: float, k_max: int = 200) -> float:
    """P(Y > threshold) for Y = sum of N iid marks, N ~ Poisson(lam).

    The marks have mean ``mu_s`` and coefficient of variation ``cv_s``.  The
    sum of ``k`` marks is approximated by the Gamma with matched first two
    moments, which is exact when the marks are themselves Gamma and accurate in
    the right tail otherwise.  The ``k = 0`` term contributes nothing for a
    positive threshold, which is what gives this distribution its atom at zero
    -- the ~14 % chance of no event that a Normal approximation cannot express.
    """
    if threshold <= 0.0:
        return 1.0 if lam > 0.0 else 0.0
    if lam <= 0.0 or mu_s <= 0.0:
        return 0.0
    shape1 = 1.0 / max(1e-9, cv_s ** 2)      # Gamma shape of one mark
    scale = mu_s * cv_s ** 2                 # Gamma scale of one mark
    # Poisson terms, walking out from the mode so truncation is symmetric.
    total = 0.0
    log_lam = math.log(lam)
    upper = int(min(k_max, max(10, lam + 10.0 * math.sqrt(lam) + 10)))
    for k in range(1, upper + 1):
        log_pk = -lam + k * log_lam - math.lgamma(k + 1)
        if log_pk < -40.0 and k > lam:
            break
        total += math.exp(log_pk) * _gammq(shape1 * k, threshold / scale)
    return min(1.0, total)


def lognormal_exceedance(mean: float, cv: float, threshold: float) -> float:
    """P(X > threshold) for a lognormal with the given mean and CV."""
    if threshold <= 0.0:
        return 1.0
    if mean <= 0.0:
        return 0.0
    sigma2 = math.log(1.0 + cv ** 2)
    mu = math.log(mean) - 0.5 * sigma2
    z = (math.log(threshold) - mu) / math.sqrt(sigma2)
    return 0.5 * math.erfc(z / math.sqrt(2.0))


class YieldModel:
    """Committed-mass model for the increment endgame.

    The naive version of this -- predict each increment's yield independently
    from ``g * n``, fit ``g`` by EWMA on per-step yields -- fails on the real
    plant, and it fails in the direction that scraps doses.  Two coupled
    reasons, both worth stating because they are properties of the rig and not
    of any particular controller:

    1.  **The lip is a hidden integrator.**  Powder commanded out of the screw
        lands on the lip and stays there until the charge exceeds what the lip
        retains, then leaves as one avalanche.  So a sequence of small commands
        can each weigh as ~0 mg and then a later one delivers everything banked.
        Per-step prediction has no term for the banked mass and is therefore
        violated exactly when it matters.
    2.  **Zero-yield steps corrupt a per-step ``g``.**  Each 0 mg observation
        pulls the EWMA down, which makes the model believe a revolution
        delivers less, which makes the *next commanded increment larger* -- a
        positive feedback straight into the avalanche.

    So this model is written on the conserved quantity instead.  It tracks
    cumulative commanded revolutions ``N`` and cumulative settled mass ``M``,
    and splits the total into what has arrived and what is still in the system::

        committed = g * N              all mass the screw has metered out
        pending   = max(0, g*N - M)    metered but not yet weighed (lip + flight)

    The quantity a stopping rule has to bound is not the next increment's yield
    but **everything that could still arrive**: ``pending`` plus the new
    command's delivery.  Both are compound-Poisson, so::

        E[total]   = pending + g*n
        Var[total] = (pending + g*n) * mu_s * (1 + cv_s^2) + s0^2

    This is the same "committed mass" idea the bang-bang cutoff uses, but
    computed from commanded revolutions and at-rest weighings rather than from a
    differentiated balance signal -- so it needs no rate estimate and no
    ``tau_bal``.

    ``g`` is identified by cumulative regression ``M / N`` shrunk toward the
    bench prior, which is insensitive to the burstiness that destroys the
    per-step estimator.  The dispersion ``(mu_s, cv_s)`` is held at the bench
    prior: with a handful of increments per dose there is nowhere near enough
    data to identify a variance, and under a one-sided constraint an
    underestimated variance is the failure that costs a dose.
    """

    def __init__(self, g_prior: float = 0.113, mu_s_g: float = 6.4e-3,
                 cv_s: float = 2.48, prior_strength_rev: float = 0.5,
                 trigger_risk: float = 0.5):
        self.g_prior = g_prior
        self.g = g_prior
        self.mu_s = mu_s_g
        self.cv_s = cv_s
        self.prior_rev = prior_strength_rev
        # Any auger command, however small, can dislodge a charged lip and
        # release one full slug.  So the predictive variance does NOT go to zero
        # as the command goes to zero: it has a floor of one slug's second
        # moment.  ``trigger_risk`` is the expected number of such
        # command-triggered slugs, i.e. 1.0 = "assume every command can set one
        # off".  This floor is the whole reason a fine endgame cannot be reached
        # by making the auger step smaller: the quantum, not the command, sets
        # the achievable tolerance.
        #
        # 0.5 is calibrated so the model's p95 for a vanishingly small command
        # (19.5 mg) matches what the plant delivers for a 5 deg salt command
        # (17.7 mg).  On hardware this is the one number that most needs a bench
        # measurement: command many tiny increments at the trim tilt and record
        # the yield distribution INCLUDING the zeros.
        self.trigger_risk = trigger_risk
        self.n_cmd_rev = 0.0          # cumulative commanded revolutions
        self.m_landed_g = 0.0         # cumulative settled mass since trim start
        self.n_obs = 0

    @property
    def slug_second_moment(self) -> float:
        return (self.mu_s ** 2) * (1.0 + self.cv_s ** 2)

    # -- state --
    @property
    def holdup_g(self) -> float:
        """Commanded-but-never-weighed mass: the lip's retained charge.

        Diagnostic only.  It is deliberately NOT part of the risk model: after a
        full settle the *excess* charge has already drained, and what is left is
        retained until something disturbs it.  The risk of that disturbance is
        carried by ``trigger_risk`` instead, which is directly measurable
        (command many tiny increments, record the yield distribution) whereas
        the split between "the lip is holding X" and "g is lower than I thought"
        is not identifiable from cumulative totals alone.
        """
        return max(0.0, self.g_prior * self.n_cmd_rev - self.m_landed_g)

    # -- prediction --
    def mean(self, n_rev: float) -> float:
        """Expected settled mass from a command of ``n_rev`` revolutions."""
        m = self.g * max(0.0, n_rev)
        if n_rev > 0.0:
            m += self.trigger_risk * self.mu_s
        return m

    def _lam(self, n_rev: float) -> float:
        """Expected number of release events still to come."""
        return self.mean(n_rev) / max(1e-9, self.mu_s)

    def exceedance(self, n_rev: float, budget_g: float) -> float:
        """P(total still-to-arrive mass > budget) for a command of ``n_rev``."""
        return compound_poisson_exceedance(self._lam(n_rev), self.mu_s,
                                           self.cv_s, budget_g)

    def slug_exceedance(self, budget_g: float) -> float:
        """P(a single command-triggered slug alone exceeds ``budget_g``).

        The hard floor on what any auger endgame can achieve.  When this is
        already above the risk budget, no commanded increment is safe at any
        size -- the *quantum*, not the command resolution, is what limits the
        achievable tolerance, and closing the gap is a hardware change.
        """
        return compound_poisson_exceedance(self.trigger_risk, self.mu_s,
                                           self.cv_s, budget_g)

    def largest_safe_rev(self, budget_g: float, alpha: float,
                         n_max: float = 3.0) -> float:
        """Largest command with ``P(overshoot) <= alpha``.

        Monotone in ``n_rev``, so bisection is exact to tolerance.  Returns 0.0
        when no command is safe -- including the case where ``pending`` or the
        slug quantum alone already blows the budget, which is the model telling
        the controller to stop rather than nudge again.
        """
        if budget_g <= 0.0:
            return 0.0
        if self.exceedance(1e-9, budget_g) > alpha:
            return 0.0
        if self.exceedance(n_max, budget_g) <= alpha:
            return n_max
        lo, hi = 0.0, n_max
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            if self.exceedance(mid, budget_g) <= alpha:
                lo = mid
            else:
                hi = mid
        return lo

    # -- identification --
    def observe(self, n_rev: float, delivered_g: float) -> None:
        """Fold in one (command, settled delta) pair.

        Only the cumulative totals are updated, so a zero-yield step is recorded
        as "this much was commanded and has not arrived yet" rather than as
        evidence that revolutions deliver nothing.
        """
        if n_rev <= 1e-9:
            return
        self.n_obs += 1
        self.n_cmd_rev += n_rev
        self.m_landed_g += max(0.0, delivered_g)
        # Cumulative-regression estimate of settled g/rev, shrunk toward the
        # bench prior by prior_rev "virtual revolutions" so the first one or two
        # increments cannot move it far.
        self.g = ((self.m_landed_g + self.prior_rev * self.g_prior)
                  / (self.n_cmd_rev + self.prior_rev))
        # Never let the identified yield fall so low that the sizing rule starts
        # asking for huge commands; the floor is well below any real powder.
        self.g = max(0.2 * self.g_prior, self.g)


class TapYieldModel:
    """Yield of a single solenoid tap, as a lognormal fitted online.

    A tap is not a protective action: it cannot remove mass, and in the PR #124
    diagnostic taps caused roughly half of all strict overshoots.  So it gets
    the same treatment as an auger command -- it fires only when its own
    exceedance probability against the remaining budget is under the risk
    budget.
    """

    def __init__(self, mean_g: float = 6.5e-3, cv: float = 1.1):
        self.mean = mean_g
        self.cv = cv
        self.n_obs = 0

    def exceedance(self, budget_g: float) -> float:
        return lognormal_exceedance(self.mean, self.cv, budget_g)

    def observe(self, delivered_g: float) -> None:
        self.n_obs += 1
        a = 0.4 if self.n_obs > 1 else 0.7
        # Only ratchet the estimate down slowly; a single zero-yield tap must
        # not convince the model that taps are harmless.
        self.mean = max(5e-4, (1.0 - a) * self.mean + a * max(0.0, delivered_g))

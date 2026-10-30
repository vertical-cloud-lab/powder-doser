"""3-state mass/rate/balance Kalman filter in pure Python (no numpy).

A line-for-line port of ``optimization/trim/estimators.MassRateLagKF``
(itself derived from ``optimization/benchmarks/bangbang.MassRateLagKF``,
the twin's deployed trickle estimator) to plain floats and 3x3 lists so
it runs under MicroPython on the Pico.  The CPython test
``sim/test_trickle_tap.py`` drives this and the numpy original with the
same input trace and requires the outputs to agree to 1e-9 -- the
"identical outputs" acceptance criterion from docs/trim-bench-plan.md
section 4.

State ``x = [m, r, b]``: true cup mass, delivery rate, and the *lagged*
pan reading, with ``b' = (m - b) / tau_bal``.  The balance measures b,
not m, so the filter's m is lag-free exactly to the extent the
``tau_bal_s`` belief is right (bench-plan test A1 pins it).

One hardware addition over the original: ``update(..., dt=...)`` may
pass the MEASURED interval since the previous update, and the model
matrices are rebuilt for it.  On the Pico the loop period is the
commanded sleep plus serial latency, so assuming a fixed dt would bias
the rate integration; with dt omitted the constructor's fixed value is
used and the filter is bit-identical to the original.
"""

import math


def _mat33_mul(A, B):
    return [[A[i][0] * B[0][j] + A[i][1] * B[1][j] + A[i][2] * B[2][j]
             for j in range(3)] for i in range(3)]


def _mat33_mul_t(A, B):
    """A @ B.T for 3x3 lists."""
    return [[A[i][0] * B[j][0] + A[i][1] * B[j][1] + A[i][2] * B[j][2]
             for j in range(3)] for i in range(3)]


class TrickleKF:

    def __init__(self, dt, tau_bal_s=0.7, rate_tau_s=0.5, q_var=2e-4,
                 quiet_sd_g=5e-4, noisy_sd_g=8e-3):
        self.tau_bal_s = tau_bal_s
        self.rate_tau_s = rate_tau_s
        self.q_var = q_var
        self.quiet_sd = quiet_sd_g
        self.noisy_sd = noisy_sd_g
        self.x = [0.0, 0.0, 0.0]              # m, r, b
        self.P = [[0.05, 0.0, 0.0],
                  [0.0, 0.05, 0.0],
                  [0.0, 0.0, 0.05]]
        self.clamp_hits = 0                   # r >= 0 projection count
        self._dt = None
        self._rebuild(dt)

    def _rebuild(self, dt):
        """Recompute the dt-dependent model (F, Q, and the two poles)."""
        if dt == self._dt:
            return
        self._dt = dt
        self.a = min(1.0, dt / self.rate_tau_s)
        self.beta = 1.0 - math.exp(-dt / max(1e-3, self.tau_bal_s))
        self.F = [[1.0, dt, 0.0],
                  [0.0, 1.0 - self.a, 0.0],
                  [self.beta, 0.0, 1.0 - self.beta]]
        v = self.q_var
        self.Q = [[0.25 * dt ** 4 * v, 0.5 * dt ** 3 * v, 0.0],
                  [0.5 * dt ** 3 * v, dt ** 2 * v, 0.0],
                  [0.0, 0.0, 1e-8]]

    def seed(self, mass_g, sigma_g=None, r_sigma_gps=0.02):
        """Start mid-dose from a settled reading: m = b = mass, r = 0.

        With ``sigma_g`` omitted the covariance keeps the original's
        ``diag(0.05)`` (the cross-check test relies on that).  On the
        rig the seed comes from a settled *bracketed* read whose actual
        uncertainty is sub-mg, and leaving P at 0.05 g^2 makes the
        cutoff's ``k*sigma`` term ~0.22 g on the first polls -- larger
        than the whole trim headroom, so a from-rest trickle would halt
        on poll 1 having done nothing.  (The twin never sees this only
        because its trim always starts exactly 0.30 g out.)  Passing the
        bracket sigma gives the filter the honest initial covariance:
        m and b are known to ``sigma_g``, and the rate at rest is known
        to be ~0 within ``r_sigma_gps``.
        """
        self.x[0] = mass_g
        self.x[2] = mass_g
        if sigma_g is not None:
            v = sigma_g * sigma_g
            self.P = [[v, 0.0, 0.0],
                      [0.0, r_sigma_gps * r_sigma_gps, 0.0],
                      [0.0, 0.0, v]]

    def update(self, z, noisy, u_rev_s=None, ff=0.3, fresh=True, dt=None):
        """One predict(+update) step; returns ``(m_hat, r_hat)``.

        ``z`` is the raw balance reading (grams, baseline-corrected);
        ``noisy`` selects the actuating measurement noise; ``u_rev_s``
        is the *commanded* auger speed in rev/s (None = no input model,
        the rate persists); ``fresh`` False skips the measurement update
        (stale/absent frame -- predict only).
        """
        if dt is not None:
            self._rebuild(dt)
        F, x, P = self.F, self.x, self.P
        F[1][1] = 1.0 if u_rev_s is None else 1.0 - self.a
        u = 0.0 if u_rev_s is None else self.a * ff * u_rev_s
        # x = F x (+ B u)
        m = x[0] + F[0][1] * x[1]
        r = F[1][1] * x[1] + u
        b = self.beta * x[0] + F[2][2] * x[2]
        x[0], x[1], x[2] = m, r, b
        # P = F P F' + Q
        FP = _mat33_mul(F, P)
        P = _mat33_mul_t(FP, F)
        for i in range(3):
            for j in range(3):
                P[i][j] += self.Q[i][j]

        if fresh:
            R = (self.noisy_sd if noisy else self.quiet_sd) ** 2
            S = P[2][2] + R                   # H = [0, 0, 1]
            K = [P[0][2] / S, P[1][2] / S, P[2][2] / S]
            y = z - x[2]
            x[0] += K[0] * y
            x[1] += K[1] * y
            x[2] += K[2] * y
            Prow2 = (P[2][0], P[2][1], P[2][2])
            for i in range(3):
                for j in range(3):
                    P[i][j] -= K[i] * Prow2[j]
        self.P = P

        # Non-negativity projection on the rate.  As in the original: P is
        # NOT corrected, so pred_sigma() is miscalibrated while the clamp
        # is active -- counted so the telemetry can show it.
        if x[1] < 0.0:
            x[1] = 0.0
            self.clamp_hits += 1
        return x[0], x[1]

    def pred_sigma(self, tau_s):
        """sd of the committed-mass prediction ``m + r * tau``."""
        P = self.P
        var = P[0][0] + tau_s * tau_s * P[1][1] + 2.0 * tau_s * P[0][1]
        return math.sqrt(var) if var > 0.0 else 0.0

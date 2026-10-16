"""Tests for the trim study (issue #153).

Run with::

    python -m unittest discover -s optimization/trim -v

These check three classes of thing: that the maths helpers are right (the
incomplete gamma and the compound-Poisson tail are hand-rolled, so they are
checked against closed forms), that the plant reproduces the bench numbers it
claims to be calibrated against, and that the safety-critical properties of the
chance-constrained sizing rule actually hold.
"""
from __future__ import annotations

import math
import statistics as st
import unittest

from estimators import (MassRateLagKF, YieldModel, _gammq,
                        compound_poisson_exceedance, lognormal_exceedance)
from metrics import Outcome, mcnemar, summarize, wilson
from trim_methods import METHODS, STALL_METERED_G
from trim_sim import POWDERS, TrimPlant, make_rig


def _outcome(method, seed, err_mg, status="ok"):
    return Outcome(method=method, powder="salt", seed=seed, target_g=2.3,
                   tau_bal_plant_s=0.7, tau_bal_belief_s=0.7, slug_cv=2.48,
                   start_deficit_g=0.30, delivered_g=2.3 + err_mg / 1000.0,
                   signed_error_mg=err_mg, time_s=10.0, taps=0, auger_rev=1.0,
                   settle_waits=1, status=status)


class TestSpecialFunctions(unittest.TestCase):
    """The hand-rolled incomplete gamma, against closed forms."""

    def test_gammq_integer_shape(self):
        # Q(1, x) = exp(-x);  Q(2, x) = (1 + x) exp(-x)
        for x in (0.1, 1.0, 3.0, 12.0):
            self.assertAlmostEqual(_gammq(1.0, x), math.exp(-x), places=10)
            self.assertAlmostEqual(_gammq(2.0, x), (1 + x) * math.exp(-x),
                                   places=10)

    def test_gammq_half_shape(self):
        # Q(1/2, x) = erfc(sqrt(x))
        for x in (0.05, 0.5, 2.0, 9.0):
            self.assertAlmostEqual(_gammq(0.5, x), math.erfc(math.sqrt(x)),
                                   places=10)

    def test_gammq_monotone_and_bounded(self):
        prev = 1.0
        for x in [0.1 * i for i in range(1, 60)]:
            q = _gammq(2.5, x)
            self.assertTrue(0.0 <= q <= 1.0)
            self.assertLess(q, prev + 1e-12)
            prev = q


class TestCompoundPoisson(unittest.TestCase):

    def test_matches_monte_carlo(self):
        import random
        lam, mu_s, cv = 2.0, 6.4e-3, 2.48
        shape, scale = 1.0 / cv ** 2, mu_s * cv ** 2
        rng = random.Random(12345)
        n = 200_000
        thresholds = [5e-3, 2e-2, 5e-2]
        hits = [0] * len(thresholds)
        for _ in range(n):
            k = 0
            # Knuth Poisson sampler
            p, target = 1.0, math.exp(-lam)
            while p > target:
                p *= rng.random()
                k += 1
            k -= 1
            y = sum(rng.gammavariate(shape, scale) for _ in range(k))
            for i, t in enumerate(thresholds):
                if y > t:
                    hits[i] += 1
        for i, t in enumerate(thresholds):
            emp = hits[i] / n
            got = compound_poisson_exceedance(lam, mu_s, cv, t)
            self.assertAlmostEqual(got, emp, delta=0.01,
                                   msg=f"threshold {t}: {got} vs {emp}")

    def test_zero_event_atom(self):
        """P(Y > 0+) is bounded by 1 - exp(-lam), the "at least one event" mass.

        It sits slightly below that bound rather than on it: the Gamma used for
        the mark sum has shape 1/cv^2 = 0.16, which piles probability up near
        zero, so a fired event can still deliver essentially nothing.  Only the
        right tail feeds the safety rule, so the small deficit near zero does not
        matter -- but the bound must hold, because exceeding it would mean the
        k = 0 term had leaked in, and the ~14 % chance of no event at all is
        precisely what a Normal approximation gets wrong.
        """
        for lam in (0.3, 1.0, 6.6):
            got = compound_poisson_exceedance(lam, 6.4e-3, 2.48, 1e-9)
            bound = 1.0 - math.exp(-lam)
            self.assertLessEqual(got, bound + 1e-9)
            self.assertGreater(got, 0.9 * bound)

    def test_monotone_in_threshold(self):
        prev = 1.0
        for t in [1e-3 * i for i in range(1, 80)]:
            q = compound_poisson_exceedance(2.0, 6.4e-3, 2.48, t)
            self.assertLessEqual(q, prev + 1e-12)
            prev = q

    def test_lognormal_exceedance_median(self):
        # At the median the exceedance is 1/2; median = mean / sqrt(1 + cv^2)
        mean, cv = 6.5e-3, 1.1
        median = mean / math.sqrt(1.0 + cv ** 2)
        self.assertAlmostEqual(lognormal_exceedance(mean, cv, median), 0.5,
                               places=6)


class TestYieldModel(unittest.TestCase):

    def test_sizing_respects_the_risk_budget(self):
        """The core safety property: the returned command's own exceedance
        probability against the budget is inside alpha."""
        m = YieldModel()
        for budget in (0.400, 0.200, 0.100, 0.050, 0.020, 0.008):
            for alpha in (0.10, 0.05, 0.01):
                n = m.largest_safe_rev(budget, alpha, n_max=4.0)
                if n > 0.0:
                    self.assertLessEqual(m.exceedance(n, budget), alpha + 1e-9)

    def test_sizing_is_monotone_in_budget(self):
        m = YieldModel()
        prev = -1.0
        for budget in [0.005 * i for i in range(1, 80)]:
            n = m.largest_safe_rev(budget, 0.05, n_max=4.0)
            self.assertGreaterEqual(n, prev - 1e-9)
            prev = n

    def test_refuses_to_command_below_the_quantum(self):
        """With the measured slug statistics there is a budget below which no
        command is safe.  That floor is the study's central claim, so it is
        asserted rather than left implicit."""
        m = YieldModel()
        self.assertEqual(m.largest_safe_rev(0.005, 0.02, n_max=4.0), 0.0)
        self.assertGreater(m.largest_safe_rev(0.300, 0.02, n_max=4.0), 0.0)

    def test_a_finer_quantum_lifts_the_floor(self):
        coarse = YieldModel(mu_s_g=6.4e-3)
        fine = YieldModel(mu_s_g=0.4e-3)
        budget = 0.010
        self.assertEqual(coarse.largest_safe_rev(budget, 0.02, n_max=4.0), 0.0)
        self.assertGreater(fine.largest_safe_rev(budget, 0.02, n_max=4.0), 0.0)

    def test_zero_yield_steps_cannot_run_away_with_the_command(self):
        """Bounded response to a run of zero-yield steps.

        Some growth is correct: if revolutions really are delivering less, more
        of them are needed.  What sank the naive per-step EWMA was that the
        growth was *unbounded* -- each 0 mg step pulled the yield estimate
        further down, which made the next command larger, which banked more mass
        on the lip for one avalanche to deliver at once.  The cumulative
        estimator is shrunk toward the bench prior and floored, so the command
        can only inflate by a bounded factor no matter how long the dry run.

        The bound is the estimator's floor ratio, ``g_prior / (0.2 g_prior) =
        5``, and it is reached only after ~2 commanded revolutions have gone in
        with nothing coming out -- by which point ``STALL_METERED_G`` has long
        since declared the auger blocked and handed over to the tap.
        """
        m = YieldModel()
        first = m.largest_safe_rev(0.100, 0.05, n_max=4.0)
        for _ in range(40):
            m.observe(0.05, 0.0)
        after = m.largest_safe_rev(0.100, 0.05, n_max=4.0)
        self.assertAlmostEqual(m.g, 0.2 * m.g_prior, places=9)
        self.assertLessEqual(after, 5.0 * first + 1e-9)
        # The stall detector fires far earlier than the floor is reached.
        self.assertGreater(m.g_prior * m.n_cmd_rev, STALL_METERED_G)

    def test_identifies_a_known_yield(self):
        m = YieldModel(g_prior=0.113)
        for _ in range(20):
            m.observe(0.2, 0.2 * 0.060)      # true settled yield 0.060 g/rev
        self.assertAlmostEqual(m.g, 0.060, delta=0.006)


class TestKalmanFilter(unittest.TestCase):

    def test_tracks_a_constant_mass(self):
        kf = MassRateLagKF(0.1, tau_bal_s=0.7)
        kf.seed(2.0)
        for _ in range(80):
            m, r = kf.update(2.0, noisy=False)
        self.assertAlmostEqual(m, 2.0, places=3)
        self.assertAlmostEqual(r, 0.0, places=3)

    def test_pred_sigma_is_measurement_independent(self):
        """The Riccati point from the Edison spot-check: this covariance does
        not react to the data, so k*sigma is a model-scheduled cushion and not
        a data-quality monitor.  Encoded as a test so nobody re-describes it as
        adaptive."""
        import random
        sigmas = []
        for seed in (1, 2, 3):
            rng = random.Random(seed)
            kf = MassRateLagKF(0.1, tau_bal_s=0.7)
            kf.seed(2.0)
            for _ in range(60):
                kf.update(2.0 + rng.gauss(0.0, 0.01 * seed), noisy=False)
            sigmas.append(kf.pred_sigma(0.30))
        self.assertAlmostEqual(sigmas[0], sigmas[1], places=12)
        self.assertAlmostEqual(sigmas[1], sigmas[2], places=12)


class TestPlantCalibration(unittest.TestCase):
    """The plant claims to reproduce specific bench numbers; check it does."""

    def test_post_halt_drain_matches_bench(self):
        # diag_trickle_stages.txt: median +26.0 mg, p95 +52.4 mg
        drains = []
        for seed in range(200):
            p = TrimPlant(powder=POWDERS["salt"], seed=seed)
            p.prime_lip()
            p.set_rpm(18.0)
            p.step(8.0)
            before = p.delivered_g + sum(m for _, m in p._in_flight)
            p.set_rpm(0.0)
            p.step(8.0)
            drains.append((p.delivered_g - before) * 1000.0)
        self.assertAlmostEqual(st.mean(drains), 26.0, delta=8.0)

    def test_slug_statistics_match_bench(self):
        # Edison spot-check: mean 6.4 mg per event.
        marks = []
        for seed in range(30):
            p = TrimPlant(powder=POWDERS["salt"], seed=seed)
            p.prime_lip()
            p.set_rpm(18.0)
            p.step(10.0)
            orig = p._launch
            p._launch = lambda mass, o=orig: (marks.append(mass), o(mass))[1]
            p.step(15.0)
            p._launch = orig
        self.assertAlmostEqual(st.mean(marks) * 1000.0, 6.4, delta=1.5)

    def test_small_commands_do_not_shrink_the_tail_proportionally(self):
        """The physical fact the whole study turns on: a 9x smaller command does
        not give a 9x smaller worst case."""
        p95 = {}
        for deg in (45.0, 5.0):
            ys = []
            for seed in range(120):
                rig, plant, _ = make_rig("salt", seed, start_deficit_g=0.30)
                rig.settled_read()
                before = plant.delivered_g
                rig.rotate_deg(deg, rpm=40.0)
                rig.settled_read()
                ys.append((plant.settled_mass_g() - before) * 1000.0)
            ys.sort()
            p95[deg] = ys[int(0.95 * len(ys))]
        self.assertGreater(p95[5.0], 0.3 * p95[45.0])

    def test_balance_is_quantized_and_lagged(self):
        p = TrimPlant(powder=POWDERS["salt"], seed=1, tau_bal_s=0.7)
        p.delivered_g = 1.0
        p.step(0.2)
        g, _, _ = p.read_frame()
        self.assertLess(g, 1.0)             # lag: reading has not caught up
        p.step(5.0)
        g, _, _ = p.read_frame()
        self.assertAlmostEqual(g, 1.0, delta=5e-3)
        self.assertAlmostEqual(g / 1e-4, round(g / 1e-4), places=6)


class TestMethodsRun(unittest.TestCase):
    """Every method completes on every powder without raising."""

    def test_all_methods_terminate(self):
        for name in METHODS:
            for powder in POWDERS:
                rig, plant, target = make_rig(powder, 5, start_deficit_g=0.30)
                status = METHODS[name](rig, target)
                self.assertIn(status, ("ok", "short", "stalled", "timeout"),
                              msg=f"{name}/{powder} -> {status}")
                self.assertLess(rig.t, rig.GLOBAL_TIMEOUT_S + 30.0)

    def test_no_method_actuates_past_the_interlock(self):
        """Nothing may command an actuator once the settled reading is already
        at target: that is the guarantee that sits outside every control law."""
        for name in ("chance_increment", "chance_tap"):
            rig, plant, target = make_rig("salt", 11, start_deficit_g=0.30)
            # Start already at target.
            plant.delivered_g = target
            plant._bal_filt_g = target
            before_rev = rig.auger_rev
            METHODS[name](rig, target)
            self.assertAlmostEqual(rig.auger_rev, before_rev, places=6)
            self.assertEqual(rig.taps, 0)


class TestMetrics(unittest.TestCase):

    def test_one_sided_scorecard(self):
        outs = [_outcome("m", i, e) for i, e in
                enumerate([-10.0, -3.0, -1.0, 0.0, 2.0, 8.0])]
        s = summarize(outs)
        self.assertAlmostEqual(s["p_over"], 2 / 6)
        self.assertAlmostEqual(s["p_over_5"], 1 / 6)
        self.assertAlmostEqual(s["p_under_5"], 1 / 6)
        self.assertAlmostEqual(s["epe_mg"], 10.0 / 6)
        self.assertAlmostEqual(s["yield_band"], 3 / 6)   # -3, -1, 0
        self.assertAlmostEqual(s["max_pos_mg"], 8.0)

    def test_short_is_not_counted_as_a_failure(self):
        outs = [_outcome("m", 0, -20.0, status="short"),
                _outcome("m", 1, -2.0, status="ok"),
                _outcome("m", 2, -2.0, status="stalled")]
        s = summarize(outs)
        self.assertAlmostEqual(s["p_incomplete"], 1 / 3)
        self.assertAlmostEqual(s["p_short"], 1 / 3)

    def test_wilson_brackets_the_point_estimate(self):
        lo, hi = wilson(3, 100)
        self.assertLess(lo, 0.03)
        self.assertGreater(hi, 0.03)
        self.assertGreater(lo, 0.0)          # never negative, unlike the normal CI

    def test_mcnemar_pairs_on_design_cells(self):
        a = [_outcome("a", i, -1.0) for i in range(20)]
        b = [_outcome("b", i, +1.0) for i in range(20)]
        r = mcnemar(a, b)
        self.assertEqual(r["n_pairs"], 20)
        self.assertEqual(r["a_only"], 0)
        self.assertEqual(r["b_only"], 20)
        self.assertLess(r["p"], 1e-4)


if __name__ == "__main__":
    unittest.main()

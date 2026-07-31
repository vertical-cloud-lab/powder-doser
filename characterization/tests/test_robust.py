"""Tests for the stdlib-only robust statistics."""

from __future__ import annotations

import math
import random
import unittest

from characterization import robust


class BasicsTests(unittest.TestCase):
    def test_empty_is_none_not_zero(self) -> None:
        # Returning 0.0 for "no data" would silently report a perfect
        # noise floor for a condition that never produced a reading.
        self.assertIsNone(robust.mean([]))
        self.assertIsNone(robust.median([]))
        self.assertIsNone(robust.stdev([1.0]))
        self.assertEqual(robust.summarize([]).n, 0)

    def test_median_even_and_odd(self) -> None:
        self.assertEqual(robust.median([3, 1, 2]), 2)
        self.assertEqual(robust.median([4, 1, 2, 3]), 2.5)

    def test_non_finite_dropped(self) -> None:
        values = [1.0, 2.0, float("nan"), float("inf"), 3.0]
        self.assertEqual(robust.median(values), 2.0)
        self.assertEqual(robust.summarize(values).n, 3)

    def test_quantile_interpolates(self) -> None:
        self.assertAlmostEqual(robust.quantile([0, 10], 0.5), 5.0)
        self.assertAlmostEqual(robust.quantile([0, 1, 2, 3, 4], 0.25), 1.0)


class RobustnessTests(unittest.TestCase):
    def test_mad_estimates_sigma_for_normal_data(self) -> None:
        rng = random.Random(0)
        values = [rng.gauss(0.0, 2.0) for _ in range(4000)]
        self.assertAlmostEqual(robust.mad(values), 2.0, delta=0.15)

    def test_one_bump_wrecks_sd_but_not_mad(self) -> None:
        rng = random.Random(1)
        clean = [rng.gauss(0.0, 1e-4) for _ in range(40)]
        bumped = clean + [5.0]  # somebody knocked the bench
        self.assertGreater(robust.stdev(bumped), 50 * robust.stdev(clean))
        self.assertLess(abs(robust.mad(bumped) / robust.mad(clean) - 1.0), 0.2)

    def test_outliers_counted(self) -> None:
        rng = random.Random(2)
        values = [rng.gauss(0.0, 1.0) for _ in range(200)] + [40.0, -35.0]
        self.assertGreaterEqual(robust.outlier_count(values), 2)

    def test_sigma_rel_se_matches_formula(self) -> None:
        # n=20 pins sigma to about +/-16 %.
        self.assertAlmostEqual(robust.sigma_rel_se(20),
                               1.0 / math.sqrt(2 * 19), places=9)
        self.assertAlmostEqual(robust.sigma_rel_se(20), 0.162, places=3)
        self.assertIsNone(robust.sigma_rel_se(1))

    def test_summary_prefers_mad(self) -> None:
        summary = robust.summarize([1.0, 1.1, 0.9, 1.05, 0.95])
        self.assertEqual(summary.robust_sigma, summary.mad)
        self.assertEqual(summary.n, 5)

    def test_summary_falls_back_to_sd_when_mad_is_undefined(self) -> None:
        summary = robust.summarize([1.0])
        self.assertIsNone(summary.robust_sigma)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

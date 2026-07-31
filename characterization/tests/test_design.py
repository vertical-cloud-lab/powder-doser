"""Tests for the experiment designs."""

from __future__ import annotations

import unittest
from collections import Counter

from characterization import design, firmware_params


class ConditionTests(unittest.TestCase):
    def test_validation_coerces_against_firmware_spec(self) -> None:
        condition = design.Condition(name="x", params={"stepper_rpm": "45",
                                                       "tap_count": "3"})
        validated = condition.validated()
        self.assertEqual(validated.params["stepper_rpm"], 45.0)
        self.assertEqual(validated.params["tap_count"], 3)

    def test_bad_level_fails_on_the_host(self) -> None:
        mod = firmware_params.load_params_module()
        # The whole point of host-side validation: this must fail here,
        # in milliseconds, not at 3 a.m. on the rig.
        with self.assertRaises(mod.ParamError):
            design.Condition(name="x",
                             params={"stepper_rpm": 5000}).validated()

    def test_bad_action_rejected(self) -> None:
        with self.assertRaises(ValueError):
            design.Condition(name="x", actions=("wiggle",)).validated()


class DesignTests(unittest.TestCase):
    def test_screening_is_one_factor_at_a_time(self) -> None:
        conditions = design.screening()
        self.assertTrue(conditions)
        for condition in conditions:
            differences = [k for k, v in condition.params.items()
                           if design.BASELINE.get(k) != v]
            self.assertLessEqual(
                len(differences), 1,
                "{} perturbs more than one factor: {}".format(
                    condition.name, differences))

    def test_screening_covers_every_source(self) -> None:
        actions = {a for c in design.screening() for a in c.actions}
        self.assertEqual(actions, {"dispense", "vibrate", "tap", "servo"})

    def test_rpm_scan_spans_the_range(self) -> None:
        conditions = design.rpm_scan(lo=10, hi=50, step=10)
        rpms = [c.params["stepper_rpm"] for c in conditions]
        self.assertEqual(rpms, [10.0, 20.0, 30.0, 40.0, 50.0])

    def test_factorial_refuses_to_explode(self) -> None:
        big = [design.Factor("stepper_rpm", tuple(range(10, 100, 10))),
               design.Factor("tap_count", (1, 2, 3, 4, 5)),
               design.Factor("stepper_microsteps", (1, 2, 4, 8))]
        with self.assertRaises(ValueError):
            design.factorial(big)

    def test_factorial_small(self) -> None:
        conditions = design.factorial([
            design.Factor("stepper_rpm", (10.0, 60.0)),
            design.Factor("stepper_microsteps", (1, 8)),
        ])
        self.assertEqual(len(conditions), 4)

    def test_selfcheck_includes_a_control(self) -> None:
        kinds = [c.kind for c in design.selfcheck()]
        self.assertIn("control", kinds)


class RunlistTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conditions = design.rpm_scan(lo=10, hi=40, step=10)

    def test_controls_are_interleaved_and_bookended(self) -> None:
        runs = design.build_runlist(self.conditions, replicates=5, seed=1,
                                    control_every=4)
        kinds = [r.kind for r in runs]
        self.assertEqual(kinds[0], "control")
        self.assertEqual(kinds[-1], "control")
        n_controls = kinds.count("control")
        # 4 conditions x 5 replicates = 20 actuation runs, a control every
        # 4 of them plus the leading one.
        self.assertEqual(kinds.count("actuation"), 20)
        self.assertEqual(n_controls, 6)

    def test_replicates_are_spread_not_blocked(self) -> None:
        runs = design.build_runlist(self.conditions, replicates=10, seed=7,
                                    control_every=0)
        positions = {}
        for i, run in enumerate(runs):
            positions.setdefault(run.condition.name, []).append(i)
        # If replicates ran back to back, a slow drift would masquerade as
        # a between-condition difference. Require each condition's runs to
        # span most of the night.
        for name, idxs in positions.items():
            span = max(idxs) - min(idxs)
            self.assertGreater(span, 0.5 * len(runs),
                               "{} is clustered: {}".format(name, idxs))

    def test_seed_is_reproducible(self) -> None:
        a = design.build_runlist(self.conditions, replicates=4, seed=3)
        b = design.build_runlist(self.conditions, replicates=4, seed=3)
        c = design.build_runlist(self.conditions, replicates=4, seed=4)
        self.assertEqual([r.condition.name for r in a],
                         [r.condition.name for r in b])
        self.assertNotEqual([r.condition.name for r in a],
                            [r.condition.name for r in c])

    def test_every_condition_gets_every_replicate(self) -> None:
        runs = design.build_runlist(self.conditions, replicates=6, seed=0,
                                    control_every=0)
        counts = Counter(r.condition.name for r in runs)
        self.assertEqual(set(counts.values()), {6})

    def test_control_dwell_matches_actuation_cost(self) -> None:
        runs = design.build_runlist(self.conditions, replicates=2, seed=0,
                                    control_every=2)
        control = next(r for r in runs if r.kind == "control")
        costs = sorted(design.estimate_action_seconds(c)
                       for c in self.conditions)
        self.assertAlmostEqual(control.dwell_s, costs[len(costs) // 2])
        self.assertGreater(control.dwell_s, 0.0)

    def test_duration_estimate_accounts_for_windows(self) -> None:
        runs = design.build_runlist(self.conditions, replicates=2, seed=0,
                                    control_every=0, pre_s=3.0, post_s=10.0)
        total = design.estimate_duration_s(runs)
        self.assertGreater(total, len(runs) * 13.0)

    def test_rejects_zero_replicates(self) -> None:
        with self.assertRaises(ValueError):
            design.build_runlist(self.conditions, replicates=0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

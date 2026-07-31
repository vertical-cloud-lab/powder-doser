"""Unit tests for the analysis primitives, on hand-built traces.

Fast and hermetic: these construct traces with a known shape rather than
running the simulator, so a failure points at one function.
"""

from __future__ import annotations

import json
import math
import unittest

from characterization import analyze


def make_record(values, dt=0.05, act_end=1.0, pre_s=1.0, kind="actuation",
                condition="c", index=0, stable_from=None, params=None):
    """Build a RunRecord whose trace is ``values`` sampled every ``dt``."""
    trace = []
    for i, value in enumerate(values):
        t = i * dt
        phase = "pre" if t < pre_s else ("act" if t < act_end else "post")
        stable = stable_from is not None and t >= stable_from
        trace.append(analyze.Sample(t=t, grams=value, stable=stable,
                                    phase=phase))
    row = {
        "run_id": "{:05d}".format(index), "index": str(index),
        "condition": condition, "kind": kind, "error": "",
        "t_act_start": str(pre_s), "t_act_end": str(act_end),
        "t_trace_start": "0.0",
        "params": json.dumps(params or {}),
    }
    return analyze.RunRecord(row=row, trace=trace)


def ringdown(n, dt=0.05, act_end=1.0, amplitude=1e-3, tau=0.5, freq=6.0,
             offset=0.0, baseline=0.0):
    values = []
    for i in range(n):
        t = i * dt
        value = baseline
        if t >= act_end:
            dtt = t - act_end
            value += (offset + amplitude * math.exp(-dtt / tau)
                      * math.sin(2 * math.pi * freq * dtt))
        values.append(value)
    return values


class ValueAtDelayTests(unittest.TestCase):
    def test_referenced_to_the_pre_actuation_baseline(self) -> None:
        # A tare offset of 5 g must not show up as 5 g of dispensed powder.
        values = [5.0] * 20 + [5.002] * 100
        record = make_record(values, act_end=1.0)
        self.assertAlmostEqual(record.act_end, 1.0)
        self.assertAlmostEqual(analyze.value_at_delay(record, 2.0), 0.002,
                               places=6)

    def test_none_when_the_window_is_off_the_end_of_the_trace(self) -> None:
        record = make_record([0.0] * 40, act_end=1.0)
        self.assertIsNone(analyze.value_at_delay(record, 60.0))


class SettleTests(unittest.TestCase):
    def test_settle_time_tracks_the_ringdown(self) -> None:
        slow = make_record(ringdown(400, tau=1.0))
        fast = make_record(ringdown(400, tau=0.1))
        slow_t = analyze.settle_time(slow, window_s=1.0, tol_g=5e-5)
        fast_t = analyze.settle_time(fast, window_s=1.0, tol_g=5e-5)
        self.assertIsNotNone(slow_t)
        self.assertIsNotNone(fast_t)
        self.assertGreater(slow_t, fast_t)

    def test_never_settling_returns_none_not_a_number(self) -> None:
        # A run that never settles is a result. Reporting the last sample
        # instead would quietly turn a stalled controller into a fast one.
        forever = make_record(ringdown(400, tau=1e6, amplitude=1e-2))
        self.assertIsNone(analyze.settle_time(forever, window_s=1.0,
                                              tol_g=5e-5))

    def test_flag_latency_is_independent_of_the_offline_criterion(self) -> None:
        record = make_record(ringdown(400, tau=0.1), stable_from=3.0)
        self.assertAlmostEqual(analyze.flag_latency(record), 2.0, places=2)
        offline = analyze.settle_time(record, window_s=1.0, tol_g=5e-5)
        self.assertLess(offline, 2.0)

    def test_flag_latency_none_when_never_flagged(self) -> None:
        record = make_record(ringdown(200), stable_from=None)
        self.assertIsNone(analyze.flag_latency(record))


class StepTests(unittest.TestCase):
    def test_persistent_step_survives_the_ringdown(self) -> None:
        record = make_record(ringdown(400, offset=1e-3, tau=0.2))
        step = analyze.persistent_step(record, tail_s=3.0)
        self.assertAlmostEqual(step, 1e-3, places=5)

    def test_no_step_when_it_rings_back_to_baseline(self) -> None:
        record = make_record(ringdown(400, offset=0.0, tau=0.2))
        self.assertAlmostEqual(analyze.persistent_step(record), 0.0, places=6)


class ControlCorrectionTests(unittest.TestCase):
    def _drifting_set(self):
        """Controls and actuation runs on a ramp of 1e-4 g per run index.

        A little reproducible jitter on top: with perfectly linear drift
        the leave-one-out residual is exactly zero, which is an artefact of
        the fixture rather than of the estimator.
        """
        jitter = [1e-6, -2e-6, 3e-6, -1e-6, 2e-6, -3e-6, 1e-6]
        records = []
        for index in range(0, 21):
            level = 1e-4 * index + jitter[index % len(jitter)]
            kind = "control" if index % 5 == 0 else "actuation"
            records.append(make_record([0.0] * 20 + [level] * 100,
                                       kind=kind, index=index,
                                       condition="ctl" if kind == "control"
                                       else "act"))
        return records

    def test_drift_is_removed_from_actuation_runs(self) -> None:
        records = self._drifting_set()
        results = analyze.analyze_conditions(records, delay_s=2.0)
        act = next(r for r in results if r.condition == "act")
        self.assertGreater(abs(act.bias.median), 5e-4)
        self.assertLess(abs(act.bias_corrected.median), 1e-5)

    def test_controls_are_not_corrected_against_themselves(self) -> None:
        # Self-correction drives every control residual to exactly zero and
        # reports sigma0 = 0, which would then propagate into LOD, LOQ and
        # the self-check gate as a perfect, fictitious noise floor.
        records = self._drifting_set()
        results = analyze.analyze_conditions(records, delay_s=2.0)
        control = next(r for r in results if r.kind == "control")
        self.assertIsNotNone(control.bias_corrected.mad)
        self.assertNotEqual(control.bias_corrected.mad, 0.0)

    def test_degenerate_control_sigma_falls_back(self) -> None:
        # Perfectly linear drift with no jitter: the LOO residual is
        # identically zero, so the control gives sigma0 = 0. That is a
        # degenerate estimate, not a perfect balance, and must not become
        # LOD = 0 in the calibration.
        jitter = [1e-6, -2e-6, 3e-6, -1e-6]
        records = []
        for index in range(0, 21):
            kind = "control" if index % 5 == 0 else "actuation"
            level = 1e-4 * index
            if kind == "actuation":
                level += jitter[index % len(jitter)]
            records.append(make_record([0.0] * 20 + [level] * 100,
                                       kind=kind, index=index,
                                       condition="ctl" if kind == "control"
                                       else "act"))
        results = analyze.analyze_conditions(records, delay_s=2.0)
        calibration = analyze.build_calibration(
            records, "test", results, 2.0, 1.0, 5e-5)
        floor = calibration["noise_floor"]
        self.assertNotEqual(floor["sigma0_g"], 0.0)
        self.assertNotIn("control", floor["source"])

    def test_no_controls_leaves_bias_uncorrected(self) -> None:
        records = [make_record([0.0] * 20 + [1e-4] * 100, index=i)
                   for i in range(4)]
        results = analyze.analyze_conditions(records, delay_s=2.0)
        self.assertAlmostEqual(results[0].bias.median,
                               results[0].bias_corrected.median)


class BandTests(unittest.TestCase):
    def _rpm_results(self, sigmas):
        results = []
        for i, (rpm, sigma) in enumerate(sigmas):
            # Two-point spread of +/-sigma gives a MAD of exactly sigma.
            records = [make_record([0.0] * 20 + [s] * 100, index=2 * i + j,
                                   condition="rpm={}".format(rpm),
                                   params={"stepper_rpm": rpm})
                       for j, s in enumerate((-sigma, sigma, -sigma, sigma))]
            results.extend(analyze.analyze_conditions(records, delay_s=2.0))
        return results

    def test_flags_the_noisy_band_only(self) -> None:
        results = self._rpm_results([(10.0, 1e-5), (20.0, 1e-5),
                                     (30.0, 1e-3), (40.0, 1e-5),
                                     (50.0, 1e-5)])
        bands = analyze.forbidden_rpm_bands(results)["bands"]
        self.assertEqual(len(bands), 1)
        self.assertTrue(bands[0]["lo_rpm"] <= 30.0 <= bands[0]["hi_rpm"])
        # Widened to the neighbouring sampled levels: the true resonance
        # sits between the points, not exactly on one.
        self.assertEqual((bands[0]["lo_rpm"], bands[0]["hi_rpm"]),
                         (20.0, 40.0))

    def test_no_bands_when_everything_is_quiet(self) -> None:
        results = self._rpm_results([(10.0, 1e-5), (20.0, 1.1e-5),
                                     (30.0, 0.9e-5), (40.0, 1e-5)])
        self.assertEqual(analyze.forbidden_rpm_bands(results)["bands"], [])

    def test_non_adjacent_bands_are_not_merged(self) -> None:
        # 30 and 50 are both noisy with a quiet 40 between them. Their
        # widened windows touch at 40; merging on that would forbid a
        # perfectly good speed.
        results = self._rpm_results([(10.0, 1e-5), (20.0, 1e-5),
                                     (30.0, 1e-3), (40.0, 1e-5),
                                     (50.0, 1e-3), (60.0, 1e-5)])
        bands = analyze.forbidden_rpm_bands(results)["bands"]
        self.assertEqual([(b["lo_rpm"], b["hi_rpm"]) for b in bands],
                         [(20.0, 40.0), (40.0, 60.0)])

    def test_adjacent_bands_are_merged(self) -> None:
        results = self._rpm_results([(10.0, 1e-5), (20.0, 1e-5),
                                     (30.0, 1e-3), (40.0, 1e-3),
                                     (50.0, 1e-5), (60.0, 1e-5)])
        bands = analyze.forbidden_rpm_bands(results)["bands"]
        self.assertEqual([(b["lo_rpm"], b["hi_rpm"]) for b in bands],
                         [(20.0, 50.0)])

    def test_too_few_levels_reports_nothing_rather_than_guessing(self) -> None:
        # Three levels can produce a "band" spanning the whole swept
        # range, which reads as a finding and is not one.
        results = self._rpm_results([(10.0, 1e-5), (30.0, 1e-5),
                                     (240.0, 1e-3)])
        out = analyze.forbidden_rpm_bands(results)
        self.assertEqual(out["bands"], [])
        self.assertIsNone(out["floor_sigma_g"])
        self.assertIn("at least", out["note"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

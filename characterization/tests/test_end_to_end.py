"""End-to-end tests: mock rig -> sweep -> analysis -> calibration.

These are the tests that give the analysis any credibility.  The simulator
plants a *known* resonance band, a known reseat step, and a known ambient
drift; the assertions are that the pipeline recovers them.  An analysis
that has never been shown to recover a planted effect is not evidence of
anything, and a blank-auger sweep whose analysis is wrong is worse than
no sweep at all -- it produces a confident, fictitious noise floor.

The mock runs on the real clock with a large ``speedup``, so these
exercise the same threading and timing paths as the hardware harness.
"""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from characterization import analyze, design
from characterization.mock import MockBalance, MockRig, SimConfig, Simulator
from characterization.sweep import RUN_FIELDS, SweepRunner

SPEEDUP = 100.0
SAMPLE_HZ = 25.0
PRE_S = 1.0
POST_S = 6.0
READ_DELAY_S = 2.0

#: With 1/8 microstepping on a 200-step motor, step frequency is
#: rpm/60 * 1600 = rpm * 26.67 Hz.
STEP_HZ_PER_RPM = 200 * 8 / 60.0


def make_pair(cfg=None, never_stable=False):
    sim = Simulator(cfg or SimConfig(), speedup=SPEEDUP)
    return (MockRig(sim),
            MockBalance(sim, sample_hz=SAMPLE_HZ, never_stable=never_stable),
            sim)


def run_sweep(outdir, conditions, replicates, cfg=None, seed=0,
              control_every=5, never_stable=False, tare_every=5):
    rig, balance, sim = make_pair(cfg, never_stable)
    runs = design.build_runlist(conditions, replicates=replicates, seed=seed,
                                control_every=control_every, pre_s=PRE_S,
                                post_s=POST_S)
    runner = SweepRunner(rig, balance, outdir, tare_every=tare_every,
                         environment="test", verbose=False,
                         clock=sim.now, sleep=sim.sleep)
    runner.run(runs, manifest={"design": "test", "seed": seed})
    balance.close()
    return sim


def analyse(outdir, delay_s=READ_DELAY_S):
    records = analyze.load_runs(Path(outdir))
    results = analyze.analyze_conditions(records, delay_s=delay_s)
    calibration = analyze.build_calibration(
        records, "test", results, delay_s, analyze.DEFAULT_STABLE_WINDOW_S,
        analyze.DEFAULT_STABLE_TOL_G, analyze.load_manifest(Path(outdir)))
    return records, results, calibration


class SweepOutputTests(unittest.TestCase):
    def test_writes_rows_traces_and_manifest(self) -> None:
        conditions = design.rpm_scan(lo=20, hi=40, step=20)
        with tempfile.TemporaryDirectory() as tmp:
            run_sweep(tmp, conditions, replicates=2, control_every=2)
            out = Path(tmp)
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertEqual(manifest["environment"], "test")

            with (out / "runs.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(list(rows[0]), list(RUN_FIELDS))
            self.assertTrue(rows)
            for row in rows:
                self.assertEqual(row["error"], "")
                self.assertGreater(int(row["n_samples"]), 0)
                trace = out / "traces" / "{}.csv".format(row["run_id"])
                self.assertTrue(trace.exists())

            # The parameter snapshot is read back from the rig, not
            # assumed from the host's intent.
            actuation = [r for r in rows if r["kind"] == "actuation"]
            params = json.loads(actuation[0]["params"])
            self.assertIn("stepper_rpm", params)
            self.assertEqual(
                params["stepper_rpm"],
                float(actuation[0]["condition"].split("=")[1]))

    def test_traces_keep_both_channels_at_full_rate(self) -> None:
        conditions = design.rpm_scan(lo=30, hi=30, step=10)
        with tempfile.TemporaryDirectory() as tmp:
            run_sweep(tmp, conditions, replicates=1, control_every=0)
            trace = next((Path(tmp) / "traces").glob("*.csv"))
            with trace.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertGreater(len(rows), 20)
            self.assertEqual({r["phase"] for r in rows},
                             {"pre", "act", "post"})
            # The stable flag is recorded, never used to filter: unstable
            # samples must survive into the trace.
            self.assertIn("0", {r["stable"] for r in rows})


class RecoveryTests(unittest.TestCase):
    def test_recovers_planted_resonance_band(self) -> None:
        bad_rpm = 60.0
        cfg = SimConfig(
            base_freq_hz=6.0,
            resonant_step_hz=(bad_rpm * STEP_HZ_PER_RPM,),
            band_width_hz=10.0 * STEP_HZ_PER_RPM,
            resonance_gain=15.0,
            tap_reseat_prob=0.0,
            drift_g_per_s=0.0,
            seed=11,
        )
        conditions = design.rpm_scan(lo=20, hi=140, step=20)
        with tempfile.TemporaryDirectory() as tmp:
            run_sweep(tmp, conditions, replicates=6, cfg=cfg, seed=5)
            _records, results, calibration = analyse(tmp)

        by_rpm = {r.params["stepper_rpm"]: r for r in results
                  if r.kind == "actuation"}
        worst = max(by_rpm.values(), key=lambda r: r.sigma or 0.0)
        self.assertEqual(worst.params["stepper_rpm"], bad_rpm,
                         "planted resonance at {} RPM not the noisiest "
                         "level: {}".format(bad_rpm, {k: v.sigma for k, v
                                                      in by_rpm.items()}))
        bands = calibration["forbidden_rpm_bands"]["bands"]
        self.assertTrue(bands, "resonance not flagged as a forbidden band")
        self.assertTrue(
            any(b["lo_rpm"] <= bad_rpm <= b["hi_rpm"] for b in bands),
            "flagged bands {} do not contain {} RPM".format(bands, bad_rpm))

    def test_recovers_persistent_step_from_taps(self) -> None:
        # A one-directional reseat: the systematic case, which a powder run
        # would silently absorb into "how much powder came out".
        cfg = SimConfig(tap_reseat_prob=1.0, tap_reseat_g=1e-3,
                        tap_reseat_sign=1, drift_g_per_s=0.0, seed=3)
        base = dict(design.BASELINE)
        conditions = [
            design.Condition(name="tap", params=base, actions=("tap",)),
            design.Condition(name="dispense", params=base,
                             actions=("dispense",)),
        ]
        conditions = [c.validated() for c in conditions]
        with tempfile.TemporaryDirectory() as tmp:
            run_sweep(tmp, conditions, replicates=6, cfg=cfg, seed=2,
                      tare_every=1)
            _records, results, _cal = analyse(tmp)
        by_name = {r.condition: r for r in results}
        tap_step = abs(by_name["tap"].step.median or 0.0)
        dispense_step = abs(by_name["dispense"].step.median or 0.0)
        # A step that outlives the actuation is the artefact that most
        # convincingly imitates real mass; it must be visible and it must
        # be attributed to the taps, not to the auger.
        self.assertGreater(tap_step, 5e-4)
        self.assertGreater(tap_step, 5 * max(dispense_step, 1e-6))

    def test_control_correction_removes_ambient_drift(self) -> None:
        # 0.5 mg/s of drift dwarfs every real effect here; without control
        # subtraction it would be attributed to whichever factor was swept.
        cfg = SimConfig(drift_g_per_s=5e-4, tap_reseat_prob=0.0, seed=7)
        conditions = design.rpm_scan(lo=30, hi=90, step=30)
        with tempfile.TemporaryDirectory() as tmp:
            run_sweep(tmp, conditions, replicates=6, cfg=cfg, seed=1,
                      control_every=3, tare_every=1000)
            _records, results, _cal = analyse(tmp)
        actuation = [r for r in results if r.kind == "actuation"]
        raw = max(abs(r.bias.median) for r in actuation)
        corrected = max(abs(r.bias_corrected.median) for r in actuation)
        self.assertGreater(raw, 1e-3, "drift did not accumulate as expected")
        self.assertLess(corrected, 0.5 * raw,
                        "control correction did not reduce the drift term")

    def test_never_stable_balance_is_reported_not_hidden(self) -> None:
        conditions = design.rpm_scan(lo=30, hi=30, step=10)
        with tempfile.TemporaryDirectory() as tmp:
            run_sweep(tmp, conditions, replicates=3, control_every=0,
                      never_stable=True)
            _records, results, calibration = analyse(tmp)
        flag = calibration["balance_stability_flag"]
        self.assertEqual(flag["never_flagged_fraction"], 1.0)
        # The offline criterion still produces a settle time, which is the
        # point: the balance's flag is not the only path to a reading.
        self.assertTrue(any(r.settle.n > 0 for r in results))

    def test_settle_curve_sigma_decreases_with_waiting(self) -> None:
        cfg = SimConfig(base_freq_hz=6.0, base_tau_s=1.0, drift_g_per_s=0.0,
                        tap_reseat_prob=0.0, seed=13)
        conditions = design.rpm_scan(lo=30, hi=60, step=30)
        with tempfile.TemporaryDirectory() as tmp:
            run_sweep(tmp, conditions, replicates=6, cfg=cfg, seed=4)
            records, _results, calibration = analyse(tmp)
        curve = calibration["settle_delay_curve"]["curve"]
        sigmas = [c["sigma_g"] for c in curve if c["sigma_g"] is not None]
        self.assertGreaterEqual(len(sigmas), 3)
        self.assertLess(sigmas[-1], sigmas[0],
                        "waiting longer did not reduce sigma: {}".format(
                            sigmas))
        self.assertIsNotNone(calibration["settle_delay_curve"]["knee_s"])

    def test_noise_floor_and_lod_are_reported(self) -> None:
        cfg = SimConfig(noise_g=1e-4, drift_g_per_s=0.0, tap_reseat_prob=0.0,
                        seed=21)
        conditions = design.rpm_scan(lo=30, hi=30, step=10)
        with tempfile.TemporaryDirectory() as tmp:
            run_sweep(tmp, conditions, replicates=8, cfg=cfg, control_every=2)
            _records, results, calibration = analyse(tmp)
        floor = calibration["noise_floor"]
        self.assertIsNotNone(floor["sigma0_g"])
        self.assertAlmostEqual(floor["lod_g"], 3 * floor["sigma0_g"])
        self.assertAlmostEqual(floor["loq_g"], 10 * floor["sigma0_g"])
        report = analyze.format_report(calibration, results)
        self.assertIn("noise floor", report)


class SelfCheckTests(unittest.TestCase):
    def _write_calibration(self, tmp: Path, sigma0: float, knee: float) -> Path:
        path = tmp / "reference.json"
        path.write_text(json.dumps({
            "schema": "powder-doser/blank-auger-calibration",
            "version": 1,
            "environment": "test",
            "criterion": {"read_delay_s": READ_DELAY_S,
                          "stable_window_s": analyze.DEFAULT_STABLE_WINDOW_S,
                          "stable_tol_g": analyze.DEFAULT_STABLE_TOL_G},
            "noise_floor": {"sigma0_g": sigma0},
            "settle_delay_curve": {"knee_s": knee},
        }))
        return path

    def test_matching_environment_passes(self) -> None:
        from characterization import selfcheck

        cfg = SimConfig(noise_g=5e-5, drift_g_per_s=0.0, tap_reseat_prob=0.0,
                        seed=31)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_sweep(tmp_path / "runs", design.selfcheck(), replicates=4,
                      cfg=cfg, control_every=3)
            _records, results, observed = analyse(tmp_path / "runs")
            sigma0 = observed["noise_floor"]["sigma0_g"]
            reference = self._write_calibration(
                tmp_path, sigma0, observed["settle_delay_curve"]["knee_s"] or 1.0)
            calibration = json.loads(reference.read_text())
            checks = selfcheck.compare(calibration, results, observed)
        self.assertTrue(all(c.ok for c in checks),
                        "\n".join(c.line() for c in checks))

    def test_noisier_environment_is_refused(self) -> None:
        from characterization import selfcheck

        cfg = SimConfig(noise_g=2e-3, drift_g_per_s=0.0, tap_reseat_prob=0.0,
                        seed=41)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_sweep(tmp_path / "runs", design.selfcheck(), replicates=4,
                      cfg=cfg, control_every=3)
            _records, results, observed = analyse(tmp_path / "runs")
            # Reference from a much quieter bench.
            reference = self._write_calibration(tmp_path, 2e-5, 1.0)
            calibration = json.loads(reference.read_text())
            checks = selfcheck.compare(calibration, results, observed)
        self.assertFalse(all(c.ok for c in checks),
                         "a 100x noisier environment was accepted")
        self.assertFalse(next(c for c in checks
                              if c.name == "noise floor").ok)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

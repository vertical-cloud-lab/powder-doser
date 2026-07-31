"""Environment self-check: reproduce a stored calibration, or refuse.

"Recalibrate when you move the rig" is tribal knowledge until something
enforces it.  This is the gate: a short subset of the full sweep (a
control, the baseline dispense, both RPM extremes, and a tap) run on
entering a new environment, compared against the stored calibration for
that environment, exiting non-zero when it does not reproduce.

Wire it into whatever starts a dispensing campaign.  A non-zero exit means
*do not dispense*: either the environment is not the one that was
characterised, or something on the rig has changed, and in both cases the
noise floor the controller is trusting is fiction.

Usage::

    python -m characterization.selfcheck --calibration calibration/bench.json \\
        --rig-port /dev/ttyACM0 --balance-port /dev/ttyUSB0 --out runs/selfcheck

    # or against an already-collected subset
    python -m characterization.selfcheck --calibration calibration/bench.json \\
        --runs runs/selfcheck
"""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from . import analyze, design as design_mod
from .sweep import SweepRunner, make_hardware

#: Tolerances. Deliberately loose: a self-check is meant to catch "this is
#: a different environment" and "something on the rig broke", not to
#: re-measure the noise floor. Tightening these without the replicates to
#: support them just produces flaky refusals.
DEFAULT_SIGMA_FACTOR = 2.5
DEFAULT_BIAS_SIGMAS = 5.0
DEFAULT_SETTLE_FACTOR = 3.0


@dataclass
class Check:
    name: str
    ok: bool
    detail: str

    def line(self) -> str:
        return "{}  {:<22} {}".format("PASS" if self.ok else "FAIL",
                                      self.name, self.detail)


def _mg(value: Optional[float]) -> str:
    return "n/a" if value is None else "{:.4f} mg".format(value * 1000.0)


def compare(calibration: dict, results: Sequence[analyze.ConditionResult],
            observed: dict,
            sigma_factor: float = DEFAULT_SIGMA_FACTOR,
            bias_sigmas: float = DEFAULT_BIAS_SIGMAS,
            settle_factor: float = DEFAULT_SETTLE_FACTOR) -> List[Check]:
    checks: List[Check] = []
    ref_sigma = calibration.get("noise_floor", {}).get("sigma0_g")
    new_sigma = observed.get("noise_floor", {}).get("sigma0_g")

    if ref_sigma is None or new_sigma is None:
        checks.append(Check("noise floor", False,
                            "missing sigma0 (reference {}, observed {})".format(
                                _mg(ref_sigma), _mg(new_sigma))))
    else:
        ratio = new_sigma / ref_sigma if ref_sigma else float("inf")
        checks.append(Check(
            "noise floor", ratio <= sigma_factor,
            "sigma0 {} vs reference {} ({:.2f}x, limit {:.1f}x)".format(
                _mg(new_sigma), _mg(ref_sigma), ratio, sigma_factor)))

    # Bias: ground truth is 0, so this is an absolute check, not a
    # comparison -- a blank run that reports mass is wrong regardless of
    # what the reference environment did.
    worst = None
    for result in results:
        if result.kind != "actuation":
            continue
        bias = result.bias_corrected.median
        if bias is None:
            continue
        if worst is None or abs(bias) > abs(worst[1]):
            worst = (result.condition, bias)
    if worst is None:
        checks.append(Check("blank bias", False, "no bias measured"))
    else:
        limit = (bias_sigmas * new_sigma) if new_sigma else None
        ok = limit is not None and abs(worst[1]) <= limit
        checks.append(Check(
            "blank bias", bool(ok),
            "worst {} on {} (limit {})".format(_mg(worst[1]), worst[0],
                                               _mg(limit))))

    ref_knee = calibration.get("settle_delay_curve", {}).get("knee_s")
    new_knee = observed.get("settle_delay_curve", {}).get("knee_s")
    if ref_knee and new_knee:
        ok = new_knee <= settle_factor * ref_knee
        checks.append(Check("settle time", ok,
                            "knee {:.2f} s vs reference {:.2f} s "
                            "(limit {:.1f}x)".format(new_knee, ref_knee,
                                                     settle_factor)))
    else:
        checks.append(Check("settle time", new_knee is not None,
                            "knee {} (reference {})".format(new_knee,
                                                            ref_knee)))

    never = observed.get("balance_stability_flag", {})
    fraction = never.get("never_flagged_fraction")
    checks.append(Check(
        "stability flag", bool(fraction is not None and fraction < 0.25),
        "{} of runs never flagged stable".format(
            "unknown" if fraction is None else "{:.0%}".format(fraction))))
    return checks


def run_subset(args, outdir: Path) -> Path:
    conditions = design_mod.selfcheck(context={
        "tare_load_g": args.tare_load_g, "isolation": args.isolation,
        "auger": "blank"})
    runs = design_mod.build_runlist(conditions, replicates=args.replicates,
                                    seed=args.seed, control_every=4,
                                    pre_s=args.pre_s, post_s=args.post_s)
    est = design_mod.estimate_duration_s(runs)
    print("self-check: {} runs, about {:.0f} min".format(len(runs), est / 60.0))
    rig, balance, runner_kwargs = make_hardware(args)
    runner = SweepRunner(rig, balance, outdir, tare_every=args.tare_every,
                         environment=args.environment or "unknown",
                         **runner_kwargs)
    try:
        runner.run(runs, manifest={"design": "selfcheck", "seed": args.seed,
                                   "replicates": args.replicates,
                                   "mock": bool(args.mock)})
    finally:
        balance.close()
        rig.close()
    return outdir


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--calibration", required=True, type=Path)
    ap.add_argument("--runs", type=Path, default=None,
                    help="use an existing subset instead of running one")
    ap.add_argument("--out", type=Path, default=None,
                    help="where to write the self-check runs")
    ap.add_argument("--replicates", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pre-s", type=float, default=3.0)
    ap.add_argument("--post-s", type=float, default=10.0)
    ap.add_argument("--tare-every", type=int, default=5)
    ap.add_argument("--environment", default=None)
    ap.add_argument("--tare-load-g", type=float, default=0.0)
    ap.add_argument("--isolation", default="none")
    ap.add_argument("--sigma-factor", type=float, default=DEFAULT_SIGMA_FACTOR)
    ap.add_argument("--bias-sigmas", type=float, default=DEFAULT_BIAS_SIGMAS)
    ap.add_argument("--settle-factor", type=float,
                    default=DEFAULT_SETTLE_FACTOR)
    ap.add_argument("--rig-port")
    ap.add_argument("--rig-baud", type=int, default=115200)
    ap.add_argument("--balance-port")
    ap.add_argument("--balance-baud", type=int, default=9600)
    ap.add_argument("--balance-format", default="mtsics")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-speedup", type=float, default=50.0)
    ap.add_argument("--mock-never-stable", action="store_true")
    ap.add_argument("--mock-noise-mg", type=float, default=0.02)
    ap.add_argument("--mock-tau-s", type=float, default=0.35)
    ap.add_argument("--mock-resonant-rpm", type=float, default=None)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    calibration = json.loads(Path(args.calibration).read_text())
    environment = args.environment or calibration.get("environment")

    tmp: Optional[tempfile.TemporaryDirectory] = None
    if args.runs:
        runs_dir = args.runs
    else:
        if args.out:
            runs_dir = args.out
        else:
            tmp = tempfile.TemporaryDirectory(prefix="selfcheck-")
            runs_dir = Path(tmp.name)
        run_subset(args, Path(runs_dir))

    try:
        records = analyze.load_runs(Path(runs_dir))
        criterion = calibration.get("criterion", {})
        delay = criterion.get("read_delay_s", 2.0)
        window = criterion.get("stable_window_s", analyze.DEFAULT_STABLE_WINDOW_S)
        tol = criterion.get("stable_tol_g", analyze.DEFAULT_STABLE_TOL_G)
        results = analyze.analyze_conditions(records, delay_s=delay,
                                             window_s=window, tol_g=tol)
        observed = analyze.build_calibration(
            records, environment or "unknown", results, delay, window, tol,
            analyze.load_manifest(Path(runs_dir)))
    finally:
        if tmp is not None:
            tmp.cleanup()

    ref_design = (calibration.get("manifest") or {}).get("design")
    if ref_design and ref_design != "selfcheck":
        # Not fatal, but worth saying out loud: sigma0 comes from the
        # interleaved controls, and controls sitting next to a tap
        # condition pick up its reseat steps. Comparing a self-check
        # against a reference built from a different mix of conditions
        # produces failures that are about the design, not the room.
        print("\nnote: reference calibration was built from design {!r}, not "
              "'selfcheck'.\n      Thresholds compare best against a "
              "reference collected the same way.".format(ref_design))

    checks = compare(calibration, results, observed,
                     sigma_factor=args.sigma_factor,
                     bias_sigmas=args.bias_sigmas,
                     settle_factor=args.settle_factor)
    print("\nself-check against {} (environment {!r})".format(
        args.calibration, environment))
    for check in checks:
        print("  " + check.line())
    failed = [c for c in checks if not c.ok]
    if failed:
        print("\n{} check(s) failed -- DO NOT DISPENSE. Re-run the full "
              "characterization for this environment:\n  python -m "
              "characterization.sweep --design screen --environment {}".format(
                  len(failed), environment))
        return 1
    print("\nall checks passed; stored calibration still applies")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

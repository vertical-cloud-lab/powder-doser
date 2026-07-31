"""Run a blank-auger sweep and log raw + stable balance data.

One run is: tare (periodically), record a quiet baseline, fire the
condition's actuation, then keep recording well past the point where the
balance claims to be settled.  Everything the balance emits is written to
disk, both channels, at full rate -- the stable flag is recorded, never
used to decide what to keep.  That is what allows the stability criterion
to be re-tuned offline later without re-running the rig, which for a
multi-thousand-run sweep is the difference between a bug and a lost week.

Usage::

    # dry run, no hardware
    python -m characterization.sweep --mock --design selfcheck --out runs/mock

    # real rig
    python -m characterization.sweep \
        --rig-port /dev/ttyACM0 --balance-port /dev/ttyUSB0 \
        --balance-format mtsics --design screen --replicates 20 \
        --environment bench --out runs/2026-07-31-bench

Outputs, under ``--out``:

``manifest.json``  design, seed, environment, git commit, run count
``runs.csv``       one tidy row per run (parameters + quick-look metrics)
``traces/*.csv``   the full raw stream for every run, one file per run
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from . import design as design_mod
from . import robust
from .balance import Balance, Reading, SerialBalance
from .design import Condition, Run
from .rig import Rig, RigError, SerialRig

TRACE_FIELDS = ("t_rel", "grams", "stable", "phase", "raw")

RUN_FIELDS = (
    "run_id", "index", "wall_clock", "condition", "kind", "replicate",
    "actions", "environment", "notes", "context", "params",
    "t_trace_start", "t_pre_end", "t_act_start", "t_act_end",
    "n_samples", "sample_hz",
    "pre_median_g", "post_median_g", "delta_median_g", "delta_last_stable_g",
    "post_p2p_g", "first_stable_after_act_s", "never_stable",
    "device_est_ms", "device_duration_s", "tared", "error",
)


class Recorder:
    """Background reader that timestamps and phase-labels the stream.

    The balance streams continuously and independently of the rig, so the
    only honest way to know when something happened relative to the trace
    is to keep reading throughout and mark the boundaries on the same host
    clock.  Deriving the actuation window from the rig's own reported
    timing would inherit the firmware's estimated-move-time uncertainty.
    """

    def __init__(self, balance: Balance, sleep=time.sleep):
        self.balance = balance
        self.sleep = sleep
        self._readings: List[Reading] = []
        self._phases: List[str] = []
        self._phase = "idle"
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.error: Optional[BaseException] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="balance-reader")
        self._thread.start()

    def _loop(self) -> None:
        try:
            for reading in self.balance.readings():
                with self._lock:
                    self._readings.append(reading)
                    self._phases.append(self._phase)
                if self._stop.is_set():
                    return
        except Exception as exc:  # surfaced by the runner, not swallowed
            self.error = exc

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    def set_phase(self, phase: str) -> None:
        with self._lock:
            self._phase = phase

    def reset(self) -> None:
        with self._lock:
            self._readings = []
            self._phases = []

    def snapshot(self):
        with self._lock:
            return list(self._readings), list(self._phases)

    def wait(self, seconds: float, phase: Optional[str] = None) -> None:
        if phase is not None:
            self.set_phase(phase)
        if seconds > 0:
            self.sleep(seconds)


def _git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or "unknown"
    except Exception:  # pragma: no cover - not a git checkout
        return "unknown"


@dataclass
class RunResult:
    row: Dict[str, object]
    readings: List[Reading]
    phases: List[str]


class SweepRunner:
    def __init__(self, rig: Rig, balance: Balance, outdir: Path,
                 tare_every: int = 10, settle_s: float = 0.0,
                 environment: str = "unknown", verbose: bool = True,
                 clock=time.monotonic, sleep=time.sleep):
        # ``clock``/``sleep`` are injected so the simulator can compress
        # wall clock without distorting the recorded timeline: it sleeps
        # speedup-times faster but reports unscaled seconds, keeping mock
        # traces directly comparable to hardware traces.
        self.clock = clock
        self.sleep = sleep
        self.rig = rig
        self.balance = balance
        self.outdir = Path(outdir)
        self.tare_every = tare_every
        self.settle_s = settle_s
        self.environment = environment
        self.verbose = verbose
        self.recorder = Recorder(balance, sleep=sleep)
        self._runs_since_tare = 10 ** 9  # force a tare before the first run

    # -- plumbing --------------------------------------------------------
    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def _apply(self, condition: Condition) -> Dict[str, object]:
        """Push parameters, then read back what the rig says it has."""
        self.rig.reset_params()
        for name, value in sorted(condition.params.items()):
            self.rig.set_param(name, value)
        return self.rig.params()

    def _actuate(self, run: Run) -> Dict[str, object]:
        info: Dict[str, object] = {}
        for action in run.condition.actions:
            if action == "none":
                # A control still occupies the actuation window, so its
                # ambient sample covers the same span as a real run.
                self.sleep(run.dwell_s)
                continue
            if action == "dispense":
                ack = self.rig.dispense()
            elif action == "vibrate":
                ack = self.rig.vibrate()
            elif action == "tap":
                ack = self.rig.tap()
            elif action == "servo":
                # Out and back, so the servo ends where it started and
                # successive runs are not confounded by a changing angle.
                start = 90.0
                self.rig.servo(start + 45.0)
                ack = self.rig.servo(start)
            else:  # pragma: no cover - guarded by Condition.validated
                raise ValueError("unknown action {!r}".format(action))
            info["device_est_ms"] = ack.est_ms
            info["device_duration_s"] = ack.device_duration_s
        return info

    # -- one run ---------------------------------------------------------
    def run_one(self, run: Run) -> RunResult:
        tared = False
        if self.tare_every > 0 and self._runs_since_tare >= self.tare_every:
            self.balance.tare()
            self._runs_since_tare = 0
            tared = True
            self.sleep(min(2.0, run.pre_s))
        self._runs_since_tare += 1

        params = self._apply(run.condition)
        self.recorder.reset()

        t_start = self.clock()
        self.recorder.wait(run.pre_s, phase="pre")
        t_pre_end = self.clock()

        error = ""
        info: Dict[str, object] = {}
        self.recorder.set_phase("act")
        try:
            info = self._actuate(run)
        except RigError as exc:
            # Record and continue: one bad condition should not end the
            # night, but it must not masquerade as a clean measurement.
            error = str(exc)
            self._log("  !! {}".format(exc))
        t_act_end = self.clock()

        self.recorder.wait(run.post_s, phase="post")
        self.recorder.set_phase("idle")

        readings, phases = self.recorder.snapshot()
        if self.recorder.error is not None:
            raise RuntimeError("balance reader failed: {!r}".format(
                self.recorder.error))

        row = self._summarize(run, params, readings, phases, t_start,
                              t_pre_end, t_act_end, info, tared, error)
        return RunResult(row=row, readings=readings, phases=phases)

    def _summarize(self, run: Run, params: Dict[str, object],
                   readings: Sequence[Reading], phases: Sequence[str],
                   t_start: float, t_pre_end: float, t_act_end: float,
                   info: Dict[str, object], tared: bool,
                   error: str) -> Dict[str, object]:
        pre = [r.grams for r, p in zip(readings, phases) if p == "pre"]
        post = [r.grams for r, p in zip(readings, phases) if p == "post"]
        post_stable = [r.grams for r, p in zip(readings, phases)
                       if p == "post" and r.stable]
        first_stable = None
        for reading, phase in zip(readings, phases):
            if phase == "post" and reading.stable:
                first_stable = reading.t - t_act_end
                break
        pre_median = robust.median(pre)
        post_median = robust.median(post)
        span = readings[-1].t - readings[0].t if len(readings) > 1 else 0.0
        return {
            "run_id": run.run_id,
            "index": run.index,
            "wall_clock": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "condition": run.condition.name,
            "kind": run.kind,
            "replicate": run.replicate,
            "actions": "|".join(run.condition.actions),
            "environment": self.environment,
            "notes": run.condition.notes,
            "context": json.dumps(run.condition.context, sort_keys=True),
            "params": json.dumps(params, sort_keys=True),
            # Traces are written with t relative to their own first sample;
            # this is that sample's offset from t_start, so the analysis can
            # place the actuation window in trace coordinates exactly.
            "t_trace_start": (round(readings[0].t - t_start, 4)
                              if readings else 0.0),
            "t_pre_end": round(t_pre_end - t_start, 4),
            "t_act_start": round(t_pre_end - t_start, 4),
            "t_act_end": round(t_act_end - t_start, 4),
            "n_samples": len(readings),
            "sample_hz": round(len(readings) / span, 3) if span > 0 else "",
            "pre_median_g": pre_median,
            "post_median_g": post_median,
            "delta_median_g": (None if pre_median is None or post_median is None
                               else post_median - pre_median),
            "delta_last_stable_g": (post_stable[-1] - pre_median
                                    if post_stable and pre_median is not None
                                    else None),
            "post_p2p_g": robust.peak_to_peak(post),
            "first_stable_after_act_s": first_stable,
            "never_stable": int(first_stable is None),
            "device_est_ms": info.get("device_est_ms", ""),
            "device_duration_s": info.get("device_duration_s", ""),
            "tared": int(tared),
            "error": error,
        }

    # -- the sweep -------------------------------------------------------
    def run(self, runs: Sequence[Run], manifest: Optional[dict] = None) -> Path:
        self.outdir.mkdir(parents=True, exist_ok=True)
        traces = self.outdir / "traces"
        traces.mkdir(exist_ok=True)
        (self.outdir / "manifest.json").write_text(json.dumps({
            "environment": self.environment,
            "git_commit": _git_commit(),
            "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "n_runs": len(runs),
            "tare_every": self.tare_every,
            "estimated_seconds": round(
                design_mod.estimate_duration_s(runs, self.settle_s), 1),
            **(manifest or {}),
        }, indent=2, sort_keys=True) + "\n")

        runs_csv = self.outdir / "runs.csv"
        self.recorder.start()
        n_errors = 0
        try:
            with runs_csv.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=RUN_FIELDS)
                writer.writeheader()
                for position, run in enumerate(runs, start=1):
                    self._log("[{}/{}] {} {} rep={}".format(
                        position, len(runs), run.run_id, run.condition.name,
                        run.replicate))
                    result = self.run_one(run)
                    writer.writerow(result.row)
                    # Flush per run: an overnight sweep that dies at 4 a.m.
                    # should still yield everything up to 4 a.m.
                    handle.flush()
                    self._write_trace(traces / "{}.csv".format(run.run_id),
                                      result)
                    n_errors += 1 if result.row["error"] else 0
        except KeyboardInterrupt:
            self._log("\ninterrupted; partial results kept in {}".format(
                self.outdir))
        finally:
            self.recorder.stop()
            try:
                self.rig.stop()
            except Exception:  # pragma: no cover - best-effort teardown
                pass
        if n_errors:
            self._log("{} run(s) recorded a rig error; see the error column"
                      .format(n_errors))
        return runs_csv

    @staticmethod
    def _write_trace(path: Path, result: RunResult) -> None:
        readings, phases = result.readings, result.phases
        t0 = readings[0].t if readings else 0.0
        with path.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(TRACE_FIELDS)
            for reading, phase in zip(readings, phases):
                writer.writerow([
                    "{:.4f}".format(reading.t - t0),
                    "{:.7f}".format(reading.grams),
                    int(reading.stable), phase, reading.raw,
                ])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_conditions(args) -> List[Condition]:
    context = {"tare_load_g": args.tare_load_g,
               "isolation": args.isolation,
               "auger": args.auger}
    if args.design == "screen":
        conditions = design_mod.screening(context=context)
    elif args.design == "rpm-scan":
        conditions = design_mod.rpm_scan(lo=args.rpm_lo, hi=args.rpm_hi,
                                         step=args.rpm_step, context=context)
    elif args.design == "selfcheck":
        conditions = design_mod.selfcheck(context=context)
    else:  # pragma: no cover - argparse restricts the choices
        raise ValueError(args.design)
    return conditions


def make_hardware(args):
    """Return ``(rig, balance, runner_kwargs)`` for the requested backend."""
    if args.mock:
        from .mock import SimConfig, make_mock
        cfg = SimConfig(noise_g=args.mock_noise_mg * 1e-3,
                        base_tau_s=args.mock_tau_s)
        if args.mock_resonant_rpm:
            # Step frequency is rpm/60 * full_steps * microsteps; the
            # simulated structure resonates at that frequency, so a scan
            # that steps over it will miss the band exactly as a real one
            # would.
            steps_per_rev = 200 * 8
            cfg.resonant_step_hz = (args.mock_resonant_rpm / 60.0
                                    * steps_per_rev,)
        rig, balance, sim = make_mock(speedup=args.mock_speedup, cfg=cfg,
                                      never_stable=args.mock_never_stable)
        return rig, balance, {"clock": sim.now, "sleep": sim.sleep}
    if not args.rig_port or not args.balance_port:
        raise SystemExit("--rig-port and --balance-port are required "
                         "unless --mock is given")
    rig = SerialRig(args.rig_port, args.rig_baud)
    balance = SerialBalance(args.balance_port, args.balance_baud,
                            fmt=args.balance_format).open()
    return rig, balance, {}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path,
                    help="output directory")
    ap.add_argument("--design", default="screen",
                    choices=sorted(design_mod.DESIGNS))
    ap.add_argument("--replicates", type=int, default=20,
                    help="replicates per condition (SD of an SD is about "
                         "sigma/sqrt(2(n-1)); n=20 pins sigma to ~+/-16%%)")
    ap.add_argument("--seed", type=int, default=0,
                    help="run-order seed; recorded in the manifest")
    ap.add_argument("--control-every", type=int, default=10,
                    help="insert a do-nothing control every N runs (0 to "
                         "disable, which is almost always a mistake)")
    ap.add_argument("--pre-s", type=float, default=3.0)
    ap.add_argument("--post-s", type=float, default=10.0)
    ap.add_argument("--tare-every", type=int, default=10)
    ap.add_argument("--environment", default="bench",
                    help="label for this environment, e.g. bench, glovebox")
    ap.add_argument("--tare-load-g", type=float, default=0.0,
                    help="dummy mass on the pan, recorded with every run")
    ap.add_argument("--isolation", default="none",
                    help="isolation state, e.g. none, sorbothane, separate-stand")
    ap.add_argument("--auger", default="blank",
                    help="auger/tube state: blank, dummy-load, powder")
    ap.add_argument("--rpm-lo", type=float, default=5.0)
    ap.add_argument("--rpm-hi", type=float, default=300.0)
    ap.add_argument("--rpm-step", type=float, default=5.0)
    ap.add_argument("--rig-port")
    ap.add_argument("--rig-baud", type=int, default=115200)
    ap.add_argument("--balance-port")
    ap.add_argument("--balance-baud", type=int, default=9600)
    ap.add_argument("--balance-format", default="mtsics")
    ap.add_argument("--mock", action="store_true",
                    help="run against the simulator, no hardware")
    ap.add_argument("--mock-speedup", type=float, default=50.0)
    ap.add_argument("--mock-never-stable", action="store_true",
                    help="simulate a balance whose stability flag never "
                         "fires (the glovebox failure mode)")
    ap.add_argument("--mock-noise-mg", type=float, default=0.02,
                    help="simulated white-noise sigma, mg")
    ap.add_argument("--mock-tau-s", type=float, default=0.35,
                    help="simulated ringdown time constant, s")
    ap.add_argument("--mock-resonant-rpm", type=float, default=None,
                    help="plant a structural resonance at this auger speed")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the run plan and estimated duration, then exit")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    conditions = build_conditions(args)
    runs = design_mod.build_runlist(
        conditions, replicates=args.replicates, seed=args.seed,
        control_every=args.control_every, pre_s=args.pre_s, post_s=args.post_s)
    est_s = design_mod.estimate_duration_s(runs)
    print("{} condition(s), {} run(s), estimated {:.1f} h".format(
        len(conditions), len(runs), est_s / 3600.0))
    if args.dry_run:
        for run in runs[:20]:
            print("  {} {:<28} rep={} {}".format(
                run.run_id, run.condition.name, run.replicate, run.kind))
        if len(runs) > 20:
            print("  ... {} more".format(len(runs) - 20))
        return 0

    rig, balance, runner_kwargs = make_hardware(args)
    runner = SweepRunner(rig, balance, args.out, tare_every=args.tare_every,
                         environment=args.environment, **runner_kwargs)
    manifest = {
        "design": args.design, "seed": args.seed,
        "replicates": args.replicates, "control_every": args.control_every,
        "tare_load_g": args.tare_load_g, "isolation": args.isolation,
        "auger": args.auger, "mock": bool(args.mock),
        "balance_format": args.balance_format,
    }
    try:
        path = runner.run(runs, manifest=manifest)
    finally:
        balance.close()
        rig.close()
    print("wrote {}".format(path))
    print("next: python -m characterization.analyze --runs {} "
          "--environment {}".format(args.out, args.environment))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""Analyse a blank-auger sweep and emit a per-environment calibration.

Ground truth for every run is Delta m = 0, so three quantities fall out,
all directly interpretable:

**Bias** (median apparent Delta m).  Nonzero means *systematic* coupling,
not noise -- almost always mechanical (tube touching the cup rim, a cable
tugging the pan, the cup reseating after a solenoid tap, air currents,
static).  It is invisible in powder runs, where it is silently absorbed
into "how much powder came out", which is why it is the highest-value
number here.

**Precision** (spread across replicates).  sigma_0 sets LOD ~ 3 sigma_0 and
LOQ ~ 10 sigma_0 -- the smallest dose that can honestly be claimed.

**Settling** (ringdown from the raw stream).  Decides whether weigh-in-
motion is viable at all and what stop-and-weigh costs per increment.

Two things this module does that a naive analysis would not:

* **It recomputes stability offline** with its own criterion instead of
  trusting the balance's stable flag, and reports both.  The flag is a
  black box tuned for a quiet bench; the two failure modes that matter --
  declaring stable at a biased value, and never declaring stable at all --
  are only visible when the two are compared.
* **It subtracts the interleaved controls.**  Ambient drift is not small,
  especially in a glovebox, and un-subtracted it is attributed to whatever
  factor happened to be swept.

Usage::

    python -m characterization.analyze --runs runs/2026-07-31-bench \\
        --environment bench --out calibration/bench.json
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from . import robust

#: Offline stability criterion.  A window this long whose peak-to-peak
#: spread stays within the tolerance counts as settled.  Both are recorded
#: in the calibration artefact -- a settle time is meaningless without the
#: criterion that produced it.
DEFAULT_STABLE_WINDOW_S = 1.0
DEFAULT_STABLE_TOL_G = 5e-5

#: Delays (s after actuation ends) at which the settle-delay-vs-sigma
#: curve is evaluated.
DEFAULT_DELAYS_S = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)

#: How close to the sigma floor counts as "waiting no longer helps".
KNEE_TOLERANCE = 1.25

#: A level is flagged as a bad band when its robust sigma exceeds the
#: design's own floor by this factor.
BAND_SIGMA_FACTOR = 2.5

#: Minimum number of distinct RPM levels before band detection will report
#: anything.  A screen with three levels can produce a "band" covering the
#: entire swept range, which reads as a finding and is not one.
MIN_BAND_LEVELS = 5


@dataclass
class Sample:
    t: float
    grams: float
    stable: bool
    phase: str


@dataclass
class RunRecord:
    row: Dict[str, str]
    trace: List[Sample] = field(default_factory=list)

    @property
    def run_id(self) -> str:
        return self.row["run_id"]

    @property
    def condition(self) -> str:
        return self.row["condition"]

    @property
    def kind(self) -> str:
        return self.row["kind"]

    @property
    def index(self) -> int:
        return int(self.row["index"])

    @property
    def params(self) -> Dict[str, object]:
        return json.loads(self.row.get("params") or "{}")

    @property
    def act_end(self) -> float:
        """Actuation end, in this trace's own time coordinates."""
        return (_float(self.row.get("t_act_end"), 0.0)
                - _float(self.row.get("t_trace_start"), 0.0))

    @property
    def act_start(self) -> float:
        return (_float(self.row.get("t_act_start"), 0.0)
                - _float(self.row.get("t_trace_start"), 0.0))


def _float(value, default=None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_runs(directory: Path) -> List[RunRecord]:
    directory = Path(directory)
    runs_csv = directory / "runs.csv"
    if not runs_csv.exists():
        raise FileNotFoundError("no runs.csv in {}".format(directory))
    records: List[RunRecord] = []
    with runs_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            record = RunRecord(row=row)
            trace_path = directory / "traces" / "{}.csv".format(row["run_id"])
            if trace_path.exists():
                record.trace = load_trace(trace_path)
            records.append(record)
    return records


def load_trace(path: Path) -> List[Sample]:
    samples: List[Sample] = []
    with Path(path).open(newline="") as handle:
        for row in csv.DictReader(handle):
            t = _float(row.get("t_rel"))
            grams = _float(row.get("grams"))
            if t is None or grams is None:
                continue
            samples.append(Sample(t=t, grams=grams,
                                  stable=row.get("stable") in ("1", "True",
                                                               "true"),
                                  phase=row.get("phase", "")))
    return samples


# ---------------------------------------------------------------------------
# Per-run metrics from the raw trace
# ---------------------------------------------------------------------------

def value_at_delay(record: RunRecord, delay_s: float,
                   average_s: float = 0.5) -> Optional[float]:
    """Apparent mass ``delay_s`` after actuation, relative to baseline.

    Averaged over a short window rather than read from one sample, which
    is what a real controller would do, and referenced to the pre-actuation
    median so the answer is a Delta m whose truth value is 0.
    """
    baseline = robust.median([s.grams for s in record.trace
                              if s.phase == "pre"])
    if baseline is None:
        return None
    t0 = record.act_end + delay_s
    window = [s.grams for s in record.trace if t0 <= s.t <= t0 + average_s]
    if not window:
        return None
    value = robust.median(window)
    return None if value is None else value - baseline


def settle_time(record: RunRecord, window_s: float = DEFAULT_STABLE_WINDOW_S,
                tol_g: float = DEFAULT_STABLE_TOL_G) -> Optional[float]:
    """Seconds after actuation until an offline stability window holds.

    ``None`` means it never settled within the recorded window -- which is
    a result, not a missing value, and is counted separately rather than
    dropped.
    """
    post = [s for s in record.trace if s.t >= record.act_end]
    if not post:
        return None
    for i, sample in enumerate(post):
        window = [s.grams for s in post[i:] if s.t <= sample.t + window_s]
        if not window or post[-1].t < sample.t + window_s:
            return None  # ran out of trace before the window could close
        if max(window) - min(window) <= tol_g:
            return sample.t - record.act_end
    return None


def flag_latency(record: RunRecord) -> Optional[float]:
    """Seconds after actuation until the *balance* claims stability."""
    for sample in record.trace:
        if sample.t >= record.act_end and sample.stable:
            return sample.t - record.act_end
    return None


def excursion(record: RunRecord) -> Optional[float]:
    """Peak-to-peak excursion during and after actuation."""
    values = [s.grams for s in record.trace if s.t >= record.act_start]
    return robust.peak_to_peak(values)


def persistent_step(record: RunRecord, tail_s: float = 3.0) -> Optional[float]:
    """Baseline shift measured from the last ``tail_s`` of the trace.

    A step that survives to the end of the recording is the artefact that
    most convincingly imitates real mass: it is stable, repeatable within a
    run, and completely fictitious.  Solenoid taps are the usual culprit
    (the cup or pan reseating).
    """
    if not record.trace:
        return None
    baseline = robust.median([s.grams for s in record.trace
                              if s.phase == "pre"])
    end = record.trace[-1].t
    tail = [s.grams for s in record.trace if s.t >= end - tail_s]
    tail_median = robust.median(tail)
    if baseline is None or tail_median is None:
        return None
    return tail_median - baseline


# ---------------------------------------------------------------------------
# Control (drift) correction
# ---------------------------------------------------------------------------

def _interpolate(points: Sequence[Tuple[int, float]],
                 index: int) -> Optional[float]:
    """Linear interpolation over ``(run_index, value)``, held at the ends.

    Outside the first/last control the nearest value is held rather than
    extrapolated -- extrapolated drift is a guess dressed as a measurement.
    """
    if not points:
        return None
    if index <= points[0][0]:
        return points[0][1]
    if index >= points[-1][0]:
        return points[-1][1]
    for (i0, v0), (i1, v1) in zip(points, points[1:]):
        if i0 <= index <= i1:
            frac = (index - i0) / (i1 - i0) if i1 != i0 else 0.0
            return v0 + frac * (v1 - v0)
    return None


def control_baseline(records: Sequence[RunRecord], delay_s: float,
                     average_s: float = 0.5) -> Dict[int, float]:
    """Interpolated ambient term as a function of run index.

    Controls are interleaved throughout the night; between two of them the
    ambient term is approximated linearly.

    A control is corrected using the *other* controls, never itself.
    Self-correction would drive every control residual to exactly zero and
    report a noise floor of 0 -- an absurd answer that would nonetheless
    propagate silently into LOD, LOQ and the self-check gate.  The
    leave-one-out residual is instead a genuine estimate of how well the
    ambient term is being tracked; it is inflated by roughly sqrt(1.5) for
    an evenly spaced midpoint, which errs toward a conservative LOD.
    """
    points: List[Tuple[int, float]] = []
    for record in records:
        if record.kind != "control":
            continue
        value = value_at_delay(record, delay_s, average_s)
        if value is not None:
            points.append((record.index, value))
    points.sort()
    if not points:
        return {}
    out: Dict[int, float] = {}
    for record in records:
        usable = ([p for p in points if p[0] != record.index]
                  if record.kind == "control" else points)
        value = _interpolate(usable, record.index)
        if value is not None:
            out[record.index] = value
    return out


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

@dataclass
class ConditionResult:
    condition: str
    kind: str
    n: int
    params: Dict[str, object]
    bias: robust.Summary
    bias_corrected: robust.Summary
    settle: robust.Summary
    flag_latency: robust.Summary
    excursion: robust.Summary
    step: robust.Summary
    never_settled: int
    never_flagged: int
    errors: int

    @property
    def sigma(self) -> Optional[float]:
        return self.bias_corrected.robust_sigma

    @property
    def lod_g(self) -> Optional[float]:
        return None if self.sigma is None else 3.0 * self.sigma

    @property
    def loq_g(self) -> Optional[float]:
        return None if self.sigma is None else 10.0 * self.sigma

    def as_dict(self) -> dict:
        return {
            "condition": self.condition,
            "kind": self.kind,
            "n": self.n,
            "params": self.params,
            "bias_g": self.bias.as_dict(),
            "bias_control_corrected_g": self.bias_corrected.as_dict(),
            "settle_s": self.settle.as_dict(),
            "balance_flag_latency_s": self.flag_latency.as_dict(),
            "excursion_g": self.excursion.as_dict(),
            "persistent_step_g": self.step.as_dict(),
            "never_settled": self.never_settled,
            "never_flagged_stable": self.never_flagged,
            "rig_errors": self.errors,
            "sigma_g": self.sigma,
            "lod_g": self.lod_g,
            "loq_g": self.loq_g,
        }


def analyze_conditions(records: Sequence[RunRecord],
                       delay_s: float = 2.0,
                       window_s: float = DEFAULT_STABLE_WINDOW_S,
                       tol_g: float = DEFAULT_STABLE_TOL_G
                       ) -> List[ConditionResult]:
    controls = control_baseline(records, delay_s)
    grouped: Dict[str, List[RunRecord]] = {}
    for record in records:
        grouped.setdefault(record.condition, []).append(record)

    results: List[ConditionResult] = []
    for condition, group in grouped.items():
        biases, corrected, settles, latencies = [], [], [], []
        excursions, steps = [], []
        never_settled = never_flagged = errors = 0
        for record in group:
            if record.row.get("error"):
                errors += 1
            value = value_at_delay(record, delay_s)
            if value is not None:
                biases.append(value)
                drift = controls.get(record.index)
                corrected.append(value - drift if drift is not None else value)
            settle = settle_time(record, window_s, tol_g)
            if settle is None:
                never_settled += 1
            else:
                settles.append(settle)
            latency = flag_latency(record)
            if latency is None:
                never_flagged += 1
            else:
                latencies.append(latency)
            exc = excursion(record)
            if exc is not None:
                excursions.append(exc)
            step = persistent_step(record)
            if step is not None:
                steps.append(step)
        results.append(ConditionResult(
            condition=condition, kind=group[0].kind, n=len(group),
            params=group[0].params,
            bias=robust.summarize(biases),
            bias_corrected=robust.summarize(corrected),
            settle=robust.summarize(settles),
            flag_latency=robust.summarize(latencies),
            excursion=robust.summarize(excursions),
            step=robust.summarize(steps),
            never_settled=never_settled, never_flagged=never_flagged,
            errors=errors))
    results.sort(key=lambda r: (r.kind != "control", _natural_key(r.condition)))
    return results


def _natural_key(name: str):
    """Sort ``stepper_rpm=20`` before ``stepper_rpm=100``.

    Plain lexicographic order interleaves swept levels (20, 100, 140, 200,
    40, ...), which makes a scan's report unreadable exactly where reading
    it in order is the point.
    """
    import re

    parts = re.split(r"(-?\d+\.?\d*)", name)
    return tuple((1, float(p)) if i % 2 else (0, p)
                 for i, p in enumerate(parts))


def settle_delay_curve(records: Sequence[RunRecord],
                       delays_s: Sequence[float] = DEFAULT_DELAYS_S
                       ) -> Dict[str, object]:
    """sigma of the reported mass as a function of how long you wait.

    The deliverable is the curve and its knee, not a single settle time:
    waiting longer always helps a little, and the operational question is
    where it stops helping enough to pay for.
    """
    actuation = [r for r in records if r.kind == "actuation"]
    curve = []
    for delay in delays_s:
        values = [v for v in (value_at_delay(r, delay) for r in actuation)
                  if v is not None]
        summary = robust.summarize(values)
        curve.append({"delay_s": delay, "n": summary.n,
                      "sigma_g": summary.robust_sigma,
                      "bias_g": summary.median})
    sigmas = [(c["delay_s"], c["sigma_g"]) for c in curve
              if c["sigma_g"] is not None]
    if not sigmas:
        return {"curve": curve, "knee_s": None, "knee_limit_g": None,
                "knee_from_floor": None,
                "note": "no usable readings; no knee"}

    # The knee is the shortest wait past which waiting longer never helps
    # materially: every *subsequent* delay must also be within tolerance.
    # Taking the first delay that dips below the threshold would let one
    # lucky sample set the operating point, and a sigma estimated from a
    # handful of replicates dips readily.
    #
    # The tolerance widens with that estimator's own uncertainty
    # (SE(sigma) ~ sigma/sqrt(2(n-1))): demanding 25 % flatness from an
    # n=6 sigma, which is itself only known to about +/-32 %, would just
    # report "never settles" for a curve that is already flat.
    n_min = min((c["n"] for c in curve if c["sigma_g"] is not None),
                default=0)
    rel_se = robust.sigma_rel_se(n_min) or 0.0
    tolerance = 1.0 + max(KNEE_TOLERANCE - 1.0, 2.0 * rel_se)
    floor = min(s for _, s in sigmas)
    limit = tolerance * floor
    knee = None
    for i, (delay, _sigma) in enumerate(sigmas):
        if all(s <= limit for _, s in sigmas[i:]):
            knee = delay
            break
    from_floor = knee is None
    if from_floor:
        # The curve never flattened within tolerance, so report the delay
        # that achieved the best precision instead of nothing -- flagged,
        # because it is "best observed", not "settled".
        knee = min(sigmas, key=lambda item: item[1])[0]
    return {"curve": curve, "knee_s": knee, "knee_limit_g": limit,
            "knee_from_floor": from_floor,
            "note": ("knee = shortest delay past which sigma stays within "
                     "{:.2f}x its floor".format(tolerance)
                     + ("; curve never flattened, so this is the "
                        "best-observed delay" if from_floor else ""))}


def forbidden_rpm_bands(results: Sequence[ConditionResult],
                        factor: float = BAND_SIGMA_FACTOR
                        ) -> Dict[str, object]:
    """RPM levels whose sigma or bias stands out, merged into bands.

    Step frequency is ``rpm/60 * steps_per_rev``, and structural
    resonances are hit in bands rather than monotonically -- so the useful
    output is a list of ranges to forbid, not a "best RPM".
    """
    points = []
    for result in results:
        if result.kind != "actuation":
            continue
        rpm = result.params.get("stepper_rpm")
        if rpm is None or result.sigma is None:
            continue
        points.append((float(rpm), result.sigma,
                       result.bias_corrected.median, result.n))
    if len(points) < MIN_BAND_LEVELS:
        # Fewer levels than this cannot distinguish a band from a trend,
        # and a "forbidden band" spanning the whole swept range is worse
        # than no answer. Run ``--design rpm-scan`` for this output.
        return {"floor_sigma_g": None, "bands": [], "levels": [],
                "note": "need at least {} RPM levels; got {}".format(
                    MIN_BAND_LEVELS, len(points))}
    points.sort()
    sigmas = [p[1] for p in points]
    # Floor = the quietest quartile of levels, so a design where most RPMs
    # are bad does not define its own badness away.
    floor = robust.quantile(sigmas, 0.25) or min(sigmas)
    bands: List[Dict[str, float]] = []
    rpms = [p[0] for p in points]
    last_flagged = None
    for i, (rpm, sigma, bias, n) in enumerate(points):
        if sigma <= factor * floor:
            continue
        # Widen to the neighbouring levels: the true resonance sits
        # somewhere between the sampled points, not exactly on one.
        lo = rpms[i - 1] if i > 0 else rpm
        hi = rpms[i + 1] if i + 1 < len(rpms) else rpm
        # Merge only *adjacent* flagged levels. Widened windows of two
        # levels with a quiet one between them touch at the shared
        # neighbour, and merging on that would swallow the quiet level.
        if bands and last_flagged == i - 1:
            bands[-1]["hi_rpm"] = max(bands[-1]["hi_rpm"], hi)
            bands[-1]["worst_sigma_g"] = max(bands[-1]["worst_sigma_g"], sigma)
        else:
            bands.append({"lo_rpm": lo, "hi_rpm": hi, "worst_sigma_g": sigma})
        last_flagged = i
    return {
        "floor_sigma_g": floor,
        "sigma_factor": factor,
        "bands": bands,
        "levels": [{"stepper_rpm": p[0], "sigma_g": p[1], "bias_g": p[2],
                    "n": p[3]} for p in points],
    }


# ---------------------------------------------------------------------------
# Calibration artefact
# ---------------------------------------------------------------------------

CALIBRATION_VERSION = 1


def build_calibration(records: Sequence[RunRecord], environment: str,
                      results: Sequence[ConditionResult],
                      delay_s: float, window_s: float, tol_g: float,
                      manifest: Optional[dict] = None) -> dict:
    controls = [r for r in results if r.kind == "control"]
    actuation = [r for r in results if r.kind == "actuation"]
    control_sigma = (controls[0].sigma if controls else None)
    # A control sigma of exactly zero means the estimate is degenerate --
    # too few controls, or a balance stuck on one value -- not a perfect
    # balance.  Trusting it would put LOD = 0 into the calibration.
    if not control_sigma:
        control_sigma = None
    sigmas = [r.sigma for r in actuation if r.sigma is not None]
    sigma0 = control_sigma if control_sigma is not None else (
        robust.median(sigmas) if sigmas else None)
    curve = settle_delay_curve(records)
    bands = forbidden_rpm_bands(actuation)
    flagged_never = sum(r.never_flagged for r in results)
    n_runs = sum(r.n for r in results)
    return {
        "schema": "powder-doser/blank-auger-calibration",
        "version": CALIBRATION_VERSION,
        "environment": environment,
        "manifest": manifest or {},
        "criterion": {
            "read_delay_s": delay_s,
            "stable_window_s": window_s,
            "stable_tol_g": tol_g,
            "note": ("settle times and sigma are only meaningful together "
                     "with this criterion; changing it changes them"),
        },
        "noise_floor": {
            "sigma0_g": sigma0,
            "source": "control" if control_sigma is not None else
                      "median of actuation conditions",
            "lod_g": None if sigma0 is None else 3.0 * sigma0,
            "loq_g": None if sigma0 is None else 10.0 * sigma0,
        },
        "settle_delay_curve": curve,
        "forbidden_rpm_bands": bands,
        "balance_stability_flag": {
            "never_flagged_runs": flagged_never,
            "never_flagged_fraction": (flagged_never / n_runs
                                       if n_runs else None),
            "warning": ("a balance that never flags stable stalls any "
                        "controller that waits on it"),
        },
        "conditions": [r.as_dict() for r in results],
    }


def load_manifest(directory: Path) -> dict:
    path = Path(directory) / "manifest.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _fmt_mg(value: Optional[float]) -> str:
    return "     -" if value is None else "{:>6.3f}".format(value * 1000.0)


def _fmt_s(value: Optional[float]) -> str:
    return "    -" if value is None else "{:>5.2f}".format(value)


def format_report(calibration: dict,
                  results: Sequence[ConditionResult]) -> str:
    lines: List[str] = []
    floor = calibration["noise_floor"]
    lines.append("environment: {}".format(calibration["environment"]))
    lines.append("noise floor sigma0 = {} mg  (LOD {} mg, LOQ {} mg) [{}]"
                 .format(_fmt_mg(floor["sigma0_g"]).strip(),
                         _fmt_mg(floor["lod_g"]).strip(),
                         _fmt_mg(floor["loq_g"]).strip(), floor["source"]))
    knee = calibration["settle_delay_curve"]["knee_s"]
    lines.append("settle-delay knee: {}".format(
        "{:.2f} s".format(knee) if knee is not None else "not reached"))
    bands = calibration["forbidden_rpm_bands"]["bands"]
    if bands:
        lines.append("forbidden RPM bands: " + ", ".join(
            "{:g}-{:g} (sigma {} mg)".format(
                b["lo_rpm"], b["hi_rpm"], _fmt_mg(b["worst_sigma_g"]).strip())
            for b in bands))
    else:
        lines.append("forbidden RPM bands: none detected")
    lines.append("")
    header = ("{:<30} {:>4} {:>7} {:>7} {:>7} {:>6} {:>6} {:>5}".format(
        "condition", "n", "bias", "sigma", "step", "settle", "flag", "!"))
    lines.append(header)
    lines.append("{:<30} {:>4} {:>7} {:>7} {:>7} {:>6} {:>6} {:>5}".format(
        "", "", "mg", "mg", "mg", "s", "s", ""))
    lines.append("-" * len(header))
    for result in results:
        lines.append("{:<30} {:>4} {} {} {} {} {} {:>5}".format(
            result.condition[:30], result.n,
            _fmt_mg(result.bias_corrected.median),
            _fmt_mg(result.sigma),
            _fmt_mg(result.step.median),
            _fmt_s(result.settle.median),
            _fmt_s(result.flag_latency.median),
            "{}/{}".format(result.never_settled, result.n)))
    lines.append("")
    lines.append("bias/sigma are control-corrected; 'step' is the shift still "
                 "present at the end of the trace")
    lines.append("'!' counts runs that never met the offline stability "
                 "criterion within the recorded window")
    return "\n".join(lines)


def write_plots(records: Sequence[RunRecord],
                calibration: dict, outdir: Path) -> List[Path]:
    """Optional plots; a no-op (with a note) when matplotlib is absent."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping plots "
              "(pip install matplotlib)")
        return []
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    curve = calibration["settle_delay_curve"]["curve"]
    xs = [c["delay_s"] for c in curve if c["sigma_g"] is not None]
    ys = [c["sigma_g"] * 1000.0 for c in curve if c["sigma_g"] is not None]
    if xs:
        fig, ax = plt.subplots(figsize=(5, 3.2))
        ax.plot(xs, ys, marker="o")
        knee = calibration["settle_delay_curve"]["knee_s"]
        if knee is not None:
            # Say which kind of knee it is: a curve that never flattened
            # reports its best-observed delay, which is a weaker claim.
            from_floor = calibration["settle_delay_curve"].get(
                "knee_from_floor")
            ax.axvline(knee, ls="--", color="0.5",
                       label="{} {:.2f} s".format(
                           "best observed" if from_floor else "knee", knee))
            ax.legend()
        ax.set_xscale("log")
        # Label only the delays actually sampled; the default log minor
        # ticks overprint each other into an unreadable smear.
        ax.set_xticks(xs)
        ax.set_xticklabels(["{:g}".format(x) for x in xs])
        ax.minorticks_off()
        ax.set_xlabel("read delay after actuation (s)")
        ax.set_ylabel(r"$\sigma$ (mg)")
        ax.set_title("Precision vs. how long you wait")
        fig.tight_layout()
        path = outdir / "settle-delay-curve.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        written.append(path)

    levels = calibration["forbidden_rpm_bands"].get("levels") or []
    if len(levels) >= 3:
        fig, ax = plt.subplots(figsize=(6, 3.2))
        ax.plot([l["stepper_rpm"] for l in levels],
                [l["sigma_g"] * 1000.0 for l in levels], marker="o")
        floor = calibration["forbidden_rpm_bands"].get("floor_sigma_g")
        if floor:
            ax.axhline(floor * 1000.0, ls=":", color="0.5", label="floor")
        for band in calibration["forbidden_rpm_bands"]["bands"]:
            ax.axvspan(band["lo_rpm"], band["hi_rpm"], color="tab:red",
                       alpha=0.15)
        ax.set_xlabel("auger speed (RPM)")
        ax.set_ylabel(r"$\sigma$ (mg)")
        ax.set_title("Noise vs. RPM (shaded = flagged bands)")
        fig.tight_layout()
        path = outdir / "rpm-bands.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", required=True, type=Path,
                    help="sweep output directory (containing runs.csv)")
    ap.add_argument("--environment", default=None,
                    help="defaults to the manifest's environment")
    ap.add_argument("--out", type=Path, default=None,
                    help="calibration JSON to write "
                         "(default calibration/<environment>.json)")
    ap.add_argument("--read-delay-s", type=float, default=2.0,
                    help="delay after actuation at which mass is read")
    ap.add_argument("--stable-window-s", type=float,
                    default=DEFAULT_STABLE_WINDOW_S)
    ap.add_argument("--stable-tol-g", type=float, default=DEFAULT_STABLE_TOL_G)
    ap.add_argument("--plots", type=Path, default=None,
                    help="directory to write plots into (needs matplotlib)")
    ap.add_argument("--no-write", action="store_true",
                    help="print the report but do not write the calibration")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    records = load_runs(args.runs)
    if not records:
        raise SystemExit("no runs found in {}".format(args.runs))
    manifest = load_manifest(args.runs)
    environment = (args.environment or manifest.get("environment")
                   or "unknown")
    results = analyze_conditions(records, delay_s=args.read_delay_s,
                                 window_s=args.stable_window_s,
                                 tol_g=args.stable_tol_g)
    calibration = build_calibration(records, environment, results,
                                    args.read_delay_s, args.stable_window_s,
                                    args.stable_tol_g, manifest)
    print(format_report(calibration, results))
    if args.plots:
        for path in write_plots(records, calibration, args.plots):
            print("wrote {}".format(path))
    if not args.no_write:
        out = args.out or Path("calibration") / "{}.json".format(environment)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(calibration, indent=2, sort_keys=True)
                       + "\n")
        print("\nwrote {}".format(out))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

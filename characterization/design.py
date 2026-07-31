"""Experiment designs for the blank-auger characterization.

The experiment's whole value comes from ground truth: with an empty auger
the true mass change is exactly **0 mg**, so anything the balance reports
is artefact, and it is attributable to the actuation parameters rather
than confounded with powder flow.  That only holds if the design keeps
the artefact separable from everything *else* that moves a balance, which
is what this module is for:

* **Do-nothing controls**, of matched duration, interleaved throughout.
  Without them, ambient drift and building vibration are indistinguishable
  from actuation artefact -- and in a glovebox the ambient term may
  dominate.
* **Randomised, interleaved run order.**  Thermal drift and HVAC cycles
  are slow; blocking by condition aliases them onto whichever factor was
  swept last.  The order is seeded, so it is reproducible and recorded.
* **Screening before fine sweeps.**  Full factorial over six-plus factors
  is a waste of a night.  Screen one-factor-at-a-time from a baseline,
  then spend the replicates on a fine 1-D scan where the screen found
  something.

Parameter names and ranges are validated against the *firmware's* table
(:mod:`characterization.firmware_params`), so a bad level fails here in
milliseconds rather than at 3 a.m. on the rig.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Sequence, Tuple

from . import firmware_params

#: Rig actions a condition can fire, in order, during its actuation window.
ACTIONS = ("dispense", "vibrate", "tap", "servo", "none")


@dataclass(frozen=True)
class Condition:
    """One point in the design space."""

    name: str
    #: Firmware parameters to ``set`` before the run.
    params: Dict[str, object] = field(default_factory=dict)
    #: Rig actions fired during the actuation window.
    actions: Tuple[str, ...] = ("dispense",)
    #: ``"actuation"`` or ``"control"``.
    kind: str = "actuation"
    #: Free-form notes recorded with every run (e.g. "empty cup").
    notes: str = ""
    #: Host-side (non-firmware) context: tare load, isolation state,
    #: environment -- things the operator sets by hand and must record.
    context: Dict[str, object] = field(default_factory=dict)

    def validated(self) -> "Condition":
        """Coerce every parameter the way the firmware would.

        Returns a copy with coerced values so the run log records ``45.0``
        rather than the string ``"45"`` the CLI happened to supply.
        """
        for action in self.actions:
            if action not in ACTIONS:
                raise ValueError("unknown action {!r} in condition {!r}; "
                                 "choose from {}".format(action, self.name,
                                                         list(ACTIONS)))
        params = firmware_params.make_params()
        coerced = {}
        for key, value in self.params.items():
            coerced[key] = params.set(key, value)
        return replace(self, params=coerced)


@dataclass(frozen=True)
class Run:
    """One scheduled execution of a condition."""

    run_id: str
    index: int
    condition: Condition
    replicate: int
    #: Seconds of baseline recorded before actuation.
    pre_s: float = 3.0
    #: Seconds recorded after actuation returns -- this is the window the
    #: settle-time and stable-flag-latency measurements come from, so it
    #: must comfortably exceed the longest expected ringdown.
    post_s: float = 10.0
    #: For controls: seconds to sit idle where actuation would have been,
    #: so a control run occupies the same wall-clock shape as the runs it
    #: is compared against.
    dwell_s: float = 0.0

    @property
    def kind(self) -> str:
        return self.condition.kind


# ---------------------------------------------------------------------------
# Baseline and factor definitions
# ---------------------------------------------------------------------------

#: Centre point of the screen.  Every OFAT arm perturbs exactly one knob
#: away from this, so effects are read against a common reference.
BASELINE: Dict[str, object] = {
    "stepper_rpm": 30.0,
    "stepper_microsteps": 8,
    "stepper_accel": 2.0,
    "dispense_deg": 90.0,
    "deenergize_after": False,
    "move_pad_ms": 500,
    "vib_effect": 47,
    "vib_duration_s": 0.5,
    "tap_count": 2,
    "tap_on_ms": 40,
    "tap_duty": 0.8,
    "servo_speed_dps": 60.0,
    "servo_hold": True,
}


@dataclass(frozen=True)
class Factor:
    """A knob and the levels to try, with the actions that expose it."""

    param: str
    levels: Sequence[object]
    actions: Tuple[str, ...] = ("dispense",)
    note: str = ""


#: The four independent vibration sources plus the two firmware knobs that
#: are free to change and might matter a lot.
SCREEN_FACTORS: Tuple[Factor, ...] = (
    Factor("stepper_rpm", (10.0, 30.0, 60.0, 120.0, 240.0), ("dispense",),
           "step frequency and its harmonics hit structural resonances in "
           "bands, not monotonically"),
    Factor("stepper_microsteps", (1, 4, 8, 16, 32), ("dispense",),
           "smoother at the cost of torque"),
    Factor("stepper_accel", (0.5, 2.0, 8.0), ("dispense",)),
    Factor("dispense_deg", (30.0, 90.0, 360.0), ("dispense",)),
    Factor("deenergize_after", (False, True), ("dispense",),
           "holding current means coil hum and heat next to the load cell"),
    Factor("vib_duration_s", (0.0, 0.25, 0.5, 1.0), ("vibrate",),
           "continuous excitation: most likely to defeat a stability "
           "detector"),
    Factor("vib_effect", (14, 47, 118), ("vibrate",)),
    Factor("tap_count", (1, 2, 5), ("tap",),
           "impulsive; watch for a persistent step after the taps stop"),
    Factor("tap_duty", (0.4, 0.8, 1.0), ("tap",)),
    Factor("tap_on_ms", (20, 40, 80), ("tap",)),
    Factor("servo_hold", (False, True), ("servo",),
           "a digital servo merely holding a setpoint hunts around it"),
    Factor("servo_speed_dps", (20.0, 60.0, 180.0), ("servo",)),
)

#: Settle delay is a host-side factor: it is not something the rig does,
#: it is how long we wait before believing the number.  Swept, not fixed,
#: because the deliverable is the delay-vs-sigma curve and its knee.
SETTLE_LEVELS_S: Tuple[float, ...] = (0.5, 1.0, 2.0, 4.0, 8.0, 16.0)


# ---------------------------------------------------------------------------
# Designs
# ---------------------------------------------------------------------------

def control_condition(name: str = "control", notes: str = "",
                      context: Optional[Dict[str, object]] = None) -> Condition:
    """Everything off, for a matched duration."""
    return Condition(name=name, params={}, actions=("none",), kind="control",
                     notes=notes or "do-nothing control (ambient only)",
                     context=dict(context or {}))


def screening(factors: Sequence[Factor] = SCREEN_FACTORS,
              baseline: Optional[Dict[str, object]] = None,
              context: Optional[Dict[str, object]] = None) -> List[Condition]:
    """One-factor-at-a-time screen around :data:`BASELINE`.

    OFAT rather than fractional factorial on purpose: the leading question
    here is "which sources matter and in which bands", not "what are the
    interaction terms".  Interactions are worth a follow-up factorial over
    whichever two or three factors survive the screen -- see
    :func:`factorial`.
    """
    base = dict(BASELINE if baseline is None else baseline)
    conditions: List[Condition] = []
    seen = set()
    for factor in factors:
        for level in factor.levels:
            params = dict(base)
            params[factor.param] = level
            name = "{}={}".format(factor.param, level)
            if name in seen:
                continue
            seen.add(name)
            conditions.append(Condition(
                name=name, params=params, actions=factor.actions,
                notes=factor.note, context=dict(context or {})))
    return [c.validated() for c in conditions]


def factorial(factors: Sequence[Factor],
              baseline: Optional[Dict[str, object]] = None,
              actions: Tuple[str, ...] = ("dispense",),
              context: Optional[Dict[str, object]] = None) -> List[Condition]:
    """Full factorial over a *small* set of surviving factors.

    Guard-railed at 64 cells: past that the replicate count per cell falls
    below what is needed to estimate sigma at all, and the result is a big
    grid of numbers with no error bars.
    """
    base = dict(BASELINE if baseline is None else baseline)
    grids = [[(f.param, level) for level in f.levels] for f in factors]
    cells = list(itertools.product(*grids)) if grids else []
    if len(cells) > 64:
        raise ValueError(
            "full factorial would need {} cells; screen first, then run a "
            "factorial over the 2-3 factors that survived".format(len(cells)))
    conditions = []
    for cell in cells:
        params = dict(base)
        params.update(dict(cell))
        name = "&".join("{}={}".format(k, v) for k, v in cell)
        conditions.append(Condition(name=name, params=params, actions=actions,
                                    context=dict(context or {})))
    return [c.validated() for c in conditions]


def rpm_scan(lo: float = 5.0, hi: float = 300.0, step: float = 5.0,
             baseline: Optional[Dict[str, object]] = None,
             context: Optional[Dict[str, object]] = None) -> List[Condition]:
    """Fine 1-D RPM scan, for mapping forbidden bands.

    Resonances are narrow. A coarse screen can step straight over a band
    that will later show up as unexplained variance in a powder run, so
    once the screen says RPM matters, spend the runs here.
    """
    base = dict(BASELINE if baseline is None else baseline)
    conditions = []
    rpm = lo
    while rpm <= hi + 1e-9:
        params = dict(base)
        params["stepper_rpm"] = rpm
        conditions.append(Condition(name="stepper_rpm={:g}".format(rpm),
                                    params=params, actions=("dispense",),
                                    context=dict(context or {})))
        rpm += step
    return [c.validated() for c in conditions]


#: The ~20-minute subset run on entering a new environment: a control, the
#: baseline dispense, the two extreme RPMs, and one tap condition (the
#: source most likely to produce a persistent step).
def selfcheck(baseline: Optional[Dict[str, object]] = None,
              context: Optional[Dict[str, object]] = None) -> List[Condition]:
    base = dict(BASELINE if baseline is None else baseline)
    ctx = dict(context or {})
    out = [control_condition(context=ctx)]
    for name, overrides, actions in (
        ("baseline_dispense", {}, ("dispense",)),
        ("rpm_low", {"stepper_rpm": 10.0}, ("dispense",)),
        ("rpm_high", {"stepper_rpm": 240.0}, ("dispense",)),
        ("tap", {}, ("tap",)),
    ):
        params = dict(base)
        params.update(overrides)
        out.append(Condition(name=name, params=params, actions=actions,
                             context=ctx))
    return [c.validated() if c.kind == "actuation" else c for c in out]


DESIGNS = {
    "screen": screening,
    "rpm-scan": rpm_scan,
    "selfcheck": selfcheck,
}


# ---------------------------------------------------------------------------
# Run list construction
# ---------------------------------------------------------------------------

def estimate_action_seconds(condition: Condition,
                            full_steps_rev: int = 200) -> float:
    """Rough wall-clock cost of a condition's actuation.

    Used to give control runs a matched dwell and to print a credible
    estimate of how long the night will take before committing to it.
    """
    params = dict(BASELINE)
    params.update(condition.params)
    total = 0.0
    for action in condition.actions:
        if action == "dispense":
            rpm = max(float(params.get("stepper_rpm", 30.0)), 1e-6)
            deg = abs(float(params.get("dispense_deg", 90.0)))
            total += deg / 360.0 / rpm * 60.0
            total += float(params.get("move_pad_ms", 2000)) / 1000.0
        elif action == "vibrate":
            total += float(params.get("vib_duration_s", 0.5))
        elif action == "tap":
            total += (int(params.get("tap_count", 2))
                      * (int(params.get("tap_on_ms", 40))
                         + int(params.get("tap_off_ms", 200))) / 1000.0)
        elif action == "servo":
            speed = max(float(params.get("servo_speed_dps", 60.0)), 1e-6)
            total += 2 * 45.0 / speed  # out and back
    return total


def build_runlist(conditions: Sequence[Condition], replicates: int = 20,
                  seed: int = 0, control_every: int = 10,
                  pre_s: float = 3.0, post_s: float = 10.0,
                  control: Optional[Condition] = None) -> List[Run]:
    """Replicate, shuffle, and interleave controls.

    The shuffle is over ``(condition, replicate)`` pairs rather than over
    conditions, so a condition's replicates are spread across the whole
    night.  That is the point: if replicates run back to back, a slow
    drift shows up as small within-condition scatter and large
    between-condition differences -- exactly the wrong conclusion.
    """
    if replicates < 1:
        raise ValueError("replicates must be >= 1")
    actuation = [c for c in conditions if c.kind == "actuation"]
    explicit_controls = [c for c in conditions if c.kind == "control"]
    control = control or (explicit_controls[0] if explicit_controls
                          else control_condition())

    pairs = [(c, r) for c in actuation for r in range(replicates)]
    rng = random.Random(seed)
    rng.shuffle(pairs)

    # Matched dwell: the median actuation cost, so a control neither
    # under- nor over-samples the ambient drift relative to real runs.
    costs = sorted(estimate_action_seconds(c) for c in actuation) or [0.0]
    dwell = costs[len(costs) // 2]

    runs: List[Run] = []
    index = 0

    def _add(condition: Condition, replicate: int, dwell_s: float) -> None:
        nonlocal index
        runs.append(Run(
            run_id="{:05d}".format(index), index=index, condition=condition,
            replicate=replicate, pre_s=pre_s, post_s=post_s, dwell_s=dwell_s))
        index += 1

    control_rep = 0
    if control_every > 0:
        _add(control, control_rep, dwell)
        control_rep += 1
    for position, (condition, replicate) in enumerate(pairs, start=1):
        _add(condition, replicate, 0.0)
        if control_every > 0 and position % control_every == 0:
            _add(control, control_rep, dwell)
            control_rep += 1
    if control_every > 0 and runs[-1].kind != "control":
        # Bookend, so drift can be bracketed at both ends of the night.
        _add(control, control_rep, dwell)
    return runs


def estimate_duration_s(runs: Sequence[Run], settle_s: float = 0.0) -> float:
    """Total wall clock for a run list, including pre/post windows."""
    total = 0.0
    for run in runs:
        total += run.pre_s + run.post_s + settle_s
        total += (run.dwell_s if run.kind == "control"
                  else estimate_action_seconds(run.condition))
    return total

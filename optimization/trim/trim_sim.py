"""Trim-regime plant model for the powder doser (issue #153).

This is deliberately *not* the full digital twin in ``optimization/simulation``.
It models only the endgame -- the state the rig is in after the bang-bang bulk
phase has halted a safe distance below target -- so that trim strategies can be
compared without inheriting the twin's unmeasured mid-flow behaviour.

Why a separate model
--------------------
The 2026-08-22 Edison spot-check on PR #124 made two points that decide how the
trim question has to be posed:

1.  At the trim operating point the powder does **not** arrive as a flow.  It
    arrives as discrete slugs off the tube lip.  Measured on our own salt
    increments: mean 6.4 mg, sd 15.9 mg.  At the 0.042 g/s the trickle actually
    runs at, that is lambda ~ 6.6 events/s, so the 0.30 s lookahead the cutoff
    rule uses contains only ~2 expected events and has a ~14 % chance of
    containing *none*.  Any model that represents the trim regime as a smooth
    rate plus Gaussian noise assumes away the entire problem.

2.  The balance time constant is the most serious hardware sensitivity, and the
    twin hides it: twin plant and twin filter both used 0.7 s, so the estimator
    was handed a perfectly specified sensor.  The real HR-100A may be ~0.16 s.
    Here ``tau_bal`` is a plant parameter and the controller carries its own
    separate belief, so plant/filter *mismatch* is a first-class sweep axis.

Everything below is therefore stated in terms a bench test can measure, and the
calibration constants carry the measurement they came from.

Model
-----
::

    screw --(ff * rev/s, smooth)--> lip --(marked point process)--> free fall
                                                                       |
                                                                  cup / balance

* **Screw -> lip** is smooth.  The auger is a positive-displacement metering
  device; conveying noise is a run-level feed-factor offset plus a slow OU
  drift, not per-sample jitter.
* **Lip -> cup** is a marked point process.  Events fire at a hazard
  proportional to the lip charge held *above* its retained capacity; each event
  releases a lognormal mark.  This is the granularity that makes rate feedback
  ill-posed at trim flow, and it is also what produces afterflow: when the auger
  halts, the excess is still on the lip and keeps coming.
* **Balance** is a first-order lag sampled and held on its own 10 Hz serial
  clock, quantized to the HR-100A's 0.1 mg readability, with a vibration
  envelope that rises while actuators run and decays afterwards.

Calibration (all from PR #124 bench/diagnostic numbers)
-------------------------------------------------------
=========================  =========  ==================================
quantity                   value      source
=========================  =========  ==================================
mean slug mass             6.4 mg     Edison spot-check, salt increments
slug mass sd               15.9 mg    same (an upper bound -- see below)
trim flow rate             0.042 g/s  ``diag_trickle_stages.txt``
=> slug rate               6.6 /s     mean-consistent, matches Edison
feed factor at trim tilt   0.113 g/rev  identified median, same diagnostic
post-halt lip drain        +26.0 mg   same (p95 +52.4 mg)
=> lip drain time const    0.48 s     tuned to reproduce that drain

balance readability        0.1 mg     HR-100A
balance noise, at rest     0.5 mg     ``controllers.QUIET_SD``
balance noise, actuating   8 mg       ``controllers.NOISY_SD``
=========================  =========  ==================================

The 15.9 mg slug sd was measured on 45 deg steps on a depleted tube and includes
reading noise, so the true mark dispersion is somewhat smaller.  It is exposed
as ``slug_cv`` and swept in the study rather than trusted as a point value.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, replace

__all__ = [
    "TrimPowder", "TrimPlant", "TrimRig", "POWDERS",
    "QUIET_SD_G", "NOISY_SD_G", "TOL_G", "BALANCE_RESOLUTION_G",
]

# ---------------------------------------------------------------------------
# Instrument constants (shared with optimization/benchmarks/controllers.py so
# the two studies score against the same balance).
# ---------------------------------------------------------------------------
QUIET_SD_G = 5e-4            # balance noise sd at rest
NOISY_SD_G = 8e-3            # balance noise sd while actuators run
TOL_G = 5e-3                 # +/- 5 mg "done" tolerance (firmware PHASE3)
BALANCE_RESOLUTION_G = 1e-4  # HR-100A readability
BALANCE_RATE_HZ = 10.0       # serial frame rate
FALL_TIME_S = 0.15           # mean lip -> cup free fall

MAX_AUGER_RPM = 109.0        # firmware clamp (240 motor rpm / 2.2)

# How far into the nominally retained lip charge a single avalanche can cut.
# Bounds the worst case: without it an arbitrarily small auger command could
# discharge the whole lip, which is more pessimistic than the bench data.
AVALANCHE_DEPTH_FRAC = 0.35


@dataclass(frozen=True)
class TrimPowder:
    """Powder properties that matter in the trim regime.

    ``feed_factor_g_per_rev`` is quoted **at the trim tilt**, not at 90 deg, so
    it is directly comparable with the 0.113 g/rev median identified at cutoff
    in ``diag_trickle_stages.txt``.
    """

    name: str
    feed_factor_g_per_rev: float   # g delivered to the lip per auger revolution
    mean_slug_g: float             # mean mass per lip-release event
    slug_cv: float                 # coefficient of variation of the slug mass
    lip_capacity_g: float          # powder retained on the lip indefinitely
    lip_drain_tau_s: float         # exp. time constant of post-halt lip drain
    tap_release_frac: float        # mean fraction of lip charge a tap ejects
    stall_hazard_per_rev: float    # cohesive-blockage onset hazard
    ff_run_cv: float = 0.10        # run-to-run feed factor spread
    ff_drift_cv: float = 0.06      # within-run OU drift on the feed factor


# Three powders spanning the bench battery: free-flowing salt, mid lactose
# (calcium lactate), and cohesive AlSi10Mg.  Feed factors are the calibrated
# 90 deg values from optimization/simulation/calibrated_powders.json scaled to
# the ~20 deg trim tilt by the fitted tilt law, which lands salt on the 0.113
# g/rev median that was actually identified at cutoff.
POWDERS: dict[str, TrimPowder] = {
    "salt": TrimPowder(
        name="salt",
        feed_factor_g_per_rev=0.113,
        mean_slug_g=6.4e-3,
        slug_cv=2.48,              # sd 15.9 mg / mean 6.4 mg
        lip_capacity_g=0.055,
        lip_drain_tau_s=0.48,      # tuned so post-halt drain = +26 mg
        tap_release_frac=0.11,
        stall_hazard_per_rev=0.002,
    ),
    "lactose": TrimPowder(
        name="lactose",
        feed_factor_g_per_rev=0.128,
        mean_slug_g=4.0e-3,        # finer 60 um particles -> finer increments
        slug_cv=2.20,
        lip_capacity_g=0.070,
        lip_drain_tau_s=0.58,
        tap_release_frac=0.16,
        stall_hazard_per_rev=0.006,
    ),
    "AlSi10Mg": TrimPowder(
        name="AlSi10Mg",
        feed_factor_g_per_rev=0.072,
        mean_slug_g=9.0e-3,        # cohesive: fewer, larger avalanches
        slug_cv=2.80,
        lip_capacity_g=0.090,
        lip_drain_tau_s=0.74,
        tap_release_frac=0.22,
        stall_hazard_per_rev=0.030,
    ),
}


@dataclass
class TrimPlant:
    """Physical state of the rig during the trim phase.

    ``tau_bal_s`` is the *plant's* balance time constant.  Controllers get their
    own belief about it via :class:`TrimRig`; the two are intentionally
    separable so plant/filter mismatch can be swept (Edison item 3).
    """

    powder: TrimPowder
    seed: int = 0
    tau_bal_s: float = 0.7
    dt_internal_s: float = 0.02

    # --- state ---
    t_s: float = 0.0
    delivered_g: float = 0.0        # true settled mass in the cup
    lip_g: float = 0.0
    auger_rpm: float = 0.0
    stalled: bool = False
    _in_flight: list = field(default_factory=list)   # (land_time, mass)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        # Independent streams so that changing a controller's number of balance
        # reads does not shift the powder physics (common random numbers).
        self.flow_rng = random.Random(self.seed * 7919 + 1)
        self.slug_rng = random.Random(self.seed * 7919 + 2)
        self.bal_rng = random.Random(self.seed * 7919 + 3)
        self.tap_rng = random.Random(self.seed * 7919 + 4)

        p = self.powder
        # Run-level feed factor offset: the same tube/fill/humidity all dose.
        self._ff_run = p.feed_factor_g_per_rev * math.exp(
            self.flow_rng.gauss(0.0, p.ff_run_cv) - 0.5 * p.ff_run_cv ** 2)
        self._ff_ou = 0.0
        # Run-level lip capacity: consolidation and packing vary dose to dose,
        # and this is what gives post-halt drain its spread.
        self._cap_g = p.lip_capacity_g * math.exp(
            self.flow_rng.gauss(0.0, 0.30) - 0.5 * 0.30 ** 2)
        # Hazard constant k such that excess drains with time constant
        # lip_drain_tau_s:  d(excess)/dt = -k * excess * mean_slug.
        self._k_release = 1.0 / max(1e-6, p.lip_drain_tau_s * p.mean_slug_g)
        # Lognormal mark parameters from (mean, cv).
        sigma2 = math.log(1.0 + p.slug_cv ** 2)
        self._mark_sigma = math.sqrt(sigma2)
        self._mark_mu = math.log(p.mean_slug_g) - 0.5 * sigma2

        # Balance
        self._bal_filt_g = 0.0
        self._bal_drift_g = 0.0
        self._bal_bias_g = self.bal_rng.gauss(0.0, 3e-4)
        self._vib_level = 0.0
        self._vib_ar = 0.0
        self._next_sample_s = 0.0
        self._last_frame_g = 0.0
        self._frame_tick = 0
        self._recent: list[float] = []
        self._tare_g = 0.0
        self._disturb_until = -1.0
        self._disturb_level = 0.0

    # -- helpers -----------------------------------------------------------
    def feed_factor(self) -> float:
        return self._ff_run * math.exp(self._ff_ou
                                       - 0.5 * self.powder.ff_drift_cv ** 2)

    def prime_lip(self, excess_g: float | None = None) -> None:
        """Put the lip in the state the bulk phase leaves it in.

        After a max-rate bang the lip is charged to its capacity plus whatever
        the flow had pushed above it.  ``excess_g`` defaults to the steady-state
        excess for the bulk flow rate, which is what produces the +26 mg
        afterflow seen in the diagnostic.
        """
        if excess_g is None:
            excess_g = 0.042 * self.powder.lip_drain_tau_s
        self.lip_g = self._cap_g + max(0.0, excess_g)

    def bump_vibration(self, level_g: float, hold_s: float) -> None:
        self._disturb_level = max(self._disturb_level, level_g)
        self._disturb_until = max(self._disturb_until, self.t_s + hold_s)

    # -- actuation ---------------------------------------------------------
    def set_rpm(self, rpm: float) -> None:
        self.auger_rpm = max(0.0, min(MAX_AUGER_RPM, rpm))

    def tap(self) -> None:
        """Solenoid tap: clears a blockage and ejects a fraction of the lip.

        The ejected fraction is Beta-like (mean ``tap_release_frac``, heavy
        right tail), which is why a tap can dump a slug past target -- taps are
        not a purely protective action.
        """
        self.stalled = False
        if self.lip_g > 1e-6:
            f = self.powder.tap_release_frac
            # lognormal fraction, clipped to 1
            s = 0.9
            frac = min(1.0, math.exp(self.tap_rng.gauss(math.log(f) - 0.5 * s * s, s)))
            ejected = self.lip_g * frac
            self.lip_g -= ejected
            self._launch(ejected)
        self.bump_vibration(8e-3, 0.35)

    def _launch(self, mass_g: float) -> None:
        if mass_g <= 0.0:
            return
        jitter = max(0.02, self.flow_rng.gauss(FALL_TIME_S, 0.04))
        self._in_flight.append((self.t_s + jitter, mass_g))

    # -- integration -------------------------------------------------------
    def step(self, dt_s: float) -> None:
        remaining = dt_s
        while remaining > 1e-9:
            h = min(self.dt_internal_s, remaining)
            self._step_once(h)
            remaining -= h

    def _step_once(self, h: float) -> None:
        p = self.powder
        # --- screw -> lip (smooth) ---
        rev = self.auger_rpm / 60.0 * h
        if rev > 0.0:
            a = math.exp(-h / 1.5)
            self._ff_ou = a * self._ff_ou + \
                p.ff_drift_cv * math.sqrt(max(0.0, 1.0 - a * a)) * \
                self.flow_rng.gauss(0.0, 1.0)
            if not self.stalled and \
                    self.flow_rng.random() < p.stall_hazard_per_rev * rev:
                self.stalled = True
            if not self.stalled:
                self.lip_g += self.feed_factor() * rev
            self.bump_vibration(6e-3, 0.05)

        # --- lip -> cup: marked point process on the excess charge ---
        excess = max(0.0, self.lip_g - self._cap_g)
        lam = self._k_release * excess          # events/s
        if lam > 0.0 and self.slug_rng.random() < 1.0 - math.exp(-lam * h):
            mark = math.exp(self.slug_rng.gauss(self._mark_mu, self._mark_sigma))
            # An avalanche can undercut the nominally retained charge -- lip
            # capacity is a stability threshold, not a hard floor -- but only to
            # a limited depth.  Clipping the mark at the *excess* instead would
            # truncate the heavy right tail, which is precisely the feature that
            # makes rate feedback ill-posed here; clipping at the whole lip
            # charge would let an arbitrarily small command discharge the entire
            # lip, which is worse than what the bench shows.
            depth = excess + AVALANCHE_DEPTH_FRAC * self._cap_g
            released = min(mark, depth, self.lip_g)
            self.lip_g -= released
            self._launch(released)

        self.t_s += h

        # --- free fall ---
        if self._in_flight:
            landed = [m for (t_land, m) in self._in_flight if t_land <= self.t_s]
            if landed:
                self.delivered_g += sum(landed)
                self._in_flight = [(t, m) for (t, m) in self._in_flight
                                   if t > self.t_s]

        self._update_balance(h)

    def _update_balance(self, h: float) -> None:
        alpha = 1.0 - math.exp(-h / max(1e-3, self.tau_bal_s))
        self._bal_filt_g += alpha * (self.delivered_g - self._bal_filt_g)

        target = self._disturb_level if self.t_s <= self._disturb_until else 0.0
        if self.auger_rpm > 0.0:
            target = max(target, 6e-3)
        if self.t_s > self._disturb_until:
            self._disturb_level = 0.0
        if target > self._vib_level:
            self._vib_level = target
        else:
            self._vib_level *= math.exp(-h / (0.4 + 0.4 * self.bal_rng.random()))

        self._bal_drift_g += self.bal_rng.gauss(0.0, 5e-5) * math.sqrt(h)

        while self.t_s >= self._next_sample_s:
            self._next_sample_s += 1.0 / BALANCE_RATE_HZ
            self._vib_ar = 0.8 * self._vib_ar + 0.6 * self.bal_rng.gauss(0.0, 1.0)
            vib = self._vib_level * (0.6 * self._vib_ar)
            noise = self.bal_rng.gauss(0.0, QUIET_SD_G * 0.3)
            raw = (self._bal_filt_g + self._bal_bias_g + self._bal_drift_g
                   + vib + noise)
            grams = round((raw - self._tare_g) / BALANCE_RESOLUTION_G) \
                * BALANCE_RESOLUTION_G
            self._last_frame_g = grams
            self._frame_tick += 1
            self._recent.append(grams)
            if len(self._recent) > 5:
                self._recent.pop(0)

    # -- sensing -----------------------------------------------------------
    def read_frame(self) -> tuple[float, bool, int]:
        stable = (len(self._recent) >= 5
                  and (max(self._recent) - min(self._recent)) < 1.5e-3
                  and self._vib_level < 1e-3)
        return self._last_frame_g, stable, self._frame_tick

    def settled_mass_g(self, settle_s: float = 3.0) -> float:
        """Ground truth after everything in flight has landed (scoring only)."""
        clone_t = self.t_s
        while self._in_flight and self.t_s < clone_t + settle_s:
            self.step(0.05)
        return self.delivered_g


class TrimRig:
    """Controller-facing surface.

    Controllers may only touch this.  They see the quantized, lagged, noisy
    balance and their own commanded actuator state -- never ``lip_g``,
    ``delivered_g`` or the true feed factor.

    ``tau_bal_belief_s`` is what the *controller* thinks the balance time
    constant is.  It defaults to the plant value but the study overrides it to
    create the mismatch Edison asked us to quantify.
    """

    GLOBAL_TIMEOUT_S = 240.0
    TAP_PERIOD_S = 0.12

    def __init__(self, plant: TrimPlant, tau_bal_belief_s: float | None = None):
        self._p = plant
        self.t0 = plant.t_s
        self.tau_bal_belief_s = (plant.tau_bal_s if tau_bal_belief_s is None
                                 else tau_bal_belief_s)
        self._last_actuation_end = -10.0
        self.taps = 0
        self.auger_rev = 0.0
        self.settle_waits = 0

    # -- time --
    @property
    def t(self) -> float:
        return self._p.t_s - self.t0

    def timed_out(self) -> bool:
        return self.t > self.GLOBAL_TIMEOUT_S

    def wait(self, dt_s: float) -> None:
        if self._p.auger_rpm > 0.0:
            self.auger_rev += self._p.auger_rpm / 60.0 * dt_s
        self._p.step(dt_s)

    # -- actuation --
    def set_rpm(self, rpm: float) -> None:
        self._p.set_rpm(rpm)
        self._last_actuation_end = (float("inf") if rpm > 0.0 else self._p.t_s)

    def rotate_deg(self, deg: float, rpm: float) -> None:
        """Commanded open-loop auger increment -- the increment-and-measure
        primitive.  Blocks for the move, then halts."""
        rpm = max(1.0, min(MAX_AUGER_RPM, rpm))
        self.set_rpm(rpm)
        self.wait(abs(deg) / 360.0 / (rpm / 60.0))
        self.set_rpm(0.0)

    def tap(self, n: int = 1) -> None:
        for _ in range(n):
            self._p.tap()
            self.wait(self.TAP_PERIOD_S)
            self.taps += 1
        self._last_actuation_end = self._p.t_s

    # -- sensing --
    def read_frame(self) -> tuple[float, bool, int]:
        return self._p.read_frame()

    def read(self) -> tuple[float, bool]:
        g, stable, _ = self._p.read_frame()
        return g, stable

    def actuating(self) -> bool:
        if self._last_actuation_end == float("inf"):
            return True
        return self._p.t_s < self._last_actuation_end + 0.8

    def settled_read(self, settle_s: float = 1.0, n_avg: int = 5) -> float:
        """Halt-and-measure: wait out the balance lag and average n frames.

        This is the primitive the increment-and-measure family is built on.  It
        costs time, and buys two things a moving measurement cannot have: the
        vibration envelope has decayed (0.5 mg noise instead of 8 mg) and the
        first-order lag has expired, so the reading needs no lag correction and
        therefore no assumption about ``tau_bal``.
        """
        self.settle_waits += 1
        self.wait(max(settle_s, 3.0 * self.tau_bal_belief_s))
        acc, n, last_tick = 0.0, 0, -1
        while n < n_avg and not self.timed_out():
            self.wait(1.0 / BALANCE_RATE_HZ)
            g, _, tick = self.read_frame()
            if tick != last_tick:
                acc += g
                n += 1
                last_tick = tick
        return acc / max(1, n)

    def stalled(self) -> bool:
        """Controllers cannot see this; used only by the harness."""
        raise NotImplementedError("plant state is not visible to controllers")


def make_rig(powder: str, seed: int, tau_bal_plant_s: float = 0.7,
             tau_bal_belief_s: float | None = None,
             slug_cv: float | None = None,
             start_deficit_g: float = 0.30) -> tuple[TrimRig, TrimPlant, float]:
    """Build a rig at the bulk/trim handover point.

    Returns ``(rig, plant, target_g)`` where the balance already reads the mass
    the bulk phase delivered and ``target_g - delivered`` is roughly
    ``start_deficit_g``.  The handover deficit is what the bang-bang guard band
    leaves on the table, so it is the study's main design knob.
    """
    p = POWDERS[powder]
    if slug_cv is not None:
        p = replace(p, slug_cv=slug_cv)
    plant = TrimPlant(powder=p, seed=seed, tau_bal_s=tau_bal_plant_s)
    plant.prime_lip()
    # The bulk phase has already put mass in the cup; start the balance there so
    # the trim controller sees a realistic absolute reading.
    bulk_g = 2.0
    plant.delivered_g = bulk_g
    plant._bal_filt_g = bulk_g
    target_g = bulk_g + start_deficit_g
    rig = TrimRig(plant, tau_bal_belief_s=tau_bal_belief_s)
    return rig, plant, target_g

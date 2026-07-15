"""Reduced-order "digital twin" of the powder doser (issue #123 / PR #124).

A fast compartment model of the rig -- hopper -> auger -> tube-lip reservoir ->
free fall -> vial on balance -- meant for prototyping and pre-tuning dosing
control policies (three-phase, rate-PID, MPC, BO campaigns) before hardware
runs.  It is NOT a particle-level physics model; a separate Edison query
surveys DEM/physics-engine options for that.

Units match the firmware (main_three_phase.py): grams, seconds, mounting-plate
degrees for tilt (0 = horizontal ... 45 = "vertical"), auger RPM / auger
degrees for rotation.

Modelled behaviors, from bench observations in PR #124 and the loss-in-weight
feeder literature (Edison query.answer.md):

* Auger conveying: mass per auger revolution (the LIW "feed factor") scales
  with hopper fill level (starved screw below ~30 % fill), tilt (steeper
  dispenses more), powder cohesion, and slight densification from tapping.
  Discharge pulsates with screw angle at low fill.
* Lip reservoir coupling: rotation replenishes a small reservoir of loose
  powder at the tube lip; taps and gravity discharge it.  This reproduces the
  observed interactions -- a tap right after a rotation yields more than
  repeated taps (which deplete the lip), and everything yields more at steeper
  tilt.
* Taps: each solenoid tap ejects a tilt- and cohesion-dependent fraction of
  the lip reservoir (in discrete clumps for cohesive powders), slightly
  compacts the powder, disturbs the balance, and can clear a cohesive arch
  ("rat hole") in the hopper throat.
* Optional vibration motor (not in current firmware, kept for exploration):
  duty cycle smooths and boosts lip discharge, compacts powder, disturbs the
  balance.
* Context variables: ambient humidity + exposure time drive moisture uptake
  (hygroscopicity), which raises effective cohesion; temperature mildly
  offsets it; hopper fill level evolves as powder is used.
* Balance: first-order settling lag (configurable integration time),
  0.1 mg resolution, noise floor, large vibration noise during/after
  actuation, and an A&D-style stable/unstable flag.  Powder spends ~0.15 s
  in free fall before landing (in-flight mass the controller cannot see).
* Instantaneous dose rate: true landing rate (g/s) exposed for rate-based
  control experiments; the balance-derived estimate is up to the controller.

Example::

    from powder_sim import PowderDoserSim, Context, POWDERS

    sim = PowderDoserSim(POWDERS["salt"], Context(humidity_pct_rh=35.0), seed=1)
    sim.set_tilt_deg(45.0)
    sim.set_auger_rpm(55.0)
    while sim.dispensed_g < 1.5:
        sim.step(0.25)
    sim.set_auger_rpm(0.0)
    sim.set_tilt_deg(0.0)
    for _ in range(10):
        sim.tap()
        sim.step(0.6)
    grams, stable = sim.read_balance()
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, replace


# --------------------------------------------------------------------------
# Powder and context definitions
# --------------------------------------------------------------------------

@dataclass
class Powder:
    """Material parameters. All *_factor values are dimensionless multipliers
    calibrated so table salt at 45 deg tilt and full hopper reproduces the
    rough bench numbers from PR #124 (a few hundred mg per auger rev)."""

    name: str
    feed_factor_g_per_rev: float   # g conveyed per auger rev (full fill, 45 deg)
    density_g_per_cm3: float       # bulk density (used for clump size)
    cohesion: float                # 0 free-flowing ... 1 very cohesive
    moisture_sensitivity: float    # d(cohesion)/d(moisture fraction)
    hygroscopicity: float          # moisture fraction uptake per hour at 100 %RH
    angle_of_repose_deg: float     # holds more powder at the lip when high
    particle_size_um: float        # sets discharge granularity / noise quanta


#: Starting library. Values are plausible-order estimates to be calibrated
#: against bench data (see README); salt is loosely anchored to PR #124 videos.
POWDERS = {
    "salt": Powder(
        name="salt", feed_factor_g_per_rev=0.35, density_g_per_cm3=1.20,
        cohesion=0.08, moisture_sensitivity=1.5, hygroscopicity=0.002,
        angle_of_repose_deg=32.0, particle_size_um=400.0,
    ),
    "AlSi10Mg": Powder(  # gas-atomized spheres: dense, very free flowing
        name="AlSi10Mg", feed_factor_g_per_rev=0.55, density_g_per_cm3=1.45,
        cohesion=0.04, moisture_sensitivity=0.8, hygroscopicity=0.0005,
        angle_of_repose_deg=27.0, particle_size_um=45.0,
    ),
    "stainless_316L": Powder(
        name="stainless_316L", feed_factor_g_per_rev=1.60, density_g_per_cm3=4.00,
        cohesion=0.05, moisture_sensitivity=0.6, hygroscopicity=0.0003,
        angle_of_repose_deg=29.0, particle_size_um=35.0,
    ),
    "silicon": Powder(  # angular, somewhat cohesive when fine
        name="silicon", feed_factor_g_per_rev=0.40, density_g_per_cm3=1.10,
        cohesion=0.25, moisture_sensitivity=1.2, hygroscopicity=0.001,
        angle_of_repose_deg=38.0, particle_size_um=75.0,
    ),
    "lactose": Powder(  # cheap cohesive surrogate for bench experiments
        name="lactose", feed_factor_g_per_rev=0.25, density_g_per_cm3=0.60,
        cohesion=0.55, moisture_sensitivity=2.5, hygroscopicity=0.006,
        angle_of_repose_deg=45.0, particle_size_um=60.0,
    ),
}


@dataclass
class Context:
    """Observed-but-uncontrolled variables (the BO context vector)."""

    temperature_c: float = 22.0
    humidity_pct_rh: float = 30.0
    exposure_hours: float = 0.0       # powder's prior open-air exposure
    hopper_capacity_g: float = 60.0
    hopper_fill_frac: float = 0.8     # initial fill level


# --------------------------------------------------------------------------
# The simulator
# --------------------------------------------------------------------------

@dataclass
class _Telemetry:
    t_s: float
    dispensed_g: float
    balance_g: float
    balance_stable: bool
    dose_rate_g_per_s: float
    lip_g: float
    in_flight_g: float
    hopper_fill_frac: float
    effective_cohesion: float
    feed_factor_g_per_rev: float
    auger_rpm: float
    tilt_deg: float
    arched: bool


class PowderDoserSim:
    """Continuous-time compartment model, advanced with step(dt)."""

    MAX_TILT_DEG = 45.0          # plate 45 deg = rig "vertical"
    MAX_AUGER_RPM = 109.0        # firmware clamp (240 motor RPM / 2.2)
    TILT_SLEW_DEG_S = 90.0       # servo speed at the plate
    FALL_TIME_S = 0.15           # lip -> vial free fall
    LIP_BASE_CAPACITY_G = 0.25   # loose powder the lip holds when horizontal
    BALANCE_RESOLUTION_G = 1e-4  # HR-100A readability

    def __init__(self, powder: Powder, context: Context | None = None,
                 seed: int | None = None, balance_integration_s: float = 0.7):
        self.powder = powder
        self.context = replace(context) if context else Context()
        self.rng = random.Random(seed)
        self.t_s = 0.0

        # --- powder state ---
        self.hopper_g = self.context.hopper_capacity_g * self.context.hopper_fill_frac
        self.lip_g = 0.0
        self.in_flight: list[list[float]] = []   # [land_time_s, grams]
        self.dispensed_g = 0.0                   # true grams in the vial
        self.moisture = self.powder.hygroscopicity * \
            (self.context.humidity_pct_rh / 100.0) * self.context.exposure_hours
        self.packing = 0.0                       # 0 loose ... 1 fully tapped-down
        self.arched = False                      # cohesive arch blocks the throat
        self.auger_angle_rev = 0.0               # for low-fill discharge pulsation

        # --- actuator state ---
        self.auger_rpm = 0.0
        self.tilt_deg = 0.0
        self.tilt_target_deg = 0.0
        self.vibration_duty = 0.0

        # --- balance state ---
        self.balance_integration_s = balance_integration_s
        self._balance_filt_g = 0.0
        self._balance_prev_g = 0.0               # reading ~0.5 s ago
        self._prev_sample_age_s = 0.0
        self._disturb_until_s = 0.0              # vibration window after taps
        self._tare_g = 0.0

        # --- outputs ---
        self.dose_rate_g_per_s = 0.0             # smoothed true landing rate
        self.total_taps = 0
        self.total_auger_rev = 0.0

    # ---------------- actuator commands ----------------

    def set_auger_rpm(self, rpm: float) -> None:
        self.auger_rpm = max(0.0, min(self.MAX_AUGER_RPM, rpm))

    def set_tilt_deg(self, plate_deg: float) -> None:
        self.tilt_target_deg = max(0.0, min(self.MAX_TILT_DEG, plate_deg))

    def set_vibration_duty(self, duty: float) -> None:
        self.vibration_duty = max(0.0, min(1.0, duty))

    def rotate_auger_deg(self, auger_deg: float, rpm: float, dt: float = 0.05) -> None:
        """Convenience: blocking incremental rotation (firmware's default mode)."""
        rpm = max(1e-6, min(self.MAX_AUGER_RPM, rpm))
        duration = (auger_deg / 360.0) / (rpm / 60.0)
        old = self.auger_rpm
        self.auger_rpm = rpm
        self.step(duration)
        self.auger_rpm = old

    def tap(self) -> float:
        """One solenoid tap. Returns grams knocked off the lip (lands after
        the free-fall delay)."""
        self.total_taps += 1
        s = self._steepness()
        coh = self.effective_cohesion()
        # Tilt is the dominant lever (bench observation: taps at steep angles
        # move far more powder); cohesion holds powder back.
        eject_frac = 0.35 * (0.20 + 0.80 * s) * (1.0 - 0.55 * coh)
        expected = self.lip_g * eject_frac
        ejected = self._quantized(expected, coh)
        ejected = min(ejected, self.lip_g)
        self.lip_g -= ejected
        self._launch(ejected)
        # Side effects: compaction, hopper arch clearing, balance disturbance.
        self.packing = min(1.0, self.packing + 0.02)
        if self.arched and self.rng.random() < 0.6:
            self.arched = False
        self._disturb_until_s = max(self._disturb_until_s, self.t_s + 0.8)
        return ejected

    def tare(self) -> None:
        self._tare_g = self._balance_filt_g + self._tare_g

    # ---------------- observation ----------------

    def read_balance(self) -> tuple[float, bool]:
        """(grams, stable) as the A&D would report them: settled, quantized,
        noisy -- badly so while actuators shake the frame."""
        noisy = self._balance_filt_g + self.rng.gauss(0.0, self._balance_noise_sd())
        grams = round((noisy - self._tare_g) / self.BALANCE_RESOLUTION_G) \
            * self.BALANCE_RESOLUTION_G
        stable = (not self._disturbed()
                  and abs(self._balance_filt_g - self._balance_prev_g) < 1e-3)
        return grams, stable

    def effective_cohesion(self) -> float:
        coh = self.powder.cohesion \
            + self.powder.moisture_sensitivity * self.moisture \
            + 0.0015 * max(0.0, self.context.humidity_pct_rh - 30.0)
        coh -= 0.004 * (self.context.temperature_c - 22.0)  # warmer = drier
        return max(0.0, min(1.0, coh))

    def feed_factor_g_per_rev(self) -> float:
        """Current g per auger rev -- the LIW 'feed factor'. Depends on fill
        level, tilt, cohesion, and densification state."""
        if self.arched:
            return 0.0
        fill = self.hopper_fill_frac()
        fill_factor = min(1.0, fill / 0.30) ** 0.7 if fill > 0 else 0.0
        tilt_gain = 0.50 + 0.90 * self._steepness()
        coh_loss = 1.0 - 0.40 * self.effective_cohesion()
        densify = 1.0 + 0.12 * self.packing
        return self.powder.feed_factor_g_per_rev * fill_factor * tilt_gain \
            * coh_loss * densify

    def hopper_fill_frac(self) -> float:
        return self.hopper_g / self.context.hopper_capacity_g

    def telemetry(self) -> _Telemetry:
        grams, stable = self.read_balance()
        return _Telemetry(
            t_s=self.t_s, dispensed_g=self.dispensed_g, balance_g=grams,
            balance_stable=stable, dose_rate_g_per_s=self.dose_rate_g_per_s,
            lip_g=self.lip_g, in_flight_g=sum(m for _, m in self.in_flight),
            hopper_fill_frac=self.hopper_fill_frac(),
            effective_cohesion=self.effective_cohesion(),
            feed_factor_g_per_rev=self.feed_factor_g_per_rev(),
            auger_rpm=self.auger_rpm, tilt_deg=self.tilt_deg, arched=self.arched,
        )

    # ---------------- time stepping ----------------

    def step(self, dt: float) -> None:
        """Advance the world by dt seconds (subdivided for stability)."""
        remaining = dt
        while remaining > 1e-9:
            h = min(0.05, remaining)
            self._substep(h)
            remaining -= h

    def run(self, duration_s: float, dt: float = 0.05) -> None:
        """Alias of step(); dt kept for API symmetry (step() subdivides)."""
        self.step(duration_s)

    # ---------------- internals ----------------

    def _substep(self, h: float) -> None:
        self.t_s += h
        landed = self._update_flight()
        self._update_tilt(h)
        self._update_moisture(h)
        self._update_arching(h)

        # Auger conveys hopper powder to the lip reservoir.
        rev = (self.auger_rpm / 60.0) * h
        self.auger_angle_rev += rev
        self.total_auger_rev += rev
        conveyed = self.feed_factor_g_per_rev() * rev
        if conveyed > 0.0:
            fill = self.hopper_fill_frac()
            if fill < 0.30:  # starved screw: pulsating discharge
                pulse = 1.0 + 0.6 * math.sin(2.0 * math.pi * self.auger_angle_rev)
                conveyed *= max(0.0, pulse)
            conveyed *= max(0.0, 1.0 + self.rng.gauss(0.0, 0.10))
            conveyed = min(conveyed, self.hopper_g)
            self.hopper_g -= conveyed
            self.lip_g += conveyed
            # Rotation loosens tapped-down powder and shakes the frame a bit.
            self.packing = max(0.0, self.packing - 0.05 * rev)
            self._disturb_until_s = max(self._disturb_until_s, self.t_s + 0.3)

        # Lip reservoir discharge: gravity drainage (strong when steep),
        # avalanche overflow above the tilt/cohesion-dependent capacity,
        # and vibration-assisted flow.
        s = self._steepness()
        coh = self.effective_cohesion()
        cap = self.LIP_BASE_CAPACITY_G * (1.0 - 0.80 * s) \
            * (0.5 + 1.5 * coh) * (self.powder.angle_of_repose_deg / 35.0)
        drain_rate = 1.2 * s * s * (1.0 - 0.6 * coh) \
            + 1.5 * self.vibration_duty * (1.0 - 0.4 * coh)   # per second
        out = self.lip_g * min(1.0, drain_rate * h)
        if self.lip_g - out > cap:  # overflow avalanches off within ~0.3 s
            out += (self.lip_g - out - cap) * min(1.0, h / 0.3)
        out = self._quantized(out, coh) if coh > 0.35 else out
        out = min(out, self.lip_g)
        self.lip_g -= out
        self._launch(out)

        if self.vibration_duty > 0.0:
            self.packing = min(1.0, self.packing + 0.05 * self.vibration_duty * h)
            self._disturb_until_s = max(self._disturb_until_s, self.t_s + 0.2)

        # Balance: first-order settle toward true vial mass.
        alpha = 1.0 - math.exp(-h / max(1e-3, self.balance_integration_s))
        self._balance_filt_g += alpha * (self.dispensed_g - self._balance_filt_g)
        self._prev_sample_age_s += h
        if self._prev_sample_age_s >= 0.5:
            self._balance_prev_g = self._balance_filt_g
            self._prev_sample_age_s = 0.0

        # Smoothed true dose rate (what an ideal rate sensor would report).
        inst = landed / h
        self.dose_rate_g_per_s += min(1.0, h / 0.4) * (inst - self.dose_rate_g_per_s)

    def _launch(self, grams: float) -> None:
        if grams > 1e-7:
            self.in_flight.append([self.t_s + self.FALL_TIME_S, grams])

    def _update_flight(self) -> float:
        landed = 0.0
        keep = []
        for land_time, grams in self.in_flight:
            if land_time <= self.t_s:
                landed += grams
            else:
                keep.append([land_time, grams])
        self.in_flight = keep
        if landed > 0.0:
            self.dispensed_g += landed
            if landed > 5e-4:  # a visible impact shakes the pan briefly
                self._disturb_until_s = max(self._disturb_until_s, self.t_s + 0.15)
        return landed

    def _update_tilt(self, h: float) -> None:
        d = self.tilt_target_deg - self.tilt_deg
        step = self.TILT_SLEW_DEG_S * h
        self.tilt_deg += d if abs(d) <= step else math.copysign(step, d)
        if abs(d) > 1e-6:
            self._disturb_until_s = max(self._disturb_until_s, self.t_s + 0.3)

    def _update_moisture(self, h: float) -> None:
        self.moisture += self.powder.hygroscopicity \
            * (self.context.humidity_pct_rh / 100.0) * (h / 3600.0)

    def _update_arching(self, h: float) -> None:
        """Cohesive powders can bridge over the hopper throat and starve the
        screw; rotation slowly and taps quickly break the arch."""
        coh = self.effective_cohesion()
        if not self.arched:
            if coh > 0.45 and self.auger_rpm > 0.0:
                p = 0.05 * (coh - 0.45) / 0.55 * h * (self.auger_rpm / 30.0)
                if self.rng.random() < p:
                    self.arched = True
        elif self.auger_rpm > 0.0 and self.rng.random() < 0.02 * h:
            self.arched = False

    def _quantized(self, expected_g: float, coh: float) -> float:
        """Cohesive powder leaves in clumps, not a smooth stream: draw an
        integer number of clumps whose size grows with cohesion/particles."""
        if expected_g <= 0.0:
            return 0.0
        clump = max(2e-4, 0.030 * coh
                    * (self.powder.particle_size_um / 100.0) ** 0.5
                    * self.powder.density_g_per_cm3 / 1.2)
        lam = expected_g / clump
        if lam > 50:  # effectively continuous
            return expected_g * max(0.0, 1.0 + self.rng.gauss(0.0, 0.05))
        # Poisson draw via Knuth (lam is small here)
        l_exp, k, p = math.exp(-lam), 0, 1.0
        while True:
            p *= self.rng.random()
            if p <= l_exp:
                break
            k += 1
        return k * clump

    def _steepness(self) -> float:
        """0 at horizontal ... 1 at plate 45 deg (rig 'vertical')."""
        return math.sin(math.radians(self.tilt_deg)) / math.sin(math.radians(45.0))

    def _disturbed(self) -> bool:
        return self.t_s < self._disturb_until_s or self.auger_rpm > 0.0 \
            or self.vibration_duty > 0.0

    def _balance_noise_sd(self) -> float:
        return 0.008 if self._disturbed() else 0.00015


__all__ = ["Powder", "Context", "PowderDoserSim", "POWDERS"]

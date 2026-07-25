"""Reduced-order "digital twin" of the powder doser, v2 (issue #123 / PR #124).

A fast compartment model of the rig -- hopper -> auger screw -> tube-lip
reservoir -> free fall -> vial on balance -- for prototyping and pre-tuning
dosing control policies (three-phase, rate-PI+KF, dual UKF, MPC, BO) before
hardware runs.  NOT a particle-level physics model (see the physics-engines /
particle-methods Edison answers for that ladder).

v2 applies the Edison analysis critique (edison/query_out/sim_critique.answer.md)
of v1 as a benchmark instrument.  The "required before any ranking claim" list:

1.  Screw transport hold-up: a 3-cell, revolution-domain compartment chain
    between hopper and lip (powder stops moving when the screw stops; mean
    transport distance N_TR auger revolutions).  Screw starts pre-primed or
    empty per Context.
2.  feed_factor_g_per_rev is now a true reference-condition parameter (full
    hopper, 45 deg tilt, dry powder, loose packing); all gains are normalized
    to 1 at that reference.
3.  No privileged telemetry: tap() returns None; true dose rate / lip mass /
    screw contents are exposed only via telemetry() for scoring.  Controllers
    must use read_balance() only.
4.  Balance is sample-and-hold on its own 10 Hz serial clock: one noise
    realization per tick, cached between ticks; repeated reads cannot average
    noise away or perturb the physics.
5.  Split random streams (process / events / balance / run-level) so a
    controller's read pattern cannot alter the physical trajectory.
6.  Conveying noise is timestep-invariant: run-level feed-factor offset +
    within-dose Ornstein-Uhlenbeck (log AR(1)) drift + screw-angle harmonics,
    instead of independent 10 % draws per 50 ms substep.
7.  Balance session bias + slow random-walk drift, and colored (AR(1) +
    tonal) vibration noise whose amplitude follows actuator activity with
    uncertain decay after actuators stop.
8.  Lip discharge is a marked avalanche point process (hazard grows with
    excess over a logistic tilt-dependent capacity; lognormal avalanche
    masses) with an optional smooth component for free-flowing powders.
9.  Taps follow a hurdle model: logistic release probability (zero-yield taps
    exist), then a Beta-distributed released fraction whose mean is
    tilt/cohesion/consolidation-dependent, calibrated to ~1-30 mg per tap
    (v1's 0.35 prefactor was ~3x too large).
10. Blockage is a three-state process (flowing / starved-rathole / blocked)
    with formation and clearing hazards, replacing the binary arch.

Also per the critique: packing is split into hopper compaction, screw fill
density, and lip consolidation; moisture follows sorption-relaxation toward an
RH-dependent equilibrium (no direct RH term in cohesion, no unbounded uptake);
free-fall time is jittered.  Coefficients remain PROVISIONAL until the
calibration experiments in the critique are run; the benchmark therefore
reports "simulation sensitivity study" results, not hardware evidence.

Units match the firmware (main_three_phase.py): grams, seconds, mounting-plate
degrees for tilt (0 = horizontal ... 45 = rig "vertical"), auger RPM / auger
degrees for rotation.

Example::

    from powder_sim import PowderDoserSim, Context, POWDERS

    sim = PowderDoserSim(POWDERS["salt"], Context(humidity_pct_rh=35.0), seed=1)
    sim.set_tilt_deg(45.0)
    sim.set_auger_rpm(55.0)
    while sim.read_balance()[0] < 1.5:
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
    """Material parameters.  feed_factor_g_per_rev is defined at the REFERENCE
    condition: full hopper, 45 deg tilt, dry, loose packing.  All *_factor
    values are dimensionless and provisional pending bench calibration."""

    name: str
    feed_factor_g_per_rev: float   # g conveyed per auger rev at reference
    density_g_per_cm3: float       # bulk density (sets clump/avalanche size)
    cohesion: float                # 0 free-flowing ... 1 very cohesive (dry)
    moisture_sensitivity: float    # d(cohesion)/d(moisture fraction)
    hygroscopicity: float          # equilibrium moisture fraction at 100 %RH
    angle_of_repose_deg: float     # holds more powder at the lip when high
    particle_size_um: float        # sets discharge granularity / noise quanta
    # tilt-gain shape G_theta = g0 + (1-g0) * s^p ; normalized to 1 at 45 deg
    tilt_g0: float = 0.40
    tilt_exp: float = 1.0
    # fill-gain shape (normalized to 1 at full hopper)
    fill_h50: float = 0.15
    fill_gamma: float = 1.0
    # continuous cohesive feed loss G_C = exp(-beta_c * (C - C_dry))
    beta_c: float = 1.2


#: Starting library. Values are plausible-order estimates to be calibrated
#: against bench data (see README); salt is loosely anchored to PR #124 videos.
POWDERS = {
    "salt": Powder(
        name="salt", feed_factor_g_per_rev=0.35, density_g_per_cm3=1.20,
        cohesion=0.08, moisture_sensitivity=1.5, hygroscopicity=0.05,
        angle_of_repose_deg=32.0, particle_size_um=400.0,
        tilt_g0=0.40, tilt_exp=1.0,
    ),
    "AlSi10Mg": Powder(  # gas-atomized spheres: dense, very free flowing
        name="AlSi10Mg", feed_factor_g_per_rev=0.55, density_g_per_cm3=1.45,
        cohesion=0.04, moisture_sensitivity=0.8, hygroscopicity=0.005,
        angle_of_repose_deg=27.0, particle_size_um=45.0,
        tilt_g0=0.55, tilt_exp=0.8,
    ),
    "stainless_316L": Powder(
        name="stainless_316L", feed_factor_g_per_rev=1.60, density_g_per_cm3=4.00,
        cohesion=0.05, moisture_sensitivity=0.6, hygroscopicity=0.003,
        angle_of_repose_deg=29.0, particle_size_um=35.0,
        tilt_g0=0.50, tilt_exp=0.9,
    ),
    "silicon": Powder(  # angular, somewhat cohesive when fine
        name="silicon", feed_factor_g_per_rev=0.40, density_g_per_cm3=1.10,
        cohesion=0.25, moisture_sensitivity=2.0, hygroscopicity=0.025,
        angle_of_repose_deg=38.0, particle_size_um=75.0,
        tilt_g0=0.30, tilt_exp=1.3, fill_h50=0.20,
    ),
    "lactose": Powder(  # cheap cohesive surrogate for bench experiments
        name="lactose", feed_factor_g_per_rev=0.25, density_g_per_cm3=0.60,
        cohesion=0.55, moisture_sensitivity=2.5, hygroscopicity=0.06,
        angle_of_repose_deg=45.0, particle_size_um=60.0,
        tilt_g0=0.25, tilt_exp=1.5, fill_h50=0.25, fill_gamma=1.4,
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
    screw_primed: bool = True         # screw flights pre-loaded vs empty
    sorption_tau_hours: float = 8.0   # moisture uptake relaxation time


@dataclass
class _Telemetry:
    """Ground truth for SCORING AND DIAGNOSTICS ONLY -- controllers being
    benchmarked must never receive these fields (Edison fairness critique)."""

    t_s: float
    dispensed_g: float
    balance_g: float
    balance_stable: bool
    dose_rate_g_per_s: float
    lip_g: float
    screw_g: float
    in_flight_g: float
    hopper_fill_frac: float
    effective_cohesion: float
    feed_factor_g_per_rev: float
    auger_rpm: float
    tilt_deg: float
    flow_state: str


# --------------------------------------------------------------------------
# The simulator
# --------------------------------------------------------------------------

class PowderDoserSim:
    """Continuous-time compartment model, advanced with step(dt).  Physics
    evolve on a fixed internal clock regardless of the caller's dt."""

    MAX_TILT_DEG = 45.0          # plate 45 deg = rig "vertical"
    MAX_AUGER_RPM = 109.0        # firmware clamp (240 motor RPM / 2.2)
    TILT_SLEW_DEG_S = 90.0       # servo speed at the plate
    FALL_TIME_S = 0.15           # mean lip -> vial free fall
    BALANCE_RESOLUTION_G = 1e-4  # HR-100A readability
    BALANCE_RATE_HZ = 10.0       # serial stream rate (sample-and-hold clock)
    SUBSTEP_S = 0.05             # fixed physics timestep

    # screw transport: 3 cells, mean transport distance N_TR auger revs
    N_CELLS = 3
    N_TR_REV = 1.0

    def __init__(self, powder: Powder, context: Context | None = None,
                 seed: int | None = None, balance_integration_s: float = 0.7):
        self.powder = powder
        self.context = replace(context) if context else Context()
        # --- split random streams (critique item 5): a controller's read
        # pattern must not perturb the physical trajectory ---
        root = random.Random(seed)
        self.process_rng = random.Random(root.getrandbits(64))
        self.event_rng = random.Random(root.getrandbits(64))
        self.balance_rng = random.Random(root.getrandbits(64))
        run_rng = random.Random(root.getrandbits(64))
        self.t_s = 0.0

        # --- powder state ---
        self.hopper_g = self.context.hopper_capacity_g * self.context.hopper_fill_frac
        self.lip_g = 0.0
        self.in_flight: list[list[float]] = []   # [land_time_s, grams]
        self.dispensed_g = 0.0                   # true grams in the vial
        # sorption-relaxation moisture: starts part-way toward equilibrium
        m_eq = self._moisture_eq()
        self.moisture = m_eq * (1.0 - math.exp(
            -self.context.exposure_hours / self.context.sorption_tau_hours))
        # packing, split by location (critique: one global var was wrong)
        self.hopper_compaction = 0.0
        self.screw_density = 0.0
        self.lip_consolidation = 0.0
        self.flow_state = "flowing"              # flowing | starved | blocked
        self.auger_angle_rev = run_rng.uniform(0.0, 1.0)

        # screw cells (g per cell); primed = steady-state at reference feed
        self._k_cell = self.N_CELLS / self.N_TR_REV   # per-rev transfer coeff
        prime = (self.powder.feed_factor_g_per_rev / self._k_cell
                 if self.context.screw_primed else 0.0)
        self.screw_cells = [prime * run_rng.uniform(0.7, 1.3)
                            for _ in range(self.N_CELLS)]

        # run-level and within-dose feed variation (critique item 6)
        self._ff_run = math.exp(run_rng.gauss(0.0, 0.05))
        self._ff_ou = 0.0                        # log-domain OU state
        self._ff_ou_tau = 5.0
        self._ff_ou_sd = 0.08
        self._pulsation_phase = run_rng.uniform(0.0, 2.0 * math.pi)

        # --- actuator state ---
        self.auger_rpm = 0.0
        self.tilt_deg = 0.0
        self.tilt_target_deg = 0.0
        self.vibration_duty = 0.0

        # --- balance state (sample-and-hold, own clock; critique item 4) ---
        self.balance_integration_s = balance_integration_s
        self._balance_filt_g = 0.0
        self._tare_g = 0.0
        self._bal_bias_g = run_rng.gauss(0.0, 0.002)   # session bias
        self._bal_drift_g = 0.0                        # slow random walk
        self._vib_ar = 0.0                             # colored vibration
        self._vib_level = 0.0                          # envelope (g)
        self._vib_phase = run_rng.uniform(0.0, 2.0 * math.pi)
        self._next_sample_s = 0.0
        self._sample_hold: tuple[float, bool] = (0.0, True)
        self._recent: list[float] = []                 # last few raw samples
        self._disturb_level_target = 0.0

        # --- outputs (scoring only) ---
        self.dose_rate_g_per_s = 0.0
        self.total_taps = 0
        self.total_auger_rev = 0.0

    # ---------------- actuator commands ----------------

    def set_auger_rpm(self, rpm: float) -> None:
        self.auger_rpm = max(0.0, min(self.MAX_AUGER_RPM, rpm))

    def set_tilt_deg(self, plate_deg: float) -> None:
        self.tilt_target_deg = max(0.0, min(self.MAX_TILT_DEG, plate_deg))

    def set_vibration_duty(self, duty: float) -> None:
        self.vibration_duty = max(0.0, min(1.0, duty))

    def rotate_degrees(self, auger_deg: float, rpm: float) -> None:
        """Blocking incremental rotation (firmware's default mode)."""
        rpm = max(1e-6, min(self.MAX_AUGER_RPM, rpm))
        duration = (auger_deg / 360.0) / (rpm / 60.0)
        old = self.auger_rpm
        self.auger_rpm = rpm
        self.step(duration)
        self.auger_rpm = old

    # v1 API name kept for compatibility
    def rotate_auger_deg(self, auger_deg: float, rpm: float, dt: float = 0.05) -> None:
        self.rotate_degrees(auger_deg, rpm)

    def tap(self) -> None:
        """One solenoid tap.  Returns None: the controller must observe the
        effect through the balance, as on hardware (fairness critique).

        Hurdle model: logistic release probability (zero-yield taps are
        common), then a Beta-distributed fraction of the lip charge, with
        mean rising with tilt and falling with cohesion and consolidation.
        Calibrated provisionally to ~1-30 mg/tap (README bench range)."""
        self.total_taps += 1
        s = self._steepness()
        coh = self.effective_cohesion()
        rng = self.event_rng
        # release probability: near-certain for a loaded lip at steep tilt,
        # drops for empty lips and cohesive powder
        x = (-0.2 + 2.6 * s - 2.0 * coh - 1.0 * self.lip_consolidation
             + 0.9 * math.log(max(self.lip_g, 1e-5) / 0.05))
        p_release = 1.0 / (1.0 + math.exp(-x))
        if rng.random() < p_release and self.lip_g > 1e-6:
            # mean released fraction ~0.10 at steep/dry, less when shallow,
            # cohesive, or tap-consolidated (v1's 0.35 was ~3x high)
            mu_x = (-3.5 + 1.4 * s - 1.6 * coh - 1.5 * self.lip_consolidation)
            mu = 1.0 / (1.0 + math.exp(-mu_x))
            kappa = 8.0
            frac = min(0.95, max(0.005, rng.betavariate(
                mu * kappa, (1.0 - mu) * kappa)))
            ejected = min(self.lip_g, frac * self.lip_g)
            self.lip_g -= ejected
            self._launch(ejected)
        # side effects
        self.lip_consolidation = min(1.0, self.lip_consolidation + 0.15)
        self.screw_density = min(1.0, self.screw_density + 0.01)
        self.hopper_compaction = min(1.0, self.hopper_compaction + 0.004)
        if self.flow_state == "blocked" and rng.random() < 0.5:
            self.flow_state = "starved"
        elif self.flow_state == "starved" and rng.random() < 0.5:
            self.flow_state = "flowing"
        self._bump_vibration(0.010, 1.0)

    def tare(self) -> None:
        self._tare_g = self._sample_hold[0] + self._tare_g

    # ---------------- observation ----------------

    def read_balance(self) -> tuple[float, bool]:
        """(grams, stable) as the A&D streams them at BALANCE_RATE_HZ.
        Between serial ticks the last sample is returned unchanged, so
        polling faster than the balance yields no extra information and
        cannot perturb the simulation (fairness critique)."""
        return self._sample_hold

    def effective_cohesion(self) -> float:
        """Dry cohesion + capillary term from absorbed moisture only (no
        direct RH shortcut; humidity acts through sorption)."""
        coh = self.powder.cohesion \
            + self.powder.moisture_sensitivity * self.moisture
        return max(0.0, min(1.0, coh))

    def feed_factor_g_per_rev(self) -> float:
        """Current hopper->screw pickup, g per auger rev (the LIW 'feed
        factor'), including drift/pulsation.  Reference-normalized: equals
        powder.feed_factor_g_per_rev at full hopper, 45 deg, dry, loose."""
        if self.flow_state == "blocked":
            return 0.0
        p = self.powder
        h = self.hopper_fill_frac()
        if h <= 0.0:
            return 0.0
        g_fill = ((h / (h + p.fill_h50)) * (1.0 + p.fill_h50)) ** p.fill_gamma
        s = self._steepness()
        g_tilt = p.tilt_g0 + (1.0 - p.tilt_g0) * (s ** p.tilt_exp)
        coh = self.effective_cohesion()
        g_coh = math.exp(-p.beta_c * max(0.0, coh - p.cohesion))
        g_pack = 1.0 + 0.12 * self.screw_density
        base = p.feed_factor_g_per_rev * g_fill * g_tilt * g_coh * g_pack
        # run-level offset x OU drift x screw-angle harmonics (timestep-free)
        amp = 0.05 + 0.55 / (1.0 + math.exp((h - 0.25) / 0.08))
        pulse = 1.0 + amp * math.sin(
            2.0 * math.pi * self.auger_angle_rev + self._pulsation_phase) \
            + 0.3 * amp * math.sin(
                4.0 * math.pi * self.auger_angle_rev + 2.1 * self._pulsation_phase)
        drift = self._ff_run * math.exp(self._ff_ou - 0.5 * self._ff_ou_sd ** 2)
        if self.flow_state == "starved":
            base *= 0.30
        return max(0.0, base * drift * max(0.0, pulse))

    def hopper_fill_frac(self) -> float:
        return self.hopper_g / self.context.hopper_capacity_g

    def telemetry(self) -> _Telemetry:
        grams, stable = self._sample_hold
        return _Telemetry(
            t_s=self.t_s, dispensed_g=self.dispensed_g, balance_g=grams,
            balance_stable=stable, dose_rate_g_per_s=self.dose_rate_g_per_s,
            lip_g=self.lip_g, screw_g=sum(self.screw_cells),
            in_flight_g=sum(m for _, m in self.in_flight),
            hopper_fill_frac=self.hopper_fill_frac(),
            effective_cohesion=self.effective_cohesion(),
            feed_factor_g_per_rev=self.feed_factor_g_per_rev(),
            auger_rpm=self.auger_rpm, tilt_deg=self.tilt_deg,
            flow_state=self.flow_state)

    # v1 compatibility: binary view of the three-state blockage
    @property
    def arched(self) -> bool:
        return self.flow_state == "blocked"

    # ---------------- time stepping ----------------

    def step(self, dt: float) -> None:
        """Advance the world by dt seconds on the fixed internal clock."""
        remaining = dt
        while remaining > 1e-9:
            h = min(self.SUBSTEP_S, remaining)
            self._substep(h)
            remaining -= h

    def run(self, duration_s: float, dt: float = 0.05) -> None:
        self.step(duration_s)

    # ---------------- internals ----------------

    def _substep(self, h: float) -> None:
        self.t_s += h
        landed = self._update_flight()
        self._update_tilt(h)
        self._update_moisture(h)

        rng = self.process_rng
        # OU drift on log feed factor (timestep-invariant discretization)
        a = math.exp(-h / self._ff_ou_tau)
        self._ff_ou = a * self._ff_ou + self._ff_ou_sd \
            * math.sqrt(1.0 - a * a) * rng.gauss(0.0, 1.0)

        # --- screw transport (revolution domain; freezes when stopped) ---
        rev = (self.auger_rpm / 60.0) * h
        if rev > 0.0:
            self.auger_angle_rev += rev
            self.total_auger_rev += rev
            self._update_blockage(rev)
            pickup = min(self.feed_factor_g_per_rev() * rev, self.hopper_g)
            self.hopper_g -= pickup
            k = min(1.0, self._k_cell * rev)
            carry = pickup
            for i in range(self.N_CELLS):
                out = self.screw_cells[i] * k
                self.screw_cells[i] += carry - out
                carry = out
            self.lip_g += carry
            # rotation loosens tap-consolidated powder, shakes the frame
            self.screw_density = max(0.0, self.screw_density - 0.05 * rev)
            self.lip_consolidation = max(0.0, self.lip_consolidation - 0.8 * rev)
            self._bump_vibration(0.006, 0.3)

        # --- lip discharge: smooth trickle for free-flowing powders plus a
        # marked avalanche point process above the tilt-dependent capacity ---
        s = self._steepness()
        coh = self.effective_cohesion()
        cap = self._lip_capacity(s, coh)
        smooth = 1.2 * s * s * max(0.0, 1.0 - 2.2 * coh)     # /s, ~0 if cohesive
        out = self.lip_g * min(1.0, smooth * h)
        excess = max(0.0, self.lip_g - out - cap)
        lam = math.exp(-1.5 + 60.0 * excess + 2.0 * s - 2.5 * coh)  # events/s
        if self.event_rng.random() < 1.0 - math.exp(-lam * h):
            med = max(2e-4, 0.3 * excess + 0.01 * cap) \
                * (self.powder.particle_size_um / 100.0) ** 0.25
            mass = self.event_rng.lognormvariate(math.log(med), 0.7)
            out += min(mass, self.lip_g - out)
        if self.vibration_duty > 0.0:
            out += self.lip_g * min(1.0, 1.5 * self.vibration_duty
                                    * (1.0 - 0.4 * coh) * h)
            self.screw_density = min(1.0, self.screw_density
                                     + 0.05 * self.vibration_duty * h)
            self._bump_vibration(0.008, 0.2)
        out = min(out, self.lip_g)
        self.lip_g -= out
        self._launch(out)

        self._update_balance(h)

        # smoothed true landing rate (SCORING ONLY; controllers never see it)
        inst = landed / h
        self.dose_rate_g_per_s += min(1.0, h / 0.4) * (inst - self.dose_rate_g_per_s)

    def _lip_capacity(self, s: float, coh: float) -> float:
        """Retained lip mass: logistic decrease with tilt, more for cohesive
        / high-angle-of-repose powders (provisional until measured)."""
        c_min = 0.010
        c_max = 0.15 * (0.5 + 1.5 * coh) * (self.powder.angle_of_repose_deg / 35.0)
        theta = self.tilt_deg
        return c_min + max(0.0, c_max - c_min) / (1.0 + math.exp((theta - 22.0) / 8.0))

    def _update_blockage(self, rev: float) -> None:
        """flowing <-> starved (rat-hole) <-> blocked, hazards per revolution.
        Cohesion, hopper compaction and low fill promote formation; rotation
        slowly clears; taps clear quickly (see tap())."""
        rng = self.event_rng
        coh = self.effective_cohesion()
        h_fill = self.hopper_fill_frac()
        if self.flow_state == "flowing":
            lam = 0.10 * max(0.0, coh - 0.30) * (1.0 + self.hopper_compaction) \
                * (1.0 + max(0.0, 0.3 - h_fill) * 3.0)
            if rng.random() < 1.0 - math.exp(-lam * rev):
                self.flow_state = "starved"
        elif self.flow_state == "starved":
            lam_block = 0.15 * max(0.0, coh - 0.45)
            lam_clear = 0.08
            u = rng.random()
            if u < 1.0 - math.exp(-lam_block * rev):
                self.flow_state = "blocked"
            elif u > math.exp(-lam_clear * rev):
                self.flow_state = "flowing"
        else:  # blocked: rotation alone rarely clears it
            if rng.random() < 1.0 - math.exp(-0.02 * rev):
                self.flow_state = "starved"

    def _launch(self, grams: float) -> None:
        if grams > 1e-7:
            fall = max(0.05, self.FALL_TIME_S
                       + self.event_rng.gauss(0.0, 0.03))
            self.in_flight.append([self.t_s + fall, grams])

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
                self._bump_vibration(0.004, 0.3)
        return landed

    def _update_tilt(self, h: float) -> None:
        d = self.tilt_target_deg - self.tilt_deg
        step = self.TILT_SLEW_DEG_S * h
        self.tilt_deg += d if abs(d) <= step else math.copysign(step, d)
        if abs(d) > 1e-6:
            self._bump_vibration(0.005, 0.5)

    def _update_moisture(self, h: float) -> None:
        m_eq = self._moisture_eq()
        tau_s = self.context.sorption_tau_hours * 3600.0
        self.moisture += (m_eq - self.moisture) * min(1.0, h / tau_s)

    def _moisture_eq(self) -> float:
        """Linear-isotherm equilibrium moisture, mildly reduced when warm
        (provisional; replace with measured GAB/DVS isotherm)."""
        m = self.powder.hygroscopicity * self.context.humidity_pct_rh / 100.0
        return m * math.exp(-0.02 * (self.context.temperature_c - 22.0))

    # ---------------- balance (sample-and-hold serial model) ----------------

    def _bump_vibration(self, level_g: float, hold_s: float) -> None:
        self._disturb_level_target = max(self._disturb_level_target, level_g)
        self._disturb_hold_until = getattr(self, "_disturb_hold_until", 0.0)
        self._disturb_hold_until = max(self._disturb_hold_until,
                                       self.t_s + hold_s)

    def _update_balance(self, h: float) -> None:
        # first-order settling toward true pan mass
        alpha = 1.0 - math.exp(-h / max(1e-3, self.balance_integration_s))
        self._balance_filt_g += alpha * (self.dispensed_g - self._balance_filt_g)
        # vibration envelope: rises fast with actuation, decays with an
        # uncertain time constant after actuators stop (colored, not white)
        target = self._disturb_level_target
        if self.auger_rpm > 0.0:
            target = max(target, 0.006)
        if self.vibration_duty > 0.0:
            target = max(target, 0.008)
        if self.t_s > getattr(self, "_disturb_hold_until", 0.0):
            self._disturb_level_target = 0.0
        decay_tau = 0.4 + 0.4 * self.balance_rng.random()
        if target > self._vib_level:
            self._vib_level = target
        else:
            self._vib_level *= math.exp(-h / decay_tau)
        # slow drift random walk
        self._bal_drift_g += self.balance_rng.gauss(0.0, 5e-5) * math.sqrt(h)

        while self.t_s >= self._next_sample_s:
            self._next_sample_s += 1.0 / self.BALANCE_RATE_HZ
            rng = self.balance_rng
            # colored vibration: AR(1) + tone at ~23 Hz aliased into samples
            self._vib_ar = 0.8 * self._vib_ar + 0.6 * rng.gauss(0.0, 1.0)
            self._vib_phase += 2.0 * math.pi * 2.7 / self.BALANCE_RATE_HZ
            vib = self._vib_level * (0.7 * math.sin(self._vib_phase)
                                     + 0.5 * self._vib_ar)
            noise = rng.gauss(0.0, 0.00015)
            raw = (self._balance_filt_g + self._bal_bias_g
                   + self._bal_drift_g + vib + noise)
            grams = round((raw - self._tare_g) / self.BALANCE_RESOLUTION_G) \
                * self.BALANCE_RESOLUTION_G
            self._recent.append(grams)
            if len(self._recent) > 5:
                self._recent.pop(0)
            stable = (len(self._recent) == 5
                      and max(self._recent) - min(self._recent) < 1e-3)
            self._sample_hold = (grams, stable)

    def _steepness(self) -> float:
        """0 at horizontal ... 1 at plate 45 deg (rig 'vertical')."""
        return math.sin(math.radians(self.tilt_deg)) / math.sin(math.radians(45.0))


__all__ = ["Powder", "Context", "PowderDoserSim", "POWDERS"]

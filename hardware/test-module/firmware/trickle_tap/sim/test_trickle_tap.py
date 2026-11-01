"""CPython tests for the trickle-tap runner (no hardware needed).

Drives the real ``TrickleTapDoser`` (and through it the real
``ThreePhaseDoser`` read machinery and the pure-Python ``TrickleKF``)
against a virtual powder plant with a first-order balance lag, so the
identical code path the Pico runs is exercised end to end.

Also cross-checks ``TrickleKF`` against the trim study's numpy
``MassRateLagKF`` (``optimization/trim/estimators.py``) on a shared
input trace -- the "identical outputs" acceptance criterion from
``docs/trim-bench-plan.md`` section 4.  That one test is skipped with a
notice when numpy is not installed; everything else is stdlib-only.

Run:  python3 hardware/test-module/firmware/trickle_tap/sim/test_trickle_tap.py
"""

import random
import sys
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))          # the trickle_tap folder


# --- stub the Pico-only modules before the imports -------------------------

_config = types.ModuleType("config")
for _k, _v in (
        ("SCALE_UART_ID", 0), ("PIN_SCALE_TX", 12), ("PIN_SCALE_RX", 13),
        ("SCALE_BAUD", 19200), ("SCALE_BITS", 8), ("SCALE_PARITY", 0),
        ("SCALE_STOP", 1), ("SCALE_RESPONSE_TIMEOUT_MS", 1000),
        ("SCALE_STABLE_TIMEOUT_MS", 10000), ("STEPPER_SPEED_RPM", 30.0),
        ("STEPPER_MICROSTEPS", 8), ("STEPPER_FULL_STEPS_REV", 200),
        ("STEPPER_ACCEL_REV_PER_S2", 2.0), ("STEPPER_DISPENSE_DEG", 360.0),
        ("TAP_ON_MS", 60), ("TAP_OFF_MS", 150), ("TAP_PWM_DUTY", 1.0),
        ("TAP_COUNT", 1), ("SERVO_SPEED_DEG_PER_S", 60.0),
        ("SERVO_PRESETS", {"horizontal": 0, "vertical": 90}),
        ("TIC_UART_ID", 1), ("PIN_TIC_TX", 4), ("PIN_TIC_RX", 5),
        ("TIC_BAUD", 9600), ("TIC_READ_TIMEOUT_MS", 50),
        ("STEPPER_DIRECTION", 1), ("STEPPER_IDLE_DEENERGIZE", True)):
    setattr(_config, _k, _v)
sys.modules.setdefault("config", _config)

_tic = types.ModuleType("tic")


class _NoTic:
    def __init__(self, *a, **k):
        raise RuntimeError("sim tests do not touch the Tic")


_tic.TicSerial = _NoTic
sys.modules.setdefault("tic", _tic)

import main_three_phase as m3                                    # noqa: E402
from trickle_controller import (TrickleTapDoser, TELEMETRY_HEADER,  # noqa: E402
                                params_dict)
from trickle_kf import TrickleKF                                 # noqa: E402
import trickle_params                                            # noqa: E402


# ---------------------------------------------------------------------------
# Virtual clock, plant, and rig fakes
# ---------------------------------------------------------------------------

class VirtualClock:
    def __init__(self, plant=None):
        self.t = 0.0
        self.plant = plant

    def sleep_ms(self, ms):
        remaining = ms / 1000.0
        step = 0.01
        while remaining > 1e-9:
            dt = min(step, remaining)
            self.t += dt
            if self.plant is not None:
                self.plant.advance(dt)
            remaining -= dt

    def time(self):
        return self.t

    def ticks_ms(self):
        return int(self.t * 1000)


class Plant:
    """Hopper -> auger -> lip -> pan, with a first-order lagged balance.

    Deliberately simple and smooth (no slug quantisation) so the
    closed-loop assertions are about the CONTROLLER, not about a noisy
    plant realisation.  ``tau_bal_s`` defaults to the KF's belief so the
    happy-path tests run with a well-modelled balance; the robustness
    smoke test overrides it.
    """

    def __init__(self, ff_g_per_rev=0.113, tau_bal_s=0.7, lip_tau_s=0.4,
                 tap_yield_g=0.0065, hopper_g=50.0, seed=7,
                 quiet_sd=2e-4, noisy_sd=2e-3, afterflow_s=0.6,
                 holdup_g=0.10, dislodge_g=0.006):
        self.ff = ff_g_per_rev
        self.tau_bal = tau_bal_s
        self.lip_tau = lip_tau_s
        self.tap_yield = tap_yield_g
        self.hopper = hopper_g
        self.rng = random.Random(seed)
        self.quiet_sd = quiet_sd
        self.noisy_sd = noisy_sd
        self.afterflow_s = afterflow_s    # lip keeps draining this long
        self.holdup_g = holdup_g          # screw charge near the outlet
        self.dislodge_g = dislodge_g      # what a rest-nudge shakes loose
        self.rpm = 0.0
        self.tilt = 45.0
        self.lip = 0.0
        self.screw = 0.0
        self.pan = 0.0
        self.b = 0.0            # lagged balance state
        self.since_spin = 1e9
        self.max_rpm_seen = 0.0

    def set_rpm(self, rpm):
        self.rpm = max(0.0, rpm)
        self.max_rpm_seen = max(self.max_rpm_seen, self.rpm)

    def meter(self, revs):
        """Auger turns move powder from the hopper onto the lip."""
        mass = min(self.hopper, self.ff * revs)
        self.hopper -= mass
        self.lip += mass
        # spinning also charges the screw's outlet holdup
        self.screw = min(self.holdup_g, self.screw + 0.3 * mass)

    def nudge(self, revs):
        """A rotation from rest: meters, and dislodges some lip charge."""
        self.meter(revs)
        moved = min(self.screw, self.dislodge_g)
        self.screw -= moved
        self.lip += moved
        self.since_spin = 0.0             # shaken material can fall

    def tap_once(self):
        moved = min(self.lip, self.tap_yield)
        self.lip -= moved
        self.pan += moved

    def advance(self, dt):
        if self.rpm > 0.0:
            self.meter(self.rpm / 60.0 * dt)
            self.since_spin = 0.0
        else:
            self.since_spin += dt
        # The trim-study premise: at rest nothing arrives.  The lip only
        # discharges while actuating or during a short afterflow window.
        if self.rpm > 0.0 or self.since_spin < self.afterflow_s:
            k = (0.2 + 0.8 * max(0.0, self.tilt) / 25.0) / self.lip_tau
            flow = self.lip * min(1.0, k * dt)
            self.lip -= flow
            self.pan += flow
        # balance reading tracks the pan mass through a first-order lag
        self.b += (self.pan - self.b) * min(1.0, dt / max(1e-3, self.tau_bal))

    @property
    def actuating(self):
        return self.rpm > 0.0


class Reading:
    def __init__(self, grams, stable):
        self.grams = grams
        self.stable = stable
        self.overload = False
        self.unit = "g"


class FakeScale:
    def __init__(self, plant, clock):
        self.plant = plant
        self.clock = clock
        self.tare_ref = 0.0

    def _displayed(self):
        noisy = self.plant.actuating
        sd = self.plant.noisy_sd if noisy else self.plant.quiet_sd
        return (self.plant.b - self.tare_ref
                + self.plant.rng.gauss(0.0, sd))

    def read(self):
        return Reading(self._displayed(), not self.plant.actuating)

    def read_stable(self, timeout_ms=10000):
        return Reading(self._displayed(), True)

    def zero(self):
        self.tare_ref = self.plant.b
        self.clock.sleep_ms(1500)


class FakeStepper:
    def __init__(self, plant):
        self.plant = plant
        self.total_deg = 0.0
        self.velocity_calls = 0
        self._rpm = 30.0

    def set_speed(self, rpm):
        self._rpm = rpm

    def rotate_degrees(self, deg):
        self.total_deg += deg
        self.plant.nudge(deg / 360.0)

    def run_at_rpm(self, rpm):                # bulk velocity mode
        self.plant.set_rpm(rpm)

    def set_velocity_rpm(self, rpm):          # trickle PI commands
        self.velocity_calls += 1
        self.plant.set_rpm(rpm)

    def keep_alive(self):
        pass

    def stop(self):
        self.plant.set_rpm(0.0)

    def enable(self, on=True):
        pass


class FakeTap:
    def __init__(self, plant):
        self.plant = plant
        self.count = 0

    def tap(self, count=1, on_ms=None, off_ms=None):
        for _ in range(count):
            self.count += 1
            self.plant.tap_once()


class FakeServo:
    def __init__(self, plant):
        self.plant = plant
        self.angle = 45.0
        self.history = []

    def move_to(self, angle):
        self.angle = angle
        self.history.append(angle)
        self.plant.tilt = angle


def make_doser(plant, p_over=None, log=lambda *a: None):
    clock = VirtualClock(plant)
    scale = FakeScale(plant, clock)
    stepper = FakeStepper(plant)
    tap = FakeTap(plant)
    servo = FakeServo(plant)
    p = params_dict(trickle_params)
    p["log_to_flash"] = False                 # no files from tests
    p["print_every_n_polls"] = 10 ** 9
    if p_over:
        p.update(p_over)
    doser = TrickleTapDoser(stepper, tap, servo, scale, _config, p=p,
                            log=log, monotonic=clock.time,
                            sleep_ms=clock.sleep_ms,
                            ticks_ms=clock.ticks_ms)
    return doser, stepper, tap, servo, clock


# ---------------------------------------------------------------------------
# Check harness (same convention as sim/test_three_phase_reads.py)
# ---------------------------------------------------------------------------

_FAILURES = []


def check(what, ok):
    print("  {} {}".format("PASS" if ok else "FAIL", what))
    if not ok:
        _FAILURES.append(what)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_kf_matches_numpy_reference():
    try:
        import numpy  # noqa: F401
    except ImportError:
        print("  SKIP numpy not installed -- cross-check not run "
              "(pip install numpy to enable)")
        return
    trim_dir = _HERE.parents[4] / "optimization" / "trim"
    if not (trim_dir / "estimators.py").exists():
        print("  SKIP optimization/trim not present in this checkout")
        return
    sys.path.insert(0, str(trim_dir))
    from estimators import MassRateLagKF

    dt = 0.25
    ref = MassRateLagKF(dt, tau_bal_s=0.7)
    kf = TrickleKF(dt, tau_bal_s=0.7)
    ref.seed(0.05)
    kf.seed(0.05)
    rng = random.Random(3)
    worst = 0.0
    z = 0.05
    for i in range(400):
        z += max(0.0, rng.gauss(0.008, 0.004))     # a rising mass trace
        noisy = i % 7 != 0
        fresh = i % 5 != 4                          # stale frames mixed in
        u = None if i % 11 == 10 else 12.0 / 60.0   # input dropouts too
        m_ref, r_ref = ref.update(z, noisy, u_rev_s=u, ff=0.113, fresh=fresh)
        m_new, r_new = kf.update(z, noisy, u_rev_s=u, ff=0.113, fresh=fresh)
        worst = max(worst, abs(m_ref - m_new), abs(r_ref - r_new),
                    abs(ref.pred_sigma(0.3) - kf.pred_sigma(0.3)))
    check("pure-Python KF matches the numpy study filter to 1e-9 "
          "(worst |diff| = {:.2e})".format(worst), worst < 1e-9)
    check("clamp accounting matches ({} vs {})".format(
        ref.clamp_hits, kf.clamp_hits), ref.clamp_hits == kf.clamp_hits)
    sys.path.remove(str(trim_dir))


def test_kf_basic_properties():
    kf = TrickleKF(0.25, tau_bal_s=0.7)
    kf.seed(0.1)
    for _ in range(200):
        m, r = kf.update(0.1, False, u_rev_s=0.0, ff=0.113)
    check("KF converges to a constant reading (|m-0.1| < 0.2 mg)",
          abs(m - 0.1) < 2e-4)
    check("rate estimate decays to ~0 on a constant reading", r < 1e-4)
    sym = max(abs(kf.P[i][j] - kf.P[j][i])
              for i in range(3) for j in range(3))
    check("covariance stays symmetric (max asym {:.1e})".format(sym),
          sym < 1e-12)
    check("pred_sigma positive and finite", 0.0 < kf.pred_sigma(0.3) < 1.0)


def test_small_dose_trickles_to_tolerance():
    plant = Plant()
    doser, stepper, tap, servo, clock = make_doser(plant)
    target = 0.2
    res = doser.dose(target)
    err_mg = 1000.0 * (res.dispensed_g - target)
    stages = dict(res.phase_cycles)
    print("    -> {!r} (error {:+.1f} mg, {} taps)".format(
        res, err_mg, tap.count))
    check("dose completes ok", res.status == m3.DoseResult.OK)
    check("bulk skipped for a 0.2 g target", stages.get("bulk", -1) == 0)
    check("trickle stage ran (>= 10 polls)", stages.get("trickle", 0) >= 10)
    check("final mass within +/-5 mg of target (got {:+.1f} mg)".format(
        err_mg), abs(err_mg) <= 5.0)
    check("commanded rpm never exceeded the cap",
          plant.max_rpm_seen <= doser.p["trickle_rpm_cap"] + 1e-9)
    check("PI actually commanded velocities", stepper.velocity_calls > 5)


def test_large_dose_runs_bulk_first():
    plant = Plant()
    doser, stepper, tap, servo, clock = make_doser(plant)
    res = doser.dose(1.0)
    stages = dict(res.phase_cycles)
    err_mg = 1000.0 * (res.dispensed_g - 1.0)
    print("    -> {!r} (error {:+.1f} mg)".format(res, err_mg))
    check("dose completes ok", res.status == m3.DoseResult.OK)
    check("bulk ran for a 1 g target", stages.get("bulk", 0) > 0)
    check("final mass within +/-5 mg of target (got {:+.1f} mg)".format(
        err_mg), abs(err_mg) <= 5.0)


def test_within_tolerance_means_no_actuation():
    plant = Plant()
    doser, stepper, tap, servo, clock = make_doser(plant)
    res = doser.dose(0.004)          # 4 mg target, inside the 5 mg tolerance
    check("done immediately", res.status == m3.DoseResult.OK)
    check("auger never turned", stepper.total_deg == 0.0
          and plant.max_rpm_seen == 0.0)
    check("solenoid never fired", tap.count == 0)


def test_stalled_trickle_hands_to_taps():
    # Hopper runs dry mid-trickle; lip retains enough for the taps.
    plant = Plant(hopper_g=0.16, lip_tau_s=2.5)
    plant.lip = 0.03
    doser, stepper, tap, servo, clock = make_doser(
        plant, p_over={"stall_bail_s": 4.0})
    res = doser.dose(0.2)
    print("    -> {!r} ({} taps)".format(res, tap.count))
    check("stall did not abort the dose (status ok or stalled-in-taps)",
          res.status in (m3.DoseResult.OK, m3.DoseResult.STALLED))
    check("tap endgame engaged after the stall", tap.count > 0)


def test_telemetry_rows_are_well_formed():
    plant = Plant()
    doser, stepper, tap, servo, clock = make_doser(plant)
    doser.dose(0.2)
    n_cols = len(TELEMETRY_HEADER.split(","))
    bad = [r for r in doser.telemetry if len(r.split(",")) != n_cols]
    check("telemetry captured ({} rows)".format(len(doser.telemetry)),
          len(doser.telemetry) > 10)
    check("every row has the header's {} columns ({} bad)".format(
        n_cols, len(bad)), not bad)
    trickle_rows = [r for r in doser.telemetry
                    if r.split(",")[1] == "trickle"]
    check("trickle rows carry rpm/pred fields",
          trickle_rows and all(r.split(",")[11] != "" for r in trickle_rows))


def test_balance_lag_mismatch_smoke():
    # Plant lag 0.16 s (the drop-test value) vs the KF belief of 0.7 s --
    # the mismatch bench-plan test B4 probes.  Just proves the port keeps
    # running and finishes; the overshoot statistics are the study's job.
    plant = Plant(tau_bal_s=0.16)
    doser, stepper, tap, servo, clock = make_doser(plant)
    res = doser.dose(0.2)
    err_mg = 1000.0 * (res.dispensed_g - 0.2)
    print("    -> {!r} (error {:+.1f} mg)".format(res, err_mg))
    check("dose terminates gracefully under lag mismatch",
          res.status in (m3.DoseResult.OK, m3.DoseResult.OVERSHOOT,
                         m3.DoseResult.STALLED))
    check("error still inside +/-25 mg under mismatch", abs(err_mg) <= 25.0)


def test_live_param_change_applies():
    plant = Plant()
    doser, stepper, tap, servo, clock = make_doser(
        plant, p_over={"trickle_tilt_deg": 12.5, "bulk_enabled": False})
    res = doser.dose(0.5)
    stages = dict(res.phase_cycles)
    check("bulk_enabled=False forces a pure trickle start",
          stages.get("bulk", -1) == 0)
    check("trickle ran at the configured tilt (servo saw 12.5)",
          12.5 in servo.history and stages.get("trickle", 0) > 0)


def main():
    for fn in (test_kf_matches_numpy_reference,
               test_kf_basic_properties,
               test_small_dose_trickles_to_tolerance,
               test_large_dose_runs_bulk_first,
               test_within_tolerance_means_no_actuation,
               test_stalled_trickle_hands_to_taps,
               test_telemetry_rows_are_well_formed,
               test_balance_lag_mismatch_smoke,
               test_live_param_change_applies):
        print(fn.__name__)
        fn()
    if _FAILURES:
        print("\n{} check(s) FAILED: {}".format(
            len(_FAILURES), "; ".join(_FAILURES)))
        return 1
    print("\nall trickle-tap checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

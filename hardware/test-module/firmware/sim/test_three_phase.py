"""CPython smoke-test for the three-phase alternative main (PR #124).

Runs ``main_three_phase.ThreePhaseDoser`` -- the exact control loop the
Pico executes -- against the simulated rig from PR #100
(``sim/sim_rig.py``): virtual powder column, real A&D serial framing,
virtual clock so everything finishes instantly.

This branch does not carry PR #100's firmware modules, so the test
SKIPS (exit 0) unless ``config.py``, ``scale.py`` and ``sim/sim_rig.py``
sit next to ``main_three_phase.py`` -- i.e. run it from a checkout that
has both PRs' firmware files in one folder:

    cd hardware/test-module/firmware
    python3 sim/test_three_phase.py            # PASS/FAIL summary
    python3 sim/test_three_phase.py -v 0.1     # verbose 0.1 g transcript
"""

import sys

try:
    from pathlib import Path
    _HERE = Path(__file__).resolve().parent
    sys.path.insert(0, str(_HERE))          # sim_rig
    sys.path.insert(0, str(_HERE.parent))   # config / scale / main_three_phase
    import config  # noqa: F401  (imported for its side of the doser wiring)
    from sim_rig import (PowderColumn, SimScaleUart, SimStepper, SimTap,
                         VirtualClock)
    import scale as scale_mod
    import main_three_phase as m3p
except ImportError as exc:
    print("SKIP: needs the PR #100 firmware modules (config.py, scale.py, "
          "sim/sim_rig.py) next to main_three_phase.py -- {}".format(exc))
    sys.exit(0)


class SimServo:
    """Records every commanded dispensing angle (plate degrees)."""

    def __init__(self):
        self.angle = float(config.SERVO_DEFAULT_DEG) / m3p.PLATE_GEAR_RATIO
        self.history = []

    def move_to(self, angle_deg):
        self.angle = angle_deg
        self.history.append(angle_deg)


class SimStepper3(SimStepper):
    """PR #100's position-move sim stepper plus the velocity mode the
    continuous phase drives (run_at_rpm / keep_alive / stop).

    While spinning, powder flow is advanced on every keep_alive()/stop()
    from the elapsed virtual-clock time.  PowderColumn.auger_rotate()
    also models motion time with a clock sleep, so the flow is fed to
    the column's mass bookkeeping directly here instead of through it.
    """

    def __init__(self, column, clock):
        SimStepper.__init__(self, column)
        self.clock = clock
        self.rpm_history = []
        self.run_rpm = 0.0
        self.stop_calls = 0
        self._last_advance = 0.0

    def set_speed(self, rpm):
        self.rpm_history.append(rpm)

    def run_at_rpm(self, rpm):
        self.rpm_history.append(rpm)
        self.run_rpm = float(rpm)
        self._last_advance = self.clock.time()

    def keep_alive(self):
        self._advance_flow()

    def stop(self):
        self._advance_flow()
        self.run_rpm = 0.0
        self.stop_calls += 1

    def _advance_flow(self):
        if self.run_rpm <= 0:
            return
        now = self.clock.time()
        degrees = self.run_rpm / 60.0 * 360.0 * (now - self._last_advance)
        self._last_advance = now
        if degrees <= 0:
            return
        self.total_deg += degrees
        col = self.column
        committed = min(col.hopper_g, degrees / 360.0 * col.grams_per_rev)
        col.hopper_g -= committed
        landed = committed * (1.0 - col.inflight_fraction)
        col.pan_g += landed
        col.inflight_g += committed - landed
        col._disturb()


class SimTap3(SimTap):
    def tap(self, count=None, on_ms=None, off_ms=None):
        SimTap.tap(self, count)


def make_doser(log=lambda *_: None, **column_kwargs):
    clock = VirtualClock()
    column = PowderColumn(clock, **column_kwargs)
    sc = scale_mod.AndScale(SimScaleUart(column, clock),
                            response_timeout_ms=config.SCALE_RESPONSE_TIMEOUT_MS,
                            sleep_ms=clock.sleep_ms)
    stepper = SimStepper3(column, clock)
    tap = SimTap3(column)
    servo = SimServo()
    doser = m3p.ThreePhaseDoser(stepper, tap, servo, sc, config,
                                log=log, monotonic=clock.time,
                                sleep_ms=clock.sleep_ms)
    return doser, servo, stepper, tap


FAILURES = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("  {}: {} {}".format(tag, name, detail))
    if not cond:
        FAILURES.append(name)


def run_case(title, target_g, log=lambda *_: None, **column_kwargs):
    print("== {} ==".format(title))
    doser, servo, stepper, tap = make_doser(log=log, **column_kwargs)
    result = doser.dose(target_g)
    print("  {!r}".format(result))
    return result, servo, stepper, tap, doser


def main(argv):
    if len(argv) > 1 and argv[1] == "-v":
        # Verbose transcript of a single dose, printed exactly as the
        # Pico REPL would show it.
        target = float(argv[2]) if len(argv) > 2 else 0.1
        doser, _, _, _ = make_doser(log=print)
        doser.dose(target)
        return 0

    tol = m3p.PHASE3_TOLERANCE_G

    # 1. A 2 g dose exercises all three phases in order.
    result, servo, stepper, tap, doser = run_case("2 g dose, default powder",
                                                  2.0)
    check("status ok", result.ok, result.status)
    check("within tolerance", abs(result.dispensed_g - 2.0) <= tol,
          "{:.4f} g".format(result.dispensed_g))
    check("no overshoot", result.dispensed_g <= 2.0 + tol)
    check("phase order bulk/fine/tap",
          [n for n, _ in result.phase_cycles] == ["bulk", "fine", "tap"])
    check("all phases cycled", all(c > 0 for _, c in result.phase_cycles),
          str(result.phase_cycles))
    check("angles followed the phases",
          servo.history == [p["angle_deg"] for p in doser.phases],
          str(servo.history))
    check("per-phase rpm applied",
          stepper.rpm_history[:2] == [m3p.PHASE1_BULK["rotation_rpm"],
                                      m3p.PHASE2_FINE["rotation_rpm"]],
          str(stepper.rpm_history))

    # 2. A 0.3 g dose starts below the bulk threshold -> bulk skipped.
    result, servo, _, _, doser = run_case("0.3 g dose skips bulk", 0.3)
    check("status ok", result.ok, result.status)
    check("within tolerance", abs(result.dispensed_g - 0.3) <= tol,
          "{:.4f} g".format(result.dispensed_g))
    check("bulk skipped", dict(result.phase_cycles)["bulk"] == 0,
          str(result.phase_cycles))
    check("bulk angle never commanded",
          m3p.PHASE1_BULK["angle_deg"] not in servo.history,
          str(servo.history))

    # 3. A small dose that drains the in-flight powder mid-tap-phase
    #    must recover through the stall-nudge path.
    result, _, _, _, _ = run_case("0.1 g dose (tap-phase nudges)", 0.1)
    check("status ok", result.ok, result.status)
    check("within tolerance", abs(result.dispensed_g - 0.1) <= tol,
          "{:.4f} g".format(result.dispensed_g))

    # 4. Dense powder (4x the configured g/rev guess): the fixed steps
    #    are coarser, but the dose must still not overshoot the goal.
    result, _, _, _, _ = run_case("2 g dose, dense powder", 2.0,
                                  grams_per_rev=2.0)
    check("status ok", result.ok, result.status)
    check("no overshoot", result.dispensed_g <= 2.0 + tol,
          "{:.4f} g".format(result.dispensed_g))

    # 5. An (almost) empty hopper must abort as 'stalled', not hang.
    result, _, _, _, _ = run_case("empty hopper aborts", 2.0, hopper_g=0.05)
    check("status stalled", result.status == m3p.DoseResult.STALLED,
          result.status)

    # 6. Velocity mode: phase 1 continuous with an anticipation margin
    #    must converge through all three phases with no overshoot and
    #    must halt the auger exactly once (before the fine phase).
    print("== 2 g dose, continuous (velocity-mode) bulk ==")
    doser, servo, stepper, tap = make_doser()
    doser.phases[0]["continuous"] = 1
    doser.phases[0]["anticipation_g"] = 0.1
    result = doser.dose(2.0)
    print("  {!r}".format(result))
    check("status ok", result.ok, result.status)
    check("within tolerance", abs(result.dispensed_g - 2.0) <= tol,
          "{:.4f} g".format(result.dispensed_g))
    check("no overshoot", result.dispensed_g <= 2.0 + tol)
    check("all phases cycled", all(c > 0 for _, c in result.phase_cycles),
          str(result.phase_cycles))
    check("auger halted once and stayed halted",
          stepper.stop_calls == 1 and stepper.run_rpm == 0.0,
          "stops={} rpm={}".format(stepper.stop_calls, stepper.run_rpm))
    check("velocity rpm commanded",
          stepper.rpm_history[0] == m3p.PHASE1_BULK["rotation_rpm"],
          str(stepper.rpm_history))

    # 7. Velocity mode with an (almost) empty hopper must stop spinning
    #    and abort as 'stalled' instead of rotating forever.
    print("== continuous bulk, empty hopper aborts ==")
    doser, _, stepper, _ = make_doser(hopper_g=0.05)
    doser.phases[0]["continuous"] = 1
    result = doser.dose(2.0)
    print("  {!r}".format(result))
    check("status stalled (continuous)",
          result.status == m3p.DoseResult.STALLED, result.status)
    check("auger not left spinning", stepper.run_rpm == 0.0,
          str(stepper.run_rpm))

    print()
    if FAILURES:
        print("FAILED: {}".format(", ".join(FAILURES)))
        return 1
    print("all three-phase sim checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

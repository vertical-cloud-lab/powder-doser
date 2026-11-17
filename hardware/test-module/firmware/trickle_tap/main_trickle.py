"""Manual trickle-tap runner for the Pico -- run THIS file (PR #154).

Brings up the same bench rig as ``main_three_phase.py`` (Tic T500 auger,
DRV8871 tap solenoid, dual tilt servos, A&D HR-100A scale) but the ``g``
command doses with the KF + rate-PI **trickle-tap** controller from the
PR #124 twin instead of the fixed-increment three-phase scheme -- see
``trickle_controller.py``.  All knobs live in ``trickle_params.py``.

Quick start (details in README.md):

1. Open THIS folder in VS Code with the MicroPico extension and
   "Upload project to Pico".
2. "Run current file on Pico" with this file open.
3. In the Pico terminal:  ``g``       doses trickle_params.GOAL_MASS_G,
                          ``g 0.5``   doses 0.5 g,
                          ``set trickle_tilt_deg 15``  retunes live,
                          ``log``     prints the last dose's telemetry CSV,
                          ``!``       emergency stop.

Commands:
    h              help
    s              rig state + all trickle parameters
    g [grams]      trickle-tap dose (no argument = GOAL_MASS_G)
    set <k> <v>    change any trickle_params value live (s lists keys);
                   shorthands: goal -> goal_mass_g, tilt -> trickle_tilt_deg
    log            print the last dose's telemetry CSV (for plot_trickle.py)
    r <deg>        rotate auger by <deg> auger degrees (signed)
    t              tap (TAP_COUNT solenoid pulses)
    a <deg>        mounting plate to <deg> plate degrees
    p <preset>     plate preset (horizontal/tilt/vertical/tip)
    w / z          read / tare the scale
    !              emergency stop -- de-energise everything
"""

import time

import config
import main_three_phase as m3
from trickle_controller import TrickleTapDoser, TELEMETRY_HEADER


class TrickleStepper(m3.Stepper):
    """The base stepper plus a churn-free velocity setter for the PI loop.

    ``run_at_rpm``/``stop`` re-energise and re-zero around every call;
    the PI loop re-commands the speed every ~250 ms, so it needs a setter
    that just updates the Tic's max speed + target velocity in place.
    ``rpm <= 0`` decelerates to rest but stays energised (the loop may
    ask for flow again a beat later); ``stop()`` still fully halts.
    """

    def set_velocity_rpm(self, rpm):
        if rpm <= 0.0:
            if self._enabled:
                self.tic.set_target_velocity(0)
            return
        self.set_speed(rpm)                   # clamps to the auger ceiling
        if not self._enabled:
            self.enable(True)
        sign = 1 if config.STEPPER_DIRECTION >= 0 else -1
        usteps_per_s = self._rpm / 60.0 * self.steps_per_rev
        self.tic.set_target_velocity(sign * max(1, int(usteps_per_s * 10000)))


HELP = (
    "Trickle-tap manual runner (auger deg/RPM and plate deg -- gear\n"
    "ratios folded in).  Parameters: edit trickle_params.py, or:\n"
    "  h              this help\n"
    "  s              rig state + all trickle parameters\n"
    "  g [grams]      TRICKLE-TAP dose; bare g uses goal_mass_g\n"
    "  set <k> <v>    live-change a parameter (set goal 0.5 / set tilt 15)\n"
    "  log            print last dose telemetry CSV (paste into\n"
    "                 plot_trickle.py to see the PI behaviour)\n"
    "  r <deg> / t    rotate auger / tap solenoid\n"
    "  a <deg> / p <name>   plate angle / preset\n"
    "  w / z          read / tare scale\n"
    "  !              EMERGENCY STOP\n"
)

_ALIASES = {"goal": "goal_mass_g", "mass": "goal_mass_g",
            "tilt": "trickle_tilt_deg", "tol": "tolerance_g"}


class TrickleRig(m3.Rig):

    def __init__(self):
        print("[rig] bringing up powder-doser test module "
              "(TRICKLE-TAP manual runner, PR #154; no haptics)")
        self.stepper = TrickleStepper()
        self.tap = m3.Tap()
        self.servo = m3.Servo()
        self.scale = self._bring_up_scale()
        self.doser = (TrickleTapDoser(self.stepper, self.tap, self.servo,
                                      self.scale, config)
                      if self.scale is not None else None)
        print("[rig] ready -- 'h' for help, 'g' doses "
              "{} g".format(self.doser.p["goal_mass_g"]
                            if self.doser else "?"))

    def state(self):
        print("stepper: {} auger rpm (max ~{:.0f}), 1/{} microsteps; "
              "plate at {:.1f} deg; scale UART{} @ {}".format(
                  config.STEPPER_SPEED_RPM, m3.MAX_AUGER_RPM,
                  config.STEPPER_MICROSTEPS, self.servo.angle,
                  config.SCALE_UART_ID, config.SCALE_BAUD))
        if self.doser is None:
            print("scale: unavailable -- see boot message; dosing disabled")
            return
        print("trickle parameters ('set <key> <value>' to change):")
        for key in sorted(self.doser.p):
            print("  {} = {}".format(key, self.doser.p[key]))
        if self.doser.last_log_path:
            print("last telemetry: {} ({} rows)".format(
                self.doser.last_log_path, len(self.doser.telemetry)))

    def set_param(self, arg):
        if self.doser is None:
            print("[set] dosing unavailable (no scale)")
            return
        parts = arg.split()
        if len(parts) != 2:
            print("[set] usage: set <key> <value>   ('s' lists keys)")
            return
        key = _ALIASES.get(parts[0].lower(), parts[0].lower())
        if key not in self.doser.p:
            print("[set] unknown key {!r}; 's' lists them".format(key))
            return
        old = self.doser.p[key]
        try:
            if isinstance(old, bool):
                value = bool(int(float(parts[1])))
            elif isinstance(old, int):
                value = int(float(parts[1]))
            else:
                value = float(parts[1])
        except ValueError:
            print("[set] {!r} is not a number".format(parts[1]))
            return
        self.doser.p[key] = value
        print("[set] {} = {} (was {})".format(key, value, old))

    def print_log(self):
        if self.doser is None or not self.doser.telemetry:
            print("[log] no telemetry yet -- run a dose first")
            return
        print("--- BEGIN trickle telemetry CSV ---")
        print(TELEMETRY_HEADER)
        for row in self.doser.telemetry:
            print(row)
        print("--- END trickle telemetry CSV ---")

    def handle(self, line):
        line = line.strip()
        if not line:
            return
        cmd, _, arg = line.partition(" ")
        cmd = cmd.lower()
        try:
            if cmd in ("h", "?", "help"):
                print(HELP)
            elif cmd == "s":
                self.state()
            elif cmd in ("g", "dose"):
                if self.doser is None:
                    print("[scale] unavailable -- dosing needs the scale")
                    return
                arg = arg.strip()
                self.doser.dose(float(arg) if arg else None)
            elif cmd == "set":
                self.set_param(arg)
            elif cmd == "log":
                self.print_log()
            else:
                m3.Rig.handle(self, line)     # r/t/a/p/w/z/! and errors
        except Exception as exc:
            print("[rig] command failed: {!r}".format(exc))


def main():
    rig = TrickleRig()
    rig.state()
    while True:
        line = m3._readline_nonblocking()
        if line is not None:
            rig.handle(line)
        time.sleep_ms(10)


if __name__ == "__main__" and m3._ON_HARDWARE:
    main()

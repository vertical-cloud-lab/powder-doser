"""Trickle-tap runner with the REFILL-TAP endgame -- run THIS file instead
of ``main_trickle.py`` to try it.

Same rig, same bulk and KF + rate-PI trickle, same REPL (``main_trickle``
is imported, not copied); only the tap stage differs: after every tap
the running-average tap yield is compared with what is still needed,
and when it is far below, the auger turns REFILL_DEG between taps to
refill the tip until the taps yield enough again -- see
``refill_tap.py``.  Its knobs live in ``refill_params.py``; everything
else (goal mass, tilts, tolerance, PI) is still ``trickle_params.py``.

Quick start: upload ``refill_params.py``, ``refill_tap.py`` and this file
next to the trickle_tap build already on the Pico (PR #154's or PR
#166's), "Run current file on Pico" with this file open, then

    g                    dose GOAL_MASS_G with the refill-tap endgame
    set refill_deg 15    bigger refill rotation (any refill_* knob, live)
    set refill_enabled 0 the stock endgame on the same build (A/B)
    refills              the last dose's tap yields and refills
    !                    emergency stop

Every main_trickle command (s, g, set, log, res, r, t, a, p, w, z) works
as before.
"""

import sys
import time

if "/trickle_tap" not in sys.path:        # PR #166 layout (see main_trickle)
    sys.path.insert(0, "/trickle_tap")

import config                                            # noqa: E402
import main_three_phase as m3                            # noqa: E402
import main_trickle as mt                                # noqa: E402
from refill_tap import FIRMWARE_ID, RefillTapDoser       # noqa: E402

HELP = mt.HELP + (
    "Refill-tap endgame (refill_params.py):\n"
    "  refills        last dose: tap yields, each refill and its delivery\n"
    "  set refill_<k> <v>   e.g. set refill_deg 15, set refill_enabled 0\n"
    "                 (0 = the stock endgame, for A/B runs)\n"
)


class RefillRig(mt.TrickleRig):

    def __init__(self):
        print("[rig] bringing up powder-doser test module "
              "(TRICKLE-TAP runner, REFILL-TAP endgame; no haptics)")
        self.stepper = mt.TrickleStepper()
        self.tap = m3.Tap()
        self.servo = m3.Servo()
        self.scale = self._bring_up_scale()
        self.doser = (RefillTapDoser(self.stepper, self.tap, self.servo,
                                     self.scale, config)
                      if self.scale is not None else None)
        print("[rig] ready -- 'h' for help, 'g' doses "
              "{} g".format(self.doser.p["goal_mass_g"]
                            if self.doser else "?"))

    def state(self):
        # One firmware line, this build's: PR #166's dose executor reads
        # the first "firmware: " line and refuses anything but its own.
        print("firmware: {}".format(FIRMWARE_ID))
        try:
            import gc
            gc.collect()
            print("heap: {} bytes free, {} used".format(gc.mem_free(),
                                                        gc.mem_alloc()))
        except AttributeError:                # CPython sim
            pass
        print("stepper: {} auger rpm (max ~{:.0f}), 1/{} microsteps; "
              "plate at {:.1f} deg; scale UART{} @ {}".format(
                  config.STEPPER_SPEED_RPM, m3.MAX_AUGER_RPM,
                  config.STEPPER_MICROSTEPS, self.servo.angle,
                  config.SCALE_UART_ID, config.SCALE_BAUD))
        if self.doser is None:
            print("scale: unavailable -- see boot message; dosing disabled")
            return
        print("parameters ('set <key> <value>' to change; refill_* are "
              "the endgame's):")
        for key in sorted(self.doser.p):
            print("  {} = {}".format(key, self.doser.p[key]))
        if self.doser.last_log_path:
            print("last telemetry: {} ({} rows)".format(
                self.doser.last_log_path, len(self.doser.telemetry)))

    def handle(self, line):
        cmd = line.strip().partition(" ")[0].lower()
        try:
            if cmd in ("h", "?", "help"):
                print(HELP)
                return
            if cmd == "refills":
                if self.doser is None:
                    print("[refills] dosing unavailable (no scale)")
                else:
                    self.doser.print_refills()
                return
        except Exception as exc:
            print("[rig] command failed: {!r}".format(exc))
            return
        mt.TrickleRig.handle(self, line)


def main():
    rig = RefillRig()
    rig.state()
    while True:
        line = m3._readline_nonblocking()
        if line is not None:
            rig.handle(line)
        time.sleep_ms(10)


if __name__ == "__main__" and m3._ON_HARDWARE:
    main()

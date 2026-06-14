"""CPython simulation of the bench rig for closed-loop dosing tests.

Nothing here imports MicroPython modules -- the point is to run the
*production* control loop (``dosing.Doser``) and scale protocol parser
(``scale.parse_frame`` / ``scale.AndScale``) on a developer machine or
CI, against a physics-ish model of the powder column and the A&D
HR-100A's serial behaviour.

The model captures the failure modes that matter for the control
design:

* **Auger lag / overshoot** -- powder committed by an auger rotation
  does not all land instantly; a fraction stays "in flight" down the
  tube and keeps trickling onto the pan after the auger stops.  This
  is why the coarse phase must stop short of the target.
* **Tap transfer** -- each solenoid tap knocks a small, noisy amount
  of the in-flight/lip powder onto the pan.
* **Scale settling** -- after mass lands, the HR-100A reports ``US``
  (unstable) frames for a settling period before ``ST`` frames resume.
* **Serial framing** -- readings travel as real A&D standard-format
  ASCII frames through the same ``parse_frame`` code the Pico runs.
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class VirtualClock:
    """Deterministic stand-in for time.time/sleep so tests run instantly."""

    def __init__(self):
        self.t = 0.0

    def time(self):
        return self.t

    def sleep_ms(self, ms):
        self.t += ms / 1000.0


class PowderColumn:
    """Mass bookkeeping for hopper -> in-flight -> pan."""

    def __init__(self, clock, grams_per_rev=0.5, inflight_fraction=0.25,
                 tap_grams=0.0008, tap_jitter=0.5, hopper_g=1000.0,
                 settle_s=1.2, rng=None):
        self.clock = clock
        self.grams_per_rev = grams_per_rev
        self.inflight_fraction = inflight_fraction
        self.tap_grams = tap_grams
        self.tap_jitter = tap_jitter
        self.hopper_g = hopper_g
        self.settle_s = settle_s
        self.rng = rng or random.Random(20260612)
        self.pan_g = 0.0
        self.inflight_g = 0.0
        self.tare_g = 0.0
        self._stable_after = 0.0

    def _disturb(self):
        self._stable_after = self.clock.time() + self.settle_s

    # ---- actuator hooks ---------------------------------------------

    def auger_rotate(self, degrees):
        revs = abs(degrees) / 360.0
        committed = min(self.hopper_g, revs * self.grams_per_rev)
        self.hopper_g -= committed
        landed = committed * (1.0 - self.inflight_fraction)
        self.pan_g += landed
        self.inflight_g += committed - landed
        # Crude motion time: 60 RPM.
        self.clock.sleep_ms(int(revs * 1000))
        self._disturb()

    def tap(self, count):
        for _ in range(count):
            if self.inflight_g <= 0:
                break
            jitter = 1.0 + self.tap_jitter * (self.rng.random() * 2 - 1)
            moved = min(self.inflight_g, self.tap_grams * jitter)
            self.inflight_g -= moved
            self.pan_g += moved
            self.clock.sleep_ms(210)  # TAP_ON_MS + TAP_OFF_MS
        self._disturb()

    # ---- scale-side view --------------------------------------------

    def stable(self):
        return self.clock.time() >= self._stable_after

    def reading_g(self):
        return self.pan_g - self.tare_g

    def zero(self):
        self.tare_g = self.pan_g
        self._disturb()


class SimScaleUart:
    """Duck-typed ``machine.UART`` fed by the powder model.

    Speaks the same A&D standard-format frames the real HR-100A emits,
    so ``scale.AndScale``'s request/parse path is exercised end-to-end.
    """

    def __init__(self, column, clock, resolution_g=0.0001):
        self.column = column
        self.clock = clock
        self.resolution_g = resolution_g
        self._outbox = []

    def write(self, data):
        cmd = data.decode().strip() if isinstance(data, bytes) else data.strip()
        if cmd == "Q":
            grams = round(self.column.reading_g() / self.resolution_g) \
                * self.resolution_g
            header = "ST" if self.column.stable() else "US"
            self._outbox.append(
                "{},{:+010.4f}  g\r\n".format(header, grams).encode())
        elif cmd == "Z":
            self.column.zero()
        # Unknown commands are ignored, like a real balance with the
        # relevant function setting disabled.

    def any(self):
        return len(self._outbox)

    def readline(self):
        if self._outbox:
            return self._outbox.pop(0)
        # A real UART read blocks for its timeout; model a short wait.
        self.clock.sleep_ms(20)
        return None


class SimStepper:
    def __init__(self, column):
        self.column = column
        self.total_deg = 0.0

    def rotate_degrees(self, degrees):
        self.total_deg += degrees
        self.column.auger_rotate(degrees)


class SimTap:
    def __init__(self, column):
        self.column = column
        self.total_taps = 0

    def tap(self, count):
        self.total_taps += count
        self.column.tap(count)


def make_rig(clock=None, log=lambda *_: None, **column_kwargs):
    """Build (doser, column, clock) wired exactly like main.Rig does."""
    import config
    import dosing
    import scale as scale_mod

    clock = clock or VirtualClock()
    column = PowderColumn(clock, **column_kwargs)
    uart = SimScaleUart(column, clock)
    sc = scale_mod.AndScale(
        uart,
        response_timeout_ms=config.SCALE_RESPONSE_TIMEOUT_MS,
        sleep_ms=clock.sleep_ms)
    doser = dosing.Doser(SimStepper(column), SimTap(column), sc, config,
                         log=log, monotonic=clock.time,
                         sleep_ms=clock.sleep_ms)
    return doser, column, clock

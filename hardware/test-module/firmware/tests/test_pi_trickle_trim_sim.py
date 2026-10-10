"""Off-device smoke test for pi_trickle_trim.py (bench-plan section 4).

Fakes ``time`` (virtual clock -- sleeps advance it instantly) and
``main_three_phase`` (a small CMC-like plant: first-order rate lag toward
ff_true * rev/s, balance = first-order 0.16 s lag of true mass + noise,
5 Hz datum updates, taps ~0.1 mg, nudges pro-rata per degree) and then
imports the firmware script, which runs its whole battery in virtual
time.  Asserts the things a campaign dose depends on: the PI keeps rpm
inside [0, 45], every trial halts via the predictive cutoff or stall
bail, the trickle lands SHORT of target (the one-sided constraint), no
trial overshoots past +tol at cutoff, and the T rows parse.

Run:  python3 hardware/test-module/firmware/tests/test_pi_trickle_trim_sim.py
"""

import io
import os
import random
import re
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
FIRMWARE = os.path.dirname(HERE)

random.seed(20260908)

# ---------------------------------------------------------------- time
NOW_MS = [0]


def ticks_ms():
    return NOW_MS[0]


def ticks_diff(a, b):
    return a - b


def ticks_add(a, b):
    return a + b


def sleep_ms(ms):
    NOW_MS[0] += int(ms)
    PLANT.step(ms / 1000.0)


faketime = types.ModuleType("time")
faketime.ticks_ms = ticks_ms
faketime.ticks_diff = ticks_diff
faketime.ticks_add = ticks_add
faketime.sleep_ms = sleep_ms
faketime.sleep = lambda s: sleep_ms(int(s * 1000))

# --------------------------------------------------------------- plant


class Plant:
    """CMC-ish: ~6 mg/rev at 20 deg, rate lag 0.4 s, tau_bal 0.16 s."""

    FF_TRUE = 0.006          # g/rev at the trim tilt
    RATE_LAG_S = 0.4
    TAU_BAL_S = 0.16
    DATUM_S = 0.2            # balance updates its datum at 5 Hz

    def __init__(self):
        self.mass = 0.2321   # absolute pan grams at session start
        self.rate = 0.0
        self.bal = self.mass
        self.datum = self.mass
        self.datum_age = 0.0
        self.rev_s = 0.0
        self.stable_frac = 0.97

    def step(self, dt):
        while dt > 0.0:
            h = min(dt, 0.02)
            dt -= h
            r_cmd = self.FF_TRUE * self.rev_s
            self.rate += (r_cmd - self.rate) * min(1.0, h / self.RATE_LAG_S)
            self.mass += self.rate * h
            self.bal += (self.mass - self.bal) * (
                1.0 - pow(2.718281828, -h / self.TAU_BAL_S))
            self.datum_age += h
            if self.datum_age >= self.DATUM_S:
                self.datum_age = 0.0
                noise = random.gauss(0.0, 4e-4 if self.rev_s else 5e-5)
                self.datum = round(self.bal + noise, 4)

    def deposit(self, grams):
        self.mass += grams


PLANT = Plant()

# ------------------------------------------------------ main_three_phase


class _Reading:
    def __init__(self, grams, stable):
        self.grams = grams
        self.stable = stable


class Scale:
    def read(self):
        PLANT.step(0.03)                      # a Q-poll costs ~30 ms
        NOW_MS[0] += 30
        stable = (PLANT.rev_s == 0.0 and
                  random.random() < PLANT.stable_frac)
        return _Reading(PLANT.datum, stable)

    def read_stable(self, timeout_ms=8000):
        for _ in range(int(timeout_ms / 150)):
            r = self.read()
            NOW_MS[0] += 120
            PLANT.step(0.12)
            if r.stable:
                return r
        return None


class _Tic:
    def set_target_velocity(self, vel):
        PLANT.rev_s = abs(vel) / 10000.0 / 1600.0

    def halt_and_set_position(self, pos):
        PLANT.rev_s = 0.0


class Stepper:
    steps_per_rev = 1600.0

    def __init__(self):
        self.tic = _Tic()
        self._enabled = False
        self._position = 0

    def set_speed(self, rpm):
        self._rpm = rpm

    def enable(self, on):
        self._enabled = bool(on)
        if not on:
            PLANT.rev_s = 0.0

    def rotate_degrees(self, deg):
        self._enabled = True
        spin_s = abs(deg) / 360.0 / max(1e-6, self._rpm / 60.0)
        NOW_MS[0] += int(spin_s * 1000)
        PLANT.step(spin_s)
        PLANT.deposit(Plant.FF_TRUE * deg / 360.0)

    def keep_alive(self):
        pass


class Servo:
    def move_to(self, deg):
        self.angle = deg

    def _write_angle(self, deg):
        self.angle = deg


class Tap:
    def tap(self, count=1, on_ms=None, off_ms=None):
        for _ in range(count):
            NOW_MS[0] += 210
            PLANT.step(0.21)
            PLANT.deposit(abs(random.gauss(1e-4, 1e-4)))  # ~0.1 mg: CMC


fakem3 = types.ModuleType("main_three_phase")
fakem3.Scale = Scale
fakem3.Stepper = Stepper
fakem3.Servo = Servo
fakem3.Tap = Tap
fakem3.config = types.SimpleNamespace(STEPPER_DIRECTION=1)

# ----------------------------------------------------------- run + score
sys.modules["time"] = faketime
sys.modules["main_three_phase"] = fakem3
sys.path.insert(0, FIRMWARE)

captured = io.StringIO()
real_stdout = sys.stdout
sys.stdout = captured
try:
    import pi_trickle_trim  # noqa: F401  (import runs the battery)
finally:
    sys.stdout = real_stdout
    sys.modules["time"] = __import__("importlib").reload(
        sys.modules.pop("time") and __import__("time"))

out = captured.getvalue()
lines = out.splitlines()

t_rows = [l for l in lines if l.startswith("T,")]
d_rows = [l for l in lines if l.startswith("D,")]
h_rows = [l for l in lines if l.startswith("H,")]
assert any(l.startswith("RUN,END,ok") for l in lines), "no clean end"
assert len(t_rows) == 6, "expected 6 trials, got %d" % len(t_rows)
assert len(h_rows) >= 6, "every trial should log a halt decomposition"

rpm_max = 0.0
for l in d_rows:
    f = l.split(",")
    if f[3] == "trickle":
        rpm_max = max(rpm_max, float(f[7]))
assert rpm_max <= 45.0 + 1e-6, "PI exceeded the 45 rpm ceiling"
assert rpm_max > 5.0, "PI never actually commanded the auger"

for l in t_rows:
    f = l.split(",")
    target = float(f[2])
    err_mg = float(f[18])
    short_mg = float(f[19])
    verdict = f[21] if len(f) > 21 else f[-1]
    assert short_mg < 5.0, \
        "trickle should land short (one-sided): %s" % l
    assert err_mg < 25.0, "gross overshoot in sim: %s" % l
    assert verdict in ("ok", "tap_stalled", "stalled", "timeout"), verdict

n_ok = sum(1 for l in t_rows if l.rstrip().endswith(",ok"))
print("SIM OK: 6 trials, rpm_max %.1f, %d finished 'ok', halts: %s"
      % (rpm_max, n_ok,
         [re.split(",", h)[-1] for h in h_rows]))
print("virtual session time: %.1f min" % (NOW_MS[0] / 60000.0))
for l in t_rows:
    print("  " + l)

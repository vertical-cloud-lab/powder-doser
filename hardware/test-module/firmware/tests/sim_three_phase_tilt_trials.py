"""CPython dry run of three_phase_tilt_trials.py on the Pico's real controller.

Fakes ``time`` (a virtual clock) and the four hardware objects with a simple
salt plant (feed per auger rev by tilt, no flow at >= 58 deg like the full
tube on 2026-11-18, 0.45 s landing lag, 0.16 s balance lag, 5 Hz datum).
Everything else -- ``main_three_phase.ThreePhaseDoser``, ``balance_filter``
and ``scale.ScaleReading`` -- is the deployed code, so this needs a folder
with the Pico's copies of main_three_phase.py, config.py, scale.py, tic.py
and balance_filter.py (``mpremote fs cp :<file> <dir>/``; they are not on
this branch).

usage: python3 sim_three_phase_tilt_trials.py <dir with the Pico files> \
           hardware/test-module/firmware/three_phase_tilt_trials.py [seed] [n_trials] > sim.log
"""
import math, os, random, sys, types

M3_DIR, SCRIPT = sys.argv[1], sys.argv[2]
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 1
NTR = int(sys.argv[4]) if len(sys.argv) > 4 else 30
random.seed(SEED)

NOW = [0.0]   # virtual ms

class Plant:
    TAU_LAND = 0.45   # s, in-flight -> cup
    TAU_BAL = 0.16
    DATUM_S = 0.2
    def __init__(self):
        self.tilt = 0.0; self.rpm = 0.0; self.move_deg = 0.0; self.move_rpm = 0.0
        self.inflight = 0.0; self.mass = 12.3456; self.bal = self.mass; self.datum = self.mass
        self.age = 0.0; self.phase = 0.0; self.dispensed = 0.0
    def ff(self):   # g per auger rev vs plate tilt
        t = self.tilt
        if t >= 58: return 0.0
        return 0.01 + 0.0008 * min(t, 45)
    def step(self, dt):
        while dt > 1e-9:
            h = min(dt, 0.01); dt -= h
            rev = 0.0
            if self.rpm > 0:
                rev = self.rpm / 60.0 * h
            elif self.move_deg > 0:
                d = min(self.move_deg, self.move_rpm / 60.0 * 360.0 * h)
                self.move_deg -= d; rev = d / 360.0
            if rev > 0:
                self.phase = (self.phase + rev) % 1.0
                slug = 1.0 + 0.9 * math.sin(2 * math.pi * self.phase)
                self.inflight += self.ff() * rev * slug * random.uniform(0.7, 1.3)
            land = self.inflight * (h / self.TAU_LAND)
            self.inflight -= land; self.mass += land
            self.bal += (self.mass - self.bal) * (h / self.TAU_BAL)
            self.age += h
            if self.age >= self.DATUM_S:
                self.age = 0.0
                self.datum = round(self.bal + random.gauss(0, 0.0003), 4)
P = Plant()

def advance(ms):
    if ms <= 0: return
    NOW[0] += ms; P.step(ms / 1000.0)

ft = types.ModuleType("time")
ft.ticks_ms = lambda: int(NOW[0])
ft.ticks_diff = lambda a, b: a - b
ft.ticks_add = lambda a, b: a + b
ft.sleep_ms = lambda ms: advance(int(ms))
ft.sleep = lambda s: advance(s * 1000.0)
ft.time = lambda: int(NOW[0] / 1000.0)
ft.monotonic = lambda: NOW[0] / 1000.0
sys.modules["time"] = ft
sys.path.insert(0, M3_DIR)
import scale as scale_mod  # real driver module (ScaleReading)

class FakeScale:
    def __init__(self): self.response_timeout_ms = 1000; self.silent_until = -1
    def read(self):
        advance(random.uniform(8, 25))
        if NOW[0] < self.silent_until:
            advance(self.response_timeout_ms); return None
        st = "ST" if (P.rpm == 0 and P.move_deg <= 0 and abs(P.mass - P.bal) < 0.0005) else "US"
        return scale_mod.ScaleReading(st, P.datum, "g")

class FakeStepper:
    def __init__(self): self._rpm = 60.0; self.steps_per_rev = 200 * 8 * 2.2; self.ka = 0; self.en = False
    def set_speed(self, rpm): self._rpm = float(rpm)
    def enable(self, on=True): self.en = on
    def keep_alive(self): self.ka += 1
    def rotate_degrees(self, degrees):
        delta = int(round(degrees / 360.0 * self.steps_per_rev))
        if delta == 0: return
        P.move_deg += abs(degrees); P.move_rpm = self._rpm
        self._wait_estimated_time(delta)
    def _wait_estimated_time(self, delta):
        est_s = abs(delta) / max(1.0, self._rpm / 60.0 * self.steps_per_rev) + 0.2
        advance(est_s * 1000 + 2000)
    def run_at_rpm(self, rpm): self.set_speed(rpm); P.rpm = self._rpm
    def stop(self): P.rpm = 0.0

class FakeServo:
    def __init__(self): self.angle = 0.0
    def move_to(self, deg):
        advance(abs(deg - self.angle) / 30.0 * 1000.0)
        if abs(deg - self.angle) > 5 and random.random() < 0.05:
            P.inflight += random.uniform(0.0, 0.02)
        self.angle = deg; P.tilt = deg

class FakeTap:
    def tap(self, count=None, on_ms=None, off_ms=None):
        n = 3 if count is None else int(count)
        for _ in range(n):
            advance((60 if on_ms is None else on_ms) + (150 if off_ms is None else off_ms))
            P.inflight += random.uniform(0.0, 0.004) * (1.0 + P.tilt / 30.0)
    def _off(self): pass

import importlib.util
spec = importlib.util.spec_from_file_location("tilt_trials", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.N_TRIALS = NTR
res = mod.main(hw=(FakeStepper(), FakeTap(), FakeServo(), FakeScale()))
print("SIMDONE,virtual_min={:.1f}".format(NOW[0] / 60000.0), file=sys.stderr)

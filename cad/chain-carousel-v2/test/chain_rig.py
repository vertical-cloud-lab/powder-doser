#!/usr/bin/env python3
"""Drive and log the chain-carousel test rig v2 from a Raspberry Pi (issue #128).

Hardware (see BOM.md):
* CL86T closed-loop driver for the NEMA 34 on step/dir/enable through a 74AHCT125 (3.3 V GPIO in, 5 V out to
  PUL+/DIR+/ENA+, the minus terminals to ground).
* Two US5881 hall switches in the station hold-downs (open drain, 10k pull-ups to 3.3 V): INDEX, in the front
  hold-down, sees the magnet in every carriage's front tongue; HOME, in the back hold-down, only carriage 1's.
* Station: Actuonix P16-150-22-12-P on an Actuonix LAC board in RC mode (1.0-2.0 ms pulses = 0-150 mm); the pot is
  fed back inside the LAC. Its U-yoke holds Sam's electronics carriage on two stub pins at the carriage's
  centre-of-mass height.
* On the electronics carriage: the doser's NEMA 11 (20T steel pinion -> the auger's 44T gear, 2.2:1) on a DRV8825
  set to 0.45 A (Vref 0.225 V on Pololu's board): 0.067 N*m holding, under the 0.105 N*m that opens the dock at
  30 deg (station sim, SF 1.6); the 12 V tap solenoid on a DRV8871; the dock electromagnet (Adafruit 3872) on a
  logic-level MOSFET with a flyback diode, energized only while docked.
* HX711 on the 100 g load cell under the vial.

Geometry: one module = 8 pitches = 76.2 mm = 8/32 of a turn of the 32T drive sprocket, so at 4000 pulses/rev a
module is exactly 1000 steps. Targets are absolute step counts, so rounding never accumulates.

Run direction: the bottom run travels toward -y (RUN_DIRECTION = -1, clockwise seen from the back). Every lap turns
each module once about its own axis, which acts like an auger turn; this way it pulls powder back from the outlet,
the other way it pumps about one revolution's dose out (../auger-leakage/README.md). A positive index here always
means "the way the machine runs".

Docking: lift to 3 mm short of the plate, then finish while the pinion turns at 0.25 rev/s so it finds the gear's
gaps (gear-mesh study), then the magnet on.

Dose protocol (auger-leakage study): dock, magnet on, tilt to the dose angle, turn the auger, stop, hold 0.5 s at
the dose tilt (the tail falls into the vial), tilt back to level, then reverse the auger 1 revolution at rest
(--reverse-revs, auger revolutions; 2.2 NEMA 11 revolutions each). Never reverse while tilted: it adds dose.
Then the actuator pulls the plate back past the snap hooks through the magnet, magnet off, retract.

    sudo pigpiod
    python3 chain_rig.py home
    python3 chain_rig.py index 1                      # one module the way the machine runs
    python3 chain_rig.py repeat --moves 100 --modules 1 --speed 50 --accel 250
    python3 chain_rig.py lap                          # 13 modules, log every index edge
    python3 chain_rig.py endurance --moves 2000
    python3 chain_rig.py station --tilt 30            # dock, tilt, hold, back, undock (no auger)
    python3 chain_rig.py dose --tilt 30 --revs 2      # the full dose protocol, logs the load cell
    python3 chain_rig.py --sim dose --revs 1          # no hardware: simulated pins

Every move is appended to a CSV (default runs/<date>.csv).
"""
from __future__ import annotations

import argparse
import csv
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

PITCH_MM = 9.525
TEETH = 32
MODULE_PITCHES = 8
N_MODULES = 13
MM_PER_REV = TEETH * PITCH_MM                      # 304.8
RUN_DIRECTION = -1                                 # -1: bottom run toward -y

# station linkage (Sam's frame, mm; params.py / layout.actuator_pins)
YOKE_X, YOKE_Z, DOCK_RISE = 32.0, -34.0, 0.9      # carriage stub-pin axis, as drawn; docked it rises 0.9
UFORK_L, ACT_RETRACTED, ACT_STROKE = 60.0, 197.4, 150.0
DOCK_EXT = 20.0
GEAR_RATIO = 44 / 20                               # NEMA 11 turns per auger turn
NEMA11_USTEPS = 200 * 16                           # DRV8825 at 1/16

# BCM pin numbers (the interface board's screw terminals)
PIN_STEP, PIN_DIR, PIN_ENA = 17, 27, 22
PIN_INDEX, PIN_HOME, PIN_ALARM = 23, 24, 25
PIN_LAC = 18                                       # RC pulse to the LAC (hardware PWM pin)
PIN_AUG_STEP, PIN_AUG_DIR = 13, 21                 # DRV8825 for the NEMA 11 (STEP on a hardware-PWM pin for the docking seek)
PIN_TAP = 12                                       # DRV8871 IN1, tap solenoid
PIN_MAGNET = 16                                    # MOSFET gate, dock electromagnet
PIN_HX_DT, PIN_HX_SCK = 5, 6


def tilt_to_ext(tilt_deg: float) -> float:
    """P16 extension (mm from fully retracted) for a hinge angle: the stub-pin axis turns about the hinge, the base
    pin sits UFORK_L + ACT_RETRACTED + DOCK_EXT under the docked stub pins, and the rod end is UFORK_L short of them."""
    x0, z0 = YOKE_X, YOKE_Z + DOCK_RISE
    a = math.radians(tilt_deg)
    px, pz = x0 * math.cos(a) - z0 * math.sin(a), x0 * math.sin(a) + z0 * math.cos(a)
    bx, bz = x0, z0 - (ACT_RETRACTED + DOCK_EXT + UFORK_L)
    return math.hypot(px - bx, pz - bz) - UFORK_L - ACT_RETRACTED


@dataclass
class Rig:
    ppr: int = 4000                                 # CL86T DIP setting (pulses/rev)
    sim: bool = False
    pos: int = 0                                    # commanded steps since home, positive = the way the machine runs
    module: int = 0                                 # carriage at the station, 0-based
    edges: list = field(default_factory=list)
    ext: float = 0.0                                # actuator extension, mm

    def __post_init__(self):
        if self.sim:
            self.pi = None
            return
        import pigpio
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise SystemExit("pigpiod is not running (sudo pigpiod)")
        for p in (PIN_STEP, PIN_DIR, PIN_ENA, PIN_AUG_STEP, PIN_AUG_DIR, PIN_TAP, PIN_MAGNET):
            self.pi.set_mode(p, pigpio.OUTPUT)
            self.pi.write(p, 0)
        for p in (PIN_INDEX, PIN_HOME, PIN_ALARM):
            self.pi.set_mode(p, pigpio.INPUT)
            self.pi.set_pull_up_down(p, pigpio.PUD_UP)
        # the US5881 pulls low when a magnet's south pole is over it
        self.pi.callback(PIN_INDEX, pigpio.FALLING_EDGE, lambda g, l, t: self.edges.append(("index", self.pos, t)))
        self.pi.callback(PIN_HOME, pigpio.FALLING_EDGE, lambda g, l, t: self.edges.append(("home", self.pos, t)))
        self.actuator(0.0)

    # ---- units
    def steps_per_mm(self) -> float:
        return self.ppr / MM_PER_REV

    def module_steps(self, k: int) -> int:
        return round(k * self.ppr * MODULE_PITCHES / TEETH)

    # ---- chain
    def enable(self, on: bool = True):
        if self.pi:
            self.pi.write(PIN_ENA, 0 if on else 1)      # ENA+ high (opto on) disables the CL86T

    def move_steps(self, n: int, speed_mm_s: float = 50.0, accel_mm_s2: float = 250.0):
        """Trapezoidal move of n steps (sign: + = the way the machine runs) with pigpio waves."""
        if n == 0:
            return
        if self.ext > 0.5:
            raise SystemExit("refusing to move the chain: the station actuator is not retracted")
        if self.pi is None:
            self.pos += n
            self._sim_edges(self.pos - n, self.pos)
            return
        import pigpio
        forward = (n > 0) == (RUN_DIRECTION > 0)       # DIR high = bottom run toward +y
        self.pi.write(PIN_DIR, 1 if forward else 0)
        time.sleep(0.001)
        v = speed_mm_s * self.steps_per_mm()
        a = accel_mm_s2 * self.steps_per_mm()
        delays = _profile(abs(n), v, a)
        for i in range(0, len(delays), 2000):
            chunk = delays[i:i + 2000]
            self._wave(PIN_STEP, chunk)
            self.pos += int(math.copysign(len(chunk), n))

    def _wave(self, pin: int, delays: list[int]):
        import pigpio
        pulses = []
        for d in delays:
            pulses.append(pigpio.pulse(1 << pin, 0, 5))
            pulses.append(pigpio.pulse(0, 1 << pin, max(5, d - 5)))
        self.pi.wave_clear()
        self.pi.wave_add_generic(pulses)
        wid = self.pi.wave_create()
        self.pi.wave_send_once(wid)
        while self.pi.wave_tx_busy():
            time.sleep(0.002)
        self.pi.wave_delete(wid)

    def _sim_edges(self, a: int, b: int):
        lo, hi = sorted((a, b))
        for k in range(-N_MODULES, 3 * N_MODULES):
            s = self.module_steps(k)
            if lo < s <= hi:
                self.edges.append(("index", s, time.time()))
                if k % N_MODULES == 0:
                    self.edges.append(("home", s, time.time()))

    def go_module(self, k: int, **kw):
        self.move_steps(self.module_steps(k) - self.pos, **kw)
        self.module = k % N_MODULES

    def alarm(self) -> bool:
        return bool(self.pi and self.pi.read(PIN_ALARM) == 0)

    def home(self, speed_mm_s: float = 20.0):
        """Creep the way the machine runs until HOME fires (carriage 1's second magnet), then call that step count
        module 0."""
        self.edges.clear()
        limit = self.module_steps(N_MODULES + 1)
        moved = 0
        while moved < limit and not any(e[0] == "home" for e in self.edges):
            self.move_steps(self.module_steps(1) // 8, speed_mm_s, 200.0)
            moved += self.module_steps(1) // 8
        hits = [e for e in self.edges if e[0] == "home"]
        if not hits:
            raise SystemExit("HOME never fired: check the magnet on carriage 1 and the sensor wiring")
        self.pos -= hits[0][1]                       # the edge becomes step 0
        self.module = 0
        self.go_module(0)                            # back onto the edge
        self.edges.clear()

    # ---- station
    def actuator(self, ext_mm: float, wait: bool = True):
        ext = max(0.0, min(ACT_STROKE, ext_mm))
        if self.pi:
            self.pi.set_servo_pulsewidth(PIN_LAC, 1000 + 1000 * ext / ACT_STROKE)
        if wait:
            time.sleep(abs(ext - self.ext) / 30.0 + 0.3)     # about 30 mm/s loaded (46 no-load)
        self.ext = ext

    def magnet(self, on: bool):
        if self.pi:
            self.pi.write(PIN_MAGNET, 1 if on else 0)
        time.sleep(0.15 if on else 0.05)

    def dock(self, seek_rev_s: float = 0.25):
        """Lift to 3 mm short of the plate, then finish the last 3 mm while the pinion turns slowly so its teeth find
        the gear's gaps (held still, it parked the gear on its tips in 4 of 6 phases in the gear-mesh study); magnet on
        only once seated."""
        self.actuator(DOCK_EXT - 3.0)
        if self.pi:
            self.pi.write(PIN_AUG_DIR, 1)
            self.pi.hardware_PWM(PIN_AUG_STEP, int(seek_rev_s * NEMA11_USTEPS), 500000)
        self.actuator(DOCK_EXT + 1.2)                # 1.2 mm past the nominal dock takes up the carriage's sag
        if self.pi:
            self.pi.hardware_PWM(PIN_AUG_STEP, 0, 0)
        self.magnet(True)                            # pulls the carriage up onto the locating pins and the rim

    def tilt(self, deg: float):
        self.actuator(tilt_to_ext(deg) + 1.2)

    def undock(self):
        self.actuator(DOCK_EXT - 1.5)                # pull the plate back past the snap hooks through the magnet
        time.sleep(0.3)
        self.magnet(False)
        self.actuator(0.0)

    def auger_revs(self, revs: float, rpm: float = 30.0):
        """Turn the auger (positive = toward the outlet) through the 20T:44T pinion."""
        n = round(abs(revs) * GEAR_RATIO * NEMA11_USTEPS)
        if n == 0 or self.pi is None:
            time.sleep(abs(revs) / rpm * 60.0 if self.pi is None else 0)
            return
        self.pi.write(PIN_AUG_DIR, 1 if revs > 0 else 0)
        period = int(1e6 / (rpm / 60.0 * GEAR_RATIO * NEMA11_USTEPS))
        for i in range(0, n, 4000):
            self._wave(PIN_AUG_STEP, [period] * min(4000, n - i))

    def tap(self, n: int = 1, ms: int = 10, hz: float = 2.0):
        for _ in range(n):
            if self.pi:
                self.pi.write(PIN_TAP, 1)
            time.sleep(ms / 1000)
            if self.pi:
                self.pi.write(PIN_TAP, 0)
            time.sleep(max(0.0, 1.0 / hz - ms / 1000))

    def grams(self) -> float:
        """HX711 raw read, averaged (calibrate with a 20 g weight; TEST-PLAN.md T9)."""
        if self.pi is None:
            return 0.0
        vals = []
        for _ in range(10):
            while self.pi.read(PIN_HX_DT):
                time.sleep(0.001)
            v = 0
            for _ in range(24):
                self.pi.write(PIN_HX_SCK, 1)
                v = (v << 1) | self.pi.read(PIN_HX_DT)
                self.pi.write(PIN_HX_SCK, 0)
            self.pi.write(PIN_HX_SCK, 1)
            self.pi.write(PIN_HX_SCK, 0)
            vals.append(v - (1 << 24) if v & (1 << 23) else v)
        return sum(vals) / len(vals) / 420.0          # counts per gram: replace with the calibration


def _profile(n: int, v: float, a: float) -> list[int]:
    """Per-step periods (us) for a trapezoid: accelerate at a to v, cruise, decelerate."""
    out = []
    n_acc = min(int(v * v / (2 * a)), n // 2)
    for i in range(n):
        k = min(i, n - 1 - i)
        vi = v if k >= n_acc else math.sqrt(2 * a * (k + 1))
        out.append(int(1e6 / max(vi, 50.0)))
    return out


def log_row(path: Path, row: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim", action="store_true", help="no hardware")
    ap.add_argument("--ppr", type=int, default=4000)
    ap.add_argument("--log", type=Path, default=Path("runs") / time.strftime("%Y-%m-%d.csv"))
    ap.add_argument("--ask", action="store_true", help="prompt for a dial-indicator reading after each move")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("home")
    p = sub.add_parser("index")
    p.add_argument("modules", type=int)
    for name in ("repeat", "endurance"):
        p = sub.add_parser(name)
        p.add_argument("--moves", type=int, default=100 if name == "repeat" else 2000)
        p.add_argument("--modules", type=int, default=1)
        p.add_argument("--speed", type=float, default=50.0, help="mm/s")
        p.add_argument("--accel", type=float, default=250.0, help="mm/s^2")
        p.add_argument("--dwell", type=float, default=0.5, help="s between moves")
    sub.add_parser("lap")
    p = sub.add_parser("station")
    p.add_argument("--tilt", type=float, default=30.0, help="hinge angle, deg (frame = bench, the frame is not pitched)")
    p.add_argument("--hold", type=float, default=2.0)
    p = sub.add_parser("dose")
    p.add_argument("--tilt", type=float, default=30.0, help="dose tilt, deg; keep it at 45 or less with the 0.45 A current limit")
    p.add_argument("--revs", type=float, default=2.0, help="auger revolutions forward")
    p.add_argument("--rpm", type=float, default=30.0, help="auger rpm")
    p.add_argument("--taps", type=int, default=0, help="solenoid taps after the auger stops")
    p.add_argument("--hold", type=float, default=0.5, help="s at the dose tilt after the auger stops (the tail falls)")
    p.add_argument("--reverse-revs", type=float, default=1.0,
                   help="auger revolutions backwards after the return to level (never while tilted); 0 to skip")
    a = ap.parse_args()

    rig = Rig(ppr=a.ppr, sim=a.sim)
    rig.enable(True)
    run = time.strftime("%Y%m%dT%H%M%S")

    def record(cmd: str, k: int, t0: float, **extra):
        idx = [e[1] for e in rig.edges if e[0] == "index"]
        row = dict(run=run, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), cmd=cmd, module=k % N_MODULES,
                   target_steps=rig.module_steps(k), pos_steps=rig.pos, move_s=round(time.time() - t0, 3),
                   index_edge_steps=";".join(map(str, idx)), alarm=int(rig.alarm()),
                   dial_mm=input("dial reading (mm): ") if a.ask else "", **extra)
        log_row(a.log, row)
        rig.edges.clear()
        print(row)

    if a.cmd == "home":
        rig.home()
        print("homed; carriage 1 at the station")
    elif a.cmd == "index":
        t0 = time.time()
        rig.go_module(rig.module + a.modules)
        record("index", rig.module, t0)
    elif a.cmd in ("repeat", "endurance"):
        rig.home()
        for i in range(a.moves):
            k = a.modules if i % 2 == 0 else 0     # out and back: the station sees the same two carriages
            t0 = time.time()
            rig.go_module(k, speed_mm_s=a.speed, accel_mm_s2=a.accel)
            record(a.cmd, k, t0)
            if rig.alarm():
                raise SystemExit("driver alarm (position error): stopping")
            time.sleep(a.dwell)
    elif a.cmd == "lap":
        rig.home()
        for k in range(1, N_MODULES + 1):
            t0 = time.time()
            rig.go_module(k)
            record("lap", k, t0)
    elif a.cmd == "station":
        t0 = time.time()
        rig.dock()
        rig.tilt(a.tilt)
        time.sleep(a.hold)
        rig.tilt(0.0)
        rig.undock()
        record("station", rig.module, t0, tilt=a.tilt)
    elif a.cmd == "dose":
        t0 = time.time()
        g0 = rig.grams()
        rig.dock()
        rig.tilt(a.tilt)
        rig.auger_revs(a.revs, a.rpm)
        rig.tap(a.taps)
        time.sleep(a.hold)                          # tail into the vial before the tilt back
        rig.tilt(0.0)
        if a.reverse_revs:
            rig.auger_revs(-a.reverse_revs, a.rpm)  # at rest only: pulls powder back from the exit
        rig.undock()
        g1 = rig.grams()
        record("dose", rig.module, t0, tilt=a.tilt, revs=a.revs, rpm=a.rpm, taps=a.taps, reverse_revs=a.reverse_revs,
               dose_g=round(g1 - g0, 4))
    rig.enable(False)


if __name__ == "__main__":
    main()

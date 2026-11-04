#!/usr/bin/env python3
"""Drive and log the paternoster carousel from a Raspberry Pi (issue #128).

Hardware (BOM.md): CL86T closed-loop driver on step/dir/enable through a
74AHCT125; two US5881 hall switches under the station (INDEX sees the magnet
in every gondola's -y rail, HOME only gondola 1's second magnet); the
Actuonix P16-150-22-12-P on an Actuonix LAC board in RC mode (1.0-2.0 ms
pulses = 0-150 mm), with the pot fed back inside the LAC; an HX711 on the
100 g load cell under the vial; the dock electromagnet (Adafruit 3872) on a
logic-level MOSFET; the auger's NEMA 11 on the doser's Tic T500 (ticcmd over USB).

Station sequence (cad/gear-mesh/README.md, cad/auger-leakage/README.md):
  dock    approach in the fork, magnet ON for the last 3 mm, the pinion turning
          slowly (seek) until the LAC reaches the dock position: the gear finds a
          tooth space instead of parking on the pinion's tips
  tilt    to the dose angle (20-40 deg by default)
  dose    auger forward, stop, hold 0.5 s at the dose tilt (the tail of the dose
          falls into the vial), taps
  return  tilt back to 0, then reverse 1 auger revolution (2.2 NEMA 11 revs) at
          rest: takes 73 % of the powder off the exit's last 15 mm. Never reverse
          while tilted (it adds dose)
  undock  magnet OFF, lower
The Tic's current limit is set to 450 mA: a jam then stalls the motor (<= 0.067 N*m
at the pinion) before it can open the dock.

Geometry: one module = 10 pitches = 95.25 mm = 10/32 of a turn of the 32T drive
sprocket = 1250 steps at 4000 pulses/rev (direct drive, no ratio). Targets are
absolute step counts, so rounding never accumulates.

Motion profile (MuJoCo, sim/README.md): a trapezoid whose acceleration and
deceleration each last one pendulum period of a loaded gondola (2.54 Hz ->
0.394 s), 1.5 s per index. That cancels the swing the stop would excite, so the
station gondola settles in about 0.03 s; a plain S-curve is worse. Keep
continuous moves at or below 130 mm/s (a lap of 10 s or more).

    sudo pigpiod
    python3 paternoster_rig.py home
    python3 paternoster_rig.py index 1                 # one module forward
    python3 paternoster_rig.py repeat --moves 100       # index repeatability (dial indicator at the station)
    python3 paternoster_rig.py station --tilt 30        # dock, tilt, hold, back down
    python3 paternoster_rig.py dose --tilt 30 --revs 2  # dock, tilt, turn the auger, log the load cell
    python3 paternoster_rig.py --sim repeat --moves 5   # no hardware

Every command appends to runs/<date>.csv.
"""
from __future__ import annotations

import argparse
import csv
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

PITCH_MM, TEETH, MODULE_PITCHES, N_MODULES = 9.525, 32, 10, 12
MM_PER_REV = TEETH * PITCH_MM
PENDULUM_HZ = 2.54                   # loaded gondola, from the MuJoCo model
INDEX_S = 1.5                        # seconds per index
ACT_STROKE = 150.0
DOCK_MM, MAX_TILT_MM = 20.0, 85.1    # actuator extension at docking and at 90 deg (layout.actuator_pose)
SEEK_MM = 3.0                        # last part of the approach: magnet on, pinion seeking
AUGER_RATIO = 44 / 20                # NEMA 11 revs per auger rev
TIC_STEPS_PER_REV = 200 * 8          # Tic T500 at 1/8 step
TIC_CURRENT_MA = 450                 # stall at or below 0.067 N*m at the pinion

PIN_STEP, PIN_DIR, PIN_ENA = 17, 27, 22
PIN_INDEX, PIN_HOME, PIN_ALARM = 23, 24, 25
PIN_LAC = 18                          # RC pulse to the LAC (hardware PWM pin)
PIN_HX_DT, PIN_HX_SCK = 5, 6
PIN_TAP = 12                          # DRV8871 IN1 for the tap solenoid
PIN_MAG = 16                          # MOSFET gate for the dock electromagnet


def tilt_to_ext(tilt_deg: float) -> float:
    """Actuator extension (mm) for a module tilt, from the station linkage in layout.py: the carriage's stub pins
    32 mm behind and 33.1 mm below the hinge when docked; the P16 (197.4 mm retracted) plus the 60 mm U-yoke is one
    two-force link from its base pin, 277.4 mm under the docked pins."""
    a = math.radians(tilt_deg)
    px, pz = 32 * math.cos(a) + 33.1 * math.sin(a), 32 * math.sin(a) - 33.1 * math.cos(a)
    return math.hypot(px - 32.0, pz + 310.5) - 257.4


def trapezoid(n_steps: int, t_total: float = INDEX_S, t_acc: float = 1 / PENDULUM_HZ) -> list[float]:
    """Step times (s) for a trapezoidal move whose ramps each last t_acc."""
    v = n_steps / (t_total - t_acc)
    a = v / t_acc
    out = []
    for k in range(1, n_steps + 1):
        s = k
        s_acc = 0.5 * a * t_acc ** 2
        if s <= s_acc:
            t = math.sqrt(2 * s / a)
        elif s <= n_steps - s_acc:
            t = t_acc + (s - s_acc) / v
        else:
            t = t_total - math.sqrt(2 * (n_steps - s) / a)
        out.append(t)
    return out


@dataclass
class Rig:
    ppr: int = 4000
    sim: bool = False
    pos: int = 0
    edges: list = field(default_factory=list)

    def __post_init__(self):
        if self.sim:
            self.pi = None
            return
        import pigpio
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise SystemExit("pigpiod is not running (sudo pigpiod)")
        for p in (PIN_STEP, PIN_DIR, PIN_ENA, PIN_TAP, PIN_HX_SCK, PIN_MAG):
            self.pi.set_mode(p, pigpio.OUTPUT)
            self.pi.write(p, 0)
        for p in (PIN_INDEX, PIN_HOME, PIN_ALARM, PIN_HX_DT):
            self.pi.set_mode(p, pigpio.INPUT)
            self.pi.set_pull_up_down(p, pigpio.PUD_UP)
        self.pi.callback(PIN_INDEX, pigpio.FALLING_EDGE, lambda g, l, t: self.edges.append(("index", self.pos, t)))
        self.pi.callback(PIN_HOME, pigpio.FALLING_EDGE, lambda g, l, t: self.edges.append(("home", self.pos, t)))

    def module_steps(self, k: int) -> int:
        return round(k * self.ppr * MODULE_PITCHES / TEETH)

    # ---- chain
    def move_steps(self, n: int, t_total: float = INDEX_S) -> None:
        if n == 0:
            return
        times = trapezoid(abs(n), t_total * max(1.0, abs(n) / self.module_steps(1)) ** 0.5)
        if self.sim:
            time.sleep(min(times[-1], 0.05))
            self.pos += n
            return
        import pigpio
        self.pi.write(PIN_DIR, 1 if n > 0 else 0)
        pulses, last = [], 0.0
        for t in times:
            dt = max(int((t - last) * 1e6), 20)
            pulses += [pigpio.pulse(1 << PIN_STEP, 0, 10), pigpio.pulse(0, 1 << PIN_STEP, dt - 10)]
            last = t
        for i in range(0, len(pulses), 4000):     # wave chunks
            self.pi.wave_add_generic(pulses[i:i + 4000])
            w = self.pi.wave_create()
            self.pi.wave_send_once(w)
            while self.pi.wave_tx_busy():
                time.sleep(0.002)
            self.pi.wave_delete(w)
        self.pos += n

    def index(self, k: int = 1) -> None:
        target = self.module_steps(round(self.pos / self.module_steps(1)) + k)
        self.move_steps(target - self.pos)

    def home(self) -> None:
        """Creep forward until HOME falls, then back to the station target."""
        self.edges.clear()
        for _ in range(N_MODULES * 2 + 2):
            self.move_steps(self.module_steps(1) // 2, 1.2)
            if any(e[0] == "home" for e in self.edges):
                break
        self.pos = 0

    # ---- station
    def actuator(self, ext_mm: float, wait: bool = True) -> None:
        ext = min(max(ext_mm, 0.0), ACT_STROKE)
        if not self.sim:
            self.pi.set_servo_pulsewidth(PIN_LAC, 1000 + 1000 * ext / ACT_STROKE)
        if wait:
            time.sleep(0.2 + ext_mm / 35.0 if not self.sim else 0.01)   # ~35 mm/s under load

    def magnet(self, on: bool) -> None:
        if not self.sim:
            self.pi.write(PIN_MAG, 1 if on else 0)

    def tic(self, *args: str) -> None:
        """The doser's Tic T500 (ticcmd): the auger's NEMA 11."""
        if self.sim:
            return
        import subprocess
        subprocess.run(["ticcmd", *args], check=True)

    def auger_revs(self, revs: float, rps: float = 1.0) -> None:
        """Turn the auger (positive = dosing direction) at rps auger revolutions per second, and wait."""
        steps = int(round(revs * AUGER_RATIO * TIC_STEPS_PER_REV))
        self.tic("--exit-safe-start", "--max-speed", str(int(rps * AUGER_RATIO * TIC_STEPS_PER_REV * 10000)),
                 "--position-relative", str(steps))
        time.sleep(abs(revs) / rps + 0.2 if not self.sim else 0.01)

    def dock(self) -> None:
        """Approach in the fork; magnet on and the pinion seeking (0.25 rev/s) for the last SEEK_MM."""
        self.tic("--current", str(TIC_CURRENT_MA))
        self.actuator(DOCK_MM - SEEK_MM)
        self.magnet(True)
        self.tic("--exit-safe-start", "--velocity", str(int(0.25 * TIC_STEPS_PER_REV * 10000)))
        self.actuator(DOCK_MM)
        time.sleep(0.4 if not self.sim else 0.0)
        self.tic("--velocity", "0")

    def tilt(self, deg: float) -> None:
        self.dock()
        self.actuator(tilt_to_ext(deg))

    def lower(self, reverse_revs: float = 1.0) -> None:
        """Back to 0 deg, reverse the auger at rest, release the magnet, lower."""
        self.actuator(DOCK_MM)
        if reverse_revs:
            self.auger_revs(-reverse_revs, rps=0.5)
        self.magnet(False)
        self.actuator(0.0)

    def tap(self, n: int = 1, ms: int = 10, hz: float = 2.0) -> None:
        for _ in range(n):
            if not self.sim:
                self.pi.write(PIN_TAP, 1)
                time.sleep(ms / 1000)
                self.pi.write(PIN_TAP, 0)
            time.sleep(1 / hz)

    def grams(self) -> float:
        """HX711 raw read (calibrate with a 20 g weight; see TEST-PLAN.md T7)."""
        if self.sim:
            return 0.0
        while self.pi.read(PIN_HX_DT):
            time.sleep(0.001)
        v = 0
        for _ in range(24):
            self.pi.write(PIN_HX_SCK, 1)
            v = (v << 1) | self.pi.read(PIN_HX_DT)
            self.pi.write(PIN_HX_SCK, 0)
        self.pi.write(PIN_HX_SCK, 1)
        self.pi.write(PIN_HX_SCK, 0)
        return (v - (1 << 24) if v & (1 << 23) else v) * 1e-4


def log(row: dict) -> None:
    out = Path("runs")
    out.mkdir(exist_ok=True)
    f = out / f"{time.strftime('%Y-%m-%d')}.csv"
    new = not f.exists()
    with f.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("home")
    p = sub.add_parser("index")
    p.add_argument("k", type=int, nargs="?", default=1)
    p = sub.add_parser("repeat")
    p.add_argument("--moves", type=int, default=20)
    p = sub.add_parser("station")
    p.add_argument("--tilt", type=float, default=30.0)
    p.add_argument("--hold", type=float, default=3.0)
    p = sub.add_parser("dose")
    p.add_argument("--tilt", type=float, default=30.0)
    p.add_argument("--revs", type=float, default=2.0)
    p.add_argument("--rps", type=float, default=1.0, help="auger revolutions per second")
    p.add_argument("--reverse-revs", type=float, default=1.0, help="auger revolutions reversed at rest after the dose")
    a = ap.parse_args()
    rig = Rig(sim=a.sim)
    t0 = time.time()
    if a.cmd == "home":
        rig.home()
    elif a.cmd == "index":
        rig.index(a.k)
    elif a.cmd == "repeat":
        for m in range(a.moves):
            rig.index(1)
            time.sleep(0.5)
            log({"t": round(time.time() - t0, 3), "cmd": "repeat", "move": m, "pos": rig.pos,
                 "index_edges": sum(1 for e in rig.edges if e[0] == "index")})
    elif a.cmd == "station":
        rig.tilt(a.tilt)
        time.sleep(a.hold)
        rig.lower()
    elif a.cmd == "dose":
        rig.tilt(a.tilt)
        g0 = rig.grams()
        rig.auger_revs(a.revs, a.rps)
        time.sleep(0.5)                           # hold at the dose tilt: the tail of the dose falls into the vial
        rig.tap(4)
        log({"t": round(time.time() - t0, 3), "cmd": "dose", "tilt": a.tilt, "revs": a.revs, "grams": round(rig.grams() - g0, 4)})
        rig.lower(reverse_revs=a.reverse_revs)
    log({"t": round(time.time() - t0, 3), "cmd": a.cmd, "pos": rig.pos, "edges": len(rig.edges)})


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Drive and log the chain-carousel test rig from a Raspberry Pi (issue #128).

Hardware (BOM.md items 9, 33-36): CL86T closed-loop driver on step/dir/
enable through a 74AHCT125 (3.3 V GPIO in, 5 V out to PUL+/DIR+/ENA+, the
minus terminals to ground), two US5881 hall switches under the deck at the
station (open drain, 10k pull-ups to 3.3 V): INDEX sees the magnet every
carriage carries, HOME only carriage 1's second magnet.

Geometry: one module = 8 pitches = 76.2 mm = 8/19 of a turn of the 19T drive
sprocket. Targets are absolute step counts, round(k * PPR * 8 / 19), so the
non-integer steps per module never accumulate (error <= half a step,
0.02 mm at 4000 pulses/rev).

    sudo pigpiod
    python3 chain_rig.py home
    python3 chain_rig.py index 1                      # one module forward
    python3 chain_rig.py repeat --moves 100 --modules 1 --speed 50 --accel 250
    python3 chain_rig.py lap                          # 12 modules, log every index edge
    python3 chain_rig.py endurance --moves 2000
    python3 chain_rig.py --sim repeat --moves 5       # no hardware: simulated pins

Every move is appended to a CSV (default runs/<date>.csv): time, command,
target and commanded steps, the step count at each INDEX/HOME edge, the
operator's dial-indicator reading if --ask is given, and the driver alarm.
"""
from __future__ import annotations

import argparse
import csv
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

PITCH_MM = 9.525
TEETH = 19
MODULE_PITCHES = 8
N_MODULES = 12
MM_PER_REV = TEETH * PITCH_MM                      # 180.975

# BCM pin numbers (the interface board's screw terminals)
PIN_STEP, PIN_DIR, PIN_ENA = 17, 27, 22
PIN_INDEX, PIN_HOME, PIN_ALARM = 23, 24, 25


@dataclass
class Rig:
    ppr: int = 4000                                 # CL86T DIP setting (pulses/rev)
    sim: bool = False
    pos: int = 0                                    # commanded steps since home
    module: int = 0                                 # carriage at the station, 0-based
    edges: list = field(default_factory=list)

    def __post_init__(self):
        if self.sim:
            self.pi = None
            return
        import pigpio
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise SystemExit("pigpiod is not running (sudo pigpiod)")
        for p in (PIN_STEP, PIN_DIR, PIN_ENA):
            self.pi.set_mode(p, pigpio.OUTPUT)
            self.pi.write(p, 0)
        for p in (PIN_INDEX, PIN_HOME, PIN_ALARM):
            self.pi.set_mode(p, pigpio.INPUT)
            self.pi.set_pull_up_down(p, pigpio.PUD_UP)
        # the US5881 pulls low when a magnet's south pole is over it
        self.pi.callback(PIN_INDEX, pigpio.FALLING_EDGE, lambda g, l, t: self.edges.append(("index", self.pos, t)))
        self.pi.callback(PIN_HOME, pigpio.FALLING_EDGE, lambda g, l, t: self.edges.append(("home", self.pos, t)))

    # ---- units
    def steps_per_mm(self) -> float:
        return self.ppr / MM_PER_REV

    def module_steps(self, k: int) -> int:
        return round(k * self.ppr * MODULE_PITCHES / TEETH)

    # ---- motion
    def enable(self, on: bool = True):
        if self.pi:
            self.pi.write(PIN_ENA, 0 if on else 1)      # ENA+ high (opto on) disables the CL86T

    def move_steps(self, n: int, speed_mm_s: float = 50.0, accel_mm_s2: float = 250.0):
        """Trapezoidal move of n steps (sign = direction) with pigpio waves."""
        if n == 0:
            return
        if self.pi is None:
            self.pos += n
            self._sim_edges(self.pos - n, self.pos)
            return
        import pigpio
        self.pi.write(PIN_DIR, 1 if n > 0 else 0)
        time.sleep(0.001)
        v = speed_mm_s * self.steps_per_mm()
        a = accel_mm_s2 * self.steps_per_mm()
        delays = _profile(abs(n), v, a)
        # chain the profile into waves of <= 2000 pulses
        for i in range(0, len(delays), 2000):
            chunk = delays[i:i + 2000]
            pulses = []
            for d in chunk:
                pulses.append(pigpio.pulse(1 << PIN_STEP, 0, 5))
                pulses.append(pigpio.pulse(0, 1 << PIN_STEP, max(5, d - 5)))
            self.pi.wave_clear()
            self.pi.wave_add_generic(pulses)
            wid = self.pi.wave_create()
            self.pi.wave_send_once(wid)
            while self.pi.wave_tx_busy():
                time.sleep(0.002)
            self.pi.wave_delete(wid)
            self.pos += int(math.copysign(len(chunk), n))

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
        """Creep forward until HOME fires (carriage 1's second magnet), then
        call that step count module 0."""
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
    a = ap.parse_args()

    rig = Rig(ppr=a.ppr, sim=a.sim)
    rig.enable(True)
    run = time.strftime("%Y%m%dT%H%M%S")

    def record(cmd: str, k: int, t0: float):
        idx = [e[1] for e in rig.edges if e[0] == "index"]
        row = dict(run=run, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), cmd=cmd, module=k % N_MODULES,
                   target_steps=rig.module_steps(k), pos_steps=rig.pos, move_s=round(time.time() - t0, 3),
                   index_edge_steps=";".join(map(str, idx)), alarm=int(rig.alarm()),
                   dial_mm=input("dial reading (mm): ") if a.ask else "")
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
    rig.enable(False)


if __name__ == "__main__":
    main()

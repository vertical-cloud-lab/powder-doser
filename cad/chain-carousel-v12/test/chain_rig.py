#!/usr/bin/env python3
"""Drive and log the chain-carousel test rig v12 from a Raspberry Pi (issue #128). v12 (Sterling, PR #185, 2026-11-27) is v11 with the
spring-loaded pinion: the NEMA 11 and its 24T pinion ride on a printed cradle that pivots in the EC, a 1 N/mm spring presses the
pinion into the auger's gear (6 N at the set-screw stop, 0.4 mm past tight mesh), and a US5881 hall switch on the cradle
(PIN_HALL_CRADLE, low = lifted) tells the driver when the pinion is resting on the gear's tips instead of in mesh. After every index
the driver runs the seek (Rig.seek_mesh): the pinion turned SEEK_REV_S forward for SEEK_T and back for SEEK_T, so the auger ends where
it started; if the switch still reads "lifted", a second try the other way round; if it still does, it stops and says so (TEST-PLAN
T6a). In the v12 model (sim/README.md) every stub cleared on the first seek and nothing jammed. The rest is v11's:

Drive and log the chain-carousel test rig v11 from a Raspberry Pi (issue #128). v11 (Sam's notes of 2026-11-25, PR #185) is v10 with
0-90 deg: the carriages 40 mm longer, a P16-150 (back from v10's P16-100) whose base is outside the front side plate on a bar across
the front posts, through a slot in the plate; a straight rail (no lift: the module sits at 0 deg, its 44T gear meeting a 24T pinion
at rest, so GEAR_RATIO is 44/24); the EC opens each door itself; the solenoid taps over clip 1; the tall-cage balance on the bench,
the beaker on a pillar 33 mm under the exit. The P16's table below is v11's (layout.p16_11_ext). The rest of this docstring is v10's,
with the v11 changes noted where they matter.

v10 (Sam's note of 2026-11-19, PR #185) is
v9 (the balance on a granite block with no draft cage, the bay window and the weighing chamber) with the station turned upside
down: the electronics carriage (EC) is inside the loop on the plate's side of the module, a keyed rail replaces the kinematic
dock, and one P16-100, fully extended between doses, retracts to pull the module up to dose. Nothing of the station is under the
auger, so the beaker's rim is 18 mm under the exit. The P16's table below is v10's (layout.p16_10_ext).

Hardware (see BOM.md):
* CL86T closed-loop driver for the NEMA 34 on step/dir/enable through a 74AHCT125 (3.3 V GPIO in, 5 V out to
  PUL+/DIR+/ENA+, the minus terminals to ground).
* Two US5881 hall switches in the station hold-downs (open drain, 10k pull-ups to 3.3 V): INDEX, in the front
  hold-down, sees the magnet in every carriage's front tongue; HOME, in the back hold-down, only carriage 1's.
* Station (v10): ONE Actuonix P16-100-22-12-P on ONE LAC board (PIN_LAC, RC mode: 1.0-2.0 ms = 0-100 mm; the pot is fed back
  inside the LAC), inside the loop beside the module's path: its base pin on a printed bracket on the front side plate, its rod
  end on the EC's arm. It is FULLY EXTENDED between doses (P16_HOME_EXT, 99.4 mm: the module at 4 deg and the EC's guide shoe in
  its funnel seat on the station beam, so the EC can't swing between modules) and RETRACTS to tilt: it pulls the EC, and the
  module coupled to it, up about the hinge, 4-65 deg (P16_TABLE: 56.7 mm out at 30 deg, 11.3 at 65). There is no dock, no lift,
  no park and no magnets: every index slides the next module's T-bracket into the T-slot under the EC, whose ramps lift the
  module 4 deg about its hinge (coupled, TILT_MIN), so its 44T gear meshes with the EC's 20T pinion; the exit ramp sets it back
  on its carriage. A second ramp on the EC lifts the outlet door's cable tab, so the door is open while the module is in the
  rail: nothing to drive.
* Station (v7-v9): ONE Actuonix P16-150-22-12-P under the station (RC 1.0-2.0 ms = 0-150 mm), on a clevis on a cross bar behind
  the balance (leaning 44.5 deg) and a 2 mm lost-motion slot in the EC's tail. Parked (1.0 mm out) the EC's tail shoes sat on its
  guides' cone and vee; extending lifted the EC 10 mm up the guides onto a kinematic dock on the module (8.25 mm out: the plate's
  domes in the EC's cone and vee, the NEMA 11 seeking at 0.25 rev/s over the last 3 mm so the pinion found the gear's gaps,
  magnets holding the dock), and extending further tilted the docked EC and module 0-90 deg about the hinge (129.7 mm at 90).
  Retracting tilted them back level and parked the EC on its seats. v7 (Sam, 2026-11-10): v6's frame and plate, one P16 under
  the station; v9 (Sam, 2026-11-17): v7's station unchanged, the balance's draft cage off, the balance on a granite block with
  the beaker 32 mm under the exit, and the EC cut back where it hung over the beaker. The paragraphs below are v6's and v5's,
  kept for the history.
* Station (v6): the LIFT is two Actuonix P16-50-22-12-P (one each side of the balance on the lower rungs, LACs on PIN_LAC and
  PIN_LAC_B, always the same target, 1.0-2.0 ms = 0-50 mm) carrying a frame of two 8 mm bars; the EC hangs on the bars in two
  hooks. They only dock it (DOCK_EXT); the shoes park on the guides' cone and vee. The TILT is a third P16-150-22-12-P on the
  back side plate (its LAC on PIN_LAC_T, 0-150 mm) pinned to the EC's tilt arm: retracting turns the docked EC and module
  0-90 deg about the hinge (tilt_to_tilt_ext). The rest of this paragraph is v5's, kept for the history.
* Station (v5): two Actuonix P16-150-22-12-P, one each side of the balance, each on its own Actuonix LAC board in RC mode
  (1.0-2.0 ms pulses = 0-150 mm; the pot is fed back inside each LAC) and always sent the same target. Their rod ends lift
  an 8 mm bar through 2 mm slots in its end blocks; the electronics carriage (EC v5 = EC v4 on saddles) is clamped to the
  bar, and the end blocks' shoes run in vertical guides until the EC seats. Parked, the EC hangs on the bar 28 mm below
  its dock (clear of the passing augers) and 12 mm over the balance's top; docked, its two arms
  reach round the auger and the plate's two balls sit in the EC's cone and vee and the EC's third ball on the plate's
  steel washer (a Kelvin clamp), held by the module's own weight (it rests on the EC) and an N52 magnet behind each
  contact. There is no dock electromagnet in v4. The last 6 mm of the dock open the module's outlet door; the
  station's rail opens the carriage's plate latch whenever it is at the station, and the module rests on the tube
  rest until the EC lifts it off.
* On the electronics carriage: the doser's NEMA 11 (20T steel pinion -> the auger's 44T gear, 2.2:1) on a DRV8825
  whose current limit is set to AUGER_CURRENT_MA = 450 mA (Vref 0.225 V on Pololu's carrier; set it with the pot
  before the first dose, the Pi can't): 0.067 N*m stall at the pinion, 0.15 N*m at the auger, so a jam stalls the
  motor (v4-v9: before the mesh could open the dock, gear-mesh study; v10: the rail's lips take the mesh's separating force,
  TEST-PLAN T6d). v10: the DRV8825's EN pin is on PIN_AUG_ENA, so the motor can be left free while the chain indexes (below).
  The 12 V tap solenoid on a DRV8871 (v10: on the EC over clip 2, tapping the plate).
* The scale (v5): an A&D HR-202i (220 g x 0.1 mg) under the dose point, on RS-232 through a MAX3232 (Pi UART, A&D's
  standard format and "Q" command, set to 2400 baud 7E1 in its function table; check against README "The balance"). The
  lab's HR-100A speaks the same protocol and fits in the same place. v9/v10: its draft cage is off and it stands on a granite
  block in the weighing chamber; v10: the beaker sits on the pan under the front deck's 16 mm dose hole, its rim 18 mm under the
  exit, and goes in and out through the bay window's door. (v7: a dosing lid with a 30 mm hole replaced the top door; v5/v6: the
  top door was slid back by hand before a dose.)

Geometry: one module = 8 pitches = 76.2 mm = 8/32 of a turn of the 32T drive sprocket, so at 4000 pulses/rev a
module is exactly 1000 steps. Targets are absolute step counts, so rounding never accumulates.

Run direction: the bottom run travels toward -y (RUN_DIRECTION = -1, clockwise seen from the back). Every lap turns
each module once about its own axis, which acts like an auger turn; this way it pulls powder back from the outlet,
the other way it pumps about one revolution's dose out (../auger-leakage/README.md). A positive index here always
means "the way the machine runs".

Indexing (v10): every chain move slides one module's T-bracket out of the EC's rail and the next one's in; over its last 10 mm
or so the arriving 44T gear slides into mesh with the pinion from the side. A held pinion would make the gear roll round it and
turn the auger about 50 deg per pass, so the NEMA 11's DRV8825 is disabled (PIN_AUG_ENA high: the motor free, so the pinion
turns out of the way) before the NEMA 34 moves and enabled again after (Rig.nema11). With --seek it instead steps the pinion
slowly through the move (SEEK_REV_S, 0.25 rev/s, either direction with --seek-rev-s), as v4-v9's docking seek did over the
dock's last 3 mm; TEST-PLAN T6a compares the two. The chain only moves with the P16 fully extended.

Dose protocol (auger-leakage study; v10): with the module coupled at 4 deg after an index, retract the P16 to the dose tilt
(30 deg by default), turn the auger (and tap), stop, hold 0.5 s at the dose tilt (the tail falls into the beaker), extend the
P16 fully (back to 4 deg; the EC's shoe re-seats), then reverse the auger 1 revolution at rest (--reverse-revs, auger
revolutions; 2.2 NEMA 11 revolutions each). Never reverse at the dose tilt: it adds dose. There is no undock or park: the next
index takes the module out of the rail, its exit ramp sets the module back on its carriage, the door's spring shuts it and the
latch closes behind it. (v4-v9: dock, tilt, dose, hold, tilt back to level, reverse, undock.)

The P16 is rated 20 % duty: a full 4-70-4 deg cycle moves its rod 2 x 91.7 = 183 mm, 4.0 s at 46 mm/s, so leave about 16 s
before the next (station --cycles does: p16_rest_s); a 4-30-4 dose cycle moves 85 mm, under 2 s.

    sudo pigpiod
    python3 chain_rig.py home
    python3 chain_rig.py index 1                      # one module the way the machine runs (the NEMA 11 free while it moves)
    python3 chain_rig.py --seek index 1               # v10: the pinion seeking at 0.25 rev/s instead (T6a)
    python3 chain_rig.py repeat --moves 100 --modules 1 --speed 50 --accel 250
    python3 chain_rig.py lap                          # 13 modules, log every index edge
    python3 chain_rig.py endurance --moves 2000
    python3 chain_rig.py station --tilt 30            # 4 deg (coupled) up to 30, hold, back to 4 (no auger); v10: --tilt 4-65
    python3 chain_rig.py station --tilt 70 --cycles 50   # T6c: 50 cycles, resting between them for the P16's duty cycle
    python3 chain_rig.py dose --tilt 30 --revs 2      # the full dose protocol, logs the balance
    python3 chain_rig.py dose-to 0.050 --tilt 30      # v5: dose by weight (T8)
    python3 chain_rig.py --sim dose --revs 1          # no hardware: simulated pins, prints each step

Every move is appended to a CSV (default runs/<date>.csv). v10: chain moves also log the NEMA 11's mode (free, or seek and its
rev/s) and, with --ask-rail, what the rail did (clean, clash or jam; TEST-PLAN T6a).
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

# station linkage (v10: params.P16_10_PIN, P16_10_YW, P16_10_BX, TAU0; layout.P16_10_B, layout.p16_10_ext): the rod-end pin on
# the EC's arm (Sam x 90, z -30), the base pin on a bracket on the front side plate at world x -18, y -34 (its z set so the P16
# is fully extended at 4 deg)
ACT_RETRACTED, ACT_STROKE = 197.4, 150.0           # v11: P16-150: hole to hole fully retracted, and its stroke (v10's P16-100: 147.4, 100)
TILT_MIN = 0.0                                     # v11: no lift, the module rests at 0 deg between doses (v10: 4, the rail's ramps)
TILT_MAX = 90.0                                    # v11: the clash check is clear at 0-90 deg (v10: 4-65)
# v10: the P16's extension (mm from fully retracted) for a tilt, the module coupled, from layout.p16_10_ext. Fully extended
# between doses (99.40 at 4 deg, 0.6 mm short of its own stop), it retracts to tilt. The curve bends past 40 deg: linear
# interpolation between these points is within 0.15 mm of it to 40 deg and 0.5 mm (0.6 deg) at 65 (a pin turning about the
# hinge, fitted to these points).
P16_TABLE = ((0, 139.22), (10, 123.47), (15, 115.22), (20, 106.79), (30, 89.60), (40, 72.35), (50, 55.61), (60, 40.05), (70, 26.44), (80, 15.61),
             (90, 8.33))                           # v11: layout.p16_11_ext (base pin outside the front plate at x -62, z 612, y -31; rod-end pin Sam (96, -25))
P16_HOME_EXT = P16_TABLE[0][1]                     # v11: 139.22 mm, 10.8 short of full extension, between doses (module at 0 deg, shoe in its seat)
P16_MM_S, P16_DUTY = 46.0, 0.20                    # the P16's speed (no load) and rated duty cycle (p16_rest_s)
GEAR_RATIO = 44 / 24                               # NEMA 11 turns per auger turn (v11: a 24T pinion; v2-v10: 20T)
NEMA11_USTEPS = 200 * 16                           # DRV8825 at 1/16
AUGER_CURRENT_MA = 450                             # DRV8825 current limit (Vref = mA / 2000 V on Pololu's carrier)
SEEK_REV_S = -0.25                                 # v10 --seek: the pinion's rev/s while the chain moves (Rig.nema11)
SEEK12_REV_S, SEEK12_T, SEEK12_TRIES = 0.25, 0.2, 2   # v12: the seek after every index: rev/s, s each way, tries (params.SEEK12)
REINDEX12_MM = 3.0                                 # v12: if the switch still reads lifted after both seeks, back the chain off this far and
                                                   # come back (the NEMA 11 free), then seek once more (sim/README: dry teeth)
DOSE_HOLD_S = 0.5                                  # at the dose tilt after the auger stops (the tail falls)
REVERSE_REVS = 1.0                                 # auger revolutions backwards at rest, after the P16 is back fully extended

# BCM pin numbers (the interface board's screw terminals)
PIN_STEP, PIN_DIR, PIN_ENA = 17, 27, 22
PIN_INDEX, PIN_HOME, PIN_ALARM = 23, 24, 25
PIN_LAC = 18                                       # v7-v10: RC pulse to the one P16's LAC (v5/v6 also used 26 and 16 for their other LACs)
PIN_AUG_STEP, PIN_AUG_DIR = 13, 21                 # DRV8825 for the NEMA 11 (STEP on a hardware-PWM pin for the seek)
PIN_AUG_ENA = 20                                   # v10: DRV8825 EN, high = outputs off (the NEMA 11 free); header pin 38, beside DIR's 40
PIN_HALL_CRADLE = 26                               # v12: the cradle's US5881 (open drain, 10k pull-up to 3.3 V): low = lifted; header pin 37
PIN_TAP = 12                                       # DRV8871 IN1, tap solenoid
PIN_HX_DT, PIN_HX_SCK = 5, 6


def _interp(table, x: float) -> float:
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    raise ValueError(x)


def tilt_to_ext(tilt_deg: float) -> float:
    """v10: the P16's extension (mm from fully retracted) for a hinge angle, the module coupled: P16_TABLE, interpolated.
    4 deg (coupled, between doses): 99.4, fully extended; 30: 56.7; 50: 27.3; 70: 7.7."""
    if not TILT_MIN <= tilt_deg <= TILT_MAX:
        raise SystemExit(f"v10 tilts {TILT_MIN:g}-{TILT_MAX:g} deg ({TILT_MIN:g}: coupled, between doses)")
    return _interp(P16_TABLE, tilt_deg)


def p16_rest_s(tilt_deg: float) -> float:
    """v10: the rest after a TILT_MIN -> tilt_deg -> TILT_MIN cycle that keeps the P16 within its rated duty: the rod's travel
    at P16_MM_S, times (1 - P16_DUTY) / P16_DUTY. 4-70-4: 183 mm, 4.0 s moving, 16 s rest; 4-30-4: 85 mm, 1.9 s, 7.4 s."""
    moving_s = 2 * (P16_HOME_EXT - tilt_to_ext(tilt_deg)) / P16_MM_S
    return moving_s * (1 - P16_DUTY) / P16_DUTY


@dataclass
class Rig:
    ppr: int = 4000                                 # CL86T DIP setting (pulses/rev)
    sim: bool = False
    seek_rev_s: float = 0.0                         # v10: 0 = the NEMA 11 free while the chain moves; else it seeks at this rev/s
    pos: int = 0                                    # commanded steps since home, positive = the way the machine runs
    module: int = 0                                 # carriage at the station, 0-based
    edges: list = field(default_factory=list)
    ext: float = 0.0                                # actuator extension, mm
    n11_mode: str = "held"                          # v10: the NEMA 11's DRV8825: "held", "free" or "seek" (nema11())
    sim_stub: int = 0                               # v12 --sim: how many seeks the simulated pinion needs before it drops into mesh
    last_seek: dict = field(default_factory=dict)   # v12: what the last seek_mesh() did (logged)

    def __post_init__(self):
        if self.sim:
            self.pi = None
            self.ext = P16_HOME_EXT                     # v10: fully extended, as the hardware starts below
            self.say(f"start: P16 fully extended ({P16_HOME_EXT:.2f} mm), the module at the station coupled at {TILT_MIN:g} deg; "
                     "NEMA 11 held")
            return
        import pigpio
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise SystemExit("pigpiod is not running (sudo pigpiod)")
        for p in (PIN_STEP, PIN_DIR, PIN_ENA, PIN_AUG_STEP, PIN_AUG_DIR, PIN_AUG_ENA, PIN_TAP):
            self.pi.set_mode(p, pigpio.OUTPUT)
            self.pi.write(p, 0)                         # v10: PIN_AUG_ENA low enables the DRV8825: the NEMA 11 held
        for p in (PIN_INDEX, PIN_HOME, PIN_ALARM, PIN_HALL_CRADLE):
            self.pi.set_mode(p, pigpio.INPUT)
            self.pi.set_pull_up_down(p, pigpio.PUD_UP)
        # the US5881 pulls low when a magnet's south pole is over it
        self.pi.callback(PIN_INDEX, pigpio.FALLING_EDGE, lambda g, l, t: self.edges.append(("index", self.pos, t)))
        self.pi.callback(PIN_HOME, pigpio.FALLING_EDGE, lambda g, l, t: self.edges.append(("home", self.pos, t)))
        self.release()                                  # v10: fully extended; its position is unknown at start, so this waits a full stroke

    def say(self, msg: str):
        """--sim: print each step, so a dry run shows the sequence the hardware would follow."""
        if self.sim:
            print(f"  sim: {msg}")

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
        """Trapezoidal move of n steps (sign: + = the way the machine runs) with pigpio waves. v10: only with the P16 fully
        extended, and with the NEMA 11 free (or seeking) for the move; go_module() and home() hold it again after."""
        if n == 0:
            return
        if abs(self.ext - P16_HOME_EXT) > 0.5:
            raise SystemExit("refusing to move the chain: the P16 is not fully extended (the module at the station is tilted)")
        self.nema11("seek" if self.seek_rev_s else "free")
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
        n = self.module_steps(k) - self.pos
        self.move_steps(n, **kw)
        if n:
            self.say(f"chain {n:+d} steps: module {self.module} -> {k % N_MODULES} at the station")
        self.nema11("held")                          # v10: enabled again after the move, the arriving gear in mesh
        self.module = k % N_MODULES
        if n:
            self.seek_mesh()                         # v12: every index, then check the cradle's switch

    # ---- v12: the spring-loaded pinion's cradle
    def cradle_lifted(self) -> bool:
        """v12: the cradle's US5881 reads low while the EC's magnet is over it, i.e. while the pinion rides more than about 0.8 mm over
        tight mesh: resting on the gear's tips instead of in its gaps."""
        if self.pi is None:
            return self.sim_stub > 0
        return self.pi.read(PIN_HALL_CRADLE) == 0

    def _turn(self, rev_s: float, t: float):
        """Turn the pinion at rev_s (+ turns the auger toward the outlet) for t seconds on the STEP pin's hardware PWM, the driver on."""
        if self.pi is None:
            return
        self.pi.write(PIN_AUG_ENA, 0)
        self.pi.write(PIN_AUG_DIR, 1 if rev_s > 0 else 0)
        self.pi.hardware_PWM(PIN_AUG_STEP, int(abs(rev_s) * NEMA11_USTEPS), 500000)
        time.sleep(t)
        self.pi.hardware_PWM(PIN_AUG_STEP, 0, 0)
        self.pi.write(PIN_AUG_STEP, 0)

    def seek_mesh(self, tries: int = SEEK12_TRIES) -> dict:
        """v12, after every index: turn the pinion slowly forward and back (SEEK12_REV_S for SEEK12_T each way, so the auger ends where it
        started), then read the cradle's switch; while it still reads lifted, try again the other way round, up to `tries` seeks. A
        pinion left on the gear's tips is lifted on its spring with nothing forced (the model's 6.4-8.4 N), so a stop here is safe:
        back the chain off 2 mm and index again (TEST-PLAN T6a)."""
        before = self.cradle_lifted()
        readings = [before]
        n = 0
        for k in range(tries):
            if k > 0 and not self.cradle_lifted():
                break
            d = 1 if k % 2 == 0 else -1
            self._turn(d * SEEK12_REV_S, SEEK12_T)
            self._turn(-d * SEEK12_REV_S, SEEK12_T)
            if self.pi is not None:
                time.sleep(0.05)
            n += 1
            if self.sim_stub > 0:
                self.sim_stub -= 1
            readings.append(self.cradle_lifted())
            self.say(f"seek {n} ({'forward, back' if d > 0 else 'back, forward'} at {SEEK12_REV_S:g} rev/s, {SEEK12_T:g} s each way): "
                     f"cradle switch reads {'LIFTED' if readings[-1] else 'seated'}")
        if readings[-1]:                             # v12 fallback: the gear leaves the pinion's tips and comes back at another phase
            back = round(REINDEX12_MM * self.steps_per_mm())
            self.say(f"still lifted: back the chain off {REINDEX12_MM:g} mm and index again")
            self.move_steps(-back, speed_mm_s=20.0, accel_mm_s2=200.0)
            self.move_steps(back, speed_mm_s=20.0, accel_mm_s2=200.0)
            self.nema11("held")
            if self.sim_stub > 0:
                self.sim_stub -= 1
            self._turn(SEEK12_REV_S, SEEK12_T)
            self._turn(-SEEK12_REV_S, SEEK12_T)
            n += 1
            readings.append(self.cradle_lifted())
            self.say(f"re-indexed and seek {n}: cradle switch reads {'LIFTED' if readings[-1] else 'seated'}")
        self.last_seek = dict(hall_before=int(before), seeks=n, hall_after=int(readings[-1]))
        if readings[-1]:
            raise SystemExit("the pinion is still on the gear's tips after the seek, a second try and a re-index (the cradle's switch reads "
                             "lifted): turn the pinion by hand, and check the teeth's PTFE lube (TEST-PLAN T6a)")
        return self.last_seek

    def alarm(self) -> bool:
        return bool(self.pi and self.pi.read(PIN_ALARM) == 0)

    def home(self, speed_mm_s: float = 20.0):
        """Creep the way the machine runs until HOME fires (carriage 1's second magnet), then call that step count
        module 0."""
        self.say("homing: creep the way the machine runs until HOME fires")
        self.edges.clear()
        limit = self.module_steps(N_MODULES + 1)
        moved = 0
        while moved < limit and not any(e[0] == "home" for e in self.edges):
            self.move_steps(self.module_steps(1) // 8, speed_mm_s, 200.0)
            moved += self.module_steps(1) // 8
        hits = [e for e in self.edges if e[0] == "home"]
        if not hits:
            raise SystemExit("HOME never fired: check the magnet on carriage 1 and the sensor wiring")
        self.say(f"HOME fired {hits[0][1]} steps in: that is step 0")
        self.pos -= hits[0][1]                       # the edge becomes step 0
        self.module = 0
        self.go_module(0)                            # back onto the edge
        self.edges.clear()

    # ---- station
    def nema11(self, mode: str):
        """v10: the NEMA 11's DRV8825. "held": enabled (EN low), at rest and to turn the auger. "free": disabled (EN high, outputs
        off) while the chain moves: the arriving gear slides into mesh with the pinion from the side, and a held pinion would make
        it roll round and turn the auger about 50 deg per pass, while a free one turns out of its way. "seek" (--seek): enabled and
        stepping at seek_rev_s on the STEP pin's hardware PWM, so the pinion's teeth find the gear's gaps (+ turns the auger toward
        the outlet, - away from it, the default: the door opens as the module arrives). Enabling it again pulls the rotor to the
        driver's step, within 3.6 deg of the pinion (1.6 of the auger)."""
        if mode == self.n11_mode:
            return
        if self.pi:
            if self.n11_mode == "seek":
                self.pi.hardware_PWM(PIN_AUG_STEP, 0, 0)
                self.pi.write(PIN_AUG_STEP, 0)          # a plain output again, for auger_revs' waves
            self.pi.write(PIN_AUG_ENA, 1 if mode == "free" else 0)
            if mode == "seek":
                self.pi.write(PIN_AUG_DIR, 1 if self.seek_rev_s > 0 else 0)
                self.pi.hardware_PWM(PIN_AUG_STEP, int(abs(self.seek_rev_s) * NEMA11_USTEPS), 500000)
        self.say({"held": "NEMA 11 held (DRV8825 enabled)", "free": "NEMA 11 free (DRV8825 disabled, EN high)",
                  "seek": f"NEMA 11 seeking at {self.seek_rev_s:+g} rev/s"}[mode])
        self.n11_mode = mode

    def actuator(self, ext_mm: float, wait: bool = True):
        """v10: the one P16-100's LAC (RC: 1.0-2.0 ms = 0-100 mm)."""
        ext = max(0.0, min(ACT_STROKE, ext_mm))
        if self.pi:
            self.pi.set_servo_pulsewidth(PIN_LAC, 1000 + 1000 * ext / ACT_STROKE)
        if wait:
            time.sleep(abs(ext - self.ext) / 30.0 + 0.3)     # about 30 mm/s loaded (46 no-load)
        self.ext = ext

    def tilt(self, deg: float):
        """v10: retract the P16 to turn the coupled module, and the EC with it, up about the hinge to deg (TILT_MIN-TILT_MAX).
        Only with a module coupled, i.e. with the chain stopped on an index."""
        ext = tilt_to_ext(deg)
        self.say(f"P16 to {ext:.2f} mm: {deg:g} deg")
        self.actuator(ext)

    def release(self):
        """v10: the station's home, between doses: the P16 fully extended (P16_HOME_EXT), so the module is back down at 4 deg
        (still coupled, its gear in mesh) and the EC's guide shoe is in its funnel seat. The chain only moves from here."""
        self.say(f"P16 to {P16_HOME_EXT:.2f} mm: fully extended, {TILT_MIN:g} deg, the EC's shoe in its seat")
        self.actuator(P16_HOME_EXT)

    def auger_revs(self, revs: float, rpm: float = 30.0):
        """Turn the auger (positive = toward the outlet) through the 20T:44T pinion. v10: with the DRV8825 enabled."""
        if not self.sim and not getattr(self, "_current_noted", False):
            print(f"NEMA 11 driver: DRV8825 current limit must be {AUGER_CURRENT_MA} mA "
                  f"(Vref {AUGER_CURRENT_MA / 2000:.3f} V) before dosing")
            self._current_noted = True
        self.nema11("held")
        self.say(f"auger {revs:+g} rev at {rpm:g} rpm")
        n = round(abs(revs) * GEAR_RATIO * NEMA11_USTEPS)
        if self.pi is None and revs > 0:
            self._sim_g = getattr(self, "_sim_g", 0.0) + 0.105 * revs     # --sim: salt's 105 mg per turn
        if n == 0 or self.pi is None:
            time.sleep(abs(revs) / rpm * 60.0 if self.pi is None else 0)
            return
        self.pi.write(PIN_AUG_DIR, 1 if revs > 0 else 0)
        period = int(1e6 / (rpm / 60.0 * GEAR_RATIO * NEMA11_USTEPS))
        for i in range(0, n, 4000):
            self._wave(PIN_AUG_STEP, [period] * min(4000, n - i))

    def tap(self, n: int = 1, ms: int = 10, hz: float = 2.0):
        if n:
            self.say(f"tap x{n}")
        for _ in range(n):
            if self.pi:
                self.pi.write(PIN_TAP, 1)
            time.sleep(ms / 1000)
            if self.pi:
                self.pi.write(PIN_TAP, 0)
            time.sleep(max(0.0, 1.0 / hz - ms / 1000))

    def dose_to(self, target_g: float, tilt: float, rpm: float = 30.0, step_revs: float = 0.25, slow_frac: float = 0.8,
                max_revs: float = 40.0) -> tuple[float, float]:
        """v5: dose by weight. Tare-free: reads the stable mass first, tilts, and turns the auger in step_revs increments (a
        quarter of that and half the speed past slow_frac of the target), polling the balance after each (the reading is
        unstable while powder falls, so it takes it as it is); then holds, goes back to 4 deg (release), reverses one turn at
        rest, and returns (stable dose, auger revs). v10: start with a module coupled (after an index); the dose falls 18 mm
        through the front deck's 16 mm hole into the beaker; keep the bay window's door shut."""
        g0 = self.grams_stable()
        self.tilt(tilt)
        dosed, revs = 0.0, 0.0
        while dosed < target_g and revs < max_revs:
            slow = dosed >= slow_frac * target_g
            r = step_revs / 4 if slow else step_revs
            self.auger_revs(r, rpm / 2 if slow else rpm)
            revs += r
            time.sleep(0.3)
            g = self.grams(stable_only=False)
            if g == g:
                dosed = g - g0
        self.say(f"hold {DOSE_HOLD_S:g} s at {tilt:g} deg")
        time.sleep(DOSE_HOLD_S)
        self.release()
        self.auger_revs(-REVERSE_REVS, rpm)
        return self.grams_stable() - g0, revs

    def grams_stable(self, tries: int = 40) -> float:
        """The first stable (ST) reading, polling at about 4 Hz for up to tries reads."""
        for _ in range(tries):
            g = self.grams()
            if g == g:
                return g
            time.sleep(0.25)
        return float("nan")

    def grams(self, stable_only: bool = True) -> float:
        """A&D HR-202i (or the HR-100A) over RS-232 (A&D standard format, 2400 baud 7E1): send "Q", read "ST,+00012.3456  g".
        Returns nan when the balance answers unstable (US) or not at all."""
        if self.pi is None:
            return round(getattr(self, "_sim_g", 0.0), 4)
        import serial                                  # pyserial
        if not hasattr(self, "_bal"):
            self._bal = serial.Serial("/dev/serial0", 2400, bytesize=7, parity="E", stopbits=1, timeout=1.0)
        self._bal.reset_input_buffer()
        self._bal.write(b"Q\r\n")
        line = self._bal.readline().decode("ascii", "replace").strip()
        if not line.startswith("ST,") and (stable_only or not line.startswith("US,")):
            return float("nan")
        try:
            return float(line[3:].split()[0])
        except ValueError:
            return float("nan")


def _profile(n: int, v: float, a: float) -> list[int]:
    """Per-step periods (us) for a trapezoid: accelerate at a to v, cruise, decelerate."""
    out = []
    n_acc = min(int(v * v / (2 * a)), n // 2)
    for i in range(n):
        k = min(i, n - 1 - i)
        vi = v if k >= n_acc else math.sqrt(2 * a * (k + 1))
        out.append(int(1e6 / max(vi, 50.0)))
    return out


LOG_COLUMNS = ["run", "utc", "cmd", "module", "target_steps", "pos_steps", "move_s", "index_edge_steps", "alarm", "dial_mm",
               "tilt", "revs", "rpm", "taps", "hold_s", "reverse_revs", "auger_current_ma", "dose_g", "p16_ext_mm",
               "nema11", "rail", "hall_before", "seeks", "hall_after"]   # v10: the NEMA 11's mode and the rail's result (T6a); v12: the cradle's switch and seeks


def log_row(path: Path, row: dict):
    """Append one row; every command writes the same columns (blank where they don't apply), so one CSV holds a
    whole session."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLUMNS, restval="")
        if new:
            w.writeheader()
        w.writerow(row)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim", action="store_true", help="no hardware: simulated pins, prints each step")
    ap.add_argument("--ppr", type=int, default=4000)
    ap.add_argument("--log", type=Path, default=Path("runs") / time.strftime("%Y-%m-%d.csv"))
    ap.add_argument("--ask", action="store_true", help="prompt for a dial-indicator reading after each move")
    ap.add_argument("--seek", action="store_true", help="v10: step the NEMA 11 slowly while the chain moves instead of leaving it "
                    "free (the DRV8825 disabled), so the pinion's teeth find the arriving gear's gaps (TEST-PLAN T6a)")
    ap.add_argument("--seek-rev-s", type=float, default=SEEK_REV_S, help="v10: the pinion's rev/s for --seek, either direction "
                    "(+ turns the auger toward the outlet, - away from it)")
    ap.add_argument("--sim-stub", type=int, default=0, help="v12, with --sim: the pinion lands on the gear's tips and needs this many seeks to drop in")
    ap.add_argument("--ask-rail", action="store_true", help="v10: prompt for what the rail did after each chain move "
                    "(clean, clash or jam; TEST-PLAN T6a)")
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
    p.add_argument("--tilt", type=float, default=30.0, help=f"hinge angle, deg, {TILT_MIN:g}-{TILT_MAX:g} ({TILT_MIN:g}: coupled, "
                   "between doses; the frame is not pitched)")
    p.add_argument("--hold", type=float, default=2.0)
    p.add_argument("--cycles", type=int, default=1, help="v10: repeat, resting between cycles to keep the P16 within its 20 %% "
                   "duty (4-70-4 deg: about 16 s; TEST-PLAN T6c, T12)")
    p = sub.add_parser("dose-to", help="v5: dose a target mass onto the balance")
    p.add_argument("grams", type=float)
    p.add_argument("--tilt", type=float, default=30.0, help=f"dose tilt, deg, {TILT_MIN:g}-{TILT_MAX:g}")
    p.add_argument("--rpm", type=float, default=30.0)
    p = sub.add_parser("dose")
    p.add_argument("--tilt", type=float, default=30.0, help=f"dose tilt, deg, {TILT_MIN:g}-{TILT_MAX:g} (20-40 doses best)")
    p.add_argument("--revs", type=float, default=2.0, help="auger revolutions forward")
    p.add_argument("--rpm", type=float, default=30.0, help="auger rpm")
    p.add_argument("--taps", type=int, default=0, help="solenoid taps after the auger stops")
    p.add_argument("--hold", type=float, default=DOSE_HOLD_S, help="s at the dose tilt after the auger stops (the tail falls)")
    p.add_argument("--reverse-revs", type=float, default=REVERSE_REVS,
                   help=f"auger revolutions backwards once the P16 is back fully extended ({TILT_MIN:g} deg; never at the dose "
                        "tilt); 0 to skip")
    a = ap.parse_args()
    if a.cmd in ("station", "dose-to", "dose"):
        tilt_to_ext(a.tilt)                             # v10: refuse a tilt outside 4-65 before touching the hardware

    rig = Rig(ppr=a.ppr, sim=a.sim, seek_rev_s=a.seek_rev_s if a.seek else 0.0, sim_stub=a.sim_stub)
    rig.enable(True)
    run = time.strftime("%Y%m%dT%H%M%S")
    n11 = f"seek {rig.seek_rev_s:+g}" if rig.seek_rev_s else "free"     # v10: the NEMA 11 during chain moves, logged (T6a)

    def record(cmd: str, k: int, t0: float, **extra):
        idx = [e[1] for e in rig.edges if e[0] == "index"]
        if cmd in ("index", "repeat", "endurance", "lap"):     # v10 (T6a): the NEMA 11's mode, and what the rail did
            extra.update(nema11=n11, rail=input("rail (clean, clash or jam): ") if a.ask_rail else "")
            extra.update(rig.last_seek)                  # v12: the cradle's switch before and after, and how many seeks it took
        row = dict(run=run, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), cmd=cmd, module=k % N_MODULES,
                   target_steps=rig.module_steps(k), pos_steps=rig.pos, move_s=round(time.time() - t0, 3),
                   index_edge_steps=";".join(map(str, idx)), alarm=int(rig.alarm()),
                   dial_mm=input("dial reading (mm): ") if a.ask else "", **extra)
        log_row(a.log, row)
        rig.edges.clear()
        print(row)

    try:
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
            for i in range(a.cycles):
                t0 = time.time()
                rig.tilt(a.tilt)                        # v10: from 4 deg (coupled) up to the tilt
                rig.say(f"hold {a.hold:g} s")
                time.sleep(a.hold)
                rig.release()                           # back to 4 deg, fully extended
                record("station", rig.module, t0, tilt=a.tilt, hold_s=a.hold, p16_ext_mm=round(tilt_to_ext(a.tilt), 2))
                if i + 1 < a.cycles:
                    rest = p16_rest_s(a.tilt)
                    print(f"P16 rest {rest:.1f} s ({P16_DUTY:.0%} duty), cycle {i + 1} of {a.cycles} done")
                    time.sleep(rest)
        elif a.cmd == "dose-to":
            t0 = time.time()
            g, revs = rig.dose_to(a.grams, a.tilt, a.rpm)
            record("dose-to", rig.module, t0, tilt=a.tilt, revs=round(revs, 3), rpm=a.rpm, reverse_revs=REVERSE_REVS,
                   auger_current_ma=AUGER_CURRENT_MA, dose_g=round(g, 4), p16_ext_mm=round(tilt_to_ext(a.tilt), 2))
        elif a.cmd == "dose":
            t0 = time.time()
            g0 = rig.grams()
            rig.tilt(a.tilt)                            # v10: from 4 deg, coupled by the last index
            rig.auger_revs(a.revs, a.rpm)
            rig.tap(a.taps)
            rig.say(f"hold {a.hold:g} s at {a.tilt:g} deg")
            time.sleep(a.hold)                          # the tail falls into the beaker before the P16 extends
            rig.release()                               # fully extended: back to 4 deg, the EC's shoe in its seat
            if a.reverse_revs:
                rig.auger_revs(-abs(a.reverse_revs), a.rpm)   # at rest at 4 deg only: pulls powder back from the exit
            g1 = rig.grams()
            record("dose", rig.module, t0, tilt=a.tilt, revs=a.revs, rpm=a.rpm, taps=a.taps, hold_s=a.hold,
                   reverse_revs=a.reverse_revs, auger_current_ma=AUGER_CURRENT_MA, dose_g=round(g1 - g0, 4),
                   p16_ext_mm=round(tilt_to_ext(a.tilt), 2))
    except BaseException:
        # v10: on any error, stop a seek (pigpiod keeps a hardware PWM running after the script) and leave the NEMA 11 free
        rig.nema11("free")
        raise
    rig.enable(False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Sanity checks for the powder-doser digital twin (powder_sim.py v2).

Run with:  python optimization/simulation/test_powder_sim.py
Plain-assert style matching hardware/test-module/firmware/sim/test_three_phase.py.

White-box access (lip_g, screw_cells, tap yield via compartment deltas) is
allowed HERE for verifying the physics; benchmarked controllers only ever see
read_balance() (see optimization/benchmarks/rig.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from powder_sim import Context, POWDERS, PowderDoserSim

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"FAIL  {name}  {detail}")


def total_mass(sim):
    return (sim.hopper_g + sum(sim.screw_cells) + sim.lip_g
            + sum(m for _, m in sim.in_flight) + sim.dispensed_g)


def tap_yield(sim):
    """Ejected grams of one tap, measured from compartment deltas (tap() no
    longer returns mass -- controllers must not see it; tests may)."""
    before = sim.dispensed_g + sum(m for _, m in sim.in_flight)
    sim.tap()
    return sim.dispensed_g + sum(m for _, m in sim.in_flight) - before


print("== conservation / basic sanity ==")
sim = PowderDoserSim(POWDERS["salt"], Context(), seed=42)
m0 = total_mass(sim)
sim.set_tilt_deg(45.0)
sim.set_auger_rpm(55.0)
sim.step(20.0)
sim.set_auger_rpm(0.0)
for _ in range(5):
    sim.tap()
    sim.step(0.6)
sim.step(3.0)
check("mass is conserved", abs(total_mass(sim) - m0) < 1e-9,
      f"{total_mass(sim)} vs {m0}")
check("powder was dispensed", sim.dispensed_g > 0.5, f"{sim.dispensed_g}")
check("no negative compartments",
      sim.hopper_g >= 0 and sim.lip_g >= 0 and sim.dispensed_g >= 0
      and min(sim.screw_cells) >= 0)
grams, stable = sim.read_balance()
check("balance settled near truth (idle, within bias+drift)",
      abs(grams - sim.dispensed_g) < 0.008, f"{grams} vs {sim.dispensed_g}")
check("balance stable when idle", stable)

print("== determinism / read-pattern independence ==")
a = PowderDoserSim(POWDERS["salt"], Context(), seed=7)
b = PowderDoserSim(POWDERS["salt"], Context(), seed=7)
for s in (a, b):
    s.set_tilt_deg(30.0)
    s.set_auger_rpm(40.0)
for i in range(100):
    a.step(0.05)
    b.step(0.05)
    if i % 3 == 0:            # b is polled much harder than a
        for _ in range(20):
            b.read_balance()
check("same seed -> same trajectory", abs(a.dispensed_g - b.dispensed_g) < 1e-12)
check("extra balance reads do not alter physics (split RNG streams)",
      abs(a.dispensed_g - b.dispensed_g) < 1e-12)
check("extra reads do not change future readings",
      a.read_balance() == b.read_balance())

print("== balance is sample-and-hold on its own clock ==")
s = PowderDoserSim(POWDERS["salt"], Context(), seed=13)
s.step(1.0)
r1 = s.read_balance()
r2 = s.read_balance()          # same serial tick -> identical sample
check("repeated reads between ticks are identical", r1 == r2)
s.step(0.02)                   # < 1/10 Hz tick
check("sub-tick step keeps the held sample", s.read_balance() == r1)

print("== dispensed mass is monotone (powder cannot be removed) ==")
sim = PowderDoserSim(POWDERS["salt"], Context(), seed=3)
sim.set_tilt_deg(45.0)
sim.set_auger_rpm(60.0)
last, mono = 0.0, True
for _ in range(200):
    sim.step(0.1)
    if sim.dispensed_g < last - 1e-12:
        mono = False
    last = sim.dispensed_g
check("dispensed_g never decreases", mono)

print("== interaction: steeper tilt dispenses more per tap ==")
def per_tap_yield(tilt, n=30):
    s = PowderDoserSim(POWDERS["salt"], Context(), seed=11)
    s.set_tilt_deg(tilt)
    s.step(1.0)
    total = 0.0
    for _ in range(n):
        s.lip_g = 0.20          # white-box: same lip charge every tap
        total += tap_yield(s)
        s.step(0.3)
    return total / n

y_flat, y_steep = per_tap_yield(2.0), per_tap_yield(40.0)
check("taps at 40 deg >> taps at 2 deg", y_steep > 2.0 * max(y_flat, 1e-6),
      f"steep {y_steep:.4f} vs flat {y_flat:.4f}")
check("steep tap yield ~1-30 mg per tap (bench range)",
      0.001 < y_steep < 0.030, f"{y_steep:.4f}")
zero_seen = False
s = PowderDoserSim(POWDERS["lactose"], Context(), seed=17)
s.set_tilt_deg(10.0)
s.step(1.0)
for _ in range(20):
    s.lip_g = 0.05
    if tap_yield(s) == 0.0:
        zero_seen = True
    s.step(0.3)
check("zero-yield taps exist (hurdle model)", zero_seen)

print("== interaction: tap-after-rotation beats repeated taps ==")
def avg_over_seeds(fn, seeds=range(8)):
    vals = [fn(sd) for sd in seeds]
    return sum(vals) / len(vals)

def depletion_pair(seed):
    s = PowderDoserSim(POWDERS["salt"], Context(), seed=seed)
    s.set_tilt_deg(20.0)
    s.step(1.0)
    s.rotate_degrees(360.0, 40.0)
    s.step(0.5)
    first = tap_yield(s)
    s.step(0.6)
    last = 0.0
    for _ in range(6):
        last = tap_yield(s)
        s.step(0.6)
    s.rotate_degrees(180.0, 40.0)   # replenish the lip
    s.step(0.5)
    refreshed = tap_yield(s)
    return first, last, refreshed

firsts, lasts, refresheds = zip(*[depletion_pair(sd) for sd in range(8)])
first, last, refreshed = (sum(v) / len(v) for v in (firsts, lasts, refresheds))
check("repeated taps deplete the lip", last < 0.5 * max(first, 1e-9),
      f"first {first:.4f} last {last:.4f}")
check("rotation replenishes tap yield", refreshed > 2.0 * max(last, 1e-6),
      f"refreshed {refreshed:.4f} vs depleted {last:.4f}")

print("== screw transport: powder in the flights, frozen when stopped ==")
s = PowderDoserSim(POWDERS["salt"], Context(screw_primed=False), seed=21)
s.set_tilt_deg(45.0)
s.step(1.0)
s.rotate_degrees(90.0, 40.0)      # a quarter rev from an empty screw
s.step(3.0)
early = s.dispensed_g + sum(m for _, m in s.in_flight) + s.lip_g
check("short rotation from empty screw delivers almost nothing to the lip",
      early < 0.2 * POWDERS["salt"].feed_factor_g_per_rev * 0.25,
      f"{early:.4f} g reached lip region")
check("...because it is held in the screw", sum(s.screw_cells) > 0.5 * early or
      sum(s.screw_cells) > 0.005, f"screw {sum(s.screw_cells):.4f}")
held = sum(s.screw_cells)
s.step(10.0)                      # screw stopped: transport must freeze
check("screw hold-up does not move while stopped",
      abs(sum(s.screw_cells) - held) < 1e-9)
s.rotate_degrees(3 * 360.0, 40.0)
s.step(3.0)
check("continued rotation delivers the held powder",
      s.dispensed_g + s.lip_g + sum(m for _, m in s.in_flight) > 0.5 *
      POWDERS["salt"].feed_factor_g_per_rev, f"{s.dispensed_g:.3f}")

print("== fill level: starved screw feeds less per rev ==")
full = PowderDoserSim(POWDERS["salt"], Context(hopper_fill_frac=0.9), seed=2)
low = PowderDoserSim(POWDERS["salt"], Context(hopper_fill_frac=0.08), seed=2)
for s in (full, low):
    s.set_tilt_deg(45.0)
    s.step(1.0)
check("feed factor drops at low fill",
      low.feed_factor_g_per_rev() < 0.7 * full.feed_factor_g_per_rev(),
      f"low {low.feed_factor_g_per_rev():.4f} full {full.feed_factor_g_per_rev():.4f}")

print("== context: humid, exposed powder flows worse ==")
dry = PowderDoserSim(POWDERS["silicon"],
                     Context(humidity_pct_rh=20.0, exposure_hours=0.0), seed=9)
wet = PowderDoserSim(POWDERS["silicon"],
                     Context(humidity_pct_rh=85.0, exposure_hours=48.0), seed=9)
check("effective cohesion rises with humidity exposure",
      wet.effective_cohesion() > dry.effective_cohesion() + 0.03,
      f"wet {wet.effective_cohesion():.3f} dry {dry.effective_cohesion():.3f}")
check("moisture saturates at equilibrium (no unbounded uptake)",
      wet.moisture <= wet.powder.hygroscopicity * 0.85 + 1e-9,
      f"{wet.moisture:.4f}")
for s in (dry, wet):
    s.set_tilt_deg(45.0)
    s.set_auger_rpm(50.0)
    s.step(15.0)
check("humid powder dispenses less in equal time",
      wet.dispensed_g < dry.dispensed_g,
      f"wet {wet.dispensed_g:.3f} dry {dry.dispensed_g:.3f}")

print("== cohesive powder can block; taps clear it ==")
coh = PowderDoserSim(POWDERS["lactose"],
                     Context(humidity_pct_rh=80.0, exposure_hours=72.0), seed=1)
coh.set_tilt_deg(45.0)
coh.set_auger_rpm(80.0)
blocked_seen = False
for _ in range(2400):
    coh.step(0.25)
    if coh.flow_state == "blocked":
        blocked_seen = True
        break
check("blockage occurs for cohesive humid powder", blocked_seen,
      f"state stayed {coh.flow_state}")
if blocked_seen:
    check("blockage stops the feed", coh.feed_factor_g_per_rev() == 0.0)
    for _ in range(15):
        coh.tap()
        coh.step(0.2)
        if coh.flow_state == "flowing":
            break
    check("taps clear the blockage", coh.flow_state == "flowing",
          f"state {coh.flow_state}")
else:
    check("blockage stops the feed", False, "no blockage to test")
    check("taps clear the blockage", False, "no blockage to test")

print("== balance: unstable while actuating, settles after ==")
s = PowderDoserSim(POWDERS["salt"], Context(), seed=4)
s.set_tilt_deg(45.0)
s.set_auger_rpm(60.0)
s.step(5.0)
_, stable_running = s.read_balance()
s.set_auger_rpm(0.0)
s.step(8.0)
_, stable_settled = s.read_balance()
check("unstable while auger runs", not stable_running)
check("stable after settling", stable_settled)
reads = []
for _ in range(20):
    s.step(0.1)
    reads.append(s.read_balance()[0])
spread = max(reads) - min(reads)
check("idle noise spread is sub-mg", spread < 1.5e-3, f"{spread}")

print("== dose rate telemetry (scoring only) ==")
s = PowderDoserSim(POWDERS["salt"], Context(), seed=6)
s.set_tilt_deg(45.0)
s.set_auger_rpm(80.0)
s.step(6.0)
rate_running = s.dose_rate_g_per_s
s.set_auger_rpm(0.0)
s.step(5.0)
rate_stopped = s.dose_rate_g_per_s
check("dose rate positive while feeding", rate_running > 0.05, f"{rate_running}")
check("dose rate decays to ~0 after stop", rate_stopped < 0.02, f"{rate_stopped}")
check("tap() returns nothing (no privileged telemetry)", s.tap() is None)

print("== hopper empties and feed stops ==")
s = PowderDoserSim(POWDERS["salt"], Context(hopper_fill_frac=0.02,
                                            hopper_capacity_g=10.0,
                                            screw_primed=False), seed=8)
m0 = total_mass(s)
s.set_tilt_deg(45.0)
s.set_auger_rpm(100.0)
s.step(400.0)
check("hopper never goes negative", s.hopper_g >= 0.0, f"{s.hopper_g}")
check("dispensed bounded by initial load", s.dispensed_g <= m0 + 1e-9,
      f"{s.dispensed_g} vs {m0}")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)

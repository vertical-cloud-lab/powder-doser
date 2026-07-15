#!/usr/bin/env python3
"""Sanity checks for the powder-doser digital twin (powder_sim.py).

Run with:  python optimization/simulation/test_powder_sim.py
Plain-assert style matching hardware/test-module/firmware/sim/test_three_phase.py.
"""
import math
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
    return sim.hopper_g + sim.lip_g + sum(m for _, m in sim.in_flight) + sim.dispensed_g


def taps_yield(sim, n, gap_s=0.6):
    before = sim.dispensed_g + sum(m for _, m in sim.in_flight) + sim.lip_g * 0
    out = 0.0
    for _ in range(n):
        out += sim.tap()
        sim.step(gap_s)
    return out


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
      sim.hopper_g >= 0 and sim.lip_g >= 0 and sim.dispensed_g >= 0)
grams, stable = sim.read_balance()
check("balance settled near truth (idle)",
      abs(grams - sim.dispensed_g) < 0.005, f"{grams} vs {sim.dispensed_g}")
check("balance stable when idle", stable)

print("== determinism ==")
a = PowderDoserSim(POWDERS["salt"], Context(), seed=7)
b = PowderDoserSim(POWDERS["salt"], Context(), seed=7)
for s in (a, b):
    s.set_tilt_deg(30.0)
    s.set_auger_rpm(40.0)
    s.step(5.0)
check("same seed -> same trajectory", abs(a.dispensed_g - b.dispensed_g) < 1e-12)

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
def per_tap_yield(tilt):
    """Average ejected mass for a tap on an identically charged lip."""
    s = PowderDoserSim(POWDERS["salt"], Context(), seed=11)
    s.set_tilt_deg(tilt)
    s.step(1.0)
    total = 0.0
    for _ in range(5):
        s.lip_g = 0.20          # white-box: same lip charge every tap
        total += s.tap()
    return total / 5.0

y_flat, y_steep = per_tap_yield(2.0), per_tap_yield(40.0)
check("taps at 40 deg >> taps at 2 deg", y_steep > 2.0 * max(y_flat, 1e-6),
      f"steep {y_steep:.4f} vs flat {y_flat:.4f}")

print("== interaction: tap-after-rotation beats repeated taps ==")
s = PowderDoserSim(POWDERS["salt"], Context(), seed=5)
s.set_tilt_deg(20.0)
s.step(1.0)
s.rotate_auger_deg(360.0, 40.0)
s.step(0.5)
first = s.tap()
s.step(0.6)
repeats = [s.tap() for _ in range(6) if s.step(0.6) is None]
s.rotate_auger_deg(180.0, 40.0)   # replenish the lip
s.step(0.5)
refreshed = s.tap()
check("repeated taps deplete the lip", repeats[-1] < 0.5 * max(first, 1e-9),
      f"first {first:.4f} last {repeats[-1]:.4f}")
check("rotation replenishes tap yield", refreshed > 2.0 * max(repeats[-1], 1e-6),
      f"refreshed {refreshed:.4f} vs depleted {repeats[-1]:.4f}")

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
for s in (dry, wet):
    s.set_tilt_deg(45.0)
    s.set_auger_rpm(50.0)
    s.step(15.0)
check("humid powder dispenses less in equal time",
      wet.dispensed_g < dry.dispensed_g,
      f"wet {wet.dispensed_g:.3f} dry {dry.dispensed_g:.3f}")

print("== cohesive powder can arch; a tap clears it ==")
coh = PowderDoserSim(POWDERS["lactose"],
                     Context(humidity_pct_rh=80.0, exposure_hours=72.0), seed=1)
coh.set_tilt_deg(45.0)
coh.set_auger_rpm(80.0)
arched_seen = False
for _ in range(1200):
    coh.step(0.25)
    if coh.arched:
        arched_seen = True
        break
check("arching occurs for cohesive humid powder", arched_seen)
if arched_seen:
    check("arch stops the feed", coh.feed_factor_g_per_rev() == 0.0)
    for _ in range(10):
        coh.tap()
        coh.step(0.2)
        if not coh.arched:
            break
    check("taps clear the arch", not coh.arched)
else:
    check("arch stops the feed", False, "no arch to test")
    check("taps clear the arch", False, "no arch to test")

print("== balance: unstable while actuating, settles after ==")
s = PowderDoserSim(POWDERS["salt"], Context(), seed=4)
s.set_tilt_deg(45.0)
s.set_auger_rpm(60.0)
s.step(5.0)
_, stable_running = s.read_balance()
s.set_auger_rpm(0.0)
s.step(6.0)   # the steep lip keeps trickling ~4 s after the auger stops
_, stable_settled = s.read_balance()
check("unstable while auger runs", not stable_running)
check("stable after settling", stable_settled)
noisy_sd = s._balance_noise_sd()
check("idle noise floor is sub-mg", noisy_sd < 5e-4, f"{noisy_sd}")

print("== dose rate telemetry ==")
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

print("== hopper empties and feed stops ==")
s = PowderDoserSim(POWDERS["salt"], Context(hopper_fill_frac=0.02,
                                            hopper_capacity_g=10.0), seed=8)
s.set_tilt_deg(45.0)
s.set_auger_rpm(100.0)
s.step(400.0)
check("hopper never goes negative", s.hopper_g >= 0.0, f"{s.hopper_g}")
check("dispensed bounded by initial load", s.dispensed_g <= 0.2 + 1e-9)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)

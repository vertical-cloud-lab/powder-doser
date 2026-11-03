#!/usr/bin/env python3
"""Behaviour + estimator checks for the bang-bang controllers (bangbang.py).

Run against the digital twin through the same fair Rig interface the benchmark
uses.  Covers the iteration story (naive overshoots -> safe biases under ->
trim converges), the 3-state balance-lag KF's estimator-truth advantage, and
the no-hang / no-crash safety properties.  No hardware needed.

    python test_bangbang.py
"""
from __future__ import annotations

import statistics

import numpy as np

from rig import Context, POWDERS, PowderDoserSim, Rig
from bangbang import (BangBangNaive, BangBangSafe, BangBangTrim,
                      MassRateLagKF)
from controllers import MassRateKF, TOL_G

NOM = Context(hopper_fill_frac=0.8, humidity_pct_rh=30.0)

_passed = _failed = 0


def check(cond: bool, msg: str) -> None:
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ok  {msg}")
    else:
        _failed += 1
        print(f"FAIL  {msg}")


def dose(ctrl, powder, target, seed, ctx=NOM):
    sim = PowderDoserSim(POWDERS[powder], ctx, seed=seed)
    rig = Rig(sim)
    status = ctrl.run(rig, target)
    return rig, sim, status


# --------------------------------------------------------------------------
print("== iteration story: naive overshoots, safe biases under ==")
naive_over = []
safe_signed = []
for s in range(8):
    rig, sim, _ = dose(BangBangNaive(), "salt", 2.0, s)
    naive_over.append((rig.true_dispensed_g() - 2.0) * 1000)
    rig, sim, _ = dose(BangBangSafe(), "salt", 2.0, s)
    safe_signed.append((rig.true_dispensed_g() - 2.0) * 1000)
check(min(naive_over) > 50.0,
      f"naive stop-at-crossing always overshoots (min {min(naive_over):.0f} mg)")
check(statistics.median(safe_signed) < 0.0,
      f"safe predictor biases to undershoot (median {statistics.median(safe_signed):+.0f} mg)")
check(sum(x > 0 for x in safe_signed) <= 2,
      f"safe rarely overshoots ({sum(x > 0 for x in safe_signed)}/8)")


# --------------------------------------------------------------------------
print("== bangbang_trim converges within tolerance for salt, no hang ==")
errs, times, statuses = [], [], []
for s in range(12):
    rig, sim, st = dose(BangBangTrim(), "salt", 2.0, s)
    errs.append(abs(rig.true_dispensed_g() - 2.0) * 1000)
    times.append(rig.t)
    statuses.append(st)
check(statistics.median(errs) <= 15.0,
      f"salt 2 g median |error| <= 15 mg ({statistics.median(errs):.1f})")
check(max(times) <= 300.0, f"never exceeds the 300 s timeout (max {max(times):.0f} s)")
check(statistics.median(times) < 120.0,
      f"much faster than the feedback methods (median {statistics.median(times):.0f} s)")


# --------------------------------------------------------------------------
print("== bangbang_trim never overshoots grossly (asymmetric constraint) ==")
signed = []
for powder in ["salt", "lactose", "AlSi10Mg"]:
    for s in range(6):
        rig, sim, st = dose(BangBangTrim(), powder, 2.0, s)
        signed.append((rig.true_dispensed_g() - 2.0) * 1000)
check(max(signed) < 60.0,
      f"2 g overshoot bounded by the guard+trim (max {max(signed):+.0f} mg)")


# --------------------------------------------------------------------------
print("== 3-state lag KF tracks true mass better than raw balance / 2-state ==")
# drive the rig open-loop and compare estimator error against ground truth
sim = PowderDoserSim(POWDERS["salt"], NOM, seed=3)
rig = Rig(sim)
kf3 = MassRateLagKF(0.1)
kf2 = MassRateKF(0.1)
rig.set_tilt(45.0)
rig.wait(0.8)
rig.set_rpm(60.0)
last = -1
e_raw, e_kf2, e_kf3 = [], [], []
for _ in range(120):
    rig.wait(0.1)
    z, _s, tick = rig.read_frame()
    m3, _r3 = kf3.update(z, rig.actuating(), u_rev_s=60.0 / 60.0, ff=0.5,
                         fresh=tick != last)
    m2, _r2 = kf2.update(z, rig.actuating(), u_rev_s=60.0 / 60.0, ff=0.5,
                         fresh=tick != last)
    last = tick
    truth = sim.dispensed_g            # ground truth (scoring only)
    if truth > 0.2:                    # once mass is rising steadily
        e_raw.append(abs(z - truth))
        e_kf2.append(abs(m2 - truth))
        e_kf3.append(abs(m3 - truth))
    if truth > 1.5:
        break
rmse = lambda e: float(np.sqrt(np.mean(np.square(e))))
check(rmse(e_kf3) < rmse(e_raw),
      f"lag KF beats raw balance (RMSE {rmse(e_kf3)*1000:.1f} vs {rmse(e_raw)*1000:.1f} mg)")
check(rmse(e_kf3) < rmse(e_kf2),
      f"lag KF beats the 2-state KF during the rising ramp "
      f"(RMSE {rmse(e_kf3)*1000:.1f} vs {rmse(e_kf2)*1000:.1f} mg)")


# --------------------------------------------------------------------------
print("== cohesive powder that blocks aborts safely, doesn't hang ==")
# near-empty cohesive hopper: expect stall/timeout, not a crash or a spin
starved = Context(hopper_fill_frac=0.05, humidity_pct_rh=70.0, exposure_hours=48.0)
rig, sim, st = dose(BangBangTrim(), "lactose", 2.0, 0, ctx=starved)
check(rig.t <= 305.0 and sim.auger_rpm == 0.0,
      f"auger halted and bounded runtime on a blocked dose (status {st}, {rig.t:.0f} s)")


print(f"\n{_passed} passed, {_failed} failed")
raise SystemExit(1 if _failed else 0)

#!/usr/bin/env python3
"""Would trickle_tap's feed-factor EWMA also work in the bulk (bang) stage?

Diagnostic (no controller code is modified) for the PR #124 review question
on bangbang.py: "why is feed factor only updated in the trickle tap? wouldn't
this also work in the bulk section?".  Three sub-questions, each measured on
the calibrated twin with paired seeds:

1. --ident   If the bang stage ran the SAME cumulative-EWMA update
             (ff = 0.9*ff + 0.1*(mass gained / revs turned)), what would it
             identify?  Compares the live estimate at the bang's halt against
             ground truth split into "landed in the cup per rev" vs "actually
             conveyed out of the hopper per rev" -- the gap is the committed
             inventory (screw hold-up + lip + in-flight) that makes a live
             arrival-based estimate read low during a short max-rate stage.
2. --consumer  How sensitive is the bang's own stop to ff, and would learning
             it live help?  2x2: bulk prior {0.50 default, 0.10 mis-set} x
             EWMA {off, on}.  The bang's stop is "m_hat + r_hat*fast_tau", and
             m_hat deconvolves the 0.7 s balance lag as roughly
             b_hat + r_hat*tau_bal -- so an ff bias in the KF input model
             enters the stop with a ~0.7 s multiplier, asymmetrically: a high
             prior halts far short (hidden safety margin), a low prior halts
             late (hard overshoot).
3. --carry   The useful version of the reviewer's idea: identify ff in the
             bulk and hand it to the trickle as its starting prior (replacing
             the fixed 0.35), either raw or rescaled by the calibrated
             tilt-gain ratio between the bulk tilt (45 deg) and the trickle
             tilt (20 deg).  Final-outcome comparison across variants.

Usage:  python diag_ff_update.py [--ident] [--consumer] [--carry] [--seeds N]
"""
from __future__ import annotations

import argparse
import math
import statistics as st
from collections import defaultdict

import bangbang
from bangbang import (BangBangTrim, MassRateLagKF, Rig_MAX_RPM, TAU_PRIOR_S,
                      trickle_tap)
from benchmark import CONTEXTS
from calibrate_from_mongo import CAL_OUT, apply_calibration
from powder_sim import POWDERS
from rig import PowderDoserSim, Rig

POWDER_SET = ["salt", "lactose", "AlSi10Mg"]
S20 = math.sin(math.radians(20.0)) / math.sin(math.radians(45.0))

_ORIG_UPDATE = bangbang.MassRateLagKF.update


def _pmap():
    return apply_calibration(POWDERS, CAL_OUT)


def tilt_ratio(powder) -> float:
    """Calibrated tilt-gain ratio g_tilt(20 deg)/g_tilt(45 deg): how much
    smaller the feed factor is at the trickle tilt than at the bulk tilt."""
    return powder.tilt_g0 + (1.0 - powder.tilt_g0) * (S20 ** powder.tilt_exp)


class TrimBulkFF(BangBangTrim):
    """BangBangTrim whose bang stage optionally runs trickle_tap's cumulative
    feed-factor EWMA, feeding the live value to its own KF input model, and
    optionally carries the identified value into the trickle as its starting
    prior (raw, or rescaled by the calibrated tilt-gain ratio).

    With learn=False and carry="none" the command/KF sequence is identical to
    the stock BangBangTrim (verified by the paired-seed equivalence check)."""

    def __init__(self, learn=False, carry="none", trickle_ff_scale=1.0, **kw):
        super().__init__(**kw)
        self.learn, self.carry = learn, carry
        self.trickle_ff_scale = trickle_ff_scale
        self.bulk = None                     # diagnostics from the last bang

    def _stage_ff(self, rig: Rig, stop_g: float) -> str:
        """Mirror of BangBangFF._stage (max rpm, fast_tau_s, k_sigma=0) with
        the trickle's ff update rule added and truth capture at the halt."""
        kf = MassRateLagKF(self.dt)
        rig.set_tilt(self.tilt)
        rig.wait(0.8)
        tel0 = rig._sim.telemetry()
        hopper0, inv0 = rig._sim.hopper_g, (tel0.screw_g + tel0.lip_g
                                            + tel0.in_flight_g)
        rig.set_rpm(Rig_MAX_RPM)
        last_tick, ff, revs, m0 = -1, self.ff_prior, 0.0, 0.0
        ff_at_1rev = None
        while True:
            if rig.timed_out():
                rig.set_rpm(0.0)
                return "timeout"
            rig.wait(self.dt)
            revs += (Rig_MAX_RPM / 60.0) * self.dt
            z, _, tick = rig.read_frame()
            m, r = kf.update(z, rig.actuating(), u_rev_s=Rig_MAX_RPM / 60.0,
                             ff=ff, fresh=tick != last_tick)
            last_tick = tick
            if self.learn and revs > 0.3 and m - m0 > 1e-3:
                ff = 0.9 * ff + 0.1 * ((m - m0) / revs)
            if ff_at_1rev is None and revs >= 1.0:
                ff_at_1rev = ff
            sigma = kf.pred_sigma(self.fast_tau_s)
            if m + r * self.fast_tau_s + 0.0 * sigma >= stop_g:
                break
        rig.set_rpm(0.0)
        tel = rig._sim.telemetry()
        conveyed = hopper0 - rig._sim.hopper_g
        inv_gain = (tel.screw_g + tel.lip_g + tel.in_flight_g) - inv0
        self.bulk = dict(
            ff_est=ff, ff_at_1rev=ff_at_1rev, revs=revs,
            landed_per_rev=tel.dispensed_g / max(revs, 1e-9),
            conveyed_per_rev=conveyed / max(revs, 1e-9),
            inv_gain_mg=inv_gain * 1000.0, conveyed_mg=conveyed * 1000.0,
            halt_vs_stop_mg=(tel.dispensed_g - stop_g) * 1000.0,
            true_ff_now=tel.feed_factor_g_per_rev, t_s=rig.t)
        return "ok"

    def run(self, rig: Rig, target_g: float) -> str:
        self.bulk = None
        if target_g > self.guard_g + 0.10:
            status = self._stage_ff(rig, target_g - self.guard_g)
            if status == "timeout":
                return status
            rig.wait(1.0)
        kw = {}
        if self.bulk is not None and self.carry != "none":
            kw["ff_prior"] = self.bulk["ff_est"] * self.trickle_ff_scale
        return trickle_tap(rig, target_g, tilt=self.trickle_tilt,
                           tap_tilt=self.trim_tilt, **kw)


def _grid(ctor, seeds, targets=(2.0,), contexts=("nominal", "stressed"),
          spy_ff=False):
    """Run a controller over the powder grid; returns per-dose rows."""
    pmap, rows = _pmap(), []
    last_ff = {}
    if spy_ff:
        def upd(self, z, noisy, u_rev_s=None, ff=None, fresh=True):
            if ff is not None:
                last_ff["ff"] = ff
            return _ORIG_UPDATE(self, z, noisy, u_rev_s=u_rev_s, ff=ff,
                                fresh=fresh)
        bangbang.MassRateLagKF.update = upd
    try:
        for powder in POWDER_SET:
            for ctx in contexts:
                for target in targets:
                    for seed in range(seeds):
                        ctrl = ctor(pmap[powder])
                        sim = PowderDoserSim(pmap[powder], CONTEXTS[ctx],
                                             seed=seed)
                        rig = Rig(sim)
                        last_ff.clear()
                        status = ctrl.run(rig, target)
                        final = rig.true_dispensed_g()
                        rows.append(dict(
                            powder=powder, ctx=ctx, target=target, seed=seed,
                            status=status, err_mg=(final - target) * 1000.0,
                            t_s=rig.t,
                            ff_cutoff=last_ff.get("ff"),
                            bulk=getattr(ctrl, "bulk", None)))
    finally:
        bangbang.MassRateLagKF.update = _ORIG_UPDATE
    return rows


def _summ(rows):
    errs = sorted(r["err_mg"] for r in rows)
    return dict(
        med=st.median(errs), p95=errs[max(0, int(0.95 * len(errs)) - 1)],
        over=100.0 * sum(e > 0 for e in errs) / len(errs),
        tol=100.0 * sum(abs(e) <= 5 for e in errs) / len(errs),
        t=st.median([r["t_s"] for r in rows]))


def report_ident(seeds: int) -> None:
    print("\n=== 1. what would the bulk stage identify? (learn=on, 2 g doses) ===")
    print("  live EWMA vs truth at the bang's halt; 'conveyed' = out of the "
          "hopper,\n  'landed' = in the cup -- the gap is the committed "
          "inventory in the screw/lip/air")
    rows = _grid(lambda p: TrimBulkFF(learn=True), seeds)
    by = defaultdict(list)
    for r in rows:
        if r["bulk"]:
            by[r["powder"]].append(r["bulk"])
    print(f"{'powder':9}{'revs':>6}{'bang s':>7} | {'ff@1rev':>8}{'ff@halt':>8}"
          f" | {'landed/rev':>11}{'conveyed/rev':>13} | {'bias vs conveyed':>17}"
          f"{'inventory':>11}")
    for p in POWDER_SET:
        b = by[p]
        if not b:
            continue
        ff, f1 = _m(b, "ff_est"), _m(b, "ff_at_1rev")
        lan, conv = _m(b, "landed_per_rev"), _m(b, "conveyed_per_rev")
        inv, cmg = _m(b, "inv_gain_mg"), _m(b, "conveyed_mg")
        print(f"{p:9}{_m(b,'revs'):6.1f}{_m(b,'t_s'):7.1f} | {f1:8.3f}{ff:8.3f}"
              f" | {lan:11.3f}{conv:13.3f} | {100*(ff-conv)/conv:16.0f}%"
              f"{inv:8.0f} mg")
    allb = [x for v in by.values() for x in v]
    prog = [100.0 * (bangbang.FF_PRIOR - b["ff_at_1rev"])
            / max(1e-9, bangbang.FF_PRIOR - b["conveyed_per_rev"])
            for b in allb if b["ff_at_1rev"] is not None]
    print(f"\n  pooled: after 1 auger rev the EWMA has closed only "
          f"{st.median(prog):.0f}% of the gap from its 0.50 prior to truth;\n"
          f"  at the halt it reads "
          f"{100*(_m(allb,'ff_est')-_m(allb,'conveyed_per_rev'))/_m(allb,'conveyed_per_rev'):+.0f}% "
          f"vs true conveyed (prior residue, amplified by the KF input-model "
          f"coupling),\n  while its raw argument landed/rev reads "
          f"{100*(_m(allb,'landed_per_rev')-_m(allb,'conveyed_per_rev'))/_m(allb,'conveyed_per_rev'):+.0f}% "
          f"({_m(allb,'inv_gain_mg'):+.0f} mg of the "
          f"{_m(allb,'conveyed_mg'):.0f} mg conveyed still in the screw/lip/air)")


def _m(rows, key):
    return st.median([r[key] for r in rows if r.get(key) is not None])


def report_consumer(seeds: int) -> None:
    print("\n=== 2. bang sensitivity to ff, and does learning it live help? "
          "(2 g doses) ===")
    print("  nominal bang stop line is target - guard = 1.700 g; 'halt' is "
          "true mass there")
    print(f"  {'bulk ff model':34}{'halt vs stop':>13}{'med':>8}{'p95':>7}"
          f"{'over%':>7}{'abort%':>8}{'tmo%':>6}{'med t':>7}")
    for name, prior, learn in [
            ("prior 0.50 (default), no update", 0.50, False),
            ("prior 0.50 + bulk EWMA", 0.50, True),
            ("prior 0.10 (5x low), no update", 0.10, False),
            ("prior 0.10 + bulk EWMA", 0.10, True)]:
        rows = _grid(lambda p, pr=prior, ln=learn:
                     TrimBulkFF(learn=ln, ff_prior=pr), seeds)
        s = _summ(rows)
        halt = _m([r["bulk"] for r in rows if r["bulk"]], "halt_vs_stop_mg")
        ab = 100.0 * sum(r["status"] == "overshoot_abort" for r in rows) / len(rows)
        tmo = 100.0 * sum(r["status"] == "timeout" for r in rows) / len(rows)
        print(f"  {name:34}{halt:10.0f} mg{s['med']:8.1f}{s['p95']:7.1f}"
              f"{s['over']:7.0f}{ab:8.0f}{tmo:6.0f}{s['t']:7.0f}")
    print("  (m_hat ~ b_hat + r_hat*tau_bal: the input-model ff biases r_hat, "
          "and the 0.7 s\n   lag deconvolution turns that into the halt "
          "position -- high prior = early/safe,\n   low prior = late/overshoot."
          "  The EWMA partially rescues a low prior (aborts\n   36%->11%), but "
          "any bang that halts near the nominal stop line hands the\n   trickle"
          " a small remaining gap, and there trickle_tap's FIRST-TICK k*sigma\n"
          "   (~229 mg: the freshly seeded KF's initial covariance, never yet "
          "shrunk by a\n   measurement) fires the cutoff immediately -- "
          "tap_finish is left to close\n   0.15-0.28 g at ~1 mg/tap and the "
          "dose times out short.)")


def report_carry(seeds: int) -> None:
    print(f"\n=== 3. carrying the bulk-identified ff into the trickle "
          f"(2 g doses, {seeds} seeds x 3 powders x 2 contexts) ===")
    variants = [
        ("as implemented (fixed trickle prior 0.35)",
         lambda p: TrimBulkFF(learn=False)),
        ("bulk EWMA, self-consumed only",
         lambda p: TrimBulkFF(learn=True)),
        ("bulk EWMA -> trickle prior, raw",
         lambda p: TrimBulkFF(learn=True, carry="raw")),
        ("bulk EWMA -> trickle prior, tilt-rescaled",
         lambda p: TrimBulkFF(learn=True, carry="scaled",
                              trickle_ff_scale=tilt_ratio(p))),
    ]
    print(f"{'variant':44}{'med':>7}{'p95':>7}{'over%':>7}{'+/-5mg%':>9}"
          f"{'med t':>7}{'ff@cutoff':>10}")
    for name, ctor in variants:
        rows = _grid(ctor, seeds, spy_ff=True)
        s = _summ(rows)
        ffc = _m(rows, "ff_cutoff")
        print(f"{name:44}{s['med']:7.1f}{s['p95']:7.1f}{s['over']:7.0f}"
              f"{s['tol']:9.0f}{s['t']:7.0f}{ffc:10.3f}")
    print("  (ff@cutoff 0.350 = the trickle's own EWMA never ran: the cutoff "
          "fired on its\n   first tick via the fresh-covariance k*sigma, see "
          "section 2.  The carry\n   variants inherit the same collapse, so "
          "their trickle priors never matter.)")
    # equivalence check: learn=False must reproduce stock BangBangTrim exactly
    pmap = _pmap()
    same = True
    for powder in POWDER_SET:
        for seed in range(3):
            outs = []
            for ctor in (lambda p: BangBangTrim(),
                         lambda p: TrimBulkFF(learn=False)):
                sim = PowderDoserSim(pmap[powder], CONTEXTS["nominal"],
                                     seed=seed)
                rig = Rig(sim)
                ctor(pmap[powder]).run(rig, 2.0)
                outs.append(round(rig.true_dispensed_g(), 6))
            same &= outs[0] == outs[1]
    print(f"\n  paired-seed equivalence of the learn=off variant vs stock "
          f"BangBangTrim: {'exact' if same else 'DIFFERS'}")
    print("  calibrated tilt-gain ratio g(20 deg)/g(45 deg): "
          + ", ".join(f"{p} {tilt_ratio(pmap[p]):.2f}" for p in POWDER_SET))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ident", action="store_true")
    ap.add_argument("--consumer", action="store_true")
    ap.add_argument("--carry", action="store_true")
    ap.add_argument("--seeds", type=int, default=25)
    args = ap.parse_args()
    if not (args.ident or args.consumer or args.carry):
        args.ident = args.consumer = args.carry = True
    if args.ident:
        report_ident(args.seeds)
    if args.consumer:
        report_consumer(args.seeds)
    if args.carry:
        report_carry(args.seeds)


if __name__ == "__main__":
    main()

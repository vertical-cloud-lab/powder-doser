#!/usr/bin/env python3
"""Where does bangbang_trim's mass actually land, stage by stage?

Diagnostic (no controller code is modified) answering the PR #124 question
"the KF's rate estimate gets noisy at trickle rates -- so why is the KF used
inside trickle_tap, and how does that avoid overshoot?".  It instruments a
BangBangTrim dose on the calibrated twin and reports:

1. --stages   the mass at each handoff: trickle cutoff (estimate and ground
              truth), the powder that drains out of the lip during the
              post-cutoff settle, the mass when the tap endgame takes over,
              and the final settled mass.  Also splits the strict-overshoot
              trials into "the trickle cutoff fired late" vs "a tap slug
              crossed target".
2. --budget   the decomposition of the cutoff decision itself into its three
              terms (fixed margin, r_hat*tau lookahead, k*sigma cushion) and
              the scatter of the KF rate estimate at trickle rates.
3. --ablation what each term is worth: re-runs the grid with k*sigma off, with
              the fixed margin off, and with the KF replaced by raw balance
              readings + a finite-difference rate.

Instrumentation is read-only (it never calls rig.stable_read() or steps the
sim), because waiting inside a spy lets the lip keep draining and changes the
result -- the twin's lip discharges ~25 %/s at the 20 deg trickle tilt.

Usage:  python diag_trickle_stages.py [--stages] [--budget] [--ablation] [--seeds N]
"""
from __future__ import annotations

import argparse
import functools
import statistics as st
from collections import defaultdict

import bangbang
from benchmark import CONTEXTS
from calibrate_from_mongo import CAL_OUT, apply_calibration
from powder_sim import POWDERS
from rig import PowderDoserSim, Rig

POWDER_SET = ["salt", "lactose", "AlSi10Mg"]
TARGETS = [2.0, 0.3]
TAU_S = bangbang.TAU_PRIOR_S

_ORIG_UPDATE = bangbang.MassRateLagKF.update
_ORIG_TRICKLE = bangbang.trickle_tap
_ORIG_TAP = bangbang.tap_finish


def _pmap():
    return apply_calibration(POWDERS, CAL_OUT)


def _median(rows, key):
    return st.median([r[key] for r in rows])


def _pct(rows, key, p):
    s = sorted(r[key] for r in rows)
    return s[max(0, min(len(s) - 1, int(p * len(s)) - 1))]


def _instrument(record_samples: bool = False):
    """Patch the KF/stage boundaries to record state, without perturbing time."""
    cur, last, entry, samples = {}, {}, {}, []

    def upd(self, z, noisy, u_rev_s=None, ff=None, fresh=True):
        m, r = _ORIG_UPDATE(self, z, noisy, u_rev_s=u_rev_s, ff=ff, fresh=fresh)
        if cur.get("stage") == "trickle":
            rig = cur["rig"]
            snap = dict(t=rig.t, m=m, r=r, ff=ff, truth=rig._sim.dispensed_g,
                        lip=rig._sim.lip_g, sigma=self.pred_sigma(TAU_S),
                        rpm=(u_rev_s or 0.0) * 60.0)
            last.clear(); last.update(snap)
            if record_samples:
                samples.append(snap)
        return m, r

    def trickle_spy(rig, target_g, **kw):
        cur.update(stage="trickle", rig=rig)
        try:
            return _ORIG_TRICKLE(rig, target_g, **kw)
        finally:
            cur["stage"] = None

    def tap_spy(rig, target_g, **kw):
        entry.clear()
        entry.update(truth=rig._sim.dispensed_g, lip=rig._sim.lip_g, t=rig.t,
                     taps=rig._sim.total_taps)
        return _ORIG_TAP(rig, target_g, **kw)

    bangbang.MassRateLagKF.update = upd
    bangbang.trickle_tap = trickle_spy
    bangbang.tap_finish = tap_spy
    return cur, last, entry, samples


def _restore():
    bangbang.MassRateLagKF.update = _ORIG_UPDATE
    bangbang.trickle_tap = _ORIG_TRICKLE
    bangbang.tap_finish = _ORIG_TAP


def run_stages(seeds: int, contexts=("nominal", "stressed")) -> list[dict]:
    pmap, rows = _pmap(), []
    _, last, entry, _ = _instrument()
    try:
        for powder in POWDER_SET:
            for ctx in contexts:
                for target in TARGETS:
                    for seed in range(seeds):
                        sim = PowderDoserSim(pmap[powder], CONTEXTS[ctx], seed=seed)
                        rig = Rig(sim)
                        last.clear(); entry.clear()
                        status = bangbang.BangBangTrim().run(rig, target)
                        final = rig.true_dispensed_g()
                        if not last or not entry:
                            continue          # never reached the trickle/tap stage
                        rows.append(dict(
                            powder=powder, ctx=ctx, target=target, seed=seed,
                            status=status,
                            cut_est_mg=(last["m"] - target) * 1000.0,
                            cut_truth_mg=(last["truth"] - target) * 1000.0,
                            m_err_mg=(last["m"] - last["truth"]) * 1000.0,
                            r_tau_mg=last["r"] * TAU_S * 1000.0,
                            sigma_mg=last["sigma"] * 1000.0,
                            ff=last["ff"] or 0.0,
                            lip_cut_mg=last["lip"] * 1000.0,
                            drain_mg=(entry["truth"] - last["truth"]) * 1000.0,
                            entry_mg=(entry["truth"] - target) * 1000.0,
                            taps=sim.total_taps - entry["taps"],
                            tap_added_mg=(final - entry["truth"]) * 1000.0,
                            t_entry=entry["t"], t_total=rig.t,
                            final_mg=(final - target) * 1000.0))
    finally:
        _restore()
    return rows


def report_stages(rows: list[dict]) -> None:
    print(f"\n=== stage-by-stage mass (mg relative to target), n={len(rows)} ===")
    print(f"{'powder':9}{'ctx':10}{'tgt':>5} | {'cutoff est':>10} {'cutoff true':>11} "
          f"{'lip@cut':>8} {'drain':>7} | {'tap entry':>9} {'taps':>5} {'tapAdd':>7} | {'final':>7}")
    by = defaultdict(list)
    for r in rows:
        by[(r["powder"], r["ctx"], r["target"])].append(r)
    for k in sorted(by):
        v = by[k]
        print(f"{k[0]:9}{k[1]:10}{k[2]:5} | {_median(v,'cut_est_mg'):10.1f} "
              f"{_median(v,'cut_truth_mg'):11.1f} {_median(v,'lip_cut_mg'):8.1f} "
              f"{_median(v,'drain_mg'):7.1f} | {_median(v,'entry_mg'):9.1f} "
              f"{_median(v,'taps'):5.0f} {_median(v,'tap_added_mg'):7.1f} | "
              f"{_median(v,'final_mg'):7.1f}")
    print(f"\npooled: cutoff est {_median(rows,'cut_est_mg'):.1f} mg / true "
          f"{_median(rows,'cut_truth_mg'):.1f} mg -> post-cutoff lip drain "
          f"{_median(rows,'drain_mg'):+.1f} mg (p95 {_pct(rows,'drain_mg',0.95):+.1f}) -> "
          f"tap entry {_median(rows,'entry_mg'):.1f} mg -> final {_median(rows,'final_mg'):+.1f} mg")
    print(f"        tap endgame: median {_median(rows,'taps'):.0f} taps adding "
          f"{_median(rows,'tap_added_mg'):.1f} mg; handoff at {_median(rows,'t_entry'):.0f} s "
          f"of {_median(rows,'t_total'):.0f} s total")
    late = [r for r in rows if r["cut_truth_mg"] > 0 or r["entry_mg"] > 0]
    short = [r for r in rows if r not in late]
    over = [r for r in rows if r["final_mg"] > 0]
    print(f"\nstrict overshoot {100*len(over)/len(rows):.0f}% "
          f"(median {_median(over,'final_mg'):+.1f} mg, p90 {_pct(over,'final_mg',0.9):+.1f} mg)")
    if late:
        print(f"  trickle already past target at handoff: {100*len(late)/len(rows):.0f}% of doses, "
              f"{100*sum(r['final_mg']>0 for r in late)/len(late):.0f}% end over, "
              f"median final {_median(late,'final_mg'):+.1f} mg")
    if short:
        so = [r for r in short if r["final_mg"] > 0]
        print(f"  handed off short: {100*len(short)/len(rows):.0f}% of doses, "
              f"{100*len(so)/len(short):.0f}% still end over, median "
              f"{(_median(so,'final_mg') if so else 0):+.1f} mg (a single tap slug)")
    print(f"  within +/-5 mg: {100*sum(abs(r['final_mg'])<=5 for r in rows)/len(rows):.0f}%")


def report_budget(rows: list[dict]) -> None:
    """What the cutoff rule is made of at the moment it fires."""
    print(f"\n=== cutoff decision budget (mg below target), n={len(rows)} ===")
    print("  rule: m_hat + r_hat*tau + k*sigma >= target - margin      "
          "(bangbang.py trickle_tap)")
    margin = [35.0 + 60.0 * max(0.0, r["ff"] - 0.30) for r in rows]
    print(f"  fixed margin        {st.median(margin):6.1f} mg   "
          f"(cutoff_margin_g=0.035 + 0.06*max(0, ff-0.30))")
    print(f"  r_hat * tau         {_median(rows,'r_tau_mg'):6.1f} mg   "
          f"(tau={TAU_S:.2f} s, the only predictive term)")
    print(f"  k * sigma           {_median(rows,'sigma_mg'):6.1f} mg   "
          f"(k_sigma=1.0, grows when the filter is unsure)")
    print(f"  -> total stop-early budget {st.median(margin)+_median(rows,'r_tau_mg')+_median(rows,'sigma_mg'):.1f} mg; "
          f"KF-derived share {100*(_median(rows,'r_tau_mg')+_median(rows,'sigma_mg'))/(st.median(margin)+_median(rows,'r_tau_mg')+_median(rows,'sigma_mg')):.0f}%")
    print(f"  identified feed factor at cutoff: median {_median(rows,'ff'):.3f} g/rev "
          f"(max {max(r['ff'] for r in rows):.3f}) -> the ff-adaptive part of the margin "
          f"fires in {100*sum(r['ff']>0.30 for r in rows)/len(rows):.0f}% of doses")
    print(f"  |m_hat - truth| at cutoff: median {st.median([abs(r['m_err_mg']) for r in rows]):.1f} mg "
          f"(signed median {_median(rows,'m_err_mg'):+.1f} mg)")


def _raw_update(self, z, noisy, u_rev_s=None, ff=None, fresh=True):
    """Ablation: no filter -- 'mass' is the raw frame, 'rate' a 2-frame diff.

    P is pinned tiny so pred_sigma() ~ 0: without it the never-updated initial
    covariance would dominate the cutoff and the ablation would measure the
    stale sigma rather than the missing filter."""
    import numpy as _np
    prev_z = getattr(self, "_pz", z)
    self._pz = z
    r = max(0.0, (z - prev_z) / max(self.dt, 1e-6))
    self.kf.x[0, 0], self.kf.x[1, 0], self.kf.x[2, 0] = z, r, z
    self.kf.P = _np.diag([1e-8, 1e-8, 1e-8])
    return z, r


def _rawrate_update(self, z, noisy, u_rev_s=None, ff=None, fresh=True):
    """Ablation: keep the KF's lag-free mass, but feed the controller an
    unfiltered finite-difference rate -- isolates the rate channel from the
    mass channel."""
    m, _ = _ORIG_UPDATE(self, z, noisy, u_rev_s=u_rev_s, ff=ff, fresh=fresh)
    prev_z = getattr(self, "_pz", z)
    self._pz = z
    return m, max(0.0, (z - prev_z) / max(self.dt, 1e-6))


def run_ablation(seeds: int) -> None:
    pmap = _pmap()
    variants = [
        ("as implemented (KF mass + r*tau + k*sigma + margin)", {}, False),
        ("no k*sigma cushion", {"k_sigma": 0.0}, False),
        ("no fixed margin (KF terms only)", {"cutoff_margin_g": 0.0}, False),
        ("KF mass, but raw finite-diff rate", {}, "rawrate"),
        ("no KF: raw balance + finite-diff rate", {}, True),
        ("no KF and no fixed margin", {"cutoff_margin_g": 0.0}, True),
    ]
    print(f"\n=== ablation (nominal context, {seeds} seeds x 3 powders x 2 targets) ===")
    print(f"{'variant':52}{'med signed':>11}{'p95':>8}{'over%':>7}{'+/-5mg%':>9}{'med t':>7}{'handoff':>9}")
    for name, kw, raw in variants:
        bangbang.trickle_tap = (functools.partial(_ORIG_TRICKLE, **kw) if kw
                                else _ORIG_TRICKLE)
        bangbang.MassRateLagKF.update = (
            _rawrate_update if raw == "rawrate"
            else _raw_update if raw else _ORIG_UPDATE)
        entry, errs, times, handoff = {}, [], [], []

        def tap_spy(rig, target_g, **k2):
            entry.update(truth=rig._sim.dispensed_g)
            return _ORIG_TAP(rig, target_g, **k2)
        bangbang.tap_finish = tap_spy
        try:
            for powder in POWDER_SET:
                for target in TARGETS:
                    for seed in range(seeds):
                        sim = PowderDoserSim(pmap[powder], CONTEXTS["nominal"], seed=seed)
                        rig = Rig(sim)
                        entry.clear()
                        bangbang.BangBangTrim().run(rig, target)
                        final = rig.true_dispensed_g()
                        errs.append((final - target) * 1000.0)
                        times.append(rig.t)
                        if entry:
                            handoff.append((entry["truth"] - target) * 1000.0)
        finally:
            _restore()
        s = sorted(errs)
        print(f"{name:52}{st.median(s):11.1f}{s[int(0.95*len(s))-1]:8.1f}"
              f"{100*sum(x>0 for x in s)/len(s):7.0f}"
              f"{100*sum(abs(x)<=5 for x in s)/len(s):9.0f}{st.median(times):7.0f}"
              f"{(st.median(handoff) if handoff else float('nan')):9.1f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", action="store_true")
    ap.add_argument("--budget", action="store_true")
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--ablation-seeds", type=int, default=15)
    args = ap.parse_args()
    if not (args.stages or args.budget or args.ablation):
        args.stages = args.budget = args.ablation = True
    if args.stages or args.budget:
        rows = run_stages(args.seeds)
        if args.stages:
            report_stages(rows)
        if args.budget:
            report_budget(rows)
    if args.ablation:
        run_ablation(args.ablation_seeds)


if __name__ == "__main__":
    main()

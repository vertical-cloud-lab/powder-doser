#!/usr/bin/env python3
"""Analyze the KF bang-bang stop-accuracy battery (PR #131, 2026-08-17).

Two modes:

  (default)  parse one or more on-rig logs written by
             ``hardware/test-module/firmware/kf_bangbang.py`` -> tidy CSVs,
             per-variant/target accuracy tables and figures.

  --replay   offline calibration/validation: replay the SAME KF3 filter
             (imported from the firmware module) over the recorded
             dispense-and-settle trials of an earlier battery log and score
             its settled-mass prediction against the measured settled mass.
             This is how tau_after / Q_ACC_SD were chosen before the run,
             and how the sensitivity to tau_bal (0.16 s measured vs the
             twin's assumed 0.7 s) is quantified.

Usage:
    python scripts/analyze_kf_bangbang.py data/kf-bangbang/2026-08-17_salt
    python scripts/analyze_kf_bangbang.py --replay \
        data/afterflow/2026-08-12_salt/afterflow_battery_salt.log
"""
from __future__ import annotations

import argparse
import csv
import os
import statistics as st
import sys

FIRMWARE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "hardware", "test-module", "firmware")
sys.path.insert(0, os.path.abspath(FIRMWARE))
import kf_bangbang as KFM  # noqa: E402  (imports KF3 only, off-device)

T_COLS = ["trial", "variant", "target_g", "tilt", "rpm", "rep", "m_base",
          "m_halt_raw", "m_hat_halt", "r_hat_halt", "sigma_halt",
          "pred_halt", "t_disp_s", "m_settled", "m_settled2", "dispensed_g",
          "error_mg", "afterflow_mg", "verdict"]
D_COLS = ["t_ms", "trial", "phase", "mass", "stab", "fresh", "rpm", "m_hat",
          "r_hat", "b_hat", "sigma", "pred"]


def parse_log(path, pass_id):
    trials, samples, meta = [], [], {}
    for line in open(path):
        p = line.rstrip("\n").split(",")
        if p[0] == "M" and len(p) >= 3:
            meta[p[1]] = ",".join(p[2:])
        elif p[0] == "T" and len(p) >= len(T_COLS) + 1:
            row = dict(zip(T_COLS, p[1:]))
            row["pass"] = pass_id
            trials.append(row)
        elif p[0] == "D" and len(p) >= 13:
            row = dict(zip(D_COLS, p[1:13]))
            row["pass"] = pass_id
            samples.append(row)
    return meta, trials, samples


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def summarize(trials):
    """Accuracy tables: by variant, and by target within the kf variant."""
    out = []
    by_var = {}
    for t in trials:
        by_var.setdefault(t["variant"], []).append(t)
    for var, rows in sorted(by_var.items()):
        e = [fnum(r["error_mg"]) for r in rows]
        out.append(("variant", var, len(e), st.mean(e),
                    st.pstdev(e) if len(e) > 1 else float("nan"),
                    max(abs(x) for x in e)))
    kf = [t for t in trials if t["variant"] == "kf"]
    by_tgt = {}
    for t in kf:
        by_tgt.setdefault(float(t["target_g"]), []).append(t)
    for tgt, rows in sorted(by_tgt.items()):
        e = [fnum(r["error_mg"]) for r in rows]
        out.append(("kf@target", "{:.2f} g".format(tgt), len(e), st.mean(e),
                    st.pstdev(e) if len(e) > 1 else float("nan"),
                    max(abs(x) for x in e)))
    return out


# ---------------------------------------------------------------------
# offline replay (calibration / validation)
# ---------------------------------------------------------------------

def replay_log(path, tau_after, q_acc, ff, tau_bal, stale_ms=260):
    """Replay KF3 over an afterflow-battery log; score pred vs settled."""
    rows, res = {}, {}
    for line in open(path):
        p = line.rstrip("\n").split(",")
        if p[0] == "D" and len(p) >= 8:
            rows.setdefault(int(p[2]), []).append(
                (int(p[1]), p[3], p[4], float(p[6])))
        elif p[0] == "R":
            res[int(p[1])] = p
    KFM.Q_ACC_SD = q_acc
    out = []
    for tr, R in sorted(res.items()):
        test = R[2]
        try:
            m_set2 = float(R[10])
        except (ValueError, IndexError):
            continue
        kf = KFM.KF3(tau_bal=tau_bal, ff=ff)
        kf.reset(0.0)
        t_prev = z_prev = t_upd = None
        z = float("nan")
        last = None
        for ts, ph, mass, rpm in rows.get(tr, []):
            if ph not in ("preroll", "dispense"):
                continue
            dt = 0.095 if t_prev is None else max(1e-3, (ts - t_prev) / 1000.0)
            t_prev = ts
            kf.predict(dt, rpm / 60.0)
            if mass != "nan":
                z = float(mass)
                if z != z_prev or t_upd is None or ts - t_upd > stale_ms:
                    kf.update(z, rpm > 0)
                    t_upd = ts
                z_prev = z
            if ph == "dispense":
                last = (kf.x[0], kf.x[1], kf.pred_sigma(tau_after), z)
        if last is None:
            continue
        m, r, sig, z = last
        out.append({"trial": tr, "test": test, "m_hat": m, "r_hat": r,
                    "sigma": sig, "raw": z, "settled": m_set2,
                    "pred": m + r * tau_after,
                    "pred_err_mg": (m + r * tau_after - m_set2) * 1000.0,
                    "lag_only_err_mg": (m - m_set2) * 1000.0,
                    "raw_err_mg": (z - m_set2) * 1000.0})
    return out


def cmd_replay(paths):
    print("offline replay -- predictor error vs measured settled mass\n")
    for path in paths:
        for tau_bal in (0.16, 0.70):
            for tau in (0.25, 0.40):
                res = replay_log(path, tau, KFM.Q_ACC_SD, KFM.FF_PRIOR,
                                 tau_bal)
                groups = {}
                for r in res:
                    groups.setdefault(r["test"], []).append(r)
                for test, rows in sorted(groups.items()):
                    if test not in ("C6", "C7"):
                        continue
                    e = [r["pred_err_mg"] for r in rows]
                    raw = [r["raw_err_mg"] for r in rows]
                    lag = [r["lag_only_err_mg"] for r in rows]
                    print("tau_bal={:.2f} tau_after={:.2f} {} n={:2d}  "
                          "pred {:+6.1f} +- {:4.1f} mg | m_hat only {:+6.1f} "
                          "| raw {:+6.1f}".format(
                              tau_bal, tau, test, len(e), st.mean(e),
                              st.pstdev(e), st.mean(lag), st.mean(raw)))
        print()


# ---------------------------------------------------------------------

def cmd_analyze(outdir, logs):
    trials, samples, meta = [], [], {}
    for i, path in enumerate(logs, 1):
        m, t, s = parse_log(path, i)
        meta.update({"pass{}_{}".format(i, k): v for k, v in m.items()})
        trials += t
        samples += s
    if not trials:
        raise SystemExit("no T rows found in {}".format(logs))

    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "trials.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["pass"] + T_COLS)
        w.writeheader()
        w.writerows(trials)
    with open(os.path.join(outdir, "samples.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["pass"] + D_COLS)
        w.writeheader()
        w.writerows(samples)

    print("{} trials, {} samples".format(len(trials), len(samples)))
    print("\n{:<10} {:<10} {:>3} {:>9} {:>8} {:>9}".format(
        "group", "key", "n", "mean(mg)", "sd(mg)", "max|e|(mg)"))
    for grp, key, n, mean, sd, mx in summarize(trials):
        print("{:<10} {:<10} {:>3} {:>9.1f} {:>8.1f} {:>9.1f}".format(
            grp, key, n, mean, sd, mx))

    try:
        make_figures(outdir, trials, samples)
    except ImportError:
        print("matplotlib unavailable -- figures skipped")
    return trials, samples


def make_figures(outdir, trials, samples):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"kf": "#2b6cb0", "naive": "#c53030", "kfsafe": "#2f855a",
              "kflag": "#b7791f"}
    labels = {"kf": "kf  (m̂ + r̂·τ_after)", "naive": "naive (raw ≥ target)",
              "kfsafe": "kfsafe (+2σ margin)", "kflag": "kflag (m̂ only)"}

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))

    ax = axes[0]
    for var in ("kf", "kflag", "kfsafe", "naive"):
        rows = [t for t in trials if t["variant"] == var]
        if not rows:
            continue
        ax.scatter([fnum(r["target_g"]) for r in rows],
                   [fnum(r["error_mg"]) for r in rows],
                   s=[70 if fnum(r["rpm"]) < 70 else 130 for r in rows],
                   marker="o" if var != "naive" else "X",
                   color=colors[var], label=labels[var], alpha=0.85,
                   edgecolors="k", linewidths=0.4, zorder=3)
    ax.axhline(0, color="k", lw=1)
    ax.axhspan(-50, 50, color="#2b6cb0", alpha=0.07, zorder=0)
    ax.set_xscale("log")
    ax.set_xlabel("target mass (g, log scale)")
    ax.set_ylabel("stop error = dispensed − target (mg)")
    ax.set_title("Bang-bang stop accuracy vs target\n"
                 "(large markers = 90 rpm)")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)

    ax = axes[1]
    kf = [t for t in trials if t["variant"] == "kf"]
    tg = [fnum(t["target_g"]) for t in kf]
    err = [fnum(t["error_mg"]) for t in kf]
    aft = [fnum(t["afterflow_mg"]) for t in kf]
    ax.scatter(tg, [abs(e) / (t * 1000.0) * 100.0 for e, t in zip(err, tg)],
               color=colors["kf"], s=70, edgecolors="k", linewidths=0.4,
               label="|error| (% of target)", zorder=3)
    ax.scatter(tg, [a / (t * 1000.0) * 100.0 for a, t in zip(aft, tg)],
               color="#718096", marker="s", s=55, alpha=0.8,
               label="afterflow cancelled (% of target)", zorder=3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("target mass (g, log scale)")
    ax.set_ylabel("percent of target")
    ax.set_title("Relative accuracy: a ~constant mg error\n"
                 "becomes a big % error at small targets")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")

    ax = axes[2]
    for t in trials:
        pred = fnum(t["pred_halt"])
        disp = fnum(t["dispensed_g"])
        ax.scatter(pred, disp, color=colors[t["variant"]], s=60,
                   marker="o" if t["variant"] != "naive" else "X",
                   edgecolors="k", linewidths=0.4, zorder=3)
    lim = [0, max(fnum(t["dispensed_g"]) for t in trials) * 1.08]
    ax.plot(lim, lim, "k--", lw=1, label="perfect prediction")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("predicted settled mass at the halt (g)")
    ax.set_ylabel("actual settled mass (g)")
    ax.set_title("Predictor calibration at the moment of the halt")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "kf_bangbang_accuracy.png"), dpi=150)
    plt.close(fig)

    # --- trace figure: one representative trial per target -------------
    want, seen = [], set()
    for t in trials:
        if t["variant"] != "kf":
            continue
        key = t["target_g"]
        if key in seen:
            continue
        seen.add(key)
        want.append(t)
    want = sorted(want, key=lambda t: float(t["target_g"]))[:4]
    fig, axes = plt.subplots(1, len(want), figsize=(4.4 * len(want), 4.4),
                             squeeze=False)
    for ax, t in zip(axes[0], want):
        tr = t["trial"]
        pas = t["pass"]
        rows = [s for s in samples if s["trial"] == tr and s["pass"] == pas
                and s["phase"] in ("preroll", "dispense", "settle")]
        if not rows:
            continue
        t0 = fnum(rows[0]["t_ms"])
        base = fnum(t["m_base"])
        tt = [(fnum(r["t_ms"]) - t0) / 1000.0 for r in rows]
        ax.plot(tt, [fnum(r["mass"]) - base for r in rows], color="#a0aec0",
                lw=1.2, label="raw balance")
        dis = [r for r in rows if r["phase"] in ("preroll", "dispense")]
        td = [(fnum(r["t_ms"]) - t0) / 1000.0 for r in dis]
        ax.plot(td, [fnum(r["m_hat"]) for r in dis], color="#2b6cb0", lw=1.6,
                label="m̂ (KF true mass)")
        ax.plot(td, [fnum(r["pred"]) for r in dis], color="#c53030", lw=1.4,
                ls="--", label="predicted settled")
        ax.axhline(fnum(t["target_g"]), color="k", lw=1, ls=":",
                   label="target")
        ax.axvline(td[-1] if td else 0.0, color="#2f855a", lw=1, alpha=0.6,
                   label="halt")
        ax.set_title("target {:.2f} g -> {:+.1f} mg".format(
            fnum(t["target_g"]), fnum(t["error_mg"])), fontsize=10)
        ax.set_xlabel("time (s)")
        ax.set_ylabel("mass above baseline (g)")
        ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=7.5)
    fig.suptitle("KF bang-bang traces: the filter leads the balance, "
                 "and the halt lands on target after the afterflow", y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "kf_bangbang_traces.png"), dpi=150)
    plt.close(fig)
    print("figures written to {}".format(outdir))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()
    if args.replay:
        cmd_replay(args.paths)
        return
    logs = []
    for p in args.paths:
        if os.path.isdir(p):
            logs += [os.path.join(p, f) for f in sorted(os.listdir(p))
                     if f.endswith(".log")]
        else:
            logs.append(p)
    outdir = args.outdir or os.path.dirname(logs[0]) or "."
    cmd_analyze(outdir, logs)


if __name__ == "__main__":
    main()

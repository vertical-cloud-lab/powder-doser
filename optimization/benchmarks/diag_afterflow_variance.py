"""Afterflow-model adequacy + weigh-error decomposition (PR #124, 2026-09-07).

Answers two questions raised by @williamulbz on the 2026-09-03 comment:

1. "We previously ran tests on afterflow as a function of flow rate at the
   cutoff — are you stating that isn't adequately predicting afterflow?"
   -> Quantifies the difference between the C7 fit on rpm MEANS (R^2 ~ 0.9,
   what made the law look adequate) and the same fit per TRIAL (R^2 ~ 0.18,
   what a per-dose controller actually gets), then shows the closed-loop
   2026-08-17 doses land at the same R^2 with a ~32 mg residual, and that
   the fitted "tau" is not stable across sessions/blocks.

2. "The doser and the scale are not physically attached... [vibration]
   doesn't seem to be a real issue."
   -> Confirms the balance itself is quiet (re-weigh repeatability ~0.2-0.5
   mg, at-rest frame noise ~0.08 mg) and shows the +/-30 mg "swings" in the
   low-rpm quantum block carry the exact fingerprint of PER-WEIGH reading
   error (lag-1 autocorrelation ~ -0.5; errors cancel in sums), not real
   mass movement and not vibration.  Decomposes the reported per-increment
   scatter into weigh error vs true slug scatter.

Data: real bench captures from PR #131's data tree, pinned at commit
8c9d8a1 and fetched via `gh api` into a /tmp cache (nothing is written to
the repo besides results/).  Run:  python diag_afterflow_variance.py
Outputs: results/diag_afterflow_variance.txt, results/fig_afterflow_variance.png
"""

import io
import os
import subprocess
import sys

import numpy as np
import pandas as pd

DATA_SHA = "8c9d8a1"
REPO = "vertical-cloud-lab/powder-doser"
CACHE = f"/tmp/pdoser_data_{DATA_SHA}"
FILES = [
    "data/kf-bangbang/2026-08-17_salt/trials.csv",
    "data/kf-bangbang/2026-08-17_salt/samples.csv",
    "data/afterflow/2026-08-12_salt/afterflow_trials.csv",
    "data/afterflow-phase/2026-08-13_salt/afterflow_phase_A.csv",
    "data/lowrpm-quantum/2026-08-17_salt/quantum.csv",
    "data/lowrpm-quantum/2026-08-17_salt/stop_trials.csv",
]
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def fetch(path):
    dest = os.path.join(CACHE, path.replace("/", "_"))
    if not os.path.exists(dest):
        os.makedirs(CACHE, exist_ok=True)
        raw = subprocess.run(
            ["gh", "api", "-H", "Accept: application/vnd.github.raw",
             f"repos/{REPO}/contents/{path}?ref={DATA_SHA}"],
            capture_output=True, check=True).stdout
        with open(dest, "wb") as f:
            f.write(raw)
    return pd.read_csv(dest)


def ols(y, X):
    """OLS with intercept; returns (coefs, R^2, residual rmse, n)."""
    y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(y))] + [np.asarray(x, float) for x in X])
    m = np.all(np.isfinite(X), axis=1) & np.isfinite(y)
    X, y = X[m], y[m]
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - np.sum(res ** 2) / ss_tot
    rmse = np.sqrt(np.sum(res ** 2) / max(len(y) - X.shape[1], 1))
    return b, r2, rmse, len(y)


def main():
    out = io.StringIO()

    def p(*a):
        print(*a)
        print(*a, file=out)

    tr = fetch(FILES[0])
    smp = fetch(FILES[1])
    af = fetch(FILES[2])
    pha = fetch(FILES[3])
    q = fetch(FILES[4])
    stop = fetch(FILES[5])

    # ---------------- Q1: what does the flow law actually explain? --------
    p("=" * 74)
    p("Q1.  AFTERFLOW ~ FLOW: mean law vs per-dose prediction")
    p("=" * 74)
    ok = af[af.verdict == "ok"]
    c7 = ok[ok.test == "C7"]
    gm = c7.groupby("rpm").agg(flow=("flow_slope_g_per_s", "mean"),
                               afm=("afterflow_mg", "mean"))
    bm, r2m, _, _ = ols(gm.afm, [gm.flow])
    bt, r2t, rmset, nt = ols(c7.afterflow_mg, [c7.flow_slope_g_per_s])
    p(f"C7 sweep (08-12, rpm 15..75, tilt 55, halt 0.5 g):")
    p(f"  fit on the 4 rpm MEANS : AF = {bm[0]:5.1f} mg + {bm[1]/1000:.3f} s*flow   R^2 = {r2m:.2f}")
    p(f"  fit per TRIAL (n={nt})  : AF = {bt[0]:5.1f} mg + {bt[1]/1000:.3f} s*flow   R^2 = {r2t:.2f}  resid rmse {rmset:.1f} mg")
    p(f"  within-rpm afterflow sd: " + ", ".join(
        f"{r} rpm: {s:.1f}" for r, s in c7.groupby("rpm").afterflow_mg.std().items()) + " mg")

    tau = ok.tau_s.dropna()
    ball, r2all, rmsall, nall = ols(ok[ok["mode"].isin(["rot", "auger"])].afterflow_mg,
                                    [ok[ok["mode"].isin(["rot", "auger"])].flow_slope_g_per_s])
    p(f"\nWhole 08-12 battery, auger trials pooled (C6+C7+C8, n={nall}):")
    p(f"  AF = {ball[0]:.1f} mg + {ball[1]/1000:.3f} s*flow   R^2 = {r2all:.2f}  resid rmse {rmsall:.1f} mg")
    p(f"  NOTE the slope: {ball[1]/1000:.2f} s pooled vs {bt[1]/1000:.2f} s for C7 alone -- the 'constant'")
    p(f"  depends on which flow/fill regime you probe.")
    p(f"  implied per-trial tau (n={len(tau)}): mean {tau.mean():.2f} s, CV {tau.std()/tau.mean()*100:.0f}%, "
      f"range {tau.min():.2f}..{tau.max():.2f} s")

    # low-rpm matched-fill battery (08-17): the trim-rate end of the law
    st = stop[stop.verdict == "ok"]
    for tilt, g in st.groupby("tilt"):
        b, r2, rm, n = ols(g.afterflow_mg, [g.flow_at_halt_g_per_s])
        p(f"low-rpm matched-fill battery 08-17, tilt {tilt:g} (n={n}, flows "
          f"{g.flow_at_halt_g_per_s.min():.3f}..{g.flow_at_halt_g_per_s.max():.3f} g/s): "
          f"AF0 = {b[0]:.1f} mg, tau = {b[1]/1000:+.2f} s, R^2 = {r2:.2f}")

    # closed-loop doses (08-17): the dataset the controller actually lives in
    kf = tr[(tr.variant == "kf") & (tr.rpm == 55)].copy()
    kf["raw_disp_halt"] = kf.m_halt_raw - kf.m_base
    kf["A"] = kf.afterflow_mg
    kf["anticipated"] = (kf.m_hat_halt - kf.raw_disp_halt + kf.pred_halt - kf.m_hat_halt) * 1000
    kf["trigger"] = (kf.pred_halt - kf.target_g) * 1000
    kf["resid"] = (kf.dispensed_g - kf.pred_halt) * 1000
    p(f"\nClosed-loop kf doses (08-17, n={len(kf)}, all at 55 rpm / 55 deg):")
    p(f"  post-halt arrival A: mean {kf.A.mean():.1f}  sd {kf.A.std():.1f}  range {kf.A.min():.0f}..{kf.A.max():.0f} mg")
    p(f"  KF anticipation    : mean {kf.anticipated.mean():.1f}  (mean bias only {kf.A.mean()-kf.anticipated.mean():+.1f} mg -> the law is right ON AVERAGE)")
    for name, X in [("A ~ r_hat (the current rule)", [kf.r_hat_halt]),
                    ("A ~ r_hat + 1/t_run", [kf.r_hat_halt, 1 / kf.t_disp_s]),
                    ("A ~ 1/t_run alone", [1 / kf.t_disp_s])]:
        b, r2, rm, n = ols(kf.A, X)
        p(f"  {name:29s}: R^2 = {r2:.2f}  resid rmse {rm:.1f} mg")
    pred_c7 = bt[0] + bt[1] * kf.r_hat_halt
    res = kf.A - pred_c7
    p(f"  C7 line applied out-of-sample: bias {res.mean():+.1f} mg, sd {res.std():.1f} mg")
    p(f"  error decomposition: total sd {kf.error_mg.std():.1f} | trigger sd {kf.trigger.std():.1f} | "
      f"prediction-residual sd {kf.resid.std():.1f} (corr {np.corrcoef(kf.trigger, kf.resid)[0,1]:.2f})")
    p(f"  counterfactuals: perfect afterflow model -> error sd {kf.trigger.std():.1f} mg; "
      f"perfect trigger -> {kf.resid.std():.1f} mg")

    # ---------------- Q2: measurement vs material ------------------------
    p("")
    p("=" * 74)
    p("Q2.  THE BALANCE IS QUIET; THE QUANTUM 'SWINGS' ARE PER-WEIGH ERROR")
    p("=" * 74)
    noi = [np.std(np.diff(g.mass.values) * 1000, ddof=1)
           for _, g in smp[smp.phase == "noise"].groupby(["pass", "trial"]) if len(g) > 5]
    p(f"at-rest frame-to-frame noise (08-17 session): " +
      ", ".join(f"{x:.2f}" for x in noi) + " mg sd")
    for pas, g in tr.groupby("pass"):
        d = (g.m_base.values[1:] - g.m_settled2.values[:-1]) * 1000
        d = d[np.abs(d) < 400]  # exclude refill/tare discontinuities
        p(f"re-weigh repeatability, pass {pas} (next trial's base vs prev settled, minutes apart): "
          f"sd {d.std(ddof=1):.2f} mg, max |.| {np.abs(d).max():.1f} mg (n={len(d)})")
    rr = [np.std(np.diff(g.mass.values) * 1000, ddof=1)
          for _, g in smp[smp.rpm > 0].groupby(["pass", "trial"]) if len(g) > 6]
    p(f"during dispensing: median frame-to-frame sd {np.median(rr):.1f} mg "
      f"({len(rr)} trials) -- the channel the blocked-outlet null test splits")

    p("\nlow-rpm quantum block (20 deg steps @ 10 rpm, weighed at rest, S-flagged):")
    p(f"{'tilt':>5} {'yield sd':>9} {'lag-1 acf':>10} {'sum-of-18 sd':>13} {'per-weigh err':>14} {'true slug sd':>13}")
    for tilt, g in q.groupby("tilt"):
        ys = [gg.sort_values("incr").yield_mg.values for _, gg in g.groupby("scan")]
        v = np.mean([np.var(y, ddof=1) for y in ys])
        r1 = np.mean([np.corrcoef(y[:-1], y[1:])[0, 1] for y in ys])
        ve = max(-r1 * v, 0.0)
        vt = max(v - 2 * ve, 0.0)
        ssum = np.std([y.sum() for y in ys], ddof=1) if len(ys) > 1 else float("nan")
        p(f"{tilt:>5g} {np.sqrt(v):>8.1f}m {r1:>+10.2f} {ssum:>12.1f}m {np.sqrt(ve):>13.1f}m {np.sqrt(vt):>12.1f}m")
    p("(pure per-weigh reading error predicts lag-1 acf = -0.50 and cancellation in sums;")
    p(" independent real slugs predict acf = 0 and sums growing as sqrt(k).)")

    y = pha.sort_values(["trial", "scan", "incr"]).yield_g.values * 1000
    v = np.var(y, ddof=1)
    r1 = np.corrcoef(y[:-1], y[1:])[0, 1]
    ve = max(-r1 * v, 0.0)
    p(f"\n08-13 phase-A 45-deg increments (n={len(y)}): yield sd {np.sqrt(v):.1f} mg, lag-1 acf {r1:+.2f}")
    p(f"  -> per-weigh error ~{np.sqrt(ve):.1f} mg, TRUE slug sd ~{np.sqrt(max(v-2*ve,0)):.1f} mg per 45 deg")
    p("  (the '15.9 mg salt quantum' quoted since 08-17 was ~2/3 weigh error.)")

    # ---------------- figure ---------------------------------------------
    make_figure(ok, c7, bt, st, kf, q)
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "diag_afterflow_variance.txt"), "w") as f:
        f.write(out.getvalue())
    p(f"\nwrote results/diag_afterflow_variance.txt and results/fig_afterflow_variance.png")


def make_figure(ok, c7, bt, st, kf, q):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e7e5e1"
    BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#a3a19b"
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.6, 5.0), dpi=150)
    fig.patch.set_facecolor(SURF)

    for a in (ax, bx):
        a.set_facecolor(SURF)
        a.grid(True, color=GRID, lw=0.8)
        a.set_axisbelow(True)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            a.spines[s].set_color(INK2)
        a.tick_params(colors=INK2, labelsize=9)

    # Panel A: every afterflow measurement vs flow at halt
    c6 = ok[(ok.test == "C6") & ok.flow_slope_g_per_s.notna()]
    ax.scatter(c6.flow_slope_g_per_s, c6.afterflow_mg, s=52, facecolor="none",
               edgecolor=GRAY, lw=1.4, label="08-12 C6 (higher fill)", zorder=3)
    ax.scatter(c7.flow_slope_g_per_s, c7.afterflow_mg, s=54, color=BLUE,
               edgecolor=SURF, lw=1.0, label="08-12 C7 speed sweep", zorder=4)
    ax.scatter(st.flow_at_halt_g_per_s, st.afterflow_mg, s=56, marker="D", color=AQUA,
               edgecolor=SURF, lw=1.0, label="08-17 low-rpm battery (matched fill)", zorder=4)
    ax.scatter(kf.r_hat_halt, kf.A, s=64, marker="^", color=ORANGE,
               edgecolor=SURF, lw=1.0, label="08-17 closed-loop KF doses", zorder=5)
    xs = np.linspace(0.0, 0.235, 50)
    ax.plot(xs, bt[0] + bt[1] * xs, color=BLUE, lw=2, alpha=0.85, zorder=2)
    ax.plot(xs[xs > c7.flow_slope_g_per_s.max()],
            bt[0] + bt[1] * xs[xs > c7.flow_slope_g_per_s.max()],
            color=SURF, lw=2.6, ls=(0, (2, 3)), zorder=2)  # dash the extrapolated part
    ax.annotate("C7 fit: 16 mg + 0.28 s x flow\nR$^2$ = 0.90 on rpm means, 0.18 per trial",
                xy=(0.124, 4), color=INK2, fontsize=8.6, ha="left")
    ax.annotate("closed-loop doses: 30..159 mg\nafter the halt at one condition",
                xy=(0.219, 156), xytext=(0.128, 132), color=INK2, fontsize=8.6,
                ha="left", arrowprops=dict(arrowstyle="-", color=INK2, lw=0.9,
                                           shrinkA=2, shrinkB=6))
    ax.set_xlabel("flow at halt (g/s)", color=INK, fontsize=10)
    ax.set_ylabel("post-halt arrival / afterflow (mg)", color=INK, fontsize=10)
    ax.set_title("The flow law is a mean law: per-dose scatter dominates",
                 color=INK, fontsize=11, loc="left", pad=10)
    leg = ax.legend(loc="upper left", fontsize=8.4, frameon=False, labelcolor=INK2)
    ax.set_xlim(-0.005, 0.235)

    # Panel B: consecutive quantum yields anticorrelate at -0.5
    y0, y1, cols = [], [], []
    for (_, _), g in q.groupby(["tilt", "scan"]):
        yy = g.sort_values("incr").yield_mg.values
        y0.extend(yy[:-1])
        y1.extend(yy[1:])
    y0, y1 = np.asarray(y0), np.asarray(y1)
    bx.axhline(0, color=GRID, lw=1.0)
    bx.axvline(0, color=GRID, lw=1.0)
    bx.scatter(y0, y1, s=42, color=BLUE, edgecolor=SURF, lw=0.8, alpha=0.9, zorder=4)
    bfit = np.polyfit(y0, y1, 1)
    xs = np.linspace(y0.min(), y0.max(), 10)
    bx.plot(xs, np.polyval(bfit, xs), color=INK2, lw=1.6, ls="--", zorder=3)
    r1 = np.corrcoef(y0, y1)[0, 1]
    bx.annotate(f"lag-1 correlation = {r1:+.2f}\n"
                "pure weigh error predicts -0.50\nreal independent slugs predict 0",
                xy=(0.03, 0.03), xycoords="axes fraction", color=INK2, fontsize=8.8)
    bx.set_xlabel("increment $i$ apparent yield (mg)", color=INK, fontsize=10)
    bx.set_ylabel("increment $i{+}1$ apparent yield (mg)", color=INK, fontsize=10)
    bx.set_title("Quantum-block swings sit in the weighs, not the powder",
                 color=INK, fontsize=11, loc="left", pad=10)

    fig.suptitle("")
    fig.tight_layout()
    os.makedirs(RESULTS, exist_ok=True)
    fig.savefig(os.path.join(RESULTS, "fig_afterflow_variance.png"),
                facecolor=SURF, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())

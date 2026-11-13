#!/usr/bin/env python3
"""Follow-up to run 33: would optimizing for consistent doses help the predictor?

William asked on #196 (6 Nov 2026) whether the BO should look for settings that dose consistently and
predictably, rather than fast and accurately, and whether that would help a simulator or predictor. This
script measures, on data that already exist:

  1. how much repeated doses at one set of controller settings vary (the salt BO campaign), and whether
     the campaign's single-dose objective was fooled by a lucky dose;
  2. how much of the inverse and forward models' error (run 33) comes from dosing scatter, compared with
     the handbook labels and with session-to-session drift (simulation-extrapolation, SIMEX);
  3. whether the scatter between revolutions carries information about the powder;
  4. the 1-factor model's hidden ("latent") score for each powder, to illustrate what one is.

Inputs (pinned copies, see data/SOURCES.md):
  data/salt_campaign_records.jsonl   the 60 doses of campaign salt-20260929T014732Z (#166, #179 branch)
  data/trials.csv                    Sam's per-revolution battery data (#116)
  ../heldout-powders/data/           per-powder rates and #163 handbook properties
usage: python consistency.py      (about 20 s; numpy, scipy, scikit-learn, matplotlib)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ml_property_dose as M  # noqa: E402  (run 33: data loading, LOPO helpers, the joint factor model)

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RNG = np.random.default_rng(0)
NDRAW = 400
TOL_MG = 3.0

# palette (dataviz reference instance, light mode): first three categorical slots + text inks
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"


# ------------------------------------------------------------------------------ 1. salt campaign repeats

GROUPS = [
    ("hand-tuned", "hand-tuned\n(baseline)", lambda l: l.startswith(("baseline-", "rebaseline-")), None),
    ("centre", "centre point", lambda l: l.startswith(("center-", "recenter-")), None),
    ("corner-09", "corner-09", lambda l: l == "corner-09" or l.startswith("val-corner-09-"), "corner-09"),
    ("bo-005", "bo-005\n(recommended)", lambda l: l == "bo-005" or l.startswith("val-bo-005-"), "bo-005"),
]


def campaign():
    recs = [json.loads(s) for s in (HERE / "data" / "salt_campaign_records.jsonl").read_text().splitlines() if s]
    out = {}
    for key, _, match, first_label in GROUPS:
        g = [r for r in recs if match(r["label"])]
        t = np.array([r["summary"]["t_total_s"] for r in g])
        e = np.array([r["summary"]["error_mg"] for r in g])
        st = [r["summary"]["status"] for r in g]
        first = g[0]
        q1, q3 = np.percentile(t, [25, 75])
        out[key] = {
            "n": len(g), "labels": [r["label"] for r in g], "t_s": t.round(1).tolist(), "error_mg": e.round(1).tolist(),
            "status": st, "first_label": first["label"], "first_t_s": float(t[0]), "first_abs_error_mg": float(abs(e[0])),
            "median_t_s": float(np.median(t)), "min_t_s": float(t.min()), "max_t_s": float(t.max()),
            "iqr_t_s": [float(q1), float(q3)], "max_over_min_t": float(t.max() / t.min()),
            "cv_t_pct": float(t.std(ddof=1) / t.mean() * 100),
            "median_abs_error_mg": float(np.median(np.abs(e))), "max_abs_error_mg": float(np.max(np.abs(e))),
            "p_within_tol": float(np.mean((np.abs(e) <= TOL_MG) & np.array([s == "ok" for s in st]))),
            "n_ok": int(sum(s == "ok" for s in st)),
            "taps_range": [int(min(r["summary"]["taps"] for r in g)), int(max(r["summary"]["taps"] for r in g))],
        }
    # what the single-dose objective saw: every non-validation dose, ranked by the knee of (t, |e|)
    single = [r for r in recs if not r["label"].startswith("val-")]
    ok = [r for r in single if r["summary"]["status"] == "ok" and r["summary"]["abs_error_mg"] <= TOL_MG]
    fastest = min(ok, key=lambda r: r["summary"]["t_total_s"])
    out["fastest_single_dose_within_tol"] = {"label": fastest["label"], "t_s": fastest["summary"]["t_total_s"],
                                             "abs_error_mg": fastest["summary"]["abs_error_mg"]}
    return out


# ----------------------------------------------------------------- 2. error budget and SIMEX (run 33 lines)

def per_rev(rows):
    """Per-powder revolution masses (mg) at each protocol C tilt, from trials.csv."""
    tr = M.rcsv(HERE / "data" / "trials.csv")
    out = {}
    for r in rows:
        d = {}
        for servo, key in ((0.0, "0"), (45.0, "22.5"), (90.0, "45")):
            d[key] = np.array([M.fnum(t["delta_g"]) * 1000 for t in tr
                               if t["run_id"] == r["run_id"] and t["block"] == "C" and M.fnum(t["tilt_deg"]) == servo])
        out[r["powder_id"]] = d
    return out


def lopo_rmse_line(x, y):
    X = x.reshape(-1, 1)
    mu, _, _ = M.lopo(X, y, M.make_line(0))
    return float(np.sqrt(np.mean((mu - y) ** 2)))


def simex(x, y, se, which, lams=(0.0, 0.5, 1.0, 2.0, 4.0)):
    """Add extra noise of variance lam * se^2 to x (which='x') or y (which='y'); extrapolate MSE to lam = -1."""
    mse = []
    for lam in lams:
        v = []
        for _ in range(NDRAW if lam > 0 else 1):
            eps = RNG.normal(0, 1, len(se)) * se * math.sqrt(lam)
            v.append(lopo_rmse_line(x + eps, y) ** 2 if which == "x" else lopo_rmse_line(x, y + eps) ** 2)
        mse.append(float(np.mean(v)))
    c = np.polyfit(lams, mse, 2)
    return {"lambda": list(lams), "rmse": [math.sqrt(m) for m in mse],
            "rmse_noise_free": float(math.sqrt(max(np.polyval(c, -1.0), 0.0)))}


def drift_whatif(x, y, sd, which):
    v = []
    for _ in range(NDRAW):
        eps = RNG.normal(0, sd, len(x))
        v.append(lopo_rmse_line(x + eps, y) ** 2 if which == "x" else lopo_rmse_line(x, y + eps) ** 2)
    return float(math.sqrt(np.mean(v)))


def budget(rows, revs):
    aor = np.array([r["aor"] for r in rows])
    l45 = np.array([r["lmg45"] for r in rows])
    se = np.array([r["se_lmg45"] for r in rows])
    b_inv = float(np.polyfit(l45, aor, 1)[0])        # deg per decade
    b_fwd = float(np.polyfit(aor, l45, 1)[0])        # decades per deg
    res33 = json.loads((HERE / "result.json").read_text())
    label_sd = res33["inverse"]["aor"]["ceiling"]["label_sd_rms"]
    inv_rmse, mean_rmse = lopo_rmse_line(l45, aor), res33["inverse"]["aor"]["mean"]["rmse"]
    fwd_rmse = lopo_rmse_line(aor, l45)
    day, fill = math.log10(1.10), math.log10(1.8)
    out = {
        "slope_inverse_deg_per_decade": b_inv, "slope_forward_decade_per_deg": b_fwd,
        "se_log10_mg45_median": float(np.median(se)), "se_log10_mg45_max": float(np.max(se)),
        "se_log10_mg45_rms": float(np.sqrt(np.mean(se ** 2))),
        "inverse_deg": {
            "model_rmse_line45": inv_rmse, "guess_the_mean": mean_rmse,
            "handbook_label_sd_rms": label_sd,
            "within_run_scatter_rms": abs(b_inv) * float(np.sqrt(np.mean(se ** 2))),
            "within_run_scatter_median_powder": abs(b_inv) * float(np.median(se)),
            "day_to_day_drift_10pct": abs(b_inv) * day, "fill_level_drift_1p8x": abs(b_inv) * fill,
            "simex_within_run": simex(l45, aor, se, "x"),
            "whatif_rmse_with_day_drift_10pct": drift_whatif(l45, aor, day, "x"),
            "whatif_rmse_with_fill_drift_1p8x": drift_whatif(l45, aor, fill, "x"),
        },
        "forward_decades": {
            "model_rmse_aor_line": fwd_rmse,
            "handbook_aor_spread_times_slope": abs(b_fwd) * label_sd,
            "within_run_scatter_rms": float(np.sqrt(np.mean(se ** 2))),
            "day_to_day_drift_10pct": day, "fill_level_drift_1p8x": fill,
            "simex_within_run": simex(aor, l45, se, "y"),
            "whatif_rmse_with_day_drift_10pct": drift_whatif(aor, l45, day, "y"),
            "whatif_rmse_with_fill_drift_1p8x": drift_whatif(aor, l45, fill, "y"),
        },
    }
    return out


# ------------------------------------------------------------------- 3. is the scatter itself a signal?

def scatter_signal(rows, revs):
    aor = np.array([r["aor"] for r in rows])
    l45 = np.array([r["lmg45"] for r in rows])
    cv = {}
    for k in ("22.5", "45"):
        c = []
        for r in rows:
            a = revs[r["powder_id"]][k]
            c.append(a.std(ddof=1) / a.mean() * 100 if a.mean() > 0 else float("nan"))
        cv[k] = np.array(c)
    out = {"cv_pct": {k: [None if not np.isfinite(v) else round(float(v), 1) for v in cv[k]] for k in cv},
           "powders": [r["powder_id"] for r in rows]}
    for k in cv:
        ok = np.isfinite(cv[k])
        lc = np.log10(cv[k][ok])
        rho = stats.spearmanr(lc, aor[ok])[0]
        rho_mean = stats.spearmanr(lc, l45[ok])[0]
        # partial: rank residuals of log CV and AoR after removing log mg/rev 45
        rr = lambda v: stats.rankdata(v)  # noqa: E731
        res_c = rr(lc) - np.polyval(np.polyfit(rr(l45[ok]), rr(lc), 1), rr(l45[ok]))
        res_a = rr(aor[ok]) - np.polyval(np.polyfit(rr(l45[ok]), rr(aor[ok]), 1), rr(l45[ok]))
        X2 = np.column_stack([l45[ok], lc])
        mu2, _, _ = M.lopo(X2, aor[ok], M.m_ridge)
        out[k] = {"n": int(ok.sum()), "spearman_logcv_aor": float(rho), "spearman_logcv_logmg45": float(rho_mean),
                  "partial_spearman_given_logmg45": float(stats.pearsonr(res_c, res_a)[0]),
                  "lopo_rmse_aor_line_on_logcv": lopo_rmse_line(lc, aor[ok]),
                  "lopo_rmse_aor_line_on_logmg45_same_powders": lopo_rmse_line(l45[ok], aor[ok]),
                  "lopo_rmse_aor_ridge_on_logmg45_and_logcv": float(np.sqrt(np.mean((mu2 - aor[ok]) ** 2)))}
    return out, cv


# ----------------------------------------------------------------------------- 4. hidden (latent) scores

def hidden_scores(rows):
    V = M.FP_CORE + M.PROPS
    Z = M.matrix(rows, V)
    J = M.Joint(Z, 1)
    W = J.W[0].copy()
    sgn = 1.0 if W[V.index("lmg45")] > 0 else -1.0     # orient: higher score = delivers more
    W *= sgn
    Zi, _ = M.impute(Z, Z[:1])
    zs = (Zi - J.mu) / J.sd

    def post(idx):
        Soo, w = J.S[np.ix_(idx, idx)], W[idx]
        return zs[:, idx] @ np.linalg.solve(Soo, w), float(math.sqrt(max(1 - w @ np.linalg.solve(Soo, w), 0)))

    fp, pr = [V.index(v) for v in M.FP_CORE], [V.index(v) for v in M.PROPS]
    m_fp, s_fp = post(fp)
    m_pr, s_pr = post(pr)
    return {"loadings": {M.NAMES[v]: round(float(w), 2) for v, w in zip(V, W)},
            "posterior_sd_from_fingerprint": s_fp, "posterior_sd_from_properties": s_pr,
            "per_powder": {r["powder_id"]: {"display": r["display"], "from_fingerprint": round(float(a), 2),
                                            "from_properties": round(float(b), 2), "aor": r["aor"],
                                            "mg_rev_45": r["mg45"]}
                           for r, a, b in zip(rows, m_fp, m_pr)}}


# ----------------------------------------------------------------------------------------------- figure

def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8.5)
    ax.grid(True, color=GRID, lw=0.6, zorder=0)
    ax.set_axisbelow(True)


def figure(C, Bd, cv, rows, path):
    fig, axs = plt.subplots(1, 3, figsize=(15.5, 4.9), gridspec_kw={"width_ratios": [1.15, 1.25, 1.0]})
    fig.patch.set_facecolor(SURF)

    # (a) repeats at fixed settings
    ax = axs[0]
    style(ax)
    for i, (key, lab, _, _) in enumerate(GROUPS):
        g = C[key]
        t = np.array(g["t_s"])
        jit = (RNG.random(len(t)) - 0.5) * 0.28
        ax.scatter(i + jit[1:], t[1:], s=34, color=BLUE, edgecolor=SURF, lw=1.0, zorder=3,
                   label="repeat doses" if i == 0 else None)
        ax.scatter(i + jit[0], t[0], s=70, marker="D", color=ORANGE, edgecolor=SURF, lw=1.2, zorder=4,
                   label="first dose at these settings" if i == 0 else None)
        ax.hlines(g["median_t_s"], i - 0.25, i + 0.25, color=INK, lw=1.6, zorder=5,
                  label="median" if i == 0 else None)
        ax.text(i, 640, f"{g['min_t_s']:.0f}–{g['max_t_s']:.0f} s", ha="center", va="top", fontsize=8,
                color=INK2)
    f = C["corner-09"]
    ax.annotate("the campaign's best single dose\n(51.8 s, 0.7 mg)", xy=(2.08, f["first_t_s"]),
                xytext=(2.35, 19), fontsize=7.8, color=INK2, ha="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_yscale("log")
    ax.set_ylim(9, 700)
    ax.set_xlim(-0.55, 3.55)
    ax.set_yticks([10, 20, 50, 100, 200, 500], ["10", "20", "50", "100", "200", "500"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks(range(len(GROUPS)), [f"{g[1]}\nn = {C[g[0]]['n']}" for g in GROUPS], fontsize=8.5, color=INK)
    ax.set_ylabel("dose time (s), 0.5 g of salt", color=INK, fontsize=9.5)
    ax.set_title("(a) Same settings, repeated doses", loc="left", fontsize=10.5, color=INK)
    ax.legend(loc="lower left", fontsize=7.8, frameon=False, labelcolor=INK2, handletextpad=0.3,
              borderaxespad=0.2)

    # (b) error budget, inverse AoR
    ax = axs[1]
    style(ax)
    I = Bd["inverse_deg"]
    items = [
        ("scatter within a run\n(6 revolutions, RMS over powders)", I["within_run_scatter_rms"]),
        ("salt's day-to-day drift (10 %)", I["day_to_day_drift_10pct"]),
        ("fill-level drift (1.8×)", I["fill_level_drift_1p8x"]),
        ("handbook spread of the AoR labels", I["handbook_label_sd_rms"]),
    ]
    y = np.arange(len(items))[::-1]
    ax.barh(y, [v for _, v in items], height=0.55, color=BLUE, zorder=3)
    for yy, (_, v) in zip(y, items):
        ax.text(v + 0.08, yy, f"{v:.2f}°" if v < 1 else f"{v:.1f}°", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y, [n for n, _ in items], fontsize=8.5, color=INK)
    ax.axvline(I["model_rmse_line45"], color=INK2, lw=1.0, ls="--", zorder=2)
    ax.text(I["model_rmse_line45"] - 0.1, len(items) - 0.25,
            f"model error now: {I['model_rmse_line45']:.1f}°\n(RMSE, line on mg/rev at 45°)",
            fontsize=8, color=INK2, va="top", ha="right")
    ax.axvline(I["guess_the_mean"], color=INK2, lw=1.0, ls=":", zorder=2)
    ax.text(I["guess_the_mean"] + 0.1, len(items) - 0.25, f"guessing\nthe mean:\n{I['guess_the_mean']:.1f}°",
            fontsize=8, color=INK2, va="top", ha="left")
    ax.set_xlim(0, 7.6)
    ax.set_ylim(-0.6, len(items) + 0.35)
    ax.set_xlabel("error each source adds to predicted AoR (°)", color=INK, fontsize=9.5)
    ax.set_title("(b) What limits reading AoR from dosing", loc="left", fontsize=10.5, color=INK)

    # (c) scatter between revolutions vs AoR
    ax = axs[2]
    style(ax)
    aor = np.array([r["aor"] for r in rows])
    conv = np.array([r["conveys"] for r in rows], bool)
    c45 = cv["45"]
    for msk, col, lab in ((conv, BLUE, "conveys"), (~conv, ORANGE, "does not convey")):
        ok = msk & np.isfinite(c45)
        ax.scatter(aor[ok], c45[ok], s=46, color=col, edgecolor=SURF, lw=1.0, zorder=3, label=lab)
    short = {"salt": "salt", "carboxymethyl-cellulose": "CMC", "calcium-lactate": "Ca lactate",
             "barium-chloride": "BaCl₂", "white-rice-flour": "white rice flour"}
    for r, a, c in zip(rows, aor, c45):
        if np.isfinite(c) and r["powder_id"] in short:
            right = r["powder_id"] == "white-rice-flour"
            ax.annotate(short[r["powder_id"]], (a, c), xytext=(-5 if right else 5, 4), textcoords="offset points",
                        fontsize=7.8, color=INK2, ha="right" if right else "left")
    ax.set_yscale("log")
    ax.set_xlabel("handbook angle of repose (°)", color=INK, fontsize=9.5)
    ax.set_ylabel("scatter between revolutions at 45° (CV, %)", color=INK, fontsize=9.5)
    ax.set_title("(c) Cohesive powders flow erratically", loc="left", fontsize=10.5, color=INK)
    ax.legend(loc="upper left", fontsize=7.8, frameon=False, labelcolor=INK2)

    fig.tight_layout(w_pad=2.2)
    fig.savefig(path, dpi=150, facecolor=SURF)
    plt.close(fig)


# ------------------------------------------------------------------------------------------------- main

def main():
    rows, _ = M.load()
    revs = per_rev(rows)
    C = campaign()
    Bd = budget(rows, revs)
    S, cv = scatter_signal(rows, revs)
    H = hidden_scores(rows)
    figure(C, Bd, cv, rows, HERE / "consistency.png")
    out = {"what": "run 33 follow-up: does dosing consistency limit the predictor; what a consistency objective "
                   "would change in the salt BO campaign",
           "salt_campaign_repeats": C, "error_budget": Bd, "scatter_as_signal": S, "hidden_scores_1factor": H,
           "notes": ["drift magnitudes are from the #179 draft (Limits of the present data): salt's feed factor "
                     "drifted about 10 % between two days and up to 1.8-fold across sessions with different fill "
                     "levels (#140); here they are applied as random per-powder offsets with that SD",
                     "SIMEX: extra noise of variance lambda * SE^2 added to log10 mg/rev at 45 deg, MSE fitted "
                     "with a quadratic in lambda and extrapolated to lambda = -1 (no scatter at all)",
                     f"P(within tol) counts ok doses with |error| <= {TOL_MG} mg"]}
    (HERE / "consistency.json").write_text(json.dumps(out, indent=1))
    I, F = Bd["inverse_deg"], Bd["forward_decades"]
    print(json.dumps({k: {kk: C[k][kk] for kk in ("n", "first_t_s", "median_t_s", "min_t_s", "max_t_s",
                                                   "median_abs_error_mg", "p_within_tol", "taps_range")}
                      for k, *_ in GROUPS}, indent=1))
    print("fastest single within tol:", C["fastest_single_dose_within_tol"])
    print("inverse:", json.dumps(I, indent=1))
    print("forward:", json.dumps(F, indent=1))
    print("scatter:", json.dumps({k: S[k] for k in ("22.5", "45")}, indent=1))
    print("hidden:", json.dumps(H, indent=1))


if __name__ == "__main__":
    main()

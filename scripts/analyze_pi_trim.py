#!/usr/bin/env python3
"""Analyze a pi_trickle_trim.py telemetry log (PR #131, 2026-09-08).

Parses the M/E/B/D/P/C/H/T rows the firmware script streams, fits the
fume-hood drift from the quiet windows (issues #116/#157), scores the
trials with the one-sided scorecard from ``docs/trim-bench-plan.md``
(raw AND drift-corrected), decomposes the predictive-cutoff budget per
bench-plan B1, and writes tidy CSVs + a run JSON + two figures.

Usage:
    python3 scripts/analyze_pi_trim.py --log <raw.log> --outdir <dir> \
        --started-utc 2026-09-08T22:25:35Z
"""

import argparse
import csv
import datetime
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import stream_reference
except ImportError:
    stream_reference = None

# dataviz reference palette (validated: adjacent CVD dE 9.1, normal 22.9)
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
INK = "#0b0b0b"
INK2 = "#52514e"
SURF = "#fcfcfb"
GRID = "#e4e3e0"
TOL_BAND = "#d9d8d4"


def parse_log(path):
    meta, events, probes = {}, [], []
    D, P, C, H, T = [], [], [], [], []
    with open(path, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("M,"):
                _, k, v = line.split(",", 2)
                meta[k] = v
            elif line.startswith("E,"):
                _, t, msg = line.split(",", 2)
                events.append((int(t), msg))
            elif line.startswith("B,"):
                f = line.split(",")
                probes.append(dict(t_ms=int(f[1]), tilt=float(f[2]),
                                   total_g=float(f[3]),
                                   per_rev_g=float(f[4])))
            elif line.startswith("D,"):
                f = line.split(",")
                if len(f) < 17:
                    continue
                D.append((int(f[1]), int(f[2]), f[3],
                          float(f[4]) if f[4] not in ("nan", "") else np.nan,
                          f[5], int(f[6] or 0),
                          float(f[7]) if f[7] else np.nan,
                          *[float(x) if x else np.nan for x in f[8:17]]))
            elif line.startswith("P,"):
                f = line.split(",")
                P.append(dict(t_ms=int(f[1]), trial=int(f[2]), kind=f[3],
                              mass=float(f[4]) if f[4] != "nan" else np.nan,
                              flag=f[5]))
            elif line.startswith("C,"):
                f = line.split(",")
                C.append(dict(t_ms=int(f[1]), trial=int(f[2]),
                              cycle=int(f[3]), taps=int(f[4]),
                              nudges=int(f[5]), m_before=float(f[6]),
                              m_after=float(f[7])))
            elif line.startswith("H,"):
                f = line.split(",")
                H.append(dict(t_ms=int(f[1]), trial=int(f[2]),
                              m_hat=float(f[3]), r_tau=float(f[4]),
                              k_sigma=float(f[5]), margin=float(f[6]),
                              target=float(f[7]), why=f[8]))
            elif line.startswith("T,"):
                f = line.split(",")
                T.append(dict(trial=int(f[1]), target_g=float(f[2]),
                              tilt=float(f[3]), tap_tilt=float(f[4]),
                              rep=int(f[5]), m_base=float(f[6]),
                              t_trickle_s=float(f[7]), revs=float(f[8]),
                              ff_end=float(f[9]), m_post=float(f[10]),
                              taps=int(f[11]), nudges=int(f[12]),
                              tap_cycles=int(f[13]),
                              t_total_s=float(f[14]),
                              m_settled=float(f[15]),
                              m_settled2=float(f[16]),
                              dispensed_g=float(f[17]),
                              error_mg=float(f[18]),
                              trickle_short_mg=float(f[19]),
                              verdict=f[20]))
    d = np.array(D, dtype=object)
    return meta, events, probes, d, P, C, H, T


def dcol(d, i, sel=None):
    rows = d if sel is None else d[sel]
    return np.array([r[i] for r in rows], dtype=float)


def fit_drift(d, phase, trial=None):
    """Least-squares slope over a quiet window; consecutive-duplicate
    frames dropped (the balance repeats its 5 Hz datum at our 10 Hz
    poll)."""
    sel = [i for i, r in enumerate(d)
           if r[2] == phase and (trial is None or r[1] == trial)
           and not math.isnan(r[3])]
    if len(sel) < 8:
        return None
    t = dcol(d, 0, sel) / 1000.0
    m = dcol(d, 3, sel)
    keep = np.concatenate([[True], np.diff(m) != 0.0]) | \
        np.concatenate([[True], np.diff(t) > 0.26])
    t, m = t[keep], m[keep]
    if len(t) < 6:
        return None
    A = np.vstack([t - t[0], np.ones_like(t)]).T
    (slope, icpt), *_ = np.linalg.lstsq(A, m, rcond=None)
    resid = m - A @ np.array([slope, icpt])
    shocks = int(np.sum(np.abs(np.diff(m)) > 0.010))
    return dict(t_start_s=float(t[0]), t_end_s=float(t[-1]),
                n=int(len(t)), rate_mg_min=float(slope * 1000 * 60),
                jitter_mg=float(np.std(resid) * 1000), shocks=shocks)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, ctr - hw), min(1.0, ctr + hw)


def scorecard(errors_mg, times_s, tol=5.0):
    e = np.asarray(errors_mg, dtype=float)
    n = len(e)
    over = int(np.sum(e > 0))
    p, lo, hi = wilson(over, n)
    strict = int(np.sum(e > tol))
    ps, los, his = wilson(strict, n)
    return {
        "n": n,
        "P_over": p, "P_over_ci95": [lo, hi], "n_over": over,
        "P_over_tol": ps, "P_over_tol_ci95": [los, his],
        "n_over_tol": strict,
        "n_within_tol": int(np.sum(np.abs(e) <= tol)),
        "n_in_yield_band": int(np.sum((e >= -tol) & (e <= 0))),
        "E_max_pos_mg": float(np.mean(np.maximum(e, 0.0))),
        "median_E_mg": float(np.median(e)),
        "mean_E_mg": float(np.mean(e)),
        "sd_E_mg": float(np.std(e, ddof=1)) if n > 1 else float("nan"),
        "max_pos_excess_mg": float(np.max(np.maximum(e, 0.0))),
        "min_E_mg": float(np.min(e)),
        "mean_dose_time_s": float(np.mean(times_s)),
        "median_dose_time_s": float(np.median(times_s)),
    }


def trial_p_times(P, trial):
    out = {}
    for p in P:
        if p["trial"] == trial:
            out[p["kind"]] = p
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--started-utc", default=None)
    ap.add_argument("--powder-id", default=None)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    meta, events, probes, d, P, C, H, T = parse_log(args.log)
    pid = args.powder_id or meta.get("powder_id", "unknown")
    tol = float(meta.get("tol_g", 0.005)) * 1000.0

    # ---- drift ------------------------------------------------------
    drift_rows = []
    sv = fit_drift(d, "survey", trial=0)
    if sv:
        drift_rows.append(dict(window="survey", **sv))
    for t in T:
        w = fit_drift(d, "drift", trial=t["trial"])
        if w:
            drift_rows.append(dict(window="trial%d" % t["trial"], **w))
    esv = fit_drift(d, "endsurvey", trial=0)
    if esv:
        drift_rows.append(dict(window="endsurvey", **esv))

    # ---- session drift rate for correction --------------------------
    # The 15 s pre-trial windows are contaminated by post-dose settling
    # (the pan relaxes for tens of seconds after the servo returns to
    # horizontal and the auger de-energises), so their slopes (-13 to
    # -31 mg/min here) are transients, NOT the thermal drift that acts
    # during a dose -- extrapolating them over a 5-6 min dose is wrong.
    # The trustworthy steady drift is the long quiet end-of-session
    # survey (stepper idle well clear of any actuation); fall back to the
    # start survey, then to the median of the per-trial windows.
    end_w = next((r for r in drift_rows if r["window"] == "endsurvey"),
                 None)
    beg_w = next((r for r in drift_rows if r["window"] == "survey"), None)
    if end_w is not None:
        session_drift = end_w["rate_mg_min"]
        drift_src = "endsurvey"
    elif beg_w is not None:
        session_drift = beg_w["rate_mg_min"]
        drift_src = "survey"
    else:
        vals = [r["rate_mg_min"] for r in drift_rows]
        session_drift = float(np.median(vals)) if vals else 0.0
        drift_src = "median_windows"

    # ---- per-trial correction + KF internals ------------------------
    trials = []
    for t in T:
        pt = trial_p_times(P, t["trial"])
        w = next((r for r in drift_rows
                  if r["window"] == "trial%d" % t["trial"]), None)
        rate = session_drift
        settle_rate = w["rate_mg_min"] if w else float("nan")
        tb = pt.get("base", {}).get("t_ms", np.nan)
        ts2 = pt.get("settled2", {}).get("t_ms", np.nan)
        tpost = pt.get("posttrickle", {}).get("t_ms", np.nan)
        span_min = (ts2 - tb) / 60000.0 if not (
            math.isnan(tb) or math.isnan(ts2)) else 0.0
        span_post = (tpost - tb) / 60000.0 if not (
            math.isnan(tb) or math.isnan(tpost)) else 0.0
        h = next((x for x in H if x["trial"] == t["trial"]), None)
        sel = [i for i, r in enumerate(d)
               if r[1] == t["trial"] and r[2] == "trickle"]
        rpm_peak = float(np.nanmax(dcol(d, 6, sel))) if sel else np.nan
        rhat_halt = h and (h["r_tau"] / float(meta.get("tau_s", 0.3)))
        tt = dict(powder_id=pid, **t)
        tt.update(dict(
            drift_mg_min=rate,
            settle_window_mg_min=settle_rate,
            error_corr_mg=t["error_mg"] - rate * span_min,
            trickle_short_corr_mg=t["trickle_short_mg"] - rate * span_post,
            drift_span_min=span_min,
            rpm_peak=rpm_peak,
            trickle_rate_mg_s=1000.0 * (t["m_post"] - t["m_base"])
            / t["t_trickle_s"] if t["t_trickle_s"] > 0 else np.nan,
            tap_phase_gain_mg=(t["m_settled2"] - t["m_post"]) * 1000.0,
            halt_why=h["why"] if h else "",
            halt_m_hat_g=h["m_hat"] if h else np.nan,
            halt_r_tau_mg=h["r_tau"] * 1000 if h else np.nan,
            halt_k_sigma_mg=h["k_sigma"] * 1000 if h else np.nan,
            halt_margin_mg=h["margin"] * 1000 if h else np.nan,
            r_hat_halt_mg_s=rhat_halt * 1000 if h else np.nan,
        ))
        trials.append(tt)

    # ---- scorecards -------------------------------------------------
    err_raw = [t["error_mg"] for t in trials]
    err_cor = [t["error_corr_mg"] for t in trials]
    times = [t["t_total_s"] for t in trials]
    card_raw = scorecard(err_raw, times, tol)
    card_cor = scorecard(err_cor, times, tol)
    short_raw = [t["trickle_short_mg"] for t in trials]
    short_cor = [t["trickle_short_corr_mg"] for t in trials]
    card_trickle = scorecard(short_cor, [t["t_trickle_s"] for t in trials],
                             tol)

    # ---- write CSVs -------------------------------------------------
    def wcsv(name, rows, fields):
        path = os.path.join(args.outdir, name)
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return path

    tfields = ["powder_id", "trial", "target_g", "rep", "tilt", "tap_tilt",
               "verdict", "m_base", "t_trickle_s", "revs", "ff_end",
               "m_post", "taps", "nudges", "tap_cycles", "t_total_s",
               "m_settled", "m_settled2", "dispensed_g", "error_mg",
               "error_corr_mg", "trickle_short_mg",
               "trickle_short_corr_mg", "drift_mg_min",
               "settle_window_mg_min", "drift_span_min",
               "rpm_peak", "trickle_rate_mg_s", "tap_phase_gain_mg",
               "halt_why", "halt_m_hat_g", "halt_r_tau_mg",
               "halt_k_sigma_mg", "halt_margin_mg", "r_hat_halt_mg_s"]
    wcsv("trials_%s.csv" % pid, trials, tfields)
    wcsv("drift_%s.csv" % pid, drift_rows,
         ["window", "t_start_s", "t_end_s", "n", "rate_mg_min",
          "jitter_mg", "shocks"])
    crows = [dict(powder_id=pid, delta_mg=(c["m_after"] - c["m_before"])
                  * 1000.0, **c) for c in C]
    wcsv("tapcycles_%s.csv" % pid, crows,
         ["powder_id", "trial", "cycle", "taps", "nudges", "m_before",
          "m_after", "delta_mg", "t_ms"])

    # ---- run JSON ---------------------------------------------------
    t_end_ms = max([r[0] for r in d] + [p["t_ms"] for p in P] + [0])
    started = args.started_utc
    ended = None
    if started:
        s = datetime.datetime.fromisoformat(started.replace("Z", "+00:00"))
        ended = (s + datetime.timedelta(milliseconds=t_end_ms)).isoformat()
    doc = {
        "doc_type": "pi_trickle_trim",
        "experiment": meta.get("experiment"),
        "powder_id": pid,
        "pr": 131,
        "started_utc": started,
        "ended_utc": ended,
        "algorithm": meta.get("algorithm"),
        "meta": meta,
        "probes": probes,
        "session_drift_mg_min": session_drift,
        "session_drift_source": drift_src,
        "drift_windows": drift_rows,
        "trials": trials,
        "scorecard_raw": card_raw,
        "scorecard_drift_corrected": card_cor,
        "scorecard_trickle_landing_corrected": card_trickle,
        "trickle_short_raw_mg": short_raw,
        "events": ["%d,%s" % e for e in events],
    }
    if stream_reference is not None and started:
        try:
            doc["video"] = stream_reference.describe(started, ended)
        except Exception as exc:   # video must never be fatal
            doc["video"] = {"resolved": False, "note": str(exc)}
    with open(os.path.join(args.outdir, "run_%s.json" % pid), "w") as fh:
        json.dump(doc, fh, indent=2)

    # ---- figures ----------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def style(ax):
        ax.set_facecolor(SURF)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.grid(True, color=GRID, lw=0.6, alpha=0.7)
        ax.tick_params(colors=INK2, labelsize=8)

    # Fig 1: session dashboard --------------------------------------
    sel_tr = [i for i, r in enumerate(d) if r[2] in
              ("trickle", "preroll", "tapsettle", "settle", "drift")
              or r[2] in ("survey", "endsurvey")]
    tmin = dcol(d, 0) / 60000.0
    mass = dcol(d, 3)
    fig, axes = plt.subplots(3, 1, figsize=(11, 7.6), sharex=True,
                             gridspec_kw=dict(height_ratios=[2.2, 1, 1]))
    fig.patch.set_facecolor(SURF)
    axA, axB, axC = axes
    ok = ~np.isnan(mass)
    axA.plot(tmin[ok], mass[ok], color=BLUE, lw=0.8, label="balance (raw)")
    sel_k = [i for i, r in enumerate(d) if r[2] == "trickle"
             and not math.isnan(r[7])]
    for t in T:
        s = [i for i in sel_k if d[i][1] == t["trial"]]
        if not s:
            continue
        axA.plot(dcol(d, 0, s) / 60000.0, dcol(d, 7, s) + t["m_base"],
                 color=ORANGE, lw=1.6,
                 label="KF $\\hat{m}$ (trickle)" if t["trial"] == 1
                 else None)
        axA.hlines(t["m_base"] + t["target_g"],
                   min(dcol(d, 0, s)) / 60000.0,
                   trial_p_times(P, t["trial"]).get(
                       "settled2", {}).get("t_ms", max(dcol(d, 0, s)))
                   / 60000.0, color=INK2, lw=0.9, ls="--")
        axA.annotate("T%d: %.0f mg" % (t["trial"], t["target_g"] * 1000),
                     xy=(min(dcol(d, 0, s)) / 60000.0,
                         t["m_base"] + t["target_g"]),
                     xytext=(0, 4), textcoords="offset points",
                     fontsize=7.5, color=INK2)
    axA.set_ylabel("pan mass (g, absolute)", fontsize=9, color=INK)
    axA.legend(loc="upper left", fontsize=8, frameon=False)
    style(axA)

    s_all = [i for i, r in enumerate(d) if r[2] == "trickle"]
    axB.plot(dcol(d, 0, s_all) / 60000.0, dcol(d, 8, s_all) * 1000,
             color=BLUE, lw=1.2, label="KF $\\hat{r}$")
    axB.plot(dcol(d, 0, s_all) / 60000.0, dcol(d, 12, s_all) * 1000,
             color=ORANGE, lw=1.2, ls="--", label="$r_{sp}$ (PI setpoint)")
    axB.set_ylabel("flow (mg/s)", fontsize=9, color=INK)
    axB.legend(loc="upper right", fontsize=8, frameon=False)
    style(axB)

    axC.plot(dcol(d, 0, s_all) / 60000.0, dcol(d, 6, s_all),
             color=BLUE, lw=1.0)
    axC.set_ylabel("commanded rpm", fontsize=9, color=INK)
    axC.set_xlabel("session time (min)", fontsize=9, color=INK)
    axC.set_ylim(-2, 50)
    axC.axhline(45, color=INK2, lw=0.8, ls=":")
    axC.annotate("45 rpm ceiling", xy=(0.99, 45), xycoords=("axes fraction",
                 "data"), xytext=(0, 3), textcoords="offset points",
                 ha="right", fontsize=7.5, color=INK2)
    style(axC)
    fig.suptitle("First hardware run of the rate-PI trickle-tap trim "
                 "(trickle_tap @ dc99459) -- %s, %s" %
                 (pid, (started or "")[:10]), fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(args.outdir, "pi_trim_dashboard.png"),
                dpi=160, facecolor=SURF)
    plt.close(fig)

    # Fig 2: scorecard ----------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2),
                             gridspec_kw=dict(width_ratios=[1.5, 1, 1]))
    fig.patch.set_facecolor(SURF)
    axE, axH, axD = axes
    x = np.arange(1, len(trials) + 1)
    axE.axhspan(-tol, tol, color=TOL_BAND, alpha=0.55, lw=0)
    axE.axhline(0, color=INK2, lw=0.8)
    axE.plot(x, [t["trickle_short_corr_mg"] for t in trials], "s",
             color=AQUA, ms=6, label="trickle landing (corr.)")
    axE.plot(x, err_raw, "o", color=BLUE, ms=7, label="final error (raw)")
    axE.plot(x, err_cor, "o", mfc="none", mec=ORANGE, mew=1.8, ms=10,
             label="final (drift-corr.)")
    for xi, t in zip(x, trials):
        axE.annotate("%.0f" % t["trickle_short_corr_mg"],
                     xy=(xi, t["trickle_short_corr_mg"]),
                     xytext=(6, -3), textcoords="offset points",
                     fontsize=7, color=AQUA)
    axE.set_xticks(x)
    axE.set_xticklabels(["T%d\n%.0f mg" % (t["trial"], t["target_g"] * 1000)
                         for t in trials], fontsize=7.5)
    axE.set_ylabel("error vs target (mg)", fontsize=9, color=INK)
    axE.annotate("tolerance $\\pm$%.0f mg" % tol, xy=(0.02, 0.535),
                 xycoords="axes fraction", fontsize=7.5, color=INK2)
    axE.legend(loc="lower right", fontsize=7.5, frameon=False)
    axE.set_title("dose error, n=%d (over-target: %d raw / %d corr.)"
                  % (len(trials), card_raw["n_over"], card_cor["n_over"]),
                  fontsize=9, color=INK)
    style(axE)

    bot = np.zeros(len(trials))
    for key, col, lab in (("halt_margin_mg", BLUE, "margin"),
                          ("halt_r_tau_mg", ORANGE, "$\\hat{r}\\tau$"),
                          ("halt_k_sigma_mg", AQUA, "$k\\sigma$")):
        v = np.array([t.get(key) or 0.0 for t in trials])
        v = np.nan_to_num(v)
        axH.bar(x, v, 0.62, bottom=bot, color=col, label=lab,
                edgecolor=SURF, linewidth=2)
        bot += v
    axH.set_xticks(x)
    axH.set_xticklabels(["T%d" % t["trial"] for t in trials], fontsize=8)
    axH.set_ylabel("stop-early budget at halt (mg)", fontsize=9, color=INK)
    axH.legend(loc="upper right", fontsize=7.5, frameon=False)
    axH.set_title("cutoff budget decomposition", fontsize=9, color=INK)
    style(axH)

    # steady thermal drift (long quiet surveys) vs settling transients
    # (15 s pre-trial windows, still relaxing from the last dose)
    axD.axhline(0, color=INK2, lw=0.8)
    surv = [r for r in drift_rows if r["window"] in ("survey", "endsurvey")]
    tri = [r for r in drift_rows if r["window"].startswith("trial")]
    if tri:
        axD.plot([r["t_start_s"] / 60.0 for r in tri],
                 [r["rate_mg_min"] for r in tri], "o", color=ORANGE,
                 ms=6, label="pre-trial 15 s (settling transient)")
    if surv:
        axD.plot([r["t_start_s"] / 60.0 for r in surv],
                 [r["rate_mg_min"] for r in surv], "D", color=BLUE,
                 ms=8, label="quiet survey (steady drift)")
    axD.axhline(session_drift, color=BLUE, lw=1.0, ls="--")
    axD.annotate("session drift %.1f mg/min (%s)"
                 % (session_drift, drift_src),
                 xy=(0.5, session_drift), xycoords=("axes fraction", "data"),
                 xytext=(0, -11), textcoords="offset points", ha="center",
                 fontsize=7.5, color=BLUE)
    axD.set_xlabel("session time (min)", fontsize=9, color=INK)
    axD.set_ylabel("drift (mg/min)", fontsize=9, color=INK)
    axD.set_title("fume-hood drift", fontsize=9, color=INK)
    axD.legend(loc="lower left", fontsize=7, frameon=False)
    style(axD)
    fig.suptitle("Rate-PI trickle-tap trim scorecard -- %s" % pid,
                 fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(args.outdir, "pi_trim_scorecard.png"),
                dpi=160, facecolor=SURF)
    plt.close(fig)

    # ---- console summary -------------------------------------------
    print(json.dumps({"scorecard_raw": card_raw,
                      "scorecard_drift_corrected": card_cor,
                      "trickle_landing_corrected": card_trickle,
                      "session_drift_mg_min": session_drift,
                      "session_drift_source": drift_src,
                      "drift_windows": drift_rows,
                      "probes": probes}, indent=2))
    for t in trials:
        print("T%d %4.0fmg rep%d %-14s err %+7.1f (corr %+7.1f)  "
              "short %+7.1f  taps %3d nudges %2d  %5.1fs" %
              (t["trial"], t["target_g"] * 1000, t["rep"], t["verdict"],
               t["error_mg"], t["error_corr_mg"], t["trickle_short_mg"],
               t["taps"], t["nudges"], t["t_total_s"]))


if __name__ == "__main__":
    main()

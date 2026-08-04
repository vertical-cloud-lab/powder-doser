#!/usr/bin/env python3
"""Identify the powder-doser state-space parameters from the salt datasets.

Fits every parameter of the model in ``docs/state-space-model.md`` /
``state_space.py`` that the data collected in PR #131 can support, and writes
the result to ``salt_params.json`` plus a set of figures.

The raw data lives in PR #131 (``data/tap-characterization/…``,
``data/pid-dose/…``, ``data/three-phase/…``).  Until that PR merges, point the
script at a checkout of its branch::

    git worktree add /tmp/pr131 origin/claude/issue-130-20260721-1807
    python optimization/state_space/fit_salt_parameters.py --data-root /tmp/pr131/data

What is identified, and from what:

============================  =========================================
parameter                     source
============================  =========================================
ff(alpha) feed factor map     tap-characterization ``trials_summary.csv``
                              (``prime_mg_per_rev``: one auger revolution
                              into an empty-lip state), both fill levels
G_fill fill-level gain        the two sessions' ff maps (same rig, same
                              powder, 2026-07-31 morning vs afternoon)
tap gain g_tap(alpha)         ``taps_tidy.csv``, first tap after re-feed
lip depletion r, floor y_inf  ``taps_tidy.csv``, 10 successive single taps
M_lip = A/(1-r)               tap-accessible lip inventory per tilt
tau_f in-flight time const.   PID run-2 halt transient (10 Hz raw frames)
m_air in-flight inventory     same, and the three-phase bulk halt
pulsation harmonics a_k,b_k   PID run-1 bulk phase at constant 45 rpm,
                              mass rate folded on auger phase
balance noise sigma_y         pre-roll stable frames; no-tap control
                              intervals in the tap sessions
============================  =========================================

Everything here is *salt only* — see the caveats section of the doc.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit, least_squares

REPO_ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

# Sessions of the single-tap characterization battery.  "half" and "full" are
# the hopper (auger-tube) fill states: the morning session ran on a tube that
# had been drawn down by several days of dosing, the afternoon session ran
# immediately after a refill weighed at 110 g gross - 56.716 g tare = 53.3 g.
TAP_SESSIONS = {
    "half": {
        "dir": "tap-characterization/2026-07-31_salt",
        "tube_powder_g": None,  # unweighed; ledger estimate only
        "note": "drawn-down tube, pre-refill (2026-07-31 AM)",
    },
    "full": {
        "dir": "tap-characterization/2026-07-31_salt_angles",
        "tube_powder_g": 53.3,
        "note": "freshly refilled tube, 53.3 g weighed (2026-07-31 PM)",
    },
}


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def read_csv(path: Path) -> list[dict]:
    with path.open() as fh:
        return list(csv.DictReader(fh))


def group_mean(pairs: list[tuple[float, float]]) -> dict[float, tuple[float, float, int]]:
    """{key: (mean, sd, n)} from (key, value) pairs."""
    buckets: dict[float, list[float]] = defaultdict(list)
    for k, v in pairs:
        buckets[k].append(v)
    out = {}
    for k, vals in sorted(buckets.items()):
        arr = np.asarray(vals, float)
        out[k] = (float(arr.mean()),
                  float(arr.std(ddof=1)) if len(arr) > 1 else float("nan"),
                  len(arr))
    return out


# ---------------------------------------------------------------------------
# 1. auger feed factor ff(tilt), at two fill levels
# ---------------------------------------------------------------------------

def ff_shape(alpha_deg, ff0, gain, a_peak):
    """Rise-then-roll-off feed-factor shape, g/rev.

    ff(0) = ff0 (the screw still conveys with the tube horizontal); tilt adds a
    gravity-assist term that is progressively lost once the tube is steep
    enough that the screw stops being the metering element.  The gamma shape
    ``a*exp(-a/a_peak)`` peaks at ``a_peak`` — observed near 40 deg plate for
    salt, with delivery falling again by 70 deg.
    """
    a = np.asarray(alpha_deg, float)
    return ff0 + gain * (a / a_peak) * np.exp(1.0 - a / a_peak)


def fit_feed_factor(data_root: Path) -> dict:
    out = {}
    # fit the wide-angle (full-tube) session first: it is the only one that can
    # locate the roll-off, which the 0-25 deg session then borrows.
    for fill in ("full", "half"):
        meta = TAP_SESSIONS[fill]
        rows = read_csv(data_root / meta["dir"] / "trials_summary.csv")
        pairs = [(float(r["angle_plate_deg"]), float(r["prime_mg_per_rev"]) / 1000.0)
                 for r in rows]
        stats = group_mean(pairs)
        angles = np.array(list(stats))
        means = np.array([stats[a][0] for a in angles])
        sds = np.array([stats[a][1] for a in angles])

        entry = {
            "note": meta["note"],
            "tube_powder_g": meta["tube_powder_g"],
            "n_trials": len(rows),
            "table": {f"{a:g}": {"mean_g_per_rev": stats[a][0],
                                 "sd_g_per_rev": stats[a][1],
                                 "n": stats[a][2]} for a in angles},
        }
        # the peaked shape needs the wide-angle sweep; the 0-25 deg session can
        # only support the rising branch, so fix the roll-off there.
        try:
            if angles.max() >= 50:
                popt, _ = curve_fit(ff_shape, angles, means, p0=[0.06, 0.10, 40.0],
                                    bounds=([0.0, 0.0, 5.0], [0.5, 2.0, 90.0]),
                                    maxfev=40000)
                a_peak_fixed = None
            else:
                # the 0-25 deg session cannot see the roll-off: borrow it
                a_peak_fixed = out["full"]["fit"]["a_peak_deg"]

                def _rise(a, ff0, gain):
                    return ff_shape(a, ff0, gain, a_peak_fixed)

                popt2, _ = curve_fit(_rise, angles, means, p0=[0.02, 0.15],
                                     bounds=([0.0, 0.0], [0.5, 2.0]), maxfev=40000)
                popt = [*popt2, a_peak_fixed]
            pred = ff_shape(angles, *popt)
            entry["fit"] = {
                "form": "ff(a) = ff0 + gain*(a/a_peak)*exp(1 - a/a_peak)  [g/rev]",
                "ff0_g_per_rev": float(popt[0]),
                "gain_g_per_rev": float(popt[1]),
                "a_peak_deg": float(popt[2]),
                "a_peak_borrowed_from_full_session": a_peak_fixed is not None,
                "ff_at_peak_g_per_rev": float(ff_shape(popt[2], *popt)),
                "rms_resid_g_per_rev": float(np.sqrt(np.mean((means - pred) ** 2))),
            }
        except Exception as exc:  # pragma: no cover - diagnostic path
            entry["fit"] = {"error": str(exc)}
        # replicate-to-replicate scatter is the process noise on one revolution
        rel = sds[np.isfinite(sds)] / means[np.isfinite(sds)]
        entry["cv_between_reps_median"] = float(np.median(rel))
        out[fill] = entry

    # Fill-level gain.  The sessions used different tilt grids, so compare the
    # fitted curves over the tilt range both sessions actually covered (0-25
    # deg).  NOTE: the two sessions differ by fill level AND by the act of
    # refilling (which re-packs the column) -- the two are confounded.
    grid = np.linspace(0.0, 25.0, 26)
    curves = {}
    for fill in ("full", "half"):
        f = out[fill]["fit"]
        curves[fill] = ff_shape(grid, f["ff0_g_per_rev"], f["gain_g_per_rev"],
                                f["a_peak_deg"])
    ratio = curves["full"] / curves["half"]
    out["fill_gain_full_over_half"] = {
        "overlap_tilt_range_deg": [0.0, 25.0],
        "ratio_at_0_deg": float(ratio[0]),
        "ratio_at_25_deg": float(ratio[-1]),
        "median_ratio_over_overlap": float(np.median(ratio)),
        "caveat": "fill level and re-packing from the refill are confounded",
    }
    return out


# ---------------------------------------------------------------------------
# 2. tap model: g_tap(tilt), depletion ratio r, floor y_inf, lip inventory
# ---------------------------------------------------------------------------

def fit_tap_model(data_root: Path) -> dict:
    out = {}
    for fill, meta in TAP_SESSIONS.items():
        rows = read_csv(data_root / meta["dir"] / "taps_tidy.csv")
        per_tilt: dict[float, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
        for r in rows:
            per_tilt[float(r["angle_plate_deg"])][int(r["tap_index"])].append(
                float(r["marginal_mg"]) / 1000.0)

        table = {}
        for tilt, by_index in sorted(per_tilt.items()):
            idx = np.array(sorted(by_index))
            mean = np.array([np.mean(by_index[i]) for i in idx])
            sd = np.array([np.std(by_index[i], ddof=1) if len(by_index[i]) > 1
                           else np.nan for i in idx])

            def model(i, A, r, y_inf):
                return y_inf + A * r ** (i - 1)

            try:
                popt, _ = curve_fit(model, idx, mean,
                                    p0=[max(mean[0] - mean[-1], 1e-4), 0.5, mean[-1]],
                                    bounds=([0.0, 0.0, 0.0], [1.0, 0.999, 1.0]),
                                    maxfev=40000)
                A, r, y_inf = (float(v) for v in popt)
                resid = mean - model(idx, A, r, y_inf)
                fit = {"A_g": A, "r": r, "y_inf_g": y_inf,
                       "M_lip_g": A / (1.0 - r) if r < 0.999 else float("nan"),
                       "rms_resid_g": float(np.sqrt(np.mean(resid ** 2)))}
            except Exception as exc:  # pragma: no cover
                fit = {"error": str(exc)}

            all_taps = np.concatenate([np.asarray(by_index[i], float) for i in idx])
            table[f"{tilt:g}"] = {
                "tap1_mean_g": float(mean[0]),
                "tap1_sd_g": float(sd[0]) if np.isfinite(sd[0]) else None,
                "tap_mean_g": float(all_taps.mean()),
                "tap_cv": float(all_taps.std(ddof=1) / all_taps.mean())
                          if all_taps.mean() > 0 else None,
                "cum10_g": float(mean.sum()),
                "n_taps": int(all_taps.size),
                "fit": fit,
                "profile_mean_g": [float(v) for v in mean],
            }
        # slope of the normalized profile: <0 means successive taps deplete
        norms = []
        for entry in table.values():
            p = np.asarray(entry["profile_mean_g"], float)
            if p.mean() > 0:
                norms.append(p / p.mean())
        norms = np.asarray(norms)
        i = np.arange(1, norms.shape[1] + 1)
        slope = float(np.polyfit(i, norms.mean(axis=0), 1)[0])
        # tilt scaling of the two tap terms: the depleting amplitude A and the
        # non-depleting floor y_inf.  Both are close to exponential in tilt.
        tilts = np.array([float(k) for k in table])
        scaling = {}
        for key, series in (("A", np.array([table[k]["fit"].get("A_g", np.nan)
                                            for k in table])),
                            ("y_inf", np.array([table[k]["fit"].get("y_inf_g", np.nan)
                                                for k in table])),
                            ("tap1", np.array([table[k]["tap1_mean_g"] for k in table]))):
            ok = np.isfinite(series) & (series > 1e-6)
            if ok.sum() >= 3:
                b, a = np.polyfit(tilts[ok], np.log(series[ok]), 1)
                scaling[key] = {"form": f"{key}(a) = k0*exp(a/a_scale)  [g]",
                                "k0_g": float(np.exp(a)),
                                "a_scale_deg": float(1.0 / b) if b != 0 else None,
                                "n_tilts": int(ok.sum())}
        out[fill] = {"note": meta["note"], "per_tilt": table,
                     "tilt_scaling": scaling,
                     "pooled_normalized_slope_per_tap": slope}

    # how much the fill/packing state moves the tap gain, at the nearest tilts
    # the two sessions share (18 vs 20 deg, 25 vs 30 deg)
    pairs = [("18", "20"), ("25", "30")]
    ratios = {}
    for half_a, full_a in pairs:
        h = out["half"]["per_tilt"].get(half_a)
        f = out["full"]["per_tilt"].get(full_a)
        if h and f and h["tap1_mean_g"] > 0:
            ratios[f"half@{half_a}deg / full@{full_a}deg"] = {
                "tap1_ratio": h["tap1_mean_g"] / max(f["tap1_mean_g"], 1e-9),
                "mean_tap_ratio": h["tap_mean_g"] / max(f["tap_mean_g"], 1e-9),
            }
    out["fill_effect_half_over_full"] = {
        "nearest_tilt_pairs": ratios,
        "note": ("taps got 10-20x WEAKER on the fuller/freshly-packed tube while "
                 "the auger got STRONGER -- one scalar fill factor cannot serve "
                 "both actuators"),
    }
    return out


# ---------------------------------------------------------------------------
# 3. in-flight inventory and its time constant, from the halt transient
# ---------------------------------------------------------------------------

def read_telemetry(path: Path) -> dict[str, np.ndarray]:
    rows = read_csv(path)
    return {
        "t": np.array([int(r["t_ms"]) / 1000.0 for r in rows]),
        "m": np.array([float(r["mass_g"]) for r in rows]),
        "stable": np.array([r["frame"] == "S" for r in rows]),
        "tilt": np.array([float(r["tilt_deg"]) for r in rows]),
        "rpm": np.array([float(r["auger_rpm_cmd"]) for r in rows]),
        "taps": np.array([int(r["taps_cum"]) for r in rows]),
        "phase": np.array([r["phase"] for r in rows]),
    }


def fit_in_flight(data_root: Path) -> dict:
    tel = read_telemetry(data_root / "pid-dose/2026-07-29_salt/telemetry_run2_salt.csv")
    dose = tel["phase"] == "dose"
    t, m, rpm = tel["t"][dose], tel["m"][dose], tel["rpm"][dose]

    # last sample with the auger commanded on
    running = np.flatnonzero(rpm > 0)
    i_halt = int(running[-1])
    t_halt = float(t[i_halt])

    # pre-halt flow: robust slope over the 0.8 s before the halt
    pre = (t >= t_halt - 0.8) & (t <= t_halt)
    flow_pre = float(np.polyfit(t[pre], m[pre], 1)[0])

    # post-halt: mass keeps arriving.  Model the landed mass as a first-order
    # emptying of the in-flight column, seen through the balance's own lag:
    #   m_land(t) = m_air0 * [1 - (tf*exp(-d/tf) - tb*exp(-d/tb)) / (tf - tb)]
    post = (t >= t_halt) & (t <= t_halt + 1.6)
    d = t[post] - t_halt
    y = m[post] - m[i_halt]

    def dual_lag(d, m_air0, tau_f, tau_b):
        tau_f = max(tau_f, 1e-3)
        tau_b = max(tau_b, 1e-3)
        if abs(tau_f - tau_b) < 1e-6:
            tau_b = tau_f * 1.01
        return m_air0 * (1.0 - (tau_f * np.exp(-d / tau_f)
                                - tau_b * np.exp(-d / tau_b)) / (tau_f - tau_b))

    p_dual, _ = curve_fit(dual_lag, d, y, p0=[0.03, 0.25, 0.15],
                          bounds=([0.0, 0.02, 0.02], [0.5, 3.0, 3.0]), maxfev=60000)

    def first_order(d, m_air0, tau):
        return m_air0 * (1.0 - np.exp(-d / tau))

    p_1st, _ = curve_fit(first_order, d, y, p0=[0.03, 0.3],
                         bounds=([0.0, 0.02], [0.5, 3.0]), maxfev=60000)

    settled = float(m[-1] - m[i_halt])

    # cross-check from the three-phase bulk halt (55 rpm continuous, 25 deg):
    # the log prints the mass gained during the 800 ms settle after the halt.
    three_phase = {}
    tp_dir = data_root / "three-phase/2026-07-30_salt"
    if tp_dir.is_dir():
        gains = []
        for log in sorted(tp_dir.glob("*.log")):
            txt = log.read_text(errors="replace")
            for mt in re.finditer(r"settled: mass .*?\(\s*[-\d.]+ g to go, \+([\d.]+) g while settling",
                                  txt):
                gains.append(float(mt.group(1)))
        if gains:
            three_phase = {"post_halt_gain_g": gains,
                           "mean_g": float(np.mean(gains)),
                           "note": "auger halted from 55 rpm continuous at 25 deg plate"}

    return {
        "source": "pid-dose/2026-07-29_salt run2 (PID, halt at 25 deg plate)",
        "t_halt_s": t_halt,
        "flow_pre_halt_g_per_s": flow_pre,
        "landed_after_halt_g": settled,
        "first_order_fit": {"m_air0_g": float(p_1st[0]), "tau_s": float(p_1st[1])},
        "dual_lag_fit": {"m_air0_g": float(p_dual[0]),
                         "tau_flight_s": float(p_dual[1]),
                         "tau_balance_s": float(p_dual[2])},
        "implied_tau_from_ratio_s": settled / flow_pre if flow_pre > 0 else None,
        "three_phase_cross_check": three_phase,
    }


# ---------------------------------------------------------------------------
# 4. per-revolution pulsation, folded on auger phase
# ---------------------------------------------------------------------------

def fit_pulsation(data_root: Path) -> dict:
    tel = read_telemetry(data_root / "pid-dose/2026-07-29_salt/telemetry_run1_salt.csv")
    # the open-loop stretch of run 1: tilt parked at 25 deg, auger at a constant
    # 45 rpm commanded, before the PID starts modulating speed.
    sel = (tel["phase"] == "dose") & (tel["rpm"] == 45.0) & (tel["tilt"] == 25.0)
    idx = np.flatnonzero(sel)
    # keep the longest contiguous block
    splits = np.split(idx, np.flatnonzero(np.diff(idx) != 1) + 1)
    block = max(splits, key=len)
    t, m = tel["t"][block], tel["m"][block]
    rpm = 45.0
    period = 60.0 / rpm

    rate = np.gradient(m, t)                      # g/s, balance-smoothed
    mean_rate = float(rate.mean())
    phase = ((t - t[0]) / period) % 1.0

    # first two harmonics of the rate vs auger phase
    def harm(p, c0, a1, b1, a2, b2):
        w = 2 * np.pi * p
        return c0 * (1 + a1 * np.cos(w) + b1 * np.sin(w)
                     + a2 * np.cos(2 * w) + b2 * np.sin(2 * w))

    popt, _ = curve_fit(harm, phase, rate, p0=[mean_rate, 0.3, 0.0, 0.1, 0.0],
                        maxfev=60000)
    c0, a1, b1, a2, b2 = (float(v) for v in popt)
    pred = harm(phase, *popt)
    ss_res = float(np.sum((rate - pred) ** 2))
    ss_tot = float(np.sum((rate - rate.mean()) ** 2))

    # revolution-to-revolution delivered mass over the same block
    n_rev = int((t[-1] - t[0]) / period)
    per_rev = [float(np.interp(t[0] + (k + 1) * period, t, m)
                     - np.interp(t[0] + k * period, t, m)) for k in range(n_rev)]

    return {
        "source": "pid-dose/2026-07-29_salt run1 bulk phase, 45 rpm at 25 deg plate",
        "window_s": [float(t[0]), float(t[-1])],
        "rev_period_s": period,
        "mean_flow_g_per_s": mean_rate,
        "mean_g_per_rev": mean_rate * period,
        "per_rev_delivered_g": per_rev,
        "harmonics": {"c0_g_per_s": c0, "a1": a1, "b1": b1, "a2": a2, "b2": b2,
                      "h1_amplitude": float(math.hypot(a1, b1)),
                      "h2_amplitude": float(math.hypot(a2, b2)),
                      "r2": 1.0 - ss_res / ss_tot if ss_tot > 0 else None},
        "note": ("amplitudes are a LOWER bound on the true screw pulsation: the "
                 "balance's ~0.2-0.4 s lag attenuates a 1.33 s cycle"),
        "_fold": {"phase": phase.tolist(), "rate": rate.tolist()},
    }


# ---------------------------------------------------------------------------
# 5. balance noise
# ---------------------------------------------------------------------------

def fit_balance_noise(data_root: Path) -> dict:
    out = {"quantization_g": 1e-4}
    sds, drifts = [], []
    for run in ("run1", "run2"):
        tel = read_telemetry(
            data_root / f"pid-dose/2026-07-29_salt/telemetry_{run}_salt.csv")
        pre = (tel["phase"] == "preroll") & tel["stable"]
        if pre.sum() > 5:
            m = tel["m"][pre]
            sds.append(float(m.std(ddof=1)))
            t = tel["t"][pre]
            drifts.append(float(np.polyfit(t, m, 1)[0]))
    out["preroll_stable_sd_g"] = sds
    out["preroll_drift_g_per_s"] = drifts

    # no-tap control intervals from the tap batteries: mass change with the rig
    # parked and nothing actuating -- the only clean "zero input" measurement
    ctrl = []
    for meta in TAP_SESSIONS.values():
        p = data_root / meta["dir"] / "trials_summary.csv"
        if p.exists():
            ctrl += [float(r["ctrl_mg_per_interval"]) / 1000.0 for r in read_csv(p)]
            ctrl += [float(r["post_mg_per_interval"]) / 1000.0 for r in read_csv(p)]
    if ctrl:
        arr = np.asarray(ctrl)
        out["no_actuation_interval_g"] = {"mean": float(arr.mean()),
                                          "sd": float(arr.std(ddof=1)),
                                          "n": int(arr.size)}
    return out


# ---------------------------------------------------------------------------
# 6. figures
# ---------------------------------------------------------------------------

def make_figures(params: dict, data_root: Path, outdir: Path) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    C = {"full": "#1f77b4", "half": "#d62728"}

    # --- feed factor + tap gain vs tilt -----------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    ax = axes[0]
    for fill in ("full", "half"):
        e = params["feed_factor"][fill]
        a = np.array([float(k) for k in e["table"]])
        mu = np.array([e["table"][k]["mean_g_per_rev"] for k in e["table"]]) * 1e3
        sd = np.array([e["table"][k]["sd_g_per_rev"] or 0 for k in e["table"]]) * 1e3
        ax.errorbar(a, mu, yerr=sd, fmt="o", color=C[fill], capsize=3,
                    label=f"{fill} tube ({e['note'].split('(')[0].strip()})")
        if "ff0_g_per_rev" in e["fit"]:
            g = np.linspace(0, max(a.max(), 70), 300)
            ax.plot(g, ff_shape(g, e["fit"]["ff0_g_per_rev"], e["fit"]["gain_g_per_rev"],
                                e["fit"]["a_peak_deg"]) * 1e3,
                    color=C[fill], alpha=0.6,
                    ls="--" if e["fit"].get("a_peak_borrowed_from_full_session") else "-")
    ax.set_xlabel("plate tilt α [deg]")
    ax.set_ylabel("feed factor ff [mg / auger rev]")
    ax.set_title("Auger: ff(α, fill)  — state x₅ → x₄ → x₃")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

    ax = axes[1]
    for fill in ("full", "half"):
        e = params["tap"][fill]["per_tilt"]
        a = np.array([float(k) for k in e])
        t1 = np.array([e[k]["tap1_mean_g"] for k in e]) * 1e3
        tm = np.array([e[k]["tap_mean_g"] for k in e]) * 1e3
        ax.plot(a, t1, "o-", color=C[fill], label=f"{fill}: 1st tap after re-feed")
        ax.plot(a, tm, "s--", color=C[fill], alpha=0.55, label=f"{fill}: mean of 10 taps")
    ax.set_yscale("log")
    ax.set_xlabel("plate tilt α [deg]")
    ax.set_ylabel("tap yield [mg]")
    ax.set_title("Tap: g_tap(α, x_lip, fill) — state x₃")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3, which="both")

    ax = axes[2]
    for fill in ("full", "half"):
        e = params["tap"][fill]["per_tilt"]
        for k in e:
            p = np.asarray(e[k]["profile_mean_g"]) * 1e3
            ax.plot(np.arange(1, len(p) + 1), p / p.mean(), color=C[fill], alpha=0.45,
                    lw=1)
        ax.plot([], [], color=C[fill],
                label=f"{fill}: slope {params['tap'][fill]['pooled_normalized_slope_per_tap']:+.3f}/tap")
    ax.set_xlabel("tap index after one re-feed revolution")
    ax.set_ylabel("yield / session mean")
    ax.set_title("Lip depletion — the x₃ discharge that taps see")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    p = outdir / "fig1-actuator-gains.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    written.append(p)

    # --- halt transient / in-flight inventory ------------------------------
    tel = read_telemetry(data_root / "pid-dose/2026-07-29_salt/telemetry_run2_salt.csv")
    fl = params["in_flight"]
    dose = tel["phase"] != "preroll"
    t, m, rpm = tel["t"][dose], tel["m"][dose], tel["rpm"][dose]
    t0 = fl["t_halt_s"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axes[0]
    ax.plot(t - t0, m * 1e3, ".-", ms=3, lw=0.8, color="#333", label="balance (10 Hz raw)")
    ax.axvline(0, color="#d62728", lw=1, ls="--", label="auger halt")
    d = np.linspace(0, 1.6, 200)
    f = fl["dual_lag_fit"]
    tf, tb, m0 = f["tau_flight_s"], f["tau_balance_s"], f["m_air0_g"]
    land = m0 * (1 - (tf * np.exp(-d / tf) - tb * np.exp(-d / tb)) / (tf - tb))
    ax.plot(d, (m[np.searchsorted(t, t0)] + land) * 1e3, color="#2ca02c", lw=2,
            label=f"fit: m_air={m0*1e3:.0f} mg, τ_f={tf:.2f} s, τ_b={tb:.2f} s")
    ax.set_xlim(-3, 3)
    m_halt = float(m[np.searchsorted(t, t0)])
    ax.set_ylim((m_halt - 0.10) * 1e3, (m_halt + 0.08) * 1e3)
    ax.set_xlabel("time since auger halt [s]")
    ax.set_ylabel("indicated mass [mg]")
    ax.set_title("In-flight inventory x₂ (PID run 2, 25° plate)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    ax2 = ax.twinx()
    ax2.plot(t - t0, rpm, color="#1f77b4", alpha=0.35, lw=1)
    ax2.set_ylabel("auger rpm command", color="#1f77b4", fontsize=8)

    # --- pulsation fold ----------------------------------------------------
    ax = axes[1]
    pl = params["pulsation"]
    ph = np.asarray(pl["_fold"]["phase"])
    rate = np.asarray(pl["_fold"]["rate"])
    ax.plot(ph, rate * 1e3, "o", ms=4, alpha=0.6, color="#333", label="10 Hz frames")
    g = np.linspace(0, 1, 200)
    h = pl["harmonics"]
    w = 2 * np.pi * g
    ax.plot(g, h["c0_g_per_s"] * (1 + h["a1"] * np.cos(w) + h["b1"] * np.sin(w)
                                  + h["a2"] * np.cos(2 * w) + h["b2"] * np.sin(2 * w)) * 1e3,
            color="#ff7f0e", lw=2,
            label=f"2 harmonics (R²={h['r2']:.2f}), |h₁|={h['h1_amplitude']:.2f}")
    ax.axhline(pl["mean_flow_g_per_s"] * 1e3, color="#888", ls=":", label="mean flow")
    ax.set_xlabel("auger phase θ [rev]")
    ax.set_ylabel("delivery rate [mg/s]")
    ax.set_title(f"Screw pulsation on phase state x₆ ({pl['mean_g_per_rev']*1e3:.0f} mg/rev)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    p = outdir / "fig2-transport-and-pulsation.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    written.append(p)
    return written


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-root", type=Path, default=REPO_ROOT / "data",
                    help="directory holding tap-characterization/, pid-dose/, three-phase/ "
                         "(they live in PR #131 until it merges)")
    ap.add_argument("--out", type=Path, default=HERE / "salt_params.json")
    ap.add_argument("--figdir", type=Path, default=HERE / "figures")
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args()

    root = args.data_root
    if not (root / "tap-characterization").is_dir():
        ap.error(f"no tap-characterization/ under {root}; see --help for PR #131 checkout")

    params = {
        "powder_id": "salt",
        "provenance": {
            "issue": 140,
            "data_prs": [124, 131],
            "data_root": str(root),
            "datasets": [
                "data/tap-characterization/2026-07-31_salt (12 trials, 0-25 deg, drawn-down tube)",
                "data/tap-characterization/2026-07-31_salt_angles (24 trials, 0-70 deg, 53.3 g tube)",
                "data/pid-dose/2026-07-29_salt (2 PID runs, 10 Hz raw telemetry)",
                "data/three-phase/2026-07-30_salt (2 three-phase 0.5 g doses)",
            ],
            "caveat": "salt only; all gains are powder-specific and must be re-identified",
        },
        "geometry": {
            "stepper_to_auger_gear": 2.2,
            "servo_to_plate_gear": 2.0,
            "plate_tilt_range_deg": [0.0, 90.0],
            "auger_rpm_max": 109.0,
            "empty_tube_tare_g": 56.716,
        },
        "feed_factor": fit_feed_factor(root),
        "tap": fit_tap_model(root),
        "in_flight": fit_in_flight(root),
        "pulsation": fit_pulsation(root),
        "balance": fit_balance_noise(root),
    }

    figs = []
    if not args.no_figures:
        figs = make_figures(params, root, args.figdir)

    # drop the bulky fold arrays from the committed JSON
    params["pulsation"].pop("_fold", None)
    args.out.write_text(json.dumps(params, indent=2, sort_keys=False) + "\n")
    print(f"wrote {args.out}")
    for f in figs:
        print(f"wrote {f}")

    ff = params["feed_factor"]["full"]["fit"]
    print(f"\nsalt summary (full tube): ff peaks at {ff['a_peak_deg']:.0f} deg plate, "
          f"{ff['ff_at_peak_g_per_rev']*1e3:.0f} mg/rev")
    fl = params["in_flight"]
    print(f"in-flight: {fl['landed_after_halt_g']*1e3:.1f} mg landed after halt, "
          f"tau_f = {fl['dual_lag_fit']['tau_flight_s']:.2f} s")
    print(f"pulsation: {params['pulsation']['mean_g_per_rev']*1e3:.0f} mg/rev, "
          f"|h1| = {params['pulsation']['harmonics']['h1_amplitude']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Statistics for the optimization manuscript, computed from the dose records.

Input: ``data/opt_trials/opt_trials_20260929-20261020.jsonl``, a snapshot of every
document in MongoDB ``powder_doser.opt_trials`` (125 documents, 29 Sep to 20 Oct 2026;
``export_opt_trials.py`` re-creates it), plus the campaign records copied into ``data/``.

Output (``analysis/results/``):
  stats.json        every number quoted in main.tex and si.tex, keyed by name
  doses_*.csv       per-dose tables behind the SI tables
  tables/*.tex      LaTeX bodies of the SI tables

Usage (from paper/optimization/):  python3 analysis/opt_stats.py
Every statistic is non-parametric or exact, because the samples are small (4-16 doses)
and dose times have a long right tail.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"
OUT = HERE / "results"
TAB = OUT / "tables"
SNAP = DATA / "opt_trials" / "opt_trials_20260929-20261020.jsonl"
SALT = DATA / "salt-20260929T014732Z"
MARGIN = DATA / "salt-margin-20261013T191339Z"
RNG = np.random.default_rng(20260929)
NBOOT = 20000

HAND = ("baseline-00", "baseline-01", "rebaseline-00", "rebaseline-01")
PRE_RESTART = (42, 43)  # validation doses before the 10-06 restart; in no block


# ------------------------------------------------------------------ loading
def load_snapshot() -> list[dict]:
    """The MongoDB snapshot (extended JSON: plain JSON for these documents)."""
    return [json.loads(line) for line in open(SNAP)]


def telemetry(doc: dict) -> pd.DataFrame | None:
    tel = doc.get("telemetry")
    if not isinstance(tel, dict) or not tel.get("header"):
        return None
    cols = tel["header"].split(",")
    rows = [r.split(",") for r in tel["rows"]]
    df = pd.DataFrame(rows, columns=cols)
    for c in df.columns:
        if c not in ("phase", "kind", "cmd", "flag", "session_utc"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def bulk_feed(doc: dict) -> dict:
    """Feed during the bulk stage, from the raw balance readings (z_g).

    rate: mass gained between the first and last bulk-stage reading / their time span.
    per_rev: rate / auger speed (rev/s) at the commanded bulk speed.  Readings lag the
    true mass by the balance's time constant, so both are slight underestimates for short
    bulk stages; stages shorter than 3 s are not used."""
    df = telemetry(doc)
    if df is None or "phase" not in df:
        return {}
    b = df[df.phase == "bulk"].dropna(subset=["t_s", "z_g"])
    if len(b) < 4:
        return {}
    dt = b.t_s.iloc[-1] - b.t_s.iloc[0]
    if dt < 3:
        return {}
    dm = b.z_g.iloc[-1] - b.z_g.iloc[0]
    p = doc.get("parameters_executed") or doc.get("parameters") or {}
    rpm = float(p.get("bulk_rpm") or np.nan)
    rate = dm / dt
    # second estimator: least-squares slope over the middle 60% of the bulk stage, which leaves out
    # the start-up gush and the end-of-stage taper (the two disagree most for short or tapering stages)
    t0 = b.t_s.iloc[0]
    w = b[(b.t_s >= t0 + 0.2 * dt) & (b.t_s <= t0 + 0.8 * dt)]
    mid = float(np.polyfit(w.t_s, w.z_g, 1)[0]) * 1e3 if len(w) >= 3 else np.nan
    return {"bulk_s": round(dt, 2), "bulk_dm_g": round(dm, 4), "bulk_rate_mgps": round(rate * 1e3, 2),
            "bulk_mid_mgps": round(mid, 2) if mid == mid else None,
            "bulk_mg_per_rev": round(rate * 1e3 / (rpm / 60.0), 1) if rpm == rpm and rpm > 0 else None}


def tap_yield(doc: dict) -> dict:
    """Mean mass per tap in the tap stage: (last - first tap-stage reading) / taps there."""
    df = telemetry(doc)
    if df is None or "phase" not in df:
        return {}
    t = df[df.phase == "tap"].dropna(subset=["z_g"])
    o = doc.get("outcomes") or {}
    if len(t) < 3:
        return {}
    dm = t.z_g.iloc[-1] - t.z_g.iloc[0]
    # taps in the tap stage = all taps minus those fired in earlier stages (not logged
    # separately); use the tap-stage row count of distinct readings as a floor check only
    n = o.get("taps") or 0
    return {"tap_stage_dm_mg": round(dm * 1e3, 2), "taps_total": n,
            "tap_stage_s": round(t.t_s.iloc[-1] - t.t_s.iloc[0], 1)}


# --------------------------------------------------------------- statistics
def boot_median_ci(x, n=NBOOT, alpha=0.05):
    x = np.asarray(x, float)
    meds = np.median(RNG.choice(x, size=(n, len(x)), replace=True), axis=1)
    return float(np.percentile(meds, 100 * alpha / 2)), float(np.percentile(meds, 100 * (1 - alpha / 2)))


def boot_ratio_ci(x, y, n=NBOOT, alpha=0.05):
    """Ratio of medians median(x)/median(y), percentile bootstrap (independent resampling)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    mx = np.median(RNG.choice(x, size=(n, len(x)), replace=True), axis=1)
    my = np.median(RNG.choice(y, size=(n, len(y)), replace=True), axis=1)
    r = mx / my
    return float(np.median(x) / np.median(y)), float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def hodges_lehmann(x, y, alpha=0.05):
    """Hodges-Lehmann shift median(x_i - y_j) with the exact Mann-Whitney confidence interval."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    d = np.sort((x[:, None] - y[None, :]).ravel())
    m, n = len(x), len(y)
    # exact null distribution of U: the CI drops the k smallest and k largest differences,
    # with k the largest count whose lower tail stays at or below alpha/2
    counts = _u_counts(m, n)
    p = np.cumsum(counts) / counts.sum()
    k = int(np.searchsorted(p, alpha / 2, side="right"))
    if k == 0:  # samples too small for any exact interval at this level
        return float(np.median(d)), float(d[0]), float(d[-1]), 1.0
    lo, hi = d[k - 1], d[len(d) - k]  # d_(u_lo+1) and d_(mn-u_lo), 1-indexed
    achieved = 1 - 2 * p[k - 1]
    return float(np.median(d)), float(lo), float(hi), float(achieved)


def _u_counts(m, n):
    """Number of arrangements giving each U = 0..m*n (Mann-Whitney null distribution)."""
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def f(m_, n_):
        if m_ == 0 or n_ == 0:
            out = np.zeros(m_ * n_ + 1)
            out[0] = 1
            return tuple(out)
        a = np.array(f(m_ - 1, n_))  # largest obs from x: contributes n_ to U
        b = np.array(f(m_, n_ - 1))
        out = np.zeros(m_ * n_ + 1)
        out[n_:n_ + len(a)] += a
        out[:len(b)] += b
        return tuple(out)
    return np.array(f(m, n))


def mwu(x, y):
    r = stats.mannwhitneyu(x, y, alternative="two-sided", method="exact")
    return float(r.statistic), float(r.pvalue)


def cp_interval(k, n, conf=0.95, one_sided=None):
    """Clopper-Pearson.  one_sided='lower' gives the one-sided lower bound at conf."""
    if one_sided == "lower":
        return float(stats.beta.ppf(1 - conf, k, n - k + 1)) if k > 0 else 0.0
    if one_sided == "upper":
        return float(stats.beta.ppf(conf, k + 1, n - k)) if k < n else 1.0
    ci = stats.binomtest(k, n).proportion_ci(confidence_level=conf, method="exact")
    return float(ci.low), float(ci.high)


def zero_failure_n(p_target=0.95, conf=0.95):
    """Doses without a failure needed to show P(success) >= p_target at one-sided conf."""
    return int(math.ceil(math.log(1 - conf) / math.log(p_target)))


def summ(x):
    x = np.asarray(x, float)
    return {"n": int(len(x)), "median": float(np.median(x)), "min": float(x.min()), "max": float(x.max()),
            "mean": float(x.mean()), "sd": float(x.std(ddof=1)) if len(x) > 1 else None}


# ------------------------------------------------------------ the campaigns
def salt_records() -> pd.DataFrame:
    rows = []
    for line in open(SALT / "campaign_records.jsonl"):
        r = json.loads(line)
        s, lab = r["summary"], r["label"]
        if r["mode"] == "validation":
            grp = "val-pre" if r["trial_index"] in PRE_RESTART else ("val-bo" if "bo-005" in lab else "val-corner")
        else:
            grp = ("hand" if lab in HAND else "center" if lab.startswith("center")
                   else "corner" if lab.startswith("corner") else "anchor" if lab.startswith("recenter")
                   else "bo")
        rows.append(dict(campaign="salt-0929", i=r["trial_index"], label=lab, group=grp, mode=r["mode"],
                         status=s["status"], t=s["t_total_s"], err=s["error_mg"], abs=s["abs_error_mg"],
                         taps=s.get("taps"), uuid=r["trial_uuid"], **r["params"]))
    return pd.DataFrame(rows).sort_values("i").reset_index(drop=True)


def margin_records() -> pd.DataFrame:
    rows = []
    for line in open(MARGIN / "campaign_records.jsonl"):
        r = json.loads(line)
        s, lab = r["summary"], r["label"]
        grp = ("corner" if lab.startswith("corner") else "check" if lab.startswith("check")
               else "bo")
        rows.append(dict(campaign="margin-1013", i=r["trial_index"], label=lab, group=grp, mode=r["mode"],
                         status=s["status"], t=s["t_total_s"], err=s["error_mg"], abs=s["abs_error_mg"],
                         taps=s.get("taps"), uuid=r["trial_uuid"], infra=bool(s.get("infra_error")),
                         utc=r.get("utc"), **r["params"]))
    return pd.DataFrame(rows).sort_values("i").reset_index(drop=True)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    TAB.mkdir(exist_ok=True)
    S: dict = {}
    docs = load_snapshot()
    by_uuid = {d["trial_uuid"]: d for d in docs}
    S["snapshot"] = {"documents": len(docs),
                     "first_utc": min(d["started_utc"] for d in docs),
                     "last_utc": max(d["started_utc"] for d in docs)}
    cnt = {}
    for d in docs:
        k = f'{d["campaign_id"]}|{d["mode"]}'
        cnt.setdefault(k, {}).setdefault(d["flags"]["status"], 0)
        cnt[k][d["flags"]["status"]] += 1
    S["snapshot"]["status_by_campaign_mode"] = cnt

    # ---------------- salt campaign, 2026-09-29, and its validation, 2026-10-06
    sr = salt_records()
    for _, r in sr.iterrows():
        d = by_uuid.get(r.uuid)
        if d is not None:
            for k, v in bulk_feed(d).items():
                sr.loc[sr.uuid == r.uuid, k] = v
            sr.loc[sr.uuid == r.uuid, "date"] = d["started_utc"][:10]
            sr.loc[sr.uuid == r.uuid, "tau_s"] = (d.get("parameters_executed") or {}).get("tau_afterflow_s")
            sr.loc[sr.uuid == r.uuid, "firmware"] = (d.get("device") or {}).get("firmware")
    sr.to_csv(OUT / "doses_salt_20260929.csv", index=False)
    camp = sr[~sr.group.str.startswith("val")]
    S["salt"] = {"doses": int(len(camp)),
                 "by_group": camp.group.value_counts().to_dict(),
                 "status": camp.status.value_counts().to_dict(),
                 "status_by_group": {g: v.status.value_counts().to_dict() for g, v in camp.groupby("group")}}
    t0 = pd.Timestamp(by_uuid[camp.uuid.iloc[0]]["started_utc"])
    t1 = pd.Timestamp(by_uuid[camp.uuid.iloc[-1]]["ended_utc"])
    S["salt"]["wall_clock_h"] = round((t1 - t0).total_seconds() / 3600, 2)
    over = camp[camp.status == "overshoot"]
    S["salt"]["overshoots"] = {"n": int(len(over)), "err_min": float(over.err.min()), "err_max": float(over.err.max()),
                               "by_group": over.group.value_counts().to_dict()}
    hand = camp[camp.group == "hand"]
    S["salt"]["hand"] = {"t": summ(hand.t), "err": summ(hand.err), "abs": summ(hand["abs"]),
                         "tau_s": hand.tau_s.tolist(), "labels": hand.label.tolist()}
    cen = camp[camp.group.isin(["center", "anchor"]) & camp.label.str.contains("center")]
    S["salt"]["center"] = {"t": summ(cen.t), "labels": cen.label.tolist()}

    vb = sr[sr.group == "val-bo"]
    vc = sr[sr.group == "val-corner"]
    V = {}
    for name, g in (("bo005", vb), ("corner09", vc)):
        V[name] = {"t": summ(g.t), "abs": summ(g["abs"]), "err": summ(g.err),
                   "t_median_ci": boot_median_ci(g.t), "abs_median_ci": boot_median_ci(g["abs"]),
                   "ok": int((g.status == "ok").sum()), "n": int(len(g)),
                   "delivered_sd_mg": float(np.std(g.err, ddof=1)),
                   "taps": summ(g.taps)}
        V[name]["p_ok_lower95_one_sided"] = cp_interval(V[name]["ok"], V[name]["n"], one_sided="lower")
        V[name]["p_overshoot_upper95_one_sided"] = cp_interval(0, V[name]["n"], one_sided="upper")
    V["n_zero_failure_for_p95"] = zero_failure_n(0.95, 0.95)
    V["n_zero_failure_for_p99"] = zero_failure_n(0.99, 0.95)
    # comparisons of time per dose
    for a_name, a in (("bo005", vb), ("corner09", vc)):
        for b_name, b in (("hand", hand), ("corner09", vc)):
            if a_name == b_name:
                continue
            u, p = mwu(a.t, b.t)
            hl = hodges_lehmann(a.t.values, b.t.values)
            ratio = boot_ratio_ci(b.t.values, a.t.values)
            V[f"{a_name}_vs_{b_name}_time"] = {"U": u, "p_exact_two_sided": p,
                                               "hl_shift_s": hl[0], "hl_ci_s": [hl[1], hl[2]],
                                               "hl_ci_achieved_conf": hl[3],
                                               "median_ratio_b_over_a": ratio[0],
                                               "median_ratio_ci95": [ratio[1], ratio[2]]}
            u, p = mwu(a["abs"], b["abs"])
            V[f"{a_name}_vs_{b_name}_abs"] = {"U": u, "p_exact_two_sided": p,
                                              "median_a": float(np.median(a["abs"])),
                                              "median_b": float(np.median(b["abs"]))}
    S["validation"] = V
    # model prediction at bo-005 (from the campaign report) vs the validation block
    pred_t, pred_t_sd, pred_e, pred_e_sd = 91.0, 66.0, 3.0, 9.0  # report.md / OUTLINE (Ax posterior)
    S["validation"]["bo005_prediction"] = {
        "t_pred_mean": pred_t, "t_pred_sd": pred_t_sd, "abs_pred_mean": pred_e, "abs_pred_sd": pred_e_sd,
        "t_block_mean": float(vb.t.mean()), "abs_block_mean": float(vb["abs"].mean()),
        "z_time": float((vb.t.mean() - pred_t) / pred_t_sd)}

    # ---------------- production doses at bo-005's profile on salt (10-06 to 10-08)
    ps = [d for d in docs if d["campaign_id"] == "production-salt"]
    prow = []
    for d in sorted(ps, key=lambda d: d["started_utc"]):
        o = d.get("outcomes") or {}
        prow.append({"utc": d["started_utc"][:16], "target_g": d["target_g"], "status": d["flags"]["status"],
                     "t_s": o.get("t_total_s"), "err_mg": o.get("error_mg"), "taps": o.get("taps"),
                     "final_g": o.get("settled_final_g"), "firmware": (d.get("device") or {}).get("firmware"),
                     **bulk_feed(d)})
    pdf = pd.DataFrame(prow)
    pdf.to_csv(OUT / "doses_production_salt.csv", index=False)
    S["production_salt"] = {"doses": prow,
                            "abs_err_range_mg": [float(pdf.err_mg.abs().min()), float(pdf.err_mg.abs().max())],
                            "targets_g": sorted(pdf.target_g.tolist())}

    # ---------------- margin campaign, 10-13 and 10-15
    mr = margin_records()
    for _, r in mr.iterrows():
        d = by_uuid.get(r.uuid)
        if d is not None:
            for k, v in bulk_feed(d).items():
                mr.loc[mr.uuid == r.uuid, k] = v
            mr.loc[mr.uuid == r.uuid, "date"] = d["started_utc"][:10]
            mr.loc[mr.uuid == r.uuid, "firmware"] = (d.get("device") or {}).get("firmware")
    mr.to_csv(OUT / "doses_margin_20261013.csv", index=False)
    M = {"doses": int(len(mr)), "status": mr.status.value_counts().to_dict(),
         "by_mode": mr["mode"].value_counts().to_dict(),
         "by_date": mr.date.value_counts().to_dict(),
         "status_by_mode": {g: v.status.value_counts().to_dict() for g, v in mr.groupby("mode")}}
    usable = mr[~mr.status.isin(["not-tared", "fw-error"])]
    M["usable"] = int(len(usable))
    # paired corners: 09-29 at 35 mg vs 10-13 at 0 mg (last attempt of each corner)
    c29 = camp[camp.group == "corner"].set_index("label")
    c13 = mr[(mr.group == "corner") & (mr.status != "not-tared")].groupby("label").tail(1).set_index("label")
    pairs = c29[["status", "t", "err", "abs", "bulk_rate_mgps"]].add_suffix("_35").join(
        c13[["status", "t", "err", "abs", "bulk_rate_mgps"]].add_suffix("_0"), how="inner")
    pairs.to_csv(OUT / "paired_corners_margin.csv")
    both = pairs[(pairs.status_35 == "ok") & (pairs.status_0 == "ok")]
    dt = both.t_0 - both.t_35
    M["pairs"] = {"n_pairs": int(len(pairs)), "n_both_ok": int(len(both)),
                  "dt_mean_s": float(dt.mean()), "dt_median_s": float(dt.median()),
                  "dabs_mean_mg": float((both.abs_0 - both.abs_35).mean()),
                  "wilcoxon_time": dict(zip(("W", "p"), map(float, stats.wilcoxon(both.t_0, both.t_35, method="exact")))),
                  "overshoot_35": int((pairs.status_35 == "overshoot").sum()),
                  "overshoot_0": int((pairs.status_0 == "overshoot").sum()),
                  "ok_35": int((pairs.status_35 == "ok").sum()), "ok_0": int((pairs.status_0 == "ok").sum()),
                  "discordant_overshoot": [int(((pairs.status_35 == "overshoot") & (pairs.status_0 != "overshoot")).sum()),
                                           int(((pairs.status_35 != "overshoot") & (pairs.status_0 == "overshoot")).sum())]}
    b = M["pairs"]["discordant_overshoot"]
    M["pairs"]["mcnemar_exact_p"] = float(stats.binomtest(min(b), sum(b), 0.5).pvalue) if sum(b) else 1.0
    # does a setting's rank carry over from one session to the next? (16 corners, all outcomes)
    for col, key in (("t", "time"), ("abs", "abs"), ("bulk_rate_mgps", "bulk")):
        r = stats.spearmanr(pairs[f"{col}_35"], pairs[f"{col}_0"], nan_policy="omit")
        M["pairs"][f"spearman_{key}"] = {"rho": float(r.statistic), "p": float(r.pvalue)}
    # bulk feed of the same corner, 09-29 vs 10-13 (bulk stage is identical at both margins)
    bf = pairs.dropna(subset=["bulk_rate_mgps_35", "bulk_rate_mgps_0"])
    if len(bf) >= 5:
        M["pairs"]["bulk_rate_ratio_median"] = float(np.median(bf.bulk_rate_mgps_0 / bf.bulk_rate_mgps_35))
        M["pairs"]["bulk_rate_wilcoxon_p"] = float(stats.wilcoxon(bf.bulk_rate_mgps_0, bf.bulk_rate_mgps_35, method="exact").pvalue)
        M["pairs"]["bulk_rate_n"] = int(len(bf))
    # BO phase outcome
    bo = mr[mr["mode"] == "bo"]
    M["bo"] = {"doses": int(len(bo)), "status": bo.status.value_counts().to_dict(),
               "ok_within_3mg": bo[(bo.status == "ok") & (bo["abs"] <= 3.0)].label.tolist(),
               "best_ok": bo[bo.status == "ok"].sort_values("t")[["label", "t", "abs"]].head(4).to_dict("records")}
    S["margin"] = M

    # ---------------- feed at 40 deg / 20 rpm across sessions (salt, same auger fill)
    allsalt = pd.concat([sr.assign(campaign="salt-0929"), mr], ignore_index=True)
    sel = allsalt[(allsalt.bulk_tilt_deg == 40.0) & (allsalt.bulk_rpm == 20.0)].dropna(subset=["bulk_rate_mgps"])
    sess = {}
    for dte, g in sel.groupby("date"):
        sess[dte] = {"n": int(len(g)), "median_mgps": float(g.bulk_rate_mgps.median()),
                     "min": float(g.bulk_rate_mgps.min()), "max": float(g.bulk_rate_mgps.max())}
    S["feed_40deg_20rpm_by_date"] = sess
    sel.to_csv(OUT / "feed_40deg_20rpm.csv", index=False)
    # all bulk feeds normalised per auger revolution, by date
    perrev = allsalt.dropna(subset=["bulk_mg_per_rev"])
    S["feed_per_rev_by_date"] = {d_: summ(g.bulk_mg_per_rev) for d_, g in perrev.groupby("date")}

    # ---------------- metal feedstock: AlSi10Mg and Al 4047 into atomizer charges
    met = []
    for d in sorted(docs, key=lambda d: d["started_utc"]):
        if not d["campaign_id"].startswith("production-al"):
            continue
        o = d.get("outcomes") or {}
        p = d.get("parameters_executed") or d.get("parameters") or {}
        row = {"campaign": d["campaign_id"], "mode": d["mode"], "utc": d["started_utc"][:16],
               "powder": d["powder_id"], "target_g": d.get("target_g"), "status": d["flags"]["status"],
               "t_s": o.get("t_total_s"), "err_mg": o.get("error_mg"), "final_g": o.get("settled_final_g"),
               "auger_rev": o.get("auger_rev"), "taps": o.get("taps"),
               "bulk_tilt": p.get("bulk_tilt_deg"), "bulk_rpm": p.get("bulk_rpm"),
               "bulk_only": p.get("bulk_only"), "firmware": (d.get("device") or {}).get("firmware")}
        if d["mode"] != "manual":
            row.update(bulk_feed(d))
            if o.get("auger_rev") and o.get("settled_final_g") is not None and o["auger_rev"] > 0:
                row["mean_mg_per_rev"] = round(1e3 * o["settled_final_g"] / o["auger_rev"], 2)
        else:
            row["hand_added_g"] = o.get("hand_added_g")
            row["auger_rev_fwd"] = o.get("auger_rev_fwd")
            row["auger_rev_rev"] = o.get("auger_rev_rev")
        met.append(row)
    mdf = pd.DataFrame(met)
    mdf.to_csv(OUT / "doses_metal_feedstock.csv", index=False)
    S["metal"] = {"rows": met}
    al = mdf[(mdf.powder == "alsi10mg")].iloc[0]
    S["metal"]["alsi10mg"] = {"final_g": float(al.final_g), "target_g": float(al.target_g), "err_mg": float(al.err_mg),
                              "rel_err_pct": float(100 * al.err_mg / 1e3 / al.target_g), "t_s": float(al.t_s),
                              "mean_mg_per_rev": float(al.mean_mg_per_rev)}
    # crucible mass accounting (from the issue #186 / PR #166 records)
    S["metal"]["charges"] = [
        {"charge": "AlSi10Mg, 8 g (09-29)", "target_g": 8.0, "final_g": 7.9928, "steps": "one dose, salt bo-005 settings"},
        {"charge": "Al 4047, 8 g (09-30)", "target_g": 8.0, "final_g": 8.0010,
         "steps": "dose stalled at 7.6811 g after 803 s (cycle budget); bulk-only top-up"},
        {"charge": "Al 4047, 7.5 wt% (10-19/20)", "target_g": 3.0407, "final_g": 3.0432,
         "steps": "3 executor doses stalled (0.20 g); 13 reverse turns at 0 deg freed the outlet; stepwise reverse dosing"},
        {"charge": "Al 4047, 15 wt% (10-20)", "target_g": 6.5674, "final_g": 6.5676,
         "steps": "3 doses stalled or timed out (5.31 g); operator removed large particles; 1 ok dose + 22-step top-up"},
    ]
    for c in S["metal"]["charges"]:
        c["err_mg"] = round(1e3 * (c["final_g"] - c["target_g"]), 1)
    # Al 4047 feed decline across restarts on 10-20 (bulk feed at 40 deg)
    a47 = mdf[(mdf.powder == "al4047") & (mdf["mode"] == "production")].dropna(subset=["bulk_rate_mgps"])
    S["metal"]["al4047_bulk_rates"] = a47[["utc", "target_g", "status", "bulk_s", "bulk_dm_g", "bulk_rate_mgps",
                                            "bulk_mg_per_rev", "bulk_tilt", "bulk_rpm"]].to_dict("records")

    # ---------------- write
    json.dump(S, open(OUT / "stats.json", "w"), indent=1, default=float)
    print("wrote", OUT / "stats.json")
    write_tables(sr, mr, pdf, mdf)


def _fmt(x, nd=1):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "--"
    return f"{x:.{nd}f}"


def write_tables(sr, mr, pdf, mdf) -> None:
    """LaTeX table bodies for the SI (one row per dose)."""
    def setting(r):
        def g1(x):
            return f"{round(x, 1):g}"
        return (f"{r.bulk_tap}/{r.trim_tap} & {g1(r.bulk_tilt_deg)} & {g1(r.trickle_tilt_deg)} & {g1(r.tap_tilt_deg)} & "
                f"{round(r.bulk_rpm):d} & {r.trickle_start_remaining_g:.3f} & {g1(1e3 * r.tolerance_g)}")
    lines = []
    for _, r in sr.iterrows():
        lab = r.label.replace("_", r"\_")
        lines.append(f"{r.i} & \\texttt{{{lab}}} & {setting(r)} & {r.status} & {_fmt(r.t)} & {_fmt(r.err)} & "
                     f"{_fmt(r.get('bulk_rate_mgps'))} \\\\")
    (TAB / "si_salt_doses.tex").write_text("\n".join(lines) + "\n")
    lines = []
    for _, r in mr.iterrows():
        lab = r.label.replace("_", r"\_")
        lines.append(f"{r.i} & \\texttt{{{lab}}} & {setting(r)} & {1e3 * r.cutoff_margin_g:.1f} & {r.status} & "
                     f"{_fmt(r.t)} & {_fmt(r.err)} & {_fmt(r.get('bulk_rate_mgps'))} \\\\")
    (TAB / "si_margin_doses.tex").write_text("\n".join(lines) + "\n")
    lines = []
    for _, r in pdf.iterrows():
        lines.append(f"{r.utc.replace('T', ' ')} & {r.target_g:g} & {r.status} & {_fmt(r.t_s)} & {_fmt(r.err_mg, 2)} & {int(r.taps)} \\\\")
    (TAB / "si_production_salt.tex").write_text("\n".join(lines) + "\n")
    lines = []
    for _, r in mdf.iterrows():
        tgt = "--" if r.target_g is None or (isinstance(r.target_g, float) and not np.isfinite(r.target_g)) else f"{r.target_g:.4f}"
        rate = _fmt(r.get("bulk_rate_mgps"), 1) if "bulk_rate_mgps" in r else "--"
        mid = _fmt(r.get("bulk_mid_mgps"), 1) if "bulk_mid_mgps" in r else "--"
        lines.append(f"{r.utc.replace('T', ' ')} & {'AlSi10Mg' if r.powder == 'alsi10mg' else 'Al 4047'} & {r['mode']} & "
                     f"{tgt} & {r.status} & {_fmt(r.t_s)} & {rate} & {mid} \\\\")
    (TAB / "si_metal_doses.tex").write_text("\n".join(lines) + "\n")
    print("wrote", TAB)


if __name__ == "__main__":
    main()

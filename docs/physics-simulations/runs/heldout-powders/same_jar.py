"""Same-jar measurements for Sam's battery powders: what the models predict before the lab measures the jars.

Sterling on #196 (4 Nov 2026): "so basically, run real experiments instead of relying on literature values".
This script puts numbers on that, from the data and runs already in this folder (no new simulation):

1. How blurred the handbook angles of repose (AoR) are, against the step in the dosing data.
2. Predictions written down now, to be checked once the AoR is measured on each jar: which side of the step,
   the AoR each model needs to reproduce the jar's measured mg/rev, and the pass/fail criteria.
3. Solid volume per revolution of the powders that convey, against the twin's grain-size effect. This is why the
   jars' PSDs and the as-printed exit matter for the simulations.
4. Predictions for a powder that has never been dosed, from its measured AoR and particle density (a prospective
   test that no fit can have seen).

Reads data/, doser_path.json and aor_path.json (through predict.py) and coarse_graining_check.json. Writes
same_jar_predictions.json, same_jar_tables.md and same_jar.png.

usage: /tmp/venv/bin/python same_jar.py               # analysis, tables, figure
       /tmp/venv/bin/python same_jar.py new 33 2.70   # never-dosed powder: measured AoR (deg), particle density (g/cm3)
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict as P  # noqa: E402

ANNULUS_MM = 1.07          # twin's exit: core-tip annulus, r = 0.43 to 1.5 mm (run 24, #180 CAD)
THRESH = P.FLOW_THRESHOLD  # 50 mg/rev at 45 deg: conveys / does not convey
SHORT = {"alsi10mg": "AlSi10Mg", "silicon-110-200": "Si 75–150 µm", "sodium-sulfate": "Na₂SO₄",
         "calcium-lactate": "Ca lactate", "barium-chloride": "BaCl₂", "xanthan-gum": "xanthan",
         "salt": "salt", "carboxymethyl-cellulose": "CMC", "white-rice-flour": "white rice flour",
         "sodium-alginate": "alginate", "brown-rice-flour": "brown rice flour", "silicon-325": "Si <44 µm",
         "fumed-silica": "fumed silica"}


def load():
    powders = P.load_powders()
    doser = json.load(open(os.path.join(HERE, "doser_path.json")))
    aor = [r for r in json.load(open(os.path.join(HERE, "aor_path.json"))) if r.get("rc") == 0 and "angle_iso_deg" in r]
    chain = P.DemChain(doser, aor)
    d50 = {}
    for r in P.read_csv("literature_powder_properties_long.csv"):
        if r["property"] == "d50":
            d50[r["powder_id"]] = (P.fnum(r["range_low"]), P.fnum(r["range_high"]))
    fumed = next(r for r in P.read_csv("rate_summary.csv") if r["powder_id"] == "fumed-silica")
    return powders, chain, d50, fumed

# ------------------------------------------------------------------------------ 1. handbook spread


def handbook_spread(powders):
    """Published AoR ranges read as the uncertainty in each jar's AoR: uniform within the range (SD = width/sqrt 12),
    or the range taken as +-2 SD (SD = width/4)."""
    w = np.array([p["aor_hi"] - p["aor_lo"] for p in powders])
    a = np.array([p["aor"] for p in powders])
    y = np.array([P.logy(p["mg_rev"]["45"]) for p in powders])
    flows = np.array([p["mg_rev"]["45"] >= THRESH for p in powders])
    step = 0.5 * (a[flows].max() + a[~flows].min()) if a[flows].max() < a[~flows].min() else None
    straddle = [p["powder_id"] for p in powders if step is not None and p["aor_lo"] < step < p["aor_hi"]]
    out = {"range_width_deg": {p["powder_id"]: round(float(x), 1) for p, x in zip(powders, w)},
           "width_min_max_median": [float(w.min()), float(w.max()), float(np.median(w))],
           "rms_sd_uniform_deg": round(float(np.sqrt(np.mean(w ** 2 / 12))), 2),
           "rms_sd_2sigma_deg": round(float(np.sqrt(np.mean((w / 4) ** 2))), 2),
           "step_deg": step, "ranges_straddling_step": straddle,
           "aor_conveying": sorted(a[flows].tolist()), "aor_not_conveying": sorted(a[~flows].tolist())}
    # regression dilution: share of the handbook AoR variance that is spread, not difference between powders
    r = float(np.corrcoef(a, y)[0, 1])
    var_a = float(np.var(a, ddof=1))
    for lab in ("uniform", "2sigma"):
        ve = out[f"rms_sd_{lab}_deg"] ** 2
        lam = (var_a - ve) / var_a
        out[f"reliability_{lab}"] = round(lam, 2)
        # residual variance left after removing the spread, as a fraction of var(log mg/rev): 1 - r^2/lambda
        out[f"residual_share_after_spread_{lab}"] = round(1 - r * r / lam, 2)
    out["pearson_r_aor_log_mg_rev_45"] = round(r, 3)
    out["var_handbook_aor_deg2"] = round(var_a, 1)
    return out

# ------------------------------------------------------------------- 2. predictions for the jars


def inverse_all12(powders, chain):
    """Inverse models fitted on all 12 powders: the AoR each model needs to reproduce a jar's measured mg/rev."""
    a = np.array([p["aor"] for p in powders])
    y45 = np.array([P.logy(p["mg_rev"]["45"]) for p in powders])
    b = P.ols(y45, a)
    resid = a - (b[0] + b[1] * y45)
    _, inv, _ = P.inverse(powders, chain)            # inv["inv_dem_noshift"]: DEM path, both tilts, no offset
    a_dem = inv["inv_dem_noshift"]
    off = float(np.mean(a - a_dem))
    # LOPO scores against the handbook values, for the record (same as predict.py)
    lopo_line = np.array([P.ols(np.delete(y45, i), np.delete(a, i)) @ [1, y45[i]] for i in range(len(a))])
    return {"line": {"a_deg": round(float(b[0]), 3), "b_deg_per_decade": round(float(b[1]), 3),
                     "in_sample_rmse_deg": round(float(np.sqrt(np.mean(resid ** 2))), 2),
                     "lopo_rmse_deg": round(float(np.sqrt(np.mean((lopo_line - a) ** 2))), 2)},
            "dem_offset_deg": round(off, 2),
            "per_powder": {p["powder_id"]: {"line": round(float(b[0] + b[1] * yy), 1), "dem": round(float(ad + off), 1)}
                           for p, yy, ad in zip(powders, y45, a_dem)}}


def jar_predictions(powders, chain, fumed, spread, invm):
    rows = []
    step = spread["step_deg"]
    for p in sorted(powders, key=lambda q: -q["mg_rev"]["45"]):
        pid = p["powder_id"]
        rows.append({"powder_id": pid, "display": SHORT[pid], "aor_handbook": p["aor"],
                     "aor_range": [p["aor_lo"], p["aor_hi"]], "mg_rev_45_aug": p["mg_rev"]["45"],
                     "mg_rev_22p5_aug": p["mg_rev"]["22p5"],
                     "side_of_step": "below" if p["mg_rev"]["45"] >= THRESH else "above",
                     "aor_line": invm["per_powder"][pid]["line"], "aor_dem": invm["per_powder"][pid]["dem"]})
    # fumed silica: no handbook properties; its 45 deg value (5.6 mg/rev) is under the run's 6.1 mg noise floor
    nf = P.fnum(fumed["noise_floor_mg"])
    b0, b1 = invm["line"]["a_deg"], invm["line"]["b_deg_per_decade"]
    rows.append({"powder_id": "fumed-silica", "display": SHORT["fumed-silica"], "aor_handbook": None, "aor_range": None,
                 "mg_rev_45_aug": P.fnum(fumed["mg_rev_tilt45deg"]), "mg_rev_22p5_aug": P.fnum(fumed["mg_rev_tilt22p5deg"]),
                 "qc_verdict": fumed["qc_verdict"], "noise_floor_mg": nf, "side_of_step": "above",
                 "aor_line": f"≥ {b0 + b1 * math.log10(nf):.1f}", "aor_dem": None})
    conv = [r for r in rows if r["side_of_step"] == "below"]
    criteria = {
        "C1_step": "One AoR threshold separates the jars that convey at 45° (≥ 50 mg/rev: " +
                   ", ".join(r["display"] for r in conv) + ") from the rest, fumed silica included (13 of 13).",
        "C2_rank": "The Spearman ρ between the jars' measured AoR and log10 mg/rev at 45° (the 12 jars with August data "
                   "above the floor) is at least as strong as with the handbook values: ρ ≤ −0.84.",
        "C3_inverse": "The line AoR = %.2f − %.2f log10(mg/rev at 45°), fitted on the handbook values, predicts the jars' "
                      "measured AoR with RMSE below %.1f° once one common offset (the difference between methods) is "
                      "removed; refitted leave-one-jar-out on the measured values, also below %.1f°." %
                      (b0, abs(b1), invm["line"]["lopo_rmse_deg"], invm["line"]["lopo_rmse_deg"]),
        "C4_dem_within_conveying": "Among the 7 jars that convey, the measured AoR rises with the DEM path's value "
                                   "(Spearman ρ ≥ +0.71, one-sided p < 0.05 for 7 jars). The DEM reads their spread in "
                                   "solid volume per revolution as a spread in friction; the line reads it as noise "
                                   "(it puts all 7 at 34–35.5°).",
    }
    return rows, criteria

# ------------------------------------------------------------------ 3. solid volume per revolution


def solid_volume(powders, d50):
    cg = json.load(open(os.path.join(HERE, "coarse_graining_check.json")))
    conv = [p for p in powders if p["mg_rev"]["45"] >= THRESH]
    v = {p["powder_id"]: p["mg_rev"]["45"] / (p["rho_p"] / 1000.0) for p in conv}       # mm3 of solid per rev
    vb = {p["powder_id"]: p["mg_rev"]["45"] / (p["rho_b"] / 1000.0) for p in conv}      # mm3 of handbook bulk per rev
    vals = np.array(list(v.values()))
    med = float(np.median(vals))
    cluster = sorted((k for k, x in v.items() if abs(x / med - 1) <= 0.06), key=lambda k: v[k])
    twin = {d: cg[f"d45_P1{s}"]["0.25-0.49"] / (P.RHO_SALT / 1000.0) for d, s in ((0.425, ""), (0.35, "_d035"))}
    # Beverloo slot through the annulus, (b - k d)^1.5, with k chosen to pass through the twin's two grain sizes
    ratio = twin[0.35] / twin[0.425]
    rr = ratio ** (1 / 1.5)
    k = (rr - 1) * ANNULUS_MM / (rr * 0.425 - 0.35)
    bev = lambda d_mm: twin[0.425] * (max(ANNULUS_MM - k * d_mm, 0) / (ANNULUS_MM - k * 0.425)) ** 1.5
    grains = {p["powder_id"]: [round(ANNULUS_MM * 1000 / d50[p["powder_id"]][1], 1), round(ANNULUS_MM * 1000 / p["d50_um"], 1),
                               round(ANNULUS_MM * 1000 / d50[p["powder_id"]][0], 1)] for p in powders}
    return {"solid_mm3_per_rev_45": {k_: round(x, 1) for k_, x in v.items()},
            "handbook_bulk_mm3_per_rev_45": {k_: round(x, 1) for k_, x in vb.items()},
            "median_mm3": round(med, 1), "cv_solid": round(float(np.std(vals, ddof=1) / np.mean(vals)), 3),
            "cv_bulk": round(float(np.std(list(vb.values()), ddof=1) / np.mean(list(vb.values()))), 3),
            "within_6pct_of_median": cluster,
            "spearman_solid_volume_vs_d50": round(float(stats.spearmanr([v[p["powder_id"]] for p in conv],
                                                                         [p["d50_um"] for p in conv])[0]), 3),
            "twin_solid_mm3_per_rev_45": {str(d): round(x, 1) for d, x in twin.items()},
            "twin_ratio_0p35_over_0p425": round(ratio, 3),
            "beverloo_k_through_twin": round(k, 3),
            "beverloo_through_twin_mm3": {str(d): round(bev(d), 1) for d in (0.042, 0.09, 0.106, 0.2, 0.3, 0.425, 0.5)},
            "grains_across_annulus_coarse_best_fine": grains}, bev

# --------------------------------------------------------------- 4. a powder that was never dosed


def fit_all12(powders, chain):
    a = np.array([p["aor"] for p in powders])
    fits = {}
    for key in P.TILTS:
        y = np.array([P.logy(p["mg_rev"][key]) for p in powders])
        b = P.ols(a, y)
        shifts = np.arange(-10.0, 15.01, 0.25)
        sse = [np.sum((np.array([chain.predict(p, key, shift=s)[0] for p in powders]) - y) ** 2) for s in shifts]
        fits[key] = {"line": [float(b[0]), float(b[1])], "dem_shift": float(shifts[int(np.argmin(sse))]),
                     "iso": P.isotonic_decreasing(a, y)}
    return fits


def new_powder(aor_deg, rho_g_cm3, powders, chain, fits=None, solid_mm3=None):
    fits = fits or fit_all12(powders, chain)
    p = {"aor": aor_deg, "rho_p": rho_g_cm3 * 1000.0}
    out = {}
    for key, f in fits.items():
        out[key] = {"line_mg_rev": round(10 ** (f["line"][0] + f["line"][1] * aor_deg), 1),
                    "monotone_mg_rev": round(10 ** f["iso"](aor_deg), 1),
                    "dem_chain_mg_rev": round(10 ** chain.predict(p, key, shift=f["dem_shift"])[0], 1),
                    "dem_offset_deg": f["dem_shift"]}
    if solid_mm3:
        out["45"]["if_it_conveys_solid_volume_rule_mg_rev"] = round(solid_mm3 * rho_g_cm3, 0)
    return out

# ----------------------------------------------------------------------------------------- outputs


def figure(powders, rows, spread, sv, bev, d50):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import ligcommon as L
    BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
    fig, axs = plt.subplots(1, 2, figsize=(13.4, 6.2), gridspec_kw={"width_ratios": [1.25, 1]})
    fig.patch.set_facecolor(L.SURF)
    # (a) handbook ranges vs the step, and where each model puts each jar
    ax = axs[0]
    ax.set_facecolor(L.SURF)
    step = spread["step_deg"]
    rr = [r for r in rows if r["aor_range"] is not None]
    n = len(rr)
    n_conv = sum(r["side_of_step"] == "below" for r in rr)
    ax.axvline(step, color=L.INK2, lw=1, ls="--", zorder=1)
    ax.text(step + 0.3, n + 0.5, f"step in the handbook values, {step:g}°", fontsize=7.5, color=L.INK2, va="top")
    for i, r in enumerate(rr):
        yy = n - 1 - i
        conv = r["side_of_step"] == "below"
        ax.plot(r["aor_range"], [yy, yy], color="#c9c8c3", lw=5, solid_capstyle="round", zorder=1)
        ax.scatter([r["aor_handbook"]], [yy], s=44, color=L.INK, zorder=3)
        ax.scatter([r["aor_line"]], [yy + 0.24], s=42, marker="v", color=ORANGE, edgecolor=L.SURF, lw=0.8, zorder=4)
        ax.scatter([r["aor_dem"]], [yy - 0.24], s=42, marker="^", color=BLUE, edgecolor=L.SURF, lw=0.8, zorder=4)
        ax.text(16.6, yy, f"{r['display']}", fontsize=8, color=L.INK, va="center", ha="left")
        ax.text(59.3, yy, f"{r['mg_rev_45_aug']:.3g}", fontsize=8, color=L.INK if conv else L.INK2, va="center", ha="right")
    ax.text(59.3, n - 0.35, "mg/rev\nat 45°", fontsize=7.5, color=L.INK2, ha="right", va="bottom")
    ysep = n - n_conv - 0.5
    ax.axhline(ysep, color="#d9d8d3", lw=1)
    ax.text(57.3, ysep + 0.07, "↑ convey at 45° (≥ 50 mg/rev)", fontsize=7, color=L.INK2, va="bottom", ha="right")
    ax.text(57.3, ysep - 0.07, "↓ do not", fontsize=7, color=L.INK2, va="top", ha="right")
    ax.set_xlim(16.5, 59.5)
    ax.set_ylim(-0.7, n + 0.6)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(FixedLocator([20, 25, 30, 35, 40, 45, 50, 55]))
    ax.set_xlabel("angle of repose (°)", fontsize=9, color=L.INK)
    ax.scatter([], [], s=44, color=L.INK, label="handbook value (grey: published range)")
    ax.scatter([], [], s=42, marker="v", color=ORANGE, label="AoR the line needs")
    ax.scatter([], [], s=42, marker="^", color=BLUE, label="AoR the DEM path needs")
    ax.legend(loc="upper center", fontsize=7.5, frameon=False, ncol=3, bbox_to_anchor=(0.5, -0.1))
    ax.set_title("(a) Handbook angle of repose, and the angle each model needs\nto reproduce the jar's measured mg/rev",
                 fontsize=9.5, color=L.INK)
    L.style_axes(ax)
    for s_ in ("left", "right", "top"):
        ax.spines[s_].set_visible(False)
    # (b) solid volume per revolution of the powders that convey, against grain size
    ax = axs[1]
    ax.set_facecolor(L.SURF)
    conv = [p for p in powders if p["mg_rev"]["45"] >= THRESH]
    dd = np.geomspace(30, 600, 200)
    ax.plot(dd, [bev(d / 1000) for d in dd], color=BLUE, lw=2, zorder=2,
            label="twin's grain-size trend (Beverloo slot through its two points)")
    for d, v in sv["twin_solid_mm3_per_rev_45"].items():
        ax.scatter([float(d) * 1000], [v], s=60, marker="s", color=BLUE, edgecolor=L.SURF, lw=1, zorder=4)
    ax.scatter([], [], s=60, marker="s", color=BLUE, label="DEM twin, salt friction, no cohesion")
    offs = {"alsi10mg": (0, -13, "center"), "xanthan-gum": (-4, -12, "right"), "silicon-110-200": (5, 6, "left"),
            "salt": (-8, -12, "right"), "calcium-lactate": (6, 5, "left"), "sodium-sulfate": (6, 5, "left"),
            "barium-chloride": (-6, 5, "right")}
    for p in conv:
        lo, hi = d50[p["powder_id"]]
        v = sv["solid_mm3_per_rev_45"][p["powder_id"]]
        ax.plot([lo, hi], [v, v], color="#c9c8c3", lw=4, solid_capstyle="round", zorder=1)
        ax.scatter([p["d50_um"]], [v], s=46, color=L.INK, edgecolor=L.SURF, lw=0.8, zorder=3)
        dx, dy, ha = offs.get(p["powder_id"], (6, 5, "left"))
        ax.annotate(SHORT[p["powder_id"]], (p["d50_um"], v), textcoords="offset points", xytext=(dx, dy), fontsize=7.5,
                    color=L.INK2, ha=ha)
    ax.scatter([], [], s=46, color=L.INK, label="measured in Aug (handbook d50; grey: published range)")
    ax.axhspan(sv["median_mm3"] * 0.94, sv["median_mm3"] * 1.06, color="#ecebe6", zorder=0)
    ax.text(31.5, sv["median_mm3"] * 1.075, "± 6 % around the median", fontsize=7, color=L.INK2, va="bottom")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(30, 700)
    ax.set_ylim(40, 1300)
    for axis, ticks in ((ax.xaxis, [30, 50, 100, 200, 300, 500]), (ax.yaxis, [50, 100, 200, 500, 1000])):
        axis.set_major_locator(FixedLocator(ticks))
        axis.set_major_formatter(FixedFormatter([f"{t:g}" for t in ticks]))
        axis.set_minor_locator(NullLocator())
    ax.set_xlabel("grain size d50 (µm)", fontsize=9, color=L.INK)
    ax.set_ylabel("solid volume per revolution at 45° (mm³)\n= mg/rev ÷ particle density", fontsize=8.5, color=L.INK)
    ax.legend(loc="upper center", fontsize=7.5, frameon=False, ncol=1, bbox_to_anchor=(0.5, -0.1))
    ax.set_title("(b) The 7 powders that convey: delivered volume vs. grain size", fontsize=9.5, color=L.INK)
    L.style_axes(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "same_jar.png"), dpi=120, facecolor=L.SURF)
    plt.close(fig)


def tables(rows, criteria, spread, invm, sv, example, d50_best):
    b1 = invm["line"]["b_deg_per_decade"]
    L_ = ["### Predictions for each jar, written before the jars are measured\n",
          f"Line: AoR = {invm['line']['a_deg']:.2f} {'−' if b1 < 0 else '+'} {abs(b1):.2f} × log<sub>10</sub>(mg/rev at 45°), "
          f"fitted on the 12 handbook values (in-sample RMSE {invm['line']['in_sample_rmse_deg']}°, leave-one-out "
          f"{invm['line']['lopo_rmse_deg']}°). DEM: the path position that reproduces the jar's mg/rev at 45° and 22.5° "
          f"(density-corrected), its DEM repose angle plus the mean offset {invm['dem_offset_deg']:+.2f}°. "
          "Both are on the handbook scale; a different AoR method on the jars shifts every value by about the same amount.\n",
          "| jar | handbook AoR (range) | mg/rev at 45°, Aug | side of the step | AoR, line | AoR, DEM path |",
          "|---|---|---|---|---|---|"]
    for r in rows:
        hb = "–" if r["aor_range"] is None else f"{r['aor_handbook']:g}° ({r['aor_range'][0]:g}–{r['aor_range'][1]:g})"
        mg = f"{r['mg_rev_45_aug']:.3g}" + (" (under the 6.1 mg noise floor)" if r["powder_id"] == "fumed-silica" else "")
        L_.append(f"| {r['display']} | {hb} | {mg} | {r['side_of_step']} | {r['aor_line']}° | "
                  f"{'–' if r['aor_dem'] is None else str(r['aor_dem']) + '°'} |")
    L_ += ["", "**Criteria**\n"] + [f"* **{k.split('_')[0]}** {v}" for k, v in criteria.items()]
    L_ += ["", "### Handbook spread\n",
           f"Published AoR ranges are {spread['width_min_max_median'][0]:g}–{spread['width_min_max_median'][1]:g}° wide "
           f"(median {spread['width_min_max_median'][2]:g}°). Read as the uncertainty in each jar's AoR, that is "
           f"{spread['rms_sd_2sigma_deg']}–{spread['rms_sd_uniform_deg']}° RMS (range = ±2 SD, or uniform). "
           f"{len(spread['ranges_straddling_step'])} of 12 ranges straddle the {spread['step_deg']:g}° step. "
           f"Of the handbook AoR's variance across the 12 powders ({spread['var_handbook_aor_deg2']} deg²), "
           f"{100 * (1 - spread['reliability_2sigma']):.0f}–{100 * (1 - spread['reliability_uniform']):.0f} % would be "
           f"that spread (reliability {spread['reliability_uniform']}–{spread['reliability_2sigma']}). "
           "Correcting the linear AoR trend for that spread (errors in variables) leaves a residual share of the "
           f"scatter of {spread['residual_share_after_spread_uniform']:.2f} to {abs(spread['residual_share_after_spread_2sigma']):.2f}, "
           "i.e. nothing: the spread alone can account for all of it. (n = 12, and the trend is closer to a step than a "
           "line, so read this as \"the handbook data cannot rule out a near-perfect relation\", not as proof of one.)\n",
           "### Solid volume per revolution, the 7 powders that convey (45°, 30 rpm)\n",
           "| powder | mg/rev | ÷ particle density (mm³ solid) | ÷ handbook bulk density (mm³ bulk) | handbook d50 (µm) | grains across the 1.07 mm annulus (coarse–best–fine) |",
           "|---|---|---|---|---|---|"]
    for pid, v in sorted(sv["solid_mm3_per_rev_45"].items(), key=lambda kv: kv[1]):
        r = next(x for x in rows if x["powder_id"] == pid)
        g = sv["grains_across_annulus_coarse_best_fine"][pid]
        L_.append(f"| {r['display']} | {r['mg_rev_45_aug']:.0f} | {v:.0f} | {sv['handbook_bulk_mm3_per_rev_45'][pid]:.0f} | "
                  f"{d50_best[pid]:g} | {g[0]:g}–{g[1]:g}–{g[2]:g} |")
    L_ += ["", f"CV {100 * sv['cv_solid']:.0f} % by particle density, {100 * sv['cv_bulk']:.0f} % by handbook bulk density. "
           f"Within 6 % of the median ({sv['median_mm3']:g} mm³): " + ", ".join(SHORT[k] for k in sv["within_6pct_of_median"]) +
           f". The twin without cohesion: {sv['twin_solid_mm3_per_rev_45']['0.425']:g} mm³ at 0.425 mm and "
           f"{sv['twin_solid_mm3_per_rev_45']['0.35']:g} mm³ at 0.35 mm ({sv['twin_ratio_0p35_over_0p425']}×); a Beverloo slot "
           f"through those two points (k = {sv['beverloo_k_through_twin']}) gives "
           f"{sv['beverloo_through_twin_mm3']['0.042']:g} mm³ at 42 µm.\n",
           "### A powder that has never been dosed\n",
           f"`python same_jar.py new <AoR> <particle density>`, models fitted on all 12. Example, AoR {example['aor']}°, "
           f"{example['rho']} g/cm³ (mg/rev):\n", "```", json.dumps(example["pred"], indent=1), "```", ""]
    with open(os.path.join(HERE, "same_jar_tables.md"), "w") as f:
        f.write("\n".join(L_) + "\n")


def main():
    powders, chain, d50, fumed = load()
    if len(sys.argv) >= 4 and sys.argv[1] == "new":
        sv, _ = solid_volume(powders, d50)
        print(json.dumps(new_powder(float(sys.argv[2]), float(sys.argv[3]), powders, chain, solid_mm3=sv["median_mm3"]), indent=1))
        return
    spread = handbook_spread(powders)
    invm = inverse_all12(powders, chain)
    rows, criteria = jar_predictions(powders, chain, fumed, spread, invm)
    sv, bev = solid_volume(powders, d50)
    fits = fit_all12(powders, chain)
    example = {"aor": 32.0, "rho": 2.70,
               "pred": new_powder(32.0, 2.70, powders, chain, fits=fits, solid_mm3=sv["median_mm3"])}
    out = {"written": "2026-11-04, before any same-jar measurement",
           "source_data": "data/ (Sam's battery @ 963fdba, #163 handbook values @ e7b7964); doser_path.json, aor_path.json",
           "handbook_spread": spread, "inverse_models_all12": {k: v for k, v in invm.items() if k != "per_powder"},
           "jar_predictions": rows, "criteria": criteria, "solid_volume": sv,
           "never_dosed_example": example,
           "dem_offsets_all12_deg": {k: f["dem_shift"] for k, f in fits.items()},
           "line_all12_log10_mg_rev": {k: f["line"] for k, f in fits.items()}}
    with open(os.path.join(HERE, "same_jar_predictions.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    tables(rows, criteria, spread, invm, sv, example, {p["powder_id"]: p["d50_um"] for p in powders})
    figure(powders, rows, spread, sv, bev, d50)
    print(json.dumps({k: out[k] for k in ("handbook_spread", "inverse_models_all12", "criteria")}, indent=1))
    print(json.dumps({k: v for k, v in sv.items() if k != "grains_across_annulus_coarse_best_fine"}, indent=1))
    print(json.dumps(example, indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Campaign report: one figure + a markdown summary (issue #164).

Reads a campaign directory written by ``opt_campaign.py``
(``campaign.json``, ``campaign_records.jsonl``, ``pareto.json``) and
writes, next to them:

* ``campaign_overview.png`` -- every dose in objective space (t_total
  vs |error|, with the observed feasible front and the 180 s / 20 mg
  reference box), plus both objectives dose by dose;
* ``report.md`` -- the dose table, the screening main effects (the 16
  corners of the 2^(8-4) fraction, section 2.4), the tau fit, and the
  recommended parameter set.

Both campaign variants (``campaign.json``'s ``variant``): the
three-stage campaign and the bulk -> tap one (section 6).

    python scripts/opt_report.py data/opt/salt-20260929T014732Z

Recommendation rule (single doses, not validated replicates): among
clean doses (status ok, no jam/spill) inside the reference box, the
knee of the observed front -- the point closest to the origin with
each objective scaled by its threshold.  The model's Pareto set from
pareto.json is listed alongside when the BO phase ran.
"""

import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opt_common as oc                                       # noqa: E402

# Reference palette (dataviz skill): 3 categorical slots max for a
# scatter, text in ink tokens, recessive grid.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
MODE_STYLE = {                       # slot order fixed, never cycled
    "screen": ("#2a78d6", "o", "screening (tau {tau:.2f} s)"),
    "recenter": ("#eb6834", "D", "re-dosed anchors (fitted tau)"),
    "bo": ("#1baf7a", "s", "Bayesian optimization"),
    "validation": ("#1baf7a", "^", "validation"),
}
TITLES = {"bulk_tap": "Bulk taps", "trim_tap": "Trim taps",
          "bulk_tilt_deg": "Bulk tilt (deg)",
          "trickle_tilt_deg": "Trim tilt (deg)",
          "tap_tilt_deg": "Tap tilt (deg)", "bulk_rpm": "Bulk RPM",
          "trickle_start_remaining_g": "Bulk->trim threshold (g)",
          "tolerance_g": "Trim tolerance band (g)",
          "bulk_min_rpm": "Approach (taper floor) RPM",
          "bulk_taper_start_g": "Taper start (g to go)",
          "bulk_stop_margin_g": "Bulk stop margin (g)"}
# Table order, and the dose-table cell, per variant.
FACTORS = {
    oc.VARIANT_THREE_STAGE: (
        "bulk_tap", "trim_tap", "bulk_tilt_deg", "trickle_tilt_deg",
        "tap_tilt_deg", "bulk_rpm", "trickle_start_remaining_g",
        "tolerance_g"),
    oc.VARIANT_BULK_TAP: (
        "bulk_tap", "bulk_tilt_deg", "bulk_rpm", "bulk_min_rpm",
        "bulk_taper_start_g", "bulk_stop_margin_g", "tap_tilt_deg",
        "tolerance_g"),
}
CELL_HEADER = {
    oc.VARIANT_THREE_STAGE: "taps bulk/trim, bulk tilt, trim tilt, tap "
                            "tilt, RPM, threshold g, tol mg",
    oc.VARIANT_BULK_TAP: "bulk taps, bulk tilt, RPM, approach RPM, taper "
                         "start g, stop margin mg, tap tilt, tol mg",
}


def variant(doc):
    return doc.get("variant", oc.VARIANT_THREE_STAGE)


def load(cdir):
    with open(os.path.join(cdir, "campaign.json")) as f:
        doc = json.load(f)
    with open(os.path.join(cdir, "campaign_records.jsonl")) as f:
        records = [json.loads(l) for l in f if l.strip()]
    pareto = None
    path = os.path.join(cdir, "pareto.json")
    if os.path.exists(path):
        with open(path) as f:
            pareto = json.load(f)
    return doc, records, pareto


def usable(r):
    return not r["summary"]["infra_error"] and not r.get("void")


def clean(r):
    s = r["summary"]
    return (usable(r) and s["status"] == "ok" and not s["jam"]
            and not r.get("spill") and s["t_total_s"] is not None
            and s["abs_error_mg"] is not None)


def in_box(r):
    s = r["summary"]
    return (s["t_total_s"] <= oc.THRESHOLD_T_TOTAL_S
            and s["abs_error_mg"] <= oc.THRESHOLD_ABS_ERROR_MG)


def knee(records):
    """Front point closest to the origin in threshold-scaled units."""
    pts = [r for r in records if clean(r) and in_box(r)
           and r["mode"] != "validation"]  # replicates, not candidates
    if not pts:
        return None
    return min(pts, key=lambda r: (
        (r["summary"]["t_total_s"] / oc.THRESHOLD_T_TOTAL_S) ** 2
        + (r["summary"]["abs_error_mg"] / oc.THRESHOLD_ABS_ERROR_MG) ** 2))


def main_effects(records, doc):
    """Mean outcome at each level of each factor over the 16 corners.
    Flagged doses (overshoot/jam) keep their raw values here."""
    bounds = {p["name"]: p.get("bounds")
              for p in oc.search_space_ax(variant(doc))}
    corners = [r for r in records if r["mode"] == "screen" and usable(r)
               and r["label"].startswith("corner-")
               and r["summary"]["t_total_s"] is not None]
    rows = []
    for name in FACTORS[variant(doc)]:
        title = TITLES[name]
        lo, hi = [], []
        for r in corners:
            v = r["params"][name]
            high = (v == oc.CAT_ON) if bounds[name] is None \
                else (v >= sum(bounds[name]) / 2.0)
            (hi if high else lo).append(r["summary"])
        if not lo or not hi:
            continue

        def mean(xs, key):
            vals = [x[key] for x in xs if x[key] is not None]
            return statistics.mean(vals) if vals else None

        # An overshoot ends in seconds, so raw time means would reward
        # it: time is averaged over the doses that ended ok.
        lo_ok = [x for x in lo if x["status"] == "ok"]
        hi_ok = [x for x in hi if x["status"] == "ok"]
        rows.append({
            "factor": title,
            "levels": ("off / 2 Hz" if bounds[name] is None else
                       "{:g} / {:g}".format(*bounds[name])),
            "n": (len(lo), len(hi)),
            "t_lo": mean(lo_ok, "t_total_s"), "t_hi": mean(hi_ok, "t_total_s"),
            "n_ok": (len(lo_ok), len(hi_ok)),
            "e_lo": mean(lo, "abs_error_mg"),
            "e_hi": mean(hi, "abs_error_mg"),
            "flag_lo": sum(1 for x in lo if x["status"] != "ok"),
            "flag_hi": sum(1 for x in hi if x["status"] != "ok"),
        })
    return rows, len(corners)


def fmt(v, spec="{:.1f}"):
    return "-" if v is None else spec.format(v)


def params_cell(p):
    if oc.variant_of(p) == oc.VARIANT_BULK_TAP:
        return ("{bulk_tap}, {bulk_tilt_deg:.1f}, {bulk_rpm:.0f}, "
                "{bulk_min_rpm:.0f}, {bulk_taper_start_g:.3f}, {margin:.1f}, "
                "{tap_tilt_deg:.1f}, {tol:.1f}").format(
                    margin=1000.0 * p["bulk_stop_margin_g"],
                    tol=1000.0 * p["tolerance_g"], **p)
    return ("{bulk_tap}/{trim_tap}, {bulk_tilt_deg:.1f}, "
            "{trickle_tilt_deg:.1f}, {tap_tilt_deg:.1f}, {bulk_rpm:.0f}, "
            "{trickle_start_remaining_g:.3f}, {tol:.1f}").format(
                tol=1000.0 * p["tolerance_g"], **p)


def figure(doc, records, pick, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": INK_2, "axes.labelcolor": INK,
        "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK,
        "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
        "axes.spines.top": False, "axes.spines.right": False})
    fig = plt.figure(figsize=(11.5, 5.2))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1.0], hspace=0.12,
                          wspace=0.22)
    ax = fig.add_subplot(gs[:, 0])
    at = fig.add_subplot(gs[0, 1])
    ae = fig.add_subplot(gs[1, 1], sharex=at)

    dosed = [r for r in records if usable(r)
             and r["summary"]["t_total_s"] is not None
             and r["summary"]["abs_error_mg"] is not None]
    floor = 0.3                                   # log axis floor, mg
    seen = set()
    screen_tau = (doc.get("frozen_params") or {}).get("tau_afterflow_s",
                                                      0.30)
    for r in dosed:
        color, marker, label = MODE_STYLE.get(r["mode"],
                                              MODE_STYLE["screen"])
        label = label.format(tau=screen_tau)
        s = r["summary"]
        ok = clean(r)
        lab = None
        key = (r["mode"], ok)
        if key not in seen:
            seen.add(key)
            lab = label if ok else "{}: overshoot or jam".format(
                label.split(" (")[0])
        kw = dict(s=46, marker=marker, linewidths=1.6, zorder=3,
                  edgecolors=color if not ok else color,
                  facecolors=color if ok else "none", label=lab)
        ax.scatter(s["t_total_s"], max(s["abs_error_mg"], floor), **kw)
        for a, y in ((at, s["t_total_s"]),
                     (ae, max(s["abs_error_mg"], floor))):
            a.scatter(r["trial_index"], y, **dict(kw, s=26, label=None))
        if r["label"].startswith(("baseline-", "rebaseline-")):
            ax.scatter(s["t_total_s"], max(s["abs_error_mg"], floor),
                       s=150, marker="o", facecolors="none",
                       edgecolors=INK_2, linewidths=1.0, zorder=2,
                       label=("hand-tuned baseline (ring)"
                              if "base" not in seen else None))
            seen.add("base")

    # observed feasible front (clean, inside the box), as a step line;
    # validation replicates are plotted, but they are not candidates
    pts = sorted((r["summary"]["t_total_s"], r["summary"]["abs_error_mg"])
                 for r in dosed if clean(r) and in_box(r)
                 and r["mode"] != "validation")
    front, best = [], float("inf")
    for t, e in pts:
        if e < best:
            front.append((t, max(e, floor)))
            best = e
    if front:
        xs, ys = [front[0][0]], [front[0][1]]
        for t, e in front[1:]:
            xs += [t, t]
            ys += [ys[-1], e]
        ax.plot(xs, ys, color=INK_2, lw=1.2, zorder=1,
                label="observed front (clean doses in the box)")
    ax.axvline(oc.THRESHOLD_T_TOTAL_S, color=INK_2, lw=0.8, ls="--")
    ax.axhline(oc.THRESHOLD_ABS_ERROR_MG, color=INK_2, lw=0.8, ls="--")
    ax.text(oc.THRESHOLD_T_TOTAL_S, 0.99, " 180 s",
            transform=ax.get_xaxis_transform(), color=INK_2, fontsize=8,
            va="top")
    if pick is not None:
        # Nothing observed dominates a front point, so the space below
        # and left of it is empty: the label goes there.
        s = pick["summary"]
        ax.annotate("best single dose: {}\n{:.0f} s, {:.1f} mg".format(
            pick["label"], s["t_total_s"], s["abs_error_mg"]),
            (s["t_total_s"], max(s["abs_error_mg"], floor)),
            xytext=(0.36, 0.05), textcoords="axes fraction", fontsize=8,
            ha="left", color=INK, arrowprops=dict(
                arrowstyle="-", color=INK_2, lw=0.8))
    ax.set_yscale("log")
    ax.set_xlabel("t_total (s), dose start to settled reading")
    ax.set_ylabel("|error| (mg) vs the 0.5 g target (log)")
    ax.grid(True, color=GRID, lw=0.6, zorder=0)
    ax.legend(fontsize=7.5, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.12), ncol=2)
    ax.set_title("Every dose in objective space (lower-left is better)",
                 fontsize=10, loc="left", color=INK)

    at.set_ylabel("t_total (s)")
    ae.set_ylabel("|error| (mg, log)")
    ae.set_yscale("log")
    ae.set_xlabel("dose index (campaign order)")
    for a, thr in ((at, oc.THRESHOLD_T_TOTAL_S),
                   (ae, oc.THRESHOLD_ABS_ERROR_MG)):
        a.axhline(thr, color=INK_2, lw=0.8, ls="--")
        a.grid(True, color=GRID, lw=0.6, zorder=0)
    plt.setp(at.get_xticklabels(), visible=False)
    at.set_title("Both objectives, dose by dose (dashed: 180 s / 20 mg "
                 "thresholds)", fontsize=10, loc="left", color=INK)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def report(cdir):
    doc, records, pareto = load(cdir)
    pick = knee(records)
    fig_path = os.path.join(cdir, "campaign_overview.png")
    try:
        figure(doc, records, pick, fig_path)
    except ImportError:                 # the laptop's Ax stack lacks it
        print("matplotlib is not installed: report.md only (pip install "
              "matplotlib for the figure)")
        fig_path = None
    effects, n_corners = main_effects(records, doc)

    L = []
    L.append("# Campaign {}\n".format(doc["campaign_id"]))
    if variant(doc) == oc.VARIANT_BULK_TAP:
        L.append("- **bulk -> tap** campaign: no PI trickle; the bulk halts "
                 "on a predicted final mass and the taps finish")
    L.append("- powder `{}`, target {} g, status **{}**{}".format(
        doc["powder_id"], doc["target_g"], doc["status"],
        " ({})".format(doc["stop_reason"]) if doc.get("stop_reason")
        else ""))
    counts = {}
    for r in records:
        counts[r["mode"]] = counts.get(r["mode"], 0) + 1
    L.append("- {} doses: {}".format(len(records), ", ".join(
        "{} {}".format(v, k) for k, v in counts.items())))
    tau = doc.get("tau_afterflow") or {}
    if tau.get("tau0_s"):
        L.append("- tau_afterflow fit: {} s ({} model, {} stop events, "
                 "rates {}-{} g/s)".format(
                     tau["tau0_s"], tau.get("model"), tau.get("n_events"),
                     *(tau.get("rate_range_gps") or ["?", "?"])))
    loads = [r["covariates"].get("cup_load_g") for r in records
             if (r.get("covariates") or {}).get("cup_load_g") is not None]
    last = records[-1]["summary"].get("settled_final_g") if records else None
    if loads:
        L.append("- powder in the cup at the end: {:.2f} g".format(
            loads[-1] + max(0.0, last or 0.0)))
    L.append("")
    if pick is not None:
        s = pick["summary"]
        L.append("## Best observed dose (knee of the observed front)\n")
        L.append("`{}` ({}): t_total {:.1f} s, |error| {:.1f} mg, a single "
                 "dose, not yet validated with replicates.\n".format(
                     pick["label"], pick["mode"], s["t_total_s"],
                     s["abs_error_mg"]))
        L.append("```json\n{}\n```\n".format(json.dumps(
            dict(pick["params"]), indent=1)))
    if pareto and pareto.get("model_pareto"):
        labels = oc.ax_trial_labels(records)
        L.append("## Model Pareto set (Ax, predicted means)\n")
        L.append("The dose column is the label `--validate-point` takes.\n")
        L.append("| Ax trial | dose | t_total (s) | abs_error (mg) | {} |"
                 .format(CELL_HEADER[variant(doc)]))
        L.append("|---|---|---|---|---|")
        for m in pareto["model_pareto"]:
            pm = m["predicted_means"]
            L.append("| {} | {} | {} | {} | {} |".format(
                m["trial_index"],
                m.get("label") or labels.get(m["trial_index"], "-"),
                fmt(pm.get("t_total_s")), fmt(pm.get("abs_error_mg")),
                params_cell(m["params"])))
        L.append("")
    if doc.get("profiles"):
        L.append("## Validation blocks\n")
        L.append("One `dosing_profiles` document each; `dose.py` doses the "
                 "newest validated one unless `--profile` names another.\n")
        L.append("| profile_id | point | {} | clean / replicates | median "
                 "abs_error (mg) | p95 (mg) | P(<= 10 mg) | median t_total "
                 "(s) | validated |".format(CELL_HEADER[variant(doc)]))
        L.append("|---|---|---|---|---|---|---|---|---|")
        for p in doc["profiles"]:
            v = p.get("validation") or {}
            L.append("| {} | {} | {} | {} / {} | {} | {} | {} | {} | {} |"
                     .format(p["profile_id"], p.get("point") or "-",
                             params_cell(p["parameters"]), v.get("clean"),
                             v.get("replicates"),
                             fmt(v.get("median_abs_error_mg")),
                             fmt(v.get("p95_abs_error_mg")),
                             fmt(v.get("p_within_10mg"), "{:.2f}"),
                             fmt(v.get("median_t_total_s")),
                             p["validated"]))
        L.append("")
    if effects:
        L.append("## Screening main effects ({} corners)\n"
                 .format(n_corners))
        L.append("8 corners sit at each level of every factor. Time is "
                 "averaged over the corners that ended `ok` (an overshoot "
                 "ends in seconds and would look fast); |error| is averaged "
                 "over all of them.\n")
        L.append("| Factor | low / high | mean t_total of ok doses, low -> "
                 "high (s) | mean abs_error, low -> high (mg) | overshoot "
                 "or jam, low / high |")
        L.append("|---|---|---|---|---|")
        for e in effects:
            L.append("| {} | {} | {} (n={}) -> {} (n={}) | {} -> {} | "
                     "{} / {} |".format(
                         e["factor"], e["levels"], fmt(e["t_lo"]),
                         e["n_ok"][0], fmt(e["t_hi"]), e["n_ok"][1],
                         fmt(e["e_lo"]), fmt(e["e_hi"]), e["flag_lo"],
                         e["flag_hi"]))
        L.append("")
    L.append("## Every dose\n")
    L.append("| # | label | {} | status | t_total (s) | error (mg) "
             "| taps |".format(CELL_HEADER[variant(doc)]))
    L.append("|---|---|---|---|---|---|---|")
    for r in records:
        s = r["summary"]
        L.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            r["trial_index"], r["label"], params_cell(r["params"]),
            s["status"], fmt(s["t_total_s"]),
            fmt(s.get("error_mg"), "{:+.1f}"),
            "-" if s.get("taps") is None else s["taps"]))
    L.append("")
    L.append("![overview](campaign_overview.png)")
    with open(os.path.join(cdir, "report.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    return pick, fig_path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("campaign_dir")
    args = ap.parse_args(argv)
    pick, fig = report(args.campaign_dir)
    print("wrote {}report.md; recommended: {}".format(
        fig + " and " if fig else "", pick["label"] if pick else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())

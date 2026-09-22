#!/usr/bin/env python3
"""Per-powder tau_afterflow fit from dose stop events (issue #164 §2.8).

Every dose emits two stop events at very different rates (the bulk halt
and the trickle cutoff), so a screening block yields ~40 free
(rate, afterflow) points.  This fits the zero-intercept model

    afterflow(mdot) = tau0 * mdot + tau1 * mdot**2      [tau(mdot) = tau0 + tau1*mdot]

-- "afterflow as a function of mass rate" -- keeping the quadratic term
only when it is statistically real (|t| > 2, n >= 10); otherwise the
saved value is the robust (median-ratio) scalar tau0, which is what
PR #131's pooled data says fits well (r = 0.95, salt tau = 0.83 s).

The fit is saved per powder to the ``powder_models`` collection (and a
local cache) and pushed to the rig as ``set tau_afterflow_s`` from the
BO phase onward by opt_campaign.py, replacing the firmware's hardcoded
0.30 s guess.

CLI (the campaign calls ``fit_events`` directly):

    python scripts/fit_tau_afterflow.py --campaign-id salt-2026... \
        [--powder-id salt --upsert] [--plot data/opt/<cid>/tau_fit.png]

Stdlib-only for the fit; matplotlib only under ``--plot``.
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opt_common as oc                                       # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STATE = os.path.join(REPO_ROOT, "data", "opt")
MODEL_CACHE = os.path.join(REPO_ROOT, "data", "powder_models")

MIN_RATE_GPS = 0.002          # below this the ratio is numerically junk


def usable_events(events):
    """(rate, afterflow, phase) triples worth fitting.

    Rate prefers the KF estimate (trickle cutoffs) and falls back to
    the trailing-poll slope (bulk halts); stalled halts carry no flow
    and are excluded, as are negative-afterflow outliers beyond -2 mg
    (a settling artifact, not physics).
    """
    out = []
    for ev in events or []:
        if ev.get("stalled"):
            continue
        rate = ev.get("rate_kf_gps")
        if rate is None:
            rate = ev.get("rate_slope_gps")
        after = ev.get("afterflow_g")
        if rate is None or after is None or rate < MIN_RATE_GPS:
            continue
        if after < -0.002:
            continue
        out.append((float(rate), float(after),
                    ev.get("phase", "?")))
    return out


def fit_events(events):
    """-> the powder_models tau block (see module docstring)."""
    pts = usable_events(events)
    n = len(pts)
    if n < 4:
        return {"tau0_s": None, "tau1_s_per_gps": None, "n_events": n,
                "note": "not enough usable stop events (need >= 4)"}
    ratios = sorted(a / r for r, a, _ in pts)
    tau0_median = ratios[n // 2] if n % 2 else 0.5 * (
        ratios[n // 2 - 1] + ratios[n // 2])

    # Least squares for afterflow = t0*r + t1*r^2 (no intercept).
    s_rr = sum(r * r for r, _a, _p in pts)
    s_r3 = sum(r ** 3 for r, _a, _p in pts)
    s_r4 = sum(r ** 4 for r, _a, _p in pts)
    s_ra = sum(r * a for r, a, _p in pts)
    s_r2a = sum(r * r * a for r, a, _p in pts)
    det = s_rr * s_r4 - s_r3 * s_r3
    tau1 = tau1_se = None
    t0_ls = t1_ls = None
    if det > 1e-18:
        t0_ls = (s_r4 * s_ra - s_r3 * s_r2a) / det
        t1_ls = (s_rr * s_r2a - s_r3 * s_ra) / det
        resid = [a - t0_ls * r - t1_ls * r * r for r, a, _p in pts]
        dof = max(1, n - 2)
        sigma2 = sum(e * e for e in resid) / dof
        tau1_se = math.sqrt(max(0.0, sigma2 * s_rr / det))
        tau1 = t1_ls
    keep_quadratic = (tau1 is not None and tau1_se and n >= 10
                      and abs(tau1) / tau1_se > 2.0)
    if keep_quadratic:
        tau0, model = t0_ls, "quadratic"
    else:
        tau0, tau1, model = tau0_median, None, "linear"
    resid = [a - tau0 * r - (tau1 or 0.0) * r * r for r, a, _p in pts]
    rms_mg = 1000.0 * math.sqrt(sum(e * e for e in resid) / n)
    rates = [r for r, _a, _p in pts]
    return {
        "tau0_s": round(tau0, 4),
        "tau1_s_per_gps": round(tau1, 4) if tau1 is not None else None,
        "tau1_t_stat": (round(abs(t1_ls) / tau1_se, 2)
                        if tau1_se else None),
        "tau0_median_s": round(tau0_median, 4),
        "model": model,
        "n_events": n,
        "rate_range_gps": [round(min(rates), 4), round(max(rates), 4)],
        "resid_rms_mg": round(rms_mg, 2),
    }


def upsert_powder_model(powder_id, fit, campaign_id=None,
                        cache_dir=None, upload=True):
    """powder_models document (Mongo + local cache); returns cache path.

    ``cache_dir`` overrides the repo-level cache -- used by
    ``opt_campaign.py --simulate`` so sim fits can never shadow a real
    powder model.
    """
    doc = {
        "kind": "powder_model",
        "schema_version": oc.SCHEMA_VERSION,
        "powder_id": powder_id,
        "tau_afterflow": fit,
        "source_campaign": campaign_id,
        "updated_utc": oc.utcnow_iso(),
    }
    cache_dir = cache_dir or MODEL_CACHE
    os.makedirs(cache_dir, exist_ok=True)
    cache = os.path.join(cache_dir, "{}.json".format(powder_id))
    with open(cache, "w") as f:
        json.dump(doc, f, indent=1)
    if upload:
        db = oc.mongo_db()
        if db is not None:
            db[oc.COLL_POWDER_MODELS].replace_one(
                {"powder_id": powder_id}, doc, upsert=True)
    return cache


# ---------------------------------------------------------------------------
# Event sources + CLI
# ---------------------------------------------------------------------------

def events_from_records(records):
    """Stop events from campaign trials.jsonl lines (jam/spill doses
    excluded, per section 2.8)."""
    events = []
    for rec in records:
        summary = rec.get("summary", rec)
        if summary.get("jam") or rec.get("spill"):
            continue
        if summary.get("infra_error"):
            continue
        events += rec.get("stop_events") or summary.get("stop_events") \
            or []
    return events


def load_campaign_events(state_dir, campaign_id):
    """Prefer the laptop's campaign ledger; fall back to the executor
    spool (same summary shape, minus the spill flag)."""
    root = os.path.join(state_dir, campaign_id)
    for name in ("campaign_records.jsonl", "trials.jsonl"):
        path = os.path.join(root, name)
        if os.path.exists(path):
            with open(path) as f:
                return events_from_records([json.loads(l) for l in f
                                            if l.strip()])
    raise SystemExit("no trial records under {}".format(root))


def plot_fit(events, fit, out_png):
    """Diagnostic scatter: afterflow vs rate, one point per stop event,
    with the fitted curve.  Static PNG for the campaign folder."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    SURFACE = "#fcfcfb"
    INK, INK2 = "#0b0b0b", "#52514e"
    BULK, TRICKLE = "#2a78d6", "#eb6834"    # categorical slots 1-2

    pts = usable_events(events)
    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for phase, color, label in (("bulk", BULK, "bulk halt"),
                                ("trickle", TRICKLE, "trickle cutoff")):
        xs = [r for r, _a, p in pts if p == phase]
        ys = [1000.0 * a for r, a, p in pts if p == phase]
        ax.scatter(xs, ys, s=45, facecolor=color, edgecolor=SURFACE,
                   linewidth=1.0, label=label, zorder=3)
    if fit.get("tau0_s") is not None and pts:
        rmax = max(r for r, _a, _p in pts) * 1.05
        xs = [rmax * i / 100.0 for i in range(101)]
        t0, t1 = fit["tau0_s"], fit.get("tau1_s_per_gps") or 0.0
        ax.plot(xs, [1000.0 * (t0 * x + t1 * x * x) for x in xs],
                color=INK, linewidth=2.0, zorder=2,
                label="fit: tau0={:.2f} s{}".format(
                    t0, ", tau1={:.2f}".format(t1) if t1 else ""))
    ax.set_xlabel("mass rate at stop (g/s)", color=INK)
    ax.set_ylabel("afterflow (mg)", color=INK)
    ax.set_title("afterflow vs rate -- tau_afterflow fit "
                 "({} events, rms {} mg)".format(fit.get("n_events"),
                                                 fit.get("resid_rms_mg")),
                 color=INK, fontsize=11)
    ax.tick_params(colors=INK2)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(INK2)
    ax.grid(True, color=INK2, alpha=0.15, linewidth=0.8)
    ax.set_axisbelow(True)
    legend = ax.legend(frameon=False, fontsize=9)
    for text in legend.get_texts():
        text.set_color(INK)
    fig.tight_layout()
    fig.savefig(out_png, facecolor=SURFACE)
    plt.close(fig)
    return out_png


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--campaign-id", required=True)
    ap.add_argument("--state-dir", default=DEFAULT_STATE)
    ap.add_argument("--powder-id")
    ap.add_argument("--upsert", action="store_true",
                    help="save to powder_models (Mongo + local cache)")
    ap.add_argument("--plot", metavar="PNG",
                    help="write the diagnostic scatter here")
    args = ap.parse_args(argv)

    events = load_campaign_events(args.state_dir, args.campaign_id)
    fit = fit_events(events)
    print(json.dumps(fit, indent=1))
    if args.plot:
        print("plot -> " + plot_fit(events, fit, args.plot))
    if args.upsert:
        if not args.powder_id:
            raise SystemExit("--upsert needs --powder-id")
        cache = upsert_powder_model(
            oc.normalize_powder_id(args.powder_id), fit,
            args.campaign_id)
        print("powder model cached -> " + cache)
    return 0


if __name__ == "__main__":
    sys.exit(main())

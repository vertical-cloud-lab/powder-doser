#!/usr/bin/env python3
"""Figure for campaign-setup.md section 6: the bulk -> tap campaign next
to the three-stage one, both on the virtual plant (not rig data).

Left: every modeled dose of each campaign in objective space, with each
campaign's observed feasible front.  Right: where a clean dose's time
goes, stage by stage (medians).

    python scripts/opt_campaign.py --powder-id salt --simulate \
        --variant bulk-tap --model moo --budget 14 --state-dir /tmp/simcamp/bt
    python scripts/opt_campaign.py --powder-id salt --simulate \
        --model moo --budget 14 --state-dir /tmp/simcamp/ts
    python docs/optimization/make_bulk_tap_sim_figure.py \
        /tmp/simcamp/bt/salt-bulktap-<stamp> /tmp/simcamp/ts/salt-<stamp> \
        docs/optimization/bulk-tap-sim-comparison.png

Reads only the campaign directories (campaign.json,
campaign_records.jsonl, and the spooled trial_<uuid>.json documents for
the per-stage times).
"""

import json
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e7e6e2"
BLUE, ORANGE = "#2a78d6", "#eb6834"                    # slots 1-2
T_MAX, E_MAX = 180.0, 20.0                             # reference box
FLOOR = 0.3                                            # log-axis floor, mg
STAGES = (("t_bulk_s", "bulk"), ("t_trickle_s", "PI trickle"),
          ("t_tap_s", "taps"), ("t_settle_s", "final settle"))


def load(campaign_dir):
    with open(os.path.join(campaign_dir, "campaign.json")) as f:
        doc = json.load(f)
    with open(os.path.join(campaign_dir, "campaign_records.jsonl")) as f:
        records = [json.loads(l) for l in f if l.strip()]
    outcomes = {}
    for name in os.listdir(campaign_dir):
        if name.startswith("trial_") and name.endswith(".json"):
            with open(os.path.join(campaign_dir, name)) as f:
                trial = json.load(f)
            outcomes[trial["trial_uuid"]] = trial["outcomes"]
    return doc, records, outcomes


def modeled(r):
    s = r["summary"]
    return (not s["infra_error"] and not r.get("void")
            and s["t_total_s"] is not None and s["abs_error_mg"] is not None)


def clean(r):
    s = r["summary"]
    return modeled(r) and s["status"] == "ok" and not s["jam"]


def front(records):
    pts = sorted((r["summary"]["t_total_s"], r["summary"]["abs_error_mg"])
                 for r in records if clean(r)
                 and r["summary"]["t_total_s"] <= T_MAX
                 and r["summary"]["abs_error_mg"] <= E_MAX)
    out, best = [], float("inf")
    for t, e in pts:
        e = max(e, FLOOR)           # on the plotted (floored) scale
        if e < best:
            out.append((t, e))
            best = e
    return out


def main(bt_dir, ts_dir, out_path):
    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": TEXT_2, "axes.labelcolor": TEXT,
        "xtick.color": TEXT_2, "ytick.color": TEXT_2, "text.color": TEXT,
        "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
        "axes.spines.top": False, "axes.spines.right": False})
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11.5, 4.6),
                                 gridspec_kw={"width_ratios": [1.45, 1.0],
                                              "wspace": 0.28})
    campaigns = [
        ("bulk → tap (no PI trickle)", BLUE, "o") + load(bt_dir),
        ("three-stage (bulk → PI trickle → taps)", ORANGE, "s")
        + load(ts_dir),
    ]
    for label, color, marker, doc, records, _o in campaigns:
        dosed = [r for r in records if modeled(r)]
        ok = [r for r in dosed if clean(r)]
        bad = [r for r in dosed if not clean(r)]
        ax.scatter([r["summary"]["t_total_s"] for r in ok],
                   [max(r["summary"]["abs_error_mg"], FLOOR) for r in ok],
                   s=46, marker=marker, color=color, edgecolors=SURFACE,
                   linewidths=0.8, zorder=3,
                   label="{}: {} clean doses".format(label, len(ok)))
        ax.scatter([r["summary"]["t_total_s"] for r in bad],
                   [max(r["summary"]["abs_error_mg"], FLOOR) for r in bad],
                   s=46, marker=marker, facecolors="none", edgecolors=color,
                   linewidths=1.4, zorder=3,
                   label="{}: {} overshoot or jam".format(
                       label.split(" (")[0], len(bad)))
        pts = front(records)
        if pts:
            xs, ys = [pts[0][0]], [pts[0][1]]
            for t, e in pts[1:]:
                xs += [t, t]
                ys += [ys[-1], e]
            ax.plot(xs, ys, color=color, lw=2.0, zorder=2, alpha=0.9)
    ax.axvline(T_MAX, color=TEXT_2, lw=0.8, ls="--")
    ax.axhline(E_MAX, color=TEXT_2, lw=0.8, ls="--")
    ax.set_yscale("log")
    ax.set_xlim(0, None)
    ax.set_xlabel("t_total (s), dose start to settled reading")
    ax.set_ylabel("|error| (mg) vs the 0.5 g target (log)")
    ax.grid(True, color=GRID, lw=0.6, zorder=0)
    ax.legend(fontsize=7.5, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.13), ncol=2)
    ax.set_title("Every modeled dose; lines: front of the clean doses (ok, "
                 "inside 180 s / 20 mg)",
                 fontsize=10, loc="left", color=TEXT)

    width = 0.36
    for i, (label, color, marker, doc, records, outcomes) in enumerate(
            campaigns):
        meds = []
        for key, _name in STAGES:
            vals = [outcomes[r["trial_uuid"]].get(key) or 0.0
                    for r in records if clean(r)
                    and r["trial_uuid"] in outcomes]
            meds.append(statistics.median(vals) if vals else 0.0)
        xs = [j + (i - 0.5) * width for j in range(len(STAGES))]
        bx.bar(xs, meds, width=width - 0.04, color=color, zorder=2,
               label=label.split(" (")[0])
        for x, m in zip(xs, meds):
            bx.text(x, m + 1.0, "{:.0f}".format(m), ha="center",
                    va="bottom", fontsize=8, color=TEXT_2)
    bx.set_xticks(range(len(STAGES)))
    bx.set_xticklabels([name for _k, name in STAGES])
    bx.set_ylabel("median seconds per clean dose")
    bx.grid(True, axis="y", color=GRID, lw=0.6, zorder=0)
    bx.set_ylim(0, 1.18 * bx.get_ylim()[1])
    bx.legend(fontsize=7.5, frameon=False, loc="upper left")
    bx.set_title("Where a clean dose's time goes", fontsize=10, loc="left",
                 color=TEXT)
    fig.suptitle("Simulated campaigns on the virtual plant (salt-like, "
                 "0.5 g target) -- illustrative, not rig data",
                 fontsize=10.5, x=0.01, ha="left", color=TEXT)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out_path)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])

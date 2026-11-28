#!/usr/bin/env python3
"""Where the PI trickle hands over to the taps, and what a smaller
cutoff margin could save -- campaign salt-20260929T014732Z plus its
2026-10-06 validation blocks (PR #166, 2026-10-08).

    python3 data/opt/salt-20260929T014732Z/plot_tap_margin.py [out png]

Left: target minus the settled reading after the trickle cutoff, one dot
per dose in which the PI ran, grouped by trim tilt.  The firmware aims
the trickle's predicted final mass ``CUTOFF_MARGIN_G`` (35 mg) short of
the target.

Right: the validated point bo-005 (8 replicates with telemetry, measured
at 35 mg) and an ESTIMATE of its dose time at smaller margins.  Each
replicate's own tap stage is replayed from a handover (35 - margin) mg
closer, two ways: the taps deliver like the FIRST taps of that dose's
real tap stage (the lip as charged as right after the PI), or like its
LAST taps (as depleted as at the end).  The PI's extra (35 - margin) mg
is charged at its cutoff rate.  Assumes the PI lands the same distance
from its aim wherever the aim is; only doses at the new margin can
confirm that.
"""

import json
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e7e6e2"
BLUE, ORANGE = "#2a78d6", "#eb6834"                    # slots 1-2
MARGIN_MG = 35.0                                       # CUTOFF_MARGIN_G
MARGINS = (35, 25, 15, 10, 5, 0)
GROUPS = (("10°", lambda t: t <= 10.0), ("13–15°", lambda t: 10 < t <= 15),
          ("20–22.5°", lambda t: 15 < t <= 25), ("30°", lambda t: t > 25))


def load(campaign_dir):
    with open(os.path.join(campaign_dir, "campaign_records.jsonl")) as f:
        records = [json.loads(l) for l in f if l.strip()]
    out = []
    for r in records:
        path = os.path.join(campaign_dir, "zero",
                            "trial_{}.json".format(r["trial_uuid"]))
        with open(path) as f:
            out.append((r, json.load(f)))
    return out


def trickle_stop(trial):
    evs = [e for e in trial["stop_events"] if e.get("phase") == "trickle"]
    return evs[-1] if evs else None


def pi_ran(trial):
    """The PI actually fed powder: a non-stalled cutoff at a real rate
    (corner-09's trickle often started inside the margin and halted on
    its first poll at zero rate)."""
    ev = trickle_stop(trial)
    return bool(ev and not ev.get("stalled")
                and (ev.get("rate_kf_gps") or 0.0) > 0.002)


def replay(trial, tol_mg, margin):
    """(t_total_s estimates (first-taps, last-taps)) for one dose re-run
    with the trickle aiming ``margin`` mg short instead of 35."""
    tel = trial.get("telemetry") or {}
    head = tel["header"].split(",")
    rows = [dict(zip(head, x.split(","))) for x in tel["rows"]]
    t_end_tr = [float(x["t_s"]) for x in rows if x["phase"] == "trickle_end"][0]
    r_cut = 1000.0 * float([x for x in rows
                            if x["phase"] == "trickle"][-1]["r_gps"])
    ev = trickle_stop(trial)
    target = trial["target_g"]
    z0 = ev["settled_g"]
    taps = [(float(x["t_s"]) - t_end_tr, float(x["z_g"]))
            for x in rows if x["phase"] == "tap"]
    zs = [z0] + [z for _t, z in taps]
    ts = [0.0] + [t for t, _z in taps]
    inc = [1000.0 * (b - a) for a, b in zip(zs, zs[1:])]
    out = trial["outcomes"]
    before_taps = out["t_total_s"] - out["t_tap_s"]
    handover = 1000.0 * (target - z0) - (MARGIN_MG - margin)
    extra_pi = (MARGIN_MG - margin) / max(5.0, r_cut)
    est = []
    for mode in ("first", "last"):
        if handover <= tol_mg:
            est.append(before_taps + extra_pi)
            continue
        start, t_start = 0, 0.0
        if mode == "last" and margin < MARGIN_MG:
            k = next((i for i, (_t, z) in enumerate(taps)
                      if 1000.0 * (target - z) <= handover), None)
            if k is not None:
                start, t_start = k + 1, taps[k][0]
        cum, t_taps = 0.0, None
        for i in range(start, len(inc)):
            cum += inc[i]
            if handover - cum <= tol_mg:
                t_taps = ts[i + 1] - t_start
                break
        if t_taps is None:                    # real stage ended first:
            step = max(0.3, statistics.median(inc[-5:]))   # keep its
            dt = statistics.median([b - a for a, b in        # last pace
                                    zip(ts[-6:], ts[-5:])])
            t_taps = ts[-1] - t_start
            while handover - cum > tol_mg:
                cum += step
                t_taps += dt
        est.append(before_taps + extra_pi + t_taps)
    return est


def main(out_path):
    campaign_dir = HERE
    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": TEXT_2, "axes.labelcolor": TEXT,
        "xtick.color": TEXT_2, "ytick.color": TEXT_2, "text.color": TEXT,
        "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
        "axes.spines.top": False, "axes.spines.right": False})
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11.5, 4.6),
                                 gridspec_kw={"width_ratios": [1.35, 1.0],
                                              "wspace": 0.25})
    doses = [(r, t) for r, t in load(campaign_dir) if pi_ran(t)]

    # --- left: the handover, by trim tilt ---------------------------------
    ax.axvspan(-90, 0, color=GRID, alpha=0.55, lw=0, zorder=0)
    ax.axvline(0, color=TEXT_2, lw=0.9, zorder=1)
    ax.axvline(MARGIN_MG, color=TEXT_2, lw=0.9, ls="--", zorder=1)
    seen = set()
    ticks = []
    for row, (name, member) in enumerate(GROUPS):
        group = [(r, t) for r, t in doses
                 if member(r["params"]["trickle_tilt_deg"])]
        for i, (r, t) in enumerate(group):
            hand = 1000.0 * (t["target_g"] - trickle_stop(t)["settled_g"])
            bo005 = r["label"] in ("bo-005",) or r["label"].startswith(
                "val-bo-005")
            color = ORANGE if bo005 else BLUE
            taps_on = r["params"]["trim_tap"] != "off"
            y = row + ((i * 0.37) % 1.0 - 0.5) * 0.5
            key = ("bo-005 (campaign dose + 10 validation doses)" if bo005
                   else "other doses, trim taps off" if not taps_on
                   else "other doses, trim taps on (open)")
            ax.scatter([hand], [y], s=40, marker="o",
                       facecolors="none" if taps_on else color,
                       edgecolors=color if taps_on else SURFACE,
                       linewidths=1.4 if taps_on else 0.8, zorder=3,
                       label=None if key in seen else key)
            seen.add(key)
        hands = [1000.0 * (t["target_g"] - trickle_stop(t)["settled_g"])
                 for _r, t in group]
        ticks.append("{}\nn={}, median {:.0f} mg".format(
            name, len(hands), statistics.median(hands)))
    ax.set_yticks(range(len(GROUPS)))
    ax.set_yticklabels(ticks, fontsize=8)
    ax.set_ylim(len(GROUPS) - 0.5, -0.9)
    ax.set_xlim(-90, 88)
    ax.set_ylabel("trim (PI) tilt")
    ax.set_xlabel("mg still to go when the taps take over "
                  "(negative: the trickle overshot the target)")
    ax.text(MARGIN_MG + 1.5, -0.72, "the PI's aim today: 35 mg short\n"
            "(CUTOFF_MARGIN_G)", fontsize=8, color=TEXT_2, va="top")
    ax.text(-1.5, -0.72, "target", fontsize=8, color=TEXT_2, va="top",
            ha="right")
    ax.grid(True, axis="x", color=GRID, lw=0.6, zorder=0)
    ax.legend(fontsize=7.5, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.14), ncol=2)
    ax.set_title("Where the PI trickle hands over to the taps "
                 "({} doses in which the PI ran)".format(len(doses)),
                 fontsize=10, loc="left", color=TEXT)

    # --- right: bo-005's dose time at smaller margins (estimate) ----------
    reps = [(r, t) for r, t in doses if r["label"].startswith("val-bo-005")
            and (t.get("telemetry") or {}).get("rows")]
    est = {m: [replay(t, 1000.0 * r["params"]["tolerance_g"], m)
               for r, t in reps] for m in MARGINS}
    first = [statistics.median(e[0] for e in est[m]) for m in MARGINS]
    last = [statistics.median(e[1] for e in est[m]) for m in MARGINS]
    bx.fill_between(MARGINS, first, last, color=ORANGE, alpha=0.14, lw=0,
                    zorder=1)
    bx.plot(MARGINS, first, color=ORANGE, lw=2.0, marker="o", ms=4,
            zorder=3)
    bx.plot(MARGINS, last, color=ORANGE, lw=2.0, ls="--", marker="o",
            ms=4, zorder=3)
    measured = [t["outcomes"]["t_total_s"] for _r, t in reps]
    bx.scatter([MARGIN_MG + 0.9 * ((i % 4) - 1.5) / 1.5 for i in
                range(len(measured))], measured, s=26, color=ORANGE,
               edgecolors=SURFACE, linewidths=0.7, zorder=4)
    bx.annotate("measured: 8 validation doses\n(median {:.0f} s)".format(
        statistics.median(measured)), xy=(MARGIN_MG - 1.2, max(measured)),
        xytext=(21.5, 112), fontsize=8, color=TEXT_2, ha="left",
        arrowprops={"arrowstyle": "-", "color": TEXT_2, "lw": 0.7})
    bx.text(1.0, first[-1] - 9, "solid: taps as productive as today's first "
            "taps\n(lip still charged): {:.0f} s at 0 mg".format(first[-1]),
            fontsize=8, color=TEXT_2, va="top")
    bx.text(1.0, last[-1] + 26, "dashed: as slow as today's last taps\n"
            "(lip depleted): {:.0f} s at 0 mg".format(last[-1]), fontsize=8,
            color=TEXT_2, va="bottom")
    bx.set_xlim(-1, 37)
    bx.set_ylim(0, 125)
    bx.set_xticks(MARGINS)
    bx.set_xlabel("cutoff margin, the PI's aim (mg short of the target)")
    bx.set_ylabel("t_total (s), dose start to settled reading")
    bx.grid(True, color=GRID, lw=0.6, zorder=0)
    bx.set_title("bo-005: dose time at a smaller margin (estimate)",
                 fontsize=10, loc="left", color=TEXT)
    fig.suptitle("Salt, 0.5 g target, campaign salt-20260929T014732Z "
                 "(rig data; right panel re-plays each dose's own tap stage)",
                 fontsize=10.5, x=0.01, ha="left", color=TEXT)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out_path)
    for m, a, b in zip(MARGINS, first, last):
        print("margin {:2d} mg: median t_total {:.1f} (first taps) / {:.1f} "
              "(last taps) s".format(m, a, b))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1
         else os.path.join(HERE, "tap_margin_20261008.png"))

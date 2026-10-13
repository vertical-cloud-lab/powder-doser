#!/usr/bin/env python3
"""The cutoff-margin campaign against the three-stage campaign it
warm-started from (PR #166, 2026-10-13).

    python3 data/opt/salt-margin-20261013T191339Z/compare_margin.py [out.png]

Campaigns: ``salt-20260929T014732Z`` (three-stage, every dose at the
hand-tuned 35 mg cutoff margin, plus its 2026-10-06 validation blocks)
and ``salt-margin-20261013T191339Z`` (the same 8 knobs plus the margin,
0-35 mg).  Both dose 0.5 g of salt on the same rig.

(a) Where the taps take over: mg still to go when the taps started
    (target minus the settled reading after the PI trickle's cutoff),
    against the margin the dose ran with.  Doses in which the PI fed
    powder (a cutoff at a real rate, not a halt on the first poll).
(b) The 16 screening corners, dosed at 35 mg on 2026-09-29 and again at
    0 mg on 2026-10-13: dose time.  Hollow marks overshot the band.
(c) Both campaigns in objective space, each with its observed front of
    clean doses, and the 2026-10-06 validated block of bo-005 (median
    and range).

Also prints the numbers the PR comment quotes.
"""

import glob
import json
import os
import re
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import opt_report as orpt                                     # noqa: E402

PARENT = os.path.join(os.path.dirname(HERE), "salt-20260929T014732Z")
TARGET_G = 0.5
PARENT_MARGIN_MG = 35.0
TRACE_PAIRS = ("corner-03", "corner-06")   # a corner the margin sped up, one it broke

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
GRAY = "#9b9a95"                 # context: the parent campaign
BLUE = "#2a78d6"                 # slot 1: this campaign
ORANGE = "#eb6834"               # slot 2: the validated bo-005 block


def trial_docs(cdir):
    out = {}
    for path in glob.glob(os.path.join(cdir, "zero", "trial_*.json")):
        with open(path) as f:
            d = json.load(f)
        out[d["trial_uuid"]] = d
    return out


def doses(cdir, margin_default_mg=None):
    """Usable doses of one campaign -> list of dicts."""
    doc, records, pareto = orpt.load(cdir)
    trials = trial_docs(cdir)
    out = []
    for r in records:
        if not orpt.usable(r):
            continue
        s = r["summary"]
        p = r.get("params") or {}
        margin = p.get("cutoff_margin_g")
        margin = (1000.0 * margin if margin is not None
                  else margin_default_mg)
        t = trials.get(r["trial_uuid"]) or {}
        out.append({
            "label": r["label"], "mode": r["mode"], "params": p,
            "index": r["trial_index"], "status": s["status"],
            "clean": orpt.clean(r), "in_box": orpt.clean(r)
            and orpt.in_box(r),
            "t": s["t_total_s"], "err": s["error_mg"],
            "abs_err": s["abs_error_mg"], "margin_mg": margin,
            "handover_mg": handover_mg(t),
            "t_tap": (t.get("outcomes") or {}).get("t_tap_s"),
            "taps": (t.get("outcomes") or {}).get("taps"),
            "trial": t})
    return doc, out, pareto


def handover_mg(trial):
    """mg still to go when the taps took over, or None when the PI did
    not feed (no trickle cutoff, or a halt at ~zero rate)."""
    evs = [e for e in (trial or {}).get("stop_events") or []
           if e.get("phase") == "trickle"]
    if not evs:
        return None
    ev = evs[-1]
    if ev.get("stalled") or (ev.get("rate_kf_gps") or 0.0) <= 0.002:
        return None
    if ev.get("settled_g") is None:
        return None
    return 1000.0 * (TARGET_G - ev["settled_g"])


def front(points):
    """Observed front of (t, |err|) points: lower-left is better."""
    out, best = [], float("inf")
    for t, e in sorted(points):
        if e < best:
            out.append((t, e))
            best = e
    return out


def step_xy(fr, floor):
    xs, ys = [fr[0][0]], [max(fr[0][1], floor)]
    for t, e in fr[1:]:
        xs += [t, t]
        ys += [ys[-1], max(e, floor)]
    return xs, ys


def style(ax):
    ax.grid(True, color=GRID, lw=0.6, zorder=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def log_seconds(ax, axis="x", ticks=(15, 30, 60, 120, 240, 480)):
    """Log time axis with plain-number ticks."""
    from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator
    getattr(ax, "set_{}scale".format(axis))("log")
    a = ax.xaxis if axis == "x" else ax.yaxis
    a.set_major_locator(FixedLocator(ticks))
    a.set_major_formatter(plt.FuncFormatter(lambda v, _p: "{:g}".format(v)))
    a.set_minor_locator(NullLocator())
    a.set_minor_formatter(NullFormatter())


def trace(trial):
    """(t_s, signed mg from the target) per telemetry row, raw reading."""
    tel = (trial or {}).get("telemetry") or {}
    target = (trial or {}).get("target_g") or TARGET_G
    ts, ys = [], []
    for row in tel.get("rows") or []:
        f = row.split(",")
        try:
            t, z = float(f[0]), float(f[2])
        except (ValueError, IndexError):
            continue
        ts.append(t)
        ys.append((z - target) * 1000.0)
    return ts, ys


SERIAL_MASS = re.compile(r"mass (-?[0-9.]+) / ([0-9.]+) g .*elapsed ([0-9.]+) s")
SERIAL_TRICKLE = re.compile(r"^\[trickle\]\s+([0-9.]+)s m (-?[0-9.]+)")


def serial_trace(cdir, uuid):
    """(t_s, signed mg) from a dose's raw serial log -- for doses whose
    trial document carries no telemetry (the fw-error ones).  Bulk/tap
    lines are raw readings, trickle lines the filter's mass estimate."""
    path = os.path.join(cdir, "zero", "serial_{}.log".format(uuid))
    pts = []
    if not os.path.exists(path):
        return [], []
    with open(path, errors="replace") as f:
        for line in f:
            m = SERIAL_MASS.search(line)
            if m:
                pts.append((float(m.group(3)), (float(m.group(1))
                                                 - float(m.group(2))) * 1e3))
                continue
            m = SERIAL_TRICKLE.search(line)
            if m:
                pts.append((float(m.group(1)),
                            (float(m.group(2)) - TARGET_G) * 1e3))
    pts.sort()
    return [t for t, _y in pts], [y for _t, y in pts]


def failed_checks(cdir):
    """This campaign's check doses that ended as rig faults (fw-error):
    usable for nothing in Ax, but the day's only bo-005 doses at 35 mg."""
    _doc, records, _p = orpt.load(cdir)
    return [r for r in records if r["label"].startswith("check-")
            and r["summary"]["infra_error"]]


def tap_start(trial):
    """(t_s, signed mg) of the first tap-phase telemetry row, or None."""
    tel = (trial or {}).get("telemetry") or {}
    target = (trial or {}).get("target_g") or TARGET_G
    for row in tel.get("rows") or []:
        f = row.split(",")
        if len(f) > 2 and f[1] == "tap":
            try:
                return float(f[0]), (float(f[2]) - target) * 1000.0
            except ValueError:
                return None
    return None


def draw_trace(ax, d, color, lw=1.6, alpha=1.0, z=3, mark=True):
    ts, ys = trace(d["trial"])
    if not ts:
        return
    ax.plot(ts, ys, color=color, lw=lw, alpha=alpha, zorder=z)
    hs = tap_start(d["trial"]) if mark else None
    if hs:
        ax.scatter([hs[0]], [hs[1]], s=26, color=color, zorder=z + 1,
                   edgecolors=SURFACE, linewidths=0.8)


def traces_figure(pairs, val_block, checks, failed, best, path):
    """How the margin changes a dose: two corner pairs, then the best
    margin-campaign point against the validated bo-005 block."""
    from matplotlib.ticker import FixedLocator
    fig, axes = plt.subplots(1, len(pairs) + 1, figsize=(15.5, 4.9),
                             sharey=True, gridspec_kw={"wspace": 0.12})
    yt = [-300, -100, -30, -10, -3, 0, 3, 10, 30, 100]
    for ax in axes:
        style(ax)
        ax.set_yscale("symlog", linthresh=3.0, linscale=0.6)
        ax.yaxis.set_major_locator(FixedLocator(yt))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda v, _p: "{:+g}".format(v) if v else "0"))
        ax.axhspan(-3, 3, color="#f0efec", zorder=0)
        ax.axhline(0, color=INK_2, lw=0.8, zorder=1)
        ax.set_ylim(-520, 130)
        ax.set_xlabel("time since the dose command (s)")
    axes[0].set_ylabel("balance reading minus the 0.5 g target (mg)")
    for ax, (lab, a, b) in zip(axes, pairs):
        draw_trace(ax, a, GRAY, z=2)
        draw_trace(ax, b, BLUE, z=3)
        ax.set_title("{}: {:.0f} s at 35 mg, {:.0f} s at 0 mg".format(
            lab, a["t"], b["t"]), loc="left", fontsize=10)
        for d, color in ((a, GRAY), (b, BLUE)):
            ts, ys = trace(d["trial"])
            if ts:
                txt = ("{:+.0f} mg".format(d["err"]) if d["err"] is not None
                       else "")
                ax.annotate(txt, (ts[-1], ys[-1]), xytext=(4, 0),
                            textcoords="offset points", fontsize=8,
                            color=INK_2, va="center")
    ax = axes[-1]
    for d in val_block:
        draw_trace(ax, d, ORANGE, lw=1.0, alpha=0.55, z=2, mark=False)
    for d in checks:
        draw_trace(ax, d, ORANGE, lw=1.8, z=3)
    for r in failed:
        ts, ys = serial_trace(HERE, r["trial_uuid"])
        if ts:
            ax.plot(ts, ys, color=ORANGE, lw=1.8, zorder=3)
            ax.annotate("ran out of taps", (ts[-1], ys[-1]), xytext=(-4, -12),
                        textcoords="offset points", fontsize=8,
                        color=INK_2, ha="right")
    for d in best:
        draw_trace(ax, d, BLUE, lw=1.8, z=4)
    ax.set_title("bo-005 at 35 mg (orange) vs {} (blue)".format(
        ", ".join(sorted({d["label"] for d in best})) or "-"), loc="left",
        fontsize=10)
    handles = [plt.Line2D([], [], color=GRAY, lw=1.6, label="35 mg (09-29)"),
               plt.Line2D([], [], color=BLUE, lw=1.6,
                          label="margin campaign (10-13)"),
               plt.Line2D([], [], color=ORANGE, lw=1.0, alpha=0.55,
                          label="bo-005 validated block (10-06)"),
               plt.Line2D([], [], color=ORANGE, lw=1.8,
                          label="bo-005 at 35 mg today (10-13)"),
               plt.Line2D([], [], ls="", marker="o", ms=5, color=INK_2,
                          label="taps take over")]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False,
               fontsize=8.5, bbox_to_anchor=(0.5, -0.07))
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


def main(argv):
    out_png = argv[1] if len(argv) > 1 else os.path.join(
        HERE, "margin_vs_three_stage.png")
    pdoc, pdoses, _ = doses(PARENT, PARENT_MARGIN_MG)
    doc, ndoses, pareto = doses(HERE)
    parent_campaign = [d for d in pdoses if d["mode"] != "validation"]
    # each block is its last 8 replicates: the first two bo-005 doses
    # ran with telemetry off and the block restarted (validation_20261006.md)
    val_bo005 = sorted((d for d in pdoses if d["mode"] == "validation"
                        and d["label"].startswith("val-bo-005")),
                       key=lambda d: d["index"])[-8:]
    val_c09 = sorted((d for d in pdoses if d["mode"] == "validation"
                      and d["label"].startswith("val-corner-09")),
                     key=lambda d: d["index"])[-8:]

    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": INK_2, "axes.labelcolor": INK,
        "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK,
        "axes.facecolor": SURFACE, "figure.facecolor": SURFACE})
    fig, (aa, ab, ac) = plt.subplots(
        1, 3, figsize=(15.5, 5.4),
        gridspec_kw={"width_ratios": [1.0, 1.05, 1.25], "wspace": 0.32})

    # (a) handover vs margin --------------------------------------------
    jitter = {}
    for group, color, z in ((pdoses, GRAY, 2), (ndoses, BLUE, 3)):
        for d in group:
            h = d["handover_mg"]
            if h is None or d["margin_mg"] is None:
                continue
            k = round(d["margin_mg"], 1)
            n = jitter.get((id(group), k), 0)
            jitter[(id(group), k)] = n + 1
            dx = ((n % 7) - 3) * 0.45 if k in (0.0, 17.5, 35.0) else 0.0
            if group is pdoses:
                dx -= 1.6
            aa.scatter(d["margin_mg"] + dx, h, s=22, color=color,
                       alpha=0.85, lw=0, zorder=z)
    aa.plot([0, 35], [0, 35], color=INK_2, lw=0.9, ls="--", zorder=1)
    aa.text(35.5, 34, "aim", color=INK_2, fontsize=8, va="center")
    aa.axhline(0, color=INK_2, lw=0.8, zorder=1)
    aa.axhspan(-120, 0, color="#f0efec", zorder=0)
    aa.text(40.5, -4, "past the target\n(slug after the cutoff)",
            color=INK_2, fontsize=8, ha="right", va="top")
    aa.set_xlim(-6, 41)
    aa.set_ylim(-115, 90)
    aa.set_xticks([0, 10, 17.5, 25, 35])
    aa.set_xticklabels(["0", "10", "17.5", "25", "35"])
    aa.set_xlabel("PI cutoff margin (mg)")
    aa.set_ylabel("mg still to go when the taps took over")
    aa.set_title("(a) Where the taps take over", loc="left",
                 fontsize=10)
    style(aa)

    # (b) paired corners ------------------------------------------------
    hi = {d["label"]: d for d in parent_campaign
          if d["mode"] == "screen" and d["label"].startswith("corner-")}
    lo = {d["label"]: d for d in ndoses
          if d["mode"] == "screen" and d["label"].startswith("corner-")}
    labels = sorted((l for l in lo if l in hi),
                    key=lambda l: hi[l]["t"])
    for y, lab in enumerate(labels):
        a, b = hi[lab], lo[lab]
        ab.plot([a["t"], b["t"]], [y, y], color=GRID, lw=2.0, zorder=1)
        for d, color in ((a, GRAY), (b, BLUE)):
            ok = d["status"] == "ok"
            ab.scatter(d["t"], y, s=40, zorder=3, linewidths=1.4,
                       facecolors=color if ok else SURFACE,
                       edgecolors=color)
    ab.set_yticks(range(len(labels)))
    ab.set_yticklabels(labels, fontsize=8)
    log_seconds(ab, "x")
    ab.set_xlabel("dose time (s, log)")
    ab.set_title("(b) The 16 corners at 35 mg (gray) and 0 mg (blue)",
                 loc="left", fontsize=10)
    style(ab)

    # (c) objective space -----------------------------------------------
    floor = 0.3
    for group, color, lab in ((parent_campaign, GRAY,
                               "three-stage campaign, 35 mg (09-29)"),
                              (ndoses, BLUE,
                               "margin campaign, 0-35 mg (10-13)")):
        cl = [d for d in group if d["clean"]]
        bad = [d for d in group if not d["clean"]
               and d["t"] is not None and d["abs_err"] is not None]
        ac.scatter([d["t"] for d in cl],
                   [max(d["abs_err"], floor) for d in cl], s=26,
                   color=color, lw=0, alpha=0.9, zorder=3, label=lab)
        ac.scatter([d["t"] for d in bad],
                   [max(d["abs_err"], floor) for d in bad], s=26,
                   facecolors=SURFACE, edgecolors=color, lw=1.2,
                   zorder=3)
        fr = front([(d["t"], d["abs_err"]) for d in cl if d["in_box"]])
        if fr:
            xs, ys = step_xy(fr, floor)
            ac.plot(xs, ys, color=color, lw=1.4, zorder=2)
    if val_bo005:
        ts = [d["t"] for d in val_bo005]
        es = [d["abs_err"] for d in val_bo005]
        mt, me = statistics.median(ts), statistics.median(es)
        ac.plot([min(ts), max(ts)], [me, me], color=ORANGE, lw=1.2,
                zorder=4)
        ac.plot([mt, mt], [min(es), max(es)], color=ORANGE, lw=1.2,
                zorder=4)
        ac.scatter([mt], [me], s=70, marker="D", color=ORANGE, zorder=5,
                   edgecolors=SURFACE, linewidths=1.2,
                   label="bo-005 validated 10-06, 8 doses (median, range)")
    fc = [r["summary"] for r in failed_checks(HERE)
          if r["summary"]["t_total_s"] and r["summary"]["abs_error_mg"]]
    if fc:
        ac.scatter([x["t_total_s"] for x in fc],
                   [x["abs_error_mg"] for x in fc], s=70, marker="D",
                   facecolors=SURFACE, edgecolors=ORANGE, linewidths=1.6,
                   zorder=5, label="bo-005 at 35 mg today: ran out of taps "
                                   "({} tries)".format(len(fc)))
    ac.axvline(180, color=INK_2, lw=0.8, ls="--")
    ac.axhline(20, color=INK_2, lw=0.8, ls="--")
    log_seconds(ac, "x")
    log_seconds(ac, "y", ticks=(0.3, 1, 3, 10, 30, 100))
    ac.set_xlabel("dose time (s, log)")
    ac.set_ylabel("|error| (mg, log) vs the 0.5 g target")
    ac.set_title("(c) Both campaigns (lines: observed fronts)", loc="left",
                 fontsize=10)
    style(ac)
    ac.legend(fontsize=8, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.13), ncol=1)
    fig.text(0.125, -0.04, "Hollow marks: overshoot or jam.  Dashed: the "
             "180 s / 20 mg thresholds.", fontsize=8, color=INK_2)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out_png)

    checks = [d for d in ndoses if d["label"].startswith("check-")
              and d["margin_mg"] == PARENT_MARGIN_MG]
    cands = [d for d in ndoses if d["in_box"] and d["mode"] != "validation"
             and not (d["label"].startswith("check-")
                      and d["margin_mg"] == PARENT_MARGIN_MG)]
    best = sorted(cands, key=lambda d: (d["t"] / 180.0) ** 2
                  + (d["abs_err"] / 20.0) ** 2)[:1]
    pairs = [(l, hi[l], lo[l]) for l in TRACE_PAIRS if l in hi and l in lo]
    traces_figure(pairs, val_bo005, checks, failed_checks(HERE), best,
                  os.path.join(
        os.path.dirname(out_png), "margin_traces.png")
        if len(argv) <= 1 else out_png.replace(".png", "_traces.png"))

    # -- numbers for the write-up ----------------------------------------
    def med(xs):
        xs = [x for x in xs if x is not None]
        return statistics.median(xs) if xs else None

    print("\nhandover (mg to go at tap start), PI-fed doses:")
    for name, group in (("parent @35", pdoses), ("this", ndoses)):
        by = {}
        for d in group:
            if d["handover_mg"] is not None and d["margin_mg"] is not None:
                by.setdefault(round(d["margin_mg"]), []).append(
                    d["handover_mg"])
        for k in sorted(by):
            v = by[k]
            print("  {:10s} margin {:>3} mg: n={:2d} median {:5.1f} "
                  "range {:5.1f}-{:5.1f}".format(name, k, len(v),
                                                 med(v), min(v), max(v)))
    print("\npaired corners (35 mg -> 0 mg):")
    for lab in sorted(labels):
        a, b = hi[lab], lo[lab]
        print("  {}  {:>9} {:6.1f} s {:+6.1f} mg  ->  {:>9} {:6.1f} s "
              "{:+6.1f} mg   tap {} -> {} s".format(
                  lab, a["status"], a["t"], a["err"] or 0, b["status"],
                  b["t"], b["err"] or 0, a["t_tap"], b["t_tap"]))
    both = [(hi[l], lo[l]) for l in labels
            if hi[l]["status"] == "ok" and lo[l]["status"] == "ok"]
    if both:
        dts = [b["t"] - a["t"] for a, b in both]
        print("  both ok: n={}, median dt {:+.1f} s, mean {:+.1f} s".format(
            len(both), med(dts), statistics.mean(dts)))
    print("  overshoots: 35 mg {} / 0 mg {}".format(
        sum(hi[l]["status"] == "overshoot" for l in labels),
        sum(lo[l]["status"] == "overshoot" for l in labels)))
    print("\novershoots by phase (bulk: the bulk stop already settled past "
          "the target; trickle: a slug after the PI cutoff):")
    for name, group in (("parent", pdoses), ("this", ndoses)):
        for d in group:
            if d["status"] != "overshoot":
                continue
            evs = (d["trial"] or {}).get("stop_events") or []
            bulk = [e for e in evs if e.get("phase") == "bulk"]
            past = bool(bulk and (bulk[-1].get("settled_g") or 0) > TARGET_G)
            print("  {:6s} {:16s} margin {:>5} mg  {:+6.1f} mg  {}".format(
                name, d["label"], d["margin_mg"], d["err"] or 0,
                "bulk" if past else "trickle"))
    for name, block in (("val bo-005 (10-06)", val_bo005),
                        ("val corner-09 (10-06)", val_c09)):
        if block:
            print("{}: n={} median t {:.1f} s, median |err| {:.2f} "
                  "mg".format(name, len(block), med([d["t"] for d in block]),
                              med([d["abs_err"] for d in block])))
    checks = [d for d in ndoses if d["label"].startswith("check-")]
    for d in checks:
        print("check {}: {} {:.1f} s {:+.1f} mg margin {} handover {}".format(
            d["label"], d["status"], d["t"], d["err"] or 0, d["margin_mg"],
            d["handover_mg"]))
    for name, group in (("parent campaign", parent_campaign),
                        ("this campaign", ndoses)):
        fr = front([(d["t"], d["abs_err"]) for d in group if d["in_box"]])
        print("{} front: {}".format(name, ", ".join(
            "{:.0f} s/{:.1f} mg".format(t, e) for t, e in fr)))


if __name__ == "__main__":
    main(sys.argv)

#!/usr/bin/env python3
"""Block D dispensing traces: does per-revolution slugging survive at speed?

Block D of the #116 uniform battery streams ~3.5 Hz scale polls while the
auger runs continuously for 3 commanded revolutions at 15, 45 and 90 RPM,
tube tilt 45 deg (non-vertical).  The PID sessions on salt (2026-07-30)
showed delivery arriving as ~one-revolution slugs; this script asks the
same question of every powder in the battery, per speed:

* ``speed_45rpm_traces.png`` -- the 45 RPM mass-vs-time trace per powder,
  with revolution boundaries and the settled (post-afterflow) mass.
* ``speed_rpm_comparison.png`` -- all three speeds per powder on a
  revolutions-completed axis, so per-revolution structure aligns across
  speeds regardless of duration.
* ``slug_metrics.csv`` -- per (powder, rpm): streamed/settled mass,
  actual revolutions, and two shape metrics:

  - ``ramp_dev`` -- max deviation of the trace from a straight ramp,
    as a fraction of the streamed total.  A clean 3-step staircase
    scores ~0.17; a smooth ramp scores < 0.05.
  - ``burstiness`` -- largest single-poll increment relative to the
    uniform expectation (total / n polls).  Uniform flow scores ~1.

Both metrics are computed from motion onset (first poll past 5 % of the
segment total) so the transport-delay flat at the start does not count
as slugging, and are suppressed below 5 mg streamed (balance floor).

Caveats the figures also carry: the polling loop's real cadence is
~287 ms (not the commanded 250 ms), so the "3 revolutions" are ~3.4-3.5
actual; sampling density is ~13.8 polls/rev at 15 RPM but only ~2.3 at
90 RPM, and the balance's own step response (~0.5-1 s, see the 08-07
Edison critique) low-passes anything faster -- so a smooth 90 RPM trace
is partly instrumental, while structure at 15-45 RPM is real.

Usage::

    python scripts/plot_battery_speed_traces.py data/battery/speed-analysis \\
        data/battery/*_salt data/battery/*_xanthan-gum ...

Run directories whose ``run_*.json`` is not marked
``qc.valid_for_cross_powder_comparison`` are skipped with a note.
"""

import csv
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SERIES_45 = "#2a78d6"
# Ordinal ramp for the ordered speed series (light -> dark = slow -> fast).
RPM_COLORS = {15.0: "#86b6ef", 45.0: "#2a78d6", 90.0: "#104281"}

MIN_METRIC_MG = 5.0     # below this the shape metrics are balance noise
ONSET_FRACTION = 0.05   # motion onset = first poll past 5 % of the total


def human_name(powder_id):
    return {
        "carboxymethyl-cellulose": "CMC",
    }.get(powder_id, powder_id.replace("-", " "))


def load_run(run_dir):
    """Return (powder_id, {rpm: segment}, {rpm: settled_delta_g}) or None."""
    js = glob.glob(os.path.join(run_dir, "run_*.json"))
    polls = glob.glob(os.path.join(run_dir, "polls_*.csv"))
    trials = glob.glob(os.path.join(run_dir, "trials_*.csv"))
    if not (js and polls and trials):
        return None
    doc = json.load(open(js[0]))
    qc = doc.get("qc", {})
    if not qc.get("valid_for_cross_powder_comparison"):
        print(f"skip {run_dir}: qc.valid_for_cross_powder_comparison is not set "
              f"(verdict: {qc.get('verdict')})")
        return None
    powder_id = doc.get("powder_id") or os.path.basename(run_dir).split("_", 1)[1]

    segments = {}
    for row in csv.DictReader(open(polls[0])):
        if row["block"] != "D":
            continue
        rpm = float(row["rpm"])
        segments.setdefault(rpm, []).append(
            (int(row["t_ms"]), float(row["grams"])))

    settled = {}
    for row in csv.DictReader(open(trials[0])):
        if row["block"] == "D" and row["phase"] == "speed":
            settled[float(row["rpm"])] = {
                "before_g": float(row["before_g"]),
                "after_g": float(row["after_g"]),
                "delta_g": float(row["delta_g"]),
            }
    return powder_id, segments, settled


def segment_series(points, before_g, rpm):
    """Rebased trace plus timing: (t_s, dm_mg, revs, actual_revs, dt_ms)."""
    ts = [p[0] for p in points]
    dts = sorted(b - a for a, b in zip(ts, ts[1:]))
    dt = dts[len(dts) // 2] if dts else 287
    t_start = ts[0] - dt          # rotation begins one loop period earlier
    t_s = [(t - t_start) / 1000.0 for t in ts]
    dm_mg = [(g - before_g) * 1000.0 for _, g in points]
    revs = [t * rpm / 60.0 for t in t_s]
    return t_s, dm_mg, revs, revs[-1], dt


def shape_metrics(t_s, dm_mg):
    """(ramp_dev, burstiness) over the streamed segment, or (None, None)."""
    total = dm_mg[-1] - dm_mg[0]
    if total < MIN_METRIC_MG:
        return None, None
    onset = 0
    for i, m in enumerate(dm_mg):
        if m - dm_mg[0] >= ONSET_FRACTION * total:
            onset = i
            break
    xs, ys = t_s[onset:], dm_mg[onset:]
    n = len(xs)
    if n < 3:
        return None, None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    ramp_dev = max(abs(y - (my + slope * (x - mx))) for x, y in zip(xs, ys)) / total
    increments = [b - a for a, b in zip(dm_mg, dm_mg[1:])]
    burstiness = max(increments) / (total / len(increments))
    return ramp_dev, burstiness


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASELINE)
    ax.tick_params(colors=TEXT_MUTED, labelsize=8, length=3)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)

    runs = []
    for run_dir in sys.argv[2:]:
        loaded = load_run(run_dir)
        if loaded:
            runs.append(loaded)
    if not runs:
        sys.exit("no valid runs")

    # Order panels by settled 45 RPM delivery, largest first.
    runs.sort(key=lambda r: -r[2].get(45.0, {}).get("delta_g", 0.0))

    metrics_rows = []
    for powder_id, segments, settled in runs:
        for rpm in sorted(segments):
            pts = segments[rpm]
            before = settled.get(rpm, {}).get("before_g", pts[0][1])
            t_s, dm, revs, actual_revs, dt = segment_series(pts, before, rpm)
            ramp_dev, burst = shape_metrics(t_s, dm)
            settled_mg = settled.get(rpm, {}).get("delta_g", float("nan")) * 1000
            metrics_rows.append({
                "powder_id": powder_id, "rpm": rpm, "tilt_deg": 45.0,
                "n_polls": len(pts), "poll_dt_ms": dt,
                "polls_per_rev": round(60000.0 / (rpm * dt), 1),
                "actual_revs": round(actual_revs, 2),
                "streamed_mg": round(dm[-1], 1),
                "settled_mg": round(settled_mg, 1),
                "settled_mg_per_rev": round(settled_mg / actual_revs, 1),
                "ramp_dev": "" if ramp_dev is None else round(ramp_dev, 3),
                "burstiness": "" if burst is None else round(burst, 2),
            })

    with open(os.path.join(out_dir, "slug_metrics.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics_rows[0]))
        writer.writeheader()
        writer.writerows(metrics_rows)

    by_key = {(r["powder_id"], r["rpm"]): r for r in metrics_rows}
    ncols, nrows = 4, 2

    # ---- Figure 1: the 45 RPM trace per powder --------------------------
    fig, axes = plt.subplots(nrows, ncols, figsize=(13.6, 6.6), dpi=150)
    fig.patch.set_facecolor(PAGE)
    for ax in axes.flat:
        ax.set_visible(False)
    for i, (powder_id, segments, settled) in enumerate(runs):
        ax = axes.flat[i]
        ax.set_visible(True)
        style(ax)
        pts = segments[45.0]
        before = settled[45.0]["before_g"]
        t_s, dm, _, actual_revs, _ = segment_series(pts, before, 45.0)
        m = by_key[(powder_id, 45.0)]
        rev_s = 60.0 / 45.0
        for k in (1, 2, 3):
            ax.axvline(k * rev_s, color=GRID, linewidth=0.8, zorder=1)
        settled_mg = m["settled_mg"]
        ax.axhline(settled_mg, color=TEXT_MUTED, linewidth=0.9,
                   linestyle=(0, (4, 3)), zorder=2)
        ax.plot(t_s, dm, color=SERIES_45, linewidth=1.6, marker="o",
                markersize=3.2, markeredgecolor=SURFACE,
                markeredgewidth=0.4, zorder=3)
        flat = (dm[-1] - dm[0]) < MIN_METRIC_MG
        if flat:
            ax.set_ylim(-1.5, 6)
            ax.text(0.5, 0.55, "no conveyance\n(cohesive powder;\nauger does not feed it)",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=8, color=TEXT_SECONDARY)
        else:
            ax.set_ylim(min(-0.03 * settled_mg, min(dm) - 1),
                        max(settled_mg, max(dm)) * 1.24)
            ax.text(0.03, 0.97,
                    f"streamed {dm[-1]:.0f} mg -> settled {settled_mg:.0f} mg\n"
                    f"slug index {m['ramp_dev']}",
                    transform=ax.transAxes, ha="left", va="top",
                    fontsize=7.5, color=TEXT_SECONDARY)
        ax.text(0.03, 0.03, f"{actual_revs:.1f} rev actual",
                transform=ax.transAxes, ha="left", va="bottom",
                fontsize=7, color=TEXT_MUTED)
        ax.set_xlim(0, t_s[-1] + 0.15)
        ax.set_title(human_name(powder_id), fontsize=10.5,
                     color=TEXT_PRIMARY, pad=6)
        if i // ncols == nrows - 1 or i + ncols >= len(runs):
            ax.set_xlabel("time since rotation start (s)", fontsize=8,
                          color=TEXT_MUTED)
        if i % ncols == 0:
            ax.set_ylabel("dispensed (mg)", fontsize=8, color=TEXT_MUTED)
    guide = axes.flat[len(runs)]
    guide.set_visible(True)
    guide.axis("off")
    guide.text(0, 0.95, "reading the panels", fontsize=9.5,
               color=TEXT_PRIMARY, va="top")
    guide.text(0, 0.80,
               "vertical hairlines: revolution\nboundaries (1 rev = 1.33 s)\n\n"
               "dashed line: settled mass 2 s\nafter the stop -- the gap above\n"
               "the trace end is afterflow the\nstream never sees\n\n"
               "slug index: max deviation from\na straight ramp / total; a 3-step\n"
               "staircase scores ~0.17, smooth\nflow < 0.05",
               fontsize=8, color=TEXT_SECONDARY, va="top", linespacing=1.35)
    fig.suptitle("Block D at 45 RPM -- dispensing trace per powder "
                 "(tilt 45°, continuous rotation, ~3.5 Hz polls)",
                 fontsize=12.5, color=TEXT_PRIMARY, y=0.985)
    fig.text(0.5, 0.005,
             "y-scales differ per panel. Balance step response ~0.5-1 s "
             "low-passes structure faster than ~1 revolution at this speed.",
             ha="center", fontsize=8, color=TEXT_MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    out1 = os.path.join(out_dir, "speed_45rpm_traces.png")
    fig.savefig(out1, facecolor=PAGE)
    plt.close(fig)
    print("wrote", out1)

    # ---- Figure 2: 15 vs 45 vs 90 RPM on a revolutions axis -------------
    fig, axes = plt.subplots(nrows, ncols, figsize=(13.6, 6.6), dpi=150)
    fig.patch.set_facecolor(PAGE)
    for ax in axes.flat:
        ax.set_visible(False)
    for i, (powder_id, segments, settled) in enumerate(runs):
        ax = axes.flat[i]
        ax.set_visible(True)
        style(ax)
        for k in (1, 2, 3):
            ax.axvline(k, color=GRID, linewidth=0.8, zorder=1)
        flat = True
        for rpm in sorted(segments):
            pts = segments[rpm]
            before = settled.get(rpm, {}).get("before_g", pts[0][1])
            _, dm, revs, _, _ = segment_series(pts, before, rpm)
            if dm[-1] - dm[0] >= MIN_METRIC_MG:
                flat = False
            ax.plot(revs, dm, color=RPM_COLORS[rpm], linewidth=1.5,
                    marker="o", markersize=2.6, markeredgecolor=SURFACE,
                    markeredgewidth=0.3, zorder=3,
                    label=f"{rpm:.0f} RPM")
            if i == 0:
                ax.annotate(f"{rpm:.0f}", xy=(revs[-1], dm[-1]),
                            xytext=(4, 0), textcoords="offset points",
                            fontsize=7.5, color=RPM_COLORS[rpm], va="center")
        if flat:
            ax.set_ylim(-1.5, 6)
            ax.text(0.5, 0.6, "no conveyance at any speed\n(sub-mg blips = balance floor)",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=8, color=TEXT_SECONDARY)
        ax.set_xlim(0, 3.75)
        ax.set_title(human_name(powder_id), fontsize=10.5,
                     color=TEXT_PRIMARY, pad=6)
        if i // ncols == nrows - 1 or i + ncols >= len(runs):
            ax.set_xlabel("auger revolutions completed", fontsize=8,
                          color=TEXT_MUTED)
        if i % ncols == 0:
            ax.set_ylabel("dispensed (mg)", fontsize=8, color=TEXT_MUTED)
    guide = axes.flat[len(runs)]
    guide.set_visible(True)
    guide.axis("off")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    guide.legend(handles, labels, loc="upper left", frameon=False,
                 fontsize=9, title="auger speed", title_fontsize=9,
                 labelcolor=TEXT_SECONDARY)
    guide.text(0, 0.52,
               "x is revolutions completed, so\nper-revolution slugs align "
               "across\nspeeds.\n\nthe flat start grows with speed\nbecause the "
               "~1 s transport delay\n(lip-to-cup fall + balance lag) is\nfixed in "
               "time: ~0.25 rev at 15 RPM\nbut ~1.5 rev at 90 RPM.\n\nsampling: "
               "~13.8 polls/rev at 15,\n~4.6 at 45, ~2.3 at 90 RPM --\nat 90 the "
               "balance filter + sampling\ncannot resolve slugs, so smooth-\nness "
               "there is partly instrumental",
               fontsize=8, color=TEXT_SECONDARY, va="top", linespacing=1.35)
    fig.suptitle("Slug behavior vs auger speed -- Block D, tilt 45°, "
                 "mass vs revolutions at 15 / 45 / 90 RPM",
                 fontsize=12.5, color=TEXT_PRIMARY, y=0.985)
    fig.text(0.5, 0.005,
             "y-scales differ per panel. Traces end when rotation stops; "
             "settled masses (incl. afterflow) are in slug_metrics.csv.",
             ha="center", fontsize=8, color=TEXT_MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    out2 = os.path.join(out_dir, "speed_rpm_comparison.png")
    fig.savefig(out2, facecolor=PAGE)
    plt.close(fig)
    print("wrote", out2)


if __name__ == "__main__":
    main()

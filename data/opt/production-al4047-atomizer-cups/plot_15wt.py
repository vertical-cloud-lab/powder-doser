"""Issue #186, 2026-10-20 (third session, 15 wt% cup): the powder in the cup through the three
40° bulk doses and the 0° reverse steps between them (left), and each bulk dose's feed rate
(right). Built from the trial documents and the stepwise dose's output.

    python3 data/opt/production-al4047-atomizer-cups/plot_15wt.py
"""
import datetime as dt
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ZERO = os.path.join(HERE, "zero")
SURFACE, INK, INK2, MUTED, GRID, AXIS = (
    "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7")
BULK, STEP = "#2a78d6", "#eb6834"            # categorical slots 1-2 of the reference palette
TARGET_G = 0.15 / 0.85 * 37.2151
# bulk dose uuid prefix -> powder already in the cup when it tared (stable reads, README)
DOSES = [("cb3096e9", 0.0), ("d737cec5", 2.6723), ("9480b818", 4.9219)]
TOPUP = "unclog_dose_20261020c.out"          # the 0° reverse steps after cb3096e9
EXTRA = "topup_20261020c.out"                # the final top-up, if one ran
# stable reads over cb3096e9's tare that rig_cmd.py printed without a clock (README timeline):
# after the reverse steps were stopped, after the forward and rocking test at 0°, and after the
# tilt test (climb to 30°, four forward turns at 25°)
TESTS = [("21:27:15", 2.5745), ("21:28:53", 2.6137), ("21:29:58", 2.6723)]


def trial(prefix):
    name = [f for f in os.listdir(ZERO) if f.startswith("trial_" + prefix)][0]
    return json.load(open(os.path.join(ZERO, name)))


def utc(stamp):
    return dt.datetime.fromisoformat(stamp).astimezone(dt.timezone.utc)


def bulk_series(doc):
    """-> (UTC datetimes, grams over the dose's tare, dose seconds).  The dose's t = 0 is put at
    ended_utc - t_total_s, a few seconds after the executor's telemetry pull starts."""
    t0 = utc(doc["ended_utc"]) - dt.timedelta(seconds=doc["outcomes"]["t_total_s"] + 3)
    ts, gs, ss = [], [], []
    for row in doc["telemetry"]["rows"]:
        f = row.split(",")
        if f[1] != "bulk" or not f[4]:
            continue
        ts.append(t0 + dt.timedelta(seconds=float(f[0])))
        gs.append(float(f[4]))
        ss.append(float(f[0]))
    return ts, gs, ss


def step_series(path, day, offset_g=0.0):
    """-> (UTC datetimes, grams + offset_g) from 'DOSE step' lines."""
    ts, gs = [], []
    if not os.path.exists(path):
        return ts, gs
    for line in open(path):
        m = re.match(r"DOSE step \d+ \S+ deg: \S+ -> (\S+) g \(\S+ mg\)\s+(\d\d:\d\d:\d\d)", line)
        if m:
            h, mi, s = (int(x) for x in m.group(2).split(":"))
            ts.append(day.replace(hour=h, minute=mi, second=s, microsecond=0))
            gs.append(float(m.group(1)) + offset_g)
    return ts, gs


def rate(ss, gs, window_s=10.0):
    """Feed rate in mg/s over a trailing window, sampled once per window."""
    out_t, out_r, j = [], [], 0
    for i, s in enumerate(ss):
        if s - ss[j] >= window_s:
            out_t.append(s)
            out_r.append(1000.0 * (gs[i] - gs[j]) / (s - ss[j]))
            j = i
    return out_t, out_r


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 4.6), facecolor=SURFACE,
                                  gridspec_kw={"width_ratios": [1.45, 1]})
    style(ax)
    style(ax2)
    day = None
    for k, (prefix, before) in enumerate(DOSES):
        if not any(f.startswith("trial_" + prefix) for f in os.listdir(ZERO)):
            continue
        doc = trial(prefix)
        ts, gs, ss = bulk_series(doc)
        day = day or ts[0]
        ax.plot(ts, [g + before for g in gs], color=BULK, linewidth=2,
                label="bulk dose at 40°, 100 rpm, 2 Hz taps" if k == 0 else None)
        rt, rr = rate(ss, gs)
        ax2.plot(rt, rr, color=BULK, linewidth=2, alpha=(1.0, 0.7, 0.45)[k],
                 label="{}: {:.4f} g, {}".format(prefix, gs[-1], doc["flags"]["status"]))
    ts, gs = step_series(os.path.join(ZERO, TOPUP), day)
    for hms, g in TESTS:
        h, mi, s = (int(x) for x in hms.split(":"))
        ts.append(day.replace(hour=h, minute=mi, second=s, microsecond=0))
        gs.append(g)
    ax.plot(ts, gs, color=STEP, linewidth=2, marker="o", markersize=2.5,
            label="auger steps with a stable read after each")
    ts, gs = step_series(os.path.join(ZERO, EXTRA), day, DOSES[-1][1])
    if ts:
        ax.plot(ts, gs, color=STEP, linewidth=2, marker="o", markersize=2.5)
    ax.axhline(TARGET_G, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(ax.get_xlim()[0], TARGET_G, " 15 wt% target, {:.4f} g".format(TARGET_G),
            color=INK2, fontsize=8, va="bottom")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M", tz=dt.timezone.utc))
    ax.set_xlabel("UTC, 2026-10-20", color=INK2, fontsize=9)
    ax.set_ylabel("powder in the cup (g)", color=INK2, fontsize=9)
    ax.set_ylim(0, TARGET_G * 1.08)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="lower right")
    ax.set_title("Powder in the cup", color=INK, fontsize=11, loc="left")
    ax2.set_xlabel("time into the bulk dose (s)", color=INK2, fontsize=9)
    ax2.set_ylabel("feed rate, 10 s windows (mg/s)", color=INK2, fontsize=9)
    ax2.set_ylim(bottom=0)
    ax2.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="upper right")
    ax2.set_title("Each 40° bulk dose slows down", color=INK, fontsize=11, loc="left")
    fig.tight_layout()
    out = os.path.join(HERE, "dose_15wt_trace.png")
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    print(out)


if __name__ == "__main__":
    main()

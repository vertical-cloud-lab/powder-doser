#!/usr/bin/env python3
"""The whole 2026-11-20 barium chloride session on one figure (PR #131).

Left: the balance, the plate angle and the auger speed from the static-tilt
pour probe through launch 2, against UTC time (the Zero's receipt stamps).
Right: powder delivered against auger revolutions turned, barium chloride's
blocks one after another next to calcium lactate's first trial of the
03:06 UTC run on the same protocol.

usage: python plot_session.py            (run from anywhere; writes session.png here)
"""
import csv
import glob
import os
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CL = os.path.join(HERE, "..", "2026-11-20_calcium-lactate_tilt-schedule-2g",
                  "launch1_0305Z")
BA_C, CL_C = "#2a78d6", "#eb6834"      # validated categorical slots 1-2
INK, INK2, GRID, SPAN = "#0b0b0b", "#52514e", "#e4e3df", "#f1f0ec"


def utc(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


def from_iso(date, hms):
    return datetime.strptime(date + " " + hms, "%Y-%m-%d %H:%M:%S.%f").replace(
        tzinfo=timezone.utc)


def stamped(path, kind):
    """Rows (time, grams, tilt, rpm) from a stamped log.

    kind 'probe': static_tilt_probe.py lines  P,<ms>,<tag>,<tilt>,<stat>,<g>
    kind 'trial': three_phase_tilt_trials.py  S,<trial>,<ms>,<src>,<stat>,<g>,<stage>,<tilt>,<rpm>,...
    """
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            if "\t" not in raw:
                continue
            host, line = raw.rstrip("\n").split("\t", 1)
            p = line.split(",")
            try:
                if kind == "probe" and p[0] == "P" and p[5]:
                    out.append((utc(float(host)), float(p[5]), float(p[3]), 0.0))
                elif kind == "trial" and p[0] == "S" and p[5]:
                    out.append((utc(float(host)), float(p[5]), float(p[7]),
                                float(p[8])))
            except (ValueError, IndexError):
                continue
    return out


def from_csv(path):
    out = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            if r["mass_abs_g"]:
                out.append((from_iso(r["date_utc"], r["time_utc"]),
                            float(r["mass_abs_g"]), float(r["tilt_deg"]),
                            float(r["auger_rpm"])))
    return out


def revs(rows):
    """Cumulative auger revolutions at each row (rpm held until the next row)."""
    c, out = 0.0, []
    for i, (t, g, a, rpm) in enumerate(rows):
        if i:
            dt = (t - rows[i - 1][0]).total_seconds()
            if 0 < dt < 2.0:
                c += rows[i - 1][3] / 60.0 * dt
        out.append(c)
    return out


blocks = [
    ("pour probe", stamped(os.path.join(HERE, "static_tilt_probe.log"), "probe")),
    ("launch 1", stamped(glob.glob(os.path.join(HERE, "launch1_*", "session_launch1.log"))[0], "trial")),
    ("priming spin", from_csv(glob.glob(os.path.join(HERE, "launch2_*", "prime_spin_0deg.csv"))[0])),
    ("flow probe", from_csv(glob.glob(os.path.join(HERE, "launch2_*", "flow_probe_by_angle.csv"))[0])),
    ("launch 2", stamped(glob.glob(os.path.join(HERE, "launch2_*", "session_launch2.log"))[0], "trial")),
]
m0 = blocks[0][1][0][1]                     # first balance frame of the session

fig = plt.figure(figsize=(13, 7.2), facecolor="white")
gs = fig.add_gridspec(3, 2, width_ratios=[2.15, 1], height_ratios=[2.2, 1, 1],
                      hspace=0.12, wspace=0.22, left=0.06, right=0.985,
                      top=0.86, bottom=0.09)
axm = fig.add_subplot(gs[0, 0])
axt = fig.add_subplot(gs[1, 0], sharex=axm)
axr = fig.add_subplot(gs[2, 0], sharex=axm)
axd = fig.add_subplot(gs[:, 1])

all_rows, cum = [], 0.0
for name, rows in blocks:
    ts = [r[0] for r in rows]
    axm.plot(ts, [1000.0 * (r[1] - m0) for r in rows], color=BA_C, lw=1.6)
    axt.step(ts, [r[2] for r in rows], where="post", color=INK2, lw=1.4)
    axr.step(ts, [r[3] for r in rows], where="post", color=INK2, lw=1.4)
    rv = revs(rows)
    for ax in (axm, axt, axr):
        ax.axvspan(ts[0], ts[-1], color=SPAN, zorder=0, lw=0)
    mid = ts[0] + (ts[-1] - ts[0]) / 2
    axm.text(mid, 1.02, "{}\n{:.0f} rev".format(name, rv[-1]) if rv[-1] >= 0.5
             else name + "\nauger still", transform=axm.get_xaxis_transform(),
             ha="center", va="bottom", fontsize=9, color=INK2)
    all_rows.append((name, rows, [cum + x for x in rv]))
    cum += rv[-1]

axm.set_ylim(-10, 25)
axm.set_ylabel("balance, mg\n(0 = session start)", color=INK2)
axt.set_ylabel("plate, deg", color=INK2)
axt.set_ylim(-5, 68)
axt.set_yticks([0, 30, 60])
axr.set_ylabel("auger, rpm", color=INK2)
axr.set_ylim(-5, 92)
axr.set_yticks([0, 40, 80])
axr.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=timezone.utc))
axr.set_xlabel("UTC, 2026-11-20", color=INK2)
for ax in (axm, axt):
    plt.setp(ax.get_xticklabels(), visible=False)
axm.annotate("+4 mg while the plate is at 50-60 deg:\nthe balance's tilt offset, gone at 0 deg",
             xy=(blocks[0][1][-40][0], 3.5), xytext=(blocks[0][1][0][0], 15),
             fontsize=8.5, color=INK2,
             arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))

# right: delivered mass against auger revolutions
cl_path = sorted(glob.glob(os.path.join(CL, "trial_01_*.csv")))[0]
cl = from_csv(cl_path)
cl_rev = revs(cl)
cl0 = cl[0][1]
axd.plot(cl_rev, [r[1] - cl0 for r in cl], color=CL_C, lw=2)
for name, rows, rv in all_rows:
    if rv[-1] - rv[0] < 0.5:
        continue
    axd.plot(rv, [r[1] - m0 for r in rows], color=BA_C, lw=2)
axd.text(cl_rev[-1] + 3, 2.08, "calcium lactate, 03:06 trial 1:\n2.12 g in 16 rev",
         ha="left", va="center", fontsize=9, color=INK)
axd.text(cum, 0.12, "barium chloride, 17:35-17:43:\nabout 3 mg in {:.0f} rev".format(cum),
         ha="right", va="bottom", fontsize=9, color=INK)
axd.set_xlabel("auger revolutions turned", color=INK2)
axd.set_ylabel("powder in the beaker, g", color=INK2)
axd.set_xlim(-3, cum + 5)
axd.set_ylim(-0.1, 2.4)
axd.legend(handles=[plt.Line2D([], [], color=CL_C, lw=2, label="calcium lactate (2 g protocol)"),
                    plt.Line2D([], [], color=BA_C, lw=2, label="barium chloride (this session)")],
           loc="center right", frameon=False, fontsize=9)

for ax in (axm, axt, axr, axd):
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9)

fig.text(0.06, 0.965, "Barium chloride, 1.5 g protocol, 2026-11-20: nothing came out of the tube",
         fontsize=13, color=INK, weight="bold", va="top")
fig.text(0.06, 0.928, "The calcium lactate run's stepped-tilt protocol stopped itself twice on two stalled "
         "trials; a 0 deg priming spin and a 30-60 deg flow probe in between gave nothing either.",
         fontsize=9.5, color=INK2, va="top")
out = os.path.join(HERE, "session.png")
fig.savefig(out, dpi=130)
print("wrote", out, "total revs %.1f" % cum)
for name, rows, rv in all_rows:
    print("{:13s} {:5.1f} rev  balance {:+.1f} -> {:+.1f} mg (min {:+.1f}, max {:+.1f})".format(
        name, rv[-1] - rv[0], 1000 * (rows[0][1] - m0), 1000 * (rows[-1][1] - m0),
        1000 * (min(r[1] for r in rows) - m0), 1000 * (max(r[1] for r in rows) - m0)))

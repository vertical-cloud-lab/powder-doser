#!/usr/bin/env python3
"""Figure for issue #157: balance drift observed overnight in the EB B125 hood."""
import csv
import datetime as dt
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
BLUE = "#2a78d6"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e9e8e6"
BAND = "#dededa"

MDT = dt.timezone(dt.timedelta(hours=-6))

# (csv path, mtime of csv = end of sampling, survey-reported drift mg/min)
SEGS = [
    ("/tmp/drift157/seg0_smoke.csv", 1788842336.9, 13.5),
    ("/tmp/drift157/seg1.csv", 1788842777.2, 10.4),
    ("/tmp/drift157/seg2.csv", 1788843105.5, 7.5),
    ("/tmp/drift157/seg3.csv", 1788843434.2, 7.5),
    ("/tmp/drift157/seg4.csv", 1788843762.7, 5.5),
    ("/tmp/drift157/seg5.csv", 1788844091.3, 3.3),
]

# livestream frames: (overlay clock MDT, display grams); 22:47:07 frame blurred
FRAMES = [
    ("22:39:49", 0.1379),
    ("22:41:37", 0.1582),
    ("22:52:35", 0.2637),
    ("22:58:03", 0.2974),
    ("23:03:33", 0.3252),
    ("23:09:01", 0.3388),
]

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(10, 7.6), dpi=150, sharex=True,
    gridspec_kw={"height_ratios": [1.55, 1.0], "hspace": 0.12},
)
fig.patch.set_facecolor(SURFACE)

mid_times, rates = [], []
for path, mtime, rate in SEGS:
    rows = list(csv.DictReader(open(path)))
    t = [float(r["t_s"]) for r in rows]
    mg = [float(r["mg"]) for r in rows]
    t_abs0 = mtime - t[-1]
    times = [dt.datetime.fromtimestamp(t_abs0 + s, MDT) for s in t]
    ax1.plot(times, mg, color=BLUE, lw=2, solid_capstyle="round")
    mid_times.append(dt.datetime.fromtimestamp(t_abs0 + t[-1] / 2, MDT))
    rates.append(rate)

# livestream display readings as ring markers
ftimes = [dt.datetime(2026, 9, 7, *map(int, clk.split(":")), tzinfo=MDT)
          for clk, _ in FRAMES]
fmg = [g * 1000 for _, g in FRAMES]
ax1.plot(ftimes, fmg, "o", ms=9, mfc=SURFACE, mec=BLUE, mew=2, ls="none",
         zorder=5)
ax1.annotate(f"display 0.1379 g", (ftimes[0], fmg[0]), xytext=(8, -14),
             textcoords="offset points", fontsize=9.5, color=INK2)
ax1.annotate(f"display 0.3388 g", (ftimes[-1], fmg[-1]), xytext=(-8, 10),
             textcoords="offset points", fontsize=9.5, color=INK2, ha="right")
ax1.text(0.02, 0.86, "serial record (A&D 'Q' polls, ~3.5 Hz)\ngaps = frame grabs between segments",
         transform=ax1.transAxes, fontsize=9.5, color=INK2, va="top")

ax1.set_ylabel("balance reading  (mg)", color=INK)
ax1.set_title(
    "A&D HR-100A drifts +224 mg in 30 min with the lab empty and dark\n"
    "EB B125 fume hood, 2026-09-07 22:38–23:08 MDT — issue #157 observation",
    color=INK, fontsize=12.5, loc="left", pad=10,
)

# --- panel B: drift rate per segment, with exponential fit ---
# log-linear fit of rate vs midpoint time
tsec = [(mt - mid_times[0]).total_seconds() for mt in mid_times]
lr = [math.log(r) for r in rates]
n = len(tsec)
sx, sy = sum(tsec), sum(lr)
sxx = sum(x * x for x in tsec)
sxy = sum(x * y for x, y in zip(tsec, lr))
slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
intercept = (sy - slope * sx) / n
tau_min = -1.0 / slope / 60.0

band = ax2.axhspan(-3.6, 2.6, color=BAND, zorder=1)
ax2.annotate("range measured Sep 3 afternoon, hours after the move\n(issue #116 report: −3.6 to +2.6 mg/min, decaying)",
             (mid_times[0], -0.4), xytext=(4, 0), textcoords="offset points",
             fontsize=9, color=INK2, va="top")
ax2.axhline(0, color=INK2, lw=1)

fit_t = [mid_times[0] + dt.timedelta(seconds=s)
         for s in range(0, int(tsec[-1]) + 300, 60)]
fit_r = [math.exp(intercept + slope * (ft - mid_times[0]).total_seconds())
         for ft in fit_t]
ax2.plot(fit_t, fit_r, ls=(0, (4, 3)), color=INK2, lw=1.5, zorder=2)
k = int(len(fit_t) * 0.72)
ax2.annotate(f"exponential fit, τ ≈ {tau_min:.0f} min",
             (fit_t[k], fit_r[k]), xytext=(6, 12),
             textcoords="offset points", fontsize=9.5, color=INK2)

ax2.plot(mid_times, rates, "o", ms=9, color=BLUE, zorder=4)
for mt, r in zip(mid_times, rates):
    ax2.annotate(f"+{r:.1f}", (mt, r), xytext=(0, 9),
                 textcoords="offset points", ha="center",
                 fontsize=9.5, color=INK)

ax2.set_ylabel("drift rate  (mg/min)", color=INK)
ax2.set_xlabel("2026-09-07, lab-local time (MDT)", color=INK)
ax2.set_ylim(-4.6, 16.5)

for ax in (ax1, ax2):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=MDT))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))

fig.savefig("/tmp/drift157/drift_massing.png", bbox_inches="tight",
            facecolor=SURFACE)
print(f"tau = {tau_min:.1f} min; wrote /tmp/drift157/drift_massing.png")

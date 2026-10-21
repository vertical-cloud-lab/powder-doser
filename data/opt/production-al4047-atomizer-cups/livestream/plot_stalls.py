"""Issue #186, 2026-10-21: why the powder-doser livestream froze at 21:12:42 UTC on 10-20.

Video missing from each lab camera's 19:00 UTC broadcast, from YouTube's own ingest times
(gap_map.py's dumps), with the Zero's Wi-Fi events (its journal) underneath. Each step up is an
upload stall that YouTube never received video for.

    python3 data/opt/production-al4047-atomizer-cups/livestream/plot_stalls.py
"""
import datetime as dt
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates                                 # noqa: E402
import matplotlib.pyplot as plt                                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ZERO = os.path.join(HERE, "zero")
SURFACE, INK, INK2, MUTED, GRID, AXIS = (
    "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7")
# categorical slots 1-3 of the reference palette, in order
CAMS = [("3CvBrmkv2xE", "powder doser (picam-d1pr)", "#2a78d6"),
        ("z13xp1AcKag", "atomizer (picam-ot2)", "#eb6834"),
        ("jjnM7zFM6YE", "OT-2 overhead (hqcam-ot2-lid)", "#1baf7a")]
UTC = dt.timezone.utc
T0 = dt.datetime(2026, 10, 20, 19, 0, tzinfo=UTC)
T1 = dt.datetime(2026, 10, 20, 21, 45, tzinfo=UTC)
LAST_D1PR = dt.datetime(2026, 10, 20, 21, 12, 42, tzinfo=UTC)    # end of segment 3613
DOSE = (dt.datetime(2026, 10, 20, 21, 7, 48, tzinfo=UTC),        # cb3096e9, trial document
        dt.datetime(2026, 10, 20, 21, 12, 8, tzinfo=UTC))


def missing(vid):
    """(wall time, seconds of video missing so far) for every fetched segment after the
    first minute. Segment 0 of every broadcast reaches YouTube about 2 s late, so the baseline
    is the first fetched segment from 30 on (1 min in)."""
    segs = json.load(open(os.path.join(ZERO, "dump_%s.json" % vid)))["segments"]
    pts = sorted((int(k), v) for k, v in segs.items() if int(k) >= 30)
    n0, w0 = pts[0]
    return [(dt.datetime.fromtimestamp(w, UTC), (w - w0) - 2.0 * (n - n0)) for n, w in pts]


def wifi_events():
    """Zero journal: (time, kind) for each disconnect and each (re)association."""
    out = []
    for line in open(os.path.join(ZERO, "zero_wifi_journal_20261020.txt")):
        t = dt.datetime.fromisoformat(line.split()[0]).astimezone(UTC)
        if "CTRL-EVENT-DISCONNECTED" in line or "timed out" in line:
            out.append((t, "dropped"))
        elif "CTRL-EVENT-CONNECTED" in line:
            out.append((t, "joined"))
    return out


fig, ax = plt.subplots(figsize=(11, 5.2), dpi=150)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

ax.axvspan(*DOSE, color=GRID, lw=0, zorder=0)
ax.text(DOSE[0] - dt.timedelta(seconds=30), 640, "dose\ncb3096e9", ha="right", va="top",
        fontsize=8, color=INK2)
ax.axvspan(LAST_D1PR, T1, facecolor="none", edgecolor=AXIS, hatch="//", lw=0, zorder=0)
ax.text(LAST_D1PR + dt.timedelta(minutes=2), 455,
        "powder doser: nothing reaches\nYouTube after 21:12:42,\nstill listed as live",
        fontsize=9, color=INK, va="top")

for vid, name, color in CAMS:
    pts = [(t, m) for t, m in missing(vid) if t <= T1]
    ts, ms = zip(*pts)
    ax.plot(ts, ms, color=color, lw=2, solid_joinstyle="round", zorder=3, label=name)
    ax.annotate("%s: %.0f s" % (name.split(" (")[0], abs(ms[-1])), (ts[-1], ms[-1]),
                xytext=(6, 4 if vid != "jjnM7zFM6YE" else 6), textcoords="offset points",
                fontsize=9, color=INK)
d1 = missing("3CvBrmkv2xE")
ax.plot([d1[-1][0]], [d1[-1][1]], "o", ms=8, color=CAMS[0][2], mec=SURFACE, mew=2, zorder=4)

# Zero's Wi-Fi, as a rug along the bottom
ev = wifi_events()
for kind, y, mk in (("joined", -55, "|"), ("dropped", -55, "v")):
    xs = [t for t, k in ev if k == kind and T0 <= t <= T1]
    ax.plot(xs, [y] * len(xs), mk, ms=9 if mk == "|" else 7, color=INK2 if kind == "joined" else "#d03b3b",
            mew=1.5, ls="none", zorder=3,
            label="Zero: Wi-Fi (re)joined an access point" if kind == "joined"
            else "Zero: dropped by the access point")
ax.text(T0 + dt.timedelta(minutes=1), -30, "the doser's Zero, same bench and Wi-Fi network",
        fontsize=8, color=MUTED, va="bottom")

ax.set_xlim(T0, T1)
ax.set_ylim(-75, 760)
ax.set_ylabel("video missing from the broadcast (s, cumulative)", color=INK2)
ax.set_xlabel("2026-10-20, UTC (MDT = UTC − 6 h)", color=INK2)
ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 15, 30, 45]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=UTC))
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(AXIS)
ax.tick_params(colors=MUTED, labelcolor=INK2)
ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK2)
ax.set_title("The three lab cameras' 19:00 UTC broadcasts: upload stalls, and the powder doser's "
             "stop at 21:12:42", fontsize=11, color=INK, loc="left")
fig.tight_layout()
out = os.path.join(HERE, "livestream_stalls_20261020.png")
fig.savefig(out, facecolor=SURFACE)
print(out)

"""Issue #186, 2026-10-20 (fourth session, 15 wt% cup): the powder in the cup through bulk dose
5851b6d6 at 40° and the stepwise top-up after it (left), and the top-up's steps and settling reads
against the target (right). Built from the trial document and topup.py's output.

    python3 data/opt/production-al4047-atomizer-cups/plot_finish.py
"""
import datetime as dt
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402

import plot_15wt as p15                                           # noqa: E402

HERE = p15.HERE
ZERO = p15.ZERO
SURFACE, INK, INK2, MUTED = p15.SURFACE, p15.INK, p15.INK2, p15.MUTED
BULK, STEP = p15.BULK, p15.STEP
TARGET_G = p15.TARGET_G
# powder in the cup when 5851b6d6 tared: 42.5053 - 37.2151 g weighed by the operator, plus the
# balance's stable 0.0765 g over the operator's tare just before the dose (README)
BEFORE_G = 42.5053 - 37.2151 + 0.0765
TOPUP = "topup_20261020d.out"
START = ("22:17:30", 1.1023)            # topup.py's first stable read, before its first step
# stable reads over 5851b6d6's tare after the last step, from topup.py's FINAL line and the
# rig_cmd.py runs that eased the plate to 0° (their clock times are from the session, to a few s)
SETTLE = [("22:19:50", 1.2014), ("22:20:08", 1.2012), ("22:20:20", 1.2012),
          ("22:20:50", 1.2007), ("22:21:13", 1.2007), ("22:21:36", 1.2009)]


def main():
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 4.6), facecolor=SURFACE,
                                  gridspec_kw={"width_ratios": [1.2, 1]})
    p15.style(ax)
    p15.style(ax2)
    doc = p15.trial("5851b6d6")
    ts, gs, _ = p15.bulk_series(doc)
    day = ts[0]
    ax.plot(ts, [g + BEFORE_G for g in gs], color=BULK, linewidth=2,
            label="5851b6d6: closed-loop dose at 40°, 100 rpm, 2 Hz taps")
    st, sg = p15.step_series(os.path.join(ZERO, TOPUP), day, BEFORE_G)
    tt, tg = [], []
    for hms, g in [START] + SETTLE:
        h, mi, s = (int(x) for x in hms.split(":"))
        tt.append(day.replace(hour=h, minute=mi, second=s, microsecond=0))
        tg.append(g + BEFORE_G)
    st, sg = tt[:1] + st, tg[:1] + sg
    tt, tg = tt[1:], tg[1:]
    for a in (ax, ax2):
        a.plot(st, sg, color=STEP, linewidth=2, marker="o", markersize=3,
               label="forward auger steps at 40°, a stable read after each")
        a.plot(tt, tg, color=MUTED, linewidth=1.5, marker="o", markersize=3,
               label="settling reads; plate eased to 0° at 22:20")
        a.axhline(TARGET_G, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
        a.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(tz=dt.timezone.utc))
        a.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M", tz=dt.timezone.utc))
        a.set_xlabel("UTC, 2026-10-20", color=INK2, fontsize=9)
        a.set_ylabel("powder in the cup (g)", color=INK2, fontsize=9)
    ax.set_ylim(BEFORE_G - 0.05, TARGET_G + 0.08)
    ax.text(ax.get_xlim()[0], TARGET_G, " 15 wt% target, {:.4f} g".format(TARGET_G),
            color=INK2, fontsize=8, va="bottom")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="lower right")
    ax.set_title("Powder in the cup", color=INK, fontsize=11, loc="left")
    ax2.set_ylim(TARGET_G - 0.11, TARGET_G + 0.01)
    ax2.text(st[0], TARGET_G, "target {:.4f} g".format(TARGET_G), color=INK2, fontsize=8,
             va="bottom")
    ax2.annotate("last read {:.4f} g".format(tg[-1]), (tt[-1], tg[-1]), xytext=(-10, -28),
                 textcoords="offset points", ha="right", color=INK2, fontsize=8,
                 arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8})
    ax2.set_title("The top-up's 22 steps", color=INK, fontsize=11, loc="left")
    fig.tight_layout()
    out = os.path.join(HERE, "dose_15wt_finish.png")
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    print(out)


if __name__ == "__main__":
    main()

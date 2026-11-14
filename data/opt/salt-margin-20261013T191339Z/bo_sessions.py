#!/usr/bin/env python3
"""The margin campaign's BO doses over its two sessions (PR #166).

    python3 data/opt/salt-margin-20261013T191339Z/bo_sessions.py [out.png]

``salt-margin-20261013T191339Z`` ran its first 6 BO doses on 2026-10-13
and was resumed on 2026-10-15 (``run_20261015.md``).  Writes
``bo_sessions_20261015.png``:

(a)-(c) Every BO dose in order: dose time, |error| against the 0.5 g
        target, and the cutoff margin Ax picked.  Hollow marks ended as a
        jam (out of taps, stalled) or an overshoot; crosses are fw-error
        doses (the Pico's RESULT MemoryError, fixed in firmware
        trickle_tap/2026-10-15), which Ax never sees and which were
        dosed again at the same point.
(d)     Bulk feed per session: the bulk stage's settled mass over its
        duration, mg/s, for every dose at 40 deg bulk tilt and 20 rpm
        (the setting BO kept returning to) in both salt campaigns and the
        2026-10-06 validation blocks.  The first and last doses of
        10-15 are labeled with their start time (UTC).
(e)     Tap yield per session: mg the tap stage delivered per tap (from
        the settled reading after the PI trickle's cutoff to the final
        reading, auger nudges included), doses with at least 5 taps at
        the 15 deg tap tilt, same doses.

Also prints the numbers the PR comment and run_20261015.md quote.
"""

import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import compare_margin as cm                                   # noqa: E402

plt = cm.plt
orpt = cm.orpt
SESSION_COLOR = {"2026-10-13": cm.BLUE, "2026-10-15": "#1baf7a"}
PARENT_SESSIONS = ("2026-09-29", "2026-10-06")
TAP_TILT = 15.0


def day(utc):
    return (utc or "")[:10]


def bo_records(cdir):
    """BO records in dose order, fw-error tries included."""
    _doc, records, _p = orpt.load(cdir)
    return [r for r in records if r["mode"] == "bo"]


def tap_yields(cdir):
    """(session date, mg per tap) for doses with >= 5 taps at TAP_TILT."""
    out = []
    for t in cm.trial_docs(cdir).values():
        o = t.get("outcomes") or {}
        p = t.get("parameters") or {}
        taps = o.get("taps") or 0
        evs = [e for e in t.get("stop_events") or []
               if e.get("phase") == "trickle"
               and e.get("settled_g") is not None]
        if (taps < 5 or not evs or o.get("settled_final_g") is None
                or p.get("tap_tilt_deg") != TAP_TILT):
            continue
        mg = 1000.0 * (o["settled_final_g"] - evs[-1]["settled_g"])
        out.append((day(t.get("started_utc")), mg / taps))
    return out


def bulk_feed(cdir):
    """(session date, mg/s, start HH:MM) of the bulk stage at 40 deg /
    20 rpm."""
    out = []
    for t in cm.trial_docs(cdir).values():
        o = t.get("outcomes") or {}
        p = t.get("parameters") or {}
        evs = [e for e in t.get("stop_events") or []
               if e.get("phase") == "bulk"
               and e.get("settled_g") is not None]
        if (not evs or not o.get("t_bulk_s")
                or p.get("bulk_tilt_deg") != 40.0
                or p.get("bulk_rpm") != 20.0):
            continue
        out.append((day(t.get("started_utc")),
                    1000.0 * evs[0]["settled_g"] / o["t_bulk_s"],
                    (t.get("started_utc") or "")[11:16]))
    return out


def strip(ax, pts, sessions, floor, label_ends=None):
    """One column of jittered points per session, median bar."""
    for i, sess in enumerate(sessions):
        ys = sorted(v for d, v, *_ in pts if d == sess)
        color = SESSION_COLOR.get(sess, cm.GRAY)
        for j, v in enumerate(ys):
            dx = ((j % 9) - 4) * 0.05
            ax.scatter(i + dx, max(v, floor), s=24, color=color, lw=0,
                       alpha=0.9, zorder=3)
        if ys:
            med = statistics.median(ys)
            ax.plot([i - 0.3, i + 0.3], [med, med], color=cm.INK, lw=1.6,
                    zorder=4)
            ax.annotate("{:.2g}".format(med), (i + 0.3, med),
                        xytext=(3, 0), textcoords="offset points",
                        fontsize=8, color=cm.INK_2, va="center")
    if label_ends:
        sess = label_ends
        i = sessions.index(sess)
        same = sorted((hm, v) for d, v, hm in pts if d == sess)
        if same:
            for hm, v in (same[0], same[-1]):
                ax.annotate(hm, (i, max(v, floor)), xytext=(-6, 0),
                            textcoords="offset points", fontsize=7.5,
                            color=cm.INK_2, ha="right", va="center")
    ax.set_yscale("log")
    from matplotlib.ticker import NullLocator
    ax.yaxis.set_major_formatter(plt.FuncFormatter(
        lambda v, _p: "{:g}".format(v)))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_xlim(-0.6, len(sessions) - 0.2)
    ax.set_xticks(range(len(sessions)))
    cm.style(ax)


def main(argv):
    out_png = argv[1] if len(argv) > 1 else os.path.join(
        HERE, "bo_sessions_20261015.png")
    recs = bo_records(HERE)
    labels = []
    for r in recs:
        if r["label"] not in labels:
            labels.append(r["label"])
    x_of = {lab: i for i, lab in enumerate(labels)}

    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": cm.INK_2,
        "axes.labelcolor": cm.INK, "xtick.color": cm.INK_2,
        "ytick.color": cm.INK_2, "text.color": cm.INK,
        "axes.facecolor": cm.SURFACE, "figure.facecolor": cm.SURFACE})
    fig = plt.figure(figsize=(15.5, 7.2))
    gs = fig.add_gridspec(3, 2, width_ratios=[2.3, 1.0], hspace=0.12,
                          wspace=0.22)
    at = fig.add_subplot(gs[0, 0])
    ae = fig.add_subplot(gs[1, 0], sharex=at)
    am = fig.add_subplot(gs[2, 0], sharex=at)
    right = gs[:, 1].subgridspec(2, 1, hspace=0.32)
    ab = fig.add_subplot(right[0])
    ay = fig.add_subplot(right[1])

    for r in recs:
        s = r["summary"]
        x = x_of[r["label"]]
        color = SESSION_COLOR.get(day(r["utc"]), cm.GRAY)
        if s["infra_error"]:
            if s.get("t_total_s"):
                at.scatter(x, s["t_total_s"], marker="x", s=34,
                           color=cm.INK_2, lw=1.2, zorder=4)
            continue
        if r.get("void"):
            continue
        clean = (s["status"] == "ok" and not s["jam"])
        kw = dict(s=46, zorder=3, linewidths=1.4, edgecolors=color,
                  facecolors=color if clean else cm.SURFACE)
        if s.get("t_total_s") is not None:
            at.scatter(x, s["t_total_s"], **kw)
        if s.get("abs_error_mg") is not None:
            ae.scatter(x, max(s["abs_error_mg"], 0.3), **kw)
        margin = (r.get("params") or {}).get("cutoff_margin_g")
        if margin is not None:
            am.scatter(x, 1000.0 * margin, **kw)

    first_new = next((x_of[r["label"]] for r in recs
                      if day(r["utc"]) == "2026-10-15"), None)
    for ax in (at, ae, am):
        cm.style(ax)
        if first_new is not None:
            ax.axvline(first_new - 0.5, color=cm.INK_2, lw=0.8, ls=":",
                       zorder=1)
    if first_new is not None:
        import matplotlib.transforms as mtransforms
        tr = mtransforms.blended_transform_factory(at.transData,
                                                   at.transAxes)
        at.text(first_new - 0.6, 0.04, "10-13", ha="right", va="bottom",
                color=cm.INK_2, fontsize=8.5, transform=tr)
        at.text(first_new - 0.4, 0.04, "10-15", ha="left", va="bottom",
                color=cm.INK_2, fontsize=8.5, transform=tr)
    at.axhline(180, color=cm.INK_2, lw=0.8, ls="--", zorder=1)
    cm.log_seconds(at, "y", ticks=(15, 30, 60, 120, 240, 480))
    at.set_ylim(12, 700)
    at.set_ylabel("dose time (s, log)")
    at.set_title("(a)-(c) The BO doses in order", loc="left",
                 fontsize=10)
    ae.axhline(20, color=cm.INK_2, lw=0.8, ls="--", zorder=1)
    cm.log_seconds(ae, "y", ticks=(0.3, 1, 3, 10, 30, 100, 300))
    ae.set_ylim(0.2, 600)
    ae.set_ylabel("|error| (mg, log)")
    am.set_ylim(-3, 38)
    am.set_yticks([0, 10, 17.5, 25, 35])
    am.set_yticklabels(["0", "10", "17.5", "25", "35"])
    am.set_ylabel("cutoff margin (mg)")
    am.set_xticks(range(len(labels)))
    am.set_xticklabels(labels, rotation=90, fontsize=8)
    for ax in (at, ae):
        plt.setp(ax.get_xticklabels(), visible=False)

    # (d) bulk feed, (e) tap yield, by session ---------------------------
    from matplotlib.ticker import FixedLocator
    sessions = list(PARENT_SESSIONS) + list(SESSION_COLOR)
    feed = bulk_feed(cm.PARENT) + bulk_feed(HERE)
    strip(ab, feed, sessions, 0.5, label_ends="2026-10-15")
    ab.yaxis.set_major_locator(FixedLocator([1, 3, 10, 30]))
    ab.set_ylim(0.6, 80)
    ab.set_xticklabels([])
    ab.set_ylabel("bulk feed (mg/s, log)")
    ab.set_title("(d) Bulk feed at 40\u00b0 tilt, 20 rpm (bar: median)",
                 loc="left", fontsize=10)
    pts = [(d, v, "") for d, v in tap_yields(cm.PARENT) + tap_yields(HERE)]
    strip(ay, pts, sessions, 0.05)
    ay.yaxis.set_major_locator(FixedLocator([0.1, 0.3, 1, 3]))
    ay.set_ylim(0.04, 10)
    ay.set_xticklabels([s[5:] for s in sessions])
    ay.set_xlabel("session (2026)")
    ay.set_ylabel("mg per tap (log)")
    ay.set_title("(e) Tap yield at 15\u00b0 tap tilt, \u2265 5 taps",
                 loc="left", fontsize=10)

    handles = [
        plt.Line2D([], [], ls="", marker="o", ms=7, color=cm.BLUE,
                   label="BO dose, 10-13"),
        plt.Line2D([], [], ls="", marker="o", ms=7,
                   color=SESSION_COLOR["2026-10-15"],
                   label="BO dose, 10-15"),
        plt.Line2D([], [], ls="", marker="o", ms=7, mfc=cm.SURFACE,
                   mec=cm.INK_2, label="jam or overshoot (hollow)"),
        plt.Line2D([], [], ls="", marker="x", ms=7, color=cm.INK_2,
                   label="fw-error, dosed again"),
        plt.Line2D([], [], ls="", marker="o", ms=6, color=cm.GRAY,
                   label="09-29 campaign / 10-06 validation (d, e)"),
        plt.Line2D([], [], color=cm.INK_2, lw=0.8, ls="--",
                   label="180 s / 20 mg thresholds")]
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False,
               fontsize=8.5, bbox_to_anchor=(0.5, -0.06))
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out_png)

    # -- numbers for the write-up ----------------------------------------
    print("\nBO doses (label, session, status, t s, |err| mg, margin mg):")
    for r in recs:
        s = r["summary"]
        m = (r.get("params") or {}).get("cutoff_margin_g")
        print("  {:8s} {} {:13s} {:>7} {:>7} {:>5}".format(
            r["label"], day(r["utc"])[5:], s["status"],
            s.get("t_total_s"), s.get("abs_error_mg"),
            None if m is None else round(1000 * m, 1)))
    print("\nbulk feed at 40 deg / 20 rpm (mg/s):")
    for sess in sessions:
        ys = [v for d, v, _hm in feed if d == sess]
        if ys:
            print("  {}: n={:2d} median {:.1f} range {:.1f}-{:.1f}".format(
                sess, len(ys), statistics.median(ys), min(ys), max(ys)))
    print("  10-15 in order:", ", ".join("{} {:.1f}".format(hm, v) for d, v, hm
                                         in sorted(feed, key=lambda x: x[2])
                                         if d == "2026-10-15"))
    print("\ntap yield at {} deg (mg/tap):".format(TAP_TILT))
    for sess in sessions:
        ys = [v for d, v, _e in pts if d == sess]
        if ys:
            print("  {}: n={:2d} median {:.2f} range {:.2f}-{:.2f}".format(
                sess, len(ys), statistics.median(ys), min(ys), max(ys)))
    for sess in SESSION_COLOR:
        ok = [r for r in recs if day(r["utc"]) == sess
              and not r["summary"]["infra_error"]]
        bad = [r for r in recs if day(r["utc"]) == sess
               and r["summary"]["infra_error"]]
        print("{}: {} usable BO doses, {} fw-error".format(
            sess, len(ok), len(bad)))


if __name__ == "__main__":
    main(sys.argv)

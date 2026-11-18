#!/usr/bin/env python3
"""Turn a three_phase_tilt_trials.py session log into per-trial CSVs.

The log is what ``hardware/test-module/firmware/three_phase_tilt_trials.py``
prints on the Pico, with every line prefixed on the Pi by its UTC receipt
time (``<epoch s>\\t<line>``, see ``stamp.py`` in the data README).  The
Pico's own millisecond clock times every frame; the Pi stamps anchor it to
UTC (offset = the smallest receipt-minus-Pico gap, i.e. the line that
crossed USB fastest).

Writes into ``--out``:

* ``trial_NN_<YYYY-MM-DD>_<HHMMSS>Z.csv`` -- one per trial, one row per
  balance frame, with the trial number and UTC date and time on every row;
* ``trials_summary.csv`` -- one row per trial;
* ``tilt_trials_overview.png``, ``tilt_trials_summary.png`` and
  ``tilt_trial_example.png``.

``--upload`` also inserts one MongoDB document per trial plus one session
document into ``powder_doser.dose_runs`` (needs PI_MONGODB_URI or
MONGODB_URI; skips documents that are already there).

Usage::

    python scripts/analyze_tilt_trials.py LOG --out DIR [--upload]
"""

import argparse
import csv
import json
import os
import statistics
import sys
from datetime import datetime, timezone

STAGE_COLORS = {            # validated categorical slots 1-3 (bulk/fine/tap)
    "bulk": "#2a78d6",
    "fine": "#eb6834",
    "tap": "#1baf7a",
}
NEUTRAL = "#a3a29c"         # pre-roll / baseline / post-roll
INK = "#0b0b0b"
INK2 = "#52514e"
SURFACE = "#fcfcfb"


def utc(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


def parse(path):
    meta, frames, events, clogs, trials, starts = {}, [], [], [], [], {}
    summary = None
    offsets = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            raw = raw.rstrip("\n")
            if "\t" not in raw:
                continue
            host_s, line = raw.split("\t", 1)
            try:
                host = float(host_s)
            except ValueError:
                continue
            line = line.rstrip("\r")
            tag = line.split(",", 1)[0]
            try:
                if tag == "M":
                    _, key, val = line.split(",", 2)
                    meta[key] = val
                elif tag == "S":
                    p = line.split(",")
                    fr = {
                        "trial": int(p[1]), "t_ms": int(p[2]), "src": p[3],
                        "stat": p[4], "grams": float(p[5]) if p[5] else None,
                        "stage": p[6], "tilt": float(p[7]),
                        "rpm": float(p[8]), "taps": int(p[9]),
                        "dur_ms": int(p[10]) if len(p) > 10 else None,
                    }
                    frames.append(fr)
                    offsets.append(host - fr["t_ms"] / 1000.0)
                elif tag in ("E", "L"):
                    p = line.split(",", 3)
                    rec = {"trial": int(p[1]), "t_ms": int(p[2]),
                           "text": p[3]}
                    (events if tag == "E" else clogs).append(rec)
                    offsets.append(host - rec["t_ms"] / 1000.0)
                elif tag == "T":
                    trials.append(json.loads(line[2:]))
                elif tag == "TRIAL_START":
                    p = line.split(",")
                    starts[int(p[1])] = int(p[2])
                elif tag == "SUMMARY":
                    summary = json.loads(line[len("SUMMARY,"):])
            except (ValueError, IndexError, json.JSONDecodeError):
                continue                  # a line cut short by a disconnect
    if not offsets:
        sys.exit("no timestamped telemetry in {}".format(path))
    return {
        "meta": meta, "frames": frames, "events": events, "clogs": clogs,
        "trials": {t["trial"]: t for t in trials}, "starts": starts,
        "summary": summary, "offset": min(offsets),
    }


def linfit(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def stage_spans(evs):
    """{stage: (start_ms, end_ms)} from 'stage X start' / 'stage X end'."""
    spans = {}
    for e in evs:
        words = e["text"].split()
        if len(words) >= 3 and words[0] == "stage":
            name, what = words[1], words[2]
            if what == "start":
                spans[name] = [e["t_ms"], None]
            elif what == "end" and name in spans:
                spans[name][1] = e["t_ms"]
    return spans


def build(d, out_dir):
    meta, offset = d["meta"], d["offset"]
    powder = meta.get("powder_id", "salt")
    target = float(meta.get("target_g", "1.0"))
    by_trial = {}
    for fr in d["frames"]:
        by_trial.setdefault(fr["trial"], []).append(fr)
    ev_by = {}
    for e in d["events"]:
        ev_by.setdefault(e["trial"], []).append(e)
    log_by = {}
    for c in d["clogs"]:
        log_by.setdefault(c["trial"], []).append(c)

    rows_summary, series = [], {}
    for n in sorted(k for k in by_trial if k > 0):
        frs = by_trial[n]
        evs = ev_by.get(n, [])
        rec = d["trials"].get(n, {})
        t0_ms = d["starts"].get(n, frs[0]["t_ms"])
        start = utc(t0_ms / 1000.0 + offset)
        base = rec.get("baseline_abs_g")
        if base is None:                  # trial cut short: pre-roll median
            pre = [f["grams"] for f in frs
                   if f["stage"] == "pre" and f["grams"] is not None]
            base = statistics.median(pre) if pre else None
        fname = "trial_{:02d}_{}Z.csv".format(
            n, start.strftime("%Y-%m-%d_%H%M%S"))

        # events attach to the first frame at or after them
        evq = sorted(evs, key=lambda e: e["t_ms"])
        ei = 0
        prev_g = None
        out_rows = []
        for f in frs:
            texts = []
            while ei < len(evq) and evq[ei]["t_ms"] <= f["t_ms"]:
                texts.append(evq[ei]["text"])
                ei += 1
            ts = utc(f["t_ms"] / 1000.0 + offset)
            g = f["grams"]
            out_rows.append({
                "powder_id": powder, "trial": n,
                "date_utc": ts.strftime("%Y-%m-%d"),
                "time_utc": ts.strftime("%H:%M:%S.%f")[:-3],
                "t_s": "{:.3f}".format((f["t_ms"] - t0_ms) / 1000.0),
                "mass_abs_g": "" if g is None else "{:.4f}".format(g),
                "mass_g": ("" if g is None or base is None
                           else "{:.4f}".format(g - base)),
                "balance_status": f["stat"],
                "fresh": ("" if g is None else
                          int(prev_g is None or g != prev_g)),
                "source": f["src"], "stage": f["stage"],
                "tilt_deg": "{:.1f}".format(f["tilt"]),
                "auger_rpm": "{:.1f}".format(f["rpm"]),
                "taps_cum": f["taps"],
                "poll_ms": "" if f["dur_ms"] is None else f["dur_ms"],
                "events": " | ".join(texts),
            })
            if g is not None:
                prev_g = g
        with open(os.path.join(out_dir, fname), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
            w.writeheader()
            w.writerows(out_rows)

        spans = stage_spans(evs)
        dur = {k: (round((v[1] - v[0]) / 1000.0, 1) if v[1] else None)
               for k, v in spans.items()}
        halts = {h.get("phase"): h for h in rec.get("halts", [])}
        steps = [e["text"].split("-> ", 1)[1] for e in evs
                 if e["text"].startswith("tilt schedule")]
        pre = [(f["t_ms"] / 1000.0, f["grams"]) for f in frs
               if f["stage"] == "pre" and f["grams"] is not None]
        post = [(f["t_ms"] / 1000.0, f["grams"]) for f in frs
                if f["stage"] == "post" and f["grams"] is not None]
        drift_pre = linfit([a for a, _ in pre], [b for _, b in pre])
        drift_post = linfit([a for a, _ in post], [b for _, b in post])
        span_s = (frs[-1]["t_ms"] - frs[0]["t_ms"]) / 1000.0
        cyc = {k: v for k, v in rec.get("phase_cycles", [])}
        nudges = sum(1 for c in log_by.get(n, []) if "nudging auger" in c["text"])
        end = utc(frs[-1]["t_ms"] / 1000.0 + offset)
        bulk_h, fine_h = halts.get("bulk", {}), halts.get("fine", {})

        def mg(x):
            return "" if x is None else round(1000.0 * x, 1)

        def g4(x):
            return "" if x is None else round(x, 4)

        rows_summary.append({
            "powder_id": powder, "trial": n,
            "date_utc": start.strftime("%Y-%m-%d"),
            "start_utc": start.strftime("%H:%M:%S"),
            "end_utc": end.strftime("%H:%M:%S"),
            "csv": fname,
            "status": rec.get("status", "incomplete"),
            "target_g": target,
            "final_g": g4(rec.get("final_g")),
            "error_mg": "" if rec.get("error_mg") is None else rec["error_mg"],
            "controller_reported_g": g4(rec.get("dose_reported_g")),
            "dose_s": ("" if "t_done_ms" not in rec else
                       round((rec["t_done_ms"] - rec["t_dose_ms"]) / 1000.0, 1)),
            "bulk_s": dur.get("bulk", ""), "fine_s": dur.get("fine", ""),
            "tap_s": dur.get("tap", ""),
            "bulk_halt_g": g4(bulk_h.get("m_stop_g")),
            "bulk_settled_g": g4(bulk_h.get("settled_g")),
            "bulk_afterflow_mg": mg(bulk_h.get("afterflow_g")),
            "bulk_rate_at_halt_g_per_s": g4(bulk_h.get("rate_slope_gps")),
            "fine_halt_g": g4(fine_h.get("m_stop_g")),
            "fine_settled_g": g4(fine_h.get("settled_g")),
            "fine_afterflow_mg": mg(fine_h.get("afterflow_g")),
            "fine_rate_at_halt_g_per_s": g4(fine_h.get("rate_slope_gps")),
            "tap_cycles": cyc.get("tap", ""), "taps": rec.get("taps", ""),
            "nudges": nudges, "auger_rev": rec.get("auger_rev", ""),
            "bulk_tilt_steps": "; ".join(steps),
            "no_flow_steps": sum(1 for s in steps if "no flow" in s),
            "preroll_drift_mg_per_min": ("" if drift_pre is None
                                         else round(60000.0 * drift_pre, 2)),
            "postroll_drift_mg_per_min": ("" if drift_post is None
                                          else round(60000.0 * drift_post, 2)),
            "baseline_abs_g": g4(base),
            "frames": len(frs),
            "frame_rate_hz": round(len(frs) / span_s, 2) if span_s > 0 else "",
        })
        series[n] = {"rows": out_rows, "spans": spans, "t0_ms": t0_ms,
                     "events": evs, "status": rec.get("status", "incomplete"),
                     "error_mg": rec.get("error_mg")}

    with open(os.path.join(out_dir, "trials_summary.csv"), "w",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_summary[0]))
        w.writeheader()
        w.writerows(rows_summary)
    return rows_summary, series


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------

def _style(plt):
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "axes.edgecolor": "#c9c8c2", "axes.labelcolor": INK2,
        "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
        "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 9,
    })


def _stage_segments(rows):
    """Split a trial's rows into contiguous (stage, t[], m[]) runs."""
    segs, cur = [], None
    for r in rows:
        if r["mass_g"] == "":
            continue
        st = r["stage"] if r["stage"] in STAGE_COLORS else "other"
        t, m = float(r["t_s"]), float(r["mass_g"])
        if cur is None or cur[0] != st:
            if cur is not None:              # join segments at the seam
                cur[1].append(t)
                cur[2].append(m)
            cur = (st, [t], [m])
            segs.append(cur)
        else:
            cur[1].append(t)
            cur[2].append(m)
    return segs


def figures(rows_summary, series, out_dir, target):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    _style(plt)
    trials = sorted(series)
    legend = [Line2D([], [], color=STAGE_COLORS[s], lw=2, label=s)
              for s in ("bulk", "fine", "tap")]
    legend.append(Line2D([], [], color=NEUTRAL, lw=2,
                         label="before / after the dose"))

    # 1 -- small multiples, one panel per trial, shared axes
    ncol = 6
    nrow = (len(trials) + ncol - 1) // ncol
    fig, axes = plt.subplots(nrow, ncol, figsize=(13, 2.0 * nrow + 0.9),
                             sharex=True, sharey=True, squeeze=False)
    tmax = max(float(series[n]["rows"][-1]["t_s"]) for n in trials)
    for i, ax in enumerate(axes.flat):
        if i >= len(trials):
            ax.axis("off")
            continue
        n = trials[i]
        for st, ts, ms in _stage_segments(series[n]["rows"]):
            ax.plot(ts, ms, color=STAGE_COLORS.get(st, NEUTRAL), lw=1.2)
        ax.axhline(target, color=INK2, lw=0.6, ls=(0, (3, 3)))
        err = series[n]["error_mg"]
        lab = "#{}  {}".format(n, series[n]["status"])
        if err is not None:
            lab += "  {:+.1f} mg".format(err)
        ax.set_title(lab, fontsize=8, color=INK, loc="left")
        ax.set_xlim(0, tmax)
        ax.set_ylim(-0.05, 1.12)
    for ax in axes[-1]:
        ax.set_xlabel("time since trial start (s)")
    for row in axes:
        row[0].set_ylabel("mass in cup (g)")
    fig.legend(handles=legend, loc="upper right", ncol=4, frameon=False,
               bbox_to_anchor=(0.99, 1.0))
    fig.suptitle("1 g salt doses: cup mass vs time, colored by controller "
                 "stage (dashed line = 1 g target)", x=0.01, ha="left",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(os.path.join(out_dir, "tilt_trials_overview.png"), dpi=130)
    plt.close(fig)

    # 2 -- per-trial outcome + stage durations (two charts, one axis each)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
    xs = [r["trial"] for r in rows_summary]
    errs = [r["error_mg"] for r in rows_summary]
    a1.axhspan(-1, 1, color="#e6e5e0", lw=0)
    a1.axhline(0, color=INK2, lw=0.6)
    pts = [(x, e) for x, e in zip(xs, errs) if e != ""]
    a1.plot([p[0] for p in pts], [p[1] for p in pts], "o", ms=6,
            color=STAGE_COLORS["bulk"], mec=SURFACE, mew=1.5)
    a1.set_xlabel("trial")
    a1.set_ylabel("final mass - 1 g (mg)")
    a1.set_title("Final error per trial (grey band = +/-1 mg tolerance)",
                 loc="left", fontsize=10)
    bottoms = [0.0] * len(xs)
    for st in ("bulk", "fine", "tap"):
        vals = [float(r[st + "_s"]) if r[st + "_s"] not in ("", None) else 0.0
                for r in rows_summary]
        a2.bar(xs, vals, bottom=bottoms, color=STAGE_COLORS[st], width=0.75,
               edgecolor=SURFACE, linewidth=1.0, label=st)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    a2.set_xlabel("trial")
    a2.set_ylabel("stage duration (s)")
    a2.set_title("Time in each stage", loc="left", fontsize=10)
    a2.legend(frameon=False, ncol=3, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "tilt_trials_summary.png"), dpi=130)
    plt.close(fig)

    # 3 -- one trial in full: mass, tilt, rpm, taps on a shared time axis
    done = [r for r in rows_summary if r["dose_s"] != ""]
    if not done:
        return
    durs = sorted(float(r["dose_s"]) for r in done)
    med = durs[len(durs) // 2]
    pick = min(done, key=lambda r: abs(float(r["dose_s"]) - med))["trial"]
    rows = series[pick]["rows"]
    ts = [float(r["t_s"]) for r in rows]
    fig, axs = plt.subplots(4, 1, figsize=(10, 8.2), sharex=True,
                            gridspec_kw={"height_ratios": [3, 1.2, 1.2, 1.2]})
    for st, tt, mm in _stage_segments(rows):
        axs[0].plot(tt, mm, color=STAGE_COLORS.get(st, NEUTRAL), lw=1.4)
    axs[0].axhline(target, color=INK2, lw=0.6, ls=(0, (3, 3)))
    axs[0].set_ylabel("mass in cup (g)")
    axs[0].legend(handles=legend, frameon=False, ncol=4, loc="upper left")
    axs[1].step(ts, [float(r["tilt_deg"]) for r in rows], where="post",
                color=INK2, lw=1.4)
    axs[1].set_ylabel("plate tilt (deg)")
    axs[2].step(ts, [float(r["auger_rpm"]) for r in rows], where="post",
                color=INK2, lw=1.4)
    axs[2].set_ylabel("auger (rpm)")
    axs[3].step(ts, [int(r["taps_cum"]) for r in rows], where="post",
                color=INK2, lw=1.4)
    axs[3].set_ylabel("taps (cumulative)")
    axs[3].set_xlabel("time since trial start (s)")
    r0 = next(r for r in rows_summary if r["trial"] == pick)
    fig.suptitle("Trial {} ({} {} UTC): {}, final {} g ({} mg)".format(
        pick, r0["date_utc"], r0["start_utc"], r0["status"], r0["final_g"],
        r0["error_mg"]), x=0.01, ha="left", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(out_dir, "tilt_trial_example.png"), dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------

def upload(d, rows_summary, series, session_id, extra):
    from pymongo import MongoClient
    uri = os.environ.get("PI_MONGODB_URI") or os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("set PI_MONGODB_URI or MONGODB_URI")
    coll = MongoClient(uri, serverSelectionTimeoutMS=20000)[
        "powder_doser"]["dose_runs"]
    inserted = []
    for r in rows_summary:
        n = r["trial"]
        key = {"doc_type": "three_phase_tilt_trial",
               "session_id": session_id, "trial": n}
        if coll.count_documents(key, limit=1):
            continue
        rows = series[n]["rows"]
        doc = dict(key)
        doc.update({
            "powder_id": r["powder_id"], "pr": 131,
            "started_utc": "{}T{}Z".format(r["date_utc"], r["start_utc"]),
            "summary": r, "params": d["meta"],
            "trial_record": d["trials"].get(n),
            "events": [{"t_s": round((e["t_ms"] - series[n]["t0_ms"]) / 1000.0,
                                     3), "text": e["text"]}
                       for e in series[n]["events"]],
            "series": {
                k: [row[k] for row in rows]
                for k in ("time_utc", "t_s", "mass_abs_g", "mass_g",
                          "balance_status", "source", "stage", "tilt_deg",
                          "auger_rpm", "taps_cum")
            },
        })
        doc.update(extra)
        inserted.append(str(coll.insert_one(doc).inserted_id))
    skey = {"doc_type": "three_phase_tilt_session", "session_id": session_id}
    if not coll.count_documents(skey, limit=1):
        sdoc = dict(skey)
        sdoc.update({"powder_id": rows_summary[0]["powder_id"], "pr": 131,
                     "params": d["meta"], "session_summary": d["summary"],
                     "trials": rows_summary})
        sdoc.update(extra)
        inserted.append(str(coll.insert_one(sdoc).inserted_id))
    return inserted


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("log")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--session-id", default=None)
    ap.add_argument("--extra-json", default=None,
                    help="JSON object merged into every uploaded document")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    d = parse(a.log)
    rows_summary, series = build(d, a.out)
    target = float(d["meta"].get("target_g", "1.0"))
    if not a.no_figures:
        figures(rows_summary, series, a.out, target)
    ok = [r for r in rows_summary if r["error_mg"] != ""]
    print("trials: {}  statuses: {}".format(
        len(rows_summary),
        {s: sum(1 for r in rows_summary if r["status"] == s)
         for s in sorted({r["status"] for r in rows_summary})}))
    if ok:
        errs = [float(r["error_mg"]) for r in ok]
        print("final error mg: median {:+.1f}, min {:+.1f}, max {:+.1f}".format(
            statistics.median(errs), min(errs), max(errs)))
    print("session summary:", d["summary"])
    if a.upload:
        sid = a.session_id or "tilt30-{}".format(
            rows_summary[0]["date_utc"] + "T" + rows_summary[0]["start_utc"])
        extra = json.loads(a.extra_json) if a.extra_json else {}
        ids = upload(d, rows_summary, series, sid, extra)
        print("uploaded {} documents (session {})".format(len(ids), sid))


if __name__ == "__main__":
    main()

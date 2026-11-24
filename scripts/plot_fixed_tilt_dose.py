#!/usr/bin/env python3
"""Figure (and MongoDB record) for the 2026-11-24 3 g CMC dose at 60 deg (PR #131).

Reads the per-dose CSVs that ``scripts/analyze_tilt_trials.py`` wrote from
the two session logs of ``hardware/test-module/firmware/fixed_tilt_dose.py``
(dose 1 = version 2026-11-24a, the top-up = 2026-11-24b) and draws
``cmc_3g_60deg.png``:

* A: the cup over the whole session, against dose 1's baseline (0.0429 g
  displayed, plate at 0 deg), coloured by controller stage;
* B: the feed rate while the auger turned, in 10 s windows (mg/s);
* C: the top-up's last 25 s, in mg to go, with the +/-1 mg band.

``--upload`` inserts one ``doc_type: "fixed_tilt_dose"`` document with both
doses' records and full series into ``powder_doser.dose_runs`` (needs
PI_MONGODB_URI or MONGODB_URI; skipped if the session is already there).

Usage::

    python scripts/plot_fixed_tilt_dose.py DATA_DIR [--upload]
"""

import argparse
import csv
import glob
import json
import os
import sys
from datetime import datetime, timezone

STAGE_COLORS = {"bulk": "#2a78d6", "fine": "#eb6834", "tap": "#1baf7a"}
NEUTRAL = "#a3a29c"
INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"
SESSION_BASE_G = 0.0429     # dose 1's baseline (displayed g, plate at 0 deg)
TARGET_G = 3.0
SESSION_ID = "fixed-tilt-dose-2026-11-24T19:52:41Z"


def load(path):
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            if not r["mass_abs_g"]:
                continue
            ts = datetime.strptime(r["date_utc"] + " " + r["time_utc"],
                                   "%Y-%m-%d %H:%M:%S.%f").replace(
                                       tzinfo=timezone.utc)
            r["epoch"] = ts.timestamp()
            r["cup_g"] = float(r["mass_abs_g"]) - SESSION_BASE_G
            r["rpm"] = float(r["auger_rpm"])
            rows.append(r)
    return rows


def segments(rows):
    """Consecutive runs of the same stage (pre/post/session -> neutral)."""
    out, cur = [], None
    for r in rows:
        st = r["stage"] if r["stage"] in STAGE_COLORS else "other"
        if cur is None or cur[0] != st:
            if cur is not None:
                cur[1].append(r)          # join the segments
            cur = (st, [r])
            out.append(cur)
        else:
            cur[1].append(r)
    return out


def rate_windows(rows, win_s=10.0):
    """(mid epoch, mg/s, stage) over windows where the auger turned."""
    spin = [r for r in rows if r["rpm"] > 0]
    out = []
    i = 0
    while i < len(spin):
        t0 = spin[i]["epoch"]
        j = i
        while j + 1 < len(spin) and spin[j + 1]["epoch"] - t0 < win_s \
                and spin[j + 1]["stage"] == spin[i]["stage"]:
            j += 1
        dt = spin[j]["epoch"] - t0
        if dt >= 0.6 * win_s:
            out.append(((t0 + spin[j]["epoch"]) / 2.0,
                        1000.0 * (spin[j]["cup_g"] - spin[i]["cup_g"]) / dt,
                        spin[i]["stage"]))
        i = j + 1
    return out


def figure(doses, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
        "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
        "axes.spines.right": False, "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE})
    fig = plt.figure(figsize=(10.5, 7.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.35, 1.0], hspace=0.38,
                          wspace=0.32)
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, :2], sharex=ax_a)
    ax_c = fig.add_subplot(gs[1, 2])

    def dt(e):
        return datetime.fromtimestamp(e, tz=timezone.utc)

    seen = set()
    for name, rows in doses:
        for st, seg in segments(rows):
            col = STAGE_COLORS.get(st, NEUTRAL)
            lab = None
            if st not in seen:
                lab = {"bulk": "bulk: 80 rpm, tap every 300 ms",
                       "fine": "fine: 25 rpm, tap every 300 ms",
                       "tap": "tap stage: 1 tap + 45° turn per cycle",
                       "other": "auger stopped (before / after a dose)"}[st]
                seen.add(st)
            ax_a.plot([dt(r["epoch"]) for r in seg], [r["cup_g"] for r in seg],
                      color=col, lw=2, label=lab, solid_capstyle="round")
    ax_a.axhline(TARGET_G, color=INK2, lw=1, ls=(0, (4, 3)))
    ax_a.text(dt(doses[0][1][0]["epoch"]), TARGET_G + 0.05, "3 g target",
              color=INK2, fontsize=8, va="bottom")
    d1_end = [r for r in doses[0][1] if r["stage"] == "post"]
    d2_end = [r for r in doses[1][1] if r["stage"] == "post"]
    e1, e2 = d1_end[-1], d2_end[-1]
    ax_a.annotate("dose 1 stops on its 15 min timeout:\n{:.4f} g at 0°"
                  .format(e1["cup_g"]), xy=(dt(e1["epoch"]), e1["cup_g"]),
                  xytext=(-210, -48), textcoords="offset points", fontsize=8,
                  color=INK, arrowprops=dict(arrowstyle="-", color=INK2,
                                             lw=0.8))
    ax_a.annotate("top-up ends:\n{:.4f} g at 0°".format(e2["cup_g"]),
                  xy=(dt(e2["epoch"]), e2["cup_g"]), xytext=(-20, -78),
                  textcoords="offset points", fontsize=8, color=INK,
                  ha="right", arrowprops=dict(arrowstyle="-", color=INK2,
                                              lw=0.8))
    ax_a.set_ylabel("cup since dose 1's baseline (g)")
    ax_a.set_ylim(-0.1, 3.35)
    ax_a.grid(axis="y", color="#e6e5e0", lw=0.6)
    ax_a.legend(loc="lower right", frameon=False, fontsize=8)
    ax_a.set_title("A  Carboxymethyl cellulose, plate held at 60°, taps "
                   "while the auger turns (2026-11-24, UTC)", loc="left",
                   fontsize=10, color=INK)

    for name, rows in doses:
        for st in ("bulk", "fine"):
            w = [x for x in rate_windows(rows) if x[2] == st]
            if w:
                ax_b.plot([dt(x[0]) for x in w], [x[1] for x in w], "o-",
                          color=STAGE_COLORS[st], ms=4, lw=1.2,
                          markeredgecolor=SURFACE, markeredgewidth=0.8)
    ax_b.set_ylabel("feed rate, 10 s windows (mg/s)")
    ax_b.set_ylim(bottom=0)
    ax_b.grid(axis="y", color="#e6e5e0", lw=0.6)
    ax_b.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M",
                                                        tz=timezone.utc))
    ax_b.set_xlabel("time (UTC)")
    ax_b.set_title("B  Feed rate while the auger turned", loc="left",
                   fontsize=10, color=INK)
    plt.setp(ax_a.get_xticklabels(), visible=True)
    ax_a.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M",
                                                        tz=timezone.utc))

    rows2 = doses[1][1]
    t_end = [r for r in rows2 if r["stage"] in STAGE_COLORS][-1]["epoch"]
    win = [r for r in rows2 if t_end - 25.0 <= r["epoch"] <= t_end + 14.0]
    ax_c.axhspan(-1, 1, color="#e6e5e0", lw=0)
    ax_c.axhline(0, color=INK2, lw=0.8)
    for st, seg in segments(win):
        ax_c.plot([r["epoch"] - t_end for r in seg],
                  [1000.0 * (r["cup_g"] - TARGET_G) for r in seg],
                  color=STAGE_COLORS.get(st, NEUTRAL), lw=2)
    ax_c.set_ylim(-12, 4)
    ax_c.set_xlabel("s from the end of the top-up")
    ax_c.set_ylabel("cup − 3 g (mg)")
    ax_c.text(0.02, 0.97, "±1 mg band", transform=ax_c.transAxes,
              color=INK2, fontsize=8, va="top")
    ax_c.set_title("C  Top-up, last 25 s", loc="left", fontsize=10,
                   color=INK)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print("wrote", out_png)


def upload(data_dir, doses, extra):
    from pymongo import MongoClient
    uri = os.environ.get("PI_MONGODB_URI") or os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("set PI_MONGODB_URI or MONGODB_URI")
    coll = MongoClient(uri, serverSelectionTimeoutMS=20000)[
        "powder_doser"]["dose_runs"]
    key = {"doc_type": "fixed_tilt_dose", "session_id": SESSION_ID}
    if coll.count_documents(key, limit=1):
        print("already uploaded")
        return None
    doc = dict(key)
    doc.update({"powder_id": "carboxymethyl-cellulose", "pr": 131,
                "started_utc": "2026-11-24T19:52:41Z",
                "target_g": TARGET_G, "fixed_tilt_deg": 60.0,
                "requested_by": "XZaitzeff",
                "request": "carboxymethyl cellulose is in the auger. Dose 3 g "
                           "at 60 degrees with tapping",
                "session_base_abs_g": SESSION_BASE_G, "doses": []})
    for name, rows, summ_path, log_path in doses:
        recs = [json.loads(l.split("\t", 1)[1][2:]) for l in
                open(log_path, encoding="utf-8", errors="replace")
                if "\tT," in l]
        meta = {}
        for l in open(log_path, encoding="utf-8", errors="replace"):
            if "\tM," in l:
                _, k, v = l.split("\t", 1)[1].rstrip("\n").split(",", 2)
                meta[k] = v
        with open(summ_path) as fh:
            summ = list(csv.DictReader(fh))
        doc["doses"].append({
            "name": name, "params": meta, "trial_record": recs[0] if recs
            else None, "summary": summ[0] if summ else None,
            "series": {k: [r[k] for r in rows] for k in
                       ("time_utc", "t_s", "mass_abs_g", "mass_g",
                        "balance_status", "source", "stage", "tilt_deg",
                        "auger_rpm", "taps_cum")}})
    doc.update(extra)
    return str(coll.insert_one(doc).inserted_id)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("data_dir")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--extra-json", default=None)
    a = ap.parse_args()
    d1 = glob.glob(os.path.join(a.data_dir, "dose1_*", "trial_01_*.csv"))[0]
    d2 = glob.glob(os.path.join(a.data_dir, "dose2_*", "trial_02_*.csv"))[0]
    doses = [("dose 1", load(d1)), ("top-up", load(d2))]
    figure(doses, os.path.join(a.data_dir, "cmc_3g_60deg.png"))
    for name, rows in doses:
        w = rate_windows(rows)
        for st in ("bulk", "fine"):
            v = sorted(x[1] for x in w if x[2] == st)
            if v:
                print("{} {}: {} windows, median {:.2f} mg/s, range "
                      "{:.2f}-{:.2f}".format(name, st, len(v),
                                              v[len(v) // 2], v[0], v[-1]))
    if a.upload:
        logs = [glob.glob(os.path.join(a.data_dir, "dose1_*", "*.log"))[0],
                glob.glob(os.path.join(a.data_dir, "dose2_*", "*.log"))[0]]
        summs = [glob.glob(os.path.join(a.data_dir, "dose1_*",
                                        "trials_summary.csv"))[0],
                 glob.glob(os.path.join(a.data_dir, "dose2_*",
                                        "trials_summary.csv"))[0]]
        extra = json.loads(a.extra_json) if a.extra_json else {}
        _id = upload(a.data_dir, [(n, r, s, l) for (n, r), s, l in
                                  zip(doses, summs, logs)], extra)
        print("uploaded", _id)


if __name__ == "__main__":
    main()

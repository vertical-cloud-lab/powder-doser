#!/usr/bin/env python3
"""Set C (issue #210): every non-salt dose made with the new trickle_tap controller.

The "new controller" is the trickle_tap firmware (PR #154, then PR #166): a
bulk stage at a fixed tilt and rpm, a trickle stage run by a 3-state Kalman
filter (cup mass, delivery rate, lagged balance reading) with PI rate control
and a predictive cutoff, then single taps. Its ``bulk_only`` mode (added
2026-09-30 and used for every Al 4047 dose since) runs the whole dose in the
bulk stage with an rpm taper and a slope-based halt, so the filter never runs.

Apart from salt, that firmware has dosed only AlSi10Mg (one dose) and Al 4047
(two batches, ten doses). An earlier port of the same filter
and PI law (``pi_trickle_trim.py``, PR #131, trickle and taps only) ran six
trials on carboxymethyl cellulose. This script copies those sources from
pinned commits into ``new-controller-powders/source/`` and writes one tidy CSV
per dose in the columns of set A, a summary table, and a figure.

Usage (from the repository root):

    git fetch origin   # the source commits below must be present
    python3 data/assimilation/extract_new_controller.py --fetch   # copy sources
    python3 data/assimilation/extract_new_controller.py           # rebuild outputs

Only the standard library is needed for the CSVs; the figure needs matplotlib.
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extract as base  # noqa: E402  (style helpers, git_show, set A paths)

OUT = os.path.join(HERE, "new-controller-powders")
SRC = os.path.join(OUT, "source")

C164 = "d14a50dd4eb4dd0e8530a79598e42a54a78fc2c9"  # claude/issue-164-20260922-1928
C186 = "5252021a723e539b686208705d8c8d733182d960"  # claude/issue-186-20261021-0136
C130 = "5bc4cc9682ddad31b28d8ce87e7c73bbc5f43f28"  # claude/issue-130-20260721-1807

ALSI = (C164, "data/opt/production-alsi10mg/zero")
AL_9F = (C164, "data/opt/production-al4047-9fxeqt/zero")
AL_CUP = (C186, "data/opt/production-al4047-atomizer-cups/zero")
DOSES = [  # (source, trial_uuid), in time order
    (ALSI, "64714f7c-c9ed-4ebe-887f-87a7e9bc16b0"),
    (AL_9F, "3e7490c2-60f6-40d1-ad53-b4bede3de8be"),
    (AL_9F, "de4dd913-beca-41af-b61c-574960aacda6"),
    (AL_9F, "56a01060-e9d2-493a-9ea5-79ef3300605e"),
    (AL_CUP, "a5fdadaa-d609-40bf-9316-af67b75a9b1f"),
    (AL_CUP, "b13e5997-8beb-4658-a0cc-859a1eea635b"),
    (AL_CUP, "f6a3403f-d381-4824-869e-82675832a916"),
    (AL_CUP, "cb3096e9-a8d3-402c-a0ba-e034f0d8c2af"),
    (AL_CUP, "d737cec5-448b-4ffe-aa61-eb84d6eb8d9d"),
    (AL_CUP, "9480b818-2e94-4356-a7d7-bbf36dec28b3"),
    (AL_CUP, "5851b6d6-805c-49cd-919a-e28add9b6d19"),
]
# These two doses have no usable telemetry, so their series is parsed from the
# console lines of the serial log. 3e7490c2 hit a MemoryError 100 s into the
# bulk stage and has no telemetry or RESULT. de4dd913's telemetry buffer stopped
# at row 80 ("heap low"); console times are whole seconds in the bulk and tap
# rows, so splicing them onto those 80 rows (0.01 s times) would run time
# backwards at the join.
CONSOLE = {"3e7490c2-60f6-40d1-ad53-b4bede3de8be", "de4dd913-beca-41af-b61c-574960aacda6"}
# 3e7490c2's document has no parameters_executed. Its bulk settings are the
# searched ones plus the cadence its serial log echoes (`set bulk_tap 1`,
# `tap_cadence_on_ms 60`, `tap_cadence_off_ms 440`).
CADENCE_FROM_LOG = {"bulk_tap": True, "tap_cadence_on_ms": 60, "tap_cadence_off_ms": 440}

CMC_DIR = "data/pi-trim/2026-09-08_carboxymethyl-cellulose"
CMC_LOG = "pi_trim_cmc_0908.log"
CMC_TRIALS = "trials_carboxymethyl-cellulose.csv"

POWDER = {"salt": "salt (NaCl)", "alsi10mg": "AlSi10Mg",
          "al4047-9fxeqt": "Al 4047", "al4047": "Al 4047",
          "carboxymethyl-cellulose": "carboxymethyl cellulose (CMC)"}

COLS = ["powder_id", "trial", "target_g", "t_s", "phase", "mass_g", "stable",
        "fresh", "kf_mass_g", "kf_rate_gps", "kf_sigma_g", "kf_balance_g",
        "ff_gpr", "rate_setpoint_gps", "rate_err_gps", "pi_integ",
        "bulk_slope_gps", "pred_g", "cutoff_g", "tilt_deg_cmd",
        "auger_rpm_cmd", "tap_mode", "source"]

RX_POLL = re.compile(r"^\[phase 1 bulk\] poll (?P<n>\d+)(?: \(unstable\))?: "
                     r"mass (?P<m>-?[\d.]+) / .*elapsed (?P<t>[\d.]+) s")
RX_SETTLED = re.compile(r"^\[phase 1 bulk\] settled: mass (?P<m>-?[\d.]+) / "
                        r".*elapsed (?P<t>[\d.]+) s")
RX_TRICKLE = re.compile(r"^\[trickle\]\s+(?P<t>[\d.]+)s m (?P<m>-?[\d.]+) r\s+"
                        r"(?P<r>-?[\d.]+) mg/s \(sp\s+(?P<sp>-?[\d.]+)\) rpm\s+"
                        r"(?P<rpm>-?[\d.]+) pred (?P<pred>-?[\d.]+)/"
                        r"(?P<cut>-?[\d.]+) sigma\s+(?P<sig>-?[\d.]+) mg")
RX_TAP = re.compile(r"^\[phase 3 (?P<ph>tap|tap-burst)\] cycle (?P<n>\d+): "
                    r"mass (?P<m>-?[\d.]+) / .*elapsed (?P<t>[\d.]+) s")
RX_CMC_TRIAL = re.compile(r"^=== trial (?P<n>\d+) : target (?P<target>[\d.]+) g")


def fetch():
    os.makedirs(SRC, exist_ok=True)
    for (commit, folder), uuid in DOSES:
        for name in ("trial_{}.json".format(uuid), "serial_{}.log".format(uuid)):
            with open(os.path.join(SRC, name), "wb") as f:
                f.write(base.git_show(commit, "{}/{}".format(folder, name)))
    for name in (CMC_LOG, CMC_TRIALS):
        with open(os.path.join(SRC, "cmc_" + name), "wb") as f:
            f.write(base.git_show(C130, "{}/{}".format(CMC_DIR, name)))


# --------------------------------------------------------------------------
# trickle_tap firmware doses (opt_trials documents)
# --------------------------------------------------------------------------
def actuators(phase, p, rpm=""):
    """Commanded (tilt, auger rpm, tap mode) for one row."""
    cadence = ("cadence {}/{} ms".format(p["tap_cadence_on_ms"], p["tap_cadence_off_ms"])
               if p.get("bulk_tap") else "none")
    if phase == "bulk":
        return p["bulk_tilt_deg"], (rpm if rpm not in ("", None) else p["bulk_rpm"]), cadence
    if phase in ("bulk_settled", "bulk_end"):
        return p["bulk_tilt_deg"], 0.0, "none"
    if phase == "trickle":
        return p["trickle_tilt_deg"], rpm, "none"
    if phase == "trickle_end":
        return p["trickle_tilt_deg"], 0.0, "none"
    if phase == "tap_burst":
        return p["tap_tilt_deg"], 0.0, "burst x{}".format(p.get("tap_burst_taps", 2))
    if phase == "tap":
        return p["tap_tilt_deg"], 0.0, "single x{}".format(p.get("taps_per_cycle", 1))
    if phase == "final_scored":
        return (p["bulk_tilt_deg"] if p.get("bulk_only") else p["tap_tilt_deg"]), 0.0, "none"
    return "", "", ""


def from_telemetry(doc):
    p = doc["parameters_executed"]
    bulk_only = bool(p.get("bulk_only"))
    tel = doc["telemetry"]
    cols = tel["header"].split(",")
    raw = [dict(zip(cols, line.split(","))) for line in tel["rows"]]
    out = []
    for i, r in enumerate(raw):
        phase = r["phase"]
        nxt = raw[i + 1]["phase"] if i + 1 < len(raw) else ""
        if not bulk_only and phase == "bulk" and nxt not in ("bulk", ""):
            phase = "bulk_settled"  # the settled read after the auger halts
        row = {"t_s": r["t_s"], "phase": phase, "mass_g": r["z_g"],
               "fresh": r["fresh"], "source": "telemetry"}
        rpm = ""
        if phase == "trickle":
            rpm = r["rpm_cmd"]
            row.update(kf_mass_g=r["m_g"], kf_rate_gps=r["r_gps"],
                       kf_sigma_g=r["sigma_g"], ff_gpr=r["ff_gpr"],
                       rate_setpoint_gps=r["r_sp_gps"], rate_err_gps=r["err_gps"],
                       pi_integ=r["integ"], pred_g=r["pred_g"], cutoff_g=r["cutoff_g"])
        elif bulk_only and phase == "bulk":
            rpm = r["rpm_cmd"]
            row.update(bulk_slope_gps=r["r_gps"], pred_g=r["pred_g"],
                       cutoff_g=r["cutoff_g"])
        tilt, rpm, taps = actuators(phase, p, rpm)
        row.update(tilt_deg_cmd=tilt, auger_rpm_cmd=rpm, tap_mode=taps)
        out.append(row)
    return out


def blank(v):
    return "" if v is None else v


def executed(doc):
    p = doc["parameters_executed"]
    return p if p else dict(doc["parameters"], **CADENCE_FROM_LOG)


def from_console(doc, log_path):
    """Rows parsed from the console lines of a dose's serial log."""
    p = executed(doc)
    with open(log_path, errors="replace") as f:
        lines = f.read().splitlines()
    start = max(i for i, s in enumerate(lines) if s.startswith(">> g "))
    out = []
    for s in lines[start:]:
        m = RX_POLL.match(s)
        if m:
            tilt, rpm, taps = actuators("bulk", p)
            out.append({"t_s": m["t"], "phase": "bulk", "mass_g": m["m"],
                        "tilt_deg_cmd": tilt, "auger_rpm_cmd": rpm,
                        "tap_mode": taps, "source": "console"})
            continue
        m = RX_SETTLED.match(s)
        if m:
            tilt, rpm, taps = actuators("bulk_settled", p)
            out.append({"t_s": m["t"], "phase": "bulk_settled", "mass_g": m["m"],
                        "tilt_deg_cmd": tilt, "auger_rpm_cmd": rpm,
                        "tap_mode": taps, "source": "console"})
            continue
        m = RX_TRICKLE.match(s)
        if m:
            tilt, rpm, taps = actuators("trickle", p, m["rpm"])
            pred, sig = float(m["pred"]), float(m["sig"]) / 1000
            out.append({"t_s": m["t"], "phase": "trickle", "mass_g": "",
                        "kf_mass_g": m["m"],
                        "kf_rate_gps": "{:.5f}".format(float(m["r"]) / 1000),
                        "kf_sigma_g": "{:.5f}".format(sig),
                        "rate_setpoint_gps": "{:.5f}".format(float(m["sp"]) / 1000),
                        "pred_g": "{:.4f}".format(pred), "cutoff_g": m["cut"],
                        "tilt_deg_cmd": tilt, "auger_rpm_cmd": rpm,
                        "tap_mode": taps, "source": "console"})
            continue
        m = RX_TAP.match(s)
        if m:
            phase = "tap_burst" if m["ph"] == "tap-burst" else "tap"
            tilt, rpm, taps = actuators(phase, p)
            out.append({"t_s": m["t"], "phase": phase, "mass_g": m["m"],
                        "tilt_deg_cmd": tilt, "auger_rpm_cmd": rpm,
                        "tap_mode": taps, "source": "console"})
    return out


def label(target_g):
    return ("{:g}".format(target_g)).replace(".", "p")


def build_executor():
    summary, series = [], {}
    for (commit, folder), uuid in DOSES:
        with open(os.path.join(SRC, "trial_{}.json".format(uuid))) as f:
            doc = json.load(f)
        assert doc["trial_uuid"] == uuid
        p = executed(doc)
        out = doc["outcomes"]
        if uuid in CONSOLE:
            rows = from_console(doc, os.path.join(SRC, "serial_{}.log".format(uuid)))
        else:
            rows = from_telemetry(doc)
        if out.get("settled_final"):
            tilt, rpm, taps = actuators("final_scored", p)
            rows.append({"t_s": "{:.2f}".format(out["t_total_s"]), "phase": "final_scored",
                         "mass_g": "{:.5f}".format(out["settled_final_g"]), "fresh": 1,
                         "tilt_deg_cmd": tilt, "auger_rpm_cmd": rpm, "tap_mode": taps,
                         "source": "outcome"})
        powder_id = doc["powder_id"]
        short = "al4047" if powder_id.startswith("al4047") else powder_id
        name = "{}_{}g_{}.csv".format(short, label(doc["target_g"]), uuid[:8])
        for r in rows:
            r.update(powder_id=powder_id, trial=uuid[:8], target_g=doc["target_g"])
        write_rows(os.path.join(OUT, name), rows)
        series[uuid[:8]] = rows
        kf_ran = any(r["phase"] == "trickle" for r in rows)
        sources = sorted({r["source"] for r in rows} - {"outcome"})
        summary.append({
            "powder": POWDER[powder_id], "powder_id": powder_id,
            "campaign_id": doc["campaign_id"], "trial": uuid[:8], "trial_uuid": uuid,
            "started_utc": doc["started_utc"][:19] + "Z", "controller": "trickle_tap",
            "mode": "bulk_only" if p.get("bulk_only") else "bulk + KF trickle + taps",
            "kf_ran": "yes" if kf_ran else "no",
            "target_g": doc["target_g"], "final_g": blank(out["settled_final_g"]),
            "error_mg": blank(out["error_mg"]), "status": doc["flags"]["status"],
            "t_total_s": blank(out["t_total_s"]), "t_bulk_s": blank(out["t_bulk_s"]),
            "t_trickle_s": blank(out["t_trickle_s"]), "t_tap_s": blank(out["t_tap_s"]),
            "taps": blank(out["taps"]), "auger_rev": blank(out["auger_rev"]),
            "bulk_tilt_deg": p["bulk_tilt_deg"], "bulk_rpm": p["bulk_rpm"],
            "firmware": blank((doc.get("device") or {}).get("firmware")) or
            "trickle_tap @ " + doc["git_commit"][:7], "rows": len(rows),
            "rows_source": "+".join(sources), "csv": name})
    return summary, series


# --------------------------------------------------------------------------
# CMC: pi_trickle_trim.py (prototype), 2026-09-08
# --------------------------------------------------------------------------
CMC_PHASE_D = {"drift": "pre_drift", "preroll": "preroll", "trickle": "trickle",
               "settle": "final_settle"}
CMC_PHASE_P = {"base": "baseline", "posttrickle": "trickle_end", "tapread": "tap",
               "settled": "final_settled", "settled2": "final_scored"}


def parse_cmc(path):
    meta, trials, cur = {}, [], None
    with open(path, errors="replace") as f:
        for line in f:
            fl = line.rstrip("\r\n").split(",")
            kind = fl[0]
            if kind == "M":
                meta[fl[1]] = ",".join(fl[2:])
            elif kind == "E":
                m = RX_CMC_TRIAL.match(fl[2])
                if m:
                    cur = {"trial": int(m["n"]), "target_g": float(m["target"]),
                           "t0_ms": int(fl[1]), "items": [], "base": None}
                    trials.append(cur)
            elif cur is None:
                continue
            elif kind in ("D", "P") and int(fl[2]) == cur["trial"]:
                if kind == "P" and fl[3] == "base":
                    cur["base"] = float(fl[4])
                cur["items"].append(fl)
            elif kind == "T":
                cur["result"] = fl
                cur = None
    return meta, trials


def build_cmc():
    meta, trials = parse_cmc(os.path.join(SRC, "cmc_" + CMC_LOG))
    k_sigma = float(meta["k_sigma"])
    with open(os.path.join(SRC, "cmc_" + CMC_TRIALS)) as f:
        ref = {int(r["trial"]): r for r in csv.DictReader(f)}
    summary, series = [], {}
    for tr in trials:
        res = tr["result"]
        # T,trial,target,tilt,tap_tilt,rep,m_base,t_trickle,revs,ff_end,m_post,
        #   taps,nudges,cycles,t_total,m_settled,m_settled2,dispensed,error_mg,
        #   trickle_short_mg,verdict
        n, target = tr["trial"], tr["target_g"]
        tilt, tap_tilt, rep = float(res[3]), float(res[4]), int(res[5])
        assert abs(float(res[6]) - tr["base"]) < 1e-9
        r_ref = ref[n]
        assert abs(float(r_ref["dispensed_g"]) - float(res[17])) < 1e-9
        rows = []
        for fl in tr["items"]:
            t = (int(fl[1]) - tr["t0_ms"]) / 1000.0
            z = fl[4]
            mass = "" if z == "nan" else "{:.4f}".format(float(z) - tr["base"])
            if fl[0] == "D":
                phase = CMC_PHASE_D[fl[3]]
                row = {"t_s": "{:.3f}".format(t), "phase": phase, "mass_g": mass,
                       "stable": fl[5], "auger_rpm_cmd": fl[7], "source": "log_D"}
                if fl[3] in ("preroll", "trickle") and fl[8] != "":
                    m, r, b, sig, mrt, rsp, integ, ff, margin = (float(x) for x in fl[8:17])
                    row.update(fresh=fl[6], kf_mass_g="{:.4f}".format(m),
                               kf_rate_gps="{:.4f}".format(r), kf_balance_g="{:.4f}".format(b),
                               kf_sigma_g="{:.5f}".format(sig),
                               rate_setpoint_gps="{:.4f}".format(rsp),
                               pi_integ="{:.3f}".format(integ), ff_gpr="{:.4f}".format(ff),
                               pred_g="{:.4f}".format(mrt + k_sigma * sig),
                               cutoff_g="{:.4f}".format(target - margin),
                               tilt_deg_cmd=tilt, tap_mode="none")
                elif fl[3] == "settle":
                    row.update(tilt_deg_cmd=tap_tilt, tap_mode="none")
            else:
                phase = CMC_PHASE_P[fl[3]]
                row = {"t_s": "{:.3f}".format(t), "phase": phase, "mass_g": mass,
                       "stable": fl[5], "auger_rpm_cmd": 0.0, "source": "log_P"}
                if phase != "baseline":
                    row.update(tilt_deg_cmd=tap_tilt,
                               tap_mode="single x1" if phase == "tap" else "none")
            row.update(powder_id="carboxymethyl-cellulose", trial="cmc-t{}".format(n),
                       target_g=target)
            rows.append(row)
        name = "cmc_{}g_trial{}.csv".format(label(target), n)
        write_rows(os.path.join(OUT, name), rows)
        series["cmc-t{}".format(n)] = rows
        summary.append({
            "powder": POWDER["carboxymethyl-cellulose"],
            "powder_id": "carboxymethyl-cellulose", "campaign_id": "pi-trim-2026-09-08",
            "trial": "cmc-t{}".format(n), "trial_uuid": "",
            "started_utc": "2026-09-08", "controller": "pi_trickle_trim.py (prototype)",
            "mode": "KF trickle + taps (no bulk)", "kf_ran": "yes",
            "target_g": target, "final_g": float(res[17]), "error_mg": float(res[18]),
            "status": res[20], "t_total_s": float(res[14]), "t_bulk_s": 0.0,
            "t_trickle_s": float(res[7]), "t_tap_s": "", "taps": int(res[11]),
            "auger_rev": float(res[8]), "bulk_tilt_deg": "", "bulk_rpm": "",
            "firmware": "pi_trickle_trim.py (PR #131)", "rows": len(rows),
            "rows_source": "log_D+log_P", "csv": name, "rep": rep})
    return summary, series


def write_rows(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLS})


def salt_reference():
    """Set A run 1, for the summary table and the figure."""
    uuid = base.SALT_TRIALS[0][1]
    with open(os.path.join(base.SALT_DIR, "source", "trial_{}.json".format(uuid))) as f:
        doc = json.load(f)
    out, p = doc["outcomes"], doc["parameters_executed"]
    with open(os.path.join(base.SALT_DIR, "run1_{}.csv".format(uuid[:8]))) as f:
        rows = list(csv.DictReader(f))
    s = {"powder": POWDER["salt"], "powder_id": "salt", "campaign_id": doc["campaign_id"],
         "trial": uuid[:8], "trial_uuid": uuid, "started_utc": doc["started_utc"][:19] + "Z",
         "controller": "trickle_tap", "mode": "bulk + KF trickle + taps", "kf_ran": "yes",
         "target_g": doc["target_g"], "final_g": out["settled_final_g"],
         "error_mg": out["error_mg"], "status": doc["flags"]["status"],
         "t_total_s": out["t_total_s"], "t_bulk_s": out["t_bulk_s"],
         "t_trickle_s": out["t_trickle_s"], "t_tap_s": out["t_tap_s"], "taps": out["taps"],
         "auger_rev": out["auger_rev"], "bulk_tilt_deg": p["bulk_tilt_deg"],
         "bulk_rpm": p["bulk_rpm"], "firmware": doc["device"]["firmware"],
         "rows": len(rows), "rows_source": "telemetry",
         "csv": "../salt-0p5g/run1_{}.csv".format(uuid[:8])}
    return s, rows


# --------------------------------------------------------------------------
# Figure
# --------------------------------------------------------------------------
def plot(summary, series, salt_rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    f = base.fnum
    by = {s["trial"]: s for s in summary}
    C1, C2, C3 = base.SERIES[:3]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.6), dpi=150)
    fig.patch.set_facecolor(base.SURFACE)
    ax_salt, ax_alsi, ax_alok, ax_alst, ax_cmc, ax_leg = axes.ravel()
    for ax in axes.ravel()[:5]:
        base.style(ax)

    def target_line(ax, y, text, x=None, va="bottom"):
        ax.axhline(y, color=base.INK2, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
        if text:
            ax.text(x if x is not None else ax.get_xlim()[0], y, " " + text,
                    ha="left", va=va, fontsize=8, color=base.INK2)

    def trace(ax, rows, color, kf=True, lw=1.5):
        pts = [(f(r["t_s"]), f(r["mass_g"])) for r in rows if r["mass_g"] not in ("", None)]
        ax.plot([t for t, _ in pts], [m for _, m in pts], color=color, linewidth=lw,
                solid_joinstyle="round", solid_capstyle="round", zorder=3)
        ax.plot([pts[-1][0]], [pts[-1][1]], "o", color=color, markersize=5,
                markeredgecolor=base.SURFACE, markeredgewidth=1.2, zorder=4)
        if kf:
            k = [r for r in rows if r["phase"] == "trickle" and r["kf_mass_g"] not in ("", None)]
            ax.plot([f(r["t_s"]) for r in k], [f(r["kf_mass_g"]) for r in k], color=color,
                    linewidth=1.3, linestyle=(0, (2, 1.6)), zorder=3)

    def title(ax, text):
        ax.set_title(text, fontsize=9.5, color=base.INK, loc="left")

    def xy_labels(ax):
        ax.set_xlabel("time since the dose command (s)", fontsize=8.5)
        ax.set_ylabel("mass on the balance (g)", fontsize=8.5)

    # salt: set A run 1
    s = by[salt_rows[0]["trial_uuid8"]]
    trace(ax_salt, salt_rows, C1)
    ax_salt.set_xlim(0, 75)
    target_line(ax_salt, 0.5, "target 0.5 g", x=1)
    title(ax_salt, "salt (NaCl), 0.5 g, set A run 1\n{} g ({:+.1f} mg, {}) in {:.0f} s".format(
        s["final_g"], s["error_mg"], s["status"], s["t_total_s"]))
    xy_labels(ax_salt)

    # AlSi10Mg, with an inset on the trickle
    s = by["64714f7c"]
    rows = series["64714f7c"]
    trace(ax_alsi, rows, C1)
    ax_alsi.set_xlim(0, 330)
    target_line(ax_alsi, 8.0, "target 8 g", x=3, va="top")
    title(ax_alsi, "AlSi10Mg, 8 g, 2026-09-29 (only dose)\n{} g ({:+.1f} mg, {}) in {:.0f} s".format(
        s["final_g"], s["error_mg"], s["status"], s["t_total_s"]))
    xy_labels(ax_alsi)
    ins = ax_alsi.inset_axes([0.45, 0.12, 0.5, 0.48])
    base.style(ins)
    tr = [r for r in rows if r["phase"] in ("bulk_settled", "trickle", "trickle_end")]
    ins.plot([f(r["t_s"]) for r in tr], [f(r["mass_g"]) for r in tr], color=C1,
             linewidth=1.4, marker="o", markersize=2.8, markeredgewidth=0)
    k = [r for r in tr if r["phase"] == "trickle"]
    ins.plot([f(r["t_s"]) for r in k], [f(r["kf_mass_g"]) for r in k], color=C1,
             linewidth=1.2, linestyle=(0, (2, 1.6)))
    ins.tick_params(labelsize=7)
    ins.set_title("trickle stage (KF ran 16 steps)", fontsize=7.5, color=base.INK2, loc="left")

    # Al 4047: the two doses that finished ok (bulk_only)
    for uuid8, color in (("56a01060", C1), ("5851b6d6", C2)):
        s = by[uuid8]
        trace(ax_alok, series[uuid8], color, kf=False)
        target_line(ax_alok, s["target_g"], "")
    ax_alok.set_xlim(0, 70)
    ax_alok.legend(handles=[
        Line2D([], [], color=c, linewidth=1.5,
               label="{} g, {}: {:+.1f} mg in {:.0f} s".format(
                   by[u]["target_g"], by[u]["started_utc"][:10], by[u]["error_mg"],
                   by[u]["t_total_s"]))
        for u, c in (("56a01060", C1), ("5851b6d6", C2))] +
        [Line2D([], [], color=base.INK2, linewidth=1.0, linestyle=(0, (4, 3)), label="targets")],
        loc="center right", fontsize=7.5, frameon=False, labelcolor=base.INK)
    title(ax_alok, "Al 4047, the two doses that finished ok\nbulk_only mode: no trickle, no KF")
    xy_labels(ax_alok)

    # Al 4047: the doses that stalled, timed out, ran out of cycles or crashed
    named = {"de4dd913": (C3, "de4dd913, 4.5095 g: the only Al 4047\ndose whose KF trickle ran"),
             "3e7490c2": (C2, "3e7490c2, 8 g: firmware\nMemoryError at 100 s")}
    stalled = [s for s in summary if s["powder_id"].startswith("al4047") and s["status"] != "ok"]
    for s in stalled:
        rows = series[s["trial"]]
        color, text = named.get(s["trial"], (base.INK2, ""))
        pts = [(f(r["t_s"]), f(r["mass_g"])) for r in rows if r["mass_g"] not in ("", None)]
        ax_alst.plot([t for t, _ in pts], [m for _, m in pts], color=color,
                     linewidth=1.5 if text else 1.0, zorder=3 if text else 2,
                     solid_joinstyle="round", solid_capstyle="round")
        ax_alst.plot([pts[-1][0]], [pts[-1][1]], "o", color=color, markersize=5 if text else 3.5,
                     markeredgecolor=base.SURFACE, markeredgewidth=1.0, zorder=4)
        if s["trial"] == "de4dd913":
            ax_alst.text(pts[-1][0], pts[-1][1] - 0.18, text, fontsize=7.5,
                         color=base.INK, ha="right", va="top")
        elif text:
            ax_alst.text(pts[-1][0] + 12, pts[-1][1], text, fontsize=7.5,
                         color=base.INK, ha="left", va="center")
    ax_alst.set_xlim(0, 830)
    ax_alst.set_ylim(-0.15, 4.6)
    ax_alst.text(330, 1.25, "gray: six bulk_only doses into the\natomizer cups that stalled or timed\n"
                 "out as the tube clogged (2026-10-19/20)", fontsize=7.5, color=base.INK2)
    title(ax_alst, "Al 4047, the eight doses that did not finish\n"
          "(clogged tube, cycle budget, firmware crash)")
    xy_labels(ax_alst)

    # CMC: three 0.2 g trials, prototype controller
    for uuid8, color in (("cmc-t1", C1), ("cmc-t4", C2), ("cmc-t6", C3)):
        trace(ax_cmc, [r for r in series[uuid8] if r["phase"] != "pre_drift"], color)
    ax_cmc.set_ylim(-0.05, 0.23)
    target_line(ax_cmc, 0.2, "target 0.2 g", x=2, va="top")
    title(ax_cmc, "CMC, 0.2 g x3, 2026-09-08, prototype controller\n"
          "all three stalled 157-174 mg short")
    ax_cmc.set_xlabel("time since the trial started (s)", fontsize=8.5)
    ax_cmc.set_ylabel("mass over the trial's baseline (g)", fontsize=8.5)
    ax_cmc.legend(handles=[
        Line2D([], [], color=c, linewidth=1.5, label="trial {}: {:+.1f} mg".format(
            by[u]["trial"][-1], by[u]["error_mg"]))
        for u, c in (("cmc-t1", C1), ("cmc-t4", C2), ("cmc-t6", C3))],
        loc="center right", fontsize=7.5, frameon=False, labelcolor=base.INK)

    ax_leg.axis("off")
    ax_leg.legend(handles=[
        Line2D([], [], color=base.INK2, linewidth=1.5, label="balance reading (observation)"),
        Line2D([], [], color=base.INK2, linewidth=1.3, linestyle=(0, (2, 1.6)),
               label="Kalman-filter mass estimate"),
        Line2D([], [], color=base.INK2, linewidth=1.0, linestyle=(0, (4, 3)), label="target"),
        Line2D([], [], color=base.INK2, marker="o", linestyle="none", markersize=5,
               label="last reading")],
        loc="upper left", fontsize=8.5, frameon=False, labelcolor=base.INK,
        title="Every powder the new (trickle_tap)\ncontroller has dosed. Only 0.5 g\n"
              "(salt, Al 4047) and 8 g (AlSi10Mg,\nAl 4047) were asked of two powders,\n"
              "and those Al 4047 doses failed.\nThe time axes differ.",
        title_fontsize=9, alignment="left")
    fig.tight_layout()
    out = os.path.join(HERE, "new_controller_powders.png")
    fig.savefig(out, facecolor=base.SURFACE)
    plt.close(fig)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fetch", action="store_true",
                    help="copy the sources from the pinned commits first")
    ap.add_argument("--no-plots", action="store_true")
    args = ap.parse_args()
    if args.fetch:
        fetch()
    os.makedirs(OUT, exist_ok=True)
    salt, salt_rows = salt_reference()
    ex_sum, ex_series = build_executor()
    cmc_sum, cmc_series = build_cmc()
    summary = [salt] + ex_sum + cmc_sum
    fields = list(salt) + ["rep"]
    with open(os.path.join(OUT, "doses_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for s in summary:
            w.writerow({k: s.get(k, "") for k in fields})
    for s in summary:
        print("{powder_id:24s} {trial:9s} {target_g:>7} g -> {final_g} g ({error_mg} mg, "
              "{status}), {mode}, {rows} rows [{rows_source}]".format(**s))
    if not args.no_plots:
        series = dict(ex_series, **cmc_series)
        print(plot(summary, series, salt_rows))


if __name__ == "__main__":
    main()

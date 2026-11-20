#!/usr/bin/env python3
"""Tidy the salt production doses spooled on the Zero by scripts/dose.py.

Reads every ``zero/trial_<uuid>.json`` (the full ``opt_trials`` document, also
in MongoDB) and writes, next to this script:

- ``doses_summary.csv``: one row per dose (target, settled result, phase times).
- ``doses/dose_<target>g_<uuid8>.csv``: one tidy time series per dose.
- ``production_salt_doses.png``: the 2026-10-06 five-target session.

The time series comes from the trial document's controller telemetry (bulk
polls, trickle KF steps, one row per tap cycle; the same rows as the
``--- BEGIN trickle telemetry CSV ---`` block in ``zero/serial_<uuid>.log``).
The 10 g dose (``676d8b4b``) hit a firmware MemoryError after its scoring read,
which lost the Pico's telemetry buffer, so its series is parsed from the
console lines of its serial log instead (``source = console``: 1 s time
resolution in bulk and tap rows, and no raw balance reading in trickle rows).

Commanded tilt, auger speed and tap mode are not logged per row; they're filled
in from the dose's executed parameters by phase (bulk: ``bulk_tilt_deg`` at
``bulk_rpm`` with cadence taps; trickle: ``trickle_tilt_deg`` with the logged PI
``rpm_cmd``; tap: ``tap_tilt_deg``, auger stopped, single taps).

Usage: python3 data/opt/production-salt/extract_doses.py
"""
import csv
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ZERO = os.path.join(HERE, "zero")
OUT = os.path.join(HERE, "doses")

TIDY_COLS = ["powder_id", "target_g", "trial_uuid8", "t_s", "phase",
             "mass_g", "kf_mass_g", "kf_rate_gps", "kf_sigma_g", "ff_gpr",
             "rate_setpoint_gps", "pred_g", "cutoff_g", "tilt_deg_cmd",
             "auger_rpm_cmd", "tap_mode", "source"]

POLL = re.compile(r"\[phase 1 bulk\] poll \d+(?: \(unstable\))?: mass "
                  r"(?P<m>-?[\d.]+) / .*elapsed (?P<t>[\d.]+) s")
SETTLED = re.compile(r"\[phase 1 bulk\] settled: mass (?P<m>-?[\d.]+) / "
                     r".*elapsed (?P<t>[\d.]+) s")
TRICKLE = re.compile(r"\[trickle\]\s+(?P<t>[\d.]+)s m (?P<m>-?[\d.]+) r\s+"
                     r"(?P<r>-?[\d.]+) mg/s \(sp\s+(?P<sp>-?[\d.]+)\) rpm\s+"
                     r"(?P<rpm>-?[\d.]+) pred (?P<pred>-?[\d.]+)/"
                     r"(?P<cut>-?[\d.]+) sigma\s+(?P<sig>-?[\d.]+) mg")
TAP = re.compile(r"\[phase 3 tap\] cycle \d+: mass (?P<m>-?[\d.]+) / "
                 r".*elapsed (?P<t>[\d.]+) s")


def actuators(phase, p, rpm_cmd=""):
    """(tilt_deg_cmd, auger_rpm_cmd, tap_mode) for one telemetry row."""
    if phase == "bulk":
        taps = "cadence {}/{} ms".format(p["tap_cadence_on_ms"],
                                         p["tap_cadence_off_ms"]) \
            if p.get("bulk_tap") else "none"
        return p["bulk_tilt_deg"], p["bulk_rpm"], taps
    if phase == "bulk_settled":
        return p["bulk_tilt_deg"], 0.0, "none"
    if phase == "trickle":
        return p["trickle_tilt_deg"], rpm_cmd, "none"
    if phase == "trickle_end":
        return p["trickle_tilt_deg"], 0.0, "none"
    if phase == "tap":
        return p["tap_tilt_deg"], 0.0, "single x{}".format(
            p.get("taps_per_cycle", 1))
    return "", "", ""


def from_telemetry(doc):
    tel = doc["telemetry"]
    cols = tel["header"].split(",")
    rows = [dict(zip(cols, line.split(","))) for line in tel["rows"]]
    out = []
    for i, r in enumerate(rows):
        phase = r["phase"]
        nxt = rows[i + 1]["phase"] if i + 1 < len(rows) else ""
        if phase == "bulk" and nxt != "bulk":
            phase = "bulk_settled"  # the settled read after the auger halts
        tilt, rpm, taps = actuators(phase, doc["parameters_executed"],
                                    r.get("rpm_cmd", ""))
        out.append({
            "t_s": r["t_s"], "phase": phase, "mass_g": r["z_g"],
            "kf_mass_g": r["m_g"] if phase == "trickle" else "",
            "kf_rate_gps": r["r_gps"], "kf_sigma_g": r["sigma_g"],
            "ff_gpr": r["ff_gpr"], "rate_setpoint_gps": r["r_sp_gps"],
            "pred_g": r["pred_g"], "cutoff_g": r["cutoff_g"],
            "tilt_deg_cmd": tilt, "auger_rpm_cmd": rpm, "tap_mode": taps,
            "source": "telemetry"})
    return out


def from_console(doc, log_path):
    p = doc["parameters_executed"]
    out = []
    with open(log_path) as f:
        lines = f.read().splitlines()
    start = max(i for i, s in enumerate(lines) if s.startswith(">> g "))
    for s in lines[start:]:
        for rx, phase in ((POLL, "bulk"), (SETTLED, "bulk_settled"),
                          (TAP, "tap")):
            m = rx.match(s)
            if m:
                tilt, rpm, taps = actuators(phase, p)
                out.append({"t_s": m["t"], "phase": phase,
                            "mass_g": m["m"], "tilt_deg_cmd": tilt,
                            "auger_rpm_cmd": rpm, "tap_mode": taps,
                            "source": "console"})
                break
        else:
            m = TRICKLE.match(s)
            if m:
                tilt, rpm, taps = actuators("trickle", p, m["rpm"])
                out.append({
                    "t_s": m["t"], "phase": "trickle", "mass_g": "",
                    "kf_mass_g": m["m"],
                    "kf_rate_gps": "{:.5f}".format(float(m["r"]) / 1000),
                    "kf_sigma_g": "{:.5f}".format(float(m["sig"]) / 1000),
                    "rate_setpoint_gps": "{:.5f}".format(
                        float(m["sp"]) / 1000),
                    "pred_g": m["pred"], "cutoff_g": m["cut"],
                    "tilt_deg_cmd": tilt, "auger_rpm_cmd": rpm,
                    "tap_mode": taps, "source": "console"})
    return out


def label(target_g):
    return ("{:g}".format(target_g)).replace(".", "p")


def main():
    docs = []
    for path in sorted(glob.glob(os.path.join(ZERO, "trial_*.json"))):
        with open(path) as f:
            docs.append(json.load(f))
    docs.sort(key=lambda d: d["started_utc"])
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for d in docs:
        u8 = d["trial_uuid"][:8]
        if d["telemetry"]["rows"]:
            rows = from_telemetry(d)
        else:
            rows = from_console(d, os.path.join(
                ZERO, "serial_{}.log".format(d["trial_uuid"])))
        name = "dose_{}g_{}.csv".format(label(d["target_g"]), u8)
        with open(os.path.join(OUT, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=TIDY_COLS)
            w.writeheader()
            for r in rows:
                r.update(powder_id=d["powder_id"], target_g=d["target_g"],
                         trial_uuid8=u8)
                w.writerow({k: r.get(k, "") for k in TIDY_COLS})
        o = d["outcomes"]
        summary.append({
            "trial_uuid": d["trial_uuid"], "started_utc": d["started_utc"],
            "powder_id": d["powder_id"], "target_g": d["target_g"],
            "settled_final_g": o["settled_final_g"],
            "error_mg": o["error_mg"], "status": d["flags"]["status"],
            "t_bulk_s": o["t_bulk_s"], "t_trickle_s": o["t_trickle_s"],
            "t_tap_s": o["t_tap_s"], "t_total_s": o["t_total_s"],
            "taps": o["taps"], "auger_rev": o["auger_rev"],
            "ff_g_per_rev": o["ff_g_per_rev"],
            "profile_id": d["covariates"]["profile_id"],
            "firmware": d["device"]["firmware"],
            "timeseries_rows": len(rows),
            "timeseries_source": rows[0]["source"] if rows else "",
            "timeseries_file": "doses/" + name})
    with open(os.path.join(HERE, "doses_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    for s in summary:
        print("{started_utc:.19s} {target_g:>7} g -> {settled_final_g} g "
              "({error_mg:+} mg, {status}), {timeseries_rows} rows "
              "[{timeseries_source}]".format(**s))
    plot([s for s in summary if s["started_utc"].startswith("2026-10-06")])


def plot(session):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # reference palette (dataviz skill): first three categorical slots
    colors = {"bulk": "#2a78d6", "trickle": "#eb6834", "tap": "#1baf7a"}
    ink, ink2, grid, surface = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    session = sorted(session, key=lambda s: s["target_g"])
    fig, axes = plt.subplots(1, len(session), figsize=(3.3 * len(session),
                                                        3.6),
                             facecolor=surface)
    for ax, s in zip(axes, session):
        with open(os.path.join(HERE, s["timeseries_file"])) as f:
            rows = list(csv.DictReader(f))
        for phase, c in colors.items():
            pts = [(float(r["t_s"]), float(r["mass_g"] or r["kf_mass_g"]))
                   for r in rows
                   if r["phase"].startswith(phase)
                   and (r["mass_g"] or r["kf_mass_g"])]
            if pts:
                x, y = zip(*pts)
                ax.plot(x, y, "-o", color=c, lw=2, ms=4.5, label=phase,
                        mec=surface, mew=0.8, zorder=3)
        ax.axhline(s["target_g"], color=ink2, lw=1, ls=(0, (4, 3)),
                   zorder=2)
        ax.set_facecolor(surface)
        ax.grid(color=grid, lw=0.8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(grid)
        ax.tick_params(colors=ink2, labelsize=8.5)
        ax.set_xlabel("time since dose command (s)", color=ink2, fontsize=9)
        ax.set_title("{:g} g target → {:.4f} g ({:+.1f} mg)".format(
            s["target_g"], s["settled_final_g"], s["error_mg"]),
            color=ink, fontsize=10, loc="left")
        note = "{:.0f} s, {} taps".format(s["t_total_s"], s["taps"])
        if s["status"] != "ok":
            note += "\nstatus {} (after the scoring read)".format(
                s["status"])
        ax.text(0.98, 0.04, note, transform=ax.transAxes, ha="right",
                va="bottom", color=ink2, fontsize=8)
    axes[0].set_ylabel("cup mass (g)", color=ink2, fontsize=9)
    from matplotlib.lines import Line2D
    fig.legend([Line2D([], [], color=c, lw=2, marker="o", ms=4.5)
                for c in colors.values()], list(colors), frameon=False,
               fontsize=9, loc="upper right", ncol=3, labelcolor=ink)
    fig.suptitle("Salt production doses, 2026-10-06 (trickle_tap, profile "
                 "bo-005): five targets, dashed line = target", color=ink,
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "production_salt_doses.png"), dpi=150,
                facecolor=surface)


if __name__ == "__main__":
    main()

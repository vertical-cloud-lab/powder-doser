#!/usr/bin/env python3
"""Powder-doser runs that all dosed the same target mass (issue #210).

Builds two sets from data that is committed on unmerged branches, so a data
assimilation project can start from tidy files:

A. ``salt-0p5g/``: five replicate doses of table salt to **0.5 g**, all at the
   same validated settings (the `bo-005` block of campaign
   ``salt-20260929T014732Z``, 2026-10-06). Each dose has the controller's
   per-step telemetry: the raw balance reading plus the on-device Kalman
   filter's mass, rate and sigma during the trickle stage.
B. ``five-powders-0p2g/``: five battery runs, one per powder, each with three
   closed-loop doses to **0.2 g** (Block H of issue #116, 2026-09-03..10).
   Their time series is parsed from the console lines of the raw serial log:
   one balance reading per bulk poll or per settled cycle, with 1 s time
   resolution.

Usage (from the repository root):

    git fetch origin   # the source commits below must be present
    python3 data/assimilation/extract.py --fetch   # copy sources into */source/
    python3 data/assimilation/extract.py           # rebuild CSVs + figures from */source/

Only the standard library is needed for the CSVs; the figures need matplotlib.
"""
import argparse
import csv
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# --------------------------------------------------------------------------
# Set A: salt, 0.5 g, five replicates of the validated bo-005 profile
# --------------------------------------------------------------------------
SALT_COMMIT = "d14a50dd4eb4dd0e8530a79598e42a54a78fc2c9"  # claude/issue-164-20260922-1928
SALT_SRC = "data/opt/salt-20260929T014732Z/zero"
SALT_TRIALS = [  # (campaign trial_index, trial_uuid); val-bo-005-00 .. -04
    (44, "21352011-eb91-4001-b4f0-95315ebae310"),
    (45, "ca073c06-e01c-4a60-bcbf-26307d0e6735"),
    (46, "b329caa2-f3d7-4353-85ca-27ebd40eb937"),
    (47, "18637814-04d9-4379-83a4-6cc25f08c65a"),
    (48, "b3332ddd-9d2f-473a-a18c-72b92ea13939"),
]
SALT_DIR = os.path.join(HERE, "salt-0p5g")

SALT_COLS = ["run", "trial_uuid8", "t_s", "phase", "mass_g", "fresh",
             "kf_mass_g", "kf_rate_gps", "kf_sigma_g", "kf_clamp_hits",
             "ff_gpr", "rate_setpoint_gps", "rate_err_gps", "pi_integ",
             "pred_g", "cutoff_g", "tilt_deg_cmd", "auger_rpm_cmd",
             "tap_mode"]

# --------------------------------------------------------------------------
# Set B: five powders, 0.2 g, battery Block H (three doses per run)
# --------------------------------------------------------------------------
BATTERY_COMMIT = "f7544503d010356feb2a5c56377b526d0a112ff3"  # claude/issue-116-20260915-1622
BATTERY_RUNS = [  # data/battery/<run dir>, powder_id
    ("20260903T214049Z_salt", "salt"),
    ("20260904T190011Z_white-rice-flour", "white-rice-flour"),
    ("20260904T203727Z_xanthan-gum", "xanthan-gum"),
    ("20260910T133932Z_sodium-sulfate", "sodium-sulfate"),
    ("20260910T194447Z_alsi10mg", "alsi10mg"),
]
POWDERS_DIR = os.path.join(HERE, "five-powders-0p2g")
TARGET_B_G = 0.2

SERIES_B_COLS = ["powder_id", "run_dir", "dose_n", "dose_rep", "t_s",
                 "phase", "cycle", "read", "mass_g", "tilt_deg_cmd",
                 "actuation"]

RX_START = re.compile(r"^\[dose\] three-phase dose to (?P<target>[\d.]+) g")
RX_TARED = re.compile(r"^\[dose\] tared: baseline (?P<base>[+-]?[\d.]+) mg "
                      r".*drift (?P<drift>[+-]?[\d.]+) mg/min, read noise "
                      r"(?P<noise>[\d.]+) mg")
RX_PHASE = re.compile(r"^=== phase \d/3 '(?P<phase>\w+)' start: .*angle "
                      r"(?P<tilt>-?[\d.]+) plate deg, (?P<act>.*?)"
                      r"(?:, settle \d+ ms)?$")
RX_POLL = re.compile(r"^\[phase 1 bulk\] poll (?P<n>\d+)(?P<unst> \(unstable\))?"
                     r": mass (?P<m>-?[\d.]+) / .*elapsed (?P<t>[\d.]+) s")
RX_SETTLED = re.compile(r"^\[phase 1 bulk\] settled: mass (?P<m>-?[\d.]+) / "
                        r".*elapsed (?P<t>[\d.]+) s")
RX_CYCLE = re.compile(r"^\[phase \d (?P<phase>fine|tap)\] cycle (?P<n>\d+): "
                      r"mass (?P<m>-?[\d.]+) / .*elapsed (?P<t>[\d.]+) s")
RX_DOSE = re.compile(r"^DOSE,(?P<n>\d+),(?P<target>[\d.]+),(?P<disp>-?[\d.]+),"
                     r"(?P<err>-?[\d.]+),(?P<status>[\w-]+),(?P<elapsed>[\d.]+),"
                     r"(?P<rev>[\d.]+),(?P<taps>\d+),(?P<cycles>[^,]+),"
                     r"(?P<t_ms>\d+),(?P<block>\w+)")


def git_show(commit, path):
    return subprocess.run(["git", "-C", REPO, "show", "{}:{}".format(commit, path)],
                          check=True, capture_output=True).stdout


def fetch():
    """Copy the source files from the pinned commits into */source/."""
    src = os.path.join(SALT_DIR, "source")
    os.makedirs(src, exist_ok=True)
    for _, uuid in SALT_TRIALS:
        for name in ("trial_{}.json".format(uuid), "serial_{}.log".format(uuid)):
            with open(os.path.join(src, name), "wb") as f:
                f.write(git_show(SALT_COMMIT, "{}/{}".format(SALT_SRC, name)))
    src = os.path.join(POWDERS_DIR, "source")
    os.makedirs(src, exist_ok=True)
    for run_dir, powder in BATTERY_RUNS:
        for name in ("raw_serial_{}.log".format(powder),
                     "doses_{}.csv".format(powder)):
            data = git_show(BATTERY_COMMIT,
                            "data/battery/{}/{}".format(run_dir, name))
            with open(os.path.join(src, "{}__{}".format(run_dir, name)), "wb") as f:
                f.write(data)


# --------------------------------------------------------------------------
# Set A
# --------------------------------------------------------------------------
def salt_actuators(phase, p, rpm_cmd):
    """Commanded (tilt, auger rpm, tap mode); only trickle rpm is logged per row."""
    if phase == "bulk":
        taps = ("cadence {}/{} ms".format(p["tap_cadence_on_ms"], p["tap_cadence_off_ms"])
                if p.get("bulk_tap") else "none")
        return p["bulk_tilt_deg"], p["bulk_rpm"], taps
    if phase in ("bulk_settled",):
        return p["bulk_tilt_deg"], 0.0, "none"
    if phase == "trickle":
        return p["trickle_tilt_deg"], rpm_cmd, "none"
    if phase == "trickle_end":
        return p["trickle_tilt_deg"], 0.0, "none"
    if phase in ("tap", "final_scored"):
        return p["tap_tilt_deg"], 0.0, ("single x{}".format(p.get("taps_per_cycle", 1))
                                        if phase == "tap" else "none")
    return "", "", ""


def build_salt():
    src = os.path.join(SALT_DIR, "source")
    summary = []
    series = {}
    for k, (trial_index, uuid) in enumerate(SALT_TRIALS, start=1):
        with open(os.path.join(src, "trial_{}.json".format(uuid))) as f:
            doc = json.load(f)
        assert doc["trial_index"] == trial_index and doc["target_g"] == 0.5
        p = doc["parameters_executed"]
        tel = doc["telemetry"]
        cols = tel["header"].split(",")
        raw = [dict(zip(cols, line.split(","))) for line in tel["rows"]]
        rows = []
        for i, r in enumerate(raw):
            phase = r["phase"]
            nxt = raw[i + 1]["phase"] if i + 1 < len(raw) else ""
            if phase == "bulk" and nxt != "bulk":
                phase = "bulk_settled"  # settled read after the auger halts
            kf = phase == "trickle"
            tilt, rpm, taps = salt_actuators(phase, p, r["rpm_cmd"])
            rows.append({
                "run": k, "trial_uuid8": uuid[:8], "t_s": r["t_s"],
                "phase": phase, "mass_g": r["z_g"], "fresh": r["fresh"],
                "kf_mass_g": r["m_g"] if kf else "",
                "kf_rate_gps": r["r_gps"], "kf_sigma_g": r["sigma_g"],
                "kf_clamp_hits": r["clamp_hits"] if kf else "",
                "ff_gpr": r["ff_gpr"], "rate_setpoint_gps": r["r_sp_gps"],
                "rate_err_gps": r["err_gps"], "pi_integ": r["integ"],
                "pred_g": r["pred_g"], "cutoff_g": r["cutoff_g"],
                "tilt_deg_cmd": tilt, "auger_rpm_cmd": rpm, "tap_mode": taps})
        out = doc["outcomes"]
        tilt, rpm, taps = salt_actuators("final_scored", p, "")
        rows.append({"run": k, "trial_uuid8": uuid[:8],
                     "t_s": "{:.2f}".format(out["t_total_s"]),
                     "phase": "final_scored",
                     "mass_g": "{:.5f}".format(out["settled_final_g"]),
                     "fresh": 1, "tilt_deg_cmd": tilt, "auger_rpm_cmd": rpm,
                     "tap_mode": taps})
        name = "run{}_{}.csv".format(k, uuid[:8])
        with open(os.path.join(SALT_DIR, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=SALT_COLS)
            w.writeheader()
            w.writerows(rows)
        series[k] = rows
        bulk_stop = next((e for e in doc["stop_events"] if e["phase"] == "bulk"), {})
        cov = doc["covariates"]
        summary.append({
            "run": k, "csv": name, "campaign_id": doc["campaign_id"],
            "trial_index": trial_index, "trial_uuid": uuid,
            "label": "val-bo-005-{:02d}".format(trial_index - 44),
            "started_utc": doc["started_utc"], "ended_utc": doc["ended_utc"],
            "powder_id": doc["powder_id"], "target_g": doc["target_g"],
            "settled_final_g": out["settled_final_g"],
            "error_mg": out["error_mg"], "status": doc["flags"]["status"],
            "t_total_s": out["t_total_s"], "t_bulk_s": out["t_bulk_s"],
            "t_trickle_s": out["t_trickle_s"], "t_tap_s": out["t_tap_s"],
            "taps": out["taps"], "auger_rev": out["auger_rev"],
            "ff_g_per_rev": out["ff_g_per_rev"],
            "bulk_afterflow_g": bulk_stop.get("afterflow_g", ""),
            "cup_load_g": cov.get("cup_load_g", ""),
            "doses_since_cup_empty": cov.get("doses_since_cup_empty", ""),
            "telemetry_rows": len(raw), "firmware": doc["device"]["firmware"],
            "git_commit": doc["git_commit"]})
    with open(os.path.join(SALT_DIR, "runs_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    return summary, series


# --------------------------------------------------------------------------
# Set B
# --------------------------------------------------------------------------
def parse_battery_log(path):
    """Yield one dict per dose: header fields plus its time series rows."""
    doses, cur = [], None
    tilt, act = "", ""
    with open(path, errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            m = RX_START.match(line)
            if m:
                cur = {"target_g": float(m["target"]), "rows": [],
                       "tare_baseline_mg": "", "tare_drift_mg_per_min": "",
                       "tare_read_noise_mg": ""}
                tilt, act = "", ""
                continue
            if cur is None:
                continue
            m = RX_TARED.match(line)
            if m:
                cur["tare_baseline_mg"] = m["base"]
                cur["tare_drift_mg_per_min"] = m["drift"]
                cur["tare_read_noise_mg"] = m["noise"]
                continue
            m = RX_PHASE.match(line)
            if m:
                tilt, act = m["tilt"], m["act"].strip()
                continue
            m = RX_POLL.match(line)
            if m:
                cur["rows"].append({"t_s": m["t"], "phase": "bulk", "cycle": m["n"],
                                    "read": "poll_unstable" if m["unst"] else "poll",
                                    "mass_g": m["m"], "tilt_deg_cmd": tilt,
                                    "actuation": act})
                continue
            m = RX_SETTLED.match(line)
            if m:
                cur["rows"].append({"t_s": m["t"], "phase": "bulk_settled", "cycle": "",
                                    "read": "settled", "mass_g": m["m"],
                                    "tilt_deg_cmd": tilt, "actuation": "auger halted"})
                continue
            m = RX_CYCLE.match(line)
            if m:
                cur["rows"].append({"t_s": m["t"], "phase": m["phase"], "cycle": m["n"],
                                    "read": "settled", "mass_g": m["m"],
                                    "tilt_deg_cmd": tilt, "actuation": act})
                continue
            m = RX_DOSE.match(line)
            if m:
                cur.update({"dose_n": int(m["n"]), "dispensed_g": float(m["disp"]),
                            "error_mg": round(float(m["err"]) * 1000, 1),
                            "status": m["status"], "elapsed_s": float(m["elapsed"]),
                            "auger_rev": float(m["rev"]), "taps": int(m["taps"]),
                            "phase_cycles": m["cycles"], "t_ms_since_run_start": int(m["t_ms"]),
                            "block": m["block"]})
                cur["rows"].append({"t_s": m["elapsed"], "phase": "final_scored",
                                    "cycle": "", "read": "settled",
                                    "mass_g": m["disp"], "tilt_deg_cmd": "",
                                    "actuation": ""})
                doses.append(cur)
                cur = None
    return doses


def build_powders():
    src = os.path.join(POWDERS_DIR, "source")
    summary, series_rows, series = [], [], {}
    for run_dir, powder in BATTERY_RUNS:
        log = os.path.join(src, "{}__raw_serial_{}.log".format(run_dir, powder))
        doses = [d for d in parse_battery_log(log)
                 if abs(d["target_g"] - TARGET_B_G) < 1e-9]
        with open(os.path.join(src, "{}__doses_{}.csv".format(run_dir, powder))) as f:
            ref = [r for r in csv.DictReader(f) if abs(float(r["target_g"]) - TARGET_B_G) < 1e-9]
        # The parsed DOSE lines must match the run's own doses CSV.
        assert [(d["dose_n"], d["dispensed_g"]) for d in doses] == \
            [(int(r["n"]), float(r["dispensed_g"])) for r in ref], run_dir
        series[powder] = []
        for rep, d in enumerate(doses, start=1):
            for r in d["rows"]:
                series_rows.append(dict(r, powder_id=powder, run_dir=run_dir,
                                        dose_n=d["dose_n"], dose_rep=rep))
            series[powder].append(d)
            summary.append({
                "powder_id": powder, "run_dir": run_dir,
                "run_started_utc": "{}-{}-{}T{}:{}:{}Z".format(
                    run_dir[0:4], run_dir[4:6], run_dir[6:8],
                    run_dir[9:11], run_dir[11:13], run_dir[13:15]),
                "dose_n": d["dose_n"], "dose_rep": rep, "block": d["block"],
                "target_g": d["target_g"], "dispensed_g": d["dispensed_g"],
                "error_mg": d["error_mg"], "status": d["status"],
                "elapsed_s": d["elapsed_s"], "auger_rev": d["auger_rev"],
                "taps": d["taps"], "phase_cycles": d["phase_cycles"],
                "tare_baseline_mg": d["tare_baseline_mg"],
                "tare_drift_mg_per_min": d["tare_drift_mg_per_min"],
                "tare_read_noise_mg": d["tare_read_noise_mg"],
                "series_rows": len(d["rows"])})
    with open(os.path.join(POWDERS_DIR, "doses_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    with open(os.path.join(POWDERS_DIR, "doses_series.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SERIES_B_COLS)
        w.writeheader()
        w.writerows(series_rows)
    return summary, series


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3de"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # validated slots 1-5


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.6, linestyle="-")
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#b5b4ae")
    ax.tick_params(colors=INK2, labelsize=9)
    ax.xaxis.label.set_color(INK2)
    ax.yaxis.label.set_color(INK2)


def fnum(s):
    return float(s) if s not in ("", None) else float("nan")


def plot_salt(summary, series):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6), dpi=150,
                                 gridspec_kw={"width_ratios": [1.25, 1]})
    fig.patch.set_facecolor(SURFACE)
    for ax in (a1, a2):
        style(ax)
    a1.axhline(0.5, color=INK2, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
    for s, color in zip(summary, SERIES):
        rows = series[s["run"]]
        t = [fnum(r["t_s"]) for r in rows]
        z = [fnum(r["mass_g"]) for r in rows]
        lab = "run {}: {} ({} g, {:+.1f} mg, {:.0f} s)".format(
            s["run"], s["trial_uuid"][:8], s["settled_final_g"], s["error_mg"], s["t_total_s"])
        a1.plot(t, z, color=color, linewidth=1.6, solid_joinstyle="round",
                solid_capstyle="round", label=lab, zorder=3)
        a1.plot(t[-1:], z[-1:], "o", color=color, markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=4)
        tr = [r for r in rows if r["phase"] in ("bulk_settled", "trickle", "trickle_end")]
        tt = [fnum(r["t_s"]) for r in tr]
        a2.plot(tt, [fnum(r["mass_g"]) for r in tr], color=color, linewidth=1.6,
                marker="o", markersize=3.2, markeredgewidth=0, zorder=3)
        kf = [r for r in tr if r["phase"] == "trickle"]
        a2.plot([fnum(r["t_s"]) for r in kf], [fnum(r["kf_mass_g"]) for r in kf],
                color=color, linewidth=1.3, linestyle=(0, (2, 1.6)), zorder=3)
    a1.set_xlabel("time since the dose command (s)")
    a1.set_ylabel("mass on the balance (g)")
    a1.set_ylim(-0.02, 0.56)
    a1.text(1, 0.505, "target 0.5 g", ha="left", va="bottom", fontsize=8.5, color=INK2)
    a1.text(11.5, 0.17, "bulk (auger 100 rpm)", fontsize=8.5, color=INK2)
    a1.text(15, 0.22, "trickle\n(PI + KF)", fontsize=8.5, color=INK2)
    a1.text(52, 0.42, "single taps", fontsize=8.5, color=INK2)
    a1.legend(loc="lower right", fontsize=8, frameon=False, labelcolor=INK)
    a1.set_title("Five replicate 0.5 g salt doses, same settings (bo-005, 2026-10-06)",
                 fontsize=10.5, color=INK, loc="left")
    a2.set_xlim(10, 28)
    a2.set_ylim(0.27, 0.47)
    a2.set_xlabel("time since the dose command (s)")
    a2.set_ylabel("mass (g)")
    a2.set_title("Trickle stage: balance reading vs on-device KF mass", fontsize=10.5,
                 color=INK, loc="left")
    a2.legend(handles=[
        Line2D([], [], color=INK2, linewidth=1.6, marker="o", markersize=3.2,
               label="balance reading (observation)"),
        Line2D([], [], color=INK2, linewidth=1.3, linestyle=(0, (2, 1.6)),
               label="Kalman-filter mass estimate")],
        loc="upper left", fontsize=8, frameon=False, labelcolor=INK)
    fig.tight_layout()
    out = os.path.join(HERE, "salt_0p5g_five_runs.png")
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


POWDER_NAMES = {"salt": "salt (NaCl)", "white-rice-flour": "white rice flour",
                "xanthan-gum": "xanthan gum", "sodium-sulfate": "sodium sulfate",
                "alsi10mg": "AlSi10Mg (metal)"}


def plot_powders(series):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    fig, axes = plt.subplots(2, 3, figsize=(12, 6.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    flat = axes.ravel()
    for ax, (run_dir, powder) in zip(flat, BATTERY_RUNS):
        style(ax)
        ax.axhline(TARGET_B_G, color=INK2, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
        for d, color in zip(series[powder], SERIES[:3]):
            rows = d["rows"]
            t = [fnum(r["t_s"]) for r in rows]
            m = [fnum(r["mass_g"]) for r in rows]
            ax.plot(t, m, color=color, linewidth=1.5, marker="o", markersize=2.6,
                    markeredgewidth=0, zorder=3)
            ax.plot(t[-1:], m[-1:], "o", color=color, markersize=5,
                    markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=4)
        errs = ", ".join("{:+.1f}".format(d["error_mg"]) for d in series[powder])
        ax.set_title("{}  ·  {}-{}-{}\nfinal error {} mg".format(
            POWDER_NAMES[powder], run_dir[:4], run_dir[4:6], run_dir[6:8], errs),
            fontsize=9.5, color=INK, loc="left")
        ax.set_ylim(-0.045, 0.25)
        ax.set_xlim(left=0)
        ax.set_xlabel("time since the dose command (s)", fontsize=8.5)
        ax.set_ylabel("mass on the balance (g)", fontsize=8.5)
    leg = flat[5]
    leg.axis("off")
    leg.legend(handles=[Line2D([], [], color=c, linewidth=1.5, marker="o", markersize=3,
                               label=l) for c, l in zip(
                                   SERIES[:3], ["1st 0.2 g dose", "2nd 0.2 g dose",
                                                "3rd 0.2 g dose"])] +
               [Line2D([], [], color=INK2, linewidth=1.0, linestyle=(0, (4, 3)),
                       label="target 0.2 g")],
               loc="center left", fontsize=9, frameon=False, labelcolor=INK,
               title="Battery Block H (issue #116),\nthree-phase controller,\n"
                     "one panel per powder; note\nthe different time axes",
               title_fontsize=9, alignment="left")
    fig.tight_layout()
    out = os.path.join(HERE, "five_powders_0p2g.png")
    fig.savefig(out, facecolor=SURFACE)
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
    s_sum, s_series = build_salt()
    p_sum, p_series = build_powders()
    for s in s_sum:
        print("A run {run}: {trial_uuid} {settled_final_g} g ({error_mg:+} mg, "
              "{status}) in {t_total_s} s, {telemetry_rows} telemetry rows".format(**s))
    for s in p_sum:
        print("B {powder_id} dose {dose_n}: {dispensed_g} g ({error_mg:+} mg, {status}) "
              "in {elapsed_s} s, {series_rows} rows".format(**s))
    if not args.no_plots:
        print(plot_salt(s_sum, s_series))
        print(plot_powders(p_series))


if __name__ == "__main__":
    main()

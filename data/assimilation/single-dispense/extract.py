#!/usr/bin/env python3
"""Single continuous auger dispenses of five powders, with continuous balance readings (issue #210).

Source: Block D ("speed") of the uniform powder battery (issue #116, battery_version 2). In
Block D the auger turns continuously at a fixed speed (15, 45, then 90 rpm) at tilt setting 45
(a physical tube angle of 22.5 deg) while the balance is read every ~0.39 s. There is no controller: no bulk/fine/tap stages,
no feedback, one uninterrupted dispense per speed.

    python3 data/assimilation/single-dispense/extract.py --fetch   # recopy source/ and weather/
    python3 data/assimilation/single-dispense/extract.py           # rebuild runs/, all_runs.csv, runs_summary.csv

--fetch needs `git fetch origin` (the pinned commit below must be present), MONGODB_URI for the
database copies (read-only; skipped if unset) and internet access for the weather. The rebuild
needs only the Python standard library.
"""
import csv
import datetime as dt
import json
import os
import statistics
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "source"
WX = HERE / "weather"
RUNS = HERE / "runs"

# Branch claude/issue-116-20260915-1622, where the battery runs were committed.
COMMIT = "f754450"

# One battery_version-2 run per powder, all run 2026-08-20/21 with identical settings.
RUN_DIRS = [
    "20260821T192031Z_salt",
    "20260820T192224Z_sodium-sulfate",
    "20260820T214823Z_silicon-110-200",
    "20260821T151337Z_alsi10mg",
    "20260821T170712Z_barium-chloride",
]
NOTES = {
    "20260821T192031Z_salt": "docs/battery-runs/2026-08-21-salt-control-repeat.md",
    "20260820T192224Z_sodium-sulfate": "docs/battery-runs/2026-08-20-sodium-sulfate.md",
    "20260820T214823Z_silicon-110-200": "docs/battery-runs/2026-08-20-silicon-110-200.md",
    "20260821T151337Z_alsi10mg": "docs/battery-runs/2026-08-21-alsi10mg.md",
    "20260821T170712Z_barium-chloride": "docs/battery-runs/2026-08-21-barium-chloride.md",
}
# Files copied from each run folder (the PNG figures are left out).
RUN_FILES = ["raw_serial_{p}.log", "polls_{p}.csv", "trials_{p}.csv", "summary_{p}.csv",
             "timeline_{p}.csv", "retries_{p}.csv", "doses_{p}.csv", "run_{p}.json"]

# Provo Municipal Airport (KPVU) METAR archive, via the Iowa Environmental Mesonet.
WX_FILE = WX / "KPVU_2026-08-20_to_2026-08-21_metar.csv"
WX_URL = ("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=PVU"
          "&data=tmpc&data=dwpc&data=relh&data=alti&year1=2026&month1=8&day1=20"
          "&year2=2026&month2=8&day2=22&tz=Etc%2FUTC&format=onlycomma&latlon=yes&elev=yes"
          "&missing=empty&trace=empty&direct=no&report_type=3&report_type=4")
MDT = dt.timezone(dt.timedelta(hours=-6), "MDT")


def git_show(path):
    out = subprocess.run(["git", "show", f"{COMMIT}:{path}"], capture_output=True, check=True)
    return out.stdout


def fetch():
    for rd in RUN_DIRS:
        p = rd.split("_", 1)[1]
        dst = SRC / rd
        dst.mkdir(parents=True, exist_ok=True)
        for pat in RUN_FILES:
            name = pat.format(p=p)
            try:
                data = git_show(f"data/battery/{rd}/{name}")
            except subprocess.CalledProcessError:
                print(f"  {rd}: no {name} at {COMMIT}")
                continue
            (dst / name).write_bytes(data)
    uri = os.environ.get("MONGODB_URI")
    if uri:
        import pymongo  # only needed for --fetch
        db = pymongo.MongoClient(uri, serverSelectionTimeoutMS=15000)["powder_doser"]
        for rd in RUN_DIRS:
            p = rd.split("_", 1)[1]
            run = json.loads((SRC / rd / f"run_{p}.json").read_text())
            doc = db.battery_runs.find_one({"powder_id": run["powder_id"],
                                            "started_utc": run["started_utc"]})
            if doc is None:
                print(f"  {rd}: not found in battery_runs")
                continue
            doc["_id"] = str(doc["_id"])
            (SRC / rd / "mongodb_battery_runs.json").write_text(
                json.dumps(doc, indent=1, default=str) + "\n")
    else:
        print("  MONGODB_URI unset: database copies not refreshed")
    WX.mkdir(exist_ok=True)
    req = urllib.request.Request(WX_URL, headers={"User-Agent": "generic-data-client"})
    WX_FILE.write_bytes(urllib.request.urlopen(req, timeout=60).read())


def parse_utc(s):
    s = s.replace("Z", "+00:00")
    t = dt.datetime.fromisoformat(s)
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def load_weather():
    rows = []
    with open(WX_FILE) as f:
        for r in csv.DictReader(f):
            if not r["tmpc"] or not r["relh"]:
                continue
            t = dt.datetime.strptime(r["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
            rows.append((t, float(r["tmpc"]), float(r["relh"]), float(r["dwpc"])))
    rows.sort()
    return rows


def weather_at(wx, t):
    """Linear interpolation between the two METAR reports that bracket t."""
    for (t0, T0, H0, D0), (t1, T1, H1, D1) in zip(wx, wx[1:]):
        if t0 <= t <= t1:
            w = (t - t0).total_seconds() / (t1 - t0).total_seconds()
            return (T0 + w * (T1 - T0), H0 + w * (H1 - H0), D0 + w * (D1 - D0), t0, t1)
    raise ValueError(f"no weather around {t}")


def fnum(x, nd=4):
    return "" if x is None else f"{x:.{nd}f}"


def build():
    wx = load_weather()
    RUNS.mkdir(exist_ok=True)
    cols = ["powder_id", "run_id", "dispense_id", "auger_rpm", "tilt_deg", "tube_angle_deg", "row_type", "t_s",
            "t_device_ms", "utc", "balance_g", "mass_g", "stable", "auger_on",
            "outdoor_temp_c", "outdoor_rh_pct", "outdoor_dewpoint_c"]
    all_rows, summary = [], []
    offsets = {}
    runs = {}
    for rd in RUN_DIRS:
        p = rd.split("_", 1)[1]
        run = json.loads((SRC / rd / f"run_{p}.json").read_text())
        with open(SRC / rd / f"trials_{p}.csv") as f:
            trials = list(csv.DictReader(f))
        with open(SRC / rd / f"polls_{p}.csv") as f:
            polls = [r for r in csv.DictReader(f) if r["block"] == "D"]
        runs[rd] = (p, run, trials, polls)
        # Device clock -> UTC. The host logged when each block started; the device's clock
        # (t_ms) at that moment is the time of the previous block's last trial row.
        tl = {b["block"]: b for b in run.get("block_timeline") or []}
        if tl.get("D", {}).get("started_utc"):
            last_c = max(int(t["t_ms"]) for t in trials if t["block"] == "C")
            off = (parse_utc(tl["D"]["started_utc"]) - parse_utc(run["started_utc"])).total_seconds() - last_c / 1000
            offsets[rd] = off
            if tl.get("E", {}).get("started_utc"):
                last_d = max(int(t["t_ms"]) for t in trials if t["block"] == "D")
                off_e = (parse_utc(tl["E"]["started_utc"]) - parse_utc(run["started_utc"])).total_seconds() - last_d / 1000
                print(f"  {rd}: device->host offset {off:.2f} s (block D anchor), {off_e:.2f} s (block E anchor)")
    typical = statistics.median(offsets.values())

    for rd in RUN_DIRS:
        p, run, trials, polls = runs[rd]
        t0_utc = parse_utc(run["started_utc"])
        off = offsets.get(rd, typical)
        utc_note = "block anchor" if rd in offsets else f"run start + median offset {typical:.1f} s (no block timeline)"
        dtrials = [t for t in trials if t["block"] == "D"]
        file_rows = []
        for k, tr in enumerate(dtrials, 1):
            rpm = float(tr["rpm"])
            ps = [r for r in polls if float(r["rpm"]) == rpm]
            tms = [int(r["t_ms"]) for r in ps]
            period = statistics.median(b - a for a, b in zip(tms, tms[1:]))
            start_ms = tms[0] - period          # the auger starts one poll period before the first reading
            stop_ms = tms[-1]                   # and is stopped right after the last one
            before, after = float(tr["before_g"]), float(tr["after_g"])
            utc_of = lambda ms: t0_utc + dt.timedelta(seconds=off + ms / 1000)
            start_utc = utc_of(start_ms)
            T, H, D, w0, w1 = weather_at(wx, start_utc)
            did = f"{p}_{int(rpm)}rpm"
            env = [f"{T:.1f}", f"{H:.1f}", f"{D:.1f}"]
            # tilt_deg is the firmware setting; the 2:1 plate gear makes the tube angle half of it.
            base = [run["powder_id"], rd, did, f"{rpm:.0f}", tr["tilt_deg"], f"{float(tr['tilt_deg']) / 2:.1f}"]
            rows = [base + ["settled_before", "0.000", "", start_utc.isoformat(timespec="milliseconds"),
                            fnum(before), fnum(0.0), "", "0"] + env]
            for r, ms in zip(ps, tms):
                g = float(r["grams"])
                rows.append(base + ["reading", f"{(ms - start_ms) / 1000:.3f}", str(ms),
                                    utc_of(ms).isoformat(timespec="milliseconds"),
                                    fnum(g), fnum(g - before), r["stable"], "1"] + env)
            after_ms = int(tr["t_ms"])
            rows.append(base + ["settled_after", f"{(after_ms - start_ms) / 1000:.3f}", str(after_ms),
                                utc_of(after_ms).isoformat(timespec="milliseconds"),
                                fnum(after), fnum(after - before), "", "0"] + env)
            with open(RUNS / f"{did}.csv", "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerows(rows)
            file_rows += rows
            on_s = (stop_ms - start_ms) / 1000
            last_mass = float(ps[-1]["grams"]) - before
            summary.append({
                "powder_id": run["powder_id"], "powder": run.get("powder", ""), "batch": run.get("batch", ""),
                "run_id": rd, "dispense_id": did, "file": f"runs/{did}.csv",
                "auger_rpm": f"{rpm:.0f}", "tilt_deg": tr["tilt_deg"],
                "tube_angle_deg": f"{float(tr['tilt_deg']) / 2:.1f}",
                "start_utc": start_utc.isoformat(timespec="seconds"),
                "start_local_mdt": start_utc.astimezone(MDT).strftime("%Y-%m-%d %H:%M:%S"),
                "utc_source": utc_note,
                "n_readings": len(ps), "poll_period_ms": f"{period:.0f}",
                "auger_on_s_est": f"{on_s:.2f}", "auger_revs_nominal": tr["action"],
                "auger_revs_est": f"{rpm / 60 * on_s:.2f}",
                "settled_before_g": tr["before_g"], "settled_after_g": tr["after_g"],
                "dispensed_g": tr["delta_g"], "last_reading_mass_g": f"{last_mass:.4f}",
                "gain_after_stop_g": f"{after - before - last_mass:.4f}",
                "bracket_sigma_g": tr["sigma_g"], "bracket_drift_g": tr["drift_g"],
                "bracket_shock_g": tr["shock_g"], "bracket_retries": tr["retries"],
                "bracket_quality": tr["quality"],
                "outdoor_temp_c": env[0], "outdoor_rh_pct": env[1], "outdoor_dewpoint_c": env[2],
                "weather_reports_utc": f"{w0:%H:%M} and {w1:%H:%M}",
                "operator": run.get("operator", ""), "battery_version": run["parameters"].get("battery_version", ""),
                "firmware_commit": run.get("git_commit") or "",
                "run_notes": f"https://github.com/vertical-cloud-lab/powder-doser/blob/{COMMIT}/{NOTES[rd]}",
            })
        all_rows += file_rows
    with open(HERE / "all_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(all_rows)
    with open(HERE / "runs_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    # Cross-checks: the database copy holds the same polls and Block D trials as the committed files.
    for rd in RUN_DIRS:
        p, run, trials, polls = runs[rd]
        mfile = SRC / rd / "mongodb_battery_runs.json"
        if not mfile.exists():
            continue
        m = json.loads(mfile.read_text())
        mp = [(int(x["t_ms"]), round(float(x["grams"]), 4)) for x in m["polls"] if x["block"] == "D"]
        fp = [(int(x["t_ms"]), round(float(x["grams"]), 4)) for x in polls]
        md = [round(float(x["delta_g"]), 4) for x in m["trials"] if x["block"] == "D"]
        fd = [round(float(x["delta_g"]), 4) for x in trials if x["block"] == "D"]
        assert mp == fp, f"{rd}: polls differ from MongoDB"
        assert md == fd, f"{rd}: Block D trials differ from MongoDB"
    print(f"  wrote {len(summary)} dispenses, {len(all_rows)} rows; polls and trials match MongoDB")


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    build()

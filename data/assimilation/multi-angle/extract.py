#!/usr/bin/env python3
"""Powder battery runs that tested the doser at several tube angles (issue #210).

Every run of the uniform powder battery (issue #116) tested more than one tube angle in three blocks:

  B "hold"      15 s with nothing moving, at tilt settings 0, 45 and 90
  C "rotation"  six single 360 deg auger turns at 30 rpm, at tilt settings 0, 45 and 90
  E "tap"       eight pairs of (one 360 deg re-feed turn, then one tap), at tilt settings 0 and 45

The tilt plate is geared 2:1, so the settings 0/45/90 are tube angles of 0, 22.5 and 45 deg above
horizontal. Each action is bracketed by balance readings taken with nothing moving; the firmware
logs the settled level before and after each action, not the individual readings.

Two sets:
  * the five battery_version-2 runs of ../single-dispense (sources in ../single-dispense/source):
    runs/<powder>.csv, all_trials.csv, angle_summary.csv
  * nine more August runs that passed their QC (sources copied to source/ by --fetch):
    more_powders_trials.csv, more_powders_summary.csv

    python3 data/assimilation/multi-angle/extract.py --fetch   # recopy source/ and weather/
    python3 data/assimilation/multi-angle/extract.py           # rebuild the CSVs

--fetch needs `git fetch origin` (the pinned commit below must be present), MONGODB_URI for the
database copies (read-only) and internet access for the weather. The rebuild needs only the
Python standard library.
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
SD = HERE.parent / "single-dispense"
COMMIT = "f754450"  # branch claude/issue-116-20260915-1622, where the battery runs were committed
MDT = dt.timezone(dt.timedelta(hours=-6), "MDT")
BLOCKS = ("B", "C", "E")
TEST = {"hold": "hold", "rotation": "turn", "refeed": "refeed_turn", "tap": "tap"}
NOTES = "https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/"

# The five runs of ../single-dispense (battery_version 2, 2026-08-20/21).
MAIN = {
    "20260821T192031Z_salt": "2026-08-21-salt-control-repeat.md",
    "20260820T192224Z_sodium-sulfate": "2026-08-20-sodium-sulfate.md",
    "20260820T214823Z_silicon-110-200": "2026-08-20-silicon-110-200.md",
    "20260821T151337Z_alsi10mg": "2026-08-21-alsi10mg.md",
    "20260821T170712Z_barium-chloride": "2026-08-21-barium-chloride.md",
}
# Every other battery run with Block C that its QC marked valid for cross-powder comparison.
MORE = {
    "20260804T211422Z_white-rice-flour": "2026-08-04-white-rice-flour.md",
    "20260805T145725Z_sodium-alginate": "2026-08-05-sodium-alginate.md",
    "20260805T185305Z_brown-rice-flour": "2026-08-05-brown-rice-flour-auger2.md",
    "20260805T200002Z_calcium-lactate": "2026-08-05-calcium-lactate.md",
    "20260805T215252Z_carboxymethyl-cellulose": "2026-08-05-carboxymethyl-cellulose.md",
    "20260806T140254Z_xanthan-gum": "2026-08-06-xanthan-gum.md",
    "20260806T145120Z_salt": "2026-08-06-salt.md",
    "20260812T215154Z_salt": "2026-08-12-salt-repeat.md",
    "20260821T161838Z_silicon-325": "2026-08-21-silicon-325.md",
}
RUN_FILES = ["raw_serial_{p}.log", "trials_{p}.csv", "retries_{p}.csv", "timeline_{p}.csv",
             "summary_{p}.csv", "run_{p}.json"]

# Provo Municipal Airport (KPVU) METAR archive, via the Iowa Environmental Mesonet.
WX_FILES = [SD / "weather" / "KPVU_2026-08-20_to_2026-08-21_metar.csv",
            HERE / "weather" / "KPVU_2026-08-04_to_2026-08-12_metar.csv"]
WX_URL = ("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=PVU"
          "&data=tmpc&data=dwpc&data=relh&data=alti&year1=2026&month1=8&day1=4"
          "&year2=2026&month2=8&day2=13&tz=Etc%2FUTC&format=onlycomma&latlon=yes&elev=yes"
          "&missing=empty&trace=empty&direct=no&report_type=3&report_type=4")

COLS = ["powder_id", "run_id", "block", "test", "tilt_setting", "tube_angle_deg", "trial",
        "row_type", "auger_turn_deg", "auger_rpm", "taps", "hold_s", "t_device_ms", "utc",
        "settled_before_g", "settled_after_g", "delta_g", "cum_delta_g", "sigma_g", "drift_g",
        "shock_g", "retries", "quality", "flag",
        "outdoor_temp_c", "outdoor_rh_pct", "outdoor_dewpoint_c"]
MORE_COLS = COLS + ["battery_version", "qc_verdict"]


def git_show(path):
    return subprocess.run(["git", "show", f"{COMMIT}:{path}"], capture_output=True, check=True).stdout


def fetch():
    src = HERE / "source"
    for rd in MORE:
        p = rd.split("_", 1)[1]
        (src / rd).mkdir(parents=True, exist_ok=True)
        for pat in RUN_FILES:
            try:
                (src / rd / pat.format(p=p)).write_bytes(git_show(f"data/battery/{rd}/{pat.format(p=p)}"))
            except subprocess.CalledProcessError:
                print(f"  {rd}: no {pat.format(p=p)} at {COMMIT}")
    uri = os.environ.get("MONGODB_URI")
    if uri:
        import pymongo  # only needed for --fetch
        db = pymongo.MongoClient(uri, serverSelectionTimeoutMS=15000)["powder_doser"]
        for rd in MORE:
            p = rd.split("_", 1)[1]
            run = json.loads((src / rd / f"run_{p}.json").read_text())
            doc = db.battery_runs.find_one({"powder_id": run["powder_id"], "started_utc": run["started_utc"]})
            if doc is None:
                print(f"  {rd}: not found in battery_runs")
                continue
            doc["_id"] = str(doc["_id"])
            (src / rd / "mongodb_battery_runs.json").write_text(json.dumps(doc, indent=1, default=str) + "\n")
    else:
        print("  MONGODB_URI unset: database copies not refreshed")
    WX_FILES[1].parent.mkdir(exist_ok=True)
    req = urllib.request.Request(WX_URL, headers={"User-Agent": "generic-data-client"})
    WX_FILES[1].write_bytes(urllib.request.urlopen(req, timeout=60).read())


def parse_utc(s):
    t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def load_weather():
    rows = []
    for path in WX_FILES:
        with open(path) as f:
            for r in csv.DictReader(f):
                if not r["tmpc"] or not r["relh"]:
                    continue
                t = dt.datetime.strptime(r["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
                rows.append((t, float(r["tmpc"]), float(r["relh"]), float(r["dwpc"])))
    return sorted(rows)


def weather_at(wx, t):
    """Linear interpolation between the two METAR reports that bracket t."""
    for (t0, T0, H0, D0), (t1, T1, H1, D1) in zip(wx, wx[1:]):
        if t0 <= t <= t1:
            assert (t1 - t0).total_seconds() <= 2 * 3600, f"weather gap around {t}"
            w = (t - t0).total_seconds() / (t1 - t0).total_seconds()
            return T0 + w * (T1 - T0), H0 + w * (H1 - H0), D0 + w * (D1 - D0)
    raise ValueError(f"no weather around {t}")


def read_csv(path):
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def device_offsets(run, trials):
    """Seconds to add to (run start + t_ms) to get UTC, from the host's block start times.

    The host logged when each block started; on the device that is just after the previous
    block's last trial row. Runs whose record has no block times get the median offset of
    the runs of the same battery version.
    """
    tl = {b["block"]: b for b in run.get("block_timeline") or [] if b.get("started_utc")}
    out = []
    for prev, nxt in zip("ABCDE", "BCDE"):
        last = [int(t["t_ms"]) for t in trials if t["block"] == prev]
        if nxt in tl and last:
            out.append((parse_utc(tl[nxt]["started_utc"]) - parse_utc(run["started_utc"])).total_seconds()
                       - max(last) / 1000)
    return out


def g(x):
    return f"{x:.4f}"


def load(run_dirs, src):
    runs = {}
    for rd in run_dirs:
        p = rd.split("_", 1)[1]
        run = json.loads((src / rd / f"run_{p}.json").read_text())
        mongo = json.loads((src / rd / "mongodb_battery_runs.json").read_text())
        runs[rd] = dict(p=p, run=run, mongo=mongo, src=src,
                        trials=read_csv(src / rd / f"trials_{p}.csv"),
                        retries=read_csv(src / rd / f"retries_{p}.csv"),
                        version=str(run["parameters"].get("battery_version", "")))
    return runs


def rows_for(r, off, wx):
    t0 = parse_utc(r["run"]["started_utc"])

    def utc_of(ms):
        return t0 + dt.timedelta(seconds=off + int(ms) / 1000)

    events = [("trial", t) for t in r["trials"] if t["block"] in BLOCKS]
    events += [("discarded_attempt", x) for x in r["retries"] if x["block"] in BLOCKS]
    events.sort(key=lambda e: int(e[1]["t_ms"]))
    rows, cum = [], {}
    for kind, x in events:
        phase = x["phase"]
        setting = float(x["tilt_deg"])
        key = (x["block"], setting)
        turn = phase in ("rotation", "refeed")
        u = utc_of(x["t_ms"])
        T, H, D = weather_at(wx, u)
        if kind == "trial":
            cum[key] = cum.get(key, 0.0) + float(x["delta_g"])
            vals = [x["before_g"], x["after_g"], x["delta_g"], g(cum[key]), x.get("sigma_g", ""),
                    x.get("drift_g", ""), x.get("shock_g", ""), x.get("retries", ""),
                    x.get("quality", ""), x["flag"]]
        else:
            # The after-window was hit by a shock, so the firmware threw this attempt away and
            # repeated the action. The powder it moved stayed in the cup.
            vals = ["", "", x["discarded_delta_g"], g(cum.get(key, 0.0)), "", "", x["shock_g"], "",
                    x["reason"], ""]
        rows.append([r["run"]["powder_id"], None, x["block"], TEST[phase], f"{setting:.0f}",
                     f"{setting / 2:.1f}", x["trial"], kind, "360" if turn else "",
                     "30" if turn else "", "1" if phase == "tap" else "",
                     "15" if phase == "hold" else "", x["t_ms"], u.isoformat(timespec="milliseconds")]
                    + vals + [f"{T:.1f}", f"{H:.1f}", f"{D:.1f}"])
    return rows, utc_of


def summarize(rd, r, rows, utc_of, wx, utc_source, notes):
    out = []
    groups = {}
    for row in rows:
        groups.setdefault((row[2], row[3], row[4]), []).append(row)
    qc = r["mongo"].get("qc") or {}
    for (block, test, setting), grp in sorted(groups.items(), key=lambda kv: (kv[0][0], float(kv[0][2]), kv[0][1])):
        kept = [x for x in grp if x[7] == "trial"]
        d = [float(x[16]) for x in kept]
        mean = statistics.mean(d)
        sd = statistics.stdev(d) if len(d) > 1 else None
        sig = [float(x[18]) for x in kept if x[18] != ""]
        first, last = utc_of(grp[0][12]), utc_of(grp[-1][12])
        T, H, D = weather_at(wx, first + (last - first) / 2)
        out.append({
            "powder_id": r["run"]["powder_id"], "powder": r["run"].get("powder", ""), "run_id": rd,
            "battery_version": r["version"], "block": block, "test": test,
            "tilt_setting": setting, "tube_angle_deg": f"{float(setting) / 2:.1f}",
            "n_trials": len(kept), "n_discarded_attempts": len(grp) - len(kept),
            "mean_delta_g": g(mean), "sd_delta_g": "" if sd is None else g(sd),
            "rsd_pct": "" if sd is None or mean <= 0 else f"{100 * sd / mean:.1f}",
            "min_delta_g": g(min(d)), "max_delta_g": g(max(d)), "sum_delta_g": g(sum(d)),
            "median_sigma_g": g(statistics.median(sig)) if sig else "",
            "n_quality_ok": sum(x[22] == "ok" for x in kept) if sig else "",
            "n_lowflow": sum(x[23] == "lowflow" for x in kept),
            "first_utc": first.isoformat(timespec="seconds"), "last_utc": last.isoformat(timespec="seconds"),
            "first_local_mdt": first.astimezone(MDT).strftime("%Y-%m-%d %H:%M:%S"),
            "outdoor_temp_c": f"{T:.1f}", "outdoor_rh_pct": f"{H:.1f}", "outdoor_dewpoint_c": f"{D:.1f}",
            "utc_source": utc_source,
            "qc_valid": qc.get("valid_for_cross_powder_comparison", ""), "qc_verdict": qc.get("verdict", ""),
            "operator": r["run"].get("operator", ""), "run_notes": NOTES + notes,
        })
    return out


def check_against_mongo(rd, r):
    m = r["mongo"]
    key = lambda x: (x["block"], round(float(x["tilt_deg"]), 1), x["phase"], int(x["trial"]),
                     int(x["t_ms"]), round(float(x["delta_g"]), 4))
    assert sorted(key(x) for x in m["trials"] if x["block"] in BLOCKS) == \
        sorted(key(x) for x in r["trials"] if x["block"] in BLOCKS), f"{rd}: trials differ from MongoDB"
    rkey = lambda x: (x["block"], int(x["trial"]), int(x["t_ms"]), round(float(x["discarded_delta_g"]), 4))
    assert sorted(rkey(x) for x in (m.get("retries") or []) if x["block"] in BLOCKS) == \
        sorted(rkey(x) for x in r["retries"] if x["block"] in BLOCKS), f"{rd}: retries differ from MongoDB"


def build():
    wx = load_weather()
    runs = load(MAIN, SD / "source")
    runs.update(load(MORE, HERE / "source"))
    offsets, by_version = {}, {}
    for rd, r in runs.items():
        offs = device_offsets(r["run"], r["trials"])
        if offs:
            offsets[rd] = statistics.median(offs)
            by_version.setdefault(r["version"], []).append(offsets[rd])
            print(f"  {rd}: device->UTC offset {offsets[rd]:.2f} s (block anchors "
                  f"{', '.join(f'{o:.2f}' for o in offs)})")
    typical = {v: statistics.median(o) for v, o in by_version.items()}

    (HERE / "runs").mkdir(exist_ok=True)
    for name, run_dirs in (("main", MAIN), ("more", MORE)):
        all_rows, summary = [], []
        for rd, notes in run_dirs.items():
            r = runs[rd]
            check_against_mongo(rd, r)
            off = offsets.get(rd, typical[r["version"]])
            src_note = ("block anchors" if rd in offsets else
                        f"run start + median offset of battery_version {r['version']} runs, "
                        f"{typical[r['version']]:.2f} s (no block times in the record)")
            rows, utc_of = rows_for(r, off, wx)
            for row in rows:
                row[1] = rd
            summary += summarize(rd, r, rows, utc_of, wx, src_note, notes)
            if name == "main":
                with open(HERE / "runs" / f"{r['p']}.csv", "w", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(COLS)
                    w.writerows(rows)
            else:
                qc = r["mongo"].get("qc") or {}
                rows = [row + [r["version"], qc.get("verdict", "")] for row in rows]
            all_rows += rows
        trials_file, summary_file, cols = (
            ("all_trials.csv", "angle_summary.csv", COLS) if name == "main"
            else ("more_powders_trials.csv", "more_powders_summary.csv", MORE_COLS))
        with open(HERE / trials_file, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(all_rows)
        with open(HERE / summary_file, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(summary[0]))
            w.writeheader()
            w.writerows(summary)
        print(f"  {name}: {len(run_dirs)} runs, {len(all_rows)} rows, {len(summary)} summary rows; "
              "trials and retries match MongoDB")


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    build()

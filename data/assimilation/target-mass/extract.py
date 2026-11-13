#!/usr/bin/env python3
"""Doses that ran to a target mass, one or more per powder (issue #210).

Every dose here was told to put a set mass in the cup and stopped on its own when the balance said
it was there (or when it gave up). Three controllers are represented:

* ``pid_single_loop`` (salt, 2026-07-29): one continuous dispense, a PI loop on auger speed
  with flow anticipation; balance read every ~0.1 s. MongoDB ``dose_runs``.
* ``bulk_only`` (Al 4047, 2026-09-30 and 2026-10-20): the trickle_tap firmware's single-stage
  mode, one continuous dispense with a tapering rpm and a slope-predicted halt; balance read every
  ~0.38 s. MongoDB ``opt_trials``.
* ``three_phase`` (every other powder, 2026-08-04 to 2026-09-15): the powder battery's dose
  blocks (G: 1 g, H: 0.05 g then 0.2 g) with bulk, fine and tap stages. Balance polled every
  250 ms in bulk and read once per fine or tap cycle; the console prints whole seconds.

    python3 data/assimilation/target-mass/extract.py --fetch   # recopy source/ and weather/
    python3 data/assimilation/target-mass/extract.py           # rebuild doses/ and the CSVs

--fetch needs ``git fetch origin`` (the pinned commits below must be present), MONGODB_URI
(read-only) and internet access for the weather. The rebuild needs only the standard library.
"""
import csv
import datetime as dt
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "source"
WX = HERE / "weather"
DOSES = HERE / "doses"

# Branch claude/issue-116-20260915-1622, where the battery runs were committed.
BATTERY_COMMIT = "f754450"
# Branch claude/issue-210-20261112-0137 (set C of #210): Al 4047 trial documents, serial logs and
# the tidy telemetry series built from them by extract_new_controller.py.
AL_COMMIT = "9085f9a"
AL_DIR = "data/assimilation/new-controller-powders"
AL_TRIALS = {  # trial_uuid: tidy csv on AL_COMMIT
    "56a01060-e9d2-493a-9ea5-79ef3300605e": "al4047_0p3189g_56a01060.csv",
    "5851b6d6-805c-49cd-919a-e28add9b6d19": "al4047_1p1012g_5851b6d6.csv",
}

# Battery runs with dose blocks. Left out: 20260804T204316Z and 20260804T224937Z brown rice flour
# (auger suspect), 20260805T185305Z brown rice flour (no serial log on any branch), 20260811
# AlSi10Mg (tilt servos failed), 20260903T163527Z/170437Z salt (balance unreadable), 20260908T172730Z
# CMC (outlet misaligned) and 20260901 salt (not on any branch).
BATTERY_RUNS = {  # run dir: run notes under docs/battery-runs/ at BATTERY_COMMIT
    "20260806T145120Z_salt": "2026-08-06-salt.md",
    "20260812T215154Z_salt": "2026-08-12-salt-repeat.md",
    "20260903T214049Z_salt": "2026-09-03-salt-block-h-new-hood.md",
    "20260904T001821Z_salt": "",
    "20260804T211422Z_white-rice-flour": "2026-08-04-white-rice-flour.md",
    "20260904T190011Z_white-rice-flour": "2026-09-04-white-rice-flour-block-h.md",
    "20260806T140254Z_xanthan-gum": "2026-08-06-xanthan-gum.md",
    "20260904T203727Z_xanthan-gum": "2026-09-04-xanthan-gum-block-h.md",
    "20260910T133932Z_sodium-sulfate": "2026-09-10-sodium-sulfate-blocks-gh.md",
    "20260910T194447Z_alsi10mg": "2026-09-10-alsi10mg-blocks-gh.md",
    "20260915T025556Z_silicon-110-200": "2026-09-15-silicon-110-200-gh-attempt5.md",
    "20260805T200002Z_calcium-lactate": "2026-08-05-calcium-lactate.md",
    "20260909T225206Z_calcium-lactate": "2026-09-09-calcium-lactate-block-h.md",
    "20260805T215252Z_carboxymethyl-cellulose": "2026-08-05-carboxymethyl-cellulose.md",
    "20260908T194201Z_carboxymethyl-cellulose": "2026-09-08-carboxymethyl-cellulose-block-h.md",
    "20260805T145725Z_sodium-alginate": "2026-08-05-sodium-alginate.md",
    "20260909T185352Z_sodium-alginate": "2026-09-09-sodium-alginate-block-h.md",
    "20260910T170858Z_barium-chloride": "2026-09-10-barium-chloride-blocks-gh-no-feed.md",
    "20260821T161838Z_silicon-325": "2026-08-21-silicon-325.md",
    "20260910T212920Z_silicon-325": "2026-09-10-silicon-325-blocks-gh.md",
}
BATTERY_FILES = ["raw_serial_{p}.log", "doses_{p}.csv", "run_{p}.json", "timeline_{p}.csv"]

# Salt, single PI loop: the 2026-07-29 dose_runs document (runs run1 and run2); run2 is used.
PID_QUERY = {"doc_type": "pid_dose_telemetry", "started_utc": "2026-07-29T20:52:00Z"}
PID_FILE = "pid_dose_20260729_salt.json"
PID_RUN = "run2"
PID_START_UTC = "2026-07-29T20:52:00+00:00"  # from the document's note; to the minute

# One dose per powder. Salt and Al 4047 get their single-dispense doses; for the rest the rule in
# pick_battery() applies (largest target that finished "ok", then the smallest error).
PICK_OVERRIDE = {"salt": "salt_pid_20260729_run2", "al4047": "al4047_bulkonly_20260930_56a01060"}

WX_FILE = WX / "KPVU_2026-07-29_to_2026-10-20_metar.csv"
WX_URL = ("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=PVU"
          "&data=tmpc&data=dwpc&data=relh&year1=2026&month1=7&day1=29"
          "&year2=2026&month2=10&day2=21&tz=Etc%2FUTC&format=onlycomma&latlon=yes&elev=yes"
          "&missing=empty&trace=empty&direct=no&report_type=3&report_type=4")

COLS = ["powder_id", "dose_id", "controller", "target_g", "t_s", "utc", "phase", "read_type",
        "mass_g", "to_go_g", "stable", "tilt_setting_deg", "auger_rpm_cmd", "taps_cum",
        "actuation", "outdoor_temp_c", "outdoor_rh_pct", "outdoor_dewpoint_c"]


def git_show(commit, path):
    return subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True,
                          check=True).stdout


def mongo():
    import pymongo  # only needed for --fetch
    return pymongo.MongoClient(os.environ["MONGODB_URI"],
                               serverSelectionTimeoutMS=20000)["powder_doser"]


def dump(doc, path):
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    path.write_text(json.dumps(doc, indent=1, default=str) + "\n")


def fetch():
    db = mongo()
    for rd in BATTERY_RUNS:
        p = rd.split("_", 1)[1]
        dst = SRC / "battery" / rd
        dst.mkdir(parents=True, exist_ok=True)
        for pat in BATTERY_FILES:
            name = pat.format(p=p)
            try:
                (dst / name).write_bytes(git_show(BATTERY_COMMIT, f"data/battery/{rd}/{name}"))
            except subprocess.CalledProcessError:
                print(f"  {rd}: no {name} at {BATTERY_COMMIT}")
        run = json.loads((dst / f"run_{p}.json").read_text())
        doc = db.battery_runs.find_one({"powder_id": run["powder_id"],
                                        "started_utc": run["started_utc"]})
        if doc is None:
            print(f"  {rd}: not in battery_runs")
        else:
            dump(doc, dst / "mongodb_battery_runs.json")
    dst = SRC / "al4047"
    dst.mkdir(parents=True, exist_ok=True)
    for uuid, tidy in AL_TRIALS.items():
        for name in (f"trial_{uuid}.json", f"serial_{uuid}.log"):
            (dst / name).write_bytes(git_show(AL_COMMIT, f"{AL_DIR}/source/{name}"))
        (dst / tidy).write_bytes(git_show(AL_COMMIT, f"{AL_DIR}/{tidy}"))
    dst = SRC / "pid"
    dst.mkdir(parents=True, exist_ok=True)
    dump(db.dose_runs.find_one(PID_QUERY), dst / PID_FILE)
    WX.mkdir(exist_ok=True)
    req = urllib.request.Request(WX_URL, headers={"User-Agent": "generic-data-client"})
    WX_FILE.write_bytes(urllib.request.urlopen(req, timeout=120).read())


# --------------------------------------------------------------------------------------------
# Weather and time
# --------------------------------------------------------------------------------------------
def parse_utc(s):
    t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def load_weather():
    rows = []
    with open(WX_FILE) as f:
        for r in csv.DictReader(f):
            if not r["tmpc"] or not r["relh"] or not r["dwpc"]:
                continue
            t = dt.datetime.strptime(r["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
            rows.append((t, float(r["tmpc"]), float(r["relh"]), float(r["dwpc"])))
    rows.sort()
    return rows


def weather_at(wx, t):
    """Linear interpolation between the two reports that bracket t (both within 3 h)."""
    lo, hi = 0, len(wx) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if wx[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    (t0, T0, H0, D0), (t1, T1, H1, D1) = wx[lo], wx[hi]
    if not (t0 <= t <= t1) or (t1 - t0).total_seconds() > 3 * 3600:
        raise ValueError(f"no weather report bracketing {t}")
    w = (t - t0).total_seconds() / (t1 - t0).total_seconds() if t1 > t0 else 0.0
    return T0 + w * (T1 - T0), H0 + w * (H1 - H0), D0 + w * (D1 - D0)


def fmt(x, nd=4):
    return "" if x is None or x == "" else f"{float(x):.{nd}f}"


def utc_str(t):
    return t.isoformat(timespec="milliseconds")


# --------------------------------------------------------------------------------------------
# Battery (three-phase) doses
# --------------------------------------------------------------------------------------------
RX_START = re.compile(r"^\[dose\] three-phase dose to (?P<target>[\d.]+) g")
RX_TARED = re.compile(r"^\[dose\] tared: baseline (?P<base>[+-]?[\d.]+) mg .*drift "
                      r"(?P<drift>[+-]?[\d.]+) mg/min, read noise (?P<noise>[\d.]+) mg")
RX_PHASE = re.compile(r"^=== phase \d/3 '(?P<phase>\w+)' start: .*angle (?P<tilt>-?[\d.]+) "
                      r"plate deg, (?P<act>.*?)(?:, settle \d+ ms)?$")
RX_POLL = re.compile(r"^\[phase 1 bulk\] poll (?P<n>\d+)(?P<unst> \(unstable\))?: mass "
                     r"(?P<m>-?[\d.]+) / .*elapsed (?P<t>[\d.]+) s")
RX_SETTLED = re.compile(r"^\[phase 1 bulk\] settled: mass (?P<m>-?[\d.]+) / .*elapsed "
                        r"(?P<t>[\d.]+) s")
RX_CYCLE = re.compile(r"^\[phase \d (?P<phase>fine|tap)\] cycle (?P<n>\d+)(?P<extra>[^:]*): "
                      r"mass (?P<m>-?[\d.]+) / .*elapsed (?P<t>[\d.]+) s")
RX_DOSE = re.compile(r"^DOSE,(?P<n>\d+),(?P<target>[\d.]+),(?P<disp>-?[\d.]+),(?P<err>-?[\d.]+),"
                     r"(?P<status>[\w-]+),(?P<elapsed>[\d.]+),(?P<rev>[\d.]+),(?P<taps>\d+),"
                     r"(?P<cycles>[^,]*),(?P<t_ms>\d+)(?:,(?P<block>\w+))?")
RX_RPM = re.compile(r"@ (?P<rpm>[\d.]+) (?:auger )?rpm")
RX_TPC = re.compile(r"(?P<taps>\d+) taps/cycle")


def parse_battery_log(path):
    """One dict per dose: header fields and the console's mass readings."""
    doses, cur, tilt, act, rpm, tpc, attended = [], None, "", "", "", 0, None
    unparsed = 0
    with open(path, errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if line.startswith("META,attended,"):
                attended = line.split(",")[2]
            m = RX_START.match(line)
            if m:
                cur = {"target_g": float(m["target"]), "rows": [], "tare": {}}
                tilt, act, rpm, tpc, taps = "", "", "", 0, 0
                continue
            if cur is None:
                continue
            m = RX_TARED.match(line)
            if m:
                cur["tare"] = {"tare_baseline_mg": m["base"], "tare_drift_mg_per_min": m["drift"],
                               "tare_read_noise_mg": m["noise"]}
                continue
            m = RX_PHASE.match(line)
            if m:
                tilt, act = m["tilt"], m["act"].strip()
                r = RX_RPM.search(act)
                rpm = r["rpm"] if r else ""
                t = RX_TPC.search(act)
                tpc = int(t["taps"]) if t else 0
                continue
            m = RX_POLL.match(line)
            if m:
                cur["rows"].append(dict(t_s=m["t"], phase="bulk", read_type="poll",
                                        mass_g=m["m"], stable="0" if m["unst"] else "1",
                                        tilt_setting_deg=tilt, auger_rpm_cmd=rpm, taps_cum=taps,
                                        actuation=act))
                continue
            m = RX_SETTLED.match(line)
            if m:
                cur["rows"].append(dict(t_s=m["t"], phase="bulk_settled", read_type="settled",
                                        mass_g=m["m"], stable="", tilt_setting_deg=tilt,
                                        auger_rpm_cmd="0", taps_cum=taps,
                                        actuation="auger halted, settling"))
                continue
            m = RX_CYCLE.match(line)
            if m:
                taps += tpc
                cur["rows"].append(dict(t_s=m["t"], phase=m["phase"], read_type="settled",
                                        mass_g=m["m"], stable="", tilt_setting_deg=tilt,
                                        auger_rpm_cmd=rpm, taps_cum=taps,
                                        actuation=(act + m["extra"]).strip()))
                continue
            m = RX_DOSE.match(line)
            if m:
                cur.update(dose_n=int(m["n"]), dispensed_g=float(m["disp"]),
                           error_mg=round(float(m["err"]) * 1000, 1), status=m["status"],
                           elapsed_s=float(m["elapsed"]), auger_rev=float(m["rev"]),
                           taps=int(m["taps"]), phase_cycles=m["cycles"],
                           t_ms_end=int(m["t_ms"]), block=m["block"] or "G")
                cur["rows"].append(dict(t_s=m["elapsed"], phase="final", read_type="final",
                                        mass_g=m["disp"], stable="", tilt_setting_deg="",
                                        auger_rpm_cmd="0", taps_cum=int(m["taps"]),
                                        actuation="dose result"))
                doses.append(cur)
                cur = None
                continue
            if " mass " in line and "/" in line:
                unparsed += 1
    return doses, attended, unparsed


def battery_offset(run, doses):
    """Seconds from (run start + device seconds) to UTC, from the host's block start times.

    The host logged when each dose block started. When an earlier dose block ran, the new block
    starts on the device right after its last dose; otherwise its first dose starts at once
    (unattended runs). Returns (offset, list of anchors)."""
    t0 = parse_utc(run["started_utc"])
    anchors = []
    for b in run.get("block_timeline") or []:
        blk = b.get("block")
        if blk not in ("G", "H") or not b.get("started_utc"):
            continue
        host = (parse_utc(b["started_utc"]) - t0).total_seconds()
        prev = [d for d in doses if d["block"] < blk]
        mine = [d for d in doses if d["block"] == blk]
        if prev:
            dev = max(d["t_ms_end"] for d in prev) / 1000
        elif mine:
            dev = min(d["t_ms_end"] / 1000 - d["elapsed_s"] for d in mine)
        else:
            continue
        anchors.append(host - dev)
    good = [a for a in anchors if 0 <= a <= 10]
    return (statistics.median(good) if good else None), anchors


def build_battery(wx):
    out, summaries = [], []
    offsets = {}
    parsed = {}
    for rd in BATTERY_RUNS:
        p = rd.split("_", 1)[1]
        d = SRC / "battery" / rd
        run = json.loads((d / f"run_{p}.json").read_text())
        doses, attended, unparsed = parse_battery_log(d / f"raw_serial_{p}.log")
        with open(d / f"doses_{p}.csv") as f:
            ref = list(csv.DictReader(f))
        got = [(x["dose_n"], round(x["dispensed_g"], 4), x["status"]) for x in doses]
        want = [(int(r["n"]), round(float(r["dispensed_g"]), 4), r["status"]) for r in ref]
        assert got == want, (rd, got, want)
        mdoc = json.loads((d / "mongodb_battery_runs.json").read_text())
        mwant = [(int(x["n"]), round(float(x["dispensed_g"]), 4), x["status"])
                 for x in mdoc["doses"]]
        assert got == mwant, (rd, "mongodb", got, mwant)
        if unparsed:
            print(f"  {rd}: {unparsed} mass lines not parsed")
        off, anchors = battery_offset(run, doses)
        if off is not None:
            offsets[rd] = off
        parsed[rd] = (run, doses, attended, anchors, mdoc)
    fallback = statistics.median(offsets.values())
    for rd, (run, doses, attended, anchors, mdoc) in parsed.items():
        p = rd.split("_", 1)[1]
        off = offsets.get(rd, fallback)
        t0 = parse_utc(run["started_utc"])
        qc = mdoc.get("qc") or {}
        bv = (mdoc.get("parameters") or {}).get("battery_version") or run.get(
            "parameters", {}).get("battery_version", "")
        rep = {}
        for x in doses:
            key = (x["block"], x["target_g"])
            rep[key] = rep.get(key, 0) + 1
            tg = f"{x['target_g']:g}".replace(".", "p")
            dose_id = f"{p}_{rd[:8]}_{x['block']}{x['dose_n']}_{tg}g"
            start = t0 + dt.timedelta(seconds=off + x["t_ms_end"] / 1000 - x["elapsed_s"])
            rows = []
            for r in x["rows"]:
                t = start + dt.timedelta(seconds=float(r["t_s"]))
                T, H, D = weather_at(wx, t)
                rows.append(dict(r, powder_id=p, dose_id=dose_id, controller="three_phase",
                                 target_g=f"{x['target_g']:g}", t_s=f"{float(r['t_s']):.1f}",
                                 utc=utc_str(t),
                                 to_go_g=fmt(x["target_g"] - float(r["mass_g"])),
                                 outdoor_temp_c=f"{T:.1f}", outdoor_rh_pct=f"{H:.1f}",
                                 outdoor_dewpoint_c=f"{D:.1f}"))
            out.append((dose_id, rows))
            T, H, D = weather_at(wx, start)
            reads = [r for r in rows if r["read_type"] != "final"]
            summaries.append({
                "powder_id": p, "dose_id": dose_id, "controller": "three_phase",
                "source": f"battery run {rd}, block {x['block']}, dose {x['dose_n']}",
                "target_g": f"{x['target_g']:g}", "final_g": f"{x['dispensed_g']:.4f}",
                "error_mg": f"{x['error_mg']:.1f}", "status": x["status"],
                "reached_target": int(x["status"] == "ok"),
                "elapsed_s": f"{x['elapsed_s']:.1f}", "auger_rev": f"{x['auger_rev']:.2f}",
                "taps": x["taps"], "stages": x["phase_cycles"].replace(";", " "),
                "n_readings": len(reads),
                "time_resolution": "whole seconds (bulk polls every 0.25 s share a second)",
                "started_utc": utc_str(start),
                "outdoor_temp_c": f"{T:.1f}", "outdoor_rh_pct": f"{H:.1f}",
                "outdoor_dewpoint_c": f"{D:.1f}",
                "run_qc_verdict": qc.get("verdict", ""),
                "run_valid_for_cross_powder": qc.get("valid_for_cross_powder_comparison", ""),
                "battery_version": bv, "attended": attended or "",
                "utc_from": ("block anchors " + ", ".join(f"{a:.2f}" for a in anchors) + " s"
                             if rd in offsets else f"median offset {fallback:.2f} s"),
                "tare_baseline_mg": x["tare"].get("tare_baseline_mg", ""),
                "tare_drift_mg_per_min": x["tare"].get("tare_drift_mg_per_min", ""),
                "tare_read_noise_mg": x["tare"].get("tare_read_noise_mg", ""),
                "notes": (f"https://github.com/vertical-cloud-lab/powder-doser/blob/"
                          f"{BATTERY_COMMIT}/docs/battery-runs/{BATTERY_RUNS[rd]}"
                          if BATTERY_RUNS[rd] else ""),
            })
    return out, summaries


# --------------------------------------------------------------------------------------------
# Salt, single PI loop
# --------------------------------------------------------------------------------------------
def build_pid(wx):
    doc = json.loads((SRC / "pid" / PID_FILE).read_text())
    run = doc["runs"][PID_RUN]
    meta, summ = run["meta"], run["summary"]
    t0 = parse_utc(PID_START_UTC)
    target = float(meta["target_g"])
    dose_id = "salt_pid_20260729_run2"
    rows = []
    ev = {e["event"]: e["t_ms"] for e in run["events"]}
    t_dose = next(v for k, v in ev.items() if k.startswith("dose start"))
    t_tare = next(v for k, v in ev.items() if k.startswith("tare settled"))
    for r in run["telemetry"]:
        t = t0 + dt.timedelta(milliseconds=r["t_ms"])
        T, H, D = weather_at(wx, t)
        rows.append(dict(powder_id="salt", dose_id=dose_id, controller="pid_single_loop",
                         target_g=f"{target:g}", t_s=f"{r['t_ms'] / 1000:.3f}", utc=utc_str(t),
                         phase=r["phase"],
                         read_type="pre_tare" if r["t_ms"] < t_tare else "poll",
                         mass_g=f"{r['mass_g']:.4f}",
                         to_go_g="" if r["t_ms"] < t_tare else fmt(target - r["mass_g"]),
                         stable={"S": "1", "U": "0"}.get(r["frame"], ""),
                         tilt_setting_deg=f"{r['tilt_deg']:g}", auger_rpm_cmd=f"{r['rpm_cmd']:g}",
                         taps_cum=r["taps_cum"], actuation="",
                         outdoor_temp_c=f"{T:.1f}", outdoor_rh_pct=f"{H:.1f}",
                         outdoor_dewpoint_c=f"{D:.1f}"))
    final = float(summ["final_g"])
    t_final = ev["final stable weigh: {:.4f} g".format(final)]
    T, H, D = weather_at(wx, t0)
    summary = {
        "powder_id": "salt", "dose_id": dose_id, "controller": "pid_single_loop",
        "source": f"MongoDB dose_runs {doc['_id']} ({doc['commit']}:{doc['repo_path']}), {PID_RUN}",
        "target_g": f"{target:g}", "final_g": f"{final:.4f}",
        "error_mg": f"{(final - target) * 1000:.1f}", "status": summ["status"],
        "reached_target": int(summ["status"] == "ok"),
        "elapsed_s": f"{t_final / 1000:.1f}", "auger_rev": "",
        "taps": int(summ["taps"]), "stages": "one continuous PI loop",
        "n_readings": len(rows), "time_resolution": "0.1 s (device ms)",
        "started_utc": utc_str(t0),
        "outdoor_temp_c": f"{T:.1f}", "outdoor_rh_pct": f"{H:.1f}",
        "outdoor_dewpoint_c": f"{D:.1f}", "run_qc_verdict": "", "run_valid_for_cross_powder": "",
        "battery_version": "", "attended": "",
        "utc_from": "document note: started 20:52 UTC (to the minute)",
        "tare_baseline_mg": "", "tare_drift_mg_per_min": "", "tare_read_noise_mg": "",
        "notes": "events: " + "; ".join(f"{e['t_ms'] / 1000:.2f} s {e['event']}"
                                        for e in run["events"]),
    }
    return [(dose_id, rows)], [summary]


# --------------------------------------------------------------------------------------------
# Al 4047, bulk_only
# --------------------------------------------------------------------------------------------
def build_al4047(wx):
    out, summaries = [], []
    for uuid, tidy in AL_TRIALS.items():
        doc = json.loads((SRC / "al4047" / f"trial_{uuid}.json").read_text())
        t0 = parse_utc(doc["started_utc"])
        oc = doc["outcomes"]
        target = float(doc.get("target_g") or oc.get("target_g"))
        day = doc["started_utc"][:10].replace("-", "")
        dose_id = f"al4047_bulkonly_{day}_{uuid[:8]}"
        rows = []
        with open(SRC / "al4047" / tidy) as f:
            for r in csv.DictReader(f):
                t = t0 + dt.timedelta(seconds=float(r["t_s"]))
                T, H, D = weather_at(wx, t)
                ph = r["phase"]
                rows.append(dict(powder_id="al4047", dose_id=dose_id, controller="bulk_only",
                                 target_g=f"{target:g}", t_s=r["t_s"], utc=utc_str(t), phase=ph,
                                 read_type={"bulk": "poll", "bulk_end": "settled",
                                            "final_scored": "final"}.get(ph, ph),
                                 mass_g=r["mass_g"], to_go_g=fmt(target - float(r["mass_g"])),
                                 stable="", tilt_setting_deg=r["tilt_deg_cmd"],
                                 auger_rpm_cmd=r["auger_rpm_cmd"], taps_cum="",
                                 actuation=(f"auger + taps {r['tap_mode']}" if ph == "bulk"
                                            else ""),
                                 outdoor_temp_c=f"{T:.1f}", outdoor_rh_pct=f"{H:.1f}",
                                 outdoor_dewpoint_c=f"{D:.1f}"))
        out.append((dose_id, rows))
        T, H, D = weather_at(wx, t0)
        final = float(oc["settled_final_g"])
        status = doc["flags"]["status"]
        summaries.append({
            "powder_id": "al4047", "dose_id": dose_id, "controller": "bulk_only",
            "source": f"MongoDB opt_trials {uuid} (campaign {doc.get('campaign_id', '')})",
            "target_g": f"{target:g}", "final_g": f"{final:.4f}",
            "error_mg": f"{(final - target) * 1000:.1f}", "status": status,
            "reached_target": int(status == "ok"),
            "elapsed_s": fmt(oc["t_total_s"], 1), "auger_rev": fmt(oc["auger_rev"], 2),
            "taps": oc.get("taps", ""), "stages": "bulk_only (one continuous dispense)",
            "n_readings": len([r for r in rows if r["read_type"] != "final"]),
            "time_resolution": "0.28-0.47 s (device ms)",
            "started_utc": utc_str(t0), "outdoor_temp_c": f"{T:.1f}",
            "outdoor_rh_pct": f"{H:.1f}", "outdoor_dewpoint_c": f"{D:.1f}",
            "run_qc_verdict": "", "run_valid_for_cross_powder": "", "battery_version": "",
            "attended": "", "utc_from": "trial document started_utc + t_s",
            "tare_baseline_mg": "", "tare_drift_mg_per_min": "", "tare_read_noise_mg": "",
            "notes": "",
        })
    return out, summaries


# --------------------------------------------------------------------------------------------
def pick(summaries):
    """One dose per powder."""
    by = {}
    for s in summaries:
        by.setdefault(s["powder_id"], []).append(s)
    picks = {}
    for p, ss in by.items():
        if p in PICK_OVERRIDE:
            picks[p] = PICK_OVERRIDE[p]
            continue
        ok = [s for s in ss if s["status"] == "ok"]
        if ok:
            best = min(ok, key=lambda s: (-float(s["target_g"]), abs(float(s["error_mg"]))))
        else:  # none reached the target: the dose that got furthest towards it
            best = max(ss, key=lambda s: float(s["final_g"]) / float(s["target_g"]))
        picks[p] = best["dose_id"]
    return picks


def write(path, rows, cols):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def build():
    wx = load_weather()
    series, summaries = [], []
    for fn in (build_pid, build_al4047, build_battery):
        a, b = fn(wx)
        series += a
        summaries += b
    picks = pick(summaries)
    DOSES.mkdir(exist_ok=True)
    for old in DOSES.glob("*.csv"):
        old.unlink()
    order = {p: i for i, p in enumerate(POWDER_ORDER)}
    summaries.sort(key=lambda s: (order.get(s["powder_id"], 99), s["started_utc"]))
    rank = {s["dose_id"]: i for i, s in enumerate(summaries)}
    series.sort(key=lambda x: rank[x[0]])
    all_rows, pick_rows = [], []
    for dose_id, rows in series:
        write(DOSES / f"{dose_id}.csv", rows, COLS)
        all_rows += rows
        if dose_id in picks.values():
            pick_rows += rows
    for s in summaries:
        s["pick"] = int(picks[s["powder_id"]] == s["dose_id"])
        s["file"] = f"doses/{s['dose_id']}.csv"
    scols = ["powder_id", "pick", "dose_id", "controller", "target_g", "final_g", "error_mg",
             "status", "reached_target", "elapsed_s", "n_readings", "time_resolution",
             "started_utc", "outdoor_temp_c", "outdoor_rh_pct", "outdoor_dewpoint_c", "auger_rev",
             "taps", "stages", "source", "run_qc_verdict", "run_valid_for_cross_powder",
             "battery_version", "attended", "utc_from", "tare_baseline_mg",
             "tare_drift_mg_per_min", "tare_read_noise_mg", "notes", "file"]
    write(HERE / "doses_summary.csv", summaries, scols)
    write(HERE / "all_doses.csv", all_rows, COLS)
    write(HERE / "one_per_powder.csv", pick_rows, COLS)
    print(f"{len(summaries)} doses, {len(all_rows)} rows; one per powder: {len(picks)} doses, "
          f"{len(pick_rows)} rows")
    for s in summaries:
        if s["pick"]:
            print(f"  {s['powder_id']:24s} {s['dose_id']:48s} {s['target_g']:>6s} g -> "
                  f"{s['final_g']} g ({s['error_mg']} mg, {s['status']}), {s['n_readings']} "
                  f"readings, {s['outdoor_temp_c']} C {s['outdoor_rh_pct']} %")


POWDER_ORDER = ["salt", "al4047", "sodium-sulfate", "alsi10mg", "silicon-110-200",
                "white-rice-flour", "xanthan-gum", "calcium-lactate", "carboxymethyl-cellulose",
                "sodium-alginate", "barium-chloride", "silicon-325"]

if __name__ == "__main__":
    os.chdir(HERE)
    if "--fetch" in sys.argv:
        fetch()
    build()

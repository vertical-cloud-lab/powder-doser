#!/usr/bin/env python3
"""Issue #186: put the hand-driven rig sessions into MongoDB ``opt_trials``.

The dose executor (``opt_dose_capture.py``) uploads its own doses.  The
rest of each session -- scale reads, tilt steps, reverse unclog turns, the
stepwise doses and the top-up -- ran through ``rig_cmd.py``,
``unclog_dose.py`` and ``topup.py``, which only wrote raw serial logs.  This
builds one ``opt_trials`` document per session from the committed logs
(``mode`` "manual", the executor's campaign id), writes it to
``zero/manual_trial_<tag>.json`` and upserts it by ``trial_uuid``, the
executor's own upload rule (``opt_common.upload_trial``).  Re-running it
replaces the same five documents; it never touches the executor's.

    python log_manual_to_mongo.py             # build, write, upload, read back
    python log_manual_to_mongo.py --dry-run   # build and write only

The URI comes from $MONGODB_URI or $PI_MONGODB_URI and is never printed.
"""
import argparse
import csv
import datetime
import glob
import hashlib
import io
import json
import os
import re
import subprocess
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ZERO = os.path.join(HERE, "zero")
REPO_DIR = "data/opt/production-al4047-atomizer-cups"
CAMPAIGN_ID = "production-al4047-atomizer-cups"
DB_NAME, COLL_TRIALS = "powder_doser", "opt_trials"
FIRMWARE = "trickle_tap/2026-10-15"
ZERO_CHECKOUT = "306bbee"   # opt_dose_capture.PicoSession, which rig_cmd.py imports
TAPS_PER_T = 3              # the runner's 't': 3 solenoid taps at 60/150 ms
ISSUE = "https://github.com/vertical-cloud-lab/powder-doser/issues/186"

CUP_75 = {
    "label": "7.5 wt% cup",
    "cup_mass_g": 32.5074,
    "cup_mass_note": "as-made (thick-wall) cup weighed without its plug (operator, issue #186 body)",
    "plug_mass_g": 4.995,
    "plug_note": "not weighed; byu-vcl PR #232's computed .508 x .5625 in plug with a #60 vent",
    "target_wt_pct": 7.5,
    "powder_target_g": 3.0407,
    "target_note": "byu-vcl PR #232: powder / (cup + plug + powder) = 7.5 wt% -> 0.075/0.925 x (32.5074 + 4.995) g",
}
CUP_15 = {
    "label": "15 wt% cup",
    "cup_plus_plug_mass_g": 37.2151,
    "cup_mass_note": "new, cleaned as-made cup weighed with its plug (williamulbz, issue #186, 2026-10-20)",
    "target_wt_pct": 15.0,
    "powder_target_g": 6.5674,
    "target_note": "byu-vcl PR #232: powder / (cup + plug + powder) = 15 wt% -> 0.15/0.85 x 37.2151 g",
}
STABLE_READ = "3 consecutive ST reads within 0.3 mg (rig_cmd.read_stable)"

# One entry per session.  The ledgers and hand-added masses are the README's
# accounting; the segments, steps and telemetry below are parsed from the logs.
SESSIONS = [
    {
        "tag": "20261019",
        "log": "serial_readback_20261019.log",
        "outs": [],
        "operator": "claude-for-sgbaird",
        "requested_by": "sgbaird (issue #186 body, 2026-10-19): dose the 7.5 wt% point of byu-vcl PR #232 "
                        "into the weighed 32.5074 g cup, with 0.0103 g already in it",
        "cup": CUP_75,
        "initial_basis": "the operator's tare (cup and funnel on the pan)",
        "activity": "scale reads before and after executor dose a5fdadaa, then the handback to the "
                    "power-on main.py; no auger or plate commands",
        "status": "reads-only",
        "target_g": None,
        "parameters": {"method": "readback in the executor's serial session (5 x 'w' each time)"},
        "scripts": [],
        "hand_added_g": 0.0,
        "hand_added_note": "no auger or plate commands",
        "ledger_after": [
            ["leaked into the cup when the auger was fitted on 10-19 (operator)", 0.0103],
            ["a5fdadaa, stable over its tare (23:30 UTC)", 0.2035],
        ],
        "in_cup_after_g": 0.2138,
        "still_to_dispense_g": 2.8269,
    },
    {
        "tag": "20261020",
        "log": "serial_readback_20261020.log",
        "outs": [],
        "operator": "claude-for-sgbaird",
        "requested_by": "sgbaird (issue #186, 2026-10-20T01:07Z): 'try at higher tilt, fast rotation, and "
                        "frequent tapping all at once'",
        "cup": CUP_75,
        "initial_basis": "a5fdadaa's tare",
        "activity": "guarded tilt steps with the auger stopped (40 -> 60 deg before b13e5997, 60 -> 75 deg "
                    "before f6a3403f; a stable read at each 5 deg step, stop on a 15 mg jump), reads, the "
                    "plate eased back to 0 deg, then the handback",
        "status": "reads-only",
        "target_g": None,
        "parameters": {"method": "rig_cmd.py climb:<from>:<to>:5:0.015 and a<deg>", "stable_read": STABLE_READ},
        "scripts": ["rig_cmd.py"],
        "hand_added_g": 0.0,
        "hand_added_note": "plate moves only; the reading stayed at 0.2028-0.2030 g and then 0.0029 g "
                           "at every step, so nothing fell and the outlet never touched the funnel",
        "ledger_after": [
            ["leaked into the cup when the auger was fitted on 10-19 (operator)", 0.0103],
            ["a5fdadaa, last read over its tare before the next tare (01:18 UTC)", 0.2028],
            ["b13e5997, read over its tare (01:23 UTC)", 0.0029],
            ["f6a3403f, read over its tare (01:26 UTC)", 0.0083],
        ],
        "in_cup_after_g": 0.2243,
        "still_to_dispense_g": 2.8164,
    },
    {
        "tag": "20261020b",
        "log": "serial_readback_20261020b.log",
        "outs": ["dose_rev_20261020b.out"],
        "operator": "claude-for-sgbaird",
        "requested_by": "sgbaird (issue #186, 2026-10-20T02:24Z): 'Sure, try reversing a bunch at 0 tilt. "
                        "You can tap while you're doing that too.'",
        "cup": CUP_75,
        "initial_basis": "f6a3403f's tare (nobody re-zeroed after 10-20 01:26 UTC)",
        "activity": "reverse half turns with a 't' after each at 0 deg until the outlet freed (after "
                    "12.75 reverse turns), an A/B test of direction and taps at 0 deg, then a stepwise "
                    "reverse dose to a reading of 2.8247 g",
        "status": "overshoot",
        "status_note": "the last step (24.9 deg, 26.5 mg to go) added 28.8 mg: 2.3 mg over the 2.8247 g "
                       "reading target, 2.5 mg at the final stable read",
        "target_g": 2.8247,
        "target_basis": "f6a3403f",
        "target_note": "balance reading over f6a3403f's tare: 3.0407 - 0.0103 - 0.2028 - 0.0029 g",
        "parameters": {
            "method": "rig_cmd.py rot<deg> / tap<n> / dose:<g>:<tol>",
            "plate_deg": 0.0,
            "runner_rpm": 60.0,
            "unclog": "r -180 then one 't' (3 taps), repeated",
            "ab_test": "4 x 't' alone; 4 x (r +180, 't'); 6 x (r -180, 't'); 4 x r +180; 6 x r -180",
            "dose": "dose:2.8247:0.002 -- r -180 while over 150 mg remained, then steps of "
                    "max(5, min(90, 0.5 x remaining / steepest g per deg so far)) deg reverse; a 't' "
                    "after any step adding under 2 mg",
            "tolerance_g": 0.002,
            "stable_read": STABLE_READ,
        },
        "scripts": ["rig_cmd.py"],
        "hand_added_g": 2.8192,
        "hand_added_note": "2.8272 g (stable, 02:49 UTC) - 0.0080 g (stable at takeover, 02:33 UTC), both "
                           "over f6a3403f's tare",
        "ledger_after": [
            ["leaked into the cup when the auger was fitted on 10-19 (operator)", 0.0103],
            ["a5fdadaa, over its tare", 0.2028],
            ["b13e5997, over its tare", 0.0029],
            ["f6a3403f plus this session, over f6a3403f's tare (stable, 02:49 UTC)", 2.8272],
        ],
        "in_cup_after_g": 3.0432,
        "still_to_dispense_g": 0.0,
        "result_note": "3.0432 g vs the 3.0407 g target (+2.5 mg): 7.5056 wt% with the 4.995 g plug estimate",
    },
    {
        "tag": "20261020c",
        "log": "serial_readback_20261020c.log",
        "outs": ["unclog_dose_20261020c.out"],
        "operator": "claude-for-williamulbz",
        "requested_by": "williamulbz (issue #186, 2026-10-20T21:01Z): dose the 15 wt% point into a new "
                        "cup (cup + plug 37.2151 g), following the 10-20 protocol in the event of clogs",
        "cup": CUP_15,
        "initial_basis": "the operator's zero (new, empty cup and funnel on the pan)",
        "activity": "after cb3096e9 stalled: the plate eased 40 -> 0 deg, 10 reverse half turns with a "
                    "'t' after each, unclog_dose.py's 99 reverse steps at 0 deg, forward half turns and "
                    "rocking at 0 deg, a guarded climb to 30 deg and back to 25 deg, and 4 forward turns at "
                    "25 deg; reads around d737cec5 and 9480b818; the plate eased to 0 deg and the handback",
        "status": "stopped",
        "status_note": "unclog_dose.py was stopped by hand after 99 steps: the flow never freed (2-4 mg "
                       "per half turn), unlike 10-20b",
        "target_g": 6.5674,
        "target_basis": "cb3096e9",
        "target_note": "unclog_dose.py's reading target over cb3096e9's tare (the cup was empty)",
        "parameters": {
            "method": "rig_cmd.py a<deg> / rot<deg> / tap<n> / climb:5:60:5:0.004, unclog_dose.py 6.5674 0.002",
            "plate_deg": [0.0, 25.0],
            "runner_rpm": 60.0,
            "unclog_dose": "reverse half turns (full turns once flowing, never reached) with a stable read "
                           "after each and a 't' after any step adding under 2 mg; 60-step no-flow budget",
            "rocking": "8 x (r +180, r -180, 't') at 0 deg",
            "tilt_test": "climb from 5 deg in 5 deg steps, stop on a 4 mg jump (it did at 30 deg), back to "
                         "25 deg; then r +360 x 4 with a 't' after each two",
            "tolerance_g": 0.002,
            "stable_read": STABLE_READ,
        },
        "scripts": ["rig_cmd.py", "unclog_dose.py"],
        "hand_added_g": 0.4302,
        "hand_added_note": "2.6723 g (stable, 21:29:58 UTC, after the 25 deg turns) - 2.2421 g (cb3096e9's "
                           "settled final), both over cb3096e9's tare; includes what fell while the plate "
                           "was eased 40 -> 0 deg",
        "ledger_after": [
            ["cb3096e9, then this session's 0 and 25 deg steps, over cb3096e9's tare (stable, 21:29:58)", 2.6723],
            ["d737cec5, over its tare (stable, 21:36:30)", 2.2496],
            ["9480b818, over its tare (stable, 21:40:55)", 0.3901],
        ],
        "in_cup_after_g": 5.3120,
        "still_to_dispense_g": 1.2554,
        "result_note": "12.49 wt%: 5.3120 / (37.2151 + 5.3120)",
    },
    {
        "tag": "20261020d",
        "log": "serial_readback_20261020d.log",
        "outs": ["topup_20261020d.out"],
        "operator": "claude-for-williamulbz",
        "requested_by": "williamulbz (issue #186, 2026-10-20T22:08Z): 'I have cleared the auger of large "
                        "particles. Continue the dose. the combined mass of the cup + the plug + the "
                        "powder inside = 42.5053g.'",
        "cup": dict(CUP_15, cup_plug_powder_weighed_g=42.5053,
                    weighed_powder_g=5.2902,
                    weighed_note="42.5053 - 37.2151 g, weighed by the operator before this session"),
        "initial_basis": "the operator's zero (re-zeroed after the 20261020c session)",
        "activity": "reads before 5851b6d6 (stable 0.0760 then 0.0765 g over the operator's zero), "
                    "topup.py's 22 forward steps at 40 deg after 5851b6d6, the plate eased 40 -> 0 deg, "
                    "reads at 0 deg, then the handback",
        "status": "ok",
        "status_note": "topup.py: 'DOSE done 1.1996 g (-1.1 mg vs 1.2007 g)'; 1.2014 g 30 s later at "
                       "40 deg (creep), 1.2009 g at 0 deg",
        "target_g": 1.2007,
        "target_basis": "5851b6d6",
        "target_note": "topup.py's reading target over 5851b6d6's tare: 6.5674 - 5.2902 - 0.0765 g",
        "parameters": {
            "method": "topup.py 1.2007 0.002 (forward), rig_cmd.py a<deg> / wait<s> / wst",
            "plate_deg": 40.0,
            "runner_rpm": 60.0,
            "topup": "forward steps of max(20, min(max_deg, 0.5 x remaining / steepest g per deg so far)) "
                     "deg, seeded at 13 mg per 360 deg, a stable read after each",
            "tolerance_g": 0.002,
            "stable_read": STABLE_READ,
        },
        "scripts": ["rig_cmd.py", "topup.py"],
        "hand_added_g": 0.0981,
        "hand_added_note": "1.2009 g (stable at 0 deg, 22:21:36 UTC) - 1.1028 g (5851b6d6's settled "
                           "final), both over 5851b6d6's tare; the steps themselves read 1.1023 -> 1.1996 g",
        "ledger_after": [
            ["weighed by the operator: 42.5053 - 37.2151", 5.2902],
            ["on the balance before 5851b6d6, over the operator's zero (stable, 22:15:22)", 0.0765],
            ["5851b6d6 and the top-up, over 5851b6d6's tare (stable, 22:21:36)", 1.2009],
        ],
        "in_cup_after_g": 6.5676,
        "still_to_dispense_g": 0.0,
        "result_note": "15.000 wt%: 6.5676 / (37.2151 + 6.5676); counts the 0.0765 g read before the dose "
                       "as powder in the cup (the operator's final weighing, 43.7827 g expected, checks it)",
    },
]

MARK_RE = re.compile(r"^--- (session|readback|handback) (\S+) ---$")
INVOKE_RE = re.compile(r"^--- (rig_cmd|unclog_dose|topup) (.*) ---$")
SCALE_RE = re.compile(r"^\[scale\] (\S+) (-?[\d.]+) g$")
SENT_RE = re.compile(r"^>> (.+)$")
STEP_RE = re.compile(r"^DOSE step (\d+) ([+-][\d.]+) deg: ([\d.]+) -> ([\d.]+) g "
                     r"\(([+-][\d.]+) mg\)(?: (\d\d:\d\d:\d\d))?$")
MOTION_RE = re.compile(r"^(r|a) (-?[\d.]+)$")


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", HERE] + list(args), text=True).strip()


def record_commit(name):
    """The commit that added a file under zero/ (the session's record)."""
    return git("log", "--diff-filter=A", "--format=%H", "--", os.path.join(ZERO, name)).splitlines()[-1]


def executor_starts():
    out = []
    for path in sorted(glob.glob(os.path.join(ZERO, "trial_*.json"))):
        doc = json.load(open(path))
        out.append((doc["started_utc"], doc["trial_uuid"]))
    return sorted(out)


def csv_row(values):
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow(values)
    return buf.getvalue()


def parse_log(path, initial_basis, starts):
    """Telemetry rows and per-invocation segments from a raw serial log."""
    rows, segments = [], []
    session_utc, first_utc, last_utc, seg, seq = None, None, None, None, 0
    for line in open(path, encoding="utf-8", errors="replace").read().splitlines():
        m = MARK_RE.match(line)
        if m:
            session_utc = last_utc = m.group(2)
            first_utc = first_utc or session_utc
            if m.group(1) != "session":
                seg = new_segment(segments, session_utc, m.group(1), first_utc, initial_basis, starts)
            rows.append(csv_row([seq, session_utc, m.group(1), "", "", ""]))
            seq += 1
            continue
        m = INVOKE_RE.match(line)
        if m:
            seg = new_segment(segments, session_utc, "{} {}".format(*m.groups()), first_utc,
                              initial_basis, starts)
            rows.append(csv_row([seq, session_utc, "invoke", "{} {}".format(*m.groups()), "", ""]))
            seq += 1
            continue
        m = SENT_RE.match(line)
        if m:
            cmd = m.group(1).strip()
            rows.append(csv_row([seq, session_utc, "cmd", cmd, "", ""]))
            seq += 1
            if seg is not None:
                mm = MOTION_RE.match(cmd)
                if mm and mm.group(1) == "r":
                    deg = float(mm.group(2))
                    seg["auger_deg_fwd" if deg > 0 else "auger_deg_rev"] += abs(deg)
                    seg["r_cmds"] += 1
                elif mm and mm.group(1) == "a":
                    ang = float(mm.group(2))
                    if ang not in seg["plate_deg"]:
                        seg["plate_deg"].append(ang)
                elif cmd == "t":
                    seg["t_cmds"] += 1
            continue
        m = SCALE_RE.match(line)
        if m:
            flag, g = m.group(1), float(m.group(2))
            rows.append(csv_row([seq, session_utc, "scale", "", flag, g]))
            seq += 1
            if seg is not None:
                seg["n_reads"] += 1
                if flag == "ST":
                    if seg["first_st_g"] is None:
                        seg["first_st_g"] = g
                    seg["last_st_g"] = g
    for s in segments:
        s["taps"] = s["t_cmds"] * TAPS_PER_T
        s["auger_turns_fwd"] = round(s["auger_deg_fwd"] / 360.0, 3)
        s["auger_turns_rev"] = round(s["auger_deg_rev"] / 360.0, 3)
    return rows, segments, first_utc, last_utc


def new_segment(segments, utc, invocation, first_utc, initial_basis, starts):
    basis = initial_basis
    for started, trial_uuid in starts:
        if first_utc <= started <= utc:
            basis = "{}'s tare".format(trial_uuid[:8])
    seg = {"utc": utc, "invocation": invocation, "tare_basis": basis, "n_reads": 0,
           "first_st_g": None, "last_st_g": None, "r_cmds": 0, "auger_deg_fwd": 0.0,
           "auger_deg_rev": 0.0, "t_cmds": 0, "plate_deg": []}
    segments.append(seg)
    return seg


def parse_steps(path, date):
    steps = []
    for line in open(path, encoding="utf-8").read().splitlines():
        m = STEP_RE.match(line)
        if m:
            n, deg, g0, g1, mg, hms = m.groups()
            steps.append({"step": int(n), "auger_deg": float(deg), "g_before": float(g0),
                          "g_after": float(g1), "added_mg": float(mg),
                          "utc": "{}T{}+00:00".format(date, hms) if hms else None})
    return steps


def iso_seconds(a, b):
    fa = datetime.datetime.fromisoformat(a)
    fb = datetime.datetime.fromisoformat(b)
    return round((fb - fa).total_seconds(), 1)


def raw_entry(name):
    path = os.path.join(ZERO, name)
    text = open(path, encoding="utf-8", errors="replace").read()
    return {"name": name, "path": "{}/zero/{}".format(REPO_DIR, name), "sha256": sha256(path),
            "bytes": os.path.getsize(path), "commit": record_commit(name), "text": text}


def build(meta, starts):
    log_path = os.path.join(ZERO, meta["log"])
    rows, segments, first_utc, last_utc = parse_log(log_path, meta["initial_basis"], starts)
    date = first_utc[:10]
    steps = []
    for name in meta["outs"]:
        for s in parse_steps(os.path.join(ZERO, name), date):
            steps.append(dict(s, source=name))
    commit = record_commit(meta["log"])
    totals = {k: sum(s[k] for s in segments) for k in ("r_cmds", "auger_deg_fwd", "auger_deg_rev", "t_cmds")}
    plates = sorted({a for s in segments for a in s["plate_deg"]})
    # The final reading on the dose target's tare basis (the last read of the
    # session for sessions without a target).
    basis = meta.get("target_basis", "")
    final_reads = [s["last_st_g"] for s in segments
                   if s["last_st_g"] is not None and s["tare_basis"].startswith(basis)]
    settled = final_reads[-1] if final_reads else None
    target = meta["target_g"]
    error_mg = round((settled - target) * 1e3, 1) if (target is not None and settled is not None) else None
    tol_mg = meta["parameters"].get("tolerance_g", 0.0) * 1e3
    trial_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, "{}#manual-{}".format(ISSUE, meta["tag"])))
    related = [u for t, u in starts
               if first_utc <= t <= last_utc or u[:8] in meta["initial_basis"]]
    doc = {
        "kind": "opt_trial",
        "schema_version": 1,
        "campaign_id": CAMPAIGN_ID,
        "trial_uuid": trial_uuid,
        "trial_index": -1,
        "powder_id": "al4047",
        "target_g": target,
        "mode": "manual",
        "started_utc": first_utc,
        "ended_utc": last_utc,
        "operator": meta["operator"],
        "git_commit": git("rev-parse", commit),
        "parameters": meta["parameters"],
        "parameters_executed": {"invocations": [s["invocation"] for s in segments]},
        "outcomes": {
            "t_total_s": iso_seconds(first_utc, last_utc),
            "settled_final_g": settled,
            "error_mg": error_mg,
            "abs_error_mg": abs(error_mg) if error_mg is not None else None,
            "overshoot": bool(error_mg is not None and error_mg > tol_mg),
            "taps": totals["t_cmds"] * TAPS_PER_T,
            "t_cmds": totals["t_cmds"],
            "r_cmds": totals["r_cmds"],
            "auger_rev_fwd": round(totals["auger_deg_fwd"] / 360.0, 3),
            "auger_rev_rev": round(totals["auger_deg_rev"] / 360.0, 3),
            "plate_deg": plates,
            "hand_added_g": meta["hand_added_g"],
            "hand_added_note": meta["hand_added_note"],
            "steps": len(steps),
        },
        "stop_events": [],
        "flags": {
            "status": meta["status"],
            "status_note": meta.get("status_note"),
            "jam": False,
            "jam_reason": None,
            "infra_error": False,
            "spill": None,
            "aborted": meta["status"] == "stopped",
        },
        "covariates": {
            "requested_by": meta["requested_by"],
            "purpose": "byu-vcl atomizer composition spread (byu-vcl PR #232): Al 4047 powder in as-made "
                       "6063 cups",
            "activity": meta["activity"],
            "cup": meta["cup"],
            "funnel": "a funnel in the cup mouth under the auger outlet; the balance counts powder on it",
            "target_note": meta.get("target_note"),
            "initial_tare_basis": meta["initial_basis"],
            "related_trials": related,
            "cup_ledger_after": [{"item": k, "g": round(v, 4)} for k, v in meta["ledger_after"]],
            "in_cup_after_g": meta["in_cup_after_g"],
            "still_to_dispense_g": meta["still_to_dispense_g"],
            "result_note": meta.get("result_note"),
            "zero_checkout": ZERO_CHECKOUT,
        },
        "device": {
            "log_path": "{}/zero/{}".format(REPO_DIR, meta["log"]),
            "firmware": FIRMWARE,
            "runner": "/trickle_tap main_trickle.main() (manual runner), driven over USB serial by the Zero",
        },
        "manual": {
            "why": "hand-driven steps outside opt_dose_capture.py, which uploads only its own doses; "
                   "added 2026-10-21 after sgbaird asked in issue #186 that everything go to MongoDB",
            "issue": ISSUE,
            "scripts": [{"path": "{}/{}".format(REPO_DIR, s), "commit": git("log", "-1", "--format=%H", commit,
                                                                            "--", os.path.join(HERE, s))}
                        for s in meta["scripts"]],
            "segments": segments,
            "steps": steps,
            "raw_logs": [raw_entry(meta["log"])] + [raw_entry(n) for n in meta["outs"]],
            "uploaded_by": "log_manual_to_mongo.py",
            "uploaded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "telemetry": {
            "header": "seq,session_utc,kind,cmd,flag,g",
            "rows": rows,
        },
    }
    return doc


def resolve_uri():
    for name in ("MONGODB_URI", "PI_MONGODB_URI"):
        if os.environ.get(name):
            return os.environ[name], name
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    starts = executor_starts()
    docs = [build(meta, starts) for meta in SESSIONS]
    for meta, doc in zip(SESSIONS, docs):
        path = os.path.join(ZERO, "manual_trial_{}.json".format(meta["tag"]))
        with open(path, "w") as fh:
            json.dump(doc, fh, indent=1)
            fh.write("\n")
        o = doc["outcomes"]
        print("{} {} {:<10} final {} g, error {} mg, {} r ({} fwd / {} rev turns), {} t, plates {}, "
              "{} steps, {} telemetry rows".format(
                  meta["tag"], doc["trial_uuid"][:8], doc["flags"]["status"], o["settled_final_g"],
                  o["error_mg"], o["r_cmds"], o["auger_rev_fwd"], o["auger_rev_rev"], o["t_cmds"],
                  o["plate_deg"], o["steps"], len(doc["telemetry"]["rows"])))
    if args.dry_run:
        return 0
    uri, source = resolve_uri()
    if not uri:
        print("no MongoDB URI ($MONGODB_URI, $PI_MONGODB_URI)")
        return 2
    import pymongo
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=15000)
    coll = client[DB_NAME][COLL_TRIALS]
    for doc in docs:
        coll.replace_one({"trial_uuid": doc["trial_uuid"]}, doc, upsert=True)
    print("upserted {} documents into {}.{} (URI from ${})".format(len(docs), DB_NAME, COLL_TRIALS, source))
    for doc in docs:
        got = coll.find_one({"trial_uuid": doc["trial_uuid"]}, {"_id": 0, "manual.raw_logs.sha256": 1,
                                                                "telemetry.rows": 1, "mode": 1})
        ok = (got is not None and got["mode"] == "manual"
              and [r["sha256"] for r in got["manual"]["raw_logs"]]
              == [r["sha256"] for r in doc["manual"]["raw_logs"]]
              and len(got["telemetry"]["rows"]) == len(doc["telemetry"]["rows"]))
        print("read back {}: {}".format(doc["trial_uuid"][:8], "ok" if ok else "MISMATCH"))
    n = coll.count_documents({"campaign_id": CAMPAIGN_ID})
    n_manual = coll.count_documents({"campaign_id": CAMPAIGN_ID, "mode": "manual"})
    print("{} now holds {} documents for {} ({} manual)".format(COLL_TRIALS, n, CAMPAIGN_ID, n_manual))
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

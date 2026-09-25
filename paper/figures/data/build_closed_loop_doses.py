#!/usr/bin/env python3
"""Tidy closed-loop dose tables for the issue #116 powder battery, rounds 1 + 2.

Everything is read straight out of git (``git show REF:path``), so the local
working tree is never touched.  The default REF is the newest #116 branch,
``origin/claude/issue-116-20260915-1622``: it carries all 37 run directories
under ``data/battery/`` (the union over every ``claude/issue-116-*`` branch) and
the newest version of every file in them (checked 2026-09-25).

Outputs (in --out, default the directory of this script):

  runs_all.csv                           one row per run directory, both rounds
  doses_all.csv                          one row per closed-loop dose attempt
                                         (protocol G = 1 g, H = 50/200 mg, demos)
  dose_summary_by_powder_target.csv      valid doses, per powder x target
  dose_summary_by_powder_target_round.csv  same, split by round
  round2_inventory.csv                   every round-2 session incl. stand-downs
                                         that produced no run document
  raw/<run_dir>/...                      (--copy-raw) verbatim copies of every
                                         round-2 run directory

Conventions (read these before using the numbers)
-------------------------------------------------
* error_mg = delivered - target, from the firmware DOSE row (0.1 mg resolution);
  error_pct = 100 * error_mg / target_mg.
* time_s = DOSE-row elapsed_s (MicroPython integer-second clock, 1 s resolution).
* pass_5pct       |error| <= 5 % of target (2.5 mg @ 50, 10 mg @ 200, 50 mg @ 1 g).
  pass_fw_status  firmware terminated 'ok' (inside its +/-5 mg tolerance t3).
  pass_fw_abs5    |error| <= 5.0 mg, recomputed from the recorded error.
* auger_rev_fw is what the firmware logged: commanded AUGER revolutions of
  ``main_three_phase.Stepper``, which folds AUGER_GEAR_RATIO = 44/20 = 2.2 into
  steps_per_rev (3520 microsteps per "revolution").  stepper_rev = 2.2 x that.
  auger_rev_if_48_16 = stepper_rev / 3.0, i.e. true auger turns IF the as-built
  gear is the 48:16 pair in cad/auger-geared/ (unresolved: the rig builder
  stated 44:20 on PR #124).  The same unit applies to every pre-flight mg/rev.
* read_path: 'read_stable' (doser waits for an ST frame; all round-1 Block G and
  the two 2026-09-03 morning runs) vs 'bracket' (balance_filter brackets, from
  2026-09-03 21:40Z on).  Numbers either side are not the same measurement method.
* dose_valid (strict) = run QC valid AND terminal control state (not
  scale-error / not-tared) AND the dose actuated something (auger_rev > 0 or
  taps > 0) AND not a demo.  The zero-actuation rule follows the capture
  script's own statistics (n_no_actuation); the #116 sessions applied it
  inconsistently (Si 110/200 H2 excluded in QC, calcium lactate H2 kept in
  prose), so ``actuated`` is exported for re-analysis.
* location: lab_pre_hood (< 2026-08-11 18:12Z), shared_fume_hood (polishing-lab
  hood; moved in 08-11, moved "back into the fume hood" 08-19; students' compressed
  air / sink use), new_fume_hood (relocated 2026-09-03 before 20:38Z).

Usage::

    python build_round2.py [--repo PATH] [--ref REF] [--out DIR] [--copy-raw]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO = "/home/runner/work/powder-doser/powder-doser"
DEFAULT_REF = "origin/claude/issue-116-20260915-1622"

FW_GEAR = 44.0 / 20.0      # folded into main_three_phase.Stepper.steps_per_rev
CAD_GEAR = 48.0 / 16.0     # cad/auger-geared/stepper-pinion.scad + auger-core.scad
FW_TOL_MG = 5.0            # DOSE_THRESHOLDS t3 = 0.005 g

DISPLAY = {
    "alsi10mg": "AlSi10Mg", "silicon-110-200": "Si (-110/+200 mesh)",
    "silicon-325": "Si (-325 mesh)", "sodium-sulfate": "Sodium sulfate",
    "barium-chloride": "Barium chloride", "fumed-silica": "Fumed silica",
    "salt": "NaCl (control)", "salt-demo": "NaCl (control)",
    "calcium-lactate": "Calcium lactate", "sodium-alginate": "Sodium alginate",
    "xanthan-gum": "Xanthan gum", "carboxymethyl-cellulose": "CMC",
    "white-rice-flour": "White rice flour", "brown-rice-flour": "Brown rice flour",
}

# Round-2 provenance: #116 comment ids (issuecomment-<id>) and the commit that
# first committed each run directory, cross-checked against `git log`.
R2_PROVENANCE = {
    "20260903T163527Z_salt": ("5528661410", "claude/issue-116-20260903-1617@b7d38a1"),
    "20260903T170437Z_salt": ("5529102139;5529245844",
                              "claude/issue-116-20260903-1704@3d48d2c (QC amended bf18aa1); in parallel 20260903-1652@00ce372"),
    "20260903T214049Z_salt": ("5531825264;5544565454",
                              "claude/issue-116-blockh-recovered@81bbe75; 20260904-1805@0604674"),
    "20260904T001821Z_salt": ("#148 2026-09-04T00:13Z;5544565454",
                              "claude/issue-116-20260904-1805@0604674"),
    "20260904T190011Z_white-rice-flour": ("5544943576;5545827194;5545930757",
                                          "claude/issue-116-20260904-2013@f3a34de"),
    "20260904T203727Z_xanthan-gum": ("5545930757", "claude/issue-116-20260904-2013@e50a70f"),
    "20260908T172730Z_carboxymethyl-cellulose": ("5588686080;5590598698",
                                                 "claude/issue-116-20260908-1924@8ffc72e"),
    "20260908T194201Z_carboxymethyl-cellulose": ("5590598698;5592079984",
                                                 "claude/issue-116-20260908-2125@fb39d5d"),
    "20260909T185352Z_sodium-alginate": ("5606851396;5609012161",
                                         "claude/issue-116-20260909-2129@2ef5775 (tip 2668e55)"),
    "20260909T225206Z_calcium-lactate": ("5609012161", "claude/issue-116-20260909-2129@2668e55"),
    "20260910T133932Z_sodium-sulfate": ("5619383507", "claude/issue-116-20260910-1323@927fb87"),
    "20260910T170858Z_barium-chloride": ("5622273948", "claude/issue-116-20260910-1650@642c35a"),
    "20260910T194447Z_alsi10mg": ("5623309132;5624320823;5625025031",
                                  "claude/issue-116-20260910-1813@60b5a38"),
    "20260910T212920Z_silicon-325": ("5625482642", "claude/issue-116-20260910-2110@d256752"),
    "20260910T231950Z_silicon-110-200_preflight": ("5626124921",
                                                   "claude/issue-116-20260910-2211@b37b3d9"),
    "20260915T025556Z_silicon-110-200": ("5673425201;5673671255",
                                         "claude/issue-116-20260915-0219@356d45b+105f0eb"),
    "20260915T164228Z_salt-demo": ("5683919348", "claude/issue-116-20260915-1622@2522858"),
}

# Run-level caveats that are true of the data but live only in comments/notes.
RUN_CAVEATS = {
    "20260903T163527Z_salt": "shared hood; read_stable doser read path: balance 0-2 % ST frames once rig actuated; refused tare -> phantom 7.5393 g",
    "20260903T170437Z_salt": "shared hood; student using fume-hood compressed air; 0.00 auger rev on all six doses; dose 5 '1.541 g' = pre-flight salt left in cup",
    "20260903T214049Z_salt": "first new-hood run; first bracket read path; drift -3.6/-1.8/+2.6 mg/min (2.8-3.8 mg over a 17-64 s dose)",
    "20260904T001821Z_salt": "issue #148 1 g demo by sgbaird, skip-checks; QC left 'unreviewed', valid=false",
    "20260904T190011Z_white-rice-flour": "quietest pre-run survey (0.015 mg jitter, 98 % stable); every error parked at the -5 mg band edge",
    "20260904T203727Z_xanthan-gum": "pre-run drift -4.5 mg/min (tares -6.2 to -8.7); bidirectional intra-dose swings of tens of mg, suspected triboelectric charging",
    "20260908T172730Z_carboxymethyl-cellulose": "outlet misaligned with enclosure hole (#156): stream piled behind the hole, balance saw a fraction",
    "20260908T194201Z_carboxymethyl-cellulose": "200 mg triple feed-limited (low/caked auger after misaligned run; 20.2 -> 10.7 mg/rev); pre-run drift -11.4 mg/min (#157)",
    "20260909T185352Z_sodium-alginate": "launched detached; ~4.5 mg/rev conveyor, all doses stalled/timed out; H5 stalled at 14.3 mg (column depletion)",
    "20260909T225206Z_calcium-lactate": "launch held ~50 min for drift (-9.7 -> ~-2 mg/min); every tare 'did not take' and was subtracted; USB serial corrupted during H5 (row reconstructed from notes)",
    "20260910T133932Z_sodium-sulfate": "pre-roll drift -1.6 mg/min (worst dose bias <= 4.7 mg, sign known); device counters clean",
    "20260910T170858Z_barium-chloride": "caked hygroscopic BaCl2 arched over the intake after ~3 weeks loaded; G0 drained the flights (0.345 g), rest stalled",
    "20260910T194447Z_alsi10mg": "Pi off tailnet 11:37-12:30 MDT; launch held ~70 min for drift after BaCl2 cleanup; run clean (0 shocks)",
    "20260910T212920Z_silicon-325": "cohesive powder, agitation-immune; 18.0 auger rev over 9 doses moved 1.6 mg; valid 'cannot dose' measurement",
    "20260910T231950Z_silicon-110-200_preflight": "stand-down #1 at the dose gate (+/-10-30 mg, ~10 min oscillation); pre-flight only",
    "20260915T025556Z_silicon-110-200": "attempt #5, evening empty lab, gate passed on window 2; H2 excluded in QC (0 rev, 0 taps: afterflow)",
    "20260915T164228Z_salt-demo": "0.5 g demo; gate not passed (+2.9 mg/min drift), kept out of battery_runs (batch demo)",
}

# Doses that exist only in comments (artifacts never committed to git).
COMMENT_ONLY_DOSES = [
    # issue #148 demo, 2026-09-01, shared fume hood, read_stable path, Pi-only artifacts
    dict(run_id="20260901T164658Z_salt(#148)", round="2-pre", source="issue #148 comment 2026-09-01T16:37Z (artifacts Pi-only; Mongo 6a97025021119262684581ca)",
         started_utc="2026-09-01T16:46:58Z", powder_id="salt", protocol="demo", block="G", n=0,
         target_g=2.0, dispensed_g=-0.0389, status="stalled", elapsed_s=8.0, auger_rev=4.58, taps=0,
         phase_cycles="bulk:16", read_path="read_stable", location="shared_fume_hood",
         run_qc_valid=False, run_qc_verdict="demo (balance off / no feed)",
         note="balance had been switched off; stalled with zero mass gain"),
    dict(run_id="20260901T165026Z_salt(#148)", round="2-pre", source="issue #148 comment 2026-09-01T16:47Z (artifacts Pi-only; Mongo 6a970324467c700d5bcfcd51)",
         started_utc="2026-09-01T16:50:26Z", powder_id="salt", protocol="demo", block="G", n=0,
         target_g=2.0, dispensed_g=1.9963, status="ok", elapsed_s=167.0, auger_rev=9.75, taps=48,
         phase_cycles="bulk:31;fine:12;tap:24", read_path="read_stable", location="shared_fume_hood",
         run_qc_valid=False, run_qc_verdict="demo",
         note="2 g demo; bulk exit 1.5639 g, fine exit 1.9566 g"),
]

# Dose whose DOSE row was lost to USB serial corruption (run note
# docs/battery-runs/2026-09-09-calcium-lactate-block-h.md, #116 5609012161).
RECONSTRUCTED_DOSES = [
    dict(run_id="20260909T225206Z_calcium-lactate", block="H", n=5, target_g=0.2,
         dispensed_g=0.1645, status="stalled", elapsed_s=None, auger_rev=None, taps=None,
         phase_cycles="", note="RECONSTRUCTED: DOSE row lost (USB serial corruption 23:18Z after nudge 10/10); "
         "delivered ~164.5 mg triangulated from trace (170.1 mg @ tap cycle 144), camera (163.5 mg) and "
         "300 s post-run capture (164.9->164.5 mg); time ~560-900 s; taps ~150"),
]

# Every round-2 session on #116 (2026-09-03 .. 09-15), including attempts that
# never produced a run document.  Hand-curated from the comment bodies.
ROUND2_SESSIONS = [
    ("2026-09-03 10:35", "salt", "H", "20260903T163527Z_salt", "shared_fume_hood", "invalid",
     "doser-scale-unreadable: read_stable() path, balance 0-2 % stable once rig actuated; refused tare",
     "4/6 scale-error; dose 1 phantom 7.5393 g (0 rev); dose 2 57.5 mg (+7.5) from one 45 deg fine increment", "5528661410"),
    ("2026-09-03 11:04", "salt", "H", "20260903T170437Z_salt", "shared_fume_hood", "invalid",
     "doser-scale-unreadable; student repeatedly used hood compressed air; operator stood the shared hood down for G/H (5529240158)",
     "0.00 auger rev on all six; 5 scale-error; dose 5 '1.5410 g' = pre-flight salt (1.54132 g)", "5529102139;5529245844"),
    ("2026-09-03 ~15:04", "salt", "H", "", "new_fume_hood", "aborted (no run doc)",
     "first attempt after relocation hit two new firmware faults (over-strict refused-tare guard; integer-second retry deadline); fixed, re-run 15:40",
     "", "5531825264; run note 2026-09-03-salt-block-h-new-hood.md"),
    ("2026-09-03 15:40", "salt", "H", "20260903T214049Z_salt", "new_fume_hood", "valid",
     "qc ok; first bracket-read run", "50 mg +8.9/+4.3/-0.6; 200 mg -1.3/+13.3/-3.7; 4/6 ok", "5544565454"),
    ("2026-09-03 18:18", "salt", "G x1 (demo, #148)", "20260904T001821Z_salt", "new_fume_hood", "demo (valid=false, unreviewed)",
     "issue #148 demo", "1.0040 g (+3.9 mg), ok, 90 s", "#148; 5544565454"),
    ("2026-09-04 13:00", "white rice flour", "H", "20260904T190011Z_white-rice-flour", "new_fume_hood", "valid",
     "qc ok", "50 mg -5.0/-5.0/-4.0; 200 mg -4.8/-4.9/-5.0; 6/6 ok; 200 mg doses 677-780 s", "5544943576;5545930757"),
    ("2026-09-04 14:37", "xanthan gum", "H", "20260904T203727Z_xanthan-gum", "new_fume_hood", "valid",
     "qc ok (static/drift noted)", "50 mg -4.1/-2.3/+59.8; 200 mg +2.5/+2.6/+3.5; 5/6 ok", "5545930757"),
    ("2026-09-08 11:27", "CMC", "H", "20260908T172730Z_carboxymethyl-cellulose", "new_fume_hood", "invalid",
     "outlet-misaligned (#156)", "apparent 50 mg -39.6/-27.1/-2.6; 200 mg -43.2/-4.0/-4.6 (not accuracy data)", "5590598698"),
    ("2026-09-08 13:42", "CMC", "H", "20260908T194201Z_carboxymethyl-cellulose", "new_fume_hood", "valid (caveat)",
     "200 mg triple feed-limited; drift -11.4 mg/min", "50 mg -4.6/+0.2/-2.1 (3/3 ok); 200 mg -4.5/-14.2/-49.0 (1/3 ok)", "5592079984"),
    ("2026-09-09 12:53", "sodium alginate", "H", "20260909T185352Z_sodium-alginate", "new_fume_hood", "valid",
     "qc ok (budget-limited)", "50 mg -27.8/-11.3/-19.7; 200 mg -66.7/-52.1/-185.7; 0/6 ok", "5606851396;5609012161"),
    ("2026-09-09 16:52", "calcium lactate", "H", "20260909T225206Z_calcium-lactate", "new_fume_hood", "valid (capture-interrupted)",
     "qc ok; dose H5 reconstructed", "50 mg -1.3/+21.0/+12.1 (H2 zero-actuation); 200 mg -4.9/-9.0/~-35.5; 2/6 ok", "5609012161"),
    ("2026-09-10 07:39", "sodium sulfate", "G+H", "20260910T133932Z_sodium-sulfate", "new_fume_hood", "valid",
     "qc ok", "1 g -2.9/-4.7/-4.9 (3/3); 50 mg +17.7/+22.1/+46.9; 200 mg +6.6/+30.2/-4.5", "5619383507"),
    ("2026-09-10 11:08", "barium chloride", "G+H", "20260910T170858Z_barium-chloride", "new_fume_hood", "invalid",
     "arching-no-feed (caked hygroscopic column)", "9/9 stalled; G0 0.3453 g", "5622273948"),
    ("2026-09-10 13:44", "AlSi10Mg", "G+H", "20260910T194447Z_alsi10mg", "new_fume_hood", "valid",
     "qc ok", "1 g -2.7/+9.4/-1.1; 50 mg -3.4/+18.1/+49.7; 200 mg -2.8/-0.6/+2.6; 6/9 ok", "5623309132"),
    ("2026-09-10 15:29", "Si -325", "G+H", "20260910T212920Z_silicon-325", "new_fume_hood", "valid (conveying-slowly)",
     "cannot dose (replicates 2026-08-21)", "9/9 stalled at ~0 g (18.0 rev -> 1.6 mg)", "5625482642"),
    ("2026-09-10 16:20-17:25", "Si -110/+200", "G+H not run", "20260910T231950Z_silicon-110-200_preflight", "new_fume_hood", "stand-down #1",
     "dose gate failed 10/10 windows (+/-10-30 mg, ~10 min period, 0 shocks)", "pre-flight 316.5 mg/rev, 9.5 mg/tap", "5626124921"),
    ("2026-09-14 12:22-13:58", "Si -110/+200", "not run", "", "new_fume_hood", "stand-down #2",
     "19 gate windows, 0 passes (wave + mid-hold beaker service); Pi dropped off tailnet 14:00", "", "5668530343"),
    ("2026-09-14 15:43-17:17", "Si -110/+200", "not run", "", "new_fume_hood", "stand-down #3",
     "30 gate windows, 0 passes (wave, bench activity, then -7 to -9 mg/min drift)", "", "5671072772"),
    ("2026-09-14 19:55-20:27", "Si -110/+200", "not run", "", "new_fume_hood", "stand-down #4",
     "rig contention: PR #131 blocked-auger fixture install + concurrent sessions", "", "5673425201"),
    ("2026-09-14 20:55", "Si -110/+200", "G+H", "20260915T025556Z_silicon-110-200", "new_fume_hood", "valid",
     "qc ok; H2 excluded (0 rev, 0 taps)", "1 g -0.5/+3.3/-2.2 (3/3); 50 mg +4.5/-2.3/[+5.2 excl]; 200 mg -1.5/-1.8/+32.6", "5673671255"),
    ("2026-09-15 10:42", "salt", "0.5 g demo", "20260915T164228Z_salt-demo", "new_fume_hood", "demo (valid=false)",
     "gate not passed (+2.9 mg/min drift); batch demo", "0.4963 g (-3.7 mg), ok, 100 s, bulk 0/fine 16/tap 2", "5683919348"),
]

DOSE_START = re.compile(r"^\[dose\] three-phase dose to ([0-9.]+) g")
TARED = re.compile(r"^\[dose\] tared: baseline ([+-]?[0-9.]+) mg \(subtracted\), "
                   r"drift ([+-]?[0-9.]+) mg/min, read noise ([0-9.]+) mg")
TARE_WARN = re.compile(r"^\[dose\] WARNING the tare did not take -- pan reads ([+-]?[0-9.]+) g")
PHASE_END = re.compile(r"^=== phase (\d)/3 '(\w+)' end \((\d+) cycles\): mass ([+-]?[0-9.]+) / "
                       r"([0-9.]+) g \(([+-]?[0-9.]+) g to go, ([+-]?[0-9.]+) g this phase\), "
                       r"elapsed ([0-9.]+) s")
PHASE_SKIP = re.compile(r"^=== phase (\d)/3 '(\w+)' skipped")
TRACE = re.compile(r"^\[phase (\d) (\w+)\] (?:cycle|poll) (\d+)[^:]*: mass ([+-]?[0-9.]+) / "
                   r"([0-9.]+) g.*elapsed ([0-9.]+) s")
NUDGE = re.compile(r"nudging auger [0-9.]+ deg \(nudge (\d+)/(\d+)\)")


def git(repo: str, *args: str, binary: bool = False):
    out = subprocess.run(["git", "-C", repo, *args], check=True,
                         capture_output=True)
    return out.stdout if binary else out.stdout.decode("utf-8", "replace")


def ls_dirs(repo, ref, path):
    return [l for l in git(repo, "ls-tree", "-d", "--name-only", f"{ref}:{path}").splitlines() if l]


def ls_files(repo, ref, path):
    return [l for l in git(repo, "ls-tree", "--name-only", f"{ref}:{path}").splitlines() if l]


def first_commit(repo, path):
    """Earliest commit on any ref that added ``path`` (short hash + date)."""
    out = git(repo, "log", "--all", "--diff-filter=A", "--format=%h %ad",
              "--date=short", "--", path).strip().splitlines()
    return out[-1] if out else ""


def fnum(x):
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def parse_cycles(s):
    out = {"bulk": None, "fine": None, "tap": None}
    for part in (s or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            if k in out:
                out[k] = int(v)
    return out


def location_for(ts: str) -> str:
    if ts < "2026-08-11T18:12":
        return "lab_pre_hood"
    if ts < "2026-09-03T20:00":
        return "shared_fume_hood"
    return "new_fume_hood"


def parse_raw_serial(text: str):
    """Per-dose detail from the raw serial log, in DOSE-row order.

    Returns (details, partial): ``details`` is a list of dicts keyed by
    (block, n) for every completed DOSE row; ``partial`` holds the last dose
    context if the log ends without its DOSE row (serial corruption).
    """
    details, cur = [], None
    for raw in text.splitlines():
        line = raw.strip("\r")
        m = DOSE_START.match(line)
        if m:
            cur = {"log_target_g": float(m.group(1)), "tare_warning_pan_g": None,
                   "tare_baseline_mg": None, "tare_drift_mg_per_min": None,
                   "tare_read_noise_mg": None, "nudges": 0, "no_flow_msg": False,
                   "last_trace_mass_g": None, "last_trace_elapsed_s": None}
            for ph in ("bulk", "fine", "tap"):
                cur[f"{ph}_gain_mg"] = None
                cur[f"{ph}_end_s"] = None
                cur[f"{ph}_skipped"] = False
            continue
        if cur is None:
            continue
        if (m := TARE_WARN.match(line)):
            cur["tare_warning_pan_g"] = float(m.group(1))
        elif (m := TARED.match(line)):
            cur["tare_baseline_mg"] = float(m.group(1))
            cur["tare_drift_mg_per_min"] = float(m.group(2))
            cur["tare_read_noise_mg"] = float(m.group(3))
        elif (m := PHASE_END.match(line)):
            ph = m.group(2)
            cur[f"{ph}_gain_mg"] = round(1000.0 * float(m.group(7)), 1)
            cur[f"{ph}_end_s"] = float(m.group(8))
            cur["last_trace_mass_g"] = float(m.group(4))
            cur["last_trace_elapsed_s"] = float(m.group(8))
        elif (m := PHASE_SKIP.match(line)):
            cur[f"{m.group(2)}_skipped"] = True
        elif (m := TRACE.match(line)):
            cur["last_trace_mass_g"] = float(m.group(4))
            cur["last_trace_elapsed_s"] = float(m.group(6))
        elif (m := NUDGE.search(line)):
            cur["nudges"] = max(cur["nudges"], int(m.group(1)))
        elif "no powder flow" in line:
            cur["no_flow_msg"] = True
        elif line.startswith("DOSE,"):
            f = line.split(",")
            cur["block"] = f[11] if len(f) > 11 and f[11] else "G"
            cur["n"] = int(f[1])
            details.append(cur)
            cur = None
    return details, cur


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--ref", default=DEFAULT_REF)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--copy-raw", action="store_true",
                    help="copy every round-2 run directory into OUT/raw/")
    ap.add_argument("--no-provenance", action="store_true",
                    help="skip the (slow) per-run first-commit lookup")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    run_rows, dose_rows = [], []
    for d in ls_dirs(a.repo, a.ref, "data/battery"):
        base = f"data/battery/{d}"
        files = ls_files(a.repo, a.ref, base)
        rnd = "2" if d >= "20260901" else "1"
        if a.copy_raw and rnd == "2":
            for fn in files:
                dst = out / "raw" / d / fn
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(git(a.repo, "show", f"{a.ref}:{base}/{fn}", binary=True))
        rjson = [f for f in files if f.startswith("run_") and f.endswith(".json")]
        comment_ids, commit_note = R2_PROVENANCE.get(d, ("", ""))
        if not rjson:
            pf = json.loads(git(a.repo, "show", f"{a.ref}:{base}/preflight.json")) \
                if "preflight.json" in files else {}
            outcome = pf.get("outcome", "")          # round-1 layout (nested)
            if isinstance(pf.get("preflight"), dict):
                pf = dict(pf["preflight"], outcome=outcome)
            ts = d[:4] + "-" + d[4:6] + "-" + d[6:8] + "T" + d[9:11] + ":" + d[11:13] + ":" + d[13:15] + "Z"
            run_rows.append(dict(
                run_id=d, round=rnd, kind="preflight-only", started_utc=ts, started_local="",
                elapsed_s="", powder_id=d.split("_", 1)[1].replace("_preflight", ""),
                display="", batch="", blocks="", battery_version="", status="",
                qc_valid=False,
                qc_verdict=pf.get("outcome") or "dose-gate stand-down (no battery run)",
                qc_reason="", preflight_verdict=pf.get("verdict", ""),
                preflight_mg_per_rev_fw=pf.get("mg_per_rev", ""),
                preflight_per_rev_mg=";".join(str(x) for x in (
                    pf.get("per_rev_mg") or [round(1000 * g, 1) for g in
                                             (pf.get("per_rev_g") or pf.get("rev_deltas") or [])])),
                preflight_tilt_deg=pf.get("tilt_deg", ""), preflight_rpm=pf.get("rpm", ""),
                read_path="", location=location_for(ts), n_doses=0, env_shock_events="",
                env_retries="", env_unsettled_brackets="", caveat=RUN_CAVEATS.get(d, ""),
                issue116_comments=comment_ids, commit=commit_note,
                first_commit="" if a.no_provenance else first_commit(a.repo, f"{base}/preflight.json"),
                data_dir=base))
            continue
        doc = json.loads(git(a.repo, "show", f"{a.ref}:{base}/{rjson[0]}"))
        params = doc.get("parameters") or {}
        qc = doc.get("qc") or {}
        pre = doc.get("preflight") or {}
        ts = doc.get("started_utc") or ""
        read_path = params.get("config.dose_read_path") or "read_stable"
        pid = doc.get("powder_id") or d.split("_", 1)[1]
        batch = doc.get("batch", "")
        is_demo = batch == "demo" or qc.get("verdict") in ("demo", "unreviewed")
        kind = "demo" if is_demo else "battery"
        per_rev = pre.get("per_rev_mg") or [round(1000 * g, 1) for g in (pre.get("per_rev_g") or [])]
        run_rows.append(dict(
            run_id=d, round=rnd, kind=kind, started_utc=ts,
            started_local=doc.get("started_local") or "", elapsed_s=doc.get("elapsed_s", ""),
            powder_id=pid, display=DISPLAY.get(pid, pid), batch=batch,
            blocks=params.get("blocks", ""), battery_version=params.get("battery_version", ""),
            status=doc.get("status", ""), qc_valid=bool(qc.get("valid_for_cross_powder_comparison")),
            qc_verdict=qc.get("verdict", ""), qc_reason=(qc.get("reason") or
                                                          (qc.get("review") or {}).get("exclusions", "")),
            preflight_verdict=qc.get("preflight_verdict") or pre.get("verdict", ""),
            preflight_mg_per_rev_fw=pre.get("mg_per_rev", ""),
            preflight_per_rev_mg=";".join(str(x) for x in per_rev),
            preflight_tilt_deg=pre.get("tilt_deg", ""), preflight_rpm=pre.get("rpm", ""),
            read_path=read_path, location=location_for(ts), n_doses=len(doc.get("doses") or []),
            env_shock_events=params.get("env.shock_events", ""), env_retries=params.get("env.retries", ""),
            env_unsettled_brackets=params.get("env.unsettled_brackets", ""),
            caveat=RUN_CAVEATS.get(d, ""), issue116_comments=comment_ids, commit=commit_note,
            first_commit="" if a.no_provenance else first_commit(a.repo, f"{base}/{rjson[0]}"),
            data_dir=base))

        raw = [f for f in files if f.startswith("raw_serial_") and f.endswith(".log")]
        details, partial = ([], None)
        if raw:
            details, partial = parse_raw_serial(git(a.repo, "show", f"{a.ref}:{base}/{raw[0]}"))
        by_key = {(x["block"], x["n"]): x for x in details}
        doses = list(doc.get("doses") or [])
        for rec in RECONSTRUCTED_DOSES:
            if rec["run_id"] == d and not any((x.get("block") or "G") == rec["block"] and x.get("n") == rec["n"] for x in doses):
                doses.append(dict(rec, _reconstructed=True))
        for seq, x in enumerate(doses):
            block = x.get("block") or "G"
            det = by_key.get((block, x.get("n")))
            if det is None and x.get("_reconstructed") and partial:
                det = partial
            dose_rows.append(make_dose_row(d, rnd, doc, x, block, seq, det, read_path,
                                           location_for(ts), is_demo, qc))

    for c in COMMENT_ONLY_DOSES:
        x = dict(n=c["n"], target_g=c["target_g"], dispensed_g=c["dispensed_g"],
                 error_g=round(c["dispensed_g"] - c["target_g"], 4), status=c["status"],
                 elapsed_s=c["elapsed_s"], auger_rev=c["auger_rev"], taps=c["taps"],
                 phase_cycles=c["phase_cycles"])
        doc = dict(powder_id=c["powder_id"], started_utc=c["started_utc"], started_local="",
                   batch="demo")
        row = make_dose_row(c["run_id"], c["round"], doc, x, c["block"], 0, None, c["read_path"],
                            c["location"], True, {"verdict": c["run_qc_verdict"]})
        row["source"] = c["source"]
        row["note"] = c["note"]
        dose_rows.append(row)

    write_csv(out / "runs_all.csv", run_rows)
    write_csv(out / "doses_all.csv", dose_rows)
    s1 = summarise(dose_rows, ("powder_id", "target_mg"))
    s2 = summarise(dose_rows, ("powder_id", "target_mg", "round"))
    write_csv(out / "dose_summary_by_powder_target.csv", s1)
    write_csv(out / "dose_summary_by_powder_target_round.csv", s2)
    inv = [dict(zip(("date_local_MDT", "powder", "protocols", "run_id", "location", "outcome",
                     "reason", "key_results", "issue116_comments"), r)) for r in ROUND2_SESSIONS]
    write_csv(out / "round2_inventory.csv", inv)
    crosscheck_round1(a.repo, dose_rows)


def make_dose_row(run_id, rnd, doc, x, block, seq, det, read_path, location, is_demo, qc):
    target_mg = 1000.0 * float(x["target_g"])
    delivered = fnum(x.get("dispensed_g"))
    delivered_mg = None if delivered is None else round(1000.0 * delivered, 1)
    err_g = fnum(x.get("error_g"))
    if err_g is None and delivered is not None:
        err_g = delivered - float(x["target_g"])
    error_mg = None if err_g is None else round(1000.0 * err_g, 1)
    rev = fnum(x.get("auger_rev"))
    taps = x.get("taps")
    reconstructed = bool(x.get("_reconstructed"))
    actuated = None if reconstructed else ((rev or 0) > 0 or (taps or 0) > 0)
    if reconstructed:
        actuated = True
    cyc = parse_cycles(x.get("phase_cycles"))
    status = x.get("status", "")
    protocol = "demo" if is_demo else block
    run_valid = bool(qc.get("valid_for_cross_powder_comparison"))
    reasons = []
    if is_demo:
        reasons.append(f"demo ({qc.get('verdict', '')})")
    elif not run_valid:
        reasons.append(f"run QC invalid: {qc.get('verdict', '')}")
    if status in ("scale-error", "not-tared"):
        reasons.append(f"no terminal control state ({status})")
    if actuated is False:
        reasons.append("no actuation (0 auger rev, 0 taps): afterflow/settling, not a controller measurement")
    dose_valid = not reasons
    within5pct = None if error_mg is None else abs(error_mg) <= 0.05 * target_mg + 1e-9
    within_fw = None if error_mg is None else abs(error_mg) <= FW_TOL_MG + 1e-9
    ts = doc.get("started_utc") or ""
    pid = doc.get("powder_id", "")
    row = dict(
        run_id=run_id, round=rnd, date_utc=ts[:10], started_utc=ts,
        started_local=doc.get("started_local") or "", powder_id=pid,
        display=DISPLAY.get(pid, pid), batch=doc.get("batch", ""), protocol=protocol, block=block,
        dose_n=x.get("n"), dose_seq=seq, target_mg=round(target_mg, 1), delivered_mg=delivered_mg,
        error_mg=error_mg, error_pct=None if error_mg is None else round(100.0 * error_mg / target_mg, 2),
        abs_error_mg=None if error_mg is None else abs(error_mg), time_s=fnum(x.get("elapsed_s")),
        status=status, pass_fw_status=status == "ok", pass_fw_abs5=within_fw, pass_5pct=within5pct,
        auger_rev_fw=rev, stepper_rev=None if rev is None else round(rev * FW_GEAR, 3),
        auger_rev_if_48_16=None if rev is None else round(rev * FW_GEAR / CAD_GEAR, 3),
        taps=taps, bulk_cycles=cyc["bulk"], fine_cycles=cyc["fine"], tap_cycles=cyc["tap"],
        phase_cycles=x.get("phase_cycles", ""), actuated=actuated, reconstructed=reconstructed,
        read_path=read_path, location=location, run_qc_valid=run_valid,
        run_qc_verdict=qc.get("verdict", ""), dose_valid=dose_valid,
        invalid_reason="; ".join(reasons), caveat=RUN_CAVEATS.get(run_id, ""),
        source="git run JSON" if not reconstructed else "run note (reconstructed)",
        note=x.get("note", ""))
    keys = ["tare_warning_pan_g", "tare_baseline_mg", "tare_drift_mg_per_min", "tare_read_noise_mg",
            "bulk_gain_mg", "bulk_end_s", "bulk_skipped", "fine_gain_mg", "fine_end_s", "fine_skipped",
            "tap_gain_mg", "tap_end_s", "tap_skipped", "nudges", "no_flow_msg",
            "last_trace_mass_g", "last_trace_elapsed_s"]
    for k in keys:
        row[k] = det.get(k) if det else None
    return row


def summarise(rows, keys):
    groups = {}
    for r in rows:
        if not r["dose_valid"]:
            continue
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    out = []
    for key, g in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1:])):
        errs = [r["error_mg"] for r in g if r["error_mg"] is not None]
        pcts = [r["error_pct"] for r in g if r["error_pct"] is not None]
        times = [r["time_s"] for r in g if r["time_s"] is not None]
        n = len(g)
        row = dict(zip(keys, key))
        row.update(
            display=g[0]["display"], n=n,
            n_reconstructed=sum(1 for r in g if r["reconstructed"]),
            mean_error_mg=round(statistics.mean(errs), 2) if errs else None,
            sd_error_mg=round(statistics.stdev(errs), 2) if len(errs) > 1 else None,
            mean_abs_error_mg=round(statistics.mean(abs(e) for e in errs), 2) if errs else None,
            min_error_mg=min(errs) if errs else None, max_error_mg=max(errs) if errs else None,
            mean_error_pct=round(statistics.mean(pcts), 2) if pcts else None,
            sd_error_pct=round(statistics.stdev(pcts), 2) if len(pcts) > 1 else None,
            pass_5pct=f"{sum(1 for r in g if r['pass_5pct'])}/{n}",
            pass_fw_status_ok=f"{sum(1 for r in g if r['pass_fw_status'])}/{n}",
            pass_fw_abs5=f"{sum(1 for r in g if r['pass_fw_abs5'])}/{n}",
            mean_time_s=round(statistics.mean(times), 1) if times else None,
            median_time_s=round(statistics.median(times), 1) if times else None,
            statuses=";".join(sorted({r["status"] for r in g})),
            rounds=";".join(sorted({str(r["round"]) for r in g})),
            dates=";".join(sorted({r["date_utc"] for r in g})),
            read_paths=";".join(sorted({r["read_path"] for r in g})),
            locations=";".join(sorted({r["location"] for r in g})),
            runs=";".join(sorted({r["run_id"] for r in g})))
        out.append(row)
    return out


def write_csv(path, rows):
    if not rows:
        return
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    print(f"wrote {path} ({len(rows)} rows)")


def crosscheck_round1(repo, dose_rows):
    """Compare round-1 doses against the committed candidates/data/doses.csv."""
    p = Path(repo) / "paper/figures/candidates/data/doses.csv"
    if not p.exists():
        return
    ref = {(r["run_id"], int(r["n"])): r for r in csv.DictReader(open(p))}
    ours = {(r["run_id"], r["dose_n"]): r for r in dose_rows if r["round"] == "1"}
    bad = [k for k in ref if k not in ours or
           abs(float(ref[k]["dispensed_g"]) * 1000 - (ours[k]["delivered_mg"] or 0)) > 0.051]
    print(f"round-1 cross-check vs {p.name}: {len(ref)} committed rows, "
          f"{len(ours)} built, {len(bad)} mismatches {bad[:5]}")


if __name__ == "__main__":
    sys.exit(main())

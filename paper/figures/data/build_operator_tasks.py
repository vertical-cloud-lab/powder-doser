#!/usr/bin/env python3
"""Count the operator's tasks in the two test rounds and write the SI table.

The paper has to say what a person did between doses: filling and loading the
auger, positioning it over the cup, taring, checking the cup and outlet, and
clearing faults.  This script counts each task from the record and writes

  operator_tasks.csv          one row per task: when it is needed, how often it
                              happened, what could automate it, the numbers
                              behind the text, and where they come from
  operator_tasks_table.tex    the same rows as an SI table (label tbl:operator)

Two kinds of source are used.

* Run logs, read straight out of git (``git show REF:path``), so the working
  tree is never touched.  The default REF is the newest issue #116 branch,
  which holds all 37 run directories listed in runs_all.csv.  From each raw
  serial log the script counts every operator PROMPT line by type, the dose
  tares the firmware checked, refused protocol tares, and doses that read
  powder already in the cup.  Three runs have no raw serial log (the
  brown-rice-flour runs of 4 August 22:49 and 5 August 18:53 UTC, and the
  AlSi10Mg run of 21 August).  Their prompts are rebuilt from the run
  document: the firmware prints one cup prompt per closed-loop dose and per
  protocol C tilt, and one refill prompt per tilt that logs four low-flow
  trials in a row.  That rule reproduces the logged prompts of every run that
  has a log, and the script checks this each time it runs.
* Events that exist only in the issue threads and run notes: auger fills and
  loads, moves, faults and their recoveries.  They are listed below (LOADS,
  FILLED_AUGERS, EVENTS), each with the comment or file that records it, and
  counted by type.

Every run was started with ``attended=False``.  The device printed each prompt
and carried on at once; the operator worked at the bench only between runs.
The prompt counts are therefore how often the protocol asked for a person,
not how often one answered.

Usage:  python3 build_operator_tasks.py [--repo PATH] [--ref REF] [--events]
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = str(HERE.parents[2])
DEFAULT_REF = "origin/claude/issue-116-20260915-1622"
BATTERY = "data/battery"
GH = "https://github.com/vertical-cloud-lab/powder-doser"


def c(issue: int, comment: int) -> str:
    """Link to one comment (#124 and #131 are pull requests)."""
    kind = "pull" if issue in (124, 131) else "issues"
    return f"{GH}/{kind}/{issue}#issuecomment-{comment}"


def note(name: str) -> str:
    """Link to a run-notes file on the campaign branch."""
    return f"{GH}/blob/{DEFAULT_REF.split('/', 1)[1]}/docs/battery-runs/{name}"


# Operator prompts printed by hardware/test-module/firmware/powder_battery.py,
# each keyed by a phrase that only it contains.
PROMPTS = (
    ("cup_protocol_c", "block C at tilt"),                       # each C tilt
    ("cup_first_dose", "EMPTY the collection cup now"),           # start of G or H
    ("cup_next_dose", "done -- empty the cup for the next dose"),
    ("refill_check", "hopper empty?"),                            # 4 low-flow trials
    ("capacity", "near its"),                                     # gross load
    ("scale_silent", "scale silent or overloaded"),
)
STALL_RUN = 4   # MAX_STALLS in powder_battery.py

# --------------------------------------------------------------------------
# The record outside the logs
# --------------------------------------------------------------------------
# Every message on issue #116 in which an operator reports putting an auger
# on the doser (and, from the second one on, removing its outlet tape).
LOADS = [
    ("2026-08-04", "brown rice flour", 5184344406),
    ("2026-08-04", "white rice flour", 5184669386),
    ("2026-08-04", "brown rice flour", 5185277911),
    ("2026-08-05", "sodium alginate", 5193368145),
    ("2026-08-05", "brown rice flour (second auger)", 5195877808),
    ("2026-08-05", "calcium lactate", 5196667702),
    ("2026-08-05", "CMC", 5197386841),
    ("2026-08-06", "xanthan gum", 5205634345),
    ("2026-08-06", "salt", 5206324891),
    ("2026-08-11", "AlSi10Mg", 5257182538),
    ("2026-08-12", "salt", 5273060787),
    ("2026-08-19", "sodium sulfate", 5345684837),
    ("2026-08-19", "salt", 5348359774),
    ("2026-08-20", "salt", 5358241347),
    ("2026-08-20", "sodium sulfate", 5360522925),
    ("2026-08-20", "Si −110/+200", 5362101891),
    ("2026-08-20", "salt", 5362816062),
    ("2026-08-21", "AlSi10Mg", 5371600301),
    ("2026-08-21", "Si −325", 5372253305),
    ("2026-08-21", "barium chloride", 5372813290),
    ("2026-08-21", "fumed silica", 5373409748),
    ("2026-08-21", "salt", 5374113532),
    ("2026-09-03", "salt", 5531820924),
    ("2026-09-04", "white rice flour", 5544938076),
    ("2026-09-04", "xanthan gum", 5545925836),
    ("2026-09-08", "CMC", 5588681063),
    ("2026-09-09", "sodium alginate", 5606846231),
    ("2026-09-09", "calcium lactate", 5609007522),
    ("2026-09-10", "sodium sulfate", 5619377364),
    ("2026-09-10", "barium chloride", 5622268049),
    ("2026-09-10", "AlSi10Mg", 5623303425),
    ("2026-09-10", "Si −325", 5625477508),
    ("2026-09-10", "Si −110/+200", 5626119989),
    ("2026-09-11", "salt", 5635766543),
    ("2026-09-14", "Si −110/+200", 5668524313),
    ("2026-09-15", "Si −110/+200 (refitted after a blocked test auger)", 5673668067),
    ("2026-09-15", "salt", 5683911877),
]

# Augers filled for the campaign, with the first load of each.  Sixteen were
# printed (#134, #116 comment 5168132697); every powder kept its own tube.
FILLED_AUGERS = [
    ("brown rice flour", 5184344406), ("white rice flour", 5184669386),
    ("sodium alginate", 5193368145), ("brown rice flour, second auger", 5195877808),
    ("calcium lactate", 5196667702), ("CMC", 5197386841),
    ("xanthan gum", 5205634345), ("salt", 5206324891), ("AlSi10Mg", 5257182538),
    ("sodium sulfate", 5345684837), ("Si −110/+200", 5362101891),
    ("Si −325", 5372253305), ("barium chloride", 5372813290),
    ("fumed silica", 5373409748),
]
AUGERS_PRINTED = 16

# (date, task, type, what happened, source).  Types are what the table counts.
EVENTS = [
    # fill
    ("2026-08-12", "fill", "top-up", "salt auger freshly and fully reloaded", c(116, 5273064523)),
    ("2026-08-20", "fill", "top-up", "salt from a paper funnel poured back into its auger", c(116, 5358241347)),
    ("2026-08-21", "fill", "top-up", "AlSi10Mg auger freshly reloaded", c(116, 5371604726)),
    # tare: the AI agent re-zeroed the balance remotely, replacing a hand zero
    ("2026-08-20", "tare", "remote re-zero", "Error 1 cleared by a remote zero; hand taring stopped",
     c(116, 5356911453)),
    ("2026-08-20", "tare", "remote re-zero", "stale tare cleared before the salt reload", c(116, 5362820574)),
    ("2026-08-21", "tare", "remote re-zero", "stale -4.35 g reference cleared", c(116, 5374118952)),
    ("2026-09-04", "tare", "remote re-zero", "re-zeroed before white rice flour", c(116, 5544943576)),
    ("2026-09-04", "tare", "remote re-zero", "re-zeroed before xanthan gum", c(116, 5545930757)),
    ("2026-09-08", "tare", "remote re-zero", "1.378 g of stray CMC zeroed out", c(116, 5590598698)),
    ("2026-09-10", "tare", "remote re-zero", "stale -5.07 g tare cleared", c(116, 5625482642)),
    ("2026-09-10", "tare", "remote re-zero", "stale -33 mg tare cleared", c(116, 5626124921)),
    ("2026-09-14", "tare", "remote re-zero", "stale +73.8 mg tare cleared", c(116, 5668530343)),
    ("2026-09-14", "tare", "remote re-zero", "stale +252.6 mg tare cleared", c(116, 5671072772)),
    ("2026-09-15", "tare", "remote re-zero", "stale -66.6 mg tare cleared", c(116, 5673425201)),
    ("2026-09-15", "tare", "remote re-zero", "stale -9.97 g tare cleared", c(116, 5683919348)),
    # load
    ("2026-08-05", "load", "tape left on", "CMC loaded with tape over the outlet; feed check read 0 g; "
     "camera showed the tape; operator removed it", c(116, 5197393181)),
    # position
    ("2026-08-19", "position", "levelled", "balance levelled after the move back into the fume hood",
     c(116, 5344171434)),
    ("2026-08-20", "position", "levelled", "balance levelled again", c(116, 5362101891)),
    ("2026-09-03", "position", "levelled", "balance levelled in the second fume hood", c(116, 5531820924)),
    ("2026-09-08", "position", "misaligned", "outlet missed the hole over the cup; run excluded; "
     "doser re-aligned", c(116, 5590592011)),
    # check
    ("2026-08-11", "check", "not hand-turned", "AlSi10Mg loaded without hand-turning; feed check "
     "charged the flights", c(116, 5257182538)),
    ("2026-08-20", "check", "not hand-turned", "sodium sulfate auger not turned before the run",
     c(116, 5360527579)),
    ("2026-08-20", "check", "not hand-turned", "Si −110/+200 loaded but not hand-rotated",
     note("2026-08-20-silicon-110-200.md")),
    ("2026-09-04", "check", "not hand-turned", "white rice flour not hand-rotated after loading",
     note("2026-09-04-white-rice-flour-block-h.md")),
    ("2026-08-21", "check", "outlet not visible", "draft cage hid the outlet from the camera; "
     "fumed-silica run excluded", c(116, 5373414333)),
    # clean (cup emptied or cleaned between runs, vessels, spills)
    ("2026-08-11", "clean", "vessel", "glass beaker broken; smaller cup used meanwhile", c(116, 5259483789)),
    ("2026-08-19", "clean", "vessel", "new 100 mL beaker too tall for the draft shield", c(116, 5345684837)),
    ("2026-08-19", "clean", "vessel", "paper cup on the pan", c(116, 5348362954)),
    ("2026-08-20", "clean", "vessel", "glass beaker that fits under the shield", c(116, 5357315768)),
    ("2026-08-12", "clean", "statement", "operator: the container is cleaned out between runs",
     c(116, 5273545919)),
    ("2026-09-04", "clean", "left over", "2.8 g of salt left from the previous run and a demo",
     c(116, 5544565454)),
    ("2026-09-08", "clean", "left over", "1.38 g of CMC left from the misaligned run", c(116, 5590598698)),
    ("2026-09-14", "clean", "left over", "1.69 g of silicon left in the beaker from 10 to 14 Sep; "
     "emptied during a stability hold", c(116, 5668530343)),
    ("2026-08-21", "clean", "most in one run", "about 15 g of AlSi10Mg collected in one run",
     c(116, 5371604726)),
    ("2026-09-09", "clean", "drying hold", "launch held about 50 min while a washed beaker dried",
     c(116, 5609012161)),
    ("2026-09-10", "clean", "drying hold", "launch held about 70 min after the barium chloride clean-up",
     c(116, 5623309132)),
    ("2026-08-21", "clean", "spill", "AlSi10Mg spreads over the draft-shield top", c(116, 5372253305)),
    ("2026-09-08", "clean", "spill", "misaligned run put most of 80 min of CMC on the enclosure top",
     c(116, 5590598698)),
    # fault: feed
    ("2026-08-05", "fault_feed", "second auger", "brown rice flour moved into a second printed auger",
     c(116, 5195877808)),
    ("2026-09-15", "fault_feed", "blocked auger removed", "blocked test auger (PR #131) removed and the "
     "silicon auger refitted", c(116, 5673668067)),
    ("2026-09-10", "fault_feed", "caked, not cleared", "barium chloride caked after 3 weeks in its auger; "
     "all nine doses stalled; re-run still owed", c(116, 5622273948)),
    # fault: mechanism
    ("2026-08-11", "fault_mech", "servo", "tilt servos seized; plate stayed at 0 deg; run excluded",
     c(116, 5259483789)),
    ("2026-08-11", "fault_mech", "screw", "hinge screw backing out under vibration", c(116, 5259483789)),
    ("2026-08-19", "fault_mech", "tap collar", "tap collar caught under the mounting plate; freed",
     c(116, 5344711922)),
    # fault: balance
    ("2026-08-19", "fault_balance", "off", "balance not switched on after the move", c(116, 5344711922)),
    ("2026-08-19", "fault_balance", "off", "balance off again; Error 1 on switching on", c(116, 5345684837)),
    ("2026-09-01", "fault_balance", "off", "balance found in standby before a demo", c(148, 5497295014)),
    ("2026-08-20", "fault_balance", "error 1", "hand zeroing and the CAL key did not clear Error 1",
     c(116, 5356905712)),
    ("2026-08-19", "fault_balance", "shield", "draft shield resting on a tall beaker (overload)",
     c(116, 5345690049)),
    ("2026-09-15", "fault_balance", "dust plate", "after the last run, drift traced to powder under the "
     "dust plate; cleaned and re-seated", c(157, 5686518259)),
    # fault: control link and reporting
    ("2026-08-07", "fault_link", "power cycle", "Pi offline; unplugged and replugged at the bench",
     c(127, 5220074912)),
    ("2026-09-10", "fault_link", "network drop", "Pi off the network 53 min; recovered without action",
     c(116, 5623309132)),
    ("2026-09-14", "fault_link", "network drop", "Pi off the network mid-hold; recovered without action",
     c(116, 5668530343)),
    ("2026-08-04", "fault_link", "status query", "operator asked whether the run had ended", c(116, 5184619548)),
    ("2026-08-05", "fault_link", "status query", "report frozen on protocol C", c(116, 5194659248)),
    ("2026-08-11", "fault_link", "status query", "run seemed to have stopped", c(116, 5257530987)),
    ("2026-09-04", "fault_link", "status query", "report paused before the end", c(116, 5544560003)),
    ("2026-09-04", "fault_link", "status query", "is the previous run done?", c(116, 5545823292)),
    ("2026-09-08", "fault_link", "status query", "comment if it is done", c(116, 5590592011)),
    ("2026-09-08", "fault_link", "status query", "report not updated", c(116, 5592074517)),
    ("2026-09-10", "fault_link", "status query", "is the previous run finished?", c(116, 5624316069)),
    ("2026-09-10", "fault_link", "status query", "is the run over now?", c(116, 5625019786)),
    # move or wait
    ("2026-08-11", "move", "move", "open bench to a shared fume hood", c(116, 5257056784)),
    ("2026-08-14", "move", "move", "balance taken back to the lab because it would not tare in the hood",
     c(131, 5297531375)),
    ("2026-08-19", "move", "move", "doser moved back into the fume hood", c(116, 5344171434)),
    ("2026-09-03", "move", "move", "shared hood to a second fume hood", c(116, 5531820924)),
    ("2026-08-21", "move", "draft cage", "improvised draft cage added; it hid the outlet from the camera",
     c(116, 5373409748)),
    ("2026-09-03", "move", "stand-down", "operator stopped dose runs in the shared hood "
     "(compressed air in use)", c(116, 5529240158)),
    ("2026-09-10", "move", "stand-down", "stability check failed 10 of 10 windows (Si −110/+200)",
     c(116, 5626124921)),
    ("2026-09-14", "move", "stand-down", "19 windows failed (Si −110/+200)", c(116, 5668530343)),
    ("2026-09-14", "move", "stand-down", "30 windows failed (Si −110/+200)", c(116, 5671072772)),
    ("2026-09-15", "move", "stand-down", "blocked test auger and other sessions on the rig (Si −110/+200)",
     c(116, 5673425201)),
]


# --------------------------------------------------------------------------
# Reading the logs
# --------------------------------------------------------------------------
def git(repo: str, *args: str) -> str:
    out = subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)
    return out.stdout.decode("utf-8", "replace")


def ls(repo: str, ref: str, path: str, dirs: bool = False) -> list[str]:
    args = ["ls-tree"] + (["-d"] if dirs else []) + ["--name-only", f"{ref}:{path}"]
    return [line for line in git(repo, *args).splitlines() if line]


def scan_log(text: str) -> collections.Counter:
    """Count prompts, tares and dose outcomes in one raw serial log."""
    n = collections.Counter()
    for raw in text.splitlines():
        line = raw.strip("\r")
        if line.startswith("PROMPT,"):
            for key, phrase in PROMPTS:
                if phrase in line:
                    n[key] += 1
                    break
            else:
                raise SystemExit(f"unclassified prompt: {line}")
        elif line.startswith("META,attended,"):
            n["attended" if line.endswith(",1") else "unattended"] += 1
        elif line.startswith("META,tare,"):
            n["protocol_tare_" + line.split(",")[2]] += 1
        elif line.startswith("[dose] three-phase dose to"):
            n["dose_started"] += 1
        elif line.startswith("[dose] tared:"):
            n["dose_tare_checked"] += 1
        elif line.startswith("[dose] WARNING the tare did not take"):
            n["dose_tare_not_taken"] += 1
        elif line.startswith("RETRY,"):
            n["shock_retry"] += 1
        elif line.startswith("DOSE,"):
            f = line.split(",")
            target, got, status = float(f[2]), float(f[3]), f[5]
            revs, taps = float(f[7]), int(f[8])
            n["dose_row"] += 1
            n["dose_" + status] += 1
            # Grams with no actuation, many times the target: powder already
            # in the cup, read as delivered after a refused tare.
            if revs == 0 and taps == 0 and got > 5 * target:
                n["phantom_dose"] += 1
    return n


def rebuild_from_doc(doc: dict) -> collections.Counter:
    """The prompts of a run with no raw log, from its run document."""
    n = collections.Counter()
    p = doc.get("parameters", {})
    blocks = p.get("blocks", "")
    n["unattended" if str(p.get("attended", "0")) == "0" else "attended"] += 1
    if "C" in blocks:
        n["cup_protocol_c"] += len(str(p.get("tilts_deg", "0;45;90")).split(";"))
    doses = doc.get("doses") or []
    n["dose_started"] = len(doses)
    for block in "GH":
        k = sum(1 for d in doses if (d.get("block") or "G") == block)
        if k:
            n["cup_first_dose"] += 1
            n["cup_next_dose"] += k - 1
    n["refill_check"] = refill_prompts(doc)
    n["rebuilt"] = 1
    return n


def refill_prompts(doc: dict) -> int:
    """One prompt per C or E tilt with STALL_RUN low-flow trials in a row."""
    flags = collections.defaultdict(list)
    for t in doc.get("trials") or []:
        if t.get("block") in ("C", "E") and t.get("phase") in ("rotation", "refeed"):
            flags[(t["block"], float(t["tilt_deg"]))].append(t.get("flag") == "lowflow")
    count = 0
    for series in flags.values():
        run = 0
        for low in series:
            run = run + 1 if low else 0
            if run >= STALL_RUN:
                count += 1
                break
    return count


def check_rebuild(name: str, logged: collections.Counter, doc: dict) -> None:
    """The rebuild rule must reproduce the prompts of a run that has a log.

    A run whose capture died mid-dose (calcium lactate, 9 Sep) logged the
    prompt for a dose its run document never received, so cup prompts are
    compared only when the document holds every dose the log started.
    """
    rebuilt = rebuild_from_doc(doc)
    keys = ["cup_protocol_c", "refill_check"]
    if rebuilt["dose_started"] == logged["dose_started"]:
        keys += ["cup_first_dose", "cup_next_dose"]
    for key in keys:
        if rebuilt[key] != logged[key]:
            raise SystemExit(f"{name}: rebuild rule gives {key}={rebuilt[key]}, log has {logged[key]}")


def collect(repo: str, ref: str) -> dict:
    runs = {}
    for d in ls(repo, ref, BATTERY, dirs=True):
        files = ls(repo, ref, f"{BATTERY}/{d}")
        raw = [f for f in files if f.startswith("raw_serial_")]
        doc = [f for f in files if f.startswith("run_") and f.endswith(".json")]
        if raw:
            runs[d] = scan_log(git(repo, "show", f"{ref}:{BATTERY}/{d}/{raw[0]}"))
            if doc:
                check_rebuild(d, runs[d], json.loads(git(repo, "show", f"{ref}:{BATTERY}/{d}/{doc[0]}")))
        elif doc:
            runs[d] = rebuild_from_doc(json.loads(git(repo, "show", f"{ref}:{BATTERY}/{d}/{doc[0]}")))
        else:
            runs[d] = collections.Counter(feed_check_only=1)
    return runs


# --------------------------------------------------------------------------
# Counting
# --------------------------------------------------------------------------
def count_everything(runs: dict, inventory: list[dict]) -> dict:
    total = collections.Counter()
    logged = collections.Counter()
    for name, n in runs.items():
        total.update(n)
        if not n.get("rebuilt"):
            logged.update(n)
    if total["attended"]:
        raise SystemExit("a run was attended; the table text assumes none was")

    ordered = sorted(inventory, key=lambda r: r["started_utc"])
    powders = [r["powder_id"].replace("salt-demo", "salt") for r in ordered]
    needed_loads = 1 + sum(1 for a, b in zip(powders, powders[1:]) if a != b)

    ev = collections.Counter((e[1], e[2]) for e in EVENTS)
    per_task = collections.Counter(e[1] for e in EVENTS)
    k = {
        "runs": len(inventory),
        "runs_with_prompts": sum(1 for n in runs.values() if n.get("unattended")),
        "logs": sum(1 for n in runs.values() if n.get("unattended") and not n.get("rebuilt")),
        "doses": total["dose_started"],
        "cup_dose": total["cup_first_dose"] + total["cup_next_dose"],
        "cup_first": total["cup_first_dose"],
        "cup_next": total["cup_next_dose"],
        "cup_c": total["cup_protocol_c"],
        "refill": total["refill_check"],
        "capacity": total["capacity"],
        "scale_silent": total["scale_silent"],
        "prompts_logged": sum(logged[key] for key, _ in PROMPTS),
        "prompts_all": sum(total[key] for key, _ in PROMPTS),
        "tare_checked": total["dose_tare_checked"],
        "tare_not_taken": total["dose_tare_not_taken"],
        "phantom": total["phantom_dose"],
        "protocol_tares": sum(v for key, v in total.items() if key.startswith("protocol_tare_")),
        "protocol_tares_failed": sum(v for key, v in total.items()
                                     if key.startswith("protocol_tare_") and key != "protocol_tare_ok"),
        "feed_checks": sum(1 for r in inventory if r["preflight_verdict"]),
        "check_only": sum(1 for r in inventory if r["kind"] == "preflight-only"),
        "filled": len(FILLED_AUGERS),
        "printed": AUGERS_PRINTED,
        "loads": len(LOADS),
        "needed_loads": needed_loads,
    }
    for (task, kind), v in ev.items():
        k[f"{task}:{kind}"] = v
    for task, v in per_task.items():
        k[f"{task}:all"] = v
    if k["cup_dose"] != k["doses"]:
        raise SystemExit(f"{k['cup_dose']} cup prompts for {k['doses']} doses")
    return k


def g(k: dict, key: str) -> int:
    return k.get(key, 0)


def rows(k: dict) -> list[dict]:
    """The table, in the order printed.  Text is plain; tex() escapes it."""
    return [
        dict(
            when="Every dose",
            task="Empty the collection cup",
            how=(f"Asked for before all {k['doses']} closed-loop doses and before {k['cup_c']} "
                 f"protocol C tilts. No request was answered, because every run was unattended: "
                 f"earlier powder stayed in the cup, and each dose was weighed from its own tare."),
            auto="A second cup position or a cup changer",
            counts=(f"prompts before a dose={k['cup_dose']} (before the first dose of protocol G or H="
                    f"{k['cup_first']}, between doses={k['cup_next']}); protocol C prompts={k['cup_c']}; "
                    f"capacity prompts={k['capacity']}; logged prompts of all kinds={k['prompts_logged']}, "
                    f"with rebuilt runs={k['prompts_all']}; answered at the bench=0"),
            basis="raw serial logs; 3 runs rebuilt from run documents",
            sources=f"{BATTERY}/*/raw_serial_*.log (PROMPT lines)"),
        dict(
            when="Every dose",
            task="Tare the balance",
            how=(f"Done by the firmware before each dose. From 3 Sep it also checked each tare and "
                 f"subtracted any residue ({k['tare_not_taken']} of {k['tare_checked']} had not taken). "
                 f"Before that, {k['phantom']} refused tares read leftover powder as doses of "
                 f"7.54 and 1.54 g."),
            auto="An auto-tare check (in the firmware from 3 Sep)",
            counts=(f"dose tares checked={k['tare_checked']}; not taken={k['tare_not_taken']}; "
                    f"phantom doses={k['phantom']}; protocol tares={k['protocol_tares']}, refused or "
                    f"skipped={k['protocol_tares_failed']}; remote re-zeros by the AI agent at the start "
                    f"of a session={g(k, 'tare:remote re-zero')}"),
            basis="raw serial logs ([dose] and META,tare lines); issue #116 for remote re-zeros",
            sources="; ".join([f"{BATTERY}/*/raw_serial_*.log", c(116, 5528661410), c(116, 5529102139)]
                              + [e[4] for e in EVENTS if e[1] == "tare"])),
        dict(
            when="Every run or powder change",
            task="Fill and label an auger; top it up",
            how=(f"At least {k['filled']} of the {k['printed']} printed augers were filled: one per powder, "
                 f"plus a second for brown rice flour. Top-ups were recorded at least "
                 f"{g(k, 'fill:top-up')} times. The firmware "
                 f"asked {k['refill']} times whether the tube was empty, and each was answered "
                 f"“keep” automatically."),
            auto="A cap-and-refill station with fill-level sensing",
            counts=(f"augers filled={k['filled']}; printed={k['printed']}; "
                    f"top-ups={g(k, 'fill:top-up')}; refill prompts={k['refill']}"),
            basis="issues #116 and #134; refill prompts from the raw serial logs",
            sources="; ".join([f"{GH}/issues/134#issuecomment-5183033746", c(116, 5168132697)]
                              + [c(116, cid) for _, cid in FILLED_AUGERS]
                              + [e[4] for e in EVENTS if e[1] == "fill"])),
        dict(
            when="Every run or powder change",
            task="Load an auger: mount it, seat its gear, remove the outlet tape",
            how=(f"The operators reported {k['loads']} loads; the order of the runs alone needed "
                 f"{k['needed_loads']}. Tape was left on the outlet once (5 Aug); the feed check and a "
                 f"camera frame caught it."),
            auto="A cartridge changer with a tape-free outlet seal",
            counts=(f"loads reported={k['loads']}; powder changes in run order={k['needed_loads']}; "
                    f"tape left on={g(k, 'load:tape left on')}"),
            basis="issue #116 operator comments; runs_all.csv for the run order",
            sources="; ".join(c(116, cid) for _, _, cid in LOADS)),
        dict(
            when="Every run or powder change",
            task="Position the outlet over the cup; level the balance",
            how=(f"Done by eye, with no fixture. Levelling was recorded {g(k, 'position:levelled')} times, "
                 f"after moves of the rig. One run was excluded because the outlet missed the cup "
                 f"(8 Sep)."),
            auto="A kinematic mount that fixes the outlet over the cup",
            counts=(f"levelled={g(k, 'position:levelled')}; misaligned={g(k, 'position:misaligned')}; "
                    f"moves={g(k, 'move:move')}"),
            basis="issues #116 and #156",
            sources="; ".join([e[4] for e in EVENTS if e[1] == "position"]
                              + [f"{GH}/issues/156#issuecomment-5590508708"])),
        dict(
            when="Every run or powder change",
            task="Check the outlet and feed before a run",
            how=(f"A scripted feed check (five auger revolutions) is recorded for at least "
                 f"{k['feed_checks']} of the {k['runs']} runs, {k['check_only']} of which went no "
                 f"further, and camera frames were checked remotely. "
                 f"It also filled the outlet flights when hand-turning after loading was skipped "
                 f"({g(k, 'check:not hand-turned')} times recorded)."),
            auto="The scripted check and camera (both used); an outlet sensor",
            counts=(f"runs with a recorded feed check={k['feed_checks']}; "
                    f"hand-turning skipped={g(k, 'check:not hand-turned')}; "
                    f"outlet hidden from the camera={g(k, 'check:outlet not visible')}"),
            basis="runs_all.csv (preflight_verdict); issue #116; run notes",
            sources="; ".join(e[4] for e in EVENTS if e[1] == "check")),
        dict(
            when="Every run or powder change",
            task="Empty and clean the cup; dispose of powder; wipe up spills",
            how=(f"By hand between runs, but powder stayed in the cup across a run or a powder "
                 f"change at least {g(k, 'clean:left over')} times. A beaker broke, and {g(k, 'clean:vessel') - 1} more "
                 f"vessels were tried before one fitted. Drying after washing delayed "
                 f"{g(k, 'clean:drying hold')} runs by 50 and 70 min."),
            auto="Disposable cups, a funnel, or a pan-clearing step",
            counts=(f"left over={g(k, 'clean:left over')}; vessels after the breakage="
                    f"{g(k, 'clean:vessel') - 1}; drying holds={g(k, 'clean:drying hold')}; "
                    f"spills noted={g(k, 'clean:spill')}; most collected in one run=15 g"),
            basis="issue #116",
            sources="; ".join(e[4] for e in EVENTS if e[1] == "clean")),
        dict(
            when="On a fault",
            task="Clear a feed fault",
            how=("Brown rice flour was moved into a second auger (5 Aug), and a blocked test auger "
                 "fitted for other work was removed (15 Sep). Barium chloride caked after 3 weeks in "
                 "its auger and was not cleared (10 Sep; run excluded)."),
            auto="Tapping before dosing; sealed, dry storage",
            counts=(f"cleared={g(k, 'fault_feed:second auger') + g(k, 'fault_feed:blocked auger removed')}; "
                    f"not cleared={g(k, 'fault_feed:caked, not cleared')}"),
            basis="issues #116 and #131",
            sources="; ".join(e[4] for e in EVENTS if e[1] == "fault_feed")),
        dict(
            when="On a fault",
            task="Repair the mechanism",
            how=("The tilt servos seized (11 Aug; run excluded; repaired next day), a hinge screw "
                 "backed out (11 Aug), and the tap collar caught under the mounting plate (19 Aug)."),
            auto="A tilt sensor; locknuts",
            counts=(f"faults={g(k, 'fault_mech:all')} (servo={g(k, 'fault_mech:servo')}, "
                    f"screw={g(k, 'fault_mech:screw')}, tap collar={g(k, 'fault_mech:tap collar')})"),
            basis="issue #116",
            sources="; ".join(e[4] for e in EVENTS if e[1] == "fault_mech")),
        dict(
            when="On a fault",
            task="Restore the balance",
            how=(f"Found off or in standby {g(k, 'fault_balance:off')} times. Error 1 resisted zeroing "
                 f"by hand and was cleared remotely (19–20 Aug). After the last run, drift was "
                 f"traced to powder under the dust plate."),
            auto="Automatic power-on and a standby check at start-up",
            counts=(f"off or standby={g(k, 'fault_balance:off')}; Error 1 episodes="
                    f"{g(k, 'fault_balance:error 1')}; draft shield on a tall beaker="
                    f"{g(k, 'fault_balance:shield')}; powder under the dust plate="
                    f"{g(k, 'fault_balance:dust plate')}"),
            basis="issues #116, #148 and #157",
            sources="; ".join(e[4] for e in EVENTS if e[1] == "fault_balance")),
        dict(
            when="On a fault",
            task="Restore the control link; confirm that a run ended",
            how=(f"The Pi was power-cycled by hand once (7 Aug), and {g(k, 'fault_link:network drop')} "
                 f"network drops cleared on their own. The operator asked "
                 f"{g(k, 'fault_link:status query')} times whether a run had ended, because the AI "
                 f"agent's report had stalled."),
            auto="A network watchdog; status messages from the rig",
            counts=(f"power cycles={g(k, 'fault_link:power cycle')}; "
                    f"network drops={g(k, 'fault_link:network drop')}; "
                    f"status queries={g(k, 'fault_link:status query')}"),
            basis="issues #116 and #127",
            sources="; ".join(e[4] for e in EVENTS if e[1] == "fault_link")),
        dict(
            when="On a fault",
            task="Move the rig or wait for a quiet room",
            how=(f"Moved {g(k, 'move:move')} times between the open bench and two fume hoods. Dose runs "
                 f"were postponed {g(k, 'move:stand-down')} times, {g(k, 'move:stand-down') - 1} of them "
                 f"for Si −110/+200, which finally ran in an empty lab in the evening."),
            auto="An enclosure on a vibration-isolated base; the stability check (used)",
            counts=(f"moves={g(k, 'move:move')}; postponements={g(k, 'move:stand-down')}; "
                    f"draft cage={g(k, 'move:draft cage')}"),
            basis="issues #116 and #131",
            sources="; ".join(e[4] for e in EVENTS if e[1] == "move")),
    ]


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------
def tex(s: str) -> str:
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"),
                 ("\u2212", "$-$"), ("\u2013", "--"), ("\u201c", "``"), ("\u201d", "''")):
        s = s.replace(a, b)
    # Keep numbers with their units and dates, and the silicon grade, on one line.
    s = re.sub(r"(\d) (g|mg|min|Aug|Sep)\b", r"\1~\2", s)
    return s.replace("Si $-$", "Si~$-$")


def plain(s: str) -> str:
    """ASCII punctuation for the CSV, like the other tables in this folder."""
    for a, b in (("\u2212", "-"), ("\u2013", "-"), ("\u201c", '"'), ("\u201d", '"')):
        s = s.replace(a, b)
    return s


def unique(sources: str) -> str:
    seen = []
    for item in sources.split("; "):
        if item and item not in seen:
            seen.append(item)
    return "; ".join(seen)


def write_csv(table: list[dict]) -> None:
    with open(HERE / "operator_tasks.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["task", "when_needed", "how_often", "automation", "counts", "basis", "sources"])
        for r in table:
            w.writerow([plain(r[key]) for key in ("task", "when", "how", "auto", "counts", "basis")]
                       + [unique(r["sources"])])


def write_tex(table: list[dict], k: dict) -> None:
    cols = (r"@{}>{\raggedright\arraybackslash}p{2.7cm}"
            r">{\raggedright\arraybackslash}p{1.7cm}"
            r">{\raggedright\arraybackslash}p{7.6cm}"
            r">{\raggedright\arraybackslash}p{3.1cm}@{}")
    caption = (
        f"Human tasks in the test campaign ({k['runs']} recorded runs and {k['doses']} "
        r"closed-loop doses in two rounds, 4--21~August and 3--15~September 2026). Counts come "
        r"from the raw serial logs where the firmware recorded the task, and otherwise from the "
        r"issue threads and run notes. Every run was started unattended, so the firmware's "
        r"requests to the operator continued at once and no one acted between doses. Counts and "
        r"sources for each task are in \texttt{paper/figures/data/operator\_tasks.csv}.")
    lines = [
        "% Generated by paper/figures/data/build_operator_tasks.py -- do not edit by hand.",
        r"\begin{table}[htbp]",
        r"\small",
        r"\centering",
        r"\caption{" + caption + "}",
        r"\label{tbl:operator}",
        r"\begin{tabular}{" + cols + "}",
        r"\toprule",
        r"Task & When needed & How often in the campaign & What could automate it \\",
    ]
    previous = None
    for r in table:
        if r["when"] != previous:
            lines.append(r"\midrule")
            when = tex(r["when"])
            previous = r["when"]
        else:
            lines.append(r"\addlinespace[3pt]")
            when = ""
        lines.append(f"{tex(r['task'])} & {when} & {tex(r['how'])} & {tex(r['auto'])} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    (HERE / "operator_tasks_table.tex").write_text("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--ref", default=DEFAULT_REF)
    ap.add_argument("--events", action="store_true", help="also print every curated event")
    a = ap.parse_args()

    with open(HERE / "runs_all.csv", newline="") as fh:
        inventory = list(csv.DictReader(fh))
    runs = collect(a.repo, a.ref)
    if {r["run_id"] for r in inventory} != set(runs):
        raise SystemExit("run directories on the branch and runs_all.csv disagree")
    k = count_everything(runs, inventory)
    table = rows(k)
    write_csv(table)
    write_tex(table, k)

    print(f"{k['runs']} runs, {k['logs']} raw logs + {k['runs_with_prompts'] - k['logs']} rebuilt, "
          f"{k['doses']} closed-loop doses")
    print(f"prompts: {k['prompts_logged']} logged, {k['prompts_all']} with rebuilt runs; "
          f"cup before a dose {k['cup_dose']}, protocol C {k['cup_c']}, refill {k['refill']}, "
          f"capacity {k['capacity']}, scale silent {k['scale_silent']}")
    print(f"tares: {k['tare_not_taken']}/{k['tare_checked']} dose tares not taken; "
          f"{k['phantom']} phantom doses; protocol tares {k['protocol_tares_failed']}/"
          f"{k['protocol_tares']} refused or skipped")
    print(f"wrote operator_tasks.csv and operator_tasks_table.tex ({len(table)} tasks)")
    if a.events:
        for date, task, kind, what, src in sorted(EVENTS):
            print(f"{date}  {task:14s} {kind:22s} {what}  <{src}>")


if __name__ == "__main__":
    main()

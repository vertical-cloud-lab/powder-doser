#!/usr/bin/env python3
"""Write the SI design-log table (CAD entries only) from design_log_cad.csv.

design_log_cad.csv is hand-coded: one row per entry of DESIGN-LOG.md (PR #74)
that made or changed a 3D model of a part. Each row records who modelled it,
whether a print is recorded, its outcome, every recorded failure with what
caught it, and whether a later version was made for a new requirement. The
coding comes from the entry's text and the issue or pull-request thread it
links; ``evidence`` and ``notes`` give the sources.

This script checks the coding for consistency and, when DESIGN-LOG.md can be
found, against the log itself: every entry in the part subsystems must be
either coded or listed in EXCLUDED with a reason. It then sums the coding by
part family into design_log_cad_table.tex.

Usage:  python3 build_design_log_table.py [--log PATH/TO/DESIGN-LOG.md]
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import re
import subprocess
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CSV_PATH = HERE / "design_log_cad.csv"
OUT_PATH = HERE / "design_log_cad_table.tex"
LOG_BRANCH = "origin/copilot/record-of-designs"  # PR #74, until DESIGN-LOG.md is on main

# Log subsystem (as assigned by tools/design_log/build_design_log.py) -> table row.
FAMILY_OF_SUBSYSTEM = {
    "Scoop / excavator": "Scoop and excavator",
    "Sieve-cup alternatives (A–H)": "Sieve-cup alternatives",
    "Auger": "Auger",
    "Auger bracket": "Auger bracket",
    "Sealing cap": "Sealing cap",
    "Tap collar": "Tap collar",
    "Doser module": "Doser module",
    "Mounting plate & hinge": "Mounting plate and hinge",
    "Multi-doser": "Multi-doser",
}
FAMILIES = list(FAMILY_OF_SUBSYSTEM.values())
ROW_LABEL = {  # shorter names for the table
    "Scoop and excavator": "Excavator scoop",
    "Sieve-cup alternatives": "Sieve cups (A--H)",
}

# Copied from tools/design_log/build_design_log.py (PR #74): how the log assigns
# each entry to a subsystem, from its pr= tag or, for newer entries, its sub= tag.
PR_SUBSYSTEM = {
    "0": "Scoop / excavator", "2": "Scoop / excavator", "5": "Scoop / excavator",
    "13": "Sieve-cup alternatives (A–H)", "16": "Auger", "25": "Electronics & PCB",
    "31": "Doser module", "35": "Doser module", "37": "Sealing cap",
    "45": "Electronics & PCB", "47": "Auger bracket", "49": "Auger", "51": "Tap collar",
    "53": "Auger bracket", "55": "Auger bracket", "57": "Mounting plate & hinge",
    "59": "Mounting plate & hinge", "61": "Electronics & PCB",
    "63": "Mounting plate & hinge", "66": "Mounting plate & hinge", "68": "Auger",
}
SUB_SLUG = {
    "auger": "Auger", "module": "Doser module", "mounting": "Mounting plate & hinge",
    "electronics": "Electronics & PCB", "firmware": "Firmware & control",
    "test-rig": "Test method & rig", "multi-doser": "Multi-doser", "tooling": "Design tooling",
}

# Entries in the part subsystems that are not counted, and why.
_DUPLICATE = "same commit as {} (PR #66 was branched from PR #57), so logged twice"
EXCLUDED = {
    "e001": "hand sketch",
    "e002": "2D concept diagram", "e003": "2D concept diagram", "e004": "2D concept diagram",
    "e005": "2D concept diagram", "e006": "2D concept diagram",
    "e007": "2D diagrams redrawn for clarity",
    "e008": "2D mechanism animation and bistability analysis",
    "e017": "x-ray and cross-section views only",
    "e028": "annotated explainer panels only",
    "e040": "flow diagram and tilt render only",
    "e066": _DUPLICATE.format("e065"), "e068": _DUPLICATE.format("e067"),
    "e075": _DUPLICATE.format("e074"), "e077": _DUPLICATE.format("e076"),
    "e079": _DUPLICATE.format("e078"), "e082": _DUPLICATE.format("e081"),
    "e084": _DUPLICATE.format("e083"),
    "e098": "decision to adopt e097; no new geometry",
    "e103": "second servo added in firmware and wiring; no CAD recorded",
    "e113": "locknuts fitted; merging the brackets into the plate is not recorded",
    "e114": "batch printing and labelling of e109; no new geometry",
    "e117": "concept described in text; no CAD recorded",
    "e121": "collar freed on the rig and a pre-flight check changed; no CAD",
    "e128": "documentation render of the current assembly",
}

MODELLERS = {"AI coding agent": "agent", "text-to-CAD tool": None, "team, conventional CAD": "team"}
OUTCOMES = {  # CSV value -> table column
    "worked": "W", "worked with issues": "I", "failed": "F",
    "superseded": "S", "not built": "N", "not yet tested": "N",
}
BUILT = {"worked", "worked with issues", "failed", "not yet tested"}
# Failure types in the order of the main text's Table 2, then the others the log shows.
FAILURE_TYPES = {
    "parts do not fit": "do not fit",
    "unrequested change": "unrequested",
    "mislabelled variant": "mislabelled",
    "sub-millimetre error": "sub-millimetre",
    "bad inputs": "bad inputs",
    "no sense of finished": "no sense of finished",
    "wrong orientation": "orientation",
    "malformed feature": "malformed",
    "not printable": "not printable",
    "failed in use or test": "failed in test",
}
CATCHERS = {
    "human review": "review",
    "print or bench test": "test",
    "check or AI judge": "check",
    "not recorded": "not recorded",
}

ENTRY_RE = re.compile(r"<!-- ENTRY (?P<meta>[^>]*?)-->\r?\n", re.S)
HEAD_RE = re.compile(r"^### (?P<head>.+)$", re.M)
NAME_RE = re.compile(r"—\s*(?P<name>.+?)\s*·")


def parse_failures(cell: str) -> list[tuple[str, str]]:
    pairs = []
    for item in filter(None, (s.strip() for s in cell.split(";"))):
        kind, _, catcher = (s.strip() for s in item.partition(":"))
        if kind not in FAILURE_TYPES or catcher not in CATCHERS:
            raise SystemExit(f"unknown failure coding {item!r}")
        pairs.append((kind, catcher))
    return pairs


def load_rows() -> list[dict]:
    rows = list(csv.DictReader(CSV_PATH.open(newline="", encoding="utf-8")))
    seen = set()
    for r in rows:
        e = r["entry"]
        problems = []
        if e in seen or e in EXCLUDED:
            problems.append("duplicate or excluded entry")
        seen.add(e)
        if r["family"] not in FAMILIES:
            problems.append(f"family {r['family']!r}")
        if r["modelled_by"] not in MODELLERS:
            problems.append(f"modelled_by {r['modelled_by']!r}")
        if r["outcome"] not in OUTCOMES:
            problems.append(f"outcome {r['outcome']!r}")
        if r["printed"] not in ("yes", "no") or (r["printed"] == "yes") != (r["outcome"] in BUILT):
            problems.append("printed must be yes exactly when the outcome comes from a built part")
        if r["requirement_changed"] not in ("yes", "no"):
            problems.append("requirement_changed must be yes or no")
        if problems:
            raise SystemExit(f"{e}: " + "; ".join(problems))
        r["failure_list"] = parse_failures(r["failures"])
    return rows


def read_log(path: str | None) -> str | None:
    if path:
        return pathlib.Path(path).read_text(encoding="utf-8")
    local = REPO_ROOT / "DESIGN-LOG.md"
    if local.exists():
        return local.read_text(encoding="utf-8")
    try:
        return subprocess.run(["git", "show", f"{LOG_BRANCH}:DESIGN-LOG.md"], cwd=REPO_ROOT,
                              capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def check_against_log(rows: list[dict], text: str) -> None:
    log = {}
    for i, m in enumerate(ENTRY_RE.finditer(text), start=1):
        kv = dict(re.findall(r"(\w+)=(\S+)", m.group("meta")))
        head = HEAD_RE.search(text[m.end():]).group("head")
        sub = SUB_SLUG[kv["sub"]] if "sub" in kv else PR_SUBSYSTEM.get(kv.get("pr", "0"), "Other")
        log[f"e{i:03d}"] = (kv.get("date", "")[:10], NAME_RE.search(head).group("name"), sub)
    for r in rows:
        if r["entry"] not in log:
            raise SystemExit(f"{r['entry']} is not in DESIGN-LOG.md")
        date, title, sub = log[r["entry"]]
        if (r["date"], r["title"], r["log_subsystem"]) != (date, title, sub) \
                or FAMILY_OF_SUBSYSTEM.get(sub) != r["family"]:
            raise SystemExit(f"{r['entry']} does not match the log: {date}, {title!r}, {sub}")
    in_scope = {e for e, (_, _, sub) in log.items() if sub in FAMILY_OF_SUBSYSTEM}
    coded = {r["entry"] for r in rows}
    if in_scope != coded | set(EXCLUDED):
        raise SystemExit(f"uncoded part entries {sorted(in_scope - coded - set(EXCLUDED))}; "
                         f"coded or excluded entries outside the part subsystems "
                         f"{sorted((coded | set(EXCLUDED)) - in_scope)}")
    print(f"Checked against DESIGN-LOG.md: {len(log)} entries, {len(in_scope)} in the part "
          f"subsystems, {len(coded)} coded, {len(EXCLUDED)} excluded.")


def summarize(rows: list[dict]) -> dict:
    modellers, outcomes, types, catchers = Counter(), Counter(), Counter(), Counter()
    for r in rows:
        label = MODELLERS[r["modelled_by"]] or r["tool"].split(",")[0]
        modellers[label] += 1
        outcomes[OUTCOMES[r["outcome"]]] += 1
        for kind, catcher in r["failure_list"]:
            types[kind] += 1
            catchers[catcher] += 1
    return {
        "n": len(rows), "modellers": modellers, "outcomes": outcomes,
        "printed": sum(r["printed"] == "yes" for r in rows),
        "types": types, "catchers": catchers,
        "failed_entries": sum(bool(r["failure_list"]) for r in rows),
        "requirement": sum(r["requirement_changed"] == "yes" for r in rows),
    }


def counts_text(counter: Counter, labels: dict, main_only: bool = False) -> str:
    """'label n, label n' by descending count, ties in the order of ``labels``.

    With ``main_only``, a list of more than three types keeps the types seen at
    least twice and folds the rest into 'other n'.
    """
    order = list(labels)
    items = sorted((k for k in counter if counter[k]), key=lambda k: (-counter[k], order.index(k)))
    rest = [k for k in items if counter[k] < 2] if main_only and len(items) > 3 else []
    parts = [f"{labels[k]}~{counter[k]}" for k in items if k not in rest]
    if rest:
        parts.append(f"other~{sum(counter[k] for k in rest)}")
    return ", ".join(parts) or "none recorded"


def table_row(name: str, s: dict, main_only: bool = True) -> str:
    modelled = ", ".join(f"{k}~{v}" for k, v in sorted(s["modellers"].items(),
                                                     key=lambda kv: (kv[0] == "team", -kv[1])))
    cells = [ROW_LABEL.get(name, name), str(s["n"]), modelled, str(s["printed"])]
    cells += [str(s["outcomes"][c]) for c in "WIFSN"]
    cells += [str(sum(s["types"].values())),
              counts_text(s["types"], FAILURE_TYPES, main_only),
              counts_text(s["catchers"], CATCHERS) if s["catchers"] else "--"]
    return " & ".join(cells) + r" \\"


def build_tex(rows: list[dict]) -> str:
    total = summarize(rows)
    caption = (
        r"CAD entries in the design log, by part family. "
        r"Coding rules: an entry counts if it made or changed a 3D part model; each is coded from "
        r"its log text and linked thread, and each recorded defect is credited to what first "
        r"caught it. "
        rf"Excluded are {len(EXCLUDED)} entries that added no part model or repeat another entry, "
        r"and all electronics, firmware, test-rig, and design-tooling entries. "
        r"Agent, an AI coding agent; team, team members in Fusion~360 or Onshape. "
        r"W, worked; I, worked with issues; F, failed; S, superseded; N, not built, or printed but "
        r"untested (the multi-doser); S and N entries otherwise have no print on record. "
        r"Failure types follow Table~2 of the main text; family rows list the main ones. "
        r"Review, a person inspecting renders, slicer previews, or CAD; test, a print or bench "
        r"test; check, a mesh check or AI design review run by the agent. "
        rf"Revisions made for new requirements ({total['requirement']} entries) are not counted "
        r"as failures. "
        r"Some coding-agent revisions from June 2026 are missing from the log."
    )
    col = r">{\raggedright\arraybackslash}p"
    lines = [
        "% Generated by paper/figures/data/build_design_log_table.py -- do not edit by hand.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\small",
        rf"\caption{{{caption}}}",
        r"\label{tbl:designlog}",
        r"\setlength{\tabcolsep}{3pt}",
        rf"\begin{{tabular}}{{@{{}}{col}{{2.4cm}}r{col}{{1.8cm}}rrrrrrr{col}{{4.65cm}}{col}{{2.5cm}}@{{}}}}",
        r"\toprule",
        r" & & & & \multicolumn{5}{c}{Outcome} & \multicolumn{3}{c}{Failures} \\",
        r"\cmidrule(lr){5-9}\cmidrule(l){10-12}",
        r"Part family & Entries & Modelled by & Printed & W & I & F & S & N & $n$ & Types & Caught by \\",
        r"\midrule",
    ]
    for family in FAMILIES:
        lines.append(table_row(family, summarize([r for r in rows if r["family"] == family])))
    lines += [r"\midrule", table_row("Total", total, main_only=False), r"\bottomrule", r"\end{tabular}",
              r"\end{table}", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", help="path to DESIGN-LOG.md (default: repository root, then the PR #74 branch)")
    args = ap.parse_args()
    rows = load_rows()
    text = read_log(args.log)
    if text is None:
        print("DESIGN-LOG.md not found; skipping the check against the log.")
    else:
        check_against_log(rows, text)
    OUT_PATH.write_text(build_tex(rows), encoding="utf-8")
    t = summarize(rows)
    print(f"Wrote {OUT_PATH.name}: {t['n']} CAD entries, {t['printed']} printed, "
          f"{sum(t['types'].values())} failures in {t['failed_entries']} entries.")


if __name__ == "__main__":
    main()

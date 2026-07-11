#!/usr/bin/env python3
"""Regenerate the machine-derived sections of ``DESIGN-LOG.md`` in place.

``DESIGN-LOG.md`` is the hand-maintained source of truth: the per-entry prose
(Trigger / Design / Rationale / Outcome / images) is authored by hand. This
script only (re)generates the *deterministic* scaffolding around those entries
so the navigation never drifts from the content:

1. **YAML front-matter** — machine-readable summary (date span, entry count,
   per-subsystem counts, iteration-chain count).
2. **Index by subsystem** — a summary table grouping every entry by subsystem,
   plus the multi-version iteration chains rendered as ``v1 → v2 → …`` anchor
   links (each version is superseded by the next in its chain).
3. **Per-entry anchors** — a stable ``<a id="eNNN">`` before every heading so the
   index can deep-link to an exact iteration even though headings repeat dates.

Everything generated lives between explicit ``<!-- …:START -->`` /
``<!-- …:END -->`` markers (front-matter is delimited by ``---`` fences), so the
script is idempotent: running it twice produces no further changes.

Usage::

    python3 tools/design_log/build_design_log.py            # rewrite in place
    python3 tools/design_log/build_design_log.py --check    # CI: fail if stale
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections import Counter, OrderedDict

# This file lives at <repo>/tools/design_log/build_design_log.py, so the repo
# root is two parent levels up.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
LOG = REPO_ROOT / "DESIGN-LOG.md"

# Each pull request in this repository corresponds to one design subsystem, so the
# pr= tag on every entry is an authoritative subsystem signal (more reliable than
# parsing the free-text title). Issue-only entries use pr=0.
PR_SUBSYSTEM = {
    "0": "Scoop / excavator",
    "2": "Scoop / excavator",
    "5": "Scoop / excavator",
    "13": "Sieve-cup alternatives (A–H)",
    "16": "Auger",
    "25": "Electronics & PCB",
    "31": "Doser module",
    "35": "Doser module",
    "37": "Sealing cap",
    "45": "Electronics & PCB",
    "47": "Auger bracket",
    "49": "Auger",
    "51": "Tap collar",
    "53": "Auger bracket",
    "55": "Auger bracket",
    "57": "Mounting plate & hinge",
    "59": "Mounting plate & hinge",
    "61": "Electronics & PCB",
    "63": "Mounting plate & hinge",
    "66": "Mounting plate & hinge",
    "68": "Auger",
}

# Display order for the index.
SUBSYSTEM_ORDER = [
    "Scoop / excavator",
    "Sieve-cup alternatives (A–H)",
    "Auger",
    "Auger bracket",
    "Sealing cap",
    "Tap collar",
    "Doser module",
    "Mounting plate & hinge",
    "Electronics & PCB",
]

ENTRY_RE = re.compile(r"<!-- ENTRY (?P<meta>[^>]*?)-->\r?\n", re.S)
HEAD_RE = re.compile(r"^### (?P<head>.+)$", re.M)
ANCHOR_RE = re.compile(r'^<a id="e\d+"></a>\n', re.M)
NAME_RE = re.compile(r"—\s*(?P<name>.+?)\s*·")
VERSION_RE = re.compile(r"\s+v\d[\w.\-]*$")

FM_START, FM_END = "<!-- FRONTMATTER:START -->", "<!-- FRONTMATTER:END -->"
IDX_START, IDX_END = "<!-- INDEX:START -->", "<!-- INDEX:END -->"


class Entry:
    def __init__(self, meta: str, head: str, anchor: str):
        kv = dict(re.findall(r"(\w+)=(\S+)", meta))
        self.date = kv.get("date", "")
        self.pr = kv.get("pr", "0")
        self.head = head
        self.anchor = anchor
        nm = NAME_RE.search(head)
        self.name = nm.group("name") if nm else head
        self.base = VERSION_RE.sub("", self.name)
        self.subsystem = PR_SUBSYSTEM.get(self.pr, "Other")

    @property
    def day(self) -> str:
        return self.date[:10]

    @property
    def ref(self) -> str:
        # The reference suffix after the last "·" in the heading (e.g. "PR #16").
        return self.head.rsplit("·", 1)[-1].strip()


def parse_entries(text: str) -> list[Entry]:
    entries: list[Entry] = []
    for i, m in enumerate(ENTRY_RE.finditer(text), start=1):
        tail = text[m.end():]
        hm = HEAD_RE.search(tail)
        if not hm:
            raise ValueError(f"entry {i} has no '### ' heading")
        entries.append(Entry(m.group("meta"), hm.group("head"), f"e{i:03d}"))
    return entries


def insert_anchors(text: str) -> str:
    """Place ``<a id="eNNN"></a>`` directly after each ENTRY marker (idempotent)."""
    # Strip any anchors we previously inserted, then re-add in order.
    text = ANCHOR_RE.sub("", text)
    out: list[str] = []
    last = 0
    for i, m in enumerate(ENTRY_RE.finditer(text), start=1):
        out.append(text[last:m.end()])
        out.append(f'<a id="e{i:03d}"></a>\n')
        last = m.end()
    out.append(text[last:])
    return "".join(out)


def build_frontmatter(entries: list[Entry]) -> str:
    days = sorted(e.day for e in entries)
    counts = Counter(e.subsystem for e in entries)
    chains = OrderedDict()
    for e in entries:
        chains.setdefault((e.subsystem, e.base), []).append(e)
    n_chains = sum(1 for v in chains.values() if len(v) > 1)
    lines = [
        FM_START,
        "<!-- Machine-readable summary; regenerated by tools/design_log/build_design_log.py -->",
        "```yaml",
        'title: "Record of Designs"',
        "kind: design-log",
        f"entries: {len(entries)}",
        f"date_span: [{days[0]}, {days[-1]}]",
        f"iteration_chains: {n_chains}",
        "subsystems:",
    ]
    for s in SUBSYSTEM_ORDER:
        if counts.get(s):
            lines.append(f'  - name: "{s}"')
            lines.append(f"    entries: {counts[s]}")
    lines += ["```", FM_END]
    return "\n".join(lines)


def build_index(entries: list[Entry]) -> str:
    by_sub: "OrderedDict[str, list[Entry]]" = OrderedDict()
    for s in SUBSYSTEM_ORDER:
        by_sub[s] = []
    for e in entries:
        by_sub.setdefault(e.subsystem, []).append(e)

    out = [IDX_START, "## Index by subsystem", ""]
    out.append(
        "Designs are logged chronologically below, but iterations of one object are "
        "scattered across that timeline. This index regroups them. Within a multi-"
        "version **iteration chain** each version is superseded by the next "
        "(`v1 → v2 → …`); follow a link to jump to that exact iteration."
    )
    out.append("")
    out.append("| Subsystem | Entries | Iteration chains (oldest → newest) |")
    out.append("| --- | --: | --- |")
    for sub, items in by_sub.items():
        if not items:
            continue
        chains: "OrderedDict[str, list[Entry]]" = OrderedDict()
        for e in items:
            chains.setdefault(e.base, []).append(e)
        cells = []
        for base, versions in chains.items():
            if len(versions) > 1:
                links = " → ".join(
                    f"[{_ver_label(v)}](#{v.anchor})" for v in versions
                )
                cells.append(f"**{base}:** {links}")
            else:
                v = versions[0]
                cells.append(f"[{base}](#{v.anchor})")
        out.append(f"| {sub} | {len(items)} | " + "<br>".join(cells) + " |")
    out.append("")
    out.append(IDX_END)
    return "\n".join(out)


def _ver_label(e: Entry) -> str:
    """Short label for a chain link: the version token, or the day if none."""
    m = re.search(r"\bv\d[\w.\-]*$", e.name)
    return m.group(0) if m else e.day


def _replace_block(text: str, start: str, end: str, new: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pattern.search(text):
        return pattern.sub(lambda _m: new, text)
    raise ValueError(f"markers {start} .. {end} not found")


def render(text: str) -> str:
    text = insert_anchors(text)
    entries = parse_entries(text)
    text = _replace_block(text, FM_START, FM_END, build_frontmatter(entries))
    text = _replace_block(text, IDX_START, IDX_END, build_index(entries))
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if regeneration changes the file")
    args = ap.parse_args()

    original = LOG.read_text()
    updated = render(original)
    if args.check:
        if original != updated:
            print("DESIGN-LOG.md is stale; run tools/design_log/build_design_log.py", file=sys.stderr)
            return 1
        print("DESIGN-LOG.md is up to date.")
        return 0
    LOG.write_text(updated)
    n = len(parse_entries(updated))
    print(f"Regenerated DESIGN-LOG.md ({n} entries).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

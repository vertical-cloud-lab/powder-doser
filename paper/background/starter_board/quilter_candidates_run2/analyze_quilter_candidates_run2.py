#!/usr/bin/env python3
"""Evaluate the 2026-07-14 Quilter.ai candidate boards (run 2).

@lbwinters re-ran Quilter.ai on the post-audit ``test_module_unplaced`` trio
(110 x 110 mm outline, vendor-exact footprints, PR #100 scale integration,
JLC04161H-7628 4-layer *with power plane* preset, 10/6 mil rules, per-net
power currents) and uploaded six candidates (PR #76 comment, 2026-07-14).
Candidate 4's attachment link was malformed, so five are committed here.

This is the run-2 counterpart of ``../quilter_candidates/analyze_quilter_candidates.py``
(note ``22``), extended with the checks that matter for this run's settings:

* whether the per-net power currents produced wider copper (they did for
  ``+12V``/``GND`` -- 0.514 mm vs the 0.254 mm floor -- but not for ``+5V`` or
  the stepper/solenoid drive nets);
* which side each footprint landed on (the stackup's placement settings
  allowed ``BODY_DOWN`` on the bottom layer, and candidates 2/5 used it --
  impractical for this all-THT, top-access board);
* the systemic ``<no net>`` zone on ``In2.Cu`` ("Power Layer 2") whose fill
  touches only no-net PTH pads (the source of every clearance /
  hole_clearance DRC error).

Read-only; never modifies the candidate files.

Usage::

    python3 analyze_quilter_candidates_run2.py            # prints the table
    python3 analyze_quilter_candidates_run2.py --json out.json
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_NAME = "test_module_unplaced.kicad_pcb"
POWER_NETS = {"+12V", "+5V", "+3V3", "GND"}
DRIVE_NETS = {"STP_A1", "STP_A2", "STP_B1", "STP_B2", "SOL_A", "SOL_B",
              "VIB_A", "VIB_B"}

try:
    import pcbnew  # type: ignore

    HAVE_PCBNEW = True
except Exception:  # pragma: no cover - environment without KiCad
    HAVE_PCBNEW = False

from kiutils.board import Board
from kiutils.items.brditems import Segment, Via


def _candidate_dirs() -> list[str]:
    return sorted(
        d for d in glob.glob(os.path.join(HERE, "candidate_*"))
        if os.path.isfile(os.path.join(d, BOARD_NAME))
    )


def _ref(fp) -> str:
    for g in fp.graphicItems:
        if getattr(g, "type", None) == "reference":
            return g.text
    return "?"


def _geometry(path: str) -> dict:
    b = Board.from_file(path)
    xs: list[float] = []
    ys: list[float] = []
    for g in b.graphicItems:
        if getattr(g, "layer", None) == "Edge.Cuts" and hasattr(g, "start"):
            xs += [g.start.X, g.end.X]
            ys += [g.start.Y, g.end.Y]
    outline = (round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1)) if xs else None

    copper = [l.name for l in b.layers if l.type == "signal"]
    netname = {n.number: n.name for n in b.nets}
    zones = [
        (netname.get(z.net, str(z.net)) or "<no net>", tuple(z.layers))
        for z in b.zones
    ]

    length = 0.0
    nonet = 0
    vias = 0
    nseg = 0
    net_widths: dict[str, set[float]] = collections.defaultdict(set)
    for t in b.traceItems:
        if isinstance(t, Via):
            vias += 1
            continue
        if not isinstance(t, Segment):
            continue
        nseg += 1
        w = round(t.width, 3)
        length += math.dist((t.start.X, t.start.Y), (t.end.X, t.end.Y))
        net = t.net or 0
        if net == 0:
            nonet += 1
        nm = netname.get(net, "")
        if nm in POWER_NETS:
            net_widths["power:" + nm].add(w)
        elif nm in DRIVE_NETS:
            net_widths["drive"].add(w)
        else:
            net_widths["signal"].add(w)

    bottom_parts = sorted(_ref(fp) for fp in b.footprints if fp.layer == "B.Cu")
    return dict(
        outline=outline,
        copper_layers=copper,
        zones=zones,
        track_len_mm=round(length),
        vias=vias,
        no_net_tracks=nonet,
        n_tracks=nseg,
        widths_mm={k: sorted(v) for k, v in sorted(net_widths.items())},
        bottom_side_parts=bottom_parts,
    )


def _drc(path: str) -> dict:
    if not HAVE_PCBNEW:
        return {}
    board = pcbnew.LoadBoard(path)
    board.BuildConnectivity()
    unconnected = board.GetConnectivity().GetUnconnectedCount(True)
    with tempfile.NamedTemporaryFile("r", suffix=".rpt", delete=False) as fh:
        report = fh.name
    pcbnew.WriteDRCReport(board, report, pcbnew.EDA_UNITS_MILLIMETRES, True)
    buckets: collections.Counter = collections.Counter()
    nonet_zone_hits = 0
    with open(report) as fh:
        lines = fh.readlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("[") and "]:" in line:
            buckets[line[1 : line.index("]")]] += 1
        if "Zone [<no net>]" in line:
            nonet_zone_hits += 1
    os.unlink(report)
    return dict(unconnected=unconnected, drc=dict(buckets),
                drc_items_vs_no_net_zone=nonet_zone_hits)


def analyze() -> dict:
    out = {}
    for d in _candidate_dirs():
        key = os.path.basename(d)
        info = _geometry(os.path.join(d, BOARD_NAME))
        info.update(_drc(os.path.join(d, BOARD_NAME)))
        out[key] = info
    return out


def _print(results: dict) -> None:
    hdr = (f"{'candidate':12}{'len(mm)':9}{'vias':6}{'unconn':8}"
           f"{'clr+hole':10}{'silk':6}{'bottom parts':14}")
    print(hdr)
    print("-" * len(hdr))
    for k, v in results.items():
        drc = v.get("drc", {})
        clr = drc.get("clearance", 0) + drc.get("hole_clearance", 0)
        print(f"{k:12}"
              f"{v['track_len_mm']:<9}"
              f"{v['vias']:<6}"
              f"{v.get('unconnected', '?'):<8}"
              f"{clr:<10}"
              f"{drc.get('silk_overlap', 0):<6}"
              f"{len(v['bottom_side_parts']):<3}"
              f"{(' (' + ','.join(v['bottom_side_parts']) + ')') if v['bottom_side_parts'] else ''}")
    any_v = next(iter(results.values()))
    print()
    print(f"copper layers : {any_v['copper_layers']}")
    print(f"zones         : {any_v['zones']}")
    print(f"trace widths  : {any_v['widths_mm']}")
    if not HAVE_PCBNEW:
        print("\n(pcbnew not installed -> DRC/connectivity columns omitted)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", help="write the full result dict to this path")
    args = ap.parse_args()
    results = analyze()
    _print(results)
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(results, fh, indent=2, sort_keys=True)
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()

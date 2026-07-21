#!/usr/bin/env python3
"""Evaluate the six Quilter.ai auto-placed/-routed candidate boards.

@lbwinters uploaded the ``test_module_unplaced`` trio (the 100x100 mm staged
board from ``build_starter_board.py``) to Quilter.ai, which returned **six**
auto-placed-and-routed candidates
(PR #76 comment 4755682488). This script re-runs the visual + electrical
analysis that backs note ``22-quilter-routed-candidate-evaluation.md`` so the
ranking is reproducible.

For each ``candidate_N/test_module_unplaced.kicad_pcb`` it reports:

* board outline, copper-layer count and the inner-layer (plane) nets;
* routed track length, via count, and how much copper Quilter exported with
  **no net** assigned (``(net 0)`` segments -- a Quilter export quirk that
  drives the solder-mask-sliver DRC count);
* the track widths used on the power nets vs. the signal nets (Quilter does
  *not* honour the ``Power`` net-class 0.6 mm width recorded in the
  ``.kicad_pro``);
* a full KiCad DRC pass (``pcbnew.WriteDRCReport``) bucketed by violation type,
  plus the authoritative unconnected-ratsnest count.

``pcbnew`` (the KiCad 7 Python module) gives the authoritative connectivity /
DRC numbers; when it is not installed the script falls back to ``kiutils`` for
the geometry-only metrics. It is read-only -- it never modifies the candidate
files.

Usage::

    python3 analyze_quilter_candidates.py            # prints the table
    python3 analyze_quilter_candidates.py --json out.json
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


def _geometry(path: str) -> dict:
    """Outline, copper layers, track length / vias / no-net count, widths."""
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
    plane_nets = sorted(
        {netname.get(z.net, str(z.net)) if isinstance(z.net, int)
         else getattr(z.net, "name", str(z.net))
         for z in b.zones}
    )

    length = 0.0
    nonet = 0
    vias = 0
    pwr_w: list[float] = []
    sig_w: list[float] = []
    for t in b.traceItems:
        if isinstance(t, Via):
            vias += 1
            continue
        if not isinstance(t, Segment):
            continue
        w = round(t.width, 3)
        length += math.dist((t.start.X, t.start.Y), (t.end.X, t.end.Y))
        net = t.net or 0
        if net == 0:
            nonet += 1
        (pwr_w if netname.get(net, "") in POWER_NETS else sig_w).append(w)
    return dict(
        outline=outline,
        copper_layers=copper,
        plane_nets=plane_nets,
        track_len_mm=round(length),
        vias=vias,
        no_net_tracks=nonet,
        n_tracks=sum(1 for t in b.traceItems if isinstance(t, Segment)),
        power_width_mm=sorted(set(pwr_w)),
        signal_width_mm=sorted(set(sig_w)),
    )


def _drc(path: str) -> dict:
    """Authoritative KiCad DRC + connectivity (requires pcbnew)."""
    if not HAVE_PCBNEW:
        return {}
    board = pcbnew.LoadBoard(path)
    board.BuildConnectivity()
    unconnected = board.GetConnectivity().GetUnconnectedCount(True)
    with tempfile.NamedTemporaryFile("r", suffix=".rpt", delete=False) as fh:
        report = fh.name
    pcbnew.WriteDRCReport(board, report, pcbnew.EDA_UNITS_MILLIMETRES, True)
    buckets: collections.Counter = collections.Counter()
    with open(report) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("[") and "]:" in line:
                buckets[line[1:line.index("]")]] += 1
    os.unlink(report)
    return dict(unconnected=unconnected, drc=dict(buckets))


def analyze() -> dict:
    out = {}
    for d in _candidate_dirs():
        key = os.path.basename(d)
        info = _geometry(os.path.join(d, BOARD_NAME))
        info.update(_drc(os.path.join(d, BOARD_NAME)))
        out[key] = info
    return out


def _print(results: dict) -> None:
    hdr = (f"{'candidate':12}{'outline':10}{'cu':4}{'len(mm)':9}"
           f"{'vias':6}{'no-net':8}{'unconn':8}{'mask_brg':10}")
    print(hdr)
    print("-" * len(hdr))
    for k, v in results.items():
        drc = v.get("drc", {})
        print(f"{k:12}"
              f"{('%gx%g' % tuple(v['outline'])):10}"
              f"{len(v['copper_layers']):<4}"
              f"{v['track_len_mm']:<9}"
              f"{v['vias']:<6}"
              f"{v['no_net_tracks']:<8}"
              f"{v.get('unconnected', '?'):<8}"
              f"{drc.get('solder_mask_bridge', 0):<10}")
    # shared facts
    any_v = next(iter(results.values()))
    print()
    print(f"copper layers : {any_v['copper_layers']}")
    print(f"plane nets    : {any_v['plane_nets']}  (no dedicated power plane)")
    print(f"power widths  : {any_v['power_width_mm']} mm   "
          f"signal widths: {any_v['signal_width_mm']} mm")
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

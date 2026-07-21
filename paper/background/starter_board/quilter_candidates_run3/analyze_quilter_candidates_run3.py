#!/usr/bin/env python3
"""Evaluate the 2026-07-15 Quilter.ai candidate boards (run 3, with M4).

@lbwinters re-ran Quilter.ai on the regenerated ``test_module_unplaced``
trio at commit ``0683525`` -- the first upload carrying the **second
dispensing-angle servo** (``M4`` on Pico ``GP2``, net ``SERVO_SIG2``,
PR #66 dual-servo hinge / PR #100 rev C) -- and uploaded six candidates
(PR #76 comment, 2026-07-15).  All six links were valid this time.

Run-3 counterpart of ``../quilter_candidates_run2/analyze_quilter_candidates_run2.py``
(note ``24``), extended with the checks that matter for this run:

* an explicit **second-servo verification**: ``M4`` present with its 3 pads
  on ``+5V``/``GND``/``SERVO_SIG2``, and the routed ``SERVO_SIG2`` copper
  forming one connected component that reaches both the ``M4`` signal pad
  and the Pico's ``GP2`` pad (union-find over segments/vias/pads);
* a **full parts/netlist audit** against the upload trio in
  ``../test_module_unplaced.kicad_pcb`` (same refs, same per-ref net sets,
  same pad counts) so nothing was dropped or renamed by Quilter's export;
* bypass-cap proximity (C1->U1 VIN, C2->U2 VSYS, C3->U5 VIN), placement
  side, per-class trace widths, and the run-2 ``<no net>`` "Power Layer 2"
  zone check.

Read-only; never modifies the candidate files.

Usage::

    python3 analyze_quilter_candidates_run3.py            # prints the table
    python3 analyze_quilter_candidates_run3.py --json out.json
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


def _world_pad(fp, pad) -> tuple[float, float]:
    a = math.radians(-(fp.position.angle or 0.0))
    x, y = pad.position.X, pad.position.Y
    return (fp.position.X + (x * math.cos(a) - y * math.sin(a)),
            fp.position.Y + (x * math.sin(a) + y * math.cos(a)))


def _pad_net_map(path: str) -> dict:
    """{ref: sorted list of net names} + per-ref pad count, for the audit."""
    b = Board.from_file(path)
    netname = {n.number: n.name for n in b.nets}
    out: dict[str, dict] = {}
    for fp in b.footprints:
        ref = _ref(fp)
        nets = sorted({netname.get(p.net.number, "") for p in fp.pads
                       if p.net and netname.get(p.net.number, "")})
        out[ref] = {"pads": len(fp.pads), "nets": nets}
    return out


def _servo2_check(path: str) -> dict:
    """Verify M4 exists, carries the right nets, and SERVO_SIG2 copper
    physically connects the M4 signal pad to the Pico (U2) GP2 pad."""
    b = Board.from_file(path)
    netname = {n.number: n.name for n in b.nets}
    signum = next((n.number for n in b.nets if n.name == "SERVO_SIG2"), None)
    m4 = next((fp for fp in b.footprints if _ref(fp) == "M4"), None)
    if m4 is None or signum is None:
        return {"m4_present": m4 is not None,
                "servo_sig2_net": signum is not None, "routed": False}
    m4_nets = sorted({netname.get(p.net.number, "") for p in m4.pads if p.net})

    # union-find over SERVO_SIG2 copper (segments + vias) plus the two pads
    pts: list[tuple[float, float]] = []
    edges: list[tuple[int, int]] = []
    def add(x, y):
        pts.append((x, y))
        return len(pts) - 1
    for t in b.traceItems:
        if isinstance(t, Segment) and t.net == signum:
            edges.append((add(t.start.X, t.start.Y), add(t.end.X, t.end.Y)))
        elif isinstance(t, Via) and t.net == signum:
            add(t.position.X, t.position.Y)
    endpoints = {}
    for fp in b.footprints:
        ref = _ref(fp)
        for p in fp.pads:
            if p.net and p.net.number == signum:
                endpoints[ref] = add(*_world_pad(fp, p))
    parent = list(range(len(pts)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri
    for i, (xi, yi) in enumerate(pts):
        for j in range(i + 1, len(pts)):
            xj, yj = pts[j]
            if abs(xi - xj) <= 0.06 and abs(yi - yj) <= 0.06:
                union(i, j)
    for a2, b2 in edges:
        union(a2, b2)
    routed = ("M4" in endpoints and "U2" in endpoints
              and find(endpoints["M4"]) == find(endpoints["U2"]))
    return {"m4_present": True, "m4_pads": len(m4.pads),
            "m4_nets": m4_nets, "m4_layer": m4.layer,
            "sig2_segments": sum(1 for t in b.traceItems
                                 if isinstance(t, Segment) and t.net == signum),
            "routed_m4_to_gp2": routed}


def _cap_distances(path: str) -> dict:
    """Distance (mm) from each bulk cap's + pad to its assigned supply pin.

    C1 -> U1 VIN (+12V), C2 -> U2 VSYS (+5V), C3 -> U5 VIN (+12V): for each
    pair, the minimum distance between the cap's supply-net pad and the
    partner ref's pads on the same net.
    """
    b = Board.from_file(path)
    netname = {n.number: n.name for n in b.nets}
    pads_by_ref: dict[str, list[tuple[str, float, float]]] = {}
    for fp in b.footprints:
        ref = _ref(fp)
        for p in fp.pads:
            nm = netname.get(p.net.number, "") if p.net else ""
            if nm:
                pads_by_ref.setdefault(ref, []).append((nm, *_world_pad(fp, p)))
    out = {}
    for cap, partner, net in (("C1", "U1", "+12V"), ("C2", "U2", "+5V"),
                              ("C3", "U5", "+12V")):
        cp = [(x, y) for nm, x, y in pads_by_ref.get(cap, []) if nm == net]
        pp = [(x, y) for nm, x, y in pads_by_ref.get(partner, []) if nm == net]
        if cp and pp:
            out[f"{cap}->{partner}"] = round(min(
                math.dist(c, p) for c in cp for p in pp), 1)
    return out


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
    # reference pad->net map from the upload trio one directory up
    ref_board = os.path.join(HERE, "..", BOARD_NAME)
    ref_map = _pad_net_map(ref_board) if os.path.isfile(ref_board) else None

    out = {}
    for d in _candidate_dirs():
        key = os.path.basename(d)
        path = os.path.join(d, BOARD_NAME)
        info = _geometry(path)
        info.update(_drc(path))
        info["servo2"] = _servo2_check(path)
        info["cap_dist_mm"] = _cap_distances(path)
        if ref_map is not None:
            cand_map = _pad_net_map(path)
            missing = sorted(set(ref_map) - set(cand_map))
            extra = sorted(set(cand_map) - set(ref_map))
            diffs = {r: {"expected": ref_map[r], "got": cand_map[r]}
                     for r in ref_map if r in cand_map
                     and (ref_map[r]["nets"] != cand_map[r]["nets"]
                          or ref_map[r]["pads"] != cand_map[r]["pads"])}
            info["netlist_audit"] = {
                "missing_refs": missing, "extra_refs": extra,
                "mismatched_refs": diffs,
                "ok": not (missing or extra or diffs),
            }
        out[key] = info
    return out


def _print(results: dict) -> None:
    hdr = (f"{'candidate':12}{'len(mm)':9}{'vias':6}{'unconn':8}"
           f"{'clr+hole':10}{'silk':6}{'M4 ok':7}{'audit':7}{'bottom parts':14}")
    print(hdr)
    print("-" * len(hdr))
    for k, v in results.items():
        drc = v.get("drc", {})
        clr = drc.get("clearance", 0) + drc.get("hole_clearance", 0)
        s2 = v.get("servo2", {})
        m4ok = "yes" if s2.get("routed_m4_to_gp2") else "NO"
        audit = v.get("netlist_audit", {})
        audit_s = "ok" if audit.get("ok") else ("FAIL" if audit else "?")
        print(f"{k:12}"
              f"{v['track_len_mm']:<9}"
              f"{v['vias']:<6}"
              f"{v.get('unconnected', '?'):<8}"
              f"{clr:<10}"
              f"{drc.get('silk_overlap', 0):<6}"
              f"{m4ok:<7}"
              f"{audit_s:<7}"
              f"{len(v['bottom_side_parts']):<3}"
              f"{(' (' + ','.join(v['bottom_side_parts']) + ')') if v['bottom_side_parts'] else ''}")
    any_v = next(iter(results.values()))
    print()
    print(f"copper layers : {any_v['copper_layers']}")
    print(f"zones         : {any_v['zones']}")
    print(f"trace widths  : {any_v['widths_mm']}")
    print("cap distances (C->supply pin, mm):")
    for k, v in results.items():
        print(f"  {k}: {v.get('cap_dist_mm')}")
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

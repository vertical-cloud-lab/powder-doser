#!/usr/bin/env python3
"""ngspice power-distribution (IR-drop) simulation of the run-2 Quilter candidates.

Run-2 counterpart of ``../quilter_candidates/simulate_power_ngspice.py``
(note ``23``), updated for the 2026-07-14 candidates, which come from the
post-audit board with the PR #100 scale integration:

* the RS-232 module is ``U6`` and is powered from ``+3V3`` (not the old ``J2``
  on ``+5V``), so a third simulated net ``+3V3`` (sourced at the Pico's
  onboard regulator output) replaces the old J2 load;
* this run's boards carry real net assignments on every segment (the run-1
  ``(net 0)`` export quirk is gone), but the connected-component recovery is
  kept -- it independently re-confirms there are no shorts
  (``foreign_nets_on_copper`` must stay empty);
* the IPC-2221 temperature rise is computed at the *actual* minimum routed
  trace width of each net's copper (run 1 hard-coded the 6 mil width every
  trace had back then; this run routes +12V/GND at 0.514 mm and the rest at
  0.254 mm).

Model, constants, and method are otherwise identical to note ``23``:
each routed segment becomes ``R = rho*L/(W*t)`` (1 oz copper), endpoints are
clustered into electrical nodes, ngspice solves the ``.op`` IR-drop with
worst-case load currents, and a ``.tran`` checks the +12 V solenoid rail
under a PWM pulse against the bulk cap.

Usage::

    python3 simulate_power_ngspice_run2.py                 # prints the table
    python3 simulate_power_ngspice_run2.py --json out.json
    python3 simulate_power_ngspice_run2.py --decks decks/  # also dump .cir files
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import shutil
import subprocess
import tempfile

from kiutils.board import Board
from kiutils.items.brditems import Segment, Via

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_NAME = "test_module_unplaced.kicad_pcb"

# --- physical constants (identical to note 23) -------------------------------
RHO_CU = 1.724e-8           # copper resistivity, ohm*m (20 C)
T_CU = 35e-6                # 1 oz finished copper thickness, m
NODE_TOL = 0.06             # endpoint-clustering tolerance, mm
# (vias are modelled as ideal layer bridges; a real barrel is ~1 mohm, well
#  below the trace resistances solved here)

# Transient decoupling model (board-level, +12V solenoid rail).
C_BULK = 100e-6             # bulk electrolytic on +12V (C3, assumed 100 uF)
ESR_BULK = 0.5              # bulk-cap equivalent series resistance, ohm
SOL_PULSE_A = 0.65          # solenoid current pulse amplitude, A
SOL_FREQ = 1000.0           # solenoid PWM frequency, Hz (DRV8871 drive)

# Supply reference for each simulated power net (the pad on this ref that
# carries the net is the source node):
#   +12 V enters at the barrel jack J1; +5 V is the buck (U1) output;
#   +3V3 is the Pico W's onboard regulator output (U2).
SOURCES = {
    "+12V": "J1",
    "+5V": "U1",
    "+3V3": "U2",
}

# Representative worst-case load currents (A) drawn at each consumer's pad.
# Same provenance as note 23, updated for the PR #100 netlist (U6 RS-232
# module on +3V3; the spare RS-232 channel and old J2 receptacle are gone).
LOADS = {
    "+12V": {
        "U4": 0.65,   # DRV8871 -> Adafruit 412 / TAU0730TM tap solenoid, ~12 V/18 ohm
        "U5": 1.00,   # Tic T500 -> stepper coil rail (current-limited)
        "U1": 0.30,   # buck input current (reflects the +5 V system load)
    },
    "+5V": {
        "M3": 0.75,   # servo header (near-stall transient)
        "U2": 0.15,   # Raspberry Pi Pico W VSYS (Wi-Fi active)
    },
    "+3V3": {
        "U3": 0.25,   # DRV2605L VIN incl. ERM overdrive peaks
        "U6": 0.05,   # Waveshare RS-232 module (SP3232EEN + charge pump + LEDs)
    },
}

SUPPLY_V = {"+12V": 12.0, "+5V": 5.0, "+3V3": 3.3}


def _candidate_dirs() -> list[str]:
    return sorted(
        d for d in glob.glob(os.path.join(HERE, "candidate_*"))
        if os.path.isfile(os.path.join(d, BOARD_NAME))
    )


def _world_pad(fp, pad) -> tuple[float, float]:
    """Footprint-local pad coordinate -> board coordinate."""
    a = math.radians(-(fp.position.angle or 0.0))
    x, y = pad.position.X, pad.position.Y
    wx = fp.position.X + (x * math.cos(a) - y * math.sin(a))
    wy = fp.position.Y + (x * math.sin(a) + y * math.cos(a))
    return wx, wy


def _ref(fp) -> str:
    for g in fp.graphicItems:
        if getattr(g, "type", None) == "reference":
            return g.text
    return "?"


class _Nodes:
    """Layer-aware electrical nodes clustered within NODE_TOL mm.

    Each point carries the copper layer it lives on; ``'*'`` (a via or a
    through-hole pad) spans every layer.  Two points merge only when they are
    coincident in X/Y *and* layer-compatible (same layer, or either is
    ``'*'``) -- so traces crossing on opposite layers stay separate, and only
    a via/THT pad bridges them (union-find keeps that transitive).
    """

    def __init__(self) -> None:
        self.pts: list[tuple[float, float, str]] = []
        self._parent: list[int] = []

    def add(self, x: float, y: float, layer: str) -> int:
        self.pts.append((x, y, layer))
        self._parent.append(len(self.pts) - 1)
        return len(self.pts) - 1

    def find(self, i: int) -> int:
        while self._parent[i] != i:
            self._parent[i] = self._parent[self._parent[i]]
            i = self._parent[i]
        return i

    def union(self, i: int, j: int) -> None:
        ri, rj = self.find(i), self.find(j)
        if ri != rj:
            self._parent[rj] = ri

    def cluster(self) -> None:
        pts = self.pts
        for i in range(len(pts)):
            xi, yi, li = pts[i]
            for j in range(i + 1, len(pts)):
                xj, yj, lj = pts[j]
                if (abs(xi - xj) <= NODE_TOL and abs(yi - yj) <= NODE_TOL
                        and (li == lj or li == "*" or lj == "*")):
                    self.union(i, j)


def _seg_resistance(length_mm: float, width_mm: float) -> float:
    return RHO_CU * (length_mm * 1e-3) / (width_mm * 1e-3 * T_CU)


def _ipc2221_temp_rise(current_a: float, width_mm: float,
                       thickness_um: float = 35.0) -> float:
    """External-layer copper temperature rise (deg C), IPC-2221 curve fit."""
    width_mil = width_mm / 0.0254
    thickness_mil = thickness_um / 25.4
    area = width_mil * thickness_mil
    k = 0.048
    return (current_a / (k * area ** 0.725)) ** (1.0 / 0.44)


def _build_graph(board: Board, bridge_module_pads: bool = True):
    """Cluster ALL routed copper into a node graph.

    Run-1's builder only merged *endpoints*, which misses Quilter's
    T-junctions (a trace ending in the middle of another segment) -- in this
    run that left candidate 5's Tic +12 V pad looking unreachable even though
    ``pcbnew`` connectivity is complete.  Each segment is therefore split at
    every node that lies on its copper (within half the trace width), and the
    chain ``end -> tee -> ... -> end`` gets proportional resistances.

    Returns ``(nodes, resistors, pads, seg_widths)`` where ``resistors`` is a
    list of ``(na, nb, ohm)``, ``pads`` a list of ``(ref, net_name, node)``
    and ``seg_widths`` maps a resistor index to the segment width (mm).
    """
    netname = {n.number: n.name for n in board.nets}
    nodes = _Nodes()
    segs: list[tuple[int, int, float, float, float, float, float, str]] = []
    for t in board.traceItems:
        if isinstance(t, Segment):
            na = nodes.add(t.start.X, t.start.Y, t.layer)
            nb = nodes.add(t.end.X, t.end.Y, t.layer)
            segs.append((na, nb, t.start.X, t.start.Y,
                         t.end.X, t.end.Y, t.width, t.layer))
        elif isinstance(t, Via):
            nodes.add(t.position.X, t.position.Y, "*")
    raw_pads: list[tuple[str, str, int]] = []
    for fp in board.footprints:
        ref = _ref(fp)
        for pad in fp.pads:
            nm = netname.get(pad.net.number if pad.net else 0, "")
            wx, wy = _world_pad(fp, pad)
            span = "*" if any("*" in l for l in (pad.layers or [])) else fp.layer
            raw_pads.append((ref, nm, nodes.add(wx, wy, span)))
    nodes.cluster()
    if bridge_module_pads:
        # Same-net pads of one footprint are physically connected by the
        # component itself (e.g. SR1's duplicate VIN access holes share the
        # Pololu carrier's copper pour) -- KiCad connectivity assumes this
        # too.  Union them so through-module continuity is modelled; the
        # un-bridged graph is used separately to *detect* nets that rely on
        # it (see _net_module_bridges).
        groups: dict[tuple[str, str], list[int]] = {}
        for ref, nm, n in raw_pads:
            if nm:
                groups.setdefault((ref, nm), []).append(n)
        for members in groups.values():
            for other in members[1:]:
                nodes.union(members[0], other)

    resistors: list[tuple[int, int, float]] = []
    seg_widths: dict[int, float] = {}
    for na, nb, x1, y1, x2, y2, width, layer in segs:
        seg_len = math.dist((x1, y1), (x2, y2))
        if seg_len == 0.0:
            continue
        dx, dy = x2 - x1, y2 - y1
        # nodes sitting on this segment's copper (T-junctions / mid-trace pads)
        tees: list[tuple[float, int]] = []
        tol = width / 2 + NODE_TOL
        ra, rb = nodes.find(na), nodes.find(nb)
        for k, (px, py, kl) in enumerate(nodes.pts):
            rk = nodes.find(k)
            if rk in (ra, rb) or (kl != layer and kl != "*"):
                continue
            s = ((px - x1) * dx + (py - y1) * dy) / (seg_len * seg_len)
            if not 0.0 < s < 1.0:
                continue
            if math.dist((px, py), (x1 + s * dx, y1 + s * dy)) <= tol:
                tees.append((s, rk))
        chain = [(0.0, ra)] + sorted(tees) + [(1.0, rb)]
        for (sa, ka), (sb, kb) in zip(chain, chain[1:]):
            if ka == kb:
                continue
            seg_widths[len(resistors)] = width
            resistors.append(
                (ka, kb, _seg_resistance(seg_len * (sb - sa), width)))
    pads = [(ref, nm, nodes.find(n)) for ref, nm, n in raw_pads]
    return nodes, resistors, pads, seg_widths


def _net_module_bridges(nobridge_graph, net: str) -> list[str]:
    """Refs whose own body is the only continuity on ``net``'s copper.

    Built from the graph *without* same-footprint pad unions: if one ref's
    same-net pads land in different copper components, the routed copper
    relies on the module's internal link (e.g. candidate 5 feeds the Tic's
    +12 V through SR1's carrier pour).
    """
    nodes, resistors, pads, _ = nobridge_graph
    adj: dict[int, list[int]] = {}
    for na, nb, _r in resistors:
        if na != nb:
            adj.setdefault(na, []).append(nb)
            adj.setdefault(nb, []).append(na)
    label: dict[int, int] = {}
    def comp_of(start: int) -> int:
        if start in label:
            return label[start]
        cid = start
        stack = [start]
        label[start] = cid
        while stack:
            u = stack.pop()
            for v in adj.get(u, ()):
                if v not in label:
                    label[v] = cid
                    stack.append(v)
        return cid
    by_ref: dict[str, set[int]] = {}
    for ref, nm, n in pads:
        if nm == net:
            by_ref.setdefault(ref, set()).add(comp_of(n))
    return sorted(r for r, comps in by_ref.items() if len(comps) > 1)


def _component(resistors, start: int) -> set[int]:
    adj: dict[int, list[int]] = {}
    for na, nb, _ in resistors:
        if na == nb:
            continue
        adj.setdefault(na, []).append(nb)
        adj.setdefault(nb, []).append(na)
    seen = {start}
    stack = [start]
    while stack:
        u = stack.pop()
        for v in adj.get(u, ()):
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def _emit_deck(net: str, supply_v: float, src_node: int,
               loads: dict[int, float], resistors: list[tuple[int, int, float]],
               probes: dict[str, int]) -> str:
    lines = [f"* ngspice power IR-drop deck for {net} (run 2)"]
    for i, (na, nb, r) in enumerate(resistors):
        if na == nb:
            continue
        lines.append(f"R{i} c{na} c{nb} {r:.6e}")
    lines.append(f"Vsup c{src_node} 0 {supply_v}")
    for j, (node, cur) in enumerate(loads.items()):
        lines.append(f"Iload{j} c{node} 0 {cur:.4f}")
    lines.append(".op")
    lines.append(".control")
    lines.append("run")
    for name, node in probes.items():
        lines.append(f'print v(c{node})')
    lines.append(".endc")
    lines.append(".end")
    return "\n".join(lines) + "\n"


def _run_ngspice(deck: str) -> dict[str, float] | None:
    if not shutil.which("ngspice"):
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as fh:
        fh.write(deck)
        path = fh.name
    try:
        out = subprocess.run(["ngspice", "-b", path], capture_output=True,
                             text=True, timeout=120).stdout
    finally:
        os.unlink(path)
    volts: dict[str, float] = {}
    for m in re.finditer(r"v\(c(\d+)\)\s*=\s*([-\d.eE+]+)", out):
        volts[f"c{m.group(1)}"] = float(m.group(2))
    return volts


def _transient_sag(r_feed: float) -> dict | None:
    """ngspice .tran of the +12V solenoid rail under a PWM current pulse."""
    if not shutil.which("ngspice"):
        return None
    period = 1.0 / SOL_FREQ
    deck = f"""* +12V solenoid-rail transient decoupling check (run 2)
Vsup nsrc 0 12
Rfeed nsrc nrail {r_feed:.6e}
Cbulk nrail nc {C_BULK:.3e}
Resr  nc 0 {ESR_BULK:.3e}
Iload nrail 0 PULSE(0 {SOL_PULSE_A} 1u 1u 1u {period/2:.3e} {period:.3e})
.tran 1u {period*3:.3e}
.control
run
meas tran vmin MIN v(nrail)
meas tran vmax MAX v(nrail)
.endc
.end
"""
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as fh:
        fh.write(deck)
        path = fh.name
    try:
        out = subprocess.run(["ngspice", "-b", path], capture_output=True,
                             text=True, timeout=120).stdout
    finally:
        os.unlink(path)
    vmin = vmax = None
    for m in re.finditer(r"vmin\s*=\s*([-\d.eE+]+)", out):
        vmin = float(m.group(1))
    for m in re.finditer(r"vmax\s*=\s*([-\d.eE+]+)", out):
        vmax = float(m.group(1))
    if vmin is None or vmax is None:
        return {"deck": deck}
    return {
        "rail_min_v": round(vmin, 4),
        "rail_max_v": round(vmax, 4),
        "droop_mv": round((vmax - vmin) * 1e3, 2),
        "deck": deck,
    }


def _simulate_net(net: str, graph, nobridge_graph=None) -> dict:
    supply_v = SUPPLY_V[net]
    nodes, resistors, pads, seg_widths = graph
    src_ref = SOURCES[net]

    src_nodes = [n for ref, nm, n in pads if ref == src_ref and nm == net]
    if not src_nodes:
        return {"error": f"supply ref {src_ref} not on {net}"}
    src_node = src_nodes[0]

    comp = _component(resistors, src_node)
    comp_idx = [i for i, (a, b, r) in enumerate(resistors)
                if a in comp and b in comp and a != b]
    comp_res = [resistors[i] for i in comp_idx]
    min_w = min((seg_widths[i] for i in comp_idx if i in seg_widths),
                default=0.254)

    # short check: a foreign *named* net sharing this copper component is a
    # real short (DRC says there are none, so this must stay empty).
    foreign = sorted({nm for ref, nm, n in pads
                      if n in comp and nm not in ("", net)})

    loads_by_node: dict[int, float] = {}
    probe_ref: dict[str, int] = {}
    missing: list[str] = []
    for ref, cur in LOADS[net].items():
        ref_nodes = [n for r, nm, n in pads if r == ref and nm == net]
        if ref_nodes and ref_nodes[0] in comp:
            node = ref_nodes[0]
            loads_by_node[node] = loads_by_node.get(node, 0.0) + cur
            probe_ref[ref] = node
        else:
            missing.append(ref)
    probe_ref[src_ref] = src_node

    deck = _emit_deck(net, supply_v, src_node, loads_by_node, comp_res, probe_ref)
    volts = _run_ngspice(deck)

    result = {
        "supply_v": supply_v,
        "n_segments": len(comp_res),
        "n_nodes": len(comp),
        "min_trace_width_mm": round(min_w, 3),
        "loads_a": {r: LOADS[net][r] for r in probe_ref if r in LOADS[net]},
        "unreached_loads": missing,
        "foreign_nets_on_copper": foreign,
        "module_internal_bridges": (
            _net_module_bridges(nobridge_graph, net) if nobridge_graph else []),
        "deck": deck,
    }
    if volts is None:
        result["ngspice"] = "not installed"
        return result

    drops = {}
    vsrc = volts.get(f"c{src_node}", supply_v)
    for ref, node in probe_ref.items():
        if ref == src_ref:
            continue
        vnode = volts.get(f"c{node}")
        if vnode is not None:
            drops[ref] = round((vsrc - vnode) * 1e3, 2)  # mV
    result["v_supply_pad"] = round(vsrc, 4)
    result["ir_drop_mv"] = drops
    if drops:
        worst = max(drops, key=lambda k: drops[k])
        result["worst_load"] = worst
        result["worst_drop_mv"] = drops[worst]
        cur = LOADS[net][worst]
        result["worst_temp_rise_c"] = round(_ipc2221_temp_rise(cur, min_w), 1)
        result["worst_current_a"] = cur
        if net == "+12V" and "U4" in drops:
            r_feed = (drops["U4"] * 1e-3) / LOADS[net]["U4"]
            tran = _transient_sag(r_feed)
            if tran:
                result["solenoid_feed_ohm"] = round(r_feed, 4)
                result["transient"] = {k: v for k, v in tran.items()
                                       if k != "deck"}
    return result


def simulate() -> dict:
    out = {}
    for d in _candidate_dirs():
        key = os.path.basename(d)
        board = Board.from_file(os.path.join(d, BOARD_NAME))
        graph = _build_graph(board)
        nobridge = _build_graph(board, bridge_module_pads=False)
        out[key] = {net: _simulate_net(net, graph, nobridge)
                    for net in SOURCES}
    return out


def _print(results: dict) -> None:
    hdr = (f"{'candidate':12}{'net':7}{'segs':6}{'minW':7}"
           f"{'worst load':12}{'I(A)':7}{'IR drop':11}{'dT(C)':7}")
    print(hdr)
    print("-" * len(hdr))
    for cand, nets in results.items():
        for net, r in nets.items():
            if "worst_drop_mv" in r:
                print(f"{cand:12}{net:7}{r['n_segments']:<6}"
                      f"{r['min_trace_width_mm']:<7}"
                      f"{r['worst_load']:12}{r['worst_current_a']:<7}"
                      f"{str(r['worst_drop_mv']) + ' mV':11}"
                      f"{r.get('worst_temp_rise_c', '?'):<7}")
            else:
                print(f"{cand:12}{net:7}  {r.get('ngspice', r.get('error', '?'))}")
    print("\nIR drop = supply-pad to worst-case load-pad voltage on the routed "
          "copper (ngspice .op resistor-mesh solve).")
    print("dT(C)   = IPC-2221 external-layer temperature rise at the load "
          "current on the net's minimum routed trace width (minW, mm).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", help="write the full result dict to this path")
    ap.add_argument("--decks", help="also write each ngspice .cir to this dir")
    args = ap.parse_args()
    if not shutil.which("ngspice"):
        print("WARNING: ngspice not found on PATH; printing decks / bounds only.\n")
    results = simulate()
    _print(results)
    if args.decks:
        os.makedirs(args.decks, exist_ok=True)
        for cand, nets in results.items():
            for net, r in nets.items():
                fn = os.path.join(args.decks, f"{cand}_{net.strip('+')}.cir")
                with open(fn, "w") as fh:
                    fh.write(r.get("deck", ""))
        print(f"\nwrote decks to {args.decks}")
    if args.json:
        slim = {c: {n: {k: v for k, v in r.items() if k != "deck"}
                    for n, r in nets.items()}
                for c, nets in results.items()}
        with open(args.json, "w") as fh:
            json.dump(slim, fh, indent=2, sort_keys=True)
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()

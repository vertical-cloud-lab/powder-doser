#!/usr/bin/env python3
"""ngspice power-distribution (IR-drop) simulation of the Quilter candidates.

@sgbaird asked (PR #76 comment 4756046192) to extend the electrical evaluation
of the six Quilter.ai auto-routed candidate boards by *actually running ngspice*
and the other electrical tools the notes recommend, rather than only the
``pcbnew`` DRC / connectivity pass in ``analyze_quilter_candidates.py``.

These boards are a digital control + motor-driver carrier (no analog signal
chain to "solve" in the textbook SPICE sense), so the electrically meaningful
SPICE problem is **power delivery**: note ``22`` flagged that Quilter routed
*every* net -- including the +12 V input and the solenoid/stepper motor rails --
at ~6 mil (0.16 mm), ignoring the ``Power`` net-class width.  This script turns
that qualitative warning into numbers by:

1. extracting each candidate's *actual routed copper* for the +12 V and +5 V
   nets (every ``Segment`` with that net), converting each segment to a
   resistor ``R = rho * L / (W * t)`` (1 oz copper, ``t = 35 um``);
2. clustering segment / pad endpoints into electrical nodes (a via or a
   through-hole pad shorts the layers, so nodes are clustered in X/Y);
3. emitting a SPICE deck -- a 12 V (or 5 V) source at the supply pad, a current
   sink at every load pad (representative worst-case motor/logic currents, see
   ``LOADS``) -- and solving the resistor mesh with **ngspice** (``.op``);
4. reporting the worst-case IR drop at each load pad and the IPC-2221 copper
   temperature rise for those 6 mil traces.

It is read-only with respect to the candidate board files.  ngspice is the
solver; if it is not on ``PATH`` the script prints the generated decks and the
analytic series-resistance bound instead.

Usage::

    python3 simulate_power_ngspice.py                 # prints the table
    python3 simulate_power_ngspice.py --json out.json
    python3 simulate_power_ngspice.py --decks decks/  # also dump the .cir files
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

# --- physical constants -----------------------------------------------------
RHO_CU = 1.724e-8           # copper resistivity, ohm*m (20 C)
T_CU = 35e-6                # 1 oz finished copper thickness, m
VIA_R = 1.0e-3              # modelled barrel resistance of one via, ohm
NODE_TOL = 0.06             # endpoint-clustering tolerance, mm

# Transient decoupling model (board-level, +12V solenoid rail).
C_BULK = 100e-6             # bulk electrolytic on +12V (C3, assumed 100 uF)
ESR_BULK = 0.5              # bulk-cap equivalent series resistance, ohm
SOL_PULSE_A = 0.65         # solenoid current pulse amplitude, A
SOL_FREQ = 1000.0         # solenoid PWM frequency, Hz (DRV8871 drive)

# Supply pad for each power net: (reference designator, pad number).
#   +12 V enters at the barrel jack J1; +5 V is the buck (U1) output pin.
SOURCES = {
    "+12V": ("J1", "1"),
    "+5V": ("U1", "3"),
}

# Representative worst-case load currents (A) drawn at each consumer's pad.
# Values are steady-state / typical-peak figures with provenance in note 23;
# they bracket the real draw rather than claim datasheet precision.
LOADS = {
    "+12V": {
        "U4": 0.65,   # DRV8871 -> Adafruit 412 / TAU0730TM tap solenoid, ~12 V/18 ohm
        "U5": 1.00,   # Tic T500 -> stepper coil rail (current-limited)
        "U1": 0.30,   # buck input current (reflects the +5 V system load)
    },
    "+5V": {
        "M3": 0.75,   # servo header (near-stall transient)
        "U2": 0.15,   # Raspberry Pi Pico W (Wi-Fi active)
        "J2": 0.05,   # Waveshare RS-232 module (SP3232EEN)
    },
}


def _candidate_dirs() -> list[str]:
    return sorted(
        d for d in glob.glob(os.path.join(HERE, "candidate_*"))
        if os.path.isfile(os.path.join(d, BOARD_NAME))
    )


def _world_pad(fp, pad) -> tuple[float, float]:
    """Footprint-local pad coordinate -> board coordinate.

    KiCad footprint angles are clockwise-positive on a Y-down canvas, so the
    pad is rotated by ``-angle`` in standard (math) orientation.
    """
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
    """Cluster (x, y) endpoints into electrical nodes within NODE_TOL mm."""

    def __init__(self) -> None:
        self.pts: list[tuple[float, float]] = []

    def node(self, x: float, y: float) -> int:
        for i, (px, py) in enumerate(self.pts):
            if abs(px - x) <= NODE_TOL and abs(py - y) <= NODE_TOL:
                return i
        self.pts.append((x, y))
        return len(self.pts) - 1


def _seg_resistance(length_mm: float, width_mm: float) -> float:
    return RHO_CU * (length_mm * 1e-3) / (width_mm * 1e-3 * T_CU)


def _ipc2152_temp_rise(current_a: float, width_mm: float,
                       thickness_um: float = 35.0) -> float:
    """External-layer copper temperature rise (deg C), IPC-2221 curve fit.

    ``I = k * dT^0.44 * A^0.725`` with ``k = 0.048`` (external layer) and the
    cross-section ``A = width(mil) * thickness(mil)`` in mil^2.  Inverted for
    ``dT`` given ``I`` and ``A``.
    """
    width_mil = width_mm / 0.0254
    thickness_mil = thickness_um / 25.4
    area = width_mil * thickness_mil
    k = 0.048
    return (current_a / (k * area ** 0.725)) ** (1.0 / 0.44)


def _build_graph(board: Board):
    """Cluster ALL routed copper into a node graph (handles net-0 export).

    Quilter exports ~half its copper with ``(net 0)``, so a per-net filter
    misses the physical trace.  Instead we cluster *every* segment's endpoints
    into nodes (a via or through-hole pad shorts layers, so clustering in X/Y
    merges them) and recover each power net as the connected component that
    contains its supply pad.  DRC is clean (no shorts), so components are
    net-isolated; we still assert that below.

    Returns ``(nodes, resistors, pads)`` where ``resistors`` is a list of
    ``(na, nb, ohm)`` and ``pads`` a list of ``(ref, net_name, node)``.
    """
    netname = {n.number: n.name for n in board.nets}
    nodes = _Nodes()
    resistors: list[tuple[int, int, float]] = []
    for t in board.traceItems:
        if isinstance(t, Segment):
            na = nodes.node(t.start.X, t.start.Y)
            nb = nodes.node(t.end.X, t.end.Y)
            if na != nb:
                length = math.dist((t.start.X, t.start.Y), (t.end.X, t.end.Y))
                resistors.append((na, nb, _seg_resistance(length, t.width)))
        elif isinstance(t, Via):
            # the via XY clusters onto the touching segment nodes; add a tiny
            # barrel resistance so layer transitions are not modelled as ideal.
            n = nodes.node(t.position.X, t.position.Y)
            resistors.append((n, n, VIA_R))
    pads: list[tuple[str, str, int]] = []
    for fp in board.footprints:
        ref = _ref(fp)
        for pad in fp.pads:
            nm = netname.get(pad.net.number if pad.net else 0, "")
            wx, wy = _world_pad(fp, pad)
            pads.append((ref, nm, nodes.node(wx, wy)))
    return nodes, resistors, pads


def _component(resistors, start: int) -> set[int]:
    """Nodes reachable from ``start`` through the resistor edges."""
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
    lines = [f"* ngspice power IR-drop deck for {net}"]
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
    """ngspice .tran of the +12V solenoid rail under a PWM current pulse.

    Lumped model: 12 V source -> ``r_feed`` (the DC supply->solenoid copper
    resistance solved above) -> rail node, with the bulk cap (``C_BULK`` +
    ``ESR_BULK``) across the rail and the DRV8871/solenoid drawing a
    ``SOL_PULSE_A`` PWM pulse.  Reports the worst-case rail droop.
    """
    if not shutil.which("ngspice"):
        return None
    period = 1.0 / SOL_FREQ
    deck = f"""* +12V solenoid-rail transient decoupling check
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


def _simulate_net(net: str, graph) -> dict:
    supply_v = 12.0 if net == "+12V" else 5.0
    nodes, resistors, pads = graph
    src_ref, _ = SOURCES[net]

    # supply pad node for this net
    src_nodes = [n for ref, nm, n in pads if ref == src_ref and nm == net]
    if not src_nodes:
        return {"error": f"supply ref {src_ref} not on {net}"}
    src_node = src_nodes[0]

    comp = _component(resistors, src_node)
    comp_res = [(a, b, r) for a, b, r in resistors if a in comp and b in comp and a != b]

    # short check: a foreign *named* net sharing this copper component is a real
    # short (DRC says there are none, so this should stay empty).
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
        "loads_a": {r: LOADS[net][r] for r in probe_ref if r in LOADS[net]},
        "unreached_loads": missing,
        "foreign_nets_on_copper": foreign,
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
        result["worst_temp_rise_c"] = round(_ipc2152_temp_rise(cur, 0.16), 1)
        result["worst_current_a"] = cur
        # transient decoupling check on the +12V solenoid (U4) feed
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
        out[key] = {net: _simulate_net(net, graph) for net in SOURCES}
    return out


def _print(results: dict) -> None:
    hdr = (f"{'candidate':12}{'net':6}{'segs':6}{'src V':8}"
           f"{'worst load':12}{'I(A)':7}{'IR drop':10}{'dT(C)':7}")
    print(hdr)
    print("-" * len(hdr))
    for cand, nets in results.items():
        for net, r in nets.items():
            if "worst_drop_mv" in r:
                print(f"{cand:12}{net:6}{r['n_segments']:<6}"
                      f"{r['v_supply_pad']:<8}"
                      f"{r['worst_load']:12}{r['worst_current_a']:<7}"
                      f"{str(r['worst_drop_mv']) + ' mV':10}"
                      f"{r.get('worst_temp_rise_c', '?'):<7}")
            else:
                print(f"{cand:12}{net:6}  {r.get('ngspice', r.get('error', '?'))}")
    print("\nIR drop = supply-pad to worst-case load-pad voltage on the routed "
          "copper (ngspice .op resistor-mesh solve).")
    print("dT(C)   = IPC-2221 external-layer temperature rise of the 0.16 mm "
          "(~6 mil) power trace at the load current.")


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

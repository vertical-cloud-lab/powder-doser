#!/usr/bin/env python3
"""Generate a router-ready KiCad *starter board* for Quilter / DeepPCB.

Background
----------
Notes ``16``/``17`` established that the autonomous PCB-layout vendors
(Quilter.ai, DeepPCB) only do *placement + routing* — they each need a
fully-defined **starter board** as input: a ``.kicad_pcb`` whose footprints
already carry assigned pads, a netlist, and a board outline (Edge.Cuts).
Note ``20`` (the Edison ``ANALYSIS`` pass over this repo's actual
``hardware/test-module/kicad`` schematic from PR #61) found that schematic
has the full 14-component / 20-net topology but **no footprints, no
``.kicad_pcb``, no outline**, and recommended (Rank 1) a code-first
"design-as-code → KiCad" build that assigns 0.1" pin-header *proxy*
footprints and emits the starter board headlessly in CI.

This script is that Rank-1 implementation. It is fully self-contained and
headless: it depends only on the pure-Python ``kiutils`` package (no KiCad
install, no GUI, no network), so it runs in the GitHub/Copilot sandbox and
in CI. It writes ``test_module_starter.kicad_pcb`` (plus a matching
``.kicad_pro`` with Power/Default net classes and a BOM/net summary) that
can be uploaded directly to Quilter or DeepPCB for the placement/routing
step that note ``20`` said still needs an automated or human pass.

Provenance of the netlist
-------------------------
``NETLIST`` and ``PINOUTS`` below are transcribed verbatim from the
``PLACEMENTS`` / ``SYMBOL_PINS`` data structures in PR #61's
``hardware/test-module/kicad/generate.py`` (commit ``147e505``), so the
component set, pin names, and net connectivity match the bench-rig
schematic exactly. Each breakout is rendered as a through-hole 0.1"
header *proxy* (one pad per schematic pin) — functionally correct for
routing even though the silkscreen outline is a generic header rather
than the exact Pololu/Adafruit/Pico board shape (note ``20`` §4 Rank 1).

Run:  python3 build_starter_board.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from kiutils.board import Board
from kiutils.footprint import DrillDefinition, Footprint, FpLine, FpText, Pad
from kiutils.items.common import Effects, Font, Net, Position
from kiutils.items.gritems import GrLine

HERE = Path(__file__).resolve().parent
BOARD_NAME = "test_module_starter"

# ---------------------------------------------------------------------------
# Netlist, transcribed from PR #61 hardware/test-module/kicad/generate.py
# (PLACEMENTS). (x, y) are the schematic-sheet anchor coordinates; we reuse
# them as a rough, non-overlapping starting *floorplan* on the board (note 20
# §4: "arranges them in a rough grid ... relies on Quilter to untangle it").
# ---------------------------------------------------------------------------
# Each entry: ref, lib_id (proxy type), x, y, [(pin_name, net), ...]
NETLIST = [
    ("J1", "Barrel_Jack_12V", 30, 40, [("+12V", "+12V"), ("GND", "GND")]),
    ("U1", "D24V22F5_Buck", 30, 70, [("VIN", "+12V"), ("GND_IN", "GND"),
                                     ("SHDN", "+12V"), ("VOUT", "+5V"),
                                     ("GND_OUT", "GND")]),
    ("C1", "Cap_Polar", 30, 100, [("+", "+12V"), ("-", "GND")]),
    ("C2", "Cap_Polar", 30, 120, [("+", "+5V"), ("-", "GND")]),
    ("U2", "Pi_Pico_W", 110, 50, [("VSYS", "+5V"), ("GND", "GND"),
                                  ("3V3", "+3V3"), ("GP0", "I2C_SDA"),
                                  ("GP1", "I2C_SCL"), ("GP4", "STP_TX"),
                                  ("GP5", "STP_RX"), ("GP10", "SOL_IN1"),
                                  ("GP11", "SOL_IN2"), ("GP15", "SERVO_SIG"),
                                  ("GP14", "HAPT_EN")]),
    ("U3", "DRV2605L_Breakout", 210, 40, [("VIN", "+3V3"), ("GND", "GND"),
                                          ("SDA", "I2C_SDA"), ("SCL", "I2C_SCL"),
                                          ("EN", "HAPT_EN"), ("IN_TRIG", "HAPT_EN"),
                                          ("OUT+", "VIB_A"), ("OUT-", "VIB_B")]),
    ("M1", "ERM_Motor", 275, 50, [("+", "VIB_A"), ("-", "VIB_B")]),
    ("U4", "DRV8871_Breakout", 210, 90, [("VM", "+12V"), ("GND", "GND"),
                                         ("IN1", "SOL_IN1"), ("IN2", "SOL_IN2"),
                                         ("OUT1", "SOL_A"), ("OUT2", "SOL_B")]),
    ("SOL1", "Solenoid", 275, 100, [("+", "SOL_A"), ("-", "SOL_B")]),
    ("U5", "Tic_T500", 210, 140, [("RX", "STP_TX"), ("TX", "STP_RX"),
                                  ("VIN", "+12V"), ("GND", "GND"),
                                  ("A1", "STP_A1"), ("A2", "STP_A2"),
                                  ("B1", "STP_B1"), ("B2", "STP_B2")]),
    ("C3", "Cap_Polar", 210, 195, [("+", "+12V"), ("-", "GND")]),
    ("SR1", "Shunt_Regulator", 175, 195, [("+", "+12V"), ("-", "GND")]),
    ("M2", "Stepper_4wire", 285, 145, [("A1", "STP_A1"), ("A2", "STP_A2"),
                                       ("B1", "STP_B1"), ("B2", "STP_B2")]),
    ("M3", "Servo_3pin", 210, 215, [("+5V", "+5V"), ("GND", "GND"),
                                    ("SIG", "SERVO_SIG")]),
]

# Full recorded pinout per proxy type (left/right header columns), so the
# proxy footprint has one pad per physical pin even when the schematic only
# wires a subset. Transcribed from generate.py SYMBOL_PINS.
PINOUTS = {
    "Barrel_Jack_12V": {"left": ["+12V", "GND"], "right": []},
    "D24V22F5_Buck": {"left": ["VIN", "GND_IN", "SHDN"], "right": ["VOUT", "GND_OUT"]},
    "Cap_Polar": {"left": ["+"], "right": ["-"]},
    "Shunt_Regulator": {"left": ["+"], "right": ["-"]},
    "Pi_Pico_W": {"left": ["GP0", "GP1", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7",
                           "GP10", "GP11", "GP14", "GP15"],
                  "right": ["VSYS", "GND", "3V3"]},
    "DRV2605L_Breakout": {"left": ["VIN", "GND", "SDA", "SCL", "IN_TRIG", "EN"],
                          "right": ["OUT+", "OUT-"]},
    "DRV8871_Breakout": {"left": ["VM", "GND", "IN1", "IN2"], "right": ["OUT1", "OUT2"]},
    "Tic_T500": {"left": ["SCL", "SDA", "TX", "RX", "ERR"],
                 "right": ["VIN", "GND", "A1", "A2", "B1", "B2"]},
    "Stepper_4wire": {"left": ["A1", "A2"], "right": ["B1", "B2"]},
    "Servo_3pin": {"left": ["+5V", "GND", "SIG"], "right": []},
    "ERM_Motor": {"left": ["+"], "right": ["-"]},
    "Solenoid": {"left": ["+"], "right": ["-"]},
}

# Nets carrying power; routed wider / with more clearance. The rest are signals.
POWER_NETS = {"+12V", "+5V", "+3V3", "GND"}

# Geometry (mm).
PITCH = 2.54          # 0.1" pad pitch within a header column
ROW_GAP = 7.62        # 0.3" between the left and right header columns
PAD_SIZE = 1.7
PAD_DRILL = 1.0
EDGE_MARGIN = 5.0     # board-outline clearance around the outermost pads
SILK_MARGIN = 1.0
# Compaction of the schematic-sheet anchor coordinates into a tidier board
# floorplan. The exact placement is unimportant (Quilter/DeepPCB re-place
# everything); _assert_no_overlap() guarantees the result stays DRC-clean.
FLOORPLAN_SCALE = 0.5


def _effects(size: float = 1.0) -> Effects:
    return Effects(font=Font(width=size, height=size, thickness=0.15))


def _pad(number: str, lx: float, ly: float, net: Net | None, pin1: bool) -> Pad:
    """A through-hole pad. Pad 1 is rectangular as a pin-1 marker."""
    return Pad(
        number=number,
        type="thru_hole",
        shape="rect" if pin1 else "oval",
        position=Position(lx, ly, 0),
        size=Position(PAD_SIZE, PAD_SIZE),
        drill=DrillDefinition(diameter=PAD_DRILL),
        layers=["*.Cu", "*.Mask"],
        net=net,
    )


def _make_footprint(ref: str, lib_id: str, x: float, y: float,
                    pin_nets: dict[str, str], nets: dict[str, Net]) -> tuple[Footprint, list[tuple[float, float]], tuple[float, float]]:
    """Build one proxy footprint; return it, the world (x, y) of every pad, and (hw, hh)."""
    cols = PINOUTS[lib_id]
    left, right = cols["left"], cols["right"]
    n_rows = max(len(left), len(right)) or 1

    fp = Footprint.create_new(
        library_id=f"powder_doser_proxies:{lib_id}",
        value=lib_id,
        reference=ref,
    )
    fp.position = Position(x, y, 0)
    fp.layer = "F.Cu"
    fp.tedit = "00000000"  # fixed so regeneration is byte-for-byte reproducible

    pad_world: list[tuple[float, float]] = []
    pad_num = 1
    half_x = ROW_GAP / 2.0

    def col_y(i: int, n: int) -> float:
        return (i - (n - 1) / 2.0) * PITCH

    for i, pin in enumerate(left):
        lx, ly = -half_x, col_y(i, len(left))
        net = nets.get(pin_nets.get(pin, ""))
        pad = _pad(str(pad_num), lx, ly, net, pin1=(pad_num == 1))
        pad.pinFunction = pin
        fp.pads.append(pad)
        pad_world.append((x + lx, y + ly))
        pad_num += 1
    for i, pin in enumerate(right):
        lx, ly = half_x, col_y(i, len(right))
        net = nets.get(pin_nets.get(pin, ""))
        pad = _pad(str(pad_num), lx, ly, net, pin1=(pad_num == 1))
        pad.pinFunction = pin
        fp.pads.append(pad)
        pad_world.append((x + lx, y + ly))
        pad_num += 1

    # Silkscreen courtyard rectangle + reference designator.
    hw = half_x + PAD_SIZE / 2 + SILK_MARGIN
    hh = (n_rows - 1) / 2.0 * PITCH + PAD_SIZE / 2 + SILK_MARGIN
    corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh), (-hw, -hh)]
    for (x1, y1), (x2, y2) in zip(corners, corners[1:]):
        fp.graphicItems.append(FpLine(start=Position(x1, y1), end=Position(x2, y2),
                                      layer="F.SilkS", width=0.12))
    for item in fp.graphicItems:
        if isinstance(item, FpText) and item.type == "reference":
            item.position = Position(0, -hh - 1.0, 0)
            item.layer = "F.SilkS"
            item.effects = _effects()
    return fp, pad_world, (hw, hh)


def _assert_no_overlap(courtyards: list[tuple[str, float, float, float, float]]) -> None:
    """Raise if any two footprint courtyards overlap (keeps the board DRC-clean)."""
    for i in range(len(courtyards)):
        ra, ax0, ay0, ax1, ay1 = courtyards[i]
        for j in range(i + 1, len(courtyards)):
            rb, bx0, by0, bx1, by1 = courtyards[j]
            if ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1:
                raise ValueError(
                    f"footprints {ra} and {rb} overlap; increase FLOORPLAN_SCALE")


def build_board() -> tuple[Board, tuple[float, float], dict[str, Net]]:
    board = Board.create_new()
    board.generator = "powder_doser_build_starter_board"

    # Net table: net 0 is the unconnected net.
    net_names = []
    for *_, pins in NETLIST:
        for _, net in pins:
            if net not in net_names:
                net_names.append(net)
    net_names.sort()
    nets = {"": Net(0, "")}
    board.nets = [nets[""]]
    for i, name in enumerate(net_names, start=1):
        nets[name] = Net(i, name)
        board.nets.append(nets[name])

    all_pads: list[tuple[float, float]] = []
    courtyards: list[tuple[str, float, float, float, float]] = []
    for ref, lib_id, x, y, pins in NETLIST:
        px, py = float(x) * FLOORPLAN_SCALE, float(y) * FLOORPLAN_SCALE
        pin_nets = {pin: net for pin, net in pins}
        fp, pad_world, (hw, hh) = _make_footprint(ref, lib_id, px, py, pin_nets, nets)
        board.footprints.append(fp)
        all_pads.extend(pad_world)
        courtyards.append((ref, px - hw, py - hh, px + hw, py + hh))

    _assert_no_overlap(courtyards)

    # Board outline (Edge.Cuts rectangle) around all pads + margin.
    xs = [p[0] for p in all_pads]
    ys = [p[1] for p in all_pads]
    x0, x1 = min(xs) - EDGE_MARGIN, max(xs) + EDGE_MARGIN
    y0, y1 = min(ys) - EDGE_MARGIN, max(ys) + EDGE_MARGIN
    rect = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    for (ax, ay), (bx, by) in zip(rect, rect[1:]):
        board.graphicItems.append(GrLine(start=Position(ax, ay), end=Position(bx, by),
                                         layer="Edge.Cuts", width=0.1))
    return board, (x1 - x0, y1 - y0), nets


def write_project(net_names_by_class: dict[str, list[str]]) -> None:
    """Write a minimal .kicad_pro with Default + Power net classes (DRC rules)."""
    pro = {
        "board": {"design_settings": {"rules": {"min_clearance": 0.2,
                                                 "min_track_width": 0.25}}},
        "net_settings": {
            "classes": [
                {"name": "Default", "clearance": 0.2, "track_width": 0.25,
                 "via_diameter": 0.8, "via_drill": 0.4,
                 "microvia_diameter": 0.3, "microvia_drill": 0.2,
                 "diff_pair_gap": 0.25, "diff_pair_width": 0.2},
                {"name": "Power", "clearance": 0.3, "track_width": 0.6,
                 "via_diameter": 1.0, "via_drill": 0.5,
                 "microvia_diameter": 0.3, "microvia_drill": 0.2,
                 "diff_pair_gap": 0.25, "diff_pair_width": 0.2},
            ],
            "netclass_assignments": {n: "Power" for n in net_names_by_class["Power"]},
        },
        "meta": {"filename": f"{BOARD_NAME}.kicad_pro", "version": 1},
    }
    (HERE / f"{BOARD_NAME}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")


def render_preview(pcb_path: Path) -> None:
    """Render a board-only SVG preview when kicad-cli is available (optional)."""
    cli = shutil.which("kicad-cli")
    if not cli:
        print("note: kicad-cli not on PATH; skipping SVG preview", flush=True)
        return
    svg = pcb_path.with_suffix(".svg")
    subprocess.run(
        [cli, "pcb", "export", "svg",
         "--layers", "F.Cu,B.Cu,F.SilkS,Edge.Cuts",
         "--exclude-drawing-sheet", "--page-size-mode", "2",
         "-o", str(svg), str(pcb_path)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"wrote {svg.name}")
    try:
        import cairosvg  # type: ignore
    except ImportError:
        print("note: cairosvg not installed; skipping PNG preview", flush=True)
        return
    png = pcb_path.with_suffix(".png")
    cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=1100)
    print(f"wrote {png.name}")


def main() -> None:
    board, (bw, bh), nets = build_board()
    pcb_path = HERE / f"{BOARD_NAME}.kicad_pcb"
    board.to_file(str(pcb_path))

    power = sorted(n for n in nets if n in POWER_NETS and n)
    write_project({"Power": power})

    # Human-readable BOM / net summary for review and provenance.
    summary = {
        "board": f"{BOARD_NAME}.kicad_pcb",
        "components": len(NETLIST),
        "nets": len(nets) - 1,
        "outline_mm": [round(bw, 2), round(bh, 2)],
        "power_nets": power,
        "bom": [{"ref": r, "proxy": lib, "pins": len(p)} for r, lib, _, _, p in NETLIST],
    }
    (HERE / "starter_board_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"wrote {pcb_path.name}: {len(NETLIST)} footprints, "
          f"{len(nets) - 1} nets, outline {bw:.1f}x{bh:.1f} mm")
    render_preview(pcb_path)


if __name__ == "__main__":
    main()

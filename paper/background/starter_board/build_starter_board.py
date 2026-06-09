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
"design-as-code → KiCad" build that emits the starter board headlessly in
CI. Component pads are 0.1" headers (one per schematic pin), while each part's
body outline / courtyard / 3-D model is taken from the real vendor design
files committed under ``hardware/vendor-files/`` (PR #25).

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
schematic exactly. Each schematic pin still becomes one through-hole
0.1" pad (so the 20-net ratsnest is preserved exactly), but the body
**outline, courtyard, and 3-D model** are now taken from the real
vendor design files committed to the repo under
``hardware/vendor-files/`` (PR #25), instead of a generic header box.

Provenance of the component packages (``PACKAGES``)
---------------------------------------------------
The real per-part body sizes in ``PACKAGES`` come from the committed
vendor files (PR #25, ``hardware/vendor-files/``):

* Adafruit breakouts (DRV2605L #2305, DRV8871 #3190) — board outline
  read from the vendor **Eagle ``.brd``** (layer 20 / Dimension).
* Pololu carriers (D24V22F5 #2858, Tic T500 #3135, shunt regulator
  #3776) — published 0.1"-grid PCB size, cross-checked against the
  vendor **STEP** envelope.
* Off-board actuators (NEMA-11 stepper #11HS18, servo #1142, solenoid
  #412, ERM #1201) — they live *off* the PCB, so they appear here as
  their on-board **connector** only; the actuator body size / STEP is
  recorded for reference (mating part), not drawn as a board courtyard.
* Raspberry Pi Pico W (PR #61's MCU, not in the PR #25 vendor set) —
  standard 51 x 21 mm / 2x20 0.1" mechanical outline.

3-D model paths point at ``hardware/vendor-files/...`` so they resolve
once PR #25 is merged; KiCad simply omits a missing model (the
``.kicad_pcb`` itself is self-contained and needs no external file).

Run:  python3 build_starter_board.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from kiutils.board import Board
from kiutils.footprint import DrillDefinition, Footprint, FpLine, FpText, Model, Pad
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

# ---------------------------------------------------------------------------
# Real component packages, sourced from the committed vendor design files
# under hardware/vendor-files/ (PR #25). Each entry:
#   kind   "module"    -> an on-board breakout; draw its real PCB outline +
#                         courtyard and attach the vendor 3-D model.
#          "connector" -> an off-board actuator (motor/solenoid/servo) that
#                         only appears on the PCB as its wiring connector;
#                         the body/outline auto-fits the header (the actuator
#                         body is recorded in "ref" for provenance only).
#          "passive"   -> generic discrete (electrolytic cap); auto-fit body.
#   body   (w, h) real board outline in mm, or None to auto-fit to the pads.
#   model  vendor STEP path (relative to repo root) or None.
#   source human-readable provenance (which committed file the size came from).
# ---------------------------------------------------------------------------
VENDOR = "hardware/vendor-files"
PACKAGES = {
    "Barrel_Jack_12V": dict(
        kind="module", body=(14.0, 11.0), model=None,
        source="Adafruit #373 2.1 mm DC barrel-jack breakout (datasheet)"),
    "D24V22F5_Buck": dict(
        kind="module", body=(12.70, 10.16),
        model=f"{VENDOR}/pololu-2858-d24v22f5/cad/d24v22fx-step-down-voltage-regulator.step",
        source="Pololu #2858 0.5x0.4 in PCB; STEP envelope 19.5x20.7x13.8 mm"),
    "Cap_Polar": dict(
        kind="passive", body=(8.5, 8.5), model=None,
        source="generic radial electrolytic, Ø8 mm body"),
    "Shunt_Regulator": dict(
        kind="module", body=(24.13, 10.16),
        model=f"{VENDOR}/pololu-3776-shunt-regulator-9w/cad/shunt-regulator.step",
        source="Pololu #3776 0.95x0.4 in PCB; STEP envelope 28.6x21.2x13.8 mm"),
    "Pi_Pico_W": dict(
        kind="module", body=(51.0, 21.0), model=None,
        source="Raspberry Pi Pico W mechanical 51x21 mm, 2x20 0.1 in (PR #61 MCU)"),
    "DRV2605L_Breakout": dict(
        kind="module", body=(17.78, 16.51),
        model=f"{VENDOR}/adafruit-2305-drv2605l/cad/2305 DRV2605L.step",
        source="Adafruit #2305 Eagle .brd outline (layer 20) 17.78x16.51 mm"),
    "DRV8871_Breakout": dict(
        kind="module", body=(20.32, 24.13),
        model=f"{VENDOR}/adafruit-3190-drv8871/cad/3190 DRV8871 Breakout.step",
        source="Adafruit #3190 Eagle .brd outline (layer 20) 20.32x24.13 mm"),
    "Tic_T500": dict(
        kind="module", body=(25.40, 15.24), model=None,
        source="Pololu #3135 1.0x0.6 in PCB; STEP/STL in "
               f"{VENDOR}/pololu-3135-tic-t500/cad/tic-stepper-motor-controller-models.zip"),
    "Stepper_4wire": dict(
        kind="connector", body=None, model=None,
        source="off-board StepperOnline 11HS18-0674S NEMA-11 28x28x45 mm; STEP in "
               f"{VENDOR}/stepperonline-11hs18-0674s/cad/11HS18-0674S.STEP"),
    "Servo_3pin": dict(
        kind="connector", body=None, model=None,
        source="off-board Adafruit #1142 metal-gear servo 40.7x19.7x42.9 mm"),
    "ERM_Motor": dict(
        kind="connector", body=None, model=None,
        source="off-board Adafruit #1201 ERM coin, Ø10 x 2.7 mm"),
    "Solenoid": dict(
        kind="connector", body=None, model=None,
        source="off-board Adafruit #412 JF-0530B 5 V push-pull solenoid"),
}

# Geometry (mm).
PITCH = 2.54          # 0.1" pad pitch within a header column
ROW_GAP = 7.62        # 0.3" between the left and right header columns
PAD_SIZE = 1.7
PAD_DRILL = 1.0
EDGE_MARGIN = 5.0     # board-outline clearance around the outermost pads
SILK_MARGIN = 1.0
CRTYD_CLEARANCE = 0.5  # F.CrtYd gap around the real body outline
# Spread of the schematic-sheet anchor coordinates into a board floorplan.
# Scaled up to 1.0 (vs the old proxy 0.5) so the now-real, larger component
# bodies do not collide. The exact placement is unimportant (Quilter/DeepPCB
# re-place everything); _assert_no_overlap() guarantees it stays DRC-clean.
FLOORPLAN_SCALE = 1.0


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
    """Build one footprint (real body from PACKAGES); return it, the world (x, y) of every pad, and (hw, hh)."""
    cols = PINOUTS[lib_id]
    left, right = cols["left"], cols["right"]
    n_rows = max(len(left), len(right)) or 1

    fp = Footprint.create_new(
        library_id=f"powder_doser_parts:{lib_id}",
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

    # Real component body outline (F.Fab) + courtyard (F.CrtYd) + silk, sized
    # from the committed vendor files (PACKAGES). The outline never shrinks
    # below the pad cluster, so the pads always stay inside the body.
    pkg = PACKAGES[lib_id]
    pad_hw = half_x + PAD_SIZE / 2 + SILK_MARGIN
    pad_hh = (n_rows - 1) / 2.0 * PITCH + PAD_SIZE / 2 + SILK_MARGIN
    if pkg["body"] is not None:
        body_hw = max(pad_hw, pkg["body"][0] / 2.0)
        body_hh = max(pad_hh, pkg["body"][1] / 2.0)
    else:
        body_hw, body_hh = pad_hw, pad_hh

    def _rect(hw: float, hh: float, layer: str, width: float) -> None:
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh), (-hw, -hh)]
        for (x1, y1), (x2, y2) in zip(corners, corners[1:]):
            fp.graphicItems.append(FpLine(start=Position(x1, y1), end=Position(x2, y2),
                                          layer=layer, width=width))

    _rect(body_hw, body_hh, "F.Fab", 0.1)                                  # real body
    _rect(body_hw + 0.1, body_hh + 0.1, "F.SilkS", 0.12)                   # silk
    _rect(body_hw + CRTYD_CLEARANCE, body_hh + CRTYD_CLEARANCE, "F.CrtYd", 0.05)  # courtyard

    for item in fp.graphicItems:
        if isinstance(item, FpText) and item.type == "reference":
            item.position = Position(0, -body_hh - 1.0, 0)
            item.layer = "F.SilkS"
            item.effects = _effects()

    # Attach the vendor 3-D model (resolves once PR #25 is merged; KiCad just
    # omits it if absent, so the .kicad_pcb stays self-contained).
    if pkg["model"]:
        fp.models.append(Model(path=pkg["model"]))

    hw = body_hw + CRTYD_CLEARANCE
    hh = body_hh + CRTYD_CLEARANCE
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

    courtyards: list[tuple[str, float, float, float, float]] = []
    for ref, lib_id, x, y, pins in NETLIST:
        px, py = float(x) * FLOORPLAN_SCALE, float(y) * FLOORPLAN_SCALE
        pin_nets = {pin: net for pin, net in pins}
        fp, pad_world, (hw, hh) = _make_footprint(ref, lib_id, px, py, pin_nets, nets)
        board.footprints.append(fp)
        courtyards.append((ref, px - hw, py - hh, px + hw, py + hh))

    _assert_no_overlap(courtyards)

    # Board outline (Edge.Cuts rectangle) around every component courtyard +
    # margin (courtyards now reflect the real body sizes, which extend past the
    # pad cluster, so the outline is taken from them rather than the pads).
    x0 = min(c[1] for c in courtyards) - EDGE_MARGIN
    x1 = max(c[3] for c in courtyards) + EDGE_MARGIN
    y0 = min(c[2] for c in courtyards) - EDGE_MARGIN
    y1 = max(c[4] for c in courtyards) + EDGE_MARGIN
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


def _render_svg_fallback(pcb_path: Path) -> Path:
    """Write a dependency-free SVG preview straight from the board model.

    Used when ``kicad-cli`` is not installed, so the preview is reproducible
    in the headless sandbox / CI. Draws the Edge.Cuts outline, each component's
    real F.Fab body rectangle + reference, every pad, and the unrouted ratsnest
    (pads sharing a net), matching what ``kicad-cli`` would render.
    """
    board = Board.from_file(str(pcb_path))

    # Edge.Cuts bbox.
    ex, ey = [], []
    for g in board.graphicItems:
        if isinstance(g, GrLine) and g.layer == "Edge.Cuts":
            ex += [g.start.X, g.end.X]
            ey += [g.start.Y, g.end.Y]
    x0, x1, y0, y1 = min(ex), max(ex), min(ey), max(ey)
    pad = 4.0
    vb_w, vb_h = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    scale = 1100.0 / vb_w

    def X(v: float) -> float: return (v - x0 + pad)
    def Y(v: float) -> float: return (v - y0 + pad)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{vb_w * scale:.0f}" '
        f'height="{vb_h * scale:.0f}" viewBox="0 0 {vb_w:.2f} {vb_h:.2f}">',
        f'<rect x="0" y="0" width="{vb_w:.2f}" height="{vb_h:.2f}" fill="#0b1a12"/>',
    ]
    # Edge.Cuts outline.
    for g in board.graphicItems:
        if isinstance(g, GrLine) and g.layer == "Edge.Cuts":
            parts.append(f'<line x1="{X(g.start.X):.2f}" y1="{Y(g.start.Y):.2f}" '
                         f'x2="{X(g.end.X):.2f}" y2="{Y(g.end.Y):.2f}" '
                         f'stroke="#e8d44d" stroke-width="0.3"/>')

    # Ratsnest: collect pad world positions per net.
    net_pads: dict[str, list[tuple[float, float]]] = {}
    for fp in board.footprints:
        fx, fy = fp.position.X, fp.position.Y
        for p in fp.pads:
            if p.net and p.net.name:
                net_pads.setdefault(p.net.name, []).append((fx + p.position.X, fy + p.position.Y))
    for pts in net_pads.values():
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            parts.append(f'<line x1="{X(ax):.2f}" y1="{Y(ay):.2f}" x2="{X(bx):.2f}" '
                         f'y2="{Y(by):.2f}" stroke="#3a6ea5" stroke-width="0.12"/>')

    # Component bodies (F.Fab), pads, and reference designators.
    for fp in board.footprints:
        fx, fy = fp.position.X, fp.position.Y
        fab = [g for g in fp.graphicItems if isinstance(g, FpLine) and g.layer == "F.Fab"]
        xs = [g.start.X for g in fab] + [g.end.X for g in fab]
        ys = [g.start.Y for g in fab] + [g.end.Y for g in fab]
        ref = next((g.text for g in fp.graphicItems
                    if isinstance(g, FpText) and g.type == "reference"), "")
        if xs:
            bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
            parts.append(f'<rect x="{X(fx + bx0):.2f}" y="{Y(fy + by0):.2f}" '
                         f'width="{bx1 - bx0:.2f}" height="{by1 - by0:.2f}" '
                         f'fill="#14543a" stroke="#cfcfcf" stroke-width="0.12"/>')
            parts.append(f'<text x="{X(fx):.2f}" y="{Y(fy + by0) - 0.4:.2f}" '
                         f'font-size="1.6" fill="#e0e0e0" text-anchor="middle">'
                         f'{ref} {fp.entryName.split(":")[-1]}</text>')
        for p in fp.pads:
            cx, cy = X(fx + p.position.X), Y(fy + p.position.Y)
            parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{PAD_SIZE / 2:.2f}" '
                         f'fill="#d08a2c"/>')
    parts.append('</svg>')
    svg = pcb_path.with_suffix(".svg")
    svg.write_text("\n".join(parts) + "\n")
    return svg


def render_preview(pcb_path: Path) -> None:
    """Render a board preview. Uses kicad-cli if present, else a pure-Python SVG."""
    cli = shutil.which("kicad-cli")
    svg = pcb_path.with_suffix(".svg")
    if cli:
        subprocess.run(
            [cli, "pcb", "export", "svg",
             "--layers", "F.Cu,B.Cu,F.SilkS,F.Fab,Edge.Cuts",
             "--exclude-drawing-sheet", "--page-size-mode", "2",
             "-o", str(svg), str(pcb_path)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    else:
        print("note: kicad-cli not on PATH; using built-in SVG fallback", flush=True)
        _render_svg_fallback(pcb_path)
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
        "bom": [{
            "ref": r,
            "part": lib,
            "kind": PACKAGES[lib]["kind"],
            "pins": len(p),
            "body_mm": list(PACKAGES[lib]["body"]) if PACKAGES[lib]["body"] else None,
            "model": PACKAGES[lib]["model"],
            "source": PACKAGES[lib]["source"],
        } for r, lib, _, _, p in NETLIST],
    }
    (HERE / "starter_board_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"wrote {pcb_path.name}: {len(NETLIST)} footprints, "
          f"{len(nets) - 1} nets, outline {bw:.1f}x{bh:.1f} mm")
    render_preview(pcb_path)


if __name__ == "__main__":
    main()

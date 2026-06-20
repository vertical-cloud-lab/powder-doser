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
CI. Every component land pattern is now copied verbatim from a **real KiCad
library footprint** (vendored under ``kicad_footprints/``; see
``_part_groups``) instead of a synthesized 0.1" placeholder, while each part's
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
schematic exactly. Each schematic pin becomes one real through-hole pad,
copied from the matching **KiCad library footprint** (real pad size, drill,
shape, pad-1 marker and 3-D model — see ``kicad_footprints/`` and
``_part_groups``), so the 20-net ratsnest is preserved exactly while the land
patterns are genuine manufacturer-grade KiCad footprints. The body
**outline, courtyard, and 3-D model** are taken from the real vendor design
files committed to the repo under ``hardware/vendor-files/`` (PR #25).

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

import copy
import json
import re
import shutil
import subprocess
import tempfile
from hashlib import sha256
from pathlib import Path

from kiutils.board import Board
from kiutils.footprint import Footprint, FpLine, FpText, Model, Pad
from kiutils.items.common import Effects, Font, Net, Position
from kiutils.items.gritems import GrLine

HERE = Path(__file__).resolve().parent
BOARD_NAME = "test_module_starter"
# Second variant: same netlist/parts but every footprint staged *outside* an
# empty board outline, so DeepPCB/Quilter can be tested on auto-*placement* (not
# just routing). Lets us compare their placement against this generator's compact
# placement (issue #94 / PR #76). Emitted as its own .kicad_pcb/.kicad_sch/
# .kicad_pro trio.
UNPLACED_NAME = "test_module_unplaced"

# kiutils' ``create_new`` stamps every board/footprint with the KiCad 6 file
# format version (20211014). Quilter (and other KiCad 7+ tools) reject that
# with "Version 20211014 not supported. ... KiCAD versions 7.0 and newer".
# Emit the KiCad 7.0 stable .kicad_pcb format version instead so the upload
# trio is accepted (the matching .kicad_sch already uses the KiCad 7 20230121
# schematic version).
KICAD7_PCB_VERSION = "20221018"

# ---------------------------------------------------------------------------
# Real KiCad library footprints. Every component land pattern is copied from a
# genuine KiCad footprint (vendored verbatim under ``kicad_footprints/`` from
# the official ``kicad-footprints`` 7.0.11 library, CC-BY-SA-4.0-with-exception
# — see kicad_footprints/README.md) instead of a synthesized 0.1" header, so
# the board carries real manufacturer-grade pads / pad-1 markers / 3-D models.
# Vendoring the handful of needed ``.kicad_mod`` files keeps the build
# self-contained and byte-for-byte reproducible (no system KiCad required); a
# system install under /usr/share/kicad/footprints is used as a fallback.
# ---------------------------------------------------------------------------
LIB_DIRS = [
    Path(__file__).resolve().parent / "kicad_footprints",
    Path("/usr/share/kicad/footprints"),
    Path("/usr/share/kicad/modules"),
]
_FP_CACHE: dict[tuple[str, str], Footprint] = {}


def _lib_fp_path(lib: str, name: str) -> Path | None:
    for base in LIB_DIRS:
        p = base / f"{lib}.pretty" / f"{name}.kicad_mod"
        if p.exists():
            return p
    return None


def _load_lib_fp(lib: str, name: str) -> Footprint:
    """Load (and cache) a real KiCad library footprint by ``lib:name``."""
    key = (lib, name)
    if key not in _FP_CACHE:
        path = _lib_fp_path(lib, name)
        if path is None:
            raise FileNotFoundError(
                f"KiCad library footprint {lib}:{name} not found under "
                f"{[str(d) for d in LIB_DIRS]}; expected it vendored in "
                f"kicad_footprints/ (see kicad_footprints/README.md)")
        _FP_CACHE[key] = Footprint.from_file(str(path))
    return _FP_CACHE[key]


def _lib_pads(lib: str, name: str) -> dict[str, Pad]:
    """Real pads of one library footprint, keyed by their pad number."""
    return {p.number: p for p in _load_lib_fp(lib, name).pads}


def _lib_model(lib: str, name: str) -> Model | None:
    """First 3-D model of a library footprint (real ``${KICAD6_3DMODEL_DIR}`` ref)."""
    models = _load_lib_fp(lib, name).models
    return models[0] if models else None


# Standard 0.1" single-row pin header (the real land pattern that each
# through-hole breakout / connector mates to on the host PCB).
def _header(n: int) -> tuple[str, str]:
    return ("Connector_PinHeader_2.54mm", f"PinHeader_1x{n:02d}_P2.54mm_Vertical")


# A "group" is one real library footprint whose real pads supply the geometry
# for a run of this part's physical pins. ``pins`` is an ordered list of
# ``(pin_name, source_pad_number)`` and ``anchor`` is "left" / "right" /
# "center" (left/right columns are placed on opposite body edges). The board's
# sequential pad numbering follows the group order, which is kept identical to
# the left-then-right ``PINOUTS`` order so the board pad numbers line up with
# the schematic pin numbers (verified by ``validate_schematic_netlist``).
# ---------------------------------------------------------------------------
# Netlist, transcribed from PR #61 hardware/test-module/kicad/generate.py
# (PLACEMENTS), plus the J2 RS-232 scale-interface module added on PR #76
# (issue: integrate the A&D balance for gravimetric dosing). (x, y) are the
# schematic-sheet anchor coordinates; the board ignores them (see
# _pack_positions) and only the schematic sheet uses them for symbol layout.
# ---------------------------------------------------------------------------
# Each entry: ref, lib_id (proxy type), x, y, [(pin_name, net), ...]
NETLIST = [
    ("J1", "Barrel_Jack_12V", 30, 40, [("+12V", "+12V"), ("GND", "GND")]),
    ("U1", "D24V22F5_Buck", 30, 70, [("VIN", "+12V"), ("GND", "GND"),
                                     ("SHDN", "+12V"), ("VOUT", "+5V")]),
    ("C1", "Cap_Polar", 30, 100, [("+", "+12V"), ("-", "GND")]),
    ("C2", "Cap_Polar", 30, 120, [("+", "+5V"), ("-", "GND")]),
    ("U2", "Pi_Pico_W", 110, 50, [("VSYS", "+5V"), ("GND", "GND"),
                                  ("3V3", "+3V3"), ("GP0", "I2C_SDA"),
                                  ("GP1", "I2C_SCL"), ("GP4", "STP_TX"),
                                  ("GP5", "STP_RX"), ("GP10", "SOL_IN1"),
                                  ("GP11", "SOL_IN2"), ("GP15", "SERVO_SIG"),
                                  ("GP14", "HAPT_EN"),
                                  # RS-232 module (scale + spare channel). The
                                  # Waveshare board hard-wires its channels to
                                  # GP0/GP1 and GP4/GP5, but those are taken here
                                  # by I2C and the Tic UART, so the side-header
                                  # mount (see J2) re-routes the four UART lines
                                  # to free Pico UART pins: UART0 alt GP12/GP13
                                  # (channel 0 = A&D HR-100A scale) and UART1 alt
                                  # GP8/GP9 (channel 1 = spare).
                                  ("GP12", "RS232_0_TXD"), ("GP13", "RS232_0_RXD"),
                                  ("GP8", "RS232_1_TXD"), ("GP9", "RS232_1_RXD")]),
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
    ("SR1", "Shunt_Regulator", 175, 195, [("A", "+12V"), ("+", "+12V"),
                                          ("B", "GND"), ("-", "GND")]),
    ("M2", "Stepper_4wire", 285, 145, [("A1", "STP_A1"), ("A2", "STP_A2"),
                                       ("B1", "STP_B1"), ("B2", "STP_B2")]),
    ("M3", "Servo_3pin", 210, 215, [("+5V", "+5V"), ("GND", "GND"),
                                    ("SIG", "SERVO_SIG")]),
    # Waveshare Pico-2CH-RS232: a Pico-form-factor HAT (SP3232EEN, 2 channels)
    # that mounts on a side 2x20 header (Proto-Doubler spirit) beside the Pico,
    # so its own embedded RS-232 charge-pump caps replace a discrete MAX3232 +
    # ~5 caps on this board. Modelled as the 2x20 receptacle it plugs onto; the
    # module taps VCC/GND plus its four UART lines at the GP0/GP1/GP4/GP5
    # positions (datasheets under hardware/vendor-files/waveshare-pico-2ch-rs232).
    ("J2", "RS232_2CH_Module", 110, 200, [("VSYS", "+5V"), ("GND", "GND"),
                                         ("GP0", "RS232_0_TXD"),
                                         ("GP1", "RS232_0_RXD"),
                                         ("GP4", "RS232_1_TXD"),
                                         ("GP5", "RS232_1_RXD")]),
]

# Full recorded pinout per proxy type (left/right header columns), so the
# proxy footprint has one pad per physical pin of the real part even when the
# schematic only wires a subset. Pin *names* may repeat (e.g. the Raspberry Pi
# Pico W has eight GND pins); every pad/pin sharing a name is tied to the same
# net. Counts were verified pin-by-pin against the vendor datasheets / Eagle
# files under hardware/vendor-files/ (PR #25) and the manufacturers' pinout
# diagrams (see note 21 "Pin-count verification").
PINOUTS = {
    # Adafruit #373: a 2.1 mm DC barrel jack has three solder lugs - centre
    # (tip, +), sleeve (-) and the normally-closed switch lug (left unused here).
    "Barrel_Jack_12V": {"left": ["+12V", "GND", "SW"], "right": []},
    # Pololu D24V22Fx: four pins in one row - VIN, GND, VOUT, SHDN (single GND).
    "D24V22F5_Buck": {"left": ["VIN", "GND", "VOUT", "SHDN"], "right": []},
    "Cap_Polar": {"left": ["+"], "right": ["-"]},
    # Pololu #3776 shunt regulator: four large holes - A/+ on one node and
    # B/- on the other (A is tied to +, B to -) - connected across the rail.
    "Shunt_Regulator": {"left": ["A", "+"], "right": ["B", "-"]},
    # Raspberry Pi Pico W: the full 40-pin (2x20, 0.1") castellated module.
    # Physical order (left col top->bottom = pins 1-20, right col = pins 21-40)
    # per the official Pico-R3-A4 pinout; unused GPIO are NC in this design.
    "Pi_Pico_W": {
        "left": ["GP0", "GP1", "GND", "GP2", "GP3", "GP4", "GP5", "GND",
                 "GP6", "GP7", "GP8", "GP9", "GND", "GP10", "GP11", "GP12",
                 "GP13", "GND", "GP14", "GP15"],
        "right": ["VBUS", "VSYS", "GND", "3V3_EN", "3V3", "ADC_VREF", "GP28",
                  "GND", "GP27", "GP26", "RUN", "GP22", "GND", "GP21", "GP20",
                  "GP19", "GP18", "GND", "GP17", "GP16"]},
    # Waveshare Pico-2CH-RS232 module: a Pico-form-factor HAT, so the side
    # header it plugs onto mirrors the Pico's 2x20 castellated pinout exactly
    # (one pad per position). Only the positions the module actually uses
    # (VSYS, GND, GP0/GP1 = channel 0, GP4/GP5 = channel 1) are netted in
    # NETLIST; the rest are pass-through no-connects. Re-uses the Pico pinout
    # by reference so the two land patterns can never drift apart.
    "RS232_2CH_Module": None,  # set to the Pico pinout just below
    "DRV2605L_Breakout": {"left": ["VIN", "GND", "SDA", "SCL", "IN_TRIG", "EN"],
                          "right": ["OUT+", "OUT-"]},
    # Adafruit #3190 DRV8871: 4-pos power/motor terminal block (VM, GND, OUT1,
    # OUT2) + 3-pin logic header (IN1, IN2, GND) = 7 connections, two of them GND.
    "DRV8871_Breakout": {"left": ["VM", "GND", "OUT1", "OUT2"],
                         "right": ["IN1", "IN2", "GND"]},
    # Pololu Tic T500: control row (SCL, SDA/AN, TX, RX, RC, ERR, GND, 5V) +
    # power/motor row (VIN, GND, A1, A2, B1, B2) = 14 pins, two of them GND.
    "Tic_T500": {"left": ["SCL", "SDA", "TX", "RX", "RC", "ERR", "GND", "5V"],
                 "right": ["VIN", "GND", "A1", "A2", "B1", "B2"]},
    "Stepper_4wire": {"left": ["A1", "A2"], "right": ["B1", "B2"]},
    "Servo_3pin": {"left": ["+5V", "GND", "SIG"], "right": []},
    "ERM_Motor": {"left": ["+"], "right": ["-"]},
    "Solenoid": {"left": ["+"], "right": ["-"]},
}
# The RS-232 module receptacle is the Pico's land pattern (the HAT plugs onto
# it), so bind it to the same pinout rather than duplicating the 40-pin lists.
PINOUTS["RS232_2CH_Module"] = PINOUTS["Pi_Pico_W"]

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
        kind="module", body=(21.0, 51.0), model=None,
        source="Raspberry Pi Pico W mechanical 51x21 mm, 2x20 0.1 in "
               "castellated (long 51 mm edge runs along the pin columns; PR #61 MCU)"),
    "RS232_2CH_Module": dict(
        kind="module", body=(21.0, 52.0), model=None,
        source="Waveshare Pico-2CH-RS232 (SP3232EEN, 2 channels) 21x52 mm; "
               "mounts on a side 2x20 header (Proto-Doubler PiCowbell spirit); "
               "embeds its own RS-232 charge-pump caps so no discrete MAX3232 is "
               "needed; datasheets in "
               f"{VENDOR}/waveshare-pico-2ch-rs232/datasheets/"),
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
# Board placement. The earliest build reused the schematic-sheet anchor
# coordinates (NETLIST x/y) as the board floorplan, scaled by FLOORPLAN_SCALE,
# which left the parts ridiculously spread out (~279x199 mm board; issue #94).
# The board now ignores those coordinates and lays the real component bodies out
# with a domain- and edge-aware compact packer (_pack_positions, below);
# PLACE_GAP is the clearance left between adjacent courtyards. The exact
# placement is unimportant (Quilter/DeepPCB re-place everything) but a *tight,
# domain-grouped* start hands the routers short local nets on a right-sized
# board. FLOORPLAN_SCALE is retained only for the schematic-sheet layout below.
FLOORPLAN_SCALE = 1.0
PLACE_GAP = 1.5        # extra gap (mm) between courtyards in the compact pack
STAGE_GAP = 12.0       # gap (mm) between the empty board outline and the parts
#                        staged beside it in the unplaced (auto-place) variant
DOMAIN_GAP = 6.0       # aisle (mm) between the power and logic domains

# Right-sized outline for the *unplaced* (auto-placement) variant. Quilter/DeepPCB
# place components onto whatever outline is uploaded and *cannot resize it
# themselves* (https://docs.quilter.ai — "Quilter can't define or resize the
# board outline for you"), so the unplaced board no longer mirrors the wider
# pre-placed outline (which spread parts into domain rows). 100 x 100 mm gives
# ~51% courtyard / ~42% body utilisation — inside the 35-55% band recommended
# for through-hole mixed-signal auto-placement/routing (enough copper room for
# the 2-layer routes while cutting the wasted area) — comfortably fits the two
# tallest parts (the 52 mm Pico/RS-232 modules) with EDGE_MARGIN to spare, and
# lands on JLCPCB's 100 x 100 mm prototype price break.
UNPLACED_OUTLINE_MM = (100.0, 100.0)

# ---------------------------------------------------------------------------
# Placement strategy (Edison board-placement review,
# edison_artifacts/board_placement_review_for_powder_doser.answer.md). The pure
# area shelf-pack was compact but domain-blind; the review's #1 recommendation
# was to make placement domain-aware and cluster-aware so an autonomous router
# (DeepPCB/Quilter) starts from short, local nets and a clean noisy/quiet
# partition instead of an arbitrary grid. The compact placement now:
#   * packs each cluster (a regulator/driver with its decoupling caps and its
#     load connector) as a rigid contiguous row, keeping those local nets short;
#   * orders clusters by domain - the +12 V/+5 V power + motor/solenoid section
#     on the left, then a DOMAIN_GAP aisle, then the 3V3/I2C logic section (Pico
#     + haptics + servo) on the right - separating noisy switching from quiet
#     control nets;
#   * biases each cluster's off-board connector (EDGE_REFS) to the outward end
#     of its row (left edge of the left domain, right edge of the right domain)
#     for cable exit, without divorcing it from the driver it serves.
# Each entry: (domain, cluster-name, [refs, in packing order]). Every ref in
# NETLIST appears in exactly one cluster.
PLACEMENT_CLUSTERS = [
    ("power", "input_12v", ["J1", "C1", "U1", "C2"]),   # jack -> bulk -> buck -> 5V cap
    ("power", "solenoid",  ["U4", "SOL1"]),             # DRV8871 + solenoid load
    ("power", "stepper",   ["SR1", "C3", "U5", "M2"]),  # shunt + cap + Tic + stepper
    ("logic", "haptic",    ["U3", "M1"]),               # DRV2605L + ERM
    ("logic", "mcu",       ["U2", "J2", "M3"]),       # Pico + RS-232 module + servo header
]
# Off-board connectors (cables leaving the PCB); edge-placed for harnessing.
EDGE_REFS = {"J1", "SOL1", "M2", "M1", "M3"}

# Real Raspberry Pi Pico W castellated row spacing (centre-to-centre between
# the two 1x20 edges); 17.78 mm = 7 x 0.1" per the official mechanical drawing.
PICO_ROW_SPACING = 17.78

# ---------------------------------------------------------------------------
# Per-part real-footprint plan. ``_part_groups`` returns, for one part, the
# ordered list of groups ``(lib, fp_name, [(pin_name, src_pad_number), ...],
# anchor)`` whose real KiCad pads supply that part's land pattern. Most parts
# fall through to the generic rule (each PINOUTS column -> a 1xN pin header on
# the matching body edge, the real land pattern a through-hole module mates to).
# A few have an exact dedicated library footprint and are overridden here.
# ---------------------------------------------------------------------------
# Pure-connector parts (no on-board breakout body) whose real land pattern is a
# single inline 0.1" pin header rather than two opposed columns. Listed in the
# left-then-right PINOUTS order so the single header's pad numbers still match
# the schematic pin numbering. Keeps every header within the vendored set.
SINGLE_HEADER_ORDER = {
    "ERM_Motor": ["+", "-"],
    "Solenoid": ["+", "-"],
    "Stepper_4wire": ["A1", "A2", "B1", "B2"],
    "Shunt_Regulator": ["A", "+", "B", "-"],
}


def _part_groups(lib_id: str) -> list[tuple[str, str, list[tuple[str, str]], str]]:
    cols = PINOUTS[lib_id]
    left, right = cols["left"], cols["right"]

    if lib_id == "Cap_Polar":
        # Real radial electrolytic: pad 1 (+, square) and pad 2 (-) 3.5 mm apart.
        return [("Capacitor_THT", "CP_Radial_D8.0mm_P3.50mm",
                 [("+", "1"), ("-", "2")], "center")]
    if lib_id == "Barrel_Jack_12V":
        # Real 2.1 mm DC jack: tip lug (pad 1, +), sleeve lug (pad 3, -) and the
        # switch lug (pad 2). Renumbered 1/2/3 in the schematic's +12V/GND/SW
        # order while keeping each lug's real geometry.
        return [("Connector_BarrelJack", "BarrelJack_Horizontal",
                 [("+12V", "1"), ("GND", "3"), ("SW", "2")], "center")]
    if lib_id in SINGLE_HEADER_ORDER:
        order = SINGLE_HEADER_ORDER[lib_id]
        lib, name = _header(len(order))
        return [(lib, name, [(p, str(i + 1)) for i, p in enumerate(order)], "center")]

    groups: list[tuple[str, str, list[tuple[str, str]], str]] = []
    if left:
        lib, name = _header(len(left))
        groups.append((lib, name, [(p, str(i + 1)) for i, p in enumerate(left)],
                       "left" if right else "center"))
    if right:
        lib, name = _header(len(right))
        groups.append((lib, name, [(p, str(i + 1)) for i, p in enumerate(right)],
                       "right"))
    return groups


def _row_spacing(lib_id: str) -> float:
    """Centre-to-centre distance between the left and right column groups."""
    cols = PINOUTS[lib_id]
    if not cols["right"]:
        return 0.0
    if lib_id == "Pi_Pico_W":
        return PICO_ROW_SPACING
    if lib_id == "RS232_2CH_Module":
        # Pico-form-factor HAT receptacle: same castellation row spacing so the
        # module mates pin-for-pin with the side header.
        return PICO_ROW_SPACING
    body = PACKAGES[lib_id]["body"]
    if body is not None:                       # place columns near the body edges
        return max(ROW_GAP, body[0] - 2.0)
    return ROW_GAP                             # body-less connector (e.g. stepper)


# ---------------------------------------------------------------------------
# Schematic (.kicad_sch) geometry. Quilter / DeepPCB also ask for the
# schematic alongside the .kicad_pcb / .kicad_pro, so we emit a matching
# KiCad 7 schematic from the *same* NETLIST/PINOUTS data, guaranteeing the
# schematic netlist is identical to the board's. Each part is a labelled
# rectangle symbol with one pin per physical pin (numbered exactly like the
# board pads), and connectivity is expressed with global net labels placed
# directly on the pin endpoints — KiCad treats matching global labels as
# electrically connected, so no wires are drawn. The board flips Y between
# the symbol-editor frame (Y up) and the schematic sheet (Y down): a pin
# whose connection point is at symbol-local (px, py) lands on the sheet at
# (instance_x + px, instance_y - py), and a global label placed there
# connects to it (verified with kicad-cli's netlist exporter).
# ---------------------------------------------------------------------------
SYMBOL_LIB_NICK = "powder_doser_parts"  # matches the board footprint library id
SCH_ROOT_UUID = "00000000-0000-0000-0003-000000000001"
SCH_BODY_HW = 6.35    # symbol rectangle half-width (mm)
SCH_PIN_LEN = 2.54    # pin graphic length (endpoint -> body edge)
SCH_STUB = SCH_BODY_HW + SCH_PIN_LEN  # pin connection-point half-extent


def _uid(group: str, *parts: object) -> str:
    """Deterministic UUID-shaped id (stable across runs, unlike salted hash())."""
    digest = sha256("|".join(map(str, parts)).encode()).hexdigest()[:12]
    return f"00000000-0000-0000-{group}-{digest}"


def _effects(size: float = 1.0) -> Effects:
    return Effects(font=Font(width=size, height=size, thickness=0.15))


def _pad_half(pad: Pad) -> tuple[float, float]:
    """Half width/height of a real library pad's copper (for body sizing)."""
    return pad.size.X / 2.0, pad.size.Y / 2.0


def _pad_layout(lib_id: str) -> list[tuple[str, str, float, float, str, str, Pad]]:
    """Local pad geometry for every physical pin, from real library footprints.

    Returns an ordered list of ``(number, pin_name, lx, ly, src_lib, src_name,
    src_pad)`` numbered ``1..`` in the left-then-right ``PINOUTS`` order (so the
    board pad numbers line up with the schematic pin numbers). Each record's
    ``(lx, ly)`` and ``src_pad`` come straight from the chosen real KiCad
    library footprint (``_part_groups``): the group's source pads are recentred
    about their own centroid and shifted to the body edge (left/right columns)
    or kept centred, preserving the real intra-group geometry (header pitch,
    radial-cap spacing, barrel-jack lug layout, Pico castellation spacing).
    """
    row = _row_spacing(lib_id)
    records: list[tuple[str, str, float, float, str, str, Pad]] = []
    num = 1
    for lib, name, pins, anchor in _part_groups(lib_id):
        pads = _lib_pads(lib, name)
        pts = [(pads[src].position.X, pads[src].position.Y) for _, src in pins]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        gx = -row / 2 if anchor == "left" else (row / 2 if anchor == "right" else 0.0)
        for (pin_name, src), (sx, sy) in zip(pins, pts):
            records.append((str(num), pin_name, sx - cx + gx, sy - cy,
                            lib, name, pads[src]))
            num += 1
    return records


def _footprint_id(lib_id: str) -> str:
    """The footprint library id used on the board (and in the schematic).

    A part carries the *real* library footprint id (e.g.
    ``Capacitor_THT:CP_Radial_D8.0mm_P3.50mm``) when that single library land
    pattern fully represents it on the board: passive discretes, the off-board
    actuators' mating connector, and the barrel jack (whose own library
    footprint is the body). Parts whose real land pattern is a generic 0.1"
    header overlaid with a separate vendor carrier body (the Pololu modules), or
    that are composed from two real connectors on opposite body edges (the
    breakouts), get a ``powder_doser_parts:`` project id so the id reflects the
    drawn part rather than the bare header.
    """
    groups = _part_groups(lib_id)
    if len(groups) == 1:
        lib, name, *_ = groups[0]
        body = PACKAGES[lib_id]["body"]
        # A module-kind carrier mounted via a *generic* 0.1" pin header overlays
        # its real vendor body on that header land pattern, so its id should not
        # masquerade as a bare header. Parts whose own library footprint is the
        # body (barrel jack, caps) keep the real id.
        generic_header = lib == "Connector_PinHeader_2.54mm"
        if not (generic_header and body is not None
                and PACKAGES[lib_id]["kind"] == "module"):
            return f"{lib}:{name}"
    return f"powder_doser_parts:{lib_id}"


def _is_header_carrier(lib_id: str) -> bool:
    """True for a module that mounts on a *generic* 0.1" pin header.

    These parts (Pi Pico W, the Waveshare RS-232 module, the Tic carrier) use a
    real ``Connector_PinHeader_2.54mm`` land pattern with a vendor body overlaid
    rather than their own dedicated library footprint, and they have no vendor
    STEP. The header library's own 3-D model is a bare vertical pin header,
    which renders as phantom pins sticking up where the module body sits, so it
    must not be attached as the part's 3-D model. The barrel jack and passive
    discretes (whose own library footprint *is* the body) are excluded.
    """
    return (PACKAGES[lib_id]["kind"] == "module"
            and PACKAGES[lib_id]["body"] is not None
            and all(lib == "Connector_PinHeader_2.54mm"
                    for lib, _name, *_ in _part_groups(lib_id)))


def _body_extents(lib_id: str) -> tuple[float, float]:
    """Half-width/height of one part's drawn body (F.Fab), no courtyard gap.

    Factored out of ``_make_footprint`` so the compact placer (``_pack_positions``)
    can size every part *before* the footprints are built. Sized to enclose the
    real library pads (their actual copper extents) and never below the real
    vendor body from ``PACKAGES``.
    """
    recs = _pad_layout(lib_id)
    x_lo = min(lx - _pad_half(pad)[0] for _n0, _pn, lx, ly, _l, _nm, pad in recs)
    x_hi = max(lx + _pad_half(pad)[0] for _n0, _pn, lx, ly, _l, _nm, pad in recs)
    y_lo = min(ly - _pad_half(pad)[1] for _n0, _pn, lx, ly, _l, _nm, pad in recs)
    y_hi = max(ly + _pad_half(pad)[1] for _n0, _pn, lx, ly, _l, _nm, pad in recs)
    pad_hw = max(abs(x_lo), abs(x_hi)) + SILK_MARGIN
    pad_hh = max(abs(y_lo), abs(y_hi)) + SILK_MARGIN
    pkg = PACKAGES[lib_id]
    if pkg["body"] is not None:
        return max(pad_hw, pkg["body"][0] / 2.0), max(pad_hh, pkg["body"][1] / 2.0)
    return pad_hw, pad_hh


def _courtyard_extents(lib_id: str) -> tuple[float, float]:
    """Half-width/height including the F.CrtYd clearance (collision footprint)."""
    body_hw, body_hh = _body_extents(lib_id)
    return body_hw + CRTYD_CLEARANCE, body_hh + CRTYD_CLEARANCE


def _pack_positions() -> dict[str, tuple[float, float]]:
    """Domain- and cluster-aware compact placement (centre coordinates).

    The first compact build replaced the *ridiculously spaced out* schematic
    floorplan (a ~279x199 mm board for 14 small breakouts; issue #94) with a
    pure area shelf-pack. That was tight but domain-blind, so the Edison
    placement review (``edison_artifacts/board_placement_review_for_powder_doser``)
    asked for a placement that gives the router short, local nets and a clean
    power/logic partition. This packer therefore:

      * packs each cluster in ``PLACEMENT_CLUSTERS`` (a regulator/driver with its
        caps and its off-board load connector) as one rigid contiguous row, so
        the high-value local nets (driver->load, regulator->cap) stay short;
      * stacks the power/mechanics domain on the left and the logic/control
        domain on the right, separated by a ``DOMAIN_GAP`` aisle, so the noisy
        +12 V switching is partitioned from the quiet 3V3/I2C control nets;
      * orders each cluster row so its off-board connector (``EDGE_REFS``) sits
        at the outward end of the row (left edge of the left domain, right edge
        of the right domain), biasing cables toward the board perimeter while
        keeping the connector adjacent to the driver it serves.

    Keeping clusters intact (rather than pulling every connector into a separate
    bottom edge band) was the variant that did *not* inflate the ratsnest: a
    literal edge band shortens cable exit but lengthens every driver->connector
    net, so full edge pinning is left as documented future work (note 21).

    The layout is fully deterministic (fixed cluster order) and
    ``_assert_no_overlap`` still guarantees it is DRC-clean.
    """
    ext = {ref: _courtyard_extents(lib_id) for ref, lib_id, *_ in NETLIST}

    # Guard the PLACEMENT_CLUSTERS <-> NETLIST invariant: every part must be
    # packed exactly once. Catches a NETLIST edit that forgets to update the
    # clusters (the unplaced ref would otherwise silently land at the origin).
    netlist_refs = {ref for ref, *_ in NETLIST}
    clustered: list[str] = [r for _dom, _name, refs in PLACEMENT_CLUSTERS for r in refs]
    missing = netlist_refs - set(clustered)
    extra = set(clustered) - netlist_refs
    dupes = sorted({r for r in clustered if clustered.count(r) > 1})
    if missing or extra or dupes:
        raise ValueError(
            "PLACEMENT_CLUSTERS must cover every NETLIST ref exactly once: "
            f"missing={sorted(missing)} unknown={sorted(extra)} duplicated={dupes}")

    def w(ref: str) -> float:
        return 2 * ext[ref][0]

    def h(ref: str) -> float:
        return 2 * ext[ref][1]

    def order_row(refs: list[str], connector_first: bool) -> list[str]:
        """Move the cluster's off-board connector to the row's outward end."""
        conns = [r for r in refs if r in EDGE_REFS]
        rest = [r for r in refs if r not in EDGE_REFS]
        return (conns + rest) if connector_first else (rest + conns)

    positions: dict[str, tuple[float, float]] = {}

    def pack_domain(rows: list[list[str]], x_left: float, connector_first: bool
                    ) -> tuple[float, float]:
        """Stack each cluster as a left-to-right row; return (width, height)."""
        cy = 0.0
        max_w = 0.0
        for refs in rows:
            refs = order_row(refs, connector_first)
            row_h = max(h(r) for r in refs)
            cx = x_left
            for r in refs:
                positions[r] = (cx + ext[r][0], cy + row_h / 2.0)
                cx += w(r) + PLACE_GAP
            max_w = max(max_w, cx - PLACE_GAP - x_left)
            cy += row_h + PLACE_GAP
        return max_w, (cy - PLACE_GAP if rows else 0.0)

    rows_by_domain: dict[str, list[list[str]]] = {"power": [], "logic": []}
    for domain, _name, refs in PLACEMENT_CLUSTERS:
        rows_by_domain[domain].append(list(refs))

    # Power/mechanics domain on the left (connectors biased to the left edge),
    # logic/control domain on the right (connectors biased to the right edge).
    power_w, _ = pack_domain(rows_by_domain["power"], 0.0, connector_first=True)
    pack_domain(rows_by_domain["logic"], power_w + DOMAIN_GAP, connector_first=False)
    return positions


def _make_footprint(ref: str, lib_id: str, x: float, y: float,
                    pin_nets: dict[str, str], nets: dict[str, Net],
                    sym_uuid: str | None = None) -> tuple[Footprint, list[tuple[float, float]], tuple[float, float]]:
    """Build one footprint from real KiCad library pads + the vendor body.

    Returns the footprint, the world (x, y) of every pad, and its courtyard
    half-extents (hw, hh). Each pad is a deep copy of the matching real library
    pad (``_pad_layout``) with the net / number / pin function applied, so the
    land pattern is a genuine KiCad footprint rather than a synthesized header.

    ``sym_uuid`` is the UUID of this part's schematic symbol instance
    (``_symbol_uuid``); when given, the footprint records ``(path "/<uuid>")``
    so KiCad / Quilter link it back to that symbol. Every part on this board is
    through-hole, so ``(attr through_hole)`` is always emitted — without these
    two fields Quilter reports a *"component mismatch ... pin count mismatch"*
    because it cannot pair the footprint with its schematic symbol.
    """
    fp = Footprint.create_new(
        library_id=_footprint_id(lib_id),
        value=lib_id,
        reference=ref,
    )
    fp.version = KICAD7_PCB_VERSION
    fp.position = Position(x, y, 0)
    fp.layer = "F.Cu"
    fp.tedit = "00000000"  # fixed so regeneration is byte-for-byte reproducible
    # Link the footprint to its schematic symbol (the pairing Quilter/KiCad use
    # to match pin counts). All parts here are through-hole.
    fp.attributes.type = "through_hole"
    if sym_uuid is not None:
        fp.path = f"/{sym_uuid}"

    records = _pad_layout(lib_id)
    sources = sorted({f"{lib}:{name}" for _n, _pn, _lx, _ly, lib, name, _p in records})
    fp.description = ("Powder-doser starter-board part; real land pattern(s): "
                      + ", ".join(sources))

    pad_world: list[tuple[float, float]] = []
    for number, pin_name, lx, ly, _lib, _name, src_pad in records:
        pad = copy.deepcopy(src_pad)
        pad.number = number
        pad.position = Position(round(lx, 4), round(ly, 4), 0)
        pad.net = nets.get(pin_nets.get(pin_name, ""))
        pad.pinFunction = pin_name
        pad.tstamp = _uid("00aa", lib_id, ref, number)
        fp.pads.append(pad)
        pad_world.append((x + lx, y + ly))

    # Real component body outline (F.Fab) + courtyard (F.CrtYd) + silk, sized
    # from the committed vendor files (PACKAGES). The outline never shrinks
    # below the real library pad cluster, so the pads always stay inside.
    pkg = PACKAGES[lib_id]
    body_hw, body_hh = _body_extents(lib_id)

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

    # Attach a real 3-D model: the vendor STEP from PACKAGES (resolves once
    # PR #25 is merged) when one is recorded, else the library footprint's own
    # KiCad 3-D model. KiCad simply omits a missing model, so the .kicad_pcb
    # stays self-contained.
    #
    # Exception: a module that mounts on a *generic* 0.1" pin header (Pico W,
    # the RS-232 module, the Tic carrier) has no vendor STEP, and the library
    # footprint's own model is a bare vertical pin header. Attaching it renders
    # as a column of pins sticking straight up exactly where the module body
    # sits on top of the header — misleading in the 3-D view (reported on the
    # Pico/RS-232 positions). For these the model is omitted: KiCad then shows
    # the real F.Fab body outline with no phantom pins. A proper module STEP
    # (e.g. RPi_Pico, the Waveshare module) can be dropped into PACKAGES later.
    if pkg["model"]:
        fp.models.append(Model(path=pkg["model"]))
    elif not _is_header_carrier(lib_id):
        lib, name, *_ = _part_groups(lib_id)[0]
        model = _lib_model(lib, name)
        if model is not None:
            fp.models.append(copy.deepcopy(model))

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
                    f"footprints {ra} and {rb} overlap; increase PLACE_GAP or "
                    "adjust their cluster order in PLACEMENT_CLUSTERS")


def build_board(mode: str = "placed") -> tuple[Board, tuple[float, float], dict[str, Net]]:
    """Build the starter board.

    ``mode="placed"`` (default) emits the compact, pre-placed board this
    generator lays out. ``mode="unplaced"`` emits the *same* parts and nets but
    staged entirely **outside** an empty board outline, so autonomous tools
    (DeepPCB/Quilter) can be tested on placement as well as routing. In both
    modes the empty/target outline is identical, so the two variants target the
    same board area.
    """
    if mode not in ("placed", "unplaced"):
        raise ValueError(f"unknown board mode {mode!r}")
    board = Board.create_new()
    board.version = KICAD7_PCB_VERSION
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

    # Compact placement (centre coords) and the resulting *placed* board outline.
    positions = _pack_positions()
    ext = {ref: _courtyard_extents(lib_id) for ref, lib_id, *_ in NETLIST}
    x0 = min(positions[r][0] - ext[r][0] for r in positions) - EDGE_MARGIN
    x1 = max(positions[r][0] + ext[r][0] for r in positions) + EDGE_MARGIN
    y0 = min(positions[r][1] - ext[r][1] for r in positions) - EDGE_MARGIN
    y1 = max(positions[r][1] + ext[r][1] for r in positions) + EDGE_MARGIN

    # The "placed" outline encloses this generator's own placement. The
    # "unplaced" outline is an independent, right-sized empty rectangle for
    # Quilter/DeepPCB to auto-place into (Quilter can't resize it itself), so it
    # is *not* tied to the wider placed floorplan — that's the wasted space the
    # review flagged. Keep the same lower-left origin (x0, y0).
    if mode == "unplaced":
        ow, oh = UNPLACED_OUTLINE_MM
        x1, y1 = x0 + ow, y0 + oh
    bw, bh = x1 - x0, y1 - y0

    # In the unplaced variant, shift every part one outline-width + gap to the
    # right so it sits wholly outside the (now empty) outline.
    dx = bw + STAGE_GAP if mode == "unplaced" else 0.0

    courtyards: list[tuple[str, float, float, float, float]] = []
    for ref, lib_id, x, y, pins in NETLIST:
        px, py = positions[ref][0] + dx, positions[ref][1]
        pin_nets = {pin: net for pin, net in pins}
        # Schematic-symbol anchor (build_schematic uses the same coords) → the
        # UUID the footprint's (path ...) must reference so Quilter pairs them.
        sym_uuid = _symbol_uuid(lib_id, ref, float(x) * FLOORPLAN_SCALE,
                                float(y) * FLOORPLAN_SCALE)
        fp, pad_world, (hw, hh) = _make_footprint(ref, lib_id, px, py, pin_nets,
                                                  nets, sym_uuid)
        board.footprints.append(fp)
        courtyards.append((ref, px - hw, py - hh, px + hw, py + hh))

    _assert_no_overlap(courtyards)

    # Board outline (Edge.Cuts rectangle): in "placed" mode it encloses every
    # courtyard; in "unplaced" mode it is the right-sized empty target rectangle
    # while the parts sit staged to its right.
    rect = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    for (ax, ay), (bx, by) in zip(rect, rect[1:]):
        board.graphicItems.append(GrLine(start=Position(ax, ay), end=Position(bx, by),
                                         layer="Edge.Cuts", width=0.1))
    return board, (bw, bh), nets


def write_project(net_names_by_class: dict[str, list[str]],
                  name: str = BOARD_NAME) -> None:
    """Write a minimal .kicad_pro with Default + Power net classes (DRC rules).

    Also registers the root schematic sheet (``SCH_ROOT_UUID``) so the
    ``.kicad_pcb`` / ``.kicad_pro`` / ``.kicad_sch`` open together as one
    coherent KiCad project (the trio Quilter / DeepPCB ask for).
    """
    pro = {
        "board": {"design_settings": {"rules": {"min_clearance": 0.2,
                                                 "min_track_width": 0.25}}},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "net_settings": {
            # Power class clearance is held at the board min (0.2 mm, not 0.3)
            # so a 0.6 mm power trace can break out between adjacent 0.1" header
            # pads (copper-to-copper gap is only PITCH-PAD_SIZE = 0.84 mm); wide
            # power nets still neck down through headers, which is exactly the
            # behaviour the DeepPCB/Quilter routing test is meant to exercise
            # (see edison_artifacts/board_placement_review_for_powder_doser).
            "classes": [
                {"name": "Default", "clearance": 0.2, "track_width": 0.25,
                 "via_diameter": 0.8, "via_drill": 0.4,
                 "microvia_diameter": 0.3, "microvia_drill": 0.2,
                 "diff_pair_gap": 0.25, "diff_pair_width": 0.2},
                {"name": "Power", "clearance": 0.2, "track_width": 0.6,
                 "via_diameter": 1.0, "via_drill": 0.5,
                 "microvia_diameter": 0.3, "microvia_drill": 0.2,
                 "diff_pair_gap": 0.25, "diff_pair_width": 0.2},
            ],
            "netclass_assignments": {n: "Power" for n in net_names_by_class["Power"]},
        },
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[SCH_ROOT_UUID, ""]],
        "meta": {"filename": f"{name}.kicad_pro", "version": 1},
    }
    (HERE / f"{name}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Schematic (.kicad_sch) generation, from the same NETLIST / PINOUTS data.
# ---------------------------------------------------------------------------
def _symbol_pin_layout(lib_id: str) -> tuple[list[tuple[str, float, float, int, int]], float]:
    """Pin geometry for one symbol, derived from PINOUTS.

    Returns ``(records, half_h)`` where each record is ``(name, px, py, angle,
    number)``: the pin's symbol-local connection point (Y up), its KiCad
    orientation, and its pin number. Pins are numbered left column first then
    right column - identical to the board pad numbering in ``_make_footprint``
    - and laid out on the same 0.1" pitch / column centring as the board pads,
    so the schematic mirrors the board exactly. Pin *names* may repeat (e.g.
    the Pico's eight GND pins); the numbers are always unique, so the records
    are returned as an ordered list rather than a name-keyed dict.
    """
    cols = PINOUTS[lib_id]
    left, right = cols["left"], cols["right"]

    def col_y(i: int, n: int) -> float:  # board/page convention (Y down)
        return (i - (n - 1) / 2.0) * PITCH

    records: list[tuple[str, float, float, int, int]] = []
    num = 1
    for i, pin in enumerate(left):
        records.append((pin, -SCH_STUB, -col_y(i, len(left)), 0, num))  # Y up = -page Y
        num += 1
    for j, pin in enumerate(right):
        records.append((pin, SCH_STUB, -col_y(j, len(right)), 180, num))
        num += 1
    n_rows = max(len(left), len(right)) or 1
    half_h = (n_rows - 1) / 2.0 * PITCH + PITCH
    return records, half_h


def _sym_pin(name: str, number: int, x: float, y: float, angle: int) -> str:
    return (f'        (pin passive line (at {x:g} {y:g} {angle}) (length {SCH_PIN_LEN:g})\n'
            f'          (name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'          (number "{number}" (effects (font (size 1.27 1.27))))\n'
            f'        )')


def _lib_symbol(lib_id: str) -> str:
    records, half_h = _symbol_pin_layout(lib_id)
    pins = [_sym_pin(name, number, px, py, angle)
            for name, px, py, angle, number in records]
    body = (f'(rectangle (start {-SCH_BODY_HW:g} {half_h:g}) (end {SCH_BODY_HW:g} {-half_h:g})\n'
            f'        (stroke (width 0.254) (type default)) (fill (type background)))')
    name = f"{SYMBOL_LIB_NICK}:{lib_id}"
    fp_id = _footprint_id(lib_id)
    return (f'    (symbol "{name}" (in_bom yes) (on_board yes)\n'
            f'      (property "Reference" "U" (id 0) (at {-SCH_BODY_HW:g} {half_h + 2.54:g} 0)\n'
            f'        (effects (font (size 1.27 1.27))))\n'
            f'      (property "Value" "{lib_id}" (id 1) (at {-SCH_BODY_HW:g} {half_h + 0.8:g} 0)\n'
            f'        (effects (font (size 1.27 1.27))))\n'
            f'      (property "Footprint" "{fp_id}" (id 2) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'      (property "Datasheet" "" (id 3) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'      (symbol "{lib_id}_0_1" {body})\n'
            f'      (symbol "{lib_id}_1_1"\n' + "\n".join(pins) + "\n      )\n    )")


def _symbol_uuid(lib_id: str, ref: str, x: float, y: float) -> str:
    """Deterministic UUID of a schematic symbol instance.

    Shared by the schematic writer (``_sym_instance``) and the board writer
    (``build_board``) so each board footprint can carry a ``(path "/<uuid>")``
    back to *its* schematic symbol — the link KiCad (and Quilter) use to match
    a footprint to its symbol. Keeping the two in one place guarantees they can
    never drift apart.
    """
    return _uid("0001", lib_id, ref, x, y)


def _sym_instance(lib_id: str, ref: str, x: float, y: float, half_h: float,
                  project: str = BOARD_NAME) -> str:
    uid = _symbol_uuid(lib_id, ref, x, y)
    rx, ry = x - SCH_BODY_HW, y - half_h
    fp_id = _footprint_id(lib_id)
    return (f'  (symbol (lib_id "{SYMBOL_LIB_NICK}:{lib_id}") (at {x:g} {y:g} 0) (unit 1)\n'
            f'    (in_bom yes) (on_board yes) (dnp no)\n'
            f'    (uuid "{uid}")\n'
            f'    (property "Reference" "{ref}" (id 0) (at {rx:g} {ry - 3.81:g} 0)\n'
            f'      (effects (font (size 1.27 1.27)) (justify left)))\n'
            f'    (property "Value" "{lib_id}" (id 1) (at {rx:g} {ry - 1.27:g} 0)\n'
            f'      (effects (font (size 1.27 1.27)) (justify left)))\n'
            f'    (property "Footprint" "{fp_id}" (id 2) (at {x:g} {y:g} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Datasheet" "" (id 3) (at {x:g} {y:g} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide))\n'
            f'    (instances\n'
            f'      (project "{project}"\n'
            f'        (path "/{SCH_ROOT_UUID}" (reference "{ref}") (unit 1))\n'
            f'      )\n'
            f'    )\n'
            f'  )')


def _global_label(net: str, x: float, y: float, rot: int) -> str:
    uid = _uid("0009", net, x, y)
    return (f'  (global_label "{net}" (shape input) (at {x:g} {y:g} {rot}) (fields_autoplaced)\n'
            f'    (effects (font (size 1.27 1.27)) (justify left))\n'
            f'    (uuid "{uid}")\n'
            f'  )')


def _wire(x1: float, y1: float, x2: float, y2: float) -> str:
    uid = _uid("0004", x1, y1, x2, y2)
    return (f'  (wire (pts (xy {x1:g} {y1:g}) (xy {x2:g} {y2:g}))\n'
            f'    (stroke (width 0) (type default)) (uuid "{uid}")\n'
            f'  )')


# Stub length from each pin endpoint out to its net label, so labels read
# clear of the symbol body / pin-name text instead of overlapping it. KiCad
# joins pin -> stub wire -> global label, so connectivity is unchanged.
SCH_STUB_OUT = 5.08


def build_schematic(project: str = BOARD_NAME) -> str:
    """Compose a self-contained KiCad 7 schematic for the starter board.

    ``project`` names the owning KiCad project in each symbol instance; it must
    match the trio's ``.kicad_pcb`` / ``.kicad_pro`` base name (Quilter and
    KiCad use the project name + symbol UUID to tie a schematic symbol to its
    board footprint), so the placed and unplaced variants pass their own name.
    """
    lib_ids: list[str] = []
    for _, lib_id, *_ in NETLIST:
        if lib_id not in lib_ids:
            lib_ids.append(lib_id)
    lib_symbols = "  (lib_symbols\n" + "\n".join(_lib_symbol(l) for l in lib_ids) + "\n  )"

    body: list[str] = []
    placed: dict[tuple[float, float], str] = {}
    for ref, lib_id, x, y, pins in NETLIST:
        px, py = float(x) * FLOORPLAN_SCALE, float(y) * FLOORPLAN_SCALE
        records, half_h = _symbol_pin_layout(lib_id)
        body.append(_sym_instance(lib_id, ref, px, py, half_h, project))
        pin_nets = {pin_name: net for pin_name, net in pins}
        pin_names = {name for name, *_ in records}
        for pin_name in pin_nets:
            if pin_name not in pin_names:
                raise KeyError(f"{lib_id!r} has no pin {pin_name!r}; check PINOUTS")
        # Wire every *physical* pin whose name is netted (so e.g. all eight Pico
        # GND pins land on GND, matching the board's pad nets). Unnetted pins
        # (unused GPIO, the barrel-jack switch lug) stay no-connect.
        for pin_name, ppx, ppy, angle, _ in records:
            if pin_name not in pin_nets:
                continue
            net = pin_nets[pin_name]
            tip_x, tip_y = round(px + ppx, 4), round(py - ppy, 4)  # sheet pin endpoint
            # Push the label outward (left pins to -x, right pins to +x) along a
            # short stub wire so the label text doesn't sit on the pin name.
            lx = round(tip_x - SCH_STUB_OUT if angle == 0 else tip_x + SCH_STUB_OUT, 4)
            ly = tip_y
            key = (lx, ly)
            if key in placed and placed[key] != net:
                raise ValueError(
                    f"label for {ref}.{pin_name} ({net}) collides with net {placed[key]} "
                    f"at ({lx}, {ly})")
            placed[key] = net
            body.append(_wire(tip_x, tip_y, lx, ly))
            body.append(_global_label(net, lx, ly, 180 if angle == 0 else 0))

    title_block = (
        '  (title_block\n'
        '    (title "Powder-doser test-module starter board")\n'
        '    (rev "A")\n'
        '    (company "Vertical Cloud Lab")\n'
        f'    (comment 1 "Schematic companion to {project}.kicad_pcb")\n'
        '    (comment 2 "Netlist transcribed from PR #61 generate.py; upload trio for Quilter/DeepPCB")\n'
        '  )')
    header = (f'(kicad_sch (version 20230121) (generator powder_doser_build_starter_board)\n'
              f'  (uuid "{SCH_ROOT_UUID}")\n'
              f'  (paper "A3")\n'
              f'{title_block}\n'
              f'{lib_symbols}\n')
    footer = ('  (sheet_instances\n'
              '    (path "/" (page "1"))\n'
              '  )\n)\n')
    return header + "\n".join(body) + "\n" + footer


def validate_schematic_netlist(sch_path: Path) -> None:
    """If kicad-cli is present, export the netlist and assert every wired pin
    landed on its intended net (no ``unconnected-`` stragglers). This catches
    any label/pin misalignment exactly as KiCad's connectivity engine sees it.
    Skipped silently when kicad-cli is unavailable (e.g. CI / sandbox)."""
    cli = shutil.which("kicad-cli")
    if not cli:
        print("note: kicad-cli not on PATH; skipping schematic netlist check", flush=True)
        return
    net_path = sch_path.with_suffix(".net")
    try:
        proc = subprocess.run(
            [cli, "sch", "export", "netlist", "--format", "kicadsexpr",
             "-o", str(net_path), str(sch_path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"kicad-cli netlist export failed (exit {proc.returncode}):\n"
                + (proc.stderr or "").strip())
        txt = net_path.read_text()
        net_nodes: dict[str, set[tuple[str, str]]] = {}
        for m in re.finditer(
                r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)', txt, re.S):
            name, nodes = m.group(1), set(re.findall(
                r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)))
            net_nodes[name] = nodes
        errors = []
        n_conn = 0
        for ref, lib_id, _x, _y, pins in NETLIST:
            records, _ = _symbol_pin_layout(lib_id)
            pin_nets = {pin_name: net for pin_name, net in pins}
            for pin_name, _ppx, _ppy, _angle, number in records:
                if pin_name not in pin_nets:
                    continue
                n_conn += 1
                net = pin_nets[pin_name]
                if (ref, str(number)) not in net_nodes.get(net, set()):
                    errors.append(f"{ref}.{pin_name} (#{number}) not on net {net}")
        if errors:
            raise ValueError("schematic connectivity check failed:\n  " + "\n  ".join(errors))
        print(f"verified schematic netlist: {n_conn} pins connected across "
              f"{len([n for n in net_nodes if not n.startswith('unconnected-')])} named nets")
    finally:
        net_path.unlink(missing_ok=True)


def render_schematic_preview(sch_path: Path) -> None:
    """Render the schematic to SVG via kicad-cli when present (committed as
    test_module_starter_schematic.svg). Skipped when kicad-cli is unavailable."""
    cli = shutil.which("kicad-cli")
    if not cli:
        print("note: kicad-cli not on PATH; skipping schematic render", flush=True)
        return
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        subprocess.run(
            [cli, "sch", "export", "svg", "--no-background-color",
             "--exclude-drawing-sheet", "-o", str(tmp), str(sch_path)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        produced = tmp / f"{sch_path.stem}.svg"
        if produced.exists():
            dest = sch_path.with_name(f"{sch_path.stem}_schematic.svg")
            shutil.copyfile(produced, dest)
            print(f"wrote {dest.name}")
            try:
                import cairosvg  # type: ignore
            except ImportError:
                print("note: cairosvg not installed; skipping schematic PNG", flush=True)
                return
            png = dest.with_suffix(".png")
            cairosvg.svg2png(url=str(dest), write_to=str(png), output_width=1100)
            print(f"wrote {png.name}")


def _render_svg_fallback(pcb_path: Path) -> Path:
    """Write a dependency-free SVG preview straight from the board model.

    Used when ``kicad-cli`` is not installed, so the preview is reproducible
    in the headless sandbox / CI. Draws the Edge.Cuts outline, each component's
    real F.Fab body rectangle + reference, every pad, and the unrouted ratsnest
    (pads sharing a net), matching what ``kicad-cli`` would render.
    """
    board = Board.from_file(str(pcb_path))

    # View bounds: include the Edge.Cuts outline *and* every footprint, so the
    # unplaced variant (parts staged outside the outline) is fully visible.
    ex, ey = [], []
    for g in board.graphicItems:
        if isinstance(g, GrLine) and g.layer == "Edge.Cuts":
            ex += [g.start.X, g.end.X]
            ey += [g.start.Y, g.end.Y]
    for fp in board.footprints:
        fx, fy = fp.position.X, fp.position.Y
        for p in fp.pads:
            ex.append(fx + p.position.X)
            ey.append(fy + p.position.Y)
        for g in fp.graphicItems:
            if isinstance(g, FpLine):
                ex += [fx + g.start.X, fx + g.end.X]
                ey += [fy + g.start.Y, fy + g.end.Y]
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


def write_variant(name: str, mode: str) -> dict:
    """Write one .kicad_pcb/.kicad_sch/.kicad_pro trio + previews; return summary."""
    board, (bw, bh), nets = build_board(mode)
    pcb_path = HERE / f"{name}.kicad_pcb"
    board.to_file(str(pcb_path))

    power = sorted(n for n in nets if n in POWER_NETS and n)
    write_project({"Power": power}, name)

    # Schematic uses the same netlist for both variants; only the owning project
    # name differs so each trio (sch/pcb/pro) shares one project name — the link
    # Quilter/KiCad use (project name + symbol UUID) to pair symbol↔footprint.
    schematic_text = build_schematic(name)
    sch_path = HERE / f"{name}.kicad_sch"
    sch_path.write_text(schematic_text)

    print(f"wrote {pcb_path.name}: {len(NETLIST)} footprints, "
          f"{len(nets) - 1} nets, outline {bw:.1f}x{bh:.1f} mm ({mode})")
    print(f"wrote {sch_path.name}: {len(NETLIST)} symbols, {len(nets) - 1} nets")
    render_preview(pcb_path)
    validate_schematic_netlist(sch_path)
    render_schematic_preview(sch_path)
    return {
        "board": f"{name}.kicad_pcb",
        "schematic": f"{name}.kicad_sch",
        "project": f"{name}.kicad_pro",
        "mode": mode,
        "outline_mm": [round(bw, 2), round(bh, 2)],
        "power_nets": power,
    }


def main() -> None:
    # Variant 1: compact, pre-placed board (this generator's placement).
    placed = write_variant(BOARD_NAME, "placed")
    # Variant 2: same parts staged outside an empty outline, for testing the
    # routers' auto-placement (compare against the placed variant).
    unplaced = write_variant(UNPLACED_NAME, "unplaced")

    # Human-readable BOM / net summary for review and provenance.
    summary = {
        "board": placed["board"],
        "schematic": placed["schematic"],
        "project": placed["project"],
        "components": len(NETLIST),
        "nets": len({net for *_, pins in NETLIST for _, net in pins}),
        "outline_mm": placed["outline_mm"],
        "power_nets": placed["power_nets"],
        "unplaced_variant": {
            "board": unplaced["board"],
            "schematic": unplaced["schematic"],
            "project": unplaced["project"],
            "outline_mm": unplaced["outline_mm"],
            "note": ("Same netlist/parts as the placed board, but every "
                     "footprint is staged outside the (empty) board outline so "
                     "DeepPCB/Quilter can be tested on auto-placement, not just "
                     "routing."),
        },
        "bom": [{
            "ref": r,
            "part": lib,
            "kind": PACKAGES[lib]["kind"],
            "pins": len(PINOUTS[lib]["left"]) + len(PINOUTS[lib]["right"]),
            "pins_netted": len(p),
            "body_mm": list(PACKAGES[lib]["body"]) if PACKAGES[lib]["body"] else None,
            "model": PACKAGES[lib]["model"],
            "source": PACKAGES[lib]["source"],
        } for r, lib, _, _, p in NETLIST],
    }
    (HERE / "starter_board_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote starter_board_summary.json (placed {placed['outline_mm']} mm, "
          f"unplaced {unplaced['outline_mm']} mm)")


if __name__ == "__main__":
    main()

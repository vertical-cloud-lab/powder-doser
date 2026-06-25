#!/usr/bin/env python3
"""
Generate the satellite-rev-a KiCad 7 project for the powder-doser §3.4
satellite PCB outline. Emits:

  hardware/kicad/satellite-rev-a/satellite.kicad_pro
  hardware/kicad/satellite-rev-a/satellite.kicad_sch
  hardware/kicad/satellite-rev-a/satellite.kicad_pcb

Idempotent: running it again overwrites cleanly. Run from repo root.

This is a *placed-but-unrouted* board capture: every component from §3.4
is instantiated, with the schematic showing each symbol annotated with
hierarchical (global) labels naming the nets from the §3.4 pin-assignment
table, and the PCB showing each footprint placed in the region planned
in §3.4 (TMC2209 socketed at center, USB-C on +X edge, 12 V terminal on
-X edge, JST stepper headers on -Y edge, JST PH solenoid/ERM headers on
+Y edge, servo header on +Y edge, BOOTSEL/RUN buttons + status LED on
-X edge). Net routing (copper traces) is intentionally left for the
follow-up PR after the topology is approved; what's here is the
schematic capture + mechanical layout outline that the brainstorm
promised.

Net naming matches §3.4's RP2040 pin-assignment table verbatim
(STEP / DIR / nEN / TAP / SERVO / SDA / SCL / UART_TX / UART_RX, plus
+12V / +5V / +3V3 / GND power rails and USB_DP / USB_DM).
"""
from __future__ import annotations
import os, sys, uuid, time, pathlib, textwrap

REPO = pathlib.Path(__file__).resolve().parents[2] / "powder-doser"
# When invoked from the repo, use cwd:
if not REPO.exists():
    REPO = pathlib.Path.cwd()
OUT = REPO / "hardware" / "kicad" / "satellite-rev-a"
OUT.mkdir(parents=True, exist_ok=True)

def U(): return str(uuid.uuid4())

# ---------------------------------------------------------------- project file
PRO = """{
  "board": {
    "design_settings": {
      "defaults": {
        "board_outline_line_width": 0.1,
        "copper_line_width": 0.2,
        "copper_text_size_h": 1.5,
        "copper_text_size_v": 1.5,
        "copper_text_thickness": 0.3,
        "other_line_width": 0.15,
        "silk_line_width": 0.15,
        "silk_text_size_h": 1.0,
        "silk_text_size_v": 1.0,
        "silk_text_thickness": 0.15
      },
      "diff_pair_dimensions": [],
      "drc_exclusions": [],
      "rules": {
        "min_clearance": 0.2,
        "min_track_width": 0.2,
        "min_via_diameter": 0.6,
        "min_via_drill": 0.3
      },
      "track_widths": [0.0, 0.25, 0.5, 1.0],
      "via_dimensions": [
        {"diameter": 0.0, "drill": 0.0},
        {"diameter": 0.6, "drill": 0.3}
      ]
    },
    "layer_presets": [],
    "viewports": []
  },
  "boards": [],
  "cvpcb": {"equivalence_files": []},
  "erc": {"erc_exclusions": [], "meta": {"version": 0}, "pin_map": [], "rule_severities": {}, "rule_severitieslegacy": {}},
  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
  "meta": {"filename": "satellite.kicad_pro", "version": 1},
  "net_settings": {
    "classes": [
      {"clearance": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
       "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1, "name": "Default",
       "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
       "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3, "wire_width": 6}
    ],
    "meta": {"version": 3},
    "net_colors": null,
    "netclass_assignments": null,
    "netclass_patterns": []
  },
  "pcbnew": {
    "last_paths": {"gencad": "", "idf": "", "netlist": "", "specctra_dsn": "", "step": "",
                   "vrml": "", "plot": ""},
    "page_layout_descr_file": ""
  },
  "schematic": {
    "annotate_start_num": 0,
    "drawing": {
      "dashed_lines_dash_length_ratio": 12.0,
      "dashed_lines_gap_length_ratio": 3.0,
      "default_line_thickness": 6.0,
      "default_text_size": 50.0,
      "field_names": [],
      "intersheets_ref_own_page": false,
      "intersheets_ref_prefix": "",
      "intersheets_ref_short": false,
      "intersheets_ref_show": false,
      "intersheets_ref_suffix": "",
      "junction_size_choice": 3,
      "label_size_ratio": 0.375,
      "pin_symbol_size": 25.0,
      "text_offset_ratio": 0.15
    },
    "legacy_lib_dir": "",
    "legacy_lib_list": [],
    "meta": {"version": 1},
    "net_format_name": "",
    "page_layout_descr_file": "",
    "plot_directory": "",
    "spice_adjust_passive_values": false,
    "spice_external_command": "spice \\\"%I\\\"",
    "subpart_first_id": 65,
    "subpart_id_separator": 0
  },
  "sheets": [["__SHEETUUID__", ""]],
  "text_variables": {}
}
"""

# --------------------------------------------------------------------- helpers
def lib_sym_block(name: str) -> str:
    """Return the (symbol \"...\") subtree for one library symbol pulled
    from /usr/share/kicad/symbols/<lib>.kicad_sym, rewriting the top-level
    symbol name from \"Lib:Name\" to the lib_id we want, so the schematic
    loads even on a system without the library tables configured."""
    lib, ent = name.split(":")
    src = pathlib.Path(f"/usr/share/kicad/symbols/{lib}.kicad_sym").read_text()
    # find "(symbol \"<ent>\" ..." then balance parens
    needle = f'(symbol "{ent}"'
    i = src.find(needle)
    if i < 0:
        raise SystemExit(f"symbol {name} not found")
    # find balanced end
    depth = 0
    j = i
    while j < len(src):
        c = src[j]
        if c == '(': depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                j += 1; break
        j += 1
    block = src[i:j]
    # rename to library-qualified id so the instance can find it in lib_symbols
    block = block.replace(f'(symbol "{ent}"', f'(symbol "{name}"', 1)
    return block

# --------------------------------------------------------------- schematic gen
SHEET_UUID = U()

# ---- components: (ref, lib_id, x_mm, y_mm, value, footprint)
COMPS = [
    ("U1", "MCU_RaspberryPi:RP2040",      150, 100, "RP2040",   "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm"),
    ("U2", "Driver_Motor:DRV8871DDA",      80,  90, "DRV8871",  "Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm"),
    ("U3", "Driver_Haptic:DRV2605LDGS",    80, 130, "DRV2605L", "Package_SO:MSOP-10-1EP_3x3mm_P0.5mm_EP1.68x1.88mm"),
    ("J1", "Connector:USB_C_Receptacle_USB2.0_14P", 220, 70, "USB-C", "Connector_USB:USB_C_Receptacle_GCT_USB4085"),
    ("J2", "Connector:Screw_Terminal_01x02",     50,  70, "+12V/GND", "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"),
    ("J3", "Connector_Generic:Conn_01x04",      120, 170, "STEPPER_A", "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"),
    ("J4", "Connector_Generic:Conn_01x04",      170, 170, "STEPPER_B", "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"),
    ("J5", "Connector_Generic:Conn_01x02",       70, 175, "SOLENOID",  "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal"),
    ("J6", "Connector_Generic:Conn_01x02",       70, 195, "ERM/LRA",   "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal"),
    ("J7", "Connector_Generic:Conn_01x03",      220, 180, "SERVO",     "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"),
    ("J8", "Connector_Generic:Conn_02x08_Odd_Even", 150, 50, "TMC2209_SOCKET",
            "Connector_PinSocket_2.54mm:PinSocket_2x08_P2.54mm_Vertical"),
    ("U4", "Connector_Generic:Conn_01x04",       50, 110, "MP1584 buck module",
            "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"),
    ("D1", "Device:LED",                         60, 145, "STATUS",
            "LED_SMD:LED_0805_2012Metric"),
    ("R1", "Device:R",                           70, 135, "1k",
            "Resistor_SMD:R_0805_2012Metric"),
    ("R2", "Device:R",                          230, 100, "5.1k",  # USB-C CC1
            "Resistor_SMD:R_0805_2012Metric"),
    ("R3", "Device:R",                          230, 110, "5.1k",  # USB-C CC2
            "Resistor_SMD:R_0805_2012Metric"),
    ("SW1","Switch:SW_Push",                     45, 145, "BOOTSEL",
            "Button_Switch_SMD:SW_SPST_SKQG_WithoutStem"),
    ("SW2","Switch:SW_Push",                     45, 165, "RUN",
            "Button_Switch_SMD:SW_SPST_SKQG_WithoutStem"),
    ("C1", "Device:C",                           90,  75, "100uF/25V",
            "Capacitor_SMD:CP_Elec_6.3x7.7"),
    ("C2", "Device:C",                          165, 100, "100nF",
            "Capacitor_SMD:C_0805_2012Metric"),
]

# Resolve some symbols not in /usr/share/kicad/symbols by mapping to their actual lib files.
# For Connector_Generic, Connector, Switch, Device, Regulator_Switching - they exist:
EXTRA_LIB_RESOLVE = {
    "Connector:USB_C_Receptacle_USB2.0": "Connector",
    "Connector:Screw_Terminal_01x02": "Connector",
    "Connector_Generic:Conn_01x04": "Connector_Generic",
    "Connector_Generic:Conn_01x02": "Connector_Generic",
    "Connector_Generic:Conn_01x03": "Connector_Generic",
    "Connector_Generic:Conn_02x08_Odd_Even": "Connector_Generic",
    "Regulator_Switching:MP1584EN": "Regulator_Switching",
    "Device:LED": "Device",
    "Device:R": "Device",
    "Device:C": "Device",
    "Switch:SW_Push": "Switch",
    "MCU_RaspberryPi:RP2040": "MCU_RaspberryPi",
    "Driver_Motor:DRV8871DDA": "Driver_Motor",
    "Driver_Haptic:DRV2605LDGS": "Driver_Haptic",
}

def gather_lib_symbols():
    out = []
    for ref, lib_id, *_ in COMPS:
        try:
            out.append(lib_sym_block(lib_id))
        except SystemExit as e:
            print(f"warn: {e}", file=sys.stderr)
    return "\n".join(out)

# Hierarchical labels per ref describing each component's role + key nets,
# placed near the component so the schematic reads as documentation.
LABELS = [
    # (x, y, text, justify)  - ref helpers below the symbol
    (150,  85, "RP2040 — host MCU (USB-CDC slave, asyncio target)"),
    ( 80,  78, "DRV8871 — H-bridge → SOLENOID (PWM on TAP)"),
    ( 80, 118, "DRV2605L — haptic driver → ERM/LRA (local I²C @ 0x5A)"),
    (220,  58, "USB-C — host link + RP2040 BOOTSEL flashing"),
    ( 50,  58, "12 V backbone tap"),
    (145, 162, "Stepper coil A/B headers → TMC2209"),
    ( 70, 165, "Solenoid / ERM JST-PH headers"),
    (220, 168, "Servo (signal / +5V / GND)"),
    (150,  38, "TMC2209 SilentStepStick socket (STEP/DIR/EN/UART)"),
    ( 50,  98, "MP1584 buck: +12 V → +5 V @ 1 A"),
    ( 50, 130, "BOOTSEL / RUN tactiles + STATUS LED"),
]

# Net labels at component pins — these are global_label entries placed at
# each pin location of the major ICs to document connectivity per the
# §3.4 pin-assignment table. (KiCad lets a label coexist with a free pin
# by being placed at the same coord; ERC will warn, which is fine — this
# is a placement-and-doc capture, not a wired schematic.)
NET_LABELS = [
    # placed at convenient grid positions next to U1 (RP2040 at (150,100))
    (140,  95, "STEP"),
    (140,  98, "DIR"),
    (140, 101, "nEN"),
    (140, 104, "TAP"),
    (140, 107, "SERVO"),
    (160,  95, "SDA"),
    (160,  98, "SCL"),
    (160, 101, "UART_TX"),
    (160, 104, "UART_RX"),
    (160, 107, "USB_DP"),
    (160, 110, "USB_DM"),
    # power rails
    (150, 115, "+3V3"),
    (150, 118, "GND"),
    ( 50, 105, "+12V"),
    ( 50, 115, "+5V"),
]

def sch():
    parts = []
    parts.append("(kicad_sch (version 20230121) (generator powder_doser_satgen)")
    parts.append(f'  (uuid "{SHEET_UUID}")')
    parts.append("  (paper \"A4\")")
    parts.append("  (title_block")
    parts.append("    (title \"Powder Doser — Satellite Rev A\")")
    parts.append("    (date \"2026-05-14\")")
    parts.append("    (rev \"A\")")
    parts.append("    (company \"vertical-cloud-lab/powder-doser\")")
    parts.append("    (comment 1 \"Per-module satellite for §3.3 USB-CDC topology, see design/electrical-software-brainstorming.md §3.4\")")
    parts.append("    (comment 2 \"Schematic capture: components placed; net routing left for follow-up PR.\")")
    parts.append("  )")

    parts.append("  (lib_symbols")
    parts.append(gather_lib_symbols())
    parts.append("  )")

    # Place each component as a (symbol ...) instance.
    for ref, lib_id, x, y, value, fp in COMPS:
        u = U()
        parts.append(textwrap.dedent(f"""\
          (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit 1)
            (in_bom yes) (on_board yes) (dnp no)
            (uuid "{u}")
            (property "Reference" "{ref}" (at {x} {y-8} 0)
              (effects (font (size 1.27 1.27))))
            (property "Value" "{value}" (at {x} {y+8} 0)
              (effects (font (size 1.27 1.27))))
            (property "Footprint" "{fp}" (at {x} {y} 0)
              (effects (font (size 1.27 1.27)) hide))
            (property "Datasheet" "~" (at {x} {y} 0)
              (effects (font (size 1.27 1.27)) hide))
            (instances
              (project "satellite"
                (path "/{SHEET_UUID}" (reference "{ref}") (unit 1))
              )
            )
          )"""))

    # Documentation labels (regular text)
    for x, y, txt in LABELS:
        u = U()
        parts.append(f'  (text "{txt}" (at {x} {y} 0) (effects (font (size 1.0 1.0))) (uuid "{u}"))')

    # Net global labels acting as a per-pin documentation legend
    for x, y, name in NET_LABELS:
        u = U()
        parts.append(f'  (global_label "{name}" (shape input) (at {x} {y} 0) (fields_autoplaced)\n'
                     f'    (effects (font (size 1.0 1.0)) (justify left))\n'
                     f'    (uuid "{u}"))')

    # Sheet instances
    parts.append("  (sheet_instances")
    parts.append('    (path "/" (page "1"))')
    parts.append("  )")
    parts.append(")")
    return "\n".join(parts)

# ----------------------------------------------------------------- pcb gen
# 50 mm x 50 mm board, origin at (100,100) in KiCad page coords for kicad-cli.
ORG_X, ORG_Y = 100.0, 100.0
W, H = 50.0, 50.0

# (ref, footprint, x_offset, y_offset, rotation, value, layer_top=True)
PCB_COMPS = [
    # TMC2209 socket dead center, 2x8 with 2.54mm pitch -> 17.78 x 2.54
    ("J8", "Connector_PinSocket_2.54mm:PinSocket_2x08_P2.54mm_Vertical",
     25.0, 25.0, 0, "TMC2209"),
    # RP2040 just south of the socket
    ("U1", "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
     25.0, 36.0, 0, "RP2040"),
    # MP1584 buck on the west edge near the 12V terminal
    ("U4", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     8.0, 22.0, 0, "MP1584"),
    # DRV8871 northwest
    ("U2", "Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm",
     12.0, 10.0, 0, "DRV8871"),
    # DRV2605L northeast
    ("U3", "Package_SO:MSOP-10-1EP_3x3mm_P0.5mm_EP1.68x1.88mm",
     38.0, 10.0, 0, "DRV2605L"),
    # USB-C on east edge
    ("J1", "Connector_USB:USB_C_Receptacle_GCT_USB4085",
     47.0, 25.0, 90, "USB-C"),
    # 12V terminal on west edge
    ("J2", "TerminalBlock:TerminalBlock_bornier-2_P5.08mm",
     3.5, 35.0, 0, "+12V"),
    # Stepper coil headers on south edge
    ("J3", "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
     17.0, 47.0, 0, "COIL_A"),
    ("J4", "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
     31.0, 47.0, 0, "COIL_B"),
    # Solenoid / ERM JST-PH on north edge
    ("J5", "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
     22.0, 3.0, 0, "SOLENOID"),
    ("J6", "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
     30.0, 3.0, 0, "ERM"),
    # Servo header on east edge
    ("J7", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
     43.0, 40.0, 0, "SERVO"),
    # BOOTSEL/RUN buttons + status LED on west edge
    ("SW1", "Button_Switch_SMD:SW_SPST_SKQG_WithoutStem",
     6.0, 42.0, 0, "BOOTSEL"),
    ("SW2", "Button_Switch_SMD:SW_SPST_SKQG_WithoutStem",
     6.0, 47.0, 0, "RUN"),
    ("D1",  "LED_SMD:LED_0805_2012Metric", 11.0, 42.0, 0, "STATUS"),
    ("R1",  "Resistor_SMD:R_0805_2012Metric", 11.0, 45.0, 0, "1k"),
    # USB-C CC pulldowns
    ("R2",  "Resistor_SMD:R_0805_2012Metric", 43.0, 22.0, 0, "5.1k"),
    ("R3",  "Resistor_SMD:R_0805_2012Metric", 43.0, 26.0, 0, "5.1k"),
    # Decoupling caps
    ("C1",  "Capacitor_SMD:CP_Elec_6.3x7.7",  17.0, 18.0, 0, "100uF"),
    ("C2",  "Capacitor_SMD:C_0805_2012Metric",30.0, 35.0, 0, "100nF"),
]

# 4 mounting holes at (3,3),(47,3),(3,47),(47,47)  — 44 mm pattern
HOLES = [(3,3),(47,3),(3,47),(47,47)]

def fp_block(fp_id: str) -> str:
    """Read a footprint file from the system library."""
    lib, ent = fp_id.split(":")
    p = pathlib.Path(f"/usr/share/kicad/footprints/{lib}.pretty/{ent}.kicad_mod")
    return p.read_text()

def reflow_fp(fp_text: str, ref: str, value: str, x: float, y: float, rot: int, fp_id: str) -> str:
    """Convert a (footprint Name ...) module-file body into a board-level
    (footprint "lib:Name" ...) entry placed at (x, y, rot) on F.Cu, with
    our reference and value text rewritten in place. Tolerant of both
    quoted ("Name") and unquoted (Name) module-name tokens."""
    import re
    body = fp_text.strip()
    # Replace the opening token with our placed header. Keep everything
    # else (descr/tags/attrs/fp_text/fp_line/pad/...) verbatim — KiCad
    # tolerates the duplicate (layer "F.Cu") that some module files have.
    body = re.sub(
        r'^\(footprint\s+("[^"]+"|\S+)',
        f'(footprint "{fp_id}" (layer "F.Cu") '
        f'(tstamp {U()}) (at {x} {y} {rot})',
        body, count=1)
    # Drop module-only header keys that aren't valid in board context.
    body = re.sub(r'\(version\s+\d+\)\s*', '', body)
    body = re.sub(r'\(generator\s+[^\)]+\)\s*', '', body)
    body = re.sub(r'\(tedit\s+[0-9A-Fa-f]+\)\s*', '', body)
    # Rewrite the reference designator (modules ship with "REF**", sometimes unquoted).
    body = re.sub(
        r'\(fp_text\s+reference\s+("[^"]*"|\S+)',
        f'(fp_text reference "{ref}"',
        body, count=1)
    # Rewrite the value text.
    body = re.sub(
        r'\(fp_text\s+value\s+("[^"]*"|\S+)',
        f'(fp_text value "{value}"',
        body, count=1)
    return body

def hole_block(x, y, ref):
    fp_id = "MountingHole:MountingHole_3.2mm_M3"
    txt = fp_block(fp_id)
    return reflow_fp(txt, ref, "M3", x, y, 0, fp_id)

def edge_cuts():
    # 50x50 rectangle origin at (0,0) in board-local (KiCad uses page coords —
    # we'll emit board-local since most viewers interpret raw geometry).
    L = []
    pts = [(0,0,W,0),(W,0,W,H),(W,H,0,H),(0,H,0,0)]
    for x1,y1,x2,y2 in pts:
        L.append(f'(gr_line (start {x1} {y1}) (end {x2} {y2}) (layer "Edge.Cuts") (width 0.1) (tstamp {U()}))')
    return "\n  ".join(L)

def silk_text():
    items = [
        (W/2,  -2, "Powder Doser Satellite Rev A"),
        (W/2,   H+2, "vertical-cloud-lab/powder-doser  §3.4"),
        (W/2,  20, "TMC2209"),
        (W/2,  31, "RP2040"),
        ( 9.0, 5.0, "BUCK"),
        (12.0,15.0, "DRV8871"),
        (38.0,15.0, "DRV2605L"),
        (47.0,30.0, "USB-C"),
        ( 5.0,32.0, "+12V"),
        (17.0,44.0, "COIL_A"),
        (31.0,44.0, "COIL_B"),
        (43.0,37.0, "SERVO"),
        (22.0, 6.0, "SOLENOID"),
        (30.0, 6.0, "ERM/LRA"),
    ]
    out = []
    for x,y,t in items:
        out.append(f'(gr_text "{t}" (at {x} {y} 0) (layer "F.SilkS") (tstamp {U()}) '
                   f'(effects (font (size 1 1) (thickness 0.15))))')
    return "\n  ".join(out)

def pcb():
    parts = []
    parts.append("(kicad_pcb (version 20221018) (generator powder_doser_satgen)")
    parts.append("  (general (thickness 1.6))")
    parts.append("  (paper \"A4\")")
    parts.append("  (title_block")
    parts.append("    (title \"Powder Doser — Satellite Rev A — Placement Outline\")")
    parts.append("    (date \"2026-05-14\")")
    parts.append("    (rev \"A\")")
    parts.append("    (company \"vertical-cloud-lab/powder-doser\")")
    parts.append("    (comment 1 \"§3.4 board outline + footprint placement; routing is follow-up work.\")")
    parts.append("  )")
    parts.append("  (layers")
    parts.append('    (0 "F.Cu" signal)')
    parts.append('    (31 "B.Cu" signal)')
    parts.append('    (32 "B.Adhes" user "B.Adhesive")')
    parts.append('    (33 "F.Adhes" user "F.Adhesive")')
    parts.append('    (34 "B.Paste" user)')
    parts.append('    (35 "F.Paste" user)')
    parts.append('    (36 "B.SilkS" user "B.Silkscreen")')
    parts.append('    (37 "F.SilkS" user "F.Silkscreen")')
    parts.append('    (38 "B.Mask" user)')
    parts.append('    (39 "F.Mask" user)')
    parts.append('    (40 "Dwgs.User" user "User.Drawings")')
    parts.append('    (41 "Cmts.User" user "User.Comments")')
    parts.append('    (42 "Eco1.User" user "User.Eco1")')
    parts.append('    (43 "Eco2.User" user "User.Eco2")')
    parts.append('    (44 "Edge.Cuts" user)')
    parts.append('    (45 "Margin" user)')
    parts.append('    (46 "B.CrtYd" user "B.Courtyard")')
    parts.append('    (47 "F.CrtYd" user "F.Courtyard")')
    parts.append('    (48 "B.Fab" user)')
    parts.append('    (49 "F.Fab" user)')
    parts.append("  )")
    parts.append("  (setup")
    parts.append("    (pad_to_mask_clearance 0)")
    parts.append("  )")
    parts.append("  (net 0 \"\")")

    # Edge cuts + silk
    parts.append("  " + edge_cuts())
    parts.append("  " + silk_text())

    # Footprints
    for ref, fp_id, x, y, rot, value in PCB_COMPS:
        try:
            fp_text = fp_block(fp_id)
        except Exception as e:
            print(f"warn: footprint {fp_id} missing ({e})", file=sys.stderr)
            continue
        parts.append("  " + reflow_fp(fp_text, ref, value, x, y, rot, fp_id))

    # Mounting holes
    for i,(x,y) in enumerate(HOLES, start=1):
        try:
            parts.append("  " + hole_block(x, y, f"H{i}"))
        except Exception as e:
            print(f"warn: mounting hole missing ({e})", file=sys.stderr)

    parts.append(")")
    return "\n".join(parts)

# ------------------------------------------------------------------- write
(OUT / "satellite.kicad_pro").write_text(PRO.replace("__SHEETUUID__", SHEET_UUID))
(OUT / "satellite.kicad_sch").write_text(sch())
(OUT / "satellite.kicad_pcb").write_text(pcb())
print(f"wrote project to {OUT}")

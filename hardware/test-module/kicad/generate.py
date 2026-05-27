"""Generate the powder-doser test-module KiCad 7 project from scratch.

The test rig consolidates one full powder-doser channel
(auger stepper + vibration ERM + tap solenoid + dispensing-angle servo)
onto a single Raspberry Pi Pico W (RP2040) so the whole module can be
exercised over USB-serial (or, in a future revision, wirelessly) without
bringing up the production Pi Zero 2 W stack from PR #25.

Because none of the breakouts we use (Pi Pico W, DRV2605L, DRV8871,
DRV8825, Pololu shunt regulator, hobby servo, JF-0530B solenoid, NEMA-11
4-wire stepper) have KiCad symbols in the stock symbol libraries, we
author a project-local ``test_module.kicad_sym`` library here and place
those symbols on the sheet purely with global net labels — no wires.
KiCad treats matching global labels as electrically connected, which
makes the schematic both machine-generatable and human-readable.

Coordinate convention used in this file:
  * Symbol library internals (``_pin`` / ``_rectangle``) use KiCad's
    symbol-editor convention: Y is positive UP, so a pin "below" the
    origin has a negative local Y.
  * The schematic page uses the opposite convention (Y positive DOWN),
    so when KiCad places a symbol on the page it FLIPS the local Y.
    ``SYMBOL_PINS`` therefore stores label-side offsets in *page*
    coordinates (Y positive DOWN) — that is, with the sign flipped
    relative to the corresponding pin's ``(at ...)`` entry in the
    symbol library.  Skipping the flip is what produced the
    "labels float above the body" rendering that was flagged in PR
    review.

After writing the project files the script invokes ``kicad-cli`` to
render SVG / PDF / PNG previews next to the source.

Run:  python3 generate.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

HERE = Path(__file__).resolve().parent
PROJECT = "test_module"

# ---------------------------------------------------------------------------
# Symbol library (KiCad 7 S-expression).
#
# Every breakout is rendered as a labelled rectangle with named pins on
# the left and right.  The chip-style attribute keeps reference / value
# fields legible at 1:1.
# ---------------------------------------------------------------------------

# pin definition helper -- KiCad pin orientations: 0=right, 90=up, 180=left, 270=down
def _pin(name: str, num: str, x: float, y: float, orient: int,
         length: float = 2.54, etype: str = "passive") -> str:
    return dedent(f"""\
        (pin {etype} line (at {x} {y} {orient}) (length {length})
          (name "{name}" (effects (font (size 1.27 1.27))))
          (number "{num}" (effects (font (size 1.27 1.27))))
        )""")


def _rectangle(x1: float, y1: float, x2: float, y2: float) -> str:
    return dedent(f"""\
        (rectangle (start {x1} {y1}) (end {x2} {y2})
          (stroke (width 0.254) (type default)) (fill (type background)))""")


def _props(ref: str, ref_x: float, ref_y: float,
           value: str, val_x: float, val_y: float,
           footprint: str = "") -> str:
    return dedent(f"""\
        (property "Reference" "{ref}" (id 0) (at {ref_x} {ref_y} 0)
          (effects (font (size 1.27 1.27))))
        (property "Value" "{value}" (id 1) (at {val_x} {val_y} 0)
          (effects (font (size 1.27 1.27))))
        (property "Footprint" "{footprint}" (id 2) (at 0 0 0)
          (effects (font (size 1.27 1.27)) hide))
        (property "Datasheet" "" (id 3) (at 0 0 0)
          (effects (font (size 1.27 1.27)) hide))""")


def build_symbol_lib() -> str:
    """Compose the project-local symbol library."""

    symbols = []

    # ------------------------------------------------------------------
    # Raspberry Pi Pico W (RP2040 + CYW43439 wireless).  Same 2x20
    # castellated header / GPIO pinout as the Pi Pico for pins 1..20
    # (the GPIOs we use here); the only differences are on the right
    # side -- the Pico W reuses GP23/24/25/29 for the wireless module's
    # SPI, so those four GPIOs are NOT general-purpose on the Pico W.
    # We don't use any of GP23..GP29 in this design, so the rig is
    # firmware-compatible with both the Pico and the Pico W; we draw
    # the symbol as the Pico W (with VBUS/VSYS/3V3 etc. on the right)
    # so the silkscreen matches the production part.
    # ------------------------------------------------------------------
    pico_left = [
        ("GP0", "1"),  ("GP1", "2"),   ("GND", "3"),   ("GP2", "4"),   ("GP3", "5"),
        ("GP4", "6"),  ("GP5", "7"),   ("GND", "8"),   ("GP6", "9"),   ("GP7", "10"),
        ("GP8", "11"), ("GP9", "12"),  ("GND", "13"),  ("GP10", "14"), ("GP11", "15"),
        ("GP12", "16"),("GP13", "17"), ("GND", "18"),  ("GP14", "19"), ("GP15", "20"),
    ]
    pico_right = [
        ("VBUS", "40"),    ("VSYS", "39"),  ("GND", "38"),  ("3V3_EN", "37"), ("3V3", "36"),
        ("ADC_VREF","35"), ("GP28","34"),   ("GND","33"),   ("GP27","32"),    ("GP26","31"),
        ("RUN","30"),      ("GP22","29"),   ("GND","28"),   ("GP21","27"),    ("GP20","26"),
        ("GP19","25"),     ("GP18","24"),   ("GND","23"),   ("GP17","22"),    ("GP16","21"),
    ]

    row_pitch = 2.54
    body_w = 22.86  # 9 grid units
    body_top = 0
    body_bot = body_top - row_pitch * (len(pico_left) + 1)
    pins = []
    for i, (name, num) in enumerate(pico_left):
        y = body_top - row_pitch * (i + 1)
        pins.append(_pin(name, num, -body_w / 2 - 2.54, y, 0, etype="bidirectional"))
    for i, (name, num) in enumerate(pico_right):
        y = body_top - row_pitch * (i + 1)
        etype = "power_in" if name in ("VBUS", "VSYS", "3V3", "GND", "ADC_VREF") else "bidirectional"
        pins.append(_pin(name, num, body_w / 2 + 2.54, y, 180, etype=etype))
    pico_body = _rectangle(-body_w / 2, body_top, body_w / 2, body_bot)
    symbols.append(dedent(f"""\
        (symbol "Pi_Pico_W" (in_bom yes) (on_board yes)
          {_props("U", -body_w / 2, body_top + 2.54, "Pi_Pico_W", -body_w / 2, body_top + 0.8)}
          (symbol "Pi_Pico_W_0_1"
            {pico_body}
          )
          (symbol "Pi_Pico_W_1_1"
            {chr(10).join(pins)}
          )
        )"""))

    # ------------------------------------------------------------------
    # DRV2605L haptic driver breakout (Adafruit #2305).
    # Left: I2C + power.  Right: motor outputs.
    # ------------------------------------------------------------------
    drv2605_left = [("VIN", "1", "power_in"), ("GND", "2", "power_in"),
                    ("SDA", "3", "bidirectional"), ("SCL", "4", "bidirectional"),
                    ("IN_TRIG", "5", "input"), ("EN", "6", "input")]
    drv2605_right = [("OUT+", "7", "passive"), ("OUT-", "8", "passive")]
    w = 17.78
    top = 0
    bot = top - row_pitch * (max(len(drv2605_left), len(drv2605_right)) + 1)
    pins = []
    for i, (n, num, et) in enumerate(drv2605_left):
        pins.append(_pin(n, num, -w / 2 - 2.54, top - row_pitch * (i + 1), 0, etype=et))
    for i, (n, num, et) in enumerate(drv2605_right):
        pins.append(_pin(n, num, w / 2 + 2.54, top - row_pitch * (i + 1), 180, etype=et))
    body = _rectangle(-w / 2, top, w / 2, bot)
    symbols.append(dedent(f"""\
        (symbol "DRV2605L_Breakout" (in_bom yes) (on_board yes)
          {_props("U", -w / 2, top + 2.54, "DRV2605L_Breakout", -w / 2, top + 0.8)}
          (symbol "DRV2605L_Breakout_0_1" {body})
          (symbol "DRV2605L_Breakout_1_1"
            {chr(10).join(pins)}
          )
        )"""))

    # ------------------------------------------------------------------
    # DRV8871 brushed-DC motor driver breakout (Adafruit #3190).
    # ------------------------------------------------------------------
    drv8871_left = [("VM", "1", "power_in"), ("GND", "2", "power_in"),
                    ("IN1", "3", "input"), ("IN2", "4", "input")]
    drv8871_right = [("OUT1", "5", "passive"), ("OUT2", "6", "passive")]
    w = 17.78
    top = 0
    bot = top - row_pitch * (max(len(drv8871_left), len(drv8871_right)) + 1)
    pins = []
    for i, (n, num, et) in enumerate(drv8871_left):
        pins.append(_pin(n, num, -w / 2 - 2.54, top - row_pitch * (i + 1), 0, etype=et))
    for i, (n, num, et) in enumerate(drv8871_right):
        pins.append(_pin(n, num, w / 2 + 2.54, top - row_pitch * (i + 1), 180, etype=et))
    body = _rectangle(-w / 2, top, w / 2, bot)
    symbols.append(dedent(f"""\
        (symbol "DRV8871_Breakout" (in_bom yes) (on_board yes)
          {_props("U", -w / 2, top + 2.54, "DRV8871_Breakout", -w / 2, top + 0.8)}
          (symbol "DRV8871_Breakout_0_1" {body})
          (symbol "DRV8871_Breakout_1_1"
            {chr(10).join(pins)}
          )
        )"""))

    # ------------------------------------------------------------------
    # DRV8825 stepper driver carrier (Pololu #2133): 16 pins total,
    # 8 per side, matching the physical 2x8 0.1" header on the carrier.
    # Left (logic): nEN, M0, M1, M2, nRST, nSLP, STEP, DIR.
    # Right (motor): VMOT, GND, B2, B1, A1, A2, nFAULT, GND.
    # There is no separate VDD pin — the carrier's logic supply is
    # generated internally from VMOT by the DRV8825's 3.3 V LDO, and
    # the logic inputs are 3.3 V / 5 V tolerant directly (no level
    # shifter required).  See Pololu #2133 product page / schematic.
    # ------------------------------------------------------------------
    drv8825_left = [("nEN", "1", "input"),  ("M0", "2", "input"),
                    ("M1", "3", "input"),   ("M2", "4", "input"),
                    ("nRST", "5", "input"), ("nSLP", "6", "input"),
                    ("STEP", "7", "input"), ("DIR", "8", "input")]
    drv8825_right = [("VMOT", "9", "power_in"),  ("GND_M", "10", "power_in"),
                     ("B2", "11", "passive"),    ("B1", "12", "passive"),
                     ("A1", "13", "passive"),    ("A2", "14", "passive"),
                     ("nFAULT", "15", "output"), ("GND_L", "16", "power_in")]
    w = 17.78
    top = 0
    bot = top - row_pitch * (max(len(drv8825_left), len(drv8825_right)) + 1)
    pins = []
    for i, (n, num, et) in enumerate(drv8825_left):
        pins.append(_pin(n, num, -w / 2 - 2.54, top - row_pitch * (i + 1), 0, etype=et))
    for i, (n, num, et) in enumerate(drv8825_right):
        pins.append(_pin(n, num, w / 2 + 2.54, top - row_pitch * (i + 1), 180, etype=et))
    body = _rectangle(-w / 2, top, w / 2, bot)
    symbols.append(dedent(f"""\
        (symbol "DRV8825_Carrier" (in_bom yes) (on_board yes)
          {_props("U", -w / 2, top + 2.54, "DRV8825_Carrier", -w / 2, top + 0.8)}
          (symbol "DRV8825_Carrier_0_1" {body})
          (symbol "DRV8825_Carrier_1_1"
            {chr(10).join(pins)}
          )
        )"""))

    # ------------------------------------------------------------------
    # Pololu D24V22F5 5 V / 2.5 A buck regulator (item 15).
    # ------------------------------------------------------------------
    buck_left = [("VIN", "1", "power_in"), ("GND_IN", "2", "power_in"),
                 ("SHDN", "3", "input")]
    buck_right = [("VOUT", "4", "power_out"), ("GND_OUT", "5", "power_in")]
    w = 15.24
    top = 0
    bot = top - row_pitch * (max(len(buck_left), len(buck_right)) + 1)
    pins = []
    for i, (n, num, et) in enumerate(buck_left):
        pins.append(_pin(n, num, -w / 2 - 2.54, top - row_pitch * (i + 1), 0, etype=et))
    for i, (n, num, et) in enumerate(buck_right):
        pins.append(_pin(n, num, w / 2 + 2.54, top - row_pitch * (i + 1), 180, etype=et))
    body = _rectangle(-w / 2, top, w / 2, bot)
    symbols.append(dedent(f"""\
        (symbol "D24V22F5_Buck" (in_bom yes) (on_board yes)
          {_props("U", -w / 2, top + 2.54, "D24V22F5_Buck", -w / 2, top + 0.8)}
          (symbol "D24V22F5_Buck_0_1" {body})
          (symbol "D24V22F5_Buck_1_1"
            {chr(10).join(pins)}
          )
        )"""))

    # ------------------------------------------------------------------
    # Generic 2-pin load (ERM motor, solenoid, electrolytic cap, shunt
    # regulator).  Each lays out the same way; the value label
    # differentiates them in the BOM.
    # ------------------------------------------------------------------
    for sym_name, value_label, ref_prefix in (
            ("ERM_Motor", "ERM 10mm coin", "M"),
            ("Solenoid", "JF-0530B 5V", "SOL"),
            ("Cap_Polar", "100u/25V", "C"),
            ("Shunt_Regulator", "Pololu #3776 33V 9W shunt", "SR"),
    ):
        pins = [
            _pin("+", "1", -5.08, 0, 0),
            _pin("-", "2", 5.08, 0, 180),
        ]
        body = _rectangle(-2.54, 1.27, 2.54, -1.27)
        symbols.append(dedent(f"""\
            (symbol "{sym_name}" (in_bom yes) (on_board yes)
              {_props(ref_prefix, -2.54, 3.81, value_label, -2.54, 2.54)}
              (symbol "{sym_name}_0_1" {body})
              (symbol "{sym_name}_1_1"
                {chr(10).join(pins)}
              )
            )"""))

    # ------------------------------------------------------------------
    # 4-wire bipolar stepper (NEMA-11 11HS18-0674S).
    # ------------------------------------------------------------------
    pins = [
        _pin("A1", "1", -7.62, 0, 0),
        _pin("A2", "2", -7.62, -2.54, 0),
        _pin("B1", "3", 7.62, 0, 180),
        _pin("B2", "4", 7.62, -2.54, 180),
    ]
    body = _rectangle(-5.08, 1.27, 5.08, -3.81)
    symbols.append(dedent(f"""\
        (symbol "Stepper_4wire" (in_bom yes) (on_board yes)
          {_props("M", -5.08, 3.81, "NEMA11 11HS18", -5.08, 2.54)}
          (symbol "Stepper_4wire_0_1" {body})
          (symbol "Stepper_4wire_1_1"
            {chr(10).join(pins)}
          )
        )"""))

    # ------------------------------------------------------------------
    # Hobby servo (3-pin: +5V, GND, signal).
    # ------------------------------------------------------------------
    pins = [
        _pin("+5V", "1", -7.62, 2.54, 0, etype="power_in"),
        _pin("GND", "2", -7.62, 0, 0, etype="power_in"),
        _pin("SIG", "3", -7.62, -2.54, 0, etype="input"),
    ]
    body = _rectangle(-5.08, 3.81, 5.08, -3.81)
    symbols.append(dedent(f"""\
        (symbol "Servo_3pin" (in_bom yes) (on_board yes)
          {_props("M", -5.08, 5.08, "HD-1810MG", -5.08, 4.32)}
          (symbol "Servo_3pin_0_1" {body})
          (symbol "Servo_3pin_1_1"
            {chr(10).join(pins)}
          )
        )"""))

    # ------------------------------------------------------------------
    # 2-pin power input connector (barrel jack from 12 V brick).
    # ------------------------------------------------------------------
    pins = [
        _pin("+12V", "1", -5.08, 1.27, 0, etype="power_in"),
        _pin("GND", "2", -5.08, -1.27, 0, etype="power_in"),
    ]
    body = _rectangle(-2.54, 2.54, 2.54, -2.54)
    symbols.append(dedent(f"""\
        (symbol "Barrel_Jack_12V" (in_bom yes) (on_board yes)
          {_props("J", -2.54, 5.08, "Barrel 12V/5A", -2.54, 3.81)}
          (symbol "Barrel_Jack_12V_0_1" {body})
          (symbol "Barrel_Jack_12V_1_1"
            {chr(10).join(pins)}
          )
        )"""))

    header = '(kicad_symbol_lib (version 20211014) (generator powder_doser_test_module)\n'
    return header + "\n".join(symbols) + "\n)\n"


# ---------------------------------------------------------------------------
# Schematic.
#
# Layout is a simple grid: power column on the left, MCU in the centre,
# the four driver breakouts on the right with their respective actuators
# further to the right.  Connectivity is expressed entirely via global
# labels on the pins (no drawn wires) — KiCad treats matching globals
# as electrically connected.
# ---------------------------------------------------------------------------

# (component_symbol, instance_ref, x, y, [(pin_name, net_label), ...])
#
# Layout is roughly:
#   x≈30  power column
#   x≈100 MCU
#   x≈210 driver breakouts (Pico stubs need ~13 mm clearance on each side)
#   x≈275 actuators
PLACEMENTS = [
    # ---- Power column (left) ----
    ("Barrel_Jack_12V", "J1",  30,  40, [("+12V", "+12V"), ("GND", "GND")]),
    ("D24V22F5_Buck",  "U1",   30,  70, [("VIN", "+12V"),  ("GND_IN", "GND"),
                                          ("SHDN", "+12V"),  # tie SHDN high -> enabled
                                          ("VOUT", "+5V"),  ("GND_OUT", "GND")]),
    ("Cap_Polar",     "C1",   30,  100, [("+", "+12V"), ("-", "GND")]),
    ("Cap_Polar",     "C2",   30,  120, [("+", "+5V"),  ("-", "GND")]),

    # ---- MCU (centre) ----
    # The Pico W is powered from the buck via VSYS so it can survive USB
    # disconnect; VBUS is left floating.  3V3 logic is sourced from the
    # Pico W's on-board LDO and feeds the DRV8825 / DRV2605L logic rails.
    ("Pi_Pico_W", "U2", 110, 50,
        [("VSYS", "+5V"), ("GND", "GND"), ("3V3", "+3V3"),
         # I2C0 for DRV2605L
         ("GP0", "I2C_SDA"), ("GP1", "I2C_SCL"),
         # DRV8825 stepper control
         ("GP2", "STP_STEP"), ("GP3", "STP_DIR"), ("GP4", "STP_nEN"),
         ("GP5", "STP_M0"),   ("GP6", "STP_M1"),  ("GP7", "STP_M2"),
         # DRV8871 (solenoid)
         ("GP10", "SOL_IN1"), ("GP11", "SOL_IN2"),
         # Servo PWM (dispensing angle)
         ("GP15", "SERVO_SIG"),
         # DRV2605L enable + trigger (optional; we drive in I2C mode but
         # expose EN so the firmware can hard-mute the haptic driver).
         ("GP14", "HAPT_EN")]),

    # ---- Vibration channel (right side, top) ----
    ("DRV2605L_Breakout", "U3", 210, 40,
        [("VIN", "+3V3"), ("GND", "GND"),
         ("SDA", "I2C_SDA"), ("SCL", "I2C_SCL"),
         ("EN", "HAPT_EN"), ("IN_TRIG", "HAPT_EN"),
         ("OUT+", "VIB_A"), ("OUT-", "VIB_B")]),
    ("ERM_Motor", "M1", 275, 50, [("+", "VIB_A"), ("-", "VIB_B")]),

    # ---- Solenoid / tap channel ----
    ("DRV8871_Breakout", "U4", 210, 90,
        [("VM", "+12V"), ("GND", "GND"),
         ("IN1", "SOL_IN1"), ("IN2", "SOL_IN2"),
         ("OUT1", "SOL_A"), ("OUT2", "SOL_B")]),
    ("Solenoid", "SOL1", 275, 100, [("+", "SOL_A"), ("-", "SOL_B")]),

    # ---- Stepper / auger channel ----
    ("DRV8825_Carrier", "U5", 210, 140,
        [("STEP", "STP_STEP"), ("DIR", "STP_DIR"), ("nEN", "STP_nEN"),
         ("nSLP", "+3V3"), ("nRST", "+3V3"),
         ("M0", "STP_M0"), ("M1", "STP_M1"), ("M2", "STP_M2"),
         ("nFAULT", "STP_FAULT"),
         ("VMOT", "+12V"), ("GND_M", "GND"), ("GND_L", "GND"),
         ("A1", "STP_A1"), ("A2", "STP_A2"),
         ("B1", "STP_B1"), ("B2", "STP_B2")]),
    ("Cap_Polar", "C3", 210, 195, [("+", "+12V"), ("-", "GND")]),
    # Pololu #3776 33 V / 9 W shunt regulator across +12V / GND, sitting
    # right next to the DRV8825's VMOT screw terminals.  Clamps back-EMF
    # transients during deceleration / back-driving so the wall-wart-
    # powered 12 V rail can't push the DRV8825 past its 45 V abs max.
    # See PR #25 BOM item 18 for rationale.
    ("Shunt_Regulator", "SR1", 175, 195, [("+", "+12V"), ("-", "GND")]),
    ("Stepper_4wire", "M2", 285, 145,
        [("A1", "STP_A1"), ("A2", "STP_A2"),
         ("B1", "STP_B1"), ("B2", "STP_B2")]),

    # ---- Dispensing-angle servo channel ----
    ("Servo_3pin", "M3", 210, 215,
        [("+5V", "+5V"), ("GND", "GND"), ("SIG", "SERVO_SIG")]),
]


def _label(net: str, x: float, y: float, rot: int = 0) -> str:
    return dedent(f"""\
        (global_label "{net}" (shape input) (at {x} {y} {rot}) (fields_autoplaced)
          (effects (font (size 1.27 1.27)) (justify left))
          (uuid "00000000-0000-0000-0000-{abs(hash((net, x, y))) % 10**12:012d}")
        )""")


def _wire(x1: float, y1: float, x2: float, y2: float) -> str:
    return dedent(f"""\
        (wire (pts (xy {x1} {y1}) (xy {x2} {y2}))
          (stroke (width 0) (type default)) (stroke (width 0) (type default))
          (uuid "00000000-0000-0000-0004-{abs(hash((x1, y1, x2, y2))) % 10**12:012d}")
        )""")


# Per-symbol stub length: pin tip -> label.  Pico needs a longer stub
# because each side has 20 closely-spaced pins; everything else fits at 5 mm.
STUB_LEN: dict[str, float] = {"Pi_Pico": 12.7}


def _symbol_instance(lib_id: str, ref: str, x: float, y: float, unit: int = 1) -> str:
    return dedent(f"""\
        (symbol (lib_id "test_module:{lib_id}") (at {x} {y} 0) (unit {unit})
          (in_bom yes) (on_board yes) (dnp no)
          (uuid "00000000-0000-0000-0001-{abs(hash((lib_id, ref, x, y))) % 10**12:012d}")
          (property "Reference" "{ref}" (id 0) (at {x - 12} {y - 5} 0)
            (effects (font (size 1.27 1.27)) (justify left)))
          (property "Value" "{lib_id}" (id 1) (at {x - 12} {y - 2.5} 0)
            (effects (font (size 1.27 1.27)) (justify left)))
          (property "Footprint" "" (id 2) (at {x} {y} 0)
            (effects (font (size 1.27 1.27)) hide))
          (property "Datasheet" "" (id 3) (at {x} {y} 0)
            (effects (font (size 1.27 1.27)) hide))
          (instances
            (project "{PROJECT}"
              (path "/00000000-0000-0000-0002-000000000001"
                (reference "{ref}") (unit 1)
              )
            )
          )
        )""")


# Geometry of the symbols we authored above — needed to place labels at
# the correct world coordinates relative to each instance's origin.
# Returns (x_offset, y_offset, label_rotation) for each (lib_id, pin_name).
#
# NB: The Y values here are in SCHEMATIC PAGE coordinates (Y positive
# DOWN), so they are the NEGATIVE of the Y in the corresponding
# ``(pin ... (at x y orient))`` entry in the symbol library (which
# uses the symbol-editor convention of Y positive UP).  When KiCad
# places the symbol on the sheet it flips Y, so the page-space tip of
# a pin defined at local (x, -7.62) ends up at world y = instance_y +
# 7.62.  Without this flip, labels render *above* the symbol body
# instead of next to the actual pins -- which is the rendering bug
# flagged in PR review.
SYMBOL_PINS: dict[str, dict[str, tuple[float, float, int]]] = {
    "Barrel_Jack_12V": {
        "+12V": (-7.62, -1.27, 180), "GND": (-7.62, 1.27, 180),
    },
    "D24V22F5_Buck": {
        "VIN":     (-10.16, 2.54, 180), "GND_IN":  (-10.16, 5.08, 180),
        "SHDN":    (-10.16, 7.62, 180),
        "VOUT":    (10.16,  2.54, 0),   "GND_OUT": (10.16,  5.08, 0),
    },
    "Cap_Polar": {
        "+": (-7.62, 0, 180), "-": (7.62, 0, 0),
    },
    "Shunt_Regulator": {
        "+": (-7.62, 0, 180), "-": (7.62, 0, 0),
    },
    "Pi_Pico_W": {
        # Left column GP0..GP15 + GNDs (we only need ones we actually wire)
        "GP0": (-13.97, 2.54, 180),   "GP1": (-13.97, 5.08, 180),
        "GP2": (-13.97, 10.16, 180),  "GP3": (-13.97, 12.7, 180),
        "GP4": (-13.97, 15.24, 180),  "GP5": (-13.97, 17.78, 180),
        "GP6": (-13.97, 22.86, 180),  "GP7": (-13.97, 25.4, 180),
        "GP10": (-13.97, 35.56, 180), "GP11": (-13.97, 38.1, 180),
        "GP14": (-13.97, 48.26, 180), "GP15": (-13.97, 50.8, 180),
        # Right column power
        "VSYS": (13.97, 5.08, 0),     "GND":  (13.97, 7.62, 0),
        "3V3":  (13.97, 12.7, 0),
    },
    "DRV2605L_Breakout": {
        "VIN":     (-11.43, 2.54, 180), "GND":     (-11.43, 5.08, 180),
        "SDA":     (-11.43, 7.62, 180), "SCL":     (-11.43, 10.16, 180),
        "IN_TRIG": (-11.43, 12.7, 180), "EN":      (-11.43, 15.24, 180),
        "OUT+":    (11.43,  2.54, 0),   "OUT-":    (11.43,  5.08, 0),
    },
    "DRV8871_Breakout": {
        "VM":   (-11.43, 2.54, 180), "GND":  (-11.43, 5.08, 180),
        "IN1":  (-11.43, 7.62, 180), "IN2":  (-11.43, 10.16, 180),
        "OUT1": (11.43,  2.54, 0),   "OUT2": (11.43,  5.08, 0),
    },
    "DRV8825_Carrier": {
        # Left side (logic), 8 pins, top → bottom matching the symbol
        # pin order (nEN, M0, M1, M2, nRST, nSLP, STEP, DIR):
        "nEN":    (-11.43, 2.54, 180), "M0":     (-11.43, 5.08, 180),
        "M1":     (-11.43, 7.62, 180), "M2":     (-11.43, 10.16, 180),
        "nRST":   (-11.43, 12.7, 180), "nSLP":   (-11.43, 15.24, 180),
        "STEP":   (-11.43, 17.78, 180),"DIR":    (-11.43, 20.32, 180),
        # Right side (motor), 8 pins, top → bottom (VMOT, GND, B2, B1,
        # A1, A2, nFAULT, GND).  No separate VDD pin on this carrier.
        "VMOT":   (11.43, 2.54, 0),    "GND_M":  (11.43, 5.08, 0),
        "B2":     (11.43, 7.62, 0),    "B1":     (11.43, 10.16, 0),
        "A1":     (11.43, 12.7, 0),    "A2":     (11.43, 15.24, 0),
        "nFAULT": (11.43, 17.78, 0),   "GND_L":  (11.43, 20.32, 0),
    },
    "Stepper_4wire": {
        "A1": (-10.16, 0, 180), "A2": (-10.16, 2.54, 180),
        "B1": (10.16,  0, 0),   "B2": (10.16,  2.54, 0),
    },
    "Servo_3pin": {
        "+5V": (-10.16, -2.54, 180), "GND": (-10.16, 0, 180),
        "SIG": (-10.16, 2.54, 180),
    },
    "ERM_Motor": {
        "+": (-7.62, 0, 180), "-": (7.62, 0, 0),
    },
    "Solenoid": {
        "+": (-7.62, 0, 180), "-": (7.62, 0, 0),
    },
}


def build_schematic() -> str:
    body_parts: list[str] = []
    for lib_id, ref, x, y, nets in PLACEMENTS:
        body_parts.append(_symbol_instance(lib_id, ref, x, y))
        pin_map = SYMBOL_PINS[lib_id]
        stub = STUB_LEN.get(lib_id, 5.08)
        for pin_name, net in nets:
            if pin_name not in pin_map:
                raise KeyError(
                    f"Symbol {lib_id!r} has no recorded pin {pin_name!r} — "
                    f"add it to SYMBOL_PINS."
                )
            dx, dy, rot = pin_map[pin_name]
            tip_x, tip_y = x + dx, y + dy
            # Extend the label further out from the symbol body so the
            # generated labels don't pile on top of adjacent pins.
            if rot == 180:
                lbl_x, lbl_y = tip_x - stub, tip_y
            elif rot == 0:
                lbl_x, lbl_y = tip_x + stub, tip_y
            elif rot == 90:
                lbl_x, lbl_y = tip_x, tip_y - stub
            else:  # 270
                lbl_x, lbl_y = tip_x, tip_y + stub
            body_parts.append(_wire(tip_x, tip_y, lbl_x, lbl_y))
            body_parts.append(_label(net, lbl_x, lbl_y, rot))

    title_block = dedent("""\
        (paper "A3")
        (title_block
          (title "Powder-doser test module — single-Pico bench rig")
          (date "2026-05-18")
          (rev "A")
          (company "Vertical Cloud Lab")
          (comment 1 "Exercises auger stepper + ERM vibration + tap solenoid + dispense-angle servo")
          (comment 2 "Resolves issue #50; parts from PR #25")
          (comment 3 "")
          (comment 4 "")
        )
    """)

    lib_symbols = build_symbol_lib_block()

    header = dedent(f"""\
        (kicad_sch (version 20230121) (generator powder_doser_test_module)
          (uuid "00000000-0000-0000-0003-000000000001")
        {title_block}
        {lib_symbols}
        """)

    footer = dedent("""\
          (sheet_instances
            (path "/" (page "1"))
          )
        )
    """)

    return header + "\n".join(body_parts) + "\n" + footer


def build_symbol_lib_block() -> str:
    """Embed the symbol library inside the schematic for self-contained rendering."""
    lib = build_symbol_lib()
    # Drop the outer (kicad_symbol_lib ...) wrapper and re-emit as (lib_symbols ...)
    # with each symbol renamed to test_module:NAME.
    inner = lib.split("\n", 1)[1].rsplit(")\n", 1)[0]
    inner = inner.replace('(symbol "', '(symbol "test_module:', 1)
    # The first replace is for the lib top; do per-line for top-level symbols.
    out = []
    depth = 0
    for line in lib.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("(symbol \"") and depth == 1:
            # top-level symbol declaration -- prefix with library name
            line = line.replace('(symbol "', '(symbol "test_module:', 1)
        depth += line.count("(") - line.count(")")
        out.append(line)
    # Drop wrapper first + last
    body_lines = out[1:-1]
    return "(lib_symbols\n" + "\n".join(body_lines) + "\n)"


PROJECT_JSON = dedent("""\
{
  "board": {},
  "boards": [],
  "cvpcb": {"equivalence_files": []},
  "erc": {"erc_exclusions": [], "meta": {"version": 0}},
  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
  "meta": {"filename": "test_module.kicad_pro", "version": 1},
  "net_settings": {"classes": [], "meta": {"version": 3}, "net_colors": null},
  "pcbnew": {"page_layout_descr_file": ""},
  "schematic": {
    "annotate_start_num": 0,
    "drawing": {"default_line_thickness": 6.0, "default_text_size": 50.0},
    "legacy_lib_dir": "",
    "legacy_lib_list": [],
    "meta": {"version": 1},
    "net_format_name": "Pcbnew",
    "ngspice": {"meta": {"version": 0}, "workbook_filename": ""},
    "page_layout_descr_file": "",
    "plot_directory": "",
    "spice_external_command": "spice \\"%I\\"",
    "subpart_first_id": 65,
    "subpart_id_separator": 0
  },
  "sheets": [["00000000-0000-0000-0003-000000000001", ""]],
  "text_variables": {}
}
""")

SYM_LIB_TABLE = dedent("""\
    (sym_lib_table
      (lib (name "test_module")(type "KiCad")(uri "${KIPRJMOD}/test_module.kicad_sym")(options "")(descr "Powder-doser test-module breakouts"))
    )
""")


def main() -> int:
    (HERE / f"{PROJECT}.kicad_sym").write_text(build_symbol_lib())
    (HERE / f"{PROJECT}.kicad_sch").write_text(build_schematic())
    (HERE / f"{PROJECT}.kicad_pro").write_text(PROJECT_JSON)
    (HERE / "sym-lib-table").write_text(SYM_LIB_TABLE)

    cli = shutil.which("kicad-cli")
    if cli is None:
        print("warning: kicad-cli not on PATH; skipping render", file=sys.stderr)
        return 0

    sch = HERE / f"{PROJECT}.kicad_sch"
    out_svg = HERE / f"{PROJECT}.svg"
    out_pdf = HERE / f"{PROJECT}.pdf"

    # Export SVG (the .png we ship is rasterised from this).
    subprocess.run(
        [cli, "sch", "export", "svg", "--no-background-color",
         "--exclude-drawing-sheet", "-o", str(HERE), str(sch)],
        check=True,
    )
    # KiCad writes <project>.svg with one file per page.
    subprocess.run(
        [cli, "sch", "export", "pdf", "--no-background-color", "-o",
         str(out_pdf), str(sch)],
        check=True,
    )
    # Rasterise SVG -> PNG via rsvg-convert if available.
    rsvg = shutil.which("rsvg-convert")
    if rsvg and out_svg.exists():
        subprocess.run([rsvg, "-w", "1800", "-o",
                        str(HERE / f"{PROJECT}.png"), str(out_svg)],
                       check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

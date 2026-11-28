#!/usr/bin/python3
"""Write solder_steps.json (hand-soldering order for the animation) from fc1.kicad_pcb.

Frame: origin at the board's lower-left corner, x right, y up, mm (y = 40 - KiCad y).
body_l is along the part's own x axis before rotation, body_w along its own y axis;
rot is counter-clockwise in degrees (KiCad's orientation). pads are [x, y, w, h]
(centre and size of each pad's bounding box in the board frame).
"""
import json
import os
import sys

import pcbnew
from pcbnew import ToMM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fc1_design as D  # noqa: E402

H = D.BOARD_H
# body sizes (l along local x, w along local y, h) in mm; approximate package outlines from the data sheets
BODY = {
    "R0805": (2.0, 1.25, 0.6), "C0805": (2.0, 1.25, 0.9), "R1206": (3.2, 1.6, 0.6), "C1206": (3.2, 1.6, 1.1),
    "C1206_100n": (3.2, 1.6, 1.6), "LED0805": (2.0, 1.25, 0.8), "SOT23": (1.3, 2.9, 1.1), "SOD123": (2.7, 1.6, 1.15),
    "SOIC8": (3.9, 4.9, 1.75), "MSOP10": (3.0, 3.0, 1.1), "JSTSH": (6.0, 4.25, 2.95),
    "HDR1x2": (2.54, 5.08, 8.5), "HDR1x6": (2.54, 15.24, 8.5), "COTO9002": (19.3, 5.08, 7.6),
    "BNC5539": (14.0, 14.0, 31.0), "SJ": (3.6, 1.5, 0.05),
}
COL = {"R": "#1c1c1c", "C": "#c9a36a", "C0G": "#b58b55", "IC": "#202020", "LEDG": "#7fd67f", "LEDY": "#ffd23f",
       "JST": "#f2f2f2", "HDR": "#151515", "RELAY": "#333333", "BNC": "#c8c8c8", "SOLDER": "#b9b9b9", "DIODE": "#262626"}

# (ref, caption, body key, colour)
STEPS = [
    ("U3", "U3 ADS1115 (MSOP-10): tack one corner, check pin 1, drag-solder", "MSOP10", COL["IC"]),
    ("U1", "U1 ADA4530-1 (SOIC-8): pin 1 dot to the arrow; no flux residue", "SOIC8", COL["IC"]),
    ("U2", "U2 REF3025 2.5 V reference (SOT-23)", "SOT23", COL["IC"]),
    ("Q1", "Q1 MMBT3904 relay driver (SOT-23)", "SOT23", COL["IC"]),
    ("Q2", "Q2 BSS138 SDA level shifter (SOT-23)", "SOT23", COL["IC"]),
    ("Q3", "Q3 BSS138 SCL level shifter (SOT-23)", "SOT23", COL["IC"]),
    ("D1", "D1 1N4148W flyback diode: cathode bar toward K1 pin 2 (+5 V)", "SOD123", COL["DIODE"]),
    ("R2", "R2 100R in series with the reed contacts", "R0805", COL["R"]),
    ("R3", "R3 1k OUT -> AIN0", "R0805", COL["R"]),
    ("R4", "R4 1k REF -> AIN1", "R0805", COL["R"]),
    ("R5", "R5 10R supply filter (+5V -> +5VA)", "R0805", COL["R"]),
    ("R6", "R6 10k SDA pull-up, 3.3 V side", "R0805", COL["R"]),
    ("R7", "R7 10k SCL pull-up, 3.3 V side", "R0805", COL["R"]),
    ("R8", "R8 10k SDA pull-up, 5 V side", "R0805", COL["R"]),
    ("R9", "R9 10k SCL pull-up, 5 V side", "R0805", COL["R"]),
    ("R10", "R10 100k ADDR pull-down (address 0x48)", "R0805", COL["R"]),
    ("R11", "R11 4k7 base resistor", "R0805", COL["R"]),
    ("R12", "R12 100k base pull-down", "R0805", COL["R"]),
    ("R13", "R13 1k5 reset LED resistor", "R0805", COL["R"]),
    ("R14", "R14 2k2 power LED resistor", "R0805", COL["R"]),
    ("C3", "C3 100nF U1 supply decoupling", "C0805", COL["C"]),
    ("C4", "C4 10uF +5VA bulk", "C0805", COL["C"]),
    ("C5", "C5 1uF U2 input", "C0805", COL["C"]),
    ("C6", "C6 1uF U2 output (REF)", "C0805", COL["C"]),
    ("C7", "C7 10nF C0G AIN0 filter", "C0805", COL["C0G"]),
    ("C8", "C8 10nF C0G AIN1 filter", "C0805", COL["C0G"]),
    ("C9", "C9 100nF U3 supply decoupling", "C0805", COL["C"]),
    ("C10", "C10 10uF +5V input bulk", "C0805", COL["C"]),
    ("C11", "C11 100nF 3V3 decoupling", "C0805", COL["C"]),
    ("D2", "D2 yellow RST LED: cathode (green mark) to the left pad", "LED0805", COL["LEDY"]),
    ("D3", "D3 green PWR LED: cathode (green mark) to the lower pad", "LED0805", COL["LEDG"]),
    ("C1", "C1 10nF C0G feedback cap (guarded node: clean afterwards)", "C1206", COL["C0G"]),
    ("C2", "C2 100nF C0G feedback cap, x10 range (guarded node)", "C1206_100n", COL["C0G"]),
    ("R15", "R15 0R links the CAN lug to GND", "R1206", COL["R"]),
    ("JP5", "JP5: bridge pads 1-2 with solder (BNC shell to GND)", "SJ", COL["SOLDER"]),
    ("J2", "J2 STEMMA QT socket: tabs first, then the four pins", "JSTSH", COL["JST"]),
    ("J3", "J3 STEMMA QT socket (pass-through)", "JSTSH", COL["JST"]),
    ("JP1", "JP1 2-pin range header; shunt on = 110 nF (x10 range)", "HDR1x2", COL["HDR"]),
    ("J4", "J4 6-pin Pico header: GND 5V 3V3 SDA SCL RST", "HDR1x6", COL["HDR"]),
    ("K1", "K1 Coto 9002 reed relay: dot = pin 1 at the guarded end", "COTO9002", COL["RELAY"]),
    ("J1", "J1 BNC last; then wash the guard area with IPA and dry", "BNC5539", COL["BNC"]),
]

board = pcbnew.LoadBoard(os.path.join(HERE, "fc1.kicad_pcb"))
steps = []
for n, (ref, cap, body, colour) in enumerate(STEPS, 1):
    fp = board.FindFootprintByReference(ref)
    assert fp is not None, ref
    assert len(cap) <= 70, (ref, len(cap))
    pos = fp.GetPosition()
    # body centre = centre of the F.Fab outline (falls back to the courtyard); differs from the
    # footprint origin for headers, the relay and the JST sockets
    fab = [g.GetBoundingBox() for g in fp.GraphicalItems()
           if g.GetLayer() == pcbnew.F_Fab and g.GetClass() != "PCB_TEXT"]
    if fab:
        x0 = min(ToMM(b.GetLeft()) for b in fab); x1 = max(ToMM(b.GetRight()) for b in fab)
        y0 = min(ToMM(b.GetTop()) for b in fab); y1 = max(ToMM(b.GetBottom()) for b in fab)
    else:
        cb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        x0, x1, y0, y1 = ToMM(cb.GetLeft()), ToMM(cb.GetRight()), ToMM(cb.GetTop()), ToMM(cb.GetBottom())
    bx, by = (x0 + x1) / 2, (y0 + y1) / 2
    pads = []
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            continue
        bb = p.GetBoundingBox()
        cx = (ToMM(bb.GetLeft()) + ToMM(bb.GetRight())) / 2
        cy = (ToMM(bb.GetTop()) + ToMM(bb.GetBottom())) / 2
        pads.append([round(cx, 3), round(H - cy, 3), round(ToMM(bb.GetWidth()), 3), round(ToMM(bb.GetHeight()), 3)])
    l, w, h = BODY[body]
    steps.append({"step": n, "ref": ref, "caption": cap, "side": "top",
                  "x": round(bx, 3), "y": round(H - by, 3),
                  "fp_origin": [round(ToMM(pos.x), 3), round(H - ToMM(pos.y), 3)],
                  "rot": round(fp.GetOrientationDegrees(), 1),
                  "body_w": w, "body_l": l, "body_h": h, "pads": pads, "colour": colour})

placed = {s["ref"] for s in steps}
skipped = sorted(fp.GetReference() for fp in board.GetFootprints() if fp.GetReference() not in placed)
doc = {
    "board": "FC-1 Faraday-cup charge amplifier v%s (%s)" % (D.VERSION, D.DATE),
    "units": "mm",
    "frame": "origin at the board's lower-left corner, x right, y up; rot counter-clockwise in degrees",
    "xy": "x, y = centre of the part body (F.Fab outline); fp_origin = KiCad footprint origin (pin 1 for headers and K1)",
    "body_axes": "body_l along the part's own x axis before rotation, body_w along its own y axis",
    "board_outline": [[0, 0], [D.BOARD_W, 0], [D.BOARD_W, D.BOARD_H], [0, D.BOARD_H], [0, 0]],
    "board_thickness": 1.6,
    "holes": [[round(ToMM(fp.GetPosition().x), 3), round(H - ToMM(fp.GetPosition().y), 3),
               round(ToMM(max(p.GetDrillSize().x for p in fp.Pads())), 2), fp.GetReference()]
              for fp in board.GetFootprints() if fp.GetReference().startswith("H")],
    "guard_area": [[x, round(H - y, 3)] for x, y in D.GUARD_POLY],
    "not_soldered": {"R1": "DNP (optional 10 G bleed resistor)", "H1-H4": "M3 mounting holes",
                     "H5": "M3 lug for the outer can", "H6": "2.2 mm hole for an optional PTFE turret",
                     "TP1": "test pad (OUT)", "JP2-JP4": "address solder jumpers, left open (0x48)"},
    "steps": steps,
}
assert set(skipped) <= {"R1", "H1", "H2", "H3", "H4", "H5", "H6", "TP1", "JP2", "JP3", "JP4"}, skipped
with open(os.path.join(HERE, "solder_steps.json"), "w") as f:
    json.dump(doc, f, indent=1)
print("wrote solder_steps.json with", len(steps), "steps; not soldered:", skipped)

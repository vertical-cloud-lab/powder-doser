"""Write BOM.md, bom.csv and ASSEMBLY.md from bom.ITEMS and layout.STEPS.

    python docs.py

ASSEMBLY.md pairs each step's render (renders/steps/step_NN.png) with the
BoM lines it consumes and the instructions in STEP_TEXT, so a change to the
CAD or the BoM shows up in the instructions on the next run.
"""
from __future__ import annotations

from pathlib import Path

import bom
import layout as L
from params import CHAIN_Z, HINGE_Y, HINGE_Z, TENSION_TRAVEL

HERE = Path(__file__).resolve().parent

STEP_TEXT = {
    1: """Cut the 2020 to length: 2 x 1050 mm (long rails), 5 x 690 mm (cross members), 4 x 230 mm (legs).
Lay the long rails parallel, 710 mm apart centre to centre. Put the cross members between them at
10, 261.6, 421.6, 805 and 1040 mm from the **drive end** of the rails. The two at 261.6 and 421.6
box in the motor plate. Join every cross member to both rails with a corner bracket in each inside
corner (the end members only get brackets on their inner side): drop-in T-nuts, M5 screws, snug.
Square the frame by its diagonals (equal within 1 mm), then tighten.""",
    2: """Hang a 230 mm leg under each rail end with two corner brackets: one to the rail's underside, one to
the end cross member's underside. Tap each leg's 4.2 mm centre bore M5 at the bottom and screw in
an M5 leveling foot. Level the frame on the bench.""",
    3: """Drill the motor plate from [`dxf/motor_plate.dxf`](dxf/motor_plate.dxf): a 73.5 mm pilot bore (hole saw
or the shop's lathe), 4 x M5 tapped holes on the 69.58 mm square for the motor, and 4 x 5.5 mm
corner holes for the deck screws. Bolt the NEMA 34 up against the plate's underside: shaft up,
pilot in the bore, 4 x M5 x 18 into the tapped holes. Check the screws don't stand proud of the
plate's top face.""",
    4: """Cut the deck from the HDPE sheet to 1050 x 740 mm. Tape the 1:1 print of
[`dxf/deck.dxf`](dxf/deck.dxf) on top and mark it out. Cut the 80 mm drive hole (3-1/8 in hole saw), the idler
slot (32 x 44 mm), the station window and the two 11.8 mm sensor holes. Drill and
**countersink every screw hole so the heads sit 0.3 mm below the surface**: the carriage skids
slide over them. Set the deck on the frame. Screw it down with M5 x 25 flat heads into drop-in
T-nuts in the rails and cross members. Then lift the motor plate into its box under the drive
hole and fix it with 4 x M5 x 20 flat heads from the top, nuts underneath.""",
    5: f"""Idler, from below: put the printed slider under the idler slot with the 1/2-13 stud up through it
and through the slot. Clamp it with the two M5 screws through the deck (finger-tight for now).
From above: the printed spacer (it puts the idler's tooth ring at the chain's centre plane,
{CHAIN_Z:.1f} mm above the deck), the idler sprocket, a washer and the nylon locknut, snug (the
bearing turns, not the stud). Screw the tensioner block to the deck between the sprockets. Thread
the M5 x 40 jack screw through it until it touches the slider; the slider has {TENSION_TRAVEL:.0f} mm
of travel.""",
    6: f"""Have the 35B19 bored to 14 mm H7 with a 5 mm keyway (BYU machine shop; or order it finished,
BOM item 4). Put the key in the motor shaft and slide the sprocket on **hub down**, into the deck
hole. Set the tooth ring's mid-plane {CHAIN_Z:.1f} mm above the deck: rest a 3.3 mm shim under the
tooth ring, tighten both set screws (one on the key), and remove the shim.""",
    7: """Solder 30 cm leads to the two A3144s. Push each into its printed holder, face up, and press the
holders into the sensor holes from below so the sensor face sits 0.8 mm under the deck surface.
The one on the drive side (+X in the carriage frame) is INDEX; the other is HOME.""",
    8: """Lay the chain round both sprockets to check the length (96 pitches, both spans tight with the
idler slid fully in). With the chain breaker, take out **11 riveted outer links, one every 8
pitches**, and fit an A-1 attachment connecting link in each gap, **tab up and on the outside of
the loop**. Close the loop with the 12th A-1 link. Every spring clip's closed end points the way
the chain travels (counter-clockwise from above). Back the jack screw out until the mid-span
deflection is 3-4 mm under a 5 N side push (TEST-PLAN T1), then tighten the slider clamps.""",
    9: f"""Print 12 carriages in PETG on the H2D (skids down, 0.2 mm layers, 4 walls, 30% gyroid; about
125 g each). Melt an M3 heat-set insert into each inner wall. Glue a 6 x 3 mm magnet, **south
pole down**, into the +X pocket under the inner skid of every carriage (INDEX). On carriage 1
only, glue a second one into the -X pocket (HOME). Mark carriage numbers on the ribs. Stand each
carriage on the deck against its A-1 tab and screw it on from the chain side with an M3 x 10
button head. Carriage 1 goes on the A-1 link that sits over the sensors when the chain is at
home.""",
    10: """Bolt the two hold-down blocks to the deck at the station's front edge (M4 x 30, nylon locknuts
under the deck). Slide carriage 1 under them by hand and shim each lip to 0.5 mm above the tongue
with a feeler gauge before tightening. Check that every carriage's tongue enters under the lips
without catching when it indexes in.""",
    11: f"""Module 1 is the existing hardware: Sam's Oct 8 mounting plate holding the lab auger (threaded
storage + cap). Put the plate between carriage 1's lugs, hinge end outward, and push the M5 x 70
hinge pin through lug, plate, lug. Nylon locknut snug but free: the plate must drop onto its rest
posts under its own weight. The hinge axis is {HINGE_Y:.0f} mm out from the chain line and
{HINGE_Z:.0f} mm above the deck. With the auger in the plate's clamps, its 44T gear hangs in the
carriage window and its cap end stops short of the chain.""",
    12: """Electronics board, on the bench beside the drive end:

| From | To |
|---|---|
| Mains (IEC inlet, fuse, switch) | LRS-350-36 AC input |
| LRS-350-36 +V | E-stop (NC) -> 10 A fuse -> CL86T +VDC |
| LRS-350-36 -V | CL86T GND |
| NEMA 34 A+/A-/B+/B- | CL86T A+/A-/B+/B- |
| NEMA 34 encoder (EA+/EA-/EB+/EB-/VCC/GND) | CL86T encoder port |
| Pi 5 V | CL86T PUL+, DIR+, ENA+ |
| Pi GPIO 17 / 27 / 22 | ULN2803A in 1 / 2 / 3 |
| ULN2803A out 1 / 2 / 3 | CL86T PUL- / DIR- / ENA- |
| Pi 3.3 V via 10k | GPIO 23 (INDEX), GPIO 24 (HOME), GPIO 25 (CL86T ALM+; ALM- to GND) |
| Pi 5 V, GND | Both A3144 VCC, GND; outputs to GPIO 23 / 24 |

Set the CL86T DIP switches to 4000 pulses/rev and the motor's current (6.0 A). Run `sudo pigpiod`, then
`python3 test/chain_rig.py --sim lap` to check the software and `python3 test/chain_rig.py home` to
check the hardware.""",
}


def write_bom(rs: list[dict]) -> None:
    total = sum(r["ext_usd"] for r in rs)
    rig = sum(r["ext_usd"] for r in rs if r["category"] != "Test")
    lines = ["# Bill of materials: chain-carousel test rig v0", "",
             "Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are "
             "counted from the CAD (`layout.placements()`), so this table and the Onshape assembly agree. Prices are "
             "USD as listed on 2026-10-10 and will drift. **Step** is the assembly step that uses the line "
             "([ASSEMBLY.md](ASSEMBLY.md)). `bom.csv` has the same data.", "",
             f"**Total ${total:,.2f}; rig without test gear ${rig:,.2f}.** "
             "The NEMA 34 and module 1 are already in the lab and count as $0.", "",
             "| # | Qty | Part | Vendor | Part no. | Unit | Ext. | Step |", "|---|---|---|---|---|---|---|---|"]
    cat = None
    for r in rs:
        if r["category"] != cat:
            cat = r["category"]
            lines.append(f"| | | **{cat}** | | | | | |")
        part = f"[{r['description']}]({r['url']})" if r["url"] else r["description"]
        note = f" ({r['pack']})" if r["pack"] else ""
        lines.append(f"| {r['item']} | {r['qty']} | {part}{note} | {r['vendor']} | {r['part_number']} | "
                     f"${r['unit_usd']:,.2f} | ${r['ext_usd']:,.2f} | {r['steps']} |")
    notes = getattr(bom, "NOTES", "")
    if notes:
        lines += ["", notes]
    (HERE / "BOM.md").write_text("\n".join(lines) + "\n")


def write_assembly(rs: list[dict]) -> None:
    by_step: dict[int, list[dict]] = {}
    for r in rs:
        for s in map(int, r["steps"].split(",")):
            by_step.setdefault(s, []).append(r)
    out = ["# Assembly: chain-carousel test rig v0", "",
           "Twelve steps in build order, then the test set-up. In each render the parts from earlier steps are "
           "pale, and the step's new parts are in colour, lifted along the way they go in. The table under each "
           "render is the BoM lines that step uses ([BOM.md](BOM.md) item numbers). The same order is the "
           "Onshape assembly's tree (`01 Frame` ... `12 Electronics board`).", "",
           "Tools: chain breaker (BOM item 3), metric hex keys, 8 mm and 1/2 in wrenches, drill + countersink, "
           "3-1/8 in hole saw, jigsaw, soldering iron, heat-set insert tip, feeler gauges.", ""]
    for s, title in L.STEPS.items():
        out += [f"## Step {s}. {title}", "", f"![Step {s}](renders/steps/step_{s:02d}.png)", "",
                "| # | Qty | Part |", "|---|---|---|"]
        for r in by_step.get(s, []):
            out.append(f"| {r['item']} | {r['qty']} | {r['description']} |")
        out += ["", STEP_TEXT[s], ""]
    out += ["## Step 13. Test set-up (not in the CAD)", "", "| # | Qty | Part |", "|---|---|---|"]
    for r in by_step.get(13, []):
        out.append(f"| {r['item']} | {r['qty']} | {r['description']} |")
    out += ["", "Put a 250 g dummy (a salt bag taped to the plate) on carriages 2-12, mount the dial indicator on its "
            "magnetic base on a steel plate on the deck at the station, and stick the ADXL345 to module 1's "
            "mounting plate near the outlet. Then run [TEST-PLAN.md](TEST-PLAN.md) T0-T7.", ""]
    (HERE / "ASSEMBLY.md").write_text("\n".join(out))


if __name__ == "__main__":
    rs = bom.rows()
    bom.write()
    write_bom(rs)
    write_assembly(rs)
    print("wrote BOM.md, bom.csv, ASSEMBLY.md")

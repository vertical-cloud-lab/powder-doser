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
    1: """The frame uses one VEVOR 10-pack of 1000 mm 2020 bars: 2 whole bars are the long rails, 7 are cut
to 690 mm for the cross members, and 4 legs of 230 mm come from the offcuts. Lay the rails parallel,
710 mm apart centre to centre. Put the cross members between them at 10, 236.6, 396.6, 560, 580, 780
and 990 mm from the **drive end** of the rails:

- the pair at 236.6 and 396.6 box in the motor plate;
- the touching pair at 560 and 580 carry the seam between the two deck sheets, one sheet edge each.

Join each cross member to both rails with a corner bracket in each inside corner. The end members
only get brackets on their inner side. Use M5 x 10 button heads into drop-in T-nuts, snug. Square the
frame by its diagonals (equal within 1 mm), then tighten.""",
    2: """Hang a 230 mm leg under each rail end with two corner brackets: one to the rail's underside, one to
the end cross member's underside. Tap each leg's 4.2 mm centre bore M5 at the bottom and screw in
an M5 leveling foot. Level the frame on the bench.""",
    3: """Make the motor plate from [`dxf/motor_plate.dxf`](dxf/motor_plate.dxf): 1/4 in 6061, 140 x 140 mm, a 73.5 mm
pilot bore (hole saw or the shop's lathe), 4 x M5 tapped holes on the 69.6 mm square, and 4 x 5.5 mm corner
holes for the screws that hang it from the deck. Bolt the NEMA 34 up against the plate's underside: shaft
up, pilot in the bore, 4 x M5 x 12 through the motor flange into the tapped holes. The screws must not
stand proud of the plate's top face. The 34HS59 is 169 mm long and weighs about 6 kg; it hangs 190 mm
below the deck.""",
    4: """The deck is two 1/2 in HDPE sheets, both cut from 24 x 48 in stock to a 740 mm width: the idler half
is 455 mm long, the drive half 595 mm. They butt together over the touching pair of cross members at
560/580 mm from the drive end, and each sheet screws into its own member. Print
[`dxf/deck_left.dxf`](dxf/deck_left.dxf) and [`dxf/deck_right.dxf`](dxf/deck_right.dxf) at 1:1, tape them on and mark out.
Cut the 80 mm drive hole (3-1/8 in hole saw), the idler slot (22 x 34 mm), the station window
and the two 11.8 mm sensor holes. Drill and **countersink every screw hole so the heads sit 0.3 mm
below the surface**, because the carriage skids slide over them. Lay both halves on the frame and screw
them down with M5 x 18 flat heads into drop-in T-nuts in the rails and cross members. Then lift the
motor plate into its box under the drive hole and fix it with 4 x M5 x 25 flat heads from the top,
with nylock nuts underneath.""",
    5: f"""Measure the idler sprocket's width through its bearing, W. Print the spacer with height
12.7 + {CHAIN_Z:.1f} - W/2 mm, which puts the tooth ring at the chain's centre plane, {CHAIN_Z:.1f} mm
above the deck. The model uses W = 9.65 mm, the 35BB19H figure.

1. From below: put the printed slider under the idler slot with the 1/2-13 bolt up through it and
   the slot. Clamp it with the two M5 x 25 flat heads through the deck, finger-tight for now.
2. From above: the spacer, the idler sprocket, a washer and the nylock nut. Make it snug: the bearing
   turns, not the bolt.
3. Screw the tensioner block to the deck's underside with two M4 x 20 flat heads from the top, and
   trap an M5 nut in it.
4. Thread the M5 x 40 jack screw through the block until it touches the slider's face. The slider
   has {TENSION_TRAVEL:.0f} mm of travel.""",
    6: f"""Have the 35B19 bored to 14 mm H7 with a 5 mm keyway (BYU machine shop). Check that the key is in
the motor shaft, then slide the sprocket on **hub down**, into the deck hole. Set the tooth ring's
mid-plane {CHAIN_Z:.1f} mm above the deck: rest a 3.3 mm shim under the tooth ring, tighten both set
screws (one over the key), and remove the shim. The 37 mm shaft stands about 10 mm above the sprocket.""",
    7: """Solder 30 cm leads to the two US5881 sensors. Push each into its printed holder, face up, and press the
holders into the sensor holes from below so the sensor face sits 0.8 mm under the deck surface.
The one on the drive side (+X in the carriage frame) is INDEX; the other is HOME. Both run on 5 V,
and their open-drain outputs get 10k pull-ups to 3.3 V.""",
    8: """**First measure the chain** (see the BoM note): about 4.78 mm between the inner plates and a 5.08 mm
bushing means ANSI 35, which is what the sprockets are. Lay it round both sprockets to check the
length: 96 pitches, both spans tight with the idler slid fully in.

With the chain breaker, take out **11 riveted outer links, one every 8 pitches**. Fit an A-1
attachment connecting link in each gap, **tab up and on the outside of the loop**, then close the
loop with the 12th A-1 link. Each spring clip's closed end points the way the chain travels
(counter-clockwise seen from above).

Back the jack screw out until the mid-span deflection is 3-4 mm under a 5 N side push (TEST-PLAN
T1), then tighten the slider clamps.""",
    9: """Print 12 carriages in PETG on the H2D: skids down, 0.2 mm layers, 4 walls, 30% gyroid, about 125 g
each. Then, on each one:

1. Melt an M2.5 heat-set insert into the inner wall.
2. Glue a 1/4 x 1/8 in magnet, **south pole down**, into the +X pocket under the inner skid (INDEX).
3. On carriage 1 only, glue a second magnet into the -X pocket (HOME).
4. Write the carriage number on a rib.

Stand each carriage on the deck against its A-1 tab and screw it on from the chain side with an
M2.5 x 8 button head through the tab's 0.10 in hole. Carriage 1 goes on the A-1 link that sits over
the sensors when the chain is at home.""",
    10: """Bolt the two hold-down blocks to the front rail at the station: M4 x 25 screws into M4 drop-in T-nuts in
the rail's top slot, through the deck. Slide carriage 1 under them by hand. With a feeler gauge, set
each lip 0.5 mm above the tongue before tightening. Then index every carriage in and check its tongue
slides under the lips without catching.""",
    11: f"""Module 1 is the hardware the lab already has: Sam's Oct 8 mounting plate holding the lab auger
(threaded storage + cap). The 44T gear sits in the 10.1 mm gap between his second and third clamp
rings, with the outlet end at the hinge.

Put the plate between carriage 1's lugs, hinge end outward. Pin each side with an M5 x 18 socket
head through the lug into the plate's knuckle, with a nylock nut. A single through-pin would cross
the auger's outlet end. Leave the nuts snug but free, so the plate drops onto its rest posts under
its own weight. The hinge axis is {HINGE_Y:.0f} mm out from the chain line and {HINGE_Z:.0f} mm above the
deck. The gear hangs in the carriage window, and the cap end stops 20 mm short of the chain.""",
    12: """The electronics board sits on the bench beside the drive end. Wire it like this:

| From | To |
|---|---|
| Mains (IEC inlet, fuse, switch) | LRS-350-48 AC input |
| LRS-350-48 +V | E-stop (NC) -> 10 A fuse -> CL86T +VDC |
| LRS-350-48 -V | CL86T GND |
| NEMA 34 A+/A-/B+/B- | CL86T A+/A-/B+/B- |
| NEMA 34 encoder (EA+/EA-/EB+/EB-/VCC/GND) | CL86T encoder port |
| Pi GPIO 17 / 27 / 22 | 74AHCT125 inputs 1A / 2A / 3A (VCC 5 V, OE tied low) |
| 74AHCT125 outputs 1Y / 2Y / 3Y | CL86T PUL+ / DIR+ / ENA+ (logic selector at 5 V) |
| CL86T PUL- / DIR- / ENA- | Pi GND |
| Pi 3.3 V via 10k | GPIO 23 (INDEX), GPIO 24 (HOME), GPIO 25 (CL86T ALM+; ALM- to GND) |
| Pi 5 V, GND | Both US5881 VCC, GND; outputs to GPIO 23 / 24 |

The 74AHCT125 is there because a 3.3 V GPIO pin only just reaches the CL86T's 7 mA input minimum. A
ULN2803 sinking the minus terminals drops about 1 V, which would put it at the same limit.

Set the CL86T DIP switches to 4000 pulses/rev and the motor current to 6.0 A. Run `sudo pigpiod`, then
`python3 test/chain_rig.py --sim lap` to check the software and `python3 test/chain_rig.py home` to
check the hardware.""",
}


CATS = ("Chain", "Drive", "Frame", "Fasteners", "Printed", "Electronics", "Module", "Tools", "Test")


def write_bom(rs: list[dict]) -> None:
    rs = sorted(rs, key=lambda r: (CATS.index(r["category"]), r["item"]))
    total = sum(r["ext_usd"] for r in rs)
    rig = sum(r["ext_usd"] for r in rs if r["category"] != "Test")
    lines = ["# Bill of materials: chain-carousel test rig", "",
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
        lines += ["", "## Notes", "", notes]
    (HERE / "BOM.md").write_text("\n".join(lines) + "\n")


def write_assembly(rs: list[dict]) -> None:
    by_step: dict[int, list[dict]] = {}
    for r in rs:
        for s in map(int, r["steps"].split(",")):
            by_step.setdefault(s, []).append(r)
    out = ["# Assembly: chain-carousel test rig", "",
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

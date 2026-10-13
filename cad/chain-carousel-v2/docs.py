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
from params import (BRG, CHAIN_L, EXT, HINGE_W, HINGE_X, LOOP_A, LOOP_B, N_LINKS, N_MODULES, POST_Y, SIDE_Z,
                    STANDOFF_L, TENSION_TRAVEL, Z_BOT, Z_RUN, Z_TOP, Z_TOP_RAIL)

HERE = Path(__file__).resolve().parent
L_LONG = L.RAIL_X1 - L.RAIL_X0
L_CROSS = 2 * POST_Y - EXT
L_POST = Z_TOP_RAIL - 15.0 - EXT

STEP_TEXT = {
    1: f"""The frame uses half of one VEVOR 10-pack of 1000 mm 2020 bars. Cut four posts of {L_POST:.0f} mm, four long
rails of {L_LONG:.1f} mm (one post and one long rail come out of each of four bars) and four cross rails of
{L_CROSS:.0f} mm (all four from a fifth bar). Square every cut.

Lay two long rails on the bench, {2 * POST_Y:.0f} mm apart centre to centre, and put a cross rail between them at
each end, flush with the rail ends. Screw the four leveling feet up into drop-in T-nuts in the long rails'
bottom slots, 15 mm in from each end. The cross rails are held by the post brackets in step 2, so leave them
loose for now.""",
    2: f"""Stand a post on each end of the long rails (the cross rails butt against them underneath). Each post
gets four corner brackets: at its foot, one on the long rail's top on the inner side and one on the cross
rail's top; at its head, the same two under the top rails. Use M5 x 10 button heads into drop-in T-nuts.
Put the two top long rails and two top cross rails on the posts the same way as the base, then square the
box by its diagonals (equal within 1 mm) and tighten.

Don't put brackets on the posts' inner x faces between {SIDE_Z[0]:.0f} and {SIDE_Z[1]:.0f} mm: the side plates sit there.""",
    3: f"""Have the two side plates cut from 1/4 in 6061 (dxf/side_plate_front.dxf, dxf/side_plate_back.dxf;
SendCutSend or the BYU shop). Tap the four M5 holes under the top bearing slots on each plate. The back plate
also has the motor's four standoff holes.

Bolt each plate to the inner faces of its two posts with M5 x 12 button heads from the inside into drop-in
T-nuts, four per post. Set the plate's bottom edge {SIDE_Z[0]:.0f} mm above the bench (rest it on two
{SIDE_Z[0] - 35:.0f} mm blocks on the base rails while you tighten). The plates' inner faces end up
{CHAIN_L + 60:.0f} mm apart, 30 mm outside each chain.""",
    4: f"""Mount the eight flange bearings on the plates' outer faces, bolt line vertical, with M10 x 30 (or 3/8-16
x 1-1/4) bolts and nylock nuts. The four bottom bearings are fixed; their shafts are {Z_BOT:.1f} mm above the
bench. Put the four top bearings at the bottom of their slots, {-TENSION_TRAVEL[0]:.0f} mm below the
nominal {Z_TOP:.1f} mm, which leaves room to fit the chains in step 7. Snug those bolts only.

Under each top bearing, screw a printed tensioner block to the plate (two M5 x 10 into the tapped holes).
Drop an M5 nut into the block's slot and run an M5 x 30 jack screw up through it until it touches the
bearing's lower lobe.""",
    5: f"""Each shaft carries two sprockets. Feed it through the front bearing, slide on the front sprocket with its
hub toward the front, then the back sprocket with its hub toward the back, and push the shaft on through
the back bearing. Centre each sprocket's teeth on its chain line: {CHAIN_L:.0f} mm apart, with the front
one 30 mm inside the front plate. A 30 mm spacer block between the plate and the tooth ring sets it. Snug
one set screw on each sprocket so the teeth stay put, and leave the rest loose: the carriages set the
phase between front and back in step 8. Tighten the bearings' own set screws on the shaft.

The drive shaft (B+, bottom, +y side) is 20 mm longer than the other three and sticks out of the back
bearing.""",
    6: f"""Screw four M5 hex standoffs ({STANDOFF_L:.0f} mm) to the back plate around the drive shaft, using M5 x 12
from inside. Put the jaw coupling's 1/2 in hub on the drive shaft's stub and the 14 mm hub on the motor
shaft over its key. Offer the NEMA 34 up with the spider between the jaws, and screw its flange to the
standoffs with four M5 x 20. Leave about 1 mm of float between the jaws, then tighten both hubs.

The motor is 6 kg on {STANDOFF_L:.0f} mm standoffs. Lift it while you fit it, and don't hang anything else from it.""",
    7: f"""**First measure the chain** (see the BoM note): about 4.78 mm between the inner plates and a 5.08 mm
bushing means ANSI 35, which is what the sprockets are.

Cut two loops of {N_LINKS} pitches from the 10 ft roll with the chain breaker. In each, take out an outer link
every 8 pitches and fit an A-1 attachment connecting link in its place, 13 per chain. On the front chain
the tabs point back (+x, toward the other chain); on the back chain they point forward. Number the A-1
links 1-13 the same way on both chains.

Wrap each chain round its four sprockets with the tabs on the outside of the loop, then close it with its
13th A-1 link. Each spring clip's closed end points the way the chain travels. The chains hang slack,
because the top shafts are still at the bottom of their slots.""",
    8: f"""Print {N_MODULES} carriages in PETG on the H2D, outer face down, laid on the bed's diagonal (each is
{CHAIN_L + 46:.0f} mm long). Use 0.2 mm layers, 4 walls and 30% gyroid. On each carriage:

1. Melt an M2.5 heat-set insert into each end, under where the A-1 tab sits.
2. Glue a 1/4 x 1/8 in magnet, **south pole up**, into the front tongue's pocket (INDEX).
3. On carriage 1 only, glue a second one into the back tongue's pocket (HOME).

Turn the drive shaft by hand until A-1 link 1 on both chains is on the bottom run, then lay carriage 1
under the two tabs and screw it on with two M2.5 x 6 button heads, one through each tab. Index on and fit
the other twelve. The carriages now lock the chains in phase. Tighten the remaining sprocket set screws.

To tension, turn the four jack screws the same amount until each long side deflects 3-4 mm under a 5 N
side push at mid-span. Do the front and back together, so the top shafts stay level. Then tighten the top
bearings' bolts.""",
    9: f"""Melt two M5 heat-set inserts into the plate-side face of each printed hold-down. Push a US5881 hall
switch into each lip's pocket, flat (branded) face down, and lead the wires out of the top. The front
switch is INDEX and the back one is HOME.

With carriage 1 at the station, hold each hold-down against its plate's inner face with its C round the
carriage's tongue, and screw it on from outside with two M5 x 16. The holes are slotted, so set the lip
0.5 mm over the tongue with a feeler gauge before tightening. Then index all {N_MODULES} carriages through by
hand. Each tongue must slide into both C's without catching.""",
    10: f"""Module 1 is the lab's: Sam's Oct 8 mounting plate holding the lab auger (threaded storage + cap). The
44T gear sits in the 10.1 mm gap between his second and third clamp rings, with the outlet end at the
hinge. Modules 2-{N_MODULES} are stand-ins of the same size and mass: a printed mounting plate (Sam's Onshape
part), a printed auger blank (stl/auger_blank.stl: the auger's outside, hollow) filled with table salt to
about 200 g in all, and a printed cap.

Put each plate between its carriage's lugs, hinge end at the front, and pin it with two M5 x 10 flat
heads through the lugs into the knuckle. Then press the plate's free end down past the two snap hooks.
The hooks hold it shut on the top run, where it hangs upside down. The hinge axis is {HINGE_X:.0f} mm behind
the front chain and {HINGE_W:.2f} mm inside the chain line.

Sam's electronics carriage is shown docked under module 1 at the station. It belongs to the station
(linear actuator not yet designed), not to this rig.""",
    11: """The electronics board sits on the bench beside the back of the rig. Wire it like this:

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

Run the hall-switch leads down the front and back plates' inner faces in adhesive cable clips, clear of
the tongues.

Set the CL86T DIP switches to 4000 pulses/rev and the motor current to 6.0 A. Run `sudo pigpiod`, then
`python3 test/chain_rig.py --sim lap` to check the software and `python3 test/chain_rig.py home` to check the
hardware. At 4000 pulses/rev one module is exactly 1000 steps.""",
}


CATS = ("Chain", "Shafts", "Drive", "Frame", "Fasteners", "Printed", "Electronics", "Module", "Tools", "Test")


def write_bom(rs: list[dict]) -> None:
    rs = sorted(rs, key=lambda r: (CATS.index(r["category"]), r["item"]))
    total = sum(r["ext_usd"] for r in rs)
    rig = sum(r["ext_usd"] for r in rs if r["category"] != "Test")
    lines = ["# Bill of materials: chain-carousel test rig v2 (vertical twin chain)", "",
             "Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are "
             "counted from the CAD (`layout.placements()`), so this table and the Onshape assembly agree. Prices are "
             "USD as listed on 2026-10-13 and will drift. **Step** is the assembly step that uses the line "
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
    out = ["# Assembly: chain-carousel test rig v2 (vertical twin chain)", "",
           "Eleven steps in build order, then the test set-up. In each render the parts from earlier steps are "
           "pale, and the step's new parts are in colour, lifted along the way they go in. The table under each "
           "render is the BoM lines that step uses ([BOM.md](BOM.md) item numbers). The same order is the "
           "Onshape assembly's tree (`01 Base frame` ... `11 Electronics board`).", "",
           "Tools: chain breaker, metric hex keys, 8 and 16 mm (or 9/16 in) wrenches, M5 tap, chop or band saw for "
           "the 2020 and the shafts, soldering iron, heat-set insert tip, feeler gauges.", ""]
    for s, title in L.STEPS.items():
        out += [f"## Step {s}. {title}", "", f"![Step {s}](renders/steps/step_{s:02d}.png)", "",
                "| # | Qty | Part |", "|---|---|---|"]
        for r in by_step.get(s, []):
            out.append(f"| {r['item']} | {r['qty']} | {r['description']} |")
        out += ["", STEP_TEXT[s], ""]
    out += ["## Step 12. Test set-up (not in the CAD)", "", "| # | Qty | Part |", "|---|---|---|"]
    for r in by_step.get(12, []):
        out.append(f"| {r['item']} | {r['qty']} | {r['description']} |")
    out += ["", "Fill the auger blanks on carriages 2-13 with salt to about 200 g per module. Clamp the dial "
            "indicator's magnetic base to a steel plate screwed to the front side plate's inner face beside the "
            "station, and stick the ADXL343 to module 1's mounting plate near the outlet. Then run "
            "[TEST-PLAN.md](TEST-PLAN.md) T0-T8.", ""]
    (HERE / "ASSEMBLY.md").write_text("\n".join(out))


if __name__ == "__main__":
    rs = bom.rows()
    bom.write()
    write_bom(rs)
    write_assembly(rs)
    print("wrote BOM.md, bom.csv, ASSEMBLY.md")

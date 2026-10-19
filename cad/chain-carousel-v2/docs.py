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
from params import (BRG, CHAIN_L, DOCK_EXT, DRIVE_LINKS, DRIVE_TRAVEL, EXT, HINGE_W, HINGE_X, HOOK_SLIDE, N_LINKS, N_MODULES, POST_Y,
                    SIDE_Z, SIDE_Z_BACK, TENSION_TRAVEL, YOKE_X, YOKE_Z, Z_BASE, Z_BOT, Z_MOTOR, Z_TOP, Z_TOP_RAIL)

HERE = Path(__file__).resolve().parent
L_LONG = L.RAIL_X1 - L.RAIL_X0
L_CROSS = 2 * POST_Y - EXT
L_POST = Z_TOP_RAIL - Z_BASE - EXT
L_FORK = L.FORK_Z - 6.0 - (Z_BASE + EXT)
L_VIAL = L.WEDGE_Z - (Z_BASE + EXT)

STEP_TEXT = {
    1: f"""The frame uses seven bars of one VEVOR 10-pack of 1000 mm 2020. Cut four posts of {L_POST:.0f} mm (each
offcut gives a {L_CROSS:.0f} mm cross rail), four long rails of {L_LONG:.1f} mm (two per bar), and from a seventh bar
the station rail ({L_CROSS:.0f} mm), the fork post ({L_FORK:.0f} mm) and the vial post ({L_VIAL:.0f} mm). Square every cut.

Lay two long rails on the bench, {2 * POST_Y:.0f} mm apart centre to centre, with a cross rail between them at each
end and the station rail {L.STATION_RAIL_X:.0f} mm behind the front chain's plane (two corner brackets). Screw the
four leveling feet up into T-nuts in the long rails' bottom slots, 15 mm in from each end. Blue Loctite on every
screw that goes into a T-nut.""",
    2: f"""Stand a post on each end of the long rails. Each post gets four corner brackets: at its foot, one on the
long rail's top on the inner side and one on the cross rail's top; at its head, the same two under the top rails.
Use M5 x 10 button heads into drop-in T-nuts. Put the two top long rails and two top cross rails on the posts the
same way as the base, then square the box by its diagonals (equal within 1 mm) and tighten.

Don't put brackets on the posts' inner x faces between {SIDE_Z_BACK[0]:.0f} and {SIDE_Z[1]:.0f} mm: the side plates sit there.""",
    3: f"""Have the two side plates cut from one 12 x 36 in sheet of 1/4 in 6061 (`dxf/side_plate_front.dxf`,
`dxf/side_plate_back.dxf`, by the BYU shop or SendCutSend). The front plate is 244 x {SIDE_Z[1] - SIDE_Z[0]:.0f} mm. The back
plate runs down to {SIDE_Z_BACK[0]:.0f} mm above the bench, 244 x {SIDE_Z_BACK[1] - SIDE_Z_BACK[0]:.0f} mm, because it carries the motor.
Tap the four M5 holes under the top bearing slots on each plate.

Bolt each plate to the inner faces of its two posts with M5 x 12 button heads from the inside into drop-in T-nuts.
Set the front plate's bottom edge {SIDE_Z[0]:.0f} mm above the bench and the back plate's {SIDE_Z_BACK[0]:.0f} mm. The plates' inner
faces end up {CHAIN_L + 60:.0f} mm apart, 30 mm outside each chain.""",
    4: f"""Mount the eight SBSFL202-10 flange bearings on the plates' outer faces, bolt line horizontal, with
1/4-20 x 1 in bolts and nylon-insert locknuts on the plates' inner faces. Each bearing's rear dome sits in its
plate's 49 mm hole. The bottom shafts are {Z_BOT:.1f} mm above the bench. Put the four top bearings at the bottom of their
slots, {-TENSION_TRAVEL[0]:.0f} mm below the nominal {Z_TOP:.1f} mm, which leaves room to fit the chains. Snug those bolts only.

Under each top bearing, screw a printed tensioner block to the plate (two M5 x 10 into the tapped holes, blue
Loctite). Drop an M5 nylon-insert locknut into the block's slot and run an M5 x 30 jack screw up through it until it
touches the underside of the bearing's front dome. The locknut keeps the jack screw from turning with the vibration.""",
    5: f"""Cut the 72 in keyed bar into three shafts of {L.SHAFT_L:.1f} mm and one of {L.SHAFT_L + L.DRIVE_EXTRA:.1f} mm. The long
one is the drive shaft and goes in the bottom +y corner (B+). Each shaft carries two sprockets. Feed it through the
front bearing, slide on the front sprocket with its hub toward the front, then the back sprocket with its hub toward
the back, and push the shaft on through the back bearing.

Centre each sprocket's teeth on its chain line, {CHAIN_L:.0f} mm apart, the front one 30 mm inside the front plate. Key
the front sprocket and tighten its set screws (blue Loctite). Leave the back one's key out and its set screws loose:
the carriages set its phase in step 10. Tighten the bearings' set screws on the shaft.""",
    6: f"""Have the shop re-bore the 35BS15H-1/2 sprocket to 14 mm H7 with a 5 mm keyway, then slide it onto the NEMA 34's
shaft, hub outward, over the key. Offer the motor up to the back plate's inner face from inside the frame, with its
pilot in the plate's slot and the shaft and sprocket out the back. Bolt it on with four M5 x 25 from outside and
nylon-insert locknuts on the flange. The motor's axis is {Z_MOTOR:.1f} mm above the bench, right under the drive shaft.
It is 6 kg, so support it while you fit the bolts.

Key the 35BS15H-5/8 sprocket onto the drive shaft's stub, in line with the motor's sprocket. Cut {DRIVE_LINKS} pitches from
the 10 ft roll and close them round both sprockets. Pull the motor down in its slots (+-{DRIVE_TRAVEL:.0f} mm) until the
chain has about 2 mm of play at mid-span, then tighten its bolts.""",
    7: f"""**First measure the chain** (see the BoM note): about 4.78 mm between the inner plates and a 5.08 mm bushing
means ANSI 35, which is what the sprockets are.

Cut two loops of {N_LINKS} pitches from the 10 ft roll. In each, take out an outer link every 8 pitches and fit an A-1
attachment connecting link in its place, 13 per chain. On the front chain the tabs point back (+x, toward the
other chain); on the back chain they point forward. Number the A-1 links 1-13 the same way on both chains.

Wrap each chain round its four sprockets with the tabs on the outside of the loop, then close it with its 13th A-1
link. Each spring clip's closed end points the way the chain travels (bottom run toward -y). The chains hang slack,
because the top shafts are still at the bottom of their slots.""",
    8: f"""The station, under the bottom run:

1. Hold-downs: melt two M5 inserts into each printed hold-down, push a US5881 into each lip's pocket (INDEX front,
   HOME back), and screw them to the plates' inner faces with two M5 x 16 (blue Loctite). The lip sits 2 mm over the
   carriage tongue, the foot 4 mm under it; both have 3 mm lead-ins.
2. Actuator: the printed base clevis on the station rail (two M5 into T-nuts), the P16-150's rear clevis on a
   4 x 30 mm shoulder screw and M3 locknut.
3. Electronics carriage (Sam's): face the KHK SS1-20A pinion's hub off and bond it onto the NEMA 11's shaft with
   Loctite 638, flush with the shaft end (the motor sits inside the carriage on its back wall, boss in the recess). Bond the dock electromagnet (Adafruit 3872) into the
   printed bracket and fix the bracket with the NEMA 11's two upper M2.5 screws (lengthened by 3 mm). Press two 4 mm
   steel locating pins into the rim at Sam's ({30}, 16) and (70, -16). Bond a printed stub-pin plate to each side post
   (mirror-image pair, tails pointing back and down) and press a 4 mm stub pin through post and plate at Sam's
   ({YOKE_X:.0f}, {YOKE_Z:.0f}).
4. U-yoke: screw the two 2 mm steel arms to the printed crossbar (M3 x 8 into inserts), glue a stop block inside each
   arm under the pin plate's tail (mirror-image pair), push the P16's rod-end plug into the crossbar's square socket
   and bolt it with an M4 x 25. Hang the carriage on the stub pins in the arms and fit a DIN 6799-3.2 e-clip on each
   pin. Set the NEMA 11's DRV8825 to 450 mA (Vref 0.225 V) before the first dock.
5. Approach fork on its post on the station rail, the tongue under the crossbar in its slot.
6. Vial post on the -y base rail, the level wedge, the load cell, the vial cup, the vial and the D-cut funnel.""",
    9: f"""Modules on the bench (one per carriage, {N_MODULES} in all):

1. Plate: melt two M3 inserts into the back strip of Sam's plate, and drill or print the locating hole (4.2 mm) and
   slot (4.2 x 6 mm) in its underside. Screw the 2 mm steel armature tab on with two M3 x 6 flat heads.
2. Slide the lab auger into the plate's clamp rings (the 44T gear between the second and third), outlet at the hinge,
   and screw on the cap.
3. Put the plate between a carriage's lugs, hinge end at the front, and push a 5 mm clevis pin through each lug into
   Sam's knuckle; e-clip on each pin's inner end (before the auger goes in, if you do it the other way round). Press
   the plate's free end down past the two snap hooks: they hold it shut on the top run, where it hangs upside down.

The carriage and its module now come on and off the chain as one unit.""",
    10: f"""At the loading position (the +y side, mid-height): hold the unit beside the two A-1 tabs, {HOOK_SLIDE:.0f} mm
off along the run, push it in until the carriage plate touches the tabs, slide it {HOOK_SLIDE:.0f} mm so the printed hooks
take the tabs, and drive an M3 x 12 button head from outside through the plate and each tab into the locknut in
the hook. Index one module (bottom run toward -y) and fit the next. After 13, tighten the back sprockets' set screws
on the round of the shaft and spot a dimple under each.

To tension, turn the four jack screws the same amount until each long side deflects 3-4 mm under a 5 N side push at
mid-span (about 80 N per chain). Do the front and back together, so the top shafts stay level, then tighten the top
bearings' bolts.""",
    11: """The electronics board sits on the bench behind the rig. Wire it like this:

| From | To |
|---|---|
| Mains (IEC inlet, fuse, switch) | LRS-350-48 AC input |
| LRS-350-48 +V | E-stop (NC) -> 10 A fuse -> CL86T +VDC |
| LRS-350-48 -V | CL86T GND |
| NEMA 34 A+/A-/B+/B- | CL86T A+/A-/B+/B- |
| NEMA 34 encoder | CL86T encoder port |
| Pi GPIO 17 / 27 / 22 | 74AHCT125 inputs 1A / 2A / 3A (VCC 5 V, OE tied low) |
| 74AHCT125 outputs 1Y / 2Y / 3Y | CL86T PUL+ / DIR+ / ENA+ (logic selector at 5 V) |
| CL86T PUL- / DIR- / ENA- | Pi GND |
| Pi 3.3 V via 10k | GPIO 23 (INDEX), GPIO 24 (HOME), GPIO 25 (CL86T ALM+; ALM- to GND) |
| Pi GPIO 18 | LAC RC input (1.0-2.0 ms = 0-150 mm); LAC on its 12 V supply |
| Pi GPIO 13 / 21 | DRV8825 STEP / DIR for the NEMA 11 (current limit 0.45 A: Vref 0.225 V) |
| Pi GPIO 16 | Dock magnet MOSFET gate (IRLB8721), 1N4001 across the coil, 5 V supply |
| Pi GPIO 12 | DRV8871 IN1 for the tap solenoid |
| Pi GPIO 5 / 6 | HX711 DT / SCK |

Set the CL86T DIP switches to 4000 pulses/rev and the motor current to 6.0 A. Run `sudo pigpiod`, then
`python3 test/chain_rig.py --sim lap` to check the software and `python3 test/chain_rig.py home` to check the
hardware. At 4000 pulses/rev one module is exactly 1000 steps.""",
}


CATS = ("Chain", "Shafts", "Drive", "Frame", "Fasteners", "Printed", "Station", "Electronics", "Module", "Tools", "Test")


def write_bom(rs: list[dict]) -> None:
    rs = sorted(rs, key=lambda r: (CATS.index(r["category"]), r["item"]))
    t = bom.totals(rs)
    lines = ["# Bill of materials: chain-carousel test rig v2 (vertical twin chain)", "",
             "Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are "
             "counted from the CAD (`layout.placements()`). Prices are USD on the date shown on each line and will "
             "drift. **Step** is the assembly step that uses the line ([ASSEMBLY.md](ASSEMBLY.md)). `bom.csv` has the "
             "same data.", "",
             f"**Total ${t['total']:,.2f}; rig without test gear ${t['without_test']:,.2f}.** Lines marked estimate "
             f"add up to ${t['estimated']:,.2f}. The NEMA 34, the CL86T, module 1's plate, the 13 augers (#134's batch "
             "of 16) and the electronics carriage's NEMA 11, solenoid and printed body are already in the lab and count as $0.", "",
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
           "render is the BoM lines that step uses ([BOM.md](BOM.md) item numbers). The animation "
           "([MP4](renders/chain_carousel_v2.mp4)) shows the same sequence moving.", "",
           "Tools: chain breaker, metric hex keys, 8 mm and 7/16 in wrenches, M5 tap, chop or band saw for "
           "the 2020 and the shafts, soldering iron, heat-set insert tip, e-clip pliers, feeler gauges.", ""]
    for s, title in L.STEPS.items():
        out += [f"## Step {s}. {title}", "", f"![Step {s}](renders/steps/step_{s:02d}.png)", "",
                "| # | Qty | Part |", "|---|---|---|"]
        for r in by_step.get(s, []):
            out.append(f"| {r['item']} | {r['qty']} | {r['description']} |")
        out += ["", STEP_TEXT[s], ""]
    out += ["## Step 12. Test set-up (not in the CAD)", "", "| # | Qty | Part |", "|---|---|---|"]
    for r in by_step.get(12, []):
        out.append(f"| {r['item']} | {r['qty']} | {r['description']} |")
    out += ["", "Fill the augers to a working mass with salt (or the powder under test). Clamp the dial indicator's "
            "magnetic base to a steel plate screwed to the front side plate's inner face beside the station, and stick "
            "the ADXL343 to module 1's mounting plate near the outlet. Then run [TEST-PLAN.md](TEST-PLAN.md).", ""]
    (HERE / "ASSEMBLY.md").write_text("\n".join(out))


if __name__ == "__main__":
    rs = bom.rows()
    bom.write()
    write_bom(rs)
    write_assembly(rs)
    print("wrote BOM.md, bom.csv, ASSEMBLY.md")

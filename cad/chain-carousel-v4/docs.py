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
from params import (BRG, CHAIN_L, DRIVE_LINKS, DRIVE_TRAVEL, EXT, HINGE_W, HINGE_X, HOOK_SLIDE, N_LINKS, N_MODULES, POST_Y,
                    SIDE_Z, SIDE_Z_BACK, TENSION_TRAVEL, Z_BASE, Z_BOT, Z_MOTOR, Z_TOP, Z_TOP_RAIL, PARK_DROP, DOOR_TRAVEL, LATCH_TRAVEL,
                    EC_PIN, KC4_A, KC4_B, KC4_C, EC_BALLS, ACRYLIC_T, PANEL_STANDOFF, HATCH_FRONT, HATCH_SIDE, SIDE_W, LATCH4_ENGAGE,
                    TILT_MAX_V4)

HERE = Path(__file__).resolve().parent
L_LONG = L.RAIL_X1 - L.RAIL_X0
L_CROSS = 2 * POST_Y - EXT
L_POST = Z_TOP_RAIL - Z_BASE - EXT
L_CRADLE = L.CRADLE_FLOOR_Z - (Z_BASE + EXT)
L_LATCH = L.HINGE_STATION[2] - L.P4.STATION_RAILS_OUTER - 35.0 - (Z_BASE + EXT)

STEP_TEXT = {
    1: f"""The frame uses nine bars of one VEVOR 10-pack of 1000 mm 2020 (v4's frame is wider and taller than v3's, because
the modules ride outside the loop). Cut four posts of {L_POST:.0f} mm (one bar each; two of the offcuts give the cradle post,
{L_CRADLE:.0f} mm, and the station-rails post, {L_LATCH:.0f} mm), four long rails of {L_LONG:.1f} mm (two per bar), and six rails of
{L_CROSS:.0f} mm (two per bar): four cross rails and the two station rails. Square every cut.

Lay two long rails on the bench, {2 * POST_Y:.0f} mm apart centre to centre, with a cross rail between them at each
end, the actuator's station rail {L.STATION_RAIL_X:.0f} mm behind the front chain's plane and the latch-rail post's station
rail at {L.LATCH_RAIL_X:.0f} mm (two corner brackets each). Screw the
four leveling feet up into T-nuts in the long rails' bottom slots, 15 mm in from each end. Blue Loctite on every
screw that goes into a T-nut.""",
    2: f"""Stand a post on each end of the long rails. Each post gets four corner brackets: at its foot, one on the
long rail's top on the inner side and one on the cross rail's top; at its head, the same two under the top rails.
Use M5 x 10 button heads into drop-in T-nuts. Put the two top long rails and two top cross rails on the posts the
same way as the base, then square the box by its diagonals (equal within 1 mm) and tighten.

Don't put brackets on the posts' inner x faces between {SIDE_Z_BACK[0]:.0f} and {SIDE_Z[1]:.0f} mm: the side plates sit there.""",
    3: f"""Have the two side plates cut from one 24 x 36 in sheet of 1/4 in 6061 (`dxf/side_plate_front.dxf`,
`dxf/side_plate_back.dxf`, by the BYU shop or SendCutSend). The front plate is {SIDE_W:.0f} x {SIDE_Z[1] - SIDE_Z[0]:.0f} mm. The back
plate runs down to {SIDE_Z_BACK[0]:.0f} mm above the bench, {SIDE_W:.0f} x {SIDE_Z_BACK[1] - SIDE_Z_BACK[0]:.0f} mm, because it carries the motor.
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

1. Hold-downs: as v2. Melt two M5 inserts into each printed hold-down, push a US5881 into each lip's pocket (INDEX
   front, HOME back) and screw them to the plates' inner faces with two M5 x 16 (blue Loctite).
2. Side tabs (item 5a) at the loading position (+y side, mid-height): the same way, two M5 inserts each, on the plates'
   inner faces. Their lips cover only the bottom 8 mm of a tongue, so a carriage slid {HOOK_SLIDE:.0f} mm up comes out.
3. Actuator: the printed base clevis on the actuator's station rail (two M5 into T-nuts); the P16-150's rear tab on a
   4 x 16 mm shoulder screw (McMaster 90265A123) and an M3 locknut.
4. Electronics carriage v4 (print `stl/electronics_carriage_v4.stl`, Sam's carriage printed upside down with the new
   features). It parks under the module and reaches up round the auger to the plate's auger side:
   - press the four 1/4 in steel balls into the base's three pockets and into the +y arm's boss (ball C), 3.8 mm proud;
   - push a D44-N52 magnet into the pocket behind the cone (+y arm), behind the vee (-y arm) and behind ball C, then press
     the vee's two 1/8 x 5/16 in dowels in over its magnet. There is no electromagnet in v4: the module's own weight,
     resting on the EC, and the three magnets hold the dock;
   - fit the NEMA 11 and the solenoid as Sam's carriage; bond the KHK SS1-20A pinion (hub faced off) onto the motor shaft
     with Loctite 638;
   - put the P16's rod-end tab between the clevis cheeks and push a 4 x 20 mm shoulder screw through cheeks, two PTFE
     washers each side and the tab; M3 locknut. The pin rides in 2 mm slots, so the actuator can stop short of the dock
     or the seat without forcing either.
5. Guide cradle (`stl/cradle.stl`, v3's turned over): press its two vee dowels in, bond the M4 washer into the flat pocket,
   bolt the cradle's arm onto the cradle post's top end and the post onto the station rail beside the P16. Lower the EC
   into it: its three balls sit in the cone, the vee and on the washer. It parks {PARK_DROP:.0f} mm below the passing augers.
6. Station rails (`stl/latch_rail.stl`, one part on its own post on the second station rail): the latch rail, whose face
   runs along the travel {LATCH_TRAVEL} mm inside the carriages' latch followers' tips with 25 degree ramps at both ends,
   and the tube rest, 0.5 mm under the passing augers' tubes behind the keeper. At the station the rail holds the latch
   open and the module rests on the tube rest until the EC lifts it off.""",
    9: f"""Modules on the bench (one per carriage, {N_MODULES} in all):

1. Plate v4 (`stl/mounting_plate_v4.stl`: Sam's plate with the dock on its auger side, the latch keeper with its 4.2 mm
   pin hole, two M2 insert holes). Press two 1/4 in balls into the pockets at Sam's ({KC4_A[0]:.0f}, +-{KC4_A[1]:.1f}) on the auger
   side, 3.8 mm proud, and bond an M5 steel washer flush into the pocket at ({KC4_C[0]:.0f}, {KC4_C[1]:.1f}) (the dock's flat).
2. Outlet door (v3's, turned over: the shutter slides toward the plate to open): melt two M2 inserts into the plate beside
   the tube, drop the shutter into the printed housing with the spring behind it, and screw the housing's two arms to the
   plate (M2 x 8). The shutter covers the 3 mm exit; its push strip runs out past the auger, where the EC's finger meets it.
3. Slide the lab auger into the plate's clamp rings (the 44T gear behind the rear ring), outlet against the door's
   housing, and screw on the cap.
4. Put the plate between a carriage v4's lugs on the carriage's outer face, hinge end at the front, and push a 5 mm clevis
   pin through each lug into the plate's knuckles; e-clip on each pin's inner end. Pull the latch's follower back with a
   finger, lay the plate down and let go: the latch's 4 mm pin goes {LATCH4_ENGAGE:.0f} mm into the keeper's hole and holds the plate
   both ways (the carriage's opening leaves nothing under the plate).""",
    10: f"""At the loading position (the +y side, mid-height), with the auger facing out toward the side hatch: hold the unit
beside the two A-1 tabs, {HOOK_SLIDE:.0f} mm
up from position, push it in until the carriage plate touches the tabs, slide it {HOOK_SLIDE:.0f} mm down so the printed hooks
take the tabs and the tongues go under the side tabs' lips, and drive an M3 x 12 button head from outside through the
plate and each tab into the locknut in the hook. Index one module (bottom run toward -y) and fit the next. After 13,
tighten the back sprockets' set screws on the round of the shaft and spot a dimple under each.

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
| Pi GPIO 12 | DRV8871 IN1 for the tap solenoid |
| Pi UART RX/TX (GPIO 15 / 14) | MAX3232 -> HR-100A RS-232 (DB-9) |

Set the CL86T DIP switches to 4000 pulses/rev and the motor current to 6.0 A. Run `sudo pigpiod`, then
`python3 test/chain_rig.py --sim lap` to check the software and `python3 test/chain_rig.py home` to check the
hardware. At 4000 pulses/rev one module is exactly 1000 steps.""",
    12: f"""Enclosure (item 5): laser-cut the panels and the two hatch doors from 1/8 in clear cast acrylic (`dxf/panel_*.dxf`,
`dxf/hatch_*.dxf`). Each panel stands {PANEL_STANDOFF:.0f} mm off the frame on nylon spacers (M5 x 16 button heads into T-nuts), so it
clears the side runs' carriages and the side tabs; the back panel's spacers are 30 mm, past the drive sprocket. The front
panel's hatch ({HATCH_FRONT[0]:.0f} x {HATCH_FRONT[1]:.0f} mm, under the station) and the +y panel's hatch ({HATCH_SIDE[0]:.0f} x {HATCH_SIDE[1]:.0f} mm, at the
loading position) each get a door 4 mm larger all round on two stainless butt hinges, a printed knob and a turn
button.

The HR-100A: v4 draws the balance where it has to stand, its pan under the dose point. It doesn't fit there yet: the
SCALE_BLOCKERS stand inside its breeze break's footprint (`check_interference.py --scale`,
`renders/features/scale_fit.gif`). Until the station is moved, test doses go into a beaker on a bench balance placed
by hand under the dose point with the station parked.""",
}


CATS = ("Chain", "Shafts", "Drive", "Frame", "Fasteners", "Printed", "Station", "Doors", "Enclosure", "Electronics", "Module", "Tools", "Test")


def write_bom(rs: list[dict]) -> None:
    rs = sorted(rs, key=lambda r: (CATS.index(r["category"]), r["item"]))
    t = bom.totals(rs)
    lines = ["# Bill of materials: chain-carousel test rig v4", "",
             "Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are "
             "counted from the CAD (`layout.placements()`). Prices are USD on the date shown on each line and will "
             "drift. **Step** is the assembly step that uses the line ([ASSEMBLY.md](ASSEMBLY.md)). `bom.csv` has the "
             "same data.", "",
             f"**Total ${t['total']:,.2f}; rig without test gear ${t['without_test']:,.2f}.** Lines marked estimate "
             f"add up to ${t['estimated']:,.2f}. The NEMA 34, the CL86T, the 13 augers (#134's batch "
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
    out = ["# Assembly: chain-carousel test rig v4", "",
           "Twelve steps in build order, then the test set-up. In each render the parts from earlier steps are "
           "pale, and the step's new parts are in colour, lifted along the way they go in. The table under each "
           "render is the BoM lines that step uses ([BOM.md](BOM.md) item numbers). The animation "
           "([MP4](renders/chain_carousel_v4.mp4)) shows the same sequence moving.", "",
           "Tools: chain breaker, metric hex keys, 8 mm and 7/16 in wrenches, M5 tap, chop or band saw for "
           "the 2020 and the shafts, soldering iron, heat-set insert tip, e-clip pliers, feeler gauges.", ""]
    for s, title in L.STEPS.items():
        out += [f"## Step {s}. {title}", "", f"![Step {s}](renders/steps/step_{s:02d}.png)", "",
                "| # | Qty | Part |", "|---|---|---|"]
        for r in by_step.get(s, []):
            out.append(f"| {r['item']} | {r['qty']} | {r['description']} |")
        out += ["", STEP_TEXT[s], ""]
    out += ["## Step 13. Test set-up (not in the CAD)", "", "| # | Qty | Part |", "|---|---|---|"]
    for r in by_step.get(13, []):
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

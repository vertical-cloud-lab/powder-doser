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
    # 2026-11-27: rewritten for v11 (it was v4's text). Numbers are v11's: the BoM lines and the README.
    1: """Cut the 2020 from one VEVOR 10-pack (BoM item 18): four posts of 697.5 mm, four long rails of 457.7 mm, four rungs of
417.7 mm, three cross rails of 340 mm, the two 405 mm station beams (v12: the second carries the EC's second guide) and the
380 mm front bar. Square every cut, and tap both ends of both station beams M5.

The base is a U that the balance stands inside: lay two long rails on the bench and join them at the back with a cross rail (two
corner brackets each corner, M5 x 10 into drop-in T-nuts, blue Loctite on every screw that goes into a T-nut). Leave the front open:
the balance slides in there. Screw the four levelling feet up into T-nuts in the long rails' bottom slots, 15 mm in from each end.""",
    2: """Stand a post on each corner of the base and bracket it to the long rail and, at the back, to the cross rail. Put the top
frame on the posts the same way: two long rails and two cross rails. Square the box by its diagonals (equal within 1 mm) and tighten.

The ladder (Sam: "I love the ladder rungs"): on each side, two 417.7 mm rungs between the front and the back post, the lower at
86 mm and the upper at 214 mm (centres over the bench). The lower rungs' brackets go under them, just over the posts' foot brackets;
the upper rungs' tops sit 2.5 mm under the back side plate's lower edge. Nothing in v11 hangs on them; they stiffen the posts.""",
    3: """Have the two side plates cut and drilled from 1/4 in 6061 (`dxf/side_plate_front.dxf`, `dxf/side_plate_back.dxf`). v11's front
plate has the P16's 22 x 68 mm slot and, under it, the 13/16 in (20.6 mm) hole for the wiring grommet; both plates have the two station
beams' end-screw holes (v12: the second at y +56). Tap the M5 holes under the top bearing slots.

Bolt each plate to the inner faces of its two posts with M5 x 12 button heads into drop-in T-nuts (blue Loctite). The chains end up
345 mm apart, centre plane to centre plane, 30 mm inside each plate.""",
    4: """Mount the eight SBSFL202-10 flange bearings on the plates' outer faces, bolt line horizontal, with 1/4-20 x 1 in bolts and
nylon-insert locknuts inside. Put the four top bearings at the bottom of their slots, which leaves slack to fit the chains; snug
those bolts only.

Under each top bearing, screw a printed tensioner block to the plate (two M5 x 10 into the tapped holes, blue Loctite). Drop an M5
nylon-insert locknut into the block's slot and run an M5 x 30 jack screw up through it to the bearing's front dome. The locknut
stops the jack screw turning with vibration.""",
    5: """Cut the two 72 in keyed bars into three shafts of 449.8 mm and the 474.2 mm drive shaft (v11's are 40 mm longer, so they no
longer come out of one bar). The drive shaft goes in the bottom +y corner (B+). On each shaft, feed it through the front bearing,
slide on the front sprocket (hub toward the front), then the back sprocket (hub toward the back), and push it on through the back
bearing.

Centre each sprocket's teeth on its chain line, 345 mm apart. Key the front sprocket and tighten its set screws (blue Loctite). Leave
the back sprocket's key out and its set screws loose: the carriages set its phase in step 10. Tighten the bearings' set screws.""",
    6: """Have the 35BS15H-1/2 sprocket re-bored to 14 mm H7 with a 5 mm keyway, and slide it onto the NEMA 34's shaft over the key.
Offer the motor up to the back plate's inner face from inside the frame and bolt it with four M5 x 25 and nylon-insert locknuts. It
is 6 kg: support it while you fit the bolts.

Key the 35BS15H-5/8 sprocket onto the drive shaft's stub, in line with the motor's sprocket. Cut 44 pitches from the 10 ft roll and
close them round both sprockets; pull the motor down in its slots until the drive chain has about 2 mm of play at mid-span.""",
    7: """**Measure the chain first** (BoM notes): about 4.78 mm between the inner plates and a 5.08 mm bushing is ANSI 35, which the
sprockets are. ISO 06B looks the same and doesn't fit.

Cut two loops of 104 pitches from the 10 ft roll. In each, replace an outer link every 8 pitches with a Nitro CL35-A1 attachment
connecting link, 13 per chain, the tabs pointing toward the other chain. Number the A-1 links 1-13 the same way on both chains.
Wrap each chain round its four sprockets with the tabs on the outside of the loop and close it with its 13th A-1 link, each spring
clip's closed end pointing the way the chain travels (the bottom run toward -y). The chains hang slack until step 10.""",
    8: """The station is inside the loop, over the bottom run:

1. **Hold-downs and switches:** melt two M5 inserts into each printed hold-down, push a US5881 hall switch into each lip's pocket
   (INDEX front, HOME back), and screw them to the plates' inner faces (M5 x 16, blue Loctite). The side tabs go on at the loading
   position the same way.
2. **The station beams:** two 405 mm 2020s from the front side plate to the back one, at y -56 and (v12) y +56, an M5 x 16 through
   each plate into their tapped ends. A printed guide hangs from each one's bottom slot (two M5 x 10 into T-nuts): guide 1 (`guide11`)
   on the -56 beam, guide 2 (`guide12`, v12) on the +56 beam. Their seats are the cones the EC's two shoes park in.
3. **The front bar and the P16:** the 380 mm 2020 across the front posts' front faces, an M5 x 35 through it into a T-nut in each
   post's front slot (blue Loctite). The printed clevis hangs from its bottom slot (two M5 x 10). The P16-150's rear tab goes in the
   clevis on the 4 x 16 shoulder screw and an M3 nylock; its rod runs back through the front plate's slot.
4. **The pinion's cradle (v12)** (print `stl/cradle12.stl`): melt an M3 insert into the lug from its top, and push the US5881 into
   the pocket on the lug's +y face, branded face out, its leads up the slot. Cut the NEMA 11's 5 mm shaft to 15 mm (from 20), so it
   ends at the pinion's front face. Bolt the motor's face to the cradle's plate with its four M2.5 screws, shaft forward. The KHK
   SS1-24A pinion (hub faced off) goes on the shaft over a slotted 5 x 6 mm brass sleeve, its M4 set screw through the slot, Loctite
   638. Thread the M3 x 6 cup-point set screw into the lug's insert from the top until its tip just shows under the lug.
5. **EC v12** (print `stl/ec12.stl`, on its side, with supports): press the K&J D42-N52 into the magnet post beside the lug's pocket
   (south pole toward the switch: the US5881 switches on a south pole). Set the cradle between the EC's two pivot bosses and press a
   3 x 12 mm dowel through each EC boss into the cradle's bore (2.95 mm in the EC, a press fit; 3.1 mm in the cradle, free). The
   cradle must swing freely; if it doesn't, ream its bores 3.1. Drop the spring (1 N/mm, about 19 mm free) onto the cradle's peg
   and compress it into the roof's pocket as the cradle goes in. The solenoid goes in its collar over clip 1, plunger toward the
   plate. Pin the EC's arm to the P16's rod end on the 4 x 20 shoulder screw (its tab in the arm's slot, a PTFE washer each side, the
   nut in its pocket), and an M3 nylock.
6. **Set the P16** fully out (139.2 of its 150 mm) so both shoes sit in their seats with the EC level.
7. **Set the stop (v12), with module 1 at the station** (the spring holds the pinion in tight mesh: no backlash when you rock the
   auger by hand), a dial indicator on the motor's top: turn the set screw down until its tip touches the EC's arm and the dial just
   starts to move, then back it out 1.7 turns (0.85 mm at the lug, which moves 2.1 times as far as the pinion: 0.4 mm at the pinion).
   Loctite 222. Index module 1 away: the dial shows the cradle dropping 0.4 mm onto the stop.
8. **Set the switch:** with module 1 in mesh the switch must read "seated" (`chain_rig.py` logs `hall_before`); lift the pinion
   0.8 mm with a feeler gauge under the lug's stop and it must read "lifted". Shim the magnet in its post (or bend the switch's legs)
   until it switches between 0.6 and 1.0 mm.
9. **The latch cam** on the back side plate (two M5 x 12 through the plate).""",
    9: """Build each module on the bench (13):

1. Print the mounting plate (v11's, 5 per H2D plate). Melt in the two M3 inserts for the T-bracket and the two M2 inserts for the door
   housing, flush with the underside.
2. Screw the T-bracket on (two M3 x 6). Its chamfered head finds the EC's slot.
3. The outlet door (v12: print the bored housing and the shutter with its round boss): press the 1/16 in 316 rod (22.7 mm) 2 mm into
   the shutter's boss (its 1.55 mm hole), slide the spring over the rod into the housing's bored tower, the shutter into its grooves over
   the exit, and the housing on with two M2 x 8. The rod runs up the spring's axis and out through the cap's 1.8 mm hole to its printed
   head (pressed on and glued). v4-v11 drew the tower solid and the shutter's boss too small for the rod; v12 fixes both.
4. Snap the auger into clips 1 and 2, its cap on the saddle, and check it pulls straight out of the clips.
5. Pin the plate to a carriage's outer face on its two 5 mm clevis pins (e-clips). Fit the latch bolt (its 4 x 12 dowel pressed into
   the printed carrier) with its spring in the carriage's latch housing, so the pin sits in the plate's keeper.""",
    10: f"""At the loading position (the +y side, behind the side hatch), with the auger facing out: hold the carriage beside the two
A-1 tabs, {HOOK_SLIDE:.0f} mm up from position, push it in until it touches the tabs, slide it {HOOK_SLIDE:.0f} mm down so the printed hooks
take the tabs and the tongues go under the side tabs' lips, and drive an M3 x 12 button head from outside through the carriage and
each tab into the locknut in the hook. Index one module (8 pitches, bottom run toward -y) and fit the next.

After 13, tighten the back sprockets' set screws on the round of the shaft (blue Loctite) and spot a dimple under each: bolting the
carriages across both chains has set their phase. To tension, turn the four jack screws the same amount until each long side deflects
3-4 mm under a 5 N side push at mid-span (about 80 N per chain), front and back together so the top shafts stay level, then
tighten the top bearings' bolts.""",
    11: """The electronics board stands behind the rig: the 48 V supply, the CL86T for the NEMA 34, the DRV8825 for the NEMA 11 (current
limit 450 mA; its EN pin on a GPIO, so the motor is left free while a module slides into mesh), the DRV8871 for the solenoid, the
Actuonix LAC for the P16, the Pi and the interface board, and the e-stop. The NEMA 11's, the solenoid's and the P16's leads run in one
braided sleeve from the EC along its arm and the P16, out through the grommet in the front side plate, then down the post and along
the base rail to the board. The hall switches run along the plates. `test/chain_rig.py --sim` checks the wiring map before power.""",
    12: """Slide the balance in through the front doorway onto the bench, inside the base's U, touching nothing of the frame. Set the
dosing lid in its top in place of the top door, its 24 mm hole under the exit, and the beaker's pillar on the pan, the beaker in its
socket. (The lab's HR-100A has a round breeze break: its lid is a disc, and its pillar is 36.5 mm shorter; TEST-PLAN T8c.)

Then the enclosure: the acrylic panels on nylon standoffs, the front panel (with the balance's doorway) on 30 mm standoffs to clear the
front bar and the P16; the side hatch's 408 x 238 mm door on its hinges with its knob and catch.""",
}


CATS = ("Chain", "Shafts", "Drive", "Frame", "Fasteners", "Printed", "Station", "Doors", "Enclosure", "Electronics", "Module", "Tools", "Test")


def write_bom(rs: list[dict]) -> None:
    rs = sorted(rs, key=lambda r: (CATS.index(r["category"]), r["item"]))
    t = bom.totals(rs)
    lines = ["# Bill of materials: chain-carousel test rig v12", "",
             "Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are "
             "counted from the CAD (`layout.placements()`). Prices are USD on the date shown on each line and will "
             "drift. **Step** is the assembly step that uses the line (`layout.STEPS`; v12's step 8 is the station inside the loop: "
             "EC v12 with the pinion's spring-loaded cradle, the P16-150 through the front side plate and its clevis on the front bar, the "
             "two guide hangers on the two station beams; step 12 "
             "is the balance with its tall draft cage on the bench, its dosing lid and the beaker's pillar, and the enclosure with the "
             "front doorway). `bom.csv` has the same data.", "",
             f"**Total ${t['total']:,.2f}; rig without test gear ${t['without_test']:,.2f}.** Lines marked estimate "
             f"add up to ${t['estimated']:,.2f}. The NEMA 34, the CL86T, the 13 augers (#134's batch "
             "of 16), the electronics carriage's NEMA 11 and solenoid, and the balance are already in the lab and count as $0 (EC v12's "
             "body is new, item 77, and its cradle, item 122). v12's new parts (items 122-125) were priced on 2026-11-27 from McMaster's "
             "tables through the doser Pi ([checks/vendor_v12.json](checks/vendor_v12.json)).", "",
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
    out = ["# Assembly: chain-carousel test rig v12", "",
           "Twelve steps in build order, then the test set-up. Each step's title is `layout.STEPS` and its render is v12's CAD "
           "(`xvfb-run -a python render.py --steps` writes `renders/steps/step_NN.png`): the parts from earlier steps are "
           "pale, and the step's new parts are in colour, lifted along the way they go in. The table under each "
           "render is the BoM lines that step uses ([BOM.md](BOM.md) item numbers). "
           "[`renders/assembly_steps.gif`](renders/assembly_steps.gif) runs through the twelve renders. The written "
           "instructions under each table are v11's (rewritten 2026-11-27) with v12's changes: steps 1 and 3 (the second station "
           "beam), 8 (the pinion's cradle, EC v12, setting the stop and the switch) and 9 (the door's rod into the shutter's new boss).", "",
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

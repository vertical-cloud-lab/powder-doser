"""Write BOM.md, bom.csv and ASSEMBLY.md from bom.ITEMS and layout.STEP_TITLES.

    python docs.py

ASSEMBLY.md pairs each step's render (renders/steps/step_NN.png) with the BoM
lines it uses and the instructions below, so a change to the CAD or the BoM
shows up in the instructions on the next run.
"""
from __future__ import annotations

from pathlib import Path

import bom
import kinematics as K
import layout as L
from params import (ACT_RETRACTED, CHAIN_L, DOCK_EXT, HINGE_X, LOOP_A, LOOP_B, MODULE_LIFT, MODULE_PITCH, MODULE_SLIDE, N_LINKS,
                    N_MODULES, POST_Y, R, SA1_C, SIDE_IN, STEPS_PER_MODULE, TENSION_TRAVEL, THUMB_L, Z_BOT, Z_TOP)

HERE = Path(__file__).resolve().parent

STEP_TEXT = {
    1: f"""Cut the 2020 (80/20 20-2020, or any slot-6 2020): four x-rails of 444 mm, four posts of 710 mm, six cross
rails of 260 mm, and 200 mm and 170 mm for the two station posts. Lay two x-rails on the bench {2 * POST_Y:.0f} mm apart
(centres) and put the two station cross rails between them, at x = {L.STATION_RAIL_X[0]:.0f} and {L.STATION_RAIL_X[1]:.0f} mm from the front chain's
plane (the vial post and the actuator stand on them). Screw the four M6 leveling feet into T-nuts in the x-rails'
bottom slots. Every frame screw is an M5 x 10 button head into a drop-in T-nut with a drop of Loctite 243 (T-nuts
can't take a nylock).""",
    2: f"""Stand the four posts on the x-rails' ends, put a cross rail between each pair at the bottom and at the top,
and fix each joint with a cast corner bracket. Put the two top x-rails on the posts. Square the box by its
diagonals (equal within 1 mm). Keep the posts' inner faces clear between {L.SIDE_Z[0]:.0f} and {L.SIDE_Z[1]:.0f} mm: the side plates go there.""",
    3: f"""Have the two side plates and the motor plate cut from 1/4 in 6061 (`dxf/side_plate_front.dxf`, `dxf/side_plate_back.dxf`,
`dxf/motor_plate.dxf`, SendCutSend or the BYU shop). Bolt each side plate to its posts' inner faces with six M5 x 10
button heads into T-nuts, so the plates' inner faces are {CHAIN_L - 2 * SIDE_IN:.0f} mm apart, {-SIDE_IN:.0f} mm outside each chain.
Bolt the four SBSFL202-10 flange bearings to the plates' outer faces at the two bottom corners, bolt line vertical,
rear dome in the 49 mm hole, with 1/4-20 x 1 in bolts and nylon-insert locknuts.""",
    4: f"""Cut the keyed bar into 435 mm (B-) and 463 mm (B+, the drive shaft, which runs on into the coupling).
Feed each shaft through its front bearing, slide on the front 32T with its hub toward the front plate, then
the back 32T with its hub toward the back plate, and on through the back bearing. Key the front sprockets.
Leave the back sprockets' set screws loose until step 6: both chains have to hang in phase, so the back
sprockets are set from the gondolas, not from their keyways.""",
    5: f"""Top idlers: the shop re-bores four 35BS32 sprockets to 35 mm H7 and turns four axles (15 mm h6 seat, 22 mm
shoulder, M10 stem). Press two 6202-2RS into each sprocket. Put each axle's stem through the vertical slot at a
top corner of a side plate from the inside, slide the sprocket on (hub toward the plate) so its inner face ends
flush with the axle's end, and fit the M10 nylon-insert locknut outside, finger tight, with the axle at the bottom
of its slot ({-TENSION_TRAVEL[0]:.0f} mm below its working height). Nothing may stick out past the sprocket's inner face:
the gondolas pass {L.HINGE_X - 39:.0f}-odd mm from the axle's end when they go over the top.""",
    6: f"""Break the 10 ft roll into two pieces of {N_LINKS - 2 * N_MODULES:.0f} plain pitches plus the SA-1 links: each loop is {N_LINKS}
pitches with an SA-1 connecting link every {MODULE_PITCH / 9.525:.0f}th pitch ({N_MODULES} per chain, always at an outer-link position).
Fit each SA-1 with its tab on the side facing the other chain (toward the gondolas), clip on the far side. Wrap
each loop round its four sprockets, close it with the last SA-1 link, then raise the four idler axles together
with the jack screws until each chain's longest span deflects 3-4 mm under a 10 N push; lock the axle nuts.
Turn the drive shaft until a front SA-1 link is at the middle of the bottom run, set the matching back SA-1
link exactly behind it (same height), and tighten the back sprockets' set screws: the two chains are now in
phase. Rotate a full lap by hand and check every SA-1 pair is level to 0.5 mm.""",
    7: f"""Key the L090 hubs: the 5/8 in hub on the drive shaft's end behind the back bearing, the 14 mm hub on the
NEMA 34. Put the spider in, screw the four 79 mm standoffs to the back plate, bolt the motor to the motor plate
(M5 x 16 + nylon-insert locknuts), slide the motor's hub into the spider and bolt the motor plate to the standoffs.
The motor drives the bottom +y shaft directly: one module ({MODULE_PITCH:.2f} mm of chain) is 10/32 of a turn,
{STEPS_PER_MODULE} steps at 4000 pulses/rev.""",
    8: f"""Gondolas (PETG, H2D: 313 x 62 x 55 mm). Press a 6659K65 bronze bushing into each end plate's 7 mm bore from
the inside, set a magnet in the -y rail's bottom pocket (gondola 1 gets the second, HOME, magnet), and heat-set
two M5 inserts into the hinge lugs. Hang each gondola between a front and a back SA-1 link: PTFE washer on the
tab, end plate, PTFE washer under the head, and the 4 x 10 mm shoulder screw from the inside through the
bushing and the tab, with an M3 nylon-insert locknut on the chain side. Tighten the screw to the shoulder (the
shoulder clamps on the tab; the gondola turns on the shoulder). The gondola must swing freely and come back to
hanging straight down: if it sticks off-vertical by more than about half a degree, the bushing is too tight.""",
    9: f"""Modules: in each of Sam's mounting plates heat-set two M3 inserts in the back strip and screw a 2 mm steel
armature tab under it (two M3 x 6 flat heads): the dock magnet pulls on it. The plate also needs the 4.2 mm hole and
4.2 x 6 mm slot for the carriage's locating pins (print them in, or drill 3.5 mm deep). Slide an auger (lab design,
PR #170) into the plate and screw on the cap. Index the
carousel until an empty gondola is at the loading position (right side, mid-height; module k+3 is there when
module k is at the station). Hold the module with the auger's outlet toward the front, lower it {MODULE_LIFT:.0f} mm
above the floor and slide it in from the right ({MODULE_SLIDE:.0f} mm), lower it onto the floor between the lugs, and
turn the two M5 x {THUMB_L:.0f} thumb screws in from outside: their tips are the hinge pins in Sam's 5.3 mm knuckle holes.
Index one module ({STEPS_PER_MODULE} steps) and load the next. To swap a module, reverse it: two thumb screws out, lift, slide out.""",
    10: f"""Station (cad/gear-mesh has the reasons). Bolt the base clevis to the actuator cross rail and pin the Actuonix
P16-150-22-12-P's rear lug in it ({ACT_RETRACTED:.1f} mm hole to hole retracted). Sam's electronics carriage: mount the NEMA 11
on the inner face of its back wall, bond the steel KHK SS1-20A pinion (hub faced off) on the shaft's last 10 mm with
Loctite 638, screw the printed magnet bracket on the two upper motor screws and bond the Adafruit 3872 electromagnet in
its cup, press the two 4 mm locating dowels into the rim and the two 4 mm stub pins through the side posts (with the
printed pin plates bonded on). The U-yoke: push the P16's rod-end plug into the printed crossbar's square socket and
bolt it rigid (M4 x 25 + nylock), screw the two 2 mm steel arms to the crossbar, slide them over the stub pins and fit
the e-clips. The P16 + yoke is then one two-force link from the base clevis to the stub pins, which sit at the
carriage's centre-of-mass height, so the carriage can't tip off the plate when it tilts. Set the approach fork on its
post so the crossbar's tongue rides in it for the first {DOCK_EXT:.0f} mm. Wire the magnet through a logic-level MOSFET
with a 1N4001 across the coil, and set the Tic's current limit to 450 mA. Screw the two UHMW hold-down
strips to their brackets on the side plates' inner faces, 0.5 mm above the chains' bottom runs at the station:
when the module tilts, the gondola's front pivot is pulled upward (MuJoCo run, sim/README.md), and the strips stop the
chain from lifting. Wire the LAC board (12 V) to the actuator's motor and pot and set its limits so the retracted
carriage clears the passing gondolas.""",
    11: f"""Dispense: screw the load cell to the vial post and the cup to its free end, and set a vial in the cup
(its mouth sits 32 mm under the gondolas' path). Mount the INDEX and HOME hall switches under the -y rail's line,
3 mm below the passing magnets. Wire the CL86T, the LAC, the HX711 and the two hall switches to the Pi
(test/paternoster_rig.py has the pin map), with the E-stop in the driver's 48 V feed.""",
}


def bom_md(rs, t) -> str:
    lines = ["# Paternoster carousel: bill of materials", "",
             f"Generated by `bom.py` / `docs.py` from the CAD (quantities are counted from `layout.placements()`). "
             f"Prices are USD, read on the vendor's own page on the date given in the last column; \"estimate\" lines were not.", "",
             f"**Total ${t['total']:,.2f}; ${t['without_test']:,.2f} without the test gear.** Lines marked estimate add up to ${t['estimated_part']:,.2f}. "
             "The NEMA 34, the CL86T, module 1, the augers (#134's batch of 16) and the electronics carriage's NEMA 11 and solenoid (the steel pinion is bought) "
             "are already in the lab and are priced at $0.", "",
             "| # | Qty | Part | Vendor | Part no. | Unit | Ext. | Step | Price source |", "|---:|---:|---|---|---|---:|---:|---|---|"]
    for r in rs:
        pn = f"[{r['pn']}]({r['url']})" if r["url"] else r["pn"]
        lines.append(f"| {r['item']} | {r['qty']} | {r['desc']} | {r['vendor']} | {pn} | ${r['unit']:.2f} | ${r['ext']:.2f} | "
                     f"{', '.join(str(s) for s in r['steps'])} | {r['note']} |")
    cats = {}
    for r in rs:
        cats[r["cat"]] = cats.get(r["cat"], 0) + r["ext"]
    lines += ["", "| Category | Subtotal |", "|---|---:|"] + [f"| {k} | ${v:,.2f} |" for k, v in sorted(cats.items(), key=lambda kv: -kv[1])]
    lines += ["", "## Shop work", "",
              "- Cut the two side plates and the motor plate from `dxf/` (1/4 in 6061).",
              "- Re-bore four 35BS32 sprockets to 35 mm H7 for two 6202-2RS each (top idlers).",
              "- Turn four idler axles: 15 mm h6 seat (31 mm), 22 mm shoulder, M10 stem through the side plate.",
              "- Cut the keyed bar to 435 mm and 463 mm.", ""]
    return "\n".join(lines) + "\n"


def assembly_md(rs) -> str:
    by_step = {}
    for r in rs:
        for s in r["steps"]:
            by_step.setdefault(s, []).append(r)
    out = ["# Paternoster carousel: assembly", "",
           "Eleven steps from bare extrusion to a dosing station; each has a render and the BoM lines it uses "
           "([BOM.md](BOM.md)). The animation [`renders/paternoster.mp4`](renders/paternoster.mp4) shows the same "
           "build from scratch, then loading all 12 modules, a lap, a dose at the station and a module swap.", "",
           "![Assembly steps](renders/assembly_steps.gif)", ""]
    for s in range(1, 12):
        out += [f"## Step {s}: {L.STEP_TITLES[s].split(':')[0] if ':' in L.STEP_TITLES[s] else L.STEP_TITLES[s]}", "",
                f"![Step {s}](renders/steps/step_{s:02d}.png)", "", STEP_TEXT[s], ""]
        if s in by_step:
            out += ["| # | Qty | Part |", "|---:|---:|---|"] + [f"| {r['item']} | {r['qty']} | {r['desc']} |" for r in by_step[s]] + [""]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    rs = bom.rows()
    t = bom.totals(rs)
    bom.write_csv(rs)
    (HERE / "BOM.md").write_text(bom_md(rs, t))
    (HERE / "ASSEMBLY.md").write_text(assembly_md(rs))
    print(f"BOM.md ({len(rs)} lines, ${t['total']:,.2f}), ASSEMBLY.md, bom.csv")

"""Bill of materials for the chain-carousel test rig v8 (Sam's note of 2026-11-12: a new electronics carriage on his Aug 27
layout, behind the balance, with the solenoid just in front of the gear and the NEMA 11 behind it; the dock's posts and the
guides moved behind the gear; the door's push strip carried back to the EC; the pan 38 mm in front of the exit on an offset
riser; the carousel 104 mm lower; the NEMA 34 35 mm toward +y; the front panel notched round the balance, no front hatch door.
v7 is the line-for-line base).

ITEMS is the single table: item number, what, where to buy it, price, and
which assembly step uses it. Quantities of modelled parts are counted from
layout.placements(), so the BoM and the CAD cannot drift apart; unmodelled
items (wire, tools, test gear) carry their own quantity.

    python bom.py        # writes bom.csv and prints the totals
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (item, keys counted from the CAD or None, qty if not counted, description,
#  vendor, part number, url, unit price USD, price source, steps, category)
V = "verified 2026-10-18"
# v5: the balance, checked against A&D's HR-i manual (p.59-60) and A&D Japan's DXF on 2026-11-04 (README, "The balance")
HR202I_DESC = ("Analytical balance, 0.1 mg (v7: drawn as a weighing base and a draft cage with nothing tall behind the cage, as Sam "
               "describes the lab's balances; v5's HR-202i chamber, pan and dose height, 200 x 263 x 311 mm, close to the lab's HR-100A's "
               "198 x 253 x 315), RS-232C (2400 7E1): under the station, its pan under the dose point, on the bench (it touches nothing of "
               "the doser). Counted as the lab's, as asked. A new HR-202i (220 g x 0.1 mg) was $2,989 at MNM Scales (out of stock, "
               "2026-11-04; A&D's replacement is the GH-202)")
HR202I_URL = "https://www.aandd.co.jp/products/weighing/balance/bal-analytical/hr/"
HR202I_USD = 0.0
HR202I_SRC = "the lab's (assumed); new: $2,989 at MNM Scales, discontinued"
V29 = "estimate (v3 part, McMaster lookup pending)"
V27 = "verified 2026-10-27"
V16 = "verified 2026-10-16 (paternoster BoM)"
V13 = "verified 2026-10-13"
V10 = "verified 2026-10-10 (v1 BoM)"
E = "estimate, not verified"
SC = "https://www.surpluscenter.com"
MC = "https://www.mcmaster.com"
NITRO_A1 = "https://www.nitrochain.com/35-a1-standard-attachment-connecting-link"

ITEMS = [
    # ---- chain & sprockets
    (1, None, 1, "ANSI #35 roller chain, 10 ft roll (320 pitches): two 104-link loops + the 46-link drive chain (v8: 2 more links, the "
     "NEMA 34 moved 35 mm toward +y)",
     "Nitro Chain", "RC35-1R-10FT", "https://www.nitrochain.com/35-roller-chain-10ft", 23.53, V13, (6, 7), "Chain"),
    (2, ("chain_a1",), None, "#35 A-1 attachment connecting link, spring clip, 0.133 in hole (M3): 13 per chain",
     "Nitro Chain", "CL35-A1", NITRO_A1, 2.55, V13, (7,), "Chain"),
    (3, None, 1, "Spring clips for #35 connecting links, pack of 5 (spares)", "McMaster-Carr", "5501N12", f"{MC}/5501N12/", 4.60, V16, (7,), "Chain"),
    (4, None, 1, "Roller chain breaker, #25-#60 (Dura-Roll #1)", "Surplus Center", "100115",
     "https://surpluscenter.com/1-roller-chain-breaker-for-25-60-pitch/", 17.20, V13, (6, 7), "Tools"),
    (5, ("sprocket_32",), None, "Sprocket 35BS32-5/8: 32T, type B, 2 in hub, 7/8 in through the bore, 5/8 in bore, 3/16 in keyway, 2 set screws",
     "Surplus Center", "601139", f"{SC}/32t-5-8-bore-35p-sprocket/", 21.55, V16, (5,), "Chain"),
    (6, ("sprocket_15_shaft",), None, "Sprocket 35BS15H-5/8: 15T, 5/8 in bore (drive chain, on the B+ shaft's stub)",
     "Surplus Center", "601078", f"{SC}/15t-5-8-bore-35p-sprocket/", 6.65, V13, (6,), "Chain"),
    (7, ("sprocket_15_motor",), None, "Sprocket 35BS15H-1/2: 15T, 1/2 in bore; shop re-bores it to 14 mm H7 with a 5 mm keyway for the NEMA 34",
     "Surplus Center", "601077", f"{SC}/15t-1-2-bore-35p-sprocket/", 6.65, V13, (6,), "Chain"),
    # ---- shafts & bearings
    (8, None, 1, "Keyed shafting, 5/8 in x 72 in, 1018, 3/16 in keyway: cut 3 x 409.8 mm + 1 x 434.2 mm (the drive shaft); lengths from "
     "the CAD after the flange bearing's real 16.05 mm stand-off (was 403 / 427)",
     "Surplus Center", "601881", f"{SC}/5-8-x-72-keyed-shafting-3-16-wide-keyway/", 43.90, V16, (5,), "Shafts"),
    (9, ("flange_bearing",), None, "2-bolt stamped-steel flange bearing SBSFL202-10: 5/8 in bore, set screws, 2-1/2 in bolt centres",
     "Surplus Center", "600174", f"{SC}/5-8-2-bolt-stamped-steel-flange-bearing/", 11.30, V16, (4,), "Shafts"),
    (10, None, 1, "Key stock 3/16 x 3/16 in, 12 in (front sprockets and the 15T on the shaft; back sprockets locked by set screws after phasing)",
     "Surplus Center", "G&G 407-0300", "https://surpluscenter.com/3-16-square-key-stock-12-length-g-g-mfg-407-", 2.80, V16, (5, 6), "Shafts"),
    (11, ("bolt_m6x25",), None, "Hex bolt 1/4-20 x 1 in, Grade 5 (flange bearings to the side plates)", "PaulB Hardware", "H5C14X1",
     "https://paulbhardware.com/hex-cap-screw-1-4-20x1-gr5-zinc-h5c14x1", 0.15, V16, (4,), "Shafts"),
    (12, None, 1, "1/4-20 nylon-insert locknuts, pack of 100 (16 used on the bearings)", "McMaster-Carr", "95615A120", f"{MC}/95615A120/",
     7.46, V16, (4,), "Shafts"),
    # ---- drive
    (13, ("nema34",), None, "NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 14 mm x 37 mm keyed shaft",
     "StepperOnline", "34HS59-6004D-E1000",
     "https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000",
     0.0, "already bought by UofU", (6,), "Drive"),
    (14, ("cl86t",), None, "Closed-loop stepper driver CL86T V4.1 (lab has one from the UofU order)", "StepperOnline (OzRobotics)", "CL86T",
     "https://ozrobotics.com/shop/closed-loop-stepper-driver-v4-1-08-2a-2480vdc-for-nema-34-stepper-motor/", 0.0,
     "in the lab (47.43 new, verified 2026-10-16)", (11,), "Drive"),
    (15, ("lrs350",), None, "Power supply Mean Well LRS-350-48 (48 V, 7.3 A)", "TRC Electronics", "LRS-350-48",
     "https://www.trcelectronics.com/products/mean-well-lrs-350-48", 36.11, V16, (11,), "Drive"),
    (16, None, 1, "M5 x 25 socket head screw, 18-8, pack of 50 (4 used: motor flange to the back plate, in slots)", "McMaster-Carr", "91292A129",
     f"{MC}/91292A129/", 10.96, "verified 2026-10-27 (McMaster page, logged out)", (6,), "Drive"),
    (17, None, 1, "M5 nylon-insert locknut, 18-8, pack of 100 (8 used: 4 on the motor, 4 trapped in the tensioner blocks as jack-screw nuts)",
     "McMaster-Carr", "93625A200", f"{MC}/93625A200/", 9.02, "verified 2026-10-27 (McMaster page, logged out)", (4, 6), "Drive"),
    # ---- frame
    (18, None, 2, "2020 T-slot extrusion, 10 x 1000 mm pack. v8: 4 posts of 692 mm (v7: 796; the carousel is 104 mm lower), 4 long rails of 417.7 mm (2 per bar), 4 rungs of "
     "377.7 mm (2 per bar), and 3 cross rails plus v7's 2 cross bars of 340 mm (2 per bar; 3 x 340 is 1020): eleven bars, so a "
     "second pack (or any single 2020 x 1000 mm bar) for the 11th; 9 spare",
     "VEVOR", "2020OBLXC10JMQNSK001V0",
     "https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492",
     66.90, f"{V13}; the page shows both in and out of stock", (1, 2, 8), "Frame"),
    (19, ("corner_bracket",), 2, "2020 90-degree corner bracket (+2 spare)", "West3D", "NA0394",
     "https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds", 1.59, V13, (1, 2, 8), "Frame"),
    (20, None, 70, "M5 x 10 button head screw, with blue threadlocker (T-nuts can't take a nylock). v7: 32 corner brackets x 2, the P16's "
     "clevis to its cross bar (2), spares", "BelMetric",
     "M5 x 10 BHCS", "https://www.belmetric.com/", 0.12, V16, (1, 2, 8), "Frame"),
    (21, ("tnut_m5",), 70, "M5 drop-in T-nut, 2020 slot 6 (side plates and feet, counted; v7: + 64 for the 32 corner brackets, 4 for the "
     "guides and 2 for the P16's clevis on the cross bars)", "West3D", "WES5240M5",
     "https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads", 0.17, V13, (1, 2, 3, 8), "Frame"),
    (22, ("foot",), None, "Leveling foot, M6 x 40 stud, into a T-nut in the base rail", "TNUTZ", "LF-020-A", "https://www.tnutz.com/product/lf-020-a/",
     1.85, V16, (1,), "Frame"),
    (23, ("side_plate_front", "side_plate_back"), None,
     "Side plates, 1/4 in 6061: front 380 x 375 mm, back 380 x 485 mm (v4's frame is 136 mm wider than v3's), both from one 24 x 36 in "
     "plate; cut and drilled from dxf/ (BYU shop, or SendCutSend: price on upload)", "FixSupply (thyssenkrupp)", "SHT-6061-0.25X24-36",
     "https://fixsupply.com/", 210.0 / 2, "estimate (v3's 12 x 36 in plate was $104.89; twice the area)", (3,), "Frame"),
    (24, None, 1, "M5 x 12 button head screw, 18-8, pack of 50 (v7: 26 used: side plates to the posts' T-nuts 20, the latch cam 2, the "
     "guides into the guide cross bar 4), with blue threadlocker",
     "McMaster-Carr", "92095A210", f"{MC}/92095A210/", 10.91, "verified 2026-10-27 (McMaster page, logged out)", (3,), "Frame"),
    (25, None, 1, "Loctite 243 (blue, medium strength) for T-nut screws, set screws and the tensioner blocks' screws; Loctite 222 "
     "(purple, low strength) where a part is meant to come apart", "McMaster-Carr", "Loctite 243", f"{MC}/loctite/", 27.25, V16, (1,), "Frame"),
    # ---- fasteners
    (26, None, 1, "M3 x 12 button head screw, 18-8, pack of 100 (26 used: carriage to each A-1 tab, from the outside)", "McMaster-Carr",
     "92095A183", f"{MC}/92095A183/", 8.17, "verified 2026-10-27 (McMaster page, logged out)", (10,), "Fasteners"),
    (27, None, 1, "M3 nylon-insert locknut, 18-8, pack of 100 (one in each carriage hook; the P16 base pin)", "McMaster-Carr",
     "93625A100", f"{MC}/93625A100/", 6.94, "verified 2026-10-27 (McMaster page, logged out)", (9, 10), "Fasteners"),
    (28, ("clevis_pin",), 4, "Clevis pin 5 mm with a DIN 6799-4 groove (4 mm dia, 0.74 wide), steel, about 14 mm usable length (module hinge "
     "pins, 2 per module; 4 spare)", "McMaster-Carr", "clevis pins, metric", f"{MC}/clevis-pins/", 0.65, E, (9,), "Fasteners"),
    (29, None, 1, "E-clip DIN 6799-4 (5-7 mm shaft, 4 mm groove x 0.74), spring steel, 8.85 OD, 0.7 thick, pack of 100 (26 used on the hinge "
     "pins)", "McMaster-Carr", "98543A112", f"{MC}/98543A112/", 4.25, "verified 2026-10-27 (McMaster page, logged out)", (9,), "Fasteners"),
    (32, None, 1, "M5 x 16 socket head screw, 18-8, pack of 100 (8 used: hold-downs and side tabs, through the side plates), with blue threadlocker",
     "McMaster-Carr", "91292A126", f"{MC}/91292A126/", 16.05, "verified 2026-10-27 (McMaster page, logged out)", (8,), "Fasteners"),
    (33, None, 1, "M5 brass heat-set insert, 5.7 mm long, 6.4 mm hole, pack of 25 (hold-downs and side tabs)", "McMaster-Carr", "94459A774", f"{MC}/94459A774/",
     7.27, "verified 2026-10-27 (McMaster page, logged out)", (8,), "Fasteners"),
    (34, None, 1, "M5 x 10 socket head screw, 18-8, pack of 100 (8 used: tensioner blocks, into tapped holes in the plates)", "McMaster-Carr",
     "91292A124", f"{MC}/91292A124/", 13.07, "verified 2026-10-27 (McMaster page, logged out)", (4,), "Fasteners"),
    (35, ("m5x30_shcs",), None, "M5 x 30 socket head screw (tensioner jack screws)", "BelMetric", "M5 x 30 SHCS", "https://www.belmetric.com/",
     0.25, E, (4,), "Fasteners"),
    # ---- printed parts
    (36, ("carriage",), None, "Carriage v4, PETG: 66 mm wide, the module on its outer face: a 51.6 mm opening from in front of the hinge to "
     "past the cap (the module swings up through it into the loop to dose), the hinge lugs and the latch housing on the outer face; one per "
     "H2D plate on the bed's diagonal; break-off webs under the hooks' fingers", "printed", "stl/carriage.stl", "", 1.20,
     "filament at $20/kg (about 60 g)", (10,), "Printed"),
    (37, ("hold_down", "tensioner_block"), None, "Hold-downs (2) and tensioner blocks (4), PETG", "printed", "stl/hold_down.stl, stl/tensioner_block.stl",
     "", 0.16, "filament (46.5 g for all six, sliced)", (4, 8), "Printed"),
    (38, ("clevis_bracket", "guide7_cone", "guide7_vee", "beaker_riser", "latch_rail", "side_tab", "side_tab_m", "catch"), None,
     "Station and enclosure parts, PETG. v8: the P16's base clevis (v4's, on the P16 cross bar), 2 guides with v6's funnel mouths and a "
     "cone or vee seat round the EC's back shoes (their feet reach back to the guide cross bar at x 205), the beaker riser v8 (its cup "
     "on a 38 mm arm, under the exit), the latch cam with its arm to the back side plate, 2 side tabs, 1 turn button (no front hatch)",
     "printed", "stl/", "", 0.6, "filament", (8, 12), "Printed"),
    (39, ("sam_mounting_plate",), None, "Mounting plate v8: v7's (Sam's Oct 13 plate carried on to the cap's end: clip 2, cap saddle, the "
     "latch keeper, the door housing's inserts; three 8 x 8 mm dock posts reaching past the auger, printed domes on A and B, a flat "
     "tip on C, a D42-N52 dropped into each at a print pause) with the posts moved behind the gear (x 104, 104 and 128: over EC v8) "
     "and a guide lug for the door bar (x 46-52 beside the tube). Print all 13 flat, posts and lug up", "printed",
     "Onshape 581956d5 + parts8.plate_additions_v8",
     "https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f",
     1.10, "filament at $20/kg (about 55 g: v6's 48 g + the three posts)", (9,), "Printed"),
    # ---- station
    (40, ("actuator_body",), None, "Actuonix P16-150-22-12-P linear actuator: 150 mm stroke, potentiometer feedback, 46 mm/s, 50 N, 10 N side "
     "load, 197 mm closed hole to hole, 20 % duty cycle (datasheet rev B; modelled from Actuonix's STEP). v8: the only actuator, under "
     "the station: pinned to a printed clevis on the P16 cross bar behind the balance (95 mm off the bench; it leans 32 deg back) and "
     "to the clevis under EC v8's solenoid cradle. Extending lifts the EC 10 mm out of its guides onto the dock (9.4 mm of stroke), "
     "then turns the docked EC and module 0-90 deg (126 mm at 90 deg, 24 mm spare)",
     "Actuonix", "P16-150-22-12-P", "https://www.actuonix.com/p16-150-22-12-p", 90.0, V27, (8,), "Station"),
    (41, None, 1, "Actuonix LAC linear actuator control board (closed-loop position from the pot; USB, RC, PWM or 0-3.3 V in). v7: one, "
     "for the one P16 (v6: three)", "Actuonix", "LAC",
     "https://www.actuonix.com/lac", 30.0, V16, (8,), "Station"),

    (42, None, 1, "12 V supply for the LAC and actuator", "Actuonix", "12V PSU", "https://www.actuonix.com/lac", 10.0, V16, (8,), "Station"),
    (43, ("clevis_screw",), None, "Shoulder screw, 18-8, 4 mm x 16 mm shoulder, M3 x 5 thread: the P16's base pin (cheek, 8 mm rear tab, "
     "cheek) + an M3 nylock from item 27. v7: one (v6: six, for three P16s)", "McMaster-Carr", "90265A123",
     f"{MC}/90265A123/", 4.40, V27, (8,), "Station"),
    (101, ("ec_pin_screw",), None, "Shoulder screw, 18-8, 4 mm x 20 mm shoulder, M3 thread: v8: the P16's rod-end pin through the EC "
     "cradle's two cheeks (19.6 mm over them), the rod end's 6 mm tab and a PTFE washer each side, in the cheeks' 2 mm lost-motion "
     "slots; an M3 nylock from item 27. Same family as item 43 (the 4 x 20 length not looked up)", "McMaster-Carr", "90265A123 family",
     f"{MC}/90265A123/", 4.40, "estimate (the 4 x 16's price, verified 2026-10-27)", (8,), "Station"),
    (102, None, 1, "PTFE washer for M4, 4.3 x 9 x 0.8 mm, pack of 50: v7: 2 used, either side of the P16's rod-end tab in the EC's "
     "clevis", "McMaster-Carr", "95630A630", f"{MC}/95630A630/", 9.99, "verified 2026-10-27 (paternoster BoM, McMaster page, logged out)",
     (8,), "Station"),
    # ---- station: gear-mesh preload and the carriage's pivot at its COM height (cad/gear-mesh), as the paternoster's BoM
    (66, ("pinion",), None, "Steel spur gear KHK SS1-20A: module 1, 20T, 20 deg, 5 mm H8 bore, 10 mm face (S45C). Face the 10 mm hub off and bond "
     "it to the NEMA 11's shaft with Loctite 638; replaces the printed 20T. KHK USA lists it at $14.77 (10 on hand), plus shipping", "KHK USA",
     "SS1-20A", "https://catalog.khkgears.us/item/spur-gears/spur-gears-ss/ss1-20a", 14.77, "KHK USA catalog, read 2026-10-27 (cad/shop)",
     (8,), "Station"),
    (72, None, 1, "Dry PTFE lubricant spray (pinion and gear teeth; keeps the separating force near 0.47 x the tangential load)", "McMaster-Carr",
     "dry-film PTFE lubricant", f"{MC}/dry-lubricants/", 12.0, E, (8,), "Station"),
    (73, None, 1, "Stepper driver carrier DRV8825 for the NEMA 11 (current limit set to 450 mA: Vref 0.225 V), 100 uF across VMOT", "Pololu",
     "2133", "https://www.pololu.com/product/2133", 15.95, "estimate (list price in hardware/vibration-motor-and-solenoid.md, not re-checked)",
     (11,), "Electronics"),
    (74, None, 1, "DC motor driver DRV8871 breakout (the 12 V tap solenoid)", "Adafruit", "3190", "https://www.adafruit.com/product/3190", 7.50,
     "estimate (list price in hardware/vibration-motor-and-solenoid.md, not re-checked)", (11,), "Electronics"),
    # ---- v3: kinematic dock and guide (items 1-2 of Sam's 2026-10-29 review)
    (77, ("sam_electronics_carriage",), None, "Electronics carriage v8 (new, on Sam's Aug 27 layout): a flat base, 96 x 50 mm, behind "
     "the balance, with the parts standing on it: the solenoid's cradle just in front of the 44T gear (the solenoid screwed through its "
     "front wall with 2 M3 x 6, plunger up), the motor plate behind the pinion (the NEMA 11 behind the gear, shaft forward: cut its "
     "shaft 4.5 mm), the dock's cone (A), dowel vee (B) and ball C on ears beside the motor with an N52 behind each, the door finger at "
     "the front, the P16's clevis under the cradle and two guide shoes on a neck at the back. Print base down",
     "printed", "stl/electronics_carriage_v8.stl", "", 1.6, "filament (about 80 g, estimated from its 38 cm3)", (8,), "Printed"),
    (78, None, 1, "Precision ball, 1/4 in, hardened 52100 chrome steel (Rockwell C60, ground and polished, diameter +/-0.00005 in; "
     "McMaster gives no ABMA grade), pack of 2: 1 used, ball C on the EC (v6: the plates' two balls are printed domes; v5 bought 18 "
     "packs). The only 1/4 in 52100 ball McMaster lists; its 6 mm 52100 balls are $5.87 per 50 (9292K41) if the seats are "
     "redrawn for 6 mm", "McMaster-Carr", "9528K53", f"{MC}/9528K53/", 6.28, "verified 2026-10-29 (McMaster page, logged out)", (8, 9), "Station"),
    (79, None, 1, "Dowel pin, hardened alloy steel (Rockwell C47 min.), 1/8 x 5/16 in, pack of 100: 6 used (two per vee groove, the "
     "EC's dock vee and the cradle's, 2 spare; v7: 2 used, the EC's vee, no cradle)", "McMaster-Carr", "98381A216", f"{MC}/98381A216/", 16.11, "verified 2026-10-29 (McMaster page, logged out)", (8,), "Station"),
    (80, ("kc_magnet",), None, "Neodymium magnet D44-N52, 1/4 x 1/4 in, axially magnetized, Ni-Cu-Ni: behind the EC's cone, vee and ball C "
     "(no electromagnet in v4) ($0.86 each below 25)", "K&J Magnetics", "D44-N52",
     "https://www.kjmagnetics.com/d44-n52-neodymium-cylinder-magnet", 0.86, "verified 2026-10-29 (K&J page)", (8,), "Station"),
    # ---- v3: outlet doors (item 4) and plate latches (item 4a)
    (83, ("door_housing", "door_shutter"), None, "Outlet door housing and shutter, PETG (one pair per module)", "printed",
     "stl/door_housing.stl, stl/door_shutter.stl", "", 0.10, "filament", (9,), "Printed"),
    (84, None, 15, "Compression spring, 316 stainless, 3 mm OD, 15 mm free, 0.25 mm wire, 0.03 lbf/mm (0.13 N/mm), 7.3 mm long at its "
     "0.2 lb max. load, pack of 1: 15 used (13 doors + 2 spare). Nearest McMaster spring to the 16 mm, 0.06 N/mm drawn, which no "
     "listed spring matches (none reaches the 5.5 mm open length): lengthen the spring pocket 2 mm (13.5 shut, 7.5 open: about "
     "0.2 N shut, 0.9 N open); OD +/-0.4 mm, so a bore of about 3.6 mm", "McMaster-Carr", "8969T21", f"{MC}/8969T21/", 4.88, "verified 2026-10-29 (McMaster page, logged out)", (9,), "Doors"),
    (85, None, 1, "M2 x 8 socket head screw, 18-8, pack of 100 (91292A832, $7.74) + M2 brass heat-set insert, 3.2 mm long for a 3.2 mm "
     "hole, pack of 50 (94459A767, $7.73): 26 of each used (door housing to the plate)", "McMaster-Carr", "91292A832 + 94459A767",
     f"{MC}/91292A832/", 15.47, "verified 2026-10-29 (McMaster page, logged out)", (9,), "Doors"),
    (86, None, 1, "Latch bolt v7: a 4 x 12 mm hardened 52100 dowel (tip at Sam's x 248, 4 mm into the keeper's hole on the plate's back "
     "end, 2 mm into the carrier) pressed into a printed PETG carrier with the rest shelf (stl/latch_bolt.stl), one per carriage. v7: the "
     "carrier is 8 mm long (v6: 12) so the spring has room behind it, and the shelf reaches 7 mm over the keeper (v6: 8): 2.5 mm under it "
     "at the cam's 4.5 mm, clear by 1 mm at the 8 mm hand release. Dowels pack of 50: 13 used; McMaster's 4 mm 91595A family read so "
     "far has 8, 14, 22, 24 and 38 mm, not 12", "McMaster-Carr + printed", "91595A family, 4 x 12",
     f"{MC}/91595A158/", 14.99, "estimate (the 4 x 14 pack's price, 91595A158, verified 2026-10-30; 4 x 12 not looked up)", (10,), "Doors"),
    (87, None, 1, "Dowel pin, hardened 52100 alloy steel, 3 x 25 mm (v6: shorter, its tip clears the NEMA 34 under the bottom run), "
     "pack of 25: 16 used (13 + 3 spare); the 3 x 40 pack (91595A142) is the verified price", "McMaster-Carr", "91595A142 family",
     f"{MC}/91595A142/", 13.92, "estimate (3 x 40 pack price, verified 2026-10-29; 3 x 25 not looked up)", (10,), "Doors"),
    (88, None, 16, "Latch spring. v7: 3 mm OD, about 14 mm free, about 0.3 N/mm, solid under 3.5 mm: 11.5 mm long closed (0.75 N), "
     "7.0 at the cam's 4.5 mm (2.1 N), 3.5 at the 8 mm hand release (3.2 N, 75 % of its free length). TO SELECT: the 3 mm OD "
     "stainless springs read from McMaster so far (8969T21, 8969T261: 15 mm free) stop at 7.3-8.2 mm at their maximum load, so neither "
     "reaches the cam's 7.0; if none does, drop the hand release (the cam alone needs 50 %). 16: 13 + 3 spare",
     "McMaster-Carr", "to select (8969T family)", f"{MC}/compression-springs/", 4.88,
     "estimate (the 8969T family's pack-of-1 price, verified 2026-10-29)", (10,), "Doors"),
    # ---- v3: enclosure (item 5) and side tabs (5a)
    (89, None, 5, "Clear cast acrylic sheet, 1/8 in (-0.025/+0.015 in), 24 x 48 in, scratch and UV resistant: two side panels, front, "
     "back, top and the side hatch door, laser cut from dxf/. v8: the walls are 746 mm tall (104 mm less than v5-v7) and 400-418 mm "
     "wide, so each still takes a sheet's length, and the top and the door a fifth; the front panel is notched round the balance "
     "(225 x 313 mm) and has no hatch door. The balance's dosing lid (item 103) comes from the fifth sheet's offcut", "McMaster-Carr", "8560K262", f"{MC}/8560K262/", 70.99, "verified 2026-10-29 (McMaster page, logged out)",
     (12,), "Enclosure"),
    (103, ("bal7_lid",), None, "Dosing lid for the balance (v8): replaces the draft cage's top door glass: 3 mm cast acrylic (item 89's "
     "offcut), laser cut 162.5 x 181 mm with a 30 mm hole 38 mm behind the pan's centre (under the exit), no collar (v7's 6 mm collar "
     "would meet the passing door bars). The exit stays on the hinge axis, so the stream falls through the same hole at every tilt",
     "laser cut", "", "", 0.25, "estimate (offcut)", (12,), "Enclosure"),
    (90, None, 1, "Nylon spacers for M5, 10 mm OD: 20 x 6 mm (93657A075, $0.89 each at 10 or more; 18 used) and 8 x 25 mm (93657A093, "
     "$1.78 each; 6 used, the back panel past the drive sprocket). The CAD's back standoff is 25.6 mm (this line said 30): 25 mm leaves "
     "2.4 mm to the sprocket's hub instead of 3", "McMaster-Carr", "93657A075 + 93657A093", f"{MC}/93657A075/", 32.04, "verified 2026-10-29 (McMaster page, logged out)", (12,),
     "Enclosure"),
    (91, None, 30, "M5 x 16 button head screw + T-nut (item 21) per standoff (panels to the frame), with blue threadlocker", "BelMetric",
     "M5 x 16 BHCS", "https://www.belmetric.com/", 0.15, E, (12,), "Enclosure"),
    (92, None, 2, "Butt hinge, polished 304 stainless, v8: the side hatch only (no front hatch door), 1-1/2 in tall, 5/8 in leaves (1-1/4 in open), 0.060 in thick, fixed pin, two "
     "countersunk holes per leaf for No. 8 screws (hatch doors) + 16 M4 flat head screws and nylocks (the line had 8 M3): the nearest "
     "McMaster stainless hinge to the 1-1/2 x 1-1/2 in noted", "McMaster-Carr", "1586A22", f"{MC}/1586A22/", 12.29, "verified 2026-10-29 (McMaster page, logged out)", (12,),
     "Enclosure"),
    (93, ("hatch_front", "hatch_side"), None, "Hatch door knob (printed, bonded to the acrylic)", "printed", "", "", 0.05, "filament", (12,),
     "Printed"),
    # ---- v3: the scale (item 6)
    (94, None, 1, HR202I_DESC, "A&D Weighing", "HR-202i", HR202I_URL, HR202I_USD, HR202I_SRC, (12,), "Station"),
    (99, None, 1, "Brush strip with an aluminium holder, nylon bristles about 9 mm, 1 m (v8: three pieces, 313 + 313 + 249 mm, on "
     "the front panel's notch round the balance: its sides and top; the bristles lie on the draft cage's frame and let the side doors' "
     "grips pass)", "McMaster-Carr", "brush strip (to select)", f"{MC}/products/brush-strips/", 24.0, E, (12,), "Enclosure"),
    (95, None, 1, "RS-232 to 3.3 V level shifter (MAX3232 breakout) for the balance's serial port", "SparkFun", "BOB-11189",
     "https://www.sparkfun.com/products/11189", 4.50, E, (11,), "Electronics"),
    (96, None, 1, "Beaker, 25 mL low form, borosilicate (lab stock)", "lab", "", "", 0.0, "existing", (12,), "Station"),
    # ---- sensing & electronics
    (53, ("hall_switch",), None, "Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME", "Adafruit", "158",
     "https://www.adafruit.com/product/158", 2.00, V10, (8,), "Electronics"),
    (54, ("magnet", "kc6_magnet"), None, "Neodymium disc magnet D42-N52, 1/4 x 1/8 in (13 index + 1 home; v7: + 3 in each mounting "
     "plate's dock posts, dropped in at a print pause 1.8 mm under the tips, for the EC's magnets to pull on)", "K&J Magnetics", "D42-N52",
     "https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet", 0.52, V10, (10,), "Electronics"),
    (55, ("raspberry_pi",), None, "Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio)", "Adafruit", "5291",
     "https://www.adafruit.com/product/5291", 15.00, E, (11,), "Electronics"),
    (56, ("perfboard",), None, "Interface board: 74AHCT125 (3.3 V GPIO to 5 V step/dir/enable), 3 x 10k pull-ups, screw terminals, perfboard",
     "Adafruit", "1787", "https://www.adafruit.com/product/1787", 6.0, E, (11,), "Electronics"),
    (57, ("estop",), None, "E-stop GCX1136 (22 mm, NC, twist to release) + enclosure; breaks the 48 V feed to the driver",
     "AutomationDirect", "GCX1136", "https://www.automationdirect.com/pn/GCX1136", 30.0, f"$21 + $9 box; {V10}", (11,), "Electronics"),
    (58, ("board_panel",), None, "Electronics board, 1/4 in plywood 420 x 300", "Home Depot", "", "", 6.0, E, (11,), "Electronics"),
    (59, None, 1, "IEC C14 inlet with switch + fuse drawer (Qualtek 719W-UEL3BR51)", "Digi-Key", "719W-UEL3BR51",
     "https://www.digikey.com/en/products/detail/qualtek/719W-UEL3BR51/23019206", 7.66, V10, (11,), "Electronics"),
    (60, None, 1, "18 AWG stranded hook-up wire, 25 ft (48 V and motor)", "Digi-Key", "18UL1007STRBLA25",
     "https://www.digikey.com/en/products/result?keywords=18UL1007STRBLA25", 14.57, V10, (11,), "Electronics"),
    # ---- modules (exist in the lab)
    (61, ("auger",), None, "Auger, threaded storage (44T gear), and cap, lab design (PR #170): 13 from #134's batch of 16", "lab",
     "reference/auger-*.step", "", 0.0, "existing", (9,), "Module"),
    # ---- test equipment (not in CAD)
    (62, None, 1, "Digital indicator 0-1 in / 0.01 mm with arm and magnetic base (index, lift, sag tests)", "Penn Tool Co",
     "iGaging 35-520", "https://www.penntoolco.com/igaging-digital-indicator-universal-arm-magnetic-base-set-35-520", 119.95, V10,
     (13,), "Test"),
    (63, None, 1, "Digital hanging scale 50 kg (torque lever, push-up and snap forces; a 50 N push-pull gauge is better if the lab has one)",
     "Etekcity", "EL11", "https://etekcity.com/products/luggage-scale-el11", 10.99, V10, (13,), "Test"),
    (64, None, 1, "ADXL343 accelerometer breakout (transit vibration)", "Adafruit", "4097", "https://www.adafruit.com/product/4097",
     5.95, V10, (13,), "Test"),
    (65, None, 3, "Table salt, 26 oz (test fill for the augers)", "grocery", "", "", 1.5, E, (13,), "Test"),
]

# lines you can only buy in packs larger than the rig uses: what you actually pay
BUY = {23: 210.0}

NOTES = """**Before cutting the chain, measure it.** ANSI #35 has a 0.200 in (5.08 mm) bushing and 0.188 in (4.78 mm) between the
inner plates. ISO 06B has the same 3/8 in pitch but a 6.35 mm roller and 5.72 mm between the plates, and the two don't mix.
(ISO 06C *is* ANSI 35.) The 3 ft box already on the ME order is 96 links, 8 short of one v2 loop: keep it as spares.

**A-1 links: Nitro's hole is 0.133 in (M3).** The M3 x 12 screw goes in from the carriage's outer face, through the tab, into
a nylon-insert locknut held in the carriage's printed hook under the tab.

**Sprocket phase.** On each shaft, key the front sprocket and leave the back one's key out. Bolting the carriages across
both chains (step 10) sets the back sprocket's phase. Then lock it with both set screws on the round of the shaft and spot a
dimple under each one (Loctite 243 on every set screw). A 32T tooth is 11.25 deg, so a keyed back sprocket would land up to
4.8 mm out of step.

**Vibration.** Every nut on the machine is a nylon-insert locknut: bearings, motor, carriage tabs, jack screws, actuator pins.
Screws into T-nuts, heat-set inserts and tapped holes get Loctite 243; the hinge pins are retained by e-clips.

**Shop work:** cut and drill the two side plates from `dxf/` (or upload the DXFs to SendCutSend for a quote); re-bore the
motor's 15T sprocket from 1/2 in to 14 mm H7 and broach a 5 mm keyway; tap the eight M5 holes for the tensioner blocks;
face the steel pinion's hub off (KHK SS1-20A); laser cut the acrylic panels. v2's yoke arms and stub pins are gone, and v4
has no armatures (its flat is a washer) and no dock electromagnet. v2's shop animations are in
[../shop/README.md](../shop/README.md).

**Prices** are as listed on the date shown on each line. Every McMaster line was read on McMaster's own page on 2026-10-27,
logged out, through the doser Pi, and is McMaster's pack price; each part's STEP is in the CAD ([../vendor/](../vendor/README.md)).
What is still generic is marked `estimate`."""


def counted() -> Counter:
    import layout
    return Counter(p.key for p in layout.placements())


def rows() -> list[dict]:
    n = counted()
    out = []
    for item, keys, qty, desc, vendor, pn, url, price, pack, steps, cat in ITEMS:
        q = sum(n[k] for k in keys) + (qty or 0) if keys else qty
        ext = BUY.get(item, q * price)
        out.append(dict(item=item, qty=q, description=desc, vendor=vendor, part_number=pn, url=url,
                        unit_usd=round(price, 2), ext_usd=round(ext, 2), pack=pack,
                        steps=",".join(map(str, steps)), category=cat, keys=",".join(keys or ())))
    return out


def totals(rs: list[dict]) -> dict:
    t = sum(r["ext_usd"] for r in rs)
    test = sum(r["ext_usd"] for r in rs if r["category"] == "Test")
    est = sum(r["ext_usd"] for r in rs if r["pack"].startswith("estimate"))
    return dict(total=round(t, 2), without_test=round(t - test, 2), estimated=round(est, 2))


def step_lines() -> dict[int, list[str]]:
    """Per assembly step, the BoM lines it uses (for the step renders)."""
    out: dict[int, list[str]] = {}
    for r in rows():
        for s in map(int, r["steps"].split(",")):
            d = r["description"]
            out.setdefault(s, []).append(f"[{r['item']}] {r['qty']} x {d if len(d) <= 100 else d[:97] + '...'}")
    return out


def write() -> None:
    rs = rows()
    with (HERE / "bom.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0]))
        w.writeheader()
        w.writerows(rs)
    t = totals(rs)
    print(f"{len(rs)} lines, total ${t['total']:.2f} (without test gear ${t['without_test']:.2f}; estimated lines ${t['estimated']:.2f})")


if __name__ == "__main__":
    write()

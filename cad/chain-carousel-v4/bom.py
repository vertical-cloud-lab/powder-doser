"""Bill of materials for the chain-carousel test rig v4 (v3 with the augers outside the loop, Sam's item 7 of 2026-10-29).

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
    (1, None, 1, "ANSI #35 roller chain, 10 ft roll (320 pitches): two 104-link loops + the 44-link drive chain",
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
    (18, None, 1, "2020 T-slot extrusion, 10 x 1000 mm pack: 4 posts of 716 mm (offcuts: the cradle post 224, the station-rails post 255), "
     "4 long rails of 417.7 mm (2 per bar), 4 cross rails and 2 station rails of 340 mm (2 per bar): nine bars",
     "VEVOR", "2020OBLXC10JMQNSK001V0",
     "https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492",
     66.90, f"{V13}; the page shows both in and out of stock", (1, 2, 8), "Frame"),
    (19, ("corner_bracket",), 2, "2020 90-degree corner bracket (+2 at the cradle and latch-rail posts' feet)", "West3D", "NA0394",
     "https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds", 1.59, V13, (1, 2, 8), "Frame"),
    (20, None, 50, "M5 x 10 button head screw, with blue threadlocker (brackets and station parts; T-nuts can't take a nylock)", "BelMetric",
     "M5 x 10 BHCS", "https://www.belmetric.com/", 0.12, V16, (1, 2, 8), "Frame"),
    (21, ("tnut_m5",), 50, "M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet, station)", "West3D", "WES5240M5",
     "https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads", 0.17, V13, (1, 2, 3, 8), "Frame"),
    (22, ("foot",), None, "Leveling foot, M6 x 40 stud, into a T-nut in the base rail", "TNUTZ", "LF-020-A", "https://www.tnutz.com/product/lf-020-a/",
     1.85, V16, (1,), "Frame"),
    (23, ("side_plate_front", "side_plate_back"), None,
     "Side plates, 1/4 in 6061: front 380 x 375 mm, back 380 x 485 mm (v4's frame is 136 mm wider than v3's), both from one 24 x 36 in "
     "plate; cut and drilled from dxf/ (BYU shop, or SendCutSend: price on upload)", "FixSupply (thyssenkrupp)", "SHT-6061-0.25X24-36",
     "https://fixsupply.com/", 210.0 / 2, "estimate (v3's 12 x 36 in plate was $104.89; twice the area)", (3,), "Frame"),
    (24, None, 1, "M5 x 12 button head screw, 18-8, pack of 50 (20 used: side plates to the posts' T-nuts), with blue threadlocker",
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
    (38, ("clevis_bracket", "cradle", "latch_rail", "side_tab", "side_tab_m", "catch"), None,
     "Station and enclosure parts, PETG: actuator base clevis, guide cradle with its arm, latch rail and tube rest (one part) with their "
     "arm, 2 side tabs, 2 turn buttons",
     "printed", "stl/", "", 0.6, "filament", (8, 12), "Printed"),
    (39, ("sam_mounting_plate",), None, "Mounting plate v4: Sam's Oct 13 plate with two dock-ball pockets and a washer pocket on its auger "
     "side (the dock), the latch keeper with its 4.2 mm pin hole, and the door housing's inserts (stl/mounting_plate_v4.stl): print all 13",
     "printed", "Onshape 581956d5 + parts3.plate_additions",
     "https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f",
     0.48, "filament at $20/kg (Sam's 21.8 g + the keeper)", (9,), "Printed"),
    # ---- station
    (40, ("actuator_body",), None, "Actuonix P16-150-22-12-P linear actuator: 150 mm stroke, potentiometer feedback, 46 mm/s, 50 N, 10 N side "
     "load, 197 mm closed hole to hole, 20 % duty cycle (datasheet rev B; modelled from Actuonix's STEP)",
     "Actuonix", "P16-150-22-12-P", "https://www.actuonix.com/p16-150-22-12-p", 90.0, V27, (8,), "Station"),
    (41, None, 1, "Actuonix LAC linear actuator control board (closed-loop position from the pot; USB, RC, PWM or 0-3.3 V in)", "Actuonix", "LAC",
     "https://www.actuonix.com/lac", 30.0, V16, (8,), "Station"),
    (42, None, 1, "12 V supply for the LAC and actuator", "Actuonix", "12V PSU", "https://www.actuonix.com/lac", 10.0, V16, (8,), "Station"),
    (43, ("clevis_screw",), None, "Shoulder screw, 18-8, 4 mm x 16 mm shoulder, M3 x 5 thread: the P16's base pin (cheek, 8 mm rear tab, "
     "cheek) and the EC's clevis pin (cheek, rod-end tab, cheek, in 2 mm slots) + an M3 nylock each from item 27", "McMaster-Carr", "90265A123",
     f"{MC}/90265A123/", 4.40, V27, (8,), "Station"),
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
    (77, ("sam_electronics_carriage",), None, "Electronics carriage v4: Sam's Oct 13 carriage printed upside down (mirrored), with two arms "
     "that reach round the auger to the plate's auger side (the cone and ball C on one, the dowel vee on the other, an N52 behind each), "
     "the base (three seat balls) and the slotted clevis (stl/electronics_carriage_v4.stl); the doser's NEMA 11 and 12 V solenoid move into it",
     "printed", "stl/electronics_carriage_v4.stl", "", 1.15, "filament (about 58 g)", (8,), "Printed"),
    (78, ("kc_ball",), 6, "Precision ball, 1/4 in, hardened 52100 chrome steel, grade 25: 2 per mounting plate (the dock), 4 on the EC (the flat "
     "and the parking seat), 6 spare", "McMaster-Carr", "1/4 in 52100 ball", f"{MC}/precision-balls/", 0.30, "estimate (v3 part, McMaster lookup pending)", (8, 9), "Station"),
    (79, ("vee_dowel",), 2, "Dowel pin, hardened steel, 1/8 x 5/16 in: two per vee groove (the EC's dock vee and the cradle's), 2 spare",
     "McMaster-Carr", "1/8 x 5/16 dowel", f"{MC}/dowel-pins/", 0.25, "estimate (v3 part, McMaster lookup pending)", (8,), "Station"),
    (80, ("kc_magnet",), None, "Neodymium magnet D44-N52, 1/4 x 1/4 in: behind the EC's cone, vee and ball C (no electromagnet in v4)",
     "K&J Magnetics", "D44-N52", "https://www.kjmagnetics.com/d44-n52-neodymium-cylinder-magnet", 1.10, "estimate (v3 part, McMaster lookup pending)", (8,), "Station"),
    (81, ("flat_pad",), None, "Steel flat washer, M4, case-hardened if available, bonded in the cradle floor (the parking seat's flat)",
     "McMaster-Carr", "M4 washer", f"{MC}/washers/", 0.20, "estimate (v3 part, McMaster lookup pending)", (8,), "Station"),
    (97, ("flat_pad_v4",), 2, "Steel flat washer, M5 (10 mm OD, 1 mm), case-hardened, bonded flush in each plate's auger-side face at C: the "
     "dock's flat", "McMaster-Carr", "M5 washer", f"{MC}/washers/", 0.20, "estimate (v4 part)", (9,), "Station"),
    # ---- v3: outlet doors (item 4) and plate latches (item 4a)
    (83, ("door_housing", "door_shutter"), None, "Outlet door housing and shutter, PETG (one pair per module)", "printed",
     "stl/door_housing.stl, stl/door_shutter.stl", "", 0.10, "filament", (9,), "Printed"),
    (84, ("door_spring",), 3, "Compression spring, stainless, 3 mm OD, about 16 mm free, about 0.06 N/mm (door: 0.18 N shut, 0.69 N open)",
     "McMaster-Carr", "3 mm OD compression spring", f"{MC}/compression-springs/", 0.80, "estimate (v3 part, McMaster lookup pending)", (9,), "Doors"),
    (85, ("m2x8_shcs",), 4, "M2 x 8 socket head screw, 18-8 (door housing to the plate) + M2 brass heat-set insert in the plate", "McMaster-Carr",
     "M2 x 8 SHCS + M2 insert", f"{MC}/", 0.25, "estimate (v3 part, McMaster lookup pending)", (9,), "Doors"),
    (86, ("latch_bolt",), None, "Latch bolt v4: a printed PETG carrier (stl/latch_bolt.stl) with a 4 x 24 mm hardened dowel pressed in, "
     "its tip 4 mm into the keeper's hole (one per carriage)", "McMaster-Carr + printed", "4 x 24 dowel", f"{MC}/dowel-pins/", 0.40,
     "estimate (v4 part)", (10,), "Doors"),
    (87, ("latch_follower",), 3, "Dowel pin, hardened steel, 3 x 40 mm: the latch bolt's follower (out past the auger to the station's rail)", "McMaster-Carr", "3 x 20 dowel",
     f"{MC}/dowel-pins/", 0.30, "estimate (v3 part, McMaster lookup pending)", (10,), "Doors"),
    (88, ("latch_spring",), 3, "Compression spring, stainless, 3 mm OD, about 12.7 mm free, about 0.25 N/mm (latch: 0.7 N home, 1.8 N open)",
     "McMaster-Carr", "3 mm OD compression spring", f"{MC}/compression-springs/", 0.80, "estimate (v3 part, McMaster lookup pending)", (10,), "Doors"),
    # ---- v3: enclosure (item 5) and side tabs (5a)
    (89, None, 2, "Clear cast acrylic sheet, 1/8 in, 24 x 48 in: two side panels, front, back, top and the two hatch doors (1.25 m^2), "
     "laser cut from dxf/", "McMaster-Carr", "1/8 in clear cast acrylic 24 x 48", f"{MC}/acrylic/", 75.0, "estimate (v3 part, McMaster lookup pending)", (12,), "Enclosure"),
    (90, ("standoff", "standoff_back"), 4, "Nylon spacer for M5: 10 mm OD x 6 mm (24) and x 30 mm (6, the back panel, past the drive sprocket)",
     "McMaster-Carr", "M5 nylon spacers", f"{MC}/spacers/", 0.35, "estimate (v3 part, McMaster lookup pending)", (12,), "Enclosure"),
    (91, None, 30, "M5 x 16 button head screw + T-nut (item 21) per standoff (panels to the frame), with blue threadlocker", "BelMetric",
     "M5 x 16 BHCS", "https://www.belmetric.com/", 0.15, E, (12,), "Enclosure"),
    (92, None, 4, "Stainless butt hinge, 1-1/2 x 1-1/2 in (hatch doors) + 8 M3 x 8 screws and nylocks", "McMaster-Carr", "1-1/2 in butt hinge",
     f"{MC}/hinges/", 4.50, "estimate (v3 part, McMaster lookup pending)", (12,), "Enclosure"),
    (93, ("hatch_front", "hatch_side"), None, "Hatch door knob (printed, bonded to the acrylic)", "printed", "", "", 0.05, "filament", (12,),
     "Printed"),
    # ---- v3: the scale (item 6)
    (94, None, 1, "A&D HR-100A analytical balance (102 g x 0.1 mg, RS-232): the lab's, modelled from A&D's manual section 22; v4 can't put it "
     "under the dose point yet (scale_fit)", "lab", "HR-100A", "https://weighing.andonline.com/product/hr-a-series/", 0.0, "existing", (12,),
     "Station"),
    (95, None, 1, "RS-232 to 3.3 V level shifter (MAX3232 breakout) for the HR-100A's serial port", "SparkFun", "BOB-11189",
     "https://www.sparkfun.com/products/11189", 4.50, E, (11,), "Electronics"),
    (96, None, 1, "Beaker, 25 mL low form, borosilicate (lab stock)", "lab", "", "", 0.0, "existing", (12,), "Station"),
    # ---- sensing & electronics
    (53, ("hall_switch",), None, "Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME", "Adafruit", "158",
     "https://www.adafruit.com/product/158", 2.00, V10, (8,), "Electronics"),
    (54, ("magnet",), None, "Neodymium disc magnet D42-N52, 1/4 x 1/8 in (13 index + 1 home)", "K&J Magnetics", "D42-N52",
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

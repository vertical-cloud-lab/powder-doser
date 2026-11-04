# Bill of materials: chain-carousel test rig v4

Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are counted from the CAD (`layout.placements()`). Prices are USD on the date shown on each line and will drift. **Step** is the assembly step that uses the line ([ASSEMBLY.md](ASSEMBLY.md)). `bom.csv` has the same data.

**Total $1,983.89; rig without test gear $1,842.50.** Lines marked estimate add up to $306.45. The NEMA 34, the CL86T, the 13 augers (#134's batch of 16) and the electronics carriage's NEMA 11, solenoid and printed body are already in the lab and count as $0.

| # | Qty | Part | Vendor | Part no. | Unit | Ext. | Step |
|---|---|---|---|---|---|---|---|
| | | **Chain** | | | | | |
| 1 | 1 | [ANSI #35 roller chain, 10 ft roll (320 pitches): two 104-link loops + the 44-link drive chain](https://www.nitrochain.com/35-roller-chain-10ft) (verified 2026-10-13) | Nitro Chain | RC35-1R-10FT | $23.53 | $23.53 | 6,7 |
| 2 | 26 | [#35 A-1 attachment connecting link, spring clip, 0.133 in hole (M3): 13 per chain](https://www.nitrochain.com/35-a1-standard-attachment-connecting-link) (verified 2026-10-13) | Nitro Chain | CL35-A1 | $2.55 | $66.30 | 7 |
| 3 | 1 | [Spring clips for #35 connecting links, pack of 5 (spares)](https://www.mcmaster.com/5501N12/) (verified 2026-10-16 (paternoster BoM)) | McMaster-Carr | 5501N12 | $4.60 | $4.60 | 7 |
| 5 | 8 | [Sprocket 35BS32-5/8: 32T, type B, 2 in hub, 7/8 in through the bore, 5/8 in bore, 3/16 in keyway, 2 set screws](https://www.surpluscenter.com/32t-5-8-bore-35p-sprocket/) (verified 2026-10-16 (paternoster BoM)) | Surplus Center | 601139 | $21.55 | $172.40 | 5 |
| 6 | 1 | [Sprocket 35BS15H-5/8: 15T, 5/8 in bore (drive chain, on the B+ shaft's stub)](https://www.surpluscenter.com/15t-5-8-bore-35p-sprocket/) (verified 2026-10-13) | Surplus Center | 601078 | $6.65 | $6.65 | 6 |
| 7 | 1 | [Sprocket 35BS15H-1/2: 15T, 1/2 in bore; shop re-bores it to 14 mm H7 with a 5 mm keyway for the NEMA 34](https://www.surpluscenter.com/15t-1-2-bore-35p-sprocket/) (verified 2026-10-13) | Surplus Center | 601077 | $6.65 | $6.65 | 6 |
| | | **Shafts** | | | | | |
| 8 | 1 | [Keyed shafting, 5/8 in x 72 in, 1018, 3/16 in keyway: cut 3 x 409.8 mm + 1 x 434.2 mm (the drive shaft); lengths from the CAD after the flange bearing's real 16.05 mm stand-off (was 403 / 427)](https://www.surpluscenter.com/5-8-x-72-keyed-shafting-3-16-wide-keyway/) (verified 2026-10-16 (paternoster BoM)) | Surplus Center | 601881 | $43.90 | $43.90 | 5 |
| 9 | 8 | [2-bolt stamped-steel flange bearing SBSFL202-10: 5/8 in bore, set screws, 2-1/2 in bolt centres](https://www.surpluscenter.com/5-8-2-bolt-stamped-steel-flange-bearing/) (verified 2026-10-16 (paternoster BoM)) | Surplus Center | 600174 | $11.30 | $90.40 | 4 |
| 10 | 1 | [Key stock 3/16 x 3/16 in, 12 in (front sprockets and the 15T on the shaft; back sprockets locked by set screws after phasing)](https://surpluscenter.com/3-16-square-key-stock-12-length-g-g-mfg-407-) (verified 2026-10-16 (paternoster BoM)) | Surplus Center | G&G 407-0300 | $2.80 | $2.80 | 5,6 |
| 11 | 16 | [Hex bolt 1/4-20 x 1 in, Grade 5 (flange bearings to the side plates)](https://paulbhardware.com/hex-cap-screw-1-4-20x1-gr5-zinc-h5c14x1) (verified 2026-10-16 (paternoster BoM)) | PaulB Hardware | H5C14X1 | $0.15 | $2.40 | 4 |
| 12 | 1 | [1/4-20 nylon-insert locknuts, pack of 100 (16 used on the bearings)](https://www.mcmaster.com/95615A120/) (verified 2026-10-16 (paternoster BoM)) | McMaster-Carr | 95615A120 | $7.46 | $7.46 | 4 |
| | | **Drive** | | | | | |
| 13 | 1 | [NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 14 mm x 37 mm keyed shaft](https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000) (already bought by UofU) | StepperOnline | 34HS59-6004D-E1000 | $0.00 | $0.00 | 6 |
| 14 | 1 | [Closed-loop stepper driver CL86T V4.1 (lab has one from the UofU order)](https://ozrobotics.com/shop/closed-loop-stepper-driver-v4-1-08-2a-2480vdc-for-nema-34-stepper-motor/) (in the lab (47.43 new, verified 2026-10-16)) | StepperOnline (OzRobotics) | CL86T | $0.00 | $0.00 | 11 |
| 15 | 1 | [Power supply Mean Well LRS-350-48 (48 V, 7.3 A)](https://www.trcelectronics.com/products/mean-well-lrs-350-48) (verified 2026-10-16 (paternoster BoM)) | TRC Electronics | LRS-350-48 | $36.11 | $36.11 | 11 |
| 16 | 1 | [M5 x 25 socket head screw, 18-8, pack of 50 (4 used: motor flange to the back plate, in slots)](https://www.mcmaster.com/91292A129/) (verified 2026-10-27 (McMaster page, logged out)) | McMaster-Carr | 91292A129 | $10.96 | $10.96 | 6 |
| 17 | 1 | [M5 nylon-insert locknut, 18-8, pack of 100 (8 used: 4 on the motor, 4 trapped in the tensioner blocks as jack-screw nuts)](https://www.mcmaster.com/93625A200/) (verified 2026-10-27 (McMaster page, logged out)) | McMaster-Carr | 93625A200 | $9.02 | $9.02 | 4,6 |
| | | **Frame** | | | | | |
| 18 | 1 | [2020 T-slot extrusion, 10 x 1000 mm pack: 4 posts of 716 mm (offcuts: the cradle post 224, the station-rails post 255), 4 long rails of 417.7 mm (2 per bar), 4 cross rails and 2 station rails of 340 mm (2 per bar): nine bars](https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492) (verified 2026-10-13; the page shows both in and out of stock) | VEVOR | 2020OBLXC10JMQNSK001V0 | $66.90 | $66.90 | 1,2,8 |
| 19 | 22 | [2020 90-degree corner bracket (+2 at the cradle and latch-rail posts' feet)](https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds) (verified 2026-10-13) | West3D | NA0394 | $1.59 | $34.98 | 1,2,8 |
| 20 | 50 | [M5 x 10 button head screw, with blue threadlocker (brackets and station parts; T-nuts can't take a nylock)](https://www.belmetric.com/) (verified 2026-10-16 (paternoster BoM)) | BelMetric | M5 x 10 BHCS | $0.12 | $6.00 | 1,2,8 |
| 21 | 74 | [M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet, station)](https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads) (verified 2026-10-13) | West3D | WES5240M5 | $0.17 | $12.58 | 1,2,3,8 |
| 22 | 4 | [Leveling foot, M6 x 40 stud, into a T-nut in the base rail](https://www.tnutz.com/product/lf-020-a/) (verified 2026-10-16 (paternoster BoM)) | TNUTZ | LF-020-A | $1.85 | $7.40 | 1 |
| 23 | 2 | [Side plates, 1/4 in 6061: front 380 x 375 mm, back 380 x 485 mm (v4's frame is 136 mm wider than v3's), both from one 24 x 36 in plate; cut and drilled from dxf/ (BYU shop, or SendCutSend: price on upload)](https://fixsupply.com/) (estimate (v3's 12 x 36 in plate was $104.89; twice the area)) | FixSupply (thyssenkrupp) | SHT-6061-0.25X24-36 | $105.00 | $210.00 | 3 |
| 24 | 1 | [M5 x 12 button head screw, 18-8, pack of 50 (20 used: side plates to the posts' T-nuts), with blue threadlocker](https://www.mcmaster.com/92095A210/) (verified 2026-10-27 (McMaster page, logged out)) | McMaster-Carr | 92095A210 | $10.91 | $10.91 | 3 |
| 25 | 1 | [Loctite 243 (blue, medium strength) for T-nut screws, set screws and the tensioner blocks' screws; Loctite 222 (purple, low strength) where a part is meant to come apart](https://www.mcmaster.com/loctite/) (verified 2026-10-16 (paternoster BoM)) | McMaster-Carr | Loctite 243 | $27.25 | $27.25 | 1 |
| | | **Fasteners** | | | | | |
| 26 | 1 | [M3 x 12 button head screw, 18-8, pack of 100 (26 used: carriage to each A-1 tab, from the outside)](https://www.mcmaster.com/92095A183/) (verified 2026-10-27 (McMaster page, logged out)) | McMaster-Carr | 92095A183 | $8.17 | $8.17 | 10 |
| 27 | 1 | [M3 nylon-insert locknut, 18-8, pack of 100 (one in each carriage hook; the P16 base pin)](https://www.mcmaster.com/93625A100/) (verified 2026-10-27 (McMaster page, logged out)) | McMaster-Carr | 93625A100 | $6.94 | $6.94 | 9,10 |
| 28 | 30 | [Clevis pin 5 mm with a DIN 6799-4 groove (4 mm dia, 0.74 wide), steel, about 14 mm usable length (module hinge pins, 2 per module; 4 spare)](https://www.mcmaster.com/clevis-pins/) (estimate, not verified) | McMaster-Carr | clevis pins, metric | $0.65 | $19.50 | 9 |
| 29 | 1 | [E-clip DIN 6799-4 (5-7 mm shaft, 4 mm groove x 0.74), spring steel, 8.85 OD, 0.7 thick, pack of 100 (26 used on the hinge pins)](https://www.mcmaster.com/98543A112/) (verified 2026-10-27 (McMaster page, logged out)) | McMaster-Carr | 98543A112 | $4.25 | $4.25 | 9 |
| 32 | 1 | [M5 x 16 socket head screw, 18-8, pack of 100 (8 used: hold-downs and side tabs, through the side plates), with blue threadlocker](https://www.mcmaster.com/91292A126/) (verified 2026-10-27 (McMaster page, logged out)) | McMaster-Carr | 91292A126 | $16.05 | $16.05 | 8 |
| 33 | 1 | [M5 brass heat-set insert, 5.7 mm long, 6.4 mm hole, pack of 25 (hold-downs and side tabs)](https://www.mcmaster.com/94459A774/) (verified 2026-10-27 (McMaster page, logged out)) | McMaster-Carr | 94459A774 | $7.27 | $7.27 | 8 |
| 34 | 1 | [M5 x 10 socket head screw, 18-8, pack of 100 (8 used: tensioner blocks, into tapped holes in the plates)](https://www.mcmaster.com/91292A124/) (verified 2026-10-27 (McMaster page, logged out)) | McMaster-Carr | 91292A124 | $13.07 | $13.07 | 4 |
| 35 | 4 | [M5 x 30 socket head screw (tensioner jack screws)](https://www.belmetric.com/) (estimate, not verified) | BelMetric | M5 x 30 SHCS | $0.25 | $1.00 | 4 |
| | | **Printed** | | | | | |
| 36 | 13 | Carriage v4, PETG: 66 mm wide, the module on its outer face: a 51.6 mm opening from in front of the hinge to past the cap (the module swings up through it into the loop to dose), the hinge lugs and the latch housing on the outer face; one per H2D plate on the bed's diagonal; break-off webs under the hooks' fingers (filament at $20/kg (about 60 g)) | printed | stl/carriage.stl | $1.20 | $15.60 | 10 |
| 37 | 6 | Hold-downs (2) and tensioner blocks (4), PETG (filament (46.5 g for all six, sliced)) | printed | stl/hold_down.stl, stl/tensioner_block.stl | $0.16 | $0.96 | 4,8 |
| 38 | 7 | Station and enclosure parts, PETG: actuator base clevis, guide cradle with its arm, latch rail and tube rest (one part) with their arm, 2 side tabs, 2 turn buttons (filament) | printed | stl/ | $0.60 | $4.20 | 8,12 |
| 39 | 13 | [Mounting plate v4: Sam's Oct 13 plate with two dock-ball pockets and a washer pocket on its auger side (the dock), the latch keeper with its 4.2 mm pin hole, and the door housing's inserts (stl/mounting_plate_v4.stl): print all 13](https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f) (filament at $20/kg (Sam's 21.8 g + the keeper)) | printed | Onshape 581956d5 + parts3.plate_additions | $0.48 | $6.24 | 9 |
| 77 | 1 | Electronics carriage v4: Sam's Oct 13 carriage printed upside down (mirrored), with two arms that reach round the auger to the plate's auger side (the cone and ball C on one, the dowel vee on the other, an N52 behind each), the base (three seat balls) and the slotted clevis (stl/electronics_carriage_v4.stl); the doser's NEMA 11 and 12 V solenoid move into it (filament (about 58 g)) | printed | stl/electronics_carriage_v4.stl | $1.15 | $1.15 | 8 |
| 83 | 26 | Outlet door housing and shutter, PETG (one pair per module) (filament) | printed | stl/door_housing.stl, stl/door_shutter.stl | $0.10 | $2.60 | 9 |
| 93 | 2 | Hatch door knob (printed, bonded to the acrylic) (filament) | printed |  | $0.05 | $0.10 | 12 |
| | | **Station** | | | | | |
| 40 | 1 | [Actuonix P16-150-22-12-P linear actuator: 150 mm stroke, potentiometer feedback, 46 mm/s, 50 N, 10 N side load, 197 mm closed hole to hole, 20 % duty cycle (datasheet rev B; modelled from Actuonix's STEP)](https://www.actuonix.com/p16-150-22-12-p) (verified 2026-10-27) | Actuonix | P16-150-22-12-P | $90.00 | $90.00 | 8 |
| 41 | 1 | [Actuonix LAC linear actuator control board (closed-loop position from the pot; USB, RC, PWM or 0-3.3 V in)](https://www.actuonix.com/lac) (verified 2026-10-16 (paternoster BoM)) | Actuonix | LAC | $30.00 | $30.00 | 8 |
| 42 | 1 | [12 V supply for the LAC and actuator](https://www.actuonix.com/lac) (verified 2026-10-16 (paternoster BoM)) | Actuonix | 12V PSU | $10.00 | $10.00 | 8 |
| 43 | 2 | [Shoulder screw, 18-8, 4 mm x 16 mm shoulder, M3 x 5 thread: the P16's base pin (cheek, 8 mm rear tab, cheek) and the EC's clevis pin (cheek, rod-end tab, cheek, in 2 mm slots) + an M3 nylock each from item 27](https://www.mcmaster.com/90265A123/) (verified 2026-10-27) | McMaster-Carr | 90265A123 | $4.40 | $8.80 | 8 |
| 66 | 1 | [Steel spur gear KHK SS1-20A: module 1, 20T, 20 deg, 5 mm H8 bore, 10 mm face (S45C). Face the 10 mm hub off and bond it to the NEMA 11's shaft with Loctite 638; replaces the printed 20T. KHK USA lists it at $14.77 (10 on hand), plus shipping](https://catalog.khkgears.us/item/spur-gears/spur-gears-ss/ss1-20a) (KHK USA catalog, read 2026-10-27 (cad/shop)) | KHK USA | SS1-20A | $14.77 | $14.77 | 8 |
| 72 | 1 | [Dry PTFE lubricant spray (pinion and gear teeth; keeps the separating force near 0.47 x the tangential load)](https://www.mcmaster.com/dry-lubricants/) (estimate, not verified) | McMaster-Carr | dry-film PTFE lubricant | $12.00 | $12.00 | 8 |
| 78 | 18 | [Precision ball, 1/4 in, hardened 52100 chrome steel (Rockwell C60, ground and polished, diameter +/-0.00005 in; McMaster gives no ABMA grade), pack of 2: 36 used (2 per mounting plate for the dock, 4 on the EC for the flat and the parking seat, 6 spare). The only 1/4 in 52100 ball McMaster lists; its 6 mm 52100 balls are $5.87 per 50 (9292K41) if the seats are redrawn for 6 mm](https://www.mcmaster.com/9528K53/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 9528K53 | $6.28 | $113.04 | 8,9 |
| 79 | 1 | [Dowel pin, hardened alloy steel (Rockwell C47 min.), 1/8 x 5/16 in, pack of 100: 6 used (two per vee groove, the EC's dock vee and the cradle's, 2 spare)](https://www.mcmaster.com/98381A216/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 98381A216 | $16.11 | $16.11 | 8 |
| 80 | 3 | [Neodymium magnet D44-N52, 1/4 x 1/4 in, axially magnetized, Ni-Cu-Ni: behind the EC's cone, vee and ball C (no electromagnet in v4) ($0.86 each below 25)](https://www.kjmagnetics.com/d44-n52-neodymium-cylinder-magnet) (verified 2026-10-29 (K&J page)) | K&J Magnetics | D44-N52 | $0.86 | $2.58 | 8 |
| 81 | 1 | [Steel flat washer, M4, 4.3 x 9 x 0.8 mm (0.7 to 0.9), black super-corrosion-resistant coated steel, Rockwell B75, pack of 10: 1 used, bonded in the cradle floor (the parking seat's flat). Not hardened: McMaster's general-purpose metric washers include no case-hardened steel. The CAD draws an 8 x 1 mm pad, so the pocket needs 9.2 x 0.8](https://www.mcmaster.com/93413A120/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 93413A120 | $9.42 | $9.42 | 8 |
| 94 | 1 | [A&D HR-100A analytical balance (102 g x 0.1 mg, RS-232): the lab's, modelled from A&D's manual section 22; v4 can't put it under the dose point yet (scale_fit)](https://weighing.andonline.com/product/hr-a-series/) (existing) | lab | HR-100A | $0.00 | $0.00 | 12 |
| 96 | 1 | Beaker, 25 mL low form, borosilicate (lab stock) (existing) | lab |  | $0.00 | $0.00 | 12 |
| 97 | 1 | [Steel flat washer, M5, 5.3 x 10 x 1 mm (0.9 to 1.1), zinc-flake coated, Rockwell B91, for class 8.8 screws, pack of 50: 15 used (13 + 2 spare), bonded flush in each plate's auger-side face at C: the dock's flat. Not hardened: McMaster's general-purpose metric washers include no case-hardened steel](https://www.mcmaster.com/91455A420/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 91455A420 | $10.48 | $10.48 | 9 |
| | | **Doors** | | | | | |
| 84 | 15 | [Compression spring, 316 stainless, 3 mm OD, 15 mm free, 0.25 mm wire, 0.03 lbf/mm (0.13 N/mm), 7.3 mm long at its 0.2 lb max. load, pack of 1: 15 used (13 doors + 2 spare). Nearest McMaster spring to the 16 mm, 0.06 N/mm drawn, which no listed spring matches (none reaches the 5.5 mm open length): lengthen the spring pocket 2 mm (13.5 shut, 7.5 open: about 0.2 N shut, 0.9 N open); OD +/-0.4 mm, so a bore of about 3.6 mm](https://www.mcmaster.com/8969T21/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 8969T21 | $4.88 | $73.20 | 9 |
| 85 | 1 | [M2 x 8 socket head screw, 18-8, pack of 100 (91292A832, $7.74) + M2 brass heat-set insert, 3.2 mm long for a 3.2 mm hole, pack of 50 (94459A767, $7.73): 26 of each used (door housing to the plate)](https://www.mcmaster.com/91292A832/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 91292A832 + 94459A767 | $15.47 | $15.47 | 9 |
| 86 | 1 | [Latch bolt v4: a 4 x 14 mm hardened 52100 dowel (tip at Sam's x 102, 4 mm into the keeper's hole) with its tail pressed 6 mm into a printed PETG carrier (stl/latch_bolt.stl, from x 110, about $0.03 of filament each, not priced here), one per carriage; dowels pack of 50: 13 used + 37 spare](https://www.mcmaster.com/91595A158/) (verified 2026-10-30 (McMaster page, logged out)) | McMaster-Carr + printed | 91595A158 | $14.99 | $14.99 | 10 |
| 87 | 1 | [Dowel pin, hardened 52100 alloy steel, 3 x 40 mm, pack of 25: 16 used (the latch bolt's follower, out past the auger to the station's rail; 13 + 3 spare)](https://www.mcmaster.com/91595A142/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 91595A142 | $13.92 | $13.92 | 10 |
| 88 | 16 | [Compression spring, 316 stainless, 3 mm OD, 15 mm free, 0.3 mm wire, 0.06 lbf/mm (0.27 N/mm), 8.2 mm long at its 0.4 lb max. load, pack of 1: 16 used (13 + 3 spare). Nearest McMaster spring to the 4 mm OD x 12.7 mm, 0.25 N/mm drawn (it lists no 4 mm OD metric compression spring, and none reaches the 5.5 mm open length): pocket 3 mm longer (13 home, 8.5 open: about 0.5 N home, 1.75 N open), bore about 3.6 mm (OD +/-0.4 mm)](https://www.mcmaster.com/8969T261/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 8969T261 | $4.88 | $78.08 | 10 |
| | | **Enclosure** | | | | | |
| 89 | 2 | [Clear cast acrylic sheet, 1/8 in (-0.025/+0.015 in), 24 x 48 in, scratch and UV resistant: two side panels, front, back, top and the two hatch doors (1.25 m^2), laser cut from dxf/](https://www.mcmaster.com/8560K262/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 8560K262 | $70.99 | $141.98 | 12 |
| 90 | 1 | [Nylon spacers for M5, 10 mm OD: 20 x 6 mm (93657A075, $0.89 each at 10 or more; 18 used) and 8 x 25 mm (93657A093, $1.78 each; 6 used, the back panel past the drive sprocket). The CAD's back standoff is 25.6 mm (this line said 30): 25 mm leaves 2.4 mm to the sprocket's hub instead of 3](https://www.mcmaster.com/93657A075/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 93657A075 + 93657A093 | $32.04 | $32.04 | 12 |
| 91 | 30 | [M5 x 16 button head screw + T-nut (item 21) per standoff (panels to the frame), with blue threadlocker](https://www.belmetric.com/) (estimate, not verified) | BelMetric | M5 x 16 BHCS | $0.15 | $4.50 | 12 |
| 92 | 4 | [Butt hinge, polished 304 stainless, 1-1/2 in tall, 5/8 in leaves (1-1/4 in open), 0.060 in thick, fixed pin, two countersunk holes per leaf for No. 8 screws (hatch doors) + 16 M4 flat head screws and nylocks (the line had 8 M3): the nearest McMaster stainless hinge to the 1-1/2 x 1-1/2 in noted](https://www.mcmaster.com/1586A22/) (verified 2026-10-29 (McMaster page, logged out)) | McMaster-Carr | 1586A22 | $12.29 | $49.16 | 12 |
| | | **Electronics** | | | | | |
| 53 | 2 | [Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME](https://www.adafruit.com/product/158) (verified 2026-10-10 (v1 BoM)) | Adafruit | 158 | $2.00 | $4.00 | 8 |
| 54 | 14 | [Neodymium disc magnet D42-N52, 1/4 x 1/8 in (13 index + 1 home)](https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet) (verified 2026-10-10 (v1 BoM)) | K&J Magnetics | D42-N52 | $0.52 | $7.28 | 10 |
| 55 | 1 | [Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio)](https://www.adafruit.com/product/5291) (estimate, not verified) | Adafruit | 5291 | $15.00 | $15.00 | 11 |
| 56 | 1 | [Interface board: 74AHCT125 (3.3 V GPIO to 5 V step/dir/enable), 3 x 10k pull-ups, screw terminals, perfboard](https://www.adafruit.com/product/1787) (estimate, not verified) | Adafruit | 1787 | $6.00 | $6.00 | 11 |
| 57 | 1 | [E-stop GCX1136 (22 mm, NC, twist to release) + enclosure; breaks the 48 V feed to the driver](https://www.automationdirect.com/pn/GCX1136) ($21 + $9 box; verified 2026-10-10 (v1 BoM)) | AutomationDirect | GCX1136 | $30.00 | $30.00 | 11 |
| 58 | 1 | Electronics board, 1/4 in plywood 420 x 300 (estimate, not verified) | Home Depot |  | $6.00 | $6.00 | 11 |
| 59 | 1 | [IEC C14 inlet with switch + fuse drawer (Qualtek 719W-UEL3BR51)](https://www.digikey.com/en/products/detail/qualtek/719W-UEL3BR51/23019206) (verified 2026-10-10 (v1 BoM)) | Digi-Key | 719W-UEL3BR51 | $7.66 | $7.66 | 11 |
| 60 | 1 | [18 AWG stranded hook-up wire, 25 ft (48 V and motor)](https://www.digikey.com/en/products/result?keywords=18UL1007STRBLA25) (verified 2026-10-10 (v1 BoM)) | Digi-Key | 18UL1007STRBLA25 | $14.57 | $14.57 | 11 |
| 73 | 1 | [Stepper driver carrier DRV8825 for the NEMA 11 (current limit set to 450 mA: Vref 0.225 V), 100 uF across VMOT](https://www.pololu.com/product/2133) (estimate (list price in hardware/vibration-motor-and-solenoid.md, not re-checked)) | Pololu | 2133 | $15.95 | $15.95 | 11 |
| 74 | 1 | [DC motor driver DRV8871 breakout (the 12 V tap solenoid)](https://www.adafruit.com/product/3190) (estimate (list price in hardware/vibration-motor-and-solenoid.md, not re-checked)) | Adafruit | 3190 | $7.50 | $7.50 | 11 |
| 95 | 1 | [RS-232 to 3.3 V level shifter (MAX3232 breakout) for the HR-100A's serial port](https://www.sparkfun.com/products/11189) (estimate, not verified) | SparkFun | BOB-11189 | $4.50 | $4.50 | 11 |
| | | **Module** | | | | | |
| 61 | 13 | Auger, threaded storage (44T gear), and cap, lab design (PR #170): 13 from #134's batch of 16 (existing) | lab | reference/auger-*.step | $0.00 | $0.00 | 9 |
| | | **Tools** | | | | | |
| 4 | 1 | [Roller chain breaker, #25-#60 (Dura-Roll #1)](https://surpluscenter.com/1-roller-chain-breaker-for-25-60-pitch/) (verified 2026-10-13) | Surplus Center | 100115 | $17.20 | $17.20 | 6,7 |
| | | **Test** | | | | | |
| 62 | 1 | [Digital indicator 0-1 in / 0.01 mm with arm and magnetic base (index, lift, sag tests)](https://www.penntoolco.com/igaging-digital-indicator-universal-arm-magnetic-base-set-35-520) (verified 2026-10-10 (v1 BoM)) | Penn Tool Co | iGaging 35-520 | $119.95 | $119.95 | 13 |
| 63 | 1 | [Digital hanging scale 50 kg (torque lever, push-up and snap forces; a 50 N push-pull gauge is better if the lab has one)](https://etekcity.com/products/luggage-scale-el11) (verified 2026-10-10 (v1 BoM)) | Etekcity | EL11 | $10.99 | $10.99 | 13 |
| 64 | 1 | [ADXL343 accelerometer breakout (transit vibration)](https://www.adafruit.com/product/4097) (verified 2026-10-10 (v1 BoM)) | Adafruit | 4097 | $5.95 | $5.95 | 13 |
| 65 | 3 | Table salt, 26 oz (test fill for the augers) (estimate, not verified) | grocery |  | $1.50 | $4.50 | 13 |

## Notes

**Before cutting the chain, measure it.** ANSI #35 has a 0.200 in (5.08 mm) bushing and 0.188 in (4.78 mm) between the
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
What is still generic is marked `estimate`.

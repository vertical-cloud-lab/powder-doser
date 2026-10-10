# Assembly: chain-carousel test rig v0

Twelve steps in build order, then the test set-up. In each render the parts from earlier steps are pale, and the step's new parts are in colour, lifted along the way they go in. The table under each render is the BoM lines that step uses ([BOM.md](BOM.md) item numbers). The same order is the Onshape assembly's tree (`01 Frame` ... `12 Electronics board`).

Tools: chain breaker (BOM item 3), metric hex keys, 8 mm and 1/2 in wrenches, drill + countersink, 3-1/8 in hole saw, jigsaw, soldering iron, heat-set insert tip, feeler gauges.

## Step 1. Frame: long rails, cross members, corner brackets

![Step 1](renders/steps/step_01.png)

| # | Qty | Part |
|---|---|---|
| 11 | 2 | 2020 T-slot extrusion, 1050 mm (long rails) |
| 12 | 5 | 2020 T-slot extrusion, 690 mm (cross members) |
| 14 | 24 | 2020 corner bracket with M5 screws and T-nuts |

Cut the 2020 to length: 2 x 1050 mm (long rails), 5 x 690 mm (cross members), 4 x 230 mm (legs).
Lay the long rails parallel, 710 mm apart centre to centre. Put the cross members between them at
10, 261.6, 421.6, 805 and 1040 mm from the **drive end** of the rails. The two at 261.6 and 421.6
box in the motor plate. Join every cross member to both rails with a corner bracket in each inside
corner (the end members only get brackets on their inner side): drop-in T-nuts, M5 screws, snug.
Square the frame by its diagonals (equal within 1 mm), then tighten.

## Step 2. Legs and leveling feet

![Step 2](renders/steps/step_02.png)

| # | Qty | Part |
|---|---|---|
| 13 | 4 | 2020 T-slot extrusion, 230 mm (legs) |
| 15 | 4 | Leveling foot, M5 stud (into the leg's centre bore, tapped M5) |

Hang a 230 mm leg under each rail end with two corner brackets: one to the rail's underside, one to
the end cross member's underside. Tap each leg's 4.2 mm centre bore M5 at the bottom and screw in
an M5 leveling foot. Level the frame on the bench.

## Step 3. NEMA 34 on its motor plate

![Step 3](renders/steps/step_03.png)

| # | Qty | Part |
|---|---|---|
| 6 | 1 | NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 14 mm keyed shaft |
| 8 | 1 | Motor plate, 6061 aluminium 1/4 in x 6 in x 6 in, cut to 140 x 140 and drilled (DXF in dxf/) |
| 20 | 4 | M5 x 18 socket head screw (motor flange into the M5-tapped plate) |

Drill the motor plate from [`dxf/motor_plate.dxf`](dxf/motor_plate.dxf): a 73.5 mm pilot bore (hole saw
or the shop's lathe), 4 x M5 tapped holes on the 69.58 mm square for the motor, and 4 x 5.5 mm
corner holes for the deck screws. Bolt the NEMA 34 up against the plate's underside: shaft up,
pilot in the bore, 4 x M5 x 18 into the tapped holes. Check the screws don't stand proud of the
plate's top face.

## Step 4. Deck onto the frame; motor plate up into the deck

![Step 4](renders/steps/step_04.png)

| # | Qty | Part |
|---|---|---|
| 16 | 1 | Deck, HDPE 1/2 in, 48 x 48 in sheet cut to 1050 x 740 (DXF in dxf/) |
| 21 | 4 | M5 x 20 flat head screw + nut (motor plate up into the deck) |
| 22 | 24 | M5 x 25 flat head screw (deck to frame) |
| 23 | 24 | M5 drop-in T-nut, 2020 slot 6 |

Cut the deck from the HDPE sheet to 1050 x 740 mm. Tape the 1:1 print of
[`dxf/deck.dxf`](dxf/deck.dxf) on top and mark it out. Cut the 80 mm drive hole (3-1/8 in hole saw), the idler
slot (32 x 44 mm), the station window and the two 11.8 mm sensor holes. Drill and
**countersink every screw hole so the heads sit 0.3 mm below the surface**: the carriage skids
slide over them. Set the deck on the frame. Screw it down with M5 x 25 flat heads into drop-in
T-nuts in the rails and cross members. Then lift the motor plate into its box under the drive
hole and fix it with 4 x M5 x 20 flat heads from the top, nuts underneath.

## Step 5. Idler: slider, stud, spacer, idler sprocket, tensioner

![Step 5](renders/steps/step_05.png)

| # | Qty | Part |
|---|---|---|
| 5 | 1 | Idler sprocket #35 19T with ball bearing, 1/2 in bore |
| 17 | 1 | Hex bolt 1/2-13 x 2-1/2 in (idler stud) |
| 18 | 1 | Nylon-insert locknut 1/2-13 |
| 19 | 1 | Washer 1/2 in |
| 24 | 1 | M5 x 40 socket head screw + nut (tensioner jack screw) |
| 30 | 3 | Idler slider, spacer and tensioner block, printed PETG |

Idler, from below: put the printed slider under the idler slot with the 1/2-13 stud up through it
and through the slot. Clamp it with the two M5 screws through the deck (finger-tight for now).
From above: the printed spacer (it puts the idler's tooth ring at the chain's centre plane,
5.4 mm above the deck), the idler sprocket, a washer and the nylon locknut, snug (the
bearing turns, not the stud). Screw the tensioner block to the deck between the sprockets. Thread
the M5 x 40 jack screw through it until it touches the slider; the slider has 12 mm
of travel.

## Step 6. Drive sprocket on the motor shaft

![Step 6](renders/steps/step_06.png)

| # | Qty | Part |
|---|---|---|
| 4 | 1 | Sprocket 35B19, 19T ANSI 35, B hub, bored 14 mm H7 + 5 mm keyway (NEMA 34 shaft) |
| 7 | 1 | Key 5 x 5 x 25 mm (ships with the motor) |

Have the 35B19 bored to 14 mm H7 with a 5 mm keyway (BYU machine shop; or order it finished,
BOM item 4). Put the key in the motor shaft and slide the sprocket on **hub down**, into the deck
hole. Set the tooth ring's mid-plane 5.4 mm above the deck: rest a 3.3 mm shim under the
tooth ring, tighten both set screws (one on the key), and remove the shim.

## Step 7. Hall sensors (index, home) into the deck

![Step 7](renders/steps/step_07.png)

| # | Qty | Part |
|---|---|---|
| 32 | 2 | Hall sensor holder, printed PETG |
| 33 | 2 | A3144 hall-effect switch (open collector), index + home |

Solder 30 cm leads to the two A3144s. Push each into its printed holder, face up, and press the
holders into the sensor holes from below so the sensor face sits 0.8 mm under the deck surface.
The one on the drive side (+X in the carriage frame) is INDEX; the other is HOME.

## Step 8. Chain: 12 A-1 attachment links every 8 pitches, close the loop, tension

![Step 8](renders/steps/step_08.png)

| # | Qty | Part |
|---|---|---|
| 1 | 1 | ANSI #35 roller chain, 3 ft (96 pitches) + 2 connecting links |
| 2 | 12 | #35 A-1 attachment connecting link (bent tab, 1 hole), replaces 12 riveted outer links |
| 3 | 1 | #35 chain breaker / pin press (removes the 11 outer links the A-1 links replace) |

Lay the chain round both sprockets to check the length (96 pitches, both spans tight with the
idler slid fully in). With the chain breaker, take out **11 riveted outer links, one every 8
pitches**, and fit an A-1 attachment connecting link in each gap, **tab up and on the outside of
the loop**. Close the loop with the 12th A-1 link. Every spring clip's closed end points the way
the chain travels (counter-clockwise from above). Back the jack screw out until the mid-span
deflection is 3-4 mm under a 5 N side push (TEST-PLAN T1), then tighten the slider clamps.

## Step 9. Carriages: inserts and magnets, then bolt each to its A-1 tab

![Step 9](renders/steps/step_09.png)

| # | Qty | Part |
|---|---|---|
| 25 | 12 | M3 x 10 button head screw (carriage to A-1 tab) |
| 26 | 12 | M3 heat-set insert, 5.7 mm long |
| 29 | 12 | Carriage base plate, printed PETG (H2D bed; ~125 g each) |
| 34 | 13 | Neodymium disc magnet 6 x 3 mm N52 (12 index + 1 home) |

Print 12 carriages in PETG on the H2D (skids down, 0.2 mm layers, 4 walls, 30% gyroid; about
125 g each). Melt an M3 heat-set insert into each inner wall. Glue a 6 x 3 mm magnet, **south
pole down**, into the +X pocket under the inner skid of every carriage (INDEX). On carriage 1
only, glue a second one into the -X pocket (HOME). Mark carriage numbers on the ribs. Stand each
carriage on the deck against its A-1 tab and screw it on from the chain side with an M3 x 10
button head. Carriage 1 goes on the A-1 link that sits over the sensors when the chain is at
home.

## Step 10. Station hold-down blocks

![Step 10](renders/steps/step_10.png)

| # | Qty | Part |
|---|---|---|
| 27 | 4 | M4 x 30 socket head screw + nylon locknut (hold-down blocks) |
| 31 | 2 | Hold-down block, printed PETG |

Bolt the two hold-down blocks to the deck at the station's front edge (M4 x 30, nylon locknuts
under the deck). Slide carriage 1 under them by hand and shim each lip to 0.5 mm above the tongue
with a feeler gauge before tightening. Check that every carriage's tongue enters under the lips
without catching when it indexes in.

## Step 11. Module 1: Sam's mounting plate, auger and cap on carriage 1

![Step 11](renders/steps/step_11.png)

| # | Qty | Part |
|---|---|---|
| 28 | 1 | M5 x 70 socket head screw + nylon locknut (hinge pin) |
| 40 | 1 | Mounting plate (Sam's Oct 8 Onshape design), printed |
| 41 | 2 | Auger, threaded storage, and cap (lab design, PR #170) |

Module 1 is the existing hardware: Sam's Oct 8 mounting plate holding the lab auger (threaded
storage + cap). Put the plate between carriage 1's lugs, hinge end outward, and push the M5 x 70
hinge pin through lug, plate, lug. Nylon locknut snug but free: the plate must drop onto its rest
posts under its own weight. The hinge axis is 279 mm out from the chain line and
28 mm above the deck. With the auger in the plate's clamps, its 44T gear hangs in the
carriage window and its cap end stops short of the chain.

## Step 12. Electronics board: supply, driver, Pi, interface board, e-stop

![Step 12](renders/steps/step_12.png)

| # | Qty | Part |
|---|---|---|
| 9 | 1 | Closed-loop stepper driver CL86T V4.1 (24-80 VDC) |
| 10 | 1 | Power supply Mean Well LRS-350-36 (36 V, 9.7 A) |
| 35 | 1 | Raspberry Pi 4 Model B (any Pi with pigpio works; the lab's spare) |
| 36 | 1 | Interface board: ULN2803A (step/dir/enable to the CL86T opto inputs), 3 x 10k pull-ups to 3.3 V, screw terminals, perfboard |
| 37 | 1 | E-stop mushroom switch, NC, in enclosure (breaks the 36 V DC feed to the driver) |
| 38 | 1 | Electronics board, 1/4 in plywood 420 x 300 |
| 39 | 1 | Wire, fuses and connectors: 18 AWG (36 V), 22 AWG (signals), IEC C14 inlet with fuse + switch, 4-pin motor + encoder extension |

Electronics board, on the bench beside the drive end:

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
check the hardware.

## Step 13. Test set-up (not in the CAD)

| # | Qty | Part |
|---|---|---|
| 42 | 1 | Digital dial indicator 0-12.7 mm x 0.01 mm with magnetic base (lift and sag tests) |
| 43 | 1 | Push-pull force gauge 50 N (station push-up, drag force) |
| 44 | 1 | ADXL345 accelerometer breakout (carriage vibration in transit) |
| 45 | 11 | Dummy module mass: 250 g bag of table salt (or 2 x 125 g steel bars) per carriage |

Put a 250 g dummy (a salt bag taped to the plate) on carriages 2-12, mount the dial indicator on its magnetic base on a steel plate on the deck at the station, and stick the ADXL345 to module 1's mounting plate near the outlet. Then run [TEST-PLAN.md](TEST-PLAN.md) T0-T7.

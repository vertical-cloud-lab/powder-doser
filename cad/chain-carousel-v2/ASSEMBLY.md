# Assembly: chain-carousel test rig v2 (vertical twin chain)

Eleven steps in build order, then the test set-up. In each render the parts from earlier steps are pale, and the step's new parts are in colour, lifted along the way they go in. The table under each render is the BoM lines that step uses ([BOM.md](BOM.md) item numbers). The animation ([MP4](renders/chain_carousel_v2.mp4)) shows the same sequence moving.

Tools: chain breaker, metric hex keys, 8 mm and 7/16 in wrenches, M5 tap, chop or band saw for the 2020 and the shafts, soldering iron, heat-set insert tip, e-clip pliers, feeler gauges.

## Step 1. Base frame: rails, station rail, corner brackets, leveling feet and front risers

![Step 1](renders/steps/step_01.png)

| # | Qty | Part |
|---|---|---|
| 18 | 1 | 2020 T-slot extrusion, 10 x 1000 mm pack: 4 posts of 676 mm (each offcut gives a 204 mm cross rail), 4 long rails of 417.7 mm (2 per bar), station rail 204 + fork post 194 + vial post 197 from a seventh bar |
| 19 | 20 | 2020 90-degree corner bracket (+2 for the fork and vial posts) |
| 20 | 50 | M5 x 10 button head screw, with blue threadlocker (brackets and station parts; T-nuts can't take a nylock) |
| 21 | 74 | M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet, station) |
| 22 | 4 | Leveling foot, M6 x 40 stud, into a T-nut in the base rail |
| 25 | 1 | Loctite 243 (blue, medium strength) for T-nut screws, set screws and the tensioner blocks' screws; Loctite 222 (purple, low strength) where a part is meant to come apart |

The frame uses seven bars of one VEVOR 10-pack of 1000 mm 2020. Cut four posts of 676 mm (each
offcut gives a 204 mm cross rail), four long rails of 417.7 mm (two per bar), and from a seventh bar
the station rail (204 mm), the fork post (155 mm) and the vial post (197 mm). Square every cut.

Lay two long rails on the bench, 224 mm apart centre to centre, with a cross rail between them at each
end and the station rail 65 mm behind the front chain's plane (two corner brackets). Screw the
four leveling feet up into T-nuts in the long rails' bottom slots, 15 mm in from each end. Blue Loctite on every
screw that goes into a T-nut.

## Step 2. Posts and top frame

![Step 2](renders/steps/step_02.png)

| # | Qty | Part |
|---|---|---|
| 18 | 1 | 2020 T-slot extrusion, 10 x 1000 mm pack: 4 posts of 676 mm (each offcut gives a 204 mm cross rail), 4 long rails of 417.7 mm (2 per bar), station rail 204 + fork post 194 + vial post 197 from a seventh bar |
| 19 | 20 | 2020 90-degree corner bracket (+2 for the fork and vial posts) |
| 20 | 50 | M5 x 10 button head screw, with blue threadlocker (brackets and station parts; T-nuts can't take a nylock) |
| 21 | 74 | M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet, station) |

Stand a post on each end of the long rails. Each post gets four corner brackets: at its foot, one on the
long rail's top on the inner side and one on the cross rail's top; at its head, the same two under the top rails.
Use M5 x 10 button heads into drop-in T-nuts. Put the two top long rails and two top cross rails on the posts the
same way as the base, then square the box by its diagonals (equal within 1 mm) and tighten.

Don't put brackets on the posts' inner x faces between 205 and 690 mm: the side plates sit there.

## Step 3. Side plates onto the posts

![Step 3](renders/steps/step_03.png)

| # | Qty | Part |
|---|---|---|
| 21 | 74 | M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet, station) |
| 23 | 2 | Side plates, 1/4 in 6061: front 244 x 375 mm, back 244 x 485 mm, both from one 12 x 36 in plate; cut and drilled from dxf/ (BYU shop, or SendCutSend: price on upload) |
| 24 | 20 | M5 x 12 button head screw (side plates to the posts' T-nuts), with blue threadlocker |

Have the two side plates cut from one 12 x 36 in sheet of 1/4 in 6061 (`dxf/side_plate_front.dxf`,
`dxf/side_plate_back.dxf`, by the BYU shop or SendCutSend). The front plate is 244 x 375 mm. The back
plate runs down to 205 mm above the bench, 244 x 485 mm, because it carries the motor.
Tap the four M5 holes under the top bearing slots on each plate.

Bolt each plate to the inner faces of its two posts with M5 x 12 button heads from the inside into drop-in T-nuts.
Set the front plate's bottom edge 315 mm above the bench and the back plate's 205 mm. The plates' inner
faces end up 365 mm apart, 30 mm outside each chain.

## Step 4. Flange bearings and top-shaft tensioners on the side plates

![Step 4](renders/steps/step_04.png)

| # | Qty | Part |
|---|---|---|
| 9 | 8 | 2-bolt stamped-steel flange bearing SBSFL202-10: 5/8 in bore, set screws, 2-1/2 in bolt centres |
| 11 | 16 | Hex bolt 1/4-20 x 1 in, Grade 5 (flange bearings to the side plates) |
| 12 | 1 | 1/4-20 nylon-insert locknuts, pack of 100 (16 used on the bearings) |
| 17 | 8 | M5 nylon-insert locknut (4 on the motor, 4 trapped in the tensioner blocks as jack-screw nuts) |
| 34 | 8 | M5 x 10 socket head screw (tensioner blocks, into tapped holes in the plates) |
| 35 | 4 | M5 x 30 socket head screw (tensioner jack screws) |
| 37 | 6 | Hold-downs (2) and tensioner blocks (4), PETG |

Mount the eight SBSFL202-10 flange bearings on the plates' outer faces, bolt line horizontal, with
1/4-20 x 1 in bolts and nylon-insert locknuts on the plates' inner faces. Each bearing's rear dome sits in its
plate's 49 mm hole. The bottom shafts are 393.6 mm above the bench. Put the four top bearings at the bottom of their
slots, 6 mm below the nominal 622.2 mm, which leaves room to fit the chains. Snug those bolts only.

Under each top bearing, screw a printed tensioner block to the plate (two M5 x 10 into the tapped holes, blue
Loctite). Drop an M5 nylon-insert locknut into the block's slot and run an M5 x 30 jack screw up through it until it
touches the underside of the bearing's front dome. The locknut keeps the jack screw from turning with the vibration.

## Step 5. Corner shafts with their sprockets (back set screws loose)

![Step 5](renders/steps/step_05.png)

| # | Qty | Part |
|---|---|---|
| 5 | 8 | Sprocket 35BS32-5/8: 32T, type B, 2 in hub, 7/8 in through the bore, 5/8 in bore, 3/16 in keyway, 2 set screws |
| 8 | 1 | Keyed shafting, 5/8 in x 72 in, 1018, 3/16 in keyway: cut 3 x 403 mm + 1 x 427 mm (the drive shaft) |
| 10 | 1 | Key stock 3/16 x 3/16 in, 12 in (front sprockets and the 15T on the shaft; back sprockets locked by set screws after phasing) |

Cut the 72 in keyed bar into three shafts of 402.9 mm and one of 427.3 mm. The long
one is the drive shaft and goes in the bottom +y corner (B+). Each shaft carries two sprockets. Feed it through the
front bearing, slide on the front sprocket with its hub toward the front, then the back sprocket with its hub toward
the back, and push the shaft on through the back bearing.

Centre each sprocket's teeth on its chain line, 305 mm apart, the front one 30 mm inside the front plate. Key
the front sprocket and tighten its set screws (blue Loctite). Leave the back one's key out and its set screws loose:
the carriages set its phase in step 10. Tighten the bearings' set screws on the shaft.

## Step 6. NEMA 34 on the back plate, 15T sprockets, drive chain

![Step 6](renders/steps/step_06.png)

| # | Qty | Part |
|---|---|---|
| 1 | 1 | ANSI #35 roller chain, 10 ft roll (320 pitches): two 104-link loops + the 44-link drive chain |
| 4 | 1 | Roller chain breaker, #25-#60 (Dura-Roll #1) |
| 6 | 1 | Sprocket 35BS15H-5/8: 15T, 5/8 in bore (drive chain, on the B+ shaft's stub) |
| 7 | 1 | Sprocket 35BS15H-1/2: 15T, 1/2 in bore; shop re-bores it to 14 mm H7 with a 5 mm keyway for the NEMA 34 |
| 10 | 1 | Key stock 3/16 x 3/16 in, 12 in (front sprockets and the 15T on the shaft; back sprockets locked by set screws after phasing) |
| 13 | 1 | NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 14 mm x 37 mm keyed shaft |
| 16 | 4 | M5 x 25 socket head screw (motor flange to the back plate, in slots) |
| 17 | 8 | M5 nylon-insert locknut (4 on the motor, 4 trapped in the tensioner blocks as jack-screw nuts) |

Have the shop re-bore the 35BS15H-1/2 sprocket to 14 mm H7 with a 5 mm keyway, then slide it onto the NEMA 34's
shaft, hub outward, over the key. Offer the motor up to the back plate's inner face from inside the frame, with its
pilot in the plate's slot and the shaft and sprocket out the back. Bolt it on with four M5 x 25 from outside and
nylon-insert locknuts on the flange. The motor's axis is 255.5 mm above the bench, right under the drive shaft.
It is 6 kg, so support it while you fit the bolts.

Key the 35BS15H-5/8 sprocket onto the drive shaft's stub, in line with the motor's sprocket. Cut 44 pitches from
the 10 ft roll and close them round both sprockets. Pull the motor down in its slots (+-4 mm) until the
chain has about 2 mm of play at mid-span, then tighten its bolts.

## Step 7. Chains: 13 A-1 links per chain, close both loops

![Step 7](renders/steps/step_07.png)

| # | Qty | Part |
|---|---|---|
| 1 | 1 | ANSI #35 roller chain, 10 ft roll (320 pitches): two 104-link loops + the 44-link drive chain |
| 2 | 26 | #35 A-1 attachment connecting link, spring clip, 0.133 in hole (M3): 13 per chain |
| 3 | 1 | Spring clips for #35 connecting links, pack of 5 (spares) |
| 4 | 1 | Roller chain breaker, #25-#60 (Dura-Roll #1) |

**First measure the chain** (see the BoM note): about 4.78 mm between the inner plates and a 5.08 mm bushing
means ANSI 35, which is what the sprockets are.

Cut two loops of 104 pitches from the 10 ft roll. In each, take out an outer link every 8 pitches and fit an A-1
attachment connecting link in its place, 13 per chain. On the front chain the tabs point back (+x, toward the
other chain); on the back chain they point forward. Number the A-1 links 1-13 the same way on both chains.

Wrap each chain round its four sprockets with the tabs on the outside of the loop, then close it with its 13th A-1
link. Each spring clip's closed end points the way the chain travels (bottom run toward -y). The chains hang slack,
because the top shafts are still at the bottom of their slots.

## Step 8. Station: hold-downs, hall switches, actuator, electronics carriage with dock magnet, approach fork, vial on the load cell

![Step 8](renders/steps/step_08.png)

| # | Qty | Part |
|---|---|---|
| 18 | 1 | 2020 T-slot extrusion, 10 x 1000 mm pack: 4 posts of 676 mm (each offcut gives a 204 mm cross rail), 4 long rails of 417.7 mm (2 per bar), station rail 204 + fork post 194 + vial post 197 from a seventh bar |
| 19 | 20 | 2020 90-degree corner bracket (+2 for the fork and vial posts) |
| 20 | 50 | M5 x 10 button head screw, with blue threadlocker (brackets and station parts; T-nuts can't take a nylock) |
| 21 | 74 | M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet, station) |
| 32 | 4 | M5 x 16 socket head screw (hold-downs, through the side plates), with blue threadlocker |
| 33 | 1 | M5 brass heat-set insert, 5.7 mm long, 6.4 mm hole, pack of 25 (hold-downs) |
| 37 | 6 | Hold-downs (2) and tensioner blocks (4), PETG |
| 38 | 6 | Station parts, PETG: actuator base clevis, yoke, approach fork and arm, vial cup, D-cut funnel, dock magnet bracket |
| 40 | 1 | Actuonix P16-150-22-12-P linear actuator: 150 mm stroke, potentiometer feedback, 46 mm/s, 50 N |
| 41 | 1 | Actuonix LAC linear actuator control board (closed-loop position from the pot; USB, RC, PWM or 0-3.3 V in) |
| 42 | 1 | 12 V supply for the LAC and actuator |
| 43 | 1 | Shoulder screw 4 x 30 mm, M3 (actuator's rear clevis) + M3 locknut |
| 44 | 1 | Shoulder screw 4 x 20 mm, M3 (rod end in the yoke) + M3 locknut |
| 45 | 1 | Holding electromagnet P20/15, 5 V, 0.22 A, 2.5 kg (24.5 N) at zero gap: the dock's mesh preload |
| 46 | 1 | N-channel logic-level MOSFET IRLB8721 (switches the dock magnet from the carriage board; out of stock on 2026-10-18, any logic-level N-MOSFET such as FQP30N06L works) |
| 47 | 1 | 1N4001 diode, 10-pack (flyback across the magnet coil) |
| 49 | 1 | Load cell 100 g (TAL221) under the vial |
| 50 | 1 | HX711 load-cell amplifier |
| 51 | 1 | 20 mL glass scintillation vial (lab stock; Wheaton 986546 is $383.77 per 500) |
| 52 | 1 | Electronics carriage (Sam's Oct 13) with the doser's NEMA 11 (shaft trimmed to 15 mm), 20T pinion and 12 V solenoid |
| 53 | 2 | Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME |

The station, under the bottom run:

1. Hold-downs: melt two M5 inserts into each printed hold-down, push a US5881 into each lip's pocket (INDEX front,
   HOME back), and screw them to the plates' inner faces with two M5 x 16 (blue Loctite). The lip sits 2 mm over the
   carriage tongue, the foot 4 mm under it; both have 3 mm lead-ins.
2. Actuator: the printed base clevis on the station rail (two M5 into T-nuts), the P16-150's rear clevis on a
   4 x 30 mm shoulder screw and M3 locknut.
3. Electronics carriage (Sam's): trim the NEMA 11's shaft to 15 mm, face the KHK SS1-20A pinion's hub off and bond
   the pinion on with Loctite 638, flush with the shaft end. Bond the dock electromagnet (Adafruit 3872) into the
   printed bracket and fix the bracket with the NEMA 11's two upper M2.5 screws (lengthened by 3 mm). Press two 4 mm
   steel locating pins into the rim at Sam's (30, 16) and (70, -16). Bond a printed boss to each side post and press
   a 4 mm stub pin through post and boss at Sam's (32, -34).
4. U-yoke: screw the two 2 mm steel arms to the printed crossbar (M3 into inserts), glue a stop block inside each
   arm, push the P16's rod-end plug into the crossbar's square socket and bolt it with an M4. Hang the carriage on
   the stub pins in the arms and fit an e-clip on each pin.
5. Approach fork on its post on the station rail, the tongue under the crossbar in its slot.
6. Vial post on the -y base rail, the level wedge, the load cell, the vial cup, the vial and the D-cut funnel.

## Step 9. Modules on the bench: auger into Sam's plate (the carrier), steel armature tab, plate pinned onto a carriage

![Step 9](renders/steps/step_09.png)

| # | Qty | Part |
|---|---|---|
| 27 | 1 | M3 nylon-insert locknut, 18-8, pack of 100 (one in each carriage hook; the actuator's clevis pins) |
| 28 | 30 | Clevis pin 5 mm with retaining-ring groove, steel, about 14 mm usable length (module hinge pins, 2 per module; 4 spare) |
| 29 | 38 | E-clip DIN 6799 for a 4 mm groove (5 mm pin), steel (on the hinge pins; 10 spare) |
| 30 | 26 | M3 x 6 flat head screw (steel armature tab to the plate) |
| 31 | 26 | M3 x 4 heat-set insert (CNC Kitchen short): two per mounting plate, for the armature tab |
| 39 | 12 | Mounting plate (Sam's Oct 13 Onshape part), printed for modules 2-13 (module 1 exists) |
| 48 | 13 | Armature tab, low-carbon steel 2 mm (14 ga), 22 x 28 mm, two countersunk M3 holes: laser cut |
| 61 | 13 | Auger, threaded storage (44T gear), and cap, lab design (PR #170): 13 from #134's batch of 16 |

Modules on the bench (one per carriage, 13 in all):

1. Plate: melt two M3 inserts into the back strip of Sam's plate, and drill or print the locating hole (4.2 mm) and
   slot (4.2 x 6 mm) in its underside. Screw the 2 mm steel armature tab on with two M3 x 6 flat heads.
2. Slide the lab auger into the plate's clamp rings (the 44T gear between the second and third), outlet at the hinge,
   and screw on the cap.
3. Put the plate between a carriage's lugs, hinge end at the front, and push a 5 mm clevis pin through each lug into
   Sam's knuckle; e-clip on each pin's inner end (before the auger goes in, if you do it the other way round). Press
   the plate's free end down past the two snap hooks: they hold it shut on the top run, where it hangs upside down.

The carriage and its module now come on and off the chain as one unit.

## Step 10. Carriages onto the chain at the loading position, one index at a time; phase and tension

![Step 10](renders/steps/step_10.png)

| # | Qty | Part |
|---|---|---|
| 26 | 26 | M3 x 12 button head screw (carriage to each A-1 tab, from the outside) |
| 27 | 1 | M3 nylon-insert locknut, 18-8, pack of 100 (one in each carriage hook; the actuator's clevis pins) |
| 36 | 13 | Carriage, PETG, with the two tab hooks (H2D, on the bed's diagonal; about 100 g each) |
| 54 | 14 | Neodymium disc magnet D42-N52, 1/4 x 1/8 in (13 index + 1 home) |

At the loading position (the +y side, mid-height): hold the unit beside the two A-1 tabs, 10 mm
off along the run, push it in until the carriage plate touches the tabs, slide it 10 mm so the printed hooks
take the tabs, and drive an M3 x 12 button head from outside through the plate and each tab into the locknut in
the hook. Index one module (bottom run toward -y) and fit the next. After 13, tighten the back sprockets' set screws
on the round of the shaft and spot a dimple under each.

To tension, turn the four jack screws the same amount until each long side deflects 3-4 mm under a 5 N side push at
mid-span (about 80 N per chain). Do the front and back together, so the top shafts stay level, then tighten the top
bearings' bolts.

## Step 11. Electronics board: supply, driver, Pi, interface board, LAC, e-stop

![Step 11](renders/steps/step_11.png)

| # | Qty | Part |
|---|---|---|
| 14 | 1 | Closed-loop stepper driver CL86T V4.1 (lab has one from the UofU order) |
| 15 | 1 | Power supply Mean Well LRS-350-48 (48 V, 7.3 A) |
| 55 | 1 | Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio) |
| 56 | 1 | Interface board: 74AHCT125 (3.3 V GPIO to 5 V step/dir/enable), 3 x 10k pull-ups, screw terminals, perfboard |
| 57 | 1 | E-stop GCX1136 (22 mm, NC, twist to release) + enclosure; breaks the 48 V feed to the driver |
| 58 | 1 | Electronics board, 1/4 in plywood 420 x 300 |
| 59 | 1 | IEC C14 inlet with switch + fuse drawer (Qualtek 719W-UEL3BR51) |
| 60 | 1 | 18 AWG stranded hook-up wire, 25 ft (48 V and motor) |

The electronics board sits on the bench behind the rig. Wire it like this:

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
| Pi GPIO 20 / 21 | DRV8825 STEP / DIR for the NEMA 11 (current limit 0.45 A: Vref 0.225 V) |
| Pi GPIO 16 | Dock magnet MOSFET gate (IRLB8721), 1N4001 across the coil, 5 V supply |
| Pi GPIO 12 | DRV8871 IN1 for the tap solenoid |
| Pi GPIO 5 / 6 | HX711 DT / SCK |

Set the CL86T DIP switches to 4000 pulses/rev and the motor current to 6.0 A. Run `sudo pigpiod`, then
`python3 test/chain_rig.py --sim lap` to check the software and `python3 test/chain_rig.py home` to check the
hardware. At 4000 pulses/rev one module is exactly 1000 steps.

## Step 12. Test set-up (not in the CAD)

| # | Qty | Part |
|---|---|---|
| 62 | 1 | Digital indicator 0-1 in / 0.01 mm with arm and magnetic base (index, lift, sag tests) |
| 63 | 1 | Digital hanging scale 50 kg (torque lever, push-up and snap forces; a 50 N push-pull gauge is better if the lab has one) |
| 64 | 1 | ADXL343 accelerometer breakout (transit vibration) |
| 65 | 3 | Table salt, 26 oz (test fill for the augers) |

Fill the augers to a working mass with salt (or the powder under test). Clamp the dial indicator's magnetic base to a steel plate screwed to the front side plate's inner face beside the station, and stick the ADXL343 to module 1's mounting plate near the outlet. Then run [TEST-PLAN.md](TEST-PLAN.md).

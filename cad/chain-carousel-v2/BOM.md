# Bill of materials: chain-carousel test rig v2 (vertical twin chain)

Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are counted from the CAD (`layout.placements()`). Prices are USD on the date shown on each line and will drift. **Step** is the assembly step that uses the line ([ASSEMBLY.md](ASSEMBLY.md)). `bom.csv` has the same data.

**Total $1,288.85; rig without test gear $1,147.46.** Lines marked estimate add up to $116.56. The NEMA 34, the CL86T, module 1's plate, the 13 augers (#134's batch of 16) and the electronics carriage's NEMA 11, solenoid and printed body are already in the lab and count as $0.

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
| 8 | 1 | [Keyed shafting, 5/8 in x 72 in, 1018, 3/16 in keyway: cut 3 x 403 mm + 1 x 427 mm (the drive shaft)](https://www.surpluscenter.com/5-8-x-72-keyed-shafting-3-16-wide-keyway/) (verified 2026-10-16 (paternoster BoM)) | Surplus Center | 601881 | $43.90 | $43.90 | 5 |
| 9 | 8 | [2-bolt stamped-steel flange bearing SBSFL202-10: 5/8 in bore, set screws, 2-1/2 in bolt centres](https://www.surpluscenter.com/5-8-2-bolt-stamped-steel-flange-bearing/) (verified 2026-10-16 (paternoster BoM)) | Surplus Center | 600174 | $11.30 | $90.40 | 4 |
| 10 | 1 | [Key stock 3/16 x 3/16 in, 12 in (front sprockets and the 15T on the shaft; back sprockets locked by set screws after phasing)](https://surpluscenter.com/3-16-square-key-stock-12-length-g-g-mfg-407-) (verified 2026-10-16 (paternoster BoM)) | Surplus Center | G&G 407-0300 | $2.80 | $2.80 | 5,6 |
| 11 | 16 | [Hex bolt 1/4-20 x 1 in, Grade 5 (flange bearings to the side plates)](https://paulbhardware.com/hex-cap-screw-1-4-20x1-gr5-zinc-h5c14x1) (verified 2026-10-16 (paternoster BoM)) | PaulB Hardware | H5C14X1 | $0.15 | $2.40 | 4 |
| 12 | 1 | [1/4-20 nylon-insert locknuts, pack of 100 (16 used on the bearings)](https://www.mcmaster.com/95615A120/) (verified 2026-10-16 (paternoster BoM)) | McMaster-Carr | 95615A120 | $7.46 | $7.46 | 4 |
| | | **Drive** | | | | | |
| 13 | 1 | [NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 14 mm x 37 mm keyed shaft](https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000) (already bought by UofU) | StepperOnline | 34HS59-6004D-E1000 | $0.00 | $0.00 | 6 |
| 14 | 1 | [Closed-loop stepper driver CL86T V4.1 (lab has one from the UofU order)](https://ozrobotics.com/shop/closed-loop-stepper-driver-v4-1-08-2a-2480vdc-for-nema-34-stepper-motor/) (in the lab (47.43 new, verified 2026-10-16)) | StepperOnline (OzRobotics) | CL86T | $0.00 | $0.00 | 11 |
| 15 | 1 | [Power supply Mean Well LRS-350-48 (48 V, 7.3 A)](https://www.trcelectronics.com/products/mean-well-lrs-350-48) (verified 2026-10-16 (paternoster BoM)) | TRC Electronics | LRS-350-48 | $36.11 | $36.11 | 11 |
| 16 | 4 | [M5 x 25 socket head screw (motor flange to the back plate, in slots)](https://www.belmetric.com/) (estimate, not verified) | BelMetric | M5 x 25 SHCS | $0.20 | $0.80 | 6 |
| 17 | 8 | [M5 nylon-insert locknut (4 on the motor, 4 trapped in the tensioner blocks as jack-screw nuts)](https://www.mcmaster.com/93625A200/) (estimate, not verified) | McMaster-Carr | 93625A200 | $0.12 | $0.96 | 4,6 |
| | | **Frame** | | | | | |
| 18 | 1 | [2020 T-slot extrusion, 10 x 1000 mm pack: 4 posts of 676 mm (each offcut gives a 204 mm cross rail), 4 long rails of 417.7 mm (2 per bar), station rail 204 + fork post 194 + vial post 197 from a seventh bar](https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492) (verified 2026-10-13; the page shows both in and out of stock) | VEVOR | 2020OBLXC10JMQNSK001V0 | $66.90 | $66.90 | 1,2,8 |
| 19 | 20 | [2020 90-degree corner bracket (+2 for the fork and vial posts)](https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds) (verified 2026-10-13) | West3D | NA0394 | $1.59 | $31.80 | 1,2,8 |
| 20 | 50 | [M5 x 10 button head screw, with blue threadlocker (brackets and station parts; T-nuts can't take a nylock)](https://www.belmetric.com/) (verified 2026-10-16 (paternoster BoM)) | BelMetric | M5 x 10 BHCS | $0.12 | $6.00 | 1,2,8 |
| 21 | 74 | [M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet, station)](https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads) (verified 2026-10-13) | West3D | WES5240M5 | $0.17 | $12.58 | 1,2,3,8 |
| 22 | 4 | [Leveling foot, M6 x 40 stud, into a T-nut in the base rail](https://www.tnutz.com/product/lf-020-a/) (verified 2026-10-16 (paternoster BoM)) | TNUTZ | LF-020-A | $1.85 | $7.40 | 1 |
| 23 | 2 | [Side plates, 1/4 in 6061: front 244 x 375 mm, back 244 x 485 mm, both from one 12 x 36 in plate; cut and drilled from dxf/ (BYU shop, or SendCutSend: price on upload)](https://fixsupply.com/1248-12-36-6061-aluminum-plate-t651-1-4-thick-x-12-wide-x-36-long) (one plate $104.89 for both; verified 2026-10-13) | FixSupply (thyssenkrupp) | SHT-6061-0.25X12-36 | $52.45 | $104.89 | 3 |
| 24 | 20 | [M5 x 12 button head screw (side plates to the posts' T-nuts), with blue threadlocker](https://www.belmetric.com/) (estimate, not verified) | BelMetric | M5 x 12 BHCS | $0.12 | $2.40 | 3 |
| 25 | 1 | [Loctite 243 (blue, medium strength) for T-nut screws, set screws and the tensioner blocks' screws; Loctite 222 (purple, low strength) where a part is meant to come apart](https://www.mcmaster.com/loctite/) (verified 2026-10-16 (paternoster BoM)) | McMaster-Carr | Loctite 243 | $27.25 | $27.25 | 1 |
| | | **Fasteners** | | | | | |
| 26 | 26 | [M3 x 12 button head screw (carriage to each A-1 tab, from the outside)](https://www.belmetric.com/) (estimate, not verified) | BelMetric | M3 x 12 BHCS | $0.10 | $2.60 | 10 |
| 27 | 1 | [M3 nylon-insert locknut, 18-8, pack of 100 (one in each carriage hook; the actuator's clevis pins)](https://www.mcmaster.com/93625A100/) (verified 2026-10-16 (paternoster BoM)) | McMaster-Carr | 93625A100 | $6.94 | $6.94 | 9,10 |
| 28 | 30 | [Clevis pin 5 mm with retaining-ring groove, steel, about 14 mm usable length (module hinge pins, 2 per module; 4 spare)](https://www.mcmaster.com/clevis-pins/) (estimate, not verified) | McMaster-Carr | clevis pins, metric | $0.65 | $19.50 | 9 |
| 29 | 38 | [E-clip DIN 6799 for a 4 mm groove (5 mm pin), steel (on the hinge pins; 10 spare)](https://www.mcmaster.com/e-style-retaining-rings/) (estimate, not verified) | McMaster-Carr | e-style retaining rings, metric | $0.10 | $3.80 | 9 |
| 30 | 26 | [M3 x 6 flat head screw (steel armature tab to the plate)](https://www.belmetric.com/) (estimate, not verified) | BelMetric | M3 x 6 FHCS | $0.10 | $2.60 | 9 |
| 31 | 26 | [M3 x 4 heat-set insert (CNC Kitchen short): two per mounting plate, for the armature tab](https://west3d.com/products/cnc-kitchen-heat-set-inserts-various-sizes) (estimate, not verified) | West3D |  | $0.15 | $3.90 | 9 |
| 32 | 4 | [M5 x 16 socket head screw (hold-downs, through the side plates), with blue threadlocker](https://www.belmetric.com/) (estimate, not verified) | BelMetric | M5 x 16 SHCS | $0.20 | $0.80 | 8 |
| 33 | 1 | [M5 brass heat-set insert, 5.7 mm long, 6.4 mm hole, pack of 25 (hold-downs)](https://www.mcmaster.com/94459A774/) (verified 2026-10-16 (paternoster BoM)) | McMaster-Carr | 94459A774 | $7.27 | $7.27 | 8 |
| 34 | 8 | [M5 x 10 socket head screw (tensioner blocks, into tapped holes in the plates)](https://www.belmetric.com/) (estimate, not verified) | BelMetric | M5 x 10 SHCS | $0.15 | $1.20 | 4 |
| 35 | 4 | [M5 x 30 socket head screw (tensioner jack screws)](https://www.belmetric.com/) (estimate, not verified) | BelMetric | M5 x 30 SHCS | $0.25 | $1.00 | 4 |
| | | **Printed** | | | | | |
| 36 | 13 | Carriage, PETG, with the two tab hooks (H2D, on the bed's diagonal; about 100 g each) (filament at $20/kg) | printed | stl/carriage.stl | $2.00 | $26.00 | 10 |
| 37 | 6 | Hold-downs (2) and tensioner blocks (4), PETG (filament) | printed | stl/hold_down.stl, stl/tensioner_block.stl | $0.40 | $2.40 | 4,8 |
| 38 | 6 | Station parts, PETG: actuator base clevis, yoke, approach fork and arm, vial cup, D-cut funnel, dock magnet bracket (filament) | printed | stl/ | $0.50 | $3.00 | 8 |
| 39 | 12 | [Mounting plate (Sam's Oct 13 Onshape part), printed for modules 2-13 (module 1 exists)](https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f) (filament at $20/kg) | printed | Onshape 581956d5 | $1.40 | $16.80 | 9 |
| | | **Station** | | | | | |
| 40 | 1 | [Actuonix P16-150-22-12-P linear actuator: 150 mm stroke, potentiometer feedback, 46 mm/s, 50 N](https://www.actuonix.com/p16-p) (verified 2026-10-16 (paternoster BoM)) | Actuonix | P16-150-22-12-P | $90.00 | $90.00 | 8 |
| 41 | 1 | [Actuonix LAC linear actuator control board (closed-loop position from the pot; USB, RC, PWM or 0-3.3 V in)](https://www.actuonix.com/lac) (verified 2026-10-16 (paternoster BoM)) | Actuonix | LAC | $30.00 | $30.00 | 8 |
| 42 | 1 | [12 V supply for the LAC and actuator](https://www.actuonix.com/lac) (verified 2026-10-16 (paternoster BoM)) | Actuonix | 12V PSU | $10.00 | $10.00 | 8 |
| 43 | 1 | [Shoulder screw 4 x 30 mm, M3 (actuator's rear clevis) + M3 locknut](https://www.mcmaster.com/90265A992/) (verified 2026-10-16 (paternoster BoM)) | McMaster-Carr | 90265A992 | $5.11 | $5.11 | 8 |
| 44 | 1 | [Shoulder screw 4 x 20 mm, M3 (rod end in the yoke) + M3 locknut](https://www.mcmaster.com/90265A124/) (verified 2026-10-16 (paternoster BoM)) | McMaster-Carr | 90265A124 | $5.68 | $5.68 | 8 |
| 45 | 1 | [Holding electromagnet P20/15, 5 V, 0.22 A, 2.5 kg (24.5 N) at zero gap: the dock's mesh preload](https://www.adafruit.com/product/3872) (verified 2026-10-18) | Adafruit | 3872 | $7.50 | $7.50 | 8 |
| 46 | 1 | [N-channel logic-level MOSFET IRLB8721 (switches the dock magnet from the carriage board; out of stock on 2026-10-18, any logic-level N-MOSFET such as FQP30N06L works)](https://www.adafruit.com/product/355) (verified 2026-10-18) | Adafruit | 355 | $2.25 | $2.25 | 8 |
| 47 | 1 | [1N4001 diode, 10-pack (flyback across the magnet coil)](https://www.adafruit.com/product/755) (verified 2026-10-18) | Adafruit | 755 | $1.50 | $1.50 | 8 |
| 48 | 13 | [Armature tab, low-carbon steel 2 mm (14 ga), 22 x 28 mm, two countersunk M3 holes: laser cut](https://sendcutsend.com/) (estimate (SendCutSend quotes on upload)) | SendCutSend | dxf (from parts.armature_tab) | $3.50 | $45.50 | 9 |
| 49 | 1 | [Load cell 100 g (TAL221) under the vial](https://www.sparkfun.com/products/14727) (verified 2026-10-16 (paternoster BoM)) | SparkFun | SEN-14727 | $14.50 | $14.50 | 8 |
| 50 | 1 | [HX711 load-cell amplifier](https://www.sparkfun.com/products/13879) (verified 2026-10-16 (paternoster BoM)) | SparkFun | SEN-13879 | $4.95 | $4.95 | 8 |
| 51 | 1 | [20 mL glass scintillation vial (lab stock; Wheaton 986546 is $383.77 per 500)](https://pfstar.com/986546-20-mL-LS-Vial-22-400-Urea-Cap-PE-Cone-Ln) (verified 2026-10-16 (paternoster BoM)) | lab / pfstar.com | 986546 | $0.77 | $0.77 | 8 |
| 52 | 1 | Electronics carriage (Sam's Oct 13) with the doser's NEMA 11 (shaft trimmed to 15 mm), 20T pinion and 12 V solenoid (existing (doser parts)) | lab | Onshape 581956d5 | $0.00 | $0.00 | 8 |
| | | **Electronics** | | | | | |
| 53 | 2 | [Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME](https://www.adafruit.com/product/158) (verified 2026-10-10 (v1 BoM)) | Adafruit | 158 | $2.00 | $4.00 | 8 |
| 54 | 14 | [Neodymium disc magnet D42-N52, 1/4 x 1/8 in (13 index + 1 home)](https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet) (verified 2026-10-10 (v1 BoM)) | K&J Magnetics | D42-N52 | $0.52 | $7.28 | 10 |
| 55 | 1 | [Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio)](https://www.adafruit.com/product/5291) (estimate, not verified) | Adafruit | 5291 | $15.00 | $15.00 | 11 |
| 56 | 1 | [Interface board: 74AHCT125 (3.3 V GPIO to 5 V step/dir/enable), 3 x 10k pull-ups, screw terminals, perfboard](https://www.adafruit.com/product/1787) (estimate, not verified) | Adafruit | 1787 | $6.00 | $6.00 | 11 |
| 57 | 1 | [E-stop GCX1136 (22 mm, NC, twist to release) + enclosure; breaks the 48 V feed to the driver](https://www.automationdirect.com/pn/GCX1136) ($21 + $9 box; verified 2026-10-10 (v1 BoM)) | AutomationDirect | GCX1136 | $30.00 | $30.00 | 11 |
| 58 | 1 | Electronics board, 1/4 in plywood 420 x 300 (estimate, not verified) | Home Depot |  | $6.00 | $6.00 | 11 |
| 59 | 1 | [IEC C14 inlet with switch + fuse drawer (Qualtek 719W-UEL3BR51)](https://www.digikey.com/en/products/detail/qualtek/719W-UEL3BR51/23019206) (verified 2026-10-10 (v1 BoM)) | Digi-Key | 719W-UEL3BR51 | $7.66 | $7.66 | 11 |
| 60 | 1 | [18 AWG stranded hook-up wire, 25 ft (48 V and motor)](https://www.digikey.com/en/products/result?keywords=18UL1007STRBLA25) (verified 2026-10-10 (v1 BoM)) | Digi-Key | 18UL1007STRBLA25 | $14.57 | $14.57 | 11 |
| | | **Module** | | | | | |
| 61 | 13 | Auger, threaded storage (44T gear), and cap, lab design (PR #170): 13 from #134's batch of 16 (existing) | lab | reference/auger-*.step | $0.00 | $0.00 | 9 |
| | | **Tools** | | | | | |
| 4 | 1 | [Roller chain breaker, #25-#60 (Dura-Roll #1)](https://surpluscenter.com/1-roller-chain-breaker-for-25-60-pitch/) (verified 2026-10-13) | Surplus Center | 100115 | $17.20 | $17.20 | 6,7 |
| | | **Test** | | | | | |
| 62 | 1 | [Digital indicator 0-1 in / 0.01 mm with arm and magnetic base (index, lift, sag tests)](https://www.penntoolco.com/igaging-digital-indicator-universal-arm-magnetic-base-set-35-520) (verified 2026-10-10 (v1 BoM)) | Penn Tool Co | iGaging 35-520 | $119.95 | $119.95 | 12 |
| 63 | 1 | [Digital hanging scale 50 kg (torque lever, push-up and snap forces; a 50 N push-pull gauge is better if the lab has one)](https://etekcity.com/products/luggage-scale-el11) (verified 2026-10-10 (v1 BoM)) | Etekcity | EL11 | $10.99 | $10.99 | 12 |
| 64 | 1 | [ADXL343 accelerometer breakout (transit vibration)](https://www.adafruit.com/product/4097) (verified 2026-10-10 (v1 BoM)) | Adafruit | 4097 | $5.95 | $5.95 | 12 |
| 65 | 3 | Table salt, 26 oz (test fill for the augers) (estimate, not verified) | grocery |  | $1.50 | $4.50 | 12 |

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
trim the NEMA 11's shaft to 15 mm so it ends at the pinion's back face (clear of the dock magnet); laser cut the 13 steel
armature tabs.

**Prices** are as listed on the date shown on each line. McMaster asked for a login on 2026-10-18, so McMaster lines are
carried from the paternoster BoM (read logged out on 2026-10-16) or marked estimate. Generic hardware is `estimate`.

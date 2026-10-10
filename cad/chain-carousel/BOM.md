# Bill of materials: chain-carousel test rig

Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are counted from the CAD (`layout.placements()`), so this table and the Onshape assembly agree. Prices are USD as listed on 2026-10-10 and will drift. **Step** is the assembly step that uses the line ([ASSEMBLY.md](ASSEMBLY.md)). `bom.csv` has the same data.

**Total $783.42; rig without test gear $641.03.** The NEMA 34 and module 1 are already in the lab and count as $0.

| # | Qty | Part | Vendor | Part no. | Unit | Ext. | Step |
|---|---|---|---|---|---|---|---|
| | | **Chain** | | | | | |
| 1 | 1 | [ANSI #35 roller chain, 3 ft (96 pitches) + 2 connecting links (now listed as AZSSMUK)](https://www.amazon.com/dp/B0C1YTF613) (on the ME order; verified 2026-10-10 via the Pi) | Amazon | B0C1YTF613 | $7.99 | $7.99 | 8 |
| 2 | 12 | [#35 A-1 attachment connecting link (bent tab, 0.10 in hole, M2.5); buy a 10-pack + a 5-pack](https://redboarchain.com/products/35-a1-c-l-attachment-connecting-link-for-35-roller-chain) (10-pack $38.92 + 5-pack $21.75; verified 2026-10-10) | Red Boar Chain | 35 A1 C/L | $4.04 | $60.67 | 8 |
| 4 | 1 | [Sprocket 35B19, 19T ANSI 35, B hub, stock bore; shop bores it to 14 mm H7 + 5 mm keyway](https://usarollerchain.com/products/35b19-sprocket) (verified 2026-10-10; $300 web minimum, order by phone (407-347-3519)) | USA Roller Chain | 35B19 | $15.99 | $15.99 | 6 |
| 5 | 1 | [Idler sprocket #35 19T with ball bearing, 1/2 in bore](https://www.amazon.com/dp/B07LDKCN1X) (verified 2026-10-10 via the Pi) | Amazon | B07LDKCN1X | $7.99 | $7.99 | 5 |
| | | **Drive** | | | | | |
| 6 | 1 | [NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 6 A, 14 mm x 37 mm keyed shaft](https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000) (already bought by UofU) | StepperOnline | 34HS59-6004D-E1000 | $0.00 | $0.00 | 3 |
| 7 | 1 | Key 5 x 5 x 25 mm (ships in the motor's keyway) (with the motor) | StepperOnline |  | $0.00 | $0.00 | 6 |
| 8 | 1 | Motor plate, 6061 aluminium 1/4 in, 140 x 140, from dxf/motor_plate.dxf (pilot bore, 4 x M5 tapped) (estimate, not verified) | local metal supplier / BYU shop stock |  | $20.00 | $20.00 | 3 |
| 9 | 1 | [Closed-loop stepper driver CL86T V4.1 (24-80 VDC, 5 V/24 V logic selector)](https://ozrobotics.com/shop/closed-loop-stepper-driver-v4-1-08-2a-2480vdc-for-nema-34-stepper-motor/) (verified 2026-10-10) | StepperOnline (OzRobotics) | CL86T | $47.43 | $47.43 | 12 |
| 10 | 1 | [Power supply Mean Well LRS-350-48 (48 V, 7.3 A)](https://www.trcelectronics.com/products/mean-well-lrs-350-48) (verified 2026-10-10) | TRC Electronics | LRS-350-48 | $36.11 | $36.11 | 12 |
| | | **Frame** | | | | | |
| 11 | 1 | [2020 T-slot extrusion, 10 x 1000 mm pack: 2 bars whole (rails), 7 cut to 690 (cross members), 4 legs of 230 from the offcuts](https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492) (verified 2026-10-10) | VEVOR | 10 x 1000 mm | $66.90 | $66.90 | 1,2 |
| 12 | 28 | [2020 90-degree corner bracket](https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds) (verified 2026-10-10) | West3D | NA03 | $1.59 | $44.52 | 1,2 |
| 13 | 56 | [M5 x 10 button head screw for the brackets (2 per bracket)](https://west3d.com/products/ldo-black-screws-nuts-and-various-fasteners-black) (50-pack $1.99; verified 2026-10-10) | West3D | LDO3385M5X | $0.04 | $2.23 | 1,2 |
| 14 | 84 | [M5 drop-in T-nut, 2020 slot 6 (brackets + deck screws)](https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads) (verified 2026-10-10) | West3D |  | $0.17 | $14.28 | 1,4 |
| 15 | 4 | [Leveling foot, M5 stud (into the leg's centre bore, tapped M5)](https://www.amazon.com/s?k=m5+leveling+feet+2020+extrusion) (estimate, not verified) | Amazon |  | $2.00 | $8.00 | 2 |
| 16 | 2 | [HDPE sheet 1/2 x 24 x 48 in, white; one per deck half (455 and 595 x 740 mm)](https://www.vevor.com/hdpe-sheets-c_13698/1-pack-hdpe-plastic-sheet-board-24-x-48-inch-plastic-panel-1-2-inch-) (verified 2026-10-10) | VEVOR |  | $74.90 | $149.80 | 4 |
| | | **Fasteners** | | | | | |
| 17 | 1 | [Idler stud: 1/2-13 x 2-1/2 in hex bolt, Grade 5, with a 1/2-13 nylock nut and a washer](https://boltsandnuts.com/products/1-2-13x2-1-2-hex-cap-screws-grade-5-bolts-zinc-clear) (set $2.55; verified 2026-10-10) | BoltsAndNuts.com |  | $2.55 | $2.55 | 5 |
| 18 | 7 | M5 nylock nut (motor plate, slider clamps, jack screw) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.06 | $0.42 | 4,5 |
| 20 | 4 | [M5 x 12 socket head screw (motor flange into the M5-tapped plate)](https://boltsandnuts.com/products/m5-0-8x12-class-12-9-alloy-socket-head-cap-screws-black-oxide) (100-pack $12.21; verified 2026-10-10) | BoltsAndNuts.com |  | $0.12 | $0.49 | 3 |
| 21 | 28 | M5 x 18 flat head (countersunk) screw, deck to frame T-nuts (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.15 | $4.20 | 4 |
| 22 | 6 | M5 x 25 flat head screw (motor plate and slider clamps, through the deck) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.20 | $1.20 | 4,5 |
| 23 | 1 | M5 x 40 socket head screw (tensioner jack screw) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.30 | $0.30 | 5 |
| 24 | 2 | M4 x 20 flat head screw (tensioner block, down from the deck into the PETG) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.15 | $0.30 | 5 |
| 25 | 12 | M2.5 x 8 button head screw (carriage to A-1 tab, through the 0.10 in hole) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.12 | $1.44 | 9 |
| 26 | 12 | [M2.5 heat-set insert (CNC Kitchen), in each carriage's inner wall](https://west3d.com/products/cnc-kitchen-heat-set-inserts-various-sizes) (estimate, not verified) | West3D |  | $0.15 | $1.80 | 9 |
| 27 | 4 | M4 x 25 socket head screw, each into an M4 drop-in T-nut in the front rail (hold-downs) (estimate, not verified) | West3D / BoltsAndNuts.com |  | $0.30 | $1.20 | 10 |
| 28 | 2 | M5 x 18 socket head screw + nylock nut (module 1 hinge pins, one per side) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.25 | $0.50 | 11 |
| | | **Printed** | | | | | |
| 29 | 12 | Carriage, PETG (H2D bed; about 125 g each) (filament at $20/kg) | printed | stl/carriage.stl | $2.50 | $30.00 | 9 |
| 30 | 3 | Idler slider, spacer and tensioner block, PETG (print the spacer to suit the idler's measured width) (filament) | printed | stl/idler_*.stl, stl/tensioner_block.stl | $0.50 | $1.50 | 5 |
| 31 | 2 | Hold-down block, PETG (filament) | printed | stl/hold_down.stl | $0.30 | $0.60 | 10 |
| 32 | 2 | Hall sensor holder, PETG (filament) | printed | stl/hall_holder.stl | $0.05 | $0.10 | 7 |
| | | **Electronics** | | | | | |
| 33 | 2 | [Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME](https://www.adafruit.com/product/158) (verified 2026-10-10) | Adafruit | 158 | $2.00 | $4.00 | 7 |
| 34 | 13 | [Neodymium disc magnet D42-N52, 1/4 x 1/8 in (12 index + 1 home)](https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet) (verified 2026-10-10) | K&J Magnetics | D42-N52 | $0.52 | $6.76 | 9 |
| 35 | 1 | [Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio)](https://www.adafruit.com/product/5291) (estimate, not verified) | Adafruit | 5291 | $15.00 | $15.00 | 12 |
| 36 | 1 | [Interface board: 74AHCT125 (3.3 V GPIO to 5 V step/dir/enable), 3 x 10k pull-ups to 3.3 V, screw terminals, perfboard](https://www.adafruit.com/product/1787) (estimate, not verified) | Adafruit | 1787 | $6.00 | $6.00 | 12 |
| 37 | 1 | [E-stop GCX1136 (22 mm, NC, twist to release) + enclosure; breaks the 48 V feed to the driver](https://www.automationdirect.com/pn/GCX1136) ($21 + $9 box; verified 2026-10-10) | AutomationDirect | GCX1136 | $30.00 | $30.00 | 12 |
| 38 | 1 | Electronics board, 1/4 in plywood 420 x 300 (estimate, not verified) | Home Depot |  | $6.00 | $6.00 | 12 |
| 39 | 1 | [IEC C14 inlet with switch + fuse drawer (Qualtek 719W-UEL3BR51)](https://www.digikey.com/en/products/detail/qualtek/719W-UEL3BR51/23019206) (verified 2026-10-10) | Digi-Key | 719W-UEL3BR51 | $7.66 | $7.66 | 12 |
| 40 | 1 | [18 AWG stranded hook-up wire, 25 ft (48 V and motor)](https://www.digikey.com/en/products/result?keywords=18UL1007STRBLA25) (verified 2026-10-10) | Digi-Key | 18UL1007STRBLA25 | $14.57 | $14.57 | 12 |
| | | **Module** | | | | | |
| 41 | 1 | [Mounting plate (Sam's Oct 8 Onshape design), printed](https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f) (existing) | lab | Onshape 581956d5 | $0.00 | $0.00 | 11 |
| 42 | 2 | Auger, threaded storage, and cap (lab design, PR #170) (existing) | lab | reference/auger-*.step | $0.00 | $0.00 | 11 |
| | | **Tools** | | | | | |
| 3 | 1 | [Chain breaker CB25/60 (#25-#60)](https://redboarchain.com/products/cb25-60-roller-chain-breaker-breaks-25-thru-60-chain) (verified 2026-10-10) | Red Boar Chain | CB25/60 | $22.53 | $22.53 | 8 |
| | | **Test** | | | | | |
| 43 | 1 | [Digital indicator 0-1 in / 0.01 mm with arm and magnetic base (lift, sag, index tests)](https://www.penntoolco.com/igaging-digital-indicator-universal-arm-magnetic-base-set-35-520) (verified 2026-10-10) | Penn Tool Co | iGaging 35-520 | $119.95 | $119.95 | 13 |
| 44 | 1 | [Digital hanging scale 50 kg (drag and push-up force; a 50 N push-pull gauge is better if the lab has one)](https://etekcity.com/products/luggage-scale-el11) (verified 2026-10-10) | Etekcity | EL11 | $10.99 | $10.99 | 13 |
| 45 | 1 | [ADXL343 accelerometer breakout (transit vibration)](https://www.adafruit.com/product/4097) (verified 2026-10-10) | Adafruit | 4097 | $5.95 | $5.95 | 13 |
| 46 | 11 | Dummy module mass: 250 g bag of table salt per carriage (estimate, not verified) | grocery |  | $0.50 | $5.50 | 13 |

## Notes

**Before ordering sprockets, measure the chain that arrived.** The Amazon listing no longer gives dimensions.
ANSI #35 has a 0.200 in (5.08 mm) bushing and 0.188 in (4.78 mm) between the inner plates. ISO 06B has the same
3/8 in pitch but a 6.35 mm roller and 5.72 mm between the plates, and the two don't mix: a 5.3 mm 06B tooth can't
enter a #35 chain, and a 0.168 in #35 tooth rattles in 06B. (ISO 06C *is* ANSI 35.)

**Attachment-link holes are 0.10 in (M2.5).** McMaster's 7321K1 (A-1) and 7321K31 (SA-1) have a 0.134 in hole
for M3, but their prices don't show without a login. Drilling the Red Boar tabs to 3.2 mm leaves about 2.35 mm
of metal each side, which is plenty for this load.

**USA Roller Chain has a $300 web minimum.** Order the 35B19 by phone, or take Red Boar's 35B19H ($16.95, pick
the bore, out of stock on 2026-10-10). No vendor checked lists a 19T #35 sprocket with a 14 mm bore and 5 mm
keyway, so the plan is a stock-bore blank bored in the BYU shop.

**Prices** are as listed on 2026-10-10 by vendor (`verified`), or estimates for generic hardware (`estimate`).
The two `Amazon` prices were read through the powder-doser Pi, because Amazon blocks the CI runner's IP.

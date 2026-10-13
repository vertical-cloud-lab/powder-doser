# Bill of materials: chain-carousel test rig v2 (vertical twin chain)

Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are counted from the CAD (`layout.placements()`), so this table and the Onshape assembly agree. Prices are USD as listed on 2026-10-13 and will drift. **Step** is the assembly step that uses the line ([ASSEMBLY.md](ASSEMBLY.md)). `bom.csv` has the same data.

**Total $1,034.91; rig without test gear $893.52.** The NEMA 34 and module 1 are already in the lab and count as $0.

| # | Qty | Part | Vendor | Part no. | Unit | Ext. | Step |
|---|---|---|---|---|---|---|---|
| | | **Chain** | | | | | |
| 1 | 1 | [ANSI #35 roller chain, 10 ft roll (320 pitches, 1 connecting link): two 104-link loops + the 44-link drive chain](https://www.nitrochain.com/35-roller-chain-10ft) (verified 2026-10-13) | Nitro Chain | RC35-1R-10FT | $23.53 | $23.53 | 6,7 |
| 2 | 26 | [#35 A-1 attachment connecting link, spring clip, 0.133 in hole (M3): 13 per chain](https://www.nitrochain.com/35-a1-standard-attachment-connecting-link) (verified 2026-10-13) | Nitro Chain | CL35-A1 | $2.55 | $66.30 | 7 |
| 4 | 8 | [Sprocket 35BS32-5/8: 32T, type B, 2 in hub, 7/8 in through the bore, 5/8 in bore, 3/16 in keyway, 2 set screws](https://www.surpluscenter.com/32t-5-8-bore-35p-sprocket/) (verified 2026-10-13) | Surplus Center | 601139 | $21.55 | $172.40 | 5 |
| 5 | 1 | [Sprocket 35BS15H-5/8: 15T, 5/8 in bore, 3/16 in keyway (drive chain, on the B+ shaft's stub)](https://www.surpluscenter.com/15t-5-8-bore-35p-sprocket/) (verified 2026-10-13) | Surplus Center | 601078 | $6.65 | $6.65 | 6 |
| 6 | 1 | [Sprocket 35BS15H-1/2: 15T, 1/2 in bore; shop re-bores it to 14 mm H7 with a 5 mm keyway for the NEMA 34](https://www.surpluscenter.com/15t-1-2-bore-35p-sprocket/) (verified 2026-10-13) | Surplus Center | 601077 | $6.65 | $6.65 | 6 |
| | | **Shafts** | | | | | |
| 7 | 1 | [Keyed shafting, 5/8 in x 72 in, 1018 cold-drawn, 3/16 in keyway: cut 3 x 403 mm + 1 x 427 mm (the drive shaft)](https://www.surpluscenter.com/5-8-x-72-keyed-shafting-3-16-wide-keyway/) (verified 2026-10-13) | Surplus Center | 601881 | $43.90 | $43.90 | 5 |
| 8 | 8 | [2-bolt stamped-steel flange bearing SBSFL202-10: 5/8 in bore, set screws, 2-1/2 in bolt centres, 1/4 in bolts](https://www.surpluscenter.com/5-8-2-bolt-stamped-steel-flange-bearing/) (verified 2026-10-13) | Surplus Center | 600174 | $11.30 | $90.40 | 4 |
| 9 | 1 | Key stock 3/16 x 3/16 in, 12 in (keys for the 4 front sprockets and the 15T on the shaft) (estimate, not verified) | any (hardware store, McMaster) |  | $4.00 | $4.00 | 5,6 |
| 10 | 16 | Hex bolt 1/4-20 x 1 in + nylock nut (bearings to the side plates) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.30 | $4.80 | 4 |
| | | **Drive** | | | | | |
| 11 | 1 | [NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 6 A, 14 mm x 37 mm keyed shaft](https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000) (already bought by UofU) | StepperOnline | 34HS59-6004D-E1000 | $0.00 | $0.00 | 6 |
| 12 | 1 | [Closed-loop stepper driver CL86T V4.1 (24-80 VDC, 5 V/24 V logic selector)](https://ozrobotics.com/shop/closed-loop-stepper-driver-v4-1-08-2a-2480vdc-for-nema-34-stepper-motor/) (verified 2026-10-10 (v1 BoM)) | StepperOnline (OzRobotics) | CL86T | $47.43 | $47.43 | 11 |
| 13 | 1 | [Power supply Mean Well LRS-350-48 (48 V, 7.3 A)](https://www.trcelectronics.com/products/mean-well-lrs-350-48) (verified 2026-10-10 (v1 BoM)) | TRC Electronics | LRS-350-48 | $36.11 | $36.11 | 11 |
| 14 | 4 | M5 x 25 socket head screw + nylock nut (motor flange to the back plate, in slots) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.30 | $1.20 | 6 |
| | | **Frame** | | | | | |
| 15 | 1 | [2020 T-slot extrusion, 10 x 1000 mm pack: 4 posts of 541 mm, 4 long rails of 417.7 mm, 4 cross rails of 204 mm (5 bars)](https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492) (verified 2026-10-13; the page shows both in and out of stock) | VEVOR | 2020OBLXC10JMQNSK001V0 | $66.90 | $66.90 | 1,2 |
| 16 | 16 | [2020 90-degree corner bracket](https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds) (verified 2026-10-13) | West3D | NA0394 | $1.59 | $25.44 | 2 |
| 17 | 32 | [M5 x 10 button head screw for the brackets (2 per bracket)](https://west3d.com/products/ldo-black-screws-nuts-and-various-fasteners-black) (50-pack $1.99; verified 2026-10-10 (v1 BoM)) | West3D | LDO3385M5X | $0.04 | $1.27 | 2 |
| 18 | 56 | [M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet)](https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads) (verified 2026-10-13) | West3D | WES5240M5 | $0.17 | $9.52 | 1,2,3 |
| 19 | 4 | [Leveling foot, M5 stud, into a T-nut in the base rail's bottom slot](https://www.amazon.com/s?k=m5+leveling+feet+2020+extrusion) (estimate, not verified) | Amazon |  | $2.00 | $8.00 | 1 |
| 20 | 2 | [Side plates, 1/4 in 6061: front 244 x 375 mm, back 244 x 485 mm, both from one 12 x 36 in plate; cut and drilled from dxf/ (BYU shop, or SendCutSend: price on upload)](https://fixsupply.com/1248-12-36-6061-aluminum-plate-t651-1-4-thick-x-12-wide-x-36-long) (one plate $104.89 for both; verified 2026-10-13) | FixSupply (thyssenkrupp) | SHT-6061-0.25X12-36 | $52.45 | $104.89 | 3 |
| 21 | 20 | M5 x 12 button head screw (side plates to the posts' T-nuts) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.12 | $2.40 | 3 |
| | | **Fasteners** | | | | | |
| 22 | 26 | M3 x 6 button head screw (carriage to each A-1 tab) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.10 | $2.60 | 8 |
| 23 | 26 | [M3 x 4 heat-set insert (CNC Kitchen short), two per carriage](https://west3d.com/products/cnc-kitchen-heat-set-inserts-various-sizes) (estimate, not verified) | West3D |  | $0.15 | $3.90 | 8 |
| 24 | 26 | M5 x 10 flat head (countersunk) screw: hinge pins, two per module (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.12 | $3.12 | 10 |
| 25 | 4 | M5 x 16 socket head screw (hold-downs, through the side plates) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.20 | $0.80 | 9 |
| 26 | 4 | [M5 heat-set insert (hold-downs)](https://west3d.com/products/cnc-kitchen-heat-set-inserts-various-sizes) (estimate, not verified) | West3D |  | $0.30 | $1.20 | 9 |
| 27 | 8 | M5 x 10 socket head screw (tensioner blocks, into tapped holes in the plates) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.15 | $1.20 | 4 |
| 28 | 4 | M5 x 30 socket head screw + hex nut (tensioner jack screws) (estimate, not verified) | BoltsAndNuts.com / McMaster |  | $0.30 | $1.20 | 4 |
| | | **Printed** | | | | | |
| 29 | 13 | Carriage, PETG (H2D, on the bed's diagonal; about 100 g each) (filament at $20/kg) | printed | stl/carriage.stl | $2.00 | $26.00 | 8 |
| 30 | 6 | Hold-downs (2) and tensioner blocks (4), PETG (filament) | printed | stl/hold_down.stl, stl/tensioner_block.stl | $0.40 | $2.40 | 4,9 |
| 31 | 12 | Auger blank, PETG (the auger's outside, hollow; fill with salt to about 200 g per module) (filament) | printed | stl/auger_blank.stl | $1.00 | $12.00 | 10 |
| 32 | 12 | Mounting plate (Sam's Oct 8 Onshape part) and auger cap (PR #170), printed for modules 2-13 (filament) | printed | Onshape 581956d5; reference/auger-cap-threaded.step | $0.80 | $9.60 | 10 |
| | | **Electronics** | | | | | |
| 33 | 2 | [Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME](https://www.adafruit.com/product/158) (verified 2026-10-10 (v1 BoM)) | Adafruit | 158 | $2.00 | $4.00 | 9 |
| 34 | 14 | [Neodymium disc magnet D42-N52, 1/4 x 1/8 in (13 index + 1 home)](https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet) (verified 2026-10-10 (v1 BoM)) | K&J Magnetics | D42-N52 | $0.52 | $7.28 | 8 |
| 35 | 1 | [Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio)](https://www.adafruit.com/product/5291) (estimate, not verified) | Adafruit | 5291 | $15.00 | $15.00 | 11 |
| 36 | 1 | [Interface board: 74AHCT125 (3.3 V GPIO to 5 V step/dir/enable), 3 x 10k pull-ups to 3.3 V, screw terminals, perfboard](https://www.adafruit.com/product/1787) (estimate, not verified) | Adafruit | 1787 | $6.00 | $6.00 | 11 |
| 37 | 1 | [E-stop GCX1136 (22 mm, NC, twist to release) + enclosure; breaks the 48 V feed to the driver](https://www.automationdirect.com/pn/GCX1136) ($21 + $9 box; verified 2026-10-10 (v1 BoM)) | AutomationDirect | GCX1136 | $30.00 | $30.00 | 11 |
| 38 | 1 | Electronics board, 1/4 in plywood 420 x 300 (estimate, not verified) | Home Depot |  | $6.00 | $6.00 | 11 |
| 39 | 1 | [IEC C14 inlet with switch + fuse drawer (Qualtek 719W-UEL3BR51)](https://www.digikey.com/en/products/detail/qualtek/719W-UEL3BR51/23019206) (verified 2026-10-10 (v1 BoM)) | Digi-Key | 719W-UEL3BR51 | $7.66 | $7.66 | 11 |
| 40 | 1 | [18 AWG stranded hook-up wire, 25 ft (48 V and motor)](https://www.digikey.com/en/products/result?keywords=18UL1007STRBLA25) (verified 2026-10-10 (v1 BoM)) | Digi-Key | 18UL1007STRBLA25 | $14.57 | $14.57 | 11 |
| | | **Module** | | | | | |
| 41 | 1 | [Module 1: mounting plate (Sam's Oct 8 Onshape design), printed](https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f) (existing) | lab | Onshape 581956d5 | $0.00 | $0.00 | 10 |
| 42 | 1 | Module 1: auger, threaded storage, and cap (lab design, PR #170) (existing) | lab | reference/auger-*.step | $0.00 | $0.00 | 10 |
| 43 | 1 | Electronics carriage (Sam's Oct 8), shown docked at the station for reference (existing) | lab | Onshape 581956d5 | $0.00 | $0.00 | 10 |
| | | **Tools** | | | | | |
| 3 | 1 | [Roller chain breaker, #25-#60 (Dura-Roll #1)](https://surpluscenter.com/1-roller-chain-breaker-for-25-60-pitch/) (verified 2026-10-13) | Surplus Center | 100115 | $17.20 | $17.20 | 6,7 |
| | | **Test** | | | | | |
| 44 | 1 | [Digital indicator 0-1 in / 0.01 mm with arm and magnetic base (index, lift, sag tests)](https://www.penntoolco.com/igaging-digital-indicator-universal-arm-magnetic-base-set-35-520) (verified 2026-10-10 (v1 BoM)) | Penn Tool Co | iGaging 35-520 | $119.95 | $119.95 | 12 |
| 45 | 1 | [Digital hanging scale 50 kg (torque lever, push-up and snap forces; a 50 N push-pull gauge is better if the lab has one)](https://etekcity.com/products/luggage-scale-el11) (verified 2026-10-10 (v1 BoM)) | Etekcity | EL11 | $10.99 | $10.99 | 12 |
| 46 | 1 | [ADXL343 accelerometer breakout (transit vibration)](https://www.adafruit.com/product/4097) (verified 2026-10-10 (v1 BoM)) | Adafruit | 4097 | $5.95 | $5.95 | 12 |
| 47 | 3 | Table salt, 26 oz (fills the 12 auger blanks to working mass) (estimate, not verified) | grocery |  | $1.50 | $4.50 | 12 |

## Notes

**Before cutting the chain, measure it.** ANSI #35 has a 0.200 in (5.08 mm) bushing and 0.188 in (4.78 mm) between the
inner plates. ISO 06B has the same 3/8 in pitch but a 6.35 mm roller and 5.72 mm between the plates, and the two don't mix.
(ISO 06C *is* ANSI 35.) The 3 ft box already on the ME order is 96 links, 8 short of one v2 loop: keep it as spares.

**A-1 links: Nitro's hole is 0.133 in (M3), Red Boar's is 0.10 in (M2.5).** The carriage takes M3 inserts. If you buy Red
Boar's instead (25-pack $92.76), use M2.5 x 6 screws and M2.5 inserts, or drill the tabs to 3.2 mm.

**Sprocket phase.** On each shaft, key the front sprocket and leave the back one's key out. Bolting the carriages across
both chains (step 8) sets the back sprocket's phase. Then lock it with both set screws on the round of the shaft and spot a
dimple under each one. A 32T tooth is 11.25 deg, so a keyed back sprocket would land up to 4.8 mm out of step.

**Shafts are keyed 1018, not hardened**, so the set screws bite. Cutting 3 x 403 + 427 mm from 72 in leaves about 190 mm.

**Shop work:** cut and drill the two side plates from `dxf/` (or upload the DXFs to SendCutSend for a quote); re-bore the
motor's 15T sprocket from 1/2 in to 14 mm H7 and broach a 5 mm keyway; tap the eight M5 holes for the tensioner blocks.

**Prices** are as listed on 2026-10-13 by vendor (`verified`); lines carried over from the v1 BoM were verified on
2026-10-10; generic hardware is `estimate`. USA Roller Chain still has a $300 web minimum, which is why the sprockets come
from Surplus Center.

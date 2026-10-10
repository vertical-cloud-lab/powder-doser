# Bill of materials: chain-carousel test rig v0

Every line is a real, orderable part (or one of the lab's own). Quantities of modelled parts are counted from the CAD (`layout.placements()`), so this table and the Onshape assembly agree. Prices are USD as listed on 2026-10-10 and will drift. **Step** is the assembly step that uses the line ([ASSEMBLY.md](ASSEMBLY.md)). `bom.csv` has the same data.

**Total $919.79; rig without test gear $830.79.** The NEMA 34 and module 1 are already in the lab and count as $0.

| # | Qty | Part | Vendor | Part no. | Unit | Ext. | Step |
|---|---|---|---|---|---|---|---|
| | | **Chain** | | | | | |
| 1 | 1 | [ANSI #35 roller chain, 3 ft (96 pitches) + 2 connecting links](https://www.amazon.com/Aobbmok-Roller-Chain-Connecting-Replacements/dp/B0C1YTF613/) (1 box (on the ME order)) | Amazon (Aobbmok) | B0C1YTF613 | $7.99 | $7.99 | 8 |
| 2 | 12 | [#35 A-1 attachment connecting link (bent tab, 1 hole), replaces 12 riveted outer links](https://redboarchain.com/products/35-a1-c-l-attachment-connecting-link-for-35-roller-chain) (each) | Red Boar Chain | 35 A1 C/L | $21.75 | $261.00 | 8 |
| | | **Tools** | | | | | |
| 3 | 1 | [#35 chain breaker / pin press (removes the 11 outer links the A-1 links replace)](https://www.amazon.com/s?k=%2335+roller+chain+breaker) (tool) | Amazon |  | $15.00 | $15.00 | 8 |
| | | **Chain** | | | | | |
| 4 | 1 | [Sprocket 35B19, 19T ANSI 35, B hub, bored 14 mm H7 + 5 mm keyway (NEMA 34 shaft)](https://usarollerchain.com/products/35b19-sprocket) (stock bore; bore + keyway in the BYU shop) | USA Roller Chain | 35B19 | $14.99 | $14.99 | 6 |
| 5 | 1 | [Idler sprocket #35 19T with ball bearing, 1/2 in bore](https://www.amazon.com/HEAVY-ROLLER-CHAIN-SPROCKET-IDLER/dp/B07LDKCN1X) (each) | Amazon | B07LDKCN1X | $7.99 | $7.99 | 5 |
| | | **Drive** | | | | | |
| 6 | 1 | [NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 14 mm keyed shaft](https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000) (already bought by UofU) | StepperOnline | 34HS59-6004D-E1000 | $0.00 | $0.00 | 3 |
| 7 | 1 | Key 5 x 5 x 25 mm (ships with the motor) (with motor) | StepperOnline |  | $0.00 | $0.00 | 6 |
| 8 | 1 | [Motor plate, 6061 aluminium 1/4 in x 6 in x 6 in, cut to 140 x 140 and drilled (DXF in dxf/)](https://www.mcmaster.com/89015K251/) (1 piece) | McMaster-Carr | 89015K251 | $22.00 | $22.00 | 3 |
| 9 | 1 | [Closed-loop stepper driver CL86T V4.1 (24-80 VDC)](https://www.omc-stepperonline.com/closed-loop-stepper-driver-0-8-2a-18-80vac-24-110vdc-for-nema-34-stepper-motor-cl86t) (each) | StepperOnline | CL86T | $47.43 | $47.43 | 12 |
| 10 | 1 | [Power supply Mean Well LRS-350-36 (36 V, 9.7 A)](https://www.digikey.com/en/products/detail/mean-well-usa-inc/LRS-350-36/7705124) (each) | Digi-Key | LRS-350-36 | $40.00 | $40.00 | 12 |
| | | **Frame** | | | | | |
| 11 | 2 | [2020 T-slot extrusion, 1050 mm (long rails)](https://us.misumi-ec.com/vona2/detail/110302683830/) (cut to length) | Misumi | HFS5-2020-1050 | $13.00 | $26.00 | 1 |
| 12 | 5 | [2020 T-slot extrusion, 690 mm (cross members)](https://us.misumi-ec.com/vona2/detail/110302683830/) (cut to length) | Misumi | HFS5-2020-690 | $9.00 | $45.00 | 1 |
| 13 | 4 | [2020 T-slot extrusion, 230 mm (legs)](https://us.misumi-ec.com/vona2/detail/110302683830/) (cut to length) | Misumi | HFS5-2020-230 | $4.00 | $16.00 | 2 |
| 14 | 24 | [2020 corner bracket with M5 screws and T-nuts](https://www.amazon.com/s?k=2020+corner+bracket+m5) (20-pack ~$12) | Amazon |  | $0.60 | $14.40 | 1 |
| 15 | 4 | [Leveling foot, M5 stud (into the leg's centre bore, tapped M5)](https://www.amazon.com/s?k=m5+leveling+feet+2020+extrusion) (4-pack ~$8) | Amazon |  | $2.00 | $8.00 | 2 |
| 16 | 1 | [Deck, HDPE 1/2 in, 48 x 48 in sheet cut to 1050 x 740 (DXF in dxf/)](https://www.mcmaster.com/8619K478/) (1 sheet) | McMaster-Carr | 8619K478 | $165.00 | $165.00 | 4 |
| | | **Fasteners** | | | | | |
| 17 | 1 | [Hex bolt 1/2-13 x 2-1/2 in (idler stud)](https://www.mcmaster.com/92620A724/) (each) | McMaster-Carr | 92620A724 | $1.50 | $1.50 | 5 |
| 18 | 1 | [Nylon-insert locknut 1/2-13](https://www.mcmaster.com/95615A140/) (each) | McMaster-Carr | 95615A140 | $0.50 | $0.50 | 5 |
| 19 | 1 | [Washer 1/2 in](https://www.mcmaster.com/98023A033/) (each) | McMaster-Carr | 98023A033 | $0.20 | $0.20 | 5 |
| 20 | 4 | [M5 x 18 socket head screw (motor flange into the M5-tapped plate)](https://www.mcmaster.com/91292A126/) (pack of 50) | McMaster-Carr | 91292A126 | $0.25 | $1.00 | 3 |
| 21 | 4 | [M5 x 20 flat head screw + nut (motor plate up into the deck)](https://www.mcmaster.com/92125A212/) (pack of 25) | McMaster-Carr | 92125A212 | $0.30 | $1.20 | 4 |
| 22 | 24 | [M5 x 25 flat head screw (deck to frame)](https://www.mcmaster.com/92125A214/) (pack of 25) | McMaster-Carr | 92125A214 | $0.30 | $7.20 | 4 |
| 23 | 24 | [M5 drop-in T-nut, 2020 slot 6](https://www.amazon.com/s?k=2020+drop+in+t+nut+m5) (100-pack ~$10) | Amazon |  | $0.10 | $2.40 | 4 |
| 24 | 1 | [M5 x 40 socket head screw + nut (tensioner jack screw)](https://www.mcmaster.com/91292A135/) (each) | McMaster-Carr | 91292A135 | $0.40 | $0.40 | 5 |
| 25 | 12 | [M3 x 10 button head screw (carriage to A-1 tab)](https://www.mcmaster.com/92095A181/) (pack of 100) | McMaster-Carr | 92095A181 | $0.12 | $1.44 | 9 |
| 26 | 12 | [M3 heat-set insert, 5.7 mm long](https://www.mcmaster.com/94180A333/) (pack of 100) | McMaster-Carr | 94180A333 | $0.20 | $2.40 | 9 |
| 27 | 4 | [M4 x 30 socket head screw + nylon locknut (hold-down blocks)](https://www.mcmaster.com/91292A120/) (pack of 50) | McMaster-Carr | 91292A120 | $0.25 | $1.00 | 10 |
| 28 | 1 | [M5 x 70 socket head screw + nylon locknut (hinge pin)](https://www.mcmaster.com/91292A139/) (each) | McMaster-Carr | 91292A139 | $0.60 | $0.60 | 11 |
| | | **Printed** | | | | | |
| 29 | 12 | Carriage base plate, printed PETG (H2D bed; ~125 g each) (filament) | printed | carriage.stl | $2.50 | $30.00 | 9 |
| 30 | 3 | Idler slider, spacer and tensioner block, printed PETG (filament) | printed | idler_*.stl | $0.50 | $1.50 | 5 |
| 31 | 2 | Hold-down block, printed PETG (filament) | printed | hold_down.stl | $0.30 | $0.60 | 10 |
| 32 | 2 | Hall sensor holder, printed PETG (filament) | printed | hall_holder.stl | $0.05 | $0.10 | 7 |
| | | **Electronics** | | | | | |
| 33 | 2 | [A3144 hall-effect switch (open collector), index + home](https://www.amazon.com/s?k=a3144+hall+effect+sensor) (10-pack ~$6) | Amazon |  | $0.50 | $1.00 | 7 |
| 34 | 13 | [Neodymium disc magnet 6 x 3 mm N52 (12 index + 1 home)](https://www.amazon.com/s?k=6x3mm+n52+magnets) (50-pack ~$8) | Amazon |  | $0.15 | $1.95 | 9 |
| 35 | 1 | [Raspberry Pi 4 Model B (any Pi with pigpio works; the lab's spare)](https://www.adafruit.com/product/4296) (each) | Adafruit | 4296 | $35.00 | $35.00 | 12 |
| 36 | 1 | [Interface board: ULN2803A (step/dir/enable to the CL86T opto inputs), 3 x 10k pull-ups to 3.3 V, screw terminals, perfboard](https://www.digikey.com/en/products/detail/texas-instruments/ULN2803ADWR/277680) (kit) | Digi-Key | ULN2803A | $4.00 | $4.00 | 12 |
| 37 | 1 | [E-stop mushroom switch, NC, in enclosure (breaks the 36 V DC feed to the driver)](https://www.amazon.com/s?k=emergency+stop+switch+enclosure) (each) | Amazon |  | $15.00 | $15.00 | 12 |
| 38 | 1 | Electronics board, 1/4 in plywood 420 x 300 (offcut) | Home Depot |  | $6.00 | $6.00 | 12 |
| 39 | 1 | Wire, fuses and connectors: 18 AWG (36 V), 22 AWG (signals), IEC C14 inlet with fuse + switch, 4-pin motor + encoder extension (lot) | Amazon |  | $25.00 | $25.00 | 12 |
| | | **Module** | | | | | |
| 40 | 1 | [Mounting plate (Sam's Oct 8 Onshape design), printed](https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f) (existing) | lab | Onshape 581956d5 | $0.00 | $0.00 | 11 |
| 41 | 2 | Auger, threaded storage, and cap (lab design, PR #170) (existing) | lab | auger.step | $0.00 | $0.00 | 11 |
| | | **Test** | | | | | |
| 42 | 1 | [Digital dial indicator 0-12.7 mm x 0.01 mm with magnetic base (lift and sag tests)](https://www.amazon.com/s?k=digital+dial+indicator+magnetic+base) (each) | Amazon |  | $30.00 | $30.00 | 13 |
| 43 | 1 | [Push-pull force gauge 50 N (station push-up, drag force)](https://www.amazon.com/s?k=digital+force+gauge+50n) (each) | Amazon |  | $40.00 | $40.00 | 13 |
| 44 | 1 | [ADXL345 accelerometer breakout (carriage vibration in transit)](https://www.adafruit.com/product/4097) (each) | Adafruit | 4097 | $8.00 | $8.00 | 13 |
| 45 | 11 | Dummy module mass: 250 g bag of table salt (or 2 x 125 g steel bars) per carriage (each) | grocery |  | $1.00 | $11.00 | 13 |

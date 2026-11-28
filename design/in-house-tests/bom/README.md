# Bill of materials: the ten in-house test apparatuses

**Status: priced 2026-11-28, nothing ordered.** Quantities follow [`../SPEC.md`](../SPEC.md). Prices and stock were read on
vendor pages on 2026-11-28 for delivery to Provo, UT; they change, so re-check at checkout. Every line, with its URL, how it
was checked and an alternate, is in [`bom.csv`](bom.csv). Lead times per line and per apparatus are in
[`lead_times.json`](lead_times.json).

## In short

- **Grand total: $1,309.76** from verified prices on 49 of 81 lines. The **working total is $1,322.69**:
  it adds the verified price of an alternate for 2 unpriced lines. **30 lines have no verified price**
  (most are Amazon and McMaster items, see [How it was checked](#how-it-was-checked)); price them at checkout.
- **Without the bench computer** (Pi 5, supply, cooler, card: $192.00): $1,117.76 verified, $1,130.69 working.
- **Lead time.** Ordered on Sat 28 Nov, the verified lines are in stock and arrive by about day 9 by ground, or about day 5
  with 2-day shipping from DigiKey and Adafruit. Exceptions: the stage micrometer (T4-2) and the barrel adapter (S20) are
  out of stock, and ServoCity (S22c, S22d) shows no stock text. The longest leads are the **IMX477 camera** for test 4
  (Arducam B0240E from UCTRONICS, about day 4-14: the
  page shows 'Add to Cart' but not where it ships from), the **FC-1 bare boards** (test 10; OSH Park Super Swift, about day 7-11) and the
  **Lab Alley salts** (test 6; 5-10 days, one is hazmat). The official Pi HQ Camera is out or backordered everywhere checked.
- **Spec changes** agreed on 2026-11-28 are listed in [Spec changes for the CAD and SPEC](#spec-changes-for-the-cad-and-spec):
  Pi 5 8 GB, Pico 2 WH, SHT45 without membrane, Arducam IMX477 camera, 15.5 kg-cm servo, DIY linear stage, 1/4 in anvil,
  0.91 mm coupons, NEMA 11 D-shaft, 12 V JF-0530B.

## How it was checked

- **DigiKey and Pololu:** product pages read in a headed Chrome whose traffic left through the lab's Pi (BYU network, Utah),
  08:46-09:23 UTC, 48 page loads in all. DigiKey then started showing a Cloudflare "Verify you are human" box; we did not
  click through it, so a few DigiKey lookups (line cord, barrel adapter, microSD, the ADA4530-1 for the PCB) were not done.
- **Adafruit, PiShop.us, SparkFun, AmScope, Uline, Target, Lab Alley:** product pages read with a plain fetch from the
  runner (stock text is the datacenter's view).
- **Amazon** answered the browser with "Access restricted. Continued access by an unauthorized AI agent violates Amazon's
  Conditions of Use", so we stopped. Amazon lines carry an ASIN taken from a search-result URL only: no price, stock or
  delivery date. The one Amazon page we opened (the linear-stage candidate) said "Currently unavailable".
- **McMaster** answered the browser with "Access has been restricted" and serves empty product pages to plain fetches.
  Part numbers come from McMaster's own category-page text; only two prices were visible (9208K136, 91292A113).
- **Follow-up, 09:25-09:35 UTC, plain fetch only:** camera alternatives at UCTRONICS (Arducam's store; arducam.com product
  pages returned 403), PiShop.us, Adafruit, SparkFun, CanaKit and Pimoroni; DIY-stage parts at Pololu, Adafruit, SparkFun,
  ServoCity and McMaster (McMaster category pages showed no part-number rows for 8 mm shafts or bearings).
- The session's web-search allowance ran out early, so a few items have no candidate at all. Each unverified line in
  `bom.csv` has a `search_to_run`. No part number, price or URL in this folder was guessed.

## Spec changes for the CAD and SPEC

Agreed with the coordinator on 2026-11-28, who is applying them to the CAD; `../SPEC.md` should follow. Reasons: stock on
2026-11-28, or parts that only come in these sizes.

| Item | SPEC said | Now (BOM line) | What changes in the CAD or wiring |
|---|---|---|---|
| Tapper anvil (test 2) | 304 disc 25 x 3 mm | 304 disc 1 in x **1/4 in** (25.4 x 6.35 mm), McMaster 9208K136 (T2-5) | Anvil seat 3.35 mm deeper; drop height stays 3.0 mm |
| Steel coupons (tests 3, 9) | 304, 1 mm | 304 brushed #4, **0.036 in (0.91 mm)**, McMaster 9748K42 (T3-4) | Coupon pocket depth 0.91 - 0.2 = 0.71 mm |
| Cam-tapper motor (test 2) | NEMA 11, round shaft | NEMA 11 28 x 32 mm, 5 mm **D-shaft** (0.5 mm flat, 20 mm long), Pololu 1205 (T2-2) | Cam bore gets the flat |
| Cup tapper (test 5) | JF-0530B | JF-0530B **12 V**, Adafruit 412 (T5-2) | DRV8871 #2 motor supply from the 12 V rail (S18); the DRV8871 needs 6.5-45 V |
| Tilt-table servo (test 3) | 20 kg-cm metal gear | **15.5 kg-cm** (216 oz-in at 6 V), all-metal gears, FEETECH FS5115M, Pololu 3426 (T3-1) | Check its body and spline in the servo mount; the plate needs well under 1 kg-cm |
| Bench computer | Pi 5, 4 GB | Pi 5 **8 GB**, SC1432 (S01) | None (same board); 4 GB is out of stock everywhere checked |
| Accessory controller | Pico 2 W | **Pico 2 WH** (headers fitted), SC1634 (S11) | Headers are soldered; plan for a socket or jumper wires |
| RH/T sensors (x7) | SHT45, PTFE membrane | SHT45 **without membrane**, Adafruit 5665 (S14, T6-7) | Same board size and address (0x44); keep it away from the sample dish |
| Microscope camera (test 4) | Pi HQ Camera, C/CS | **Arducam B0240E**, IMX477 12.3 MP, C/CS with C-CS adapter and tripod mount (S07) | Check its board outline and mounting holes against the stand; Pi 5 cable included |
| Linear stage (tests 8, 9) | Bought 100 mm T8 stage + NEMA 17 | **DIY**: Pololu 2268 NEMA 17 with 282 mm Tr8x8(P2) screw and flanged nut (8 mm lead), two 8 x 200 mm shafts, four 8 x 15 x 24 mm linear bearings, one 608 end bearing (S22a-S22d) | Printed motor block, end block and carriage (coordinator); cut the screw, or use Pololu 2689 (18 cm screw) |

## Totals

| Apparatus | Verified prices | Working total | Lines without a price |
|---|---|---|---|
| 1. Heap angle of repose | $0.00 | $0.00 | 1 (T1-1) |
| 2. Bulk and tapped density | $80.30 | $80.30 | 2 (T2-3, T2-4) |
| 3. Tilting plate | $44.01 | $44.01 | 4 (T3-3, T3-4, T3-5, T3-6) |
| 4. PSD and shape from images | $27.13 | $27.13 | 4 (T4-3, T4-4, T4-5, T4-6) |
| 5. Orifice cup | $24.95 | $24.95 | 2 (T5-4, T5-5) |
| 6. Humidity chambers | $415.63 | $415.63 | 1 (T6-6) |
| 7. Rotating drum | $0.00 | $0.00 | 2 (T7-1, T7-2) |
| 8. Unconfined strength | $20.45 | $20.45 | 2 (T8-3, T8-4) |
| 9. Blade spreading | $0.00 | $0.00 | 3 (T9-2, T9-3, T9-4) |
| 10. Faraday cup | $134.92 | $134.92 | 3 (T10-1, T10-2, T10-3) |
| Shared hardware (all of 0.2 and 0.3) | $562.37 | $575.30 | 6 (S04, S09, S19, S26, S27, S28) |
| of which: bench computer (S01-S04) | $192.00 | $192.00 | 1 (S04) |
| **Grand total, with the bench computer** | $1,309.76 | $1,322.69 | 30 (S04, S09, S19, S26, S27, S28, T1-1, T2-3, T2-4, T3-3, T3-4, T3-5, T3-6, T4-3, T4-4, T4-5, T4-6, T5-4, T5-5, T6-6, T7-1, T7-2, T8-3, T8-4, T9-2, T9-3, T9-4, T10-1, T10-2, T10-3) |
| **Grand total, without the bench computer** | $1,117.76 | $1,130.69 | 29 (S09, S19, S26, S27, S28, T1-1, T2-3, T2-4, T3-3, T3-4, T3-5, T3-6, T4-3, T4-4, T4-5, T4-6, T5-4, T5-5, T6-6, T7-1, T7-2, T8-3, T8-4, T9-2, T9-3, T9-4, T10-1, T10-2, T10-3) |

- **Verified prices**: lines whose price was read on the vendor page. **Working total**: adds the verified price of an
  alternate where the main line has none (shown in brackets in the tables). The FC-1 parts ($72.00) come from
  `../pcb/bom.csv` (qty-1 DigiKey prices); the bare boards are priced from OSH Park's published rate.
- Lines without a price are left out of both. Most are small hardware; the larger unknowns are the LED tracing pad (S09),
  the hardened 8 mm shafts (S22b; ServoCity stainless shafts priced as the fallback) and the McMaster metal stock.
- Lines marked as likely already in the lab (S04, S12, S19, S20, S27, T1-1, T3-6, T4-3, T6-4, T6-6) add $72.90 to the verified total; skip them if found.

## Per apparatus

Lead column: calendar days from an order on Sat 2026-11-28 to arrival in Provo, then the stock text seen. Prices in
brackets are a verified alternate's, used for the working total only.

### 1. Heap angle of repose

Uses from the shared hardware: silhouette camera, backlight, bench Pi, in-chamber tripod, pan adapter and riser set (printed). Own parts: $0.00 verified, $0.00 working; longest lead with shared parts:
9 days (S01, S02, S03, S05 and others).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T1-1 | Spray adhesive or thin double-sided tape (powder layer on pedestal tops) | 1 x can | Amazon: not verified | not verified | - | lab stock |

### 2. Bulk and tapped density

Uses from the shared hardware: silhouette camera, backlight, Tic T500, 12 V rail, pan adapter (printed). Own parts: $80.30 verified, $80.30 working; longest lead with shared parts:
9 days (T2-6, S01, S02, S03 and others).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T2-1 | Graduated cylinder, 10 mL, Class A, glass hex base | 2 (minimum 2) | Uline [S-26274](https://www.uline.com/Product/Detail/S-26274/Labware/Glass-Graduated-Cylinders-10-mL) | $12.00 | $24.00 | 3-6 d; 'IN STOCK SHIPS TODAY' |
| T2-2 | NEMA 11 stepper for the cam tapper | 1 | Pololu [1205](https://www.pololu.com/product/1205) | $39.92 | $39.92 | 3-4 d; 200 in stock |
| T2-3 | Hardened linear shaft, 6 mm x 100 mm, tapped M3 both ends | 2 | McMaster-Carr [4316N102](https://www.mcmaster.com/4316N102/) | not verified | - | 3-4 d; not verified |
| T2-4 | PTFE film tape, 1/2 in x 15 ft, 0.005 in, acrylic adhesive | 1 x roll | McMaster-Carr [6305A11](https://www.mcmaster.com/6305A11/) | not verified | - | 3-4 d; not verified |
| T2-5 | 304 stainless disc, 1 in dia x 1/4 in thick (anvil) | 1 x pack of 5 | McMaster-Carr [9208K136](https://www.mcmaster.com/9208K136/) | $13.12 | $13.12 | 3-4 d; In stock |
| T2-6 | Reflective optical sensor TCRT5000 (cam-turn counter) | 2 | DigiKey [TCRT5000 (751-1033-5-ND)](https://www.digikey.com/en/products/detail/vishay-semiconductor-opto-division/TCRT5000/1681167) | $1.63 | $3.26 | 4-9 d; In-Stock: 10,294 |

### 3. Tilting plate: wall friction and layer start angle

Uses from the shared hardware: silhouette camera, backlight, accessory Pico, 5 V regulator, STEMMA QT chain. Own parts: $44.01 verified, $44.01 working; longest lead with shared parts:
9 days (T3-2, S01, S02, S03 and others).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T3-1 | Servo, 15.5 kg-cm, all-metal gears (tilt table) | 1 | Pololu [3426](https://www.pololu.com/product/3426) | $32.06 | $32.06 | 3-4 d; 683 in stock |
| T3-2 | LSM6DSOX 6-DoF IMU, STEMMA QT | 1 | DigiKey [4438 (1528-4438-ND)](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4438/11497501) | $11.95 | $11.95 | 4-9 d; In-Stock: 113 |
| T3-3 | Steel shaft 5 mm x 100 mm (hinge pin) | 1 | McMaster-Carr [1327K51](https://www.mcmaster.com/1327K51/) | not verified | - | 3-4 d; not verified |
| T3-4 | 304 stainless sheet, 0.036 in (0.91 mm) x 6 x 12 in, brushed #4 | 1 | McMaster-Carr [9748K42](https://www.mcmaster.com/9748K42/) | not verified | - | 3-4 d; not verified |
| T3-5 | Glass plate 75 x 50 x 1 mm (glass coupon) | 1 x pack | vendor not chosen: not verified | not verified | - | not verified |
| T3-6 | Steel flat washers M8 (DIN 125), for 5 g and 15 g lids | 1 x pack | McMaster-Carr: not verified | not verified | - | not verified |

### 4. PSD and shape from images

Uses from the shared hardware: IMX477 camera (S07), zoom lens, backlight (masked), bench Pi; the doser's ERM shakes the sieve cup. Own parts: $27.13 verified, $27.13 working; longest lead with shared parts:
14 days (S07).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T4-1 | Microscope mechanical stage, X-Y | 1 | AmScope [MS90](https://amscope.com/products/ms90) | $10.14 | $10.14 | 4-7 d; 'In Stock' (sale price, was $28.99) |
| T4-2 | Stage micrometer, 1 mm / 100 divisions (0.01 mm) | 1 | AmScope [MR095](https://amscope.com/products/mr095) | $16.99 | $16.99 | unknown; 'Out of Stock' / 'Sold Out' |
| T4-3 | Plain glass slides 75 x 25 mm (sample slides) | 1 x pack | vendor not chosen: not verified | not verified | - | not verified |
| T4-4 | 316 stainless wire cloth, 100 x 100 mesh (0.006 in opening), 12 x 12 in | 1 | McMaster-Carr [9319T183](https://www.mcmaster.com/9319T183/) | not verified | - | 3-4 d; not verified |
| T4-5 | 316 stainless wire cloth, 200 x 200 mesh (0.0029 in = 74 um), 12 x 12 in | 1 | McMaster-Carr [9319T191](https://www.mcmaster.com/9319T191/) | not verified | - | 3-4 d; not verified |
| T4-6 | M3 x 0.5 threaded rod, stainless, 100-150 mm, and M3 nuts (focus lead screw) | 1 x rod + pack of nuts | McMaster-Carr: not verified | not verified | - | not verified |

### 5. Orifice cup

Uses from the shared hardware: silhouette camera, backlight, accessory Pico, 12 V and 5 V rails, in-chamber tripod. Own parts: $24.95 verified, $24.95 working; longest lead with shared parts:
9 days (T5-1, T5-2, T5-3, S01 and others).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T5-1 | Micro servo, metal gear, MG90D (orifice gate) | 1 | Adafruit [1143](https://www.adafruit.com/product/1143) | $9.95 | $9.95 | 4-9 d; In stock |
| T5-2 | Push-pull solenoid JF-0530B, 12 V (cup tapper) | 1 | Adafruit [412](https://www.adafruit.com/product/412) | $7.50 | $7.50 | 4-9 d; In stock |
| T5-3 | DRV8871 motor driver breakout (DRV8871 #2) | 1 | Adafruit [3190](https://www.adafruit.com/product/3190) | $7.50 | $7.50 | 4-9 d; In stock |
| T5-4 | Drill bit set 1-6 mm in 0.1 mm steps (51 pcs) | 1 x set | Amazon [B0895ZYLZ3](https://www.amazon.com/dp/B0895ZYLZ3) | not verified | - | 1-4 d; not verified |
| T5-5 | Gage pins 0.100 in and 0.200 in, class ZZ (optional check) | 2 | McMaster-Carr: not verified | not verified | - | not verified |

### 6. Humidity chambers

Uses from the shared hardware: bench Pi (the mux sits on its I2C), ambient SHT45. Own parts: $415.63 verified, $415.63 working; longest lead with shared parts:
10 days (T6-2, T6-3, T6-4, T6-5).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T6-1 | Airtight food container, 4.7 cup (1.1 L), latched gasket lid | 5 | Target [TCIN 52119450](https://www.target.com/p/rubbermaid-4-7-cup-brilliance-food-storage-container/-/A-52119450) | $9.59 | $47.95 | 2-6 d; 'In Stock' (datacenter view) |
| T6-2 | Magnesium chloride hexahydrate, lab grade, 500 g (33 % RH) | 1 x 500 g | Lab Alley [C5020-500G](https://www.laballey.com/products/magnesium-chloride-crystal-lab-grade) | $56.49 | $56.49 | 5-10 d; In stock |
| T6-3 | Magnesium nitrate hexahydrate, lab grade, 500 g (53 % RH) | 1 x 500 g | Lab Alley [C5047-500g](https://laballey.com/products/magnesium-nitrate-crystal-lab) | $50.47 | $50.47 | 5-10 d; 'In stock' |
| T6-4 | Sodium chloride, lab grade, 500 g (75 % RH) | 1 x 500 g | Lab Alley [SOCHLGL-500G](https://www.laballey.com/products/sodium-chloride-lab) | $70.90 | $70.90 | 5-10 d; In stock |
| T6-5 | Potassium chloride, lab grade, 500 g (84 % RH) | 1 x 500 g | Lab Alley [C6330-500g](https://www.laballey.com/products/potassium-chloride-granular-lab-grade) | $69.70 | $69.70 | 5-10 d; In stock |
| T6-6 | Indicating silica gel, at least 1 lb | 1 x 1 lb | vendor not chosen: not verified | not verified | - | not verified |
| T6-7 | SHT45 RH/T breakout, STEMMA QT (one per chamber) | 5 | DigiKey [5665 (1528-5665-ND)](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5665/17831054) | $12.50 | $62.50 | 4-9 d; In-Stock: 2,915 |
| T6-8 | STEMMA QT / Qwiic cable, 400 mm (chamber to mux) | 5 | DigiKey [5385 (1528-5385-ND)](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5385/16546436) | $1.50 | $7.50 | 4-9 d; In-Stock: 4,352 |
| T6-9 | I2C multiplexer PCA9548 (TCA9548A compatible), STEMMA QT | 1 | Adafruit [5626](https://www.adafruit.com/product/5626) | $6.95 | $6.95 | 4-9 d; In stock |
| T6-10 | Cable gland PG7, nylon, with locknut | 6 | DigiKey [CG-P-7](https://www.digikey.com/en/products/detail/adam-tech/CG-P-7/17736920) | $0.82 | $4.92 | 4-9 d; 1,278 In Stock (listing row) |
| T6-11 | Fan 25 x 25 x 6.5 mm, 5 V (optional, one per chamber) | 5 | DigiKey [MF25060V1-1000U-A99](https://www.digikey.com/en/products/detail/sunon-fans/MF25060V1-1000U-A99/10441399) | $7.65 | $38.25 | 4-9 d; 1,402 In Stock (listing row; tariff note) |

### 7. Rotating drum

Uses from the shared hardware: the doser's own stepper and gears turn the printed drum; silhouette camera. Own parts: $0.00 verified, $0.00 working; longest lead with shared parts:
9 days (S01, S02, S03, S05 and others).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T7-1 | Clear acrylic disc 50 mm x 2 mm (drum window) | 1 x pack of 30 | Amazon [B0DNSSHYV1](https://www.amazon.com/dp/B0DNSSHYV1) | not verified | - | 1-4 d; not verified |
| T7-2 | USB LED light bar, about 30 cm (low-angle light; also test 9) | 1 | Amazon [B081VLXDYC](https://www.amazon.com/dp/B081VLXDYC) | not verified | - | 1-4 d; not verified |

### 8. Unconfined strength

Uses from the shared hardware: DIY linear stage (S22a-S22d, printed blocks from the CAD), Tic T500, accessory Pico, STEMMA QT chain. Own parts: $20.45 verified, $20.45 working; longest lead with shared parts:
9 days (T8-1, T8-2, S01, S02 and others).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T8-1 | Load cell 100 g, mini bar (TAL221) | 1 | DigiKey [14727 (1568-14727-ND)](https://www.digikey.com/en/products/detail/sparkfun-electronics/14727/9555601) | $14.50 | $14.50 | 4-9 d; In-Stock: 394 |
| T8-2 | NAU7802 24-bit load-cell ADC, STEMMA QT | 1 | Adafruit [4538](https://www.adafruit.com/product/4538) | $5.95 | $5.95 | 4-9 d; In stock |
| T8-3 | Test weights 1-50 g (or slotted masses) for 6.4 / 16 / 32 / 64 g | 1 x set | vendor not chosen: not verified | not verified | - | not verified |
| T8-4 | Dowel pins 3 mm x 10-12 mm (split-mould alignment) | 1 x pack | McMaster-Carr: not verified | not verified | - | not verified |

### 9. Blade spreading

Uses from the shared hardware: DIY linear stage (S22a-S22d), Tic T500, limit switch, silhouette camera, LED bar from test 7. Own parts: $0.00 verified, $0.00 working; longest lead with shared parts:
9 days (S01, S02, S03, S05 and others).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T9-1 | 304 stainless coupons 100 x 30 mm | 0 | see T3-4: cut from the T3-4 sheet | - | - | 3-4 d; see T3-4 |
| T9-2 | Razor blades, stainless, pack of 100 (blade option) | 1 x pack of 100 | McMaster-Carr [3962A5](https://www.mcmaster.com/3962A5/) | not verified | - | 3-4 d; not verified |
| T9-3 | Feeler gauge set, metric, 13 blades 0.03-0.50 mm (has 0.10, 0.15, 0.20) | 1 x set | McMaster-Carr [2070A21](https://www.mcmaster.com/2070A21/) | not verified | - | 3-4 d; not verified |
| T9-4 | 304 stainless flat bar 1/16 x 1 in (ground blade option) | 1 x 1 ft | McMaster-Carr: not verified | not verified | - | not verified |

### 10. Faraday cup

Uses from the shared hardware: in-chamber tripod, accessory Pico (charge-amp reset), STEMMA QT chain. Own parts: $134.92 verified, $134.92 working; longest lead with shared parts:
11 days (T10-6).

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| T10-1 | Aluminium inner cup, about 40 mm dia x 50 mm | 1 | vendor not chosen: not verified | not verified | - | not verified |
| T10-2 | Aluminium outer can, about 70 mm dia x 80 mm, grounded | 1 | vendor not chosen: not verified | not verified | - | not verified |
| T10-3 | PTFE standoffs, M3, 10-20 mm (inner-cup insulators) | 3 | McMaster-Carr: not verified | not verified | - | not verified |
| T10-4 | BNC to BNC cable, 24 in | 1 | DigiKey [2249-C-24 (501-1016-ND)](https://www.digikey.com/en/products/detail/pomona-electronics/2249-C-24/603326) | $31.92 | $31.92 | 4-9 d; In-Stock: 1,125 |
| T10-5 | FC-1 charge-amplifier parts for one board (see ../pcb/bom.csv) | 1 x set | DigiKey [see ../pcb/bom.csv](../pcb/bom.csv) | $72.00 | $72.00 | 4-9 d; all fitted parts in stock per pcb/bom.csv; ADA4530-1ARZ 103 in stock (44 wk factory lead time) |
| T10-6 | FC-1 bare boards, 2 layers, 1.6 mm, 50 x 40 mm, set of 3 | 1 x set of 3 | OSH Park [2-layer Super Swift](https://docs.oshpark.com/services/) | $31.00 | $31.00 | 7-11 d; published rate '$10 per square inch, per set of 3', '4-5 business days'; free shipping |

## Shared hardware (SPEC 0.2 and 0.3)

$562.37 verified, $575.30 working. Used-by lists are in `bom.csv` (`used_by`).

**Bench computer**

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| S01 | Raspberry Pi 5, 8 GB (in place of 4 GB) | 1 | DigiKey [SC1432 (2648-SC1432-ND)](https://www.digikey.com/en/products/detail/raspberry-pi/SC1432/21658257) | $175.00 | $175.00 | 4-9 d; In-Stock: 18,731 (maximum purchase limit applies) |
| S02 | Raspberry Pi 27 W USB-C power supply, US plug, white | 1 | DigiKey [SC1153 (2648-SC1153-ND)](https://www.digikey.com/en/products/detail/raspberry-pi/SC1153/21658276) | $12.00 | $12.00 | 4-9 d; In-Stock: 6,777 |
| S03 | Raspberry Pi 5 Active Cooler | 1 | DigiKey [SC1148 (2648-SC1148-ND)](https://www.digikey.com/en/products/detail/raspberry-pi/SC1148/21658255) | $5.00 | $5.00 | 4-9 d; In-Stock: 31,125 |
| S04 | microSD card, 32 GB, A1 or A2 | 1 | Amazon [B08GY9NYRM (SanDisk Ultra 32 GB, A1)](https://www.amazon.com/dp/B08GY9NYRM) | not verified | - | 1-4 d; not verified |

**Cameras and light**

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| S05 | Raspberry Pi Camera Module 3 (standard, 75 deg) | 1 | DigiKey [SC1223 (2648-SC1223-ND; alias SC0872)](https://www.digikey.com/en/products/detail/raspberry-pi/SC1223/17278639) | $25.00 | $25.00 | 4-9 d; In-Stock: 859 |
| S06 | Raspberry Pi 5 camera cable, 300 mm | 2 | DigiKey [SC1129 (2648-SC1129-ND)](https://www.digikey.com/en/products/detail/raspberry-pi/SC1129/21658260) | $2.00 | $4.00 | 4-9 d; In-Stock: 1,676 |
| S07 | 12.3 MP IMX477 camera, C/CS mount (in place of the Pi HQ Camera) | 1 | UCTRONICS (Arducam store) [B0240E](https://www.uctronics.com/arducam-12-3mp-imx477-camera-module-w-c-cs-lens-mount-and-tripod-adapter-for-raspberry-pi.html) | $49.99 | $49.99 | 4-14 d; 'Add to Cart' (no stock count; out-of-stock items on the same site say 'Out of stock') |
| S08 | C/CS-mount zoom microscope lens, 0.12-1.8x | 1 | PiShop.us [SKU 734-2 (Waveshare 24229)](https://www.pishop.us/product/100x-industrial-microscope-lens-c-cs-mount-compatible-with-raspberry-pi-hq-camera-cs/) | $18.95 | $18.95 | 4-9 d; 'IN STOCK' |
| S09 | USB LED tracing pad, A5, dimmable | 1 | Amazon [B09VT7814N](https://www.amazon.com/dp/B09VT7814N) | not verified | - | 1-4 d; not verified |
| S10 | MOSFET driver breakout (backlight PWM) | 1 | Adafruit [5648](https://www.adafruit.com/product/5648) | $3.95 | $3.95 | 4-9 d; In stock |

**Accessory controller and I2C**

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| S11 | Raspberry Pi Pico 2 WH (Pico 2 W with headers) | 1 | DigiKey [SC1634 (2648-SC1634-ND)](https://www.digikey.com/en/products/detail/raspberry-pi/SC1634/26241087) | $8.00 | $8.00 | 4-9 d; In-Stock: 3,093 |
| S12 | USB-A to micro-B data cable, about 1 m | 1 x pack of 2 | Amazon [B01MUJJVOG (Anker PowerLine, 2-pack)](https://www.amazon.com/dp/B01MUJJVOG) | (alt $2.95) | ($2.95) | 1-4 d; not verified |
| S13 | Pololu Tic T500 stepper controller | 1 | Pololu [3135](https://www.pololu.com/product/3135) | $32.95 | $32.95 | 3-4 d; 65 in stock (status 'Rationed') |
| S14 | SHT45 RH/T breakout, STEMMA QT (bench ambient + spare) | 2 | DigiKey [5665 (1528-5665-ND)](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5665/17831054) | $12.50 | $25.00 | 4-9 d; In-Stock: 2,915 |
| S15 | STEMMA QT / Qwiic cable, 400 mm | 4 | DigiKey [5385 (1528-5385-ND)](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5385/16546436) | $1.50 | $6.00 | 4-9 d; In-Stock: 4,352 |
| S16 | STEMMA QT / Qwiic cable, 50 mm | 2 | Adafruit [4399](https://www.adafruit.com/product/4399) | $0.95 | $1.90 | 4-9 d; In stock (100 and 200 mm versions out of stock) |
| S17 | Jumper wires, female-female and female-male, 40 x 6 in each | 1 x set (266 + 826) | Adafruit [266 + 826](https://www.adafruit.com/product/266) | $7.90 | $7.90 | 4-9 d; 266: 32 in stock; 826: 50 in stock |

**Power**

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| S18 | 12 V 5 A desktop supply (accessory rail) | 1 | DigiKey [GST60A12-P1J (1866-2149-ND)](https://www.digikey.com/en/products/detail/mean-well-usa-inc/GST60A12-P1J/7703712) | $19.40 | $19.40 | 4-9 d; In-Stock: 4,613 |
| S19 | AC line cord, NEMA 5-15P to IEC C13, about 6 ft | 1 | lab stock: not verified | not verified | - | lab stock |
| S20 | 2.1 mm barrel jack to screw-terminal adapter | 1 | Adafruit [368](https://www.adafruit.com/product/368) | $2.00 | $2.00 | unknown; Out of stock |
| S21 | 5 V 3.2 A step-down regulator (servos, fans) | 1 | Pololu [3782](https://www.pololu.com/product/3782) | $23.95 | $23.95 | 3-4 d; 189 in stock |

**Universal linear stage**

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| S22a | NEMA 17 stepper with integrated lead screw and nut (DIY stage drive) | 1 | Pololu [2268](https://www.pololu.com/product/2268) | $105.52 | $105.52 | 3-4 d; 98 in stock |
| S22b | Hardened linear shaft, 8 mm x 200 mm | 2 | McMaster-Carr: not verified | (alt $4.99) | ($9.98) | 3-4 d; not verified (McMaster 'Linear Shafts' family has an 8 mm, hardened filter; no part-number rows visible to a fetch) |
| S22c | Linear ball bearing, 8 mm ID x 15 mm OD x 24 mm (LM8UU size) | 2 x pack of 2 | ServoCity [1612-0815-0024](https://www.servocity.com/linear-bearings/) | $4.99 | $9.98 | 4-9 d; price shown; stock not shown |
| S22d | Ball bearing 8 x 22 x 7 mm (608 size), lead-screw free end | 1 x pack of 2 | ServoCity [1600-0722-0008](https://www.servocity.com/8mm-id-x-22mm-od-non-flanged-ball-bearing-2-pack/) | $3.99 | $3.99 | 4-9 d; price shown; stock not shown |
| S23 | Limit switch (stage homing), lever | 2 | DigiKey [D2F-01L (SW154-ND)](https://www.digikey.com/en/products/detail/aratas-formerly-omron-components/D2F-01L/83264) | $1.44 | $2.88 | 4-9 d; In-Stock: 79,628 |

**Fasteners and wire**

| Line | Item | Qty | Vendor and part | Unit | Ext. | Lead (days), stock seen |
|---|---|---|---|---|---|---|
| S24 | Brass heat-set inserts, M3 x 4 mm, pack of 50 | 2 x pack of 50 | Adafruit [4255](https://www.adafruit.com/product/4255) | $5.95 | $11.90 | 4-9 d; In stock |
| S25 | Socket head screws, M3 x 0.5 x 10 mm, 18-8 stainless, pack of 100 | 1 x pack of 100 | McMaster-Carr [91292A113](https://www.mcmaster.com/91292A113/) | $7.11 | $7.11 | 3-4 d; In stock |
| S26 | Socket head screws, M3 x 0.5 x 8 mm, 18-8 stainless, pack of 100 | 1 x pack of 100 | McMaster-Carr [91292A112](https://www.mcmaster.com/91292A112/) | not verified | - | 3-4 d; In stock (price not shown) |
| S27 | Hook-up wire, 22 AWG silicone, 6 colours | 1 x kit | Amazon [B07G2JWYDW](https://www.amazon.com/dp/B07G2JWYDW) | not verified | - | 1-4 d; not verified |
| S28 | Neodymium disc magnets 6 x 3 mm (optional) | 1 x pack of 50 | Amazon [B0GWM9DYKL](https://www.amazon.com/dp/B0GWM9DYKL) | not verified | - | 1-4 d; not verified |

## Consumables

| Consumable | Tests | Line | Note |
|---|---|---|---|
| MgCl2, Mg(NO3)2, NaCl, KCl, 500 g each | 6 | T6-2 to T6-5 | A slurry takes about 50-100 g; 500 g lasts many refills |
| Indicating silica gel | 6 | T6-6 | Regenerate at about 120 C |
| Razor blades | 9 | T9-2 | One per few spreads if the edge nicks |
| 304 coupons (cut from sheet) | 3, 9 | T3-4 | Re-cut when scratched |
| Wire cloth discs (100 and 200 mesh) | 4 | T4-4, T4-5 | One 12 x 12 in sheet gives many 30 mm discs |
| Glass slides 75 x 25 | 4 | T4-3 | One or more per jar |
| PTFE film tape | 2 | T2-4 | Re-line bushings when worn |
| Spray adhesive | 1, 3 | T1-1 | Powder layer on pedestal tops and the mode B coupon |
| IPA 99 %, distilled water | 4, 6 | lab stock | Wet dispersion; salt slurries |
| PLA (Bambu PLA Basic) | all | lab stock | All printed fixtures; one set per powder if needed |

## What the lab likely already has

- **The doser** with its NEMA 11 and Tic T500, tilt servos, JF-0530B tapper and DRV8871, ERM and DRV2605L, Pico W,
  Pi Zero 2 W and livestream camera, and its 12 V supply. Tests 1, 2, 5, 7 and 10 use it as is.
- **The A&D HR-100A balance** (0.1 mg), which weighs every test.
- **Printers:** Bambu A1 mini and H2D (PLA), an SLA printer for smooth moulds and windows; a fume hood.
- **Probably:** microSD cards, USB cables, IEC power cords, a 2.1 mm barrel adapter, hook-up wire, resistors, a heat-set
  insert tip, calipers, IPA, beakers (50 mL catch beaker for test 5), NaCl, silica gel and glass slides. Check before ordering.

## Lead times

Order date Sat 2026-11-28 (Thanksgiving weekend): most vendors ship from Mon 30 Nov, and DigiKey's site warns that orders
may need an extra business day. Days below are calendar days to Provo. Transit times are assumptions unless a page said
otherwise (`lead_basis` in `bom.csv`).

| Apparatus | Own parts, max (days) | With the shared parts it uses, max (days) | Lines at the max | Lines with unknown lead |
|---|---|---|---|---|
| 1. Heap angle of repose | 0 | 9 | S01, S02, S03, S05 and others | - |
| 2. Bulk and tapped density | 9 | 9 | T2-6, S01, S02, S03 and others | S20 |
| 3. Tilting plate | 9 | 9 | T3-2, S01, S02, S03 and others | T3-5, T3-6, S20 |
| 4. PSD and shape from images | 7 | 14 | S07 | T4-2, T4-3, T4-6 |
| 5. Orifice cup | 9 | 9 | T5-1, T5-2, T5-3, S01 and others | T5-5, S20 |
| 6. Humidity chambers | 10 | 10 | T6-2, T6-3, T6-4, T6-5 | T6-6 |
| 7. Rotating drum | 4 | 9 | S01, S02, S03, S05 and others | - |
| 8. Unconfined strength | 9 | 9 | T8-1, T8-2, S01, S02 and others | T8-3, T8-4, S20 |
| 9. Blade spreading | 4 | 9 | S01, S02, S03, S05 and others | T9-4, S20 |
| 10. Faraday cup | 11 | 11 | T10-6 | T10-1, T10-2, T10-3 |

The 9-day ties are DigiKey and Adafruit lines by ground. With 2-day shipping they come in at about day 5, and the maximum
for tests 1-3, 5 and 7-9 drops to about 5 days.

**Critical path, last to arrive first:**

1. **IMX477 camera (S07, test 4 only): about day 4-14.** The Arducam B0240E page at UCTRONICS shows 'Add to Cart' (sold-out
   items there say 'Out of stock'); its policy says in-stock items ship within 24-72 h, but not from where. About day 4-8 from
   a US warehouse, up to about day 14 from overseas (assumption). To shorten: ask UCTRONICS for 2-day shipping (its policy
   offers it to US customers on request). The official HQ Camera would be about day 32-38 (DigiKey: 90 due 28-Dec-2026);
   it is also out at PiShop.us, Adafruit, SparkFun (backorder), CanaKit and Pimoroni (UK, pre-order), and the Global Shutter
   fallback is out at PiShop.us and Adafruit and on backorder at SparkFun.
2. **FC-1 bare boards (T10-6, test 10): about day 7-11.** Gerbers are in `../pcb/fc1-gerbers.zip`. OSH Park Super Swift is
   '4-5 business days' plus free shipping ($31.00 for 3 boards at the published '$10 per square inch, per set of 3'); standard
   service is '9-12 calendar days' ($15.50), about day 11-17. JLCPCB was not checked. The parts (T10-5, $72.00, from
   `../pcb/bom.csv`) are all in stock at DigiKey; the ADA4530-1ARZ has only 103 (44-week factory lead time), so order it now.
3. **Lab Alley salts (T6-2 to T6-5, test 6): about day 5-10.** Magnesium nitrate ships as hazmat by ground, to a business
   address only. To shorten: buy MgCl2, NaCl and KCl from Amazon (not hazmat; not verified) and only Mg(NO3)2 from Lab Alley;
   or start test 6 with NaCl and silica gel from lab stock.
4. **DigiKey and Adafruit by ground: up to about day 9.** With UPS 2nd Day: about day 4-5. Pololu (Las Vegas) and McMaster
   arrive in about 3-4 days. ServoCity (stage bearings) shows no stock text; assumed about day 4-9.
5. **Avoided:** the Pi 5 4 GB (day 11-16 at best), the SHT45 PTFE version (day 56 or later, 1 unit due), the Pico 2 W
   without headers (day 72 or later) and the official HQ Camera (day 32-38), by the spec changes above.

With 2-day shipping and the substitutions, tests 1-3 and 5-9 can be built from about day 5 (given the unverified Amazon and
McMaster lines arrive as usual); test 4 when the camera arrives (about day 4-14) and test 10 when the boards do (about day 7-11).

## Ordering plan

One order per vendor, all placed on the same day. Read the McMaster and Amazon prices at checkout and add them to `bom.csv`.

**DigiKey (one cart, UPS 2nd Day).** Add the FC-1 parts from `../pcb/bom.csv` (T10-5, $72.00) to the same cart.

- 1 x SC1432 (2648-SC1432-ND): Raspberry Pi 5, 8 GB (in place of 4 GB) (S01)
- 1 x SC1153 (2648-SC1153-ND): Raspberry Pi 27 W USB-C power supply, US plug, white (S02)
- 1 x SC1148 (2648-SC1148-ND): Raspberry Pi 5 Active Cooler (S03)
- 1 x SC1223 (2648-SC1223-ND; alias SC0872): Raspberry Pi Camera Module 3 (standard, 75 deg) (S05)
- 2 x SC1129 (2648-SC1129-ND): Raspberry Pi 5 camera cable, 300 mm (S06)
- 1 x SC1634 (2648-SC1634-ND): Raspberry Pi Pico 2 WH (Pico 2 W with headers) (S11)
- 1 x GST60A12-P1J (1866-2149-ND): 12 V 5 A desktop supply (accessory rail) (S18)
- 2 x D2F-01L (SW154-ND): Limit switch (stage homing), lever (S23)
- 2 x TCRT5000 (751-1033-5-ND): Reflective optical sensor TCRT5000 (cam-turn counter) (T2-6)
- 1 x 4438 (1528-4438-ND): LSM6DSOX 6-DoF IMU, STEMMA QT (T3-2)
- 6 x CG-P-7: Cable gland PG7, nylon, with locknut (T6-10)
- 5 x MF25060V1-1000U-A99: Fan 25 x 25 x 6.5 mm, 5 V (optional, one per chamber) (T6-11)
- 1 x 14727 (1568-14727-ND): Load cell 100 g, mini bar (TAL221) (T8-1)
- 1 x 2249-C-24 (501-1016-ND): BNC to BNC cable, 24 in (T10-4)
- 7 x 5665 (1528-5665-ND): SHT45 breakout (S14 x 2 + T6-7 x 5)
- 9 x 5385 (1528-5385-ND): STEMMA QT cable 400 mm (S15 x 4 + T6-8 x 5)

**Pololu (one order; ships same day from Las Vegas).**

- 1 x 3135: Pololu Tic T500 stepper controller (S13)
- 1 x 3782: 5 V 3.2 A step-down regulator (servos, fans) (S21)
- 1 x 1205: NEMA 11 stepper for the cam tapper (T2-2)
- 1 x 3426: Servo, 15.5 kg-cm, all-metal gears (tilt table) (T3-1)
- 1 x 2268: NEMA 17 stepper with integrated lead screw and nut (DIY stage drive) (S22a)
- Optional: a second 3135 Tic T500 ($32.95) so the tapper and stage motors need not be swapped (S13 note)

**Adafruit (one order, 2-day).**

- 1 x 5648: MOSFET driver breakout (backlight PWM) (S10)
- 2 x 4399: STEMMA QT / Qwiic cable, 50 mm (S16)
- 1 x 266 + 826: Jumper wires, female-female and female-male, 40 x 6 in each (S17)
- 2 x 4255: Brass heat-set inserts, M3 x 4 mm, pack of 50 (S24)
- 1 x 1143: Micro servo, metal gear, MG90D (orifice gate) (T5-1)
- 1 x 412: Push-pull solenoid JF-0530B, 12 V (cup tapper) (T5-2)
- 1 x 3190: DRV8871 motor driver breakout (DRV8871 #2) (T5-3)
- 1 x 5626: I2C multiplexer PCA9548 (TCA9548A compatible), STEMMA QT (T6-9)
- 1 x 4538: NAU7802 24-bit load-cell ADC, STEMMA QT (T8-2)
- Out of stock, skip: 368 (barrel adapter, S20)

**McMaster-Carr (one order).** Part numbers confirmed; prices at checkout.

- 1 x 91292A113: Socket head screws, M3 x 0.5 x 10 mm, 18-8 stainless, pack of 100 (S25)
- 1 x 91292A112: Socket head screws, M3 x 0.5 x 8 mm, 18-8 stainless, pack of 100 (S26)
- 2 x 4316N102: Hardened linear shaft, 6 mm x 100 mm, tapped M3 both ends (T2-3)
- 1 x 6305A11: PTFE film tape, 1/2 in x 15 ft, 0.005 in, acrylic adhesive (T2-4)
- 1 x 9208K136: 304 stainless disc, 1 in dia x 1/4 in thick (anvil) (T2-5)
- 1 x 1327K51: Steel shaft 5 mm x 100 mm (hinge pin) (T3-3)
- 1 x 9748K42: 304 stainless sheet, 0.036 in (0.91 mm) x 6 x 12 in, brushed #4 (T3-4)
- 1 x 9319T183: 316 stainless wire cloth, 100 x 100 mesh (0.006 in opening), 12 x 12 in (T4-4)
- 1 x 9319T191: 316 stainless wire cloth, 200 x 200 mesh (0.0029 in = 74 um), 12 x 12 in (T4-5)
- 1 x 3962A5: Razor blades, stainless, pack of 100 (blade option) (T9-2)
- 1 x 2070A21: Feeler gauge set, metric, 13 blades 0.03-0.50 mm (has 0.10, 0.15, 0.20) (T9-3)
- To choose on the site (part numbers not found): M8 washers (T3-6), M3 threaded rod and nuts (T4-6), gage pins (T5-5),
  3 mm dowel pins (T8-4), 1/16 x 1 in 304 bar (T9-4), PTFE standoffs M3 (T10-3), aluminium tube for the Faraday cup
  (T10-1, T10-2), test weights (T8-3), hardened 8 x 200 mm linear shafts x 2 (S22b, 'Linear Shafts' family)

**Amazon (one order; open each listing first, none was verified).**

- 1 x B09VT7814N: USB LED tracing pad, A5, dimmable (S09)
- 1 x B0895ZYLZ3: Drill bit set 1-6 mm in 0.1 mm steps (51 pcs) (T5-4)
- 1 x B0DNSSHYV1: Clear acrylic disc 50 mm x 2 mm (drum window) (T7-1)
- 1 x B081VLXDYC: USB LED light bar, about 30 cm (low-angle light; also test 9) (T7-2)
- 1 x B08GY9NYRM (SanDisk Ultra 32 GB, A1): microSD card, 32 GB, A1 or A2 (S04)
- 1 x B01MUJJVOG (Anker PowerLine, 2-pack): USB-A to micro-B data cable, about 1 m (S12)
- 1 x B07G2JWYDW: Hook-up wire, 22 AWG silicone, 6 colours (S27)
- To choose: 75 x 50 glass slides (T3-5), 75 x 25 slides (T4-3), silica gel (T6-6), spray adhesive (T1-1), and the
  stage micrometer (T4-2) while AmScope is out

**Others.**

- UCTRONICS (Arducam's store): 1 x B0240E IMX477 C/CS camera (S07); ask where it ships from and for 2-day shipping
- ServoCity: 2 x 1612-0815-0024 linear bearings, 2-pack (S22c); 1 x 1600-0722-0008 608-size bearings, 2-pack (S22d);
  2 x 2100-0008-0200 stainless 8 x 200 mm shafts only if hardened shafts are not found (S22b fallback)
- PiShop.us: 1 x SKU 734-2 zoom lens (S08)
- AmScope: 1 x MS90 stage (T4-1); MR095 micrometer when back in stock (T4-2)
- Uline: 2 x S-26274 10 mL Class A cylinders (T2-1; minimum 2)
- Target: 5 x Rubbermaid Brilliance 4.7 cup, TCIN 52119450 (T6-1); store pickup may be faster
- Lab Alley: C5020-500G, C5047-500g, SOCHLGL-500G, C6330-500g (T6-2 to T6-5); ship to the lab's business address
- OSH Park: FC-1 bare boards, Super Swift, set of 3 (T10-6), from `../pcb/fc1-gerbers.zip`

## Files

- [`bom.csv`](bom.csv): one row per line. Key columns: `apparatus` and `used_by`; `vendor_part_number` and `url`;
  `unit_price_usd` (verified only) and `ext_price_usd`; `price_status` (verified, alternate verified, estimate, not
  priced); `stock_seen_2026_11_28` and `how_checked`; `lead_days_min`, `lead_days_max`, `lead_basis`; the alternate;
  `lab_likely_has`; `search_to_run` for anything not verified.
- [`lead_times.json`](lead_times.json): per line `{vendor, days_min, days_max, basis}`, per apparatus the maximum with and
  without the shared parts, and the long-lead alternates that the substitutions avoid.

# v11 vendor check (2026-11-27)

The balance's height, the #35 chain's plate waist and the prices of v11's estimated BoM lines, read on 2026-11-27. The raw
results are in [`checks/vendor_v11.json`](checks/vendor_v11.json). The price changes are in [`bom.py`](bom.py).

**How the pages were read.**
- **McMaster and Amazon:** a headed Chromium (Playwright under Xvfb), logged out, whose traffic left through the doser Pi
  (SOCKS5, the Pi's residential IP). It was throttled to 400 kB/s, moved the pointer and typed like a person, and paused
  between pages ([`../vendor/common.py`](../vendor/common.py)). Neither site showed a bot check.
- **McMaster's product pages now need a login.** `mcmaster.com/<part number>/` answers "Log in to view Product Detail" to a
  logged-out browser. The family tables and each part's panel (click the part number in the table) still show the part
  number, price, pack and CAD menu, so every McMaster price below comes from a table row or a panel. Nothing was read
  logged in.
- **Read from the runner directly:** A&D's manual, Pololu, Adafruit, SparkFun, West3D, FixSupply and Nitro, and KHK's
  specification tables. All of them served the pages.
- **KHK's prices** went through the Pi browser, because KHK fills them in by script.

Vendor files (STEP, PDF, screenshots) are in `../vendor/files/` (git-ignored), pinned by sha256 in
[`../vendor/manifest_mcmaster.json`](../vendor/manifest_mcmaster.json) and [`../vendor/manifest_aandd.json`](../vendor/manifest_aandd.json).

## 1. The HR-100A's height with its breeze break

**315 mm is right as the HR-100A's overall height, but it is the height of the top door's grips, not of the cage's frame.**

- **Source:** A&D's [HR-AZ / HR-A instruction manual](https://www.aandd.jp/products/manual/balances/hr-az_hr-a_manual.pdf)
  (1WMPD4002375), section 23 "External Dimensions", printed page 79 (PDF page 81). It is one outline for the HR-100A, HR-150A,
  HR-250A and HR-251A and their AZ versions. The colour edition
  ([1WMPD4002375C](https://www.aandd.jp/products/manual/balances/1WMPD4002375C_HR-AZ_HR-A_color.pdf), section 25, p.94) has the same
  drawing. A&D's brochure gives 198 (W) × 294 (D) × 315 (H) mm.
- **Method:** the numbers in the first table are printed on the drawing. The heights in the second table were measured off the
  PDF's vector lines at 1.500 mm per point. That scale was checked against two printed dimensions, 315 and 86.5.

| Printed on A&D's drawing | mm |
|---|---|
| Overall height, bench to the top of the breeze break's top door grips | **315** |
| Base width | 198 |
| Base depth (61.5 + 191.5) | 253 |
| Depth with the doors open fully | 294 (+6) |
| Pan diameter | 90 |
| Pan height over the bench | 86.5 |
| Breeze break, inside diameter (it is **round**, a glass cylinder) | 156 |
| Breeze break, inside height over the pan | 198 |
| Top door's travel from the centre line, open fully | 270 to the left, 105 to the right |

| Scaled off the same drawing | mm over the bench |
|---|---|
| Top of the glass cylinder's wall | about 281 |
| Top of the breeze break's fixed top frame | about 297 |
| Top face of the top door | about 301 |
| Knob on the top door | about 311 |
| The two grips on the top door (the overall 315) | 315 |

**What it means for v11.** `BAL11_TOP = 315` is the right height for the HR-100A with its top door in place. v11 takes the top
door off and sets a dosing lid flush with the frame. Without the door, the balance's own top is the frame, at about 297 to
301 mm. So the 4 mm the passing 44T gears clear by is really about 18 mm on a real HR-100A.

Two other differences from v11's drawn balance (v7's model), for whoever re-draws it:
- The HR-100A's breeze break is round, 156 mm inside. v11 draws a rectangular cage.
- The HR-100A's pan is 86.5 mm up. v11 draws 50 mm.

## 2. The #35 chain's plate waist

**McMaster's own CAD for its #35 chain has waisted plates, and its inner and outer plates differ:**

| Plate | Height at the ends | Waist at mid-pitch | Waist / height | Thickness | Hole |
|---|---|---|---|---|---|
| Inner (roller link) | 8.81 | **7.49** | 0.85 | 1.27 | 4.66 (bushing) |
| Outer (pin link) | 7.76 | **6.39** | 0.82 | 1.27 | 3.58 (pin) |
| v11 before this check (every plate) | 8.79 | 6.59 (0.75 × 8.79) | 0.75 | 1.27 | |

- **Edge shape:** each waisted edge is one concave arc of R 13.08 mm (dia. 26.16) on both plates.
- **Connecting link:** its clip-side plate has straight edges (7.76 high, no waist).
- **Pins:** 3.58 dia. × 11.84 long in the chain, and 12.70 over a connecting link. Nitro gives 12.40 and 13.16.
- **Bushing and roller:** the bushing is 4.66 OD × 7.30 long. The roller is 5.08 OD × 4.76 long.
- **Source:** [McMaster 6261K172](https://www.mcmaster.com/products/roller-chain/roller-chain-trade-number~35/roller-chain-and-links-3~~/)
  (ANSI #35 single strand, steel). Its 3-D STEP for a 1 ft length (McMaster drawing 6261K291, 32 pitches: 32 inner plates,
  32 outer plates, 32 pins) was downloaded logged out through the doser Pi, from the CAD menu in the part's panel on the
  family table. 6261K191 (connecting link) was downloaded the same way.
- **Method:** each STEP was loaded with cadquery. Every plate was sliced across its length every 1/24 of it, and the height
  of each section was read. Hole and arc diameters come from the cylindrical faces.
- **McMaster's 2-D PDFs** dimension only the pitch (0.375), roller (0.200), pin (0.141), roller width (0.188), plate
  thickness (0.050) and the connecting link's width (0.500 in). They give neither the plate height nor the waist. Nitro
  doesn't publish the waist either. These numbers are McMaster's model of its own chain, not Nitro's.

**What it means for v11.**
- The old 6.59 mm waist was within 0.2 mm of McMaster's outer plates.
- It was 0.9 mm shallower than McMaster's inner plates, the plates that carry the bushings.
- McMaster's outer plates are 1.0 mm lower than the old 8.79.
- `params.py` now draws McMaster's numbers: `PLATE_WAIST` 7.49, `PLATE_H_OUT` 7.76, `PLATE_WAIST_OUT` 6.39 and
  `PLATE_WAIST_R` 13.08.

## 3. Prices

Read 2026-11-27. "Pi" means the headed browser through the doser Pi, logged out (McMaster's family table or the part's panel).
"Direct" means fetched from the runner.

**The four asked about first**

| BoM item | What | Source | Part number | Price | Pack | How |
|---|---|---|---|---|---|---|
| 66 | 24T pinion, module 1, S45C steel, 6 mm finished bore, M4 set screw, hub 20 × 10, face 10 | [KHK USA](https://catalog.khkgears.us/item/spur-gears/spur-gears-ss/ss1-24a) | **SS1-24A** | $15.20 (1-9) | each, 8 on hand | Pi (KHK fills prices by script) |
| 66 | the same gear with KHK's stock **8 mm plain bore** | [KHK USA](https://catalog.khkgears.us/item/spur-gears/spur-gears-ss/ss1-24) | SS1-24 | $13.90 | each, 8 on hand | Pi |
| 66 | McMaster's module 1, 24T, black-oxide 1045, 6 mm bore with set screw (8 mm bore: 2664N355, $15.17) | [McMaster](https://www.mcmaster.com/products/spur-gears/system-of-measurement~metric/) | 2664N354 | $15.22 | each | Pi |
| 116 | Door rods: tight-tolerance 316 rod, **1/16 in (1.59 mm)**, 1 ft (13 × 21.8 mm = 283 mm) | [McMaster](https://www.mcmaster.com/products/stainless-steel-rods/tight-tolerance-highly-corrosion-resistant-316-stainless-steel-rods~~/) | 8936K35 | $9.88 | 1 ft | Pi |
| 90 | Front standoffs: nylon, 10 mm OD, M5, **30 mm** | [McMaster](https://www.mcmaster.com/products/93657a/system-of-measurement~metric/) | 93657A272 | $2.29 (1-9), $1.87 (10+) | each | Pi |
| 90 | (the 6 mm and 25 mm on the same line) | same | 93657A075, 93657A093 | $1.08 / $0.89; $1.78 / $1.46 | each | Pi |
| 115 | M5 × 35 socket head screw, 18-8, partially threaded | [McMaster](https://www.mcmaster.com/products/91292a/system-of-measurement~metric/) | 91292A193 | $8.59 | 25 | Pi |

- **The pinion's bore.** No stock module 1, 24T gear has a 5 mm bore:
  - KHK's SS1-24 has an 8 mm plain bore.
  - KHK's SS1-24A and McMaster's 2664N354 have 6 mm bores.
  - A bore can only be opened up, not made smaller, so v11's "bored 5 mm H8" can't be done.
  - The NEMA 11's 5 mm shaft needs a 5 × 6 mm sleeve, or the pinion goes back to 20T: KHK SS1-20A or McMaster 2664N353,
    which have 5 mm bores.
- **The door rods.** McMaster lists no 1.5 mm 316 rod: the tight-tolerance family's metric sizes start at 2 mm. The 1/16 in
  rod is 0.09 mm bigger and still passes the cap's 1.8 mm hole.

**The other lines that were estimates**

| BoM item | What | Source | Part number | Price | Pack | How |
|---|---|---|---|---|---|---|
| 35 | M5 × 30 socket head screw, 18-8 (was BelMetric) | McMaster | 91292A192 | $12.78 | 50 | Pi |
| 107 | M3 × 6 socket head screw, 18-8 | McMaster | 91292A111 | $11.58 | 100 | Pi |
| 101 | Shoulder screw, 18-8, 4 × **20** mm shoulder, M3 (the length the CAD places) | [McMaster](https://www.mcmaster.com/products/90265a/shoulder-diameter~4-mm/) | 90265A124 | $6.06 (1-4), $5.19 (5+) | each | Pi |
| 86 | Dowel, 4 × 12 mm, DIN 6325-m6 / ISO 8734, Rockwell C52 | [McMaster](https://www.mcmaster.com/products/91595a/diameter~4-mm/) | 91595A155 | $13.49 | 50 | Pi |
| 87 | Dowel, 3 × 25: **not listed**. Nearest: 3 × 24 (priced, still marked estimate) or 3 × 26 | [McMaster](https://www.mcmaster.com/products/91595a/diameter~3-mm/) | 91595A130 / 91595A387 | $15.61 / $7.81 | 50 / 25 | Pi |
| 72 | Dry PTFE lubricant: Sprayon LU 708 dry film, PTFE, 10 oz aerosol | [McMaster](https://www.mcmaster.com/products/dry-lubricants/) | 1130K15 | $14.70 | each | Pi |
| 91 | M5 × 16 button head screw, 18-8 (was BelMetric) | [McMaster](https://www.mcmaster.com/products/92095a/system-of-measurement~metric/) | 92095A212 | $12.34 | 50 | Pi |
| 110 | Grommet, EPDM, for a **13/16 in** hole in 1/4 in material, 1/2 in ID | [McMaster](https://www.mcmaster.com/products/9600k/) | 11113N147 | $10.83 | 25 | Pi |
| 112 | Cable ties, 4 in, 18 lb, bundles to 7/8 in (UV resistant: 7130K52, $3.59) | [McMaster](https://www.mcmaster.com/products/cable-ties/cable-ties-1~/cable-ties-3~~/) | 7130K12 | $3.53 | 100 | Pi |
| 111 | Expandable wire sleeving, 1/4 in ID (7/16 in expanded), 10 ft | [McMaster](https://www.mcmaster.com/products/expandable-sleeving/expandable-wire-sleeving~~/) | 9284K612 | $2.31 | 10 ft | Pi |
| 23 | 6061-T651 plate, 1/4 × 24 × 36 in, in stock | [FixSupply](https://www.fixsupply.com/1248-24-36-6061-aluminum-plate-t651-1-4-thick-x-24-wide-x-36-long) | SHT-6061-0.25X24-36 | $188.30 | each | Direct |
| 108 | CNC Kitchen heat-set inserts, M3 × 3 short, in stock | [West3D](https://west3d.com/products/cnc-kitchen-heat-set-inserts-various-sizes?variant=46784419561684) | WES3495M3X | $14.99 | 100 | Direct |
| 73 | DRV8825 carrier, high current, in stock | [Pololu](https://www.pololu.com/product/2133) | 2133 | $15.95 | each | Direct |
| 74 | DRV8871 breakout, in stock | [Adafruit](https://www.adafruit.com/product/3190) | 3190 | $7.50 | each | Direct |
| 55 | Raspberry Pi Zero 2 W, **out of stock** | [Adafruit](https://www.adafruit.com/product/5291) | 5291 | $19.05 | each | Direct |
| 56 | 74AHCT125 (the chip only; the line stays an estimate), out of stock | [Adafruit](https://www.adafruit.com/product/1787) | 1787 | $1.50 | each | Direct |
| 95 | MAX3232 transceiver breakout | [SparkFun](https://www.sparkfun.com/sparkfun-transceiver-breakout-max3232.html) | BOB-11189 | $7.26 | each | Direct |
| (none) | Small push-pull solenoid, 12 V, in stock. It is placed in the CAD (`solenoid`) but has no BoM line | [Adafruit](https://www.adafruit.com/product/412) | 412 | $7.50 | each | Direct |
| 88 | Latch spring, a **candidate**: 316, 3.0 mm OD, 12.5 mm free, 0.3 mm wire, 0.36 N/mm, 6.9 mm at its 0.4 lb maximum load. Of the 3 mm OD 316 springs 11-18 mm long, it is the only one that reaches the cam's 7.0 mm. None reaches the hand release's 3.5. The line stays an estimate until the pocket is checked | [McMaster](https://www.mcmaster.com/products/compression-springs/material~316-stainless-steel/system-of-measurement~metric/) | 8969T26 | $4.88 | each | Pi |
| 28 | Clevis pin, 5 mm, with a ring groove: **McMaster has none at 5 mm**. Its grooved ones come in 4, 6, 8, 10 and 12 mm (e.g. 4 × 16 usable, 92735A317, $4.33 with ring); headless grooved in 3, 4, 6, 8, 10 and 12 mm | [McMaster](https://www.mcmaster.com/products/clevis-pins/clevis-pins-with-retaining-ring-groove-1~~/) | — | still an estimate | | Pi |

**Spot checks of lines already marked verified.** These prices are unchanged on 2026-11-27:
- socket head screws 91292A124, 91292A126 and 91292A129;
- M2 × 8 socket head screws 91292A832;
- button head screws 92095A183 and 92095A210;
- the 4 × 14 dowel 91595A158;
- Nitro's RC35-1R-10FT, $23.53, CL35-A1, $2.55, and CL35, $0.79, re-read directly.

One has changed. Item 43's 4 × 16 shoulder screw, 90265A123, is now $4.72 (1-4), against the $4.40 on the line. It was left
alone because it isn't an estimate line.

**#35 chain: Nitro against McMaster and Amazon**

| Chain, 10 ft | Price | Rating | Links |
|---|---|---|---|
| **Nitro RC35-1R-10FT** (v11's; heat treated, pre-lubricated, ANSI B29.1, publishes P, b1, d1, d2, L, h2, T) | **$23.53** | | CL35-A1 $2.55, CL35 $0.79 |
| McMaster 6261K172, steel (10 ft picked in the panel) | $50.70 ($5.07/ft) | | A-1 connecting link 7321K1 $3.13, connecting link 6261K191 $1.96 |
| [PGN #35 carbon steel, 319 links + 2](https://www.amazon.com/dp/B07NM75SBB) (PGN Bearings, ASIN B07NM75SBB) | $18.43 | 4.6 of 5, 1,585 ratings | 2 links included |
| [#35, 40Mn carbon steel, 320 links](https://www.amazon.com/dp/B079L77YM4) (AZSSMUK, ASIN B079L77YM4, Amazon's Choice) | $16.99 | 4.4 of 5, 1,086 ratings | 2 connecting links |
| [#35, 319 links + 2 master links](https://www.amazon.com/dp/B018WFTJCY) (Jeremywell, ASIN B018WFTJCY) | $18.25 | 4.5 of 5, 642 ratings | 2 master links |

The Amazon chains are $5-7 cheaper. None of them publishes h2 or the plate profile; their listings give only the pitch, the
roller, the plate thickness and, for AZSSMUK, the inner width and the pin. That leaves Nitro as the cheapest chain whose
drawing numbers v11 can be built to.

**The BoM after these changes** (`python bom.py`):

| | Before | After |
|---|---|---|
| Total | $2,083.31 | **$2,114.48** |
| Without test gear | $1,941.92 | $1,973.09 |
| Lines still marked estimate | $473.94 (24 lines) | **$129.69** (6 lines: 28, 56, 58, 65, 87, 88) |

## 4. What could not be read, or doesn't exist

- **McMaster product-detail pages:** they ask for a login now, so none was read. Nothing was read logged in. The tables and
  panels gave every number needed.
- **McMaster 6261K241 (the #35 adding link):** its CAD download returned HTTP 403 once. It wasn't needed: the 1 ft chain's
  STEP has the inner plates.
- **Doesn't exist at McMaster:**
  - a 5 mm clevis pin with a ring groove (item 28);
  - a 3 × 25 mm hardened dowel (item 87);
  - a 1.5 mm 316 rod (item 116: 1/16 in used);
  - an 18-8 4 × 14 mm shoulder screw (item 101's text; the CAD places a 4 × 20);
  - a grommet for a 3/4 in hole in 1/4 in plate with a 3/8 in ID (item 110: 13/16 in hole used).
- **Doesn't exist at KHK or McMaster:** a module 1, 24T steel gear with a 5 mm bore (item 66).
- **Not looked up:**
  - item 56's perfboard, resistors and terminals (only the 74AHCT125, $1.50, was read);
  - item 58, the plywood board;
  - item 65, the salt.
- **Not checked against the drawings:** v11's CAD draws the balance (v7's model) with a rectangular cage and the pan at
  50 mm. Section 1 gives A&D's numbers for whoever re-draws it.

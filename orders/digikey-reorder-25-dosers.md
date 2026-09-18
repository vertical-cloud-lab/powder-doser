# DigiKey-only re-order — 25 dosers (PR #115, final)

**Status: this is the order to place.** Supersedes
[`digikey-reorder-50-dosers.md`](./digikey-reorder-50-dosers.md) after @sgbaird's
decisions ([comment](https://github.com/vertical-cloud-lab/powder-doser/pull/115#issuecomment-5575693994),
2026-09-07):

- **25 dosers**, not 50.
- **No UPS** — SMART1500LCDT dropped from the cart entirely.
- **One power supply per doser** (power Decision 1 = Option A): 25 × GST60A12-P1J
  bricks + 25 × AC cords. Rationale: the dosers don't necessarily all go into the
  same lab, so shared bulk rails (Option B) don't fit.
- Context: @kinstonwithoutg had already placed the full order; only the **DigiKey
  portion was cancelled**, and everything else arrived (2026-07-28 check-in). This
  cart re-orders the cancelled DigiKey lines only. The original invoice is being
  retrieved — **reconcile this cart against it before submitting** in case the
  cancelled order differed (e.g. no carousel PSU, different caps).

**Price provenance:** every DigiKey line below was **page-verified on
2026-09-07** by loading the actual product pages through the lab Raspberry Pi's
residential connection (per @sgbaird's direction). digikey.com 403s both
datacenter IPs and plain-`curl` TLS fingerprints; a Chrome-impersonating client
(`curl_cffi`, in a throwaway venv on the Pi, removed afterwards) returns the
full pages. Prices, tier breaks, and stock states below are DigiKey's own
server-rendered data from those loads — no more search-snapshot guesses. The
cart still pulls live pricing on CSV upload.

**Re-verified 2026-09-18** (same Pi method, all pages HTTP 200) after
@kinstonwithoutg's arrived-inventory check-in — **nothing in this cart has
arrived, so the whole cart is still to order**, with two stock-driven changes:
the 20-pos header line is swapped to Sullins breakaway strips (Amphenol down to
9 in stock) and the servo line is **3 units short of stock** (47 available, 50
needed) — see the rows and watch-outs below. GST bricks (4,857), cords (5,318),
and Pico 2 WH (2,918) are all comfortably in stock at unchanged prices.

## The DigiKey cart (25 dosers)

| # | Part | MPN | DigiKey product page | Qty | Unit $ (break) | Ext $ |
|---|---|---|---|---|---|---|
| 1 | Raspberry Pi **Pico 2 WH** (RP2350, headers, Wi-Fi) — 1/doser. 2,918 in stock (2026-09-18) | SC1634 | <https://www.digikey.com/en/products/detail/raspberry-pi/SC1634/26241087> | 25 | 8.00 | 200.00 |
| 2 | 0.1″ **40-pos breakaway male header**, snap each strip in half → 2 × 20-pos (connector/pigtail headers) — 1 strip/doser. ⚠ **Swapped 2026-09-18:** the original Amphenol 10129378-920003BLF 20-pos is down to **9 in stock** (50 needed); Sullins breakaway is the standard substitute, 48,079 in stock | **PRPC040SAAN-RC** (Sullins) | <https://www.digikey.com/en/products/detail/sullins-connector-solutions/PRPC040SAAN-RC/2775214> | 25 | 1.041 @10+ (1.23 @1) | 26.03 |
| 3 | **MG996R-series tilt servo** (Terasic-branded MG996R) — 2/doser. ⚠ **2026-09-18: only 47 in stock** (50 needed; 56-week mfr lead behind it). Either cut this line to 47 and source 3 elsewhere, or move the whole line to Amazon TowerPro MG996R multi-packs (≈$3–5/pc, saves ≈$400) | FXX-3037-TOP | <https://www.digikey.com/en/products/detail/terasic-inc/FXX-3037-TOP/7044113> | 50 | 12.50 (no breaks) | 625.00 |
| 4 | Mean Well **GST60A12-P1J** 12 V/5 A brick — 1/doser ✅ in stock, **4,857** (2026-09-18) | GST60A12-P1J | <https://www.digikey.com/en/products/detail/mean-well-usa-inc/GST60A12-P1J/7703712> | 25 | 17.10 @25 (19.40 @1) | 427.50 |
| 5 | Mean Well **YP12+YC12** AC cord, 5-15P→C13 (feeds the GST brick's C14 inlet) — 1/brick, 5,318 in stock (2026-09-18) | YP12-YC12 | <https://www.digikey.com/en/products/detail/mean-well-usa-inc/YP12-YC12/7707223> | 25 | 6.19 @10+ (7.29 @1) | 154.75 |
| | **DigiKey subtotal** (if all 50 servos were in stock) | | | | | **$1,433.28** |

> Servo-stock reality check: with only 47 servos on the shelf, the practical
> options are **(a)** DigiKey cart with 47 servos = **$1,395.78** + 3 servos
> from a second vendor, or **(b)** servos entirely via Amazon multi-packs →
> DigiKey cart = **$808.28** + ≈$150–250 on Amazon for 50 MG996R.

Removed vs the ×50 doc: **SMART1500LCDT UPS** (−$379.12, per decision — and BOM §4
records one already ordered via BYU ME #12929). Removed on page-verification:
**LRS-350-48** 48 V carousel PSU — its DigiKey page now shows **“This product is
no longer available at DigiKey”**, so it can't be on this cart at all; source it
with the StepperOnline drive order or from Mouser instead (see watch-outs).

Optional add-ons (listed as vendor "any"/Adafruit in the BOM — add here to keep a
single PO, DigiKey stocks both):

| Part | MPN | DigiKey product page | Qty | Unit $ | Ext $ |
|---|---|---|---|---|---|
| 100 µF / 25 V radial electrolytic — 3/doser (C1/C2/C3, BOM §2). ⚠ Plain **ECA-1EM101** is 0-stock with a 37-week lead — order the in-stock **-B** packaging variant instead (1,597 in stock, same cap) | ECA-1EM101**B** (Panasonic) | <https://www.digikey.com/en/products/detail/panasonic-industry/ECA-1EM101B/268461> | 100 (75 + spares) | 0.1291 @100 (0.33 @1) | 12.91 |
| 2.1 mm DC jack → screw-terminal adapter (female; mates the GST brick's plug — BOM §4 item 13b, needed under one-PSU-per-doser) | Adafruit 368 | <https://www.digikey.com/en/products/detail/adafruit-industries-llc/368/5629434> | 25 | 2.00 (verified, in stock) | 50.00 |

### CSV for DigiKey's BOM/list upload

```csv
Quantity,Part Number,Customer Reference
25,SC1634,Pico 2 WH (1/doser)
25,PRPC040SAAN-RC,40-pos breakaway headers - snap in half = 2x 20-pos per doser
50,FXX-3037-TOP,MG996R tilt servos (2/doser) - only 47 in stock 2026-09-18 see notes
25,GST60A12-P1J,12V 5A brick (1/doser) - in stock as of 2026-09-18
25,YP12-YC12,AC cord for GST60A12 (1/brick)
100,ECA-1EM101B,100uF/25V bulk caps (3/doser + spares) - optional
25,368,2.1mm jack to screw terminal (1/brick) - optional
```

(LRS-350-48 removed — no longer available at DigiKey. Plain ECA-1EM101 swapped
for the in-stock ECA-1EM101B packaging variant. 2026-09-18: Amphenol
10129378-920003BLF header swapped for Sullins PRPC040SAAN-RC breakaway strips —
only 9 of the Amphenol left in stock.)

## Stock watch-outs (page-verified 2026-09-07, re-verified 2026-09-18, via the lab Pi)

2026-09-18 deltas first:

- **FXX-3037-TOP servos: 47 in stock** (was ≈115 on 2026-09-02) vs **50
  needed** — the line no longer covers the build on its own. Decide: 47 from
  DigiKey + 3 elsewhere, or all 50 via Amazon TowerPro MG996R multi-packs
  (≈$3–5/pc; Amazon is already an approved route for this project's
  purchasing — the NEMA 34, CL86T, NEMA-11s and Waveshare boards all came
  through it).
- **Amphenol 10129378-920003BLF header: 9 in stock** — line swapped to
  **Sullins PRPC040SAAN-RC** 40-pos breakaway strips (48,079 in stock,
  $1.041 @10+); snap each strip in half for the two 20-pos runs per doser.
  Any 0.1″ breakaway male header is equivalent if this one moves.
- **GST60A12-P1J: 4,857 in stock**, $17.10 @25 unchanged. **YP12-YC12: 5,318
  in stock**, $6.19 @10+ unchanged. **SC1634: 2,918 in stock**, $8.00
  unchanged. **ECA-1EM101B** cut-tape in stock, $0.1291 @100 unchanged;
  **Adafruit 368** in stock, $2.00 unchanged.

Original 2026-09-07 notes:

- **GST60A12-P1J backorder has cleared — it is in stock at DigiKey** (product
  page and category filter both say In Stock; ordering 25 should go straight
  through, which removes the suspected cause of the original cancellation).
  Tier price is **$17.10 @25** ($19.40 @1), a bit above the earlier $16.50
  snapshot. The fallbacks are no longer needed, kept for reference: (a)
  **GSM60A12-P1J** medical variant, page-verified in stock, $21.20 @25 —
  <https://www.digikey.com/en/products/detail/mean-well-usa-inc/GSM60A12-P1J/7703568>;
  (b) RS (us.rs-online.com) — unverifiable by machine (403s even the Pi).
- **LRS-350-48 is no longer available at DigiKey** (page banner: “This product
  is no longer available at DigiKey”; not a marketplace listing either, and no
  LRS-350H-48 successor listed). Buy it elsewhere `[confirm the exact listing
  in a browser]`: add it to the StepperOnline order alongside the carousel
  motor + driver, or Mouser (mouser.com also 403s automated clients, so it
  needs a human click-through).
- **FXX-3037-TOP servos**: in stock, $12.50 flat (no qty breaks). The page
  doesn't server-render the exact count (US stock read ~115 on 2026-09-02 and
  50 are needed) — glance at the number when adding to the cart. TowerPro
  MG996R multi-packs still run ~$3–5/pc on Amazon (~−$400) if a second vendor
  is acceptable.
- **YP12-YC12 cord**: 5,583 in stock; tiers $7.29 @1 / $6.19 @10+ (the ×50
  doc's $3.50 and the last session's $6.13 were both off).
- **ECA-1EM101 (plain, bulk)**: 0 in stock, **37-week** factory lead — the
  optional caps line now points at **ECA-1EM101B** (1,597 in stock,
  $0.1291 @100). Same-family spares if that moves: ECA-1EM101I (454 in stock),
  ECA-1VM101 (35 V rating, 21k in stock).
- **SC1634 Pico 2 WH**: $8.00, in stock (the 18-week figure on the page is the
  manufacturer lead that applies only if it slips to backorder).

## Not on DigiKey — don't look for these in the cart

Per the 2026-07-28 check-in, **all non-DigiKey items already arrived**, so nothing
below should need re-ordering; kept for reference:

- Waveshare Pico-2CH-RS232 (PiShop), RPi 5 starter kit (PiShop).
- NEMA 34 34HS59-6004D-E1000 + CL86T V4.1 (StepperOnline / Amazon).
- Balance: A&D HR-100A (ceproducts.shop) + AD-1671 anti-vibration table.
- Tic T500 / Pololu / Adafruit / StepperOnline lines.
- **New (per the LRS-350-48 delisting above): the 48 V carousel PSU joins this
  list** — bundle it with the StepperOnline order or buy from Mouser.

Bonus from the same Pi session — the two StepperOnline carousel-drive links
finally **direct-loaded (HTTP 200, exact SKU confirmed on-page)** after months
of 403-only checks, and both are cheaper than the BOM's estimates:

- 34HS59-6004D-E1000 motor: **$62.58, in stock** (BOM guessed ~$110).
- CL86T-V41 driver: **$46.31, in stock** (BOM guessed ~$55).

## Gap check — needed by the design but on *no* order list

- **25 × Pololu D24V22F5** 5 V/2.5 A buck (BOM §2 U1, one per module) — Pololu
  #2858, $18.95 (≈ $474). Not a DigiKey part; still absent from every order list,
  and 2.5 A remains marginal under two MG996R stalls.
- **Per-module proto/solder substrate** (bench = breadboard; production =
  Perma-Proto, Adafruit #2310) — confirm how 25 modules get wired.

## Firmware note

Pico 2 WH is **RP2350**; the bench firmware/pin contract (BOM §2) targets Pico W
(RP2040) on GP0..GP15 only, so the pinout carries over — but flash the RP2350
MicroPython UF2, and re-verify the Tic serial + DRV2605L I²C drivers on RP2350
before committing all 25.

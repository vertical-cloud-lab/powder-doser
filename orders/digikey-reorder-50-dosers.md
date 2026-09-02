# DigiKey-only re-order — 50-doser scale-up (PR #115)

**Who/why:** @kinstonwithoutg's DigiKey order was cancelled and needs re-ordering, but the
cost wouldn't reproduce from the ×50 list in the PR #115 thread
([request](https://github.com/vertical-cloud-lab/powder-doser/pull/115#issuecomment-5428149972)).
This doc isolates **only the DigiKey lines** from the SGB-edited ×50 list
(50 dosers, Tic T500 path, 2× MG996R servos standard) and re-prices them.

**Price provenance:** DigiKey listing prices as indexed by web search on **2026-09-02**
(digikey.com returns HTTP 403 to automated fetchers, so these are search-snapshot prices —
the cart itself will pull live pricing when the part numbers are entered). Quantity breaks
at 25/50/100 units apply to several lines and are noted where known.

## Why the old cost number didn't reproduce

1. **There never was a DigiKey-only subtotal.** The ≈ $6,220 rollup mixed Pololu,
   Adafruit, StepperOnline, Amazon, PiShop **and** DigiKey lines.
2. **Garbled table columns.** In the edited rows the quantity landed in the Unit-$ column
   (e.g. `| GST60A12-P1J | 50 | ~90–150 |`), so unit/qty/extended can't be told apart.
3. **The 12 V power row contradicts itself** (biggest swing, ≈ $900): the row *text* says
   "≈2–3× LRS-350-12 bulk supplies" (≈ $98–130) but the *link + qty-50 + the 50× YP12-YC12
   cord row* say one GST60A12-P1J brick per doser (≈ $825–930 + $175 cords). See Decision 1.
4. **Stale / wrong unit prices.** UPS listed "~$200" → DigiKey now shows **$379.12**;
   MG996R listed $8.00 → the linked DigiKey part (Terasic FXX-3037-TOP) is **$12.50**
   (100 × = $1,250, not $800); the header line's own math was wrong ($2.00 × 100 ≠ $50;
   real price is ~$0.51 ea).
5. **Unpriced lines.** The Pico 2 WH ×50 row (+$400) and the cord row carried no extended
   price into the rollup.
6. **Stock:** GST60A12-P1J showed **backorder** on US DigiKey when checked — possibly
   related to the original cancellation; verify live stock before submitting.

## The DigiKey cart (as the edited ×50 list specifies)

| # | Part | MPN | DigiKey product page | Qty | Unit $ (break) | Ext $ |
|---|---|---|---|---|---|---|
| 1 | Raspberry Pi **Pico 2 WH** (RP2350, headers, Wi-Fi) — 1/doser | SC1634 | <https://www.digikey.com/en/products/detail/raspberry-pi/SC1634/26241087> | 50 | 8.00 | 400.00 |
| 2 | 0.1″ 20-pos male header (connector/pigtail headers) — 2/doser | 10129378-920003BLF | <https://www.digikey.com/en/products/detail/amphenol-icc-fci-/10129378-920003BLF/7915971> | 100 | ~0.51 | ~51.00 |
| 3 | **MG996R-series tilt servo** (Terasic-branded MG996R) — 2/doser | FXX-3037-TOP | <https://www.digikey.com/en/products/detail/terasic-inc/FXX-3037-TOP/7044113> | 100 | 12.50 | 1,250.00 |
| 4 | Mean Well **GST60A12-P1J** 12 V/5 A brick — 1/doser *(see Decision 1)* | GST60A12-P1J | <https://www.digikey.com/en/products/detail/mean-well-usa-inc/GST60A12-P1J/7703712> | 50 | 16.50 @25+ (18.60 @1) | ~825–930 |
| 5 | Mean Well **YP12+YC12** AC cord, 5-15P→C13 (feeds the GST brick's C14 inlet) — 1/brick | YP12-YC12 | <https://www.digikey.com/en/products/detail/mean-well-usa-inc/YP12-YC12/7707223> | 50 | ~3.50 `[confirm]` | ~175.00 |
| 6 | Eaton Tripp Lite **SMART1500LCDT** UPS *(see Decision 2)* | SMART1500LCDT | <https://www.digikey.com/en/products/detail/eaton-tripp-lite/SMART1500LCDT/4439114> | 1 | 379.12 | 379.12 |
| 7 | Mean Well **LRS-350-48** 48 V PSU (carousel NEMA 34 + CL86T) | LRS-350-48 | <https://www.digikey.com/en/products/detail/mean-well-usa-inc/LRS-350-48/7705033> | 1 | 32.50 | 32.50 |
| | **DigiKey subtotal (cart as edited)** | | | | | **≈ $3,110–3,220** |

Optional add-on (in the ×50 list as vendor "any" — add here if not sourced elsewhere):

| Part | MPN | DigiKey product page | Qty | Unit $ | Ext $ |
|---|---|---|---|---|---|
| 100 µF / 25 V radial electrolytic — 3/doser (C1/C2/C3, BOM §2) | ECA-1EM101 (Panasonic) | <https://www.digikey.com/en/products/detail/panasonic-industry/ECA-1EM101/245011> | 200 (150 + spares, hits the 200 break) | 0.1095 @200 | 21.90 |

### CSV for DigiKey's BOM/list upload

```csv
Quantity,Part Number,Customer Reference
50,SC1634,Pico 2 WH (1/doser)
100,10129378-920003BLF,0.1in 20-pos male headers (2/doser)
100,FXX-3037-TOP,MG996R tilt servos (2/doser) - see Decision 3
50,GST60A12-P1J,12V 5A brick (1/doser) - see Decision 1
50,YP12-YC12,AC cord for GST60A12 (1/brick) - see Decision 1
1,SMART1500LCDT,UPS - see Decision 2 (may already be delivered)
1,LRS-350-48,48V PSU for carousel CL86T
200,ECA-1EM101,100uF/25V bulk caps (3/doser + spares) - optional line
```

## Decisions needed before submitting (@sgbaird)

1. **12 V power topology (± ~$870).**
   *Option A — as edited:* 50 × GST60A12-P1J + 50 × YP12-YC12 ≈ **$1,000–1,100**.
   Faithful 1:1 replication of the bench module (BOM §2 J1), but needs 50 outlets/power
   strips, and the brick showed **backorder** (drop-in if short: **GSM60A12-P1J** medical
   variant, same 2.1 mm plug, ≈ $21).
   *Option B — as the row text says:* 3–4 × **LRS-350-12** bulk rails
   ([$32.50 ea](https://www.digikey.com/en/products/detail/mean-well-usa-inc./LRS-350-12/7705030),
   598 in stock) ≈ **$98–130**, plus 12 V DC distribution (terminal blocks, per-branch
   fusing, wire) and hardwired mains input (screw terminals — the YP12 cords don't apply).
   With 2 × MG996R standard per doser, 3 rails is thin; 4 is safer.
2. **UPS dedup (− $379.12 if already on hand).** BOM §4 records SMART1500LCDT as
   *"ordered (BYU ME order #12929)"*. Confirm whether that order delivered before
   re-buying — and note the price is now **$379.12**, not the ~$200 in the list.
3. **Servo sourcing (− ~$800 if moved off DigiKey).** FXX-3037-TOP *is* an MG996R-series
   servo, so the link in the edited list is the right part — but $12.50 × 100 = $1,250,
   US stock read **115 units** (barely covers 100; 56-week mfr lead time behind it), vs
   roughly $3–5/unit for TowerPro MG996R multi-packs on Amazon. Keep on DigiKey only if
   the single-PO convenience is worth it.

**Range:** all-DigiKey as edited ≈ **$3,110–3,220** → with Option B rails, servos via
Amazon, and UPS already delivered ≈ **$640** (lines 1, 2, 7 + rails + caps). This spread
is why no single "same cost number" exists.

## Not on DigiKey — don't look for these in the cart

From the same edited ×50 list; order separately if still outstanding:

- **Waveshare Pico-2CH-RS232** — PiShop $8.95 (listed qty 50 → ~$448; only 1–2 balances
  exist today, so confirm the 50× intent before buying 50).
- **Raspberry Pi 5 (8 GB) starter kit** — PiShop (replaces Pi Zero 2 W host).
- **NEMA 34 34HS59-6004D-E1000 + CL86T V4.1** — StepperOnline / Amazon (carousel drive).
- Balance: resolved 2026-06-26 → **A&D HR-100A** (ceproducts.shop) + **AD-1671**
  anti-vibration table.
- Tic T500 / Pololu / Adafruit / StepperOnline lines — arrived per 2026-07-28 check-in.

## Gap check — needed by the design but on *no* order list

- **50 × Pololu D24V22F5** 5 V/2.5 A buck (BOM §2 U1, one per module: Pico + servos +
  solenoid 5 V rail) — absent from the ×50 list entirely. Pololu #2858, $18.95
  (≈ $950 — and 2.5 A is already marginal under two MG996R stalls; worth revisiting).
- **50 × 2.1 mm barrel jack** to receive the GST brick's plug (BOM §4 item 13b,
  "~$2.50", no P/N pinned; Adafruit #373 breadboard style is the referenced part) —
  only needed under power Option A.
- **Per-module proto/solder substrate** (bench = breadboard; production = Perma-Proto,
  Adafruit #2310) — not in the ×50 list; confirm how 50 modules get wired.

## Firmware note

Pico 2 WH is **RP2350**; the bench firmware/pin contract (BOM §2) targets Pico W (RP2040)
on GP0..GP15 only, so the pinout carries over — but flash the RP2350 MicroPython UF2, and
re-verify the Tic serial + DRV2605L I²C drivers on RP2350 before committing all 50.

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

**Price provenance:** DigiKey listing prices as indexed by web search on
**2026-09-07** (digikey.com returns HTTP 403 to automated fetchers, so these are
search-snapshot prices — the cart pulls live pricing when the part numbers are
entered). Servo/Pico/cord prices were re-checked this session; others carry over
from the 2026-09-02 check.

## The DigiKey cart (25 dosers)

| # | Part | MPN | DigiKey product page | Qty | Unit $ (break) | Ext $ |
|---|---|---|---|---|---|---|
| 1 | Raspberry Pi **Pico 2 WH** (RP2350, headers, Wi-Fi) — 1/doser | SC1634 | <https://www.digikey.com/en/products/detail/raspberry-pi/SC1634/26241087> | 25 | 8.00 | 200.00 |
| 2 | 0.1″ 20-pos male header (connector/pigtail headers) — 2/doser | 10129378-920003BLF | <https://www.digikey.com/en/products/detail/amphenol-icc-fci-/10129378-920003BLF/7915971> | 50 | ~0.51 | ~25.50 |
| 3 | **MG996R-series tilt servo** (Terasic-branded MG996R) — 2/doser | FXX-3037-TOP | <https://www.digikey.com/en/products/detail/terasic-inc/FXX-3037-TOP/7044113> | 50 | 12.50 | 625.00 |
| 4 | Mean Well **GST60A12-P1J** 12 V/5 A brick — 1/doser ⚠ **backorder** | GST60A12-P1J | <https://www.digikey.com/en/products/detail/mean-well-usa-inc/GST60A12-P1J/7703712> | 25 | 16.50 @25 (18.60 @1) | 412.50 |
| 5 | Mean Well **YP12+YC12** AC cord, 5-15P→C13 (feeds the GST brick's C14 inlet) — 1/brick | YP12-YC12 | <https://www.digikey.com/en/products/detail/mean-well-usa-inc/YP12-YC12/7707223> | 25 | 6.13 | 153.25 |
| 6 | Mean Well **LRS-350-48** 48 V PSU (carousel NEMA 34 + CL86T) — *drop if not on the cancelled order* | LRS-350-48 | <https://www.digikey.com/en/products/detail/mean-well-usa-inc/LRS-350-48/7705033> | 1 | 32.50 | 32.50 |
| | **DigiKey subtotal** | | | | | **≈ $1,450** |

Removed vs the ×50 doc: **SMART1500LCDT UPS** (−$379.12, per decision — and BOM §4
records one already ordered via BYU ME #12929).

Optional add-ons (listed as vendor "any"/Adafruit in the BOM — add here to keep a
single PO, DigiKey stocks both):

| Part | MPN | DigiKey product page | Qty | Unit $ | Ext $ |
|---|---|---|---|---|---|
| 100 µF / 25 V radial electrolytic — 3/doser (C1/C2/C3, BOM §2) | ECA-1EM101 (Panasonic) | <https://www.digikey.com/en/products/detail/panasonic-industry/ECA-1EM101/245011> | 100 (75 + spares) | ~0.13 `[confirm]` | ~13.00 |
| 2.1 mm DC jack → screw-terminal adapter (female; mates the GST brick's plug — BOM §4 item 13b, needed under one-PSU-per-doser) | Adafruit 368 | <https://www.digikey.com/en/products/detail/adafruit-industries-llc/368/5629434> | 25 | ~2.00 `[confirm]` | ~50.00 |

### CSV for DigiKey's BOM/list upload

```csv
Quantity,Part Number,Customer Reference
25,SC1634,Pico 2 WH (1/doser)
50,10129378-920003BLF,0.1in 20-pos male headers (2/doser)
50,FXX-3037-TOP,MG996R tilt servos (2/doser)
25,GST60A12-P1J,12V 5A brick (1/doser) - backordered, see note
25,YP12-YC12,AC cord for GST60A12 (1/brick)
1,LRS-350-48,48V PSU for carousel CL86T - drop if not on cancelled order
100,ECA-1EM101,100uF/25V bulk caps (3/doser + spares) - optional
25,368,2.1mm jack to screw terminal (1/brick) - optional
```

## Stock watch-outs (checked 2026-09-07)

- **GST60A12-P1J is still on DigiKey backorder** (likely related to the original
  cancellation). Options, in order: (a) place the backorder line and wait;
  (b) substitute the **GSM60A12-P1J** medical variant — same 12 V/5 A, same 2.1 mm
  plug, ≈ $21 — <https://www.digikey.com/en/products/detail/mean-well-usa-inc/GSM60A12-P1J/7703568>
  (stock also looked thin; check live); (c) off-DigiKey fallback: RS
  (us.rs-online.com) showed **166 in stock @ $23.05**.
- **FXX-3037-TOP servos**: in stock / ships same day; 50 pcs sits well inside the
  ~115-unit US stock seen earlier (100 pcs barely did). If DigiKey pricing stings,
  TowerPro MG996R multi-packs run ~$3–5/pc on Amazon (~−$400), but that breaks the
  single-PO convenience.
- **YP12+YC12** re-priced: $6.13 (the ×50 doc's ~$3.50 guess was low).

## Not on DigiKey — don't look for these in the cart

Per the 2026-07-28 check-in, **all non-DigiKey items already arrived**, so nothing
below should need re-ordering; kept for reference:

- Waveshare Pico-2CH-RS232 (PiShop), RPi 5 starter kit (PiShop).
- NEMA 34 34HS59-6004D-E1000 + CL86T V4.1 (StepperOnline / Amazon).
- Balance: A&D HR-100A (ceproducts.shop) + AD-1671 anti-vibration table.
- Tic T500 / Pololu / Adafruit / StepperOnline lines.

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

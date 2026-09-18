# Remaining to order — 25 dosers (as of 2026-09-18)

Answer to @kinstonwithoutg's 2026-09-15 check-in on PR #115 ("Check what do I
have left to order on DigiKey or other places for 25 dosers"), cross-referencing
the arrived-items list against [`BILL-OF-MATERIALS.md`](../BILL-OF-MATERIALS.md)
and [`digikey-reorder-25-dosers.md`](./digikey-reorder-25-dosers.md).

**Bottom line:** the 2026-09-15 arrived list covers **every non-DigiKey
electronics item** in the 25-doser build, and **nothing from the cancelled
DigiKey order has arrived** — so what's left is (1) the DigiKey cart, re-verified
2026-09-18 with two stock-driven changes, and (2) a short list of support items
that were never on any order.

## 1. Arrived — cross-checked against the BOM ✓

Everything on the 2026-09-15 list maps cleanly to a BOM line at the right
quantity for 25 dosers; no duplicates, no mystery parts:

| Arrived | Qty | BOM ref | Need (×25) | OK |
|---|---|---|---|---|
| Pololu **Tic T500** stepper controller | 25 | §2 U5 | 25 | ✓ |
| Pololu **#3776** 33 V/9 W shunt regulator | 25 | §2 SR1 | 25 | ✓ |
| Raspberry Pi 5 (8 GB) starter kit | 1 | host orchestrator (SGB-edited list) | 1 | ✓ |
| Adafruit **#1201** vibration mini motor disc | 25 | §2 M1 | 25 | ✓ |
| Adafruit **#412** push-pull solenoid | 25 | §2 SOL1 | 25 | ✓ |
| Adafruit **DRV8871** motor driver (#3190) | 25 | §2 U4 | 25 | ✓ |
| Adafruit **DRV2605L** haptic driver (#2305) | 25 | §2 U3 | 25 | ✓ |
| **NEMA-11 11HS18-0674S** stepper (Amazon) | 25 | §2 M2 | 25 | ✓ |
| **NEMA 34 34HS59-6004D-E1000** closed-loop (Amazon) | 1 | §5.1 MC1 (carousel) | 1 | ✓ |
| **CL86T V4.1** closed-loop driver (Amazon) | 1 | §5.1 MD1 (carousel) | 1 | ✓ |
| **Waveshare Pico-2CH-RS232** (Amazon) | 25 | §2 U6 | 25 | ✓ |
| A&D balances ("the two scales", 2026-07-22) | 2 | §3 | 1–2 | ✓ |

## 2. Still to order — DigiKey

The full cart in [`digikey-reorder-25-dosers.md`](./digikey-reorder-25-dosers.md)
(every line re-verified in stock 2026-09-18 via the lab Pi, except as flagged):

| Part | MPN | Qty | Ext $ |
|---|---|---|---|
| Pico 2 WH (1/doser) — 2,918 in stock | SC1634 | 25 | 200.00 |
| 40-pos breakaway male headers (snap in half → 2 × 20-pos/doser) — **swapped 2026-09-18**, the Amphenol 20-pos original is down to 9 in stock | PRPC040SAAN-RC | 25 | 26.03 |
| MG996R-series tilt servo (2/doser) — ⚠ **only 47 in stock, 50 needed** (see options below) | FXX-3037-TOP | 50 | 625.00 |
| Mean Well 12 V/5 A brick (1/doser) — 4,857 in stock | GST60A12-P1J | 25 | 427.50 |
| AC cord for the brick (1/brick) — 5,318 in stock | YP12-YC12 | 25 | 154.75 |
| *Optional:* 100 µF/25 V caps (3/doser + spares) | ECA-1EM101B | 100 | 12.91 |
| *Optional:* 2.1 mm jack → screw terminal (1/brick) | Adafruit 368 | 25 | 50.00 |

**Servo shortfall decision:** (a) order 47 from DigiKey ($587.50) + 3 MG996R
from a second vendor, or (b) drop the line and buy all 50 as Amazon TowerPro
MG996R multi-packs (≈$3–5/pc ≈ $150–250, saves ≈$400; Amazon is already an
approved purchasing route here). DigiKey totals: **$1,395.78** under (a),
**$808.28** under (b), + optionals.

## 3. Still to order — elsewhere (never on any order list)

| # | Item | Qty | Source | ≈$ | Why |
|---|---|---|---|---|---|
| 1 | **48 V PSU** for the carousel drive (Mean Well **LRS-350-48** or equal, ≥350 W) | 1 | Amazon (search "Mean Well LRS-350-48") or Mouser — delisted at DigiKey; StepperOnline checked 2026-09-18: only a CN-warehouse 250 W S-250-48 and 120 W DIN units | 40 | **Blocking**: the arrived NEMA 34 + CL86T can't even bench-test without it |
| 2 | **Pololu D24V22F5** 5 V/2.5 A buck (1/doser) | 25 | pololu.com #2858 — **$16.04 @25** (verified 2026-09-18) | 401 | BOM §2 U1: the 12 V→5 V rail for Pico + servos + solenoid. Note: 2.5 A is marginal under a two-servo stall (BOM flag) |
| 3 | Wiring substrate (1/doser): half-size breadboards *or* Adafruit **Perma-Proto half-size #571** | 25 | Adafruit / any | 115–190 | BOM §2 bench = breadboard; §5 item 6's Pi-bonnet #2310 doesn't fit the Pico-per-module design — pick one |
| 4 | **Filament**: ≈6.6 kg PLA (Sam's measured 262.07 g/doser × 25 + waste) | 8 × 1 kg spools | Amazon etc. | 130–165 | BOM §8 open item — never ordered |
| 5 | **M3/M5 fasteners** per BOM §6.2 × 25 (≈550 M3 mixed lengths + setscrews/self-tap, ≈200 M5 incl. 50 hinge pins + lock-nuts) | kits | McMaster / Amazon assortments | 60–90 | "Bench-stock" in the BOM, but 25 units exceeds bench stock |
| 6 | **RS-232 DB9 cables** for the balances (A&D AX-KO2466-200 or generic — buzz out pinout first, BOM §2/§3) | 1–2 | A&D dealer / any | 10–40 | Confirm none shipped with the balances |
| 7 | 3 × MG996R servo top-up | 3 | Amazon | 15 | Only under servo option (a) |

**Rough grand total for everything remaining: ≈ $1,850–2,250** (DigiKey cart +
the table above; servo-option dependent).

## 4. Confirm-only (no purchase expected)

- **AD-1671 anti-vibration table** — ordered with the HR-100A (2026-06-26
  decision); confirm it arrived with the balances.
- **Waveshare ×25 via Amazon** — if the XYGStudy listing was the
  "with Pico" bundle, those bundled boards are plain RP2040 Picos (no Wi-Fi,
  not RP2350) and are **not** a substitute for the SC1634 Pico 2 WH cart line.
- **SC1634 title glance** — when adding to the cart, confirm the title reads
  "Pico 2 **WH**" (pre-soldered headers). If it's the headerless Pico 2 W,
  add 25 more Sullins strips to header the Picos themselves.
- **ST-FC01 5 mm couplers** — struck from the SGB-edited ×50 list; the current
  assembly is gear-driven (16T stepper pinion → 48T auger band, BOM §6.1), so
  no couplers are needed unless a direct-drive variant returns.
- **Invoice reconciliation** — the cancelled-order invoice (requested
  2026-09-07) remains the final tie-breaker on line items.

## 5. Separate bucket — carousel mechanical build (not part of this order)

The carousel **drive** is now in hand (NEMA 34 + CL86T; PSU = §3 item 1), but
the mechanical build — shaft, pillow blocks, worm reducer/brake, extrusion
frame, pocket discs, counterweight, home sensor, E-stop — is still unordered:
≈$400–800 depending on options, per
[`../carousel/carousel-build-parts-list.md`](../carousel/carousel-build-parts-list.md).
That's a build-decision purchase, not part of replacing the cancelled order.

---

*Stock/price provenance: DigiKey pages loaded 2026-09-18 through the lab Pi's
residential connection (Chrome-impersonating TLS; throwaway venv removed
afterwards); Pololu re-priced the same day from the runner. The Edison
feedback task on the vertical-carousel plan (`11ddf6db…`, build-list §12) was
also re-attempted this session and is blocked by an API-key permission change —
see that §12 for details.*

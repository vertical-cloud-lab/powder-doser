# Getting started: printing and assembling the new dosers

For **@lshuldberg**, who is picking up the build of the repeat dosers. The new
dosers are copies of the single-channel doser running on the bench today, so
this page is about reproducing that rig: print the parts, find out what we're
missing, build one doser end to end, then batch the rest.

PR #115 sized the purchasing for **25 dosers**, so quantities below are given
per doser and for 25. If you're building fewer to start with, scale down.

**Your first week, in order:**

1. **Start the A1 mini now.** Every printed part except the baseplate and
   the auger fits on it ([§2](#2-printing)).
2. **Use the H2D slots for baseplates and augers only.** Nothing else needs
   the big printer ([§2.3](#23-h2d-slots-baseplates-and-augers-only)).
3. **Do the inventory count** with
   [`inventory-checklist.csv`](inventory-checklist.csv) and post the
   shortfalls on your PR ([§3](#3-inventory-check)).
4. **Build doser #1 end to end** with Sam and William nearby, writing down
   every snag ([§4](#4-build-order)).
5. Then build the rest in batches.

## 1. What you're building

![Exploded view of one doser with numbered parts](https://github.com/vertical-cloud-lab/powder-doser/blob/ce256c3/cad/full-assembly/renders/assembly_exploded_bom.png?raw=true)

One doser is **11 printed parts, 4 purchased motion parts, 52 screws and nuts,
and a 38 mm (1.5 in) board** to screw it to, plus the electronics on the
**V2 PCB**. The motion parts are 2 MG996R tilt servos, a NEMA-11 stepper and a
12 V push-pull solenoid. The electronics are a Pico 2 WH, Tic T500 stepper
controller, DRV8871 solenoid driver, DRV2605L haptic driver with a coin
vibration motor, shunt regulator, 5 V buck, Waveshare RS-232 module, and a
12 V/5 A power brick.

Sources of truth:

| What | Where |
|---|---|
| Mechanical parts list and the 19 build steps | [`cad/full-assembly/BOM.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/ce256c3/cad/full-assembly/BOM.md) (PR #170) |
| Step-by-step GIFs | [whole doser](https://github.com/vertical-cloud-lab/powder-doser/blob/ce256c3/cad/full-assembly/renders/assembly_steps.gif), [auger unit](https://github.com/vertical-cloud-lab/powder-doser/blob/ce256c3/cad/full-assembly/renders/auger_unit_steps.gif) |
| Fastener notes, including where the rig differs from the CAD | [`cad/full-assembly/README.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/ce256c3/cad/full-assembly/README.md#fasteners) |
| Printed-part files | Sam's Fusion 360 files on the lab account (share links in [§2.1](#21-what-fits-where)); STEP exports in [`components/fusion-step/`](https://github.com/vertical-cloud-lab/powder-doser/tree/ce256c3/cad/full-assembly/components/fusion-step) |
| V2 PCB gerbers | [`hardware/PCBs/POWDER_DOSER_V2.zip`](../../hardware/PCBs/POWDER_DOSER_V2.zip) (JLCPCB) |
| Purchasing status for 25 | [`orders/remaining-to-order-25-dosers.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/3048472/orders/remaining-to-order-25-dosers.md) and [`orders/digikey-reorder-25-dosers.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/3048472/orders/digikey-reorder-25-dosers.md) (PR #115) |

The July draft of full build instructions (`BUILD-INSTRUCTIONS.md` on branch
`claude/issue-121-20260702-2151`, issue #121) predates Sam's current parts.
Use it for the electronics overview only; your notes from doser #1 are what
will bring it up to date.

## 2. Printing

### 2.1 What fits where

Measured from the STEP files with [`print_fit.py`](print_fit.py). Sizes are
for the part lying on its largest flat face (the auger stands on end). The
A1 mini's build volume is 180 × 180 × 180 mm; the H2D's is 350 × 320 × 325 mm.

| Part | Per doser | Size as printed (mm) | Fits A1 mini? | Printer | g per doser | g for 25 | File |
|---|---:|---|---|---|---:|---:|---|
| Mounting plate (with both 28T tilt gears) | 1 | 149.5 × 108.2 × 54.7 | yes, one per plate | A1 mini | 70.17 | 1,754 | [Fusion](https://a360.co/4xXUj8L) |
| Auger bracket | 2 | 60.0 × 53.0 × 12.0 | yes | A1 mini | 11.86 | 297 | [Fusion](https://a360.co/46XtYN1) |
| Tap collar | 1 | 60.3 × 46.0 × 17.0 | yes | A1 mini | 9.58 | 240 | [Fusion](https://a360.co/4AIIgyz) |
| Tap-collar base (hard stop) | 1 | 60.0 × 18.0 × 21.0 | yes | A1 mini | about 12* | about 300 | [STEP](https://github.com/vertical-cloud-lab/powder-doser/blob/ce256c3/cad/full-assembly/components/ai-step/tap-collar-base.step) (PR #51) |
| Auger cap | 1 | 29.0 × 28.9 × 27.0 | yes | A1 mini | 10.78 | 270 | [Fusion](https://a360.co/4w9kRE5) |
| Servo pinion, 14T | 2 | 20.8 × 20.4 × 12.3 | yes | A1 mini | 4.54 | 114 | [Fusion](https://a360.co/4dcGSdF) |
| Stepper pinion, 20T | 1 | 21.8 × 21.8 × 16.1 | yes | A1 mini | 1.93 | 48 | [Fusion](https://a360.co/4yqSHFz) |
| **Baseplate** | 1 | **190.0** × 115.0 × 92.2 | **no**, 10 mm too long every way | **H2D** | 86.88 | 2,172 | [Fusion](https://a360.co/4AOA7sI) |
| **Auger** (threaded storage, 44T gear) | 1 | 45.9 × 45.9 × **250.0** | **no** | **H2D** | 66.33 | 1,658 | [Fusion](https://a360.co/4y1oz2H) |
| **Total** | | | | | **about 274** | **about 6.9 kg** | |

Grams are from Sam's slicer sheet (262.07 g per doser, posted on PR #115).
*The tap-collar base wasn't on that sheet, so its 12 g is scaled from its
volume against the tap collar's.

That splits as **about 121 g per doser on the A1 mini (3.0 kg for 25)** and
**153 g per doser on the H2D (3.8 kg for 25)**. With failed prints, plan on
about eight 1 kg spools for 25 dosers.

### 2.2 A1 mini queue (start now)

1. **One full A1 mini set for doser #1 first** (everything in the table
   above the baseplate). Before printing more, test-fit it: the 14T and 20T
   pinions should mesh with their 28T and 44T gears without binding, the
   brackets should slide onto the auger tube, and M3 screws should pass
   their holes.
2. **Then batch.** The mounting plates are the long pole: one per plate,
   so 25 separate jobs. Keep the A1 mini busy with those during the day
   and run plates of small parts (brackets, collars, bases, caps, pinions)
   overnight. Group small parts by type so one failed plate doesn't cost a
   whole doser set.
3. **Settings.** Ask Sam for his Bambu Studio project files: they carry the
   orientation and the profile his gram counts came from. If they aren't
   handy, PLA with a 0.4 mm nozzle, 0.2 mm layers, 3 to 4 walls and 25 to
   30 % infill is what the July draft used. Print gears with their axis
   vertical.

### 2.3 H2D slots (baseplates and augers only)

Only the baseplate and the auger are too big for the A1 mini, so put every
H2D slot toward those two.

- **Baseplates:** two fit per plate side by side (2 × 115 mm across, 190 mm
  deep).
- **Augers:** stand them on end, as in the 16-auger batch in #134, which ran
  for several days. Print their caps on the A1 mini to fit more augers per
  plate (#134 did the same).
- **If you only get one slot soon,** make it count toward complete dosers:
  2 baseplates plus 2 or more augers lets you build and test doser #1 (and #2)
  while the A1 mini works through the rest.
- **Label every auger** with a unique 6-character ID (lowercase), as set up
  in #134.

Two ways to free up the H2D, worth raising with Sam:

- The baseplate is only 10 mm over the A1 mini's 180 mm. A version that is
  10 mm shorter, or split in two and bolted together, would move all 25
  baseplates off the H2D.
- The auger can't shrink without losing capacity, but any 256 mm-class
  Bambu printer (A1, P1S, X1C) fits it standing, with 6 mm to spare.

## 3. Inventory check

Purpose: find out what's missing for the repeat dosers **before** assembly
starts. Open [`inventory-checklist.csv`](inventory-checklist.csv) in Excel or
Google Sheets, count what's physically on hand into the `On hand` column, and
fill in `Short`. Most purchased parts were delivered to the U (ask
@kinstonwithoutg / @Dila-Kandel for their counts), so count what's at BYU
yourself and merge the two.

### 3.1 Where things stood in PR #115 (as of 2 Oct)

| Status | Items |
|---|---|
| **Arrived, 25 of each** (15 Sep) | Tic T500, Pololu #3776 shunt regulator, NEMA-11 11HS18-0674S, Adafruit 412 solenoid (12 V), DRV8871, DRV2605L, ERM vibration disc, Waveshare Pico-2CH-RS232. Also 1 Raspberry Pi 5 kit, the carousel's NEMA 34 + CL86T, and 2 balances. |
| **On the DigiKey re-order** (cancelled order, cart re-cut 18 Sep) | 25 Pico 2 WH, 50 MG996R servos, 25 × 12 V/5 A bricks + AC cords, 0.1″ headers, optional 100 µF caps. **Whether it has been placed or arrived isn't recorded in the PR yet; check first.** |
| **Still missing** (@Dila-Kandel, 24 Sep) | 25 Pololu D24V22F5 5 V bucks, M3/M5 fasteners, the 48 V carousel PSU (not needed for the dosers themselves) |
| **PCBs** | 4 spare V2 boards at BYU. At least 25 plus spares still to order from JLCPCB, possibly after small design tweaks. |
| **Not on any list yet** | PCB-mount 12 V barrel jack (1 per board), 38 mm mounting boards and #10 wood screws, stepper/servo/solenoid wiring, USB cables |

### 3.2 Check the fastener order against PR #170 before buying

The fastener list priced on 2 Oct came from the older `BILL-OF-MATERIALS.md`
§6.2 (M3 × 12 and M3 × 16 socket heads, plain hex nuts, M5 × 20 and M5 × 40).
The current rig's fasteners are the 52 per doser in PR #170's
[BOM](https://github.com/vertical-cloud-lab/powder-doser/blob/ce256c3/cad/full-assembly/BOM.md),
checked joint by joint against the CAD: button heads under the mounting plate
(only 2 mm of clearance), nylon-insert locknuts on the servos, brackets and
hinge (the rig's hinge screws were backing out, #116), M5 × 45 hinge screws,
and #10 wood screws into the board. Those are the lines in the checklist.
Order from that list, not the 2 Oct one. Two notes from PR #170's README:

- The rig itself mostly uses zinc-plated Phillips pan heads, so its hardware
  won't match the list exactly. The list is the consistent set.
- The solenoid's ears may be clearance holes rather than tapped (nuts came
  off it, #117). If so, use M3 × 8 with a locknut instead of the two M3 × 5.
  Check on one solenoid and order accordingly.

### 3.3 What goes on each V2 PCB

From the component placements in the gerber zip (`FlyingProbeTesting.json`),
so you can check every board has its parts:

| Footprint | Pads | Part |
|---|---:|---|
| `pico_l`, `pico_r` | 2 × 20 | Pico 2 WH (comes with headers) |
| `waveshareleft`, `waveshareright` | 2 × 20 | Waveshare Pico-2CH-RS232 (balance link) |
| `tic` / `ticpower` | 3 / 2 | Tic T500 serial (GND, RX, TX) and 12 V input |
| `stepperpins`, `stepperpins_OUT` | 4 + 4 | Tic motor outputs to the NEMA-11 lead |
| `solenoiddriver` | 4 | DRV8871 (GND, 12 V, IN1, IN2) |
| `hapticdriver` | 5 | DRV2605L (EN, SDA, SCL, GND, 3V3) |
| `Shunt` | 4 | Pololu #3776 shunt regulator |
| `5v_reg` | 5 | Pololu D24V22F5 5 V buck (12 V in, 5 V out) |
| `servo_l`, `servo_r` | 3 + 3 | MG996R plugs (signal, 5 V, GND) on 3-pin male headers |
| `12vBarrel` | 3 | PCB-mount 5.5 × 2.1 mm jack for the 12 V brick |
| `3v_cap`, `5v_cap`, `12v_cap`, `tic_cap` | 2 each | 4 electrolytic caps |

Two things to check with William against the boards BYU already built:

- **Caps:** that's 4 per board, so the optional 100 caps on the DigiKey cart
  are exactly enough for 25 with no spares. The pads are 5.0 mm apart; a
  6.3 mm-diameter 100 µF cap such as ECA-1EM101B has 2.5 mm leads, which
  have to be bent out to fit. Use the values and parts on the BYU boards.
- **Barrel jack:** match the jack used on the BYU boards. PR #115 suggested
  Same Sky PJ-002AH.

## 4. Build order

1. **Doser #1, start to finish, with help.** Mechanics with Sam, following
   the 19 steps in PR #170's
   [BOM.md](https://github.com/vertical-cloud-lab/powder-doser/blob/ce256c3/cad/full-assembly/BOM.md#build-steps)
   and the GIFs. Then electronics with William: solder the V2 PCB, flash
   the Pico, and bench-test the stepper, both servos, the solenoid tap, the
   vibration motor and the RS-232 link to a balance. William has wanted to
   film a full assembly for a video tutorial (PR #115, 18 Sep), so doser #1
   is a good one to record.
2. **Firmware.** The Pico 2 WH is an RP2350, so it needs the RP2350 build
   of MicroPython, not the RP2040 one. The documented firmware is
   `hardware/test-module/firmware/` on the PR #100 branch
   ([`d3a42d7`](https://github.com/vertical-cloud-lab/powder-doser/tree/d3a42d7/hardware/test-module/firmware));
   the code on the current rig was backed up in PR #166
   ([`data/trickle-tap/2026-09_pico-flash-backup/`](https://github.com/vertical-cloud-lab/powder-doser/tree/4de0faa/data/trickle-tap/2026-09_pico-flash-backup/pico-root-code)).
   Ask William which one to flash.
3. **Write down every snag** with a photo: wrong screw length, a part that
   needed sanding, a step that was out of order. Post them on issue #121;
   they are what turns the July draft into working build instructions.
4. **Then batch** the rest. Keep a one-line record per doser (auger ID,
   date built, anything unusual).

## 5. Who to ask

| Person | For |
|---|---|
| Sam Charles (@swcharles) | Printed parts, Fusion files, print settings, the H2D-saving baseplate idea |
| William Mulberry (@williamulbz) | Electronics, the V2 PCB, firmware |
| Luke Winters (@lbwinters) | PCB design |
| @kinstonwithoutg, @Dila-Kandel | Purchased parts and orders at the U |
| Sterling Baird (@sgbaird) | Priorities and anything blocked |

## 6. Open questions

1. How many dosers are in this first batch, and where are they assembled
   (BYU, the U, or both)?
2. Standalone dosers like the bench rig (this page), or modules for the
   multi-doser carousel (#128)? Sam's 8 Oct carriage changes the mounting
   plate, so confirm before printing 25 mounting plates.
3. Has the DigiKey re-order (Pico 2 WH, servos, bricks) been placed?
4. Are V2 PCB tweaks planned before the order of 25 or more?
5. Can the baseplate be trimmed to 180 mm so it prints on the A1 mini?

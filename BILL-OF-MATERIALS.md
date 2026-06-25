# Powder-Doser — Bill of Materials (BOM)

Consolidated, current bill of materials for the powder-doser (a.k.a.
"powder-excavator") project, scraped from the issues, pull-request
discussions, and branch files of this repository. Because the design has
gone through many iterations, this document records the **most recent
design decision** for each subsystem and notes what it superseded.

> **Status:** Most of the detailed CAD and electronics work lives on open
> (un-merged) feature branches/PRs, so part numbers here are the current
> *design intent* and are subject to change until the branches land on
> `main`. Each line cites the issue/PR it came from. Prices are
> approximate single-unit USD from vendor pages at time of writing.

## How this document is organized

- [1. Most-recent design decisions (supersession log)](#1-most-recent-design-decisions-supersession-log)
- [2. Single-channel bench test-module — electronics BOM (current)](#2-single-channel-bench-test-module--electronics-bom-current)
- [3. Scale / closed-loop feedback](#3-scale--closed-loop-feedback)
- [4. Power, battery & UPS](#4-power-battery--ups)
- [5. Production multi-channel electronics BOM (reference)](#5-production-multi-channel-electronics-bom-reference)
- [6. Mechanical / 3D-printed parts & fasteners](#6-mechanical--3d-printed-parts--fasteners)
- [7. Filament & print settings](#7-filament--print-settings)
- [8. Open questions / not-yet-specified](#8-open-questions--not-yet-specified)
- [9. Commercial reference systems (comparison only)](#9-commercial-reference-systems-comparison-only)
- [10. Source provenance](#10-source-provenance)

---

## 1. Most-recent design decisions (supersession log)

| Subsystem | Current choice | Superseded / rejected | Source |
|---|---|---|---|
| Bench-rig host MCU | **Raspberry Pi Pico W** (RP2040 + CYW43439) | Raspberry Pi Zero 2 W (kept for production orchestration) | #60, PR #61 |
| Production host | **Pi Zero 2 W orchestrator** likely driving an array of Pico-W satellites | Single Pi-direct fan-out | #44/PR #45, #60 |
| Stepper driver | **Pololu Tic T500** (USB/serial, MP6500, on-board planner) | bare Pololu DRV8825 carrier (kept as cost alt; Tic T825 as drop-in upgrade) | PR #61 |
| Stepper motor | **NEMA 11 11HS18-0674S** (0.67 A/phase, 10 N·cm) | SparkFun ROB-10848 (was NEMA 17, under-rated) | PR #25 |
| Scale RS-232 interface | **Waveshare Pico-2CH-RS232 module** (SP3232EEN) | discrete MAX3232 breakout (SparkFun BOB-11189) + Molex 43645 receptacle | #102, PR #100 |
| Tilt / dispensing-angle servo | **MG996R** (×2, mirrored) — physically built & tested | HD-1810MG (#1142) was the original electronics-BOM pick; still referenced in firmware notes | #65, PR #66 vs PR #25/#61 |
| Baseplate tilt actuation | **Dual MG996R servos + involute gear band** on the hinge | Glideforce GF01-121010-1-66 linear actuator (optional, still in production BOM) | PR #66 vs PR #25 |
| System AC power | **Mean Well GST60A12-P1J** 12 V / 5 A brick | Adafruit #352 (out of stock 2026-Q2); adjustable #4880 avoided | PR #25 |
| Back-up / conference power | **Eaton Tripp Lite SMART1500LCDT UPS** (ordered) | portable power station / LiFePO4 packs from the battery study | #85, PR #86 |
| Back-EMF clamp | **Pololu #3776 33 V / 9 W shunt regulator** (now required) | (was optional) | PR #25, PR #61 |
| Auger | **Geared Archimedes auger v3, "nozzle 4"** (Ø25 tube, 48T band, Ø3 exit) | nozzles 1–3; empty-tube revisions | #48, PR #49, PR #68; `Auger4.stl` on `main` |

---

## 2. Single-channel bench test-module — electronics BOM (current)

This is the **most up-to-date, authoritative parts list** for the working
bench rig: one powder-doser channel driven from a single Pico W. From
`hardware/test-module/README.md` on the scale-feedback branch (PR #100,
which builds on PR #61). Only `GP0..GP15` are used, so a plain Pico, Pico
W, or Pico WH all work.

| Ref | Part | Vendor / P-N | Qty | Notes |
|---|---|---|---|---|
| U2 | Raspberry Pi **Pico W** (RP2040 + CYW43439) | Raspberry Pi | 1 | Bench host MCU; ~$6. |
| U1 | **Pololu D24V22F5** 5 V / 2.5 A buck regulator | Pololu #2858 | 1 | 12 V → 5 V for Pico + servos + solenoid. |
| U3 | Adafruit **DRV2605L** haptic driver breakout | Adafruit #2305 | 1 | I²C, drives the ERM. ~$7.95 |
| M1 | 10 mm **ERM coin** vibration motor (3 V) | Adafruit #1201 | 1 | Or an LRA (`VIBRATION_LIBRARY = 6`). ~$1.95 |
| U4 | Adafruit **DRV8871** DC motor driver breakout | Adafruit #3190 | 1 | Drives the tap solenoid. ~$7.50 |
| SOL1 | **JF-0530B** 5 V push-pull solenoid | Adafruit #412 | 1 | The tap actuator (~4.5 mm stroke). ~$7.50 |
| U5 | **Pololu Tic T500** USB stepper controller (MP6500) | Pololu #3135 | 1 | Drives auger over TTL serial (UART1: GP4→RX, GP5←TX). ~$32.95 |
| SR1 | **Pololu #3776** 33 V / 9 W shunt regulator | Pololu #3776 | 1 | Across +12 V/GND at U5 VIN; clamps stepper back-EMF. ~$14.95 |
| M2 | **NEMA-11 11HS18-0674S** bipolar stepper | StepperOnline | 1 | Direct-coupled to the auger. ~$13–15 |
| M3 (+M4) | Dispensing-angle / tilt servo | see note ▼ | 1–2 | Two servos on opposite sides, driven in unison (firmware mirrors servo 2). |
| J1 | **Mean Well GST60A12-P1J** 12 V / 5 A barrel-jack PSU | Digi-Key | 1 | System power. ~$18.60 (+ IEC cord + barrel pigtail) |
| C1 | 100 µF / 25 V electrolytic (12 V bulk) | any | 1 | 12 V rail decoupling. |
| C2 | 100 µF / 10 V electrolytic (5 V bulk) | any | 1 | Tames servo + solenoid transients on 5 V. |
| C3 | 100 µF / 25 V electrolytic (2nd bulk) | any | 1 | Directly on Tic T500 VIN terminals. |
| U6 | **Waveshare Pico-2CH-RS232** module (SP3232EEN) | Waveshare 19979 / PiShop.us | 1 | Scale RS-232 ↔ Pico logic. **Power VCC from +3V3, not 5 V.** UART0 GP12/GP13. ~$8.95 |
| — | RS-232 cable (DB9 ↔ A&D HR-100A) | — | 1 | "Buzz out the harness with a meter first." |
| — | A&D **HR-100A** analytical balance (102 g × 0.1 mg) | A&D | 1 | Lab equipment, not purchased for the build; closed-loop mass sensor. |
| — | Half-size breadboard, jumper wires, 0.1″ headers | any | — | Bench wiring substrate (replaces the production Perma-Proto Bonnet). |

> **Tilt-servo note (M3/M4):** the electronics docs (PR #25 item 16, PR
> #61/#100 BOM) list the **Adafruit HD-1810MG metal-gear servo (#1142,
> ~$22.50)**. However the most-recent *mechanical* design and the
> physically-built prototype use the **TowerPro MG996R** (issue #65: *"We
> will use an MG 996R for the time being,"* PR #66 dual-servo gear-band
> hinge). Treat **MG996R as the current physical part**; the HD-1810MG is
> a higher-precision alternative the firmware/electronics were originally
> sized around.

Approx. bench-rig electronics cost: **≈ $70 + $19 (PSU) + $13 (stepper) +
~$10 (breadboard/jumpers) + Pico W (~$6)** ≈ **$120**, plus the
scale-interface module (~$9) and the (lab-owned) balance.

### Pin / net contract (Pico W)

| Net | Pico W GPIO | Goes to |
|---|---|---|
| I2C_SDA / I2C_SCL | GP0 / GP1 | DRV2605L (U3) |
| STP_TX / STP_RX | GP4 / GP5 | Tic T500 (U5) UART1 (cross-over) |
| SOL_IN1 / SOL_IN2 | GP10 / GP11 | DRV8871 (U4) |
| HAPT_EN | GP14 | DRV2605L EN/IN_TRIG |
| SERVO_SIG / SERVO_SIG2 | GP15 / GP2 | tilt servos M3 / M4 |
| SCALE_TX / SCALE_RX | GP12 / GP13 | Waveshare RS-232 (U6) UART0 |

Source: `hardware/test-module/firmware/config.py`, `hardware/test-module/README.md` (PR #61, PR #100).

---

## 3. Scale / closed-loop feedback

Closed-loop "dose to a target mass" for conference demos (issue #99,
PR #100). Auger runs coarse to ~90 % of target, then the solenoid taps to
trim to the exact mass.

| Item | Part | Notes |
|---|---|---|
| Balance | **A&D HR-100A** (102 g × 0.1 mg, RS-232C) | A&D Standard Format protocol (`Q`/`S`/`Z` commands; `ST,`/`US,`/`OL,` frames); default **2400-7-E-1**, CR LF. Lab equipment. |
| Level shifter | **Waveshare Pico-2CH-RS232** module (SP3232EEN) | Replaces the earlier discrete MAX3232 (BOB-11189) + Molex 43645 receptacle design; ordered per issue #102 (PiShop.us). Power from **+3V3**. |
| Cable | DB9 ↔ HR-100A RS-232C port | Crossover lives only in the DB9 cable; meter out the pinout first. |

Firmware: `firmware/scale.py` (A&D driver), `firmware/dosing.py` (two-phase
coarse/fine controller), CPython simulation under `firmware/sim/`.
Validated by ngspice (`analysis/rs232_analysis.py`, 9/9 checks) — a direct
GPIO connection to the scale was quantitatively rejected (RP2040 abs-max
violation), confirming the transceiver is required.

---

## 4. Power, battery & UPS

| Item | Part | Vendor / P-N | Notes |
|---|---|---|---|
| AC adapter (primary) | Mean Well **GST60A12-P1J**, 12 V / 5 A / 60 W | Digi-Key | Ships **without** AC cord. ~$18.60 |
| AC line cord | IEC-C14, NEMA 5-15P → C13, ~6 ft | Digi-Key (e.g. Tripp Lite P006-006) | ~$5 |
| Barrel pigtail | 2.1 × 5.5 mm DC jack → screw terminals | Digi-Key / Adafruit #368 | ~$2.50 |
| Buck regulator | Pololu **D24V22F5** 5 V / 2.5 A | Pololu #2858 | 12 V → 5 V. ~$18.95 |
| Conference back-up power | **Eaton Tripp Lite SMART1500LCDT** UPS | Digi-Key #4439114 | 1500 VA / 900 W; ordered (BYU ME order #12929). **Current decision** — supersedes portable-power-station / LiFePO4 options from the PR #86 battery study. |

The PR #86 battery study (`paper/background/15-battery-power-options.md`)
catalogued portable power stations (#1 recommended there), 12.8 V LiFePO4
packs, SLA, USB-C PD, and tool-battery options with a runtime model
(`runtime_h ≈ Wh × 0.85 / 60 W`). A BYU PSC 3 Ah LiFePO4 pack was
considered but rejected (~30–35 min runtime). The team ultimately ordered
the UPS above for demo reliability (issue #85, PR #86 comments).

---

## 5. Production multi-channel electronics BOM (reference)

The original full, numbered BOM for the multi-channel production system
lives in `hardware/vibration-motor-and-solenoid.md` (PR #25, resolving
issue #24). The bench rig in §2 is a single-channel subset of this. Items
are **per-channel** unless marked *system-shared*.

| # | Part | Vendor / P-N | Qty | ~USD | Notes |
|---|---|---|---|---|---|
| 1 | DRV2605L haptic controller breakout | Adafruit #2305 | 1/ch | 7.95 | Fixed I²C addr 0x5A → forces fan-out / per-module bus at N>1. |
| 2 | ERM coin vibration motor, 10×2.7 mm, 3 V | Adafruit #1201 | 1/ch | 1.95 | Default vibrator. |
| 3 | LRA (~10 mm coin), optional alt to #2 | Precision Microdrives / Digi-Key | 0–1 | ~5 | Adafruit #1631 LRA discontinued. |
| 4 | JF-0530B 5 V push-pull solenoid | Adafruit #412 | 1/ch | 7.50 | Tap actuator. |
| 5 | DRV8871 DC motor driver breakout | Adafruit #3190 | 1/ch | 7.50 | Drives the solenoid. |
| 6 | Perma-Proto Bonnet Mini Kit for Pi | Adafruit #2310 | 1 | 4.95 | Solder substrate (bench rig uses a breadboard instead). |
| 7 | 5 V ≥2 A supply *(dual-supply variant only)* | any | 1\* | — | Omit when using buck (#15). |
| 8 | 2.1 mm barrel-jack breakout *(dual-supply only)* | Adafruit #373 | 1\* | 0.95 | Omit when using buck. |
| 9 | Headers, jumpers, 100 µF/10 V bulk cap | any | — | — | 5 V rail decoupling. |
| 10 | NEMA 11 bipolar stepper, 11HS18-0674S | StepperOnline | 1/ch | 13–15 | 28 mm face, Ø5 shaft, 0.67 A/phase, 10 N·cm. |
| 11 | **Pololu Tic T500** stepper controller (default) | Pololu #3135 | 1/ch | 32.95 | High-level "go to position N"; no host step-pulse generation. |
| 11-alt | Pololu DRV8825 carrier (cost alternative) | Pololu #2133 | 1/ch | 15.95 | Saves ~$17/ch; host generates STEP/DIR. |
| 12 | 5 mm ↔ 5 mm flexible shaft coupler | StepperOnline ST-FC01 | 1/ch | 1–6 | Direct-drive to auger. |
| 13 | Mean Well GST60A12-P1J 12 V / 5 A PSU | Digi-Key | 1 *(system)* | 18.60 | + 13a IEC cord (~$5), + 13b barrel pigtail (~$2.50). |
| 14 | 100 µF / 25 V electrolytic (VMOT/VIN bulk) | any | 1/ch | <0.50 | Required by Pololu for DRV8825; helps Tic too. |
| 15 | Pololu D24V22F5 5 V / 2.5 A buck regulator | Pololu #2858 | 1 *(system)* | 18.95 | Single-supply variant. |
| 16 | HD-1810MG metal-gear servo (auger-tilt) | Adafruit #1142 | 0–1/ch | 22.50 | *Optional.* See §2 tilt-servo note — physical build uses MG996R. |
| 16-alt | SG-92R micro servo (cheaper tilt alt) | Adafruit #169 | 0–1 | 5.95 | For light ±15° wipers. |
| 17 | M2/M3 servo-horn → tilt-bracket hardware | bench-stock | 0–1 | <2 | Only with #16/#16-alt. |
| 18 | **Pololu #3776** 33 V / 9 W shunt regulator | Pololu #3776 | 1/ch | 14.95 | Now a **required** item (back-EMF clamp). |
| 19 | Glideforce GF01-121010-1-66 linear actuator, 100 mm | Pololu #4467 | 1 *(system)* | 79.95 | *Optional* whole-plate horizontal↔vertical tilt; limit-switch variant (Pi has no ADC). |
| 19-alt | Generic 12 V ~100 mm linear actuator | Amazon (ECO-WORTHY etc.) | 1 *(system)* | ~25–35 | Lower duty-cycle; plug-compatible. |
| 20 | 2nd DRV8871 breakout (drives actuator #19) | Adafruit #3190 | 1 *(system)* | 7.50 | Only with #19/#19-alt. |

*System-shared host (production, Pi Zero 2 W path):* Raspberry Pi Zero 2 W
(Adafruit #5291, ~$19.05) + heat sink (#3084, ~$0.95) + 16 GB microSD
(#2693, ~$9.95) + 5 V/2.4 A USB PSU (#1995, ~$7.50).

Cost (default Tic path, items 1,2,4,5,6,10,11,12,14,18): **≈ $98/channel**
+ **≈ $65 system-shared** → **≈ $163** for a single-channel v1.0; **≈ $250**
with the linear-actuator tilt; **≈ $146** with the DRV8825 cost-down path.

### Production multi-channel architecture (issue #44 / PR #45)

To scale past ~6 channels the Pi Zero 2 W runs out of GPIO and all
DRV2605Ls collide on I²C 0x5A. The evaluated/recommended topology is
**USB-CDC satellites**: one **RP2040 (Pico) per module** carrying a
**TMC2209** SilentStepStick (≈$5, replacing the ~$33 Tic T500 to control
per-channel cost), DRV8871, and DRV2605L, all reporting to a **Pi Zero
2 W host** over USB-CDC. A 50×50 mm 2-layer "satellite Rev A" board was
sketched (~$15–25/board). A CAN-bus satellite variant is the v2 fallback.

---

## 6. Mechanical / 3D-printed parts & fasteners

All printed parts are FDM (PLA or PETG). All assembly CAD currently lives
on open feature branches; the consolidated parametric spec is
`cad/powder-doser-assembly/SPEC.md` + `params.py` (PR #112). `Auger4.stl`
is the only CAD artifact currently on `main`.

### 6.1 Printed parts

| Part | Qty | Key dimensions | Source |
|---|---|---|---|
| **Auger — geared, "nozzle 4"** (full) | 1 | Ø25 mm OD × 250 mm, 2 mm wall (Ø21 bore); internal Archimedean screw Ø8 shaft, 10 mm pitch, 2 mm fin; Ø3 mm axial exit; 12 mm funnel; external **48T** spur band (module 1.0, 20° PA, Ø50 tip) at L/3 from tip; 4× loading slots; M3 top pilot. | #48, PR #49, PR #68 |
| Auger (180 mm) variant | 1 | Same Ø25 tube + 48T band, 180 mm long. | PR #49 |
| Auger (90 mm) bench variant | 1 | Ø25 × 90 mm, **no** gear band. | PR #49 |
| Auger — threaded sealable | 1 | Same tube + external thread (pitch 4.0, 25.4 mm long, crest flush to Ø25). | PR #49 |
| Thread cap | 1 | Internal mating thread, 0.35 mm hand-fit clearance, 3 mm wall. | PR #49 |
| **Stepper pinion** | 1 | **16T**, module 1.0, Ø18 tip, Ø5 bore + hub, M3 setscrew. Drives the 48T auger band at **3:1**, centre distance 32 mm. | PR #49, PR #112 |
| **Servo pinion** | 2 | **20T**, module 0.9083, Ø20.2 tip, Ø6 + flat bore for MG996R 25T spline. Drives the 40T hinge gear at **2:1**, centre distance 27.25 mm. | PR #66 |
| **Mounting plate** | 1 | 108.2 × 130 × 6 mm; auger/dispense axis at Z = +29.25 mm; 32 mm front U-notch; NEMA-11 motor face (4× M3 @ 23 mm + Ø22 pilot); Ø18 hinge eyes (M5 bore) with integrated **40T** hinge gear per side. | #62, PR #63, PR #66 |
| **Baseplate** | 1 | 200 × 60 × 6 mm; 4× M5 corner holes; sloped hinge arms for 0–45°+ sweep; servo posts at X = ±79 mm. | PR #63, PR #66 |
| **Auger bracket** (shaft collar + flange) | 2 | 60 × 12 × 14 mm flange; Ø25.5 bore (0.5 mm running fit), Ø33.5 collar; M3 clamp slot; 2× M3 mount holes; bore axis Z = 29.25 mm; brackets 180 mm apart. | #46, PR #47 |
| **Tap collar** (rotates on auger) | 1 | Ø33.5 OD / Ø25.5 bore, 24 mm deep; M3 clamp; Ø10×1 coin-motor recess; solenoid boss (2× M3 self-tap, 18.2 × 16.0 mm diagonal pitch, Ø7.5 plunger bore); 3 mm solenoid interference into bore = "the tap". | #50, PR #51 |
| **Tap-collar mount plate** | 1 | 60 × 24 × 14 mm; 4× M3 mount holes; half-cylinder collar relief R17; hardstop bump. | PR #51 |
| Channel-sealing cap *(prototype concepts)* | — | Twist-shutter (60° throw), spring-loaded auto-hatch, or bayonet plug with 1.5 mm O-ring face seal. Not finalized. | #36, PR #37 |

### 6.2 Off-the-shelf mechanical hardware

| Item | Qty | Spec | Source |
|---|---|---|---|
| NEMA 11 stepper | 1 | 11HS18-0674S, 28×28 mm, Ø5 shaft | PR #25/#49 |
| **MG996R servo** | 2 | 40 × 20 × 36.8 mm, 25T spline (tilt/hinge drive) | #65, PR #66 |
| Adafruit 412 / TAU0730TM solenoid | 1 | 12 V push/pull, Ø6.9 bushing | #24, PR #51 |
| Ø10 coin vibration motor (ERM) | 1 | adhesive-backed | PR #51 |
| 5 mm flexible shaft coupler | 1 | direct-drive (if not gear-driven) | PR #25 |
| M3 clamp screws | 3 | 1 per auger bracket (×2) + 1 tap collar | PR #47/#51 |
| M3 × 12 SHCS + nut (bracket mounting) | 8 | 4 per bracket × 2 | PR #59 |
| M3 × 12 SHCS + nut (tap-collar mount) | 4 | — | PR #59 |
| M3 × 8 SHCS (NEMA-11 mount) | 4 | 23 mm bolt pattern | PR #59 |
| M3 self-tapping (solenoid) | 2 | into Ø2.7 pilots | PR #51 |
| M3 setscrew (stepper pinion) | 1 | into Ø2.5 pilot | PR #112 |
| M5 hinge pin + lock-nut | 2 | one per side (Ø5 pin, Ø5.4 bore) | PR #57/#63 |
| M5 baseplate corner bolts | 4 | Ø5.4 clearance | PR #63 |
| M5 servo-flange side bolt | 2 | one per servo flange | PR #66 |

**Fastener pilot/clearance convention** (`params.py` §7): M3 clearance
Ø3.4, M3 self-tap pilot Ø2.7, M3 setscrew pilot Ø2.5, M5 clearance Ø5.4,
printed-thread clearance 0.35 mm, gear backlash ≈ 0.15 mm.

> No heat-set inserts and no ball/needle bearings are specified — printed
> holes are clearance or self-tapping pilots, and the auger turns in plain
> FDM running-fit collar bores (0.5 mm diametral clearance). This is a
> deliberate design choice.

### 6.3 Auger capacity (for dosing math, PR #81)

Auger-4 capacity `V(mL) ≈ 0.283·L − 3.93` (L in mm): ≈ 21.6 mL @ 90 mm,
≈ 32 mL @ 127 mm (~38 g fine NaCl), ≈ 66.8 mL @ 250 mm. Dose ≈ **2.83
mL/rev** (10 mm screw pitch).

### 6.4 Platform / frame (issue #113)

A simple wooden test-stand frame was built: ~5× 6-inch lengths of 2×4
lumber, a tabletop, and ~16 wood screws.

---

## 7. Filament & print settings

| Setting | Value | Source |
|---|---|---|
| Material | **PLA or PETG** | PR #53, PR #59 |
| Layer height | 0.2 mm | PR #59 |
| Infill | 25–30 % | PR #59 |
| Perimeters / walls | 3–4 | PR #59 |
| Nozzle | 0.4 mm | PR #59 |
| Supports | none for bracket/tap-collar (print face-down); tree supports under mounting-plate hinge pillars | PR #51/#53/#59 |

Parts were printed **in-house** (issue #72). The maintainer has noted that
**filament cost still needs to be accounted for** (issue #114) — no
per-part gram/cost figures are recorded in the repo yet (see §8).

---

## 8. Open questions / not-yet-specified

- **Filament / print cost** — not yet tallied; flagged in issue #114 as a
  cost to consider. No per-part mass or $/part data exists in the repo.
- **Static electricity** (issue #84, no comments yet) — open question of
  whether to make the auger from a groundable material or just ground the
  aluminum dispense crucible. No anti-static parts specified.
- **Solenoid impulse adequacy** (issue #64, no recorded results) — the
  JF-0530B/Adafruit 412 solenoid is still in the BOM, implying it was
  adequate; fallback idea was a DC stepper + finger if impulse is too low.
- **Tilt servo conflict** — MG996R (mechanical, current) vs HD-1810MG
  (#1142, electronics BOM). Reconcile when the assembly branches merge.
- **Tic T500 SKU** — referenced as both Pololu #3135 and #3134; verify at
  checkout (same product, ~$32.95).
- **Branch status** — most CAD/electronics work is on un-merged PRs; only
  `Auger4.stl` is on `main`. Part numbers are current design intent.

---

## 9. Commercial reference systems (comparison only)

Surveyed for benchmarking (issue #32) — **not** part of the custom BOM:

- **Mettler-Toledo Chronect XPR** — full system ~$400k; up to 32 powders
  base (160 with carousel); inert-glovebox option.
- **Labman + Mettler-Toledo dosing head** — full system ~$330k; carousel
  of 56 dosing heads.
- **MTI** AM-PD6 / AM-PD16 / PF-A — quotes gathered.
- Reference test powders: AlSi10Mg (15–45 µm, MSE Supplies), Si –100+200
  mesh (Fisher), Si –325 mesh (Micron Metals).

---

## 10. Source provenance

| Topic | Issues / PRs | Key files |
|---|---|---|
| Full production electronics BOM | #24, PR #25 | `hardware/vibration-motor-and-solenoid.md` |
| Bench test-module electronics | #50, #60, PR #61 | `hardware/test-module/README.md`, `firmware/config.py` |
| Scale closed-loop feedback | #99, #102, PR #100 | `hardware/test-module/{README,scale-integration-report}.md`, `firmware/{scale,dosing}.py` |
| Battery / UPS | #85, PR #86 | `paper/background/15-battery-power-options.md` |
| Electrical/software architecture | #44, PR #45 | `design/electrical-software-brainstorming.md` |
| Auger | #48, #67, #80, PR #49/#68/#81 | `cad/auger-geared/`, `Auger4.stl` |
| Mounting plate / baseplate / servo tilt | #62, #65, PR #57/#63/#66 | `cad/mounting-plate*/` |
| Auger bracket | #46, PR #47/#53/#55 | `design/cad/auger-bracket/` |
| Tap collar | #50, PR #51 | `design/cad/tap-collar/` |
| Channel-sealing cap | #36, PR #37 | `design/cad/sealing-cap-*/` |
| Full parametric assembly | PR #107/#110/#112 | `cad/powder-doser-assembly/{SPEC.md,params.py}` |
| Prints / assemblies / design log | #72, #73, PR #74 | `DESIGN-LOG.md` |
| Commercial comparators | #32 | (issue thread) |
| Platform / frame, host OS | #98, #113 | (issue threads) |

*This BOM was compiled by scraping the repository's issues, PR
discussions, and feature-branch files (issue #114). Where a subsystem
iterated, the most-recent decision is recorded above with the older
option noted as superseded.*

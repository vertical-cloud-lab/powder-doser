# Powder Doser — Build Instructions

Step-by-step instructions for building one complete powder-doser channel:
mechanical assembly, electronics, software, and closed-loop dosing against
an analytical balance. They assume you have access to a 3D printer and all
of the electrical components (see the parts checklist in §2), but that
nothing is printed or assembled yet.

**Who this is for.** Someone comfortable with 3D printing and basic
hands-on construction (screwdrivers, hex keys, breadboards) who has *not*
worked on this project before. You do not need to be a mechanical or
electrical engineer — every step says exactly what to do and what it
should look like when done. Where a choice matters (screw size, wire
polarity, print orientation), it is called out explicitly.

**Time estimate.** *[PLACEHOLDER: total build time — expect roughly one
to two days of printing plus an afternoon or two of assembly, wiring, and
software bring-up. Update after the first guided build.]*

> **Placeholders.** This document is a first draft written ahead of the
> next physical build. Anything marked `[PLACEHOLDER: …]` is a value or
> photo we still need to capture from a real build — treat those as "to be
> confirmed," and trust everything else.

---

## Table of contents

1. [How the powder doser works](#1-how-the-powder-doser-works)
2. [What you need](#2-what-you-need)
3. [3D printing the parts](#3-3d-printing-the-parts)
4. [Mechanical assembly](#4-mechanical-assembly)
5. [Electronics](#5-electronics)
6. [Software setup](#6-software-setup)
7. [First power-on and channel tests](#7-first-power-on-and-channel-tests)
8. [Scale integration and closed-loop dosing](#8-scale-integration-and-closed-loop-dosing)
9. [Calibration and tuning](#9-calibration-and-tuning)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. How the powder doser works

The powder doser dispenses small, precise masses of powder (targeting
sub-milligram trim resolution with an analytical balance in the loop). One
"channel" is a horizontal printed tube — the **auger** — with an internal
Archimedean screw, held above a cup that sits on a balance.

There are four actuators, each with one job:

| Actuator | What it does |
|---|---|
| **NEMA-11 stepper motor** | Rotates the auger via a 16-tooth pinion meshing with a 48-tooth gear band printed onto the outside of the auger tube (3:1 reduction). Each revolution of the auger conveys ≈ 2.8 mL of powder toward the exit hole. This is the *coarse* dispense. |
| **Tap solenoid** | A small push-pull solenoid mounted on a collar around the auger. Each pulse taps the tube, shaking a few particles out of the exit. This is the *fine* trim. |
| **ERM vibration motor** | A coin-cell-sized vibration motor on the same collar. Buzzing it helps powder flow and un-sticks clogs. |
| **Two MG996R servos** | The whole mechanism sits on a **mounting plate** that hinges on a **baseplate**. Each servo drives a printed pinion meshing with a gear band on the mounting-plate hinge, tilting the assembly from horizontal (0°, storage/transport) to steep angles for dispensing. The hinge axis passes through the auger's dispense point, so the powder exit *does not move* as the assembly tilts. |

A **Raspberry Pi Pico W** microcontroller drives all four actuators and
talks to an **A&D HR-100A analytical balance** over RS-232. The firmware's
closed-loop dosing routine runs the auger to ~90 % of the target mass,
then fires solenoid taps until the balance reads the target within
tolerance.

For visual reference before you start:

- Full-assembly render: `cad/mounting-plate-assembly/assembly/assembly_iso_az090.png`
- Interactive 3D model (orbit/zoom in your browser):
  <https://cad.onshape.com/documents/ecf8ca6d0bd5040cb48b695e/w/f7136eb089ef839f6bde67fc>
- Tilt sequence: `cad/mounting-plate-assembly/assembly/rotation_0_45_90.png`
- Powder path: `cad/mounting-plate-assembly/assembly/powder_flow.png`
- Wiring schematic: `hardware/test-module/kicad/test_module.png`

*[PLACEHOLDER: photo of the completed physical build for the cover of
this document.]*

---

## 2. What you need

### 2.1 Tools

- 3D printer (an FDM printer with a ≥ 250 mm vertical build volume prints
  the full-length auger; a 180 mm variant exists for smaller printers)
- Metric hex keys / screwdrivers for M3 and M5 hardware
- Small adjustable wrench or pliers (for M5 lock nuts)
- Multimeter (continuity checks are **required** before first power-on)
- Wire strippers and jumper wires
- Computer with a USB-A or USB-C port, two micro-USB cables
- *[PLACEHOLDER: deburring knife / drill bits for cleaning printed holes,
  if experience shows they're needed]*

### 2.2 Printed parts (see §3 for files and settings)

| Part | Qty | Repo location |
|---|---|---|
| Auger, geared "nozzle 4" (Ø25 × 250 mm, 48T gear band) | 1 | `Auger4.stl` (also `cad/auger-geared/`) |
| Stepper pinion (16T, Ø5 bore) | 1 | `cad/auger-geared/stepper-pinion.stl` |
| Auger bracket (split shaft collar + flange) | 2 | `cad/mounting-plate-assembly/imported-parts/auger-bracket/` |
| Tap collar | 1 | `cad/mounting-plate-assembly/imported-parts/tap-collar/tap_collar.stl` |
| Tap-collar mount plate | 1 | `cad/mounting-plate-assembly/imported-parts/tap-collar/mount_plate.stl` |
| Mounting plate (with integrated 28T hinge-gear bands) | 1 | `cad/mounting-plate-assembly/stl/mounting_plate.stl` |
| Baseplate (rectangular mounting tab with servo posts) | 1 | `cad/mounting-plate-assembly/stl/baseplate.stl` |
| Servo pinion (14T, for MG996R spline) | 2 | `cad/mounting-plate-assembly/stl/servo_pinion.stl` |
| Hinge pin — only if not using M5 bolts | (2) | `cad/mounting-plate-assembly/stl/hinge_pin.stl` |

> **Note on gear versions.** The gear train has been revised to stop tooth
> stripping: the servo pinion / hinge gear pair is now **14T / 28T at
> module ≈ 1.3** (older files were 20T / 40T at module ≈ 0.91 — visibly
> finer teeth). Make sure you print the current STLs from this repository
> rather than files from an older download.

### 2.3 Fasteners

| Fastener | Qty | Used for |
|---|---|---|
| M3 × 12 socket-head cap screw + nut | 8 | Auger brackets → mounting plate (4 per bracket) |
| M3 × 12 socket-head cap screw + nut | 4 | Tap-collar mount plate → mounting plate |
| M3 × 8 socket-head cap screw | 4 | NEMA-11 stepper → motor wall (23 mm bolt pattern) |
| M3 clamp screw | 3 | 1 per auger-bracket collar (×2) + 1 tap collar |
| M3 self-tapping screw | 2 | Solenoid → tap collar (Ø2.7 pilots) |
| M3 setscrew | 1 | Stepper pinion → motor shaft (Ø2.5 pilot) |
| M3 screw (servo-horn thread) | 2 | Servo pinion retention on MG996R spline |
| M5 bolt/pin + lock nut | 2 | Hinge pins (one per side) |
| M5 bolt + nut | 4 | Baseplate tab → frame |
| Servo mounting screws (fit MG996R flange ears; posts have Ø5 holes) | 8 | MG996R servos → baseplate posts. *[PLACEHOLDER: confirm screw size/length used — M4 or #8 self-tappers both fit the MG996R flange]* |

### 2.4 Electronics

The authoritative, priced parts list with verified vendor links is
[`BILL-OF-MATERIALS.md`](BILL-OF-MATERIALS.md) — the table below is the
short version. All electronics mount on a half-size breadboard.

| Ref | Part | Role |
|---|---|---|
| U2 | Raspberry Pi Pico W | Controller (a plain Pico also works — only GP0–GP15 are used) |
| U1 | Pololu D24V22F5 buck regulator (5 V / 2.5 A) | 12 V → 5 V rail |
| U3 | Adafruit DRV2605L haptic driver breakout | Drives the vibration motor (I²C) |
| M1 | 10 mm ERM coin vibration motor | Vibration |
| U4 | Adafruit DRV8871 motor driver breakout | Drives the tap solenoid |
| SOL1 | JF-0530B 5 V push-pull solenoid | Tap actuator |
| U5 | Pololu Tic T500 USB stepper controller | Drives the auger stepper over serial |
| SR1 | Pololu #3776 33 V / 9 W shunt regulator | Clamps stepper back-EMF on the 12 V rail — **required** |
| M2 | NEMA-11 stepper, 11HS18-0674S (0.67 A/phase) | Auger drive |
| M3, M4 | TowerPro MG996R servo × 2 | Tilt/hinge drive |
| U6 | Waveshare Pico-2CH-RS232 module (SP3232EEN) | Balance RS-232 ↔ Pico logic levels |
| J1 | Mean Well GST60A12-P1J 12 V / 5 A barrel-jack PSU | System power |
| C1–C3 | 3 × 100 µF electrolytic capacitors (2 × 25 V, 1 × 10 V) | Rail decoupling |
| — | Half-size breadboard, jumpers, headers | Wiring substrate |
| — | DB9 RS-232 cable to the balance | Scale link |
| — | A&D HR-100A analytical balance (102 g × 0.1 mg) | Mass feedback (lab equipment) |

> **Servo note:** some electronics documents in this repo reference the
> Adafruit HD-1810MG servo — that was the original electronics-BOM pick.
> The physical build uses the **MG996R** (it's what the printed pinions
> and baseplate posts are sized for). If you use a different servo you
> must re-check the pinion bore and post spacing.

### 2.5 A frame to bolt it to

The baseplate is a compact mounting tab, not a free-standing table — it
bolts to a separate stand through its four corner M5 holes. Our test stand
is a simple wooden frame (~5 six-inch lengths of 2×4 lumber, a tabletop
board, and ~16 wood screws) tall enough that the balance and cup fit
underneath the dispense point.

*[PLACEHOLDER: dimensioned sketch or photo of the wooden test stand, with
the height from the tabletop to the dispense point and the M5 hole
positions marked out.]*

---

## 3. 3D printing the parts

### 3.1 Getting the files

All print files are in this repository (see the table in §2.2). STLs are
ready to slice; STEP files are alongside them if you want to modify
anything. The parts are parametric — the sources are OpenSCAD
(`cad/auger-geared/`) and CadQuery/KCL (`cad/mounting-plate-assembly/`) —
so dimensions can be regenerated rather than hand-edited.

### 3.2 Print settings

| Setting | Value |
|---|---|
| Material | PLA or PETG for structural parts (see gear note below) |
| Layer height | 0.2 mm |
| Infill | 25–30 % |
| Perimeters / walls | 3–4 |
| Nozzle | 0.4 mm |

**Gears (stepper pinion, servo pinions, and the gear bands that are part
of the auger and mounting plate):** the servo gear train carries the full
weight of the loaded mechanism and has stripped teeth in past builds when
printed in PLA with a non-rigid servo mount. For the separate pinion
parts we recommend a tough engineering filament — **PA6-CF** (or PAHT-CF /
PA6-GF) — printed with ~100 % infill and a hardened nozzle, with the gear
axis vertical so the layer lines run across the face of the teeth. PLA
works for a first prototype; expect to reprint pinions if you cycle the
tilt a lot under load.

### 3.3 Per-part notes

| Part | Orientation | Supports |
|---|---|---|
| Auger | Vertical, dispense end (funnel tip) down | *[PLACEHOLDER: confirm — the internal helix prints unsupported; note any support/brim needs from the next print]* |
| Stepper pinion | Gear axis vertical | None |
| Servo pinions | Gear axis vertical | None |
| Auger brackets | Flange face down | None |
| Tap collar | Face down | None |
| Tap-collar mount plate | Face down | None |
| Mounting plate | Flat face down | Tree supports under the hinge lobes / gear bands |
| Baseplate | Flat face down | *[PLACEHOLDER: confirm whether the servo posts / hinge arms need supports]* |

*[PLACEHOLDER: per-part print times and filament usage in grams — record
these during the next build for cost accounting (issue #114).]*

After printing, test-fit before assembly:

- The auger should rotate freely inside a bracket bore (the bore is Ø25.5
  for a 0.5 mm running clearance — the auger turns in the plain printed
  bore, there are no bearings in this design, and that is intentional).
- M3 holes are Ø3.4 clearance; M5 holes are Ø5.4 clearance. Clean out any
  stringing with a drill bit or a spare screw.
- Mesh the stepper pinion against the auger's gear band by hand; it
  should turn without binding.

---

## 4. Mechanical assembly

Orientation language used below: the auger lies horizontally along the
mounting plate. The **front** is the dispense end (funnel/exit hole,
which overhangs the front edge of the plate); the **rear** is the loading
end. "Left/right" are as seen looking at the front.

### Step 4.1 — Bolt the auger brackets to the mounting plate

The two identical brackets are split shaft collars on a flange: the auger
passes through the collar bore, and a clamp screw pinches the split to
grip it.

1. Place the **front bracket** over the pair of M3 holes nearest the
   mounting plate's front U-notch, flange down.
2. Bolt it down with M3 × 12 screws + nuts. Snug, not gorilla-tight —
   you're compressing printed plastic.
3. Repeat for the **rear bracket** on the rear pair of holes.
4. Leave both clamp screws loose for now.

The bracket flanges raise the auger axis to 29.25 mm above the plate —
this is what gives the auger's Ø50 gear band clearance over the plate
surface, so nothing else is needed underneath.

### Step 4.2 — Bolt down the tap-collar mount plate

The tap-collar mount plate is the small block with a half-cylinder cradle
on top. Bolt it to its four M3 holes, directly behind the front bracket
(there is only ~1 mm of designed clearance between the front bracket, the
tap collar, and the auger gear band — the parts are meant to sit nearly
flush against each other, packed toward the front).

### Step 4.3 — Mount the stepper and its pinion

1. The mounting plate has a vertical **motor wall** with a Ø22 pilot hole
   and a 4-hole M3 pattern (23 mm pitch). Hold the NEMA-11 body on the
   *rear* side of the wall so its shaft pokes through the pilot toward
   the front, and fasten it with 4 × M3 × 8 screws through the wall into
   the motor's face threads.
2. Slide the 16T stepper pinion onto the motor's 5 mm shaft, teeth facing
   so they will line up with the auger's gear band. Thread the M3
   setscrew into the pinion hub and leave it loose — you'll set the final
   axial position in step 4.4.

### Step 4.4 — Install the auger

1. Slide the auger, **dispense end first**, through the rear bracket, the
   tap-collar cradle position, and the front bracket, until the dispense
   tip overhangs the plate's front U-notch and the 48T gear band lines up
   with the stepper pinion.
2. Slide the **tap collar** onto the auger before it passes the mount
   plate (the collar rides on the auger between the gear band and the
   front bracket) and seat it in the mount-plate cradle. Snug its M3
   clamp screw just enough that the collar stays put. The mount plate has
   a hardstop bump that keeps the collar from rotating with the auger.
3. Center the stepper pinion on the gear band (slide it along the motor
   shaft) and tighten its setscrew.
4. Check gear mesh: rotate the pinion by hand (or the motor shaft) — the
   auger should turn smoothly through a full revolution with no tight
   spots. There is ~0.15 mm of designed backlash; a little play is
   correct.
5. Tighten both bracket clamp screws just enough to remove radial slop
   while the auger still spins freely. **The brackets locate the auger;
   they must not brake it.**

### Step 4.5 — Fit the solenoid and vibration motor to the tap collar

1. Screw the JF-0530B solenoid to the boss on the tap collar with 2 × M3
   self-tapping screws into the printed pilots. The plunger passes
   through the Ø7.5 bore and protrudes ~3 mm into the collar's inner
   bore — it strikes the auger tube through this hole. That interference
   is the "tap."
2. Stick the ERM coin motor into the Ø10 recess on the collar
   (adhesive-backed; add a drop of CA glue if it's loose).
3. Route both parts' wires back along the plate with a zip tie or tape so
   they can't wrap around the auger.

### Step 4.6 — Hinge the mounting plate to the baseplate

The hinge is a 3-layer sandwich on each side of the front U-notch: inner
mounting-plate lobe → baseplate arm → outer mounting-plate lobe, with one
long M5 pin through all three.

1. Offer the baseplate up to the front of the mounting plate so each
   baseplate **hinge arm** slots between its pair of mounting-plate
   lobes. The bores (Ø5.4) line up when all three layers are flush.
2. Push an M5 bolt (or printed hinge pin) through each side and secure
   with a lock nut — tight enough that it won't walk out, loose enough
   that the plate swings freely.
3. Swing the mounting plate through its travel by hand, 0° (flat) toward
   90° (auger pointing down past the baseplate's front edge). It must
   move without any part contacting another. The dispense tip should
   stay in essentially the same place as it tilts — that's the design
   working, not a coincidence.

### Step 4.7 — Mount the servos and their pinions

Each side of the baseplate has a **porch** with two square posts; the
MG996R bolts to the posts by its flange ears, body passing between the
posts, output spline toward the mounting-plate gear band.

1. Fit a 14T servo pinion onto each MG996R output spline (the bore is Ø6
   with a flat; it's a light push fit) and retain it with an M3 screw
   into the spline's center thread.
2. Bolt each servo to its posts through the four Ø5 flange holes. **A
   rigid, fully screwed-down servo mount is essential** — a past build
   that held a servo with tape stripped gear teeth within a day, because
   the gears could push apart and skip. Use all four screws.
3. Check that each pinion meshes with its mounting-plate gear band across
   the full tilt travel. With both servos unpowered you can still swing
   the plate slowly by hand and feel the gears track.

> Do **not** center the servos by twisting them by hand against their
> internal gearing. The firmware moves them to a soft home position on
> boot; if the plate ends up at a weird angle on first power-up, remove
> the pinion screws, let the firmware home the servos, and re-seat the
> pinions at the correct plate angle. *[PLACEHOLDER: document the exact
> mechanical zero — which plate angle corresponds to the firmware's
> default servo angle — after the first calibrated build.]*

### Step 4.8 — Bolt the baseplate to the frame

Bolt the baseplate tab to your stand through the four corner M5 holes.
The dispense point overhangs the front edge, so position the stand so a
cup on the balance sits directly under it, with nothing in the powder's
fall path at any tilt angle.

*[PLACEHOLDER: photo of the assembled mechanism on the stand with the
balance underneath.]*

---

## 5. Electronics

Everything wires point-to-point on a half-size breadboard. The schematic
(`hardware/test-module/kicad/test_module.png` — the KiCad project is in
the same folder) is the reference; the steps below are the build order.
The detailed rationale for each part lives in
`hardware/test-module/README.md`.

**Wire with all power disconnected. The three checks in step 5.9 are not
optional.**

### 5.0 Pin map (the contract between wiring and firmware)

| Net | Pico W GPIO (physical pin) | Goes to |
|---|---|---|
| I2C_SDA / I2C_SCL | GP0 / GP1 (pins 1, 2) | DRV2605L SDA / SCL |
| SERVO_SIG2 | GP2 (pin 4) | Servo M4 signal (second/mirrored servo) |
| STP_TX / STP_RX | GP4 / GP5 (pins 6, 7) | Tic T500 RX / TX (UART1, crossed) |
| SOL_IN1 / SOL_IN2 | GP10 / GP11 (pins 14, 15) | DRV8871 IN1 / IN2 |
| SCALE_TX / SCALE_RX | GP12 / GP13 (pins 16, 17) | RS-232 module TXD / RXD (UART0, straight) |
| HAPT_EN | GP14 (pin 19) | DRV2605L EN / IN_TRIG |
| SERVO_SIG | GP15 (pin 20) | Servo M3 signal |

### Step 5.1 — Configure the Tic T500 first, over USB

Before wiring anything: plug the Tic T500 into your computer with a
micro-USB cable and open Pololu's free **Tic Control Center**
(<https://www.pololu.com/docs/0J71>). Set:

- **Control mode:** "Serial / I²C / USB"
- **Current limit:** the motor's per-phase rating — **670 mA** for the
  11HS18-0674S (never above the Tic T500's 1500 mA limit). There is no
  potentiometer to adjust; this software setting is the current limit.
- **Command timeout:** 0 (disabled), so long moves aren't cut short.

Then connect the stepper's four leads to the Tic's A/B terminals and use
the Control Center's manual jog to confirm the motor spins **before** the
Tic ever touches the breadboard — this catches motor/wiring problems in
minutes. For the 11HS18-0674S: black + green = coil A, red + blue =
coil B (verify with a multimeter: the two leads of one coil show a few
ohms between them).

### Step 5.2 — Power rails

1. Connect the 12 V brick's barrel-jack pigtail leads to one pair of
   breadboard rails: `+12V` and `GND`. Add C1 (100 µF / 25 V) across
   them — stripe (negative) to GND.
2. Wire `+12V → buck VIN` and `GND → buck GND`. The buck's `VOUT` feeds
   a second pair of rails: `+5V` and `GND`. Add C2 (100 µF / 10 V)
   across the 5 V rail.

### Step 5.3 — Pico power

- `+5V → Pico VSYS` (pin 39), `GND → any Pico GND` (pins 3, 8, 13, …).
- Leave `VBUS` unconnected.
- The Pico's own `3V3` output (pin 36) becomes your `+3V3` rail — it
  powers the DRV2605L and the RS-232 module.

### Step 5.4 — Vibration (DRV2605L + ERM)

- `GP0 → SDA`, `GP1 → SCL`
- `DRV2605L VIN → +3V3`, `GND → GND`
- `GP14 → EN` (jumper EN to IN_TRIG on the breakout)
- `OUT+ → ERM red`, `OUT− → ERM black`

### Step 5.5 — Tap solenoid (DRV8871)

- `DRV8871 VM → +12V`, `GND → GND`
- `GP10 → IN1`, `GP11 → IN2`
- `OUT1 → solenoid lead 1`, `OUT2 → solenoid lead 2` (the solenoid coil
  is not polarized)

### Step 5.6 — Stepper (Tic T500 + shunt regulator)

- `Tic VIN → +12V`, `Tic GND → GND` (the GND next to VIN). Put C3
  (100 µF / 25 V) directly across VIN/GND at the Tic's terminals.
- Mount **SR1** (Pololu #3776 shunt regulator) in parallel with C3, `+`
  to `+12V`, `−` to `GND`, as close to the Tic's VIN as possible. It
  clamps the voltage spike the motor generates when it decelerates or is
  back-driven (e.g. by clogged powder). **It is polarized — reversed, it
  dies instantly.**
- UART, crossed over: `GP4 → Tic RX`, `GP5 ← Tic TX`.
- Stepper coils to the Tic's A/B terminals (already verified in 5.1).
- **Never connect or disconnect the stepper motor while 12 V is on** —
  hot-plugging a stepper destroys the driver.

### Step 5.7 — Servos

- Servo M3 (right side): `+5V`, `GND`, signal → `GP15`.
- Servo M4 (left side): `+5V`, `GND`, signal → `GP2`.
- Both servos follow a single angle command. Because they face opposite
  directions across the baseplate, the firmware drives M4 with the
  mirrored angle (`SERVO2_INVERT = True` in `config.py`). If you mount
  both servos facing the same way, set it to `False`.

### Step 5.8 — Scale RS-232 module (Waveshare Pico-2CH-RS232)

The balance's RS-232 port swings ±5–9 V. **Never wire it directly to a
Pico GPIO** (the RP2040's absolute maximum is 3.6 V — a direct connection
was analyzed and quantitatively rejected in
`hardware/test-module/analysis/rs232_analysis_results.md`). The Waveshare
module translates the levels:

- **Power the module from `+3V3`, not 5 V.** Jumper `+3V3` to *both* the
  module's VSYS pin position (physical pin 39 — this feeds the SP3232
  transceiver) *and* its 3V3 pin position (pin 36 — this feeds only the
  status LEDs, so a lit PWR LED alone doesn't prove the transceiver is
  powered). Module `GND → GND`.
- **TTL side, wired straight across** (the module's header is labeled
  from the Pico's point of view): `GP12 → module TXD`,
  `GP13 ← module RXD`. The module's native channel pins collide with
  the I²C and Tic UART assignments, so mount it on its own breadboard
  area and jumper the chosen channel's TXD/RXD over to GP12/GP13.
- Plug the DB9 cable into the **same channel's** RS-232 port that you
  jumpered on the TTL side (channel 0's port pairs with TXD0/RXD0). A
  channel-0-TTL / channel-1-DB9 mismatch is the classic *silent* failure.
- **Buzz out the DB9 harness with a multimeter before first use** — an
  idle RS-232 transmit line sits at about −5 to −9 V relative to ground,
  which is how you identify the scale's TX pin. Harnesses are not all
  wired alike.
- On the balance itself, check the communication settings match the
  firmware defaults: **2400 baud, 7 data bits, even parity, 1 stop bit,
  A&D standard format** (these are the HR-A factory defaults).

### Step 5.9 — Pre-power checks (do all three)

With the 12 V brick unplugged:

1. **No shorts:** multimeter continuity between `+12V`↔`GND` and
   `+5V`↔`GND` — both must be open.
2. **UART crossover:** `GP4 → Tic RX` and `GP5 → Tic TX` (TX-to-RX, not
   TX-to-TX). Scale side is the opposite convention: GP12/GP13 go
   *straight* to the module's TXD/RXD.
3. **SR1 polarity:** `+` on `+12V`, `−` on `GND`.

Do not plug in the 12 V brick yet — flash the software first (§6).

---

## 6. Software setup

The firmware is MicroPython, in `hardware/test-module/firmware/`. The
Pico runs everything; no code runs on your computer during normal
operation.

### Step 6.1 — Flash MicroPython onto the Pico

1. Download the latest **Pico W** MicroPython UF2 from
   <https://micropython.org/download/RPI_PICO_W/> (plain Pico:
   `RPI_PICO` image — the project firmware is identical for both).
2. Hold the Pico's `BOOTSEL` button while plugging in its USB cable. It
   mounts as a drive named `RPI-RP2`.
3. Drag the UF2 onto the drive. The Pico reboots into MicroPython.

### Step 6.2 — Install the upload toolchain

1. Install **VS Code**, then the **MicroPico** extension
   (`paulober.pico-w-go`).
2. Open `hardware/test-module/firmware/` as the workspace root folder.
3. From the Command Palette run **`MicroPico: Configure project`**.

### Step 6.3 — Upload the firmware

Run **`MicroPico: Upload project to Pico`**. This copies `main.py`,
`config.py`, `drv2605.py`, `tic.py`, `scale.py`, `dosing.py`, and
`tests/` onto the Pico's flash. Then press `Ctrl+D` in the MicroPico
terminal (soft reset) to start `main.py`.

> **Always upload the whole project, not just `main.py`.** The green
> "Run" button only streams `main.py` into RAM; `import config` etc.
> still load from flash. Symptoms of a stale flash copy include
> `AttributeError: ... 'SCALE_UART_ID'` at boot.

### Step 6.4 — Know your way around `config.py`

Every tunable lives in `hardware/test-module/firmware/config.py`: pin
assignments, stepper speed/acceleration/microstepping, dispense degrees
per shot, tap count/duration, vibration effect, servo range/speed/presets,
scale port settings, and the closed-loop dosing knobs. Edit → re-upload →
`Ctrl+D` is the whole iteration loop.

---

## 7. First power-on and channel tests

Order matters: **plug the Pico's USB in first** (so the firmware boots
with the actuator rails dead), *then* plug in the 12 V brick.

In the MicroPico terminal you should see the rig print its configuration
and `[rig] ready`. The firmware is a one-line-per-command serial REPL:

| Command | Effect |
|---|---|
| `h` | help |
| `s` | print state / config |
| `d` | dispense — rotate the auger one configured shot (`STEPPER_DISPENSE_DEG`, default 360°) |
| `r <deg>` | rotate the auger by a signed number of degrees |
| `v` | vibrate once |
| `t` | tap (a burst of `TAP_COUNT` solenoid pulses) |
| `a <deg>` | move the tilt servos to an angle (smoothly ramped) |
| `p <preset>` | move to a named tilt preset (`horizontal` / `tilt` / `vertical` / `tip`) |
| `w` | read the scale once |
| `z` | re-zero (tare) the scale |
| `g <grams>` | closed-loop dose to a target mass (§8) |
| `!` | emergency stop — de-energize everything |

Exercise one channel at a time, with the auger **empty**:

1. `a 0` then `a 180` — both servos sweep smoothly end-to-end and the
   plate tilts. If the plate binds anywhere, stop (`!`) and find the
   mechanical interference.
2. `t` — the solenoid clicks against the auger tube.
3. `v` — the collar buzzes.
4. `r 90` — the auger turns exactly a quarter turn. `r -90` brings it
   back.
5. `d` — one full dispense shot.

There are also standalone per-channel test scripts in
`hardware/test-module/firmware/tests/` if you want to isolate a
misbehaving channel.

Once every channel works dry, pour a test powder (we use fine table salt
or xanthan gum as safe surrogates) into the auger's top loading slots and
run `d` a few times over a cup — you should see repeatable little piles.
Roughly, the full auger holds ~67 mL and each revolution dispenses
~2.8 mL.

---

## 8. Scale integration and closed-loop dosing

With the balance connected (§5.8), place the cup on the balance under the
dispense point.

### Step 8.1 — Prove the link

Run the no-keypress diagnostic **before** trying any weigh commands:

```
hardware/test-module/firmware/tests/test_scale_contact.py
```

(Upload it with the project; run it from MicroPico.) It prints
`PASS` / `PARTIAL` / `FAIL` with a checklist. A silent link is almost
always a swapped TX/RX pair or the DB9 plugged into the wrong module
channel.

### Step 8.2 — Weigh and tare

- `w` — the balance replies with one weighing datum (prefixed `ST` when
  the reading is stable, `US` when still settling).
- `z` — tare.

### Step 8.3 — Closed-loop dose

`g 0.5` doses 0.5 g into the cup in two phases
(`firmware/dosing.py`):

1. **Coarse:** the auger advances in scale-checked increments while the
   firmware learns the powder's grams-per-revolution on the fly, stopping
   at ~90 % of target so powder still in flight can't overshoot.
2. **Fine:** the solenoid fires short tap bursts, waiting for a stable
   scale reading between bursts, until the target is reached within
   `DOSE_TOLERANCE_G`. If several bursts move nothing, the auger nudges
   a few degrees to re-feed the tube lip.

The dosing knobs (`DOSE_TOLERANCE_G`, `DOSE_COARSE_HEADROOM_G`,
`DOSE_TAPS_PER_BURST`, …) are in `config.py`. The controller is also
unit-tested against a simulated rig on your computer — no hardware
needed:

```sh
cd hardware/test-module/firmware
python3 sim/test_dosing_sim.py
```

*[PLACEHOLDER: measured dosing performance from the physical build —
typical time to dose 0.5 g, achieved repeatability vs `DOSE_TOLERANCE_G`,
and recommended per-powder starting values.]*

---

## 9. Calibration and tuning

All in `config.py` (edit → upload → `Ctrl+D`):

| What you observe | What to adjust |
|---|---|
| Powder surges / overshoots on coarse fill | Lower `STEPPER_SPEED_RPM` or `STEPPER_DISPENSE_DEG`; raise `DOSE_COARSE_HEADROOM_G` |
| Taps too weak / too strong | `TAP_PWM_DUTY`, `TAP_ON_MS`, `TAP_COUNT` |
| Powder bridges / stops flowing | Trigger `v` before dispensing; try a longer `VIBRATION_DURATION_S` or a different `VIBRATION_EFFECT_ID` (1–123, see Adafruit's DRV2605 guide) |
| Plate tilt too violent, powder jumps out | Lower `SERVO_SPEED_DEG_PER_S` (every servo move is ramped, never snapped) |
| Tilt angle presets don't match physical angles | Adjust `SERVO_PRESETS`; re-seat the servo pinions at the correct mechanical zero (§4.7) |
| Auger position drifts over a session | Expected in small amounts — the Tic tracks position open-loop and missed steps go undetected; exact auger angle is deliberately not treated as critical |

*[PLACEHOLDER: a filled-in example config for a reference powder (e.g.
fine NaCl), with measured grams-per-rev.]*

---

## 10. Troubleshooting

| Symptom | Likely cause → fix |
|---|---|
| Stepper does nothing; Tic LED red | Tic still in safe-start or wrong control mode → re-check §5.1 (Control mode = Serial/I²C/USB); the firmware sends `exit_safe_start` on boot, so also check the GP4/GP5 crossover. |
| Stepper stalls or misses steps under load | Current limit set too low, or powder jam → verify 670 mA in Tic Control Center; run `v` to un-stick the powder; lower `STEPPER_SPEED_RPM`. |
| Servo gears "click" and skip under load | Gear separation from a flexing mount → all four flange screws in each servo, posts undamaged; if teeth are visibly rounded, reprint the pinion (PA6-CF strongly recommended) — see the gear history note in §2.2. |
| Plate won't lift / servos strain | Check the mesh across the full travel; confirm both servos actually move on `a` commands (a dead M4 makes M3 fight the whole load). |
| `w` returns nothing (silent scale) | 90 % of the time: TX/RX swapped or the DB9 is in the other channel's port → run `test_scale_contact.py`, §8.1; also re-check the balance's baud/parity settings vs `config.py`. |
| Scale readings garbled | Baud/parity mismatch (default is 2400-7-E-1) or the module powered from 5 V instead of 3V3. |
| `AttributeError ... 'SCALE_UART_ID'` at boot | Stale `config.py` on the Pico flash → run **Upload project to Pico** (whole project), then `Ctrl+D`. |
| Pico resets when the solenoid fires | 5 V rail sagging → confirm C2 is installed; keep servo moves and taps from overlapping while testing. |
| ERM does nothing, `[vib] DRV2605L unavailable` at boot | I²C wiring (GP0/GP1 swapped) or the breakout unpowered → it's on `+3V3`, not 5 V. |
| Powder leaks from the loading slots when tilted | Expected with very free-flowing powders at steep angles — a sealing cap design exists as a prototype concept (`cad/` sealing-cap variants); *[PLACEHOLDER: finalize and document the sealing cap]*. |
| Anything scary | `!` — de-energizes every channel immediately. |

---

## Where to go next

- **Bill of materials with prices and vendor links:**
  [`BILL-OF-MATERIALS.md`](BILL-OF-MATERIALS.md)
- **Full electronics rationale and schematic:**
  `hardware/test-module/README.md` and `hardware/test-module/kicad/`
- **Firmware internals:** `hardware/test-module/firmware/README.md`
- **Design history** (why every part looks the way it does):
  `DESIGN-LOG.md` — the chronological Record of Designs
- **Scaling up:** the production concept is one Pico per channel
  reporting to a Raspberry Pi Zero 2 W host, and a 50-auger vertical
  carousel magazine — see `BILL-OF-MATERIALS.md` §5.

If you build one of these from this document, please open an issue with
everything that was confusing or wrong — these instructions are meant to
be tested against fresh eyes and improved.

# Powder-doser test-module electronics

Single-microcontroller bench rig for **one** powder-doser module — enough
to characterise dispensing angle, tapping, vibrating, and auger rotation
in isolation before scaling to the 30-channel production target tracked
in [#1](https://github.com/vertical-cloud-lab/powder-doser/issues/1).

Resolves **[#50](https://github.com/vertical-cloud-lab/powder-doser/issues/50)**.
Parts are the same ones identified in
**[#25](https://github.com/vertical-cloud-lab/powder-doser/pull/25)** but
the host MCU is consolidated from a Raspberry Pi Zero 2 W (production)
to a single **Raspberry Pi Pico W (RP2040 + CYW43439)** so the whole bench
rig can be exercised over USB-serial (and, in a future revision,
wirelessly) without bringing up a Linux stack.

## Contents

```
hardware/test-module/
├── README.md                  (this file)
├── analysis/
│   ├── rs232_analysis.py      # ngspice checks of the scale RS-232 interface
│   ├── rs232_analysis_results.md
│   └── *.log                  # raw ngspice output
├── kicad/
│   ├── generate.py            # regenerates the .kicad_* files + renders
│   ├── test_module.kicad_pro
│   ├── test_module.kicad_sch
│   ├── test_module.kicad_sym  # project-local breakout symbols
│   ├── sym-lib-table
│   ├── test_module.svg
│   ├── test_module.pdf
│   ├── test_module.png
│   └── test_module_review.png # exaggerated-stroke render for visual review
└── firmware/
    ├── README.md
    ├── main.py                # MicroPython main loop + driver classes
    ├── config.py              # easily adjustable parameters
    ├── drv2605.py             # in-tree MicroPython driver for the haptic chip
    ├── tic.py                 # in-tree MicroPython driver for the Tic T500
    ├── scale.py               # in-tree driver for the A&D HR-100A balance
    ├── dosing.py              # closed-loop dose controller (issue #99)
    ├── sim/                   # CPython simulation + unit tests for dosing
    └── tests/                 # per-component keyboard-driven bench scripts
```

## Schematic

![Schematic preview](kicad/test_module.png)

Open `kicad/test_module.kicad_pro` in KiCad 7.  The schematic is
authored as global-label-only connectivity — matching label names
(`+12V`, `GND`, `I2C_SDA`, `STP_TX`, etc.) are electrically connected
across the sheet.  No wires are routed, which keeps the layout
trivially regeneratable from `generate.py`.

## Bill of materials (subset of PR #25)

Only the parts needed to drive one channel from a single Pico are
listed here.  The Pi Zero 2 W, Perma-Proto Bonnet, baseplate-tilt
linear actuator, and second DRV8871 from the full BOM are intentionally
omitted — the Pico replaces the Pi and stands in for the bonnet by
hosting all the wiring on a half-size breadboard.

| Ref | Part | PR #25 item | Qty | Notes |
|---|---|---|---|---|
| U2  | Raspberry Pi Pico W (RP2040 + CYW43439, 2 × 20 castellated header) | — *(new for bench rig)* | 1 | Pico WH (pre-soldered) or plain Pico also work — only GP0..GP15 are used, which are pinned identically across the family. |
| U1  | Pololu D24V22F5 5 V / 2.5 A buck regulator | 15 | 1 | 12 V → 5 V for the Pico W + servo + solenoid. |
| U3  | Adafruit DRV2605L haptic driver breakout (#2305) | 1 | 1 | I²C, drives the ERM. |
| M1  | 10 mm ERM coin motor (Adafruit #1201) | 2 | 1 | Or any LRA on `VIBRATION_LIBRARY = 6`. |
| U4  | Adafruit DRV8871 motor driver breakout (#3190) | 5 | 1 | Drives the solenoid. |
| SOL1| JF-0530B 5 V push-pull solenoid (Adafruit #412) | 4 | 1 | The tap actuator. |
| U5  | Pololu Tic T500 USB stepper motor controller (#3134, MP6500) | 11 | 1 | Drives the auger over TTL serial from the Pico W; on-board motion planner + software-set current limit. |
| SR1 | Pololu #3776 33 V / 9 W shunt regulator | 18 | 1 | Across `+12V` / `GND` next to U5's `VIN` to clamp stepper back-EMF — see notes below. |
| M2  | NEMA-11 11HS18-0674S bipolar stepper | 10 | 1 | Direct-coupled to the auger. |
| M3, M4 | HD-1810MG metal-gear digital servo (#1142) | 16 | 2 | Dispensing-angle / wiper axis — **two** servos on opposite sides of the baseplate, moving in unison for steadier tilt control. |
| J1  | Mean Well GST60A12-P1J 12 V / 5 A barrel-jack PSU | 13 + 13a/13b | 1 | System power. |
| C1  | 100 µF / 25 V electrolytic, 12 V bulk | 14 | 1 | 12 V rail bulk decoupling. |
| C2  | 100 µF / 10 V electrolytic, 5 V bulk | 9 | 1 | Tames the servo + solenoid transients on the 5 V rail. |
| C3  | 100 µF / 25 V electrolytic, second bulk | 14 | 1 | Sits directly on the Tic T500's `VIN` screw terminals. |
| —   | Half-size breadboard, jumper wires, 0.1" headers | 9 | — | Bench wiring substrate (replaces item 6 bonnet for tests). |
| U6  | Waveshare Pico-2CH-RS232 module (SP3232EEN, 2-channel RS-232 transceiver) | — *(new, issue #99)* | 1 | Level-shifts the HR-100A's ±5..9 V RS-232 to Pico-safe logic and carries the DB9 to the scale. **Power it from `+3V3` (not 5 V)** — jumper `+3V3` to *both* its `VSYS` pin position (physical pin 39, which feeds the SP3232) *and* its `3V3` position (pin 36, which feeds only the status LEDs) — so the TTL `RXD` output stays within the RP2040's 3.6 V max.  Its TTL header is labelled from the Pico's point of view (`TXD`/`RXD`), so it wires straight across to the Pico. |
| —   | RS-232 cable (DB9 ↔ HR-100A RS-232C port; DIN-7/D-sub per scale option installed) | — *(new, issue #99)* | 1 | **Buzz out the pin order with a meter before first power-on** — harnesses are not all wired identically. |
| —   | A&D HR-100A analytical balance (102 g × 0.1 mg) | — *(lab equipment)* | 1 | The closed-loop mass feedback sensor; sits under the dispense cup. |

### Why the shunt regulator (SR1) is on the bench rig

PR #25 calls out the Pololu #3776 33 V / 9 W shunt regulator as item 18
for the production multi-channel system.  The single-channel bench rig
keeps it for three reasons:

1. **Back-EMF clamping.**  When the auger decelerates or is back-driven
   (e.g. clogged powder pushes the stepper backwards), the motor pumps
   energy back into the `VIN` rail.  With only the 100 µF bulk cap
   (C3) and a wall-wart that can't sink current, the rail voltage can
   transient well above 12 V — the Tic T500's maximum input is 35 V, so
   a hard stop on a fast move can push it past its limit.  The shunt
   regulator begins conducting at ~33 V and dumps the excess into its
   on-board power resistor, holding the rail safely below the Tic's
   35 V ceiling.
2. **Identical-to-production wiring.**  Keeping SR1 on the bench means
   step-rate / acceleration profiles found here transfer directly to
   the 30-channel system without re-tuning for a different transient
   envelope.
3. **Cheap insurance.**  At ~$7 it costs less than one Tic T500
   replacement.

It mounts as a single 2-pin part across `+12V` / `GND`, electrically
in parallel with C3, as close to U5's `VIN` screw terminals as the
breadboard allows.  See SR1 in the schematic.

### Why the Tic T500 is the stepper driver on the bench rig

PR #25 lists the **Pololu Tic T500 USB multi-interface stepper motor
controller** (item 11) as the option for driving the auger, and this
bench rig uses it directly.  The Tic T500 is an MP6500 stepper driver
plus an on-board microcontroller that exposes USB / I²C / TTL-serial /
RC / analog / encoder / step-and-direction inputs and runs its own
motion planner (acceleration ramps, current-position tracking, soft
limits, software-set current limit).  We picked it over a bare driver
carrier for the bench because:

1. **It is easy to bring up and tune.**  The free Tic Control Center
   configures the current limit (in mA, no `V_REF` pot maths), step
   mode, decay, and lets you jog the motor over USB before any
   microcontroller is involved — so a wiring or motor problem is caught
   in minutes.
2. **It matches the production plan from PR #25.**  Using the same Tic
   T500 here means the bench numbers (current limit, microstepping,
   accel) transfer unchanged to the multi-channel system instead of
   being re-derived for a different driver.
3. **The Pico W just sends targets.**  The Pico W drives the Tic over
   **UART1 (TTL serial)** — `Pico GP4 (TX) → Tic RX`,
   `Pico GP5 (RX) ← Tic TX` — using the Tic serial command set in
   [`firmware/tic.py`](firmware/tic.py).  The firmware sets step mode,
   max speed, and acceleration on boot and then issues
   "set target position" commands; the Tic handles the step generation
   and ramps.  This frees the six GPIOs a bare STEP/DIR/M0–2/nEN driver
   would have needed.

> **Why not the bare DRV8825 carrier (Pololu #2133)?**  An earlier
> revision of this rig drove a DRV8825 carrier straight from the Pico
> W's GPIOs to save a few dollars.  The team chose the Tic T500 instead
> because its USB configuration utility and on-board motion planner make
> it markedly easier to interface with and tune — the priority is to
> prove out one channel quickly, not to shave cost on a single bench
> rig.  The DRV8825-based **Tic T825** is a drop-in alternative if a
> higher microstep count (1/16, 1/32) or a higher (45 V) input ceiling
> is ever needed; only the BOM line and the Control-Center current
> limit would change, not the firmware (it talks the same serial
> protocol to every Tic).

Total ≈ **$70 + $19 (PSU) + $13 (stepper) + ~$10 (breadboard / jumpers)**
on top of whatever Pico W is on the bench.

## Pin / net table

These nets are the contract between
[`kicad/generate.py`](kicad/generate.py) and
[`firmware/config.py`](firmware/config.py); the firmware constants
`PIN_*` mirror the right-hand column.

| Net | DRV / actuator pin | Pico W pin | Notes |
|---|---|---|---|
| `+12V`       | J1.+ , U1.VIN , U4.VM , U5.VIN , SR1.+ , C1.+ , C3.+ | —     | 12 V from the wall brick; SR1 shunt regulator clamps back-EMF. |
| `+5V`        | U1.VOUT , U2.VSYS , M3.+5V , M4.+5V , C2.+    | —     | Buck output; powers Pico W + both servos. |
| `+3V3`       | U2.3V3 , U3.VIN , U6.VCC                       | —     | Pico W on-board LDO; powers the DRV2605L logic **and the Waveshare RS-232 module** (land it on the module's `VSYS` pin position — physical pin 39, the SP3232 supply — *and* its `3V3` position, pin 36, the LED supply; keep 5 V off both so the module's `RXD` output stays Pico-safe).  The Tic T500 needs no logic rail from the Pico — it generates its own logic supply from `VIN`. |
| `GND`        | (all, incl. SR1.- , U5.GND) | —     | Common ground. |
| `I2C_SDA`    | U3.SDA            | GP0   | I2C0 SDA to DRV2605L. |
| `I2C_SCL`    | U3.SCL            | GP1   | I2C0 SCL to DRV2605L. |
| `STP_TX`     | U5.RX             | GP4   | Pico UART1 TX → Tic T500 RX (commands to the Tic). |
| `STP_RX`     | U5.TX             | GP5   | Pico UART1 RX ← Tic T500 TX (telemetry / current position). |
| `SOL_IN1`    | U4.IN1            | GP10  | DRV8871 IN1 — PWM, drives the solenoid forward. |
| `SOL_IN2`    | U4.IN2            | GP11  | DRV8871 IN2 — held low. |
| `HAPT_EN`    | U3.EN , U3.IN_TRIG| GP14  | Hard-mute / wake for DRV2605L. |
| `SERVO_SIG`  | M3.SIG            | GP15  | 50 Hz PWM to servo 1 (dispensing-angle axis). |
| `SERVO_SIG2` | M4.SIG            | GP2   | 50 Hz PWM to servo 2 (opposite side); firmware mirrors servo 1 (`SERVO2_INVERT`). |
| `SCALE_TX`   | U6.TXD            | GP12  | Pico UART0 TX → module `TXD` input (commands to the scale).  Wire straight across — the Waveshare header is labelled from the Pico's point of view. |
| `SCALE_RX`   | U6.RXD            | GP13  | Pico UART0 RX ← module `RXD` output (weight frames from the scale). |
| `STP_A1/A2`  | U5.A1/A2 ↔ M2.A1/A2 | —   | Stepper coil A. |
| `STP_B1/B2`  | U5.B1/B2 ↔ M2.B1/B2 | —   | Stepper coil B. |
| `VIB_A/B`    | U3.OUT± ↔ M1.±    | —     | ERM coin motor leads. |
| `SOL_A/B`    | U4.OUT1/OUT2 ↔ SOL1.± | — | Solenoid coil. |
| —            | U5.ERR            | (n/c) | Optional — Tic error line; wire to a free GPIO for fault detection. |

## Assembly / wiring instructions

Build order, top to bottom:

1. **Configure the Tic T500 over USB** (U5) *before* installing it.
   Plug the Tic into your computer with a micro-USB cable and open the
   **Tic Control Center**.  Set *Control mode* to "Serial / I²C / USB",
   set the *current limit* to the motor's per-phase rating (≈ 0.67 A /
   `670 mA` for the 11HS18-0674S; never above the Tic T500's `1500 mA`
   continuous limit), choose the *step mode* (1/8 by default), and set
   the *Command timeout* to 0 (disabled) so a long move can't be cut
   short.  There is **no `V_REF` pot** — the current limit is a software
   setting enforced by the MP6500's on-chip current sensing.  Use the
   Control Center's manual jog to confirm the motor spins before wiring
   anything to the Pico.

2. **Power rails**. Plug the Mean Well 12 V brick (item 13) into the
   barrel-jack pigtail (item 13b) and land the two leads on the
   breadboard rails labelled `+12V` and `GND`.  Add C1 (100 µF/25 V)
   across them.  Wire `+12V → U1.VIN` and `GND → U1.GND_IN` on the
   D24V22F5 buck.  The buck's `VOUT` feeds the second pair of
   breadboard rails labelled `+5V` (and `GND`).  Add C2 (100 µF/10 V)
   across the `+5V` rail.

3. **MCU power.** Run `+5V → Pico W VSYS (pin 39)` and `GND → Pico W GND
   (any of pins 3/8/13/18/23/28/33/38)`.  Leave `VBUS` open.  Tap the
   Pico W's `3V3` (pin 36) for a `+3V3` rail.

4. **I²C (DRV2605L).** Wire:
   * `Pico W GP0 (pin 1) → U3 SDA`
   * `Pico W GP1 (pin 2) → U3 SCL`
   * `U3 VIN → +3V3`, `U3 GND → GND`
   * `Pico W GP14 (pin 19) → U3 EN` *(short to `U3 IN_TRIG` if you ever
     drive the breakout in external-trigger mode)*
   * `U3 OUT+ → ERM red lead`, `U3 OUT- → ERM black lead`.

5. **Solenoid (DRV8871).** Wire:
   * `U4 VM → +12V`, `U4 GND → GND`
   * `Pico W GP10 (pin 14) → U4 IN1`
   * `Pico W GP11 (pin 15) → U4 IN2`
   * `U4 OUT1 → solenoid +`, `U4 OUT2 → solenoid -`.

6. **Stepper (Tic T500 + shunt regulator).** Wire:
   * `U5 VIN → +12V`, `U5 GND → GND` (the `GND` next to `VIN` on the
     high-current side).  Add C3 (100 µF/25 V) directly across these two
     terminals; it tames the 12 V rail when the motor starts and stops.
   * **Mount SR1 (Pololu #3776 shunt regulator) in parallel with C3**,
     `+` to `+12V` and `-` to `GND`, as close to `VIN` as possible.
     Its on-board power resistor handles the back-EMF clamp described
     in the BOM section (the Tic T500's max input is 35 V).
   * `Pico W GP4 (pin 6) → U5 RX`, `Pico W GP5 (pin 7) → U5 TX`
     (UART1 cross-over: Pico TX → Tic RX, Pico RX ← Tic TX).  A common
     `GND` between the Pico and the Tic is already provided by the
     shared breadboard ground rail.  The Tic generates its own logic
     supply from `VIN`, so there is **no logic-rail or enable wire** to
     run from the Pico.
   * `U5 A1/A2 → stepper coil A`, `U5 B1/B2 → stepper coil B`.
     For the 11HS18-0674S: black/green = coil A, red/blue = coil B
     (verify with a multimeter — adjacent leads with low resistance
     belong to the same coil).  **Never connect or disconnect the
     stepper while `VIN` is powered** — doing so can destroy the Tic's
     driver.

7. **Dispense-angle servos (two, opposite sides).**
   * `M3 +5V → +5V`, `M3 GND → GND`, `Pico W GP15 (pin 20) → M3 SIG`.
   * `M4 +5V → +5V`, `M4 GND → GND`, `Pico W GP2 (pin 4) → M4 SIG`.
   * Both servos move in unison off a single angle command — there is no
     independent control.  Because they sit on opposite sides of the
     baseplate facing opposite ways, the firmware drives M4 with the
     mirror-image angle (`config.SERVO2_INVERT = True`) so they tilt the
     auger the same physical way.  Set `SERVO2_INVERT = False` if both
     servos are mounted facing the same direction.
   * The firmware ramps every angle command at `SERVO_SPEED_DEG_PER_S`
     deg/s so the servos never slam to the new setpoint.

8. **Scale (A&D HR-100A via the Waveshare Pico-2CH-RS232 module).**  The
   balance's RS-232C port swings **±5..9 V** — never wire it straight to a
   Pico GPIO (RP2040 absolute max is −0.3 / +3.6 V; see
   [`analysis/rs232_analysis_results.md`](analysis/rs232_analysis_results.md)
   for the ngspice numbers — those use a bare MAX3232, but the Waveshare
   board's SP3232EEN is the same RS-232 ↔ logic transceiver class).  All
   scale traffic goes through the module (U6):
   * **Power:** `+3V3 → U6 VSYS pin position` (physical pin 39 — per the
     [Waveshare schematic](https://files.waveshare.com/upload/3/38/Pico_2CH_RS232_SchDoc.pdf)
     this is what feeds the SP3232) **and** `+3V3 → U6 3V3 pin position`
     (pin 36 — this feeds only the PWR/TXD/RXD status LEDs, so a lit PWR
     LED alone does *not* prove the transceiver has power); `U6 GND → GND`.
     Use **+3V3, not 5 V** — the module's `RXD` output high level follows
     its supply, so 3.3 V keeps it inside the RP2040's 3.6 V max; the
     on-board charge pump still makes the ±RS-232 rails from 3.3 V.
   * **TTL side (to the Pico):** the Waveshare header is labelled from the
     **Pico's** point of view, so wire it *straight across* (no crossover
     here): `Pico W GP12 (pin 16) → U6 TXD`, `Pico W GP13 (pin 17) ← U6 RXD`
     (UART0).  Because the rig already uses the module's native channel
     pins (`TXD0`/`RXD0` → GP0/GP1 = I2C0, `TXD1`/`RXD1` → GP4/GP5 = the
     Tic's UART1), mount the module on its own breadboard and jumper the
     chosen channel out to GP12/GP13.  Count the module's pin positions
     from the end with the USB marking (position 1 = `GP0`/`TXD0`), and
     plug the scale into that **same channel's** RS-232 port — channel 0's
     port pairs with `TXD0`/`RXD0`; a ch-0 ↔ ch-1 mismatch is the classic
     silent link from ac-dev-lab#20.
   * **RS-232 side (to the scale):** run the DB9/RS-232 cable from the
     module to the balance's RS-232C port.  **Verify the harness pinout
     with a multimeter first** (idle RS-232 TXD sits at about −5..−9 V
     relative to GND — that's how you find the scale's TX pin); not all
     harnesses are wired alike.
   * On the balance, check the communication function settings match
     `config.py` (`SCALE_BAUD` etc.; the HR-A factory default is
     2400 baud, 7 data bits, even parity, 1 stop, A&D standard format).
   * **Before** trying `w`/`g`, confirm the link with the no-keypress
     [`firmware/tests/test_scale_contact.py`](firmware/tests/test_scale_contact.py)
     diagnostic — it prints `PASS`/`PARTIAL`/`FAIL` and a checklist.  A
     silent link is almost always a swapped TX/RX pair (the exact issue
     that stalled
     [ac-dev-lab#20](https://github.com/AccelerationConsortium/ac-dev-lab/issues/20)).

9. **Sanity check before powering.** With the brick **unplugged**:
   * Confirm no continuity between `+12V` and `GND`, or between `+5V`
     and `GND`.
   * Confirm the Tic T500 current limit / control mode are set (step 1).
   * Confirm the UART cross-over is right: `Pico GP4 → U5 RX` and
     `Pico GP5 → U5 TX` (TX-to-RX, not TX-to-TX).
   * Confirm the scale link: on the TTL side `Pico GP12 → U6 TXD` and
     `Pico GP13 ← U6 RXD` (straight across); the only crossover left is in
     the DB9 cable, where the scale's `TXD` must reach the module's RS-232
     receive pin.
   * Confirm SR1's `+` is on `+12V` and `-` is on `GND` (it is a
     polarised part and reversing it kills the regulator instantly).

10. **First power-on.** Plug the Pico W into USB *first* (so the firmware
    starts with the rails de-energised), then plug in the 12 V brick.
    Open the USB-serial port — you should see the rig print its state
    and a `[rig] ready` line.  Run `s` to dump the configuration, then
    exercise one channel at a time:
    * `a 0` then `a 180` — both servos sweep end-to-end (M4 mirrored when
      `SERVO2_INVERT = True`).
    * `t` — solenoid clicks `TAP_COUNT` times.
    * `v` — ERM buzzes for `VIBRATION_DURATION_S` seconds.
    * `r 90` — auger rotates 90 °.
    * `w` — scale replies with one weighing datum (`ST …` when stable).
    * `z` — re-zero (tare) the balance.
    * `g 0.5` — **closed-loop dose**: auger to ~90 % of 0.5 g, then
      solenoid taps until the scale reads 0.5 g ± `DOSE_TOLERANCE_G`.

## Closed-loop dosing (issue #99)

`g <grams>` runs the two-phase controller in
[`firmware/dosing.py`](firmware/dosing.py):

1. **Coarse** — the auger advances in scale-checked increments while the
   firmware *learns* the powder's grams-per-revolution online, stopping
   at ~90 % of the target (capped to `DOSE_COARSE_HEADROOM_G` on big
   doses) so trailing powder can't overshoot.
2. **Fine** — the tap solenoid fires `DOSE_TAPS_PER_BURST`-tap bursts,
   waiting for a stable (`ST`) reading between bursts, until the target
   mass is reached within `DOSE_TOLERANCE_G`.  If a few bursts move
   nothing, the auger nudges a few degrees to re-feed the tube lip.

All knobs live in `config.py` under "Closed-loop dosing".  The control
loop is hardware-agnostic and is unit-tested under CPython against a
simulated rig — see [`firmware/sim/`](firmware/sim/):

```sh
cd hardware/test-module/firmware
python3 sim/test_dosing_sim.py     # or: python3 -m pytest sim/ -q
```


## Reproducing the schematic files

The KiCad project + symbol library are emitted by
[`kicad/generate.py`](kicad/generate.py).  Re-run it after editing the
script (or after changing `PLACEMENTS` to add / move a component):

```sh
sudo apt-get install -y kicad kicad-symbols librsvg2-bin   # one-time
cd hardware/test-module/kicad
python3 generate.py                                        # rewrites files
```

The script will:

1. Regenerate `test_module.kicad_sym`, `test_module.kicad_sch`,
   `test_module.kicad_pro`, and `sym-lib-table`.
2. Call `kicad-cli sch export svg ...` and `... pdf ...` to refresh
   the rendered previews.
3. Rasterise the SVG to `test_module.png` via `rsvg-convert` if it's
   on `PATH`.

The headless export is the same path KiCad-CI uses, so the artefacts
match what you would get from opening the project in KiCad GUI and
hitting *File → Export → Schematic*.

## Why a Pico W instead of the Pi Zero 2 W from PR #25?

The production system in #25 needs Linux for I²C device trees, USB
control of the Tic T500, networking, and the eventual 30-channel
multiplexer.  The bench rig has none of those requirements — it just
needs to drive a handful of GPIO pins (and one UART to the Tic)
reliably with adjustable timing.  Folding the controller into a $6
microcontroller:

* eliminates the Pi Zero 2 W + microSD + USB power brick + bonnet
  (≈ $38 of system-shared cost in #25);
* leans on the Tic T500's own safe-start / command-timeout watchdog so
  the auger stays put until the firmware explicitly energises it and
  sends a target — no boot-time enable-line gotcha to engineer around;
* keeps the test loop "edit `config.py`, click MicroPico's *Run current
  file on Pico*, see new behaviour" — much faster iteration than
  redeploying a `systemd` service on the Pi;
* leaves the CYW43439 radio available for a future "trigger a dispense
  from the lab laptop over Wi-Fi" mode without a hardware change.

When the system grows past one channel the wiring is identical — just
move the same nets onto the production Pi Zero 2 W + Perma-Proto
Bonnet from #25 and re-use the same DRV2605L / DRV8871 / Tic T500 /
shunt regulator / servo parts.

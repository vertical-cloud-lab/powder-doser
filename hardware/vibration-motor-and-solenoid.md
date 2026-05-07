# Auger drive, vibration motor, and solenoid — parts identification

Resolves [#24](https://github.com/vertical-cloud-lab/powder-doser/issues/24).
Companion to the Archimedes auger CAD in [`cad/auger/`](../cad/auger/) (PR
[#16](https://github.com/vertical-cloud-lab/powder-doser/pull/16); housing
≈ 20 mm OD × 100 mm tall).

## Goals (from #24)

* Small enough to mount on / next to the 20 mm OD auger housing.
* A **drive motor** to **rotate the auger** itself (this is what
  actually meters the powder); preferably **direct-coupled to the
  auger shaft**, with belt drive as a fallback.
* A **vibration motor** to free bridged powder, mounted on the
  **stationary auger housing or hopper wall** (not on the rotating
  auger itself — wires can't follow a rotating shaft without a
  slip ring, which we want to avoid). Ideally with **variable
  frequency and amplitude**.
* A **solenoid** mounted **externally** (e.g. as a tap that strikes the
  housing) to dislodge stuck powder.
* All driven from a **Raspberry Pi Zero 2 W** (3.3 V GPIO, limited drive
  current), so a small **driver / breakout board** is needed for each
  actuator.

## Rotating vs stationary parts (no slip ring needed)

To make the wire-routing constraints explicit:

* **Stationary** (mounted to the frame / housing): the Pi Zero 2 W,
  the Perma-Proto Bonnet, all three driver breakouts (DRV2605L,
  DRV8871, DRV8825), the power supply / supplies, the vibration
  motor (epoxied to the housing or hopper wall), the solenoid (on
  a printed bracket beside the housing), and the **stepper motor
  body** (bolted to a bracket co-axial with the auger).
* **Rotating**: only the **auger shaft itself**. The shaft is
  driven by the stepper through a **flexible shaft coupler**
  (item 12) which sits *outside* the powder-side housing.
* **Wires never cross a rotating boundary.** All four motor leads
  on the stepper, the two leads on the vibration motor, and the
  two leads on the solenoid land on stationary boards, so no slip
  ring is needed. The flex coupler is the only mechanical link
  between the rotating and stationary domains.

## TL;DR — recommended bill of materials

| # | Part | Qty | Approx. price (USD) | Source / link |
|---|------|-----|---------------------|---------------|
| 1 | Adafruit DRV2605L Haptic Motor Controller breakout (I²C) | 1 | $7.95 | [adafruit.com/product/2305](https://www.adafruit.com/product/2305) |
| 2 | Vibrating Mini Motor Disc — ERM coin, 10 mm × 2.7 mm, 3 V | 1 | $1.95 | [adafruit.com/product/1201](https://www.adafruit.com/product/1201) |
| 3 | Linear Resonant Actuator (LRA) — 10 mm × 3.4 mm, ~175 Hz (alternative to #2) | 1 | $4.95 | [adafruit.com/product/1631](https://www.adafruit.com/product/1631) |
| 4 | JF-0530B 5 V mini push–pull solenoid (~9.6 × 19 × 22 mm, ~4.5 mm stroke) | 1 | $4.95 | [adafruit.com/product/412](https://www.adafruit.com/product/412) |
| 5 | Adafruit DRV8871 DC Motor Driver Breakout — 3.6 A peak, built-in flyback clamps + current limit, screw terminals, takes PWM logic in directly | 1 | $7.50 | [adafruit.com/product/3190](https://www.adafruit.com/product/3190) |
| 6 | Adafruit Perma-Proto Bonnet Mini Kit for Pi — Pi-HAT-shaped solder substrate that the two breakouts and the Pi Zero 2 W's 2×20 header mate to | 1 | $4.95 | [adafruit.com/product/2310](https://www.adafruit.com/product/2310) |
| 7 | 5 V / ≥2 A external supply *(only needed if you do **not** use the consolidated single-supply variant — see "Power supply" below; if you use the buck converter (item 15) you can omit this and item 8)* | 0–1 | — | any 5 V barrel-jack PSU |
| 8 | 2.1 mm barrel-jack breakout for the 5 V supply input on the Bonnet (omit when using the consolidated single-supply variant) | 0–1 | $0.95 | [adafruit.com/product/373](https://www.adafruit.com/product/373) |
| 9 | 0.1" headers, jumper wires, 100 µF / 10 V bulk cap (across the DRV8871 motor supply) | — | — | any |
| 10 | NEMA 11 bipolar stepper motor — 28 mm faceplate, 5 mm shaft, ~0.67 A/phase, ~12 N·cm holding (e.g. SparkFun ROB-10848 or StepperOnline 11HS18-0674S) | 1 | $14–18 | [sparkfun.com/products/10848](https://www.sparkfun.com/products/10848) |
| 11 | Pololu DRV8825 stepper-driver carrier — pre-soldered carrier PCB, on-board current limit pot, 1/32 microstepping, accepts 3.3 V STEP/DIR/EN logic from the Pi | 1 | $7.95 | [pololu.com/product/2133](https://www.pololu.com/product/2133) |
| 12 | 5 mm ↔ 5 mm flexible shaft coupler (or 5 mm ↔ auger shaft diameter) for direct-drive to the auger | 1 | $3–6 | any (Amazon / McMaster) |
| 13 | **12 V / ≥3 A external supply** — sized to power the stepper *and* (via item 15) the 5 V rail in the consolidated single-supply variant | 1 | ~$10 | any 12 V/3 A barrel-jack wall-wart, e.g. [adafruit.com/product/352](https://www.adafruit.com/product/352) (12 V/5 A) |
| 14 | 100 µF / 25 V electrolytic across the DRV8825's `VMOT` / `GND` (Pololu specifically calls this out as required) | 1 | <$0.50 | any |
| 15 | **Pololu D24V22F5** 5 V / 2.5 A step-down (buck) regulator — 12 V → 5 V, lets a single 12 V supply power the Pi *and* the DRV8871 solenoid rail, eliminating the second wall-wart and item 8 | 1 | $14.95 | [pololu.com/product/2858](https://www.pololu.com/product/2858) |

Total for the full actuator stack (items 1, 2, 4, 5, 6, 10, 11, 12): **≈ $60**.
With the **consolidated single-supply variant** (add item 15, drop
items 7 and 8): **≈ $75** but with **only one wall plug** instead
of two.

Everything in this list is a **pre-packaged board with screw terminals
or 0.1" headers** — no transistor / diode / gate-resistor sizing
needed. You solder the two breakouts and the Pi's 2×20 header onto
the Perma-Proto Bonnet, screw the motor and solenoid leads into the
DRV2605L and DRV8871 terminals respectively, and you're done.

## Power supply

The actuators want two distinct rails:

* **12 V / ≥1 A** for the stepper, into the DRV8825's `VMOT`.
* **5 V / ≥1.5 A** for the solenoid coil (peak ~1.1 A inrush)
  *and* the Pi Zero 2 W (~0.7 A under WiFi load), with a common
  ground tied to the stepper supply's GND.

There are two wiring options; **the single-supply variant is
recommended** because it eliminates one wall-wart and one
barrel-jack breakout:

### Recommended: single 12 V supply + on-board buck (item 13 + item 15)

* Use a single **12 V / 3 A barrel-jack wall-wart** (item 13,
  e.g. [Adafruit #352](https://www.adafruit.com/product/352)
  rated 12 V / 5 A so it stays cool at our ~1 A continuous draw).
* Solder a **Pololu D24V22F5** 12 V → 5 V / 2.5 A step-down
  (item 15, [Pololu #2858](https://www.pololu.com/product/2858))
  onto the bonnet next to the DRV8825. It's a pre-built carrier
  with `VIN`, `GND`, and `VOUT` pads on a 0.1" pitch — no
  inductor or feedback-divider sizing needed.
* Wire `VIN/GND` of the buck to the same 12 V net that feeds the
  DRV8825's `VMOT`. Wire `VOUT` to the DRV8871's `VM` and to the
  Pi Zero 2 W's 5 V rail (header pin 2 or 4) on the bonnet. All
  GNDs are already common via the bonnet's ground rail.
* Item 7 (separate 5 V PSU) and item 8 (second barrel-jack
  breakout) become unnecessary — the wall-plug count drops from
  **two to one**.
* Why the D24V22F5 specifically: it's the cheapest Pololu buck
  carrier that comfortably handles the Pi's startup transient
  plus the JF-0530B's ~1.1 A inrush in the same 5 V rail (2.5 A
  continuous, ~3 A peak). The D24V10F5 (1 A continuous) is too
  small once the solenoid is firing while the Pi is busy on WiFi.

### Alternative: two separate wall-warts (items 7, 8, 13)

Keep this option if you already have a 5 V supply on the bench
and don't want to buy a buck converter. In that case wire the
5 V PSU through item 8 to the DRV8871's `VM` (and to a Pi USB
power input), and the 12 V PSU through a screw-terminal pad to
the DRV8825's `VMOT`. Tie all grounds together at the bonnet.
This is also the configuration drawn in the KiCad schematic
([`kicad/`](kicad/)).

## Auger drive motor

### Recommended: NEMA 11 bipolar stepper, direct-coupled to the auger shaft (items 10, 11, 12)

Powder dosing is fundamentally an **angle-counting** problem — one
revolution of the auger displaces a known volume of powder, so a
**stepper** (open-loop position control by counting steps) is the
natural fit. A NEMA 11 bipolar stepper is the smallest standard
frame size and lines up well with the 20 mm OD housing footprint:

* **28 mm × 28 mm faceplate**, ~30–45 mm body length, 5 mm output
  shaft.
* ~0.67 A/phase, ~12 N·cm holding torque — comfortably above what
  a small Archimedes auger metering loose powder needs.
* 200 full steps/rev (1.8°), down to 6400 microsteps/rev with the
  DRV8825 at 1/32 microstepping → sub-degree dose resolution.
* Direct-drive — the auger shaft from `cad/auger/` is sized for a
  5 mm coupler bore, so the stepper output shaft mates to it
  through a **flexible shaft coupler** (item 12). No belt, no
  pulleys, no alignment tooling.

### Driver: Pololu DRV8825 stepper-driver carrier (item 11)

Same "pre-packaged board, just solder pin headers in" pattern as
the rest of this BOM. The DRV8825 carrier provides:

* Two integrated H-bridges with built-in flyback handling (no
  external diodes).
* On-board **current-limit potentiometer** — set once with a
  multimeter (or by reading `Vref`) to ~0.67 A/phase to match the
  motor; no current-sense resistor sizing needed.
* 1/1, 1/2, 1/4, 1/8, 1/16, 1/32 microstepping selected by three
  mode pins (tie to 3.3 V or GND through the Bonnet).
* 3.3 V-tolerant `STEP` / `DIR` / `~ENABLE` logic inputs that the
  Pi's GPIOs drive directly.
* Screw-terminal-friendly 0.1" pin rows for both the motor coils
  (`A1/A2/B1/B2`) and motor supply (`VMOT/GND`).

Wire-up:

* `VMOT` / `GND` ← **12 V external PSU** (item 13), with the
  100 µF / 25 V cap (item 14) right at those pins. *Do not* power
  the DRV8825 from the 5 V rail or the solenoid PSU — the stepper
  needs the higher voltage to commutate quickly.
* `A1, A2` ← stepper coil A; `B1, B2` ← stepper coil B (check
  motor datasheet for pairs).
* `STEP` ← Pi **GPIO20**, `DIR` ← Pi **GPIO21**, `~ENABLE` ← Pi
  **GPIO16** (active-low; pull high to coast the motor between
  doses to save power and heat).
* `RESET` and `SLEEP` tied together and pulled high (otherwise the
  driver stays asleep).
* Common GND between the 12 V PSU, the DRV8825 logic GND, and the
  Pi.

### Belt-drive alternative

If mechanical layout forces the motor off-axis (e.g. to clear the
hopper or fit a smaller envelope around the housing), substitute
the flexible coupler (item 12) for a small **GT2 timing-belt
pulley pair + closed-loop belt** (e.g. 16T pulleys, 110–158 mm
belt). 1:1 ratio keeps the dose calibration identical to direct
drive; a 2:1 reduction (16T → 32T on the auger) doubles torque
and halves max RPM if needed. **Direct-drive is preferred per the
issue review** — the specific reasons for that preference haven't
been spelled out yet, so this section captures both options and
defers the final choice to the reviewer.

### Why not a brushed DC gearmotor (e.g. N20) with an encoder?

Workable, but it adds an encoder + closed-loop control just to
recover the absolute-position guarantee a stepper gives you for
free. For a metered-dose application the stepper is simpler,
cheaper at this scale, and the DRV8825 carrier keeps the wiring
just as "solder-on" as the DRV8871.



### Why not just a bare ERM on a GPIO + transistor?

A bare **Eccentric Rotating Mass** (ERM) coin motor coupled to a MOSFET
driven by Pi PWM lets you change the **drive duty cycle**, but in an ERM
**rotation speed and eccentric force are coupled** — you can't pick a
frequency and amplitude independently, and the response is non-linear
near startup. That makes "vary frequency and amplitude" from the issue
hard to deliver well with the simplest possible circuit.

### Recommended: ERM (or LRA) + DRV2605L haptic driver

The TI **DRV2605L** is a tiny I²C haptic driver designed exactly for
small ERMs and LRAs. It gives us the closest match to the issue's
"vary frequency and amplitude" goal with a single $8 breakout:

* **Amplitude control** — open-loop or closed-loop drive from
  silent up to full scale, set per-effect or via real-time playback
  (PWM / analog / I²C).
* **Frequency control** —
  * For an **LRA** (item 3), the chip auto-tracks the actuator's
    resonance and you can sweep ±a few Hz around it, plus build
    arbitrary on/off pulse trains at any rate up to several hundred Hz
    via the real-time playback / waveform-sequencer registers.
  * For an **ERM** (item 2), absolute spin frequency is still tied to
    duty, but the chip's 123-effect ROM and waveform sequencer let
    you pulse / chirp / ramp the motor to produce a wide range of
    perceived buzz frequencies and intensities — far more tunable
    than raw PWM.
* **No high-side switching, no flyback diode, no current-sense
  resistor** to design — all on-chip.

Pick **one** vibrating actuator:

* **Item 2 (ERM coin, 10 mm × 2.7 mm)** — cheapest, smallest,
  glue-on; good default. Spin frequency ~150–200 Hz at 3 V.
* **Item 3 (LRA, 10 mm × 3.4 mm)** — same footprint, slightly
  taller, but gives true independent amplitude control at a
  well-defined resonant frequency (~175 Hz). Recommended if we
  actually want to characterize the powder response vs. drive
  parameters in the paper.

Both fit comfortably on the flat outer wall of the 20 mm auger
housing or on the hopper (e.g. epoxied or held by a printed clip
on the housing exterior). They must **not** be attached to the
rotating auger itself — the leads can't follow a spinning shaft
without a slip ring, and a slip ring is exactly what we want to
avoid.

### Wiring (Pi Zero 2 W ↔ DRV2605L ↔ motor)

```
   Pi Zero 2 W              DRV2605L breakout         Vibration motor
   ────────────              ─────────────────         ───────────────
   3V3   (pin 1)  ────────►  VIN                       (motor +) ─┐
   GND   (pin 6)  ────────►  GND                                  ├─ to OUT+/OUT-
   SDA1  (pin 3)  ◄────────  SDA                       (motor −) ─┘
   SCL1  (pin 5)  ◄────────  SCL
                              IN  ── (optional ext. PWM, leave open for I²C mode)
```

Default I²C address: `0x5A`. Software:
[`adafruit-circuitpython-drv2605`](https://docs.circuitpython.org/projects/drv2605/en/latest/)
runs on the Pi Zero 2 W via Blinka; `i2cdetect -y 1` should show the
chip after enabling I²C with `raspi-config`.

## Solenoid (external tap)

### Recommended: JF-0530B 5 V push–pull solenoid (item 4)

* Body **~9.6 × 19 × 22 mm**, 4.5 mm stroke, 5 V coil (~1.1 A
  inrush, ~150 mA hold during a short pulse).
* "Push–pull" = built-in return spring; energising drives the
  plunger, releasing returns it. Perfect for short tap pulses
  against the auger housing.
* Mounts **externally** (per the issue) on a small printed bracket
  alongside the auger; the plunger taps the housing wall at a
  configurable position.

### Driver: Adafruit DRV8871 DC motor driver breakout (item 5)

The Pi Zero 2 W's 3.3 V GPIO can sink/source only ~16 mA per pin and
must never drive an inductive load directly. Rather than designing a
discrete MOSFET + flyback + gate-resistor circuit, we use the
**Adafruit DRV8871** breakout — a pre-packaged board built around
TI's DRV8871 H-bridge that already includes:

* Internal high- and low-side flyback clamps (no external diode
  needed).
* Adjustable internal current limiting (set by a single resistor on
  the board — Adafruit ships it pre-populated for ~2.7 A peak,
  comfortably above the JF-0530B's ~1.1 A inrush).
* Two logic inputs (`IN1`, `IN2`) that accept the Pi's 3.3 V GPIO
  directly and can be PWM'd.
* Screw terminals for both the motor supply (`VM`, 6.5 – 48 V — for
  our 5 V coil we'll feed 5 V here) and the load (`OUT1`, `OUT2`
  → solenoid coil).

Functionally the DRV8871 is a full H-bridge; for a single-coil
solenoid we only use one of its two output legs. Tying `IN2` low and
PWM'ing `IN1` from the Pi gives standard "low-side switching with
flyback handled internally" behaviour at any tap rate we care about
(5–20 Hz, 20–80 ms pulses).

* Use **GPIO18** (hardware PWM) on the Pi for `IN1` so pulse width is
  jitter-free; control with `pigpio` / `gpiozero`'s
  `PWMOutputDevice`. Tie `IN2` to Pi GND.
* Feed the DRV8871's `VM` / `GND` from the **separate 5 V supply**
  (item 7) via the barrel-jack breakout (item 8) so coil current
  doesn't sag the Pi's 5 V rail. Add the 100 µF bulk cap (item 9)
  across `VM` / `GND` to absorb the inrush.
* Tie the 5 V supply ground to Pi ground — single common GND.

### Why not a relay HAT?

A mechanical-relay Pi HAT (e.g. Waveshare RPi Relay Board) is
similarly "just solder and go", but its 10–20 ms switching latency
and finite contact life make it a poor fit for pulsed taps; the
DRV8871 is silent, has no moving parts, and supports any PWM rate.

## Electrical schematic

The full electrical schematic is a real KiCad 7 project under
[`kicad/`](kicad/). Open it with `kicad
hardware/kicad/powder_doser_actuators.kicad_pro`, or browse the
rendered exports:

* [`kicad/powder_doser_actuators.pdf`](kicad/powder_doser_actuators.pdf) — printable PDF.
* [`kicad/powder_doser_actuators.svg`](kicad/powder_doser_actuators.svg) — vector SVG.
* PNG render embedded below.

![KiCad schematic of the powder-doser actuator stack](kicad/powder_doser_actuators.png)

Connectivity is expressed by **matching global net labels** (KiCad
treats identically-named labels as the same net) rather than drawn
wires; see [`kicad/README.md`](kicad/README.md) for the symbol
inventory, the labels-vs-wires rationale, and — importantly — the
explicit list of **placeholder symbols** (the four breakout boards,
for which no first-party Adafruit / Pololu KiCad library currently
exists) and **assumed connections** that need a human to confirm
before fabrication.

## Build order

1. Solder the Pi Zero 2 W's 2×20 header onto the **Perma-Proto
   Bonnet** (item 6) and seat the Pi on it.
2. Solder the **DRV2605L** breakout (item 1) onto the Bonnet's
   prototyping area; jumper its `VIN/GND/SDA/SCL` pads to the
   matching Pi pads broken out by the Bonnet. Wire `OUT+`/`OUT-`
   to the ERM/LRA leads.
3. Solder the **DRV8871** breakout (item 5) onto the Bonnet; jumper
   `IN1` to the Pi's GPIO18 pad, `IN2` to GND. Wire `OUT1`/`OUT2`
   to the solenoid coil leads (polarity doesn't matter for a single
   coil).
4. Solder the **DRV8825 carrier** (item 11) onto the Bonnet using
   its included 0.1" pin headers. Jumper `STEP`→GPIO20, `DIR`→GPIO21,
   `~ENABLE`→GPIO16; tie `RESET` and `SLEEP` together to `3V3`.
   Pick a microstep mode by tying `M0/M1/M2` to `3V3` or `GND`
   (start with all-low = full step, switch to all-high = 1/32 once
   calibration is dialed in). Wire `A1/A2` and `B1/B2` to the
   stepper coils.
5. **Power-supply wiring — pick one of the two variants in the
   "Power supply" section above:**
   * **Recommended (single-supply):** solder the **Pololu D24V22F5
     buck converter** (item 15) onto the Bonnet next to the
     DRV8825. Bring the **12 V PSU** (item 13) in on a
     screw-terminal pad pair; jumper `+` to both the DRV8825's
     `VMOT`, the buck's `VIN`, and the 100 µF / 25 V cap's `+`,
     and `−` to the DRV8825's `GND`, the buck's `GND`, the cap's
     `−`, and a Pi GND pad. Jumper the buck's `VOUT` to the
     DRV8871's `VM`, the 100 µF / 10 V cap's `+`, and the Pi's
     5 V rail (header pin 2 or 4 on the bonnet); jumper the
     buck's `GND` side of `VOUT` to the DRV8871's `GND` and the
     cap's `−`. Items 7 and 8 are not used in this variant.
   * **Alternative (two PSUs):** solder the **barrel-jack
     breakout** (item 8) onto the Bonnet for the 5 V supply
     (item 7); jumper its `+` to the DRV8871's `VM` and the
     100 µF / 10 V cap's `+`, and `−` to the DRV8871's `GND`,
     the cap's `−`, and a Pi GND pad. Then bring the **12 V PSU**
     (item 13) in on a second screw-terminal pad pair; jumper
     `+` to the DRV8825's `VMOT` and the 100 µF / 25 V cap's
     `+`, and `−` to the DRV8825's `GND`, the cap's `−`, and
     the same Pi GND pad.

   **In either variant, set the DRV8825 current-limit pot to
   ~Vref = 0.42 V (≈0.67 A/phase) before powering the motor for
   the first time** — this is the only "tuning" step in the
   build.
6. Couple the stepper output shaft to the auger shaft with the
   flexible coupler (item 12). The coupler is the *only*
   mechanical link between the rotating auger shaft and the
   stationary stepper body — no wires cross this boundary.

That's the entire assembly — no transistor, diode, or resistor
sizing.

## Software stub

A minimal Python sketch on the Pi (for reference; not part of this
PR's scope):

```python
import time
import board, busio
import adafruit_drv2605
from gpiozero import PWMOutputDevice, DigitalOutputDevice

# --- vibration motor (DRV2605L over I²C) ---
i2c = busio.I2C(board.SCL, board.SDA)
drv = adafruit_drv2605.DRV2605(i2c)
drv.sequence[0] = adafruit_drv2605.Effect(47)   # "buzz 1, 100%"
drv.play(); time.sleep(0.5); drv.stop()

# --- solenoid tap (DRV8871, IN1 on GPIO18, IN2 tied low) ---
tap = PWMOutputDevice(18, frequency=10)  # 10 Hz tap train
tap.value = 0.3                          # 30% duty → ~30 ms ON / 70 ms OFF
time.sleep(1.0)
tap.off()

# --- auger drive (NEMA 11 + DRV8825: STEP/DIR/~EN on GPIO20/21/16) ---
step  = DigitalOutputDevice(20)
dir_  = DigitalOutputDevice(21)
en_n  = DigitalOutputDevice(16, active_high=False, initial_value=False)  # enabled
dir_.on()                              # forward
STEPS_PER_REV = 200                    # full-step mode; ×microstep factor otherwise
for _ in range(STEPS_PER_REV):         # one revolution of the auger
    step.on();  time.sleep(0.001)
    step.off(); time.sleep(0.001)
en_n.off()                             # coast/disable to save power & heat
```

## Notes / open questions

* If we end up wanting **independent control of both spin frequency
  and amplitude** on the vibration side (rather than the
  ERM-with-tricks approach above), the next step up is a small
  brushed DC motor (e.g. an N20 6 mm coreless) with a custom
  3D-printed eccentric mass, driven by a DRV8833 H-bridge. That's
  bulkier than item 2/3 and is only worth doing if the
  ERM/LRA + DRV2605L combo is not expressive enough.
* Final mounting locations (vibration motor on the housing wall vs.
  on the hopper; solenoid tap point; stepper bracket and coupler
  alignment) should be revisited once the auger housing CAD from
  #16 is finalised.
* Auger shaft bore in `cad/auger/` should be confirmed at 5 mm to
  match the NEMA 11 output shaft (item 10) and the flexible coupler
  (item 12); if it's a different diameter, swap to a 5 mm ↔ Xmm
  coupler rather than re-picking the motor.

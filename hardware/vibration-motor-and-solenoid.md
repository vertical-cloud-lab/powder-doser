# Vibration motor and solenoid — parts identification

Resolves [#24](https://github.com/vertical-cloud-lab/powder-doser/issues/24).
Companion to the Archimedes auger CAD in [`cad/auger/`](../cad/auger/) (PR
[#16](https://github.com/vertical-cloud-lab/powder-doser/pull/16); housing
≈ 20 mm OD × 100 mm tall).

## Goals (from #24)

* Small enough to mount on / next to the 20 mm OD auger housing.
* A **vibration motor** to free bridged powder in the hopper / on the
  auger flights, ideally with **variable frequency and amplitude**.
* A **solenoid** mounted **externally** (e.g. as a tap that strikes the
  housing) to dislodge stuck powder.
* All driven from a **Raspberry Pi Zero 2 W** (3.3 V GPIO, limited drive
  current), so a small **driver / breakout board** is needed for each
  actuator.

## TL;DR — recommended bill of materials

| # | Part | Qty | Approx. price (USD) | Source / link |
|---|------|-----|---------------------|---------------|
| 1 | Adafruit DRV2605L Haptic Motor Controller breakout (I²C) | 1 | $7.95 | [adafruit.com/product/2305](https://www.adafruit.com/product/2305) |
| 2 | Vibrating Mini Motor Disc — ERM coin, 10 mm × 2.7 mm, 3 V | 1 | $1.95 | [adafruit.com/product/1201](https://www.adafruit.com/product/1201) |
| 3 | Linear Resonant Actuator (LRA) — 10 mm × 3.4 mm, ~175 Hz (alternative to #2) | 1 | $4.95 | [adafruit.com/product/1631](https://www.adafruit.com/product/1631) |
| 4 | JF-0530B 5 V mini push–pull solenoid (~9.6 × 19 × 22 mm, ~4.5 mm stroke) | 1 | $4.95 | [adafruit.com/product/412](https://www.adafruit.com/product/412) |
| 5 | Adafruit DRV8871 DC Motor Driver Breakout — 3.6 A peak, built-in flyback clamps + current limit, screw terminals, takes PWM logic in directly | 1 | $7.50 | [adafruit.com/product/3190](https://www.adafruit.com/product/3190) |
| 6 | Adafruit Perma-Proto Bonnet Mini Kit for Pi — Pi-HAT-shaped solder substrate that the two breakouts and the Pi Zero 2 W's 2×20 header mate to | 1 | $4.95 | [adafruit.com/product/2310](https://www.adafruit.com/product/2310) |
| 7 | 5 V / ≥1 A external supply (separate from the Pi 5 V rail) | 1 | — | any USB-C or barrel-jack PSU |
| 8 | 2.1 mm barrel-jack breakout (or screw-terminal pigtail) for the 5 V supply input on the Bonnet | 1 | $0.95 | [adafruit.com/product/373](https://www.adafruit.com/product/373) |
| 9 | 0.1" headers, jumper wires, 100 µF / 10 V bulk cap (across the DRV8871 motor supply) | — | — | any |

Total for the actuator stack (items 1, 2, 4, 5, 6): **≈ $26**.

Everything in this list is a **pre-packaged board with screw terminals
or 0.1" headers** — no transistor / diode / gate-resistor sizing
needed. You solder the two breakouts and the Pi's 2×20 header onto
the Perma-Proto Bonnet, screw the motor and solenoid leads into the
DRV2605L and DRV8871 terminals respectively, and you're done.

## Vibration motor

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
housing (e.g. epoxied or held by a printed clip on the housing
exterior).

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

## High-level system block diagram

This is the level you actually need to assemble: each box is a
pre-made board, and the arrows are wires (jumper or screw-terminal)
between named pads on those boards.

```
                ┌──────────────────────────────────────────────┐
                │  Raspberry Pi Zero 2 W  (mounted on Bonnet)  │
                │                                              │
                │   3V3  GND   SDA   SCL              GPIO18   │
                └────┬────┬────┬─────┬───────────────────┬─────┘
                     │    │    │     │                   │
                     │    │    │     │                   │  PWM
                     ▼    ▼    ▼     ▼                   ▼
   ┌──────────────────────────────────┐    ┌──────────────────────────────┐
   │  Adafruit DRV2605L breakout      │    │  Adafruit DRV8871 breakout   │
   │  (haptic motor controller, I²C)  │    │  (H-bridge, screw terminals) │
   │                                  │    │                              │
   │  VIN GND SDA SCL    OUT+  OUT-   │    │  IN1  IN2  VM  GND  OUT1 OUT2│
   └─────────────────────┬──────┬─────┘    └──┬────┬───┬────┬─────┬────┬──┘
                         │      │             │    │   │    │     │    │
                         │      │             PWM  GND │    │     │    │
                         ▼      ▼                      │    │     ▼    ▼
                  ┌──────────────────┐                 │    │   ┌────────────┐
                  │  ERM coin (#2)   │                 │    │   │ Solenoid   │
                  │   or LRA (#3)    │                 │    │   │  JF-0530B  │
                  │  on auger wall   │                 │    │   │  (#4)      │
                  └──────────────────┘                 │    │   └────────────┘
                                                       │    │
                                              ┌────────┴────┴────────┐
                                              │  5 V external PSU    │
                                              │  via barrel-jack     │
                                              │  breakout (#7, #8)   │
                                              │  GND tied to Pi GND  │
                                              └──────────────────────┘
```

Build order:

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
4. Solder the **barrel-jack breakout** (item 8) onto the Bonnet;
   jumper its `+` to the DRV8871's `VM` and the 100 µF cap's `+`,
   and `−` to the DRV8871's `GND`, the cap's `−`, and a Pi GND
   pad. Plug in the 5 V PSU.

That's the entire assembly — no transistor, diode, or resistor
sizing.

## Software stub

A minimal Python sketch on the Pi (for reference; not part of this
PR's scope):

```python
import time
import board, busio
import adafruit_drv2605
from gpiozero import PWMOutputDevice

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
  on the hopper; solenoid tap point) should be revisited once the
  auger housing CAD from #16 is finalised.

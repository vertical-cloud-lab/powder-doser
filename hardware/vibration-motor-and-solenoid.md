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
| 5 | Logic-level N-channel MOSFET breakout — e.g. SparkFun MOSFET Power Control Kit (IRLB8721) | 1 | $9.95 | [sparkfun.com/products/12959](https://www.sparkfun.com/products/12959) |
| 6 | SS14 Schottky flyback diode (preferred) or 1N4007 — across the solenoid coil | 1 | <$0.10 | any |
| 7 | 5 V / ≥1 A external supply (separate from the Pi 5 V rail) | 1 | — | any USB-C or barrel-jack PSU |
| 8 | Dupont jumpers, screw terminal, 0.1 µF + 100 µF decoupling caps | — | — | any |

Total for the actuator stack (items 1, 2, 4, 5, 6): **≈ $25**.

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

### Driver: logic-level N-MOSFET + flyback diode (items 5, 6)

The Pi Zero 2 W's 3.3 V GPIO can sink/source only ~16 mA per pin and
must never drive an inductive load directly. A logic-level
N-channel MOSFET (e.g. **IRLB8721** on the SparkFun breakout) is
enough to switch the JF-0530B at PWM rates suitable for tapping
(typically 5–20 Hz, 20–80 ms pulses).

```
                 +5 V (separate supply, common GND with Pi)
                  │
                  ├──[ solenoid coil ]──┬─────► MOSFET drain (switching node)
                  │                     │
                  │        SS14         │     ← flyback diode reverse-biased in
                  └────────|◄───────────┘       normal operation: cathode to +5 V,
                                                anode to MOSFET drain. It only
                                                conducts on coil turn-off, clamping
                                                the inductive kick to ≈ +5 V + Vf.

   Pi GPIO18 ──[ 220 Ω ]── G ── MOSFET ── D ── (joins drain node above)
   Pi GND ───────────────── S ─────────────── GND  (tied to Pi GND)
                            │
                          (10 kΩ from G to S, pulldown so the FET is
                           off while the Pi boots)
```

A Schottky like the **SS14** (40 V / 1 A, Vf ≈ 0.5 V, very fast
recovery) is preferred over a 1N4007 here: the lower forward drop
clamps the inductive kick closer to the rail, and the faster
reverse-recovery dissipates the stored energy more quickly, which
matters when we pulse the solenoid many times per second. A 1N4007
will work for slow / single taps but is a slow rectifier.

* Use **GPIO18** (hardware PWM) on the Pi so pulse width is
  jitter-free; control with `pigpio` / `gpiozero`'s
  `PWMOutputDevice`.
* Keep the **5 V solenoid supply separate** from the Pi's 5 V rail
  (or at least add a fat bulk cap, e.g. 1000 µF, on the solenoid
  side) to avoid brown-outs on the Pi when the coil energises.
* Tie the solenoid PSU ground to Pi ground — single common GND.

### Why not a relay?

A mechanical relay would work, but its 10–20 ms switching latency
and limited cycle life make it a poor fit for pulsed taps; a MOSFET
is smaller, silent, and lasts effectively forever.

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

# --- solenoid tap (MOSFET on GPIO18) ---
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

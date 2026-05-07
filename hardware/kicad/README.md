# KiCad project — powder-doser actuator stack

This directory contains the electrical schematic for the actuators
documented in [`../vibration-motor-and-solenoid.md`](../vibration-motor-and-solenoid.md):

* `powder_doser_actuators.kicad_pro` — KiCad 7 project file.
* `powder_doser_actuators.kicad_sch` — schematic.
* `powder_doser.kicad_sym` — local symbol library containing the four
  custom block symbols used for boards with no first-party KiCad
  symbol available (see "Placeholder symbols" below).
* `sym-lib-table` — points the project at `powder_doser.kicad_sym`.
* `powder_doser_actuators.svg`, `.png`, `.pdf` — rendered exports
  produced by `kicad-cli sch export {svg,pdf} …` and
  `rsvg-convert`. The PNG is the one embedded in
  [`../vibration-motor-and-solenoid.md`](../vibration-motor-and-solenoid.md).

Open the project with `kicad powder_doser_actuators.kicad_pro` (KiCad 7
or newer).

## How connectivity is expressed

The schematic uses **global net labels** rather than drawn wires.
KiCad treats two pins with identical net-label strings as
electrically connected, regardless of where they are on the sheet.
This keeps the layout legible while still producing an ERC-clean
schematic that can drive a netlist export. Power nets (`+3V3`,
`+5V`, `+12V`, `GND`) and signal nets (`I2C_SDA`, `I2C_SCL`,
`PI_GPIO16`, `PI_GPIO18`, `PI_GPIO20`, `PI_GPIO21`, `ERM_PLUS`,
`ERM_MINUS`, `SOL_A`, `SOL_B`, `STEP_A1/A2/B1/B2`) all use this
convention.

## Symbols used

### From the stock KiCad-7 libraries (`/usr/share/kicad/symbols/`)

| Symbol                          | Used for                                |
|---------------------------------|-----------------------------------------|
| `Connector:Barrel_Jack`         | 5 V and 12 V external supply inputs (J2, J3) |
| `Device:C_Polarized`            | 100 µF / 10 V (C1) and 100 µF / 25 V (C2) bulk caps |
| `Device:L`                      | JF-0530B solenoid coil (L1) — represented as a plain inductor since the coil's external behaviour is just inductance |
| `Motor:Motor_DC`                | ERM coin / LRA vibration motor (M1)     |
| `Motor:Stepper_Motor_bipolar`   | NEMA 11 bipolar stepper (M2)            |
| `power:+3V3`, `+5V`, `+12V`, `GND` | Power-net flags (referenced via labels) |

### Custom block symbols (in `powder_doser.kicad_sym`)

These are simple labelled rectangles with the board's actual
pinout, used **as placeholders** because no first-party
Adafruit / Pololu KiCad library exists at the time of writing:

| Symbol                                          | Refers to                                   |
|-------------------------------------------------|---------------------------------------------|
| `powder_doser:Adafruit_DRV2605L`                | Adafruit DRV2605L haptic-driver breakout — [Adafruit #2305](https://www.adafruit.com/product/2305) |
| `powder_doser:Adafruit_DRV8871`                 | Adafruit DRV8871 H-bridge breakout — [Adafruit #3190](https://www.adafruit.com/product/3190) |
| `powder_doser:Pololu_DRV8825_Carrier`           | Pololu DRV8825 stepper-driver carrier — [Pololu #2133](https://www.pololu.com/product/2133) |
| `powder_doser:Adafruit_PermaProto_Bonnet_Pi_Header` | Pi 2×20 GPIO header on the Adafruit Perma-Proto Bonnet Mini — [Adafruit #2310](https://www.adafruit.com/product/2310). Only the pins this project actually uses are exposed on the symbol; the other ~30 GPIOs on the bonnet are passed through unchanged. |

If the BYU PSC has any of these boards already in a vetted local
KiCad library, swap the `powder_doser:*` `lib_id` references in
`powder_doser_actuators.kicad_sch` for the real ones — the net
names will still match.

## Components / connections that need a human to confirm

Per the review feedback ("Don't assume connections you don't know,
instead make note of them and tell me so I can put them in this
repository and clarify where needed"):

1. **Stepper coil pairings.** The schematic ties net labels
   `STEP_A1`/`STEP_A2`/`STEP_B1`/`STEP_B2` to both the DRV8825's
   coil-output pins and the bipolar-stepper symbol's four pins, but
   the *physical* wire colour ↔ coil mapping varies by NEMA-11 SKU
   and must be read from the chosen motor's datasheet (or
   identified with a multimeter on the resistance check) before
   wiring.
2. **Solenoid coil polarity.** The JF-0530B is driven by the
   DRV8871 in single-direction PWM "tap" mode (IN2 tied to GND);
   coil polarity is irrelevant in that mode. If a future revision
   wants bidirectional drive (e.g. active push *and* return), this
   needs to be re-evaluated.
3. **NEMA-11 mounting bracket.** The schematic captures only the
   electrical interface; the mechanical bracket that holds the
   stepper coaxial with the auger shaft is in `cad/`, not here.
4. **Common ground.** The schematic shows the 5 V supply, 12 V
   supply, and Pi all sharing `GND`, but on the Perma-Proto Bonnet
   that is a single physical net only if the two barrel-jack `−`
   terminals are explicitly tied to a Pi `GND` pad — call this out
   in the build instructions.
5. **Footprints / PCB layout.** This project ships a schematic
   only; no `.kicad_pcb` is included because the actuator stack
   sits on a hand-soldered Perma-Proto Bonnet rather than a
   custom-fab PCB.

## Regenerating the schematic and the PNG/PDF/SVG exports

The schematic is produced by a small Python generator that lives
under `/tmp/kicad_build/` during a build session (it embeds stock
KiCad symbol definitions into the schematic so the project is
self-contained). To regenerate the rendered exports from the
checked-in `.kicad_sch`:

```bash
sudo apt-get install -y kicad librsvg2-bin
cd hardware/kicad
kicad-cli sch export svg powder_doser_actuators.kicad_sch -o ./
kicad-cli sch export pdf powder_doser_actuators.kicad_sch -o powder_doser_actuators.pdf
rsvg-convert -o powder_doser_actuators.png powder_doser_actuators.svg
```

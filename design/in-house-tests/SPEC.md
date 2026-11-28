# Systems spec: the ten in-house test apparatuses

**Status: design, 2026-11-28.** Nothing here has been built. This file is the single source of numbers
for the CAD (`cad/`), the bill of materials (`bom/`), the simulations (`sim/`), the firmware and bench
software (`firmware/`, `software/`), the PCB (`pcb/`) and the videos (`video/`). Change a number here
first, then regenerate.

Units: mm, g, s, Pa, unless stated. "Printed" = PLA (Bambu PLA Basic), A1 mini, 0.4 mm nozzle, 0.20 mm
layers, unless stated.

## 0. What every apparatus shares

### 0.1 The doser and the balance, as the fixtures see them

| Item | Value | Source |
|---|---|---|
| Auger tube | Ø25 OD, Ø21 bore, 250 long, outlet face at z = 0 | [`auger-dimensions.png`](auger-dimensions.png) |
| Auger outlet | Ø3 hole, Ø0.8 core tip, 6.6 mm² annulus | same |
| Drive | 44T m1 spur on the tube (z = 78.33–88.33), 20T m1 pinion on a NEMA 11, 32.00 mm centres, 2.2:1 | same |
| Auger speed | 1–109 rpm (motor 240 rpm max) | same |
| Tilt | servos with 2:1 pinions; firmware presets 0 / 45 / 90 / 135° | `config.py` (`d14a50d`) |
| Doser controller | Pico W: GP0/1 I2C0 (DRV2605L 0x5A), GP2 + GP15 tilt servos, GP4/5 Tic T500 UART1, GP10/11 tap solenoid (DRV8871), GP12/13 balance RS-232 (UART0), GP14 haptic EN | same |
| Doser computer | Raspberry Pi Zero 2 W (512 MB, one CSI port, one USB port, which the Pico uses); runs the livestream | checked read-only 2026-11-28 |
| Balance | A&D HR-100A, 102 g × 0.1 mg, pan Ø90 with its top 86.5 above the bench, round breeze break Ø156 inside from z = 86 to 284.5, top door Ø76, 198 × 294 × 315 overall | PR #185 / #204 (`doserlib.hr100a`, A&D manual) |

### 0.2 New shared hardware (bought once, used by several tests)

| Item | Used by | Why |
|---|---|---|
| **Bench computer:** Raspberry Pi 5, 4 GB, 27 W USB-C PSU, active cooler, 32 GB card | all | The doser's Pi Zero 2 W has one camera port, one USB port and 512 MB. The bench Pi runs cameras, image analysis and the SOP scripts, and talks to the doser through `doser_bridge.py` on the Zero, so the production setup is not rewired |
| **Silhouette camera:** Raspberry Pi Camera Module 3 (standard, 75° → use at 100–150 mm) + Pi 5 camera cable | 1, 2, 3, 5, 7, 9 | 4608 × 2592 px; at 120 mm working distance ≈ 35 µm/px |
| **Microscope camera:** Raspberry Pi HQ camera (C/CS mount) + C-mount 0.12–1.8× zoom macro lens + Pi 5 camera cable | 4 | 1.55 µm pixels → 0.9–13 µm/px |
| **Backlight:** USB LED tracing pad, A5, dimmable | 1, 2, 3, 5, 7 | Silhouettes |
| **Accessory controller:** Raspberry Pi Pico 2 W on the bench Pi's USB | 3, 5, 6, 8, 9, 10 | Runs the new servos, stepper, sensors; firmware `firmware/accessory_main.py` |
| **Accessory stepper driver:** Pololu Tic T500 (#3135) on the accessory Pico's UART | 2, 8, 9 | One driver; one motor connected at a time |
| **I2C (STEMMA QT / Qwiic) chain** on the accessory Pico: SHT45 (0x44), LSM6DSOX IMU (0x6A), NAU7802 24-bit load-cell ADC (0x2A); the charge amplifier's ADS1115 (0x48) | 3, 6, 8, 10 | No address clashes |
| **Ambient sensor:** SHT45 on the bench, logged with every test | all | RH and T on every record |
| **In-chamber tripod** (printed): three legs standing on the HR-100A's chamber floor at r = 62 mm (clear of the Ø90 pan by 17 mm), top ring at an adjustable height (leg sets 40 / 80 / 120 / 160 mm) | 1, 5, 10 | Holds things over the pan without touching it |
| **Pan adapter** (printed): Ø86 × 3 plate with a central M6 socket, centred on the pan by a 3-point rim | 1, 2, 5 | Holds risers and vessels on the pan |
| **Riser set** (printed): Ø20 tubes 40 / 80 / 120 / 160 mm, M6 printed thread at both ends | 1 | Put the heap base 12 mm below the doser outlet |

Accessory Pico pins (Pico 2 W): GP0/1 I2C0 (STEMMA QT chain), GP4/5 UART1 → Tic T500 (TX/RX),
GP6 servo A (orifice gate), GP7 servo B (tilt table), GP8/9 DRV8871 #2 (orifice-cup tapper solenoid),
GP10 charge-amp reset (reed relay driver), GP11 limit switch (linear stage home), GP12 backlight
MOSFET (PWM), GP26/ADC0 spare analog.

### 0.3 The universal linear stage (tests 8 and 9)

One bought 100 mm-stroke lead-screw linear stage with a NEMA 17 (T8 lead screw, 8 mm lead, two Ø8
guide rods, a 40–60 mm slider), driven by the accessory Tic T500 (max 1.5 A per phase; set 1.0 A).
- Mounted **vertically** on the UCS frame (test 8): platen speed 0.05–0.2 mm/s (6–24 motor steps/s at 1/8
  microstep = 0.005 mm per microstep).
- Mounted **horizontally** on the spreading base (test 9): blade speed 10–100 mm/s.
- A limit switch (homing) on GP11.

## 1. Heap angle of repose (tier 1)

- **Pedestal tops** (printed, swappable): Ø12, Ø20 (default), Ø30. 45° chamfer underneath to a 0.4 mm
  land, top face with 0.3 mm deep, 1 mm pitch cross-hatch (roughness; powder glued on top for the
  test). M6 printed stud underneath.
- **Riser** from the set, on the pan adapter. Pedestal top 12 mm below the doser outlet at the
  chosen tilt (45° default).
- **Overflow tray** on the in-chamber tripod: Ø120 × 8 mm dish, Ø14 × 10 mm chimney in the middle,
  Ø10 hole, sitting 20 mm below the pedestal top. The riser passes through the chimney with 2 mm
  clearance, so the balance weighs pedestal + heap only.
- **Camera:** silhouette camera outside the breeze break, level with the pedestal, 120 mm from the
  axis; backlight on the far side.
- **Mass on pan:** pan adapter 12 g + riser ≤ 15 g + pedestal 2 g + heap ≤ 5 g ≈ 34 g (< 102 g).
- **Fallback** (if the tripod can't stand in the chamber): the same pedestal on a 100 g load cell
  (test 8's) on the bench.
- **SOP:** tilt 45°; `r 360` steps; photo + balance after each; stop when the heap mass grows < 2 % per
  rev for 3 revs; 3 pours per jar.
- **Outputs:** flank angles (left/right line fits between 15 % and 85 % of the height), ISO apex angle
  atan(2h/D), heap mass, heap volume (silhouette of revolution) → heap density, avalanche sizes from
  mass drops.

## 2. Bulk and tapped density (tier 1)

- **Vessel:** 10 mL Class A graduated cylinder (borosilicate, ±0.1 mL, ≈ 13 mm ID). The bore is
  calibrated by weighing water to height (camera) before first use.
- **Fill:** the cylinder in a printed **fill holder** (base Ø40, holds the cylinder's hex foot) on the
  pan adapter, with a printed **funnel collar** (cone 60°, Ø25 top → Ø8 throat, sits on the rim) to
  centre the stream. Fill by doser at 45°, 30 rpm to 6 g (or 8 mL, whichever first).
- **Tap:** a **cam-drop tapper** (printed frame) to USP <616> method 2 / ASTM B527 geometry: drop
  3.0 ± 0.2 mm, 250 taps/min. A two-lobe snail cam (printed, 3.0 mm rise) on a NEMA 11 (Tic T500, 125
  rpm) lifts a **cylinder carriage** (printed, rides on two Ø6 × 100 steel rods in four printed bushings
  with PTFE tape) and drops it on a 304 stainless anvil disc (Ø25 × 3). Carriage + cylinder + powder ≈
  70 g. Optical end stop (TCRT5000) counts cam turns.
- **Camera:** silhouette camera at 120 mm with backlight; column height to ±0.05 mm.
- **Batches:** 0 (poured), 1, 2, 5, 10, 20, 50, 100, 200, 500, 1250 taps.
- **Outputs:** ρ_bulk, ρ_tap(N), Hausner, Carr, Kawakita a and 1/b.

## 3. Tilting plate: wall friction (A) and layer start angle (B) (tier 1)

- **Tilt table** (stand-alone, printed): hinge on an Ø5 steel pin, plate turned by a 20 kg·cm metal-gear
  servo through a printed 1:2 spur pair (servo 0–180° → table 0–90°); accessory servo B. IMU (LSM6DSOX)
  on the plate gives the true angle. Tilt rate 0.5°/s near the expected angle.
- **Plate:** printed 120 × 60 × 6 with a 100 × 50 pocket (depth = coupon thickness − 0.2) for coupons:
  PLA (printed with the auger's settings), 304 stainless 100 × 50 × 1, glass 75 × 50 × 1 slide (in a
  shim), and a powder-roughened PLA coupon (mode B). A stop rail at the low end catches sliding rings.
- **Mode A ring:** printed, Ø25 ID × 6 tall, 1.2 wall; three 0.5 mm removable shim tabs; lids
  0 / 5 / 15 g (printed + steel washers). σ_n ≈ 70–450 Pa.
- **Mode B frames:** printed strike-off frames 60 × 40 with 1, 2, 3, 5 mm depth.
- **Detection:** camera side view (slip = ring moves > 0.5 mm) and an IMU / accelerometer jolt.
- **Outputs:** φ_w (wall friction angle) vs σ_n on each coupon (μ_w = tan φ_w; intercept = wall adhesion),
  layer start angle vs thickness.

## 4. PSD and shape from images (tier 1)

- **Microscope stand** (printed): HQ camera + zoom lens on a printed rack-and-pinion focus carriage
  (M3 lead screw, 0.5 mm/turn), over a printed slide holder with a 40 × 30 mm window; diffuse LED below
  (backlight pad, masked).
- **Stage:** manual microscope mechanical stage (X–Y, verniers) bolted to the stand.
- **Calibration:** stage micrometer slide (0.01 mm divisions).
- **Dispersal:** printed vibrating sieve cup (Ø30, stainless wire-cloth disc, 100 or 200 mesh) on the
  doser's ERM, or wet dispersion in IPA for cohesive powders.
- **Field:** at 1× zoom ≈ 1.55 µm/px, 7.1 × 5.4 mm field; ≥ 2000 grains over ≥ 10 fields.
- **Outputs:** number- and volume-weighted d10/d50/d90 of the area-equivalent diameter, span, aspect
  ratio, circularity, solidity.

## 5. Orifice cup (tier 2)

- **Cup** (printed): Ø25 bore × 40 tall, flat bottom with a Ø20 × 2 recess for orifice discs; holds
  ≈ 19.6 mL.
- **Orifice discs** (printed 2 mm thick, holes drilled/reamed to size): 1.0, 1.5, 2.0, 2.54, 3.0, 4.0,
  5.08, 6.0 mm; 45° relief underneath; 2.54 and 5.08 match the Hall and Carney funnels.
- **Gate:** printed slide (1.5 mm thick) under the disc, moved 10 mm by a 9 g metal-gear micro servo
  (accessory servo A).
- **Tapper:** a second JF-0530B solenoid on the cup holder, on DRV8871 #2.
- **Mount:** cup holder on the in-chamber tripod, outlet 40 mm above a catch beaker on the pan
  adapter.
- **SOP:** fill to 5 g with the gate shut; open; log mass at the balance's 10 Hz; step down discs
  until no flow in 60 s; repeat the smallest with taps.
- **Outputs:** W(D) fitted with Beverloo W = C ρ_b √g (D − k d)^2.5; D_c and D_c,tapped; σ_c ≈ ρ_b g D_c / H(θ)
  with H ≈ 2.2.

## 6. Humidity chambers (tier 2)

- **Boxes:** five clear airtight food containers ≈ 1.2 L (≈ 180 × 120 × 90 internal) with gasketed
  lids. Saturated salt slurries (Greenspan 1977, 25 °C): MgCl₂ 32.8 %, Mg(NO₃)₂ 52.9 %, NaCl 75.3 %,
  KCl 84.3 %, and one with silica gel (≈ 5 %).
- **Inside** (printed): a slurry tray (150 × 90 × 15) on the floor, a perforated shelf 30 mm above it,
  a Ø60 × 5 sample dish (≈ 2 mm layer of 2–5 g powder), a sensor bracket for an SHT45 (PTFE-membrane
  version), and an optional 25 mm 5 V fan.
- **Cable:** a PG7 cable gland through the lid; 4-wire STEMMA QT cable to a TCA9548A I2C multiplexer
  on the bench Pi (all SHT45s are 0x44).
- **SOP:** fingerprint; spread sample; condition 24 h (weigh at 0, 1, 2, 4, 8, 24 h); fingerprint and heap
  AoR again; dry over silica gel 24 h; repeat.
- **Outputs:** uptake (mg/g) vs RH and time, deliquescence onset, change in mg/rev and AoR.

## 7. Rotating drum (tier 2)

- **Drum shaft** (printed, replaces the auger in the doser's brackets): Ø25 tube with the 44T m1 gear at
  the auger's z = 78.33–88.33 (measured from the drum end), tube length 225 to match the auger's
  bearing surfaces, so the doser's own stepper and gears turn it (1–109 rpm).
- **Drum** (printed, on the outlet end): Ø40 ID × 15 deep, 24 radial ribs 0.8 tall on the wall, black
  or white rear-wall insert, front window a Ø50 × 2 acrylic disc in a screw-on printed bezel.
- **Fill:** 40 % of the volume (≈ 7.5 mL).
- **Module horizontal** (`p horizontal`); camera on the axis 120 mm in front; ring light or a low-angle
  LED.
- **SOP:** 1, 2, 5, 10, 20 rpm, 90 s each, 10 fps.
- **Outputs:** dynamic angle vs rpm, avalanche angles (start/stop), surface fluctuation (cohesive
  index), Froude number.

## 8. Unconfined strength (tier 3)

- **Split mould** (printed, ideally SLA): Ø20 ID × 40 (H/D = 2), two halves with alignment pins and two
  printed latches; base plate with a Ø20 locating boss.
- **Consolidation:** printed piston (Ø19.6) + slotted weights; σ₁ 0.2 / 0.5 / 1 / 2 kPa = 6.4 / 16 / 32
  / 64 g total on 314 mm².
- **Load cell:** 100 g mini bar load cell (TAL221) under the sample base, read by the NAU7802 at 10–80 Hz
  (≈ 2 mg noise → 0.06 Pa).
- **Platen:** Ø30 printed disc on the universal linear stage (vertical), lowered at 0.1 mm/s.
- **Frame** (printed): base 120 × 120 with the load-cell mount, a column for the stage.
- **Outputs:** σ_c (peak force / area) vs σ₁ → ff_c = σ₁/σ_c; a free-flowing powder collapses when the mould
  opens (σ_c ≈ 0).

## 9. Blade spreading (tier 3)

- **Coupon:** 100 × 30, 304 stainless 1 mm and printed PLA; sits in a printed coupon bed.
- **Blade:** 304 stainless 1.5 × 25 × 50 ground flat bar (or a single-edge razor in a printed holder) in
  a printed carriage with two M3 gap screws; gap set with feeler gauges 0.10–0.20 mm.
- **Drive:** the universal linear stage (horizontal), 10–100 mm/s.
- **Feed:** the doser lays a 0.2–0.5 g line across the coupon's start.
- **Camera:** silhouette camera looking down at 150 mm, low-angle LED bar.
- **Outputs:** coverage, areal mass (coupon weighed before/after), layer packing fraction, streak area.

## 10. Faraday cup (tier 3)

- **Inner cup:** aluminium, ≈ Ø40 × 50, on three PTFE standoffs.
- **Outer can (shield):** aluminium or steel, ≈ Ø70 × 80, grounded; printed lid with a Ø20 inlet.
- **Charge amplifier:** custom PCB (`pcb/`): low-bias-current op-amp (ADA4530-1 class, < 20 fA), C_f
  10 nF / 100 nF (C0G / polystyrene), reed-relay reset, ADS1115 on board, guard ring, BNC input.
  Full scale ±24 nC / ±240 nC.
- **Mount:** on the in-chamber tripod under the doser outlet (not weighed); the inner cup is weighed
  before and after on the HR-100A with the lead unplugged.
- **SOP:** zero (reset), dose N revs, read Q 2 s after the last grain, weigh; q/m in C/kg.
- **Expected:** 10⁻⁶–10⁻⁴ C/kg → 1–100 nC per gram.

## Printer and slicing

Every printed part fits an A1 mini (180 × 180 × 180). Slice for **Bambu Lab A1 mini, 0.4 nozzle**,
*0.20mm Standard @BBL A1M*, Bambu PLA Basic, 3 walls, 15–25 % infill, textured PEI. Parts that carry
powder are printed with the auger's settings so their surfaces match.

## Folder map

| Folder | What |
|---|---|
| `cad/` | CadQuery source, STEP, STL, renders |
| `print/` | sliced plates, checks, print records |
| `bom/` | priced, linked bill of materials and lead times |
| `pcb/` | KiCad project, Gerbers, renders, BOM |
| `firmware/` | accessory Pico MicroPython |
| `software/` | bench Pi SOP runners, image analysis, tests |
| `sim/` | DEM, FEA, CFD, theory |
| `edison/` | Edison queries and answers |
| `video/` | animation sources and the rendered videos |
| `labs/` | where to run the standard tests |

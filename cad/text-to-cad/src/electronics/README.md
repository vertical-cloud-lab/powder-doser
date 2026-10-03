# Electronics: POWDER_DOSER_V2 PCB (issue #172)

The team's single-doser carrier board, modelled straight from its Gerbers
(`hardware/PCBs/POWDER_DOSER_V2.zip`, EasyEDA Pro 3.2.149, exported
2026-09-29), populated, and stood on a printed holder.

| Script | Output | Purpose |
| --- | --- | --- |
| `pcb.py` | `STEP/electronics/pcb.step` | Bare board: FR-4, all 137 holes, exposed pads, copper under the mask, silkscreen outlines |
| `pcb_assembly.py` | `STEP/electronics/pcb_assembly.step`, `GLB/electronics/pcb_assembly.glb` | Board + modules, headers, caps, barrel jack, 3 standoffs and screws |
| `pcb_mount.py` | `STEP/electronics/pcb_mount.step`, `STL/electronics/pcb_mount.stl` | Printed holder that stands the board up |
| `pcb_holder_assembly.py` | `STEP/electronics/pcb_holder_assembly.step` | The drop-in: populated board on the holder, with the rear M3 screws and the #10 wood screws |
| `pcb_gerber.py`, `pcb_layout.py`, `pcb_parts.py` | (helpers) | Gerber/Excellon reader, board constants, purchased-part stand-ins |

Build everything with `python3 src/electronics/pcb_holder_assembly.py`
(from `cad/text-to-cad`). Check with `python3 checks/pcb_checks.py`, which
writes `checks/results/pcb_checks.json`. Review images are in
`renders/electronics/`. `pcb_vs_gerber.png` puts the raw Gerber artwork,
text included, beside the CAD board.

## Board

* **Outline**: 101.6 x 76.2 mm (4.000 x 3.000 in) rectangle. The GKO outline
  runs from x -78.105 to 23.495 and from y -47.625 to 28.575 in EasyEDA
  coordinates. The board is 2-layer. Its thickness is not in the Gerbers, so
  it is modelled at the standard 1.6 mm.
* **Frame** (`pcb.step`, `pcb_assembly.step`): the origin is the lower-left
  outline corner, X runs along the 101.6 mm edge, Y along the 76.2 mm edge,
  and Z is up. The FR-4 spans z = 0 to 1.6, with the top (component) side
  up. Board = Gerber + (78.105, 47.625).
* **Holes** (Excellon): 137 in total. All 137 are drilled in `pcb.step` and
  all 137 are matched by the check.

  | Tool | Count | Use |
  | --- | --- | --- |
  | 0.90 mm PTH | 80 + 3 slots | 4 x 1x20 Pico-format rows; barrel-jack slots, 0.9 mm wide (3.0 to 3.1 mm long) |
  | 1.00 mm PTH | 20 | DRV8871 header (4), 4 caps (8), Tic motor row (4), motor-out header (4) |
  | 1.02 mm PTH | 9 | 2 servo headers (6), Tic serial (3) |
  | 1.10 mm PTH | 14 | D24V22F5 (5), DRV2605L (5), shunt (4) |
  | 1.20 mm PTH | 2 | Tic VIN/GND |
  | vias | 4 x 0.305 + 2 x 0.610 | tented |
  | **4.064 mm NPTH** | **3** | mounting holes, see below |

* **Mounting holes**: there are only **three** (0.160 in, NPTH).

  | Name | Board frame (mm) | Gerber (mm) | Note |
  | --- | --- | --- | --- |
  | `lower_left` | (6.350, 6.985) | (-71.755, -40.640) | free |
  | `lower_right` | (86.995, 7.620) | (8.890, -40.005) | under the shunt module. The module seats 2.54 mm above the board, so this hole needs a low head (button head, 1.65 mm) |
  | `upper_mid` | (63.500, 61.595) | (-14.605, 13.970) | between the RS-232 module's header rows, about 11 mm under its PCB |

## What is on the board

Evidence comes first from `FlyingProbeTesting.json` in the zip. It gives
the designer's component names, centroids, every pin, and its net. That is
checked against the PR #115 BOM pin contract, the vendor CAD and Eagle files
in `hardware/vendor-files/`, and the silkscreen outlines.

| Footprint (probe name) | Part | Evidence | CAD in `pcb_assembly` |
| --- | --- | --- | --- |
| `pico_l`, `pico_r` | **U2 Raspberry Pi Pico W** (USB toward +Y, the board's top edge) | 2 x 20 holes 0.9 mm, rows 17.78 mm apart. Nets match the PR #115 contract exactly: GP0/1 = SDA/SCL, GP2 = servo 2, GP4/5 = STP_TX/RX, GP10/11 = SOL_IN1/2, GP12/13 = SCALE_TX/RX, GP14 = HAPT_EN, GP15 = servo 1, pin 39 VSYS = 5V, pin 36 = 3V3 | Stand-in `pcb_parts.pico_w`. Boxes are taken from the step.parts `raspberry_pi_pico_w` solids; that model was 13 MB once re-emitted. It sits in 2 x 1x20 sockets (8.5 mm) on its own headers, PCB underside at z = 12.64 |
| `waveshareleft`, `waveshareright` | **U6 Waveshare Pico-2CH-RS232** (SP3232EEN) | Pico-format 2 x 20. Pins 1/2 (UART0 position) = SCALE_TX/RX. VSYS and 3V3 are both on 3V, which matches the BOM ("power VCC from +3V3") | Stand-in. No vendor CAD exists; the Waveshare wiki gives the size as 21 x 52 mm. It carries female headers underneath and plugs onto 2 x 1x20 male headers |
| `tic`, `ticpower`, `stepperpins` | **U5 Pololu Tic T500** | The 0.1 in row 12V, GND, gap, A1, A2, B2, B1 equals the Tic's x = 36.83 column, which has a gap at 12.70. The GND/TX/RX row is 35.56 mm (1.4 in) away, on the Tic's opposite column. Silk outline 26.7 x 38.3 mm vs Tic 26.67 x 38.1 mm | Stand-in. Holes come from the vendor `tic-t500-...step` in `pololu-3135-tic-t500/cad/*.zip`. Rotated +90 deg, USB facing the board's left edge. Seated on 1x2, 1x4 and 1x3 headers |
| `solenoiddriver` | **U4 Adafruit DRV8871** (solenoid) | Pins GND, 12V, SOL_IN1, SOL_IN2 = JP2 (GND, VMOTOR, IN1, IN2) in `Adafruit DRV8871.brd` | Stand-in sized from `3190 DRV8871 Breakout.step` and the .brd. Rotated +90 deg |
| `hapticdriver` | **U3 Adafruit DRV2605L, STEMMA QT revision** | Pins IN, SDA, SCL, GND, 3V = JP2 (VCC, GND, SCL, SDA, IN) rotated 180 deg. The silk outline 25.5 x 17.9 mm matches the STEMMA QT board (25.4 x 17.78), not the older 17.78 x 16.51 board in vendor-files | Stand-in from `Adafruit DRV2605L STEMMA QT.brd` (outline, holes, header, JST-SH) |
| `5v_reg` | **U1 Pololu D24V22F5** 5 V buck | Pins NET, NET, 12V, GND, 5V = PG, EN, VIN, GND, VOUT. Silk 17.8 mm square = the 0.7 in board | Stand-in from the vendor STEP holes and the reg19a drawing. It overhangs the board's top edge by 3.8 mm, as the silk shows |
| `Shunt` | **SR1 Pololu #3776** 33 V / 9 W shunt regulator | Pins GND, -, -, 12V. Silk 28.6 x 20.3 mm = board 28.575 x 20.32 | Stand-in from `shunt-regulator.step` (holes, 12 top resistors). Its bottom resistors are fitted only on 15 W versions, so they are omitted. Rotated 180 deg, flush with the board's bottom/right corner |
| `12v_cap`, `tic_cap`, `5v_cap`, `3v_cap` | **C1/C3/C2/C?** radial electrolytics, D10 mm, 5.0 mm pitch | Silk circles 10.1 mm with the minus band on the GND pad. BOM: C1 100 uF/25 V on 12 V, C3 100 uF/25 V at the Tic VIN, C2 100 uF/10 V on 5 V. `3v_cap` is not in the BOM | step.parts `cp_radial_d10_0mm_p5_00mm` (KiCad model) |
| `12vBarrel` | **J1** 5.5/2.1 mm DC jack for the Mean Well GST60A12 | 3 slotted pads: centre pin to 12V, sleeve and switch to GND. Silk body 14.4 x 9.1 mm, opening 5 mm past the left edge | step.parts `barreljack_horizontal`. Its pin 3 is 3.0 mm off the axis; the board has 2.5 mm |
| `servo_l`, `servo_r` | 3-pin 0.1 in headers for the two MG996R servos | Signal (GP2 / GP15), 5V, GND, with "-" and "+" marks in the silk | Stand-in 1x3 male header |
| `stepperpins_OUT` | 4-pin 0.1 in header to the NEMA 11 motor | STP_A1, A2, B2, B1 | Stand-in 1x4 male header |
| mounting | 3 x M3 x 10 F-F hex standoffs (below), 3 x M3 x 6 button heads (top) | 4.064 mm NPTH | step.parts `standoff_hex_female_female_m3_l0010_simple`, `button_head_screw_m3_l0006_simple` |

### Why stand-ins instead of the vendor STEP files

cadgen re-emits the vendor models at these sizes:

| Model | Re-emitted size |
| --- | --- |
| Tic T500 | 13.2 MB |
| Pico W | 13.1 MB |
| D24V22F5 | 5.0 MB |
| Shunt | 5.1 MB |
| DRV8871 | 2.2 MB |
| KiCad 1x20 header | 1.6 MB |

That is far over the ~5–10 MB budget per committed file. The stand-ins in
`pcb_parts.py` keep each module's real board outline and hole pattern, which
were measured from the vendor STEP and Eagle files. Their component
envelopes come from the vendor solids or the dimension drawings. Header pins
are round 0.64 mm posts. The check confirms that all 107 module pins land on
their footprint pads within 0.001 mm. The vendor files remain the reference
in `hardware/vendor-files/`.

## Holder and pose in the doser world frame

`pcb_mount` is a single printed part, about 70 cm³:

* a 5 mm base, 120 x 70 mm, with a window in the front toe and 3 countersunk
  #10 holes in the rear deck;
* a 4 mm upright, 110 x 84 mm, with 3 teardrop M3 holes on the PCB's
  mounting pattern;
* two 4 mm gussets.

Print it base-down without supports. The upright and gussets are vertical
walls, the gusset slopes face up (about 58 deg), the horizontal holes have
45 deg roofs, and every wall is at least 4 mm thick.

Hardware, besides the PCB's own 3 x M3 x 6 button heads and 3 x M3 x 10 F-F
standoffs:

* 3 x M3 x 8 button heads, fitted from behind the upright;
* 3 x #10 x 1 in flat-head wood screws, 20 mm into the 38.1 mm board. These
  are a stand-in because step.parts has no wood screws.

**`pcb_holder_assembly` frame**: z = 0 is the wooden board's top surface,
x = 0 is the holder centre line, and y = 0 is the holder's front face.
Everything lies at y >= 0.

* Footprint: x = -60..60, y = 0..70.
* Height: 92.1 mm (84 mm upright; the D24V22F5 reaches z = 92.1).
* The wood screws go down to z = -20.4.

The PCB stands vertically with its components facing -Y, toward the doser:

* component face at y = 24.4;
* back face at y = 26.0, on 10 mm standoffs;
* upright front face at y = 36.0;
* lower edge at z = 12.

**Pose in the doser assemblies** (`lib/electronics_place.py`): the holder
is turned -90° about z, so its 120 × 70 mm footprint runs along y with the
components facing -x, towards the doser. It stands on the +X side of the
board, at x = 50..120:

* current doser: origin at `(50, 200, 0)`, so the holder spans y = 140..260;
* servos-above doser (its baseplate reaches y = 170): origin at
  `(50, 240, 0)`, so the holder spans y = 180..300.

The first pose, on the centre line behind the doser at `(0, 150, 0)` or
`(0, 190, 0)`, did not work. The auger runs along y on x = 0 out to
y = 286, and the mounting plate, stepper and rear bracket sweep
x = -46..54 behind the hinge, so the tube and the plate cut through the
holder and the board (`checks/electronics_clearance.py`). Off the centre
line, the tilting parts pass the holder at every angle from 0 to 45°.

## Uncertainties and findings

* **Three mounting holes, not four**: the drill file has three 4.064 mm
  NPTH. The task brief assumed four.
* **RS-232 footprint is mirrored**: on `waveshareleft/right`, pin 1 is at the
  top-right. On the Pico footprint it is at the top-left. A face-up
  Pico-format module would put its GP0/GP1 on VBUS/VSYS. Check the module's
  orientation, or the footprint, before soldering. The stand-in is drawn
  face-up.
* **DRV2605L revision**: the silk is for the STEMMA QT board. The vendor
  STEP is the older revision, so the stand-in follows the silk.
* **D24V22F5 silk is offset by about 3 mm**: the designer's outline is
  centred on the pin row. The real module has its pins toward one side (PG
  at x = 1.27 of 17.78). The model follows the pins.
* **Tic T500 terminal block**: the pre-soldered #3135 would put its 6-way
  terminal block over the 0.1 in power/motor row this carrier uses. The
  board therefore implies a bare Tic (or the block removed), and it is
  modelled bare.
* **Seating heights are assumptions**: modules sit on 2.54 mm male-header
  plastic. The Pico sits in 8.5 mm sockets.
* **Other assumptions**: board thickness 1.6 mm, gold-coloured exposed
  copper, and the KiCad capacitor height of 10 mm. The 3V3 capacitor's
  value is unknown.
* **Left out of `pcb.step` to save size**: silkscreen text and bottom copper
  and pads. The first complete build was 130 MB, at about 1 kB per B-rep
  edge. Both appear in `pcb_vs_gerber.png`.

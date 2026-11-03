# Linear actuator for the dosing station: parameters and parts

For [#202](https://github.com/vertical-cloud-lab/powder-doser/issues/202). The numbers come from the carousel designs in
[PR #185](https://github.com/vertical-cloud-lab/powder-doser/pull/185) (branch `claude/issue-128-20261013-2050` at
[`a94824f`](https://github.com/vertical-cloud-lab/powder-doser/tree/a94824f)): its CAD parameters, rig scripts and
MuJoCo station runs. Vendor specs, prices and stock were read on the makers' own datasheets and product pages on
2026-11-03. Prices drift, so treat the links as the source of truth.

## Recommendation

Order the part the designs are already drawn around:

| Qty | Part | Price | Stock (2026-11-03) |
|---|---|---|---|
| 1 | [Actuonix P16-150-22-12-P](https://www.actuonix.com/p16-150-22-12-p): 150 mm stroke, pot feedback, 22:1 | $90.00 | 82 |
| 1 | [Actuonix LAC control board](https://www.actuonix.com/lac) | $30.00 | 166 |
| 1 | [Actuonix 12 V, 2 A supply](https://www.actuonix.com/dcpowersupply) (choose 12 V) | $10.00 | 149 |
| 1 | [LAC case](https://www.actuonix.com/case) (optional) | $12.00 | 171 |
| 1 | [USB Mini-B cable](https://www.actuonix.com/usb-mini-b) for the LAC's USB setup and readback | $4.00 | 79 |
| | **Total** before shipping and import duty | **$146.00** | |

- The P16-150-22-12-P meets every parameter below.
- v2, v3, v4 and the paternoster all use it, with Actuonix's own STEP in the CAD (`cad/vendor/actuonix.py` on the
  #185 branch). Their clevises, pins, frame height and MuJoCo runs are all sized for it.
- **Optional:** add a [P16-150-64-12-P](https://www.actuonix.com/p16-150-64-12-p) ($90, 92 in stock). It has the same
  body, ends and stroke, so it swaps in with no CAD change. It is slower (18 mm/s) but has 90 N and 200 N back-drive
  instead of 50 N and 75 N. Testing both on the bench (T6 in the v3/v4 test plans) answers the speed-versus-holding
  question with real parts.

## What the actuator does

There is one actuator at the station on the bottom run, pinned at both ends (a two-force member). In v3 and v4 it:

1. lifts the electronics carriage (EC) out of its guide cradle and docks it under the module's plate (20 mm in v3,
   28 mm in v4);
2. keeps pushing, so that module and EC tilt together about the hinge to the dose angle (30° by default; the window is
   20-40°; v3 goes to 90°, v4 to 50°);
3. holds still while the auger turns and the solenoid taps;
4. tilts back, then pulls the EC off its seat magnets and parks it.

## Parameters

| Parameter | Target | Why |
|---|---|---|
| Type | Brushed-DC lead-screw **rod** actuator with **absolute position feedback** (potentiometer) and a clevis eye at each end | Sterling asked for an Actuonix with position feedback (#185). Every design pins it at both ends. A pot needs no homing after a power cut |
| Stroke | **At least 100 mm** for the 20-40° window. **150 mm** keeps each design's full range | With 3 mm in reserve: v3 needs 64 mm at 30°, 80 at 40°, 97 at 50° and 157 at 90°. v4 needs 72 at 30° and 105 at its 50° limit. 100 mm reaches 52° in v3 and 47° in v4. 150 mm reaches 85° in v3 and all 50° in v4 (plot below) |
| Closed length (hole to hole) | **About 200 mm or less** | The frame was raised so the P16-150 (197.4 mm) stands under the hinge (the `Z_RUN` note in v3/v4 `params.py`). Every mm longer raises the hinge by a mm; shorter lets the frame drop. The stroke needed hardly depends on the closed length (within 0.7 mm from 135 to 247 mm) |
| Max force | **40-50 N or more**; **100 N or less** preferred | MuJoCo: 9.2 N peak over v3's dock-tilt-dose-undock cycle, 19.3 N transient in the paternoster, 3.2 N to hold 30° with an empty module. When the EC toppled in v3 as drawn, the P16 was driven to its 50 N limit, so extra force mostly goes into printed parts during a jam |
| Continuous force (peak-efficiency point) | **20 N or more** | Covers the 19.3 N transient. It also covers pulling the EC off stronger seat magnets: about 13-14 N if each seat ball gets the 8 N that v3's simulation proposes. That is my estimate: 2 × 8 N, plus 0.8 N at ball C, less the EC's 3 N weight |
| Back-drive (holds with power off) | **30 N or more** | Three times the 10 N steady load, so the tilt holds through taps and the motor can sit idle while the balance settles, with no controller dither |
| Speed | **20-50 mm/s** with no load, adjustable | A 30° dose moves the rod 126 mm (v3) or 141 mm (v4) in the rig's sequence. At 46 mm/s that is 3-3.5 s. The simulation docked at 18 mm/s, and the LAC's speed setting slows the approach |
| Duty cycle | 20% or more (every candidate is 20%) | At 20%, a 46 mm/s actuator allows a dose every 15-17 s, and an 18 mm/s one every 37-42 s |
| Repeatability | **±0.6 mm or better** | The EC's pin rides in 2 mm lost-motion slots, and 1 mm of rod is 0.63° of tilt near 30° |
| Feedback the Pi can read | yes | The rig scripts drive the LAC open loop with RC pulses and wait a fixed time. Reading the position back confirms the dock and the tilt, and catches a jam |
| Side load | 10 N or more | Pinned at both ends, it swings at most 7° about its base pin in v3/v4, so the side load is pin friction plus its own weight |
| Ingress | IP54 or better (IP65 is better still) | It stands under the dose point, in the powder |
| Supply | 12 V DC, 1 A stall or less | The station already has 12 V for the solenoid and the NEMA 11 driver, and the LAC needs the actuator's rated voltage |
| Envelope | No bigger than the P16's 20 × 36 mm body; vendor STEP available | Its column already stands inside the HR-100A's breeze break, which is why the scale doesn't fit (v3/v4 item 6) |
| Ends | Ø4.25 mm holes, 8 mm rear tab, 6 mm rod-end tab | The base clevis (8.4 mm gap), the EC's clevis and the 4 mm shoulder screws (McMaster 90265A123) are drawn round the P16's ends. Another model means redrawing those parts |
| Cost | $150 or less with its controller, and in stock | |

### Stroke against tilt

![Stroke needed against tilt](stroke_vs_tilt.png)

- **The stroke depends on where the rod pins to the EC, not on which actuator is used.**
  - In v3/v4 the EC's pin is 95 mm from the hinge, with a moment arm of 91 mm at 30°.
  - v2's and the paternoster's U-yoke pin was 46 mm out, with a 45 mm arm. There, 90° took only 88 mm of stroke, but
    each N·m of moment took twice the force.
- A future station that moves the pin is trading stroke for force in that ratio.
- [`stroke_vs_tilt.py`](stroke_vs_tilt.py) recomputes the plot and [`stroke_vs_tilt.json`](stroke_vs_tilt.json) from
  the rig scripts' geometry.

## Candidates

All have potentiometer feedback, 12 V, a 20% duty cycle, and $78-90 each. Reach is the furthest tilt with 3 mm kept
back. Dose spacing is the shortest time between 30° doses at the 20% duty limit, at the speed under 10 N.

| Part | Stroke / closed | Max force / back-drive | Speed, no load | Side load | Body | Reach v3 / v4 | Dose spacing v3 / v4 | Price, stock | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| [Actuonix P16-150-22-12-P](https://www.actuonix.com/p16-150-22-12-p) | 150 / 197 mm | 50 / 75 N | 46 mm/s | 10 N | 20 × 36 mm, IP54, 125 g | 85° / 50° | 15 / 17 s | $90, 82 | **Order this** (as drawn) |
| [Actuonix P16-150-64-12-P](https://www.actuonix.com/p16-150-64-12-p) | 150 / 197 mm | 90 / 200 N | 18 mm/s | 10 N | same | 85° / 50° | 37 / 42 s | $90, 92 | Drop-in if holding or magnet pull-off needs more |
| [Actuonix P16-100-22-12-P](https://www.actuonix.com/p16-100-22-12-p) | 100 / 147 mm | 50 / 75 N | 46 mm/s | 15 N | same | 52° / 47° | 15 / 17 s | $90, 78 | If dosing stays at 20-40°: frame 50 mm lower |
| [Actuonix L16-140-63-12-P](https://www.actuonix.com/l16-140-63-12-p) | 140 / 208 mm | 100 / 46 N | 20 mm/s | 20 N | 18 × 20 mm, IP54, 84 g | 78° / 50° | 34 / 38 s | $80, 118 | Slimmest at full stroke; frame 11 mm higher; ends redrawn |
| [Actuonix L16-140-35-12-P](https://www.actuonix.com/l16-140-35-12-p) | 140 / 208 mm | 50 / 31 N | 32 mm/s | 20 N | same | 78° / 50° | 22 / 25 s | $80, 142 | Same, faster; back-drive only just meets 30 N |
| [Actuonix P8-100-165-12-P](https://www.actuonix.com/p8-100-165-12-p) | 100 / 135 mm | 110 / 40 N | 9.2 mm/s | 2 N | 11 × 25 mm, IP54, 41 g | 52° / 47° | 73 / 82 s | $85, 103 | Actuonix's smallest, but slow, and only 2 N side load |
| [Progressive Automations PA-MC1-6-8-POT-12VDC](https://www.progressiveautomations.com/products/ip65-micro-linear-actuator-potentiometer) (choose 12 VDC / 6 inch / 8 lbs) | 152 / 223 mm | 35 / 20 N (static) | 48 mm/s | not given | 18 × 20 mm, **IP65** | 86° / 50° | 15 / 17 s | $77.99, in stock | Non-Actuonix option; dust-tight, but frame 26 mm higher and 20 N holding |

Datasheets: [P16](https://www.actuonix.com/assets/images/datasheets/ActuonixP16Datasheet.pdf) (rev B),
[L16](https://www.actuonix.com/assets/images/datasheets/ActuonixL16Datasheet.pdf) (rev E),
[P8](https://www.actuonix.com/assets/images/datasheets/Actuonix%20P8%20Datasheet.pdf),
[PA-MC1](https://7717445.fs1.hubspotusercontent-na1.net/hubfs/7717445/PDF%20Manuals/Actuator%20datasheets/PA-MC1-POT%20Datasheet.pdf).
The P16 sheet is byte-identical (sha256 `070deb5f…`) to the copy #185 pinned in `cad/vendor/manifest_actuonix.json`.

**Considered and not recommended:**
- [Actuonix S20-100-38-B](https://www.actuonix.com/s20-100-38-b) stepper ($80): 13 N maximum on its product page, and
  its [datasheet](https://actuonix-com.3dcartstores.com/assets/images/datasheets/ActuonixS20-38MMDatasheet.pdf) advises
  running at 50-75% of that. That is under the 19 N peak, and it has no position feedback.
- [Actuonix T16-P](https://www.actuonix.com/t16) track actuators: their datasheet lists no ingress protection, and a
  sliding carriage doesn't fit the pinned two-force mount.
- P16-200 (4 N side load, 247 mm closed). P8-100-50 (10 N back-drive, about the holding load). The 150:1 and 256:1
  gearings (5-8 mm/s, and 200-300 N into printed parts on a jam).
- Pololu Glideforce LACT4P and Progressive Automations PA-14P: 150-670 N class, far larger than needed, $145-195.

## Controller

- **[Actuonix LAC](https://www.actuonix.com/lac) ($30)** closes the loop on the pot. It takes RC, PWM, 0-3.3 V, 4-20 mA
  or USB input, and has stall detection and soft stroke limits.
  - The #185 rig scripts already drive it with RC pulses from GPIO 18 through pigpio.
  - In RC mode the Pi never reads the position. To read it, use the LAC's USB commands (`SET_POSITION` returns the
    current position, `GET_FEEDBACK` is `0x10`), in the 3-byte protocol of the
    [advanced configuration guide](https://www.actuonix.com/assets/images/datasheets/ActuonixLACAdvancedConfigurationDatasheet.pdf).
  - Actuonix ships a Windows DLL for USB. It should work from Linux with pyusb (USB ID `04d8:fc5f`, as reported on
    RobotShop's forum), but that is untested.
  - Set the limits 1-2 mm short of the end stops, as Actuonix advises, and keep the stall time short so a jam stops
    the motor.
- **Alternative: [Pololu Jrk G2 21v3](https://www.pololu.com/product/3142) ($54.95).** It reads the same pot as 0-5 V
  feedback, talks USB, TTL serial or I²C with Linux-supported tools, and reports position and current, with software
  current limiting.

## Where to buy

- **Actuonix direct** (prices above): ships from Canada by DHL. Its shipping page says US duties and tariffs are not
  included, and points to US Customs for China-origin products.
- **DigiKey Marketplace** (shipped by Actuonix): [P16-150-22-12-P](https://www.digikey.com/en/products/result?keywords=P16-150-22-12-P)
  2495-P16-150-22-12-P-ND at $100 (48 in stock), P16-150-64-12-P at $100 (50), LAC 2495-LAC-ND at $50 (47).
- **RobotShop US:** [P16-150-22-12-P](https://www.robotshop.com/products/actuonix-p16-p-linear-actuator-150mm-221-12v-w-potentiometer-feedback)
  at $113.21 (backorder), [LAC](https://www.robotshop.com/products/actuonix-linear-actuator-control-board) at $34.80.

## Caveats

- **The force and holding targets come from simulations.** Nothing at the station has been built (see #185's test
  plans).
- **The 13-14 N pull-off is my estimate** for the proposed stronger seat magnets. It isn't a simulated number.
- **None of these actuators fixes the scale fit by itself.** The EC's column has to move out of the breeze break
  (v3/v4 item 6).
- **Any model other than the P16 needs its own STEP** in `cad/vendor/` and redrawn clevises.
- **Not checked for the PA-MC1:** compatibility with the LAC (on paper, the LAC takes 12 V third-party actuators with
  pot feedback), its side load and its repeatability.

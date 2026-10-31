# Station FEA: chain carousel v3 and v4 (#185 at 45e9740)

`cases/station.py` (CalculiX 2.21, C3D10, single-threaded) and its hand calculations (`hertz.json`). Every number is a prediction: nothing is built.
- Printed parts are PETG, checked against 23 MPa (Bambu PETG HF across the layers, short-term).
- Steel ball contacts are checked against first subsurface yield (Hertz: 1.6 Y for point contact, 1.67 Y for line contact).
- Hardened 52100 balls and dowels are checked against 4000 MPa (ISO 76).

## Summary table

| Part | Design | Load case | Max displacement (mm) | Peak stress (MPa) | Allowable (MPa) | SF | Functional number |
|---|---|---|---|---|---|---|---|
| Dock cone A (1/4 in ball in the EC's printed 45° cone) | v3 | docked and tilting 0-45°, motor idle | 1.0-1.5 µm approach | 9.3-11.7 (contact) | 73 | 6.3-7.9 | 2.1-2.6 µm approach after creep |
| Dock cone A | v3 | P16 stall, 50 N | 4.3 µm | 20.9 | 73 | 3.5 | |
| Dock vee B (ball on two hardened 1/8 in dowels) | v3 | docked and tilting | 0.2-0.4 µm | 700-1190 | 4000 | 3.4-5.7 | normal force only 0.6-3.0 N |
| Dock vee B | v3 | P16 stall | 1.5 µm | 2134 | 4000 | 1.9 | |
| Dock flat C (ball C on the low-carbon steel armature) | v3 | docked and tilting | | 1236-1371 | 288 | 0.21-0.23 | yields locally: a dent about 1.0 µm deep and 0.16 mm across, then elastic |
| Dock, all three contacts | v3 | tilt 0-45°, motor idle | | | | | stays seated (lowest normal: B 0.93 N at 45°) |
| Dock, all three contacts | v3 | 3 N solenoid tap | | | | | vee B unseats at 0°, 15°, 30° and 45° (B goes to -1.2 to 0 N) |
| Dock: drive torque it holds seated | v3 | NEMA 11 mesh load | | | | | 3-19 N·mm at the pinion frictionless; 20-43 N·mm with μ 0.15. Heavy running is 13.6 N·mm, the 0.45 A stall 67 N·mm |
| Dock cone / vee / flat (case-hardened washer) | v4 | docked at 0°, motor idle | ≤ 0.8 µm | 7.9 / 1166 / 1080 | 73 / 4000 / 960 | 9.3 / 3.4 / 0.89 | seated: A 2.98, B 2.83, C 5.24 N |
| Dock, all three contacts | v4 | tilt 15°, 30°, 50°, motor idle | | | | | **unseats: cone A goes into tension (-2.1 to -3.9 N; -8 to -10 N with a tap)** |
| Dock | v4 | P16 stall at 0° / 50° | | | | | unseats: A at -5.7 N / -180 N |
| Electronics carriage v3 (printed, with bridge ribs, see finding 3) | v3 | tilt 30°, mesh load at the dock's seated limit (0.12 x stall) | 0.17 | 2.1 | 23 | 11 | pinion-to-gear centre distance opens 0.076 mm |
| Electronics carriage v3 | v3 | P16 stall 50 N at 0° | 0.62 | 19.8 at the base's back legs | 23 | 1.16 | centre distance opens 0.33 mm |
| Electronics carriage v4 (reach-round arms) | v4 | docked at 0° | 0.21 | 3.0 | 23 | 7.7 | arm contacts move 0.18-0.21 mm; centre distance changes 0.001 mm |
| Electronics carriage v4 | v4 | P16 stall 50 N at 0°, dock assumed to hold | 1.18 | 26.6 at the +y arm's C end | 23 | 0.86 | upper bound: the dock tips open before this |
| Electronics carriage v4, undocked | v4 | natural frequencies, held at its clevis pin | | | | | 32.8 Hz door finger; 39.3 / 73.2 / 89.8 Hz whole EC rocking on its cheeks (peaks at the arm tips); arms alone about 1.8 kHz (hand) |
| Guide cradle (on one 2020 post) | v3 | parked EC, 3.2 N | 0.13 | 1.6 | 23 | 14 | seats sink 0.08 mm (about 0.15 mm after creep) |
| Guide cradle | v3 | P16 retract stall 50 N + weight + 2 N lean | 2.23 | 25.6 at the arm-to-wall corner | 23 | 0.90 | cone seat sinks 1.40 mm |
| Guide cradle (mirrored, with arm notches) | v4 | same as v3 | 2.28 | 26.6 | 23 | 0.87 | cone seat sinks 1.56 mm |
| Cradle seats (ball on cone / dowels / plain M4 washer) | v3, v4 | parked, sustained | 0.2 µm (0.4 µm after creep) | 4.1 / 760 / 738 | 73 / 4000 / 400 | 18 / 5.3 / 0.54 | the washer dents by well under 1 µm |
| P16 base clevis bracket (printed) | v3 (v4 uses the same part) | P16 stall 50 N, vertical | 0.013 | 3.3 | 23 | 6.9 | |
| P16 base clevis bracket | v3 | back-drive 75 N at 30° | 0.059 | 5.2 | 23 | 4.4 | |
| Clevis pins (4 mm 18-8 shoulder screws, hand) | v3, v4 | 75 N, double shear | | 3.0 shear | 119 | 40 | 1.9 MPa mean bearing on the EC's 5 mm cheeks |
| Latch rail (cam) | v3 | follower on the 25° ramp, 3.3 N | 0.6 µm | 0.22 | 23 | > 100 | |
| Latch rail | v3 | jammed follower, NEMA 34 at 12 N·m | | | | | rail holds about 350 N on the ramp; a jam puts 585 N on it (247 N chain pull / sin 25°) |
| Latch rail + tube rest (one part) | v4 | module on the rest (2.1 N) + follower 3.3 N | 0.021 | 0.42 | 23 | 55 | 0.021 mm against the 0.5 mm rest gap |
| Latch rail + tube rest | v4 | jammed follower | | | | | holds about 285 N on the ramp |
| Hold-down | v3, v4 | 25 N up on the lip (half a P16 stall through the carriage) | 0.013 | 6.5 | 23 | 3.5 | lip lifts 0.013 mm (gap 2.0 mm) |

## What the results say

1. **v4's dock tips open as it tilts.** It is seated at 0°. From 15° on, the cone A goes into tension: -2.1 to -3.9 N with the motor idle, -8 to -10 N during a solenoid tap. Two things cause it:
   - The P16 pushes on the EC's clevis 88 mm below the dock contacts. The clevis tilts with the module, so at 30° 60 % of the P16 force acts along the auger.
   - The contacts resist that moment over only a 20 mm base along x (A and B at x 44, C at x 64). The clevis pin (x 58) is also outside the contact triangle, which spans x 44-54 at y 0.

   None of these alone fixes it: moving the pin to x 48, moving the vee to x 64, or stronger seat magnets. It needs either about 10-15 N more preload at A (for example v3's dock electromagnet), or a long x-base like v3's 84.5 mm, which means a contact behind the 44T gear.
2. **v3's dock carries the tilt, but with almost no margin at the vee.**
   - The vee's magnet sits 2.4 mm below its ball and pulls with about 0.9 N; the cone's sits 0.6 mm away and pulls 4.3 N. So B carries only 0.6-3.0 N, and a 3 N solenoid tap unseats it at 0°, 15°, 30° and 45°.
   - The pinion's tangential force twists the dock. A and B, 37 mm apart, react that twist, so B's preload and the friction at C set how much drive torque the dock holds.
   - Frictionless it holds 3-19 N·mm at the pinion, below the 13.6 N·mm of heavy running. With μ 0.15 it holds 20-43 N·mm, 1.5-3x heavy running. A jam slips the dock before the DRV8825 0.45 A stall (67 N·mm).
   - Fix: put the vee's magnet 0.6 mm under its ball, like the cone's. B then carries at least 2.3 N in every state and taps no longer unseat it.
3. **EC v3 as drawn has a loose piece.** The electromagnet cup and ball C's boss are a separate solid, 3.6 mm from the bracket arms. The arms end at x 90 (|y| 12-15) and the cup is r 12 about x 100, so they never meet.
   - For this FEA I added two bridge ribs (x 88-99.5, |y| 10.4-12.4, full bracket height). They stay inside the carriage window's |u| ≤ 13 behind x 88 and clear the pinion (x ≤ 88.3).
   - Even bridged, the bracket's give pitches the plate on its three balls. The gear centre distance opens 0.076 mm docked and 0.33 mm at a P16 stall.
4. **Ball C dents v3's armature.** The steel ball on low-carbon steel peaks at 1236-1371 MPa against 288 MPa first yield.
   - It dents about 1 µm on the first docks, then stays elastic. That is harmless for the mesh.
   - A hardened flat (like v4's washer) avoids it. The cradle's plain M4 washer dents too, by well under 1 µm.
5. **A P16 retract stall overloads the cradle.**
   - Pulling the EC into the cradle at 50 N bends the single-post arm to SF 0.9 at its sharp corner (7.9 MPa nominal, Kt about 3.2). The cone seat sinks 1.4-1.6 mm. Parked, the seats sink only 0.08 mm.
   - Fixes: limit the retract in firmware using the P16's pot, add a 2-3 mm fillet or gusset at the arm, or add a second post.
   - The EC's base reaches SF 1.16 at a P16 stall. The clevis bracket, pins, latch rails and hold-downs are all at SF 3.5 or more.
6. **A jammed latch follower at full drive torque would break either printed rail.** Their ramps hold about 350 N (v3) and 285 N (v4); a jam puts about 585 N on them. This relies on the closed-loop NEMA 34 faulting on its following error first.

## Checks against hand calculations

- **EC load set against the statics:**
  - 30° case: FEA pin reaction (2.64, 0, 3.58) N, statics (2.74, 0, 3.69) N.
  - P16 stall: 48.8 N against 50.0 N.
  - The residual moment is ≤ 31 N·mm. The FEA spreads the EC's mass over its printed body, which puts the centre of mass about 6 mm from the statics' estimate.
- **EC base at the P16 stall:** as a fixed-fixed 30 x 3 mm beam, 6.4 MPa nominal at the x 70 legs. The FEA's 19.8 MPa is at the 4 x 4 mm leg's sharp corner (Kt about 3).
- **Cradle arm root:** 53 N at 17.8 mm on a 20 x 6 mm section gives 7.9 MPa nominal. The FEA gives 25.6 MPa at the corner.
- **Clevis cheeks:** 1.7 MPa mean bearing (2.2 MPa peak for a cosine distribution) by hand, 3.3 MPa in the FEA.
- **Vee Hertz:** 1587 MPa at 5 N per dowel by hand (Hamrock-Brewe), the same as the code.
- **Cone:** 10.3 MPa at 5 N, against the design's own "about 11 MPa at 5 N" (params.KC_CONE_HALF).

## Assumptions that could change a conclusion

- **Seat magnet pull is modelled, not measured.** The model gives 4.3 N at 0.6 mm and 0.9 N at 2.4 mm, ±50 %. v3's vee margin and v4's tension at A scale directly with it, so measure the real magnet on a ball.
- **Friction at the balls (μ 0-0.3) is unknown.** It decides whether v3 holds heavy running: frictionless it doesn't, at μ ≥ 0.15 it does.
- **Load estimates:**
  - Auger torques come from cad/gear-mesh (0.03 N·m heavy running at the auger; the 0.45 A stall).
  - EC masses (0.33 / 0.31 kg) and module masses (0.226 / 0.218 kg) are estimates.
- **The tap is treated as a steady 3 N.** It really lasts 10 ms, and the EC's inertia limits how far it separates. "B unseats" means chatter at the vee, not losing the dock.
- **v4 statics assume nothing guides the EC while it tilts.** The P16's direction comes from the layout (base pin fixed, rod-end pin on the EC). A guide during the tilt would change v4's conclusion.
- **Allowables are conservative.** Every printed part is checked against the across-layer strength (23 MPa). Peaks at the CAD's sharp corners depend on the mesh; nominal stresses are about 3x lower.

Not done: the mounting plate's dock-side features (pressed-in balls, keeper) under the dock loads.

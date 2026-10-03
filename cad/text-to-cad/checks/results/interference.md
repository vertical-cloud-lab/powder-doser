# Interference sweep (issue #172)

`checks/interference.py --tilts 0 15 30 45 --fasteners`, both layouts, every
pair of placed parts (OCC boolean on each pair whose boxes touch; overlaps
above 0.05 mm³ reported), then every screw and nut against the parts it
passes through. Raw numbers: `interference.json` (2129 s on the CI runner).
`interference_reference.py` repeats the flagged pairs on PR #170's own files
(the lab's Fusion 360 exports and PR #170's purchased-part stand-ins) to show
which overlaps the recreation inherited and which it introduced:
`interference_reference.json`.

The sweep ran before the auger-cap fix below; every other number is
unaffected by it (the cap only touches the auger).

## Part pairs

| Pair | Current (servos below) | Servos above | PR #170 files | What it is |
|---|---|---|---|---|
| Auger × auger cap | 546 mm³, all tilts | 546 mm³, all tilts | 0 with the fix | **Fixed.** The cap's thread groove was half a turn out of phase with the auger's thread as placed. `checks/cap_thread.py` turns the cap in 30° steps: 546 mm³ at 0°, zero from 150° to 210°. `lib.frames.CAP_TURN_DEG = 180` now seats it, and both the recreated and the Fusion cap are clear there. |
| Baseplate × MG996R (each) | **69.0 mm³**, all tilts | none | 69.0 mm³ | Inherited: the same overlap is in the lab's Fusion baseplate with PR #170's servo placement. The servos-above baseplate has no servo posts and no overlap. Check the printed posts against a real servo. |
| Mounting plate × NEMA 11 | 17.2 mm³ | 17.2 mm³ | 1.1 mm³ | Mostly the vendor STEP (the recreation uses the real 11HS18-0674S model, not PR #170's stand-in). Three rigid Ø1 mm lead stubs pierce the plate (3.8 mm³ each), and the body's front face sits 0.5 mm into the plate (4.7 mm³). The real leads are flexible wires, but they leave the motor towards the plate, so route them away from it. |
| Bracket (rear) × NEMA 11 | 6.3 mm³ | 6.3 mm³ | 0 | The fourth vendor lead stub, into the rear bracket. Same note on lead routing. |
| Stepper pinion × NEMA 11 shaft | 0.64 mm³ | 0.64 mm³ | 0.66 mm³ | Intended: the pinion's D-bore is a press fit on the shaft. |
| Baseplate × tap-collar base | 0.135 mm³ at 0° only | 0.135 mm³ at 0° only | 0.137 mm³ | Intended: the tap-collar base is the hard stop that rests on the baseplate at 0°. |

Nothing else touches at 0, 15, 30 or 45°, in either layout: no gear,
servo, bracket, collar, solenoid or electronics collisions through the tilt
range.

## Fasteners

| Fastener × part | Current | Servos above | Note |
|---|---|---|---|
| Tap-base screw (+) × baseplate | **4.7 mm³ at 0°** | none | The M3 hardware under the tap-collar base hits the current baseplate when the plate rests on its hard stop. The servos-above baseplate has a slot there. On the current design: shorter screw, or a pocket in the baseplate. |
| Tap-base nut (+) × baseplate | **7.3 mm³ at 0°** | none | Same joint. |
| Stepper screws × NEMA 11, solenoid screws × solenoid, servo-pinion screws × servo shaft, wood screws × board | flagged | flagged | Expected: these thread into the part they hold (the check marks them `expected`). |

Every other screw and nut sits in a clearance hole with no overlap.

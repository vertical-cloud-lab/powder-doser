# Adafruit #1142 — Standard-size High-Torque Metal-Gear digital servo

BOM item 16 (default tilt actuator) in ../../vibration-motor-and-solenoid.md

Reproduced verbatim from the Adafruit product page so we don't have to
re-fetch it every time we want to author rough CAD or sanity-check the
5 V rail budget:
<https://www.adafruit.com/product/1142>

```
Power:           4.8 V – 6 V DC max (5 V works well)
Average Speed:   60° in 0.20 s (@ 4.8 V), 60° in 0.16 s (@ 6.0 V)
Weight:          62.41 g
Torque:          @ 4.8 V →  8.5 kg·cm / 120 oz·in
                 @ 6.0 V → 10   kg·cm / 140 oz·in
Size (L × W × H): 40.7 × 19.7 × 42.9 mm
Spline count:    25
```

## Notes for our use

- **Rail**: shares the D24V22F5 5 V buck with the Pi + DRV8871. Adafruit
  rates the slewing surge at "well under 1 A" for this body size, so
  2.5 A continuous from the buck is comfortably enough as long as we
  don't slew while the solenoid taps (firmware should serialize them
  per the operating-mode note in the parent doc).
- **PWM**: Pi hardware-PWM on GPIO12 or GPIO18 (`gpiozero.AngularServo`).
- **Mount**: 25-spline output → metal servo horn from the #1142
  accessory bag → printed cradle (lives in the auger CAD from PR #16).

Adafruit does not publish a STEP file for #1142 in `Adafruit_CAD_Parts`;
the closely-related #1143 ("Micro Servo - High Torque Metal Gear") STEP
in that repo is an OK envelope proxy when you only need a rough box for
clearance checks. For a precise model, build a 40.7 × 19.7 × 42.9 mm
box with the spline boss centered in the standard hobby-servo location.

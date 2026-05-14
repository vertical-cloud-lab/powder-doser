// ================================================================
// Powder Excavator - NEMA 11 stepper pinion  v1
// ================================================================
//
// 12-tooth, module-1 mm spur pinion sized to mate with the 30-tooth
// integrated gear band on cad/auger-geared/archimedes-auger-geared.scad
// (which itself is the geared variant of the Archimedes auger from
// PR #16). The pinion mounts on the 5 mm round output shaft of a
// NEMA 11 bipolar stepper -- specifically the StepperOnline
// 11HS18-0674S that PR #25 selected as the auger drive motor (item 10
// in hardware/vibration-motor-and-solenoid.md).
//
// Drive parameters
// ----------------
//   Pinion teeth          (Z_p) = 12
//   Driven (auger) teeth  (Z_g) = 30
//   Module                (m)   = 1.0 mm
//   Pressure angle        (PA)  = 20 deg
//   Center distance       (C)   = (Z_g + Z_p) * m / 2 = 21.0 mm
//   Gear ratio (reduction)      = Z_g / Z_p = 30 / 12 = 2.5 : 1
//   Backlash allowance          = ~0.15 mm at pitch (printed-gear rule
//                                  of thumb; absorbed by adjustable
//                                  bracket slots, see ./README.md)
//
// At the NEMA 11's native 1.8 deg/full-step:
//   Per auger revolution = 200 * 2.5 = 500 full-steps = 8000 microsteps
//                           at 1/16 microstepping.
//   Per microstep        = 360 / 8000 = 0.045 deg of auger rotation,
//                           i.e. ~6.1 um of arc at the 25 mm OD.
//
// Print:   PLA or PETG, 0.2 mm layers, 0.4 mm nozzle. Print FLAT on
//          the build plate (gear face down) so the teeth come out as
//          full-perimeter walls -- highest dimensional accuracy. 4
//          perimeters, 30% gyroid infill, no supports.
// Render:  Paste into https://openscad.org/demo/ -> F6 (Render)
// Headless:
//   openscad -o stepper-pinion.stl  stepper-pinion.scad
//   openscad -o stepper-pinion.step stepper-pinion.scad
//
// ================================================================

// ----------------------------------------------------------------
// Parameters
// ----------------------------------------------------------------

/* [Gear teeth] */
gear_module      = 1.0;   // mm  (must match archimedes-auger-geared.scad)
pinion_teeth     = 12;
pressure_angle   = 20;    // deg
face_width       = 10;    // mm  (must match archimedes-auger-geared.scad)

/* [NEMA 11 shaft mount] */
// 11HS18-0674S has a 5 mm round output shaft (no D-cut). Bore is
// printed slightly oversize for slip-fit; an M3 setscrew through a
// radial threaded hole in the hub locks the pinion to the shaft.
shaft_d          = 5.0;
shaft_clearance  = 0.20;  // mm radial slip-fit allowance for FDM
hub_d            = 9.0;   // mm hub OD around the bore (above gear face)
hub_h            = 6.0;   // mm hub height ABOVE the gear face
setscrew_d       = 2.5;   // mm M3 pilot (tap M3 after print)
setscrew_z       = 3.0;   // mm height of setscrew axis above gear face

$fn = 96;

// ----------------------------------------------------------------
// Derived gear geometry
// ----------------------------------------------------------------
pinion_pitch_r   = gear_module * pinion_teeth / 2;       // 6.0 mm
pinion_addendum  = gear_module;                           // 1.0 mm
pinion_dedendum  = 1.25 * gear_module;                    // 1.25 mm
pinion_tip_r     = pinion_pitch_r + pinion_addendum;      // 7.0 mm
pinion_root_r    = pinion_pitch_r - pinion_dedendum;      // 4.75 mm
bore_r           = shaft_d / 2 + shaft_clearance;         // 2.70 mm

// Sanity:
//   pinion_root_r (4.75) > bore_r (2.70) by 2.05 mm -> ample wall
//   between the bore and the tooth roots.

// ----------------------------------------------------------------
// Stub-tooth helper - shared with archimedes-auger-geared.scad via
// gear-teeth.scad so the meshing pair cannot drift apart. Linear-
// flank approximation of a 20-deg involute (see gear-teeth.scad
// header for rationale). For Z=12 the analytic root half-angle would
// exceed the half-pitch (360/2Z = 15 deg); spur_gear_2d() clamps to
// the half-pitch in that case, so the tooth roots meet tangentially
// with zero gap, which prints cleanly and is fine for the low-speed
// metering drive.
// ----------------------------------------------------------------

include <gear-teeth.scad>;

// ----------------------------------------------------------------
// Assembly
// ----------------------------------------------------------------
module stepper_pinion() {
    color("#D55B5B", 0.95)
    difference() {
        union() {
            // Toothed gear disc (face_width thick, sitting at z = 0)
            linear_extrude(height = face_width, convexity = 2 * pinion_teeth)
                spur_gear_2d(
                    Z       = pinion_teeth,
                    m       = gear_module,
                    PA      = pressure_angle,
                    root_r  = pinion_root_r,
                    pitch_r = pinion_pitch_r,
                    tip_r   = pinion_tip_r
                );
            // Hub stack ABOVE the gear face for the setscrew. Hub OD
            // (9 mm) is smaller than the root diameter (9.5 mm) so it
            // never collides with a meshing tooth.
            translate([0, 0, face_width])
                cylinder(d = hub_d, h = hub_h);
        }
        // Through-bore for the 5 mm stepper shaft.
        translate([0, 0, -0.1])
            cylinder(r = bore_r, h = face_width + hub_h + 0.2);
        // Radial M3 setscrew pilot, axis through the hub.
        translate([0, 0, face_width + setscrew_z])
            rotate([0, 90, 0])
                cylinder(d = setscrew_d, h = hub_d / 2 + 0.5);
    }
}

stepper_pinion();

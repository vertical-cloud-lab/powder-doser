// ================================================================
// Assembly preview (SHORT alternate): geared auger + pinion + NEMA 11
// ================================================================
// Same view as assembly-preview.scad but uses the 180 mm short
// alternate auger so reviewers can compare overall stack height
// side-by-side.  See assembly-preview.scad for full notes.

include <archimedes-auger-geared-short.scad>;

auger_total_h    = total_height_short;     // 180 mm
auger_gear_z     = gear_center_z_short;    // 83.33 mm

pinion_teeth_assembly = 16;
center_distance       = (gear_teeth + pinion_teeth_assembly)
                          * gear_module / 2;               // 32.0 mm

// NEMA 11 frame (StepperOnline 11HS18-0674S):
nema_frame    = 28.2;
nema_length   = 32.0;
nema_shaft_d  = 5.0;
nema_shaft_l  = 20.0;

motor_front_z = auger_gear_z - gear_face_width / 2;

// Pinion -- imported from the pre-rendered STL.
translate([center_distance, 0, motor_front_z])
    rotate([0, 0, 360 / (2 * pinion_teeth_assembly)])
        color("#D55B5B", 0.95) import("stepper-pinion.stl");

// NEMA 11 dummy body (placeholder geometry, NOT a print part)
module nema11_dummy() {
    color("#444444", 0.85)
    union() {
        translate([center_distance - nema_frame / 2,
                   -nema_frame / 2,
                   motor_front_z - nema_length])
            cube([nema_frame, nema_frame, nema_length]);
        translate([center_distance, 0, motor_front_z])
            cylinder(d = nema_shaft_d, h = nema_shaft_l);
    }
}
nema11_dummy();

// ================================================================
// Assembly preview: geared auger + pinion + NEMA 11 motor body
// ================================================================
//
// Non-printable visualisation requested in the PR review thread:
//
//   "include an assembly drawing or stl file including the auger,
//    the new pinion fitting into it, and the NEMA motor behind it
//    with clearance between it and the auger."
//
// This file places three things in space, all at the design
// dimensions used by the printable parts so any change there shows
// up here automatically:
//
//   1. archimedes-auger-geared() at the origin, axis along +Z.
//   2. stepper-pinion (imported STL) on a parallel axis at
//      x = +center_distance, axially positioned so its gear face
//      lines up with the auger's gear band.
//   3. A simple NEMA 11 dummy body (28.2 x 28.2 x 32 mm frame +
//      shaft stub) BEHIND the pinion, sized from the StepperOnline
//      11HS18-0674S datasheet, so the radial clearance from the
//      auger OD (12.5 mm) to the nearest face of the motor frame
//      can be visually confirmed.
//
// What "clearance" means here
// ---------------------------
//   center_distance C        = 32 mm   (axis-to-axis)
//   auger outer radius       = 12.5 mm
//   NEMA 11 frame half-width = 14.1 mm (28.2 / 2)
//   ---------------------------------
//   radial air gap           = C - 12.5 - 14.1 = 5.4 mm
//
// That 5.4 mm is the gap visible between the auger tube and the
// motor's near face in the iso/top renders.
//
// Render to STL (single solid for sharing) or PNG previews:
//   openscad -o assembly-preview.stl assembly-preview.scad
//   xvfb-run -a openscad -o assembly-preview-iso.png \
//       --imgsize=1100,900 --camera=15,0,90,55,0,30,260 \
//       --colorscheme=Tomorrow assembly-preview.scad
//   xvfb-run -a openscad -o assembly-preview-top.png \
//       --imgsize=900,500 --camera=15,0,83,0,0,0,90 \
//       --projection=ortho --colorscheme=Tomorrow assembly-preview.scad
//
// ================================================================

include <archimedes-auger-geared.scad>;

// --------------------------------------------------------------
// Geometry
// --------------------------------------------------------------
// Pull the height + gear-axial-position from archimedes-auger-geared.scad
// so the preview tracks the printable part automatically.
auger_total_h    = total_height_full;     // 250 mm
auger_gear_z     = gear_center_z_full;    // 83.33 mm

pinion_teeth_assembly = 16;
center_distance       = (gear_teeth + pinion_teeth_assembly)
                          * gear_module / 2;               // 32.0 mm

// NEMA 11 frame (StepperOnline 11HS18-0674S):
//   frame:     28.2 x 28.2 mm square
//   length:    32 mm (varies slightly by part; 11HS18 is a short body)
//   shaft:     Ø5 mm round, ~20 mm protrusion past the front face
nema_frame    = 28.2;
nema_length   = 32.0;
nema_shaft_d  = 5.0;
nema_shaft_l  = 20.0;   // protrusion past front face

// Pinion is printed gear-face-down, hub on top -> when seated on
// the motor shaft (face flush against the motor front face) the
// gear face is at z = motor_front_face_z + 0 and extends
// +face_width up the shaft. Align that face with the bottom of
// the auger gear band so the teeth overlap fully:
//   auger band bottom z = gear_center_z - gear_face_width / 2
motor_front_z = auger_gear_z - gear_face_width / 2;

// --------------------------------------------------------------
// Auger (full-length variant -- the include above already
// instantiates one at the origin via archimedes-auger-geared.scad's
// top-level call, so we don't add a second one here)
// --------------------------------------------------------------

// --------------------------------------------------------------
// Pinion (imported pre-rendered STL so we don't re-mesh here)
// --------------------------------------------------------------
translate([center_distance, 0, motor_front_z])
    rotate([0, 0, 360 / (2 * pinion_teeth_assembly)])
        color("#D55B5B", 0.95) import("stepper-pinion.stl");

// --------------------------------------------------------------
// NEMA 11 dummy body (placeholder geometry, NOT a print part)
// --------------------------------------------------------------
// Frame is centred on the motor axis; its front face is in the
// X-Y plane at z = motor_front_z, and the body extends DOWNWARD
// (-Z) by nema_length. This keeps the motor and the auger's
// dispensing end on the same side, matching the issue sketch.
module nema11_dummy() {
    color("#444444", 0.85)
    union() {
        // Square frame
        translate([center_distance - nema_frame / 2,
                   -nema_frame / 2,
                   motor_front_z - nema_length])
            cube([nema_frame, nema_frame, nema_length]);
        // Shaft stub (already inside the pinion bore; only the part
        // sticking out past the pinion + flanged section is shown)
        translate([center_distance, 0, motor_front_z])
            cylinder(d = nema_shaft_d, h = nema_shaft_l);
    }
}
nema11_dummy();

// --------------------------------------------------------------
// Tiny visual aid: a 5.4 mm "gap indicator" rod between the
// auger OD and the nearest face of the motor frame, at the same
// z as the gear band. Comment out for export-quality renders.
// --------------------------------------------------------------
gap_z = auger_gear_z;
gap_x_start = outer_r;                            // 12.5 mm
gap_x_end   = center_distance - nema_frame / 2;   // 17.9 mm
color("#1AA64A")
    translate([gap_x_start, 0, gap_z])
        rotate([0, 90, 0])
            cylinder(d = 0.6, h = gap_x_end - gap_x_start);

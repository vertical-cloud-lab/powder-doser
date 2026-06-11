// ================================================================
// Mesh preview: auger gear band + NEMA 11 pinion
// ================================================================
// Visual sanity check that the 48/16 pair meshes at the calculated
// 32 mm center distance. Renders a thin slice (gear-band region only)
// of the auger, plus the pinion offset by C = 32 mm in +X. Not a
// printable part -- ./README.md describes how to reproduce. See
// assembly-preview.scad for the full auger + pinion + NEMA 11 dummy
// body assembly view that confirms the motor body clears the auger.

// Pull just the parametric core (no top-level rendering) so this
// preview can render only the slice it cares about.
include <auger-core.scad>;

total_height_full   = 250;
gear_center_z_full  = total_height_full / 3;
pinion_teeth_preview = 16;

// The include above renders the full auger at the origin; we only
// want the gear-band slice for this preview, so override that with
// an intersection.  Use total_height_full / gear_center_z_full from
// the include so this preview tracks any future change to the
// printable variant.
intersection() {
    archimedes_auger_geared(total_height_full, gear_center_z_full);
    translate([-50, -50, gear_center_z_full - gear_face_width])
        cube([100, 100, 2 * gear_face_width]);
}

// Pinion at the meshing center distance, axis parallel, vertically
// aligned with the gear band, rotated to interleave teeth.
center_distance = (gear_teeth + pinion_teeth_preview) * gear_module / 2;  // 32.0 mm
translate([center_distance, 0, gear_center_z_full - gear_face_width / 2])
    rotate([0, 0, 360 / (2 * pinion_teeth_preview)])  // half-tooth offset for clean mesh
        import("stepper-pinion.stl");  // pre-rendered STL

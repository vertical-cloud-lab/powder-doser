// ================================================================
// Mesh preview: auger gear band + NEMA 11 pinion
// ================================================================
// Visual sanity check that the 30/12 pair meshes at the calculated
// 21 mm center distance. Renders a thin slice (gear-band region only)
// of the auger, plus the pinion offset by C = 21 mm in +X. Not a
// printable part -- ./README.md describes how to reproduce.

include <archimedes-auger-geared.scad>;

// Slice the auger to just the gear band region so the mesh is easy
// to see from the top / iso view.
intersection() {
    archimedes_auger_geared();
    translate([-50, -50, gear_center_z - gear_face_width])
        cube([100, 100, 2 * gear_face_width]);
}

// Pinion at the meshing center distance, axis parallel, vertically
// aligned with the gear band, rotated to interleave teeth.
center_distance = (gear_teeth + 12) * gear_module / 2;  // 21.0 mm
translate([center_distance, 0, gear_center_z - gear_face_width / 2])
    rotate([0, 0, 360 / (2 * 12)])  // half-tooth offset for clean mesh
        import("stepper-pinion.stl");  // pre-rendered STL

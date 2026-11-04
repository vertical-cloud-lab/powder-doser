// ================================================================
// Powder Excavator -- Archimedes Auger TEST PIECE  (nozzle v1)
// ================================================================
//
// Short, gearless test print for nozzle variant 1 from
// vertical-cloud-lab/powder-doser issue #48 comment 4513155870:
//
//   (v1) Direct cutoff of the screw, large open funnel below.
//
// Requested by @williamulbz on PR #49 (comment 4566308356) so all
// four nozzle designs can be print-tested side-by-side without
// burning filament on the full 250 mm geared body.
//
// Same inlets and outlets as the full part:
//   * Top cap: 4 radial loading slots + M3 spindle pilot
//   * Bottom: Ø3 mm exit hole
//
// Length: 90 mm (~3.54 in) -- in the 3-4 in band asked for, and
// enough to fit > 3 full helix turns above the funnel.
//
// NO external gear band on test pieces -- spin the spindle by hand
// (or chuck the M3 pilot into a drill) during the bench test.
//
// Render:
//   openscad -o archimedes-auger-test-nozzle1.stl \
//             archimedes-auger-test-nozzle1.scad
// ================================================================

include <nozzle-variants.scad>;

total_h_test    = 90;   // mm  (~3.54 in)
nozzle_variant  = 1;

archimedes_auger_test(
    total_h        = total_h_test,
    nozzle_variant = nozzle_variant
);

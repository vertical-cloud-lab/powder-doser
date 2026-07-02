// ================================================================
// Powder Excavator -- "Storage" Archimedes Auger  TEST PIECE
// ================================================================
//
// Smaller-scale bench-test version of the storage auger, asked for by
// @swcharles on PR #49 (comment 4712371378): "create a smaller scale
// auger with the same stipulations (1/3 auger, 2/3 open space inside
// the cylinder) for testing, similar to the augers created [the
// nozzle test pieces in PR #49 comment 4566308356], just with this
// new version, the 'storage auger.'"
//
// Like the nozzle test pieces it is:
//   * Short -- total height 90 mm (~3.54 in).
//   * Gearless -- no external gear band (spin the M3 pilot by hand or
//     in a low-speed drill for the bench test).
//   * Same inlets / outlets as the full part (25/21 mm tube, top cap
//     with 4 loading slots + M3 pilot, Ø3 mm exit hole, v4 nozzle).
//
// Same storage stipulation as the full part: the Archimedean screw
// occupies only the bottom third (30 mm) of the bore; the top two
// thirds (60 mm) is open loose-powder storage volume.
//
// Render:
//   openscad -o archimedes-auger-storage-test.stl \
//             archimedes-auger-storage-test.scad
// ================================================================

include <storage-auger-core.scad>;

total_h_test = 90;   // mm  (~3.54 in, same as the nozzle test pieces)

archimedes_auger_storage(
    total_h   = total_h_test,
    with_gear = false
);

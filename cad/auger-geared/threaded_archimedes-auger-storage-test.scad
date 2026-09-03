// ================================================================
// Powder Excavator -- THREADED "Storage" Archimedes Auger  TEST PIECE
// ================================================================
//
// Threaded version of `archimedes-auger-storage-test.scad`, asked for
// by @swcharles on PR #49 (comment 4720626775).  This is the smaller
// bench-test piece that "we will then test ... with the cap".
//
// Identical to `archimedes-auger-storage-test.scad` (90 mm, gearless,
// 1/3-screw / 2/3-open storage, same inlets/outlets) EXCEPT that an
// external thread is cut into the TOP INCH of the outer wall.  The
// thread crest is flush with the auger OD and never exceeds it.
//
// Pair with the matching cap `threaded-storage-cap.scad`.
//
// Render:
//   openscad -o threaded_archimedes-auger-storage-test.stl \
//             threaded_archimedes-auger-storage-test.scad
// ================================================================

include <threaded-storage-auger-core.scad>;

total_h_test = 90;   // mm  (~3.54 in, same as the storage test piece)

threaded_archimedes_auger_storage(
    total_h   = total_h_test,
    with_gear = false
);

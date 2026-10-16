// ================================================================
// Powder Excavator -- THREADED "Storage" Archimedes Auger (FULL)
// ================================================================
//
// Threaded version of `archimedes-auger-storage.scad`, asked for by
// @swcharles on PR #49 (comment 4720626775): a hand-operated screw-on
// cap to seal the filling (non-dispensing / top "+") end of the auger.
//
// Identical to `archimedes-auger-storage.scad` (same outer cylinder,
// bore, top cap, v4 nozzle exit, gear band, and 1/3-screw storage
// geometry) EXCEPT that an external thread is cut into the TOP INCH of
// the outer wall.  The thread crest is flush with the auger OD and
// never exceeds it, so existing brackets still slide over the tube.
//
// The matching cap is `threaded-storage-cap.scad`.
//
// Render:
//   openscad -o threaded_archimedes-auger-storage.stl \
//             threaded_archimedes-auger-storage.scad
// ================================================================

include <threaded-storage-auger-core.scad>;

total_height_full  = 250;                     // mm  (same as storage)
gear_center_z_full = total_height_full / 3;   // 83.33 mm from bottom

threaded_archimedes_auger_storage(
    total_h       = total_height_full,
    gear_center_z = gear_center_z_full,
    with_gear     = true
);

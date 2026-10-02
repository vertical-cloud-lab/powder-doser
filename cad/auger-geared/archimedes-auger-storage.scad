// ================================================================
// Powder Excavator -- "Storage" Archimedes Auger  (FULL LENGTH)
// ================================================================
//
// New high-capacity variant asked for by @swcharles on PR #49
// (comment 4712371378): "adjusting the design for more powder storage
// capacity ... remove the top two thirds of the internal screw,
// allowing for a large internal open area to store loose powder ...
// the outer cylinder should be unchanged -- all that changes in this
// design is where the screw starts."
//
// This is the full-length production part.  It keeps the SAME outer
// cylinder, bore, top cap (4 loading slots + M3 spindle pilot),
// bottom exit funnel and external gear band as
// `archimedes-auger-geared.scad`, and uses the now-standard v4 nozzle
// dispensing-end geometry.  The ONLY difference from the geared auger
// is the internal screw: instead of running the full length of the
// bore, the Archimedean screw (central shaft + helical fin) occupies
// only the BOTTOM THIRD of the part.  The top two thirds of the bore
// is an open volume for storing loose powder, which feeds down into
// the screw at the bottom.
//
// The original `archimedes-auger-geared.scad` / `-short.scad` are left
// in place unchanged.
//
// Render:
//   openscad -o archimedes-auger-storage.stl archimedes-auger-storage.scad
//
// PNG previews / cross-section: see ./README.md "Reproducing the
// renders".
// ================================================================

include <storage-auger-core.scad>;

// ----------------------------------------------------------------
// Variant parameters (FULL LENGTH -- outer cylinder unchanged vs the
// geared production auger)
// ----------------------------------------------------------------
total_height_full   = 250;                    // mm  (same as geared)
gear_center_z_full  = total_height_full / 3;  // 83.33 mm from bottom

archimedes_auger_storage(
    total_h       = total_height_full,
    gear_center_z = gear_center_z_full,
    with_gear     = true
);

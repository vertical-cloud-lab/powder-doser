// ================================================================
// Powder Excavator - "Storage" Archimedes Auger CORE
// ================================================================
//
// New auger version asked for by @swcharles on PR #49
// (comment 4712371378):
//
//   "we're adjusting the design for more powder storage capacity.
//    Make a new auger version (leaving the old auger version in the
//    file system) called 'storage auger' utilizing the same (and now
//    standard) v4 auger nozzle type, defined in issue #48 comment
//    4513155870.  However, for this version, remove the top two
//    thirds of the internal screw, allowing for a large internal open
//    area to store loose powder.  To be clear, the outer cylinder
//    should be unchanged -- all that changes in this design is where
//    the screw starts.
//    Also create a smaller scale auger with the same stipulations
//    (1/3 auger, 2/3 open space inside the cylinder) for testing,
//    similar to the augers created [in PR #49 comment 4566308356],
//    just with this new version, the 'storage auger.'"
//
// What this file provides
// -----------------------
// `archimedes_auger_storage(total_h, gear_center_z, with_gear)` --
// the storage variant of the auger.  It is identical to the geared /
// nozzle-test parts EXCEPT for the internal screw:
//
//   * Outer cylinder, bore, top cap (4 loading slots + M3 pilot),
//     bottom exit funnel and -- on the full part -- the external gear
//     band are all UNCHANGED.  They are reused verbatim from
//     auger-core.scad, so the "outer cylinder should be unchanged"
//     requirement is met by construction.
//   * The internal Archimedean screw (central shaft + helical fin)
//     uses the standard v4 nozzle geometry (tapered tip + helix that
//     follows the shaft down to just above the exit hole; see
//     nozzle-variants.scad variant 4) but only occupies the BOTTOM
//     THIRD of the part.  The top two thirds of the bore is left
//     completely open as a loose-powder storage volume.
//
// "Bottom third": the screw runs from the exit end up to
//   screw_top_z = total_h * screw_fraction   (screw_fraction = 1/3)
// and nothing internal exists above that height -- the bore is empty
// from screw_top_z up to the underside of the top cap.
//
// Two top-level files set the parameters and call the module below so
// they cannot drift apart:
//   archimedes-auger-storage.scad        full part   (total_h = 250,
//                                         with_gear = true, gear band)
//   archimedes-auger-storage-test.scad   bench test  (total_h = 90,
//                                         with_gear = false, no gear)
// ================================================================

include <nozzle-variants.scad>;

// Fraction of the total height taken up by the screw, measured from
// the dispensing (bottom) end.  1/3 screw, 2/3 open storage volume.
screw_fraction = 1 / 3;

// ----------------------------------------------------------------
// Storage central shaft -- standard v4 nozzle shaft (conical tip that
// shrinks to a near-point at the exit, then a straight Ø8 shaft) but
// truncated at screw_top_z so the top two thirds of the bore is open.
// ----------------------------------------------------------------
module storage_central_shaft(screw_top_z) {
    // Tapered tip: r1 = taper_tip_bottom_r at z = 0, r2 = shaft_r at
    // z = bottom_cap_h (identical to nozzle variant 4).
    cylinder(r1 = taper_tip_bottom_r, r2 = shaft_r, h = bottom_cap_h);
    // Straight shaft above the cone, up to the top of the screw zone.
    h_above = screw_top_z - bottom_cap_h;
    translate([0, 0, bottom_cap_h])
        cylinder(r = shaft_r, h = h_above);
}

// ----------------------------------------------------------------
// Storage helical fin -- the standard v4 helix (continuous from just
// above the exit, following the tapering shaft) but ending at
// screw_top_z instead of just below the top cap.
// ----------------------------------------------------------------
module storage_helical_fin(screw_top_z) {
    z0 = 0.5;                       // just above the exit-hole plane
    h  = screw_top_z - z0;
    _helix(z0, h, taper_tip_bottom_r);
}

// ================================================================
// Top-level storage-auger assembly module
// ================================================================
//
//   total_h        overall part height (outer cylinder unchanged from
//                  the matching geared / test part).
//   gear_center_z  axial centre of the external gear band (only used
//                  when with_gear = true).
//   with_gear      true on the full production part, false on the
//                  short bench-test piece (matching the gearless
//                  nozzle test pieces from PR #49).

//   with_top_cap   true on the open-but-capped storage parts; false on
//                  the threaded variants, which drop the 4-loading-slot
//                  top cover so the bore is a smooth open cylinder that
//                  the screw-on cap seals instead.

module archimedes_auger_storage(total_h, gear_center_z = 0, with_gear = true, with_top_cap = true) {
    screw_top_z = total_h * screw_fraction;
    color("#5B9BD5", 0.9)
    union() {
        tube_walls(total_h);
        nozzle_bottom_funnel(4);          // v4 standard nozzle outlet
        if (with_top_cap)
            top_cap(total_h);
        storage_central_shaft(screw_top_z);
        storage_helical_fin(screw_top_z);
        if (with_gear)
            gear_band(gear_center_z);
    }
}

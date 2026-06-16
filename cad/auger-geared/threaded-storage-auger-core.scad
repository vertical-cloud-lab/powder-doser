// ================================================================
// Powder Excavator - THREADED "Storage" Archimedes Auger CORE
// ================================================================
//
// New variant asked for by @swcharles on PR #49 (comment 4720626775):
//
//   "for both the storage auger and the test storage auger, make a new
//    version called threaded_[previous name] and add the following:
//    We need a way to securely seal this filling (non-dispensing) end
//    of the auger, and since this will be done by hand, we can have a
//    hand-operated cap.  Add an external thread on the top inch of the
//    auger and create a simple cap with an internal thread.  This will
//    act like a long bottle cap.
//      - Add an external thread to the auger, allowing for the cap to
//        screw on.  Importantly, the threads should not have a wider
//        maximum diameter than the auger's outer diameter, allowing for
//        us to continue to slide brackets on.
//      - Add a cap with a matching internal thread to screw on to the
//        auger.  The threaded portion of each should be about an inch.
//        And chamfer the cap's top edge a little bit because it looks
//        good.  Note that, while the external thread of the auger should
//        not extend past the outer diameter of the auger, it is
//        anticipated that the cap will be larger in diameter than the
//        auger.
//    We will then test the smaller test storage auger with the cap."
//
// What this file provides
// -----------------------
//   threaded_archimedes_auger_storage(total_h, gear_center_z, with_gear)
//       -- the storage auger (from storage-auger-core.scad) with an
//          external thread cut into the TOP INCH of the outer wall.
//   threaded_storage_cap()
//       -- a simple screw-on cap with a matching internal thread and a
//          chamfered top edge.  One cap fits BOTH threaded storage
//          augers (the thread profile is identical on both).
//
// Thread strategy
// ---------------
// The external thread is formed by REDUCING the outer wall to the
// thread *minor* radius over the top inch and adding a single-start
// helical ridge whose crest is FLUSH with the original auger OD.  So
// the maximum diameter of the threaded section equals the auger OD and
// never exceeds it -- brackets that slide over the 25 mm tube still
// pass over the crests.  (The grooves cut inward, the crests stay at
// the original surface.)
//
// The cap is the matching nut: a solid cup with the *same* helical
// screw (grown radially by `thread_clear` for a printable hand fit)
// subtracted from it, so the cap's internal ridges drop into the
// auger's external grooves.  Both male and female use the same pitch
// and handedness, so the fit is correct by construction; only the
// rotational phase differs, which self-aligns as the cap is turned on.
// ================================================================

include <storage-auger-core.scad>;

// ----------------------------------------------------------------
// Thread parameters
// ----------------------------------------------------------------
//   thread_len      axial length of the threaded section (~1 inch).
//   thread_pitch    axial rise per turn (coarse, for easy hand use).
//   thread_depth    radial depth of the thread (crest - root).
//   thread_crest_r  crest (major) radius -- FLUSH with the auger OD so
//                   the thread never exceeds outer_diameter.
//   thread_minor_r  root (minor) radius of the external thread.
//   thread_half_ang angular half-width of the tooth at the core; sets
//                   how much of each pitch the ridge fills.
//   thread_clear    radial/flank clearance added to the cap's internal
//                   thread so it hand-screws onto the auger.
thread_len      = 25.4;            // mm  (~1 inch)
thread_pitch    = 4.0;             // mm/turn
thread_depth    = 1.0;             // mm
thread_crest_r  = outer_r;         // 12.5 mm -> flush with the auger OD
thread_minor_r  = outer_r - thread_depth;  // 11.5 mm
thread_half_ang = 58;              // deg
thread_clear    = 0.35;            // mm  printed-thread hand fit

// 2D tooth cross-section at angle 0 (a triangle from the core out to
// the crest), optionally grown outward by `extra` for clearance.
module thread_tooth_2d(extra = 0) {
    offset(r = extra)
        polygon(points = [
            [thread_minor_r * cos(thread_half_ang),  thread_minor_r * sin(thread_half_ang)],
            [thread_crest_r, 0],
            [thread_minor_r * cos(thread_half_ang), -thread_minor_r * sin(thread_half_ang)]
        ]);
}

// Single-start helical thread ridge, swept from z0 over `len`.
module thread_ridge(z0, len, extra = 0) {
    turns  = len / thread_pitch;
    twist  = 360 * turns;                  // right-handed
    slices = max(80, ceil(len * 6));
    translate([0, 0, z0])
        linear_extrude(height = len, twist = twist, slices = slices, convexity = 8)
            thread_tooth_2d(extra);
}

// Solid male screw (core cylinder + ridge), grown by `extra`.  Used to
// carve the cap's internal thread.
module male_screw_solid(z0, len, extra = 0) {
    translate([0, 0, z0])
        cylinder(r = thread_minor_r + extra, h = len);
    thread_ridge(z0, len, extra);
}

// ----------------------------------------------------------------
// Threaded storage auger
// ----------------------------------------------------------------
module threaded_archimedes_auger_storage(total_h, gear_center_z = 0, with_gear = true) {
    z0 = total_h - thread_len;     // bottom of the threaded section
    union() {
        // Storage auger with the outer shell removed over the thread
        // region (down to the thread minor radius), so the added ridge
        // crest sits flush with -- and never exceeds -- the auger OD.
        difference() {
            archimedes_auger_storage(total_h, gear_center_z, with_gear);
            translate([0, 0, z0 - 0.01])
                difference() {
                    cylinder(r = outer_r + 5, h = thread_len + 0.02);
                    cylinder(r = thread_minor_r, h = thread_len + 0.02);
                }
        }
        // Helical ridge (crest flush with the auger OD).
        color("#5B9BD5", 0.9)
            thread_ridge(z0, thread_len);
    }
}

// ----------------------------------------------------------------
// Screw-on cap (matching internal thread + chamfered top edge)
// ----------------------------------------------------------------
//   cap_wall      radial wall thickness around the thread.
//   cap_top       solid thickness of the closed (sealing) top.
//   cap_gap_above clearance above the engaged threads so the threads
//                 seat before the cap bottoms out on the auger top.
//   cap_chamfer   45-deg chamfer on the top outer edge ("looks good").
module threaded_storage_cap(cap_wall = 3, cap_top = 3, cap_gap_above = 3, cap_chamfer = 1.5) {
    bore_clear_r = thread_crest_r + thread_clear;   // clears the auger crests
    cap_outer_r  = bore_clear_r + cap_wall;         // > auger OD (allowed)
    cavity_h     = thread_len + cap_gap_above;
    cap_h        = cavity_h + cap_top;

    color("#ED7D31", 0.9)
    difference() {
        // Outer body with a chamfered top edge.
        union() {
            cylinder(r = cap_outer_r, h = cap_h - cap_chamfer);
            translate([0, 0, cap_h - cap_chamfer])
                cylinder(r1 = cap_outer_r, r2 = cap_outer_r - cap_chamfer, h = cap_chamfer);
        }
        // Internal thread: subtract the male screw (grown by the fit
        // clearance) over the engagement length, opening from the rim.
        translate([0, 0, -0.01])
            male_screw_solid(0, thread_len + 0.01, extra = thread_clear);
        // Plain clearance counterbore above the threads so the auger's
        // upper crests pass through un-engaged as the cap screws down.
        translate([0, 0, thread_len])
            cylinder(r = bore_clear_r, h = cap_gap_above + 0.01);
    }
}

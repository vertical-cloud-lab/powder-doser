// ================================================================
// Nozzle-variant test pieces -- short gearless augers for testing
// the 4 dispensing-end designs from @swcharles in
// vertical-cloud-lab/powder-doser issue #48 comment 4513155870.
// ================================================================
//
// Asked for by @williamulbz (PR #49 review comment 4566308356):
//
//   "We want to create shorter test designs for each nozzle design
//    mentioned in @swcharles's comments in #48.  These test designs
//    should keep the same overall design with no changes to the
//    inlets and outlets and should have at least 3 full rotations of
//    the inner archimedes screw.  The overall length should be about
//    3-4 inches and does not need the integrated gear to be a part of
//    it.  Create one for each of the 4 nozzle designs and keep the
//    naming conventions in line (1 through 4) with the comments
//    mentioned."
//
// Each of the four top-level files
//   archimedes-auger-test-nozzle1.scad
//   archimedes-auger-test-nozzle2.scad
//   archimedes-auger-test-nozzle3.scad
//   archimedes-auger-test-nozzle4.scad
// just sets `nozzle_variant` and calls `archimedes_auger_test(...)`
// below; all the geometry lives here so the four files cannot drift
// apart.
//
// What stays the SAME across all four variants (per the requirement
// "no changes to the inlets and outlets"):
//
//   * Tube OD = 25 mm, ID = 21 mm (wall_thickness = 2 mm)
//   * Top cap: 6 mm thick, M3 pilot boss for the spindle, 4 radial
//     loading slots (4 mm x 7 mm, on a 6.5 mm radius circle)
//   * Bottom exit hole: Ø3.0 mm (exit_hole_d, from auger-core.scad)
//   * Helical fin: 2 mm thick, 10 mm pitch, same twist law as the
//     production part -- so all four test prints share the same
//     loading geometry and the same hole the powder exits through.
//
// What CHANGES per variant is just the bottom-funnel + shaft-tip +
// helix-extent geometry near the exit hole; see the nozzle_variant
// switch in `archimedes_auger_test` for the per-variant choices.
//
// Test-piece height:
//   total_h_test = 90 mm  ~= 3.54 in  (in the 3-4 in band asked for)
//
// Helix-turn count (each variant has >= 3 full turns -- the minimum
// asked for):
//
//   v1   (helix from z=shaft_bottom_z ~= 3.53 mm to z=84 mm)
//        turns = (84 - 3.53) / 10  ~= 8.05
//   v2   (helix from z=small_funnel_h = 3 mm to z=84 mm)
//        turns = (84 - 3) / 10     ~= 8.10
//   v3   (helix from z=bottom_cap_h = 12 mm to z=84 mm)
//        turns = (84 - 12) / 10    ~= 7.20
//   v4   (helix from z=0.5 mm to z=84 mm, follows the tapered tip)
//        turns = (84 - 0.5) / 10   ~= 8.35
//
// Render:
//   openscad -o archimedes-auger-test-nozzle<N>.stl \
//             archimedes-auger-test-nozzle<N>.scad
// ================================================================

include <auger-core.scad>;

// ----------------------------------------------------------------
// Variant-specific geometry parameters
// ----------------------------------------------------------------
// small_funnel_h     v2 only: axial length of the short funnel that
//                    sits below the straight shaft and tapers down
//                    from the inner wall to the Ø3 mm exit hole.
//                    Picked as 3 mm so the shaft + helix can keep
//                    running practically all the way to the exit.
//
// taper_tip_bottom_r v3/v4 only: tip radius of the cone that
//                    replaces the cylindrical bottom of the shaft.
//                    A tiny non-zero value (0.4 mm) keeps the cone
//                    printable -- a true point would print as a
//                    single jagged spike.  The cone radius equals
//                    the exit-hole radius (Ø3 mm / 2 = 1.5 mm) at
//                    z = bottom_cap_h * (1 - 1.5/4) ~= 7.5 mm, so
//                    by the time the shaft reaches the exit z it is
//                    well clear of the Ø3 mm exit hole.
small_funnel_h        = 3;
taper_tip_bottom_r    = 0.4;

// ----------------------------------------------------------------
// Per-variant bottom funnel (housing)
// ----------------------------------------------------------------
// v1, v3, v4 share the large open cone from PR #16 (bottom_cap_h=12
// mm, going from the Ø3 exit hole up to the inner wall).  v2 uses a
// short, small funnel so the shaft + helix can keep going almost to
// the exit.

module nozzle_bottom_funnel(nozzle_variant) {
    if (nozzle_variant == 2) {
        // Small short funnel: same end-radii as the large one, but
        // compressed into a small_funnel_h axial slice.
        difference() {
            cylinder(r=outer_r, h=small_funnel_h);
            translate([0, 0, -0.1])
                cylinder(
                    r1 = exit_hole_d / 2,
                    r2 = inner_r - 0.5,
                    h  = small_funnel_h + 0.2
                );
        }
    } else {
        // v1 / v3 / v4: standard PR #16 bottom funnel
        bottom_funnel();
    }
}

// ----------------------------------------------------------------
// Per-variant central shaft
// ----------------------------------------------------------------
// v1   -- straight Ø8 shaft starting at shaft_bottom_z (where the
//         cone wall has narrowed to r = shaft_r), so the shaft tip
//         tangentially fuses to the cone with no floating point.
// v2   -- straight Ø8 shaft from small_funnel_h up to the top cap,
//         so the screw runs practically to the exit.
// v3/v4 -- straight Ø8 shaft above bottom_cap_h, plus a CONICAL tip
//         (taper_tip_bottom_r -> shaft_r over 0..bottom_cap_h) that
//         shrinks to a near-point at the exit.  Same shaft geometry
//         in v3 and v4 -- only the helix differs between the two.

module nozzle_central_shaft(total_h, nozzle_variant) {
    if (nozzle_variant == 1) {
        h = total_h - top_cap_height - shaft_bottom_z;
        translate([0, 0, shaft_bottom_z])
            cylinder(r = shaft_r, h = h);
    } else if (nozzle_variant == 2) {
        h = total_h - top_cap_height - small_funnel_h;
        translate([0, 0, small_funnel_h])
            cylinder(r = shaft_r, h = h);
    } else {
        // v3 / v4: tapered tip + straight shaft above
        h_above = total_h - top_cap_height - bottom_cap_h;
        // tapered tip: r1 at z=0, r2 = shaft_r at z=bottom_cap_h
        cylinder(r1 = taper_tip_bottom_r, r2 = shaft_r, h = bottom_cap_h);
        translate([0, 0, bottom_cap_h])
            cylinder(r = shaft_r, h = h_above);
    }
}

// ----------------------------------------------------------------
// Per-variant helical fin
// ----------------------------------------------------------------
// The fin profile and pitch are identical across all four variants;
// only the z-range (and, for v4 where the fin reaches down past the
// cone, the inner-edge radius) varies.
//
// Slice density: 4 slices per mm of helix, with a floor of 120, so
// even the shortest segment renders smoothly without exploding
// OpenSCAD's render time.

module nozzle_helical_fin(total_h, nozzle_variant) {
    if (nozzle_variant == 1) {
        z0 = shaft_bottom_z;
        h  = total_h - top_cap_height - z0;
        _helix(z0, h, shaft_r - fin_inner_sink);
    } else if (nozzle_variant == 2) {
        z0 = small_funnel_h;
        h  = total_h - top_cap_height - z0;
        _helix(z0, h, shaft_r - fin_inner_sink);
    } else if (nozzle_variant == 3) {
        // Helix is cut off cleanly at the top of the tapered tip --
        // the cone region below has no helix.
        z0 = bottom_cap_h;
        h  = total_h - top_cap_height - z0;
        _helix(z0, h, shaft_r - fin_inner_sink);
    } else {
        // v4: helix continues all the way down the cone to near the
        // exit.  Inner edge dropped to taper_tip_bottom_r so the fin
        // always touches the (narrowing) shaft surface; above the
        // cone the fin's inner portion is simply absorbed by the
        // shaft in the union(), which is fine for CGAL.
        z0 = 0.5;  // just above the exit hole plane
        h  = total_h - top_cap_height - z0;
        _helix(z0, h, taper_tip_bottom_r);
    }
}

// Helper: extrude a `fin_thickness`-thick radial blade from
// inner_edge to (inner_r + fin_outer_sink), starting at z=z0 and
// running for `h` mm with a -360 deg / fin_pitch axial twist.
module _helix(z0, h, inner_edge) {
    turns       = h / fin_pitch;
    twist       = -360 * turns;
    slices      = max(120, ceil(h * 4));
    outer_edge  = inner_r + fin_outer_sink;
    fin_radial  = outer_edge - inner_edge;
    translate([0, 0, z0])
        linear_extrude(height = h, twist = twist, slices = slices, convexity = 4)
            translate([inner_edge, -fin_thickness / 2])
                square([fin_radial, fin_thickness]);
}

// ================================================================
// Top-level test-piece assembly  (NO gear band, per the request)
// ================================================================

module archimedes_auger_test(total_h, nozzle_variant) {
    color("#5B9BD5", 0.9)
    union() {
        tube_walls(total_h);
        nozzle_bottom_funnel(nozzle_variant);
        top_cap(total_h);
        nozzle_central_shaft(total_h, nozzle_variant);
        nozzle_helical_fin(total_h, nozzle_variant);
    }
}

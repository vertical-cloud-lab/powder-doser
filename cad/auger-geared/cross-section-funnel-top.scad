// Horizontal cross-section at the funnel/screw seam (z = bottom_cap_h
// = 12 mm).  Renders the lower 14 mm of the auger so the funnel + the
// first turn of the upper fin are both visible, then clips off
// everything above the seam to expose the planar cut.  Use an
// isometric camera looking slightly down to make the seam plane the
// dominant surface.
include <auger-core.scad>;

total_height_full   = 250;
gear_center_z_full  = total_height_full / 3;

intersection() {
    archimedes_auger_geared(total_height_full, gear_center_z_full);
    translate([-30, -30, 0]) cube([60, 60, bottom_cap_h]);
}

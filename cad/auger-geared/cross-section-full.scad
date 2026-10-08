// Cross-section: cuts the auger in half along the X=0 plane so the
// helix and central shaft are clearly visible.  Used only for
// verification renders; not a printable part.
include <auger-core.scad>;
total_height_full   = 250;
gear_center_z_full  = total_height_full / 3;
difference() {
    archimedes_auger_geared(total_height_full, gear_center_z_full);
    translate([-gear_tip_r - 1, -gear_tip_r - 1, -1])
        cube([2 * gear_tip_r + 2, gear_tip_r + 1, total_height_full + 2]);
}

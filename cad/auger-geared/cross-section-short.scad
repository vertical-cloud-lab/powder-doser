// Cross-section of the SHORT alternate -- same purpose as
// cross-section-full.scad but for archimedes-auger-geared-short.scad.
include <auger-core.scad>;
total_height_short   = 180;
gear_center_z_short  = 250 / 3;
difference() {
    archimedes_auger_geared(total_height_short, gear_center_z_short);
    translate([-gear_tip_r - 1, -gear_tip_r - 1, -1])
        cube([2 * gear_tip_r + 2, gear_tip_r + 1, total_height_short + 2]);
}

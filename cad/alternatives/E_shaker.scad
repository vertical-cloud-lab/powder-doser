// =====================================================================
// alternatives/E_shaker.scad — Salt-shaker oscillation (concept E).
// ---------------------------------------------------------------------
// Mounts on the spindle clamp. The cup base has a *patterned multi-hole
// floor* (like a salt shaker) instead of a fine mesh. The gantry shakes
// the cup in X-Y at ~5–20 Hz over the target vial; powder dispenses
// through the holes at a rate set by hole geometry × shake amplitude.
//
// Fully passive (gantry-as-actuator). One-piece print.
// =====================================================================

$fa = 2; $fs = 0.4;

// --- Parameters (mm) -------------------------------------------------
boss_d        = 43;
boss_h        = 14;
boss_flat_w   = 6;
boss_flat_d   = 0.8;
cup_id        = 22;
cup_wall      = 2.0;
cup_h         = 22;
floor_h       = 1.6;
hole_d        = 1.2;
n_rings       = 3;
holes_per_ring = [6, 12, 18];
ring_radii    = [3, 6.5, 9.5];

module e_shaker() {
    difference() {
        union() {
            cylinder(d = cup_id + 2*cup_wall, h = cup_h);
            translate([0, 0, cup_h])
                cylinder(d = boss_d, h = boss_h);
        }
        // wrench flats
        for (sx = [-1, 1])
            translate([sx*(boss_d/2 - boss_flat_d),
                       -boss_flat_w/2, cup_h + 2])
                cube([boss_flat_d + 0.5, boss_flat_w, boss_h - 4]);
        // hollow boss
        translate([0, 0, cup_h - 0.01])
            cylinder(d = cup_id - 4, h = boss_h + 0.1);
        // reservoir
        translate([0, 0, floor_h])
            cylinder(d = cup_id, h = cup_h);
        // hole pattern — concentric rings
        for (r_idx = [0 : n_rings - 1])
            for (i = [0 : holes_per_ring[r_idx] - 1]) {
                ang = 360 * i / holes_per_ring[r_idx];
                translate([ring_radii[r_idx]*cos(ang),
                           ring_radii[r_idx]*sin(ang), -0.1])
                    cylinder(d = hole_d, h = floor_h + 0.2);
            }
        // central hole
        translate([0, 0, -0.1])
            cylinder(d = hole_d, h = floor_h + 0.2);
    }
}

e_shaker();

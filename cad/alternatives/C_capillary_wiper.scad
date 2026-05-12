// =====================================================================
// alternatives/C_capillary_wiper.scad — Capillary dip + fixed wiper
// (concept C: printable mini-SWILE / PowderPicking analogue).
// ---------------------------------------------------------------------
// A spindle-mounted vertical rod ends in a small capillary tip. The
// gantry dips the tip into a powder bed; cohesive fines pack into the
// capillary; a *fixed* printed wiper bar on the bed strikes off any
// excess as the tip retracts. The struck-off plug is then ejected at
// the target by tapping or by a thin printed plunger inside the bore.
// =====================================================================

$fa = 2; $fs = 0.4;

// --- Parameters (mm) -------------------------------------------------
boss_d        = 43;
boss_h        = 14;
boss_flat_w   = 6;
boss_flat_d   = 0.8;
shank_d       = 8.0;
shank_l       = 38;            // length below the clamp
tip_d_outer   = 3.5;            // outer dia of the capillary tip
tip_d_inner   = 1.4;            // bore that actually holds the powder plug
tip_l         = 12;             // capillary length (sets max plug volume)

// fixed wiper (printed companion piece, lives on the bed)
wiper_w       = 30;
wiper_h       = 8;
wiper_t       = 3;
wiper_slot_w  = tip_d_outer + 0.4;   // slot the tip enters
wiper_post_h  = 22;                  // post height of the wiper above bed

module c_pickup_rod() {
    // boss
    translate([0, 0, shank_l])
        difference() {
            cylinder(d = boss_d, h = boss_h);
            // wrench-flats
            for (sx = [-1, 1])
                translate([sx*(boss_d/2 - boss_flat_d),
                           -boss_flat_w/2, 2])
                    cube([boss_flat_d + 0.5, boss_flat_w, boss_h - 4]);
        }
    // shank
    cylinder(d = shank_d, h = shank_l + 0.5);
    // capillary tip (steps down)
    difference() {
        union() {
            translate([0, 0, -tip_l])
                cylinder(d = tip_d_outer, h = tip_l + 0.5);
            // small chamfer step at shank-to-tip junction for printability
            translate([0, 0, -1.0])
                cylinder(d1 = tip_d_outer, d2 = shank_d, h = 1.0);
        }
        // capillary bore
        translate([0, 0, -tip_l - 0.1])
            cylinder(d = tip_d_inner, h = tip_l + shank_l + boss_h + 1);
    }
}

module c_wiper_post() {
    // bed-mounted wiper post that strikes off the excess. Lives on the
    // 3018 bed offset from the powder cup; the gantry dips, lifts,
    // then drags the tip across the slot to wipe.
    translate([0, 60, 0]) {       // offset so it doesn't intersect the rod
        difference() {
            union() {
                translate([-wiper_w/2, -wiper_h/2, 0])
                    cube([wiper_w, wiper_h, wiper_post_h]);
                translate([-wiper_w/2 - 5, -wiper_h/2 - 2, 0])
                    cube([wiper_w + 10, wiper_h + 4, 3]);   // base flange
            }
            // slot the capillary tip drags through
            translate([-wiper_w/2 - 1, -wiper_slot_w/2,
                       wiper_post_h - tip_l + 1])
                cube([wiper_w + 2, wiper_slot_w, tip_l]);
            // M3 mounting holes
            for (sx = [-1, 1])
                translate([sx*(wiper_w/2 + 2), 0, -0.1])
                    cylinder(d = 3.4, h = 4);
        }
    }
}

c_pickup_rod();
c_wiper_post();

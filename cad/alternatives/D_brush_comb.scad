// =====================================================================
// alternatives/D_brush_comb.scad — Brush / swab pickup + fixed comb
// knock-off (concept D).
// ---------------------------------------------------------------------
// A spindle-mounted disc carries a circular array of stiff bristle
// stand-offs (or a printed soft brush head); cohesive powder adheres
// between the bristles. A *fixed* printed comb on the bed strips the
// adhered powder into the receiving vial when the gantry sweeps the
// disc through it.
//
// Bristles are printed as thin pins (PETG / TPU) — at 0.2 mm layer
// height a 0.6 mm pin prints reliably. For a stiffer brush, replace
// the printed pins with cyanoacrylate-glued tufts of bottlebrush
// fibre.
// =====================================================================

$fa = 2; $fs = 0.3;

// --- Parameters (mm) -------------------------------------------------
boss_d        = 43;
boss_h        = 14;
boss_flat_w   = 6;
boss_flat_d   = 0.8;
disc_d        = 28;
disc_t        = 3;
n_bristles    = 24;
bristle_d     = 0.8;
bristle_h     = 6;
bristle_r     = 11;     // radial position of the bristle ring

// fixed comb on the bed
comb_l        = 30;
comb_w        = 8;
comb_h        = 14;
n_teeth       = 12;
tooth_w       = 0.9;
tooth_gap     = 1.2;

module d_brush_head() {
    // boss + disc
    translate([0, 0, disc_t])
        difference() {
            cylinder(d = boss_d, h = boss_h);
            for (sx = [-1, 1])
                translate([sx*(boss_d/2 - boss_flat_d),
                           -boss_flat_w/2, 2])
                    cube([boss_flat_d + 0.5, boss_flat_w, boss_h - 4]);
        }
    cylinder(d = disc_d, h = disc_t);

    // bristle ring
    for (i = [0 : n_bristles - 1])
        rotate([0, 0, 360 * i / n_bristles])
            translate([bristle_r, 0, -bristle_h])
                cylinder(d = bristle_d, h = bristle_h + 0.1);
}

module d_comb() {
    // bed-mounted comb. Sits on the bed offset from the powder bed; the
    // gantry rapids the brush through the comb and bristle-trapped
    // powder is combed off into the vial below.
    translate([0, 50, 0]) {
        difference() {
            translate([-comb_l/2, -comb_w/2, 0])
                cube([comb_l, comb_w, comb_h]);
            // teeth (slots top-side)
            for (i = [0 : n_teeth - 1])
                translate([-comb_l/2 + 2 + i*(tooth_w + tooth_gap),
                           -comb_w/2 - 0.1, comb_h - bristle_h - 0.5])
                    cube([tooth_gap, comb_w + 0.2, bristle_h + 0.6]);
            // M3 mount holes
            for (sx = [-1, 1])
                translate([sx*(comb_l/2 - 3), 0, -0.1])
                    cylinder(d = 3.4, h = comb_h + 0.2);
        }
    }
}

d_brush_head();
d_comb();

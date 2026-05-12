// =====================================================================
// alternatives/F_passive_auger.scad — Passive auger via rack-and-pinion
// against a fixed pin (concept F).
// ---------------------------------------------------------------------
// A spindle-mounted vertical Archimedes auger inside a tube. The
// auger is keyed to a small printed pinion at the top; a *fixed*
// printed rack on the bed engages the pinion when the gantry rapids
// the assembly horizontally. The spindle does not have to rotate —
// linear gantry motion drives auger rotation passively.
//
// Heavily inspired by PR #16's Archimedes auger geometry, simplified
// to fit in a single ~80-line SCAD source.
// =====================================================================

$fa = 2; $fs = 0.4;

// --- Parameters (mm) -------------------------------------------------
boss_d        = 43;
boss_h        = 12;
tube_od       = 16;
tube_id       = 13;
tube_h        = 60;
pinion_d      = 18;
pinion_h      = 4;
n_teeth       = 14;
helix_pitch   = 12;
helix_r       = 5.5;
fin_t         = 1.6;
exit_d        = 2.5;

module f_pinion() {
    difference() {
        cylinder(d = pinion_d, h = pinion_h);
        for (i = [0 : n_teeth - 1])
            rotate([0, 0, 360*i/n_teeth + 360/(2*n_teeth)])
                translate([pinion_d/2 - 0.5, -0.6, -0.1])
                    cube([1.5, 1.2, pinion_h + 0.2]);
    }
}

module f_helix() {
    n_steps = 220;
    helix_h = tube_h - 6;
    union() {
        // central shaft
        cylinder(d = 3, h = helix_h);
        // helical fin built from rotated thin slabs
        for (i = [0 : n_steps - 1]) {
            z   = i * helix_h / n_steps;
            ang = 360 * z / helix_pitch;
            rotate([0, 0, ang])
                translate([0, -fin_t/2, z])
                    cube([helix_r, fin_t, helix_h/n_steps + 0.05]);
        }
    }
}

module f_tube() {
    difference() {
        cylinder(d = tube_od, h = tube_h);
        translate([0, 0, 1])
            cylinder(d = tube_id, h = tube_h + 0.1);
        // exit hole
        translate([0, 0, -0.1])
            cylinder(d = exit_d, h = 1.2);
    }
}

module f_assembly() {
    f_tube();
    translate([0, 0, 3]) f_helix();
    translate([0, 0, tube_h]) f_pinion();
    translate([0, 0, tube_h + pinion_h])
        cylinder(d = boss_d, h = boss_h);
}

f_assembly();

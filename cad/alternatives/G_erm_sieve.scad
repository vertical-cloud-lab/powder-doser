// =====================================================================
// alternatives/G_erm_sieve_body.scad — ERM-augmented sieve cup
// (concept G), self-contained variant of cad/sieve_cup.scad with the
// ERM motor + CR2032 holder pockets always enabled.
// ---------------------------------------------------------------------
// Continuous bounded vibration (10 mm coin ERM on a CR2032) replaces
// the quantized gantry-tap impulse of concept A. Matches the
// vibratory-sieve-chute regime of Besenhard 2015 (mg-scale fills with
// a definable amplitude window).
//
// Geometry derived 1:1 from cad/sieve_cup.scad with
// erm_motor_pocket = true; inlined here so each concept in
// cad/alternatives/ renders independently and the pipeline doesn't
// have to special-case OpenSCAD's `include` variable scoping.
// =====================================================================

$fa = 2; $fs = 0.4;

cup_id = 22; cup_wall = 2.0; cup_h = 22;
floor_h = 2.0; mesh_d = 18; retainer_pkt_d = 32; retainer_pkt_h = 3;
strike_pad_id = 14; strike_pad_od = 20; strike_pad_h = 1.5; cone_h = 3.0;
boss_d = 43; boss_h = 18; boss_flat_w = 6; boss_flat_d = 0.8;

erm_d = 10.4; erm_pkt_h = 3.6; erm_z = 9.0;
cell_w = 21; cell_h = 14; cell_d = 5.5; cell_z = 14.5;

module g_cup() {
    cup_or = cup_id/2 + cup_wall;

    difference() {
        union() {
            cylinder(d = cup_id + 2*cup_wall, h = cup_h);
            cylinder(d = retainer_pkt_d, h = retainer_pkt_h);
            translate([0, 0, -strike_pad_h])
                cylinder(d = strike_pad_od, h = strike_pad_h);
            translate([0, 0, cup_h])
                cylinder(d = boss_d, h = boss_h);
        }
        // wrench-flats
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
        // mesh window
        translate([0, 0, -strike_pad_h - 0.1])
            cylinder(d = mesh_d, h = floor_h + strike_pad_h + 0.2);
        // mesh-disc relief
        cylinder(d = retainer_pkt_d - 2, h = 1.0);
        // anti-bridging cone
        translate([0, 0, floor_h - 0.01])
            cylinder(d1 = mesh_d + 4, d2 = mesh_d, h = cone_h);

        // --- ERM accessory pockets (this is what makes G ≠ A) ----
        // ERM motor pocket on +x face
        translate([cup_or - erm_pkt_h + 0.5, 0, erm_z])
            rotate([0, 90, 0])
                cylinder(d = erm_d, h = erm_pkt_h + 0.5);
        // CR2032 holder pocket on -x face
        translate([-cup_or - 0.5, -cell_w/2, cell_z - cell_h/2])
            cube([cell_d + 0.5, cell_w, cell_h]);
    }
}

g_cup();

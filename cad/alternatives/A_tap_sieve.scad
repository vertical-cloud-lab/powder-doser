// =====================================================================
// alternatives/A_tap_sieve.scad — Tap-driven sieve cup (passive)
// ---------------------------------------------------------------------
// Concept A from docs/alternative-dosing/brainstorm.md.
//
// Mounts on the 3018-Pro V2 spindle clamp; the gantry pecks the cup
// downward against a fixed printed anvil — each impact dislodges a
// near-constant micro-dose through the bottom mesh.
//
// One-piece printable; mesh disc is a separate consumable cut from
// polyester sieve cloth and clamped by a press-fit retainer ring (not
// rendered here; identical to the one in cad/sieve_cup.scad).
// =====================================================================

$fa = 2; $fs = 0.4;

// --- Parameters (mm) -------------------------------------------------
boss_d        = 43;     // 3018-Pro V2 spindle-clamp grip diameter
boss_h        = 14;
boss_flat_w   = 6;
boss_flat_d   = 0.8;
cup_id        = 22;
cup_wall      = 2.0;
cup_h         = 20;
floor_h       = 2.0;
mesh_d        = 16;     // open dispensing window
retainer_pkt_d = 30;
retainer_pkt_h = 3.0;
strike_pad_id = 14;
strike_pad_od = 20;     // matches anvil strike face
strike_pad_h  = 1.5;
cone_h        = 3.0;    // anti-bridging funnel inside the cup

module a_cup() {
    difference() {
        union() {
            // boss
            translate([0, 0, cup_h])
                cylinder(d = boss_d, h = boss_h);
            // cup body
            cylinder(d = cup_id + 2*cup_wall, h = cup_h);
            // base flange / retainer pocket
            cylinder(d = retainer_pkt_d, h = retainer_pkt_h);
            // strike pad
            translate([0, 0, -strike_pad_h])
                cylinder(d = strike_pad_od, h = strike_pad_h);
        }
        // wrench-flats on boss
        for (sx = [-1, 1])
            translate([sx*(boss_d/2 - boss_flat_d), -boss_flat_w/2, cup_h+2])
                cube([boss_flat_d+0.5, boss_flat_w, boss_h-4]);
        // hollow boss
        translate([0, 0, cup_h - 0.01])
            cylinder(d = cup_id - 4, h = boss_h + 0.1);
        // reservoir
        translate([0, 0, floor_h])
            cylinder(d = cup_id, h = cup_h);
        // mesh window (through floor and strike pad)
        translate([0, 0, -strike_pad_h - 0.1])
            cylinder(d = mesh_d, h = floor_h + strike_pad_h + 0.2);
        // mesh-disc relief
        cylinder(d = retainer_pkt_d - 2, h = 1.0);
        // anti-bridging cone
        translate([0, 0, floor_h - 0.01])
            cylinder(d1 = mesh_d + 4, d2 = mesh_d, h = cone_h);
    }
}

a_cup();

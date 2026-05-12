// =====================================================================
// alternatives/H_solenoid_sieve.scad — Solenoid-tapped sieve, closed-
// loop (concept H).
// ---------------------------------------------------------------------
// Concept A's sieve cup, but driven by a 5 V push-pull solenoid
// (10 × 20 mm) clamped against a printed L-bracket alongside the cup.
// A microcontroller (off-board, not modelled) fires the solenoid
// against an external 0.1 mg balance reading until the target mass is
// reached.
//
// What this SCAD *renders* is the printed solenoid bracket clipped
// onto the side of the same cup geometry — the cup itself is
// imported by name from the alternative-A SCAD so the two concepts
// share their cup body and only diverge in actuation.
// =====================================================================

$fa = 2; $fs = 0.4;

// Re-use concept A's cup body
include <A_tap_sieve.scad>;

// --- Solenoid-bracket parameters (mm) --------------------------------
sol_d         = 10.2;          // 10 mm push-pull solenoid + clearance
sol_l         = 22;            // body length
sol_z         = 8;             // height of the solenoid axis above cup base
sol_x_off     = 18;            // x offset of the bracket from cup centre

bracket_t     = 3;
bracket_w     = 16;
bracket_h     = 30;

module h_bracket() {
    translate([sol_x_off, 0, 0]) {
        difference() {
            // L-bracket: vertical post + horizontal foot
            union() {
                translate([-bracket_t/2, -bracket_w/2, 0])
                    cube([bracket_t, bracket_w, bracket_h]);
                translate([-12, -bracket_w/2, 0])
                    cube([24, bracket_w, bracket_t]);
            }
            // solenoid clearance bore (axis along -x toward cup)
            translate([0, 0, sol_z])
                rotate([0, -90, 0])
                    cylinder(d = sol_d, h = sol_l + 1);
            // M3 mount holes through the foot
            for (sx = [-1, 1])
                translate([sx * 9, 0, -0.1])
                    cylinder(d = 3.4, h = bracket_t + 0.2);
        }
    }
}

h_bracket();

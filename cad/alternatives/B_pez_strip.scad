// =====================================================================
// alternatives/B_pez_strip.scad — Pez-style positive-displacement
// chamber strip (concept B).
// ---------------------------------------------------------------------
// A linear cartridge with N small chambers in series. Each is loaded
// once (slot-fill + strike-off) and dispensed by a fixed pawl on the
// bed advancing the strip one pitch under the gantry.
//
// One-piece print. The strip itself is printed; the pin/pawl is on the
// bed (a separate, trivial part — not rendered here). After loading,
// the strip slides under the gantry; the pawl knocks each chamber's
// powder downward through the chamber's exit port.
// =====================================================================

$fa = 2; $fs = 0.4;

// --- Parameters (mm) -------------------------------------------------
n_chambers    = 8;
pitch         = 8;             // chamber-to-chamber spacing along x
chamber_d     = 4.5;           // each chamber inner dia.
chamber_h     = 5.0;           // chamber depth (sets dose volume)
strip_w       = 14;
strip_h       = 7.0;           // strip thickness
exit_d        = 2.0;           // dispense port at chamber bottom
mount_d       = 43;            // clamp boss
mount_h       = 12;
arm_l         = 30;            // arm linking strip to clamp
arm_t         = 4;
ratchet_pitch = pitch;
n_teeth       = n_chambers + 2;

module b_strip() {
    strip_l = n_chambers * pitch + pitch;

    // top mounting boss (clamp grip) + arm bringing strip below
    translate([0, 0, strip_h + arm_t])
        cylinder(d = mount_d, h = mount_h);

    // arm
    translate([-arm_l/2, -strip_w/2, strip_h])
        cube([arm_l, strip_w, arm_t]);

    // chamber strip
    difference() {
        translate([-strip_l/2, -strip_w/2, 0])
            cube([strip_l, strip_w, strip_h]);

        // chambers along x
        for (i = [0 : n_chambers - 1])
            translate([-strip_l/2 + pitch/2 + i*pitch, 0, strip_h - chamber_h + 0.01])
                cylinder(d = chamber_d, h = chamber_h + 0.1);

        // exit ports
        for (i = [0 : n_chambers - 1])
            translate([-strip_l/2 + pitch/2 + i*pitch, 0, -0.1])
                cylinder(d = exit_d, h = strip_h - chamber_h + 0.2);

        // ratchet teeth on the +y edge (sawtooth notches the bed pawl drops into)
        for (i = [0 : n_teeth - 1])
            translate([-strip_l/2 + i*ratchet_pitch + pitch/2,
                       strip_w/2 - 1.2, -0.1])
                rotate([0, 0, 45])
                    cube([1.6, 1.6, strip_h + 0.2]);
    }
}

b_strip();

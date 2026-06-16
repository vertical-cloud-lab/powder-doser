// ================================================================
// Cap-on-auger fit preview + half-cut cross-sections for the threaded
// storage augers (non-printable visualisation).
//
// `part`:
//   "test-cs"    half-cut of the threaded storage TEST auger
//   "full-cs"    half-cut of the threaded storage FULL auger
//   "assembly"   the screw-on cap seated on the test auger, half-cut so
//                the external auger thread nests inside the cap's
//                internal thread (the open store + bottom-third screw
//                are visible below)
//
// Render commands are in ./README.md ("Reproducing the renders").
// ================================================================

include <threaded-storage-auger-core.scad>;

part = "assembly";   // overridden on the command line with -D

total_h_test = 90;
total_h_full = 250;

module half_cut(h_for_box) {
    translate([-40, -0.01, -1])
        cube([80, 40, h_for_box + 40]);
}

if (part == "test-cs") {
    difference() {
        threaded_archimedes_auger_storage(total_h_test, with_gear = false);
        half_cut(total_h_test);
    }
} else if (part == "full-cs") {
    difference() {
        threaded_archimedes_auger_storage(total_h_full, total_h_full / 3, true);
        half_cut(total_h_full);
    }
} else {
    // Assembly: cap seated on the threaded test auger, half-cut.
    z0 = total_h_test - thread_len;
    difference() {
        union() {
            threaded_archimedes_auger_storage(total_h_test, with_gear = false);
            translate([0, 0, z0])
                threaded_storage_cap();
        }
        half_cut(total_h_test + 40);
    }
}

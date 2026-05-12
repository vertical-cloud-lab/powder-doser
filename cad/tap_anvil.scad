// =====================================================================
// tap_anvil.scad
// ---------------------------------------------------------------------
// Bed-mounted anvil for concept A (tap-driven sieve cup) of the
// alternative powder-dosing brainstorm in
// docs/alternative-dosing/brainstorm.md.
//
// The Genmitsu 3018-Pro V2 gantry "pecks" cad/sieve_cup.scad downward
// onto this anvil at a controlled feedrate. Each peck is one tap;
// each tap shakes a roughly-constant micro-dose through the sieve
// mesh into the target vial below. The anvil's only job is to provide
// a hard, repeatable, *fixed* impact surface; the dose receiver (vial)
// sits in the bore that runs through the anvil's centre.
//
// Geometry rationale:
//
//   - Strike face is an annular pad whose OD matches the cup's
//     ``strike_pad_d + 6 mm`` ring (default 20 mm OD), with a clear
//     bore through the middle so the powder-stream from the mesh
//     window passes straight through into the receiving vial.
//   - Four M3 holes on a 30 x 30 mm pattern bolt the anvil to the
//     T-slot bed plate using standard 3018 hold-down clamps.
//   - The strike face is intentionally raised on a short pillar so
//     spilled powder cannot accumulate at the impact line.
//
// Render to STL from the CLI (no GUI required):
//
//     openscad -o cad/tap-anvil.stl cad/tap_anvil.scad
//
// Render an isometric preview PNG:
//
//     openscad -o cad/tap-anvil-iso.png \
//         --imgsize=1100,800 --camera=0,0,8,55,0,25,200 \
//         --colorscheme=Tomorrow cad/tap_anvil.scad
//
// Tested with OpenSCAD 2021.01.
// =====================================================================

// ---------- Parameters ----------------------------------------------
base_x          = 60.0;    // base footprint along x                   [mm]
base_y          = 50.0;    // base footprint along y                   [mm]
base_thick      =  5.0;    // base plate thickness                     [mm]

mount_hole_d    =  3.4;    // M3 clearance                             [mm]
mount_hole_dx   = 30.0;    // hole pitch along x                       [mm]
mount_hole_dy   = 30.0;    // hole pitch along y                       [mm]
counterbore_d   =  6.5;    // M3 cap-screw counterbore diameter        [mm]
counterbore_h   =  3.0;    // counterbore depth                        [mm]

pillar_d        = 28.0;    // pillar OD around the strike face         [mm]
pillar_h        = 12.0;    // height of the pillar above the base      [mm]

strike_face_od  = 20.0;    // strike face OD (matches cup pad)         [mm]
strike_face_id  = 12.0;    // central bore for the dispensed powder    [mm]
strike_face_h   =  2.0;    // raised lip of the strike pad             [mm]

vial_collar_d   = 16.5;    // collar diameter to locate a 15 mm vial   [mm]
vial_collar_h   =  4.0;    // collar depth                             [mm]

// ---------- Render quality ------------------------------------------
$fa = 2;
$fs = 0.4;

// =====================================================================
// Sub-assemblies
// =====================================================================

module base_plate() {
    difference() {
        translate([-base_x / 2, -base_y / 2, 0])
            cube([base_x, base_y, base_thick]);
        // M3 mounting holes with counterbores from the top
        for (sx = [-1, 1]) for (sy = [-1, 1])
            translate([sx * mount_hole_dx / 2,
                       sy * mount_hole_dy / 2, -0.1]) {
                cylinder(d = mount_hole_d, h = base_thick + 0.2);
                translate([0, 0, base_thick - counterbore_h + 0.1])
                    cylinder(d = counterbore_d,
                             h = counterbore_h + 0.2);
            }
        // central vial bore
        translate([0, 0, -0.1])
            cylinder(d = vial_collar_d, h = vial_collar_h + 0.1);
        translate([0, 0, vial_collar_h - 0.01])
            cylinder(d = strike_face_id,
                     h = base_thick - vial_collar_h + 0.2);
    }
}

module pillar() {
    difference() {
        translate([0, 0, base_thick])
            cylinder(d = pillar_d, h = pillar_h);
        translate([0, 0, base_thick - 0.01])
            cylinder(d = strike_face_id, h = pillar_h + 0.1);
    }
}

module strike_pad() {
    difference() {
        translate([0, 0, base_thick + pillar_h])
            cylinder(d = strike_face_od, h = strike_face_h);
        translate([0, 0, base_thick + pillar_h - 0.1])
            cylinder(d = strike_face_id,
                     h = strike_face_h + 0.2);
    }
}

// =====================================================================
// Top-level assembly
// =====================================================================

module tap_anvil() {
    color([0.55, 0.65, 0.85]) base_plate();
    color([0.85, 0.85, 0.88]) pillar();
    color([0.95, 0.55, 0.45]) strike_pad();
}

tap_anvil();

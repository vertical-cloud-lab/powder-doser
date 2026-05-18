// ================================================================
// Powder Excavator — Auger Clamp Bracket  v1
// ================================================================
//
// Split shaft-collar-with-mounting-plate bracket sketched in the
// design issue. Two of these clamp the v5 Archimedes auger
// (cad/auger/archimedes-auger.scad, OD = 25 mm) to a flat chassis
// rail with print-friendly tolerance.
//
// Geometry (per the hand sketch):
//   - Bore ID = auger OD + 0.8 mm diametral clearance (loose slip
//     fit; the M3 pinch bolt compresses the 2 mm slit to take up
//     the slack and grip the auger).
//   - 4 mm ring wall, 10 mm width along the auger axis.
//   - 2 mm slit at top with twin ears + horizontal M3 through-hole
//     for the pinch bolt.
//   - Mounting plate tangent to the bottom of the ring with hull()
//     fillets on both flanks ("smooth transition" callout in the
//     sketch).
//   - Two M3 mounting holes through the plate; the flat bottom face
//     is the print-on face (marked "print on this face" in the
//     sketch), so no overhang supports are needed.
//
// Print: PLA or PETG, 0.2 mm layers, 0.4 mm nozzle, 3 perimeters,
//        25 % gyroid infill. Print bottom-face-down (default
//        orientation in this file), no supports required.
//
// Render: openscad.org/demo → F6, or:
//   bash cad/auger-bracket/render.sh
//
// ================================================================

/* [Auger Fit] */
auger_od        = 25.0;   // mm — must match cad/auger/archimedes-auger.scad outer_diameter
bore_clearance  = 0.8;    // mm — diametral clearance (loose slip fit)

/* [Ring] */
ring_wall       = 4.0;    // mm — radial wall around the bore
ring_width      = 10.0;   // mm — extent along the auger axis (matches sketch "10 mm")

/* [Clamp Slit + Pinch Bolt] */
slit_width      = 2.0;    // mm — gap between the two clamp halves
ear_height      = 6.0;    // mm — how far the ears stick above the ring OD
ear_thickness   = 6.0;    // mm — fore/aft thickness of each ear (along auger axis is ring_width)
pinch_bolt_d    = 3.4;    // mm — M3 clearance hole (loose, so the bolt slides freely)
pinch_nut_af    = 5.5;    // mm — M3 hex nut across-flats
pinch_nut_t     = 2.4;    // mm — M3 nut thickness
pinch_head_d    = 6.2;    // mm — M3 socket-cap head pocket OD

/* [Mounting Plate] */
plate_width     = 50.0;   // mm — along the auger axis direction... no, perpendicular: see below
plate_length    = 50.0;   // mm — perpendicular to the auger axis (wider than the ring for the mount holes)
plate_thickness = 4.0;    // mm — plate is 4 mm thick (same as ring wall — looks balanced and prints flat)
mount_hole_d    = 3.4;    // mm — M3 clearance for mounting screws
mount_hole_spacing = 36.0;// mm — between the two mounting holes, centred on the ring
mount_hole_inset   = 5.5; // mm — from the long edge of the plate (clears an M3 washer)

/* [Cosmetic Fillets] */
fillet_r        = 3.0;    // mm — hull() blob radius at the smooth ring→plate transition

// ================================================================
// Derived — do not edit
// ================================================================
bore_d          = auger_od + bore_clearance;
bore_r          = bore_d / 2;
ring_or         = bore_r + ring_wall;
ear_outer_x     = slit_width / 2 + ear_thickness;
ear_top_z       = ring_or + ear_height;
pinch_bolt_z    = ring_or + ear_height / 2;   // mid-height of the ear

$fn = 96;

// ================================================================
// Modules
// ================================================================

// Coordinate convention:
//   - Auger axis runs along Y (so the ring is in the XZ plane,
//     extruded in Y for ring_width).
//   - Plate sits at the bottom (-Z), flat side down on the build
//     plate. X is "across" the plate, Y is along the auger axis.

module ring_2d() {
    difference() {
        circle(r = ring_or);
        circle(r = bore_r);
    }
}

module ears_2d() {
    // Two ear blocks sitting tangent to the top of the ring,
    // separated by the slit. Each ear is ear_thickness wide
    // (X direction) and ear_height tall (above the ring OD).
    // They overlap the ring by 0.5 mm so the union is manifold.
    overlap = 0.5;
    for (sx = [-1, 1])
        translate([sx * (slit_width / 2 + ear_thickness / 2),
                   ring_or + ear_height / 2 - overlap])
            square([ear_thickness, ear_height + overlap], center = true);
}

module slit_2d() {
    // Vertical slit from just above the bore to past the top of
    // the ears. Width = slit_width.
    h = ear_top_z + 1;
    translate([0, bore_r - 0.01])
        square([slit_width, h - bore_r + 1], center = false)
            ;  // (will be re-expressed below to be centred on X=0)
}

module slit_cut_2d() {
    // Centred-on-X slit that opens the ring at the top and runs
    // through the ears.
    h = ear_top_z - bore_r + 1.5;
    translate([-slit_width / 2, bore_r])
        square([slit_width, h]);
}

module bracket_profile_2d() {
    // 2D profile in the XZ plane (auger axis = Y, into the page).
    difference() {
        union() {
            ring_2d();
            ears_2d();
            // Tangent stub down to the plate so the hull() smoothing
            // step has a continuous surface to blend.
            translate([-ring_or, -ring_or - 0.01])
                square([2 * ring_or, ring_or + 0.01]);
        }
        slit_cut_2d();
    }
}

// Plate footprint (XY plane), centred on the origin in X and Y.
module plate_2d() {
    square([plate_length, plate_width], center = true);
}

// The smooth ring→plate transition is built in 3D with hull() of:
//   - the lower half of the ring (extruded along Y), and
//   - a thin slab that is the top face of the plate.
// hull() then fills the space tangentially. fillet_r controls how
// much the ring's lower flank is shrunk before the hull, so that
// the blend is concave instead of a sharp tangent meet.
module smooth_transition() {
    // Lower-half-ring "anchor" for the hull. We extrude a half-disc
    // of OD = 2*ring_or sitting at the ring's lower flank, but
    // centred at z = -fillet_r so the hull has somewhere to grow
    // sideways from.
    hull() {
        // Anchor 1: full-width ring-OD half disc at z just below
        // the ring centre.
        translate([0, 0, -fillet_r * 0.4])
            rotate([90, 0, 0])
                linear_extrude(height = ring_width, center = true)
                    intersection() {
                        circle(r = ring_or);
                        translate([-ring_or, -ring_or])
                            square([2 * ring_or, ring_or]);
                    }
        // Anchor 2: top face of the plate.
        translate([0, 0, -plate_thickness])
            linear_extrude(height = 0.01)
                plate_2d();
    }
}

module mounting_plate() {
    difference() {
        translate([0, 0, -plate_thickness])
            linear_extrude(height = plate_thickness)
                plate_2d();
        // Two M3 mounting clearance holes, on the long axis of the
        // plate, symmetric about the ring.
        for (sx = [-1, 1])
            translate([sx * mount_hole_spacing / 2, 0, -plate_thickness - 0.1])
                cylinder(d = mount_hole_d, h = plate_thickness + 0.2);
    }
}

module pinch_bolt_cut() {
    // Horizontal M3 through-hole across both ears (along X), at
    // the ears' mid-height. One end is counterbored for an M3 hex
    // nut (captive); the other end is counterbored for an M3
    // socket-cap head.
    bolt_len = 2 * ear_outer_x + 1;
    translate([-(ear_outer_x + 0.5), ring_width / 2, pinch_bolt_z])
        rotate([0, 90, 0])
            cylinder(d = pinch_bolt_d, h = bolt_len);
    // Hex nut pocket on the -X side: a hexagonal prism cut into the
    // outer face of the left ear.
    nut_depth = pinch_nut_t + 0.2;
    translate([-ear_outer_x - 0.01, ring_width / 2, pinch_bolt_z])
        rotate([0, 90, 0])
            cylinder(r = pinch_nut_af / sqrt(3) * 2 / 2,  // af → across-corners radius
                     h = nut_depth, $fn = 6);
    // Socket-cap head pocket on the +X side.
    head_depth = 3.0;
    translate([ear_outer_x - head_depth + 0.01, ring_width / 2, pinch_bolt_z])
        rotate([0, 90, 0])
            cylinder(d = pinch_head_d, h = head_depth + 0.01);
}

module auger_bracket() {
    color("#7FB069", 0.95)
    difference() {
        union() {
            // Ring + ears, extruded along the auger axis (Y).
            rotate([90, 0, 0])
                translate([0, 0, -ring_width / 2])
                    linear_extrude(height = ring_width)
                        bracket_profile_2d();
            // Mounting plate.
            mounting_plate();
            // Smooth ring→plate blend on both flanks.
            smooth_transition();
        }
        // M3 pinch-bolt through-hole + nut/head pockets.
        pinch_bolt_cut();
        // Re-cut the bore (the hull() blend would otherwise close
        // a chord across it from below).
        rotate([90, 0, 0])
            translate([0, 0, -ring_width / 2 - 0.1])
                linear_extrude(height = ring_width + 0.2)
                    circle(r = bore_r);
        // Re-cut the mounting-plate clearance holes (in case the
        // hull blend grew over them — it won't with default
        // parameters, but stays robust if the plate is shrunk).
        for (sx = [-1, 1])
            translate([sx * mount_hole_spacing / 2, 0, -plate_thickness - 0.1])
                cylinder(d = mount_hole_d, h = plate_thickness + 0.2);
        // Re-cut the slit so the hull-derived smooth_transition
        // doesn't seal the gap between the two clamp halves.
        translate([-slit_width / 2, -ring_width / 2 - 0.1, bore_r])
            cube([slit_width, ring_width + 0.2, ear_top_z - bore_r + 1]);
    }
}

auger_bracket();

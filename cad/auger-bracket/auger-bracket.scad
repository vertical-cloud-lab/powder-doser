// ================================================================
// Powder Excavator — Auger Clamp Bracket  v2
// ================================================================
//
// Split shaft-collar-with-mounting-plate bracket sketched in the
// design issue. Holds close to the hand drawing:
//
//   - Ring + ears + plate are a SINGLE 2D profile in the XZ plane
//     (front view), then linear_extrude'd along the auger axis (Y)
//     for ring_width. The whole part is one uniform-width piece —
//     no pyramidal hull blends.
//   - "Smooth transition" callouts on the sketch are concave fillets
//     where each side of the ring meets the top face of the plate;
//     implemented with offset(r) offset(-r) on the merged 2D profile.
//   - The auger bore (Y), the M3 pinch bolt through the ears (X),
//     and the two M3 plate mount holes (Z) are cut after extrusion.
//   - Bottom face of the plate is the print-on face (flat, no
//     supports needed).
//
// Sized to clamp the v5 Archimedes auger from cad/auger/
// (OD = 25 mm) with print-friendly tolerance.
//
// Render / slice:
//   xvfb-run -a openscad -o auger-bracket.stl auger-bracket.scad
//
// ================================================================

/* [Auger Fit] */
auger_od           = 25.0;   // mm — must match cad/auger/archimedes-auger.scad
bore_clearance     = 0.8;    // mm — diametral clearance (loose slip fit)

/* [Ring] */
ring_wall          = 4.0;    // mm — radial wall around the bore
ring_width         = 10.0;   // mm — extent along the auger axis

/* [Clamp Slit + Pinch Bolt] */
slit_width         = 2.0;    // mm — gap between the two clamp halves
ear_height         = 6.0;    // mm — ear height above the ring OD
ear_thickness      = 6.0;    // mm — ear thickness (each side of slit, in X)
pinch_bolt_d       = 3.4;    // mm — M3 clearance hole

/* [Mounting Plate] */
plate_length       = 50.0;   // mm — plate dimension in X (across)
plate_thickness    = 4.0;    // mm — plate dimension in Z (thickness)
mount_hole_d       = 3.4;    // mm — M3 clearance
mount_hole_spacing = 38.0;   // mm — between the two mount holes

// ================================================================
// Derived
// ================================================================
bore_d   = auger_od + bore_clearance;
bore_r   = bore_d / 2;
ring_or  = bore_r + ring_wall;
ear_top  = ring_or + ear_height;

$fn = 96;

// ================================================================
// 2D profile (XZ plane — front view of the bracket)
//   X = horizontal, Z = vertical, ring centred at origin,
//   plate sits below the ring with its top face at z = -ring_or
// ================================================================

// Lower-half disc of the ring OD: used as one anchor for the
// tangent hull() that creates the "smooth transition" flanks.
module lower_half_ring_2d() {
    intersection() {
        circle(r = ring_or);
        translate([-ring_or, -ring_or])
            square([2 * ring_or, ring_or]);
    }
}

// Mounting plate rectangle: top face tangent to the ring OD.
// A tiny epsilon overlap into the ring keeps the merged 2D outline
// manifold (single-point tangent contact would otherwise produce a
// non-closed mesh after extrusion).
module plate_2d() {
    eps = 0.05;
    translate([0, -ring_or - plate_thickness / 2 + eps])
        square([plate_length, plate_thickness], center = true);
}

// Two ears at the top of the ring, flanking the slit. Sunk slightly
// into the ring so the union is fully connected (otherwise the ear
// inner-bottom corner floats above the ring's curved top surface).
module ears_2d() {
    sink = 2.0;
    for (sx = [-1, 1])
        translate([sx * (slit_width / 2 + ear_thickness / 2),
                   ring_or + ear_height / 2 - sink])
            square([ear_thickness, ear_height], center = true);
}

module bracket_profile_2d() {
    difference() {
        union() {
            // Ring (full disc — bore is cut at the end).
            circle(r = ring_or);
            // Ears.
            ears_2d();
            // Plate.
            plate_2d();
            // "Smooth transition" flanks: hull() of the lower half
            // of the ring OD and the plate rectangle. This produces
            // tangent wings on each flank that blend the ring into
            // the plate, exactly as drawn on the sketch.
            hull() {
                lower_half_ring_2d();
                plate_2d();
            }
        }
        // Clamp slit, cut from inside the bore through both ears
        // (start slightly inside the bore to avoid a tangent edge
        // with the bore cut).
        translate([-slit_width / 2, bore_r - 1])
            square([slit_width, ear_top - bore_r + 2]);
        // Bore.
        circle(r = bore_r);
    }
}

// ================================================================
// 3D part
// ================================================================
module auger_bracket() {
    color("#7FB069")
    difference() {
        // Single uniform extrusion along the auger axis (Y).
        rotate([90, 0, 0])
            translate([0, 0, -ring_width / 2])
                linear_extrude(height = ring_width)
                    bracket_profile_2d();

        // Pinch-bolt hole: horizontal through both ears at ear mid-
        // height, oriented along X. Centred along Y on the bracket.
        translate([-(ear_thickness + slit_width / 2 + 1),
                   0,
                   ring_or + ear_height / 2])
            rotate([0, 90, 0])
                cylinder(d = pinch_bolt_d,
                         h = 2 * (ear_thickness + slit_width / 2) + 2);

        // Two M3 mounting clearance holes through the plate (Z axis).
        for (sx = [-1, 1])
            translate([sx * mount_hole_spacing / 2,
                       0,
                       -ring_or - plate_thickness - 0.1])
                cylinder(d = mount_hole_d, h = plate_thickness + 0.2);
    }
}

auger_bracket();

// ================================================================
// Powder Excavator - Geared Archimedes Auger CORE  v3
// ================================================================
//
// Shared parametric geometry for the geared auger.  Both
// `archimedes-auger-geared.scad`        (full-length, total_h = 250)
// and
// `archimedes-auger-geared-short.scad`  (alternate, total_h = 180)
// `include` this file and then call `archimedes_auger_geared(...)`
// with their own height parameters.  Keeping all the geometry in one
// place means the two variants cannot drift apart -- the only thing
// that differs is the body length above the gear band.
//
// History (full chronology in archimedes-auger-geared.scad header):
//   v1 of cad/auger-geared/  Copied PR #16 v5 internals verbatim;
//                            v5 had stripped the helix + central
//                            shaft, so the geared auger was a hollow
//                            cup with no Archimedean lift.  Gear was
//                            also a solid disc, sealing the bore.
//   v2                       Fixed the gear: annular band via
//                            spur_gear_2d(..., inner_r=inner_r); also
//                            resized to Z_g=48 / Z_p=16, C=32 mm so
//                            the NEMA 11 body clears the auger.  Bore
//                            is now open through the band, but the
//                            helix was still missing -- print
//                            confirmed by @williamulbz reveals an
//                            empty tube with no auger surface.
//   v3 (here)                Re-add the central shaft + helical fin
//                            from PR #16's v4.1 era (Ø8 mm shaft,
//                            10 mm pitch, 2 mm fin) -- the geometry
//                            that successfully metered powder before
//                            v5's print test removed it.  Helix is
//                            CONTINUOUS from the funnel up to just
//                            below the top cap, so both the standard
//                            and the shorter variant have an
//                            unbroken Archimedean surface across the
//                            gear band.  See ./README.md "v3"
//                            section for the rationale.
//
// Parameter naming
// ----------------
// Constants that are physical traits of the printed part (wall
// thickness, fin pitch, gear module, etc.) are declared here at
// file scope.  Two values that change between variants -- the total
// length of the part and the axial centre of the gear band -- are
// passed as arguments to `archimedes_auger_geared(total_h,
// gear_center_z)`.
//
// ================================================================

include <gear-teeth.scad>;

// ----------------------------------------------------------------
// Tube / funnel / cap parameters  (identical to PR #16 v4.1/v5)
// ----------------------------------------------------------------
outer_diameter  = 25;    // mm
wall_thickness  = 2;     // mm

m3_pilot_d      = 2.5;
top_cap_height  = 6;
m3_boss_r       = 4;
m3_boss_h       = 6;

exit_hole_d     = 3.0;
bottom_cap_h    = 12;

slot_count      = 4;
slot_width      = 4;
slot_length     = 7;
slot_radius     = 6.5;

inner_d         = outer_diameter - 2 * wall_thickness;
inner_r         = inner_d / 2;       // 10.5 mm
outer_r         = outer_diameter / 2; // 12.5 mm
m3_pilot_depth  = top_cap_height + m3_boss_h;

// ----------------------------------------------------------------
// Inner Archimedean screw parameters (re-introduced in v3)
// ----------------------------------------------------------------
//   shaft_r            radius of the central support shaft (Ø8 mm).
//                      Sits in the centre of the bore; powder is
//                      lifted by the helical fin wrapped around it.
//   shaft_tip_r        radius the shaft tapers down to at the exit
//                      hole (1.5 mm, matching exit_hole_d/2 -- see
//                      "Funnel-region clearance" note below).
//   fin_thickness      radial-cross-section thickness of the helical
//                      fin (2 mm -- a 5x perimeter at 0.4 mm nozzle).
//   fin_pitch          axial rise per 360 deg of helix (10 mm, same
//                      as PR #16 v2.1/v4.1).
//   fin_inner_sink     overlap of the fin inner edge into the shaft
//                      (0.4 mm, keeps the union() CGAL-manifold).
//   fin_outer_sink     overlap of the fin outer edge into the inside
//                      of the tube wall (0.2 mm, same reason).
shaft_r         = 4;
shaft_tip_r     = 0.5;               // 0.5 mm; leaves a 1.0 mm
                                     // annular gap at the exit hole
                                     // (Ø3 mm), so powder can flow
                                     // around the shaft tip.
fin_thickness   = 2;
fin_pitch       = 10;
fin_inner_sink  = 0.4;
fin_outer_sink  = 0.2;

// Funnel-region clearance
// -----------------------
// v3.1 (this revision): the shaft tapers from `shaft_r` at the top of
// the funnel (z = bottom_cap_h) down to `shaft_tip_r` at the exit
// hole (z = 0).  That keeps the "screw continuing down as the auger
// funnels" appearance from v3 while widening the annular gap between
// the shaft and the funnel cone wall.  Worked example at the first
// printable layer above the exit (z ~ 4 mm):
//
//   funnel inner r(z) = exit_hole_d/2 + (inner_r - 0.5 - exit_hole_d/2)*z/bottom_cap_h
//                     = 1.5 + 8.5*z/12
//   shaft    r(z) = shaft_tip_r + (shaft_r - shaft_tip_r)*z/bottom_cap_h
//                 = 0.5 + 3.5*z/12
//   radial gap(z) = 1.0 + 5.0 * z / 12
//
// So at z = 4 mm the gap is ~2.7 mm wide -- up from ~0.26 mm in v3,
// where the shaft was a constant-r cylinder that kissed the cone
// wall at z = 3.53 mm.  At the exit hole (z = 0) the gap is 1.0 mm
// (shaft tip Ø1.0 inside the Ø3.0 exit hole) so the dispensing path
// is open.  See PR #68 comment 4330241789 for the slicer layer-13
// screenshot that motivated this change.
//
// v3.2 (this revision): the helical fin now also continues down
// through the funnel region.  Inside z = 0 .. bottom_cap_h the fin
// is intersected with the (funnel cone interior - shaft frustum)
// annulus, so its inner edge follows the tapered shaft while its
// outer edge follows the tapered funnel cone wall.  The fin's helix
// phase is matched across z = bottom_cap_h so the flight is one
// continuous surface from the exit hole all the way up to the top
// cap.  See PR #68 comment 4330577754 for the request that motivated
// this change ("the screw would continue [to the end], but the
// middle pole would taper").
shaft_bottom_z  = bottom_cap_h;       // = 12 mm; upper (cylindrical)
                                      // fin starts here.  Tapered
                                      // funnel-region fin runs
                                      // z = 0 .. bottom_cap_h below.

// ----------------------------------------------------------------
// External gear-band parameters  (unchanged from v2)
// ----------------------------------------------------------------
gear_module        = 1.0;
gear_teeth         = 48;
pressure_angle     = 20;
gear_face_width    = 10;

gear_pitch_r   = gear_module * gear_teeth / 2;          // 24.0 mm
gear_addendum  = gear_module;                            //  1.0 mm
gear_dedendum  = 1.25 * gear_module;                     //  1.25 mm
gear_tip_r     = gear_pitch_r + gear_addendum;           // 25.0 mm
gear_root_r    = gear_pitch_r - gear_dedendum;           // 22.75 mm

$fn = 96;

// ================================================================
// Modules (parameterised by total_h)
// ================================================================

module tube_walls(total_h) {
    difference() {
        cylinder(r=outer_r, h=total_h);
        translate([0, 0, -0.1])
            cylinder(r=inner_r, h=total_h + 0.2);
    }
}

module bottom_funnel() {
    difference() {
        cylinder(r=outer_r, h=bottom_cap_h);
        translate([0, 0, -0.1])
            cylinder(
                r1 = exit_hole_d / 2,
                r2 = inner_r - 0.5,
                h  = bottom_cap_h + 0.2
            );
    }
}

module top_cap(total_h) {
    difference() {
        union() {
            translate([0, 0, total_h - top_cap_height])
                cylinder(r=outer_r, h=top_cap_height);
            translate([0, 0, total_h - top_cap_height - m3_boss_h])
                cylinder(r=m3_boss_r, h=m3_boss_h);
        }
        translate([0, 0, total_h - m3_pilot_depth - 0.1])
            cylinder(d=m3_pilot_d, h=m3_pilot_depth + 0.2);

        for (i = [0 : slot_count - 1]) {
            angle = i * (360 / slot_count);
            translate([0, 0, total_h - top_cap_height / 2])
            rotate([0, 0, angle])
            translate([slot_radius, 0, 0])
                cube([slot_length, slot_width, top_cap_height + 0.2], center=true);
        }
    }
}

// Central support shaft -- a conical tip in the funnel region
// (z = 0 .. bottom_cap_h, tapering from shaft_tip_r up to shaft_r)
// fused to a cylinder of radius shaft_r above the funnel, running up
// to the underside of the top cap.  The tapered tip keeps a clear
// annular gap to the funnel cone wall everywhere below the fin --
// see the "Funnel-region clearance" comment block above.
module central_shaft(total_h) {
    cyl_h = total_h - top_cap_height - bottom_cap_h;
    // Conical tip following the screw down into the funnel.
    cylinder(r1 = shaft_tip_r, r2 = shaft_r, h = bottom_cap_h);
    // Cylindrical body above the funnel.
    translate([0, 0, bottom_cap_h])
        cylinder(r = shaft_r, h = cyl_h);
}

// Helical fin -- a flat radial blade swept around the shaft with a
// fin_pitch mm axial rise per turn.  Runs CONTINUOUSLY from the
// exit hole (z = 0) up to the underside of the top cap.
//
// Built as two stacked, phase-aligned linear_extrude pieces:
//   1. Funnel region (z = 0 .. bottom_cap_h): a wide twisted blade
//      intersected with the conical annulus between the shaft
//      frustum and the funnel cone wall, so the fin tapers with
//      the funnel.
//   2. Above the funnel (z = bottom_cap_h .. total_h - top_cap_height):
//      constant-radius blade between the shaft cylinder and the tube
//      wall.  Rotated to match the funnel-region fin's exit phase
//      so the helix is continuous across z = bottom_cap_h.
// Inner edge sinks `fin_inner_sink` into the shaft, outer edge sinks
// `fin_outer_sink` into the inside of the tube wall / funnel cone,
// both for CGAL-manifold safety.
module helical_fin(total_h) {
    h_upper      = total_h - top_cap_height - shaft_bottom_z;
    turns_upper  = h_upper / fin_pitch;
    twist_upper  = -360 * turns_upper;
    slices_upper = max(120, ceil(h_upper * 4));
    inner_edge   = shaft_r - fin_inner_sink;   // 3.6 mm
    outer_edge   = inner_r + fin_outer_sink;   // 10.7 mm
    fin_radial   = outer_edge - inner_edge;    // 7.1 mm

    // ---- Funnel-region fin (tapered) -------------------------------
    funnel_h      = bottom_cap_h;
    funnel_turns  = funnel_h / fin_pitch;
    funnel_twist  = -360 * funnel_turns;       // -432 deg over 12 mm
    funnel_slices = max(96, ceil(funnel_h * 8));
    intersection() {
        // Oversized twisted blade -- spans from the axis out past
        // the funnel mouth; the intersection below clips it to the
        // tapered annulus.
        linear_extrude(height = funnel_h, twist = funnel_twist,
                       slices = funnel_slices, convexity = 4)
            translate([0, -fin_thickness / 2])
                square([outer_r, fin_thickness]);
        // Conical annulus: funnel cone interior minus shaft frustum,
        // each grown/shrunk by the manifold sinks so the fin fuses
        // cleanly to the surrounding solids.
        difference() {
            translate([0, 0, -0.05])
                cylinder(
                    r1 = exit_hole_d / 2 + fin_outer_sink,
                    r2 = inner_r - 0.5  + fin_outer_sink,
                    h  = funnel_h + 0.1
                );
            translate([0, 0, -0.1])
                cylinder(
                    r1 = shaft_tip_r - fin_inner_sink,
                    r2 = shaft_r    - fin_inner_sink,
                    h  = funnel_h + 0.2
                );
        }
    }

    // ---- Upper fin (constant radius) -------------------------------
    // Rotated by funnel_twist so its profile at z = shaft_bottom_z
    // is at the same world angle as the funnel-region fin's exit
    // profile -- the helix is continuous across the seam.
    translate([0, 0, shaft_bottom_z])
        rotate([0, 0, funnel_twist])
            linear_extrude(height = h_upper, twist = twist_upper,
                           slices = slices_upper, convexity = 4)
                translate([inner_edge, -fin_thickness / 2])
                    square([fin_radial, fin_thickness]);
}

// External spur-tooth band.  ANNULAR (inner_r passed through to
// spur_gear_2d) so the bore stays open through the band's axial
// slice -- otherwise the gear's root-circle disc would seal the
// bore.  See cad/auger-geared/gear-teeth.scad for the helper.
module spur_gear_band(Z, m, PA, face_w, root_r, pitch_r, tip_r, inner_r_param) {
    linear_extrude(height = face_w, convexity = 2 * Z)
        spur_gear_2d(Z, m, PA, root_r, pitch_r, tip_r, inner_r_param);
}

module gear_band(gear_center_z) {
    translate([0, 0, gear_center_z - gear_face_width / 2])
        spur_gear_band(
            Z              = gear_teeth,
            m              = gear_module,
            PA             = pressure_angle,
            face_w         = gear_face_width,
            root_r         = gear_root_r,
            pitch_r        = gear_pitch_r,
            tip_r          = gear_tip_r,
            inner_r_param  = inner_r
        );
}

// ================================================================
// Top-level assembly module
// ================================================================
//
// Caller picks a length (`total_h`) and a gear-band axial position
// (`gear_center_z`).  The standard variant uses 250 mm / 83.33 mm;
// the short alternate uses 180 mm / 83.33 mm so the gear sits at
// the same distance from the dispensing end and the body above it
// is shortened by 70 mm.

module archimedes_auger_geared(total_h, gear_center_z) {
    color("#5B9BD5", 0.9)
    union() {
        tube_walls(total_h);
        bottom_funnel();
        top_cap(total_h);
        central_shaft(total_h);   // <-- v3: re-added (was stripped in v1/v2)
        helical_fin(total_h);     // <-- v3: re-added (was stripped in v1/v2)
        gear_band(gear_center_z); // <-- v2: annular band, bore stays open
    }
}

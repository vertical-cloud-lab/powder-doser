// ================================================================
// Powder Excavator — Archimedes Auger, Geared variant  v1
// ================================================================
//
// Geared sibling of cad/auger/archimedes-auger.scad (PR #16, v5).
//
// Goal
// ----
// PR #16 mounts the auger on its top M3 spindle and drives it with a
// flexible shaft coupler from a NEMA 11 (#24/#25). Issue #48 asks for
// an alternative drive scheme: an integrated spur-gear band machined
// into the *outside* of the auger about a third of the way up from
// the dispensing (bottom) end, meshing with a pinion on the NEMA 11
// shaft mounted alongside the housing. The gear is *additive only* —
// teeth project outward from the wall like a gear interfering with
// the auger in a 3D modelling program. See ./README.md for the gear
// ratio derivation, mesh distance, and bracket-design implications.
//
// Internal geometry guarantee
// ---------------------------
// Per the source issue: "no part of this new design can alter or
// interfere with the internal design of the auger. The internals
// should be exactly the same -- only its external features should
// change." The bore, conical exit funnel, M3 spindle mount, and four
// top-cap loading slots are all copied byte-for-byte from the v5
// modules in cad/auger/archimedes-auger.scad. The only delta is the
// added gear_band() module, which is union()'d onto the OUTSIDE of
// tube_walls() with its root circle 1.25 mm clear of the auger OD.
//
// The original M3 spindle on top is retained so the same upper
// thrust bearing / cap from PR #16 still works; the gear simply
// transmits torque, while the spindle constrains the shaft axially.
//
// Render:  Paste into https://openscad.org/demo/ -> F6 (Render)
// Export:  File -> Export -> Export as STL
// Headless:
//   openscad -o archimedes-auger-geared.stl  archimedes-auger-geared.scad
//   openscad -o archimedes-auger-geared.step archimedes-auger-geared.scad
//
// ================================================================

// ----------------------------------------------------------------
// Internals (IDENTICAL to cad/auger/archimedes-auger.scad v5)
// ----------------------------------------------------------------

/* [Main Dimensions] */
outer_diameter  = 25;    // mm
total_height    = 250;   // mm
wall_thickness  = 2;     // mm

/* [M3 Mount - Top] */
m3_pilot_d      = 2.5;
top_cap_height  = 6;
m3_boss_r       = 4;
m3_boss_h       = 6;

/* [Powder Exit - Bottom] */
exit_hole_d     = 3.0;
bottom_cap_h    = 12;

/* [Loading Slots - Top Cap] */
slot_count      = 4;
slot_width      = 4;
slot_length     = 7;
slot_radius     = 6.5;

// Derived (identical to v5)
inner_d         = outer_diameter - 2 * wall_thickness;
inner_r         = inner_d / 2;
outer_r         = outer_diameter / 2;
m3_pilot_depth  = top_cap_height + m3_boss_h;

$fn = 96;

// ----------------------------------------------------------------
// Geared variant: external spur-tooth band parameters
// ----------------------------------------------------------------
//
// Module-1 mm, 20 deg pressure-angle stub teeth. The 30/12 pair gives
// a 2.5:1 reduction at a 21 mm center distance (see ./README.md).
//
//   Auger driven gear            Pinion (on NEMA 11 shaft)
//   --------------------         --------------------------
//   teeth (Z)            30        teeth (Z)            12
//   pitch diameter       30 mm     pitch diameter       12 mm
//   tip diameter         32 mm     tip diameter         14 mm
//   root diameter        27.5 mm   root diameter         9.5 mm
//
// The root circle (27.5 mm) sits 1.25 mm OUTSIDE the auger's 25 mm
// OD, so no tooth feature ever crosses into the wall -- the inner
// bore and funnel are untouched.
//
// Axial position: centered 1/3 of total_height up from the dispensing
// (bottom) end -> z = total_height / 3 = 83.33 mm. With a 10 mm face
// width the band spans z = [78.33, 88.33], well clear of both the
// 12 mm bottom funnel and the 6 mm top cap.

gear_module        = 1.0;   // mm
gear_teeth         = 30;
pressure_angle     = 20;    // deg
gear_face_width    = 10;    // mm  (axial height of the tooth band)
gear_center_z      = total_height / 3;  // 1/3 from dispensing end
root_clearance     = 1.25;  // mm  root-circle stand-off from outer_r

// Derived gear geometry (driven gear, Z = gear_teeth)
gear_pitch_r   = gear_module * gear_teeth / 2;          // 15.0 mm
gear_addendum  = gear_module;                            //  1.0 mm
gear_dedendum  = 1.25 * gear_module;                     //  1.25 mm
gear_tip_r     = gear_pitch_r + gear_addendum;           // 16.0 mm
gear_root_r    = gear_pitch_r - gear_dedendum;           // 13.75 mm

// Sanity check: root must clear the auger wall.
//   gear_root_r (13.75) - outer_r (12.5) = 1.25 mm  -> matches root_clearance
// If you change gear_module, gear_teeth, or outer_diameter, re-verify.

// ================================================================
// Modules - tube_walls / bottom_funnel / top_cap are COPIED VERBATIM
// from cad/auger/archimedes-auger.scad v5. Do not modify here; if v5
// changes, mirror the change.
// ================================================================

module tube_walls() {
    difference() {
        cylinder(r=outer_r, h=total_height);
        translate([0, 0, -0.1])
            cylinder(r=inner_r, h=total_height + 0.2);
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

module top_cap() {
    difference() {
        union() {
            translate([0, 0, total_height - top_cap_height])
                cylinder(r=outer_r, h=top_cap_height);
            translate([0, 0, total_height - top_cap_height - m3_boss_h])
                cylinder(r=m3_boss_r, h=m3_boss_h);
        }
        translate([0, 0, total_height - m3_pilot_depth - 0.1])
            cylinder(d=m3_pilot_d, h=m3_pilot_depth + 0.2);

        for (i = [0 : slot_count - 1]) {
            angle = i * (360 / slot_count);
            translate([0, 0, total_height - top_cap_height / 2])
            rotate([0, 0, angle])
            translate([slot_radius, 0, 0])
                cube([slot_length, slot_width, top_cap_height + 0.2], center=true);
        }
    }
}

// ----------------------------------------------------------------
// Stub spur-tooth band (additive, sits on the OUTSIDE of tube_walls)
// ----------------------------------------------------------------
//
// Tooth math (tooth_half_angle, spur_gear_2d) is shared with
// stepper-pinion.scad via gear-teeth.scad so the meshing pair cannot
// drift apart.

include <gear-teeth.scad>;

module spur_gear_band(Z, m, PA, face_w, root_r, pitch_r, tip_r) {
    linear_extrude(height = face_w, convexity = 2 * Z)
        spur_gear_2d(Z, m, PA, root_r, pitch_r, tip_r);
}

module gear_band() {
    // Center the face width on gear_center_z.
    translate([0, 0, gear_center_z - gear_face_width / 2])
        spur_gear_band(
            Z       = gear_teeth,
            m       = gear_module,
            PA      = pressure_angle,
            face_w  = gear_face_width,
            root_r  = gear_root_r,
            pitch_r = gear_pitch_r,
            tip_r   = gear_tip_r
        );
}

// ================================================================
// Assembly
// ================================================================
module archimedes_auger_geared() {
    color("#5B9BD5", 0.9)
    union() {
        tube_walls();
        bottom_funnel();
        top_cap();
        gear_band();   // <-- the only addition vs. cad/auger/ v5
    }
}

archimedes_auger_geared();

// ================================================================
// Cross-section view - uncomment to verify the bore/funnel are
// untouched and the gear teeth sit fully outside the wall.
// ================================================================
// difference() {
//     archimedes_auger_geared();
//     translate([-gear_tip_r - 1, -0.5, -1])
//         cube([2 * gear_tip_r + 2, gear_tip_r + 1, total_height + 2]);
// }

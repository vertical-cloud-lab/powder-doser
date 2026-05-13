// ================================================================
// Powder Excavator — Archimedes Auger Attachment  v5 (hollow tube)
// ================================================================
//
// Rotating dispenser tube — hollow cylinder with conical exit funnel,
// top loading slots, and M3 spindle mount. NO internal helix and NO
// central shaft. Powder is metered by rotation + gravity through the
// on-axis exit hole, with de-bridging from the planned solenoid (#25)
// and coin vibration motor (#31).
//
// Architecture history (so future maintainers don't re-litigate this):
//   v1/v2/v2.1  monolithic union() rotor — outer tube + helical fin.
//   v3/v3.1     experiment: split into fixed shaft + rotating housing
//               around a 0.5 mm radial-clearance journal fit.
//   v4          Reverted to monolithic per PR review.
//   v4.1        Added a central support shaft for the helix to print
//               on (real-auger geometry).
//   v5 (here)   Drop the inner core entirely. The H2D test print on
//               2026-05-13 produced a clean outer tube + funnel + cap
//               but the helix / central shaft inside came out as
//               strings. Per PR #16 review thread: "We were able to
//               print this without the inner core, leave the inner
//               core out, and it's fine to make that 'empty core
//               space' larger to reduce the cantilever effect. I don't
//               want powder getting trapped." So:
//                 - helical_fin() and central_shaft() removed from the
//                   union; the assembly is now just tube_walls() +
//                   bottom_funnel() + top_cap().
//                 - The bottom funnel is lengthened (bottom_cap_h
//                   8 mm → 12 mm) so the cone half-angle from vertical
//                   drops below 45° (atan(8.5/12) ≈ 35°) — self-
//                   supporting under any slicer, no helix-inner-edge
//                   bridge to worry about.
//                 - Inner bore (inner_r ≈ 10.5 mm, ID 21 mm) is left
//                   untouched: it's already wide and smooth, with no
//                   inward features for powder to lodge against, so
//                   nothing can get trapped between auger and tube
//                   (there is no auger).
//                 - Throughput is now governed by the exit-hole
//                   diameter + rotation speed + vibration tap, the
//                   autotrickler-style metering scheme. Capacity ≈
//                   80 cm³ usable.
//
// v4 changes vs v2.1 (capacity scale-up — review thread "we need larger
// capacity here"):
//   - total_height   100 mm → 250 mm  (~10")
//   - outer_diameter  20 mm →  25 mm  (slightly larger bore)
//   - The 250 × 25 mm pillar prints vertically inside the Bambu Lab H2D
//     envelope (350 × 320 × 325 mm); ~75 mm Z headroom remaining.
//   - Usable channel volume ≈ 4.5× v2.1 (~63 cm³ vs ~14 cm³).
//   - Everything else (M3 spindle mount, 2 mm wall, 10 mm pitch, 2 mm
//     fin, 4 sectoral top loading slots, conical funnel + 3 mm CAD exit
//     hole, 0.4 mm fin-into-wall sink + 0.2 mm helix z-overlap that
//     keeps the union() CGAL-manifold) is preserved from v2.1.
//
// Hopper: deliberately NOT modelled. Cohesive powders (xanthan gum,
// flour, etc.) tend to bridge and rathole at a hopper-to-tube
// transition, so this design feeds the auger directly through the four
// top-cap loading slots. The companion solenoid (#25, percussive tap)
// and coin vibration motor (#31, continuous low-amplitude shake) are
// the de-bridging strategy; they will mount to the rotor frame in
// follow-up PRs.
//
// Print:   PLA or PETG, 0.2 mm layers, 0.4 mm nozzle, 1.75 mm filament.
//          Vertical orientation (exit hole DOWN on the build plate).
//          3+ perimeters, 40 % gyroid infill, 4 mm brim (small annular
//          bed contact around the exit hole), supports at 50° (helix
//          inner-edge bridge above the funnel + top-cap annulus bridge).
//          After printing, tap the M3 spindle hole with an M3 hand tap.
// Render:  Paste into https://openscad.org/demo/ → F6 (Render)
// Export:  File → Export → Export as STL
// Headless STL + STEP + slices + checks (CI/local):
//   bash cad/auger/render_print.sh
//
// ================================================================

/* [Main Dimensions] */
outer_diameter  = 25;    // mm — outer cylinder OD (v2.1: 20)
total_height    = 250;   // mm — total length (v2.1: 100)
wall_thickness  = 2;     // mm — outer tube wall

/* [M3 Mount — Top] */
// Boss protrudes below the top cap to give 12 mm of M3 engagement.
// After printing, use an M3 hand tap to cut threads.
// M3 minor diameter = 2.459 mm; pilot at 2.5 mm is correct for tapping.
m3_pilot_d      = 2.5;   // mm — M3 pilot hole (tap after print)
top_cap_height  = 6;     // mm — solid cap at top
m3_boss_r       = 4;     // mm — radius of central boss below cap
m3_boss_h       = 6;     // mm — boss height below cap
// Total M3 engagement = top_cap_height + m3_boss_h = 12 mm

/* [Powder Exit — Bottom] */
// Conical funnel guides powder from outer wall to exit hole.
// 3.0 mm CAD diameter accounts for FDM shrinkage; as-printed on a
// 0.4 mm nozzle ≈ 2.5 mm functional diameter. Open with a 2.5 mm drill
// bit if it comes out tight.
exit_hole_d     = 3.0;   // mm — exit hole diameter (CAD)
bottom_cap_h    = 12;    // mm — height of conical funnel section.
                          // v5: 8 → 12 mm so the cone half-angle from
                          // vertical = atan((inner_r - exit_r)/h) ≈ 35°,
                          // well under any slicer's 50° overhang
                          // threshold — funnel is fully self-supporting
                          // without supports or a brim ring.

/* [Loading Slots — Top Cap] */
// Powder is loaded through these slots from above before the assembly
// is mounted on the spindle. NOT a hopper — see header note on
// bridging/ratholing for cohesive powders.
slot_count      = 4;
slot_width      = 4;     // mm
slot_length     = 7;     // mm (was 6; +1 to track the larger top cap)
slot_radius     = 6.5;   // mm from center (was 5; sits inside the new
                          // inner_r = 10.5 mm at OD=25)

// ================================================================
// Derived — do not edit
// ================================================================
inner_d         = outer_diameter - 2 * wall_thickness;
inner_r         = inner_d / 2;
outer_r         = outer_diameter / 2;
m3_pilot_depth  = top_cap_height + m3_boss_h;

$fn = 64;

// ================================================================
// Modules
// ================================================================

// Outer tube walls — hollow cylinder, full height.
module tube_walls() {
    difference() {
        cylinder(r=outer_r, h=total_height);
        translate([0, 0, -0.1])
            cylinder(r=inner_r, h=total_height + 0.2);
    }
}

// Conical funnel bottom — directs powder to exit hole as rotation slows.
// Inner surface tapers from (inner_r - 0.5) at the top to exit_hole_d/2
// at the base. Outer surface is a flat cylinder matching the tube OD.
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

// Top cap with M3 boss, pilot hole, and powder loading slots.
module top_cap() {
    difference() {
        union() {
            translate([0, 0, total_height - top_cap_height])
                cylinder(r=outer_r, h=top_cap_height);
            translate([0, 0, total_height - top_cap_height - m3_boss_h])
                cylinder(r=m3_boss_r, h=m3_boss_h);
        }
        // M3 pilot hole — full depth through cap + boss.
        translate([0, 0, total_height - m3_pilot_depth - 0.1])
            cylinder(d=m3_pilot_d, h=m3_pilot_depth + 0.2);

        // Powder loading slots (4×, 90° apart). Centered vertically on
        // the top cap so the cube cuts fully through (top_cap_height +
        // 0.2 mm Z overshoot). Earlier versions translated to the cap's
        // underside which left the top face sealed — re-rendered top-down
        // showed only the M3 pilot, no slots, hence "I can't see any
        // openings to load powder".
        for (i = [0 : slot_count - 1]) {
            angle = i * (360 / slot_count);
            translate([0, 0, total_height - top_cap_height / 2])
            rotate([0, 0, angle])
            translate([slot_radius, 0, 0])
                cube([slot_length, slot_width, top_cap_height + 0.2], center=true);
        }
    }
}

// Central support shaft and helical fin removed in v5 — see header.

// ================================================================
// Assembly
// ================================================================
module archimedes_auger() {
    color("#5B9BD5", 0.9)
    union() {
        tube_walls();
        bottom_funnel();
        top_cap();
    }
}

archimedes_auger();

// ================================================================
// Cross-section view — uncomment to inspect interior geometry:
// ================================================================
// difference() {
//     archimedes_auger();
//     translate([-outer_r - 1, -0.5, -1])
//         cube([outer_diameter + 2, outer_r + 1, total_height + 2]);
// }

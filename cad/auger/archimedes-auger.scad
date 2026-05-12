// ================================================================
// Powder Excavator — Archimedes Auger Attachment  v4 (integrated)
// ================================================================
//
// One-piece rotating helical dispenser — auger + tube fused as a single
// rigid rotor, mirroring the autotrickler-style architecture. The whole
// cylinder spins on the stepper-driven spindle; powder is advanced down
// the helical channel and exits the on-axis hole at the bottom.
//
// Architecture history (so future maintainers don't re-litigate this):
//   v1/v2/v2.1  monolithic union() rotor (this architecture).
//   v3/v3.1     experiment: split into fixed shaft + rotating housing
//               around a 0.5 mm radial-clearance journal fit.
//   v4 (here)   REVERTED to monolithic per PR review. Reasons:
//                 - It worked fine for xanthan-gum dispensing in bench
//                   testing.
//                 - One rigid body means one rotating frame: easier to
//                   couple the planned solenoid (tapping, #25) and coin
//                   vibration motor (#31) without wiring across a
//                   journal bearing.
//                 - Mimics autotrickler's tube-with-internal-helix.
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
bottom_cap_h    = 8;     // mm — height of conical funnel section
                          // (was 6 mm in v2.1; +2 mm gives a gentler
                          // taper at the larger 25 mm OD)

/* [Helical Fin] */
pitch           = 10;    // mm per full 360° rotation
// Helix angle at mid-radius ≈ 15° (was 18° at OD=20) → still printable
// without per-layer support; each 0.2 mm layer rotates by 7.2°.
fin_thickness   = 2;     // mm — blade thickness (≥1.6 mm for 0.4 mm nozzle)
fin_inner_r     = 2.0;   // mm — inner edge radius (clear of exit hole & M3)

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
helix_z_start   = bottom_cap_h;
helix_z_end     = total_height - top_cap_height - m3_boss_h;
helix_height    = helix_z_end - helix_z_start;
turns           = helix_height / pitch;
slices_per_turn = 80;
total_slices    = ceil(turns * slices_per_turn);

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

// Helical fin — the Archimedes element.
// Single-start helix from fin_inner_r to (inner_r + fin_wall_overlap).
// The outer edge sinks `fin_wall_overlap` into the tube wall and the
// vertical extent sinks `fin_z_overlap` into the funnel/boss; without
// these overlaps the union() produces zero-thickness coincident
// surfaces, which CGAL splits into ~100 disconnected volumes on STL
// export. With them, admesh reports a single closed manifold.
fin_wall_overlap = 0.4;   // mm
fin_z_overlap    = 0.2;   // mm

module helical_fin() {
    fin_outer = inner_r + fin_wall_overlap;
    fin_width = fin_outer - fin_inner_r;
    z_start   = helix_z_start - fin_z_overlap;
    z_height  = helix_height + 2 * fin_z_overlap;
    translate([0, 0, z_start])
    linear_extrude(
        height    = z_height,
        twist     = turns * 360,
        slices    = total_slices,
        convexity = 10
    ) {
        translate([(fin_inner_r + fin_outer) / 2, 0])
            square([fin_width, fin_thickness], center=true);
    }
}

// ================================================================
// Assembly
// ================================================================
module archimedes_auger() {
    color("#5B9BD5", 0.9)
    union() {
        tube_walls();
        bottom_funnel();
        top_cap();
        helical_fin();
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

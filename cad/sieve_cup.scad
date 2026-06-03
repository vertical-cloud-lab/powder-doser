// =====================================================================
// sieve_cup.scad
// ---------------------------------------------------------------------
// Parametric, monolithic 3D-printable sieve cup for the top-ranked
// alternative powder-dosing concepts in
// docs/alternative-dosing/brainstorm.md:
//
//   Concept A — Tap-driven sieve cup (passive, gantry-as-actuator).
//     Mounts on the Genmitsu 3018-Pro V2 spindle clamp; loaded with
//     cohesive powder; the gantry pecks the cup downward against a
//     fixed printed anvil on the bed (cad/tap_anvil.scad), and each
//     tap "snaps" a near-constant micro-dose through the bottom mesh.
//
//   Concept G — Same cup augmented with a single ~$2 ERM coin
//     vibration motor on a 3 V coin cell. Continuous bounded
//     vibration replaces the quantized gantry-tap impulse and matches
//     the published vibratory-sieve-chute regime (Besenhard et al.
//     2015, Eur. J. Pharm. Biopharm. 94, 264-272).
//
// One parametric body covers BOTH concepts: ``erm_motor_pocket = true``
// adds a side pocket sized for a 10 mm dia. x 3.4 mm coin ERM and a
// CR2032 coin-cell holder; ``false`` renders the fully-passive cup of
// concept A.
//
// The base ring carries a swappable polyester / stainless mesh
// (clamped between the cup and a screw-on retainer) so a single cup
// can be re-tuned for different powders by changing the mesh — the
// "swappable mesh" mitigation called out in the Edison literature
// critique (docs/alternative-dosing/edison_result.md).
//
// Render to STL from the CLI (no GUI required):
//
//     openscad -o cad/sieve-cup.stl \
//         -D 'erm_motor_pocket=false' cad/sieve_cup.scad
//
//     openscad -o cad/sieve-cup-erm.stl \
//         -D 'erm_motor_pocket=true' cad/sieve_cup.scad
//
// Render an isometric preview PNG:
//
//     openscad -o cad/sieve-cup-iso.png \
//         --imgsize=1100,800 --camera=0,0,18,55,0,25,260 \
//         --colorscheme=Tomorrow \
//         -D 'erm_motor_pocket=false' cad/sieve_cup.scad
//
// Tested with OpenSCAD 2021.01.
// =====================================================================

// ---------- Cup body --------------------------------------------------
cup_id            = 24.0;   // inside diameter of the powder reservoir [mm]
cup_wall          =  2.0;   // cup side-wall thickness                  [mm]
cup_height        = 22.0;   // overall cup height (powder column)       [mm]
cup_floor_thick   =  2.0;   // thickness of the mesh-clamping floor ring[mm]
mesh_window_d     = 18.0;   // open dia. through which mesh dispenses   [mm]
mesh_relief_h     =  1.0;   // recess depth that captures the mesh disc [mm]

// ---------- Anti-bridging fillet at the powder-mesh interface --------
// A small chamfered cone inside the cup biases powder toward the centre
// of the mesh window so the periphery does not arch / rathole. This
// is the "design for an adjustable excitation window + re-levelable
// powder bed" build mitigation from Besenhard 2015.
inner_cone_h      =  3.0;   // height of the powder-funneling cone      [mm]

// ---------- Spindle-clamp boss ---------------------------------------
// The Genmitsu 3018-Pro V2 spindle clamp accepts a Ø 52 mm (or, for
// some revisions, Ø 43 / 45 mm) cylindrical shank. A short cylindrical
// boss on top of the cup is the single grip surface; flats let the
// clamp's set-screws bite without crushing the powder reservoir.
boss_d            = 43.0;   // boss outer diameter                      [mm]
boss_h            = 18.0;   // boss height (length the clamp grips)     [mm]
boss_flat_w       =  6.0;   // width of the wrench-flat on the boss     [mm]
boss_flat_depth   =  0.8;   // depth of the wrench-flat                 [mm]

// Vent across the boss top so loading powder doesn't trap air.
boss_vent_d       =  3.0;   // vent hole diameter                       [mm]

// ---------- Mesh-retainer ring (printed; threaded onto cup base) -----
// We don't print the retainer here (it's a separate trivial ring); we
// just expose the female pocket geometry where the mesh is captured.
retainer_pocket_d = 32.0;   // OD pocket for the retainer ring          [mm]
retainer_pocket_h =  3.5;   // depth of the retainer pocket             [mm]

// ---------- Anvil-strike target -------------------------------------
// The base of the cup gets a short standoff annular pad — sized for
// the anvil's printed pad — that takes the impact when the gantry
// pecks the cup against cad/tap_anvil.scad. Annular (not solid) so
// the mesh window stays free; the shock travels through the cup wall
// rather than the mesh disc.
//
// NOTE: ``strike_pad_d`` is the *inner reference* diameter of the
// annulus; the actual strike-pad OD is ``strike_pad_d + 6.0`` (so
// 20 mm with the default 14 mm), matched to the 20 mm anvil strike
// face in cad/tap_anvil.scad (``strike_face_od = 20``).
strike_pad_d      = 14.0;   // inner reference dia. (OD = +6 mm)        [mm]
strike_pad_h      =  1.5;   // strike pad standoff below the floor      [mm]

// ---------- ERM motor pocket (concept G only) ------------------------
// Sized for a stock 10 mm dia. x 3.4 mm coin ERM (e.g. Vybronics
// VC1034B202F, Adafruit 1201). Flat back, two solder pads on one
// face. The pocket is open on the outer face so the ERM can be glued
// in with a dab of cyanoacrylate after wires are routed.
//
// A second pocket alongside it accepts a CR2032 coin-cell holder
// (20 mm dia. x 4 mm, e.g. Keystone 1066) wired through a SPST switch
// glued to a third small flat. No microcontroller is required for the
// "open-loop G" build documented in the brainstorm.
erm_motor_pocket  = false;

erm_pocket_d      = 10.4;   // ERM pocket dia. (with print clearance)   [mm]
erm_pocket_h      =  3.6;   // ERM pocket depth                         [mm]
erm_pocket_z      =  9.0;   // height of pocket centre above cup base   [mm]

cell_pocket_w     = 21.0;   // CR2032 holder pocket width               [mm]
cell_pocket_h     = 14.0;   // CR2032 holder pocket height              [mm]
cell_pocket_d     =  5.5;   // CR2032 holder pocket depth into wall     [mm]
cell_pocket_z     = 14.5;   // height of pocket centre above cup base   [mm]

// Small wire-routing relief from the ERM pocket up to the boss vent so
// the lead wires stay clear of the gantry clamp.
wire_relief_w     =  1.6;   // wire-relief slot width                   [mm]
wire_relief_d     =  1.6;   // wire-relief slot depth into the wall     [mm]

// ---------- Render quality ------------------------------------------
$fa = 2;        // facet angle [deg]
$fs = 0.4;      // facet size  [mm]

// =====================================================================
// Sub-assemblies
// =====================================================================

module cup_body() {
    difference() {
        // outer cup + base flange (mesh-retainer pocket) + strike pad
        union() {
            cylinder(d = cup_id + 2 * cup_wall, h = cup_height);
            cylinder(d = retainer_pocket_d,     h = retainer_pocket_h);
            // strike pad sits below the floor as a continuation of
            // the cup body; declared inside the union so the booleans
            // apply consistently and the part stays a single volume.
            translate([0, 0, -strike_pad_h])
                cylinder(d = strike_pad_d + 6.0, h = strike_pad_h);
        }
        // inner reservoir
        translate([0, 0, cup_floor_thick])
            cylinder(d = cup_id, h = cup_height);
        // mesh window through the floor and strike pad
        translate([0, 0, -strike_pad_h - 0.1])
            cylinder(d = mesh_window_d,
                     h = cup_floor_thick + mesh_relief_h
                         + strike_pad_h + 0.2);
        // recess to capture the mesh disc on the underside (above floor only)
        translate([0, 0, 0])
            cylinder(d = retainer_pocket_d - 2.0,
                     h = mesh_relief_h);
        // powder-funneling cone (anti-bridging) inside the cup
        translate([0, 0, cup_floor_thick - 0.01])
            cylinder(d1 = mesh_window_d + 4.0,
                     d2 = mesh_window_d,
                     h  = inner_cone_h);
    }
}

module spindle_boss() {
    boss_z = cup_height;
    difference() {
        // boss cylinder
        translate([0, 0, boss_z])
            cylinder(d = boss_d, h = boss_h);
        // two opposed wrench-flats for the clamp set-screws
        for (sx = [-1, 1])
            translate([sx * (boss_d / 2 - boss_flat_depth),
                       -boss_flat_w / 2,
                       boss_z + 2.0])
                cube([boss_flat_depth + 0.5,
                      boss_flat_w,
                      boss_h - 4.0]);
        // top vent
        translate([0, 0, boss_z - 0.1])
            cylinder(d = boss_vent_d, h = boss_h + 0.2);
        // open the boss interior so it's hollow over the cup
        translate([0, 0, boss_z - 0.1])
            cylinder(d = cup_id - 4.0, h = boss_h + 0.2);
    }
}

// Concept-G accessory pockets, subtracted from the cup wall at fixed
// angular positions (ERM at +x, coin cell at -x).
module erm_accessories() {
    cup_or = cup_id / 2 + cup_wall;   // cup outer radius
    overshoot = 0.5;                   // poke clearly through the outer wall

    // ERM pocket on the +x face
    translate([cup_or + overshoot - erm_pocket_h, 0, erm_pocket_z])
        rotate([0, 90, 0])
            cylinder(d = erm_pocket_d, h = erm_pocket_h + overshoot);

    // CR2032-holder pocket on the -x face
    translate([-(cup_or + overshoot),
               -cell_pocket_w / 2,
               cell_pocket_z - cell_pocket_h / 2])
        cube([cell_pocket_d + overshoot, cell_pocket_w, cell_pocket_h]);

    // Wire-relief slot from ERM pocket up toward the boss base
    // (overlaps the ERM pocket by 0.5 mm to avoid a coincident edge)
    translate([cup_or + overshoot - wire_relief_d,
               -wire_relief_w / 2,
               erm_pocket_z + erm_pocket_d / 2 - 0.5])
        cube([wire_relief_d + overshoot, wire_relief_w,
              cup_height - erm_pocket_z - erm_pocket_d / 2 - 0.5]);
}

// =====================================================================
// Top-level assembly
// =====================================================================

module sieve_cup() {
    color([0.85, 0.85, 0.88]) {
        difference() {
            union() {
                cup_body();
                spindle_boss();
            }
            if (erm_motor_pocket) erm_accessories();
        }
    }
}

sieve_cup();

// ================================================================
// Powder Excavator -- Geared Archimedes Auger  v3 (SHORT ALTERNATE)
// ================================================================
//
// Alternate, 70 mm shorter sibling of `archimedes-auger-geared.scad`.
// Same internals (bore, funnel, M3 spindle mount, top cap loading
// slots, Ø8 mm central shaft, 10 mm-pitch helical fin) and the same
// external 48-tooth gear band -- only the length of the body
// ABOVE the gear band changes.
//
// Per @williamulbz's comment:
//   "create a separate, alternate, shorter design.  Ensure that the
//    reduction in size comes from reducing the length between the
//    gear and the face of the '+' side (the side with 4 rectangular
//    holes arranged in a cross shape).  Make sure that the auger
//    shape remains continuous within the part.  Specify this
//    alternate part in its file name.  Trim off anywhere from 5-8 cm
//    of the body length."
//
// Sizing
// ------
//   total_height       250 mm  ->  180 mm    (-70 mm = -7.0 cm)
//   gear_center_z       83.33 mm  ->   83.33 mm  (UNCHANGED -- the
//                      gear-to-dispensing-end distance is preserved
//                      so the meshing pinion / motor bracket from
//                      the full-length variant are reused as-is.)
//   gear-to-top-cap    166.67 mm  ->   96.67 mm   (-70 mm trimmed
//                      from the "+" side, exactly as requested.)
//
// The helical fin is generated as a single `linear_extrude` with a
// twist proportional to the shaft's full length, so trimming the
// total height just means fewer turns -- the auger surface remains
// CONTINUOUS from the funnel mouth (z = shaft_bottom_z ~= 3.53 mm)
// up to the underside of the top cap (z = 174 mm in this variant).
// No gap is introduced at the gear band.
//
// Loaded volume vs full-length
// ----------------------------
//   Bore: pi * 10.5^2 * (total_h - bottom_cap_h - top_cap_height)
//   - Full   : pi * 10.5^2 * 232  ~=  80 cm^3 internal
//   - Short  : pi * 10.5^2 * 162  ~=  56 cm^3 internal
//   ~30 % capacity reduction in exchange for 70 mm less z height.
//
// Print
// -----
// Same recipe as the full-length variant, but the shorter pillar is
// less wobble-prone during a vertical print -- 4 mm brim is still
// recommended around the exit hole.
//
// Render
// ------
//   openscad -o archimedes-auger-geared-short.stl \
//            archimedes-auger-geared-short.scad
// ================================================================

include <auger-core.scad>;

// ----------------------------------------------------------------
// Variant parameters (SHORT ALTERNATE)
// ----------------------------------------------------------------
total_height_short   = 180;     // mm  (full-length is 250; -70 mm)
gear_center_z_short  = 250 / 3; // 83.33 mm  (kept at the same axial
                                // position as the full-length
                                // variant so the gear-to-dispensing-
                                // end distance is preserved)

archimedes_auger_geared(
    total_h       = total_height_short,
    gear_center_z = gear_center_z_short
);

// ================================================================
// Cross-section view -- uncomment to verify in OpenSCAD preview
// that the helix is unbroken across the gear band and that the body
// above the gear is 70 mm shorter than the full variant.
// ================================================================
// difference() {
//     archimedes_auger_geared(total_height_short, gear_center_z_short);
//     translate([-gear_tip_r - 1, -0.5, -1])
//         cube([2 * gear_tip_r + 2, gear_tip_r + 1, total_height_short + 2]);
// }

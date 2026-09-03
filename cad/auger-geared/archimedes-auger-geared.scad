// ================================================================
// Powder Excavator -- Geared Archimedes Auger  v3 (FULL LENGTH)
// ================================================================
//
// Geared sibling of cad/auger/archimedes-auger.scad (PR #16). This
// is the full-length 250 mm variant; an alternate, 70 mm shorter
// variant lives next to it as `archimedes-auger-geared-short.scad`.
// All shared geometry -- inner Archimedean screw (central shaft +
// helical fin), outer gear band, top cap with M3 spindle mount,
// conical exit funnel -- is defined parametrically in
// `auger-core.scad` so the two variants cannot drift apart.
//
// ----------------------------------------------------------------
// Architecture history (so future maintainers don't re-litigate it)
// ----------------------------------------------------------------
//   PR #16 v1..v2.1   monolithic union: outer tube + helical fin.
//   PR #16 v3..v3.1   experiment: split shaft + housing.
//   PR #16 v4         reverted to monolithic.
//   PR #16 v4.1       added a Ø8 mm central support shaft for the
//                     helix -- the geometry that successfully
//                     metered powder in @williamulbz's print test.
//   PR #16 v5         removed the helix + shaft; the H2D test print
//                     showed the inner core stringing.  v5 became
//                     just an empty tube relying on rotation +
//                     vibration to meter powder out the exit hole.
//   cad/auger-geared/ v1
//                     (this folder) Copied PR #16 v5 internals
//                     verbatim, so the inner core was empty.  Gear
//                     was also a SOLID disc, sealing the bore at
//                     the band z -- the auger was a closed cup.
//   v2                Fixed the gear: annular band via
//                     spur_gear_2d(..., inner_r=inner_r); also
//                     resized to Z_g=48 / Z_p=16, C=32 mm so the
//                     NEMA 11 body clears the auger.  Bore is open
//                     through the band -- but the helix was still
//                     missing.
//   v3 (here)         @williamulbz: "the inner auger core is
//                     completely missing from this part file ... be
//                     sure that the next iteration has the same
//                     core auger as that design [PR #16, v4.1]."
//                     This version puts the central shaft + helical
//                     fin back in, refactors the geometry into
//                     auger-core.scad, and adds a parameter pair
//                     `(total_h, gear_center_z)` so this file and
//                     `archimedes-auger-geared-short.scad` can share
//                     all geometry and only differ in length.
//
// ----------------------------------------------------------------
// Internal-geometry guarantee (issue requirement)
// ----------------------------------------------------------------
// "no part of this new design can alter or interfere with the
//  internal design of the auger.  The internals should be exactly
//  the same -- only its external features should change."
//
// Bore (10.5 mm radius), conical exit funnel, M3 spindle mount, top
// cap loading slots, central shaft (Ø8 mm), helical fin (10 mm
// pitch, 2 mm thick) are all in `auger-core.scad`.  The ONLY
// external addition vs PR #16 v4.1 is `gear_band()`, which is
// `union()`-only -- it never appears inside a `difference()`
// against the bore, funnel, cap, M3 pilot, shaft, or fin.
//
// ----------------------------------------------------------------
// Render
// ----------------------------------------------------------------
//   openscad -o archimedes-auger-geared.stl archimedes-auger-geared.scad
//
// PNG previews and cross-section: see ./README.md "Reproducing the
// renders".
// ================================================================

include <auger-core.scad>;

// ----------------------------------------------------------------
// Variant parameters (FULL LENGTH)
// ----------------------------------------------------------------
total_height_full   = 250;                    // mm  (PR #16 size)
gear_center_z_full  = total_height_full / 3;  // 83.33 mm from bottom

archimedes_auger_geared(
    total_h       = total_height_full,
    gear_center_z = gear_center_z_full
);

// ================================================================
// Cross-section view -- uncomment to verify in OpenSCAD preview
// that the central shaft + helical fin are continuous from funnel
// to top cap, and that the gear band is annular (bore visibly open
// through the band's axial slice).
// ================================================================
// difference() {
//     archimedes_auger_geared(total_height_full, gear_center_z_full);
//     translate([-gear_tip_r - 1, -0.5, -1])
//         cube([2 * gear_tip_r + 2, gear_tip_r + 1, total_height_full + 2]);
// }

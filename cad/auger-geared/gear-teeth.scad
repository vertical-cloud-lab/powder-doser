// ================================================================
// Powder Excavator - shared spur-gear primitives
// ================================================================
//
// Common stub-tooth math used by both
//   - archimedes-auger-geared.scad  (driven gear band on the auger)
//   - stepper-pinion.scad           (pinion on the NEMA 11 shaft)
//
// Keeping these helpers in one file means the two meshing parts
// cannot drift out of agreement on tooth profile during future
// maintenance.
//
// Tooth model: linear-flank approximation to a 20-deg involute stub
// tooth. For each tooth at radius r the half-thickness is
//
//   t(r) = pi * m / 2 - 2 * (r - pitch_r) * tan(PA)        [arc len]
//
// expressed as an angle in degrees (`tooth_half_angle`). For very
// small tooth counts (Z <= ~14) the analytic root half-angle exceeds
// half the angular pitch and adjacent tooth roots would overlap;
// `clamp_half_angle` clamps that case to the half-pitch, which prints
// cleanly and is harmless because the working flanks at and outside
// the pitch circle remain correct.
//
// OpenSCAD's tan() takes degrees, which is what we want for `PA`.
// ================================================================

function tooth_half_angle(r, pitch_r, m, PA) =
    ((PI * m / 2 - 2 * (r - pitch_r) * tan(PA)) / (2 * r)) * 180 / PI;

function clamp_half_angle(a, Z) = min(a, 360 / (2 * Z));

// 2D spur-gear cross-section: a root-circle disc (optionally hollowed
// to `inner_r`) unioned with `Z` trapezoidal teeth. Caller supplies
// the derived radii so the same helper works for any module / tooth
// count. `inner_r` defaults to 0 (solid disc, the natural pinion
// shape). For an external gear *band* integrated into a hollow tube
// (e.g. the geared Archimedes auger) pass `inner_r` equal to the
// tube's inner radius so the central bore stays open through the
// gear's axial slice -- otherwise the disc would seal the bore where
// the band sits and turn the auger into a closed cup. See
// archimedes-auger-geared.scad for the integrated-band use case.
module spur_gear_2d(Z, m, PA, root_r, pitch_r, tip_r, inner_r = 0) {
    difference() {
        union() {
            circle(r = root_r);
            for (i = [0 : Z - 1]) {
                rotate(360 * i / Z) {
                    a_root = clamp_half_angle(tooth_half_angle(root_r, pitch_r, m, PA), Z);
                    a_tip  = tooth_half_angle(tip_r,  pitch_r, m, PA);
                    polygon(points = [
                        [root_r * cos(-a_root), root_r * sin(-a_root)],
                        [tip_r  * cos(-a_tip),  tip_r  * sin(-a_tip) ],
                        [tip_r  * cos( a_tip),  tip_r  * sin( a_tip) ],
                        [root_r * cos( a_root), root_r * sin( a_root)],
                    ]);
                }
            }
        }
        if (inner_r > 0)
            circle(r = inner_r);
    }
}

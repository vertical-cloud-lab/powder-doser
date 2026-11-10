// Powder-excavator trough, OpenSCAD parametric model.
// All dimensions in mm. Dump-pivot axis is along +Y at z = trough_radius + cam.
trough_radius   = 12;
trough_length   = 40;
wall_thickness  = 1.6;

module trough() {
    difference() {
        // outer half-cylinder (lower hemisphere swept along Y)
        rotate([-90,0,0])
          translate([0,0,-trough_length/2])
            difference() {
              cylinder(h=trough_length, r=trough_radius, $fn=120);
              translate([-trough_radius*1.1, 0, -1])
                cube([trough_radius*2.2, trough_radius*1.1, trough_length+2]);
            }
        // hollow it out
        rotate([-90,0,0])
          translate([0,0,-trough_length/2 + 0.001])
            difference() {
              cylinder(h=trough_length, r=trough_radius - wall_thickness, $fn=120);
              translate([-trough_radius, 0, -1])
                cube([trough_radius*2, trough_radius*1.1, trough_length+2]);
            }
    }
}
trough();

Design a single 3D-printable Archimedes screw auger for metering dry powder.
All units millimetres. Orient the long axis along Z, print-upright.

Outer tube: outer diameter 25.0, wall thickness 2.0, so the inner bore
diameter is 21.0. Total length 250.0. The bore must stay fully open from end
to end (it is hollow). 

Top cap (at the +Z loading end), height 6.0: a disc closing the tube top with
four rectangular loading slots (each 4.0 wide by 7.0 long) evenly spaced on a
6.5 mm radius bolt circle, plus a central M3 pilot boss (3.0 mm diameter peg).

Bottom funnel (at the -Z dispense end), height 12.0: the tube tapers down to a
single central exit hole of diameter 3.0.

Internal single-start helical screw fin running only in the bottom one third
of the tube (from the bottom funnel up to Z = 83.33): central shaft diameter
8.0 on the axis, helical fin pitch 10.0 mm per turn, fin thickness 2.0. The
top two thirds of the bore above the screw is left completely open as a
loose-powder reservoir.

External spur gear drive band wrapped around the outside of the tube, centred
83.33 mm from the dispense (-Z) end: module 1.0, 48 teeth, 20 degree pressure
angle, face width 10.0, tip diameter 50.0, root diameter 45.5. The gear band
is annular - the 21 mm bore passes straight through it and is never filled.

Why it matters: rotating the screw conveys a small repeatable powder slug per
revolution (dose is proportional to revolutions); the open reservoir holds the
charge; the annular gear band is driven by the stepper pinion without ever
blocking the powder path.

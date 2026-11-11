FeatureScript 3083;
import(path : "onshape/std/common.fs", version : "3083.0");

// Baseplate for the servos-above powder doser (issue #172, PR #176), as a native Onshape
// feature tree. Same spec as cad/text-to-cad/src/parts/baseplate.py, make_baseplate("above"):
// Z up, underside on z = 0, hinge axis along X through y = 45.4, outlet towards -Y.
//
// Everything above the table is placed relative to the plate top (#plateThickness), and the
// towers and cradles are #hingeDrop shorter, so the two edits PR #176 made through the REST API
// are one variable each here:
//   "thinner table"           #plateThickness 6 -> 3 mm (everything on the table sits 3 mm lower)
//   "hinge 5 mm lower"        #hingeDrop (5 mm in the current design)
// The same script as ../parts/baseplate_servos_above.fs (fsgen 0.1), repeated with fsgen 0.2.0.
// 0.2.0 dimensions every line, polyline and arc point from the origin with these expressions, so
// in Onshape the tower and cradle sketches follow #plateThickness and #hingeDrop too.
export function build(context is Context, id is Id)
{
    variable(context, "plateThickness", 6 * millimeter);      // the table (PR #176 main edit: 6 -> 3 mm)
    variable(context, "hingeDrop", 5 * millimeter);           // towers and cradles this much shorter
    variable(context, "slotWidth", 57.8 * millimeter);        // cup slot between the towers
    variable(context, "reliefSkin", 2 * millimeter);          // floor left under the relief
    variable(context, "screwHoleDiameter", 5.5 * millimeter); // #10 wood screws into the board
    variable(context, "hingeHoleDiameter", 5.3 * millimeter); // M5 x 45 hinge screw
    variable(context, "cradleHoleDiameter", 3.4 * millimeter);// M3 servo-ear screws

    // ---- plate: 45 deg rear corners, four screw holes into the board
    var plate = newSketch(context, id + "Plate sketch", { "sketchPlane" : qCreatedBy(makeId("Top"), EntityType.FACE) });
    skPolyline(plate, "outline", { "points" : [
            vector(-95, 55.4) * millimeter, vector(95, 55.4) * millimeter,
            vector(95, 146) * millimeter, vector(71, 170) * millimeter,
            vector(-71, 170) * millimeter, vector(-95, 146) * millimeter,
            vector(-95, 55.4) * millimeter] });
    for (var sx in [-1, 1])
    {
        for (var y in [120, 155])
        {
            skCircle(plate, "screw" ~ (sx > 0 ? "R" : "L") ~ y, { "center" : vector(sx * 80, y) * millimeter,
                        "radius" : #screwHoleDiameter / 2 });
        }
    }
    skSolve(plate);
    extrude(context, id + "Plate", {
        "entities" : qSketchRegion(id + "Plate sketch", true),
        "endBound" : BoundingType.BLIND,
        "depth" : #plateThickness });

    // ---- relief under the mounting plate's floor (its footprint + 1.5 mm, + 1.5 mm swing
    //      allowance), from #reliefSkin up through the top; tongues forward beside the towers
    cPlane(context, id + "Relief floor plane", { "entities" : qCreatedBy(makeId("Top"), EntityType.FACE),
                "offset" : #reliefSkin });
    var relief = newSketch(context, id + "Relief sketch", { "sketchPlane" : qCreatedBy(id + "Relief floor plane", EntityType.FACE) });
    const half = [[41.2, 80.9], [41.2, 61.0], [55.6, 61.0], [55.6, 85.1426], [35.5, 105.2426], [35.5, 121.23],
            [55.6, 121.23], [55.6, 143.73], [35.5, 143.73], [35.5, 180.4]];
    var pts = [];
    for (var p in half)
    {
        pts = append(pts, vector(p[0], p[1]) * millimeter);
    }
    for (var i = size(half) - 1; i >= 0; i -= 1)
    {
        pts = append(pts, vector(-half[i][0], half[i][1]) * millimeter);
    }
    pts = append(pts, pts[0]);
    skPolyline(relief, "outline", { "points" : pts });
    skSolve(relief);
    extrude(context, id + "Relief", {
        "entities" : qSketchRegion(id + "Relief sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Plate", EntityType.BODY) });

    // ---- the cup slot between the towers, back past the board's edge (the plate is a fork in front
    //      of the board), and notches for the rear bracket's two M3 button heads
    var cuts = newSketch(context, id + "Slot and notch sketch", { "sketchPlane" : qCreatedBy(makeId("Top"), EntityType.FACE) });
    skRectangle(cuts, "slot", { "firstCorner" : vector(-#slotWidth / 2, 54.4 * millimeter),
                "secondCorner" : vector(#slotWidth / 2, 111 * millimeter) });
    skCircle(cuts, "notchR", { "center" : vector(24, 169.4) * millimeter, "radius" : 4.5 * millimeter });
    skCircle(cuts, "notchL", { "center" : vector(-24, 169.4) * millimeter, "radius" : 4.5 * millimeter });
    skSolve(cuts);
    extrude(context, id + "Cup slot and head notches", {
        "entities" : qSketchRegion(id + "Slot and notch sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Plate", EntityType.BODY) });

    // ---- hinge tower (+X side): inclined front face up to a knuckle round on the hinge, rear round
    //      tangent to the back face; the back face keeps its slope as the hinge drops.
    //      Sketch on a plane parallel to Right: sketch x -> world Y, sketch y -> world Z.
    cPlane(context, id + "Tower plane", { "entities" : qCreatedBy(makeId("Right"), EntityType.FACE),
                "offset" : 28.9 * millimeter });
    var tower = newSketch(context, id + "Tower sketch", { "sketchPlane" : qCreatedBy(id + "Tower plane", EntityType.FACE) });
    const hingeZ = #plateThickness + 37.25 * millimeter - #hingeDrop;
    skLineSegment(tower, "base", { "start" : vector(55.4 * millimeter, #plateThickness),
                "end" : vector(81.77 * millimeter - #hingeDrop * 0.3539851, #plateThickness) });
    skLineSegment(tower, "back", { "start" : vector(81.77 * millimeter - #hingeDrop * 0.3539851, #plateThickness),
                "end" : vector(67.756415 * millimeter, #plateThickness + 39.588069 * millimeter - #hingeDrop) });
    skArc(tower, "rearRound", { "start" : vector(67.756415 * millimeter, #plateThickness + 39.588069 * millimeter - #hingeDrop),
                "mid" : vector(64.101452 * millimeter, #plateThickness + 44.416416 * millimeter - #hingeDrop),
                "end" : vector(58.33 * millimeter, #plateThickness + 46.25 * millimeter - #hingeDrop) });
    skLineSegment(tower, "top", { "start" : vector(58.33 * millimeter, #plateThickness + 46.25 * millimeter - #hingeDrop),
                "end" : vector(45.4 * millimeter, #plateThickness + 46.25 * millimeter - #hingeDrop) });
    skArc(tower, "knuckle", { "start" : vector(45.4 * millimeter, #plateThickness + 46.25 * millimeter - #hingeDrop),
                "mid" : vector(36.4 * millimeter, hingeZ),
                "end" : vector(45.4 * millimeter, #plateThickness + 28.25 * millimeter - #hingeDrop) });
    skLineSegment(tower, "front", { "start" : vector(45.4 * millimeter, #plateThickness + 28.25 * millimeter - #hingeDrop),
                "end" : vector(55.4 * millimeter, #plateThickness) });
    skCircle(tower, "hingeHole", { "center" : vector(45.4 * millimeter, hingeZ), "radius" : #hingeHoleDiameter / 2 });
    skSolve(tower);
    extrude(context, id + "Hinge tower", {
        "entities" : qSketchRegion(id + "Tower sketch", true),
        "operationType" : NewBodyOperationType.ADD,
        "endBound" : BoundingType.BLIND,
        "depth" : 12.3 * millimeter,
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Plate", EntityType.BODY) });

    // ---- servo cradle (+X side): open-top U that takes the MG996R case (40.7 mm + 0.3 mm each side)
    //      from above, four M3 ear holes, a diagonal strut from the plate's front edge to the front post
    cPlane(context, id + "Cradle plane", { "entities" : qCreatedBy(makeId("Right"), EntityType.FACE),
                "offset" : 67.1 * millimeter });
    var cradle = newSketch(context, id + "Cradle sketch", { "sketchPlane" : qCreatedBy(id + "Cradle plane", EntityType.FACE) });
    const top = #plateThickness + 74.66 * millimeter - #hingeDrop;
    const slotFloor = #plateThickness + 54.36 * millimeter - #hingeDrop;
    skPolyline(cradle, "outline", { "points" : [
            vector(55.4 * millimeter, #plateThickness), vector(101 * millimeter, #plateThickness),
            vector(83.3 * millimeter, top), vector(75.93 * millimeter, top),
            vector(75.93 * millimeter, slotFloor), vector(34.63 * millimeter, slotFloor),
            vector(34.63 * millimeter, top), vector(27.3 * millimeter, top),
            vector(27.3 * millimeter, #plateThickness + 52 * millimeter - #hingeDrop),
            vector(55.4 * millimeter, #plateThickness)] });
    for (var y in [79.3, 31.26])
    {
        for (var z in [69.02, 59.98])
        {
            skCircle(cradle, "ear" ~ (y > 50 ? "Rear" : "Front") ~ (z > 65 ? "Upper" : "Lower"), { "center" : vector(y * millimeter, #plateThickness + z * millimeter - #hingeDrop),
                        "radius" : #cradleHoleDiameter / 2 });
        }
    }
    skSolve(cradle);
    extrude(context, id + "Servo cradle", {
        "entities" : qSketchRegion(id + "Cradle sketch", true),
        "operationType" : NewBodyOperationType.ADD,
        "endBound" : BoundingType.BLIND,
        "depth" : 5 * millimeter,
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Plate", EntityType.BODY) });

    // ---- the -X tower and cradle. As first written for fsgen 0.1: no "fullFeaturePattern" here.
    //      fsgen 0.2.0 sends "Reapply features" for feature patterns by default (0.1 didn't, and
    //      Onshape rejected this mirror with PATTERN_SWITCH_TO_PER_INSTANCE)
    mirror(context, id + "Mirror tower and cradle", {
        "patternType" : PatternType.FEATURE,
        "instanceFunction" : [id + "Hinge tower", id + "Servo cradle"],
        "mirrorPlane" : qCreatedBy(makeId("Right"), EntityType.FACE) });
}

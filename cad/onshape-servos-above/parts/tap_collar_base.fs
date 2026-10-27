FeatureScript 3083;
import(path : "onshape/std/common.fs", version : "3083.0");

// Tap-collar base of the servos-above powder doser as a native Onshape feature tree (issue #172), for fsgen 0.2.0:
// the hard-stop plate under the tap collar. Same part as cad/text-to-cad/src/parts/tap_collar_base.py, which
// recreates PR #170's components/ai-step/tap-collar-base.step (PR #51's mount_plate.step, still on the rig).
// Same frame as tap_collar_base.step:
//   underside on z = 0, centred on x = 0 and y = 0; the profile is extruded along Y, symmetric about y = 0;
//   the cradle (a cylindrical saddle for the collar ring) is coaxial with the auger tube: x = 0, z = #cradleHeight,
//   axis parallel to Y.
// One profile (block + the hard-stop tower on the +X end) extruded symmetrically, the cradle cut into the block top,
// two vertical M3 clearance holes (plain at -x, through the tower at +x), then the concave fillets at the tower root
// and a 90 deg countersink at the tower top for a flat-head screw (an equal-offset chamfer of the hole's top edge).
export function build(context is Context, id is Id)
{
    // ---------- variables (one Variable Studio) ----------
    variable(context, "length", 60 * millimeter);               // X
    variable(context, "depth", 18 * millimeter);                // Y, symmetric about y = 0
    variable(context, "blockHeight", 14 * millimeter);          // top of the block
    variable(context, "cradleDiameter", 34 * millimeter);       // saddle for the collar ring
    variable(context, "cradleHeight", 29.25 * millimeter);      // saddle axis (= auger tube axis)
    variable(context, "towerStop", 17.25 * millimeter);         // x of the tower's hard-stop face (towards the cradle)
    variable(context, "towerWidth", 9.95 * millimeter);         // tower along X (to x = 27.2 mm)
    variable(context, "towerHeight", 21 * millimeter);          // top of the tower
    variable(context, "towerFilletRadius", 1.5 * millimeter);   // concave fillets at the tower root, both sides
    variable(context, "holeDiameter", 3.4 * millimeter);        // M3 clearance, vertical
    variable(context, "holeSpacing", 48 * millimeter);          // plain hole at -x, countersunk hole through the tower at +x
    variable(context, "countersinkDiameter", 6 * millimeter);   // at the tower top, 90 deg included angle

    const zero = 0 * millimeter;
    const SINK = 1 * millimeter;
    const frontPlane = qCreatedBy(makeId("Front"), EntityType.FACE);   // sketch x -> +X, sketch y -> +Z
    const towerOuter = #towerStop + #towerWidth;

    // ---------- body: block with the hard-stop tower on the +X end, one outline ----------
    var bodySk = newSketch(context, id + "Body sketch", { "sketchPlane" : frontPlane });
    skPolyline(bodySk, "outline", { "points" : [
            vector(-#length / 2, zero), vector(#length / 2, zero),
            vector(#length / 2, #blockHeight), vector(towerOuter, #blockHeight),
            vector(towerOuter, #towerHeight), vector(#towerStop, #towerHeight),
            vector(#towerStop, #blockHeight), vector(-#length / 2, #blockHeight),
            vector(-#length / 2, zero)] });
    skSolve(bodySk);
    extrude(context, id + "Body", {
        "entities" : qSketchRegion(id + "Body sketch"),
        "endBound" : BoundingType.BLIND,
        "depth" : #depth,
        "symmetric" : true });

    // ---------- cradle: the collar-ring saddle cut into the block top ----------
    var cradleSk = newSketch(context, id + "Cradle sketch", { "sketchPlane" : frontPlane });
    skCircle(cradleSk, "cradle", { "center" : vector(zero, #cradleHeight), "radius" : #cradleDiameter / 2 });
    skSolve(cradleSk);
    extrude(context, id + "Cradle", {
        "entities" : qSketchRegion(id + "Cradle sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.BLIND,
        "depth" : #depth + 2 * SINK,
        "symmetric" : true,
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Body", EntityType.BODY) });

    // ---------- two vertical mounting holes, up through the block and the tower ----------
    var holeSk = newSketch(context, id + "Mounting holes sketch", { "sketchPlane" : qCreatedBy(makeId("Top"), EntityType.FACE) });
    skCircle(holeSk, "plain", { "center" : vector(-#holeSpacing / 2, zero), "radius" : #holeDiameter / 2 });
    skCircle(holeSk, "tower", { "center" : vector(#holeSpacing / 2, zero), "radius" : #holeDiameter / 2 });
    skSolve(holeSk);
    extrude(context, id + "Mounting holes", {
        "entities" : qSketchRegion(id + "Mounting holes sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,                          // +Z
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Body", EntityType.BODY) });

    // ---------- fillet and countersink (faces picked by feature and direction, so variable edits keep them) ----------
    const upFaces = qParallelPlanes(qCreatedBy(id + "Body", EntityType.FACE), vector(0, 0, 1));   // block top pieces, tower top
    const towerTop = qFarthestAlong(upFaces, vector(0, 0, 1));
    const besideTowerTop = qAdjacent(towerTop, AdjacencyType.EDGE, EntityType.FACE);
    const towerSides = qUnion([qParallelPlanes(besideTowerTop, vector(1, 0, 0)), qParallelPlanes(besideTowerTop, vector(-1, 0, 0))]);
    // the two edges where the tower sides meet the block top
    fillet(context, id + "Tower root fillets", {
        "entities" : qIntersection([qAdjacent(towerSides, AdjacencyType.EDGE, EntityType.EDGE),
                    qAdjacent(qSubtraction(upFaces, towerTop), AdjacencyType.EDGE, EntityType.EDGE)]),
        "radius" : #towerFilletRadius });
    // 90 deg countersink: equal offsets of (countersink - hole) / 2 on the hole's edge in the tower top
    chamfer(context, id + "Countersink", {
        "entities" : qGeometry(qAdjacent(towerTop, AdjacencyType.EDGE, EntityType.EDGE), GeometryType.CIRCLE),
        "chamferType" : ChamferType.EQUAL_OFFSETS,
        "width" : (#countersinkDiameter - #holeDiameter) / 2 });
}

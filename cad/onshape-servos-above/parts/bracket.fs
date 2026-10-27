FeatureScript 3083;
import(path : "onshape/std/common.fs", version : "3083.0");

// Auger bracket of the servos-above powder doser as a native Onshape feature tree (issue #172), for fsgen 0.2.0.
// Same part as cad/text-to-cad/src/parts/bracket.py, which recreates the lab's Fusion 360 part
// "Auger_Bracket_Recorded_v1": a split clamp ring on a footed base. One part, used twice (front and rear bracket).
// Same frame as bracket.step:
//   base underside on z = 0, centred on x = 0; every profile is extruded along +Y from y = 0 to #thickness;
//   the clamp bore axis is parallel to Y at x = 0, z = #boreHeight (the auger tube axis).
// The outline is drawn as simple overlapping shapes (stepped base; ring circle + ear rectangle; bore circle +
// split rectangle), so every sketch point is an expression of the variables and nothing needs a computed
// intersection. M3 clearance holes on the mid-plane y = #thickness / 2: the clamp screw through both ears (along X)
// and one mounting hole through each foot (along Z). Fillets last: the concave web fillets where the pedestal top
// meets the ring, and rounds on all four top edges of each ear (the corners mitre, as in the Fusion part).
// Added shapes sink into what they join, so no faces only touch.
export function build(context is Context, id is Id)
{
    // ---------- variables (one Variable Studio) ----------
    variable(context, "thickness", 12 * millimeter);           // extrusion depth along +Y
    variable(context, "baseLength", 60 * millimeter);          // X extent of the footed base
    variable(context, "footHeight", 8 * millimeter);           // feet (flanges) at both ends
    variable(context, "pedestalWidth", 36 * millimeter);       // centre block between the feet
    variable(context, "pedestalHeight", 14 * millimeter);      // top of the centre block
    variable(context, "boreHeight", 29.25 * millimeter);       // clamp bore axis (= auger tube axis)
    variable(context, "boreDiameter", 25.5 * millimeter);      // auger tube clearance
    variable(context, "ringWall", 4 * millimeter);             // clamp ring wall around the bore
    variable(context, "slotWidth", 2 * millimeter);            // clamp split, from the bore to the top
    variable(context, "earThickness", 3 * millimeter);         // each clamp ear, along X
    variable(context, "earTopHeight", 52.9615 * millimeter);   // top of the ears (30 sqrt(3) + 1 mm in Fusion)
    variable(context, "screwHoleDiameter", 3.4 * millimeter);  // M3 clearance: clamp screw and mounting screws
    variable(context, "clampHoleHeight", 49.2 * millimeter);   // clamp screw axis
    variable(context, "mountHoleSpacing", 48 * millimeter);    // between the two foot holes
    variable(context, "webFilletRadius", 3 * millimeter);      // concave fillet, pedestal top -> ring
    variable(context, "earRoundRadius", 1 * millimeter);       // rounds on the ear tops

    const mm = millimeter;
    const zero = 0 * millimeter;
    const SINK = 1 * millimeter;
    const frontPlane = qCreatedBy(makeId("Front"), EntityType.FACE);   // sketch x -> +X, sketch y -> +Z, normal -Y
    const earHalfSpan = #slotWidth / 2 + #earThickness;

    // ---------- base: two feet and the pedestal between them, one stepped outline ----------
    var baseSk = newSketch(context, id + "Base sketch", { "sketchPlane" : frontPlane });
    skPolyline(baseSk, "outline", { "points" : [
            vector(-#baseLength / 2, zero), vector(#baseLength / 2, zero),
            vector(#baseLength / 2, #footHeight), vector(#pedestalWidth / 2, #footHeight),
            vector(#pedestalWidth / 2, #pedestalHeight), vector(-#pedestalWidth / 2, #pedestalHeight),
            vector(-#pedestalWidth / 2, #footHeight), vector(-#baseLength / 2, #footHeight),
            vector(-#baseLength / 2, zero)] });
    skSolve(baseSk);
    extrude(context, id + "Base", {
        "entities" : qSketchRegion(id + "Base sketch"),
        "endBound" : BoundingType.BLIND,
        "depth" : #thickness,
        "oppositeDirection" : true });                                  // +Y

    // ---------- clamp ring and the two ears above it (the ring dips into the pedestal, the ears into the ring) ----------
    var ringSk = newSketch(context, id + "Clamp ring and ears sketch", { "sketchPlane" : frontPlane });
    skCircle(ringSk, "ring", { "center" : vector(zero, #boreHeight), "radius" : #boreDiameter / 2 + #ringWall });
    skRectangle(ringSk, "ears", { "firstCorner" : vector(-earHalfSpan, #boreHeight),
                "secondCorner" : vector(earHalfSpan, #earTopHeight) });
    skSolve(ringSk);
    extrude(context, id + "Clamp ring and ears", {
        "entities" : qSketchRegion(id + "Clamp ring and ears sketch"),
        "operationType" : NewBodyOperationType.ADD,
        "endBound" : BoundingType.BLIND,
        "depth" : #thickness,
        "oppositeDirection" : true,
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Base", EntityType.BODY) });

    // ---------- bore and the clamp split up through the ears ----------
    var boreSk = newSketch(context, id + "Bore and split sketch", { "sketchPlane" : frontPlane });
    skCircle(boreSk, "bore", { "center" : vector(zero, #boreHeight), "radius" : #boreDiameter / 2 });
    skRectangle(boreSk, "split", { "firstCorner" : vector(-#slotWidth / 2, #boreHeight),
                "secondCorner" : vector(#slotWidth / 2, #earTopHeight + SINK) });
    skSolve(boreSk);
    extrude(context, id + "Bore and clamp split", {
        "entities" : qSketchRegion(id + "Bore and split sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,
        "oppositeDirection" : true,                                     // +Y, through the part
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Base", EntityType.BODY) });

    // ---------- clamp screw hole through both ears, along X (Right plane: sketch x -> +Y, sketch y -> +Z) ----------
    var clampSk = newSketch(context, id + "Clamp screw hole sketch", { "sketchPlane" : qCreatedBy(makeId("Right"), EntityType.FACE) });
    skCircle(clampSk, "hole", { "center" : vector(#thickness / 2, #clampHoleHeight), "radius" : #screwHoleDiameter / 2 });
    skSolve(clampSk);
    extrude(context, id + "Clamp screw hole", {
        "entities" : qSketchRegion(id + "Clamp screw hole sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.BLIND,
        "depth" : 2 * earHalfSpan + 2 * SINK,
        "symmetric" : true,                                             // through both ears, centred on x = 0
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Base", EntityType.BODY) });

    // ---------- one mounting hole through each foot, along Z ----------
    var mountSk = newSketch(context, id + "Mounting holes sketch", { "sketchPlane" : qCreatedBy(makeId("Top"), EntityType.FACE) });
    skCircle(mountSk, "holeL", { "center" : vector(-#mountHoleSpacing / 2, #thickness / 2), "radius" : #screwHoleDiameter / 2 });
    skCircle(mountSk, "holeR", { "center" : vector(#mountHoleSpacing / 2, #thickness / 2), "radius" : #screwHoleDiameter / 2 });
    skSolve(mountSk);
    extrude(context, id + "Mounting holes", {
        "entities" : qSketchRegion(id + "Mounting holes sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,                          // +Z, up through the feet
        "defaultScope" : false,
        "booleanScope" : qCreatedBy(id + "Base", EntityType.BODY) });

    // ---------- fillets (edges picked by the features that made their faces, so variable edits keep them) ----------
    // web: the two edges where the ring's outside cylinder meets the pedestal top
    const ringOutside = qGeometry(qCreatedBy(id + "Clamp ring and ears", EntityType.FACE), GeometryType.CYLINDER);
    const baseTops = qParallelPlanes(qCreatedBy(id + "Base", EntityType.FACE), vector(0, 0, 1));
    fillet(context, id + "Web fillets", {
        "entities" : qIntersection([qAdjacent(ringOutside, AdjacencyType.EDGE, EntityType.EDGE),
                    qAdjacent(baseTops, AdjacencyType.EDGE, EntityType.EDGE)]),
        "radius" : #webFilletRadius });
    // ears: the two top faces (the ear rectangle's top, split by the clamp slot); all four edges of each
    fillet(context, id + "Ear top rounds", {
        "entities" : qParallelPlanes(qCreatedBy(id + "Clamp ring and ears", EntityType.FACE), vector(0, 0, 1)),
        "radius" : #earRoundRadius });
}

FeatureScript 3083;
import(path : "onshape/std/geometry.fs", version : "3083.0");

// Powder doser, servos above (vertical-cloud-lab/powder-doser #172).
// Lowers the baseplate's hinge towers and servo cradles by `drop` (every
// piece above `splitHeight` moves down and is merged back), then pockets the
// table under the mounting plate so its floor clears the table by
// `clearance` once the tilting system is `drop` lower, and opens holes under
// the four bracket screw heads.  Written by cad/text-to-cad/onshape/lower_hinge.py.

// the mounting plate's outline where it would sink into the table, + 1 mm
const MP_OUTLINE = [
    vector(55.100, 82.814) * millimeter,
    vector(55.100, 61.394) * millimeter,
    vector(41.200, 61.394) * millimeter,
    vector(41.200, 81.770) * millimeter,
    vector(28.900, 81.770) * millimeter,
    vector(28.900, 61.394) * millimeter,
    vector(15.100, 61.394) * millimeter,
    vector(15.100, 81.400) * millimeter,
    vector(-15.100, 81.400) * millimeter,
    vector(-15.100, 61.394) * millimeter,
    vector(-28.900, 61.394) * millimeter,
    vector(-28.900, 81.770) * millimeter,
    vector(-41.200, 81.770) * millimeter,
    vector(-41.200, 61.394) * millimeter,
    vector(-55.100, 61.394) * millimeter,
    vector(-55.100, 82.012) * millimeter,
    vector(-35.000, 102.112) * millimeter,
    vector(-35.000, 121.733) * millimeter,
    vector(-48.156, 121.733) * millimeter,
    vector(-49.659, 121.902) * millimeter,
    vector(-51.140, 122.421) * millimeter,
    vector(-52.468, 123.255) * millimeter,
    vector(-53.578, 124.365) * millimeter,
    vector(-54.412, 125.693) * millimeter,
    vector(-54.931, 127.174) * millimeter,
    vector(-55.100, 128.677) * millimeter,
    vector(-55.100, 134.789) * millimeter,
    vector(-54.931, 136.292) * millimeter,
    vector(-54.412, 137.773) * millimeter,
    vector(-53.578, 139.101) * millimeter,
    vector(-52.468, 140.211) * millimeter,
    vector(-51.140, 141.045) * millimeter,
    vector(-49.659, 141.564) * millimeter,
    vector(-48.156, 141.733) * millimeter,
    vector(-35.000, 141.733) * millimeter,
    vector(-35.000, 176.400) * millimeter,
    vector(35.000, 176.400) * millimeter,
    vector(35.000, 102.914) * millimeter,
    vector(55.100, 82.814) * millimeter
];
const SCREW_HEADS_MM = [[24.0, 103.73], [-24.0, 103.73], [24.0, 169.4], [-24.0, 169.4]];
const SCREW_HEAD_HOLE_R = 3.5 * millimeter;     // heads are 5.7 mm across
const TABLE_TOP = 6 * millimeter;
const MP_BOTTOM_AT_REST = 8 * millimeter;
const SCREW_HEADS_AT_REST = 6.35 * millimeter;

function sketchPlaneOnTable() returns Plane
{
    return plane(vector(0, 0, 1) * TABLE_TOP, vector(0, 0, 1), vector(1, 0, 0));
}

annotation { "Feature Type Name" : "Lower hinge, relieve table" }
export const lowerHinge = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Baseplate", "Filter" : EntityType.BODY && BodyType.SOLID, "MaxNumberOfPicks" : 1 }
        definition.baseplate is Query;

        annotation { "Name" : "Drop" }
        isLength(definition.drop, { (millimeter) : [0, 5, 6.3] } as LengthBoundSpec);

        annotation { "Name" : "Split height" }
        isLength(definition.splitHeight, { (millimeter) : [12.5, 20, 30] } as LengthBoundSpec);

        annotation { "Name" : "Clearance" }
        isLength(definition.clearance, { (millimeter) : [0, 0.5, 2] } as LengthBoundSpec);
    }
    {
        const drop = definition.drop;
        if (drop < 1e-6 * millimeter)
            return;

        // 1. shorter towers and cradles: split, move the tops down, merge
        opPlane(context, id + "splitPlane", { "plane" : plane(vector(0, 0, 1) * definition.splitHeight, vector(0, 0, 1), vector(1, 0, 0)) });
        opSplitPart(context, id + "split", { "targets" : definition.baseplate,
                    "tool" : qCreatedBy(id + "splitPlane", EntityType.FACE), "keepTools" : false });
        const pieces = qUnion([definition.baseplate, qCreatedBy(id + "split", EntityType.BODY)]);
        var tops = [];
        for (var body in evaluateQuery(context, pieces))
        {
            if (evBox3d(context, { "topology" : body, "tight" : true }).minCorner[2] > definition.splitHeight - 1e-4 * millimeter)
                tops = append(tops, body);
        }
        opTransform(context, id + "down", { "bodies" : qUnion(tops), "transform" : transform(vector(0, 0, -1) * drop) });
        opBoolean(context, id + "merge", { "tools" : pieces, "operationType" : BooleanOperationType.UNION });
        if (size(evaluateQuery(context, qCreatedBy(id + "splitPlane"))) > 0)
            opDeleteBodies(context, id + "deletePlane", { "entities" : qCreatedBy(id + "splitPlane") });
        const base = qUnion([definition.baseplate, qCreatedBy(id + "merge", EntityType.BODY)]);

        // 2. pocket under the mounting plate
        const floorZ = MP_BOTTOM_AT_REST - drop - definition.clearance;
        if (floorZ < TABLE_TOP)
        {
            const sk = newSketchOnPlane(context, id + "pocketSketch", { "sketchPlane" : sketchPlaneOnTable() });
            skPolyline(sk, "outline", { "points" : MP_OUTLINE });
            skSolve(sk);
            opExtrude(context, id + "pocketTool", { "entities" : qSketchRegion(id + "pocketSketch"),
                      "direction" : vector(0, 0, -1), "endBound" : BoundingType.BLIND, "endDepth" : TABLE_TOP - floorZ });
            opBoolean(context, id + "pocket", { "tools" : qCreatedBy(id + "pocketTool", EntityType.BODY),
                      "targets" : base, "operationType" : BooleanOperationType.SUBTRACTION });
            opDeleteBodies(context, id + "deletePocketSketch", { "entities" : qCreatedBy(id + "pocketSketch") });
        }

        // 3. holes under the bracket screw heads, through the table
        if (SCREW_HEADS_AT_REST - drop - definition.clearance < max(floorZ, 0 * millimeter))
        {
            const sk = newSketchOnPlane(context, id + "headSketch", { "sketchPlane" : sketchPlaneOnTable() });
            for (var i = 0; i < size(SCREW_HEADS_MM); i += 1)
                skCircle(sk, "head" ~ i, { "center" : vector(SCREW_HEADS_MM[i][0], SCREW_HEADS_MM[i][1]) * millimeter,
                         "radius" : SCREW_HEAD_HOLE_R });
            skSolve(sk);
            opExtrude(context, id + "headTool", { "entities" : qSketchRegion(id + "headSketch"),
                      "direction" : vector(0, 0, -1), "endBound" : BoundingType.BLIND, "endDepth" : TABLE_TOP + 1 * millimeter });
            opBoolean(context, id + "heads", { "tools" : qCreatedBy(id + "headTool", EntityType.BODY),
                      "targets" : base, "operationType" : BooleanOperationType.SUBTRACTION });
            opDeleteBodies(context, id + "deleteHeadSketch", { "entities" : qCreatedBy(id + "headSketch") });
        }
    });

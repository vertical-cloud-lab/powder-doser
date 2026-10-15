FeatureScript 3083;
import(path : "onshape/std/geometry.fs", version : "3083.0");

// Powder doser, servos above (vertical-cloud-lab/powder-doser #172).
// The text-to-cad lowering (cad/text-to-cad/src/parts/baseplate.py at
// 92c195e), redone as one Onshape feature on the imported baseplate: the
// old hinge towers and servo cradles are cut off at the table top and
// rebuilt `drop` lower from the same profiles (the towers' back faces keep
// their slope, the front faces still end on the plate's front edge, the
// cradles keep their feet), and the plate gets the same cuts: the slot
// widened to the towers and run on to y = 111, the relief under the
// mounting plate's floor (2 mm skin; 1.5 mm margin, 1.5 mm more where the
// floor swings back as the doser tilts), and notches under the rear
// bracket's screw heads.  Numbers in mm, world frame of baseplate.py.

// plate
const PLATE_T = 6;
const BOARD_EDGE_Y = 55.4;
// hinge towers
const TOWER_X = [28.9, 41.2];
const HINGE_Y = 45.4;
const HINGE_Z = 43.25;
const KNUCKLE_R = 9;
const TOWER_TOP_Z = 52.25;
const REAR_ROUND_R = 10;
const REAR_ROUND_C = [58.33, 42.25];
const TOWER_BACK_FOOT_Y = 81.77;
const HINGE_HOLE_D = 5.3;
// servo cradles
const POST_X = [67.1, 72.1];
const FLIP_Y = 90.8;
const FLIP_Z = 86.5;
const POST_HOLE_YS = [11.5, 59.54];
const POST_HOLE_ZS = [11.48, 20.52];
const SERVO_CASE_Y = [34.93, 75.63];
const SERVO_CASE_Z = [60.66, 80.36];
const CASE_CLEARANCE = 0.3;
const CRADLE_HOLE_D = 3.4;
const FRAME_FOOT_REAR_Y = 101.0;
const FRAME_FRONT_POST_Y = 27.3;
const FRAME_FRONT_POST_FOOT_Z = 58.0;
const REAR_POST_Y1 = 83.3;
// plate cuts for the lowered layout
const SLOT_HALF_W = 28.9;
const SLOT_END_Y = 111.0;
const RELIEF_Z = 2.0;
const RELIEF_MARGIN = 1.5;
const RELIEF_SWING = 1.5;
const RELIEF_TONGUE_Y = 61.0;
const RELIEF_BEHIND_TOWER_Y = 80.9;
const HEAD_NOTCH_D = 9.0;
const REAR_HEADS = [[24.0, 169.4], [-24.0, 169.4]];

function p3(x is number, y is number, z is number) returns Vector
{
    return vector(x, y, z) * millimeter;
}

function p2(u is number, v is number) returns Vector
{
    return vector(u, v) * millimeter;
}

function makeBox(context is Context, id is Id, lo is array, hi is array) returns Query
{
    fCuboid(context, id, { "corner1" : p3(lo[0], lo[1], lo[2]), "corner2" : p3(hi[0], hi[1], hi[2]) });
    return qCreatedBy(id, EntityType.BODY);
}

function makeCylinder(context is Context, id is Id, a is Vector, b is Vector, d is number) returns Query
{
    fCylinder(context, id, { "bottomCenter" : a, "topCenter" : b, "radius" : d / 2 * millimeter });
    return qCreatedBy(id, EntityType.BODY);
}

function cutAway(context is Context, id is Id, targets is Query, tools is Query)
{
    opBoolean(context, id, { "tools" : tools, "targets" : targets,
              "operationType" : BooleanOperationType.SUBTRACTION });
}

function closedPolyline(points is array) returns array
{
    var pts = [];
    for (var p in points)
        pts = append(pts, p2(p[0], p[1]));
    return append(pts, p2(points[0][0], points[0][1]));
}

function extrudeSketch(context is Context, id is Id, direction is Vector, depth is number) returns Query
{
    opExtrude(context, id + "extrude", { "entities" : qSketchRegion(id + "sketch"), "direction" : direction,
              "endBound" : BoundingType.BLIND, "endDepth" : depth * millimeter });
    opDeleteBodies(context, id + "deleteSketch", { "entities" : qCreatedBy(id + "sketch") });
    return qCreatedBy(id + "extrude", EntityType.BODY);
}

function yzPlane(x is number) returns Plane
{
    return plane(p3(x, 0, 0), vector(1, 0, 0), vector(0, 1, 0));   // sketch (u, v) = world (y, z)
}

/** Hinge tower between x0 and x1 (baseplate.py _tower). */
function tower(context is Context, id is Id, x0 is number, x1 is number, drop is number) returns Query
{
    const hz = HINGE_Z - drop;
    const top = TOWER_TOP_Z - drop;
    const cy = REAR_ROUND_C[0];
    const cz = REAR_ROUND_C[1] - drop;
    const a0 = 19.5 * degree;
    const am = (19.5 + 90) / 2 * degree;
    const pRound = [cy + REAR_ROUND_R * cos(a0), cz + REAR_ROUND_R * sin(a0)];
    const pMid = [cy + REAR_ROUND_R * cos(am), cz + REAR_ROUND_R * sin(am)];
    // the back face keeps its slope, so its foot moves forward
    const backFootY = TOWER_BACK_FOOT_Y + (pRound[0] - TOWER_BACK_FOOT_Y) * drop / (pRound[1] + drop - PLATE_T);
    const sk = newSketchOnPlane(context, id + "sketch", { "sketchPlane" : yzPlane(x0) });
    skLineSegment(sk, "foot", { "start" : p2(BOARD_EDGE_Y, PLATE_T), "end" : p2(backFootY, PLATE_T) });
    skLineSegment(sk, "back", { "start" : p2(backFootY, PLATE_T), "end" : p2(pRound[0], pRound[1]) });
    skArc(sk, "rearRound", { "start" : p2(pRound[0], pRound[1]), "mid" : p2(pMid[0], pMid[1]), "end" : p2(cy, top) });
    skLineSegment(sk, "top", { "start" : p2(cy, top), "end" : p2(HINGE_Y, top) });
    skArc(sk, "knuckle", { "start" : p2(HINGE_Y, top), "mid" : p2(HINGE_Y - KNUCKLE_R, hz),
                           "end" : p2(HINGE_Y, hz - KNUCKLE_R) });
    skLineSegment(sk, "front", { "start" : p2(HINGE_Y, hz - KNUCKLE_R), "end" : p2(BOARD_EDGE_Y, PLATE_T) });
    skSolve(sk);
    const body = extrudeSketch(context, id, vector(1, 0, 0), x1 - x0);
    cutAway(context, id + "hingeHole", body,
            makeCylinder(context, id + "hingeCylinder", p3(-100, HINGE_Y, hz), p3(100, HINGE_Y, hz), HINGE_HOLE_D));
    return body;
}

/** Open-top servo cradle on the +x (sx = 1) or -x side (baseplate.py _servo_frame). */
function servoFrame(context is Context, id is Id, sx is number, drop is number) returns Query
{
    const c = CASE_CLEARANCE;
    const topZ = SERVO_CASE_Z[1] + c - drop;
    const x0 = sx > 0 ? POST_X[0] : -POST_X[1];
    const x1 = sx > 0 ? POST_X[1] : -POST_X[0];
    const sk = newSketchOnPlane(context, id + "sketch", { "sketchPlane" : yzPlane(x0) });
    skPolyline(sk, "outline", { "points" : closedPolyline([[BOARD_EDGE_Y, PLATE_T], [FRAME_FOOT_REAR_Y, PLATE_T],
                                [REAR_POST_Y1, topZ], [FRAME_FRONT_POST_Y, topZ],
                                [FRAME_FRONT_POST_Y, FRAME_FRONT_POST_FOOT_Z - drop]]) });
    skSolve(sk);
    const frame = extrudeSketch(context, id, vector(1, 0, 0), x1 - x0);
    const slotX0 = sx > 0 ? POST_X[0] - 10 : -(POST_X[0] - 10) - 30;
    cutAway(context, id + "caseSlot", frame, makeBox(context, id + "caseSlotBox",
            [slotX0, SERVO_CASE_Y[0] - c, SERVO_CASE_Z[0] - c - drop],
            [slotX0 + 30, SERVO_CASE_Y[1] + c, SERVO_CASE_Z[0] - c - drop + 60]));
    const xm = sx * (POST_X[0] + POST_X[1]) / 2;
    var holes = [];
    for (var i = 0; i < size(POST_HOLE_YS); i += 1)
    {
        for (var j = 0; j < size(POST_HOLE_ZS); j += 1)
        {
            const y = FLIP_Y - POST_HOLE_YS[i];
            const z = FLIP_Z - POST_HOLE_ZS[j] - drop;
            holes = append(holes, makeCylinder(context, id + ("earHole" ~ i ~ j), p3(xm - 15, y, z), p3(xm + 15, y, z), CRADLE_HOLE_D));
        }
    }
    cutAway(context, id + "earHoles", frame, qUnion(holes));
    return frame;
}

/** The pocket under the mounting plate's floor (baseplate.py _relief). */
function relief(context is Context, id is Id) returns Query
{
    const m = RELIEF_MARGIN;
    const ms = m + RELIEF_SWING;
    const wFull = 54.1 + m;
    const wRear = 34.0 + m;
    const chamfer = 54.1 + 82.4 + ms * sqrt(2);      // x + y on the chamfer
    const tabY = [122.73 - m, 140.73 + ms];
    const rearY = 175.4 + 5.0;
    const half = [[0, RELIEF_BEHIND_TOWER_Y], [wFull, RELIEF_BEHIND_TOWER_Y], [wFull, chamfer - wFull],
                  [wRear, chamfer - wRear], [wRear, tabY[0]], [wFull, tabY[0]], [wFull, tabY[1]],
                  [wRear, tabY[1]], [wRear, rearY], [0, rearY]];
    var outline = [];
    for (var i = 1; i < size(half) - 1; i += 1)
        outline = append(outline, half[i]);
    for (var i = size(half) - 2; i >= 1; i -= 1)
        outline = append(outline, [-half[i][0], half[i][1]]);
    const h = PLATE_T + 1.0 - RELIEF_Z;
    const sk = newSketchOnPlane(context, id + "sketch", { "sketchPlane" : plane(p3(0, 0, RELIEF_Z), vector(0, 0, 1), vector(1, 0, 0)) });
    skPolyline(sk, "outline", { "points" : closedPolyline(outline) });
    skSolve(sk);
    var tools = [extrudeSketch(context, id, vector(0, 0, 1), h)];
    // forward to the gear blocks' tongues, outside the towers' feet
    tools = append(tools, makeBox(context, id + "tonguePos", [TOWER_X[1], RELIEF_TONGUE_Y, RELIEF_Z],
                                  [wFull, RELIEF_BEHIND_TOWER_Y + 1.0, RELIEF_Z + h]));
    tools = append(tools, makeBox(context, id + "tongueNeg", [-wFull, RELIEF_TONGUE_Y, RELIEF_Z],
                                  [-TOWER_X[1], RELIEF_BEHIND_TOWER_Y + 1.0, RELIEF_Z + h]));
    return qUnion(tools);
}

annotation { "Feature Type Name" : "Lower hinge (text-to-cad)" }
export const lowerHingeT2C = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Baseplate", "Filter" : EntityType.BODY && BodyType.SOLID, "MaxNumberOfPicks" : 1 }
        definition.baseplate is Query;

        annotation { "Name" : "Drop" }
        isLength(definition.drop, { (millimeter) : [0, 5, 6.3] } as LengthBoundSpec);
    }
    {
        const drop = definition.drop / millimeter;
        const base = definition.baseplate;
        // 1. the old towers and cradles off, at the table top
        cutAway(context, id + "cutOld", base, qUnion([
                    makeBox(context, id + "oldTowerPos", [28.8, 20, PLATE_T], [41.3, 100, 60]),
                    makeBox(context, id + "oldTowerNeg", [-41.3, 20, PLATE_T], [-28.8, 100, 60]),
                    makeBox(context, id + "oldFramePos", [67.0, 20, PLATE_T], [72.2, 110, 90]),
                    makeBox(context, id + "oldFrameNeg", [-72.2, 20, PLATE_T], [-67.0, 110, 90])]));
        // 2. the plate: slot, relief, notches
        cutAway(context, id + "slot", base, makeBox(context, id + "slotBox",
                [-SLOT_HALF_W, BOARD_EDGE_Y - 1.0, -6], [SLOT_HALF_W, SLOT_END_Y, 12]));
        cutAway(context, id + "relief", base, relief(context, id + "reliefTool"));
        var notches = [];
        for (var i = 0; i < size(REAR_HEADS); i += 1)
            notches = append(notches, makeCylinder(context, id + ("notch" ~ i),
                             p3(REAR_HEADS[i][0], REAR_HEADS[i][1], -9), p3(REAR_HEADS[i][0], REAR_HEADS[i][1], 9), HEAD_NOTCH_D));
        cutAway(context, id + "notches", base, qUnion(notches));
        // 3. the towers and cradles, drop lower
        opBoolean(context, id + "union", { "operationType" : BooleanOperationType.UNION, "tools" : qUnion([base,
                  tower(context, id + "towerPos", TOWER_X[0], TOWER_X[1], drop),
                  tower(context, id + "towerNeg", -TOWER_X[1], -TOWER_X[0], drop),
                  servoFrame(context, id + "framePos", 1, drop),
                  servoFrame(context, id + "frameNeg", -1, drop)]) });
    });

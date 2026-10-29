FeatureScript 3083;
import(path : "onshape/std/common.fs", version : "3083.0");

// Tap collar of the powder doser as a native Onshape feature tree (issue #172), pushed with fsgen 0.2.0.
// Same part as cad/text-to-cad/src/parts/tap_collar.py (PR #176), which matches the lab's Fusion 360 part
// tapcollar_v1: a split clamp ring on the auger tube that carries the tapping solenoid.
//   bore axis = Y axis (x = 0, z = 0); the collar runs along +Y from y = 0 to #collarDepth
//   +Z up: the block and the thin solenoid plate rise above the ring, the split clamp ear points to -X,
//   the tab with the keyhole pocket to +X
// Added features sink SINK into the body they join, so no faces only touch.
export function build(context is Context, id is Id)
{
    // ---------- variables (one Variable Studio) ----------
    variable(context, "collarDepth", 17 * millimeter);         // along the bore axis (Y)
    variable(context, "boreDiameter", 25.5 * millimeter);      // clamp bore on the 25 mm auger tube
    variable(context, "ringDiameter", 33.5 * millimeter);
    variable(context, "blockWidth", 25.4 * millimeter);        // block and solenoid plate width (X)
    variable(context, "blockHeight", 24.5 * millimeter);       // block top, above the bore axis
    variable(context, "plateThickness", 1.2 * millimeter);     // solenoid plate, flush with the +Y face
    variable(context, "plateTop", 53.35 * millimeter);         // plate top, above the bore axis
    variable(context, "solenoidHeight", 41 * millimeter);      // centre of the solenoid's two M3 holes
    variable(context, "plateHoleDiameter", 3.2 * millimeter);  // M3 clearance, through the plate (Y)
    variable(context, "tapHoleDiameter", 6.9 * millimeter);    // vertical hole from the block top into the bore
    variable(context, "earLength", 26 * millimeter);           // clamp ear end, from the bore axis (-X)
    variable(context, "earHeight", 13.8 * millimeter);
    variable(context, "splitWidth", 2.2 * millimeter);         // clamp split, from the ear end into the bore
    variable(context, "clampHoleOffset", 20.2 * millimeter);   // M3 clamp screw through the ear (Z), from the axis
    variable(context, "clampHoleDiameter", 3.4 * millimeter);
    variable(context, "tabLength", 19.95 * millimeter);        // tab end, from the bore axis (+X)
    variable(context, "tabHeight", 10.8 * millimeter);
    variable(context, "pocketDiameter", 10.5 * millimeter);    // keyhole pocket in the tab's end face
    variable(context, "pocketDepth", 2.5 * millimeter);

    const mm = millimeter;
    const zero = 0 * millimeter;
    const SINK = 0.5 * millimeter;
    const topPlane = qCreatedBy(makeId("Top"), EntityType.FACE);
    const frontPlane = qCreatedBy(makeId("Front"), EntityType.FACE);
    const rightPlane = qCreatedBy(makeId("Right"), EntityType.FACE);
    const midY = #collarDepth / 2;                             // mid-plane of the holes across the collar
    const collar = qCreatedBy(id + "Collar", EntityType.BODY);

    // ---------- collar: ring, block, clamp ear and tab in one Front-plane sketch, extruded along +Y ----------
    // Front plane: sketch x -> world X, sketch y -> world Z, normal -Y (so "oppositeDirection" extrudes along +Y).
    // The ear and the tab start on the bore axis; the bore cut below trims their inner ends.
    var collarSk = newSketch(context, id + "Collar sketch", { "sketchPlane" : frontPlane });
    skCircle(collarSk, "ring", { "center" : vector(zero, zero), "radius" : #ringDiameter / 2 });
    skRectangle(collarSk, "block", { "firstCorner" : vector(-#blockWidth / 2, zero), "secondCorner" : vector(#blockWidth / 2, #blockHeight) });
    skRectangle(collarSk, "ear", { "firstCorner" : vector(-#earLength, -#earHeight / 2), "secondCorner" : vector(zero, #earHeight / 2) });
    skRectangle(collarSk, "tab", { "firstCorner" : vector(zero, -#tabHeight / 2), "secondCorner" : vector(#tabLength, #tabHeight / 2) });
    skSolve(collarSk);
    extrude(context, id + "Collar", {
        "entities" : qSketchRegion(id + "Collar sketch"),
        "endBound" : BoundingType.BLIND,
        "depth" : #collarDepth,
        "oppositeDirection" : true });

    // ---------- solenoid plate: a thin wall on the +Y face, from the block top up to #plateTop ----------
    // Right plane: sketch x -> world Y, sketch y -> world Z; extruded #blockWidth / 2 to each side of x = 0
    var plateSk = newSketch(context, id + "Solenoid plate sketch", { "sketchPlane" : rightPlane });
    skRectangle(plateSk, "plate", { "firstCorner" : vector(#collarDepth - #plateThickness, #blockHeight - SINK),
                "secondCorner" : vector(#collarDepth, #plateTop) });
    skSolve(plateSk);
    extrude(context, id + "Solenoid plate", {
        "entities" : qSketchRegion(id + "Solenoid plate sketch"),
        "operationType" : NewBodyOperationType.ADD,
        "endBound" : BoundingType.BLIND,
        "depth" : #blockWidth / 2,
        "hasSecondDirection" : true,
        "secondDirectionBound" : BoundingType.BLIND,
        "secondDirectionDepth" : #blockWidth / 2,
        "defaultScope" : false,
        "booleanScope" : collar });

    // ---------- cuts along Y, through everything: the clamp bore, the clamp split (from beyond the ear end
    //            into the bore) and the solenoid's two M3 holes in the plate (a diagonal pair about its centre) ----------
    var boreSk = newSketch(context, id + "Bore split and plate holes sketch", { "sketchPlane" : frontPlane });
    skCircle(boreSk, "bore", { "center" : vector(zero, zero), "radius" : #boreDiameter / 2 });
    skRectangle(boreSk, "split", { "firstCorner" : vector(-#earLength - 1 * mm, -#splitWidth / 2), "secondCorner" : vector(zero, #splitWidth / 2) });
    skCircle(boreSk, "plateHoleUpper", { "center" : vector(9.1 * mm, #solenoidHeight + 8 * mm), "radius" : #plateHoleDiameter / 2 });
    skCircle(boreSk, "plateHoleLower", { "center" : vector(-9.1 * mm, #solenoidHeight - 8 * mm), "radius" : #plateHoleDiameter / 2 });
    skSolve(boreSk);
    extrude(context, id + "Bore split and plate holes", {
        "entities" : qSketchRegion(id + "Bore split and plate holes sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,
        "oppositeDirection" : true,
        "defaultScope" : false,
        "booleanScope" : collar });

    // ---------- vertical holes on the collar's mid-plane: the tap hole up from the bore through the block,
    //            and the M3 clamp hole through the ear. One cut, up through all and down past the ear's
    //            underside (below the axis the tap hole lies inside the bore, so it cuts nothing there) ----------
    var holeSk = newSketch(context, id + "Tap and clamp hole sketch", { "sketchPlane" : topPlane });
    skCircle(holeSk, "tapHole", { "center" : vector(zero, midY), "radius" : #tapHoleDiameter / 2 });
    skCircle(holeSk, "clampHole", { "center" : vector(-#clampHoleOffset, midY), "radius" : #clampHoleDiameter / 2 });
    skSolve(holeSk);
    extrude(context, id + "Tap and clamp holes", {
        "entities" : qSketchRegion(id + "Tap and clamp hole sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,
        "hasSecondDirection" : true,
        "secondDirectionBound" : BoundingType.BLIND,
        "secondDirectionDepth" : #earHeight / 2 + 1 * mm,
        "defaultScope" : false,
        "booleanScope" : collar });

    // ---------- keyhole pocket in the tab's end face: a round seat plus a 4 mm slot through the tab's height ----------
    // pocket floor #pocketDepth inside the tab end; on it (like Right) sketch x -> world Y, sketch y -> world Z;
    // cut along +X, out through the tab end
    cPlane(context, id + "Pocket floor plane", { "entities" : rightPlane, "offset" : #tabLength - #pocketDepth });
    var pocketSk = newSketch(context, id + "Keyhole pocket sketch", { "sketchPlane" : qCreatedBy(id + "Pocket floor plane", EntityType.FACE) });
    skCircle(pocketSk, "seat", { "center" : vector(midY, zero), "radius" : #pocketDiameter / 2 });
    skRectangle(pocketSk, "slot", { "firstCorner" : vector(midY - 2 * mm, -#tabHeight / 2 - 1 * mm),
                "secondCorner" : vector(midY + 2 * mm, #tabHeight / 2 + 1 * mm) });
    skSolve(pocketSk);
    extrude(context, id + "Keyhole pocket", {
        "entities" : qSketchRegion(id + "Keyhole pocket sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,
        "defaultScope" : false,
        "booleanScope" : collar });
}

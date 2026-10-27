FeatureScript 3083;
import(path : "onshape/std/common.fs", version : "3083.0");

// Auger tube of the powder doser as a native Onshape feature tree (issue #172), pushed with fsgen 0.2.0.
// Same part as cad/text-to-cad/src/parts/auger.py (PR #176), which matches the lab's Fusion 360 body "Shaft":
// tube axis +Z, outlet face at z = 0, cap end at z = #tubeLength.
//   z = 0 .. #funnelLength      outlet funnel: the bore closes in a cone to the outlet hole, around the
//                                conical tip of a central core
//   z = 0 .. pitch x turns      right-handed helical flight from the core tip radius to the bore wall,
//                                starting on +X at the outlet face
//   #gearCenter                 44T module-1 spur gear (meshes the 20T stepper pinion)
//   last #threadLength          3.5 mm-pitch right-handed thread for the screw cap
// Added features sink SINK into the wall they join, so no faces only touch.
export function build(context is Context, id is Id)
{
    // ---------- variables (one Variable Studio) ----------
    variable(context, "tubeLength", 250 * millimeter);
    variable(context, "tubeDiameter", 25 * millimeter);
    variable(context, "wallThickness", 2 * millimeter);
    variable(context, "funnelLength", 12 * millimeter);         // outlet cone, from the outlet face
    variable(context, "outletDiameter", 3 * millimeter);        // hole in the outlet face
    variable(context, "coreDiameter", 8 * millimeter);
    variable(context, "coreTipDiameter", 0.8 * millimeter);     // core tip at the outlet face
    variable(context, "flightPitch", 10.41625 * millimeter);    // 83.33 mm over 8 turns
    variable(context, "flightTurns", 8);
    variable(context, "flightThickness", 0.5 * millimeter);     // axial
    variable(context, "gearCenter", 83.333 * millimeter);       // gear mid-plane, from the outlet face
    variable(context, "gearWidth", 10 * millimeter);
    variable(context, "threadLength", 25 * millimeter);         // reduced diameter at the cap end
    variable(context, "threadPitch", 3.5 * millimeter);
    variable(context, "threadMajorDiameter", 26 * millimeter);
    variable(context, "threadMinorDiameter", 23 * millimeter);

    const mm = millimeter;
    const zero = 0 * millimeter;
    const SINK = 0.5 * millimeter;
    const topPlane = qCreatedBy(makeId("Top"), EntityType.FACE);
    const frontPlane = qCreatedBy(makeId("Front"), EntityType.FACE);

    const rOutlet = #outletDiameter / 2;
    const rTube = #tubeDiameter / 2;
    const rBore = #tubeDiameter / 2 - #wallThickness;
    const rThread = #threadMinorDiameter / 2;
    const rCrest = #threadMajorDiameter / 2;
    const rCore = #coreDiameter / 2;
    const rTip = #coreTipDiameter / 2;
    const flightRise = #flightPitch * #flightTurns;
    const shoulderZ = #tubeLength - #threadLength;

    // ---------- core: conical tip inside the funnel, then a plain shaft up to the end of the flight ----------
    // half-sections on the Front plane: sketch x -> world X (radius), sketch y -> world Z
    var coreSk = newSketch(context, id + "Core sketch", { "sketchPlane" : frontPlane });
    skPolyline(coreSk, "core", { "points" : [
            vector(zero, zero), vector(rTip, zero), vector(rCore, #funnelLength), vector(rCore, flightRise),
            vector(zero, flightRise), vector(zero, zero)] });
    skLineSegment(coreSk, "axis", { "start" : vector(zero, zero), "end" : vector(zero, 10 * mm), "construction" : true });
    skSolve(coreSk);
    const axis = sketchEntityQuery(id + "Core sketch", EntityType.EDGE, "axis");
    revolve(context, id + "Core", {
        "entities" : qSketchRegion(id + "Core sketch"),
        "axis" : axis,
        "fullRevolve" : true });

    // ---------- flight: radial blade swept along a right-handed helix from +X at the outlet face ----------
    var flightHelixSk = newSketch(context, id + "Flight helix sketch", { "sketchPlane" : topPlane });
    skCircle(flightHelixSk, "circle", { "center" : vector(zero, zero), "radius" : rCore });
    skSolve(flightHelixSk);
    helix(context, id + "Flight helix", {
        "axisType" : AxisType.CIRCLE,
        "edge" : sketchEntityQuery(id + "Flight helix sketch", EntityType.EDGE, "circle"),
        "pathType" : PathType.TURNS_PITCH,
        "revolutions" : #flightTurns,
        "helicalPitch" : #flightPitch,
        "handedness" : Direction.CW });
    var flightSk = newSketch(context, id + "Flight profile", { "sketchPlane" : frontPlane });
    skRectangle(flightSk, "blade", { "firstCorner" : vector(rTip, zero), "secondCorner" : vector(rBore + SINK, #flightThickness) });
    skSolve(flightSk);
    sweep(context, id + "Flight", {
        "profiles" : qSketchRegion(id + "Flight profile"),
        "path" : qCreatedBy(id + "Flight helix", EntityType.EDGE),
        "operationType" : NewBodyOperationType.ADD,
        "defaultScope" : true });

    // ---------- tube around the flight: outlet funnel, bore, shoulder and the reduced cap end ----------
    var tubeSk = newSketch(context, id + "Tube sketch", { "sketchPlane" : frontPlane });
    skPolyline(tubeSk, "wall", { "points" : [
            vector(rOutlet, zero), vector(rTube, zero), vector(rTube, shoulderZ), vector(rThread, shoulderZ),
            vector(rThread, #tubeLength), vector(rBore, #tubeLength), vector(rBore, #funnelLength),
            vector(rOutlet, zero)] });
    skSolve(tubeSk);
    revolve(context, id + "Tube", {
        "entities" : qSketchRegion(id + "Tube sketch"),
        "axis" : axis,
        "operationType" : NewBodyOperationType.ADD,
        "fullRevolve" : true,
        "defaultScope" : true });

    // ---------- drive gear: blank, one tooth gap, patterned around the axis ----------
    // module 1, 44 teeth, 20 deg: fixed by the stepper pinion; tooth 0 is centred on +X
    cPlane(context, id + "Gear plane", { "entities" : topPlane, "offset" : #gearCenter - #gearWidth / 2 });
    var blankSk = newSketch(context, id + "Gear blank sketch", { "sketchPlane" : qCreatedBy(id + "Gear plane", EntityType.FACE) });
    skCircle(blankSk, "tip", { "center" : vector(zero, zero), "radius" : 23 * mm });
    skCircle(blankSk, "hub", { "center" : vector(zero, zero), "radius" : rTube - SINK });
    skSolve(blankSk);
    extrude(context, id + "Gear blank", {
        "entities" : qSketchRegion(id + "Gear blank sketch", true),
        "operationType" : NewBodyOperationType.ADD,
        "endBound" : BoundingType.BLIND,
        "depth" : #gearWidth,
        "defaultScope" : true });
    var gapSk = newSketch(context, id + "Tooth gap sketch", { "sketchPlane" : qCreatedBy(id + "Gear plane", EntityType.FACE) });
    // ---- generated by tooth_gap.py (module 1, 44 teeth, 20 deg); do not edit by hand ----
    skArc(gapSk, "flankA", { "start" : vector(23.499629023, 0.132044685) * mm, "mid" : vector(22.151393387, 0.729546390) * mm, "end" : vector(21.201260099, 0.987633599) * mm });
    skArc(gapSk, "filletA", { "start" : vector(21.201260099, 0.987633599) * mm, "mid" : vector(20.918804812, 1.146264181) * mm, "end" : vector(20.792868733, 1.444734874) * mm });
    skArc(gapSk, "rootLand", { "start" : vector(20.792868733, 1.444734874) * mm, "mid" : vector(20.789894425, 1.486922595) * mm, "end" : vector(20.786834520, 1.529104195) * mm });
    skArc(gapSk, "filletB", { "start" : vector(20.786834520, 1.529104195) * mm, "mid" : vector(20.869011943, 1.842459459) * mm, "end" : vector(21.126016756, 2.039672989) * mm });
    skArc(gapSk, "flankB", { "start" : vector(21.126016756, 2.039672989) * mm, "mid" : vector(22.029749419, 2.430351308) * mm, "end" : vector(23.279228601, 3.213645243) * mm });
    skLineSegment(gapSk, "outside", { "start" : vector(23.279228601, 3.213645243) * mm, "end" : vector(23.499629023, 0.132044685) * mm });
    // ---- end of generated block ----
    skSolve(gapSk);
    extrude(context, id + "Tooth gap", {
        "entities" : qSketchRegion(id + "Tooth gap sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,
        "defaultScope" : true });
    circularPattern(context, id + "Gear teeth", {
        "patternType" : PatternType.FEATURE,
        "instanceFunction" : [id + "Tooth gap"],
        "axis" : axis,
        "angle" : 360 * degree,
        "instanceCount" : 44,
        "equalSpace" : true });

    // ---------- cap thread: rounded trapezoid swept along a right-handed helix, trimmed at the cap end ----------
    // tooth 2 mm wide on the minor diameter, flanks 9.46 deg off radial, 0.5 mm crest rounds; its crest
    // centre starts on +X 1.65 mm below the shoulder
    const zThread = shoulderZ - 1.65 * mm;
    cPlane(context, id + "Thread plane", { "entities" : topPlane, "offset" : zThread });
    var threadHelixSk = newSketch(context, id + "Thread helix sketch", { "sketchPlane" : qCreatedBy(id + "Thread plane", EntityType.FACE) });
    skCircle(threadHelixSk, "circle", { "center" : vector(zero, zero), "radius" : rThread });
    skSolve(threadHelixSk);
    helix(context, id + "Thread helix", {
        "axisType" : AxisType.CIRCLE,
        "edge" : sketchEntityQuery(id + "Thread helix sketch", EntityType.EDGE, "circle"),
        "pathType" : PathType.TURNS_PITCH,
        "revolutions" : (#threadLength + 3 * mm) / #threadPitch,
        "helicalPitch" : #threadPitch,
        "handedness" : Direction.CW });
    var threadSk = newSketch(context, id + "Thread profile", { "sketchPlane" : frontPlane });
    const rIn = rThread - SINK;
    skLineSegment(threadSk, "lowerFlank", { "start" : vector(rIn, zThread - 1.083333 * mm), "end" : vector(rCrest - 0.417797 * mm, zThread - 0.819634 * mm) });
    skArc(threadSk, "lowerRound", { "start" : vector(rCrest - 0.417797 * mm, zThread - 0.819634 * mm),
            "mid" : vector(rCrest - 0.118492 * mm, zThread - 0.649622 * mm), "end" : vector(rCrest, zThread - 0.326438 * mm) });
    skLineSegment(threadSk, "crest", { "start" : vector(rCrest, zThread - 0.326438 * mm), "end" : vector(rCrest, zThread + 0.326438 * mm) });
    skArc(threadSk, "upperRound", { "start" : vector(rCrest, zThread + 0.326438 * mm),
            "mid" : vector(rCrest - 0.118492 * mm, zThread + 0.649622 * mm), "end" : vector(rCrest - 0.417797 * mm, zThread + 0.819634 * mm) });
    skLineSegment(threadSk, "upperFlank", { "start" : vector(rCrest - 0.417797 * mm, zThread + 0.819634 * mm), "end" : vector(rIn, zThread + 1.083333 * mm) });
    skLineSegment(threadSk, "root", { "start" : vector(rIn, zThread + 1.083333 * mm), "end" : vector(rIn, zThread - 1.083333 * mm) });
    skSolve(threadSk);
    sweep(context, id + "Thread", {
        "profiles" : qSketchRegion(id + "Thread profile"),
        "path" : qCreatedBy(id + "Thread helix", EntityType.EDGE),
        "operationType" : NewBodyOperationType.ADD,
        "defaultScope" : true });
    var trimSk = newSketch(context, id + "Thread trim sketch", { "sketchPlane" : frontPlane });
    skRectangle(trimSk, "overrun", { "firstCorner" : vector(rBore, #tubeLength), "secondCorner" : vector(rCrest + 1 * mm, #tubeLength + 2 * #threadPitch) });
    skSolve(trimSk);
    revolve(context, id + "Thread trim", {
        "entities" : qSketchRegion(id + "Thread trim sketch"),
        "axis" : axis,
        "operationType" : NewBodyOperationType.REMOVE,
        "fullRevolve" : true,
        "defaultScope" : true });
}

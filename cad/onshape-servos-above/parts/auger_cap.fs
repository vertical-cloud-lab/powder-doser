FeatureScript 3083;
import(path : "onshape/std/common.fs", version : "3083.0");

// Auger cap of the powder doser as a native Onshape feature tree (issue #172), pushed with fsgen 0.2.0.
// Same part as cad/text-to-cad/src/parts/auger_cap.py (PR #176), which matches the lab's Fusion 360 body "Cap":
// the screw-on cap closing the reservoir end of the auger tube.
//   axis +Z; inner face of the end wall at z = 0, open rim at z = -#capDepth, top outside at z = #endWall;
//   the top outer edge is a 45 deg chamfer over the whole end-wall height
//   internal thread: the auger's thread tooth (parts/auger.fs: 3.5 mm pitch, right-handed, 26 / 23 mm) grown by
//   #threadClearance normal to its flanks, cut as a helical groove around the plain #capMinorDiameter bore; it
//   runs out through the rim and stops at the inner end face. A groove centre lies on +X at z = #threadPhase
//   (mod #threadPitch). In the doser the cap sits on the tube end (auger z = #tubeLength) turned 180 deg about Z
//   (text-to-cad frames.py, CAP_TURN_DEG), which puts this groove on the auger's thread.
// Order: solid blank, groove, end wall added back where the groove's run-out cut it, then the bore. (Cutting the
// groove into an already bored cup is the same part, but the local OpenCascade build fails on it.)
export function build(context is Context, id is Id)
{
    // ---------- variables (one Variable Studio) ----------
    variable(context, "capDiameter", 29 * millimeter);
    variable(context, "capDepth", 25 * millimeter);              // inner end face to rim (= auger thread length)
    variable(context, "endWall", 2 * millimeter);                // end wall thickness = top chamfer height
    variable(context, "capMinorDiameter", 23.5 * millimeter);    // internal-thread crest (plain bore)
    variable(context, "threadPitch", 3.5 * millimeter);          // the auger's cap thread, right-handed
    variable(context, "threadMajorDiameter", 26 * millimeter);   // auger thread crest
    variable(context, "threadMinorDiameter", 23 * millimeter);   // auger thread root
    variable(context, "threadClearance", 0.5 * millimeter);      // groove = auger tooth grown by this, normal to the flanks
    variable(context, "threadPhase", -0.4 * millimeter);         // groove centre on +X, from the inner end face

    const mm = millimeter;
    const zero = 0 * millimeter;
    const SINK = 0.5 * millimeter;
    const topPlane = qCreatedBy(makeId("Top"), EntityType.FACE);
    const frontPlane = qCreatedBy(makeId("Front"), EntityType.FACE);
    const cap = qCreatedBy(id + "Cap", EntityType.BODY);

    const rCap = #capDiameter / 2;
    const rBore = #capMinorDiameter / 2;

    // ---------- cap blank: solid half-section on the Front plane (sketch x -> world X = radius, sketch y -> world Z) ----------
    var capSk = newSketch(context, id + "Cap sketch", { "sketchPlane" : frontPlane });
    skPolyline(capSk, "outline", { "points" : [
            vector(zero, -#capDepth), vector(rCap, -#capDepth), vector(rCap, zero), vector(rCap - #endWall, #endWall),
            vector(zero, #endWall), vector(zero, -#capDepth)] });
    skLineSegment(capSk, "axis", { "start" : vector(zero, zero), "end" : vector(zero, 10 * mm), "construction" : true });
    skSolve(capSk);
    const axis = sketchEntityQuery(id + "Cap sketch", EntityType.EDGE, "axis");
    revolve(context, id + "Cap", {
        "entities" : qSketchRegion(id + "Cap sketch"),
        "axis" : axis,
        "fullRevolve" : true });

    // ---------- internal thread: groove swept along a right-handed helix from below the rim to above the top ----------
    // The helix starts on +X, 8 pitches below #threadPhase (below the rim for a cap up to 26 mm deep), and makes
    // 10 turns, ending above the cap: the groove has no end inside the part. (9 turns reach far enough too, but
    // then the local OpenCascade build fails where the sweep ends just above the inner end face.)
    const zGroove = #threadPhase - 8 * #threadPitch;
    cPlane(context, id + "Thread plane", { "entities" : topPlane, "offset" : zGroove });
    var helixSk = newSketch(context, id + "Thread helix sketch", { "sketchPlane" : qCreatedBy(id + "Thread plane", EntityType.FACE) });
    skCircle(helixSk, "circle", { "center" : vector(zero, zero), "radius" : rBore });
    skSolve(helixSk);
    helix(context, id + "Thread helix", {
        "axisType" : AxisType.CIRCLE,
        "edge" : sketchEntityQuery(id + "Thread helix sketch", EntityType.EDGE, "circle"),
        "pathType" : PathType.TURNS_PITCH,
        "revolutions" : 10,
        "helicalPitch" : #threadPitch,
        "handedness" : Direction.CW });

    // Groove section at the helix start, centred at z = zGroove on +X. Auger tooth: 2 mm wide on the minor
    // diameter, flanks 1/6 axial per radial (9.46 deg off radial), 0.5 mm crest rounds. Grown by c =
    // #threadClearance: the flanks move out by c (axially c * 1.013794), the crest becomes the groove bottom on
    // #threadMajorDiameter / 2 + c, and the rounds keep their centres (radius 0.5 mm + c). The inner side lies
    // SINK inside the bore, so the groove opens into it.
    const rIn = rBore - SINK;
    const rBottom = #threadMajorDiameter / 2 + #threadClearance;
    const rRound = #threadMajorDiameter / 2 - 0.5 * mm;              // radius of the corner-round centres
    const rCorner = 0.5 * mm + #threadClearance;                     // corner-round radius
    const hIn = 1 * mm + (#threadMinorDiameter / 2 - rIn) / 6 + 1.013794 * #threadClearance;  // half-width at rIn
    const hRound = 0.576436 * mm - (#threadMajorDiameter - #threadMinorDiameter) / 12;       // round centres, from zGroove
    var grooveSk = newSketch(context, id + "Thread groove profile", { "sketchPlane" : frontPlane });
    skLineSegment(grooveSk, "lowerFlank", { "start" : vector(rIn, zGroove - hIn),
            "end" : vector(rRound + 0.164399 * rCorner, zGroove - hRound - 0.986394 * rCorner) });
    skArc(grooveSk, "lowerRound", { "start" : vector(rRound + 0.164399 * rCorner, zGroove - hRound - 0.986394 * rCorner),
            "mid" : vector(rRound + 0.763020 * rCorner, zGroove - hRound - 0.646375 * rCorner), "end" : vector(rBottom, zGroove - hRound) });
    skLineSegment(grooveSk, "bottom", { "start" : vector(rBottom, zGroove - hRound), "end" : vector(rBottom, zGroove + hRound) });
    skArc(grooveSk, "upperRound", { "start" : vector(rBottom, zGroove + hRound),
            "mid" : vector(rRound + 0.763020 * rCorner, zGroove + hRound + 0.646375 * rCorner),
            "end" : vector(rRound + 0.164399 * rCorner, zGroove + hRound + 0.986394 * rCorner) });
    skLineSegment(grooveSk, "upperFlank", { "start" : vector(rRound + 0.164399 * rCorner, zGroove + hRound + 0.986394 * rCorner),
            "end" : vector(rIn, zGroove + hIn) });
    skLineSegment(grooveSk, "inner", { "start" : vector(rIn, zGroove + hIn), "end" : vector(rIn, zGroove - hIn) });
    skSolve(grooveSk);
    sweep(context, id + "Thread groove", {
        "profiles" : qSketchRegion(id + "Thread groove profile"),
        "path" : qCreatedBy(id + "Thread helix", EntityType.EDGE),
        "operationType" : NewBodyOperationType.REMOVE,
        "defaultScope" : false,
        "booleanScope" : cap });

    // ---------- end wall: the groove's run-out also cut through the end wall (z = 0 .. #endWall); adding the
    //            end wall back (same section as the top of the cap sketch) stops the thread at the inner end face ----------
    var endSk = newSketch(context, id + "End wall sketch", { "sketchPlane" : frontPlane });
    skPolyline(endSk, "outline", { "points" : [
            vector(zero, zero), vector(rCap, zero), vector(rCap - #endWall, #endWall), vector(zero, #endWall), vector(zero, zero)] });
    skSolve(endSk);
    revolve(context, id + "End wall", {
        "entities" : qSketchRegion(id + "End wall sketch"),
        "axis" : axis,
        "operationType" : NewBodyOperationType.ADD,
        "fullRevolve" : true,
        "defaultScope" : false,
        "booleanScope" : cap });

    // ---------- bore (the internal thread's crest): from the inner end face down through the rim ----------
    var boreSk = newSketch(context, id + "Bore sketch", { "sketchPlane" : topPlane });
    skCircle(boreSk, "bore", { "center" : vector(zero, zero), "radius" : rBore });
    skSolve(boreSk);
    extrude(context, id + "Bore", {
        "entities" : qSketchRegion(id + "Bore sketch"),
        "operationType" : NewBodyOperationType.REMOVE,
        "endBound" : BoundingType.THROUGH_ALL,
        "oppositeDirection" : true,
        "defaultScope" : false,
        "booleanScope" : cap });
}

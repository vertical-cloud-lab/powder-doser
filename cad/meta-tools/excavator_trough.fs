FeatureScript 2374;
import(path : "onshape/std/geometry.fs", version : "2374.0");

/**
 * powder-excavator trough as a parametric Onshape Custom Feature.
 * Drives every dimension off a single annotated parameter list, which is
 * the same pattern as our CadQuery `ExcavatorParams` dataclass — but here
 * the parameters become a real Onshape feature dialog when this FS file is
 * pasted into a Feature Studio.
 */
annotation { "Feature Type Name" : "Powder-Excavator Trough" }
export const powderExcavatorTrough = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Trough radius" }
        isLength(definition.troughRadius, { (millimeter) : [4.0, 12.0, 50.0] } as LengthBoundSpec);

        annotation { "Name" : "Trough length" }
        isLength(definition.troughLength, { (millimeter) : [10.0, 40.0, 200.0] } as LengthBoundSpec);

        annotation { "Name" : "Wall thickness" }
        isLength(definition.wallThickness, { (millimeter) : [0.8, 1.6, 5.0] } as LengthBoundSpec);
    }
    {
        // Sketch a half-circle profile on the front plane.
        var sk = newSketch(context, id + "profile", { "sketchPlane" : qCreatedBy(makeId("Front"), EntityType.FACE) });
        skArc(sk, "outer", {
            "start" : vector( definition.troughRadius, 0 * millimeter),
            "mid"   : vector( 0 * millimeter, -definition.troughRadius),
            "end"   : vector(-definition.troughRadius, 0 * millimeter)
        });
        skArc(sk, "inner", {
            "start" : vector( definition.troughRadius - definition.wallThickness, 0 * millimeter),
            "mid"   : vector( 0 * millimeter, -(definition.troughRadius - definition.wallThickness)),
            "end"   : vector(-(definition.troughRadius - definition.wallThickness), 0 * millimeter)
        });
        skLineSegment(sk, "lipR", {
            "start" : vector( definition.troughRadius, 0 * millimeter),
            "end"   : vector( definition.troughRadius - definition.wallThickness, 0 * millimeter)
        });
        skLineSegment(sk, "lipL", {
            "start" : vector(-definition.troughRadius, 0 * millimeter),
            "end"   : vector(-(definition.troughRadius - definition.wallThickness), 0 * millimeter)
        });
        skSolve(sk);

        // Extrude the closed annulus-segment along normal.
        opExtrude(context, id + "ext", {
            "entities" : qSketchRegion(id + "profile"),
            "direction" : evPlane(context, { "face" : qCreatedBy(makeId("Front"), EntityType.FACE) }).normal,
            "endBound" : BoundingType.BLIND,
            "endDepth" : definition.troughLength
        });
    });

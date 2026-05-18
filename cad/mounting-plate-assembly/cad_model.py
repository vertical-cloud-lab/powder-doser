"""Parametric CadQuery mirror of the KCL sources in kcl/.

Why this exists
---------------
The zoo.dev account attached to ZOO_API_TOKEN in this Copilot sandbox has
exhausted its included monthly quota (HTTP 402 ``missing_payment_method``),
so the ``zoo kcl export`` and ``zoo kcl snapshot`` calls cannot run here.
Re-implementing the same parts in CadQuery lets us still produce STEP/STL/
PNG artefacts that match the KCL geometry one-for-one, and keeps the design
auditable for review.  When the zoo.dev account is funded, run
``render_with_zoo.sh`` to regenerate the same parts from the .kcl sources.

Coordinate convention (mirrors kcl/params.kcl)
----------------------------------------------
* Auger long axis = +Y, tip at +Y, dispense hole near tip.
* Mounting-plate top surface at Z = 0, bottom at Z = -plateT.
* Hinge axis: along X, passing through the dispense point at
  ``(0, +plateLen/2 + yokeArmLen, hingeZ)`` where ``hingeZ`` is the auger
  centreline (negative).
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

# ---- shared params (mirror of kcl/params.kcl) ----
P = dict(
    augerOd=15.0, augerLen=180.0, dispOffset=12.0, dispHoleDia=8.0,
    m3Clear=3.4, m5Clear=5.4,
    brkPlateW=30.0, brkPlateL=24.0, brkPlateT=4.0,
    brkHoleSpanX=16.0, brkHoleSpanY=22.0,
    tapPlateW=30.0, tapPlateL=24.0, tapPlateT=4.0,
    nemaBody=42.3, nemaHoleSpan=31.0, nemaPilotDia=22.5,
    nemaShaftDia=5.0, nemaShaftLen=24.0,
    plateLen=180.0, plateWidth=70.0, plateT=6.0,
    yokeArmLen=22.0, yokeEyeOd=14.0, yokeEyeId=5.4, yokeEyeGap=24.0,
    plateFillet=4.0,
    brkRearY=-55.0, brkFrontY=+25.0, tapPlateY=+5.0, nemaCentreY=-75.0,
    augerDrop=18.0,
    baseLen=280.0, baseWidth=180.0, baseT=6.0,
    legW=18.0, legT=12.0, legH=95.0,
    clevisT=24.0 - 0.4, clevisH=28.0, clevisRoot=18.0,
    actBodyLen=80.0, actBodyDia=18.0, actStrokeMax=60.0,
    actBaseY=-85.0, actBaseZ=14.0, actRodPlateY=-40.0,
)

HINGE_Z = -(P["plateT"] + P["brkPlateT"] + 12.0 / 2)  # = -16; auger centreline
                                                     # = -plateT − brkPlateT − collarH/2

OUT_STEP = Path(__file__).resolve().parent / "step"
OUT_STL = Path(__file__).resolve().parent / "stl"
OUT_STEP.mkdir(parents=True, exist_ok=True)
OUT_STL.mkdir(parents=True, exist_ok=True)


def _export(part: cq.Workplane, name: str) -> None:
    step_path = OUT_STEP / f"{name}.step"
    stl_path = OUT_STL / f"{name}.stl"
    cq.exporters.export(part, str(step_path))
    cq.exporters.export(part, str(stl_path), tolerance=0.05, angularTolerance=0.2)
    print(f"  wrote {step_path.relative_to(step_path.parent.parent)} + .stl")


# ----------------------------------------------------------------------- parts

def mounting_plate() -> cq.Workplane:
    p = P
    # ---- main rectangular plate, top at Z=0, bottom at Z=-plateT ----
    plate = (
        cq.Workplane("XY")
        .box(p["plateWidth"], p["plateLen"], p["plateT"], centered=(True, True, False))
        .translate((0, 0, -p["plateT"]))
        .edges("|Z").fillet(p["plateFillet"])
    )

    # Powder-fall slot near the +Y front edge.
    slotW = p["yokeEyeGap"]
    slotL = 35.0
    slotY = p["plateLen"] / 2 - slotL / 2 - 1.0
    plate = (
        plate.faces(">Z").workplane()
        .center(0, slotY)
        .rect(slotW, slotL + 2)
        .cutThruAll()
    )

    # ---- yoke arms + eyes (axis = X, centred on the dispense-point Z) ----
    # The eyes hang below the plate so their bore axis passes THROUGH the
    # auger dispense point.  Each yoke side is an L-shaped drop leg in YZ
    # (horizontal arm at plate height + vertical drop down to the eye)
    # extruded in X by yokeEyeOd, plus a YZ-plane eye disc at the bottom.
    armOffsetX = p["yokeEyeGap"] / 2 + p["yokeEyeOd"] / 2
    armW = p["yokeEyeOd"]
    armL = p["yokeArmLen"]
    armY0 = p["plateLen"] / 2 - 2     # horizontal arm starts inside front edge
    eyeY = p["plateLen"] / 2 + armL   # eye centre Y
    eyeZ = HINGE_Z

    # Horizontal portion (continuous with plate, top at Z=0, bot at Z=-plateT)
    for sx in (+armOffsetX, -armOffsetX):
        horiz = (
            cq.Workplane("XY")
            .center(sx, armY0 + (armL + 2) / 2)
            .box(armW, armL + 2, p["plateT"], centered=(True, True, False))
            .translate((0, 0, -p["plateT"]))
        )
        plate = plate.union(horiz)

        # Vertical drop leg at the +Y end: from plate bottom (-plateT) down to
        # eyeZ-yokeEyeOd/2 (so its bottom edge meets the bottom of the eye).
        drop_h = (-p["plateT"]) - (eyeZ - p["yokeEyeOd"] / 2)  # +ve since plate Z higher
        drop = (
            cq.Workplane("XY")
            .center(sx, eyeY - armW / 2 + armW / 2)
            .box(armW, armW, drop_h, centered=(True, True, False))
            .translate((0, 0, eyeZ - p["yokeEyeOd"] / 2))
        )
        plate = plate.union(drop)

        # Eye disc: YZ-plane circle, axis = X, axial extent = yokeEyeOd.
        eye = (
            cq.Workplane("YZ").workplane(offset=sx - p["yokeEyeOd"] / 2)
            .center(eyeY, eyeZ).circle(p["yokeEyeOd"] / 2)
            .extrude(p["yokeEyeOd"])
        )
        plate = plate.union(eye)

        # Hinge pin bore (X-axis, through the eye).
        bore = (
            cq.Workplane("YZ").workplane(offset=sx - p["yokeEyeOd"])
            .center(eyeY, eyeZ).circle(p["yokeEyeId"] / 2)
            .extrude(p["yokeEyeOd"] * 2 + 2)
        )
        plate = plate.cut(bore)

    # ---- mounting holes (bracket front, bracket rear, tap-collar, NEMA) ----
    def _hole(x, y, d):
        return (
            cq.Workplane("XY").center(x, y).circle(d / 2)
            .extrude(-(p["plateT"] + 4)).translate((0, 0, 2))
        )

    hole_centres = []
    for cy in (p["brkFrontY"], p["brkRearY"], p["tapPlateY"]):
        for sy in (-p["brkHoleSpanY"] / 2, +p["brkHoleSpanY"] / 2):
            for sx in (-p["brkHoleSpanX"] / 2, +p["brkHoleSpanX"] / 2):
                hole_centres.append((sx, cy + sy, p["m3Clear"]))

    for sx in (-p["nemaHoleSpan"] / 2, +p["nemaHoleSpan"] / 2):
        for sy in (-p["nemaHoleSpan"] / 2, +p["nemaHoleSpan"] / 2):
            hole_centres.append((sx, p["nemaCentreY"] + sy, p["m3Clear"]))
    hole_centres.append((0, p["nemaCentreY"], p["nemaPilotDia"]))

    for x, y, d in hole_centres:
        plate = plate.cut(_hole(x, y, d))

    # ---- linear-actuator rod-end lug hanging from underside ----
    lugW, lugT, lugH = 10.0, 8.0, 16.0
    lug = (
        cq.Workplane("XY")
        .center(0, p["actRodPlateY"])
        .box(lugW, lugT, lugH, centered=(True, True, False))
        .translate((0, 0, -p["plateT"] - lugH))
    )
    plate = plate.union(lug)
    pivot = (
        cq.Workplane("XZ")
        .center(0, -p["plateT"] - lugH + 5)
        .circle(p["m5Clear"] / 2)
        .extrude(lugT + 4, both=True)
        .translate((0, p["actRodPlateY"], 0))
    )
    plate = plate.cut(pivot)
    return plate


def baseplate() -> cq.Workplane:
    p = P
    base = (
        cq.Workplane("XY")
        .box(p["baseWidth"], p["baseLen"], p["baseT"], centered=(True, True, False))
        .edges("|Z").fillet(6.0)
    )

    # Powder window: directly under the dispense hole / hinge axis at
    # Y = plateLen/2 + yokeArmLen, so falling powder reaches the cup placed
    # on the scale BELOW the baseplate.
    windowW, windowL = 60.0, 60.0
    windowY = p["plateLen"] / 2 + p["yokeArmLen"]   # = 112 mm
    base = (
        base.faces(">Z").workplane()
        .center(0, windowY)
        .rect(windowW, windowL).cutThruAll()
    )

    # 4 corner legs, hanging down from baseplate underside.
    for sx in (+p["baseWidth"] / 2 - p["legW"] / 2, -p["baseWidth"] / 2 + p["legW"] / 2):
        for sy in (+p["baseLen"] / 2 - p["legT"] / 2, -p["baseLen"] / 2 + p["legT"] / 2):
            leg = (
                cq.Workplane("XY")
                .center(sx, sy)
                .box(p["legW"], p["legT"], p["legH"], centered=(True, True, False))
                .translate((0, 0, -p["legH"]))
            )
            base = base.union(leg)

    # ---- central hinge clevis (single tang centred at the dispense-axis Y) ----
    # Sits BETWEEN the mounting-plate yoke eyes.  Top of tang must reach the
    # hinge axis at Z = HINGE_Z (the bore through the tang aligns with the
    # bores through both yoke eyes), so we size the tang's height so its
    # mid-height (where the bore is) is at HINGE_Z.
    clevisY = p["plateLen"] / 2 + p["yokeArmLen"]
    # Baseplate top is at Z=0 (relative to baseplate local frame); we'll
    # translate the whole baseplate down later in build_assembly so that the
    # tang bore aligns with HINGE_Z in the global frame.
    hinge_top_z = p["baseT"] + p["clevisH"]      # local tang top Z
    bore_local_z = hinge_top_z - p["clevisH"] / 2  # local Z of bore == middle of tang
    clevis = (
        cq.Workplane("XY")
        .center(0, clevisY)
        .box(p["clevisT"], p["clevisRoot"], p["clevisH"], centered=(True, True, False))
        .translate((0, 0, p["baseT"]))
        .edges("|Y and >Z").fillet(p["clevisT"] / 2 - 1)
    )
    base = base.union(clevis)
    # Bore: along X axis through the tang at its mid-height.
    clevisBore = (
        cq.Workplane("YZ").workplane(offset=-(p["clevisT"] / 2 + 1))
        .center(clevisY, bore_local_z)
        .circle(p["m5Clear"] / 2)
        .extrude(p["clevisT"] + 2)
    )
    base = base.cut(clevisBore)

    # ---- rear clevis for linear-actuator base ----
    actClevisH, actClevisRoot = 18.0, 14.0
    actClv = (
        cq.Workplane("XY")
        .center(0, p["actBaseY"])
        .box(p["clevisT"], actClevisRoot, actClevisH, centered=(True, True, False))
        .translate((0, 0, p["baseT"]))
    )
    base = base.union(actClv)
    actBore = (
        cq.Workplane("YZ").workplane(offset=-(p["clevisT"] / 2 + 1))
        .center(p["actBaseY"], p["baseT"] + actClevisH - 4)
        .circle(p["m5Clear"] / 2)
        .extrude(p["clevisT"] + 2)
    )
    base = base.cut(actBore)
    return base


def hinge_pin() -> cq.Workplane:
    p = P
    pinLen = p["yokeEyeGap"] + 2 * p["yokeEyeOd"] + 2.0
    pin = cq.Workplane("YZ").circle((p["m5Clear"] - 0.4) / 2).extrude(pinLen)
    pin = pin.union(
        cq.Workplane("YZ").circle(4.5).extrude(-2.5)
    )
    return pin


def linear_actuator() -> cq.Workplane:
    p = P
    body = cq.Workplane("XY").circle(p["actBodyDia"] / 2).extrude(p["actBodyLen"])
    rod = (
        cq.Workplane("XY").circle(p["actBodyDia"] / 4)
        .extrude(p["actBodyLen"] + p["actStrokeMax"] / 2)
    )
    asm = body.union(rod)
    # Base clevis (cross-bore for M5 pin).
    base_clv = (
        cq.Workplane("XY").box(14, 6, 8, centered=(True, True, False))
        .translate((0, 0, -8))
    )
    asm = asm.union(base_clv)
    return asm


def cup_placeholder() -> cq.Workplane:
    outer = cq.Workplane("XY").circle(38 / 2).extrude(45)
    bore = cq.Workplane("XY").circle(32 / 2).extrude(45 - 2.5).translate((0, 0, 2.5))
    return outer.cut(bore)


def scale_placeholder() -> cq.Workplane:
    body = cq.Workplane("XY").box(100, 80, 25, centered=(True, True, False))
    platter = cq.Workplane("XY").circle(50 / 2).extrude(4).translate((0, 0, 25))
    return body.union(platter)


def auger_placeholder() -> cq.Workplane:
    p = P
    # Auger built along +Y so the dispense hole sits at Y near the tip.
    tube = (
        cq.Workplane("XZ").circle(p["augerOd"] / 2)
        .extrude(p["augerLen"])
    )
    # Dispense hole pierces the tube wall in the Z direction near the +Y tip.
    disp = (
        cq.Workplane("XY").circle(p["dispHoleDia"] / 2)
        .extrude((p["augerOd"] + 2), both=True)
        .translate((0, p["augerLen"] - p["dispOffset"], 0))
    )
    return tube.cut(disp)


def bracket_placeholder() -> cq.Workplane:
    p = P
    plate = cq.Workplane("XY").box(p["brkPlateL"], p["brkPlateW"], p["brkPlateT"],
                                   centered=(True, True, False))
    collarOd, collarH = p["augerOd"] + 8.0, 12.0
    collar = (
        cq.Workplane("XY").circle(collarOd / 2).extrude(-collarH)
        .cut(cq.Workplane("XY").circle((p["augerOd"] + 0.4) / 2).extrude(-(collarH + 2)))
    )
    part = plate.union(collar)
    for sx in (-p["brkHoleSpanX"] / 2, +p["brkHoleSpanX"] / 2):
        for sy in (-p["brkHoleSpanY"] / 2, +p["brkHoleSpanY"] / 2):
            part = part.cut(
                cq.Workplane("XY").center(sx, sy).circle(p["m3Clear"] / 2)
                .extrude(-(p["brkPlateT"] + 4)).translate((0, 0, 2))
            )
    return part


def tap_collar_mount_placeholder() -> cq.Workplane:
    p = P
    plate = cq.Workplane("XY").box(p["tapPlateL"], p["tapPlateW"], p["tapPlateT"],
                                   centered=(True, True, False))
    column = (
        cq.Workplane("XY").box(6, 6, 14, centered=(True, True, False))
        .translate((0, 0, -14))
    )
    part = plate.union(column)
    for sx in (-p["brkHoleSpanX"] / 2, +p["brkHoleSpanX"] / 2):
        for sy in (-p["brkHoleSpanY"] / 2, +p["brkHoleSpanY"] / 2):
            part = part.cut(
                cq.Workplane("XY").center(sx, sy).circle(p["m3Clear"] / 2)
                .extrude(-(p["tapPlateT"] + 4)).translate((0, 0, 2))
            )
    return part


def nema17_placeholder() -> cq.Workplane:
    p = P
    body = (
        cq.Workplane("XY").box(p["nemaBody"], p["nemaBody"], 42.0,
                               centered=(True, True, False))
        .translate((0, 0, -42.0))
    )
    shaft = cq.Workplane("XY").circle(p["nemaShaftDia"] / 2).extrude(p["nemaShaftLen"])
    pilot = cq.Workplane("XY").circle(p["nemaPilotDia"] / 2).extrude(2.0)
    return body.union(pilot).union(shaft)


PARTS = {
    "mounting_plate": mounting_plate,
    "baseplate": baseplate,
    "hinge_pin": hinge_pin,
    "linear_actuator_placeholder": linear_actuator,
    "cup_placeholder": cup_placeholder,
    "scale_placeholder": scale_placeholder,
    "auger_placeholder": auger_placeholder,
    "bracket_placeholder": bracket_placeholder,
    "tap_collar_mount_placeholder": tap_collar_mount_placeholder,
    "nema17_placeholder": nema17_placeholder,
}


def main() -> None:
    for name, fn in PARTS.items():
        print(f"Building {name} ...")
        part = fn()
        _export(part, name)
        bb = part.val().BoundingBox()
        print(f"  bbox X[{bb.xmin:.1f},{bb.xmax:.1f}] "
              f"Y[{bb.ymin:.1f},{bb.ymax:.1f}] Z[{bb.zmin:.1f},{bb.zmax:.1f}]")


if __name__ == "__main__":
    main()

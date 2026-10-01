"""Simplified models of the bought-in parts, for the Onshape assembly.

Each is built in its own frame with the output axis on +Z, so the
placement in ``layout.py`` reads like the hardware:

* NEMA 11 stepper, OMC StepperOnline 11HS18-0674S: 28 x 28 x 45 mm body,
  Ø22 x 2 mm pilot, Ø5 x 20 mm D-cut shaft, 4 x M2.5 on a 23 mm square.
  Mounting face at z = 0, body in -z, shaft along +z.
* MG996R servo: 40.7 x 19.7 mm case, 54.5 mm flange 2.5 mm thick, case
  top 37 mm and spline tip 42.9 mm above the bottom.  Flange holes on the
  48.04 x 9.04 mm pattern of the Fusion baseplate's servo posts (the
  servo's own ears are slotted).  Output spline axis is +z through the
  origin, case top at z = 0, case towards +x.
* Adafruit 412 push-pull solenoid (TAU0730TM): 29.7 mm body, 14 x 17 mm
  open frame, Ø6.9 bushing, 51.9 mm long with the plunger, two M3 ears
  diagonally opposite (18.2 mm across, 16.0 mm along), per the datasheet
  numbers recorded in the AI tap-collar CAD (PR #51).  Mounting face is
  the plane y = 0 with the body in -y; plunger axis +z (spring end up),
  body centred on z = 0.

    python3 purchased_parts.py      # -> ../components/purchased/*.step, *.stl
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq

OUT = Path(__file__).resolve().parent.parent / "components" / "purchased"

# NEMA 11, 11HS18-0674S
NEMA11_W = 28.0
NEMA11_L = 45.0
NEMA11_PILOT_D, NEMA11_PILOT_H = 22.0, 2.0
NEMA11_SHAFT_D, NEMA11_SHAFT_L = 5.0, 20.0
NEMA11_HOLE_PITCH = 23.0

# MG996R
SERVO_L, SERVO_W = 40.7, 19.7
SERVO_CASE_H = 37.0
SERVO_TOTAL_H = 42.9
SERVO_FLANGE_L, SERVO_FLANGE_T = 54.5, 2.5
SERVO_FLANGE_Z = 26.5            # flange underside above the case bottom
SERVO_HOLES_L, SERVO_HOLES_W = 48.04, 9.04
SERVO_SPLINE_TO_HOLES = 9.88     # spline axis to the hole-pattern centre
SERVO_SPLINE_D = 5.8

# Adafruit 412 / TAU0730TM
SOL_BODY_L = 29.7
SOL_W, SOL_D = 17.0, 14.0        # across the mounting face, away from it
SOL_LEN_TOTAL = 51.9
SOL_BUSHING_D = 6.9
SOL_PLUNGER_D = 5.0
SOL_HOLE_ACROSS, SOL_HOLE_ALONG = 18.2, 16.0
SOL_BOTTOM_STICKOUT = 6.0        # plunger below the body (push end)


def nema11() -> cq.Workplane:
    body = (cq.Workplane("XY").rect(NEMA11_W, NEMA11_W).extrude(-NEMA11_L)
            .edges("|Z").chamfer(2.5))
    holes = (cq.Workplane("XY").rect(NEMA11_HOLE_PITCH, NEMA11_HOLE_PITCH,
                                     forConstruction=True)
             .vertices().circle(1.25).extrude(-2.5))
    body = body.cut(holes)
    pilot = cq.Workplane("XY").circle(NEMA11_PILOT_D / 2).extrude(NEMA11_PILOT_H)
    shaft = (cq.Workplane("XY").circle(NEMA11_SHAFT_D / 2).extrude(NEMA11_SHAFT_L)
             .cut(cq.Workplane("XY").box(10, 10, 15, centered=(True, True, False))
                  .translate((0, 5 + NEMA11_SHAFT_D / 2 - 0.5, NEMA11_SHAFT_L - 15))))
    return body.union(pilot).union(shaft)


def mg996r() -> cq.Workplane:
    # case centred on the hole pattern, which sits SERVO_SPLINE_TO_HOLES from
    # the spline towards +x
    cx = SERVO_SPLINE_TO_HOLES
    case = (cq.Workplane("XY").box(SERVO_L, SERVO_W, SERVO_CASE_H, centered=(True, True, False))
            .translate((cx, 0, -SERVO_CASE_H)))
    fz = -SERVO_CASE_H + SERVO_FLANGE_Z
    flange = (cq.Workplane("XY").box(SERVO_FLANGE_L, SERVO_W, SERVO_FLANGE_T,
                                     centered=(True, True, False))
              .translate((cx, 0, fz)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            flange = flange.cut(cq.Workplane("XY").circle(2.2).extrude(SERVO_FLANGE_T + 2)
                                .translate((cx + sx * SERVO_HOLES_L / 2,
                                            sy * SERVO_HOLES_W / 2, fz - 1)))
    boss = cq.Workplane("XY").circle(6.5).extrude(1.5)
    spline = (cq.Workplane("XY").polygon(25, SERVO_SPLINE_D).extrude(SERVO_TOTAL_H - SERVO_CASE_H)
              .faces(">Z").hole(2.5, 4.0))
    return case.union(flange).union(boss).union(spline)


def adafruit412() -> cq.Workplane:
    h = SOL_BODY_L
    frame = (cq.Workplane("XY").box(SOL_W, SOL_D, h).translate((0, -SOL_D / 2, 0))
             .cut(cq.Workplane("XY").box(SOL_W + 2, SOL_D - 2.4, h - 2.4)
                  .translate((0, -SOL_D / 2, 0))))
    coil = (cq.Workplane("XY").circle(SOL_D / 2 - 1.4).extrude(h - 3.0)
            .translate((0, -SOL_D / 2, -(h - 3.0) / 2)))
    # two ears, diagonally opposite, on the mounting face
    ears = None
    for sx, sz in ((-1, -1), (1, 1)):
        ear = (cq.Workplane("XZ").center(sx * SOL_HOLE_ACROSS / 2, sz * SOL_HOLE_ALONG / 2)
               .rect(6.0, 6.0).extrude(1.0)            # XZ normal is -Y
               .faces("<Y").workplane().center(0, 0).hole(3.1))
        ears = ear if ears is None else ears.union(ear)
    ears = ears.union(
        cq.Workplane("XY").box(SOL_W, 1.0, h).translate((0, -0.5, 0)))
    axis_y = -SOL_D / 2
    top_len = SOL_LEN_TOTAL - h - SOL_BOTTOM_STICKOUT
    plunger = (cq.Workplane("XY").circle(SOL_PLUNGER_D / 2)
               .extrude(SOL_LEN_TOTAL)
               .translate((0, axis_y, -h / 2 - SOL_BOTTOM_STICKOUT)))
    bushing = (cq.Workplane("XY").circle(SOL_BUSHING_D / 2).extrude(0.5)
               .translate((0, axis_y, -h / 2 - 0.5)))
    spring = None
    for k in range(6):
        turn = (cq.Workplane("XY").circle(4.0).circle(3.2).extrude(0.8)
                .translate((0, axis_y, h / 2 + 1.0 + k * (top_len - 3.0) / 6)))
        spring = turn if spring is None else spring.union(turn)
    cap = (cq.Workplane("XY").circle(4.5).extrude(1.0)
           .translate((0, axis_y, h / 2 + top_len - 1.0)))
    return frame.union(coil).union(ears).union(plunger).union(bushing).union(spring).union(cap)


PARTS = {
    "nema11-11hs18-0674s": (nema11, "NEMA 11 stepper 11HS18-0674S (simplified)"),
    "mg996r-servo": (mg996r, "MG996R servo (simplified)"),
    "adafruit-412-solenoid": (adafruit412, "Adafruit 412 push-pull solenoid (simplified)"),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for stem, (fn, label) in PARTS.items():
        wp = fn()
        cq.exporters.export(wp, str(OUT / f"{stem}.step"))
        cq.exporters.export(wp, str(OUT / f"{stem}.stl"), tolerance=0.05, angularTolerance=0.2)
        bb = wp.val().BoundingBox()
        print(f"{stem}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, "
              f"vol {wp.val().Volume():.0f} mm3")


if __name__ == "__main__":
    main()

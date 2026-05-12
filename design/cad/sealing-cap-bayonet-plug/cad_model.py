"""
Parametric CadQuery model — Bayonet-Plug Sealing Cap (Concept §2.3 of
design/cap-brainstorming.md).

A short male plug with two opposing ears engages a quarter-turn bayonet
groove on the cartridge bottom. A 1.5 mm cross-section O-ring on the
plug face provides the powder seal against the auger Ø3 exit.

Coordinate frame:
  +Z = up (towards the auger), Z = 0 at the bottom of the cartridge
  cap-receiver. All dimensions in millimetres.
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

OUT = Path(__file__).parent
RENDER = OUT / "renders"
STL = OUT / "stl"
RENDER.mkdir(exist_ok=True)
STL.mkdir(exist_ok=True)


# --- Auger / channel interface (PR-#16) ------------------------------------
AUGER_OD = 25.0
EXIT_HOLE_D = 3.0

# --- Cartridge-side receiver (printed onto the bottom of the channel) ------
RECV_OD = 32.0
RECV_H = 10.0
RECV_BORE_D = 18.0       # straight bore the plug body slides into
GROOVE_W = 4.0           # axial width of the bayonet groove
GROOVE_DEPTH = 2.5       # radial depth of the groove
GROOVE_Z = 4.0           # height above receiver bottom where ears sit
EAR_ANGLE = 16.0         # angular size of each ear (deg)
EAR_RUN = 80.0           # angular travel from entry to locked (deg)

# --- Plug body --------------------------------------------------------------
PLUG_OD = RECV_BORE_D - 0.4   # sliding clearance
PLUG_H = 8.0
PLUG_FACE_RECESS_D = 12.0     # O-ring groove ID
ORING_CS = 1.5                # O-ring cross section
ORING_OD = 14.0               # AS568 ~006-008 ballpark — pick what's stocked
KNOB_OD = 22.0
KNOB_T = 4.0


# ============================================================================
# Receiver — a cup that bonds to the bottom of the auger cartridge
# ============================================================================

def receiver() -> cq.Workplane:
    body = cq.Workplane("XY").circle(RECV_OD / 2).extrude(RECV_H)
    # Through bore
    body = body.faces(">Z").workplane().hole(RECV_BORE_D)
    # Snap collar on top to grip auger OD (same trick as the other concepts)
    collar = (
        cq.Workplane("XY")
        .workplane(offset=RECV_H)
        .circle(AUGER_OD / 2 + 1.6)
        .circle(AUGER_OD / 2)
        .extrude(8.0)
    )
    body = body.union(collar)

    # Cut bayonet grooves: J-shaped slot — axial entry slot + circumferential
    # locking run. Two of them, 180° apart.
    for theta0 in (0.0, 180.0):
        # Axial entry slot: full height from top of receiver down to GROOVE_Z
        entry = (
            cq.Workplane("XY")
            .workplane(offset=GROOVE_Z)
            .moveTo(0, 0)
            .parametricCurve(
                lambda t: (
                    (RECV_BORE_D / 2 + GROOVE_DEPTH) * math.cos(math.radians(
                        theta0 - EAR_ANGLE / 2 + EAR_ANGLE * t)),
                    (RECV_BORE_D / 2 + GROOVE_DEPTH) * math.sin(math.radians(
                        theta0 - EAR_ANGLE / 2 + EAR_ANGLE * t)),
                ),
                stop=1.0,
            )
        )
        # Simpler: just box-cut the entry channel and a ring slot.
        entry_box = (
            cq.Workplane("XY")
            .workplane(offset=GROOVE_Z)
            .transformed(rotate=(0, 0, theta0))
            .moveTo(RECV_BORE_D / 2, -GROOVE_W / 2)
            .rect(GROOVE_DEPTH + 0.5, GROOVE_W, centered=False)
            .extrude(RECV_H - GROOVE_Z + 1.0)
        )
        body = body.cut(entry_box)
        # Circumferential locking run — sweep an arc-shaped cutter
        npts = 24
        pts = []
        for i in range(npts + 1):
            a = math.radians(theta0 + i * EAR_RUN / npts)
            r_in = RECV_BORE_D / 2
            r_out = RECV_BORE_D / 2 + GROOVE_DEPTH + 0.5
            pts.append((r_out * math.cos(a), r_out * math.sin(a)))
        for i in range(npts, -1, -1):
            a = math.radians(theta0 + i * EAR_RUN / npts)
            r_in = RECV_BORE_D / 2
            pts.append((r_in * math.cos(a), r_in * math.sin(a)))
        run = (
            cq.Workplane("XY")
            .workplane(offset=GROOVE_Z)
            .polyline(pts)
            .close()
            .extrude(GROOVE_W)
        )
        body = body.cut(run)
    return body


# ============================================================================
# Plug (separate part)
# ============================================================================

def plug() -> cq.Workplane:
    body = cq.Workplane("XY").circle(PLUG_OD / 2).extrude(PLUG_H)
    # O-ring groove on the +Z face
    body = (
        body.faces(">Z")
        .workplane()
        .moveTo(0, 0)
        .circle((ORING_OD + ORING_CS) / 2)
        .circle((ORING_OD - ORING_CS) / 2)
        .cutBlind(-(ORING_CS * 0.75))
    )
    # Two ears at GROOVE_Z that ride the bayonet slots
    for theta0 in (0.0, 180.0):
        ear = (
            cq.Workplane("XY")
            .workplane(offset=GROOVE_Z - PLUG_H / 2 + PLUG_H / 2)
            .transformed(rotate=(0, 0, theta0))
            .moveTo(PLUG_OD / 2, -GROOVE_W / 2 + 0.4)
            .rect(GROOVE_DEPTH - 0.4, GROOVE_W - 0.8, centered=False)
            .extrude(GROOVE_W - 0.8)
        )
        body = body.union(ear)
    # Knob on the bottom — what the mechanism's gripper grabs
    knob = (
        cq.Workplane("XY")
        .workplane(offset=-KNOB_T)
        .circle(KNOB_OD / 2)
        .extrude(KNOB_T)
    )
    body = body.union(knob)
    return body


def auger_stub() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .workplane(offset=RECV_H + 8.0)
        .circle(AUGER_OD / 2)
        .circle(AUGER_OD / 2 - 2.0)
        .extrude(20.0)
    )


def assembly(installed: bool = True) -> cq.Assembly:
    asm = cq.Assembly()
    asm.add(receiver(), name="receiver",
            color=cq.Color(0.78, 0.70, 0.95))
    if installed:
        asm.add(plug().translate((0, 0, GROOVE_Z - GROOVE_W / 2)),
                name="plug", color=cq.Color(0.55, 0.85, 0.55))
    asm.add(auger_stub(), name="auger_stub_REF",
            color=cq.Color(0.55, 0.55, 0.55))
    return asm


def export_all() -> None:
    asm = assembly(installed=True)
    step_path = OUT / "sealing_cap_bayonet_plug.step"
    asm.save(str(step_path))
    print(f"wrote {step_path}")

    cq.exporters.export(receiver(), str(STL / "receiver.stl"))
    cq.exporters.export(plug(), str(STL / "plug.stl"))
    print(f"wrote {STL}/receiver.stl, plug.stl")

    compound = asm.toCompound()
    views = {
        "iso": (1, -1, 0.8),
        "front": (0, -1, 0),
        "top": (0, 0, 1),
        "side": (1, 0, 0),
    }
    for name, vec in views.items():
        svg = cq.exporters.svg.getSVG(
            compound,
            opts={
                "projectionDir": vec,
                "showAxes": False,
                "strokeColor": (40, 40, 40),
                "hiddenColor": (180, 180, 180),
                "showHidden": False,
                "width": 800,
                "height": 800,
                "marginLeft": 40,
                "marginTop": 40,
            },
        )
        (RENDER / f"sealing_cap_bayonet_plug_{name}.svg").write_text(svg)
        print(f"wrote renders/sealing_cap_bayonet_plug_{name}.svg")


if __name__ == "__main__":
    export_all()

"""Bayonet-Plug Sealing Cap — see README.md for full discussion.

REVISION addressing PR #37 review (@swcharles): the v1 model had ear/slot
interference (ears started inside the bore wall and were tangentially
wider than the slot). This rewrite fixes the ear geometry, widens the
slot, and adds an `interference_check()` that prints the residual
volume after subtracting the locked plug from the receiver.
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

# --- Receiver --------------------------------------------------------------
RECV_OD = 36.0
RECV_H = 12.0
RECV_BORE_D = 18.0
SNAP_COLLAR_H = 8.0
SNAP_COLLAR_WALL = 1.6

# --- Plug body -------------------------------------------------------------
# The plug body fills the receiver bore over the full receiver height; its
# top face (Z = RECV_H) presses up against the auger exit (sealed by the
# O-ring). Knob hangs entirely BELOW the receiver bottom (Z ≤ 0) so it
# doesn't interfere with the receiver wall — this was the v1 bug
# (@swcharles in PR #37 review). Mechanism gripper accesses the knob
# from below.
PLUG_BODY_CLEAR = 0.4
PLUG_OD = RECV_BORE_D - PLUG_BODY_CLEAR     # 17.6
PLUG_H = RECV_H                              # plug body fills the bore
KNOB_OD = 26.0
KNOB_T = 4.0

# --- Bayonet ear / J-slot --------------------------------------------------
EAR_RADIAL = 2.5
EAR_TANG = 3.5
EAR_AXIAL = 3.5
EAR_TANG_CLEAR = 1.0      # per-side tangential clearance in the slot
EAR_RADIAL_CLEAR = 0.4
EAR_AXIAL_CLEAR = 0.6
EAR_THETAS_DEG = (0.0, 180.0)
EAR_RUN = 80.0            # twist degrees from entry to locked

# --- O-ring face seal ------------------------------------------------------
ORING_OD = 14.0
ORING_CS = 1.5
ORING_GROOVE_DEPTH = ORING_CS * 0.75

# ============================================================================
# Derived geometry
# ============================================================================

EAR_R_IN = PLUG_OD / 2
EAR_R_OUT = EAR_R_IN + EAR_RADIAL
EAR_R_MID = (EAR_R_IN + EAR_R_OUT) / 2

EAR_HALF_ANGLE = math.degrees(EAR_TANG / 2.0 / EAR_R_MID)
SLOT_HALF_ANGLE = math.degrees(
    (EAR_TANG / 2.0 + EAR_TANG_CLEAR) / EAR_R_MID
)

# Z-position of the ear axial centreline when seated. Ear lives in the
# upper portion of the plug body so the slot doesn't have to be cut all
# the way through the receiver wall.
EAR_TOP_INSET = 1.0       # gap from receiver top down to top of ear
EAR_Z_TOP = RECV_H - EAR_TOP_INSET
EAR_Z_BOT = EAR_Z_TOP - EAR_AXIAL
PLUG_BOTTOM_Z = 0.0       # plug body bottom Z when fully seated

# Locking groove cut into the receiver — slightly larger than the ear in Z.
GROOVE_Z_BOT = EAR_Z_BOT - EAR_AXIAL_CLEAR / 2
GROOVE_Z_TOP = EAR_Z_TOP + EAR_AXIAL_CLEAR / 2
GROOVE_H = GROOVE_Z_TOP - GROOVE_Z_BOT

# Locking-run angular bounds: from entry slot all the way to entry+EAR_RUN
# plus a little extra slack on each end.
RUN_PAD = 4.0             # extra degrees on each end of the run


# ============================================================================
# Receiver
# ============================================================================

def _arc_polygon(theta0_deg: float, theta1_deg: float,
                 r_in: float, r_out: float, npts: int = 24) -> list:
    """Polygon vertices for an annular arc sector (for use as a cutter)."""
    pts = []
    for i in range(npts + 1):
        a = math.radians(theta0_deg + (theta1_deg - theta0_deg) * i / npts)
        pts.append((r_out * math.cos(a), r_out * math.sin(a)))
    for i in range(npts, -1, -1):
        a = math.radians(theta0_deg + (theta1_deg - theta0_deg) * i / npts)
        pts.append((r_in * math.cos(a), r_in * math.sin(a)))
    return pts


def receiver() -> cq.Workplane:
    """Receiver: cup with through-bore + snap collar + two J-slots."""
    body = cq.Workplane("XY").circle(RECV_OD / 2).extrude(RECV_H)

    # Through-bore
    body = body.faces(">Z").workplane().hole(RECV_BORE_D)

    # Snap collar above
    collar = (
        cq.Workplane("XY")
        .workplane(offset=RECV_H)
        .circle(AUGER_OD / 2 + SNAP_COLLAR_WALL)
        .circle(AUGER_OD / 2)
        .extrude(SNAP_COLLAR_H)
    )
    body = body.union(collar)

    # Cut the two J-slots. Plug enters from BELOW (-Z) going up, so the
    # entry slots are open at the bottom of the receiver (z=0) and rise
    # up to meet the locking groove.
    for theta0 in EAR_THETAS_DEG:
        # Entry slot — axial channel from receiver bottom up to GROOVE_Z_TOP
        entry_pts = _arc_polygon(
            theta0 - SLOT_HALF_ANGLE, theta0 + SLOT_HALF_ANGLE,
            EAR_R_IN - 0.05, EAR_R_OUT + EAR_RADIAL_CLEAR
        )
        entry = (
            cq.Workplane("XY")
            .workplane(offset=-0.5)
            .polyline(entry_pts).close()
            .extrude(GROOVE_Z_TOP + 0.5)
        )
        body = body.cut(entry)

        # Locking-run groove — a circumferential pocket from the entry
        # slot to entry + EAR_RUN, with RUN_PAD slack on each end.
        run_pts = _arc_polygon(
            theta0 - SLOT_HALF_ANGLE - RUN_PAD,
            theta0 + EAR_RUN + SLOT_HALF_ANGLE + RUN_PAD,
            EAR_R_IN - 0.05, EAR_R_OUT + EAR_RADIAL_CLEAR
        )
        run = (
            cq.Workplane("XY")
            .workplane(offset=GROOVE_Z_BOT)
            .polyline(run_pts).close()
            .extrude(GROOVE_H)
        )
        body = body.cut(run)
    return body


# ============================================================================
# Plug
# ============================================================================

def plug() -> cq.Workplane:
    """Plug body + ears + knob + O-ring face groove.

    Body fills the receiver bore from z=PLUG_BOTTOM_Z to z=RECV_H.
    Knob hangs entirely below z=0 so it does not foul the receiver wall.
    """
    body = (
        cq.Workplane("XY")
        .workplane(offset=PLUG_BOTTOM_Z)
        .circle(PLUG_OD / 2)
        .extrude(PLUG_H)
    )

    # O-ring groove on the +Z face (sealing face against the auger)
    body = (
        body.faces(">Z")
        .workplane()
        .moveTo(0, 0)
        .circle((ORING_OD + ORING_CS) / 2)
        .circle((ORING_OD - ORING_CS) / 2)
        .cutBlind(-ORING_GROOVE_DEPTH)
    )

    # Ears at theta0=0 and theta0=180 — annular sectors in the upper
    # portion of the plug body.
    for theta0 in EAR_THETAS_DEG:
        ear_pts = _arc_polygon(
            theta0 - EAR_HALF_ANGLE, theta0 + EAR_HALF_ANGLE,
            EAR_R_IN, EAR_R_OUT
        )
        ear = (
            cq.Workplane("XY")
            .workplane(offset=EAR_Z_BOT)
            .polyline(ear_pts).close()
            .extrude(EAR_AXIAL)
        )
        body = body.union(ear)

    # Knob — hangs entirely below the receiver (z = -KNOB_T to 0).
    knob = (
        cq.Workplane("XY")
        .workplane(offset=-KNOB_T)
        .circle(KNOB_OD / 2)
        .extrude(KNOB_T)
    )
    # Two thumb ridges so the knob orientation visually matches the ears
    for theta0 in EAR_THETAS_DEG:
        ridge_pts = _arc_polygon(
            theta0 - 6.0, theta0 + 6.0,
            KNOB_OD / 2 - 1.5, KNOB_OD / 2 + 1.0
        )
        ridge = (
            cq.Workplane("XY")
            .workplane(offset=-KNOB_T)
            .polyline(ridge_pts).close()
            .extrude(KNOB_T)
        )
        knob = knob.union(ridge)
    body = body.union(knob)
    return body


def plug_locked() -> cq.Workplane:
    """Plug rotated by EAR_RUN so the ears sit in the locked position."""
    return plug().rotate((0, 0, 0), (0, 0, 1), EAR_RUN)


# ============================================================================
# Auger reference stub
# ============================================================================

def auger_stub() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .workplane(offset=RECV_H + SNAP_COLLAR_H)
        .circle(AUGER_OD / 2)
        .circle(AUGER_OD / 2 - 2.0)
        .extrude(20.0)
    )


# ============================================================================
# Interference check
# ============================================================================

def interference_check() -> float:
    """Subtract the locked plug from the receiver and report the residual
    volume of the *plug* that remains inside the receiver wall.

    A correctly sized bayonet should give a small residual (the radial
    clearance volume) but no large overlap. Returns the residual volume
    in mm^3 of `plug ∩ receiver` (i.e. material shared between the two).
    """
    p = plug_locked()
    r = receiver()
    overlap = p.intersect(r)
    try:
        vol = overlap.val().Volume()
    except Exception:
        vol = 0.0
    print(f"[interference_check] plug ∩ receiver volume = {vol:.2f} mm^3")
    return vol


# ============================================================================
# Assemblies
# ============================================================================

def assembly_locked() -> cq.Assembly:
    asm = cq.Assembly()
    asm.add(receiver(), name="receiver",
            color=cq.Color(0.78, 0.70, 0.95))
    asm.add(plug_locked(), name="plug_locked",
            color=cq.Color(0.55, 0.85, 0.55))
    asm.add(auger_stub(), name="auger_stub_REF",
            color=cq.Color(0.55, 0.55, 0.55))
    return asm


def assembly_inserted() -> cq.Assembly:
    """Plug fully inserted but NOT yet rotated to lock."""
    asm = cq.Assembly()
    asm.add(receiver(), name="receiver",
            color=cq.Color(0.78, 0.70, 0.95))
    asm.add(plug(), name="plug_inserted",
            color=cq.Color(0.55, 0.85, 0.55))
    asm.add(auger_stub(), name="auger_stub_REF",
            color=cq.Color(0.55, 0.55, 0.55))
    return asm


def exploded_assembly() -> cq.Assembly:
    """Plug pulled down (off-axis) so the J-slots and ears are visible."""
    asm = cq.Assembly()
    asm.add(receiver(), name="1_receiver",
            color=cq.Color(0.78, 0.70, 0.95))
    asm.add(plug().translate((0, 0, -25.0)),
            name="2_plug", color=cq.Color(0.55, 0.85, 0.55))
    asm.add(auger_stub(), name="3_auger_stub_REF",
            color=cq.Color(0.55, 0.55, 0.55))
    return asm


# ============================================================================
# Export
# ============================================================================

def _save_svg(compound, name, vec):
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
    (RENDER / f"{name}.svg").write_text(svg)
    print(f"wrote renders/{name}.svg")


def export_all() -> None:
    interference_check()

    asm = assembly_locked()
    step_path = OUT / "sealing_cap_bayonet_plug.step"
    asm.save(str(step_path))
    print(f"wrote {step_path}")

    cq.exporters.export(receiver(), str(STL / "receiver.stl"))
    cq.exporters.export(plug(), str(STL / "plug.stl"))
    print(f"wrote {STL}/receiver.stl, plug.stl")

    views = {
        "iso": (1, -1, 0.8),
        "front": (0, -1, 0),
        "top": (0, 0, 1),
        "side": (1, 0, 0),
    }
    for name, vec in views.items():
        _save_svg(asm.toCompound(),
                  f"sealing_cap_bayonet_plug_{name}", vec)

    _save_svg(exploded_assembly().toCompound(),
              "sealing_cap_bayonet_plug_exploded", (1, -1, 0.5))


if __name__ == "__main__":
    export_all()

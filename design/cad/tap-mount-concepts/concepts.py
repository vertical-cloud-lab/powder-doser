"""Concept models for a plate-mounted tapper (issue #203).

The tap collar rides on the auger tube, so it has to be slid off every time
an auger is swapped.  These are four ways to mount the Adafruit 412 solenoid
(TAU0730TM) on the mounting plate instead, so the auger lifts straight out of
its C-clips and the tapper never moves:

  1. tap tower    bolt-on side tower on the old tap-collar base's two holes
  2. tap bracket  the front C-clip and the tower printed as one part (4 screws)
  3. hammer       see-saw hammer: the solenoid pushes one end down, the other
                  end flips up and knocks the tube from underneath
  4. flip saddle  the old collar cut open and hinged to the plate; it rests on
                  the tube and swings out of the way for a swap

Everything is placed in the current-design assembly from PR #170
(``cad/full-assembly`` on branch claude/issue-165-20261001-1931, pinned at
7f5b3b7), with its brackets swapped for the Flexible Bracket that Ethan
recreated in Onshape (outline copied from the "Bracket Recreation" sketch on
2026-11-07) and the tap collar, its base and the solenoid removed.

Frames (mm).  ``L`` is the mounting-plate (MP) frame of PR #170's layout.py
shifted so the origin is on the auger axis at the old tap-collar base's hole
row: x along the auger towards the outlet, y up from the plate (floor top at
y = -29.25), z across the plate, with -z the side away from the stepper
(world +X).  MP = L + (-42.33, 0, -41.8).

    pip install cadquery vtk matplotlib
    xvfb-run -a python3 concepts.py        # renders/*.png, sections, STEPs
"""
from __future__ import annotations

import math
import os
import subprocess
import sys
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
STEP_OUT = HERE / "step"
PR170_SHA = "7f5b3b779e1d036f001c0cbf9f979721139b904d"
FA = Path(os.environ.get("PR170_FULL_ASSEMBLY", "/tmp/pr170/cad/full-assembly"))


def ensure_pr170() -> None:
    """Unpack PR #170's cad/full-assembly at the pinned commit if needed."""
    if (FA / "onshape" / "layout.py").exists():
        return
    repo = HERE.parents[2]
    FA.parents[1].mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(repo), "fetch", "origin", PR170_SHA], check=True)
    arch = subprocess.run(["git", "-C", str(repo), "archive", PR170_SHA, "cad/full-assembly"],
                          check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(FA.parents[1])], input=arch, check=True)


# --------------------------------------------------------------------------- #
# numbers
# --------------------------------------------------------------------------- #
TAP_ROW_MP_X = -42.33          # old tap-collar base hole row (PR #170 layout.py)
AUGER_MP_Z = -41.8
L2MP = np.array([TAP_ROW_MP_X, 0.0, AUGER_MP_Z])
FLOOR_Y = -29.25               # top of the mounting plate's floor
HOLE_Z = 24.0                  # M3 rows are 48 mm apart across the tube
FRONT_BRACKET_X = -58.33 - TAP_ROW_MP_X   # = -16.0 in L
TUBE_R = 12.5

# Adafruit 412 / TAU0730TM (datasheet 412_C514-B_diagram.pdf)
SOL_BODY_L = 29.7              # frame length
SOL_W, SOL_D = 17.0, 14.0      # across the ear face, away from it
SOL_STROKE = 4.9
SOL_ROD_D = 5.0                # brass push cap, 10 mm long
SOL_ROD_OUT_ENERGISED = 15.4   # frame face to cap tip, energised
SOL_ROD_OUT = SOL_ROD_OUT_ENERGISED - SOL_STROKE      # 10.5 at rest
SOL_TOP_OUT = 51.9 - SOL_BODY_L - SOL_ROD_OUT_ENERGISED + SOL_STROKE  # spring end, at rest
SOL_BUSH_D = 6.9
SOL_EAR_X, SOL_EAR_Z = 9.1, 8.0  # M3 ear holes, diagonal (PR #51 / #170)

REST_GAP = 3.5                 # cap tip to tube at rest; hits with 1.4 mm of stroke left


# --------------------------------------------------------------------------- #
# geometry helpers
# --------------------------------------------------------------------------- #
def box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0)
            .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def cyl_x(r, x0, x1, y=0.0, z=0.0) -> cq.Workplane:
    return cq.Workplane("YZ").circle(r).extrude(x1 - x0).translate((x0, y, z))


def cyl_y(r, y0, y1, x=0.0, z=0.0) -> cq.Workplane:
    return cq.Workplane("XZ").circle(r).extrude(-(y1 - y0)).translate((x, y0, z))


def cyl_z(r, z0, z1, x=0.0, y=0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(r).extrude(z1 - z0).translate((x, y, z0))


def flexible_bracket() -> cq.Workplane:
    """Ethan's Onshape recreation of Sam's Flexible Bracket ("Outline Copy",
    extruded 12 mm): 60 x 8 mm base, 36 x 6 mm step, Ø25.5 bore with a 2 mm
    wall centred 29.25 mm above the base, R2.5 detents and flared lips.
    Profile in XY (x across, y up from the base), extruded along +Z."""
    def arc(c, r, t):        # Onshape sketch circles here have xDir = (0, -1)
        return (c[0] + r * math.sin(t), c[1] - r * math.cos(t))
    C0, C1 = (0.0, 29.25), (0.0, 49.841)
    pts = []
    def add_arc(c, r, t0, t1, n=10):
        for t in np.linspace(t0, t1, n):
            pts.append(arc(c, r, t))
    # right half, from the bottom centre going counter-clockwise
    right = [(0.0, 0.0), (30.0, 0.0), (30.0, 8.0), (18.0, 8.0), (18.0, 14.0), (12.845, 14.0)]
    pts.extend(right)
    add_arc((12.845, 17.0), 3.0, 0.0, -2.33248)                 # fillet into the clip
    add_arc(C0, 14.75, 0.80911, 2.34341)                         # clip outside
    add_arc(C1, 14.75, 0.79818, 1.49800)                         # lip outside
    add_arc((13.714, 48.841), 1.0, -4.78518 + 2 * math.pi, -1.64359 + 2 * math.pi)  # lip tip
    add_arc(C1, 12.75, 1.49800, 0.82966)                         # lip inside
    add_arc((11.25, 39.546), 2.5, -2.31193, -0.82966)           # detent
    add_arc(C0, 12.75, 2.31193, 0.0, n=16)                       # bore, right half
    right_pts = pts[:]
    left_pts = [(-x, y) for (x, y) in reversed(right_pts)]
    poly = right_pts + left_pts[1:]
    # de-duplicate consecutive points
    clean = [poly[0]]
    for p in poly[1:]:
        if math.dist(p, clean[-1]) > 0.05:      # arcs meet within ~0.01 mm
            clean.append(p)
    if math.dist(clean[0], clean[-1]) < 0.05:
        clean.pop()
    prof = cq.Workplane("XY").polyline(clean).close().extrude(12.0)
    holes = (cq.Workplane("XZ").pushPoints([(24.0, 6.0), (-24.0, 6.0)]).circle(1.7)
             .extrude(-20).translate((0, -2, 0)))
    return prof.cut(holes)


def bracket_in_L(row_x_L: float) -> cq.Workplane:
    """Flexible bracket on the MP floor row at L x = row_x_L."""
    b = flexible_bracket()
    # profile x -> -L z, profile y -> L y, extrusion z -> L x (right-handed)
    b = b.rotate((0, 0, 0), (0, 1, 0), 90)       # extrusion now along +X, profile x -> -Z
    return b.translate((row_x_L - 6.0, FLOOR_Y, 0.0))


def solenoid(energised: bool = False) -> cq.Workplane:
    """Adafruit 412 in its own frame: ear (mounting) face y = 0, body in -y,
    plunger axis along z at (x, y) = (0, -SOL_D/2), push end towards -z."""
    zc = SOL_BODY_L / 2
    frame = box(-SOL_W / 2, SOL_W / 2, -SOL_D, 0.0, -zc, zc)
    window = box(-SOL_W / 2 - 1, SOL_W / 2 + 1, -SOL_D + 1.2, -1.2, -zc + 1.6, zc - 1.6)
    coil = cyl_z(6.2, -zc + 1.6, zc - 1.6, 0.0, -SOL_D / 2)
    body = frame.cut(window).union(coil)
    ears = (box(-SOL_W / 2 - 4.0, -SOL_W / 2 + 1, -1.2, 0.0, -SOL_EAR_Z - 3.5, -SOL_EAR_Z + 3.5)
            .union(box(SOL_W / 2 - 1, SOL_W / 2 + 4.0, -1.2, 0.0, SOL_EAR_Z - 3.5, SOL_EAR_Z + 3.5)))
    ear_holes = (cyl_y(1.6, -3, 1, -SOL_EAR_X - 1.0, -SOL_EAR_Z)
                 .union(cyl_y(1.6, -3, 1, SOL_EAR_X + 1.0, SOL_EAR_Z)))
    out = SOL_ROD_OUT_ENERGISED if energised else SOL_ROD_OUT
    rod = cyl_z(SOL_ROD_D / 2, -zc - out, -zc, 0.0, -SOL_D / 2)
    top_out = SOL_TOP_OUT - (SOL_STROKE if energised else 0.0)
    bush = cyl_z(SOL_BUSH_D / 2, zc, zc + top_out, 0.0, -SOL_D / 2)
    spring = cq.Workplane("XY")
    for i in range(5):
        z = zc + 1.0 + i * (top_out - 2.5) / 4
        spring = spring.union(cyl_z(4.6, z, z + 0.7, 0.0, -SOL_D / 2))
    return body.union(ears.cut(ear_holes)).union(rod).union(bush).union(spring)


def place(shape: cq.Workplane, R_cols, t) -> cq.Workplane:
    """Move a shape by a rotation (columns = images of local X, Y, Z) + t."""
    from OCP.gp import gp_Trsf
    R = np.array(R_cols, float).T
    assert abs(np.linalg.det(R) - 1) < 1e-9
    tr = gp_Trsf()
    tr.SetValues(R[0, 0], R[0, 1], R[0, 2], t[0],
                 R[1, 0], R[1, 1], R[1, 2], t[1],
                 R[2, 0], R[2, 1], R[2, 2], t[2])
    return cq.Workplane("XY").add(cq.Shape.cast(shape.val().moved(cq.Location(tr)).wrapped))


X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
NX, NY, NZ = (-1, 0, 0), (0, -1, 0), (0, 0, -1)


def side_solenoid(x_c: float, energised=False) -> cq.Workplane:
    """Solenoid lying on a shelf at y = -SOL_D/2, ears down, plunger along +z
    (towards the tube from the -z side), cap tip REST_GAP off the tube."""
    tip_z = -(TUBE_R + REST_GAP)                        # cap tip at rest
    face_z = tip_z - SOL_ROD_OUT                        # frame's push face
    zc = face_z - SOL_BODY_L / 2
    # local x -> L x, local y -> L -y, local z -> L -z
    return place(solenoid(energised), [X, NY, NZ], (x_c, -SOL_D / 2, zc))


def m3_holes(x_c: float, y0: float, y1: float) -> cq.Workplane:
    return cyl_y(1.7, y0 - 1, y1 + 1, x_c, HOLE_Z).union(cyl_y(1.7, y0 - 1, y1 + 1, x_c, -HOLE_Z))


# --------------------------------------------------------------------------- #
# concepts (all in L)
# --------------------------------------------------------------------------- #
def tower_body(x0=-9.0, x1=8.0, base_t=5.0) -> cq.Workplane:
    """Base across the plate under the tube + a pillar and shelf on the -z
    side.  The shelf top is y = -SOL_D/2, so the plunger is level with the
    auger axis; its slots let the solenoid slide 2 mm either way along z to
    set the gap."""
    base = box(x0, x1, FLOOR_Y, FLOOR_Y + base_t, -30.0, 30.0)
    shelf_top = -SOL_D / 2
    pillar = box(x0, x1, FLOOR_Y, shelf_top, -36.0, -21.5)
    shelf = box(-11.5, 11.5, shelf_top - 5.0, shelf_top, -60.0, -21.5)
    gusset = (cq.Workplane("YZ").polyline([(FLOOR_Y + base_t, -36.0), (shelf_top - 5.0, -36.0),
                                           (shelf_top - 5.0, -52.0)]).close()
              .extrude(6.0).translate((-3.0, 0, 0)))
    body = base.union(pillar).union(shelf).union(gusset)
    # ear slots (the ears sit at x = -/+ 10.1, z = face - 14.85 -/+ 8)
    face_z = -(TUBE_R + REST_GAP) - SOL_ROD_OUT
    zc = face_z - SOL_BODY_L / 2
    for (ex, ez) in ((-(SOL_EAR_X + 1.0), zc + SOL_EAR_Z), ((SOL_EAR_X + 1.0), zc - SOL_EAR_Z)):
        slot = (cq.Workplane("XZ").slot2D(4.0 + 3.4, 3.4, angle=90).extrude(-12)
                .translate((ex, shelf_top - 8.0, ez)))
        body = body.cut(slot)
    # lightening window through the pillar
    body = body.cut(box(x0 - 1, x1 + 1, FLOOR_Y + base_t + 3, shelf_top - 8, -32.5, -25.0))
    return body.cut(m3_holes((x0 + x1) / 2, FLOOR_Y, FLOOR_Y + base_t))


def concept1():
    """Tap tower: bolt-on, on the old tap-collar base's two M3 holes."""
    return {"Tap tower (printed)": tower_body(), "Solenoid": side_solenoid(0.0)}


def concept2():
    """Tap bracket: the front Flexible Bracket and the tower on one base."""
    clip = bracket_in_L(FRONT_BRACKET_X)
    base = box(FRONT_BRACKET_X - 6.0, 8.0, FLOOR_Y, FLOOR_Y + 8.0, -30.0, 30.0)
    body = clip.union(base).union(tower_body(base_t=8.0))
    body = body.cut(m3_holes(FRONT_BRACKET_X, FLOOR_Y, FLOOR_Y + 8.0)).cut(m3_holes(0.0, FLOOR_Y, FLOOR_Y + 8.0))
    return {"Tap bracket (printed)": body, "Solenoid": side_solenoid(0.0)}


HAMMER_PIVOT = (-21.5, -24.0)      # (y, z) of the pivot pin (along x)
HAMMER_ROD_Z = -34.0               # where the solenoid pushes down
HAMMER_GAP = 6.0                   # head to tube at rest


def concept3(energised=False):
    """See-saw hammer: solenoid stands beside the tube and pushes the short
    end of a pivoting arm down; the long end flips up and knocks the tube
    from underneath (lever about 2.4 : 1, so about 12 mm of head travel for
    the 4.9 mm stroke).  The head hits in free flight after the plunger
    bottoms out, so nothing presses on the turning tube."""
    x0, x1 = -7.0, 8.0          # stays 1 mm short of a baseplate rib under the comb
    xc = (x0 + x1) / 2
    py, pz = HAMMER_PIVOT
    base = box(xc - 10.5, x1, FLOOR_Y, FLOOR_Y + 4.0, -30.0, 30.0).cut(m3_holes(0.0, FLOOR_Y, FLOOR_Y + 4.0))
    ears = (box(x0, xc - 3.2, FLOOR_Y, py + 4.0, pz - 4.0, pz + 4.0)
            .union(box(xc + 3.2, x1, FLOOR_Y, py + 4.0, pz - 4.0, pz + 4.0)))
    ears = ears.cut(cyl_x(1.7, x0 - 1, x1 + 1, py, pz))
    stop = box(xc - 3.0, xc + 3.0, FLOOR_Y, -24.6, -4.0, 4.0)       # head rests on this
    # solenoid tower: a plate on the cap side of the solenoid (its ears face -x),
    # leaving the outboard side open
    tower = box(xc - 10.5, xc - 7.0, FLOOR_Y, 22.0, HAMMER_ROD_Z - 12.5, HAMMER_ROD_Z + 12.5)
    tower = tower.union(box(xc - 10.5, x1, FLOOR_Y, FLOOR_Y + 4.0, HAMMER_ROD_Z - 12.5, -24.0))
    frame = base.union(ears).union(stop).union(tower)
    # arm: rests with the head GAP under the tube
    head_top = -TUBE_R - HAMMER_GAP
    arm = (box(xc - 2.9, xc + 2.9, py - 2.5, py + 2.5, HAMMER_ROD_Z - 3.0, pz)
           .union(box(xc - 2.9, xc + 2.9, py - 2.5, head_top - 4.0 + 2.5, pz, -2.0)))
    arm = arm.union(box(xc - 4.5, xc + 4.5, head_top - 7.0, head_top, -5.0, 5.0))   # head
    arm = arm.cut(cyl_x(1.7, x0 - 1, x1 + 1, py, pz))
    ang = 0.0
    if energised:   # head at the tube: rotate about the pivot
        ang = -math.degrees(math.atan2(HAMMER_GAP, abs(pz)))
        arm = arm.rotate((0, py, pz), (1, py, pz), ang)
    pin = cyl_x(1.5, x0 - 3, x1 + 3, py, pz)
    # solenoid: plunger along L y, push end down onto the arm's short end
    tip_y = py + 2.5 + (0 if not energised else -6.0 * 10.0 / abs(pz))
    face_y = tip_y + (SOL_ROD_OUT if not energised else SOL_ROD_OUT_ENERGISED)
    yc = face_y + SOL_BODY_L / 2
    # local x -> L -z, local y -> L -x (ears on the tower), local z -> L y (push end down)
    sol = place(solenoid(energised), [NZ, NX, Y], (xc - SOL_D / 2, yc, HAMMER_ROD_Z))
    return {"Hammer frame (printed)": frame, "Hammer arm (printed)": arm, "Pivot (M3 screw)": pin,
            "Solenoid": sol}


SADDLE_HINGE = (-6.0, -33.0)       # (y, z) of the hinge pin (along x)


def concept4(open_deg: float = 0.0):
    """Flip saddle: the old collar's top half on a hinged arm.  It rests on
    the tube (gap set by the saddle, not by the plate) and flips out of the
    way for a swap.  A stronger ERM can ride on it too (#142)."""
    x0, x1 = -8.5, 8.5
    hy, hz = SADDLE_HINGE
    base = box(x0, x1, FLOOR_Y, FLOOR_Y + 5.0, -42.0, 30.0).cut(m3_holes(0.0, FLOOR_Y, FLOOR_Y + 5.0))
    post = box(-3.0, 3.0, FLOOR_Y, hy + 4.0, hz - 4.0, hz + 4.0).cut(cyl_x(1.7, x0 - 1, x1 + 1, hy, hz))
    stop = box(x0, x1, FLOOR_Y, -13.0, -42.0, -36.0)          # open position rests here
    frame = base.union(post).union(stop)
    # saddle: shell r 12.75..17.75 from 20 deg past the top to 10 deg below the -z side
    a0, a1 = math.radians(95), math.radians(190)               # angle from +z towards +y
    pts_o = [(17.75 * math.sin(a), 17.75 * math.cos(a)) for a in np.linspace(a0, a1, 24)]
    pts_i = [(12.75 * math.sin(a), 12.75 * math.cos(a)) for a in np.linspace(a1, a0, 24)]
    shell = (cq.Workplane("YZ").polyline(pts_o + pts_i).close().extrude(x1 - x0).translate((x0, 0, 0)))
    # arm from the saddle's lower edge down to the hinge (outboard of the post)
    knuckle = cyl_x(4.0, x0, -3.4, hy, hz).union(cyl_x(4.0, 3.4, x1, hy, hz))
    link = box(x0, x1, hy, -2.0, hz - 3.0, -15.5).cut(box(-3.4, 3.4, hy - 5, hy + 5, hz - 5, hz + 5))
    # solenoid seat on the saddle, plunger radial at 45 deg (upper, -z side):
    # built at 12 o'clock (push end down along -y), then rolled -45 deg about x
    tip_r = TUBE_R + 3.3                    # the old collar's gap
    face_r = tip_r + SOL_ROD_OUT
    seat = box(x0, x1, 15.0, face_r, -8.5, 8.5)
    ear_plate = box(-12.5, 12.5, 15.0, face_r + SOL_BODY_L, -SOL_D / 2 - 2.0, -SOL_D / 2)
    hole = cyl_y(3.75, 10.0, face_r + 1.0)
    roll = lambda w: w.rotate((0, 0, 0), (1, 0, 0), -45.0)
    saddle = shell.union(link).union(knuckle).union(roll(seat.union(ear_plate))).cut(roll(hole))
    sol = roll(place(solenoid(), [X, NZ, Y], (0.0, face_r + SOL_BODY_L / 2, -SOL_D / 2)))
    parts = {"Saddle (printed)": saddle, "Solenoid": sol}
    if open_deg:
        parts = {k: v.rotate((0, hy, hz), (1, hy, hz), -open_deg) for k, v in parts.items()}
    parts["Hinge post (printed)"] = frame
    parts["Hinge pin (M3 screw)"] = cyl_x(1.5, x0 - 3, x1 + 3, hy, hz)
    return parts


CONCEPTS = {
    1: ("Bolt-on tap tower", concept1),
    2: ("Tap bracket (clip + tower, one part)", concept2),
    3: ("See-saw hammer from below", concept3),
    4: ("Flip-away saddle", concept4),
}

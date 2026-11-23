"""Where the clevis block's two holes go in the mounting plate's floor (issue #204, 17 Nov).

Ethan asked for the positions of the two new holes the clevis block needs in the
mounting plate.  This measures them on the plate as he has it now (PR #170's plate
body without the gears, their arms and the floor's front wings, as base.py models
it) from features that can be picked in an Onshape sketch: the centre line, the
floor's rear and side edges, the existing floor holes, the stepper wall and the
hinge axis.  It also checks what sits above and below the holes, and draws a plan
of the floor with the holes dimensioned and a section through them.  Renders
only: nothing touches Onshape.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib
    xvfb-run -a python holes.py      # about 15 s; writes holes.json and renders/clevis_holes.png

Frame: doserlib's unit frame (hinge axis = X through the origin, +Y = behind the
hinge, Z up, tilt 0).  The stepper mount is on the plate's -X side.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import cadquery as cq

import doserlib as D
import concepts as C
import components as K
import base as B

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
MOWN = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]      # plate's STEP frame -> unit frame
A = K.A                                                       # 95: hole row and rod-end pin, behind the hinge
SX = K.BLOCK["screw_x"]                                       # 11: holes either side of the centre line
FLOOR_U, FLOOR_TOP = K.FLOOR_U, K.FLOOR_TOP                   # -35.25 / -29.25
INK, GREY = "#1f1f1f", "#8a8a8a"
NEW_C, EXIST_C = "#e8731e", "#4a78b5"


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #
def plate_u():
    """The plate as Ethan has it (no gears, arms or front wings), with the two holes, in the unit frame."""
    return B.plate_trimmed().moved(C._loc(MOWN))


def _section(shape, axis, at, keep=None):
    """Planar faces of ``shape`` cut by the plane <axis> = at (axis 1 = y, 2 = z)."""
    big = 400.0
    lo = [-big / 2] * 3
    size = [big] * 3
    lo[axis], size[axis] = at - 0.005, 0.01
    s = shape.intersect(cq.Solid.makeBox(*size, cq.Vector(*lo)))
    out = []
    for f in s.Faces():
        n = f.normalAt()
        if abs((n.x, n.y, n.z)[axis]) < 0.9:
            continue
        c = f.Center()
        if (c.x, c.y, c.z)[axis] > at + 0.001:
            continue
        out.append(f)
    return out


def _wire_pts(w, ij, n=36):
    """A wire as an ordered polygon in two of x, y, z: edges sampled (lines every 1 mm), then chained end to start."""
    segs = []
    for e in w.Edges():
        k = n if e.geomType() != "LINE" else max(2, int(e.Length()) + 1)
        pts = [e.positionAt(t) for t in np.linspace(0, 1, k)]
        segs.append([((p.x, p.y, p.z)[ij[0]], (p.x, p.y, p.z)[ij[1]]) for p in pts])
    out = segs.pop(0)
    while segs:
        end = out[-1]
        j, rev = min(((j, r) for j in range(len(segs)) for r in (False, True)),
                     key=lambda jr: math.dist(segs[jr[0]][-1 if jr[1] else 0], end))
        s = segs.pop(j)
        out += (s[::-1] if rev else s)[1:]
    return np.array(out)


def floor_outline(pl):
    """The floor's outline at mid-thickness (x, y) and its holes (x, y, dia)."""
    f = max(_section(pl, 2, (FLOOR_U + FLOOR_TOP) / 2), key=lambda f_: f_.Area())
    holes = []
    for w in f.innerWires():
        e = w.Edges()[0]
        c = e.arcCenter()
        holes.append((round(c.x, 2), round(c.y, 2), round(2 * e.radius(), 2)))
    return _wire_pts(f.outerWire(), (0, 1)), sorted(holes, key=lambda h: (h[1], h[0]))


def wall_box(pl):
    """The stepper wall's footprint on the floor: section just above the floor's top."""
    f = max(_section(pl, 2, FLOOR_TOP + 4.0), key=lambda f_: f_.BoundingBox().xlen * f_.BoundingBox().ylen)
    bb = f.BoundingBox()
    return dict(x=[round(bb.xmin, 2), round(bb.xmax, 2)], y=[round(bb.ymin, 2), round(bb.ymax, 2)])


def silhouette(shape):
    """Top-view triangles of a shape (x, y), for a light fill."""
    m = D.mesh_of(shape, 0.2)
    v = np.asarray(m.vertices)[:, :2]
    return v[np.asarray(m.faces)]


def dist(a, b):
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return float(d.Value())


def module_parts():
    """The module at tilt 0 in the unit frame, the plate as Ethan has it: name -> shape."""
    out = {}
    for p in K.module(0.0, with_hanger=False):
        name = p.name.split(":", 1)[1]
        sh = B.plate_trimmed() if name == "Mounting plate" else p.shape
        out[name] = sh.moved(C._loc(p.M))
    return out


# --------------------------------------------------------------------------- #
# measurements
# --------------------------------------------------------------------------- #
def use_of(x, y):
    if abs(y - A) < 0.5:
        return "new: clevis block"
    if abs(y - 124.0) < 0.5:
        return "rear Flexible Bracket"
    if abs(y - 58.33) < 0.5 or (abs(y - 42.33) < 0.5 and x < 0):
        return "#203's tap bracket"
    return "not used"


def measure():
    pl = plate_u()
    outline, holes = floor_outline(pl)
    new = [h for h in holes if abs(h[1] - A) < 0.5]
    assert len(new) == 2 and {h[0] for h in new} == {-SX, SX}, new
    rear_y = float(outline[:, 1].max())
    front_y = float(outline[(np.abs(outline[:, 0]) < 10.0), 1].min())        # the floor's front edge between the knuckle arms
    side_x = float(outline[(outline[:, 1] > 100.0) & (outline[:, 1] < 125.0), 0].max())   # plain side, behind the stepper tab
    wall = wall_box(pl)
    tab = outline[outline[:, 0] < -side_x - 1.0]
    rb = [h for h in holes if abs(h[1] - 124.0) < 0.5]
    tb = [h for h in holes if abs(h[1] - 58.33) < 0.5]
    res = dict(
        plate="PR #170's mounting plate body without the gears, their arms (webs) and the floor's front wings"
              " (base.plate_trimmed), plus the two new holes; Ethan's Onshape plate matched PR #170's to a median of 0.38 mm",
        frame="unit frame: hinge axis = X through the origin, +Y = behind the hinge, Z up, tilt 0; stepper mount on -X",
        new_holes=dict(
            dia=new[0][2], through="the 6 mm floor", for_="M3 (2 x M3 x 10 socket head, nuts in the clevis block)",
            x=[-SX, SX], y_behind_hinge_axis=A,
            centre_to_centre=2 * SX,
            from_centre_line=SX,
            from_floor_rear_edge=round(rear_y - A, 2),
            from_floor_side_edge=round(side_x - SX, 2),
            from_floor_front_edge=round(A - front_y, 2),
            from_rear_bracket_holes=dict(along=round(rb[0][1] - A, 2), across=round(abs(rb[0][0]) - SX, 2),
                                         direct=round(math.hypot(rb[0][1] - A, abs(rb[0][0]) - SX), 2)),
            from_tap_bracket_rear_holes=dict(along=round(A - tb[0][1], 2), across=round(abs(tb[0][0]) - SX, 2)),
            from_stepper_wall_rear_face=round(A - wall["y"][1], 2),
            stepper_wall_inner_end_x=wall["x"][1],
            in_pr170_step_frame=[[round(float(v), 2) for v in (np.linalg.inv(MOWN) @ np.array([x, A, FLOOR_TOP, 1.0]))[:3]]
                                 for x in (-SX, SX)],
            in_pr170_step_frame_note="mounting-plate.step's own frame (the hinge axis is its Z axis), at the floor's top face",
        ),
        floor=dict(thickness=round(FLOOR_TOP - FLOOR_U, 2), top_below_hinge_axis=-FLOOR_TOP, underside_below_hinge_axis=-FLOOR_U,
                   rear_edge_y=round(rear_y, 2), front_edge_y=round(front_y, 2), side_edges_x=[-round(side_x, 2), round(side_x, 2)],
                   stepper_tab=dict(x_out_to=round(float(tab[:, 0].min()), 2), y=[round(float(tab[:, 1].min()), 2),
                                                                                 round(float(tab[:, 1].max()), 2)])),
        stepper_wall=wall,
        floor_holes=[dict(x=x, y=y, dia=d, from_rear_edge=round(rear_y - y, 2), used_by=use_of(x, y)) for x, y, d in holes],
    )
    # what sits over and under the holes, at tilt 0
    parts = module_parts()
    tube = parts["Auger"]
    heads = []
    for x in (-SX, SX):
        col = cq.Solid.makeCylinder(2.75, 80.0, cq.Vector(x, A, FLOOR_TOP + 0.01))       # an M3 socket head, 5.5 mm
        z = tube.intersect(col).BoundingBox().zmin
        heads.append(round(z - FLOOR_TOP, 2))
    axis_h = round(-math.sqrt(12.5 ** 2 - SX ** 2) - FLOOR_TOP, 2)
    scr = parts["M3 screws"]
    near = {k: round(dist(scr, v), 2) for k, v in parts.items()
            if k in ("Auger", "Stepper (NEMA 11)", "Bracket (rear)", "Tap bracket (#203)", "Stepper pinion")}
    res["over_the_holes"] = dict(
        auger_tube_above_floor_top_on_hole_axis=axis_h,
        auger_tube_above_floor_top_over_a_5_5mm_head=min(heads),
        screws_to_nearest_parts_mm=near,
        screw_head_to_stepper_wall_mm=round(dist(scr, pl.intersect(cq.Solid.makeBox(
            60, 6.5, 50, cq.Vector(-55, wall["y"][0] - 0.25, FLOOR_TOP + 0.05)))), 2),
    )
    px, py, pt = K.BLOCK["pad"]
    res["clevis_block"] = dict(pad=[px, py, pt], holes_centre_to_centre=2 * SX, holes_from_pad_ends=round(px / 2 - SX, 2),
                               holes_from_pad_front_and_back=round(py / 2, 2), pin_below_floor_underside=round(FLOOR_U + K.CC, 2),
                               pin_y_behind_hinge_axis=A,
                               pad_from_floor_side_edges=round(side_x - px / 2, 2), pad_from_floor_rear_edge=round(rear_y - A - py / 2, 2))
    return res, pl, outline, parts


# --------------------------------------------------------------------------- #
# drawing
# --------------------------------------------------------------------------- #
def _dim(ax, p1, p2, off, text, fs=9.5, tpos=0.5, col=INK, ext=True):
    B._dim(ax, p1, p2, off, text, fs=fs, tpos=tpos, col=col, ext=ext)


def drawing(res, pl, outline, parts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Circle, Rectangle

    nh, fl, wall = res["new_holes"], res["floor"], res["stepper_wall"]
    fig = plt.figure(figsize=(16.0, 9.6))

    # ---- plan, seen from above: hinge on the left, rear on the right; drawing (u, v) = (y, -x) -----------------
    ax = fig.add_axes([0.01, 0.02, 0.62, 0.84])
    ax.set_aspect("equal")
    ax.axis("off")
    P = lambda x, y: (y, -x)                                       # noqa: E731
    tri = silhouette(pl)
    ax.add_collection(PolyCollection([[P(*p) for p in t] for t in tri], facecolor="#e4e7ec", edgecolor="#e4e7ec", lw=0.3,
                                     zorder=0))
    o = np.array([P(x, y) for x, y in outline])
    ax.fill(o[:, 0], o[:, 1], color="#c9d0da", zorder=1)
    ax.plot(o[:, 0], o[:, 1], color=INK, lw=1.2, zorder=3)
    wx, wy = wall["x"], wall["y"]
    ax.add_patch(Rectangle(P(wx[1], wy[0]), wy[1] - wy[0], wx[1] - wx[0], fc="#9aa6b8", ec=INK, lw=0.9, hatch="////",
                           zorder=4))
    px, py, _ = res["clevis_block"]["pad"]
    ax.add_patch(Rectangle(P(px / 2, A - py / 2), py, px, fill=False, ec=NEW_C, lw=1.1, ls=(0, (4, 2)), zorder=5))
    for h in res["floor_holes"]:
        c = P(h["x"], h["y"])
        new = h["used_by"].startswith("new")
        ax.add_patch(Circle(c, h["dia"] / 2, fc="white", ec=NEW_C if new else INK, lw=2.0 if new else 0.8, zorder=6))
        if new:
            ax.add_patch(Circle(c, 3.6, fill=False, ec=NEW_C, lw=1.0, zorder=6))
        ax.plot([c[0] - 2.6, c[0] + 2.6], [c[1], c[1]], color=GREY, lw=0.4, zorder=7)
        ax.plot([c[0], c[0]], [c[1] - 2.6, c[1] + 2.6], color=GREY, lw=0.4, zorder=7)
    # centre line and hinge axis
    ax.plot([-14, 162], [0, 0], color=GREY, lw=0.6, ls=(0, (10, 3, 2, 3)), zorder=2)
    ax.plot([0, 0], [-48, 62], color="#3060c0", lw=0.9, ls=(0, (10, 3, 2, 3)), zorder=8)
    ax.text(0, 64, "hinge axis\n(knuckle bores)", ha="center", va="bottom", fontsize=9.5, color="#3060c0")
    ax.text(163, 0, "centre line", ha="left", va="center", fontsize=9.5, color=GREY)
    # dimensions for the new holes, plain (+X) side at the bottom of the drawing
    se, re_ = fl["side_edges_x"][1], fl["rear_edge_y"]
    yb = -se - 9.0
    ax.plot([0, 0], [-se + 1, yb - 2], color=INK, lw=0.45)
    ax.plot([A, A], [-SX - 2.5, yb - 2], color=INK, lw=0.45)
    ax.plot([re_, re_], [-se - 1, yb - 2], color=INK, lw=0.45)
    B._dim(ax, (0.0, yb), (A, yb), 0.0, f"{A:.2f}", fs=11, ext=False)
    B._dim(ax, (A, yb), (re_, yb), 0.0, f"{nh['from_floor_rear_edge']:.2f}", fs=11, ext=False)
    yb2 = yb - 10.0
    rb = nh["from_rear_bracket_holes"]
    ax.plot([124.0, 124.0], [-24 - 2.5, yb2 - 2], color=GREY, lw=0.45)
    ax.plot([A, A], [yb - 2, yb2 - 2], color=GREY, lw=0.45)
    B._dim(ax, (A, yb2), (124.0, yb2), 0.0, f"({rb['along']:.2f})", fs=10, ext=False, col="#555555")
    # across: to the right of the plate
    xr = re_ + 9.0
    for v in (-SX, SX):
        ax.plot([A + 2.5, xr + 9], [v, v], color=INK, lw=0.45)
    ax.plot([re_ + 1, xr + 20], [-se, -se], color=INK, lw=0.45)
    B._dim(ax, (xr, -SX), (xr, SX), 0.0, f"{2 * SX:.2f}", fs=11, ext=False)
    B._dim(ax, (xr + 16, -se), (xr + 16, -SX), 0.0, f"{nh['from_floor_side_edge']:.2f}", fs=11, ext=False)
    B._dim(ax, (xr + 16, -SX), (xr + 16, 0.0), 0.0, f"{SX:.2f}", fs=11, ext=False)
    # callouts
    ax.annotate(f"2 × Ø{nh['dia']:.1f} THRU (M3)\nnew, for the clevis block", xy=(A + 1.5, SX + 1.5), xytext=(122, 56),
                fontsize=11, fontweight="bold", color=NEW_C, ha="center", va="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.9, color=NEW_C, mutation_scale=9, shrinkA=2, shrinkB=0),
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
    ax.annotate(f"stepper wall (hatched); its rear face\nis {nh['from_stepper_wall_rear_face']:.2f} in front of the new holes",
                xy=(wy[0] + 3, -wx[0] - 4), xytext=(50, 50), fontsize=9, color=INK, ha="center", va="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK, mutation_scale=7, shrinkA=2, shrinkB=0),
                bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none"))
    ax.annotate("rear bracket holes,\n6 from the rear edge", xy=(124.0, 24.0 + 2.0), xytext=(166, 30), fontsize=9,
                color=INK, ha="center", va="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK, mutation_scale=7, shrinkA=2, shrinkB=0),
                bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none"))
    for h in res["floor_holes"]:
        if h["used_by"].startswith(("#203", "not used")):
            u, v = P(h["x"], h["y"])
            t = "unused" if h["used_by"] == "not used" else "tap bracket"
            ax.text(u, v + (-3.2 if v < 0 else 3.2), t, ha="center", va="top" if v < 0 else "bottom", fontsize=8, color=INK)
    ax.text(re_ + 1.5, -se - 3.5, "rear edge", ha="left", va="top", fontsize=8.5, color=GREY, rotation=0)
    ax.text(-12, 41, "STEPPER SIDE (-X)", fontsize=9, color=GREY, ha="left", va="center")
    ax.text(-12, -41, "PLAIN SIDE (+X)", fontsize=9, color=GREY, ha="left", va="center")
    ax.text(62, -8, "floor, 6.00 thick", fontsize=9, color=INK, ha="center", va="center")
    ax.text(A, -px / 2 - 1.5, "block's pad (hidden)", fontsize=8, color=NEW_C, ha="center", va="top",
            bbox=dict(boxstyle="square,pad=0.08", fc="#c9d0da", ec="none"))
    ax.set_xlim(-16, 196)
    ax.set_ylim(-70, 72)
    ax.set_title("Mounting plate floor, seen from above (mm). Plate as you have it: no gears, arms or front wings",
                 fontsize=12, loc="left", fontweight="bold")

    # ---- section A-A at y = 95, seen from the hinge side (x to the right, as from the front) ---------------------
    ax = fig.add_axes([0.64, 0.30, 0.355, 0.61])
    ax.set_aspect("equal")
    ax.axis("off")
    cols = {"Mounting plate": "#c9d0da", "clevis block": "#f2a65a", "M3 screws": "#8d8f94", "M4 pin": "#8d8f94",
            "P16 rod": "#b9bcc2", "Auger": "#9cc3e4", "Stepper (NEMA 11)": "#5c6370"}
    for name, sh in parts.items():
        if name not in cols:
            continue
        for f in _section(sh, 1, A):
            ow = _wire_pts(f.outerWire(), (0, 2))
            ax.fill(ow[:, 0], ow[:, 1], color=cols[name], zorder=2 if name != "M3 screws" else 4)
            ax.plot(ow[:, 0], ow[:, 1], color=INK, lw=0.6, zorder=3 if name != "M3 screws" else 5)
            for w in f.innerWires():
                iw = _wire_pts(w, (0, 2))
                ax.fill(iw[:, 0], iw[:, 1], color="white", zorder=3)
                ax.plot(iw[:, 0], iw[:, 1], color=INK, lw=0.5, zorder=3)
    ax.plot([0, 0], [-58, 16], color=GREY, lw=0.5, ls=(0, (8, 3, 2, 3)), zorder=6)
    zd = FLOOR_TOP + 9.0
    for x in (-SX, SX):
        ax.plot([x, x], [FLOOR_U - 8, zd + 2], color=GREY, lw=0.5, ls=(0, (8, 3, 2, 3)), zorder=6)
    B._dim(ax, (-SX, zd), (SX, zd), 0.0, f"{2 * SX:.2f}", fs=10.5, ext=False)
    oh = res["over_the_holes"]
    zt = FLOOR_TOP + oh["auger_tube_above_floor_top_over_a_5_5mm_head"]
    B._dim(ax, (SX + 8, FLOOR_TOP), (SX + 8, zt), 0.0, f"{oh['auger_tube_above_floor_top_over_a_5_5mm_head']:.1f}", fs=9.5,
           ext=False)
    ax.plot([SX + 2.75, SX + 10], [FLOOR_TOP, FLOOR_TOP], color=INK, lw=0.4)
    ax.plot([SX - 2.75, SX + 10], [zt, zt], color=INK, lw=0.4)
    B._dim(ax, (36.0, FLOOR_U), (36.0, FLOOR_TOP), 0.0, "6.00", fs=9.5, ext=False)
    ax.plot([-15.0, -24.0], [-K.CC, -K.CC], color=INK, lw=0.4)
    B._dim(ax, (-22.0, FLOOR_U), (-22.0, -K.CC), 0.0, f"{res['clevis_block']['pin_below_floor_underside']:.2f}", fs=9,
           ext=False)
    notes = [((-24.0, 6.0), "stepper (cut)", (-44.0, 18.0)), ((7.0, 10.4), "auger tube, Ø25", (24.0, 18.0)),
             ((-SX - 1.5, FLOOR_TOP + 2.0), "M3 × 10, head on the floor", (-33.0, -16.0)),
             ((SX + 1.5, FLOOR_U - 3.0), "nut in a pocket", (30.0, -50.0)),
             ((-12.0, FLOOR_U - 2.0), "clevis block", (-36.0, -50.0)),
             ((0.0, -K.CC - 6.0), "P16 rod end on the M4 pin", (6.0, -64.0))]
    for xy, t, xt in notes:
        ax.annotate(t, xy=xy, xytext=xt, fontsize=9, color=INK, ha="center", va="center",
                    arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK, mutation_scale=7, shrinkA=2, shrinkB=0),
                    bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none"))
    ax.set_xlim(-56, 42)
    ax.set_ylim(-68, 22)
    ax.set_title("Section through the holes, seen from the hinge (mm)", fontsize=12, loc="left", fontweight="bold")

    # ---- notes ----------------------------------------------------------------------------------------------------
    ax = fig.add_axes([0.645, 0.02, 0.35, 0.27])
    ax.axis("off")
    rb = nh["from_rear_bracket_holes"]
    lines = [
        ("In an Onshape sketch on the floor:", True),
        (f"two Ø{nh['dia']:.1f} circles, {2 * SX:.0f} apart, {SX:.0f} either side of the centre line,", False),
        (f"centres {nh['from_floor_rear_edge']:.0f} in front of the floor's rear edge ({A:.0f} behind the hinge axis);", False),
        ("then extrude, remove, through all (the floor is 6 thick).", False),
        ("Cross-checks:", True),
        (f"{nh['from_floor_side_edge']:.0f} from each side edge; {rb['along']:.0f} in front of and {rb['across']:.0f} inboard of"
         " the rear", False),
        ("bracket's holes. The clevis pin sits right under the holes' line.", False),
        (f"The auger tube passes {oh['auger_tube_above_floor_top_over_a_5_5mm_head']:.1f} above the floor over the holes:", False),
        ("fit the block before the auger, or put the screws in from below.", False),
    ]
    y = 0.98
    for t_, b_ in lines:
        ax.text(0.0, y, t_, fontsize=10.5, fontweight="bold" if b_ else "normal", va="top", transform=ax.transAxes)
        y -= 0.108
    fig.text(0.01, 0.985, "Clevis block holes in the mounting plate (issue #204): positions in mm", fontsize=17,
             fontweight="bold", va="top")
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / "clevis_holes.png", dpi=110)
    plt.close(fig)
    print("  -> renders/clevis_holes.png", flush=True)


def main():
    res, pl, outline, parts = measure()
    print(json.dumps({k: res[k] for k in ("new_holes", "over_the_holes", "clevis_block")}, indent=1), flush=True)
    (HERE / "holes.json").write_text(json.dumps(res, indent=1) + "\n")
    drawing(res, pl, outline, parts)


if __name__ == "__main__":
    main()

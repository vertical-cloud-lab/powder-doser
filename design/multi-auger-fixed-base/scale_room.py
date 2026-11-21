"""Room for a balance under the telescoping tripod (S2), and the lab's A&D HR-100A in it (issue #204, 21 Nov).

Ethan asked: with S2, how much clearance is there underneath for the scale, and how does that compare
with the size of the scale under the current doser?  The scale under the current doser is the lab's
A&D HR-100A (102 g x 0.1 mg).  Today's single doser stands on a platform that bridges over it on four
legs and doses down through its top.

1. S2's room, whatever the balance: the shelf's height over S2's range, how far down the actuators
   hang, and the free column between them at each height (modules parked at 0 deg, and over 0-90 deg).
2. The HR-100A traced from A&D's own drawing (HR-A/HR-AZ manual, section 22 "External dimensions",
   page 74, drawn at 1:5): the base with its sloped display, the round breeze break, the full-height
   rear column, the lid with its front handle and knobs, and where the lid goes when it opens.
   doserlib.hr100a(), which stands.py used on 20 Nov, is simpler: it has no rear column, puts the
   base 95 mm in front of the pan instead of 167, and draws the breeze break 7 mm smaller in radius.
3. The HR-100A under S2, its pan centre on the beaker axis: every orientation in 5 deg steps, at
   stand heights 320-359 mm, against the stand and every part of all three modules that hangs below
   the shelf, over 0-90 deg one module at a time (so every tilt mix), with the lid on and with it off.
   A fast pass uses surface samples (1.5 mm apart) and an exact distance to the balance's primitives;
   the configurations reported are then re-checked with mesh-to-mesh distances (python-fcl).

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib scipy
    xvfb-run -a python scale_room.py      # about 9 min; writes scale_room.json and renders/scale_*.png
    python scale_room.py --figures-only   # redraws renders/scale_room.png from scale_room.json

Frames: the station frame of doserlib.py (beaker axis = Z, hinge axes at z = 0, modules at bearings 90
(back), 210 and 330 deg, the front gap facing -Y).  The balance frame: origin at the pan centre on the
bench, +X towards the rear column, +Y to the user's left when facing the display, z up.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import cadquery as cq

import doserlib as D
import stands as ST
import base as B
import components as K

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
BOT = D.BASE_BOT_U                       # shelf underside, station z (-43.25)
GAP = 2.0
HEIGHTS = (320.0, 330.0, 340.0, 350.0, 359.0)
TILTS = tuple(range(0, 91, 5))
PHIS = tuple(range(0, 360, 5))
SPACING = 1.5                            # mm between surface samples
GAPS_AT = (30.0, 150.0, 270.0)           # bearings of the gaps between modules (front gap = 270)

# --------------------------------------------------------------------------- #
# the A&D HR-100A, from the manual's drawing (section 22): balance frame, mm
# --------------------------------------------------------------------------- #
HR = dict(
    W=198.0, D=294.0, H=315.0,            # A&D's external dimensions (section 21)
    front_tip=-167.0,                     # display edge, in front of the pan centre
    rear=127.0,                           # rear column's back face (front_tip + 294)
    pan_z=86.5, pan_d=90.0,               # section 22, notes *3 and *4
    inside_d=156.0, inside_h=198.0,       # breeze break inside (notes *2, *6)
    bb_r=93.0,                            # breeze break and lid, outside radius (front view: 186 mm across the door frames)
    base_top=72.0, rim_top=290.0, lid_top=303.0,
    lid_open_reach=270.0,                 # the lid swings out to the user's left, to 270 mm from the pan centre (note *1)
    door_open_reach=105.0,                # an opened side door reaches 105 mm from the pan centre (note *1)
    feet=((-105.5, 81.0, 17.0), (87.0, 81.0, 6.0)),   # (x, |y|, radius): 61.5 + 191.5 apart, 162 across
)
SPINE = [(78.0, -86.0), (93.0, -84.0), (124.0, -38.0), (124.0, 38.0), (93.0, 84.0), (78.0, 86.0)]   # plan, CCW
WEDGE = [(-167.0, 6.0), (-88.0, 6.0), (-88.0, 64.0), (-167.0, 33.0)]    # sloped display, (x, z), CCW


def hr_prims(lid=True):
    """The HR-100A as convex primitives: ("cyl", cx, cy, r, z0, z1), ("xy", poly, z0, z1) (plan polygon
    extruded in z) and ("xz", poly, y0, y1) (side polygon extruded in y)."""
    top = HR["lid_top"] if lid else HR["rim_top"]
    w = HR["W"] / 2
    p = [("xz", WEDGE, -w, w),
         ("xy", [(-88.0, -w), (93.0, -w), (93.0, w), (-88.0, w)], 6.0, HR["base_top"]),
         ("cyl", 0.0, 0.0, HR["bb_r"], HR["base_top"], top),
         ("xy", SPINE, 60.0, top)]
    for x, y, r in HR["feet"]:
        p += [("cyl", x, y, r, 0.0, 8.0), ("cyl", x, -y, r, 0.0, 8.0)]
    if lid:
        p += [("xy", [(90.0, -40.0), (130.0, -40.0), (130.0, 40.0), (90.0, 40.0)], 283.0, HR["lid_top"]),   # lid's rear lip
              ("xy", [(-113.0, -15.0), (-88.0, -15.0), (-88.0, 15.0), (-113.0, 15.0)], 290.0, HR["H"]),  # front handle
              ("cyl", 60.0, 68.0, 9.0, 290.0, 314.0),                                                    # knurled knob
              ("xy", [(85.0, -77.0), (105.0, -77.0), (105.0, -56.0), (85.0, -56.0)], 290.0, HR["H"])]    # rear latch
    return p


def hr_top(lid=True):
    return HR["H"] if lid else HR["rim_top"]


def _sd_poly(P, poly):
    """Signed distance from 2-D points P (n, 2) to a convex CCW polygon (negative inside)."""
    poly = np.asarray(poly, float)
    dmin = np.full(len(P), np.inf)
    inside = np.ones(len(P), bool)
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ab = b - a
        ap = P - a
        t = np.clip(ap @ ab / (ab @ ab), 0.0, 1.0)
        dmin = np.minimum(dmin, np.linalg.norm(ap - t[:, None] * ab, axis=1))
        inside &= (ab[0] * ap[:, 1] - ab[1] * ap[:, 0]) >= 0.0
    return np.where(inside, -dmin, dmin)


def _sd_prism(d2, w, w0, w1):
    dw = np.maximum(w0 - w, w - w1)
    return np.sqrt(np.maximum(d2, 0.0) ** 2 + np.maximum(dw, 0.0) ** 2) + np.minimum(np.maximum(d2, dw), 0.0)


def sdf(Pb, prims):
    """Distance from points in the balance frame (n, 3) to the balance (negative inside)."""
    d = np.full(len(Pb), np.inf)
    x, y, z = Pb[:, 0], Pb[:, 1], Pb[:, 2]
    for pr in prims:
        if pr[0] == "cyl":
            _, cx, cy, r, z0, z1 = pr
            di = _sd_prism(np.hypot(x - cx, y - cy) - r, z, z0, z1)
        elif pr[0] == "xy":
            di = _sd_prism(_sd_poly(Pb[:, :2], pr[1]), z, pr[2], pr[3])
        else:
            di = _sd_prism(_sd_poly(np.c_[x, z], pr[1]), y, pr[2], pr[3])
        d = np.minimum(d, di)
    return d


def hr_solid(lid=True):
    """The same primitives as a CadQuery solid (balance frame), for the exact check and the renders."""
    out = None
    for pr in hr_prims(lid):
        if pr[0] == "cyl":
            _, cx, cy, r, z0, z1 = pr
            s = D.cyl(r, z1 - z0, cx, cy, z0)
        elif pr[0] == "xy":
            s = cq.Workplane("XY", origin=(0, 0, pr[2])).polyline(pr[1]).close().extrude(pr[3] - pr[2]).val()
        else:
            pts = [(px, pz) for px, pz in pr[1]]
            s = cq.Workplane("XZ", origin=(0, pr[3], 0)).polyline(pts).close().extrude(pr[3] - pr[2]).val()
        out = s if out is None else out.fuse(s)
    return out.clean()


def hr_pan_glass():
    """Pan and a glass shell inside the breeze break, for the renders only."""
    pan = D.cyl(HR["pan_d"] / 2, 2.0, 0, 0, HR["pan_z"] - 2.0)
    return pan


def M_balance(phi, zb):
    """Balance frame -> station frame: rear column towards bearing phi, bench at station z = zb."""
    return D.Tt(0.0, 0.0, zb) @ D.Rz(phi)


def to_balance(P, phi, zb):
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    x, y = P[:, 0], P[:, 1]
    return np.c_[c * x + s * y, -s * x + c * y, P[:, 2] - zb]


# --------------------------------------------------------------------------- #
# what hangs under the shelf: surface samples at every tilt, and the stand
# --------------------------------------------------------------------------- #
def _samples(shape, M, spacing=SPACING):
    import trimesh
    m = D.mesh_of(shape)
    n = max(200, int(m.area / spacing ** 2))
    pts, _ = trimesh.sample.sample_surface_even(m, n, seed=1)
    pts = np.vstack([pts, np.asarray(m.vertices)])
    return (M[:3, :3] @ pts.T).T + M[:3, 3]


def hanging_parts(tilts_abc):
    """Doser parts that reach below the shelf's underside (P16s, U-brackets, pins, clevis blocks)."""
    out = []
    for p in ST.doser(tilts_abc):
        if p.kind == "base":
            continue
        m = D.mesh_of(p.shape)
        v = (p.M[:3, :3] @ np.asarray(m.vertices).T).T + p.M[:3, 3]
        if v[:, 2].min() < BOT - 0.5:
            out.append(p)
    return out


def moving_samples(tilts=TILTS):
    """(points, module index, tilt) for every hanging part of every module, tilts 0..90 in 5 deg steps."""
    P, mod, til = [], [], []
    for i, u in enumerate("ABC"):
        for t in tilts:
            tl = [0, 0, 0]
            tl[i] = t
            for p in hanging_parts(tl):
                if not p.name.startswith(u + ":"):
                    continue
                q = _samples(p.shape, p.M)
                q = q[q[:, 2] < BOT + 25.0]
                P.append(q)
                mod.append(np.full(len(q), i))
                til.append(np.full(len(q), t))
    return np.vstack(P), np.concatenate(mod), np.concatenate(til)


def stand_samples(S):
    P = []
    for p in ST.s2_parts(S):
        P.append(_samples(p.shape, p.M, 2.0))
    return np.vstack(P)


# --------------------------------------------------------------------------- #
# S2's room, whatever the balance
# --------------------------------------------------------------------------- #
def room_profile(mv, S):
    """Free radius about the beaker axis in 10 mm bands from the bench to the shelf, with the modules
    parked at 0 deg and over 0..90 deg; plus the stand's (legs') own free radius per band."""
    P, mod, til = mv
    zb = BOT - S
    st = stand_samples(S)
    rows = []
    for z0 in np.arange(0.0, S, 10.0):
        z1 = min(z0 + 10.0, S)
        sel = (P[:, 2] - zb >= z0) & (P[:, 2] - zb < z1)
        sel0 = sel & (til == 0)
        r_all = float(np.hypot(P[sel, 0], P[sel, 1]).min()) if sel.any() else None
        r_0 = float(np.hypot(P[sel0, 0], P[sel0, 1]).min()) if sel0.any() else None
        ss = (st[:, 2] - zb >= z0) & (st[:, 2] - zb < z1)
        r_st = float(np.hypot(st[ss, 0], st[ss, 1]).min()) if ss.any() else None
        rows.append(dict(z=[round(z0), round(z1)], r_parked=None if r_0 is None else round(r_0, 1),
                         r_any_tilt=None if r_all is None else round(r_all, 1),
                         r_legs=None if r_st is None else round(r_st, 1)))
    lowest = float((P[:, 2] - zb).min())
    return rows, round(lowest, 1)


# --------------------------------------------------------------------------- #
# the HR-100A under S2: fast sweep, then exact checks
# --------------------------------------------------------------------------- #
def sweep(mv, S, lid):
    P, mod, til = mv
    zb = BOT - S
    st = stand_samples(S)
    prims = hr_prims(lid)
    shelf = S - hr_top(lid)
    res = []
    for phi in PHIS:
        d_st = float(sdf(to_balance(st, phi, zb), prims).min())
        d = sdf(to_balance(P, phi, zb), prims)
        per_tilt = []
        for t in TILTS:
            m = til == t
            per_tilt.append(float(d[m].min()))
        per_tilt = np.array(per_tilt)
        # the largest tilt T such that every module may go anywhere in 0..T with >= GAP everywhere
        ok = per_tilt >= GAP
        t_max = -1
        for k, t in enumerate(TILTS):
            if ok[: k + 1].all():
                t_max = t
        res.append(dict(phi=phi, stand=round(d_st, 2), shelf=round(shelf, 2), moving_0_90=round(float(per_tilt.min()), 2),
                        moving_parked=round(float(per_tilt[0]), 2), t_max=t_max,
                        per_tilt=[round(float(x), 2) for x in per_tilt]))
    return res


def exact_check(S, phi, lid, tilts=TILTS):
    zb = BOT - S
    hr = D.Part("HR-100A", hr_solid(lid), M_balance(phi, zb), D.COL["balance"], "balance")
    hr.kind = "balance"
    st = ST.s2_parts(S)
    d_st = min(ST._dist(o1, o2) for (_, o1) in ST._objs(st) for (_, o2) in ST._objs([hr]))
    mv = ST.stand_vs_doser([hr], units="ABC", tilts=tilts)
    return dict(stand=round(d_st, 2), moving=mv, shelf=round(S - hr_top(lid), 2))


def best_of(rows, key):
    return max(rows, key=lambda r: (r[key], r["moving_0_90"], r["stand"]))


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #
def plan_outline_station(phi, lid=True, z=None):
    """The balance's plan outline (union of its primitives' plan shapes) in the station frame."""
    out = []
    for pr in hr_prims(lid):
        if pr[0] == "cyl":
            _, cx, cy, r, z0, z1 = pr
            t = np.linspace(0, 2 * math.pi, 120)
            pts = np.c_[cx + r * np.cos(t), cy + r * np.sin(t)]
        elif pr[0] == "xy":
            z0, z1 = pr[2], pr[3]
            pts = np.vstack([pr[1], pr[1][:1]])
        else:
            xs = [q[0] for q in pr[1]]
            z0, z1 = min(q[1] for q in pr[1]), max(q[1] for q in pr[1])
            pts = np.array([(min(xs), pr[2]), (max(xs), pr[2]), (max(xs), pr[3]), (min(xs), pr[3]), (min(xs), pr[2])])
        if z is not None and not (z0 <= z <= z1):
            continue
        c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        out.append(np.c_[c * pts[:, 0] - s * pts[:, 1], s * pts[:, 0] + c * pts[:, 1]])
    return out


def figure_room(res, fn):
    """Side elevation of S2's room (free radius vs height) with the HR-100A's half-widths, and a plan."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly, Circle, Rectangle
    S = res["fit"]["height_mm"]
    prof = res["room"][str(int(S))]["profile"]
    fig = plt.figure(figsize=(19.5, 8.6), dpi=110)
    ax = fig.add_axes([0.04, 0.10, 0.36, 0.80])
    z = np.array([(r["z"][0] + r["z"][1]) / 2 for r in prof])
    for key, col, lab in (("r_parked", "#5b8bd9", "actuators, all modules parked at 0°"),
                          ("r_any_tilt", "#c0392b", "actuators, any tilt 0-90°"),
                          ("r_legs", "#16a085", "stand (sleeves, posts, feet)")):
        r = np.array([np.nan if x[key] is None else x[key] for x in prof])
        ax.step(r, z, where="mid", color=col, lw=2.2, label=lab)
    # HR-100A: largest distance from the pan axis at each height (its plan outline is not round)
    zz = np.arange(0, HR["H"] + 1, 2.0)
    rmax_side = []
    for zi in zz:
        r = 0.0
        for pr in hr_prims(True):
            if pr[0] == "cyl":
                if pr[4] <= zi <= pr[5]:
                    r = max(r, math.hypot(pr[1], pr[2]) + pr[3])
            elif pr[0] == "xy":
                if pr[2] <= zi <= pr[3]:
                    r = max(r, max(math.hypot(a, b) for a, b in pr[1]))
            else:
                zmin, zmax = min(q[1] for q in pr[1]), max(q[1] for q in pr[1])
                if zmin <= zi <= zmax:
                    r = max(r, max(math.hypot(q[0], pr[3]) for q in pr[1]))
        rmax_side.append(r)
    ax.fill_betweenx(zz, 0, [HR["bb_r"] if 72 <= zi <= HR["H"] else 0 for zi in zz], color="#d9d9d9", alpha=0.9,
                     label="HR-100A: breeze break and lid (R 93)")
    ax.plot(rmax_side, zz, color="#555", lw=1.2, ls="--", label="HR-100A: farthest point at that height")
    ax.axhline(S, color="#c46a1c", lw=2.5)
    ax.text(5, S + 4, f"shelf underside, S2 at {S:.0f} mm (range 217-359)", color="#c46a1c", fontsize=10)
    ax.axhline(HR["H"], color="#555", lw=1.0, ls=":")
    ax.text(5, HR["H"] - 13, "HR-100A top 315", color="#333", fontsize=9.5)
    low = res["room"][str(int(S))]["lowest_hanging_mm"]
    ax.axhline(low, color="#888", lw=1.0, ls=":")
    ax.text(150, low - 13, f"lowest actuator point {low:.0f}", color="#333", fontsize=9.5)
    ax.set_xlim(0, 270)
    ax.set_ylim(0, 380)
    ax.set_xlabel("distance from the beaker axis (mm)")
    ax.set_ylabel("height above the bench (mm)")
    ax.set_title(f"S2 at {S:.0f} mm: free radius under the shelf, by height", loc="left", fontsize=12, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)
    # plan
    ax2 = fig.add_axes([0.43, 0.06, 0.28, 0.86])
    ax2.set_aspect("equal")
    face = B.shelf_outline_sketch()._faces.Faces()[0]
    ol = B._wire_xy(face.outerWire())
    ax2.fill(ol[:, 0], ol[:, 1], color="#fbe3c8", zorder=1)
    ax2.plot(ol[:, 0], ol[:, 1], color="#c46a1c", lw=1.0, zorder=2)
    fit = res["fit"]
    phi = fit["phi_deg"]
    for poly in plan_outline_station(phi, lid=fit["lid"]):
        ax2.add_patch(MPoly(poly, closed=True, fc=(0.55, 0.55, 0.55, 0.30), ec="#333", lw=1.0, zorder=4))
    P, mod, til = res["_mv"]
    zb = BOT - S
    for t, col in ((0, "#5b8bd9"), (90, "#c0392b")):
        m = (til == t) & (P[:, 2] < BOT)
        ax2.scatter(P[m, 0], P[m, 1], s=0.4, color=col, zorder=5)
    st = stand_samples(S)
    ax2.scatter(st[:, 0], st[:, 1], s=0.3, color="#16a085", zorder=3)
    ax2.add_patch(Circle((0, 0), HR["bb_r"], fill=False, ls="--", color="#333", lw=0.8, zorder=6))
    for g in GAPS_AT:
        ax2.plot([0, 300 * math.cos(math.radians(g))], [0, 300 * math.sin(math.radians(g))], color="#999", lw=0.6, ls=":")
    ax2.annotate("front", xy=(0, -300), ha="center", fontsize=10)
    ax2.set_xlim(-310, 310)
    ax2.set_ylim(-320, 310)
    ax2.axis("off")
    ax2.set_title(f"Plan: HR-100A {'with' if fit['lid'] else 'without'} its lid, rear column to {phi:.0f}°\n"
                  f"blue: actuators at 0°, red: at 90°, teal: stand", fontsize=10.5, loc="left")
    # clearance vs orientation
    ax3 = fig.add_axes([0.755, 0.13, 0.225, 0.74])
    for lid, ls in ((True, "-"), (False, "--")):
        rows = res["sweep"][f"{int(S)}_{'lid' if lid else 'nolid'}"]
        ph = [r["phi"] for r in rows]
        ax3.plot(ph, [r["moving_0_90"] for r in rows], ls, color="#c0392b", lw=1.6,
                 label=f"actuators, any tilt 0-90°, lid {'on' if lid else 'off'}")
        ax3.plot(ph, [r["moving_parked"] for r in rows], ls, color="#5b8bd9", lw=1.6,
                 label=f"actuators, all at 0°, lid {'on' if lid else 'off'}")
    rows = res["sweep"][f"{int(S)}_nolid"]
    ax3.plot([r["phi"] for r in rows], [r["stand"] for r in rows], "-", color="#16a085", lw=2.0, label="stand (legs, feet)")
    ax3.axhline(GAP, color="k", lw=0.8)
    ax3.text(2, GAP + 0.8, "2 mm target", fontsize=9)
    for g in (30, 150, 270):
        ax3.axvline(g, color="#999", lw=0.6, ls=":")
        ax3.text(g, 18.5, "gap", ha="center", fontsize=8.5, color="#666")
    ax3.set_xlim(0, 355)
    ax3.set_ylim(-30, 20)
    ax3.set_xlabel("bearing of the rear column (°)")
    ax3.set_ylabel("closest approach (mm); below 0 = they collide")
    ax3.set_title(f"Turning the HR-100A, S2 at {S:.0f} mm", loc="left", fontsize=11, fontweight="bold")
    ax3.legend(fontsize=8, loc="lower left")
    ax3.grid(alpha=0.3)
    fig.savefig(fn)
    plt.close(fig)


def render_fit(res, fn):
    """Iso render of the HR-100A under S2 at the reported configuration (modules at 30, 60, 0 deg)."""
    from PIL import Image
    fit = res["fit"]
    S, phi, lid = fit["height_mm"], fit["phi_deg"], fit["lid"]
    zb = BOT - S
    tilts = tuple(fit.get("render_tilts", (30, 60, 0)))
    hr = D.Part("HR-100A", hr_solid(lid), M_balance(phi, zb), D.COL["balance"], "balance")
    hr.kind = "balance"
    pan = D.Part("HR-100A pan", hr_pan_glass(), M_balance(phi, zb), (0.75, 0.76, 0.78), "balance")
    pan.kind = "balance"
    parts = ST.doser(tilts) + ST.s2_parts(S) + [hr, pan, ST.bench(zb)]
    sub = [f"S2 at {S:.0f} mm; the HR-100A {'with' if lid else 'without'} its lid, its rear column turned to {phi:.0f}° "
           f"(into a gap between modules).",
           f"Modules at {tilts[0]}, {tilts[1]} and {tilts[2]}°. The HR-100A is traced from A&D's drawing (manual section 22)."]
    ST.render_concept("scalefit", parts, "The HR-100A under the telescoping tripod", sub, fn, az=-58.0, el=16.0)
    return fn


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    import sys
    OUT.mkdir(exist_ok=True)
    if "--figures-only" in sys.argv:                       # redraw scale_room.png from scale_room.json
        res = json.loads((HERE / "scale_room.json").read_text())
        res["_mv"] = moving_samples(tilts=(0, 90))
        figure_room(res, OUT / "scale_room.png")
        print("  -> scale_room.png", flush=True)
        return
    res = dict(HR100A=dict(source="A&D HR-A/HR-AZ manual, sections 21-22 (page 74, drawn at 1:5)",
                           **{k: v for k, v in HR.items()}, rear_column_plan=SPINE, display_wedge_xz=WEDGE))
    print("sampling the hanging parts ...", flush=True)
    mv = moving_samples()
    print("  samples:", len(mv[0]), flush=True)
    res["room"] = {}
    for S in (217.0,) + HEIGHTS:
        prof, low = room_profile(mv, S)
        r_par = [r["r_parked"] for r in prof if r["r_parked"] is not None]
        r_any = [r["r_any_tilt"] for r in prof if r["r_any_tilt"] is not None]
        res["room"][str(int(S))] = dict(shelf_underside_mm=S, lowest_hanging_mm=low,
                                        column_dia_parked_mm=round(2 * min(r_par), 1),
                                        column_dia_any_tilt_mm=round(2 * min(r_any), 1), profile=prof)
        print("room", S, low, 2 * min(r_par), 2 * min(r_any), flush=True)
    res["sweep"] = {}
    for S in HEIGHTS:
        for lid in (True, False):
            rows = sweep(mv, S, lid)
            res["sweep"][f"{int(S)}_{'lid' if lid else 'nolid'}"] = rows
            b = best_of(rows, "t_max")
            print("sweep", S, "lid" if lid else "nolid", "best", b["phi"], "t_max", b["t_max"], "moving", b["moving_0_90"],
                  "parked", b["moving_parked"], "stand", b["stand"], flush=True)
    # summary per height and lid state: the best orientation, the tilt limit there, and the closest approaches
    summ = {}
    for key, rows in res["sweep"].items():
        b = best_of(rows, "t_max")
        ok_parked = [r["phi"] for r in rows if r["moving_parked"] >= GAP and r["stand"] >= GAP and r["shelf"] >= GAP]
        ok_all = [r["phi"] for r in rows if r["t_max"] == 90 and r["stand"] >= GAP and r["shelf"] >= GAP]
        summ[key] = dict(best_phi=b["phi"], t_max=b["t_max"], moving_0_90=b["moving_0_90"], moving_parked=b["moving_parked"],
                         stand=b["stand"], shelf=b["shelf"], phis_ok_parked=ok_parked, phis_ok_0_90=ok_all)
    res["summary"] = summ
    # the configuration to report and render: the lowest height (and lid on, if possible) that takes 0-90 deg
    fit = None
    for S in HEIGHTS:
        for lid in (True, False):
            s = summ[f"{int(S)}_{'lid' if lid else 'nolid'}"]
            if s["t_max"] == 90 and s["stand"] >= GAP and s["shelf"] >= GAP:
                fit = dict(height_mm=S, lid=lid, phi_deg=s["best_phi"])
                break
        if fit:
            break
    if fit is None:                                        # nothing takes 0-90: report the best tilt limit
        best = max(((S, lid) for S in HEIGHTS for lid in (True, False)),
                   key=lambda k: (summ[f"{int(k[0])}_{'lid' if k[1] else 'nolid'}"]["t_max"], -k[0], k[1]))
        s = summ[f"{int(best[0])}_{'lid' if best[1] else 'nolid'}"]
        fit = dict(height_mm=best[0], lid=best[1], phi_deg=s["best_phi"])
    fit["exact"] = exact_check(fit["height_mm"], fit["phi_deg"], fit["lid"])
    print("exact", fit, flush=True)
    # also the exact check at 320 mm with the lid on, display to the front gap (rear column to 90): 20 Nov's set-up
    res["nov20_setup_exact"] = dict(height_mm=320.0, lid=True, phi_deg=90.0,
                                    **exact_check(320.0, 90.0, True, tilts=(0, 30, 60, 90)))
    print("nov20", res["nov20_setup_exact"], flush=True)
    res["fit"] = fit
    if "--no-figures" not in sys.argv:
        res["_mv"] = mv
        figure_room(res, OUT / "scale_room.png")
        print("  -> scale_room.png", flush=True)
        render_fit(res, OUT / "scale_fit.png")
        print("  -> scale_fit.png", flush=True)
        res.pop("_mv")
    (HERE / "scale_room.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()

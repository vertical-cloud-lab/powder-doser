"""One-piece base for the three-auger tri-star (B2 with #203's tap bracket), issue #204, 13 Nov.

Ethan asked for detailed dimensions of the base, with the hinge towers merged into
it. He has also cut the gears and their arms off the mounting plate, so the plate is
now widest at the stepper mount.  This script:

* models the plate that way: PR #170's plate body without the gears, the webs and the
  floor's front wings (|x| > 34 mm), plus the clevis block's two holes;
* builds the base as one part: a 6 mm shelf (three tapered lobes round a 78 mm window,
  a slot per module for the clevis block and actuator rod, four hanger holes per lobe)
  and six hinge towers.  The towers are copied from today's baseplate (PR #170's
  baseplate.step): same profile, 12.3 mm wide, 5.3 mm bore;
* checks every moving part against the base over 0-90 deg (2 mm target) at the
  tri-star's spacing (hinges 32 mm from the beaker axis);
* writes base/base.step and base/base.stl, base.json, renders/base_drawing.png (the
  dimensioned drawing) and renders/base_iso.png.

    xvfb-run -a python base.py        # about 2 min

Frames: the unit frame of doserlib.py (hinge axis = X, +Y = behind the hinge, Z up,
hinge at z = 0, shelf top at z = -37.25).  The drawing and the STEP file use the
beaker axis as the origin, with z = 0 on the base's underside.
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

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
CAD = HERE / "base"
SP = K.SP                         # 32 mm: hinge axis to beaker axis
T = 6.0                           # shelf thickness, as today's baseplate
TOP, BOT = D.BASE_TOP_U, D.BASE_BOT_U       # shelf top / underside in the unit frame (-37.25 / -43.25)
GAP = 2.0
LOBE = dict(half_w=50.0, y_wide=50.0, half_w_end=25.0, y_end=150.0, root=15.0, r=10.0)
WIN_D = 78.0                      # 250 mL beaker (70 mm) + 4 mm a side, as before
SLOT = K.SLOT                     # |x| < 17, 33..120 mm behind the hinge (clevis block + rod)
PAD = dict(x=14.5, y=(126.0, 142.0), d=4.5)  # hanger (or leg) holes, M4
TOWER_X = (28.9, 41.2)            # today's towers, |x| from the module centreline
WING_CUT_X, WING_CUT_Y = 34.0, 70.0          # trim the plate's floor to |x| <= 34 up to 70 mm behind the hinge
BEARINGS = (90.0, 210.0, 330.0)


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #
_S: dict = {}


def tower_today():
    """Today's +X hinge tower, cut out of PR #170's baseplate above its top face, in the unit frame."""
    if "tower" not in _S:
        bp = D.step_shape("fusion-step/baseplate.step")
        H = D.HINGE
        tw = bp.intersect(cq.Solid.makeBox(20.0, 70.0, 60.0, cq.Vector(25.0, H[1] - 25.0, 6.0)))
        _S["tower"] = tw.moved(C._loc(D.W2U)).clean()
    return _S["tower"]


def tower_profile():
    """The tower's side profile (y behind the hinge, z above it) from a section at mid-width."""
    tw = tower_today()
    xm = sum(TOWER_X) / 2
    sec = tw.intersect(cq.Solid.makeBox(0.01, 200, 200, cq.Vector(xm, -100, -100)))
    face = next(f for f in sec.Faces() if abs(f.normalAt().x) > 0.9 and f.Center().x < xm + 0.005)
    out = []
    for e in face.Edges():
        a, b = e.startPoint(), e.endPoint()
        row = dict(kind=e.geomType().lower(), start=[round(a.y, 2), round(a.z, 2)], end=[round(b.y, 2), round(b.z, 2)])
        if e.geomType() == "CIRCLE":
            c = e.arcCenter()
            row.update(radius=round(e.radius(), 2), centre=[round(c.y, 2), round(c.z, 2)])
        out.append(row)
    return out


def plate_trimmed():
    """PR #170's plate without gears, webs and the floor's front wings (Ethan, 13 Nov), plus the
    clevis block's two holes, in the plate's STEP frame (as components.plate_with_holes)."""
    if "plate" not in _S:
        Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]
        inv = C._loc(np.linalg.inv(Mown))
        pl = K.plate_with_holes()
        for sx in (1, -1):
            x0 = WING_CUT_X if sx > 0 else -WING_CUT_X - 40.0
            pl = pl.cut(D.box(x0, x0 + 40.0, -30.0, WING_CUT_Y, -60.0, 40.0).moved(inv))
        _S["plate"] = pl.clean()
    return _S["plate"]


def plate_split():
    """The trimmed plate in two pieces: inboard of the towers' inner faces (|x| < 28.75: the knuckles and
    the arms under them, which run 0.3 mm from the towers' inner faces, as today) and the rest, which
    must clear the base by 2 mm."""
    if "split" not in _S:
        Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]
        inv = C._loc(np.linalg.inv(Mown))
        pl = plate_trimmed()
        mid = D.box(-28.75, 28.75, -40.0, 140.0, -60.0, 40.0).moved(inv)
        _S["split"] = (pl.intersect(mid).clean(), pl.cut(mid).clean())
    return _S["split"]


def lobe_pts():
    """One lobe of the shelf, unit frame (the beaker axis is at y = -SP)."""
    w, yw, we, ye, rt = (LOBE[k] for k in ("half_w", "y_wide", "half_w_end", "y_end", "root"))
    y0 = -SP - rt
    return [(-w, y0), (w, y0), (w, yw), (we, ye), (-we, ye), (-w, yw)]


def station_xy(M, pts):
    return [tuple((M @ np.array([x, y, 0.0, 1.0]))[:2]) for x, y in pts]


def shelf_outline_sketch():
    sk = cq.Sketch()
    for i, th in enumerate(BEARINGS):
        pts = station_xy(D.place(th, SP, 0.0), lobe_pts())
        sk = sk.polygon(pts + [pts[0]], mode="a")
    return sk.clean().reset().vertices().fillet(LOBE["r"]).reset()


def base_station():
    """The base as one solid, station frame (beaker axis = Z, hinge axes at z = 0)."""
    if "base" in _S:
        return _S["base"]
    sk = shelf_outline_sketch()
    shelf = cq.Workplane("XY", origin=(0, 0, BOT)).placeSketch(sk).extrude(T).val()
    shelf = shelf.cut(D.cyl(WIN_D / 2, T + 2, 0, 0, BOT - 1))
    for th in BEARINGS:
        loc = C._loc(D.place(th, SP, 0.0))
        cut = D.box(-SLOT["x"], SLOT["x"], SLOT["y0"], SLOT["y1"], BOT - 1, TOP + 1)
        for x in (-PAD["x"], PAD["x"]):
            for y in PAD["y"]:
                cut = cut.fuse(D.cyl(PAD["d"] / 2, T + 2, x, y, BOT - 1))
        shelf = shelf.cut(cut.moved(loc))
    base = shelf
    tw = tower_today()
    tw_neg = tw.mirror("YZ", (0, 0, 0))          # a true mirror (a det = -1 matrix would turn the solid inside out)
    for th in BEARINGS:
        loc = C._loc(D.place(th, SP, 0.0))
        base = base.fuse(tw.moved(loc)).fuse(tw_neg.moved(loc))
    _S["base"] = base.clean()
    return _S["base"]


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def shelf_only():
    if "shelf" not in _S:
        sk = shelf_outline_sketch()
        sh = cq.Workplane("XY", origin=(0, 0, BOT)).placeSketch(sk).extrude(T).val()
        _S["shelf"] = sh.cut(D.cyl(WIN_D / 2, T + 2, 0, 0, BOT - 1))
    return _S["shelf"]


def station_parts(tilts, units="ABC"):
    """The modules' parts at ``tilts`` (no placeholder towers, hangers, U-brackets or their pins), the
    trimmed plate split in two (plate_split), the base as one fixed part, and its shelf alone."""
    parts = []
    inner, outer = plate_split()
    for i, th in enumerate(BEARINGS):
        if "ABC"[i] not in units:
            continue
        M = D.place(th, SP, 0.0)
        for p in K.module(float(tilts[i]), M, "ABC"[i], with_hanger=False):
            if p.kind == "tower" or p.name.endswith(("P16 bracket", "#8-32 pin")):
                continue
            if p.name.endswith("Mounting plate"):
                parts.append(D.Part(p.name + " (inboard)", inner, p.M, p.colour, p.unit, True))
                p.shape = outer
            parts.append(p)
    parts.append(D.Part("base", base_station(), np.eye(4), (0.95, 0.47, 0.18), "fixed", False))
    parts.append(D.Part("shelf", shelf_only(), np.eye(4), (0.95, 0.47, 0.18), "fixed", False))
    return parts


def pair_ok(a, b):
    """Which pairs to measure: different units; the plate's inboard piece against the shelf only (it runs
    0.3 mm from its own towers by design); everything else against the whole base."""
    if a.unit == b.unit:
        return False
    for x, y in ((a, b), (b, a)):
        if y.name == "shelf":
            return x.name.endswith("(inboard)")
        if y.name == "base" and x.name.endswith("(inboard)"):
            return False
    return True


def clear(parts, only=None):
    import fcl
    objs = [(p, fcl.CollisionObject(D._bvh(p.shape), fcl.Transform(p.M[:3, :3], p.M[:3, 3]))) for p in parts]
    best = (1e9, None, None)
    req = fcl.DistanceRequest(enable_nearest_points=False)
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            pa, oa = objs[i]
            pb, ob = objs[j]
            if not pair_ok(pa, pb) or (only and not only(pa, pb)):
                continue
            d = fcl.distance(oa, ob, req, fcl.DistanceResult())
            if d < best[0]:
                best = (d, pa.name, pb.name)
    return best


CASES = [(0, 0, 0), (30, 30, 30), (45, 45, 45), (60, 60, 60), (90, 90, 90), (90, 0, 0),
         (60, 0, 0), (90, 90, 0), (60, 60, 0), (30, 60, 0)]


def checks():
    """(1) one module's parts against the base, 0..90 deg in 5 deg steps; (2) the three modules against
    each other and the base at the B2T tilt cases; (3) the hinge's running gap (knuckle to tower)."""
    out = {}
    worst, per_tilt = (1e9, None, None, None), {}
    for t in range(0, 91, 5):
        d, a, b = clear(station_parts((t, 0, 0), units="A"))
        per_tilt[str(t)] = round(d, 2)
        if d < worst[0]:
            worst = (d, a, b, t)
    out["one_module_to_base"] = dict(mm=round(worst[0], 2), between=f"{worst[1]} / {worst[2]}", at_tilt=worst[3],
                                     by_tilt=per_tilt)
    print("  one module:", out["one_module_to_base"], flush=True)
    cases = {}
    for c in CASES:
        ps = station_parts(c)
        d, a, b = clear(ps)
        dm, am, bm = clear(ps, only=lambda x, y: "fixed" not in (x.unit, y.unit))
        cases[",".join(map(str, c))] = dict(mm=round(d, 2), between=f"{a} / {b}", modules_only_mm=round(dm, 2),
                                            modules_only_between=f"{am} / {bm}")
        print(f"  tilts {c}: {d:.2f} mm ({a} / {b}); between modules {dm:.2f} ({am} / {bm})", flush=True)
    out["station_cases"] = cases
    pl = plate_trimmed()
    Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]
    m = D.mesh_of(pl)
    v = (Mown[:3, :3] @ np.asarray(m.vertices).T).T + Mown[:3, 3]
    near = v[np.hypot(v[:, 1], v[:, 2]) < 7.6]
    kx = float(np.abs(near[:, 0]).max())
    out["knuckle_outer_face_x"] = round(kx, 2)
    out["knuckle_to_tower_gap"] = round(TOWER_X[0] - kx, 2)
    return out


def plate_extent():
    pl = plate_trimmed()
    Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]
    m = D.mesh_of(pl)
    v = (Mown[:3, :3] @ np.asarray(m.vertices).T).T + Mown[:3, 3]
    lo, hi = v.min(0), v.max(0)
    floor = v[(v[:, 2] < TOP + 2.0 + 6.5) & (v[:, 2] > TOP + 1.5)]
    widest_y = float(floor[np.argmin(floor[:, 0]), 1])
    return dict(x=[round(lo[0], 2), round(hi[0], 2)], y=[round(lo[1], 2), round(hi[1], 2)], z=[round(lo[2], 2), round(hi[2], 2)],
                width=round(hi[0] - lo[0], 2), widest_at_y_behind_hinge=round(widest_y, 1),
                volume_cm3=round(pl.Volume() / 1000.0, 1))


# --------------------------------------------------------------------------- #
# export
# --------------------------------------------------------------------------- #
def base_export_shape():
    """Base with the beaker axis at the origin and z = 0 on its underside."""
    return base_station().moved(cq.Location(cq.Vector(0, 0, -BOT)))


def export():
    CAD.mkdir(parents=True, exist_ok=True)
    sh = base_export_shape()
    cq.exporters.export(cq.Workplane().add(sh), str(CAD / "base.step"))
    cq.exporters.export(cq.Workplane().add(sh), str(CAD / "base.stl"), tolerance=0.05, angularTolerance=0.1)
    bb = sh.BoundingBox()
    return dict(x=[round(bb.xmin, 2), round(bb.xmax, 2)], y=[round(bb.ymin, 2), round(bb.ymax, 2)],
                z=[round(bb.zmin, 2), round(bb.zmax, 2)], volume_cm3=round(sh.Volume() / 1000.0, 1))


def min_box(shape, step=0.5):
    """Smallest axis-aligned footprint over in-plane rotations (for the print bed)."""
    m = D.mesh_of(shape)
    v = np.asarray(m.vertices)[:, :2]
    best = (1e9, None, None)
    for a in np.arange(0.0, 120.0, step):
        r = math.radians(a)
        R = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
        w = v @ R.T
        ext = w.max(0) - w.min(0)
        if max(ext) < best[0]:
            best = (max(ext), a, ext)
    return dict(angle_deg=best[1], size=[round(float(best[2][0]), 1), round(float(best[2][1]), 1)])


if __name__ == "__main__":
    import sys
    res = dict(spacing_hinge_to_beaker_axis=SP, shelf_thickness=T, lobe=LOBE, window_dia=WIN_D, slot=SLOT, pad=PAD,
               tower_x=TOWER_X, wing_cut=dict(x=WING_CUT_X, y_up_to=WING_CUT_Y))
    res["plate_trimmed"] = plate_extent()
    print("plate", res["plate_trimmed"], flush=True)
    res["tower_profile"] = tower_profile()
    res["export"] = export()
    print("export", res["export"], flush=True)
    res["print_footprint"] = min_box(base_export_shape())
    print("footprint", res["print_footprint"], flush=True)
    if "--no-checks" not in sys.argv:
        res["checks"] = checks()
        print(json.dumps(res["checks"], indent=1), flush=True)
    (HERE / "base.json").write_text(json.dumps(res, indent=1) + "\n")

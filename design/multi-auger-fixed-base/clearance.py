"""Room under the B2 tri-star with #203's tap bracket (issue #204, 10 Nov).

Philip asked what clearance there is under the doser, whether the hinge
towers set it, and whether a stand could change it.  This script measures it
on the same model as concepts.py (PR #170's STEP files, Ethan's tap bracket,
hinges 32 mm from the beaker axis):

* the "ceiling" over the beaker axis: for a vessel of radius R, the lowest
  point of any doser part within R of the axis, over every tilt 0..90 deg
  (each unit's parts depend only on its own tilt, and the three units are
  copies at 120 deg, so one unit swept over 0..90 covers every tilt mix);
* how far the actuators hang below the shelf, and how close they come to
  the axis under it;
* the stand height (bench to shelf underside) that some beaker and
  Erlenmeyer stacks need, on a placeholder stir plate.

    xvfb-run -a python clearance.py    # about 1 min; writes clearance.json and renders/b2_clearance.png

Heights are in the station frame of concepts.py: z = 0 on the hinge axis.
The stand, stir plate, riser, funnel and glassware are placeholders.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import doserlib as D
import concepts as C

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
KEY = "B2T"
GAP = 2.0                        # clearance to the doser (mm)
RIM_BELOW_90 = 15.0              # beaker rim under the 90 deg outlets, as in the other figures
SHELF_T = D.BASE_TOP_U - D.BASE_BOT_U          # 6 mm
STIR = dict(w=150.0, h=100.0, top=135.0)       # placeholder stir plate: 150 x 150 x 100, 135 mm top plate
FOOT = 8.0                       # base clevis under the actuator's lower eye, down to its foot
FUNNEL = dict(mouth=80.0, stem=16.0, stem_len=40.0, wall=1.5)   # 60 deg powder funnel
NECK_WALL = 2.0                  # Erlenmeyer neck wall: inside dia = outside dia - 4 mm (estimate)

# DURAN (ISO 1773 narrow neck / ISO 24450 wide neck) catalogue sizes: body dia, height, neck outside dia
ERLENMEYER = {"250 mL": (85.0, 145.0, 34.0), "500 mL": (105.0, 180.0, 34.0), "1 L": (131.0, 220.0, 42.0),
              "500 mL wide neck": (105.0, 175.0, 50.0)}


def _samples(shape, density=2.0, _cache={}):
    """Mesh vertices plus area-weighted random surface points (about 2 per mm^2)."""
    import trimesh
    k = id(shape)
    if k not in _cache:
        m = D.mesh_of(shape)
        pts, _ = trimesh.sample.sample_surface(m, max(200, int(m.area * density)), seed=1)
        _cache[k] = np.vstack([m.vertices, pts])
    return _cache[k]


def ceiling(sp, tilts=range(0, 91, 5), dr=0.5, rmax=140.0):
    """For each radius R, the lowest z of any part of a unit within R of the beaker axis, over
    every tilt (the shelf is left out: its window is a free choice).  Also the actuators'
    closest approach to the axis below the shelf, and their lowest point."""
    R = np.arange(0.0, rmax + 1e-9, dr)
    env = np.full_like(R, np.inf)
    who = [None] * len(R)
    p16_rmin, p16_zmin = {}, np.inf
    for tl in tilts:
        parts, _ = C.layout(KEY, sp, (tl, tl, tl), extras=False)
        rmin = np.inf
        for p in parts:
            if not p.name.startswith("A:"):
                continue
            v = _samples(p.shape)
            w = (p.M[:3, :3] @ v.T).T + p.M[:3, 3]
            r = np.hypot(w[:, 0], w[:, 1])
            if "P16" in p.name:
                below = w[:, 2] < D.BASE_BOT_U
                if below.any():
                    rmin = min(rmin, float(r[below].min()))
                p16_zmin = min(p16_zmin, float(w[:, 2].min()))
            o = np.argsort(r)
            rs, zs = r[o], np.minimum.accumulate(w[o, 2])
            idx = np.searchsorted(rs, R, side="right") - 1
            c = np.where(idx >= 0, zs[np.clip(idx, 0, None)], np.inf)
            for i in np.nonzero(c < env)[0]:
                who[i] = (p.name[2:], tl)
            env = np.minimum(env, c)
        p16_rmin[tl] = round(rmin, 1)
        print(f"  tilt {tl:2d}: actuators come within {rmin:.1f} mm of the axis below the shelf", flush=True)
    return R, env, who, p16_rmin, p16_zmin


def funnel_rise(neck_od):
    """How far the funnel's mouth stands above the neck it sits in (60 deg cone)."""
    r_in = neck_od / 2 - NECK_WALL
    return (FUNNEL["mouth"] / 2 - r_in) / math.tan(math.radians(30.0))


def stacks(lv):
    """Stand height (bench to shelf underside) for each vessel on the placeholder stir plate."""
    sp_h = STIR["h"]
    rows = []
    for kind, (d, h) in C.BEAKERS.items():
        stack = sp_h + h
        if d / 2 <= lv["window_r"] - 1.5:          # rises between the towers: rim 15 mm under the 90 deg outlets
            rim = lv["outlet_90"] - RIM_BELOW_90
            where = "between the towers, rim 15 mm under the 90 deg outlets"
        else:                                       # too wide for the window: rim under the shelf
            rim = D.BASE_BOT_U - GAP
            where = "under the shelf, rim 2 mm below it"
        need = stack - (rim - D.BASE_BOT_U)        # bench to shelf underside
        S = max(need, lv["S_min"])
        rows.append(dict(vessel=f"{kind} beaker ({d:.0f} x {h:.0f} mm)", stack=stack, where=where,
                         stand_needed=round(need, 1), stand=round(S, 1), riser=round(S - need, 1),
                         gap_to_90deg_outlets=round(lv["outlet_90"] - rim, 1)))
    for kind, (d, h, dn) in ERLENMEYER.items():
        rise = funnel_rise(dn)
        stack = sp_h + h + rise
        need = stack + GAP
        S = max(need, lv["S_min"])
        rows.append(dict(vessel=f"{kind} Erlenmeyer ({d:.0f} x {h:.0f} mm, neck {dn:.0f}) + {FUNNEL['mouth']:.0f} mm funnel",
                         stack=round(stack, 1), where="funnel mouth 2 mm under the shelf", stand_needed=round(need, 1),
                         stand=round(S, 1), riser=round(S - need, 1), funnel_rise=round(rise, 1),
                         gap_to_90deg_outlets=round(lv["outlet_90"] - (D.BASE_BOT_U - GAP), 1)))
    return rows


# --------------------------------------------------------------------------- #
# placeholder geometry
# --------------------------------------------------------------------------- #
def _revolve(pts):
    import cadquery as cq
    return cq.Workplane("XZ").polyline(pts).close().revolve(360.0, (0, 0, 0), (0, 1, 0)).val()


def erlenmeyer(d, h, dn, neck_h=None, t=NECK_WALL):
    """Conical flask as a glass shell, base at z = 0 (outline only, from the catalogue sizes)."""
    rb, rn = d / 2, dn / 2
    neck_h = neck_h or 0.2 * h
    zc, zn = 10.0, h - neck_h
    return _revolve([(0, 0), (rb - 6, 0), (rb, 6), (rb, zc), (rn, zn), (rn, h), (rn - t, h), (rn - t, zn + 1.0),
                     (rb - t, zc + 0.8), (rb - t, 6.5), (rb - 6.5, t), (0, t)])


def funnel():
    """60 deg powder funnel, stem tip at z = 0."""
    rm, rs, sl, t = FUNNEL["mouth"] / 2, FUNNEL["stem"] / 2, FUNNEL["stem_len"], FUNNEL["wall"]
    hc = (rm - rs) / math.tan(math.radians(30.0))
    return _revolve([(rs - t, 0), (rs, 0), (rs, sl), (rm, sl + hc), (rm - 1.7 * t, sl + hc), (rs - t, sl + 1.0)])


def column(r_col, z0, z1, r_win, z2):
    """The room for a vessel: radius r_col from z0 up to z1 (the shelf underside), then r_win up to z2."""
    return _revolve([(0, z0), (r_col, z0), (r_col, z1), (r_win, z1), (r_win, z2), (0, z2)])


def stand(Ms, S, lv):
    """Three legs under the shelf's lobes and a hanger per actuator holding its base clevis."""
    zb = D.BASE_BOT_U - S
    out = [D.Part("bench", D.box(-320, 0.3, -420, 420, zb - 10, zb), np.eye(4), (0.80, 0.78, 0.74), "fixed")]
    pin = -C.ACT_C - D.P16["closed"] - 5.0
    for i, M in enumerate(Ms):
        leg = D.box(-10, 10, 165, 185, zb, D.BASE_BOT_U)
        out.append(D.Part(f"leg {i}", leg, M, D.COL["new"], "fixed"))
        hang = D.box(-10, 10, C.ACT_A + 19, C.ACT_A + 25, pin - 4.5 - FOOT, D.BASE_BOT_U)
        foot = D.box(-10, 10, C.ACT_A - 9, C.ACT_A + 25, pin - 4.5 - FOOT, pin - 4.5 - 2.0)
        cheeks = D.box(4.5, 7.5, C.ACT_A - 7, C.ACT_A + 7, pin - 4.5 - 2.0, pin + 6).fuse(
            D.box(-7.5, -4.5, C.ACT_A - 7, C.ACT_A + 7, pin - 4.5 - 2.0, pin + 6))
        out.append(D.Part(f"hanger {i}", hang.fuse(foot).fuse(cheeks), M, D.COL["new"], "fixed"))
    return out


def stir_plate(z_top):
    w, h = STIR["w"], STIR["h"]
    body = D.box(-w / 2, w / 2, -w / 2, w / 2, z_top - h, z_top - 3)
    top = D.cyl(STIR["top"] / 2, 3.0, 0, 0, z_top - 3)
    return [D.Part("stir plate", body, np.eye(4), (0.30, 0.31, 0.34), "fixed"),
            D.Part("stir plate top", top, np.eye(4), (0.92, 0.92, 0.92), "fixed")]


def stir_plate_check(sp, lv, tilts=range(0, 91, 10)):
    """On the shortest stand the stir plate stands among the actuators' lower ends: how close they
    come to the axis below the plate's top, and to the placeholder plate itself, over 0..90 deg."""
    S = lv["S_min"]
    zb = D.BASE_BOT_U - S
    rmin, worst = np.inf, (np.inf, None, None, None)
    for tl in tilts:
        parts, Ms = C.layout(KEY, sp, (tl,) * 3, extras=False)
        parts += stand(Ms, S, lv)
        others = [p for p in parts if "P16" in p.name or p.name.startswith(("hanger", "leg"))]
        for p in others:
            p.unit = "doser"
            v = _samples(p.shape)
            w = (p.M[:3, :3] @ v.T).T + p.M[:3, 3]
            sel = w[:, 2] < zb + STIR["h"]
            if sel.any():
                rmin = min(rmin, float(np.hypot(w[sel, 0], w[sel, 1]).min()))
        plate = stir_plate(zb + STIR["h"])
        for q in plate:
            q.unit = "stir plate"
        d, a, b = D.clearance(plate + others)
        if d < worst[0]:
            worst = (d, a, b, tl)
    foot = D.BASE_BOT_U - (lv["p16_bottom"] - FOOT)          # foot of the base clevis, below the shelf underside
    return dict(stand=S, actuators_within_r_below_plate_top=round(rmin, 1), placeholder_gap=round(worst[0], 1),
                between=f"{worst[1]} / {worst[2]}", at_tilt=worst[3],
                stand_with_actuators_above_plate=float(math.ceil(foot + STIR["h"] + GAP)))


# --------------------------------------------------------------------------- #
# figure
# --------------------------------------------------------------------------- #
PX = 1.6                     # pixels per mm
VIEW_Y = (-450.0, 320.0)     # station y shown (left margin for the labels)
VIEW_Z = (-395.0, 150.0)     # station z shown, measured from the hinge with the tallest stand


def render_panel(parts, S, fn):
    """Half-section from +X at a fixed scale; the bench sits at the same pixel row in every panel."""
    zb = D.BASE_BOT_U - S
    zb_ref = VIEW_Z[0] + 25.0                     # bench row in the tallest panel
    dz = zb - zb_ref                               # shift so the bench lines up
    W = round((VIEW_Y[1] - VIEW_Y[0]) * PX)
    H = round((VIEW_Z[1] - VIEW_Z[0]) * PX)
    fy = (VIEW_Y[0] + VIEW_Y[1]) / 2
    fz = (VIEW_Z[0] + VIEW_Z[1]) / 2 + dz
    D.render(parts, fn, view="side", size=(W, H), parallel=True, dist=(VIEW_Z[1] - VIEW_Z[0]) / 2,
             focal=(0.0, fy, fz), clip_x=0.3, fixed=True)
    return lambda y, z: (W / 2 + (y - fy) * PX, H / 2 - (z - fz) * PX)


def annotate(fn, to_px, S, marks, notes=()):
    """Level lines with their height above the bench in the left margin; marks = [(z, name, colour)]."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(fn).convert("RGB")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(C.FONT, 21)
    fb = ImageFont.truetype(C.FONT_B, 24)
    zb = D.BASE_BOT_U - S
    marks = sorted(marks, key=lambda m: -m[0]) + [(zb, "bench", (40, 40, 40))]
    last = -1e9
    for z, name, col in marks:
        x0, y = to_px(-212.0, z)
        x1 = to_px(-25.0, z)[0]
        for xx in range(int(x0), int(x1), 14):        # dashed level line
            d.line([(xx, y), (min(xx + 8, x1), y)], fill=col, width=2)
        ty = max(y - 13, last + 25)                    # keep close labels apart
        d.text((14, ty), f"{z - zb:4.0f} mm", font=f, fill=col)
        d.text((112, ty), name, font=f, fill=col)
        last = ty
    for i, ln in enumerate(notes):
        d.text((14, 14 + 32 * i), ln, font=fb if i == 0 else f, fill=(30, 30, 30))
    im.save(fn)


def figure(res):
    lv = res["levels"]
    sp = res["spacing"]
    S0 = lv["S_min"]
    tilts = (30, 0, 0)
    win_r = lv["window_r"] - 0.4

    def doser(S):
        parts, Ms = C.layout(KEY, sp, tilts, extras=False)
        parts.append(D.Part("shelf", C.shelf(Ms, win_r, slot=True), np.eye(4), D.COL["base"], "fixed"))
        return parts + C.outlet_marks(Ms, tilts) + stand(Ms, S, lv), Ms

    red, blue, grey = (200, 30, 30), (40, 90, 200), (90, 90, 90)
    common = [(0.0, "outlets at 0 deg (hinge)", red), (lv["outlet_90"], "outlets at 90 deg", red),
              (D.BASE_BOT_U, "shelf underside", (40, 40, 40))]
    paths = []

    # 1. the room itself, on the shortest stand
    parts, Ms = doser(S0)
    zb = D.BASE_BOT_U - S0
    vw = 2 * (lv["window_r"] - 1.5)
    room = D.Part("room", column(lv["column_r"], zb, D.BASE_BOT_U, vw / 2, lv["top_in_window"]),
                  np.eye(4), (0.35, 0.60, 0.95), "fixed", False, 0.30)
    fn = OUT / "_cl1.png"
    to_px = render_panel(parts + [room], S0, fn)
    annotate(fn, to_px, S0, common + [(lv["top_in_window"], f"top of a vessel up to {vw:.0f} mm wide", blue),
                                      (lv["p16_bottom"], "actuators' lower ends", grey)],
             notes=(f"1  The room under it, on the shortest stand",
                    f"Blue: {2 * lv['column_r']:.0f} mm wide up to the shelf,",
                    f"{vw:.0f} mm wide up between the hinge towers."))
    paths.append(fn)

    # 2. 250 mL beaker on the stir plate, shortest stand, with a riser
    row = next(r for r in res["stacks"] if r["vessel"].startswith("250 mL beaker"))
    rim = lv["outlet_90"] - RIM_BELOW_90
    parts, Ms = doser(S0)
    zsp = zb + STIR["h"]
    riser = row["riser"]
    parts += stir_plate(zsp)
    parts.append(D.Part("riser", D.box(-45, 45, -45, 45, zsp, zsp + riser), np.eye(4), (0.70, 0.72, 0.76), "fixed"))
    parts.append(C.beaker_part("250 mL", rim))
    fn = OUT / "_cl2.png"
    to_px = render_panel(parts, S0, fn)
    annotate(fn, to_px, S0, common + [(rim, "beaker rim", blue), (zsp + riser, "riser", grey),
                                      (zsp, "stir plate (placeholder)", grey)],
             notes=(f"2  250 mL beaker, same stand",
                    f"{STIR['h']:.0f} mm stir plate + {riser:.0f} mm riser; the rim",
                    f"rises between the towers, {RIM_BELOW_90:.0f} mm under the 90 deg outlets."))
    paths.append(fn)

    # 3. 500 mL Erlenmeyer + funnel, on a taller stand
    row = next(r for r in res["stacks"] if r["vessel"].startswith("500 mL Erlenmeyer"))
    S = float(math.ceil(row["stand"]))
    db, hb, dn = ERLENMEYER["500 mL"]
    parts, Ms = doser(S)
    zb3 = D.BASE_BOT_U - S
    zsp = zb3 + STIR["h"]
    parts += stir_plate(zsp)
    parts.append(D.Part("flask", erlenmeyer(db, hb, dn), D.Tt(0, 0, zsp), D.COL["glass"], "fixed", False, 0.45))
    seat = FUNNEL["stem_len"] + (dn / 2 - NECK_WALL - FUNNEL["stem"] / 2) / math.tan(math.radians(30.0))
    parts.append(D.Part("funnel", funnel(), D.Tt(0, 0, zsp + hb - seat), (0.55, 0.75, 0.90), "fixed", False, 0.75))
    mouth = zsp + hb + row["funnel_rise"]
    fn = OUT / "_cl3.png"
    to_px = render_panel(parts, S, fn)
    annotate(fn, to_px, S, common + [(mouth, "funnel mouth", blue), (zsp + hb, "flask neck", blue),
                                     (zsp, "stir plate (placeholder)", grey)],
             notes=(f"3  500 mL Erlenmeyer + {FUNNEL['mouth']:.0f} mm funnel",
                    f"Its {dn:.0f} mm neck can't catch three outlets, so a funnel",
                    f"sits in it, mouth under the shelf. Stand {S:.0f} mm."))
    paths.append(fn)

    C.side_by_side(paths, OUT / "b2_clearance.png",
                   "Room under the tri-star: a stand sets it; the hinge towers only put the outlets 26-37 mm above the shelf",
                   [f"Half-section through one module's centreline: that module (right) at 30 deg, the others at 0. Heights from the bench."
                    f" Hinges {sp} mm from the beaker axis, {-D.BASE_TOP_U:.1f} mm above the shelf top.",
                    f"The P16s hang {D.BASE_BOT_U - lv['p16_bottom']:.0f} mm below the shelf, so the stand can't be shorter than about"
                    f" {S0:.0f} mm; a taller one adds room 1:1. Below the shelf the actuators leave a {2 * lv['column_r']:.0f} mm"
                    f" column ({2 * lv['column_r_60']:.0f} mm if no module goes past 60 deg).",
                    "Placeholders: stand legs, actuator hangers, stir plate (150 x 150 x 100 mm), riser, funnel. Glassware from"
                    " DURAN (Erlenmeyer) and ISO 3819 (beaker) catalogue sizes."])
    print("  -> b2_clearance.png", flush=True)


def main():
    rpath = HERE / "results.json"
    base = json.loads(rpath.read_text())
    sp = base["working_spacing"][KEY]
    R, env, who, p16_rmin, p16_zmin = ceiling(sp)
    # the towers' inner corners bound the window: a vessel wider than this stops under the shelf
    tower_r = math.hypot(sp - 9.0, 28.9)
    i_win = int(np.searchsorted(R, tower_r - 1.5, side="right") - 1)
    lv = dict(
        hinge=0.0, shelf_top=D.BASE_TOP_U, shelf_underside=D.BASE_BOT_U, outlet_0=0.0,
        outlet_90=-D.OUTLET_AHEAD, window_r=round(tower_r, 2),
        lowest_tube_in_window=round(float(env[i_win]), 2), lowest_tube_by=list(who[i_win]),
        top_in_window=round(float(env[i_win]) - GAP, 2),
        p16_bottom=round(p16_zmin, 2), column_r=round(min(p16_rmin.values()), 1),
        column_r_60=round(min(v for k, v in p16_rmin.items() if k <= 60), 1),
    )
    lv["S_min"] = float(math.ceil(D.BASE_BOT_U - lv["p16_bottom"] + FOOT))
    res = dict(spacing=sp, levels=lv, p16_rmin_by_tilt=p16_rmin,
               ceiling=dict(R=[float(r) for r in R[::4]], z=[round(float(z), 2) if np.isfinite(z) else None for z in env[::4]]),
               stir_plate=STIR, funnel=FUNNEL)
    res["stacks"] = stacks(lv)
    res["stir_plate_check"] = stir_plate_check(sp, lv)
    print(res["stir_plate_check"])
    (HERE / "clearance.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(lv, indent=1))
    for r in res["stacks"]:
        print(r)
    OUT.mkdir(exist_ok=True)
    figure(res)


if __name__ == "__main__":
    main()

"""Is the tri-star's mounting plate the current one without its gears?  (issue #204, 13 Nov)

Ethan asked whether the gearless mounting plate in the tri-star renders has the
same dimensions as the current plate.  This measures PR #170's mounting-plate.step
body by body against the plate components.py draws (PR #170's 'plate' body plus
the clevis block's two holes), lists every hole in the floor and the part that
uses it, and draws the two side by side.  Renders only: nothing touches Onshape.

    xvfb-run -a python plate.py      # about 10 s; writes plate.json and renders/plate_compare.png

Frame (as in doserlib): hinge axis = X through the origin, outlet towards -Y
(the front), +Y towards the rear, Z up; the plate at tilt 0.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import doserlib as D
import concepts as C
import components as CP

HERE = Path(__file__).resolve().parent
MOWN = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]      # plate's STEP frame -> unit frame
GREY = (0.80, 0.82, 0.86)
GONE = (0.86, 0.30, 0.27)                                     # gears and webs, not in the tri-star
TOWER_COL = (0.45, 0.55, 0.70)
RING = {   # who uses each floor hole in the tri-star
    "rear": ("rear Flexible Bracket (as today)", CP.STATUS["reuse"][2]),
    "tap": ("#203's tap bracket", CP.STATUS["t203"][2]),
    "free": ("not used (was the tap collar's base)", (0.55, 0.55, 0.57)),
    "new": ("new: clevis block, 2 x M3", CP.STATUS["new"][2]),
}


# --------------------------------------------------------------------------- #
# measurements
# --------------------------------------------------------------------------- #
def verts(shape, M=MOWN):
    m = D.mesh_of(shape)
    return (M[:3, :3] @ np.asarray(m.vertices).T).T + M[:3, 3]


def extent(shapes):
    v = np.vstack([verts(s) for s in shapes])
    lo, hi = v.min(0), v.max(0)
    return dict(x=[round(float(lo[0]), 2), round(float(hi[0]), 2)], y=[round(float(lo[1]), 2), round(float(hi[1]), 2)],
                z=[round(float(lo[2]), 2), round(float(hi[2]), 2)], size_WxLxH=[round(float(e), 2) for e in hi - lo])


def cylinders(shape, rmax=8.0):
    """Cylindrical faces of radius <= rmax: (radius, axis in the unit frame, face bounds in the unit frame)."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder
    out = []
    for f in shape.Faces():
        ad = BRepAdaptor_Surface(f.wrapped)
        if ad.GetType() != GeomAbs_Cylinder or ad.Cylinder().Radius() > rmax:
            continue
        c = ad.Cylinder()
        d = c.Axis().Direction()
        ax = MOWN[:3, :3] @ np.array([d.X(), d.Y(), d.Z()])
        bb = f.BoundingBox()
        q = (MOWN[:3, :3] @ np.array([[bb.xmin, bb.ymin, bb.zmin], [bb.xmax, bb.ymax, bb.zmax]]).T).T + MOWN[:3, 3]
        out.append((round(c.Radius(), 2), np.round(np.abs(ax), 3), q.min(0), q.max(0)))
    return out


def floor_holes(shape):
    """Vertical holes through the floor (z -35.25..-29.25): unique (x, y) centres."""
    out = {}
    for r, ax, lo, hi in cylinders(shape, 2.0):
        if ax[2] > 0.99 and hi[2] <= -29.0:
            key = (round((lo[0] + hi[0]) / 2, 1), round((lo[1] + hi[1]) / 2, 2))
            out[key] = round(2 * r, 1)
    return dict(sorted(out.items(), key=lambda kv: (kv[0][1], kv[0][0])))


def hole_use(x, y):
    if abs(y - 124.0) < 0.5:
        return "rear"
    if abs(y - 58.33) < 0.5 or (abs(y - 42.33) < 0.5 and x < 0):
        return "tap"
    if abs(y - 42.33) < 0.5:
        return "free"
    return "new"


def bracket_holes():
    """Vertical floor-screw holes in #203's tap bracket (unit frame), to check they land on the plate's holes."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder
    br = D.tap_bracket_shapes()["Tap bracket (#203)"]
    out = set()
    for f in br.Faces():
        ad = BRepAdaptor_Surface(f.wrapped)
        if ad.GetType() != GeomAbs_Cylinder:
            continue
        d = ad.Cylinder().Axis().Direction()
        if abs(abs(d.Z()) - 1) > 1e-3 or ad.Cylinder().Radius() > 2.0:
            continue
        bb = f.BoundingBox()
        c = (D.W2U @ np.array([(bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, bb.zmin, 1.0]))[:3]
        out.add((round(float(c[0]), 1), round(float(c[1]), 2), round(2 * ad.Cylinder().Radius(), 1)))
    return sorted(out, key=lambda t: (t[1], t[0]))


def width_at(shape, y, z0=-35.0, z1=-29.5):
    """The floor's x extent at one y (slab through the floor only)."""
    inv = np.linalg.inv(MOWN)
    slab = D.box(-80, 80, y - 0.05, y + 0.05, z0, z1).moved(C._loc(inv))
    s = shape.intersect(slab)
    if not s.Solids():
        return None
    v = verts(s)
    return [round(float(v[:, 0].min()), 2), round(float(v[:, 0].max()), 2)]


def measure():
    b = D.mp_bodies()
    gl = CP._shape("plate", CP.plate_with_holes)
    res = {"source": f"PR #170 cad/full-assembly/components/fusion-step/mounting-plate.step @ {D.PR170_SHA[:7]}",
           "frame": "hinge axis = X through the origin; -Y = front (outlet), +Y = rear; Z up; tilt 0"}
    res["bodies_in_step"] = {k: dict(volume_mm3=round(s.Volume(), 1), **extent([s])) for k, s in b.items()}
    res["current_plate_with_gears"] = extent(list(b.values()))
    res["gearless_plate"] = extent([gl])
    res["volume_mm3"] = dict(current=round(sum(s.Volume() for s in b.values()), 1), gearless=round(gl.Volume(), 1))
    res["volume_mm3"]["removed_pct"] = round(100 * (1 - res["volume_mm3"]["gearless"] / res["volume_mm3"]["current"]), 1)
    res["volume_mm3"]["taken_by_the_two_new_holes"] = round(b["plate"].Volume() - gl.Volume(), 1)
    res["volume_mm3"]["two_3.4mm_holes_through_6mm"] = round(2 * math.pi * 1.7 ** 2 * 6.0, 1)
    res["floor_widths_x"] = {f"{y:g} mm behind the hinge": width_at(gl, y) for y in (25.0, 45.0, 70.0, 86.33, 110.0)}
    hs = floor_holes(gl)
    res["floor_holes"] = [dict(x=k[0], y=k[1], dia=v, used_by=RING[hole_use(*k)][0]) for k, v in hs.items()]
    res["tap_bracket_floor_holes"] = [dict(x=x, y=y, dia=d) for x, y, d in bracket_holes()]
    # the hinge stack on each side: knuckle (plate), tower (base), gear (plate), along X
    kn = [(lo, hi) for r, ax, lo, hi in cylinders(b["plate"]) if r == 7.5 and ax[0] > 0.99 and lo[0] > 0]
    bore_p = sorted({r for r, ax, lo, hi in cylinders(b["plate"]) if ax[0] > 0.99 and r < 4})
    bore_g = sorted({r for r, ax, lo, hi in cylinders(b["gear+X"]) if ax[0] > 0.99 and r < 4})
    res["hinge_stack_plus_x"] = dict(
        knuckle=[round(float(kn[0][0][0]), 2), round(float(kn[0][1][0]), 2)], knuckle_od=15.0, knuckle_bore=round(2 * bore_p[0], 2),
        tower_today=[28.9, 41.2], tower_bore_today=5.3, tower_tristar=[28.9, 37.0],
        gear=list(D.L.GEAR_PLANE_X), gear_bore=round(2 * bore_g[0], 2), gear_tip_dia=round(2 * res["bodies_in_step"]["gear+X"]["z"][1], 2))
    return res


# --------------------------------------------------------------------------- #
# figure
# --------------------------------------------------------------------------- #
def ring(x, y, r_in=1.7, r_out=3.6, z=-29.25):
    return D.cyl(r_out, 0.4, x, y, z).cut(D.cyl(r_in, 2.0, x, y, z - 0.8))


def arrow(d, tip, u, col, ln=13, w=5):
    px, py = -u[1], u[0]
    d.polygon([tip, (tip[0] - u[0] * ln + px * w, tip[1] - u[1] * ln + py * w),
               (tip[0] - u[0] * ln - px * w, tip[1] - u[1] * ln - py * w)], fill=col)


def dim(d, ren, H, f1, f2, l1, l2, text, f, col=(25, 25, 25), side=(0, -1), pad=8):
    """Dimension: extension lines from features f1, f2 to the dim line l1-l2 (unit frame), arrows, boxed label."""
    P = lambda p: CP.project(ren, np.asarray(p, float), H)   # noqa: E731
    a, b, a2, b2 = P(f1), P(f2), P(l1), P(l2)
    for s, e in ((a, a2), (b, b2)):
        v = np.subtract(e, s)
        n = np.linalg.norm(v)
        if n > 1:
            e2 = np.add(e, v / n * 6)
            d.line([tuple(np.add(s, v / n * 3)), tuple(e2)], fill=(150, 150, 150), width=1)
    d.line([a2, b2], fill=col, width=2)
    u = np.subtract(b2, a2)
    u = u / np.linalg.norm(u)
    arrow(d, a2, -u, col)
    arrow(d, b2, u, col)
    tw = d.textlength(text, font=f)
    mx, my = (a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2
    x = mx - tw / 2 + side[0] * (tw / 2 + pad)
    y = my - f.size / 2 - 3 + side[1] * (f.size / 2 + pad)
    d.rectangle([x - 4, y, x + tw + 4, y + f.size + 6], fill=(255, 255, 255))
    d.text((x, y), text, font=f, fill=col)


def note(d, ren, H, p, text, xy, f, col=(30, 30, 30)):
    x, y = CP.project(ren, np.asarray(p, float), H)
    tx, ty = xy
    tw = d.textlength(text, font=f)
    cx = tx if x < tx else tx + tw + 12
    d.line([(x, y), (cx, ty + f.size / 2 + 4)], fill=(90, 90, 90), width=2)
    d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(40, 40, 40))
    d.rectangle([tx, ty, tx + tw + 12, ty + f.size + 10], fill=(255, 255, 255), outline=(160, 160, 160))
    d.text((tx + 6, ty + 3), text, font=f, fill=col)


def wrap(lines, f, width):
    """Wrap caption lines to a pixel width."""
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    out = []
    for ln in lines:
        cur = ""
        for w in ln.split():
            if cur and d.textlength(cur + " " + w, font=f) > width:
                out.append(cur)
                cur = "    " + w
            else:
                cur = (cur + " " + w).strip() if not cur.startswith("    ") else cur + " " + w
        out.append(cur)
    return out


def band(im, h, draw):
    """Put a white band of height h on top of a panel and let draw(d) fill it."""
    from PIL import Image, ImageDraw
    out = Image.new("RGB", (im.width, im.height + h), "white")
    out.paste(im, (0, h))
    draw(ImageDraw.Draw(out))
    return out


def dashed(d, a, c, col=(200, 30, 30)):
    for t in np.arange(0, 1, 0.04):
        d.line([(a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t),
                (a[0] + (c[0] - a[0]) * (t + 0.02), a[1] + (c[1] - a[1]) * (t + 0.02))], fill=col, width=2)


def figure(res):
    from PIL import Image, ImageDraw
    b = D.mp_bodies()
    gl = CP._shape("plate", CP.plate_with_holes)
    gone = [b["gear+X"], b["web+X"], b["gear-X"], b["web-X"]]
    I = np.eye(4)
    f, fb, fs = CP.font(22), CP.font(22, True), CP.font(20)
    holes = res["floor_holes"]
    rings = [D.Part(f"ring{i}", ring(h["x"], h["y"]), I, RING[hole_use(h["x"], h["y"])][1], "x") for i, h in enumerate(holes)]
    new_rings = [r for r, h in zip(rings, holes) if hole_use(h["x"], h["y"]) == "new"]
    W = res["gearless_plate"]
    x0, x1 = W["x"]
    y0, y1 = W["y"]
    gy0 = res["current_plate_with_gears"]["y"][0]
    zt = res["current_plate_with_gears"]["z"][1]
    zb = res["current_plate_with_gears"]["z"][0]
    zw = W["z"][1]
    hs = res["hinge_stack_plus_x"]
    panels = []

    # (a), (b): the same iso camera and scale
    S = (1000, 780)
    foc = (0.0, 52.0, -8.0)
    cur = [D.Part("plate", b["plate"], MOWN, GREY, "x")] + [D.Part(f"g{i}", s, MOWN, GONE, "x") for i, s in enumerate(gone)]
    fn = HERE / "renders" / "_pa.png"
    ren, _ = D.render(cur, fn, az=-62, el=30, size=S, parallel=True, dist=92, focal=foc, fixed=True)
    im = Image.open(fn).convert("RGB")
    d = ImageDraw.Draw(im)
    note(d, ren, S[1], (54.1, 0, 12), "28T gear (x2)", (640, 120), fb, (170, 40, 35))
    note(d, ren, S[1], (54.1, 16, -14), "web: the gear's arm down to the floor (x2)", (420, 200), fb, (170, 40, 35))
    note(d, ren, S[1], (-22.35, -4, 6), "knuckle (x2)", (40, 150), fb)
    panels.append(im)
    fn.unlink()

    fn = HERE / "renders" / "_pb.png"
    ren, _ = D.render([D.Part("plate", gl, MOWN, GREY, "x")] + new_rings, fn, az=-62, el=30, size=S, parallel=True,
                      dist=92, focal=foc, fixed=True)
    im = Image.open(fn).convert("RGB")
    d = ImageDraw.Draw(im)
    note(d, ren, S[1], (11.0, 95.0, -29.25), "2 new holes, dia 3.4 (clevis block)", (520, 110), fb, (190, 90, 20))
    note(d, ren, S[1], (48.0, 27.0, -29.25), "floor wings: carried the webs, now carry nothing", (330, 690), fb)
    note(d, ren, S[1], (-22.35, -4, 6), "same knuckles", (40, 150), fb)
    panels.append(im)
    fn.unlink()

    # (c) plan of the gearless plate, today's gears and webs see-through, holes coloured by use
    S2 = (1000, 1000)
    gh = [D.Part(f"g{i}", s, MOWN, GONE, "x") for i, s in enumerate(gone)]
    for p in gh:
        p.opacity = 0.35
    fn = HERE / "renders" / "_pc.png"
    ren, _ = D.render([D.Part("plate", gl, MOWN, GREY, "x")] + rings + gh, fn, view="top", size=S2, parallel=True,
                      dist=104, focal=(42.0, 52.0, 0.0), fixed=True)
    im = Image.open(fn).convert("RGB")
    d = ImageDraw.Draw(im)
    z = 0.0
    dim(d, ren, S2[1], (x0, 30, z), (x1, 30, z), (x0, gy0 - 9, z), (x1, gy0 - 9, z),
        f"{x1 - x0:.1f} (today and gearless)", fb, side=(0, 1))
    fw = res["floor_widths_x"]["110 mm behind the hinge"]
    dim(d, ren, S2[1], (fw[0], y1, z), (fw[1], y1, z), (fw[0], y1 + 8, z), (fw[1], y1 + 8, z), f"{fw[1] - fw[0]:.1f}", fb)
    xl, xl2 = x1 + 10, x1 + 54
    dim(d, ren, S2[1], (28.6, y0, z), (fw[1], y1, z), (xl, y0, z), (xl, y1, z), f"{y1 - y0:.1f} gearless", fb, side=(1, 0))
    dim(d, ren, S2[1], (x1, gy0, z), (fw[1], y1, z), (xl2, gy0, z), (xl2, y1, z), f"{y1 - gy0:.1f} today", fb, side=(1, 0))
    dashed(d, CP.project(ren, np.array([x0 - 4, 0, z]), S2[1]), CP.project(ren, np.array([x1 + 4, 0, z]), S2[1]))
    p = CP.project(ren, np.array([0.0, 0.0, z]), S2[1])
    d.text((p[0] - d.textlength("hinge axis", font=fs) / 2, p[1] - 30), "hinge axis", font=fs, fill=(200, 30, 30))
    fn.unlink()

    def legend(dd):
        yy = 14
        for k in ("rear", "tap", "free", "new"):
            name, col = RING[k]
            dd.ellipse([22, yy + 2, 44, yy + 24], outline=tuple(int(255 * c_) for c_ in col), width=6)
            dd.text((56, yy), name, font=f, fill=(30, 30, 30))
            yy += 34
        dd.rectangle([22, yy + 4, 44, yy + 26], fill=(235, 175, 170))
        dd.text((56, yy + 2), "today's gears and webs (see-through)", font=f, fill=(170, 40, 35))
    BAND = 200
    panels.append(band(im, BAND, legend))

    # (d) front view (from the outlet side): the hinge stack, today's towers see-through
    fn = HERE / "renders" / "_pd.png"
    tw = [D.Part("t+", C.TOWER_STD, I, TOWER_COL, "x"), D.Part("t-", C.TOWER_STD.mirror("YZ"), I, TOWER_COL, "x")]
    for p in tw:
        p.opacity = 0.45
    ren, _ = D.render(cur + tw, fn, view="front", size=S2, parallel=True, dist=78, focal=(0.0, 0.0, 2.0), fixed=True)
    im = Image.open(fn).convert("RGB")
    d = ImageDraw.Draw(im)
    yv = -40.0
    dim(d, ren, S2[1], (x0, yv, zb), (x1, yv, zb), (x0, yv, zb - 12), (x1, yv, zb - 12), f"{x1 - x0:.1f}", fb, side=(0, 1))
    for (u0, u1), lab in ((hs["knuckle"], "knuckle"), (hs["tower_today"], "tower"), (hs["gear"], "gear")):
        dim(d, ren, S2[1], (u0, yv, zt), (u1, yv, zt), (u0, yv, zt + 9), (u1, yv, zt + 9), f"{u1 - u0:.1f}", fs)
        p = CP.project(ren, np.array([(u0 + u1) / 2, yv, zt + 19]), S2[1])
        d.text((p[0] - d.textlength(lab, font=fs) / 2, p[1] - 30), lab, font=fs, fill=(30, 30, 30))
    xv = x0 - 9
    dim(d, ren, S2[1], (x0, yv, zb), (-41.8, yv, 0.0), (xv, yv, zb), (xv, yv, 0.0), f"{-zb:.2f}", fb, side=(-1, 0))
    dim(d, ren, S2[1], (-41.8, yv, 0.0), (-48.0, yv, zt), (xv, yv, 0.0), (xv, yv, zt), f"{zt:.2f}", fb, side=(-1, 0))
    dashed(d, CP.project(ren, np.array([x0 - 6, 0, 0]), S2[1]), CP.project(ren, np.array([x1 + 4, 0, 0]), S2[1]))
    note(d, ren, S2[1], (-30.0, 86.0, zw), f"stepper wall top: {zw:.2f} above the hinge", (40, 60), f)
    note(d, ren, S2[1], (35.0, -9.0, -20.0), "today's tower (see-through)", (600, 900), f, (60, 75, 110))
    fn.unlink()

    def stack_note(dd):
        lines = wrap([f"Today the hinge axis runs through the knuckle (bore {hs['knuckle_bore']:.1f}), the tower"
                      f" ({hs['tower_bore_today']:.1f}) and the gear ({hs['gear_bore']:.1f}), so each tower sits between"
                      f" two parts of the plate: 0.3 mm from the knuckle, 0.6 mm from the gear.",
                      f"Gearless, the knuckle alone holds the plate on each side. The tri-star's towers are"
                      f" {hs['tower_tristar'][1] - hs['tower_tristar'][0]:.1f} mm wide (|x| {hs['tower_tristar'][0]}"
                      f" to {hs['tower_tristar'][1]}), as nothing sits outside them."], f, 950)
        for i, ln in enumerate(lines):
            dd.text((22, 14 + 32 * i), ln, font=f, fill=(40, 40, 40))
    panels.append(band(im, BAND, stack_note))

    # assemble 2 x 2
    labels = ["Today: the plate with its 28T gears and webs (red)", "Tri-star: the same plate, gears and webs off",
              "Plan of the gearless plate (mm); floor holes by what uses them", "From the front (outlet side): today's hinge (mm)"]
    gap, lab_h = 20, 48
    Wd = panels[0].width + panels[1].width + gap
    r1 = max(panels[0].height, panels[1].height)
    r2 = max(panels[2].height, panels[3].height)
    sheet = Image.new("RGB", (Wd, r1 + r2 + 2 * lab_h + gap), "white")
    dd = ImageDraw.Draw(sheet)
    pos = [(0, lab_h), (panels[0].width + gap, lab_h), (0, 2 * lab_h + r1 + gap), (panels[0].width + gap, 2 * lab_h + r1 + gap)]
    for im_, (x, y), lab in zip(panels, pos, labels):
        sheet.paste(im_, (x, y))
        dd.text((x + 16, y - lab_h + 10), lab, font=CP.font(26, True), fill=(30, 30, 30))
    dd.line([(panels[0].width + gap / 2, 10), (panels[0].width + gap / 2, sheet.height - 10)], fill=(220, 220, 220), width=2)
    dd.line([(10, lab_h + r1 + gap / 2), (sheet.width - 10, lab_h + r1 + gap / 2)], fill=(220, 220, 220), width=2)
    cw = res["current_plate_with_gears"]["size_WxLxH"]
    gw = W["size_WxLxH"]
    lines = wrap([f"Overall, W x L x H (mm): today {cw[0]:.1f} x {cw[1]:.1f} x {cw[2]:.1f} with the gears;"
                  f" gearless {gw[0]:.1f} x {gw[1]:.1f} x {gw[2]:.2f}.",
                  "The width doesn't change: the floor's front wings, which carried the webs, are as wide as the gears"
                  f" (|x| up to {x1:.1f}).",
                  f"Length and height drop only because the gear teeth stuck out: {-gy0:.1f} mm in front of the hinge"
                  f" (the knuckles reach {-y0:.1f}) and {zt:.1f} mm above it (the stepper wall reaches {zw:.1f}).",
                  "Unchanged: the 6 mm floor, knuckles, tower notches, stepper wall and the six floor holes. #203's tap"
                  " bracket screws into three of those; the clevis block adds two."], CP.font(24), sheet.width - 60)
    out = C.caption(sheet, "The tri-star's mounting plate is today's plate body, unchanged, minus the gears and their webs",
                    lines)
    out.save(HERE / "renders" / "plate_compare.png")
    print("  -> renders/plate_compare.png", flush=True)


def main():
    res = measure()
    print(json.dumps({k: res[k] for k in ("current_plate_with_gears", "gearless_plate", "volume_mm3", "floor_widths_x",
                                          "hinge_stack_plus_x")}, indent=1), flush=True)
    (HERE / "plate.json").write_text(json.dumps(res, indent=1) + "\n")
    figure(res)


if __name__ == "__main__":
    main()

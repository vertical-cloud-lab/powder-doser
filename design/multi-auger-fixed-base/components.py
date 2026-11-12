"""Parts breakdown of the three-auger tri-star (B2 with #203's tap bracket), issue #204, 12 Nov.

Ethan asked for the tri-star broken into its parts with a render of each, how the
actuator connects to the mounting plate, and which parts are new and which come
from the current doser unchanged.  Renders only: nothing here touches Onshape.

    xvfb-run -a python components.py      # about 2 min; writes parts.json and renders/components/

The module is the one concepts.py and clearance.py use (PR #170's STEP files,
Ethan's tap bracket, hinges 32 mm from the beaker axis).  New here:

* the actuator is drawn from Actuonix's P16 drawing (Rev B) instead of a box:
  70 x 36 x 20 mm housing, 12 mm tube, 6 mm rod-end tab and 8 mm rear lug,
  both with 4.25 mm holes (M4 or #8), 197 mm hole to hole when closed;
* the rod end hangs on a printed clevis block screwed under the mounting
  plate's floor (two M3 screws through two new holes), pinned with an M4 screw;
* the rear lug sits in one of the two U-brackets that ship with every P16,
  screwed to a hanger under the shelf.

The rod-end pin stays 95 mm behind and 45 mm below the hinge, so the stroke
table in the README still holds.  Shelf, towers, block, hanger and legs are
placeholders to look over, not drawn parts.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import doserlib as D
import concepts as C

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders" / "components"
SPEC = D.UnitSpec("none", tapper="bracket")
RES = json.loads((HERE / "results.json").read_text())
SP = RES["working_spacing"]["B2T"]                  # 32 mm, hinge to beaker axis
STAND = json.loads((HERE / "clearance.json").read_text())["levels"]["S_min"]   # 217 mm
A, CC = C.ACT_A, C.ACT_C                            # rod-end pin: 95 mm behind, 45 mm below the hinge
FLOOR_U = 8.0 - D.L.HINGE_Z                         # underside of the plate's floor (-35.25)
FLOOR_TOP = FLOOR_U + 6.0                           # top of the floor (-29.25)
HOLE = 4.25                                         # P16 rod-end and rear-lug holes (M4 or #8)
P16R = dict(closed=197.0, stroke=150.0, preload=5.0, lug_t=8.0, tab_t=6.0, boss=9.0, tube=12.0, shaft=8.0,
            housing=(20.0, 36.0, 70.0), axis_from_edge=10.5, housing_from_hole=5.0)
BASE_PIN_Z = -CC - P16R["closed"] - P16R["preload"]     # -247: base pin straight under the rod pin
UB = dict(gap=11.5, t=1.5, w=7.5, h=9.1)            # P16 mounting bracket (ships with it): inside, sheet, width, hole height
BLOCK = dict(pad=(30.0, 24.0, 4.0), gap=6.5, cheek=4.0, lug_r=7.0, screw_x=11.0)
SLOT = dict(x=17.0, y0=33.0, y1=120.0)              # shelf slot per module (was |x| < 12, y 35..110)
HANG = dict(y0=128.0, y1=134.0, w=20.0, foot=4.0)   # hanger strap behind the P16, foot under it
WIN_R = 70.0 / 2 + 4.0                              # window for a 250 mL beaker, as in the B2 figures

STATUS = {
    "reuse": ("Reused as is", "a current doser part (PR #170), no change", (0.50, 0.70, 0.90)),
    "modify": ("Modified", "the current mounting plate: gears off, 2 holes added", (0.97, 0.77, 0.20)),
    "t203": ("New, already drawn", "#203's tap bracket, used as drawn", (0.85, 0.20, 0.55)),
    "new": ("New, to draw", "placeholder here", (0.95, 0.47, 0.18)),
    "buy": ("Bought", "Actuonix P16 and the bracket it ships with", (0.30, 0.32, 0.36)),
    "hw": ("Hardware", "screws, nuts, pins", (0.60, 0.60, 0.62)),
}


# --------------------------------------------------------------------------- #
# new geometry (placeholders)
# --------------------------------------------------------------------------- #
def clevis_block():
    """Rod-end clevis, printed, screwed under the plate's floor (unit frame at tilt 0;
    moves with the plate): a 30 x 24 x 4 pad and two 4 mm lugs 6.5 mm apart, rounded
    R7 round the pin so the rod end's 9 mm hub (8.5 mm from the pin) can swing past."""
    px, py, pt = BLOCK["pad"]
    blk = D.box(-px / 2, px / 2, A - py / 2, A + py / 2, FLOOR_U - pt, FLOOR_U)
    g, t, r = BLOCK["gap"] / 2, BLOCK["cheek"], BLOCK["lug_r"]
    for x0 in (g, -g - t):
        lug = D.box(x0, x0 + t, A - r, A + r, -CC, FLOOR_U - pt + 0.5).fuse(D.cyl(r, t, x0, A, -CC, d=(1, 0, 0)))
        blk = blk.fuse(lug)
    blk = blk.cut(D.cyl(HOLE / 2, 40, -20, A, -CC, d=(1, 0, 0)))
    for sx in (1, -1):
        blk = blk.cut(D.cyl(1.7, 20, sx * BLOCK["screw_x"], A, FLOOR_U - 10))
        blk = blk.cut(D.cyl(3.2, 2.6, sx * BLOCK["screw_x"], A, FLOOR_U - pt - 0.01))   # M3 nut pocket from below
    return blk.clean()


def block_screws():
    """2 x M3 x 10 socket head, heads on the floor's top, nuts in the pad's pockets."""
    out = None
    for sx in (1, -1):
        x = sx * BLOCK["screw_x"]
        s = D.cyl(2.75, 3.0, x, A, FLOOR_TOP).fuse(D.cyl(1.5, 10.0, x, A, FLOOR_TOP - 10.0))
        n = D.cyl(3.1, 2.4, x, A, FLOOR_U - BLOCK["pad"][2])
        out = s.fuse(n) if out is None else out.fuse(s).fuse(n)
    return out


def rod_pin():
    """M4 x 20 socket head through lug, rod-end tab, lug; nyloc on the far side."""
    g, t = BLOCK["gap"] / 2, BLOCK["cheek"]
    head = D.cyl(3.5, 4.0, g + t, A, -CC, d=(1, 0, 0))
    shank = D.cyl(2.0, 20.0, g + t - 20.0, A, -CC, d=(1, 0, 0))
    nut = D.cyl(3.9, 5.0, -g - t - 5.0, A, -CC, d=(1, 0, 0))
    return head.fuse(shank).fuse(nut)


def p16_shapes(L_):
    """Actuonix P16 from its drawing (Rev B), in the actuator frame: base pin at the
    origin, rod pin at (0, 0, L_), pin axes along x, the housing's long side to +y
    (outward, away from the beaker).  Returns (housing, rod)."""
    w, h, ln = P16R["housing"]
    e, z0 = P16R["axis_from_edge"], P16R["housing_from_hole"]
    lug = D.cyl(4.75, P16R["lug_t"], -P16R["lug_t"] / 2, 0, 0, d=(1, 0, 0)).fuse(
        D.box(-P16R["lug_t"] / 2, P16R["lug_t"] / 2, -4.75, 4.75, 0, z0 + 1))
    lug = lug.cut(D.cyl(HOLE / 2, 20, -10, 0, 0, d=(1, 0, 0)))
    tube_end = P16R["closed"] - 15.5
    if "p16body" not in _S:
        housing = D.box(-w / 2, w / 2, -e, h - e, z0, z0 + ln)
        tube = D.box(-P16R["tube"] / 2, P16R["tube"] / 2, -P16R["tube"] / 2, P16R["tube"] / 2, z0 + ln - 1, tube_end)
        _S["p16body"] = housing.fuse(lug).fuse(tube)
    body = _S["p16body"]
    shaft = D.cyl(P16R["shaft"] / 2, L_ - 14.5 - (tube_end - 2), 0, 0, tube_end - 2)
    hub = D.cyl(P16R["boss"] / 2, 6.0, 0, 0, L_ - 14.5)
    tab = D.box(-P16R["tab_t"] / 2, P16R["tab_t"] / 2, -P16R["boss"] / 2, P16R["boss"] / 2, L_ - 8.5, L_).fuse(
        D.cyl(P16R["boss"] / 2, P16R["tab_t"], -P16R["tab_t"] / 2, 0, L_, d=(1, 0, 0)))
    tab = tab.cut(D.cyl(HOLE / 2, 20, -10, 0, L_, d=(1, 0, 0)))
    return body, shaft.fuse(hub).fuse(tab)


def u_bracket():
    """The P16's own mounting bracket: a U of 1.5 mm sheet, 11.5 mm inside, 7.5 mm wide,
    holes 9.1 mm above its base; pin at the origin along x, base underneath."""
    g, t, w, h = UB["gap"] / 2, UB["t"], UB["w"], UB["h"]
    base = D.box(-g - t, g + t, -w / 2, w / 2, -h, -h + t).cut(D.cyl(2.1, 5, 0, 0, -h - 1))
    out = base
    for x0 in (g, -g - t):
        ch = D.box(x0, x0 + t, -w / 2, w / 2, -h, 0).fuse(D.cyl(w / 2, t, x0, 0, 0, d=(1, 0, 0)))
        out = out.fuse(ch)
    return out.cut(D.cyl(HOLE / 2, 30, -15, 0, 0, d=(1, 0, 0))).clean()


def base_pin():
    """#8-32 x 3/4 in (ships with the P16) through bracket, rear lug, bracket."""
    g, t = UB["gap"] / 2, UB["t"]
    return D.cyl(3.4, 3.0, g + t, 0, 0, d=(1, 0, 0)).fuse(D.cyl(2.0, 19.0, g + t - 19.0, 0, 0, d=(1, 0, 0))).fuse(
        D.cyl(3.6, 4.0, -g - t - 4.0, 0, 0, d=(1, 0, 0)))


def plate_with_holes():
    """PR #170's mounting plate without its gears (the 'plate' body), plus the two
    3.4 mm holes the clevis block's M3 screws need, 11 mm either side of the centreline."""
    Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]          # plate's own frame -> unit frame
    inv = np.linalg.inv(Mown)
    pl = D.mp_bodies()["plate"]
    for sx in (1, -1):
        h = D.cyl(1.7, 12.0, sx * BLOCK["screw_x"], A, FLOOR_U - 3.0)
        pl = pl.cut(h.moved(C._loc(inv)))
    return pl


def hanger():
    """Strap from the shelf's underside down behind the P16, and a foot under its
    rear lug that carries the U-bracket (unit frame, fixed)."""
    zf = BASE_PIN_Z - UB["h"]
    strap = D.box(-HANG["w"] / 2, HANG["w"] / 2, HANG["y0"], HANG["y1"], zf - HANG["foot"], D.BASE_BOT_U)
    foot = D.box(-HANG["w"] / 2, HANG["w"] / 2, A - 8.0, HANG["y1"], zf - HANG["foot"], zf)
    flange = D.box(-HANG["w"] / 2, HANG["w"] / 2, HANG["y0"] - 12.0, HANG["y1"] + 12.0, D.BASE_BOT_U - 4.0, D.BASE_BOT_U)
    return strap.fuse(foot).fuse(flange).cut(D.cyl(2.1, 20, 0, A, zf - 10))


def leg(height):
    return D.box(-10.0, 10.0, 165.0, 185.0, D.BASE_BOT_U - height, D.BASE_BOT_U)


def shelf_full(Ms):
    """One shelf for the three modules: the earlier lobes, a window for a 250 mL
    beaker, and a longer, wider slot per module for the clevis block and the rod."""
    s = C.shelf(Ms, WIN_R, slot=False)
    for M in Ms:
        s = s.cut(D.box(-SLOT["x"], SLOT["x"], SLOT["y0"], SLOT["y1"], D.BASE_BOT_U - 5, D.BASE_TOP_U + 5).moved(C._loc(M)))
    return s.clean()


def shelf_lobe():
    """One module's lobe of the shelf, for the exploded view (unit frame)."""
    s = D.box(-100.0, 100.0, -25.0, 190.0, D.BASE_BOT_U, D.BASE_TOP_U)
    s = s.cut(D.box(-SLOT["x"], SLOT["x"], SLOT["y0"], SLOT["y1"], D.BASE_BOT_U - 5, D.BASE_TOP_U + 5))
    return s.cut(D.cyl(WIN_R, 20, 0, -SP, D.BASE_BOT_U - 5)).clean()


# --------------------------------------------------------------------------- #
# one module, every part tagged with its status
# --------------------------------------------------------------------------- #
KIND = {   # part name (after the tag) -> (catalogue key, status)
    "Auger": ("auger", "reuse"), "Auger cap": ("cap", "reuse"), "Bracket (rear)": ("rear", "reuse"),
    "Stepper pinion": ("pinion", "reuse"), "Stepper (NEMA 11)": ("nema", "reuse"),
    "Solenoid coil": ("solenoid", "reuse"), "Solenoid yoke": ("solenoid", "reuse"),
    "Solenoid plunger": ("solenoid", "reuse"), "Tap bracket (#203)": ("tap", "t203"),
    "Mounting plate": ("plate", "modify"), "tower +X": ("tower", "new"), "tower -X": ("tower", "new"),
    "clevis block": ("block", "new"), "M3 screws": ("hw", "hw"), "M4 pin": ("hw", "hw"),
    "P16 body": ("p16", "buy"), "P16 rod": ("p16", "buy"), "P16 bracket": ("ubracket", "buy"),
    "#8-32 pin": ("hw", "hw"), "hanger": ("hanger", "new"),
}


def actuator_frame(Mst, tilt):
    Pp = (Mst @ D.Rx(tilt) @ np.append([0.0, A, -CC], 1.0))[:3]
    Bp = (Mst @ np.array([0.0, A, BASE_PIN_Z, 1.0]))[:3]
    L_ = float(np.linalg.norm(Pp - Bp))
    wv = (Pp - Bp) / L_
    ax = Mst[:3, 0] - wv * (Mst[:3, 0] @ wv)
    ax /= np.linalg.norm(ax)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = ax, np.cross(wv, ax), wv, Bp
    return M, L_


_P16_CACHE: dict = {}


def module(tilt, Mst=None, tag="A", with_hanger=True):
    """Every part of one module at ``tilt`` (unit -> station by Mst), with ``kind`` and ``status``."""
    Mst = np.eye(4) if Mst is None else Mst
    parts = D.unit_parts(SPEC, tilt, Mst, tag) + C.towers(SPEC, Mst, tag)
    for p in parts:
        if p.name.endswith("Mounting plate"):
            p.shape = _shape("plate", plate_with_holes)
    Mt = Mst @ D.Rx(tilt)
    parts.append(D.Part(f"{tag}:clevis block", _shape("block", clevis_block), Mt, STATUS["new"][2], tag, True))
    parts.append(D.Part(f"{tag}:M3 screws", _shape("m3", block_screws), Mt, STATUS["hw"][2], tag, True))
    parts.append(D.Part(f"{tag}:M4 pin", _shape("pin", rod_pin), Mt, STATUS["hw"][2], tag, True))
    Ma, L_ = actuator_frame(Mst, tilt)
    key = round(L_, 3)
    if key not in _P16_CACHE:
        _P16_CACHE[key] = p16_shapes(L_)
    body, rod = _P16_CACHE[key]
    parts.append(D.Part(f"{tag}:P16 body", body, Ma, STATUS["buy"][2], tag, False))
    parts.append(D.Part(f"{tag}:P16 rod", rod, Ma, (0.80, 0.81, 0.84), tag, True))
    Mb = Mst @ D.Tt(0.0, A, BASE_PIN_Z)
    parts.append(D.Part(f"{tag}:P16 bracket", _shape("ub", u_bracket), Mb, STATUS["buy"][2], tag, False))
    parts.append(D.Part(f"{tag}:#8-32 pin", _shape("bpin", base_pin), Mb @ D.Rx(0.0), STATUS["hw"][2], tag, False))
    if with_hanger:
        parts.append(D.Part(f"{tag}:hanger", _shape("hanger", hanger), Mst, STATUS["new"][2], tag, False))
    for p in parts:
        k = p.name.split(":", 1)[1]
        p.kind, p.status = KIND[k]
    return parts


_S: dict = {}


def _shape(k, fn):
    if k not in _S:
        _S[k] = fn()
    return _S[k]


def station(tilts, legs=True):
    Ms = [D.place(90 + i * 120, SP, 0.0) for i in range(3)]
    parts = []
    for i, M in enumerate(Ms):
        parts += module(tilts[i], M, "ABC"[i])
        if legs:
            p = D.Part(f"{'ABC'[i]}:leg", _shape("leg", lambda: leg(STAND)), M, STATUS["new"][2], "ABC"[i], False)
            p.kind, p.status = "leg", "new"
            parts.append(p)
    sh = D.Part("shelf", _shape("shelf", lambda: shelf_full(Ms)), np.eye(4), STATUS["new"][2], "fixed", False)
    sh.kind, sh.status = "shelf", "new"
    return parts + [sh], Ms


def recolour(parts, by="status"):
    for p in parts:
        if by == "status":
            p.colour = STATUS[p.status][2]
    return parts


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def checks(tilts=np.arange(0.0, 90.01, 2.5)):
    """The new connection over 0..90 deg: clevis block and rod end against the shelf, the
    rod end's hub and shaft against the lugs, the P16 against its hanger, and how close
    the P16s come to the beaker axis under the shelf."""
    out = {}
    sh = D.Part("shelf", shelf_lobe(), np.eye(4), (0, 0, 0), "shelf")
    worst = dict(shelf=(1e9, None, None, None), lugs=(1e9, None, None), hanger=(1e9, None, None, None))
    rmin = 1e9
    for t in tilts:
        ps = module(float(t))
        mv = [p for p in ps if p.kind in ("block", "p16") or p.name.endswith(("M3 screws", "M4 pin"))]
        for p in mv:
            p.unit = "m"
        d, a, b = D.clearance(mv + [sh])
        if d < worst["shelf"][0]:
            worst["shelf"] = (d, a, b, float(t))
        # rod end (hub + shaft only, the tab sits in the 6.5 mm gap by design) against the block
        body, rod = _P16_CACHE[round(actuator_frame(np.eye(4), float(t))[1], 3)]
        Ma, L_ = actuator_frame(np.eye(4), float(t))
        hub = D.cyl(P16R["boss"] / 2, 6.0 + 30.0, 0, 0, L_ - 14.5 - 30.0)      # hub and the shaft below it
        blk = next(p for p in ps if p.name.endswith("clevis block"))
        d2 = D.clearance([D.Part("hub", hub, Ma, (0, 0, 0), "h"), D.Part("blk", blk.shape, blk.M, (0, 0, 0), "b")])[0]
        if d2 < worst["lugs"][0]:
            worst["lugs"] = (d2, "rod-end hub/shaft", "clevis lugs", float(t))
        hg = next(p for p in ps if p.name.endswith("hanger"))
        bd = next(p for p in ps if p.name.endswith("P16 body"))
        d3 = D.clearance([D.Part("h", hg.shape, hg.M, (0, 0, 0), "h"), D.Part("p", bd.shape, bd.M, (0, 0, 0), "p")])[0]
        if d3 < worst["hanger"][0]:
            worst["hanger"] = (d3, "P16 housing", "hanger", float(t))
        # P16s under the shelf, distance to the beaker axis (module at R = SP)
        Mst = D.place(90, SP, 0.0)
        Ma2, _ = actuator_frame(Mst, float(t))
        m = D.mesh_of(body)
        v = (Ma2[:3, :3] @ np.asarray(m.vertices).T).T + Ma2[:3, 3]
        sel = v[:, 2] < D.BASE_BOT_U
        rmin = min(rmin, float(np.hypot(v[sel, 0], v[sel, 1]).min()))
    out["moving_parts_to_shelf"] = dict(mm=round(worst["shelf"][0], 2), between=f"{worst['shelf'][1]} / {worst['shelf'][2]}",
                                        at_tilt=worst["shelf"][3])
    out["rod_end_hub_to_lugs"] = dict(mm=round(worst["lugs"][0], 2), at_tilt=worst["lugs"][3])
    out["p16_housing_to_hanger"] = dict(mm=round(worst["hanger"][0], 2), at_tilt=worst["hanger"][3])
    out["p16_closest_to_beaker_axis_below_shelf"] = round(rmin, 1)
    # static: the block, its screws and the pin against the module's own parts
    ps = module(0.0)
    own = [p for p in ps if p.kind in ("auger", "nema", "pinion", "rear", "tap", "solenoid", "cap")]
    best = (1e9, None, None)
    for q in (p for p in ps if p.kind in ("block", "hw") and "#8-32" not in p.name):
        for o in own:
            d = D.clearance([D.Part("q", q.shape, q.M, (0, 0, 0), "q"), D.Part("o", o.shape, o.M, (0, 0, 0), "o")])[0]
            if d < best[0]:
                best = (d, q.name[2:], o.name[2:])
    out["block_and_screws_to_module_parts"] = dict(mm=round(best[0], 2), between=f"{best[1]} / {best[2]}")
    out["stroke_from_closed"] = {str(t): round(actuator_frame(np.eye(4), float(t))[1] - P16R["closed"], 1)
                                 for t in (0, 30, 45, 60, 90)}
    return out


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #
FONT, FONT_B = C.FONT, C.FONT_B


def font(sz, bold=False):
    from PIL import ImageFont
    return ImageFont.truetype(FONT_B if bold else FONT, sz)


def project(ren, p, H):
    ren.SetWorldPoint(float(p[0]), float(p[1]), float(p[2]), 1.0)
    ren.WorldToDisplay()
    x, y, _ = ren.GetDisplayPoint()
    return x, H - y


def legend(img, keys, x=20, y=20, sz=24):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    f, fb = font(sz), font(sz, True)
    for i, k in enumerate(keys):
        name, what, col = STATUS[k]
        yy = y + i * (sz + 14)
        d.rectangle([x, yy, x + sz, yy + sz], fill=tuple(int(255 * c) for c in col), outline=(40, 40, 40))
        d.text((x + sz + 12, yy - 2), name, font=fb, fill=(25, 25, 25))
        d.text((x + sz + 12 + d.textlength(name, font=fb) + 10, yy - 2), what, font=f, fill=(70, 70, 70))
    return img


def boxed(d, xy, txt, f, fill=(20, 20, 20)):
    x, y = xy
    d.rectangle([x - 4, y - 2, x + d.textlength(txt, font=f) + 4, y + f.size + 6], fill=(255, 255, 255))
    d.text((x, y), txt, font=f, fill=fill)


def bbox_mm(p):
    m = D.mesh_of(p.shape)
    v = (p.M[:3, :3] @ np.asarray(m.vertices).T).T
    ext = v.max(0) - v.min(0)
    return ext


CATALOG = [   # key, name, qty in the station, status, where it comes from / what changes
    ("auger", "Auger (tube, flights, 44T gear)", 3, "reuse", "PR #170 auger.step"),
    ("cap", "Auger cap", 3, "reuse", "PR #170 auger-cap.step"),
    ("rear", "Rear Flexible Bracket", 3, "reuse", "PR #170 brackets.step"),
    ("nema", "NEMA 11 stepper 11HS18-0674S", 3, "reuse", "bought; as today"),
    ("pinion", "20T stepper pinion", 3, "reuse", "PR #170 stepper-pinion.step"),
    ("solenoid", "Adafruit 412 solenoid", 3, "reuse", "bought; now held by #203's bracket"),
    ("plate", "Mounting plate, gearless", 3, "modify", "PR #170 plate: both 28T gears and webs off; 2 x M3 holes"),
    ("tap", "Tap bracket (#203)", 3, "t203", "Ethan's part (9 Nov): front clamp + solenoid"),
    ("block", "Rod-end clevis block", 3, "new", "printed; 2 x M3 to the floor, M4 pin"),
    ("tower", "Hinge tower", 6, "new", "like the baseplate's towers, 8 mm wide; M5 hinge screw"),
    ("shelf", "Shelf (all three modules)", 1, "new", "6 mm; 78 mm window, a slot per module"),
    ("hanger", "Actuator hanger", 3, "new", "strap + foot under the shelf"),
    ("leg", "Stand leg", 3, "new", f"{STAND:.0f} mm, the shortest stand"),
    ("p16", "Actuonix P16-150-22-12-P", 3, "buy", "+ an LAC board each; from its drawing"),
    ("ubracket", "P16 mounting bracket", 3, "buy", "ships with the P16 (2 each; 1 used)"),
]

REMOVED = [   # what the tri-star no longer uses, from PR #170
    ("Baseplate", "fusion-step/baseplate.step", None),
    ("MG996R servo (2 per module)", "purchased/mg996r-servo.step", None),
    ("14T servo pinion (2 per module)", "fusion-step/servo-pinion.step", None),
    ("28T gears + webs (cut off the plate)", None, "gears"),
    ("Front Flexible Bracket", "fusion-step/brackets.step", None),
    ("Tap collar", "fusion-step/tap-collar.step", None),
    ("Tap collar base", "ai-step/tap-collar-base.step", None),
]


def tile(parts, fn, size=(620, 520), az=-58.0, el=24.0, zoom=1.0):
    """One part (list of Parts) alone, parallel iso, filling the frame."""
    pts = []
    for p in parts:
        m = D.mesh_of(p.shape)
        pts.append((p.M[:3, :3] @ np.asarray(m.vertices).T).T + p.M[:3, 3])
    v = np.vstack(pts)
    c = (v.max(0) + v.min(0)) / 2
    a_, e_ = math.radians(az), math.radians(el)
    d = np.array([math.cos(e_) * math.cos(a_), math.cos(e_) * math.sin(a_), math.sin(e_)])
    up = np.array([0, 0, 1.0]) - d * d[2]
    up /= np.linalg.norm(up)
    rt = np.cross(up, d)
    w = (v - c) @ rt
    h = (v - c) @ up
    scale = max((h.max() - h.min()) / 2, (w.max() - w.min()) / 2 * size[1] / size[0]) * 1.12 / zoom
    hc, wc = (h.max() + h.min()) / 2, (w.max() + w.min()) / 2
    foc = c + up * hc + rt * wc
    D.render(parts, fn, az=az, el=el, size=size, parallel=True, dist=scale, focal=tuple(foc), fixed=True)


def tiles_sheet(entries, out, title, cols=4, tw=620, th=520):
    """entries: (png, name, qty line, status key, size line, source)."""
    from PIL import Image, ImageDraw
    cap = 150
    rows = math.ceil(len(entries) / cols)
    W, H = cols * tw, rows * (th + cap) + 70
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    d.text((20, 16), title, font=font(32, True), fill=(20, 20, 20))
    for i, (png, name, qty, st, dims, src) in enumerate(entries):
        x, y = (i % cols) * tw, 70 + (i // cols) * (th + cap)
        im = Image.open(png).convert("RGB")
        sheet.paste(im, (x, y))
        col = tuple(int(255 * c) for c in STATUS[st][2])
        d.rectangle([x + 6, y + 4, x + tw - 6, y + 12], fill=col)
        d.text((x + 16, y + th + 4), f"{name}", font=font(24, True), fill=(20, 20, 20))
        d.text((x + 16, y + th + 36), f"{STATUS[st][0]}  |  {qty}", font=font(21, True), fill=col if st != "buy" else (60, 60, 60))
        d.text((x + 16, y + th + 66), dims, font=font(20), fill=(70, 70, 70))
        d.text((x + 16, y + th + 94), src, font=font(19), fill=(90, 90, 90))
        d.rectangle([x + 4, y + 2, x + tw - 4, y + th + cap - 6], outline=(215, 215, 215), width=2)
    sheet.save(out)


def part_tiles(res):
    OUT.mkdir(parents=True, exist_ok=True)
    ps = module(0.0)
    by = {}
    for p in ps:
        by.setdefault(p.kind, []).append(p)
    st, Ms = station((0, 0, 0))
    by["shelf"] = [p for p in st if p.kind == "shelf"]
    by["leg"] = [next(p for p in st if p.kind == "leg")]
    by["tower"] = [p for p in by["tower"] if p.name.endswith("+X")]
    res["catalog"] = []
    entries = []
    for key, name, qty, sts, src in CATALOG:
        parts = by[key]
        fn = OUT / f"{key}.png"
        if key == "p16":                 # the actuator closed, with its rod end
            parts = [p for p in parts]
        tile(parts, fn, az=-58 if key not in ("shelf",) else -90, el=24 if key != "shelf" else 55)
        ext = np.max([bbox_mm(p) for p in parts], axis=0) if len(parts) == 1 else None
        if ext is None:
            v = np.vstack([(p.M[:3, :3] @ np.asarray(D.mesh_of(p.shape).vertices).T).T + p.M[:3, 3] for p in parts])
            ext = v.max(0) - v.min(0)
        dims = f"{ext[0]:.0f} x {ext[1]:.0f} x {ext[2]:.0f} mm (W x L x H)"
        entries.append((fn, name, f"{qty} in the station", sts, dims, src))
        res["catalog"].append(dict(key=key, name=name, qty=qty, status=STATUS[sts][0], source=src,
                                   size_mm=[round(float(e), 1) for e in ext], render=f"renders/components/{key}.png"))
    # hardware tile: the screws and pins together
    hw = [D.Part("M4 pin", _shape("pin", rod_pin), D.Tt(0, -A, CC), STATUS["hw"][2], "x"),
          D.Part("M3 screws", _shape("m3", block_screws), D.Tt(0, -A + 14, -FLOOR_TOP - 4), STATUS["hw"][2], "x"),
          D.Part("#8-32 pin", _shape("bpin", base_pin), D.Tt(0, 28, 0), STATUS["hw"][2], "x")]
    tile(hw, OUT / "hardware.png", zoom=0.95)
    entries.append((OUT / "hardware.png", "Screws and pins (per module)", "1 set per module", "hw",
                    "M4 x 20 + nyloc: rod-end pin (left)", "2 x M3 x 10 + nuts: block; #8-32: base pin (P16's)"))
    reuse = [e for e in entries if e[3] == "reuse"]
    new = [e for e in entries if e[3] != "reuse"]
    tiles_sheet(reuse, HERE / "renders" / "parts_reused.png",
                "Parts reused from the current doser unchanged (3 of each)", cols=3)
    tiles_sheet(new, HERE / "renders" / "parts_new.png",
                "Parts that are modified, new or bought for the tri-star", cols=4)
    # what is no longer used
    rem = []
    for name, rel, special in REMOVED:
        fn = OUT / f"removed_{len(rem)}.png"
        if special == "gears":
            b = D.mp_bodies()
            shapes = [b["gear+X"], b["web+X"], b["gear-X"], b["web-X"]]
            parts = [D.Part("g", s, D.W2U @ D.L.placements(0.0)["Mounting plate"][1], (0.75, 0.75, 0.77), "x") for s in shapes]
        else:
            parts = [D.Part("r", D.step_shape(rel), np.eye(4), (0.75, 0.75, 0.77), "x")]
        tile(parts, fn, size=(420, 340))
        rem.append((fn, name))
    from PIL import Image, ImageDraw
    W = 420 * len(rem)
    im = Image.new("RGB", (W, 340 + 110), "white")
    d = ImageDraw.Draw(im)
    for i, (fn, name) in enumerate(rem):
        im.paste(Image.open(fn).convert("RGB"), (i * 420, 60))
        words, line, lines = name.split(), "", []
        for w_ in words:
            if d.textlength(line + " " + w_, font=font(20, True)) > 400:
                lines.append(line)
                line = w_
            else:
                line = (line + " " + w_).strip()
        lines.append(line)
        for j, ln in enumerate(lines):
            d.text((i * 420 + 12, 340 + 62 + 24 * j), ln, font=font(20, True), fill=(60, 60, 60))
        fn.unlink()
    d.text((20, 14), "No longer used in the tri-star (from the current doser)", font=font(30, True), fill=(20, 20, 20))
    im.save(HERE / "renders" / "parts_removed.png")
    print("  -> parts_reused.png, parts_new.png, parts_removed.png", flush=True)


EXPLODE = {   # catalogue key -> offset in the unit frame (mm)
    "auger": (0, 0, 95), "cap": (0, 55, 95), "rear": (0, 0, 52), "tap": (0, 0, 52), "solenoid": (48, 0, 52),
    "nema": (-60, 0, 38), "pinion": (-60, -40, 38), "plate": (0, 0, 0), "tower": (0, 0, -32),
    "block": (0, 0, -40), "p16": (0, 0, -120), "ubracket": (0, 0, -150), "hanger": (0, 45, -150),
}


def exploded(res):
    ps = module(0.0)
    tw = [p for p in ps if p.kind == "tower"]
    out, labels = [], {}
    for p in ps:
        off = np.array(EXPLODE.get(p.kind, (0, 0, 0)), float)
        if p.kind == "tower":
            off = off + np.array([30.0 if p.name.endswith("+X") else -30.0, 0, 0])
        if p.name.endswith("M3 screws"):
            off = np.array([0, 0, 22.0])
        if p.name.endswith("M4 pin"):
            off = np.array([45.0, 0, -40.0])
        if p.name.endswith("#8-32 pin"):
            off = np.array([40.0, 0, -150.0])
        q = D.Part(p.name, p.shape, D.Tt(*off) @ p.M, STATUS[p.status][2], "x")
        q.kind, q.status = p.kind, p.status
        out.append(q)
    lobe = D.Part("shelf", shelf_lobe(), D.Tt(0, 0, -62), STATUS["new"][2], "x")
    lobe.kind, lobe.status = "shelf", "new"
    out.append(lobe)
    fn = HERE / "renders" / "_exploded.png"
    size = (1500, 1900)
    ren, _ = D.render(out, fn, az=-35, el=20, size=size, parallel=True, dist=330, focal=(0, 80, -95), fixed=True)
    # numbered balloons at each catalogue item's centre
    from PIL import Image, ImageDraw
    im = Image.open(fn).convert("RGB")
    d = ImageDraw.Draw(im)
    num = {k: i + 1 for i, (k, *_r) in enumerate(CATALOG)}
    num["hw"] = len(CATALOG) + 1
    anchor = {}
    for q in out:
        k = q.kind if q.kind != "hw" else "hw"
        if k in anchor or k not in num:
            continue
        m = D.mesh_of(q.shape)
        v = (q.M[:3, :3] @ np.asarray(m.vertices).T).T + q.M[:3, 3]
        anchor[k] = project(ren, (v.max(0) + v.min(0)) / 2, size[1])
    side = {"auger": "R", "cap": "R", "rear": "R", "tap": "L", "solenoid": "R", "nema": "L", "pinion": "L",
            "plate": "R", "tower": "L", "block": "R", "shelf": "L", "p16": "L", "ubracket": "R", "hanger": "R", "hw": "R"}
    placed = {"L": [], "R": []}
    for k, (x, y) in sorted(anchor.items(), key=lambda kv: kv[1][1]):
        sd = side.get(k, "R")
        tx = 70 if sd == "L" else size[0] - 70
        ty = y
        for yy in placed[sd]:
            if abs(ty - yy) < 58:
                ty = yy + 58
        placed[sd].append(ty)
        d.line([(x, y), (tx, ty)], fill=(90, 90, 90), width=2)
        y = ty
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(40, 40, 40))
        r = 24
        st = next((s for kk, _n, _q, s, _src in CATALOG if kk == k), "hw")
        d.ellipse([tx - r, y - r, tx + r, y + r], fill=tuple(int(255 * c) for c in STATUS[st][2]), outline=(30, 30, 30), width=2)
        t = str(num[k])
        f = font(24, True)
        d.text((tx - d.textlength(t, font=f) / 2, y - 15), t, font=f, fill=(255, 255, 255) if st in ("buy", "t203") else (20, 20, 20))
    legend(im, ["reuse", "modify", "t203", "new", "buy", "hw"], x=24, y=24, sz=24)
    # key under the figure
    rows = [f"{num[k]}  {n}  (x{q})" for k, n, q, _s, _src in CATALOG] + [f"{num['hw']}  Screws and pins", "(13, the legs, are in the overview)"]
    key_h = 36 * math.ceil(len(rows) / 2) + 80
    full = Image.new("RGB", (size[0], size[1] + key_h), "white")
    full.paste(im, (0, 0))
    dd = ImageDraw.Draw(full)
    dd.text((24, size[1] + 10), "One module, exploded (the other two are copies at 120 deg)",
            font=font(28, True), fill=(20, 20, 20))
    half = math.ceil(len(rows) / 2)
    for i, r in enumerate(rows):
        dd.text((24 + (i // half) * 740, size[1] + 56 + 36 * (i % half)), r, font=font(24), fill=(40, 40, 40))
    full.save(HERE / "renders" / "parts_exploded.png")
    fn.unlink()
    print("  -> parts_exploded.png", flush=True)


def overview(res):
    tilts = (30, 60, 0)
    parts, Ms = station(tilts)
    recolour(parts)
    fn = HERE / "renders" / "_ov.png"
    D.render(parts, fn, az=-70, el=22, size=(1500, 1250), dist=1.45)
    top, _ = station((0, 0, 0), legs=False)
    recolour(top)
    fn2 = HERE / "renders" / "_ovtop.png"
    D.render(top, fn2, view="top", size=(1100, 1250), parallel=True, dist=300, focal=(0, 40, 0))
    from PIL import Image
    C.side_by_side([fn, fn2], HERE / "renders" / "parts_overview.png",
                   "The tri-star coloured by where each part comes from",
                   ["Blue: current doser parts used as they are (auger, cap, rear bracket, stepper and pinion, solenoid)."
                    " Yellow: the mounting plate, with its gears cut off.",
                    "Magenta: #203's tap bracket. Orange: new parts, still placeholders (shelf, hinge towers, clevis block,"
                    " hangers, legs). Dark grey: bought (Actuonix P16 and its bracket).",
                    f"Left: tilts 30, 60, 0 deg, on the shortest stand ({STAND:.0f} mm). Right: plan at 0 deg."],
                   labels=("", "plan"))
    im = Image.open(HERE / "renders" / "parts_overview.png")
    band = Image.new("RGB", (im.width, im.height + 120), "white")
    band.paste(im, (0, 120))
    keys = ["reuse", "modify", "t203", "new", "buy"]
    legend(band, keys[:3], x=24, y=16, sz=24)
    legend(band, keys[3:], x=1350, y=16, sz=24)
    band.save(HERE / "renders" / "parts_overview.png")
    print("  -> parts_overview.png", flush=True)


def connection(res):
    """How the actuator connects: rod end to the plate (iso + section at 0 and 90 deg) and the base end."""
    from PIL import Image, ImageDraw
    paths = []
    # 1. iso close-up from below and behind, 0 deg
    ps = module(0.0)
    sh = D.Part("shelf", shelf_lobe(), np.eye(4), (0.78, 0.80, 0.84), "fixed")
    sh.opacity = 0.35
    near = [p for p in ps if p.kind not in ("hanger", "ubracket") and "#8-32" not in p.name] + [sh]
    fn = HERE / "renders" / "_c1.png"
    S1 = (1000, 900)
    ren, _ = D.render(near, fn, az=35, el=-28, size=S1, parallel=True, dist=48, focal=(0, A, -40), fixed=True)
    im = Image.open(fn).convert("RGB")
    d = ImageDraw.Draw(im)
    f = font(22, True)
    notes = [((12, A + 10, FLOOR_U - 4), "clevis block (new, printed)", (600, 90)),
             ((BLOCK["gap"] / 2 + BLOCK["cheek"] + 2, A, -CC), "M4 x 20 pin + nyloc", (620, 780)),
             ((0, A - 2, -CC - 7), "P16 rod end: 6 mm tab, 4.25 mm hole", (40, 840)),
             ((-BLOCK["screw_x"], A, FLOOR_U - 4), "M3 nut in a pocket (x2)", (40, 600)),
             ((-30, A + 25, FLOOR_U), "mounting plate floor (6 mm)", (40, 70)),
             ((-SLOT["x"], A - 30, D.BASE_BOT_U), "shelf (slot 34 x 87 mm)", (40, 140))]
    for p3, txt, (tx, ty) in notes:
        x, y = project(ren, p3, S1[1])
        d.line([(x, y), (tx + 6, ty + 14)], fill=(60, 60, 60), width=2)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(40, 40, 40))
        d.rectangle([tx, ty, tx + d.textlength(txt, font=f) + 12, ty + 30], fill=(255, 255, 255), outline=(150, 150, 150))
        d.text((tx + 6, ty + 2), txt, font=f, fill=(20, 20, 20))
    im.save(fn)
    paths.append(fn)
    # 2-3. half-sections through the centreline at 0 and 90 deg, with the key dimensions
    for t in (0.0, 90.0):
        ps = module(t, with_hanger=False)
        sh = D.Part("shelf", shelf_lobe(), np.eye(4), (0.62, 0.66, 0.72), "fixed")
        fn = HERE / "renders" / f"_c{int(t)}.png"
        S2 = (900, 900)
        ren, _ = D.render(ps + [sh], fn, view="side", size=S2, parallel=True, dist=72 if t == 0 else 78, focal=(0, 50, -25) if t == 0 else (0, 30, 45),
                          clip_x=0.3, fixed=True)
        im = Image.open(fn).convert("RGB")
        d = ImageDraw.Draw(im)
        hp = project(ren, (0, 0, 0), S2[1])
        pin = D.Rx(t) @ np.array([0.0, A, -CC, 1.0])
        pp = project(ren, pin[:3], S2[1])
        red = (200, 30, 30)
        d.ellipse([hp[0] - 6, hp[1] - 6, hp[0] + 6, hp[1] + 6], outline=red, width=3)
        d.ellipse([pp[0] - 6, pp[1] - 6, pp[0] + 6, pp[1] + 6], outline=red, width=3)
        if t == 0:
            d.line([hp, (pp[0], hp[1])], fill=red, width=2)
            d.line([(pp[0], hp[1]), pp], fill=red, width=2)
            boxed(d, ((hp[0] + pp[0]) / 2 - 60, hp[1] - 34), f"{A:.0f} mm behind", f, red)
            boxed(d, (pp[0] + 10, (hp[1] + pp[1]) / 2 - 12), f"{CC:.0f} mm below", f, red)
            boxed(d, (pp[0] - 250, pp[1] + 60), f"pin {FLOOR_U + CC:.2f} mm under the floor", font(20), (40, 40, 40))
            boxed(d, (20, 16), "0 deg: rod end straight down", font(24, True))
        else:
            boxed(d, (20, 16), "90 deg: the rod end has turned 82 deg in the clevis;", font(24, True))
            boxed(d, (20, 50), "the lugs are rounded (R7) so its 9 mm hub swings past", font(22), (40, 40, 40))
        boxed(d, (hp[0] - 40, hp[1] + 14), "hinge", font(20, True), red)
        boxed(d, (pp[0] + 12, pp[1] + 8), "pin", font(20, True), red)
        im.save(fn)
        paths.append(fn)
    # 4. base end: U-bracket on the hanger foot
    ps = module(0.0)
    near = [p for p in ps if p.kind in ("p16", "ubracket", "hanger") or "#8-32" in p.name]
    fn = HERE / "renders" / "_cb.png"
    S4 = (900, 900)
    ren, _ = D.render(near, fn, az=-35, el=22, size=S4, parallel=True, dist=48, focal=(0, A + 12, BASE_PIN_Z + 12), fixed=True)
    im = Image.open(fn).convert("RGB")
    d = ImageDraw.Draw(im)
    notes = [((0, A, BASE_PIN_Z - UB["h"] + 1), "P16 bracket (ships with it)", (40, 760)),
             ((-UB["gap"] / 2 - 3, 0 + A, BASE_PIN_Z), "#8-32 screw (ships with it)", (40, 820)),
             ((0, HANG["y0"] + 3, BASE_PIN_Z + 30), "hanger (new) from the shelf", (430, 70)),
             ((0, A - 12, BASE_PIN_Z + 30), "P16 housing, 8 mm rear lug", (40, 70))]
    for p3, txt, (tx, ty) in notes:
        x, y = project(ren, p3, S4[1])
        d.line([(x, y), (tx + 6, ty + 14)], fill=(60, 60, 60), width=2)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(40, 40, 40))
        d.rectangle([tx, ty, tx + d.textlength(txt, font=f) + 12, ty + 30], fill=(255, 255, 255), outline=(150, 150, 150))
        d.text((tx + 6, ty + 2), txt, font=f, fill=(20, 20, 20))
    im.save(fn)
    paths.append(fn)
    ck = res["checks"]
    C.side_by_side(paths, HERE / "renders" / "actuator_connection.png",
                   "How the actuator connects: rod end to the mounting plate, rear lug to a hanger under the shelf",
                   [f"Rod end: a printed clevis block under the plate's floor, held by 2 x M3 x 10 through two new holes in the floor"
                    f" (nuts in pockets); the P16's 6 mm tab sits between 4 mm lugs 6.5 mm apart on an M4 x 20 pin + nyloc.",
                    f"The pin stays {A:.0f} mm behind and {CC:.0f} mm below the hinge, so the stroke is as before:"
                    f" {ck['stroke_from_closed']['0']} mm out at 0 deg, {ck['stroke_from_closed']['45']} at 45,"
                    f" {ck['stroke_from_closed']['90']} at 90 (150 mm available).",
                    f"Rear lug: one of the two U-brackets that ship with each P16, screwed to the hanger's foot, on the #8-32 screw"
                    f" that ships with it. Closest approaches over 0-90 deg: block/rod to shelf {ck['moving_parts_to_shelf']['mm']} mm,"
                    f" hub to lugs {ck['rod_end_hub_to_lugs']['mm']} mm, actuator to hanger {ck['p16_housing_to_hanger']['mm']} mm."],
                   labels=("rod end, from below", "", "", "base end"))
    print("  -> actuator_connection.png", flush=True)


def main():
    import sys
    OUT.mkdir(parents=True, exist_ok=True)
    res = dict(spacing=SP, stand=STAND, p16=P16R, u_bracket=UB, clevis_block=BLOCK, shelf_slot=SLOT, hanger=HANG,
               rod_pin_unit_frame=[0.0, A, -CC], base_pin_unit_frame=[0.0, A, BASE_PIN_Z])
    res["checks"] = checks()
    print(json.dumps(res["checks"], indent=1), flush=True)
    if "--checks" in sys.argv:
        return
    connection(res)
    part_tiles(res)
    exploded(res)
    overview(res)
    (HERE / "parts.json").write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()

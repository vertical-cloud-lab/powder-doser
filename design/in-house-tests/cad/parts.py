"""Printed parts for the ten in-house test apparatuses (PR #205), in CadQuery.

Every function returns a CadQuery Workplane in the part's *use* frame (z up, mm). PARTS maps a part
name to its builder, the apparatus it belongs to, how many to print, the printer, and the rotation
that puts it on the bed. Numbers come from ../SPEC.md; change them there first.

    python build.py            # every part -> out/step, out/stl, out/parts.json
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cadquery as cq

# --------------------------------------------------------------------------------------------- #
# primitives
# --------------------------------------------------------------------------------------------- #


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(r, h, x=0.0, y=0.0, z=0.0):
    return cq.Workplane("XY").circle(r).extrude(h).translate((x, y, z))


def tube(ro, ri, h, x=0.0, y=0.0, z=0.0):
    return cq.Workplane("XY").circle(ro).circle(ri).extrude(h).translate((x, y, z))


def xcyl(r, h, x=0.0, y=0.0, z=0.0):
    """Cylinder along +x starting at x."""
    return cq.Workplane("YZ").circle(r).extrude(h).translate((x, y, z))


def ycyl(r, h, x=0.0, y=0.0, z=0.0):
    """Cylinder along +y starting at y."""
    return cq.Workplane("XZ").circle(r).extrude(-h).translate((x, y, z))


def hexprism(af, h, x=0.0, y=0.0, z=0.0):
    return cq.Workplane("XY").polygon(6, af / math.cos(math.pi / 6)).extrude(h).translate((x, y, z))


def cone(r0, r1, h, z=0.0):
    return cq.Workplane("XY").add(cq.Solid.makeCone(r0, r1, h)).translate((0, 0, z))


def gear_profile(m, z, pa_deg=20.0, n_flank=7):
    """Involute spur-gear outline (list of xy points), tooth 0 centred on +x."""
    pa = math.radians(pa_deg)
    rp, ra, rf = m * z / 2, m * z / 2 + m, m * z / 2 - 1.25 * m
    rb = rp * math.cos(pa)
    inv = lambda a: math.tan(a) - a  # noqa: E731
    half = math.pi / (2 * z) + inv(pa)
    r_start = max(rb, rf)
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        flank = []
        for i in range(n_flank):
            r = r_start + (ra - r_start) * i / (n_flank - 1)
            a = math.acos(min(1.0, rb / r))
            flank.append((r, half - inv(a)))
        right = [(r, c - phi) for r, phi in flank]
        left = [(r, c + phi) for r, phi in reversed(flank)]
        seg = []
        if rf < rb:
            seg.append((rf, c - half))
        seg += right + left
        if rf < rb:
            seg.append((rf, c + half))
        pts += [(r * math.cos(t), r * math.sin(t)) for r, t in seg]
    return pts


def gear(m, z, width, bore=0.0, z0=0.0):
    g = cq.Workplane("XY").polyline(gear_profile(m, z)).close().extrude(width)
    if bore:
        g = g.cut(cyl(bore / 2, width + 2, z=-1))
    return g.translate((0, 0, z0))


def holes(wp, pts, d, h=200.0, z=-100.0):
    for x, y in pts:
        wp = wp.cut(cyl(d / 2, h, x, y, z))
    return wp


# --------------------------------------------------------------------------------------------- #
# shared bench parts
# --------------------------------------------------------------------------------------------- #
PAN_D = 90.0          # HR-100A pan
SPIGOT_D = 10.0       # riser / adapter push fit
SOCKET_D = 10.25
TRIPOD_R = 62.0       # leg radius, clear of the pan by 17 mm
LEG_AF = 8.0


def pan_adapter():
    p = cyl(43, 3)
    for k in range(3):  # three locating lips over the pan rim
        a = math.radians(90 + 120 * k)
        tab = box(-4, 4, 41.0, 47.2, 0, 3).union(box(-4, 4, 45.4, 47.2, -2.5, 3))
        p = p.union(tab.rotate((0, 0, 0), (0, 0, 1), math.degrees(a) - 90))
    p = p.union(cyl(9, 11)).cut(cyl(SOCKET_D / 2, 9, z=3))
    for k in range(6):
        a = 2 * math.pi * k / 6
        p = p.cut(cyl(8.5, 10, 26 * math.cos(a), 26 * math.sin(a), -1))
    return p


def riser(h):
    def f():
        r = tube(7, SOCKET_D / 2, h)
        r = r.union(cyl(SPIGOT_D / 2 - 0.05, 8, z=-8)).union(cyl(7, 3))  # spigot + solid plug
        return r
    return f


def tripod_spider():
    s = tube(20, 12, 6)
    for k in range(3):
        a = 90 + 120 * k
        arm = box(14, TRIPOD_R, -5, 5, 0, 6).rotate((0, 0, 0), (0, 0, 1), a)
        boss = cyl(7.5, 6, TRIPOD_R, 0, 0).rotate((0, 0, 0), (0, 0, 1), a)
        s = s.union(arm).union(boss)
    for k in range(3):
        a = 90 + 120 * k
        sock = hexprism(LEG_AF + 0.3, 4.5, TRIPOD_R, 0, -0.01).rotate((0, 0, 0), (0, 0, 1), a)
        s = s.cut(sock)
        m3 = cyl(1.6, 10, 16, 0, -2).rotate((0, 0, 0), (0, 0, 1), a + 60)
        s = s.cut(m3)
    return s


def tripod_leg(h):
    def f():
        leg = hexprism(LEG_AF, h - 2, z=0).union(cyl(7, 2, z=0))  # foot pad at the bottom
        return leg.union(hexprism(LEG_AF, 0.01, z=h - 2))
    return f


def camera_tower():
    t = box(-35, 35, -25, 25, 0, 6)
    t = holes(t, [(-28, -18), (28, -18), (-28, 18), (28, 18)], 4.4)
    post = box(-10, 10, -6, 6, 6, 170)
    slot = box(-1.7, 1.7, -7, 7, 20, 160)
    t = t.union(post).cut(slot)
    gus = box(-2, 2, 6, 24, 6, 30)
    return t.union(gus).union(gus.translate((0, -30, 0)))


def camera_carriage():
    c = box(-14, 14, -10, 10, 0, 24).cut(box(-10.3, 10.3, -6.3, 6.3, -1, 25))  # sleeve on the post
    c = c.cut(box(-14.5, 14.5, -11, -6, -1, 25).translate((0, 0, 0)).intersect(box(-1.7, 1.7, -11, -6, -1, 25)))
    c = c.cut(ycyl(1.7, 6, 0, -16, 12))
    plate = box(-16, 16, -13, -10, -6, 30)  # camera plate in front
    plate = holes_y(plate, [(-10.5, 6.0), (10.5, 6.0), (-10.5, 18.5), (10.5, 18.5)], 2.2)
    plate = plate.cut(ycyl(4.5, 10, 0, -20, 14.0))
    return c.union(plate)


def holes_y(wp, pts, d):
    for x, z in pts:
        wp = wp.cut(ycyl(d / 2, 60, x, -30, z))
    return wp


def camera_rod_clamp():
    """Camera Module 3 (or backlight) on a lab retort-stand rod, Ø10-13 mm, M4 thumb screw."""
    c = box(-12, 12, -12, 12, 0, 20).cut(cyl(6.6, 22, z=-1))
    c = c.cut(xcyl(1.75, 14, 0, 0, 10)).cut(box(5, 13, -3.6, 3.6, 7, 13))  # M4 nut trap
    arm = box(-4, 4, -60, -12, 4, 16)
    plate = box(-16, 16, -63, -60, -6, 30)
    plate = holes_y(plate, [(-10.5, 6.0), (10.5, 6.0), (-10.5, 18.5), (10.5, 18.5)], 2.2)
    plate = plate.cut(ycyl(4.5, 10, 0, -70, 14.0))
    return c.union(arm).union(plate)


def backlight_foot():
    f = box(-30, 30, -20, 20, 0, 5)
    f = f.union(box(-30, 30, -8, 8, 5, 25)).cut(box(-31, 31, -3, 3, 7, 26))
    return f


# --------------------------------------------------------------------------------------------- #
# 1. heap angle of repose
# --------------------------------------------------------------------------------------------- #

def pedestal(d):
    def f():
        land, th = 0.4, 4.0
        r = d / 2
        top = cyl(r, land, z=th - land)
        cham = cone(max(r - (th - land), 1.0), r, th - land)
        p = top.union(cham).union(cyl(6.5, th - land)).union(cyl(SPIGOT_D / 2 - 0.05, 8, z=-8))
        pitch = 1.5  # 0.5 mm wide, 0.3 mm deep cross-hatch: a key for the glued powder layer
        n = int(d // pitch) + 2
        for i in range(-n // 2, n // 2 + 1):
            p = p.cut(box(i * pitch - 0.25, i * pitch + 0.25, -r - 1, r + 1, th - 0.3, th + 1))
            p = p.cut(box(-r - 1, r + 1, i * pitch - 0.25, i * pitch + 0.25, th - 0.3, th + 1))
        return p
    return f


def overflow_tray():
    t = cyl(60, 1.6).union(tube(60, 58.4, 8))
    t = t.union(tube(11, 9, 10)).cut(cyl(9, 20, z=-1))
    t = t.union(tube(11.9, 9, 3, z=-3))  # spigot into the spider hub (ID 24)
    return t


# --------------------------------------------------------------------------------------------- #
# 2. bulk and tapped density
# --------------------------------------------------------------------------------------------- #
CYL_OD = 15.0     # 10 mL Class A graduated cylinder (measure the real one)
CYL_HEX_AF = 38.0  # its foot, across flats
CYL_H = 155.0


def cyl_fill_holder():
    h = cyl(26, 9).cut(hexprism(CYL_HEX_AF + 0.8, 7, z=3))
    return h.union(cyl(SPIGOT_D / 2 - 0.05, 8, z=-8))


def funnel_collar():
    outer = cone(6.2, 20, 18, z=8)
    inner = cone(5.0, 18.8, 18.02, z=8)
    f = outer.cut(inner)
    skirt = tube(CYL_OD / 2 + 1.6, CYL_OD / 2 + 0.3, 9)
    f = f.union(skirt).union(tube(CYL_OD / 2 + 1.6, 5.0, 1.2, z=7.5))
    return f


# cam-drop tapper geometry (base frame: base bottom z = 0)
TAP_BASE_T = 6.0
TAP_ROD_X = 25.0
TAP_SHAFT_Z = 26.0
TAP_CAM_R0, TAP_CAM_RISE = 8.0, 3.5
TAP_CAM_Y = (24.0, 28.0)
ANVIL_PROUD = 1.0


def tapper_base():
    b = box(-45, 45, -50, 90, 0, TAP_BASE_T)
    for x in (-TAP_ROD_X, TAP_ROD_X):
        b = b.union(cyl(7, 15, x, 0, TAP_BASE_T)).cut(cyl(3.0, 16, x, 0, TAP_BASE_T - 1))
    b = b.cut(cyl(12.6, 2.0, 0, 0, TAP_BASE_T - 2.0 + 0.001))  # anvil pocket (anvil 25 x 3 sits 1 proud)
    mp = box(-20, 20, 32, 38, TAP_BASE_T, TAP_SHAFT_Z + 20)
    mp = mp.cut(ycyl(11.25, 10, 0, 30, TAP_SHAFT_Z))
    for dx in (-11.5, 11.5):
        for dz in (-11.5, 11.5):
            mp = mp.cut(ycyl(1.35, 10, dx, 30, TAP_SHAFT_Z + dz))
    rib = box(-3, 3, 38, 60, TAP_BASE_T, 26)
    b = b.union(mp).union(rib.translate((-17, 0, 0))).union(rib.translate((17, 0, 0)))
    b = holes(b, [(-38, -43), (38, -43), (-38, 83), (38, 83)], 4.4)
    return b


def tapper_cam():
    pts = []
    for lobe in range(2):
        for i in range(0, 41):
            th = math.pi * lobe + math.pi * i / 40 * 0.97
            r = TAP_CAM_R0 + TAP_CAM_RISE * (i / 40)
            pts.append((r * math.cos(th), r * math.sin(th)))
    cam = cq.Workplane("XY").polyline(pts).close().extrude(4)
    hub = cyl(6, 8)
    c = cam.union(hub)
    d = cyl(2.55, 12, z=-1).cut(box(-3, 3, 2.0, 3, -2, 13))  # 5 mm D-shaft, flat 0.5
    c = c.cut(d).cut(xcyl(1.4, 8, 0, 0, 6))
    return c


def tapper_carriage():
    """Lower block (foot pocket, striker, follower lug) + upper collar, joined by a back spine.
    Use frame: resting on the anvil, striker face at z = TAP_BASE_T + ANVIL_PROUD."""
    z0 = TAP_BASE_T + ANVIL_PROUD
    lower = box(-32, 32, -22, 22, z0, z0 + 12)
    lower = lower.cut(hexprism(CYL_HEX_AF + 0.8, 7, 0, 0, z0 + 5.01))
    upper = box(-32, 32, -8, 8, z0 + 70, z0 + 80).union(cyl(12, 10, 0, 0, z0 + 70))
    upper = upper.cut(cyl(CYL_OD / 2 + 0.4, 12, 0, 0, z0 + 69)).cut(box(-0.8, 0.8, -14, 0, z0 + 69, z0 + 81))
    upper = upper.union(box(-6, -2, -16, -9, z0 + 70, z0 + 80)).union(box(2, 6, -16, -9, z0 + 70, z0 + 80))
    upper = upper.cut(xcyl(1.6, 16, -8, -12.5, z0 + 75))
    spine = box(-10, 10, 10, 22, z0 + 12, z0 + 80).union(box(-10, 10, 8, 22, z0 + 70, z0 + 80))
    c = lower.union(upper).union(spine)
    for x in (-TAP_ROD_X, TAP_ROD_X):
        c = c.cut(cyl(3.25, 100, x, 0, z0 - 1))
    # follower lug over the cam: underside 0.5 mm above the base circle at rest
    lug_z = TAP_SHAFT_Z + TAP_CAM_R0 + 0.5
    lug = box(-5, 5, 18, 31, lug_z, lug_z + 5)   # hangs off the spine, over the cam (y 24-28)
    return c.union(lug)


# --------------------------------------------------------------------------------------------- #
# 3. tilting plate
# --------------------------------------------------------------------------------------------- #
HINGE_Z = 60.0
PIN_D = 5.0
GEAR_M = 1.5
PIN_Z15, GEAR_Z30 = 15, 30
CENTRE_D = GEAR_M * (PIN_Z15 + GEAR_Z30) / 2   # 33.75
PLATE_T = 6.0


def tilt_base():
    b = box(-50, 50, -45, 130, 0, 6)
    for x0 in (-37, 31):  # hinge towers
        t = box(x0, x0 + 6, -10, 10, 6, HINGE_Z + 8).union(xcyl(10, 6, x0, 0, HINGE_Z))
        t = t.cut(xcyl(PIN_D / 2 + 0.1, 8, x0 - 1, 0, HINGE_Z))
        b = b.union(t)
    # servo bracket: vertical plate in the y-z plane; flange face at x = 29
    sz = HINGE_Z - CENTRE_D
    br = box(24, 29, -42, 18, 6, sz + 22)
    br = br.cut(box(23, 30, -30.7 - 0.3, 10 + 0.3, sz - 10.25 - 0.3, sz + 10.25 + 0.3))
    for dy in (-24.75, 24.75):
        for dz in (-5, 5):
            br = br.cut(xcyl(1.4, 8, 22, -10.35 + dy, sz + dz))
    b = b.union(br).union(box(10, 24, -42, -36, 6, 20)).union(box(10, 24, 12, 18, 6, 20))
    b = holes(b, [(-43, -38), (43, -38), (-43, 123), (43, 123)], 4.4)
    return b


def tilt_plate():
    z0 = HINGE_Z - PLATE_T / 2
    p = box(-30, 30, 0, 120, z0, z0 + PLATE_T)
    p = p.cut(box(-25.1, 25.1, 14, 114.2, z0 + PLATE_T - 0.8, z0 + PLATE_T + 1))  # coupon pocket
    p = p.union(box(-30, 30, 4, 8, z0 + PLATE_T, z0 + PLATE_T + 4))             # stop rail
    for xs in (1, -1):
        lug = box(min(38 * xs, 43.5 * xs), max(38 * xs, 43.5 * xs), -8, 8, HINGE_Z - 8, HINGE_Z + 8)
        arm = box(min(30 * xs, 38.5 * xs), max(30 * xs, 38.5 * xs), -8, 14, z0, z0 + PLATE_T)
        p = p.union(lug).union(arm)
    p = p.cut(xcyl(PIN_D / 2 + 0.05, 100, -50, 0, HINGE_Z))
    for dy in (-5, 5):
        p = p.cut(xcyl(1.6, 8, 37, dy, HINGE_Z - 5)) if False else p
    p = p.cut(xcyl(1.6, 8, 37, 0, HINGE_Z + 5.0)).cut(xcyl(1.6, 8, 37, 0, HINGE_Z - 5.0))
    for x in (-10.15, 10.15):  # LSM6DSOX breakout bosses under the plate
        for y in (60 - 6.35, 60 + 6.35):
            p = p.union(cyl(2.6, 5, x, y, z0 - 5)).cut(cyl(1.1, 6, x, y, z0 - 5.5))
    p = p.cut(box(-24, 24, 20, 30, z0 - 1, z0 + 2))  # finger notch under the coupon
    return p


def tilt_gear_30t():
    g = gear(GEAR_M, GEAR_Z30, 4.0, bore=PIN_D + 0.2)
    g = holes(g, [(0, 5.0), (0, -5.0)], 3.3)
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        g = g.cut(cyl(3.5, 10, 13 * math.cos(a), 13 * math.sin(a), -1))
    return g


def tilt_pinion_15t():
    g = gear(GEAR_M, PIN_Z15, 4.0, bore=7.0)
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        g = g.cut(cyl(1.05, 10, 7 * math.cos(a), 7 * math.sin(a), -1))
    return g


def wall_ring():
    return tube(13.7, 12.5, 6.0)


def ring_lid():
    lid = cyl(12.3, 1.2).union(tube(12.3, 11.1, 5.0))
    return lid.union(cyl(4, 6))  # centre post for M8 washers


def strike_frame(depth):
    def f():
        fr = box(-34, 34, -24, 24, 0, depth).cut(box(-30, 30, -20, 20, -1, depth + 1))
        return fr.union(box(34, 46, -6, 6, 0, depth))
    return f


# --------------------------------------------------------------------------------------------- #
# 4. microscope (PSD)
# --------------------------------------------------------------------------------------------- #

def micro_base():
    b = box(-75, 75, -55, 55, 0, 6).cut(box(-25, 25, -20, 20, -1, 7))
    b = holes(b, [(-40, -35), (40, -35)], 4.4)
    b = b.union(box(-17, 17, 30, 54, 6, 16)).cut(box(-10.25, 10.25, 35.75, 48.25, 5, 17))
    return b


def micro_column():
    c = box(-10, 10, -6, 6, 0, 170).cut(box(-1.7, 1.7, -7, 0, 30, 165))
    return c


def micro_carriage():
    c = box(-15, 15, -10, 10, 0, 30).cut(box(-10.3, 10.3, -6.3, 6.3, -1, 31))
    c = c.cut(ycyl(1.7, 8, 0, -14, 15))
    arm = box(-24, 24, -70, -10, 22, 28)
    arm = arm.cut(cyl(19, 10, 0, -45, 20))
    arm = holes(arm, [(-15, -60), (15, -60), (-15, -30), (15, -30)], 2.7)
    return c.union(arm)


def sieve_cup():
    return tube(17, 15, 25).union(tube(17, 13.5, 1.5))


def sieve_ring():
    return tube(14.9, 13.0, 4.0)


# --------------------------------------------------------------------------------------------- #
# 5. orifice cup
# --------------------------------------------------------------------------------------------- #
ORIFICES = (1.0, 1.5, 2.0, 2.54, 3.0, 4.0, 5.08, 6.0)


def orifice_cup():
    c = tube(15, 12.5, 40, z=3).union(cyl(20, 3))
    c = c.cut(cyl(12.5, 10, z=-1))
    c = holes(c, [(14.5 * math.cos(a), 14.5 * math.sin(a)) for a in (0.5, 2.594, 4.689)], 3.3)
    return c


def orifice_disc(dmm):
    def f():
        land = 0.4
        d = cyl(16, 2.0)
        d = d.cut(cyl(dmm / 2, 3, z=-0.5))
        d = d.cut(cone(dmm / 2 + (2.0 - land), dmm / 2, 2.0 - land, z=0).rotate((0, 0, 0), (1, 0, 0), 180)
                  .translate((0, 0, 2.0 - land)))
        d = holes(d, [(14.5 * math.cos(a), 14.5 * math.sin(a)) for a in (0.5, 2.594, 4.689)], 3.3)
        return d
    return f


def gate_guide():
    g = cyl(20, 6).union(box(14, 46, -8, 8, 0, 6))
    g = g.cut(box(-21, 47, -6.0, 6.0, 4.2, 5.8 + 0.01))      # gate channel, 1.6 tall, open both ends
    g = g.cut(cyl(5.0, 8, z=-1))
    g = holes(g, [(14.5 * math.cos(a), 14.5 * math.sin(a)) for a in (0.5, 2.594, 4.689)], 3.3)
    g = g.union(box(30, 46, -20, -8, 0, 6))                   # micro-servo pad
    g = holes(g, [(33, -14), (43, -14)], 1.8)
    return g


def gate_slide():
    s = box(-20, 40, -5.8, 5.8, 0, 1.5)
    s = s.cut(cyl(5.0, 4, -10, 0, -1)).cut(cyl(1.1, 4, 36, 0, -1))
    return s


def cup_holder():
    h = tube(19.8, 12.2, 5).union(tube(11.9, 9.5, 3, z=-3))  # spigot into the spider hub
    arm = box(10, 52, -8, 8, 0, 5)
    ring = tube(26, 20.4, 5, 52 + 22, 0, 0).union(box(48, 54, -8, 8, 0, 5))
    h = h.union(arm).union(ring)
    sol = box(60, 92, 24, 40, 0, 26).cut(box(63, 89, 27, 37, 3, 27))  # JF-0530B cradle
    return h.union(sol).union(box(70, 80, 18, 26, 0, 5))


def catch_cup():
    return tube(22, 20.8, 30, z=1.2).union(cyl(22, 1.2)).union(cyl(SPIGOT_D / 2 - 0.05, 8, z=-8))


# --------------------------------------------------------------------------------------------- #
# 6. humidity chambers
# --------------------------------------------------------------------------------------------- #

def hc_slurry_tray():
    return box(-75, 75, -45, 45, 0, 15).cut(box(-73.4, 73.4, -43.4, 43.4, 1.6, 16))


def hc_shelf():
    s = box(-80, 80, -50, 50, 0, 2.4)
    for i in range(-7, 8):
        for j in range(-4, 5):
            s = s.cut(cyl(3, 4, i * 10, j * 10, -1))
    for x in (-74, 74):
        for y in (-44, 44):
            s = s.union(cyl(3.5, 30, x, y, -30 + 0.01))
    return s


def hc_sample_dish():
    d = cyl(30, 1.2).union(tube(30, 28.8, 5))
    return d.union(box(28, 38, -5, 5, 0, 1.6)).union(box(-38, -28, -5, 5, 0, 1.6))


def hc_sensor_clip():
    c = box(-15, 15, -12, 12, 0, 2).cut(box(-10, 10, -4, 4, -1, 3))
    c = holes(c, [(-10.15, -6.35 + 6.35), (10.15, 0)], 2.2)
    return c.union(box(-15, 15, 12, 14, -8, 2)).union(box(-15, 15, 14, 20, -8, -5.6))


def hc_fan_mount():
    m = box(-15, 15, -15, 15, 0, 3).cut(cyl(12, 5, z=-1))
    m = holes(m, [(-10, -10), (10, -10), (-10, 10), (10, 10)], 2.9)
    return m.union(box(-15, 15, 15, 18, -10, 3)).union(box(-15, 15, 18, 24, -10, -7.6))


# --------------------------------------------------------------------------------------------- #
# 7. rotating drum (replaces the auger in the doser's brackets)
# --------------------------------------------------------------------------------------------- #
DRUM_EXT = 20.0   # flange sits 20 mm in front of where the auger's outlet face would be
DRUM_ID, DRUM_DEPTH = 40.0, 15.0
GEAR_Z0 = 78.33   # 44T band, from the auger outlet face


def drum_shaft():
    s = tube(12.5, 10.5, 225 + DRUM_EXT, z=0)
    s = s.union(cyl(20, 4, z=0))
    s = s.cut(cyl(10.5, 10, z=-1).translate((0, 0, 0)))
    g = gear(1.0, 44, 10.0, bore=21.0, z0=DRUM_EXT + GEAR_Z0)
    s = s.union(g).union(tube(16, 12, 10, z=DRUM_EXT + GEAR_Z0))
    s = s.cut(cyl(4.0, 6, z=-1))
    for a in (0, 120, 240):
        x, y = 15 * math.cos(math.radians(a)), 15 * math.sin(math.radians(a))
        s = s.cut(cyl(2.1, 6, x, y, -1))  # heat-set inserts M3
    return s


def drum_body():
    d = cyl(28, 3)                                     # rear wall
    d = d.union(tube(22.5, DRUM_ID / 2, DRUM_DEPTH, z=3))
    for k in range(24):
        a = 360 * k / 24
        rib = box(DRUM_ID / 2 - 0.8, DRUM_ID / 2 + 0.2, -0.5, 0.5, 3, 3 + DRUM_DEPTH)
        d = d.union(rib.rotate((0, 0, 0), (0, 0, 1), a))
    d = d.union(tube(28, 22.0, 3, z=3 + DRUM_DEPTH))   # front flange for the window
    for a in (0, 120, 240):
        x, y = 15 * math.cos(math.radians(a)), 15 * math.sin(math.radians(a))
        d = d.cut(cyl(1.7, 5, x, y, -1))
        x2, y2 = 25 * math.cos(math.radians(a + 60)), 25 * math.sin(math.radians(a + 60))
        d = d.cut(cyl(2.1, 6, x2, y2, 3 + DRUM_DEPTH - 2.5))
    return d


def drum_bezel():
    b = tube(28, 22, 3).cut(cyl(25.2, 2.1, z=-0.01))
    for a in (60, 180, 300):
        b = b.cut(cyl(1.7, 5, 25 * math.cos(math.radians(a)), 25 * math.sin(math.radians(a)), -1))
    return b


def drum_backdisc():
    return cyl(19.0, 1.2)


# --------------------------------------------------------------------------------------------- #
# 8. unconfined strength
# --------------------------------------------------------------------------------------------- #
MOULD_ID, MOULD_H, MOULD_OD = 20.0, 40.0, 30.0


def ucs_base():
    b = box(-60, 60, -60, 82, 0, 8)
    b = b.union(box(-48, -28, -8, 8, 8, 28))                  # load-cell fixed block
    b = b.cut(cyl(1.35, 25, -43, 0, 7)).cut(cyl(1.35, 25, -33, 0, 7))  # M3 into the block (load cell)
    col = box(-30, 30, 60, 80, 8, 170)                          # column; the stage bolts to its front
    for x in (-20, 20):
        col = col.cut(box(x - 2.75, x + 2.75, 59, 81, 30, 160))
    b = b.union(col).union(box(-30, -24, 30, 60, 8, 60)).union(box(24, 30, 30, 60, 8, 60))
    return holes(b, [(-52, -52), (52, -52), (-52, 74), (52, 74)], 4.4)


def ucs_sample_base():
    b = cyl(22, 4).union(tube(MOULD_OD / 2 + 2.5, MOULD_OD / 2 + 0.3, 1.5, z=4))
    return holes(b, [(-5, 0), (5, 0)], 2.7)


def split_mould_half(side):
    def f():
        h = tube(MOULD_OD / 2, MOULD_ID / 2, MOULD_H).intersect(box(-20, 20, 0, 20, 0, MOULD_H))
        for zp in (8, MOULD_H - 8):
            for x in (-12.5, 12.5):
                h = h.cut(ycyl(1.55, 6, x, -1, zp))
        if side == "B":
            h = h.rotate((0, 0, 0), (0, 0, 1), 180)
        return h
    return f


def mould_ring():
    return tube(MOULD_OD / 2 + 3.5, MOULD_OD / 2 + 0.25, 6)


def ucs_piston():
    return cyl(9.8, 8).union(cyl(4, 40, z=8)).union(cyl(15, 3, z=20))


def ucs_platen():
    """Platen disc on a 36 mm arm; the vertical plate bolts to the stage slider's face."""
    p = cyl(15, 6).union(box(0, 38, -6, 6, 0, 8))
    plate = box(36, 42, -20, 20, -12, 20)
    for y in (-12, 12):
        for z in (-4, 12):
            plate = plate.cut(xcyl(1.7, 10, 34, y, z))
    return p.union(plate)


# --------------------------------------------------------------------------------------------- #
# 9. blade spreading
# --------------------------------------------------------------------------------------------- #

def coupon_bed():
    b = box(-70, 70, -25, 25, 0, 10).cut(box(-50.2, 50.2, -15.2, 15.2, 9.0, 11))
    b = b.cut(box(-55, -50, -12, 12, 8.0, 11))  # finger notch to lift the coupon
    return holes(b, [(-62, -18), (-62, 18), (62, -18), (62, 18)], 4.4)


def spread_bracket():
    br = box(-20, 20, 0, 6, 0, 40).union(box(-20, 20, 0, 40, 0, 6))
    br = holes_y(br, [(-12, 28), (12, 28)], 4.4)
    return holes(br, [(-12, 25), (12, 25)], 4.4)


def blade_carriage():
    c = box(-25, 25, -20, 20, 0, 10)
    c = holes(c, [(-15, -15), (15, -15), (-15, 15), (15, 15)], 4.4)
    arm = box(-8, 8, 20, 85, 0, 10)
    clamp = box(-30, 30, 80, 96, -22, 10).cut(box(-26, 26, 87.2, 88.8, -23, 11))  # 1.6 slot for the blade
    for x in (-18, 18):
        clamp = clamp.cut(ycyl(1.6, 20, x, 78, -10))
        clamp = clamp.cut(cyl(1.35, 40, x, 92, -30))
    return c.union(arm).union(clamp)


# --------------------------------------------------------------------------------------------- #
# 10. Faraday cup
# --------------------------------------------------------------------------------------------- #
FC_CAN_ID = 70.0


def fc_lid():
    lid = cyl(FC_CAN_ID / 2 + 3, 3).union(tube(FC_CAN_ID / 2 - 0.2, FC_CAN_ID / 2 - 2.0, 6, z=-6))
    fun = cone(10, 6, 12, z=-12).cut(cone(8.8, 4.8, 12.02, z=-12.01))
    lid = lid.cut(cyl(8.8, 6, z=-1)).union(fun)
    return lid.cut(cyl(4.8, 30, z=-20))


def fc_insulator_base():
    b = cyl(FC_CAN_ID / 2 - 0.5, 3)
    b = holes(b, [(12 * math.cos(math.radians(a)), 12 * math.sin(math.radians(a))) for a in (90, 210, 330)], 3.4)
    return b.cut(cyl(3, 5, z=-1))


def fc_cradle():
    c = tube(11.9, 9, 3, z=-3).union(cyl(42, 4)).cut(cyl(9, 10, z=-1))
    c = c.union(tube(42, FC_CAN_ID / 2 + 0.4, 14, z=4))
    for a in (0, 120, 240):
        c = c.cut(box(-6, 6, 30, 45, 8, 19).rotate((0, 0, 0), (0, 0, 1), a))
    return c


def fc_pcb_box():
    b = box(-30, 30, -25, 25, 0, 24).cut(box(-28, 28, -23, 23, 2, 25))
    b = b.cut(xcyl(4.8, 5, 27, 0, 12)).cut(xcyl(3.0, 5, -31, 0, 12))
    for x, y in ((-22, -17), (22, -17), (-22, 17), (22, 17)):
        b = b.union(cyl(3, 6, x, y, 2)).cut(cyl(1.35, 7, x, y, 2))
    return b


def fc_pcb_lid():
    l = box(-30, 30, -25, 25, 0, 2).union(box(-27.8, 27.8, -22.8, 22.8, -2, 0).cut(box(-26.6, 26.6, -21.6, 21.6, -3, 1)))
    return l


# --------------------------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------------------------- #

@dataclass
class Part:
    name: str
    fn: callable
    test: str
    qty: int = 1
    printer: str = "A1M"
    bed_rot: tuple = (0.0, 0.0, 0.0)   # rotation (deg about x, y, z) that puts the print face down
    note: str = ""
    infill: int = 25
    tags: list = field(default_factory=list)


PARTS: dict[str, Part] = {}


def _p(name, fn, test, **kw):
    PARTS[name] = Part(name, fn, test, **kw)


_p("pan_adapter", pan_adapter, "shared", note="sits on the HR-100A pan", infill=15)
for _h in (40, 80, 120, 160):
    _p(f"riser_{_h}", riser(_h), "shared", note=f"{_h} mm riser")
_p("tripod_spider", tripod_spider, "shared")
for _h in (40, 80, 120, 160):
    _p(f"tripod_leg_{_h}", tripod_leg(_h), "shared", qty=3, bed_rot=(90, 0, 0), note="print lying on a flat")
_p("camera_tower", camera_tower, "shared")
_p("camera_carriage", camera_carriage, "shared", bed_rot=(0, 0, 0))
_p("camera_rod_clamp", camera_rod_clamp, "shared", qty=2, note="one for the camera, one for the backlight")
_p("backlight_foot", backlight_foot, "shared", qty=2)
for _d in (12, 20, 30):
    _p(f"pedestal_d{_d}", pedestal(_d), "1", bed_rot=(180, 0, 0), note="top face down for a flat, sharp rim", infill=100)
_p("overflow_tray", overflow_tray, "1")
_p("cyl_fill_holder", cyl_fill_holder, "2", bed_rot=(180, 0, 0))
_p("funnel_collar", funnel_collar, "2", bed_rot=(180, 0, 0))
_p("tapper_base", tapper_base, "2")
_p("tapper_cam", tapper_cam, "2", infill=100)
_p("tapper_carriage", tapper_carriage, "2", bed_rot=(-90, 0, 0), note="on its back (spine down)", infill=40)
_p("tilt_base", tilt_base, "3")
_p("tilt_plate", tilt_plate, "3", bed_rot=(180, 0, 0), note="coupon face down for flatness", infill=40)
_p("tilt_gear_30t", tilt_gear_30t, "3", infill=100)
_p("tilt_pinion_15t", tilt_pinion_15t, "3", infill=100)
_p("wall_ring", wall_ring, "3", qty=3, infill=100, note="auger settings: 0.20 mm layers, 3 walls")
_p("ring_lid", ring_lid, "3", qty=2)
for _t in (1, 2, 3, 5):
    _p(f"strike_frame_{_t}mm", strike_frame(_t), "3")
_p("micro_base", micro_base, "4")
_p("micro_column", micro_column, "4", bed_rot=(90, 0, 0))
_p("micro_carriage", micro_carriage, "4", bed_rot=(180, 0, 0))
_p("sieve_cup", sieve_cup, "4")
_p("sieve_ring", sieve_ring, "4")
_p("orifice_cup", orifice_cup, "5", infill=40)
for _d in ORIFICES:
    _p(f"orifice_disc_{_d:.2f}".replace(".", "p"), orifice_disc(_d), "5", infill=100,
       note=f"drill/ream to {_d} mm after printing")
_p("gate_guide", gate_guide, "5")
_p("gate_slide", gate_slide, "5", infill=100)
_p("cup_holder", cup_holder, "5")
_p("catch_cup", catch_cup, "5", bed_rot=(180, 0, 0))
_p("hc_slurry_tray", hc_slurry_tray, "6", qty=5, infill=15)
_p("hc_shelf", hc_shelf, "6", qty=5, bed_rot=(180, 0, 0), infill=15)
_p("hc_sample_dish", hc_sample_dish, "6", qty=5)
_p("hc_sensor_clip", hc_sensor_clip, "6", qty=5)
_p("hc_fan_mount", hc_fan_mount, "6", qty=5)
_p("drum_shaft", drum_shaft, "7", printer="H2D", infill=40, note="245 mm tall: H2D, flange down")
_p("drum_body", drum_body, "7", infill=40)
_p("drum_bezel", drum_bezel, "7")
_p("drum_backdisc", drum_backdisc, "7", qty=2, note="one black, one white")
_p("ucs_base", ucs_base, "8", infill=30)
_p("ucs_sample_base", ucs_sample_base, "8")
_p("split_mould_A", split_mould_half("A"), "8", infill=100, note="standing on its end: smooth bore")
_p("split_mould_B", split_mould_half("B"), "8", infill=100, note="standing on its end: smooth bore")
_p("mould_ring", mould_ring, "8", qty=2)
_p("ucs_piston", ucs_piston, "8")
_p("ucs_platen", ucs_platen, "8")
_p("coupon_bed", coupon_bed, "9", infill=40)
_p("spread_bracket", spread_bracket, "9", qty=2)
_p("blade_carriage", blade_carriage, "9", bed_rot=(180, 0, 0), infill=40)
_p("fc_lid", fc_lid, "10", bed_rot=(180, 0, 0))
_p("fc_insulator_base", fc_insulator_base, "10")
_p("fc_cradle", fc_cradle, "10")
_p("fc_pcb_box", fc_pcb_box, "10")
_p("fc_pcb_lid", fc_pcb_lid, "10", bed_rot=(180, 0, 0))

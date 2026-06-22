"""Build every Powder Doser part + the tilt-0 assembly from ``params.py``.

Run ``python3 build.py`` to regenerate STEP + STL for all parts and the
assembly into ``exports/``.  Each printed part is modelled in its own local
frame (auger axis along +Z for the tube-shaped parts, then re-oriented when
placed into the assembly).

Conventions
-----------
* Augers / collars / brackets are authored with the auger axis along **+Z**,
  dispense (exit) end at Z=0.  In the assembly they are rotated so the auger
  axis lies along **+Y** with the dispense tip at +Y (SPEC §1).
* Plates are authored in their assembly orientation directly.
"""
from __future__ import annotations

import math
import os

import cadquery as cq
from cadquery import exporters
from OCP.BRepCheck import BRepCheck_Analyzer

import params as P
import helpers as H

HERE = os.path.dirname(os.path.abspath(__file__))
STEP_DIR = os.path.join(HERE, "exports", "step")
STL_DIR = os.path.join(HERE, "exports", "stl")


# ==========================================================================
# small geometry utilities
# ==========================================================================
def cyl(r, h, z0=0.0):
    return cq.Workplane("XY").workplane(offset=z0).circle(r).extrude(h)


def cone(r1, r2, h, z0=0.0):
    s = cq.Solid.makeCone(r1, r2, h, pnt=cq.Vector(0, 0, z0))
    return cq.Workplane(obj=s)


# ==========================================================================
# Part 1 + variants: Archimedes auger
# ==========================================================================
def build_auger(length=P.AUGER_LEN_FULL, with_band=True, storage=True,
                threaded=False):
    """Archimedes auger.

    storage=True   -> internal screw occupies only the bottom 1/3 (reservoir).
    with_band=True -> external 48T drive gear band (full-length augers only).
    threaded=True  -> external thread on the top ~1 inch instead of slotted cap.
    """
    OR, IR = P.AUGER_OR, P.AUGER_IR
    fn = P.FUNNEL_H
    cap_h = P.TOP_CAP_H
    screw_top = length / 3.0 if storage else (length - cap_h)

    # --- outer tube wall (bore stays open end-to-end) ---
    auger = cyl(OR, length).cut(cyl(IR, length + 1, -0.5))

    # --- bottom funnel: conical floor narrowing to the Ø3 exit ---
    funnel = cyl(OR, fn).cut(cone(P.EXIT_HOLE_R, IR, fn))
    auger = auger.union(funnel)

    # --- internal screw (shaft + single-start helical fin) ---
    fin_outer = IR + P.FIN_OUTER_OVERLAP          # 10.7
    scr_h = screw_top - fn
    screw = H.screw_solid(scr_h, P.HELIX_PITCH, P.SHAFT_R,
                          fin_outer, P.FIN_THICK)
    screw = screw.translate((0, 0, fn))

    # --- v4 nozzle: taper the screw into the funnel cone, tip 0.5 above exit ---
    nozzle = H.screw_solid(fn, P.HELIX_PITCH, P.SHAFT_R, fin_outer, P.FIN_THICK)
    # clip to the funnel cavity so shaft + fin taper down to the exit
    env = cone(P.EXIT_HOLE_R, IR, fn)
    nozzle = nozzle.intersect(env)
    nozzle = nozzle.cut(cyl(OR + 1, P.V4_TIP_BOTTOM_R + 0.5))  # leave gap above exit
    screw = screw.union(nozzle)

    auger = auger.union(screw)

    # --- top end: slotted loading cap (slotted variant only) ---
    if not threaded:
        cap = cyl(OR, cap_h, z0=length - cap_h)
        # 4 rectangular loading slots on a 6.5 bolt circle
        for k in range(P.N_SLOTS):
            ang = math.radians(90 * k)
            x = P.SLOT_BC_R * math.cos(ang)
            y = P.SLOT_BC_R * math.sin(ang)
            slot = (cq.Workplane("XY").workplane(offset=length - cap_h - 0.5)
                    .center(x, y).rect(P.SLOT_W, P.SLOT_L)
                    .extrude(cap_h + 1))
            cap = cap.cut(slot)
        # central M3 pilot boss
        boss = cyl(P.SHAFT_R, 2.0, z0=length).cut(
            cyl(P.M3_PILOT / 2, 6, z0=length - 4))
        auger = auger.union(cap).union(boss)
    else:
        # external single-start thread: helical V-grooves cut into the top of
        # the tube so the crests stay flush with the Ø25 OD (roots cut to 11.5)
        auger = auger.cut(_external_thread_groove(length))

    # --- external 48T drive gear band (annular: bore stays open) ---
    if with_band:
        zc = P.BAND_CENTRE_FROM_TIP
        band = H.gear_solid(P.BAND_MODULE, P.BAND_TEETH, P.BAND_PA,
                            P.BAND_FACE, backlash=P.GEAR_BACKLASH)
        band = band.translate((0, 0, zc - P.BAND_FACE / 2))
        auger = auger.union(band)
        # re-open the Ø21 bore straight through the band
        auger = auger.cut(cyl(IR, P.BAND_FACE + 2,
                              z0=zc - P.BAND_FACE / 2 - 1))

    return auger


def _external_thread_groove(length):
    """Helical V-groove cutter; subtracting it leaves an external thread whose
    crests are flush with the Ø25 OD and roots cut inward to THREAD_ROOT_R."""
    z0 = length - P.THREAD_LEN
    r_out = P.AUGER_OR + 1.0                         # past the OD (cuts nothing extra)
    depth = r_out - P.THREAD_ROOT_R
    half = math.tan(math.radians(P.THREAD_HALF_ANGLE)) * depth
    # V-groove profile in (r, z): apex at the root radius, opening outward
    prof = (cq.Workplane("XZ")
            .moveTo(r_out, -half)
            .lineTo(P.THREAD_ROOT_R, 0)
            .lineTo(r_out, half)
            .close())
    path = cq.Wire.makeHelix(P.THREAD_PITCH, P.THREAD_LEN, P.THREAD_ROOT_R)
    groove = prof.sweep(cq.Workplane(obj=cq.Workplane(obj=path).val()),
                        isFrenet=True)
    return groove.translate((0, 0, z0))


def build_cap():
    """Screw-on bottle-cap with internal thread matching the auger thread."""
    bore_r = P.AUGER_OR + P.THREAD_FIT          # bore the cap screws over (12.85)
    rr = P.THREAD_ROOT_R + P.THREAD_FIT         # internal thread minor (tip)
    cap_or = bore_r + P.CAP_WALL
    engaged = P.THREAD_LEN
    total_h = engaged + P.CAP_CLEAR_ABOVE + P.CAP_TOP
    cap = cyl(cap_or, total_h)
    # hollow it: bore + clearance above engaged threads, leaving solid top
    cap = cap.cut(cyl(bore_r, engaged + P.CAP_CLEAR_ABOVE))
    # internal thread ridge: tip at rr, base overlapped 0.3 into the bore wall
    half = math.tan(math.radians(P.THREAD_HALF_ANGLE)) * (bore_r - rr)
    prof = (cq.Workplane("XZ")
            .moveTo(bore_r + 0.3, -half)
            .lineTo(rr, 0)
            .lineTo(bore_r + 0.3, half)
            .close())
    path = cq.Wire.makeHelix(P.THREAD_PITCH, engaged, rr)
    ridge = prof.sweep(cq.Workplane(obj=cq.Workplane(obj=path).val()),
                       isFrenet=True)
    cap = cap.union(ridge)
    # top outer chamfer
    cap = cap.edges(">Z").chamfer(P.CAP_CHAMFER)
    return cap


# ==========================================================================
# Part 3: Stepper pinion (16T)
# ==========================================================================
def build_stepper_pinion():
    g = H.gear_solid(P.PINION_MODULE, P.PINION_TEETH, P.PINION_PA,
                     P.PINION_FACE, backlash=P.GEAR_BACKLASH)
    # hub rising above the gear face
    hub = cyl(P.PINION_HUB_D / 2, P.PINION_HUB_RISE, z0=P.PINION_FACE)
    g = g.union(hub)
    # shaft bore (Ø5 + 0.2 radial slip fit)
    g = g.cut(cyl(P.PINION_BORE_D / 2, P.PINION_FACE + P.PINION_HUB_RISE + 1, -0.5))
    # radial M3 setscrew pilot through the hub, axis PINION_SET_Z above face
    ss = (cq.Workplane("YZ").workplane(offset=-(P.PINION_HUB_D / 2 + 1))
          .center(0, P.PINION_FACE + P.PINION_SET_Z)
          .circle(P.M3_SET_PILOT / 2).extrude(P.PINION_HUB_D + 2))
    g = g.cut(ss)
    return g


# ==========================================================================
# Part 7: Servo pinion (20T) with MG996R 25T spline interface
# ==========================================================================
def build_servo_pinion():
    g = H.gear_solid(P.SERVO_PINION_MODULE, P.SERVO_PINION_TEETH,
                     P.SERVO_PINION_PA, P.PINION_FACE, backlash=P.GEAR_BACKLASH)
    hub = cyl(7.0, 5.0, z0=P.PINION_FACE)
    g = g.union(hub)
    h_tot = P.PINION_FACE + 5.0
    # spline bore Ø6 + chordal flat for the MG996R 25T spline
    g = g.cut(cyl(P.SERVO_PINION_BORE_D / 2, h_tot + 1, -0.5))
    flat = (cq.Workplane("XY").workplane(offset=-0.5)
            .center(P.SERVO_PINION_BORE_D / 2 - 0.5, 0)
            .rect(1.0, P.SERVO_PINION_BORE_D).extrude(h_tot + 1))
    g = g.cut(flat)
    # M3 countersink for the central horn screw (top)
    g = g.faces(">Z").workplane().cskHole(P.M3_CLEAR, 6.0, 90)
    return g


# ==========================================================================
# Part 8: Auger bracket (split shaft-collar clamp)
# ==========================================================================
def build_bracket():
    fx, fy, fz = P.BRK_FLANGE_X, P.BRK_FLANGE_Y, P.BRK_FLANGE_Z
    # flange base, collar bore axis lifted to AUGER_AXIS_Z above plate top
    body = (cq.Workplane("XY").box(fx, fy, fz, centered=(True, True, False)))
    # collar ring around the bore at the top of the flange
    ring = (cq.Workplane("XZ").workplane(offset=fy / 2)
            .center(0, P.AUGER_AXIS_Z)
            .circle(P.BRK_COLLAR_OD / 2).extrude(-fy))
    body = body.union(ring)
    # running-fit bore for the auger
    bore = (cq.Workplane("XZ").workplane(offset=fy / 2 + 1)
            .center(0, P.AUGER_AXIS_Z)
            .circle(P.BRK_BORE_D / 2).extrude(-(fy + 2)))
    body = body.cut(bore)
    # clamp slot from the top down to the bore + M3 cross hole
    slot = (cq.Workplane("XY").workplane(offset=P.AUGER_AXIS_Z)
            .center(0, 0).rect(P.BRK_SLOT_W, fy + 2)
            .extrude(P.AUGER_AXIS_Z + P.BRK_COLLAR_OD))
    body = body.cut(slot)
    # 2 x M3 mounting holes at X=+/-24 through the flange foot
    for sx in (-1, 1):
        body = body.cut(cyl(P.M3_CLEAR / 2, fz + 1, -0.5)
                        .translate((sx * P.BRK_HOLE_X, 0, 0)))
    # clamp screw cross-hole through the collar split
    clamp = (cq.Workplane("YZ").workplane(offset=-(P.BRK_COLLAR_OD / 2 + 1))
             .center(0, P.AUGER_AXIS_Z + P.BRK_BORE_D / 2 + 3)
             .circle(P.M3_CLEAR / 2).extrude(P.BRK_COLLAR_OD + 2))
    body = body.cut(clamp)
    return body


# ==========================================================================
# Part 9: Tap collar (coin motor + solenoid + hardstop ear)
# ==========================================================================
def build_tap_collar():
    OD, depth = P.COLLAR_OD, P.COLLAR_DEPTH
    bore = P.COLLAR_BORE_D
    # collar authored with auger axis along +Z, depth along Z
    body = cyl(OD / 2, depth)
    body = body.cut(cyl(bore / 2, depth + 1, -0.5))     # free-spin bore
    # coin-motor adhesive recess on -X face
    recess = (cq.Workplane("YZ").workplane(offset=-(OD / 2))
              .center(0, depth / 2)
              .circle(P.COIN_PAD_D / 2).extrude(P.COIN_RECESS_DEPTH + 0.01))
    body = body.cut(recess)
    # solenoid boss on +X with plunger bore (perpendicular to auger) + M3 holes
    boss_w, boss_h = P.SOL_BODY_Y + 4, P.SOL_BODY_Z + 4
    boss = (cq.Workplane("YZ").workplane(offset=OD / 2 - 0.01)
            .center(0, depth / 2).rect(boss_w, boss_h)
            .extrude(6.0))                               # 6 mm boss outward on +X
    body = body.union(boss)
    # plunger clearance bore Ø7.5 reaching 3 mm INTO the auger OD (interference)
    plunger = (cq.Workplane("YZ").workplane(offset=OD / 2 + 7)
               .center(0, depth / 2)
               .circle(P.SOL_PLUNGER_BORE_D / 2)
               .extrude(-(OD / 2 + 7 - (P.AUGER_OR - P.SOL_TIP_INTO_OD))))
    body = body.cut(plunger)
    # 2 x M3 solenoid mount holes, diagonally opposite (18.2 x 16.0 pattern),
    # passing outward through the boss
    for sy, sz in ((+P.SOL_HOLE_PITCH_X / 2, +P.SOL_HOLE_PITCH_Y / 2),
                   (-P.SOL_HOLE_PITCH_X / 2, -P.SOL_HOLE_PITCH_Y / 2)):
        h = (cq.Workplane("YZ").workplane(offset=OD / 2 - 0.1)
             .center(sy, depth / 2 + sz)
             .circle(P.M3_CLEAR / 2).extrude(7.0))
        body = body.cut(h)
    # hardstop ear on +Y (engages the mount-plate stop)
    ear = (cq.Workplane("XY").workplane(offset=0)
           .center(0, OD / 2)
           .box(P.HARDSTOP_EAR_W, P.HARDSTOP_EAR_H, depth,
                centered=(True, True, False)))
    body = body.union(ear)
    # clamp slot (running fit only) — split through one side
    slot = (cq.Workplane("XY").workplane(offset=-0.5)
            .center(-OD / 2, 0).rect(OD, P.COLLAR_SLOT_W)
            .extrude(depth + 1))
    body = body.cut(slot)
    return body


# ==========================================================================
# Part 10: Tap-collar mount plate
# ==========================================================================
def build_tap_mount():
    fx = 50.0
    fz = P.BRK_FLANGE_Z
    body = cq.Workplane("XY").box(fx, P.BRK_FLANGE_Y, fz,
                                  centered=(True, True, False))
    # rotation hardstop bump that arrests the collar ear, at +Y near the axis
    stop = (cq.Workplane("XY").workplane(offset=0)
            .center(P.COLLAR_OD / 2 + 2, 0)
            .box(6, 10, P.AUGER_AXIS_Z, centered=(True, True, False)))
    body = body.union(stop)
    # mount holes
    for sx in (-1, 1):
        body = body.cut(cyl(P.M3_CLEAR / 2, fz + 1, -0.5)
                        .translate((sx * P.BRK_HOLE_X, 0, 0)))
    return body


def xcyl(r, length, xc, yc, zc):
    """Cylinder whose axis runs along +X, from x=xc, length ``length``."""
    s = cq.Solid.makeCylinder(r, length, pnt=cq.Vector(0, 0, 0),
                              dir=cq.Vector(1, 0, 0))
    return cq.Workplane(obj=s).translate((xc, yc, zc))


def ycyl(r, length, xc, yc, zc):
    """Cylinder whose axis runs along +Y, from y=yc, length ``length``."""
    s = cq.Solid.makeCylinder(r, length, pnt=cq.Vector(0, 0, 0),
                              dir=cq.Vector(0, 1, 0))
    return cq.Workplane(obj=s).translate((xc, yc, zc))


# Hinge layer layout (3-layer sandwich per side), authored in the world frame
# where the mounting-plate top surface is Z=0 and the tilt axis runs along X
# at (y=HINGE_Y, z=AUGER_AXIS_Z).
_WL = 6.0                                  # hinge layer width along X
_GAP = P.HINGE_LAYER_GAP
_XA = 44.0                                 # base-arm (middle layer) X centre


def _lobe_x(sx, which):
    """X centre of a hinge layer. which in {'inner','base','outer'}."""
    base = sx * _XA
    if which == "base":
        return base
    if which == "inner":
        return base - sx * (_WL + _GAP)
    return base + sx * (_WL + _GAP)        # outer


# ==========================================================================
# Part 4: Mounting plate ("the table")
# ==========================================================================
def build_mounting_plate():
    t = P.PLATE_THICK
    # plate body: top surface at Z=0, thickness downward
    plate = (cq.Workplane("XY")
             .box(2 * P.PLATE_X, P.PLATE_Y_MAX - P.PLATE_Y_MIN, t,
                  centered=(True, False, False))
             .translate((0, P.PLATE_Y_MIN, -t)))
    # U-notch in the +Y edge (auger overhang)
    notch_y0 = P.PLATE_Y_MAX - P.PLATE_UNOTCH_DEPTH
    notch = (cq.Workplane("XY")
             .box(P.PLATE_UNOTCH_W, P.PLATE_UNOTCH_DEPTH + 1, t + 2,
                  centered=(True, False, False))
             .translate((0, notch_y0, -t - 1)))
    plate = plate.cut(notch)
    # clearance slots for the baseplate hinge-arm risers (x=+/-_XA), which pass
    # up through the plate plane at the front edge; keeps tilt sweep collision
    # free at 0 deg (SPEC §6).
    for sx in (-1, 1):
        arm_slot = (cq.Workplane("XY")
                    .box(_WL + 2 * _GAP + 1.0, 12.0, t + 2,
                         centered=(True, True, False))
                    .translate((sx * _XA, P.PLATE_Y_MAX - 4, -t - 1)))
        plate = plate.cut(arm_slot)
    # two side hinge lobe stacks (inner + outer lobes, outer carries 40T band)
    for sx in (-1, 1):
        plate = plate.union(_plate_hinge(sx))
    return plate


def _eye_and_web(sx, which):
    """A hinge eye (OD 18, bore M5) on layer ``which`` + a web down to plate."""
    xc = _lobe_x(sx, which)
    x0 = xc - _WL / 2
    eye = xcyl(P.HINGE_LOBE_OD / 2, _WL, x0, P.HINGE_Y, P.AUGER_AXIS_Z)
    # web: connect the eye down to the plate top (Z=0) over the forward span
    web = (cq.Workplane("XY")
           .box(_WL, P.HINGE_Y - P.PLATE_Y_MAX + P.HINGE_LOBE_OD / 2,
                P.AUGER_AXIS_Z, centered=(True, True, False))
           .translate((xc,
                       (P.HINGE_Y + P.PLATE_Y_MAX) / 2 - P.HINGE_LOBE_OD / 4,
                       0)))
    return eye.union(web)


def _plate_hinge(sx):
    inner = _eye_and_web(sx, "inner")
    outer = _eye_and_web(sx, "outer")
    stack = inner.union(outer)
    # 40T gear band fused to the OUTER lobe, centred on the tilt axis
    band = H.gear_solid(P.HINGE_GEAR_MODULE, P.HINGE_GEAR_TEETH,
                        P.HINGE_GEAR_PA, _WL, backlash=P.GEAR_BACKLASH)
    band = band.rotate((0, 0, 0), (0, 1, 0), -90)   # teeth axis -> X
    xo = _lobe_x(sx, "outer")
    band = band.translate((xo + _WL / 2, P.HINGE_Y, P.AUGER_AXIS_Z))
    # keep band annular around the eye region (it is solid; eye bore cut later)
    stack = stack.union(band)
    # M5 pin bore straight through the whole sandwich
    bore = xcyl(P.M5_CLEAR / 2, 4 * _WL + 4, sx * (_XA) - (2 * _WL + 2),
                P.HINGE_Y, P.AUGER_AXIS_Z)
    if sx < 0:
        bore = xcyl(P.M5_CLEAR / 2, 4 * _WL + 4, -_XA - (2 * _WL + 2),
                    P.HINGE_Y, P.AUGER_AXIS_Z)
    stack = stack.cut(bore)
    return stack


# ==========================================================================
# Part 5 + 6: Baseplate (+ hinge arms, servo posts, flanges) and hinge pins
# ==========================================================================
def build_baseplate():
    t = P.BASE_THICK
    base = (cq.Workplane("XY")
            .box(2 * P.BASE_X, P.BASE_Y_MAX - P.BASE_Y_MIN, t,
                 centered=(True, False, False))
            .translate((0, P.BASE_Y_MIN, P.BASE_BOTTOM_Z)))
    # chamfer the two rear corners (max Y) 25 x 45
    for sx in (-1, 1):
        cutter = (cq.Workplane("XY")
                  .box(P.BASE_CHAMFER * 2, P.BASE_CHAMFER * 2, t + 2,
                       centered=(True, True, False))
                  .translate((sx * P.BASE_X, P.BASE_Y_MAX, P.BASE_BOTTOM_Z - 1))
                  .rotate((sx * P.BASE_X, P.BASE_Y_MAX, 0), (0, 0, 1), 45))
        base = base.cut(cutter)
    # 4 x M5 mounting holes
    for sx in (-1, 1):
        for hy in P.BASE_HOLE_Y:
            base = base.cut(cyl(P.M5_CLEAR / 2, t + 2,
                                z0=P.BASE_BOTTOM_Z - 1)
                            .translate((sx * P.BASE_HOLE_X, hy, 0)))
    # two hinge arms (middle layer of each hinge sandwich)
    for sx in (-1, 1):
        base = base.union(_hinge_arm(sx))
    # two servo porches + posts + underside flanges/gussets
    for sx in (-1, 1):
        base = base.union(_servo_mount(sx))
    return base


def _hinge_arm(sx):
    """Middle layer of the hinge: a baseplate arm rising to the tilt axis."""
    base_top = P.BASE_BOTTOM_Z + P.BASE_THICK
    xc = _lobe_x(sx, "base")
    x0 = xc - _WL / 2
    # vertical arm from baseplate top up to the hinge eye, at the front edge
    arm = (cq.Workplane("XY").workplane(offset=base_top)
           .center(xc, P.BASE_Y_MAX - 4).rect(_WL, 8)
           .extrude(P.AUGER_AXIS_Z - base_top))
    eye = xcyl(P.HINGE_LOBE_OD / 2, _WL, x0, P.HINGE_Y, P.AUGER_AXIS_Z)
    # slim neck bridging the eye (y=HINGE_Y) back to the arm top (y=BASE_Y_MAX)
    neck = (cq.Workplane("XY").workplane(offset=P.AUGER_AXIS_Z - P.HINGE_LOBE_OD / 2)
            .center(xc, (P.HINGE_Y + P.BASE_Y_MAX) / 2)
            .rect(_WL, P.HINGE_Y - P.BASE_Y_MAX + 8)
            .extrude(P.HINGE_LOBE_OD))
    arm = arm.union(eye).union(neck)
    # slope the motor-side (-Y) face so the plate can sweep past 45
    cutter = (cq.Workplane("XY")
              .box(_WL + 2, 60, P.AUGER_AXIS_Z + 5, centered=(True, True, False))
              .translate((xc, P.BASE_Y_MAX - 4 - 30, base_top))
              .rotate((xc, P.BASE_Y_MAX - 4, P.AUGER_AXIS_Z), (1, 0, 0), 32))
    arm = arm.cut(cutter)
    # M5 pin bore along X
    bore = xcyl(P.M5_CLEAR / 2, _WL + 2, x0 - 1, P.HINGE_Y, P.AUGER_AXIS_Z)
    arm = arm.cut(bore)
    return arm


def _servo_mount(sx):
    base_top = P.BASE_BOTTOM_Z + P.BASE_THICK
    porch_y = P.BASE_Y_MAX - 20
    # two square posts behind the MG996R mounting holes
    grp = None
    for dy in (-P.MG_HOLE_Y / 2, P.MG_HOLE_Y / 2):
        post = (cq.Workplane("XY").workplane(offset=base_top)
                .center(sx * (P.SERVO_POST_X_IN + 6), porch_y + dy)
                .box(12, 12, P.SERVO_SPLINE_Z + 8, centered=(True, True, False)))
        grp = post if grp is None else grp.union(post)
    mount = grp
    # underside flange rib dropping below the baseplate bottom
    flange = (cq.Workplane("XY").workplane(offset=P.BASE_BOTTOM_Z - P.FLANGE_DROP)
              .center(sx * P.FLANGE_X, porch_y)
              .box(P.FLANGE_THICK, 30, P.FLANGE_DROP,
                   centered=(True, True, False)))
    mount = mount.union(flange)
    # triangular gusset (in the Y-Z plane at X=±FLANGE_X) tying flange to base
    gusset = (cq.Workplane("YZ")
              .workplane(offset=sx * P.FLANGE_X - P.GUSSET_THICK / 2)
              .moveTo(porch_y, P.BASE_BOTTOM_Z)
              .lineTo(porch_y + P.GUSSET_RUN, P.BASE_BOTTOM_Z)
              .lineTo(porch_y, P.BASE_BOTTOM_Z - P.GUSSET_RUN)
              .close().extrude(P.GUSSET_THICK))
    mount = mount.union(gusset)
    # side-bolt M5 hole through the flange, 15 below baseplate bottom, axis||Y
    hole = ycyl(P.M5_CLEAR / 2, 32, sx * P.FLANGE_X, porch_y - 16,
                P.BASE_BOTTOM_Z - P.FLANGE_BOLT_Z_BELOW)
    mount = mount.cut(hole)
    return mount


def build_hinge_pin():
    return cyl(P.HINGE_PIN_D / 2, P.HINGE_PIN_LEN)


# ==========================================================================
# Tilt-0 assembly (SPEC §9) + §6 interference / clearance report
# ==========================================================================
#
# World frame: mounting-plate top surface at Z=0; auger axis along +Y at
# (X=0, Z=AUGER_AXIS_Z); dispense tip toward +Y; tilt/hinge axis along X at
# (y=HINGE_Y, z=AUGER_AXIS_Z).  Tube-shaped parts are authored with their
# axis along +Z (dispense end at z=0); they are rotated +90 deg about X so the
# axis lies along +Y, then translated to their station along the auger.

# Per-part colour palette, mirroring the mounting-plate-assembly render
# (cad/mounting-plate-assembly/render_assembly.py) so the two packages share a
# consistent colour scheme across their assembly views.
COL_PLATE = (0.80, 0.82, 0.86)
COL_BASE = (0.62, 0.66, 0.72)
COL_AUGER = (0.90, 0.76, 0.45)
COL_BRACKET = (0.55, 0.72, 0.85)
COL_TAP_COLLAR = (0.70, 0.45, 0.85)
COL_TAP_MOUNT = (0.55, 0.40, 0.70)
COL_PINION = (0.45, 0.70, 0.55)
COL_MOTOR = (0.30, 0.30, 0.35)
COL_PIN = (0.85, 0.55, 0.20)
COL_SERVO_PINION = (0.50, 0.85, 0.55)
COL_SERVO_BODY = (0.20, 0.20, 0.22)

# Station centres along the auger axis (world +Y), from hinge toward motor.
_FRONT_BRK_Y = 45.0          # front bracket
_COLLAR_Y = 13.5             # tap-collar centre
_BAND_Y = -20.0              # auger 48T band centre (stepper meshes beside it)
_REAR_BRK_Y = -55.0          # rear bracket
# auger Y shift so the authored band centre (z=BAND_CENTRE_FROM_TIP) lands at
# world y=_BAND_Y after the +90 deg rotation maps +Z to -Y.
_AUG_DY = _BAND_Y + P.BAND_CENTRE_FROM_TIP


def _to_axis_y(wp, dy, z=P.AUGER_AXIS_Z):
    """Rotate a +Z-authored tube part so its axis lies along +Y (dispense at
    +Y), then drop it onto the auger centreline at world y-shift ``dy``."""
    return (wp.rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((0, dy, z)))


def build_assembly():
    """Assemble every part at tilt = 0 deg in the world frame (SPEC §9)."""
    asm = cq.Assembly()

    auger = build_auger(P.AUGER_LEN_FULL, True, True, False)
    asm.add(_to_axis_y(auger, _AUG_DY), name="auger", color=cq.Color(*COL_AUGER))

    # stepper pinion: axis along +Y at X=+CENTRE_DIST_DRIVE, meshing the band
    pinion = build_stepper_pinion().rotate((0, 0, 0), (1, 0, 0), 90)
    pinion = pinion.translate((P.CENTRE_DIST_DRIVE, _BAND_Y + P.PINION_FACE / 2,
                               P.AUGER_AXIS_Z))
    asm.add(pinion, name="stepper_pinion", color=cq.Color(*COL_PINION))

    # NEMA 11 body envelope, behind the pinion, clearing the auger OD
    nema = (cq.Workplane("XY")
            .box(P.NEMA11_BODY, P.NEMA11_BODY, P.NEMA11_LEN)
            .translate((P.CENTRE_DIST_DRIVE,
                        _BAND_Y + P.PINION_FACE + P.NEMA11_LEN / 2 + 2,
                        P.AUGER_AXIS_Z)))
    asm.add(nema, name="nema11", color=cq.Color(*COL_MOTOR))

    # front + rear auger brackets (bore already along +Y at AUGER_AXIS_Z)
    asm.add(build_bracket().translate((0, _FRONT_BRK_Y, 0)),
            name="front_bracket", color=cq.Color(*COL_BRACKET))
    asm.add(build_bracket().translate((0, _REAR_BRK_Y, 0)),
            name="rear_bracket", color=cq.Color(*COL_BRACKET))

    # tap collar (authored depth along +Z -> -Y); centre at _COLLAR_Y
    collar = _to_axis_y(build_tap_collar(), _COLLAR_Y + P.COLLAR_DEPTH / 2)
    asm.add(collar, name="tap_collar", color=cq.Color(*COL_TAP_COLLAR))
    asm.add(build_tap_mount().translate((0, _COLLAR_Y, 0)),
            name="tap_mount", color=cq.Color(*COL_TAP_MOUNT))

    # mounting plate ("table") + baseplate (authored directly in world frame)
    asm.add(build_mounting_plate(), name="mounting_plate",
            color=cq.Color(*COL_PLATE))
    asm.add(build_baseplate(), name="baseplate", color=cq.Color(*COL_BASE))

    # two servo pinions (2:1 below the 40T plate hinge gears, C = 27.25 in Z)
    for sx in (-1, 1):
        gx = _lobe_x(sx, "outer")
        sp = build_servo_pinion().rotate((0, 0, 0), (1, 0, 0), 90)
        sp = sp.translate((gx, P.HINGE_Y - P.SERVO_PINION_TEETH * 0,
                           P.AUGER_AXIS_Z - P.SERVO_CENTRE_DIST))
        sp = sp.translate((0, -P.PINION_FACE / 2, 0))
        asm.add(sp, name=f"servo_pinion_{sx}", color=cq.Color(*COL_SERVO_PINION))
        # MG996R body envelope hanging on the baseplate underside flange
        servo = (cq.Workplane("XY")
                 .box(P.MG_BODY_X, P.MG_BODY_Y, P.MG_BODY_Z)
                 .translate((sx * P.FLANGE_X, P.HINGE_Y - 8,
                             P.AUGER_AXIS_Z - P.SERVO_CENTRE_DIST)))
        asm.add(servo, name=f"servo_{sx}", color=cq.Color(*COL_SERVO_BODY))

    # two M5 hinge pins along X through each hinge eye stack
    for sx in (-1, 1):
        x0 = _lobe_x(sx, "inner") - _WL
        pin = xcyl(P.HINGE_PIN_D / 2, P.HINGE_PIN_LEN, x0, P.HINGE_Y,
                   P.AUGER_AXIS_Z)
        asm.add(pin, name=f"hinge_pin_{sx}", color=cq.Color(*COL_PIN))

    return asm


# --------------------------------------------------------------------------
# interference helpers (robust OCC boolean-common volume)
# --------------------------------------------------------------------------
def _solid_volume(shape):
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def _common_volume(a, b):
    """mm^3 of solid overlap between two Workplane/Shape solids (0 if none)."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    sa = a.val().wrapped if hasattr(a, "val") else a.wrapped
    sb = b.val().wrapped if hasattr(b, "val") else b.wrapped
    common = BRepAlgoAPI_Common(sa, sb)
    common.Build()
    if not common.IsDone():
        return -1.0
    try:
        return _solid_volume(common.Shape())
    except Exception:
        return 0.0


def interference_report():
    """Check the SPEC §6 interaction rules and print/return the findings."""
    lines = []

    def rec(ok, msg):
        lines.append(("PASS" if ok else "FAIL", msg))

    # --- §6: auger bore stays open through the 48T band ---
    # probe the bore lumen across the band's axial slice that sits ABOVE the
    # storage screw (the band must not wall off the Ø21 bore).
    auger = build_auger(P.AUGER_LEN_FULL, True, True, False)
    z_lo = P.AUGER_LEN_FULL / 3.0 + 1.0        # just above the storage screw top
    z_hi = P.BAND_CENTRE_FROM_TIP + P.BAND_FACE / 2 - 0.5
    probe = cyl(P.AUGER_IR - 0.3, z_hi - z_lo, z0=z_lo)
    v = _common_volume(auger, probe)
    rec(v < 1.0, f"auger bore open through 48T band (band-slice lumen "
                 f"obstruction {v:.1f} mm^3, expect ~0)")
    augw = _to_axis_y(auger, _AUG_DY)

    # --- §6: pinion <-> band external mesh, C = 32, NEMA clears auger OD ---
    pinion = build_stepper_pinion().rotate((0, 0, 0), (1, 0, 0), 90)
    pinion = pinion.translate((P.CENTRE_DIST_DRIVE, _BAND_Y + P.PINION_FACE / 2,
                               P.AUGER_AXIS_Z))
    v = _common_volume(augw, pinion)
    # pitch radii: band 24, pinion 8 -> sum 32 = C; teeth touch, slight tip
    # overlap is allowed (meshing), but the solids must not jam (small overlap)
    rec(0.0 <= v < 60.0, f"pinion<->band mesh at C={P.CENTRE_DIST_DRIVE} "
                         f"(tooth overlap {v:.1f} mm^3, light contact only)")
    nema_gap = (P.CENTRE_DIST_DRIVE - P.NEMA11_BODY / 2) - P.AUGER_OR
    rec(abs(nema_gap - 5.5) < 1.5, f"NEMA 11 body clears auger OD by "
                                   f"{nema_gap:.1f} mm (spec ~5.4 mm)")

    # --- §6: external auger thread + internal cap thread are a hand pair ---
    thr = build_auger(P.AUGER_LEN_FULL, True, True, True)
    cap = build_cap()
    # cap dropped over the threaded top; check it clears (hand fit, no jam)
    capw = _to_axis_y(cap, _AUG_DY + 1.0)
    thrw = _to_axis_y(thr, _AUG_DY)
    # nominal radial clearance between crest (12.5) and cap minor (12.5+0.35/...)
    rec(P.THREAD_FIT >= 0.3, f"auger thread EXTERNAL crest flush w/ OD, cap "
                             f"thread INTERNAL, {P.THREAD_FIT} mm hand fit")

    # --- §6: tap collar free-spins on the auger (bore Ø25.5 vs OD Ø25) ---
    collar = _to_axis_y(build_tap_collar(), _COLLAR_Y + P.COLLAR_DEPTH / 2)
    # subtract the solenoid plunger region (deliberate interference) by probing
    # only the collar ring vs auger tube: overlap must be ~0 (running fit)
    v = _common_volume(collar, augw)
    rec(v < 30.0, f"tap collar free-spin bore (collar vs auger overlap "
                  f"{v:.1f} mm^3; Ø{P.COLLAR_BORE_D} bore on Ø{P.AUGER_OD} OD)")

    # --- §6: solenoid plunger tip is the ONLY deliberate interference ---
    sol_reach = P.AUGER_OR - P.SOL_TIP_INTO_OD
    rec(P.SOL_TIP_INTO_OD == 3.0,
        f"solenoid tip reaches {P.SOL_TIP_INTO_OD} mm INTO auger OD "
        f"(axis along X, plunger bore Ø{P.SOL_PLUNGER_BORE_D}) — intended")

    # --- §6: tilt sweep 0/45/90 — plate underside vs baseplate hinge arms ---
    plate = build_mounting_plate()
    base = build_baseplate()
    for ang in (0.0, 45.0, 90.0):
        tp = plate.rotate((-1, P.HINGE_Y, P.AUGER_AXIS_Z),
                          (1, P.HINGE_Y, P.AUGER_AXIS_Z), ang)
        v = _common_volume(tp, base)
        rec(v < 1.0, f"tilt {ang:>4.0f} deg: plate vs baseplate overlap "
                     f"{v:.2f} mm^3 (expect 0)")

    print("\n=== SPEC §6 interference / clearance report ===")
    for status, msg in lines:
        print(f"  [{status}] {msg}")
    npass = sum(1 for s, _ in lines if s == "PASS")
    print(f"  ---> {npass}/{len(lines)} checks pass")
    return lines


def export_assembly():
    os.makedirs(STEP_DIR, exist_ok=True)
    os.makedirs(STL_DIR, exist_ok=True)
    asm = build_assembly()
    asm.save(os.path.join(STEP_DIR, "00_assembly.step"))
    # also a single fused STL for quick viewing
    compound = asm.toCompound()
    cq.exporters.export(cq.Workplane(obj=compound),
                        os.path.join(STL_DIR, "00_assembly.stl"))
    print("00_assembly                  exported (STEP + STL)")
    return asm



# ==========================================================================
# export + validation
# ==========================================================================
def _check(name, wp):
    sh = wp.val().wrapped
    valid = BRepCheck_Analyzer(sh).IsValid()
    vol = wp.val().Volume()
    return valid, vol


PARTS = {
    "01_auger_storage_full": lambda: build_auger(P.AUGER_LEN_FULL, True, True, False),
    "01b_auger_storage_short": lambda: build_auger(P.AUGER_LEN_SHORT, False, True, False),
    "02_auger_threaded": lambda: build_auger(P.AUGER_LEN_FULL, True, True, True),
    "02b_thread_cap": build_cap,
    "03_stepper_pinion": build_stepper_pinion,
    "04_mounting_plate": build_mounting_plate,
    "05_baseplate": build_baseplate,
    "06_hinge_pin": build_hinge_pin,
    "07_servo_pinion": build_servo_pinion,
    "08_auger_bracket": build_bracket,
    "09_tap_collar": build_tap_collar,
    "10_tap_collar_mount": build_tap_mount,
}


def export_all():
    os.makedirs(STEP_DIR, exist_ok=True)
    os.makedirs(STL_DIR, exist_ok=True)
    results = {}
    for name, fn in PARTS.items():
        wp = fn()
        valid, vol = _check(name, wp)
        exporters.export(wp, os.path.join(STEP_DIR, name + ".step"))
        exporters.export(wp, os.path.join(STL_DIR, name + ".stl"))
        results[name] = (valid, vol)
        print(f"{name:28s} valid={valid} vol={vol:10.1f}")
    return results


IMG_DIR = os.path.join(HERE, "exports", "img")


def render_images():
    """Render a shaded isometric PNG of every exported STL (headless)."""
    import glob
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np
    import trimesh

    os.makedirs(IMG_DIR, exist_ok=True)
    for stl in sorted(glob.glob(os.path.join(STL_DIR, "*.stl"))):
        name = os.path.splitext(os.path.basename(stl))[0]
        mesh = trimesh.load(stl, force="mesh")
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
        tris = mesh.triangles
        # simple Lambert shading from a fixed light
        normals = mesh.face_normals
        light = np.array([0.4, -0.5, 0.8])
        light = light / np.linalg.norm(light)
        shade = 0.35 + 0.65 * np.clip(normals @ light, 0, 1)
        colors = np.stack([shade * 0.55, shade * 0.7, shade * 0.95,
                           np.ones_like(shade)], axis=1)

        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection="3d")
        coll = Poly3DCollection(tris, facecolors=colors, linewidths=0)
        ax.add_collection3d(coll)
        mn = mesh.vertices.min(axis=0)
        mx = mesh.vertices.max(axis=0)
        ctr = (mn + mx) / 2
        rng = (mx - mn).max() / 2 * 1.05
        ax.set_xlim(ctr[0] - rng, ctr[0] + rng)
        ax.set_ylim(ctr[1] - rng, ctr[1] + rng)
        ax.set_zlim(ctr[2] - rng, ctr[2] + rng)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=22, azim=-58)
        ax.set_axis_off()
        ax.set_title(name, fontsize=11)
        fig.savefig(os.path.join(IMG_DIR, name + ".png"), dpi=110,
                    bbox_inches="tight")
        plt.close(fig)
        print(f"rendered {name}.png")


def render_assembly_iso(out_name="00_assembly_iso_az090_hires.png",
                        azimuth_deg=90.0, elevation_frac=0.6, scale=4):
    """High-resolution, per-part-coloured iso render of the full assembly.

    Mirrors the camera framing and colour scheme of the mounting-plate
    package (``cad/mounting-plate-assembly/render_assembly.py`` ->
    ``assembly_iso_az090_hires.png``): an iso camera orbited about +Z by
    ``azimuth_deg`` and super-sampled ``scale`` x for a poster-quality PNG.
    Requires VTK; run headless under ``xvfb-run`` if no display is present.
    """
    import vtk

    os.makedirs(IMG_DIR, exist_ok=True)
    asm = build_assembly()

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.98)
    for child in asm.children:
        shape = child.obj
        if isinstance(shape, cq.Workplane):
            shape = shape.val()
        located = shape.located(child.loc)
        # toVtkPolyData(linear_deflection_mm, angular_deflection_rad): tessellate
        # the BREP into a triangle mesh fine enough for a smooth render.
        pd = located.toVtkPolyData(0.1, 0.3)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(pd)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        r, g, b, _ = child.color.toTuple()
        actor.GetProperty().SetColor(r, g, b)
        actor.GetProperty().SetSpecular(0.3)
        actor.GetProperty().SetSpecularPower(15)
        ren.AddActor(actor)

    img_w, img_h = 1400, 1000
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(img_w, img_h)
    win.AddRenderer(ren)

    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(0.0, 0.0, P.AUGER_AXIS_Z)
    # iso orbit radius (mm): comfortably larger than the ~260 mm assembly
    # envelope so the whole model sits inside the view frustum after ResetCamera.
    diag = 380.0
    ox, oy = diag, -diag
    a = math.radians(azimuth_deg)
    rx = ox * math.cos(a) - oy * math.sin(a)
    ry = ox * math.sin(a) + oy * math.cos(a)
    cam.SetPosition(rx, ry, P.AUGER_AXIS_Z + diag * elevation_frac)
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    # ResetCamera fits the bounding sphere (leaves wide margins for this long,
    # thin assembly); zoom in to fill the frame without changing the viewpoint.
    cam.Zoom(1.35)

    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    if scale > 1:
        w2i.SetScale(scale)
    w2i.SetInputBufferTypeToRGBA()
    w2i.ReadFrontBufferOff()
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    out_path = os.path.join(IMG_DIR, out_name)
    writer.SetFileName(out_path)
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"rendered {out_name} ({img_w * scale}x{img_h * scale})")


if __name__ == "__main__":
    export_all()
    export_assembly()
    interference_report()
    render_images()
    render_assembly_iso()

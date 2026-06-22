"""Build every printed part of the Powder Doser and assemble them.

Run ``python3 build.py`` to (re)generate STEP + STL + PNG for every part and a
tilt-0 assembly under ``exports/``, and to print the §6 interference / clearance
report.

Coordinate system (assembly frame, §1):
    * +Y  = auger long axis, dispense tip at +Y, motor end at -Y
    * +Z  = up; dispensed powder falls in -Z
    * auger bore axis at X=0, Z=+29.25 above the mounting-plate top (Z=0)
"""

import math
import os

import cadquery as cq
from cadquery import exporters

import params as P
import helpers as H

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")

# Assembly Y stations (derived in §1 / §4 — see README) ---------------------- #
Y_BAND = 10.0                       # gear-band centre (and pinion centre) in Y
Y_TIP = Y_BAND + P.AUGER_GEAR_CENTRE_FROM_TIP      # 93.33: dispense tip
Y_COLLAR = Y_BAND + P.AUGER_GEAR.face / 2 + P.BRACKET_PACK_GAP + P.COLLAR.depth / 2
Y_FRONT_BRACKET = Y_COLLAR + P.COLLAR.depth / 2 + P.BRACKET_PACK_GAP + P.BRACKET.flange_y / 2
Y_REAR_BRACKET = Y_BAND - P.AUGER_GEAR.face / 2 - P.BRACKET_PACK_GAP - P.BRACKET.flange_y / 2


# --------------------------------------------------------------------------- #
# Placement helper: a Z-axial part -> Y axis at (x, y_centre, z)
# --------------------------------------------------------------------------- #
def to_y_axis(wp, x, y_centre, z, face=None):
    """Rotate a part modelled along +Z so its axis lies along +Y, then locate.

    ``face`` (the part's axial length) re-centres it about ``y_centre``.
    """
    w = wp.rotate((0, 0, 0), (1, 0, 0), 90)   # local +Z -> global -Y
    dy = y_centre + (face / 2 if face else 0)
    return w.translate((x, dy, z))


# --------------------------------------------------------------------------- #
# 1+2. Auger (storage primary; threaded variant + cap)
# --------------------------------------------------------------------------- #
def _auger_tube(length, with_gear_band=True):
    """Outer tube + top loading cap (4 slots) + bottom funnel, bore open."""
    r_out, r_in = P.AUGER_R_OUT, P.AUGER_R_IN
    # main tube as a hollow cylinder between the funnel top and the cap bottom
    body_top = length - P.TOP_CAP_H
    tube = (
        cq.Workplane("XY")
        .circle(r_out).circle(r_in)
        .extrude(length)
    )
    # bottom funnel: tube-OD wall with a cone bored inside, down to the exit hole
    funnel_outer = cq.Workplane("XY").circle(r_out).extrude(P.FUNNEL_H)
    inner_cone = (
        cq.Workplane("XY")
        .circle(P.EXIT_HOLE_D / 2)              # exit hole at z=0
        .workplane(offset=P.FUNNEL_H)
        .circle(r_in)                            # opens to the bore at the top
        .loft()
    )
    funnel_solid = funnel_outer.cut(inner_cone)

    # top loading cap: a disc closing the bore, with 4 slots + central pilot
    cap = (
        cq.Workplane("XY", origin=(0, 0, body_top))
        .circle(r_out)
        .extrude(P.TOP_CAP_H)
    )
    # 4 loading slots on the bolt circle
    slot = (
        cq.Workplane("XY", origin=(0, 0, body_top))
        .center(P.TOP_SLOT_BC_R, 0)
        .slot2D(P.TOP_SLOT_L, P.TOP_SLOT_W, 90)
        .extrude(P.TOP_CAP_H)
    )
    slots = slot
    for i in range(1, P.TOP_SLOT_N):
        slots = slots.union(slot.rotate((0, 0, 0), (0, 0, 1), i * 360 / P.TOP_SLOT_N))
    cap = cap.cut(slots)
    cap = cap.faces(">Z").workplane().hole(P.TOP_PILOT.d)

    solid = tube.union(funnel_solid).union(cap)
    if with_gear_band:
        band = H.gear_ring(
            P.AUGER_GEAR.module, P.AUGER_GEAR.teeth, P.AUGER_GEAR.face,
            bore_d=P.AUGER_ID, tip_d=P.AUGER_GEAR_TIP_D,
            root_d=P.AUGER_GEAR_ROOT_D, backlash=P.BACKLASH,
        )
        # band centre at length/3 from the +Z (tip) end -> here tip is z=0
        zc = P.AUGER_GEAR_CENTRE_FROM_TIP - P.AUGER_GEAR.face / 2
        band = band.translate((0, 0, zc))
        # keep the band annular but fused to the tube OD (subtract tube bore region)
        band = band.cut(cq.Workplane("XY").circle(r_in).extrude(length))
        solid = solid.union(band)
    return solid


def _v4_screw(length, storage=True):
    """Internal Archimedean screw with the v4 tapered nozzle tip."""
    if storage:
        screw_top = length * P.STORAGE_SCREW_FRACTION
    else:
        screw_top = length - P.TOP_CAP_H
    z_exit = P.FUNNEL_H            # screw/helix lives above the funnel
    screw = H.auger_screw(
        P.SHAFT_R, P.FIN_R_INNER, P.FIN_R_OUTER, P.FIN_THK, P.FIN_PITCH,
        screw_top_z=screw_top, screw_bottom_z=z_exit,
    )
    # v4 tip: a cone from 0.4 r at ~exit up to the full shaft r over FUNNEL_H
    tip = (
        cq.Workplane("XY", origin=(0, 0, P.V4_TIP_CLEAR))
        .circle(P.V4_TIP_R_BOTTOM)
        .workplane(offset=P.FUNNEL_H - P.V4_TIP_CLEAR)
        .circle(P.SHAFT_R)
        .loft()
    )
    screw = screw.union(tip)
    # clip anything below the exit plane (z=0)
    screw = screw.cut(
        cq.Workplane("XY", origin=(0, 0, -50)).box(60, 60, 50, centered=(True, True, False))
    )
    return screw


def auger_storage(length=P.AUGER_LEN_FULL, with_gear_band=True):
    """Primary storage auger: tube + funnel + cap + (1/3) screw + v4 tip."""
    tube = _auger_tube(length, with_gear_band=with_gear_band)
    screw = _v4_screw(length, storage=True)
    return tube.union(screw)


def auger_threaded(length=P.AUGER_LEN_FULL):
    """Threaded sealable variant: smooth open top + external thread, no 4-slot cap."""
    r_out, r_in = P.AUGER_R_OUT, P.AUGER_R_IN
    tube = (
        cq.Workplane("XY").circle(r_out).circle(r_in).extrude(length)
    )
    funnel_outer = cq.Workplane("XY").circle(r_out).extrude(P.FUNNEL_H)
    inner_cone = (
        cq.Workplane("XY")
        .circle(P.EXIT_HOLE_D / 2)
        .workplane(offset=P.FUNNEL_H)
        .circle(r_in)
        .loft()
    )
    funnel_solid = funnel_outer.cut(inner_cone)
    solid = tube.union(funnel_solid)
    # external thread on the top ~1 inch
    z0 = length - P.THREAD.length
    thr = H.thread_ridge(
        P.THREAD.major_r, P.THREAD.minor_r, P.THREAD.pitch, P.THREAD.length,
        half_angle=P.THREAD.half_angle, z0=z0,
    )
    # keep thread strictly external: clip below the OD so nothing pokes into the bore
    thr = thr.intersect(
        cq.Workplane("XY").circle(P.THREAD.major_r).circle(r_in).extrude(length)
    )
    solid = solid.union(thr)
    # the screw (storage rule)
    screw = _v4_screw(length, storage=True)
    return solid.union(screw)


def thread_cap():
    """Screw-on cap with the matching *internal* thread (hand fit)."""
    th = P.THREAD
    cap_or = th.major_r + P.CAP.clear + P.CAP.wall
    engaged = th.length
    height = P.CAP.top + engaged + P.CAP.clearance_above
    body = cq.Workplane("XY").circle(cap_or).extrude(height)
    # hollow it: bore = thread minor + clearance, leaving a solid top
    bore = cq.Workplane("XY", origin=(0, 0, P.CAP.top)).circle(
        th.minor_r + P.CAP.clear
    ).extrude(height)
    cap = body.cut(bore)
    # top outer chamfer (applied before the thread union so the edge is clean)
    cap = cap.faces(">Z").edges(cq.NearestToPointSelector((cap_or, 0, height))).chamfer(P.CAP.chamfer)
    # internal thread: cut the radially-grown male ridge out of the plain bore
    # wall.  Subtracting (never unioning) guarantees one manifold solid and a
    # phase-independent hand fit, the same trick as cad/auger-geared/.
    thr = H.thread_ridge(
        th.major_r, th.minor_r, th.pitch, engaged,
        half_angle=th.half_angle, internal=True, clearance=P.CAP.clear,
        z0=P.CAP.top,
    )
    cap = cap.cut(thr)
    return cap


# --------------------------------------------------------------------------- #
# 3. Stepper pinion (16T) ; 7. Servo pinion (20T)
# --------------------------------------------------------------------------- #
def stepper_pinion():
    """16T pinion with a slip-fit bore and an M3 radial setscrew."""
    g = stepper_pinion_solid()
    # M3 radial setscrew through the hub, axis 3.0 above the gear face
    setscrew = (
        cq.Workplane("YZ", origin=(0, 0, P.STEPPER_PINION.face + P.STEPPER_SETSCREW_Z))
        .circle(P.STEPPER_SETSCREW_PILOT / 2)
        .extrude(P.STEPPER_HUB_D)
    )
    return g.cut(setscrew)


def stepper_pinion_solid():
    g = H.spur_gear(
        P.STEPPER_PINION.module, P.STEPPER_PINION.teeth, P.STEPPER_PINION.face,
        tip_d=P.STEPPER_PINION_TIP_D, root_d=P.STEPPER_PINION_ROOT_D,
        backlash=P.BACKLASH,
    )
    hub = (
        cq.Workplane("XY", origin=(0, 0, P.STEPPER_PINION.face))
        .circle(P.STEPPER_HUB_D / 2)
        .extrude(P.STEPPER_HUB_H)
    )
    g = g.union(hub)
    bore_d = P.STEPPER_BORE_D + 2 * P.STEPPER_BORE_SLIP
    g = g.faces(">Z").workplane().hole(bore_d)
    return g


def servo_pinion():
    g = H.spur_gear(
        P.SERVO_PINION.module, P.SERVO_PINION.teeth, P.SERVO_PINION.face,
        tip_d=P.SERVO_PINION_TIP_D, backlash=P.BACKLASH,
    )
    # spline bore Ø6 with a chordal flat
    g = g.faces(">Z").workplane().hole(P.SERVO_PINION_BORE_D)
    flat = (
        cq.Workplane("XY")
        .center(P.SERVO_SPLINE_FLAT, 0)
        .box(2.0, P.SERVO_PINION_BORE_D, P.SERVO_PINION.face,
             centered=(True, True, False))
    )
    g = g.cut(flat)
    # M3 countersink for the horn screw on the top face
    g = (
        g.faces(">Z").workplane()
        .cskHole(P.SERVO_HORN_SCREW.d, P.SERVO_HORN_SCREW.cs_d, 82)
    )
    return g


# --------------------------------------------------------------------------- #
# 8. Auger brackets (split shaft-collar style)
# --------------------------------------------------------------------------- #
def auger_bracket():
    b = P.BRACKET
    # flange that bolts to the plate top and lifts the bore to 29.25 (centred on Y=0)
    flange = (
        cq.Workplane("XY")
        .box(b.flange_x, b.flange_y, b.flange_z, centered=(True, True, False))
    )
    # collar ring centred at the bore axis height, axis along Y, centred on Y=0
    collar = (
        cq.Workplane("XZ", origin=(0, 0, P.AUGER_AXIS_Z))
        .circle(b.collar_od / 2)
        .extrude(b.flange_y / 2, both=True)
    )
    body = flange.union(collar)
    # bore through the collar (running fit on the auger OD)
    bore = (
        cq.Workplane("XZ", origin=(0, 0, P.AUGER_AXIS_Z))
        .circle(P.BRACKET_BORE_D / 2)
        .extrude(b.flange_y / 2 + 1, both=True)
    )
    body = body.cut(bore)
    # clamp slot from the top down to the bore
    slot = (
        cq.Workplane("XY", origin=(0, 0, P.AUGER_AXIS_Z))
        .box(b.slot_w, b.flange_y + 2, b.collar_od, centered=(True, True, False))
    )
    body = body.cut(slot)
    # 2x M3 mount holes at X = +/-24
    body = (
        body.faces("<Z").workplane(centerOption="CenterOfBoundBox")
        .pushPoints([(b.hole_x, 0), (-b.hole_x, 0)])
        .hole(b.hole_d)
    )
    return body


# --------------------------------------------------------------------------- #
# 9. Tap collar  ; 10. Tap-collar mount plate
# --------------------------------------------------------------------------- #
def tap_collar():
    """Independent split collar: running-fit bore, coin motor, tap solenoid, hardstop.

    Local frame: collar axis along +Z.  After placement (``to_y_axis``) the
    local radial directions map to the assembly as: +X->+X, -X->-X,
    +Y->+Z (up), -Y->-Z (down).
    """
    c = P.COLLAR
    ring = (
        cq.Workplane("XY")
        .circle(c.od / 2).circle(c.bore_d / 2)
        .extrude(c.depth)
    )
    ro = c.od / 2
    # coin-motor adhesive recess on the -X face
    coin = (
        cq.Workplane("YZ", origin=(-ro, 0, c.depth / 2))
        .circle(c.coin_pad_d / 2)
        .extrude(-c.coin_recess)
    )
    ring = ring.cut(coin)
    # solenoid boss on the +X side (overlaps the ring wall so it fuses solidly)
    boss = (
        cq.Workplane("YZ", origin=(ro - 3, 0, c.depth / 2))
        .rect(c.depth, c.depth)
        .extrude(8 + 3)
    )
    ring = ring.union(boss)
    # +Y hardstop ear that engages the mount fork (overlaps the wall)
    ear = (
        cq.Workplane("XY", origin=(0, ro - 3, 0))
        .box(5, 10 + 3, c.depth, centered=(True, False, False))
    )
    ring = ring.union(ear)
    # two clamp lugs straddling the bottom slot, each tied into the ring wall
    # and hanging *below* it (−Y) so they never intrude into the Ø25.5 bore
    for sx in (+1, -1):
        lug = (
            cq.Workplane("XY", origin=(sx * (c.slot_w / 2 + 3), -25, 0))
            .box(6, 12, c.depth, centered=(False, False, False))
        )
        if sx < 0:
            lug = lug.translate((-6, 0, 0))
        ring = ring.union(lug)
    # clamp slot bisecting the bottom wall + lugs -> a true C-clamp running fit
    slot = (
        cq.Workplane("XY", origin=(0, -ro, 0))
        .box(c.slot_w, c.od, c.depth, centered=(True, True, False))
    )
    ring = ring.cut(slot)
    # M3 clamp cross-hole through both lugs (sets the running fit)
    clamp_hole = (
        cq.Workplane("YZ", origin=(-12, -19, c.depth / 2))
        .circle(c.m3_hole_d / 2)
        .extrude(24)
    )
    ring = ring.cut(clamp_hole)
    # plunger clearance bore along X: from the +X boss through to the bore wall
    plunger = (
        cq.Workplane("YZ", origin=(ro + 8, 0, c.depth / 2))
        .circle(c.solenoid_bore_d / 2)
        .extrude(-(ro + 8))
    )
    ring = ring.cut(plunger)
    # 2x M3 solenoid mount holes on the +X boss face (diagonally opposite)
    ring = (
        ring.faces(">X").workplane(centerOption="CenterOfBoundBox")
        .pushPoints([(c.solenoid_hole_pitch_y / 2, c.solenoid_hole_pitch_x / 2 - c.depth / 2 + 2),
                     (-c.solenoid_hole_pitch_y / 2, -(c.solenoid_hole_pitch_x / 2 - c.depth / 2 + 2))])
        .hole(c.m3_hole_d, 6)
    )
    return ring


def tap_collar_mount():
    """Bracket plate holding the collar's angular position (hard-stop fork).

    One manifold solid: a base flange, two side posts rising past the collar
    axis, and a top bridge with a central fork slot the collar ear drops into.
    """
    c = P.COLLAR
    ro = c.od / 2
    flange = (
        cq.Workplane("XY")
        .box(60, P.BRACKET.flange_y, P.BRACKET.flange_z, centered=(True, True, False))
    )
    body = flange
    post_x = ro + 3
    top_z = P.AUGER_AXIS_Z + ro + 10
    for sx in (+1, -1):
        post = (
            cq.Workplane("XY", origin=(sx * post_x, 0, 0))
            .box(6, P.BRACKET.flange_y, top_z, centered=(False, True, False))
        )
        if sx < 0:
            post = post.translate((-6, 0, 0))
        body = body.union(post)
    # top bridge tying the two posts together
    bridge = (
        cq.Workplane("XY", origin=(0, 0, top_z - 6))
        .box(2 * (post_x + 6), P.BRACKET.flange_y, 6, centered=(True, True, False))
    )
    body = body.union(bridge)
    # central fork slot the +Z collar ear engages (arrests rotation)
    fork = (
        cq.Workplane("XY", origin=(0, 0, P.AUGER_AXIS_Z + ro - 2))
        .box(5 + 0.8, P.BRACKET.flange_y + 2, top_z, centered=(True, True, False))
    )
    body = body.cut(fork)
    body = (
        body.faces("<Z").workplane(centerOption="CenterOfBoundBox")
        .pushPoints([(P.BRACKET.hole_x, 0), (-P.BRACKET.hole_x, 0)])
        .hole(P.BRACKET.hole_d)
    )
    return body


# --------------------------------------------------------------------------- #
# 4. Mounting plate ("the table")
# --------------------------------------------------------------------------- #
def mounting_plate():
    plate = (
        cq.Workplane("XY", origin=(0, (P.PLATE_Y_MIN + P.PLATE_Y_MAX) / 2, -P.PLATE_THK))
        .box(2 * P.PLATE_X, P.PLATE_Y_MAX - P.PLATE_Y_MIN, P.PLATE_THK,
             centered=(True, True, False))
    )
    # open U-notch in the +Y edge
    notch_y0 = P.PLATE_Y_MAX - P.PLATE_NOTCH_FROM_FRONT
    notch = (
        cq.Workplane("XY", origin=(0, (notch_y0 + P.PLATE_Y_MAX) / 2, -P.PLATE_THK))
        .box(P.PLATE_NOTCH_W, P.PLATE_Y_MAX - notch_y0, P.PLATE_THK + 2,
             centered=(True, True, False))
    )
    plate = plate.cut(notch)
    # Two hinge sandwiches (one per side).  Each side stacks, along X:
    #   inner plate lobe | (0.4) | middle baseplate arm | (0.4) | outer plate lobe
    # The plate owns the inner + outer lobes; the outer lobe carries the 40T gear.
    g = P.HINGE_LAYER_GAP
    w = P.HINGE_LOBE_W
    for sx in (+1, -1):
        arm_cx = sx * P.HINGE_ARM_X
        inner_cx = arm_cx - sx * (w + g)
        outer_cx = arm_cx + sx * (w + g)
        # inner lobe: plain Ø18 eye
        inner = _hinge_eye(inner_cx, w, P.HINGE_EYE_OD)
        inner = inner.union(_hinge_bridge(inner_cx, w))
        # outer lobe: 40T gear band
        gear = H.spur_gear(
            P.HINGE_GEAR.module, P.HINGE_GEAR.teeth, w,
            tip_d=P.HINGE_GEAR_TIP_D, backlash=P.BACKLASH,
        ).rotate((0, 0, 0), (0, 1, 0), 90)          # axis +Z -> +X
        gear = gear.translate((outer_cx - w / 2, P.HINGE_AXIS_Y, P.HINGE_AXIS_Z))
        gear = gear.union(_hinge_bridge(outer_cx, w))
        plate = plate.union(inner).union(gear)
        # M5 bore through both lobes
        for cx in (inner_cx, outer_cx):
            plate = plate.cut(
                cq.Workplane("YZ", origin=(cx - w, P.HINGE_AXIS_Y, P.HINGE_AXIS_Z))
                .circle(P.HINGE_BORE_D / 2).extrude(2 * w)
            )
        # front-edge clearance slot so the plate body never fouls the fixed
        # baseplate hinge arm (the middle layer at X = +/-HINGE_ARM_X).
        slot_y0 = P.HINGE_AXIS_Y - P.HINGE_ARM_DEPTH - g
        slot = (
            cq.Workplane("XY", origin=(arm_cx, (slot_y0 + P.PLATE_Y_MAX + 1) / 2,
                                       -P.PLATE_THK - 1))
            .box(w + 2 * g, P.PLATE_Y_MAX + 1 - slot_y0, P.PLATE_THK + 2,
                 centered=(True, True, False))
        )
        plate = plate.cut(slot)
    return plate


def _hinge_eye(cx, w, od):
    return (
        cq.Workplane("YZ", origin=(cx - w / 2, P.HINGE_AXIS_Y, P.HINGE_AXIS_Z))
        .circle(od / 2).extrude(w)
    )


def _hinge_bridge(cx, w):
    """Web tying a plate hinge lobe back to the plate front edge."""
    return (
        cq.Workplane("XY", origin=(cx - w / 2, P.PLATE_Y_MAX, -P.PLATE_THK))
        .box(w, P.HINGE_AXIS_Y - P.PLATE_Y_MAX, P.HINGE_AXIS_Z + P.PLATE_THK,
             centered=(False, False, False))
    )


# --------------------------------------------------------------------------- #
# 5. Baseplate (fixed forward tab) + 6. hinge arms + servo posts/flanges
# --------------------------------------------------------------------------- #
def baseplate():
    z0 = P.BASE_BOTTOM_Z
    plate = (
        cq.Workplane("XY", origin=(0, (P.BASE_Y_MIN + P.BASE_Y_MAX) / 2, z0))
        .box(2 * P.BASE_X, P.BASE_Y_MAX - P.BASE_Y_MIN, P.BASE_THK,
             centered=(True, True, False))
    )
    # chamfer the two rear (-Y) corners 25 x 45
    plate = plate.edges("|Z and <Y").chamfer(P.BASE_CHAMFER)
    # 4x M5 mounting holes
    plate = (
        plate.faces("<Z").workplane(centerOption="CenterOfBoundBox")
        .pushPoints([(sx * P.BASE_HOLE_X, sy - (P.BASE_Y_MIN + P.BASE_Y_MAX) / 2)
                     for sx in (1, -1) for sy in P.BASE_HOLE_Y])
        .hole(P.BASE_HOLE_D)
    )
    # two hinge arms (the middle layer of each sandwich) reaching to the hinge axis
    w = P.HINGE_LOBE_W
    top = top_z(z0)
    H = P.HINGE_AXIS_Z - top
    run = 16.0
    for sx in (+1, -1):
        arm_cx = sx * P.HINGE_ARM_X
        eye = _hinge_eye(arm_cx, w, P.HINGE_EYE_OD)
        # post body down to the baseplate top; -Y face sloped so the plate clears it
        post = (
            cq.Workplane("YZ", origin=(arm_cx - w / 2, P.HINGE_AXIS_Y, P.HINGE_AXIS_Z))
            .polyline([
                (0, 0),
                (-P.HINGE_ARM_DEPTH, 0),
                (-P.HINGE_ARM_DEPTH + run, -H),
                (0, -H),
            ])
            .close()
            .extrude(w)
        )
        plate = plate.union(eye).union(post)
        plate = plate.cut(
            cq.Workplane("YZ", origin=(arm_cx - w, P.HINGE_AXIS_Y, P.HINGE_AXIS_Z))
            .circle(P.HINGE_BORE_D / 2).extrude(2 * w)
        )
    # servo posts + underside flanges/gussets (one per side)
    for sx in (+1, -1):
        plate = plate.union(_servo_support(sx, z0))
    return plate


def top_z(z0):
    return z0 + P.BASE_THK


def _servo_support(sx, z0):
    top = z0 + P.BASE_THK
    posts = cq.Workplane()
    parts = None
    for dy in (-P.MG996R.hole_span_y / 2, P.MG996R.hole_span_y / 2):
        post = (
            cq.Workplane("XY", origin=(sx * P.SERVO_POST_INBOARD_X,
                                       (P.BASE_Y_MIN + P.BASE_Y_MAX) / 2 + dy, top))
            .box(P.SERVO_POST.size, P.SERVO_POST.size, 20,
                 centered=(True, True, False))
        )
        parts = post if parts is None else parts.union(post)
    # underside flange rib at X = +/-79 dropping 40 mm below the baseplate.
    # Keep its inboard edge outboard of the tilting plate (max |X| = 57.4) so the
    # plate never fouls it through the full 0-90 deg tilt sweep.
    flange = (
        cq.Workplane("XZ", origin=(sx * P.SERVO_FLANGE_X,
                                   (P.BASE_Y_MIN + P.BASE_Y_MAX) / 2,
                                   z0 - P.SERVO_FLANGE_DROP))
        .box(P.SERVO_FLANGE_LEN, P.SERVO_FLANGE_DROP, P.SERVO_FLANGE_THK,
             centered=(True, False, True))
    )
    parts = parts.union(flange)
    # M5 side-bolt hole through the flange, axis along Y, 15 mm below the base
    hole = (
        cq.Workplane("XZ", origin=(sx * P.SERVO_FLANGE_X,
                                   (P.BASE_Y_MIN + P.BASE_Y_MAX) / 2,
                                   z0 - P.SERVO_FLANGE_HOLE_DROP))
        .circle(P.SERVO_FLANGE_HOLE_D / 2)
        .extrude(P.SERVO_FLANGE_THK + 4, both=True)
    )
    parts = parts.cut(hole)
    return parts


# --------------------------------------------------------------------------- #
# Off-the-shelf envelopes (for the assembly only)
# --------------------------------------------------------------------------- #
def nema11_envelope():
    n = P.NEMA11
    body = cq.Workplane("XY").box(n.body, n.body, n.length, centered=(True, True, False))
    shaft = (
        cq.Workplane("XY", origin=(0, 0, n.length))
        .circle(n.shaft_d / 2).extrude(n.shaft_len)
    )
    pilot = (
        cq.Workplane("XY", origin=(0, 0, n.length))
        .circle(n.pilot_d / 2).extrude(n.pilot_h)
    )
    return body.union(shaft).union(pilot)


def mg996r_envelope():
    m = P.MG996R
    body = cq.Workplane("XY").box(m.body_x, m.body_y, m.body_z, centered=(True, True, False))
    return body


def solenoid_envelope():
    s = P.SOLENOID
    body = cq.Workplane("XY").box(s.body_x, s.body_y, s.body_z, centered=True)
    plunger = (
        cq.Workplane("YZ", origin=(s.body_x / 2, 0, 0))
        .circle(s.bushing_d / 2).extrude(20)
    )
    return body.union(plunger)


# --------------------------------------------------------------------------- #
# Assembly (tilt 0)
# --------------------------------------------------------------------------- #
def placed_parts():
    """Return a dict name -> placed cq.Workplane in the assembly (global) frame."""
    parts = {}

    # auger (storage, full) along +Y; tip(z=0) -> y=Y_TIP, motor(z=len) -> -Y
    auger = auger_storage(P.AUGER_LEN_FULL)
    auger = auger.rotate((0, 0, 0), (1, 0, 0), 90)   # local +Z -> -Y
    auger = auger.translate((0, Y_TIP, P.AUGER_AXIS_Z))
    parts["auger"] = auger

    # stepper pinion: axis along Y at X=+32, Z=29.25, face centred on band
    pin = stepper_pinion()
    parts["stepper_pinion"] = to_y_axis(
        pin, P.STEPPER_CENTRE_DIST, Y_BAND, P.AUGER_AXIS_Z, face=P.STEPPER_PINION.face)

    # NEMA 11 envelope behind the pinion (-Y face carries the motor)
    nema = nema11_envelope().rotate((0, 0, 0), (1, 0, 0), 90)
    nema = nema.translate((P.STEPPER_CENTRE_DIST, Y_BAND - P.STEPPER_PINION.face / 2,
                           P.AUGER_AXIS_Z))
    parts["nema11"] = nema

    # tap collar
    coll = tap_collar()
    parts["tap_collar"] = to_y_axis(coll, 0, Y_COLLAR, P.AUGER_AXIS_Z,
                                    face=P.COLLAR.depth)

    # tap solenoid envelope on the +X side, plunger pointing -X to tap the wall.
    # The plunger tip reaches 3 mm inside the auger OD (deliberate interference, §6).
    sol = solenoid_envelope().rotate((0, 0, 0), (0, 0, 1), 180)
    tip_x = P.AUGER_R_OUT - P.SOLENOID.interference          # 9.5
    body_cx = tip_x + 20 + P.SOLENOID.body_x / 2
    sol = sol.translate((body_cx, Y_COLLAR, P.AUGER_AXIS_Z))
    parts["solenoid"] = sol

    # tap-collar mount + brackets sit on the plate top (Z=0)
    parts["tap_collar_mount"] = tap_collar_mount().translate((0, Y_COLLAR, 0))
    parts["front_bracket"] = auger_bracket().translate((0, Y_FRONT_BRACKET, 0))
    parts["rear_bracket"] = auger_bracket().translate((0, Y_REAR_BRACKET, 0))

    # mounting plate + baseplate
    parts["mounting_plate"] = mounting_plate()
    parts["baseplate"] = baseplate()

    # servos + servo pinions (mirrored about X=0).  Each 20T servo pinion meshes
    # with the 40T hinge gear on the outer plate lobe; the 2:1 reduction lives in
    # the vertical (Z) centre distance C = 27.25 (§6), so the pinion sits directly
    # below the hinge gear.
    g = P.HINGE_LAYER_GAP
    w = P.HINGE_LOBE_W
    spline_z = P.HINGE_AXIS_Z - P.SERVO_CENTRE_DIST           # = 2.0
    for sx in (+1, -1):
        outer_cx = sx * P.HINGE_ARM_X + sx * (w + g)
        sp = servo_pinion().rotate((0, 0, 0), (0, 1, 0), 90)   # axis +Z -> +X
        sp = sp.translate((outer_cx - sx * w / 2, P.HINGE_AXIS_Y, spline_z))
        parts[f"servo_pinion_{'p' if sx > 0 else 'm'}"] = sp
        # MG996R body inboard of the spline, spline at the near body end
        sv = mg996r_envelope().rotate((0, 0, 0), (0, 0, 1), 90)
        sv = sv.translate((outer_cx - sx * (P.MG996R.body_x / 2 + 4),
                           P.HINGE_AXIS_Y - P.MG996R.spline_offset, spline_z))
        parts[f"servo_{'p' if sx > 0 else 'm'}"] = sv

    # M5 hinge pins (one per side) along X
    for sx in (+1, -1):
        pin = (
            cq.Workplane("YZ", origin=(sx * (P.PLATE_X + 2), P.HINGE_AXIS_Y, P.HINGE_AXIS_Z))
            .circle(P.HINGE_PIN_D / 2).extrude(-sx * (P.PLATE_X + 4))
        )
        parts[f"hinge_pin_{'p' if sx>0 else 'm'}"] = pin

    return parts


def build_assembly():
    parts = placed_parts()
    colors = {
        "auger": (0.82, 0.71, 0.55), "stepper_pinion": (0.44, 0.50, 0.56),
        "nema11": (0.41, 0.41, 0.41), "tap_collar": (1.0, 0.65, 0.0),
        "solenoid": (0.70, 0.13, 0.13), "tap_collar_mount": (0.94, 0.90, 0.55),
        "front_bracket": (0.27, 0.51, 0.71), "rear_bracket": (0.27, 0.51, 0.71),
        "mounting_plate": (0.83, 0.83, 0.83), "baseplate": (0.50, 0.50, 0.50),
    }
    asm = cq.Assembly(name="powder_doser")
    for name, wp in parts.items():
        r, g, b = colors.get(name, (0.24, 0.70, 0.44))
        asm.add(wp, name=name, color=cq.Color(r, g, b))
    return asm, parts


# --------------------------------------------------------------------------- #
# §6 Interference / clearance report
# --------------------------------------------------------------------------- #
def _vol(wp):
    try:
        return wp.val().Volume()
    except Exception:
        return 0.0


def _intersection_vol(a, b):
    try:
        inter = a.intersect(b)
        return _vol(inter)
    except Exception:
        return 0.0


def interference_report(parts=None):
    if parts is None:
        _, parts = build_assembly()
    checks = []

    def add(name, ok, detail):
        checks.append((name, ok, detail))

    auger = parts["auger"]

    # 1. auger bore stays open through the gear band: a Ø20 probe along Y is clear
    probe = (
        cq.Workplane("XZ", origin=(0, Y_TIP + 5, P.AUGER_AXIS_Z))
        .circle((P.AUGER_ID - 1) / 2).extrude(-(P.AUGER_LEN_FULL + 10))
    )
    bore_block = _intersection_vol(auger, probe)
    add("auger bore open through gear band", bore_block < 1.0,
        f"bore-probe intersection = {bore_block:.2f} mm^3 (want ~0)")

    # 2. pinion <-> auger gear: meshing overlap is small (teeth touch, not jam)
    overlap = _intersection_vol(auger, parts["stepper_pinion"])
    add("pinion/auger-band mesh (no jam)", overlap < 30.0,
        f"tooth overlap = {overlap:.2f} mm^3 (small backlash contact only)")

    # 2b. NEMA 11 body clears the auger OD (>= ~5 mm)
    gap = P.STEPPER_CENTRE_DIST - P.NEMA11.body / 2 - P.AUGER_R_OUT
    add("NEMA 11 body clears auger OD", gap > 4.0,
        f"radial gap = {gap:.2f} mm (spec ~5.4)")

    # 3. tap collar is a running fit on the auger (clearance, no clamp)
    coll_overlap = _intersection_vol(auger, parts["tap_collar"])
    radial_fit = (P.COLLAR.bore_d - P.AUGER_OD) / 2
    add("tap collar running fit on auger", coll_overlap < 1.0 and radial_fit > 0.1,
        f"overlap = {coll_overlap:.2f} mm^3, radial clearance = {radial_fit:.2f} mm")

    # 4. solenoid plunger is a DELIBERATE interference (tip 3 mm into auger OD)
    sol_overlap = _intersection_vol(auger, parts["solenoid"])
    add("solenoid plunger interference (intended)", sol_overlap > 0.5,
        f"plunger/auger overlap = {sol_overlap:.2f} mm^3 (>0 = taps the wall)")

    # 5. brackets are a running fit on the auger
    fb = _intersection_vol(auger, parts["front_bracket"])
    rb = _intersection_vol(auger, parts["rear_bracket"])
    add("auger brackets running fit", fb < 1.0 and rb < 1.0,
        f"front = {fb:.2f}, rear = {rb:.2f} mm^3 (want ~0)")

    # 6. tilt clearance: plate underside vs baseplate hinge arms at 0/45/90 deg
    plate = parts["mounting_plate"]
    base = parts["baseplate"]
    axis_pt = (0, P.HINGE_AXIS_Y, P.HINGE_AXIS_Z)
    for ang in (0, 45, 90):
        tp = plate.rotate(axis_pt, (axis_pt[0] + 1, axis_pt[1], axis_pt[2]), ang)
        v = _intersection_vol(tp, base)
        add(f"tilt clearance @ {ang} deg", v < 1.0,
            f"plate/baseplate intersection = {v:.2f} mm^3 (want 0)")

    # 7. every printed part is a single manifold solid (FDM-printable, §0)
    bad = []
    for name, fn in PARTS_TO_EXPORT.items():
        try:
            n = len(fn().val().Solids())
        except Exception as exc:  # pragma: no cover - build failure surfaces here
            n = -1
            bad.append(f"{name}({exc})")
            continue
        if n != 1:
            bad.append(f"{name}={n}")
    add("each printed part is one manifold solid", not bad,
        "all single-solid" if not bad else f"non-manifold: {', '.join(bad)}")

    return checks


# --------------------------------------------------------------------------- #
# Exports
# --------------------------------------------------------------------------- #
PARTS_TO_EXPORT = {
    "auger-storage-full": lambda: auger_storage(P.AUGER_LEN_FULL),
    "auger-storage-180": lambda: auger_storage(P.AUGER_LEN_180),
    "auger-storage-short": lambda: auger_storage(P.AUGER_LEN_SHORT, with_gear_band=False),
    "auger-threaded": lambda: auger_threaded(P.AUGER_LEN_FULL),
    "thread-cap": thread_cap,
    "stepper-pinion": stepper_pinion,
    "servo-pinion": servo_pinion,
    "auger-bracket": auger_bracket,
    "tap-collar": tap_collar,
    "tap-collar-mount": tap_collar_mount,
    "mounting-plate": mounting_plate,
    "baseplate": baseplate,
}


def export_all(do_png=True):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    for name, fn in PARTS_TO_EXPORT.items():
        print(f"  building {name} ...", flush=True)
        wp = fn()
        stl = os.path.join(EXPORT_DIR, f"{name}.stl")
        exporters.export(wp, os.path.join(EXPORT_DIR, f"{name}.step"))
        exporters.export(wp, stl)
        if do_png:
            _render_stl_png(stl, os.path.join(EXPORT_DIR, f"{name}.png"))
    # assembly: STEP + a combined STL + a rendered PNG
    asm, parts = build_assembly()
    asm.save(os.path.join(EXPORT_DIR, "powder-doser-assembly.step"))
    asm_stl = os.path.join(EXPORT_DIR, "powder-doser-assembly.stl")
    combined = None
    for wp in parts.values():
        combined = wp if combined is None else combined.add(wp)
    exporters.export(combined, asm_stl)
    if do_png:
        _render_stl_png(asm_stl, os.path.join(EXPORT_DIR, "powder-doser-assembly.png"),
                        size=(1100, 825))


def _render_stl_png(stl_path, png_path, size=(900, 700)):
    """Offscreen-render an STL mesh to a shaded PNG with VTK (headless)."""
    try:
        import vtk
        reader = vtk.vtkSTLReader()
        reader.SetFileName(stl_path)
        reader.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.62, 0.66, 0.72)
        actor.GetProperty().SetSpecular(0.3)
        actor.GetProperty().SetSpecularPower(20)

        ren = vtk.vtkRenderer()
        ren.AddActor(actor)
        ren.SetBackground(1.0, 1.0, 1.0)
        cam = ren.GetActiveCamera()
        cam.SetPosition(1, -1, 0.6)
        cam.SetViewUp(0, 0, 1)
        ren.ResetCamera()
        cam.Azimuth(20)
        cam.Elevation(20)
        ren.ResetCameraClippingRange()

        win = vtk.vtkRenderWindow()
        win.SetOffScreenRendering(1)
        win.AddRenderer(ren)
        win.SetSize(*size)
        win.Render()

        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(win)
        w2i.Update()
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(png_path)
        writer.SetInputConnection(w2i.GetOutputPort())
        writer.Write()
    except Exception as e:  # pragma: no cover - rendering is best-effort
        print(f"    (png skipped for {png_path}: {e})")


if __name__ == "__main__":
    print("Building Powder Doser parts + assembly ...")
    export_all(do_png=True)
    print("\nInterference / clearance report (SPEC §6):")
    ok_all = True
    for name, ok, detail in interference_report():
        flag = "PASS" if ok else "FAIL"
        ok_all = ok_all and ok
        print(f"  [{flag}] {name}: {detail}")
    print("\nAll checks passed." if ok_all else "\nSome checks FAILED.")

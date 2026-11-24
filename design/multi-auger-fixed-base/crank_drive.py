"""L6: a short linear actuator above the shelf on a crank at each hinge, so nothing hangs under it (issue #204, 23 Nov).

The new balance (new_scale.py) is a box about 183 x 240 mm and 320 mm tall, with sliding side doors.  Any
layout that hangs the P16s under the shelf puts an actuator beside or behind it (new_scale.py), so a side door
can't slide back or be reached through.  L5 (leg_room.py) solved that with a gearmotor on each hinge axis.
L6 keeps a linear actuator instead:

  * an 8 mm shaft through the module's +X knuckle and hinge tower, keyed to the knuckle, in place of the M5
    hinge screw (as L5's);
  * a crank on the shaft's outer end (x = 67.5-73.5 mm), beside the module, 33 mm from the hinge axis to its pin.  At 0 deg it
    points 45 deg down and back; at 90 deg, 45 deg up and back;
  * an Actuonix P16-50 (50 mm stroke) hanging from a pivot 130 mm above the hinge axis, pulling the crank pin
    up as the module tilts.  It holds its position with the power off, like the P16-150;
  * the pivot is the P16's own U-bracket, under an arm on a post that stands on a small ear added to the
    shelf beside the module.

Beside each module's +X side, past x = 64 mm and behind the hinge line (the module's own parts reach x = 63.6), nothing of the module itself, its
neighbour or the base passes at any tilt (probed 23 Nov), which is where all of this goes.  Under the shelf
there is then nothing but the legs.

    python crank_drive.py       # kinematics, clearance checks over 0-90 deg, the base with ears; crank_drive.json (1 min)
                                # (renders/crank_drive.png is drawn by new_scale_figs.py)

Frames as in doserlib.py: the unit frame of a module has its hinge axis on x, +y behind the hinge, z up,
hinge at z = 0; the station frame has the beaker axis on z, modules at bearings 90, 210 and 330 deg.  The
crank, pin, post, arm and ear are placeholders.  The P16-50's closed length is taken as 105 mm hole to hole
(open 155 mm), as RobotShop lists the P16-50-22-12-P; the stroke + 47 mm rule the P16-100 and P16-150 follow
would give 97 mm.  Check it against Actuonix's drawing: if it is 97 mm, lower the pivot by 8 mm.
Forces: the P16 and T16 share their gearboxes; Actuonix's T16 datasheet gives, for 22:1 / 64:1, a peak power
point of 40 N / 80 N, a maximum force of 50 N / 90 N and a back-drive force of 75 N / 200 N.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

import doserlib as D
import components as K
import mounts as MT
import leg_room as LR
import stands as ST
import base as B

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
SP = LR.SP
TOP, BOT = B.TOP, B.BOT                    # shelf top / underside, unit frame (-37.25 / -43.25)
TILTS = tuple(range(0, 91, 5))
GAP = 2.0

CR = dict(R=33.0, beta0=-45.0, x=(67.5, 73.5), hub_r=8.0, arm_w=14.0)          # crank on the +X shaft end
ACT = dict(name="P16-50", closed=105.0, stroke=50.0, x=79.0, pivot=(28.0, 130.0))  # actuator plane x; pivot (y, z)
SHAFT = dict(r=4.0, x=(20.0, 75.0))
PIN = dict(r=2.0, x=(67.5, 83.0), nut_r=3.9, nut_x=(83.0, 86.2))
SUP = dict(x=(69.0, 89.0), post_y=(62.0, 78.0), arm_t=8.0, arm_y0=16.0, ear_x=(40.0, 95.0), ear_y=(46.0, 94.0))
TORQUE = MT.TORQUE                          # 0.65 N m at the hinge, the upper estimate


# --------------------------------------------------------------------------- #
# kinematics
# --------------------------------------------------------------------------- #
def crank_pin(t):
    """(y, z) of the crank pin at tilt t (unit frame)."""
    b = math.radians(CR["beta0"] + t)
    return np.array([CR["R"] * math.cos(b), CR["R"] * math.sin(b)])


def kinematics(tilts=np.arange(0.0, 90.001, 0.5)):
    Pv = np.array(ACT["pivot"])
    L = np.array([np.linalg.norm(crank_pin(t) - Pv) for t in tilts])
    lever = np.abs(np.gradient(L, np.radians(tilts)))          # mm of stroke per radian of tilt
    i = int(np.argmin(lever))
    out = dict(actuator=ACT["name"], closed=ACT["closed"], stroke=ACT["stroke"],
               crank_radius=CR["R"], pivot_yz=list(ACT["pivot"]),
               length_at={f"{t:g}": round(float(L[int(t * 2)]), 1) for t in (0, 30, 45, 60, 90)},
               rod_out={f"{t:g}": round(float(L[int(t * 2)] - ACT["closed"]), 1) for t in (0, 30, 45, 60, 90)},
               spare_retracted=round(float(L.min() - ACT["closed"]), 1),
               spare_extended=round(float(ACT["closed"] + ACT["stroke"] - L.max()), 1),
               stroke_used=round(float(L.max() - L.min()), 1),
               monotonic=bool(np.all(np.diff(L) < 0)),
               mm_per_deg=[round(float(lever.min()) * math.pi / 180, 2), round(float(lever.max()) * math.pi / 180, 2)],
               max_force_N=round(TORQUE / float(lever.min()), 1), max_force_at_tilt=float(tilts[i]),
               swing_deg=[round(math.degrees(math.atan2(float(crank_pin(t)[0] - Pv[0]), float(Pv[1] - crank_pin(t)[1]))), 1)
                          for t in (0, 45, 90)])
    return out


# --------------------------------------------------------------------------- #
# geometry (unit frame of the module; +X side)
# --------------------------------------------------------------------------- #
_S: dict = {}


def crank_shape():
    """Hub on the shaft and an arm to the pin, drawn at tilt 0 (it turns with the plate)."""
    if "crank" not in _S:
        x0, x1 = CR["x"]
        hub = D.cyl(CR["hub_r"], x1 - x0, x0, 0, 0, d=(1, 0, 0))
        b = math.radians(CR["beta0"])
        w = CR["arm_w"] / 2
        arm = D.box(x0, x1, 0.0, CR["R"], -w, w)
        import cadquery as cq
        arm = arm.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), math.degrees(b))
        py, pz = crank_pin(0.0)
        end = D.cyl(w, x1 - x0, x0, py, pz, d=(1, 0, 0))
        hole = D.cyl(SHAFT["r"], 30, x0 - 5, 0, 0, d=(1, 0, 0))
        _S["crank"] = hub.fuse(arm).fuse(end).cut(hole).clean()
    return _S["crank"]


def pin_shape():
    if "pin" not in _S:
        py, pz = crank_pin(0.0)
        sh = D.cyl(PIN["r"], PIN["x"][1] - PIN["x"][0], PIN["x"][0], py, pz, d=(1, 0, 0))
        nut = D.cyl(PIN["nut_r"], PIN["nut_x"][1] - PIN["nut_x"][0], PIN["nut_x"][0], py, pz, d=(1, 0, 0))
        _S["pin"] = sh.fuse(nut).clean()
    return _S["pin"]


def shaft_shape():
    if "shaft" not in _S:
        _S["shaft"] = D.cyl(SHAFT["r"], SHAFT["x"][1] - SHAFT["x"][0], SHAFT["x"][0], 0, 0, d=(1, 0, 0))
    return _S["shaft"]


def support_shapes():
    """Post, arm (the U-bracket screws under it) and the ear on the shelf the post stands on."""
    if "sup" not in _S:
        x0, x1 = SUP["x"]
        py, pz = ACT["pivot"]
        top = pz + K.UB["h"]                                  # the U-bracket's base, flipped, sits under the arm
        arm = D.box(x0, x1, py - SUP["arm_y0"] + 4.0, SUP["post_y"][1], top, top + SUP["arm_t"])
        post = D.box(x0, x1, SUP["post_y"][0], SUP["post_y"][1], TOP, top + SUP["arm_t"])
        ear = D.box(SUP["ear_x"][0], SUP["ear_x"][1], SUP["ear_y"][0], SUP["ear_y"][1], BOT, TOP)
        _S["sup"] = dict(post=post.fuse(arm).clean(), ear=ear.clean())
    return _S["sup"]


def act_frame(Mst, tilt):
    """Actuator frame (MT.p16's): base pin at the pivot, z towards the crank pin, pins along x, housing out (+y)."""
    x = ACT["x"]
    py, pz = ACT["pivot"]
    cy, cz = crank_pin(tilt)
    Pp = (Mst @ np.array([x, cy, cz, 1.0]))[:3]
    Bw = (Mst @ np.array([x, py, pz, 1.0]))[:3]
    L_ = float(np.linalg.norm(Pp - Bw))
    wv = (Pp - Bw) / L_
    ax = -Mst[:3, 0] - wv * (-Mst[:3, 0] @ wv)
    ax /= np.linalg.norm(ax)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = ax, np.cross(wv, ax), wv, Bw
    return M, L_


def drive_parts(tilt, Mst, tag):
    """L6's parts for one module at ``tilt``: shaft, crank, pin (turn with the plate), the P16-50 and its
    U-bracket, the post with its arm, and the ear (fixed)."""
    out = []
    Mt = Mst @ D.Rx(float(tilt))
    out.append(D.Part(f"{tag}:drive shaft", shaft_shape(), Mt, (0.55, 0.56, 0.58), tag, True))
    out.append(D.Part(f"{tag}:crank", crank_shape(), Mt, K.STATUS["new"][2], tag, True))
    out.append(D.Part(f"{tag}:crank pin", pin_shape(), Mt, K.STATUS["hw"][2], tag, True))
    Ma, L_ = act_frame(Mst, tilt)
    body, rod = MT.p16(L_, ACT["closed"])
    out.append(D.Part(f"{tag}:P16-50 body", body, Ma, K.STATUS["buy"][2], tag, False))
    out.append(D.Part(f"{tag}:P16-50 rod", rod, Ma, (0.80, 0.81, 0.84), tag, True))
    if "ub" not in _S:
        _S["ub"] = K.u_bracket()
    py, pz = ACT["pivot"]
    Mu = Mst @ D.Tt(ACT["x"], py, pz) @ D.Rx(180.0)
    out.append(D.Part(f"{tag}:P16 bracket", _S["ub"], Mu, K.STATUS["buy"][2], tag, False))
    sp = support_shapes()
    out.append(D.Part(f"{tag}:post and arm", sp["post"], Mst, K.STATUS["new"][2], tag, False))
    out.append(D.Part(f"{tag}:ear", sp["ear"], Mst, K.STATUS["new"][2], tag, False))
    for p in out:
        p.kind = "drive"
    return out


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def checks(step=10):
    """A's drive at every tilt of A against: A's own parts (except the plate the shaft is keyed into, and the
    ear under the plate's floor is checked against the plate too); C (the neighbour its +X side faces) at
    every tilt of C; B; and the base (towers, shelf), except the shaft (in the tower's bore) and the post
    and ear (fixed to the shelf)."""
    MA, MB_, MC = D.place(90.0, SP, 0.0), D.place(210.0, SP, 0.0), D.place(330.0, SP, 0.0)
    tilts = tuple(range(0, 91, step))
    res = {}
    w = (1e9, None, None, None)
    for t in tilts:
        dp = ST._objs(drive_parts(t, MA, "A"))
        for p, op in ST._objs(LR.module_parts("L5", t, MA, "A")):
            for q, oq in dp:
                if q.name == "A:drive shaft" and p.name.endswith("Mounting plate"):
                    continue                      # keyed into the +X knuckle
                d = ST._dist(op, oq)
                if d < w[0]:
                    w = (d, p.name, q.name, t)
    res["own_module"] = dict(mm=round(w[0], 2), between=f"{w[1]} / {w[2]}", at_tilt=w[3])
    for who, M, u in (("neighbour C (its +X side faces it)", MC, "C"), ("neighbour B", MB_, "B")):
        w = (1e9, None, None, None, None)
        cache = {tc: ST._objs(LR.module_parts("L5", tc, M, u)) for tc in tilts}
        for ta in tilts:
            dp = ST._objs(drive_parts(ta, MA, "A"))
            for tc in tilts:
                for p, op in cache[tc]:
                    for q, oq in dp:
                        d = ST._dist(op, oq)
                        if d < w[0]:
                            w = (d, p.name, q.name, ta, tc)
        res[who] = dict(mm=round(w[0], 2), between=f"{w[1]} / {w[2]}", tilt_A=w[3], tilt_other=w[4])
    base = D.Part("base", LR.base_for("L5"), np.eye(4), (0.6, 0.6, 0.6))
    bo = ST._objs([base])[0][1]
    w = (1e9, None, None)
    for t in tilts:
        for q, oq in ST._objs(drive_parts(t, MA, "A")):
            if q.name in ("A:drive shaft", "A:post and arm", "A:ear"):
                continue
            d = ST._dist(oq, bo)
            if d < w[0]:
                w = (d, q.name, t)
    res["base"] = dict(mm=round(w[0], 2), part=w[1], at_tilt=w[2])
    # C's own drive against A (C's drive sits in the C-B gap; A is on C's -X side): by symmetry it is B's drive
    # against A, the same as A's drive against C, so it is not repeated.
    return res


def base_with_ears():
    """The one-piece base (no slots, as L5's) with the three ears: its box, and whether it fits one H2D nozzle."""
    import cadquery as cq
    shp = LR.base_for("L5")
    ear = support_shapes()["ear"]
    for th in LR.BEARINGS:
        shp = shp.fuse(ear.moved(LR.C_loc(D.place(th, SP, 0.0))))
    bb = shp.BoundingBox()
    fits = []
    for rot in range(0, 180, 2):
        b2 = shp.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), rot).BoundingBox()
        a, c = sorted((b2.xlen, b2.ylen), reverse=True)
        if a <= B.BED[0] and c <= B.BED[1]:
            fits.append(rot)
    return dict(box=[round(bb.xlen, 1), round(bb.ylen, 1)], bed=list(B.BED), fits_h2d_at_0=bool(0 in fits),
                rotations_that_fit_deg=fits)


def main():
    t0 = time.time()
    LR.prepare()
    res = dict(kinematics=kinematics(), crank=CR, actuator=ACT, shaft=SHAFT, support=SUP)
    print(json.dumps(res["kinematics"], indent=1), flush=True)
    if "--no-checks" not in sys.argv:
        res["checks"] = checks(step=10 if "--fast" in sys.argv else 5)
        print(json.dumps(res["checks"], indent=1), round(time.time() - t0), "s", flush=True)
    # where the post and actuator sit in the station (module A)
    MA = D.place(90.0, SP, 0.0)
    pts = {}
    for nm, (x, y) in dict(pivot=(ACT["x"], ACT["pivot"][0]), post=(np.mean(SUP["x"]), np.mean(SUP["post_y"]))).items():
        p = MA @ np.array([x, y, 0.0, 1.0])
        pts[nm] = dict(r=round(float(math.hypot(p[0], p[1])), 1), bearing=round(math.degrees(math.atan2(p[1], p[0])) % 360, 1))
    res["station_positions_module_A"] = pts
    res["base_with_ears"] = base_with_ears()
    print("base with ears", res["base_with_ears"]["box"], res["base_with_ears"]["fits_h2d_at_0"], flush=True)
    if "--no-json" not in sys.argv:
        (HERE / "crank_drive.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()

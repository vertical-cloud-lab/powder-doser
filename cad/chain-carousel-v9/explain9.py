"""v9's clips (Sam, PR #185, 2026-11-17: "give another report, complete with gifs of changes and highlighting features"). One
clip per change and an overview; every frame is the v9 CAD (layout.placements) in the state described, moving by the model's
own kinematics (explain.py's Clip: the parts a step is about keep their colours, the rest is washed out, callouts name them).

    xvfb-run -a python explain9.py overview|drop|balance|ec|enclosure|tilt90 [--preview]
    -> renders/v9/<name>_v9.{mp4,gif}
"""
from __future__ import annotations

import math
import sys

import cadquery as cq
import numpy as np

import explain as E
import explain7 as X7
import layout as L
import parts7 as P7
import parts9 as P9
import render as R
import render_balance as RB
from params import (BEAKER_H, BAY9_DEPTH, D9, DOOR_TRAVEL, EC7_PIN, EC9_FRONT, KC7_A, KC7_TIP, MODULE_LINKS, PAN9_AHEAD, PARK_DROP7,
                    RUN_DIRECTION, SOL9_X, SOL_X, SOL_Z, BLOCK9)

E.OUT = R.OUT / "v9"
H = L.HINGE_STATION
D = L.DOSE_POINT
SY = L.STATION_Y
PAN = L.scale_pan_target()
part, sam, ec, world = E.part, E.sam, E.ec, E.world
wide = X7.wide
TAG = "chain carousel v9 · PR #185 · 2026-11-17"
S0 = dict(enclosure=False)
FPS = E.FPS
RIM = L.BEAKER9_RIM
Z_LAND = RIM - BEAKER_H + 6.0
SEE = ("panel_", "hatch_", "bay9_", "baffle9_", "deck9")
CAM_SIDE = ((70.0, SY, 385.0), (0.0, -1.0, 0.07), 560)          # the station, the beaker and the balance's top, side section from -y
CAM_SIDE90 = ((120.0, SY, 430.0), (0.0, -1.0, 0.05), 860)        # ... with room for the module at 90 deg


def opac(pl, extra=None):
    o = {}
    for k, p in R.keyed(pl):
        if p.key == "beaker":
            o[k] = 0.35
        elif p.key.startswith(SEE):
            o[k] = 0.16
        if extra and p.key in extra:
            o[k] = extra[p.key]
    return o


def near_cut(p) -> bool:
    """v7's section from -y, plus the -y baffle and the bay's -y side (they stand between the camera and the station)."""
    if p.key in ("baffle9_side_m", "bay9_side_m", "bay9_front", "bay9_door"):
        return True
    if p.group == "chamber":
        return False
    return X7.near_cut(p)


def ext_ro(st: L.State) -> str:
    return f"P16 {L.p16_7_ext(st.tilt, st.ext):5.1f} of 150 mm out"


def tilt_ro(st: L.State) -> str:
    return f"tilt {st.tilt:4.1f} deg\n" + ext_ro(st)


def rise_ro(st: L.State) -> str:
    return f"EC rise {st.ext:4.1f} of {PARK_DROP7:.0f} mm\n" + ext_ro(st)


def door_ro(st: L.State) -> str:
    return rise_ro(st) + f"\ndoor {L.door_open(st):3.1f} of {DOOR_TRAVEL:.0f} mm open"


def _dose(c: E.Clip, secs: float, foc=None, text: str = "", cam=CAM_SIDE, hide=near_cut, save=None, tilt=30.0) -> None:
    g = {"g": None}

    def fr(t, i, n):
        if g["g"] is None:
            g["g"] = RB.Grains(c.v)
        tt = i / FPS
        return dict(st=L.State(tilt=tilt, spin=2 * math.pi * 1.5 * t, **S0), cam=cam, hide=hide, focus=foc, opacity=opac,
                    before=lambda v, s: g["g"].set(tt, True, Z_LAND), readout=lambda st: f"tilt {tilt:.1f} deg\nauger {st.spin / (2 * math.pi):3.1f} turns",
                    text=text, save_as=save)
    c.move(secs, fr, eased=False)
    if g["g"] is not None:
        g["g"].set(0.0, False, Z_LAND)


# ---------------------------------------------------------------- animation props
def _extra_key(key: str, builder) -> str:
    if key not in L.BUILDERS:
        L.BUILDERS[key] = builder
    return key


def _ec7() -> cq.Workplane:
    sam_ = L._read_step_parts(L.REF / "sam-oct13-mounting-plate-and-carriage.step")
    a, c = P7.ec_additions_v7()
    return cq.Workplane("XY").add(sam_["Carriage"]).mirror("XY").union(a).cut(c)


def _ec_trim_part() -> cq.Workplane:
    trim, _, _ = P9.ec_mods_v9()
    return _ec7().intersect(trim)


_extra_key("ec7_whole", _ec7)
_extra_key("ec9_trimmed_off", _ec_trim_part)


# ---------------------------------------------------------------- 1. overview
def overview(preview=False):
    c = E.Clip("overview_v9", TAG, 3, preview)
    camA = ((90, 0, 420), (-1.0, -1.1, 0.45), 1750)
    camB = ((90, 0, 420), (-1.15, 0.75, 0.38), 1750)
    lab = [("Bay window round the balance,\na door for the beaker", part("bay9_front", local=(-163.0, 60.0, 260.0)), "L"),
           ("Balance: no draft cage,\non a granite block", part("block9", local=(-60.0, -100.0, -150.0)), "L"),
           ("Weighing chamber: baffles and\na deck under the bottom run", part("deck9", local=(60.0, -100.0, 406.0)), "R"),
           ("Carousel at v7's height;\nv7's station and EC", part("sprocket_32", name="T+ front"), "R")]
    c.chapter(1, "Chain carousel v9: a variation on v7")
    c.move(4.5, lambda t, i, n: dict(st=L.State(ext=0.0), cam=R.cam_lerp(camA, camB, t), hide=lambda p: p.group == "elec", labels=lab if t > 0.2 else (),
                                     opacity=lambda pl: opac(pl, {"panel_side": 0.1, "panel_side_hatch": 0.1, "panel_top": 0.08}),
                                     text="v7 stays the main version. v9 takes its draft cage off the balance and puts the balance on a granite block, so "
                                          "the beaker sits on the pan 32 mm under the exit (v7: 154, v8: 50). A bay window and a weighing chamber inside "
                                          "the frame take the cage's place. Only what hung over the beaker comes off v7's EC.",
                                     save_as="o1" if preview else None))
    c.chapter(2, "Index, dock, tilt to 30 deg and dose")
    c.move(1.5, lambda t, i, n: dict(st=L.State(shift=-RUN_DIRECTION * MODULE_LINKS * (1 - t), ext=0.0, **S0), cam=R.cam_lerp(camB, CAM_SIDE, t),
                                     hide=lambda p: p.group == "elec" if t < 0.6 else near_cut(p), opacity=opac,
                                     readout=lambda st: f"chain {abs(st.shift) * 9.525:4.1f} mm to go", text="The NEMA 34 moves both chains 8 links.",
                                     save_as="o2" if preview else None))
    c.move(1.2, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * t, **S0), cam=CAM_SIDE, hide=near_cut, opacity=opac, readout=door_ro,
                                     text="The P16 lifts the EC 10 mm onto the posts' domes; its slim finger opens the outlet door.",
                                     save_as="o3" if preview else None))
    c.move(1.2, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=CAM_SIDE, hide=near_cut, opacity=opac, readout=tilt_ro,
                                     text="The same P16 turns the docked EC and module about the hinge, away from the beaker.", save_as="o4" if preview else None))
    _dose(c, 1.8, text="The NEMA 11 turns the auger; the dose falls 32 mm from the exit into the beaker on the pan.", save="o5" if preview else None)
    c.chapter(3, "...on to 90 deg, back, and down")
    c.move(1.8, lambda t, i, n: dict(st=L.State(tilt=30.0 + 60.0 * t, **S0), cam=CAM_SIDE90, hide=near_cut, opacity=opac, readout=tilt_ro,
                                     text="0-90 deg with v7's P16 (130 of its 150 mm).", save_as="o6" if preview else None))
    c.move(1.8, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, opacity=opac, readout=tilt_ro, text="",
                                     save_as="o7" if preview else None))
    c.move(0.8, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, opacity=opac, readout=rise_ro,
                                     text="", save_as="o8" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 2. the drop: what sets it
def drop(preview=False):
    c = E.Clip("drop_v9", TAG, 2, preview)
    foc = lambda p: p.group == "scale" or p.module == 0 or p.group == "station_ec"            # noqa: E731
    cam = ((52.0, SY, 395.0), (0.0, -1.0, 0.04), 300)
    fy = 7.5
    lab = [("Exit (on the hinge axis)", world((D[0], D[1], D[2])), "L"),
           ("Beaker's rim: 32 mm under\nthe exit (v7: 154, v8: 50)", world((PAN[0] - 19.0, D[1], RIM)), "L"),
           ("Slim door finger: its underside\n29 mm under the exit when parked", ec((8.0, fy, 19.9)), "R"),
           ("Every module's door strip:\n22 mm under the exit", sam(0, (-1.0, 7.5, 21.0)), "R"),
           ("EC's new front face (v7's\nwas 18 mm further forward)", ec((EC9_FRONT, 0.0, 45.0)), "R"),
           ("Pan's centre 7 mm in\nfront of the exit", part("bal9_pan", local=(0.0, 0.0, 50.0)), "L")]
    c.chapter(1, "1. What sets the drop now the cage is off")
    c.move(4.5, lambda t, i, n: dict(st=L.State(ext=0.0, **S0), cam=cam, hide=near_cut, focus=foc, opacity=opac, labels=lab if t > 0.15 else (),
                                     text="With no cage, the beaker rises until it meets whatever hangs lowest over it. In v7 that was the EC's front "
                                          "(70 mm under the exit, parked) and its solenoid (63). v9 cuts those back; the slim finger is now the lowest "
                                          "thing over the beaker (29 mm), so the rim sits at 32 mm, 3 mm under it.",
                                     save_as="d1" if preview else None))
    c.chapter(2, "2. Dock, tilt and dose")
    c.move(1.2, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * t, **S0), cam=cam, hide=near_cut, focus=foc, opacity=opac, readout=door_ro,
                                     text="Docking lifts the finger 10 mm: it pushes the door's strip up 6 mm, and the exit opens.", save_as="d2" if preview else None))
    c.move(1.2, lambda t, i, n: dict(st=L.State(tilt=30.0 * t, **S0), cam=cam, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     text="The exit is on the hinge axis, so the stream falls from the same point at every tilt.", save_as="d3" if preview else None))
    _dose(c, 2.0, foc=foc, cam=cam, text="32 mm from the exit to the rim, 81 mm to the beaker's floor (v7: 154 and 201; single doser: about 85 "
                                          "and 153).", save="d4" if preview else None)
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 3. the cage off, the balance up on a block
def balance(preview=False):
    c = E.Clip("balance_v9", TAG, 3, preview)
    hb = float(L.BLOCK9_H)
    nb = 12
    for j in range(nb + 1):
        _extra_key(f"block9_h{j}", (lambda h=max(1.0, hb * j / nb): P9.block_v9(h)))
    cam = ((20.0, SY, 300.0), (-0.85, -1.0, 0.32), 1150)
    foc = lambda p: p.group == "scale" or p.key.startswith(("bal7_", "block9", "beaker"))      # noqa: E731

    def props(z: float, dx: float, cage: float, riser: bool) -> list:
        """v7's balance (cage drawn while cage > 0) or v9's, its feet at height z, the pan's centre dx in front of the exit."""
        M = L.T(None, (D[0] - dx, D[1], z))
        out = []
        j = int(round(nb * z / hb))
        if j > 0:
            out.append(L.Placement(f"block9_h{j}", "Granite block", M, 12, L.GRANITE, "scale"))
        for k, col in (("bal7_base", L.WHITE), ("bal7_display", L.DARK), ("bal7_pan", L.STEEL)):
            out.append(L.Placement(k, k, M, 12, col, "scale"))
        if cage > 0.01:
            up = L.T(None, (0.0, 0.0, 260.0 * (1.0 - cage)))
            for k, col in (("bal7_frame", (0.85, 0.86, 0.88)), ("bal7_glass", L.GLASS), ("bal7_door_left", L.GLASS), ("bal7_door_right", L.GLASS),
                           ("bal7_lid", L.ACRYL)):
                out.append(L.Placement(k, k, M @ up, 12, col, "scale"))
        if riser:
            out.append(L.Placement("beaker_riser", "riser", M @ L.T(None, (0, 0, 50.0)), 12, L.ORANGE, "scale"))
            out.append(L.Placement("beaker", "beaker v7", M @ L.T(None, (0, 0, 50.0 + L.BEAKER_RISER_H - 5.0)), 12, L.GLASS, "scale"))
        else:
            out.append(L.Placement("beaker", "beaker", M @ L.T(None, (0, 0, 50.0)), 12, L.GLASS, "scale"))
        return out

    def st_(z, dx, cage, riser):
        return L.State(ext=0.0, scale=False, chamber=False, extra=props(z, dx, cage, riser), **S0)

    def op(pl):
        o = opac(pl)
        for k, p in R.keyed(pl):
            if p.key in ("bal7_glass", "bal7_door_left", "bal7_door_right", "bal7_lid"):
                o[k] = 0.25
        return o

    hide = lambda p: wide(p) or p.key in ("guide7_cone",)                                       # noqa: E731
    lab1 = [("v7: the draft cage under\nthe EC; rim 154 mm down", world((D[0], D[1], 300.0)), "L"),
            ("Riser in the cage", world((D[0], D[1], 200.0)), "L")]
    c.chapter(1, "1. v7: the draft cage set the drop")
    c.move(2.5, lambda t, i, n: dict(st=st_(0.0, 0.0, 1.0, True), cam=cam, hide=hide, focus=foc, opacity=op, labels=lab1 if t > 0.2 else (),
                                     text="In v7 the balance stood on the bench with its draft cage under the EC, and the beaker sat on a 188 mm riser "
                                          "inside the cage, its rim 154 mm under the exit.", save_as="b1" if preview else None))
    c.chapter(2, "2. The cage comes off")
    c.move(2.5, lambda t, i, n: dict(st=st_(0.0, 0.0, 1.0 - t, t < 0.5), cam=cam, hide=hide, focus=foc, opacity=op,
                                     text="v9 takes the cage off (the closed enclosure round the doser does its job) and the riser out.",
                                     save_as="b2" if preview else None))
    c.chapter(3, "3. The balance goes up on a block; the carousel stays put")
    lab3 = [("Granite block\n252 x 210 x 305 mm", part("block9_h12", local=(-30.0, -105.0, -150.0)), "L"),
            ("Beaker on the pan,\nrim 32 mm under the exit", world((PAN[0], PAN[1], RIM)), "L"),
            ("Carousel at v7's height\n(v8 lowered it 104 mm)", part("sprocket_32", name="B- front"), "R")]
    c.move(3.5, lambda t, i, n: dict(st=st_(hb * t, PAN9_AHEAD * t, 0.0, False), cam=cam, hide=hide, focus=foc, opacity=op,
                                     readout=lambda st: f"block {hb * t:5.1f} mm\nrim {D[2] - (hb * t + 99.0):5.1f} mm under the exit",
                                     text="Instead of lowering the doser, the balance goes up on a block (granite, as the paver in #146, to damp the "
                                          "bench). The pan's centre moves 7 mm in front of the exit, so the beaker clears the EC's new front face.",
                                     save_as="b3" if preview else None))
    c.move(2.5, lambda t, i, n: dict(st=st_(hb, PAN9_AHEAD, 0.0, False), cam=cam, hide=hide, focus=foc, opacity=op, labels=lab3,
                                     readout=f"block {hb:5.1f} mm\nrim {D9:4.1f} mm under the exit", text="", save_as="b4" if preview else None))
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 4. the EC: only what hung over the beaker comes off
def ec_clip(preview=False):
    c = E.Clip("ec_v9", TAG, 3, preview)
    cen = (H[0] + 55.0, SY, H[2] - 34.0)
    cam_a = (cen, (-0.5, -1.0, -0.5), 330)
    cam_b = (cen, (-0.1, -1.0, -0.15), 320)
    foc = lambda p: p.group == "station_ec" or p.key in ("ec7_whole", "ec9_trimmed_off", "solenoid") or (p.module == 0 and p.key in ("door_shutter",))  # noqa: E731
    hide_base = lambda p: near_cut(p) or p.group in ("scale", "station_act", "chamber") or p.key in ("guide7_vee", "guide7_cone", "nema34")   # noqa: E731
    S = L.electronics_frame(0.0, 0.0)                     # the parked EC's frame (as drawn)

    def sol_M(x: float, dz: float) -> np.ndarray:
        return S @ L.T(L.Rx(math.pi), (x, 0, -SOL_Z + dz))

    def st_v7():
        ex = [L.Placement("ec7_whole", "EC v7 (as drawn)", S, 8, L.ELEC, "station_ec"),
              L.Placement("solenoid", "solenoid at v7's place", sol_M(SOL_X, 0.0), 8, L.DARK, "station_ec")]
        return ex

    def hide_v7(p):
        return hide_base(p) or (p.key in ("sam_electronics_carriage", "solenoid") and p.name.startswith(("Electronics carriage v9", "Solenoid (Adafruit 412; v9")))

    lab1 = [("v7's EC: its front hangs\n70 mm under the exit, parked", ec((6.0, 0.0, 58.0)), "L"),
            ("Solenoid at the front:\n63 mm under the exit", ec((SOL_X, -7.0, 45.0)), "L"),
            ("v7's door finger", ec((-2.0, 7.5, 24.0)), "L"),
            ("NEMA 11 in front of the gear", ec((45.0, -14.0, 33.0)), "R")]
    c.chapter(1, "1. v7's EC over the beaker")
    c.move(3.0, lambda t, i, n: dict(st=L.State(ext=0.0, extra=st_v7(), **S0), cam=R.cam_lerp(cam_a, cam_b, t), hide=hide_v7, focus=foc,
                                     labels=lab1 if t > 0.2 else (), readout=rise_ro,
                                     text="With the cage gone, v7's EC is what stops the beaker: its front 18 mm (Sam's carriage's solenoid bay) hangs "
                                          "70 mm under the exit when parked, and the solenoid in it 63.", save_as="e1" if preview else None))
    c.chapter(2, "2. Cut back the front, move the solenoid behind the gear")

    def move_frame(t, i, n):
        # the trimmed part turns red and drops away; the solenoid goes down, back along the tail and up into its cradle
        fall = 120.0 * max(0.0, (t - 0.15) / 0.35) if t > 0.15 else 0.0
        if t < 0.5:
            sx, sdz = SOL_X, 0.0
        elif t < 0.6:
            sx, sdz = SOL_X, 45.0 * (t - 0.5) / 0.1
        elif t < 0.85:
            sx, sdz = SOL_X + (SOL9_X - SOL_X) * (t - 0.6) / 0.25, 45.0
        else:
            sx, sdz = SOL9_X, 45.0 * (1.0 - (t - 0.85) / 0.15)
        ex = [L.Placement("solenoid", "solenoid moving", sol_M(sx, sdz), 8, L.DARK, "station_ec")]
        if t < 0.5:
            ex.append(L.Placement("ec9_trimmed_off", "front 18 mm", S @ L.T(None, (0, 0, fall)), 8, (0.92, 0.22, 0.12), "station_ec"))
        return dict(st=L.State(ext=0.0, extra=ex, **S0), cam=cam_b, hide=lambda p: hide_base(p) or p.name.startswith("Solenoid (Adafruit 412; v9"),
                    focus=foc, accent=lambda p: (0.92, 0.22, 0.12) if p.key == "ec9_trimmed_off" else None,
                    text="The front 18 mm (red) comes off, with v7's finger. The solenoid moves behind the gear onto the EC's tail, between "
                         "the guide shoes, plunger up under the tube as before: in v7's layout the NEMA 11's body fills the space in front of "
                         "the gear.", save_as="e2" if preview else None)
    c.move(5.0, move_frame, eased=False)
    c.chapter(3, "3. EC v9: the rest is v7's")
    lab3 = [("New front wall, 2.5 mm in\nfront of the NEMA 11", ec((EC9_FRONT + 1.2, -12.0, 40.0)), "L"),
            ("Slim finger: a 3 x 4 mm arm\nto the door's push strip", ec((4.0, 7.5, 18.4)), "L"),
            ("Solenoid on the tail,\nbehind the gear", ec((SOL9_X, -7.0, 40.0)), "R"),
            ("Unchanged: the dock's ears,\nthe P16's pin, the shoes", ec((KC7_A[0], KC7_A[1], 25.0)), "R")]
    c.move(3.5, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * t, **S0), cam=cam_b, hide=hide_base, focus=foc, labels=lab3, readout=door_ro,
                                     text="Docking is v7's: the P16 lifts the EC 10 mm onto the posts' domes, and the finger opens the outlet door "
                                          "in the last 6 mm.", save_as="e3" if preview else None))
    c.hold(1.0)
    c.done()


# ---------------------------------------------------------------- 5. the enclosure: the bay window and the weighing chamber
def enclosure(preview=False):
    c = E.Clip("enclosure_v9", TAG, 3, preview)
    cam1 = ((-40.0, 0.0, 330.0), (-1.0, -0.75, 0.32), 1250)
    foc1 = lambda p: p.group in ("enclosure", "scale", "chamber")                             # noqa: E731
    lab1 = [("Bay window: 100 mm proud\nof the front panel", part("bay9_top", local=(-115.0, -60.0, 408.0)), "L"),
            ("Door for the beaker\n(200 x 112 mm)", part("bay9_door", local=(100.0, 56.0, 0.0)), "L"),
            ("Balance on its block, inside\nthe bay (display nose 79 mm out)", part("bal9_display"), "R"),
            ("Side hatch for swaps (v7's)", part("hatch_side", local=(100.0, 100.0, 0.0)), "R")]
    c.chapter(1, "1. A bay window round the balance")
    c.move(3.5, lambda t, i, n: dict(st=L.State(ext=0.0), cam=R.cam_lerp(cam1, ((-40.0, 0.0, 330.0), (-1.0, -0.35, 0.25), 1250), t),
                                     hide=lambda p: p.group == "elec", focus=foc1, labels=lab1 if t > 0.2 else (),
                                     opacity=lambda pl: opac(pl, {"panel_side": 0.1, "panel_side_hatch": 0.1, "panel_top": 0.08}),
                                     text="The balance's display sticks out 79 mm past the frame. The bay window, a clear acrylic box 100 mm proud of "
                                          "the front panel, closes round it, from the bench up to the deck; the front panel's opening joins the bay to the "
                                          "space under the station.", save_as="n1" if preview else None))
    c.chapter(2, "2. Open the door, put a beaker on the pan, close the door")
    cam2 = ((-20.0, SY, 380.0), (-1.0, -0.45, 0.35), 700)

    def load(t, i, n):
        ang = 100.0 * min(1.0, t / 0.2) if t < 0.8 else 100.0 * (1.0 - (t - 0.8) / 0.2)
        u = min(1.0, max(0.0, (t - 0.2) / 0.45))
        dx = -230.0 * (1.0 - u)
        dz = 12.0 * min(1.0, max(0.0, (0.75 - t) / 0.1)) if t < 0.75 else 0.0
        return dict(st=L.State(ext=0.0, hatch_front=ang, beaker_dx=dx, beaker_dz=dz), cam=cam2, hide=lambda p: p.group == "elec" or p.key in ("panel_side", "panel_top"),
                    focus=foc1, opacity=lambda pl: opac(pl), readout=f"bay door {ang:4.0f} deg",
                    text="Sam's item 5, kept: open the door, reach over the display, set the beaker on the pan under the exit, close the door.",
                    save_as="n2" if preview else None)
    c.move(5.0, load, eased=False)
    c.chapter(3, "3. Inside: a weighing chamber under the carousel")
    cam3 = ((60.0, SY, 330.0), (-0.55, -1.0, 0.62), 1050)
    lab3 = [("Deck: 4.6 mm under the passing\nmodules, open only at the station", part("deck9", local=(-20.0, -90.0, 408.0)), "L"),
            ("Side baffles, in line with\nthe bay's sides", part("baffle9_side_p", local=(60.0, 122.0, 200.0)), "R"),
            ("Back baffle: a slot for the P16,\n3 mm in front of the NEMA 34", part("baffle9_back", local=(161.0, 60.0, 250.0)), "R")]

    def inside(t, i, n):
        return dict(st=L.State(shift=-RUN_DIRECTION * MODULE_LINKS * t, ext=0.0), cam=cam3,
                    hide=lambda p: p.group == "elec" or p.key in ("panel_side", "panel_side_hatch", "panel_top", "panel_front_bay", "panel_back", "hatch_side",
                                                                  "bay9_top", "bay9_side_m", "baffle9_side_m"),
                    focus=lambda p: p.group in ("chamber", "scale") or p.key.startswith("bay9_"), labels=lab3 if t > 0.1 else (),
                    accent=lambda p: (0.20, 0.55, 0.95) if p.group == "chamber" else None,
                    opacity=lambda pl: opac(pl, {"deck9": 0.35, "baffle9_side_p": 0.3, "baffle9_back": 0.3}),
                    readout=lambda st: f"chain {abs(st.shift) * 9.525:4.1f} mm",
                    text="Inside the frame, two side baffles, a back baffle and a deck close the space round the balance, so the air the "
                         "moving carousel stirs stays above the deck. The deck is open only where the EC rises and the stream falls; the "
                         "back baffle has a slot for the P16.", save_as="n3" if preview else None)
    c.move(5.0, inside, eased=False)
    c.hold(0.8)
    c.done()


# ---------------------------------------------------------------- 6. 90 degrees with the beaker in place
def tilt90(preview=False):
    c = E.Clip("tilt90_v9", TAG, 2, preview)
    foc = lambda p: p.group in ("station_act", "station_ec", "scale") or p.key in ("clevis_bracket",) or p.module == 0 or p.key == "carriage"  # noqa: E731
    lab = [("P16: 130 of 150 mm\nout at 90 deg", part("actuator_rod", local=(0, 0, 150.0)), "R"),
           ("The EC turns back and up,\naway from the beaker", ec((60.0, 0.0, 40.0)), "R"),
           ("Beaker: rim 32 mm\nunder the exit", world((PAN[0], PAN[1], RIM)), "L")]
    c.chapter(1, "1. 0 to 90 deg with the one P16, the beaker in place")
    c.move(5.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * t, **S0), cam=CAM_SIDE90, hide=near_cut, focus=foc, opacity=opac,
                                     labels=lab if t > 0.85 else (), readout=tilt_ro,
                                     text="v7's P16, pins and guides, unchanged: 0-90 deg takes 130 of its 150 mm. The exit stays on the hinge "
                                          "axis, and everything that turns with the module swings back and up, away from the beaker.",
                                     save_as="t1" if preview else None))
    c.hold(1.0)
    c.chapter(2, "2. Back to 0, and down onto the guides' seats")
    c.move(3.0, lambda t, i, n: dict(st=L.State(tilt=90.0 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, focus=foc, opacity=opac, readout=tilt_ro,
                                     text="", save_as="t2" if preview else None))
    c.move(1.2, lambda t, i, n: dict(st=L.State(ext=PARK_DROP7 * (1 - t), **S0), cam=CAM_SIDE90, hide=near_cut, focus=foc, opacity=opac,
                                     readout=rise_ro, text="", save_as="t3" if preview else None))
    c.hold(0.8)
    c.done()


CLIPS = {"overview": overview, "drop": drop, "balance": balance, "ec": ec_clip, "enclosure": enclosure, "tilt90": tilt90}

if __name__ == "__main__":
    pv = "--preview" in sys.argv
    for name in [a for a in sys.argv[1:] if not a.startswith("--")] or list(CLIPS):
        CLIPS[name](pv)
